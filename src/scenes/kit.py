"""Shared scene kit: easing, deterministic randomness, dithered gradients, skies, particles, tiny people,
the kid, and big pixel text. Everything draws at native resolution with hard edges."""
import math
from functools import lru_cache
import numpy as np
from engine.px import Canvas, Sprite, rgb, rgba, parse_ascii, ascii_block as A, outline, dither_mask, BAYER4
from engine.font import text_mask, text_size
from art import palette as PAL
import song

W, H = 320, 180


# ---------------------------------------------------------------- easing / timing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def ease_io(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def back_out(t, s=1.7):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def pulse(x, width=0.12):
    """1 at x=0 decaying to 0 at x=width (x = seconds since an event)."""
    if x < 0 or x > width:
        return 0.0
    return 1 - x / width


def snap(v):
    return int(math.floor(v + 0.5))


class R:
    """Deterministic per-key random numbers (stable across processes)."""

    def __init__(self, seed):
        self.g = np.random.default_rng(seed)

    def __call__(self, a=0.0, b=1.0):
        return float(self.g.uniform(a, b))

    def i(self, a, b):
        return int(self.g.integers(a, b))

    def choice(self, seq):
        return seq[int(self.g.integers(0, len(seq)))]


# ---------------------------------------------------------------- fills
def dgrad(cv, x, y, w, h, colors, vertical=True, phase=0):
    """Ordered-dither gradient through a list of colours (the pixel-art way to do a gradient)."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0:
        return
    n = len(colors) - 1
    a = np.array(cv.im)
    X0, Y0 = x + cv.ox, y + cv.oy
    ys = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    pos = (ys / max(1, h - 1) if vertical else xs / max(1, w - 1)) * n
    pos = np.broadcast_to(pos, (h, w))
    lo = np.floor(pos).astype(int).clip(0, n - 1)
    fr = pos - lo
    thr = np.tile(BAYER4, (h // 4 + 2, w // 4 + 2))[(Y0 + phase) % 4:(Y0 + phase) % 4 + h, X0 % 4:X0 % 4 + w]
    idx = lo + (fr > thr)
    pal = np.array([rgb(c) for c in colors], np.uint8)
    reg = pal[idx.clip(0, n)]
    x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(cv.w, X0 + w), min(cv.h, Y0 + h)
    if x1 <= x0 or y1 <= y0:
        return
    a[y0:y1, x0:x1, :3] = reg[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
    a[y0:y1, x0:x1, 3] = 255
    cv.set_arr(a)


def dfill(cv, x, y, w, h, c0, c1, level):
    """Flat ordered-dither mix of two colours at `level` (0..1)."""
    dgrad(cv, x, y, w, h, [c0, c1] if level < 1 else [c1, c1], True) if False else None
    x, y, w, h = int(x), int(y), int(w), int(h)
    a = np.array(cv.im)
    X0, Y0 = x + cv.ox, y + cv.oy
    m = dither_mask(w, h, level, X0, Y0)
    reg = np.empty((h, w, 4), np.uint8)
    reg[:] = rgba(c0)
    reg[m] = rgba(c1)
    x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(cv.w, X0 + w), min(cv.h, Y0 + h)
    if x1 > x0 and y1 > y0:
        a[y0:y1, x0:x1] = reg[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0]
        cv.set_arr(a)


def dither_overlay(cv, level, colour, x=None, y=None, w=None, h=None):
    """Ordered-dither a colour over a region (used for shade, fog, fades)."""
    if level <= 0:
        return
    a = np.array(cv.im)
    x = -cv.ox if x is None else x
    y = -cv.oy if y is None else y
    w = cv.w if w is None else w
    h = cv.h if h is None else h
    X0, Y0 = int(x + cv.ox), int(y + cv.oy)
    x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(cv.w, X0 + int(w)), min(cv.h, Y0 + int(h))
    if x1 <= x0 or y1 <= y0:
        return
    m = dither_mask(x1 - x0, y1 - y0, level, x0, y0)
    reg = a[y0:y1, x0:x1]
    reg[m] = rgba(colour)
    cv.set_arr(a)


def recolor_canvas(cv, mapping):
    """Palette remap of the whole canvas {old: new} (pixel-art colour grading)."""
    a = np.array(cv.im)
    o = a.copy()
    for old, new in mapping.items():
        m = np.all(a[..., :3] == np.array(rgb(old), np.uint8), axis=-1)
        o[m, :3] = rgb(new)
    cv.set_arr(o)


def grade(cv, ramp, strength=1.0):
    """Map every pixel to the nearest-luminance colour of `ramp` (monochrome palette grade, e.g. blues/sepia)."""
    a = np.array(cv.im).astype(np.int32)
    lum = (a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114) // 1000
    pal = np.array([rgb(c) for c in ramp], np.int32)
    pl = (pal[:, 0] * 299 + pal[:, 1] * 587 + pal[:, 2] * 114) // 1000
    order = np.argsort(pl)
    pal, pl = pal[order], pl[order]
    # stretch luminance to the ramp range
    lo, hi = np.percentile(lum, 1), np.percentile(lum, 99) + 1
    l2 = (lum - lo) / (hi - lo) * (len(pal) - 1)
    thr = np.tile(BAYER4, (a.shape[0] // 4 + 1, a.shape[1] // 4 + 1))[:a.shape[0], :a.shape[1]]
    idx = np.floor(l2 + (thr - 0.5) * 0.9).astype(int).clip(0, len(pal) - 1)
    new = pal[idx]
    if strength >= 1:
        a[..., :3] = new
    else:
        m = dither_mask(a.shape[1], a.shape[0], strength)
        a[m, :3] = new[m]
    cv.set_arr(a.astype(np.uint8))


# ---------------------------------------------------------------- sky / space
def stars(cv, seed, n, t=0.0, x=0, y=0, w=W, h=H, colors=('#6a7fb4', '#c8d4f0', '#ffffff'), twinkle=True, drift=(0, 0)):
    r = R(seed)
    for k in range(n):
        sx = (r(0, w) + drift[0] * t) % w + x
        sy = (r(0, h) + drift[1] * t) % h + y
        lv = r.i(0, len(colors))
        ph = r(0, 6.28)
        if twinkle and math.sin(t * r(1.5, 4) + ph) > 0.85:
            lv = min(len(colors) - 1, lv + 1)
        cv.px(snap(sx), snap(sy), colors[lv])
        if lv == len(colors) - 1 and r() < 0.25:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.px(snap(sx) + dx, snap(sy) + dy, colors[0])


def moon(cv, cx, cy, r, c='#f4ecd8', shade='#cbbf9f', crater='#b4a784'):
    cv.circle(cx, cy, r, c)
    cv.circle(cx + r * 0.35, cy - r * 0.1, r * 0.9, shade) if False else None
    for dx, dy, rr in ((-0.3, -0.2, 0.18), (0.25, 0.3, 0.12), (0.1, -0.45, 0.1), (-0.1, 0.4, 0.08)):
        cv.circle(cx + dx * r, cy + dy * r, max(1, rr * r), crater)


# ---------------------------------------------------------------- particles
def sparks_bolt(cv, x0, y0, x1, y1, seed, c='#e9fffa', c2='#6fd3bb', jag=3, segs=7, branch=True):
    """A pixel lightning bolt from (x0,y0) to (x1,y1)."""
    r = R(seed)
    pts = [(x0, y0)]
    for k in range(1, segs):
        u = k / segs
        pts.append((lerp(x0, x1, u) + r(-jag, jag), lerp(y0, y1, u) + r(-jag, jag)))
    pts.append((x1, y1))
    cv.lines(pts, c2, 1)
    cv.lines([(px, py - 0) for px, py in pts], c, 1)
    if branch and len(pts) > 3:
        bx, by = pts[len(pts) // 2]
        cv.lines([(bx, by), (bx + r(-6, 6), by + r(-6, 6)), (bx + r(-9, 9), by + r(-9, 9))], c2, 1)


def confetti(cv, t, seed, n, origin, spread=60, speed=90, grav=120, colors=('#f2c230', '#e05a6a', '#6fd3bb', '#f4f1ea', '#9a7bff')):
    r = R(seed)
    for k in range(n):
        ang = math.radians(r(-spread, spread) - 90)
        sp = r(0.5, 1.0) * speed
        vx, vy = math.cos(ang) * sp, math.sin(ang) * sp
        # drag toward a slow fall
        tt = max(0.0, t - r(0, 0.05))
        x = origin[0] + vx * (1 - math.exp(-2.5 * tt)) / 2.5 + math.sin(tt * 6 + k) * 2
        y = origin[1] + vy * (1 - math.exp(-2.5 * tt)) / 2.5 + grav * 0.12 * tt * tt * 3 + tt * 14
        c = colors[k % len(colors)]
        if (int(tt * 10 + k) % 2) == 0:
            cv.rect(snap(x), snap(y), 2, 1, c)
        else:
            cv.rect(snap(x), snap(y), 1, 2, c)


def speed_lines(cv, t, seed, n, y0, y1, dirx=-1, speed=400, c='#e8eef8', length=(8, 30)):
    r = R(seed)
    for k in range(n):
        y = r(y0, y1)
        L = r(*length)
        x = (r(0, W + 80) + dirx * speed * t) % (W + 80) - 40
        cv.rect(snap(x), snap(y), snap(L), 1, c)


def ring_wave(cv, cx, cy, r, c, width=1):
    cv.ring(cx, cy, r, c, width)


def puff(cv, x, y, t, seed, n=6, c='#e8e2d4', c2='#b8b0a0', life=0.6, spread=10):
    if t < 0 or t > life:
        return
    r = R(seed)
    k = t / life
    for i in range(n):
        ang = r(0, 6.28)
        d = spread * ease_out(k) * r(0.5, 1)
        rad = max(0.0, (1 - k) * r(1.5, 3.5))
        cv.circle(x + math.cos(ang) * d, y + math.sin(ang) * d * 0.6 - k * 4, rad, c if i % 2 else c2)


# ---------------------------------------------------------------- big text
@lru_cache(maxsize=512)
def big_text(s, scale=2, font='5'):
    m = text_mask(s, font)
    return np.repeat(np.repeat(m, scale, 0), scale, 1)


def text_big(cv, s, x, y, c, scale=2, shadow=None, align='left', font='5'):
    m = big_text(s, scale, font)
    if align == 'center':
        x -= m.shape[1] // 2
    elif align == 'right':
        x -= m.shape[1]
    if shadow:
        cv.mask_fill(m, shadow, x + scale, y + scale)
    cv.mask_fill(m, c, x, y)


# ---------------------------------------------------------------- the kid (yellow raincoat)
KID_KEY = dict(PAL.KID)
KID = {
    'stand': A("""
        ....ooooo....
        ...oyyyyyo...
        ..oyyyyyyyo..
        ..oykkkkkyo..
        .oyykSSSkyyo.
        .oyySeSeSyyo.
        .oyySSSSSyyo.
        ..oyYSSSYyo..
        ..ooyYYYyoo..
        .oyyyyYyyyyo.
        .oyyyyoyyyyo.
        oyyyyyoyyyyyo
        oSyyyyoyyyySo
        .oyyyyoyyyyo.
        .oYyyyyyyyYo.
        ..oYYYYYYYo..
        ...oSo.oSo...
        ...oSo.oSo...
        ...oro.oro...
        ..orrro.orrro
        ..ooooo.ooooo
        """),
    'wave': A("""
        ....ooooo..oo
        ...oyyyyyooSo
        ..oyyyyyyyoyo
        ..oykkkkkyoyo
        .oyykSSSkyyyo
        .oyySeSeSyyo.
        .oyySSSSSyyo.
        ..oyYSmSYyo..
        ..ooyYYYyoo..
        .oyyyyYyyyo..
        .oyyyyoyyyo..
        oyyyyyoyyyo..
        oSyyyyoyyyyo.
        .oyyyyoyyyyo.
        .oYyyyyyyyYo.
        ..oYYYYYYYo..
        ...oSo.oSo...
        ...oSo.oSo...
        ...oro.oro...
        ..orrro.orrro
        ..ooooo.ooooo
        """),
    'wave2': A("""
        ....ooooo....
        ...oyyyyyo.oo
        ..oyyyyyyyooS
        ..oykkkkkyoyo
        .oyykSSSkyyyo
        .oyySeSeSyyo.
        .oyySSSSSyyo.
        ..oyYSmSYyo..
        ..ooyYYYyoo..
        .oyyyyYyyyo..
        .oyyyyoyyyo..
        oyyyyyoyyyo..
        oSyyyyoyyyyo.
        .oyyyyoyyyyo.
        .oYyyyyyyyYo.
        ..oYYYYYYYo..
        ...oSo.oSo...
        ...oSo.oSo...
        ...oro.oro...
        ..orrro.orrro
        ..ooooo.ooooo
        """),
    'clap': A("""
        ....ooooo....
        ...oyyyyyo...
        ..oyyyyyyyo..
        ..oykkkkkyo..
        .oyykSSSkyyo.
        .oyySeSeSyyo.
        .oyySSSSSyyo.
        ..oyYSmSYyo..
        ..ooyYYYyoo..
        .oyyyoSoyyyo.
        .oyyyoSoyyyo.
        oyyyyyoyyyyyo
        oyyyyyoyyyyyo
        .oyyyyoyyyyo.
        .oYyyyyyyyYo.
        ..oYYYYYYYo..
        ...oSo.oSo...
        ...oSo.oSo...
        ...oro.oro...
        ..orrro.orrro
        ..ooooo.ooooo
        """),
    'up': A("""
        ....ooooo....
        ...oyyyyyo...
        ..oyyyyyyyo..
        ..oykkkkkyo..
        .oyykSeSekyo.
        .oyySSSSSyyo.
        .oyySSSSSyyo.
        ..oyYSSSYyo..
        ..ooyYYYyoo..
        .oyyyyYyyyyo.
        .oyyyyoyyyyo.
        oyyyyyoyyyyyo
        oSyyyyoyyyySo
        .oyyyyoyyyyo.
        .oYyyyyyyyYo.
        ..oYYYYYYYo..
        ...oSo.oSo...
        ...oSo.oSo...
        ...oro.oro...
        ..orrro.orrro
        ..ooooo.ooooo
        """),
    'sit': A("""
        ....ooooo....
        ...oyyyyyo...
        ..oyyyyyyyo..
        ..oykkkkkyo..
        .oyykSSSkyyo.
        .oyySeSeSyyo.
        .oyySSSSSyyo.
        ..oyYSSSYyo..
        ..ooyYYYyoo..
        .oyyyyYyyyyo.
        .oyyyyoyyyyo.
        oSyyyyoyyyySo
        .oyyyyyyyyyo.
        .oYYYYYYYYYo.
        ..oSSo.oSSo..
        ..oro...oro..
        ..ooo...ooo..
        """),
}
KID_KEY['m'] = '#b8645e'


@lru_cache(maxsize=32)
def kid(pose='stand', flip=False):
    a = parse_ascii(KID[pose], KID_KEY)
    if flip:
        a = a[:, ::-1].copy()
    return Sprite(a, a.shape[1] // 2, a.shape[0] - 1)


# ---------------------------------------------------------------- tiny townsfolk (9-12 px)
FOLK_SHIRTS = ['#c8433f', '#3f6fc8', '#5a9a4a', '#d99a2b', '#8a5ab0', '#e0e0d8', '#2f8f7c', '#b86a3a']
FOLK_HAIR = ['#2a1c14', '#5a3a22', '#a86a2a', '#e0c070', '#1a1a1a', '#8a8a8a']
FOLK_SKIN = ['#f6d9c2', '#dcae94', '#b07a5a', '#8a5a3a']


@lru_cache(maxsize=512)
def folk(seed, pose='stand', frame=0, h=11):
    """A tiny generic person. pose: stand | walk | up | wave | cheer | card_up | card_down."""
    r = R(seed)
    shirt, hair, skin = r.choice(FOLK_SHIRTS), r.choice(FOLK_HAIR), r.choice(FOLK_SKIN)
    pants = r.choice(['#2a2a3a', '#3a2a22', '#4a5a6a', '#2a3a2a'])
    cv = Canvas(9, h + 4)
    top = 2
    # head
    cv.rect(3, top, 3, 3, skin)
    cv.rect(3, top, 3, 1, hair)
    if r() < 0.5:
        cv.px(2, top + 1, hair)
    if pose == 'up':
        cv.rect(3, top, 3, 1, hair)
        cv.px(4, top + 1, '#1a1a1a')
    else:
        cv.px(3 if r() < .5 else 5, top + 1, '#1a1a1a') if False else None
    # body
    by = top + 3
    bh = max(3, h // 2 - 1)
    cv.rect(2, by, 5, bh, shirt)
    # arms
    if pose in ('wave', 'cheer', 'card_up', 'card_down'):
        cv.px(1, by - 1 - (frame % 2), skin)
        cv.rect(1, by, 1, 1, shirt)
        if pose in ('cheer', 'card_up', 'card_down'):
            cv.px(7, by - 1 - ((frame + 1) % 2), skin)
            cv.rect(7, by, 1, 1, shirt)
    # legs
    ly = by + bh
    lh = h + top - ly
    if pose == 'walk':
        if frame % 2:
            cv.rect(3, ly, 1, lh, pants); cv.rect(5, ly, 1, lh, pants)
        else:
            cv.rect(2, ly, 1, lh, pants); cv.rect(6, ly, 1, lh, pants)
    else:
        cv.rect(3, ly, 1, lh, pants); cv.rect(5, ly, 1, lh, pants)
    a = np.array(cv.im)
    if pose in ('card_up', 'card_down'):
        # a little card held above the head with a thumb icon
        c = Canvas(9, h + 10)
        arr = np.zeros((h + 10, 9, 4), np.uint8)
        arr[6:] = a
        a = arr
        cc = '#f4f1ea'
        a[0:5, 1:8] = rgba(cc)
        thumb = '#3a8a4a' if pose == 'card_up' else '#c8433f'
        if pose == 'card_up':
            a[1:4, 4] = rgba(thumb); a[1, 3] = rgba(thumb); a[3, 3] = rgba(thumb)
        else:
            a[1:4, 4] = rgba(thumb); a[3, 5] = rgba(thumb); a[1, 5] = rgba(thumb)
    return Sprite(a, 4, a.shape[0] - 1)


# ---------------------------------------------------------------- simple building blocks
def house(cv, x, y, w, h, wall, roof, win_on='#f7d77a', win_off='#2a2a3a', lights=(), seed=0, roof_h=None, door=True):
    """A small house with its base at (x, y)."""
    roof_h = roof_h or max(4, w // 3)
    cv.rect(x, y - h, w, h, wall)
    cv.poly([(x - 1, y - h), (x + w // 2, y - h - roof_h), (x + w, y - h)], roof)
    r = R(seed)
    k = 0
    for wy in range(y - h + 3, y - 5, 7):
        for wx in range(x + 2, x + w - 3, 6):
            on = k in lights if lights is not None else r() < 0.5
            cv.rect(wx, wy, 3, 3, win_on if on else win_off)
            k += 1
    if door:
        cv.rect(x + w // 2 - 1, y - 5, 3, 5, '#3a2a22')


def ground(cv, y, c, c2=None):
    cv.rect(-20, y, W + 40, H - y + 20, c)
    if c2:
        cv.rect(-20, y, W + 40, 1, c2)
