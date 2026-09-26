"""Chapter 2 — chorus 1 + break (22.78 - 38.62): the P(DOOM) knob (5 -> 10), FOOM, the Chinese room, the bag of
shrooms, the shoggoth under the magnifying glass, shinigami eyes over the town, numbers rising into dusk stars."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw
from engine.film import Shot, MARGIN, CW, CH
from engine.px import rgb, rgba, Sprite, silhouette, dilate4, dilate8, parse_ascii, ascii_block as A
from art.body import render, make_pose
from art import poses as PO
from art.portrait import bust
from art.ecu import draw_eye
from art import palette as PAL
from scenes.kit import *
from scenes import props
import song

G, C = PAL.GPT, PAL.CLAUDE
HAND_LINE = '#c98f7a'      # Claude's hand outline (same as the body painter)
NAIL = '#fff4ec'


def wt(prefix, word):
    return song.word_time(prefix, word)


# ================================================================ hard-edged prop painter (view coords)
def _mask():
    return Image.new('1', (CW, CH), 0)


def m_poly(pts):
    im = _mask()
    ImageDraw.Draw(im).polygon([(round(x + MARGIN), round(y + MARGIN)) for x, y in pts], fill=1)
    return np.array(im, bool)


def m_ellipse(cx, cy, rx, ry):
    im = _mask()
    cx, cy = cx + MARGIN, cy + MARGIN
    ImageDraw.Draw(im).ellipse([round(cx - rx), round(cy - ry), round(cx + rx), round(cy + ry)], fill=1)
    return np.array(im, bool)


def m_limb(pts, widths, caps=True):
    """Tapered strip through pts with per-point widths (same construction as art.body.limb_mask)."""
    im = _mask()
    d = ImageDraw.Draw(im)
    n = len(pts)
    left, right = [], []
    for i in range(n):
        j0, j1 = max(0, i - 1), min(n - 1, i + 1)
        dx, dy = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        h = (widths[i] - 1) / 2
        left.append((MARGIN + pts[i][0] + nx * h, MARGIN + pts[i][1] + ny * h))
        right.append((MARGIN + pts[i][0] - nx * h, MARGIN + pts[i][1] - ny * h))
    d.polygon([(round(x), round(y)) for x, y in left + right[::-1]], fill=1)
    if caps:
        for (x, y), w in zip(pts, widths):
            r = (w - 1) / 2
            if r >= 1:
                d.ellipse([round(MARGIN + x - r), round(MARGIN + y - r), round(MARGIN + x + r), round(MARGIN + y + r)], fill=1)
    return np.array(im, bool)


def shift(m, dx, dy):
    o = np.zeros_like(m)
    h, w = m.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    o[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return o


def edge(m):
    return m & ~(shift(m, 1, 0) & shift(m, -1, 0) & shift(m, 0, 1) & shift(m, 0, -1))


class Cel:
    """Paint masks with rim shading and 1 px lines into a full-canvas RGBA layer, then stamp it on the canvas."""

    def __init__(self):
        self.a = np.zeros((CH, CW, 4), np.uint8)

    def put(self, m, c):
        self.a[m] = rgba(c)

    def part(self, m, fill, line=None, shade=None, light=None, sdir=1, sw=2, lw=1, bottom=0):
        if not m.any():
            return
        self.put(m, fill)
        if shade:
            s = m & ~shift(m, -sw * sdir, 0)
            if bottom:
                s |= m & ~shift(m, 0, -bottom)
            self.put(s, shade)
        if light:
            self.put(m & ~shift(m, lw * sdir, 0) & shift(m, 0, 1), light)
        if line:
            self.put(edge(m), line)

    def stamp(self, cv):
        a = np.array(cv.im)
        m = self.a[..., 3] > 127
        a[m] = self.a[m]
        cv.set_arr(a)


def arr_blit(cv, arr):
    """Paste a full-canvas RGBA layer (CH x CW) built in canvas coords."""
    cv.blit(arr, -MARGIN, -MARGIN)


def rot(pts, ang, cx, cy):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


# ================================================================ 10 the P(DOOM) knob, clicked up 5 -> 10
KX, KY, KR = 214, 88, 30          # knob centre / radius
SPX, SPY, SPR = 80, 90, 52        # speaker


@lru_cache(maxsize=2)
def amp_layer():
    """The amp front (tolex, piping, speaker basket) as a static full-canvas layer."""
    from engine.px import Canvas
    cv = Canvas(CW, CH, '#000000', ox=MARGIN, oy=MARGIN)
    tolex, tolex2, pipe = '#231915', '#2c201b', '#d8c7a4'
    cv.fill(tolex)
    dfill(cv, -12, -12, 344, 204, tolex, tolex2, 0.25)
    # piping around the front panel and a brass strip
    cv.frame(-4, 4, 328, 164, pipe)
    cv.frame(-3, 5, 326, 162, '#8a7a5e')
    # speaker: baffle ring, surround, cone ridges (the moving parts are drawn per frame)
    cv.circle(SPX, SPY, SPR + 6, '#141010')
    cv.circle(SPX, SPY, SPR + 4, '#3a3030')
    for a_ in range(8):
        ang = a_ / 8 * math.tau + 0.39
        bx, by = SPX + math.cos(ang) * (SPR + 5), SPY + math.sin(ang) * (SPR + 5)
        cv.rect(snap(bx) - 1, snap(by) - 1, 3, 3, '#9aa0aa')
        cv.px(snap(bx), snap(by), '#d2d8e0')
    # brand plate
    cv.rect(SPX - 20, 150, 40, 9, '#1a1414')
    cv.rect(SPX - 20, 150, 40, 1, '#4a3a2a')
    cv.text('DOOMCO', SPX, 152, '#d8c7a4', font='3', align='center')
    a = np.array(cv.im)
    return a


def speaker(cv, push, t):
    """Cone at rest (push=0) or thrown forward (push=1): the dust cap and ridges grow toward the camera."""
    cv.circle(SPX, SPY, SPR, '#171313')                       # rubber surround
    cv.ring(SPX, SPY, SPR - 1, '#2e2626')
    cone = SPR - 5
    cv.circle(SPX, SPY, cone, '#3c3431')
    # dithered cone shading (light from upper left)
    dfill(cv, SPX - cone, SPY - cone, cone * 2, cone * 2, '#3c3431', '#4a413d', 0.0)
    for k, r in enumerate((0.88, 0.72, 0.56)):
        rr = cone * (r + 0.05 * push)
        cv.ring(SPX, SPY, rr, '#2a2321')
        cv.ring(SPX - 1, SPY - 1, rr, '#51463f') if k == 0 else None
    cap = cone * (0.36 + 0.12 * push)
    cv.circle(SPX + 1, SPY + 1, cap, '#0e0b0b')
    cv.circle(SPX, SPY, cap, '#1e1918')
    cv.circle(SPX - cap * 0.35, SPY - cap * 0.35, cap * 0.35, '#3a3230')
    cv.px(snap(SPX - cap * 0.45), snap(SPY - cap * 0.5), '#6a5e58')


def knob_value(t, clicks, t_pd):
    """Detent value + displayed (animated) value."""
    v = 5.0
    det = 5
    for tc in clicks:
        k = t - tc
        if k >= 0:
            det += 1
            # quick twist with a tiny overshoot into the detent (15 fps drawings)
            kk = math.floor(k * 30) / 30
            v = det - 1 + (1.35 if kk < 0.034 else 1.0 if kk >= 0.067 else 1.12)
            v = det if kk >= 0.067 else v
    k = t - t_pd
    if k >= 0:
        det = 10
        kk = math.floor(k * 30) / 30
        # big wind: overshoot to ~14 then spring back into the 10 detent
        seq = [11.5, 13.6, 14.2, 13.0, 10.6, 9.6, 10.4, 10.0]
        i = int(kk * 30)
        v = seq[i] if i < len(seq) else 10.0
    return det, v


def claude_hand(cel, cx, cy, ang, grip=1.0, slide=0.0):
    """Claude's right hand pinching the knob from the right: cream cardigan sleeve + ribbed cuff + skin hand.
    Drawn in knob-local coordinates (px), rotated by `ang` about the knob centre. slide pushes it off to the right."""
    ox = slide * 150
    def T(pts):
        return rot([(x + ox, y) for x, y in pts], ang, cx, cy)
    # sleeve to the right edge
    sl = m_poly(T([(64, -16), (70, 22), (180, 44), (180, -40)]))
    cel.part(sl, C['c'], line=C['N'], shade=C['n'], light=C['C'], sw=2, bottom=2)
    # a sleeve bow (the cardigan detail) and knit rows
    for k in range(3):
        cel.put(m_limb(T([(90 + k * 20, -20 + k * 1), (92 + k * 20, 26 + k * 3)]), [1, 1]) & sl, C['n'])
    bow = m_poly(T([(98, -2), (104, 2), (98, 6)])) | m_poly(T([(110, -2), (104, 2), (110, 6)]))
    cel.put(bow & sl, C['r'])
    # ribbed cuff
    cuff = m_poly(T([(56, -18), (66, -20), (72, 24), (60, 26)]))
    cel.part(cuff, C['n'], line=C['N'], light=C['c'])
    for k in range(4):
        cel.put(m_limb(T([(58 + k * 3, -18), (61 + k * 3, 25)]), [1, 1]) & cuff & ~edge(cuff), C['N'])
    # back of the hand (palm block)
    hb = m_poly(T([(30, -20), (40, -24), (58, -18), (61, 16), (44, 22), (30, 12)]))
    # curled fingers (knuckle bumps under the index finger)
    curl = m_limb(T([(40, -12), (32, -12), (30, -4)]), [8, 8, 7]) | m_limb(T([(42, -2), (34, -1), (33, 6)]), [7, 7, 6])
    thumb = m_limb(T([(48, 16), (36, 30), (22, 36), (12, 34)]), [10, 9, 8, 7])
    index = m_limb(T([(40, -20), (30, -34), (18, -38), (8, -35)]), [10, 9, 8, 7])
    cel.part(curl, C['S'], line=HAND_LINE, shade=C['s'], sw=2)
    cel.part(hb, C['S'], line=HAND_LINE, shade=C['s'], sw=3, bottom=2)
    cel.part(thumb, C['S'], line=HAND_LINE, shade=C['s'], sw=2, bottom=2)
    cel.part(index, C['S'], line=HAND_LINE, shade=C['s'], sw=2, bottom=1)
    # knuckle creases + nails
    for p0, p1 in (((30, -30), (34, -27)), ((26, 29), (30, 27))):
        cel.put(m_limb(T([p0, p1]), [1, 1]), C['s'])
    for (nx_, ny_) in ((10, -37), (13, 35)):
        cel.put(m_ellipse(*T([(nx_, ny_)])[0], 1.5, 1.2), NAIL)
    # a hint of hand shadow on the plate below (1 px darker line)


def s10(f):
    cv = f.cv
    t_im = wt("I'm upping", "I'm")
    t_up = wt("I'm upping", 'upping')
    t_my = wt("I'm upping", 'my')
    t_ping = (t_up + t_my) / 2          # "up-PING": the second syllable of "upping"
    t_pd = wt("I'm upping", 'P(doom)')
    t_kick = song.bar(13)
    clicks = [t_im, t_up, t_ping, t_my]
    det, v = knob_value(f.t, clicks, t_pd)
    arr_blit(cv, amp_layer())
    # speaker: a small flutter on each click, the big throw on the kick downbeat
    k = f.t - t_kick
    push = 0.0
    if k >= 0:
        seq = [1.0, 0.9, 0.55, 0.2, -0.15, 0.05, 0.0]
        i = int(k * 30)
        push = seq[i] if i < len(seq) else 0.0
    speaker(cv, push, f.t)
    # air rings off the cone on the kick
    if 0 <= k < 0.35:
        for j in range(2):
            rr = SPR + 4 + (k - j * 0.06) * 160
            if rr > SPR + 4:
                cv.ring(SPX, SPY, rr, '#d8c7a4' if j == 0 else '#8a7a5e')
    # the knob (the recurring prop)
    kick_glow = 1.0 if 0 <= k < 0.12 else 0.0
    props.knob(cv, KX, KY, KR, v, t=f.t, readout=f"{det}%", glow=0.8 if 0 <= f.t - t_pd < 0.25 else 0.0)
    # pilot jewel lamp (flashes with the kick)
    lx, ly = KX - 52, KY + 44
    cv.circle(lx, ly, 3, '#2a0c0c')
    cv.circle(lx, ly, 2, '#ff5040' if kick_glow or (f.t > t_pd and f.step(4) % 2 == 0) else '#7a1a18')
    cv.px(lx - 1, ly - 1, '#ffd0c0' if kick_glow else '#c04030')
    # click marks at the grip
    for tc in clicks + [t_pd]:
        kc = f.t - tc
        if 0 <= kc < 0.1:
            big = tc == t_pd
            for j, a0 in enumerate((-0.5, -0.25, 0.0) if not big else (-0.7, -0.45, -0.2, 0.05, 0.3)):
                a_ = props.knob_angle(v) - props.knob_angle(5) + a0 - 0.15
                r0, r1 = KR + 8 + kc * 40, KR + 12 + kc * 40 + (6 if big else 2)
                cv.line(KX + math.sin(a_) * r0, KY - math.cos(a_) * r0, KX + math.sin(a_) * r1, KY - math.cos(a_) * r1,
                        '#fbf8f2')
    # Claude's hand: it holds the knob until just after the kick, then lets go
    ang = props.knob_angle(v) - props.knob_angle(5)
    rel = clamp((f.t - (t_kick + 0.12)) / 0.16)
    if rel < 1:
        cel = Cel()
        claude_hand(cel, KX, KY, ang, slide=ease_in(rel))
        cel.stamp(cv)
    # the kick thumps the whole amp
    if 0 <= k < 0.14:
        f.shake = ((1.5 if f.step(30) % 2 else -1.5) * (1 - k / 0.14), (1.0 if f.step(30) % 2 else -0.5) * (1 - k / 0.14))
    if 0 <= f.t - t_pd < 0.06:
        f.shake = (0.8, 0)
    # slow push toward the knob; a small bump on "P(doom)"
    f.cam['x'] = 160 + 10 * ease_io(f.u)
    f.cam['zoom'] = 1.0 + 0.03 * ease_io(f.u) + (0.03 * (1 - clamp((f.t - t_pd) / 0.3)) if f.t > t_pd else 0)


def knob_angle_px(v):
    return props.knob_angle(v)


# ================================================================ placeholder draws (filled in below)
def _todo(name):
    def draw(f):
        f.cv.fill('#101018')
        f.cv.text(name, 160, 86, '#6a7fb4', align='center')
    return draw


s11 = _todo('11 foom')
s12 = _todo('12 chinese room')
s13 = _todo('13 shrooms')
s14 = _todo('14 shoggoth')
s15 = _todo('15 shinigami')
s16 = _todo('16 break')

SHOTS = [
    Shot('10_knob1', 22.78, 0, s10),
    Shot('11_foom', 24.30, 0, s11),
    Shot('12_chinese_room', 26.30, 0, s12),
    Shot('13_shrooms', 27.98, 0, s13),
    Shot('14_shoggoth', 29.90, 0, s14),
    Shot('15_shinigami', 33.34, 0, s15),
    Shot('16_break', 35.80, 0, s16),
]
