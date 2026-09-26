"""Render CLI.

  python3 src/render.py sheet 2.1,3.4,5 [--cols 4] [--out qa/sheet.png]      contact sheet (1/4-res composed frames)
  python3 src/render.py strip 9.5:12.5 [--every 3] [--cols 8] [--out ...]    every Nth frame in a span (motion check)
  python3 src/render.py stills 2.1,3.4 [--out qa/stills]                     full-res 1080p PNGs
  python3 src/render.py shots [--out qa/contact]                             one contact sheet per shot (start/mid/end)
  python3 src/render.py frames [--range a:b] [--shots 01,02] [--workers 4]   native frames -> cache/native (parallel)
  python3 src/render.py encode [--out out/final.mp4] [--range a:b]           cached frames -> H.264 1080p60 + audio
  python3 src/render.py preview a:b [--out out/preview.mp4]                  quick 540p mp4 with audio (motion QA)
"""
import sys, os, json, argparse, subprocess, math, time
from multiprocessing import Pool
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import numpy as np
from PIL import Image
import song
from engine.post import compose, OW, OH
from engine.film import FPS

AUDIO = os.path.join(ROOT, 'audio', 'pdoom.mp3')
CACHE = os.path.join(ROOT, 'cache', 'native')
NFRAMES = int(round(song.DURATION * FPS))
FFMPEG = os.environ.get('FFMPEG', 'ffmpeg')


def film():
    from film_def import FILM
    return FILM


def comp(t, F=None):
    F = F or film()
    img, post = F.frame(t)
    return compose(img, post, t, song.LYRICS)


def parse_times(s):
    return [float(x) for x in s.split(',') if x]


def grid(images, cols, pad=6, bg=(16, 16, 22), labels=None):
    h, w = images[0].shape[:2]
    rows = math.ceil(len(images) / cols)
    out = np.full((rows * (h + pad + 14) + pad, cols * (w + pad) + pad, 3), bg, np.uint8)
    from engine.px import Canvas
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        y, x = pad + r * (h + pad + 14), pad + c * (w + pad)
        out[y:y + h, x:x + w] = im
    img = Image.fromarray(out)
    if labels:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        for i, lb in enumerate(labels):
            r, c = divmod(i, cols)
            d.text((pad + c * (w + pad) + 2, pad + r * (h + pad + 14) + h + 1), lb, fill=(200, 200, 210))
    return img


def small(im, k=4):
    return im[::k, ::k]


def cmd_sheet(a):
    F = film()
    ts = parse_times(a.times)
    ims = [small(comp(t, F), a.k) for t in ts]
    labs = [f"{t:.2f} {F.shot_at(t)[1].name}" for t in ts]
    out = a.out or os.path.join(ROOT, 'qa', 'sheet.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    grid(ims, a.cols, labels=labs).save(out)
    print(out)


def cmd_strip(a):
    F = film()
    t0, t1 = [float(x) for x in a.times.split(':')]
    i0, i1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    idx = list(range(i0, i1, a.every))
    ims = [small(comp(i / FPS, F), a.k) for i in idx]
    out = a.out or os.path.join(ROOT, 'qa', 'strip.png')
    grid(ims, a.cols, labels=[f"{i / FPS:.3f}" for i in idx]).save(out)
    print(out)


def cmd_stills(a):
    F = film()
    out = a.out or os.path.join(ROOT, 'qa', 'stills')
    os.makedirs(out, exist_ok=True)
    for t in parse_times(a.times):
        Image.fromarray(comp(t, F)).save(os.path.join(out, f"t{t:07.3f}.png"))
    print(out)


def cmd_shots(a):
    F = film()
    out = a.out or os.path.join(ROOT, 'qa', 'contact')
    os.makedirs(out, exist_ok=True)
    sel = set(a.only.split(',')) if a.only else None
    for s in F.shots:
        if sel and s.name.split('_')[0] not in sel and s.name not in sel:
            continue
        d = s.end - s.start
        ts = [s.start + d * k for k in (0.02, 0.25, 0.5, 0.75, 0.97)]
        ims = [small(comp(t, F), 4) for t in ts]
        grid(ims, 5, labels=[f"{t:.2f}" for t in ts]).save(os.path.join(out, f"{s.name}.png"))
        print(s.name)


# ---------------------------------------------------------------- parallel native frames
def _render_chunk(args):
    idxs, = args
    F = film()
    os.makedirs(CACHE, exist_ok=True)
    for i in idxs:
        t = i / FPS
        img, post = F.frame(t)
        Image.fromarray(img).save(os.path.join(CACHE, f"f{i:05d}.png"), compress_level=1)
        with open(os.path.join(CACHE, f"f{i:05d}.json"), 'w') as fh:
            json.dump(post, fh)
    return len(idxs)


def frame_range(a):
    if a.range:
        t0, t1 = [float(x) for x in a.range.split(':')]
        return list(range(int(round(t0 * FPS)), min(NFRAMES, int(round(t1 * FPS)))))
    if getattr(a, 'shots', None):
        F = film()
        sel = set(a.shots.split(','))
        out = []
        for s in F.shots:
            if s.name.split('_')[0] in sel or s.name in sel:
                out += list(range(int(math.ceil(s.start * FPS - 1e-9)), int(math.ceil(s.end * FPS - 1e-9))))
        return out
    return list(range(NFRAMES))


def cmd_frames(a):
    idxs = frame_range(a)
    n = a.workers
    chunks = [idxs[k::n] for k in range(n)]
    t = time.time()
    with Pool(n) as p:
        done = sum(p.map(_render_chunk, [(c,) for c in chunks]))
    print(f"rendered {done} frames in {time.time() - t:.1f}s")


def _encode_segment(args):
    """Compose one contiguous run of cached frames and encode it (video only)."""
    idxs, path, crf, preset = args
    cmd = [FFMPEG, '-y', '-loglevel', 'error', '-nostats', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-tune', 'animation',
           '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-threads', '2', '-r', str(FPS), path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in idxs:
        img = np.array(Image.open(os.path.join(CACHE, f"f{i:05d}.png")).convert('RGB'))
        with open(os.path.join(CACHE, f"f{i:05d}.json")) as fh:
            post = json.load(fh)
        p.stdin.write(compose(img, post, i / FPS, song.LYRICS).tobytes())
    p.stdin.close()
    p.wait()
    return path


def cmd_encode(a):
    """Parallel: N workers each compose + encode a contiguous segment; then concat (stream copy) and mux the audio."""
    out = a.out or os.path.join(ROOT, 'out', 'final_pdoom_pixel_chatgpt_claude.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    idxs = frame_range(a)
    t0, dur = idxs[0] / FPS, len(idxs) / FPS
    segdir = os.path.join(ROOT, 'cache', 'segments')
    os.makedirs(segdir, exist_ok=True)
    n = max(1, a.workers)
    size = math.ceil(len(idxs) / n)
    jobs = [(idxs[k * size:(k + 1) * size], os.path.join(segdir, f'seg{k}.mp4'), a.crf, a.preset) for k in range(n)
            if idxs[k * size:(k + 1) * size]]
    t = time.time()
    with Pool(len(jobs)) as p:
        segs = p.map(_encode_segment, jobs)
    lst = os.path.join(segdir, 'list.txt')
    with open(lst, 'w') as fh:
        fh.writelines(f"file '{s}'\n" for s in segs)
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-ss', f'{t0:.4f}', '-t', f'{dur:.4f}', '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', out], check=True)
    print(f'wrote {out} in {time.time() - t:.0f}s')


def cmd_preview(a):
    """Single-process quick preview at 960x540 with audio."""
    F = film()
    t0, t1 = [float(x) for x in a.times.split(':')]
    out = a.out or os.path.join(ROOT, 'out', 'preview.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fps = a.fps
    n = int(round((t1 - t0) * fps))
    cmd = [FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW // 2}x{OH // 2}',
           '-r', str(fps), '-i', '-', '-ss', f'{t0:.4f}', '-t', f'{t1 - t0:.4f}', '-i', AUDIO, '-map', '0:v', '-map', '1:a',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        t = t0 + k / fps
        p.stdin.write(comp(t, F)[::2, ::2].tobytes())
    p.stdin.close()
    p.wait()
    print('wrote', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('times', nargs='?', default='')
    ap.add_argument('--out')
    ap.add_argument('--cols', type=int, default=4)
    ap.add_argument('--k', type=int, default=4)
    ap.add_argument('--every', type=int, default=3)
    ap.add_argument('--range')
    ap.add_argument('--shots')
    ap.add_argument('--only')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--crf', type=int, default=14)
    ap.add_argument('--preset', default='slow')
    ap.add_argument('--fps', type=int, default=30)
    a = ap.parse_args()
    {'sheet': cmd_sheet, 'strip': cmd_strip, 'stills': cmd_stills, 'shots': cmd_shots, 'frames': cmd_frames,
     'encode': cmd_encode, 'preview': cmd_preview}[a.cmd](a)


if __name__ == '__main__':
    main()
