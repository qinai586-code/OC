"""REV3 singing close-up, 0:52.42-0:56.29 of the locked track (same excerpt as the v2 baseline).

Changes from the baseline (tools/test2_sing.py):
- Composition: an over-the-shoulder close-up. A sings the question to B; B's out-of-focus hair and
  shoulder (from the kv4_B drawing) fill the right of frame. The frame's left edge cuts inside A's
  clean hair. The straight crop edges of the source head are therefore never in frame.
- Matte: re-made from the white-background source with rev3/tools/matte.py, so there is no white
  fringe and no paper between strands.
- Mouths: chosen from the sounds of the author text, timed to measured landmarks in the vocal stem
  (rev3/docs/phoneme_evidence.png). Teeth only on f, v and s, using a narrowed "I" drawing. No smile
  drawing. Mouths change one frame before the sound and hold on twos.
- Anatomy: the chin and jaw contour drop with the open vowels (A 7 px, E 3 px, U 2 px at hd scale).
- Performance: the head lifts into the stressed "SIM" and settles on "verse". Breath and hair lag
  follow the head. Eyes stay on B (no blinking is forced).
- Light: night ambient, a warm uplight from the note between them (frame right, below), and a cool
  sky rim.

  python3 rev3/tools/sing.py   -> rev3/tests/REV3_singing_closeup.mp4 (+ frames in rev3/work/sing)
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from matte import load_rgba  # noqa: E402

AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
IMG = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/images'
KV1 = '/home/user/OC/loading/work/plates/KV1.png'
KV4B = '/home/user/OC/loading2/work/chars/kv4_B.png'
OUTD = os.path.join(R, 'work', 'sing')
MP4 = os.path.join(R, 'tests', 'REV3_singing_closeup.mp4')
os.makedirs(OUTD, exist_ok=True)
FPS, OW, OH = 24, 1920, 1080
T0, T1 = 52.42, 56.29
F0, F1 = int(round(T0 * FPS)), int(round(T1 * FPS))       # 1258 .. 1351 (93 frames)

# ---------------------------------------------------------------- head + mouth assets
head = load_rgba(os.path.join(R, 'assets', 'A_front_head.png'))   # 964 x 1212, hd scale
H, W = head.shape[:2]
# measured on the drawing: chin tip (522, 945), jaw midpoints x~521 -> the face's centre line is x=521.
# The drawing's own mouth is a small slanted stroke at (535-545, 855); it is painted out, and every new
# mouth is centred on the face axis (the v2/first rev3 anchor x=538 sat 17 px off-centre).
FACE_X = 521
MX, MY = FACE_X, 855
reg = np.zeros((H, W), np.uint8)
cv2.rectangle(reg, (538 - 34, MY - 12), (538 + 34, MY + 12), 255, -1)
rgb8 = (np.clip(head[:, :, :3], 0, 1) * 255).astype(np.uint8)
paint = cv2.inpaint(rgb8, reg, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255.0
mouthless = head.copy()
mouthless[:, :, :3] = np.where(reg[:, :, None] > 0, paint, head[:, :, :3])
CHECK = {'mouthless_changed_px': int((np.abs(mouthless - head).max(2) > 1e-6).sum()),
         'mouthless_region_px': int((reg > 0).sum()),
         'mouthless_max_change_outside': float(np.abs(mouthless - head)[reg == 0].max())}

chart = cv2.imread(os.path.join(IMG, '6.webp'))[:, :, ::-1].astype(np.float32) / 255.0
ink = 1 - chart.min(2)
m = cv2.morphologyEx((ink > 0.06).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(m)
comps = sorted([i for i in range(1, n) if st[i, 4] > 150], key=lambda i: (round(cen[i][1] / 200), cen[i][0]))
assert len(comps) == 8
NAMES = ['closed', 'smile', 'small', 'A', 'I', 'U', 'E', 'O']
SP = {}
for name, i in zip(NAMES, comps):
    x, y, w, h = st[i, :4]
    p = 10
    crop = chart[y - p:y + h + p, x - p:x + w + p].copy()
    d = 1 - crop.min(2)
    ff = (d < 0.05).astype(np.uint8)
    mk = np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8)
    for sx, sy in ((0, 0), (ff.shape[1] - 1, 0), (0, ff.shape[0] - 1), (ff.shape[1] - 1, ff.shape[0] - 1)):
        cv2.floodFill(ff, mk, (sx, sy), 2)
    alpha = np.where(ff == 2, np.clip(d / 0.25, 0, 1), 1.0).astype(np.float32)
    a3 = np.maximum(alpha[:, :, None], 1e-3)
    rgb = np.clip((crop - (1 - a3)) / a3, 0, 1)
    SP[name] = np.dstack([rgb, alpha]).astype(np.float32)
# teeth for f / v / s: the "I" drawing narrowed (less spread, so it does not read as a grin)
i_sp = SP['I']
SP['F'] = cv2.resize(i_sp, (int(i_sp.shape[1] * 0.68), int(i_sp.shape[0] * 0.85)), interpolation=cv2.INTER_AREA)
# sung E: the chart drawing narrowed a little so the vowel does not read as a held smile
e_sp = SP['E']
SP['E'] = cv2.resize(e_sp, (int(e_sp.shape[1] * 0.84), e_sp.shape[0]), interpolation=cv2.INTER_AREA)
# anime proportions on this face (width at mouth level ~336 px): open A ~1/5 of it, closed line ~1/8


def desmile(sp, c):
    """Lower the mouth corners by c * height (parabolic), so a spread vowel / teeth shape stops reading as a grin."""
    h, w = sp.shape[:2]
    yy_, xx_ = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx_ - (w - 1) / 2.0) / ((w - 1) / 2.0)
    dy = c * h * u * u
    pad = int(np.ceil(c * h)) + 2
    src = cv2.copyMakeBorder(sp, 0, pad, 0, 0, cv2.BORDER_CONSTANT, value=0)
    yy2, xx2 = np.mgrid[0:h + pad, 0:w].astype(np.float32)
    u2 = (xx2 - (w - 1) / 2.0) / ((w - 1) / 2.0)
    return cv2.remap(src, xx2, yy2 - c * h * u2 * u2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


SP['F'] = desmile(SP['F'], 0.16)
SP['E'] = desmile(SP['E'], 0.10)
SCALE = 0.38
SCALE_XY = {'A': (0.38, 0.33), 'O': (0.38, 0.33)}
JAW = {'A': 7.0, 'O': 6.0, 'E': 3.0, 'U': 2.0, 'small': 1.5}

# ---------------------------------------------------------------- viseme track (sound onsets, s)
# author text: "What if we live in a simulated universe:" - landmarks from rev3/docs/phoneme_evidence.png
TRACK = [
    (52.40, 'U', 'w'), (52.47, 'A', 'a (What)'), (52.64, 'small', 't'), (52.70, 'small', 'i (if)'), (52.76, 'F', 'f'),
    (52.86, 'U', 'w (we)'), (52.92, 'E', 'ee'), (53.12, 'small', 'l'), (53.18, 'small', 'i (live)'), (53.30, 'F', 'v'),
    (53.45, 'small', 'in'), (53.58, 'E', 'a'), (53.86, 'F', 's'), (54.02, 'small', 'i (si)'), (54.10, 'closed', 'm'),
    (54.18, 'U', 'u (mu)'), (54.45, 'small', 'l'), (54.52, 'A', 'a (la)'), (54.75, 'E', 'ey'), (54.88, 'small', 't'),
    (54.95, 'E', 'e (ted)'), (55.22, 'small', 'd'), (55.30, 'U', 'u'), (55.45, 'small', 'n'), (55.52, 'E', 'i (ni)'),
    (55.70, 'F', 'v'), (55.90, 'U', 'er'), (56.06, 'F', 's'), (56.22, 'closed', 'rest'),
]
LEAD = 1.0 / FPS


def viseme_at(t):
    v = TRACK[0]
    for e in TRACK:
        if t + LEAD >= e[0] - 1e-9:
            v = e
    return v


def smooth(t, a, b):
    x = np.clip((t - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- framing: hd -> output
FX0, FY0, FW = 100.0, 398.0, 1240.0
S_OUT = OW / FW                                  # 1.548


def head_matrix(t):
    """hd -> output affine for time t: phrase-shaped lift/tilt + breath."""
    lift = 7.0 * smooth(t, 53.70, 54.25) - 6.0 * smooth(t, 55.55, 56.25)      # into "SIM", settle on "verse"
    tilt = -1.6 * smooth(t, 53.70, 54.25) + 1.3 * smooth(t, 55.55, 56.25) + 0.25 * np.sin((t - T0) * 1.7)
    breath = 1.0 + 0.003 * np.sin((t - T0) * 2 * np.pi / 3.4)
    M = cv2.getRotationMatrix2D((500.0, 1000.0), tilt, breath)
    M[1, 2] -= lift
    A = np.array([[S_OUT, 0, -FX0 * S_OUT], [0, S_OUT, -FY0 * S_OUT], [0, 0, 1]])
    return (A @ np.vstack([M, [0, 0, 1]]))[:2], lift, tilt


def jaw_warp(img, drop):
    """Move the chin/jaw contour down by `drop` px (hd), fading out above the mouth line and to the sides."""
    if drop <= 0.05:
        return img
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    wy = np.clip((yy - (MY - 6)) / 40.0, 0, 1) * np.clip((1060 - yy) / 90.0, 0, 1)
    wx = np.exp(-((xx - FACE_X) / 150.0) ** 4)          # symmetric about the face axis
    dy = drop * wy * wx
    return cv2.remap(img, xx, yy - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


# ---------------------------------------------------------------- background and foreground plates
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
sky = np.zeros((OH, OW, 3), np.float32)
g = yy / OH
sky[:] = np.stack([0.035 + 0.05 * g, 0.045 + 0.06 * g, 0.10 + 0.10 * g], -1)
kv = cv2.imread(KV1)[:, :, ::-1].astype(np.float32) / 255.0
city = kv[1150:1650, 0:1300]                       # night Earth with city lights, left of the girls in KV1
city = cv2.resize(city, (OW, int(OW * city.shape[0] / city.shape[1])), interpolation=cv2.INTER_AREA)
city = cv2.GaussianBlur(city, (0, 0), 9)
bg = sky.copy()
ch = city.shape[0]
y0 = OH - ch + 240
band = np.clip((yy[y0:OH] - y0) / 160.0, 0, 1)[:, :, None]
bg[y0:OH] = bg[y0:OH] * (1 - band) + city[:OH - y0] * 0.9 * band
rng = np.random.default_rng(3)
for _ in range(90):                               # a few soft stars in the upper sky
    sx, sy = rng.integers(0, OW), rng.integers(0, int(OH * 0.55))
    cv2.circle(bg, (int(sx), int(sy)), 1, (0.6, 0.65, 0.8), -1, cv2.LINE_AA)
bg = cv2.GaussianBlur(bg, (0, 0), 1.2)

b = load_rgba(KV4B)                                # B, profile facing left; use her back hair + shoulder
bcrop = b[0:2048, 760:1996]
bs = 1.15
bcrop = cv2.resize(bcrop, (int(bcrop.shape[1] * bs), int(bcrop.shape[0] * bs)), interpolation=cv2.INTER_AREA)
fg = np.zeros((OH, OW, 4), np.float32)
ox, oy = 1250, -40
hh = min(OH - max(oy, 0), bcrop.shape[0] + min(oy, 0))
ww = min(OW - ox, bcrop.shape[1])
fg[max(oy, 0):max(oy, 0) + hh, ox:ox + ww] = bcrop[max(-oy, 0):max(-oy, 0) + hh, :ww]
# guarantee the right side is covered (A's straight crop at hd x=963 must never show), with an
# organic, wavy hair contour rather than a straight edge
edge_x = 1255 + 42 * np.sin(yy / 170.0 + 1.0) + 22 * np.sin(yy / 61.0 + 0.4) + 10 * np.sin(yy / 23.0)
cover = np.clip((xx - edge_x) / 34.0, 0, 1)
hair_col = (fg[:, :, :3] * fg[:, :, 3:]).sum((0, 1)) / max(fg[:, :, 3].sum(), 1)
col = fg[:, :, :3] * fg[:, :, 3:] + hair_col * (1 - fg[:, :, 3:])      # straight colour: B's drawing, else her hair tone
col *= np.array([0.80, 0.70, 0.68])                                    # in shade: B faces away from the camera
warm_fg = np.exp(-(((xx - 1500) / 520) ** 2 + ((yy - 1250) / 420) ** 2))[:, :, None]
col += warm_fg * np.array([0.35, 0.18, 0.07])
alpha = cover[:, :, None]                                               # the wavy contour is B's edge in this frame
prem = cv2.GaussianBlur(col * alpha, (0, 0), 12)
alpha_b = cv2.GaussianBlur(alpha, (0, 0), 12)[:, :, None]
fg = np.dstack([prem / np.maximum(alpha_b, 1e-3), alpha_b])

LIGHT = np.array([1480.0, 1180.0])                 # the note's glow, below frame between them
WARM = np.array([1.0, 0.70, 0.42])


def relight(rgba):
    al = rgba[:, :, 3:]
    alb = rgba[:, :, :3]
    soft = cv2.GaussianBlur(al[:, :, 0], (0, 0), 18)
    gx = cv2.Sobel(soft, cv2.CV_32F, 1, 0, ksize=5)
    gy = cv2.Sobel(soft, cv2.CV_32F, 0, 1, ksize=5)
    nrm = np.dstack([-gx, -gy, np.full_like(gx, 0.05)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True) + 1e-6
    lv = np.dstack([LIGHT[0] - xx, LIGHT[1] - yy, np.full_like(xx, 500.0)])
    dist = np.linalg.norm(lv, axis=2, keepdims=True)
    lv /= dist
    lam = np.clip((nrm * lv).sum(2, keepdims=True), 0, 1)
    fall = np.clip(1.0 - dist / 2100.0, 0, 1) ** 1.4
    amb = np.array([0.60, 0.61, 0.74])
    lit = alb * (amb + WARM * (0.30 + 0.70 * lam) * fall * 0.75)
    # cool sky rim on the upper-left silhouette
    rim = np.clip(-(gx * 0.6 + gy * 0.8), 0, None)
    rim = (rim / (rim.max() + 1e-6))[:, :, None] * np.array([0.10, 0.14, 0.24])
    return np.dstack([np.clip(lit + rim * al, 0, 1), al])


def render(f):
    t = f / FPS
    tt = np.floor(t * 12 + 1e-6) / 12              # drawings change on twos
    onset, name, ph = viseme_at(tt)
    hd = mouthless.copy()
    sp = SP[name]
    sh, sw = sp.shape[:2]
    kx, ky = SCALE_XY.get(name, (SCALE, SCALE))
    sp = cv2.resize(sp, (max(1, int(round(sw * kx))), max(1, int(round(sh * ky)))), interpolation=cv2.INTER_AREA)
    sh, sw = sp.shape[:2]
    pad = int(round(10 * ky))
    top = MY - 5 if name not in ('closed', 'smile', 'F') else MY - sh // 2
    x0, y0 = int(round(MX - sw / 2.0)), top - pad
    a = sp[:, :, 3:4]
    hd[y0:y0 + sh, x0:x0 + sw, :3] = hd[y0:y0 + sh, x0:x0 + sw, :3] * (1 - a) + sp[:, :, :3] * a
    hd = jaw_warp(hd, JAW.get(name, 0.0))
    M, lift, tilt = head_matrix(t)
    out = cv2.warpAffine(hd, M, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    out = relight(out)
    al = out[:, :, 3:]
    img = bg * (1 - al) + out[:, :, :3] * al
    # warm spill in the air from the note, then B's foreground
    img += np.exp(-(((xx - LIGHT[0]) / 700) ** 2 + ((yy - LIGHT[1]) / 500) ** 2))[:, :, None] * WARM * 0.10
    img = img * (1 - fg[:, :, 3:]) + fg[:, :, :3] * fg[:, :, 3:]
    # gentle vignette
    vig = 1 - 0.35 * (((xx - OW * 0.42) / OW) ** 2 + ((yy - OH * 0.5) / OH) ** 2)
    img *= vig[:, :, None]
    o8 = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)[:, :, ::-1]
    # checks in the visible face region: holes (alpha < 0.5 inside the eroded head) and light edge pixels
    fm = cv2.warpAffine(cv2.erode((head[:, :, 3] > 0.99).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(np.float32),
                        M, (OW, OH), flags=cv2.INTER_NEAREST) > 0.5
    fm &= fg[:, :, 3] < 0.05
    holes = int((fm & (al[:, :, 0] < 0.5)).sum())
    edge = (al[:, :, 0] > 0.05) & (al[:, :, 0] < 0.95) & (fg[:, :, 3] < 0.05)
    sc = out[:, :, :3]
    light_edge = int((edge & (sc.mean(2) > 0.55) & ((sc.max(2) - sc.min(2)) < 0.08)).sum())   # light AND neutral = white fringe
    return o8, dict(frame=f, t=round(t, 3), viseme=name, phoneme=ph, lift=round(float(lift), 2), tilt=round(float(tilt), 2),
                    holes_alpha_lt_0p5_in_face=holes, light_edge_px=light_edge)


if __name__ == '__main__':
    log = []
    for f in range(F0, F1):
        o8, rec = render(f)
        cv2.imwrite(os.path.join(OUTD, '%05d.png' % f), o8)
        log.append(rec)
    json.dump({'checks': CHECK, 'track': TRACK, 'lead_s': LEAD, 'frames': log}, open(os.path.join(R, 'tests', 'rev3_sing_log.json'), 'w'), indent=1)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-start_number', str(F0), '-i', os.path.join(OUTD, '%05d.png'),
                    '-ss', '%.4f' % (F0 / FPS), '-t', '%.4f' % ((F1 - F0) / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-shortest', MP4], check=True)
    from collections import Counter
    print(CHECK, Counter(r['viseme'] for r in log), 'max holes', max(r['holes_alpha_lt_0p5_in_face'] for r in log),
          'max light edge', max(r['light_edge_px'] for r in log))
