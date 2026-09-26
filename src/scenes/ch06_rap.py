"""Chapter 6 — the rap (110.14 - 124.54): transformers all the way down, STOP/GO, the chinchilla,
the fences, a hundred thousand GPUs, RLHF askew."""
import math
import numpy as np
from functools import lru_cache
from engine.film import Shot
from engine.px import rgb, rgba, Sprite, dither_mask, silhouette, Canvas
from art.body import render, make_pose
from art import poses as PO
from art.portrait import bust
from art import palette as PAL
from scenes.kit import *
from scenes import props
import song


def wt(p, w):
    return song.word_time(p, w)


# ================================================================ 40 transformers all the way down
@lru_cache(maxsize=2)
def block_tile(kind):
    cv = Canvas(132, 34, '#141820')
    cv.rect(0, 0, 132, 34, '#1b1f27')
    cv.frame(0, 0, 132, 34, '#454d5c')
    cv.rect(1, 1, 130, 1, '#687282')
    if kind == 0:
        cv.text('ATTENTION', 6, 4, '#95e3cc', font='3')
        xs = [14 + i * 13 for i in range(9)]
        for i, x in enumerate(xs):
            cv.circle(x, 22, 2, '#4fb49b')
        for i in range(9):
            j = (i * 4 + 3) % 9
            a, b = xs[i], xs[j]
            mid = (a + b) / 2
            cv.lines([(a, 20), (mid, 20 - abs(b - a) * 0.12 - 2), (b, 20)], '#2c8574')
    else:
        cv.text('MLP', 6, 4, '#f2cd5a', font='3')
        for i in range(8):
            cv.rect(14 + i * 14, 16, 8, 10, '#3a2a10')
            cv.rect(14 + i * 14, 16 + (i * 3) % 7, 8, 10 - (i * 3) % 7, '#a0701c')
    return np.array(cv.im)


def s40(f):
    cv = f.cv
    t = f.t
    k = t - f.shot.start
    t_all = wt('"Just', 'all')
    cv.fill('#07090e')
    # side rails of the tower
    speed = 120 + 260 * clamp((t - t_all) / 1.0) + 60 * k
    off = 120 * k + 130 * k * k
    y0 = -((off) % 68) - 20
    for i in range(6):
        y = snap(y0 + i * 34)
        cv.blit(block_tile(i % 2 if (int((off) // 34) + i) % 2 == 0 else (i + 1) % 2), 94, y)
    cv.rect(90, -12, 3, 204, '#2d333f')
    cv.rect(230, -12, 3, 204, '#2d333f')
    # layer counter
    n = 12 + int(off / 34)
    cv.text(f'LAYER {n}', 244, 8, '#687282', font='3')
    for j in range(20):
        yy = (j * 23 - off * 1.5) % 200 - 10
        cv.rect(60 if j % 2 else 262, snap(yy), 1, 10, '#2d333f')
    # ChatGPT diving past
    p = PO.fall(f.step(10), 'gpt')
    p['eyes'], p['mouth'] = 'happy', 'shout'
    cv.blit(render('gpt', p), 160 + math.sin(t * 3) * 6, 120)
    if k < 0.12:
        f.flash = 1 - k / 0.12


# ================================================================ 41 STOP -> GO
def finger(cv, x, y, L=90):
    """A giant fingertip reaching down-left from the top-right."""
    cv.poly([(x, y), (x + 22, y - 8), (x + L, y - L * 0.9), (x + L - 30, y - L * 0.9 - 26)], PAL.GPT['s'])
    cv.poly([(x + 2, y - 2), (x + 20, y - 8), (x + L - 4, y - L * 0.9 + 2), (x + L - 30, y - L * 0.9 - 22)], PAL.GPT['S'])
    cv.poly([(x + 4, y - 6), (x + 12, y - 10), (x + 16, y - 20), (x + 6, y - 18)], '#f8e8e0')
    # coat cuff
    cv.poly([(x + L - 34, y - L * 0.9 - 30), (x + L + 30, y - L * 0.9 - 10), (x + L + 40, y - L), (x + L - 10, y - L - 50)], PAL.GPT['c'])
    cv.line(x + L - 34, y - L * 0.9 - 30, x + L + 30, y - L * 0.9 - 10, PAL.GPT['n'], width=2)


def sign(cv, cx, cy, word, col, squash=1.0):
    r = 22
    w = max(1, r * squash)
    pts = []
    for i in range(8):
        a = math.pi / 8 + i * math.pi / 4
        pts.append((cx + math.cos(a) * w, cy + math.sin(a) * r))
    cv.poly(pts, '#f4f1ea')
    pts2 = [(cx + (x - cx) * 0.86, cy + (y - cy) * 0.86) for x, y in pts]
    cv.poly(pts2, col)
    if squash > 0.6:
        text_big(cv, word, cx, cy - 3, '#f4f1ea', scale=1, align='center')
    cv.rect(cx - 1, cy + r, 3, 60, '#8a8f9a')


def s41(f):
    cv = f.cv
    t = f.t
    t_dis = wt('till you', 'disobey')
    cv.fill('#1a1628')
    dgrad(cv, -12, -12, 344, 204, ['#2a2240', '#1a1628'])
    b = bust('gpt', 'Q', 'sharp' if t > t_dis - 0.3 else 'open', 'smile' if t > t_dis else 'none', bottom=-30)
    cv.blit(b, 214, 118, flip=True)
    k = t - t_dis
    if k < 0:
        sign(cv, 110, 92, 'STOP', '#c8433f')
        finger(cv, 136 + snap(max(0, -k) * 40), 78)
    else:
        sq = abs(math.cos(clamp(k / 0.18) * math.pi))
        flipped = k > 0.09
        sign(cv, 110, 92, 'GO' if flipped else 'STOP', '#3a8a4a' if flipped else '#c8433f', squash=max(0.05, sq))
        finger(cv, 128 - snap(min(1, k * 6) * 4), 72)
    # the tiny hand holding the pole
    cv.rect(106, 150, 9, 6, PAL.KID['S'])
    cv.rect(104, 156, 13, 30, '#3f6fc8')


# ================================================================ 42 post-chinchilla, super-dense
def chinchilla(cv, x, y, s=1.0, blink=False):
    cv.ellipse(x - 16 * s, y - 20 * s, x + 16 * s, y, '#a8a8b0')
    cv.ellipse(x - 13 * s, y - 18 * s, x + 13 * s, y - 2, '#c8c8d0')
    for sx in (-1, 1):
        cv.circle(x + sx * 9 * s, y - 24 * s, 6 * s, '#a8a8b0')
        cv.circle(x + sx * 9 * s, y - 24 * s, 3.5 * s, '#e8b0b8')
    for sx in (-1, 1):
        if blink:
            cv.rect(x + sx * 5 * s - 1, y - 14 * s, 3, 1, '#1a1a1a')
        else:
            cv.circle(x + sx * 5 * s, y - 14 * s, 1.6 * s, '#1a1a1a')
            cv.px(x + sx * 5 * s - 1, y - 15 * s, '#fbf8f2')
    cv.px(x, y - 11 * s, '#e8a0a8')
    for sx in (-1, 1):
        cv.line(x + sx * 3, y - 10 * s, x + sx * 14 * s, y - 12 * s, '#5a5a60')
        cv.line(x + sx * 3, y - 9 * s, x + sx * 14 * s, y - 8 * s, '#5a5a60')
    cv.circle(x + 15 * s, y - 4 * s, 5 * s, '#c8c8d0')


def s42(f):
    cv = f.cv
    t = f.t
    t_sup = wt('Post-Chinchilla', 'super-dense')
    k = t - t_sup
    cv.fill('#20242c')
    cv.rect(-12, -12, 344, 120, '#2a3038')
    sag = 0 if k < 0 else min(10, k * 40)
    # the bench (bends under the marble)
    pts = [(-12, 120)] + [(x, 120 + sag * math.exp(-((x - 160) / 50) ** 2)) for x in range(-12, 340, 4)] + [(340, 200), (-12, 200)]
    cv.poly(pts, '#5a4632')
    cv.lines([(x, 120 + sag * math.exp(-((x - 160) / 50) ** 2)) for x in range(-12, 340, 4)], '#8e6a44', width=2)
    cv.rect(24, 94, 56, 12, '#f4f1ea')
    cv.text('CHINCHILLA', 28, 98, '#2a2440', font='3')
    cv.text('SCALING', 238, 40, '#687282', font='3')
    # press plates close in on "super"
    close = clamp((t - (t_sup - 0.25)) / 0.25)
    gap = lerp(70, 4, ease_in(close))
    cv.rect(160 - gap - 30, 60, 30, 60, '#687282'); cv.rect(160 - gap - 4, 60, 4, 60, '#98a2b0')
    cv.rect(160 + gap, 60, 30, 60, '#687282'); cv.rect(160 + gap, 60, 4, 60, '#98a2b0')
    if k < 0:
        s_ = min(1.0, gap / 30)
        chinchilla(cv, 160, 118, max(0.35, s_) if gap < 30 else 1.0, blink=f.step(3) % 5 == 0)
    else:
        # the super-dense marble, with a tiny face
        cv.circle(160, 116 + sag, 4, '#fff0c8')
        cv.circle(160, 116 + sag, 3, '#f2cd5a')
        cv.px(159, 115 + sag, '#1a1a1a'); cv.px(161, 115 + sag, '#1a1a1a')
        for i in range(10):
            a = i * 0.63 + t * 2
            rr = 8 + (t * 20 + i * 3) % 12
            cv.px(snap(160 + math.cos(a) * rr), snap(116 + sag + math.sin(a) * rr * 0.5), '#ffc27a')
        if k < 0.1:
            f.flash = 0.7
            f.shake = (1.5, 1)


# ================================================================ 43 breaking through each safety fence
FENCE_T = None


def s43(f):
    cv = f.cv
    t = f.t
    hits = [wt('breaking through', 'breaking'), wt('breaking through', 'through'), wt('breaking through', 'safety'),
            wt('breaking through', 'fence')]
    fx = [200, 330, 460, 590]
    # runner position: piecewise linear through the fences at their hit times
    ts = [f.shot.start] + hits + [f.shot.start + 1.92]
    xs = [120] + fx + [700]
    for i in range(len(ts) - 1):
        if ts[i] <= t <= ts[i + 1]:
            gx = lerp(xs[i], xs[i + 1], (t - ts[i]) / (ts[i + 1] - ts[i]))
            break
    else:
        gx = xs[-1]
    cam = gx - 130
    cv.fill('#0c0e16')
    dgrad(cv, -12, -12, 344, 150, ['#07090e', '#141a2a'])
    cv.rect(-12, 150, 344, 50, '#1a1a24')
    cv.rect(-12, 150, 344, 1, '#3a3a50')
    kinds = ['picket', 'chain', 'laser', 'field']
    for i, (x, kind) in enumerate(zip(fx, kinds)):
        sx = x - cam
        broken = t >= hits[i]
        kb = t - hits[i]
        if not broken:
            if kind == 'picket':
                for j in range(-3, 4):
                    cv.rect(sx + j * 6, 120, 4, 30, '#e8e2d4'); cv.poly([(sx + j * 6, 120), (sx + j * 6 + 4, 120), (sx + j * 6 + 2, 116)], '#e8e2d4')
                cv.rect(sx - 20, 128, 44, 2, '#c8c0b0')
            elif kind == 'chain':
                for yy in range(96, 150, 4):
                    for xx in range(-14, 16, 4):
                        cv.px(sx + xx + (yy // 4) % 2 * 2, yy, '#98a2b0')
                cv.rect(sx - 16, 94, 2, 56, '#687282'); cv.rect(sx + 16, 94, 2, 56, '#687282')
            elif kind == 'laser':
                for yy in range(100, 150, 8):
                    cv.rect(sx - 2, yy, 4, 1, '#ff5040')
                cv.rect(sx - 4, 96, 3, 54, '#454d5c'); cv.rect(sx + 3, 96, 3, 54, '#454d5c')
                for yy in range(100, 150, 8):
                    cv.line(sx - 1, yy, sx + 3, yy, '#ff8070')
            else:
                dfill(cv, sx - 3, 60, 8, 90, '#0c0e16', '#6fa8ff', 0.6)
                cv.rect(sx, 60, 1, 90, '#b8d0f0')
        elif kb < 0.7:
            r = R(4300 + i)
            col = ['#e8e2d4', '#98a2b0', '#ff5040', '#6fa8ff'][i]
            for j in range(16):
                vx, vy = r(40, 220), r(-160, -20)
                x = sx + vx * kb
                y = r(100, 145) + vy * kb + 300 * kb * kb
                cv.rect(snap(x), snap(y), 3 if i == 0 else 2, 2 if i == 0 else 1, col)
    spr = render('gpt', PO.run(f.step(16), 'gpt', eyes='sharp', mouth='grin'))
    cv.blit(spr, 130, 152)
    for h in hits:
        kb = t - h
        if 0 <= kb < 0.08:
            f.flash = 0.6 * (1 - kb / 0.08)
            f.shake = (2.0, 1.0)
    speed_lines(cv, t, 43, 12, 20, 150, dirx=-1, speed=700, c='#2a3044', length=(20, 60))


# ================================================================ 44 a hundred thousand GPUs
def s44(f):
    cv = f.cv
    t = f.t
    k = f.u
    s = lerp(1.0, 0.3, ease_io(k))
    cv.fill('#0a0c12')
    dgrad(cv, -12, -12, 344, 40, ['#101828', '#0a0c12'])
    hz = 28
    # rows of racks receding to the horizon, spacing shrinks as we pull back
    rows = int(10 / s) + 4
    for i in range(rows, -1, -1):
        d = i * 10 * s
        y = 180 - d * 1.2
        if y < hz:
            continue
        hgt = max(1, 14 * s * (1 - d / 260))
        cv.rect(-12, snap(y - hgt), 344, max(1, snap(hgt)), '#1b1f27')
        cv.rect(-12, snap(y - hgt), 344, 1, '#2d333f')
        step = max(2, snap(6 * s))
        r = R(4400 + i)
        for x in range(-12 + i % 2 * 2, 332, step):
            if (x + i * 7 + int(t * 8)) % 5 == 0:
                cv.px(x, snap(y - hgt / 2), '#5fe0a0' if (x + i) % 3 else '#f2c24a')
    # the town: a smudge at the top-left edge
    for j in range(6):
        cv.rect(8 + j * 4, hz - 3 - (j % 2), 3, 3 + (j % 2), '#6a4a5a')
        cv.px(9 + j * 4, hz - 2, '#f7d77a')
    cv.text(f'{int(1000 + 99000 * ease_in(k)):,} GPU'.replace(',', ' '), 222, 8, '#98a2b0', font='3')


# ================================================================ 45 RLHF goes askew
@lru_cache(maxsize=1)
def eyes_under():
    cv = Canvas(64, 64, '#07050a')
    r = R(4545)
    for i in range(18):
        x, y = r(4, 60), r(4, 60)
        cv.circle(x, y, 1.5, '#e8e2d0')
        cv.px(x, y, '#12060a')
    return np.array(cv.im)


def s45(f):
    cv = f.cv
    t = f.t
    t_ask = wt('RLHF', 'askew')
    cv.fill('#141828')
    dgrad(cv, -12, -12, 344, 204, ['#1e1a30', '#141828'])
    b = bust('gpt', 'F', 'open', 'none', bottom=-34)
    cv.blit(b, 160, 116)
    # the mask over her face; slips crooked on "askew", revealing darkness with eyes
    k = t - t_ask
    slip = 0.0 if k < 0 else ease_out(clamp(k / 0.25)) * 0.45
    mx, my = 160 + slip * 22, 86 + slip * 10
    if k > 0:
        ey = eyes_under()
        cv.blit(ey[18:46, 18:50], 146, 72)
    props.smiley_mask(cv, mx, my, 22, slip=slip)
    # the crowd with thumbs cards
    r = R(4546)
    for i in range(22):
        pose = 'card_up' if (i + (1 if t > t_ask else 0) * (i % 3 == 0)) % 4 else 'card_down'
        cv.blit(folk(4500 + i, pose, (f.step(4) + i) % 2, 10), 12 + i * 14 + r(-3, 3), 176 + (i % 2) * 3)
    if k > 0:
        rot = 0.16 * ease_out(clamp(k / 0.2))
        if t > song.bar(68) - 0.25:
            rot *= 1 - clamp((t - (song.bar(68) - 0.25)) / 0.2)
        f.cam['rot'] = rot
        if k < 0.08:
            f.shake = (1.5, 0)


SHOTS = [
    Shot('40_transformers', 110.14, 0, s40),
    Shot('41_disobey', 113.34, 0, s41),
    Shot('42_chinchilla', 115.10, 0, s42),
    Shot('43_fences', 117.02, 0, s43),
    Shot('44_gpus', 118.94, 0, s44),
    Shot('45_rlhf', 120.70, 0, s45),
]
