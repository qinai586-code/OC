"""Close-up test, 0:08.45-0:21 of the master, with the drawn face assets.

  S1 8.452-13.40  A sings (verse 1, lines 1-2): profile close-up, slow push in
  S2 13.40-14.45  the song's silence: B3 (eyes closed, exhale), time frozen, the camera still drifts
  S3 14.45-21.0   A sings (lines 3-4): wider, face low in frame, space above for the sky

What moves and why:
- mouth: the held three-shape flaps from lipsync.py (0 closed, 1 half, 2 open), a drawn panel each
- eyes: a blink (half, closed, closed, half) just after each cut and at phrase edges, never inside a
  held note; after 0.4 s of a held open note the lids drop to half, as singers do
- head: chin lifts through a phrase (anticipating it by 0.1 s), a slow idle sway, breath
- hair: the back hair sways from the ears down; embers rise and brighten on the tracked beats
- the figure fades into bare paper below the shoulders ("the painting that finishes itself")

Usage: python3 closeup.py OUTDIR [--sheet]
"""
import sys, os, json, numpy as np, cv2
from multiprocessing import Pool
import faces

W, H, FPS = 1280, 720, 30
T0, T_SIL0, T_SIL1, T1 = 8.452, 13.40, 14.45, 21.0
HERE = os.path.dirname(os.path.abspath(__file__))
LS = json.load(open(f'{HERE}/../timing/lipsync_opening.json'))
BEATS = np.array([b for b in json.load(open(f'{HERE}/../timing/p0_beatmap.json'))['beats_s'] if b < 22])
EMBER = np.array([1.00, 0.60, 0.26], np.float32); JADE = np.array([0.30, 0.95, 0.72], np.float32)
PAPER = np.array([0.95, 0.925, 0.875], np.float32); WARM = np.array([1.0, 0.93, 0.80], np.float32)

def ss(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def tau(t):                          # story time stops in the silence
    return t if t < T_SIL0 else (T_SIL0 if t < T_SIL1 else t - (T_SIL1 - T_SIL0))
def beat_pulse(s):
    b = BEATS[BEATS <= s]; return float(np.exp(-(s - b[-1]) * 7)) if len(b) else 0.0

# ---------------------------------------------------------------- timing: mouth, eyes, head
def flap_track(who):
    fr = {}
    for tr in LS['tracks']:
        if tr['who'] != who: continue
        i0 = int(round(tr['t0'] * FPS))
        for i, c in enumerate(tr['flaps30']): fr[i0 + i] = int(c)
    return fr
FLAP = flap_track('A')
def mouth_at(i): return FLAP.get(i, 0)                        # i = video frame index at real time

def blink_frames():
    """Blink starts: 0.25 s after each A cut, then roughly every 3-4.5 s at a phrase edge."""
    starts = []
    for c0, c1 in ((T0, T_SIL0), (T_SIL1, T1)):
        f0, f1 = int(round(c0 * FPS)), int(round(c1 * FPS))
        cand = f0 + 8; nxt = cand
        while nxt < f1 - 6:
            # search +-0.6 s for a frame at a phrase edge (mouth closing or closed), not inside a held open note
            best = None
            for d in sorted(range(-18, 19), key=abs):
                j = nxt + d
                if f0 + 6 <= j < f1 - 6 and all(mouth_at(k) < 2 for k in range(j, j + 4)) and (mouth_at(j - 1) != mouth_at(j) or mouth_at(j) == 0):
                    best = j; break
            if best is not None and (not starts or best - starts[-1] > 45): starts.append(best)
            nxt = (best if best is not None else nxt) + int(FPS * (3.0 + 1.5 * ((len(starts) * 37) % 10) / 10))
    return starts
BLINKS = blink_frames()
def eye_at(i):
    for b in BLINKS:
        if b <= i < b + 4: return (1, 2, 2, 1)[i - b]
    # held open note: lids drop to half after 0.4 s
    if mouth_at(i) == 2 and all(mouth_at(k) == 2 for k in range(i - 12, i)): return 1
    return 0
def sing_at(t):                                                # 0..1, running mean with 0.1 s anticipation
    i = int(round((t + 0.1) * FPS)); return np.mean([mouth_at(k) for k in range(i - 18, i + 1)]) / 2

# ---------------------------------------------------------------- assets
HA = faces.Head('A')
B3 = faces.pose('B3')
def fade_bottom(rgba, y0, y1):                                  # the figure dissolves into bare paper
    out = rgba.copy(); ys = np.arange(out.shape[0])[:, None]
    out[..., 3] *= 1 - ss(y0, y1, ys); return out
PLATES = {(m, e): fade_bottom(HA.plate(m, e), 440, 560) for m in range(3) for e in range(3)}
B3F = fade_bottom(B3, 1100, 1350)
NECK_A = (300.0, 470.0)                                         # plate coords: rotation pivot
hy, hx = np.mgrid[0:1024, 0:512].astype(np.float32)
HAIR_W = (ss(300, 560, hy) * ss(300, 110, hx)).astype(np.float32)   # A's back hair, ears down

rng = np.random.default_rng(3)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
grain = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 1.0)
fibre = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 20)
PAPER_TEX = PAPER * (0.965 + 0.05 * grain[..., None] + 0.07 * (fibre[..., None] - 0.5))
VIGN = (1 - 0.45 * (((xx - W / 2) / (W / 1.1)) ** 2 + ((yy - H / 2) / (H / 1.0)) ** 2))[..., None]
NE = 110
e_x = rng.uniform(0, W, NE); e_y0 = rng.uniform(0, H, NE); e_sp = rng.uniform(14, 48, NE)
e_tier = rng.integers(0, 3, NE); e_ph = rng.uniform(0, 2 * np.pi, NE)
e_col = np.where(rng.random(NE)[:, None] < 0.22, JADE, EMBER)
e_w = rng.uniform(0.5, 1.0, NE) * np.array([4.0, 11.0, 26.0])[e_tier]

# ---------------------------------------------------------------- shots
def shot(t):
    if t < T_SIL0:   # S1: push in, face right of centre
        u = (t - T0) / (T_SIL0 - T0)
        return dict(kind='A', scale=1.24 + 0.08 * u, face=(0.54 * W - 8 * u, 0.55 * H), light=(0.56, 0.45))
    if t < T_SIL1:   # S2: B in the silence
        u = (t - T_SIL0) / (T_SIL1 - T_SIL0)
        return dict(kind='B3', scale=0.62 + 0.02 * u, face=(0.47 * W, 0.46 * H), light=(0.47, 0.40))
    u = (t - T_SIL1) / (T1 - T_SIL1)   # S3: wider, face low, sky above; slow pull out, drift up
    return dict(kind='A', scale=1.08 - 0.06 * u, face=(0.40 * W, 0.64 * H - 10 * u), light=(0.45, 0.55))

STARS = [(0.58, 0.14), (0.66, 0.24), (0.74, 0.17), (0.82, 0.29), (0.78, 0.42), (0.90, 0.36), (0.93, 0.20)]
FACE_A = (395.0, 330.0)          # plate coords of A's cheek, the framing anchor
FACE_B3 = (560.0, 520.0)         # B3 pose coords of her cheek

def place(rgba, anchor, target, scale, angle=0.0, pivot=None):
    pv = pivot or anchor
    M = cv2.getRotationMatrix2D(pv, angle, scale)
    p = M @ np.array([anchor[0], anchor[1], 1.0])                # where the anchor lands
    M[:, 2] += np.array(target) - p
    return cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))

def frame_at(i):
    t = i / FPS; s = tau(t); sh = shot(t); frozen = T_SIL0 <= t < T_SIL1
    # plate: paper under a pool of light at the face
    lx, ly = sh['light']
    pool = np.exp(-(((xx - lx * W) / (0.55 * W)) ** 2 + ((yy - ly * H) / (0.60 * H)) ** 2))
    bg = PAPER_TEX * (0.42 + 0.58 * pool[..., None])
    bg = bg + (pool * 0.05 * (1 + 0.8 * beat_pulse(s)))[..., None] * WARM
    # character
    b = np.sin(2 * np.pi * s / 3.7)
    if sh['kind'] == 'A':
        m, e = mouth_at(i), eye_at(i)
        plate = PLATES[(m, e)]
        wind = 0.75 + 0.25 * np.sin(2 * np.pi * s / 7.1)
        dx = 2.6 * wind * np.sin(2 * np.pi * s / 2.9 - hy / 140) * HAIR_W
        dy = 0.7 * np.sin(2 * np.pi * s / 2.9 + 1.3 - hy / 140) * HAIR_W
        plate = cv2.remap(plate, (hx - dx).astype(np.float32), (hy - dy).astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        ang = 0.5 * np.sin(2 * np.pi * s / 5.3) + 1.6 * sing_at(t)             # chin up through a phrase
        tgt = (sh['face'][0], sh['face'][1] - 2.0 * b)
        fig = place(plate, FACE_A, tgt, sh['scale'] * (1 + 0.003 * b), ang, NECK_A)
    else:
        fig = place(B3F, FACE_B3, sh['face'], sh['scale'])
    a = fig[..., 3:]
    # light wrap: the lit paper bleeds a little over the silhouette's edge
    edge = np.clip(a - cv2.erode(a, np.ones((9, 9), np.uint8))[..., None], 0, 1)
    wrap = cv2.GaussianBlur(bg, (0, 0), 10) * edge * 0.35
    col = fig[..., :3] * (0.94 + 0.06 * pool[..., None]) + wrap
    frame = bg * (1 - a) + col * a
    # embers: soft bokeh rising past the lens, brighter on the beats
    lay = np.zeros((H // 2, W // 2, 3), np.float32); big = np.zeros_like(lay); mid = np.zeros_like(lay)
    y = (e_y0 - e_sp * s) % (H + 80) - 40; x = e_x + 14 * np.sin(s * 0.7 + e_ph)
    wt = e_w * (0.7 + 0.3 * np.sin(s * 5 + e_ph * 3)) * (1 + 0.7 * beat_pulse(s))
    for k in range(NE):
        tgtl = (lay, mid, big)[e_tier[k]]
        xi, yi = int(x[k] / 2), int(y[k] / 2)
        if 0 <= xi < W // 2 and 0 <= yi < H // 2: tgtl[yi, xi] += e_col[k] * wt[k]
    L = cv2.GaussianBlur(lay, (0, 0), 1.2) + cv2.GaussianBlur(mid, (0, 0), 3.5) + cv2.GaussianBlur(big, (0, 0), 8)
    L = cv2.resize(L, (W, H), interpolation=cv2.INTER_LINEAR)
    L = 1 - np.exp(-L * 1.2)
    frame = frame + L * (1 - frame)
    frame = frame * (1 - 0.35 * L.mean(-1, keepdims=True)) + L * 0.35 * EMBER   # warm the paper under them
    # after the silence, the embers' constellation draws itself in the space she looks into
    if t >= T_SIL1:
        lay = np.zeros((H, W), np.float32); u = t - T_SIL1
        pts = [(int(x * W), int(y * H)) for x, y in STARS]
        for j in range(len(pts) - 1):
            v = float(np.clip((u - 0.9 - 0.35 * j) / 0.4, 0, 1))
            if v > 0:
                p0 = np.array(pts[j]); p1 = p0 + (np.array(pts[j + 1]) - p0) * v
                cv2.line(lay, tuple(int(c) for c in p0), tuple(int(c) for c in p1), 0.8, 2, cv2.LINE_AA)
        for j, pt in enumerate(pts):
            lit = float(np.clip((u - 0.3 - 0.25 * j) / 0.3, 0, 1)) * (0.85 + 0.15 * np.sin(s * 3 + j))
            cv2.circle(lay, pt, 5, 1.0 * lit, -1, cv2.LINE_AA)
        g = cv2.GaussianBlur(lay, (0, 0), 1.0) + cv2.GaussianBlur(lay, (0, 0), 6) * 1.5
        gold = np.array([0.72, 0.52, 0.22], np.float32)
        frame = frame * (1 - 0.8 * np.clip(g, 0, 1)[..., None]) + gold * 0.8 * np.clip(g, 0, 1)[..., None]
    if frozen:        # the silence: colour drains a little, as in the opening
        g = frame.mean(-1, keepdims=True); frame = frame * 0.6 + g * np.array([0.93, 0.98, 1.06]) * 0.4
    if abs(t - T_SIL1) < 0.2 and t >= T_SIL1: frame = frame + 0.10 * np.exp(-(t - T_SIL1) * 12)
    frame = frame * VIGN
    frame = frame + np.random.default_rng(int(round(s * FPS))).normal(0, 0.010, (H, W, 1))
    return (np.clip(frame, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)

def work(args):
    out, i = args
    cv2.imwrite(f'{out}/f{i - int(round(T0 * FPS)):05d}.png', cv2.cvtColor(frame_at(i), cv2.COLOR_RGB2BGR))

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    i0, i1 = int(round(T0 * FPS)), int(round(T1 * FPS))
    if '--sheet' in sys.argv:
        pick = [i0 + 10, BLINKS[0] + 1, 267, 283, 300, 345, int(13.9 * FPS), int(14.7 * FPS), 505, 575, 590, 625]
        with Pool(4) as p: fr = p.map(frame_at, pick)
        tiles = [cv2.resize(f, (W // 2, H // 2), interpolation=cv2.INTER_AREA) for f in fr]
        for i, im in zip(pick, tiles):
            cv2.putText(im, f'{i / FPS:.2f}s m{mouth_at(i)} e{eye_at(i)}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 60, 60), 2)
        rows = [np.concatenate(tiles[k:k + 4], 1) for k in range(0, len(tiles), 4)]
        cv2.imwrite(f'{out}/sheet.jpg', cv2.cvtColor(np.concatenate(rows, 0), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        print('blinks at', [round(b / FPS, 2) for b in BLINKS]); sys.exit()
    with Pool(4) as p: p.map(work, [(out, i) for i in range(i0, i1)])
