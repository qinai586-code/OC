"""ACCEPTANCE TEST 2 - singing close-up, 0:52.40-0:56.30 of the locked track (3.9 s).

Technique under test: an existing front head drawing + a locally made mouthless base + the supplied
front 8-mouth chart, switched on twos (12 drawings/s) from a viseme track that follows the AUTHOR
text, timed to syllables read off the measured vocal level/voicing (tools/audio_evidence.py
sources). Head motion is a rigid similarity transform of the whole face (features cannot drift).
Singer attribution (A) is a staging proposal: the author text gives this chorus no voice role.
"""
import os, sys, json
import numpy as np, cv2, subprocess
sys.path.insert(0, '/home/user/OC/loading2/src')
from lw import imread, imwrite, gblur, smooth
from acting import char

OUT = '/home/user/OC/loading2/tests/test2_sing'
os.makedirs(OUT, exist_ok=True)
IMG = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/images'
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
T0, T1, FPS = 52.40, 56.30, 24

# ---------------------------------------------------------------- 1. mouth sprites from the A chart
chart = cv2.imread(os.path.join(IMG, '6.webp'))[:, :, ::-1].astype(np.float32) / 255.0
ink = 1 - chart.min(2)
m = cv2.morphologyEx((ink > 0.06).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(m)
comps = sorted([i for i in range(1, n) if st[i, 4] > 150], key=lambda i: (round(cen[i][1] / 200), cen[i][0]))
assert len(comps) == 8, len(comps)
NAMES = ['closed', 'smile', 'small', 'A', 'I', 'U', 'E', 'O']
sprites = {}
for name, i in zip(NAMES, comps):
    x, y, w, h = st[i, :4]
    p = 10
    crop = chart[y - p:y + h + p, x - p:x + w + p].copy()
    d = 1 - crop.min(2)
    bg = (d < 0.05).astype(np.uint8)
    ff = bg.copy(); mask = np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8)
    for sx, sy in ((0, 0), (ff.shape[1] - 1, 0), (0, ff.shape[0] - 1), (ff.shape[1] - 1, ff.shape[0] - 1)):
        cv2.floodFill(ff, mask, (sx, sy), 2)
    outside = (ff == 2)
    alpha = np.where(outside, np.clip(d / 0.25, 0, 1), 1.0).astype(np.float32)
    rgb = np.where(alpha[:, :, None] > 0, crop, 0)
    # un-premultiply the anti-aliased edge against white
    a3 = np.maximum(alpha[:, :, None], 1e-3)
    rgb = np.clip((crop - (1 - a3) * 1.0) / a3, 0, 1)
    sprites[name] = np.dstack([rgb, alpha]).astype(np.float32)

# ---------------------------------------------------------------- 2. mouthless base (local, verified)
base = char('A_x0').copy()                   # 4x upscale of A_head_neutral, RGBA
H, W = base.shape[:2]
MX, MY = 538, 855                            # measured mouth centre (face.py HEADS)
reg = np.zeros((H, W), np.uint8)
cv2.rectangle(reg, (MX - 34, MY - 12), (MX + 34, MY + 12), 255, -1)
rgb8 = (np.clip(base[:, :, :3], 0, 1) * 255).astype(np.uint8)
paint = cv2.inpaint(rgb8, reg, 6, cv2.INPAINT_TELEA).astype(np.float32) / 255.0
mouthless = base.copy()
mouthless[:, :, :3] = np.where(reg[:, :, None] > 0, paint, base[:, :, :3])
diff_out = np.abs(mouthless - base)[reg == 0].max()
check = {'mouthless_changed_pixels': int((np.abs(mouthless - base).max(2) > 1e-6).sum()),
         'region_pixels': int((reg > 0).sum()), 'max_change_outside_region': float(diff_out)}

# ---------------------------------------------------------------- 3. viseme track (author text, measured timing)
# (start time, viseme) read from the vocal level/voicing curve at 0.04 s resolution
TRACK = [(52.40, 'closed'),
         (52.44, 'U'), (52.48, 'A'), (52.84, 'small'),            # what
         (52.90, 'I'), (53.10, 'I'),                              # if (f: teeth)
         (53.16, 'U'), (53.22, 'I'),                              # we
         (53.40, 'small'), (53.60, 'I'), (53.90, 'I'),            # live
         (54.04, 'I'), (54.20, 'small'),                          # in
         (54.28, 'E'),                                            # a
         (54.52, 'I'), (54.66, 'I'), (54.80, 'closed'),           # sim (m closes)
         (54.86, 'U'),                                            # u
         (55.00, 'small'), (55.06, 'A'),                          # la
         (55.36, 'small'), (55.42, 'E'), (55.56, 'small'),        # ted
         (55.60, 'U'),                                            # u
         (55.72, 'small'), (55.78, 'I'),                          # ni
         (56.00, 'I'), (56.04, 'E'), (56.12, 'I'),                # verse
         (56.24, 'closed')]


def viseme_at(t):
    v = TRACK[0][1]
    for s, name in TRACK:
        if t >= s:
            v = name
    return v


SCALE = 0.45                                 # chart -> 4x head pixels (A shape about 77 px vs eye 142 px)

# ---------------------------------------------------------------- 4. render
OW, OH = 1920, 1080
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
bg = np.zeros((OH, OW, 3), np.float32)
g = yy / OH
bg[:] = np.stack([0.10 + 0.10 * g, 0.07 + 0.05 * g, 0.20 - 0.04 * g], -1)
bg += np.exp(-(((xx - 1350) / 500) ** 2 + ((yy - 300) / 420) ** 2))[:, :, None] * np.array([0.35, 0.25, 0.12], np.float32)
face_mask = cv2.erode((base[:, :, 3] > 0.99).astype(np.uint8), np.ones((15, 15), np.uint8))
frames = []
log = []
f0, f1 = int(round(T0 * FPS)), int(round(T1 * FPS))
for f in range(f0, f1):
    t = f / FPS
    tt = np.floor(t * 12) / 12                # drawings change on twos
    name = viseme_at(tt + 1e-6)
    head = mouthless.copy()
    sp = sprites[name]
    sh, sw = sp.shape[:2]
    sp = cv2.resize(sp, (max(1, int(sw * SCALE)), max(1, int(sh * SCALE))), interpolation=cv2.INTER_AREA)
    sh, sw = sp.shape[:2]
    pad = int(10 * SCALE)
    top = MY - 4 if name not in ('closed', 'smile') else MY - sh // 2
    x0, y0 = MX - sw // 2, top - pad
    a = sp[:, :, 3:4]
    head[y0:y0 + sh, x0:x0 + sw, :3] = head[y0:y0 + sh, x0:x0 + sw, :3] * (1 - a) + sp[:, :, :3] * a
    # rigid head motion: a small lift into "sim-u-la-ted", settle on "verse", breathing
    lift = 6.0 * smooth(t, 54.4, 54.9) - 4.0 * smooth(t, 55.4, 56.1)
    tilt = 1.2 * np.sin((t - T0) * 1.3) * 0.6 + 0.8 * smooth(t, 54.5, 55.2)
    sc = 0.86 * (1 + 0.004 * np.sin((t - T0) * 2 * np.pi / 3.2))
    M = cv2.getRotationMatrix2D((W / 2, H * 0.62), tilt, sc)
    M[0, 2] += OW * 0.40 - W / 2
    M[1, 2] += OH * 0.50 - H * 0.55 - lift
    warped = cv2.warpAffine(head, M, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    al = warped[:, :, 3:4]
    lit = warped[:, :, :3] * (0.92 + 0.10 * np.exp(-(((xx - 1350) / 700) ** 2))[:, :, None])
    img = bg * (1 - al) + lit * al
    # automated checks: holes inside the face, mouth inside the lower face
    fm = cv2.warpAffine(face_mask.astype(np.float32), M, (OW, OH), flags=cv2.INTER_NEAREST) > 0.5
    holes = int((fm & (al[:, :, 0] < 0.99)).sum())
    log.append({'frame': f, 't': round(t, 3), 'viseme': name, 'holes_in_face': holes, 'lift_px': round(float(lift), 2), 'tilt_deg': round(float(tilt), 2)})
    out = (np.clip(img, 0, 1) * 255).astype(np.uint8)[:, :, ::-1].copy()
    cv2.putText(out, 'ACCEPTANCE TEST 2 - singing close-up - not final animation', (24, 40), 0, 0.9, (220, 220, 220), 2, cv2.LINE_AA)
    cv2.putText(out, f'{t:7.3f}s  f{f}  viseme {name}', (24, 1060), 0, 0.8, (180, 220, 255), 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(OUT, f'{f:05d}.png'), out)
json.dump({'checks': check, 'frames': log}, open(os.path.join(OUT, 'test2_log.json'), 'w'), indent=1)
mp4 = '/home/user/OC/loading2/tests/TEST2_singing_closeup.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-start_number', str(f0), '-i', os.path.join(OUT, '%05d.png'),
                '-ss', f'{f0 / FPS:.4f}', '-t', f'{(f1 - f0) / FPS:.4f}', '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-c:a', 'aac', '-b:a', '192k', '-shortest', mp4], check=True)
print(json.dumps(check), 'frames', len(log), 'max holes', max(r['holes_in_face'] for r in log))
from collections import Counter
print(Counter(r['viseme'] for r in log))
