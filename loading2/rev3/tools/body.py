"""REV3 body/environment test, 0:07.50-0:12.50 of the locked track (same slot as v2 Test 1).

Action (simplified to what the existing drawings support): A, seated on the parapet at night, watches
a warm light descend (key drawing A1: chin raised, eyes up, lips parted in awe). As it sinks past
her eye line she nods down to follow it (anticipation, one breakdown, then key drawing A3), raises
her forearm about the elbow, and the light settles into her open palm. The palm gives under it and
recovers, the light warms her hand and face, and her hair swings and settles.

What carries the action:
- two genuinely different drawn poses (A1 and A3, QC pack), aligned on the torso;
- the head pitch between them, which in a profile view is an in-plane rotation, used only for the
  anticipation and the breakdown frames;
- a forearm rotation about the elbow (below frame), with ease-out, overshoot and settle;
- secondary hair motion (lag, swing, settle), a contact dip and changing light.
No uniform scaling, camera push or crossfade between views.

  python3 rev3/tools/body.py  -> rev3/tests/REV3_body_light_catch.mp4 (+ frames in rev3/work/body)
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from matte import load_rgba  # noqa: E402

AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
KV1 = '/home/user/OC/loading/work/plates/KV1.png'
OUTD = os.path.join(R, 'work', 'body')
MP4 = os.path.join(R, 'tests', 'REV3_body_light_catch.mp4')
os.makedirs(OUTD, exist_ok=True)
FPS, OW, OH = 24, 1920, 1080
F0, F1 = 180, 300

# ---------------------------------------------------------------- layers in "A1 space"
A1 = load_rgba(os.path.join(R, 'assets', 'A1.png'))
A3 = load_rgba(os.path.join(R, 'assets', 'A3.png'))
S3, T3 = 1.27, np.array([148.5, -224.0])            # A3 -> A1 space (torso-aligned)


def choke(rgba):
    # keep the drawn line art, drop the soft grey halo the source drawings carry outside it
    a = rgba[:, :, 3]
    x = np.clip((a - 0.28) / 0.5, 0, 1)
    rgba[:, :, 3] = x * x * (3 - 2 * x)
    return rgba


def reink(rgba):
    """Replace the source drawings' noisy grey halo (which reads as a dotted outline once lit) with one clean
    edge: a continuous line in the darkened neighbouring interior colour (brown on skin, near-black on
    hair), blending into the interior over the outer 4 px."""
    a = rgba[:, :, 3]
    solid = (cv2.GaussianBlur(a, (0, 0), 1.6) > 0.5).astype(np.uint8)
    solid = cv2.morphologyEx(solid, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # the matte keeps a pale tinted halo ~4 px wide outside the drawn outline: pull the silhouette in to the line
    solid = (cv2.distanceTransform(solid, cv2.DIST_L2, 5) > 4.0).astype(np.uint8)
    solid = (cv2.GaussianBlur(solid.astype(np.float32), (0, 0), 1.0) > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(solid, cv2.DIST_L2, 5)
    core = (dist > 4.5).astype(np.float32)
    num = cv2.GaussianBlur(rgba[:, :, :3] * core[:, :, None], (0, 0), 4)
    den = cv2.GaussianBlur(core, (0, 0), 4)[:, :, None]
    inner = num / np.maximum(den, 1e-4)
    line = inner * np.array([0.40, 0.33, 0.33])
    w_line = np.clip((2.6 - dist) / 1.2, 0, 1)[:, :, None]          # line over the outer ~2 px
    w_band = np.clip((4.5 - dist) / 2.0, 0, 1)[:, :, None]          # outer 4.5 px: interior colour, not halo
    col = rgba[:, :, :3] * (1 - w_band) + inner * w_band
    col = col * (1 - w_line) + line * w_line
    out = rgba.copy()
    out[:, :, :3] = np.where(solid[:, :, None] > 0, col, rgba[:, :, :3])
    out[:, :, 3] = cv2.GaussianBlur(solid.astype(np.float32), (0, 0), 0.8)
    return out


A1, A3 = reink(choke(A1)), reink(choke(A3))

FX0, FY0, FW = 300.0, 60.0, 2260.0                   # frame in A1 space (hides both drawings' crops)
SO = OW / FW


def to_out(p):
    return (np.asarray(p, np.float32) - [FX0, FY0]) * SO


# arm layer (A3 coords): hand + forearm + sleeve
ARM = np.array([(600, 1000), (640, 960), (662, 905), (700, 868), (760, 838), (850, 815), (905, 775), (955, 785),
                (945, 850), (885, 932), (800, 985), (720, 1012), (702, 1060), (700, 1080), (765, 1150), (790, 1240),
                (795, 1300), (590, 1300), (590, 1130), (575, 1080), (590, 1040)], np.int32)
arm_m = np.zeros(A3.shape[:2], np.uint8)
cv2.fillPoly(arm_m, [ARM], 255)
arm_m = cv2.GaussianBlur(arm_m.astype(np.float32) / 255, (5, 5), 0)
arm = A3.copy()
arm[:, :, 3] *= arm_m
# the lit hand shows the matte's soft ink band: smooth it so the outline reads as a line, not dots
ab = cv2.GaussianBlur(arm[:, :, 3], (0, 0), 1.1)
arm[:, :, 3] = np.where(arm[:, :, 3] < 0.98, ab, arm[:, :, 3])
body3 = A3.copy()
body3[:, :, 3] *= (1 - arm_m)
# behind the sleeve the torso continues. Fill that part with the real drawn coat, shirt and bow from
# the A1 drawing (aligned on the torso), not with an inpainting smudge.
yy3, xx3 = np.mgrid[0:A3.shape[0], 0:A3.shape[1]]
front = 600 + (yy3 - 1000) * (70.0 / 290.0)
behind = (arm_m > 0.02) & (xx3 < front) & (yy3 > 990)
A1_in3 = cv2.warpAffine(A1, np.float32([[1 / S3, 0, -T3[0] / S3], [0, 1 / S3, -T3[1] / S3]]),
                        (A3.shape[1], A3.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
wfill = (behind & (A1_in3[:, :, 3] > 0.5)).astype(np.float32)
wfill = cv2.GaussianBlur(wfill, (0, 0), 3) * behind
body3[:, :, :3] = body3[:, :, :3] * (1 - wfill[:, :, None]) * (body3[:, :, 3:] > 0) + A1_in3[:, :, :3] * wfill[:, :, None] \
    + body3[:, :, :3] * (1 - wfill[:, :, None]) * (body3[:, :, 3:] <= 0)
body3[:, :, 3] = np.maximum(body3[:, :, 3], wfill * A1_in3[:, :, 3])
PIV3 = np.array([610.0, 1330.0])                     # elbow, below frame (A3 coords)
PALM3 = np.array([790.0, 902.0])                     # where the light rests (A3 coords)

NECK1 = np.array([640.0, 880.0])                     # head pivot in A1
NECK3 = np.array([440.0, 850.0])                     # head pivot in A3


def smooth(t, a, b):
    x = np.clip((t - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def ease_out(t, a, b):
    x = np.clip((t - a) / (b - a), 0, 1)
    return 1 - (1 - x) ** 3


def spring(t, t0, amp, period, tau):
    if t < t0:
        return 0.0
    u = t - t0
    return amp * np.exp(-u / tau) * np.sin(2 * np.pi * u / period)


# ---------------------------------------------------------------- timing (seconds)
T_ANT0, T_ANT1 = 8.50, 8.75           # anticipation: chin lifts a little, breath in
T_BRK = 8.75                          # breakdown frames 210-212 (A1 head pitched down)
T_SW = 8.875                          # switch to the A3 drawing (frame 213)
T_ARM0, T_ARM1 = 8.875, 9.70          # forearm rises
T_LAND = 10.25                        # light settles into the palm


def head_angle(t, drawing=None):
    """A1: chin-up anticipation then pitch down into the breakdown; A3: overshoot then settle (deg, + = chin down)."""
    if t < T_SW or drawing == 'A1':
        return -1.8 * smooth(t, T_ANT0, T_ANT1) + 11.0 * smooth(t, T_BRK - 0.02, T_SW)
    return 4.5 * (1 - ease_out(t, T_SW, T_SW + 0.42)) + spring(t, T_SW + 0.30, 0.8, 0.9, 0.5)


def arm_angle(t):
    """forearm rotation from its drawn pose (deg, + = lowered toward the lap)."""
    base = 78.0 * (1 - ease_out(t, T_ARM0, T_ARM1)) - 4.0 * np.sin(np.pi * smooth(t, T_ARM1 - 0.25, T_ARM1 + 0.30))
    dip = 2.2 * np.exp(-max(t - T_LAND, 0) / 0.18) * np.sin(np.pi * min(max(t - T_LAND, 0) / 0.18, 1.0)) if t >= T_LAND else 0.0
    dip += spring(t, T_LAND + 0.18, 0.6, 0.5, 0.25)
    return base + dip


def light_pos(t):
    """canvas (A1 space) position of the light; ends resting in the palm of the final arm pose."""
    palm = S3 * PALM3 + T3
    p0, p1, p2 = np.array([2380.0, 120.0]), np.array([1700.0, 260.0]), palm
    u = ease_out(t, 7.5, T_LAND) if t < T_LAND else 1.0
    u = 0.55 * (t - 7.5) / (T_LAND - 7.5) + 0.45 * u if t < T_LAND else 1.0
    q = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u ** 2 * p2
    if t >= T_LAND:
        # rides the palm while it gives under the contact
        q = q + np.array([0.0, 1.0]) * 9.0 * np.sin(np.pi * min((t - T_LAND) / 0.36, 1.0)) * np.exp(-(t - T_LAND) / 0.3)
    q = q + np.array([0.0, 2.0 * np.sin(t * 5.1)]) * (1 if t > T_LAND + 0.5 else 0)
    return q


def light_power(t):
    p = 0.55 + 0.45 * smooth(t, 9.3, T_LAND)
    p += 0.55 * np.exp(-max(t - T_LAND, 0) / 0.35) * (t >= T_LAND)
    return p * (1 + 0.04 * np.sin(t * 11.0))


# ---------------------------------------------------------------- background plate
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
kv = cv2.imread(KV1)[:, :, ::-1].astype(np.float32) / 255.0
plate = kv[60:1100, 2050:3072]                        # sky, clouds and the lit Earth limb, clear of B in KV1
plate = cv2.resize(plate, (OW, int(OW * plate.shape[0] / plate.shape[1])), interpolation=cv2.INTER_AREA)
plate = plate[plate.shape[0] - OH:] if plate.shape[0] >= OH else cv2.resize(plate, (OW, OH))
BG = cv2.GaussianBlur(plate, (0, 0), 3.0) * 0.92


def rot_field(shape, M_out_to_layer, pivot, angle_deg, w_fn):
    """Backward map (layer coords) for output pixels: head rotation about `pivot` weighted by w_fn(layer xy)."""
    px = M_out_to_layer[0, 0] * xx + M_out_to_layer[0, 1] * yy + M_out_to_layer[0, 2]
    py = M_out_to_layer[1, 0] * xx + M_out_to_layer[1, 1] * yy + M_out_to_layer[1, 2]
    if abs(angle_deg) < 1e-4:
        return px, py
    a = np.radians(angle_deg)
    ca, sa = np.cos(a), np.sin(a)
    sx, sy = px.copy(), py.copy()
    for _ in range(3):                                # fixed-point inverse of p -> p + w(p)(R(p-c)+c-p)
        w = w_fn(sx, sy)
        dx = sx - pivot[0]
        dy = sy - pivot[1]
        rx = ca * dx - sa * dy + pivot[0] - sx
        ry = sa * dx + ca * dy + pivot[1] - sy
        sx = px - w * rx
        sy = py - w * ry
    return sx, sy


def head_w1(x, y):
    return np.clip((980 - y) / 190.0, 0, 1)


def head_w3(x, y):
    return np.clip((960 - y) / 170.0, 0, 1) * np.clip((x - 120) / 120.0, 0, 1)


def hair_sway(sx, sy, t, which):
    """secondary hair motion: lag + swing after the nod, tiny breeze before it (layer coords)."""
    if which == 1:
        w = np.clip((sy - 620) / 600.0, 0, 1) * np.clip((560 - sx) / 260.0, 0, 1)
        d = 2.0 * np.sin(t * 2.1 + sy / 160.0)
    else:
        w = np.clip((sy - 640) / 520.0, 0, 1) * np.clip((470 - sx) / 260.0, 0, 1)
        d = spring(t, T_SW, -14.0, 0.62, 0.38) + 1.6 * np.sin(t * 2.1 + sy / 150.0)
    return sx + w * d, sy + 0.3 * w * abs(d)


def layer_matrix(which):
    """output -> layer coords (inverse of layer -> A1 space -> output)."""
    if which == 1:
        L = np.eye(3)
    else:
        L = np.array([[S3, 0, T3[0]], [0, S3, T3[1]], [0, 0, 1]])
    O = np.array([[SO, 0, -FX0 * SO], [0, SO, -FY0 * SO], [0, 0, 1]])
    return np.linalg.inv(O @ L)


MI1, MI3 = layer_matrix(1), layer_matrix(3)


def sample(img, sx, sy):
    return cv2.remap(img, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def character(t, drawing=None):
    """straight-colour RGBA of the character at output resolution, plus which drawing is used.
    `drawing` fixes the drawing for every motion-blur subsample of one frame (no mixing of drawings)."""
    ang = head_angle(t, drawing)
    breath = 1.2 * np.sin((t - 7.5) * 2 * np.pi / 3.3) - 2.2 * smooth(t, T_ANT0, T_ANT1) * (t < T_SW)
    if (drawing or ('A1' if t < T_SW else 'A3')) == 'A1':
        sx, sy = rot_field(None, MI1, NECK1, ang, head_w1)
        sx, sy = hair_sway(sx, sy, t, 1)
        out = sample(A1, sx, sy + breath / SO * 0)
        return out, 'A1', ang, 0.0
    sx, sy = rot_field(None, MI3, NECK3, ang, head_w3)
    sx, sy = hair_sway(sx, sy, t, 3)
    out = sample(body3, sx, sy)
    aa = arm_angle(t)
    # forearm about the elbow
    a = np.radians(aa)                                # + lowers the hand forward/down toward the lap
    ca, sa = np.cos(a), np.sin(a)
    px = MI3[0, 0] * xx + MI3[0, 2]
    py = MI3[1, 1] * yy + MI3[1, 2]
    dx, dy = px - PIV3[0], py - PIV3[1]
    ax = ca * dx + sa * dy + PIV3[0]                  # inverse rotation
    ay = -sa * dx + ca * dy + PIV3[1]
    arm_o = sample(arm, ax, ay)
    al = arm_o[:, :, 3:]
    comp_a = al + out[:, :, 3:] * (1 - al)
    comp_c = (arm_o[:, :, :3] * al + out[:, :, :3] * out[:, :, 3:] * (1 - al)) / np.maximum(comp_a, 1e-4)
    return np.dstack([comp_c, comp_a]), 'A3', ang, aa


WARM = np.array([1.0, 0.72, 0.42])


def relight(rgba, lp, power):
    al = rgba[:, :, 3:]
    alb = rgba[:, :, :3]
    soft = cv2.GaussianBlur(al[:, :, 0], (0, 0), 14)
    gx = cv2.Sobel(soft, cv2.CV_32F, 1, 0, ksize=5)
    gy = cv2.Sobel(soft, cv2.CV_32F, 0, 1, ksize=5)
    nrm = np.dstack([-gx, -gy, np.full_like(gx, 0.04)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True) + 1e-6
    lv = np.dstack([lp[0] - xx, lp[1] - yy, np.full_like(xx, 160.0)])
    dist = np.linalg.norm(lv, axis=2, keepdims=True)
    lv /= dist
    lam = np.clip((nrm * lv).sum(2, keepdims=True), 0, 1)
    fall = 1.0 / (1.0 + (dist / 260.0) ** 2)
    amb = np.array([0.46, 0.50, 0.68])
    lit = alb * (amb + WARM * power * (0.35 + 0.65 * lam) * fall * 1.7)
    rim = np.clip(-(gx * 0.5 + gy * 0.85), 0, None)
    rim = (rim / (rim.max() + 1e-6))[:, :, None] * np.array([0.10, 0.13, 0.22])
    return np.dstack([np.clip(lit + rim * al, 0, 1.2), al])


def light_layer(lp, power):
    d2 = (xx - lp[0]) ** 2 + (yy - lp[1]) ** 2
    core = np.exp(-d2 / (2 * 7.0 ** 2))[:, :, None] * np.array([1.0, 0.95, 0.85])
    halo = np.exp(-d2 / (2 * 30.0 ** 2))[:, :, None] * WARM * 0.55
    glow = np.exp(-d2 / (2 * 150.0 ** 2))[:, :, None] * WARM * 0.16
    return (core * 1.4 + halo + glow) * power


def render(f, sub=1):
    acc = np.zeros((OH, OW, 3), np.float32)
    info = None
    for k in range(sub):
        t = (f + 0.5 * ((k + 0.5) / sub - 0.5)) / FPS if sub > 1 else f / FPS     # 180-degree shutter
        ch, which, ang, aa = character(t, 'A1' if f / FPS < T_SW else 'A3')
        lpc = light_pos(t)
        lp = to_out(lpc)
        pw = light_power(t)
        ch = relight(ch, lp, pw)
        al = ch[:, :, 3:]
        img = BG + light_layer(lp, pw) * 0.35 * (1 - al)      # light spill on the sky
        img = img * (1 - al) + ch[:, :, :3] * al
        img += light_layer(lp, pw) * 0.9                       # the light sits in front of the palm
        acc += img
        if info is None:
            info = dict(frame=f, t=round(f / FPS, 3), drawing=which, head_deg=round(float(ang), 2), forearm_deg=round(float(aa), 2),
                        light_out=[round(float(lp[0]), 1), round(float(lp[1]), 1)], light_power=round(float(pw), 3))
    img = acc / sub
    vig = 1 - 0.30 * (((xx - OW * 0.45) / OW) ** 2 + ((yy - OH * 0.5) / OH) ** 2)
    img = img * vig[:, :, None]
    img = img / (1 + 0.15 * img)                               # soft shoulder for the bright core
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)[:, :, ::-1], info


def subsamples(f):
    t = f / FPS
    fast = (T_ANT1 - 0.05 <= t <= T_SW + 0.25) or (T_ARM0 <= t <= T_ARM1 - 0.1)
    return 5 if fast else 1


if __name__ == '__main__':
    only = [int(x) for x in sys.argv[1].split(',')] if len(sys.argv) > 1 else range(F0, F1)
    log = []
    for f in only:
        o8, rec = render(f, subsamples(f))
        cv2.imwrite(os.path.join(OUTD, '%05d.png' % f), o8)
        log.append(rec)
    if len(sys.argv) == 1:
        json.dump({'frames': log}, open(os.path.join(R, 'tests', 'rev3_body_log.json'), 'w'), indent=1)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-start_number', str(F0), '-i', os.path.join(OUTD, '%05d.png'),
                        '-ss', '%.4f' % (F0 / FPS), '-t', '%.4f' % ((F1 - F0) / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-shortest', MP4], check=True)
    print('done', len(log))
