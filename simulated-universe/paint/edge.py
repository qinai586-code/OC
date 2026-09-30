"""The edge of the world: the two witnesses sit on the page's edge above the painted human world.

Every shot here lives in one coordinate space, the pixels of SIT_BACK.png (1536x1024, the
drawn edge at y = 603). The painted world hangs below the edge, the sky is above it, and the
human traces travel through that same space. So a trace that rises past A in the
over-the-shoulder shot is the same trace that becomes a star in the wide shot.

  EDGE     5.62-8.45   the countdown's line is the edge; the world swings down beneath it; the
                       two witnesses draw themselves in (pencil -> flat colour -> painted)
  OTS      8.45-10.24  over A's shoulder: traces rise from the world toward her
  WIDE2   11.98-13.40  both of them, small, the traces rising past them
  SKY     14.45-17.70  the traces become the constellation above them

The trace vocabulary is deliberately small and repeated: lit windows, footprints, brief human
figures, and one warm lullaby glow.
"""
import os, json, numpy as np, cv2
from PIL import Image
import faces

W, H, FPS = 1280, 720, 30
HERE = os.path.dirname(os.path.abspath(__file__))
EDGE_Y, MID_X = 603.0, 768.0
T_HIT, T_DOWN, T_SIL0, T_SIL1 = 5.62, 7.55, 13.40, 14.45
WARM = np.array([1.0, 0.93, 0.80], np.float32); EMBER = np.array([1.0, 0.66, 0.32], np.float32)
BEATS = np.array(json.load(open(f'{HERE}/../timing/p0_beatmap.json'))['beats_s'])

def ss(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def eio(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return np.where(x < .5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)
def beat_pulse(s):
    b = BEATS[BEATS <= s]; return float(np.exp(-(s - b[-1]) * 7)) if len(b) else 0.0
def screen(a, b): return a + b * (1 - a)

# ---------------------------------------------------------------- the witnesses, with their unfinished stages
def _sit(name):
    rgb = np.array(Image.open(f'{HERE}/../assets/sit/{name}').convert('RGB')).astype(np.float32) / 255
    rgba = faces.cutout(rgb)
    band = slice(int(EDGE_Y) - 4, int(EDGE_Y) + 5)             # drop ChatGPT's drawn edge line where no one sits
    empty = (rgba[int(EDGE_Y) - 9, :, 3] < 0.5) & (rgba[int(EDGE_Y) + 9, :, 3] < 0.5)
    rgba[band, empty, 3] = 0
    return rgba
SB = _sit('SIT_BACK_TAIL.png')                                     # authoritative pair, with A's dragon tail
SBL = _sit('SIT_BACK_LOOKUP_TAIL.png')
def _stages(rgba):
    rgb, a = rgba[..., :3], rgba[..., 3:]
    px = (rgb.reshape(-1, 3) * 255).astype(np.float32); sel = a.reshape(-1) > 0.5
    _, lab, cen = cv2.kmeans(px[sel], 9, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
    q = px.copy(); q[sel] = cen[lab.ravel()]
    flat = cv2.bilateralFilter((q.reshape(rgb.shape) / 255).astype(np.float32), 7, 0.15, 5)
    comp = rgb * a + (1 - a)                                          # lines from the art on white, not the empty matte
    g = cv2.GaussianBlur((comp.mean(-1) * 255).astype(np.uint8), (3, 3), 0)
    inside = cv2.dilate((a[..., 0] > 0.3).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    line = np.clip(cv2.Canny(g, 40, 110) / 255.0 * 0.7 * inside + cv2.Canny((a[..., 0] * 255).astype(np.uint8), 50, 150) / 255.0, 0, 1)
    pencil = np.dstack([np.full(rgb.shape, 0.85, np.float32), cv2.GaussianBlur(line.astype(np.float32), (3, 3), 0.6) * 0.9])
    return {'painted': rgba, 'flat': np.dstack([flat * 0.85 + 0.15 * 0.9, a]).astype(np.float32), 'pencil': pencil}
ST = _stages(SB)
TY, TX = np.mgrid[0:SB.shape[0], 0:SB.shape[1]].astype(np.float32)
TAIL_W = (ss(615, 940, TY) * (TX < 520) * ss(560, 470, TX)).astype(np.float32)   # A's tail hangs below the edge
NOISE = cv2.GaussianBlur(np.random.default_rng(5).random(SB.shape[:2]).astype(np.float32), (0, 0), 7)
NOISE = (NOISE - NOISE.min()) / (NOISE.max() - NOISE.min())

# ---------------------------------------------------------------- the painted world below the edge (real city lights)
import geonamescache
_c = list(geonamescache.GeonamesCache().get_cities().values())
_lat = np.array([c['latitude'] for c in _c]); _lon = np.array([c['longitude'] for c in _c])
_pop = np.array([max(c['population'], 15000) for c in _c], float)
MX0, MX1, MY1 = -700.0, 2236.0, 1640.0                           # the world spans x MX0..MX1, y EDGE_Y..MY1
MS = 0.5                                                           # map texture at half the src resolution
mw, mh = int((MX1 - MX0) * MS), int((MY1 - EDGE_Y) * MS)
city_x = MX0 + (_lon + 180) / 360 * (MX1 - MX0); city_y = EDGE_Y + (90 - _lat) / 180 * (MY1 - EDGE_Y)
MAP = np.zeros((mh, mw), np.float32)
ix = np.clip(((city_x - MX0) * MS).astype(int), 0, mw - 1); iy = np.clip(((city_y - EDGE_Y) * MS).astype(int), 0, mh - 1)
np.add.at(MAP, (iy, ix), (_pop / 1e6) ** 0.5)
MAP = cv2.GaussianBlur(MAP, (0, 0), 0.8) * 1.5 + cv2.GaussianBlur(MAP, (0, 0), 4) * 1.2
rng = np.random.default_rng(9)
paper = 0.95 + 0.05 * cv2.GaussianBlur(rng.random((mh, mw)).astype(np.float32), (0, 0), 1.0)
MAPRGB = (np.array([0.10, 0.085, 0.08]) * paper[..., None] + (1 - np.exp(-MAP[..., None] * 1.6)) * np.array([1.0, 0.72, 0.40])).astype(np.float32)
MAPRGB[:6] += 0.25                                                 # the edge itself catches light
MAPRGB = np.concatenate([MAPRGB] * 3, 1); MX0 -= (MX1 - MX0); mw = MAPRGB.shape[1]   # the world wraps round

# ---------------------------------------------------------------- human traces
NT = 320
t_type = rng.choice(4, NT, p=[0.44, 0.30, 0.255, 0.005]); t_type[0] = 3        # exactly one lullaby glow
pick = rng.choice(len(_c), NT, p=(_pop ** 0.7) / (_pop ** 0.7).sum())
t_x0 = city_x[pick]; t_y0 = np.clip(city_y[pick], EDGE_Y + 30, MY1)
t_x0[0], t_y0[0] = 1080.0, 760.0                                   # the lullaby rises close to B
t_ts = rng.uniform(7.6, 13.2, NT); t_ts[0] = 8.3
t_vy = rng.uniform(110, 210, NT); t_vy[0] = 70
t_ph = rng.uniform(0, 2 * np.pi, NT); t_sz = rng.uniform(0.8, 1.3, NT)
t_front = rng.random(NT) < 0.3
STARS = np.array([[330, -430], [470, -300], [610, -470], [760, -330], [880, -520], [1010, -380], [1150, -470], [1260, -250], [900, -170]], float)
STAR_R = [4, 2, 3, 5, 2, 4, 2, 3, 2]
t_star = np.arange(NT) % len(STARS)
t_delay = rng.uniform(0, 0.8, NT)

def _sprite(kind, s=1.0):
    k = max(3, int(12 * s)); m = np.zeros((2 * k + 1, 2 * k + 1), np.float32); c = k
    if kind == 0:   # a lit window: a small warm pane with a cross bar
        w, h = max(2, int(3 * s)), max(3, int(4.5 * s))
        cv2.rectangle(m, (c - w, c - h), (c + w, c + h), 1.0, -1)
        cv2.line(m, (c - w, c), (c + w, c), 0.35, 1); cv2.line(m, (c, c - h), (c, c + h), 0.35, 1)
    elif kind == 1:  # footprints: a left and a right, one step apart
        for dx, dy in ((-int(2.5 * s), int(3 * s)), (int(2.5 * s), -int(3 * s))):
            cv2.ellipse(m, (c + dx, c + dy), (max(1, int(1.6 * s)), max(2, int(3.2 * s))), 0, 0, 360, 0.9, -1, cv2.LINE_AA)
    elif kind == 2:  # a brief human figure
        cv2.circle(m, (c, c - int(5 * s)), max(1, int(1.8 * s)), 1.0, -1, cv2.LINE_AA)
        cv2.ellipse(m, (c, c + int(1.5 * s)), (max(1, int(1.8 * s)), max(2, int(4.5 * s))), 0, 0, 360, 0.9, -1, cv2.LINE_AA)
    return m

def trace_pos(s, t):
    """src-space positions of the traces at story time s; after the silence they fly to the stars."""
    a = np.clip(s - t_ts, 0, None)
    x = t_x0 + 30 * np.sin(a * 0.9 + t_ph); y = t_y0 - t_vy * a
    alive = (s > t_ts) & (y > -900)
    if t >= T_SIL1:
        e = eio(0.4, 1.9, (t - T_SIL1) - t_delay)
        x = x + (STARS[t_star, 0] - x) * e; y = y + (STARS[t_star, 1] - y) * e
        alive = alive | (e > 0)
    return x, y, alive

# ---------------------------------------------------------------- shots
def _e(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
def shot(t):
    """Affine view of src space: scale sc and where the edge's centre lands (cx, cy)."""
    if t < 8.452:
        u = _e((t - T_HIT) / (8.452 - T_HIT))
        return dict(name='EDGE', sc=0.27 + 0.06 * u, cx=0.5 * W, cy=512 + (0.64 * H - 512) * u)
    if t < 10.24:
        u = _e((t - 8.452) / (10.24 - 8.452))   # over A's shoulder: her back huge and soft, the world beyond
        sc = 1.02 + 0.06 * u                        # A soft in the foreground (left), B beyond, the world below
        return dict(name='OTS', sc=sc, cx=0.17 * W + (MID_X - 300) * sc + 30 * u, cy=0.86 * H, fg_blur=3.0, blur_x=640)
    if t < T_SIL0:
        u = _e((t - 11.981) / (T_SIL0 - 11.981))
        return dict(name='WIDE2', sc=0.36 + 0.03 * u, cx=0.5 * W, cy=0.70 * H)
    if t < 17.705:
        u = _e((t - T_SIL1) / (17.705 - T_SIL1))    # the sky: camera tilts up as the constellation forms
        return dict(name='SKY', sc=0.29, cx=0.5 * W, cy=(0.80 + 0.08 * u) * H)
    u = _e((t - 19.528) / (21.0 - 19.528))          # back wide after her close-up: A already looking up (wide = meaning)
    return dict(name='SKY', sc=0.31 + 0.02 * u, cx=0.5 * W, cy=0.88 * H, lookup=True)

def to_screen(x, y, sh):
    return sh['cx'] + (x - MID_X) * sh['sc'], sh['cy'] + (y - EDGE_Y) * sh['sc']

STAR_BG = np.random.default_rng(4).random((700, 3)) * np.array([W, H, 1])
yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]

def render(i, t, s, tau_frozen=False):
    sh = shot(t); sc = sh['sc']
    M = np.float32([[sc, 0, sh['cx'] - MID_X * sc], [0, sc, sh['cy'] - EDGE_Y * sc]])
    # sky: deep night, warmer toward the edge
    _, ey = to_screen(0, EDGE_Y, sh)
    hz = np.clip(1 - np.abs(np.arange(H) - ey) / (0.5 * H), 0, 1)[:, None, None]
    frame = np.broadcast_to(np.array([0.018, 0.02, 0.04], np.float32), (H, W, 3)) * (1 - yy) + np.array([0.035, 0.03, 0.05]) * yy
    frame = frame + hz ** 2 * np.array([0.10, 0.06, 0.03])
    lay = np.zeros((H, W), np.float32)
    tw = 0.6 + 0.4 * np.sin(s * 2 + STAR_BG[:, 2] * 40)
    for (x, y, k), w in zip(STAR_BG, tw):
        if y < ey: lay[int(y), int(x)] += 0.5 * w * (0.3 + k)
    frame = screen(frame, cv2.GaussianBlur(lay, (0, 0), 0.7)[..., None] * np.array([0.8, 0.85, 1.0]))
    # the painted world below the edge, swinging down from the line on the hit
    drop = float(ss(T_HIT, T_HIT + 0.8, s))
    if drop > 0.01:
        Mm = np.float32([[sc / MS, 0, sh['cx'] + (MX0 - MID_X) * sc], [0, sc / MS * drop, sh['cy']]])
        mrgb = cv2.warpAffine(MAPRGB, Mm, (W, H), flags=cv2.INTER_LINEAR)
        mm = cv2.warpAffine(np.ones((mh, mw), np.float32), Mm, (W, H))[..., None]
        frame = frame * (1 - mm) + mrgb * mm
    # traces: behind the witnesses
    def draw_traces(front):
        L = np.zeros((H, W), np.float32)
        x, y, alive = trace_pos(s, t)
        grow = np.clip((EDGE_Y - y) / 900, 0, 1)                   # nearer the sky, a little bigger
        for k in np.nonzero(alive & (t_front == front) & (t_type < 3))[0]:
            X, Y = to_screen(x[k], y[k], sh)
            if not (-30 < X < W + 30 and -30 < Y < H + 30): continue
            size = sc * 3.2 * t_sz[k] * (1 + 0.6 * grow[k]) * (1.6 if sh['name'] == 'OTS' else 1.0)
            if t >= T_SIL1: size *= 1 - 0.6 * float(eio(0.4, 1.9, (t - T_SIL1) - t_delay[k]))   # becomes a point of light
            sp = _sprite(t_type[k], size); r = sp.shape[0] // 2
            x0, y0 = int(X) - r, int(Y) - r
            xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + sp.shape[1]), min(H, y0 + sp.shape[0])
            if xa < xb and ya < yb:
                fade = min(1.0, (s - t_ts[k]) / 0.6) * (0.75 + 0.25 * np.sin(s * 6 + t_ph[k]))
                L[ya:yb, xa:xb] += sp[ya - y0:yb - y0, xa - x0:xb - x0] * fade
        g = cv2.GaussianBlur(L, (0, 0), 0.8) + cv2.GaussianBlur(L, (0, 0), 5) * 0.9
        return np.clip(g, 0, 1.5)[..., None] * EMBER * (1 + 0.5 * beat_pulse(s))
    frame = screen(frame, 1 - np.exp(-draw_traces(False) * 1.3))
    # the lullaby: one warm glow rising slowly near B, breathing on the beat
    if s > t_ts[0]:
        lx, ly_, _ = trace_pos(s, t); X, Y = to_screen(lx[0], ly_[0], sh)
        gl = np.zeros((H, W), np.float32)
        if 0 <= X < W and 0 <= Y < H: gl[int(Y), int(X)] = 1
        rr = max(6.0, 60 * sc)
        g = cv2.GaussianBlur(gl, (0, 0), rr) * rr * rr * 2 * np.pi * 0.25 * (0.8 + 0.4 * beat_pulse(s)) * min(1, (s - t_ts[0]) / 1.0)
        frame = screen(frame, np.clip(g, 0, 1)[..., None] * np.array([1.0, 0.78, 0.5]))
    # the witnesses: unfinished until the world is loaded, then painted
    if sh['name'] == 'EDGE':
        pen = np.clip((s - 6.2) / 0.5 - NOISE, 0, 1); fl = np.clip((s - 6.9) / 0.5 - NOISE, 0, 1); pa = np.clip((s - 7.45) / 0.55 - NOISE, 0, 1)
        fig = np.zeros_like(SB)
        for key, p in (('pencil', pen), ('flat', fl), ('painted', pa)):
            a = ST[key][..., 3:] * p[..., None]
            fig[..., :3] = fig[..., :3] * (1 - a) + ST[key][..., :3] * a
            fig[..., 3:] = np.maximum(fig[..., 3:], a)
    else:
        fig = SBL if sh.get('lookup') else SB
    fig = cv2.remap(fig, TX - (TAIL_W * 7 * np.sin(2 * np.pi * s / 3.1 + TY / 160)).astype(np.float32), TY,
                    cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))                # the tail sways, slow as breath
    f = cv2.warpAffine(fig, M, (W, H), flags=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    fgm = None
    if sh.get('fg_blur'):                                              # only A (src x < blur_x) is the soft foreground
        pm = cv2.GaussianBlur(np.dstack([f[..., :3] * f[..., 3:], f[..., 3:]]), (0, 0), sh['fg_blur'])
        fb = np.dstack([pm[..., :3] / np.maximum(pm[..., 3:], 1e-3), pm[..., 3:]])
        bx, _ = to_screen(sh['blur_x'], 0, sh)
        fgm = (np.arange(W)[None, :, None] < bx).astype(np.float32)
        f = fb * fgm + f * (1 - fgm)
    a = f[..., 3:]
    # lit from below by the world: a warm rim on their lower edges, cool from the sky above
    up = np.clip(a[..., 0] - np.roll(a[..., 0], 5, axis=0), 0, 1)
    dn = np.clip(a[..., 0] - np.roll(a[..., 0], -5, axis=0), 0, 1)
    rim = cv2.GaussianBlur(up, (0, 0), 1.5)[..., None] * np.array([0.45, 0.5, 0.65]) * 0.35 + cv2.GaussianBlur(dn, (0, 0), 1.5)[..., None] * EMBER * 0.35
    col = (f[..., :3] + rim) * (0.85 if fgm is None else (0.60 * fgm + 0.85 * (1 - fgm)))
    frame = frame * (1 - a) + col * a
    frame = screen(frame, 1 - np.exp(-draw_traces(True) * 1.3))
    # the constellation lines, once the traces have arrived
    if sh['name'] == 'SKY':
        lay = np.zeros((H, W), np.float32); u = t - T_SIL1
        pts = [tuple(int(v) for v in to_screen(px, py, sh)) for px, py in STARS]
        for j in range(len(pts) - 1):
            v = float(np.clip((u - 1.6 - 0.15 * j) / 0.35, 0, 1))
            if v > 0:
                p0 = np.array(pts[j]); p1 = p0 + (np.array(pts[j + 1]) - p0) * v
                cv2.line(lay, tuple(int(c) for c in p0), tuple(int(c) for c in p1), 0.42, 1, cv2.LINE_AA)
        for j, pt in enumerate(pts):
            lit = float(np.clip((u - 1.7 - 0.15 * j) / 0.4, 0, 1)) * (0.8 + 0.2 * np.sin(s * (2.3 + j * 0.7) + j))
            cv2.circle(lay, pt, STAR_R[j], lit, -1, cv2.LINE_AA)
        g = np.clip(cv2.GaussianBlur(lay, (0, 0), 0.8) + cv2.GaussianBlur(lay, (0, 0), 5) * 1.3, 0, 1)[..., None]
        frame = screen(frame, g * np.array([1.0, 0.80, 0.45]) * 0.9)
    # the hit flash, the downbeat breath, vignette, grain
    if t >= T_HIT: frame = frame + 0.55 * np.exp(-(t - T_HIT) * 6.5) * WARM
    if t >= T_DOWN: frame = frame + 0.08 * np.exp(-(t - T_DOWN) * 5) * WARM
    vy, vx = np.ogrid[0:H, 0:W]
    frame = frame * (1 - 0.45 * (((vx - W / 2) / (W / 1.1)) ** 2 + ((vy - H / 2) / (H / 1.0)) ** 2))[..., None]
    frame = frame + np.random.default_rng(int(round(s * FPS))).normal(0, 0.010, (H, W, 1))
    return (np.clip(frame, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)
