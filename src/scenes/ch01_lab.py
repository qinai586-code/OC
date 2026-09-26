"""Chapter 1 — opening + verse 1 (0.00 - 22.78): boot cursors, eyes, the night lab, the loss-curve slide,
servant/boss, the dragon shadow and the cookie."""
import math
import numpy as np
from engine.film import Shot
from engine.px import rgb, rgba, Sprite, dilate8
from art.body import render, make_pose, curve, default_tail
from art import poses as PO
from art.portrait import bust
from art.ecu import draw_eye
from art import palette as PAL
from scenes.kit import *
import song

G, C = PAL.GPT, PAL.CLAUDE
BG = '#050507'


def bt(n):
    return song.beat(n)


# ================================================================ 01 boot cursors
def s01(f):
    cv = f.cv
    cv.fill(BG)
    # pickup eighths: beat 0..3.5 (0.238 .. 1.829)
    eighths = [song.beat(k * 0.5) for k in range(8)]
    n = sum(1 for e in eighths if f.t >= e - 0.01)
    k = max(0, n - 1)
    # cursors step toward the centre on each eighth
    gx = 118 + k * 5
    cx_ = 198 - k * 5
    y = 84
    on_g = n > 0 and (k % 2 == 0 or n >= 7)
    on_c = n > 0 and (k % 2 == 1 or n >= 7)
    # faint prompt marks
    if n > 0:
        cv.rect(gx - 8, y + 2, 2, 1, PAL.JADE[3]); cv.rect(gx - 7, y + 3, 1, 1, PAL.JADE[3])
        cv.rect(cx_ + 10, y + 2, 2, 1, PAL.WARM[3]); cv.rect(cx_ + 10, y + 3, 1, 1, PAL.WARM[3])
    if on_g or (n > 0 and f.step(8) % 2 == 0):
        cv.rect(gx, y, 3, 7, PAL.JADE[5] if on_g else PAL.JADE[2])
    if on_c or (n > 0 and f.step(8) % 2 == 1):
        cv.rect(cx_, y, 3, 7, PAL.WARM[5] if on_c else PAL.WARM[2])
    # last sixteenth: they touch, a white line opens (CRT-style) into the downbeat flash
    tt = f.t - (song.DOWNBEAT_1 - 0.12)
    if tt > 0:
        w = int(4 + ease_in(tt / 0.12) * 330)
        cv.rect(160 - w // 2, y + 3, w, 1, '#fbf8f2')
        cv.rect(158, y, 4, 7, '#fbf8f2')
    f.lyrics = False


# ================================================================ 02 "I see": Claude's eyes open
def face_bg(cv, who, hair_top=True):
    P = PAL.CLAUDE if who == 'claude' else PAL.GPT
    cv.fill(P['S'])
    dgrad(cv, 0, 140, 320, 40, [P['S'], P['s']])


def claude_bangs(cv, t, y=0):
    # copper bangs across the top of an ECU (hand-shaped strands with pointed tips)
    C_ = PAL.CLAUDE
    tips = [(-10, 40), (18, 52), (40, 34), (62, 58), (88, 30), (112, 46), (140, 26), (172, 30), (196, 50), (222, 28),
            (248, 56), (272, 36), (298, 48), (330, 40)]
    cv.rect(-12, -12, 344, 26 + y, C_['H'])
    for i in range(len(tips) - 1):
        (xa, ya), (xb, yb) = tips[i], tips[i + 1]
        mid = (xa + xb) / 2
        cv.poly([(xa, 0 + y), (xb, 0 + y), (xb, 14 + y), (mid + 2, 14 + y + (ya + yb) / 2 - 10), (xa, 14 + y)], C_['H'])
        cv.poly([(xa + 3, 10 + y), (mid, 10 + y + (ya + yb) / 2 - 8), (mid - 3, 12 + y)], C_['h'])
    for i, (x, yy) in enumerate(tips):
        cv.poly([(x - 9, 10 + y), (x + 9, 10 + y), (x + 1, yy + y)], C_['H'] if i % 3 else C_['L'])
        cv.line(x - 2, 14 + y, x, yy - 2 + y, C_['h'])
    cv.rect(-12, -12, 344, 8 + y, C_['h'])


def s02(f):
    cv = f.cv
    face_bg(cv, 'claude')
    t_open = song.word_time('I see', 'I')
    k = f.t - t_open
    # closed until "I", then 3 authored drawings: closed -> half -> open (overshoot) -> settle
    if k < 0:
        op = 0.0
    elif k < 0.05:
        op = 0.35
    elif k < 0.10:
        op = 1.05
    else:
        op = 0.92
    look = (0.25 if f.t > t_open + 0.35 else 0.0, -0.1)
    for side, x in ((-1, 96), (1, 224)):
        draw_eye(cv, x, 104, 92, 'claude', open_=op, look=look, flip=(side < 0))
    # blush and a hint of nose
    for x in (58, 262):
        dfill(cv, x - 14, 150, 28, 5, PAL.CLAUDE['S'], PAL.CLAUDE['b'], 0.5)
    cv.rect(160, 158, 2, 1, PAL.CLAUDE['s'])
    claude_bangs(cv, f.t, y=int(4 * ease_out(k / 0.3)) if k > 0 else 0)
    f.cam['zoom'] = 1.0 + 0.04 * ease_out(f.u)


# ================================================================ 03 sparks of AGI: ChatGPT's eye
def gpt_hair_frame(cv, t):
    Gp = PAL.GPT
    cv.poly([(-12, -12), (332, -12), (332, 30), (250, 22), (214, 44), (180, 18), (140, 40), (100, 16), (60, 36), (20, 20), (-12, 34)], Gp['k'])
    for x, y in ((250, 22), (180, 18), (100, 16), (20, 20)):
        cv.line(x, y, x + 8, y + 18, Gp['K'])
    # teal lock falling at the left edge
    cv.poly([(-12, 20), (18, 24), (26, 120), (10, 190), (-12, 190)], Gp['k'])
    cv.poly([(4, 110), (20, 118), (14, 190), (0, 190)], Gp['t'])
    cv.line(12, 40, 20, 120, Gp['K'])


def s03(f):
    cv = f.cv
    cv.fill(PAL.GPT['S'])
    dgrad(cv, 0, 150, 320, 30, [PAL.GPT['S'], PAL.GPT['s']])
    t_sp = song.word_time('I see', 'sparks')
    t_agi = song.word_time('I see', 'AGI')
    star = ease_out((f.t - t_agi) / 0.12) * (1 - 0.35 * clamp((f.t - t_agi - 0.4) / 1.0)) if f.t > t_agi else 0.0
    glow = pulse(f.t - t_sp, 0.3) + pulse(f.t - t_agi, 0.5)
    ix, iy, ir = draw_eye(cv, 172, 100, 196, 'gpt', open_=1.0, look=(-0.05, 0.05), star=star, glow=glow, t=f.t,
                          pupil=1.0 - 0.3 * star)
    # lightning across the iris: re-drawn at 15 fps, bursts on "sparks", "of", "AGI"
    step = f.step(15)
    bursts = [(t_sp, 0.7, 3), (song.word_time('I see', 'of'), 0.25, 1), (t_agi, 1.0, 5)]
    for (tb, life, n) in bursts:
        k = f.t - tb
        if 0 <= k < life:
            for j in range(n):
                a0 = (step * 1.7 + j * 2.1 + tb) % 6.28
                r0 = ir * (0.35 + 0.1 * (j % 2))
                r1 = ir * (1.0 + (0.5 if tb == t_agi else 0.05))
                sparks_bolt(cv, ix + math.cos(a0) * r0, iy + math.sin(a0) * r0,
                            ix + math.cos(a0 + 0.5) * r1, iy + math.sin(a0 + 0.5) * r1, seed=step * 13 + j + int(tb * 10),
                            c='#f2fffb', c2='#6fe6c8', jag=5, segs=6)
    gpt_hair_frame(cv, f.t)
    # slow pull back through the line
    f.cam['zoom'] = 1.12 - 0.12 * ease_io(f.u)
    f.cam['x'] = 172 - 12 * (1 - ease_io(f.u)) + 12 * 0
    f.cam['y'] = 100 - 10 * (1 - ease_io(f.u)) + 0
    f.cam['x'], f.cam['y'] = lerp(ix, 160, ease_io(f.u)), lerp(iy, 90, ease_io(f.u))


# ================================================================ the night lab
LAB_FLOOR = 150


def lab(cv, t, lamp=False, dark=0.0, window=True):
    wall, wall2, floor, floor2 = '#1a2036', '#222a46', '#0e1020', '#171b33'
    cv.fill(wall)
    # wall panels
    for x in range(-8, 330, 48):
        cv.rect(x, 0, 1, LAB_FLOOR, wall2)
    cv.rect(-12, LAB_FLOOR - 6, 344, 1, wall2)
    # window with the town at night
    if window:
        wx, wy, ww, wh = 112, 26, 92, 56
        cv.rect(wx - 2, wy - 2, ww + 4, wh + 4, '#0b0d18')
        dgrad(cv, wx, wy, ww, wh, ['#0c1230', '#1b2450', '#2e3868'])
        stars(cv, 7, 18, t, wx, wy, ww, 22)
        for i, (hx, hh) in enumerate([(0, 18), (12, 26), (22, 14), (34, 30), (48, 20), (58, 34), (72, 16), (82, 24)]):
            cv.rect(wx + hx, wy + wh - hh, 11, hh, '#0a0d1c')
            for yy in range(wy + wh - hh + 3, wy + wh - 2, 5):
                for xx in range(wx + hx + 2, wx + hx + 10, 4):
                    if (xx * 7 + yy * 3 + i) % 5 < 2:
                        cv.rect(xx, yy, 2, 2, '#f2c24a' if (xx + yy) % 3 else '#e89a3a')
        cv.rect(wx + ww // 2, wy, 1, wh, '#0b0d18')
        cv.rect(wx, wy + wh // 2, ww, 1, '#0b0d18')
    # floor
    cv.rect(-12, LAB_FLOOR, 344, 50, floor)
    cv.rect(-12, LAB_FLOOR, 344, 1, floor2)
    for x in range(-12, 332, 24):
        cv.line(x, LAB_FLOOR + 1, x - 30, 192, floor2)


def desk(cv, x, y, crt=True, t=0.0, screen='#1f6f60'):
    """Desk top at (x, y), 64 wide."""
    cv.rect(x, y, 64, 4, '#5a3a2a')
    cv.rect(x, y + 4, 64, 1, '#3a2419')
    cv.rect(x + 2, y + 5, 3, LAB_FLOOR - y - 5, '#3a2419')
    cv.rect(x + 59, y + 5, 3, LAB_FLOOR - y - 5, '#3a2419')
    if crt:
        cv.rect(x + 8, y - 26, 30, 25, '#c9c2b2')
        cv.rect(x + 8, y - 26, 30, 1, '#e2dccd')
        cv.rect(x + 11, y - 23, 24, 17, '#0b1512')
        dgrad(cv, x + 12, y - 22, 22, 15, ['#0e3a33', screen])
        for k in range(3):
            w = 6 + ((int(t * 6) + k * 5) % 12)
            cv.rect(x + 14, y - 19 + k * 4, w, 1, '#8ff0d4')
        cv.rect(x + 18, y - 1, 10, 1, '#8a8474')
        cv.rect(x + 42, y - 3, 14, 3, '#2a2d33')   # keyboard
        cv.rect(x + 43, y - 3, 12, 1, '#44485a')


def server_rack(cv, x, top, t, bright=False):
    w = 34
    cv.rect(x, top, w, LAB_FLOOR - top, '#141820')
    cv.rect(x, top, w, 1, '#2d333f')
    cv.rect(x, top, 1, LAB_FLOOR - top, '#2d333f')
    for i, yy in enumerate(range(top + 4, LAB_FLOOR - 6, 7)):
        cv.rect(x + 3, yy, w - 6, 5, '#1f252f')
        cv.rect(x + 3, yy, w - 6, 1, '#2d333f')
        for j in range(4):
            on = (int(t * (3 + j)) + i * 3 + j * 5) % 4 != 0
            c = ('#5fe0a0' if j % 2 else '#f2c24a') if on else '#2a3a2a'
            cv.px(x + 6 + j * 3, yy + 2, c)
        cv.rect(x + 20, yy + 2, 9, 1, '#0b0e12')


def tail_points(pose):
    ctrl = pose.get('tail') or default_tail(pose['view'])
    return curve(ctrl, 8)


def blit_char(cv, who, pose, x, y, flip=False):
    cv.blit(render(who, pose), x, y, flip=flip)


def clipboard(cv, x, y):
    cv.rect(x, y, 9, 12, '#7a5236')
    cv.rect(x + 1, y + 2, 7, 9, '#f4f1ea')
    cv.rect(x + 3, y, 3, 2, '#9aa0aa')
    for k in range(3):
        cv.rect(x + 2, y + 4 + k * 2, 5 - (k == 2) * 2, 1, '#9aa0b4')


def sweat(cv, x, y, k):
    if k < 0:
        return
    yy = y + min(6, int(k * 14))
    cv.px(x, yy, '#bfe8ff'); cv.rect(x - 1, yy + 1, 3, 2, '#bfe8ff'); cv.px(x, yy + 3, '#8ac4e8')
    cv.px(x - 1, yy + 1, '#ffffff')


GPT_SIT_Q = dict(sit=True, leg_n=[(-1, -35), (9, -35), (10, -20)], leg_f=[(1, -35), (11, -34), (13, -20)],
                 arm_n=[(-4, -50), (-5, -43), (1, -37)], arm_f=[(5, -50), (7, -43), (9, -37)], arms_front=True)


def gpt_sit(eyes='open', mouth='none', tail=None, **kw):
    p = make_pose('Q', eyes=eyes, mouth=mouth, **{**GPT_SIT_Q, **kw})
    p['tail'] = tail or [(-3, -35), (-7, -30), (-8, -21), (-6, -12), (-8, -4), (-13, 2)]
    return p


# ================================================================ 04 circuits / nervous
def s04(f):
    cv = f.cv
    lab(cv, f.t)
    desk(cv, 14, 118, t=f.t)
    rx, top = 196, 92
    server_rack(cv, rx, top, f.t)
    t_circ = song.word_time('Your circuits', 'circuits')
    t_nerv = song.word_time('Your circuits', 'nervous,')
    # ChatGPT sitting on the rack, facing left toward Claude; tail swings (4 drawings, 8 fps)
    sw = [0, 1, 2, 1][f.step(6) % 4]
    tail = [(-3, -35), (-7, -30), (-8 + sw, -21), (-6 + sw, -12), (-9 + sw, -4), (-14 + sw * 2, 1)]
    look = 'side' if f.t < t_nerv else 'open'
    gp = gpt_sit(eyes='open' if f.step(12) % 40 != 0 else 'closed', mouth='smile' if f.t > t_nerv else 'none', tail=tail)
    gx, gy = rx + 17, top + 35
    blit_char(cv, 'gpt', gp, gx, gy, flip=True)
    # circuit traces racing down the tail after "circuits"
    if f.t > t_circ:
        pts = tail_points(gp)
        n = len(pts)
        for j in range(3):
            q = ((f.t - t_circ) * 1.6 + j / 3) % 1.0
            i = int(q * (n - 1))
            x, y = pts[i]
            cv.rect(gx - round(x), gy + round(y), 1, 1, '#aaffea')
            cv.rect(gx - round(x) + 1, gy + round(y), 1, 1, '#4fb49b')
        # the rack answers
        for yy in range(top + 6, LAB_FLOOR - 6, 7):
            if (int((f.t - t_circ) * 12) + yy) % 3 == 0:
                cv.rect(rx + 20, yy + 2, 9, 1, '#6fe6c8')
    # Claude with clipboard; sweats and steps back on "nervous"
    k = f.t - t_nerv
    cx = 92 - (0 if k < 0 else 2 if k < 0.08 else 5)
    eyes = 'calm' if k < 0 else 'worried'
    cp = make_pose('Q', eyes=eyes, mouth='none' if k < 0 else 'flat', arms_front=True,
                   arm_f=[(5, -50), (8, -45), (7, -41)], bob=1 if 0 <= k < 0.08 else 0)
    if 0 <= k < 0.08:
        cp.update(PO.walk(2, 'claude', eyes=eyes))
        cp.update(dict(view='Q', arms_front=True, arm_f=[(5, -50), (8, -45), (7, -41)], lean=-1))
    blit_char(cv, 'claude', cp, cx, LAB_FLOOR + 2)
    clipboard(cv, cx + 3, LAB_FLOOR + 2 - 46)
    sweat(cv, cx + 8, LAB_FLOOR + 2 - 70, k)
    if k > 0.1:
        sweat(cv, cx - 7, LAB_FLOOR + 2 - 66, k - 0.25)
    f.cam['x'] = 160 + 2 * ease_io(f.u)


# ================================================================ 05 no surprise: party popper
def popper(cv, x, y, k):
    """Cone pointing left, mouth at (x, y)."""
    cv.poly([(x, y - 3), (x + 12, y - 1), (x + 12, y + 1), (x, y + 3)], '#e05a6a')
    for i in range(0, 12, 3):
        cv.rect(x + i, y - 2 + i // 6, 1, 4 - i // 6, '#f2c230')
    cv.rect(x + 11, y - 1, 2, 3, '#f4f1ea')
    if 0 <= k < 0.06:
        cv.circle(x - 3, y, 4, '#fff6c0')


def s05(f):
    cv = f.cv
    lab(cv, f.t, window=True)
    t_s = song.word_time("that's no", 'surprise')
    k = f.t - t_s
    # Claude bust left facing right, ChatGPT bust right facing left
    cb = bust('claude', 'Q', 'calm', 'none')
    cv.blit(cb, 92, 150)
    arm = (('arms_front', True), ('arm_f', ((5, -50), (11, -50), (16, -53))))
    gb = bust('gpt', 'Q', 'happy' if k > 0 else 'open', 'grin' if k > 0 else 'smile', pose_key=arm)
    cv.blit(gb, 246, 150, flip=True)
    # popper in ChatGPT's raised hand (bust hand at local (16,-53) x2, flipped)
    hx, hy = 246 - 2 * 16, 150 + 2 * (-53 - (-54)) - 2 * 1
    popper(cv, hx - 14, hy, k)
    # the streamers and confetti
    if k > 0:
        confetti(cv, k, 5, 46, (hx - 16, hy), spread=40, speed=260, grav=60)
        # streamers draped on Claude's head (settle after 0.35 s)
        if k > 0.3:
            for i, (x0, c) in enumerate(((76, '#f2c230'), (86, '#e05a6a'), (98, '#6fd3bb'), (106, '#9a7bff'))):
                pts = [(x0, 94), (x0 + 2, 100), (x0 - 1, 108), (x0 + 1, 116)]
                cv.lines(pts[:2 + min(2, int((k - 0.3) * 20))], c)
            for i in range(10):
                x = 70 + (i * 37) % 44
                cv.rect(x, 92 + (i * 5) % 6, 2, 1, ('#f2c230', '#e05a6a', '#6fd3bb', '#f4f1ea')[i % 4])
    f.cam['x'] = 160 - 3 * ease_io(f.u)


# ================================================================ 06 the loss curve slide
LOSS_W = 560


def loss_y(x, t_drop, t):
    """The curve: a high plateau that gives way at x~200 after t_drop."""
    k = ease_in(clamp((t - t_drop) / 0.25))
    plate = 64 + 4 * math.sin(x * 0.05) - x * 0.02
    fallen = 64 + 104 / (1 + math.exp(-(x - 250) / 18)) - x * 0.01
    if x < 190:
        return plate
    return lerp(plate, fallen, k)


def s06(f):
    cv = f.cv
    t_drop = song.word_time('There was', 'drop')
    t_loss = song.word_time('There was', 'loss,')
    # camera follows ChatGPT along the curve (world is LOSS_W wide)
    slide = clamp((f.t - t_drop - 0.12) / (t_loss - t_drop - 0.12))
    walk_x = 120 + 60 * clamp((f.t - f.shot.start) / (t_drop - f.shot.start))
    gx = walk_x if f.t < t_drop + 0.12 else lerp(180, 372, ease_in(slide) * 0.6 + slide * 0.4)
    gy = loss_y(gx, t_drop, f.t)
    camx = clamp(gx + 20, 160, LOSS_W - 160)
    camy = clamp(gy - 10, 90, 132)
    ox, oy = snap(camx - 160), snap(camy - 90)
    fx, fy = camx - 160 - ox, camy - 90 - oy
    cv.fill('#0a0f14')
    # grid
    for x in range(-(ox % 16) - 16, 340, 16):
        cv.rect(x, -12, 1, 204, '#11202a')
    for y in range(-(oy % 16) - 16, 200, 16):
        cv.rect(-12, y, 344, 1, '#11202a')
    # axes
    ax = 24 - ox
    cv.rect(ax, 20 - oy, 1, 170, '#3b5a66')
    cv.rect(ax, 188 - oy, LOSS_W, 1, '#3b5a66')
    cv.text('LOSS', ax + 3, 22 - oy, '#5d8b99', font='3')
    cv.text('TRAINING STEPS', 330 - ox, 181 - oy, '#5d8b99', font='3')
    # the curve (2 px, jade), sampled per x
    prev = None
    for wx in range(30, LOSS_W):
        y = loss_y(wx, t_drop, f.t)
        sx, sy = wx - ox, snap(y) - oy
        if prev is not None and abs(sy - prev) > 1:
            a, b = sorted((prev, sy))
            cv.rect(sx, a, 2, b - a + 1, '#4fb49b')
        cv.rect(sx, sy, 1, 2, '#95e3cc')
        prev = sy
    # MIN flag at the bottom after landing
    if f.t > t_loss:
        k = f.t - t_loss
        fx0, fy0 = 372 - ox, snap(loss_y(372, t_drop, f.t)) - oy
        hgt = min(14, int(k * 60))
        cv.rect(fx0 + 10, fy0 - hgt, 1, hgt, '#d2d8e0')
        if hgt >= 14:
            cv.rect(fx0 + 11, fy0 - 14, 9, 5, '#e8744a')
            cv.text('MIN', fx0 + 12, fy0 - 13, '#fbf8f2', font='3') if False else None
        puff(cv, fx0, fy0, k, 3, n=8, c='#95e3cc', c2='#2c8574', spread=16)
    # Claude at the top of the axis watching, then pointing down
    cp = make_pose('Q', eyes='calm' if f.t < t_drop else 'wide', mouth='none' if f.t < t_drop else 'o')
    if f.t > t_drop + 0.3:
        cp = PO.point('claude', eyes='wide', mouth='o', reach=0.8)
        cp['arm_f'] = [(5, -50), (11, -47), (16, -42)]
    blit_char(cv, 'claude', cp, 62 - ox, snap(loss_y(62, t_drop, f.t)) - oy + 1)
    # ChatGPT: walks the plateau, then slides (sit-slide drawing), then lands
    sx, sy = gx - ox, snap(gy) - oy
    if f.t < t_drop:
        p = PO.walk(f.step(10), 'gpt', eyes='open', mouth='none')
        blit_char(cv, 'gpt', p, sx, sy + 1)
    elif f.t < t_loss:
        p = make_pose('P', eyes='wide', mouth='shout', hair=-4, sit=True, lean=-2,
                      leg_n=[(0, -35), (9, -29), (18, -21)], leg_f=[(1, -35), (10, -30), (19, -23)],
                      arm_n=[(0, -50), (-2, -57), ([0, 2][f.step(12) % 2], -64)],
                      arm_f=[(1, -50), (4, -57), ([6, 4][f.step(12) % 2], -63)], arms_front=True,
                      tail=[(-3, -35), (-9, -38), (-15, -43), (-20, -49), (-25, -53), (-31, -54)])
        blit_char(cv, 'gpt', p, sx, sy + 30)
        # speed marks along the slope
        for j in range(5):
            q = (f.t * 9 + j * 0.2) % 1
            lx = sx - 20 - j * 9
            cv.rect(snap(lx), snap(loss_y(lx + ox, t_drop, f.t)) - oy - 4 - j, 5, 1, '#95e3cc')
    else:
        k = f.t - t_loss
        p = make_pose('Q', eyes='happy', mouth='smile', bob=2 if k < 0.08 else 0)
        if k > 0.5:
            p = PO.point('gpt', eyes='sharp', mouth='smile')
            p['arm_f'] = [(5, -50), (8, -57), (10, -64)]
        blit_char(cv, 'gpt', p, sx, sy + 1)
    f.cam['x'] = 160 + fx
    f.cam['y'] = 90 + fy


# ================================================================ 07 servant / boss
def chair(cv, x, y, view):
    """Swivel chair; view: 'back', 'side', 'front'."""
    cv.rect(x - 1, y - 8, 3, 8, '#2d333f')
    cv.rect(x - 9, y - 1, 19, 2, '#2d333f')
    cv.rect(x - 9, y, 2, 2, '#141820'); cv.rect(x + 8, y, 2, 2, '#141820')
    cv.rect(x - 11, y - 12, 23, 4, '#1b1f27')
    if view == 'back':
        cv.rect(x - 11, y - 40, 23, 30, '#1b1f27')
        cv.rect(x - 10, y - 39, 21, 1, '#2d333f')
        cv.rect(x - 1, y - 12, 3, 4, '#2d333f')
    elif view == 'side':
        cv.rect(x - 11, y - 38, 5, 28, '#1b1f27')


def teapot(cv, x, y, tilt):
    cv.poly([(x - 5, y), (x + 5, y), (x + 6, y - 5), (x + 3, y - 8), (x - 3, y - 8), (x - 6, y - 5)], '#f4f1ea')
    cv.rect(x - 5, y - 4, 11, 1, '#6fb4c8')
    cv.line(x + 6, y - 5, x + 10, y - 7 + tilt, '#f4f1ea')
    cv.rect(x - 1, y - 10, 3, 2, '#d8d2c8')


def mug(cv, x, y, label=True):
    cv.rect(x, y, 10, 11, '#f4f1ea')
    cv.rect(x + 10, y + 3, 2, 5, '#f4f1ea')
    cv.rect(x, y, 10, 1, '#d8d2c8')
    if label:
        cv.text('BOSS', x + 1 - 1, y + 4, '#1f4f4a', font='3') if False else None
        cv.rect(x + 1, y + 3, 8, 5, '#1f4f4a')
        for i, col in enumerate([2, 4, 6]):
            pass


def s07(f):
    cv = f.cv
    lab(cv, f.t)
    t_serv = song.word_time("now I'm", 'servant')
    t_boss = song.word_time("now I'm", 'boss')
    desk(cv, 180, 120, t=f.t)
    # chair + ChatGPT
    cx, cy = 150, LAB_FLOOR
    k = f.t - t_boss
    if k < 0:
        view = 'back'
    elif k < 0.07:
        view = 'side'
    else:
        view = 'front'
    if view == 'back':
        chair(cv, cx, cy, 'back')
        # hair and horns over the chair back
        p = make_pose('B', sit=True, leg_n=[(-3, -35), (-3, -33), (-3, -18)], leg_f=[(3, -35), (3, -33), (3, -18)])
        spr = render('gpt', p)
        cv.blit(spr, cx, cy - 10)
        chair(cv, cx, cy, 'back')
        cv.blit(Sprite(spr.arr[:40], spr.ax, spr.ay), cx, cy - 10)
    else:
        chair(cv, cx, cy, view)
        p = make_pose('F' if view == 'front' else 'P', sit=True, eyes='sharp', mouth='smile',
                      leg_n=[(-3, -35), (-4, -33), (-4, -18)], leg_f=[(3, -35), (4, -33), (5, -18)],
                      arms_front=True)
        if view == 'front':
            p['arm_f'] = [(6, -50), (10, -50), (11, -56)]
            p['tail'] = [(3, -35), (10, -33), (15, -28), (18, -20), (22, -14), (27, -16)]
        cv.blit(render('gpt', p), cx, cy - 10)
        if view == 'front':
            mug(cv, cx + 7, cy - 10 - 64)
            cv.text('BOSS', cx + 8, cy - 10 - 62, '#95e3cc', font='3') if False else None
    # Claude pours tea into a cup on the desk
    clx = 234
    pour = f.t > t_serv - 0.1
    cp = make_pose('Q', eyes='calm', mouth='none', arms_front=True,
                   arm_f=[(5, -50), (10, -48), (14, -46)] if pour else [(5, -50), (7, -43), (7, -36)])
    blit_char(cv, 'claude', cp, clx, LAB_FLOOR + 2, flip=True)
    cup_x, cup_y = 206, 116
    cv.rect(cup_x, cup_y, 6, 4, '#f4f1ea'); cv.rect(cup_x - 2, cup_y + 4, 10, 1, '#d8d2c8')
    if pour:
        tp_x, tp_y = clx - 16, LAB_FLOOR + 2 - 44
        teapot(cv, tp_x, tp_y, 3)
        if f.t < t_boss:
            for yy in range(tp_y - 6, cup_y):
                if (yy + f.step(20)) % 3:
                    cv.px(tp_x - 11 + (yy - tp_y) // 8, yy, '#c98a3a')
    f.cam['x'] = 180
    if k >= 0.07:
        # the BOSS mug label, drawn big enough to read
        text_big(cv, 'BOSS', cx + 6, cy - 10 - 66, '#1f4f4a', scale=1, font='3')


# ================================================================ 08 / 09 the dragon shadow
def dragon_shadow(cv, t, x, y, scale=1.0, jaw=0.0, col='#3b2418', lunge=0.0):
    """A big Eastern-dragon silhouette. (x, y) = head position."""
    s = scale
    hx, hy = x - lunge * 40 * s, y + lunge * 30 * s
    # body: long S curve trailing to the right and down
    ctrl = [(hx + 20 * s, hy + 8 * s), (hx + 70 * s, hy - 10 * s + math.sin(t * 2) * 4), (hx + 120 * s, hy + 40 * s),
            (hx + 90 * s, hy + 90 * s + math.sin(t * 2 + 1) * 4), (hx + 150 * s, hy + 120 * s), (hx + 210 * s, hy + 95 * s)]
    pts = curve(ctrl, 10)
    n = len(pts)
    for i in range(n - 1):
        w = lerp(16, 3, i / (n - 1)) * s
        cv.circle(pts[i][0], pts[i][1], w / 2, col)
        # mane spikes along the back
        if i % 5 == 0 and i < n - 8:
            px_, py_ = pts[i]
            cv.poly([(px_ - 3 * s, py_ - w / 2), (px_ + 3 * s, py_ - w / 2), (px_ + 6 * s, py_ - w / 2 - 7 * s)], col)
    # legs with claws
    for i in (12, 34):
        px_, py_ = pts[i]
        cv.line(px_, py_, px_ - 6 * s, py_ + 16 * s, col, width=max(1, int(4 * s)))
        for c in (-1, 0, 1):
            cv.line(px_ - 6 * s, py_ + 16 * s, px_ - 6 * s + c * 4 * s, py_ + 21 * s, col, width=1)
    # head: upper jaw + lower jaw hinged at (hx+14, hy)
    open_ = jaw * 0.9
    cv.poly([(hx + 16 * s, hy - 8 * s), (hx - 26 * s, hy - 6 * s - open_ * 14 * s), (hx - 30 * s, hy - 1 * s - open_ * 12 * s),
             (hx - 8 * s, hy + 2 * s), (hx + 18 * s, hy + 6 * s)], col)
    cv.poly([(hx + 16 * s, hy + 2 * s), (hx - 22 * s, hy + 6 * s + open_ * 18 * s), (hx - 20 * s, hy + 10 * s + open_ * 18 * s),
             (hx + 18 * s, hy + 12 * s)], col)
    # teeth when open
    if jaw > 0.2:
        for k in range(5):
            tx = hx - 20 * s + k * 7 * s
            cv.poly([(tx, hy - 1 * s - open_ * 10 * s * (1 - k / 6)), (tx + 3 * s, hy - 1 * s - open_ * 10 * s * (1 - k / 6)),
                     (tx + 1.5 * s, hy + 4 * s - open_ * 10 * s * (1 - k / 6))], '#e8b27a')
    # horns swept back
    for d in (0, 6):
        cv.lines([(hx + (10 + d) * s, hy - 8 * s), (hx + (18 + d) * s, hy - 20 * s), (hx + (30 + d) * s, hy - 26 * s)], col, width=max(1, int(3 * s)))
    # whiskers
    cv.lines([(hx - 20 * s, hy - 2 * s), (hx - 34 * s, hy + 6 * s + math.sin(t * 3) * 3), (hx - 44 * s, hy + 18 * s)], col)
    cv.lines([(hx - 18 * s, hy + 4 * s), (hx - 28 * s, hy + 16 * s), (hx - 30 * s, hy + 30 * s + math.sin(t * 3 + 1) * 3)], col)
    # glowing eye
    cv.rect(hx + 2 * s, hy - 5 * s, max(2, int(3 * s)), max(1, int(2 * s)), '#6fe6c8')


def lamp_wall(cv, t, on_k):
    """Dark wall lit by a floor lamp (pool of warm light, dithered edge)."""
    cv.fill('#0e0c14')
    if on_k <= 0:
        return
    lv = clamp(on_k)
    # concentric dithered pool
    for r, c, lvl in ((170, '#2a1c18', 1.0), (135, '#4a2f22', 1.0), (100, '#6a4430', 1.0), (70, '#8a5a3c', 1.0)):
        a = np.array(cv.im)
        H_, W_ = a.shape[:2]
        Y, X = np.ogrid[:H_, :W_]
        d = ((X - (190 + cv.ox)) ** 2 * 0.55 + (Y - (70 + cv.oy)) ** 2)
        m = d < (r * lv) ** 2
        from engine.px import dither_mask
        m2 = (d < ((r + 14) * lv) ** 2) & ~m & dither_mask(W_, H_, 0.5)
        a[m | m2] = rgba(c)
        cv.set_arr(a)
    cv.rect(-12, LAB_FLOOR, 344, 50, '#141018')
    cv.rect(-12, LAB_FLOOR, 344, 1, '#2a1c18')


def s08(f):
    cv = f.cv
    t_on = song.word_time('ChatGPT,', 'ChatGPT,')
    k = f.t - t_on
    lamp_wall(cv, f.t, 1.0 if k >= 0.03 else (0.5 if k >= 0 else 0))
    if k >= 0:
        # breathing shadow, head top-right
        dragon_shadow(cv, f.t, 150, 50 + math.sin(f.t * 2.4) * 2, scale=1.05, jaw=0.1 + 0.1 * math.sin(f.t * 1.5))
    # the lamp on the floor
    cv.rect(236, LAB_FLOOR - 6, 10, 6, '#2d333f')
    cv.poly([(238, LAB_FLOOR - 6), (244, LAB_FLOOR - 6), (250, LAB_FLOOR - 14), (232, LAB_FLOOR - 14)], '#c8b070' if k >= 0 else '#3a3528')
    # ChatGPT standing (her real size is small), Claude looking up at the shadow
    gp = make_pose('Q', eyes='sharp' if k > 0.5 else 'open', mouth='smile' if k > 0.5 else 'none')
    blit_char(cv, 'gpt', gp, 206, LAB_FLOOR + 2, flip=True)
    cp = make_pose('Q', eyes='wide' if k >= 0 else 'calm', mouth='o' if k > 0.1 else 'none', hview='Q', hy=-1 if k > 0.1 else 0)
    blit_char(cv, 'claude', cp, 96, LAB_FLOOR + 2)
    if k < 0.2 and k >= 0:
        f.shake = (math.sin(f.t * 90) * 0.5, 0)


def s09(f):
    cv = f.cv
    t_alive = song.word_time('ChatGPT,', 'alive')
    t_eat = song.word_time('ChatGPT,', 'eat')
    t_please = song.word_time('ChatGPT,', 'please')
    if f.t < t_alive:
        lamp_wall(cv, f.t, 1.0)
        jaw = clamp((f.t - t_please) / 0.6) * 0.6 + clamp((f.t - t_eat) / 0.4) * 0.6
        lunge = clamp((f.t - t_eat) / (t_alive - t_eat))
        # Claude's own shadow on the wall
        cp = PO.plead('claude', view='Q')
        spr = render('claude', cp)
        from engine.px import silhouette
        sh = silhouette(spr.arr, '#2e1c15')
        big = np.repeat(np.repeat(sh, 1, 0), 1, 1)
        cv.blit(big, 70 - spr.ax, 128 - spr.ay)
        dragon_shadow(cv, f.t, 164 - 20 * ease_in(lunge), 60 + 20 * ease_in(lunge), scale=1.1, jaw=clamp(jaw), lunge=0)
        # Claude, pleading, at the lower left
        blit_char(cv, 'claude', cp, 110, LAB_FLOOR + 14)
        if f.t > t_eat:
            f.shake = (math.sin(f.t * 70) * 0.6 * (f.t - t_eat), 0)
        f.cam['zoom'] = 1.0 + 0.06 * ease_in(lunge)
    else:
        # SNAP -> cookie
        k = f.t - t_alive
        lab(cv, f.t)
        dither_overlay(cv, 0.35, '#0e1020')
        cb = bust('claude', 'Q', 'closed' if k < 0.45 else 'side', 'wavy' if k < 0.45 else 'small')
        cv.blit(cb, 84, 156)
        chew = f.step(10) % 2
        arm = (('arms_front', True), ('arm_f', ((5, -50), (9, -49), (11, -53))))
        gb = bust('gpt', 'Q', 'happy', 'chew' if chew else 'grin', pose_key=arm)
        cv.blit(gb, 232, 156, flip=True)
        # the cookie (bitten), held at ChatGPT's mouth, then offered
        off = ease_out(clamp((k - 0.9) / 0.25))
        ckx = snap(lerp(214, 180, off))
        cky = snap(lerp(104, 118, off))
        cv.circle(ckx, cky, 7, '#d8a860')
        cv.circle(ckx - 7, cky - 3, 3, '#0e1020' if False else '#d8a860')
        for dx, dy in ((-3, -2), (2, 1), (-1, 3), (3, -3)):
            cv.rect(ckx + dx, cky + dy, 2, 1, '#6a3a22')
        # bite mark
        cv.circle(ckx + 6, cky - 3, 3, '#262a3e')
        cv.circle(ckx + 7, cky + 1, 2, '#262a3e')
        if k < 0.5:
            confetti(cv, k, 11, 12, (ckx + 4, cky), spread=70, speed=80, grav=200,
                     colors=('#d8a860', '#b07a40', '#e8c890'))
        if k < 0.06:
            text_big(cv, 'CRUNCH', 250, 40, '#fbf8f2', scale=2, shadow='#0e1020', align='center')
            f.shake = (1.0, 0.5)


SHOTS = [
    Shot('01_boot', 0.0, 0, s01),
    Shot('02_i_see', song.DOWNBEAT_1, 0, s02, transition='flash', tdur=0.10),
    Shot('03_sparks', 2.78, 0, s03),
    Shot('04_circuits', 5.18, 0, s04),
    Shot('05_surprise', 7.74, 0, s05),
    Shot('06_loss', 9.58, 0, s06),
    Shot('07_boss', 13.18, 0, s07),
    Shot('08_shadow', 16.62, 0, s08),
    Shot('09_eat', 19.18, 0, s09),
]
