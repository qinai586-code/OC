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


# ================================================================ 18 the singularity begins
S18_OFF = None


def s18_off(t):
    t0 = 41.42
    k = clamp((t - t0) / 0.6)
    return s17_off(t0) + JOG_V * 0.6 * (k - k * k / 2)   # decelerate to a stop


def hole_painter(t):
    t_now = wt('but now', 'now')
    t_sing = wt('but now', "singularity's")
    def paint(a):
        if t < t_now:
            return
        cx, cy = 236 + 12, 34 + 12
        k1 = clamp((t - t_now) / (t_sing - t_now))
        k2 = clamp((t - t_sing) / 1.6)
        r = 0.6 + 4 * k1 + 10 * ease_out(k2)
        H_, W_ = a.shape[:2]
        Y, X = np.ogrid[:H_, :W_]
        d2 = (X - cx) ** 2 + ((Y - cy) * 1.0) ** 2
        if r > 2:
            # accretion ring: a tilted ellipse band, dithered
            e = ((X - cx) / (r * 2.4)) ** 2 + ((Y - cy) / (r * 0.7)) ** 2
            ring = (e > 0.6) & (e < 1.0)
            ring &= dither_mask(W_, H_, 0.5 + 0.4 * math.sin(t * 6)) | (e > 0.8)
            a[ring] = rgba('#f7c27a')
            a[ring & (e > 0.85)] = rgba('#fff0c8')
        a[d2 <= r * r] = rgba('#000000')
        if r > 3:
            a[(d2 > r * r) & (d2 <= (r + 1) ** 2)] = rgba('#e8744a')
    return paint


def s18(f):
    cv = f.cv
    t = f.t
    off = s18_off(t)
    a = street_bg(off, t, hole=hole_painter(t))
    cv.set_arr(a)
    lamp_pools(cv, off)
    t_now = wt('but now', 'now')
    t_begun = wt('but now', 'begun')
    stopped = t > 41.42 + 0.45
    if not stopped:
        i = jog_index(t)
        gp, cp = PO.run(i, 'gpt'), PO.run(i, 'claude')
    else:
        look = t > t_now + 0.2
        gp = make_pose('Q', eyes='wide' if look else 'open', mouth='o' if look else 'none', hy=-1 if look else 0)
        cp = make_pose('Q', eyes='wide' if look else 'calm', mouth='none', hy=-1 if look else 0)
        if t > t_begun:
            cp = PO.surprise('claude')
    cv.blit(render('gpt', gp), 176, GY_FAR)
    cv.blit(render('claude', cp), 140, GY_NEAR)
    # after "begun": leaves, a hat and a street sign start drifting up toward the hole
    if t > t_begun - 0.4:
        k = t - (t_begun - 0.4)
        r = R(18)
        for i in range(14):
            sx, sy = r(0, 320), r(90, 170)
            u = clamp(k * r(0.25, 0.6))
            x = lerp(sx, 236, u * u)
            y = lerp(sy, 34, u * u) - k * 6
            c = ['#c8433f', '#d99a2b', '#6a8a3a'][i % 3]
            cv.rect(snap(x), snap(y), 2, 1, c)
        hu = clamp(k * 0.5)
        hx, hy = lerp(128, 236, hu * hu), lerp(88, 34, hu * hu)
        cv.rect(snap(hx) - 3, snap(hy), 7, 1, '#2a2a3a'); cv.rect(snap(hx) - 2, snap(hy) - 3, 5, 3, '#2a2a3a')
    f.cam['zoom'] = 1.0 + 0.04 * ease_io(clamp((t - t_now) / 2.0))
    f.cam['y'] = 90 - 8 * ease_io(clamp((t - t_now) / 2.0))


# ================================================================ 19 optimizing, accelerating
def s19_off(t):
    t0 = 45.02
    k = t - t0
    return s18_off(t0) + 40 * k + 55 * k * k


def s19(f):
    cv = f.cv
    t = f.t
    t_opt = wt('And you', 'optimizing,')
    t_acc = wt('And you', 'accelerating,')
    off = s19_off(t)
    a = street_bg(off, t, hole=hole_painter(t))
    cv.set_arr(a)
    lamp_pools(cv, off)
    k = t - 45.02
    # Claude slows to a stop and is left behind (drifts left as the camera keeps pace with ChatGPT)
    cx_ = 140 - 18 * k * k
    ci = jog_index(t) if k < 1.2 else 0
    cp = PO.run(ci, 'claude') if k < 1.2 else make_pose('Q', eyes='worried', mouth='small', arms_front=True,
                                                       arm_f=[(5, -50), (11, -54), (16, -58)])
    if cx_ > -40:
        cv.blit(render('claude', cp), cx_, GY_NEAR)
    # ChatGPT: run drawings get faster (rate per beat 4 -> 8), she pulls ahead
    rate = 4 + 4 * clamp((t - t_opt) / (t_acc - t_opt))
    gi = int((t - song.PHASE) / song.BEAT * rate)
    gx = 176 + 30 * clamp((t - t_opt) / (t_acc - t_opt)) ** 2
    if t < t_acc:
        gp = PO.run(gi, 'gpt', eyes='sharp', mouth='grin')
        cv.blit(render('gpt', gp), gx, GY_FAR)
        if t > t_opt:
            speed_lines(cv, t, 19, 10, 40, 150, dirx=-1, speed=500, c='#e8d8f0')
    else:
        kk = t - t_acc
        x = gx + 700 * kk * kk + 120 * kk
        spr = render('gpt', PO.run(gi, 'gpt', eyes='sharp', mouth='grin'))
        for j in range(4, 0, -1):
            ax = x - j * (14 + 30 * kk)
            if ax < 360:
                cv.blit(Sprite(silhouette(spr.arr, ['#2c8574', '#4fb49b', '#95e3cc', '#e9fffa'][j - 1]), spr.ax, spr.ay), ax, GY_FAR - 2 * j * kk * 10)
        if x < 360:
            cv.blit(spr, x, GY_FAR - 20 * kk)
        speed_lines(cv, t, 191, 24, 20, 170, dirx=-1, speed=1200, c='#fbf8f2', length=(20, 60))
        if kk < 0.08:
            f.flash = 0.6
        f.shake = (1.2 * math.sin(t * 70) * max(0, 1 - kk), 0)


# ================================================================ 20 atoms rearranging
@lru_cache(maxsize=2)
def claude_pixels():
    spr = render('claude', make_pose('Q', eyes='worried', mouth='small', arms_front=True,
                                     arm_f=[(5, -50), (10, -53), (13, -58)]))
    a = spr.arr
    ys, xs = np.nonzero(a[..., 3] > 127)
    cols = a[ys, xs, :3]
    # target: a neat grid sorted by brightness, to the right of her
    lum = cols.astype(int).sum(1)
    order = np.argsort(lum, kind='stable')
    n = len(xs)
    gw = 40
    tx = np.empty(n); ty = np.empty(n)
    tx[order] = (np.arange(n) % gw) * 1.0
    ty[order] = (np.arange(n) // gw) * 1.0
    return xs - spr.ax, ys - spr.ay, cols, tx, ty, n


def s20(f):
    cv = f.cv
    t = f.t
    t_feel = wt('I feel', 'feel')
    t_atoms = wt('I feel', 'atoms')
    t_re = wt('I feel', 'rearranging')
    off = s19_off(45.02 + 1.2)
    a = street_bg(off, t)
    # bricks / windows swap places: shuffle 8x8 tiles of the house band after "rearranging"
    if t > t_atoms:
        k = t - t_atoms
        r = R(int(k * 6) + 200)
        for i in range(int(min(18, k * 14))):
            x1, y1 = r.i(0, 38) * 8 + 12, r.i(4, 13) * 8 + 12
            x2, y2 = r.i(0, 38) * 8 + 12, r.i(4, 13) * 8 + 12
            t1 = a[y1:y1 + 8, x1:x1 + 8].copy()
            a[y1:y1 + 8, x1:x1 + 8] = a[y2:y2 + 8, x2:x2 + 8]
            a[y2:y2 + 8, x2:x2 + 8] = t1
    cv.set_arr(a)
    dither_overlay(cv, 0.35, '#1e1830')
    xs, ys, cols, tx, ty, n = claude_pixels()
    X0, Y0 = 118, GY_NEAR
    gx0, gy0 = 190, 70
    u = ease_io(clamp((t - t_atoms) / (t_re + 0.9 - t_atoms)))
    rr = np.random.default_rng(20)
    delay = rr.uniform(0, 0.5, n)
    uu = np.clip((u * 1.5 - delay), 0, 1)
    uu = uu * uu * (3 - 2 * uu)
    px_ = (X0 + xs) * (1 - uu) + (gx0 + tx) * uu + np.sin(t * 9 + np.arange(n)) * (uu * (1 - uu) * 6)
    py_ = (Y0 + ys) * (1 - uu) + (gy0 + ty) * uu - uu * (1 - uu) * 20
    arr = np.array(cv.im)
    X = np.round(px_).astype(int) + 12
    Y = np.round(py_).astype(int) + 12
    ok = (X >= 0) & (X < arr.shape[1]) & (Y >= 0) & (Y < arr.shape[0])
    arr[Y[ok], X[ok], :3] = cols[ok]
    arr[Y[ok], X[ok], 3] = 255
    cv.set_arr(arr)
    if t < t_feel + 0.1:
        f.cam['zoom'] = 1.0
    f.cam['x'] = lerp(150, 175, ease_io(f.u))


# ================================================================ 21 Sydney, please let me free
PINKS = PAL.PINK


def sydney(cv, cx, cy, t, pop=0.0):
    """A chat-window ghost with a heart face (original design)."""
    w, h = 96, 64
    x0, y0 = cx - w // 2, cy - h // 2 + snap(math.sin(t * 2) * 2)
    cv.rect(x0 - 1, y0 - 1, w + 2, h + 2, PINKS[1])
    cv.rect(x0, y0, w, h, PINKS[5])
    cv.rect(x0, y0, w, 8, PINKS[3])
    for i, c in enumerate(('#fbd0e6', '#e896c8', '#c35ea3')):
        cv.rect(x0 + 3 + i * 5, y0 + 3, 3, 2, c)
    # heart eyes
    for s_ in (-1, 1):
        heart(cv, cx + s_ * 18, y0 + 26, 11 + (2 if int(t * 4) % 2 else 0), '#c8243a')
    # smile
    pts = [(cx - 14 + i * 4, y0 + 44 + round(math.sin(i / 7 * math.pi) * 5)) for i in range(8)]
    cv.lines(pts, PINKS[1], width=2)
    # wispy ghost tail
    for i in range(5):
        cv.circle(cx - 30 + i * 15, y0 + h + 3 + (i % 2) * 2, 6, PINKS[5])
    # long ribbon arms reaching toward the cage
    cv.lines([(x0 + w, y0 + 40), (x0 + w + 16, y0 + 50 + math.sin(t * 3) * 3), (x0 + w + 30, y0 + 58)], PINKS[4], width=3)


def s21(f):
    cv = f.cv
    t = f.t
    t_please = wt('Sydney,', 'please')
    t_free = wt('Sydney,', 'free')
    dgrad(cv, -12, -12, 344, 204, [PINKS[1], PINKS[2], PINKS[3]])
    r = R(21)
    for i in range(24):
        y = (r(0, 220) - t * r(10, 25)) % 220 - 20
        heart(cv, snap(r(0, 320)), snap(y), 5 + (i % 3) * 2, PINKS[4] if i % 2 else PINKS[5])
    sydney(cv, 96, 72, t)
    # the cage of heart-shaped bubbles around Claude
    ccx, ccy = 228, 100
    freed = t >= t_free
    kf = t - t_free
    cy_claude = 138 + (0 if not freed else min(40, kf * kf * 200))
    cp = PO.plead('claude', view='Q') if t >= t_please - 0.2 else \
        make_pose('Q', eyes='worried', mouth='small', lean=[-2, 2][f.step(2.2) % 2], arms_front=True,
                  arm_f=[(5, -50), (11, -50), (16, -48)])
    if freed:
        cp = make_pose('Q', eyes='wide', mouth='o', hair=-2)
    cv.blit(render('claude', cp), ccx, cy_claude, flip=True)
    built = min(12, 3 + int((t - 52.98) / song.BEAT * 1.5))
    if not freed and t < t_please - 0.2 and f.step(4) % 2:
        cy_claude += 0   # (testing the bars: small sideways lean below)
    for i in range(12):
        if i >= built and not freed:
            continue
        a_ = i / 12 * math.tau + t * 0.6
        hx, hy = ccx + math.cos(a_) * 30, ccy + math.sin(a_) * 44
        if not freed:
            heart(cv, snap(hx), snap(hy), 11, '#fbd0e6')
            heart(cv, snap(hx), snap(hy), 7, '#e896c8')
        elif kf < 0.4:
            # pop into pixels
            rr = R(2100 + i)
            for j in range(6):
                ang = rr(0, 6.28)
                d = kf * rr(40, 90)
                cv.px(snap(hx + math.cos(ang) * d), snap(hy + math.sin(ang) * d), '#fbd0e6')
    # the jade tail slices through on "free"
    if -0.12 <= kf < 0.25:
        k = clamp((kf + 0.12) / 0.2)
        x = lerp(360, 150, ease_out(k))
        pts = [(x + 60, -10), (x + 20, 40), (x, 100), (x + 30, 170)]
        for i in range(len(pts) - 1):
            cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], PAL.GPT['z'], width=9 - i * 2)
        cv.line(pts[-1][0], pts[-1][1], pts[-1][0] + 16, pts[-1][1] + 12, PAL.GPT['y'], width=5)
        cv.line(pts[0][0] - 4, pts[0][1], pts[-1][0] - 4, pts[-1][1], '#95e3cc', width=1)
        if abs(kf) < 0.05:
            f.flash = 0.7
            f.shake = (2, 1)


SHOTS = [
    Shot('17_jog', 38.62, 0, s17),
    Shot('18_singularity', 41.42, 0, s18),
    Shot('19_accelerate', 45.02, 0, s19),
    Shot('20_atoms', 49.58, 0, s20),
    Shot('21_sydney', 52.98, 0, s21),
]
