"""Render shots to JPEG frames, build review sheets, assemble the film.

  python3 render.py S01 S02        # render shots (all frames)
  python3 render.py S01 --step 12  # quick pass: every 12th frame
  python3 render.py S01 --sheet    # contact sheet of rendered frames
  python3 render.py all --assemble # concat all frames + master audio -> out/
"""
import argparse
import glob
import importlib
import multiprocessing as mp
import subprocess
import sys
import time
import cv2
import numpy as np
from common import *

FRAMES = os.path.join(ROOT, 'frames')
OUT = os.path.join(os.path.dirname(ROOT), 'out')
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
SONG_LEN = 213.40

MODULES = ['shots_a', 'shots_b', 'shots_c', 'shots_d', 'shots_e', 'shots_f']


def registry():
    reg = {}
    for m in MODULES:
        try:
            mod = importlib.import_module(m)
        except ModuleNotFoundError as e:
            if e.name == m:
                continue
            raise
        for k, v in mod.SHOTS.items():
            reg[k] = v
    return reg


_shot = {}


def _render_frame(args):
    name, f, quality = args
    reg = registry()
    if name not in _shot:
        s = reg[name]()
        s.setup()
        _shot[name] = s
    s = _shot[name]
    t = f / FPS
    img = s.render(t)
    path = os.path.join(FRAMES, name, f'{f:05d}.jpg')
    im = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)[:, :, ::-1]
    cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return f


def frames_of(cls):
    f0 = int(round(cls.t0 * FPS))
    f1 = int(round(cls.t1 * FPS))
    return list(range(f0, f1))


def render(names, step=1, jobs=4, quality=94, only=None):
    reg = registry()
    for n in names:
        cls = reg[n]
        os.makedirs(os.path.join(FRAMES, n), exist_ok=True)
        fr = frames_of(cls)
        if only is not None:
            fr = [f for f in fr if only[0] <= f / FPS < only[1]]
        fr = fr[::step]
        t = time.time()
        if jobs <= 1:
            for f in fr:
                _render_frame((n, f, quality))
        else:
            with mp.Pool(jobs) as pool:
                for _ in pool.imap_unordered(_render_frame, [(n, f, quality) for f in fr], chunksize=2):
                    pass
        print(f'{n}: {len(fr)} frames in {time.time() - t:.1f}s', flush=True)


def sheet(names, cols=6, w=480, every=None):
    reg = registry()
    for n in names:
        files = sorted(glob.glob(os.path.join(FRAMES, n, '*.jpg')))
        if not files:
            continue
        if every:
            files = files[::every]
        if len(files) > 36:
            idx = np.linspace(0, len(files) - 1, 36).astype(int)
            files = [files[i] for i in idx]
        ims = []
        for fp in files:
            im = cv2.imread(fp)
            im = cv2.resize(im, (w, int(w * 9 / 16)), interpolation=cv2.INTER_AREA)
            f = int(os.path.basename(fp)[:5])
            cv2.putText(im, f'{n} {f / FPS:6.2f}s', (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            ims.append(im)
        while len(ims) % cols:
            ims.append(np.zeros_like(ims[0]))
        rows = [np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]
        out = os.path.join(FRAMES, f'sheet_{n}.jpg')
        cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(out)


def clip(names, crf=18):
    """Per-shot preview mp4 with the matching audio segment."""
    reg = registry()
    os.makedirs(OUT, exist_ok=True)
    for n in names:
        cls = reg[n]
        fr = frames_of(cls)
        d = os.path.join(FRAMES, n)
        out = os.path.join(OUT, f'preview_{n}.mp4')
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-start_number', str(fr[0]), '-i', os.path.join(d, '%05d.jpg'),
               '-ss', f'{fr[0] / FPS:.4f}', '-t', f'{len(fr) / FPS:.4f}', '-i', AUDIO,
               '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(crf), '-preset', 'medium',
               '-c:a', 'aac', '-b:a', '256k', '-shortest', out]
        subprocess.run(cmd, check=True)
        print(out)


def assemble(names, crf=16, out_name='LOADING_MV.mp4'):
    reg = registry()
    allf = os.path.join(FRAMES, '_all')
    if os.path.exists(allf):
        for p in glob.glob(os.path.join(allf, '*.jpg')):
            os.remove(p)
    os.makedirs(allf, exist_ok=True)
    total = int(round(SONG_LEN * FPS))
    have = {}
    for n in names:
        for f in frames_of(reg[n]):
            p = os.path.join(FRAMES, n, f'{f:05d}.jpg')
            if os.path.exists(p):
                have[f] = p
    black = os.path.join(allf, '_black.jpg')
    cv2.imwrite(black, np.zeros((H_OUT, W_OUT, 3), np.uint8))
    missing = 0
    for f in range(total):
        src = have.get(f, black)
        if src == black:
            missing += 1
        os.symlink(src, os.path.join(allf, f'{f:05d}.jpg'))
    print('missing frames:', missing)
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, out_name)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(allf, '%05d.jpg'), '-i', AUDIO,
           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(crf), '-preset', 'slow',
           '-tune', 'animation', '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', '-shortest', out]
    subprocess.run(cmd, check=True)
    print(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('shots', nargs='+')
    ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--sheet', action='store_true')
    ap.add_argument('--clip', action='store_true')
    ap.add_argument('--assemble', action='store_true')
    ap.add_argument('--norender', action='store_true')
    ap.add_argument('--only', type=float, nargs=2, default=None)
    a = ap.parse_args()
    names = a.shots
    if names == ['all']:
        names = sorted(registry().keys(), key=lambda k: registry()[k].t0)
    if not (a.norender or a.assemble):
        render(names, a.step, a.jobs, only=a.only)
    if a.sheet:
        sheet(names)
    if a.clip:
        clip(names)
    if a.assemble:
        assemble(names)
