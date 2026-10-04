import json, os, subprocess, sys, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clarity_metrics import lum, band
S = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
R = '/home/user/OC/loading2/rev3'
V8, V7 = R + '/tests/DEMO_0-43_v8_720p.mp4', R + '/tests/DEMO_0-43_v7_720p.mp4'
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', V8]))
for s in pr['streams']:
    print(s['codec_type'], s.get('codec_name'), s.get('width'), s.get('height'), s.get('pix_fmt'), s.get('r_frame_rate'), s.get('nb_frames'), s.get('duration'), s.get('bit_rate'))
ts = sorted(float(x) for x in subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'packet=pts_time', '-of', 'csv=p=0', V8]).decode().split())
print('frames', len(ts), 'irregular steps', int((np.abs(np.diff(ts) - 1 / 24) > 1e-3).sum()))
# audio vs the locked master
def pcm(path, t=43.25):
    return np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-t', str(t), '-ac', '1', '-ar', '8000', '-f', 'f32le', '-']), np.float32)
a, b = pcm(V8), pcm(AUDIO)
n = min(len(a), len(b)); a, b = a[:n], b[:n]
lags = range(-80, 81)
cc = [np.corrcoef(a[max(0, l):n + min(0, l)], b[max(0, -l):n - max(0, l)])[0, 1] for l in lags]
k = int(np.argmax(cc)); print('audio: correlation %.4f at %+.1f ms (%.2f s)' % (cc[k], list(lags)[k] / 8.0, n / 8000))
# per-frame: v8 frames vs v7 frames (pre-encode), and each mp4 vs its own pre-encode frames
DEC = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:in_range=tv:in_color_matrix=bt601'
def reader(path):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', DEC, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    while True:
        bb = p.stdout.read(1280 * 720 * 3)
        if len(bb) < 1280 * 720 * 3:
            return
        yield np.frombuffer(bb, np.uint8).reshape(720, 1280, 3)
def v8src(f):
    p = S + '/v8/op/f%04d.png' % f
    return p if os.path.exists(p) else S + '/v7/cache/f%04d.png' % f
shots = json.load(open(R + '/tests/DEMO_0-43_v7_shots.json'))
rows = {}
changed = []
for f, (d8, d7) in enumerate(zip(reader(V8), reader(V7))):
    p8, p7 = cv2.imread(v8src(f)), cv2.imread(S + '/v7/cache/f%04d.png' % f)
    if not np.array_equal(p8, p7):
        changed.append(f)
    out = []
    for d, p in ((d8, p8), (d7, p7)):
        e = lum(d.astype(np.float32)) - lum(p.astype(np.float32))
        fd, fp = band(lum(d.astype(np.float32))), band(lum(p.astype(np.float32)))
        out.append((20 * np.log10(255 / max(np.sqrt((e ** 2).mean()), 1e-6)), float(e.mean()), float(np.sqrt((fd ** 2).mean() / max((fp ** 2).mean(), 1e-9)))))
    sh = [s['id'] for s in shots if s['frames'][0] <= f <= s['frames'][1]][0]
    rows.setdefault(sh, []).append(out)
print('decoded both: %d frames' % (f + 1))
runs = []
for x in changed:
    if runs and x == runs[-1][1] + 1:
        runs[-1][1] = x
    else:
        runs.append([x, x])
print('pre-encode frames that differ v8 vs v7: %d in runs %s' % (len(changed), runs))
print('%-6s %-9s | v7 mp4 vs its frames: PSNR  bias  fine | v8 mp4 vs its frames: PSNR  bias  fine' % ('shot', 'frames'))
tab = []
for s in shots:
    r = np.array(rows[s['id']])
    v8_, v7_ = r[:, 0].mean(0), r[:, 1].mean(0)
    tab.append(dict(shot=s['id'], frames=s['frames'], v7=[round(float(x), 3) for x in v7_], v8=[round(float(x), 3) for x in v8_]))
    print('%-6s %4d-%-4d |                    %5.2f %+5.2f %5.3f |                     %5.2f %+5.2f %5.3f' % (s['id'], s['frames'][0], s['frames'][1], *v7_, *v8_))
json.dump(dict(changed_runs=runs, per_shot=tab, audio_corr=float(cc[k]), audio_lag_ms=list(lags)[k] / 8.0), open(S + '/v8/qc_v8.json', 'w'), indent=1)
