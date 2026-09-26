"""Extreme close-up eyes, drawn analytically at native resolution (hard edges, dithered iris bands)."""
import math
import numpy as np
from engine.px import rgb, rgba, BAYER4

IRIS = {
    'gpt': dict(ring='#0b302b', deep='#11584d', mid='#23a58c', light='#6fe6c8', pupil='#061413', lash='#0b0e12',
                skin='#f7e3d5', skin2='#e7bca7', white='#f4f6f4', white2='#c9d3d2'),
    'claude': dict(ring='#4a220c', deep='#8a4a14', mid='#dc9427', light='#f9d57c', pupil='#240f05', lash='#3a1b10',
                   skin='#fce9dc', skin2='#efc3ad', white='#fbf6f1', white2='#dfd3cc'),
}


def draw_eye(cv, cx, cy, w, who='gpt', open_=1.0, look=(0.0, 0.0), flip=False, star=0.0, glow=0.0, pupil=1.0, t=0.0):
    """Paint one big anime eye centred at (cx, cy), width w (native px). Returns iris centre + radius."""
    P = IRIS[who]
    cx, cy = cx + cv.ox, cy + cv.oy
    h = w * 0.62
    x0, y0 = int(cx - w * 0.62), int(cy - h * 0.9)
    x1, y1 = int(cx + w * 0.62), int(cy + h * 0.75)
    ww, hh = x1 - x0, y1 - y0
    a = np.array(cv.im)
    X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    u = (X - cx) / (w / 2)
    if flip:
        u = -u
    uu = np.clip(np.abs(u), 0, 1)
    # lids: upper lid peaks slightly toward the inner corner; outer corner flicks up
    top = cy - h * 0.55 * (1 - uu ** 2.2) ** 0.7 + h * 0.08 * u
    bot = cy + h * 0.42 * (1 - uu ** 2.0) ** 0.9 + h * 0.02 * u
    lid = bot - (bot - top) * max(0.0, min(1.0, open_))
    inside = (np.abs(u) < 1) & (Y >= lid) & (Y <= bot)
    col = np.zeros((hh, ww, 3), np.uint8)
    sel = np.zeros((hh, ww), bool)

    def paint(m, c):
        col[m] = rgb(c)
        sel[m] = True

    paint(inside, P['white'])
    paint(inside & (Y < lid + h * 0.16), P['white2'])
    # iris
    ir = w * 0.29
    ix, iy = cx + look[0] * w * 0.25, cy + h * 0.02 + look[1] * h * 0.2
    d = np.sqrt((X - ix) ** 2 + ((Y - iy) * 0.92) ** 2)
    iris = inside & (d <= ir)
    thr = np.tile(BAYER4, (hh // 4 + 1, ww // 4 + 1))[:hh, :ww]
    band = (Y - (iy - ir)) / (2 * ir)       # 0 top .. 1 bottom
    lvl = np.clip(band * 3 + (thr - 0.5) * 0.9, 0, 2.99).astype(int)
    for k, c in enumerate([P['deep'], P['mid'], P['light']]):
        paint(iris & (lvl == k), c)
    paint(iris & (Y < lid + h * 0.18), P['deep'])
    paint(iris & (d > ir - 1.2), P['ring'])
    # pupil
    pr = ir * 0.38 * pupil
    pm = inside & (((X - ix) / (pr * 0.8)) ** 2 + ((Y - iy) / pr) ** 2 <= 1)
    paint(pm, P['pupil'])
    # star pupil flare (AGI)
    if star > 0:
        ang = np.arctan2(Y - iy, X - ix)
        rr = np.sqrt((X - ix) ** 2 + (Y - iy) ** 2)
        spike = (np.cos(ang * 4 + t * 3) ** 12) * ir * 0.95 * star + ir * 0.18 * star
        paint(inside & (rr < spike), P['light'])
        paint(inside & (rr < ir * 0.22 * star), '#ffffff')
    if glow > 0:
        gl = inside & (d <= ir) & (thr < glow * 0.6)
        paint(gl, P['light'])
    # highlights
    hx, hy = ix - ir * 0.38 * (-1 if flip else 1), iy - ir * 0.42
    hl = inside & (((X - hx) / (ir * 0.3)) ** 2 + ((Y - hy) / (ir * 0.24)) ** 2 <= 1)
    paint(hl, '#ffffff')
    h2 = inside & (((X - (ix + ir * 0.35 * (-1 if flip else 1))) / (ir * 0.12)) ** 2 + ((Y - (iy + ir * 0.4)) / (ir * 0.12)) ** 2 <= 1)
    paint(h2, '#ffffff')
    # upper lash: thick band above the lid line, flicking out past the outer corner
    lash_th = max(2.0, w * 0.06)
    ext = (np.abs(u) < 1.12)
    topx = cy - h * 0.55 * (1 - np.clip(np.abs(u), 0, 1) ** 2.2) ** 0.7 + h * 0.08 * u
    lidx = bot - (bot - topx) * max(0.0, min(1.0, open_))
    lashm = ext & (Y >= lidx - lash_th) & (Y < lidx + 1) & (Y <= bot + 1)
    flick = (u > 0.85) & (u < 1.25) & (Y > lidx - lash_th - (u - 0.85) * h * 0.35) & (Y < lidx - (u - 0.85) * h * 0.2)
    paint(lashm | flick, P['lash'])
    # lower lash (partial, outer half)
    low = (np.abs(Y - bot) < 0.8) & (u > 0.1) & (u < 0.95)
    paint(low, P['lash'])
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(a.shape[1], x1), min(a.shape[0], y1)
    if X1 > X0 and Y1 > Y0:
        reg = a[Y0:Y1, X0:X1]
        s2 = sel[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        c2 = col[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        reg[..., :3][s2] = c2[s2]
        reg[..., 3][s2] = 255
    cv.set_arr(a)
    return ix - cv.ox, iy - cv.oy, ir
