"""Self-test for seedance_check.py on synthetic clips built from the approved S1 frame.

  python3 rev3/tools/seedance_check_selftest.py

It checks the light detector on the three P1 first frames (1672x941, 1280x720, 1920x1080). Then it
builds three 4 s, 1280x720, 24 fps clips (in rev3/work/selftest/, not committed):
  clean   the orb drifts down-left at a steady speed
  faulty  the same, with a stall (clip frames 24-36) and a second light (frames 40-42)
  head    the head region turns 9 deg chin-down between clip frames 20 and 40; the hand stays still
It runs the checker on the S1 pilot window and asserts what it should find. These are synthetic
tests of the measurement code only, not of any generated motion.
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
from seedance_check import lights  # noqa: E402

REFS = os.path.join(R, 'seedance', 'refs_in2')
WORK = os.path.join(R, 'work', 'selftest')
CHECK = os.path.join(R, 'tools', 'seedance_check.py')
S1 = os.path.join(REFS, 'P1_S1_original_reference_v8.png')
WINDOW = ['--in', '0.500', '--song', '7.500', '--dur', '1.667', '--light-box', '950,0,1672,260', '--min-move', '60',
          '--head', '340,90,640,400', '--hand', '760,650,940,770']


def encode(path, frames):
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1280x720', '-r', '24',
                           '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for fr in frames:
        ff.stdin.write(cv2.resize((np.clip(fr, 0, 1) * 255).astype(np.uint8), (1280, 720), interpolation=cv2.INTER_AREA).tobytes())
    ff.stdin.close()
    ff.wait()


def run(name, clip, extra=WINDOW):
    subprocess.run([sys.executable, CHECK, clip, '--name', name] + extra, check=True, capture_output=True)
    return json.load(open(os.path.join(R, 'seedance', 'checks', name, 'report.json')))


def main():
    os.makedirs(WORK, exist_ok=True)
    # 1. detector on the three first frames, at three sizes
    expect = {'P1_S1_original_reference_v8.png': [(1205, 121)], 'P1_S2_HAND_START_v2.png': [],
              'P1_S3_HOVER_START_v2.png': [(1029, 597)]}
    for name, pts in expect.items():
        im = cv2.imread(os.path.join(REFS, name))
        for size in (None, (1280, 720), (1920, 1080)):
            x = im if size is None else cv2.resize(im, size, interpolation=cv2.INTER_AREA if size[0] < 1672 else cv2.INTER_CUBIC)
            got = [(px * 1672 / x.shape[1], py * 941 / x.shape[0]) for a, px, py in lights(x)]
            assert len(got) == len(pts), (name, size, got)
            for (gx, gy), (ex, ey) in zip(got, pts):
                assert abs(gx - ex) < 4 and abs(gy - ey) < 4, (name, size, got)
    print('detector: S1 1 light, S2 none, S3 1 light, at 3 sizes: ok')

    im = cv2.imread(S1).astype(np.float32) / 255
    H, W = im.shape[:2]
    m = np.zeros((H, W), np.uint8)
    cv2.circle(m, (1205, 121), 75, 255, -1)
    bg = cv2.inpaint((im * 255).astype(np.uint8), m, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    def orb(cx, cy):                                          # white core, orange glow (BGR)
        d = np.hypot(xx - cx, yy - cy)
        glow = np.exp(-(np.maximum(d - 10, 0) / 14.0) ** 2)[..., None] * np.array([0.35, 0.65, 1.0], np.float32)
        return np.clip(glow + np.clip(11 - d, 0, 1)[..., None], 0, 1)

    screen = lambda a, b: 1 - (1 - a) * (1 - b)

    def orb_clip(stall=False, dup=False):
        pos, out = 0.0, []
        for f in range(96):
            if f > 0 and not (stall and 24 <= f <= 36):
                pos += 2.7
            fr = screen(bg, orb(1205 - 0.8 * pos, 121 + 0.6 * pos))
            if dup and 40 <= f <= 42:
                fr = screen(fr, orb(905, 371))
            out.append(fr)
        return out

    # 2. clean and faulty light paths
    encode(os.path.join(WORK, 'clean.mp4'), orb_clip())
    encode(os.path.join(WORK, 'faulty.mp4'), orb_clip(stall=True, dup=True))
    c = run('SELFTEST_clean', os.path.join(WORK, 'clean.mp4'))['window']
    assert c['clip_frames'] == [12, 51] and c['n_frames'] == 40, c
    assert not c['frames_not_exactly_one_light'] and not c['stalled_quarter_seconds'] and not c['frames_light_outside_box'], c
    assert c['meets_min_move'] and 95 < c['net_travel_px'] < 115, c
    f = run('SELFTEST_faulty', os.path.join(WORK, 'faulty.mp4'))['window']
    assert f['frames_not_exactly_one_light'] == [40, 41, 42], f
    assert f['stalled_quarter_seconds'] == [2, 3], f
    print('light window: clean passes (%.1f px); planted second light %s and stall %s flagged: ok'
          % (c['net_travel_px'], f['frames_not_exactly_one_light'], f['stalled_quarter_seconds']))

    # 3. head turn, hand still
    hm = np.zeros((H, W), np.float32)
    cv2.fillPoly(hm, [np.array([[330, 80], [650, 80], [650, 420], [560, 450], [330, 420]], np.int32)], 1.0)
    hm = cv2.GaussianBlur(hm, (0, 0), 6)
    frames = []
    for k in range(96):
        u = np.clip((k - 20) / 20.0, 0, 1)
        M = cv2.getRotationMatrix2D((595, 440), -9.0 * u * u * (3 - 2 * u), 1.0)   # clockwise = chin down
        mm = cv2.warpAffine(hm, M, (W, H))[..., None]
        frames.append(cv2.warpAffine(im, M, (W, H), borderMode=cv2.BORDER_REFLECT) * mm + im * (1 - mm))
    encode(os.path.join(WORK, 'head.mp4'), frames)
    h = run('SELFTEST_head', os.path.join(WORK, 'head.mp4'))['window']
    assert 7.5 < h['head']['rotation_deg_end'] < 10.0, h['head']
    assert h['hand']['shift_px_max'] < 2 and h['hand']['rotation_deg_max_abs'] < 0.5, h['hand']
    hw = run('SELFTEST_head_whole', os.path.join(WORK, 'head.mp4'),
             ['--in', '0', '--song', '7.0', '--dur', '4.0', '--head', '340,90,640,400'])['window']
    assert 22 <= hw['head']['first_output_frame_over_1deg'] <= 27, hw['head']
    print('head: planted 9.0 deg measured %.2f deg; whole-clip onset at clip frame %d (planted ~24); hand %.1f px: ok'
          % (h['head']['rotation_deg_end'], hw['head']['first_output_frame_over_1deg'], h['hand']['shift_px_max']))


if __name__ == '__main__':
    main()
