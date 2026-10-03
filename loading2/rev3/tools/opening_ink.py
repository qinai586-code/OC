"""Opening demo v2: the stroke becomes the lived world (0.000-13.583 s, 326 frames, 1280x720, 24 fps).

  python3 rev3/tools/opening_ink.py          ->  rev3/tests/OPENING_INK_demo_v2_720p.mp4 (+ _strip.jpg, log)
  python3 rev3/tools/opening_ink.py --check  ->  full-size check frames in the scratch folder given by $INK_CHECK

0.232  out of black on the drone: a lamplit letter seen from above. Two lines of earlier handwriting (dry); the pen
       rests at the end of the last line and a small pool of ink spreads under the nib.
0.50   the pen writes a flourish: fast through the swash, slowing into the hooked curl (1.36); it lifts and taps a
       full stop (1.44); it lifts away and leaves (1.52-1.85), its shadow parting from it. The fresh ink is wet and
       glossy, and dries matte with darker edges.
1.62   evening crosses the page like the Earth's terminator; on the night side every line of ink beads into
       warm lights, the flourish brightest, the full stop brightest of all.
2.00   the page tilts away (to 50 deg), still a page. From 2.45 the camera pulls up about 6.8x while it tilts on
       to KV1's angle; the night Earth comes through the paper only once the view is close to KV1's own angle and
       scale, so the painting is never seen stretched. The surface curves, the horizon and sky appear, and the
       parapet and both girls rise into frame. The move lands on the first onset of the six-onset cluster (3.344).
3.344  six onsets, six lights along the flourish toward the full stop; the full stop lifts as the light (3.82),
       rises above the girls, hangs (6.70-7.05) and turns down toward A (7.05-7.50).
5.55   on "three" A lifts her head toward it; on "two" (6.64) her right hand leaves the stone and her sleeve
       rises; B turns toward her. Still moving at the cut.
7.500  the approved light catch, decoded unchanged from tests/P1_light_catch_720p.mp4.

Geometry: a unit-radius globe and a pinhole camera fitted to KV1's painted limb (max error 1.8 px: f 1100 px,
altitude 0.1107 radii, pitch 30.1 deg). The globe's texture is KV1 itself, projected from that camera, so the
move lands exactly on KV1. Behind the girls and the parapet the Earth is filled locally (a proxy for a clean plate).
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
OUT = os.path.join(R, 'tests', 'OPENING_INK_demo_v2_720p.mp4')
STRIP = os.path.join(R, 'tests', 'OPENING_INK_demo_v2_strip.jpg')
LOG = os.path.join(R, 'tests', 'opening_ink_v2_log.json')

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

HOOK_Y1 = 440.0                               # the flourish's centre on the final frame (x = CX1), between the girls
HOOK_W = 0.0275                               # flourish width on the globe (radii): about 130 px on the final frame
CHIMES = [3.344, 3.471, 3.529, 3.634, 3.704, 3.820]
T_LAND = 3.344
T_FG = 2.62
SHUTTER = 0.15 / 24                           # half the shutter (0.3 of a frame)
T_PULL = 2.25                                 # the pull-back starts (gentle cubic ease to the landing)


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
    b = D @ P
    c = P @ P - 1.0
    disc = b * b - c
    t = -b - np.sqrt(np.where(disc > 0, disc, np.nan))
    return t, b, disc


# ---------------------------------------------------------------- the move
def c1_ray(x, y):
    d = FW1 + ((x - CX1) / F) * RX - ((y - 360.0) / F) * UP1
    return d / np.linalg.norm(d)


D_H1 = c1_ray(CX1, HOOK_Y1)
t1, _, _ = hit_sphere(C1, D_H1[None])
PH = C1 + t1[0] * D_H1
NH = PH / np.linalg.norm(PH)
EV = rotx(NH, np.pi / 2)                                   # tangent at PH, away from the camera (page "up")
D1 = float(np.linalg.norm(PH - C1))
ALPHA1 = float(np.arccos(-(D_H1 @ NH)))                    # 66.6 deg from the vertical
BETA1 = float(np.arctan((HOOK_Y1 - 360.0) / F))
D0 = HOOK_W * F / 900.0                                    # start: the flourish about 900 px wide
ALPHA_PAGE = np.radians(50.0)                              # the page tilts this far before the Earth shows


def schedule(t):
    """zoom (0..1 of log distance), tilt angle, page-centre offset (radii, along RX)."""
    zm = 0.99 * float(smooth((t - T_PULL) / (T_LAND - T_PULL)))
    if t > T_LAND:
        zm = 0.99 + 0.01 * (1 - (1 - min((t - T_LAND) / (7.5 - T_LAND), 1.0)) ** 2)
    push = 1.04 - 0.04 * ease(0.23, 1.95, t)                # a slow settle while the pen writes
    a1 = ALPHA_PAGE * float(smoother((t - 1.90) / 0.55))
    a2 = (0.99 * ALPHA1 - ALPHA_PAGE) * float(smooth((t - T_PULL) / (T_LAND - T_PULL)))
    al = a1 + a2
    if t > T_LAND:
        al = 0.99 * ALPHA1 + 0.01 * ALPHA1 * (1 - (1 - min((t - T_LAND) / (7.5 - T_LAND), 1.0)) ** 2)
    uc = -0.0072 * (1 - ease(0.35, 1.75, t))               # follow the pen from the line into the flourish
    return zm, al, push, uc


PUSH_C = np.array([520.0, 330.0])                          # between A's head and the light


def push_in(t):
    """slow push toward A from "three" to the cut: (background zoom, foreground zoom)."""
    u = ease(5.45, 7.5, t)
    return 1.0 + 0.045 * u, 1.0 + 0.075 * u


def camera(t):
    zm, al, push, uc = schedule(t)
    d = D0 * (D1 / D0) ** zm * push
    beta = BETA1 * zm
    anchor = PH + uc * RX
    anchor = anchor / np.linalg.norm(anchor)
    ray = -np.cos(al) * NH + np.sin(al) * EV
    P = anchor - d * ray
    fw = rotx(ray, -beta)
    up = np.cross(fw, RX)
    cx = 640.0 + (CX1 - 640.0) * zm
    return dict(P=P, fw=fw, up=up, cx=cx, d=d, zm=zm, al=al, zf=push_in(t)[0])


def project(cam, X):
    v = X - cam['P']
    z = v @ cam['fw']
    xy = np.stack([cam['cx'] + F * (v @ RX) / z, 360.0 - F * (v @ cam['up']) / z], -1)
    return PUSH_C + (xy - PUSH_C) * cam['zf'], z


GRID = None


def pixel_rays(cam):
    global GRID
    if GRID is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
        GRID = (xx, yy)
    xx, yy = GRID
    xx = PUSH_C[0] + (xx - PUSH_C[0]) / cam['zf']
    yy = PUSH_C[1] + (yy - PUSH_C[1]) / cam['zf']
    D = cam['fw'][None, None] + ((xx - cam['cx']) / F)[..., None] * RX[None, None] - ((yy - 360.0) / F)[..., None] * cam['up'][None, None]
    return D / np.linalg.norm(D, axis=-1, keepdims=True)


def uv_to_X(uv):
    """page coordinates (radii, relative to PH) to points on the globe."""
    uv = np.atleast_2d(uv)
    X = PH[None] + uv[:, :1] * RX[None] + uv[:, 1:2] * EV[None]
    return X / np.linalg.norm(X, axis=1, keepdims=True)


# ---------------------------------------------------------------- KV1 plates
def load_alpha(name):
    m = cv2.imread(os.path.join(CHARS, name + '.png'), cv2.IMREAD_UNCHANGED)
    a = m[..., 3].astype(np.float32)
    return a / (65535.0 if m.dtype == np.uint16 else 255.0)


def limb_y_full():
    psi = np.linspace(-1.2, 1.2, 6000)
    b = np.arcsin(1 / (1 + H1))
    d = np.stack([np.sin(b) * np.sin(psi), -np.cos(b) * np.ones_like(psi), np.sin(b) * np.cos(psi)], -1)
    xc, yc, zc = d @ RX, d @ UP1, d @ FW1
    X, Y = CX1 + F * xc / zc, 360 - F * yc / zc
    ok = zc > 0
    o = np.argsort(X[ok])
    return np.interp(np.arange(3072) * S, X[ok][o], Y[ok][o]) / S


def build_plates():
    kv = cv2.imread(KV1).astype(np.float32)
    crop = kv[Y0:Y0 + 1728].copy()
    off = json.load(open(os.path.join(CHARS, 'offsets.json')))
    girls = np.zeros(crop.shape[:2], np.float32)
    mats = {}
    for n in ('kv1_A', 'kv1_B'):
        a = load_alpha(n)
        x0, y0, _, _ = off[n]
        y0 -= Y0
        h, w = min(a.shape[0], 1728 - y0), min(a.shape[1], 3072 - x0)
        full = np.zeros_like(girls)
        full[y0:y0 + h, x0:x0 + w] = a[:h, :w]
        mats[n] = full
        girls = np.maximum(girls, full)
    para_y = 1668 - Y0
    para = np.zeros_like(girls)
    para[para_y:] = 1.0
    para = cv2.GaussianBlur(para, (0, 0), 1.2)
    fg_a = np.maximum(girls, para)
    # the hidden Earth: a rounded region (never the girls' outline), filled with a smooth base colour pulled toward
    # the dark sea between them plus the plate's own cloud detail from the same latitude band
    hard = (np.maximum(girls, para) > 0.12).astype(np.float32)
    blob = cv2.GaussianBlur(hard, (0, 0), 28)
    occ = (blob > 0.08) | (hard > 0)
    q = cv2.resize(np.clip(crop, 0, 255).astype(np.uint8), (768, 432), interpolation=cv2.INTER_AREA)
    qm = cv2.resize(occ.astype(np.uint8) * 255, (768, 432), interpolation=cv2.INTER_NEAREST)
    qm = cv2.dilate(qm, np.ones((3, 3), np.uint8))
    lf = cv2.inpaint(q, qm, 12, cv2.INPAINT_TELEA)
    lf = cv2.resize(cv2.GaussianBlur(lf, (0, 0), 9), (3072, 1728), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    ocean = crop[1000:1300, 1450:1550].reshape(-1, 3).mean(0)
    lf = lf * 0.4 + ocean * 0.6
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
    soft = np.clip(cv2.GaussianBlur(occ.astype(np.float32), (0, 0), 30) * 1.6, 0, 1)
    soft = np.maximum(soft, hard)[..., None]
    earth = crop * (1 - soft) + fill * soft
    lim = limb_y_full()
    Y = np.arange(1728)[:, None].astype(np.float64)
    rows = np.clip((lim - 66).astype(int), 0, 1727)
    band = cv2.GaussianBlur(crop[rows, np.arange(3072)][None], (0, 0), 24)[0]
    k = np.clip((Y - (lim[None, :] - 60)) / 50.0, 0, 1)[..., None]
    sky = crop * (1 - k) + band[None] * k
    return crop, earth, sky, fg_a, mats


# ---------------------------------------------------------------- the page
EXT = 0.05                                   # page texture covers u, v in [-EXT, EXT] (radii)
NP = 3200


def uv_px(u, v):
    return (u / EXT * 0.5 + 0.5) * NP, (0.5 - v / EXT * 0.5) * NP


def build_paper():
    rng = np.random.default_rng(3)
    n = NP
    base = np.ones((n, n, 3), np.float32) * np.array([196, 224, 236], np.float32) / 255.0
    fib = np.zeros((n, n), np.float32)
    for _ in range(2600):
        x, y = rng.uniform(0, n, 2)
        L, a = rng.uniform(20, 90), rng.uniform(0, np.pi)
        cv2.line(fib, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), float(rng.uniform(-1, 1)), 1, cv2.LINE_AA)
    fib = cv2.GaussianBlur(fib, (0, 0), 0.8)
    grain = cv2.GaussianBlur(rng.normal(0, 1, (n, n)).astype(np.float32), (0, 0), 1.6)
    blotch = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (n // 8, n // 8)).astype(np.float32), (0, 0), 6), (n, n),
                        interpolation=cv2.INTER_CUBIC)
    tex = 1.0 + 0.035 * fib + 0.025 * grain + 0.05 * blotch
    paper = np.clip(base * tex[..., None], 0, 1)
    # a faint inky thumbprint where the writer's hand rested (lower left of the letter)
    cx, cy = uv_px(-0.92 * HOOK_W, -0.27 * HOOK_W)
    bx, by, bs = int(cx) - 90, int(cy) - 90, 180
    tp = np.zeros((bs, bs), np.float32)
    for r in range(6, 60, 5):
        for a0 in np.arange(0, 2 * np.pi, 0.5):
            if rng.uniform() < 0.25:
                continue
            cv2.ellipse(tp, (90, 90), (int(r * 0.85), r), 25, np.degrees(a0), np.degrees(a0 + 0.42), 1.0, 2, cv2.LINE_AA)
    yy, xx = np.mgrid[0:bs, 0:bs].astype(np.float32)
    tp = cv2.GaussianBlur(tp, (0, 0), 1.0) * np.exp(-((xx - 90) ** 2 + (yy - 90) ** 2) / (2 * 55.0 ** 2))
    reg = paper[by:by + bs, bx:bx + bs]
    paper[by:by + bs, bx:bx + bs] = reg * (1 - 0.22 * tp[..., None]) + np.array([0.30, 0.20, 0.17]) * 0.22 * tp[..., None]
    return paper.astype(np.float32)


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


def resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(s[-1] / step))
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, path[:, 0]), np.interp(ss, s, path[:, 1])], 1), ss / max(s[-1], 1e-9)


# the flourish (normalised to its width; x right, y away from the camera) and its full stop
HOOK = [(-0.50, -0.03), (-0.38, 0.03), (-0.22, 0.065), (-0.06, 0.055), (0.08, 0.01), (0.20, -0.045), (0.31, -0.07),
        (0.40, -0.045), (0.435, 0.02), (0.395, 0.085), (0.315, 0.09), (0.27, 0.035), (0.30, -0.015), (0.355, -0.01)]
DOT = (0.505, -0.035)


def cursive_word(x0, base, n, rng, xh=0.036, capital=False):
    """a word of illegible cursive. Letters vary: arches (n, m), cups (u, w), small loops (e), tall loops (l, h, b),
    ovals (o, a), a descender loop (g, y); slant, size and baseline drift like a hand."""
    kinds = rng.choice(['e', 'n', 'u', 'o', 'l', 'a', 'g', 'i'], size=n, p=[0.20, 0.20, 0.16, 0.12, 0.12, 0.10, 0.05, 0.05])
    if capital:
        kinds[0] = 'L'
    pts = []
    x = x0
    drift = 0.0
    dots = []
    for k, kd in enumerate(kinds):
        wl = rng.uniform(0.020, 0.028) * (1.6 if kd in ('o', 'a', 'L') else 1.0)
        hh = xh * rng.uniform(0.85, 1.12)
        f = np.linspace(0, 1, 36)
        if kd == 'e':                                      # small loop
            xs = x + wl * f + 0.006 * np.sin(2 * np.pi * f)
            ys = hh * (1 - np.cos(2 * np.pi * f)) / 2
        elif kd in ('l', 'L'):                             # tall loop
            hh *= 2.5 if kd == 'l' else 3.0
            xs = x + wl * f + 0.009 * np.sin(2 * np.pi * f)
            ys = hh * (1 - np.cos(2 * np.pi * f)) / 2
        elif kd == 'n':                                    # two arches
            xs = x + wl * f
            ys = hh * np.abs(np.sin(2 * np.pi * f))
        elif kd == 'u':                                    # two cups
            xs = x + wl * f
            ys = hh * (1 - np.abs(np.sin(2 * np.pi * f))) * np.clip(f * 6, 0, 1)
        elif kd in ('o', 'a'):                             # an oval, then out along the x-height
            g = np.linspace(0, 2 * np.pi, 30)
            cxo = x + wl * 0.45
            xs = np.concatenate([cxo + wl * 0.42 * np.cos(g + np.pi / 2), np.linspace(cxo, x + wl, 6)])
            ys = np.concatenate([hh * 0.5 + hh * 0.5 * np.sin(g + np.pi / 2), np.linspace(hh * (0.15 if kd == 'a' else 0.9), 0.0, 6)])
        elif kd == 'g':                                    # descender loop
            xs = x + wl * f + 0.008 * np.sin(2 * np.pi * f)
            ys = -1.6 * hh * (1 - np.cos(2 * np.pi * f)) / 2 + hh * 0.5 * np.clip(1 - f * 4, 0, 1)
        else:                                              # i: a stroke and a dot
            xs = x + wl * f
            ys = hh * np.sin(np.pi * f)
            dots.append((x + wl * 0.6 + 0.3 * xh * 1.9, base + drift + xh * 1.9))
        drift += rng.normal(0, 0.0015)
        yb = base + drift
        pts.append(np.stack([xs + 0.30 * ys, yb + ys], 1))
        x += wl
    pts = np.vstack(pts)
    return pts, x, dots


def build_strokes():
    """every ink mark on the page: (path in page radii, kind, start time, end time)."""
    rng = np.random.default_rng(21)
    marks = []
    # two lines of earlier handwriting (already dry)
    for li, (base, xa, xb) in enumerate(((0.200, -1.55, 0.62), (-0.035, -1.62, -0.535))):
        x = xa
        first = True
        while x < xb - 0.05:
            n = int(rng.integers(2, 7))
            n = max(2, min(n, int((xb - x) / 0.026)))
            p, x_end, dots = cursive_word(x, base, n, rng, capital=first and li == 0)
            first = False
            marks.append(dict(uv=p * HOOK_W, kind='old', t0=-9.0, t1=-8.5))
            for d in dots:
                marks.append(dict(uv=np.array([d, (d[0] + 0.002, d[1] + 0.001)]) * HOOK_W, kind='old', t0=-9.0, t1=-8.5))
            x = x_end + rng.uniform(0.028, 0.042)
    # the flourish, written now
    path = catmull(HOOK, 40)
    trem = cv2.GaussianBlur(rng.normal(0, 1, (len(path), 2)).astype(np.float32), (1, 0), sigmaX=0.01, sigmaY=4)
    path += trem / (trem.std() + 1e-9) * 0.0016                                     # the fine tremor of a real hand
    marks.append(dict(uv=path * HOOK_W, kind='flourish', t0=0.50, t1=1.36))
    marks.append(dict(uv=np.array([DOT, (DOT[0] + 0.002, DOT[1] - 0.002)]) * HOOK_W, kind='dot', t0=1.44, t1=1.50))
    return marks


def write_profile(path_n):
    """time fraction along the flourish: quick in the swash, slower where it curls."""
    d = np.diff(path_n, axis=0)
    ang = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    seg = np.linalg.norm(d, axis=1) + 1e-9
    curv = np.abs(np.diff(ang, prepend=ang[0])) / seg
    speed = 1.0 / (1.0 + 0.012 * np.convolve(curv, np.ones(9) / 9, 'same'))
    speed *= np.clip(np.linspace(0, 1, len(seg)) * 12, 0.35, 1)                  # setting off from rest
    dt = seg / speed
    tt = np.concatenate([[0], np.cumsum(dt)])
    return tt / tt[-1]


class Ink:
    """ink in page-texture space: coverage, the time each texel was inked, ink amount; rendered per frame."""
    SS = 4                                                                           # supersampling for stamping

    def __init__(self, marks):
        allp = np.vstack([m['uv'] for m in marks])
        px, py = uv_px(allp[:, 0], allp[:, 1])
        pad = 40
        self.x0, self.y0 = int(px.min()) - pad, int(py.min()) - pad
        self.x1, self.y1 = int(px.max()) + pad, int(py.max()) + pad
        w, h = self.x1 - self.x0, self.y1 - self.y0
        ss = self.SS
        cov = np.zeros((h * ss, w * ss), np.uint8)
        tmap = np.full((h * ss, w * ss), 99.0, np.float32)
        amt = np.zeros((h * ss, w * ss), np.float32)
        stamps = []                                                                  # (x, y, r, t, amount)
        R0 = 6.2                                                                     # nib half-width, texels
        nib_ang = np.radians(38)
        for m in marks:
            p = m['uv']
            qx, qy = uv_px(p[:, 0], p[:, 1])
            q = np.stack([qx, qy], 1)
            if m['kind'] == 'dot':
                c = q[0]
                for k, r in enumerate(np.linspace(0.4, 1.55, 12)):
                    stamps.append((c[0], c[1], R0 * r, m['t0'] + (m['t1'] - m['t0']) * k / 11, 1.15))
                continue
            dense, sfrac = resample(q, 0.45)
            if m['kind'] == 'flourish':
                sq = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))])
                tfrac = np.interp(sfrac, sq / sq[-1], write_profile(q / 880.0))
            else:
                tfrac = sfrac
            tt = m['t0'] + (m['t1'] - m['t0']) * tfrac
            d = np.gradient(dense, axis=0)
            th = np.arctan2(-d[:, 1], d[:, 0])
            nib = 0.42 + 0.58 * np.abs(np.sin(th - nib_ang))
            if m['kind'] == 'flourish':
                press = 0.55 + 0.45 * np.sin(np.pi * np.clip(sfrac * 1.08, 0, 1)) ** 0.5
                press *= 1 + 0.25 * np.exp(-((sfrac - 0.86) / 0.06) ** 2)
                press[sfrac > 0.93] *= np.linspace(1, 0.45, int((sfrac > 0.93).sum()))     # the lift at the end
                spd = np.gradient(tt) + 1e-6
                amount = np.clip((spd / np.median(spd)) ** 0.25, 0.85, 1.25)
            else:
                press = 0.52 + 0.12 * np.sin(sfrac * 37.0)
                amount = np.ones_like(sfrac)
            r = R0 * press * nib
            for i in range(len(dense)):
                stamps.append((dense[i, 0], dense[i, 1], r[i], tt[i], amount[i]))
            if m['kind'] == 'flourish':                                               # ink pooled where the nib rested
                stamps.append((dense[0, 0], dense[0, 1], R0 * 1.45, m['t0'] - 0.2, 1.3))
        stamps.sort(key=lambda s: -s[3])                                              # latest first: earliest wins
        for (x, y, r, t, a) in stamps:
            c = (int(round((x - self.x0) * ss)), int(round((y - self.y0) * ss)))
            rr = max(1, int(round(r * ss)))
            cv2.circle(cov, c, rr, 255, -1)
            cv2.circle(tmap, c, rr, float(t), -1)
            cv2.circle(amt, c, rr, float(a), -1)
        cov = cv2.resize(cov.astype(np.float32) / 255.0, (w, h), interpolation=cv2.INTER_AREA)
        self.T = cv2.erode(tmap.reshape(h, ss, w, ss).min(axis=(1, 3)), np.ones((5, 5), np.uint8))   # reach the feathered edge
        self.A = cv2.resize(amt, (w, h), interpolation=cv2.INTER_AREA)
        rng = np.random.default_rng(8)
        fiber = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.7)
        fiber /= fiber.std() + 1e-6
        a = np.clip((cov + 0.10 * fiber - 0.30) / 0.42, 0, 1)                         # ink feathers into the fibres
        self.alpha = cv2.GaussianBlur(a, (0, 0), 0.6)
        self.edge = np.clip(self.alpha - cv2.GaussianBlur(self.alpha, (0, 0), 2.2), 0, 1) * 1.6
        lamp = (0.75, 0.66)                                                           # gloss on the lamp side (up, left)
        M = np.float32([[1, 0, lamp[0] * 2.0], [0, 1, lamp[1] * 2.0]])
        shifted = cv2.warpAffine(self.alpha, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        self.sheen = np.clip(self.alpha - shifted, 0, 1) * self.alpha

    def render(self, page, t):
        a = self.alpha * smooth((t - self.T) / 0.03)
        age = t - self.T
        wet = np.exp(-np.clip(age, 0, None) / 0.75) * (self.T > -5)
        wet_c = np.array([0.20, 0.09, 0.05], np.float32)
        dry_c = np.array([0.33, 0.23, 0.19], np.float32)
        old_c = np.array([0.42, 0.34, 0.30], np.float32)
        col = np.where((self.T < -5)[..., None], old_c, dry_c * (1 - wet[..., None]) + wet_c * wet[..., None])
        col = col * (1 - 0.60 * (self.edge * (1 - wet))[..., None])                   # dried edges darken
        k = 0.93 * np.clip(self.A, 0.8, 1.3) / 1.1
        reg = page[self.y0:self.y1, self.x0:self.x1]
        aa = (a * k)[..., None]
        reg = reg * (1 - aa) + col * aa
        reg = reg + (np.clip(self.sheen * 2.2, 0, 1) * wet * a)[..., None] * np.array([0.62, 0.70, 0.78], np.float32)
        page[self.y0:self.y1, self.x0:self.x1] = reg
        return page


# ---------------------------------------------------------------- the pen and the hand's shadow (screen space)
PEN_DIR = np.array([np.cos(np.radians(34)), np.sin(np.radians(34))])               # nib toward the writer, lower right
SHD_DIR = np.array([np.cos(np.radians(47)), np.sin(np.radians(47))])


def pen_state(t, tip_fn):
    """nib position (screen), lift 0..1, exit offset (screen px)."""
    if t < 0.50:
        return tip_fn(0.50), 0.0, 0.0
    if t <= 1.36:
        return tip_fn(t), 0.0, 0.0
    if t <= 1.44:                                                                    # lift, carry to the full stop
        u = smooth((t - 1.36) / 0.08)
        return tip_fn(1.36) * (1 - u) + tip_fn(1.47) * u, 0.6 * np.sin(np.pi * u), 0.0
    if t <= 1.50:
        return tip_fn(1.47), 0.0, 0.0
    u = smooth((t - 1.50) / 0.35)
    return tip_fn(1.47), min(1.0, (t - 1.50) / 0.12), 900.0 * u ** 1.6


def draw_pen(img, nib, lift, exit_px):
    """a fountain pen seen from above: steel nib, black grip and barrel rising out of focus toward the camera."""
    h, w = img.shape[:2]
    # the hand's and pen's shadow on the paper (the shadow meets the nib only while it touches)
    so = nib + SHD_DIR * (6 + 46 * lift) + np.array([10.0, 14.0]) * lift + SHD_DIR * exit_px
    shadow = np.zeros((h, w), np.float32)
    p0, p1 = so, so + SHD_DIR * 1400
    for k, (a, b, wd) in enumerate(((0.0, 0.10, 4), (0.10, 0.35, 14), (0.35, 1.0, 34))):
        q0, q1 = p0 + (p1 - p0) * a, p0 + (p1 - p0) * b
        cv2.line(shadow, tuple(np.int32(q0)), tuple(np.int32(q1)), 1.0, wd, cv2.LINE_AA)
    shadow = cv2.GaussianBlur(shadow, (0, 0), 6 + 10 * lift)
    hs = np.zeros((h, w), np.float32)
    hand = so + SHD_DIR * 520 + np.array([-SHD_DIR[1], SHD_DIR[0]]) * 60
    cv2.ellipse(hs, tuple(np.int32(hand)), (300, 170), 47, 0, 360, 1.0, -1, cv2.LINE_AA)
    shadow = np.maximum(shadow, cv2.GaussianBlur(hs, (0, 0), 45) * 0.9)
    img = img * (1 - 0.30 * shadow[..., None])
    # the pen itself
    base = nib + np.array([-6.0, -16.0]) * lift + PEN_DIR * exit_px
    sc = 1 + 0.10 * lift
    layer = np.zeros((h, w, 3), np.float32)
    alpha = np.zeros((h, w), np.float32)
    perp = np.array([-PEN_DIR[1], PEN_DIR[0]])

    def quad(a, b, wa, wb, col, blur):
        pa, pb = base + PEN_DIR * a * sc, base + PEN_DIR * b * sc
        poly = np.array([pa + perp * wa * sc, pb + perp * wb * sc, pb - perp * wb * sc, pa - perp * wa * sc], np.float32)
        lc = np.zeros((h, w, 3), np.float32)
        la = np.zeros((h, w), np.float32)
        cv2.fillConvexPoly(lc, np.int32(poly * 4), col, cv2.LINE_AA, shift=2)
        cv2.fillConvexPoly(la, np.int32(poly * 4), 1.0, cv2.LINE_AA, shift=2)
        if blur > 0:
            lc, la = cv2.GaussianBlur(lc, (0, 0), blur), cv2.GaussianBlur(la, (0, 0), blur)
        return lc, la

    parts = [(0, 50, 0.8, 7.0, (150, 160, 170), 0.5),       # steel nib
             (46, 170, 7.0, 13.0, (26, 24, 26), 1.2),        # grip
             (166, 450, 14.0, 22.0, (20, 18, 22), 3.5),      # barrel, nearer the camera
             (446, 1250, 22.0, 34.0, (18, 16, 20), 8.0)]
    for a, b, wa, wb, col, bl in parts[::-1]:
        lc, la = quad(a, b, wa, wb, col, bl)
        layer = layer * (1 - la[..., None]) + lc
        alpha = alpha * (1 - la) + la
    hl = np.zeros((h, w), np.float32)                                                # a lamp highlight along the barrel
    q0 = base + PEN_DIR * 60 * sc - perp * 3
    q1 = base + PEN_DIR * 1100 * sc - perp * 8
    cv2.line(hl, tuple(np.int32(q0)), tuple(np.int32(q1)), 1.0, 3, cv2.LINE_AA)
    hl = cv2.GaussianBlur(hl, (0, 0), 2.5) * alpha
    cv2.line(hl, tuple(np.int32(base + PEN_DIR * 6)), tuple(np.int32(base + PEN_DIR * 38)), 0.9, 1, cv2.LINE_AA)
    img = img * (1 - alpha[..., None]) + layer
    return img + hl[..., None] * np.array([120, 130, 140], np.float32)


# ---------------------------------------------------------------- lights
def night_at(u, t):
    ut = terminator(t)
    return np.maximum(smooth((u - ut) / 0.004 + 0.5), ease(2.05, 2.30, t))


def terminator(t):
    """the dusk line crosses the page right to left at an even pace (about 0.7 s across the frame)."""
    return 0.024 - 0.062 * float(np.clip((t - 1.45) / 0.75, 0, 1))


def dot(img, c, r, k, col=(150, 215, 255)):
    rad = int(r * 4 + 3)
    x0, y0 = int(c[0]) - rad, int(c[1]) - rad
    x1, y1 = x0 + 2 * rad + 1, y0 + 2 * rad + 1
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
        return
    yy, xx = np.mgrid[max(y0, 0):min(y1, H), max(x0, 0):min(x1, W)].astype(np.float32)
    d2 = (xx - c[0]) ** 2 + (yy - c[1]) ** 2
    v = k * (np.exp(-d2 / (2 * (0.55 * r) ** 2)) + 0.22 * np.exp(-d2 / (2 * (1.8 * r) ** 2)))
    img[max(y0, 0):min(y1, H), max(x0, 0):min(x1, W)] += v[..., None] * np.array(col, np.float32)


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


def light_path(t, birth):
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


# ---------------------------------------------------------------- the girls (KV1 crop coordinates, full resolution)
A_HEAD = dict(box=(980, 990 - Y0, 1310, 1330 - Y0), top=1010 - Y0, neck=1300 - Y0,
              horns=[(1075, 1015 - Y0), (1212, 1015 - Y0)])
A_HAND = [(1338, 1702), (1368, 1700), (1398, 1709), (1424, 1722), (1422, 1737), (1392, 1746), (1350, 1750), (1334, 1738)]
A_SLEEVE = dict(box=(1200, 1560 - Y0, 1400, 1770 - Y0), bottom=1748 - Y0)
B_HEAD = dict(box=(1740, 1040 - Y0, 2030, 1330 - Y0), top=1060 - Y0, neck=1320 - Y0)


def girl_motion(t):
    head_a = ease(5.55, 6.35, t)                     # A looks up on "three"
    hand_a = ease(6.60, 7.45, t)                     # her right hand leaves the stone on "two"
    head_b = ease(6.70, 7.35, t)                     # B turns toward her
    return head_a, hand_a, head_b


class Girls:
    def __init__(self, crop, fg_a, mats):
        self.crop, self.alpha = crop, fg_a
        self.mA = mats['kv1_A']
        # the hand as its own layer; under it, the stone (inpainted)
        poly = np.array([(x, y - Y0) for x, y in A_HAND], np.int32)
        hm = np.zeros(fg_a.shape, np.uint8)
        cv2.fillPoly(hm, [poly], 255)
        hm = cv2.dilate(hm, np.ones((5, 5), np.uint8))
        self.hand_m = cv2.GaussianBlur(hm.astype(np.float32) / 255, (0, 0), 1.0)
        x0, y0 = poly[:, 0].min() - 40, poly[:, 1].min() - 40
        x1, y1 = poly[:, 0].max() + 40, poly[:, 1].max() + 40
        # the stone under the hand: the parapet's own surface from just to its right (it runs horizontally)
        self.clean = crop.copy()
        cm = cv2.GaussianBlur(cv2.dilate(hm, np.ones((9, 9), np.uint8)).astype(np.float32) / 255, (0, 0), 2.5)[..., None]
        stone = np.roll(crop, -96, axis=1)
        sleeve = np.roll(crop, 45, axis=1)                                            # dark coat just inside the cuff
        yy_, xx_ = np.mgrid[0:1728, 0:3072].astype(np.float32)
        xb = 1350.0 + (yy_ + Y0 - 1700.0) * 0.45                                     # the cuff's edge runs down and right
        k_sl = np.clip((xb - xx_) / 5.0, 0, 1)[..., None]                            # left of it: sleeve; right: stone
        src = stone * (1 - k_sl) + sleeve * k_sl
        self.clean = crop * (1 - cm) + src * cm
        self.hbox = (x0, y0, x1, y1)
        # the body that hides the rising hand: A's matte without the hand
        self.body = np.clip(self.mA - cv2.dilate(self.hand_m, np.ones((9, 9), np.uint8)), 0, 1)

    def frame(self, t):
        ha, hn, hb = girl_motion(t)
        col, a = self.crop, self.alpha
        if hn > 0:
            col, a = self.hand(hn)
        if ha > 0:
            col, a = self.head(col, a, A_HEAD, ha, dy=18.0, horn=18.0, dx=0.0)
        if hb > 0:
            col, a = self.head(col, a, B_HEAD, hb, dy=8.0, horn=0.0, dx=13.0)
        return col, a

    def head(self, col, a, spec, k, dy, horn, dx):
        """looking up, seen from behind: the crown sinks a little toward the nape and the horn tips tilt back.
        dx turns the back of the head (B turning toward A)."""
        x0, y0, x1, y1 = spec['box']
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        w = np.clip((spec['neck'] - yy) / (spec['neck'] - spec['top']), 0, 1) ** 1.2
        sy = yy - k * dy * w
        sx = xx - k * dx * w
        for hx, hy in spec.get('horns', []):
            g = np.exp(-((xx - hx) ** 2 + (yy - hy) ** 2) / (2 * 45.0 ** 2))
            sy -= k * horn * g
        col = col.copy()
        a = a.copy()
        col[y0:y1, x0:x1] = cv2.remap(np.ascontiguousarray(col), sx, sy, cv2.INTER_LINEAR)
        a[y0:y1, x0:x1] = cv2.remap(np.ascontiguousarray(a), sx, sy, cv2.INTER_LINEAR)
        return col, a

    def hand(self, k):
        """the hand rises off the stone toward her chest and passes behind her body; the sleeve lifts."""
        col = self.clean.copy()
        a = self.alpha.copy()
        # the sleeve lifts (its lower edge rises up to 12 px)
        x0, y0, x1, y1 = A_SLEEVE['box']
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        wv = np.clip(1 - (A_SLEEVE['bottom'] - yy) / 160.0, 0, 1) * np.clip(1 - np.abs(yy - A_SLEEVE['bottom']) / 60.0, 0, 1)
        wx = np.exp(-((xx - 1310) / 80.0) ** 2)
        inside = np.clip((A_SLEEVE['bottom'] - 8 - yy) / 30.0, 0, 1)                   # keep the move inside the sleeve
        cuff = 26.0 * float(smooth((k - 0.35) / 0.65))                                       # the cuff rises with the hand (v6)
        sy = yy + (5.0 * k + cuff) * np.clip(wv + 0.6 * np.clip((yy - (A_SLEEVE['bottom'] - 160)) / 160, 0, 1), 0, 1) * wx * inside
        col[y0:y1, x0:x1] = cv2.remap(np.ascontiguousarray(col), xx, sy.astype(np.float32), cv2.INTER_LINEAR)
        # the hand (v6): a release, then the start of a lift, cut on the motion (S1 opens on the raised palm). First the
        # fingertips come up off the stone, turning about the wrist (k 0..0.45); then hand and cuff rise together, the
        # wrist staying in the sleeve. No fade.
        rel = smooth(k / 0.45)
        lift = smooth((k - 0.35) / 0.65)
        wr = np.array([1342.0, 1722.0 - Y0])                                           # the wrist, at the sleeve
        ang = 16.0 * rel + 6.0 * lift                                                  # fingertips up (counter-clockwise)
        R = cv2.getRotationMatrix2D((float(wr[0]), float(wr[1])), ang, 1.0)
        R[:, 2] += np.array([-6.0, -26.0]) * lift
        hl = cv2.warpAffine(self.crop * self.hand_m[..., None], R, (3072, 1728))
        ha = cv2.warpAffine(self.hand_m, R, (3072, 1728))
        vis = ha * (1 - self.body)                                                    # hidden behind her as it rises
        col = col * (1 - vis[..., None]) + hl * (vis / np.maximum(ha, 1e-3))[..., None]
        return col, np.maximum(a, vis)


# ---------------------------------------------------------------- one frame of the opening
class Opening:
    def __init__(self):
        global PROF
        PROF = glow_profile()
        self.crop, self.earth, self.sky, fg_a, mats = build_plates()
        self.girls = Girls(self.crop, fg_a, mats)
        self.paper = build_paper()
        self.paper_soft = cv2.GaussianBlur(self.paper, (0, 0), 3.0)
        self.marks = build_strokes()
        self.ink = Ink(self.marks)
        self.limb_x = np.arange(3072) * S
        self.limb_y = limb_y_full() * S
        self.haze = np.array([92, 58, 40], np.float32)
        self.ocean = self.earth[1100 - Y0 - 30:1100 - Y0 + 30, 1450:1650].reshape(-1, 3).mean(0) / 255.0
        self.build_lights()
        self._page_t = None

    # the flourish's points (for the pen) and the lights along every line
    def build_lights(self):
        rng = np.random.default_rng(11)
        fl = [m for m in self.marks if m['kind'] == 'flourish'][0]
        self.fl_uv = fl['uv']
        self.fl_tf = write_profile(np.stack(uv_px(fl['uv'][:, 0], fl['uv'][:, 1]), 1) / 880.0)
        uv, k, r, kind = [], [], [], []
        dense, sf = resample(fl['uv'], HOOK_W * 0.004)
        idx = np.unique(np.clip((np.sort(np.concatenate([np.linspace(0.02, 0.97, 30) + rng.uniform(-0.012, 0.012, 30),
                                                          rng.uniform(0.05, 0.95, 12)])) * (len(dense) - 1)).astype(int), 0, len(dense) - 1))
        for i in idx:
            uv.append(dense[i]); k.append(rng.uniform(0.5, 1.0)); r.append(rng.uniform(0.6, 1.2)); kind.append('fl')
        for m in self.marks:
            if m['kind'] != 'old' or len(m['uv']) < 10:
                continue
            d, _ = resample(m['uv'], HOOK_W * 0.03)
            for p in d[rng.uniform(size=len(d)) < 0.55]:
                uv.append(p); k.append(rng.uniform(0.15, 0.45)); r.append(rng.uniform(0.4, 0.75)); kind.append('old')
        uv.append(np.array(DOT) * HOOK_W); k.append(1.0); r.append(1.6); kind.append('dot')
        self.l_uv = np.array(uv)
        self.l_X = uv_to_X(self.l_uv)
        self.l_k, self.l_r, self.l_kind = np.array(k), np.array(r), np.array(kind)
        fl_ids = [i for i in range(len(kind)) if kind[i] == 'fl']
        order = sorted(fl_ids, key=lambda i: np.argmin(np.linalg.norm(dense - self.l_uv[i], axis=1)))
        late = [i for i in order if np.argmin(np.linalg.norm(dense - self.l_uv[i], axis=1)) > 0.62 * len(dense)]
        pick = np.linspace(0, len(late) - 1, 5).round().astype(int)
        self.onset = [late[i] for i in pick] + [len(kind) - 1]

    def tip_screen(self, cam, t):
        def tip(tq):
            if tq >= 1.44:
                X = uv_to_X(np.array(DOT) * HOOK_W)[0]
            else:
                f = np.clip((tq - 0.50) / (1.36 - 0.50), 0, 1)
                i = int(np.searchsorted(self.fl_tf, f))
                X = uv_to_X(self.fl_uv[min(i, len(self.fl_uv) - 1)])[0]
            return project(cam, X[None])[0][0]
        return tip

    def page(self, t):
        if self._page_t == t:
            return self._page
        pg = self.paper.copy()
        pg = self.ink.render(pg, t)
        self._page, self._page_t = pg, t
        return pg

    def background(self, cam, t):
        D = pixel_rays(cam)
        tt, b, disc = hit_sphere(cam['P'], D)
        hitm = np.isfinite(tt)
        X = cam['P'][None, None] + np.nan_to_num(tt)[..., None] * D
        img = None
        earth_k = ease(2.58, 2.92, t)
        if earth_k > 0:
            v = X - C1
            z = v @ FW1
            x1 = (CX1 + F * (v @ RX) / z) / S
            y1 = (360.0 - F * (v @ UP1) / z) / S
            hidden = (X @ C1) < 1.0 + 1e-4
            earth = cv2.remap(self.earth, x1.astype(np.float32), y1.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            mu = np.clip(-(D * X).sum(-1), 0, 1)
            hz = np.where(hidden, 1.0, np.exp(-mu / 0.07) * (1.0 - ease(0.93, 0.995, cam['zm'])))
            earth = earth * (1 - hz[..., None]) + self.haze * hz[..., None]
            dz = D @ FW1
            sx = (CX1 + F * (D @ RX) / dz) / S
            sy = (360.0 - F * (D @ UP1) / dz) / S
            sky = cv2.remap(self.sky, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            img = np.where(hitm[..., None], earth, sky)
            k_atm = 1.0 - ease(0.80, 0.99, cam['zm'])
            if k_atm > 0:
                cl = np.sqrt(np.clip(cam['P'] @ cam['P'] - b * b, 0, None)) - 1.0
                a = np.where(hitm, 0.0, np.clip(cl, 0, None))
                img = img + k_atm * (np.exp(-a / 0.0016) * (~hitm))[..., None] * np.array([96, 56, 36], np.float32)
        pa = 1.0 - earth_k
        if pa > 0:
            rel = X - PH[None, None]
            u = rel @ RX
            vv = rel @ EV
            px, py = uv_px(u, vv)
            pg = self.page(t)
            near = cv2.remap(pg, px.astype(np.float32), py.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            # far parts of the tilted page use a softened copy (no shimmer)
            dist = np.linalg.norm(X - cam['P'][None, None], axis=-1) / cam['d']
            fk = np.clip((dist - 1.3) / 1.2, 0, 1)[..., None]
            if fk.max() > 0:
                far = cv2.remap(self.paper_soft, px.astype(np.float32), py.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                near = near * (1 - fk) + far * fk
            nt = night_at(u, t)[..., None]
            lamp = np.clip(1.0 - 0.28 * ((u + 0.004) ** 2 + vv * vv) / 0.016 ** 2, 0.55, 1.0)[..., None]
            ut = terminator(t)
            band = np.exp(-((u - ut) / 0.0032) ** 2)[..., None]
            tint = 1.0 - band * np.array([0.42, 0.22, 0.02])
            night = near / np.array([196, 224, 236]) * 255 * self.ocean * 1.05
            pgc = (near * lamp * tint * (1 - nt) + night * nt) * 255.0
            img = pgc if img is None else img * (1 - pa) + pgc * pa
        return img

    def lights(self, img, cam, t):
        xy, z = project(cam, self.l_X)
        u = self.l_uv[:, 0]
        nt = night_at(u, t)
        on = np.clip((nt - 0.3) / 0.5, 0, 1)
        pxu = F / cam['d']
        r = np.clip(self.l_r * 0.00022 * pxu, 0.75, 6.0)
        page_k = 1.0 - ease(2.58, 2.92, t)
        layer = np.zeros((H, W, 3), np.float32)
        for i in range(len(xy)):
            k = on[i] * self.l_k[i]
            if self.l_kind[i] == 'old':
                k *= page_k
            if i in self.onset:
                j = self.onset.index(i)
                if t >= CHIMES[j]:
                    k += 1.6 * np.exp(-(t - CHIMES[j]) / 0.09)
                if j == 5:
                    k *= 1.0 - ease(3.82, 4.1, t)
            if k > 0.01 and z[i] > 0:
                dot(layer, xy[i], r[i], k)
        return img + layer, xy[-1]

    def foreground(self, img, t, subs=(0.0,)):
        if t < T_FG:
            return img
        acc_c = np.zeros((H, W, 3), np.float32)
        acc_a = np.zeros((H, W), np.float32)
        col, a = self.girls.frame(t)
        pre = col * a[..., None]
        for dt in subs:
            ts = t + dt
            u = float(np.clip((ts - T_FG) / (T_LAND - T_FG), 0, 1))
            u = 1 - (1 - u) ** 3
            if ts <= T_LAND:
                s = 1.35 + (1.05 - 1.35) * u
                dy = 520.0 * (1 - u)
            else:
                s = 1.05 - 0.05 * (1 - (1 - np.clip((ts - T_LAND) / (7.5 - T_LAND), 0, 1)) ** 2)
                dy = 0.0
            zf = push_in(ts)[1]
            sc = S * s * zf
            tx = (640 - 640 * s) * zf + PUSH_C[0] * (1 - zf)
            ty = (720 - 720 * s + dy) * zf + PUSH_C[1] * (1 - zf)
            M = np.float32([[sc, 0, tx], [0, sc, ty]])
            acc_c += cv2.warpAffine(pre, M, (W, H), flags=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
            acc_a += cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR)
        n = float(len(subs))
        return img * (1 - acc_a[..., None] / n) + acc_c / n

    def frame(self, t, subs=1):
        dts = [0.0] if subs == 1 else list(np.linspace(-SHUTTER, SHUTTER, subs))
        acc = None
        for dt in dts:
            ts = t + dt
            cam = camera(ts)
            img = self.background(cam, ts)
            img, end_xy = self.lights(img, cam, ts)
            if ts < 1.95:
                tip = self.tip_screen(cam, ts)
                nib, lift, ex = pen_state(ts, tip)
                if ex < 1400:
                    img = draw_pen(img, nib, lift, ex)
            p, sc, it = light_path(ts, end_xy)
            if it > 0:
                zb = push_in(ts)[0]
                img = glow(img, PUSH_C + (p - PUSH_C) * zb, sc * zb, it)
            acc = img if acc is None else acc + img
        img = acc / len(dts)
        fg_subs = tuple(np.linspace(-SHUTTER, SHUTTER, 9)) if T_FG <= t <= T_LAND + 0.05 else (0.0,)
        return self.foreground(img, t, fg_subs)


# ---------------------------------------------------------------- render
def main():
    op = Opening()
    if '--check' in sys.argv:
        out = os.environ.get('INK_CHECK', '/tmp')
        for t in [float(x) for x in os.environ.get('INK_T', '0.4,1.0,1.4,1.6').split(',')]:
            im = op.frame(t, subs=1) * ease(0.232, 0.55, t)
            cv2.imwrite(os.path.join(out, 'chk_%05.3f.jpg' % t), np.clip(im, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
        return
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
    strip_t = [0.4, 0.9, 1.3, 1.6, 1.9, 2.2, 2.5, 2.75, 3.0, 3.344, 4.5, 6.0, 7.0, 7.45, 7.6]
    strip = []
    for f in range(N_ALL):
        t = f / FPS
        if f < N_OPEN:
            subs = 5 if T_PULL <= t <= 3.40 else 1
            pic = op.frame(t, subs=subs) * ease(0.232, 0.55, t)
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
    json.dump(dict(frames=N_ALL, fps=FPS, size=[W, H], approved_from=N_OPEN,
                   final_camera=dict(f=F, cx=CX1, altitude=H1, pitch_deg=float(np.degrees(PHI1))),
                   start_distance=D0, final_distance=D1, scale_change=D1 / D0, page_tilt_deg=float(np.degrees(ALPHA_PAGE)),
                   final_tilt_deg=float(np.degrees(ALPHA1))), open(LOG, 'w'), indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
