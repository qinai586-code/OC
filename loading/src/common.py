"""Shared helpers for the LOADING MV renderer.

Images are float32 RGB in [0, 1] (display-referred, like an After Effects 8/16-bit comp).
Coordinates are (x, y) in pixels of the 3072x2048 working plates unless stated.
"""
import os
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'work')
SCRATCH = os.environ.get('LOADING_SCRATCH', '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad')
PACK = os.path.join(SCRATCH, 'pack')
UP = os.path.join(SCRATCH, 'up')
PREP = os.path.join(SCRATCH, 'prep')

W_OUT, H_OUT = 1920, 1080
FPS = 24


def imread(path, rgb=True):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(path)
    if im.dtype == np.uint16:
        im = im.astype(np.float32) / 65535.0
    else:
        im = im.astype(np.float32) / 255.0
    if im.ndim == 3 and rgb:
        im = im[:, :, ::-1] if im.shape[2] == 3 else im[:, :, [2, 1, 0, 3]]
    return np.ascontiguousarray(im)


def imwrite(path, im, rgb=True):
    im = np.clip(im, 0, 1)
    if im.ndim == 3 and rgb:
        im = im[:, :, ::-1]
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    cv2.imwrite(path, (im * 255 + 0.5).astype(np.uint8))


def work(*p):
    return os.path.join(WORK, *p)


# ---------------------------------------------------------------- easing / timing
def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def lin(t, a, b):
    """0 at t<=a, 1 at t>=b, linear between."""
    if b == a:
        return float(t >= b)
    return float(np.clip((t - a) / (b - a), 0, 1))


def smooth(t, a, b):
    x = lin(t, a, b)
    return x * x * (3 - 2 * x)


def smoother(t, a, b):
    x = lin(t, a, b)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ease_out(t, a, b, p=3):
    x = lin(t, a, b)
    return 1 - (1 - x) ** p


def ease_in(t, a, b, p=3):
    x = lin(t, a, b)
    return x ** p


def ease_io(t, a, b, p=3):
    x = lin(t, a, b)
    return 4 * x ** 3 if x < 0.5 and p == 3 else (1 - (-2 * x + 2) ** p / 2 if p == 3 else smoother(t, a, b))


def mix(a, b, w):
    return a + (b - a) * w


def spring(t, t0, freq=1.6, damp=0.35):
    """Damped response to a step at t0 (0 -> 1 with overshoot). Used for follow-through."""
    if t <= t0:
        return 0.0
    x = t - t0
    w = 2 * np.pi * freq
    return float(1 - np.exp(-damp * w * x) * np.cos(w * np.sqrt(max(1e-6, 1 - damp ** 2)) * x))


# ---------------------------------------------------------------- noise
def value_noise(h, w, scale, seed=0, octaves=1, persistence=0.5):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 2), max(2, int(w / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= persistence
        s /= 2
    return out / tot


def fbm_field(h, w, scale, seed=0, octaves=4):
    n = value_noise(h, w, scale, seed, octaves)
    n = (n - n.min()) / (n.max() - n.min() + 1e-9)
    return n


# ---------------------------------------------------------------- image ops
def gblur(im, sigma):
    if sigma <= 0.05:
        return im
    k = int(sigma * 6) | 1
    return cv2.GaussianBlur(im, (k, k), sigma, borderType=cv2.BORDER_REFLECT)


def fast_blur(im, sigma):
    """Large-radius gaussian via downsampling."""
    if sigma < 6:
        return gblur(im, sigma)
    f = int(min(16, max(2, sigma // 3)))
    h, w = im.shape[:2]
    small = cv2.resize(im, (max(1, w // f), max(1, h // f)), interpolation=cv2.INTER_AREA)
    small = gblur(small, sigma / f)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def screen(a, b):
    return 1 - (1 - a) * (1 - b)


def over(dst, src, alpha):
    if alpha.ndim == 2:
        alpha = alpha[:, :, None]
    return dst * (1 - alpha) + src * alpha


def lum(im):
    return im[:, :, 0] * 0.2126 + im[:, :, 1] * 0.7152 + im[:, :, 2] * 0.0722


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def affine_sample(src, M, out_w=W_OUT, out_h=H_OUT, border=cv2.BORDER_REFLECT, interp=cv2.INTER_LINEAR):
    """M maps OUTPUT pixel coords -> SOURCE coords (2x3)."""
    return cv2.warpAffine(src, M, (out_w, out_h), flags=interp | cv2.WARP_INVERSE_MAP, borderMode=border)


def cam_matrix(cx, cy, zoom, rot=0.0, out_w=W_OUT, out_h=H_OUT, src_w=3072, src_h=2048):
    """Camera looking at source point (cx, cy). zoom=1 shows the full source width (16:9 crop).
    Returns 2x3 matrix mapping source->output (use with WARP_INVERSE_MAP after inverting) —
    we return output->source for affine_sample."""
    s = out_w / (src_w / zoom)  # output px per source px
    c, si = np.cos(rot), np.sin(rot)
    # output = s*R*(src - c) + center_out  =>  src = R^T*(out - center_out)/s + c
    A = np.array([[c, si], [-si, c]]) / s
    b = np.array([cx, cy]) - A @ np.array([out_w / 2, out_h / 2])
    return np.hstack([A, b[:, None]]).astype(np.float32)
