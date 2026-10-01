"""Per-plate preparation: emissive layers, clean plates, character layers."""
import sys
from engine import *


def shift_fill(img, remove, protect, shifts=(-240, -380, -520, -680, -840, -1000), lowfreq=40):
    h, w = remove.shape
    out = img.copy()
    todo = remove > 0.5
    bad = (remove > 0.5) | (protect > 0)
    filled = np.zeros_like(todo)
    for dx in shifts:
        src_bad = np.roll(bad, -dx, axis=1)
        if dx > 0:
            src_bad[:, w - dx:] = True
        else:
            src_bad[:, :-dx] = True
        ok = todo & ~filled & ~src_bad
        sh = np.roll(img, -dx, axis=1)
        out[ok] = sh[ok]
        filled |= ok
    left = todo & ~filled
    if left.any():
        wgt = gblur((~bad).astype(np.float32), 25)
        acc = gblur(img * (~bad)[:, :, None], 25)
        out[left] = (acc / (wgt[:, :, None] + 1e-4))[left]
    keep = ((remove <= 0.5) & (protect <= 0)).astype(np.float32)
    tgt = gblur(img * keep[:, :, None], lowfreq) / (gblur(keep, lowfreq)[:, :, None] + 1e-4)
    out = out - gblur(out, lowfreq) + tgt
    f = gblur(remove.astype(np.float32), 4)[:, :, None]
    return img * (1 - f) + out * f


def kv3(name='KV3'):
    P = Plate(name)
    img = P.img
    op = cv2.morphologyEx(img, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    th = np.clip(img - op, 0, 1)
    sky = np.zeros(img.shape[:2], np.float32)
    sky[:1120] = 1
    ca = P.char_alpha if P.char_alpha is not None else Plate('KV3').char_alpha
    sky = sky * (1 - cv2.dilate((ca > 0.05).astype(np.uint8), np.ones((31, 31), np.uint8)))
    # keep the left/right ruins' leaves out
    sky[620:, :460] = 0     # ivy on the left ruin
    sky[620:, 2680:] = 0    # right ruin
    const = th * sky[:, :, None]
    l = lum(const)
    const = const * smoothstep(0.03, 0.08, l)[:, :, None]
    l = lum(const)
    # points = compact bright blobs; lines = thin remainder
    pk = (l > 0.28).astype(np.uint8)
    pts_mask = cv2.morphologyEx(pk, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    pts_mask = cv2.dilate(pts_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(np.float32)
    pts_mask = gblur(pts_mask, 1.5)
    points = const * pts_mask[:, :, None]
    lines = const * (1 - pts_mask[:, :, None])
    # sky estimate without the constellation: masked normalized convolution (the constellation
    # sits on open sky, so a smooth estimate is the true background there)
    cm = cv2.dilate((lum(const) > 0.02).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))).astype(np.float32) * sky
    keep = 1 - cm
    est = gblur(img * keep[:, :, None], 45) / (gblur(keep, 45)[:, :, None] + 1e-4)
    rng = np.random.default_rng(2)
    tex = gblur(rng.normal(0, 1, img.shape[:2]).astype(np.float32), 0.9)[:, :, None] * 0.008
    f = gblur(cm, 10)[:, :, None]
    clean = img * (1 - f) + (est + tex) * f
    const = np.clip(img - clean, 0, 1) * sky[:, :, None]
    lines = np.clip(const - points, 0, 1)
    n, lab, st, cen = cv2.connectedComponentsWithStats((l > 0.28).astype(np.uint8), 8)
    centers = [(float(cen[i][0]), float(cen[i][1]), float(st[i, 4])) for i in range(1, n)]
    np.save(work('derived', f'{name}_const_points.npy'), points.astype(np.float16))
    np.save(work('derived', f'{name}_const_lines.npy'), lines.astype(np.float16))
    np.save(work('derived', f'{name}_sky_clean.npy'), clean.astype(np.float16))
    np.save(work('derived', f'{name}_const_centers.npy'), np.array(centers, np.float32))
    print(name, 'const points', len(centers))


def char_band_clean(name, band=110, shifts=(-240, -380, -520, -680, -840, -1000)):
    """Background behind a character, rebuilt only in the band that parallax can reveal."""
    P = Plate(name)
    a = P.char_alpha
    outer = cv2.dilate((a > 0.03).astype(np.uint8), np.ones((11, 11), np.uint8))
    inner = cv2.erode((a > 0.5).astype(np.uint8), np.ones((band * 2 + 1, band * 2 + 1), np.uint8))
    remove = (outer & (1 - inner)).astype(np.float32)
    clean = shift_fill(P.img, remove, inner, shifts=shifts)
    np.save(work('derived', f'{name}_bandclean.npy'), clean.astype(np.float16))
    print(name, 'band clean')


def kv5():
    P = Plate('KV5')
    img = P.img
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    fc = (1355.0, 1190.0)
    r = np.hypot(xs - fc[0], ys - fc[1])
    # 1) the flame itself -> inpaint the dark skirt behind it
    box = np.zeros((h, w), np.uint8)
    box[1050:1285, 1270:1450] = 1
    fl = ((lum(img) > 0.30) & (box > 0)).astype(np.uint8)
    fl = cv2.dilate(fl, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    inp = cv2.inpaint(u8, fl, 6, cv2.INPAINT_NS).astype(np.float32) / 255.
    rng = np.random.default_rng(4)
    f = gblur(fl.astype(np.float32), 2)[:, :, None]
    inp = inp + gblur(rng.normal(0, 1, (h, w)).astype(np.float32), 1.0)[:, :, None] * 0.006 * f
    # 2) the flame's light on everything around it
    L = 0.80 * np.exp(-(r / 190.0) ** 2) + 0.25 * np.exp(-(r / 620.0) ** 2)
    s = np.array([0.50, 0.44, 0.30], np.float32)
    unlit = inp * (1 - L[:, :, None] * s)
    # keep the faraway night untouched
    np.save(work('derived', 'KV5_unlit.npy'), unlit.astype(np.float16))
    np.save(work('derived', 'KV5_flamemask.npy'), gblur(fl.astype(np.float32), 3).astype(np.float16))
    # 3) the hill fire and its paths (emissive layer over the dark land)
    land = np.zeros((h, w), np.float32)
    land[1150:, 1850:] = 1
    land[1520:, :2120] = 0      # the ledge's own plants are not paths
    land *= (1 - cv2.dilate((P.char_alpha > 0.05).astype(np.uint8), np.ones((25, 25), np.uint8)))
    op = cv2.morphologyEx(unlit, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    th = np.clip(unlit - op, 0, 1)
    warm = np.clip((th[:, :, 0] - th[:, :, 2]) * 6, 0, 1)
    em = th * (warm * land)[:, :, None]
    # the fire's own halo
    fr = np.hypot(xs - 2303, ys - 1452)
    halo = np.clip(unlit - gblur(op, 2), 0, 1) * (fr < 90)[:, :, None]
    em = np.maximum(em, halo * 0.9)
    dark = np.clip(unlit - em, 0, 1)
    np.save(work('derived', 'KV5_hill_emis.npy'), em.astype(np.float16))
    np.save(work('derived', 'KV5_dark.npy'), dark.astype(np.float16))
    print('kv5 ok')


if __name__ == '__main__':
    for a in sys.argv[1:]:
        if a.startswith('KV3'):
            kv3(a)
        if a == 'KV5':
            kv5()
        if a.startswith('band:'):
            char_band_clean(a[5:])
