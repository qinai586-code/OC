"""Light World: everything is points and lines of light in real 3D; the only images are the
characters, placed as lit cards. Depth of field turns out-of-focus points into bokeh discs."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'loading', 'src'))

import cv2
import numpy as np
from common import (imread, imwrite, gblur, fast_blur, lin, smooth, smoother, ease_out, ease_in, mix,
                    clamp01, value_noise, fbm_field, smoothstep, lum, over, W_OUT, H_OUT, FPS, SCRATCH)
from proj import PCam, rot_x, rot_y, rot_z

ROOT2 = os.path.dirname(HERE)
WORK2 = os.path.join(ROOT2, 'work')
os.makedirs(WORK2, exist_ok=True)


def w2(*p):
    return os.path.join(WORK2, *p)


AMBER = np.array([1.00, 0.66, 0.30], np.float32)
WARM = np.array([1.00, 0.80, 0.55], np.float32)
TEAL = np.array([0.35, 1.00, 0.85], np.float32)
STAR = np.array([0.78, 0.85, 1.00], np.float32)
RED = np.array([1.00, 0.20, 0.14], np.float32)
WHITE = np.array([1.0, 1.0, 1.0], np.float32)

LEVELS = np.array([0.0, 2.0, 4.5, 9.0, 18.0, 36.0, 72.0], np.float32)     # bokeh radii (px)
SCALES = [1, 1, 1, 2, 2, 4, 8]                                           # buffer downsample per level

_kern = {}


def disc_kernel(r):
    key = round(float(r), 2)
    if key not in _kern:
        R = int(np.ceil(r)) + 1
        yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
        d = np.sqrt(xx * xx + yy * yy)
        k = np.clip(r + 0.5 - d, 0, 1)
        # a slightly brighter rim, like real lens bokeh
        k = k * (0.85 + 0.25 * np.clip(d / max(r, 1e-3), 0, 1) ** 4)
        _kern[key] = (k / k.sum()).astype(np.float32)
    return _kern[key]


class Frame:
    """Accumulates light for one frame. Points are binned by blur radius; each bin is convolved
    once with its bokeh disc. Two depth layers ('far'/'near') let cards sit between them."""

    def __init__(self, cam, focus=None, aperture=0.0, split=None, w=W_OUT, h=H_OUT):
        self.cam, self.focus, self.ap, self.split = cam, focus, aperture, split
        self.w, self.h = w, h
        self.bufs = {}
        self.lines = {'far': np.zeros((h, w, 3), np.float32), 'near': np.zeros((h, w, 3), np.float32)}

    def _buf(self, layer, lv):
        key = (layer, lv)
        if key not in self.bufs:
            s = SCALES[lv]
            self.bufs[key] = np.zeros((self.h // s + 2, self.w // s + 2, 3), np.float32)
        return self.bufs[key]

    def project(self, P):
        C = self.cam.to_cam(P)
        z = C[:, 2]
        ok = z > 0.02
        zz = np.where(ok, z, 1.0)
        x = self.cam.cx + self.cam.f * C[:, 0] / zz
        y = self.cam.cy - self.cam.f * C[:, 1] / zz
        return x, y, z, ok

    def points(self, P, col, inten=1.0, size=0.0, min_r=0.0, extra_blur=0.0):
        """P (N,3) world; col (3,) or (N,3); inten scalar or (N,); size: world radius of a light."""
        P = np.asarray(P, np.float64)
        if len(P) == 0:
            return
        x, y, z, ok = self.project(P)
        col = np.asarray(col, np.float32)
        inten = np.broadcast_to(np.asarray(inten, np.float32), (len(P),)).copy()
        m = ok & (x > -120) & (x < self.w + 120) & (y > -120) & (y < self.h + 120) & (inten > 1e-4)
        if not m.any():
            return
        x, y, z, inten = x[m], y[m], z[m], inten[m]
        if col.ndim == 2:
            col = col[m]
        f = self.cam.f
        coc = np.zeros_like(z)
        if self.focus is not None and self.ap > 0:
            coc = self.ap * f * np.abs(1.0 / z - 1.0 / self.focus)
        r = np.sqrt(coc ** 2 + (size * f / z) ** 2 + min_r ** 2 + extra_blur ** 2)
        lv = np.clip(np.searchsorted(LEVELS, r, side='right') - 1, 0, len(LEVELS) - 1)
        # interpolate energy between two adjacent levels so blur changes smoothly
        lo = lv
        hi = np.minimum(lv + 1, len(LEVELS) - 1)
        span = np.maximum(LEVELS[hi] - LEVELS[lo], 1e-3)
        wh = np.where(hi > lo, np.clip((r - LEVELS[lo]) / span, 0, 1), 0.0)
        layer = np.full(len(z), 'far', object)
        if self.split is not None:
            layer[z < self.split] = 'near'
        E = (col if col.ndim == 2 else col[None, :]) * inten[:, None]
        for L in ('far', 'near'):
            mL = layer == L
            if not mL.any():
                continue
            for lvl in np.unique(np.concatenate([lo[mL], hi[mL]])):
                for sel, wgt in ((mL & (lo == lvl), 1 - wh), (mL & (hi == lvl) & (hi > lo), wh)):
                    if not sel.any():
                        continue
                    s = SCALES[lvl]
                    buf = self._buf(L, lvl)
                    xs, ys = x[sel] / s, y[sel] / s
                    e = E[sel] * wgt[sel][:, None]
                    self._splat(buf, xs, ys, e)

    @staticmethod
    def _splat(buf, xs, ys, e):
        h, w = buf.shape[:2]
        x0 = np.floor(xs).astype(np.int64)
        y0 = np.floor(ys).astype(np.int64)
        fx_ = (xs - x0).astype(np.float32)
        fy_ = (ys - y0).astype(np.float32)
        flat = buf.reshape(-1, 3)
        idxs, ws = [], []
        for dx, dy, wt in ((0, 0, (1 - fx_) * (1 - fy_)), (1, 0, fx_ * (1 - fy_)), (0, 1, (1 - fx_) * fy_), (1, 1, fx_ * fy_)):
            xi, yi = x0 + dx, y0 + dy
            ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
            idxs.append(np.where(ok, yi * w + xi, 0))
            ws.append(np.where(ok, wt, 0.0))
        idx = np.concatenate(idxs)
        wv = np.concatenate(ws)
        n = h * w
        for c in range(3):
            flat[:, c] += np.bincount(idx, weights=wv * np.tile(e[:, c], 4), minlength=n)[:n].astype(np.float32)

    def segments(self, A, B, col, inten=1.0, width=1.0, layer=None, near=0.05):
        """3D line segments A[i]-B[i] as thin lines of light (AA), brightness falls with distance."""
        A = np.atleast_2d(np.asarray(A, np.float64))
        B = np.atleast_2d(np.asarray(B, np.float64))
        if len(A) == 0:
            return
        CA, CB = self.cam.to_cam(A), self.cam.to_cam(B)
        col = np.asarray(col, np.float32)
        inten = np.broadcast_to(np.asarray(inten, np.float32), (len(A),))
        f, cx, cy = self.cam.f, self.cam.cx, self.cam.cy
        for i in range(len(A)):
            a, b = CA[i], CB[i]
            if a[2] < near and b[2] < near:
                continue
            if a[2] < near:
                a = a + (b - a) * (near - a[2]) / (b[2] - a[2])
            if b[2] < near:
                b = b + (a - b) * (near - b[2]) / (a[2] - b[2])
            pa = (cx + f * a[0] / a[2], cy - f * a[1] / a[2])
            pb = (cx + f * b[0] / b[2], cy - f * b[1] / b[2])
            if max(abs(pa[0]), abs(pa[1]), abs(pb[0]), abs(pb[1])) > 2e4:
                continue
            L = layer or ('near' if (self.split is not None and min(a[2], b[2]) < self.split) else 'far')
            c = col[i] if col.ndim == 2 else col
            v = float(inten[i])
            if v <= 1e-4:
                continue
            S = 4
            cv2.line(self.lines[L], (int(pa[0] * S), int(pa[1] * S)), (int(pb[0] * S), int(pb[1] * S)),
                     tuple(float(q) * v for q in c), max(1, int(round(width * S))), cv2.LINE_AA, shift=2)

    def polyline(self, P, col, inten=1.0, width=1.0, layer=None):
        P = np.asarray(P, np.float64)
        if len(P) < 2:
            return
        I = np.broadcast_to(np.asarray(inten, np.float32), (len(P),))
        self.segments(P[:-1], P[1:], col, I[:-1], width, layer)

    def resolve(self, layer):
        out = np.zeros((self.h, self.w, 3), np.float32)
        for (L, lv), buf in self.bufs.items():
            if L != layer:
                continue
            s = SCALES[lv]
            r = LEVELS[lv] / s
            if lv == 0:
                img = cv2.GaussianBlur(buf, (0, 0), 0.65)
            else:
                img = cv2.filter2D(buf, -1, disc_kernel(max(r, 1.0)), borderType=cv2.BORDER_CONSTANT)
            if s > 1:
                img = cv2.resize(img, (img.shape[1] * s, img.shape[0] * s), interpolation=cv2.INTER_LINEAR)
                img = img * 1.0
            out += img[:self.h, :self.w]
        out += cv2.GaussianBlur(self.lines[layer], (0, 0), 0.6)
        return out


# ---------------------------------------------------------------------------------- finishing
def bloom(light, strength=0.6):
    acc = np.zeros_like(light)
    for r, wgt in ((2.0, 0.45), (7.0, 0.30), (20.0, 0.18), (60.0, 0.10)):
        acc += fast_blur(light, r) * wgt
    return light + acc * strength


def tonemap(x, exposure=1.0):
    x = np.maximum(x * exposure, 0)
    return 1.0 - np.exp(-x * 1.15)


_grain = {}


def finish(img, t, grain=0.012, vignette=0.30, seed=0):
    h, w = img.shape[:2]
    key = ('v', h, w)
    if key not in _grain:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot((xs / w - 0.5) * 1.25, ys / h - 0.5)
        _grain[key] = (1 - np.clip(d / 0.72, 0, 1.3) ** 2.4)[:, :, None]
    v = 1 - vignette + vignette * _grain[key]
    rng = np.random.default_rng(int(round(t * 60)) + seed * 7919)
    n = rng.normal(0, 1, (h // 2, w // 2)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_LINEAR)[:, :, None]
    out = img * v + n * grain * (0.3 + 0.7 * np.sqrt(np.clip(lum(img), 0, 1))[:, :, None])
    return np.clip(out, 0, 1)


def compose(fr, t, bg=None, cards=(), exposure=1.0, gain=1.45, bloom_k=0.6, grain=0.012, vignette=0.30):
    """bg (optional, HxWx3 linear) + far light + cards + near light -> display image."""
    far = fr.resolve('far')
    out = far if bg is None else bg + far
    for c in cards:
        rgb, a = c
        out = out * (1 - a[:, :, None]) + rgb * a[:, :, None]
    near = fr.resolve('near')
    out = out + near
    out = bloom(out, bloom_k)
    return finish(tonemap(out, exposure * gain), t, grain, vignette)


# ---------------------------------------------------------------------------------- cards
class Card:
    """A character image placed in the 3D world as a flat card (it is paper-thin: turning it
    edge-on makes it a line). Lit by the scene: ambient * rgb + coloured light falloff + rim."""

    def __init__(self, rgba):
        self.rgb = rgba[:, :, :3].astype(np.float32)
        self.a = rgba[:, :, 3].astype(np.float32)
        self.h, self.w = self.a.shape
        e = cv2.erode((self.a > 0.5).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
        self.edge = np.clip(self.a - gblur(e, 3), 0, 1)

    def corners(self, pos, height, yaw=0.0, pitch=0.0, anchor=(0.5, 1.0)):
        """World corners TL, TR, BR, BL. pos = world point of the anchor (default bottom-centre)."""
        W = height * self.w / self.h
        ax, ay = anchor
        R = rot_y(yaw) @ rot_x(pitch)
        loc = np.array([[-ax * W, (1 - 0) * height - ay * height, 0], [(1 - ax) * W, height - ay * height, 0],
                        [(1 - ax) * W, -ay * height, 0], [-ax * W, -ay * height, 0]])
        loc[:, 1] = np.array([ay * height, ay * height, -(1 - ay) * height, -(1 - ay) * height])
        return loc @ R.T + np.asarray(pos)

    def render(self, fr, pos, height, yaw=0.0, pitch=0.0, anchor=(0.5, 1.0), ambient=0.55, lights=(),
               rim=None, opacity=1.0, tint=(1.0, 1.0, 1.0), blur=0.0, sat=1.0):
        """lights: list of (world_pos, rgb, strength, radius_world). rim: (rgb, strength, dir2d)."""
        P = self.corners(pos, height, yaw, pitch, anchor)
        x, y, z, ok = fr.project(P)
        if not ok.all():
            return None
        dst = np.float32(np.stack([x, y], 1))
        src = np.float32([[0, 0], [self.w, 0], [self.w, self.h], [0, self.h]])
        H = cv2.getPerspectiveTransform(src, dst)
        size = (fr.w, fr.h)
        a = cv2.warpPerspective(self.a, H, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * opacity
        if a.max() <= 0.001:
            return None
        rgb = cv2.warpPerspective(self.rgb, H, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        edge = cv2.warpPerspective(self.edge, H, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        if sat != 1.0:
            g = lum(rgb)[:, :, None]
            rgb = g + (rgb - g) * sat
        lit = rgb * ambient * np.asarray(tint, np.float32)
        if lights:
            ys, xs = np.mgrid[0:fr.h:4, 0:fr.w:4].astype(np.float32)
            acc = np.zeros((ys.shape[0], ys.shape[1], 3), np.float32)
            for (lp, lc, ls, lr) in lights:
                lx, ly, lz, lok = fr.project(np.array([lp], np.float64))
                if not lok[0]:
                    continue
                rpx = max(4.0, lr * fr.cam.f / max(lz[0], 0.05))
                d2 = ((xs - lx[0]) ** 2 + (ys - ly[0]) ** 2) / (rpx * rpx)
                acc += (np.asarray(lc, np.float32) * ls)[None, None, :] / (1 + d2)[:, :, None]
            acc = cv2.resize(acc, size, interpolation=cv2.INTER_LINEAR)
            lit = lit + rgb * acc + acc * edge[:, :, None] * 0.6
        if rim is not None:
            rc, rs, (dx, dy) = rim
            sh = cv2.warpAffine(a, np.float32([[1, 0, -dx * 6], [0, 1, -dy * 6]]), size)
            r_ = np.clip(a - sh, 0, 1)
            lit = lit + gblur(r_, 1.2)[:, :, None] * np.asarray(rc, np.float32) * rs
        if blur > 0.3:
            lit = gblur(lit * a[:, :, None], blur)
            a = gblur(a, blur)
            lit = lit / np.maximum(a[:, :, None], 1e-4)
        return lit, np.clip(a, 0, 1), H

    def particles(self, n=6000, seed=0):
        """Sample the figure as light points (u, v in card units [0,1], colour)."""
        rng = np.random.default_rng(seed)
        ys, xs = np.nonzero(self.a > 0.6)
        if len(xs) == 0:
            return np.zeros((0, 2)), np.zeros((0, 3))
        idx = rng.choice(len(xs), size=min(n, len(xs)), replace=False)
        u = (xs[idx] + rng.random(len(idx))) / self.w
        v = (ys[idx] + rng.random(len(idx))) / self.h
        c = self.rgb[ys[idx], xs[idx]]
        return np.stack([u, v], 1), c

    def uv_to_world(self, uv, pos, height, yaw=0.0, pitch=0.0, anchor=(0.5, 1.0)):
        P = self.corners(pos, height, yaw, pitch, anchor)
        TL, TR, BR, BL = P
        u, v = uv[:, 0:1], uv[:, 1:2]
        top = TL + (TR - TL) * u
        bot = BL + (BR - BL) * u
        return top + (bot - top) * v


def load_rgba(path, max_h=None):
    im = imread(path)
    if max_h and im.shape[0] > max_h:
        s = max_h / im.shape[0]
        im = cv2.resize(im, (int(im.shape[1] * s), max_h), interpolation=cv2.INTER_AREA)
    return im


# ---------------------------------------------------------------------------------- helpers
def sphere_pts(n, R, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.normal(0, 1, (n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v * R


def starfield(n=7000, R=900.0, seed=1):
    rng = np.random.default_rng(seed)
    P = sphere_pts(n, R, seed) * rng.uniform(0.6, 1.4, (n, 1))
    b = rng.random(n) ** 4 * 2.2 + 0.05
    tint = rng.random(n)
    col = np.stack([0.78 + 0.22 * tint, 0.84 + 0.06 * tint, 1.0 - 0.18 * tint], 1).astype(np.float32)
    ph = rng.random(n) * 6.28
    fr = rng.uniform(0.3, 1.6, n)
    return dict(P=P, b=b, col=col, ph=ph, fr=fr)


def twinkle(S, t, hold=0.0):
    tw = 0.75 + 0.25 * np.sin(t * S['fr'] * 6.283 + S['ph'])
    return S['b'] * (tw * (1 - hold) + 0.85 * hold)


def beats(a, b):
    import json
    tj = json.load(open(os.path.join(SCRATCH, 'audio', 'timing.json')))
    return [float(x) for x in tj['beats'] if a <= x < b]


def pulse(t, bl, decay=0.18):
    p = 0.0
    for b in bl:
        if t >= b:
            p = max(p, float(np.exp(-(t - b) / decay)))
    return p


def hero(fr, p, col, inten=1.0, size=1.0):
    """A light that is the subject of the shot: hot core, coloured halo, wide faint glow."""
    p = np.atleast_2d(np.asarray(p, np.float64))
    col = np.asarray(col, np.float32)
    s2 = size * size
    fr.points(p, WARM * 0.4 + col * 0.6 + 0.25, inten * 5.0 * max(1.0, s2), min_r=1.2 * size)
    fr.points(p, col, inten * 30.0 * s2, min_r=4.0 * size)
    fr.points(p, col, inten * 80.0 * s2, min_r=14.0 * size)
    fr.points(p, col, inten * 160.0 * s2, min_r=40.0 * size)
