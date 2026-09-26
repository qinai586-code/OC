"""Shared props that recur across chapters. Keep them identical everywhere they appear.

  knob(...)       the P(DOOM) amplifier knob (choruses 1-4)
  town(...)       the little human town (verse 2, chorus 2, chorus 3, rap)
  mascot(...)     the friendly chat mascot / smiley mask (chorus 1, rap)
  marquee(...)    theatre marquee with bulbs ("COMING SOON", ending "P(DOOM) = ?%")
  paperclip(...)  one paperclip; paperclip_field(...) a pile / flood of them
"""
import math
import numpy as np
from engine.px import rgb, rgba, dither_mask
from scenes.kit import *
from art import palette as PAL

# ================================================================= the P(DOOM) knob
KNOB = dict(plate='#1c1e24', plate2='#2a2d35', plate_hi='#3c404b', face='#2a2d35', knob='#101114', knob_hi='#50555f',
            skirt='#9aa0aa', skirt_hi='#e2e6ec', pointer='#f4f1ea', tick='#9aa0aa', hot='#e8744a', led='#ff5040',
            label='#e9e0cc', lcd='#0b1512', lcd_on='#8ff0d4')


def knob_angle(v):
    """Pointer angle (radians, 0 = straight up, clockwise positive) for value v (0-100, may exceed)."""
    return math.radians(-135 + 270 * v / 100.0)


def knob(cv, cx, cy, R, value, t=0.0, plate=True, label=True, crack=0.0, glow=0.0, readout=None, spin_blur=0.0):
    """Draw the knob centred at (cx, cy) with knob radius R (native px). value in percent.
    readout: text for the little LCD (default '{value}%'); pass '' to hide."""
    K = KNOB
    if plate:
        pw, ph = int(R * 4.2), int(R * 4.4)
        x0, y0 = int(cx - pw / 2), int(cy - ph * 0.56)
        cv.rect(x0, y0, pw, ph, K['plate'])
        cv.rect(x0, y0, pw, 1, K['plate_hi'])
        cv.rect(x0, y0, 1, ph, K['plate2'])
        # brushed lines
        for yy in range(y0 + 3, y0 + ph - 2, 3):
            cv.rect(x0 + 2, yy, pw - 4, 1, K['plate2'])
        # screws
        for sx, sy in ((x0 + 4, y0 + 4), (x0 + pw - 5, y0 + 4), (x0 + 4, y0 + ph - 5), (x0 + pw - 5, y0 + ph - 5)):
            cv.rect(sx - 1, sy, 3, 1, K['tick']); cv.rect(sx, sy - 1, 1, 3, K['tick'])
    # dial scale
    rs = R * 1.45
    for i in range(11):
        a = knob_angle(i * 10)
        r0 = rs - (3 if i % 5 == 0 else 1)
        hot = i >= 8
        c = K['hot'] if hot else K['tick']
        x_a, y_a = cx + math.sin(a) * r0, cy - math.cos(a) * r0
        x_b, y_b = cx + math.sin(a) * (rs + 2), cy - math.cos(a) * (rs + 2)
        cv.line(x_a, y_a, x_b, y_b, c)
        if label and i % 2 == 0 and R >= 10:
            s = str(i * 10)
            tx, ty = cx + math.sin(a) * (rs + 8), cy - math.cos(a) * (rs + 8)
            cv.text(s, snap(tx - (len(s) * 4 - 1) / 2), snap(ty - 2), c, font='3')
    # red arc from 80 to 100
    for k in range(20):
        a = knob_angle(80 + k)
        cv.px(snap(cx + math.sin(a) * (rs + 1)), snap(cy - math.cos(a) * (rs + 1)), K['hot'])
    if label:
        txt = 'P(DOOM)'
        if R >= 10:
            text_big(cv, txt, cx, snap(cy - rs - (22 if R >= 10 else 10)), K['label'], scale=1, align='center')
        else:
            cv.text(txt, cx, snap(cy - rs - 8), K['label'], font='3', align='center')
    # skirt with grip notches
    cv.circle(cx, cy, R + 2, K['skirt'])
    for i in range(24):
        a = i / 24 * math.tau + knob_angle(value)
        cv.px(snap(cx + math.sin(a) * (R + 2)), snap(cy - math.cos(a) * (R + 2)), K['plate2'])
    cv.circle(cx - 1, cy - 1, R, K['knob_hi'])
    cv.circle(cx, cy, R, K['knob'])
    cv.circle(cx - R * 0.3, cy - R * 0.3, R * 0.35, '#1c1e24')
    # pointer (with motion smear when spinning)
    angs = [knob_angle(value)]
    if spin_blur > 0:
        angs = [knob_angle(value - spin_blur * k / 3) for k in range(4)]
    for j, a in enumerate(angs):
        c = K['pointer'] if j == 0 else K['tick']
        cv.line(cx + math.sin(a) * R * 0.25, cy - math.cos(a) * R * 0.25, cx + math.sin(a) * (R - 1), cy - math.cos(a) * (R - 1), c,
                width=2 if R >= 12 and j == 0 else 1)
    # LED + LCD readout
    if plate:
        led_on = value >= 50 and (value < 80 or int(t * 6) % 2 == 0)
        cv.rect(snap(cx + R * 1.6), snap(cy + R * 1.5), 2, 2, K['led'] if led_on else '#4a1a18')
        if readout != '':
            s = readout if readout is not None else f"{int(round(value))}%"
            wv = len(s) * 4 + 3
            lx, ly = snap(cx - wv / 2), snap(cy + rs + 5)
            cv.rect(lx, ly, wv, 9, K['lcd'])
            cv.text(s, lx + 2, ly + 2, K['lcd_on'] if value < 80 else K['hot'], font='3')
    if crack > 0:
        r = R * 1.6
        for i, (a0, l0) in enumerate(((0.3, 1.0), (1.9, 0.8), (3.6, 0.9), (5.1, 0.7))):
            if crack * 4 > i:
                pts = [(cx + math.cos(a0) * 3, cy + math.sin(a0) * 3)]
                for k in range(1, 5):
                    rr = r * l0 * k / 4
                    pts.append((cx + math.cos(a0 + 0.25 * math.sin(k * 3 + i)) * rr, cy + math.sin(a0 + 0.25 * math.sin(k * 3 + i)) * rr))
                cv.lines(pts, '#d2d8e0')
    if glow > 0:
        for i in range(int(glow * 12)):
            a = i * 0.52 + t * 3
            rr = R * 1.6 + (i % 3) * 3
            cv.px(snap(cx + math.cos(a) * rr), snap(cy + math.sin(a) * rr), K['hot'])


# ================================================================= the town
TOWN_DUSK = dict(sky=['#2a2250', '#5a3a6a', '#a8586a', '#e88a5a', '#f7c27a'], far='#3a2e52', mid='#4a3656', near='#2e2240',
                 roof='#6a3a48', ground='#221a2e', lamp='#f7d77a', win='#f7d77a', win_off='#1e1830')
TOWN_NIGHT = dict(sky=['#07070d', '#0e1020', '#171b33', '#222849'], far='#141830', mid='#1b2040', near='#10132a',
                  roof='#2a2448', ground='#0c0e1c', lamp='#f7d77a', win='#f2c24a', win_off='#161a30')


def town(cv, t, horizon=130, seed=3, pal=TOWN_DUSK, scale=1.0, lights=0.6, offset=0, sky=True, rows=3, hill=None):
    """A little town skyline whose ground line is at `horizon`. scale shrinks houses (world-shrinks-around-them).
    offset scrolls the near row (parallax: far rows scroll slower)."""
    if sky:
        dgrad(cv, -12, -12, 344, horizon + 12, pal['sky'])
    if hill is not None:
        # rolling hills behind the town
        pts = [(-12, horizon)]
        for x in range(-12, 340, 8):
            pts.append((x, horizon - hill - 10 * math.sin(x * 0.02 + seed) - 6 * math.sin(x * 0.05)))
        pts.append((340, horizon))
        cv.poly(pts, pal['far'])
    for row in range(rows):
        depth = rows - row            # far rows first
        sc = scale * (0.55 + 0.45 * (row / max(1, rows - 1)))
        col = [pal['far'], pal['mid'], pal['near']][min(2, row + (3 - rows))]
        r = R(seed * 31 + row)
        par = 0.3 + 0.7 * row / max(1, rows - 1)
        x = -60 - (offset * par) % 60
        base = horizon - (rows - 1 - row) * 4 * scale
        while x < 340:
            w = r(14, 26) * sc
            h = r(14, 30) * sc
            cv.rect(snap(x), snap(base - h), snap(w), snap(h + 3), col)
            rh = max(2, h * 0.35)
            cv.poly([(snap(x) - 1, snap(base - h)), (snap(x + w / 2), snap(base - h - rh)), (snap(x + w) + 1, snap(base - h))],
                    pal['roof'] if row == rows - 1 else col)
            # windows
            if sc > 0.3:
                ws = max(1, round(2 * sc))
                for wy in range(snap(base - h + 3 * sc), snap(base - 3 * sc), max(3, snap(6 * sc))):
                    for wx in range(snap(x + 3 * sc), snap(x + w - 3 * sc), max(3, snap(6 * sc))):
                        on = r() < lights
                        cv.rect(wx, wy, ws, ws, pal['win'] if on else pal['win_off'])
            x += w + r(1, 5) * sc
    cv.rect(-12, horizon, 344, 200, pal['ground'])


# ================================================================= the mascot (friendly chat bubble) / smiley mask
MASCOT = dict(body='#f4f1ea', shade='#c9c2d8', line='#2a2440', cheek='#f2a9a2', eye='#2a2440')


def mascot(cv, cx, cy, r, t=0.0, wave=True, smile=1.0, slip=0.0):
    """Round speech-bubble mascot with ^_^ eyes. slip (0..1) slides the face askew (the mask slips)."""
    M = MASCOT
    cv.circle(cx, cy, r + 1, M['line'])
    cv.circle(cx, cy, r, M['body'])
    cv.circle(cx + r * 0.25, cy + r * 0.25, r * 0.8, M['body'])
    # tail of the speech bubble
    cv.poly([(cx - r * 0.5, cy + r * 0.7), (cx - r * 0.9, cy + r * 1.3), (cx - r * 0.1, cy + r * 0.9)], M['body'])
    cv.lines([(cx - r * 0.5, cy + r * 0.78), (cx - r * 0.9, cy + r * 1.3), (cx - r * 0.1, cy + r * 0.95)], M['line'])
    # face (slips with `slip`)
    fx, fy = cx + slip * r * 0.35, cy + slip * r * 0.25
    ang = slip * 0.5
    def rot(dx, dy):
        return fx + dx * math.cos(ang) - dy * math.sin(ang), fy + dx * math.sin(ang) + dy * math.cos(ang)
    for s in (-1, 1):
        ex, ey = rot(s * r * 0.35, -r * 0.1)
        cv.lines([(ex - r * 0.14, ey + r * 0.06), (ex, ey - r * 0.08), (ex + r * 0.14, ey + r * 0.06)], M['eye'], width=max(1, int(r / 10)))
        bx, by = rot(s * r * 0.55, r * 0.18)
        cv.rect(snap(bx - r * 0.1), snap(by), max(2, snap(r * 0.18)), max(1, snap(r * 0.06)), M['cheek'])
    # smile
    pts = [rot(r * 0.3 * math.cos(a), r * 0.12 + r * 0.22 * math.sin(a) * smile) for a in np.linspace(0.3, math.pi - 0.3, 8)]
    cv.lines(pts, M['eye'], width=max(1, int(r / 12)))
    if wave:
        k = math.sin(t * 10)
        ax, ay = cx + r * 0.95, cy - r * 0.1
        cv.lines([(ax, ay), (ax + r * 0.35, ay - r * 0.35 - k * r * 0.12)], M['line'], width=max(1, int(r / 8)))
        cv.circle(ax + r * 0.38, ay - r * 0.4 - k * r * 0.12, max(1, r * 0.1), M['body'])


def smiley_mask(cv, cx, cy, r, slip=0.0):
    """Just the mask: a flat disc with ^_^ face, tilted by `slip` (radians-ish)."""
    M = MASCOT
    cv.circle(cx, cy, r + 1, M['line'])
    cv.circle(cx, cy, r, M['body'])
    ang = slip
    def rot(dx, dy):
        return cx + dx * math.cos(ang) - dy * math.sin(ang), cy + dx * math.sin(ang) + dy * math.cos(ang)
    for s in (-1, 1):
        ex, ey = rot(s * r * 0.38, -r * 0.12)
        cv.lines([(ex - r * 0.16, ey + r * 0.07), (ex, ey - r * 0.09), (ex + r * 0.16, ey + r * 0.07)], M['eye'], width=max(1, int(r / 9)))
    pts = [rot(r * 0.34 * math.cos(a), r * 0.14 + r * 0.24 * math.sin(a)) for a in np.linspace(0.3, math.pi - 0.3, 9)]
    cv.lines(pts, M['eye'], width=max(1, int(r / 10)))
    # strap
    cv.lines([rot(-r, 0), rot(-r - 6, -2)], M['line'])
    cv.lines([rot(r, 0), rot(r + 6, -2)], M['line'])


# ================================================================= theatre marquee
def marquee(cv, x, y, w, h, text, t=0.0, scale=2, on=1.0, chase=True, text_col='#1e0f0c', body='#8a1c24', trim='#f2cd5a', bulb='#fff0a8', bulb_off='#5a3a20', seed=0):
    """Bulb-lined marquee sign, top-left (x, y). on (0..1) = fraction of bulbs lit (lights going out)."""
    cv.rect(x, y, w, h, trim)
    cv.rect(x + 2, y + 2, w - 4, h - 4, body)
    cv.rect(x + 5, y + 5, w - 10, h - 10, '#f8f3e6')
    text_big(cv, text, x + w // 2, y + h // 2 - (7 * scale) // 2 + 1, text_col, scale=scale, align='center')
    r = R(seed)
    order = []
    k = 0
    for bx in range(x + 2, x + w - 1, 4):
        order.append((bx, y + 1)); order.append((bx, y + h - 2))
    for by in range(y + 5, y + h - 3, 4):
        order.append((x + 1, by)); order.append((x + w - 2, by))
    n = len(order)
    lit_n = int(round(on * n))
    perm = list(range(n))
    rr = np.random.default_rng(seed).permutation(n)
    for i, (bx, by) in enumerate(order):
        lit = rr[i] < lit_n
        if lit and chase and (i + int(t * 8)) % 3 == 0:
            c = '#f7c27a'
        else:
            c = bulb if lit else bulb_off
        cv.rect(bx, by, 1, 1, c)


# ================================================================= paperclips
CLIP = '#c9d1dc'
CLIP_HI = '#f4f6fa'
CLIP_LO = '#7d8796'


def paperclip(cv, x, y, ang=0.0, s=1.0, c=CLIP, hi=CLIP_HI):
    """A paperclip centred at (x, y), ~10 px long at s=1 (angle in radians)."""
    ca, sa = math.cos(ang), math.sin(ang)
    def P(u, v):
        return x + (u * ca - v * sa) * s, y + (u * sa + v * ca) * s
    pts = [P(-5, 1.5), P(4, 1.5), P(5, 0), P(4, -1.5), P(-4, -1.5), P(-5, -0.5), P(-4, 0.5), P(3, 0.5)]
    cv.lines(pts, c)
    cv.px(*[snap(v) for v in P(4, -1.5)], hi)


def paperclip_field(cv, t, seed, level_y, x0=-12, x1=332, density=0.18, bottom=192, surge=0.0):
    """A heap of paperclips filling everything below level_y (a silvery sea with individual clips on top)."""
    if level_y >= bottom:
        return
    ly = snap(level_y)
    dfill(cv, x0, ly + 3, x1 - x0, bottom - ly, '#5a6474', '#7d8796', 0.35)
    r = R(seed)
    n = int((x1 - x0) * (bottom - ly) * density / 6)
    for i in range(min(n, 900)):
        px_ = r(x0, x1)
        py_ = r(ly, bottom)
        wob = math.sin(t * 3 + i) * surge
        paperclip(cv, px_, py_ + wob, r(0, 6.28), 1.0, c=CLIP if r() < 0.7 else CLIP_LO)
    # the surface line: clips tumbling on top
    for i in range(int((x1 - x0) / 5)):
        px_ = x0 + i * 5 + r(-2, 2)
        py_ = ly + r(-2, 2) + math.sin(t * 5 + i * 0.7) * 1.2
        paperclip(cv, px_, py_, r(0, 6.28) + t * r(-2, 2), 1.0)


# ================================================================= crowd of tiny people
def crowd(cv, t, seed, n, x0, x1, y, pose='stand', h=11, jitter=4, rows=2, flip_frac=0.5, frame_fps=4):
    """n tiny people standing on line y (rows go slightly up and back)."""
    r = R(seed)
    out = []
    for i in range(n):
        row = i % rows
        x = r(x0, x1)
        yy = y - row * 3 + r(-1, 1)
        fr = (int(t * frame_fps) + i) % 2
        spr = folk(seed * 1000 + i, pose, fr, h)
        cv.blit(spr, snap(x), snap(yy), flip=r() < flip_frac)
        out.append((x, yy))
    return out
