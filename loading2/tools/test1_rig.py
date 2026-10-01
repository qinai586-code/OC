"""ACCEPTANCE TEST 1 - character performance, gate G1 (S01 seated interaction), 0:07.50-0:12.50.

Technique under test (local, no fees): a 2D bone rig with smooth (linear-blend) weights on the existing
seated back-view drawings kv1_A / kv1_B (cut from the supplied KV1). Hips and hands are pinned to the
parapet (support); the spine bends waist -> chest -> neck; the head turns toward a light that arrives
and lands on the ledge (gaze shift); hair and A's tail follow with spring lag. Background is the
KV1 plate with the earlier pipeline's fill (not a clean plate).
This tests whether deformation of ONE drawing per character can carry the action. It cannot add
anatomy the drawing does not contain (no new face angle, no limb leaving its silhouette).
"""
import os, sys, json, subprocess
import numpy as np, cv2
sys.path.insert(0, '/home/user/OC/loading2/src')
from lw import gblur, smooth, smoother
from acting import char

OUT = '/home/user/OC/loading2/tests/test1_rig'
os.makedirs(OUT, exist_ok=True)
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
T0, T1, FPS = 7.50, 12.50, 24
OFF = {'A': (826, 980), 'B': (1555, 1042)}
LIGHT_LAND = np.array([1495.0, 1702.0])          # plate px: on the ledge between them

def R(th):
    c, s = np.cos(th), np.sin(th)
    return np.array([[c, -s], [s, c]])

def rot_about(c, th, t=(0, 0)):
    A = np.zeros((2, 3)); A[:, :2] = R(th); A[:, 2] = np.asarray(c) - R(th) @ np.asarray(c) + np.asarray(t)
    return A

def compose(A2, A1):                       # A2 after A1
    M = np.zeros((2, 3)); M[:, :2] = A2[:, :2] @ A1[:, :2]; M[:, 2] = A2[:, :2] @ A1[:, 2] + A2[:, 2]
    return M

I = rot_about((0, 0), 0.0)

def spring(target_fn, t, w=8.0, z=0.35, dt=1 / 240.0):
    """Lagging follower of target_fn (critically under-damped): integrated from T0-1 s."""
    x = target_fn(T0 - 1.0); v = 0.0
    tt = T0 - 1.0
    while tt < t:
        a = w * w * (target_fn(tt) - x) - 2 * z * w * v
        v += a * dt; x += v * dt; tt += dt
    return x

def soft_poly(shape, pts, blur):
    m = np.zeros(shape, np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0)
    return gblur(m, blur)

# ------------------------------------------------------------------ rig definitions (cut-out px)
RIG = {
 'A': dict(neck=(300, 255), chest=(300, 400), waist=(300, 560), hip=(300, 730),
           ys=(255, 330, 400, 560, 730),
           arms=[[(118, 300), (205, 330), (160, 560), (95, 770), (0, 780), (15, 600), (85, 400)],
                 [(482, 300), (395, 330), (440, 560), (515, 770), (610, 780), (595, 600), (515, 400)]],
           hands=[(40, 745), (565, 748)], arm_top=330, hand_y=745,
           hair=dict(cx=300, half=135, y0=270, y1=600, k=0.65),
           tail=[(300, 760), (340, 880), (390, 980)]),
 'B': dict(neck=(290, 245), chest=(320, 380), waist=(330, 520), hip=(330, 690),
           ys=(245, 310, 380, 520, 690),
           arms=[[(225, 280), (305, 320), (215, 470), (110, 610), (10, 620), (40, 540), (150, 380)]],
           hands=[(45, 590)], arm_top=320, hand_y=590,
           hair=dict(cx=340, half=250, y0=260, y1=700, k=0.75),
           tail=None),
}

# ------------------------------------------------------------------ performance curves (degrees, px)
def ease(t, a, b):
    return smoother(t, a, b)

def A_head(t):    # anticipation dip, then turn toward the light, settle with the landing
    return np.deg2rad(-2.0 * smooth(t, 7.85, 8.05) * (1 - smooth(t, 8.05, 8.3)) + 13.0 * ease(t, 8.05, 8.95) + 3.0 * ease(t, 10.15, 10.9))
def A_chest(t):
    return np.deg2rad(4.5 * ease(t, 8.3, 9.35) + 1.5 * ease(t, 10.2, 11.0))
def A_waist(t):
    return np.deg2rad(2.0 * ease(t, 8.45, 9.5))
def B_head(t):
    return np.deg2rad(-8.5 * ease(t, 8.65, 9.6) - 3.0 * ease(t, 10.2, 11.0))
def B_chest(t):
    return np.deg2rad(-3.0 * ease(t, 8.85, 9.9) - 1.0 * ease(t, 10.25, 11.1))
def B_waist(t):
    return np.deg2rad(-1.2 * ease(t, 9.0, 10.0))

CURVES = {'A': (A_head, A_chest, A_waist, (14.0, 8.0)), 'B': (B_head, B_chest, B_waist, (-10.0, 6.0))}

# ------------------------------------------------------------------ weights (half resolution)
WEIGHTS = {}
def weights(who, img):
    if who in WEIGHTS:
        return WEIGHTS[who]
    rg = RIG[who]; h, w = img.shape[:2]
    s = 2
    ys, xs = np.mgrid[0:h // s, 0:w // s].astype(np.float32) * s
    yn, y1, yc, yw, yh = rg['ys']
    def ss(a, b, y):
        u = np.clip((y - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
    wh = 1 - ss(yn, y1, ys)                                  # head (+ horns) above the neck
    wc = ss(yn, y1, ys) * (1 - ss(yc, yw, ys))               # chest
    ww = ss(yc, yw, ys) * (1 - ss(yw, yh, ys))               # waist
    wp = ss(yw, yh, ys)                                      # hips / seat (pinned)
    arm = np.zeros_like(xs)
    for poly in rg['arms']:
        arm = np.maximum(arm, cv2.resize(soft_poly((h, w), poly, 9), (w // s, h // s)))
    hr = rg['hair']
    hair = np.clip(1 - np.abs(xs - hr['cx']) / hr['half'], 0, 1) ** 0.5 * ss(hr['y0'] - 20, hr['y0'] + 40, ys) * (1 - ss(hr['y1'] - 90, hr['y1'], ys)) * hr['k']
    hair = hair * (1 - arm)
    tail = np.zeros_like(xs)
    if rg['tail']:
        tail = ss(rg['tail'][0][1] - 20, rg['tail'][0][1] + 20, ys) * (np.abs(xs - 330) < 200)
        wp = wp * (1 - tail)
    tarm = np.clip((ys - rg['arm_top']) / (rg['hand_y'] - rg['arm_top']), 0, 1)
    WEIGHTS[who] = dict(xs=xs, ys=ys, wh=wh, wc=wc, ww=ww, wp=wp, arm=arm, hair=hair, tail=tail, tarm=tarm, s=s)
    return WEIGHTS[who]

def apply(A, xs, ys):
    return A[0, 0] * xs + A[0, 1] * ys + A[0, 2], A[1, 0] * xs + A[1, 1] * ys + A[1, 2]

def deform(who, img, t):
    rg = RIG[who]; W = weights(who, img)
    fh, fc, fw, (hx, hy) = CURVES[who]
    th_h, th_c, th_w = fh(t), fc(t), fw(t)
    lag_h = spring(fh, t)                                     # hair follows the head with lag
    Aw = rot_about(rg['waist'], th_w)
    Ac = compose(Aw, rot_about(rg['chest'], th_c))
    head_shift = (hx * th_h / max(1e-6, np.deg2rad(16.0)), hy * abs(th_h) / max(1e-6, np.deg2rad(16.0)))
    Ah = compose(Ac, rot_about(rg['neck'], th_h, head_shift))
    Ahair = compose(Ac, rot_about(rg['neck'], 0.8 * lag_h, (0.8 * hx * lag_h / np.deg2rad(16.0), 0)))
    xs, ys = W['xs'], W['ys']
    fx = np.zeros_like(xs); fy = np.zeros_like(ys)
    def add(A, wgt):
        nonlocal fx, fy
        X, Y = apply(A, xs, ys); fx += wgt * (X - xs); fy += wgt * (Y - ys)
    body = 1 - W['arm']
    add(Ah, W['wh'] * body); add(Ac, W['wc'] * body * (1 - W['hair'])); add(Aw, W['ww'] * body * (1 - W['hair']))
    add(Ahair, (W['wc'] + W['ww']) * body * W['hair'])
    # arms: chest at the shoulder -> pinned at the hand (support)
    ta = W['tarm']; ta = ta * ta * (3 - 2 * ta)
    Xc, Yc = apply(Ac, xs, ys)
    fx += W['arm'] * (1 - ta) * (Xc - xs); fy += W['arm'] * (1 - ta) * (Yc - ys)
    if rg['tail']:
        # tail swings against the lean, lags and settles
        sw = spring(lambda u: -0.5 * fc(u) - 0.25 * fh(u), t, w=5.0, z=0.3)
        j0, j1, j2 = rg['tail']
        A1 = rot_about(j0, 0.35 * sw); A2 = compose(A1, rot_about(j1, 0.5 * sw)); A3 = compose(A2, rot_about(j2, 0.7 * sw))
        u = np.clip((ys - j0[1]) / (1068 - j0[1]), 0, 1)
        for A, wgt in ((A1, (1 - u) ** 2), (A2, 2 * u * (1 - u)), (A3, u ** 2)):
            X, Y = apply(A, xs, ys); fx += W['tail'] * wgt * (X - xs); fy += W['tail'] * wgt * (Y - ys)
    # inverse map by fixed-point iteration (forward displacement -> backward sampling)
    h, w = img.shape[:2]
    s = W['s']
    gx, gy = np.meshgrid(np.arange(w // s, dtype=np.float32) * s, np.arange(h // s, dtype=np.float32) * s)
    sx, sy = gx.copy(), gy.copy()
    for _ in range(8):
        dx = cv2.remap(fx.astype(np.float32), sx / s, sy / s, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        dy = cv2.remap(fy.astype(np.float32), sx / s, sy / s, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        sx, sy = gx - dx, gy - dy
    mx = cv2.resize(sx, (w, h), interpolation=cv2.INTER_LINEAR)
    my = cv2.resize(sy, (w, h), interpolation=cv2.INTER_LINEAR)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    mag = float(np.sqrt(fx ** 2 + fy ** 2).max())
    return out, mag, (np.degrees(th_h), np.degrees(th_c), np.degrees(th_w), np.degrees(lag_h))

# ------------------------------------------------------------------ render
plate = np.load('/home/user/OC/loading/work/derived/KV1_clean.npy').astype(np.float32)
CX0, CY0, CW, CH = 560, 900, 2000, 1125
imgs = {'A': char('kv1_A'), 'B': char('kv1_B')}
log = []
f0, f1 = int(round(T0 * FPS)), int(round(T1 * FPS))
for f in range(f0, f1):
    t = f / FPS
    canvas = plate.copy()
    info = {}
    for who in ('A', 'B'):
        im, mag, ang = deform(who, imgs[who], t)
        ox, oy = OFF[who]; h, w = im.shape[:2]
        a = im[:, :, 3:4]
        canvas[oy:oy + h, ox:ox + w] = canvas[oy:oy + h, ox:ox + w] * (1 - a) + im[:, :, :3] * a
        info[who] = {'max_disp_px': round(mag, 1), 'head_deg': round(ang[0], 2), 'chest_deg': round(ang[1], 2), 'waist_deg': round(ang[2], 2), 'hair_lag_deg': round(ang[3], 2)}
    # the arriving light: from the city on the right, lands on the ledge between them at 10.15 s
    u = smoother(t, 7.55, 10.15)
    p0 = np.array([2350.0, 1350.0]); p2 = LIGHT_LAND; p1 = np.array([1950.0, 1050.0])
    p = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u ** 2 * p2
    yy, xx = np.mgrid[0:canvas.shape[0], 0:canvas.shape[1]]
    roi = (slice(int(p[1]) - 260, int(p[1]) + 260), slice(int(p[0]) - 260, int(p[0]) + 260))
    d2 = (xx[roi] - p[0]) ** 2 + (yy[roi] - p[1]) ** 2
    glow = (np.exp(-d2 / (2 * 9.0 ** 2)) * 2.5 + np.exp(-d2 / (2 * 45.0 ** 2)) * 0.5 + np.exp(-d2 / (2 * 140.0 ** 2)) * 0.18) * smooth(t, 7.5, 7.8)
    canvas[roi] += glow[:, :, None] * np.array([1.0, 0.75, 0.42], np.float32)
    crop = canvas[CY0:CY0 + CH, CX0:CX0 + CW]
    out = cv2.resize(np.clip(crop, 0, 1), (1920, 1080), interpolation=cv2.INTER_AREA)
    o8 = (out * 255).astype(np.uint8)[:, :, ::-1].copy()
    cv2.putText(o8, 'ACCEPTANCE TEST 1 - G1 seated interaction - deformation rig on single drawings - not final animation', (20, 36), 0, 0.75, (220, 220, 220), 2, cv2.LINE_AA)
    cv2.putText(o8, f'{t:6.3f}s  f{f}', (20, 1060), 0, 0.8, (180, 220, 255), 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(OUT, f'{f:05d}.png'), o8)
    log.append({'frame': f, 't': round(t, 3), **{k + '_' + kk: vv for k, v in info.items() for kk, vv in v.items()}})
json.dump(log, open(os.path.join(OUT, 'test1_log.json'), 'w'), indent=1)
mp4 = '/home/user/OC/loading2/tests/TEST1_seated_performance.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-start_number', str(f0), '-i', os.path.join(OUT, '%05d.png'),
                '-ss', f'{f0 / FPS:.4f}', '-t', f'{(f1 - f0) / FPS:.4f}', '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-c:a', 'aac', '-b:a', '192k', '-shortest', mp4], check=True)
print('frames', len(log), 'max displacement A', max(r['A_max_disp_px'] for r in log), 'B', max(r['B_max_disp_px'] for r in log))
