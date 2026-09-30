"""0:00-0:33.2 on the key frames (assets/kv, painted by ChatGPT; visual masters).

Each KV stays one intact painted frame: no layer separation, no puppet motion. What moves is
the human world inside it (lights, traces, the falling light, the flame), the pose states
KV3b/KV4b are locked local variants, and the camera moves only to follow a trace or an eyeline,
or to change scale. Every shot hands an element to the next:

  0.00  BG0a globe (3D), its lights full        "Three"
  3.30  the rim flattens into the BG0b map (2D)   "two"
  4.50  the map compresses into one line of lights (1D) at the height of KV1's ledge   "one"
  5.62  the line opens into KV1; the frame resolves from unfinished to painted by 7.55   "Loading"
  8.45  KV2 over A's shoulder: the camera tilts up with the traces rising from the city
 10.24  human scale: the city below, windows lighting and going dark (people pass)
 11.98  KV3: an empty sky; city lights rise, hang frozen in the silence (13.40-14.45), settle
        into the constellation; A looks up (KV3b, 17.75) and the camera follows her eyeline up
 20.86  KV4: the cut returns downward to B looking at the city; her gaze grows heavier (KV4b)
 25.91  KV1 again: time has passed below
 27.75  KV5a: a falling light; 29.12 hard cut to KV5 at contact, the flame lights A
 30.93  the flame's screen position match-cuts to one light on the dark globe; it spreads into
        the network as the camera pulls back to cosmic scale (-> pre-chorus 33.2)
Usage: python3 kvfilm.py OUTDIR [t0 t1]
"""
import os, sys, json, numpy as np, cv2
from multiprocessing import Pool
from PIL import Image

W, H, FPS = 1280, 720, 30
HERE = os.path.dirname(os.path.abspath(__file__)); KVD = os.path.join(HERE, '..', 'assets', 'kv')
BEATS = np.array(json.load(open(f'{HERE}/../timing/p0_beatmap.json'))['beats_s'])
T_SIL0, T_SIL1 = 13.40, 14.45
SW, SH = 1536, 1024

def ss(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def tau(t): return t if t < T_SIL0 else (T_SIL0 if t < T_SIL1 else t - (T_SIL1 - T_SIL0))
def beat_pulse(s):
    b = BEATS[BEATS <= s]; return float(np.exp(-(s - b[-1]) * 6)) if len(b) else 0.0
def load(n): return np.array(Image.open(f'{KVD}/{n}.png').convert('RGB')).astype(np.float32) / 255
KV = {n: load(n) for n in ('BG0a', 'BG0b', 'KV1', 'KV2', 'KV3', 'KV3b', 'KV4', 'KV4b', 'KV5', 'KV5a')}

def split_lights(img, region=None, loose=False):
    """Warm human light -> (base without it, light layer). Warm = red well above blue, and bright."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    m = (r > 0.50) & (r - b > 0.16) & (img.mean(-1) > 0.40)
    if loose: m = (r - b > 0.05) & (img.mean(-1) > 0.20)              # every warm speck, for an empty sky
    if region is not None: m &= region
    m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8))
    base = cv2.inpaint((img * 255).astype(np.uint8), m * 255, 3, cv2.INPAINT_TELEA).astype(np.float32) / 255
    return base, np.clip(img - base, 0, 1), m.astype(np.float32)
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
B0A, L0A, M0A = split_lights(KV['BG0a'])
B1, L1, _ = split_lights(KV['KV1'])
B4, L4, _ = split_lights(KV['KV4'], xx < 1080)                     # the city only, not B's lit face
B3, L3, M3 = split_lights(KV['KV3'], yy < 560, loose=True)                     # the constellation (sky part only)
rng = np.random.default_rng(3)
PHASE = cv2.resize(rng.random((64, 96)).astype(np.float32), (SW, SH), interpolation=cv2.INTER_NEAREST)
SLOW = cv2.GaussianBlur(rng.random((SH, SW)).astype(np.float32), (0, 0), 18)
SLOW = (SLOW - SLOW.min()) / (SLOW.max() - SLOW.min())

def living(base, light, s, turnover=0.0):
    """City lights that flicker slightly; with turnover, some districts go dark while others light:
    people pass, the lights change hands."""
    g = 0.88 + 0.12 * np.sin(s * 2.1 + PHASE * 40)
    if turnover:
        th = 0.5 + 0.5 * np.sin(s * 0.9 + SLOW * 9)
        g = g * (0.35 + 0.65 * (th > 0.25 * turnover))
    return base + light * g[..., None]

def view(img, cx=SW / 2, cy=SH / 2, zoom=1.0):
    """Camera: output 1280x720 of the source, centred at (cx, cy); zoom 1 = the full 16:9 crop."""
    sc = W / SW * zoom
    M = np.float32([[sc, 0, W / 2 - cx * sc], [0, sc, H / 2 - cy * sc]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA if zoom <= 1 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT), M

def dot(fr, x, y, r, col, k=1.0):
    """A small warm light: painted, not a sparkle."""
    lay = np.zeros((H, W), np.float32)
    if -20 < x < W + 20 and -20 < y < H + 20: cv2.circle(lay, (int(x), int(y)), max(1, int(r)), 1.0, -1, cv2.LINE_AA)
    g = np.clip(cv2.GaussianBlur(lay, (0, 0), max(0.8, r * 0.6)) * 1.3 + cv2.GaussianBlur(lay, (0, 0), r * 3) * 0.5, 0, 1) * k
    return fr + g[..., None] * np.array(col) * (1 - fr)

WARM = (1.0, 0.72, 0.40)
LEDGE_Y = 840.0                                                     # KV1's ledge, source px

# ---------------------------------------------------------------- countdown
cols = np.array([0, 384, 768, 1152, 1535], float); tops = np.array([383, 296, 270, 313, 435], float)
ARC = np.polyval(np.polyfit(cols, tops, 2), np.arange(SW)).astype(np.float32) - 270   # how far the rim curves down

def countdown(t):
    s = t
    if t < 3.3:                                                     # 3D: the living globe, lights coming up on "Three"
        k = 0.35 + 0.65 * ss(0.9, 2.2, s)
        img = B0A + L0A * (k * (0.9 + 0.1 * np.sin(s * 2 + PHASE * 40)))[..., None]
        return view(img, SW / 2 + 30 * s, SH / 2, 1.0 + 0.02 * s)[0]
    if t < 4.5:                                                     # 3D -> 2D: the rim straightens, the world lies flat
        e = float(ss(3.3, 4.2, s))
        img = B0A + L0A * 0.95
        mx, my = xx, (yy + ARC[None, :] * e * (1 - yy / SH) * 1.8).astype(np.float32)
        flat = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        img = flat * (1 - ss(3.7, 4.3, s)) + KV['BG0b'] * ss(3.7, 4.3, s)
        return view(img, SW / 2 + 30 * 3.3, SH / 2, 1.066)[0]
    # 2D -> 1D: the map compresses toward the line at the height of KV1's ledge
    e = float(ss(4.5, 5.3, s)); h = max(0.004, 1 - e)
    fr, _ = view(KV['BG0b'], SW / 2 + 99, SH / 2, 1.066)
    ly = (LEDGE_Y - 80) * W / SW                                     # the ledge in the output frame
    M = np.float32([[1, 0, 0], [0, h, ly * (1 - h)]])
    fr = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_AREA, borderValue=(0.02, 0.025, 0.05))
    warm = np.clip((fr - 0.25) * 1.6, 0, 1) * (1 + 2.5 * e)           # the lights concentrate as the world thins
    return np.clip(fr * (1 - 0.6 * e) + warm * np.array(WARM) * e * 0.6, 0, 1)

# ---------------------------------------------------------------- traces for KV3
ys3, xs3 = np.nonzero(M3 > 0)
pick = rng.choice(len(xs3), 70, replace=False)
T_TGT = np.stack([xs3[pick], ys3[pick]], 1).astype(np.float32)       # where each trace settles as a star
T_SRC = np.stack([rng.uniform(250, 1300, 70), rng.uniform(760, 840, 70)], 1).astype(np.float32)  # city near the horizon
T_T0 = rng.uniform(12.0, 13.3, 70); T_DUR = rng.uniform(1.6, 2.6, 70)

def kv3(t, variant):
    s = tau(t)
    reveal = np.zeros((SH, SW), np.float32)
    pos = []
    for k in range(70):
        u = np.clip((s - T_T0[k]) / T_DUR[k], 0, 1)
        if u <= 0: continue
        uu = u * u * (3 - 2 * u)
        p = T_SRC[k] + (T_TGT[k] - T_SRC[k]) * uu + np.array([40 * np.sin(u * 3.1 + k), 0])
        if u < 1: pos.append(p)
        else: cv2.circle(reveal, (int(T_TGT[k][0]), int(T_TGT[k][1])), 70, 1.0, -1)
    reveal = np.maximum(cv2.GaussianBlur(reveal, (0, 0), 25), ss(15.6, 17.2, s))  # the whole sky completes
    src = KV[variant]
    if variant == 'KV3b':                                            # her look-up, a locked local variant
        k3 = float(ss(17.75, 17.86, t))
        diff = (np.abs(KV['KV3b'] - KV['KV3']).max(-1) > 0.02).astype(np.float32)
        dm = cv2.GaussianBlur(diff, (0, 0), 4)[..., None]
        src = KV['KV3'] * (1 - dm * k3) + KV['KV3b'] * dm * k3
    base = src - L3 * (1 - reveal)[..., None]                        # the sky stays empty until the traces arrive
    base = living(base, np.zeros_like(base), s)
    # camera: from 17.9 it follows her eyeline up into the sky
    lk = float(ss(17.9, 20.4, t))
    fr, M = view(base, SW / 2, SH / 2 - 240 * lk, 1.0 + 0.10 * lk)
    for p in pos:
        x, y = M @ np.array([p[0], p[1], 1.0])
        fr = dot(fr, x, y, 2.2, WARM, 0.9)
    return fr

# ---------------------------------------------------------------- shots
def frame_at(t):
    s = tau(t)
    if t < 5.62:
        fr = countdown(t)
    elif t < 8.452:                                                 # KV1 opens out of the line and resolves ("Loading")
        e = float(ss(5.62, 6.25, t))
        img = living(B1, L1, s)
        rough = cv2.GaussianBlur(img, (0, 0), 7)                      # not yet resolved: soft, colour not yet in
        rough = rough * 0.45 + rough.mean(-1, keepdims=True) * 0.55
        img = rough * (1 - ss(6.4, 7.55, t)) + img * ss(6.4, 7.55, t)
        fr, _ = view(img)
        ly = (LEDGE_Y - 80) * W / SW
        M = np.float32([[1, 0, 0], [0, max(0.004, e), ly * (1 - max(0.004, e))]])
        fr = cv2.warpAffine(fr, M, (W, H), borderValue=(0.02, 0.025, 0.05))
        fr = fr + 0.25 * np.exp(-(t - 5.62) * 10)                    # a brief lift on the hit, not a bloom
    elif t < 10.24:                                                 # KV2: follow the rising traces up
        u = float(ss(8.452, 10.24, t))
        img = living(*split_lights(KV['KV2'])[:2], s) if False else KV['KV2']
        fr, M = view(img, SW / 2 - 60 * u, SH / 2 - 150 * u, 1.0 + 0.08 * u)
        for k in range(9):                                          # a few lights still leaving the city
            ph = ((s - 8.45) * 0.45 + k / 9) % 1.0
            x0, y0 = 700 + 80 * np.sin(k * 2.3), 880
            x, y = M @ np.array([x0 + 220 * ph * np.sin(k), y0 - 780 * ph, 1.0])
            fr = dot(fr, x, y, 2.0, WARM, np.sin(np.pi * ph) * 0.9)
    elif t < 11.981:                                                # human scale: the city B will look at
        u = float(ss(10.24, 11.981, t))
        img = living(B4, L4, s, turnover=1.0)
        fr, _ = view(img, 285 + 20 * u, 805, 2.6)
    elif t < 20.863:                                                # KV3: city lights become the sky; A looks up
        fr = kv3(t, 'KV3b' if t >= 17.75 else 'KV3')
    elif t < 25.913:                                                # KV4: B returns her attention to people
        k4 = float(ss(21.12, 21.3, t))
        diff = cv2.GaussianBlur((np.abs(KV['KV4b'] - KV['KV4']).max(-1) > 0.02).astype(np.float32), (0, 0), 3)[..., None]
        src = KV['KV4'] * (1 - diff * k4) + KV['KV4b'] * diff * k4
        img = src - L4 + living(np.zeros_like(B4), L4, s, turnover=ss(21.5, 24, s))
        fr, _ = view(img)
    elif t < 27.748:                                                # KV1 again: time has passed below
        fr, _ = view(living(B1, L1, s, turnover=0.8))
    elif t < 29.118:                                                # KV5a: a light falls toward her open palm
        fr, M = view(KV['KV5a'])
        u = np.clip((t - 27.95) / (29.118 - 27.95), 0, 1)
        x, y = M @ np.array([657 + 30 * np.sin(u * 4), -40 + (500 + 40) * u ** 1.6, 1.0])
        fr = dot(fr, x, y, 2.6, WARM, 1.0)
    elif t < 30.929:                                                # KV5: contact, the first fire; it lights her
        fl = 0.86 + 0.14 * np.sin(s * 21) * np.sin(s * 7.7) + 0.08 * beat_pulse(s)
        img = KV['KV5a'] + (KV['KV5'] - KV['KV5a']) * fl
        fr, _ = view(img)
    else:                                                           # the first fire becomes the network
        u = float(ss(30.929, 33.2, t))
        o = np.array([700.0, 520.0])                                 # the first light on the globe
        rad = 40 + 1500 * ss(31.1, 33.2, t) ** 1.5
        grow = np.clip((rad - np.hypot(xx - o[0], yy - o[1])) / 120, 0, 1)
        img = B0A * 0.8 + L0A * grow[..., None] * (0.9 + 0.1 * np.sin(s * 2 + PHASE * 40))[..., None]
        fx, fy = 657 * W / SW, (521 - 80) * W / SW                  # where the flame was on screen
        zoom = 2.6 - 1.6 * u
        cx = o[0] - (fx - W / 2) / (W / SW * zoom); cy = o[1] - (fy - H / 2) / (W / SW * zoom)
        fr, M = view(img, cx, cy, zoom)
        x, y = M @ np.array([o[0], o[1], 1.0])
        fr = dot(fr, x, y, 3.0, WARM, 1.0 - 0.5 * u)
    if T_SIL0 <= t < T_SIL1:                                         # the silence: the world holds its breath
        g = fr.mean(-1, keepdims=True); fr = fr * 0.75 + g * 0.25
    fr = fr + np.random.default_rng(int(round(s * FPS))).normal(0, 0.007, (H, W, 1))
    return (np.clip(fr, 0, 1) * 255).astype(np.uint8)

def work(a):
    out, i = a
    cv2.imwrite(f'{out}/f{i:05d}.png', cv2.cvtColor(frame_at(i / FPS), cv2.COLOR_RGB2BGR))

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    t0, t1 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (0.0, 33.2)
    with Pool(4) as p: p.map(work, [(out, i) for i in range(int(round(t0 * FPS)), int(round(t1 * FPS)))])
