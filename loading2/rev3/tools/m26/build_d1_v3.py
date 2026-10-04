"""D1 (686-730, 28.583-30.417), v9: event -> reaction -> result, all in the source's own order and speed.

Source f0-44 (round 2 used f20-64, round 1 f8-52; both started after or on the event):
  src  0-8   the paper strip lies dim and out of focus; B looks down at it, in cool night light
  src  9-11  the strip brightens (the source's own change: bright pixels in its region 545 -> 7141)   EVENT  (28.96 s)
  src 12-17  B blinks                                                                               REACTION
  src 18-27  her eyes move down to the strip                                                        REACTION
  src 24-44  the cards rise out of the strip; their windows light (added, as in round 2)            RESULT
Added (local light only, no added motion): the strip's brightening is carried as a warm front running along the strip
(src 7-12) so it reads as an event; B's near side warms with the strip's light, 3 frames behind it, then with the
windows. Window detection and flow use round 2's decode so window shapes are unchanged."""
import os, numpy as np, cv2
from yuv import load, hq_bgr
from build_d1_b3 import windows, smooth, xx, yy
P = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
OUTD = os.environ.get('D1_OUT', P + '/v9/op')
Y, U, V = load('dec/D1_papercity_rep.yuv')
OFF = 686


def get_v7(i):
    return cv2.cvtColor(np.concatenate([Y[i].reshape(-1), U[i].reshape(-1), V[i].reshape(-1)]).reshape(1080, 1280), cv2.COLOR_YUV2BGR_I420)


bmask = smooth((xx - 600.0) / 60.0)
near = np.exp(-((xx - 640) ** 2 + (yy - 470) ** 2) / (2 * 230.0 ** 2)) * smooth((xx - 600) / 60.0)
COOL = np.array([0.95, 0.80, 0.72], np.float32)
# the strip's axis (measured on src 0-8: from about (100, 690) to (640, 450))
A0, A1 = np.array([100.0, 690.0]), np.array([640.0, 450.0])
ax = (A1 - A0) / np.linalg.norm(A1 - A0)
along = ((xx - A0[0]) * ax[0] + (yy - A0[1]) * ax[1]) / np.linalg.norm(A1 - A0)       # 0 at the left end, 1 at the right
lit_prev, g_prev, counts, strip_l = None, None, {}, {}
for k in range(686, 731):
    s = k - OFF
    img = hq_bgr(Y, U, V, s).astype(np.float32)
    det = get_v7(s)
    g_now = cv2.cvtColor(det, cv2.COLOR_BGR2GRAY)
    # the strip (and later the rising cards): warm bright paper left of her
    lum = img.mean(2)
    paper = np.clip((lum - 45.0) / 60.0, 0, 1) * (1 - bmask) * (img[..., 2] > img[..., 0])
    front = smooth((s - 7) / 5.0) * 1.15 - along                                         # the warm front runs left -> right
    run = np.clip(smooth(front / 0.25), 0, 1) * (1 - 0.6 * smooth((s - 26) / 10.0))     # fades as the cards take the light
    add = paper * run
    img = img * (1 + (0.30 * add)[..., None] * np.array([0.55, 0.85, 1.15], np.float32))
    img = img + cv2.GaussianBlur(add, (0, 0), 10.0)[..., None] * np.array([10, 28, 52], np.float32)
    strip_l[k] = float(add.sum())
    # windows (as round 2), from src 32 when the cards stand
    wl = smooth((k - 718) / 12.0)
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
    # her light: from the strip (3 frames behind it), then from the windows
    kw = float(np.clip(0.55 * strip_l.get(k - 3, 0.0) / 9000.0 + counts.get(k - 3, 0.0) / 1800.0, 0, 1)) ** 0.8
    gain = COOL + (1 - COOL) * kw
    img = img * (1 - bmask[..., None] + bmask[..., None] * gain)
    img = img * (1 + (0.16 * kw * near)[..., None] * np.array([0.45, 0.85, 1.2], np.float32))
    if wl > 0:
        core = cv2.GaussianBlur(lit, (0, 0), 0.8)
        img = img * (1 - core[..., None]) + core[..., None] * np.array([110, 215, 255], np.float32)
        img = img + cv2.GaussianBlur(lit, (0, 0), 6.0)[..., None] * np.array([30, 90, 160], np.float32)
    cv2.imwrite(OUTD + '/f%04d.png' % k, np.clip(np.round(img), 0, 255).astype(np.uint8))
print('strip light', {k: int(v) for k, v in strip_l.items() if k % 3 == 0})
print('windows', {k: int(v) for k, v in counts.items() if k % 3 == 0 and v > 0})
