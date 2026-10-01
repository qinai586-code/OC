"""The film's dimensional grammar: DEPTH -> FLAT -> LINE -> TRACE (and back = 'loading').

TRACE : bare paper, only the warm marks people left
LINE  : the frame as a layout / genga drawing (graphite, with blue construction pencil)
FLAT  : cel colours without lighting or atmosphere (shiage before satsuei)
DEPTH : the finished painted frame with light, haze and parallax

Every derived state is computed from the same plate so that a transition between
states never moves a single contour: the drawing is literally under the painting.
"""
import cv2
import numpy as np
from common import *

PAPER = np.array([0.925, 0.905, 0.862], np.float32)    # warm sketch paper
GRAPHITE = np.array([0.20, 0.21, 0.24], np.float32)
BLUE_PENCIL = np.array([0.36, 0.50, 0.78], np.float32)  # anime layout construction pencil
RED_PENCIL = np.array([0.80, 0.33, 0.28], np.float32)   # shadow-boundary pencil


def paper_texture(h, w, seed=3, tone=PAPER):
    """Sketch paper: tooth (fine grain), fibres (streaks), soft cockling."""
    rng = np.random.default_rng(seed)
    tooth = gblur(rng.random((h, w)).astype(np.float32), 0.7)
    tooth = (tooth - tooth.mean()) / (tooth.std() + 1e-6)
    fib = rng.random((h // 2, w // 2)).astype(np.float32)
    fib = cv2.resize(cv2.GaussianBlur(fib, (1, 21), 0, sigmaY=6), (w, h))
    fib = (fib - fib.mean()) / (fib.std() + 1e-6)
    cock = fbm_field(h, w, max(h, w) / 3, seed + 1, 3) - 0.5
    shade = 1 + 0.018 * tooth + 0.010 * fib + 0.05 * cock
    pap = tone[None, None, :] * shade[:, :, None]
    return np.clip(pap, 0, 1).astype(np.float32), np.clip(0.5 + 0.18 * tooth, 0, 1)


def xdog(gray, sigma=1.1, k=1.6, tau=0.985, eps=0.0, phi=60.0):
    g1 = gblur(gray, sigma)
    g2 = gblur(gray, sigma * k)
    d = g1 - tau * g2
    e = np.where(d >= eps, 1.0, 1.0 + np.tanh(phi * (d - eps)))
    return np.clip(e, 0, 1).astype(np.float32)


def line_art(plate, strength=1.0, detail=1.0):
    """Pencil linework extracted from a painted anime frame.
    Combines the drawn ink lines (thin dark structures) with colour-region boundaries."""
    lab = cv2.cvtColor((plate * 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32) / 255.
    L = lab[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(16, 16))
    Ln = clahe.apply((L * 255).astype(np.uint8)).astype(np.float32) / 255.
    Ls = cv2.bilateralFilter(Ln, 9, 0.12, 5)
    # 1) drawn ink: black-hat picks up thin dark strokes
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    bh = cv2.morphologyEx(Ls, cv2.MORPH_BLACKHAT, k)
    ink = smoothstep(0.035 / detail, 0.16 / detail, bh)
    # 2) region contours: XDoG on smoothed luminance + chroma edges
    xd = 1 - xdog(Ls, sigma=1.4, tau=0.99, phi=45)
    ab = np.sqrt(gblur(lab[:, :, 1], 1.2) ** 2 + gblur(lab[:, :, 2], 1.2) ** 2)
    sob = np.hypot(cv2.Sobel(gblur(lab[:, :, 1], 1.5), cv2.CV_32F, 1, 0), cv2.Sobel(gblur(lab[:, :, 2], 1.5), cv2.CV_32F, 0, 1))
    ce = smoothstep(0.04, 0.12, sob)
    lines = np.clip(np.maximum(ink, 0.8 * xd) + 0.5 * ce, 0, 1) * strength
    # thin very slightly so it reads as pencil, not marker
    lines = gblur(lines, 0.6)
    return np.clip(lines * 1.15, 0, 1).astype(np.float32)


def flat_cel(plate, n_colors=28, seed=0):
    """Unlit cel colours: mean-shift + palette quantisation; lights removed (lights are TRACE)."""
    small = cv2.resize(plate, (plate.shape[1] // 2, plate.shape[0] // 2), interpolation=cv2.INTER_AREA)
    u8 = (small * 255).astype(np.uint8)
    ms = cv2.pyrMeanShiftFiltering(u8, 10, 18, maxLevel=1)
    Z = ms.reshape(-1, 3).astype(np.float32)
    rng = np.random.default_rng(seed)
    sample = Z[rng.choice(len(Z), min(len(Z), 60000), replace=False)]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, _, centers = cv2.kmeans(sample, n_colors, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    d = ((Z[:, None, :] - centers[None]) ** 2).sum(-1)
    q = centers[d.argmin(1)].reshape(ms.shape)
    q = cv2.medianBlur(q.astype(np.uint8), 5)
    q = cv2.resize(q, (plate.shape[1], plate.shape[0]), interpolation=cv2.INTER_NEAREST)
    q = cv2.medianBlur(q, 5).astype(np.float32) / 255.
    return q


def light_mask(plate, warm_only=True, thresh=0.42):
    """Pixels that are human light (warm emissive points). Returns soft mask [0,1]."""
    hsv = cv2.cvtColor((plate * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    v = hsv[:, :, 2] / 255.
    s = hsv[:, :, 1] / 255.
    h = hsv[:, :, 0] * 2
    local = v - fast_blur(v, 12)
    m = smoothstep(thresh, thresh + 0.25, v) * smoothstep(0.04, 0.16, local)
    if warm_only:
        warm = ((h > 15) & (h < 60)).astype(np.float32) * smoothstep(0.25, 0.5, s)
        m = m * np.maximum(warm, smoothstep(0.85, 0.95, v))
    return np.clip(m, 0, 1).astype(np.float32)


def stroke_order(lines, seed=0, origin=None, speed=900.0, spread=1.0):
    """Arrival time (seconds from 0) for each line pixel so lines 'draw themselves':
    each connected stroke starts at a time based on its distance from `origin`, then
    is swept along its principal axis like a pencil stroke."""
    h, w = lines.shape
    bw = (lines > 0.25).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(bw, 8)
    rng = np.random.default_rng(seed)
    if origin is None:
        origin = (w / 2, h / 2)
    dist = np.hypot(cent[:, 0] - origin[0], cent[:, 1] - origin[1])
    start = dist / max(h, w) * spread + rng.random(n) * 0.25 * spread
    ang = rng.random(n) * np.pi
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    ca, sa = np.cos(ang).astype(np.float32), np.sin(ang).astype(np.float32)
    proj = xs * ca[lab] + ys * sa[lab]
    # per-component min projection
    pmin = np.full(n, 1e9, np.float32)
    np.minimum.at(pmin, lab.ravel(), proj.ravel())
    arr = start[lab] + (proj - pmin[lab]) / speed
    arr[bw == 0] = 1e6
    # spread arrival into the soft line halo
    arr_s = cv2.erode(arr.astype(np.float32), np.ones((3, 3), np.uint8))
    return arr_s.astype(np.float32)


def voronoi_tiles(h, w, cell=90, seed=0, wobble=14):
    """Jigsaw-like tile ids (the film's 'loading' unit, echoing the painted cloud tiles)."""
    rng = np.random.default_rng(seed)
    nx, ny = int(w / cell) + 2, int(h / cell) + 2
    pts = np.stack(np.meshgrid(np.arange(nx), np.arange(ny)), -1).reshape(-1, 2).astype(np.float32) * cell
    pts += rng.random(pts.shape).astype(np.float32) * cell * 0.9 - cell * 0.45
    sw, sh = w // 4, h // 4
    ys, xs = np.mgrid[0:sh, 0:sw].astype(np.float32) * 4
    nx_ = (fbm_field(sh, sw, cell / 4, seed + 7, 3) - 0.5) * wobble * 2
    ny_ = (fbm_field(sh, sw, cell / 4, seed + 9, 3) - 0.5) * wobble * 2
    X, Y = xs + nx_, ys + ny_
    from scipy.spatial import cKDTree
    tr = cKDTree(pts)
    _, idx = tr.query(np.stack([X.ravel(), Y.ravel()], 1))
    ids = idx.reshape(sh, sw).astype(np.int32)
    ids = cv2.resize(ids.astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST).astype(np.int32)
    return ids, pts


def tile_arrival(ids, pts, origin, spread=1.0, jitter=0.35, seed=0):
    rng = np.random.default_rng(seed)
    d = np.hypot(pts[:, 0] - origin[0], pts[:, 1] - origin[1])
    d = d / d.max()
    t = d * spread + rng.random(len(pts)) * jitter
    return t[ids].astype(np.float32)
