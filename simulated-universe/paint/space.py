"""The space layer: my own 3D shots between the painted key frames.

A small particle universe in world units (Earth radius 1): the real Earth at night (34k real cities
from geonamescache, land from global-land-mask), cold stars, the human traces, light-shells, the
lattice at the edge of the light, and the sheet. It follows the film's colour script: warm is human
and only human (cities, traces, signals, keys pressed); stars, the lattice and the sheet are cold. The
backdrop is the painted space of BG0a, so these shots sit in the same world as the key frames.
Dimension is literal here: a plane seen edge-on is a hairline, a sphere unrolls into a plane, a plane
collapses into a line, a line into a point, and the sheet flattens the Earth.
"""
import os, numpy as np, cv2
from PIL import Image

W, H = 1280, 720
F = 1100.0                                                          # focal length, px
HERE = os.path.dirname(os.path.abspath(__file__))
C_WARM = np.array([1.0, 0.74, 0.42], np.float32); C_WHITE = np.array([1.0, 0.90, 0.78], np.float32)
C_LAND = np.array([0.20, 0.26, 0.38], np.float32); C_AIR = np.array([0.35, 0.55, 1.0], np.float32)
C_STAR = np.array([0.70, 0.78, 1.0], np.float32); C_GRID = np.array([0.55, 0.65, 0.88], np.float32)
PAPER = np.array([0.93, 0.90, 0.83], np.float32); OCHRE = np.array([0.86, 0.50, 0.18], np.float32)

def ss(a, b, x):
    x = np.clip((np.asarray(x, np.float64) - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def nrm(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)

# ---------------------------------------------------------------- backdrop: the painted space of BG0a
_bg = np.array(Image.open(f'{HERE}/../assets/kv/BG0a.png').convert('RGB')).astype(np.float32)[:230] / 255
BACK = cv2.GaussianBlur(cv2.resize(_bg, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 3)
BACK = BACK * (0.85 + 0.15 * np.linspace(1, 0.7, H)[:, None, None])

# ---------------------------------------------------------------- the real Earth at night
rng = np.random.default_rng(7)
def unit(lat, lon): return np.stack([np.cos(lat) * np.sin(lon), np.sin(lat), np.cos(lat) * np.cos(lon)], -1)
import geonamescache
from global_land_mask import globe as _globe
_c = list(geonamescache.GeonamesCache().get_cities().values())
_lat = np.radians([c['latitude'] for c in _c]); _lon = np.radians([c['longitude'] for c in _c])
_pop = np.array([max(c['population'], 15000) for c in _c], float)
NC = 52000
_w = _pop ** 0.6; _pk = rng.choice(len(_c), NC, p=_w / _w.sum())
_sp = np.radians(0.04 + 0.05 * (_pop[_pk] / 1e5) ** 0.3)
CITY_LAT = _lat[_pk] + rng.normal(0, 1, NC) * _sp
CITY_LON = _lon[_pk] + rng.normal(0, 1, NC) * _sp / np.maximum(np.cos(_lat[_pk]), 0.2)
_cl = np.degrees(np.arcsin(rng.uniform(-1, 1, 90000))); _co = rng.uniform(-180, 180, 90000)
_k = _globe.is_land(_cl, _co) & (_cl > -60)
LAND_LAT, LAND_LON = np.radians(_cl[_k][:20000]), np.radians(_co[_k][:20000])
CITY = unit(CITY_LAT, CITY_LON).astype(np.float32)
LAND = unit(LAND_LAT, LAND_LON).astype(np.float32)
AIR = (nrm(rng.normal(0, 1, (9000, 3))) * 1.03).astype(np.float32)
CITY_COL = np.where((rng.random(NC) < 0.3)[:, None], C_WHITE, C_WARM).astype(np.float32)
CITY_W = rng.uniform(0.4, 1.0, NC).astype(np.float32)
FIRST = unit(np.radians(-3.0), np.radians(35.0))                     # the first fire: East Africa
CITY_D = np.arccos(np.clip(CITY @ FIRST, -1, 1))                     # each light's distance from it
BIG = np.argsort(-_pop)[:400]                                        # the largest real cities
BIG_U = unit(_lat[BIG], _lon[BIG]).astype(np.float32)

# ---------------------------------------------------------------- the rest of the universe
STARS = (nrm(rng.normal(0, 1, (9000, 3))) * 500).astype(np.float32)
STAR_W = (rng.uniform(0.03, 0.35, 9000) ** 1.6).astype(np.float32)
def fib_sphere(n):
    i = np.arange(n) + 0.5; phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1).astype(np.float32)
SHELL = fib_sphere(6000); SHELL_S = fib_sphere(1500)

# ---------------------------------------------------------------- camera and splatting
def look(eye, target, up=(0, 1, 0)):
    eye = np.asarray(eye, np.float64); f = nrm(np.asarray(target, np.float64) - eye)
    r = nrm(np.cross(f, up)); u = np.cross(r, f)
    return eye, np.stack([r, u, f])

def project(P, cam, shift=(0.0, 0.0)):
    eye, R = cam; Q = (np.asarray(P, np.float64) - eye) @ R.T
    z = Q[:, 2]; zs = np.maximum(z, 1e-3)
    return W / 2 + shift[0] + F * Q[:, 0] / zs, H / 2 + shift[1] - F * Q[:, 1] / zs, z

class Film:
    """Accumulates points into three depth-of-field layers (fine, soft, near) and composites them."""
    def __init__(self): self.acc = [np.zeros((3, H * W)) for _ in range(3)]
    def add(self, P, col, w, cam, size=0.012, shift=(0.0, 0.0), minw=1e-4):
        xs, ys, z = project(P, cam, shift)
        w = np.broadcast_to(np.asarray(w, np.float64), (len(xs),))
        col = np.broadcast_to(np.asarray(col, np.float64), (len(xs), 3))
        ok = (z > 0.02) & (w > minw) & (xs > -2) & (xs < W + 1) & (ys > -2) & (ys < H + 1)
        xs, ys, z, w, col = xs[ok], ys[ok], z[ok], w[ok], col[ok]
        px = size * F / z                                             # apparent size in px
        cls = np.digitize(px, [1.6, 4.5])
        w = w * np.array([1.0, 7.0, 55.0])[cls]                       # each blur layer keeps the points' surface brightness
        x0 = np.floor(xs).astype(np.int64); y0 = np.floor(ys).astype(np.int64); fx = xs - x0; fy = ys - y0
        xi = np.concatenate([x0, x0 + 1, x0, x0 + 1]); yi = np.concatenate([y0, y0, y0 + 1, y0 + 1])
        bw = np.concatenate([(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy]) * np.tile(w, 4)
        cl = np.tile(cls, 4); cc = np.tile(col, (4, 1))
        k = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
        for L in range(3):
            m = k & (cl == L)
            if not m.any(): continue
            idx = yi[m] * W + xi[m]
            for c in range(3): self.acc[L][c] += np.bincount(idx, cc[m, c] * bw[m], minlength=H * W)
        return self
    def image(self, exposure=1.0, back=BACK, halo=0.30, paper=None, ink=None):
        a = [x.reshape(3, H, W).transpose(1, 2, 0).astype(np.float32) for x in self.acc]
        acc = cv2.GaussianBlur(a[0], (0, 0), 0.6) + cv2.GaussianBlur(a[1], (0, 0), 1.6) + cv2.GaussianBlur(a[2], (0, 0), 4.5)
        acc = (acc + cv2.GaussianBlur(acc, (0, 0), 6) * halo) * exposure
        lit = 1 - np.exp(-acc)
        bg = back.copy()
        if paper is not None:                                         # the flattened world lies on paper
            pm = paper[..., None]
            bg = bg * (1 - pm) + PAPER * (0.97 + 0.06 * (cv2.GaussianBlur(np.random.default_rng(3).random((H, W)).astype(np.float32), (0, 0), 1.2) - 0.5))[..., None] * pm
            if ink is not None:
                im = np.clip(ink * exposure, 0, 1)[..., None] * pm
                return np.clip(bg * (1 - im) + OCHRE * im + lit * (1 - bg) * (1 - pm), 0, 1)
            return np.clip(bg + lit * (1 - bg) * (1 - pm), 0, 1)
        return np.clip(bg + lit * (1 - bg), 0, 1)

def earth(film, cam, P_city=None, k_city=1.0, gain=1.0, land=True, air=True, flick_s=None, shift=(0.0, 0.0), rot=0.0):
    """The Earth at night: cities warm, land and air cold, the far side hidden."""
    ca, sa = np.cos(rot), np.sin(rot); Ry = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]], np.float32)
    eye = cam[0]
    def facing(P):
        v = nrm(eye - P); return (nrm(P) * v).sum(1)
    Pc = CITY @ Ry.T if P_city is None else P_city
    fc = facing(CITY @ Ry.T)
    wc = CITY_W * ss(-0.05, 0.10, fc) * k_city * gain
    if flick_s is not None: wc = wc * (0.85 + 0.15 * np.sin(flick_s * 5 + CITY_LON * 40 + CITY_LAT * 17))
    film.add(Pc, CITY_COL, wc * 0.5, cam, shift=shift)
    if land:
        Pl = LAND @ Ry.T; film.add(Pl, C_LAND, 0.16 * gain * ss(-0.05, 0.10, facing(Pl)), cam, shift=shift)
    if air:
        Pa = AIR @ Ry.T; fa = facing(Pa)
        film.add(Pa, C_AIR, 0.6 * gain * np.clip(1 - np.abs(fa), 0, 1) ** 4 * (fa > -0.15), cam, shift=shift)
    return film

def limb(U, centre, r, eye):
    """Weight for a sphere of points so it reads as its silhouette ring: a light-cone seen from outside."""
    v = nrm(np.asarray(eye) - (centre + U * r)); return np.clip(1 - np.abs((U * v).sum(1)), 0, 1) ** 3

def stars(film, cam, k=1.0, shift=(0.0, 0.0)): return film.add(STARS + cam[0], C_STAR, STAR_W * k, cam, shift=shift)

# ---------------------------------------------------------------- 0:30.9 the first fire becomes the network; the dark forest
def s_network(t, fx, fy):
    u = float(ss(30.93, 33.2, t))
    D = lerp(1.32, 6.0, u ** 0.8) * lerp(1.0, 7.5, float(ss(33.2, 38.4, t)))
    tgt = FIRST * (1 - u)
    eye = nrm(FIRST + np.array([0.18, 0.30, 0.0])) * D
    cam = look(eye, tgt)
    x0, y0, _ = project(FIRST[None], cam)
    sh = ((fx - x0[0]) * (1 - ss(30.93, 31.9, t)), (fy - y0[0]) * (1 - ss(30.93, 31.9, t)))
    k = ss(31.0 + CITY_D * 0.62, 31.35 + CITY_D * 0.62, t)          # out of Africa, across the world
    k = np.maximum(k, (CITY_D < 0.015) * 1.0)
    film = stars(Film(), cam, 0.8, sh)
    earth(film, cam, k_city=k, gain=lerp(1.0, 0.55, float(ss(33.2, 38.4, t))), flick_s=min(t, 33.2), shift=sh)
    film.add(FIRST[None] * 1.002, C_WARM, 12.0 * (1 - 0.85 * ss(31.2, 32.4, t)), cam, size=0.004, shift=sh)   # the first fire
    return film.image(exposure=lerp(1.4, 1.0, u))

# ---------------------------------------------------------------- 0:51.3 the speed of light is a wall
WALL_R = 9.0
def s_wall(t):
    cam = look((6, 7, 30), (0, 0, 0))
    film = stars(Film(), cam, 0.7)
    earth(film, cam, gain=1.0, flick_s=t)
    r = min(WALL_R, 1.05 + (WALL_R - 1.05) * max(0.0, t - 51.45) / 2.1)   # constant speed, then it stops
    if t > 51.45: film.add(SHELL * r, C_WARM, 0.12 + 0.9 * limb(SHELL, 0, r, cam[0]), cam)
    film.add(SHELL * (WALL_R + 0.06), C_GRID, (0.05 + 0.5 * limb(SHELL, 0, WALL_R, cam[0])) * ss(53.45, 53.9, t), cam)   # the wall, seen only where light reaches it
    return film.image()

# ---------------------------------------------------------------- 0:57.2 the Planck scale: the lattice under the painting
_g = np.stack(np.meshgrid(np.arange(-15, 16), np.arange(-8, 9), np.arange(0, 41), indexing='ij'), -1).reshape(-1, 3).astype(np.float32)
LATTICE = _g; LAT_WARM = _g[rng.choice(len(_g), 40, replace=False)]
def s_lattice(t):
    z = (t - 57.2) * 1.1
    cam = look((0.35, 0.2, -2 + z), (0.3, 0.1, 10 + z))
    film = Film()
    dz = LATTICE[:, 2] - (-2 + z)
    film.add(LATTICE, C_GRID, 1.0 * np.exp(-np.maximum(dz, 0) / 9), cam, size=0.02)
    dzw = LAT_WARM[:, 2] - (-2 + z)
    film.add(LAT_WARM, C_WARM, 1.2 * np.exp(-np.maximum(dzw, 0) / 12), cam, size=0.03)
    return film.image(back=BACK * 0.8)

# ---------------------------------------------------------------- 1:13 signals into the dark forest
SIG = BIG_U[[i for i in range(len(BIG_U)) if (BIG_U[i] @ nrm(np.array([0.55, 0.45, 0.70]))) > 0.35][:8]]
def s_signals(t, beats):
    D = lerp(3.0, 8.5, float(ss(73.0, 78.4, t)))
    eye = nrm(np.array([0.55, 0.45, 0.70])) * D
    cam = look(eye, (0, 0, 0))
    film = stars(Film(), cam, 0.8)
    earth(film, cam, flick_s=t)
    for p, b in zip(SIG, beats):
        if t < b: continue
        r = 0.04 + 1.05 * (t - b)
        film.add(p + SHELL_S * r, C_WARM, 0.9 * limb(SHELL_S, p, r, cam[0]) * np.exp(-r * 0.35), cam)
        film.add(p[None] * 1.001, C_WHITE, 2.0 * np.exp(-(t - b) * 3), cam)
    return film.image(exposure=lerp(0.55, 0.9, float(ss(73.0, 78.4, t))))

# ---------------------------------------------------------------- 1:26.5 the sheet; 1:33.7 everything falls flat
N_SHEET = nrm(np.array([0.12, 1.0, 0.05]))
_a = nrm(np.cross(N_SHEET, [0, 0, 1.0])); _b = np.cross(N_SHEET, _a)
_uv = np.stack(np.meshgrid(np.linspace(-35, 35, 150), np.linspace(-35, 35, 150)), -1).reshape(-1, 2)
SHEET = (_uv[:, :1] * _a + _uv[:, 1:] * _b).astype(np.float32)
def sheet_pts(h): return SHEET + N_SHEET * h

def s_sheet(t):
    h = lerp(7.0, 1.0, float(ss(87.0, 93.7, t)))
    lift = 2.6 * float(ss(90.0, 93.7, t))
    eye = np.array([0.0, 0.0, 14.0]); eye = eye + N_SHEET * (h - eye @ N_SHEET + lift)  # starts exactly edge-on
    cam = look(eye, (0, 0.55 * h, 0))
    film = stars(Film(), cam, 0.7)
    earth(film, cam, flick_s=t)
    film.add(sheet_pts(h), C_GRID, 0.22 * ss(86.6, 87.6, t), cam, size=0.02)
    return film.image()

H0 = 1.0
TOUCH = N_SHEET * H0
def flatten(P, t, t0=93.75, dur=2.2):
    """Each point collapses onto the sheet when its turn comes (the top first) and spreads in its plane."""
    tf = t0 + (1 - P @ N_SHEET) / 2 * dur
    q = ss(tf, tf + 0.35, t)[:, None]
    on = P - N_SHEET * ((P @ N_SHEET) - H0)[:, None]
    Pf = TOUCH + (on - TOUCH) * 1.9
    return P * (1 - q) + Pf * q, q[:, 0]

def s_flat(t):
    v = float(ss(94.2, 97.2, t)); lift = lerp(2.6, 12.0, v)
    eye = np.array([0.0, 0.0, lerp(14.0, 6.0, v)]); eye = eye + N_SHEET * (H0 - eye @ N_SHEET + lift)
    cam = look(eye, lerp(np.array([0, 0.55, 0]), TOUCH * 0.5, v))
    film = stars(Film(), cam, 0.6)
    Pc, qc = flatten(CITY, t)
    film.add(sheet_pts(H0), C_GRID, 0.22, cam, size=0.02)
    fc = (nrm(CITY) * nrm(eye - CITY)).sum(1)
    vis = np.maximum(ss(-0.05, 0.10, fc), qc)                       # flat, nothing is hidden behind anything
    film.add(Pc, CITY_COL, CITY_W * vis * 0.5, cam)
    Pl, ql = flatten(LAND, t)
    film.add(Pl, C_LAND, 0.10 * np.maximum(ss(-0.05, 0.10, (nrm(LAND) * nrm(eye - LAND)).sum(1)), ql), cam)
    pk = float(ss(95.9, 97.3, t))
    if pk <= 0: return film.image()
    xs, ys, z = project(Pc[qc > 0.98], cam)                         # the flattened world becomes a drawing on paper
    mask = np.zeros((H, W), np.float32)
    if len(xs) > 3:
        pts = np.stack([xs, ys], 1); pts = pts[(z > 0) & (np.abs(pts) < 5000).all(1)]
        if len(pts) > 3: cv2.fillConvexPoly(mask, cv2.convexHull(pts.astype(np.float32)).astype(np.int32), 1.0)
    mask = cv2.GaussianBlur(mask, (0, 0), 8) * pk
    ink = Film().add(Pc, CITY_COL, CITY_W * vis * 0.5, cam)
    a = ink.acc[0].reshape(3, H, W).mean(0).astype(np.float32)
    return film.image(paper=mask, ink=cv2.GaussianBlur(a, (0, 0), 0.7) * 1.6)

# ---------------------------------------------------------------- 1:50.6 past the stars; the room at the end of the light
FLY_DIR = nrm(np.array([0.2, 0.35, -1.0]))
_fa = nrm(np.cross(FLY_DIR, [0, 1, 0])); _fb = np.cross(_fa, FLY_DIR)
def _chains(n, pts, r0, r1, spread, step):
    out = []
    for _ in range(n):
        d = rng.uniform(r0, r1); c = FLY_DIR * d + _fa * rng.normal(0, spread) + _fb * rng.normal(0, spread)
        v = nrm(rng.normal(0, 1, 3))
        for _ in range(pts):
            v = nrm(v + rng.normal(0, 0.35, 3)); c = c + v * step; out.append(c.copy())
    return np.array(out, np.float32)
TRACES = _chains(60, 26, 2.5, 22, 2.2, 0.22)                         # human traces: the warm constellation
_d = rng.uniform(4, 330, 16000); _r = rng.uniform(1.5, 70, 16000) * (0.3 + _d / 330); _th = rng.uniform(0, 2 * np.pi, 16000)
FLY_STARS = (FLY_DIR * _d[:, None] + _fa * (_r * np.cos(_th))[:, None] + _fb * (_r * np.sin(_th))[:, None]).astype(np.float32)
FLY_SW = (rng.uniform(0.05, 0.6, 16000) ** 1.5).astype(np.float32)
EDGE_D = 360.0                                                      # the end of the light
_gu = np.stack(np.meshgrid(np.arange(-48, 49) * 1.0, np.arange(-27, 28) * 1.0), -1).reshape(-1, 2)
KEYS = (FLY_DIR * EDGE_D + _fa * _gu[:, :1] + _fb * _gu[:, 1:]).astype(np.float32)

def s_fly(t):
    u = float(ss(110.7, 116.9, t))
    d = 1.6 * (EDGE_D * 0.93 / 1.6) ** u
    eye = FLY_DIR * d; cam = look(eye, eye + FLY_DIR, up=_fb)
    film = Film()
    film.add(TRACES, C_WARM, 0.9, cam, size=0.02)
    film.add(FLY_STARS, C_STAR, FLY_SW, cam, size=0.05)
    film.add(KEYS, C_GRID, 0.8 * ss(115.0, 116.6, t), cam, size=0.05)
    return film.image()

rK = np.random.default_rng(8)
CON_CAM = look(FLY_DIR * (EDGE_D - 9) + _fb * -6 + _fa * -3, FLY_DIR * EDGE_D + _fb * 2 + _fa * 4, up=_fb)
_kx, _ky, _kz = project(KEYS, CON_CAM)
KEY_VIS = np.nonzero((_kx > 80) & (_kx < W - 80) & (_ky > 60) & (_ky < H - 60) & (_kz > 10) & (_kz < 30))[0]
def s_console(t, beats):
    cam = CON_CAM
    film = Film()
    film.add(KEYS, C_GRID, 0.5, cam, size=0.05)
    idx = KEY_VIS[np.random.default_rng(8).integers(len(KEY_VIS), size=len(beats) * 2)]
    for j, b in enumerate(beats):                                    # keys pressed; no hand on them
        if t >= b:
            for i in idx[2 * j:2 * j + 2]: film.add(KEYS[i][None], C_WARM, 3.0 * np.exp(-(t - b) * 1.6) + 0.35, cam, size=0.08)
    return film.image(back=BACK * 0.85)

def s_no_gods(t):
    """From the edge, looking back: the only light out here is the one people made."""
    eye = FLY_DIR * (EDGE_D - 3) + _fb * 1.2
    cam = look(eye, (0, 0, 0), up=_fb)
    film = Film()
    film.add(KEYS, C_GRID, 0.22, cam, size=0.05)
    film.add(FLY_STARS, C_STAR, FLY_SW * 0.7, cam, size=0.05)
    film.add(np.zeros((1, 3), np.float32), C_WARM, 7.0, cam, size=0.4)
    return film.image(back=BACK * 0.9)

# ---------------------------------------------------------------- 2:38.8 the whole Earth and its threads; the breath
THR = CITY[rng.choice(NC, 6000, replace=False)]
THR_L = rng.uniform(0.03, 0.35, 6000).astype(np.float32)
def s_threads(t):
    eye = nrm(np.array([0.3, 0.35, 1.0])) * 3.4; cam = look(eye, (0, 0, 0))
    grow = float(ss(158.8, 159.8, t)); breath = float(ss(160.1, 160.5, t))
    film = stars(Film(), cam, 0.7 * (1 - 0.6 * breath))
    earth(film, cam, gain=1.0 - 0.6 * breath, flick_s=min(t, 160.1))
    fc = ss(-0.05, 0.10, (nrm(THR) * nrm(eye - THR)).sum(1))
    for j in range(1, 7):                                            # each life's line: time as a direction
        film.add(THR * (1 + THR_L[:, None] * grow * j / 6), C_WARM, 0.035 * fc * (1 - 0.3 * breath), cam)
    return film.image(exposure=0.6)

# ---------------------------------------------------------------- 3:31 two dimensions... three... and one... still loading
_sub = rng.choice(NC, 26000, replace=False)
O_PLANE = np.stack([CITY_LON[_sub] / np.pi * 3.0, CITY_LAT[_sub] / (np.pi / 2) * 1.5, np.zeros(26000)], 1).astype(np.float32)
O_SPH = (CITY[_sub] * 1.35).astype(np.float32)
def s_outro(t):
    cam = look((0, 0, 7.5), (0, 0, 0))
    a = float(ss(211.35, 211.85, t)); b = float(ss(211.95, 212.25, t)); c = float(ss(212.25, 212.45, t))
    ang = 0.5 * (1 - a)                                              # it curls as it closes
    ca, sa = np.cos(ang), np.sin(ang); Ry = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]], np.float32)
    P = O_PLANE * (1 - a) + (O_SPH @ Ry.T) * a
    if a > 0:
        fc = ss(-0.1, 0.1, (nrm(P) * nrm(np.array([0, 0, 7.5]) - P)).sum(1)); w = 0.45 * (1 - a + a * fc)
    else: w = np.full(len(P), 0.45)
    P = P.copy(); P[:, 1] *= (1 - b); P[:, 2] *= (1 - b)              # and one: the line
    if b > 0: w = w * (1 - b) + 0.45 * b
    P[:, 0] *= (1 - c)                                               # the point
    film = Film().add(P, CITY_COL[_sub], w * (1 - 0.97 * c), cam)
    if c > 0:
        blink = 1.0 if t < 212.45 else 0.55 + 0.45 * np.cos(2 * np.pi * (t - 212.45) / 0.25)
        film.add(np.zeros((1, 3), np.float32), C_WARM, 2.5 * c * blink, cam, size=0.25)
    return film.image(exposure=1.0)
