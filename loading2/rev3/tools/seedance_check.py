"""Check a returned Seedance clip and fit it to the locked track (no music change).

  python3 rev3/tools/seedance_check.py CLIP.mp4 --name P1-S1_try1 --in 0.500 --song 7.500 --dur 1.667 \
      [--mouth x0,y0,x1,y1] [--light-box x0,y0,x1,y1] [--min-move PX]

--in        seconds into the clip where the usable range starts (played 1:1, never retimed)
--song      song time where that frame lands; --dur usable duration
--mouth     mouth box in the first-frame image's pixel coordinates (default: the S1 v8 lips),
            scaled to the clip's resolution
--light-box region the light must stay inside during the usable window (first-frame coordinates)
--min-move  minimum net down-left travel of the light across the usable window (first-frame px)

Writes rev3/seedance/checks/<name>/:
  report.json   container facts and measured flags for the whole clip and for the usable window
                (light count and path, stalls, box, camera drift, mouth activity, frame-change spikes)
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
    """orb-like lights: a compact near-white core inside a saturated warm (orange) ring.
    The shirt and skin highlights in the P1 frames have one of these but not both.
    Returns a list of (core area, x, y), largest first."""
    f = frame.astype(np.int16)
    b, g, r = f[:, :, 0], f[:, :, 1], f[:, :, 2]
    H, W = b.shape
    core = ((r > 230) & (g > 200) & (b > 150)).astype(np.uint8)     # white to warm-white
    n, lab, st, cen = cv2.connectedComponentsWithStats(core)
    amin, amax = 0.00002 * H * W, 0.004 * H * W                     # 31..6300 px at 1672x941
    out = []
    for i in range(1, n):
        a = int(st[i, 4])
        if not amin <= a <= amax:
            continue
        cx, cy = cen[i]
        rc = np.sqrt(a / np.pi)
        if a < 0.55 * np.pi * (max(st[i, 2], st[i, 3]) / 2.0) ** 2:  # a disc, not a streak or finger
            continue
        r0, r1, r2 = rc + 2, 1.8 * rc + 4, 3.0 * rc + 10   # glow ring, then local background
        x0, x1 = int(max(0, cx - r2)), int(min(W, cx + r2 + 1))
        y0, y1 = int(max(0, cy - r2)), int(min(H, cy + r2 + 1))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xx - cx, yy - cy)
        ring, back = (d >= r0) & (d <= r1), (d > r1 + 2) & (d <= r2)
        if ring.sum() < 8 or back.sum() < 8:
            continue
        rr, rb = r[y0:y1, x0:x1], (r - b)[y0:y1, x0:x1]
        warm = float(rb[ring].mean() - rb[back].mean())   # the glow is warmer than what it sits on
        lift = float(rr[ring].mean() - rr[back].mean())   # and brighter in red
        if warm > 40 and lift > 40:
            out.append((a, float(cx), float(cy)))
    return sorted(out, reverse=True)


def track_box(frames, sel, box, sx, sy):
    """Rigid motion of a region across the selected frames: features found inside box (first-frame
    coordinates) on frame sel[0], followed frame to frame with pyramidal Lucas-Kanade, then a RANSAC
    similarity fit against their start positions. Returns per output frame (rotation deg, shift px in
    first-frame coordinates). Rotation + = clockwise on screen (for a right-facing profile, chin down)."""
    x0, y0, x1, y1 = box
    x0, x1, y0, y1 = int(x0 * sx), int(x1 * sx), int(y0 * sy), int(y1 * sy)
    g = cv2.cvtColor(frames[sel[0]], cv2.COLOR_BGR2GRAY)
    mask = np.zeros_like(g)
    mask[y0:y1, x0:x1] = 255
    p0 = cv2.goodFeaturesToTrack(g, 300, 0.01, 5, mask=mask)
    if p0 is None or len(p0) < 6:
        return None
    start, cur, alive, prev = p0.copy(), p0.copy(), np.ones(len(p0), bool), g
    out = [(0.0, 0.0)]
    for i in sel[1:]:
        gi = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gi, cur, None, winSize=(21, 21), maxLevel=3)
        alive &= st.ravel() == 1
        cur, prev = nxt, gi
        if alive.sum() < 6:
            out.append(None)
            continue
        M, _ = cv2.estimateAffinePartial2D(start[alive], cur[alive], method=cv2.RANSAC, ransacReprojThreshold=2.0)
        if M is None:
            out.append(None)
            continue
        ang = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
        d = np.median((cur[alive] - start[alive]).reshape(-1, 2), axis=0)
        out.append((round(ang, 2), round(float(np.hypot(d[0] / sx, d[1] / sy)), 1)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--name', required=True)
    ap.add_argument('--in', dest='tin', type=float, required=True)
    ap.add_argument('--song', type=float, required=True)
    ap.add_argument('--dur', type=float, required=True)
    ap.add_argument('--mouth', default='565,325,600,360')
    ap.add_argument('--light-box', default=None)
    ap.add_argument('--min-move', type=float, default=0.0)
    ap.add_argument('--head', default=None, help='head box (horns, clip, face) for the rotation track')
    ap.add_argument('--hand', default=None, help='hand box for the hand-motion track')
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
                             light_path_start_clip_px=path[0] if path else None,
                             light_path_end_clip_px=path[-1] if path else None,
                             light_moves_down_left=bool(path and path[-1][0] < path[0][0] and path[-1][1] > path[0][1]),
                             max_camera_shift_px=float(max(abs(a) + abs(b) for a, b in drift)),
                             max_camera_shift_pct_of_width=round(100 * max(abs(a) for a, b in drift) / W, 2),
                             mouth_change_mean=round(float(np.mean(mouth)), 2), mouth_change_max=round(float(np.max(mouth)), 2),
                             frame_change_median=round(med, 3), frame_change_spike_frames=spikes),
                  track=track)

    # usable range -> 24 fps by frame selection (1:1 time, no retiming)
    n_out = int(round(args.dur * 24))
    sel = [min(len(frames) - 1, int(round((args.tin + k / 24.0) * fps))) for k in range(n_out)]

    # the same measurements restricted to the usable window, in first-frame (REF) pixel coordinates
    wt = [track[i] for i in sel]
    wpath = [(t['frame'], t['main'][1] / sx, t['main'][2] / sy) for t in wt if t['main']]
    bins = []                                   # net travel per 0.25 s of song time (6 output frames)
    for b in range(0, n_out - 1, 6):
        p = [q for q in wpath if sel[b] <= q[0] <= sel[min(b + 6, n_out - 1)]]
        bins.append(round(float(np.hypot(p[-1][1] - p[0][1], p[-1][2] - p[0][2])), 1) if len(p) > 1 else None)
    wrep = dict(clip_frames=[sel[0], sel[-1]], clip_seconds=[round(sel[0] / fps, 3), round(sel[-1] / fps, 3)],
               song=[args.song, round(args.song + n_out / 24.0, 3)], n_frames=n_out,
               frames_not_exactly_one_light=[t['frame'] for t in wt if t['n_lights'] != 1],
               light_start=[round(v, 1) for v in wpath[0][1:]] if wpath else None,
               light_end=[round(v, 1) for v in wpath[-1][1:]] if wpath else None,
               travel_per_quarter_second_px=bins,
               stalled_quarter_seconds=[k for k, v in enumerate(bins) if v is None or v < 3.0],
               max_camera_shift_px=float(max(abs(drift[i][0]) + abs(drift[i][1]) for i in sel)),
               mouth_change_max=round(float(max(mouth[i] for i in sel)), 2),
               frame_change_spike_frames=[i for i in spikes if sel[0] < i <= sel[-1]])
    if wpath:
        dx, dy = wpath[-1][1] - wpath[0][1], wpath[-1][2] - wpath[0][2]
        wrep['net_travel_px'] = round(float(np.hypot(dx, dy)), 1)
        wrep['moves_down_left'] = bool(dx < 0 and dy > 0)
        if args.min_move:
            wrep['meets_min_move'] = bool(dx < 0 and dy > 0 and np.hypot(dx, dy) >= args.min_move)
    if args.light_box:
        bx0, by0, bx1, by1 = [float(v) for v in args.light_box.split(',')]
        wrep['light_box'] = [bx0, by0, bx1, by1]
        wrep['frames_light_outside_box'] = [f for f, x, y in wpath if not (bx0 <= x <= bx1 and by0 <= y <= by1)]
    for key, box in (('head', args.head), ('hand', args.hand)):
        if not box:
            continue
        tr = track_box(frames, sel, [float(v) for v in box.split(',')], sx, sy)
        if tr is None:
            wrep[key] = 'no trackable features in the box'
            continue
        ok = [(k, a, s) for k, v in enumerate(tr) if v for a, s in [v]]
        wrep[key] = dict(rotation_deg_per_quarter_second=[tr[k][0] if tr[k] else None for k in range(0, n_out, 6)],
                         rotation_deg_end=ok[-1][1], rotation_deg_max_abs=max(abs(a) for k, a, s in ok),
                         first_output_frame_over_1deg=next((k for k, a, s in ok if abs(a) > 1.0), None),
                         shift_px_max=max(s for k, a, s in ok), frames_lost=n_out - len(ok))
    report['window'] = wrep
    json.dump(report, open(os.path.join(od, 'report.json'), 'w'), indent=1)
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
    print(json.dumps(report['window'], indent=1))
    print('wrote', od)


if __name__ == '__main__':
    main()
