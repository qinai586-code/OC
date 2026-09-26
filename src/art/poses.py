"""Authored pose library. Each function returns a pose dict (or a list of frames).

Animation frames are keyframes, not interpolations: a run is 8 drawings, a blink is 3.
The engine holds each drawing for its authored number of film frames (usually 8-12 fps).
"""
import math
from art.body import make_pose, default_tail

THIGH, SHIN = 16, 16
UPPER, FORE = 8, 8


def leg_from_angles(hip, a_thigh, bend, facing=1):
    """Angles in degrees from vertical; a_thigh>0 swings forward; bend>0 folds the shin back."""
    a1 = math.radians(a_thigh)
    a2 = math.radians(a_thigh - bend)
    kx, ky = hip[0] + facing * THIGH * math.sin(a1), hip[1] + THIGH * math.cos(a1)
    ax, ay = kx + facing * SHIN * math.sin(a2), ky + SHIN * math.cos(a2)
    return [hip, (kx, ky), (ax, ay)]


def arm_from_angles(sh, a_up, bend, facing=1):
    a1 = math.radians(a_up)
    a2 = math.radians(a_up + bend)
    ex, ey = sh[0] + facing * UPPER * math.sin(a1), sh[1] + UPPER * math.cos(a1)
    hx, hy = ex + facing * FORE * math.sin(a2), ey + FORE * math.cos(a2)
    return [sh, (ex, ey), (hx, hy)]


# ---------------------------------------------------------------- standing / idle
def stand(view='Q', **kw):
    return make_pose(view, **kw)


def idle(view='Q', frame=0, **kw):
    """2-drawing breath: frame 1 settles the upper body by 1 px."""
    return make_pose(view, bob=1 if frame % 2 else 0, **kw)


def blink(view='Q', frame=0, base='open', **kw):
    eyes = [base, 'closed', base][frame % 3] if frame < 3 else base
    return make_pose(view, eyes=eyes, **kw)


# ---------------------------------------------------------------- locomotion (profile, facing right)
RUN_KEYS = [  # (near thigh, near bend, far thigh, far bend, hip lift, near-arm swing)
    (32, 14, -24, 84, 0, -40),     # contact
    (14, 36, -4, 116, -1, -22),    # down (trailing foot tucked high)
    (-8, 30, 30, 96, 0, 10),       # passing, far knee drives up
    (-30, 48, 44, 40, 2, 34),      # airborne push-off
]


def run(frame, who='gpt', eyes='open', mouth='none', speed=1.0):
    k = frame % 8
    a = RUN_KEYS[k % 4]
    if k >= 4:  # other leg leads
        a = (a[2], a[3], a[0], a[1], a[4], -a[5])
    n_th, n_b, f_th, f_b, lift, sw = a
    hip = (0, -35)
    ln = leg_from_angles(hip, n_th, n_b)
    lf = leg_from_angles(hip, f_th, f_b)
    low = max(ln[2][1], lf[2][1])
    dy = -3 - low - lift
    ln = [(x, y + dy) for x, y in ln]
    lf = [(x, y + dy) for x, y in lf]
    b = round(dy)
    sh = (0, -50)
    an = arm_from_angles((sh[0], sh[1]), sw, 95)
    af = arm_from_angles((sh[0] + 1, sh[1]), -sw, 95)
    an = [(x, y + b) for x, y in an]
    af = [(x, y + b) for x, y in af]
    ph = k / 8 * math.tau
    p = make_pose('P', leg_n=ln, leg_f=lf, arm_n=an, arm_f=af, bob=b, lean=1, eyes=eyes, mouth=mouth,
                  hair=round(-3 - math.sin(ph) * 1))
    if who == 'gpt':
        p['tail'] = [(-3, -35 + b), (-10, -33 + b), (-17, -31 + round(math.sin(ph) * 2)), (-24, -30 + round(math.sin(ph + 1) * 3)),
                     (-31, -30 + round(math.sin(ph + 2) * 4)), (-38, -32 + round(math.sin(ph + 3) * 4))]
    return p


def walk(frame, who='gpt', eyes='open', mouth='none'):
    WALK = [(20, 6, -18, 20, 0, -20), (8, 14, -4, 40, -1, -10), (-4, 8, 8, 30, 0, 0), (-16, 12, 18, 10, 0, 16)]
    k = frame % 8
    a = WALK[k % 4]
    if k >= 4:
        a = (a[2], a[3], a[0], a[1], a[4], -a[5])
    n_th, n_b, f_th, f_b, lift, sw = a
    hip = (0, -35)
    ln = leg_from_angles(hip, n_th, n_b)
    lf = leg_from_angles(hip, f_th, f_b)
    low = max(ln[2][1], lf[2][1])
    dy = -3 - low - lift
    ln = [(x, y + dy) for x, y in ln]
    lf = [(x, y + dy) for x, y in lf]
    b = round(dy)
    an = [(x, y + b) for x, y in arm_from_angles((0, -50), sw, 10)]
    af = [(x, y + b) for x, y in arm_from_angles((1, -50), -sw, 10)]
    ph = k / 8 * math.tau
    p = make_pose('P', leg_n=ln, leg_f=lf, arm_n=an, arm_f=af, bob=b, eyes=eyes, mouth=mouth, hair=round(-1 - math.sin(ph) * .6))
    if who == 'gpt':
        p['tail'] = [(-3, -35 + b), (-10, -29 + b), (-16, -20), (-21, -10 + round(math.sin(ph) * 1)), (-28, -6), (-35, -9 + round(math.sin(ph + 1) * 2))]
    return p


# ---------------------------------------------------------------- expressive single poses
def point(who='gpt', eyes='sharp', mouth='smile', reach=1.0):
    """3/4 facing right, near arm thrown out pointing."""
    p = make_pose('Q', eyes=eyes, mouth=mouth, lean=1, arms_front=True)
    p['arm_f'] = [(5, -50), (11, -51), (17 * reach + 1, -53)]
    p['arm_n'] = [(-4, -50), (-6, -43), (-4, -36)]
    if who == 'gpt':
        p['tail'] = [(-2, -35), (-9, -31), (-14, -24), (-18, -17), (-22, -14), (-27, -17)]
    return p


def plead(who='claude', eyes='worried', mouth='frown', view='F'):
    """Hands clasped at the chest."""
    p = make_pose(view, eyes=eyes, mouth=mouth, bob=1)
    if view == 'F':
        p['arm_n'] = [(-6, -50), (-7, -44), (-1, -44)]
        p['arm_f'] = [(6, -50), (7, -44), (1, -44)]
    else:
        p['arms_front'] = True
        p['arm_n'] = [(-4, -50), (-4, -44), (2, -44)]
        p['arm_f'] = [(5, -50), (6, -45), (3, -45)]
    return p


def think(who='claude', view='Q', eyes='side', mouth='none'):
    """Hand to chin (both references show this pose)."""
    p = make_pose(view, eyes=eyes, mouth=mouth, arms_front=True)
    p['arm_f'] = [(5, -50), (6, -43), (3, -52)] if view == 'Q' else [(6, -50), (7, -44), (2, -53)]
    return p


def surprise(who='claude', view='Q', eyes='wide', mouth='o'):
    p = make_pose(view, eyes=eyes, mouth=mouth, bob=-1, hair=0)
    p['arm_n'] = [(-4, -50), (-9, -46), (-12, -50)]
    p['arm_f'] = [(5, -50), (10, -46), (13, -50)]
    p['arms_front'] = True
    return p


def reach_up(who='claude', view='Q', eyes='open', mouth='none'):
    p = make_pose(view, eyes=eyes, mouth=mouth, arms_front=True)
    p['arm_f'] = [(5, -50), (8, -57), (10, -64)]
    return p


def wave(frame, who='claude', view='F', eyes='happy', mouth='smile'):
    p = make_pose(view, eyes=eyes, mouth=mouth)
    hx = [11, 13][frame % 2]
    p['arm_f'] = [(6, -50), (10, -54), (hx, -61)]
    return p


def bow(frame=0, who='claude', view='Q'):
    """Stage bow: 0 = upright, 1 = half, 2 = deep (head/torso lowered by bob; arms at sides)."""
    d = [0, 4, 7][frame]
    p = make_pose(view, eyes='closed' if d else 'open', mouth='smile', bob=d, lean=[0, 2, 4][frame], hy=[0, 1, 2][frame])
    return p


def fall(frame, who='claude'):
    """Tumbling-fall drawings (front view with limbs flung up)."""
    k = frame % 2
    p = make_pose('F', eyes='wide', mouth='shout', hair=[-2, 2][k], bob=0)
    p['arm_n'] = [(-6, -50), (-10, -56), ([-12, -13][k], -63)]
    p['arm_f'] = [(6, -50), (10, -56), ([13, 12][k], -63)]
    p['leg_n'] = [(-3, -35), (-6, -22), ([-5, -7][k], -8)]
    p['leg_f'] = [(3, -35), (6, -24), ([8, 6][k], -12)]
    return p
