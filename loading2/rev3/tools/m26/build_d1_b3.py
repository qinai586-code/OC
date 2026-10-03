import numpy as np, cv2, sys
from yuv import load
P = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
V6 = P + '/v6/cache/f%04d.png'
def frames(name):
    Y, U, V = load('dec/%s_rep.yuv' % name)
    return lambda i: cv2.cvtColor(np.concatenate([Y[i].reshape(-1), U[i].reshape(-1), V[i].reshape(-1)]).reshape(1080, 1280), cv2.COLOR_YUV2BGR_I420)
def preview(fn):
    cap = cv2.VideoCapture(P + '/m26/Claude_MV_Repair_Package/media/previews/' + fn); out = []
    while True:
        ok, fr = cap.read()
        if not ok: return out
        out.append(fr)
def smooth(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
yy, xx = np.mgrid[0:720, 0:1280].astype(np.float32)

def windows(img):
    """the window squares on the paper cards: interiors enclosed by a dark outline, inside a bright card."""
    g = img.astype(np.float32).mean(2)
    card = (g > 150).astype(np.uint8)
    card = cv2.morphologyEx(card, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    loc = cv2.blur(g, (15, 15))
    ink = ((g < loc - 35) & (cv2.dilate(card, np.ones((7, 7), np.uint8)) > 0)).astype(np.uint8)
    ink[:, 640:] = 0                                                                  # the city is left of her face
    cs, hier = cv2.findContours(ink, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    m = np.zeros(g.shape, np.uint8)
    if hier is not None:
        for c, h in zip(cs, hier[0]):
            if h[3] >= 0:                                                             # a hole inside an outline
                x, y, w, hh = cv2.boundingRect(c)
                if 4 <= w <= 30 and 4 <= hh <= 34 and cv2.contourArea(c) >= 12:
                    cv2.drawContours(m, [c], -1, 1, -1)
    return m

# ---- D1: source f8-52 -> timeline 686-730; windows light over 718-730
get = frames('D1_papercity')
lit_prev, g_prev = None, None
for k in range(660, 760):
    if 686 <= k <= 730:
        img = get(k - 686 + 8).astype(np.float32)
        g_now = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        wl = smooth((k - 716) / 12.0)
        if wl > 0:
            m = windows(img.astype(np.uint8)).astype(np.float32)
            # light them in an order that is fixed across frames (left to right, a few at a time)
            frac = np.clip((xx / 640.0) * 0.6 + 0.4 - (1 - wl) * 1.2, 0, 1)
            m = m * smooth(frac / 0.4)
            if lit_prev is not None:                                                     # a lit window stays lit: carried by optical flow
                fl = cv2.calcOpticalFlowFarneback(g_now, g_prev, None, 0.5, 4, 15, 3, 5, 1.2, 0)
                carried = cv2.remap(lit_prev, xx + fl[..., 0], yy + fl[..., 1], cv2.INTER_LINEAR)
                m = np.maximum(m, carried * (cv2.dilate(m, np.ones((3, 3), np.uint8)) * 0 + 1))
            lit_prev = m.copy()
            m = m * wl
            core = cv2.GaussianBlur(m, (0, 0), 0.8)
            img = img * (1 - core[..., None]) + core[..., None] * np.array([110, 215, 255], np.float32)
            img = img + cv2.GaussianBlur(m, (0, 0), 6.0)[..., None] * np.array([30, 90, 160], np.float32)
            # restrained warm light from the windows on her near face and hair (the side facing the city)
            near = np.exp(-((xx - 640) ** 2 + (yy - 470) ** 2) / (2 * 230.0 ** 2)) * smooth((xx - 600) / 60.0)
            img = img * (1 + (0.16 * wl * near)[..., None] * np.array([0.45, 0.85, 1.2], np.float32))
        g_prev = g_now
    else:
        img = cv2.imread(V6 % k).astype(np.float32)
    cv2.imwrite(P + '/m26/d1_cand/f%04d.png' % k, np.clip(img, 0, 255).astype(np.uint8))
pv = preview('preview_D1_trim_src1.0-2.833_45f.mp4')
for k in range(660, 760):
    cv2.imwrite(P + '/m26/d1_before/f%04d.png' % k, pv[k - 686] if 686 <= k <= 730 else cv2.imread(V6 % k))

# ---- B3: source f42-84 -> timeline 819-861 (open, one slow closure, closed hold)
get = frames('B3_eyeclosure')
for k in range(792, 889):
    img = get(k - 819 + 42) if 819 <= k <= 861 else cv2.imread(V6 % k)
    cv2.imwrite(P + '/m26/b3_cand/f%04d.png' % k, img)
pv = preview('preview_B3_trim_src1.917-3.667_43f.mp4')
for k in range(792, 889):
    cv2.imwrite(P + '/m26/b3_before/f%04d.png' % k, pv[k - 819] if 819 <= k <= 861 else cv2.imread(V6 % k))
print('done')
