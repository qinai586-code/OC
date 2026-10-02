"""Opening 0:00-13.583 as one continuous 720p preview on the locked music.

STATUS: WORK IN PROGRESS, PAUSED BY THE OWNER (2026-10-02) BEFORE ITS FIRST RENDER. The design is under
review in rev3/OPENING_VERSE1_PLAN.md and may change. The first run stopped in head_disp (full-frame head
weights used with the cropped head region); the fix below (sub-region weights) has not been run.

  python3 rev3/tools/opening.py   ->  rev3/tests/OPENING_0000-1358_720p.mp4 (+ opening_log.json)

Measured music (locked master; vocal stem for the voice):
  0.232  pad enters (silence before)         3.344-3.820  six-note chime cluster (accompaniment onsets
  5.631  "three"   6.641  "two"   7.500  "one" (sustained to 11.59)      3.344 3.471 3.529 3.634 3.704 3.820)
  13.061 "Loading."   13.45-13.75 near-silence (the breath)   13.80 glitch, 13.91 next line

Shots (one source picture, KV1, for the setting; the approved light catch after it):
  O1  0.000-5.625 (frames   0-134)  The world loads around the one who is watching it. Black; the night
                                     side's city lights switch on first, the Earth fills in around them,
                                     and the camera pulls back from the lights to find A and B on the
                                     ledge, from behind. On the chime one small city light straight ahead
                                     of them wakes, a pulse per note, and lifts off; it climbs toward them.
  O2  5.625-7.500 (frames 135-179)  Cut on "three", closer, from behind: A's head tips back to follow the
                                     light rising past the horizon; on "two" B turns to follow her gaze;
                                     the light slows near its height above them.
  S1-S3 7.500-13.583 (180-325)       Approved light catch (cut on "one"), rebuilt by p1_local.py.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
import p1_local as P  # noqa: E402
from p1s1_light import glow_profile  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R))
KV1 = os.path.join(ROOT, 'loading', 'work', 'plates', 'KV1.png')
CHARS = os.path.join(ROOT, 'loading2', 'work', 'chars')
WORK = os.path.join(R, 'work', 'opening')
OUT = os.path.join(R, 'tests', 'OPENING_0000-1358_720p.mp4')
LOG = os.path.join(R, 'tests', 'opening_log.json')
AUDIO = P.AUDIO
OW, OH, FPS = 1280, 720, 24
N_O1, N_O2 = 135, 45                                 # frames 0-134, 135-179; S1 starts at 180 (7.500)
PAD_IN = 0.232
CHIMES = [3.344, 3.471, 3.529, 3.634, 3.704, 3.820]
THREE, TWO, ONE = 5.631, 6.641, 7.500
BIRTH = np.array([1571.0, 1167.0])                   # the lone city light between them (KV1 px), measured
APEX = np.array([1598.0, 545.0])                     # its height when she turns to it (cut to S1 on "one")


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- camera
def cam(t):
    """crop centre and width in KV1 px."""
    if t < N_O1 / FPS:                                # O1: pull back from the lights, then a slow push
        if t < 3.30:
            u = smooth((t - 0.10) / 3.20)
            c0, c1 = np.array([600.0, 1290.0]), np.array([1536.0, 1090.0])
            w = np.exp(np.log(1150.0) * (1 - u) + np.log(2950.0) * u)
            return c0 * (1 - u) + c1 * u, w
        u = (t - 3.30) / (N_O1 / FPS - 3.30)
        return np.array([1536.0, 1090.0]) * (1 - u) + np.array([1548.0, 1080.0]) * u, 2950.0 - 230.0 * u
    u = (t - N_O1 / FPS) / (N_O2 / FPS)               # O2: closer, a slow push
    return np.array([1490.0, 935.0]) * (1 - u) + np.array([1505.0, 930.0]) * u, 1720.0 - 150.0 * u


def sample(img, half, c, w, interp=cv2.INTER_LINEAR):
    s = OW / w
    src, k = (half, 0.5) if (half is not None and s < 0.6) else (img, 1.0)
    s2 = s / k
    M = np.float32([[s2, 0, OW / 2 - s2 * c[0] * k], [0, s2, OH / 2 - s2 * c[1] * k]])
    return cv2.warpAffine(src, M, (OW, OH), flags=interp, borderMode=cv2.BORDER_REFLECT)


def to_out_xy(p, c, w):
    s = OW / w
    return np.array([OW / 2 + s * (p[0] - c[0]), OH / 2 + s * (p[1] - c[1])]), s


# ---------------------------------------------------------------- the light
def light_state(t):
    """position (KV1 px), size (x the approved orb's radius, in KV1 px) and intensity."""
    if t < CHIMES[0]:
        return BIRTH, 0.10, 0.0
    pulses = sum(0.9 * np.exp(-(t - on) / 0.07) for on in CHIMES if t >= on)
    level = 0.30 + 0.70 * smooth((t - CHIMES[0]) / (CHIMES[-1] - CHIMES[0] + 0.15))
    x = (t - CHIMES[-1]) / (ONE - CHIMES[-1])
    u = smooth(x) if x > 0 else 0.0
    p = BIRTH * (1 - u) + APEX * u + np.array([-26.0, 0.0]) * np.sin(np.pi * u)   # a slight arc, not a rail
    p = p + np.array([2.5 * np.sin(2 * np.pi * t / 1.3), 0.0]) * u                # a slow float as it rises
    size = 0.10 + 0.32 * u
    if t >= TWO:
        pulses += 0.35 * np.exp(-(t - TWO) / 0.12)                                 # it answers "two"
    return p, size, level + pulses


def draw_light(fr, p_out, scale_px, inten, prof, occl=None, trail=()):
    rr, add = prof
    H, W = fr.shape[:2]
    x0, y0 = int(max(0, p_out[0] - 200)), int(max(0, p_out[1] - 200))
    x1, y1 = int(min(W, p_out[0] + 200)), int(min(H, p_out[1] + 200))
    if x1 <= x0 or y1 <= y0:
        return fr
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    L = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
    for (q, sc, it) in [(p_out, scale_px, inten)] + list(trail):
        sc = max(sc, 0.075)
        d = np.clip(np.hypot(xx - q[0], yy - q[1]) / sc, 0, rr[-1])
        L += np.stack([np.interp(d, rr, add[:, c]) for c in range(3)], -1) * it
    if occl is not None:
        L *= (1 - occl[y0:y1, x0:x1, None])
    fr[y0:y1, x0:x1] += L
    return fr


# ---------------------------------------------------------------- characters (O2 head moves)
def char_alpha(shape):
    off = json.load(open(os.path.join(CHARS, 'offsets.json')))
    out = {}
    for n in ('kv1_A', 'kv1_B'):
        a = cv2.imread(os.path.join(CHARS, n + '.png'), cv2.IMREAD_UNCHANGED)[..., 3].astype(np.float32) / 65535.0
        x0, y0, x1, y1 = off[n]
        m = np.zeros(shape[:2], np.float32)
        h, w = min(a.shape[0], shape[0] - y0), min(a.shape[1], shape[1] - x0)
        m[y0:y0 + h, x0:x0 + w] = a[:h, :w]
        out[n] = m
    return out


def head_rig(kv, alphas):
    """per-character rigid head + decaying hair weights and a background plate under the moving parts."""
    H, W = kv.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rig = {
        'A': dict(alpha=alphas['kv1_A'], piv=(1125.0, 1320.0),
                  head=[(978, 985), (1272, 985), (1290, 1150), (1272, 1322), (992, 1322), (968, 1150)],
                  hair=[(930, 1290), (1330, 1290), (1380, 1720), (880, 1720)], y_hair=(1310, 1660)),
        'B': dict(alpha=alphas['kv1_B'], piv=(1858.0, 1345.0),
                  head=[(1722, 1128), (1995, 1128), (2006, 1250), (1990, 1352), (1728, 1352), (1712, 1250)],
                  hair=[(1690, 1330), (2020, 1330), (2250, 1810), (1590, 1810)], y_hair=(1340, 1720)),
    }
    moving = np.zeros((H, W), np.float32)
    for r in rig.values():
        r['w_head'] = P.poly_mask(kv.shape, r['head'], 5)
        hy0, hy1 = r['y_hair']
        r['w_hair'] = P.poly_mask(kv.shape, r['hair'], 12) * (np.clip((hy1 - yy) / (hy1 - hy0), 0, 1) ** 1.5) * (1 - r['w_head'])
        moving = np.maximum(moving, np.maximum(r['w_head'], r['w_hair']) * (r['alpha'] > 0.05))
    pp = os.path.join(WORK, 'kv1_plate_heads.png')
    if not os.path.exists(pp):                     # background under the moving parts, filled at half res
        reg = cv2.dilate((moving > 0.02).astype(np.uint8), np.ones((15, 15), np.uint8))
        h2 = cv2.resize(kv.astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        r2 = cv2.resize(reg, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
        f2 = cv2.inpaint(h2, r2 * 255, 6, cv2.INPAINT_TELEA)
        full = cv2.resize(f2, (W, H), interpolation=cv2.INTER_CUBIC)
        plate = np.where(reg[..., None] > 0, full, kv.astype(np.uint8))
        cv2.imwrite(pp, plate)
    return rig, cv2.imread(pp).astype(np.float32)


def head_disp(r, xx, yy, roll, comp, tx, ty, lag_roll, lag_comp):
    """a head tipping back seen from above-behind: the head shortens toward the neck (crown comes toward
    the camera) and rolls toward what it looks at; the hair follows, lagging and decaying downward."""
    piv = r['piv']
    rx, ry = P.rot_disp(xx, yy, piv, roll)
    hx, hy = rx + tx, ry + (piv[1] - yy) * comp + ty
    lx, ly = P.rot_disp(xx, yy, piv, lag_roll)
    gx, gy = lx + tx * 0.6, ly + (piv[1] - yy) * lag_comp + ty * 0.6
    wh, wr = r['w_head_sub'], r['w_hair_sub']
    DX = wh * hx + wr * gx
    DY = wh * hy + wr * gy
    return DX, DY


def pose(t, start, dur, amp_roll, amp_comp, amp_tx, amp_ty, lag=0.12):
    def f(tt):
        u = smooth((tt - start) / dur)
        over = 0.08 * np.sin(np.pi * np.clip((tt - start - dur) / 0.35, 0, 1))
        return u + over
    a, b = f(t), f(t - lag)
    return amp_roll * a, amp_comp * a, amp_tx * a, amp_ty * a, amp_roll * b, amp_comp * b


# ---------------------------------------------------------------- build
def build_opening():
    os.makedirs(WORK, exist_ok=True)
    kv = cv2.imread(KV1).astype(np.float32)
    H, W = kv.shape[:2]
    half = cv2.resize(kv, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    prof = glow_profile()
    k16 = kv.astype(np.int16)
    b, g, r_ = k16[..., 0], k16[..., 1], k16[..., 2]
    lum = k16.mean(2)
    lights = np.clip((r_ - 110) / 90.0, 0, 1) * np.clip((r_ - b - 40) / 50.0, 0, 1) * (np.arange(H)[:, None] > 850)
    stars = np.clip((lum - 110) / 60.0, 0, 1) * (np.arange(H)[:, None] < 840)
    Lm = np.clip(np.maximum(lights, stars), 0, 1).astype(np.float32)
    lab_n, lab = cv2.connectedComponents((cv2.dilate((Lm > 0.15).astype(np.uint8), np.ones((5, 5), np.uint8))))
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dn = np.hypot(xx - 600, yy - 1290) / np.hypot(3072, 2048) * 1.6           # 0 where we start, ~1 far away
    jitter = rng.uniform(0, 1, lab_n).astype(np.float32)[lab]
    phase = rng.uniform(0, 2 * np.pi, lab_n).astype(np.float32)[lab]
    t_on = (0.30 + 1.05 * np.clip(dn, 0, 1.3) + 0.45 * jitter).astype(np.float32)
    maps = np.dstack([Lm, dn.astype(np.float32), t_on, phase])
    maps_half = cv2.resize(maps, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    alphas = char_alpha(kv.shape)
    occ_full = np.clip(alphas['kv1_A'] + alphas['kv1_B'], 0, 1)
    rig, plate = head_rig(kv, alphas)
    bx0, by0, bx1, by1 = 860, 940, 2300, 1860                                   # region where heads/hair move
    sub = (slice(by0, by1), slice(bx0, bx1))
    syy, sxx = yy[sub], xx[sub]
    prem = {k: kv[sub] * v['alpha'][sub][..., None] for k, v in rig.items()}
    for v in rig.values():
        v['w_head_sub'], v['w_hair_sub'] = v['w_head'][sub], v['w_hair'][sub]
    frames, log = [], []
    for f in range(N_O1 + N_O2):
        t = f / FPS
        c, w = cam(t)
        src = kv
        if f >= N_O1:                                                            # O2: heads
            comp = plate[sub].copy()
            moved = np.zeros(syy.shape, np.float32)
            occ_sub = np.zeros(syy.shape, np.float32)
            for k, (start, dur, roll, cmp_, tx, ty) in (('A', (THREE + 0.06, 0.62, -3.2, 0.055, 2.0, 3.0)),
                                                       ('B', (TWO + 0.04, 0.50, 3.4, 0.045, -2.0, 3.0))):
                rr_, cc_, tx_, ty_, lr, lc = pose(t, start, dur, roll, cmp_, tx, ty)
                DX, DY = head_disp(rig[k], sxx, syy, rr_, cc_, tx_, ty_, lr, lc)
                lay = P.warp(prem[k], DX, DY, cv2.BORDER_CONSTANT)
                aw = P.warp(rig[k]['alpha'][sub], DX, DY, cv2.BORDER_CONSTANT)
                comp = comp * (1 - aw[..., None]) + lay
                occ_sub = np.maximum(occ_sub, aw)
                moved = np.maximum(moved, np.clip(np.hypot(DX, DY) / 0.3, 0, 1))
            moved = cv2.GaussianBlur(cv2.dilate(moved, np.ones((7, 7), np.uint8)), (0, 0), 2)[..., None]
            src = kv.copy()
            src[sub] = comp * moved + kv[sub] * (1 - moved)
            occ = occ_full.copy()
            occ[sub] = np.where(moved[..., 0] > 0.5, occ_sub, occ_full[sub])
            fr = sample(src, None, c, w)
            occ_o = sample(occ, None, c, w)
        else:
            fr = sample(src, half, c, w, cv2.INTER_LINEAR)
            occ_o = sample(occ_full, None, c, w)
            mp = sample(maps, maps_half, c, w)
            Lo, dno, ton, ph = mp[..., 0], mp[..., 1], mp[..., 2], mp[..., 3]
            reveal = smooth((t - 0.85 - 1.25 * np.clip(dno, 0, 1.3)) / 0.9)      # the world fills in outward
            lights_on = Lo * smooth((t - ton) / 0.12)
            twinkle = 1.0 + 0.10 * Lo * np.sin(2 * np.pi * t * 0.9 + ph)
            gate = smooth((t - PAD_IN) / 0.35)                                   # black until the pad enters
            fr = fr * (np.maximum(reveal, lights_on) * twinkle * gate)[..., None]
        if f >= N_O1:
            ph = sample(maps, None, c, w)
            fr = fr * (1.0 + 0.08 * ph[..., 0] * np.sin(2 * np.pi * t * 0.9 + ph[..., 3]))[..., None]
        p, size, inten = light_state(t)
        if inten > 0:
            po, s = to_out_xy(p, c, w)
            trail = []
            for dt in (0.04, 0.08, 0.13, 0.19, 0.26):
                if t - dt > CHIMES[-1]:
                    q, sq, _ = light_state(t - dt)
                    qo, _ = to_out_xy(q, c, w)
                    trail.append((qo, sq * s * 0.7, 0.10 * np.exp(-dt / 0.12)))
            fr = draw_light(fr, po, size * s, inten, prof, occl=occ_o, trail=trail)
        frames.append(np.clip(fr, 0, 255).astype(np.uint8))
        if f % 12 == 0 or f in (N_O1 - 1, N_O1, N_O1 + N_O2 - 1):
            log.append(dict(frame=f, t=round(t, 3), cam_center=[round(float(c[0]), 1), round(float(c[1]), 1)],
                            cam_width=round(float(w), 1), light_kv1=[round(float(p[0]), 1), round(float(p[1]), 1)],
                            light_size=round(float(size), 3), light_intensity=round(float(inten), 3)))
    return frames, log


def main():
    o_frames, o_log = build_opening()
    f3, prof3, log3 = P.build_s3()
    from p1_s1_clip import build_s1_clip
    f1, log1 = build_s1_clip()
    f2, log2 = P.build_s2(prof3)
    frames = o_frames + f1 + f2 + f3
    assert len(frames) == 326, len(frames)
    dur = len(frames) / FPS
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (OW, OH), '-r', str(FPS),
                           '-i', '-', '-t', '%.4f' % dur, '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16',
                           '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', OUT], stdin=subprocess.PIPE)
    for fr in frames:
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    json.dump(dict(song=[0.0, round(dur, 4)], frames=[0, 325],
                   cuts={'O2 (three)': 5.625, 'S1 (one)': 7.5, 'S2': 9.167, 'S3': 10.667},
                   music=dict(pad_in=PAD_IN, chimes=CHIMES, three=THREE, two=TWO, one=ONE, loading=13.061),
                   O1_O2=o_log, S1=log1), open(LOG, 'w'), indent=1)
    np.save(os.path.join(WORK, 'keyframes.npy'), np.stack([frames[i] for i in (0, 20, 50, 80, 100, 134, 135, 158, 179, 180)]))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
