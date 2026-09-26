"""Chapter 3 — verse 2 (38.62 - 59.10): the training run through town at dusk, the singularity opens in the sky,
ChatGPT accelerates away, Claude's atoms rearrange, and Sydney's heart-bubble cage is sliced open."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw
from engine.film import Shot, MARGIN, CW, CH
from engine.px import Canvas, Sprite, rgb, rgba, dither_mask, silhouette, dilate4, dilate8
from art.body import render, make_pose, curve
from art import poses as PO
from art.portrait import bust
from art import palette as PAL
from scenes.kit import *
from scenes import props
import song

G, C = PAL.GPT, PAL.CLAUDE
OX = MARGIN
DUSK = props.TOWN_DUSK


def wt(prefix, word):
    return song.word_time(prefix, word)


# ================================================================ small numpy compositing helpers
def paste_np(dst, src, x, y, mask=None):
    """Binary-alpha paste of RGBA src onto dst (canvas array) with top-left at view (x, y)."""
    x, y = int(round(x)) + OX, int(round(y)) + OX
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 127
    if mask is not None:
        m &= mask[y0 - y:y1 - y, x0 - x:x1 - x]
    dst[y0:y1, x0:x1][m] = s[m]


def spr_np(dst, spr, x, y, flip=False, mask=None):
    a = spr.arr[:, ::-1] if flip else spr.arr
    ax = (spr.arr.shape[1] - 1 - spr.ax) if flip else spr.ax
    paste_np(dst, a, int(round(x)) - ax, int(round(y)) - spr.ay, mask)


def flat(spr_arr, colour):
    return silhouette(spr_arr, colour)


def canvas_np(cv):
    return np.array(cv.im)


@lru_cache(maxsize=64)
def heart_mask(w):
    """Pixel heart of width w (boolean), from the implicit heart curve."""
    h = max(3, int(round(w * 0.9)))
    ys, xs = np.mgrid[0:h, 0:w]
    X = (xs + 0.5 - w / 2) / (w / 2) * 1.18
    Y = -((ys + 0.5) / h * 2.35 - 1.2)
    m = (X * X + Y * Y - 1) ** 3 - X * X * Y ** 3 <= 0
    return m


HEART_SMALL = {
    5: ['.#.#.', '#####', '#####', '.###.', '..#..'],
    7: ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...'],
    9: ['.##...##.', '####.####', '#########', '#########', '.#######.', '..#####..', '...###...', '....#....'],
}


@lru_cache(maxsize=64)
def heart_bits(w):
    if w in HEART_SMALL:
        return np.array([[c == '#' for c in r] for r in HEART_SMALL[w]], bool)
    return heart_mask(w)


def heart(cv, cx, cy, w, c):
    m = heart_bits(w)
    cv.mask_fill(m, c, snap(cx - m.shape[1] / 2), snap(cy - m.shape[0] / 2))


# ================================================================ the street at dusk (shots 17, 18, 19)
GY_FAR, GY_NEAR = 151, 157          # ground lines of the two jog lanes
WALK_TOP, CURB = 141, 163           # sidewalk band
HOUSE_BASE = 141
WALLS = ['#5e4566', '#6b4a5e', '#54456a', '#6e4f5c', '#5a4a6e', '#634a66']
ROOFS = ['#3b2640', '#46283a', '#34284a', '#3e2a44']
WIN_ON, WIN_ON2, WIN_OFF = '#f7d77a', '#e8a860', '#2e2440'
FRAME = '#35283f'


def cv_local(w, h):
    return Canvas(w, h)


@lru_cache(maxsize=4)
def sky_arr(variant=0):
    cv = Canvas(CW, CH, (0, 0, 0), ox=OX, oy=OX)
    dgrad(cv, -12, -12, 344, 132, DUSK['sky'])
    # faint first stars in the deep top band
    r = R(71)
    for k in range(26):
        x, y = r(-10, 330), r(-10, 26)
        cv.px(x, y, '#7a6aa0' if k % 3 else '#b8a8d8')
    # the low sun (retro slit disc), partly behind the far town
    sx, sy, sr = 252, 104, 15
    cv.circle(sx, sy, sr + 2, '#f7c27a')
    cv.circle(sx, sy, sr, '#fbe3a0')
    for k, yy in enumerate((sy + 3, sy + 7, sy + 10, sy + 13)):
        cv.rect(sx - sr - 2, yy, 2 * sr + 5, 1 + k // 2, '#f7c27a')
    return np.array(cv.im)


@lru_cache(maxsize=16)
def row_strip(seed, period, base, hmin, hmax, wmin, wmax, col, roof, lights, win_sz=1, gap=(1, 4), top_pad=40):
    """A seamless distant town row: RGBA strip of width period + 360, top at base - hmax - top_pad."""
    H = hmax + top_pad + 6
    Wd = period + 360
    cv = Canvas(Wd, H)
    r = R(seed)
    x = 0
    houses = []
    while x < period:
        w = r(wmin, wmax)
        h = r(hmin, hmax)
        houses.append((x, w, h, r(0, 1), r.i(0, 1000)))
        x += w + r(*gap)
    sc = period / x  # stretch so the row repeats exactly
    y0 = H - 6
    for rep in (-1, 0, 1, 2):
        for (hx, w, h, kind, s2) in houses:
            X = hx * sc + rep * period
            if X > Wd or X + w < 0:
                continue
            X, w_ = snap(X), snap(w)
            cv.rect(X, y0 - h, w_, h + 6, col)
            rh = max(2, h * 0.3)
            if kind < 0.6:
                cv.poly([(X - 1, y0 - h), (X + w_ / 2, y0 - h - rh), (X + w_, y0 - h)], roof)
            elif kind < 0.8:
                cv.rect(X + 2, snap(y0 - h - 3), 2, 3, col)
            rr = R(s2)
            for wy in range(snap(y0 - h + 3), y0 - 2, 4 + win_sz):
                for wx in range(X + 2, X + w_ - 2, 3 + win_sz):
                    if rr() < lights:
                        cv.rect(wx, wy, win_sz, win_sz, DUSK['win'])
    return np.array(cv.im), base - (H - 6)


def window(cv, x, y, w, h, lit, seed=0, curtains=True):
    cv.rect(x - 1, y - 1, w + 2, h + 2, FRAME)
    if lit:
        cv.rect(x, y, w, h, WIN_ON)
        cv.rect(x, y + h // 2, w, h - h // 2, WIN_ON2)
        if curtains:
            cv.rect(x, y, 2, h, '#b86a5a')
            cv.rect(x + w - 2, y, 2, h, '#b86a5a')
    else:
        cv.rect(x, y, w, h, WIN_OFF)
        cv.rect(x + 1, y + 1, 1, 2, '#4a3a5a')
    cv.rect(x + w // 2, y, 1, h, FRAME)
    cv.rect(x - 2, y + h + 1, w + 4, 1, '#7a6078')


HOUSE_PERIOD = 600
KID_HOUSE = 3
KIDWIN = (6, 12, 15, 14)  # upper-left window of the kid house: dx, dy (from wall top), w, h


@lru_cache(maxsize=1)
def house_list():
    r = R(1717)
    out = []
    x = 8
    i = 0
    while x < HOUSE_PERIOD - 50:
        w = snap(r(46, 62))
        h = snap(r(40, 50))
        out.append(dict(x=x, w=w, h=h, wall=WALLS[i % len(WALLS)], roof=ROOFS[r.i(0, len(ROOFS))], rh=snap(r(11, 16)),
                        chim=r() < 0.5, seed=r.i(0, 999), kid=(i == KID_HOUSE)))
        x += w + snap(r(12, 26))
        i += 1
    sc = HOUSE_PERIOD / x
    for hh in out:
        hh['x'] = snap(hh['x'] * sc)
    return out


def draw_house(cv, X, hh):
    w, h, base = hh['w'], hh['h'], HOUSE_BASE
    top = base - h
    wall = hh['wall']
    cv.rect(X, top, w, h, wall)
    cv.rect(X + w - 2, top, 2, h, '#7a5a72')                      # sunlit right edge
    cv.rect(X, top, w, 2, '#3a2a44')                              # eave shadow
    rh = hh['rh']
    if hh['chim']:
        cv.rect(X + w - 14, top - rh + 2, 5, rh, '#4a3040')
        cv.rect(X + w - 15, top - rh + 1, 7, 2, '#5a3a4a')
    cv.poly([(X - 3, top), (X + w / 2, top - rh), (X + w + 2, top)], hh['roof'])
    cv.line(X + w / 2, top - rh, X + w + 2, top, '#8a5a6a')      # sunlit roof edge
    r = R(hh['seed'])
    # upper windows
    if hh['kid']:
        dx, dy, ww, wh = KIDWIN
        window(cv, X + dx, top + dy, ww, wh, True, curtains=False)
        window(cv, X + w - 17, top + dy, 11, 12, False)
    else:
        for k, wx in enumerate((X + 6, X + w - 17)):
            window(cv, wx, top + 12, 11, 12, r() < 0.55)
    # lower windows + door (mostly behind the fence)
    window(cv, X + 6, top + 32, 11, 10, r() < 0.5)
    cv.rect(X + w - 16, top + 30, 9, h - 30, '#3a2632')
    cv.rect(X + w - 15, top + 31, 7, h - 31, '#5a3444')


@lru_cache(maxsize=1)
def houses_strip():
    Wd = HOUSE_PERIOD + 360
    top = HOUSE_BASE - 80
    cv = Canvas(Wd, 90, ox=0, oy=-top)
    hl = house_list()
    for rep in (-1, 0, 1):
        for hh in hl:
            X = hh['x'] + rep * HOUSE_PERIOD
            if -80 < X < Wd + 10:
                draw_house(cv, X, hh)
        # round bushes / trees in the gaps
        r = R(99 + rep)
        for k, hh in enumerate(hl):
            gx = hh['x'] + hh['w'] + 7 + rep * HOUSE_PERIOD
            cv.circle(gx, HOUSE_BASE - 20, 9, '#33284a')
            cv.circle(gx + 5, HOUSE_BASE - 12, 8, '#2c2242')
            cv.circle(gx - 3, HOUSE_BASE - 25, 6, '#3c3056')
    return np.array(cv.im), top


FENCE_P = 5


@lru_cache(maxsize=1)
def fence_strip():
    period = 60
    Wd = 420
    cv = Canvas(Wd, 20)
    cv.rect(0, 6, Wd, 2, '#8a7088')
    cv.rect(0, 13, Wd, 2, '#7a6078')
    for x in range(0, Wd, FENCE_P):
        cv.rect(x, 2, 3, 17, '#a58aa0')
        cv.rect(x + 2, 2, 1, 17, '#806680')
        cv.px(x + 1, 1, '#a58aa0')
    cv.rect(0, 18, Wd, 2, '#3e3048')
    return np.array(cv.im), 124, period


@lru_cache(maxsize=1)
def walk_strip():
    """Sidewalk + curb + road edge, 168 px period."""
    period = 168
    Wd = period + 360
    cv = Canvas(Wd, 60)
    y0 = WALK_TOP
    cv.rect(0, 0, Wd, 60, '#221a2e')
    cv.rect(0, 0, Wd, CURB - y0, '#4a3a56')
    cv.rect(0, 0, Wd, 1, '#6a5676')
    cv.rect(0, 1, Wd, 1, '#56466a')
    for x in range(0, Wd, 28):
        cv.line(x, 2, x - 5, CURB - y0 - 1, '#3e3048')
    cv.rect(0, CURB - y0, Wd, 2, '#7a6880')
    cv.rect(0, CURB - y0 + 2, Wd, 3, '#352a40')
    # grit
    r = R(5)
    for k in range(60):
        x = r(0, period)
        for rep in (0, 1, 2):
            if x + rep * period < Wd:
                cv.px(x + rep * period, r(3, CURB - y0 - 2), '#56466a')
    return np.array(cv.im), y0, period


LAMP_P = 210


@lru_cache(maxsize=2)
def lamp_sprite(on=True):
    cv = Canvas(16, 84)
    cv.rect(7, 12, 2, 70, '#2a2034')
    cv.rect(6, 78, 4, 4, '#2a2034')
    cv.rect(8, 8, 6, 2, '#2a2034')
    cv.rect(11, 10, 5, 2, '#2a2034')
    cv.rect(12, 12, 3, 3, '#f7d77a' if on else '#6a5a6a')
    cv.px(13, 13, '#fff0a8' if on else '#6a5a6a')
    return np.array(cv.im)


def street_bg(off, t, hole=None, walk_off=None, extra_house=None):
    """Build the side-scrolling street. off = foreground scroll (px). Returns the canvas RGBA array."""
    a = sky_arr().copy()
    if hole is not None:
        hole(a)
    for (seed, per, base, hmin, hmax, wmin, wmax, col, roof, lights, par) in (
            (11, 420, 112, 8, 20, 10, 18, '#3a2e52', '#4a3456', 0.25, 0.10),
            (12, 480, 118, 12, 26, 12, 22, '#46365a', '#5a3a5a', 0.30, 0.22)):
        s, y = row_strip(seed, per, base, hmin, hmax, wmin, wmax, col, roof, lights)
        paste_np(a, s, -12 - (off * par) % per, y)
    hs, hy = houses_strip()
    hx = -12 - (off * 0.6) % HOUSE_PERIOD
    paste_np(a, hs, hx, hy)
    if extra_house:
        extra_house(a, off * 0.6)
    fs, fy, fp = fence_strip()
    paste_np(a, fs, -12 - (off * 0.9) % fp, fy)
    ws, wy, wp = walk_strip()
    paste_np(a, ws, -12 - (off if walk_off is None else walk_off) % wp, wy)
    # lamp posts (on the back edge of the sidewalk)
    lp = lamp_sprite()
    lx0 = -((off) % LAMP_P) + 40
    for k in range(-1, 3):
        x = lx0 + k * LAMP_P
        if -20 < x < 340:
            paste_np(a, lp, x - 8, WALK_TOP + 2 - 82)
    return a


def lamp_pools(cv, off):
    lx0 = -((off) % LAMP_P) + 40
    for k in range(-1, 3):
        x = lx0 + k * LAMP_P
        if -40 < x < 360:
            dither_overlay(cv, 0.25, '#6a5676', x - 4, WALK_TOP + 2, 26, 18)


def kid_window_overlay(pose):
    """Small RGBA array: the lit bay window with the kid inside (clipped to the glass)."""
    return _kid_window(pose)


@lru_cache(maxsize=8)
def _kid_window(pose):
    dx, dy, ww, wh = KIDWIN
    cv = Canvas(ww + 4, wh + 4, ox=2, oy=2)
    window(cv, 0, 0, ww, wh, True, curtains=False)
    cv.rect(0, 0, ww, wh, WIN_ON)
    cv.rect(0, wh // 2 + 2, ww, wh - wh // 2 - 2, WIN_ON2)
    k = kid(pose)
    a = np.array(cv.im)
    ka = k.arr
    # kid centred, head 2 px under the lintel
    X0, Y0 = 2 + (ww - ka.shape[1]) // 2 + (0 if pose != 'up' else 0), 2 + 1
    hh = min(ka.shape[0], wh - 1)
    sub = ka[:hh]
    m = sub[..., 3] > 127
    a[Y0:Y0 + hh, X0:X0 + sub.shape[1]][m] = sub[m]
    # sill + curtain edges back on top
    cv2 = Canvas.from_array(a)
    cv2.ox = cv2.oy = 2
    cv2.rect(0, 0, 2, wh, '#b86a5a')
    cv2.rect(ww - 2, 0, 2, wh, '#b86a5a')
    cv2.rect(-1, wh, ww + 2, 1, FRAME)
    cv2.rect(-2, wh + 1, ww + 4, 1, '#7a6078')
    return np.array(cv2.im)


def kid_house_x(off_house):
    """Screen x of the kid house's left wall for a house-layer offset."""
    hh = house_list()[KID_HOUSE]
    x = -12 + hh['x'] - (off_house % HOUSE_PERIOD)
    if x < -100:
        x += HOUSE_PERIOD
    return x, hh


def jog_index(t, rate_per_beat=4):
    return int(math.floor((t - song.PHASE) / song.BEAT * rate_per_beat + 1e-6))


def footfall_puffs(cv, t, x, y, seed):
    """Tiny dust puff at the lead foot on each contact drawing (on the beat)."""
    ph = ((t - song.PHASE) / song.BEAT) % 1.0
    k = ph * song.BEAT
    if k < 0.18:
        for i in range(3):
            dx = -2 - i * 2 - k * 30
            cv.px(snap(x + dx), snap(y - 1 - (i % 2) - k * 6), '#8a7890' if i else '#a898ac')


# ================================================================ 17 "We had a stable training run"
S17_OFF0 = 40.0
JOG_V = 60.0   # px/s on the sidewalk


def s17_off(t):
    return S17_OFF0 + JOG_V * (t - 38.62)


def claude_wave_arm(p, frame):
    b = p['bob']
    hx = [5, 8][frame % 2]
    p['arm_n'] = [(0, -50 + b), (4, -57 + b), (hx, -65 + b)]
    return p


def s17(f):
    cv = f.cv
    t = f.t
    off = s17_off(t)
    a = street_bg(off, t)
    # the kid's window (dynamic)
    t_stable = wt('We had', 'stable')
    t_train = wt('We had', 'training')
    t_run = wt('We had', 'run,')
    kx, hh = kid_house_x(off * 0.6)
    top = HOUSE_BASE - hh['h']
    if t < t_stable - 0.25:
        kp = 'stand'
    else:
        kp = 'wave' if f.step(5) % 2 == 0 else 'wave2'
    kw = _kid_window(kp)
    paste_np(a, kw, kx + KIDWIN[0] - 2, top + KIDWIN[1] - 2)
    cv.set_arr(a)
    lamp_pools(cv, off)
    # the two jog in step: contact drawings land on the beat
    i = jog_index(t)
    gp = PO.run(i, 'gpt', eyes='open', mouth='none')
    t_wave = t_train + 0.3
    t_wave_end = t_run + 0.35
    ceyes = 'calm'
    if t > t_train - 0.1:
        ceyes = 'open'
    cp = PO.run(i, 'claude', eyes=ceyes, mouth='none')
    if t_wave <= t < t_wave_end:
        cp['eyes'], cp['mouth'] = 'happy', 'smile'
        claude_wave_arm(cp, f.step(7))
    elif t >= t_wave_end:
        cp['eyes'], cp['mouth'] = 'happy', 'none'
    cv.blit(render('gpt', gp), 176, GY_FAR)
    footfall_puffs(cv, t, 176, GY_FAR, 1)
    cv.blit(render('claude', cp), 140, GY_NEAR)
    footfall_puffs(cv, t, 140, GY_NEAR, 2)
    f.cam['x'] = 160
    f.cam['y'] = 90


# ================================================================ placeholders (filled below)
def s18(f):
    s17(f)


def s19(f):
    s17(f)


def s20(f):
    s17(f)


def s21(f):
    s17(f)


SHOTS = [
    Shot('17_jog', 38.62, 0, s17),
    Shot('18_singularity', 41.42, 0, s18),
    Shot('19_accelerate', 45.02, 0, s19),
    Shot('20_atoms', 49.58, 0, s20),
    Shot('21_sydney', 52.98, 0, s21),
]
