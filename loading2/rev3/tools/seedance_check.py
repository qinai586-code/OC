"""Check a returned Seedance clip and fit it to the locked track (no music change).

  python3 rev3/tools/seedance_check.py CLIP.mp4 --name P1-S1_try1 --in 0.80 --song 7.500 --dur 1.667 \
      [--mouth x0,y0,x1,y1] [--ref FIRST_FRAME.png]

--in    seconds into the clip where the usable range starts
--song  song time where that frame lands; --dur usable duration
--mouth mouth box in the first-frame image's pixel coordinates (default: the P1-S1 candidate's lips),
        scaled to the clip's resolution

Writes rev3/seedance/checks/<name>/:
  report.json   container facts and measured flags (light count and path, camera drift, mouth
                activity, frame-change spikes)
  strip.jpg     8 frames across the usable range plus head crops
  fit.mp4       the usable range conformed to 24 fps by frame selection (no blending), 1920x1080,
                over the locked audio at the song time, with burned local and song timecode
Measurements flag problems; they do not certify smoothness, identity or emotional read.
"""
import argparse
import json
import os
import subprocess

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
REF_W, REF_H = 1672, 941                       # size of the P1 candidate first frames


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,codec_name:format=duration',
                          '-of', 'json', path], capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    s = j['streams'][0]
    num, den = map(int, s['avg_frame_rate'].split('/'))
    return dict(width=s['width'], height=s['height'], fps=num / den if den else None, codec=s['codec_name'],
                nb_frames=int(s.get('nb_frames', 0) or 0), duration=float(j['format']['duration']))


def read_frames(path):
    cap = cv2.VideoCapture(path)
    fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(f)
    return fr


def lights(frame):
    """small, very bright warm blobs (candidate orbs); returns list of (area, x, y)."""
    f = frame.astype(np.int16)
    b, g, r = f[:, :, 0], f[:, :, 1], f[:, :, 2]
    lum = (b + g + r) / 3
    m = ((lum > 225) & (r > 230) & (r - b > 10)).astype(np.uint8)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    out = [(int(st[i, 4]), float(cen[i][0]), float(cen[i][1])) for i in range(1, n) if 3 <= st[i, 4] <= 4000]
    return sorted(out, reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--name', required=True)
    ap.add_argument('--in', dest='tin', type=float, required=True)
    ap.add_argument('--song', type=float, required=True)
    ap.add_argument('--dur', type=float, required=True)
    ap.add_argument('--mouth', default='540,405,600,450')
    args = ap.parse_args()
    od = os.path.join(R, 'seedance', 'checks', args.name)
    os.makedirs(od, exist_ok=True)
    meta = probe(args.clip)
    frames = read_frames(args.clip)
    fps = meta['fps'] or 24.0
    H, W = frames[0].shape[:2]
    sx, sy = W / REF_W, H / REF_H
    mx0, my0, mx1, my1 = [int(v) for v in args.mouth.split(',')]
    mx0, mx1, my0, my1 = int(mx0 * sx), int(mx1 * sx), int(my0 * sy), int(my1 * sy)

    # light track, camera drift, mouth activity, frame-change spikes (whole clip)
    g0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    win = cv2.createHanningWindow((W, H), cv2.CV_32F)
    track, drift, mouth, dchg = [], [], [], []
    prev = None
    m0 = frames[0][my0:my1, mx0:mx1].astype(np.float32)
    for i, f in enumerate(frames):
        L = lights(f)
        track.append(dict(frame=i, t=round(i / fps, 3), n_lights=len(L), main=L[0] if L else None))
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        (dx, dy), _ = cv2.phaseCorrelate(g0, g, win)
        drift.append((round(dx, 2), round(dy, 2)))
        mouth.append(float(np.abs(f[my0:my1, mx0:mx1].astype(np.float32) - m0).mean()))
        if prev is not None:
            dchg.append(float(np.abs(g - prev).mean()))
        prev = g
    med = float(np.median(dchg)) if dchg else 0.0
    spikes = [i + 1 for i, v in enumerate(dchg) if med > 0 and v > 4 * med and v > 2.0]
    multi = [t['frame'] for t in track if t['n_lights'] > 1]
    path = [(t['main'][1], t['main'][2]) for t in track if t['main']]
    report = dict(meta=meta, frames_read=len(frames), usable=dict(clip_in=args.tin, song_start=args.song, dur=args.dur),
                  flags=dict(frames_with_more_than_one_light=multi[:50], n_frames_more_than_one_light=len(multi),
                             light_path_start=path[0] if path else None, light_path_end=path[-1] if path else None,
                             light_moves_down_left=bool(path and path[-1][0] < path[0][0] and path[-1][1] > path[0][1]),
                             max_camera_shift_px=float(max(abs(a) + abs(b) for a, b in drift)),
                             max_camera_shift_pct_of_width=round(100 * max(abs(a) for a, b in drift) / W, 2),
                             mouth_change_mean=round(float(np.mean(mouth)), 2), mouth_change_max=round(float(np.max(mouth)), 2),
                             frame_change_median=round(med, 3), frame_change_spike_frames=spikes),
                  track=track)
    json.dump(report, open(os.path.join(od, 'report.json'), 'w'), indent=1)

    # usable range -> 24 fps by frame selection
    n_out = int(round(args.dur * 24))
    sel = [min(len(frames) - 1, int(round((args.tin + k / 24.0) * fps))) for k in range(n_out)]
    strip_idx = [sel[int(i * (n_out - 1) / 7)] for i in range(8)]
    tiles = []
    for i in strip_idx:
        im = cv2.resize(frames[i], (480, int(480 * H / W)))
        cv2.putText(im, 'clip f%d  %.2fs' % (i, i / fps), (6, im.shape[0] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    cv2.imwrite(os.path.join(od, 'strip.jpg'), np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])]), [cv2.IMWRITE_JPEG_QUALITY, 88])

    out = os.path.join(od, 'fit.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1920x1080', '-r', '24', '-i', '-',
                           '-ss', '%.4f' % args.song, '-t', '%.4f' % (n_out / 24.0), '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                           '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out],
                          stdin=subprocess.PIPE)
    for k, i in enumerate(sel):
        f = cv2.resize(frames[i], (1920, int(round(1920 * H / W))), interpolation=cv2.INTER_CUBIC)
        canvas = np.zeros((1080, 1920, 3), np.uint8)
        y0 = max(0, (1080 - f.shape[0]) // 2)
        fy0 = max(0, (f.shape[0] - 1080) // 2)
        canvas[y0:y0 + min(1080, f.shape[0])] = f[fy0:fy0 + min(1080, f.shape[0])]
        t_song = args.song + k / 24.0
        cv2.putText(canvas, '%s  local %.3fs (clip f%d)  song %d:%06.3f' % (args.name, k / 24.0, i, int(t_song // 60), t_song % 60),
                    (16, 1064), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (235, 235, 235), 2, cv2.LINE_AA)
        ff.stdin.write(canvas.tobytes())
    ff.stdin.close()
    ff.wait()
    print(json.dumps(report['flags'], indent=1))
    print('wrote', od)


if __name__ == '__main__':
    main()
