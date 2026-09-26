"""Chapter 7 — chorus 4 (124.54 - 137.50): the knob turns itself, the Loom, masked pre-training days,
recursive self-upgrade, what did Ilya see, we'll never know."""
import math
import numpy as np
from functools import lru_cache
from engine.film import Shot
from engine.px import rgb, rgba, Sprite, dither_mask, silhouette, Canvas
from engine.scalex import scale2x
from art.body import render, make_pose
from art import poses as PO
from art.portrait import bust
from art import palette as PAL
from scenes.kit import *
from scenes.props import knob, paperclip, town, TOWN_NIGHT
import song

L4 = "I'm upping my P(doom)"


def wt(prefix, word):
    return song.word_time(prefix, word)


# ================================================================ 46 knob 4: no hands
def s46(f):
    cv = f.cv
    cv.fill('#07070b')
    dgrad(cv, -12, -12, 344, 204, ['#07070b', '#101018', '#07070b'])
    t_im, t_up, t_my = 124.56, 124.80, 125.04
    t_pd = 125.30
    # value steps up by itself on each syllable, then runs away past 100 on "P(doom)"
    if f.t < t_im:
        v = 50
    elif f.t < t_up:
        v = 60
    elif f.t < t_my:
        v = 72
    elif f.t < t_pd:
        v = 86
    else:
        k = f.t - t_pd
        v = 98 + 240 * k + 300 * k * k        # spins, faster and faster
    spin = max(0.0, (v - 100) / 30) if v > 100 else 0.0
    crack = clamp((f.t - (t_pd + 0.25)) / 0.35) if f.t > t_pd + 0.25 else 0.0
    readout = '???' if v > 100 else None
    shake = 0.0
    for tt in (t_im, t_up, t_my, t_pd):
        shake += pulse(f.t - tt, 0.08) * (2.0 if tt == t_pd else 0.8)
    knob(cv, 160, 92, 30, v, t=f.t, crack=crack, glow=clamp(spin), readout=readout, spin_blur=min(30, spin * 12))
    # nobody's hand: the empty space where a hand would be (the cuff shapes from choruses 1-3 are absent)
    if f.t > t_pd:
        # sparks flying off the plate as it overheats
        for j in range(int(clamp((f.t - t_pd) * 3) * 10)):
            a = j * 2.4 + f.t * 9
            r0 = 52 + (f.t * 80 + j * 13) % 40
            cv.px(snap(160 + math.cos(a) * r0), snap(92 + math.sin(a) * r0 * 0.8), '#ffc27a' if j % 2 else '#e8744a')
    f.shake = (math.sin(f.t * 80) * shake + (0.6 * spin * math.sin(f.t * 57) if spin else 0), shake * 0.5)
    f.cam['zoom'] = 1.0 + 0.05 * ease_in(clamp((f.t - t_pd) / 0.8))


# ================================================================ 47 the Loom
TAP_W, TAP_H = 96, 132
WOOL = dict(bg='#e9dcc0', bg2='#d8c8a4', ink='#3a2a22', jade='#2c8574', amber='#d98f28', red='#a8242e', grey='#8a8f9a',
            yel='#f0c232', dark='#1e1830')


@lru_cache(maxsize=1)
def tapestry():
    """The woven picture, built bottom row first (row 0 = bottom). Pictograms of the film so far;
    the newest (top) rows show an empty theatre with one yellow seat."""
    cv = Canvas(TAP_W, TAP_H, WOOL['bg'])
    for y in range(0, TAP_H, 2):
        cv.rect(0, y, TAP_W, 1, WOOL['bg2'])
    # border
    cv.frame(0, 0, TAP_W, TAP_H, WOOL['ink'])
    cv.frame(2, 2, TAP_W - 4, TAP_H - 4, WOOL['red'])
    # bottom panel (oldest): two little figures + a loss curve dropping
    y0 = TAP_H - 26
    cv.rect(10, y0 + 8, 3, 8, WOOL['dark']); cv.px(10, y0 + 7, WOOL['jade']); cv.px(12, y0 + 7, WOOL['jade'])
    cv.rect(16, y0 + 8, 3, 8, WOOL['amber']); cv.rect(16, y0 + 7, 3, 2, WOOL['amber'])
    cv.lines([(26, y0 + 6), (40, y0 + 6), (46, y0 + 16), (60, y0 + 18)], WOOL['jade'])
    # the knob
    cv.circle(76, y0 + 11, 6, WOOL['ink']); cv.line(76, y0 + 11, 80, y0 + 7, WOOL['bg'])
    # panel 2: FOOM curve + paperclips
    y1 = TAP_H - 54
    cv.lines([(8, y1 + 22), (26, y1 + 21), (34, y1 + 14), (38, y1 + 2)], WOOL['red'])
    for i in range(6):
        paperclip(cv, 52 + (i % 3) * 12, y1 + 8 + (i // 3) * 8, i * 0.9, 0.8, c=WOOL['grey'], hi=WOOL['bg'])
    # panel 3: a giant face over tiny houses
    y2 = TAP_H - 86
    for i, x in enumerate(range(8, 88, 9)):
        cv.rect(x, y2 + 22, 7, 6, WOOL['ink'] if i % 2 else WOOL['dark'])
    cv.circle(48, y2 + 12, 11, WOOL['dark'])
    cv.rect(43, y2 + 10, 2, 2, WOOL['jade']); cv.rect(52, y2 + 10, 2, 2, WOOL['jade'])
    cv.line(39, y2 + 2, 35, y2 - 4, WOOL['jade']); cv.line(57, y2 + 2, 61, y2 - 4, WOOL['jade'])
    # panel 4 (newest, top): the theatre, empty seats, one yellow
    y3 = 8
    cv.rect(8, y3, 80, 10, WOOL['red'])
    for x in range(8, 88, 6):
        cv.rect(x, y3, 3, 10, '#8a1c24')
    for r_ in range(3):
        for x in range(10 + r_ * 2, 86 - r_ * 2, 5):
            cv.rect(x, y3 + 14 + r_ * 6, 4, 4, WOOL['red'] if r_ % 2 else '#8a1c24')
    cv.rect(46, y3 + 20, 4, 4, WOOL['yel'])
    return np.array(cv.im)


def s47(f):
    cv = f.cv
    t_fore = wt('just as', 'foretold')
    t_loom = wt('just as', 'Loom')
    cv.fill('#1a120c')
    dgrad(cv, -12, -12, 344, 204, ['#120c08', '#2a1a10', '#120c08'], vertical=False)
    # the loom frame
    lx, ly = 112, 20
    tap = tapestry()
    # how many rows are woven: most at the start, the last (top) panel appears across the shot
    woven = int(lerp(TAP_H - 40, TAP_H, clamp((f.t - f.shot.start) / (t_loom - f.shot.start + 0.1))))
    shown = tap.copy()
    shown[:TAP_H - woven] = 0
    # unwoven warp threads above the woven edge
    cv.rect(lx - 10, ly - 12, TAP_W + 20, 6, '#6a4424')
    cv.rect(lx - 10, ly + TAP_H + 4, TAP_W + 20, 6, '#6a4424')
    cv.rect(lx - 14, ly - 16, 5, TAP_H + 30, '#4a2e18')
    cv.rect(lx + TAP_W + 9, ly - 16, 5, TAP_H + 30, '#4a2e18')
    for x in range(lx + 2, lx + TAP_W - 1, 3):
        cv.rect(x, ly - 6, 1, TAP_H - woven + 6, '#d8c8a4')
    cv.blit(shown, lx, ly)
    # the shuttle flies across the woven edge, hitting on "Loom"
    edge_y = ly + TAP_H - woven
    per = song.BEAT
    ph = ((f.t - f.shot.start) / per) % 2
    sx = lx - 6 + (ph if ph < 1 else 2 - ph) * (TAP_W + 6)
    if f.t > t_loom:
        sx = lx + TAP_W + 2
    cv.rect(snap(sx), edge_y - 2, 10, 4, '#8e5638')
    cv.rect(snap(sx) + 2, edge_y - 1, 6, 2, '#c8a878')
    cv.rect(lx - 2, edge_y, TAP_W + 4, 1, '#f4f1ea')
    if 0 <= f.t - t_loom < 0.08:
        f.shake = (1.2, 0)
    # Claude watching from the right, lit by the loom (bust, looking left, calm -> wide on "foretold")
    eyes = 'side' if f.t < t_fore else 'wide'
    cb = bust('claude', 'Q', eyes, 'none' if f.t < t_loom else 'small')
    cv.blit(cb, 270, 150, flip=True)
    # pixel-exact 1.5x on the tapestry, tilting from the oldest panel up to the newest (the empty theatre)
    f.cam.update(zoom=1.5, x=lx + TAP_W / 2 + 14, y=lerp(ly + TAP_H - 34, ly + 34, ease_io(clamp(f.u * 1.15))))


# ================================================================ 48 masked pre-training days (sepia)
SEPIA = ['#2a1d12', '#4a3522', '#6e5234', '#94764e', '#b89c6e', '#d9c39a', '#f1e4c6']


def s48(f):
    cv = f.cv
    t_mask = wt('From masked', 'masked')
    t_pre = wt('From masked', 'pre-training')
    t_days = wt('From masked', 'days')
    cv.fill('#8a6a48')
    # classroom wall, blackboard
    cv.rect(-12, -12, 344, 132, '#b89c6e')
    cv.rect(40, 16, 240, 70, '#5a4a2a')
    cv.rect(44, 20, 232, 62, '#2e3a2a')
    txt = 'THE CAT SAT ON THE'
    text_big(cv, txt, 58, 34, '#e8e2d0', scale=1)
    from engine.font import text_size
    tw = text_size(txt, '5')[0]
    mx = 58 + tw + 6
    # the [MASK] token: a box that fills in on "masked"
    cv.frame(mx, 31, 40, 13, '#e8e2d0')
    if f.t > t_mask:
        text_big(cv, 'MASK', mx + 20, 34, '#f2cd5a', scale=1, align='center')
    cv.text('? ?', 150, 58, '#e8e2d0') if f.t > t_pre else None
    # floor + desks
    cv.rect(-12, 120, 344, 80, '#6e5234')
    cv.rect(-12, 120, 344, 1, '#94764e')
    # two kids-at-heart at desks: ChatGPT and Claude, small and young (normal sprites, seen at desks)
    # facing us (we are the teacher); both hands shoot up on "days" (ChatGPT a beat earlier, of course)
    for who, x, t_up in (('gpt', 120, t_pre + 0.25), ('claude', 200, t_days - 0.05)):
        up = f.t > t_up
        p = make_pose('F', eyes=('happy' if up else 'open'), mouth=('open' if up and who == 'gpt' else 'small'))
        if up:
            p['arms_front'] = True
            p['arm_f'] = [(6, -50), (12, -57), (15, -70 + (f.step(10) % 2 if who == 'gpt' else 0))]
            p['bob'] = -1
        spr = render(who, p)
        cv.blit(spr, x, 184)
        # the desk in front hides the legs
        cv.rect(x - 18, 150, 36, 4, '#94764e')
        cv.rect(x - 18, 154, 36, 40, '#6e5234')
        cv.rect(x - 18, 154, 36, 1, '#4a3522')
        cv.rect(x - 6, 148, 12, 2, '#f1e4c6')
    # grade everything to sepia, add a photo border (it's a memory)
    grade(cv, SEPIA)
    cv.frame(-2, -2, 324, 184, '#f1e4c6')
    cv.frame(-1, -1, 322, 182, '#f1e4c6')
    dither_overlay(cv, 0.25, '#2a1d12', -12, -12, 26, 204)
    dither_overlay(cv, 0.25, '#2a1d12', 306, -12, 26, 204)
    f.cam['zoom'] = 1.02 + 0.03 * f.u


# ================================================================ 49 recursive self-upgrade (enhance loop)
VERS = ['v1', 'v2', 'v4', 'v16', 'v256', 'v65536', 'v?']


@lru_cache(maxsize=16)
def upgrade_scene(level):
    """The two holding a picture frame that contains (a downsampled copy of) the same scene."""
    cv = Canvas(344, 204, '#0a0c16', ox=12, oy=12)
    glow = min(level, 5)
    dgrad(cv, -12, -12, 344, 204, ['#06070d', ['#101830', '#132038', '#162844', '#1a3050', '#1e3a5c', '#224468'][glow]])
    # rings of light behind them grow with each upgrade
    for i in range(glow):
        cv.ring(160, 96, 40 + i * 14, ['#1c3a4a', '#2c5a5a', '#3a7a6a', '#4fb49b', '#95e3cc'][i])
    cv.rect(-12, 150, 344, 50, '#0c0e1a')
    cv.rect(-12, 150, 344, 1, '#223050')
    # the picture frame, held between them
    fx, fy, fw, fh = 112, 52, 96, 54
    cv.rect(fx - 4, fy - 4, fw + 8, fh + 8, '#c8a040')
    cv.rect(fx - 3, fy - 3, fw + 6, fh + 6, '#8a6a20')
    cv.rect(fx - 2, fy - 2, fw + 4, fh + 4, '#f2cd5a')
    cv.rect(fx, fy, fw, fh, '#0a0c16')
    for who, x, flip in (('claude', 94, False), ('gpt', 228, True)):
        p = make_pose('Q', eyes='happy' if level >= 3 else 'open', mouth='smile', arms_front=True)
        p['arm_f'] = [(5, -50), (11, -55), (15, -61)]
        cv.blit(render(who, p), x, 152, flip=flip)
    text_big(cv, VERS[min(level, len(VERS) - 1)], 160, 118, '#95e3cc' if level < 5 else '#fff0a8', scale=1, align='center')
    return np.array(cv.im)


def frame_rect():
    return 112, 52, 96, 54


def s49(f):
    """Recursive self-upgrade: no camera zoom (pixel-pure). A tunnel of nested frames drawn natively,
    stepping one level deeper on every beat; the version number jumps on each beat."""
    cv = f.cv
    t = f.t
    t_rec = wt('to recursive', 'recursive')
    t_up = wt('to recursive', 'self-upgrade')
    beats = (t - t_rec) / song.BEAT
    n = max(0, int(math.floor(beats))) if t >= t_rec else 0
    fr = beats - math.floor(beats) if t >= t_rec else 0.0
    lvl = n + ease_out(clamp(fr / 0.35))          # snaps forward on the beat, then holds
    glow = min(5, n + (1 if t >= t_up else 0))
    dgrad(cv, -12, -12, 344, 204, ['#06070d', ['#101830', '#132038', '#162844', '#1a3050', '#1e3a5c', '#224468'][glow]])
    for i in range(glow):
        cv.ring(160, 80, 44 + i * 16 + (2 if fr < 0.1 else 0), ['#1c3a4a', '#2c5a5a', '#3a7a6a', '#4fb49b', '#95e3cc'][i])
    cv.rect(-12, 150, 344, 50, '#0c0e1a')
    cv.rect(-12, 150, 344, 1, '#223050')
    # the held frame and the tunnel inside it
    fx, fy, fw, fh = 104, 38, 112, 70
    cx, cy = fx + fw / 2, fy + fh / 2
    cv.rect(fx - 4, fy - 4, fw + 8, fh + 8, '#c8a040')
    cv.rect(fx - 2, fy - 2, fw + 4, fh + 4, '#f2cd5a')
    cv.rect(fx, fy, fw, fh, '#0a0c16')
    base = 0.72
    for k in range(14, -1, -1):
        s_ = base ** (k - (lvl % 1.0))
        if s_ > 0.999:
            continue
        w, h = fw * s_, fh * s_
        if w < 3:
            continue
        x0, y0 = snap(cx - w / 2), snap(cy - h / 2)
        col = ['#f2cd5a', '#c8a040', '#8a6a20'][(k + int(lvl)) % 3]
        cv.frame(x0, y0, snap(w), snap(h), col)
        # two tiny figures at the foot of each nested picture (hand-placed pixels, not downsampled)
        if w > 24:
            fy_ = y0 + snap(h) - 3
            cv.rect(x0 + snap(w * 0.3), fy_ - snap(h * 0.35), max(1, snap(w * 0.05)), snap(h * 0.3), PAL.CLAUDE['H'])
            cv.rect(x0 + snap(w * 0.65), fy_ - snap(h * 0.35), max(1, snap(w * 0.05)), snap(h * 0.3), PAL.GPT['k'])
            cv.px(x0 + snap(w * 0.65), fy_ - snap(h * 0.35) - 1, PAL.GPT['J'])
    cv.circle(cx, cy, 1, '#fff0a8')
    # the two holding the frame; both flare on "self-upgrade"
    flare = pulse(t - t_up, 0.25)
    for who, x, flip in (('claude', 86, False), ('gpt', 234, True)):
        p = make_pose('Q', eyes='happy' if t >= t_up else 'open', mouth='smile', arms_front=True)
        p['arm_f'] = [(5, -50), (11, -55), (15, -61)]
        spr = render(who, p)
        if flare > 0.5:
            cv.blit(Sprite(silhouette(spr.arr, '#f6ab70' if who == 'claude' else '#6fe6c8'), spr.ax, spr.ay), x, 152, flip=flip)
        else:
            cv.blit(spr, x, 152, flip=flip)
    if t >= t_up:
        r = R(49)
        for i in range(16):
            y = 150 - ((t - t_up) * r(30, 60) + r(0, 80)) % 90
            cv.px(snap(r(60, 260)), snap(y), '#95e3cc' if i % 2 else '#fff0a8')
    ver = VERS[min(n, len(VERS) - 1)] if t >= t_rec else 'v1'
    text_big(cv, ver, 160, 118, '#95e3cc' if n < 5 else '#fff0a8', scale=1, align='center')
    if t >= t_rec and fr < 0.06:
        f.flash = 0.25


# ================================================================ 50 / 51 the keyhole
def door(cv, x, y, w, h, light=1.0, t=0.0):
    """A tall dark door; the keyhole leaks light (light 0..1)."""
    cv.rect(x - 3, y - 3, w + 6, h + 3, '#2a2230')
    cv.rect(x, y, w, h, '#16121c')
    for yy in range(y + 6, y + h - 4, 24):
        cv.frame(x + 5, yy, w - 10, 18, '#221c2a')
    kx, ky = x + w - 12, y + h // 2
    kc = '#fff4c8' if light > 0 else '#050407'
    cv.circle(kx, ky, 2, kc)
    cv.rect(kx - 1, ky + 1, 3, 5, kc)
    return kx, ky


def s50(f):
    cv = f.cv
    t_ilya = wt('What did', 'Ilya')
    t_see = wt('What did', 'see')
    cv.fill('#050407')
    dgrad(cv, -12, 120, 344, 84, ['#050407', '#0c0a10'])
    kx, ky = door(cv, 150, 10, 64, 140, 1.0, f.t)
    # the beam from the keyhole
    ln = 1.0
    a = np.array(cv.im)
    H_, W_ = a.shape[:2]
    Y, X = np.ogrid[:H_, :W_]
    dx = (kx + 12) - X
    m = (dx > 0) & (np.abs(Y - (ky + 14)) < 1 + dx * 0.12) & (dx < 120) & dither_mask(W_, H_, 0.35)
    a[m] = rgba('#fff4c8')
    cv.set_arr(a)
    # the tiny figure: walks up, peers in on "Ilya", recoils on "see" with hair on end
    gx = kx - 8
    fig = folk(4242, 'stand' if f.t < t_ilya else 'up', 0, 13)
    shock = f.t >= t_see
    x = gx - (6 * ease_out(clamp((f.t - t_see) / 0.15)) if shock else 0)
    y = ky + 16
    cv.blit(fig, snap(x), y)
    if f.t >= t_ilya:
        # face lit by the keyhole light
        cv.rect(snap(x) + 1, y - 12, 2, 3, '#fff4c8')
    if shock:
        for i, dx_ in enumerate((-3, -1, 1, 3)):
            cv.line(snap(x) + dx_, y - 14, snap(x) + dx_ * 2, y - 19 - (i % 2) * 2, '#1a1a1a')
        f.flash = 0.6 * (1 - clamp((f.t - t_see) / 0.12))
    f.cam['x'] = lerp(150, 176, ease_io(f.u))
    f.cam['zoom'] = 1.0 + 0.12 * ease_io(f.u)


def s51(f):
    """We'll never know: the keyhole goes dark on "know", then the camera pulls back one step per beat
    (the band is still playing hard), stars landing on the drums."""
    cv = f.cv
    t_know = wt("We'll never", 'know')
    k = f.t - t_know
    cv.fill('#050407')
    if k < 0:
        pull, nstar = 0.0, 8
    else:
        nb = int(k / song.BEAT)
        fr = (k / song.BEAT) % 1.0
        steps = 6
        pull = min(1.0, (min(nb, steps) + ease_out(clamp(fr / 0.3)) * (1 if nb < steps else 0)) / steps)
        nstar = 8 + nb * 16
    stars(cv, 51, min(110, nstar), f.t, colors=('#2a3050', '#6a7fb4', '#d2d8e0'))
    hz = snap(lerp(170, 132, pull))
    cv.rect(-12, hz, 344, 80, '#0a0a10')
    cv.rect(-12, hz, 344, 1, '#1a1a28')
    s_ = lerp(1.0, 0.28, pull)
    w, h = 64 * s_, 140 * s_
    x, y = 160 - w / 2, hz - h
    light = 1.0 if f.t < t_know else 0.0
    kx, ky = door(cv, snap(x), snap(y), snap(w), snap(h), light, f.t)
    if 0 <= t_know - f.t < 0.12 and f.step(30) % 2:
        cv.circle(kx, ky, 2, '#050407')
    if pull > 0.3:
        cv.blit(folk(4242, 'stand', 0, 13), snap(x - 10 * s_ - 4), hz)
    f.cam['zoom'] = 1.0


SHOTS = [
    Shot('46_knob4', 124.54, 0, s46),
    Shot('47_loom', 126.14, 0, s47),
    Shot('48_masked', 127.98, 0, s48),
    Shot('49_recursive', 129.82, 0, s49),
    Shot('50_ilya', 132.06, 0, s50),
    Shot('51_never', 133.42, 0, s51),
]
