"""P1-S1 light, done locally, plus the v4 timing animatic.

The light in S1 is not generated. Its look is measured from the owner-approved S1 frame (the
radial glow of the orb, so it matches S1 and S3), and its path and timing are designed here.
Generated S1 footage carries only the character's performance; the light is composited on it.

  python3 rev3/tools/p1s1_light.py animatic   ->  rev3/seedance/pilot_S1/P1-S1_v4_timing_animatic.mp4

Window frame k = 0..39 is song 7.500 + k/24 (song frames 180..219). Coordinates are in the
1672x941 first frame.
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(R, 'seedance', 'refs_in2')
V8 = os.path.join(REFS, 'P1_S1_original_reference_v8.png')
NOLIGHT = os.path.join(REFS, 'P1_S1_v8_nolight.png')
S2 = os.path.join(REFS, 'P1_S2_HAND_START_v2.png')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
OUT = os.path.join(R, 'seedance', 'pilot_S1', 'P1-S1_v4_timing_animatic.mp4')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ORB_V8 = (1205.0, 121.0)
EYE = (518.0, 297.0)                 # her eye (iris) in the approved frame
SONG0, N = 7.500, 40

# ---- action timing (window frames) --------------------------------------------------------
EYES = (6, 10)                       # eyes lower first
HEAD = (9, 24, 6.0)                  # head dips 6 deg chin-down (pitch only), ease in/out
SETTLE = (24, 29, 0.4)               # small overshoot that settles
# k >= 29: hold, watching; the light keeps moving; cut to S2 at k = 40 (song 9.167)


def glow_profile():
    """Radial glow (BGR, added light per radius) measured on the clean sky above the approved orb."""
    im = cv2.imread(V8).astype(np.float32)
    H, W = im.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - ORB_V8[0], yy - ORB_V8[1])
    up = yy < ORB_V8[1] - 3
    rr = np.arange(0, 181)
    prof = np.full((len(rr), 3), np.nan, np.float32)
    for i, r in enumerate(rr):
        sel = up & (np.abs(d - r) < 1.0)
        if sel.sum() > 3:
            prof[i] = np.median(im[sel], axis=0)
    first = int(np.argmax(~np.isnan(prof[:, 0])))           # radii too small to sample: the saturated core
    prof[:first] = prof[first]
    base = np.nanmedian(prof[160:181], axis=0)
    add = np.nan_to_num(np.clip(prof - base, 0, None))
    add = cv2.GaussianBlur(add.reshape(-1, 1, 3), (1, 7), 0).reshape(-1, 3)
    add *= np.clip((170 - rr) / 30.0, 0, 1)[:, None]
    return rr.astype(np.float32), add


def path(k):
    """Designed light position, size and brightness at window frame k (may be < 0 or >= 40).
    Starts on her drawn eyeline (~32 deg above her eye) and sinks toward her open hand, slightly
    accelerating, with a slow float sway: alive, not a moon on a rail."""
    t = k / 39.0
    u = 0.88 * t + 0.12 * t * t
    p0, p1, p2 = np.array([905.0, 50.0]), np.array([918.0, 112.0]), np.array([884.0, 176.0])
    p = (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u * u * p2
    p[0] += 3.5 * np.sin(2 * np.pi * k / 29.0)
    scale = 1.0 + 0.10 * u
    inten = 1.0 + 0.06 * np.sin(2 * np.pi * k / 19.0 + 0.7)
    return float(p[0]), float(p[1]), scale, inten


def light_layer(shape, x, y, scale, inten, prof, sx=1.0, sy=1.0):
    """Added light (float BGR) for a frame of the given shape; x, y in 1672x941 coordinates."""
    H, W = shape[:2]
    rr, add = prof
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    s = (sx + sy) / 2.0
    d = np.hypot(xx - x * sx, yy - y * sy) / (scale * s)
    return np.stack([np.interp(np.clip(d, 0, 180), rr, add[:, c]) for c in range(3)], -1) * inten


def ease(a, b, k):
    u = np.clip((k - a) / float(b - a), 0, 1)
    return u * u * (3 - 2 * u)


def head_angle(k):
    a0, a1, amp = HEAD
    s0, s1, over = SETTLE
    ang = amp * ease(a0, a1, k)
    ang += over * np.sin(np.pi * np.clip((k - s0) / float(s1 - s0), 0, 1))
    return ang


def placeholder_performance(img, k, mask):
    """CRUDE 2D placeholder for the timing animatic only: an iris nudge and a rigid head rotation.
    It shows WHEN things happen, not how the generated performance should look."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    e = ease(*EYES, k) + 0.15 * ease(29, 39, k)
    g = np.exp(-((xx - EYE[0]) ** 2 + (yy - EYE[1]) ** 2) / (2 * 7.0 ** 2))
    mx, my = (xx - 1.5 * e * g).astype(np.float32), (yy - 3.0 * e * g).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    M = cv2.getRotationMatrix2D((530, 430), -head_angle(k), 1.0)       # negative = clockwise = chin down
    rot = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mm = cv2.warpAffine(mask, M, (W, H))[..., None]
    return rot * mm + img * (1 - mm)


def head_mask(shape):
    m = np.zeros(shape[:2], np.float32)
    # head plus the smooth sky around the horns, so a rotated horn never leaves its old copy behind
    poly = np.array([[180, 0], [720, 0], [720, 410], [600, 470], [420, 475], [290, 445], [200, 300]], np.int32)
    cv2.fillPoly(m, [poly], 1.0)
    return cv2.GaussianBlur(m, (0, 0), 14)


def label(frame, lines, color=(235, 235, 240)):
    im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(im)
    for i, (txt, size) in enumerate(lines):
        y = 18 + sum(s + 12 for _, s in lines[:i])
        d.text((24, y), txt, font=ImageFont.truetype(FONT, size), fill=color, stroke_width=2, stroke_fill=(10, 10, 16))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def beat(k):
    if k < EYES[0]:
        return 'light already moving; she holds'
    if k < HEAD[0]:
        return 'eyes lower first'
    if k < HEAD[1]:
        return 'head dips (pitch only, ~6 deg)'
    if k < SETTLE[1]:
        return 'settles'
    return 'holds, watching; the light keeps sinking'


def animatic():
    prof = glow_profile()
    base = cv2.imread(NOLIGHT).astype(np.float32)
    mask = head_mask(base.shape)
    s2 = cv2.resize(cv2.imread(S2), (1920, 1080), interpolation=cv2.INTER_CUBIC)
    n_s2 = 12
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1920x1080', '-r', '24',
                           '-i', '-', '-ss', '%.4f' % SONG0, '-t', '%.4f' % ((N + n_s2) / 24.0), '-i', AUDIO,
                           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], stdin=subprocess.PIPE)
    log = []
    for k in range(N):
        x, y, sc, it = path(k)
        fr = placeholder_performance(base, k, mask)
        fr = np.clip(fr + light_layer(fr.shape, x, y, sc, it, prof), 0, 255).astype(np.uint8)
        fr = cv2.resize(fr, (1920, 1080), interpolation=cv2.INTER_CUBIC)
        t = SONG0 + k / 24.0
        fr = label(fr, [('S1 TIMING ANIMATIC  |  light = proposed final design  |  head/eyes = crude 2D placeholder', 22),
                        ('song %.3f   window frame %d/39   %s' % (t, k, beat(k)), 22)])
        ff.stdin.write(fr.tobytes())
        log.append((k, round(t, 3), round(x, 1), round(y, 1), round(float(np.degrees(np.arctan2(EYE[1] - y, x - EYE[0]))), 1),
                    round(float(head_angle(k)), 2)))
    for j in range(n_s2):
        t = SONG0 + (N + j) / 24.0
        ff.stdin.write(label(s2.copy(), [('CUT to S2 first frame (still, not animated)  |  the light enters from the top, slightly right of the palm', 22),
                                         ('song %.3f' % t, 22)]).tobytes())
    ff.stdin.close()
    ff.wait()
    print('k  song  light_x light_y elevation_from_eye_deg head_deg')
    for row in log[::3] + [log[-1]]:
        print(*row)
    print('wrote', OUT)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'animatic':
        animatic()
    else:
        print(__doc__)
