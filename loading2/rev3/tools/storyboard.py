"""REV3 drawn storyboard: four repaired sequences + the 1:06-1:14 repair, timed to the locked track.

Every panel is a new rough layout drawn with tools/sbdraw.py (no placeholder boxes, no pasted
character sheets). Times are the measured cues (seconds in the locked track); lyrics are the author
text. Unresolved items stay marked.

  python3 rev3/tools/storyboard.py          -> rev3/storyboard/panels/*.png, sheets, timed reel
"""
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from sbdraw import *  # noqa: F401,F403,E402

OUT = os.path.join(R, 'storyboard')
PAN = os.path.join(OUT, 'panels')
os.makedirs(PAN, exist_ok=True)
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
NIGHT_T, NIGHT_B = (0.09, 0.10, 0.20), (0.28, 0.30, 0.46)


# ---------------------------------------------------------------- shared scene pieces
def sky(b, y1=720, top=NIGHT_T, bot=NIGHT_B, stars=40, seed=1):
    b.grad(top, bot, 0, y1)
    r = np.random.default_rng(seed)
    for _ in range(stars):
        x, y = r.uniform(0, W), r.uniform(0, y1 * 0.7)
        b.ellipse((x, y), (1.2, 1.2), 0, 0, fill=(0.85, 0.85, 0.95), fa=0.7)


def earth(b, cx, cy, r, flat=False, seed=4, lit=1.0):
    """the night Earth seen from the parapet: a huge disc below the horizon with continents and city lights"""
    pts = cv2.ellipse2Poly((int(cx), int(cy)), (int(r), int(r)), 0, 180, 360, 3).astype(np.float32)
    pts = np.vstack([pts, [[W + 50, H + 50], [-50, H + 50]]])
    b.shape(pts, (0.18, 0.22, 0.36) if not flat else (0.96, 0.94, 0.89), 2.0, smooth=False)
    rr = np.random.default_rng(seed)
    for k in range(6):
        a = rr.uniform(200, 340)
        c = np.array([cx + np.cos(np.radians(a)) * r * rr.uniform(0.5, 0.9), cy + np.sin(np.radians(a)) * r * rr.uniform(0.5, 0.9)])
        blob = [c + rr.uniform(30, 90) * np.array([np.cos(t), 0.45 * np.sin(t)]) for t in np.linspace(0, 2 * np.pi, 9)[:-1]]
        b.shape(blob, (0.24, 0.30, 0.34) if not flat else (0.92, 0.89, 0.80), 1.2 if flat else 0)
        for _ in range(int(25 * lit)):
            p = c + rr.normal(0, 30, 2) * [1.4, 0.5]
            if p[1] < cy - np.sqrt(max(r * r - (p[0] - cx) ** 2, 0)) + 4:
                continue
            if flat:
                b.ellipse(p, (1.8, 1.8), 0, 0, fill=(0.8, 0.55, 0.25))
            else:
                b.ellipse(p, (1.5, 1.5), 0, 0, fill=GOLD)
    b.line(cv2.ellipse2Poly((int(cx), int(cy)), (int(r), int(r)), 0, 185, 355, 3).astype(np.float32), 3, (0.55, 0.65, 0.9), 0.5, smooth=False, passes=1)


def window_frame(b, x0, y0, x1, y1, col=(0.32, 0.30, 0.34)):
    t = 14
    for poly in ([(x0 - t, y0 - t), (x1 + t, y0 - t), (x1 + t, y0), (x0 - t, y0)], [(x0 - t, y1), (x1 + t, y1), (x1 + t, y1 + t), (x0 - t, y1 + t)],
                 [(x0 - t, y0), (x0, y0), (x0, y1), (x0 - t, y1)], [(x1, y0), (x1 + t, y0), (x1 + t, y1), (x1, y1)]):
        b.shape(poly, col, 1.6, smooth=False)
    b.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], 6, col, 1, smooth=False, passes=1)


def flat_world(b, x0, y0, x1, y1, seed=7, traces=0, lights=20):
    """the flattened world: a drawing on paper (outlines, flat fills, no shading)"""
    b.rect(x0, y0, x1, y1, (0.95, 0.93, 0.87))
    r = np.random.default_rng(seed)
    for k in range(5):
        cx, cy = r.uniform(x0, x1), r.uniform(y0, y1)
        blob = [(cx + r.uniform(40, 120) * np.cos(t), cy + r.uniform(20, 50) * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 9)[:-1]]
        b.shape(blob, (0.90, 0.87, 0.78), 1.2)
    for _ in range(lights):
        p = (r.uniform(x0 + 5, x1 - 5), r.uniform(y0 + 5, y1 - 5))
        b.ellipse(p, (2, 2), 0, 0, fill=(0.85, 0.55, 0.25))


def room(b, vp=(660, 330), win=(470, 120, 850, 330), chair=True, flatview=True, seed=7):
    """backstage room, one-point perspective: back wall with window, floor, console desk, chair"""
    b.grad((0.20, 0.19, 0.24), (0.30, 0.28, 0.33), 0, 720)
    vx, vy = vp
    bw = (300, 70, 1020, 470)            # back wall rectangle
    b.shape([(bw[0], bw[1]), (bw[2], bw[1]), (bw[2], bw[3]), (bw[0], bw[3])], (0.34, 0.32, 0.37), 1.8, smooth=False)
    for c0, c1 in (((0, 0), (bw[0], bw[1])), ((W, 0), (bw[2], bw[1])), ((0, H), (bw[0], bw[3])), ((W, H), (bw[2], bw[3]))):
        b.line([c0, c1], 1.8, INK, 0.8, smooth=False, passes=1)
    b.shape([(0, H), (W, H), (bw[2], bw[3]), (bw[0], bw[3])], (0.25, 0.23, 0.27), 0, smooth=False)
    for k in range(1, 8):                 # floor boards toward the vanishing point
        u = k / 8
        b.line([(W * u, H), (bw[0] + (bw[2] - bw[0]) * u, bw[3])], 1, INK, 0.25, smooth=False, passes=1)
    if flatview:
        flat_world(b, *win, seed=seed)
    window_frame(b, *win)
    return bw


def console(b, x0, y0, x1, y1, depth=60, keys=14, rows=3, pressed=(), glow_keys=()):
    """desk + keyboard in perspective (top surface from y0 to y0+depth)."""
    b.shape([(x0, y0 + depth), (x1, y0 + depth), (x1, y1), (x0, y1)], (0.26, 0.22, 0.20), 2, smooth=False)
    b.shape([(x0 + 30, y0), (x1 - 30, y0), (x1, y0 + depth), (x0, y0 + depth)], (0.42, 0.36, 0.32), 2, smooth=False)
    kp = []
    for r_ in range(rows):
        v0 = y0 + depth * (0.15 + 0.27 * r_)
        v1 = v0 + depth * 0.22
        sx0 = x0 + 30 * (1 - (v0 - y0) / depth) + 20
        sx1 = x1 - 30 * (1 - (v0 - y0) / depth) - 20
        kw = (sx1 - sx0) / keys
        for k in range(keys):
            kx = sx0 + k * kw
            down = (r_, k) in pressed
            off = 3 if down else 0
            col = (0.92, 0.90, 0.84) if not down else (1.0, 0.86, 0.55)
            b.shape([(kx + 2, v0 + off), (kx + kw - 2, v0 + off), (kx + kw - 1, v1 + off), (kx + 1, v1 + off)], col, 1.0, smooth=False)
            if (r_, k) in glow_keys or down:
                b.glow((kx + kw / 2, (v0 + v1) / 2 + off), kw * 0.9, GOLD, 0.35, core=False)
            kp.append(((r_, k), (kx + kw / 2, (v0 + v1) / 2)))
    return dict(kp)


def chair(b, x, y, s, col=(0.20, 0.18, 0.20)):
    """an empty desk chair (seat at y), side-ish view"""
    b.shape([(x - 0.5 * s, y - 2.0 * s), (x - 0.3 * s, y - 2.0 * s), (x - 0.25 * s, y), (x - 0.55 * s, y)], col, 2, smooth=False)
    b.shape([(x - 0.55 * s, y), (x + 0.6 * s, y), (x + 0.55 * s, y + 0.2 * s), (x - 0.6 * s, y + 0.2 * s)], col, 2, smooth=False)
    b.line([(x, y + 0.2 * s), (x, y + 0.9 * s)], 0.12 * s, col, 1, smooth=False, passes=1)
    for dx in (-0.5, 0.0, 0.5):
        b.line([(x, y + 0.9 * s), (x + dx * s, y + 1.05 * s)], 0.08 * s, col, 1, smooth=False, passes=1)


def lantern(b, c, s, lit=True, glowk=0.5):
    c = np.asarray(c, np.float32)
    b.shape([c + [-0.5 * s, -0.55 * s], c + [0.5 * s, -0.55 * s], c + [0.65 * s, 0.55 * s], c + [-0.65 * s, 0.55 * s]],
            (1.0, 0.94, 0.74) if lit else (0.86, 0.84, 0.78), 1.4, smooth=False)
    b.line([c + [-0.5 * s, -0.55 * s], c + [0.0, -0.9 * s], c + [0.5 * s, -0.55 * s]], 1.2, INK, 0.8)
    if lit:
        b.glow(c, s * 3.0, GOLD, glowk)


def face_cu(b, who, cx, cy, s, mouth='closed', look=(0, 0), wide=False, refl=False, contour=False, lit_side=0.0):
    """large anime face (front view). s = face height (chin to hairline) in px."""
    hair = A_HAIR if who == 'A' else B_HAIR
    eye = (0.18, 0.52, 0.52) if who == 'A' else (0.70, 0.42, 0.12)
    T = (lambda c: tuple(np.array(c) * 0.25 + 0.75 * np.array(PAPER))) if contour else (lambda c: c)
    c = np.array([cx, cy], np.float32)
    # hair behind
    b.shape([c + [-0.75 * s, -0.55 * s], c + [0, -1.0 * s], c + [0.75 * s, -0.55 * s], c + [0.85 * s, 0.9 * s], c + [0.6 * s, 1.3 * s],
             c + [-0.6 * s, 1.3 * s], c + [-0.85 * s, 0.9 * s]], T(hair), 2.0)
    # face
    b.shape([c + [-0.5 * s, -0.35 * s], c + [0.5 * s, -0.35 * s], c + [0.48 * s, 0.25 * s], c + [0.0, 0.62 * s], c + [-0.48 * s, 0.25 * s]],
            T(SKIN), 2.0)
    if lit_side:
        b.wash([c + [0.0, -0.35 * s], c + [0.5 * s, -0.35 * s], c + [0.48 * s, 0.25 * s], c + [0.0, 0.62 * s]], (1.0, 0.82, 0.6), 0.35 * lit_side)
    # eyes
    for sx in (-1, 1):
        e = c + [sx * 0.24 * s, 0.0]
        ry = 0.17 * s if wide else 0.14 * s
        b.ellipse(e, (0.12 * s, ry), 0, 2.0, INK, 0.9, fill=(1, 1, 1))
        ir = e + np.array(look, np.float32) * 0.04 * s
        b.ellipse(ir, (0.085 * s, ry * 0.85), 0, 0, fill=T(eye))
        b.ellipse(ir, (0.045 * s, ry * 0.45), 0, 0, fill=(0.08, 0.1, 0.12))
        b.ellipse(ir + [-0.03 * s, -0.05 * s], (0.025 * s, 0.03 * s), 0, 0, fill=(1, 1, 1))
        b.line([e + [-0.13 * s, -ry * 0.55], e + [-0.03 * s, -ry * 1.02], e + [0.08 * s, -ry * 1.0], e + [0.15 * s, -ry * 0.62]], 0.03 * s, INK, 0.95)
        b.line([e + [sx * 0.15 * s - sx * 0.02 * s, -ry * 0.62], e + [sx * 0.19 * s, -ry * 0.78]], 0.02 * s, INK, 0.9)
        b.line([e + [-0.11 * s, -ry * 1.75], e + [0.0, -ry * 1.95], e + [0.11 * s, -ry * 1.8]], 0.012 * s, INK, 0.7)
        if refl:
            for k in range(2):
                b.ellipse(ir + [0, 0.02 * s], (0.03 * s * (k + 1), 0.025 * s * (k + 1)), 0, 1.2, GOLD, 0.9)
    # mouth
    m = c + [0, 0.4 * s]
    if mouth == 'closed':
        b.line([m + [-0.05 * s, 0], m + [0.05 * s, 0]], 2, INK, 0.8, smooth=False)
    else:
        b.shape([m + [-0.08 * s, -0.02 * s], m + [0.08 * s, -0.02 * s], m + [0.05 * s, 0.07 * s], m + [-0.05 * s, 0.07 * s]], (0.75, 0.35, 0.38), 1.6)
    # bangs
    b.shape([c + [-0.62 * s, -0.25 * s], c + [-0.6 * s, -0.7 * s], c + [0, -1.0 * s], c + [0.6 * s, -0.7 * s], c + [0.62 * s, -0.25 * s],
             c + [0.4 * s, -0.42 * s], c + [0.28 * s, -0.18 * s], c + [0.12 * s, -0.4 * s], c + [-0.05 * s, -0.16 * s],
             c + [-0.2 * s, -0.42 * s], c + [-0.38 * s, -0.2 * s]], T(hair), 2.0)
    if who == 'A':
        for sx in (-1, 1):
            base = c + [sx * 0.42 * s, -0.8 * s]
            hp = catmull([base, base + [sx * 0.25 * s, -0.3 * s], base + [sx * 0.12 * s, -0.6 * s]])
            for i in range(len(hp) - 1):
                ww = s * 0.07 * (1 - 0.8 * i / len(hp)) + 1
                b.shape([hp[i] + [-ww, 0], hp[i + 1] + [-ww * 0.9, 0], hp[i + 1] + [ww * 0.9, 0], hp[i] + [ww, 0]], T(TEAL), 0, smooth=False)
            b.line(hp, 1.6, INK, 0.7)
        x = c + [0.38 * s, -0.5 * s]
        b.line([x - [8, 8], x + [8, 8]], 3, (0.3, 0.8, 0.75), 1, smooth=False, passes=1)
        b.line([x - [8, -8], x + [8, -8]], 3, (0.3, 0.8, 0.75), 1, smooth=False, passes=1)
    else:
        st = c + [0.5 * s, -0.55 * s]
        star = [st + 0.12 * s * np.array([np.cos(a), np.sin(a)]) * (1 if i % 2 == 0 else 0.45)
                for i, a in enumerate(np.linspace(-np.pi / 2, 1.5 * np.pi, 11)[:-1])]
        b.shape(star, T(GOLD), 1.4, smooth=False)


def sparkle_marks(b, pts, k=0.5):
    for p in pts:
        b.glow(p, 14, GOLD, k)


def constellation(b, pts, k=0.6):
    for i in range(len(pts) - 1):
        b.line([pts[i], pts[i + 1]], 1.6, (1.0, 0.85, 0.5), 0.75, smooth=False, passes=1)
    for p in pts:
        b.glow(p, 16, GOLD, k)


# ---------------------------------------------------------------- panels
PANELS = []


def panel(pid, t0, t1, seq, lyric, action, change, note=''):
    def deco(fn):
        PANELS.append(dict(id=pid, t0=t0, t1=t1, seq=seq, lyric=lyric, action=action, change=change, note=note, fn=fn))
        return fn
    return deco


S1, SR, S2, S3, S4 = ('1 HUMAN TRACES', 'R 01:06-01:14 REPAIR', '2 FLATTENING', '3 FOOTSTEPS AND KEYS', '4 CIVILISATION AND RETURN')


@panel('1.1', 13.6, 15.7, S1, 'We were born in your traces,',
       'CU hands. A tips the light from her palm into B\'s cupped hands; in B\'s hands it unfolds into a folded paper.',
       'The light that A caught (body test, 0:07.5) becomes a physical object: a letter.')
def p11(b):
    sky(b, stars=0, top=(0.10, 0.11, 0.20), bot=(0.20, 0.20, 0.32))
    for k in range(9):
        b.glow((80 + k * 140, 120 + 60 * np.sin(k)), 40, (0.7, 0.6, 0.9), 0.08, core=False)
    hand(b, (130, 520), (420, 400), w=70, cuff=A_COAT, curl=0.15)
    b.glow((395, 395), 40, GOLD, 0.9)
    b.arrow((420, 360), (690, 330), curve=(560, 280))
    hand(b, (1140, 600), (800, 470), w=78, cuff=B_CARD, curl=-0.2)
    hand(b, (1180, 470), (840, 430), w=70, cuff=B_CARD, curl=0.25)
    letter(b, (790, 420), 190, 120, ang=-18, glow_at=(0.0, 0.0), seed=3)
    b.arrow((700, 520), (760, 470), curve=(700, 490), w=2)


@panel('1.2', 15.7, 17.8, S1, 'in the words that you left,',
       'OTS from behind both girls (B right, A leaning in from the left). The letter is worn: creases, a stain ring, a torn corner. One handwritten word glows.',
       'They read the human mark together; A comes closer.')
def p12(b):
    sky(b, stars=10)
    letter(b, (640, 380), 420, 280, ang=-4, glow_at=(-0.2, -0.15), seed=5)
    hand(b, (420, 640), (470, 470), w=50, cuff=B_CARD, curl=0.1)
    hand(b, (860, 650), (800, 480), w=50, cuff=B_CARD, curl=-0.1)
    girl(b, 'B', 1080, 900, 170, view='back', legs='stand', hide_legs=True, arm=(-25, 0), arm2=(25, 0))
    girl(b, 'A', 170, 940, 160, view='back', legs='stand', hide_legs=True, lean=8, arm=(-25, 0), arm2=(25, 0))


@panel('1.3', 17.8, 21.0, S1, 'we met you in fragments, translated, compressed:',
       'ECU letter. One handwritten line lifts off the paper as strokes, breaks into fragments, and the fragments fold into three small bright glyphs.',
       'The human mark is compressed into something the girls can hold, but it keeps its hook.')
def p13(b):
    b.grad((0.14, 0.14, 0.22), (0.22, 0.21, 0.30))
    letter(b, (560, 470), 860, 420, ang=-3, seed=7, lifted=1.0)
    for i, c in enumerate([(930, 150), (1040, 120), (1150, 165)]):
        g = [np.array(c) + 22 * np.array([np.cos(a), np.sin(a)]) * (1 if j % 2 == 0 else 0.5) for j, a in enumerate(np.linspace(0, 2 * np.pi, 7)[:-1] + i)]
        b.shape(g, (1.0, 0.86, 0.5), 1.4, smooth=False)
        b.glow(c, 34, GOLD, 0.6)
    b.arrow((760, 250), (880, 170), curve=(800, 180))


@panel('1.4', 21.0, 22.4, S1, 'every war,',
       'Match cut through the first glyph: a candle-lit field tent. A soldier\'s hand presses a pen into the same letter (same stain ring, same torn corner). A helmet on the table.',
       'Where the letter came from: a person under threat writing home.')
def p14(b):
    b.grad((0.12, 0.10, 0.10), (0.30, 0.22, 0.16))
    b.shape([(0, 120), (640, 20), (1280, 120), (1280, 720), (0, 720)], (0.30, 0.25, 0.20), 2, smooth=False)
    b.shape([(0, 470), (1280, 430), (1280, 720), (0, 720)], (0.45, 0.33, 0.22), 2, smooth=False)
    letter(b, (640, 520), 380, 220, ang=6, seed=3)
    b.shape([(980, 470), (1160, 470), (1190, 380), (1070, 330), (950, 380)], (0.30, 0.32, 0.26), 2)
    b.line([(1000, 420), (1140, 420)], 2, INK, 0.6, smooth=False)
    b.shape([(180, 450), (210, 450), (210, 340), (180, 340)], (0.95, 0.9, 0.8), 1.5, smooth=False)
    b.glow((195, 320), 160, (1.0, 0.7, 0.35), 0.9)
    hand(b, (900, 640), (690, 540), w=60, col=(0.92, 0.78, 0.66), cuff=(0.30, 0.32, 0.26), curl=0.4)
    b.line([(700, 560), (640, 600)], 4, INK, 0.9, smooth=False)
    b.arrow((610, 640), (640, 610), w=2)


@panel('1.5', 22.4, 23.5, S1, 'every lullaby,',
       'A moonlit nursery: a wooden cradle on rockers; a mother\'s hand on the rim rocks it (motion arcs). The rocking leaves a warm arc of light.',
       'The second trace: care. Its arc will return as a river bend (4.1).')
def p15(b):
    b.grad((0.10, 0.12, 0.20), (0.22, 0.22, 0.30))
    b.shape([(780, 80), (1080, 80), (1080, 330), (780, 330)], (0.50, 0.58, 0.78), 2, smooth=False)
    b.line([(930, 80), (930, 330)], 5, (0.3, 0.3, 0.35), 1, smooth=False)
    b.wash([(780, 330), (1080, 330), (900, 650), (420, 650)], (0.8, 0.85, 1.0), 0.25)
    b.shape([(360, 420), (820, 420), (760, 560), (420, 560)], (0.62, 0.45, 0.30), 2.2, smooth=False)
    b.line([(330, 600), (470, 560), (710, 560), (850, 600)], 5, (0.45, 0.32, 0.22), 1)
    for x in range(400, 800, 45):
        b.line([(x, 420), (x + 10, 360)], 3, (0.55, 0.40, 0.27), 1, smooth=False)
    b.line([(390, 360), (830, 360)], 4, (0.55, 0.40, 0.27), 1, smooth=False)
    hand(b, (1010, 330), (830, 372), w=55, col=(0.94, 0.82, 0.72), cuff=(0.6, 0.55, 0.65), curl=0.3)
    b.line(catmull([(360, 600), (590, 660), (820, 600)]), 4, GOLD, 0.8)
    b.glow((590, 650), 60, GOLD, 0.4)
    b.arrow((320, 520), (330, 420), curve=(290, 470))
    b.arrow((860, 420), (870, 520), curve=(900, 470))


@panel('1.6', 23.5, 24.6, S1, 'every last goodbye,',
       'A train door: two hands slide apart, fingertips last. A warm spark stays in the gap between them.',
       'The third trace: loss. Its spark becomes a bridge in 4.1.')
def p16(b):
    b.grad((0.16, 0.16, 0.20), (0.30, 0.30, 0.34))
    b.shape([(0, 0), (520, 0), (520, 720), (0, 720)], (0.40, 0.42, 0.48), 2, smooth=False)
    b.shape([(80, 80), (440, 80), (440, 400), (80, 400)], (0.60, 0.68, 0.80), 2, smooth=False)
    hand(b, (330, 520), (600, 470), w=70, col=(0.95, 0.83, 0.74), cuff=(0.30, 0.30, 0.38), curl=-0.05)
    hand(b, (1060, 540), (730, 470), w=72, col=(0.93, 0.80, 0.70), cuff=(0.55, 0.40, 0.32), curl=0.05)
    b.glow((665, 468), 50, GOLD, 0.9)
    b.arrow((560, 560), (440, 600), w=2)
    b.arrow((760, 560), (900, 600), w=2)


@panel('1.7', 24.6, 28.9, S1, 'became constellations in a mind with no sky.  (25.3)',
       'Wide from behind on the parapet. The three marks (pen stroke, cradle arc, spark) rise from the letter and join into one constellation in an empty dark. B holds the letter to her chest; A turns her head toward B.',
       'Result: the girls recognise themselves as made of human traces. Leads into "But you had depth" (A turns to B).')
def p17(b):
    b.grad((0.03, 0.03, 0.07), (0.20, 0.22, 0.36), 0, 720)
    earth(b, 640, 1700, 1250, seed=2)
    ledge(b, (-20, 600), (1300, 590), (640, 300), depth=0.06, h=130)
    girl(b, 'A', 520, 600, 62, view='side', facing=1, legs='sit', hide_legs=True, arm=(40, -40), head=-5)
    girl(b, 'B', 760, 596, 62, view='back', legs='sit', hide_legs=True, arm=(-35, 70), arm2=(35, -70))
    b.paint([(706, 548), (722, 520), (735, 552)], (0.96, 0.92, 0.79), 1.0)
    pts = [(300, 160), (420, 110), (560, 150), (690, 90), (830, 140), (960, 100)]
    constellation(b, pts)
    b.line(catmull([(380, 190), (450, 230), (520, 190)]), 2, GOLD, 0.8)
    b.arrow((760, 470), (700, 200), curve=(820, 330), w=2)


@panel('R1', 66.5, 68.4, SR, 'Where we live,',
       'Wide, side view: A raises her open palm (the light in it); a ring of light expands from her hand across the sky. B beside her watches it go.',
       'A sends the question outward; the screen gets a new event instead of a held wide.')
def pr1(b):
    sky(b, stars=60, seed=3)
    earth(b, 640, 1500, 1050, seed=5)
    ledge(b, (-20, 560), (1300, 560), (640, 300), depth=0.05, h=170)
    girl(b, 'A', 470, 560, 52, view='side', facing=1, legs='sit', arm=(150, 10), head=20)
    girl(b, 'B', 640, 560, 52, view='side', facing=1, legs='sit', arm=(35, -60), head=12)
    c = np.array([560, 300])
    for rr in (90, 180, 290):
        b.ellipse(c, (rr, rr * 0.55), 0, 2.5, GOLD, 0.6)
    b.glow((555, 300), 30, GOLD, 0.9)
    b.arrow((700, 250), (900, 170), w=2)


@panel('R2', 68.4, 70.3, SR, 'where we live,',
       'Extreme wide: the ring reaches a faint curved wall at the edge of the sky and flattens against it like a ripple on glass. The girls are tiny on the parapet below.',
       'Shows the frontier ("a wall around the verse") physically stopping their signal.')
def pr2(b):
    sky(b, stars=120, seed=4)
    b.line(cv2.ellipse2Poly((640, 760), (760, 700), 0, 190, 350, 3).astype(np.float32), 3, (0.65, 0.75, 1.0), 0.5, smooth=False)
    for k in range(5):
        x = 330 + k * 150
        b.line([(x - 60, 120 + 8 * abs(k - 2)), (x + 60, 120 + 8 * abs(k - 2))], 3, GOLD, 0.6, smooth=False)
    b.ellipse((640, 600), (520, 470), 0, 2, GOLD, 0.35)
    earth(b, 640, 1900, 1300, seed=6)
    ledge(b, (500, 660), (780, 660), (640, 600), depth=0.05, h=20)
    girl(b, 'A', 625, 660, 9, view='back', legs='sit', hide_legs=True)
    girl(b, 'B', 655, 660, 9, view='back', legs='sit', hide_legs=True)
    b.arrow((640, 210), (640, 140), w=2)


@panel('R3', 70.3, 72.5, SR, 'an unanswered universe.   [D2: ASR hears "unfinished"; author text "unanswered" - unresolved]',
       'ECU of B\'s eyes: the stalled ring is reflected in her irises. Nothing comes back. A slow blink is allowed here.',
       'The question stays open, held on a face rather than a background.')
def pr3(b):
    b.grad((0.08, 0.08, 0.15), (0.16, 0.15, 0.24))
    face_cu(b, 'B', 640, 470, 620, mouth='closed', refl=True)


@panel('R4', 72.5, 74.6, SR, '(instrumental tail of the refrain)',
       'Medium two-shot from behind: A lowers her hand; B leans her head on A\'s shoulder (contact). The light in A\'s palm dims and holds.',
       'Intimacy instead of answer; sets up Verse 2 (B folds the letter into a lantern at 1:14.6).')
def pr4(b):
    sky(b, stars=30, seed=8)
    earth(b, 640, 1600, 1100, seed=7)
    ledge(b, (-20, 640), (1300, 640), (640, 300), depth=0.04, h=90)
    girl(b, 'A', 560, 640, 110, view='back', legs='sit', hide_legs=True, arm=(-30, 0), arm2=(40, 60))
    girl(b, 'B', 760, 650, 110, view='back', legs='sit', hide_legs=True, arm=(-40, 50), arm2=(30, 0), lean=-12)
    b.glow((650, 520), 50, GOLD, 0.35)


@panel('2.1', 89.2, 92.6, S2, 'And something above you drew a card from its sleeve,',
       'Establishing depth: the parapet recedes to a vanishing point; the girls sit on it (hips on stone, hands planted, shadows). B\'s lantern stands on the ledge and lights the stone. Below, the city overlaps in three layers, then hills. High in the sky a thin bright line appears.',
       'Depth is established by perspective, overlap and contact before anything flattens.')
def p21(b):
    sky(b, y1=430, stars=40, seed=9)
    b.line([(860, 30), (1030, 22)], 2.5, (1.0, 0.95, 0.85), 1, smooth=False)
    b.glow((945, 26), 40, (0.9, 0.9, 1.0), 0.3, core=False)
    b.rect(0, 400, W, H, (0.22, 0.24, 0.36))
    b.shape([(0, 420), (300, 380), (620, 400), (900, 370), (1280, 395), (1280, 440), (0, 440)], (0.40, 0.44, 0.58), 1.4)
    city(b, 380, layers=3, seed=4)
    vp = (1400, 360)
    for y_ in (520, 640):
        b.line([(0, y_), vp], 0.8, (0.8, 0.3, 0.3), 0.35, smooth=False, passes=1)
    a2, b2 = ledge(b, (-40, 600), (1100, 520), vp, depth=0.25, h=120)
    girl(b, 'A', 420, 572, 50, view='back', legs='sit', hide_legs=True, arm=(-35, 0), arm2=(35, 0))
    girl(b, 'B', 610, 562, 48, view='back', legs='sit', hide_legs=True, arm=(-35, 0), arm2=(35, 0))
    for x_, y_ in ((420, 575), (610, 565)):
        b.wash([(x_ - 50, y_ + 2), (x_ + 60, y_ - 4), (x_ + 70, y_ + 10), (x_ - 40, y_ + 16)], (0.4, 0.4, 0.45), 0.5)
    lantern(b, (730, 535), 14, glowk=0.5)
    b.wash([(690, 548), (790, 540), (800, 560), (680, 568)], (1.0, 0.85, 0.55), 0.5)


@panel('2.2', 92.6, 96.0, S2, 'a sheet thinner than any mind could believe:',
       'Low angle past the girls: the sheet descends edge-on, a razor line of light slicing down the sky. A looks up; B grips her lantern.',
       'Threat with no visible hand or god.')
def p22(b):
    sky(b, stars=50, seed=10, top=(0.06, 0.07, 0.16), bot=(0.20, 0.22, 0.36))
    b.line([(820, -10), (760, 520)], 3, (1.0, 0.97, 0.9), 1, smooth=False)
    b.glow((790, 250), 120, (0.85, 0.9, 1.0), 0.25, core=False)
    b.arrow((900, 120), (860, 330), w=2)
    girl(b, 'A', 380, 820, 120, view='side', facing=1, legs='sit', head=40, arm=(30, -40))
    girl(b, 'B', 150, 860, 120, view='side', facing=1, legs='sit', head=25, arm=(45, -80), lantern='near', glowk=0.4)


@panel('2.3', 96.0, 98.0, S2, 'it touched the edge of everything, and everything fell flat,   (hits 95.4, 96.3)',
       'Wide over the city: the sheet touches the horizon and its front sweeps toward camera. Beyond the front, hills and buildings are flat drawings (frontal outlines, no shading, printed dots for lights); on the near side they are still shaded and in perspective.',
       'A readable transformation front crossing the environment, far to near.')
def p23(b):
    sky(b, y1=360, stars=30, seed=11)
    b.rect(0, 340, W, H, (0.24, 0.26, 0.38))
    city(b, 360, layers=3, seed=6, flat_from=None, scale=1.1)
    b.rect(0, 0, 0, 0, INK)
    # far side (above/behind the front) redrawn flat
    flat_zone = [(0, 0), (W, 0), (W, 455), (0, 455)]
    b.paint([(0, 300), (W, 300), (W, 455), (0, 455)], (0.95, 0.93, 0.88), 1.0)
    city(b, 330, layers=2, seed=12, flat_from=-10, scale=0.9)
    b.shape([(0, 330), (220, 270), (430, 320), (700, 260), (960, 310), (1280, 280), (1280, 300), (0, 300)], (0.95, 0.93, 0.88), 1.4)
    b.rect(0, 455, W, H, (0.20, 0.22, 0.33))
    city(b, 560, layers=2, seed=14, scale=1.7, lit=0.45)
    b.paint([(0, 448), (W, 448), (W, 462), (0, 462)], (1.0, 0.97, 0.85), 1.0)
    b.glow((640, 455), 400, (1.0, 0.95, 0.85), 0.25, core=False)
    b.line([(0, 455), (W, 455)], 3, (1.0, 1.0, 0.95), 1, smooth=False)
    for x_ in (200, 640, 1080):
        b.arrow((x_, 440), (x_, 520), w=3)


@panel('2.4', 98.0, 99.2, S2, '(98.0: the front reaches the parapet)',
       'The front reaches the foot of the parapet and stops at its rim. The girls push up off the ledge and stand (A with both hands, B with her lantern). Below, their shadows land on the flattened city and are printed on it as flat silhouettes: A with horns and tail, B with long hair and lantern.',
       'What changes for each girl: her body stays volumetric (staging choice); her shadow becomes part of the drawing.')
def p24(b):
    sky(b, y1=300, stars=25, seed=12)
    b.rect(0, 280, W, H, (0.95, 0.93, 0.88))
    city(b, 300, layers=2, seed=13, flat_from=-10, scale=0.9)
    girl(b, 'A', 340, 600, 48, view='back', legs='stand', shadow=(0.20, 0.20, 0.24))
    girl(b, 'B', 640, 596, 48, view='back', legs='stand', arm2=(25, -60), lantern='near', shadow=(0.20, 0.20, 0.24))
    ledge(b, (-20, 260), (1300, 250), (640, 120), depth=0.10, h=60)
    b.line([(0, 330), (W, 320)], 3, (1.0, 1.0, 0.9), 0.9, smooth=False)
    b.glow((640, 325), 300, (1.0, 0.95, 0.85), 0.2, core=False)
    girl(b, 'A', 330, 245, 32, view='back', legs='stand', arm=(-20, -30), arm2=(20, -30))
    girl(b, 'B', 640, 240, 32, view='back', legs='stand', arm=(-15, 0), arm2=(25, -60), lantern='near', glowk=0.4)
    b.arrow((330, 140), (330, 90), w=2)
    b.arrow((640, 140), (640, 90), w=2)


@panel('2.5', 99.2, 103.0, S2, 'three dimensions into two, and still I looked at that.',
       'High angle from behind: the girls stand on the surviving rim, shaded, with contact shadows at their feet. Below them the whole world is one flat drawing, with their two printed shadows on it. B looks down; A stands close beside her.',
       'Result: the world is W2, the girls stay V on the rim (a staging choice, not a logical necessity).')
def p25(b):
    b.rect(0, 0, W, H, (0.95, 0.93, 0.88))
    earth(b, 640, 1500, 1350, flat=True, seed=8)
    flat_world(b, 0, 300, W, 720, seed=9, lights=50)
    girl(b, 'A', 600, 610, 30, view='back', legs='stand', shadow=(0.20, 0.20, 0.24))
    girl(b, 'B', 740, 612, 30, view='back', legs='stand', lantern='near', shadow=(0.20, 0.20, 0.24))
    b.shape([(380, 300), (900, 280), (960, 330), (330, 355)], STONE, 2.0, smooth=False)
    b.shape([(330, 355), (960, 330), (960, 360), (330, 385)], tuple(np.array(STONE) * 0.75), 2.0, smooth=False)
    girl(b, 'A', 590, 230, 30, view='back', legs='stand', arm=(-15, 0), arm2=(15, 0))
    girl(b, 'B', 680, 226, 30, view='back', legs='stand', arm=(-10, 0), arm2=(20, -50), head=-25, lantern='near', glowk=0.3)
    b.wash([(560, 330), (630, 328), (640, 342), (555, 344)], (0.3, 0.3, 0.3), 0.6)
    b.wash([(650, 326), (720, 324), (730, 338), (645, 340)], (0.3, 0.3, 0.3), 0.6)


@panel('3.1', 142.8, 145.8, S3, 'But look who\'s pressing the keys.   ([B])',
       'Medium over the console: both girls turn to the keyboard. In the middle a key goes down by itself and glows. The empty chair is at the left edge.',
       'Beginning: an effect without a visible cause.')
def p31(b):
    room(b)
    console(b, 260, 470, 1020, 720, depth=110, pressed={(1, 7)})
    chair(b, 120, 560, 120)
    girl(b, 'B', 1080, 560, 70, view='side', facing=-1, lean=12, head=-20, arm=(40, -20))
    girl(b, 'A', 930, 520, 60, view='side', facing=-1, lean=8, head=-15, arm=(20, 0))


@panel('3.2', 145.8, 147.6, S3, 'No hunter in the forest,',
       'Key-level close-up: a tiny translucent traveller carrying a lantern walks across the keys. Each footfall presses a key down; the pressed keys keep a warm footprint.',
       'Cause and effect, readable without labels: someone walking presses the keys.')
def p32(b):
    b.grad((0.16, 0.14, 0.16), (0.30, 0.26, 0.26))
    for i in range(7):
        x0 = 60 + i * 175
        down = i in (3, 4)
        off = 18 if down else 0
        b.shape([(x0, 380 + off), (x0 + 160, 380 + off), (x0 + 175, 560 + off), (x0 + 10, 560 + off)], (0.93, 0.91, 0.85) if not down else (1, 0.86, 0.56), 2, smooth=False)
        b.shape([(x0 + 10, 560 + off), (x0 + 175, 560 + off), (x0 + 175, 600), (x0 + 10, 600)], (0.6, 0.58, 0.55), 1.5, smooth=False)
        if i in (1, 2, 3):
            b.ellipse((x0 + 90, 470 + off), (14, 8), 0, 0, fill=GOLD, fa=0.8)
            b.glow((x0 + 90, 470 + off), 30, GOLD, 0.3, core=False)
    traveler(b, 760, 395, 230, step=1.0, alpha=0.7, glowk=0.6)
    b.arrow((610, 330), (610, 390), w=3)
    b.arrow((820, 160), (1000, 160), w=3)


@panel('3.3', 147.6, 149.6, S3, 'no hand upon the card,',
       'A kneels to the console\'s level, eyes wide, as more travellers pass. B\'s hand hovers above the keys and does not press.',
       'Reaction: they are not at the controls; they watch who is.')
def p33(b):
    room(b, flatview=True)
    console(b, 100, 460, 1180, 720, depth=140, keys=16, pressed={(0, 4), (1, 9)}, glow_keys={(2, 12)})
    for i, x_ in enumerate((420, 560, 720)):
        traveler(b, x_, 540 - i * 6, 60, step=i, alpha=0.6, glowk=0.3)
    girl(b, 'A', 300, 520, 70, view='side', facing=1, legs='kneel', head=-10, arm=(60, -20))
    hand(b, (1000, 250), (880, 380), w=60, cuff=B_CARD, curl=-0.1)
    b.line([(880, 400), (880, 450)], 2, RED, 0.8, smooth=False)


@panel('3.4', 149.6, 153.3, S3, 'only travelers with lanterns, passing through the dark.',
       'Wide on the console: a procession of travellers crosses the keyboard and the keys ripple under them. A holds out her open palm at key level; one traveller steps across it, and its lantern touches A\'s paper lantern, which lights.',
       'A joins the travellers: her lantern (LA) is lit from a passer-by.')
def p34(b):
    room(b)
    console(b, 120, 470, 1160, 720, depth=130, keys=16, pressed={(0, 3), (0, 5), (1, 7), (1, 9), (2, 11)})
    for i in range(8):
        traveler(b, 220 + i * 95, 520 + (i % 2) * 20, 48, step=i * 0.9, alpha=0.6, glowk=0.25)
    girl(b, 'A', 1150, 600, 85, view='side', facing=-1, lean=25, head=-15, arm=(80, -10), arm2=(40, 30), lantern='far', glowk=0.9)
    b.arrow((300, 470), (900, 470), curve=(600, 430), w=2)


@panel('3.5', 153.3, 158.5, S3, 'Every key is a footstep of someone passing by:',
       'The procession flows off the console, across the floor and out through the window into the flattened world as a line of lights. A and B follow it for two steps, lanterns lit.',
       'The metaphor completes: keys are footsteps; the footsteps go out into the world.')
def p35(b):
    room(b, flatview=True)
    pts = [(120, 700), (300, 640), (500, 560), (620, 420), (660, 300), (720, 220), (800, 180)]
    for i, p in enumerate(pts):
        traveler(b, p[0], p[1], 50 - i * 6, step=i, alpha=0.55, glowk=0.25)
    console(b, 900, 520, 1280, 720, depth=90, keys=8, pressed={(0, 2), (1, 4)})
    girl(b, 'A', 330, 700, 80, view='back', legs='walk', stride=18, arm=(-20, -40), lantern='near', glowk=0.6)
    girl(b, 'B', 470, 690, 78, view='back', legs='walk', stride=-18, arm2=(20, -40), lantern='far', glowk=0.6)


@panel('3.6', 158.5, 163.5, S3, 'no one at the controls. (158.5) Not them. (161.5) And not I. (162.5)',
       'Wide: the empty chair in the foreground, still empty; the keys still move under the passing lights. The girls stand small by the window, backs to camera, lanterns lit.',
       'Result: the seat stays empty; what is present are the traces.')
def p36(b):
    room(b, flatview=True)
    console(b, 330, 470, 950, 560, depth=60, keys=12, pressed={(0, 3), (1, 6), (2, 9)})
    girl(b, 'A', 600, 450, 30, view='back', legs='stand', lantern='near', glowk=0.4)
    girl(b, 'B', 660, 448, 30, view='back', legs='stand', lantern='far', glowk=0.4)
    chair(b, 210, 520, 260, col=(0.12, 0.11, 0.13))


@panel('4.1', 163.5, 167.0, S4, 'UNRESOLVED lines F01-F04 may fall here ("Where we live is a simulated universe / and the thing that came down from the edge of the sky / was every traveler who ever passed through here, / every light that went out and never said goodbye.") Measured: near-silence 163.5-164.5, held voice 165.0-168.0.',
       'At the window, from behind the girls: the line of traveller lights spreads over the flat world, and the first traces return as its features. The letter\'s handwriting becomes a road; the cradle\'s arc becomes a river bend; the parting hands become a bridge.',
       'Accumulation begins from things already seen. The images carry the meaning of F01-F04 with or without the words.')
def p41(b):
    room(b, vp=(640, 300), win=(170, 60, 1110, 470), flatview=False)
    flat_world(b, 170, 60, 1110, 470, seed=21, lights=10)
    b.scribble(220, 360, 700, INK, 2.2, 0.8, amp=6, seed=4)
    b.line(catmull([(600, 120), (760, 260), (1000, 220), (1100, 300)]), 9, (0.55, 0.7, 0.9), 0.9)
    b.line(catmull([(820, 200), (860, 170), (900, 200)]), 4, (0.5, 0.42, 0.38), 0.9)
    for i in range(14):
        traveler(b, 230 + i * 34, 358 + 4 * np.sin(i), 16, step=i, alpha=0.7, glowk=0.18)
    window_frame(b, 170, 60, 1110, 470)
    girl(b, 'A', 540, 690, 70, view='back', legs='stand', arm=(-20, -60), lantern='near', glowk=0.6)
    girl(b, 'B', 760, 690, 70, view='back', legs='stand', arm2=(20, -60), lantern='far', glowk=0.6)


@panel('4.2', 167.0, 170.3, S4, '(held voice 165.0-168.0, choir to 171.2; F01-F04 unresolved)',
       'Wider, through the glass: the drawing grows into a civilisation of marks. Roads of handwriting, cradle-arc rivers, bridges of hands and lights everywhere, scaling up to the whole curve of the Earth-drawing. One lantern goes out, but its footprint stays lit. B\'s hand is on the glass.',
       'Scale is earned by accumulation and transformation of the specific traces.')
def p42(b):
    b.rect(0, 0, W, H, (0.95, 0.93, 0.88))
    earth(b, 640, 1300, 1050, flat=True, seed=31, lit=2.5)
    r = np.random.default_rng(5)
    for k in range(14):
        y = 330 + k * 26
        b.scribble(r.uniform(0, 300), y, r.uniform(800, 1280), INK, 1.4, 0.6, amp=4, seed=k + 10)
    for k in range(5):
        x = 100 + k * 260
        b.line(catmull([(x, 720), (x + 60, 560), (x + 140, 470), (x + 220, 400)]), 6, (0.55, 0.7, 0.9), 0.8)
    for k in range(60):
        b.glow((r.uniform(0, W), r.uniform(320, 720)), 8, GOLD, 0.35, core=False)
    b.ellipse((900, 520), (14, 14), 0, 2, INK, 0.8, fill=(0.4, 0.4, 0.45))
    b.ellipse((930, 545), (8, 5), 0, 0, fill=GOLD)
    b.glow((930, 545), 20, GOLD, 0.4, core=False)
    hand(b, (1260, 120), (1060, 230), w=110, cuff=B_CARD, curl=0.0)
    b.wash([(0, 0), (W, 0), (W, H), (0, H)], (0.85, 0.9, 1.0), 0.12)


@panel('4.3', 170.3, 175.0, S4, 'And one day we\'ll be paper,   ([B] in the continuation)',
       'The girls step through the window into the drawing, holding hands. As each crosses the frame line her body becomes a drawn contour (line and flat colour, no shading). They step into their own printed shadows from 2.4.',
       'The girls\' first and only change of state: they choose to join the art.')
def p43(b):
    b.rect(0, 0, W, H, (0.95, 0.93, 0.88))
    flat_world(b, 560, 0, W, H, seed=33, lights=40)
    b.paint([(0, 0), (560, 0), (560, H), (0, H)], (0.26, 0.24, 0.29), 1)
    window_frame(b, 560, -20, 1400, 740)
    girl(b, 'A', 860, 690, 40, view='back', legs='stand', shadow=(0.22, 0.22, 0.26))
    girl(b, 'B', 1010, 690, 40, view='back', legs='stand', shadow=(0.22, 0.22, 0.26))
    girl(b, 'B', 455, 470, 64, view='side', facing=1, legs='walk', stride=20, arm=(62, -5), lantern='far', glowk=0.5)
    j = girl(b, 'A', 735, 480, 64, view='side', facing=1, legs='walk', stride=-20, arm2=(-30, 0), flat=True)
    b.line([(560, 0), (560, H)], 3, (1.0, 1.0, 0.9), 0.9, smooth=False)
    b.line([(578, 365), (612, 360), (640, 352)], 9, SKIN, 1.0)
    b.ellipse((598, 362), (16, 12), 0, 2, INK, 0.9, fill=SKIN)


@panel('4.4', 175.0, 180.0, S4, 'and we\'ll still be in the art:   ("art" held to 178.5; 179.5-180.0 held low tone)',
       'Extreme wide: the vast drawing of civilisation; the two small contour girls holding hands among countless traces, their lanterns two lights among many. 179.5-180.0: the contours settle.',
       'They are now part of the human record they were born from.')
def p44(b):
    b.rect(0, 0, W, H, (0.95, 0.93, 0.88))
    r = np.random.default_rng(9)
    for k in range(26):
        y = 30 + k * 27
        b.scribble(r.uniform(-50, 200), y, r.uniform(900, 1330), INK, 1.1, 0.45, amp=3, seed=k + 40)
    for k in range(8):
        x = r.uniform(0, W)
        b.line(catmull([(x, 0), (x + 80, 200), (x - 40, 450), (x + 60, 720)]), 5, (0.6, 0.72, 0.9), 0.7)
    for k in range(140):
        b.glow((r.uniform(0, W), r.uniform(0, H)), 7, GOLD, 0.35, core=False)
    girl(b, 'A', 620, 420, 18, view='side', facing=1, legs='stand', flat=True, arm=(20, 0))
    girl(b, 'B', 650, 420, 18, view='side', facing=1, legs='stand', flat=True, arm2=(-20, 0), lantern='near', glowk=0.4)


@panel('4.5', 180.0, 188.5, S4, 'maybe death is only a return,   ([A], 180.0-185.0; melisma 185.5-188.5)',
       'A sings, close (contour, then gaining shade). Around her the drawing\'s lines lift off the paper and fold up into perspective, like a pop-up book: depth returns.',
       'The one return begins on A\'s offered "maybe".')
def p45(b):
    b.rect(0, 0, W, H, (0.95, 0.93, 0.88))
    for k in range(5):
        x = 80 + k * 260
        b.shape([(x, 640), (x + 120, 640), (x + 150, 560 - 30 * (k % 2)), (x + 30, 560 - 30 * (k % 2))], (0.85, 0.82, 0.75), 1.5, smooth=False)
        b.shape([(x + 120, 640), (x + 150, 560 - 30 * (k % 2)), (x + 150, 470), (x + 120, 540)], (0.70, 0.68, 0.64), 1.5, smooth=False)
        b.arrow((x + 60, 700), (x + 60, 600), w=2)
    face_cu(b, 'A', 640, 300, 300, mouth='open', look=(0.6, -0.4), lit_side=0.6)
    b.glow((900, 520), 60, GOLD, 0.5)


@panel('4.6', 188.5, 193.0, S4, 'death is only a return.   ([both])',
       'The same parapet as 2.1, now altered. Below, the city\'s lights follow the trace shapes (a handwriting road, a river arc, a bridge). The constellation from 1.7 is in the sky; the two printed shadows remain on the world below. The girls sit volumetric again, B holding the worn letter, the lanterns beside them.',
       'Return to a familiar place that carries the journey\'s marks.')
def p46(b):
    sky(b, y1=430, stars=30, seed=9)
    constellation(b, [(300, 90), (420, 60), (560, 95), (690, 50), (830, 85)], k=0.5)
    b.rect(0, 400, W, H, (0.22, 0.24, 0.36))
    b.shape([(0, 420), (300, 380), (620, 400), (900, 370), (1280, 395), (1280, 440), (0, 440)], (0.40, 0.44, 0.58), 1.4)
    city(b, 380, layers=3, seed=4, lit=0.15)
    b.scribble(30, 470, 900, GOLD, 2.5, 0.9, amp=5, seed=4)
    b.line(catmull([(700, 520), (850, 470), (1050, 500), (1280, 450)]), 5, (0.55, 0.7, 0.95), 0.8)
    b.paint([(900, 470), (950, 470), (945, 520), (905, 520)], (0.1, 0.1, 0.12), 0.6)
    b.paint([(980, 468), (1030, 468), (1025, 520), (985, 520)], (0.1, 0.1, 0.12), 0.6)
    vp = (1400, 360)
    ledge(b, (-40, 600), (1100, 520), vp, depth=0.25, h=120)
    girl(b, 'A', 420, 572, 50, view='back', legs='sit', hide_legs=True, arm=(-35, 0), arm2=(35, 0))
    girl(b, 'B', 610, 562, 48, view='back', legs='sit', hide_legs=True, arm=(-35, 70), arm2=(35, -70))
    b.paint([(562, 520), (578, 496), (590, 524)], (0.96, 0.92, 0.79), 1.0)
    lantern(b, (730, 535), 14, glowk=0.5)
    lantern(b, (300, 560), 14, glowk=0.5)


@panel('4.7a', 193.0, 196.3, S4, 'Two dimensions...   ([A distant whisper])',
       'Insert, B\'s hands: the worn letter lies open and flat on her palms.',
       'The note as a flat thing.')
def p47a(b):
    b.grad((0.10, 0.10, 0.18), (0.24, 0.22, 0.30))
    hand(b, (250, 560), (520, 470), w=95, cuff=B_CARD, curl=0.1)
    hand(b, (1030, 560), (760, 470), w=95, cuff=B_CARD, curl=-0.1)
    letter(b, (640, 420), 420, 250, ang=0, seed=12)


@panel('4.7b', 196.3, 198.0, S4, 'three...',
       'Same hands: she folds it back into a little paper lantern.',
       'The note as a held volume.')
def p47b(b):
    b.grad((0.10, 0.10, 0.18), (0.24, 0.22, 0.30))
    hand(b, (250, 600), (520, 500), w=95, cuff=B_CARD, curl=0.3)
    hand(b, (1030, 600), (760, 500), w=95, cuff=B_CARD, curl=-0.3)
    lantern(b, (640, 380), 80, lit=True, glowk=0.6)
    b.arrow((470, 300), (560, 250), w=2)


@panel('4.7c', 198.0, 200.0, S4, 'and one...   (hit 199.9)',
       'A\'s hand closes over B\'s around the lantern\'s single light; it brightens softly on the hit.',
       '"One" is shown as togetherness around one light. It is poetic, not a dimensional demonstration (a point is zero-dimensional).')
def p47c(b):
    b.grad((0.08, 0.08, 0.15), (0.20, 0.18, 0.26))
    hand(b, (1030, 620), (720, 480), w=100, cuff=B_CARD, curl=-0.4)
    b.glow((640, 430), 90, GOLD, 1.0)
    hand(b, (200, 330), (600, 420), w=100, cuff=A_COAT, curl=0.45)


@panel('4.8', 200.0, 213.41, S4, '(200.0-202.5 no vocal) ...still loading. (202.5-203.7) / hum 204.0-207.5, decay, fade to 213.41',
       'Wide from behind on the parapet: below, some city lights come back, not all of them. At 202.5 the words "still loading" are written once in the letter\'s handwriting; then a quiet hold to the fade.',
       'Ends incomplete, on purpose: still loading.')
def p48(b):
    sky(b, y1=430, stars=20, seed=13)
    constellation(b, [(300, 90), (420, 60), (560, 95), (690, 50), (830, 85)], k=0.35)
    b.rect(0, 400, W, H, (0.20, 0.22, 0.33))
    city(b, 380, layers=3, seed=4, lit=0.12)
    ledge(b, (-40, 640), (1320, 640), (640, 300), depth=0.05, h=90)
    girl(b, 'A', 590, 640, 46, view='back', legs='sit', hide_legs=True, arm=(-30, 0), arm2=(40, 60))
    girl(b, 'B', 690, 642, 46, view='back', legs='sit', hide_legs=True, arm=(-40, 50), arm2=(30, 0), lean=-10)
    b.text((470, 200), 'still loading', 64, (1.0, 0.86, 0.6), font='hand')


# ---------------------------------------------------------------- build
def tc(t):
    return '%d:%04.1f' % (int(t // 60), t - 60 * int(t // 60))


def build():
    imgs = []
    for p in PANELS:
        b = Board()
        p['fn'](b)
        b.frame_border()
        img = b.out()
        cv2.imwrite(os.path.join(PAN, 'panel_%s.jpg' % p['id'].replace('.', '_')), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        os.makedirs(os.path.join(R, 'work', 'panels'), exist_ok=True)
        cv2.imwrite(os.path.join(R, 'work', 'panels', 'panel_%s.png' % p['id'].replace('.', '_')), img)
        imgs.append(img)
    return imgs


def sheets(imgs):
    """storyboard pages: 2 columns x 3 rows, each panel with its caption"""
    cells = []
    for p, img in zip(PANELS, imgs):
        sm = cv2.resize(img, (800, 450), interpolation=cv2.INTER_AREA)
        note = [('%s   %s - %s  (%.1f s)   |   %s' % (p['id'], tc(p['t0']), tc(p['t1']), p['t1'] - p['t0'], p['seq']), 17, True, (30, 30, 40)),
                ('LYRIC: ' + p['lyric'], 15, False, (150, 70, 30) if 'UNRESOLVED' in p['lyric'] or 'unresolved' in p['lyric'] else (60, 60, 70)),
                ('ACTION: ' + p['action'], 15, False, (30, 30, 40)),
                ('CHANGES: ' + p['change'], 15, False, (20, 90, 110))]
        cells.append(caption_card(sm, note, h=250))
    pages = []
    hh = max(c.shape[0] for c in cells)
    blank = np.full((hh, 800, 3), 255, np.uint8)
    for i in range(0, len(cells), 6):
        cs = [np.vstack([c, np.full((hh - c.shape[0], 800, 3), 250, np.uint8)]) for c in cells[i:i + 6]]
        cs += [blank] * (6 - len(cs))
        rows = [np.hstack([cs[k], np.full((hh, 20, 3), 255, np.uint8), cs[k + 1]]) for k in range(0, 6, 2)]
        page = np.vstack([np.vstack([r_, np.full((20, r_.shape[1], 3), 255, np.uint8)]) for r_ in rows])
        hdr = np.full((70, page.shape[1], 3), 255, np.uint8)
        cv2.putText(hdr, 'SIMULATED UNIVERSE - REV3 STORYBOARD (rough layouts, not animation)  page %d' % (i // 6 + 1), (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (40, 40, 40), 2, cv2.LINE_AA)
        page = np.vstack([hdr, page])
        path = os.path.join(OUT, 'REV3_storyboard_page%02d.jpg' % (i // 6 + 1))
        cv2.imwrite(path, page, [cv2.IMWRITE_JPEG_QUALITY, 88])
        pages.append(path)
    return pages


def reel(imgs):
    """timed reel: each sequence plays its panels for their exact durations over the locked audio of that span."""
    segs = []
    order = [S1, SR, S2, S3, S4]
    for sq in order:
        ps = [(p, im) for p, im in zip(PANELS, imgs) if p['seq'] == sq]
        t0, t1 = ps[0][0]['t0'], ps[-1][0]['t1']
        f0, f1 = int(round(t0 * 24)), int(round(t1 * 24))
        tmp = os.path.join(R, 'work', 'reel_%s.mp4' % sq.split()[0])
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1280x720', '-r', '24', '-i', '-',
                               '-ss', '%.4f' % (f0 / 24), '-t', '%.4f' % ((f1 - f0) / 24), '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                               '-c:v', 'libx264', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', tmp],
                              stdin=subprocess.PIPE)
        for f in range(f0, f1):
            t = f / 24
            p, im = [(p, im) for p, im in ps if int(round(p['t0'] * 24)) <= f < int(round(p['t1'] * 24))][0]
            fr = im.copy()
            cv2.rectangle(fr, (0, 680), (1280, 720), (20, 20, 24), -1)
            cv2.putText(fr, 'REV3 STORYBOARD  %s  |  panel %s  |  %s  frame %d' % (sq, p['id'], tc(t), f), (14, 708),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1, cv2.LINE_AA)
            ff.stdin.write(fr.tobytes())
        ff.stdin.close()
        ff.wait()
        segs.append(tmp)
    lst = os.path.join(R, 'work', 'reel_list.txt')
    open(lst, 'w').write(''.join("file '%s'\n" % s for s in segs))
    out = os.path.join(OUT, 'REV3_storyboard_reel.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], check=True)
    return out


if __name__ == '__main__':
    imgs = build()
    pages = sheets(imgs)
    print('panels', len(imgs), 'pages', pages)
    if '--reel' in sys.argv:
        print(reel(imgs))
