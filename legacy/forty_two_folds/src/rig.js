// rig.js: the shared character construction for BOTH characters.
//
// ONE canonical height h (px on screen at zoom 1) drives every proportion. Both characters use the same PROP table,
// measured from reference/chatgpt_dragon_ref.png (the proportional anchor) and nudged to 6.6 heads so both fall in the
// requested 6.5–7 range (the references themselves disagree: ChatGPT's art is ~6.1 heads, Claude's ~7.3).
// Costume, hair and face styling differ; anatomy never does. Nothing is scaled per part or per shot: a camera changes
// how big h looks, never the ratios.
//
// Coordinates: character space is in units of h, origin on the ground between the feet, y UP, x to screen-right when
// facing front (the character's own left), z toward the viewer. Turns are a yaw φ per body level (eyes, head, chest,
// hips); a point (x, y, z) lands at screen u = x·cosφ + z·sinφ, depth d = −x·sinφ + z·cosφ. Bodies are built from
// horizontal cross-sections (half-width a, front depth bf, back depth bb), so every silhouette exists at every yaw and
// a turn is continuous instead of snapping between drawn views. Yaw is given in TURN UNITS: 0 front, ±1 profile
// (+ faces screen-right), ±2 back.

const PROP = {
  head: .152,               // crown to chin (6.6 heads)
  crown: 1.0, chin: .848, eyeV: .585,   // eyeV: eye line as a fraction of the head, from the crown
  neckTop: .862, neckBase: .812, neckR: .021,
  shoulderY: .796, shoulderX: .082,     // shoulder joints
  chest: .742, underbust: .705, waist: .655, hip: .575, crotch: .505,
  hipJointY: .522, hipJointX: .046,
  upperArm: .166, foreArm: .146, hand: .07,
  thigh: .236, shin: .232, ankleY: .054, foot: .098,
};
// torso cross-sections: [y, a, bf, bb, zc] (units of h)
const TORSO = [
  [.815, .028, .025, .028, -.004],
  [.800, .062, .036, .036, -.004],
  [.785, .078, .042, .040, -.002],
  [.745, .074, .058, .042, .000],
  [.705, .064, .046, .040, .000],
  [.655, .053, .040, .038, .000],
  [.610, .066, .042, .050, -.002],
  [.570, .077, .046, .058, -.004],
  [.530, .076, .044, .056, -.004],
  [.505, .068, .040, .050, -.004],
];
// head cross-sections in HEAD units (1 = crown→chin), v from the crown: [v, a, bf, bb, zc]
const HEADSEC = [
  [.00, .10, .10, .10, 0], [.07, .27, .27, .30, 0], [.18, .36, .35, .40, 0], [.32, .405, .385, .44, 0],
  [.46, .415, .40, .43, 0], [.58, .405, .41, .38, 0], [.68, .38, .44, .30, 0], [.76, .345, .425, .22, 0],
  [.84, .30, .40, .14, 0], [.91, .225, .37, .08, 0], [.965, .135, .335, .04, 0], [1.0, .05, .31, .02, 0],
];

const TU = Math.PI / 2;   // one turn unit in radians
function secLR(a, bf, bb, zc, phi) {
  const c = Math.cos(phi), s = Math.sin(phi);
  const f = Math.sqrt(a * a * c * c + bf * bf * s * s), b = Math.sqrt(a * a * c * c + bb * bb * s * s), m = zc * s;
  return s >= 0 ? [m - b, m + f] : [m - f, m + b];
}
// point on a cross-section surface at azimuth th (0 = front centre, +π/2 = the character's left), projected under phi.
// Returns [u, depth, facing] where facing = cos of the angle between the surface normal and the view (≤0: hidden).
function surf(a, bf, bb, zc, th, phi) {
  const x = a * Math.sin(th), z = zc + (Math.cos(th) >= 0 ? bf : bb) * Math.cos(th);
  const c = Math.cos(phi), s = Math.sin(phi);
  return [x * c + z * s, -x * s + z * c, Math.cos(th + phi)];
}
// interpolate a cross-section table at y (rows sorted by y descending or v ascending: key column 0)
function secAt(tab, y) {
  const asc = tab[0][0] < tab[tab.length - 1][0];
  for (let i = 0; i < tab.length - 1; i++) {
    const A = tab[i], B = tab[i + 1], lo = asc ? A[0] : B[0], hi = asc ? B[0] : A[0];
    if (y >= lo && y <= hi) { const k = (y - A[0]) / (B[0] - A[0]); return A.map((v, j) => lerp(v, B[j], k)); }
  }
  return (asc ? (y < tab[0][0]) : (y > tab[0][0])) ? tab[0].slice() : tab[tab.length - 1].slice();
}

// 2-bone IK in a plane: root S, target T, lengths L1, L2, bend = +1/−1 (which side the joint bends to). Returns the
// middle joint. If the target is out of reach the limb straightens toward it (no pops: the reach is soft-clamped).
function ik2(S, T, L1, L2, bend = 1) {
  const d = sub2(T, S); let D = len2(d);
  const maxR = (L1 + L2) * .999; if (D > maxR) D = maxR - (maxR * .02) * Math.exp(-(D - maxR) / (maxR * .02)); // soft clamp
  D = Math.max(D, Math.abs(L1 - L2) + 1e-3);
  const a = Math.acos(clamp((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1)), base = Math.atan2(d[1], d[0]);
  return add2(S, rot2([L1, 0], base + bend * a));
}

// ---------- the body frame: character space → world px ----------
// A Body holds where the character stands and how the upper body leans. lean rotates everything above the hips
// around the pelvis (screen-plane roll); tilt rolls the head around the neck; bob lifts the whole body (crouch < 0).
function makeFrame(x, gy, h, o) {
  const pel = [x + h * (o.dx || 0), gy - h * (PROP.hipJointY + (o.bob || 0))];
  const lean = o.lean || 0, tilt = o.tilt || 0;
  const neckW = () => upper([0, PROP.neckTop]);
  function raw(u, v) { return [x + h * (u + (o.dx || 0)), gy - h * (v + (o.bob || 0))]; }
  function upper(p) { const q = raw(p[0], p[1]); return add2(pel, rot2(sub2(q, pel), lean)); }
  return { x, gy, h, pel, lean, tilt, raw, upper,
    // head space: head units (1 = head height, v = 0 at the crown, 1 at the chin, u across) around the neck pivot
    // (head v = .88, just behind the jaw), rolled by lean + tilt. headDx/headDy shift the head (units of h).
    head(u, v) {
      const hh = PROP.head * h, piv = upper([o.headDx || 0, PROP.chin + .12 * PROP.head + (o.headDy || 0)]);
      return add2(piv, rot2([u * hh, (v - .88) * hh], lean + tilt));
    } };
}
