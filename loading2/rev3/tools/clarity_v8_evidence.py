"""Clarity round evidence: native-pixel crops through every stage, at 3 s (KV1 landing), 3.625-7.458 s (Seedance rear
shot) and 9 s (S1 profile). Each crop is shown 1:1 (no scaling) in *_native.png and nearest-neighbour 2x in *_2x.png.
Stages: SOURCE (native pixels of the file the frame is made from) | v7 pre-encode | v7 final (decoded mp4) |
v8 pre-encode (= lossless master) | v8 final (decoded mp4). Both mp4s are decoded with the same accurate decoder."""
import json, os, subprocess, sys
import cv2
import numpy as np
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools')); sys.path.insert(0, os.path.join(R, 'tools', 'm26'))
import opening_ink as OI
from yuv import load, hq_bgr
SP = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clarity_metrics import fine, acut, chroma_fine
OUT = os.path.join(R, 'tests', 'clarity_v8')
V7C, V8O = SP + '/v7/cache/f%04d.png', SP + '/v8/op/f%04d.png'
DEC = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:in_range=tv:in_color_matrix=bt601'


def mp4_frame(path, f):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-vf', DEC + ',select=eq(n\\,%d)' % f, '-vsync', '0',
                                   '-frames:v', '1', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'])
    return np.frombuffer(raw, np.uint8).reshape(720, 1280, 3)


def v8pre(f):
    return cv2.imread(V8O % f) if os.path.exists(V8O % f) else cv2.imread(V7C % f)


def label(im, txt, w=None):
    w = max(w or im.shape[1], 8 + 7 * len(txt))
    bar = np.zeros((18, w, 3), np.uint8)
    cv2.putText(bar, txt, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
    pad = np.zeros((im.shape[0], w, 3), np.uint8); pad[:, :im.shape[1]] = im
    return np.vstack([bar, pad])


def sheet(name, rows, note):
    """rows: list of (row title, [(stage label, crop uint8), ...]); crops kept 1:1."""
    out_rows = []
    for title, cells in rows:
        h = max(c.shape[0] for _, c in cells)
        tiles = [label(np.vstack([c, np.zeros((h - c.shape[0], c.shape[1], 3), np.uint8)]), t) for t, c in cells]
        tiles = sum([[t, np.full((t.shape[0], 3, 3), 90, np.uint8)] for t in tiles], [])[:-1]
        row = np.hstack(tiles)
        out_rows.append(label(row, title))
    wmax = max(r.shape[1] for r in out_rows)
    words, lines = note.split(), ['']
    for wd in words:                                     # wrap the note to the sheet width
        if len(lines[-1]) + len(wd) + 1 > max(60, wmax // 7):
            lines.append('')
        lines[-1] += (' ' if lines[-1] else '') + wd
    top = [label(np.zeros((0, 8, 3), np.uint8), ln) for ln in lines]
    wmax = max([wmax] + [t.shape[1] for t in top])
    padw = lambda r: np.hstack([r, np.zeros((r.shape[0], wmax - r.shape[1], 3), np.uint8)])
    img = np.vstack([padw(t) for t in top] + sum([[padw(r), np.full((4, wmax, 3), 90, np.uint8)] for r in out_rows], []))
    cv2.imwrite(os.path.join(OUT, name + '_native.png'), img)
    cv2.imwrite(os.path.join(OUT, name + '_2x.png'), cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))


def c(im, b):
    x0, y0, x1, y1 = [int(round(v)) for v in b]
    return np.ascontiguousarray(np.clip(im[y0:y1, x0:x1], 0, 255).astype(np.uint8))


V7, V8 = os.path.join(R, 'tests', 'DEMO_0-43_v7_720p.mp4'), os.path.join(R, 'tests', 'DEMO_0-43_v8_720p.mp4')
metrics = {}


def stages(f, boxes, source_fn, source_label):
    pre7, fin7, pre8, fin8 = cv2.imread(V7C % f), mp4_frame(V7, f), v8pre(f), mp4_frame(V8, f)
    rows = []
    for rn, b in boxes.items():
        cells = [(source_label, source_fn(b))]
        for t, im in (('v7 pre-encode', pre7), ('v7 final mp4', fin7), ('v8 pre-encode', pre8), ('v8 final mp4', fin8)):
            cells.append((t, c(im, b)))
            metrics.setdefault('f%d' % f, {}).setdefault(rn, {})[t] = dict(fine=round(fine(im.astype(np.float32), b), 3),
                                                                             acut=round(acut(im.astype(np.float32), b), 2),
                                                                             chroma=round(chroma_fine(im.astype(np.float32), b), 3))
        rows.append(('%.3f s (frame %d)  %s' % (f / 24, f, rn), cells))
    return rows


# ---- 3 s: KV1 landing (frames 72, 84). Source = KV1.png at its own 3072-px resolution (2.3x the screen scale).
kv = cv2.imread(OI.KV1)[OI.Y0:OI.Y0 + 1728]
def fg_map(t):
    u = float(np.clip((t - OI.T_FG) / (OI.T_LAND - OI.T_FG), 0, 1)); u = 1 - (1 - u) ** 3
    if t <= OI.T_LAND:
        s = 1.35 + (1.05 - 1.35) * u; dy = 520.0 * (1 - u)
    else:
        s = 1.05 - 0.05 * (1 - (1 - np.clip((t - OI.T_LAND) / (7.5 - OI.T_LAND), 0, 1)) ** 2); dy = 0.0
    return OI.S * s, 640 - 640 * s, 720 - 720 * s + dy
rows = []
for f, boxes in ((72, {'A: horns, hair silhouette': (400, 360, 560, 520), 'B: star clip, ribbon, hair': (740, 390, 900, 550)}),
                 (84, {'A: horns, hair silhouette': (410, 320, 570, 480), 'B: star clip, ribbon, hair': (730, 350, 890, 510),
                       'railing, hands, cloth': (520, 590, 760, 700)})):
    sc, tx, ty = fg_map(f / 24)
    rows += stages(f, boxes, lambda b, sc=sc, tx=tx, ty=ty: c(kv, ((b[0] - tx) / sc, (b[1] - ty) / sc, (b[2] - tx) / sc, (b[3] - ty) / sc)),
                   'SOURCE KV1.png (3072 px: 2.3x)')
sheet('1_3s_KV1_landing', rows, 'Opening landing, 3.000 s (deliberate landing motion blur, about 6 px) and 3.500 s (landed). '
      'Pixels 1:1. v7 = v6 render (bilinear point sampling of KV1: broken strands); v8 = antialiased Lanczos with anti-ringing.')

# ---- 3.625-7.458: Seedance rear shot (frames 87, 120, 170). Source = the decoded Seedance file, native, same content.
Y, U, V = load(SP + '/m26/dec/Opening_rear_rep.yuv')
A = np.array([[0.988, -0.0001, -3.2259], [-0.0003, 0.9687, 0.1156], [0, 0, 1]])
zc = OI.push_in(87 / 24)[1]
rows = []
for f in (87, 120, 170):
    zf = OI.push_in(f / 24)[1] / zc; pc = OI.PUSH_C; z0 = 1.0055
    Zk = np.array([[1 / zf, 0, pc[0] * (1 - 1 / zf)], [0, 1 / zf, pc[1] * (1 - 1 / zf)], [0, 0, 1]])
    Z0 = np.array([[1 / z0, 0, 640 * (1 - 1 / z0)], [0, 1 / z0, 360 * (1 - 1 / z0)], [0, 0, 1]])
    M = A @ Z0 @ Zk
    srcim = hq_bgr(Y, U, V, f - 87)
    def sfn(b, M=M, srcim=srcim):
        p = (M @ np.array([[b[0], b[1], 1], [b[2], b[3], 1]]).T).T
        return c(srcim, (p[0, 0], p[0, 1], p[1, 0], p[1, 1]))
    boxes = {'A: horns, hair silhouette': (410, 320, 570, 480), 'B: star clip, ribbon, hair': (730, 350, 890, 510)}
    if f == 170:
        boxes = {'A: hand on the ledge, cuff': (480, 560, 700, 700), 'B: star clip, ribbon, hair': (730, 350, 890, 510)}
    if f == 120:
        boxes['railing'] = (880, 600, 1200, 700)
    rows += stages(f, boxes, sfn, 'SOURCE Seedance file')
sheet('2_3.625-7.458s_Seedance_rear', rows, 'Rear two-shot 3.625-7.458 s. Pixels 1:1. The SOURCE column is the Seedance file itself '
      '(one 69 KB I-frame, then about 1 KB per frame): its softness is in the file and is not removed by any later step.')

# ---- 9 s: S1 profile (frame 216 = take frame 88). Source = the take, decoded.
cap = cv2.VideoCapture(os.path.join(R, 'seedance', 'returned', 'P1-S1_v5_take_v2.mp4')); take = []
while True:
    ok, fr = cap.read()
    if not ok:
        break
    take.append(fr)
boxes = {'A: eye, lashes': (395, 225, 475, 290), 'A: horns, hair silhouette': (395, 50, 505, 160), 'A: profile (nose, lips)': (455, 255, 515, 350),
         'A: collar, ribbon, suspender': (290, 370, 480, 470)}
rows = stages(216, boxes, lambda b: c(take[52 + 36], b), 'SOURCE Seedance take')
# generation: the approved still the take was made from vs the take's own first frame (same pose, same geometry)
reg = np.load(os.path.join(R, 'work', 'p1', 'v2_reg.npy'))
still = cv2.imread(os.path.join(R, 'seedance', 'refs_in2', 'P1_S1_original_reference_v8.png'))
st = np.dstack([np.asarray(Image.fromarray(still[..., k]).resize((1280, 720), Image.LANCZOS)) for k in range(3)])
stw = cv2.warpAffine(st, reg, (1280, 720), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
for rn, b in (('take frame 0 vs its input still: eye', (340, 175, 430, 245)), ('take frame 0 vs its input still: horn, hair', (255, 45, 375, 165)),
               ('take frame 0 vs its input still: collar, ribbon', (290, 370, 480, 470))):
    rows.append((rn, [('approved still, Lanczos to 720p', c(stw, b)), ('take frame 0, native', c(take[0], b))]))
    metrics.setdefault('generation', {})[rn] = {k: dict(fine=round(fine(im.astype(np.float32), b), 3), acut=round(acut(im.astype(np.float32), b), 2))
                                                for k, im in (('still', stw), ('take0', take[0]))}
sheet('3_9s_S1_profile', rows, 'A\'s profile, 9.000 s (frame 216 = take frame 88). Pixels 1:1. v7 pre-encode was already a crf-16 '
      'decode (an extra lossy generation); v8 pre-encode is lossless. Bottom rows: what the generation itself lost.')
json.dump(metrics, open(os.path.join(OUT, 'roi_metrics.json'), 'w'), indent=1)
print(sorted(os.listdir(OUT)))
