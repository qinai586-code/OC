"""P1-S1 from the owner's Seedance take (v2): mask out the generated light, composite the designed light.

Used by p1_local.py (S1 = clip frames 52-91 -> song 7.500-9.167, 1:1). The take was generated from the
approved S1 frame *with* its light; the model left that light fixed at (907.3, 89.3) for all 121 frames.
  1. Mask out that light: one clean sky patch is built from the median of all frames (the camera and sky
     are still), the orb's measured glow is subtracted and its core inpainted; the patch replaces a disc
     around the orb in every frame, feathered at its edge.
  2. Composite the designed light: the approved orb's measured look (v8 profile), starting exactly where the
     approved light is and sinking ahead of her nod (it leads her head by 4 frames, following the measured
     nod curve), to end on her gaze above her hand at the cut into S2.
"""
import os
import sys

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
from p1s1_light import glow_profile  # noqa: E402
from seedance_check import read_frames, track_box  # noqa: E402

CLIP = os.path.join(R, 'seedance', 'returned', 'P1-S1_v5_take_v2.mp4')
V8 = os.path.join(R, 'seedance', 'refs_in2', 'P1_S1_original_reference_v8.png')
WORK = os.path.join(R, 'work', 'p1')
IN, N = 52, 40                                     # head turn starts at clip frame 61 (> 1 deg): IN = 61 - 9
ORB = (907.3, 89.3)                                # the take's fixed light (clip pixels), measured
START, END = (1205.0, 121.0), (1010.0, 425.0)      # designed light, approved-frame (1672x941) coordinates


def radial_add(img, c, rmax):
    """light added per radius by the orb, measured on the sky above it (median per ring)."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - c[0], yy - c[1])
    up = yy < c[1] - 2
    rr = np.arange(0, rmax + 1)
    prof = np.full((len(rr), 3), np.nan, np.float32)
    for i, r in enumerate(rr):
        sel = up & (np.abs(d - r) < 1.0)
        if sel.sum() > 3:
            prof[i] = np.median(img[sel], axis=0)
    first = int(np.argmax(~np.isnan(prof[:, 0])))
    prof[:first] = prof[first]
    for i in range(len(rr)):                        # rings that leave the top of frame: carry the last value
        if np.isnan(prof[i, 0]):
            prof[i] = prof[i - 1]
    base = np.median(prof[rmax - 15:], axis=0)
    add = np.clip(prof - base, 0, None)
    add = cv2.GaussianBlur(add.reshape(-1, 1, 3), (1, 7), 0).reshape(-1, 3)
    add *= np.clip((rmax - 5 - rr) / 25.0, 0, 1)[:, None]
    return rr.astype(np.float32), add, d


NOLIGHT = os.path.join(R, 'seedance', 'refs_in2', 'P1_S1_v8_nolight.png')


def clean_patch_from_reference(frames):
    """the light-free approved frame, aligned to the take (affine fit on frame 0) and matched in colour on the
    ring where the patch fades out; the take's orb sits too close to the top of frame to measure its glow."""
    H, W = frames[0].shape[:2]
    reg = np.load(os.path.join(WORK, 'v2_reg.npy'))
    ref = cv2.resize(cv2.imread(NOLIGHT), (W, H), interpolation=cv2.INTER_AREA)
    ref = cv2.warpAffine(ref, reg, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    med = np.median(np.stack([f.astype(np.float32) for f in frames[::4]]), axis=0)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - ORB[0], yy - ORB[1])
    ring = (d > 125) & (d < 160)
    ref += (med[ring].mean(axis=0) - ref[ring].mean(axis=0))[None, None]
    w = np.clip((155 - d) / 35.0, 0, 1)[..., None]  # replace inside r 120, fade out to r 155
    return ref, w


def clean_patch(frames):
    med = np.median(np.stack([f.astype(np.float32) for f in frames[::4]]), axis=0)
    rr, add, d = radial_add(med, ORB, 135)
    A = np.stack([np.interp(np.clip(d, 0, rr[-1]), rr, add[:, c]) for c in range(3)], -1)
    out = np.clip(med - A, 0, 255).astype(np.uint8)
    core = (d < 13).astype(np.uint8) * 255
    out = cv2.inpaint(out, core, 5, cv2.INPAINT_TELEA)
    o = out.astype(np.int16)
    rb = o[..., 2] - o[..., 0]
    far = (d > 150) & (d < 260)
    warm = ((d < 60) & (rb > np.percentile(rb[far], 99))).astype(np.uint8)
    warm = cv2.dilate(warm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    out = cv2.inpaint(out, warm * 255, 4, cv2.INPAINT_TELEA)
    w = np.clip((150 - d) / 30.0, 0, 1)[..., None]  # replace inside r 120, feather to r 150
    return out.astype(np.float32), w


def nod_curve(frames):
    """measured head rotation over the window (deg, chin down), monotone-smoothed (the take moves on threes)."""
    sx = frames[0].shape[1] / 1672.0
    t = track_box(frames, list(range(IN, IN + N + 8)), [340, 90, 640, 400], sx, sx)
    r = np.array([v[0] if v else np.nan for v in t])
    r = np.maximum.accumulate(np.nan_to_num(r))
    return r / max(r.max(), 1e-6)


def build_s1_clip():
    frames = read_frames(CLIP)
    H, W = frames[0].shape[:2]
    patch, w = clean_patch_from_reference(frames)
    prof = glow_profile()                            # approved orb look, radii in 1672-frame px
    reg = np.load(os.path.join(WORK, 'v2_reg.npy'))  # approved frame (at 1280x720) -> clip, affine
    s = W / 1672.0
    frac = nod_curve(frames)
    rr, add = prof
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    out, log = [], []
    for k in range(N):
        f = frames[IN + k].astype(np.float32)
        f = f * (1 - w) + patch * w                  # generated light masked out
        lead = frac[min(k + 4, len(frac) - 1)]       # the light leads her head by 4 frames
        u = 0.03 * min(k, 6) / 6.0 + 0.97 * lead     # already drifting before she moves
        p = np.array(START) * (1 - u) + np.array(END) * u
        p = p + np.array([-40.0, 25.0]) * np.sin(np.pi * u)   # a gentle curve, not a rail
        p[0] += 3.0 * np.sin(2 * np.pi * k / 29.0)
        q = reg @ np.array([p[0] * s, p[1] * (H / 941.0), 1.0])
        scale = (1.0 + 0.15 * u) * s
        inten = 1.0 + 0.06 * np.sin(2 * np.pi * k / 19.0 + 0.7)
        dd = np.clip(np.hypot(xx - q[0], yy - q[1]) / scale, 0, rr[-1])
        L = np.stack([np.interp(dd, rr, add[:, c]) for c in range(3)], -1) * inten
        out.append(np.clip(f + L, 0, 255).astype(np.uint8))
        log.append(dict(k=k, clip_frame=IN + k, light_clip_px=[round(float(q[0]), 1), round(float(q[1]), 1)],
                        nod_fraction=round(float(frac[min(k, len(frac) - 1)]), 3)))
    cv2.imwrite(os.path.join(WORK, 'v2_sky_patch_check.png'), np.hstack([frames[IN][0:240, 760:1060], out[0][0:240, 760:1060]]))
    return out, dict(source=os.path.basename(CLIP), clip_frames=[IN, IN + N - 1], light_start=START, light_end=END,
                     track=log[::6] + [log[-1]])
