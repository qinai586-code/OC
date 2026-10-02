"""REV3b light catch, 0:07.50-0:12.50: a motivated three-shot edit (option B).

Why an edit and not a continuous move: the only drawings are A1 (chin up, lips parted) and A3 (level
gaze, palm raised). There is no drawn in-between, so a continuous head-and-arm move between them
pops (rev3, local frame 32->33). Each shot below uses one drawing, and every cut moves the action on.

  SHOT 1  7.500-9.125  A1, MCU. A notices the warm light high in the sky and watches it sink.
  SHOT 2  9.167-10.667 Insert on her hand (A3's drawn forearm). It rises into frame about the elbow
                       and opens under the light; the light comes in from the top right and slows
                       above the palm.
  SHOT 3 10.667-12.458 A3, tighter MCU. She is looking down at her palm as the light touches it; the
                       palm gives and recovers, warm light reaches her face, hair settles.

Continuity kept across the cuts: she faces screen right in every shot; the light travels top-right
to bottom-left along one path in a shared space ("A1 space" canvas), seen by three cameras; the palm
in shot 2 is the same drawing and pose as in shot 3; same night grade and the same warm light.
The A3 back-of-head (bun and ribbon drawn differently from A1) is kept out of shot 3's frame.
No crossfades, no squeeze, no optical flow; motion blur only as a 180-degree shutter on the arm rise.

  python3 rev3/tools/body2.py  -> rev3/tests/REV3b_light_catch.mp4 (+ frames in rev3/work/body2)
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
import body as B  # noqa: E402  (prepared, re-inked A1 / A3 layers, arm split, relight, light sprite)

OUTD = os.path.join(R, 'work', 'body2')
MP4 = os.path.join(R, 'tests', 'REV3b_light_catch.mp4')
os.makedirs(OUTD, exist_ok=True)
FPS, OW, OH = 24, 1920, 1080
F0, F1 = 180, 300
CUT1, CUT2 = 220, 256                      # first frame of shot 2 and shot 3
xx, yy = B.xx, B.yy

# cameras: (x0, y0, width) of the frame in A1 space
CAM = {1: (300.0, 60.0, 2260.0),           # MCU, A at left, sky in her eye line
       2: (905.0, 600.0, 1000.0),          # insert: palm and the approaching light (her face is left of frame)
       3: (480.0, 90.0, 1850.0)}           # tighter MCU: head and whole hand (A3 bun/ribbon left of frame)
KV = B.kv
PALM_C = B.S3 * B.PALM3 + B.T3             # palm in A1 space


def cam_mat(c):
    x0, y0, w = CAM[c]
    s = OW / w
    return np.array([[s, 0, -x0 * s], [0, s, -y0 * s], [0, 0, 1]])


def to_out(c, p):
    M = cam_mat(c)
    return (M[:2, :2] @ np.asarray(p, np.float64) + M[:2, 2]).astype(np.float32)


def background(c):
    """one plate (KV1, sky and lit Earth limb) placed in A1 space; each camera frames its own part of it,
    defocused by focal length (the insert's longer lens is softer)."""
    x0, y0, w = CAM[c]
    k = 1022.0 / CAM[1][2]                         # KV1 px per A1-space px (the rev3 wide framing)
    kx0 = 2050 + (x0 - CAM[1][0]) * k
    ky0 = 525 + (y0 - CAM[1][1]) * k
    pw, ph = w * k, w * k * 9 / 16
    crop = KV[int(ky0):int(ky0 + ph), int(kx0):int(kx0 + pw)]
    img = cv2.resize(crop, (OW, OH), interpolation=cv2.INTER_CUBIC)
    sig = {1: 3.0, 2: 9.0, 3: 5.0}[c]
    return cv2.GaussianBlur(img, (0, 0), sig) * 0.92


BGS = {c: background(c) for c in CAM}


def smooth(t, a, b):
    x = np.clip((t - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def ease_out(t, a, b):
    x = np.clip((t - a) / (b - a), 0, 1)
    return 1 - (1 - x) ** 3


T_CUT1, T_CUT2 = CUT1 / FPS, CUT2 / FPS
T_LAND = T_CUT2 + 0.25                       # touches the palm 6 frames into shot 3


def light_pos(t):
    """one continuous path in A1 space: high right -> above the palm -> in the palm."""
    p0 = np.array([2380.0, 70.0])
    p1 = np.array([1650.0, 230.0])
    p2 = PALM_C + np.array([12.0, -38.0])    # hovering just above the palm
    if t < T_LAND - 0.25:
        u = (t - 7.5) / (T_LAND - 0.25 - 7.5)
        u = 0.35 * u + 0.65 * (1 - (1 - u) ** 2)              # starts drifting, slows toward the palm
        q = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u ** 2 * p2
    else:
        v = smooth(t, T_LAND - 0.25, T_LAND)
        q = p2 * (1 - v) + (PALM_C + np.array([4.0, -12.0])) * v
        if t >= T_LAND:
            q = q + np.array([0.0, 7.0]) * np.sin(np.pi * min((t - T_LAND) / 0.36, 1.0)) * np.exp(-(t - T_LAND) / 0.3)
    q = q + np.array([3.0 * np.sin(t * 2.3), 2.0 * np.sin(t * 3.1)])     # a little float
    return q


def light_power(t):
    p = 0.5 + 0.45 * smooth(t, 8.6, T_LAND)
    if t >= T_LAND:
        p += 0.6 * np.exp(-(t - T_LAND) / 0.35)
    return p * (1 + 0.04 * np.sin(t * 11.0))


def arm_angle(t):
    """shot 2: the forearm rises about the elbow; shot 3: it is up, gives on contact and recovers."""
    if t < T_CUT2:
        return 70.0 * (1 - ease_out(t, T_CUT1 - 0.15, T_CUT1 + 0.67))      # cut lands mid-rise (match on action) - 3.0 * np.sin(np.pi * smooth(t, T_CUT1 + 0.55, T_CUT1 + 1.05))
    d = 0.0
    if t >= T_LAND:
        u = t - T_LAND
        d = 2.4 * np.sin(np.pi * min(u / 0.2, 1.0)) * np.exp(-u / 0.25) + 0.5 * np.exp(-u / 0.4) * np.sin(2 * np.pi * u / 0.55)
    return d


def hair_a1(sx, sy, t):
    w = np.clip((sy - 620) / 600.0, 0, 1) * np.clip((560 - sx) / 260.0, 0, 1)
    return sx + w * 1.8 * np.sin(t * 2.0 + sy / 160.0), sy


def hair_a3(sx, sy, t):
    # she has just moved her arm: a small settle, then breeze
    w = np.clip((sy - 640) / 520.0, 0, 1) * np.clip((470 - sx) / 260.0, 0, 1)
    d = 4.0 * np.exp(-max(t - T_CUT2, 0) / 0.5) * np.sin(2 * np.pi * (t - T_CUT2) / 0.8) + 1.4 * np.sin(t * 2.0 + sy / 150.0)
    return sx + w * d, sy


def layer_inv(c, layer):
    L = np.eye(3) if layer == 1 else np.array([[B.S3, 0, B.T3[0]], [0, B.S3, B.T3[1]], [0, 0, 1]])
    return np.linalg.inv(cam_mat(c) @ L)


def sample(img, sx, sy):
    return cv2.remap(img, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)


def character(c, t):
    breath = 1.0 * np.sin((t - 7.5) * 2 * np.pi / 3.3)
    if c == 1:
        Mi = layer_inv(1, 1)
        sx = Mi[0, 0] * xx + Mi[0, 2]
        sy = Mi[1, 1] * yy + Mi[1, 2] - breath
        sx, sy = hair_a1(sx, sy, t)
        return np.clip(sample(B.A1, sx, sy), 0, 1)
    Mi = layer_inv(c, 3)
    px = Mi[0, 0] * xx + Mi[0, 2]
    py = Mi[1, 1] * yy + Mi[1, 2] - breath / B.S3
    sx, sy = hair_a3(px, py, t)
    out = np.clip(sample(B.body3, sx, sy), 0, 1)
    a = np.radians(arm_angle(t))
    ca, sa = np.cos(a), np.sin(a)
    dx, dy = px - B.PIV3[0], py - B.PIV3[1]
    ax = ca * dx + sa * dy + B.PIV3[0]
    ay = -sa * dx + ca * dy + B.PIV3[1]
    arm = np.clip(sample(B.arm, ax, ay), 0, 1)
    al = arm[:, :, 3:]
    ca_ = al + out[:, :, 3:] * (1 - al)
    cc = (arm[:, :, :3] * al + out[:, :, :3] * out[:, :, 3:] * (1 - al)) / np.maximum(ca_, 1e-4)
    return np.dstack([cc, ca_])


def render(f):
    c = 1 if f < CUT1 else (2 if f < CUT2 else 3)
    fast = c == 2 and f < CUT1 + 18          # arm rise only: 180-degree shutter, 3 samples
    subs = [f + 0.5 * ((k + 0.5) / 3 - 0.5) for k in range(3)] if fast else [f]
    acc = np.zeros((OH, OW, 3), np.float32)
    for fs in subs:
        t = fs / FPS
        ch = character(c, t)
        lp = to_out(c, light_pos(t))
        pw = light_power(t)
        scale = OW / CAM[c][2] / (OW / CAM[1][2])            # light sprite and falloff follow the lens
        ch = relight_scaled(ch, lp, pw, scale)
        al = ch[:, :, 3:]
        lay = light_layer(lp, pw, scale)
        img = BGS[c] + lay * 0.35 * (1 - al)
        img = img * (1 - al) + ch[:, :, :3] * al
        img += lay * 0.9
        acc += img
    img = acc / len(subs)
    vig = 1 - 0.30 * (((xx - OW * 0.45) / OW) ** 2 + ((yy - OH * 0.5) / OH) ** 2)
    img = img * vig[:, :, None]
    img = img / (1 + 0.15 * img)
    t = f / FPS
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)[:, :, ::-1], dict(
        frame=f, local_frame=f - F0, song_t=round(t, 3), shot=c, forearm_deg=round(float(arm_angle(t)), 2),
        light_A1space=[round(float(v), 1) for v in light_pos(t)], light_power=round(float(light_power(t)), 3))


def relight_scaled(rgba, lp, power, scale):
    al = rgba[:, :, 3:]
    alb = rgba[:, :, :3]
    soft = cv2.GaussianBlur(al[:, :, 0], (0, 0), 14 * scale)
    gx = cv2.Sobel(soft, cv2.CV_32F, 1, 0, ksize=5)
    gy = cv2.Sobel(soft, cv2.CV_32F, 0, 1, ksize=5)
    nrm = np.dstack([-gx, -gy, np.full_like(gx, 0.04 / scale)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True) + 1e-6
    lv = np.dstack([lp[0] - xx, lp[1] - yy, np.full_like(xx, 160.0 * scale)])
    dist = np.linalg.norm(lv, axis=2, keepdims=True)
    lv /= dist
    lam = np.clip((nrm * lv).sum(2, keepdims=True), 0, 1)
    fall = 1.0 / (1.0 + (dist / (260.0 * scale)) ** 2)
    amb = np.array([0.46, 0.50, 0.68])
    lit = alb * (amb + B.WARM * power * (0.35 + 0.65 * lam) * fall * 1.7)
    rim = np.clip(-(gx * 0.5 + gy * 0.85), 0, None)
    rim = (rim / (rim.max() + 1e-6))[:, :, None] * np.array([0.10, 0.13, 0.22])
    return np.dstack([np.clip(lit + rim * al, 0, 1.2), al])


def light_layer(lp, power, scale):
    d2 = (xx - lp[0]) ** 2 + (yy - lp[1]) ** 2
    core = np.exp(-d2 / (2 * (7.0 * scale) ** 2))[:, :, None] * np.array([1.0, 0.95, 0.85])
    halo = np.exp(-d2 / (2 * (30.0 * scale) ** 2))[:, :, None] * B.WARM * 0.55
    glow = np.exp(-d2 / (2 * (150.0 * scale) ** 2))[:, :, None] * B.WARM * 0.16
    return (core * 1.4 + halo + glow) * power


if __name__ == '__main__':
    only = [int(x) for x in sys.argv[1].split(',')] if len(sys.argv) > 1 else range(F0, F1)
    log = []
    for f in only:
        o8, rec = render(f)
        cv2.imwrite(os.path.join(OUTD, '%05d.png' % f), o8)
        log.append(rec)
    if len(sys.argv) == 1:
        json.dump({'cuts_song_frames': [CUT1, CUT2], 'frames': log}, open(os.path.join(R, 'tests', 'rev3b_light_catch_log.json'), 'w'), indent=1)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-start_number', str(F0), '-i', os.path.join(OUTD, '%05d.png'),
                        '-ss', '%.4f' % (F0 / FPS), '-t', '%.4f' % ((F1 - F0) / FPS), '-i', B.AUDIO, '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-shortest', MP4], check=True)
    print('done', len(log))
