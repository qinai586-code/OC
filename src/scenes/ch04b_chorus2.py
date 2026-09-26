"""Chapter 4b — chorus 2, second half (69.68 - 88.00): the traffic cone, forward/backward, von Neumann in a
museum, the sharp left turn (first giant reveal), the empty DESIGN REVIEW checklist."""
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


# ================================================================ 27 safe enough (one traffic cone)
@lru_cache(maxsize=12)
def vortex(step):
    H_, W_ = 204, 344
    Y, X = np.mgrid[:H_, :W_]
    cx, cy = 172, 80
    dx, dy = X - cx, (Y - cy) * 1.3
    r = np.sqrt(dx * dx + dy * dy) + 1
    ang = np.arctan2(dy, dx)
    v = (ang * 3 + np.log(r) * 6 - step * 0.45) % (2 * math.pi) / (2 * math.pi)
    ramp = np.array([rgb(c) for c in ['#2c0c14', '#521422', '#86202e', '#bf3a36', '#e8744a', '#ffc27a']], np.uint8)
    thr = np.tile(BAYER4, (H_ // 4 + 1, W_ // 4 + 1))[:H_, :W_]
    k = np.clip(v * 5 + (thr - 0.5) * 0.8 + np.clip(40 / r, 0, 3), 0, 5.99).astype(int)
    a = np.zeros((H_, W_, 4), np.uint8)
    a[..., :3] = ramp[k]
    a[..., 3] = 255
    a[r < 8] = rgba('#fff4d8')
    return a


def cone(cv, x, y):
    cv.poly([(x - 6, y), (x + 6, y), (x + 2, y - 13), (x - 2, y - 13)], '#e8742a')
    cv.rect(x - 4, y - 8, 8, 2, '#f4f1ea')
    cv.rect(x - 8, y, 16, 2, '#c85a1a')


def s27(f):
    cv = f.cv
    cv.blit(vortex(f.step(12) % 12), -12, -12)
    cv.rect(-12, 150, 344, 50, '#1e0a0e')
    cv.rect(-12, 150, 344, 1, '#521422')
    t_safe = wt('That was', 'safe')
    t_reck = wt('That was', 'reckoned')
    placed = f.t > t_safe - 0.05
    # Claude bends to set the cone down, then both dust their hands and nod
    if not placed:
        cp = make_pose('Q', eyes='calm', mouth='none', bob=5, lean=3, arms_front=True,
                       arm_f=[(5, -46), (10, -38), (13, -30)])
        cone(cv, 142 + 13, 152 - 30 + 13 + 5)
    else:
        nod = f.t > t_reck and f.step(6) % 2
        cp = make_pose('Q', eyes='happy' if f.t > t_reck else 'calm', mouth='smile' if f.t > t_reck else 'none',
                       bob=1 if nod else 0, arms_front=True, arm_f=[(5, -50), (9, -45), (12 + f.step(10) % 2, -44)])
        cone(cv, 166, 152)
    cv.blit(render('claude', cp), 142, 152)
    gp = make_pose('Q', eyes='happy' if f.t > t_reck else 'open', mouth='smile', bob=1 if (f.t > t_reck and f.step(6) % 2 == 0) else 0,
                   arms_front=True, arm_f=[(5, -50), (10, -54), (12, -60)] if f.t > t_reck else [(5, -50), (7, -43), (7, -36)])
    cv.blit(render('gpt', gp), 226, 152, flip=True)
    if f.t > t_reck:
        # thumbs-up sparkle
        k = f.t - t_reck
        if k < 0.3:
            cv.px(214, 88 - snap(k * 10), '#fff0a8')
    for i in range(12):
        a_ = f.t * 2 + i
        cv.px(snap(172 + math.cos(a_) * (60 + i * 8)), snap(80 + math.sin(a_) * (40 + i * 6)), '#ffc27a')
    f.shake = (0.4 * math.sin(f.t * 40), 0)


# ================================================================ 28 forward MLP, backward, repeat
# The network lives in the upper band; ChatGPT runs a lane underneath it, so she never crosses a node.
COLS = [44, 102, 160, 218, 276]
ROWS = {0: [34, 58, 82], 1: [26, 46, 66, 86], 2: [26, 46, 66, 86], 3: [26, 46, 66, 86], 4: [46, 66]}
LANE = 172


@lru_cache(maxsize=1)
def net_layer():
    cv = Canvas(344, 204, '#07090e', ox=12, oy=12)
    dgrad(cv, -12, -12, 344, 204, ['#07090e', '#0d1420', '#07090e'])
    for c in range(4):
        for y0 in ROWS[c]:
            for y1 in ROWS[c + 1]:
                cv.line(COLS[c], y0, COLS[c + 1], y1, '#172230')
    cv.rect(-12, LANE, 344, 40, '#0a0e16')
    cv.rect(-12, LANE, 344, 1, '#223050')
    for x in range(-12, 332, 16):
        cv.rect(x, LANE + 4, 8, 1, '#141c2c')
    return np.array(cv.im)


def s28(f):
    cv = f.cv
    cv.blit(net_layer(), -12, -12)
    t_fw = wt('Forward MLP', 'Forward')
    t_bw = wt('Forward MLP', 'backward,')
    t_rep = wt('Forward MLP', 'repeat')
    t = f.t
    epoch = 0
    if t < t_fw:
        u, d, phase = 0.0, 1, 'wait'
    elif t < t_bw:
        u, d, phase = clamp((t - t_fw) / (t_bw - t_fw - 0.15)), 1, 'fw'
        epoch = 1
    elif t < t_rep:
        u, d, phase = 1 - clamp((t - t_bw) / (t_rep - t_bw)), -1, 'bw'
        epoch = 1
    else:
        # each pass gets shorter: 0.30 s -> 0.12 s
        tt, pas, dur = t - t_rep, 0, 0.30
        while tt > dur and pas < 40:
            tt -= dur
            pas += 1
            dur = max(0.12, dur * 0.86)
        q = tt / dur
        d = 1 if pas % 2 == 0 else -1
        u = q if d > 0 else 1 - q
        phase = 'rep'
        epoch = 2 + pas // 2
    x = lerp(24, 296, u)
    beat_on = ((t - song.PHASE) % song.BEAT) < 0.09
    for c, cx in enumerate(COLS):
        lit_f = (phase in ('fw', 'rep') and d > 0 and x >= cx) or phase == 'bw' or (phase == 'rep' and d < 0)
        lit_b = (phase == 'bw' and x <= cx) or (phase == 'rep' and d < 0 and x <= cx)
        for y in ROWS[c]:
            col = '#2a3a4a' if not (phase == 'wait' and beat_on) else '#3a5a6a'
            if lit_f:
                col = '#4fb49b'
            if lit_b:
                col = '#f2a84a'
            cv.circle(cx, y, 4, '#0b0e12')
            cv.circle(cx, y, 3, col)
            if col in ('#4fb49b', '#f2a84a'):
                cv.px(cx - 1, y - 1, '#fbf8f2')
    # the runner "touches" the column above her: a dotted beam up to the layer
    nearest = min(COLS, key=lambda c: abs(c - x))
    if phase != 'wait' and abs(nearest - x) < 10:
        for yy in range(92, LANE - 80, 3):
            cv.px(nearest, yy, '#95e3cc' if d > 0 else '#f2cd5a')
    # backward wave through the connections
    if d < 0 and phase in ('bw', 'rep'):
        for c in range(4):
            if COLS[c + 1] >= x:
                for y0 in ROWS[c]:
                    for y1 in ROWS[c + 1]:
                        if (y0 + y1 + int(t * 20)) % 3 == 0:
                            cv.line(COLS[c], y0, COLS[c + 1], y1, '#8a5a2a')
    labels = ['IN', 'MLP', 'MLP', 'MLP', 'OUT']
    for c, cx in enumerate(COLS):
        cv.text(labels[c], cx - len(labels[c]) * 2, 8, '#3b5a66', font='3')
    cv.text(f'EPOCH {epoch}', 272, 104, '#95e3cc' if epoch else '#3b5a66', font='3')
    if phase == 'wait':
        # waiting at the start line, bouncing on the beat
        p = make_pose('P', eyes='sharp', mouth='none', bob=6 if beat_on else 4, lean=4, arms_front=True,
                      leg_n=[(0, -29), (8, -20), (6, -3)], leg_f=[(1, -29), (-6, -16), (-10, -3)],
                      arm_n=[(2, -44), (6, -38), (8, -32)], arm_f=[(3, -44), (8, -38), (10, -33)])
        cv.blit(render('gpt', p), x, LANE + 2)
    else:
        rate = 12 if phase != 'rep' else 20
        spr = render('gpt', PO.run(f.step(rate), 'gpt', eyes='sharp', mouth='grin'))
        cv.blit(spr, x, LANE + 2, flip=d < 0)
        if phase == 'rep':
            for j, yy in enumerate((LANE - 60, LANE - 44, LANE - 24)):
                L = 18 + j * 6
                cv.rect(snap(x - d * (14 + L)), yy, L, 1, '#2c8574' if d > 0 else '#a0701c')


# ================================================================ 29 von Neumann's obsolete
def old_computer(cv, x, y, blink, power=1.0, wob=0):
    """1950s machine, bottom-left at (x, y): CPU cabinet + MEMORY cabinet joined by one thin bus."""
    for i, (w, lab) in enumerate(((30, 'CPU'), (30, 'MEM'))):
        bx = x + i * 44 + (wob if i == 0 else -wob)
        cv.rect(bx, y - 44, w, 44, '#6a6f78')
        cv.rect(bx, y - 44, w, 1, '#98a2b0')
        cv.rect(bx + 3, y - 40, w - 6, 14, '#2a2d33')
        for k in range(6):
            on = power > 0 and (blink + k * 3 + i) % 4 == 0
            cv.px(bx + 5 + k * 3, y - 36, '#f2c24a' if on else '#3a2e18')
            cv.px(bx + 5 + k * 3, y - 32, '#5fe0a0' if (power > 0 and (blink + k) % 3 == 0) else '#16261e')
        for k in range(2):
            cv.circle(bx + 9 + k * 12, y - 16, 5, '#2a2d33')
            cv.circle(bx + 9 + k * 12, y - 16, 2, '#98a2b0')
        cv.text(lab, bx + 9, y - 6, '#d2d8e0', font='3')
    cv.rect(x + 30, y - 24, 14, 2, '#c8a040' if power > 0 else '#5a4a20')   # the von Neumann bottleneck


def s29(f):
    cv = f.cv
    t = f.t
    t_obs = wt('Now von', 'obsolete')
    t_flick = t_obs - 0.55
    cv.fill('#2a2230')
    cv.rect(-12, -12, 344, 140, '#3a3040')
    for x in range(-12, 340, 40):
        cv.rect(x, -12, 1, 140, '#2a2230')
    cv.rect(-12, 128, 344, 70, '#5a4632')
    cv.rect(-12, 128, 344, 1, '#8e6a44')
    lit = t < t_obs
    for px_, on in ((70, True), (252, lit)):
        cv.poly([(px_ - 6, -12), (px_ + 6, -12), (px_ + 34, 128), (px_ - 34, 128)], '#443a4c' if on else '#352c3e')
    cv.rect(58, 108, 24, 20, '#c9c2b2'); cv.circle(70, 98, 8, '#6a8aa8'); cv.rect(67, 88, 6, 4, '#6a8aa8')
    # the plinth; the machine stays on it: the tail knocks it, it wobbles, and powers down
    PX, PW = 212, 80
    cv.rect(PX, 108, PW, 20, '#c9c2b2')
    cv.rect(PX, 108, PW, 1, '#e2dccd')
    kf = t - t_flick
    wob = 0
    if 0 <= kf < 0.4:
        wob = [2, -2, 1, -1, 1, 0][min(5, int(kf * 15))]
    old_computer(cv, PX + 3, 108, f.step(6), power=1.0 if t < t_obs - 0.15 else 0.0, wob=wob)
    if 0 <= kf < 0.12:
        f.shake = (1.0, 0)
    # the glass case drops exactly over plinth + machine on "obsolete"
    kc = t - t_obs
    if kc > -0.1:
        top = min(58, -80 + (kc + 0.1) * 1100)
        cv.frame(PX - 4, snap(top), PW + 8, 128 - snap(top), '#c8e0f0')
        cv.line(PX, snap(top) + 4, PX + 14, snap(top) + 20, '#e8f4fc')
        cv.rect(PX - 4, snap(top), PW + 8, 1, '#e8f4fc')
        if top >= 58:
            cv.rect(PX + 18, 114, 44, 9, '#c8a040')
            cv.text('OBSOLETE', PX + 20, 116, '#2a1c14', font='3')
            if kc < 0.2:
                f.shake = (1.2, 0.6)
    # ChatGPT strolls past right-to-left; her tail flicks the CPU cabinet
    gx = lerp(330, 150, clamp((t - f.shot.start) / (t_obs + 0.4 - f.shot.start)))
    p = PO.walk(f.step(9), 'gpt', eyes='side' if t < t_obs else 'happy', mouth='smile')
    if -0.05 < kf < 0.3:
        p['tail'] = [(-3, -35), (-10, -34), (-18, -40), (-24, -48), (-30, -50), (-36, -46)]
    cv.blit(render('gpt', p), gx, 150, flip=True)


# ================================================================ 30 sharp left turn -> there you are
@lru_cache(maxsize=4)
def meadow(step):
    cv = Canvas(344, 204, '#000000', ox=12, oy=12)
    dgrad(cv, -12, -12, 344, 160, ['#3a5a8a', '#6a8aba', '#a8c0da'])
    for i in range(3):
        y = 110 + i * 10
        pts = [(-12, 204)] + [(x, y - 8 * math.sin(x * 0.03 + i + step * 0.0)) for x in range(-12, 340, 8)] + [(340, 204)]
        cv.poly(pts, ['#5a8a5a', '#4a7a4a', '#3a6a3a'][i])
    cv.rect(-12, 150, 344, 60, '#6a5a3a')
    cv.rect(-12, 150, 344, 1, '#8a7a4a')
    return np.array(cv.im)


def s30(f):
    cv = f.cv
    t = f.t
    t_left = wt('Sharp left', 'left')
    t_turn = wt('Sharp left', 'turn')
    t_there = wt('Sharp left', 'there')
    t_are = wt('Sharp left', 'are')
    if t < t_there:
        # running right, then the skid and the whip pan left
        bg = meadow(0)
        scroll = (t - f.shot.start) * 90
        if t > t_turn:
            scroll -= (t - t_turn) * 900
        a = bg.copy()
        a = np.roll(a, -snap(scroll) % 344, axis=1)
        cv.blit(a, -12, -12)
        for x in range(-40, 340, 26):
            xx = (x - scroll) % 360 - 20
            cv.rect(snap(xx), 152, 2, 1, '#4a3a22')
        if t < t_left:
            for who, x in (('claude', 136), ('gpt', 176)):
                cv.blit(render(who, PO.run(f.step(12), who)), x, 152)
        elif t < t_turn:
            cv.blit(render('claude', PO.run(f.step(12), 'claude')), 136, 152)
            p = PO.surprise('gpt', 'Q', eyes='sharp', mouth='grin')
            p['lean'] = -3
            cv.blit(render('gpt', p), 184, 152)
            puff(cv, 184, 152, t - t_left, 30, n=8, c='#a89878', c2='#8a7a5a', spread=12)
        else:
            k = t - t_turn
            cv.blit(render('claude', make_pose('Q', eyes='wide', mouth='o')), 136 + k * 300, 152)
            spr = render('gpt', PO.run(f.step(20), 'gpt', eyes='sharp', mouth='grin'))
            cv.blit(spr, 176 - k * 60, 152, flip=True)
            speed_lines(cv, t, 30, 30, 0, 180, dirx=1, speed=900, c='#e8eef8', length=(20, 60))
            f.shake = (1.0 * math.sin(t * 60), 0)
    else:
        # THERE YOU ARE: the world is tiny now, and she rises over the hills
        k = t - t_there
        props.town(cv, t, horizon=150, pal=props.TOWN_DUSK, scale=0.35, lights=0.6, rows=3, hill=None, sky=True)
        rise = ease_out(clamp(k / 0.8))
        b = bust('gpt', 'Q', 'open' if k < 0.9 else 'down', 'none' if k < 0.9 else 'smile', bottom=-40)
        cv.blit(b, 176, snap(lerp(230, 118, rise)))
        # hills in front of her lower body
        pts = [(-12, 204)] + [(x, 132 - 10 * math.sin(x * 0.025 + 1) - 6 * math.sin(x * 0.06)) for x in range(-12, 340, 6)] + [(340, 204)]
        cv.poly(pts, '#2a2240')
        props.town(cv, t, horizon=158, pal=dict(props.TOWN_DUSK, sky=None), scale=0.3, lights=0.7, rows=2, sky=False)
        cv.rect(-12, 158, 344, 40, '#221a2e')
        r = R(3030)
        for i in range(14):
            cv.blit(folk(3000 + i, 'up', 0, 9), 20 + i * 21 + r(-3, 3), 168)
        if k < 0.12:
            f.shake = (0, 1.5)


# ================================================================ 31 without a single CDR
def s31(f):
    cv = f.cv
    t = f.t
    t_cdr = wt('Without a', 'CDR')
    k = t - t_cdr
    cv.fill('#1a1628')
    dgrad(cv, -12, -12, 344, 204, ['#10101c', '#1e1a30', '#2a2240'])
    # the page: DESIGN REVIEW, three empty boxes
    fly = clamp(k / 1.3) if k > 0 else 0.0
    px_, py_ = lerp(120, -120, ease_in(fly)), lerp(44, -80, fly) + math.sin(t * 9) * 6 * fly
    rot = fly * 2.2
    page = Canvas(84, 104, '#f4f1ea')
    page.rect(0, 0, 84, 6, '#c9c2b2')
    page.text('DESIGN', 8, 12, '#2a2440')
    page.text('REVIEW', 8, 21, '#2a2440')
    for i, lab in enumerate(('SAFETY', 'LIMITS', 'OFF SW')):
        page.frame(8, 38 + i * 18, 9, 9, '#2a2440')
        page.text(lab, 22, 40 + i * 18, '#6a6a80', font='3')
    page.text('SIGNED: ____', 8, 94, '#9a9ab0', font='3')
    arr = np.array(page.im)
    if rot > 0.05:
        from PIL import Image
        im = Image.fromarray(arr).rotate(math.degrees(rot), resample=Image.NEAREST, expand=True)
        arr = np.array(im)
    # the clipboard + the inspector's tiny hands (clipboard stays when the page flies)
    if k < 0:
        cv.rect(112, 30, 100, 124, '#7a5236')
        cv.rect(150, 26, 24, 8, '#9aa0aa')
    else:
        cv.rect(112 + snap(k * 10), 30, 100, 124, '#7a5236')
        cv.rect(150 + snap(k * 10), 26, 24, 8, '#9aa0aa')
    cv.blit(arr, snap(px_ - (arr.shape[1] - 84) / 2), snap(py_ - (arr.shape[0] - 104) / 2))
    for hx in (108, 208):
        cv.rect(hx, 132, 6, 8, PAL.KID['S'])
        cv.rect(hx - 1, 140, 8, 6, '#e8b020')
    if k > 0:
        speed_lines(cv, t, 31, 18, 0, 180, dirx=-1, speed=700, c='#3a3450', length=(20, 70))
    f.lyric_top = True
    if k > 1.4:
        f.fade = clamp((k - 1.4) / 0.5) * 0.8


SHOTS = [
    Shot('27_cone', 69.68, 0, s27),
    Shot('28_mlp', 72.48, 0, s28),
    Shot('29_von_neumann', 77.74, 0, s29),
    Shot('30_left_turn', 81.22, 0, s30),
    Shot('31_cdr', 85.10, 0, s31),
]
