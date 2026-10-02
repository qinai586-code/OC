"""Review board for the rejected P1-S1 try 1 and the v4 fix.

  python3 rev3/tools/p1s1_try1_board.py   ->  rev3/seedance/review/P1-S1_try1_review_board.jpg

Needs rev3/seedance/checks/P1-S1_try1_whole/report.json (the checker run over the whole clip).
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
from p1s1_light import EYE, HEAD, head_angle, path  # noqa: E402
from seedance_check import read_frames, track_box  # noqa: E402

CLIP = os.path.join(R, 'seedance', 'returned', 'P1-S1_try1.mp4')
REPORT = os.path.join(R, 'seedance', 'checks', 'P1-S1_try1_whole', 'report.json')
V8 = os.path.join(R, 'seedance', 'refs_in2', 'P1_S1_original_reference_v8.png')
NOLIGHT = os.path.join(R, 'seedance', 'refs_in2', 'P1_S1_v8_nolight.png')
OUT = os.path.join(R, 'seedance', 'review', 'P1-S1_try1_review_board.jpg')
FONT, FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG, INK, INK2, MUTED, GRID = (26, 26, 25), (255, 255, 255), (195, 194, 183), (130, 130, 125), (58, 58, 56)
TRY1, TARGET = (217, 89, 38), (57, 135, 229)          # validated dark categorical slots 2 and 1
NOMINAL_IN = 17                                       # v4 nominal: head onset at clip frame 26 -> window from 17
f = lambda s, b=False: ImageFont.truetype(FONTB if b else FONT, s)


def bgr2pil(a):
    return Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))


def main():
    fr = read_frames(CLIP)
    H, W = fr[0].shape[:2]
    sx, sy = W / 1672.0, H / 941.0
    rot = np.array([t[0] for t in track_box(fr, list(range(len(fr))), [340, 90, 640, 400], sx, sy)])
    rep = json.load(open(REPORT))
    lp = [(t['frame'], t['main'][1] / sx, t['main'][2] / sy) for t in rep['track'] if t['main']]

    img = Image.new('RGB', (1920, 1270), BG)
    d = ImageDraw.Draw(img)
    d.text((40, 24), 'P1-S1 try 1: rejected. What failed, and the v4 fix', font=f(34, True), fill=INK)
    d.text((40, 70), 'Measured on the returned file (1280x720, 24 fps, 121 frames, 5.04 s). Not accepted footage; '
           'nothing here is used in the edit.', font=f(19), fill=INK2)

    # A. faces through the clip
    d.text((40, 116), 'A. Her head through the clip (try 1)', font=f(22, True), fill=INK)
    caps = [(0, 'f0, 0.00 s: start (approved)'), (34, 'f34, 1.42 s: blink'),
            (60, 'f60, 2.50 s: 14.7 deg, turned'), (120, 'f120, 5.00 s: 17.7 deg')]
    for i, (k, cap) in enumerate(caps):
        tile = bgr2pil(cv2.resize(fr[k][40:330, 170:480], (270, 252), interpolation=cv2.INTER_AREA))
        x = 40 + i * 282
        img.paste(tile, (x, 150))
        d.text((x, 408), cap, font=f(16), fill=INK2)
    d.text((40, 436), 'The far horn separates from the near one as she turns toward the camera; by the end her gaze passes',
           font=f(16), fill=MUTED)
    d.text((40, 458), 'under the light. One-frame texture pops at f10, f60, f110 (measured).', font=f(16), fill=MUTED)

    # B. head rotation chart: one y-scale (deg chin-down) over clip seconds
    cx0, cy0, cw, ch = 110, 560, 1040, 400
    d.text((40, 506), 'B. Head rotation, chin-down (deg) over clip time', font=f(22, True), fill=INK)
    ymax = 20.0
    X = lambda t: cx0 + cw * t / 5.0
    Y = lambda v: cy0 + ch - ch * v / ymax
    for v in range(0, 21, 5):
        d.line([(cx0, Y(v)), (cx0 + cw, Y(v))], fill=GRID, width=1)
        d.text((cx0 - 40, Y(v) - 10), '%d' % v, font=f(15), fill=MUTED)
    for t in range(0, 6):
        d.text((X(t) - 5, cy0 + ch + 8), '%d' % t, font=f(15), fill=MUTED)
    d.text((cx0 + cw - 120, cy0 + ch + 30), 'clip seconds', font=f(15), fill=MUTED)
    # v4 window (nominal) and the try-1 blink
    d.rectangle([X(NOMINAL_IN / 24.0), cy0, X((NOMINAL_IN + 40) / 24.0), cy0 + ch], fill=(36, 44, 58))
    d.text((X(NOMINAL_IN / 24.0) + 6, cy0 + 6), 'v4 used window (nominal): 40 frames = song 7.500-9.167', font=f(15), fill=INK2)
    for xx in np.arange(X(32 / 24.0), X(37 / 24.0), 6):
        d.line([(xx, cy0 + ch), (xx + 30, cy0 + ch - 60)], fill=MUTED, width=1)
    d.text((X(32 / 24.0) - 4, cy0 + ch - 82), 'blink', font=f(15), fill=INK2)
    pts = [(X(i / 24.0), Y(max(0.0, v))) for i, v in enumerate(rot)]
    d.line(pts, fill=TRY1, width=2)
    tgt = [(X((NOMINAL_IN + k) / 24.0), Y(head_angle(k))) for k in range(40)]
    tgt = [(X(0), Y(0)), (X(NOMINAL_IN / 24.0), Y(0))] + tgt + [(X(5.0), Y(head_angle(39)))]
    d.line(tgt, fill=TARGET, width=2)
    d.text((X(3.3), Y(rot[-1]) - 34), 'try 1 (measured): 17.7 deg, never settles', font=f(16), fill=INK2)
    d.text((X(2.6), Y(head_angle(39)) + 8), 'v4 target: 6 deg, settles by window frame 29', font=f(16), fill=INK2)
    lx = cx0 + 10
    for j, (col, name) in enumerate(((TRY1, 'try 1, measured'), (TARGET, 'v4 target (pitch only)'))):
        d.line([(lx + j * 260, cy0 + ch + 62), (lx + j * 260 + 34, cy0 + ch + 62)], fill=col, width=3)
        d.text((lx + j * 260 + 42, cy0 + ch + 52), name, font=f(15), fill=INK2)

    # C. eyeline geometry on the approved frame
    s = 700 / 1672.0
    v8 = cv2.resize(cv2.imread(V8), (700, int(941 * s)), interpolation=cv2.INTER_AREA)
    gx, gy = 1190, 150
    img.paste(bgr2pil(v8), (gx, gy))
    P = lambda p: (gx + p[0] * s, gy + p[1] * s)
    d.text((1190, 116), 'C. Why her head dropped so far', font=f(22, True), fill=INK)
    e = P(EYE)
    st = dict(stroke_width=2, stroke_fill=(10, 10, 16))
    r = np.radians(32)
    L = (EYE[1] - 4) / np.sin(r)
    d.line([e, P((EYE[0] + L * np.cos(r), 4))], fill=INK, width=2)
    d.text(P((1000, 4)), 'drawn gaze ~30-40 deg (estimate)', font=f(15), fill=INK, **st)
    d.line([e, P((1205, 121))], fill=TRY1, width=1)
    d.line([P((x, y)) for _, x, y in lp], fill=TRY1, width=4)
    d.text(P((1240, 95)), 'try 1 light', font=f(15), fill=INK, **st)
    d.text(P((1020, 300)), 'old light: 15 deg up', font=f(15), fill=INK, **st)
    d.line([P(path(k)[:2]) for k in range(40)], fill=TARGET, width=4)
    d.text(P((935, 108)), 'v4 light', font=f(15), fill=INK, **st)
    d.text((1190, gy + v8.shape[0] + 8), 'The model lowered her head ~18 deg until her eyes met a light 15 deg up.',
           font=f(16), fill=INK2)
    d.text((1190, gy + v8.shape[0] + 30), 'v4 starts the light on her drawn eyeline (32 deg) and lowers it 14 deg,',
           font=f(16), fill=INK2)
    d.text((1190, gy + v8.shape[0] + 52), 'so a 6 deg dip plus her eyes can follow it.', font=f(16), fill=INK2)

    # D. light behaviour, measured
    d.text((1190, 610), 'D. Light, try 1 (measured)', font=f(22, True), fill=INK)
    v = [np.hypot(lp[i + 1][1] - lp[i][1], lp[i + 1][2] - lp[i][2]) for i in range(len(lp) - 1)]
    rows = ['constant speed %.2f px/frame (sd %.2f): a straight rail' % (np.mean(v), np.std(v)),
            'net path (1187,118) -> (997,242): aimed at her face, not her hand',
            '74 px inside the 1.667 s window: reads as a slow moon',
            'size constant; one light in all 121 frames',
            'camera: locked (<= 2.2 px background shift, measured)']
    for j, t in enumerate(rows):
        d.text((1190, 646 + j * 26), t, font=f(16), fill=INK2)

    # E. the generation input for v4 (light removed locally)
    d.text((1190, 800), 'E. v4 input: approved frame, light removed locally', font=f(22, True), fill=INK)
    a, b = cv2.imread(V8), cv2.imread(NOLIGHT)
    crop = lambda im: cv2.resize(im[0:300, 1000:1420], (340, 243), interpolation=cv2.INTER_AREA)
    img.paste(bgr2pil(crop(a)), (1190, 836))
    img.paste(bgr2pil(crop(b)), (1550, 836))
    d.text((1190, 1084), 'approved v8 (crop)', font=f(15), fill=INK2)
    d.text((1550, 1084), 'P1_S1_v8_nolight (crop)', font=f(15), fill=INK2)
    d.text((1190, 1108), 'Only sky pixels within 165 px of the old light change; she is untouched.', font=f(16), fill=INK2)
    d.text((1190, 1130), 'The light is then composited locally, with the same measured look.', font=f(16), fill=INK2)

    # F. split
    d.text((40, 1100), 'F. Local vs new footage', font=f(22, True), fill=INK)
    left = ['LOCAL (no generation): the light (look, path, size, speed, pulse), removing any generated light,',
            'one-frame texture pops (f10, f60, f110: hold a neighbour), upscale to 1080p, fit to the locked music.']
    right = ['NEW FOOTAGE NEEDED: her performance. No 40-frame window of try 1 starts in the approved pose and stays',
             'within a 4-8 deg settled dip without the blink (measured). A local 2D rotation is only a timing placeholder.']
    for j, t in enumerate(left + right):
        d.text((40, 1136 + j * 28), t, font=f(17), fill=INK2 if j < 2 else INK)
    img.save(OUT, quality=90)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
