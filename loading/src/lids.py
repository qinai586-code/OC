"""B's eyelid (KV4): a column-wise lid warp built from hand-placed eye geometry.
c = 0 open (as painted), ~0.35 lowered gaze, 1 closed."""
import numpy as np
import cv2
from common import *

OX, OY = 1640, 560          # crop origin of the eye geometry in plate px
X0, X1 = 6, 232             # eye extent (crop px), inner -> outer corner


def y_lash(x):              # lower edge of the upper lash band
    return 195.0 - (x - 25.0) * (77.0 / 190.0)


def y_bot(x):               # lower lid line
    return np.where(x < 160, 205.0 + (x - 20.0) * (80.0 / 140.0), 285.0 - (x - 160.0) * (35.0 / 55.0))


def lid_warp(img, c, w=440, h=340):
    """Return img (plate) with B's upper lid lowered by fraction c."""
    if c <= 1e-3:
        return img
    roi = img[OY:OY + h, OX:OX + w]
    xs = np.arange(w, dtype=np.float32)
    yl = y_lash(xs)
    yb = np.maximum(y_bot(xs), yl + 4)
    band = np.clip(24.0 - (xs - 25.0) * (10.0 / 190.0), 10, 26)
    ytop = yl - band - 60.0
    ylnew = yl + c * (yb - yl) * 0.97
    bnew = band * (1 - 0.45 * c)            # the lash band thins as it closes
    ys = np.arange(h, dtype=np.float32)[:, None]
    YT, YL, YB, YN = ytop[None], yl[None], yb[None], ylnew[None]
    B0, B1 = (yl - band)[None], (ylnew - bnew)[None]
    src = ys.copy().repeat(w, 1)
    sk = (ys >= YT) & (ys < B1)              # lid skin stretches
    src = np.where(sk, YT + (ys - YT) * (B0 - YT) / (B1 - YT + 1e-6), src)
    bd = (ys >= B1) & (ys < YN)              # lash band keeps (thinned) thickness
    src = np.where(bd, B0 + (ys - B1) * (YL - B0) / (YN - B1 + 1e-6), src)
    lo = (ys >= YN) & (ys <= YB)             # iris and white compress under the lid
    src = np.where(lo, YL + (ys - YN) * (YB - YL) / (YB - YN + 1e-3), src)
    # feather the warp out at the corners
    fx_ = np.clip(np.minimum(xs - X0, X1 - xs) / 18.0, 0, 1)[None]
    src = ys + (src - ys) * fx_
    mapx = np.repeat(xs[None], h, 0)
    out = img.copy()
    warped = cv2.remap(roi, mapx, src.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if False and c > 0.85:
        # the closed lid: lashes meet into one line along the lower lid
        k = smooth(c, 0.85, 1.0)
        line = np.zeros((h, w), np.float32)
        pts = [(x, float(y_bot(np.float32(x))) - 3) for x in range(10, 228, 4)]
        pts = np.array(pts, np.float32)
        cv2.polylines(line, [(pts * 4).astype(np.int32)], False, 1.0, 9, cv2.LINE_AA, shift=2)
        line = gblur(line, 0.8) * k
        lash = np.array([0.22, 0.13, 0.12], np.float32)
        warped = warped * (1 - line[:, :, None] * 0.9) + lash * line[:, :, None] * 0.9
    out[OY:OY + h, OX:OX + w] = warped
    return out
