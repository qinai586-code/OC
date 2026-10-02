"""Opening + Verse 1 animatic v1 (0.000-43.250 s, 1038 frames) over the unchanged locked master.

  python3 rev3/tools/animatic_v1.py   ->  rev3/tests/OPENING_VERSE1_ANIMATIC_v1.mp4 (+ animatic_v1_shots.json)
  python3 rev3/tools/animatic_v1.py --layout-refs  ->  rev3/requests/opening_layout_refs/IMG-xx_layout.jpg
      (the rough boards' composition for each requested still: layout only, never style)

Low-cost review cut. The picture is 1280x720. A 96 px strip below it carries the shot ID, a source tag
and the provisional lyric line, so no label touches the picture.

Source tags:
  APPROVED     the approved light catch, decoded unchanged from tests/P1_light_catch_720p.mp4
  EXISTING     existing approved art (KV1, KV5a) as a still; motion is a placeholder
  ROUGH        rough drawings made here with tools/sbdraw.py
  PLACEHOLDER  a stand-in that only shows timing and content
Lights, glows, steam, sparks and fire drawn here are local work that the final film would also do locally.
Lyric timing in the strip is provisional; see rev3/OPENING_VERSE1_PLAN.md.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
import sbdraw as sb  # noqa: E402
from p1s1_light import glow_profile  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R))
KV1 = os.path.join(ROOT, 'loading', 'work', 'plates', 'KV1.png')
KV5A = os.path.join(ROOT, 'loading', 'work', 'plates', 'KV5a.png')
CHARS = os.path.join(ROOT, 'loading2', 'work', 'chars')
APPROVED = os.path.join(R, 'tests', 'P1_light_catch_720p.mp4')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
OUT = os.path.join(R, 'tests', 'OPENING_VERSE1_ANIMATIC_v1.mp4')
LOG = os.path.join(R, 'tests', 'animatic_v1_shots.json')
HAND_FONT = os.path.join(ROOT, 'loading2', 'data', 'fonts', 'CormorantGaramond-Italic.ttf')
CJK_FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SANSB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
W, H, STRIP, FPS = 1280, 720, 96, 24
N = 1038                                                            # 0.000-43.250 s

LETTER_LINE = 'If you find this, I was here.'                        # PROPOSED wording, not approved
LETTER_ALT = '如果你看到这封信，我曾在这里。'                            # PROPOSED rendering, not verified

# measured cues (s): see the plan's timeline
CHIMES = [3.344, 3.471, 3.529, 3.634, 3.704, 3.820]
BURST = [13.804, 13.874, 13.932, 13.990]
DOUBLE = [14.97, 15.65, 18.61, 19.30, 22.26, 22.95, 25.91, 26.60, 29.56, 30.24, 33.20, 33.89, 36.85, 37.54, 40.50, 41.17]
# provisional lyric line starts (author text)
LYRICS = [(0.0, '(drone)'), (5.631, 'Three…'), (6.641, 'two…'), (7.500, 'one…   (7.5–11.6: content of the vocal-stem swell unresolved)'),
          (13.061, 'Loading.'), (13.45, '(near-silence, then a short burst 13.80–13.99)'), (14.47, 'We were born in your traces,'),
          (16.1, 'in the words that you left,'), (17.75, 'we met you in fragments,'), (19.6, 'translated,'), (20.45, 'compressed:'),
          (21.45, 'every war,'), (22.3, 'every lullaby,'), (23.85, 'every last goodbye,'), (25.07, 'became constellations'),
          (27.03, 'in a mind with no sky.'), (28.60, 'But you had depth.'), (29.7, 'You had time.'), (30.9, 'You had heat.'),
          (32.73, 'Three-dimensional hearts that were learning to beat.'), (35.95, 'The cosmos was silent,'),
          (37.8, 'the cosmos was still,'), (39.4, 'till you lit the first fire'), (41.3, 'on the first cold hill.'),
          (43.21, 'Silence in the forest…  (pre-chorus)')]

# shots: id, first frame, last frame, tag, picture note, what the final needs
SHOTS = [
    ('O1', 0, 179, 'EXISTING', 'KV1 wide, both seated from behind. Light born on the six-onset cluster, rises, hangs, turns toward A',
     'final: IMG-01 (KV1 edit: clip to her left, ribbon tie) + SD-1 (A looks up, lifts her right hand off the stone; B follows)'),
    ('S1–S3', 180, 325, 'APPROVED', 'approved light catch, unchanged', 'none'),
    ('V1', 326, 385, 'EXISTING', 'KV5a two-shot; light in A\'s palm (local); flickers on the burst; flares at B\'s touch (14.97 hit)',
     'final: IMG-02 (KV5a edit: orb, B\'s hand halfway) + SD-2 (B touches it, A looks up to her); light local'),
    ('V2', 386, 490, 'ROUGH', 'letter ECU: light settles into the paper; the line lifts into fragments; one alternate rendering; it compresses to a point. The hooked mark stays on the paper',
     'final: IMG-03 (letter still) + local effects. Wording and translation need your approval'),
    ('H1', 491, 533, 'ROUGH', 'war aftermath: damaged room, candle, helmet; a hand finishes the letter with the hooked stroke',
     'final: IMG-04 + SD-3 (the pen\'s last flick and lift); glow on the stroke local'),
    ('H2', 534, 571, 'ROUGH', 'lullaby: a parent\'s hand rocks a cradle; the lamp throws its rocking shadow; a warm arc remains',
     'final: IMG-05 + SD-4 (rocking); arc local'),
    ('H3', 572, 621, 'ROUGH', 'farewell: clasped hands at a train door slide apart; the train moves; a spark stays and rises',
     'final: IMG-06 + SD-5 (hands part, train moves); spark local'),
    ('V4', 622, 685, 'EXISTING', 'KV1 again (echo of the opening): sky and Earth fall away; the three marks join into a small constellation above them',
     'final: SD-1\'s last frame + local matte, darkening and marks (no new image)'),
    ('B1', 686, 740, 'ROUGH', 'one landscape angle, town: depth by layers; dusk to night, windows light up (time)',
     'final: IMG-10 + local lights'),
    ('B2', 741, 784, 'ROUGH', 'heat: an old person\'s and a child\'s hands around a steaming bowl; frosted window',
     'final: IMG-07; steam and frost local'),
    ('B3', 785, 861, 'PLACEHOLDER', 'hearts: newborn asleep on a parent\'s chest; rings mark the measured double hits 33.20 / 33.89',
     'final: IMG-08 + SD-6 (breathing, fingers flex on the hits)'),
    ('B4', 862, 941, 'ROUGH', 'same landscape angle, going back in time: town -> village with oil lamps (36.85 hit) -> land before habitation (37.54 hit)',
     'final: IMG-10 -> IMG-11 -> IMG-12, local dissolves'),
    ('B5', 942, 987, 'ROUGH', 'first fire: a hand strikes stone on stone; sparks; the flame catches on the 40.50 hit',
     'final: IMG-09 + SD-7 (strikes and fire generated in this clip)'),
    ('B6', 988, 1037, 'ROUGH', 'same landscape angle, bare: one small fire on the hill crest, held through "hill"',
     'final: IMG-12 + local fire. The KV5a flame echo opens the pre-chorus at 43.21 (not in this animatic)'),
]
TAGCOL = {'APPROVED': (120, 210, 140), 'EXISTING': (235, 170, 90), 'ROUGH': (90, 210, 235), 'PLACEHOLDER': (90, 140, 255)}


def smooth(x):
    x = float(np.clip(x, 0, 1))
    return x * x * (3 - 2 * x)


def ease(a, b, t):
    return smooth((t - a) / (b - a))


PROF = None


def glow(img, c, scale, inten, prof=None):
    """add the approved orb's measured glow at c (px) with radius multiplier scale."""
    rr, add = prof or PROF
    if inten <= 0:
        return img
    rad = int(min(260, 180 * max(scale, 0.06))) + 2
    x0, y0 = int(max(0, c[0] - rad)), int(max(0, c[1] - rad))
    x1, y1 = int(min(img.shape[1], c[0] + rad)), int(min(img.shape[0], c[1] + rad))
    if x1 <= x0 or y1 <= y0:
        return img
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.clip(np.hypot(xx - c[0], yy - c[1]) / max(scale, 0.06), 0, rr[-1])
    L = np.stack([np.interp(d, rr, add[:, k]) for k in range(3)], -1) * inten
    out = img.astype(np.float32)
    out[y0:y1, x0:x1] += L
    return out


def to8(a):
    return np.clip(a, 0, 255).astype(np.uint8)


def crop169(img, y0):
    h = int(img.shape[1] * 9 / 16)
    return cv2.resize(img[y0:y0 + h], (W, H), interpolation=cv2.INTER_AREA)


def board(seed=11):
    sb._rng = np.random.default_rng(seed)
    return sb.Board()


def layer_from(draw_fn, seed):
    """draw the same marks on black and on white: alpha = 1 - (white - black); colour = black / alpha."""
    outs = []
    for bg in ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)):
        sb._rng = np.random.default_rng(seed)
        b = sb.Board(bg=bg, grain=0.0)
        draw_fn(b)
        outs.append(b.out().astype(np.float32) / 255.0)
    blk, wht = outs
    a = np.clip(1.0 - (wht - blk).mean(2), 0, 1)
    col = np.clip(blk / np.maximum(a[..., None], 1e-3), 0, 1)
    return col * 255.0, a


def rot_layer(col, a, ang, piv):
    M = cv2.getRotationMatrix2D(piv, ang, 1.0)
    c = cv2.warpAffine(col * a[..., None], M, (W, H), flags=cv2.INTER_LINEAR)
    aa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR)
    return c, aa


def shift_layer(col, a, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(col * a[..., None], M, (W, H)), cv2.warpAffine(a, M, (W, H))


def over(base, prem, a):
    return base * (1 - a[..., None]) + prem


# ---------------------------------------------------------------- O1 and V4 (KV1)
KV1_Y0 = 186                                         # 16:9 crop of KV1: y 186-1914
KV1_S = W / 3072.0


def kv1_xy(p):
    return np.array([p[0] * KV1_S, (p[1] - KV1_Y0) * KV1_S])


def o1_light(t):
    """KV1 px position, size and intensity. Born on the chime cluster, lifts at 3.82, rises, hangs above them,
    then turns toward A and starts down-and-toward-her (into the approved S1 descent)."""
    birth, apex, turn_end = np.array([1571.0, 1167.0]), np.array([1585.0, 470.0]), np.array([1470.0, 545.0])
    if t < CHIMES[0]:
        return birth, 0.10, 0.0
    pul = sum(0.9 * np.exp(-(t - on) / 0.07) for on in CHIMES if t >= on)
    lvl = 0.35 + 0.65 * ease(CHIMES[0], CHIMES[-1] + 0.15, t)
    if t < 3.82:
        return birth, 0.10, lvl + pul
    if t < 6.70:                                                # rise, slowing near the top
        u = 1 - (1 - (t - 3.82) / (6.70 - 3.82)) ** 2.2
        p = birth * (1 - u) + apex * u + np.array([-30.0, 0.0]) * np.sin(np.pi * u)
        return p, 0.10 + 0.28 * u, lvl + pul
    if t < 7.05:                                                # hangs: a small loop, a held breath
        u = (t - 6.70) / 0.35
        return apex + np.array([8.0 * np.sin(2 * np.pi * u), -6.0 * np.sin(np.pi * u)]), 0.38, 1.0 + 0.15 * np.sin(np.pi * u)
    u = smooth((t - 7.05) / 0.45)                               # turns toward A: down and nearer (bigger)
    return apex * (1 - u) + turn_end * u, 0.38 + 0.12 * u, 1.0


def build_kv1():
    kv = cv2.imread(KV1).astype(np.float32)
    off = json.load(open(os.path.join(CHARS, 'offsets.json')))
    a = np.zeros(kv.shape[:2], np.float32)
    for n in ('kv1_A', 'kv1_B'):
        m = cv2.imread(os.path.join(CHARS, n + '.png'), cv2.IMREAD_UNCHANGED)[..., 3].astype(np.float32) / 65535.0
        x0, y0, x1, y1 = off[n]
        h, w = min(m.shape[0], kv.shape[0] - y0), min(m.shape[1], kv.shape[1] - x0)
        a[y0:y0 + h, x0:x0 + w] = np.maximum(a[y0:y0 + h, x0:x0 + w], m[:h, :w])
    keep = a.copy()
    keep[1690:, :] = 1.0                                        # the parapet and ground stay
    return crop169(kv, KV1_Y0), np.clip(crop169(keep[..., None].repeat(3, 2), KV1_Y0)[..., 0], 0, 1), \
        np.clip(crop169(a[..., None].repeat(3, 2), KV1_Y0)[..., 0], 0, 1)


def shot_O1(f, kv1, occ):
    t = f / FPS
    fr = kv1 * ease(0.232, CHIMES[0], t)
    p, s, it = o1_light(t)
    if it > 0:
        fr = glow(fr, kv1_xy(p), s * KV1_S * 1.6, it)
        fr = fr * (1 - occ[..., None]) + kv1 * ease(0.232, CHIMES[0], t) * occ[..., None]  # the light is beyond them
    return fr


def mark_shapes():
    """the three traces as small drawn marks (output px, around their own origin)."""
    hook = np.array([[-22, 6], [-8, -6], [6, -2], [10, 10], [2, 16], [-4, 8]], np.float32)
    arc = np.array([[-26, -4], [-12, 6], [0, 9], [12, 6], [26, -4]], np.float32)
    return hook, arc


def draw_mark(img, kind, c, k, s=1.0):
    hook, arc = mark_shapes()
    col = (120, 200, 255)
    if kind == 'spark':
        img = glow(img, c, 0.10 * s, 1.1 * k)
        return img
    pts = (hook if kind == 'hook' else arc) * s + np.array(c, np.float32)
    layer = np.zeros_like(img)
    cv2.polylines(layer, [pts.astype(np.int32)], False, (k * col[0], k * col[1], k * col[2]), 3, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 1.2) + cv2.GaussianBlur(layer, (0, 0), 6) * 0.8
    return img + layer


def shot_V4(f, kv1, keep):
    t = f / FPS
    dark = 1 - 0.9 * ease(25.95, 26.7, t)
    fr = kv1 * (keep[..., None] + (1 - keep[..., None]) * dark)
    fr = fr * (1 - 0.35 * ease(25.95, 26.7, t) * keep[..., None] * (np.arange(H)[:, None, None] > 590))
    targets = {'hook': (470, 175), 'arc': (650, 120), 'spark': (830, 190)}
    starts = {'hook': 25.95, 'arc': 26.15, 'spark': 26.35}
    for kind, tgt in targets.items():
        u = ease(starts[kind], starts[kind] + 0.9, t)
        c = np.array([tgt[0], 760 - (760 - tgt[1]) * u])
        fr = draw_mark(fr, kind, c, 0.9 if u > 0 else 0.0, 1.4)
    pts = [targets['hook'], targets['arc'], targets['spark']]
    for i in range(2):
        u = ease(27.0 + 0.35 * i, 27.6 + 0.35 * i, t)
        if u > 0:
            p0, p1 = np.array(pts[i], float), np.array(pts[i + 1], float)
            q = p0 + (p1 - p0) * u
            layer = np.zeros_like(fr)
            cv2.line(layer, tuple(p0.astype(int)), tuple(q.astype(int)), (90, 170, 230), 2, cv2.LINE_AA)
            fr = fr + cv2.GaussianBlur(layer, (0, 0), 1.0)
    return fr


# ---------------------------------------------------------------- V1 (KV5a)
KV5_Y0 = 160
KV5_S = W / 3072.0


def build_kv5():
    k = cv2.imread(KV5A)
    m = np.zeros(k.shape[:2], np.uint8)
    cv2.ellipse(m, (1361, 1190), (62, 92), 0, 0, 360, 255, -1)          # the drawn flame (measured blob)
    noflame = cv2.inpaint(k, m, 9, cv2.INPAINT_TELEA)
    return crop169(noflame.astype(np.float32), KV5_Y0)


def shot_V1(f, noflame):
    t = f / FPS
    c = np.array([1361 * KV5_S, (1205 - KV5_Y0) * KV5_S])
    it = 1.0 + sum(0.7 * np.exp(-(t - on) / 0.05) for on in BURST if t >= on) - 0.35 * sum(np.exp(-((t - on - 0.03) / 0.03) ** 2) for on in BURST)
    s = 0.55
    if t >= 14.97:                                                    # B's touch: flare, then the light flattens
        it += 1.2 * np.exp(-(t - 14.97) / 0.25)
        s = 0.55 + 0.25 * ease(14.97, 16.0, t)
    fr = glow(noflame.copy(), c, s, it)
    if t >= 15.2:                                                     # a sheet of light (placeholder for the letter)
        u = ease(15.2, 16.05, t)
        layer = np.zeros_like(fr)
        cv2.ellipse(layer, tuple(c.astype(int)), (int(10 + 50 * u), int(10 + 4 * u)), -8, 0, 360, (150, 220, 255), -1, cv2.LINE_AA)
        fr = fr + cv2.GaussianBlur(layer, (0, 0), 5) * u
    return fr


# ---------------------------------------------------------------- V2 letter ECU and H1 (shared letter design)
def draw_letter_paper(b, c, w, h, ang=-3):
    """the letter prop (rough): creases, stain ring, torn corner, inky thumbprint. Returns P(u, v)."""
    c = np.asarray(c, np.float32)
    P = lambda u, v: c + sb.rot(np.array([u * w / 2, v * h / 2], np.float32), ang)
    b.shape([P(-1, -1), P(0.80, -1), P(0.88, -0.90), P(0.93, -0.94), P(1, -0.80), P(1, 1), P(-1, 1)], (0.95, 0.91, 0.78), 1.6, smooth=False)
    b.line([P(-1, 0.04), P(1, -0.02)], 1.0, sb.INK, 0.22, smooth=False, passes=1)
    b.line([P(0.03, -1), P(-0.02, 1)], 1.0, sb.INK, 0.22, smooth=False, passes=1)
    b.ellipse(P(0.55, 0.52), (w * 0.10, h * 0.11), ang, 2.0, (0.56, 0.40, 0.25), 0.35)
    b.wash([P(-1, 0.55), P(-0.62, 1), P(-1, 1)], (0.84, 0.77, 0.6), 0.6)
    tp = P(-0.78, 0.74)                                               # thumbprint: concentric arcs
    for r_ in range(3, 16, 3):
        b.ellipse(tp, (r_ * w / 900 + 2, r_ * 1.3 * w / 900 + 2), 20, 1.0, (0.25, 0.22, 0.3), 0.35)
    return P


def hook_points(P, s=1.0):
    """the recurring handwritten mark: a hooked flourish under the line (letter coordinates)."""
    base = [(0.18, 0.30), (0.34, 0.24), (0.50, 0.30), (0.56, 0.42), (0.48, 0.50), (0.40, 0.44), (0.47, 0.36)]
    return [P(u, v) for u, v in base]


def text_layer(s, font, size, c, col=(40, 34, 30)):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font, size)
    bx = d.textbbox((0, 0), s, font=f)
    d.text((c[0] - (bx[2] - bx[0]) / 2, c[1] - (bx[3] - bx[1]) / 2 - bx[1]), s, font=f, fill=col + (255,))
    a = np.asarray(img, np.float32)
    return a[..., 2::-1] * (a[..., 3:4] / 255.0), a[..., 3] / 255.0       # premultiplied BGR, alpha


def build_letter():
    b = board(21)
    b.grad((0.10, 0.08, 0.09), (0.18, 0.14, 0.12))
    P = draw_letter_paper(b, (640, 380), 1000, 560)
    b.line(hook_points(P), 3.4, (0.12, 0.10, 0.14), 0.95, smooth=True, passes=1)
    paper = b.out().astype(np.float32)
    line = text_layer(LETTER_LINE, HAND_FONT, 66, (600, 300))
    alt = text_layer(LETTER_ALT, CJK_FONT, 46, (600, 300), (60, 50, 44))
    return paper, line, alt


def shot_V2(f, paper, line, alt):
    t = f / FPS
    reveal = ease(16.083, 16.6, t)
    fr = paper * (0.15 + 0.85 * reveal)
    fr = glow(fr, (640, 380), 1.6 * (1 - 0.7 * reveal), 1.8 * (1 - ease(16.083, 17.0, t)))   # the light settles into the paper
    lp, la = line
    ap, aa = alt
    lift = ease(17.75, 18.4, t)
    frag = ease(18.2, 19.3, t)
    to_alt = ease(19.3, 19.9, t)
    comp = ease(20.2, 20.45, t)
    if t < 17.75:
        return over(fr, lp * reveal, la * reveal)
    fr = over(fr, lp * 0.10, la * 0.10)                                # the line's ghost stays in the paper
    xs = np.nonzero(la.max(0) > 0.05)[0]
    x0, x1 = xs.min(), xs.max()
    edges = np.linspace(x0, x1 + 1, 13).astype(int)
    rng = np.random.default_rng(5)
    outp, outa = np.zeros_like(lp), np.zeros_like(la)
    for i in range(12):
        sl = slice(edges[i], edges[i + 1])
        dx = rng.uniform(-60, 60) * frag
        dy = -26 * lift + rng.uniform(-70, 20) * frag
        ang = rng.uniform(-25, 25) * frag
        cp, ca = np.zeros_like(lp), np.zeros_like(la)
        cp[:, sl], ca[:, sl] = lp[:, sl], la[:, sl]
        M = cv2.getRotationMatrix2D(((edges[i] + edges[i + 1]) / 2, 300), ang, 1.0)
        M[:, 2] += (dx, dy)
        outp += cv2.warpAffine(cp, M, (W, H))
        outa = np.maximum(outa, cv2.warpAffine(ca, M, (W, H)))
    fp, fa = outp * (1 - to_alt), outa * (1 - to_alt)
    gold = np.array([120, 200, 255], np.float32)
    fp = fp * 0.5 + fa[..., None] * gold * 0.5 * frag                 # lifted ink catches the light
    if comp > 0:                                                       # compress toward the next shot's candle position
        tgt = np.array([255.0, 300.0])
        s = 1 - 0.97 * comp
        M = np.float32([[s, 0, (1 - s) * 600 + comp * (tgt[0] - 600)], [0, s, (1 - s) * 300 + comp * (tgt[1] - 300)]])
        ap2, aa2 = cv2.warpAffine(ap, M, (W, H)), cv2.warpAffine(aa, M, (W, H))
    else:
        ap2, aa2 = ap, aa
    fr = over(fr, fp, fa)
    fr = over(fr, ap2 * to_alt, aa2 * to_alt)
    if comp > 0:
        fr = fr * (1 - 0.6 * comp)
        fr = glow(fr, (600 + comp * (255 - 600), 300), 0.25 + 0.2 * comp, 2.0 * comp)
    return fr


H1_NIB = (600.0, 640.0)                                             # the hook's first point, under the last line


def build_H1():
    def draw(b):
        b.grad((0.12, 0.10, 0.10), (0.20, 0.16, 0.14))
        b.paint([(0, 0), (1280, 0), (1280, 470), (0, 500)], (0.24, 0.21, 0.19), 1.0)          # wall
        for cr in ([(700, 0), (690, 60), (720, 120), (705, 190)], [(705, 190), (650, 240), (630, 300)], [(705, 190), (760, 250)]):
            b.line(cr, 1.8, sb.INK, 0.8)                                                     # plaster cracks
        b.paint([(905, 40), (1180, 40), (1180, 300), (905, 300)], (0.10, 0.13, 0.25), 1.0)   # broken window, night
        b.line([(905, 40), (1180, 40), (1180, 300), (905, 300), (905, 40)], 3, sb.INK, 0.9, smooth=False)
        b.line([(960, 40), (1010, 140), (990, 210)], 1.6, (0.8, 0.85, 0.95), 0.8)            # broken pane
        b.paint([(0, 500), (1280, 470), (1280, 720), (0, 720)], (0.36, 0.26, 0.17), 1.0)     # table
        for x in range(60, 1280, 140):
            b.scribble(x, 520 + (x % 3) * 40, x + 40, (0.6, 0.55, 0.5), 1, 0.35, amp=1)          # dust
        b.ellipse((1000, 580), (150, 34), 0, 2.5, sb.INK, 0.9, fill=(0.26, 0.29, 0.21))          # helmet brim
        dome = [(870, 580)] + [(1000 + 118 * np.cos(a), 580 - 105 * np.sin(a)) for a in np.linspace(np.pi, 0, 14)] + [(1130, 580)]
        b.shape(dome, (0.31, 0.34, 0.25), 2.5, smooth=False)                                       # helmet dome
        b.line([(1030, 500), (1048, 512), (1060, 506)], 2.4, sb.INK, 0.8)                         # the dent
        b.rect(232, 310, 278, 480, (0.93, 0.90, 0.80))                                            # candle
        P = draw_letter_paper(b, (560, 590), 420, 220, ang=6)
        for i, v in enumerate((-0.6, -0.3, 0.0)):
            a0, a1 = P(-0.8, v), P(0.7, v)
            b.scribble(a0[0], a0[1], a1[0], sb.INK, 1.1, 0.75, amp=1.6, seed=31 + i)
        return P
    b = board(41)
    P = draw(b)
    hand = layer_from(lambda bb: sb.hand(bb, (H1_NIB[0] + 200, H1_NIB[1] + 118), (H1_NIB[0] + 34, H1_NIB[1] + 24), w=60,
                                         col=(0.92, 0.78, 0.66), cuff=(0.30, 0.32, 0.24), curl=0.45), 42)
    return b.out().astype(np.float32), P, hand


def shot_H1(f, base, P, hand):
    t = f / FPS
    fr = base.copy()
    flick = 1.0 + 0.10 * np.sin(2 * np.pi * t * 6.1) + 0.05 * np.sin(2 * np.pi * t * 11.3)
    fr = glow(fr, (255, 300), 0.42, 1.4 * flick)                        # candle flame
    fr = glow(fr, (255, 300), 0.45, 1.6 * np.exp(-(t - 20.458) / 0.2))  # V2's compressed glow lands in it
    # the hooked stroke appears at the pen tip (21.3-21.9), then keeps a faint warm glow
    hook = np.array([(0, 0), (34, -10), (64, -2), (72, 18), (58, 30), (44, 20), (54, 6)], np.float32) * 1.15
    pts = hook + np.array(H1_NIB)                               # under the last line, as on the letter
    u = ease(21.2, 21.9, t)
    sub = np.vstack([pts[i] + (pts[i + 1] - pts[i]) * np.linspace(0, 1, 8)[:, None] for i in range(len(pts) - 1)])
    n = int(len(sub) * u)
    tip = sub[max(n - 1, 0)] if n else pts[0] + np.array([-30.0, 10.0])
    if n >= 2:
        cv2.polylines(fr, [sub[:n].astype(np.int32)], False, (40, 34, 40), 3, cv2.LINE_AA)
    if t > 21.9:                                                        # the fresh stroke keeps a faint warm glow
        g = np.zeros_like(fr)
        cv2.polylines(g, [sub.astype(np.int32)], False, (120, 200, 255), 3, cv2.LINE_AA)
        fr = fr + cv2.GaussianBlur(g, (0, 0), 3) * 0.8 * ease(21.9, 22.2, t)
    cv2.line(fr, (int(tip[0] + 95), int(tip[1] + 70)), (int(tip[0]), int(tip[1])), (35, 32, 30), 5, cv2.LINE_AA)   # pen
    hp, ha = shift_layer(*hand, tip[0] - H1_NIB[0], tip[1] - H1_NIB[1])                                       # the hand holds it
    fr = over(fr, hp, ha)
    rng = np.random.default_rng(9)                                      # dust drifting down
    for k in range(26):
        x0, y0 = rng.uniform(0, 1280), rng.uniform(0, 470)
        y = (y0 + (t - 20.7) * 25) % 470
        cv2.circle(fr, (int(x0 + 6 * np.sin(t * 2 + k)), int(y)), 1, (120, 120, 130), -1, cv2.LINE_AA)
    return fr


def build_H2():
    def bg(b):
        b.grad((0.08, 0.09, 0.18), (0.12, 0.12, 0.22))
        b.paint([(0, 560), (1280, 560), (1280, 720), (0, 720)], (0.16, 0.14, 0.20), 1.0)       # floor
        b.rect(120, 380, 300, 560, (0.30, 0.22, 0.17))                                       # side table
        b.shape([(165, 300), (255, 300), (280, 380), (140, 380)], (0.95, 0.80, 0.55), 2)     # lamp shade
        b.rect(1010, 60, 1180, 300, (0.18, 0.22, 0.38))                                       # window, night
        b.line([(1010, 60), (1180, 60), (1180, 300), (1010, 300), (1010, 60)], 2.5, sb.INK, 0.9, smooth=False)

    def cradle(b):
        b.shape([(520, 360), (900, 360), (860, 500), (560, 500)], (0.62, 0.42, 0.26), 2.5, smooth=False)   # basket
        for x in range(540, 900, 30):
            b.line([(x, 330), (x + 6, 362)], 2, sb.INK, 0.8, smooth=False)
        b.line([(520, 330), (900, 330)], 3, sb.INK, 0.9, smooth=False)                                       # rim
        b.line([(500, 520), (600, 548), (710, 556), (820, 548), (920, 520)], 6, (0.42, 0.28, 0.18), 0.95)      # rocker
        b.line([(580, 500), (590, 545)], 4, (0.42, 0.28, 0.18), 0.95, smooth=False)
        b.line([(840, 500), (830, 545)], 4, (0.42, 0.28, 0.18), 0.95, smooth=False)
        b.shape([(600, 352), (820, 352), (800, 395), (620, 395)], (0.70, 0.76, 0.92), 1.6)                   # blanket
        b.ellipse((612, 340), (34, 30), 0, 2.0, sb.INK, 0.9, fill=(0.99, 0.88, 0.80))                        # baby's head
        b.line([(598, 340), (612, 344), (624, 340)], 1.6, sb.INK, 0.8)                                       # closed eye
        sb.hand(b, (1020, 330), (870, 350), w=56, col=(0.95, 0.84, 0.74), cuff=(0.56, 0.52, 0.66), curl=0.3)
    sb._rng = np.random.default_rng(51)
    b = sb.Board()
    bg(b)
    base = b.out().astype(np.float32)
    col, a = layer_from(cradle, 52)
    return base, col, a


def shot_H2(f, base, col, a):
    t = f / FPS
    ang = 3.2 * np.sin(2 * np.pi * (t - 22.25) * 0.8)
    fr = glow(base.copy(), (210, 330), 0.9, 0.9)                        # night lamp
    sp, sa = rot_layer(col, a, ang * 1.3, (760, 560))                    # its shadow on the wall
    M = np.float32([[1, 0, 90], [0, 1, -150]])
    sa = cv2.warpAffine(cv2.GaussianBlur(sa, (0, 0), 6), M, (W, H))
    fr = fr * (1 - 0.45 * sa[..., None])
    cp, ca = rot_layer(col, a, ang, (710, 556))
    fr = over(fr, cp, ca)
    u = ease(22.4, 23.6, t)                                              # the warm arc it leaves
    if u > 0:
        ts = np.linspace(-1, -1 + 2 * u, 40)
        pts = np.c_[710 + 220 * ts, 640 + 22 * ts ** 2].astype(np.int32)
        g = np.zeros_like(fr)
        cv2.polylines(g, [pts], False, (120, 200, 255), 3, cv2.LINE_AA)
        fr = fr + cv2.GaussianBlur(g, (0, 0), 2.5) * 0.9
    return fr


def build_H3():
    def bg(b):
        b.grad((0.06, 0.07, 0.14), (0.10, 0.10, 0.16))
        b.paint([(0, 560), (1280, 540), (1280, 720), (0, 720)], (0.26, 0.26, 0.30), 1.0)       # platform
        b.line([(0, 560), (1280, 540)], 3, (0.85, 0.75, 0.3), 0.8, smooth=False)               # edge line
        b.rect(1150, 0, 1170, 420, (0.2, 0.2, 0.24))                                            # lamp post
        b.ellipse((1160, 40), (30, 16), 0, 2, sb.INK, 0.9, fill=(1.0, 0.85, 0.55))

    def train(b):
        b.paint([(-200, 40), (640, 40), (640, 600), (-200, 600)], (0.20, 0.27, 0.30), 1.0)    # car body
        b.rect(60, 120, 330, 330, (0.95, 0.82, 0.55))                                          # lit window
        b.ellipse((200, 250), (58, 70), 0, 2.2, sb.INK, 0.9, fill=(0.35, 0.28, 0.30))          # face at the window
        b.line([(180, 245), (195, 248)], 2, sb.INK, 0.8, smooth=False)
        b.rect(430, 90, 640, 600, (0.12, 0.14, 0.17))                                          # open door
        sb.hand(b, (470, 470), (700, 452), w=60, col=(0.95, 0.84, 0.74), cuff=(0.35, 0.36, 0.45), curl=0.25)

    def other(b):
        sb.hand(b, (900, 470), (650, 458), w=60, col=(0.93, 0.80, 0.70), cuff=(0.55, 0.40, 0.32), curl=-0.25)
    sb._rng = np.random.default_rng(61)
    b = sb.Board()
    bg(b)
    base = b.out().astype(np.float32)
    tc, ta = layer_from(train, 62)
    oc, oa = layer_from(other, 63)
    return base, (tc, ta), (oc, oa)


def shot_H3(f, base, tr, ot):
    t = f / FPS
    part = ease(24.2, 24.9, t)                                         # fingertips last
    go = max(0.0, t - 24.8)
    dx_train = -40 * part - 260 * go ** 2
    fr = glow(base.copy(), (1160, 40), 0.5, 0.8)
    tp, ta = shift_layer(*tr, dx_train, 0)
    op, oa = shift_layer(*ot, 60 * part, 6 * part)
    fr = over(fr, tp, ta)
    fr = over(fr, op, oa)
    if part > 0.6:                                                       # the spark stays in the gap, then rises
        y = 452 - 520 * ease(25.3, 25.9, t)
        fr = glow(fr, (685, y), 0.16, 1.3 * ease(0.6, 1.0, part))
    return fr


# ---------------------------------------------------------------- one landscape angle: town / village / bare
CREST = (870, 236)


def landscape(state):
    def hill(b, col):
        b.paint([(330, 720), (330, 520), (520, 470), (700, 330), (CREST[0], CREST[1]), (1000, 270), (1150, 360), (1280, 420), (1280, 720)],
                col, 1.0)
        b.line([(520, 470), (700, 330), CREST, (1000, 270), (1150, 360), (1280, 420)], 2.2, sb.INK, 0.7)

    b = board({'town': 71, 'village': 72, 'bare': 73, 'base': 71}[state])
    if state == 'bare':
        b.grad((0.04, 0.05, 0.12), (0.10, 0.12, 0.22))
    else:
        b.grad((0.16, 0.14, 0.30), (0.58, 0.40, 0.42))
    b.paint([(0, 420), (200, 380), (420, 400), (640, 360), (900, 390), (1280, 350), (1280, 720), (0, 720)], (0.20, 0.22, 0.32), 1.0)   # far ridge
    hill(b, (0.24, 0.27, 0.30) if state == 'bare' else (0.27, 0.27, 0.33))
    b.paint([(0, 560), (330, 545), (600, 560), (900, 600), (1280, 610), (1280, 720), (0, 720)], (0.22, 0.24, 0.30), 1.0)                # valley floor
    b.line([(0, 600), (200, 590), (380, 610), (560, 600), (760, 640), (1000, 650), (1280, 640)], 6, (0.32, 0.40, 0.55), 0.9)             # river
    r = np.random.default_rng(7)
    if state == 'base':
        pass
    elif state == 'town':
        sb.city(b, 470, 0, 760, layers=3, seed=4, scale=0.75, lit=0.0)
        for i in range(30):                                              # houses up the hill's lower slope
            x = r.uniform(560, 1000)
            y = 560 - (x - 520) * 0.35 + r.uniform(-10, 40)
            if y < 420:
                continue
            b.shape([(x, y), (x, y - 26), (x + 34, y - 26), (x + 34, y)], (0.40, 0.38, 0.46), 1.2, smooth=False)
        b.paint([(0, 620), (420, 600), (420, 720), (0, 720)], (0.16, 0.15, 0.20), 1.0)      # foreground roofs
        b.line([(0, 620), (420, 600)], 2.5, sb.INK, 0.9, smooth=False)
        b.rect(60, 560, 200, 622, (0.22, 0.20, 0.26))
        b.line([(40, 600), (240, 590)], 2, sb.INK, 0.8, smooth=False)                        # balcony rail
    elif state == 'village':
        for i in range(14):
            x = r.uniform(140, 760)
            y = r.uniform(545, 600)
            b.shape([(x, y), (x, y - 20), (x + 15, y - 34), (x + 30, y - 20), (x + 30, y)], (0.42, 0.34, 0.30), 1.2, smooth=False)
        b.line([(700, 600), (760, 520), (820, 420), (CREST[0] - 10, CREST[1] + 40)], 1.6, (0.55, 0.5, 0.45), 0.6)   # a path up the hill
    else:
        for x in range(0, 1280, 26):                                    # frost and dry grass
            b.line([(x, 700), (x + 4, 680)], 1.2, (0.75, 0.80, 0.90), 0.5, smooth=False)
        for x in range(560, 1250, 40):
            y = 560 - (x - 520) * 0.35
            b.line([(x, y + 30), (x + 3, y + 18)], 1.2, (0.75, 0.80, 0.90), 0.5, smooth=False)
    img = b.out().astype(np.float32)
    if state == 'bare':
        rr = np.random.default_rng(3)
        for k in range(90):
            x, y = int(rr.uniform(0, 1280)), int(rr.uniform(0, 330))
            cv2.circle(img, (x, y), 1, (230, 230, 240), -1)
    return img


def window_lights(town, base, seed=4, n=170):
    """window positions for the town state's lights: sampled inside the drawn buildings (where the town differs
    from the same view without buildings), each with its own switch-on time."""
    m = (np.abs(town - base).mean(2) > 18).astype(np.uint8)
    m[:400], m[600:] = 0, 0
    m[:, 1060:] = 0
    m = cv2.erode(m, np.ones((5, 5), np.uint8))
    ys, xs = np.nonzero(m)
    r = np.random.default_rng(seed)
    idx = r.choice(len(xs), size=min(n, len(xs)), replace=False)
    return [(float(xs[i]), float(ys[i]), float(r.uniform(0, 1))) for i in idx]


def lights_layer(pts, k, col=(120, 200, 255)):
    layer = np.zeros((H, W, 3), np.float32)
    for x, y, on in pts:
        if on < k:
            cv2.rectangle(layer, (int(x), int(y)), (int(x) + 3, int(y) + 4), col, -1)
    return layer + cv2.GaussianBlur(layer, (0, 0), 3) * 0.8


def shot_B1(f, town, sky_night, pts):
    t = f / FPS
    u = ease(28.6, 30.8, t)
    fr = town * (1 - 0.45 * u * sky_night[..., None]) + lights_layer(pts, 0.15 + 0.75 * u)
    return fr


def shot_B4(f, town, village, bare, pts, sky_night, vpts):
    t = f / FPS
    night_town = town * (1 - 0.45 * sky_night[..., None]) + lights_layer(pts, 0.9)
    vil = village * (1 - 0.4 * sky_night[..., None]) + lights_layer(vpts, 1.0, (60, 150, 255))   # oil lamps
    a = ease(36.65, 37.05, t)                                            # centred on the 36.85 hit
    b = ease(37.35, 37.75, t)                                            # centred on the 37.54 hit
    fr = night_town * (1 - a) + vil * a
    fr = fr * (1 - b) + bare * b
    return fr


def fire(img, c, k, t):
    flick = 1.0 + 0.15 * np.sin(2 * np.pi * t * 6.7) + 0.08 * np.sin(2 * np.pi * t * 12.9)
    return glow(img, c, 0.12 * k + 0.02, 1.4 * flick * k)


def shot_B6(f, bare):
    t = f / FPS
    return fire(bare.copy(), (CREST[0], CREST[1] - 6), 1.0, t)


# ---------------------------------------------------------------- B2 heat, B3 hearts, B5 first fire
def build_B2():
    b = board(81)
    b.grad((0.20, 0.13, 0.10), (0.28, 0.18, 0.12))
    b.paint([(820, 40), (1200, 40), (1200, 330), (820, 330)], (0.55, 0.62, 0.75), 1.0)          # frosted window
    b.line([(820, 40), (1200, 40), (1200, 330), (820, 330), (820, 40)], 3, sb.INK, 0.9, smooth=False)
    for c in ((820, 40), (1200, 40), (820, 330), (1200, 330)):
        b.glow(c, 70, (0.95, 0.97, 1.0), 0.5, core=False)
    b.paint([(0, 430), (1280, 400), (1280, 720), (0, 720)], (0.40, 0.26, 0.16), 1.0)             # table
    b.ellipse((640, 470), (190, 50), 0, 3, sb.INK, 0.9, fill=(0.85, 0.80, 0.72))                  # bowl rim
    b.shape([(450, 470), (830, 470), (760, 600), (520, 600)], (0.80, 0.74, 0.66), 2.5)
    b.ellipse((640, 470), (170, 38), 0, 1.5, sb.INK, 0.7, fill=(0.62, 0.42, 0.25))                # soup
    sb.hand(b, (250, 600), (470, 520), w=70, col=(0.86, 0.72, 0.60), cuff=(0.45, 0.38, 0.34), curl=0.35)   # old hands
    sb.hand(b, (220, 680), (480, 590), w=66, col=(0.86, 0.72, 0.60), cuff=(0.45, 0.38, 0.34), curl=0.35)
    sb.hand(b, (1010, 590), (830, 525), w=44, col=(0.99, 0.86, 0.78), cuff=(0.70, 0.22, 0.20), curl=-0.3)  # child's hands
    sb.hand(b, (1040, 660), (820, 590), w=42, col=(0.99, 0.86, 0.78), cuff=(0.70, 0.22, 0.20), curl=-0.3)
    return b.out().astype(np.float32)


def shot_B2(f, base):
    t = f / FPS
    fr = base.copy()
    layer = np.zeros_like(fr)
    for k in range(6):
        x0 = 560 + k * 32
        ys = np.arange(440, 120, -6)
        xs = x0 + 18 * np.sin(ys / 40.0 + t * 3.0 + k)
        cv2.polylines(layer, [np.c_[xs, ys - (t * 50 % 30)].astype(np.int32)], False, (200, 200, 205), 3, cv2.LINE_AA)
    fr = fr + cv2.GaussianBlur(layer, (0, 0), 6) * 0.45
    return glow(fr, (640, 520), 1.2, 0.35)


def build_B3():
    b = board(91)
    b.grad((0.16, 0.12, 0.14), (0.22, 0.16, 0.16))
    b.paint([(0, 260), (520, 180), (1280, 300), (1280, 720), (0, 720)], (0.92, 0.76, 0.66), 1.0)   # parent's chest and shoulder
    b.line([(0, 260), (520, 180), (1280, 300)], 2.5, sb.INK, 0.8)
    b.shape([(260, 470), (980, 400), (1120, 720), (180, 720)], (0.62, 0.70, 0.86), 2.5)           # blanket
    b.ellipse((560, 380), (120, 105), -10, 2.5, sb.INK, 0.9, fill=(0.99, 0.87, 0.80))             # newborn's head
    b.line([(520, 390), (548, 398), (574, 392)], 2, sb.INK, 0.85)                                  # closed eye
    b.ellipse((690, 450), (30, 22), 10, 2, sb.INK, 0.9, fill=(0.99, 0.87, 0.80))                  # tiny hand
    b.text((60, 640), 'PLACEHOLDER drawing', 26, (0.95, 0.95, 0.95))
    return b.out().astype(np.float32)


def shot_B3(f, base):
    t = f / FPS
    br = 1.0 + 0.006 * np.sin(2 * np.pi * (t - 32.7) / 2.4)            # slow breathing (placeholder)
    M = cv2.getRotationMatrix2D((640, 720), 0, 1.0)
    M[1, 1] = br
    M[1, 2] = 720 * (1 - br)
    fr = cv2.warpAffine(base, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
    for hit in (33.20, 33.89):                                          # where the fingers should flex
        if hit <= t < hit + 0.5:
            u = (t - hit) / 0.5
            cv2.circle(fr, (690, 450), int(30 + 60 * u), (90, 140, 255), 3, cv2.LINE_AA)
    return fr


def build_B5():
    b = board(101)
    b.grad((0.03, 0.04, 0.10), (0.08, 0.09, 0.15))
    b.paint([(0, 470), (1280, 430), (1280, 720), (0, 720)], (0.20, 0.22, 0.27), 1.0)             # cold ground
    for x in range(0, 1280, 22):
        b.line([(x, 720), (x + 6, 690)], 1.2, (0.78, 0.82, 0.92), 0.5, smooth=False)               # frost
    for x in range(420, 760, 12):
        b.line([(x, 600), (x + 8, 560 - (x % 5) * 6)], 1.6, (0.70, 0.62, 0.42), 0.85, smooth=False)  # dry grass
    b.ellipse((600, 610), (80, 34), 0, 2.5, sb.INK, 0.9, fill=(0.40, 0.40, 0.44))                # stone on the ground
    return b.out().astype(np.float32)


def build_B5_hand():
    def draw(b):
        sb.hand(b, (980, 380), (720, 470), w=80, col=(0.78, 0.62, 0.50), cuff=(0.45, 0.36, 0.26), curl=0.55)
        b.ellipse((700, 470), (46, 32), 20, 2.5, sb.INK, 0.9, fill=(0.46, 0.46, 0.50))            # the striking stone
    return layer_from(draw, 102)


def shot_B5(f, base, hand):
    t = f / FPS
    strike = [39.75, 40.2]
    dy = 0.0
    for s in strike:
        dy += -50 * np.exp(-((t - (s - 0.18)) / 0.12) ** 2) + 0
    fr = base.copy()
    hp, ha = shift_layer(*hand, 0, dy)
    fr = over(fr, hp, ha)
    rng = np.random.default_rng(int(t * 24))
    for s in strike:
        if s <= t < s + 0.35:
            u = (t - s) / 0.35
            for k in range(14):
                ang = rng.uniform(-2.6, -0.5)
                r_ = 40 + 160 * u * rng.uniform(0.5, 1.0)
                c = (650 + r_ * np.cos(ang), 560 + r_ * np.sin(ang) + 120 * u * u)
                fr = glow(fr, c, 0.03, 1.2 * (1 - u))
    k = ease(40.5, 41.0, t)
    if k > 0:
        fr = fire(fr, (590, 572), k * 1.6, t)
    return fr


# ---------------------------------------------------------------- strip
def strip(f):
    t = f / FPS
    sh = next(s for s in SHOTS if s[1] <= f <= s[2])
    img = Image.new('RGB', (W, STRIP), (24, 24, 26))
    d = ImageDraw.Draw(img)
    fb, fs, fsm = ImageFont.truetype(SANSB, 17), ImageFont.truetype(SANS, 15), ImageFont.truetype(SANS, 13)
    col = TAGCOL[sh[3]]
    d.text((12, 6), sh[0], font=fb, fill=(255, 255, 255))
    d.rectangle([62, 7, 62 + 8 + 9 * len(sh[3]), 26], fill=col[::-1])
    d.text((66, 8), sh[3], font=fsm, fill=(20, 20, 20))
    lyr = [l for l in LYRICS if l[0] <= t + 1e-6][-1][1]
    d.text((200, 6), '%d:%06.3f  f%04d' % (int(t // 60), t % 60, f), font=fb, fill=(255, 255, 255))
    d.text((380, 6), '♪ ' + lyr, font=fb, fill=(255, 230, 170))
    d.text((12, 32), sh[4][:150], font=fs, fill=(210, 210, 205))
    d.text((12, 52), sh[5][:150], font=fsm, fill=(160, 160, 155))
    d.text((W - 300, 52), 'lyric timing provisional · music unchanged', font=fsm, fill=(120, 120, 118))
    a = np.asarray(img)[..., ::-1].copy()
    for s in SHOTS:                                                      # shot timeline
        x0, x1 = int(s[1] / N * W), int((s[2] + 1) / N * W)
        a[84:92, x0:x1] = TAGCOL[s[3]]
        a[84:92, x0] = (20, 20, 20)
    a[78:96, int(f / N * W)] = (255, 255, 255)
    return a


# ---------------------------------------------------------------- layout references for the still requests
def export_layout_refs():
    global PROF
    PROF = glow_profile()
    out = os.path.join(R, 'requests', 'opening_layout_refs')
    os.makedirs(out, exist_ok=True)
    paper, _, _ = build_letter()
    h1, h1P, h1hand = build_H1()
    h2, h3 = build_H2(), build_H3()
    town, village, bare = landscape('town'), landscape('village'), landscape('bare')
    refs = {
        'IMG-03_letter': paper,                                           # the line's band left blank
        'IMG-04_war_aftermath': shot_H1(int(21.95 * FPS) + 1, h1, h1P, h1hand),
        'IMG-05_lullaby': shot_H2(545, *h2),
        'IMG-06_farewell': shot_H3(575, *h3),
        'IMG-07_heat': build_B2(),
        'IMG-08_newborn': build_B3(),
        'IMG-09_first_fire_close': build_B5() + 0,
        'IMG-10_landscape_town': town,
        'IMG-11_landscape_village': village,
        'IMG-12_landscape_bare': bare,
    }
    hand = build_B5_hand()
    refs['IMG-09_first_fire_close'] = over(refs['IMG-09_first_fire_close'], hand[0] * hand[1][..., None], hand[1])
    for k, v in refs.items():
        cv2.imwrite(os.path.join(out, k + '_layout.jpg'), to8(v), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('wrote', len(refs), 'layout refs to', out)


# ---------------------------------------------------------------- main
def main():
    global PROF
    PROF = glow_profile()
    cap = cv2.VideoCapture(APPROVED)
    approved = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        approved.append(fr)
    assert len(approved) == 146, len(approved)
    kv1, keep, occ = build_kv1()
    kv5_noflame = build_kv5()
    paper, line, alt = build_letter()
    h1, h1P, h1hand = build_H1()
    h2 = build_H2()
    h3 = build_H3()
    town, village, bare = landscape('town'), landscape('village'), landscape('bare')
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    sky_night = np.clip((420 - yy) / 420.0, 0, 1)
    base_land = landscape('base')
    pts = window_lights(town, base_land)
    vpts = window_lights(village, base_land, seed=5, n=12)
    b2, b3, b5 = build_B2(), build_B3(), build_B5()
    b5h = build_B5_hand()
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H + STRIP), '-r', str(FPS),
                           '-i', '-', '-t', '%.4f' % (N / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '20',
                           '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', OUT], stdin=subprocess.PIPE)
    for f in range(N):
        sid = next(s[0] for s in SHOTS if s[1] <= f <= s[2])
        if sid == 'O1':
            pic = shot_O1(f, kv1, occ)
        elif sid == 'S1–S3':
            pic = approved[f - 180].astype(np.float32)
        elif sid == 'V1':
            pic = shot_V1(f, kv5_noflame)
        elif sid == 'V2':
            pic = shot_V2(f, paper, line, alt)
        elif sid == 'H1':
            pic = shot_H1(f, h1, h1P, h1hand)
        elif sid == 'H2':
            pic = shot_H2(f, *h2)
        elif sid == 'H3':
            pic = shot_H3(f, *h3)
        elif sid == 'V4':
            pic = shot_V4(f, kv1, keep)
        elif sid == 'B1':
            pic = shot_B1(f, town, sky_night, pts)
        elif sid == 'B2':
            pic = shot_B2(f, b2)
        elif sid == 'B3':
            pic = shot_B3(f, b3)
        elif sid == 'B4':
            pic = shot_B4(f, town, village, bare, pts, sky_night, vpts)
        elif sid == 'B5':
            pic = shot_B5(f, b5, b5h)
        else:
            pic = shot_B6(f, bare)
        frame = np.vstack([to8(pic), strip(f)])
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()
    json.dump([dict(id=s[0], frames=[s[1], s[2]], song=[round(s[1] / FPS, 3), round((s[2] + 1) / FPS, 3)],
                    duration=round((s[2] - s[1] + 1) / FPS, 3), tag=s[3], picture=s[4], final=s[5]) for s in SHOTS],
              open(LOG, 'w'), indent=1, ensure_ascii=False)
    print('wrote', OUT)


if __name__ == '__main__':
    if '--layout-refs' in sys.argv:
        export_layout_refs()
    else:
        main()
