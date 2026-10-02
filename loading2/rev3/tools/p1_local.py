"""P1 light catch, built locally from the three approved stills (no generated video).

  python3 rev3/tools/p1_local.py   ->  rev3/tests/P1_local_720p.mp4 (+ rev3/tests/p1_local_log.json)

Song 7.500-13.583, 146 frames at 24 fps, 1280x720, one continuous encode over the locked music:
  S1  7.500- 9.167  frames 180-219  P1_S1_v8_nolight.png   light sinks; eyes lead, head dips 6 deg, holds
  S2  9.167-10.667  frames 220-255  P1_S2_HAND_START_v2    light enters from the top and slows above the
                                                          palm; the hand lifts gently; warm light on the hand
  S3 10.667-13.600  frames 256-325  P1_S3_HOVER_START_v2   light hovers, sinks into the palm on "Loading."
                                                          (vocal onset 13.05, measured); palm gives and recovers
Motion is limited animation: smooth warps of the approved drawings (head, hair, palm) and, in S2, a cut-out
arm whose uncovered background is copied from further along the Earth's limb. Nothing is redrawn. The light is composited with glow profiles measured from the
approved orbs (S1 from v8, S2/S3 from S3).
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
from p1s1_light import EYE, EYES, glow_profile, head_angle  # noqa: E402
from matte import isnet  # noqa: E402

REFS = os.path.join(R, 'seedance', 'refs_in2')
WORK = os.path.join(R, 'work', 'p1')
OUT = os.path.join(R, 'tests', 'P1_light_catch_720p.mp4')
LOG = os.path.join(R, 'tests', 'p1_local_log.json')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
OW, OH = 1280, 720
SONG0 = 7.500
N1, N2, N3 = 40, 36, 70                      # S1 180-219, S2 220-255, S3 256-325
K_TOUCH = 57                                 # S3 frame of the touch: song 13.042, on the "Loading." onset (13.05)
WARM = np.array([60.0, 150.0, 255.0])        # BGR, the orb's glow hue

# Movement amplitudes (owner, 2026-10-02: "increase the movement amplitude without changing the logic or
# timing"). Beats and frame timings are unchanged; only these sizes grew. Earlier values in brackets.
HEAD_DEG = 14.0       # S1 chin-down nod [6]. S3's head sits ~34 deg further down than S1's (eye-mouth line
                      # 37.8 -> 72 deg, measured); the rest of the way falls in the S2 insert
NOD_PIVOT = (400.0, 300.0)   # inside the head, behind its centroid (444, 257): it turns nearly in place (net forward ~9 px),
                             # the face drops, the chin tucks, and the back of the head rises only ~20 px (less pull on the hair)
IRIS = (2.5, 5.0)     # S1 iris shift x, y in px [1.5, 3.0]
S1_LIGHT_END = (895.0, 240.0)   # on her gaze line after the nod (~13 deg above her eye) [887, 176]
ARM_DEG, WRIST_DEG = 2.0, 5.0   # S2 lift [1.2, 3.0]
DIP_PX, BOB_PX = 7.0, 4.0       # S3 palm give and hover bob [4.5, 2.5]
SWAY_PX, BREATH_PX = 3.5, 1.4   # S3 hair sway and breathing [2.5, 0.9]


# ---------------------------------------------------------------- helpers
def ease(a, b, k):
    u = np.clip((k - a) / float(b - a), 0, 1)
    return u * u * (3 - 2 * u)


def poly_mask(shape, pts, sigma):
    m = np.zeros(shape[:2], np.float32)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0)
    return cv2.GaussianBlur(m, (0, 0), sigma) if sigma else m


def gauss(shape, cx, cy, s):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    return np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * s * s))


def rot_disp(xx, yy, piv, deg):
    """forward displacement of a rotation by deg (cv2 sense: + = counter-clockwise on screen)."""
    a = np.radians(-deg)                       # image y points down
    x, y = xx - piv[0], yy - piv[1]
    return x * np.cos(a) - y * np.sin(a) - x, x * np.sin(a) + y * np.cos(a) - y


def warp(img, dx, dy, border=cv2.BORDER_REFLECT):
    """apply a small forward displacement field (inverse-mapped with the same field)."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return cv2.remap(img, (xx - dx).astype(np.float32), (yy - dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=border)


def radial_profile(img, c, rmax=180, rmin_base=160):
    """added light per radius, measured on the side of an orb that faces open sky (above it)."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - c[0], yy - c[1])
    up = yy < c[1] - 3
    rr = np.arange(0, rmax + 1)
    prof = np.full((len(rr), 3), np.nan, np.float32)
    for i, r in enumerate(rr):
        sel = up & (np.abs(d - r) < 1.0)
        if sel.sum() > 3:
            prof[i] = np.median(img[sel], axis=0)
    first = int(np.argmax(~np.isnan(prof[:, 0])))
    prof[:first] = prof[first]
    base = np.nanmedian(prof[rmin_base:rmax + 1], axis=0)
    add = np.nan_to_num(np.clip(prof - base, 0, None))
    add = cv2.GaussianBlur(add.reshape(-1, 1, 3), (1, 7), 0).reshape(-1, 3)
    add *= np.clip((rmax - 10 - rr) / 30.0, 0, 1)[:, None]
    return rr.astype(np.float32), add


def light(shape, x, y, scale, inten, prof):
    H, W = shape[:2]
    rr, add = prof
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.clip(np.hypot(xx - x, yy - y) / scale, 0, rr[-1])
    return np.stack([np.interp(d, rr, add[:, c]) for c in range(3)], -1) * inten


def matte(name, img):
    p = os.path.join(WORK, '%s_isnet.npy' % name)
    if os.path.exists(p):
        return np.load(p)
    m = isnet(img[:, :, ::-1] / 255.0).astype(np.float32)
    np.save(p, m)
    return m


def solid(m, close=9, thr=0.5):
    """binary matte with holes filled (fingertip holes in S2)."""
    b = (m > thr).astype(np.uint8)
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    ff = b.copy()
    h, w = b.shape
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for seed in ((0, 0), (w - 1, 0)):
        if ff[seed[1], seed[0]] == 0:
            cv2.floodFill(ff, mask, seed, 2)
    return ((b == 1) | (ff == 0)).astype(np.float32)


def remove_orb(img, c, prof, sky):
    """subtract the orb's measured glow, then inpaint its saturated core (sky pixels only)."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - c[0], yy - c[1])
    out = np.clip(img - light(img.shape, c[0], c[1], 1.0, 1.0, prof), 0, 255).astype(np.uint8)
    core = ((d < 24) & (sky > 0.5)).astype(np.uint8) * 255
    return cv2.inpaint(out, core, 6, cv2.INPAINT_TELEA).astype(np.float32)


def to_out(fr):
    return cv2.resize(np.clip(fr, 0, 255).astype(np.uint8), (OW, OH), interpolation=cv2.INTER_AREA)


# ---------------------------------------------------------------- S1
def s1_light_path(k):
    """same beats as p1s1_light.path (start on her eyeline, slight acceleration, float sway, +10% size),
    with the end moved to her gaze after the larger dip."""
    t = k / 39.0
    u = 0.88 * t + 0.12 * t * t
    p0, p2 = np.array([905.0, 50.0]), np.array(S1_LIGHT_END)
    p1 = (p0 + p2) / 2 + np.array([14.0, 0.0])
    p = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u * u * p2
    p[0] += 3.5 * np.sin(2 * np.pi * k / 29.0)
    return float(p[0]), float(p[1]), 1.0 + 0.12 * u, 1.0 + 0.06 * np.sin(2 * np.pi * k / 19.0 + 0.7)


def build_s1():
    img = cv2.imread(os.path.join(REFS, 'P1_S1_v8_nolight.png')).astype(np.float32)
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    prof = glow_profile()
    m = np.clip(matte('S1', img), 0, 1)
    # static sky plate: she is a layer warped over it, so the clouds never bend with her head
    pp = os.path.join(WORK, 'S1_sky_plate.png')
    if not os.path.exists(pp):
        reg = cv2.dilate((m > 0.05).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
        cv2.imwrite(pp, cv2.inpaint(img.astype(np.uint8), reg * 255, 9, cv2.INPAINT_TELEA))
    plate_s1 = cv2.imread(pp).astype(np.float32)
    piv = NOD_PIVOT
    # head outline with its lower edge on the drawn jaw: chin tip (595, 382) -> throat corner (540, 410) -> ear
    # (below the chin it takes in the sky in front of the throat, so the jaw's outline leaves nothing behind;
    # the neck itself, left of the throat line, stays outside)
    P_head = poly_mask(img.shape, [(280, 85), (480, 75), (565, 150), (650, 250), (655, 330), (648, 392), (612, 430),
                                   (550, 432), (540, 412), (470, 404), (430, 396), (330, 398), (255, 300), (245, 175)], 0)
    w_rigid = cv2.GaussianBlur(P_head, (0, 0), 2)
    # hair hanging from the head follows with a long, smooth falloff (no shear, no waves)
    d_out = cv2.distanceTransform((P_head < 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    body = poly_mask(img.shape, [(285, 495), (660, 495), (660, 941), (285, 941)], 0)
    body = np.maximum(body, poly_mask(img.shape, [(100, 640), (420, 640), (420, 941), (100, 941)], 0))
    keep = 1 - cv2.GaussianBlur(body, (0, 0), 6)
    back = poly_mask(img.shape, [(150, 200), (470, 380), (470, 480), (300, 520), (120, 860), (0, 860), (0, 300)], 25)
    w_back = np.exp(-d_out / 110.0) * back * keep
    strands = poly_mask(img.shape, [(430, 395), (610, 380), (615, 490), (430, 490)], 12)
    w_str = 0.8 * np.exp(-d_out / 55.0) * strands * keep * (1 - back)
    w_rest = np.maximum(w_rigid, np.maximum(w_back, w_str))
    hand_keep = 1 - poly_mask(img.shape, [(700, 620), (980, 620), (980, 800), (700, 800)], 10)
    tips = np.clip((yy - 450) / 400.0, 0, 1) * (xx < 160) * (yy < 860) * np.clip(m * 1.5, 0, 1)
    tips = cv2.GaussianBlur(tips, (0, 0), 6)
    # the face, chin and jaw are a rigid layer drawn over the still neck, so the chin tucks in front of the
    # throat instead of squashing it; the back of the head stays in the smooth warp (soft hand-over at x 450-490)
    A_front = P_head * np.clip(m, 0, 1) * np.clip((xx - 450) / 40.0, 0, 1)
    A_front = cv2.GaussianBlur(A_front, (0, 0), 1.0)
    amp = HEAD_DEG / 6.0                                    # p1s1_light.head_angle peaks at 6 deg
    ha = lambda k: amp * head_angle(k)
    premult = img * m[..., None]
    frames = []
    for k in range(N1):
        th = ha(k)                                          # + = chin down = clockwise on screen
        dx, dy = rot_disp(xx, yy, piv, -th)
        lx, ly = rot_disp(xx, yy, piv, -ha(k - 3))          # the hair lags the head by 3 frames
        t = k / 24.0
        sway = 2.0 * (np.sin(2 * np.pi * t / 1.7 - yy / 110.0) - np.sin(-yy / 110.0))   # zero at frame 0
        lag = np.clip(1 - np.exp(-d_out / 60.0), 0, 1)      # near the scalp no lag, further down more
        hx, hy = dx * (1 - lag) + lx * lag, dy * (1 - lag) + ly * lag
        DX = (w_rigid * dx + (w_rest - w_rigid) * hx + tips * sway) * hand_keep
        DY = (w_rigid * dy + (w_rest - w_rigid) * hy + tips * 0.4 * sway) * hand_keep
        e = ease(*EYES, k) + 0.15 * ease(29, 39, k)         # iris lowers first (eyes lead)
        ex, ey = EYE[0] + dx[int(EYE[1]), int(EYE[0])], EYE[1] + dy[int(EYE[1]), int(EYE[0])]
        g = gauss(img.shape, ex, ey, 7.5)
        IX, IY = IRIS[0] * e * g, IRIS[1] * e * g
        rest = warp(premult, DX + IX, DY + IY)
        a_rest = warp(m, DX + IX, DY + IY)
        comp = plate_s1 * (1 - a_rest[..., None]) + rest
        head = warp(premult, dx + IX, dy + IY)              # rigid rotation of the whole image
        a_head = warp(A_front, dx + IX, dy + IY)[..., None]
        a_full = warp(m, dx + IX, dy + IY)[..., None]
        head_rgb = head / np.maximum(a_full, 1e-3)
        comp = head_rgb * a_head + comp * (1 - a_head)
        moved = np.clip(np.maximum(np.hypot(DX, DY), np.hypot(dx, dy) * cv2.dilate(A_front, np.ones((61, 61), np.uint8))) / 0.5, 0, 1)
        moved = cv2.GaussianBlur(cv2.dilate(moved, np.ones((9, 9), np.uint8)), (0, 0), 3)[..., None]
        fr = comp * moved + img * (1 - moved)               # untouched pixels stay exactly the approved still
        x, y, sc, it = s1_light_path(k)
        fr = fr + light(fr.shape, x, y, sc, it, prof)
        frames.append(to_out(fr))
    return frames, dict(head_deg_end=round(float(ha(N1 - 1)), 2), light_start=s1_light_path(0)[:2],
                        light_end=s1_light_path(N1 - 1)[:2])


# ---------------------------------------------------------------- S2
def limb_fill(img, region):
    """fill a region with background copied from further along the Earth's limb (fit measured on clean
    columns of S2, residual p95 3.8 px), so the limb line and the sky/Earth texture continue behind the hand."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    c = np.load(os.path.join(WORK, 'S2_limb_fit.npy'))
    dx = np.where(xx > 590, 480.0, 700.0)            # the copy source must lie right of the fingertips (x > 1060)
    my = yy + (np.polyval(c, xx + dx) - np.polyval(c, xx))
    fill = cv2.remap(img, (xx + dx).astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    fs = np.clip(cv2.GaussianBlur(region.astype(np.float32), (0, 0), 3) * 1.5, 0, 1)
    return img * (1 - fs[..., None]) + fill * fs[..., None]


def build_s2(prof3):
    img = cv2.imread(os.path.join(REFS, 'P1_S2_HAND_START_v2.png')).astype(np.float32)
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # the model reads the dark coat as half-transparent, so take a low threshold and close it: the sleeve's
    # lit top edge must move as one piece with the sleeve
    m2 = matte('S2', img)
    a_s = solid(m2, close=15, thr=0.25)
    # the sleeve and cuff run off the bottom of frame, but the model fades out on the lower coat (values
    # 0.1-0.2): fill every column from the sleeve's top edge to the bottom, up to the cuff's right edge
    # right boundary = the cuff lining's outer edge, measured row by row (x = 704 - 0.0144 y, residual p90 5 px)
    xr = (704.0 - 0.0144 * np.arange(H) + 2).astype(int)
    for x in range(int(xr.max()) + 1):
        ys = np.nonzero(m2[400:, x] > 0.25)[0]
        if len(ys):
            y0 = 400 + ys[0]
            a_s[y0:, x] = np.maximum(a_s[y0:, x], (x <= xr[y0:]).astype(np.float32))
    a_s = cv2.morphologyEx(a_s, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    a = cv2.GaussianBlur(a_s, (0, 0), 1.2)
    piv_arm, piv_wrist = (-400.0, 1250.0), (640.0, 690.0)
    w_hand = np.clip((xx - 600) / 160.0, 0, 1)
    # vacated = covered now but not at the top of the lift; filled from further along the limb
    ax, ay = rot_disp(xx, yy, piv_arm, 1.07 * ARM_DEG)
    wx, wy = rot_disp(xx, yy, piv_wrist, WRIST_DEG)
    lifted = warp(a_s, ax + w_hand * wx, ay + w_hand * wy, cv2.BORDER_REPLICATE)
    vacated = cv2.dilate(((a_s > 0.5) & (lifted < 0.5)).astype(np.uint8),
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0
    bg = limb_fill(img, vacated)
    cv2.imwrite(os.path.join(WORK, 'S2_plate_check.png'), bg.astype(np.uint8))
    vy, vx = np.nonzero(vacated)
    cup0 = np.array([950.0, 600.0])
    entry, ctrl = np.array([1110.0, -70.0]), np.array([1080.0, 250.0])
    frames, light_xy = [], []
    for k in range(N2):
        lift = ARM_DEG * ease(5, 30, k) + 0.065 * ARM_DEG * np.sin(np.pi * np.clip((k - 26) / 10.0, 0, 1))
        wrist = WRIST_DEG * ease(8, 31, k)
        ax, ay = rot_disp(xx, yy, piv_arm, lift)
        wx, wy = rot_disp(xx, yy, piv_wrist, wrist)
        DX, DY = ax + w_hand * wx, ay + w_hand * wy
        arm = warp(img * a[..., None], DX, DY, cv2.BORDER_REPLICATE)
        aw = warp(a, DX, DY, cv2.BORDER_REPLICATE)
        cx, cy = cup0
        p1 = cup0 + np.array(rot_disp(np.float32(cx), np.float32(cy), piv_wrist, wrist))
        p2 = p1 + np.array(rot_disp(np.float32(p1[0]), np.float32(p1[1]), piv_arm, lift))
        target = p2 + np.array([-5.0, -135.0])
        u = 1 - (1 - np.clip(k / 28.0, 0, 1)) ** 2.2            # quick entry, slows to a hover
        pos = (1 - u) ** 2 * entry + 2 * (1 - u) * u * ctrl + u * u * target
        pos = pos + np.array([0.0, 2.0 * np.sin(2 * np.pi * k / 20.0) * ease(26, 34, k)])
        sc = 1.25 + 0.4 * u
        L = light(img.shape, pos[0], pos[1], sc, 1.0, prof3)
        near = 0.55 * np.exp(-np.hypot(*(pos - p2)) / 380.0)
        warm = aw[..., None] * gauss(img.shape, pos[0], pos[1] + 120, 230)[..., None] * near * WARM[None, None] * 0.55
        fr = bg * (1 - aw[..., None]) + arm + warm * (1 - arm / 300.0) + L
        frames.append(to_out(fr))
        light_xy.append([round(float(pos[0]), 1), round(float(pos[1]), 1)])
    tip = np.array([1045.0, 560.0])
    t1 = tip + np.array(rot_disp(np.float32(tip[0]), np.float32(tip[1]), piv_wrist, WRIST_DEG))
    t2 = t1 + np.array(rot_disp(np.float32(t1[0]), np.float32(t1[1]), piv_arm, ARM_DEG))
    return frames, dict(fingertip_rise_px=round(float(tip[1] - t2[1]), 1), vacated_px=int(vacated.sum()),
                        vacated_x=[int(vx.min()), int(vx.max())], light_path=light_xy[::7] + [light_xy[-1]])


# ---------------------------------------------------------------- S3
def build_s3():
    src = cv2.imread(os.path.join(REFS, 'P1_S3_HOVER_START_v2.png')).astype(np.float32)
    H, W = src.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    orb = (1029.0, 597.0)
    prof3 = radial_profile(src, orb)
    m = matte('S3', src)
    img = remove_orb(src, orb, prof3, 1 - m)
    hand_box = poly_mask(src.shape, [(880, 540), (1190, 540), (1190, 780), (880, 780)], 0)
    hb = (solid(m) * hand_box).astype(np.uint8)
    # palm dip as a smooth warp: the hand and the smooth sky just above it move; the Earth below is covered,
    # not uncovered, so no fill is needed
    up = cv2.dilate(hb, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    w_dip = cv2.GaussianBlur(np.maximum(hb, up * (yy < 700)).astype(np.float32), (0, 0), 6) * np.clip((xx - 900) / 90.0, 0, 1)
    hair = poly_mask(src.shape, [(0, 380), (330, 330), (420, 560), (300, 941), (0, 941)], 25) * np.clip(m * 1.4, 0, 1)
    hair *= np.clip((yy - 380) / 450.0, 0, 1)
    torso = poly_mask(src.shape, [(150, 640), (860, 640), (860, 941), (150, 941)], 30) * (1 - w_dip)
    face = gauss(src.shape, 690, 430, 110) * np.clip(m, 0, 1)
    palm = gauss(src.shape, 1050, 650, 70) * cv2.GaussianBlur(hb.astype(np.float32), (0, 0), 2)
    rest = np.array([1040.0, 634.0])
    frames, log = [], []
    for k in range(N3):
        t = k / 24.0
        bob = np.array([0.0, BOB_PX * np.sin(2 * np.pi * k / 22.0)]) * (1 - ease(24, 34, k))
        u = ease(30, K_TOUCH, k)
        pos = np.array(orb) * (1 - u) + rest * u + bob
        dip = DIP_PX * (np.exp(-((k - K_TOUCH - 2.5) / 2.6) ** 2) - 0.27 * np.exp(-((k - K_TOUCH - 8) / 3.0) ** 2)) if k >= K_TOUCH else 0.0
        breath = BREATH_PX * np.sin(2 * np.pi * t / 2.8)
        sway = SWAY_PX * (np.sin(2 * np.pi * t / 1.9 - yy / 120.0) - np.sin(-yy / 120.0))   # zero at frame 0
        fr = warp(img, hair * sway, torso * breath + w_dip * dip)
        if k >= K_TOUCH:
            pos = pos + np.array([0.0, dip])
        flare = 1.0 + 0.45 * np.exp(-((k - K_TOUCH - 1.5) / 2.2) ** 2) + 0.22 * ease(K_TOUCH, K_TOUCH + 6, k)
        pulse = 1.0 + 0.04 * np.sin(2 * np.pi * k / 18.0)
        L = light(src.shape, pos[0], pos[1], 1.0, flare * pulse, prof3)
        glow_on = 0.25 * u + 0.35 * ease(K_TOUCH - 2, K_TOUCH + 4, k)
        add = (palm * glow_on * 0.8 + face * 0.10 * ease(K_TOUCH - 2, K_TOUCH + 8, k))[..., None] * WARM[None, None] * 0.6
        fr = fr + add * (1 - fr / 320.0) + L
        frames.append(to_out(fr))
        if k % 6 == 0 or k == N3 - 1:
            log.append(dict(k=k, song=round(10.667 + k / 24.0, 3), light=[round(float(pos[0]), 1), round(float(pos[1]), 1)],
                            dip_px=round(float(dip), 2), flare=round(float(flare), 3)))
    return frames, prof3, dict(touch_frame=K_TOUCH, touch_song=round(10.667 + K_TOUCH / 24.0, 3), track=log)


def main():
    os.makedirs(WORK, exist_ok=True)
    f3, prof3, log3 = build_s3()
    if os.environ.get('P1_S1_SOURCE', 'take') == 'take':   # owner's Seedance take (v2), light masked and redone
        from p1_s1_clip import build_s1_clip
        f1, log1 = build_s1_clip()
    else:                                                  # fully local fallback (2D nod)
        f1, log1 = build_s1()
    f2, log2 = build_s2(prof3)
    frames = f1 + f2 + f3
    assert len(frames) == N1 + N2 + N3 == 146
    dur = len(frames) / 24.0
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (OW, OH), '-r', '24',
                           '-i', '-', '-ss', '%.4f' % SONG0, '-t', '%.4f' % dur, '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                           '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
                           OUT], stdin=subprocess.PIPE)
    for fr in frames:
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    json.dump(dict(song=[SONG0, round(SONG0 + dur, 4)], frames=[180, 325], cuts=dict(S2=9.167, S3=10.667),
                   S1=log1, S2=log2, S3=log3), open(LOG, 'w'), indent=1)
    np.save(os.path.join(WORK, 'frames_first.npy'), np.stack([frames[0], frames[N1], frames[N1 + N2]]))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
