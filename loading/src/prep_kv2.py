"""Cut KV2's floating windows into sprites (core + additive glow) and rebuild the sky behind them."""
import pickle
from scipy import ndimage
from engine import *


def shift_fill(img, remove, protect, shifts=(-240, -380, -520, -680, -840, -1000)):
    """Fill removed pixels by borrowing the same rows from a neighbouring stretch (sky and
    horizon run horizontally, so texture continues naturally)."""
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
    # anything left: normalized blur
    left = todo & ~filled
    if left.any():
        wgt = gblur((~bad).astype(np.float32), 25)
        acc = gblur(img * (~bad)[:, :, None], 25)
        out[left] = (acc / (wgt[:, :, None] + 1e-4))[left]
    # match low frequencies to the surrounding sky so borrowed rows don't show as bands
    keep = (~(remove > 0.5)).astype(np.float32)
    tgt = gblur(img * keep[:, :, None], 40) / (gblur(keep, 40)[:, :, None] + 1e-4)
    out = out - gblur(out, 40) + tgt
    f = gblur(remove, 4)[:, :, None]
    return img * (1 - f) + out * f


def build():
    P = Plate('KV2')
    img = P.img
    hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    v = hsv[:, :, 2] / 255.
    hh = hsv[:, :, 0] * 2
    bright = ((v > 0.40) & (hh > 8) & (hh < 62)).astype(np.uint8)
    corridor = np.zeros(bright.shape, np.uint8)
    corridor[:700, :1600] = 1                   # open sky only: low windows stay painted in place
    # never touch A (foreground): exclude near-depth pixels
    near = (gblur(P.depth, 2) > 0.55).astype(np.uint8)
    near = cv2.dilate(near, np.ones((15, 15), np.uint8))
    corridor = corridor * (1 - near)
    cand = cv2.dilate(bright * corridor, np.ones((9, 9), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(cand, 8)
    # background estimate for glow separation: heavy median of the sky
    bg_l = cv2.medianBlur((lum(img) * 255).astype(np.uint8), 31).astype(np.float32) / 255.
    sprites = []
    remove = np.zeros(bright.shape, np.float32)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 70 or y + h > 700:
            continue
        m = int(max(10, 0.35 * max(w, h)))
        x0, y0 = max(0, x - m), max(0, y - m)
        x1, y1 = min(img.shape[1], x + w + m), min(img.shape[0], y + h + m)
        crop = img[y0:y1, x0:x1].copy()
        b = (bright[y0:y1, x0:x1] & (lab[y0:y1, x0:x1] == i)).astype(np.uint8)
        cnts, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        core = np.zeros(b.shape, np.uint8)
        if cnts:
            hull = cv2.convexHull(np.vstack(cnts))
            cv2.fillConvexPoly(core, hull, 1)
        core = core.astype(np.float32)
        # include the dark window frame around the light (a few px)
        core = cv2.dilate(core, np.ones((5, 5), np.uint8)).astype(np.float32) if max(w, h) > 40 else core
        core = gblur(core, 0.8)
        excess = np.clip(lum(crop) - bg_l[y0:y1, x0:x1] - 0.015, 0, 1)
        glow = crop * np.clip(excess / (lum(crop) + 1e-3), 0, 1)[:, :, None]
        glow = glow * (1 - core[:, :, None])
        sprites.append(dict(x=x0, y=y0, rgb=crop.astype(np.float16), core=core.astype(np.float16), glow=glow.astype(np.float16),
                            box=(int(x), int(y), int(w), int(h)), area=int(a)))
        remove[y0:y1, x0:x1] = 1.0
    remove = remove * (1 - near)
    prot = cv2.dilate(((gblur(P.depth, 2) > 0.33) | (P.char_alpha > 0.05)).astype(np.uint8), np.ones((41, 41), np.uint8))
    clean = shift_fill(img, remove, prot)
    np.save(work('derived', 'KV2_windows_clean.npy'), clean.astype(np.float16))
    with open(work('derived', 'KV2_sprites.pkl'), 'wb') as f:
        pickle.dump(sprites, f)
    print(len(sprites), 'sprites')
    big = sorted(sprites, key=lambda s: -s['area'])[:12]
    for s in big:
        print(s['box'], s['area'])
    im = clean.copy()
    imwrite(work('derived', 'KV2_windows_clean_check.jpg'), cv2.resize(im[:1400, :1700], (850, 700)))


if __name__ == '__main__':
    build()
