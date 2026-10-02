"""Opening + Verse 1 demo v3 (0.000-43.250 s, 1038 frames, 1280x720, 24 fps) over the unchanged locked master.

  python3 rev3/tools/demo43.py                 ->  rev3/tests/DEMO_0-43_v3_720p.mp4 (+ _strip.jpg, _shots.json)
  python3 rev3/tools/demo43.py --stills 17,21  ->  single frames into $DEMO_CHECK (default /tmp)

0.000-7.500    the ink-to-world opening (tools/opening_ink.py, unchanged)
7.500-13.583   the approved light catch (tests/P1_light_catch_720p.mp4, with the S2 hand fix)
13.583-43.250  Verse 1, built here. One motif runs through it, as the spark does in mexicat/pdoom-video: the full
               stop that became the light becomes a sheet of paper, the letter's fragments, a compressed point, a
               candle, a lamp, a parting spark, constellations, lit windows, a hearth, a heartbeat, the first fire,
               and the flame in A's palm. Human memories are ink drawings that live on paper cards in a 3D space
               (foreground cards pass the lens as wipes); the girls appear as held key poses in varied framings;
               two compositions return with a changed meaning (KV1 from behind, KV5a palm light).
Cuts sit on the beat grid (one beat 0.912 s, anchored on the measured low hits) at or before each line's first
word, except where a held word would be cut short.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
import opening_ink as OI  # noqa: E402
from p1s1_light import glow_profile  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R))
PLATES = os.path.join(ROOT, 'loading', 'work', 'plates')
POSES = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad/assets/mv/inputs/Loading_face_assets_QC_PASS'
APPROVED = os.path.join(R, 'tests', 'P1_light_catch_720p.mp4')
ART = os.environ.get('DEMO_ART') or os.path.join(R, 'art', 'memory_cards')                  # supplied memory-card artwork (see briefs/MEMORY_CARDS_BRIEF.md)
AUDIO = OI.AUDIO
OUT = os.path.join(R, 'tests', 'DEMO_0-43_v3_720p.mp4')
STRIP = os.path.join(R, 'tests', 'DEMO_0-43_v3_strip.jpg')
LOG = os.path.join(R, 'tests', 'DEMO_0-43_v3_shots.json')
W, H, FPS, N = 1280, 720, 24, 1038
F = 1100.0
BEAT0, BEAT = 14.97, 0.9118                       # measured low hits every 4 beats


def beat(k):
    return BEAT0 + BEAT * k


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ease(a, b, t):
    return float(smooth((t - a) / (b - a)))


PROF = None


def glow(img, c, scale, inten, tint=None):
    rr, add = PROF
    if inten <= 0:
        return img
    rad = int(min(300, 180 * max(scale, 0.04))) + 2
    x0, y0 = int(max(0, c[0] - rad)), int(max(0, c[1] - rad))
    x1, y1 = int(min(W, c[0] + rad)), int(min(H, c[1] + rad))
    if x1 <= x0 or y1 <= y0:
        return img
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.clip(np.hypot(xx - c[0], yy - c[1]) / max(scale, 0.04), 0, rr[-1])
    L = np.stack([np.interp(d, rr, add[:, k]) for k in range(3)], -1) * inten
    if tint is not None:
        L = L * np.array(tint, np.float32)
    img[y0:y1, x0:x1] += L
    return img


def flame(img, c, size, t, k=1.0, seed=0):
    """a small live flame: a flickering teardrop with a warm halo (local, as the approved light is)."""
    if k <= 0:
        return img
    fl = 1.0 + 0.12 * np.sin(t * 2 * np.pi * 7.1 + seed) + 0.07 * np.sin(t * 2 * np.pi * 12.7 + 2 * seed)
    sway = 0.18 * size * np.sin(t * 2 * np.pi * 2.3 + seed)
    h, w = size * 2.4 * fl, size * 0.9
    pts = []
    for a in np.linspace(0, 2 * np.pi, 40):
        r = 1 - 0.55 * (np.sin(a / 2) ** 2) * 0
        x = np.sin(a) * w * (0.55 + 0.45 * np.cos(a / 2) ** 2) * (1 if a < np.pi else 1)
        y = -h * (1 - np.cos(a)) / 2
        pts.append((c[0] + x + sway * (-y / h), c[1] + y * 0.5 + h * 0.15))
    layer = np.zeros((H, W), np.float32)
    cv2.fillPoly(layer, [np.int32(np.array(pts) * 4)], 1.0, cv2.LINE_AA, shift=2)
    layer = cv2.GaussianBlur(layer, (0, 0), max(0.8, size * 0.12))
    img += layer[..., None] * np.array([90, 190, 255], np.float32) * 1.1 * k
    core = np.zeros((H, W), np.float32)
    cv2.circle(core, (int(c[0]), int(c[1] + h * 0.05)), max(1, int(size * 0.35)), 1.0, -1, cv2.LINE_AA)
    img += cv2.GaussianBlur(core, (0, 0), max(0.6, size * 0.15))[..., None] * np.array([200, 245, 255], np.float32) * k
    return glow(img, (c[0], c[1] - h * 0.2), 0.06 + size * 0.012, 0.9 * fl * k)


# ---------------------------------------------------------------- paper and ink
def paper(w, h, seed=1, tone=(0.80, 0.88, 0.93)):
    rng = np.random.default_rng(seed)
    fib = np.zeros((h, w), np.float32)
    for _ in range(int(w * h / 900)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        L, a = rng.uniform(8, 40), rng.uniform(0, np.pi)
        cv2.line(fib, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), float(rng.uniform(-1, 1)), 1, cv2.LINE_AA)
    grain = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 1.2)
    blot = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (h // 8 + 1, w // 8 + 1)).astype(np.float32), (0, 0), 4), (w, h))
    tex = 1 + 0.04 * cv2.GaussianBlur(fib, (0, 0), 0.7) + 0.025 * grain + 0.05 * blot
    return np.clip(np.array(tone, np.float32)[None, None] * tex[..., None], 0, 1)


INK = np.array([0.20, 0.12, 0.10], np.float32)


def catmull(pts, n=10):
    P = np.asarray(pts, np.float64)
    if len(P) < 3:
        return P
    P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


def ellipse_pts(c, rx, ry, a0=0.0, a1=2 * np.pi, n=40, rot=0.0):
    a = np.linspace(a0, a1, n)
    x, y = rx * np.cos(a), ry * np.sin(a)
    cr, sr = np.cos(rot), np.sin(rot)
    return np.stack([c[0] + x * cr - y * sr, c[1] + x * sr + y * cr], 1)


def draw_paths(canvas, paths, scale, progress=1.0, seed=3, col=INK, alpha=1.0):
    """ink line art. paths: list of (points in card units, width in card units*1000, smooth). Drawn on a 2x canvas
    as tapered strokes with a slight tremor; progress < 1 draws each stroke's first part (stroke order = list order)."""
    rng = np.random.default_rng(seed)
    ss = 2
    hgt, wid = canvas.shape[:2]
    cov = np.zeros((hgt * ss, wid * ss), np.float32)
    n = len(paths)
    for i, (pts, wpx, sm) in enumerate(paths):
        pts = np.asarray(pts, np.float64)
        if sm and len(pts) > 2:
            pts = catmull(pts, 12)
        loc = np.clip(progress * n - i, 0, 1)
        if loc <= 0:
            continue
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        if s[-1] <= 0:
            continue
        keep = s <= s[-1] * loc + 1e-9
        p = pts[keep]
        if loc < 1 and keep.sum() < len(pts):
            j = keep.sum()
            f = (s[-1] * loc - s[j - 1]) / max(seg[j - 1], 1e-9)
            p = np.vstack([p, pts[j - 1] + (pts[j] - pts[j - 1]) * f])
        q = p * scale * ss
        q += rng.normal(0, 0.35, q.shape) * ss
        m = len(q)
        for k in range(m - 1):
            fr = k / max(m - 2, 1)
            taper = np.clip(min(fr, 1 - fr) * 8, 0.35, 1.0)
            th = max(1, int(round(wpx / 1000.0 * scale * ss * taper)))
            cv2.line(cov, (int(q[k, 0] * 4), int(q[k, 1] * 4)), (int(q[k + 1, 0] * 4), int(q[k + 1, 1] * 4)), 1.0, th,
                     cv2.LINE_AA, shift=2)
    cov = cv2.resize(np.clip(cov, 0, 1), (wid, hgt), interpolation=cv2.INTER_AREA) * alpha
    canvas[..., :3] = canvas[..., :3] * (1 - cov[..., None]) + col * cov[..., None]
    return canvas


def light_pool(canvas, c, r, warm=(0.55, 0.80, 1.0), night=(0.42, 0.40, 0.52), k=1.0):
    """the card at night, lit by its own small light (card px)."""
    hgt, wid = canvas.shape[:2]
    yy, xx = np.mgrid[0:hgt, 0:wid].astype(np.float32)
    d = np.hypot(xx - c[0], yy - c[1]) / r
    lit = np.exp(-d * d) * k
    mul = np.array(night, np.float32)[None, None] * (1 - lit[..., None]) + np.array(warm, np.float32)[None, None] * lit[..., None]
    canvas[..., :3] *= mul
    return canvas


# ---------------------------------------------------------------- 3D cards
class Cam:
    def __init__(self, pos, target, cx=640.0, cy=360.0, f=F, roll=0.0):
        self.p = np.asarray(pos, np.float64)
        fw = np.asarray(target, np.float64) - self.p
        self.fw = fw / np.linalg.norm(fw)
        up0 = np.array([np.sin(roll), np.cos(roll), 0.0])
        rt = np.cross(up0, self.fw)
        self.rt = rt / np.linalg.norm(rt)
        self.up = np.cross(self.fw, self.rt)
        self.cx, self.cy, self.f = cx, cy, f

    def project(self, X):
        v = np.atleast_2d(X) - self.p
        z = v @ self.fw
        return np.stack([self.cx + self.f * (v @ self.rt) / z, self.cy - self.f * (v @ self.up) / z], -1), z


def card_corners(c, u, v, w, h):
    c, u, v = (np.asarray(a, np.float64) for a in (c, u, v))
    u, v = u / np.linalg.norm(u), v / np.linalg.norm(v)
    return np.array([c - u * w / 2 + v * h / 2, c + u * w / 2 + v * h / 2, c + u * w / 2 - v * h / 2, c - u * w / 2 - v * h / 2])


def rot_axis(v, axis, ang):
    axis = np.asarray(axis, np.float64) / np.linalg.norm(axis)
    v = np.asarray(v, np.float64)
    return v * np.cos(ang) + np.cross(axis, v) * np.sin(ang) + axis * (axis @ v) * (1 - np.cos(ang))


def put_card(img, cam, corners, tex, focus=None, aperture=0.0, fog=0.0, extra_blur=0.0, dof_map=False):
    """composite an RGBA card (tex: float, BGR 0..1 + alpha) onto img (0..255) through cam; depth of field by
    distance from the focus distance."""
    xy, z = cam.project(corners)
    if (z < 0.05).any():
        return img, None
    hgt, wid = tex.shape[:2]
    src = np.float32([[0, 0], [wid, 0], [wid, hgt], [0, hgt]])
    Hm = cv2.getPerspectiveTransform(src, np.float32(xy))
    pre = tex[..., :3] * tex[..., 3:4] * 255.0
    lay = cv2.warpPerspective(pre, Hm, (W, H), flags=cv2.INTER_LINEAR)
    a = cv2.warpPerspective(np.ascontiguousarray(tex[..., 3]), Hm, (W, H), flags=cv2.INTER_LINEAR)
    zc = float(z.mean())
    if dof_map and focus is not None:
        # a large card spans depths: blur each pixel by its own depth (z is affine across a flat card)
        uu = np.linspace(0, 1, wid, dtype=np.float32)[None, :]
        vv = np.linspace(0, 1, hgt, dtype=np.float32)[:, None]
        zs = (1 - vv) * ((1 - uu) * z[0] + uu * z[1]) + vv * ((1 - uu) * z[3] + uu * z[2])
        zm = cv2.warpPerspective(zs, Hm, (W, H), flags=cv2.INTER_LINEAR, borderValue=zc)
        sg = extra_blur + aperture * np.abs(1.0 / np.maximum(zm, 0.05) - 1.0 / focus) * 100.0
        levels = (0.0, 1.5, 3.5, 7.0, 13.0)
        sg = np.clip(sg, 0, levels[-1])
        out_l, out_a = np.zeros_like(lay), np.zeros_like(a)
        for i, lv in enumerate(levels):
            lo = levels[i - 1] if i > 0 else lv - 1
            hi = levels[i + 1] if i < len(levels) - 1 else lv + 1
            w_ = np.clip(np.minimum((sg - lo) / (lv - lo), (hi - sg) / (hi - lv)), 0, 1)
            if i == 0:
                w_ = np.clip((hi - sg) / (hi - lv), 0, 1)
            if i == len(levels) - 1:
                w_ = np.clip((sg - lo) / (lv - lo), 0, 1)
            if not w_.any():
                continue
            bl = (lay, a) if lv == 0 else (cv2.GaussianBlur(lay, (0, 0), lv), cv2.GaussianBlur(a, (0, 0), lv))
            out_l += bl[0] * w_[..., None]
            out_a += bl[1] * w_
        lay, a = out_l, out_a
        if fog > 0:
            lay = lay * np.exp(-fog * zm)[..., None]
        return img * (1 - a[..., None]) + lay, zc
    sig = extra_blur
    if focus is not None:
        sig += aperture * abs(1.0 / zc - 1.0 / focus) * 100.0
    if sig > 0.4:
        sig = min(sig, 40.0)
        lay, a = cv2.GaussianBlur(lay, (0, 0), sig), cv2.GaussianBlur(a, (0, 0), sig)
    if fog > 0:
        k = 1 - np.exp(-fog * zc)
        lay = lay * (1 - k)
    return img * (1 - a[..., None]) + lay, zc


# ---------------------------------------------------------------- character key poses
def white_matte(img):
    """alpha for a key pose drawn on white: the white connected to the border is background."""
    near = (img.min(2) > 238).astype(np.uint8)
    hgt, wid = near.shape
    mask = np.zeros((hgt + 2, wid + 2), np.uint8)
    ff = near.copy()
    for seed in ((0, 0), (wid - 1, 0), (0, hgt - 1), (wid - 1, hgt - 1)):
        if ff[seed[1], seed[0]] == 1:
            cv2.floodFill(ff, mask, seed, 2)
    bg = (ff == 2).astype(np.float32)
    a = 1 - cv2.GaussianBlur(bg, (0, 0), 1.0)
    return np.clip(a * 1.05, 0, 1)


def load_pose(name):
    """key pose on white: keep the figure's main silhouette (drops stray marks) and fade the drawing's cut sides
    and bottom into the night instead of showing a straight edge."""
    img = cv2.imread(os.path.join(POSES, name + '.png')).astype(np.float32)
    a = cv2.erode(white_matte(img), np.ones((3, 3), np.uint8), iterations=2)          # drop the pale fringe left by the white
    n, lab, st, _ = cv2.connectedComponentsWithStats((a > 0.5).astype(np.uint8))
    big = 1 + int(np.argmax(st[1:, 4]))
    keep = cv2.GaussianBlur(cv2.dilate((lab == big).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.0)
    a = a * keep
    x0, y0, w_, h_ = st[big, :4]
    hgt, wid = a.shape
    xx = np.arange(wid, dtype=np.float32)[None, :]
    yy = np.arange(hgt, dtype=np.float32)[:, None]
    fade = np.clip((xx - x0) / 140.0, 0, 1) * np.clip((x0 + w_ - xx) / 140.0, 0, 1) * np.clip((y0 + h_ - yy) / 180.0, 0, 1)
    return img, a * fade


def relight(img, a, warm_c, warm_r, warm_k=0.9, night=(0.62, 0.55, 0.52)):
    """the model-sheet drawing at night: cool fill, one warm light (image px)."""
    hgt, wid = a.shape
    yy, xx = np.mgrid[0:hgt, 0:wid].astype(np.float32)
    d = np.hypot(xx - warm_c[0], yy - warm_c[1]) / warm_r
    lit = np.exp(-d * d)[..., None] * warm_k
    out = img * (np.array(night, np.float32) * (1 - lit) + np.array([0.75, 0.95, 1.12], np.float32) * lit)
    return np.clip(out, 0, 255)


def place(img, src, a, cx, cy, h_px):
    """paste a key pose (src, alpha) with its centre at (cx, cy) and height h_px."""
    s = h_px / src.shape[0]
    M = np.float32([[s, 0, cx - src.shape[1] * s / 2], [0, s, cy - src.shape[0] * s / 2]])
    lay = cv2.warpAffine(src * a[..., None], M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    al = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR)
    return img * (1 - al[..., None]) + lay, M


def night_backdrop(seed=0, top=(34, 20, 14), bottom=(70, 42, 28)):
    yy = np.linspace(0, 1, H)[:, None, None]
    bg = np.array(top, np.float32) * (1 - yy) + np.array(bottom, np.float32) * yy
    bg = np.repeat(bg, W, 1)
    rng = np.random.default_rng(seed)
    n = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (H // 16, W // 16)).astype(np.float32), (0, 0), 2), (W, H))
    return bg * (1 + 0.06 * n[..., None])


# ---------------------------------------------------------------- the memories, drawn (card units: x 0..1.5, y 0..1, y down)
# A drawing is a list of items:
#   ('shape', prims, wash, line)   filled silhouette: wash tone (0 = paper, 1 = ink) and an ink outline of its union
#   ('line', pts, width, smooth)   a detail stroke
# prims: ('poly', pts) | ('ell', c, rx, ry, rot) | ('cap', p0, p1, r) | ('half', c, rx, ry) (upper half ellipse)
def _u(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v) + 1e-12)


def _rot(v, deg):
    a = np.radians(deg)
    return np.array([v[0] * np.cos(a) - v[1] * np.sin(a), v[0] * np.sin(a) + v[1] * np.cos(a)])


def hand_prims(wrist, direction, length, width, curl=0.0, thumb=1, open_=1.0, fist=False):
    """a hand as primitives: palm, four fingers, thumb. direction in degrees (0 = right, 90 = down)."""
    w = np.asarray(wrist, np.float64)
    d = _rot(np.array([1.0, 0.0]), direction)
    n = np.array([-d[1], d[0]]) * thumb
    pl = length * 0.48
    kn = w + d * pl
    pr = [('poly', [w + n * width * 0.40, kn + n * width * 0.50, kn - n * width * 0.48, w - n * width * 0.42])]
    lens = (0.40, 0.47, 0.45, 0.36)
    for i in range(4):
        base = kn + n * width * (0.36 - 0.24 * i)
        if fist:
            tip = base + _rot(d, 70 * thumb) * width * 0.30
        else:
            ang = (i - 1.5) * 6 * open_ + curl * (30 + 10 * i)
            tip = base + _rot(d, ang * thumb) * length * lens[i] * (0.55 + 0.45 * open_)
        pr.append(('cap', base, tip, width * 0.115))
    tb = w + d * pl * 0.30 + n * width * 0.46
    tt = tb + _rot(d, (55 if not fist else 80) * thumb) * length * 0.30
    pr.append(('cap', tb, tt, width * 0.125))
    return pr


def sleeve_prims(wrist, direction, width, length=0.6):
    w = np.asarray(wrist, np.float64)
    d = _rot(np.array([1.0, 0.0]), direction)
    n = np.array([-d[1], d[0]])
    return [('poly', [w + n * width * 0.62 + d * 0.01, w - n * width * 0.62 + d * 0.01,
                      w - n * width * 0.75 - d * length, w + n * width * 0.75 - d * length])]


def _closed(pts, n=8):
    P = np.asarray(pts, np.float64)
    Q = catmull(np.vstack([P[-1], P, P[0], P[1]]), n)
    return Q[n:-n]


def hand_shape(wrist, direction, length, flip=1, bend=15.0, thumb=-25.0, sleeve=0.0, sleeve_w=1.0, wrinkles=False):
    """a drawn hand in side view as smooth silhouettes (palm, the fingers as one bundle bent at the knuckles, the
    thumb), with finger divisions as detail lines. direction: degrees (0 = right, 90 = down); flip=1 puts the thumb
    on the left of the pointing direction (up when pointing right). Returns (prims, lines) in card units."""
    w = np.asarray(wrist, np.float64)
    d = _rot(np.array([1.0, 0.0]), direction)
    n = np.array([-d[1], d[0]]) * flip

    def X(pts, origin=(0.0, 0.0), ang=0.0):
        P = np.asarray(pts, np.float64)
        P = np.stack([_rot(q, ang) for q in P]) + np.asarray(origin)                  # the frame is already flipped
        return w + (P[:, :1] * d + P[:, 1:2] * n) * length
    palm = [(-0.02, -0.15), (0.20, -0.17), (0.44, -0.16), (0.49, -0.10), (0.49, 0.08), (0.36, 0.15), (0.14, 0.16), (-0.02, 0.14)]
    fing = [(-0.04, -0.13), (0.22, -0.13), (0.42, -0.10), (0.52, -0.05), (0.53, 0.01), (0.48, 0.05), (0.26, 0.09), (-0.04, 0.12)]
    thb = [(-0.02, -0.07), (0.16, -0.12), (0.30, -0.13), (0.35, -0.10), (0.31, -0.06), (0.14, -0.01), (0.0, 0.03)]
    kn = (0.45, -0.02)
    prims = [('poly', _closed(X(palm))), ('poly', _closed(X(fing, kn, bend))), ('poly', _closed(X(thb, (0.18, -0.08), thumb)))]
    lines = [X([(0.24, -0.055), (0.47, -0.065)], kn, bend), X([(0.22, 0.0), (0.50, 0.0)], kn, bend),
             X([(0.20, 0.05), (0.44, 0.055)], kn, bend)]
    if wrinkles:
        lines += [X([(0.03, -0.035), (0.05, 0.0), (0.03, 0.035)], kn, bend), X([(0.30, -0.12), (0.32, -0.08)]),
                  X([(0.10, 0.02), (0.22, 0.07)])]
    if sleeve > 0:
        sw = 0.19 * sleeve_w
        cuff = [(-0.02, -sw), (-0.02, sw), (-0.10, sw * 1.12), (-0.10, -sw * 1.12)]
        arm = [(-0.08, -sw * 1.05), (-0.08, sw * 1.05), (-sleeve, sw * 1.25), (-sleeve, -sw * 1.25)]
        prims = [('poly', X(arm)), ('poly', X(cuff))] + prims
        lines += [X([(-0.10, -sw * 1.12), (-0.10, sw * 1.12)]), X([(-0.30, -sw * 1.1), (-0.40, 0.0), (-0.34, sw * 0.6)])]
    return prims, lines


def add_hand(A, hs, wash, line_w=2.8, detail_w=1.3):
    prims, lines = hs
    A.append(('shape', prims, wash, line_w))
    for l in lines:
        A.append(('line', l, detail_w, True))


def art_war(t):
    A = []
    A.append(('shape', [('poly', [(0.0, 0.64), (1.5, 0.62), (1.5, 1.0), (0.0, 1.0)])], 0.22, 3.0))      # table
    A.append(('line', [(0.0, 0.68), (1.5, 0.66)], 1.4, False))
    A.append(('shape', [('poly', [(0.98, 0.06), (1.40, 0.06), (1.40, 0.40), (0.98, 0.40)])], 0.62, 4.0))  # window, night
    A.append(('line', [(1.19, 0.06), (1.19, 0.40)], 3.0, False))
    A.append(('line', [(0.98, 0.23), (1.40, 0.23)], 3.0, False))
    A.append(('line', [(1.02, 0.09), (1.07, 0.15), (1.05, 0.20), (1.11, 0.23)], 1.6, False))             # broken pane
    A.append(('line', [(1.07, 0.15), (1.13, 0.13)], 1.4, False))
    A.append(('line', [(0.52, 0.0), (0.57, 0.08), (0.54, 0.15), (0.60, 0.24), (0.58, 0.30)], 1.8, False))  # cracked plaster
    A.append(('line', [(0.57, 0.08), (0.64, 0.11)], 1.4, False))
    A.append(('line', [(0.54, 0.15), (0.48, 0.18)], 1.2, False))
    A.append(('shape', [('poly', [(0.25, 0.36), (0.36, 0.36), (0.36, 0.635), (0.25, 0.635)]), ('ell', (0.305, 0.635), 0.10, 0.022, 0)], 0.06, 3.0))  # candle
    A.append(('line', [(0.305, 0.36), (0.307, 0.33)], 2.4, False))
    A.append(('line', [(0.36, 0.40), (0.366, 0.44), (0.362, 0.47)], 2.2, True))
    A.append(('shape', [('poly', [(0.47, 0.585), (0.88, 0.57), (0.93, 0.655), (0.43, 0.665)])], 0.0, 2.6))   # the letter
    for k, y in enumerate((0.598, 0.616, 0.634)):
        xs = np.linspace(0.51, 0.82 - 0.06 * k, 26)
        A.append(('line', np.stack([xs, y + 0.003 * np.sin(xs * 170 + k)], 1), 1.2, False))
    A.append(('line', [(0.80, 0.640), (0.835, 0.636), (0.857, 0.643), (0.853, 0.656), (0.837, 0.652), (0.842, 0.644)], 1.8, True))
    A.append(('shape', [('half', (1.16, 0.60), 0.165, 0.17), ('ell', (1.16, 0.60), 0.235, 0.04, 0)], 0.42, 3.4))  # helmet
    A.append(('line', [(1.07, 0.47), (1.10, 0.50), (1.14, 0.485)], 2.4, True))                       # the dent
    A.append(('line', [(1.04, 0.62), (1.02, 0.70), (1.06, 0.78), (1.12, 0.80)], 2.0, True))           # strap
    return A


def art_lullaby(t, rock):
    A = []
    A.append(('shape', [('poly', [(0, 0.80), (1.5, 0.80), (1.5, 1.0), (0, 1.0)])], 0.18, 3.0))           # floor
    A.append(('shape', [('poly', [(0.62, 0.06), (0.98, 0.06), (0.98, 0.34), (0.62, 0.34)])], 0.58, 3.4))  # window
    A.append(('line', [(0.80, 0.06), (0.80, 0.34)], 2.4, False))
    A.append(('shape', [('poly', [(0.08, 0.56), (0.32, 0.56), (0.32, 0.80), (0.08, 0.80)])], 0.30, 3.0))  # side table
    A.append(('line', [(0.20, 0.56), (0.20, 0.44)], 2.6, False))
    A.append(('shape', [('poly', [(0.10, 0.44), (0.30, 0.44), (0.26, 0.29), (0.14, 0.29)])], 0.0, 3.0))  # lampshade
    piv = np.array([0.78, 0.80])
    ca, sa = np.cos(rock), np.sin(rock)

    def r(pts):
        p = np.asarray(pts, np.float64) - piv
        return np.stack([p[:, 0] * ca - p[:, 1] * sa, p[:, 0] * sa + p[:, 1] * ca], 1) + piv

    def rp(prims):
        out = []
        for q in prims:
            if q[0] == 'poly':
                out.append(('poly', r(q[1])))
            elif q[0] == 'cap':
                a2 = r([q[1], q[2]])
                out.append(('cap', a2[0], a2[1], q[3]))
            elif q[0] == 'ell':
                out.append(('ell', r([q[1]])[0], q[2], q[3], q[4] + rock))
        return out
    A.append(('shape', [('ell', (0.80, 0.50), 0.36, 0.09, 0)], 0.10, 0.0))                           # its shadow on the wall
    A.append(('shape', rp([('poly', [(0.46, 0.46), (1.12, 0.46), (1.04, 0.68), (0.54, 0.68)])]), 0.25, 3.4))   # basket
    for x in np.linspace(0.56, 1.02, 8):
        A.append(('line', r([(x, 0.47), (x - 0.01 * (x - 0.79), 0.67)]), 1.2, False))
    A.append(('line', r(catmull([(0.44, 0.73), (0.78, 0.80), (1.14, 0.73)], 10)), 4.2, False))         # rocker
    A.append(('line', r([(0.56, 0.68), (0.54, 0.755)]), 3.0, False))
    A.append(('line', r([(1.02, 0.68), (1.04, 0.755)]), 3.0, False))
    A.append(('shape', rp([('poly', [(0.66, 0.47), (1.08, 0.44), (1.06, 0.50), (0.68, 0.53)])]), 0.10, 2.6))  # blanket
    A.append(('shape', rp([('ell', (0.62, 0.43), 0.065, 0.058, 0)]), 0.0, 2.8))                      # baby's head
    A.append(('shape', rp([('ell', (0.605, 0.395), 0.045, 0.025, -0.3)]), 0.55, 0.0))                 # hair
    A.append(('line', r([(0.595, 0.44), (0.61, 0.448), (0.625, 0.44)]), 1.8, True))                  # closed eye
    pr, ln = hand_shape(r([(1.33, 0.41)])[0], 192 + np.degrees(rock), 0.24, flip=-1, bend=62, thumb=-15, sleeve=0.9)
    add_hand(A, (pr, ln), 0.06)                                                                       # the parent's hand on the rim
    return A


def art_farewell(t, train_dx, hand_dx):
    A = []
    d = train_dx

    def T(pts):
        return [(x + d, y) for x, y in pts]
    A.append(('shape', [('poly', [(0, 0.90), (1.5, 0.90), (1.5, 1.0), (0, 1.0)])], 0.28, 3.0))           # platform
    A.append(('line', [(1.38, 0.90), (1.38, 0.08)], 3.4, False))                                      # lamp post
    A.append(('shape', [('poly', [(1.31, 0.10), (1.45, 0.10), (1.41, 0.05), (1.35, 0.05)])], 0.0, 2.6))
    A.append(('shape', [('poly', T([(-1.2, 0.02), (0.60, 0.02), (0.64, 0.06), (0.64, 0.88), (-1.2, 0.88)]))], 0.34, 4.0))   # the car
    A.append(('shape', [('poly', T([(0.36, 0.12), (0.60, 0.12), (0.60, 0.88), (0.36, 0.88)]))], 0.70, 3.0))  # open door, dark inside
    A.append(('shape', [('poly', T([(-0.62, 0.10), (0.22, 0.10), (0.22, 0.44), (-0.62, 0.44)]))], 0.0, 3.4))  # lit window
    A.append(('shape', [('ell', T([(0.02, 0.30)])[0], 0.075, 0.09, 0), ('poly', T([(-0.10, 0.44), (0.14, 0.44), (0.10, 0.37), (-0.06, 0.37)]))], 0.60, 2.4))  # a face at the window
    for x in (-0.9, -0.4, 0.2):
        A.append(('shape', [('ell', T([(x, 0.90)])[0], 0.06, 0.06, 0)], 0.5, 2.6))
    # the hand from the door rides with the train; the hand from the platform stays
    add_hand(A, hand_shape(T([(0.62, 0.575)])[0], -2, 0.22, flip=1, bend=12, thumb=-28, sleeve=0.5), 0.05)
    e = hand_dx
    add_hand(A, hand_shape((1.12 + e, 0.58), 182, 0.22, flip=-1, bend=12, thumb=-28, sleeve=1.2), 0.12)
    return A


def art_heat(t):
    A = []
    A.append(('shape', [('poly', [(0, 0.66), (1.5, 0.64), (1.5, 1.0), (0, 1.0)])], 0.22, 3.0))           # table
    A.append(('shape', [('poly', [(0.95, 0.05), (1.42, 0.05), (1.42, 0.40), (0.95, 0.40)])], 0.38, 3.4))  # frosted window
    for k in range(10):
        x = 0.97 + 0.045 * k
        A.append(('line', [(x, 0.40), (x + 0.02, 0.34), (x - 0.01, 0.30)], 1.2, False))
    A.append(('shape', [('poly', [(0.54, 0.56), (0.96, 0.56), (0.90, 0.70), (0.80, 0.745), (0.70, 0.745), (0.60, 0.70)]),
                        ('ell', (0.75, 0.56), 0.21, 0.05, 0)], 0.05, 3.2))                          # bowl
    A.append(('shape', [('ell', (0.75, 0.56), 0.185, 0.038, 0)], 0.30, 1.6))                        # soup
    add_hand(A, hand_shape((0.42, 0.67), -18, 0.26, flip=1, bend=58, thumb=-30, sleeve=1.0, wrinkles=True), 0.16)   # an old hand
    add_hand(A, hand_shape((1.10, 0.66), 198, 0.19, flip=-1, bend=58, thumb=-30, sleeve=1.0, sleeve_w=0.9), 0.04)    # a child's
    for k in range(4):                                                                                # steam
        ys = np.linspace(0.52, 0.12, 20)
        xs = 0.66 + 0.06 * k + 0.025 * np.sin(ys * 18 + t * 3.2 + k * 1.7)
        A.append(('line', np.stack([xs, ys], 1), 1.2, True))
    return A


def art_newborn(t, fist_open):
    """a newborn asleep on a parent's chest, the parent's hand on its back. Returns (back layer: the parent, the
    blanket and the parent's hand; front layer: the baby)."""
    A = []
    A.append(('shape', [('poly', [(0, 0.0), (1.5, 0.0), (1.5, 0.30), (1.1, 0.24), (0.70, 0.22), (0.30, 0.28), (0, 0.38)])], 0.10, 3.2))   # parent's chest
    A.append(('line', [(0.42, 0.25), (0.60, 0.30), (0.78, 0.27)], 1.6, True))                     # collarbone
    A.append(('shape', [('poly', _closed([(0.66, 0.58), (0.98, 0.54), (1.28, 0.62), (1.42, 0.84), (1.30, 1.02), (0.56, 1.02), (0.50, 0.74)]))], 0.16, 3.2))   # blanket
    A.append(('line', [(0.80, 0.70), (1.00, 0.74), (1.12, 0.86)], 1.6, True))
    A.append(('line', [(0.70, 0.88), (0.92, 0.94)], 1.4, True))
    add_hand(A, hand_shape((1.46, 0.60), 188, 0.34, flip=-1, bend=22, thumb=-12, sleeve=0.3), 0.06)   # the parent's hand on its back
    back, A = A, []
    # the baby (front layer)
    A.append(('shape', [('poly', _closed([(0.47, 0.50), (0.52, 0.40), (0.62, 0.35), (0.74, 0.37), (0.80, 0.45), (0.80, 0.56), (0.73, 0.63), (0.60, 0.65), (0.50, 0.60)]))], 0.0, 3.0))   # head, turned to us
    A.append(('line', [(0.58, 0.37), (0.61, 0.40), (0.60, 0.43)], 1.4, True))                   # soft hair
    A.append(('line', [(0.65, 0.36), (0.66, 0.39)], 1.4, True))
    A.append(('line', [(0.53, 0.41), (0.56, 0.44)], 1.4, True))
    A.append(('line', [(0.755, 0.47), (0.78, 0.50), (0.765, 0.535)], 1.8, True))                # ear
    A.append(('line', [(0.535, 0.50), (0.56, 0.515), (0.585, 0.505)], 2.0, True))               # closed eye
    A.append(('line', [(0.52, 0.555), (0.53, 0.56)], 1.6, False))                               # nose
    A.append(('line', [(0.535, 0.598), (0.55, 0.604), (0.565, 0.598)], 1.6, True))              # mouth
    A.append(('shape', [('ell', (0.60, 0.565), 0.035, 0.022, 0)], 0.10, 0.0))                     # a little warmth in the cheek
    pr, ln = hand_shape((0.62, 0.76), -112, 0.12, flip=1, bend=10 if fist_open else 100, thumb=-20 if fist_open else 50)
    back.append(('shape', pr, 0.03, 2.4))                                                       # the tiny hand (on the chest)
    for l in (ln if fist_open else []):
        back.append(('line', l, 1.0, True))
    return back, A


def art_fire(t, struck):
    A = []
    A.append(('shape', [('poly', [(0, 0.0), (1.5, 0.0), (1.5, 0.66), (1.2, 0.62), (0.8, 0.60), (0.4, 0.63), (0, 0.68)])], 0.62, 0.0))   # night sky
    A.append(('shape', [('poly', [(0, 0.68), (0.4, 0.63), (0.8, 0.60), (1.2, 0.62), (1.5, 0.66), (1.5, 1.0), (0, 1.0)])], 0.30, 3.2))  # hilltop
    rng = np.random.default_rng(4)
    for x in np.linspace(0.04, 1.46, 52):
        y = 0.68 - 0.06 * np.sin(np.pi * x / 1.5) + 0.01
        A.append(('line', [(x, y + 0.01), (x + rng.uniform(-0.02, 0.02), y - rng.uniform(0.03, 0.07))], 1.2, False))
    A.append(('shape', [('ell', (0.66, 0.70), 0.09, 0.03, 0)], 0.45, 2.8))                          # the stone below
    for k in range(7):                                                                                 # tinder
        A.append(('line', [(0.58 + 0.025 * k, 0.69), (0.60 + 0.025 * k, 0.64 - 0.012 * (k % 2))], 1.6, False))
    y0 = 0.53 if struck else 0.33
    A.append(('shape', [('ell', (0.855, y0 + 0.045), 0.062, 0.040, 0.35)], 0.48, 2.8))                # the striking stone, in the fist
    add_hand(A, hand_shape((1.02, y0 - 0.06), 165, 0.24, flip=-1, bend=100, thumb=40, sleeve=0.8), 0.12)
    return A


def render_art(canvas, items, scale, prog=1.0, seed=3):
    """draw a drawing onto a card: washes and outlines of shapes, then detail lines (in list order)."""
    hgt, wid = canvas.shape[:2]
    ss = 2
    n = len(items)
    rng = np.random.default_rng(seed)
    for i, it in enumerate(items):
        k = float(np.clip(prog * n - i, 0, 1))
        if k <= 0:
            continue
        if it[0] == 'shape':
            _, prims, wash, lw = it
            m = np.zeros((hgt * ss, wid * ss), np.uint8)
            for q in prims:
                if q[0] == 'poly':
                    cv2.fillPoly(m, [np.int32(np.asarray(q[1]) * scale * ss * 4)], 255, cv2.LINE_AA, shift=2)
                elif q[0] == 'ell':
                    c = np.asarray(q[1]) * scale * ss
                    cv2.ellipse(m, (int(c[0] * 4), int(c[1] * 4)), (int(q[2] * scale * ss * 4), int(q[3] * scale * ss * 4)),
                                np.degrees(q[4]), 0, 360, 255, -1, cv2.LINE_AA, shift=2)
                elif q[0] == 'half':
                    c = np.asarray(q[1]) * scale * ss
                    cv2.ellipse(m, (int(c[0] * 4), int(c[1] * 4)), (int(q[2] * scale * ss * 4), int(q[3] * scale * ss * 4)),
                                0, 180, 360, 255, -1, cv2.LINE_AA, shift=2)
                elif q[0] == 'cap':
                    p0, p1 = np.asarray(q[1]) * scale * ss, np.asarray(q[2]) * scale * ss
                    cv2.line(m, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), 255,
                             max(1, int(2 * q[3] * scale * ss)), cv2.LINE_AA, shift=2)
            mf = m.astype(np.float32) / 255.0
            if lw > 0:
                r_ = max(1, int(round(lw / 1000.0 * scale * ss)))
                outer = cv2.dilate(mf, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r_ + 1, 2 * r_ + 1)))
                edge = np.clip(outer - mf, 0, 1)
            else:
                edge = np.zeros_like(mf)
            mf = cv2.resize(mf, (wid, hgt), interpolation=cv2.INTER_AREA)
            edge = cv2.resize(edge, (wid, hgt), interpolation=cv2.INTER_AREA)
            canvas[..., :3] = canvas[..., :3] * (1 - (wash * 0.85 * k) * mf[..., None]) + INK * (wash * 0.85 * k * 0.25) * mf[..., None]
            canvas[..., :3] = canvas[..., :3] * (1 - (edge * k)[..., None]) + INK * (edge * k)[..., None]
        else:
            _, pts, wpx, sm = it
            canvas = draw_paths(canvas, [(pts, wpx * 1.3, sm)], scale, k, seed=int(rng.integers(0, 1000)))
    return canvas


# ---------------------------------------------------------------- the paper town (pop-up layers)
def town_layer(kind, seed=0):
    """one pop-up cut-out: paper with an ink outline, transparent outside its silhouette; the bottom row is the fold.
    Returns the RGBA card, its window centres (card px) and, for the hill, the crest (card px)."""
    wid, hgt = {'town': (1500, 560), 'village': (1600, 420), 'hill': (1800, 440)}[kind]
    can = np.zeros((hgt, wid, 4), np.float32)
    can[..., :3] = paper(wid, hgt, seed + 40, tone=(0.74, 0.84, 0.90))
    rng = np.random.default_rng(seed)
    sil = np.zeros((hgt * 4, wid * 4), np.uint8)
    lines, windows, crest = [], [], None

    def P(pts):                                                                       # 4x canvas, 2 bits of sub-pixel
        return np.int32(np.asarray(pts, np.float64) * 16)
    if kind == 'hill':
        xs = np.linspace(0, wid, 120)
        ys = hgt - (0.12 * hgt + 0.66 * hgt * np.exp(-((xs - 0.68 * wid) / (0.22 * wid)) ** 2) + 0.10 * hgt * np.exp(-((xs - 0.18 * wid) / (0.2 * wid)) ** 2))
        ys += cv2.GaussianBlur(rng.normal(0, 1, (1, 120)).astype(np.float32), (0, 0), 2)[0] * 3
        ridge = np.stack([xs, ys], 1)
        cv2.fillPoly(sil, [P(np.vstack([ridge, [[wid, hgt], [0, hgt]]]))], 255, cv2.LINE_AA, shift=2)
        lines.append(ridge)
        i = int(np.argmin(ys))
        crest = (float(xs[i]), float(ys[i]))
        for x in rng.uniform(0, wid, 70):                                              # grass on the ridge
            y = np.interp(x, xs, ys)
            lines.append(np.array([(x, y + 2), (x + rng.uniform(-6, 6), y - rng.uniform(8, 18))]))
        for _ in range(3):                                                             # a few contour strokes
            x0 = rng.uniform(0.3, 0.8) * wid
            xx = np.linspace(x0, x0 + rng.uniform(120, 260), 12)
            lines.append(np.stack([xx, np.interp(xx, xs, ys) + rng.uniform(60, 160)], 1))
    else:
        big = kind == 'town'
        x = rng.uniform(5, 25)
        while x < wid - 70:
            w_ = rng.uniform(80, 140) if big else rng.uniform(70, 110)
            h_ = rng.uniform(150, 300) if big else rng.uniform(80, 120)
            style = rng.choice(['gable', 'flat', 'tower'], p=[0.55, 0.30, 0.15]) if big else 'gable'
            if style == 'tower':
                h_ += 110
            top = hgt - h_
            if style == 'gable':
                roof = rng.uniform(35, 65) if big else rng.uniform(40, 60)
                outline = [(x, hgt), (x, top), (x - 6, top), (x + w_ / 2, top - roof), (x + w_ + 6, top), (x + w_, top), (x + w_, hgt)]
                if rng.uniform() < 0.6:                                                 # a chimney
                    cx_ = x + w_ * rng.uniform(0.62, 0.78)
                    cy_ = top - roof * (1 - abs(cx_ - x - w_ / 2) / (w_ / 2 + 6))
                    cv2.fillPoly(sil, [P([(cx_, cy_ + 4), (cx_, cy_ - 28), (cx_ + 14, cy_ - 28), (cx_ + 14, cy_ + 4)])], 255, cv2.LINE_AA, shift=2)
                    lines.append(np.array([(cx_, cy_ + 2), (cx_, cy_ - 28), (cx_ + 14, cy_ - 28), (cx_ + 14, cy_ - 4)]))
            elif style == 'flat':
                outline = [(x, hgt), (x, top), (x + w_, top), (x + w_, hgt)]
                lines.append(np.array([(x, top + 12), (x + w_, top + 12)]))
            else:
                outline = [(x, hgt), (x, top), (x + w_ * 0.5, top - 90), (x + w_, top), (x + w_, hgt)]
            cv2.fillPoly(sil, [P(outline)], 255, cv2.LINE_AA, shift=2)
            lines.append(np.array(outline))
            dw = 22 if big else 18                                                     # a door
            dx = x + w_ * rng.uniform(0.3, 0.6)
            lines.append(np.array([(dx, hgt), (dx, hgt - 40), (dx + dw, hgt - 40), (dx + dw, hgt)]))
            if big:
                cols = 2 if w_ > 95 else 1
                for r_ in range(int((h_ - 70) // 56)):
                    for c_ in range(cols):
                        windows.append((x + w_ * ((0.30 + 0.40 * c_) if cols == 2 else 0.5), top + 34 + 56 * r_))
            else:
                windows.append((x + w_ * (0.75 if dx < x + w_ * 0.45 else 0.25), hgt - 60))
            x += w_ + rng.uniform(6, 26)
        if not big:
            for _ in range(7):                                                         # trees
                tx = rng.uniform(30, wid - 30)
                r_ = rng.uniform(28, 42)
                cv2.circle(sil, (int(tx * 16), int((hgt - 50 - r_) * 16)), int(r_ * 16), 255, -1, cv2.LINE_AA, shift=2)
                cv2.rectangle(sil, (int((tx - 4) * 4), int((hgt - 60) * 4)), (int((tx + 4) * 4), hgt * 4), 255, -1)
                lines.append(ellipse_pts((tx, hgt - 50 - r_), r_, r_, n=30))
    a = cv2.resize(sil.astype(np.float32) / 255, (wid, hgt), interpolation=cv2.INTER_AREA)
    can[..., 3] = a
    edge = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    can[..., :3] = can[..., :3] * (1 - 0.85 * edge[..., None]) + INK * 0.85 * edge[..., None]
    can = draw_paths(can, [(np.asarray(l) / hgt, 2.2, False) for l in lines], hgt, 1.0, seed=seed + 7)
    for wx, wy in windows:
        cv2.rectangle(can, (int(wx - 8), int(wy - 11)), (int(wx + 8), int(wy + 11)), (0.24, 0.20, 0.18, 1.0), 2, cv2.LINE_AA)
    return can, windows, crest


# ---------------------------------------------------------------- the verse
class Verse:
    def __init__(self, opening):
        self.op = opening
        self.prep_page()
        self.prep_kv()
        self.prep_poses()
        self.prep_cards()
        self.prep_town()

    # -- letter page from the opening (same paper, same hand, same hook) and its fragments
    PX0, PY0, PX1, PY1, PS = 0, 950, 2600, 2150, 0.6                                 # page crop (full-res page px), scale
    PU = 600.0                                                                       # texture px per world unit

    def prep_page(self):
        op = self.op
        X0, Y0, X1, Y1, ps = self.PX0, self.PY0, self.PX1, self.PY1, self.PS
        def cut(img):
            return cv2.resize(img[Y0:Y1, X0:X1], (int((X1 - X0) * ps), int((Y1 - Y0) * ps)), interpolation=cv2.INTER_AREA)
        self.page = cut(op.page(3.0))                                                  # dry ink, day colours
        ph, pw = self.page.shape[:2]
        self.page_wh = (pw, ph)
        # the translated page: the hook and the full stop stay; the two lines become another script (illegible)
        alt = OI.Ink([m for m in op.marks if m['kind'] != 'old']).render(op.paper.copy(), 3.0)
        rng = np.random.default_rng(12)
        col = (0.36, 0.27, 0.23)
        for base, xa, xb in ((1424, 236, 2146), (1631, 174, 1129)):
            x = xa
            while x < xb - 60:
                for _ in range(int(rng.integers(2, 6))):                               # a word of 2-5 glyphs
                    if x > xb - 60:
                        break
                    gw, gh = rng.uniform(46, 60), rng.uniform(58, 70)
                    def P(u, v):
                        return (int((x + u * gw + (1 - v) * 8) * 4), int((base + 6 - v * gh) * 4))
                    strokes = [((0.0, 0.85), (1.0, 0.85))] if rng.uniform() < 0.6 else [((0.1, 0.5), (0.9, 0.5))]
                    vx = rng.choice([0.2, 0.5, 0.8])
                    strokes.append(((vx, rng.uniform(0.85, 1.0)), (vx, rng.uniform(0.0, 0.35))))
                    for _k in range(int(rng.integers(1, 3))):
                        kind = rng.integers(0, 4)
                        if kind == 0:
                            y = rng.choice([0.1, 0.45]); strokes.append(((0.15, y), (0.9, y)))
                        elif kind == 1:
                            x2 = rng.choice([0.15, 0.85]); strokes.append(((x2, 0.6), (x2, 0.05)))
                        elif kind == 2:
                            strokes.append(((0.25, 0.7), (0.75, 0.15)))
                        else:
                            strokes.append(((0.6, 0.3), (0.68, 0.22)))
                    for p0, p1 in strokes:
                        cv2.line(alt, P(*p0), P(*p1), col, 6, cv2.LINE_AA, shift=2)
                    x += gw + rng.uniform(10, 16)
                x += rng.uniform(34, 46)
        self.page_alt = cut(alt)
        # where the full stop and the hook are (texture px)
        self.dot_px = np.array([(2044.4 - X0) * ps, (1630.8 - Y0) * ps])
        # fragments: torn shards (Voronoi cells, smaller near the full stop, with jagged edges that two neighbours
        # share exactly, so the page is whole until it tears); tears open from the full stop outward
        rng = np.random.default_rng(5)
        hero = np.array([1180.0, 398.0])                                                # one shard holds the curl and the full stop
        seeds = [hero]
        for _ in range(4000):
            q = rng.uniform((0, 0), (pw, ph))
            dmin = 125 + 0.16 * np.linalg.norm(q - self.dot_px)
            if all(np.linalg.norm(q - s_) > (dmin if np.linalg.norm(s_ - hero) > 1 else 150) for s_ in seeds):
                seeds.append(q)
        sub = cv2.Subdiv2D((-pw, -ph, 3 * pw, 3 * ph))
        for q in seeds:
            sub.insert((float(q[0]), float(q[1])))
        facets, centres = sub.getVoronoiFacetList([])
        nfield = [cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (ph // 8, pw // 8)).astype(np.float32), (0, 0), 1.2), (pw, ph))
                  for _ in range(2)]
        rect = np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]])

        def jag(p0, p1):
            n = max(2, int(np.ceil(np.linalg.norm(p1 - p0) / 9.0)))
            pts = p0[None] + (p1 - p0)[None] * np.linspace(0, 1, n + 1)[:, None]
            out = []
            for q in pts[:-1]:
                xi, yi = int(np.clip(q[0], 0, pw - 1)), int(np.clip(q[1], 0, ph - 1))
                edge = min(q[0], pw - q[0], q[1], ph - q[1])
                amp = 9.0 * np.clip(edge / 6.0, 0, 1)                                   # the sheet's own edge stays straight
                out.append(q + amp * np.array([nfield[0][yi, xi], nfield[1][yi, xi]]) / 0.35)
            return out
        crack = np.zeros((ph, pw), np.float32)
        self.frags = []
        dmax = np.hypot(pw, ph) * 0.75
        ink = (self.page.mean(2) < 0.55).astype(np.float32)
        for fct in facets:
            ok, poly = cv2.intersectConvexConvex(np.float32(fct), rect)
            if ok <= 0 or poly is None or len(poly) < 3:
                continue
            poly = np.round(poly.reshape(-1, 2).astype(np.float64), 3)
            if cv2.contourArea(np.float32(poly)) < 400:
                continue
            jp = []
            for i in range(len(poly)):
                jp += jag(poly[i], poly[(i + 1) % len(poly)])
            jp = np.array(jp)
            bx0, by0 = np.floor(jp.min(0)).astype(int) - 2
            bx1, by1 = np.ceil(jp.max(0)).astype(int) + 2
            bx0, by0, bx1, by1 = max(bx0, 0), max(by0, 0), min(bx1, pw), min(by1, ph)
            m = np.zeros((by1 - by0, bx1 - bx0), np.float32)
            cv2.fillPoly(m, [np.int32((jp - (bx0, by0)) * 4)], 1.0, cv2.LINE_AA, shift=2)
            a = m
            fibre = np.clip(a - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1)        # the torn edge shows the paper's white core
            cv2.polylines(crack, [np.int32(jp * 4)], True, 1.0, 1, cv2.LINE_AA, shift=2)
            ctr = jp.mean(0)
            d = np.linalg.norm(ctr - self.dot_px)
            self.frags.append(dict(box=(bx0, by0, bx1, by1), alpha=a, fibre=fibre, ctr=ctr,
                                   text=float((ink[by0:by1, bx0:bx1] * a).sum() / (a.sum() + 1)),
                                   hero=bool(cv2.pointPolygonTest(np.float32(jp), (float(hero[0]), float(hero[1])), False) >= 0),
                                   delay=0.30 * d / dmax + rng.uniform(0, 0.06),
                                   out=np.r_[(ctr - self.dot_px) / dmax, 0.0],
                                   rise=rng.uniform(0.45, 0.85), axis=rng.normal(0, 1, 3), spin=rng.uniform(0.5, 1.3),
                                   seed=int(rng.integers(0, 1 << 30))))
        yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
        self.crack = cv2.GaussianBlur(crack, (0, 0), 0.5)
        self.crack_t = 17.42 + 0.27 * np.clip(np.hypot(xx - self.dot_px[0], yy - self.dot_px[1]) / dmax, 0, 1)

    def prep_kv(self):
        k5 = cv2.imread(os.path.join(PLATES, 'KV5a.png'))
        m = np.zeros(k5.shape[:2], np.uint8)
        cv2.ellipse(m, (1361, 1190), (62, 92), 0, 0, 360, 255, -1)
        self.kv5a = OI_crop(cv2.inpaint(k5, m, 9, cv2.INPAINT_TELEA).astype(np.float32), 160)
        self.kv5 = OI_crop(cv2.imread(os.path.join(PLATES, 'KV5.png')).astype(np.float32), 160)
        k4 = cv2.imread(os.path.join(PLATES, 'KV4.png')).astype(np.float32)
        m4 = cv2.imread(os.path.join(PLATES, 'KV4_matte.png'), 0).astype(np.float32) / 255
        self.kv4 = OI_crop(k4, 160)
        self.kv4a = np.clip(OI_crop(np.dstack([m4] * 3), 160)[..., 0], 0, 1)

    def prep_poses(self):
        self.A1 = load_pose('A1')
        self.A3 = load_pose('A3')
        self.B3 = load_pose('B3')

    def prep_cards(self):
        self.cw, self.ch = 960, 640
        self.base = {k: paper(self.cw, self.ch, s, tone=(0.86, 0.92, 0.95)) for k, s in
                     (('war', 1), ('lull', 2), ('fare', 3), ('heat', 4), ('born', 5), ('fire', 6), ('art', 7))}

    def card(self, kind, paths, prog, light_c=None, light_r=280, light_k=1.0, night=(0.40, 0.38, 0.50)):
        can = np.dstack([self.base[kind].copy(), np.ones((self.ch, self.cw), np.float32)])
        can = render_art(can, paths, self.ch, prog, seed=sum(map(ord, kind)))
        if light_c is not None:
            can = light_pool(can, (light_c[0] * self.ch, light_c[1] * self.ch), light_r, night=night, k=light_k)
        else:
            can[..., :3] *= np.array(night, np.float32)
        return can

    # the pop-up book: layers stand on fold lines in the page (z), width and height in world units
    TOWN = dict(town=(0.55, 1.75), village=(1.05, 2.5), hill=(1.60, 3.4))

    # -- supplied artwork: each memory card is layered PNGs on one 1536x1024 canvas (3:2, like the card). When a shot's
    #    files are all present they replace its placeholder drawing; the code keeps the motion, the lights and the glows.
    def art(self, name):
        if not hasattr(self, '_art'):
            self._art = {}
        if name not in self._art:
            path = os.path.join(ART, name + '.png')
            if not os.path.exists(path):
                self._art[name] = None
            else:
                im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                im = cv2.resize(im, (self.cw, self.ch), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
                if im.ndim == 2:
                    im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
                if im.shape[2] == 3:                                                   # no transparency: white is empty
                    a = white_matte(im * 255.0) if not name.endswith('_bg') and name != 'bowl' else np.ones(im.shape[:2], np.float32)
                    im = np.dstack([im, a])
                self._art[name] = im
        return self._art[name]

    def art_ready(self, *names):
        return all(self.art(n) is not None for n in names)

    def art_card(self, layers, light_c, light_r=280, light_k=1.0, night=(0.40, 0.38, 0.50), alpha_from=None):
        """layers: (name, 2x3 affine in card px or None), back to front, over the card paper; then the night light."""
        can = np.dstack([self.base['art'].copy(), np.ones((self.ch, self.cw), np.float32)])
        for name, M in layers:
            lay = self.art(name)
            if M is not None:
                lay = cv2.warpAffine(lay, M, (self.cw, self.ch), flags=cv2.INTER_LINEAR)
            a = lay[..., 3:4]
            can[..., :3] = can[..., :3] * (1 - a) + lay[..., :3] * a
        if alpha_from is not None:
            can[..., 3] = self.art(alpha_from)[..., 3]
        return light_pool(can, (light_c[0] * self.ch, light_c[1] * self.ch), light_r, night=night, k=light_k)

    def rot_about(self, pivot, ang):
        c = (pivot[0] * self.ch, pivot[1] * self.ch)
        return cv2.getRotationMatrix2D(c, -np.degrees(ang), 1.0)

    def shift(self, dx, dy):
        return np.float32([[1, 0, dx * self.ch], [0, 1, dy * self.ch]])

    def prep_town(self):
        self.layers = {}
        for k, seed in (('town', 3), ('village', 2), ('hill', 1)):
            tex, wins, crest = town_layer(k, seed)
            zl, wl = self.TOWN[k]
            hl = wl * tex.shape[0] / tex.shape[1]
            self.layers[k] = dict(tex=tex, wins=wins, crest=crest, z=zl, w=wl, h=hl)
        g = paper(1760, 960, 9, tone=(0.74, 0.84, 0.90))                                  # the page: 4.4 x 2.4, z -0.2..2.2
        for k in self.TOWN:                                                              # pop-up creases along the folds
            y = int((2.2 - self.TOWN[k][0]) / 2.4 * 960)
            cv2.line(g, (0, y), (1759, y), (0.55, 0.62, 0.68), 2, cv2.LINE_AA)
            cv2.line(g, (0, y + 2), (1759, y + 2), (0.86, 0.94, 0.98), 1, cv2.LINE_AA)
        self.ground = np.dstack([g, np.ones((960, 1760), np.float32)])
        L = self.layers['hill']
        cx_, cy_ = L['crest']
        th, tw = L['tex'].shape[:2]
        self.crest = np.array([(cx_ / tw - 0.5) * L['w'], (1 - cy_ / th) * L['h'], L['z']])

    # ------------------------------------------------------------ shots
    def v1a(self, t):
        """KV5a: the light in A's palm flickers on the burst; she offers it (key pose, held)."""
        img = self.kv5a.copy()
        c = (1361 * OI.S, (1205 - 160) * OI.S)
        burst = [13.804, 13.874, 13.932, 13.990]
        it = 1.0 + sum(0.7 * np.exp(-(t - b) / 0.05) for b in burst if t >= b) + 0.4 * ease(14.47, 14.8, t)
        return glow(img, c, 0.5 + 0.1 * ease(14.47, 14.95, t), it)

    def v1b(self, t):
        """A3, close: at the hit the light opens into a sheet of paper that rises from her palm toward us."""
        img = night_backdrop(1)
        img = glow(img, (640, 900), 2.0, 0.35)                                       # the Earth's glow below frame
        src, a = self.A3
        pal = (700.0, 800.0)                                                           # her palm (image px)
        lit = relight(src, a, pal, 420, 1.0)
        img, M = place(img, lit, a, 400, 380, 1400)
        p = M @ np.array([pal[0], pal[1] - 40, 1.0])
        u = ease(14.97, 15.875, t)
        if u <= 0:
            return glow(img, p, 0.45, 1.4)
        cam = Cam((0, 0, -3.0), (0, 0, 0))
        # the sheet: edge-on, opening to face us as it comes closer, then tilting back to lie as P1a sees it; it is
        # already the lit letter of P1a's first frame, so the cut is a continuation
        pw, ph = self.page_wh
        open_ = smooth(u / 0.6)
        back = smooth((u - 0.6) / 0.4)
        ang = -(1 - open_) * np.radians(85) + back * np.radians(38)                     # top edge recedes at the end, as in P1a
        zc = -1.55 * u ** 1.6
        sz = 0.16 + 0.80 * u ** 1.4
        ctr = np.array([(p[0] - 640) / F * 3.0 * (1 - u ** 1.5), -(p[1] - 360) / F * 3.0 * (1 - u ** 1.5) + 0.10 * u, zc])
        v = rot_axis(np.array([0, 1.0, 0]), (1, 0, 0), ang)
        corners = card_corners(ctr, (1, 0, 0), v, sz * pw / ph, sz)
        lit = self.lit_page(15.9)
        tex = np.dstack([lit * (0.6 + 0.4 * u) + np.array([0.25, 0.42, 0.55], np.float32) * (1 - u) ** 2, np.ones((ph, pw), np.float32)])
        img, _ = put_card(img, cam, corners, tex)
        return glow(img, cam.project(ctr)[0][0], 0.6 + 0.4 * u, 1.2 * (1 - 0.7 * u))

    # -- the letter, P1a/P1b. Page plane y = 0, x right, z away from camera; texture top = far edge.
    def tex2world(self, q):
        pw, ph = self.page_wh
        q = np.asarray(q, np.float64)
        return np.stack([q[..., 0] / self.PU - pw / self.PU / 2, np.zeros(q.shape[:-1]), ph / self.PU / 2 - q[..., 1] / self.PU], -1)

    def reader_light(self, t):
        """the light that came from her palm reads the letter: it travels along the lines and settles in the full stop
        (17.35), then rises out of it with the fragments (17.71)."""
        dot = self.tex2world(self.dot_px)
        u = ease(15.95, 17.35, t)
        x = -1.05 + (dot[0] + 1.05) * u
        z = 0.04 + (dot[2] - 0.04) * ease(16.9, 17.35, t)
        y = 0.10 - 0.09 * ease(17.0, 17.35, t) + 0.55 * ease(17.71, 18.9, t) ** 1.3
        return np.array([x, y, z])

    def lit_page(self, t, src=None):
        """the page at night, lit by the reader light (plus a faint warm trace on the words already read)."""
        pw, ph = self.page_wh
        L = self.reader_light(t)
        if getattr(self, '_lit_t', None) == (t, id(src)):
            return self._lit
        if not hasattr(self, '_pxw'):
            yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
            self._pxw = (xx / self.PU - pw / self.PU / 2, ph / self.PU / 2 - yy / self.PU)
        X, Z = self._pxw
        d2 = (X - L[0]) ** 2 + (Z - L[2]) ** 2 + L[1] ** 2
        pool = 1.0 / (1.0 + d2 / 0.09) * (0.55 + 0.45 * ease(15.875, 16.3, t))
        trail = 0.28 * np.exp(-((Z - 0.04) / 0.22) ** 2) * smooth((L[0] - X) / 0.35 + 0.5) * np.exp(-np.clip(L[0] - X, 0, None) / 1.4)
        lit = np.clip(pool + trail * (t < 17.9), 0, 1.4)[..., None]
        night = np.array([0.40, 0.36, 0.42], np.float32)
        warm = np.array([0.62, 0.86, 1.10], np.float32)
        base = self.page if src is None else src
        out = base * (night * (1 - np.clip(lit, 0, 1)) + warm * lit)
        # cracks: the light leaks through the page along the tear lines, outward from the full stop
        if 17.42 <= t:
            em = self.crack * (self.crack_t < t) * (1 - ease(17.9, 18.3, t))
            out = out + em[..., None] * np.array([0.35, 0.70, 1.0], np.float32) * 1.0
        self._lit, self._lit_t = out, (t, id(src))
        return out

    def frag_pose(self, fr, t):
        """centre, u, v of a fragment at time t (P1a)."""
        bx0, by0, bx1, by1 = fr['box']
        c0 = self.tex2world(np.array([(bx0 + bx1) / 2, (by0 + by1) / 2]))
        k = max(0.0, t - 17.71 - fr['delay'])
        c = c0 + np.array([0, 1.0, 0]) * fr['rise'] * (0.30 * k + 0.35 * k * k) + fr['out'][[0, 2, 1]] * np.array([1, 0, -1]) * 0.30 * k
        ang = fr['spin'] * k * 1.1
        u = rot_axis(np.array([1.0, 0, 0]), fr['axis'], ang)
        v = rot_axis(np.array([0, 0, 1.0]), fr['axis'], ang)
        return c, u, v, k

    def p1a(self, t):
        """the letter, close: the light reads the words ("in the words that you left"), settles in the full stop, and
        the page cracks open from it and lifts in fragments ("we met you in fragments")."""
        img = night_backdrop(2, top=(22, 14, 10), bottom=(34, 22, 16))
        L = self.reader_light(t)
        g = ease(15.875, 17.35, t)
        tx = -0.62 + 1.20 * g + 0.10 * ease(17.35, 18.6, t)
        tz = 0.02 - 0.06 * ease(17.0, 17.6, t)
        h = 0.56 + 0.16 * ease(15.875, 16.6, t) + 0.38 * ease(17.6, 18.6, t)
        back = 0.50 + 0.12 * ease(15.875, 16.6, t) + 0.30 * ease(17.6, 18.6, t)
        cam = Cam((tx - 0.10, h, tz - back), (tx, 0.0, tz), roll=0.05 - 0.07 * g)
        focus = float(np.linalg.norm(np.array([tx, 0, tz]) - cam.p))
        pw, ph = self.page_wh
        lit = self.lit_page(t)
        if t < 17.71:
            tex = np.dstack([lit, np.ones((ph, pw), np.float32)])
            img, _ = put_card(img, cam, card_corners((0, 0, 0), (1, 0, 0), (0, 0, 1), pw / self.PU, ph / self.PU), tex,
                              focus=focus, aperture=0.45, dof_map=True)
        else:
            cards = []
            rest = np.ones((ph, pw), np.float32)                                         # what is still lying on the page
            for fr in self.frags:
                bx0, by0, bx1, by1 = fr['box']
                c, u, v, k = self.frag_pose(fr, t)
                if k <= 0:
                    continue
                rest[by0:by1, bx0:bx1] -= fr['alpha']
                tex = np.dstack([lit[by0:by1, bx0:bx1] * (1 + 0.25 * min(1.0, k * 2)) + fr['fibre'][..., None] * 0.18, fr['alpha']])
                corners = card_corners(c, u, v, (bx1 - bx0) / self.PU, (by1 - by0) / self.PU)
                cards.append((float((c - cam.p) @ cam.fw), corners, tex))
            tex = np.dstack([lit, np.clip(rest, 0, 1)])
            img, _ = put_card(img, cam, card_corners((0, 0, 0), (1, 0, 0), (0, 0, 1), pw / self.PU, ph / self.PU), tex,
                              focus=focus, aperture=0.45, dof_map=True)
            for zc, corners, tex in sorted(cards, key=lambda q: -q[0]):
                img, _ = put_card(img, cam, corners, tex, focus=focus, aperture=0.45)
        p, z = cam.project(L)
        if z[0] > 0.05:
            img = glow(img, p[0], 0.22 + 0.10 * ease(17.71, 18.6, t), 1.25)
            OI.dot(img, p[0], 2.2, 1.0)
        return img

    def a1(self, t):
        """A1, close: she looks up into the drifting fragments; some pass in front of her, close and dark."""
        img = night_backdrop(3, top=(36, 22, 16), bottom=(60, 36, 26))
        cam = Cam((0, 0, -2.0), (0, 0, 0))
        rng = np.random.default_rng(31)
        lit = self.page * np.array([0.58, 0.74, 0.95], np.float32)
        for k in range(9):                                                             # behind her, small, lit
            fr = self.frags[(k * 4 + 2) % len(self.frags)]
            pos = np.array([rng.uniform(-0.6, 1.6), rng.uniform(-0.1, 0.9) + 0.25 * (t - 18.6), rng.uniform(1.0, 3.0)])
            ang = 0.9 * (t - 18.6) + k
            u = rot_axis(np.array([1.0, 0, 0]), fr['axis'], ang)
            v = rot_axis(np.array([0, 1.0, 0]), fr['axis'], ang)
            bx0, by0, bx1, by1 = fr['box']
            tex = np.dstack([lit[by0:by1, bx0:bx1], fr['alpha']])
            img, _ = put_card(img, cam, card_corners(pos, u, v, (bx1 - bx0) / self.PU * 1.1, (by1 - by0) / self.PU * 1.1), tex,
                              focus=2.6, aperture=0.6)
        src, a = self.A1
        lit_a = relight(src, a, (760, 300), 460, 0.85)
        img, _ = place(img, lit_a, a, 380 + 8 * (t - 18.6), 420, 1300)
        for k in range(2):                                                             # in front of her, close: dark paper
            fr = self.frags[k * 7 + 3]
            x = 2.0 - 3.4 * ((t - 18.62 + 0.45 * k) / 1.0)
            pos = np.array([x * 0.6, 0.35 - 0.75 * k, -1.15 + 0.15 * k])
            ang = 1.2 * (t - 18.6) + k
            u = rot_axis(np.array([1.0, 0, 0]), fr['axis'], ang)
            v = rot_axis(np.array([0, 1.0, 0]), fr['axis'], ang)
            bx0, by0, bx1, by1 = fr['box']
            tex = np.dstack([self.page[by0:by1, bx0:bx1] * np.array([0.22, 0.24, 0.30]), fr['alpha']])
            img, _ = put_card(img, cam, card_corners(pos, u, v, 0.34, 0.30), tex, focus=2.0, aperture=1.0)
        return glow(img, (930, 140), 1.2, 0.35)

    def candle_xy(self):
        cam = Cam((0.10, 0.05, -1.95), (0, 0, 0))                                      # M1's first frame
        return cam.project(np.array([0.312 - 0.75, 0.5 - 0.38, 0.0]))[0][0]

    def p1b(self, t, sub=True):
        """the fragments in the air, frontal: "translated" (19.55-20.0) the writing on every piece turns into another
        script, a scan line passing across them; "compressed" (20.22-20.458) they fold into one point, which lands
        where the next shot's candle flame is."""
        if sub and t >= 20.20:                                                         # motion blur through the fold
            return sum(self.p1b(t + d, False) for d in (-1 / 72, 0.0, 1 / 72)) / 3
        cam = Cam((0.0, 0.10 * (t - 19.5), -1.75), (0.0, 0.10 * (t - 19.5), 0.0))
        img = night_backdrop(5, top=(20, 12, 9), bottom=(30, 20, 15))
        cxy = self.candle_xy()
        d = cam.fw + (cxy[0] - cam.cx) / cam.f * cam.rt - (cxy[1] - cam.cy) / cam.f * cam.up
        Pc = cam.p + d / (d @ cam.fw) * 1.75
        Lc = np.array([0.10, 0.20 + 0.10 * (t - 19.5), -0.12])
        scan = -120 + 1520 * ease(19.55, 20.0, t)
        comp = ease(20.20, 20.42, t) ** 1.5
        if not hasattr(self, 'cloud'):
            # the shard with the curl and the full stop at the centre, in focus; the shards that carry writing around it
            # (in focus, so the change of script reads); blank ones behind (soft) and a few passing close (dark, soft)
            rng = np.random.default_rng(77)
            order = sorted(range(len(self.frags)), key=lambda i: -self.frags[i]['text'])
            hero = next(i for i, f in enumerate(self.frags) if f['hero'])
            ring = [i for i in order if i != hero and self.frags[i]['box'][2] - self.frags[i]['box'][0] < 300][:7]
            cl = []
            for i, fr in enumerate(self.frags):
                if i == hero:
                    pos, a0, w = np.array([-0.08, 0.0, 0.0]), 0.0, 0.12
                elif i in ring:
                    j = ring.index(i)
                    ang = 2 * np.pi * j / len(ring) + 0.4
                    pos = np.array([0.66 * np.cos(ang), 0.37 * np.sin(ang), rng.uniform(0.0, 0.25)])
                    a0, w = rng.uniform(-0.35, 0.35), rng.uniform(0.15, 0.3) * rng.choice([-1, 1])
                elif rng.uniform() < 0.18:
                    pos = np.array([rng.choice([-1, 1]) * rng.uniform(0.55, 0.9), rng.uniform(-0.45, 0.45), rng.uniform(-0.95, -0.7)])
                    a0, w = rng.uniform(-0.6, 0.6), rng.uniform(0.3, 0.6) * rng.choice([-1, 1])
                else:
                    pos = np.array([rng.uniform(-2.2, 2.2), rng.uniform(-1.1, 1.1), rng.uniform(0.9, 2.8)])
                    a0, w = rng.uniform(-0.8, 0.8), rng.uniform(0.2, 0.5) * rng.choice([-1, 1])
                cl.append(dict(fr=fr, pos=pos, axis=rng.normal(0, 1, 3), a0=a0, w=w, near=pos[2] < -0.5))
            self.cloud = cl
        cards = []
        pw, ph = self.page_wh
        for c in self.cloud:
            fr = c['fr']
            bx0, by0, bx1, by1 = fr['box']
            pos = c['pos'] + np.array([0, 0.10 * (t - 19.5), 0])
            ang = c['a0'] + c['w'] * (t - 19.5)
            u = rot_axis(np.array([1.0, 0, 0]), c['axis'], ang)
            v = rot_axis(np.array([0, 1.0, 0]), c['axis'], ang)
            if comp > 0:
                pos = pos * (1 - comp) + Pc * comp
            sz = 1.0 - 0.96 * comp
            w_, h_ = (bx1 - bx0) / self.PU * sz, (by1 - by0) / self.PU * sz
            corners = card_corners(pos, u, v, w_, h_)
            xy, z = cam.project(corners)
            if (z < 0.05).any():
                continue
            pa, pb = self.page[by0:by1, bx0:bx1], self.page_alt[by0:by1, bx0:bx1]
            cols = np.linspace(xy[0, 0], xy[1, 0], bx1 - bx0)[None, :]                   # screen x of each texel column
            mix = np.clip((scan - cols) / 40.0, 0, 1)[..., None]
            line = np.exp(-((scan - cols) / 10.0) ** 2)[..., None] * (0 < ease(19.55, 20.0, t) < 1)
            dl = np.linalg.norm(pos - Lc)
            shade = 0.55 + 0.75 * np.exp(-(dl / 1.0) ** 2)
            col = (pa * (1 - mix) + pb * mix) * np.array([0.60, 0.80, 1.05], np.float32) * shade
            col = col + line * np.array([0.30, 0.65, 1.0], np.float32) * 0.9
            col = col * (1 + 2.5 * comp) + np.array([0.15, 0.45, 0.8], np.float32) * comp
            if c['near']:
                col = col * 0.30
            tex = np.dstack([col + fr['fibre'][..., None] * 0.15, fr['alpha']])
            cards.append((float((pos - cam.p) @ cam.fw), corners, tex))
        for zc, corners, tex in sorted(cards, key=lambda q: -q[0]):
            img, _ = put_card(img, cam, corners, tex, focus=1.75, aperture=0.6)
        p = cam.project(Lc * (1 - comp) + Pc * comp)[0][0]
        img = glow(img, p, 0.20 + 0.25 * comp, 0.9 + 1.2 * comp)
        self.compress_pt = cxy
        return img

    def memory(self, t, kind, t0, t1, cam_from, cam_to):
        """a memory card: frontal, slightly in perspective, a slow push."""
        u = (t - t0) / (t1 - t0)
        cp = np.array(cam_from) * (1 - u) + np.array(cam_to) * u
        cam = Cam(cp, (0, 0, 0))
        img = night_backdrop(4, top=(24, 14, 10), bottom=(36, 22, 16))
        prog = ease(t0, t0 + 0.45, t) * 0.999 + 0.001
        if kind == 'war':
            prog = 1.0                                                                   # the room is there; the candle reveals it
        if kind == 'war':
            paths = art_war(t)
            rev = ease(20.458, 21.0, t)                                                  # the candle reveals the room
            tex = self.card('war', paths, prog, light_c=(0.31, 0.38), light_r=70 + 290 * rev,
                            night=tuple(np.array([0.40, 0.38, 0.50]) * (0.15 + 0.85 * rev)))
            lc = (0.31, 0.38)
        elif kind == 'lull':
            rock = np.radians(4.0) * np.sin(2 * np.pi * 0.72 * (t - t0))
            if self.art_ready('lullaby_bg', 'lullaby_cradle'):
                tex = self.art_card([('lullaby_bg', None), ('lullaby_cradle', self.rot_about((0.78, 0.80), rock))], (0.21, 0.40), 420)
            else:
                tex = self.card('lull', art_lullaby(t, rock), prog, light_c=(0.21, 0.40), light_r=420)
            lc = (0.21, 0.40)
        else:
            go = max(0.0, t - 24.45)
            part = ease(24.15, 24.55, t)
            if self.art_ready('farewell_bg', 'farewell_train'):
                tex = self.art_card([('farewell_bg', None), ('farewell_train', self.shift(-0.03 * part - 0.9 * go ** 2, 0))],
                                    (0.85, 0.45), 380, 0.9)
            else:
                tex = self.card('fare', art_farewell(t, -0.03 * part - 0.9 * go ** 2, 0.06 * part), prog, light_c=(0.85, 0.45),
                                light_r=380, light_k=0.9)
            lc = (0.86, 0.55)
        corners = card_corners((0, 0, 0), (1, 0, 0), (0, 1, 0), 1.5, 1.0)
        img, _ = put_card(img, cam, corners, tex)

        def at(x, y):
            return cam.project(np.array([x - 0.75, 0.5 - y, 0.0]))[0][0]
        if kind == 'war':
            img = flame(img, at(0.312, 0.38), 9, t, k=1.0)
            rng = np.random.default_rng(9)                                               # dust in the candlelight
            for k in range(22):
                p = at(rng.uniform(0.1, 0.7), (rng.uniform(0.05, 0.6) + 0.04 * (t - t0)) % 0.65)
                cv2.circle(img, (int(p[0]), int(p[1])), 1, (110, 150, 180), -1, cv2.LINE_AA)
            hk = ease(21.6, 21.95, t) * (1 - 0.5 * ease(22.0, 22.25, t))
            img = glow(img, at(0.83, 0.68), 0.12, 0.9 * hk)                              # the hook mark catches the light
        elif kind == 'lull':
            img = glow(img, at(0.21, 0.40), 0.55, 0.85)
            img = glow(img, at(0.21, 0.40), 0.12, 0.6)
        else:
            if t > 24.35:
                y = 0.555 - 0.5 * ease(24.55, 25.0, t)
                img = glow(img, at(0.875, y), 0.10 + 0.05 * ease(24.55, 25.0, t), 1.3 * ease(24.35, 24.5, t))
            img = glow(img, at(1.40, 0.15), 0.35, 0.5)
        return img

    def wipe(self, img, t, tc, seed):
        """a paper fragment crossing close to the lens (foreground occlusion) as the cut happens."""
        u = (t - (tc - 0.16)) / 0.32
        if u <= 0 or u >= 1:
            return img
        cam = Cam((0, 0, -1.0), (0, 0, 0))
        fr = self.frags[seed % len(self.frags)]
        bx0, by0, bx1, by1 = fr['box']
        tex = np.dstack([self.page[by0:by1, bx0:bx1] * np.array([0.35, 0.42, 0.55]), fr['alpha']])
        x = 1.4 - 2.8 * u
        u_ = rot_axis(np.array([1.0, 0, 0]), (0.2, 1, 0.1), 0.6 * u)
        img, _ = put_card(img, cam, card_corners((x, 0.05, -0.35), u_, (0, 1, 0), 1.6, 1.15), tex, extra_blur=9)
        return img

    def constellations(self, t):
        """KV1 again: the same two from behind; the sky and the Earth fall away (a mind with no sky) and the three
        memories rise as constellations shaped like what they were."""
        op = self.op
        g = op.girls
        col, a = g.crop, g.alpha
        k_up = ease(25.9, 26.8, t)
        if k_up > 0:
            col, a = g.head(col, a, OI.A_HEAD, k_up, dy=18.0, horn=18.0, dx=0.0)
            col, a = g.head(col, a, OI.B_HEAD, k_up * 0.8, dy=10.0, horn=0.0, dx=0.0)
        z = 1.0 + 0.05 * ease(25.0, 28.6, t)
        c = np.array([640.0, 420.0])
        M = np.float32([[OI.S * z, 0, c[0] * (1 - z)], [0, OI.S * z, c[1] * (1 - z)]])
        bg = cv2.warpAffine(op.crop, M, (W, H), flags=cv2.INTER_AREA)
        fgc = cv2.warpAffine(col * a[..., None], M, (W, H), flags=cv2.INTER_AREA)
        fa = cv2.warpAffine(a, M, (W, H))[..., None]
        dark = 1 - 0.93 * ease(25.0, 25.9, t)
        img = bg * dark
        # the three memories as constellations traced along their own outlines, left to right
        for i, (ctr, t0) in enumerate((((240, 185), 25.9), ((640, 140), 26.3), ((1040, 185), 26.7))):
            u = ease(t0, t0 + 1.0, t)
            if u <= 0:
                continue
            lines = np.zeros((H, W, 3), np.float32)
            stars = []
            polys = CONST[i]
            total = sum(len(pl) for pl in polys)
            shown = int(total * u + 0.999)
            for pl in polys:
                xy = np.array(ctr) + (np.asarray(pl, np.float64) - (0.75, 0.5)) * 255 * z
                m = min(len(xy), shown)
                shown -= m
                for j in range(m - 1):
                    cv2.line(lines, tuple(np.int32(xy[j] * 4)), tuple(np.int32(xy[j + 1] * 4)), (80, 130, 180), 2, cv2.LINE_AA, shift=2)
                stars += list(xy[:m])
            img = img + cv2.GaussianBlur(lines, (0, 0), 0.8) + 0.6 * cv2.GaussianBlur(lines, (0, 0), 5.0)
            for j, q in enumerate(stars):
                OI.dot(img, q, 1.4 + 0.8 * (j % 4 == 0), 1.0 + 0.25 * np.sin(t * 3 + j))
        if t < 25.6:                                                                   # the parting spark rises in
            y = 760 - 640 * ease(25.0, 25.6, t)
            img = glow(img, (950, y), 0.12, 1.2)
        return img * (1 - fa) + fgc

    # -- B's half: the paper town
    def town_scene(self, t, cam, up, key, lights=None, focus=1.5, haze=None, stars=0.0, sun_x=None, cold=0.0):
        """the pop-up page. up[k]: 0 (flat on the page) .. 1 (standing); key: warm light on the paper (0 night .. 1 dusk);
        lights[k]: fraction of windows lit."""
        img = night_backdrop(6, top=(30, 16, 10), bottom=(46, 28, 20))
        rng = np.random.default_rng(14)
        for k in range(70):                                                            # stars (only when asked)
            if stars > 0:
                OI.dot(img, (rng.uniform(0, W), rng.uniform(0, 330)), 0.7 + 0.5 * (k % 7 == 0), stars * rng.uniform(0.3, 0.9))
        night = np.array([0.40, 0.38, 0.48], np.float32)
        warm = np.array([0.60, 0.84, 1.08], np.float32)
        tint = night * (1 - key) + warm * key
        tint = tint * (1 - cold) + np.array([0.46, 0.34, 0.28], np.float32) * cold      # moonlight, cold
        g = self.ground.copy()
        g[..., :3] *= tint * 0.92
        if sun_x is not None:                                                          # the light crossing the page
            xx = np.linspace(-2.2, 2.2, g.shape[1], dtype=np.float32)[None, :]
            g[..., :3] *= (1 + 0.45 * np.exp(-((xx - sun_x) / 0.9) ** 2))[..., None]
        img, _ = put_card(img, cam, card_corners((0, 0, 1.0), (1, 0, 0), (0, 0, 1), 4.4, 2.4), g, focus=focus,
                          aperture=0.35, dof_map=True)
        glows = []
        for name in ('hill', 'village', 'town'):
            L = self.layers[name]
            u_ = float(np.clip(up.get(name, 1.0), 0, 1))
            if u_ < 0.01:
                continue
            ang = (np.pi / 2) * smooth(u_)
            base = np.array([0.0, 0.0, L['z']])
            v = np.array([0.0, np.sin(ang), -np.cos(ang)])
            corners = card_corners(base + v * L['h'] / 2, (1, 0, 0), v, L['w'], L['h'])
            tex = L['tex'].copy()
            hz = (haze or {}).get(name, 0.0)
            tex[..., :3] = tex[..., :3] * tint * (1 - hz) + np.array([0.20, 0.14, 0.11], np.float32) * hz
            if sun_x is not None:
                xx = np.linspace(-L['w'] / 2, L['w'] / 2, tex.shape[1], dtype=np.float32)[None, :]
                tex[..., :3] *= (1 + 0.40 * np.exp(-((xx - sun_x) / 0.9) ** 2))[..., None]
            # its shadow on the page, falling away from the light
            if ang > 0.2:
                sh = np.zeros_like(tex)
                sh[..., 3] = L['tex'][..., 3] * 0.42 * smooth((ang - 0.2) / 0.8)
                sx = 0.0 if sun_x is None else -0.35 * np.tanh(sun_x)
                d = np.array([sx, 0.0, 0.55]) / np.linalg.norm([sx, 0.0, 0.55])
                c_ = base + d * L['h'] * 0.35
                img, _ = put_card(img, cam, card_corners(c_, (1, 0, 0), d, L['w'], L['h'] * 0.7), sh, extra_blur=3.0)
            fr = (lights or {}).get(name, 0.0)
            if fr > 0:
                rng = np.random.default_rng(len(L['wins']))
                order = rng.permutation(len(L['wins']))
                th, tw = tex.shape[:2]
                for j in order[:int(round(fr * len(order)))]:
                    wx, wy = L['wins'][j]
                    cv2.rectangle(tex, (int(wx - 7), int(wy - 10)), (int(wx + 7), int(wy + 10)), (0.42, 0.78, 1.05, 1.0), -1)
                    glows.append(base + v * L['h'] * (1 - wy / th) + np.array([(wx / tw - 0.5) * L['w'], 0, -0.01]))
            img, _ = put_card(img, cam, corners, tex, focus=focus, aperture=0.35, dof_map=True)
            if name == 'town' or name == 'village':
                pass
        if glows:
            xy, z = cam.project(np.array(glows))
            for q, zz in zip(xy, z):
                if zz > 0.05 and -20 < q[0] < W + 20 and -20 < q[1] < H + 20:
                    OI.dot(img, q, 1.6, 0.55)
        return img

    def d1(self, t):
        """KV4: B, close, looking down; below her the town pops up out of the page ("depth"), and a day passes over it
        until the windows light ("time")."""
        u = ease(28.583, 30.458, t)
        cam = Cam((-0.70 + 0.10 * u, 1.00, -0.55), (-0.32 + 0.06 * u, 0.12, 0.95))
        pop = {'hill': ease(28.65, 29.05, t), 'village': ease(28.85, 29.20, t), 'town': ease(29.0, 29.40, t)}
        sun = ease(29.56, 30.15, t)
        key = 0.75 * (1 - ease(30.0, 30.35, t)) if t < 30.15 else 0.75 * (1 - ease(30.0, 30.35, t))
        lights = {'town': ease(30.0, 30.40, t), 'village': ease(30.1, 30.45, t)}
        img = self.town_scene(t, cam, pop, key, lights, focus=1.55, haze={'hill': 0.30, 'village': 0.12},
                              sun_x=(-2.0 + 4.0 * sun) if 29.5 < t < 30.2 else None)
        z = 1.0 + 0.02 * u
        M = np.float32([[z, 0, 1280 * (1 - z) * 0.85], [0, z, 0]])
        fg = cv2.warpAffine(self.kv4 * self.kv4a[..., None], M, (W, H))
        fa = cv2.warpAffine(self.kv4a, M, (W, H))[..., None]
        return img * (1 - fa) + fg

    def d2(self, t):
        u = (t - 30.458) / (32.292 - 30.458)
        cam = Cam((0.05 * u, 0.02, -1.85 + 0.25 * u), (0, 0, 0))
        img = night_backdrop(7, top=(26, 18, 14), bottom=(40, 28, 20))
        if self.art_ready('bowl'):
            tex = self.art_card([('bowl', None)], (0.75, 0.60), 430, 1.15, night=(0.45, 0.42, 0.52))
            for k in range(4):                                                          # the steam stays code
                tex = draw_paths(tex, [(np.stack([0.66 + 0.06 * k + 0.025 * np.sin(np.linspace(0.52, 0.12, 20) * 18 + t * 3.2 + k * 1.7),
                                                  np.linspace(0.52, 0.12, 20)], 1), 1.6, True)], self.ch, 1.0,
                                 col=np.array([0.80, 0.86, 0.90], np.float32), alpha=0.5)
        else:
            tex = self.card('heat', art_heat(t), ease(30.458, 30.85, t), light_c=(0.75, 0.60), light_r=430, light_k=1.15,
                            night=(0.45, 0.42, 0.52))
        img, _ = put_card(img, cam, card_corners((0, 0, 0), (1, 0, 0), (0, 1, 0), 1.5, 1.0), tex)
        c = cam.project(np.array([0.0, -0.1, 0.0]))[0][0]
        return glow(img, c, 0.9, 0.55 + 0.1 * np.sin(t * 5))

    def d3(self, t):
        u = (t - 32.292) / (34.125 - 32.292)
        ang = -0.10 + 0.20 * u                                                           # a slight orbit: two layers, real depth
        cam = Cam((2.0 * np.sin(ang), 0.05, -2.0 * np.cos(ang)), (0, 0, 0))
        img = night_backdrop(8, top=(24, 16, 12), bottom=(36, 24, 18))
        fist = any(h <= t < h + 0.30 for h in (33.20, 33.89))
        breath = 0.006 * np.sin(2 * np.pi * (t - 32.292) / 1.6)                             # the parent's breathing lifts both
        if self.art_ready('newborn_back', 'newborn_baby', 'newborn_hand_open'):
            back = self.art_card([('newborn_back', None)] + ([('newborn_hand_open', None)] if fist else []), (0.66, 0.52), 420)
            img, _ = put_card(img, cam, card_corners((0, breath, 0.12), (1, 0, 0), (0, 1, 0), 1.5, 1.0), back)
            front = self.art_card([('newborn_baby', None)], (0.66, 0.52), 420, alpha_from='newborn_baby')
            img, _ = put_card(img, cam, card_corners((0, breath * 1.1, -0.10), (1, 0, 0), (0, 1, 0), 1.5, 1.0), front)
            beat_k = sum(np.exp(-(t - h) / 0.18) for h in (33.20, 33.89) if t >= h)
            return glow(img, cam.project(np.array([-0.02, -0.24, -0.08]))[0][0], 0.4, 0.2 + 0.8 * beat_k)
        back_items, front_items = art_newborn(t, fist)
        prog = ease(32.292, 32.75, t)
        back = self.card('born', back_items, prog, light_c=(0.66, 0.52), light_r=420, light_k=1.0)
        img, _ = put_card(img, cam, card_corners((0, breath, 0.12), (1, 0, 0), (0, 1, 0), 1.5, 1.0), back)
        front = np.zeros((self.ch, self.cw, 4), np.float32)
        mask = np.zeros((self.ch, self.cw), np.uint8)
        head = front_items[0][1][0][1]                                                   # the head's outline
        cv2.fillPoly(mask, [np.int32(np.asarray(head) * self.ch)], 255, cv2.LINE_AA)
        mask = cv2.dilate(mask, np.ones((7, 7), np.uint8))
        front[..., :3] = self.base['born']
        front[..., 3] = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 1.2)
        front = render_art(front, front_items, self.ch, prog, seed=11)
        front = light_pool(front, (0.66 * self.ch, 0.52 * self.ch), 420, k=1.0)
        img, _ = put_card(img, cam, card_corners((0, breath * 1.1, -0.10), (1, 0, 0), (0, 1, 0), 1.5, 1.0), front)
        beat_k = sum(np.exp(-(t - h) / 0.18) for h in (33.20, 33.89) if t >= h)
        c = cam.project(np.array([-0.02, -0.24, -0.08]))[0][0]                            # the heartbeat, under the baby
        return glow(img, c, 0.4, 0.2 + 0.8 * beat_k)

    def d3b(self, t):
        img = night_backdrop(9, top=(28, 18, 14), bottom=(46, 30, 22))
        src, a = self.B3
        lit = relight(src, a, (300, 1000), 520, 0.9)
        img, _ = place(img, lit, a, 700 - 10 * (t - 34.1), 400, 1250 + 30 * (t - 34.1))
        k = 0.3 + 0.5 * sum(np.exp(-(t - h) / 0.25) for h in (34.12, 35.03) if t >= h)
        return glow(img, (300, 760), 1.4, k)

    def town_cam(self, t):
        return Cam((0.0, 0.62, -1.2), (0.10, 0.36, 1.2))

    def d4(self, t):
        """"The cosmos was silent, the cosmos was still": the same page at night; the town folds back into it (36.85),
        then the village (37.54), going back in time to the bare hill under a still, cold sky. Focus racks to the hill."""
        cam = self.town_cam(t)
        f_t = ease(36.85, 37.20, t)
        f_v = ease(37.54, 37.89, t)
        up = {'town': 1 - f_t, 'village': 1 - f_v, 'hill': 1.0}
        cold = ease(37.6, 38.6, t)
        lights = {'town': 1.0 - ease(36.80, 36.95, t), 'village': 0.6 * (1 - ease(37.50, 37.62, t))}
        d_town = float(np.linalg.norm(np.array([0.1, 0.15, 0.55]) - cam.p))
        d_hill = float(np.linalg.norm(self.crest - cam.p))
        focus = d_town + (d_hill - d_town) * ease(36.85, 38.0, t)
        img = self.town_scene(t, cam, up, 0.12 * (1 - cold), lights, focus=focus, haze={'hill': 0.25 * (1 - cold), 'village': 0.12},
                              stars=cold, cold=cold)
        return img * (1 - 0.18 * cold) + np.array([14, 6, 0], np.float32) * cold

    def d6(self, t):
        """"on the first cold hill": the same angle, the bare hill; one fire on the crest, the only light. The camera
        eases in so that the fire lands where the flame in A's palm is in the next shot (E1, KV5)."""
        u = ease(41.167, 42.75, t)                                                        # E1 cuts in at 42.75, on "hill"
        cam0 = self.town_cam(t)
        if not hasattr(self, 'd6_tg'):
            # aim the end of the move so that the fire sits where the flame in A's palm is in E1 (KV5)
            p1 = cam0.p + np.array([0.0, -0.04, 0.35])
            tg = np.array([0.10, 0.36, 1.2])
            k5 = np.array([566.0, 445.0])                                                # KV5's painted flame (measured in E1)
            for _ in range(12):
                c_ = Cam(p1, tg)
                q, z = c_.project(self.crest + np.array([0, 0.012, 0]))
                err = k5 - q[0]
                tg = tg - c_.rt * err[0] / c_.f * z[0] + c_.up * err[1] / c_.f * z[0]
            self.d6_tg = tg
        p = cam0.p + np.array([0.0, -0.04, 0.35]) * u
        tg = np.array([0.10, 0.36, 1.2]) * (1 - u) + self.d6_tg * u
        cam = Cam(p, tg)
        d_hill = float(np.linalg.norm(self.crest - cam.p))
        img = self.town_scene(t, cam, {'town': 0.0, 'village': 0.0, 'hill': 1.0}, 0.0, None, focus=d_hill, stars=1.0, cold=1.0)
        img = img * 0.82 + np.array([14, 6, 0], np.float32)
        f = cam.project(self.crest + np.array([0, 0.012, 0]))[0][0]
        self.fire_xy = f
        img = glow(img, f, 0.9, 0.18)                                                  # it lights the crest a little
        return flame(img, f, 3.0 + 1.5 * u, t, k=1.0)

    def d5(self, t):
        u = (t - 39.25) / (41.167 - 39.25)
        cam = Cam((0.03 * u, 0.05, -1.75 + 0.15 * u), (0, 0, 0))
        img = night_backdrop(10, top=(20, 12, 8), bottom=(30, 20, 14))
        struck = any(s <= t < s + 0.16 for s in (39.59, 40.05))
        fk = ease(40.5, 41.0, t)
        if self.art_ready('fire_bg', 'fire_hand'):                                       # the hand strikes down 0.20 card units
            tex = self.art_card([('fire_bg', None), ('fire_hand', self.shift(0.0, 0.20 if struck else 0.0))], (0.68, 0.62),
                                200 + 380 * fk, 0.25 + 0.9 * fk, night=(0.36, 0.34, 0.46))
        else:
            tex = self.card('fire', art_fire(t, struck), ease(39.25, 39.5, t), light_c=(0.68, 0.62), light_r=200 + 380 * fk,
                            light_k=0.25 + 0.9 * fk, night=(0.36, 0.34, 0.46))
        img, _ = put_card(img, cam, card_corners((0, 0, 0), (1, 0, 0), (0, 1, 0), 1.5, 1.0), tex)

        def at(x, y):
            return cam.project(np.array([x - 0.75, 0.5 - y, 0.0]))[0][0]
        rng = np.random.default_rng(int(t * 48))
        for s in (39.59, 40.05):
            if s <= t < s + 0.4:
                q = (t - s) / 0.4
                for k in range(16):
                    a = rng.uniform(-2.8, -0.3)
                    r = 20 + 170 * q * rng.uniform(0.4, 1.0)
                    p = at(0.71, 0.70)
                    img = glow(img, (p[0] + r * np.cos(a), p[1] + r * np.sin(a) + 160 * q * q), 0.03, 1.4 * (1 - q))
        if fk > 0:
            img = flame(img, at(0.66, 0.665), 6 + 22 * fk, t, k=fk)
        return img

    def e1(self, t):
        img = self.kv5.copy()
        c = (1361 * OI.S, (1190 - 160) * OI.S)
        return glow(img, c, 0.35, 0.35 + 0.08 * np.sin(t * 2 * np.pi * 7.3))


# constellation outlines (card units): war = candle and flame, helmet, the letter; lullaby = lamp, cradle, rocker,
# the baby's head; goodbye = the window and two hands reaching for each other
CONST = [
    [[(0.305, 0.30), (0.305, 0.36)], [(0.25, 0.635), (0.25, 0.36), (0.36, 0.36), (0.36, 0.635)],
     [(0.925, 0.60), (1.00, 0.52), (1.07, 0.455), (1.16, 0.43), (1.25, 0.455), (1.32, 0.52), (1.395, 0.60)],
     [(0.47, 0.585), (0.88, 0.57), (0.93, 0.655), (0.43, 0.665), (0.47, 0.585)]],
    [[(0.10, 0.44), (0.14, 0.29), (0.26, 0.29), (0.30, 0.44), (0.10, 0.44)], [(0.20, 0.44), (0.20, 0.56)],
     [(0.46, 0.46), (0.54, 0.68), (1.04, 0.68), (1.12, 0.46)], [(0.44, 0.73), (0.60, 0.78), (0.78, 0.80), (0.96, 0.78), (1.14, 0.73)],
     [(0.62, 0.37), (0.68, 0.40), (0.68, 0.46), (0.62, 0.49), (0.56, 0.46), (0.56, 0.40), (0.62, 0.37)]],
    [[(0.0, 0.10), (0.22, 0.10), (0.22, 0.44), (0.0, 0.44), (0.0, 0.10)], [(0.36, 0.12), (0.36, 0.88)],
     [(0.55, 0.575), (0.69, 0.575), (0.80, 0.565), (0.91, 0.57)], [(1.30, 0.59), (1.07, 0.575), (0.96, 0.58), (0.86, 0.585)]],
]


def OI_crop(img, y0):
    h = int(img.shape[1] * 9 / 16)
    return cv2.resize(img[y0:y0 + h], (W, H), interpolation=cv2.INTER_AREA)


SHOTS = [
    ('O', 0, 179, 'opening: the stroke becomes the lived world (tools/opening_ink.py)'),
    ('S1-S3', 180, 325, 'approved light catch (S2 hand fixed)'),
    ('V1a', 326, 358, 'KV5a: the light in her palm flickers on the burst; "We were born"'),
    ('V1b', 359, 380, 'A3: on the hit the light opens into a sheet of paper and comes toward us'),
    ('P1a', 381, 446, 'the letter (same page, same hand, same hook); "in the words that you left"; it tears into fragments'),
    ('A1', 447, 468, 'A1: she looks up into the fragments; some pass in front of her'),
    ('P1b', 469, 490, '"translated": the writing becomes another script; "compressed": the fragments fold into one point'),
    ('M1', 491, 533, '"every war": the point is a candle; a hand-drawn room after a war, a helmet, the letter with the hook'),
    ('M2', 534, 571, '"every lullaby": a cradle rocking by lamplight'),
    ('M3', 572, 599, '"every last goodbye": hands part at a train door; a spark stays'),
    ('C1', 600, 685, 'KV1 again: the sky falls away; the three memories rise as constellations; they look up'),
    ('D1', 686, 730, 'KV4: B looks down; the town pops up from the page (depth); a day passes over it (time)'),
    ('D2', 731, 774, '"heat": hands around a bowl, steam, a frosted window'),
    ('D3', 775, 818, '"hearts": a newborn on a chest, two layers in depth; the fist flexes on the two hits'),
    ('D3b', 819, 861, 'B3: B, eyes closed, as if listening to a heartbeat'),
    ('D4', 862, 941, '"silent, still": the town folds back into the page (36.85), then the village (37.54); only the hill'),
    ('D5', 942, 987, '"the first fire": a hand strikes stone on stone; it catches on the 40.50 hit'),
    ('D6', 988, 1025, '"on the first cold hill": one fire on the crest'),
    ('E1', 1026, 1037, 'KV5: the fire is in A\'s palm (the palm-light composition returns, now warm)'),
]
WIPES = [(22.25, 7), (23.833, 11), (30.458, 2)]           # none at 20.458: that cut is a match on the point of light


def main():
    global PROF
    PROF = glow_profile()
    OI.PROF = PROF
    op = OI.Opening()
    vs = Verse(op)
    if '--stills' in sys.argv:
        out = os.environ.get('DEMO_CHECK', '/tmp')
        ts = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
        for t in ts:
            cv2.imwrite(os.path.join(out, 'd_%06.3f.jpg' % t), np.clip(render(vs, op, t, None), 0, 255).astype(np.uint8),
                        [cv2.IMWRITE_JPEG_QUALITY, 90])
        return
    cap = cv2.VideoCapture(APPROVED)
    approved = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        approved.append(fr)
    assert len(approved) == 146
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H), '-r', str(FPS),
                           '-i', '-', '-t', '%.4f' % (N / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '18',
                           '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', OUT], stdin=subprocess.PIPE)
    strip = []
    marks = [s[1] + (s[2] - s[1]) // 2 for s in SHOTS]
    for f in range(N):
        pic = np.clip(render(vs, op, f / FPS, approved), 0, 255).astype(np.uint8)
        ff.stdin.write(pic.tobytes())
        if f in marks:
            th = cv2.resize(pic, (320, 180), interpolation=cv2.INTER_AREA)
            cv2.putText(th, '%.2f' % (f / FPS), (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            strip.append(th)
    ff.stdin.close()
    ff.wait()
    strip += [np.zeros_like(strip[0])] * (-len(strip) % 5)
    cv2.imwrite(STRIP, np.vstack([np.hstack(strip[i:i + 5]) for i in range(0, len(strip), 5)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    json.dump([dict(id=s[0], frames=[s[1], s[2]], song=[round(s[1] / FPS, 3), round((s[2] + 1) / FPS, 3)], picture=s[3]) for s in SHOTS],
              open(LOG, 'w'), indent=1)
    print('wrote', OUT)


def render(vs, op, t, approved):
    f = int(round(t * FPS))
    if f < 180:
        subs = 5 if OI.T_PULL <= t <= 3.40 else 1
        return op.frame(t, subs=subs) * OI.ease(0.232, 0.55, t)
    if f <= 325:
        if approved is None:
            cap = cv2.VideoCapture(APPROVED)
            cap.set(cv2.CAP_PROP_POS_FRAMES, f - 180)
            return cap.read()[1].astype(np.float32)
        return approved[f - 180].astype(np.float32)
    sid = next(s[0] for s in SHOTS if s[1] <= f <= s[2])
    fn = {'V1a': vs.v1a, 'V1b': vs.v1b, 'P1a': vs.p1a, 'A1': vs.a1, 'P1b': vs.p1b,
          'M1': lambda t: vs.memory(t, 'war', 20.458, 22.25, (0.10, 0.05, -1.95), (0.02, 0.02, -1.70)),
          'M2': lambda t: vs.memory(t, 'lull', 22.25, 23.833, (-0.08, 0.04, -1.90), (0.0, 0.02, -1.72)),
          'M3': lambda t: vs.memory(t, 'fare', 23.833, 25.0, (0.06, -0.02, -1.88), (0.04, 0.0, -1.75)),
          'C1': vs.constellations, 'D1': vs.d1, 'D2': vs.d2, 'D3': vs.d3, 'D3b': vs.d3b, 'D4': vs.d4,
          'D5': vs.d5, 'D6': vs.d6, 'E1': vs.e1}[sid]
    img = fn(t)
    for tc, seed in WIPES:
        img = vs.wipe(img, t, tc, seed)
    return img


if __name__ == '__main__':
    main()
