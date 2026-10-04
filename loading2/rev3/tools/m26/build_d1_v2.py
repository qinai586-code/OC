"""D1 (686-730) round 2: source f20-64 at original speed (src = k - 666). The city unfolds from the first frames;
windows light left to right (k 700-714); B starts in cool night light and her face, hair and near side warm only as the
lit-window count grows (light caused by the windows, lagging them slightly). A per-channel multiply only: no blur, no
added motion. Window light persists frame to frame along optical flow."""
import os, numpy as np, cv2
from yuv import load, hq_bgr
from build_d1_b3 import windows, smooth, xx, yy
P = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
V6 = P + '/v6/cache/f%04d.png'
Y, U, V = load('dec/D1_papercity_rep.yuv')
HQ = os.environ.get('D1_HQ', '1') == '1'           # clarity round: cubic chroma at the measured siting, no 8-bit rounding
OUTD = os.environ.get('D1_OUT', P + ('/v8/op' if HQ else '/m27/d1'))
def get_v7(i):
    return cv2.cvtColor(np.concatenate([Y[i].reshape(-1), U[i].reshape(-1), V[i].reshape(-1)]).reshape(1080, 1280), cv2.COLOR_YUV2BGR_I420)
def get(i):
    return hq_bgr(Y, U, V, i) if HQ else get_v7(i)
def u8(x):
    return np.clip(np.round(x), 0, 255).astype(np.uint8)
OFF = 666
bmask = smooth((xx - 600.0) / 60.0)                                                     # B: her face, hair and shoulder (right of the city)
near = np.exp(-((xx - 640) ** 2 + (yy - 470) ** 2) / (2 * 230.0 ** 2)) * smooth((xx - 600) / 60.0)
COOL = np.array([0.97, 0.80, 0.72], np.float32)                                         # BGR: night, before the windows light
lit_prev, g_prev, counts = None, None, {}
for k in range(686, 731):
    img = get(k - OFF).astype(np.float32)
    det = get_v7(k - OFF)                       # window detection and flow on round 2's decode: the same lit windows
    g_now = cv2.cvtColor(det, cv2.COLOR_BGR2GRAY)
    wl = smooth((k - 700) / 14.0)
    lit = np.zeros((720, 1280), np.float32)
    if wl > 0:
        m = windows(det).astype(np.float32)
        frac = np.clip((xx / 640.0) * 0.6 + 0.4 - (1 - wl) * 1.2, 0, 1)
        m = m * smooth(frac / 0.4)
        if lit_prev is not None:
            fl = cv2.calcOpticalFlowFarneback(g_now, g_prev, None, 0.5, 4, 15, 3, 5, 1.2, 0)
            m = np.maximum(m, cv2.remap(lit_prev, xx + fl[..., 0], yy + fl[..., 1], cv2.INTER_LINEAR))
        lit_prev = m.copy()
        lit = m * wl
    counts[k] = float(lit.sum())
    g_prev = g_now
    # her light follows the windows: warmth = lit window area so far (normalised), lagging by 3 frames
    lag = counts.get(k - 3, 0.0)
    kw = float(np.clip(lag / 1800.0, 0, 1)) ** 0.8
    gain = COOL + (1 - COOL) * kw
    img = img * (1 - bmask[..., None] + bmask[..., None] * gain)
    img = img * (1 + (0.16 * kw * near)[..., None] * np.array([0.45, 0.85, 1.2], np.float32))
    if wl > 0:
        core = cv2.GaussianBlur(lit, (0, 0), 0.8)
        img = img * (1 - core[..., None]) + core[..., None] * np.array([110, 215, 255], np.float32)
        img = img + cv2.GaussianBlur(lit, (0, 0), 6.0)[..., None] * np.array([30, 90, 160], np.float32)
    cv2.imwrite(OUTD + '/f%04d.png' % k, u8(img) if HQ else np.clip(img, 0, 255).astype(np.uint8))
print({k: int(v) for k, v in counts.items() if k % 3 == 0})
