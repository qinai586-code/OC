"""QC for the v9 full-length candidate: stream facts, audio vs the locked music (whole length and the tail), the final
encode against the lossless master frame by frame, and the timeline itself (cut jumps, frozen runs, near-black frames).
Writes tests/v9_evidence/qc_v9.json."""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import song_v9 as SV
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'tests', 'v9_evidence', 'qc_v9.json')
V9 = SV.OUT
DEC = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:in_range=tv:in_color_matrix=bt601'
W, H, N = SV.W, SV.H, SV.N
q = {}
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', V9]))
q['streams'] = [{k: s.get(k) for k in ('codec_type', 'codec_name', 'width', 'height', 'pix_fmt', 'r_frame_rate', 'nb_frames', 'duration',
                                       'bit_rate', 'sample_rate', 'channels', 'color_space', 'color_range')} for s in pr['streams']]
q['bytes'] = os.path.getsize(V9)
ts = sorted(float(x) for x in subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'packet=pts_time',
                                                         '-of', 'csv=p=0', V9]).decode().split())
q['video_frames'] = len(ts)
q['irregular_steps'] = int((np.abs(np.diff(ts) - 1 / 24) > 1e-3).sum())


def pcm(path, rate=8000):
    return np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a', '-ac', '1', '-ar', str(rate), '-f', 'f32le', '-']),
                         np.float32)


a, b = pcm(V9), pcm(SV.AUDIO)
q['audio_seconds'] = dict(candidate=round(len(a) / 8000, 4), locked_music=round(len(b) / 8000, 4))
n = min(len(a), len(b))
lags = range(-80, 81)
cc = [np.corrcoef(a[max(0, l):n + min(0, l)], b[max(0, -l):n - max(0, l)])[0, 1] for l in lags]
k = int(np.argmax(cc))
q['audio_corr_whole'] = dict(corr=round(float(cc[k]), 5), lag_ms=list(lags)[k] / 8.0)
seg = []
for t0 in range(0, int(n / 8000) - 9, 10):
    s0, s1 = t0 * 8000, (t0 + 10) * 8000
    seg.append(round(float(np.corrcoef(a[s0:s1], b[s0:s1])[0, 1]), 4))
q['audio_corr_per_10s_min'] = min(seg)
tail = lambda x: float(np.sqrt(np.mean(x[-2 * 8000:] ** 2)))
q['audio_tail_last2s_rms'] = dict(candidate=round(tail(a[:n]), 6), locked_music=round(tail(b[:n]), 6),
                                  ratio=round(tail(a[:n]) / max(tail(b[:n]), 1e-9), 3))


def reader(path):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', DEC, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    while True:
        bb = p.stdout.read(W * H * 3)
        if len(bb) < W * H * 3:
            return
        yield np.frombuffer(bb, np.uint8).reshape(H, W, 3)


psnr, jump, mean_l, frozen = [], [], [], []
prev = None
for f, (fin, mb) in enumerate(zip(reader(V9), SV.master_frames())):
    m = np.frombuffer(mb, np.uint8).reshape(H, W, 3)
    d = (fin.astype(np.float32) - m) ** 2
    psnr.append(10 * np.log10(255 ** 2 / max(float(d.mean()), 1e-6)))
    lum = m.astype(np.float32) @ np.array([0.114, 0.587, 0.299], np.float32)
    mean_l.append(float(lum.mean()))
    if prev is not None:
        jump.append(float(np.abs(lum - prev).mean()))
        frozen.append(bool(np.array_equal(lum, prev)))
    prev = lum
psnr = np.array(psnr)
q['final_vs_master'] = dict(frames=len(psnr), psnr_mean=round(float(psnr.mean()), 2), psnr_min=round(float(psnr.min()), 2),
                            worst_frames=[int(x) for x in np.argsort(psnr)[:8]], frames_below_38dB=int((psnr < 38).sum()))
cuts = [f0 for _, f0, _ in SV.parts()][1:]
jump = np.array(jump)
q['cut_jumps'] = {str(c): round(float(jump[c - 1]), 2) for c in cuts}
q['largest_frame_to_frame_changes'] = [(int(i + 1), round(float(jump[i]), 2), (i + 1) in cuts) for i in np.argsort(-jump)[:15]]
fr = np.array(frozen)
runs, s0 = [], None
for i, z in enumerate(list(fr) + [False]):
    if z and s0 is None:
        s0 = i
    elif not z and s0 is not None:
        if i - s0 >= 3:
            runs.append((s0, i + 1))
        s0 = None
q['identical_frame_runs_ge4'] = runs
ml = np.array(mean_l)
q['near_black_frames_meanY_lt8'] = [int(x) for x in np.where(ml < 8)[0]]
json.dump(q, open(OUT, 'w'), indent=1)
print(json.dumps({k: v for k, v in q.items() if k not in ('streams',)}, indent=1))
