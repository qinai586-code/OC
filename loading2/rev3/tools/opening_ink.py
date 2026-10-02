"""Opening demo: the stroke becomes the lived world (0.000-13.583 s, 326 frames, 1280x720, 24 fps).

  python3 rev3/tools/opening_ink.py   ->  rev3/tests/OPENING_INK_demo_720p.mp4 (+ OPENING_INK_demo_strip.jpg)

0.232  the drone; macro on paper, top-down. A hooked stroke is written (0.45-1.45).
1.45   night sweeps across the page like the Earth's terminator; the wet ink beads into warm lights.
1.90   the camera pulls up and tilts: the page is the night side of the Earth. The surface curves, the horizon
       and sky appear, and the parapet and both girls rise into frame. The move lands on the six-onset cluster (3.344).
3.344  the six onsets flash six lights along the stroke toward its end; the last one lifts (3.82), rises above
       them, hangs (6.70-7.05) and turns down toward A (7.05-7.50).
7.500  the approved light catch, decoded unchanged from tests/P1_light_catch_720p.mp4.

Geometry: a unit-radius globe seen by a pinhole camera. The final camera was fitted to KV1's painted limb (max
error 1.8 px: f 1100 px, altitude 0.1107 radii, pitch 30.1 deg). The globe's texture is KV1 itself, projected
from that camera, so the move lands exactly on KV1. Where the girls and parapet hide the Earth, the plate is
filled with clones from the same latitude band (a proxy for a clean plate).
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
from p1s1_light import glow_profile  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R))
KV1 = os.path.join(ROOT, 'loading', 'work', 'plates', 'KV1.png')
CHARS = os.path.join(ROOT, 'loading2', 'work', 'chars')
APPROVED = os.path.join(R, 'tests', 'P1_light_catch_720p.mp4')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
OUT = os.path.join(R, 'tests', 'OPENING_INK_demo_720p.mp4')
STRIP = os.path.join(R, 'tests', 'OPENING_INK_demo_strip.jpg')
LOG = os.path.join(R, 'tests', 'opening_ink_log.json')

W, H, FPS = 1280, 720, 24
N_OPEN, N_ALL = 180, 326
Y0, S = 186, W / 3072.0                       # KV1 16:9 crop (y 186-1914) and its scale to 720p

# fitted final camera (KV1)
F = 1100.0
CX1 = 610.51
H1 = 0.110695805
PHI1 = 0.52599578
C1 = np.array([0.0, 1.0 + H1, 0.0])
RX = np.array([1.0, 0.0, 0.0])
FW1 = np.array([0.0, -np.sin(PHI1), np.cos(PHI1)])
UP1 = np.array([0.0, np.cos(PHI1), np.sin(PHI1)])

HOOK_Y1 = 440.0                               # the stroke's centre on the final frame (x = CX1), between the girls
HOOK_W = 0.0275                               # stroke width on the globe (radii): about 130 px on the final frame
CHIMES = [3.344, 3.471, 3.529, 3.634, 3.704, 3.820]

T_WRITE = (0.45, 1.45)
T_NIGHT = (1.45, 2.05)
T_ZOOM = (1.90, 3.344)
T_TILT = (2.05, 3.344)
T_LAND = 3.344
T_FG = (2.80, 3.344)
P_MAIN = 0.99                                 # share of the move done by the landing; the rest eases out to 7.5


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


def ease(a, b, t):
    return float(smooth((t - a) / (b - a)))


def rotx(v, a):
    c, s = np.cos(a), np.sin(a)
    return np.array([v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c])


def hit_sphere(P, D):
    """first intersection of rays P + t D (D unit, shape (..., 3)) with the unit sphere; t = nan for a miss."""
    b = D @ P
    c = P @ P - 1.0
    disc = b * b - c
    t = -b - np.sqrt(np.where(disc > 0, disc, np.nan))
    return t, b, disc


# ---------------------------------------------------------------- geometry of the move
def c1_ray(x, y):
    d = FW1 + ((x - CX1) / F) * RX - ((y - 360.0) / F) * UP1
    return d / np.linalg.norm(d)


D_H1 = c1_ray(CX1, HOOK_Y1)
t1, _, _ = hit_sphere(C1, D_H1[None])
PH = C1 + t1[0] * D_H1                                     # the stroke's centre on the globe
NH = PH / np.linalg.norm(PH)
EV = rotx(NH, np.pi / 2)                                   # tangent at PH, pointing away from the camera (page "up")
D1 = float(np.linalg.norm(PH - C1))
ALPHA1 = float(np.arccos(-(D_H1 @ NH)))                    # final angle between the view ray and the vertical
BETA1 = float(np.arctan((HOOK_Y1 - 360.0) / F))
D0 = HOOK_W * F / 900.0                                    # start: the stroke about 900 px wide


def progress(t):
    zm = P_MAIN * float(smoother((t - T_ZOOM[0]) / (T_ZOOM[1] - T_ZOOM[0])))
    tl = P_MAIN * float(smoother((t - T_TILT[0]) / (T_TILT[1] - T_TILT[0])))
    fin = (1 - P_MAIN) * (1 - (1 - np.clip((t - T_LAND) / (7.5 - T_LAND), 0, 1)) ** 2)
    if t <= T_LAND:
        fin = 0.0
    return zm + fin, tl + fin


def camera(t):
    pz, pt = progress(t)
    d = D0 * (D1 / D0) ** pz
    al = ALPHA1 * pt
    beta = BETA1 * pz
    ray = -np.cos(al) * NH + np.sin(al) * EV
    P = PH - d * ray
    fw = rotx(ray, -beta)
    up = np.cross(fw, RX)
    cx = 640.0 + (CX1 - 640.0) * pz
    hy = 360.0 + (HOOK_Y1 - 360.0) * pz
    return dict(P=P, fw=fw, up=up, cx=cx, d=d, pz=pz, pt=pt, hy=hy)


def project(cam, X):
    v = X - cam['P']
    z = v @ cam['fw']
    return np.stack([cam['cx'] + F * (v @ RX) / z, 360.0 - F * (v @ cam['up']) / z], -1), z


GRID = None


def pixel_rays(cam):
    global GRID
    if GRID is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
        GRID = (xx, yy)
    xx, yy = GRID
    D = cam['fw'][None, None] + ((xx - cam['cx']) / F)[..., None] * RX[None, None] - ((yy - 360.0) / F)[..., None] * cam['up'][None, None]
    return D / np.linalg.norm(D, axis=-1, keepdims=True)


# ---------------------------------------------------------------- plates from KV1
def load_alpha(name):
    m = cv2.imread(os.path.join(CHARS, name + '.png'), cv2.IMREAD_UNCHANGED)
    a = m[..., 3].astype(np.float32)
    return a / (65535.0 if m.dtype == np.uint16 else 255.0)


def build_plates():
    kv = cv2.imread(KV1).astype(np.float32)
    crop = kv[Y0:Y0 + 1728].copy()                                      # 3072 x 1728
    off = json.load(open(os.path.join(CHARS, 'offsets.json')))
    girls = np.zeros(crop.shape[:2], np.float32)
    for n in ('kv1_A', 'kv1_B'):
        a = load_alpha(n)
        x0, y0, _, _ = off[n]
        y0 -= Y0
        h, w = min(a.shape[0], 1728 - y0), min(a.shape[1], 3072 - x0)
        girls[y0:y0 + h, x0:x0 + w] = np.maximum(girls[y0:y0 + h, x0:x0 + w], a[:h, :w])
    para_y = 1668 - Y0                                                  # top edge of the parapet (crop px)
    para = np.zeros_like(girls)
    para[para_y:] = 1.0
    para = cv2.GaussianBlur(para, (0, 0), 1.2)
    fg_a = np.maximum(girls, para)
    # Earth plate: hidden areas filled from the same latitude band
    occ = cv2.dilate((np.maximum(girls, para) > 0.12).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
    # base colour: a smooth inpaint at quarter size, pulled toward the dark sea between the girls
    q = cv2.resize(np.clip(crop, 0, 255).astype(np.uint8), (768, 432), interpolation=cv2.INTER_AREA)
    qm = cv2.resize(occ.astype(np.uint8) * 255, (768, 432), interpolation=cv2.INTER_NEAREST)
    qm = cv2.dilate(qm, np.ones((3, 3), np.uint8))
    lf = cv2.inpaint(q, qm, 12, cv2.INPAINT_TELEA)
    lf = cv2.resize(cv2.GaussianBlur(lf, (0, 0), 7), (3072, 1728), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    ocean = crop[1000:1300, 1450:1550].reshape(-1, 3).mean(0)
    lf = lf * 0.4 + ocean * 0.6
    # detail: the plate's own cloud texture from the same latitude band (or from above, under the parapet),
    # with the city lights clipped out
    hf_all = np.clip(crop - cv2.GaussianBlur(crop, (0, 0), 12), -40, 6)
    hf = np.zeros_like(crop)
    todo = occ.copy()
    for dy, dx in ((0, 560), (0, -560), (0, 1120), (0, -1120), (0, 1680), (0, -1680), (-320, 0), (-320, 560), (-320, -560),
                   (-640, 0), (-640, 560), (-640, -560)):
        src = np.roll(np.roll(hf_all, -dy, 0), -dx, 1)
        ok = ~np.roll(np.roll(occ, -dy, 0), -dx, 1)
        ys, xs = np.arange(1728) + dy, np.arange(3072) + dx
        ok &= ((ys >= 0) & (ys < 1728))[:, None] & ((xs >= 0) & (xs < 3072))[None]
        m = todo & ok
        hf[m] = src[m]
        todo &= ~m
    fill = lf + hf * 0.9
    soft = cv2.GaussianBlur(occ.astype(np.float32), (0, 0), 6)[..., None]
    earth = crop * (1 - soft) + fill * soft
    yy = np.arange(1728)
    # sky plate: below the limb the sky continues in its own colour (for rays that miss the globe)
    lim = limb_y_full()
    Y = yy[:, None].astype(np.float64)
    rows = np.clip((lim - 66).astype(int), 0, 1727)
    band = crop[rows, np.arange(3072)]
    band = cv2.GaussianBlur(band[None], (0, 0), 24)[0]
    k = np.clip((Y - (lim[None, :] - 60)) / 50.0, 0, 1)[..., None]
    sky = crop * (1 - k) + band[None] * k
    return crop, earth, sky, fg_a


def limb_y_full():
    """KV1's limb per column (crop px), from the fitted camera."""
    psi = np.linspace(-1.2, 1.2, 6000)
    b = np.arcsin(1 / (1 + H1))
    d = np.stack([np.sin(b) * np.sin(psi), -np.cos(b) * np.ones_like(psi), np.sin(b) * np.cos(psi)], -1)
    xc, yc, zc = d @ RX, d @ UP1, d @ FW1
    X, Y = CX1 + F * xc / zc, 360 - F * yc / zc
    ok = zc > 0
    o = np.argsort(X[ok])
    xs_out = np.arange(3072) * S
    return np.interp(xs_out, X[ok][o], Y[ok][o]) / S


# ---------------------------------------------------------------- the page: paper, terminator, stroke
PAPER_EXT = 0.05                                          # paper texture covers u, v in [-ext, ext] (radii)
PAPER_N = 3200


def build_paper():
    rng = np.random.default_rng(3)
    n = PAPER_N
    base = np.ones((n, n, 3), np.float32) * np.array([196, 224, 236], np.float32) / 255.0       # warm cream (BGR)
    fib = np.zeros((n, n), np.float32)
    for k in range(2600):                                                                 # fibres
        x, y = rng.uniform(0, n, 2)
        L, a = rng.uniform(20, 90), rng.uniform(0, np.pi)
        cv2.line(fib, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), float(rng.uniform(-1, 1)), 1, cv2.LINE_AA)
    fib = cv2.GaussianBlur(fib, (0, 0), 0.8)
    grain = cv2.GaussianBlur(rng.normal(0, 1, (n, n)).astype(np.float32), (0, 0), 1.6)
    blotch = cv2.GaussianBlur(rng.normal(0, 1, (n // 8, n // 8)).astype(np.float32), (0, 0), 6)
    blotch = cv2.resize(blotch, (n, n), interpolation=cv2.INTER_CUBIC)
    tex = 1.0 + 0.035 * fib + 0.025 * grain + 0.05 * blotch
    return np.clip(base * tex[..., None], 0, 1)


def catmull(pts, n=24):
    P = np.asarray(pts, np.float64)
    P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


# the recurring human mark: a long swash ending in a hooked curl (normalised; x right, y away from camera)
HOOK = [(-0.50, -0.03), (-0.38, 0.03), (-0.22, 0.065), (-0.06, 0.055), (0.08, 0.01), (0.20, -0.045), (0.31, -0.07),
        (0.40, -0.045), (0.435, 0.02), (0.395, 0.085), (0.315, 0.09), (0.27, 0.035), (0.30, -0.015), (0.355, -0.01)]


def stroke_geometry():
    uv = catmull(HOOK, 30) * HOOK_W
    seg = np.linalg.norm(np.diff(uv, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    X = PH[None] + uv[:, :1] * RX[None] + uv[:, 1:] * EV[None]
    X = X / np.linalg.norm(X, axis=1, keepdims=True)
    width = (0.22 + 0.78 * np.sin(np.pi * np.clip(s * 1.05, 0, 1)) ** 0.55) * (1 + 0.35 * np.exp(-((s - 0.86) / 0.06) ** 2))
    return uv, X, s, width


def write_s(t):
    """arc-length fraction written by time t: steady, slowing into the curl."""
    u = np.clip((t - T_WRITE[0]) / (T_WRITE[1] - T_WRITE[0]), 0, 1)
    return float(0.62 * smooth(u / 0.55) if u < 0.55 else 0.62 + 0.38 * smooth((u - 0.55) / 0.45))


def night_at(u, t):
    """0 = day, 1 = night. The terminator crosses the page from right to left."""
    ut = 0.026 - 0.052 * ease(*T_NIGHT, t)
    return np.maximum(smooth((u - ut) / 0.004 + 0.5), ease(2.0, 2.3, t))


def beads(rng=np.random.default_rng(11)):
    """warm lights along the stroke (arc-length positions, a size, a brightness, a small offset across the line)."""
    s = np.sort(np.concatenate([np.linspace(0.02, 0.97, 30) + rng.uniform(-0.012, 0.012, 30), rng.uniform(0.05, 0.95, 14)]))
    s = np.clip(s, 0, 0.995)
    return dict(s=np.append(s, 1.0), size=np.append(rng.uniform(0.6, 1.2, len(s)), 1.5),
                k=np.append(rng.uniform(0.45, 1.0, len(s)), 1.0), off=np.append(rng.normal(0, 0.006, len(s)), 0.0))


# ---------------------------------------------------------------- drawing helpers
PROF = None


def glow(img, c, scale, inten):
    rr, add = PROF
    if inten <= 0:
        return img
    rad = int(min(260, 180 * max(scale, 0.05))) + 2
    x0, y0 = int(max(0, c[0] - rad)), int(max(0, c[1] - rad))
    x1, y1 = int(min(W, c[0] + rad)), int(min(H, c[1] + rad))
    if x1 <= x0 or y1 <= y0:
        return img
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.clip(np.hypot(xx - c[0], yy - c[1]) / max(scale, 0.05), 0, rr[-1])
    img[y0:y1, x0:x1] += np.stack([np.interp(d, rr, add[:, k]) for k in range(3)], -1) * inten
    return img


def dot(img, c, r, k, col=(150, 215, 255)):
    """a small warm city light: a crisp core and a tight halo (no bloom)."""
    rad = int(r * 4 + 3)
    x0, y0 = int(c[0]) - rad, int(c[1]) - rad
    x1, y1 = x0 + 2 * rad + 1, y0 + 2 * rad + 1
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
        return
    yy, xx = np.mgrid[max(y0, 0):min(y1, H), max(x0, 0):min(x1, W)].astype(np.float32)
    d2 = (xx - c[0]) ** 2 + (yy - c[1]) ** 2
    v = k * (np.exp(-d2 / (2 * (0.55 * r) ** 2)) + 0.22 * np.exp(-d2 / (2 * (1.8 * r) ** 2)))
    img[max(y0, 0):min(y1, H), max(x0, 0):min(x1, W)] += v[..., None] * np.array(col, np.float32)


# ---------------------------------------------------------------- one frame of the opening
class Opening:
    def __init__(self):
        global PROF
        PROF = glow_profile()
        self.crop, self.earth, self.sky, fg_a = build_plates()
        self.fg = (self.crop, fg_a)
        self.paper = build_paper()
        self.uv, self.X, self.s, self.width = stroke_geometry()
        self.bd = beads()
        n = len(self.s)
        idx = np.clip(np.searchsorted(self.s, self.bd['s']), 0, n - 1)
        nrm = np.zeros_like(self.uv)
        tng = np.gradient(self.uv, axis=0)
        nrm[:, 0], nrm[:, 1] = -tng[:, 1], tng[:, 0]
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        buv = self.uv[idx] + nrm[idx] * self.bd['off'][:, None] * HOOK_W
        BX = PH[None] + buv[:, :1] * RX[None] + buv[:, 1:] * EV[None]
        self.bead_uv = buv
        self.bead_X = BX / np.linalg.norm(BX, axis=1, keepdims=True)
        # the six onset lights: the brightest beads in the last third, in order toward the end
        cand = [i for i in range(len(self.bd['s']) - 1) if self.bd['s'][i] > 0.62]
        pick = np.linspace(0, len(cand) - 1, 5).round().astype(int)
        self.onset_beads = [cand[i] for i in pick] + [len(self.bd['s']) - 1]
        self.haze = np.array([92, 58, 40], np.float32)                      # KV1's limb haze (BGR)
        self.limb_x = np.arange(3072) * S
        self.limb_y = limb_y_full() * S
        self.ocean = self.earth[int(1100 - Y0) - 30:int(1100 - Y0) + 30, 1450:1650].reshape(-1, 3).mean(0) / 255.0

    def limb_at(self, x):
        return np.interp(x, self.limb_x, self.limb_y)

    def background(self, cam, t):
        D = pixel_rays(cam)
        tt, b, disc = hit_sphere(cam['P'], D)
        hitm = np.isfinite(tt)
        X = cam['P'][None, None] + np.nan_to_num(tt)[..., None] * D
        # Earth: KV1 projected from the fitted camera
        v = X - C1
        z = v @ FW1
        x1o = CX1 + F * (v @ RX) / z
        y1o = 360.0 - F * (v @ UP1) / z
        hidden = (X @ C1) < 1.0 + 1e-4                                   # the far side KV1 never painted
        x1, y1 = x1o / S, y1o / S
        earth = cv2.remap(self.earth, x1.astype(np.float32), y1.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # sky: directions seen through the final camera's rotation
        dz = D @ FW1
        sx = (CX1 + F * (D @ RX) / dz) / S
        sy = (360.0 - F * (D @ UP1) / dz) / S
        sky = cv2.remap(self.sky, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # aerial haze toward the horizon (and for the far side the painting never showed)
        mu = np.clip(-(D * X).sum(-1), 0, 1)
        hz = np.where(hidden, 1.0, np.exp(-mu / 0.07) * (1.0 - ease(0.93, 0.995, cam['pz'])))
        earth = earth * (1 - hz[..., None]) + self.haze * hz[..., None]
        img = np.where(hitm[..., None], earth, sky)
        # thin atmosphere at the horizon while the painted one is not yet in view
        k_atm = 1.0 - ease(0.80, 0.99, cam['pz'])
        if k_atm > 0:
            cl = np.sqrt(np.clip(cam['P'] @ cam['P'] - b * b, 0, None)) - 1.0       # closest approach altitude
            a = np.where(hitm, 0.0, np.clip(cl, 0, None))
            rim = np.exp(-a / 0.0016) * (~hitm)
            img = img + k_atm * rim[..., None] * np.array([96, 56, 36], np.float32)
        # the page: paper with the terminator, fading into the globe as the camera pulls up
        pa = 1.0 - ease(2.35, 2.95, t)
        if pa > 0:
            rel = X - PH[None, None]
            u = rel @ RX
            vv = rel @ EV
            px = ((u / PAPER_EXT) * 0.5 + 0.5) * PAPER_N
            py = (0.5 - (vv / PAPER_EXT) * 0.5) * PAPER_N
            paper = cv2.remap(self.paper, px.astype(np.float32), py.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            nt = night_at(u, t)[..., None]
            lamp = np.clip(1.0 - 0.28 * (u * u + vv * vv) / 0.016 ** 2, 0.55, 1.0)[..., None]
            day = paper * lamp
            night = paper / np.array([196, 224, 236]) * 255 * self.ocean * 1.05
            ut = 0.026 - 0.052 * ease(*T_NIGHT, t)
            band = np.exp(-((u - ut) / 0.0045) ** 2)[..., None]
            tint = 1.0 - band * np.array([0.55, 0.30, 0.0])                       # warm the edge of the light (BGR)
            pg = (day * tint * (1 - nt) + night * nt) * 255.0
            img = img * (1 - pa) + pg * pa
        return img

    def stroke(self, img, cam, t):
        sw = write_s(t)
        ink_a = 1.0 - ease(2.0, 2.55, t)
        if sw <= 0 or ink_a <= 0:
            return img
        xy, z = project(cam, self.X)
        n = int(np.searchsorted(self.s, sw))
        if n < 2:
            return img
        pxu = F / cam['d']                                                       # px per radius near the stroke
        wpx = self.width[:n] * 0.00042 * pxu
        layer = np.zeros((H, W), np.float32)
        for i in range(n - 1):
            p0, p1 = xy[i], xy[i + 1]
            cv2.line(layer, (int(p0[0] * 8), int(p0[1] * 8)), (int(p1[0] * 8), int(p1[1] * 8)), 1.0,
                     max(1, int(round(wpx[i]))), cv2.LINE_AA, shift=3)
        layer = cv2.GaussianBlur(layer, (0, 0), 0.6)
        u_line = (self.X[:n] - PH) @ RX
        nt = float(np.mean(night_at(u_line, t)))
        ink = np.array([34, 24, 22], np.float32)                                # blue-black
        a = np.clip(layer, 0, 1)[..., None] * ink_a * (1 - 0.65 * nt)
        img = img * (1 - a) + ink * a
        # wet sheen at the fresh end of the line
        if sw < 1.0 and t < T_WRITE[1] + 0.2:
            tip = xy[n - 1]
            cv2.circle(img, (int(tip[0]), int(tip[1])), max(1, int(wpx[-1] * 0.35)), (120, 110, 105), -1, cv2.LINE_AA)
        return img

    def bead_light(self, cam, t):
        xy, z = project(cam, self.bead_X)
        u = (self.bead_X - PH) @ RX
        nt = night_at(u, t)
        on = np.clip((nt - 0.3) / 0.5, 0, 1) * (self.bd['s'] <= write_s(t) + 1e-6)
        pxu = F / cam['d']
        r = np.clip(self.bd['size'] * 0.00022 * pxu, 0.75, 6.0)
        return xy, r, on

    def frame(self, t):
        cam = camera(t)
        img = self.background(cam, t)
        img = self.stroke(img, cam, t)
        xy, r, on = self.bead_light(cam, t)
        lights = np.zeros((H, W, 3), np.float32)
        for i in range(len(xy)):
            k = on[i] * self.bd['k'][i]
            if i in self.onset_beads:
                j = self.onset_beads.index(i)
                k += sum(1.6 * np.exp(-(t - CHIMES[j]) / 0.09) for _ in [0] if t >= CHIMES[j])
                if j == 5:
                    k *= 1.0 - ease(3.82, 4.1, t)                                 # the last one leaves
            if k > 0.01:
                dot(lights, xy[i], r[i], k)
        img = img + lights
        # the light: born from the stroke's last bead, rises, hangs, turns toward A
        end_xy = xy[-1]
        p, sc, it = light_path(t, end_xy)
        if it > 0:
            img = glow(img, p, sc, it)
        # parapet and girls (they are nearest the camera, so they rise into frame last)
        img = self.foreground(img, t)
        return img

    def foreground(self, img, t):
        crop, a = self.fg
        if t < T_FG[0]:
            return img
        u = float(smooth((t - T_FG[0]) / (T_FG[1] - T_FG[0])))
        u = 1 - (1 - u) ** 2
        if t <= T_LAND:
            s = 1.45 + (1.05 - 1.45) * u
            dy = 560.0 * (1 - u)
        else:
            s = 1.05 - 0.05 * (1 - (1 - np.clip((t - T_LAND) / (7.5 - T_LAND), 0, 1)) ** 2)
            dy = 0.0
        sc = S * s
        M = np.float32([[sc, 0, 640 - 640 * s], [0, sc, 720 - 720 * s + dy]])
        fg = cv2.warpAffine(crop, M, (W, H), flags=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
        fa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
        return img * (1 - fa) + fg * fa


def light_path(t, birth):
    """screen position, glow scale and intensity of the light (final-frame px)."""
    birth = np.asarray(birth, np.float64)
    apex, turn_end = np.array([660.0, 118.0]), np.array([612.0, 150.0])
    if t < CHIMES[-1]:
        return birth, 0.06, 0.0
    if t < 6.70:
        u = 1 - (1 - (t - 3.82) / (6.70 - 3.82)) ** 2.2
        p = birth * (1 - u) + apex * u + np.array([-30.0, 0.0]) * np.sin(np.pi * u)
        return p, 0.07 + 0.19 * u, 0.9 * ease(3.82, 4.05, t) + 0.25
    if t < 7.05:
        u = (t - 6.70) / 0.35
        return apex + np.array([8.0 * np.sin(2 * np.pi * u), -6.0 * np.sin(np.pi * u)]), 0.26, 1.15 + 0.15 * np.sin(np.pi * u)
    u = smooth((t - 7.05) / 0.45)
    return apex * (1 - u) + turn_end * u, 0.26 + 0.07 * u, 1.15


# ---------------------------------------------------------------- render
def main():
    op = Opening()
    cap = cv2.VideoCapture(APPROVED)
    approved = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        approved.append(fr)
    assert len(approved) == N_ALL - N_OPEN, len(approved)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H), '-r', str(FPS),
                           '-i', '-', '-t', '%.4f' % (N_ALL / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '17',
                           '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', OUT], stdin=subprocess.PIPE)
    strip_t = [0.4, 1.0, 1.6, 2.0, 2.4, 2.7, 3.0, 3.344, 3.7, 5.0, 6.9, 7.45, 7.6, 10.0, 13.2]
    strip = []
    for f in range(N_ALL):
        t = f / FPS
        if f < N_OPEN:
            fast = 2.15 <= t <= 3.40                                           # motion blur through the fast move
            if fast:
                pic = sum(op.frame(t + dt) for dt in (-1 / 72, 0.0, 1 / 72)) / 3.0
            else:
                pic = op.frame(t)
            pic = pic * ease(0.232, 0.55, t)                                     # out of black on the drone
            pic = np.clip(pic, 0, 255).astype(np.uint8)
        else:
            pic = approved[f - N_OPEN]
        ff.stdin.write(pic.tobytes())
        if any(abs(t - s) < 0.5 / FPS for s in strip_t):
            th = cv2.resize(pic, (320, 180), interpolation=cv2.INTER_AREA)
            cv2.putText(th, '%.2f' % t, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            strip.append(th)
    ff.stdin.close()
    ff.wait()
    strip += [np.zeros_like(strip[0])] * (-len(strip) % 5)
    cv2.imwrite(STRIP, np.vstack([np.hstack(strip[i:i + 5]) for i in range(0, len(strip), 5)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    json.dump(dict(frames=N_ALL, fps=FPS, size=[W, H], approved_from=N_OPEN, final_camera=dict(f=F, cx=CX1, altitude=H1, pitch_deg=float(np.degrees(PHI1))),
                   start_distance=D0, final_distance=D1, scale_change=D1 / D0, stroke_centre_final=[CX1, HOOK_Y1]), open(LOG, 'w'), indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
