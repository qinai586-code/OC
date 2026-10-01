"""Satsuei (compositing) finishing: light, glow, haze, grain — applied identically to every
shot so that painted, flat and pencil states share one photographic surface."""
import cv2
import numpy as np
from common import *

AMBER = np.array([1.0, 0.66, 0.30], np.float32)
WARM_CORE = np.array([1.0, 0.92, 0.75], np.float32)
TEAL = np.array([0.35, 0.95, 0.85], np.float32)
RED = np.array([1.0, 0.22, 0.16], np.float32)
NIGHT = np.array([0.055, 0.075, 0.16], np.float32)

_grain_cache = {}


def bloom(img, emis=None, thr=0.55, strength=0.9, radii=(3, 10, 30, 80), weights=(0.5, 0.35, 0.22, 0.12), tint=None):
    """Transmitted-light glow from emissive pixels only (or highlights above thr)."""
    if emis is None:
        l = lum(img)
        emis = smoothstep(thr, thr + 0.3, l)
    src = img * emis[:, :, None]
    if tint is not None:
        src = src * tint
    acc = np.zeros_like(img)
    for r, wgt in zip(radii, weights):
        acc += fast_blur(src, r) * wgt
    return img + acc * strength


def diffusion(img, amount=0.12, radius=14):
    b = fast_blur(img, radius)
    return mix(img, screen(img, b), amount)


def vignette(img, amount=0.28, power=2.2, center=(0.5, 0.52)):
    h, w = img.shape[:2]
    key = ('vig', h, w, amount, power, center)
    if key not in _grain_cache:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot((xs / w - center[0]) * 1.2, (ys / h - center[1]))
        _grain_cache[key] = (1 - amount * np.clip(d / 0.75, 0, 1.4) ** power)[:, :, None]
    return img * _grain_cache[key]


def grain(img, t, amount=0.016, size=1.3, seed=0):
    h, w = img.shape[:2]
    fi = int(round(t * FPS))
    rng = np.random.default_rng(seed * 100003 + fi)
    n = rng.normal(0, 1, (int(h / size), int(w / size))).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_LINEAR)
    l = lum(img)[:, :, None]
    # film-like: strongest in the mid tones, little in deep blacks
    resp = 0.35 + 0.65 * np.clip(l * 2.2, 0, 1) * (1.2 - l)
    return img + n[:, :, None] * amount * resp


def paper_tooth(img, amount=0.022):
    """Static paper surface shared by every state (the film is printed on one sheet)."""
    h, w = img.shape[:2]
    key = ('tooth', h, w)
    if key not in _grain_cache:
        import dimension as dim
        _, tooth = dim.paper_texture(h, w, seed=11)
        _grain_cache[key] = (tooth - 0.5)[:, :, None]
    return img * (1 + _grain_cache[key] * amount * 2)


def para(img, top=(0.0, 0.0, 0.0), top_a=0.0, bottom=(0, 0, 0), bottom_a=0.0, mode='screen'):
    """Vertical gradient overlay (para) — top/bottom atmosphere."""
    h, w = img.shape[:2]
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    gt = np.clip(1 - y * 1.6, 0, 1) ** 1.5 * top_a
    gb = np.clip((y - 0.35) / 0.65, 0, 1) ** 1.5 * bottom_a
    if mode == 'screen':
        img = screen(img, np.array(top, np.float32) * gt)
        img = screen(img, np.array(bottom, np.float32) * gb)
    else:
        img = img * (1 - gt) + np.array(top, np.float32) * gt
        img = img * (1 - gb) + np.array(bottom, np.float32) * gb
    return img


def chroma_ab(img, px=0.8):
    if px <= 0.01:
        return img
    h, w = img.shape[:2]
    out = img.copy()
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, 1 + px / w * 2)
    out[:, :, 0] = cv2.warpAffine(img[:, :, 0], M, (w, h), borderMode=cv2.BORDER_REFLECT)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, 1 - px / w * 2)
    out[:, :, 2] = cv2.warpAffine(img[:, :, 2], M, (w, h), borderMode=cv2.BORDER_REFLECT)
    return out


def finish(img, t, glow=True, emis=None, glow_strength=0.9, grain_amt=0.016, vig=0.26, diff=0.10, ca=0.6, tooth=True):
    if glow:
        img = bloom(img, emis=emis, strength=glow_strength)
    if diff > 0:
        img = diffusion(img, diff)
    if vig > 0:
        img = vignette(img, vig)
    if ca:
        img = chroma_ab(img, ca)
    if tooth:
        img = paper_tooth(img)
    img = grain(img, t, grain_amt)
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------- point lights
_kern = {}


def _gauss_kernel(sigma):
    key = round(float(sigma), 2)
    if key not in _kern:
        r = int(max(2, sigma * 4))
        ax = np.arange(-r, r + 1, dtype=np.float32)
        g = np.exp(-(ax[None, :] ** 2 + ax[:, None] ** 2) / (2 * sigma * sigma))
        _kern[key] = g
    return _kern[key]


def splat(buf, x, y, sigma, color, intensity=1.0):
    """Add a gaussian light at subpixel (x, y) into buf (H, W, 3)."""
    k = _gauss_kernel(sigma)
    r = k.shape[0] // 2
    h, w = buf.shape[:2]
    ix, iy = int(np.floor(x)), int(np.floor(y))
    fx, fy = x - ix, y - iy
    if ix + r + 1 < 0 or iy + r + 1 < 0 or ix - r - 1 >= w or iy - r - 1 >= h:
        return
    # subpixel shift by bilinear kernel resample
    M = np.float32([[1, 0, fx], [0, 1, fy]])
    ks = cv2.warpAffine(k, M, (k.shape[1], k.shape[0]))
    x0, y0 = ix - r, iy - r
    x1, y1 = x0 + ks.shape[1], y0 + ks.shape[0]
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(w, x1), min(h, y1)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    sub = ks[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    buf[cy0:cy1, cx0:cx1] += sub[:, :, None] * (np.asarray(color, np.float32) * intensity)


def point_light(buf, x, y, size=1.0, color=AMBER, intensity=1.0, star=0.0, star_len=18, star_angle=0.0):
    """Anime-style light: hot core + coloured halo (+ optional 4-point star)."""
    splat(buf, x, y, 0.7 * size, WARM_CORE * 0.5 + np.asarray(color) * 0.5, intensity * 1.6)
    splat(buf, x, y, 2.2 * size, color, intensity * 0.35)
    splat(buf, x, y, 7.0 * size, color, intensity * 0.06)
    if star > 0:
        L = int(star_len * size)
        for a in (star_angle, star_angle + np.pi / 2):
            for s in np.linspace(-1, 1, 2 * L + 1):
                if s == 0:
                    continue
                fall = (1 - abs(s)) ** 3
                splat(buf, x + np.cos(a) * s * L, y + np.sin(a) * s * L, 0.6 * size, color, intensity * star * fall * 0.25)


def stamp_lights(img, mask, gain, color=AMBER, core=1.0):
    """Re-light painted city lights from their mask (gain can be a per-pixel field)."""
    m = mask * gain
    return img + m[:, :, None] * (np.asarray(color) * 0.6 + WARM_CORE * 0.4) * core


def paper_light(img, x, y, color, size=2.0, intensity=1.0):
    """A light seen on paper: a saturated pigment-like core with a soft coloured halo, so it
    reads against white (additive light alone would vanish)."""
    h, w = img.shape[:2]
    r = int(size * 18) + 4
    x0, y0, x1, y1 = int(x) - r, int(y) - r, int(x) + r + 1, int(y) + r + 1
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    if X1 <= X0 or Y1 <= Y0:
        return img
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    d2 = (xx - x) ** 2 + (yy - y) ** 2
    col = np.asarray(color, np.float32)
    deep = col * np.array([0.75, 0.75, 0.75]) * np.array([1.0, 0.95, 0.9])
    halo = np.exp(-d2 / (2 * (size * 6.0) ** 2)) * 0.35 * intensity
    core = np.exp(-d2 / (2 * (size * 1.6) ** 2)) * 0.95 * min(1.0, intensity)
    hot = np.exp(-d2 / (2 * (size * 0.6) ** 2)) * min(1.0, intensity)
    roi = img[Y0:Y1, X0:X1]
    roi[:] = roi * (1 - halo[:, :, None]) + (roi * deep * 1.1) * halo[:, :, None]
    roi[:] = roi * (1 - core[:, :, None]) + deep * core[:, :, None]
    roi[:] = roi * (1 - hot[:, :, None]) + (0.55 * col + 0.45) * hot[:, :, None]
    return img
