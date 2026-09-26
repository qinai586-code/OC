"""Chapter 4 — chorus 2 (59.10 - 69.68): the P(DOOM) wheel, the basilisk boom, NVDA to the moon,
the Omega Point (COMING SOON) and one-E-thirty flops.

Shots 22-26. Everything times off song.word_time / song.beat."""
import math
from functools import lru_cache
import numpy as np
from engine.film import Shot, MARGIN, CW, CH
from engine.px import Canvas, rgb, rgba, Sprite, dither_mask
from art.body import render, make_pose
from art import poses as PO
from art.portrait import bust
from art import palette as PAL
from scenes.kit import *
from scenes.props import knob, knob_angle, marquee, town, TOWN_DUSK
import song

G, C = PAL.GPT, PAL.CLAUDE
SIX = song.BEAT / 4          # a sixteenth note (s)


def wt(prefix, word):
    return song.word_time(prefix, word)


def new_layer():
    """A blank canvas the size of a frame canvas (view coords, with the margin)."""
    return Canvas(CW, CH, (0, 0, 0), ox=MARGIN, oy=MARGIN)


def put_layer(cv, arr):
    cv.set_arr(arr.copy())


def arm_to(sh, hand, lean=0, bob=0, who='claude', flipbend=False):
    """Two-bone arm (8 + 8 px) from the pose shoulder to an absolute hand position (sprite px).
    Accounts for how body.py offsets shoulder/elbow by lean/bob. The elbow bends downward."""
    sx, sy = sh[0] + lean, sh[1] + bob + (2 if who == 'gpt' else 0)
    hx, hy = hand
    dx, dy = hx - sx, hy - sy
    L = math.hypot(dx, dy) or 1.0
    if L > 16:
        hx, hy = sx + dx / L * 16, sy + dy / L * 16
        dx, dy, L = hx - sx, hy - sy, 16.0
    b = math.sqrt(max(0.0, 64 - (L / 2) ** 2))
    nx, ny = -dy / L, dx / L
    if (ny < 0) != flipbend:
        nx, ny = -nx, -ny
    ex, ey = sx + dx / 2 + nx * b, sy + dy / 2 + ny * b
    return [sh, (round(ex - lean * .7), round(ey - bob)), (round(hx), round(hy))]


def legs_crouch(bob, front=6, back=-6, who='claude'):
    """Braced stance: hip lowered by bob, near leg back, far leg forward."""
    hy = -35 + bob
    ln = [(-2, hy), (round(back * 0.4) - 1 + (1 if bob > 1 else 0), round(hy + (-3 - hy) * 0.5) - (1 if bob > 1 else 0)), (back, -3)]
    lf = [(3, hy), (round(front * 0.7) + 3 + bob // 2, round(hy + (-3 - hy) * 0.5) - bob // 2), (front + 3, -3)]
    return ln, lf


# ================================================================ 22 the P(DOOM) wheel in the cliff
K22 = dict(cx=160, cy=96, R=30)
LEDGE = 160
ROCK = ['#17131f', '#221c2c', '#2d2539', '#3a3048', '#4a3e58', '#5e5070']


@lru_cache(maxsize=2)
def cliff_layer():
    cv = new_layer()
    # dusk sky + a far valley with the tiny town (seen past the cliff's left edge)
    town(cv, 0.0, horizon=132, seed=5, pal=TOWN_DUSK, scale=0.35, lights=0.5, rows=2, hill=10)
    # rock face (x from the jagged edge to the right)
    r = R(22)
    edge = []
    for y in range(-12, 200, 6):
        edge.append((34 + r(-5, 5) + (y - 90) * 0.06, y))
    pts = [(344, -12)] + [(x, y) for x, y in edge] + [(344, 200)]
    cv.poly(pts, ROCK[2])
    # strata bands and blocks (dithered), cracks
    a = np.array(cv.im)
    face = np.zeros(a.shape[:2], bool)
    face[np.all(a[..., :3] == np.array(rgb(ROCK[2]), np.uint8), axis=-1)] = True
    H_, W_ = face.shape
    Y, X = np.mgrid[:H_, :W_]
    band = ((Y + X // 7) // 11) % 3
    m1 = face & (band == 0) & dither_mask(W_, H_, 0.5)
    m2 = face & (band == 2) & dither_mask(W_, H_, 0.35)
    a[m1] = rgba(ROCK[3])
    a[m2] = rgba(ROCK[1])
    cv.set_arr(a)
    for i in range(26):
        x0, y0 = r(40, 330), r(-10, 150)
        pts = [(x0, y0)]
        for k in range(r.i(2, 5)):
            x0 += r(-6, 6); y0 += r(4, 10)
            pts.append((x0, y0))
        cv.lines(pts, ROCK[0])
        cv.lines([(x + 1, y) for x, y in pts], ROCK[3])
    # rim light along the jagged edge
    cv.lines([(x, y) for x, y in edge], ROCK[5])
    cv.lines([(x + 1, y) for x, y in edge], ROCK[4])
    # the steel bezel the knob is set into
    cx, cy, Rk = K22['cx'], K22['cy'], K22['R']
    rb = Rk * 1.45 + 15
    cv.circle(cx + 2, cy + 3, rb + 3, ROCK[0])
    cv.circle(cx, cy, rb + 3, '#4a4d57')
    cv.circle(cx, cy, rb + 1, '#2a2d35')
    cv.circle(cx, cy, rb, '#1c1e24')
    for i in range(10):
        ang = i / 10 * math.tau + 0.3
        bx, by = cx + math.sin(ang) * (rb - 3), cy - math.cos(ang) * (rb - 3)
        cv.rect(snap(bx) - 1, snap(by) - 1, 3, 3, '#6a6e7a')
        cv.px(snap(bx), snap(by), '#9aa0aa')
    # brass plaque behind the P(DOOM) label
    py = snap(cy - Rk * 1.45 - 22)
    cv.rect(cx - 20, py - 4, 41, 15, '#3a2a14')
    cv.rect(cx - 19, py - 3, 39, 13, '#8a6a2a')
    cv.rect(cx - 18, py - 2, 37, 11, '#5a4218')
    cv.rect(cx - 19, py - 3, 39, 1, '#c9a45a')
    # the LCD housing below
    cv.rect(cx - 19, cy + 45, 38, 15, '#0b0c10')
    cv.rect(cx - 18, cy + 46, 36, 13, '#1c1e24')
    # ledge
    cv.rect(-12, LEDGE, 344, 50, ROCK[1])
    cv.rect(-12, LEDGE, 344, 1, ROCK[4])
    cv.rect(-12, LEDGE + 1, 344, 1, ROCK[3])
    for x in range(-12, 332, 9):
        cv.rect(x + int(r(0, 5)), LEDGE + 3 + int(r(0, 5)), int(r(2, 5)), 1, ROCK[0])
    # tufts of dusk grass on the ledge
    for x in (24, 58, 250, 292, 318):
        for k in range(4):
            cv.line(x + k * 2, LEDGE, x + k * 2 + (k - 1), LEDGE - 3 - (k % 2) * 2, '#3a5a4a')
    return np.array(cv.im)


def wheel(cv, cx, cy, R, value):
    """The ship's-wheel rim and handles around the knob (rotating with its value)."""
    a0 = knob_angle(value)
    rr = R + 8
    # spokes from the skirt to the rim
    for k in range(8):
        a = a0 + k * math.pi / 4
        sa, ca = math.sin(a), -math.cos(a)
        cv.line(cx + sa * (R + 2), cy + ca * (R + 2), cx + sa * rr, cy + ca * rr, '#5a3a22', width=3)
    cv.ring(cx, cy, rr + 1, '#3e2414', 4)
    cv.ring(cx, cy, rr, '#8a5a32', 2)
    cv.ring(cx, cy, rr - 1, '#b07a44', 1) if False else None
    # brass bands where the spokes cross the rim + turned handles outside
    for k in range(8):
        a = a0 + k * math.pi / 4
        sa, ca = math.sin(a), -math.cos(a)
        cv.line(cx + sa * (rr + 2), cy + ca * (rr + 2), cx + sa * (rr + 9), cy + ca * (rr + 9), '#3e2414', width=4)
        cv.line(cx + sa * (rr + 2), cy + ca * (rr + 2), cx + sa * (rr + 9), cy + ca * (rr + 9), '#9a6438', width=2)
        cv.circle(cx + sa * (rr + 11), cy + ca * (rr + 11), 2.5, '#3e2414')
        cv.circle(cx + sa * (rr + 11) - 0.5, cy + ca * (rr + 11) - 0.5, 1.5, '#b07a44')
        cv.rect(snap(cx + sa * rr) - 1, snap(cy + ca * rr) - 1, 3, 3, '#c9a45a')


def rim_point(phi, cx=K22['cx'], cy=K22['cy'], r=K22['R'] + 8):
    """Point on the wheel rim at angle phi (degrees clockwise from up)."""
    a = math.radians(phi)
    return cx + math.sin(a) * r, cy - math.cos(a) * r


def s22(f):
    cv = f.cv
    put_layer(cv, cliff_layer())
    cx, cy, Rk = K22['cx'], K22['cy'], K22['R']
    hits = [wt("I'm upping my", "I'm"), wt("I'm upping my", 'upping'), wt("I'm upping my", 'my'),
            wt("I'm upping my", 'P(doom)')]
    vals = [10, 14, 18, 21, 25]
    n = sum(1 for h in hits if f.t >= h)
    v = vals[n]
    k = 9.0
    if n > 0:
        k = f.t - hits[n - 1]
        v = lerp(vals[n - 1], vals[n], ease_out(k / 0.09))
    # the final P(doom) heave overshoots and the ratchet settles back onto 25
    kf = f.t - hits[-1]
    if kf > 0:
        v = 25 + 1.2 * math.sin(clamp(kf / 0.35) * math.pi) * (1 - clamp(kf / 0.35))
    knob(cv, cx, cy, Rk, v, t=f.t, plate=False, label=True)
    wheel(cv, cx, cy, Rk, v)
    # LCD readout
    shown = int(round(v))
    col = '#8ff0d4'
    if kf > 0 and int(kf * 8) % 2 == 0 and kf < 0.5:
        col = '#e9fff6'
    s = f"{shown}%"
    cv.rect(cx - 17, cy + 47, 34, 11, '#0b1512')
    text_big(cv, s, cx, cy + 49, col, scale=1, align='center')
    # characters: 'set' (reach), 'heave' (pull) drawings, switched on each word
    heave = n > 0 and (k < 0.2 or n == 4)
    strain = f.step(12) % 2 if n == 4 and kf > 0.25 else 0
    # --- Claude, right of the wheel, facing left, hauling the rim down
    clx = 214
    if heave:
        bob, lean, phis = 4 + strain, -2, (98, 108)
    else:
        bob, lean, phis = 0, 1, (66, 76)
    hands = []
    for ph in phis:
        hx, hy = rim_point(ph)
        hands.append((clx - hx, hy - LEDGE))       # to sprite coords (flipped)
    ln, lf = legs_crouch(bob, front=4 if heave else 3, back=-7 if heave else -4)
    cp = make_pose('Q', eyes='closed' if heave else 'worried', mouth='shout' if heave and n == 4 else ('flat' if heave else 'none'),
                   bob=bob, lean=lean, arms_front=True, hair=-2 if heave else 0, leg_n=ln, leg_f=lf)
    cp['arm_n'] = arm_to((-4, -50), hands[1], lean, bob)
    cp['arm_f'] = arm_to((5, -50), hands[0], lean, bob)
    cv.blit(render('claude', cp), clx, LEDGE + 1, flip=True)
    # --- ChatGPT, left of the wheel, facing right, shoving the rim up
    gx = 108
    if heave:
        bob, lean, phis = -1, 2, (282, 292)
    else:
        bob, lean, phis = 4, 2, (246, 256)
    hands = []
    for ph in phis:
        hx, hy = rim_point(ph)
        hands.append((hx - gx, hy - LEDGE))
    ln, lf = legs_crouch(bob, front=5 if heave else 4, back=-9 if heave else -6, who='gpt')
    gp = make_pose('Q', eyes='sharp' if heave else 'open', mouth='grin' if heave else 'smile', bob=bob, lean=lean,
                   arms_front=True, leg_n=ln, leg_f=lf)
    gp['arm_n'] = arm_to((-4, -50), hands[0], lean, bob, who='gpt')
    gp['arm_f'] = arm_to((5, -50), hands[1], lean, bob, who='gpt')
    sw = [0, 1, 2, 1][f.step(8) % 4]
    gp['tail'] = [(-3, -35 + bob), (-9, -31), (-15, -27 + sw), (-21, -22 + sw), (-28, -21), (-35, -24 - sw)]
    cv.blit(render('gpt', gp), gx, LEDGE + 1)
    # effort marks + grit falling from the bezel on each heave
    for i, h in enumerate(hits):
        kk = f.t - h
        if 0 <= kk < 0.5:
            puff(cv, cx - 40, LEDGE - 2, kk, 30 + i, n=5, c=ROCK[4], c2=ROCK[3], spread=10)
            puff(cv, cx + 40, LEDGE - 2, kk, 40 + i, n=5, c=ROCK[4], c2=ROCK[3], spread=10)
            for j in range(6):
                rr_ = R(i * 10 + j)
                gx_ = cx + rr_(-60, 60)
                gy_ = cy - 60 + rr_(-4, 10) + kk * kk * 400
                cv.rect(snap(gx_), snap(gy_), 1, 2 if j % 2 else 1, ROCK[4])
    if kf > 0:
        sweat_drop(cv, clx - 12, LEDGE - 72, kf)
        sweat_drop(cv, gx + 14, LEDGE - 70, kf - 0.15)
    # camera: slow push in, a bump on every heave
    bump = sum(pulse(f.t - h, 0.12) for h in hits)
    f.shake = (0, bump * 1.2)
    f.cam['zoom'] = 1.0 + 0.04 * ease_io(f.u)
    f.cam['y'] = 92


def sweat_drop(cv, x, y, k):
    if k < 0:
        return
    yy = y + min(8, int(k * 16))
    cv.px(x, yy, '#bfe8ff'); cv.rect(x - 1, yy + 1, 3, 2, '#bfe8ff'); cv.px(x, yy + 3, '#8ac4e8')


# ================================================================ 23 the basilisk
HORIZON23 = 122
STONE = ['#26262e', '#3a3a44', '#4e4e5a', '#666672', '#82828e', '#a2a2ac']
GOLD = ['#6a4a14', '#c9a032', '#f2cd5a', '#fff2b0']


@lru_cache(maxsize=2)
def plain_layer():
    cv = new_layer()
    dgrad(cv, -12, -12, 344, HORIZON23 + 12, ['#1a1830', '#2c2644', '#4a3656', '#6e4658', '#9a6a5a', '#c89a6a'])
    stars(cv, 23, 30, 0.0, 0, 0, 320, 60, twinkle=False)
    # far hills, then near hills (the basilisk rises between them)
    return np.array(cv.im)


def hills(cv, y0, amp, seed, col, top=None):
    pts = [(-12, 200)]
    for x in range(-12, 340, 6):
        pts.append((x, y0 - amp * (0.5 + 0.5 * math.sin(x * 0.021 + seed)) - amp * 0.3 * math.sin(x * 0.07 + seed * 2)))
    pts.append((340, 200))
    cv.poly(pts, col)
    if top:
        cv.lines(pts[1:-1], top)


def basilisk(cv, cx, cy, s, t, eye=1.0, jaw=0.0, glint=0.0):
    """A huge stone serpent head seen from the front, rising: (cx, cy) = centre of the head. s = scale."""
    def P(x, y):
        return (cx + x * s, cy + y * s)
    # hood (cobra-like, stone plates)
    hood = [P(-44, 70), P(-50, 30), P(-46, 0), P(-34, -20), P(0, -28), P(34, -20), P(46, 0), P(50, 30), P(44, 70)]
    cv.poly(hood, STONE[1])
    cv.poly([P(-40, 70), P(-44, 30), P(-40, 4), P(-30, -12), P(0, -18), P(30, -12), P(40, 4), P(44, 30), P(40, 70)], STONE[2])
    # stone plate seams on the hood
    for i in range(-3, 4):
        cv.line(*P(i * 12, -14 + abs(i) * 3), *P(i * 13, 70), STONE[1])
    for yy in (8, 30, 52):
        cv.line(*P(-42, yy), *P(42, yy), STONE[1])
    # neck column below
    cv.poly([P(-22, 40), P(22, 40), P(26, 120), P(-26, 120)], STONE[2])
    for yy in range(46, 120, 10):
        cv.line(*P(-24, yy), *P(24, yy), STONE[1])
    # head: rounded wedge
    head = [P(-26, -6), P(-20, -26), P(-8, -34), P(8, -34), P(20, -26), P(26, -6), P(22, 14), P(12, 30), P(0, 34),
            P(-12, 30), P(-22, 14)]
    cv.poly(head, STONE[3])
    cv.poly([P(-20, -8), P(-16, -24), P(-6, -30), P(6, -30), P(16, -24), P(20, -8), P(0, -2)], STONE[4])
    # crown crest (the king of serpents)
    for dx, h in ((-12, 12), (0, 18), (12, 12)):
        cv.poly([P(dx - 4, -30), P(dx, -30 - h), P(dx + 4, -30)], STONE[4])
        cv.line(*P(dx, -30 - h), *P(dx + 3, -31), STONE[2])
    # scales on the snout
    for (x, y) in ((-8, -18), (0, -22), (8, -18), (-4, -10), (4, -10), (0, 4)):
        cv.poly([P(x - 4, y), P(x, y - 3), P(x + 4, y), P(x, y + 3)], STONE[3])
        cv.line(*P(x - 4, y), *P(x, y + 3), STONE[2])
    # cracks + moss
    cv.lines([P(10, -30), P(14, -20), P(11, -12), P(16, -2)], STONE[1])
    cv.lines([P(-18, 6), P(-12, 12), P(-14, 20)], STONE[1])
    for (x, y) in ((-22, 10), (20, -12), (-30, 40), (34, 24)):
        cv.rect(snap(cx + x * s), snap(cy + y * s), 3, 1, '#4a5a3a')
    # jaw line (opens on boom)
    jy = 20 + jaw * 8
    if jaw > 0.05:
        cv.poly([P(-18, 14), P(18, 14), P(10, jy + 6), P(-10, jy + 6)], '#141218')
        for i in range(-2, 3):
            cv.poly([P(i * 6 - 2, 14), P(i * 6 + 2, 14), P(i * 6, 18)], STONE[5])
    cv.lines([P(-20, 14), P(-8, 18), P(0, 16), P(8, 18), P(20, 14)], STONE[0])
    # nostrils
    cv.rect(snap(cx - 5 * s), snap(cy + 4 * s), 2, 1, STONE[0]); cv.rect(snap(cx + 4 * s), snap(cy + 4 * s), 2, 1, STONE[0])
    # brow ridges
    cv.poly([P(-26, -12), P(-10, -16), P(-12, -10), P(-24, -6)], STONE[2])
    cv.poly([P(26, -12), P(10, -16), P(12, -10), P(24, -6)], STONE[2])
    # eyes: cold gold almonds with slit pupils
    for side in (-1, 1):
        ex, ey = cx + side * 18 * s, cy - 6 * s
        w, h = 7 * s, max(1.0, 3.2 * s * eye)
        if eye <= 0.05:
            cv.line(ex - w, ey, ex + w, ey, STONE[0])
            continue
        cv.poly([(ex - w - 1, ey), (ex - w * 0.3, ey - h - 1), (ex + w + 1, ey - 1), (ex + w * 0.3, ey + h + 1)], STONE[0])
        cv.poly([(ex - w, ey), (ex - w * 0.3, ey - h), (ex + w, ey - 1), (ex + w * 0.3, ey + h)], GOLD[1])
        cv.poly([(ex - w * 0.6, ey - h * 0.3), (ex - w * 0.2, ey - h * 0.7), (ex + w * 0.5, ey - h * 0.4)], GOLD[2])
        cv.rect(snap(ex) - 0, snap(ey - h + 1), 1, max(1, snap(2 * h - 1)), '#101010')
        if glint > 0:
            cv.px(snap(ex - w * 0.4), snap(ey - h * 0.5), GOLD[3])


def s23(f):
    cv = f.cv
    put_layer(cv, plain_layer())
    t_hear = wt('I hear', 'hear')
    t_bas = wt('I hear', 'basilisk')
    t_boom = wt('I hear', 'boom')
    kb = f.t - t_boom
    # rise: begins on "basilisk", up by just before "boom"
    rise = ease_out(clamp((f.t - t_bas + 0.1) / (t_boom - t_bas - 0.1)))
    bx, by = 222, lerp(HORIZON23 + 70, HORIZON23 - 30, rise)
    hills(cv, HORIZON23 - 4, 10, 1.3, '#3a2c48', '#4a3a58')
    eye = clamp((f.t - (t_boom - 0.45)) / 0.08)
    jaw = pulse(kb, 0.6) if kb >= 0 else 0.0
    shk = (math.sin(f.t * 50) * 0.8, 0) if 0 < rise < 1 else (0, 0)
    basilisk(cv, bx + shk[0], by, 0.9, f.t, eye=eye, jaw=jaw, glint=1.0 if eye >= 1 else 0)
    hills(cv, HORIZON23 + 4, 7, 4.1, '#241c30', '#30263e')
    cv.rect(-12, HORIZON23 + 12, 344, 80, '#1a1424')
    # dust shed by the rising head
    if 0 < rise < 1:
        for j in range(10):
            rr_ = R(900 + j)
            tt = (f.t * 0.8 + rr_()) % 1
            cv.rect(snap(bx + rr_(-40, 40)), snap(HORIZON23 - 2 - tt * 16), 2, 1, '#6a5a6a')
    # the shockwave (from the head, on "boom")
    if kb >= 0:
        ox_, oy_ = bx, by + 10
        for j, (spd, c, wdt) in enumerate(((900, '#f4ecd8', 3), (620, '#c8b8a8', 2), (380, '#8a7a8a', 1))):
            r_ = kb * spd
            if r_ < 420:
                cv.ring(ox_, oy_, r_, c, wdt)
        # ground dust wall racing outward
        for side in (-1, 1):
            dxw = kb * 500 * side
            puff(cv, ox_ + dxw, HORIZON23 + 8, min(kb, 0.5) * 0.9, 700 + side, n=10, c='#8a7a8a', c2='#5a4a60', spread=24, life=0.6)
    # Claude, bust at left, cupping her ear toward the sound
    cupped = f.t >= t_hear
    blown = kb > 0.1
    arm = (('arms_front', True), ('arm_n', ((-4, -50), (-9, -56), (-6, -62)))) if cupped else None
    eyes = 'calm'
    if f.t >= t_bas:
        eyes = 'side'
    if kb >= 0.06:
        eyes = 'wide'
    mouth = 'o' if kb >= 0.06 else 'none'
    cb = bust('claude', 'Q', eyes, mouth, pose_key=arm, bottom=-24)
    cv.blit(cb, 76, 118)
    # the thump
    if kb >= 0:
        f.shake = (math.sin(kb * 80) * 3 * (1 - clamp(kb / 0.35)), math.cos(kb * 63) * 2 * (1 - clamp(kb / 0.35)))
        f.flash = 0.35 * pulse(kb, 0.08)
    f.cam['zoom'] = 1.0 + 0.03 * ease_io(f.u)


# ================================================================ 24 NVDA to the moon
CANDLE_N = 8
C24 = dict(x0=46, dx=22, top0=250, dy=18, moon=(268, 102, 40))
GREEN = ['#0f3a24', '#1f7a3e', '#3fbf6a', '#8ff09a']
RED = ['#3a1418', '#8a2a30', '#d0505a']


def candle_top(j):
    return C24['top0'] - C24['dy'] * j


def s24(f):
    cv = f.cv
    t0 = song.beat(137)                    # "NVDA"
    t_to = wt('NVDA', 'to')
    t_moon = wt('NVDA', 'moon')
    pops = [t0 + j * SIX for j in range(CANDLE_N)]
    # ChatGPT's path: steps onto each candle as it pops, then leaps to the moon
    mx, my, mr = C24['moon']
    t_leap = pops[-1] + 0.1
    if f.t < pops[0]:
        k = (f.t - f.shot.start) / (pops[0] - f.shot.start)
        px_, py_ = lerp(C24['x0'] - 30, C24['x0'] - 8, k), 280
        mode = 'run'
    elif f.t < t_leap:
        j = min(CANDLE_N - 1, int((f.t - pops[0]) / SIX))
        u = (f.t - pops[0]) / SIX - j
        xa, xb = C24['x0'] + C24['dx'] * j - 8, C24['x0'] + C24['dx'] * (j + 1) - 8
        ya = candle_top(j)
        yb = candle_top(min(CANDLE_N - 1, j + 1))
        if j >= CANDLE_N - 1:
            xb, yb = xa + 6, ya
        px_ = lerp(xa, xb, u)
        py_ = lerp(ya, yb, ease_out(u)) - 6 * math.sin(u * math.pi)
        if j == 0 and u < 0:
            py_ = 280
        mode = 'run'
    elif f.t < t_moon:
        u = (f.t - t_leap) / (t_moon - t_leap)
        xa, ya = C24['x0'] + C24['dx'] * (CANDLE_N - 1) - 2, candle_top(CANDLE_N - 1)
        xb, yb = mx, my - mr + 1
        px_ = lerp(xa, xb, u)
        py_ = lerp(ya, yb, u) - 70 * math.sin(u * math.pi)
        mode = 'leap'
    else:
        px_, py_ = mx, my - mr + 1
        mode = 'land'
    # camera follows her (world -> view), clamped
    camx = clamp(px_ + 20, 160, 220)
    camy = clamp(py_ - 34, 20, 200)
    ox, oy = snap(camx - 160), snap(camy - 90)
    fx, fy = camx - 160 - ox, camy - 90 - oy
    # sky
    cv.fill('#070a14')
    dgrad(cv, -12, -12, 344, 204, ['#070a14', '#0b1224', '#101a30'], phase=0)
    stars(cv, 24, 60, f.t, -12, -12, 344, 204, drift=(0, 0))
    # chart grid (scrolls with the world)
    for x in range(-(ox % 20) - 20, 340, 20):
        cv.rect(x, -12, 1, 204, '#0f1a2a')
    for y in range(-(oy % 20) - 20, 200, 20):
        cv.rect(-12, y, 344, 1, '#0f1a2a')
    # moon
    moon(cv, mx - ox, my - oy, mr)
    cv.ring(mx - ox, my - oy, mr, '#cbbf9f', 1)
    # base of the chart: a few small candles before the run (mixed)
    base_y = 282 - oy
    cv.rect(-12, base_y, 344, 1, '#2a3a4a')
    for i, (o, c_, col) in enumerate(((270, 266, 'g'), (266, 271, 'r'), (271, 262, 'g'), (262, 268, 'r'), (268, 258, 'g'))):
        x = -60 + i * 12 + 30
        lo, hi = min(o, c_), max(o, c_)
        pal = GREEN if col == 'g' else RED
        cv.rect(x + 3 - ox, lo - 4 - oy, 1, hi - lo + 8, pal[1])
        cv.rect(x - ox, lo - oy, 7, max(2, hi - lo), pal[2])
    # the staircase of green candles
    for j in range(CANDLE_N):
        k = f.t - pops[j]
        if k < 0:
            continue
        x = C24['x0'] + C24['dx'] * j - ox
        top = candle_top(j)
        opn = candle_top(j - 1) + 4 if j > 0 else 262
        grow = ease_out(k / 0.06)
        ytop = lerp(opn, top, grow)
        wick_hi = ytop - 6 - (j % 3) * 2
        cv.rect(x + 6, wick_hi - oy, 2, opn + 10 - wick_hi, GREEN[1])
        cv.rect(x - 1, ytop - oy, 16, opn - ytop + 1, GREEN[0])
        cv.rect(x, ytop - oy, 14, opn - ytop, GREEN[2])
        cv.rect(x, ytop - oy, 14, 1, GREEN[3])
        cv.rect(x + 11, ytop + 1 - oy, 2, max(0, opn - ytop - 1), GREEN[1])
        if k < 0.08:
            cv.rect(x - 2, ytop - 1 - oy, 18, 2, '#e9fff0')
    # ChatGPT
    sx, sy = px_ - ox, py_ - oy
    if mode == 'run':
        p = PO.run(f.step(14), 'gpt', eyes='sharp', mouth='grin')
        cv.blit(render('gpt', p), sx, sy)
    elif mode == 'leap':
        u = (f.t - t_leap) / (t_moon - t_leap)
        p = make_pose('P', eyes='happy', mouth='grin', hair=-4, bob=-1, lean=2, arms_front=True,
                      arm_n=[(0, -50), (4, -57), (8, -63)], arm_f=[(1, -50), (6, -56), (11, -61)],
                      leg_n=[(0, -35), (8, -27), (4, -14)], leg_f=[(1, -35), (-6, -24), (-14, -18)],
                      tail=[(-3, -35), (-10, -31), (-17, -30), (-24, -32), (-31, -35), (-38, -34)])
        cv.blit(render('gpt', p), sx, sy)
        for jj in range(4):
            cv.rect(snap(sx - 30 - jj * 10), snap(sy - 30 + jj * 6), 8, 1, '#8ff09a')
    else:
        k = f.t - t_moon
        if k < 0.1:
            p = make_pose('Q', eyes='happy', mouth='grin', bob=4, lean=1,
                          leg_n=[(-2, -31), (-6, -18), (-5, -3)], leg_f=[(3, -31), (8, -18), (6, -3)])
        else:
            p = PO.point('gpt', eyes='sharp', mouth='grin')
            p['arm_f'] = [(5, -50), (8, -57), (10, -64)]
        cv.blit(render('gpt', p), sx, sy)
        puff(cv, sx, sy, k, 24, n=10, c='#f4ecd8', c2='#cbbf9f', spread=22)
        if k < 0.07:
            f.shake = (0, 1.5)
    # ticker HUD
    if f.t >= wt('NVDA', 'NVDA') - 0.02:
        text_big(cv, 'NVDA', 12, 10, GREEN[3], scale=2, shadow='#0b1224')
        n_up = sum(1 for p_ in pops if f.t >= p_)
        pct = [0, 8, 19, 35, 58, 97, 160, 260, 420][n_up]
        if mode != 'run':
            pct = 420 + int(max(0.0, f.t - t_leap) * 2000)
        s = f"+{pct}%"
        cv.poly([(56, 20), (60, 13), (64, 20)], GREEN[2])
        text_big(cv, s, 68, 13, GREEN[2], scale=1)
    f.cam['x'] = 160 + fx
    f.cam['y'] = 90 + fy


# ================================================================ 25 the Omega Point, COMING SOON
OMEGA = (206, 46)
HOR25 = 150


@lru_cache(maxsize=2)
def star_field():
    r = R(250)
    out = []
    for i in range(170):
        x, y = r(-12, 332), r(-12, 150)
        d = math.hypot(x - OMEGA[0], y - OMEGA[1])
        out.append((x, y, d, r(0, 0.35), r.i(0, 3)))
    return out


def omega_burst(cv, x, y, s, t):
    """A pixel starburst: diamond core + 8 rays (s = size)."""
    if s <= 0:
        return
    for i in range(8):
        a = i * math.pi / 4 + (0.0 if i % 2 == 0 else 0.0)
        L = s * (2.2 if i % 2 == 0 else 1.2) * (1 + 0.15 * math.sin(t * 20 + i))
        cv.line(x, y, x + math.cos(a) * L, y + math.sin(a) * L, '#fff6c0' if i % 2 == 0 else '#f2cd5a')
    cv.poly([(x - s * 0.5, y), (x, y - s * 0.5), (x + s * 0.5, y), (x, y + s * 0.5)], '#ffffff')
    cv.circle(x, y, max(1, s * 0.25), '#ffffff')


def s25(f):
    cv = f.cv
    t_om = wt('The Omega', 'Omega')
    t_pt = wt('The Omega', "Point's")
    t_com = wt('The Omega', 'coming')
    t_soon = wt('The Omega', 'soon')
    cv.fill('#05060c')
    dgrad(cv, -12, -12, 344, 175, ['#05060c', '#080a16', '#0c1022'])
    ox, oy = OMEGA
    # stars stream into the point after "Omega"
    ks = f.t - t_om
    absorbed = 0
    for (x, y, d, dl, lv) in star_field():
        col = ('#6a7fb4', '#c8d4f0', '#ffffff')[lv]
        if ks <= dl:
            cv.px(snap(x), snap(y), col)
            continue
        tt = ks - dl
        # accelerate inward; farther stars take longer
        prog = clamp((tt * tt) * 900 / max(20.0, d))
        if prog >= 1:
            absorbed += 1
            continue
        px1 = lerp(x, ox, prog)
        py1 = lerp(y, oy, prog)
        prog0 = clamp(((tt - 0.05) ** 2 if tt > 0.05 else 0) * 900 / max(20.0, d))
        px0 = lerp(x, ox, prog0)
        py0 = lerp(y, oy, prog0)
        cv.line(px0, py0, px1, py1, col)
    # the point itself
    s = 0.0
    if f.t >= t_om:
        s = 1.5 + absorbed * 0.03
    if f.t >= t_pt:
        s += 5 * pulse(f.t - t_pt, 0.4) + 2
    if s > 0:
        rings = int(s * 1.5)
        for i in range(2):
            rr = s * 2.8 + i * 4 + (f.t * 20) % 4
            dm = int(rr)
        omega_burst(cv, ox, oy, s, f.t)
    # the marquee hangs in space, lights up on "coming"
    mw, mh = 122, 28
    sway = math.sin(f.t * 1.7) * 1.0
    mx0, my0 = 146 + sway, 88
    cv.line(mx0 + 14, -12, mx0 + 14, my0, '#3a3a4a')
    cv.line(mx0 + mw - 15, -12, mx0 + mw - 15, my0, '#3a3a4a')
    kc = f.t - t_com
    on = clamp(kc / 0.25) if kc > 0 else 0.0
    marquee(cv, snap(mx0), my0, mw, mh, 'COMING SOON', t=f.t, scale=2, on=on, seed=25)
    if kc < 0:
        dither_overlay(cv, 0.6, '#05060c', snap(mx0), my0, mw, mh)
    # the moon's edge in the foreground, the two sitting on it, backs to us
    pts = [(-12, 200)]
    for x in range(-12, 340, 4):
        pts.append((x, HOR25 + ((x - 90) / 60.0) ** 2 * 1.2))
    pts.append((340, 200))
    # characters (drawn first; the moon's limb hides their legs)
    lean_hair = -2 if f.t < t_om else -4
    cp = make_pose('B', sit=True, hair=4 if f.t > t_om else 1)
    gp = make_pose('B', sit=True)
    cv.blit(render('claude', cp), 74, HOR25 + 33)
    cv.blit(render('gpt', gp), 112, HOR25 + 33)
    cv.poly(pts, '#cbbf9f')
    cv.lines(pts[1:-1], '#f4ecd8')
    for (x, y, r_) in ((20, 160, 5), (170, 166, 7), (250, 175, 9), (300, 162, 3)):
        cv.circle(x, y, r_, '#b4a784')
    # ChatGPT's tail curls on the surface beside her
    tl = [(122, HOR25 + 2), (130, HOR25 + 5), (138, HOR25 + 4), (144, HOR25 + 1)]
    cv.lines(tl, G['o'], 3)
    cv.lines(tl, G['z'], 1)
    cv.poly([(144, HOR25 - 1), (150, HOR25 - 4), (148, HOR25 + 2)], G['y'])
    f.cam['zoom'] = 1.0 + 0.05 * ease_io(f.u)
    f.cam['x'] = 160 + 10 * ease_io(f.u)
    f.cam['y'] = 90 - 6 * ease_io(f.u)


# ================================================================ 26 one E thirty flops a second
TILE_W, TILE_H, PITCH = 22, 32, 24
BOARD_Y = 62
X1 = 40                              # world x of the "1"


def tile_x(i):
    return X1 + i * PITCH


def digit_tile(cv, x, y, ch, lit=True, squash=0):
    cv.rect(x - 1, y - 1, TILE_W + 2, TILE_H + 2, '#050608')
    cv.rect(x, y + squash, TILE_W, TILE_H - squash, '#181a22')
    cv.rect(x, y + squash, TILE_W, 1, '#2a2d38')
    cv.rect(x, y + TILE_H // 2, TILE_W, 1, '#0b0c10')     # the flap split
    text_big(cv, ch, x + TILE_W // 2 + (1 if ch == '1' else 0), y + 6 + squash, '#fff2b0' if lit else '#6a5a30', scale=4,
             align='center')


def s26(f):
    cv = f.cv
    t_one = wt('One E', 'One')
    t_yeah = 68.24
    b_one = song.beat(145)
    t_30, t_sec = wt('One E', 'thirty'), wt('One E', 'second')
    zeros = [t_30 + (k + 1) * (t_sec - t_30) / 30 for k in range(30)]
    nz = sum(1 for z in zeros if f.t >= z)
    lead = tile_x(nz)
    # camera: follows the leading digit
    camx = max(160.0, lead + TILE_W / 2 - 80)
    ox = snap(camx - 160)
    fx = camx - 160 - ox
    cv.fill('#07080e')
    dgrad(cv, -12, -12, 344, 204, ['#07080e', '#0c0e1a', '#121428'])
    # parallax: distant horizontal light streaks
    for i in range(18):
        rr_ = R(2600 + i)
        y = rr_(-10, 190)
        x = (rr_(0, 700) - ox * 0.4) % 380 - 30
        cv.rect(snap(x), snap(y), snap(rr_(4, 20)), 1, '#1a1e34')
    burst = f.t >= t_yeah
    kb = f.t - t_yeah
    # board housing: runs from before the 1 to the end cap (which gets shoved along), bursts on "yeah"
    cap_x = tile_x(nz) + TILE_W + 4 if not burst else tile_x(18) + TILE_W + 4
    hx0 = X1 - 34 - ox
    hx1 = cap_x - ox
    cv.rect(hx0, BOARD_Y - 12, hx1 - hx0, TILE_H + 24, '#2a1c14')
    cv.rect(hx0 + 2, BOARD_Y - 10, hx1 - hx0 - 4, TILE_H + 20, '#12131a')
    for x in range(hx0 + 3, hx1 - 2, 4):
        on = (x + ox + int(f.t * 16)) % 12 < 8
        cv.px(x, BOARD_Y - 11, '#fff0a8' if on else '#5a3a20')
        cv.px(x, BOARD_Y + TILE_H + 10, '#fff0a8' if on else '#5a3a20')
    cv.text('FLOP/S', X1 - 30 - ox, BOARD_Y + 13, '#c9a45a', font='3')
    # the digits
    k1 = f.t - t_one
    if k1 >= 0 or f.t >= b_one:
        drop = 1 - ease_in(clamp(k1 / 0.05)) if k1 >= 0 else 1
        digit_tile(cv, tile_x(0) - ox, snap(BOARD_Y - 60 * drop), '1', squash=1 if 0 <= k1 - 0.05 < 0.05 else 0)
    for k in range(nz + 1):
        if k >= 30:
            break
        z = zeros[k]
        kk = f.t - z
        if kk < -0.05:
            continue
        drop = 1 - ease_in(clamp((kk + 0.05) / 0.05))
        x = tile_x(k + 1) - ox
        y = snap(BOARD_Y - 70 * drop)
        sq = 1 if 0 <= kk < 0.04 else 0
        digit_tile(cv, x, y, '0', squash=sq)
        if 0 <= kk < 0.3:
            puff(cv, x + TILE_W // 2, BOARD_Y + TILE_H + 4, kk, 2600 + k, n=5, c='#8a7a6a', c2='#4a3e3a', spread=14, life=0.3)
    # end cap (pushed along), bursts off on "yeah"
    if not burst:
        cv.rect(hx1 - 4, BOARD_Y - 14, 10, TILE_H + 28, '#8a1c24')
        cv.rect(hx1 - 3, BOARD_Y - 13, 8, TILE_H + 26, '#c8433f')
    else:
        ang = kb * 12
        cxp, cyp = hx1 + kb * 300, BOARD_Y + 16 - kb * 260 + kb * kb * 400
        pts = [(cxp + math.cos(ang + a) * 20, cyp + math.sin(ang + a) * 20) for a in (0.2, math.pi - 0.2, math.pi + 0.2, -0.2)]
        cv.poly(pts, '#c8433f')
        if kb < 0.5:
            for i in range(6):
                sparks_bolt(cv, hx1, BOARD_Y + 16, hx1 + 30 + i * 8, BOARD_Y - 30 + i * 16, seed=int(f.t * 30) + i,
                            c='#fff6c0', c2='#f2c24a', jag=4, segs=5)
        confetti(cv, kb, 2680, 30, (hx1, BOARD_Y + 16), spread=80, speed=320, grav=200,
                 colors=('#fff2b0', '#f2c24a', '#e8744a', '#fff6c0'))
        # flying spare digits
        for i in range(6):
            rr_ = R(2700 + i)
            vx, vy = rr_(80, 260), rr_(-260, -60)
            dx_, dy_ = hx1 + vx * kb, BOARD_Y + 10 + vy * kb + 300 * kb * kb
            text_big(cv, rr_.choice('0123456789'), snap(dx_), snap(dy_), '#fff2b0', scale=3)
    # exponent counter HUD
    if f.t >= wt('One E', 'E') - 0.02:
        s = f"1E{nz}"
        text_big(cv, s, 12, 12, '#fff2b0', scale=2, shadow='#2a1c14')
    f.cam['x'] = 160 + fx
    f.cam['y'] = 90
    if nz > 0 and f.t - zeros[nz - 1] < 0.04:
        f.shake = (0, 0.7)
    if burst and kb < 0.25:
        f.shake = (math.sin(kb * 90) * 2.5, math.cos(kb * 70) * 2)
        f.flash = 0.4 * pulse(kb, 0.08)


SHOTS = [
    Shot('22_knob2', 59.10, 0, s22),
    Shot('23_basilisk', 60.62, 0, s23),
    Shot('24_moon', 62.54, 0, s24),
    Shot('25_omega', 64.06, 0, s25),
    Shot('26_flops', 66.18, 0, s26),
]
