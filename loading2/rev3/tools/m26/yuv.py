import numpy as np
W_, H_ = 1280, 720
FS = W_ * H_ * 3 // 2
def load(path):
    raw = np.fromfile(path, np.uint8)
    n = raw.size // FS
    raw = raw[:n * FS].reshape(n, FS)
    Y = raw[:, :W_ * H_].reshape(n, H_, W_)
    U = raw[:, W_ * H_:W_ * H_ * 5 // 4].reshape(n, H_ // 2, W_ // 2)
    V = raw[:, W_ * H_ * 5 // 4:].reshape(n, H_ // 2, W_ // 2)
    return Y, U, V


# Clarity round: OpenCV's COLOR_YUV2BGR_I420 repeats each chroma sample over a 2x2 block (blocky colour edges) and
# rounds to 8 bits. hq_bgr() keeps the same BT.601 limited-range matrix (so colours match earlier rounds) but
# interpolates U/V with a cubic at the sources' measured chroma position (centred between luma columns and
# rows) and returns float32 without rounding. The chroma position was measured, not assumed: in all three Seedance
# sources the colour edges line up best with the luma edges for centred siting (chroma sample i at luma 2i + 0.5 on
# both axes), not the MPEG-2 default (co-sited horizontally).
_GRID = None


def hq_bgr(Y, U, V, i):
    global _GRID
    import cv2
    h, w = Y.shape[1:]
    if _GRID is None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _GRID = ((xx - 0.5) / 2.0, (yy - 0.5) / 2.0)
    cx, cy = _GRID
    u = cv2.remap(U[i].astype(np.float32), cx, cy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE) - 128.0
    v = cv2.remap(V[i].astype(np.float32), cx, cy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE) - 128.0
    y = 1.164383 * (Y[i].astype(np.float32) - 16.0)
    return np.dstack([y + 2.017232 * u, y - 0.391762 * u - 0.812968 * v, y + 1.596027 * v]).astype(np.float32)
