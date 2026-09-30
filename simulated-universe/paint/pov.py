"""What A sees: the human world renders only where she looks (0:10.24-0:11.98).

A simulated universe computes what is observed. Here that is literal: her gaze travels
from one lit window to the next ("we met you in fragments") and each paints itself in:
pencil, then flat colour, then paint. What she has looked at stays painted. A pencil
fragment of the lyric writes itself on the page. The shot opens by dissolving out of the
night page she is looking down at: we go into the page.
"""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import k4_3am
from painter import W as PW, H as PH

W, H, FPS = 1280, 720, 30
T0, T1 = 10.24, 11.981
S = k4_3am.s
S.render()                                                           # builds the cached layers once
# where her gaze lands, in page pixels: lit windows (a screen at 3 a.m., a lamp, a high window)
GAZE = [(10.24, (690, 660)), (10.80, (910, 770)), (11.36, (1110, 225))]
yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
BLOBS = [np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 150.0 ** 2)) for _, (x, y) in GAZE]
FONT = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf', 46)

def attention(t):
    a = 0.12 * S.attn                                                 # a trace of the scene's own lit screens
    for (tg, _), blob in zip(GAZE, BLOBS):
        a = a + blob * float(np.clip((t - tg) / 0.45, 0, 1)) ** 0.8 * 1.05
    return a

def gaze_point(t):
    pts = [p for tg, p in GAZE if t >= tg] or [GAZE[0][1]]
    k = sum(t >= tg for tg, _ in GAZE) - 1
    if 0 <= k < len(GAZE) - 1:                                        # the eye travels ahead of the paint
        u = np.clip((t - GAZE[k][0]) / (GAZE[k + 1][0] - GAZE[k][0]), 0, 1)
        u = u * u * (3 - 2 * u)
        return np.array(GAZE[k][1]) * (1 - u) + np.array(GAZE[k + 1][1]) * u
    return np.array(pts[-1], float)

def pencil_text(img, text, xy, t, t0, dur=0.8):
    """The lyric fragment writes itself, left to right, in graphite."""
    lay = Image.new('L', img.size, 0); d = ImageDraw.Draw(lay)
    d.text(xy, text, font=FONT, fill=255)
    m = np.asarray(lay, np.float32) / 255
    x0, _, x1, _ = lay.getbbox() or (0, 0, 1, 1)
    reveal = x0 + (x1 - x0) * float(np.clip((t - t0) / dur, 0, 1))
    m = m * (np.arange(img.size[0])[None, :] < reveal)
    a = np.asarray(img, np.float32) / 255
    a = a * (1 - 0.75 * m[..., None]) + np.array([0.24, 0.23, 0.26]) * 0.75 * m[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def render(i, t, s, night_frame=None):
    page = S.render(attn=attention(t))
    page = pencil_text(page, 'translated, compressed', (1180, 470), t, 11.0)
    # camera: push toward where she is looking
    g = gaze_point(t); u = np.clip((t - T0) / (T1 - T0), 0, 1)
    sc = 0.78 + 0.16 * u                                              # output px per page px
    cx = PW / 2 + (g[0] - PW / 2) * 0.45; cy = PH / 2 + (g[1] - PH / 2) * 0.45
    M = np.float32([[sc, 0, W / 2 - cx * sc], [0, sc, H / 2 - cy * sc]])
    fr = cv2.warpAffine(np.asarray(page, np.float32) / 255, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)
    # night grade toward the edges: the page is lit where she looks
    gx, gy = M @ np.array([g[0], g[1], 1.0])
    vy, vx = np.ogrid[0:H, 0:W]
    lamp = np.exp(-(((vx - gx) / (0.55 * W)) ** 2 + ((vy - gy) / (0.60 * H)) ** 2))[..., None]
    fr = fr * (0.38 + 0.62 * lamp) * np.array([1.0, 0.96, 0.9])
    if night_frame is not None:                                       # we go into the page
        k = float(np.clip((t - T0) / 0.25, 0, 1))
        fr = night_frame * (1 - k) + fr * k
    fr = fr + np.random.default_rng(int(round(s * FPS))).normal(0, 0.010, (H, W, 1))
    return (np.clip(fr, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)
