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
T0, T_SIL0, T_SIL1, T1 = 5.62, 13.40, 14.45, 21.0      # from the bass hit (0-5.62 is opening.py's countdown)
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
NECK_A = (300.0, 470.0)

# ---------------------------------------------------------------- M1: A looks up (ChatGPT's pilot, 4 poses)
M1DIR = os.path.join(HERE, '..', 'assets', 'motion', 'M1')
M1Q = json.load(open(f'{M1DIR}/QC.json')); PIV = tuple(M1Q['pivot_xy'])
def _pad(f):                                       # 512x768 cell -> 512x1024 panel (rows below are F0's)
    im = np.array(faces.Image.open(f).convert('RGB')).astype(np.float32) / 255
    return np.concatenate([im, HA.mouth[0][768:]], 0)
M1F = [_pad(f'{M1DIR}/F{k}.png') for k in range(4)]
def _rot(im, deg):
    return cv2.warpAffine(im, cv2.getRotationMatrix2D(PIV, deg, 1.0), (512, 1024), flags=cv2.INTER_LINEAR, borderValue=(1, 1, 1))
_err = {sg: np.abs(_rot(M1F[0], sg * 9.0)[:540] - M1F[3][:540]).mean() for sg in (1, -1)}
SGN = min(_err, key=_err.get)                      # which way F3 was rotated
def _mask(a, b):
    d = (np.abs(a - b).max(-1) > 0.03).astype(np.uint8)
    d = cv2.dilate(cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)), np.ones((7, 7), np.uint8)).astype(np.float32)
    return cv2.GaussianBlur(d, (0, 0), 3)[..., None]
def _m1_plate(k, m, e):
    """Pose k (0-3) with mouth m and eyes e. On F3 the mouth/eye patches are the neutral ones turned 9 deg,
    the same way F3 itself was built; the in-between poses are only shown in a breath (mouth closed)."""
    rgb = M1F[k].copy()
    if k == 3:
        def raw(mm, ee):                           # the drawings themselves, not the matte-processed plate
            r = HA.mouth[mm].copy()
            if ee: r = r * (1 - HA.eye_mask[ee]) + HA.eye[ee] * HA.eye_mask[ee]
            return r
        base = raw(0, 0)
        for (mm, ee) in ((m, 0), (0, e)):
            if (mm, ee) == (0, 0): continue
            src = raw(mm, ee)
            msk = cv2.warpAffine(_mask(src, base), cv2.getRotationMatrix2D(PIV, SGN * 9.0, 1.0), (512, 1024))[..., None]
            rgb = rgb * (1 - msk) + _rot(src, SGN * 9.0) * msk
    return fade_bottom(faces.cutout(rgb), 440, 560)
M1_T = [17.75, 17.92, 18.02]                       # F1 (eyes lead) / F2 / F3 lands, inside the 17.63-18.17 breath
M1_DEG = [0.0, 1.5, 5.0, 9.0]
_M1C = {}
def m1_pose(t):
    return 0 if t < M1_T[0] else (1 if t < M1_T[1] else (2 if t < M1_T[2] else 3))
def m1_plate(k, m, e):
    key = (k, m if k == 3 else 0, e if k == 3 else 0)
    if key not in _M1C: _M1C[key] = _m1_plate(*key)
    return _M1C[key]
def m1_hair(s):                                    # the hair lags each head change and settles
    out = 0.0
    for j, tk in enumerate(M1_T):
        if s >= tk: out += (M1_DEG[j + 1] - M1_DEG[j]) * 0.9 * np.exp(-(s - tk) / 0.28) * np.sin(2 * np.pi * (s - tk) / 0.5)
    return out                                         # plate coords: rotation pivot
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
STAR_R = [4, 2, 3, 5, 2, 3, 2]
STARS = [(0.58, 0.14), (0.66, 0.24), (0.74, 0.17), (0.82, 0.29), (0.78, 0.42), (0.90, 0.36), (0.93, 0.20)]
def _e(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
# cut points on tracked beats (phrase ends), the silence and the re-entry
C_INS, C_TWO, C_BCUT = 10.693, 11.981, 19.528
import edge as edgeshots
EDGE_WIN = [(5.62, 10.24), (11.981, T_SIL0), (T_SIL1, 17.705), (19.528, 21.0)]   # edge-of-the-world shots (edge.py)
def shot(t):
    """Framing per shot: the figures, a camera drift (px) every layer follows by its depth,
    the light pool, and where the light rays come from. Pushes ease in and out.
    Edge, over-the-shoulder, wide and sky shots come from edge.py; the close-ups are reactions."""
    if any(a <= t < b for a, b in EDGE_WIN): return dict(scene='edge')
    if t < C_TWO:    # A reacts: medium close-up, the traces caught in her eye
        u = _e((t - 10.24) / (C_TWO - 10.24))
        return dict(figs=[('A', 1.22 + 0.10 * u, (0.54 * W, 0.55 * H))], cam=(-40 * u, -8 * u), light=(0.56, 0.45), rays='right', glint=True)
    if t < 0:        # (retired: S1a medium close-up and S1b eye insert are replaced by the reaction shot)
        u = _e((t - T0) / (C_INS - T0))
        return dict(figs=[('A', 1.20 + 0.10 * u, (0.54 * W, 0.55 * H))], cam=(-50 * u, -10 * u), light=(0.56, 0.45), rays='right')
    if t < C_TWO:    # S1b: tight insert at eye level, a quicker push
        u = _e((t - C_INS) / (C_TWO - C_INS))
        sc = 3.3 + 0.2 * u                          # her eye, an ember reflected in it (new information, not a re-crop)
        return dict(figs=[('A', sc, (0.48 * W + 31 * sc, 0.44 * H + 35 * sc))], cam=(-24 * u, 0), light=(0.50, 0.42), rays='right', glint=True)
    if t < T_SIL0:   # S1c: both witnesses, facing each other, before the silence
        u = _e((t - C_TWO) / (T_SIL0 - C_TWO))
        return dict(figs=[('A', 1.30, (0.17 * W, 0.66 * H), dict(blur=3.5, dim=0.70)), ('B', 0.86 + 0.03 * u, (0.63 * W, 0.56 * H))],
                    cam=(-18 * u, -8 * u), light=(0.60, 0.45), rays='top')   # A soft in the foreground, B listening, in focus
    if t < T_SIL1:   # S2: the silence, bullet-time drift round B
        u = (t - T_SIL0) / (T_SIL1 - T_SIL0)
        return dict(figs=[('B3', 0.62 + 0.03 * u, (0.47 * W, 0.46 * H))], cam=(60 * u, -8 * u), light=(0.47, 0.40), rays='left')
    if t < C_BCUT:   # S3: A under the formed sky; the camera tilts up with her look (M1)
        u = _e((t - 17.705) / (C_BCUT - 17.705)); lk = _e((t - 17.66) / 0.9)
        return dict(figs=[('A', 1.06 - 0.04 * u + 0.04 * lk, (0.40 * W, 0.64 * H))], cam=(-20 * u, 30 * u + 28 * lk), light=(0.45, 0.55), rays='right')
    u = _e((t - C_BCUT) / (T1 - C_BCUT))   # S3b: B listens (A sings on, off screen) - her lines are next
    return dict(figs=[('B', 1.15 + 0.05 * u, (0.56 * W, 0.56 * H))], cam=(25 * u, 0), light=(0.55, 0.45), rays='left')

HB = faces.Head('B')
PLATES_B = {e: fade_bottom(HB.plate(0, e), 440, 560) for e in range(3)}
FACE_B = (158.0, 304.0)          # plate coords of B's cheek (eye + mirrored offset of A's anchor)
NECK_B = (240.0, 470.0)
HAIR_B = (ss(300, 560, hy) * ss(220, 400, hx)).astype(np.float32)   # B faces left: back hair on the right
B_BLINKS = [int(12.55 * FPS), int(20.15 * FPS)]
def b_eye(i):
    for b0 in B_BLINKS:
        if b0 <= i < b0 + 4: return (1, 2, 2, 1)[i - b0]
    return 0

FACE_A = (395.0, 330.0)          # plate coords of A's cheek, the framing anchor
FACE_B3 = (560.0, 520.0)         # B3 pose coords of her cheek

def place(rgba, anchor, target, scale, angle=0.0, pivot=None):
    pv = pivot or anchor
    M = cv2.getRotationMatrix2D(pv, angle, scale)
    p = M @ np.array([anchor[0], anchor[1], 1.0])
    M[:, 2] += np.array(target) - p
    LAST_M[0] = M
    return cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
LAST_M = [None]
IRIS_A = (364.0, 295.0)          # plate coords: where a reflection would sit in A's iris

def frame_at(i):
    t = i / FPS; s = tau(t); sh = shot(t); frozen = T_SIL0 <= t < T_SIL1
    if sh.get("scene") == "edge": return edgeshots.render(i, t, s)
    cam = np.array(sh['cam']) * (1.0)
    kick = 1 + 0.008 * bar_pulse(s)                                 # a small push on each bar downbeat
    face = (sh['figs'][0][2][0] + cam[0], sh['figs'][0][2][1] + cam[1])
    # 1 paper, parallax 0.35
    ox, oy = int((BW - W) / 2 - cam[0] * 0.35), int((BH - H) / 2 - cam[1] * 0.35)
    bg = BGTEX[oy:oy + H, ox:ox + W]
    lx, ly = sh['light']
    pool = np.exp(-(((xx - lx * W - cam[0]) / (0.55 * W)) ** 2 + ((yy - ly * H - cam[1]) / (0.60 * H)) ** 2))
    # the same night as the edge shots: dark paper under the sky, lit warmly from the human world below
    up = np.exp(-(H - yy) / (0.38 * H))[..., None]
    bg = bg * np.array([0.30, 0.31, 0.42]) * (0.30 + 0.45 * pool[..., None]) + up * 0.16 * EMBER * (1 + 0.5 * beat_pulse(s))
    # 2 embers behind her
    px_, py_ = swarm(s, t, cam, face)
    back = p_tier == 0
    L = splat_layer(px_[back], py_[back], p_w[back] * (1 + 0.8 * beat_pulse(s)), p_col[back], 1.0)
    # 3 the characters
    b = np.sin(2 * np.pi * s / 3.7)
    frame = screen(bg, 1 - np.exp(-L * 1.2))
    for fdef in sh['figs']:
        kind, scale, fpos = fdef[:3]; opt = fdef[3] if len(fdef) > 3 else {}
        fx, fy = fpos[0] + cam[0], fpos[1] + cam[1]
        wind = 0.75 + 0.25 * np.sin(2 * np.pi * s / 7.1) + 0.5 * bar_pulse(s)
        if kind == 'A':
            m, e = mouth_at(i), eye_at(i)
            k1 = m1_pose(t) if t >= T_SIL1 else 0
            plate = PLATES[(m, e)] if k1 == 0 else m1_plate(k1, m, e)
            dx = (2.6 * wind * np.sin(2 * np.pi * s / 2.9 - hy / 140) + m1_hair(t)) * HAIR_W
            dy = 0.7 * np.sin(2 * np.pi * s / 2.9 + 1.3 - hy / 140) * HAIR_W
            plate = cv2.remap(plate, (hx - dx).astype(np.float32), (hy - dy).astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
            ang = 0.5 * np.sin(2 * np.pi * s / 5.3) + 1.6 * sing_at(t) + 0.6 * beat_pulse(s) * (m > 0)
            fig = place(plate, FACE_A, (fx, fy - 2.0 * b), scale * kick * (1 + 0.003 * b), ang, NECK_A)
            rdir = +1
        elif kind == 'B':
            plate = PLATES_B[b_eye(i)]
            dx = -2.4 * wind * np.sin(2 * np.pi * s / 3.3 + 1.7 - hy / 140) * HAIR_B
            plate = cv2.remap(plate, (hx - dx).astype(np.float32), hy, cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
            bb = np.sin(2 * np.pi * s / 4.2 + 1.7)
            ang = -0.5 * np.sin(2 * np.pi * s / 6.1 + 1.0)
            fig = place(plate, FACE_B, (fx, fy - 2.0 * bb), scale * kick * (1 + 0.003 * bb), ang, NECK_B)
            rdir = -1
        else:
            fig = place(B3F, FACE_B3, (fx, fy), scale * kick)
            rdir = -1
        if opt.get('blur'):                                            # depth of field: premultiplied blur
            pm = np.dstack([fig[..., :3] * fig[..., 3:], fig[..., 3:]])
            pm = cv2.GaussianBlur(pm, (0, 0), opt['blur'])
            fig = np.dstack([pm[..., :3] / np.maximum(pm[..., 3:], 1e-3), pm[..., 3:]])
        a = fig[..., 3:]
        edge = np.clip(a - cv2.erode(a, np.ones((9, 9), np.uint8))[..., None], 0, 1)
        wrap = cv2.GaussianBlur(bg, (0, 0), 10) * edge * 0.22
        sh_a = np.roll(a[..., 0], -6 * rdir, axis=1)                 # rim light on the edge facing the light
        rim = cv2.GaussianBlur(np.clip(a[..., 0] - sh_a, 0, 1), (0, 0), 1.5)[..., None]
        col = fig[..., :3] * (0.93 + 0.07 * pool[..., None]) + wrap + rim * 0.45 * WARM * (1 + 0.5 * beat_pulse(s))
        col = col * opt.get('dim', 1.0)
        frame = frame * (1 - a) + col * a
        if sh.get('glint') and kind == 'A' and eye_at(i) < 2:        # an ember caught in her iris
            gx, gy = LAST_M[0] @ np.array([IRIS_A[0], IRIS_A[1], 1.0])
            gl = np.zeros((H, W), np.float32)
            cv2.circle(gl, (int(gx), int(gy)), max(2, int(1.5 * scale)), 1.0, -1, cv2.LINE_AA)
            g = cv2.GaussianBlur(gl, (0, 0), 0.5 * scale) * 1.8 + cv2.GaussianBlur(gl, (0, 0), 3 * scale) * 1.2
            frame = screen(frame, np.clip(g, 0, 1)[..., None] * EMBER * (0.65 + 0.35 * beat_pulse(s)))
    light_dir = {'right': 1, 'left': -1, 'top': 0}[sh['rays']]
    # 4 light falling from where she looks
    org = {1: (W * 1.02 + cam[0] * 0.2, -0.08 * H), -1: (-0.02 * W, -0.08 * H), 0: (0.5 * W, -0.12 * H)}[light_dir]
    frame = screen(frame, god_rays(s, org, 0.28 * (0.85 + 0.3 * beat_pulse(s))))
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
    # 6 constellation: thin lines once the embers have arrived; stars of different sizes that twinkle
    if t >= T_SIL1 and sh['figs'][0][0] == 'A':                   # the sky she looks into (A's shots only)
        lay = np.zeros((H, W), np.float32); u = t - T_SIL1
        pts = [(int(x_ * W + cam[0]), int(y_ * H + cam[1])) for x_, y_ in STARS]
        for j in range(len(pts) - 1):
            v = float(np.clip((u - 1.8 - 0.3 * j) / 0.35, 0, 1))
            if v > 0:
                p0 = np.array(pts[j]); p1 = p0 + (np.array(pts[j + 1]) - p0) * v
                cv2.line(lay, tuple(int(c) for c in p0), tuple(int(c) for c in p1), 0.42, 1, cv2.LINE_AA)
        for j, pt in enumerate(pts):
            lit = float(np.clip((u - 1.6 - 0.2 * j) / 0.4, 0, 1)) * (0.8 + 0.2 * np.sin(s * (2.3 + j * 0.7) + j))
            r = STAR_R[j]
            cv2.circle(lay, pt, r, lit, -1, cv2.LINE_AA)
            if r >= 4 and lit > 0:                                    # four-point flare on the brightest
                L_ = int(4 * r * lit)
                cv2.line(lay, (pt[0] - L_, pt[1]), (pt[0] + L_, pt[1]), 0.3 * lit, 1, cv2.LINE_AA)
                cv2.line(lay, (pt[0], pt[1] - L_), (pt[0], pt[1] + L_), 0.3 * lit, 1, cv2.LINE_AA)
        g = np.clip(cv2.GaussianBlur(lay, (0, 0), 0.8) + cv2.GaussianBlur(lay, (0, 0), 5) * 1.3, 0, 1)[..., None]
        frame = screen(frame, g * np.array([1.0, 0.80, 0.45]) * 0.9)
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
