"""Opening test, 0:00-0:21 of the master: "Three... two... one... Loading." -> verse 1 (A).

The countdown is a dimension count. The world loses one dimension per word, is rebuilt as a
sheet of paper on the hit, and gets its depth back when the ink leaves the page.

  0.0-1.0    dust drifting past the lens, a galaxy barely there
  1.0        "Three": the galaxy ignites from the core outward; the camera pulls out of it
  3.3        "two": its thickness collapses into a plane (the dual-vector foil); a sheen sweeps it
  4.5        "one": the plane collapses into a single line; the camera turns face-on
  5.62       bass hit: the line is the hinge of a sheet of paper that swings up into a wall;
             most of the galaxy scatters into the starfield behind it, some flies past the lens
  6.3        "Loading.": the camera pulls back to show the page floating in space; the rest of
             the line streams into the two silhouettes; the page frays into motes at its edges
  7.55       downbeat: A and B paint themselves in (pencil -> flat -> painted) under a pool of light
  7.55-13.4  embers (the travellers' traces) lift off the page into depth and drift toward A,
             brightening on the tracked beats
  13.4-14.45 the song's silence: story time stops, the camera keeps moving (bullet time) and each
             ember's recent path hangs in the air as a filament: time shown as a direction in space
  14.45-21   the embers snap into constellations in front of and above the page; the camera
             cranes up under them ("a mind with no sky")

Every frame is a pure function of t (no state), so frames render in parallel.
Usage: python3 opening.py OUTDIR [t0 t1] [--sheet]
"""
import sys, os, json, numpy as np, cv2
from multiprocessing import Pool
from scipy.interpolate import PchipInterpolator
from characters import stages

W, H, FPS = 1280, 720, 30
PW, PH, PPU = 1600, 1000, 100          # page texture size and pixels per world unit (page is 16 x 10)
F = 900.0                              # focal length in px
PAPER = np.array([0.95, 0.925, 0.875], np.float32)
JADE = np.array([0.30, 0.95, 0.72], np.float32)
CORE = np.array([1.00, 0.84, 0.62], np.float32)
BLUE = np.array([0.60, 0.72, 1.00], np.float32)
EMBER = np.array([1.00, 0.60, 0.26], np.float32)
WARM = np.array([1.00, 0.93, 0.80], np.float32)
GOLD = np.array([1.00, 0.78, 0.45], np.float32)

T_THREE, T_TWO, T_ONE, T_HIT, T_LOAD, T_DOWN = 1.0, 3.3, 4.5, 5.62, 6.3, 7.55
T_FREEZE0, T_FREEZE1 = 13.40, 14.45
HERE = os.path.dirname(os.path.abspath(__file__))
BEATS = np.array([b for b in json.load(open(f'{HERE}/../timing/p0_beatmap.json'))['beats_s']
                  if b < 22 and not (T_FREEZE0 - 0.1 < b < T_FREEZE1)])

def sm(a, b, t):
    x = np.clip((t - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def eo(a, b, t):            # ease-out cubic
    x = np.clip((t - a) / (b - a), 0, 1); return 1 - (1 - x) ** 3
def eio(a, b, t):           # ease-in-out cubic
    x = np.clip((t - a) / (b - a), 0, 1); return np.where(x < .5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)
def tau(t):                 # story time: frozen during the silence
    if t < T_FREEZE0: return t
    if t < T_FREEZE1: return T_FREEZE0
    return t - (T_FREEZE1 - T_FREEZE0)
def beat_pulse(s):          # 1 on each tracked beat, decaying
    b = BEATS[BEATS <= s]
    return float(np.exp(-(s - b[-1]) * 7)) if len(b) else 0.0

# ---------------------------------------------------------------- galaxy (story time < T_HIT)
rng = np.random.default_rng(7)
N = 160000
g_r = rng.gamma(2.0, 1.75, N).clip(0.05, 10.5)
arm = rng.integers(0, 3, N)
g_th = arm * 2 * np.pi / 3 + g_r * 0.62 + rng.normal(0, 0.17, N)
inter = rng.random(N) < 0.22
g_th[inter] = rng.uniform(0, 2 * np.pi, inter.sum())
g_z = rng.normal(0, 1, N) * (0.22 + 1.1 * np.exp(-g_r / 1.8))
g_om = 0.55 / (1 + 0.28 * g_r)                                          # differential rotation
halo = rng.random(N) < 0.16
hv = rng.normal(0, 1, (halo.sum(), 3)); hv /= np.linalg.norm(hv, axis=1, keepdims=True)
H0 = hv * rng.uniform(1.5, 10, halo.sum())[:, None]
g_col = CORE[None] * np.exp(-g_r / 1.9)[:, None] + BLUE[None] * (1 - np.exp(-g_r / 1.9))[:, None]
knot = (rng.random(N) < 0.07) & (g_r > 2.2) & ~inter
g_col[knot] = JADE
g_col[halo] = BLUE * 0.8
g_w = (rng.uniform(0.35, 1.0, N) * 0.20).astype(np.float32)
g_w[halo] *= 0.55; g_w[knot] *= 1.8

def galaxy_pos(s):
    ang = g_th + g_om * s
    x = g_r * np.cos(ang); y = g_r * np.sin(ang) * 0.92; z = g_z.copy()
    ha = 0.05 * s; ca, sa = np.cos(ha), np.sin(ha)
    x[halo] = H0[:, 0] * ca - H0[:, 1] * sa; y[halo] = H0[:, 0] * sa + H0[:, 1] * ca; z[halo] = H0[:, 2]
    y = y + 5.0
    f2 = eio(T_TWO, T_TWO + 0.9, s); z = z * (1 - f2)                    # "two": thickness -> 0
    f1 = eio(T_ONE, T_ONE + 0.75, s)                                     # "one": height -> 0
    y = y * (1 - f1) + 0.03 * np.sin(x * 2.5 + s * 18) * f1 * (1 - sm(T_HIT - 0.2, T_HIT, s))
    x = x * (1 - 0.12 * f1)
    return np.stack([x, y, z], 1)

L_HIT = galaxy_pos(T_HIT)
NF = 14000                                                              # these become the witnesses
FORM = rng.choice(N, NF, replace=False)
rest = np.setdiff1d(np.arange(N), FORM)
FLY = rest[rng.random(len(rest)) < 0.18]                                # fly past the lens on the hit
BACK = np.setdiff1d(rest, FLY)                                          # scatter behind the page
sd = rng.normal(0, 1, (len(BACK), 3)); sd /= np.linalg.norm(sd, axis=1, keepdims=True)
S_BACK = sd * rng.uniform(18, 75, len(BACK))[:, None]
S_BACK[:, 2] = -np.abs(S_BACK[:, 2]) - 5; S_BACK[:, 1] += 5
fv = np.column_stack([rng.normal(0, 0.9, len(FLY)), rng.normal(0.25, 0.7, len(FLY)), np.ones(len(FLY)) * 2.2])
V_FLY = fv / np.linalg.norm(fv, axis=1, keepdims=True) * rng.uniform(9, 26, len(FLY))[:, None]

# far stars (always there, give the camera moves something to turn against) and near dust
NS = 7000
sv = rng.normal(0, 1, (NS, 3)); sv /= np.linalg.norm(sv, axis=1, keepdims=True)
STARS_FAR = sv * rng.uniform(160, 260, NS)[:, None]
star_col = np.where(rng.random(NS)[:, None] < 0.2, BLUE[None], WARM[None])
star_w = rng.pareto(2.2, NS).clip(0, 6) * 0.10 + 0.04
ND = 1600
DUST = np.column_stack([rng.uniform(-12, 12, ND), rng.uniform(-4, 14, ND), rng.uniform(-6, 16, ND)])
dust_ph = rng.uniform(0, 2 * np.pi, ND)

# ---------------------------------------------------------------- page and witnesses
CH_H = 600
ST = {'A': stages('A', CH_H), 'B': stages('B', CH_H)}
POS = {'A': 620, 'B': 985}                                             # page x of each figure centre
FEET = PH - 28
def char_box(w):
    im = ST[w]['painted']; return POS[w] - im.shape[1] // 2, FEET - im.shape[0], im
tg = []
for w in 'AB':
    x0, y0, im = char_box(w); ys, xs = np.nonzero(im[..., 3] > 0.5)
    idx = rng.choice(len(xs), NF // 2)
    tg.append(np.stack([(x0 + xs[idx] - PW / 2) / PPU, (PH - (y0 + ys[idx])) / PPU], 1))
TGT_UV = np.concatenate(tg).astype(np.float32)
form_delay = rng.uniform(0, 0.4, NF)

yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
grain = cv2.GaussianBlur(rng.random((PH, PW)).astype(np.float32), (0, 0), 1.1)
fibre = cv2.GaussianBlur(rng.random((PH, PW)).astype(np.float32), (0, 0), 16)
PAPER_TEX = PAPER[None, None] * (0.965 + 0.05 * grain[..., None] + 0.06 * (fibre[..., None] - 0.5))
GRID = np.zeros((PH, PW), np.float32)
GRID[:, ::100] = 1; GRID[::100, :] = 1
GRID = cv2.GaussianBlur(GRID, (3, 3), 0.6)
def norm01(a): return (a - a.min()) / (a.max() - a.min())
NOISE = norm01(cv2.GaussianBlur(rng.random((PH, PW)).astype(np.float32), (0, 0), 6))
NOISE_E = norm01(cv2.GaussianBlur(rng.random((PH, PW)).astype(np.float32), (0, 0), 4))
d_edge = np.minimum(np.minimum(xx, PW - 1 - xx), yy)                   # bottom edge (the hinge) stays crisp
ALPHA = np.clip((d_edge - 22 * NOISE_E) / 12, 0, 1)
cxp = (POS['A'] + POS['B']) / 2
LIGHT = np.clip(0.07 + 0.30 * np.exp(-(((xx - cxp) / 650) ** 2 + ((yy - 600) / 480) ** 2))
                + 0.50 * sum(np.exp(-(((xx - POS[w]) / 210) ** 2 + ((yy - 640) / 400) ** 2)) for w in 'AB'), 0, 1)
PERIPH = 1 - np.exp(-(((xx - cxp) / 520) ** 2 + ((yy - 620) / 420) ** 2))
GLOW_A = np.exp(-(((xx - POS['A']) / 300) ** 2 + ((yy - 420) / 280) ** 2))
SHADOW = np.zeros((PH, PW), np.float32)
for w in 'AB':
    cv2.ellipse(SHADOW, (POS[w] + (8 if w == 'A' else -8), FEET - 4), (95, 13), 0, 0, 360, 1.0, -1)
SHADOW = cv2.GaussianBlur(SHADOW, (0, 0), 9)
EDGE_GLOW = np.exp(-(PH - 1 - yy) / 5.0)

def page_angle(s):          # degrees; 0 = lying flat away from camera, 90 = upright; back-ease overshoot
    x = np.clip((s - T_HIT) / 0.85, 0, 1); c1 = 1.4
    return 90 * (1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2)
def page_world(u, v, s):
    a = np.radians(page_angle(s))
    return np.stack([u, v * np.sin(a), -v * np.cos(a)], -1)
def page_side(P, s):        # signed distance to the page plane, + toward the viewer
    a = np.radians(page_angle(s))
    return P[:, 1] * np.cos(a) + P[:, 2] * np.sin(a)

def page_texture(s):
    tex = PAPER_TEX.copy()
    tex -= (GRID * (0.03 + 0.05 * PERIPH))[..., None] * sm(T_HIT + 0.2, T_DOWN, s)
    tex *= 1 - (SHADOW * 0.30 * sm(T_DOWN - 0.3, T_DOWN + 0.6, s))[..., None]
    # light: flash on the hit, then an unlit page for "Loading", then two pools of light at the downbeat
    pool = sm(T_DOWN - 0.3, T_DOWN + 1.2, s)
    unlit = 0.20 + 0.80 * (1 - sm(T_HIT + 0.15, T_LOAD + 0.3, s))
    tex *= (unlit * (1 - pool) + LIGHT * pool)[..., None]
    tex += (GLOW_A * 0.06 * sm(T_DOWN, 9.5, s) * (1 + 0.8 * beat_pulse(s)))[..., None] * WARM
    lit_ch = unlit * (1 - pool) + 0.97 * pool
    for w in 'AB':          # pencil -> flat -> painted, through a ragged noise mask, top to bottom
        x0, y0, _ = char_box(w); st = ST[w]; h_, w_ = st['painted'].shape[:2]
        nz = NOISE[y0:y0 + h_, x0:x0 + w_][..., None] * 0.6 + np.linspace(0, 0.4, h_)[:, None, None]
        d = 0.18 if w == 'B' else 0.0
        p_pen = np.clip((s - (T_DOWN - 0.75 + d)) / 0.5 - nz, 0, 1)
        p_flat = np.clip((s - (T_DOWN - 0.05 + d)) / 0.45 - nz, 0, 1)
        p_paint = np.clip((s - (T_DOWN + 0.35 + d)) / 0.6 - nz, 0, 1)
        reg = tex[y0:y0 + h_, x0:x0 + w_]
        for key, p in (('pencil', p_pen), ('flat', p_flat), ('painted', p_paint)):
            a = st[key][..., 3:] * p
            c = st[key][..., :3] * (lit_ch if key != 'pencil' else 1.0)
            reg[:] = reg * (1 - a) + c * a
    if s >= T_HIT:
        tex += (EDGE_GLOW * 1.2 * np.exp(-(s - T_HIT) * 2.2))[..., None] * WARM
        tex += 0.22 * np.exp(-(s - T_HIT) * 2.5)
    return tex

# page motes: the frayed edge keeps shedding flecks into space
NM = 4000
m_side = rng.integers(0, 3, NM); m_t = rng.random(NM)
m_u = np.where(m_side == 0, -8 + 0.4 * rng.random(NM), np.where(m_side == 1, 8 - 0.4 * rng.random(NM), -8 + 16 * m_t))
m_v = np.where(m_side == 2, 10 - 0.4 * rng.random(NM), 10 * m_t)
m_du = np.where(m_side == 0, -1, np.where(m_side == 1, 1, 0)) * rng.uniform(0.2, 0.8, NM) + rng.normal(0, 0.15, NM)
m_dv = np.where(m_side == 2, 1, 0) * rng.uniform(0.2, 0.8, NM) + rng.normal(0.1, 0.15, NM)
m_dz = rng.uniform(-0.3, 0.6, NM); m_ph = rng.random(NM); M_LIFE = 3.0

# embers: the travellers' traces, lifting off the page toward A
K = 3200
e_u0 = rng.normal(0, 3.6, K).clip(-7.6, 7.6); e_v0 = rng.uniform(0.05, 1.8, K)
for _w in 'AB':                                   # keep the embers from starting on the two of them
    _c = (POS[_w] - PW / 2) / PPU; _m = np.abs(e_u0 - _c) < 1.1
    e_u0[_m] = _c + np.sign(e_u0[_m] - _c + 1e-6) * rng.uniform(1.1, 2.4, _m.sum())
e_ts = T_DOWN + rng.uniform(0, 5.6, K); e_ph = rng.uniform(0, 2 * np.pi, K)
e_sp = rng.uniform(0.45, 1.1, K); e_zm = rng.uniform(0.4, 3.5, K)
e_col = np.where(rng.random(K)[:, None] < 0.22, JADE[None], EMBER[None])
e_w = rng.uniform(0.5, 1.0, K) * 1.1
A_U = (POS['A'] - PW / 2) / PPU
cons = [((-5.4, 8.8), 7), ((-2.2, 10.2), 6), ((-7.0, 6.6), 5), ((0.9, 8.6), 6), ((-3.6, 7.1), 5)]
STAR_P, SEGS = [], []
for (cx, cy), n in cons:
    pts = np.array([cx, cy]) + np.cumsum(rng.normal(0, 0.62, (n, 2)), 0) * 0.85
    i0 = len(STAR_P)
    for p in pts: STAR_P.append([p[0], p[1], rng.uniform(0.6, 3.4)])
    SEGS.append([(i0 + j, i0 + j + 1) for j in range(n - 1)])
STAR_P = np.array(STAR_P)
star_of = rng.integers(0, len(STAR_P), K)
snap_delay = rng.uniform(0, 0.6, K)

def ember_pos(s):
    a = np.clip(s - e_ts, 0, None)
    u = e_u0 + (A_U - e_u0) * (1 - np.exp(-a * 0.22)) + 0.45 * np.sin(a * 1.1 + e_ph)
    v = e_v0 + e_sp * a + 0.3 * np.sin(a * 0.8 + e_ph * 1.7)
    z = e_zm * (1 - np.exp(-a * 0.7)) + 0.15 * np.sin(a + e_ph)
    P = np.stack([u, v, z], 1)
    e = np.zeros(K)
    if s > T_FREEZE0:
        e = eio(T_FREEZE0, T_FREEZE0 + 1.5, s - snap_delay)
        P = P + (STAR_P[star_of] - P) * e[:, None]
    return P, s > e_ts, e

# ---------------------------------------------------------------- camera (real time: it keeps moving through the freeze)
KEYS = np.array([
    # t      yaw  pitch  dist   tx    ty   tz
    [0.00,   18,  12,    9.0,  0.0,  5.0, 0.0],
    [1.00,   22,  15,   10.0,  0.0,  5.0, 0.0],
    [3.30,   40,  30,   18.0,  0.0,  5.0, 0.0],
    [4.20,   18,  10,   16.0,  0.0,  4.6, 0.0],
    [4.50,   14,   8,   15.5,  0.0,  4.3, 0.0],
    [5.50,    0,   3,   13.0,  0.0,  2.2, 0.0],
    [6.35,    0,   4,   14.5,  0.0,  3.0, 0.0],
    [7.55,   16,   8,   22.0,  0.0,  4.6, 0.0],
    [9.50,    8,   6,   14.0,  0.0,  3.4, 0.0],
    [13.40,  -9,   4,   10.5,  0.0,  3.3, 0.0],
    [14.45, -32,   9,    9.5,  0.0,  3.5, 0.0],
    [17.00, -26,  -4,   13.0, -0.8,  5.4, 0.8],
    [21.00, -18, -10,   17.0, -1.4,  6.6, 1.0]])
CAM = PchipInterpolator(KEYS[:, 0], KEYS[:, 1:], axis=0, extrapolate=True)

def camera(t):
    yaw, pitch, dist, tx, ty, tz = CAM(t)
    if t >= T_HIT:                                                          # the hit shakes the camera
        k = np.exp(-(t - T_HIT) * 5) * 0.09
        tx += k * np.sin(t * 71); ty += k * np.cos(t * 53)
    tgt = np.array([tx, ty, tz])
    cy, sy, cp, sp = np.cos(np.radians(yaw)), np.sin(np.radians(yaw)), np.cos(np.radians(pitch)), np.sin(np.radians(pitch))
    eye = tgt + dist * np.array([sy * cp, sp, cy * cp])
    fwd = tgt - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    return eye, np.stack([right, up, fwd]), dist

def project(P, cam):
    eye, R, _ = cam
    c = (P - eye) @ R.T
    z = c[:, 2]; zz = np.maximum(z, 1e-3)
    return W / 2 + F * c[:, 0] / zz, H / 2 - F * c[:, 1] / zz, z

# ---------------------------------------------------------------- particle light
def all_particles(s, t):
    """World positions, colours, weights of every light particle at story time s."""
    Ps, Cs, Ws = [STARS_FAR], [star_col], [star_w * (0.6 + 0.4 * sm(0, 2.5, t))]
    if s < T_DOWN + 0.8:                                                    # dust near the lens
        Dp = DUST + np.column_stack([0.3 * np.sin(s * 0.4 + dust_ph), -0.12 * s + 0 * dust_ph, 0.2 * np.cos(s * 0.3 + dust_ph)])
        Ps.append(Dp); Cs.append(np.broadcast_to(WARM, (ND, 3))); Ws.append(np.full(ND, 0.9) * (1 - sm(T_HIT, T_DOWN + 0.8, s)))
    ign = sm(T_THREE - 0.15 + g_r * 0.07, T_THREE + 0.35 + g_r * 0.07, s)   # ignition ripples outward
    w = g_w * (1.4 * np.exp(-g_r / 1.1) * (0.6 + 0.4 * sm(0, 0.8, s)) + (1 - np.exp(-g_r / 1.1)) * ign)
    col = g_col.copy()
    if s < T_HIT:
        P = galaxy_pos(s)
        if T_TWO <= s < T_ONE + 0.4:                                        # foil sheen sweeps the plane
            c = -12 + 24 * sm(T_TWO, T_TWO + 1.2, s)
            band = np.exp(-(((P[:, 0] * 0.8 + (P[:, 1] - 5) * 0.6) - c) / 0.8) ** 2)
            w = w * (1 + 3.0 * band); col = col * (1 - 0.5 * band[:, None]) + np.array([0.75, 1.0, 0.95]) * 0.5 * band[:, None]
        w = w * (1 + 1.4 * sm(T_ONE, T_ONE + 0.75, s))                     # the line burns brighter
        Ps.append(P); Cs.append(col); Ws.append(w)
    else:
        a = s - T_HIT
        Pb = L_HIT[BACK] + (S_BACK - L_HIT[BACK]) * eo(T_HIT, T_HIT + 2.8, s)
        Ps.append(Pb); Cs.append(col[BACK]); Ws.append(w[BACK] * (0.9 + 1.5 * np.exp(-a * 1.8)))
        Pf = L_HIT[FLY] + V_FLY * a
        Ps.append(Pf); Cs.append(col[FLY]); Ws.append(w[FLY] * 2.0 * np.exp(-a * 1.3))
        L = L_HIT[FORM]
        tgt = page_world(TGT_UV[:, 0], TGT_UV[:, 1], s) + np.array([0, 0, 0.03])
        ef = eio(T_LOAD, T_DOWN + 0.15, s - form_delay)
        arc = np.sin(np.pi * ef)[:, None] * np.array([0, 0.6, 1.8])
        Pform = L + (tgt - L) * ef[:, None] + arc
        Ps.append(Pform); Cs.append(np.broadcast_to(GOLD, (NF, 3)))
        Ws.append(g_w[FORM] * 2.2 * (1 + 0.8 * np.exp(-a * 3)) * (1 - sm(T_DOWN + 0.1, T_DOWN + 0.8, s)))
        if s > T_HIT + 0.3:                                                 # frayed edge motes
            age = ((s - T_HIT) / M_LIFE + m_ph) % 1.0 * M_LIFE
            ww = np.sin(np.pi * age / M_LIFE) * 0.5 * sm(T_HIT + 0.3, T_LOAD, s)
            mp = page_world(m_u + m_du * age, m_v + m_dv * age, s) + np.column_stack([0 * age, 0 * age, m_dz * age])
            Ps.append(mp); Cs.append(np.broadcast_to(WARM * 0.95, (NM, 3))); Ws.append(ww)
    return np.concatenate(Ps), np.concatenate([np.asarray(c, np.float32) for c in Cs]), np.concatenate(Ws)

def embers(s):
    P, alive, e = ember_pos(s)
    flick = 0.75 + 0.25 * np.sin(s * 9 + e_ph * 5)
    return P, e_w * alive * sm(0, 0.6, s - e_ts) * flick * (1 + 0.9 * beat_pulse(s)) * (1 - 0.6 * e)

def splat(buf, x, y, c, w):
    ok = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1) & (w > 1e-5)
    x, y, c, w = x[ok], y[ok], c[ok], w[ok]
    x0 = np.floor(x).astype(np.int64); y0 = np.floor(y).astype(np.int64); fx = x - x0; fy = y - y0
    base = (y0 * W + x0) * 3
    ww = np.concatenate([w * (1 - fx) * (1 - fy), w * fx * (1 - fy), w * (1 - fx) * fy, w * fx * fy])
    ii = np.concatenate([base, base + 3, base + 3 * W, base + 3 * W + 3])
    cc = np.tile(c, (4, 1))
    ii = np.concatenate([ii, ii + 1, ii + 2]); ww = np.concatenate([ww * cc[:, 0], ww * cc[:, 1], ww * cc[:, 2]])
    buf.reshape(-1)[:] += np.bincount(ii, ww, minlength=H * W * 3)

SIGMAS = [0, 1.4, 3.2, 7.0]
def dof_layers(x, y, z, c, w, focus, bufs):
    coc = 26.0 * np.abs(1 / np.maximum(z, 0.3) - 1 / focus) * (focus / 12.0)
    w = w * (z > 0.3) * np.clip(9.0 / np.maximum(z, 0.3), 0.3, 1.8) ** 0.5
    edges = [0, 1.3, 3.2, 7.5, 1e9]
    for k in range(4):
        m = (coc >= edges[k]) & (coc < edges[k + 1])
        if m.any(): splat(bufs[k], x[m], y[m], c[m], w[m] * (1 + 0.25 * k))

def collapse(bufs):
    out = bufs[0].copy()
    for k in range(1, 4): out += cv2.GaussianBlur(bufs[k], (0, 0), SIGMAS[k])
    return out

def glowed(L):
    small = cv2.resize(L, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    g = cv2.GaussianBlur(small, (0, 0), 4) * 0.45 + cv2.GaussianBlur(small, (0, 0), 14) * 0.30
    return L + cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)

def tone(L): return 1 - np.exp(-L * 1.25)
def screen(a, b): return a + b * (1 - a)

# nebula: faint low-frequency colour at infinity, shifts with camera rotation
nb = rng.random((120, 200, 3)).astype(np.float32)
nb = cv2.GaussianBlur(nb, (0, 0), 7); nb = norm01(nb) ** 2.5
NEB = cv2.resize(nb * np.array([0.05, 0.035, 0.09], np.float32), (800, 480), interpolation=cv2.INTER_CUBIC)

# ---------------------------------------------------------------- frame
SUBS = [0.0, 1 / 180, 2 / 180, 3 / 180]         # 180-degree shutter at 30 fps
vy, vx = np.mgrid[0:H, 0:W]
VIGN = (1 - 0.5 * (((vx - W / 2) / (W / 1.15)) ** 2 + ((vy - H / 2) / (H / 1.05)) ** 2))[..., None].astype(np.float32)
BG_Y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
BG = (np.array([0.012, 0.014, 0.030]) * (1 - BG_Y) + np.array([0.022, 0.018, 0.040]) * BG_Y).astype(np.float32)

def frame_at(t):
    s = tau(t); frozen = T_FREEZE0 <= t < T_FREEZE1
    cam = camera(t)
    page_on = s >= T_HIT
    back = [np.zeros((H, W, 3), np.float32) for _ in range(4)]
    front = [np.zeros((H, W, 3), np.float32) for _ in range(4)]
    acc = {True: [], False: []}
    EMB = np.zeros((H, W, 3), np.float32)                      # front?, list of (x, y, z, C, W)
    for dt in SUBS:
        ss = s if frozen else max(0.0, s - dt)
        P, C, Wt = all_particles(ss, t - dt)
        x, y, z = project(P, camera(t - dt))
        Wt = Wt / len(SUBS)
        fr = page_side(P, ss) > -0.02 if page_on else np.ones(len(P), bool)
        for side in (True, False):
            m = fr if side else ~fr
            acc[side].append((x[m], y[m], z[m], C[m], Wt[m]))
        if ss > T_DOWN:                              # embers get their own soft, bright layer
            Pe, we = embers(ss); xe, ye, _ = project(Pe, camera(t - dt))
            splat(EMB, xe, ye, e_col, we * 6.0 / len(SUBS))
    # time made visible: during the silence each ember's recent path hangs in the air
    hist = 2.4 * sm(T_FREEZE0, T_FREEZE1 - 0.15, t) * (1 - sm(T_FREEZE1, T_FREEZE1 + 0.4, t))
    if hist > 0.01:
        for j in range(1, 40):
            q = j / 40
            Pq, alive, _ = ember_pos(T_FREEZE0 - q * hist)
            x, y, z = project(Pq, cam)
            splat(EMB, x, y, e_col, e_w * alive * 0.35 * (1 - q) ** 1.5)
    for side, bufs in ((True, front), (False, back)):
        if acc[side]:
            dof_layers(*[np.concatenate([a[k] for a in acc[side]]) for k in range(5)], cam[2], bufs)
    Lb, Lf = collapse(back), collapse(front)
    Lf += cv2.GaussianBlur(EMB, (0, 0), 1.3) + cv2.GaussianBlur(EMB, (0, 0), 5) * 0.8
    # constellation lines draw themselves after the silence
    if s > T_FREEZE0 + 0.9:
        sx, sy_, sz = project(STAR_P, cam)
        lay = np.zeros((H, W), np.float32)
        for ci, segs in enumerate(SEGS):
            for j, (i0, i1) in enumerate(segs):
                u = float(np.clip((s - (T_FREEZE0 + 1.2 + ci * 0.55 + j * 0.2)) / 0.3, 0, 1))
                if u <= 0 or min(sz[i0], sz[i1]) < 0.5: continue
                p0 = np.array([sx[i0], sy_[i0]]); p1 = p0 + (np.array([sx[i1], sy_[i1]]) - p0) * u
                cv2.line(lay, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), 0.5, 1, cv2.LINE_AA, 2)
        lit = sm(T_FREEZE0 + 0.9, T_FREEZE0 + 1.6, s)
        for i in range(len(STAR_P)):                                         # four-point flares
            if sz[i] < 0.5: continue
            c = (int(sx[i] * 4), int(sy_[i] * 4)); r = int(4 * 9 * lit)
            cv2.line(lay, (c[0] - r, c[1]), (c[0] + r, c[1]), 0.25, 1, cv2.LINE_AA, 2)
            cv2.line(lay, (c[0], c[1] - r), (c[0], c[1] + r), 0.25, 1, cv2.LINE_AA, 2)
        Lf += cv2.GaussianBlur(lay, (3, 3), 0.6)[..., None] * np.array([0.85, 0.95, 1.0], np.float32)
    # background: sky gradient + nebula at infinity
    yaw, pitch = CAM(t)[0], CAM(t)[1]
    ox = int(np.clip(400 - 160 + yaw * 3.2 - 160, 0, 800 - 320)); oy = int(np.clip(240 - 90 - pitch * 3.2, 0, 480 - 180))
    neb = cv2.resize(NEB[oy:oy + 180, ox:ox + 320], (W, H), interpolation=cv2.INTER_CUBIC)
    frame = BG + neb * sm(0.0, 3.0, t)
    frame = screen(frame, tone(glowed(Lb)))
    if page_on:
        quad = page_world(np.array([-8, 8, 8, -8.]), np.array([0, 0, 10, 10.]), s)
        px, py, pz = project(quad, cam)
        dst = np.stack([px, py], 1).astype(np.float32)
        area = 0.5 * abs(np.dot(px, np.roll(py, 1)) - np.dot(py, np.roll(px, 1)))
        if pz.min() > 0.3 and area > 40:
            src = np.array([[0, PH], [PW, PH], [PW, 0], [0, 0]], np.float32)
            M = cv2.getPerspectiveTransform(src, dst)
            rgba = np.dstack([page_texture(s), ALPHA])
            wp = cv2.warpPerspective(rgba, M, (W, H), flags=cv2.INTER_LINEAR)
            mask = wp[..., 3:]
            glow_amt = 0.10 + 0.35 * np.exp(-(s - T_HIT) * 1.5)
            halo = cv2.GaussianBlur(cv2.resize(mask, (W // 4, H // 4)), (0, 0), 10)
            halo = cv2.resize(halo, (W, H))[..., None] * glow_amt * WARM
            frame = frame + halo * (1 - mask)
            frame = frame * (1 - mask) + wp[..., :3] * mask
    frame = screen(frame, tone(glowed(Lf)))
    # hit flash, downbeat breath, freeze tint, vignette, grain
    if t >= T_HIT: frame = frame + 0.55 * np.exp(-(t - T_HIT) * 6.5) * WARM
    if t >= T_DOWN: frame = frame + 0.10 * np.exp(-(t - T_DOWN) * 5) * WARM
    if frozen:
        k = sm(T_FREEZE0, T_FREEZE0 + 0.25, t) * (1 - sm(T_FREEZE1 - 0.1, T_FREEZE1, t))
        g = frame.mean(-1, keepdims=True); frame = (frame * (1 - 0.5 * k) + g * np.array([0.92, 0.98, 1.08]) * 0.5 * k) * (1 - 0.12 * k)
    frame = frame * VIGN
    frame = frame + np.random.default_rng(int(round(s * FPS))).normal(0, 0.010, (H, W, 1)).astype(np.float32)
    return (np.clip(frame, 0, 1) ** (1 / 1.06) * 255).astype(np.uint8)

def work(args):
    out, i, t = args
    cv2.imwrite(f'{out}/f{i:05d}.png', cv2.cvtColor(frame_at(t), cv2.COLOR_RGB2BGR))

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    if '--sheet' in sys.argv:
        ts = [0.4, 1.6, 2.8, 3.8, 4.9, 5.5, 5.75, 6.1, 6.9, 7.8, 8.6, 11.0, 13.9, 15.3, 17.5, 20.5]
        with Pool(4) as p: frames = p.map(frame_at, ts)
        tiles = [cv2.resize(f, (W // 2, H // 2), interpolation=cv2.INTER_AREA) for f in frames]
        for tt, im in zip(ts, tiles):
            cv2.putText(im, f'{tt:.2f}s', (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 80, 80), 2)
        while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
        rows = [np.concatenate(tiles[i:i + 4], 1) for i in range(0, len(tiles), 4)]
        cv2.imwrite(f'{out}/sheet.jpg', cv2.cvtColor(np.concatenate(rows, 0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
        sys.exit()
    t0, t1 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (0.0, 21.0)
    jobs = [(out, i, t0 + i / FPS) for i in range(int(round((t1 - t0) * FPS)))]
    with Pool(4) as p:
        for k, _ in enumerate(p.imap_unordered(work, jobs, chunksize=4)):
            if k % 60 == 0: print(k, '/', len(jobs), flush=True)
