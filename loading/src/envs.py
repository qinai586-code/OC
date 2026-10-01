"""New environments painted procedurally in the film's night palette."""
import cv2
import numpy as np
from common import *
import dimension as dim

SKY_TOP = np.array([0.030, 0.040, 0.100], np.float32)
SKY_LOW = np.array([0.085, 0.110, 0.200], np.float32)


def starfield(h, w, n=2600, seed=0, bright=1.0):
    """Returns star list (x, y, b, tint) and a rendered float image (small stars)."""
    rng = np.random.default_rng(seed)
    xs = rng.random(n) * w
    ys = rng.random(n) * h
    b = rng.random(n) ** 3.2 * bright
    tint = rng.random(n)
    img = np.zeros((h, w, 3), np.float32)
    for x, y, bb, tt in zip(xs, ys, b, tint):
        if bb < 0.02:
            continue
        col = np.array([0.80 + 0.2 * tt, 0.85, 1.0 - 0.15 * tt], np.float32)
        r = 0.6 + 1.4 * bb
        ix, iy = int(x), int(y)
        s = int(r * 3) + 1
        if s <= ix < w - s and s <= iy < h - s:
            yy, xx = np.mgrid[-s:s + 1, -s:s + 1].astype(np.float32)
            g = np.exp(-((xx - (x - ix)) ** 2 + (yy - (y - iy)) ** 2) / (2 * r * r * 0.5))
            img[iy - s:iy + s + 1, ix - s:ix + s + 1] += g[:, :, None] * col * bb * 0.9
    stars = [(float(x), float(y), float(bb)) for x, y, bb in zip(xs, ys, b) if bb > 0.25]
    return img, stars


def ridge_line(w, base, amp, scale, seed, octaves=5):
    rng = np.random.default_rng(seed)
    y = np.zeros(w, np.float32)
    a = amp
    s = scale
    for o in range(octaves):
        k = max(4, int(w / s) + 3)
        pts = rng.random((1, k)).astype(np.float32)
        y += a * cv2.resize(pts, (w, 1), interpolation=cv2.INTER_CUBIC)[0]
        a *= 0.42
        s /= 2.4
    return base - y


def spruce(alpha, x, base, h, w, rng, value=1.0):
    """Irregular spruce silhouette: uneven drooping tiers, asymmetric, ragged."""
    tiers = int(np.clip(h / 9, 5, 28))
    top = base - h
    L, R = [], []
    y = top
    for i in range(tiers):
        f = (i + 1) / tiers
        y = top + h * 0.95 * f ** 1.05 + rng.uniform(-0.25, 0.25) * h / tiers
        half = w * 0.5 * (0.10 + 0.9 * f) * rng.uniform(0.75, 1.25)
        droop = h / tiers * rng.uniform(0.2, 0.6)
        tuck = half * rng.uniform(0.35, 0.6)
        L += [(x - half * rng.uniform(0.85, 1.15), y + droop), (x - tuck, y + droop * 0.2 + h / tiers * 0.5)]
        R += [(x + half * rng.uniform(0.85, 1.15), y + droop), (x + tuck, y + droop * 0.2 + h / tiers * 0.5)]
    lean = rng.uniform(-0.04, 0.04) * h
    poly = [(x + lean, top)] + R + [(x + w * 0.05, base + 4), (x - w * 0.05, base + 4)] + L[::-1]
    poly = (np.array(poly) * 4).astype(np.int32)
    cv2.fillPoly(alpha, [poly], float(value), cv2.LINE_AA, shift=2)


def forest_band(W, H, base, seed, size=(40, 120), spacing=(0.22, 0.42), skip=None, rows=3):
    """A dense band of spruces (several staggered rows) on a rolling base; returns alpha (H, W)."""
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W), np.float32)
    roll = ridge_line(W, 0, size[1] * 0.35, 900, seed + 1)
    for row in range(rows):
        off = (rows - 1 - row) * size[0] * 0.55     # back rows sit a little higher
        sc = 0.75 + 0.25 * row / max(1, rows - 1)
        x = -size[1] * 0.3 + rng.uniform(0, size[0])
        while x < W + size[1] * 0.3:
            hgt = rng.uniform(*size) * sc * (0.55 + 0.9 * rng.random() ** 1.5)
            wid = hgt * rng.uniform(0.30, 0.42)
            b = base - off + roll[int(np.clip(x, 0, W - 1))] + rng.uniform(-0.06, 0.06) * hgt
            if skip is not None:
                hgt *= skip(x)
            if hgt > 4:
                spruce(a, x, b, hgt, wid, rng)
            x += wid * rng.uniform(*spacing)
    # the forest mass below the crowns
    for xx in range(0, W, 4):
        b = int(base + roll[xx] - size[0] * 0.55 * (rows - 1) - size[0] * 0.3)
        a[max(0, b):, xx:xx + 4] = 1
    return gblur(a, 0.7)


def conifer(canvas_a, x, y_base, height, width, rng, jag=0.22):
    """Draw one conifer silhouette (alpha) with ragged tiers into canvas_a."""
    tiers = int(6 + height / 60)
    pts_l, pts_r = [], []
    top = y_base - height
    for i in range(tiers + 1):
        f = i / tiers
        yy = top + f * height * 0.92
        half = width * 0.5 * (0.08 + 0.92 * f ** 0.9)
        # tier tips stick out, then tuck in
        out = half * (1 + jag * rng.uniform(0.3, 1.0))
        inn = half * (0.55 + 0.15 * rng.random())
        pts_l += [(x - out, yy), (x - inn, yy + height * 0.92 / tiers * 0.55)]
        pts_r += [(x + out, yy), (x + inn, yy + height * 0.92 / tiers * 0.55)]
    poly = [(x, top - height * 0.03)] + pts_r + [(x + width * 0.06, y_base), (x - width * 0.06, y_base)] + pts_l[::-1]
    poly = (np.array(poly) * 4).astype(np.int32)
    cv2.fillPoly(canvas_a, [poly], 1.0, cv2.LINE_AA, shift=2)


def human(canvas_a, x, y, h, pose, rng):
    """A tiny human silhouette (seated / standing / crouched) by the fire, ~h px tall."""
    s = h / 100.0
    def ell(cx, cy, ax, ay, ang=0):
        cv2.ellipse(canvas_a, (int(cx * 4), int(cy * 4)), (max(1, int(ax * 4)), max(1, int(ay * 4))), ang, 0, 360, 1.0, -1, cv2.LINE_AA, shift=2)
    if pose == 'stand':
        ell(x, y - 88 * s, 7 * s, 8 * s)              # head
        ell(x, y - 58 * s, 11 * s, 24 * s)            # torso / coat
        ell(x - 4 * s, y - 20 * s, 5 * s, 21 * s, 4)  # legs
        ell(x + 4 * s, y - 20 * s, 5 * s, 21 * s, -4)
    elif pose == 'sit':
        ell(x, y - 58 * s, 7 * s, 8 * s)
        ell(x, y - 32 * s, 13 * s, 20 * s, 8)
        ell(x + 10 * s, y - 8 * s, 15 * s, 7 * s)
    else:  # crouch, reaching to the fire
        ell(x, y - 48 * s, 7 * s, 8 * s)
        ell(x + 3 * s, y - 28 * s, 14 * s, 16 * s, 30)
        ell(x + 14 * s, y - 30 * s, 10 * s, 3 * s, 20)
        ell(x, y - 8 * s, 13 * s, 8 * s)


def tile_clouds(h, w, seed=0, cell=22, density=0.52, scale=700, col=(0.13, 0.15, 0.27)):
    """Clouds made of small jigsaw-like cells, echoing the painted clouds of the pack."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    n = int(h * w / (cell * cell))
    pts = rng.random((n, 2)).astype(np.float32) * [w, h]
    sh, sw = h // 2, w // 2
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32) * 2
    _, idx = cKDTree(pts).query(np.stack([xx.ravel(), yy.ravel()], 1))
    idx = idx.reshape(sh, sw)
    dens = fbm_field(h // 8, w // 8, scale / 8, seed + 1, 5)
    dens = cv2.resize(dens, (w, h))
    # stretch horizontally: night clouds lie in bands
    d_at = dens[np.clip(pts[:, 1].astype(int), 0, h - 1), np.clip(pts[:, 0].astype(int), 0, w - 1)]
    on = (d_at > density).astype(np.float32)
    shade = 0.75 + 0.5 * rng.random(n).astype(np.float32) * 0.5 + (d_at - density) * 1.5
    a = cv2.resize(on[idx], (w, h), interpolation=cv2.INTER_NEAREST)
    sv = cv2.resize(shade[idx], (w, h), interpolation=cv2.INTER_NEAREST)
    a = gblur(a, 0.7)
    rgb = np.ones((h, w, 3), np.float32) * np.array(col, np.float32) * sv[:, :, None]
    return rgb, a


def canopy_line(w, base, seed, tip_h=(40, 140), spacing=(9, 22), lean=0.0):
    """Top contour of a dense conifer forest seen from afar: many spiky tips."""
    rng = np.random.default_rng(seed)
    xs = np.arange(w, dtype=np.float32)
    top = np.full(w, base + 400.0, np.float32)
    roll = ridge_line(w, 0, 60, 900, seed + 1)
    x = -20.0
    while x < w + 20:
        hgt = rng.uniform(*tip_h) * (0.6 + 0.8 * rng.random() ** 2)
        wid = hgt * rng.uniform(0.18, 0.30)
        c = int(x)
        lo, hi = max(0, int(x - wid)), min(w, int(x + wid) + 1)
        if hi > lo:
            prof = base + roll[lo:hi] - hgt * np.clip(1 - np.abs(xs[lo:hi] - x - lean * hgt * 0.1) / wid, 0, 1) ** 0.85
            # ragged needle-clump edge
            prof += rng.normal(0, 2.0, hi - lo).astype(np.float32)
            top[lo:hi] = np.minimum(top[lo:hi], prof)
        x += rng.uniform(*spacing)
    top = np.minimum(top, base + roll + rng.normal(0, 1.5, w).astype(np.float32))
    return top


def paint_forest(seed=21, W=3072, H=4400, fire=(1880.0, 3205.0)):
    """Wide night landscape: an enormous sky over a dark forest; the first fire on a bare hilltop.
    Returns layers (name, rgb, alpha, k) back-to-front, stars (x, y, b), fire pos, horizon."""
    rng = np.random.default_rng(seed)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    horizon = 3080.0
    g = np.clip(yy / horizon, 0, 1)[:, :, None] ** 1.8
    sky = (SKY_TOP * (1 - g) + SKY_LOW * g) * np.ones((H, W, 1), np.float32)
    # a faint warm breath of the fire on the low sky
    fd = np.hypot((xx - fire[0]) / 3.0, (yy - fire[1]))
    sky += (np.exp(-(fd / 420.0) ** 2) * 0.10)[:, :, None] * np.array([0.6, 0.3, 0.12])
    simg, stars = starfield(int(horizon), W, n=5200, seed=seed)
    sky[:int(horizon)] += simg
    crgb, ca = tile_clouds(H, W, seed=seed + 2, cell=20, density=0.60, scale=900)
    band = np.exp(-((yy - 2450) / 380.0) ** 2)
    ca = ca * np.clip(band, 0, 1)
    sky = over(sky, crgb, ca * 0.30)
    tex = cv2.resize(fbm_field(H // 4, W // 4, 300, seed + 3, 5), (W, H))
    sky *= (0.94 + 0.12 * tex[:, :, None])
    layers = [('sky', sky, np.ones((H, W), np.float32), 0.30)]

    def band(top, col, haze, k, sd, rim=None, alpha=None):
        a = smoothstep(-1.0, 1.0, yy - top[None, :]) if alpha is None else alpha
        n = cv2.resize(fbm_field(H // 4, W // 4, 90, sd, 4), (W, H))
        rgb = np.ones((H, W, 3), np.float32) * np.array(col, np.float32) * (0.85 + 0.3 * n[:, :, None])
        depth = np.clip((yy - top[None, :]) / 700.0, 0, 1)[:, :, None]
        rgb = mix(rgb, SKY_LOW * 1.15, haze * (1 - 0.6 * depth))
        if rim is not None:
            # moonlight from the upper right catches the right/upper edges of every tip
            sh = cv2.warpAffine(a, np.float32([[1, 0, -3], [0, 1, 4]]), (W, H))
            edge = np.clip(a - sh, 0, 1)
            # only the tips catch the moon, the mass below does not
            tipness = np.clip(1 - gblur(a, 18) * 1.15, 0, 1)
            rgb += gblur(edge * tipness, 0.8)[:, :, None] * np.array(rim, np.float32) * 0.6
        return rgb, a
    # far mountains
    t1 = ridge_line(W, horizon - 120, 220, 1600, seed + 10)
    r, a = band(t1, (0.075, 0.095, 0.17), 0.55, 0.45, seed + 11)
    layers.append(('mountains', r, a, 0.45))
    # far forest
    t2 = np.full(W, horizon + 40, np.float32)
    a2 = forest_band(W, H, horizon + 40, seed + 12, size=(10, 34), rows=4)
    r, a = band(t2, (0.05, 0.062, 0.115), 0.55, 0.55, seed + 13, rim=None, alpha=a2)
    layers.append(('far_forest', r, a, 0.55))
    # the bare hill of the first fire, rising above the forest
    hill = fire[1] + 18 + 0.00028 * (xx[0] - fire[0]) ** 2 + ridge_line(W, 0, 12, 300, seed + 4)
    r, a = band(hill, (0.05, 0.058, 0.10), 0.18, 0.62, seed + 14)
    d = np.hypot((xx - fire[0]), (yy - fire[1]) * 2.4)
    glow = np.exp(-(d / 230.0) ** 2) * 0.6 + np.exp(-(d / 70.0) ** 2) * 0.7
    r = r + (glow * a)[:, :, None] * np.array([0.55, 0.25, 0.07])
    fig = np.zeros((H, W), np.float32)
    for dx, pose, hh in [(-62, 'sit', 38), (-26, 'crouch', 36), (40, 'stand', 46), (74, 'sit', 34)]:
        human(fig, fire[0] + dx, hill[int(fire[0] + dx)] + 2, hh, pose, rng)
    fig = gblur(fig, 0.6)
    r = r * (1 - fig[:, :, None]) + np.array([0.025, 0.02, 0.025]) * fig[:, :, None]
    layers.append(('hill', r, np.maximum(a, fig), 0.62))
    # mid forest (darker), parted below the hill
    t3 = np.full(W, horizon + 300, np.float32)
    a3 = forest_band(W, H, horizon + 300, seed + 15, size=(40, 120), skip=lambda x: 1 - 0.85 * np.exp(-((x - fire[0]) / 300.0) ** 2))
    r, a = band(t3, (0.032, 0.042, 0.08), 0.28, 0.75, seed + 16, rim=(0.07, 0.09, 0.15), alpha=a3)
    layers.append(('mid_forest', r, a, 0.75))
    # near forest: the darkest edge, big tips
    t4 = np.full(W, horizon + 760, np.float32)
    a4 = forest_band(W, H, horizon + 760, seed + 17, size=(130, 360), spacing=(0.3, 0.55), skip=lambda x: 1 - 0.75 * np.exp(-((x - fire[0]) / 480.0) ** 2))
    r, a = band(t4, (0.016, 0.022, 0.042), 0.06, 1.0, seed + 18, rim=(0.07, 0.09, 0.16), alpha=a4)
    layers.append(('near_forest', r, a, 1.0))
    return layers, stars, fire, horizon


def composite_layers(layers, cam_cx, cam_cy, zoom, ref, out_w=W_OUT, out_h=H_OUT, src_w=3072, extra=None, kmap=None):
    out = None
    for name, rgb, a, k in layers:
        if kmap is not None:
            k = kmap.get(name, k)
        cx = ref[0] + (cam_cx - ref[0]) * k
        cy = ref[1] + (cam_cy - ref[1]) * k
        M = cam_matrix(cx, cy, zoom, 0, out_w, out_h, src_w, rgb.shape[0])
        c = affine_sample(rgb, M, out_w, out_h, border=cv2.BORDER_REPLICATE)
        al = affine_sample(a, M, out_w, out_h, border=cv2.BORDER_REPLICATE)
        if out is None:
            out = c
        else:
            out = over(out, c, al)
        if extra is not None and name in extra:
            out = extra[name](out, M)
    return out
