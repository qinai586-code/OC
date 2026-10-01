"""Automated metrics + frame strips for the two acceptance tests (flags only; not a human review).

Sources
  Test 1 frames/log : tests/test1_rig/*.png, test1_log.json   (tools/test1_rig.py)
  Test 2 frames/log : tests/test2_sing/*.png, test2_log.json  (tools/test2_sing.py)
  vocal stem        : scratchpad/audio/stem_0.wav (UVR-MDX-NET-Voc_FT separation via sherpa-onnx of
                      song.wav, the 44.1 kHz decode of the locked mp3)
Writes tests/test_metrics.json, tests/TEST1_strip.jpg, tests/TEST2_strip.jpg.
"""
import json
import os
from collections import Counter

import cv2
import numpy as np
import soundfile as sf

L2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(L2, 'tests')
STEM = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad/audio/stem_0.wav'
FPS = 24

# openness assigned to each chart drawing (0 = lips together); a stated assumption, used only for the correlation
OPEN = {'closed': 0.0, 'smile': 0.0, 'small': 0.3, 'U': 0.35, 'I': 0.5, 'E': 0.6, 'O': 0.8, 'A': 1.0}


def vocal_db(frames):
    y, sr = sf.read(STEM, always_2d=True)
    y = y.mean(1)
    ref = np.sqrt(np.mean(y ** 2))
    out = []
    for f in frames:
        a, b = int(f / FPS * sr), int((f + 1) / FPS * sr)
        out.append(20 * np.log10(np.sqrt(np.mean(y[a:b] ** 2)) / ref + 1e-9))
    return np.array(out)


def test2():
    d = json.load(open(os.path.join(T, 'test2_sing', 'test2_log.json')))
    fr = d['frames']
    frames = [r['frame'] for r in fr]
    vis = [r['viseme'] for r in fr]
    op = np.array([OPEN[v] for v in vis])
    db = vocal_db(frames)
    lags = {}
    for lag in range(-3, 4):          # positive lag: mouth compared with the vocal `lag` frames earlier
        if lag >= 0:
            a, b = op[lag:], db[:len(db) - lag]
        else:
            a, b = op[:lag], db[-lag:]
        lags[lag] = round(float(np.corrcoef(a, b)[0, 1]), 3)
    loud = db > -15.0
    holes = [r['holes_in_face'] for r in fr]
    changes = sum(1 for i in range(1, len(vis)) if vis[i] != vis[i - 1])
    return dict(frames=len(fr), t0=fr[0]['t'], t1=fr[-1]['t'] + 1 / FPS,
                openness_vs_vocal_rms_corr_by_lag_frames=lags,
                loud_threshold_db_re_track_rms=-15.0, loud_frames=int(loud.sum()),
                closed_while_loud=int(sum(1 for o, l in zip(op, loud) if o == 0 and l)),
                open_while_quiet_below_minus30=int(sum(1 for o, x in zip(op, db) if o > 0 and x < -30)),
                viseme_counts=dict(Counter(vis)), drawing_changes=changes,
                holes_in_face_px=dict(min=min(holes), max=max(holes), mean=round(float(np.mean(holes)), 1),
                                      note='sampled frames 1258, 1300, 1340: all on the drawing\'s right crop edge (one pixel column, x 1179-1184 '
                                           'in the 1920x1080 frame), alpha 0.50-0.99; 0 px with alpha < 0.5 inside '
                                           'the face mask'),
                mouthless_check=d['checks'])


def test1():
    lg = json.load(open(os.path.join(T, 'test1_rig', 'test1_log.json')))
    out = {}
    for k in ('A_max_disp_px', 'B_max_disp_px'):
        out[k] = round(max(r[k] for r in lg), 1)
    for k in ('A_head_deg', 'A_chest_deg', 'A_waist_deg', 'A_hair_lag_deg', 'B_head_deg', 'B_chest_deg', 'B_waist_deg', 'B_hair_lag_deg'):
        v = [r[k] for r in lg]
        out[k + '_range'] = [round(min(v), 2), round(max(v), 2)]
    # frame-to-frame change of the whole image (detects pops / held frames)
    prev, diffs = None, []
    for r in lg:
        im = cv2.imread(os.path.join(T, 'test1_rig', '%05d.png' % r['frame']), cv2.IMREAD_REDUCED_COLOR_4).astype(np.float32)
        if prev is not None:
            diffs.append(float(np.abs(im - prev).mean()))
        prev = im
    out['frames'] = len(lg)
    out['mean_abs_frame_diff'] = dict(max=round(max(diffs), 3), median=round(float(np.median(diffs)), 3),
                                      held_frames_diff_below_0p01=int(sum(1 for x in diffs if x < 0.01)))
    return out


def strip(dirp, frames, path, crop=None, label=''):
    tiles = []
    for f in frames:
        im = cv2.imread(os.path.join(dirp, '%05d.png' % f))
        if crop:
            x, y, w, h = crop
            im = im[y:y + h, x:x + w]
        im = cv2.resize(im, (int(im.shape[1] * 300 / im.shape[0]), 300), interpolation=cv2.INTER_AREA)
        cv2.putText(im, 'f%d  %.3fs' % (f, f / FPS), (6, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    rows = [np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]
    img = np.vstack(rows)
    if label:
        bar = np.zeros((28, img.shape[1], 3), np.uint8)
        cv2.putText(bar, label, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 230, 255), 1, cv2.LINE_AA)
        img = np.vstack([bar, img])
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == '__main__':
    m = dict(test1=test1(), test2=test2())
    json.dump(m, open(os.path.join(T, 'test_metrics.json'), 'w'), indent=1)
    print(json.dumps(m, indent=1))
    strip(os.path.join(T, 'test1_rig'), [180, 204, 228, 243, 252, 264, 280, 299], os.path.join(T, 'TEST1_strip.jpg'),
          label='TEST 1 (7.5-12.5 s) full frame - local rig render, not final animation')
    strip(os.path.join(T, 'test1_rig'), [180, 228, 252, 299], os.path.join(T, 'TEST1_strip_A_head.jpg'), crop=(300, 80, 700, 620),
          label='TEST 1 crop on A head/hair/horns: frames 180 / 228 / 252 / 299')
    strip(os.path.join(T, 'test2_sing'), [1258, 1266, 1280, 1290, 1304, 1316, 1330, 1348], os.path.join(T, 'TEST2_strip.jpg'),
          crop=(620, 380, 600, 600), label='TEST 2 (52.4-56.3 s) mouth/face crop - local render, lip-sync not reviewed')
