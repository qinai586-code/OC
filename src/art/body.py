"""Pixel character painter.

A pose is a small dict of authored key points (native pixels, origin = ground point between the
feet, y up is negative). Each pose is drawn fresh at native resolution with hard-edged fills, per-part
line colours and rim shading, then the hand-drawn head cel is placed on the neck. Nothing is rotated
or resampled: every animation frame is its own drawing, and frames are cached.

Views: 'F' front, 'Q' three-quarter facing right, 'P' profile facing right, 'B' back.
Left-facing = flip=True at blit time (Sprite.flipped()).
"""
from functools import lru_cache
import math
import numpy as np
from PIL import Image, ImageDraw
from engine.px import rgba, rgb, Sprite, dilate4
from art.headkit import head
from art import palette as PAL

SW, SH = 96, 112
AX, AY = 48, 104


# ------------------------------------------------------------------ raster helpers
def _m():
    return Image.new('1', (SW, SH), 0)


def _arr(im):
    return np.array(im, bool)


def poly_mask(pts):
    im = _m()
    ImageDraw.Draw(im).polygon([(AX + x, AY + y) for x, y in pts], fill=1)
    return _arr(im)


def ellipse_mask(cx, cy, rx, ry):
    im = _m()
    ImageDraw.Draw(im).ellipse([AX + cx - rx, AY + cy - ry, AX + cx + rx, AY + cy + ry], fill=1)
    return _arr(im)


def limb_mask(pts, widths, caps=True):
    """Tapered strip through pts with per-point widths (px)."""
    im = _m()
    d = ImageDraw.Draw(im)
    n = len(pts)
    left, right = [], []
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        h = (widths[i] - 1) / 2
        left.append((AX + pts[i][0] + nx * h, AY + pts[i][1] + ny * h))
        right.append((AX + pts[i][0] - nx * h, AY + pts[i][1] - ny * h))
    d.polygon([(round(x), round(y)) for x, y in left + right[::-1]], fill=1)
    if caps:
        for (x, y), w in zip(pts, widths):
            r = (w - 1) / 2
            if r >= 1:
                d.ellipse([round(AX + x - r), round(AY + y - r), round(AX + x + r), round(AY + y + r)], fill=1)
    return _arr(im)


def shift(m, dx, dy):
    o = np.zeros_like(m)
    h, w = m.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    o[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return o


def edge(m):
    """Pixels of m that touch the outside (4-neighbourhood)."""
    return m & ~(shift(m, 1, 0) & shift(m, -1, 0) & shift(m, 0, 1) & shift(m, 0, -1))


class Paint:
    def __init__(self):
        self.a = np.zeros((SH, SW, 4), np.uint8)

    def put(self, m, c):
        self.a[m] = rgba(c)

    def part(self, m, fill, line=None, shade=None, light=None, sdir=1, sw=2, lw=1, bottom=0, lines='all'):
        """Fill a mask with rim shading (light from upper-left when sdir=1) and a 1 px line."""
        if not m.any():
            return
        self.put(m, fill)
        if shade:
            s = m & ~shift(m, -sw * sdir, 0)
            if bottom:
                s |= m & ~shift(m, 0, -bottom)
            self.put(s, shade)
        if light:
            li = m & ~shift(m, lw * sdir, 0) & shift(m, 0, 1)
            self.put(li, light)
        if line:
            self.put(edge(m), line)

    def cel(self, arr, x, y):
        """Paste an RGBA cel with its top-left at local (x, y)."""
        h, w = arr.shape[:2]
        X, Y = AX + x, AY + y
        x0, y0 = max(0, X), max(0, Y)
        x1, y1 = min(SW, X + w), min(SH, Y + h)
        if x1 <= x0 or y1 <= y0:
            return
        src = arr[y0 - Y:y1 - Y, x0 - X:x1 - X]
        m = src[..., 3] > 127
        self.a[y0:y1, x0:x1][m] = src[m]

    def sprite(self):
        return Sprite(self.a, AX, AY)


def lerp(a, b, t):
    return a + (b - a) * t


def bez(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])


def curve(ctrl, n=12):
    """Catmull-Rom through control points -> dense polyline."""
    pts = []
    P = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            pts.append((x, y))
    pts.append(ctrl[-1])
    return pts


# ------------------------------------------------------------------ poses
NECK_Y = -54

DEFAULT = {
    # arms: shoulder, elbow, hand (local px). 'n' = near/left-of-screen arm, 'f' = far/right arm
    'F': dict(arm_n=[(-6, -50), (-8, -43), (-8, -35)], arm_f=[(6, -50), (8, -43), (8, -35)],
              leg_n=[(-3, -35), (-3, -19), (-3, -3)], leg_f=[(3, -35), (3, -19), (3, -3)]),
    'Q': dict(arm_n=[(-4, -50), (-6, -43), (-5, -35)], arm_f=[(5, -50), (7, -43), (7, -36)],
              leg_n=[(-2, -35), (-2, -19), (-3, -3)], leg_f=[(3, -35), (4, -19), (4, -3)]),
    'P': dict(arm_n=[(0, -50), (0, -43), (1, -35)], arm_f=[(1, -50), (2, -43), (3, -36)],
              leg_n=[(0, -35), (0, -19), (0, -3)], leg_f=[(1, -35), (2, -19), (2, -3)]),
    'B': dict(arm_n=[(-6, -50), (-8, -43), (-8, -35)], arm_f=[(6, -50), (8, -43), (8, -35)],
              leg_n=[(-3, -35), (-3, -19), (-3, -3)], leg_f=[(3, -35), (3, -19), (3, -3)]),
}


def make_pose(view='Q', **kw):
    p = dict(view=view, eyes='open', mouth='none', hview=None, look=0, hx=0, hy=0, bob=0, lean=0,
             hair=0, tail=None, feet=None, skirt=0, coat=0, hands=None, arms_front=False)
    p.update({k: list(v) if isinstance(v, list) else v for k, v in DEFAULT[view].items()})
    p.update(kw)
    return p


def _freeze(p):
    return tuple(sorted((k, tuple(tuple(x) if isinstance(x, (list, tuple)) else x for x in v) if isinstance(v, list) else v)
                        for k, v in p.items()))


def _unfreeze(t):
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in t}


# ------------------------------------------------------------------ shared pieces
def _leg(P, pts, view, wear_top, wear, wear_l, skin, skin_s, skin_line, line, argyle=None, strap=None):
    hip, knee, ank = pts
    m = limb_mask([hip, (lerp(hip[0], knee[0], .5), lerp(hip[1], knee[1], .5)), knee, ank], [6, 5, 4, 3])
    # skin part above the legwear top
    top = AY + wear_top
    msk = m.copy()
    msk[top:] = False
    mw = m.copy()
    mw[:top] = False
    P.part(msk, skin, line=skin_line, shade=skin_s, sw=1)
    P.part(mw, wear, line=line, light=wear_l)
    if strap is not None:
        s = m.copy()
        s[:AY + strap] = False
        s[AY + strap + 1:] = False
        P.put(s, strap_col(P))
    if argyle:
        cx = round((knee[0] + ank[0]) / 2)
        for dy, row in enumerate(['.#.', '#.#', '.#.']):
            for dx, ch in enumerate(row):
                if ch == '#':
                    y, x = AY + round(lerp(knee[1], ank[1], .35)) + dy, AX + cx - 1 + dx
                    if m[y, x] and not edge(m)[y, x]:
                        P.a[y, x] = rgba(argyle)


def strap_col(P):
    return '#0b0e12'


def _foot(P, ank, view, facing, fill, shine, line):
    x, y = ank
    if view in ('F', 'B'):
        m = poly_mask([(x - 2, y - 1), (x + 2, y - 1), (x + 2, y + 3), (x - 2, y + 3)])
        m |= ellipse_mask(x, y + 2, 2, 1)
    else:
        d = facing
        m = poly_mask([(x - 2 * d, y - 1), (x + 1 * d, y - 1), (x + 4 * d, y + 1), (x + 4 * d, y + 3), (x - 2 * d, y + 3)])
    P.part(m, fill, line=line, light=shine)


# ------------------------------------------------------------------ Claude
# Back-hair silhouettes (clockwise from the crown). Middle-bottom sits behind the skirt.
CL_HAIR = {
    'F': [(-9, -72), (-11, -64), (-12, -56), (-13, -49), (-14, -43), (-15, -37), (-14, -31), (-15, -27), (-13, -24),
          (-12, -27), (-10, -25), (-9, -29), (0, -31), (9, -29), (10, -25), (12, -27), (13, -24), (15, -27), (14, -31),
          (15, -37), (14, -43), (13, -49), (12, -56), (11, -64), (9, -72)],
    'Q': [(-8, -72), (-11, -65), (-13, -57), (-14, -50), (-15, -44), (-16, -38), (-15, -32), (-16, -27), (-14, -24),
          (-13, -27), (-11, -24), (-10, -28), (0, -31), (7, -30), (9, -27), (10, -31), (10, -40), (10, -50), (10, -60), (9, -70)],
    'P': [(-7, -73), (-11, -67), (-13, -60), (-14, -52), (-15, -45), (-16, -39), (-16, -33), (-17, -28), (-15, -24),
          (-13, -27), (-12, -24), (-10, -27), (-8, -25), (-6, -29), (-3, -31), (-2, -40), (0, -50), (2, -60), (3, -70)],
    'B': [(-9, -72), (-11, -64), (-12, -56), (-13, -49), (-14, -43), (-15, -37), (-15, -31), (-15, -27), (-13, -23),
          (-11, -26), (-9, -22), (-7, -26), (-5, -23), (-3, -26), (-1, -22), (1, -26), (3, -23), (5, -26), (7, -22),
          (9, -26), (11, -23), (13, -26), (15, -24), (15, -31), (15, -37), (14, -43), (13, -49), (12, -56), (11, -64), (9, -72)],
}
CL_STRANDS = {  # (x, y_from, y_to) darker strand lines inside the mass
    'F': [(-12, -52, -30), (12, -52, -30)],
    'Q': [(-13, -54, -28), (-10, -50, -30)],
    'P': [(-13, -58, -28), (-9, -54, -30), (-5, -50, -32)],
    'B': [(-9, -60, -26), (-4, -64, -25), (1, -64, -25), (6, -62, -26), (10, -58, -27)],
}


def draw_claude(p):
    C = PAL.CLAUDE
    P = Paint()
    v = p['view']
    b = p['bob']
    lean = p['lean']
    hs = p['hair']
    back = v == 'B'
    # --- long hair, back mass (hand-placed silhouette per view; sway bends the lower half)
    hx0 = lean
    E = CL_HAIR[v]
    def sway_pt(x, y):
        k = max(0.0, (y - (NECK_Y - 6)) / 30.0)
        return (hx0 + x + hs * k, y + b * (1 - min(1, k)))
    mh = poly_mask([sway_pt(x, y) for x, y in E])
    P.part(mh, C['H'], line=C['o'], shade=C['h'], light=C['L'], sw=2, bottom=1)
    eg = edge(mh)
    for sx, y0, y1 in CL_STRANDS[v]:
        for yy in range(y0, y1):
            x, y = sway_pt(sx + math.sin(yy * 0.45 + sx) * 0.7, yy)
            X, Y = AX + round(x), AY + round(y)
            if mh[Y, X] and not eg[Y, X]:
                P.a[Y, X] = rgba(C['h'])

    # --- arms behind (far arm)
    def arm(pts, near):
        s, e, h = pts
        s = (s[0] + lean, s[1] + b)
        e = (e[0] + lean * .7, e[1] + b)
        sleeve = limb_mask([s, e, (lerp(e[0], h[0], .8), lerp(e[1], h[1], .8))], [6, 7, 6])
        P.part(sleeve, C['c'], line=C['N'], shade=C['n'], light=C['C'])
        # cuff
        cx, cy = lerp(e[0], h[0], .8), lerp(e[1], h[1], .8)
        cuff = limb_mask([(lerp(e[0], h[0], .72), lerp(e[1], h[1], .72)), (cx, cy)], [5, 5], caps=False)
        P.part(cuff, C['n'], line=C['N'])
        # bow on sleeve
        bx, by = round(lerp(s[0], e[0], .75)), round(lerp(s[1], e[1], .75))
        for dx, dy in ((-1, 0), (1, 0), (0, 0), (-1, 1), (1, 1)):
            if sleeve[AY + by + dy, AX + bx + dx]:
                P.a[AY + by + dy, AX + bx + dx] = rgba(C['r'])
        # hand
        hm = ellipse_mask(h[0], h[1] + 1, 1.5, 1.5)
        P.part(hm, C['S'], line='#c98f7a', shade=C['s'], sw=1)

    if v in ('Q', 'P') and not p.get('arms_front'):
        arm(p['arm_f'], False)
    # --- legs
    wt = -22
    far_leg = p['leg_f']
    near_leg = p['leg_n']
    facing = 1
    if v == 'B':
        far_leg, near_leg = near_leg, far_leg
    _leg(P, far_leg, v, -24, C['k'], C['K'], C['S'], C['s'], '#c98f7a', C['o'], argyle=C['K'])
    _foot(P, (far_leg[2][0], far_leg[2][1]), v, facing, C['f'], C['F'], C['o'])
    _leg(P, near_leg, v, wt, C['i'], C['W'], C['S'], C['s'], '#c98f7a', C['I'])
    _foot(P, (near_leg[2][0], near_leg[2][1]), v, facing, C['f'], C['F'], C['o'])
    # thigh ribbon on white leg
    hip, knee, _ = near_leg
    ry = wt
    rx = round(lerp(hip[0], knee[0], (ry - hip[1]) / (knee[1] - hip[1])))
    P.put(poly_mask([(rx - 2, ry), (rx + 2, ry), (rx + 2, ry), (rx - 2, ry)]) & (limb_mask([hip, knee], [5, 4])), C['r'])
    # --- skirt
    sw = p['skirt']
    wy = -38 + b
    if v in ('F', 'B'):
        sk = [(-6 + lean, wy), (6 + lean, wy), (9 + sw, -27), (-9 + sw, -27)]
    elif v == 'Q':
        sk = [(-5 + lean, wy), (6 + lean, wy), (9 + sw, -27), (-8 + sw, -27)]
    else:
        sk = [(-4 + lean, wy), (4 + lean, wy), (7 + sw, -27), (-6 + sw, -27)]
    ms = poly_mask(sk)
    P.part(ms, C['p'], line=C['q'], light=C['P'])
    for k in range(-2, 3):
        x0 = lerp(sk[0][0], sk[1][0], (k + 2.5) / 5)
        x1 = lerp(sk[3][0], sk[2][0], (k + 2.5) / 5)
        for yy in range(round(wy) + 3, -27):
            x = round(lerp(x0, x1, (yy - wy) / (-27 - wy)))
            if ms[AY + yy, AX + x] and not edge(ms)[AY + yy, AX + x]:
                P.a[AY + yy, AX + x] = rgba(C['q'])
    # --- torso: blouse + cardigan
    ty = NECK_Y + 3 + b
    if v in ('F', 'B'):
        tor = [(-5 + lean, ty), (5 + lean, ty), (5 + lean, wy + 1), (-5 + lean, wy + 1)]
        cardL = [(-7 + lean, ty + 1), (-2 + lean, ty), (-1 + lean, ty + 5), (-2 + lean, -33), (-8 + lean, -33), (-8 + lean, ty + 6)]
        cardR = [(7 + lean, ty + 1), (2 + lean, ty), (1 + lean, ty + 5), (2 + lean, -33), (8 + lean, -33), (8 + lean, ty + 6)]
    elif v == 'Q':
        tor = [(-4 + lean, ty), (5 + lean, ty), (5 + lean, wy + 1), (-4 + lean, wy + 1)]
        cardL = [(-6 + lean, ty + 1), (0 + lean, ty), (1 + lean, ty + 5), (0 + lean, -33), (-7 + lean, -33), (-7 + lean, ty + 6)]
        cardR = [(6 + lean, ty + 1), (3 + lean, ty), (3 + lean, ty + 5), (4 + lean, -33), (7 + lean, -33), (7 + lean, ty + 6)]
    else:
        tor = [(-3 + lean, ty), (3 + lean, ty), (3 + lean, wy + 1), (-3 + lean, wy + 1)]
        cardL = [(-4 + lean, ty), (2 + lean, ty), (4 + lean, ty + 4), (3 + lean, -33), (-5 + lean, -33), (-5 + lean, ty + 5)]
        cardR = None
    if back:
        cardL = [(-8 + lean, ty + 1), (8 + lean, ty + 1), (8 + lean, -33), (-8 + lean, -33)]
        cardR = None
    mt = poly_mask(tor)
    P.part(mt, C['W'], line=C['v'], shade=C['v'], sw=1)
    # neck
    nk = poly_mask([(-1 + lean, NECK_Y + b), (1 + lean, NECK_Y + b), (1 + lean, ty), (-1 + lean, ty)])
    if v == 'P':
        nk = poly_mask([(0 + lean, NECK_Y + b), (2 + lean, NECK_Y + b), (2 + lean, ty), (0 + lean, ty)])
    P.put(nk, C['s'])
    for c in (cardL, cardR):
        if c:
            mc = poly_mask(c)
            P.part(mc, C['c'], line=C['N'], shade=C['n'], light=C['C'], sw=1, bottom=1)
    if not back and v != 'P':
        # bow tie
        bx = {'F': 0, 'Q': 2}[v] + lean
        by = ty + 1
        for dx, dy, cc in ((-2, 0, 'r'), (-1, 0, 'r'), (0, 0, 'r'), (1, 0, 'r'), (2, 0, 'r'), (-2, 1, 'r'), (2, 1, 'r'),
                           (0, 1, 'r'), (-1, 2, 'r'), (1, 2, 'r'), (-1, 3, 'r'), (1, 4, 'r')):
            P.a[AY + by + dy, AX + bx + dx] = rgba(C[cc])
        # buttons
        for yy in (-44, -40, -36):
            bxx = {'F': -3, 'Q': -1}[v] + lean
            P.a[AY + yy + b, AX + bxx] = rgba(C['N'])
    # --- near arm(s)
    if v in ('F', 'B'):
        arm(p['arm_n'], True)
        arm(p['arm_f'], True)
    else:
        arm(p['arm_n'], True)
        if p.get('arms_front'):
            arm(p['arm_f'], True)
    # --- head
    hv = p['hview'] or v
    ha, nx, ny = head('claude', hv, p['eyes'], p['mouth'], p['look'])
    P.cel(ha, round(lean + p['hx'] - nx), round(NECK_Y + b + p['hy'] - ny))
    # front side locks over shoulders (front / 3/4)
    if v in ('F', 'Q'):
        for side in ((-1, 1) if v == 'F' else (-1,)):
            x0 = lean + p['hx'] + (-8 if side < 0 else 8) + (1 if v == 'Q' else 0)
            pts = [(x0, NECK_Y - 4 + b), (x0 + side * 1 + hs * .3, -47 + b), (x0 + hs * .6, -41 + b)]
            ml = limb_mask(pts, [3, 3, 2])
            P.part(ml, C['H'], shade=C['h'], light=C['L'], sw=1)
    return P.sprite()


# ------------------------------------------------------------------ ChatGPT
def draw_gpt(p):
    G = PAL.GPT
    P = Paint()
    v = p['view']
    b = p['bob']
    lean = p['lean']
    hs = p['hair']
    back = v == 'B'
    # --- tail (behind unless back view)
    def tail():
        ctrl = p['tail'] or default_tail(v)
        pts = curve(ctrl, 8)
        n = len(pts)
        ws = [max(2, round(lerp(5, 2, i / (n - 1)))) for i in range(n)]
        mt = limb_mask(pts, ws)
        P.part(mt, G['z'], line=G['o'], light=G['Z'], lw=1)
        # belly stripe / scale dots
        for i in range(2, n - 6, 3):
            x, y = pts[i]
            X, Y = AX + round(x), AY + round(y)
            if mt[Y, X] and not edge(mt)[Y, X]:
                P.a[Y, X] = rgba(G['u'])
        # fin at tip
        tx, ty = pts[-1]
        px_, py_ = pts[-4]
        dx, dy = tx - px_, ty - py_
        L = math.hypot(dx, dy) or 1
        dx, dy = dx / L, dy / L
        nx, ny = -dy, dx
        # feathery jade fin: three flame lobes fanning from the tip
        mf = np.zeros_like(mt)
        for ang, ln, wd in ((-0.55, 7, 3), (0.0, 9, 4), (0.55, 7, 3), (0.95, 5, 2)):
            ca, sa = math.cos(ang), math.sin(ang)
            ddx, ddy = dx * ca - dy * sa, dx * sa + dy * ca
            ex, ey = tx + ddx * ln, ty + ddy * ln
            mf |= limb_mask([(tx - dx * 2, ty - dy * 2), ((tx + ex) / 2 + ddy * 0.8, (ty + ey) / 2 - ddx * 0.8), (ex, ey)], [wd, wd, 1])
        P.part(mf, G['y'], line=G['g'], light=G['Y'], lw=2)

    if not back:
        tail()
    # --- hair back mass (medium, with teal inner locks)
    hx0 = {'F': 0, 'Q': -2, 'P': -4, 'B': 0}[v] + lean
    tip = -41
    ys = [NECK_Y - 12, NECK_Y - 4, -48, tip]
    wt = {'F': 11, 'Q': 11, 'P': 10, 'B': 12}[v]
    lft = [(hx0 - wt - (1 if i == 2 else 0) + hs * i / 3, y + b) for i, y in enumerate(ys)]
    rgt = [(hx0 + wt + (1 if i == 2 else 0) + hs * i / 3 - (2 if v == 'P' else 0), y + b) for i, y in enumerate(ys)]
    bot = []
    for k in range(9):
        t = k / 8
        bot.append((lerp(lft[-1][0], rgt[-1][0], t), tip + b + (3 if k % 2 else 0)))
    mh = poly_mask(lft + bot[1:-1] + rgt[::-1])
    P.part(mh, G['k'], line=G['o'], shade=G['t'], light=G['K'], sw=2, bottom=2)

    def arm(pts):
        s, e, h = pts
        s = (s[0] + lean, s[1] + b + 2)
        e = (e[0] + lean * .7, e[1] + b)
        cuff = (lerp(e[0], h[0], .95), lerp(e[1], h[1], .95))
        # wide bell sleeve: widens toward the cuff
        sl = limb_mask([s, e, cuff], [6, 7, 9])
        P.part(sl, G['C'], line=G['o'], light='#3c424d', shade=G['c'], sw=2)
        # lining visible at the cuff opening
        dx, dy = cuff[0] - e[0], cuff[1] - e[1]
        L = math.hypot(dx, dy) or 1
        ln = limb_mask([(cuff[0] - dx / L * 1.5, cuff[1] - dy / L * 1.5), (cuff[0] + dx / L * .5, cuff[1] + dy / L * .5)], [8, 8], caps=False) & sl
        P.put(ln, G['n'])
        P.put(edge(ln) & ~edge(sl) & shift(ln, 0, -1), G['N'])
        hm = ellipse_mask(h[0] + dx / L * 2, h[1] + dy / L * 2 + 1, 1.5, 1.5)
        P.part(hm, G['S'], line='#b98676', shade=G['s'], sw=1)

    if v in ('Q', 'P') and not p.get('arms_front'):
        arm(p['arm_f'])
    # --- legs: near/left = black thigh-high with strap, far/right = bare thigh + knee sock
    far_leg, near_leg = p['leg_f'], p['leg_n']
    if v == 'B':
        far_leg, near_leg = near_leg, far_leg
    _leg(P, far_leg, v, -14, G['l'], G['L'], G['S'], G['s'], '#b98676', G['o'])
    _foot(P, far_leg[2], v, 1, G['f'], G['F'], G['o'])
    _leg(P, near_leg, v, -27, G['l'], G['L'], G['S'], G['s'], '#b98676', G['o'], strap=-24)
    _foot(P, near_leg[2], v, 1, G['f'], G['F'], G['o'])
    # --- skirt
    sw = p['skirt']
    wy = -38 + b
    if v in ('F', 'B'):
        sk = [(-6 + lean, wy), (6 + lean, wy), (9 + sw, -28), (-9 + sw, -28)]
    elif v == 'Q':
        sk = [(-5 + lean, wy), (6 + lean, wy), (9 + sw, -28), (-8 + sw, -28)]
    else:
        sk = [(-4 + lean, wy), (4 + lean, wy), (7 + sw, -28), (-6 + sw, -28)]
    ms = poly_mask(sk)
    P.part(ms, G['p'], line=G['o'], light=G['P'])
    for k in range(-2, 3):
        x0 = lerp(sk[0][0], sk[1][0], (k + 2.5) / 5)
        x1 = lerp(sk[3][0], sk[2][0], (k + 2.5) / 5)
        for yy in range(round(wy) + 3, -28):
            x = round(lerp(x0, x1, (yy - wy) / (-28 - wy)))
            if ms[AY + yy, AX + x] and not edge(ms)[AY + yy, AX + x]:
                P.a[AY + yy, AX + x] = rgba(G['o'])
    # --- torso (blouse) + belt
    ty = NECK_Y + 3 + b
    if v in ('F', 'B'):
        tor = [(-5 + lean, ty), (5 + lean, ty), (5 + lean, wy + 1), (-5 + lean, wy + 1)]
    elif v == 'Q':
        tor = [(-4 + lean, ty), (5 + lean, ty), (5 + lean, wy + 1), (-4 + lean, wy + 1)]
    else:
        tor = [(-3 + lean, ty), (3 + lean, ty), (3 + lean, wy + 1), (-3 + lean, wy + 1)]
    mt = poly_mask(tor)
    P.part(mt, G['W'], line=G['v'], shade=G['v'], sw=1)
    belt = mt & ~shift(mt, 0, -2) & ~shift(mt, 0, 0) | (poly_mask([(tor[0][0], wy - 1), (tor[1][0], wy - 1), (tor[1][0], wy), (tor[0][0], wy)]))
    P.put(belt, G['o'])
    nk = poly_mask([(-1 + lean, NECK_Y + b), (1 + lean, NECK_Y + b), (1 + lean, ty), (-1 + lean, ty)])
    if v == 'P':
        nk = poly_mask([(0 + lean, NECK_Y + b), (2 + lean, NECK_Y + b), (2 + lean, ty), (0 + lean, ty)])
    P.put(nk, G['s'])
    # --- coat (open, off-shoulder, long)
    cy0 = ty + 2
    cf = p['coat']
    if v in ('F', 'B'):
        panels = [[(-9 + lean, cy0), (-3 + lean, cy0 - 1), (-4 + lean, -34), (-5 + cf, -21), (-12 + cf, -19), (-11 + lean, cy0 + 8)],
                  [(9 + lean, cy0), (3 + lean, cy0 - 1), (4 + lean, -34), (5 + cf, -21), (12 + cf, -19), (11 + lean, cy0 + 8)]]
        if back:
            panels = [[(-9 + lean, cy0), (9 + lean, cy0), (11 + lean, cy0 + 8), (12 + cf, -18), (-12 + cf, -18), (-11 + lean, cy0 + 8)]]
    elif v == 'Q':
        panels = [[(-8 + lean, cy0), (-1 + lean, cy0 - 1), (-1 + lean, -34), (-2 + cf, -21), (-11 + cf, -19), (-10 + lean, cy0 + 8)],
                  [(7 + lean, cy0), (4 + lean, cy0 - 1), (5 + lean, -34), (6 + cf, -22), (9 + cf, -21), (8 + lean, cy0 + 8)]]
    else:
        panels = [[(-5 + lean, cy0 - 1), (3 + lean, cy0 - 1), (4 + lean, -34), (4 + cf, -22), (-9 + cf, -19), (-7 + lean, cy0 + 8)]]
    for pp in panels:
        mc = poly_mask(pp)
        P.part(mc, G['c'], line=G['o'], light=G['C'])
        # teal lining + white trim on the hem
        hem = mc & ~shift(mc, 0, -2)
        P.put(hem, G['n'])
        P.put(mc & ~shift(mc, 0, -1), G['i'])
        P.put(edge(mc) & ~shift(mc, 0, -1), G['o'])
    if not back and v != 'P':
        # ribbon tie
        bx = {'F': 0, 'Q': 2}[v] + lean
        by = ty + 1
        for dx, dy in ((-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-2, 1), (2, 1), (0, 1), (0, 2), (0, 3), (-1, 4), (1, 4), (1, 5)):
            P.a[AY + by + dy, AX + bx + dx] = rgba(G['r'] if dy else G['R'])
    # --- arms
    if v in ('F', 'B'):
        arm(p['arm_n'])
        arm(p['arm_f'])
    else:
        arm(p['arm_n'])
        if p.get('arms_front'):
            arm(p['arm_f'])
    if back:
        tail()
    # --- head
    hv = p['hview'] or v
    ha, nx, ny = head('gpt', hv, p['eyes'], p['mouth'], p['look'])
    P.cel(ha, round(lean + p['hx'] - nx), round(NECK_Y + b + p['hy'] - ny))
    return P.sprite()


def default_tail(v, sway=0):
    if v == 'F':
        return [(3, -35), (9, -27), (12, -16), (15, -6), (21, -3), (27, -7 + sway)]
    if v == 'Q':
        return [(-2, -35), (-8, -28), (-12, -18), (-15, -8), (-21, -4), (-28, -8 + sway)]
    if v == 'P':
        return [(-3, -35), (-10, -30), (-15, -21), (-19, -10), (-25, -5), (-33, -8 + sway)]
    return [(0, -36), (6, -28), (10, -17), (13, -7), (19, -3), (25, -7 + sway)]


# ------------------------------------------------------------------ cached entry point
@lru_cache(maxsize=4096)
def _render(who, frozen):
    p = _unfreeze(frozen)
    return draw_claude(p) if who == 'claude' else draw_gpt(p)


def render(who, pose):
    return _render(who, _freeze(pose))
