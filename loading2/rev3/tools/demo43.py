"""Opening + Verse 1 demo v3 (0.000-43.250 s, 1038 frames, 1280x720, 24 fps) over the unchanged locked master.

  python3 rev3/tools/demo43.py --shots all --jobs 4   ->  every frame into the cache ($DEMO_CACHE)
  python3 rev3/tools/demo43.py --shots M2,M3          ->  re-render only those shots
  python3 rev3/tools/demo43.py --assemble             ->  rev3/tests/DEMO_0-43_v4_720p.mp4 (+ _strip.jpg, _shots.json)
  python3 rev3/tools/demo43.py --stills 17,21         ->  single frames into $DEMO_CHECK (default /tmp)

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
ART = os.environ.get('DEMO_ART') or os.path.join(R, 'art', 'memory_cards')
CAND = os.path.join(R, 'art', 'candidates_m23')                                  # Message 23 candidates (rear A, rear B, side palm)
PLATES5 = os.path.join(R, 'art', 'plates_v5')                                     # war_memory_v1, first_fire_hill_wide_v1 (opaque, 1672x941)                  # supplied memory-card artwork (see briefs/MEMORY_CARDS_BRIEF.md)
AUDIO = OI.AUDIO
OUT = os.path.join(R, 'tests', 'DEMO_0-43_v7_720p.mp4')                      # v6, v5, v4, v3 stay in tests/ for comparison
STRIP = os.path.join(R, 'tests', 'DEMO_0-43_v7_strip.jpg')
LOG = os.path.join(R, 'tests', 'DEMO_0-43_v7_shots.json')
STAGE = os.environ.get('DEMO_STAGE', 'v9')                                       # v9 fixes; DEMO_STAGE=v8 reproduces v8
CACHE = os.environ.get('DEMO_CACHE') or '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad/v7/cache'
S3_V5 = os.path.join(R, 'work', 'p1', 'S3_v5_frames.npy')   # the approved S3 with the v5 settle (tools/p1_local.build_s3)
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


def candle_flame(img, tip, wid, t, k=1.0, seed=0):
    """a candle's flame standing on its wick tip (screen px): a tall teardrop, a dim blue root, a pale core, a warm
    halo; it flickers and leans a little. wid: the flame's width in px."""
    if k <= 0:
        return img
    fl = 1.0 + 0.07 * np.sin(t * 2 * np.pi * 6.3 + seed) + 0.04 * np.sin(t * 2 * np.pi * 11.9 + 2 * seed)
    hgt = wid * 2.7 * fl * k ** 0.7
    wd = wid * (0.55 + 0.45 * k)
    lean = 0.10 * wd * np.sin(t * 2 * np.pi * 1.7 + seed)
    base = np.array([tip[0], tip[1] + 0.12 * hgt])                                   # the wick stands inside the flame's root
    a = np.linspace(0, 1, 48)
    half = wd / 2 * np.sin(np.pi * a ** 0.75) * (1 - 0.35 * a)                     # round root, long taper
    yy = base[1] - hgt * a
    xs = base[0] + lean * a ** 2
    pts = np.concatenate([np.stack([xs - half, yy], 1), np.stack([xs + half, yy], 1)[::-1]])
    out = np.zeros((H, W), np.float32)
    cv2.fillPoly(out, [np.int32(pts * 4)], 1.0, cv2.LINE_AA, shift=2)
    out = cv2.GaussianBlur(out, (0, 0), max(0.7, wd * 0.10))
    core = np.zeros((H, W), np.float32)
    cpts = np.concatenate([np.stack([xs - half * 0.45, yy], 1), np.stack([xs + half * 0.45, yy], 1)[::-1]])[:, :]
    cv2.fillPoly(core, [np.int32(cpts[(np.arange(len(cpts)) % 48) < 34] * 4)], 1.0, cv2.LINE_AA, shift=2)
    core = cv2.GaussianBlur(core, (0, 0), max(0.6, wd * 0.08))
    root = np.zeros((H, W), np.float32)
    cv2.ellipse(root, (int(base[0] * 4), int((base[1] - 0.06 * hgt) * 4)), (int(wd * 0.30 * 4), int(hgt * 0.07 * 4)), 0, 0, 360, 1.0, -1,
                cv2.LINE_AA, shift=2)
    root = cv2.GaussianBlur(root, (0, 0), max(0.6, wd * 0.08))
    img += out[..., None] * np.array([60, 165, 255], np.float32) * k
    img += core[..., None] * np.array([150, 225, 255], np.float32) * k
    img += root[..., None] * np.array([90, 30, 10], np.float32) * k                  # the blue root
    return glow(img, (base[0], base[1] - 0.45 * hgt), 0.05 + wid * 0.006, 0.75 * fl * k)


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


def put_bent(img, cam, c, u, v, w, h, tex, bend, focus=None, aperture=0.0, extra_blur=0.0):
    """a sheet of paper flexed along its middle (hinge along v): the two halves turn by +-bend/2 toward the same side."""
    c, u, v = (np.asarray(a_, np.float64) for a_ in (c, u, v))
    if abs(bend) < 0.02:
        return put_card(img, cam, card_corners(c, u, v, w, h), tex, focus=focus, aperture=aperture, extra_blur=extra_blur)[0]
    uL = rot_axis(u, v, bend / 2)
    uR = rot_axis(u, v, -bend / 2)
    half = tex.shape[1] // 2
    parts = [(c - uL * w / 4, uL, tex[:, :half]), (c + uR * w / 4, uR, tex[:, half:])]
    parts.sort(key=lambda q: -float((q[0] - cam.p) @ cam.fw))
    for cc, uu, tt in parts:
        img, _ = put_card(img, cam, card_corners(cc, uu, v, w / 2, h), np.ascontiguousarray(tt), focus=focus,
                          aperture=aperture, extra_blur=extra_blur)
    return img


def put_folded(img, cam, c, u, v, w, h, front, back, a_top, a_right, focus=None, aperture=0.0):
    """v9: a letter folded in quarters (right half over the left, then the top over the bottom, toward the viewer, writing
    inside), drawn as four quarter panels. a_top / a_right: fold angles of the top half and the right half (pi = closed,
    0 = open). Each panel shows the letter's face or its back depending on which side faces the camera."""
    c, u, v = (np.asarray(a_, np.float64) for a_ in (c, u, v))
    u, v = u / np.linalg.norm(u), v / np.linalg.norm(v)
    n = np.cross(u, v)
    if (cam.p - c) @ n < 0:
        n = -n
    a_top, a_right = min(a_top, np.pi - 0.05), min(a_right, np.pi - 0.07)              # paper has thickness
    v1 = v * np.cos(a_top) + n * np.sin(a_top)
    n1 = n * np.cos(a_top) - v * np.sin(a_top)
    u2 = u * np.cos(a_right) + n * np.sin(a_right)
    u2t = u * np.cos(a_right) + n1 * np.sin(a_right)
    hh, ww = front.shape[:2]
    panels = []
    for qx, qy in ((0, 0), (0, 1), (1, 0), (1, 1)):                                    # (right?, top?)
        ex = u2t if (qx and qy) else (u2 if qx else u)
        ey = v1 if qy else v
        xs = (0.0, w / 2) if qx else (-w / 2, 0.0)
        ys = (h / 2, 0.0) if qy else (0.0, -h / 2)
        corners = np.array([c + ex * xs[0] + ey * ys[0], c + ex * xs[1] + ey * ys[0], c + ex * xs[1] + ey * ys[1],
                            c + ex * xs[0] + ey * ys[1]])
        ty0, ty1 = (0, hh // 2) if qy else (hh // 2, hh)
        tx0, tx1 = (ww // 2, ww) if qx else (0, ww // 2)
        xy, z = cam.project(corners)
        area = (xy[1, 0] - xy[0, 0]) * (xy[3, 1] - xy[0, 1]) - (xy[1, 1] - xy[0, 1]) * (xy[3, 0] - xy[0, 0])
        tex = front if area > 0 else back                                                # flipped panel: its back faces us
        panels.append((float(z.mean()), corners, np.ascontiguousarray(tex[ty0:ty1, tx0:tx1])))
    panels.sort(key=lambda q: -q[0])
    for _, corners, tex in panels:
        img, _ = put_card(img, cam, corners, tex, focus=focus, aperture=aperture)
    return img


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


def close_mouth_a1(img, theta=-5.5):
    """A1 is drawn singing ('ah'). Every character shot in this demo is voice-over, so she watches with her mouth
    closed, as in panel 1 of A's own mouth sheet (A_mouth.png): the jaw rotates up about its hinge (by the opening's
    height at the lips), fading out into the neck so the collar stays put; whatever is left of the inside of the mouth
    becomes skin, and, as in the reference, the lips are told only by the profile and a tiny notch at the corner, with no
    line drawn across the cheek."""
    img = img.copy()
    hh, ww = img.shape[:2]
    # A1's own outline colour, from the untouched chin and jaw (the darkest pixel of each row at the profile)
    line_c = np.median(np.array([img[y, 800 + int(np.argmin(img[y, 800:870].sum(1)))] for y in range(655, 700)]), 0)
    Hx, Hy = 520.0, 690.0                                                           # the jaw hinge, in front of the ear (head tilted back)
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    # weight: 1 on the lower jaw (below the line from the hinge through the mouth), fading below the jaw into the neck
    mx, my = 800.0, 603.0
    nx, ny = -(my - Hy), (mx - Hx)
    nn = np.hypot(nx, ny)
    sd = ((xx - Hx) * nx + (yy - Hy) * ny) / nn                                      # >0 below the mouth line
    wgt = smooth(sd / 18.0) * (1 - smooth((yy - 712.0) / 70.0)) * smooth((xx - 560.0) / 60.0)
    c, s_ = np.cos(np.radians(-theta)), np.sin(np.radians(-theta))                   # inverse rotation for sampling
    dx, dy = xx - Hx, yy - Hy
    sx = Hx + c * dx - s_ * dy
    sy = Hy + s_ * dx + c * dy
    mapx = (xx + (sx - xx + 5.0) * wgt).astype(np.float32)                          # and 5 px back, so the lips line up as in the sheet
    mapy = (yy + (sy - yy) * wgt).astype(np.float32)
    img = cv2.remap(img, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # what is left of the opening (the red, and the pale lip rim around it) becomes the skin beside it; the white
    # beyond the profile stays white
    def edge_x(im, y):                                                               # the face's profile (last non-white pixel)
        nw = np.where(im[y, 760:880].min(1) < 225)[0]
        return 760 + int(nw.max()) if len(nw) else 820
    m = np.zeros((hh, ww), np.float32)
    cv2.ellipse(m, (805, 595), (22, 26), 10, 0, 360, 1.0, -1, cv2.LINE_AA)
    for y in range(570, 620):                                                        # never past the profile
        m[y, edge_x(img, y) - 1:] = 0
    m = cv2.GaussianBlur(m, (0, 0), 1.3)
    fill = img.copy()
    for y in range(565, 625):
        fill[y, 766:850] = np.median(img[y - 1:y + 2, 764:771].reshape(-1, 3), 0)
    img = img * (1 - m[..., None]) + fill * m[..., None]
    # the profile from the nose to the chin, by the usual rules for a closed anime mouth in profile (and A's own closed
    # panel): almost straight along the nose-tip-to-chin line, the upper lip a touch further forward than the lower, a
    # small notch where they meet; the outline breaks at the notch and a short reddish-brown mouth line runs in from it
    def dark_x(y):
        dk = np.where(img[y, 780:880].min(1) < 190)[0]
        return 780 + float(dk.max()) if len(dk) else np.nan
    ys_ = np.arange(556, 668)
    ex = np.array([dark_x(y) for y in ys_])
    ok = ~np.isnan(ex)
    ex = np.interp(ys_, ys_[ok], ex[ok])
    ex = np.convolve(np.pad(ex, 3, mode='edge'), np.ones(7) / 7, 'valid')            # the existing profile, smoothed
    yt, yc = 566 + int(np.argmax(ex[(ys_ >= 556) & (ys_ < 580)])), 0
    nose = (float(ex[yt - 556]), float(yt))
    lo = (ys_ > 640) & (ys_ < 667)
    yc = int(ys_[lo][np.argmax(ex[lo])])
    chin = (float(ex[yc - 556]), float(yc))
    def bump(y, c, sg):
        return np.exp(-((y - c) / sg) ** 2)
    L = chin[1] - nose[1]
    y_u, y_n, y_l, y_g = nose[1] + 0.21 * L, nose[1] + 0.34 * L, nose[1] + 0.45 * L, nose[1] + 0.66 * L
    yy_ = ys_.astype(np.float32)
    xe = nose[0] + (yy_ - nose[1]) * (chin[0] - nose[0]) / L                          # the nose-to-chin line
    xt = xe - 3.2 + 1.4 * bump(yy_, y_u, 6) - 1.6 * bump(yy_, y_n, 2.5) + 0.6 * bump(yy_, y_l, 6) - 1.4 * bump(yy_, y_g, 8)
    w_ = smooth((yy_ - (nose[1] + 4)) / 8) * (1 - smooth((yy_ - (chin[1] - 18)) / 10))
    xt = ex * (1 - w_) + xt * w_
    white = np.median(img[575:625, 862:876].reshape(-1, 3), 0)
    for y, x_old, x_new, ww_ in zip(ys_, ex, xt, w_):
        if ww_ < 0.01:
            continue
        x0, x1 = int(min(x_old, x_new)) - 13, int(max(x_old, x_new)) + 8                # also covers the old line's pale inner rim
        skin = np.median(img[y, int(min(x_old, x_new)) - 24:int(min(x_old, x_new)) - 17].reshape(-1, 3), 0)
        xs = np.arange(x0, x1)
        cov = np.clip(x_new - xs + 0.5, 0, 1)[:, None]
        img[y, xs] = skin * cov + white * (1 - cov)
    ink = np.zeros((hh, ww), np.float32)
    seg = [(x - 0.7, y) for x, y, ww_ in zip(xt, ys_, w_) if ww_ > 0.0 and abs(y - y_n) > 1.6]
    for part in (seg[:sum(1 for q in seg if q[1] < y_n)], seg[sum(1 for q in seg if q[1] < y_n):]):  # broken at the notch
        if len(part) > 1:
            cv2.polylines(ink, [np.int32(np.array(part) * 4)], False, 1.0, 2, cv2.LINE_AA, shift=2)
    ink = cv2.GaussianBlur(ink, (0, 0), 0.55)
    img = img * (1 - 0.85 * ink[..., None]) + line_c * 0.85 * ink[..., None]
    mouth = np.zeros((hh, ww), np.float32)                                            # the closed mouth: one short line, tapered
    xn = float(np.interp(y_n, ys_, xt))
    pts = np.array([(xn - 0.5, y_n), (xn - 4.0, y_n + 0.5), (xn - 7.5, y_n + 1.3), (xn - 10.5, y_n + 2.4)])
    for i_ in range(3):
        cv2.line(mouth, tuple(np.int32(pts[i_] * 4)), tuple(np.int32(pts[i_ + 1] * 4)), 1.0 - 0.3 * i_, 2 if i_ < 2 else 1,
                 cv2.LINE_AA, shift=2)
    mouth = cv2.GaussianBlur(mouth, (0, 0), 0.5)
    img = img * (1 - 0.8 * mouth[..., None]) + np.array([70, 74, 150], np.float32) * 0.8 * mouth[..., None]
    return img


def pose_matte(img, dark_hair=False, protect=None):
    """alpha and edge colour for a key pose drawn on white. The background is the white joined to the corners, plus
    any enclosed white that hair surrounds (the gaps between strands, the inside of a looped strand); enclosed white
    bounded by line art (a collar, a ribbon stripe) stays. Edge pixels get alpha from how far they are from paper white
    toward the drawing's local colour, and that colour with the white taken out: no erosion, no fringe, no fade."""
    mn = img.min(2)
    b_, g_, r_ = img[..., 0], img[..., 1], img[..., 2]
    hgt, wid = mn.shape
    near = (mn > 238).astype(np.uint8)
    ff = near.copy()
    mask = np.zeros((hgt + 2, wid + 2), np.uint8)
    for seed in ((0, 0), (wid - 1, 0), (0, hgt - 1), (wid - 1, hgt - 1)):
        if ff[seed[1], seed[0]] == 1:
            cv2.floodFill(ff, mask, seed, 2)
    bg = ff == 2
    n, lab, st, _ = cv2.connectedComponentsWithStats(((ff == 1)).astype(np.uint8), connectivity=8)
    d_out = cv2.distanceTransform((~bg).astype(np.uint8), cv2.DIST_L2, 5)               # distance to the outside
    if dark_hair:                                                                        # A: black hair with teal ends
        hairish = (mn < 150) | ((g_ - r_ > 20) & (b_ - r_ > 10))
    else:                                                                                # B: copper hair
        hairish = r_ - b_ > 45
    for i in range(1, n):
        if st[i, 4] < 6 or st[i, 4] > 0.012 * hgt * wid:                                 # a shirt or collar is large
            continue
        x, y, w, h = st[i, :4]
        x0, y0, x1, y1 = max(0, x - 8), max(0, y - 8), min(wid, x + w + 8), min(hgt, y + h + 8)
        comp = (lab[y0:y1, x0:x1] == i).astype(np.uint8)
        ring = (cv2.dilate(comp, np.ones((11, 11), np.uint8)) > 0) & (comp == 0)
        mid = (mn[y0:y1, x0:x1] < 225) if dark_hair else ((mn[y0:y1, x0:x1] >= 90) & (mn[y0:y1, x0:x1] < 225))
        rr = ring & mid                                                                  # not paper (and, for B, not line art)
        gap = rr.sum() > 4 and hairish[y0:y1, x0:x1][rr].mean() > (0.7 if dark_hair else 0.5)
        if dark_hair and not gap:                                                        # a gap by the horn or the head's outline
            near_out = d_out[y0:y1, x0:x1][comp > 0].min() <= 12
            gap = near_out and (mn[y0:y1, x0:x1][ring] < 150).mean() >= 0.3
        if gap and protect is not None:
            outer = (cv2.dilate(comp, np.ones((11, 11), np.uint8)) > 0) & ~(cv2.dilate(comp, np.ones((5, 5), np.uint8)) > 0)
            sub = img[y0:y1, x0:x1]
            pale_ring = ((sub.min(2) >= 200) & (np.abs(sub[..., 2] - sub[..., 0]) < 25))[outer].mean() if outer.sum() else 0.0
            if protect[y0:y1, x0:x1][comp > 0].mean() > 0.3 or pale_ring > 0.2:
                gap = False                                                              # a highlight on her face, the collar, not a gap
        if gap:
            bg[y0:y1, x0:x1] |= comp > 0
    # pale paper pockets between strands joined to the background through a narrow neck (pale grey 195-240,
    # colourless): the background reaches up to 6 px into such pixels
    pale = (mn > 195) & (np.abs(r_ - b_) < 18) & (np.abs(g_ - b_) < 18)
    if protect is not None:                                                              # face and body interiors are never paper
        pale &= ~protect
    for _ in range(6):
        bg = bg | ((cv2.dilate(bg.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & pale)
    fg = ~bg
    core = cv2.erode(fg.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    cf = core.astype(np.float32)
    wsum = cv2.GaussianBlur(cf, (0, 0), 3.0)
    loc = cv2.GaussianBlur(img * cf[..., None], (0, 0), 3.0) / np.maximum(wsum, 1e-3)[..., None]
    lmin = loc.min(2)
    a_est = np.clip((255.0 - mn) / np.maximum(255.0 - lmin, 30.0), 0, 1)
    band = cv2.dilate(fg.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    a = np.where(core, 1.0, np.where(band, a_est, 0.0)).astype(np.float32)
    a = np.where(bg & ~band, 0.0, a)
    a_s = np.maximum(a, 1e-3)[..., None]
    dec = np.clip((img - (1 - a[..., None]) * 255.0) / a_s, 0, 255)
    col = np.where(core[..., None], img, np.where(a[..., None] > 0.02, dec, loc))
    return a, col.astype(np.float32)


def body_zone(img):
    """B3's face and body interior, from the drawing: the convex hull of her face skin, extended 90 px up under the
    bangs (the forehead highlight between them), and of her cardigan, extended 40 px up over the collar. White pockets
    in it are skin highlights, eye corners or the shirt, never background. (The face is the largest bright skin-toned
    region in the upper half; the cardigan the largest in the lower half.)"""
    b, g, r = img[..., 0], img[..., 1], img[..., 2]
    mn = img.min(2)
    skin = ((r > 225) & (r - b > 15) & (r - b < 75) & (mn > 150) & (g > 175)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(skin, connectivity=8)
    hh = img.shape[0]
    zone = np.zeros(img.shape[:2], np.uint8)
    for upper, lift in ((True, 90), (False, 40)):
        cand = [i for i in range(1, n) if (cen[i][1] < hh * 0.55) == upper]
        i = max(cand, key=lambda k: st[k, 4])
        hull = cv2.convexHull(np.argwhere(lab == i)[:, ::-1].astype(np.int32))
        for dy in range(0, lift + 1, 10):
            cv2.fillConvexPoly(zone, hull - np.array([0, dy], np.int32), 1)
    return zone > 0


def load_pose(name):
    """key pose on white: its own matte from the drawing (pose_matte), the figure's main silhouette only (drops stray
    marks). Cut sides are framed out by the shots, not faded."""
    img = cv2.imread(os.path.join(POSES, name + '.png')).astype(np.float32)
    if name == 'A1':
        img = close_mouth_a1(img)
    a, col = pose_matte(img, dark_hair=name.startswith('A'), protect=body_zone(img) if name == 'B3' else None)
    n, lab, st, _ = cv2.connectedComponentsWithStats((a > 0.5).astype(np.uint8))
    big = 1 + int(np.argmax(st[1:, 4]))
    keep = cv2.dilate((lab == big).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    return col, a * keep


def load_candidate(name):
    """a Message 23 candidate PNG: BGR 0..255 and its own alpha. Inside the figure the source alpha is 251-254, not
    255, and a few hundred pixels inside the hair or coat are partly transparent: alpha is rescaled so 251 is opaque,
    and anything more than 2.5 px from the transparent background is made opaque. Real gaps (alpha 0) and the
    anti-aliased edge (within 2.5 px of them) keep their own values."""
    im = cv2.imread(os.path.join(CAND, name + '.png'), cv2.IMREAD_UNCHANGED).astype(np.float32)
    a = np.clip(im[..., 3] / 251.0, 0, 1)
    d = cv2.distanceTransform((a >= 0.05).astype(np.uint8), cv2.DIST_L2, 3)
    return im[..., :3].copy(), np.where(d > 2.5, 1.0, a).astype(np.float32)


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
    wid, hgt = {'town': (1500, 560), 'village': (1600, 420), 'hill': (3340, 440)}[kind]
    can = np.zeros((hgt, wid, 4), np.float32)
    can[..., :3] = paper(wid, hgt, seed + 40, tone=(0.74, 0.84, 0.90))
    rng = np.random.default_rng(seed)
    sil = np.zeros((hgt * 4, wid * 4), np.uint8)
    lines, windows, crest = [], [], None

    def P(pts):                                                                       # 4x canvas, 2 bits of sub-pixel
        return np.int32(np.asarray(pts, np.float64) * 16)
    if kind == 'hill':
        xs = np.linspace(0, wid, 170)
        ys = hgt - (0.12 * hgt + 0.66 * hgt * np.exp(-((xs - 0.5997 * wid) / (0.1186 * wid)) ** 2) + 0.10 * hgt * np.exp(-((xs - 0.328 * wid) / (0.108 * wid)) ** 2))
        ys += cv2.GaussianBlur(rng.normal(0, 1, (1, 170)).astype(np.float32), (0, 0), 2)[0] * 3
        ridge = np.stack([xs, ys], 1)
        cv2.fillPoly(sil, [P(np.vstack([ridge, [[wid, hgt], [0, hgt]]]))], 255, cv2.LINE_AA, shift=2)
        lines.append(ridge)
        i = int(np.argmin(ys))
        crest = (float(xs[i]), float(ys[i]))
        for x in rng.uniform(0, wid, 100):                                             # grass on the ridge
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
        # fragments: torn shards (Voronoi cells with jagged edges that two neighbours share exactly, so the page is
        # whole until it tears). The tear runs across the page from its left edge; the shard with the spiral goes last.
        rng = np.random.default_rng(5)
        hero = np.array([1165.0, 398.0])                                                # one large shard holds the whole spiral and the full stop
        seeds = [hero]
        for _ in range(4000):
            q = rng.uniform((0, 0), (pw, ph))
            dmin = 110 + 0.20 * q[0] / pw * 180                                         # smaller pieces where the tear starts (left)
            if all(np.linalg.norm(q - s_) > (dmin if np.linalg.norm(s_ - hero) > 1 else 245) for s_ in seeds):
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
        dmax = np.hypot(pw, ph) * 0.9
        origin = np.array([0.0, 0.28 * ph])                                             # the tear starts at the left edge
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
            is_hero = bool(cv2.pointPolygonTest(np.float32(jp), (float(hero[0]), float(hero[1])), False) >= 0)
            torn = 17.50 + 0.42 * np.clip(np.hypot(*(ctr - origin)) / dmax, 0, 1) + rng.uniform(0, 0.05)
            self.frags.append(dict(box=(bx0, by0, bx1, by1), alpha=a, fibre=fibre, ctr=ctr, poly=jp,
                                   text=float((ink[by0:by1, bx0:bx1] * a).sum() / (a.sum() + 1)), hero=is_hero,
                                   delay=(17.98 if is_hero else torn) - 17.71,
                                   out=np.r_[(ctr - origin) / dmax, 0.0],
                                   rise=0.22 if is_hero else rng.choice([rng.uniform(0.15, 0.35), rng.uniform(0.5, 0.95)]),
                                   axis=rng.normal(0, 1, 3), spin=rng.uniform(0.3, 1.1) * (0.3 if is_hero else 1.0),
                                   bend=rng.uniform(0.12, 0.42), phase=rng.uniform(0, 6.28),
                                   seed=int(rng.integers(0, 1 << 30))))
        yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
        self.crack = cv2.GaussianBlur(crack, (0, 0), 0.5)
        self.crack_t = 17.42 + 0.42 * np.clip(np.hypot(xx - origin[0], yy - origin[1]) / dmax, 0, 1)
        hp = [f for f in self.frags if f['hero']][0]['poly']                             # the spiral must not be torn
        for q in ((1095, 350), (1200, 350), (1095, 445), (1200, 445), tuple(self.dot_px)):
            assert cv2.pointPolygonTest(np.float32(hp), (float(q[0]), float(q[1])), False) >= 0, 'spiral cut by a tear'

    def prep_kv(self):
        k5 = cv2.imread(os.path.join(PLATES, 'KV5a.png'))
        m = np.zeros(k5.shape[:2], np.uint8)
        cv2.ellipse(m, (1361, 1190), (62, 92), 0, 0, 360, 255, -1)
        self.kv5a = OI_crop(cv2.inpaint(k5, m, 9, cv2.INPAINT_TELEA).astype(np.float32), 160)
        self.kv5 = OI_crop(cv2.imread(os.path.join(PLATES, 'KV5.png')).astype(np.float32), 160)
        k4 = cv2.imread(os.path.join(PLATES, 'KV4.png')).astype(np.float32)
        m4 = cv2.imread(os.path.join(PLATES, 'KV4_matte.png'), 0).astype(np.float32) / 255
        self.kv4 = OI_crop(k4, 160)
        a4, col = kv4_matte(k4, m4)
        al = cv2.GaussianBlur(a4, (0, 0), 1.0)
        self.kv4a = np.clip(OI_crop(np.dstack([al] * 3), 160)[..., 0], 0, 1)
        # premultiplied at full size, colour and alpha blurred alike: a pixel the matte drops brings none of its colour
        self.kv4_pre = OI_crop(cv2.GaussianBlur(col * a4[..., None], (0, 0), 1.0), 160)

    def prep_poses(self):
        self.A1 = load_pose('A1')
        self.A3 = load_pose('A3')
        self.A3c = load_candidate('Girl_A_side_palm_candidate_v1')
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
    TOWN = dict(town=(0.80, 1.75), village=(1.25, 2.5), hill=(1.75, 5.175))     # hill: the plate's 1672 px = 3.5 units, +400 px each side

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
        """the pop-up page: three cut-outs on fold lines (town, village, hill), an oblique street of small house cards
        running in from the front left, and a near row of roofs in front of everything. Each card knows its fold line
        (base, u along it), the side it lies on when flat, and its windows."""
        self.layers = {}
        for k, seed in (('town', 3), ('village', 2), ('hill', 1)):
            tex, wins, crest = town_layer(k, seed) if k != 'hill' else self.hill_print()
            zl, wl = self.TOWN[k]
            hl = wl * tex.shape[0] / tex.shape[1]
            self.layers[k] = dict(tex=tex, wins=wins, crest=crest, z=zl, w=wl, h=hl)
        T = self.layers['town']
        th, tw = T['tex'].shape[:2]
        self.cards = []

        def piece(x0, x1, group, base, u, scale, order):
            sub = T['tex'][:, x0:x1].copy()
            wins = [(wx - x0, wy) for wx, wy in T['wins'] if x0 + 10 < wx < x1 - 10]
            w_ = (x1 - x0) / tw * T['w'] * scale
            self.cards.append(dict(tex=sub, wins=wins, group=group, base=np.array(base, float), u=np.array(u, float),
                                   w=w_, h=T['h'] * scale, order=order))
        # the town itself: three staggered segments on their own folds, the left one turned to face down the street
        def yaw(deg):
            r = np.radians(deg)
            return [np.cos(r), 0.0, np.sin(r)]
        for x0, x1, base, ang in ((0, 520, [-0.58, 0.0, 0.70], 28.0), (500, 1010, [0.02, 0.0, 0.84], 0.0), (990, 1500, [0.60, 0.0, 0.74], -14.0)):
            piece(x0, x1, 'town', base, yaw(ang), 1.0, 0)
        # the street: a cobbled road printed on the page from the front left into the town, a wall of house cards on
        # each side, set along the road
        p0, p1 = np.array([-1.02, 0.0, -0.22]), np.array([-0.40, 0.0, 0.62])
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        n = np.array([-d[2], 0.0, d[0]])
        self.road = (p0 - d * 0.25, p1 + d * 0.05, n)
        for i, (sd, side, x0) in enumerate(((0.08, 1, 0), (0.33, 1, 300), (0.58, 1, 560), (0.83, 1, 1200),
                                            (0.20, -1, 820), (0.45, -1, 1080), (0.70, -1, 160), (0.95, -1, 640))):
            c = p0 + (p1 - p0) * sd + n * 0.115 * side
            piece(x0, x0 + 250, 'street', c, d, 0.62, i % 4)
        # the near roofs: big, close to the lens, out of focus
        piece(1120, 1500, 'near', [-0.80, 0.0, -0.10], [1.0, 0.0, 0.0], 0.95, 0)
        piece(40, 420, 'near', [-1.15, 0.0, 0.18], [1.0, 0.0, 0.0], 0.95, 1)
        g = paper(2640, 1148, 9, tone=(0.74, 0.84, 0.90))                                 # the page: 6.6 x 2.87, z -0.47..2.4 (wider than the hill)
        for k in self.TOWN:                                                              # pop-up creases along the folds
            if STAGE == 'v9' and k == 'hill':                                            # v9: the hill and the page are one print
                continue
            y = int((2.4 - self.TOWN[k][0]) / 2.87 * 1148)
            cv2.line(g, (0, y), (2639, y), (0.55, 0.62, 0.68), 2, cv2.LINE_AA)
            cv2.line(g, (0, y + 2), (2639, y + 2), (0.86, 0.94, 0.98), 1, cv2.LINE_AA)

        def gp(q):                                                                       # page point -> ground texture px
            return np.array([(q[0] + 3.3) / 6.6 * 2640, (2.4 - q[2]) / 2.87 * 1148])
        if STAGE == 'v9':
            g = g * self.ground_print()[..., None]                                       # the hill's own ground, continued
            self.ground_noroad = np.dstack([g.copy(), np.ones((1148, 2640), np.float32)])
        a_, b_, nn = self.road
        hw = 0.075
        poly = np.array([gp(a_ + nn * hw), gp(b_ + nn * hw * 0.8), gp(b_ - nn * hw * 0.8), gp(a_ - nn * hw)])
        rd = np.zeros(g.shape[:2], np.float32)
        cv2.fillPoly(rd, [np.int32(poly * 4)], 1.0, cv2.LINE_AA, shift=2)
        g = g * (1 - 0.10 * rd[..., None])                                               # a light wash for the road
        rng = np.random.default_rng(31)
        for k in range(1, 46):                                                           # cobbles: short strokes across it
            f = k / 46.0
            c = a_ + (b_ - a_) * f
            w_ = hw * (1 - 0.2 * f)
            for j in range(-2, 3):
                q0 = gp(c + nn * (j * 0.4 - 0.15) * w_ + (b_ - a_) * rng.uniform(-0.004, 0.004))
                q1 = gp(c + nn * (j * 0.4 + 0.15) * w_)
                cv2.line(g, tuple(np.int32(q0 * 4)), tuple(np.int32(q1 * 4)), tuple(float(v) for v in INK * 0.9 + 0.35), 1, cv2.LINE_AA, shift=2)
        for sgn in (1, -1):                                                              # its two kerbs, inked
            cv2.line(g, tuple(np.int32(gp(a_ + nn * hw * sgn) * 4)), tuple(np.int32(gp(b_ + nn * hw * 0.8 * sgn) * 4)),
                     tuple(float(v) for v in INK), 2, cv2.LINE_AA, shift=2)
        self.ground = np.dstack([g, np.ones((1148, 2640), np.float32)])
        self.crest = self.hill_world(self.HILL_TINDER)                                  # the fire's place on the hill card

    def ground_map(self):
        """v9: page texture px -> hill-plate px (two tilings and their blend). The page in front of the hill card is
        printed with the plate's own near ground (rows 760-941, far to near in the same orientation as on the card, never
        mirrored, so nothing reads as a reflection). Each further band shifts sideways; neighbouring bands cross-fade."""
        if not hasattr(self, '_gmap'):
            gy, gx = np.mgrid[0:1148, 0:2640].astype(np.float32)
            x = gx / 400.0 - 3.3
            z = 2.4 - gy / 400.0
            card_px = 2472.0 / self.TOWN['hill'][1]                                      # card texture px per unit
            d = np.clip(self.TOWN['hill'][0] - z, 0, None) * card_px * 0.55              # distance in front of the card, in rows
            band = 181.0
            maps = []
            for off in (0.0, band / 2):
                dd = d + off
                tile = np.floor(dd / band)
                row = 760.0 + np.mod(dd, band)
                cx = x * card_px + 1236.0 + tile * 397.0 + off * 2.3
                cx = np.mod(cx, 2 * 2471.0)
                cx = np.where(cx > 2471, 2 * 2471 - cx, cx)
                col = np.clip(cx - self.HILL_PAD, 0, 1671)
                maps.append((col.astype(np.float32), row.astype(np.float32)))
            w0 = np.abs(np.mod(d, 181.0) / 181.0 - 0.5) * 2                               # 1 mid-band, 0 at its seams
            wA = np.clip((1 - w0) * 1.6 - 0.3, 0, 1)
            self._gmap = (maps, wA.astype(np.float32), z)
        return self._gmap

    def _ground_sample(self, img):
        maps, wA, z = self.ground_map()
        a = cv2.remap(img, maps[0][0], maps[0][1], cv2.INTER_LINEAR)
        b = cv2.remap(img, maps[1][0], maps[1][1], cv2.INTER_LINEAR)
        w = wA if img.ndim == 2 else wA[..., None]
        return a * (1 - w) + b * w, z

    def ground_print(self):
        """the page's terrain print: the plate's ground luminance in the hill print's paper tones (factor on the paper)."""
        pl = self.plate5('first_fire_hill_wide_v1')
        l0 = np.ascontiguousarray(pl.mean(2))
        lo = cv2.GaussianBlur(l0, (0, 0), 7.0)                                           # its tones, and only a third of its
        lum, z = self._ground_sample(lo + 0.33 * (l0 - lo))                               # edges (ledges flatten into stripes on the page)
        ln = np.clip((lum - 0.02) / 0.27, 0, 1)
        k = 0.40 + 0.70 * ln
        k = np.where(z < self.TOWN['hill'][0] + 0.02, k, 1.0)                            # behind the card: plain page
        return cv2.GaussianBlur(k.astype(np.float32), (0, 0), 0.8)

    def ground_real(self):
        """the same ground in the plate's painted colours (for the end of D4, when the print becomes the place)."""
        if not hasattr(self, '_greal'):
            pl = self.plate5('first_fire_hill_wide_v1')
            lo = cv2.GaussianBlur(pl, (0, 0), 7.0)
            self._greal = self._ground_sample(np.ascontiguousarray(lo + 0.33 * (pl - lo)))[0]
        return self._greal

    HILL_ROW0, HILL_PAD, HILL_UNITS = 515, 400, 3.5      # the card: plate rows 515..941, mirrored 400 px past each side

    def hill_world(self, q):
        """a hill-plate pixel on the standing hill card (world units)."""
        k = self.HILL_UNITS / 1672.0
        return np.array([(q[0] - 836.0) * k, (941.0 - q[1]) * k, self.TOWN['hill'][0]])

    def hill_print(self):
        """the hill of first_fire_hill_wide_v1 as a pop-up card: the land below the plate's own skyline (the near hill
        with its flat stone and tinder, the far ranges), printed on the paper in the plate's tones. It is the landmark the
        town and the village stand in front of, and at the end of D4 the print becomes the painted place."""
        pl = self.plate5('first_fire_hill_wide_v1')
        sm = cv2.GaussianBlur(pl * 255.0, (0, 0), 2.0)
        sb, sr = sm[..., 0], sm[..., 2]
        sl = 0.11 * sm[..., 0] + 0.59 * sm[..., 1] + 0.30 * sm[..., 2]
        y = np.arange(480, 900)
        land = (sb[y] - sr[y] < 24) | ((sl[y] < sl[y - 7] - 3.0) & (sl[y + 4] < sl[y - 7] - 3.0))   # ground, or a darker range below the sky's glow
        sky = 480 + np.argmax(land, 0).astype(np.float32)
        sky = cv2.medianBlur(sky.astype(np.uint16)[None, :], 5)[0].astype(np.float32)
        sky = cv2.GaussianBlur(sky[None, :], (0, 0), 1.5)[0]
        self.hill_skyline = sky
        r0, pad = self.HILL_ROW0, self.HILL_PAD
        land_px = pl[r0:]
        rows = np.arange(r0, 941, dtype=np.float32)[:, None]
        a = np.clip(rows - sky[None, :] + 0.5, 0, 1)
        lum = land_px.mean(2)
        ln = np.clip((lum - 0.02) / 0.27, 0, 1)
        pr = paper(1672, 941 - r0, 41, tone=(0.74, 0.84, 0.90)) * (0.40 + 0.70 * ln)[..., None]
        tex = np.dstack([pr, a]).astype(np.float32)
        edge = np.zeros(a.shape, np.float32)
        cv2.polylines(edge, [np.int32(np.stack([np.arange(1672) * 4, (sky - r0) * 4], 1))], False, 1.0, 1, cv2.LINE_AA, shift=2)
        tex[..., :3] = tex[..., :3] * (1 - 0.7 * edge[..., None]) + INK * 0.7 * edge[..., None]
        tex = cv2.copyMakeBorder(tex, 0, 0, pad, pad, cv2.BORDER_REFLECT_101)
        self.hill_real = cv2.copyMakeBorder(np.dstack([land_px, a]).astype(np.float32), 0, 0, pad, pad, cv2.BORDER_REFLECT_101)
        q = self.HILL_TINDER
        return tex, [], (q[0] + pad, q[1] - r0)

    # ------------------------------------------------------------ shots
    def v1a(self, t):
        """KV5a: the light in A's palm flickers on the burst; she offers it (key pose, held)."""
        img = self.kv5a.copy()
        c = (1361 * OI.S, (1205 - 160) * OI.S)
        burst = [13.804, 13.874, 13.932, 13.990]
        it = 1.0 + sum(0.7 * np.exp(-(t - b) / 0.05) for b in burst if t >= b) + 0.4 * ease(14.47, 14.8, t)
        return glow(img, c, 0.5 + 0.1 * ease(14.47, 14.95, t), it)

    # V1b uses the side-palm candidate in A3's place: same pose, closer crop. Matched to A3's framing by the X clip
    # and the iris (A3 (360, 564), (468, 664); candidate (440, 272), (564, 388): scale 0.867, same angle).
    V1B_S = 0.8667 * 1400.0 / 1536.0
    V1B_T = (360.0 * 0.9115 - 66.7 - 440.0 * 0.8667 * 1400.0 / 1536.0, 564.0 * 0.9115 - 320.0 - 272.0 * 0.8667 * 1400.0 / 1536.0)

    def v1b_layers(self):
        if not hasattr(self, '_v1b'):
            src, a = self.A3c
            pal = (1005.0, 600.0)                                                        # the palm's cup (candidate px)
            lit = relight(src, a, pal, 420 / 0.8667, 1.0)
            s_, (tx, ty) = self.V1B_S, self.V1B_T
            M = np.float32([[s_, 0, tx], [0, s_, ty]])
            pre = cv2.warpAffine(lit * a[..., None], M, (W, H), flags=cv2.INTER_AREA)
            al = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_AREA)
            q = lambda x, y: np.array([s_ * x + tx, s_ * y + ty])
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            hc, nk = q(560, 280), q(600, 560)
            dh = np.hypot(xx - hc[0], yy - hc[1])
            head = (1 - smooth((dh - 160) / 160)) * (1 - smooth((yy - nk[1] + 30) / 90))          # the head and the hair at it
            hand = smooth((xx - q(800, 0)[0]) / 40) * smooth((yy - q(0, 430)[1]) / 40)
            head *= 1 - hand
            hang = smooth((yy - q(0, 330)[1]) / 200) * (1 - smooth((xx - q(470, 0)[0]) / 60)) * (1 - head)   # hair hanging on the left
            ir = q(564, 388)
            iris = np.exp(-((xx - ir[0]) ** 2 + (yy - ir[1]) ** 2) / (2 * 6.0 ** 2))
            tips = hand * smooth((xx - q(1130, 0)[0]) / 50) * (1 - smooth((yy - q(0, 600)[1]) / 40))
            self._v1b = dict(pre=pre, al=al, head=head, hang=hang, iris=iris, tips=tips, pivot=nk, light=q(1005, 560),
                             xx=xx, yy=yy)
        return self._v1b

    def v1b(self, t):
        """A, close (side-palm candidate): on the 14.97 hit the light in her palm opens into a sheet of paper. It rises
        beside her, opening to face us; her eyes lift to it first, then her head follows a little, and her hand eases as
        the light leaves it. Only in the last six frames does the sheet come to the lens and become the lit letter of P1a."""
        L = self.v1b_layers()
        img = night_backdrop(1)
        img = glow(img, (640, 900), 2.0, 0.35)                                           # the Earth's glow below frame
        xx, yy = L['xx'], L['yy']
        th = np.radians(2.0 * ease(15.06, 15.46, t))                                     # chin up 2 deg about the neck
        th_l = np.radians(2.0 * ease(15.14, 15.56, t))                                   # the hanging hair a little later
        px, py = L['pivot']

        def rot(th_):
            x, y = xx - px, yy - py
            return x * np.cos(th_) + y * np.sin(th_) - x, -x * np.sin(th_) + y * np.cos(th_) - y
        hdx, hdy = rot(th)
        ldx, ldy = rot(th_l)
        g = ease(14.99, 15.22, t)                                                        # the eyes lead
        rel = 2.5 * (ease(15.02, 15.30, t) - 0.45 * ease(15.30, 15.62, t))               # the hand eases as the light leaves
        dx = L['head'] * hdx + 0.6 * L['hang'] * ldx + L['iris'] * 1.3 * g
        dy = L['head'] * hdy + 0.6 * L['hang'] * ldy - L['iris'] * 2.2 * g + L['tips'] * rel
        mx, my = (xx - dx).astype(np.float32), (yy - dy).astype(np.float32)
        pre = cv2.remap(L['pre'], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        al = cv2.remap(L['al'], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        img = img * (1 - al[..., None]) + pre
        p = L['light']
        if t < 14.97:
            return glow(img, p, 0.45, 1.4)
        cam = Cam((0, 0, -3.0), (0, 0, 0))

        def world(q, z):                                                                 # screen point at depth z
            return np.array([(q[0] - 640) / F * (3.0 + z), -(q[1] - 360) / F * (3.0 + z), z])
        pw, ph = self.page_wh
        if STAGE == 'v9':
            # v9: no sheet grows out of a point. The light in her palm dims to show what it is: a small note, folded in
            # quarters and lit from inside. It lifts off the palm, its top half opens, then its right half, as it rises
            # toward us beside her; its size never changes, only its distance (z 0 at her palm, -1.6 beside her).
            a1 = ease(15.10, 15.58, t)                                                   # rests in the cup, then lift and travel
            h_full = 0.233
            s_, (tx_, ty_) = self.V1B_S, self.V1B_T
            palm_c = world(np.array([s_ * 1005.0 + tx_, s_ * 594.0 + ty_]), 0.0)          # on the palm's cup (candidate px 1005, 600)
            A_ctr = palm_c * (1 - a1) + world((935.0, 285.0), -1.6) * a1 + np.array([0, 0.05, 0]) * np.sin(np.pi * a1)
            A_sz = h_full
            tilt = -np.radians(62) * (1 - smooth(a1 / 0.7)) + np.radians(10) * smooth(a1)  # lying in the palm, then upright
            open_top = np.pi * (1 - ease(15.14, 15.34, t))
            open_right = np.pi * (1 - ease(15.30, 15.50, t))
        else:
            a1 = ease(14.97, 15.58, t)                                                   # opening beside her
            A_ctr = world(p, 0.0) * (1 - a1) + world((935.0, 285.0), 0.0) * a1 + np.array([0, 0.04, 0]) * np.sin(np.pi * a1)
            A_sz = 0.10 + 0.40 * a1 ** 1.2
            tilt = -np.radians(85) * (1 - smooth(a1 / 0.85)) + np.radians(10) * smooth(a1)  # top edge leans back a little
            open_top = open_right = 0.0
        b1 = ease(15.60, 15.833, t)                                                      # then onto P1a's page (exact on frame 380)
        yaw = np.radians(-16.0) + np.radians(4.0) * np.sin(2 * np.pi * (t - 14.97) / 1.6)
        uA = rot_axis(np.array([1.0, 0, 0]), (0, 1, 0), yaw)
        vA = rot_axis(rot_axis(np.array([0, 1.0, 0]), (1, 0, 0), tilt), (0, 1, 0), yaw)
        bendA = (0.22 * smooth(a1 / 0.6) + 0.05 * np.sin(2 * np.pi * (t - 14.97) / 1.1)) * (1.0 if STAGE != 'v9' else smooth((t - 15.48) / 0.12))
        # the arrival: P1a's first frame, its page pose carried into this camera (same lens, same screen geometry)
        Cp, focus = self.p1a_cam(15.875)
        Rm = np.stack([cam.rt, cam.up, cam.fw], 1) @ np.stack([Cp.rt, Cp.up, Cp.fw], 0)

        def T(X):
            return cam.p + Rm @ (np.asarray(X, np.float64) - Cp.p)
        cB, uB, vB = T((0, 0, 0)), Rm @ np.array([1.0, 0, 0]), Rm @ np.array([0, 0, 1.0])
        c = A_ctr * (1 - b1) + cB * b1
        u = uA * (1 - b1) + uB * b1
        u /= np.linalg.norm(u)
        v = vA * (1 - b1) + vB * b1
        v -= (v @ u) * u
        v /= np.linalg.norm(v)
        w_ = A_sz * pw / ph * (1 - b1) + pw / self.PU * b1
        h_ = A_sz * (1 - b1) + ph / self.PU * b1
        c_mid = c.copy()                                                                 # where the folded block's middle is
        if STAGE == 'v9':                                                                # the closed quarters sit in the lower left
            c = c + u * w_ / 4 * (open_right / np.pi) + v * h_ / 4 * (open_top / np.pi)
        k = 0.6 * a1 + 0.4 * b1
        lit = self.lit_page(15.875)
        tex = np.dstack([lit * (0.6 + 0.4 * k) + np.array([0.25, 0.42, 0.55], np.float32) * (1 - k) ** 2, np.ones((ph, pw), np.float32)])
        if STAGE == 'v9' and (open_top > 0.01 or open_right > 0.01):
            if not hasattr(self, '_note_back'):
                bk = paper(pw, ph, 77, tone=(0.70, 0.78, 0.84))
                ink = np.clip(1 - self.page.mean(2, keepdims=True) / max(float(self.page.mean()), 1e-3), 0, 1)
                self._note_back = np.dstack([bk * (1 - 0.18 * ink), np.ones((ph, pw), np.float32)]).astype(np.float32)
            glow_in = 1 - 0.6 * smooth((t - 15.10) / 0.40)                              # lit from inside while folded
            back = self._note_back.copy()
            back[..., :3] = back[..., :3] * np.array([0.42, 0.40, 0.46], np.float32) + np.array([0.25, 0.45, 0.62], np.float32) * glow_in
            hot = 1 - ease(14.97, 15.12, t)                                              # first only a light; the paper shows as it dims
            hotc = np.array([0.80, 0.93, 1.0], np.float32)
            ftex, btex = tex.copy(), back
            ftex[..., :3] = ftex[..., :3] * (1 - hot) + hotc * hot
            btex[..., :3] = btex[..., :3] * (1 - hot) + hotc * hot
            img = put_folded(img, cam, c, u, v, w_, h_, ftex, btex, open_top, open_right)
        elif b1 < 0.5:
            img = put_bent(img, cam, c, u, v, w_, h_, tex, bendA * (1 - b1))
        else:                                                                            # P1a's depth of field comes in
            img, _ = put_card(img, cam, card_corners(c, u, v, w_, h_), tex, focus=focus, aperture=0.45 * smooth((b1 - 0.5) / 0.5),
                              dof_map=True)
        # the light: on the sheet, then exactly where P1a's reader light is on its first frame
        lp = cam.project(c_mid)[0][0] * (1 - b1) + cam.project(T(self.reader_light(15.875)))[0][0] * b1
        if STAGE == 'v9':
            shrink = ease(14.97, 15.12, t)                                               # the glow draws in to the note
            img = glow(img, lp, (0.45 - 0.22 * shrink + 0.15 * k) * (1 - b1) + 0.16 * b1,
                       (1.4 - 0.75 * shrink) * (1 - 0.5 * k) * (1 - b1) + 0.9 * b1)
        else:
            img = glow(img, lp, (0.35 + 0.25 * k) * (1 - b1) + 0.16 * b1, 1.1 * (1 - 0.7 * k) * (1 - b1) + 0.9 * b1)
        if b1 > 0:
            OI.dot(img, lp, 2.0, b1)
        return img

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
        # the tear lines: a thin crease darkens just before each piece comes free (paper, not light)
        if 17.42 <= t:
            cr = self.crack * smooth((t - self.crack_t) / 0.08)
            out = out * (1 - 0.55 * cr[..., None])
        self._lit, self._lit_t = out, (t, id(src))
        return out

    def frag_pose(self, fr, t):
        """centre, u, v of a fragment at time t (P1a)."""
        bx0, by0, bx1, by1 = fr['box']
        c0 = self.tex2world(np.array([(bx0 + bx1) / 2, (by0 + by1) / 2]))
        k = max(0.0, t - 17.71 - fr['delay'])
        c = c0 + np.array([0, 1.0, 0]) * fr['rise'] * (0.30 * k + 0.35 * k * k) + fr['out'][[0, 2, 1]] * np.array([1, 0, -1]) * 0.22 * k
        ang = fr['spin'] * k * 1.1
        u = rot_axis(np.array([1.0, 0, 0]), fr['axis'], ang)
        v = rot_axis(np.array([0, 0, 1.0]), fr['axis'], ang)
        return c, u, v, k

    def p1a_cam(self, t):
        g = ease(15.875, 17.35, t)
        tx = -0.62 + 1.20 * g + 0.10 * ease(17.35, 18.6, t)
        tz = 0.02 - 0.06 * ease(17.0, 17.6, t)
        h = 0.56 + 0.16 * ease(15.875, 16.6, t) + 0.38 * ease(17.6, 18.6, t)
        back = 0.50 + 0.12 * ease(15.875, 16.6, t) + 0.30 * ease(17.6, 18.6, t)
        cam = Cam((tx - 0.10, h, tz - back), (tx, 0.0, tz), roll=0.05 - 0.07 * g)
        return cam, float(np.linalg.norm(np.array([tx, 0, tz]) - cam.p))

    def p1a(self, t):
        """the letter, close: the light reads the words ("in the words that you left"), settles in the full stop, and
        the page cracks open from it and lifts in fragments ("we met you in fragments")."""
        img = night_backdrop(2, top=(22, 14, 10), bottom=(34, 22, 16))
        L = self.reader_light(t)
        cam, focus = self.p1a_cam(t)
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
                tex = np.dstack([lit[by0:by1, bx0:bx1] * (1 + 0.15 * min(1.0, k * 2)) + fr['fibre'][..., None] * 0.12, fr['alpha']])
                bend = fr['bend'] * (0.45 + 0.55 * np.sin(fr['phase'] + 5.0 * k)) * min(1.0, k * 4)
                cards.append((float((c - cam.p) @ cam.fw), c, u, v, (bx1 - bx0) / self.PU, (by1 - by0) / self.PU, tex, bend))
            tex = np.dstack([lit, np.clip(rest, 0, 1)])
            img, _ = put_card(img, cam, card_corners((0, 0, 0), (1, 0, 0), (0, 0, 1), pw / self.PU, ph / self.PU), tex,
                              focus=focus, aperture=0.45, dof_map=True)
            for zc, c, u, v, w_, h_, tex, bend in cards:                                 # soft shadows on the page while low
                if c[1] < 0.35:
                    sh = np.zeros_like(tex)
                    sh[..., 3] = tex[..., 3] * 0.45 * np.exp(-c[1] / 0.18)
                    g0 = np.array([c[0] + 0.05 * c[1], 0.001, c[2] - 0.05 * c[1]])
                    ug, vg = np.array([u[0], 0, u[2]]), np.array([v[0], 0, v[2]])
                    if np.linalg.norm(ug) > 0.2 and np.linalg.norm(vg) > 0.2:
                        img, _ = put_card(img, cam, card_corners(g0, ug, vg, w_ * np.linalg.norm(ug), h_ * np.linalg.norm(vg)), sh,
                                          extra_blur=2.0 + 30.0 * c[1])
            for zc, c, u, v, w_, h_, tex, bend in sorted(cards, key=lambda q: -q[0]):
                img = put_bent(img, cam, c, u, v, w_, h_, tex, bend, focus=focus, aperture=0.45)
        p, z = cam.project(L)
        if z[0] > 0.05:
            img = glow(img, p[0], 0.16 + 0.06 * ease(17.71, 18.6, t), 0.9)
            OI.dot(img, p[0], 2.0, 1.0)
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
        for k in range(2):                                                             # in front of her, close: dark paper, below her face
            fr = self.frags[k * 7 + 3]
            x = 2.0 - 3.4 * ((t - 18.62 + 0.45 * k) / 1.0)
            pos = np.array([x * 0.6, -0.28 - 0.06 * k, -1.15 + 0.15 * k])
            ang = 1.2 * (t - 18.6) + k
            u = rot_axis(np.array([1.0, 0, 0]), fr['axis'], ang)
            v = rot_axis(np.array([0, 1.0, 0]), fr['axis'], ang)
            bx0, by0, bx1, by1 = fr['box']
            tex = np.dstack([self.page[by0:by1, bx0:bx1] * np.array([0.22, 0.24, 0.30]), fr['alpha']])
            img, _ = put_card(img, cam, card_corners(pos, u, v, 0.34, 0.30), tex, focus=2.0, aperture=1.0)
        q = (930 + 20 * (t - 18.6), 140 - 40 * (t - 18.6))                                # the light from the full stop, still rising
        img = glow(img, q, 0.22, 0.7)
        OI.dot(img, q, 2.0, 1.0)
        return img

    LAMP_SCREEN = (168.0, 241.0)                                                        # M2's lamp on screen (see m2)

    WAR_WICK = np.array([289.0, 351.0])            # war_memory_v1 (1672x941): the wick's tip, measured (its base is at 292, 390)
    WAR_FLAME_UP = 25.0                            # the lit flame's centre above the tip (plate px)

    def plate5(self, name):
        if not hasattr(self, '_p5'):
            self._p5 = {}
        if name not in self._p5:
            self._p5[name] = cv2.imread(os.path.join(PLATES5, name + '.png')).astype(np.float32) / 255.0
        return self._p5[name]

    def war_view(self, t):
        """M1's window on the plate (x0, y0, width): it opens from 1150 to 1500 px while the wick drifts from where the
        letter's point lands (260, 262) to where its flame sits on M2's lamp (LAMP_SCREEN)."""
        u = ease(20.458, 22.25, t)
        w = 1150.0 * (1500.0 / 1150.0) ** u
        end = np.array(self.LAMP_SCREEN) + np.array([0.0, self.WAR_FLAME_UP * W / 1500.0])
        tip = np.array([260.0, 262.0]) * (1 - u) + end * u
        return self.WAR_WICK[0] - tip[0] * w / W, self.WAR_WICK[1] - tip[1] * w / W, w

    def candle_xy(self):
        x0, y0, w = self.war_view(20.458)
        return self.c2s(self.WAR_WICK, x0, y0, w)                                       # M1's first frame: the wick tip

    def m1(self, t):
        """"every war": the letter's point lands on the unlit wick and lights it (20.47-20.62); the candle's light then
        finds the room: the wax, the letter on the table (the same hand's stroke), the helmet, and through the broken
        window the ruins under a cold night. The view opens while the candle drifts to where M2's lamp will be."""
        pl = self.plate5('war_memory_v1')
        hh, ww = pl.shape[:2]
        catch = ease(20.47, 20.62, t)
        rev = ease(20.56, 21.15, t)
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        Lx, Ly = self.WAR_WICK[0], self.WAR_WICK[1] - self.WAR_FLAME_UP
        d2 = (xx - Lx) ** 2 + (yy - Ly) ** 2
        r = 120.0 + 620.0 * rev
        fl = 1.0 + 0.04 * np.sin(t * 2 * np.pi * 6.3) + 0.025 * np.sin(t * 2 * np.pi * 11.9)
        warm = (1.25 * np.exp(-d2 / (r * r)) + 0.55 * np.exp(-d2 / (60.0 ** 2))) * catch * fl
        # moonlight: low in the room, higher through the window onto the ruins
        win = np.clip((xx - 790) / 30, 0, 1) * np.clip((1515 - xx) / 30, 0, 1) * np.clip((468 - yy) / 30, 0, 1)
        amb = (0.16 + 0.10 * rev) + 0.42 * win
        k = amb[..., None] * np.array([1.10, 0.95, 0.85], np.float32) + warm[..., None] * np.array([0.55, 0.88, 1.18], np.float32)
        img = self.to_screen(pl * k, *self.war_view(t))
        x0, y0, w = self.war_view(t)
        tip = self.c2s(self.WAR_WICK, x0, y0, w)
        img = glow(img, tip, 0.14, 1.0 * (1 - catch))                                  # the arriving point, until the wick takes it
        if catch < 1:
            OI.dot(img, tip, 1.8, 1.0 - catch)
        return candle_flame(img, tip, 26.0 * W / w, t, k=catch)

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
        scan = -120 + 1520 * ease(19.55, 20.0, t)
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
        gather = ease(20.20, 20.34, t)                                                  # the others come to the spiral
        fold = ease(20.27, 20.42, t) ** 1.2                                              # then the spiral folds to a point
        hc = [c for c in self.cloud if c['fr']['hero']][0]
        hb = hc['fr']['box']
        hdx, hdy = (self.dot_px[0] - (hb[0] + hb[2]) / 2) / self.PU, -(self.dot_px[1] - (hb[1] + hb[3]) / 2) / self.PU

        def frame_of(c):
            ang = c['a0'] + c['w'] * (t - 19.5) + (1.4 * fold if c is hc else 0.0)
            return rot_axis(np.array([1.0, 0, 0]), c['axis'], ang), rot_axis(np.array([0, 1.0, 0]), c['axis'], ang)
        hu, hv = frame_of(hc)
        hsz = 1.0 - 0.96 * fold
        hpos0 = hc['pos'] + np.array([0, 0.10 * (t - 19.5), 0])
        hpos = hpos0 * (1 - fold) + (Pc - (hu * hdx + hv * hdy) * hsz) * fold         # the full stop lands where the candle is
        Lc = hpos + (hu * hdx + hv * hdy) * hsz                                          # the light sits in the full stop
        for c in self.cloud:
            fr = c['fr']
            bx0, by0, bx1, by1 = fr['box']
            u, v = frame_of(c)
            if c is hc:
                pos, sz = hpos, hsz
            else:
                pos = c['pos'] + np.array([0, 0.10 * (t - 19.5), 0])
                pos = pos * (1 - gather) + hpos * gather
                sz = (1.0 - 0.75 * gather) * (1 - fold)
                if sz < 0.02:
                    continue
            w_, h_ = (bx1 - bx0) / self.PU * sz, (by1 - by0) / self.PU * sz
            corners = card_corners(pos, u, v, w_, h_)
            xy, z = cam.project(corners)
            if (z < 0.05).any():
                continue
            pa, pb = self.page[by0:by1, bx0:bx1], self.page_alt[by0:by1, bx0:bx1]
            cols = np.linspace(xy[0, 0], xy[1, 0], bx1 - bx0)[None, :]                   # screen x of each texel column
            mix = np.clip((scan - cols) / 40.0, 0, 1)[..., None]
            line = np.exp(-((scan - cols) / 6.0) ** 2)[..., None] * (0 < ease(19.55, 20.0, t) < 1)
            dl = np.linalg.norm(pos - Lc)
            shade = 0.55 + 0.6 * np.exp(-(dl / 1.0) ** 2)
            col = (pa * (1 - mix) + pb * mix) * np.array([0.60, 0.80, 1.05], np.float32) * shade
            col = col * (1 - 0.35 * line)                                                # the rewriting edge: a pen's shadow, not light
            if c['near']:
                col = col * 0.30
            tex = np.dstack([col + fr['fibre'][..., None] * 0.10, fr['alpha'] * (1 - 0.6 * gather * (c is not hc) * smooth((gather - 0.6) / 0.4))])
            cards.append((float((pos - cam.p) @ cam.fw), corners, tex))
        for zc, corners, tex in sorted(cards, key=lambda q: -q[0]):
            img, _ = put_card(img, cam, corners, tex, focus=1.75, aperture=0.6)
        p = cam.project(Lc)[0][0]
        img = glow(img, p, 0.14 + 0.06 * fold, 0.8 + 0.4 * fold)
        OI.dot(img, p, 1.8, 1.0)
        self.compress_pt = cxy
        return img

    # ------------------------------------------------------------ the supplied memory art (1536x1024 canvases)
    def full(self, name):
        """a supplied PNG at full size, BGR 0..1 plus its real alpha (opaque plates get alpha 1)."""
        if not hasattr(self, '_full'):
            self._full = {}
        if name not in self._full:
            im = cv2.imread(os.path.join(ART, name + '.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255.0
            if im.shape[2] == 3:
                im = np.dstack([im, np.ones(im.shape[:2], np.float32)])
            self._full[name] = im
        return self._full[name]

    @staticmethod
    def over(canvas, lay):
        a = lay[..., 3:4]
        return canvas * (1 - a) + lay[..., :3] * a

    @staticmethod
    def grade(canvas, lights, night=(0.50, 0.48, 0.58), warm=(0.66, 0.90, 1.12)):
        """the daylight drawing at night: a cool fill, warm only where a real light is (canvas px)."""
        hh, ww = canvas.shape[:2]
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        k = np.zeros((hh, ww), np.float32)
        for cx, cy, r, kk in lights:
            k += kk * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r))
        k = np.clip(k, 0, 1.3)[..., None]
        night, warm = np.array(night, np.float32), np.array(warm, np.float32)
        return canvas * (night + (warm - night) * k)

    @staticmethod
    def to_screen(canvas, x0, y0, w, cubic=False):
        """crop a 16:9 window (x0, y0, width w, canvas px) to 1280x720."""
        s_ = W / w
        M = np.float32([[s_, 0, -x0 * s_], [0, s_, -y0 * s_]])
        fl = cv2.INTER_AREA if s_ < 1 else (cv2.INTER_CUBIC if cubic else cv2.INTER_LINEAR)
        return cv2.warpAffine(canvas, M, (W, H), flags=fl) * 255.0

    @staticmethod
    def c2s(p, x0, y0, w):
        return np.array([(p[0] - x0) * W / w, (p[1] - y0) * W / w])

    def m2(self, t):
        """"every lullaby" (full frame): the parent's hand on the rim gives the cradle one small push at 22.32; it
        rolls on its rockers (no sliding: the contact stays on the floor line) and settles. The cradle and the hand move
        together; the forearm bends gently toward the sleeve, which stays at the frame edge. The lamp answers the
        candle of M1 (same screen place)."""
        bg, cr = self.full('lullaby_bg'), self.full('lullaby_cradle')
        R_, contact = 1290.0, np.array([752.0, 845.0])                                   # rocker radius and lowest contact (measured)
        tau = max(0.0, t - 22.32)
        phi = 1.1 * np.sin(2 * np.pi * 0.62 * tau) * np.exp(-tau / 1.1) * smooth(tau / 0.12)   # degrees
        C = contact - np.array([0.0, R_])
        M = cv2.getRotationMatrix2D((float(C[0]), float(C[1])), phi, 1.0)
        M[0, 2] -= R_ * np.sin(np.radians(phi))                                          # roll, do not slide
        hh, ww = cr.shape[:2]
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        Minv = cv2.invertAffineTransform(M)
        sx = Minv[0, 0] * xx + Minv[0, 1] * yy + Minv[0, 2]
        sy = Minv[1, 0] * xx + Minv[1, 1] * yy + Minv[1, 2]
        wgt = np.clip((1535.0 - xx) / (1535.0 - 1200.0), 0, 1)                           # 1 on the cradle and the fingers, 0 at the sleeve end
        mx, my = (xx + (sx - xx) * wgt).astype(np.float32), (yy + (sy - yy) * wgt).astype(np.float32)
        lay = cv2.remap(cr, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        canvas = bg[..., :3].copy()
        # a restrained contact shadow under the rockers, moving with the contact
        cxs = contact[0] - 0.0
        sh = np.exp(-(((xx - cxs) / 330.0) ** 2) - (((yy - 850.0) / 14.0) ** 2))
        canvas *= (1 - 0.22 * sh)[..., None]
        canvas = self.over(canvas, lay)
        lamp_k = 0.85 + 0.15 * ease(22.25, 22.45, t)                                     # the lamp answers the candle
        canvas = self.grade(canvas, [(202, 410, 520, lamp_k), (202, 410, 160, 0.35 * lamp_k)])
        img = self.to_screen(canvas, 0, 120, 1536)
        q = self.c2s((202, 410), 0, 120, 1536)
        return glow(img, q, 0.10, 0.45 * lamp_k)

    FW_SHIFT0 = 60.0                                                                     # the carriage starts this far right: fingertips ~11 px apart

    def fw_dx(self, t):
        part = ease(24.15, 24.55, t)
        go = max(0.0, t - 24.50)
        return self.FW_SHIFT0 - 45.0 * part - 1500.0 * go ** 2

    def m3(self, t):
        """"every last goodbye" (full frame, close on the hands): the passenger's hand and the hand on the platform nearly
        touch; the carriage begins to move and the fingertips part, then it pulls away left with a slow acceleration.
        Only the carriage moves; nothing is stretched. A small warm spark stays in the gap and rises (it becomes the
        constellations)."""
        bg, tr = self.full('farewell_bg'), self.full('farewell_train')
        dx = self.fw_dx(t)
        lay = cv2.warpAffine(tr, np.float32([[1, 0, dx], [0, 1, 0]]), (1536, 1024), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        canvas = self.over(bg[..., :3].copy(), lay)
        canvas = self.grade(canvas, [(960, 560, 520, 0.55), (560, 300, 380, 0.35)])        # the platform lamp, the lit carriage
        x0, y0, w = 400, 265, 1136
        img = self.to_screen(canvas, x0, y0, w)
        if t > 24.30:
            k = ease(24.30, 24.45, t)
            gap = np.array([907.0, 581.0]) - np.array([0.0, 140.0 * ease(24.55, 25.0, t) ** 1.3])
            q = self.c2s(gap, x0, y0, w)
            img = glow(img, q, 0.07, 0.9 * k)
            OI.dot(img, q, 1.6, k)
            self.spark_end = q
        return img

    def d2(self, t):
        """"You had heat" (full frame): an old hand and a child's hand around one bowl; thin steam rises from the rim
        and drifts; a restrained warmth near the bowl, the window stays cold. At most a small push."""
        bw = self.full('bowl')
        canvas = self.grade(bw[..., :3].copy(), [(770, 600, 560, 0.75)], night=(0.50, 0.48, 0.58))
        hh, ww = canvas.shape[:2]
        steam = np.zeros((hh, ww), np.float32)
        rng = np.random.default_rng(23)
        for k in range(7):                                                              # thin wisps from the visible opening
            bx = 640 + 260 * (k + rng.uniform(0, 0.6)) / 7
            ph0, sp = rng.uniform(0, 6.3), rng.uniform(0.6, 1.0)
            ys = np.linspace(530, 170, 60)
            life = ((t - 30.458) * sp * 0.55 + k * 0.13) % 1.0
            rise = (530 - ys) / 360.0
            xs = bx + 14 * np.sin(rise * 7 + ph0 + t * 1.6) * rise + 40 * rise * rise * np.sin(ph0)
            a = np.clip(1 - np.abs(rise - life) / 0.35, 0, 1) * np.clip(rise * 6, 0, 1) * (1 - rise) ** 0.6
            for j in range(59):
                if a[j] > 0.02:
                    cv2.line(steam, (int(xs[j] * 4), int(ys[j] * 4)), (int(xs[j + 1] * 4), int(ys[j + 1] * 4)), float(a[j]), 3,
                             cv2.LINE_AA, shift=2)
        steam = cv2.GaussianBlur(steam, (0, 0), 3.0) * ease(30.458, 30.75, t)
        canvas = canvas + steam[..., None] * np.array([0.30, 0.32, 0.34], np.float32)
        u = ease(30.458, 32.292, t)
        w = 1536 - 40 * u
        return self.to_screen(canvas, (1536 - w) / 2, 70 + 10 * u, w)

    def d3(self, t):
        """"Three-dimensional hearts" (full frame, close): the newborn asleep on the parent's chest, the parent's hand on
        its back. The parent breathes and the whole baby rises and settles with the chest (one connected layer, never a
        floating head); the baby's own faster, smaller breath on top. No light comes from the chest."""
        back, baby = self.full('newborn_back'), self.full('newborn_baby')
        tau = t - 32.292
        big = 0.5 - 0.5 * np.cos(2 * np.pi * tau / 3.1)                                  # the parent: one slow breath
        small = 0.5 - 0.5 * np.cos(2 * np.pi * tau / 1.15)                               # the baby
        piv = (900.0, 1024.0)                                                            # the chest rises from below frame
        Mp = cv2.getRotationMatrix2D(piv, 0.0, 1.0 + 0.007 * big)
        Mp[1, 2] -= 5.0 * big
        Mb = cv2.getRotationMatrix2D(piv, 0.0, 1.0 + 0.007 * big + 0.003 * small)
        Mb[1, 2] -= 5.0 * big + 1.5 * small
        canvas = cv2.warpAffine(back, Mp, (1536, 1024), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)[..., :3]
        lay = cv2.warpAffine(baby, Mb, (1536, 1024), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        canvas = self.over(canvas, lay)
        canvas = self.grade(canvas, [(380, 260, 700, 0.85)], night=(0.52, 0.50, 0.58))   # a lamp off frame, upper left
        return self.to_screen(canvas, 0, 110, 1536)

    # the strike: the held stone's lowest tip (885, 540) meets the lower stone's top (717, 684); measured on the art
    STONE_TIP, STONE_HIT, TINDER = np.array([885.0, 540.0]), np.array([717.0, 684.0]), np.array([787.0, 695.0])
    D5_VIEW = (273.0, 298.0, 1160.0)                                                     # puts the tinder at (567, 443) on screen

    # (time, s, wrist deg): s 0 rest .. 1 contact (the stone tip on the lower stone), s < 0 raised; wrist + = cocked back
    STRIKE_KEYS = [(39.25, 0.0, 0.0), (39.38, -0.14, 4.0), (39.46, -0.15, 4.5), (950 / 24, 1.0, -1.5), (951 / 24, 1.0, -1.5),
                   (39.68, 0.86, 1.5), (39.80, 0.55, 3.0), (39.92, 0.40, 4.0), (39.96, 0.40, 4.0), (961 / 24, 1.0, -2.0),
                   (962 / 24, 1.0, -2.0), (40.14, 0.88, 2.0), (40.40, 0.58, 1.0), (41.17, 0.50, 0.5)]

    def strike(self, t):
        """the stone tip's position (canvas px), the forearm's swing about the elbow (deg), the wrist (deg) and the
        contact flag. Preparation: the fist lifts and the wrist cocks back, with a slow-in hold at the top. Strike: it
        accelerates into contact (exact on frames 950-951 and 961-962). Rebound: fast out, decelerating, the wrist
        giving a little. The forearm angle follows the height (raised = swung up 3 deg), so the arm is not a sliding block."""
        ks = self.STRIKE_KEYS
        ts = [k[0] for k in ks]
        i = max(0, min(len(ks) - 2, int(np.searchsorted(ts, t)) - 1))
        (t0, s0, w0), (t1, s1, w1) = ks[i], ks[i + 1]
        f = float(np.clip((t - t0) / (t1 - t0), 0, 1))
        if s1 == 1.0 and s0 < 1.0:
            f = f * f                                                                    # accelerates into contact
        elif s0 == 1.0 and s1 < 1.0:
            f = 1 - (1 - f) ** 2                                                         # fast out of it
        elif s0 != s1:
            f = smooth(f)
        s_ = s0 + (s1 - s0) * f
        om = w0 + (w1 - w0) * (f if s0 != s1 else smooth(f))
        hit = self.STONE_HIT - self.STONE_TIP
        P = self.STONE_TIP + hit * s_ + np.array([18.0, -30.0]) * 4 * max(s_, 0.0) * (1 - s_)
        phi = -3.0 * (1 - min(s_, 1.0))
        return P, phi, om, s_ >= 0.995

    def d5_hand(self, t):
        """the hand layer at time t on the 1536x1024 canvas: the whole arm turned about the elbow (off frame, upper
        right), the fist also turned about the wrist, then placed so the stone tip is exactly where strike() puts it."""
        hd, pad = self._fire_hand, self._fire_pad
        P, phi, om, contact = self.strike(t)
        E, Wr = (1700.0, -200.0 + pad), (1060.0, 330.0 + pad)
        A = np.vstack([cv2.getRotationMatrix2D(E, phi, 1.0), [0, 0, 1]])
        B = np.vstack([cv2.getRotationMatrix2D(Wr, om, 1.0), [0, 0, 1]])
        tip = np.array([self.STONE_TIP[0], self.STONE_TIP[1] + pad, 1.0])
        q = A @ B @ tip
        T = np.array([[1, 0, P[0] - q[0]], [0, 1, P[1] - q[1]], [0, 0, 1]])
        full_i, fist_i = np.linalg.inv(T @ A), np.linalg.inv(T @ A @ B)
        if not hasattr(self, '_d5_grid'):
            yy, xx = np.mgrid[0:1024, 0:1536].astype(np.float32)
            self._d5_grid = (xx, yy)
        xx, yy = self._d5_grid
        fx = full_i[0, 0] * xx + full_i[0, 1] * yy + full_i[0, 2]
        fy = full_i[1, 0] * xx + full_i[1, 1] * yy + full_i[1, 2]
        gx = fist_i[0, 0] * xx + fist_i[0, 1] * yy + fist_i[0, 2]
        gy = fist_i[1, 0] * xx + fist_i[1, 1] * yy + fist_i[1, 2]
        wf = 1 - smooth((fx - 990.0) / 120.0)                                            # 1 on the fist, 0 past the wrist
        mx, my = (fx * (1 - wf) + gx * wf).astype(np.float32), (fy * (1 - wf) + gy * wf).astype(np.float32)
        lay = cv2.remap(hd, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        return lay, contact

    def d5(self, t):
        """"till you lit the first fire" (full frame, close): a hand strikes stone on stone; sparks start at the contact
        and fall into the tinder; the second strike leaves an ember; the flame catches on the 40.50 hit and lights the
        hand and the stone from below."""
        bg = self.full('fire_bg')
        if not hasattr(self, '_fire_hand'):
            hd = self.full('fire_hand').copy()
            g = hd[..., :3].mean(2, keepdims=True)                                       # harmonize the warmer hand with the cards
            hd[..., :3] = (hd[..., :3] * 0.6 + g * 0.4) * 0.92
            pad = 240                                                                    # the forearm continues past the canvas edge
            self._fire_hand = cv2.copyMakeBorder(hd, pad, 0, 0, pad, cv2.BORDER_REFLECT_101)   # cloth continues, not smeared
            self._fire_pad = pad
        lay, contact = self.d5_hand(t)
        ember = ease(40.08, 40.25, t) * (1 - ease(40.5, 40.7, t))
        fk = ease(40.50, 40.95, t)
        canvas = self.over(bg[..., :3].copy(), lay)
        lights = [(self.TINDER[0], self.TINDER[1] - 20, 120 + 280 * fk, 0.95 * fk + 0.25 * ember)]
        canvas = self.grade(canvas, lights, night=(0.52, 0.42, 0.38))                  # v6: the same night blue as the hill wide
        x0, y0, w = self.D5_VIEW
        img = self.to_screen(canvas, x0, y0, w)
        sc = W / w
        rng = np.random.default_rng(int(round(t * 48)))
        for s0 in (39.583, 40.042):                                                     # sparks: from the contact into the tinder
            if s0 <= t < s0 + 0.32:
                q = (t - s0) / 0.32
                srng = np.random.default_rng(int(s0 * 100))
                for k in range(11 if s0 > 40 else 8):
                    vx, vy = srng.uniform(60, 260), srng.uniform(-170, -40)
                    p = self.STONE_HIT + np.array([vx * q * 0.32, vy * q * 0.32 + 0.5 * 1400 * (q * 0.32) ** 2])
                    p = np.minimum(p, [2000, self.TINDER[1] + 10])
                    img = glow(img, self.c2s(p, x0, y0, w), 0.03, 1.3 * (1 - q) ** 0.7)
        if ember > 0:
            img = glow(img, self.c2s(self.TINDER + [0, -4], x0, y0, w), 0.05, 0.9 * ember * (0.8 + 0.2 * np.sin(t * 37)))
        if fk > 0:
            img = flame(img, self.c2s(self.TINDER, x0, y0, w), (5 + 20 * fk) * sc, t, k=fk)
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

    # C1: the memories as one spatial constellation. Each figure is traced from its own art (the M3 hands from M3's last
    # frame, the cradle from its layer's silhouette with the lamp, the candle, helmet and letter from the war plate, the
    # letter's mark from the letter page) and set in depth; the field behind is the letter's own handwriting, in pieces.
    C1_CAM = ((0.0, 0.0, -10.0), (0.0, 1.0, 0.0))
    C1_FIG = dict(hands=((650.0, 372.0), 0.30, 10.0), war=((248.0, 214.0), 0.21, 13.0),
                  lull=((1030.0, 214.0), 0.22, 8.0), mark=((640.0, 108.0), 0.50, 11.0))

    def c1_world(self, name, pts, src_c):
        """source px of a figure -> world, on a plane facing the final C1 camera."""
        (sx, sy), sc, d = self.C1_FIG[name]
        cf = Cam(*self.C1_CAM)
        x = sx + (pts[:, 0:1] - src_c[0]) * sc
        y = sy + (pts[:, 1:2] - src_c[1]) * sc
        return cf.p + d * (cf.fw + (x - 640.0) / F * cf.rt - (y - 360.0) / F * cf.up)

    def prep_const(self):
        rng = np.random.default_rng(5)
        figs = {}
        # the hands, exactly as M3 leaves them on screen (24.958)
        fr = np.clip(self.m3(24.958), 0, 255).astype(np.float32)
        lum = fr.mean(2)
        ink = ((lum < cv2.GaussianBlur(lum, (0, 0), 6) - 18) & (lum < 120)).astype(np.uint8)
        m = np.zeros_like(ink)
        cv2.rectangle(m, (0, 262), (168, 402), 1, -1)                                   # the passenger's hand
        cv2.rectangle(m, (560, 262), (1280, 500), 1, -1)                                # the hand on the platform, its sleeve
        m[:, 1118:1166] = 0                                                              # not the lamp post behind the sleeve
        ch = [c for c in skeleton_chains(ink * m, 8)]
        gap = np.array([[571.0, 198.0]])                                                 # where M3's spark is on its last frame
        figs['hands'] = dict(ch=ch, st=stars_along(ch, 46, rng), src_c=(640.0, 360.0), t0=24.90, t1=25.30, extra=gap)
        # the cradle (its layer's silhouette: basket, rockers, the hand on the rim) and the lamp
        al = (self.full('lullaby_cradle')[..., 3] > 0.5).astype(np.uint8)
        al[:, 1440:] = 0
        cs, hier = cv2.findContours(al, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        cs = sorted(cs, key=cv2.contourArea, reverse=True)[:3]
        ch = [cv2.approxPolyDP(c, 3.0, True)[:, 0, :].astype(np.float32) for c in cs]
        ch = [np.vstack([c, c[:1]]) for c in ch]
        shade = np.array([(148, 292), (260, 292), (296, 430), (110, 430), (148, 292)], np.float32)
        ball = np.array([(200 + 45 * np.cos(a), 475 + 42 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 13)], np.float32)
        ch += [shade, ball, np.array([(200, 430), (200, 433)], np.float32)]
        figs['lull'] = dict(ch=ch, st=stars_along(ch, 70, rng), src_c=(820.0, 540.0), t0=25.95, t1=26.6, extra=np.array([[203.0, 360.0]]))
        # the war room: the candle and its flame, the dish, the letter with its stroke, the helmet and its strap
        cand = np.array([(232, 383), (352, 383), (352, 672), (232, 672), (232, 383)], np.float32)
        flm = np.array([(289, 350), (279, 328), (282, 304), (289, 284), (296, 304), (299, 328), (289, 350)], np.float32)
        dish = np.array([(285 + 132 * np.cos(a), 690 + 30 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 15)], np.float32)
        letter = np.array([(392, 794), (513, 650), (1105, 657), (1180, 773), (392, 794)], np.float32)
        stroke = np.array([(554, 738), (578, 729), (602, 721), (626, 717), (650, 720), (674, 733), (698, 740), (740, 741),
                           (800, 735), (860, 726), (920, 718), (998, 716)], np.float32)
        helm = np.array([(1090, 650), (1118, 545), (1178, 470), (1258, 428), (1340, 416), (1422, 426), (1500, 462), (1560, 524),
                         (1598, 596), (1655, 700), (1380, 690), (1090, 650)], np.float32)
        strap = np.array([(1185, 652), (1250, 752), (1340, 800), (1495, 842)], np.float32)
        ch = [cand, flm, dish, letter, stroke, helm, strap]
        figs['war'] = dict(ch=ch, st=stars_along(ch, 85, rng), src_c=(945.0, 565.0), t0=25.75, t1=26.45, extra=np.array([[289.0, 315.0]]))
        # the letter's mark: the stroke from its dot, the spiral, the full stop (the hub)
        pg = self.page.mean(2)
        mk = (pg < 0.55).astype(np.uint8)
        mk[:335] = 0
        mk[440:] = 0
        mk[:, :684] = 0
        mk[:, 1212:] = 0                                                                 # the full stop is the hub star itself
        ch = skeleton_chains(mk, 6)
        figs['mark'] = dict(ch=ch, st=stars_along(ch, 60, rng), src_c=(960.0, 385.0), t0=26.25, t1=26.85,
                            extra=np.array([[1226.6, 408.5]]))
        for k, fg in figs.items():
            fg['w_ch'] = [self.c1_world(k, c, fg['src_c']) for c in fg['ch']]
            fg['w_st'] = self.c1_world(k, fg['st'], fg['src_c']) if len(fg['st']) else np.zeros((0, 3))
            fg['w_ex'] = self.c1_world(k, fg['extra'], fg['src_c'])
            fg['L'] = [float(np.linalg.norm(np.diff(c, axis=0), axis=1).sum()) for c in fg['ch']]
        # the field: the letter's handwriting, word by word, scattered deep behind
        hw = (pg < 0.55).astype(np.uint8)
        hw[:210] = 0
        hw[450:] = 0
        hw[335:, 684:] = 0
        words = []
        n_, lab, stt, _ = cv2.connectedComponentsWithStats(cv2.dilate(hw, np.ones((9, 15), np.uint8)), connectivity=8)
        for i in range(1, n_):
            x, y, w, h, area = stt[i]
            if w < 25:
                continue
            sub = hw * (lab == i)
            cc = skeleton_chains(sub, 5)
            if cc:
                words.append((cc, np.array([x + w / 2, y + h / 2], np.float32), w))
        cf = Cam(*self.C1_CAM)

        def word_pts(cc, c0, w, size):                                                    # a word's chains, centred, in units of `size` per width
            return [(c - c0) * (size / w) for c in cc]
        # middle: each memory sheds a few words of the letter, which drift from it (toward the field behind)
        mids = []
        for name in ('hands', 'war', 'lull', 'mark'):
            ctr = figs[name]['w_ch'][0].mean(0)
            for j in range(9):
                cc, c0, w = words[int(rng.integers(len(words)))]
                off = cf.rt * rng.uniform(-1.4, 1.4) + cf.up * rng.uniform(-0.8, 0.8) + cf.fw * rng.uniform(-0.5, 1.8)
                ang = rng.uniform(-0.6, 0.6)
                R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]], np.float32)
                pts = [(q @ R.T) for q in word_pts(cc, c0, w, rng.uniform(0.25, 0.45))]
                mids.append(dict(base=ctr + off, pts=pts, drift=cf.fw * rng.uniform(0.6, 1.4) + off * 0.15,
                                 t0=figs[name]['t1'] - 0.1 + rng.uniform(0, 0.5)))
        # far: the letter's handwriting along the arms of one vast spiral (the letter's own mark, enlarged), on a disk
        # leaning back behind the hub, ~150 units deep and ~300 across: it opens from its centre outward
        hub_dir = cf.fw + (640.0 - 640.0) / F * cf.rt - (150.0 - 360.0) / F * cf.up
        C = cf.p + 150.0 * hub_dir / np.linalg.norm(hub_dir)
        nrm = rot_axis(-cf.fw, cf.rt, -np.radians(64))
        e1 = cf.rt.copy()
        e2 = np.cross(nrm, e1)
        e2 /= np.linalg.norm(e2)
        far = []
        bsp = 0.21
        for arm in range(3):
            th = 0.9
            while True:
                r = 7.0 * np.exp(bsp * th)
                if r > 150:
                    break
                cc, c0, w = words[int(rng.integers(len(words)))]
                size = 0.10 * r + 1.5                                                    # word width, world units
                a0 = th + arm * 2 * np.pi / 3
                tng = np.array([-np.sin(a0) + bsp * np.cos(a0), np.cos(a0) + bsp * np.sin(a0)])
                tng /= np.linalg.norm(tng)
                rad = np.array([np.cos(a0), np.sin(a0)])
                P = r * rad + rng.normal(0, 0.04 * r, 2)
                loc = [P[None, :] + q[:, 0:1] * (size / w) * tng[None, :] - q[:, 1:2] * (size / w) * rad[None, :]
                       for q in [c - c0 for c in cc]]
                far.append(dict(loc=loc, r=r, t0=26.15 + 1.75 * (r / 150.0) ** 0.8))
                th += (size * 1.25) / (r * np.sqrt(1 + bsp * bsp))
        # near (m27): three torn pieces of the letter itself fly out of the constellation and past the lens, to the side,
        # while the camera pulls back; each leaves the frame by 27.4 s, so the reveal of the observers is clean
        near = []
        cand = sorted([f_ for f_ in self.frags if not f_['hero'] and 120 < f_['box'][2] - f_['box'][0] < 300],
                      key=lambda f_: -f_['text'])
        for j, (t0, sx, sy, d0, vz, vx, vy) in enumerate(((25.70, 470, 300, 6.0, 7.0, -1.2, 0.4), (26.05, 820, 250, 6.5, 7.0, 1.3, 0.5),
                                                          (26.40, 560, 430, 6.0, 7.5, -0.9, 1.1))):
            c0 = self.c1_cam(t0)
            W0 = c0.p + d0 * (c0.fw + (sx - 640.0) / F * c0.rt - (sy - 360.0) / F * c0.up)
            near.append(dict(fr=cand[j * 3], W0=W0, vel=-c0.fw * vz + c0.rt * vx - c0.up * vy, t0=t0,
                             axis=rng.normal(0, 1, 3), a0=rng.uniform(-0.4, 0.4), w=rng.uniform(1.2, 2.0) * rng.choice([-1, 1])))
        field = dict(mids=mids, far=far, near=near, C=C, e1=e1, e2=e2)
        self.c1 = dict(figs=figs, field=field)

    def c1_observers(self, img, gu):
        """A and B from behind on the parapet, small under the constellation. Scale: head-to-seat 160 px (KV1's figures in
        C1 v4: 145 px). Both hands rest on the stone at the parapet's top line (A's at candidate y 1075, B's at 1099); A on
        the left, B on the right as in KV1. Night grade: cool fill, a faint warm light from above (the constellation)."""
        if not hasattr(self, '_obs'):
            lays = []
            for nm, xc, hand_y, top in (('Girl_A_rear_seated_candidate_v1', 548.0, 1075.0, 70.0),
                                        ('Girl_B_rear_seated_candidate_v1', 730.0, 1099.0, 229.0)):
                src, a = load_candidate(nm)
                hh = src.shape[0]
                yy = np.arange(hh, dtype=np.float32)[:, None, None]
                up = np.clip(1 - (yy - top) / 500.0, 0, 1)                               # light from above, on heads and shoulders
                g = src * (np.array([0.50, 0.50, 0.56], np.float32) + up * np.array([0.05, 0.10, 0.16], np.float32))
                lays.append((g * a[..., None], a, xc, hand_y))
            self._obs = lays
        seat = 690.0
        k = 1.22 - 0.22 * gu                                                             # the pull-back: nearer, larger, lower
        dy = 300.0 * (1 - gu) ** 2
        # the parapet: dark stone with a cool top edge, across the frame under them
        ledge = np.zeros((H, W), np.float32)
        y_top = seat + 6 * k + dy
        yy = np.arange(H, dtype=np.float32)[:, None]
        ledge = np.clip(yy - y_top + 1, 0, 1) * np.ones((1, W), np.float32)
        stone = np.array([30, 26, 26], np.float32) + np.exp(-((yy - y_top - 2) / 2.0) ** 2)[..., None] * np.array([40, 34, 30], np.float32)
        img = img * (1 - ledge[..., None]) + stone * ledge[..., None]
        for pre, a, xc, hand_y in self._obs:                                           # contact shadows on the stone first
            sc = 0.16 * k
            tx = 640 + (xc - 640) * k - 512 * sc
            ty = seat + dy - hand_y * sc + 6 * k
            M = np.float32([[sc, 0, tx], [0, sc, ty]])
            ga = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_AREA)
            band = ga[int(min(H - 1, max(0, y_top - 26))):int(min(H, max(1, y_top)))].max(0)   # what touches the stone
            sh = np.zeros((H, W), np.float32)
            y0s = int(min(H - 1, max(0, y_top)))
            sh[y0s:min(H, y0s + 10)] = band[None, :]
            sh = cv2.GaussianBlur(sh, (0, 0), 5.0)
            img = img * (1 - 0.55 * sh[..., None])
        for pre, a, xc, hand_y in self._obs:
            sc = 0.16 * k
            tx = 640 + (xc - 640) * k - 512 * sc
            ty = seat + dy - hand_y * sc + 6 * k
            M = np.float32([[sc, 0, tx], [0, sc, ty]])
            ga = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_AREA)[..., None]
            gp = cv2.warpAffine(pre, M, (W, H), flags=cv2.INTER_AREA)
            img = img * (1 - ga) + gp
        return img

    def c1_cam(self, t):
        """a dolly straight back from the hands (filling the frame as M3 left them) to the whole constellation."""
        (sx, sy), sc, d = self.C1_FIG['hands']
        cf = Cam(*self.C1_CAM)
        ps = cf.p + (1 - sc) * d * cf.fw + d / F * ((sx - 640.0) * cf.rt - (sy - 360.0) * cf.up)
        e = ease(25.55, 27.75, t)
        r = sc ** (1 - e) * (1 + 0.035 * ease(27.6, 28.6, t))                            # distance grows evenly, then a slow drift
        pos = cf.p + (1 - r) / (1 - sc) * (ps - cf.p)
        return Cam(pos, pos + cf.fw)

    def constellations(self, t):
        """"became constellations in a mind with no sky": the parting hands of M3, traced in light on the very pixels where
        they were; the spark leaves the gap. The view pulls back: the cradle and its lamp, the candle, the helmet and the
        letter appear, the spark becomes the full stop of the letter's mark, and the mark's threads tie the memories to it.
        Behind them, the handwriting of the letter in pieces, deep into the dark. Last, the two of them, small, from behind,
        under all of it."""
        if not hasattr(self, 'c1'):
            self.prep_const()
        cam = self.c1_cam(t)
        img = night_backdrop(11, top=(10, 5, 3), bottom=(16, 9, 6))
        lines = np.zeros((H, W), np.float32)
        col = np.array([120, 190, 245], np.float32)
        fg = self.c1['figs']

        def poly(c, k, frac=1.0):
            xy, z = cam.project(c)
            if (z < 0.2).any() or k <= 0:
                return
            if frac < 1:
                seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
                Lc = np.concatenate([[0], np.cumsum(seg)])
                n = int(np.searchsorted(Lc, Lc[-1] * frac))
                xy = xy[:max(n, 1) + 1]
            if len(xy) < 2:
                return
            cv2.polylines(lines, [np.int32(xy * 4)], False, float(k), 1, cv2.LINE_AA, shift=2)
        fld = self.c1['field']
        # far: the spiral of handwriting, revealed from its centre outward, turning slowly
        far_l = np.zeros((H, W), np.float32)
        rot = 0.045 * (t - 25.0)
        cr, sr = np.cos(rot), np.sin(rot)
        for f in fld['far']:
            u = ease(f['t0'], f['t0'] + 0.45, t)
            if u <= 0:
                continue
            k = u * 0.40 * (0.45 + 0.55 * np.exp(-f['r'] / 70.0))
            for q in f['loc']:
                x, y = q[:, 0] * cr - q[:, 1] * sr, q[:, 0] * sr + q[:, 1] * cr
                P3 = fld['C'][None, :] + x[:, None] * fld['e1'][None, :] + y[:, None] * fld['e2'][None, :]
                xy, z = cam.project(P3)
                if (z < 0.2).any() or len(xy) < 2:
                    continue
                cv2.polylines(far_l, [np.int32(xy * 4)], False, float(k), 1, cv2.LINE_AA, shift=2)
        img = img + (far_l + 0.6 * cv2.GaussianBlur(far_l, (0, 0), 2.5))[..., None] * np.array([110, 165, 220], np.float32)
        # middle: words drifting off each memory
        for m in fld['mids']:
            u = ease(m['t0'], m['t0'] + 0.5, t)
            if u <= 0:
                continue
            base = m['base'] + m['drift'] * max(0.0, t - m['t0'])
            for q in m['pts']:
                P3 = base[None, :] + q[:, 0:1] * cam.rt[None, :] - q[:, 1:2] * cam.up[None, :]
                poly(P3, 0.42 * u)
        # the figures, each drawn along its lines as it comes in
        for name, fgr in fg.items():
            u = ease(fgr['t0'], fgr['t1'], t)
            if u <= 0:
                continue
            Ltot = sum(fgr['L'])
            acc = 0.0
            kb = dict(hands=1.0 - 0.30 * ease(26.3, 27.3, t), war=0.80, lull=0.72, mark=0.95)[name]   # not all equally bright
            for c, Lc in zip(fgr['w_ch'], fgr['L']):
                f = float(np.clip((u * Ltot - acc) / max(Lc, 1e-3), 0, 1))
                acc += Lc
                poly(c, 0.85 * kb, f)
        # threads: from the full stop to the flame, the lamp and the gap of the hands
        hub = fg['mark']['w_ex'][0]
        thr = ease(26.75, 27.35, t)
        if thr > 0:
            for k in ('war', 'lull', 'hands'):
                a_, b_ = hub, fg[k]['w_ex'][0]
                pts = np.array([a_ + (b_ - a_) * s_ + np.array([0, 0.25 * np.sin(np.pi * s_), 0]) for s_ in np.linspace(0, 1, 40)])
                poly(pts, 0.40, thr)
        glow_l = cv2.GaussianBlur(lines, (0, 0), 2.2)
        img = img + (lines[..., None] + 0.55 * glow_l[..., None]) * col
        # stars: on the figures' lines, brighter at their key points
        for name, fgr in fg.items():
            u = ease(fgr['t0'], fgr['t1'], t)
            if u <= 0 or not len(fgr['w_st']):
                continue
            xy, z = cam.project(fgr['w_st'])
            n_on = int(len(xy) * u)
            for j in range(n_on):
                if z[j] > 0.2:
                    OI.dot(img, xy[j], (0.8, 1.1, 1.5, 0.9, 1.9)[j % 5], 0.75 + 0.2 * np.sin(t * 2.1 + j * 1.3))
        for k in ('war', 'lull'):
            u = ease(fg[k]['t1'] - 0.2, fg[k]['t1'] + 0.2, t)
            if u > 0:
                q = cam.project(fg[k]['w_ex'])[0][0]
                img = glow(img, q, 0.05, 0.7 * u)
                OI.dot(img, q, 2.0, u)
        # the spark: in the hands' gap, then it rises to become the full stop of the letter's mark
        sp = ease(25.65, 26.45, t)
        a_, b_ = fg['hands']['w_ex'][0], hub
        P_ = a_ + (b_ - a_) * sp + np.array([0.0, 0.9, 0.0]) * 4 * sp * (1 - sp)
        q = cam.project(P_)[0][0]
        img = glow(img, q, 0.07 + 0.03 * sp, 1.0)
        OI.dot(img, q, 1.7 + 0.8 * sp, 1.0)
        # near (m27): backlit letter paper, not dark blocks. The constellation is behind the pieces, so the paper glows warm
        # and translucent with the handwriting dark in it; the torn fibre rim catches the light; a thin darker edge on the
        # lower side gives the sheet its thickness. Little defocus, so the torn edges stay readable.
        focus = float(np.linalg.norm(fg['hands']['w_ch'][0].mean(0) - cam.p))
        for nr in self.c1['field']['near']:
            if t < nr['t0']:
                continue
            fr = nr['fr']
            bx0, by0, bx1, by1 = fr['box']
            pos = nr['W0'] + nr['vel'] * (t - nr['t0'])
            if (pos - cam.p) @ cam.fw < 0.3:
                continue
            ang = nr['a0'] + nr['w'] * (t - nr['t0'])
            u_ = rot_axis(cam.rt, nr['axis'], ang)
            v_ = rot_axis(cam.up, nr['axis'], ang)
            w_, h_ = (bx1 - bx0) / self.PU * 0.9, (by1 - by0) / self.PU * 0.9
            corners = card_corners(pos, u_, v_, w_, h_)
            xy, zc_ = cam.project(corners)
            if (zc_ < 0.3).any() or xy[:, 0].max() < -40 or xy[:, 0].min() > W + 40 or xy[:, 1].max() < -40 or xy[:, 1].min() > H + 40:
                continue
            al = fr['alpha']
            pa = self.page[by0:by1, bx0:bx1]                                             # the letter's own cream paper and ink
            facing = abs(float(np.cross(u_, v_) @ cam.fw))                                # thin paper seen edge-on lets less light through
            hh_, ww_ = al.shape
            grad = np.linspace(1.12, 0.82, hh_, dtype=np.float32)[:, None, None]         # brighter toward the lit side
            body = pa * np.array([0.40, 0.50, 0.58], np.float32) * grad * (0.70 + 0.30 * facing)
            hard = (al > 0.5).astype(np.uint8)
            rim = cv2.morphologyEx(hard, cv2.MORPH_GRADIENT, np.ones((4, 4), np.uint8)).astype(np.float32)
            low = np.zeros_like(rim)
            low[3:] = np.clip(hard[3:].astype(np.float32) - hard[:-3], 0, 1)             # the lower edge: the sheet's thickness
            col = body * (1 - rim[..., None]) + rim[..., None] * np.array([0.80, 0.90, 0.98], np.float32)
            col = col * (1 - 0.6 * low[..., None])
            tex = np.dstack([col + fr['fibre'][..., None] * 0.04, al * 0.88])
            img, _ = put_card(img, cam, corners, tex, focus=focus, aperture=0.12)
        # the two of them, small, from behind, on the parapet (Message 23 rear candidates; they replace KV1's old cut-outs,
        # whose mattes carried KV1's sky around the horns): they enter the bottom of the frame as the view pulls back
        gu = ease(26.85, 27.95, t)
        if gu > 0:
            img = self.c1_observers(img, gu)
        return img

    # -- B's half: the paper town
    def town_scene(self, t, cam, up, key, lights=None, focus=1.5, haze=None, stars=0.0, sun_x=None, cold=0.0, age=None, real=0.0, sky=None,
                   road=1.0):
        """the pop-up page. up[group]: 0 lying flat toward the viewer .. 1 standing .. 2 laid back flat behind its fold
        (going back in time folds a group backward, like closing a spread, not toward the viewer as it rose).
        key: warm light on the paper (0 night .. 1 dusk); lights[group]: fraction of windows lit; age[group]: the paper
        yellows before it folds away."""
        img = night_backdrop(6, top=(30, 16, 10), bottom=(46, 28, 20))
        if sky is not None:                                                            # the plate's own night sky (D4's end)
            img = img * (1 - sky[1]) + sky[0] * sky[1]
        if stars > 0:
            rng = np.random.default_rng(14)
            for k in range(70):
                OI.dot(img, (rng.uniform(0, W), rng.uniform(0, 330)), 0.7 + 0.5 * (k % 7 == 0), stars * rng.uniform(0.3, 0.9))
        night = np.array([0.40, 0.38, 0.48], np.float32)
        warm = np.array([0.60, 0.84, 1.08], np.float32)
        tint = night * (1 - key) + warm * key
        tint = tint * (1 - cold) + np.array([0.46, 0.34, 0.28], np.float32) * cold      # moonlight, cold
        g = self.ground.copy()
        if STAGE == 'v9' and road < 1:                                                   # the road goes with the town
            g = g * road + self.ground_noroad * (1 - road)
        g[..., :3] *= tint * 0.92
        if STAGE == 'v9' and real > 0:                                                   # the page becomes the painted ground too
            g[..., :3] = g[..., :3] * (1 - real) + self.ground_real() * np.float32(0.93) * real
        if sun_x is not None:                                                          # the light crossing the page
            xx = np.linspace(-3.3, 3.3, g.shape[1], dtype=np.float32)[None, :]
            g[..., :3] *= (1 + 0.45 * np.exp(-((xx - sun_x) / 0.9) ** 2))[..., None]
        img, _ = put_card(img, cam, card_corners((0, 0, 0.965), (1, 0, 0), (0, 0, 1), 6.6, 2.87), g, focus=focus,
                          aperture=0.35, dof_map=True)
        # every standing piece, far to near
        items = []
        for name in ('hill', 'village'):
            L = self.layers[name]
            items.append(dict(tex=L['tex'], wins=L['wins'], group=name, base=np.array([0.0, 0.0, L['z']]),
                              u=np.array([1.0, 0, 0]), w=L['w'], h=L['h'], order=0))
        items += self.cards
        items.sort(key=lambda it: -float((it['base'] - cam.p) @ cam.fw))                 # far to near: nearer pieces cover
        glows = []
        drawn = []
        for it in items:
            grp = it['group']
            key_g = 'town' if grp in ('street', 'near') else grp
            st = float(up.get(grp, up.get(key_g, 1.0)))
            if grp == 'street':                                                         # the street rises/folds a little after the town, house by house
                st = float(np.clip(st * 1.25 - 0.06 * it['order'], 0, 1)) if st <= 1 else float(np.clip(1 + (st - 1) * 1.25 - 0.06 * (4 - it['order']), 1, 2))
            if st < 0.01 or st > 1.99:
                continue
            u = it['u'] / np.linalg.norm(it['u'])
            nrm = np.cross(u, [0.0, 1.0, 0.0])
            if (cam.p - it['base']) @ nrm < 0:                                           # the side facing the camera
                nrm = -nrm
            ang = (np.pi / 2) * smooth(st) if st <= 1 else np.pi / 2 + (np.pi / 2) * smooth(st - 1)
            v = np.array([0.0, 1.0, 0.0]) * np.sin(ang) + nrm * np.cos(ang)               # flat toward the viewer at 0, behind at pi
            corners = card_corners(it['base'] + v * it['h'] / 2, u, v, it['w'], it['h'])
            xy, z = cam.project(corners)
            if (z < 0.05).any():
                continue
            if xy[1, 0] < xy[0, 0]:                                                      # read left to right from this camera
                u = -u
                corners = card_corners(it['base'] + v * it['h'] / 2, u, v, it['w'], it['h'])
            tex = it['tex'].copy()
            hz = (haze or {}).get(grp, 0.0)
            ag = (age or {}).get(key_g, 0.0)
            tt = tint * (1 - 0.35 * ag) + np.array([0.30, 0.52, 0.72], np.float32) * 0.35 * ag   # yellowed with age
            tex[..., :3] = tex[..., :3] * tt * (1 - hz) + np.array([0.20, 0.14, 0.11], np.float32) * hz
            if grp == 'hill' and real > 0:                                             # the print becomes the place
                tex[..., :3] = tex[..., :3] * (1 - real) + self.hill_real[..., :3] * np.float32(0.93) * real
            hh = tex.shape[0]
            ao = 0.72 + 0.28 * smooth(np.arange(hh, 0, -1, dtype=np.float32) / 45.0)       # darker where it meets the page
            if STAGE == 'v9' and grp == 'hill':                                           # v9: the hill print continues into the page
                ao = 0.94 + 0.06 * ao
            tex[..., :3] *= ao[:, None, None]
            if sun_x is not None:
                xx = np.linspace(-it['w'] / 2, it['w'] / 2, tex.shape[1], dtype=np.float32)[None, :]
                tex[..., :3] *= (1 + 0.40 * np.exp(-((xx + it['base'][0] - sun_x) / 0.9) ** 2))[..., None]
            # the fold-root shadow on the page, behind the piece, and a cast shadow while the light crosses
            if 0.2 < ang < np.pi - 0.2:
                prof = it['tex'][-max(4, hh // 6):, :, 3].max(0)
                root = np.zeros((24, tex.shape[1], 4), np.float32)
                root[..., 3] = prof[None, :] * np.exp(-np.arange(24, dtype=np.float32)[::-1] / 7.0)[:, None] * 0.55 * np.sin(ang)
                img, _ = put_card(img, cam, card_corners(it['base'] - nrm * 0.035, u, -nrm, it['w'], 0.07), root, extra_blur=1.5)
                if sun_x is not None and grp in ('town', 'village', 'hill'):
                    sh = np.zeros_like(tex)
                    sh[..., 3] = it['tex'][..., 3] * 0.35
                    dsh = -nrm + np.array([-0.35 * np.tanh(sun_x), 0, 0])
                    dsh /= np.linalg.norm(dsh)
                    img, _ = put_card(img, cam, card_corners(it['base'] + dsh * it['h'] * 0.3, u, dsh, it['w'], it['h'] * 0.6), sh,
                                      extra_blur=3.0)
            if grp != 'hill' and 0.15 < ang < np.pi - 0.15:                                # a paper brace holds it up from behind
                ta = it['tex'][..., 3]
                for xo in (-0.32, 0.32):
                    col = ta[:, int((0.5 + xo) * (ta.shape[1] - 1))]                     # the silhouette's height at this brace
                    if col.max() < 0.5:
                        continue
                    lh = it['h'] * (1 - np.argmax(col > 0.5) / ta.shape[0])
                    top = it['base'] + v * lh * 0.55 + u * xo * it['w']
                    bot = it['base'] - nrm * lh * 0.30 + u * xo * it['w']
                    if top[1] < 0.01:
                        continue
                    bw = 0.03
                    br = np.array([top - u * bw / 2, top + u * bw / 2, bot + u * bw / 2, bot - u * bw / 2])
                    btex = np.ones((8, 8, 4), np.float32)
                    btex[..., :3] = tint * np.array([0.62, 0.70, 0.76], np.float32)
                    img, _ = put_card(img, cam, br, btex, focus=focus, aperture=0.35)
            if grp in ('town', 'street') and 0.12 < ang < np.pi - 0.12:
                # a pop-up box, not a flat card: a glued tab on the page in front of the fold, and the side wall at the end
                # that faces the camera, folding with the card (its depth goes with sin(ang))
                tab = np.ones((6, 6, 4), np.float32)
                tab[..., :3] = tint * np.array([0.70, 0.78, 0.84], np.float32)
                img, _ = put_card(img, cam, card_corners(it['base'] + nrm * 0.025 + np.array([0, 0.001, 0]), u, nrm, it['w'], 0.05), tab,
                                  focus=focus, aperture=0.35)
                end = 1.0 if (cam.p - it['base']) @ u > 0 else -1.0
                ta = it['tex'][..., 3]
                cols = np.nonzero(ta.max(0) > 0.5)[0]
                if len(cols):
                    ci = cols[-1] if end > 0 else cols[0]
                    hs = it['h'] * (1 - np.argmax(ta[:, ci] > 0.5) / ta.shape[0])
                    xe = (ci / (ta.shape[1] - 1) - 0.5) * it['w']
                    dd = 0.11 * np.sin(ang)
                    e0 = it['base'] + u * xe
                    side = np.ones((24, 8, 4), np.float32)
                    side[..., :3] = tint * np.array([0.52, 0.58, 0.64], np.float32) * (1 - 0.25 * (age or {}).get(key_g, 0.0))
                    side[:, :1, :3] = INK
                    side[:, -1:, :3] = INK
                    img, _ = put_card(img, cam, card_corners(e0 - nrm * dd / 2 + v * hs / 2, -nrm, v, dd, hs), side,
                                      focus=focus, aperture=0.35)
            fr = (lights or {}).get(grp, (lights or {}).get(key_g, 0.0))
            if fr > 0 and it['wins']:
                rng = np.random.default_rng(len(it['wins']) + 7 * it['order'])
                order = rng.permutation(len(it['wins']))
                tw_ = tex.shape[1]
                for j in order[:int(round(fr * len(order)))]:
                    wx, wy = it['wins'][j]
                    cv2.rectangle(tex, (int(wx - 7), int(wy - 10)), (int(wx + 7), int(wy + 10)), (0.42, 0.78, 1.05, 1.0), -1)
                    glows.append(it['base'] + v * it['h'] * (1 - wy / hh) + u * (wx / tw_ - 0.5) * it['w'] - nrm * 0.01)
            img, zc = put_card(img, cam, corners, tex, focus=focus, aperture=0.35 if grp != 'near' else 0.6, dof_map=grp != 'near')
            drawn.append(grp)
        if glows:
            xy, z = cam.project(np.array(glows))
            for q, zz in zip(xy, z):
                if zz > 0.05 and -20 < q[0] < W + 20 and -20 < q[1] < H + 20:
                    OI.dot(img, q, 1.4, 0.45)
        return img

    def d1(self, t):
        """KV4: B, close, looking down; below her the town pops up out of the page ("depth"), and a day passes over it
        until the windows light ("time"). B is always in front: a solid matte, and her shadow falls on the page."""
        u = ease(28.583, 30.458, t)
        cam = Cam((-0.70 + 0.10 * u, 1.00, -0.55), (-0.32 + 0.06 * u, 0.12, 0.95))
        pop = {'hill': ease(28.65, 29.05, t), 'village': ease(28.85, 29.20, t), 'town': ease(29.0, 29.40, t),
               'street': ease(29.15, 29.75, t), 'near': ease(29.25, 29.65, t)}
        sun = ease(29.56, 30.15, t)
        key = 0.75 * (1 - ease(30.0, 30.35, t))
        lights = {'town': ease(30.0, 30.40, t), 'street': ease(30.05, 30.42, t), 'village': ease(30.1, 30.45, t)}
        img = self.town_scene(t, cam, pop, key, lights, focus=1.55, haze={'hill': 0.30, 'village': 0.12},
                              sun_x=(-2.0 + 4.0 * sun) if 29.5 < t < 30.2 else None)
        z = 1.0 + 0.02 * u
        M = np.float32([[z, 0, 1280 * (1 - z) * 0.85], [0, z, 0]])
        fa = cv2.warpAffine(self.kv4a, M, (W, H))
        fg = cv2.warpAffine(self.kv4_pre, M, (W, H))
        # v6: she follows the street as it unfolds: her eyes lead (29.25-29.55), her chin lowers 1.2 deg about the neck
        # (29.35-29.85), toward the street below-left. A local warp of the head only; nothing else moves.
        if not hasattr(self, '_d1w'):
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            head = np.exp(-((xx - 745) ** 2 + (yy - 270) ** 2) / (2 * 190.0 ** 2)) * (1 - smooth((yy - 470) / 80.0))
            eye = np.exp(-((xx - 735) ** 2 + (yy - 265) ** 2) / (2 * 7.0 ** 2))
            town = np.exp(-((xx - 430) ** 2 + (yy - 640) ** 2) / (2 * 380.0 ** 2))        # the near side, toward the town
            self._d1w = (xx, yy, head, eye, town)
        xx, yy, head, eye, town = self._d1w
        th = np.radians(1.2) * ease(29.35, 29.85, t)
        ge = ease(29.25, 29.55, t)
        px, py = 830.0, 470.0
        rx, ry = xx - px, yy - py
        dx = head * (rx * np.cos(th) + ry * np.sin(th) - rx) - eye * 1.2 * ge
        dy = head * (-rx * np.sin(th) + ry * np.cos(th) - ry) + eye * 1.4 * ge
        mx, my = (xx - dx).astype(np.float32), (yy - dy).astype(np.float32)
        fa = cv2.remap(fa, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        fg = cv2.remap(fg, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        # the town's windows light her near side a little as they come on
        wl = 0.5 * lights['town'] + 0.3 * lights['street'] + 0.2 * lights['village']
        fg = fg * (1 + (town * 0.22 * wl)[..., None] * np.array([0.55, 0.85, 1.15], np.float32))
        # her shadow on what lies behind her: soft, offset away from the warm light at lower left
        sh = cv2.GaussianBlur(cv2.warpAffine(fa, np.float32([[1, 0, 38], [0, 1, -22]]), (W, H)), (0, 0), 22)
        img = img * (1 - 0.32 * sh[..., None])
        return img * (1 - fa[..., None]) + fg

    def d3b(self, t):
        """"that were learning to beat": B (B3, eyes closed, voice-over) where she sits: the stone parapet runs past at
        her left toward A, the night Earth beyond (both KV5a's own, out of focus). The light comes from A's palm, off frame
        below-left: warm on her near cheek, jaw and front hair, the far side cool and darker. She takes one slow breath;
        the hair hanging in front follows a little later. Nothing turns; no lip motion."""
        if not hasattr(self, '_d3b'):
            k = cv2.imread(os.path.join(PLATES, 'KV5a.png')).astype(np.float32)
            bg = cv2.resize(k[1000:1731, 1600:2900], (W, H), interpolation=cv2.INTER_AREA)   # the parapet and the Earth to B's right
            bg = cv2.GaussianBlur(bg, (0, 0), 4.5) * 0.80
            src, a = self.B3
            hh, ww = a.shape
            yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
            Lsrc = (-120.0, 1150.0)                                                      # A's palm, off frame below-left (B3 px)
            d2 = (xx - Lsrc[0]) ** 2 + (yy - Lsrc[1]) ** 2
            warm = np.clip(np.exp(-d2 / 640.0 ** 2) * 1.35, 0, 1)                        # near cheek, jaw, front hair
            warm *= np.clip((760.0 - xx) / 420.0, 0.15, 1.0)                              # the back of her head turns away
            cool = np.array([0.58, 0.46, 0.42], np.float32)                             # far side: night, bluish (BGR)
            hot = np.array([0.74, 1.00, 1.22], np.float32)
            edge = (a > 0.05) & (cv2.erode((a > 0.5).astype(np.uint8), np.ones((9, 9), np.uint8)) == 0)
            rim = cv2.GaussianBlur(edge.astype(np.float32), (0, 0), 2.0) * np.clip((560 - xx) / 300.0, 0, 1) * warm
            bgY, bgX = np.mgrid[0:H, 0:W].astype(np.float32)
            self._d3b = dict(bg=bg, src=src, a=a, warm=warm, cool=cool, hot=hot, rim=rim, xx=bgX, yy=bgY)
        L = self._d3b
        xx, yy = L['xx'], L['yy']
        lift = ease(34.25, 35.30, t)                                                     # the warmth grows a little, once
        img = glow(L['bg'].copy(), (-80.0, 820.0), 1.7, 0.26 + 0.10 * lift)              # A's light on the stone, off frame
        br = 2.6 * ease(34.35, 35.15, t) - 1.6 * ease(35.30, 35.92, t)                    # one slow breath (px)
        br_h = 2.6 * ease(34.55, 35.40, t) - 1.6 * ease(35.50, 35.92, t)                  # the hanging hair, later
        kw = (0.75 + 0.25 * lift + 0.04 * br / 2.6) * L['warm']
        lit = L['src'] * (L['cool'] * (1 - kw[..., None]) + L['hot'] * kw[..., None])
        lit = lit + L['rim'][..., None] * np.array([40, 95, 150], np.float32) * (0.6 + 0.4 * lift)
        src, a = L['src'], L['a']
        h_px = 1250 + 30 * (t - 34.1)
        cx = 700 - 10 * (t - 34.1)
        s_ = h_px / src.shape[0]
        M = np.float32([[s_, 0, cx - src.shape[1] * s_ / 2], [0, s_, 400 - src.shape[0] * s_ / 2]])
        pre = cv2.warpAffine(np.clip(lit, 0, 255) * a[..., None], M, (W, H), flags=cv2.INTER_AREA)
        al = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_AREA)
        neck = s_ * 860 + M[1, 2]                                                        # her neck (B3 px 860), on screen
        face_x = s_ * 300 + M[0, 2]                                                      # her profile line, on screen
        chest = smooth((yy - neck + 60) / 160.0)                                         # the chest and shoulders rise
        hang = smooth((yy - neck + 40) / 120.0) * (1 - smooth((xx - face_x - 60) / 60.0))   # the hair hanging in front
        dy = br * (0.45 + 0.55 * chest) * (1 - hang) + br_h * (0.45 + 0.55 * chest) * hang
        mx, my = xx, (yy + dy).astype(np.float32)
        pre = cv2.remap(pre, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        al = cv2.remap(al, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return img * (1 - al[..., None]) + pre

    def town_cam(self, t):
        return Cam((0.0, 1.05, -1.25), (0.05, 0.22, 1.25))

    def d4_cam(self, t):
        """from the pop-up view down onto the page, the gaze lifts to the hill card and squares to it, so that the card
        fills the frame exactly as the plate does in D6's last window."""
        k = ease(38.0, 38.95, t)
        p0, g0 = np.array([0.0, 1.05, -1.25]), np.array([0.05, 0.22, 1.25])
        x0, y0, w = self.hill_view(self.HILL_FINAL_T)
        s_ = W / w
        D = F * (self.HILL_UNITS / 1672.0) / s_
        cy = ((941.0 - y0) * s_ - 360.0) * D / F
        cx = -((836.0 - x0) * s_ - 640.0) * D / F
        zc = self.TOWN['hill'][0] - D
        p1, g1 = np.array([cx, cy, zc]), np.array([cx, cy, zc + 3.0])
        return Cam(p0 * (1 - k) + p1 * k, g0 * (1 - k) + g1 * k)

    def hill_sky(self, cam):
        """the plate's own night sky (the land filled with the sky just above it), as seen from cam (rotation only)."""
        if not hasattr(self, '_skyplate'):
            pl = self.plate5('first_fire_hill_wide_v1').copy()
            hh, ww = pl.shape[:2]
            sky = np.arange(hh)[:, None] < (self.hill_skyline[None, :] - 6)
            row = np.array([np.median(pl[y][sky[y]], 0) if sky[y].sum() > 40 else np.full(3, np.nan) for y in range(hh)])
            last = np.where(~np.isnan(row[:, 0]))[0][-1]
            row[last + 1:] = row[last]                                                   # below the lowest sky: its colour, held
            fill = np.repeat(row[:, None, :], ww, 1).astype(np.float32)
            self._skyplate = np.where(sky[..., None], pl, fill)
        x0, y0, w = self.hill_view(self.HILL_FINAL_T)
        img = self.to_screen(self._skyplate, x0, y0, w)
        pitch = np.arcsin(-cam.fw[1])                                                    # looking down: the sky slides up
        yaw = np.arctan2(cam.fw[0], cam.fw[2])
        M = np.float32([[1, 0, -F * np.tan(yaw)], [0, 1, -F * np.tan(pitch)]])
        return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)

    def d4(self, t):
        """"The cosmos was silent, the cosmos was still": the same page at night, read backward through time. The
        windows go dark one by one, the paper yellows, and the town folds back away from us like a closed spread (36.85);
        then the village (37.54). What stays is the hill: the same hill as the first fire's (its print, its stone). The
        gaze lifts to it and squares to it; the print becomes the painted place under its own still sky (38.55-39.15)."""
        cam = self.d4_cam(t)
        f_t = ease(36.85, 37.30, t)
        f_v = ease(37.54, 37.99, t)
        up = {'town': 1 + f_t, 'street': 1 + ease(36.80, 37.25, t), 'near': 1 + ease(36.95, 37.35, t),
              'village': 1 + f_v, 'hill': 1.0}
        cold = ease(37.6, 38.6, t)
        lights = {'town': 1.0 - ease(36.30, 36.90, t), 'street': 1.0 - ease(36.20, 36.85, t),
                  'village': 0.6 * (1 - ease(37.20, 37.60, t))}
        age = {'town': ease(36.2, 36.9, t), 'village': ease(37.0, 37.6, t)}
        d_town = float(np.linalg.norm(np.array([0.1, 0.15, 0.80]) - cam.p))
        d_hill = float(np.linalg.norm(self.crest - cam.p))
        focus = d_town + (d_hill - d_town) * ease(36.85, 38.0, t)
        sk = ease(37.6, 38.4, t)
        real = ease(38.55, 39.05, t)
        img = self.town_scene(t, cam, up, 0.12 * (1 - cold), lights, focus=focus, haze={'hill': 0.25 * (1 - cold), 'village': 0.12},
                              stars=0.0, cold=cold * (1 - real), age=age, real=real,
                              sky=(self.hill_sky(cam), sk) if sk > 0 else None, road=1.0 - ease(36.85, 37.45, t))
        img = img * (1 - 0.18 * cold * (1 - real)) + np.array([14, 6, 0], np.float32) * cold * (1 - real)
        fin = ease(38.95, 39.15, t)
        if fin > 0:                                                                       # exactly D6's last window, before the fire
            pl = self.plate5('first_fire_hill_wide_v1') * np.array([0.92, 0.94, 0.96], np.float32)
            img = img * (1 - fin) + self.to_screen(pl, *self.hill_view(self.HILL_FINAL_T), cubic=True) * fin
        return img

    HILL_FINAL_T = 1014 / 24                       # the hill's final framing (D4's end and D6's settled view), as in v6
    D6_END = 1038 / 24                             # m26: D6 runs to the end of the excerpt; the palm-orb return (E1) is removed
    HILL_TINDER = np.array([724.0, 596.0])        # first_fire_hill_wide_v1 (1672x941): the tinder bundle on the crest, measured;
    HILL_STONE = (646.0, 583.0, 708.0, 609.0)      # the flat stone beside it (the hearth stone of D5)
    PALM = np.array([1361 * OI.S, (1205 - 160) * OI.S])                                # the light in A's palm (V1a, E1): (567, 435)

    def hill_view(self, t):
        """D6's window on the hill plate: from close on the tinder and the stone (the struck flame on D5's screen point)
        back to the whole hill, ending with the fire on the palm light's screen point."""
        u = ease(41.00, 42.02, t)                                                        # the match registers, then the view opens
        w = 760.0 * (1540.0 / 760.0) ** u
        q = np.array([567.0, 443.0]) * (1 - u) + self.PALM * u
        return self.HILL_TINDER[0] - q[0] * w / W, self.HILL_TINDER[1] - q[1] * w / W, w

    def d6(self, t):
        """"on the first cold hill": the struck fire, on the same ground (the flat stone, the tinder, the dry grass), as
        the view opens to the bare hill, the far ranges and a still sky. The fire holds its screen point; the place
        around it grows. Then it is quiet."""
        pl = self.plate5('first_fire_hill_wide_v1')
        hh, ww = pl.shape[:2]
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        tx, ty = self.HILL_TINDER
        d2 = (xx - tx) ** 2 + ((yy - ty) * 1.6) ** 2                                      # light spreads along the ground
        fl = 1.0 + 0.06 * np.sin(t * 2 * np.pi * 5.3) + 0.04 * np.sin(t * 2 * np.pi * 9.1)
        warm = (1.05 * np.exp(-d2 / 75.0 ** 2) + 0.42 * np.exp(-d2 / 230.0 ** 2)) * fl
        k = np.array([0.92, 0.94, 0.96], np.float32) + warm[..., None] * np.array([0.35, 0.80, 1.25], np.float32)
        x0, y0, w = self.hill_view(t)
        st = 0.012 * ease(42.02, 43.25, t)                                              # m26: the camera settles, it does not stop dead
        cx_, cy_ = x0 + w / 2, y0 + w * 9 / 32
        w = w * (1 + st)
        x0, y0 = cx_ - w / 2, cy_ - w * 9 / 32
        img = self.to_screen(pl * k, x0, y0, w, cubic=True)
        f = self.c2s(self.HILL_TINDER + np.array([0.0, -3.0]), x0, y0, w)
        self.fire_xy = f
        return flame(img, f, 15.5 * W / w, t, k=1.0)

    def e1(self, t):
        """"hill": the same light, still in A's palm (V1a's frame and light, not a new catch), now warm as the fire; it
        settles into the next section."""
        u = ease(self.D6_END, 43.25, t)
        z = 1.0 + 0.018 * u                                                              # a slight push in, toward her palm
        c = self.PALM
        M = np.float32([[z, 0, c[0] * (1 - z)], [0, z, c[1] * (1 - z)]])
        img = cv2.warpAffine(self.kv5a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        mem = 1 - ease(self.D6_END, self.D6_END + 0.40, t)                               # the fire's warmth resolves into the held light
        img = glow(img, c, 0.62 + 0.10 * mem, 0.55 + 0.25 * mem + 0.05 * np.sin(t * 2 * np.pi * 1.1), tint=(0.78, 0.94, 1.16))
        return glow(img, c, 0.40, 1.15 + 0.10 * u)

# constellation shapes (card units, x 0..1.5, y 0..1): war = the candle and its flame, the helmet, the letter on the
# table; lullaby = the lamp, the cradle and its rockers; goodbye = two arms reaching toward each other, not touching
CONST = [
    [[(0.30, 0.24), (0.31, 0.31)], [(0.25, 0.64), (0.25, 0.36), (0.36, 0.36), (0.36, 0.64)],
     [(0.93, 0.60), (1.00, 0.51), (1.08, 0.45), (1.17, 0.43), (1.26, 0.46), (1.33, 0.53), (1.40, 0.60)],
     [(0.47, 0.60), (0.88, 0.58), (0.93, 0.66), (0.43, 0.67), (0.47, 0.60)]],
    [[(0.08, 0.40), (0.13, 0.22), (0.30, 0.22), (0.35, 0.40), (0.08, 0.40)], [(0.21, 0.40), (0.21, 0.55)],
     [(0.52, 0.36), (0.60, 0.58), (0.80, 0.64), (1.02, 0.60), (1.12, 0.38)], [(0.48, 0.74), (0.66, 0.80), (0.84, 0.81), (1.02, 0.78), (1.18, 0.72)],
     [(1.12, 0.38), (1.30, 0.30), (1.48, 0.27)]],
    [[(0.00, 0.47), (0.22, 0.50), (0.40, 0.52), (0.55, 0.53), (0.66, 0.535)], [(0.52, 0.49), (0.60, 0.46)],
     [(1.50, 0.50), (1.24, 0.52), (1.02, 0.535), (0.86, 0.55), (0.76, 0.545)], [(0.95, 0.50), (0.90, 0.46)]],
]
CONST_AT = [(240.0, 185.0), (640.0, 140.0), (1040.0, 185.0)]


def line_kernel(theta, n):
    k = np.zeros((n, n), np.uint8)
    c = (n - 1) / 2
    dx, dy = np.cos(theta) * c, np.sin(theta) * c
    cv2.line(k, (int(round(c - dx)), int(round(c - dy))), (int(round(c + dx)), int(round(c + dy))), 1, 1)
    return k


def open_lines(a, n, steps):
    """Keep what lies on a straight run at least n px long in some direction (a union of line openings)."""
    out = np.zeros_like(a)
    for th in np.linspace(0, np.pi, steps, endpoint=False):
        out = np.maximum(out, cv2.morphologyEx(a, cv2.MORPH_OPEN, line_kernel(th, n)))
    return out


def kv4_matte(k4, m4):
    """B's matte for D1, from KV4 (3072x2048) and its own matte. KV4's matte is soft (0.6-0.8 inside her hair, 0.05-0.2
    on the outer strands, ~0.5 where her hair leaves the right side of the picture) and also covers the night between
    the strands, so it is used only for her body; her hair edge is matted by colour and shape. Returns alpha (full size,
    unblurred) and the colour to premultiply, with the night removed from the hair's edge pixels."""
    xx = np.arange(m4.shape[1], dtype=np.float32)[None, :]
    m4 = m4 + 0.12 * np.clip((xx - (m4.shape[1] - 96)) / 48.0, 0, 1)       # her hair runs out of the right side
    bb, gg, rr = k4[..., 0], k4[..., 1], k4[..., 2]
    lum = 0.11 * bb + 0.59 * gg + 0.30 * rr
    navy = np.clip((bb - rr + 8) / 25.0, 0, 1) * np.clip((150 - lum) / 60.0, 0, 1)
    copper = np.clip((rr - bb - 18) / 30.0, 0, 1)
    solid = cv2.erode((m4 > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8))
    deep = cv2.erode((m4 > 0.5).astype(np.uint8), np.ones((61, 61), np.uint8))     # her face, body, bow: never re-matted
    near = cv2.dilate((m4 > 0.03).astype(np.uint8), np.ones((3, 3), np.uint8))           # only where KV4 itself has her
    # the city lights between the strands: small bright dots and rows (strands are tall)
    bright = ((((gg / np.maximum(rr, 1) > 0.88) & (lum > 110)) | ((lum > 165) & (rr - bb > 110))) & (deep == 0)).astype(np.uint8)
    n_b, lab_b, st_b, _ = cv2.connectedComponentsWithStats(bright, connectivity=8)
    speck = np.zeros(n_b, bool)
    speck[1:] = (np.maximum(st_b[1:, 2], st_b[1:, 3]) < 25) & (st_b[1:, 3] <= 1.5 * st_b[1:, 2])
    lights = cv2.dilate(speck[lab_b].astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    # copper connected to her body is hair; the navy night is not
    cand = (((copper > 0.45) & (navy < 0.5) & (near > 0)) | (solid > 0)) & ~lights
    n_, lab, st, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), connectivity=8)
    keep = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.float32)
    a4 = np.maximum(deep.astype(np.float32), keep * np.maximum(np.clip(copper * 1.6, 0, 1), solid * (1 - navy)))
    a4 = a4 * (1 - navy * (1 - deep)) * (1 - lights)
    a_cl = cv2.morphologyEx(a4, cv2.MORPH_CLOSE, np.ones((13, 1), np.uint8))     # strands a light crossed, closed again
    a4 = np.maximum(a4, a_cl * (near > 0) * (navy < 0.5))
    warm = np.clip((rr - bb - 2) / 14.0, 0, 1)                                       # outside her body only warm pixels are hair
    a4 = np.where(deep > 0, a4, a4 * warm)
    # The night beside the strands has pink-grey smears (r-b 30-60) that touch them and read as ticks. A strand is a
    # bright copper core (r-b > 95), or a long run, or part of a thick hair mass; keep the hair within 1 px of those.
    core = ((rr - bb > 95) & (a4 > 0.3)).astype(np.uint8)
    thick = cv2.morphologyEx(((a4 > 0.5) & (warm > 0.5)).astype(np.uint8), cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    long_ = (open_lines((a4 > 0.3).astype(np.float32), 31, 24) > 0.5).astype(np.uint8)
    anchor = cv2.dilate(core | thick | long_, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    a4 = np.where(deep > 0, a4, a4 * anchor)
    # inside a hair mass everything is hair, its black line art included; a thin neutral-dark line along a strand or a
    # mass edge is its outline (the navy night is r-b about -45); a dark patch beside her is not
    hf = cv2.morphologyEx(thick, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) * (navy < 0.5)
    a4 = np.maximum(a4, hf.astype(np.float32))
    ink = ((lum < 45) & (np.abs(rr - bb) < 30) & (cv2.dilate((a4 > 0.8).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)).astype(np.uint8)
    blob = cv2.dilate(cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))), np.ones((3, 3), np.uint8))
    a4 = np.where(deep > 0, a4, np.maximum(a4, (ink * (1 - blob)).astype(np.float32)))
    # what is left of the ticks is short: keep only what lies on a run of 17 px or more
    a4 = np.where(deep > 0, a4, np.minimum(a4, open_lines(a4, 17, 16)))
    # the sky seen through a gap in her hair where KV4's matte calls it her: navy regions joined to the background
    # (her ribbon's dark stripes are enclosed by hair and stay)
    nv = (navy > 0.6).astype(np.uint8)
    bg = cv2.dilate(((a4 < 0.05) & (deep == 0)).astype(np.uint8), np.ones((3, 3), np.uint8))
    n_s, lab_s, _, _ = cv2.connectedComponentsWithStats(nv, connectivity=8)
    touch = np.zeros(n_s, bool)
    touch[np.unique(lab_s[(bg > 0) & (nv > 0)])] = True
    touch[0] = False
    a4 = a4 * (1 - (touch[lab_s] & (deep > 0)))
    # an edge pixel half hair, half night takes the colour of the hair beside it, so no strand carries a grey rim
    w = ((warm > 0.95) & (a4 > 0.5)).astype(np.float32)
    wb = cv2.GaussianBlur(w, (0, 0), 2.5)
    fill = cv2.GaussianBlur(k4 * w[..., None], (0, 0), 2.5) / np.maximum(wb, 1e-3)[..., None]
    f = np.where(deep[..., None] > 0, 0, 1 - warm[..., None]) * (wb[..., None] > 0.02)
    return a4.astype(np.float32), k4 * (1 - f) + fill * f


def skeleton_chains(mask, min_len=6):
    """the 1-px skeleton of a drawing's lines as polylines (x, y): walked from the ends, split where lines branch."""
    sk = cv2.ximgproc.thinning((np.asarray(mask) > 0).astype(np.uint8) * 255) > 0
    ys, xs = np.nonzero(sk)
    left = set(zip(xs.tolist(), ys.tolist()))
    nb8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    def nbrs(q):
        return [(q[0] + dx, q[1] + dy) for dx, dy in nb8 if (q[0] + dx, q[1] + dy) in left]
    order = sorted(left, key=lambda q: len(nbrs(q)))                                     # line ends first
    chains = []
    for st in order:
        if st not in left:
            continue
        left.discard(st)
        ch, d = [st], None
        while True:
            nx = nbrs(ch[-1])
            if not nx:
                break
            if d is None:
                q = nx[0]
            else:
                q = max(nx, key=lambda c: (c[0] - ch[-1][0]) * d[0] + (c[1] - ch[-1][1]) * d[1])
            d = (q[0] - ch[-1][0], q[1] - ch[-1][1])
            left.discard(q)
            ch.append(q)
        if len(ch) >= min_len:
            chains.append(np.array(ch, np.float32))
    return chains


def stars_along(chains, step, rng):
    """star positions along polylines, roughly every `step` px, kept where a line turns or ends."""
    out = []
    for ch in chains:
        seg = np.linalg.norm(np.diff(ch, axis=0), axis=1)
        L = np.concatenate([[0], np.cumsum(seg)])
        if L[-1] < step * 0.6:
            out.append(ch[len(ch) // 2])
            continue
        for d in np.arange(rng.uniform(0, step * 0.5), L[-1], step):
            out.append(ch[min(int(np.searchsorted(L, d)), len(ch) - 1)])
        out.append(ch[-1])
    return np.array(out, np.float32)


def OI_crop(img, y0):
    h = int(img.shape[1] * 9 / 16)
    return cv2.resize(img[y0:y0 + h], (W, H), interpolation=cv2.INTER_AREA)


SHOTS = [
    ('O', 0, 179, 'opening ink (tools/opening_ink.py) to the KV1 landing; 3.625-7.458 the chroma-repaired Seedance rear shot (src f0-92, original speed, registered to KV1), cut as A\'s fingertips leave the ledge'),
    ('S1-S3', 180, 325, 'approved light catch (S2 hand fixed); S3 (10.67-13.54) adds a restrained wrist roll, finger close and gaze after the touch, no new reach'),
    ('V1a', 326, 358, 'KV5a: the light in her palm flickers on the burst; "We were born"'),
    ('V1b', 359, 380, 'A, side-palm candidate in A3\'s framing: the light opens into a sheet beside her; her eyes, then her head, lift to it; it comes to the lens only in the last 6 frames'),
    ('P1a', 381, 446, 'the letter: the light reads the words, settles in the full stop; the page tears as paper from its left edge, the spiral shard last'),
    ('A1', 447, 468, 'A1 (voice-over, lips closed, new matte from the drawing): she looks up at the rising light; shards pass low in front'),
    ('P1b', 469, 490, '"translated": every shard rewritten in another script, the spiral kept; "compressed": the shards gather on the spiral, which folds to a point'),
    ('M1', 491, 533, '"every war" (war_memory_v1): the point lands on the measured wick and lights it; candlelight finds the letter, helmet and ruins; the view opens, the candle drifts to the lamp\'s place'),
    ('M2', 534, 571, '"every lullaby" (full frame, supplied art): the hand gives the cradle one push; it rolls on its rockers and settles; the lamp answers the candle'),
    ('M3', 572, 599, '"every last goodbye" (full frame, close, supplied art): fingertips nearly touch, part as the carriage moves, it pulls away; a spark stays'),
    ('C1', 600, 685, 'the parting hands traced in light; pull back: cradle, war room, the letter\'s mark, the handwriting spiral; three torn pieces of the letter pass the lens (gone by 27.4); A and B small on the parapet'),
    ('D1', 686, 730, 'Seedance D1 (chroma-repaired, src f20-64): the paper city unfolds; windows light left to right; B, in cool night light at first, is warmed by them'),
    ('D2', 731, 774, '"heat" (full frame, supplied art): thin steam from the rim, warmth near the bowl, the window cold'),
    ('D3', 775, 818, '"hearts" (full frame, supplied art): parent and baby breathe together, one connected layer; no light from the chest'),
    ('D3b', 819, 861, 'Seedance B3 (chroma-repaired, src f42-84): eyes open, one slow closure, a quiet closed-eye hold'),
    ('D4', 862, 941, '"silent, still": windows go dark, paper yellows, town and street fold back (36.85), the village (37.54); the gaze lifts to the hill print, which becomes the painted hill of the first fire under its own sky'),
    ('D5', 942, 982, '"the first fire": prepare (fist up, wrist cocked), strike into contact (frames 950-951, 961-962), rebound; the forearm swings about the elbow; sparks, ember, flame at 40.50'),
    ('D6', 983, 1037, '"on the first cold hill" (first_fire_hill_wide_v1): the struck fire on the measured tinder; the view opens to the bare hill and settles; the fire flickers, small in the landscape, to the end of the excerpt'),
]
WIPES = []          # v4: no decorative wipes; the cuts are matches on the light, the hands, the spark and the fire


_W = {}


def _init_worker():
    global PROF
    PROF = glow_profile()
    OI.PROF = PROF
    _W['op'] = OI.Opening()
    _W['vs'] = Verse(_W['op'])


def _render_frame(f):
    pic = np.clip(render(_W['vs'], _W['op'], f / FPS, None), 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(CACHE, 'f%04d.png' % f), pic, [cv2.IMWRITE_PNG_COMPRESSION, 1])
    return f


def main():
    """--stills t1,t2   single frames into $DEMO_CHECK
    --shots ID,ID|all [--jobs N]   render those shots' frames into the cache (only what changed)
    --assemble   encode the cached frames 0..1037 with the locked master into one continuous file"""
    global PROF
    if '--shots' in sys.argv:
        import multiprocessing as mp
        ids = sys.argv[sys.argv.index('--shots') + 1].split(',')
        frames = [f for sh in SHOTS if ids == ['all'] or sh[0] in ids for f in range(sh[1], sh[2] + 1)]
        if '--frames' in sys.argv:                                                       # a frame range a-b (inclusive)
            a_, b_ = map(int, sys.argv[sys.argv.index('--frames') + 1].split('-'))
            frames = [f for f in range(a_, b_ + 1)] if ids == ['none'] else [f for f in frames if a_ <= f <= b_]
        jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 4
        os.makedirs(CACHE, exist_ok=True)
        frames = frames[::2] + frames[1::2]                                              # spread heavy shots over the workers
        with mp.get_context('fork').Pool(jobs, initializer=_init_worker) as pool:
            for k, f in enumerate(pool.imap_unordered(_render_frame, frames, chunksize=2)):
                if k % 50 == 0:
                    print('rendered', k, 'of', len(frames), flush=True)
        print('cached', len(frames), 'frames')
        return
    if '--assemble' in sys.argv:
        missing = [f for f in range(N) if not os.path.exists(os.path.join(CACHE, 'f%04d.png' % f))]
        assert not missing, 'missing frames %s..' % missing[:5]
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H), '-r', str(FPS),
                               '-i', '-', '-t', '%.4f' % (N / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '18',
                               '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', OUT], stdin=subprocess.PIPE)
        strip = []
        marks = [sh[1] + (sh[2] - sh[1]) // 2 for sh in SHOTS]
        for f in range(N):
            pic = cv2.imread(os.path.join(CACHE, 'f%04d.png' % f))
            ff.stdin.write(pic.tobytes())
            if f in marks:
                th = cv2.resize(pic, (320, 180), interpolation=cv2.INTER_AREA)
                cv2.putText(th, '%.2f' % (f / FPS), (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
                strip.append(th)
        ff.stdin.close()
        ff.wait()
        strip += [np.zeros_like(strip[0])] * (-len(strip) % 5)
        cv2.imwrite(STRIP, np.vstack([np.hstack(strip[i:i + 5]) for i in range(0, len(strip), 5)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
        json.dump([dict(id=sh[0], frames=[sh[1], sh[2]], song=[round(sh[1] / FPS, 3), round((sh[2] + 1) / FPS, 3)], picture=sh[3])
                   for sh in SHOTS], open(LOG, 'w'), indent=1)
        print('wrote', OUT)
        return
    PROF = glow_profile()
    OI.PROF = PROF
    op = OI.Opening()
    vs = Verse(op)
    out = os.environ.get('DEMO_CHECK', '/tmp')
    ts = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
    for t in ts:
        cv2.imwrite(os.path.join(out, 'd_%06.3f.jpg' % t), np.clip(render(vs, op, t, None), 0, 255).astype(np.uint8),
                    [cv2.IMWRITE_JPEG_QUALITY, 90])


def render(vs, op, t, approved):
    f = int(round(t * FPS))
    if f < 180:
        subs = 5 if OI.T_PULL <= t <= 3.40 else 1
        return op.frame(t, subs=subs) * OI.ease(0.232, 0.55, t)
    if f <= 325:
        if f >= 256:                                                                     # S3 with the v5 wrist/finger settle and gaze
            if 'S3' not in _W:
                if not os.path.exists(S3_V5):
                    import p1_local
                    np.save(S3_V5, np.stack(p1_local.build_s3()[0]))
                _W['S3'] = np.load(S3_V5, mmap_mode='r')
            return np.asarray(_W['S3'][f - 256]).astype(np.float32)
        if approved is None:
            cap = cv2.VideoCapture(APPROVED)
            cap.set(cv2.CAP_PROP_POS_FRAMES, f - 180)
            return cap.read()[1].astype(np.float32)
        return approved[f - 180].astype(np.float32)
    sid = next(s[0] for s in SHOTS if s[1] <= f <= s[2])
    fn = {'V1a': vs.v1a, 'V1b': vs.v1b, 'P1a': vs.p1a, 'A1': vs.a1, 'P1b': vs.p1b,
          'M1': vs.m1,
          'M2': vs.m2, 'M3': vs.m3,
          'C1': vs.constellations, 'D1': vs.d1, 'D2': vs.d2, 'D3': vs.d3, 'D3b': vs.d3b, 'D4': vs.d4,
          'D5': vs.d5, 'D6': vs.d6, 'E1': vs.e1}[sid]
    img = fn(t)
    for tc, seed in WIPES:
        img = vs.wipe(img, t, tc, seed)
    return img


if __name__ == '__main__':
    main()
