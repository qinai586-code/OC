"""Chapter 8 — the ending (137.50 - 156.65).

Lyric alignment (measured):  "Was" 137.52  "it" 137.92  [band stops 138.44]  "all" 138.48  "for" 139.24
"show?" 140.08  [band slams back, bar 77 = 140.26]  outro vocalise 141.1-152.3  decay from bar 84 = 152.99
audible hard stop 154.75  silence 155.40-156.65.
"""
import math
import numpy as np
from functools import lru_cache
from engine.film import Shot
from engine.px import rgb, rgba, Sprite, dither_mask, silhouette
from art.body import render, make_pose
from art import poses as PO
from art.portrait import bust
from art import palette as PAL
from scenes.kit import *
from scenes.props import marquee
import song

W_WAS = song.word_time('Was it', 'Was')
W_IT = song.word_time('Was it', 'it')
W_ALL = song.word_time('Was it', 'all')
W_FOR = song.word_time('Was it', 'for')
W_SHOW = song.word_time('Was it', 'show')
STOP = song.BAND_STOP
SLAM = song.SLAM
DECAY = song.OUTRO_DECAY
CUT = song.AUDIO_CUT

CUR = dict(d='#4a0c14', m='#7a1622', l='#a8242e', h='#cc3a3a', fringe='#e8b84a', fringe2='#a8781e')
STAGE_FLOOR = 146


# ------------------------------------------------------------------ curtain
@lru_cache(maxsize=8)
def curtain_layer(w=344, h=204, ripple_key=0):
    """Velvet curtain: vertical folds with dithered shading. ripple_key selects a precomputed ripple drawing."""
    a = np.zeros((h, w, 4), np.uint8)
    xs = np.arange(w)
    thr = np.tile(np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32, (h // 4 + 1, w // 4 + 1))[:h, :w]
    ph = [0, 1.3, 2.4][ripple_key]
    fold = np.sin(xs / 9.0 + np.sin(np.arange(h)[:, None] / 40.0 + ph) * (0.6 if ripple_key else 0.0))
    lv = (fold + 1) / 2 * 3 + (thr - 0.5) * 0.9
    idx = np.clip(lv, 0, 2.99).astype(int)
    pal = np.array([rgb(CUR['d']), rgb(CUR['m']), rgb(CUR['l'])], np.uint8)
    a[..., :3] = pal[idx]
    a[..., 3] = 255
    # highlight ridges
    ridge = (np.abs(fold - 0.92) < 0.05) & (thr < 0.6)
    a[ridge, :3] = rgb(CUR['h'])
    # gold fringe at the bottom
    a[h - 6:h - 3, :, :3] = rgb(CUR['fringe'])
    a[h - 3:h, ::2, :3] = rgb(CUR['fringe2'])
    a[h - 3:h, 1::2, 3] = 0
    return a


def spotlight_mask(cx, cy, rx, ry, soft=6):
    """Hard-edged ellipse + a dithered rim, in canvas coords (margin included by caller)."""
    H_, W_ = 204, 344
    Y, X = np.ogrid[:H_, :W_]
    d = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
    inner = d <= 1
    rim = (d <= (1 + soft / rx) ** 2) & ~inner & dither_mask(W_, H_, 0.5)
    return inner, rim


def darken(a, m, col='#050507'):
    a[~m] = rgba(col)


@lru_cache(maxsize=1)
def stage_behind():
    from engine.px import Canvas
    cv = Canvas(344, 204, '#000000', ox=12, oy=12)
    cv.blit(stage_bg(True), -12, -12)
    light_cone(cv, 128, -12, STAGE_FLOOR + 6, 10, 70, 0.22)
    light_cone(cv, 196, -12, STAGE_FLOOR + 6, 10, 70, 0.22)
    for who, x in (('claude', 128), ('gpt', 196)):
        p = make_pose('F', eyes='happy', mouth='smile', arms_front=True,
                      arm_n=[(-6, -50), (-11, -53), (-15, -58)], arm_f=[(6, -50), (11, -53), (15, -58)])
        cv.blit(render(who, p), x, STAGE_FLOOR + 4)
    return np.array(cv.im)


def s52(f):
    """Closed curtain. Spotlight snaps on at "Was"; band stop freezes everything; twitch on "all";
    the curtain starts to lift on "for"; it flies on "show?"."""
    cv = f.cv
    a = np.array(cv.im)
    lift = 0.0
    if f.t >= W_FOR:
        lift = 10 * ease_in(clamp((f.t - W_FOR) / (W_SHOW - W_FOR))) + 190 * ease_in(clamp((f.t - W_SHOW) / (SLAM - W_SHOW)))
    # stage behind the curtain (only visible as it lifts): the performers already in their "ta-da" pose
    a[:] = rgba('#050507')
    if lift > 0:
        a[:] = stage_behind()
    ripple = 1 if (0 <= f.t - W_ALL < 0.12) else (2 if (0.12 <= f.t - W_ALL < 0.24) else 0)
    cl = curtain_layer(ripple_key=ripple)
    top = -int(lift)
    y0 = max(0, top)
    src = cl[y0 - top:]
    a[y0:y0 + src.shape[0]] = src[:a.shape[0] - y0]
    # spotlight
    spot_on = f.t >= W_WAS
    if not spot_on:
        a[:] = rgba('#050507')
    else:
        k = f.t - W_WAS
        rx = 58 + (6 if k < 0.05 else 0)
        wob = 0 if f.t >= STOP else math.sin((f.t - W_IT) * 9) * 2 * pulse(f.t - W_IT, 0.5)
        inner, rim = spotlight_mask(172 + wob, 96, rx, rx * 0.95)
        if lift < 1:
            outside = ~(inner | rim)
            dim = a.copy()
            dim[..., :3] = (dim[..., :3] * 0.18).astype(np.uint8)
            # keep it palette-clean: quantise the dim region to two dark reds
            dm = outside & dither_mask(344, 204, 0.35)
            a[outside] = rgba('#0c0406')
            a[dm] = rgba('#1c060a')
            a[rim] = rgba(CUR['d'])
        # floor ellipse of the spotlight
        fl = np.zeros_like(inner)
    cv.set_arr(a)
    if spot_on and lift < 30:
        # stage floor strip in front of the curtain
        cv.rect(-12, STAGE_FLOOR + 30, 344, 30, '#140a08')
    # dust motes in the beam: drift until the band stops, then freeze in place
    if spot_on:
        tm = min(f.t, STOP) - W_WAS
        r = R(52)
        for i in range(26):
            x = 110 + r(0, 120) + math.sin(tm * r(0.5, 1.5) + i) * 6
            y = 40 + (r(0, 110) - tm * r(4, 10)) % 110
            if ((x - 160) / 58) ** 2 + ((y - 84) / 55) ** 2 < 1:
                cv.px(snap(x), snap(y), '#f4c8a0' if i % 3 else '#fff0d8')
    if STOP <= f.t < SLAM:
        f.shake = (0, 0)
    # the curtain starts to rise: a line of light under it
    if f.t >= W_FOR and lift < 190:
        cv.rect(-12, 178 - int(lift), 344, 2, '#fff4d8')


# ------------------------------------------------------------------ the stage (shared by 53 / 56)
@lru_cache(maxsize=4)
def stage_bg(lit=True):
    from engine.px import Canvas
    cv = Canvas(344, 204, '#1a0e0a', ox=12, oy=12)
    # back wall: dark with a painted starry backdrop
    dgrad(cv, -12, -12, 344, 170, ['#0e0a18', '#1a1230', '#2a1a3a'])
    stars(cv, 53, 40, 0.0, 0, 0, 320, 120, colors=('#5a4a7a', '#b8a8d8', '#fff0d8'), twinkle=False)
    # proscenium curtains bunched at the sides (lifted curtain)
    for side in (-1, 1):
        x0 = -12 if side < 0 else 290
        for i in range(6):
            c = CUR['l'] if i % 2 else CUR['m']
            cv.rect(x0 + i * 7, -12, 7, 170, c)
        cv.rect(x0, 150, 42, 4, CUR['fringe'])
    cv.rect(-12, -12, 344, 20, CUR['m'])
    for x in range(-12, 332, 8):
        cv.poly([(x, 8), (x + 8, 8), (x + 4, 16)], CUR['l'])
    cv.rect(-12, 6, 344, 2, CUR['fringe'])
    # wooden floor
    cv.rect(-12, STAGE_FLOOR, 344, 60, '#6a3a22')
    for y, c in ((STAGE_FLOOR, '#8e5638'), (STAGE_FLOOR + 6, '#5a3020'), (STAGE_FLOOR + 14, '#4a2818'), (STAGE_FLOOR + 24, '#3a1e12')):
        cv.rect(-12, y, 344, 1, c)
    for x in range(-12, 340, 22):
        cv.line(x, STAGE_FLOOR + 1, x - 14 + (x - 160) // 6, 192, '#4a2818')
    # footlights
    for x in range(8, 320, 20):
        cv.rect(x, 176, 8, 3, '#2a1a10')
        cv.rect(x + 2, 175, 4, 1, '#fff0a8' if lit else '#4a3a20')
    return np.array(cv.im)


def light_cone(cv, cx, top_y, bot_y, w_top, w_bot, level=0.35, col='#fff0d8'):
    a = np.array(cv.im)
    H_, W_ = a.shape[:2]
    Y, X = np.ogrid[:H_, :W_]
    yy = Y - (top_y + cv.oy)
    k = np.clip(yy / max(1, bot_y - top_y), 0, 1)
    half = w_top / 2 + (w_bot - w_top) / 2 * k
    m = (np.abs(X - (cx + cv.ox)) <= half) & (yy >= 0) & (yy <= bot_y - top_y)
    m &= dither_mask(W_, H_, level)
    a[m] = rgba(col)
    cv.set_arr(a)


def s53(f):
    """Curtain gone: blaze of light, confetti, the big bow."""
    cv = f.cv
    cv.blit(stage_bg(True), -12, -12)
    k = f.t - SLAM
    # beams from above on the two performers
    light_cone(cv, 128, -12, STAGE_FLOOR + 6, 10, 70, 0.22)
    light_cone(cv, 196, -12, STAGE_FLOOR + 6, 10, 70, 0.22)
    # bow timing on the beats after the slam
    b1, b2 = song.beat(song.beat_index(SLAM) + 1), song.beat(song.beat_index(SLAM) + 2)
    fr = 0 if f.t < b1 else (1 if f.t < b2 else 2)
    if f.t >= b2 + song.BEAT * 1.6:
        fr = 1
    # Claude (left) and ChatGPT (right), front view, big "ta-da" then bow
    for who, x, flip in (('claude', 128, False), ('gpt', 196, True)):
        if fr == 0:
            p = make_pose('F', eyes='happy', mouth='smile', arms_front=True,
                          arm_n=[(-6, -50), (-11, -53), (-15, -58)], arm_f=[(6, -50), (11, -53), (15, -58)])
        else:
            p = PO.bow(fr, who, 'F')
            p['arm_n'] = [(-6, -50 + p['bob']), (-8, -43 + p['bob']), (-7, -36 + p['bob'] // 2)]
            p['arm_f'] = [(6, -50 + p['bob']), (8, -43 + p['bob']), (7, -36 + p['bob'] // 2)]
        if who == 'gpt':
            sw = [0, 2, 4, 2][f.step(8) % 4]
            p['tail'] = [(3, -35), (10, -30), (15, -22), (19, -12 - sw), (25, -8 - sw), (31, -12 - sw)]
        cv.blit(render(who, p), x, STAGE_FLOOR + 4)
    # confetti cannons from both wings
    confetti(cv, k, 77, 70, (0, 40), spread=35, speed=300, grav=90)
    confetti(cv, k, 78, 70, (320, 40), spread=35, speed=300, grav=90)
    if k < 0.1:
        f.flash = 1 - k / 0.1
        f.shake = (1.5 * (1 - k / 0.1), 1.0 * (1 - k / 0.1))
    f.cam['zoom'] = 1.0 + 0.05 * (1 - ease_out(k / 0.6))


# ------------------------------------------------------------------ the auditorium
SEAT_LIT = dict(back='#8a1c24', top='#b8323a', seam='#5a0e16', cush='#6a1420', arm='#2a0a10', gap='#12040a',
                wall='#1a0e16', wall2='#2a1420', floor='#1e0a0e')
SEAT_DIM = dict(back='#2a0a12', top='#3a0e18', seam='#1a060c', cush='#220810', arm='#0e0306', gap='#070205',
                wall='#0a060c', wall2='#120a12', floor='#0c0408')


def seat(cv, x, y, w, h, P):
    """One theatre seat seen from the front, bottom-left at (x, y)."""
    x, y, w, h = snap(x), snap(y), max(2, snap(w)), max(2, snap(h))
    cv.rect(x, y - h, w, h, P['back'])
    cv.rect(x + 1, y - h - 1, w - 2, 1, P['back'])
    cv.rect(x + 1, y - h, w - 2, max(1, h // 6), P['top'])
    if w >= 6:
        cv.rect(x + w // 2, y - h + max(2, h // 5), 1, h - max(3, h // 3), P['seam'])
    ch = max(1, h // 4)
    cv.rect(x - 1, y, w + 2, ch, P['cush'])
    cv.rect(x - 1, y + ch, w + 2, 1, P['gap'])


def hall_rows(cv, P, rows=10, horizon=46, t=0.0, aisle_lights=True):
    for i in range(rows):
        k = (i + 1) / rows
        y = horizon + (k ** 1.5) * 128
        sh = 3 + k * 15
        sw = 5 + k * 15
        aisle = 10 + 34 * k
        for side in (-1, 1):
            xx = 160 + side * aisle / 2
            n = 0
            while (xx > -40 if side < 0 else xx < 360) and n < 40:
                sx = xx - sw if side < 0 else xx
                seat(cv, sx + 1, y, sw - 2, sh, P)
                xx += side * sw
                n += 1
            if aisle_lights:
                cv.rect(snap(160 + side * (aisle / 2 - 2)), snap(y + 1), 1, 1, '#f2b84a' if P is SEAT_LIT else '#6a4a1a')


@lru_cache(maxsize=4)
def hall_from_stage(lit):
    from engine.px import Canvas
    P = SEAT_LIT if lit else SEAT_DIM
    cv = Canvas(344, 204, P['floor'], ox=12, oy=12)
    dgrad(cv, -12, -12, 344, 62, ['#050307', P['wall'], P['wall2']])
    cv.rect(-12, 28, 344, 5, P['wall2'])
    cv.rect(-12, 33, 344, 1, P['top'])
    for x in (24, 284):
        cv.rect(x, 14, 12, 7, '#0a1a0e')
        cv.rect(x + 1, 15, 10, 5, '#1e7a3a' if lit else '#12401e')
        cv.text('EXIT', x + 1, 15, '#8ff0a8' if lit else '#3a8a4a', font='3') if False else None
        for j, xx in enumerate(range(x + 2, x + 10, 2)):
            cv.rect(xx, 17, 1, 1, '#c8ffd8' if lit else '#4aa060')
    hall_rows(cv, P)
    return np.array(cv.im)


def spot_composite(cv, lit_arr, dim_arr, cx, cy, rx, ry):
    """Dim hall everywhere, the lit version inside the spotlight ellipse with a dithered rim."""
    inner, rim = spotlight_mask(cx + 12, cy + 12, rx, ry)
    out = dim_arr.copy()
    out[inner] = lit_arr[inner]
    out[rim] = lit_arr[rim]
    cv.blit(out, -12, -12)


def s54(f):
    """Reverse angle: every seat is empty. The spotlight searches the rows; nobody."""
    cv = f.cv
    # the spotlight jumps to a new block of seats on every other beat (and finds nobody)
    stops = [(52, 132), (236, 104), (120, 150), (276, 146), (84, 98), (196, 128), (32, 150), (160, 108), (250, 136)]
    q = (f.t - f.shot.start) / (song.BEAT * 2)
    i, fr = int(q), q % 1.0
    a0, a1 = stops[i % len(stops)], stops[(i + 1) % len(stops)]
    e = ease_out(clamp(fr / 0.3))
    sx, sy = lerp(a0[0], a1[0], e), lerp(a0[1], a1[1], e)
    spot_composite(cv, hall_from_stage(True), hall_from_stage(False), sx, sy, 40, 30)
    # the lip of the stage in the foreground, the performers' feet and shadows
    cv.rect(-12, 170, 344, 22, '#3a1e12')
    cv.rect(-12, 170, 344, 1, '#8e5638')
    for x in range(8, 320, 20):
        cv.rect(x + 2, 171, 4, 1, '#fff0a8')
    f.cam['x'] = 160 + 6 * ease_io(f.u)
    f.cam['zoom'] = 1.0 + 0.03 * ease_io(f.u)


@lru_cache(maxsize=4)
def close_rows(lit):
    """Closer view of the middle rows (seats at 2x the detail), for the kid shot."""
    from engine.px import Canvas
    P = SEAT_LIT if lit else SEAT_DIM
    cv = Canvas(344, 204, P['floor'], ox=12, oy=12)
    cv.fill(P['wall'])
    for ri, (y, sh, sw) in enumerate([(70, 16, 22), (100, 22, 30), (136, 28, 38), (180, 36, 48)]):
        off = (sw / 2) if ri % 2 else 0
        for n in range(-7, 8):
            seat(cv, 160 + n * sw - sw / 2 + off + 2, y, sw - 4, sh, P)
    return np.array(cv.im)


KID_ROW_Y = 100


def s55(f):
    """...except one seat. The spotlight lands on the kid in the yellow raincoat, clapping on the beat."""
    cv = f.cv
    k = f.lt
    tx, ty = 175, 78
    sx = lerp(40, tx, ease_out(clamp(k / 0.5)))
    lit, dim = close_rows(True), close_rows(False)
    # the kid (2x, sitting: only the top half shows over the seat in front), drawn into both layers' area
    from engine.px import Canvas
    from engine.scalex import scale2x
    beat_on = int((f.t - song.PHASE) / song.BEAT) % 2 == 0
    pose = 'clap' if beat_on else 'sit'
    if f.t > song.bar(80) + song.BEAT * 3.2:
        pose = 'up'
    spr = kid(pose)
    big = scale2x(spr.arr)
    spot_composite(cv, lit, dim, sx, ty + 10, 38, 34)
    inner, rim = spotlight_mask(sx + 12, ty + 22, 38, 34)
    kx, ky = 175 - big.shape[1] // 2, KID_ROW_Y - 22 - (0 if pose != 'sit' else -4)
    cv.blit(big, kx, ky)
    # re-draw the row in front of the kid so it occludes the legs (lit inside the spot)
    front = lit.copy()
    m = np.zeros(front.shape[:2], bool)
    m[12 + KID_ROW_Y + 1:12 + 136 + 12, :] = True
    reg = np.where((inner | rim)[..., None], lit, dim)
    arr = np.array(cv.im)
    arr[m] = reg[m]
    cv.set_arr(arr)
    f.cam['zoom'] = 1.0 + 0.1 * ease_io(f.u)
    f.cam['x'] = lerp(160, tx, ease_io(f.u))
    f.cam['y'] = lerp(90, 84, ease_io(f.u))


def s56(f):
    """They look at the kid. The kid waves. Claude waves back; ChatGPT hesitates, then waves."""
    cv = f.cv
    b82 = song.bar(82)            # 149.35
    t_claude = b82 + song.BEAT * 1
    t_gpt_look = b82 + song.BEAT * 2
    t_gpt = b82 + song.BEAT * 3 + song.BEAT * 0.5
    if f.t < b82:
        # two-shot on stage, from the auditorium: they straighten up and look down toward the seats
        cv.blit(stage_bg(True), -12, -12)
        light_cone(cv, 128, -12, STAGE_FLOOR + 6, 10, 70, 0.22)
        light_cone(cv, 196, -12, STAGE_FLOOR + 6, 10, 70, 0.22)
        up = f.t > f.shot.start + 0.3
        for who, x in (('claude', 128), ('gpt', 196)):
            p = PO.bow(1 if not up else 0, who, 'F')
            p['eyes'] = 'down' if up else 'closed'
            p['mouth'] = 'none'
            if who == 'gpt':
                p['tail'] = [(3, -35), (10, -30), (15, -22), (19, -12), (25, -8), (31, -12)]
            cv.blit(render(who, p), x, STAGE_FLOOR + 4)
        f.cam['zoom'] = 1.0
    elif f.t < t_claude - 0.02:
        # insert: the kid stands on the seat and waves
        cv.fill('#07050a')
        for ri, (y, sh, sw) in enumerate([(120, 30, 40), (170, 40, 52)]):
            for n in range(-5, 6):
                x = 160 + n * sw - sw / 2 + (sw / 2 if ri else 0)
                cv.rect(snap(x), snap(y - sh), sw - 4, sh, CUR['m'] if (n + ri) % 2 else CUR['d'])
                cv.rect(snap(x), snap(y - sh), sw - 4, 3, CUR['l'])
        spr = kid('wave' if int((f.t - song.PHASE) / (song.BEAT / 2)) % 2 == 0 else 'wave2')
        # the kid at 2x for this insert (a deliberate chunky close-up, like the busts)
        from engine.scalex import scale2x
        big = scale2x(spr.arr)
        cv.blit(big, 160 - big.shape[1] // 2, 104 - big.shape[0] + 26)
        cv.rect(118, 104, 84, 26, CUR['d'])
        cv.rect(118, 104, 84, 3, CUR['l'])
        a = np.array(cv.im)
        inner, rim = spotlight_mask(172, 96, 58, 56)
        dim = ~(inner | rim)
        lum = a[..., :3].astype(int).sum(-1)
        a[dim & (lum > 0)] = rgba('#0a0306')
        a[rim & (lum > 0)] = rgba('#3a0c14')
        cv.set_arr(a)
    else:
        # two busts: Claude waves back; ChatGPT looks at Claude, then waves (tail wag behind)
        cv.blit(stage_bg(True), -12, -12)
        dither_overlay(cv, 0.5, '#1a0e0a')
        kc = f.t - t_claude
        wav = int((f.t - song.PHASE) / (song.BEAT / 2)) % 2
        c_arm = (('arms_front', True), ('arm_f', ((6, -50), (10, -55), (12 + wav, -62))))
        cb = bust('claude', 'F', 'happy' if kc > 0.2 else 'calm', 'smile', pose_key=c_arm, bottom=-22)
        cv.blit(cb, 104, 126)
        f.lyric_top = True
        kg = f.t - t_gpt
        if kg < 0:
            ge = 'side' if f.t > t_gpt_look else 'wide'
            gb = bust('gpt', 'F', ge, 'small', bottom=-22)
        else:
            g_arm = (('arms_front', True), ('arm_n', ((-6, -50), (-10, -55), (-12 - wav, -62))))
            gb = bust('gpt', 'F', 'happy', 'smile', pose_key=g_arm, bottom=-22)
        # tail peeking up behind her shoulder, wagging after she decides
        if kg > 0:
            sw_ = [0, 3, 6, 3][int((f.t - song.PHASE) / (song.BEAT / 2)) % 4]
            pts = [(262, 150), (274, 132), (280 + sw_, 112), (276 + sw_ * 1.5, 94)]
            for i in range(len(pts) - 1):
                cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], PAL.GPT['z'], width=5 - i)
            tx, ty = pts[-1]
            for ang in (-0.6, 0, 0.6):
                cv.line(tx, ty, tx + math.sin(ang) * 9, ty - math.cos(ang) * 11, PAL.GPT['y'], width=3)
                cv.line(tx, ty, tx + math.sin(ang) * 7, ty - math.cos(ang) * 9, PAL.GPT['Y'], width=1)
        cv.blit(gb, 216, 126)


# ------------------------------------------------------------------ lights out
@lru_cache(maxsize=2)
def hall_layer():
    """From the back of the hall: tiny bright stage far away, the marquee sign above it."""
    from engine.px import Canvas
    cv = Canvas(344, 204, '#050307', ox=12, oy=12)
    # side walls converging
    cv.poly([(-12, -12), (100, 40), (100, 150), (-12, 192)], '#0c0610')
    cv.poly([(332, -12), (220, 40), (220, 150), (332, 192)], '#0c0610')
    # floor sloping toward the stage, and the backs of the seats in silhouette
    cv.poly([(100, 150), (220, 150), (332, 192), (-12, 192)], '#0a0408')
    for i in range(9):
        k = i / 8
        y = 136 + k * 50
        sw = 6 + k * 10
        x = -12 - (i % 2) * sw / 2
        while x < 336:
            cv.rect(snap(x) + 1, snap(y), snap(sw) - 2, snap(4 + k * 8), '#14060c' if i % 2 else '#1a080e')
            cv.rect(snap(x) + 2, snap(y) - 1, snap(sw) - 4, 1, '#2a0c14')
            x += sw
    return np.array(cv.im)


def s57(f):
    cv = f.cv
    if f.t >= CUT:
        cv.fill('#000000')
        f.lyrics = False
        return
    cv.blit(hall_layer(), -12, -12)
    # stage opening (proscenium), lit by banks that go out on the beats after the decay starts
    banks = 4
    outs = [DECAY + song.BEAT * i for i in range(banks)]
    lit = sum(1 for o in outs if f.t < o)
    px0, py0, pw, ph = 112, 70, 96, 62
    cv.rect(px0 - 4, py0 - 4, pw + 8, ph + 8, '#3a0c14')
    shades = ['#050307', '#2a1a1a', '#6a4a3a', '#c8a878', '#f4e6c8']
    cv.rect(px0, py0, pw, ph, shades[lit])
    # the two tiny figures on stage + the kid's silhouette in the front row
    if lit > 0:
        base = py0 + ph - 2
        # Claude: copper hair, cream top, brown skirt, one light and one dark leg
        cv.rect(146, base - 26, 7, 16, PAL.CLAUDE['H']); cv.rect(147, base - 25, 5, 5, PAL.CLAUDE['S'])
        cv.rect(147, base - 19, 5, 6, PAL.CLAUDE['c']); cv.rect(147, base - 13, 5, 4, PAL.CLAUDE['p'])
        cv.rect(148, base - 9, 1, 9, PAL.CLAUDE['i']); cv.rect(150, base - 9, 1, 9, PAL.CLAUDE['k'])
        # ChatGPT: dark hair with two jade horns, black coat, one tail
        cv.px(169, base - 27, PAL.GPT['J']); cv.px(174, base - 27, PAL.GPT['J'])
        cv.rect(169, base - 26, 6, 9, PAL.GPT['k']); cv.rect(170, base - 24, 4, 4, PAL.GPT['S'])
        cv.rect(168, base - 17, 8, 9, PAL.GPT['c']); cv.rect(170, base - 16, 4, 4, PAL.GPT['W'])
        cv.rect(170, base - 8, 1, 8, PAL.GPT['l']); cv.rect(173, base - 8, 1, 8, PAL.GPT['l'])
        cv.lines([(176, base - 8), (180, base - 4), (184, base - 5)], PAL.GPT['z']); cv.px(185, base - 6, PAL.GPT['y'])
    cv.rect(px0, py0 + ph - 2, pw, 2, '#3a2418')
    # the kid: a small yellow hood above the seat backs in the middle of the hall, lit by the last light
    ky = 144
    hood = PAL.KID['y'] if lit > 0 else '#4a3a12'
    cv.rect(158, ky - 5, 5, 5, hood)
    cv.rect(159, ky - 6, 3, 1, hood)
    cv.rect(159, ky - 3, 3, 2, '#3b2a22' if lit > 0 else '#1a1208')
    # the marquee above the stage: P(DOOM) = ?% with bulbs dying
    on = 1.0 if f.t < DECAY else max(0.0, 1 - (f.t - DECAY) / (CUT - DECAY - 0.15))
    q = '?' if (f.t < DECAY or (int(f.t * 14) % 3)) else ' '
    marquee(cv, 96, 30, 128, 26, f'P(DOOM) = {q}%', t=f.t, scale=1, on=on, seed=9,
            text_col='#1e0f0c' if on > 0.1 else '#3a2418')
    if on <= 0.02:
        dither_overlay(cv, 0.6, '#050307', 96, 30, 128, 26)
    f.cam['zoom'] = 1.0 + 0.06 * ease_io(clamp((f.t - f.shot.start) / (CUT - f.shot.start)))
    f.cam['y'] = 86


def s58(f):
    """Silence. The two cursors from the opening, and the question."""
    cv = f.cv
    cv.fill('#050507')
    f.lyrics = False
    k = f.t - song.SILENCE
    if k < 0.1:
        return
    txt = 'p(doom) = ?'
    text_big(cv, txt, 160, 84, '#d2d8e0', scale=1, align='center')
    wv, _ = (len(txt) * 5, 7)
    blink = int(k * 2.2) % 2 == 0
    from engine.font import text_size
    tw = text_size(txt, '5')[0]
    if blink:
        cv.rect(160 + tw // 2 + 3, 84, 3, 7, PAL.JADE[5])
    else:
        cv.rect(160 + tw // 2 + 3, 84, 3, 7, PAL.WARM[5])


SHOTS = [
    Shot('52_curtain', 137.50, 0, s52),
    Shot('53_show', SLAM, 0, s53),
    Shot('54_seats', song.bar(78), 0, s54),
    Shot('55_kid', song.bar(80), 0, s55),
    Shot('56_wave', song.bar(81), 0, s56),
    Shot('57_lights_out', song.bar(83), 0, s57),
    Shot('58_end', song.SILENCE, 0, s58, lyrics=False),
]
