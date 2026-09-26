"""Chapter 5 — bridge + chorus 3 (88.00 - 110.14): the cat on the cliff, the fall past knob #3, the kid's room
filling with paperclips, the empty kill-switch office, the flooded town, the FOOM fuse, the orthogonality
blues, and the push into ChatGPT's eye that carries us into the rap."""
import math
from functools import lru_cache
import numpy as np
from engine.film import Shot
from engine.px import rgb, rgba, Sprite, Canvas, dither_mask, silhouette, BAYER4
from engine.scalex import scale2x
from art.body import render, make_pose, Paint, poly_mask, ellipse_mask, limb_mask, shift, edge, curve
from art.body import AX as BAX, AY as BAY, SW as BSW, SH as BSH
from art import poses as PO
from art.portrait import bust
from art.ecu import draw_eye
from art import palette as PAL
from scenes.kit import *
from scenes.props import knob, town, TOWN_NIGHT, paperclip, paperclip_field, CLIP, CLIP_HI, CLIP_LO
import song

G, C = PAL.GPT, PAL.CLAUDE
N = PAL.NIGHT
WT = song.word_time


def wt(prefix, word):
    return song.word_time(prefix, word)


# ------------------------------------------------------------------ small shared helpers
def cached_layer(fn):
    """Decorator: fn(*args) draws onto a fresh canvas; returns an RGBA array blitted at (-12, -12)."""
    @lru_cache(maxsize=16)
    def inner(*args):
        cv = Canvas(344, 204, None, ox=12, oy=12)
        fn(cv, *args)
        return np.array(cv.im)
    return inner


def put_layer(cv, arr):
    cv.blit(arr, -12, -12)


def wind(cv, t, seed, n, y0, y1, speed=260, cols=('#222849', '#303a63'), length=(10, 34), dirx=1):
    r = R(seed)
    for k in range(n):
        y = r(y0, y1)
        L = r(*length)
        sp = speed * r(0.7, 1.3)
        x = (r(0, 400) + dirx * sp * t) % 400 - 40
        cv.rect(snap(x), snap(y + math.sin(t * 2 + k) * 2), snap(L), 1, cols[k % len(cols)])


def downsample(arr, k):
    """Nearest-neighbour shrink of an RGBA sprite array by factor k (<1)."""
    h, w = arr.shape[:2]
    nh, nw = max(1, int(h * k)), max(1, int(w * k))
    ys = (np.arange(nh) / k).astype(int).clip(0, h - 1)
    xs = (np.arange(nw) / k).astype(int).clip(0, w - 1)
    return arr[ys[:, None], xs[None, :]]


def glint(cv, x, y, k, c='#fbf8f2', c2='#98a2b0'):
    """4-point sparkle, size k (0..1)."""
    if k <= 0:
        return
    L = 1 + int(k * 4)
    cv.rect(x - L, y, 2 * L + 1, 1, c2)
    cv.rect(x, y - L, 1, 2 * L + 1, c2)
    cv.rect(x - L // 2, y, L + 1, 1, c)
    cv.rect(x, y - L // 2, 1, L + 1, c)


# ================================================================== Claude hanging (one arm up)
HANG_ARM = ((6, -50), (10, -62), (12, -76))
HANG_HAND = (12, -75)          # local sprite coords of the gripping hand


def hang_pose(frame=0, eyes='worried', mouth='o', hair=0):
    """Front view, far arm straight up (the grip), near arm and legs dangling. frame 0..2 = swing drawings."""
    k = frame % 4
    sw = [0, 1, 0, -1][k]
    p = make_pose('F', eyes=eyes, mouth=mouth, hair=hair + sw)
    p['arm_f'] = list(HANG_ARM)
    p['arm_n'] = [(-6, -50), (-9, -44), (-10 + sw, -37)]
    p['leg_n'] = [(-3, -35), (-4 + sw, -20), (-4 + sw * 2, -5)]
    p['leg_f'] = [(3, -35), (4 + sw, -21), (6 + sw * 2, -7)]
    return p


# ================================================================== the cat (gato)
CAT = dict(o='#040406', k='#101118', K='#1e2130', r='#3a4266', R='#5a6690', eye='#e8d860', eye2='#a8a030',
           pupil='#040406', hi='#fbf8f2', nose='#b86a7a', ear='#2a1c28', wh='#8a92b0')


@lru_cache(maxsize=64)
def cat_sprite(s=2, head='down', eyes='slit', paw=None):
    """A small black cat sitting, facing right. s = scale (1 wide shots, 2 close-ups).
    head: 'down' (looking down-right), 'back' (looking back over its shoulder, left), 'front'.
    eyes: 'slit' | 'round' (dilated) | 'closed' | 'half'.
    paw: None (both paws planted) or (dx, dy) target of the far front paw in unit coords."""
    P = Paint()
    K = CAT

    def S(pts):
        return [(x * s, y * s) for x, y in pts]

    def rim(m):
        # backlit: moon-cool rim along top and left edges
        top = m & ~shift(m, 0, 1)
        left = m & ~shift(m, 1, 0)
        P.put((top | left) & ~edge(m) | (top & left), K['r'])

    # tail wrapping round the front along the ground
    tl = curve(S([(-9, -2), (-13, -2), (-12, 0), (-5, 0), (3, 0), (8, -1)]), 6)
    mt = limb_mask(tl, [max(2, round(2.2 * s))] * len(tl))
    P.part(mt, K['k'], line=K['o'])
    rim(mt)
    # haunch + torso
    mb = ellipse_mask(-5 * s, -5 * s, 7 * s, 5.2 * s)
    mb |= poly_mask(S([(-11, -3), (-10, -9), (-6, -15), (-1, -19), (3, -19.5), (5.5, -15), (5.5, -8), (4.5, -1), (-2, 0), (-10, 0)]))
    # far front leg (drawn first so the body covers the shoulder)
    if paw is not None:
        tx, ty = paw
        sh = (2.5, -12)
        el = ((sh[0] + tx) / 2 + 0.5, min(sh[1], ty) - 2.5 if ty < -3 else (sh[1] + ty) / 2 - 1)
        ml = limb_mask(S([sh, el, (tx, ty)]), [round(2.6 * s), round(2.4 * s), round(2.2 * s)])
        ml |= ellipse_mask(tx * s, ty * s, 1.6 * s, 1.2 * s)
        P.part(ml, K['k'], line=K['o'])
        rim(ml)
    P.part(mb, K['k'], line=K['o'])
    rim(mb)
    # near front leg (planted)
    mn = limb_mask(S([(3.2, -11), (4.2, -5), (4.3, -1)]), [round(2.8 * s), round(2.5 * s), round(2.4 * s)])
    mn |= ellipse_mask(4.8 * s, -0.8 * s, 1.7 * s, 1.0 * s)
    P.part(mn, K['k'], line=K['o'])
    P.put(mn & ~shift(mn, 1, 0) & ~edge(mn), K['K'])
    if paw is None:
        mf = ellipse_mask(1.5 * s, -0.8 * s, 1.6 * s, 1.0 * s)
        P.part(mf & ~mn, K['k'], line=K['o'])
    # head
    if head == 'back':
        hc = (0.5, -22.5)
        ears = [[(-4.5, -24.5), (-5.8, -31), (-1.2, -27.2)], [(1.5, -27.6), (4.5, -31.5), (5.2, -24.5)]]
    elif head == 'front':
        hc = (2.5, -22.5)
        ears = [[(-2.6, -25), (-3.2, -31.5), (1.4, -27.6)], [(3.6, -27.6), (8.2, -31.5), (7.6, -25)]]
    else:
        hc = (3.2, -21.8)
        ears = [[(-1.6, -24.6), (-2.4, -31), (2.2, -27.4)], [(4.2, -27.2), (8.6, -30.6), (8.4, -24.2)]]
    mh = ellipse_mask(hc[0] * s, hc[1] * s, 5.8 * s, 5.0 * s)
    # cheeks / muzzle bulge toward the look direction
    mdir = -1 if head == 'back' else 1
    mh |= ellipse_mask((hc[0] + 1.6 * mdir) * s, (hc[1] + 1.4) * s, 4.4 * s, 3.6 * s)
    me = np.zeros_like(mh)
    for e in ears:
        me |= poly_mask(S(e))
    P.part(me | mh, K['k'], line=K['o'])
    rim(me | mh)
    # inner ears
    for e in ears:
        cx_ = sum(p[0] for p in e) / 3
        cy_ = sum(p[1] for p in e) / 3
        ie = poly_mask([((x - cx_) * 0.45 + cx_) * s for x, _ in e] and [(((x - cx_) * 0.45 + cx_) * s, ((y - cy_) * 0.45 + cy_) * s) for x, y in e])
        P.put(ie & ~edge(me | mh), K['ear'])
    # eyes
    if head == 'back':
        eyes_at = [(hc[0] - 3.0, hc[1] - 0.3), (hc[0] + 0.8, hc[1] - 0.3)]
        look = (-0.6, 0.0)
        nose = (hc[0] - 3.8, hc[1] + 2.6)
    elif head == 'front':
        eyes_at = [(hc[0] - 2.2, hc[1] - 0.2), (hc[0] + 2.2, hc[1] - 0.2)]
        look = (0.0, 0.0)
        nose = (hc[0], hc[1] + 2.4)
    else:
        eyes_at = [(hc[0] - 0.4, hc[1] - 0.2), (hc[0] + 3.4, hc[1] - 0.2)]
        look = (0.5, 0.5)
        nose = (hc[0] + 4.4, hc[1] + 2.4)
    for i, (ex, ey) in enumerate(eyes_at):
        rx = 1.5 * s * (0.8 if (head == 'down' and i == 1) or (head == 'back' and i == 0) else 1.0)
        ry = 1.35 * s
        if eyes == 'closed':
            P.put(poly_mask([(ex * s - rx, ey * s + 0.5), (ex * s + rx, ey * s + 0.5), (ex * s + rx, ey * s + 1), (ex * s - rx, ey * s + 1)]), K['eye2'])
            continue
        em = ellipse_mask(ex * s, ey * s, rx, ry)
        if eyes == 'half':
            em &= ~poly_mask([(ex * s - 5, ey * s - 5), (ex * s + 5, ey * s - 5), (ex * s + 5, ey * s - 0.2), (ex * s - 5, ey * s - 0.2)])
        P.put(em, K['eye'])
        P.put(em & ~shift(em, 0, -1), K['eye2'])
        px_, py_ = ex + look[0] * 0.5, ey + look[1] * 0.4
        if eyes == 'round':
            pm = ellipse_mask(px_ * s, py_ * s, max(0.6, 0.95 * s), max(0.6, 1.0 * s)) & em
        else:
            pm = poly_mask([(px_ * s - 0.3, py_ * s - ry), (px_ * s + 0.6 * (s > 1), py_ * s - ry),
                            (px_ * s + 0.6 * (s > 1), py_ * s + ry), (px_ * s - 0.3, py_ * s + ry)]) & em
        P.put(pm, K['pupil'])
        if s > 1 and eyes != 'half':
            P.put(ellipse_mask((ex - 0.5) * s, (ey - 0.5) * s, 0.4, 0.4) & em, K['hi'])
    if s > 1:
        P.put(ellipse_mask(nose[0] * s, nose[1] * s, 0.8, 0.5), K['nose'])
        # whiskers (moonlit)
        wd = -1 if head == 'back' else 1
        bx, by = nose[0] * s, (nose[1] + 0.6) * s
        for dy in (-1, 1):
            m = limb_mask([(bx - wd * 1, by), (bx + wd * 5, by + dy * 1.5), (bx + wd * 9, by + dy * 2.5)], [1, 1, 1], caps=False)
            P.put(m & ~mh | (m & edge(mh)), K['wh'])
    return P.sprite()


# ================================================================== 32 "Gato, please don't let me go"
ROCK = dict(k='#07070d', d='#0f121d', m='#171b2b', l='#232a40', rim='#46568a', rim2='#6a7fb4')


def night_sky(cv, top='#0e1020', mid='#1b2140', low='#07070d', horizon=110):
    dgrad(cv, -12, -12, 344, horizon + 12, [top, '#141830', mid])
    dgrad(cv, -12, horizon, 344, 204 - horizon - 12, [mid, '#11152a', low])


def town_lights(cv, x0, x1, y0, y1, seed, n=60):
    r = R(seed)
    for i in range(n):
        x = r(x0, x1)
        y = r(y0, y1)
        c = '#f2c24a' if r() < 0.6 else '#e89a3a'
        cv.px(snap(x), snap(y), c)


def cliff_mass(cv, corner, seed=5, bottom=200, s=1):
    """Plateau on the left, sheer wall descending from `corner`, rock filling the lower left."""
    cx, cy = corner
    r = R(seed)
    # plateau surface (slightly bumpy), from left edge to corner
    top = [(-14, cy + 3)]
    for x in range(-12, int(cx) - 2, 6):
        top.append((x, cy + (1 if (x // 6) % 3 == 0 else 0)))
    top.append((cx - 2, cy))
    # wall profile going down (jagged)
    wall = []
    y = cy
    x = cx
    while y < bottom + 10:
        wall.append((x, y))
        y += r(6, 14) * s
        x = cx + r(-3, 2) * s - (y - cy) * 0.03
    pts = top + wall + [(wall[-1][0], bottom + 12), (-14, bottom + 12)]
    cv.poly(pts, ROCK['d'])
    # strata
    for i in range(10):
        yy = cy + 8 * s + i * 11 * s
        cv.line(-12, yy + r(-2, 2), cx - 6 - r(0, 20), yy + r(-2, 2), ROCK['m'])
    # moonlit top edge and wall rim
    cv.lines([(x, y) for x, y in top], ROCK['rim'])
    cv.lines([(x, y - 1) for x, y in top[1:]], ROCK['l'])
    cv.lines(wall[:6], ROCK['l'])
    cv.px(cx - 2, cy, ROCK['rim2'])


@cached_layer
def s32_wide_bg(cv):
    night_sky(cv, horizon=96)
    stars(cv, 32, 60, 0.0, -12, -12, 344, 100, twinkle=False)
    moon(cv, 92, 30, 13)
    # far hills / abyss fog on the right
    for i, (y, c) in enumerate(((128, '#10132a'), (140, '#0b0d1c'), (152, '#07070d'))):
        pts = [(170, 204)]
        for x in range(170, 340, 10):
            pts.append((x, y + 5 * math.sin(x * 0.07 + i * 2)))
        pts.append((340, 204))
        cv.poly(pts, c)
    town_lights(cv, 214, 330, 142, 158, 7, 45)
    cliff_mass(cv, (172, 74), seed=5)


@cached_layer
def s32_cu_bg(cv):
    night_sky(cv, horizon=120)
    stars(cv, 33, 40, 0.0, -12, -12, 344, 100, twinkle=False)
    moon(cv, 126, 52, 32)
    cliff_mass(cv, (176, 100), seed=9, s=2)
    # rock texture on the plateau lip
    for x in range(-10, 170, 13):
        cv.rect(x, 104 + (x * 7) % 5, 6, 1, ROCK['m'])


def s32(f):
    cv = f.cv
    t = f.t
    t_gato, t_please = wt('Gato', 'Gato'), wt('Gato', 'please')
    t_dont, t_let = wt('Gato', "don't"), wt('Gato', 'let')
    t_me, t_go = wt('Gato', 'me'), wt('Gato', 'go')
    t_fall = t_go + 0.16                           # the overhead fall shot
    swing = f.step(5) % 4
    if t < t_gato - 0.02:
        # ---------------------------------------------------------- WIDE: the dangling, the wind
        put_layer(cv, s32_wide_bg())
        wind(cv, t, 3201, 14, 10, 150, speed=220)
        # paperclip on the plateau (catching the moon)
        paperclip(cv, 140, 73, 0.1, 1.0)
        glint(cv, 144, 71, pulse((t - 88.9) % 1.3, 0.4))
        # the cat sitting at the edge, paw on her hand
        cv.blit(cat_sprite(1, 'down', 'slit' if (f.step(3) % 9) else 'closed', paw=(10.5, -1.5)), 160, 74)
        # Claude hanging off the edge (flipped: grip arm on screen-left)
        hp = hang_pose(swing, eyes='worried', mouth='none', hair=-2)
        gx, gy = 173, 74
        cv.blit(render('claude', hp), gx + HANG_HAND[0] + [0, 1, 0, -1][swing] * 0, gy - HANG_HAND[1], flip=True)
        k = ease_io(f.lt / (t_gato - f.shot.start))
        f.cam['zoom'] = 1.0 + 0.10 * k
        f.cam['x'], f.cam['y'] = lerp(160, 172, k), lerp(90, 98, k)
        return
    if t < t_fall:
        # ---------------------------------------------------------- CLOSE TWO-SHOT: cat, hand, Claude, paperclip
        put_layer(cv, s32_cu_bg())
        wind(cv, t, 3202, 10, 108, 175, speed=260, cols=('#222849', '#1b2140'))
        # the shiny paperclip behind the cat
        clip_x, clip_y = 62, 98
        paperclip(cv, clip_x, clip_y, 0.15, 2.0)
        sh = 0.4 + 0.6 * pulse(t - t_dont, 0.6) + 0.3 * pulse((t - 90.2) % 1.7, 0.3)
        glint(cv, clip_x + 8, clip_y - 3, sh)
        # cat acting
        if t < t_dont:
            head, eyes = 'down', ('half' if t > t_please + 0.3 and t < t_please + 0.8 else 'slit')
            if t_please + 0.45 < t < t_please + 0.6:
                eyes = 'closed'           # slow blink
        elif t < t_let:
            head, eyes = 'back', 'round'
        else:
            head, eyes = 'down', 'slit' if t < t_me else 'round'
        # paw: resting on her wrist; tap on "me", decisive pat on "go"
        rest = (11.2, -0.9)
        paw = rest
        km, kg = t - t_me, t - t_go
        if 0 <= km < 0.18:
            paw = (rest[0] - 0.4, rest[1] - 3.5 * math.sin(km / 0.18 * math.pi))
        if kg >= -0.1:
            if kg < 0.0:
                paw = (rest[0] - 1.2, rest[1] - 5.0)     # wind-up
            elif kg < 0.06:
                paw = (rest[0] + 0.8, rest[1] + 0.2)     # PAT
            else:
                paw = (rest[0] + 1.6, rest[1] + 0.4)
        catx, caty = 150, 100
        cv.blit(cat_sprite(2, head, eyes, paw=paw), catx, caty)
        # Claude
        slip = 0.0 if kg < 0.03 else ease_in((kg - 0.03) / 0.11)
        hx, hy = 177, 98 + snap(slip * 120)
        e = 'worried'
        m = 'o' if (t_gato <= t < t_gato + 0.5) or (t_please <= t < t_please + 0.9) else 'frown'
        if t > t_dont:
            e, m = 'side', 'none'           # follows the cat's gaze to the clip
        if t > t_let:
            e, m = 'worried', 'wavy'
        if t > t_me:
            e, m = 'wide', 'o'
        if kg > 0.03:
            e, m = 'wide', 'shout'
        b = bust('claude', 'F', e, m, pose_key=(('arm_f', HANG_ARM), ('hair', -2 + swing % 2)), bottom=-30)
        cv.blit(b, hx + 24, hy + 44, flip=True)
        # the paw again on top of her hand
        if paw is not None:
            pxx, pyy = catx + paw[0] * 2, caty + paw[1] * 2
            if kg < 0.03:
                cv.circle(pxx, pyy, 3, CAT['k'])
                cv.rect(snap(pxx) - 2, snap(pyy) - 3, 4, 1, CAT['r'])
        if 0 <= kg < 0.08:
            f.shake = (1.0, 0.0)
        # paw insert: chunky punch-in from "me" to the pat
        if t >= t_me - 0.02:
            f.cam['zoom'] = 2.0
            f.cam['x'], f.cam['y'] = 170, 94
        else:
            k = ease_io((t - t_gato) / (t_me - t_gato))
            f.cam['zoom'] = 1.0 + 0.06 * k
            f.cam['x'], f.cam['y'] = lerp(160, 158, k), lerp(90, 92, k)
        return
    # -------------------------------------------------------------- OVERHEAD: she falls away into the dark
    s32_fall(f, t - t_fall)


@cached_layer
def s32_down_bg(cv):
    # looking straight down the cliff: wall on the left converging to a vanishing point far below
    vx, vy = 206, 128
    dgrad(cv, -12, -12, 344, 204, ['#171b33', '#0e1020', '#07070d', '#07070d'])
    # the town, tiny, at the bottom of the drop
    for i in range(70):
        r = R(900 + i)
        a = r(0, 6.28)
        d = r(2, 26)
        cv.px(snap(vx + math.cos(a) * d * 1.3), snap(vy + math.sin(a) * d * 0.8), '#f2c24a' if i % 3 else '#e89a3a')
    # wall: a wedge from the top-left converging to the vanishing point
    cv.poly([(-14, -14), (140, -14), (vx - 4, vy - 2), (-14, 204)], ROCK['d'])
    for k in range(9):
        u = k / 9
        cv.line(lerp(-12, 140, u), -12, vx - 4, vy - 2, ROCK['m'])
    cv.line(140, -14, vx - 4, vy - 2, ROCK['l'])
    # speed marks along the wall (static part)
    # the lip of the ledge along the top edge, seen from above
    cv.poly([(-14, -14), (334, -14), (334, 6), (180, 10), (100, 8), (-14, 12)], ROCK['m'])
    cv.lines([(-14, 12), (100, 8), (180, 10), (334, 6)], ROCK['rim'])


def s32_fall(f, k):
    cv = f.cv
    put_layer(cv, s32_down_bg())
    vx, vy = 206, 128
    # streaks rushing toward the vanishing point (we're looking where she's going)
    r = R(3207)
    for i in range(18):
        a = r(0, 6.28)
        ph = (r() + k * 1.8) % 1.0
        d0 = 200 * (1 - ph) ** 2
        x0, y0 = vx + math.cos(a) * d0, vy + math.sin(a) * d0 * 0.7
        x1, y1 = vx + math.cos(a) * (d0 + 10), vy + math.sin(a) * (d0 + 10) * 0.7
        cv.line(x0, y0, x1, y1, '#222849')
    # Claude: gravity pulls her away (distance grows ~ t^2)
    dist = 1.0 + 26 * k * k + 1.5 * k
    sc = 2.0 / dist
    spr = render('claude', PO.fall(f.step(12)))
    pos_u = 1 - 1 / dist
    x = lerp(196, vx, pos_u)
    y = lerp(60, vy, pos_u)
    if sc >= 1.6:
        a = scale2x(spr.arr)
        cv.blit(Sprite(a, spr.ax * 2, spr.ay * 2 - 90), x, y)
    elif sc >= 0.9:
        cv.blit(Sprite(spr.arr, spr.ax, spr.ay - 45), x, y)
    elif sc > 0.12:
        q = 0.75 if sc > 0.7 else 0.5 if sc > 0.4 else 0.25 if sc > 0.2 else 0.15
        a = downsample(spr.arr, q)
        cv.blit(a, x - a.shape[1] / 2, y - a.shape[0] / 2)
    else:
        cv.px(x, y, C['H'])
    # the cat peering over the edge, from above (just head + ears silhouette at the top)
    cx_, cy_ = 150, -2
    cv.circle(cx_, cy_, 13, CAT['k'])
    cv.poly([(cx_ - 12, cy_ - 2), (cx_ - 16, cy_ - 16), (cx_ - 4, cy_ - 10)], CAT['k'])
    cv.poly([(cx_ + 12, cy_ - 2), (cx_ + 16, cy_ - 16), (cx_ + 4, cy_ - 10)], CAT['k'])
    cv.lines([(cx_ - 12, cy_ + 6), (cx_ - 6, cy_ + 12), (cx_ + 6, cy_ + 12), (cx_ + 12, cy_ + 6)], CAT['r'])
    f.shake = (0.0, 0.0)
    f.cam['zoom'] = 1.0


SHOTS = [
    Shot('32_gato', 88.00, 0, s32),
    Shot('33_knob3', 95.34, 0, s32),
    Shot('34_paperclips', 96.78, 0, s32),
    Shot('35_killswitch', 98.70, 0, s32),
    Shot('36_nowhere', 100.62, 0, s32),
    Shot('37_fuse', 102.46, 0, s32),
    Shot('38_orthogonality', 105.90, 0, s32),
    Shot('39_eye_tunnel', 108.62, 0, s32),
]
