"""Demo 0-43.25 s v8 (clarity round): lossless master first, then the review preview encoded from it.

  python3 rev3/tools/master_v8.py

Frames: v7's cached frames, except the 282 rebuilt this round (in $V8_OVERRIDES):
  62-86    opening landing, KV1 plates resampled with an antialiasing filter (opening_ink.AA)
  87-179   Seedance rear shot: better decode (yuv.hq_bgr) and one Lanczos warp (m26/build_opening_v3.py)
  180-255  S1-S2 rebuilt losslessly (no intermediate crf-16 file)
  686-730  D1 and 819-861 B3: better decode (m26/build_d1_v2.py, m26/build_b3_hq.py)
Master: RGB 4:4:4, lossless (libx264rgb qp 0), the locked music as FLAC (decoded once from the mp3, 0-43.25 s).
Preview: from the master; BT.601 limited range as in every earlier version (colours unchanged), but with accurate
rounding and Lanczos chroma filtering (v7's default conversion darkened every frame by ~0.9 levels), then
libx264 crf 10, preset slow, aq-mode 3, yuv420p (v7: crf 18, preset medium); AAC 192 kb/s as before."""
import hashlib, json, os, subprocess, sys
import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
BASE = os.environ.get('V7_CACHE', SP + '/v7/cache')
OVR = os.environ.get('V8_OVERRIDES', SP + '/v8/op')
MASTER = os.environ.get('V8_MASTER', SP + '/v8/DEMO_0-43_v8_master_lossless.mkv')
OUT = os.path.join(R, 'tests', 'DEMO_0-43_v8_720p.mp4')
STRIP = os.path.join(R, 'tests', 'DEMO_0-43_v8_strip.jpg')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
W, H, FPS, N = 1280, 720, 24, 1038
CONVERT = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:out_range=tv:out_color_matrix=bt601'
PREVIEW = ['-c:v', 'libx264', '-crf', '10', '-preset', 'slow', '-x264-params', 'aq-mode=3', '-pix_fmt', 'yuv420p']


def src(f):
    p = os.path.join(OVR, 'f%04d.png' % f)
    return p if os.path.exists(p) else os.path.join(BASE, 'f%04d.png' % f)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    over = sorted(int(n[1:5]) for n in os.listdir(OVR) if n.endswith('.png'))
    print('override frames:', len(over), 'runs:', [(a, b) for a, b in zip([over[0]] + [over[i] for i in range(1, len(over)) if over[i] != over[i - 1] + 1],
                                                                      [over[i - 1] for i in range(1, len(over)) if over[i] != over[i - 1] + 1] + [over[-1]])])
    # 1. lossless master
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                           '-t', '%.4f' % (N / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264rgb', '-qp', '0', '-preset', 'slow',
                           '-pix_fmt', 'bgr24', '-c:a', 'flac', MASTER], stdin=subprocess.PIPE)
    frames_sha = hashlib.sha256()
    for f in range(N):
        im = cv2.imread(src(f))
        assert im is not None and im.shape == (H, W, 3), f
        frames_sha.update(im.tobytes())
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    assert ff.wait() == 0
    # 2. the master decodes to exactly the frames
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', MASTER, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    n, bad = 0, []
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        if b != cv2.imread(src(n)).tobytes():
            bad.append(n)
        n += 1
    dec.wait()
    print('master: %d frames decoded, %d differ from the PNG frames' % (n, len(bad)))
    assert n == N and not bad
    # 3. preview from the master
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', MASTER, '-map', '0:v', '-map', '0:a', '-vf', CONVERT] + PREVIEW +
                          ['-c:a', 'aac', '-b:a', '192k', OUT])
    strip = []
    shots = json.load(open(os.path.join(R, 'tests', 'DEMO_0-43_v7_shots.json')))
    for sh in shots:
        f = (sh['frames'][0] + sh['frames'][1]) // 2
        th = cv2.resize(cv2.imread(src(f)), (320, 180), interpolation=cv2.INTER_AREA)
        cv2.putText(th, '%.2f' % (f / FPS), (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        strip.append(th)
    strip += [np.zeros_like(strip[0])] * (-len(strip) % 5)
    cv2.imwrite(STRIP, np.vstack([np.hstack(strip[i:i + 5]) for i in range(0, len(strip), 5)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    info = dict(master=MASTER, master_bytes=os.path.getsize(MASTER), master_sha256=sha(MASTER), frames_sha256=frames_sha.hexdigest(),
                preview=OUT, preview_bytes=os.path.getsize(OUT), preview_sha256=sha(OUT), overrides=len(over))
    json.dump(info, open(os.path.join(SP, 'v8', 'master_info.json'), 'w'), indent=1)
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
