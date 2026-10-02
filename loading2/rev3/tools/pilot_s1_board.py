"""One-page board for the P1-S1 motion pilot (v3): the approved S1 frame with the measured targets,
the S2/S3 first frames it cuts into, and the exact trim window against clip and song time.

  python3 rev3/tools/pilot_s1_board.py   ->  rev3/seedance/pilot_S1/PILOT_S1_v3_board.jpg
"""
import os

import librosa
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(R, 'seedance', 'refs_in2')
OUT = os.path.join(R, 'seedance', 'pilot_S1', 'PILOT_S1_v3_board.jpg')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
STEM = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad/audio/stem_0.wav'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# targets in the 1672x941 first-frame coordinates (same values as the pilot sheet and the check command)
ORB0, ORB_END, ORB_AFTER = (1205, 121), (1090, 205), (985, 300)
EYE = (517, 292)
LIGHT_BOX = (950, 0, 1672, 260)
HEAD_BOX = (340, 90, 640, 400)
HAND_BOX = (760, 650, 940, 770)
IN_S, DUR, SONG = 0.500, 40 / 24.0, 7.500

W, H = 1920, 1280
BG, INK, DIM, ACC, WARN = (20, 22, 30), (236, 236, 240), (150, 155, 170), (255, 196, 92), (120, 220, 235)
f = lambda s, b=False: ImageFont.truetype(FONTB if b else FONT, s)


def dashed_rect(d, box, col, w=2, dash=12):
    x0, y0, x1, y1 = box
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        n = max(1, int(np.hypot(b[0] - a[0], b[1] - a[1]) // dash))
        for k in range(0, n, 2):
            p = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
            q = a[0] + (b[0] - a[0]) * min(n, k + 1) / n, a[1] + (b[1] - a[1]) * min(n, k + 1) / n
            d.line([p, q], fill=col, width=w)


def arrow(d, a, b, col, w=3, head=14, dashed=False):
    if dashed:
        n = 10
        for k in range(0, n, 2):
            d.line([(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n),
                    (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n)], fill=col, width=w)
    else:
        d.line([a, b], fill=col, width=w)
    ang = np.arctan2(b[1] - a[1], b[0] - a[0])
    for s in (2.6, -2.6):
        d.line([b, (b[0] + head * np.cos(ang + s), b[1] + head * np.sin(ang + s))], fill=col, width=w)


def main():
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((40, 24), 'P1-S1 motion pilot v3: one action, exact 40-frame trim', font=f(34, True), fill=INK)
    d.text((40, 70), 'Board only. Nothing generated, uploaded or spent. Coordinates are in the 1672x941 first frame; '
           'the same numbers drive the check command.', font=f(19), fill=DIM)

    # S1 with targets
    s = 1220 / 1672.0
    S1 = Image.open(os.path.join(REFS, 'P1_S1_original_reference_v8.png')).convert('RGB').resize((1220, int(941 * s)), Image.LANCZOS)
    ox, oy = 40, 120
    img.paste(S1, (ox, oy))
    P = lambda p: (ox + p[0] * s, oy + p[1] * s)
    B = lambda b: (ox + b[0] * s, oy + b[1] * s, ox + b[2] * s, oy + b[3] * s)
    dashed_rect(d, B(LIGHT_BOX), WARN, 2)
    d.text((P((1250, 14))[0], P((1250, 14))[1]), 'the light stays in this box', font=f(17), fill=WARN)
    d.text((P((1250, 14))[0], P((1250, 14))[1] + 22), 'for the whole used window', font=f(17), fill=WARN)
    arrow(d, P(ORB0), P(ORB_END), ACC, 4)
    arrow(d, P(ORB_END), P(ORB_AFTER), ACC, 2, dashed=True)
    d.text((P(ORB0)[0] + 18, P(ORB0)[1] - 30), 'start (1205,121)', font=f(17), fill=ACC)
    d.text((P(ORB_END)[0] + 14, P(ORB_END)[1] - 6), 'at the cut: ~100-200 px travelled', font=f(17), fill=ACC)
    d.text((P(ORB_AFTER)[0] + 12, P(ORB_AFTER)[1] - 4), 'keeps going after the cut (enters S2 top-right)', font=f(16), fill=ACC)
    d.line([P(EYE), P(ORB0)], fill=(200, 200, 200), width=1)
    d.text((P((690, 236))[0], P((690, 236))[1]), 'eye to light: ~14 deg up', font=f(15), fill=(210, 210, 210))
    d.ellipse([P(EYE)[0] - 5, P(EYE)[1] - 5, P(EYE)[0] + 5, P(EYE)[1] + 5], outline=INK, width=2)
    d.rectangle(B(HEAD_BOX), outline=(170, 255, 170), width=2)
    d.text((B(HEAD_BOX)[0], B(HEAD_BOX)[1] - 24), 'head: eyes lead, then chin-down tilt ~8-10 deg, then hold',
           font=f(17), fill=(170, 255, 170))
    d.rectangle(B(HAND_BOX), outline=(255, 160, 160), width=2)
    d.text((B(HAND_BOX)[0] - 40, B(HAND_BOX)[3] + 4), 'hand stays put (the lift belongs to S2)', font=f(17), fill=(255, 160, 160))
    d.text((P((380, 420))[0], P((380, 420))[1]), 'lips softly parted, no speech', font=f(16), fill=INK)

    # S2 and S3: the first frames S1 cuts into (separate clips, not end frames)
    tx, tw = 1290, 590
    for k, (name, cap) in enumerate((('P1_S2_HAND_START_v2.png',
                                      ['S2 first frame (song 9.167): hand at rest, no light in frame.',
                                       'The light enters top-right; the hand lift happens in S2.']),
                                     ('P1_S3_HOVER_START_v2.png',
                                      ['S3 first frame (song 10.667): the light above her palm.',
                                       'Same path, top-right to down-left; no reset.']))):
        th = Image.open(os.path.join(REFS, name)).convert('RGB').resize((tw, int(tw * 941 / 1672)), Image.LANCZOS)
        y = 120 + k * 450
        img.paste(th, (tx, y))
        for j, line in enumerate(cap):
            d.text((tx, y + th.size[1] + 8 + j * 22), line, font=f(17), fill=INK if j == 0 else DIM)
    d.text((40, 822), 'Inputs for S1: its own first frame only. S2 and S3 are not attached to the S1 generation;',
           font=f(17), fill=DIM)
    d.text((40, 846), 'they set where S1 must end: hand at rest, light still high and moving down-left.', font=f(17), fill=DIM)

    # timeline: clip seconds 0..3.2, song = clip + 7.0
    x0, x1, T = 120, 1880, 3.2
    X = lambda t: x0 + (x1 - x0) * t / T
    y = 1010
    d.rectangle([X(IN_S), y - 6, X(IN_S + DUR), 1262], fill=(52, 46, 30))
    d.text((X(IN_S) + 8, y - 2), 'USED: clip 0.500-2.167 s = frames 12-51 -> song 7.500-9.167 (frames 180-219), 1:1',
           font=f(18, True), fill=ACC)
    for t in np.arange(0, T + 1e-6, 0.25):
        big = abs(t - round(t * 2) / 2) < 1e-6
        d.line([(X(t), 1238), (X(t), 1244 if big else 1241)], fill=DIM, width=1)
        if big:
            d.text((X(t) - 12, 1244), '%.1f' % t, font=f(13), fill=DIM)
    d.text((X(2.25), y - 2), 'clip seconds; song = clip + 7.0 s', font=f(16), fill=DIM)
    lanes = [('light', [(0.0, T, 'drifts down-left the whole clip (never stops)')], ACC),
             ('eyes', [(0.75, 1.10, 'follow')], (170, 255, 170)),
             ('head', [(1.00, 1.90, 'chin-down tilt'), (1.90, T, 'holds, watching')], (170, 255, 170)),
             ('hand', [(0.0, T, 'still (breathing only)')], (255, 160, 160))]
    for k, (nm, segs, col) in enumerate(lanes):
        yy = 1040 + k * 34
        d.text((40, yy), nm, font=f(16, True), fill=col)
        for a, b, lab in segs:
            d.rounded_rectangle([X(a), yy + 2, X(b), yy + 22], radius=6, outline=col, width=2)
            d.text((X(a) + 8, yy + 2), lab, font=f(15), fill=col)
    # vocal level from the stem (measured), mapped to clip time
    yv = 1186
    d.text((40, yv - 4), 'vocal', font=f(16, True), fill=DIM)
    try:
        v, sr = librosa.load(STEM, sr=22050, offset=7.0, duration=T)
        rms = librosa.feature.rms(y=v, hop_length=256)[0]
        rms = rms / max(rms.max(), 1e-9)
        pts = [(X(i * 256 / 22050.0), yv + 32 - 30 * r) for i, r in enumerate(rms)]
        d.line(pts, fill=DIM, width=2)
        d.text((X(0.62), yv - 10), '"one" enters at song 7.52 and swells; no beat hit in this span', font=f(14), fill=DIM)
    except Exception as e:                                # the stem is a session file, not in the repo
        d.text((X(0.62), yv), 'vocal stem not available (%s)' % type(e).__name__, font=f(14), fill=DIM)
    img.save(OUT, quality=90)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
