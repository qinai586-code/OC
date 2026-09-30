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

# ---------------------------------------------------------------- layers: paper, light, particles
BARS = BEATS[BEATS >= 7.5][::4]                                 # bar downbeats from the 7.55 downbeat
def bar_pulse(s):
    b = BARS[BARS <= s]; return float(np.exp(-(s - b[-1]) * 6)) if len(b) else 0.0
def eio(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return np.where(x < .5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)

# paper larger than the frame (for parallax) with a faint pencil grid and loose sketch lines
BW, BH = int(W * 1.3), int(H * 1.3)
g1 = cv2.GaussianBlur(rng.random((BH, BW)).astype(np.float32), (0, 0), 1.0)
g2 = cv2.GaussianBlur(rng.random((BH, BW)).astype(np.float32), (0, 0), 22)
BGTEX = PAPER * (0.965 + 0.05 * g1[..., None] + 0.07 * (g2[..., None] - 0.5))
sk = np.zeros((BH, BW), np.float32)
sk[:, ::96] = 0.5; sk[::96, :] = 0.5
for _ in range(40):
    c = rng.uniform([0, 0], [BW, BH]); r = rng.uniform(60, 420)
    cv2.ellipse(sk, (int(c[0]), int(c[1])), (int(r), int(r * rng.uniform(0.3, 1))), rng.uniform(0, 180), 0, rng.uniform(40, 200), 1.0, 1, cv2.LINE_AA)
BGTEX -= cv2.GaussianBlur(sk, (0, 0), 0.7)[..., None] * 0.045

# the ember swarm: three depths (behind her, around her, past the lens)
NP = 340
p_tier = rng.choice(3, NP, p=[0.35, 0.5, 0.15]); p_depth = np.array([0.55, 1.0, 1.8])[p_tier]
p_x0 = rng.uniform(-100, W + 100, NP); p_y0 = rng.uniform(0, H + 200, NP)
p_sp = rng.uniform(18, 55, NP) * p_depth; p_ph = rng.uniform(0, 2 * np.pi, NP); p_ph2 = rng.uniform(0, 2 * np.pi, NP)
p_col = np.where(rng.random(NP)[:, None] < 0.2, JADE, EMBER)
p_w = rng.uniform(0.5, 1.0, NP) * np.array([2.2, 4.0, 26.0])[p_tier]
STAR_OF = np.where(p_tier == 1, np.arange(NP) % 7, -1)          # the mid embers become the constellation

def swarm(s, t, cam, face):
    """Positions (x, y) of every ember at story time s, seen through camera offset cam."""
    y = (p_y0 - p_sp * s) % (H + 200) - 100
    x = p_x0 + 18 * np.sin(s * 0.6 + p_ph) + 26 * np.sin(y * 0.011 + s * 0.8 + p_ph2)     # sine flow
    x = x + cam[0] * p_depth; y = y + cam[1] * p_depth
    if t >= T_SIL1:                                                    # re-entry burst, then the stars
        u = t - T_SIL1
        dx, dy = x - face[0], y - face[1]; r = np.hypot(dx, dy) + 1
        k = 140 * (1 - np.exp(-u * 7)) * np.exp(-u * 1.6)
        x, y = x + dx / r * k, y + dy / r * k
        e = eio(0.5, 1.9, u - (np.arange(NP) % 11) * 0.03)
        on = STAR_OF >= 0
        sx = np.array([STARS[j][0] * W for j in STAR_OF[on]]) + cam[0] + 7 * np.sin(p_ph[on] * 5)
        sy = np.array([STARS[j][1] * H for j in STAR_OF[on]]) + cam[1] + 7 * np.cos(p_ph[on] * 5)
        x[on] = x[on] + (sx - x[on]) * e[on]; y[on] = y[on] + (sy - y[on]) * e[on]
    return x, y

def splat_layer(x, y, w, col, sig, shape=(H, W)):
    lay = np.zeros(shape + (3,), np.float32)
    ok = (x >= 0) & (x < shape[1] - 1) & (y >= 0) & (y < shape[0] - 1)
    np.add.at(lay, (y[ok].astype(int), x[ok].astype(int)), col[ok] * w[ok, None])
    return cv2.GaussianBlur(lay, (0, 0), sig) if sig > 0 else lay

def god_rays(s, origin, strength):
    """Light falling from where she looks: a slowly moving occluder pattern, zoom-blurred from the source."""
    qw, qh = W // 4, H // 4
    ph = int(s * 6) % 400
    occ = (np.sin(np.linspace(0, 40, qw)[None, :] + ph * 0.05 + np.linspace(0, 3, qh)[:, None]) > 0.35).astype(np.float32)
    occ *= cv2.resize(g2[:qh * 2:2, :qw * 2:2], (qw, qh)) > 0.5
    ox, oy = origin[0] / 4, origin[1] / 4
    acc = np.zeros((qh, qw), np.float32)
    for k in range(14):
        sc = 1 - k * 0.045
        M = np.float32([[sc, 0, ox * (1 - sc)], [0, sc, oy * (1 - sc)]])
        acc += cv2.warpAffine(occ, M, (qw, qh))
    acc = cv2.GaussianBlur(acc / 14, (0, 0), 2)
    fall = np.exp(-np.hypot(np.arange(qw)[None, :] - ox, np.arange(qh)[:, None] - oy) / (qw * 0.9))
    return cv2.resize(acc * fall * strength, (W, H))[..., None] * WARM

# ---------------------------------------------------------------- shots
STARS = [(0.58, 0.14), (0.66, 0.24), (0.74, 0.17), (0.82, 0.29), (0.78, 0.42), (0.90, 0.36), (0.93, 0.20)]
def shot(t):
    """Base framing plus a camera drift (px) that every layer follows by its depth."""
    if t < T_SIL0:   # S1: push in while the camera slides left under her gaze
        u = (t - T0) / (T_SIL0 - T0)
        return dict(kind='A', scale=1.22 + 0.10 * u, face=(0.54 * W, 0.55 * H), cam=(-70 * u, -12 * u), light=(0.56, 0.45))
    if t < T_SIL1:   # S2: the silence, bullet-time drift round B
        u = (t - T_SIL0) / (T_SIL1 - T_SIL0)
        return dict(kind='B3', scale=0.62 + 0.03 * u, face=(0.47 * W, 0.46 * H), cam=(60 * u, -8 * u), light=(0.47, 0.40))
    u = (t - T_SIL1) / (T1 - T_SIL1)   # S3: wider, face low, the sky above; crane up
    return dict(kind='A', scale=1.08 - 0.06 * u, face=(0.40 * W, 0.64 * H), cam=(-20 * u, 40 * u), light=(0.45, 0.55))

FACE_A = (395.0, 330.0)          # plate coords of A's cheek, the framing anchor
FACE_B3 = (560.0, 520.0)         # B3 pose coords of her cheek

def place(rgba, anchor, target, scale, angle=0.0, pivot=None):
    pv = pivot or anchor
    M = cv2.getRotationMatrix2D(pv, angle, scale)
    p = M @ np.array([anchor[0], anchor[1], 1.0])
    M[:, 2] += np.array(target) - p
    return cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))

def frame_at(i):
    t = i / FPS; s = tau(t); sh = shot(t); frozen = T_SIL0 <= t < T_SIL1
    cam = np.array(sh['cam']) * (1.0)
    kick = 1 + 0.008 * bar_pulse(s)                                 # a small push on each bar downbeat
    face = (sh['face'][0] + cam[0], sh['face'][1] + cam[1])
    # 1 paper, parallax 0.35
    ox, oy = int((BW - W) / 2 - cam[0] * 0.35), int((BH - H) / 2 - cam[1] * 0.35)
    bg = BGTEX[oy:oy + H, ox:ox + W]
    lx, ly = sh['light']
    pool = np.exp(-(((xx - lx * W - cam[0]) / (0.55 * W)) ** 2 + ((yy - ly * H - cam[1]) / (0.60 * H)) ** 2))
    bg = bg * np.array([1.03, 0.95, 0.84]) * (0.20 + 0.52 * pool[..., None]) + (pool * 0.06 * (1 + 0.8 * beat_pulse(s)))[..., None] * WARM   # a night page
    # 2 embers behind her
    px_, py_ = swarm(s, t, cam, face)
    back = p_tier == 0
    L = splat_layer(px_[back], py_[back], p_w[back] * (1 + 0.8 * beat_pulse(s)), p_col[back], 1.0)
    # 3 the character
    b = np.sin(2 * np.pi * s / 3.7)
    if sh['kind'] == 'A':
        m, e = mouth_at(i), eye_at(i)
        plate = PLATES[(m, e)]
        wind = 0.75 + 0.25 * np.sin(2 * np.pi * s / 7.1) + 0.5 * bar_pulse(s)
        dx = 2.6 * wind * np.sin(2 * np.pi * s / 2.9 - hy / 140) * HAIR_W
        dy = 0.7 * np.sin(2 * np.pi * s / 2.9 + 1.3 - hy / 140) * HAIR_W
        plate = cv2.remap(plate, (hx - dx).astype(np.float32), (hy - dy).astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        ang = 0.5 * np.sin(2 * np.pi * s / 5.3) + 1.6 * sing_at(t) + 0.6 * beat_pulse(s) * (m > 0)   # nods into the beat when singing
        fig = place(plate, FACE_A, (face[0], face[1] - 2.0 * b), sh['scale'] * kick * (1 + 0.003 * b), ang, NECK_A)
        light_dir = +1
    else:
        fig = place(B3F, FACE_B3, face, sh['scale'] * kick)
        light_dir = -1
    a = fig[..., 3:]
    edge = np.clip(a - cv2.erode(a, np.ones((9, 9), np.uint8))[..., None], 0, 1)
    wrap = cv2.GaussianBlur(bg, (0, 0), 10) * edge * 0.22
    # rim light on the edge that faces the light
    sh_a = np.roll(a[..., 0], -6 * light_dir, axis=1)
    rim = cv2.GaussianBlur(np.clip(a[..., 0] - sh_a, 0, 1), (0, 0), 1.5)[..., None]
    col = fig[..., :3] * (0.93 + 0.07 * pool[..., None]) + wrap + rim * 0.45 * WARM * (1 + 0.5 * beat_pulse(s))
    frame = screen(bg, 1 - np.exp(-L * 1.2)) * (1 - a) + col * a
    # 4 light falling from where she looks
    org = (W * 1.02 + cam[0] * 0.2, -0.08 * H) if light_dir > 0 else (-0.02 * W, -0.08 * H)
    frame = screen(frame, god_rays(s, org, 0.55 * (0.85 + 0.3 * beat_pulse(s))))
    # 5 embers around her (streaked) and past the lens (big bokeh)
    mid = p_tier == 1; fr = p_tier == 2
    wm = p_w[mid] * (1 + 0.8 * beat_pulse(s)) * (0.75 + 0.25 * np.sin(s * 6 + p_ph[mid] * 3))
    Lm = np.zeros((H, W, 3), np.float32)
    for k in range(4):                                             # motion streak: 4 samples over 1/15 s
        qx, qy = swarm(max(0, s - 0.022 * k) if not frozen else s, t, cam, face)
        Lm += splat_layer(qx[mid], qy[mid], wm * (1 - 0.2 * k) / 2.8, p_col[mid], 0)
    if frozen:                                                     # time as a direction: each ember's last second
        fp = np.clip((t - T_SIL0) / 0.35, 0, 1)
        for k in range(1, 28):
            qx, qy = swarm(s - k * 0.04 * fp, T_SIL0, cam, face)
            Lm += splat_layer(qx[mid], qy[mid], wm * 0.12 * (1 - k / 28), p_col[mid], 0)
    Lm = cv2.GaussianBlur(Lm, (0, 0), 1.1) * 1.6 + cv2.GaussianBlur(Lm, (0, 0), 5) * 1.2
    Lf = splat_layer(px_[fr], py_[fr], p_w[fr] * (1 + 0.6 * beat_pulse(s)), p_col[fr], 11)
    frame = screen(frame, 1 - np.exp(-(Lm + Lf) * 1.2))
    # 6 constellation lines, once the embers have arrived
    if t >= T_SIL1:
        lay = np.zeros((H, W), np.float32); u = t - T_SIL1
        pts = [(int(x_ * W + cam[0]), int(y_ * H + cam[1])) for x_, y_ in STARS]
        for j in range(len(pts) - 1):
            v = float(np.clip((u - 1.8 - 0.3 * j) / 0.35, 0, 1))
            if v > 0:
                p0 = np.array(pts[j]); p1 = p0 + (np.array(pts[j + 1]) - p0) * v
                cv2.line(lay, tuple(int(c) for c in p0), tuple(int(c) for c in p1), 0.8, 2, cv2.LINE_AA)
        g = np.clip(cv2.GaussianBlur(lay, (0, 0), 1.0) + cv2.GaussianBlur(lay, (0, 0), 6) * 1.2, 0, 1)[..., None]
        frame = frame * (1 - 0.7 * g) + np.array([0.72, 0.52, 0.22]) * 0.7 * g
    # 7 bloom, silence grade, re-entry flash, vignette, grain
    hi = cv2.resize(np.clip(frame - 0.82, 0, None), (W // 2, H // 2))
    frame = frame + cv2.resize(cv2.GaussianBlur(hi, (0, 0), 8), (W, H)) * 0.8
    if frozen:
        g_ = frame.mean(-1, keepdims=True); frame = frame * 0.6 + g_ * np.array([0.93, 0.98, 1.06]) * 0.4
    if t >= T_SIL1: frame = frame + 0.35 * np.exp(-(t - T_SIL1) * 9) * WARM
    frame = frame * VIGN
    frame = frame + np.random.default_rng(int(round(s * FPS))).normal(0, 0.010, (H, W, 1))
    return (np.clip(frame, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)

def screen(a, b): return a + b * (1 - a)

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
