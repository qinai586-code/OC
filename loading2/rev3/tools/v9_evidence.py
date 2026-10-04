"""v9 evidence: native-pixel crops (1:1, no scaling) for each item the v9 round addressed, plus the original project's
(rev1) shots before/after the bridge changes. Writes tests/v9_evidence/*_native.png.

Stages, where they exist for a frame:
  SOURCE        native pixels of the file the frame is made from (approved KV1 original 1536 px, Seedance file, ...)
  v8 final      DEMO_0-43_v8_720p.mp4, decoded
  v9 pre-encode the v9 lossless master's parts (bit-exact with the rendered frames)
  v9 final      LOADING_v9_full_720p.mp4, decoded (the delivered encode)
All mp4s are decoded with the same accurate decoder (BT.601 limited range, Lanczos chroma)."""
import json, os, subprocess, sys
import cv2
import numpy as np
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools')); sys.path.insert(0, os.path.join(R, 'tools', 'm26'))
os.environ.setdefault('OI_STAGE', 'v9')
import opening_ink as OI
from yuv import load, hq_bgr
from clarity_metrics import fine, acut
import song_v9                                                         # the master's parts and frame lookup
SP = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
OUT = os.path.join(R, 'tests', 'v9_evidence')
os.makedirs(OUT, exist_ok=True)
V8 = os.path.join(R, 'tests', 'DEMO_0-43_v8_720p.mp4')
V9 = os.path.join(R, 'tests', 'LOADING_v9_full_720p.mp4')
REV1 = '/home/user/OC/out/LOADING_MV_preview720.mp4'
DEC = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:in_range=tv:in_color_matrix=bt601'   # as clarity_v8_evidence.py
_cache = {}


def mp4_frame(path, f):
    # accurate seek: decoding starts at the keyframe before and frames before f/24 are dropped (checked against select=n)
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', '%.6f' % ((f - 0.25) / 24), '-i', path, '-vf', DEC, '-frames:v', '1',
                                   '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'])
    return np.frombuffer(raw, np.uint8).reshape(720, 1280, 3)


def label(im, txt, w=None):
    w = max(w or im.shape[1], 8 + 7 * len(txt))
    bar = np.zeros((18, w, 3), np.uint8)
    cv2.putText(bar, txt, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
    pad = np.zeros((im.shape[0], w, 3), np.uint8); pad[:, :im.shape[1]] = im
    return np.vstack([bar, pad])


def master_frame(f):
    if ('m', f) not in _cache:
        _cache[('m', f)] = song_v9.master_frame(f)
    return _cache[('m', f)]


def dec(path, f):
    if (path, f) not in _cache:
        _cache[(path, f)] = mp4_frame(path, f)
    return _cache[(path, f)]


def c(im, b):
    x0, y0, x1, y1 = [int(round(v)) for v in b]
    return np.ascontiguousarray(np.clip(im[max(0, y0):y1, max(0, x0):x1], 0, 255).astype(np.uint8))


metrics = {}


def m(im, b):
    return dict(fine=round(fine(im.astype(np.float32), b), 3), acut=round(acut(im.astype(np.float32), b), 2))


def sheet(name, rows, note):
    """rows: list of (row title, [(cell label, crop uint8), ...]); crops kept 1:1 (layout as clarity_v8_evidence.py)."""
    out_rows = []
    for title, cells in rows:
        h = max(cc.shape[0] for _, cc in cells)
        tiles = [label(np.vstack([cc, np.zeros((h - cc.shape[0], cc.shape[1], 3), np.uint8)]), t) for t, cc in cells]
        tiles = sum([[t, np.full((t.shape[0], 3, 3), 90, np.uint8)] for t in tiles], [])[:-1]
        out_rows.append(label(np.hstack(tiles), title))
    wmax = max(r.shape[1] for r in out_rows)
    lines = ['']
    for wd in note.split():
        if len(lines[-1]) + len(wd) + 1 > max(60, wmax // 7):
            lines.append('')
        lines[-1] += (' ' if lines[-1] else '') + wd
    top = [label(np.zeros((0, 8, 3), np.uint8), ln) for ln in lines]
    wmax = max([wmax] + [t.shape[1] for t in top])
    padw = lambda r: np.hstack([r, np.zeros((r.shape[0], wmax - r.shape[1], 3), np.uint8)])
    img = np.vstack([padw(t) for t in top] + sum([[padw(r), np.full((4, wmax, 3), 90, np.uint8)] for r in out_rows], []))
    cv2.imwrite(os.path.join(OUT, name + '_native.png'), img, [cv2.IMWRITE_PNG_COMPRESSION, 9])


# ---------------------------------------------------------------------------------------------------------------------
# 1. 3 s landing: v8 slid the girls 520 px up during 2.62-3.34 s under a 6 px motion blur (the "drag blur"); v9 holds
#    them still before the chime and cuts on it (frame 80 | 81), so no frame carries the slide or its blur.
rows = []
for f in (72, 76, 80, 81, 84):
    b = {'A: horns, hair': (400, 330, 580, 510), 'B: star clip, hair': (720, 360, 900, 540)}
    cells = []
    for rn, box in b.items():
        for t, im in (('v8 final', dec(V8, f)), ('v9 pre-encode', master_frame(f)), ('v9 final', dec(V9, f))):
            cells.append(('%s %s' % (t, rn[:2]), c(im, box)))
            metrics.setdefault('1_landing', {}).setdefault('f%d %s' % (f, rn), {})[t] = m(im, box)
    rows.append(('%.3f s (frame %d)' % (f / 24, f), cells))
sheet('1_landing_3s', rows, 'Landing, 2.9-3.5 s. Pixels 1:1. v8 frames 72-80 carry the girls\' 520-px slide and its motion blur. v9 '
      'removes the slide: before the cut only the Earth and sky are in frame (the camera\'s push continues, at a 0.075-frame '
      'shutter), and the girls appear in place on the cut to the rear two-shot between frames 80 and 81 (first chime, 3.344 s).')

# ---------------------------------------------------------------------------------------------------------------------
# 2. 3.375-6.6 s rear two-shot: v8 = the Seedance rear take (soft in the file itself); v9 = the approved KV1 art.
#    SOURCE columns: the Seedance file (v8) and the approved KV1 original, 1536 px (v9), each at native pixels.
kvo = cv2.imread(SP + '/final_assets/KV1.png')                      # the approved original (1536 x 1024)
Y, U, V = load(SP + '/m26/dec/Opening_rear_rep.yuv')
A = np.array([[0.988, -0.0001, -3.2259], [-0.0003, 0.9687, 0.1156], [0, 0, 1]])
zc = OI.push_in(87 / 24)[1]


def kv_src(t, b):
    s = 1.05 - 0.05 * (1 - (1 - np.clip((t - OI.CUT9) / (7.5 - OI.CUT9), 0, 1)) ** 2)
    zf = OI.push_in(t)[1]
    sc = OI.S * s * zf
    tx = (640 - 640 * s) * zf + OI.PUSH_C[0] * (1 - zf)
    ty = (720 - 720 * s) * zf + OI.PUSH_C[1] * (1 - zf)
    px = [(b[0] - tx) / sc, (b[2] - tx) / sc]
    py = [(b[1] - ty) / sc, (b[3] - ty) / sc]                       # 3072-plate crop coordinates
    return c(kvo, (px[0] / 2, (py[0] + OI.Y0) / 2, px[1] / 2, (py[1] + OI.Y0) / 2)), sc / 0.5


def sd_src(f, b):
    zf = OI.push_in(f / 24)[1] / zc; pc = OI.PUSH_C; z0 = 1.0055
    Zk = np.array([[1 / zf, 0, pc[0] * (1 - 1 / zf)], [0, 1 / zf, pc[1] * (1 - 1 / zf)], [0, 0, 1]])
    Z0 = np.array([[1 / z0, 0, 640 * (1 - 1 / z0)], [0, 1 / z0, 360 * (1 - 1 / z0)], [0, 0, 1]])
    M = A @ Z0 @ Zk
    p = (M @ np.array([[b[0], b[1], 1], [b[2], b[3], 1]]).T).T
    return c(hq_bgr(Y, U, V, f - 87), (p[0, 0], p[0, 1], p[1, 0], p[1, 1]))


rows = []
for f in (90, 120, 150):
    for rn, box in (('A: horns, hair', (410, 320, 570, 480)), ('B: star clip, ribbon', (730, 350, 890, 510))):
        ks, scale = kv_src(f / 24, box)
        cells = [('SOURCE Seedance (v8)', sd_src(f, box)), ('v8 final', c(dec(V8, f), box)),
                 ('SOURCE KV1 1536 orig (%.2fx on screen)' % scale, ks), ('v9 pre-encode', c(master_frame(f), box)), ('v9 final', c(dec(V9, f), box))]
        for t, im in (('v8 final', dec(V8, f)), ('v9 pre-encode', master_frame(f)), ('v9 final', dec(V9, f))):
            metrics.setdefault('2_rear', {}).setdefault('f%d %s' % (f, rn), {})[t] = m(im, box)
        rows.append(('%.3f s (frame %d)  %s' % (f / 24, f, rn), cells))
sheet('2_rear_3.4-6.6s', rows, 'Rear two-shot. Pixels 1:1. v8 used the Seedance rear take, which is soft in the file itself (one 69 KB '
      'I-frame, then about 1 KB per frame). v9 uses the approved KV1 art instead: its detail is that of the 1536-px original shown '
      'at about 0.9x; nothing beyond the original is claimed. The KV1 plate the renderer reads (3072 px) is a 2x Real-ESRGAN '
      'upscale of that original (the v8 report said otherwise; that was wrong). Cost: the only motion in 3.4-6.6 s is A\'s small head lift '
      '(5.55-6.35 s) and B\'s glance up (5.90-6.50 s), made on the approved art; A\'s hand stays on the stone.')

# ---------------------------------------------------------------------------------------------------------------------
# 3. 6.6-7.5 s: v8 lifted A's hand on the rear take and jumped the light at the 7.5 cut; v9 cuts to A's point of view
#    of the light (frames 159-179, KV1 sky) and lands it where the S1 take has it on frame 180.
rows = []
box = (700, 0, 1180, 300)
for t, path in (('v8 final', V8), ('v9 final', V9)):
    rows.append((t + '  (light region, x 700-1180, y 0-300)', [('frame %d (%.3f s)' % (f, f / 24), c(dec(path, f), box)) for f in (170, 176, 179, 180, 182)]))
ctx = [('frame %d, 0.25x context (not native)' % f, cv2.resize(dec(V9, f), (320, 180), interpolation=cv2.INTER_AREA)) for f in (150, 159, 170, 179, 180, 200)]
rows.append(('v9 final, whole frame for context', ctx))
ctx8 = [('frame %d, 0.25x context (not native)' % f, cv2.resize(dec(V8, f), (320, 180), interpolation=cv2.INTER_AREA)) for f in (150, 159, 170, 179, 180, 200)]
rows.append(('v8 final, whole frame for context', ctx8))
sheet('3_7.5s_light_cut', rows, 'The 7.5 s cut. v9: rear two-shot -> A\'s view of the light (6.625-7.458 s) -> the S1 take. The light on '
      'frame 179 is placed where the take has it on frame 180 (909,89 vs 908,90). Limitation kept: the hand lift is not shown at all; '
      'the cutaway hides it rather than animating it.')

# ---------------------------------------------------------------------------------------------------------------------
# 4. D1 28.58-30.42 s: v8 began after the strip had lit (B was already looking); v9 starts on the dim strip so the
#    brightening (event) precedes B's blink and the drop of her eyes (the source's own reaction).
rows = []
eye = (560, 170, 820, 360)
fr9 = (686, 692, 695, 697, 700, 703, 707, 712)
for t, path in (('v8 final', V8), ('v9 final', V9)):
    rows.append((t + ': B\'s eye (native)', [('%d %.2fs' % (f, f / 24), c(dec(path, f), eye)) for f in fr9]))
rows.append(('v9 pre-encode: B\'s eye (native)', [('%d' % f, c(master_frame(f), eye)) for f in fr9]))
rows.append(('v9 final: strip, 0.25x context (not native)', [('%d' % f, cv2.resize(dec(V9, f), (260, 146), interpolation=cv2.INTER_AREA)) for f in fr9]))
sheet('4_D1_event_gaze', rows, 'D1. v9 source frames 0-44: the strip brightens (src 9-11, 28.96 s), B blinks (src 12-17), her eyes drop '
      'to the strip (src 18-27). Event -> reaction in the source\'s own order. Limitation: the reaction is the source\'s small blink and '
      'eye shift; no head turn was added, and the warm front along the strip is an added light, not new motion.')

# ---------------------------------------------------------------------------------------------------------------------
# 5. V1b 14.96-15.83 s: v8's note appeared at full exposure in the air; v9's rests in the palm under the glow and is
#    revealed as the glow dims, then lifts and unfolds.
rows = []
box = (520, 120, 1180, 620)
for t, path in (('v8 final', V8), ('v9 final', V9)):
    rows.append((t, [('%d %.2fs' % (f, f / 24), c(dec(path, f), box)) for f in (359, 362, 366, 369, 373)]))
sheet('5_V1b_paper_entrance', rows, 'The note\'s entrance. Pixels 1:1 (x 520-1180, y 120-620: palm and note). v9: the note is in the palm cup from the start, '
      'covered by the glow; as the glow shrinks (14.97-15.12 s) it shows, lifts (15.10-15.58 s) and unfolds toward the viewer in two folds.')

# ---------------------------------------------------------------------------------------------------------------------
# 6. D4 ground 35.9-39.2 s: v8's road/hill crease vs v9's printed terrain from the approved plate rows.
rows = []
box = (60, 420, 760, 720)
for t, path in (('v8 final', V8), ('v9 final', V9)):
    rows.append((t, [('%d %.2fs' % (f, f / 24), c(dec(path, f), box)) for f in (880, 905, 930)]))
sheet('6_D4_ground', rows, 'D4 ground. Pixels 1:1. v9 drops the hill crease and road and prints the approved plate\'s own terrain '
      '(rows 760-941, tiled without mirroring, low-passed tone + 1/3 of its detail) under the paper town as it lands.')

# ---------------------------------------------------------------------------------------------------------------------
# 7. 9 s: still the S1 take (source-soft). Shown so the limitation is explicit: v9 does not change it.
cap = cv2.VideoCapture(os.path.join(R, 'seedance', 'returned', 'P1-S1_v5_take_v2.mp4')); take = []
while True:
    ok, fr = cap.read()
    if not ok:
        break
    take.append(fr)
rows = []
for rn, box in (('A: eye, lashes', (395, 225, 475, 290)), ('A: horns, hair', (395, 50, 505, 160)), ('A: collar, ribbon', (290, 370, 480, 470))):
    rows.append((rn, [('SOURCE take f88', c(take[88], box)), ('v8 final', c(dec(V8, 216), box)), ('v9 pre-encode', c(master_frame(216), box)),
                      ('v9 final', c(dec(V9, 216), box))]))
    for t, im in (('SOURCE', take[88]), ('v8 final', dec(V8, 216)), ('v9 pre-encode', master_frame(216)), ('v9 final', dec(V9, 216))):
        metrics.setdefault('7_9s', {}).setdefault(rn, {})[t] = m(im, box)
sheet('7_9s_S1_unchanged', rows, '9.000 s (frame 216 = take frame 88). Pixels 1:1. Unchanged in v9: the softness is in the Seedance take '
      'itself and no sharpening or upscaling was applied (none would restore it).')

# ---------------------------------------------------------------------------------------------------------------------
# 8. 43.25-213.4 s: the original project's render (rev1, LOADING_MV_preview720.mp4) vs v9 (same shots through the bridge).
rows = []
for f, box, note in ((1500, (320, 180, 960, 540), 'S12 62.5 s: rev1 pixel blocks + noise fog -> paint thinning into paper'),
                     (1650, (0, 0, 640, 360), 'S14 68.75 s: torn edge -> brushed edge'),
                     (1980, (320, 180, 960, 540), 'S17 82.5 s: zoom 2.5 -> capped 1.3 (wider; the approved art no longer magnified 2x)'),
                     (4224, (440, 300, 1080, 660), 'S42 176.0 s: ragged wash front -> smoothed front'),
                     (4910, (640, 100, 1280, 460), 'S47 204.6 s: ragged wash front -> smoothed front')):
    rows.append(('frame %d  %s' % (f, note), [('rev1 final (720p preview)', c(dec(REV1, f), box)), ('v9 pre-encode', c(master_frame(f), box)),
                                              ('v9 final', c(dec(V9, f), box))]))
sheet('8_rev1_vs_v9_43-213s', rows, 'Original project shots, before (rev1\'s own 720p preview) and after (v9). Pixels 1:1. v9 also removes '
      'rev1\'s grain, chromatic aberration, diffusion glow and paper-tooth overlay and renders once to 720p from 1080p float.')
json.dump(metrics, open(os.path.join(OUT, 'roi_metrics.json'), 'w'), indent=1)
print(sorted(os.listdir(OUT)))

# ---------------------------------------------------------------------------------------------------------------------
# Whole-film strip: one frame every 2 s (48 frames) from the delivered mp4, scaled (not a native-pixel sheet).
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', V9, '-vf', DEC + ",select='not(mod(n\\,48))',scale=256:144:flags=area", '-vsync', '0',
                      '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
th = []
while True:
    bb = p.stdout.read(256 * 144 * 3)
    if len(bb) < 256 * 144 * 3:
        break
    im = np.frombuffer(bb, np.uint8).reshape(144, 256, 3).copy()
    k = len(th) * 48
    cv2.putText(im, '%d:%04.1f' % (k // 24 // 60, k / 24 % 60), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(im, '%d:%04.1f' % (k // 24 // 60, k / 24 % 60), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    th.append(im)
while len(th) % 10:
    th.append(np.zeros_like(th[0]))
cv2.imwrite(os.path.join(R, 'tests', 'LOADING_v9_full_strip.jpg'), np.vstack([np.hstack(th[i:i + 10]) for i in range(0, len(th), 10)]),
            [cv2.IMWRITE_JPEG_QUALITY, 85])
