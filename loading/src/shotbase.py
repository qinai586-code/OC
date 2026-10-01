"""Base class and shared per-shot helpers."""
import cv2
import numpy as np
from common import *
from engine import *
import fx
import dimension as dim


class Shot:
    t0 = 0.0
    t1 = 0.0

    def setup(self):
        pass

    def render(self, t):
        raise NotImplementedError


# ---------------------------------------------------------------- paper in screen space
_paper = {}


def _periodic_noise(n, sigma_x, sigma_y, seed):
    """Gaussian-filtered white noise via FFT: exactly periodic (seamless when tiled)."""
    rng = np.random.default_rng(seed)
    w = rng.normal(0, 1, (n, n))
    fy = np.fft.fftfreq(n)[:, None]
    fx_ = np.fft.fftfreq(n)[None, :]
    H = np.exp(-2 * (np.pi ** 2) * ((fx_ * sigma_x) ** 2 + (fy * sigma_y) ** 2))
    r = np.real(np.fft.ifft2(np.fft.fft2(w) * H))
    return ((r - r.mean()) / (r.std() + 1e-9)).astype(np.float32)


def paper_tex():
    """Seamless fine paper texture (2048^2) and its mip chain."""
    if 'mips' not in _paper:
        p = work('derived', 'paper_tile2.npy')
        if os.path.exists(p):
            base = np.load(p).astype(np.float32)
        else:
            n = 2048
            tooth = _periodic_noise(n, 0.8, 0.8, 1)
            fib = _periodic_noise(n, 1.0, 9.0, 2)
            cock = _periodic_noise(n, 180, 180, 3)
            shade = 1 + 0.020 * tooth + 0.010 * fib + 0.020 * cock
            base = (dim.PAPER[None, None, :] * shade[:, :, None]).astype(np.float32)
            np.save(p, base.astype(np.float16))
        mips = [base]
        for _ in range(4):
            mips.append(cv2.pyrDown(mips[-1]))
        _paper['mips'] = mips
    return _paper['mips']


def paper_view(M, tex_per_plate=1.6):
    """Paper surface seen through camera matrix M (output->plate), consistent as the camera moves."""
    mips = paper_tex()
    # texture px per output px
    sc = np.hypot(M[0, 0], M[1, 0]) * tex_per_plate
    lvl = int(np.clip(np.floor(np.log2(max(sc, 1e-3))), 0, len(mips) - 1))
    tex = mips[lvl]
    f = tex_per_plate / (2 ** lvl)
    Mt = (M * f).astype(np.float32)
    return cv2.warpAffine(tex, Mt, (W_OUT, H_OUT), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_WRAP)


def pencil_stroke(buf_alpha, pts, width=1.6, pressure=None, jitter=0.0, seed=0):
    """Draw an anti-aliased pencil polyline into an alpha buffer (screen space). ROI-bounded."""
    pts = np.asarray(pts, np.float32)
    if len(pts) < 2:
        return
    rng = np.random.default_rng(abs(int(seed)))
    if jitter > 0:
        pts = pts + gblur(rng.normal(0, jitter, (len(pts), 2)).astype(np.float32), 3)
    h, w = buf_alpha.shape
    pad = int(width * 2) + 3
    x0 = int(max(0, np.floor(pts[:, 0].min()) - pad))
    y0 = int(max(0, np.floor(pts[:, 1].min()) - pad))
    x1 = int(min(w, np.ceil(pts[:, 0].max()) + pad))
    y1 = int(min(h, np.ceil(pts[:, 1].max()) + pad))
    if x1 <= x0 or y1 <= y0:
        return
    S = 4
    layer = np.zeros((y1 - y0, x1 - x0), np.float32)
    off = np.array([x0, y0], np.float32)
    n = len(pts)
    lim = 30000
    for i in range(n - 1):
        p = pressure[i] if pressure is not None else 1.0
        if p <= 0.01:
            continue
        pa = (pts[i] - off) * S
        pb = (pts[i + 1] - off) * S
        if np.abs(pa).max() > lim * S or np.abs(pb).max() > lim * S:
            continue
        cv2.line(layer, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), float(p), max(1, int(round(width * S * (0.6 + 0.4 * p)))), cv2.LINE_AA, shift=2)
    roi = buf_alpha[y0:y1, x0:x1]
    np.maximum(roi, layer, out=roi)


def graphite(base, alpha, color=dim.GRAPHITE, tooth=None, strength=0.85):
    a = np.clip(alpha, 0, 1)
    if tooth is not None:
        a = a * (0.55 + 0.9 * tooth)
    a = np.clip(a * strength, 0, 1)[:, :, None]
    return base * (1 - a) + np.asarray(color, np.float32) * a


def tooth_view(paper):
    l = lum(paper)
    return np.clip(0.5 + (l - gblur(l, 3)) * 12, 0, 1)


def fit_circle(pts):
    pts = np.asarray(pts, np.float64)
    A = np.c_[2 * pts[:, 0], 2 * pts[:, 1], np.ones(len(pts))]
    b = (pts ** 2).sum(1)
    c = np.linalg.lstsq(A, b, rcond=None)[0]
    r = np.sqrt(c[2] + c[0] ** 2 + c[1] ** 2)
    return c[0], c[1], r


def to_screen(M, x, y):
    """Plate point -> screen point for an output->plate matrix M."""
    A = M[:, :2]
    b = M[:, 2]
    inv = np.linalg.inv(A)
    p = inv @ (np.array([x, y]) - b)
    return float(p[0]), float(p[1])


def find_stars(img, region_mask, thr=0.22, max_n=200):
    """Small bright isolated points (painted stars) -> list of (x, y, brightness)."""
    l = lum(img)
    peak = l - gblur(l, 4)
    m = ((peak > thr * 0.25) & (l > thr) & (region_mask > 0.5)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        if st[i, 4] < 40:
            out.append((cen[i][0], cen[i][1], float(l[int(cen[i][1]), int(cen[i][0])])))
    out.sort(key=lambda s: -s[2])
    return out[:max_n]


def blit(canvas, rgb, alpha, A, add=None, opacity=1.0, tint=None, gain=1.0):
    """Composite a small sprite into the screen canvas. A: 2x3 sprite->screen affine.
    rgb is composited 'over' with alpha; add (optional) is added (emissive glow)."""
    h, w = alpha.shape
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float32) @ np.asarray(A, np.float32).T
    x0, y0 = np.floor(corners.min(0)).astype(int) - 2
    x1, y1 = np.ceil(corners.max(0)).astype(int) + 2
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(canvas.shape[1], x1), min(canvas.shape[0], y1)
    if X1 <= X0 or Y1 <= Y0:
        return
    A2 = np.asarray(A, np.float32).copy()
    A2[:, 2] -= [X0, Y0]
    size = (X1 - X0, Y1 - Y0)
    a = cv2.warpAffine(alpha.astype(np.float32), A2, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * opacity
    c = cv2.warpAffine(rgb.astype(np.float32), A2, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    if tint is not None:
        c = c * np.asarray(tint, np.float32)
    c = c * gain
    roi = canvas[Y0:Y1, X0:X1]
    roi[:] = roi * (1 - a[:, :, None]) + c * a[:, :, None]
    if add is not None:
        g = cv2.warpAffine(add.astype(np.float32), A2, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        if tint is not None:
            g = g * np.asarray(tint, np.float32)
        roi += g * opacity * gain


def plate_to_screen_affine(M):
    """Inverse of an output->plate 2x3 matrix (plate->screen)."""
    A = np.vstack([M, [0, 0, 1]])
    return np.linalg.inv(A)[:2]


def sprite_affine(M, pos, scale=1.0, sx=1.0, rot=0.0, anchor=(0.0, 0.0)):
    """sprite local (px) -> screen. pos = plate position of the anchor."""
    P2S = np.vstack([plate_to_screen_affine(M), [0, 0, 1]])
    c, s = np.cos(rot), np.sin(rot)
    L = np.array([[scale * sx * c, -scale * s, 0], [scale * sx * s, scale * c, 0], [0, 0, 1]], np.float64)
    T1 = np.array([[1, 0, -anchor[0]], [0, 1, -anchor[1]], [0, 0, 1]], np.float64)
    T2 = np.array([[1, 0, pos[0]], [0, 1, pos[1]], [0, 0, 1]], np.float64)
    return (P2S @ T2 @ L @ T1)[:2]
