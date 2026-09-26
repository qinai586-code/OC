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


# ================================================================ 11 'cause the future goes FOOM
def foom_curve_y(x, bend, snapk):
    """Graph line under their feet: flat NOW line that bends exponentially, then snaps vertical."""
    base = 132
    if x < 150:
        return base
    y = base - bend * (math.exp((x - 150) / 26.0) - 1)
    return y


def s11(f):
    cv = f.cv
    t_goes, t_foom = wt("'cause the", 'goes'), wt("'cause the", 'FOOM')
    cv.fill('#f1e4c6')
    for x in range(-12, 334, 12):
        cv.rect(x, -12, 1, 204, '#e0cfa8')
    for y in range(-12, 194, 12):
        cv.rect(-12, y, 344, 1, '#e0cfa8')
    cv.rect(20, -12, 1, 204, '#94764e')
    cv.text('FUTURE', 24, 6, '#94764e', font='3')
    bend = 0.0 if f.t < t_goes else 0.35 * ease_out(clamp((f.t - t_goes) / (t_foom - t_goes)))
    k = f.t - t_foom
    launch = k >= 0
    pts = []
    for x in range(-12, 334, 2):
        y = foom_curve_y(x, bend if not launch else 0.35, 0)
        if launch and x >= 190:
            y = -60  # rail snapped vertical at x = 190
        pts.append((x, max(-40, y)))
    col = '#c8433f'
    prev = None
    for x, y in pts:
        if prev is not None:
            cv.line(prev[0], prev[1], x, y, col, width=2)
        prev = (x, y)
    if launch:
        cv.rect(189, -30, 3, 164, col)
    cv.text('NOW', 60, 136, '#94764e', font='3')
    # characters: stand on the line, then launched up along the rail
    for who, x0 in (('claude', 150), ('gpt', 178)):
        if not launch:
            y = foom_curve_y(x0, bend, 0)
            p = make_pose('Q', eyes='wide' if bend > 0.05 else 'open', mouth='o' if bend > 0.1 else 'none', lean=1 if bend > 0.1 else 0)
            cv.blit(render(who, p), x0, y + 1, flip=False)
        else:
            y = foom_curve_y(x0, 0.35, 0) - 900 * k * k - 60 * k
            p = PO.fall(f.step(12), who)
            p['eyes'], p['mouth'] = ('happy', 'shout') if who == 'gpt' else ('wide', 'o')
            cv.blit(render(who, p), x0 + 8 * k, y)
    if launch:
        speed_lines(cv, k, 11, 26, -12, 192, dirx=0, speed=0, c='#e0cfa8') if False else None
        for j in range(18):
            yy = (j * 37 + k * 900) % 220 - 20
            cv.rect(120 + (j * 53) % 110, snap(yy), 1, 14 + j % 10, '#c8b890')
        puff(cv, 190, 132, k, 7, n=12, c='#fbf8f2', c2='#d8c8a4', life=0.8, spread=40)
        if k < 0.35:
            cv.ring(190, 132, 10 + k * 260, '#fbf8f2', 2)
        if k < 0.08:
            f.flash = 1 - k / 0.08
        f.shake = (2.5 * max(0, 1 - k / 0.4) * math.sin(f.t * 90), 1.5 * max(0, 1 - k / 0.4))
        text_big(cv, 'FOOM', 250, 40, '#c8433f', scale=3, shadow='#7a2a22', align='center') if k < 0.5 else None
    f.cam['zoom'] = 1.0 + 0.06 * bend / 0.35


# ================================================================ 12 / 13 the Chinese room
HANZI = {
    'ni': A("""
        .#..#..
        #..####
        #.#..#.
        ##.#.#.
        #..#.#.
        #.#..#.
        #...##.
        """),
    'hao': A("""
        .#.####
        ####..#
        .#...#.
        .#.####
        #.#..#.
        .#...#.
        #.#.##.
        """),
    'ren': A("""
        ...#...
        ...#...
        ...#...
        ..#.#..
        .#...#.
        #.....#
        .......
        """),
    'da': A("""
        ...#...
        #######
        ...#...
        ..#.#..
        .#...#.
        #.....#
        .......
        """),
    'kou': A("""
        .......
        #####..
        #...#..
        #...#..
        #...#..
        #####..
        .......
        """),
}
HZ = list(HANZI)


def hanzi(cv, key, x, y, c):
    rows = [r for r in HANZI[key] if r.strip()]
    m = np.array([[ch == '#' for ch in r.ljust(7)[:7]] for r in rows])
    cv.mask_fill(m, c, x, y)


def slip(cv, x, y, key, c='#3a2a22'):
    cv.rect(x, y, 13, 11, '#f4f1ea')
    cv.rect(x, y + 10, 13, 1, '#c9c2b2')
    hanzi(cv, key, x + 3, y + 2, c)


ROOM = (64, 40, 192, 112)   # x, y, w, h (interior)


def room_bg(cv, t):
    x, y, w, h = ROOM
    cv.fill('#0a0b12')
    cv.rect(x - 6, y - 6, w + 12, h + 12, '#3a3040')
    cv.rect(x, y, w, h, '#6a5a4a')
    dgrad(cv, x, y, w, h, ['#7a6a54', '#5a4a3a'])
    cv.rect(x, y + h - 10, w, 10, '#4a3a2c')
    # door with a slot on the right wall
    cv.rect(x + w - 30, y + 18, 26, h - 28, '#3a2a20')
    cv.rect(x + w - 26, y + 50, 18, 4, '#0a0806')
    cv.text('IN/OUT', x + w - 29, y + 44, '#c9b88a', font='3')
    # the giant rulebook on a desk
    cv.rect(x + 70, y + 70, 60, 4, '#4a2e1c')
    cv.poly([(x + 68, y + 70), (x + 100, y + 60), (x + 132, y + 70)], '#f1e4c6')
    cv.line(x + 100, y + 60, x + 100, y + 70, '#a89c88')
    for i in range(4):
        cv.rect(x + 76 + (i % 2) * 30, y + 64 + (i // 2) * 3, 16, 1, '#8a7a60')
    cv.rect(x + 80, y + 50, 40, 8, '#8a1c24')
    cv.text('RULES', x + 90, y + 52, '#f2cd5a', font='3')


def s12(f):
    cv = f.cv
    room_bg(cv, f.t)
    x, y, w, h = ROOM
    t_room = wt('Trapped in', 'room,')
    # slips come in through the slot, get looked up, and go out
    k = f.lt
    slot_x, slot_y = x + w - 26, y + 50
    for i, t0 in enumerate([0.0, 0.45, 0.9]):
        kk = k - t0
        if kk < 0:
            continue
        key = HZ[i % len(HZ)]
        sx = slot_x - min(40, kk * 160)
        sy = slot_y - 4 + min(20, max(0, kk - 0.25) * 60)
        if kk < 1.2:
            slip(cv, snap(sx), snap(sy), key)
    # an answer slip posted back out on "room"
    if f.t > t_room:
        kk = f.t - t_room
        slip(cv, snap(slot_x - 20 + kk * 120), slot_y - 4, 'hao', c='#1f4f4a')
    # ChatGPT squeezed in, sitting, tail coiled, flipping the book
    from scenes.ch01_lab import gpt_sit
    tail = [(-3, -35), (-8, -31), (-9, -24), (-4, -21), (1, -25), (-2, -30)]
    p = gpt_sit(eyes='down' if f.step(4) % 3 else 'side', mouth='small', tail=tail, hy=2)
    cv.blit(render('gpt', p), x + 150, y + h - 10 + 35 - 36, flip=True)
    # sweat of concentration
    if f.step(3) % 2:
        cv.px(x + 146, y + 30, '#bfe8ff')
    f.cam.update(zoom=1.5, x=196, y=92)


def s13(f):
    cv = f.cv
    room_bg(cv, f.t)
    x, y, w, h = ROOM
    t_bag = wt('with a bag', 'bag')
    t_sh = wt('with a bag', 'shrooms')
    from scenes.ch01_lab import gpt_sit
    p = gpt_sit(eyes='wide' if f.t > t_sh else 'side', mouth='o' if f.t > t_sh else 'small',
                tail=[(-3, -35), (-8, -31), (-9, -24), (-4, -21), (1, -25), (-2, -30)], hy=2)
    cv.blit(render('gpt', p), x + 150, y + h - 11, flip=True)
    # Claude squeezed in at the left, holding a paper bag of glowing mushrooms
    cp = make_pose('Q', eyes='calm' if f.t < t_sh else 'happy', mouth='none' if f.t < t_sh else 'smile', arms_front=True,
                   arm_f=[(5, -50), (9, -45), (12, -42)])
    cv.blit(render('claude', cp), x + 40, y + h - 8)
    bx, by = x + 50, y + h - 58
    cv.rect(bx, by, 12, 14, '#c8a878')
    cv.rect(bx, by, 12, 2, '#a88858')
    if f.t > t_bag:
        for i in range(3):
            gx = bx + 2 + i * 4
            gy = by - 3 - (i % 2) * 2
            cv.rect(gx - 1, gy, 4, 2, ['#e8744a', '#9a7bff', '#6fe6c8'][i])
            cv.rect(gx, gy + 2, 2, 2, '#f4f1ea')
    # after "shrooms": the characters peel off the slips and swirl; palette cycles
    if f.t > t_sh:
        k = f.t - t_sh
        for i in range(10):
            a = i * 0.63 + k * 2.2
            r_ = 30 + i * 4 + k * 20
            hanzi(cv, HZ[i % len(HZ)], snap(160 + math.cos(a) * r_), snap(90 + math.sin(a) * r_ * 0.6),
                  ['#e8744a', '#9a7bff', '#6fe6c8', '#f2cd5a'][i % 4])
        ramps = [PAL.PINK, PAL.JADE, PAL.GOLD, PAL.DOOM]
        ph = int(k * 8) % 4
        grade(cv, ramps[ph][1:], strength=clamp(k / 0.3) * 0.75)
        f.cam['rot'] = 0.03 * math.sin(k * 5)
    f.cam.update(zoom=1.5, x=150, y=92)


# ================================================================ 14 the shoggoth under the lens
@lru_cache(maxsize=1)
def shoggoth_layer():
    from engine.px import Canvas
    cv = Canvas(344, 204, '#07050a', ox=12, oy=12)
    r = R(1414)
    for i in range(22):
        a = r(0, 6.28)
        cx, cy = 200 + math.cos(a) * r(0, 20), 80 + math.sin(a) * r(0, 20)
        pts = [(cx, cy)]
        for k in range(1, 7):
            pts.append((cx + math.cos(a + k * 0.4 * math.sin(i)) * k * 9, cy + math.sin(a + k * 0.35) * k * 8))
        cv.lines(pts, '#1c1426' if i % 2 else '#2a1c34', width=4)
        cv.lines(pts, '#3a2848', width=1)
    cv.circle(200, 80, 26, '#1c1426')
    for i in range(26):
        ex, ey = 200 + r(-40, 40), 80 + r(-34, 34)
        rr = r(1.5, 4)
        cv.circle(ex, ey, rr, '#e8e2d0')
        cv.circle(ex + r(-1, 1), ey, max(0.6, rr * 0.5), '#12060a')
    return np.array(cv.im)


def s14(f):
    cv = f.cv
    t_see = wt('See through', 'See')
    t_lies = wt('See through', 'lies,')
    dgrad(cv, -12, -12, 344, 204, ['#dfe8f0', '#c8d4e4', '#aab8cc'])
    cv.rect(-12, 150, 344, 50, '#8a98b0')
    slipk = ease_out(clamp((f.t - t_lies) / 0.3)) * 0.6 if f.t > t_lies else 0.0
    props.mascot(cv, 200, 80, 28, t=f.t, wave=True, slip=slipk)
    if f.t < t_lies:
        cv.rect(228, 38, 50, 12, '#f4f1ea')
        cv.text('Hi! Help?', 231, 41, '#2a2440', font='3')
    # Claude with the magnifying glass
    cp = make_pose('Q', eyes='sharp' if False else 'calm', mouth='none', arms_front=True,
                   arm_f=[(5, -50), (10, -56), (14, -62)])
    cv.blit(render('claude', cp), 96, 152)
    # the lens slides over the mascot after "See"
    k = clamp((f.t - t_see) / 0.8)
    lx, ly = lerp(118, 196, ease_io(k)), lerp(88, 80, ease_io(k))
    R_ = 26
    a = np.array(cv.im)
    sh = shoggoth_layer()
    H_, W_ = a.shape[:2]
    Y, X = np.ogrid[:H_, :W_]
    m = (X - (lx + 12)) ** 2 + (Y - (ly + 12)) ** 2 <= R_ * R_
    if f.t > t_see:
        a[m] = sh[m]
        # tentacles twitch: shift a few rows
    cv.set_arr(a)
    cv.ring(lx, ly, R_, '#c8a040', 2)
    cv.ring(lx, ly, R_ + 2, '#6a4a10')
    cv.line(lx - 18, ly + 18, 110 + 14, 152 - 62, '#6a4a10', width=3)
    if f.t > t_lies and f.t - t_lies < 0.1:
        f.shake = (1, 0)


# ================================================================ 15 shinigami eyes / 16 numbers become stars
def crowd_numbers(cv, t, seed, people, glitch_i=None):
    r = R(seed)
    for i, (x, y) in enumerate(people):
        n = r.i(1, 99)
        s = str(n) if i != glitch_i else ('??' if int(t * 10) % 2 else '%%')
        if (int(t * 8) + i) % 11 == 0:
            s = str(r.i(1, 99))
        cv.text(s, snap(x) + 1, snap(y) - 22, '#6fe6c8' if i != glitch_i else '#f2c230', font='3')


def s15(f):
    cv = f.cv
    t_shin = wt('with your shinigami', 'shinigami')
    t_eyes = wt('with your shinigami', 'eyes')
    if f.t < t_shin + 0.35:
        # ECU: ChatGPT's eye lights up
        cv.fill(PAL.GPT['S'])
        glow = clamp((f.t - t_shin) / 0.2)
        draw_eye(cv, 160, 96, 180, 'gpt', open_=1.0, glow=glow, pupil=1 - 0.4 * glow, t=f.t)
        cv.poly([(-12, -12), (332, -12), (332, 24), (240, 18), (200, 36), (160, 14), (110, 34), (60, 16), (-12, 30)], PAL.GPT['k'])
        f.cam['zoom'] = 1.0 + 0.1 * glow
        return
    # POV over the town: tiny people with jade numbers over their heads; the kid's number glitches
    props.town(cv, f.t, horizon=112, pal=props.TOWN_NIGHT, lights=0.5, rows=3)
    cv.rect(-12, 112, 344, 80, '#141828')
    cv.rect(-12, 112, 344, 1, '#222849')
    ppl = []
    r = R(1515)
    for i in range(16):
        x = 20 + i * 18 + r(-4, 4)
        y = 150 + (i % 3) * 8
        cv.blit(folk(1500 + i, 'stand', 0, 11), x, y, flip=r() < 0.5)
        ppl.append((x, y))
    kx, ky = 160, 158
    cv.blit(kid('stand'), kx, ky)
    ppl.append((kx - 3, ky + 6))
    crowd_numbers(cv, f.t, 15, ppl, glitch_i=len(ppl) - 1)
    # jade tint of her vision
    grade(cv, ['#051312', '#0b2623', '#123d38', '#1c5c52', '#2c8574', '#4fb49b', '#95e3cc'], strength=0.55)
    crowd_numbers(cv, f.t, 15, ppl, glitch_i=len(ppl) - 1)
    f.cam['zoom'] = 1.04
    f.cam['y'] = 100


def s16(f):
    cv = f.cv
    k = f.lt
    # 0-1.2 s: numbers float up and turn into stars; 1.2-2.8 s: tilt down to the dusk town
    tilt = ease_io(clamp((k - 1.1) / 1.5))
    sky_y = snap(lerp(0, -140, tilt))
    dgrad(cv, -12, -12, 344, 204, ['#0e1020', '#1b1a40', '#3a2a5a'])
    stars(cv, 16, 50, f.t, 0, sky_y, 320, 180)
    r = R(1616)
    for i in range(24):
        x0 = 20 + i * 12
        y0 = 150 - r(0, 30)
        y = y0 - k * 90 * r(0.7, 1.2) + sky_y
        if k < 0.9:
            cv.text(str(r.i(1, 99)), snap(x0), snap(y), '#6fe6c8', font='3')
        else:
            cv.px(snap(x0 + 2), snap(y), '#e9fffa' if i % 3 else '#6fe6c8')
    if tilt > 0:
        from engine.px import Canvas
        sub = Canvas(344, 204, '#000000', ox=12, oy=12)
        props.town(sub, f.t, horizon=150, pal=props.TOWN_DUSK, lights=0.35, rows=3, hill=16)
        arr = np.array(sub.im)
        oy = snap(lerp(200, 0, tilt))
        a = np.array(cv.im)
        if oy < 204:
            a[oy:] = arr[:204 - oy]
        cv.set_arr(a)


SHOTS = [
    Shot('10_knob1', 22.78, 0, s10),
    Shot('11_foom', 24.30, 0, s11),
    Shot('12_chinese_room', 26.30, 0, s12),
    Shot('13_shrooms', 27.98, 0, s13),
    Shot('14_shoggoth', 29.90, 0, s14),
    Shot('15_shinigami', 33.34, 0, s15),
    Shot('16_break', 35.80, 0, s16),
]
