"""v9 full song (0-213.4 s, 5122 frames): render, lossless master, preview.

  python3 song_v9.py render S07 S09 ...   # each shot: bridge-render PNGs -> lossless segment (verified) -> PNGs deleted
  python3 song_v9.py master               # the master's parts (v9 0-43.25 master + S07..S47 segments): list, hashes
  python3 song_v9.py preview CRF          # the review mp4 encoded from the master
Frames 0-1037 are the v9 opening (DEMO_0-43_v9 master); 1038-5121 are the original project's shots S07-S47 rendered
through rev1_bridge.py (see its docstring for every change against rev1)."""
import hashlib, json, os, subprocess, sys, time
import cv2
import numpy as np

SP = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG, SEG = SP + '/v9/song_png', SP + '/v9/seg'
OPEN_MASTER = SP + '/v9/DEMO_0-43_v9_master_lossless.mkv'
MASTER_INFO = SP + '/v9/LOADING_v9_full_master_parts.json'
OUT = os.path.join(R, 'tests', 'LOADING_v9_full_720p.mp4')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
SHOTS = ['S07', 'S09', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'S21', 'S22', 'S23', 'S24',
         'S25', 'S26', 'S27', 'S28', 'S29', 'S30', 'S31', 'S32', 'S33', 'S34', 'S35', 'S36', 'S37', 'S38', 'S39', 'S40', 'S41',
         'S42', 'S43', 'S44', 'S45', 'S46', 'S47']
N = 5122
W, H = 1280, 720
CONVERT = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:out_range=tv:out_color_matrix=bt601'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def frames(name):
    import rev1_bridge
    return rev1_bridge.frames_of(name)


def render(names, jobs=4):
    os.makedirs(PNG, exist_ok=True)
    os.makedirs(SEG, exist_ok=True)
    for n in names:
        seg = os.path.join(SEG, n + '.mkv')
        fr = frames(n)
        if os.path.exists(seg):
            print(n, 'segment exists, skipped')
            continue
        t0 = time.time()
        subprocess.check_call([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rev1_bridge.py'), PNG, n,
                               '--jobs', str(jobs)], stdout=subprocess.DEVNULL)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H), '-r', '24', '-i', '-',
                               '-c:v', 'libx264rgb', '-qp', '0', '-preset', 'slow', '-pix_fmt', 'bgr24', seg], stdin=subprocess.PIPE)
        for f in fr:
            ff.stdin.write(cv2.imread(os.path.join(PNG, 'f%04d.png' % f)).tobytes())
        ff.stdin.close()
        assert ff.wait() == 0
        dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', seg, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
        bad, k = 0, 0
        for f in fr:
            b = dec.stdout.read(W * H * 3)
            if b != cv2.imread(os.path.join(PNG, 'f%04d.png' % f)).tobytes():
                bad += 1
            k += 1
        dec.wait()
        assert bad == 0, (n, bad)
        for f in fr:
            os.remove(os.path.join(PNG, 'f%04d.png' % f))
        print('%s: frames %d-%d (%d), %.0fs, lossless segment verified (%d MB)' % (n, fr[0], fr[-1], len(fr), time.time() - t0,
              os.path.getsize(seg) // 1000000), flush=True)


def _decode(path):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        yield b
    assert p.wait() == 0


def parts():
    """The master, as an ordered list of lossless parts: (path, first timeline frame, frame count)."""
    out, f0 = [(OPEN_MASTER, 0, 1038)], 1038
    for n in SHOTS:
        k = len(frames(n))
        out.append((os.path.join(SEG, n + '.mkv'), f0, k))
        f0 += k
    assert f0 == N, f0
    return out


def part_of(f):
    for path, f0, k in parts():
        if f0 <= f < f0 + k:
            return path, f - f0
    raise IndexError(f)


def master_frame(f):
    path, i = part_of(f)
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v', '-vf', 'select=eq(n\\,%d)' % i, '-vsync', '0',
                                   '-frames:v', '1', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'])
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def master_frames():
    """All 5122 master frames in order (raw BGR bytes), decoded from the parts."""
    for path, f0, k in parts():
        n = 0
        for b in _decode(path):
            if n >= k:
                break
            yield b
            n += 1
        assert n == k, (path, n, k)


def master():
    """The full-length lossless master is kept as its parts (no second 2 GB copy fits on this disk): the v9 0-43.25 master
    and one verified lossless segment per shot. This writes the ordered list with each part's sha256 and frame count,
    and a sha256 over all 5122 decoded frames (the master's content hash)."""
    h, n, info = hashlib.sha256(), 0, []
    for path, f0, k in parts():
        info.append(dict(path=path, first_frame=f0, frames=k, bytes=os.path.getsize(path), sha256=sha(path)))
    for b in master_frames():
        h.update(b)
        n += 1
    assert n == N
    out = dict(frames=n, frames_sha256=h.hexdigest(), audio=AUDIO, parts=info)
    json.dump(out, open(MASTER_INFO, 'w'), indent=1)
    print(json.dumps(dict(frames=n, frames_sha256=out['frames_sha256'], parts=len(info), bytes=sum(p['bytes'] for p in info)), indent=1))


def preview(crf):
    """The review mp4, encoded once from the master frames (RGB -> BT.601 limited, as every earlier version)."""
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H), '-r', '24', '-i', '-',
                           '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-vf', CONVERT, '-c:v', 'libx264', '-crf', str(crf), '-preset', 'slow',
                           '-x264-params', 'aq-mode=3', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', OUT], stdin=subprocess.PIPE)
    for b in master_frames():
        ff.stdin.write(b)
    ff.stdin.close()
    assert ff.wait() == 0
    print(OUT, os.path.getsize(OUT), sha(OUT))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'render':
        render(sys.argv[2:] if len(sys.argv) > 2 else SHOTS)
    elif cmd == 'master':
        master()
    elif cmd == 'preview':
        preview(sys.argv[2] if len(sys.argv) > 2 else '14')
