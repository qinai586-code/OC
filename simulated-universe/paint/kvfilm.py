"""The full film, 0:00-3:33.4, on the key frames (assets/kv, painted by ChatGPT: the visual masters).

Each KV stays one intact painted frame: no cut-outs, no puppet motion. What moves is the human world
inside it (lights, traces, windows, the flame), A's look-up (KV3b, her head only), the paper transition
(paint -> flat wash -> pencil -> bare paper, the human lights surviving as ochre marks: a thing can lose
its body without losing what it left behind), and a camera that moves only to follow a trace or an
eyeline, or to change scale. Every view is clamped inside the painting, so no frame edge can show.
KV4b and KV5a are not used: KV4b's edit leaves a seam in B's hair, KV5a has a smear where B's hands
were. The pre-contact state is KV5 with only the flame inpainted.

  0:00 globe (3D) -> map (2D) -> a line (1D) at KV1's ledge   "Three, two, one"
  0:05.6 the line opens into KV1 as a pencil drawing; it paints in from the girls outward  "Loading"
  0:08.5 KV2 traces rise; 0:10.2 the city (people pass); 0:12 KV3: city lights become the sky, freeze
         in the silence, settle; A looks up and the camera follows her eyeline
  0:20.9 KV4 B watches the city; 0:25.9 KV1, time has passed; 0:27.7 a light falls; 0:29.1 first fire
  0:30.9 the flame match-cuts to one light on the globe; it spreads into the network
  0:33.2 pre-chorus: the network holds its breath; 0:38.4 KV1, the lights count down, edges inward
  0:44.1 chorus 1: KV3b, the lights return; the speed of light: traces rise and stop at the frame's edge
  0:54.9 the Planck scale: push into one window until the painting runs out; 0:58.6 look away (A looks
         up, the city keeps changing); 1:01.8 the city alone, still running; 1:05 KV1, unanswered
  1:11.2 the stop: everything holds but one rising trace, which becomes the signals
  1:13 verse 2: signals leave the map and nothing answers; 1:18.4 KV2 windows go dark in a countdown
  1:26.5 a sheet, a cold hairline, descends onto the globe; 1:33.7 it touches the rim and everything
         behind it falls flat into a pencil drawing on paper, the cities left as ochre marks
  1:37.8 B still looking; 1:39.9 the flat comes near KV2; 1:45.2 we follow the windows up to its edge
  1:50.6 chorus 2: along the constellation, past the last star; 1:57 the map as a console of keys;
         2:01.6 A's empty hand; 2:04.9 KV1 unfinished at the edges
  2:08.6 bridge: the Earth, no gods; the empty sky A looks at; the city pressing its own keys; travellers
         cross the map and their paths accumulate; 2:24.6 B: not them, and not I
  2:26.4 the break: a street, a city, the network of paths, the Earth, one hit each; 2:40.1 the breath
  2:41.4 final chorus: the constellation comes down into the city; 2:52 KV2, every traveller;
         3:02 the lights go out one by one and B watches
  3:12.5 "we'll be paper": KV1 un-paints to pencil, the girls last, the lights stay as ochre
  3:18.9 the loudest bar: the world repaints outward from its lights, pulse by pulse ("a return")
  3:23.4 A and B together by the first fire; 3:27.2 the chain of lights, one per beat, back to the globe
  3:31 the globe returns to paper until one warm light is left; it blinks, still loading; black at 3:32.7
Usage: python3 kvfilm.py OUTDIR [t0 t1]
"""
import os, sys, json, bisect, numpy as np, cv2
import space
from multiprocessing import Pool
from PIL import Image

W, H, FPS = 1280, 720, 30
SW, SH = 1536, 1024
T_END, T_BLACK = 213.4, 212.7
HERE = os.path.dirname(os.path.abspath(__file__)); KVD = os.path.join(HERE, '..', 'assets', 'kv')
_B = np.array(json.load(open(f'{HERE}/../timing/p0_beatmap.json'))['beats_s'])
BEATS = np.concatenate([_B, _B[-1] + 0.452 * np.arange(1, 14)])  # the tracker stops at 3:27.2; the tempo holds
T_SIL0, T_SIL1 = 13.40, 14.45
STOP0, STOP1 = 71.2, 73.0
WARM, COLD = (1.0, 0.72, 0.40), (0.80, 0.87, 1.0)

def ss(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def tau(t): return t if t < T_SIL0 else (T_SIL0 if t < T_SIL1 else t - (T_SIL1 - T_SIL0))
def beat_pulse(s):
    b = BEATS[BEATS <= s]; return float(np.exp(-(s - b[-1]) * 6)) if len(b) else 0.0
def beats_in(a, b): return BEATS[(BEATS >= a) & (BEATS < b)]
def load(n): return np.array(Image.open(f'{KVD}/{n}.png').convert('RGB')).astype(np.float32) / 255
KV = {n: load(n) for n in ('BG0a', 'BG0b', 'KV1', 'KV2', 'KV3', 'KV3b', 'KV4', 'KV5')}
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)

# ---------------------------------------------------------------- the human light in each frame
def warm(img, loose=False):
    """Warm human light: red well above blue, and bright (loose: every warm speck, for an empty sky)."""
    r, b = img[..., 0], img[..., 2]
    if loose: return (r - b > 0.05) & (img.mean(-1) > 0.20)
    return (r > 0.50) & (r - b > 0.16) & (img.mean(-1) > 0.40)

def split(img, m):
    """-> (the frame without those lights, the light layer, the mask)."""
    m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8))
    base = cv2.inpaint((img * 255).astype(np.uint8), m * 255, 3, cv2.INPAINT_TELEA).astype(np.float32) / 255
    return base, np.clip(img - base, 0, 1), m

def comps(m, amin=1, amax=10 ** 9):
    n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8))
    return lab, [(i, cen[i], st[i, 4]) for i in range(1, n) if amin <= st[i, 4] <= amax]

def small_only(m, amax):
    lab, cs = comps(m, 1, amax); keep = np.zeros(lab.max() + 1, bool); keep[[i for i, _, _ in cs]] = True
    return keep[lab]

B0A, L0A, M0A = split(KV['BG0a'], warm(KV['BG0a']))
B0B, L0B, M0B = split(KV['BG0b'], warm(KV['BG0b']))
B1, L1, M1 = split(KV['KV1'], warm(KV['KV1']))
_, L2, M2 = split(KV['KV2'], warm(KV['KV2']))
B4, L4, M4 = split(KV['KV4'], warm(KV['KV4']) & (xx < 1080))            # the city only, not B's lit face
B3, L3, M3 = split(KV['KV3'], warm(KV['KV3'], True) & (yy < 560))      # the constellation
D3 = ((np.abs(KV['KV3b'] - KV['KV3']).max(-1) > 0.02) & (yy >= 540)).astype(np.float32)
DM3 = cv2.GaussianBlur(D3, (0, 0), 4)[..., None]                       # A's look-up only, not the sky
def kv3src(k): return KV['KV3'] * (1 - DM3 * k) + KV['KV3b'] * DM3 * k
KV3B = kv3src(1.0)
B3c, L3c, _ = split(KV3B, small_only(warm(KV3B) & (yy >= 780) & (yy < 940), 60))  # the city under them
_fm = (xx > 600) & (xx < 740) & (yy > 500) & (yy < 642) & (KV['KV5'].mean(-1) > 0.5) & (KV['KV5'][..., 0] - KV['KV5'][..., 2] > 0.2)
FLAME = (float(xx[_fm].mean()), float(yy[_fm].mean()))
_g5 = 0.9 * np.exp(-((xx - FLAME[0]) ** 2 + (yy - FLAME[1] - 20) ** 2) / (2 * 75.0 ** 2))[..., None]
def _unlit(img):
    """KV5 before the fire: fill the flame smoothly from around it, then take the flame's warm cast off her hand."""
    m = cv2.dilate(((np.hypot(xx - FLAME[0], yy - FLAME[1]) < 52) & (img[..., 0] - img[..., 2] > 0.08) & (yy < FLAME[1] + 40) | _fm)
                   .astype(np.float32), np.ones((7, 7), np.uint8))
    k = cv2.GaussianBlur(1 - m, (0, 0), 18)[..., None]
    fill = cv2.GaussianBlur(img * (1 - m)[..., None], (0, 0), 18) / np.maximum(k, 1e-3)
    ms = cv2.GaussianBlur(m, (0, 0), 4)[..., None]
    out = img * (1 - ms) + fill * ms
    w = np.clip(out[..., 0] - out[..., 2] - 0.02, 0, 1) * _g5[..., 0]
    out[..., 0] -= w * 0.95; out[..., 1] -= w * 0.55
    return np.clip(out * (1 - 0.35 * _g5), 0, 1)
B5 = _unlit(KV['KV5'])

LAB0B, C0B = comps(M0B, 12)
LAB4, C4 = comps(M4, 4)
LAB2, C2 = comps(M2, 140)
WIN = sorted([c for c in C2 if c[1][1] < 560 and 200 < c[1][0] < 700], key=lambda c: c[1][1])  # the window trail, top first
GROUPS = np.array_split(np.arange(len(WIN)), 3)

rng = np.random.default_rng(3)
PHASE = cv2.resize(rng.random((64, 96)).astype(np.float32), (SW, SH), interpolation=cv2.INTER_NEAREST)
SLOW = cv2.GaussianBlur(rng.random((SH, SW)).astype(np.float32), (0, 0), 18)
SLOW = (SLOW - SLOW.min()) / (SLOW.max() - SLOW.min())

def flick(s): return 0.88 + 0.12 * np.sin(s * 2.1 + PHASE * 40)
def living(base, light, s, turnover=0.0):
    """Lights that flicker slightly; with turnover some districts go dark while others light: people pass."""
    g = flick(s)
    if turnover:
        th = 0.5 + 0.5 * np.sin(s * 0.9 + SLOW * 9)
        g = g * (0.35 + 0.65 * (th > 0.25 * turnover))
    return base + light * g[..., None]

def brightest(L, box):
    x0, y0, x1, y1 = box; g = cv2.GaussianBlur(L.mean(-1), (0, 0), 6)[y0:y1, x0:x1]
    y, x = np.unravel_index(g.argmax(), g.shape); return (x0 + x, y0 + y)

# ---------------------------------------------------------------- camera and marks
def view(img, cx=SW / 2, cy=SH / 2, zoom=1.0):
    """Output 1280x720 of the painting centred at (cx, cy); zoom 1 = the full-width crop.
    The window is clamped inside the painting: nothing outside it can ever be sampled."""
    zoom = max(1.0, float(zoom)); sc = W / SW * zoom
    hw, hh = W / 2 / sc, H / 2 / sc
    cx = float(np.clip(cx, hw, SW - hw)); cy = float(np.clip(cy, hh, SH - hh))
    M = np.float32([[sc, 0, W / 2 - cx * sc], [0, sc, H / 2 - cy * sc]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR if zoom < 1.05 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE), M

def to_screen(M, p): return M @ np.array([p[0], p[1], 1.0])

def dots(fr, pts, r=2.2, col=WARM):
    """Small warm lights, painted, not sparkles. pts: (x, y, strength) on screen."""
    lay = np.zeros((H, W), np.float32); any_ = False
    for x, y, k in pts:
        if k > 0 and -20 < x < W + 20 and -20 < y < H + 20:
            cv2.circle(lay, (int(round(x * 4)), int(round(y * 4))), max(4, int(r * 4)), float(k), -1, cv2.LINE_AA, shift=2); any_ = True
    if not any_: return fr
    g = np.clip(cv2.GaussianBlur(lay, (0, 0), max(0.8, r * 0.6)) * 1.3 + cv2.GaussianBlur(lay, (0, 0), r * 3) * 0.5, 0, 1)
    return fr + g[..., None] * np.array(col) * (1 - fr)

def streaks(fr, segs, col=WARM):
    """Thin trails behind moving lights. segs: ((x0, y0), (x1, y1), alpha) on screen."""
    if not segs: return fr
    lay = np.zeros((H, W), np.float32)
    for p0, p1, a in segs:
        cv2.line(lay, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), float(a), 1, cv2.LINE_AA, shift=2)
    return fr + cv2.GaussianBlur(lay, (0, 0), 0.8)[..., None] * np.array(col) * (1 - fr)

def hairline(fr, y, k):
    """The sheet: a straight cold hairline across the frame. Not human, so never warm."""
    if k <= 0 or not -10 < y < H + 10: return fr
    lay = np.zeros((H, W), np.float32)
    cv2.line(lay, (0, int(round(y * 16))), (W * 16, int(round(y * 16))), 1.0, 1, cv2.LINE_AA, shift=4)
    g = np.clip(lay * 0.6 + cv2.GaussianBlur(lay, (0, 0), 4) * 1.5, 0, 1) * k
    return fr + g[..., None] * np.array(COLD) * (1 - fr)

# ---------------------------------------------------------------- the paper transition
PAPER = np.array([0.93, 0.90, 0.83], np.float32); GRAPHITE = np.array([0.30, 0.30, 0.34], np.float32)
OCHRE = np.array([0.86, 0.50, 0.18], np.float32)
def paper_layers(img, light, seed):
    lum = img.mean(-1)
    dog = np.clip((cv2.GaussianBlur(lum, (0, 0), 2.2) - cv2.GaussianBlur(lum, (0, 0), 0.8)) * 22, 0, 1)
    b = cv2.GaussianBlur(lum, (0, 0), 1.6)
    sob = np.hypot(cv2.Sobel(b, cv2.CV_32F, 1, 0), cv2.Sobel(b, cv2.CV_32F, 0, 1))
    pen = np.clip(np.maximum(dog, np.clip(sob * 4.5, 0, 1) * 0.75), 0, 1) ** 0.85
    sm = img.copy()
    for _ in range(2): sm = cv2.bilateralFilter(sm, 9, 0.1, 7)
    wash = PAPER * (0.45 + 0.55 * np.clip(sm / max(1e-3, np.percentile(sm, 99)), 0, 1) ** 0.55)
    r = np.random.default_rng(seed)
    tex = 1 + (cv2.GaussianBlur(r.random(lum.shape).astype(np.float32), (0, 0), 1.2) - 0.5) * 0.10 \
            + (cv2.GaussianBlur(r.random(lum.shape).astype(np.float32), (0, 0), 30) - 0.5) * 0.25
    mark = np.clip(cv2.GaussianBlur(light.max(-1), (0, 0), 1.0) * 3.0, 0, 1)
    return dict(pen=pen.astype(np.float32), wash=wash.astype(np.float32), tex=tex.astype(np.float32), mark=mark.astype(np.float32))

def paper(painted, P, a, mark=None):
    """a: per-pixel state. >0.62 painted, 0.40 flat wash, 0.16 pencil, below that bare paper.
    The human lights outlive the paint as ochre marks."""
    wp = ss(0.58, 0.66, a); wf = ss(0.36, 0.44, a); wn = ss(0.09, 0.23, a)
    out = np.broadcast_to(PAPER, painted.shape).copy()
    out = out * (1 - wf[..., None]) + P['wash'] * wf[..., None]
    out = out * P['tex'][..., None] ** (1 - wp[..., None])
    pv = P['pen'] * wn * (1 - wp)
    out = out * (1 - pv[..., None]) + GRAPHITE * pv[..., None]
    mk = (P['mark'] if mark is None else mark) * (1 - wp)
    out = out * (1 - mk[..., None]) + OCHRE * mk[..., None]
    rim = np.clip(np.abs(cv2.GaussianBlur(wp, (0, 0), 1.5) - cv2.GaussianBlur(wp, (0, 0), 5)) * 3, 0, 1)
    out = out * (1 - wp[..., None]) + painted * wp[..., None]
    return out * (1 - 0.12 * rim[..., None])

P1 = paper_layers(KV['KV1'], L1, 5)
P0A = paper_layers(KV['BG0a'], L0A, 6)
P2 = paper_layers(KV['KV2'], L2, 7)
DS1 = np.sqrt(((xx - 768) / 768) ** 2 + ((yy - 690) / 600) ** 2)       # KV1: distance from the girls
DT1 = cv2.distanceTransform((M1 == 0).astype(np.uint8), cv2.DIST_L2, 5)  # KV1: distance to the nearest light

# ---------------------------------------------------------------- 0:00 countdown
LEDGE_Y = 840.0                                                     # KV1's ledge, source px
LY = (LEDGE_Y - 80) * W / SW                                        # ...on screen
FIELD = view(cv2.GaussianBlur(KV['KV1'], (0, 0), 6) * 0.5)[0]         # the world not yet loaded
ONES = np.ones((H, W), np.float32)
cols = np.array([0, 384, 768, 1152, 1535], float); tops = np.array([383, 296, 270, 313, 435], float)
ARC = np.polyval(np.polyfit(cols, tops, 2), np.arange(SW)).astype(np.float32) - 270   # how far the rim curves down

def squash(fr, h):
    """Scale the frame vertically about the ledge line; outside it, the unloaded world."""
    h = max(0.004, h); M = np.float32([[1, 0, 0], [0, h, LY * (1 - h)]])
    w = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = cv2.warpAffine(ONES, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]
    return w + FIELD * (1 - a)

def sh_countdown(t, s):
    if t < 3.3:                                                     # 3D: the living globe, lights coming up on "Three"
        k = 0.35 + 0.65 * ss(0.9, 2.2, s)
        return view(B0A + L0A * (k * flick(s))[..., None], SW / 2 + 14 * s, SH / 2, 1.0 + 0.02 * s)[0]
    if t < 4.5:                                                     # 3D -> 2D: the rim straightens, the world lies flat
        e = float(ss(3.3, 4.2, s))
        flat = cv2.remap(B0A + L0A * 0.95, xx, (yy + ARC[None, :] * e * (1 - yy / SH) * 1.8).astype(np.float32),
                         cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        img = flat * (1 - ss(3.7, 4.3, s)) + KV['BG0b'] * ss(3.7, 4.3, s)
        return view(img, SW / 2 + 46, SH / 2, 1.066)[0]
    e = float(ss(4.5, 5.3, s))                                      # 2D -> 1D: the map thins into the line of the ledge
    fr = squash(view(KV['BG0b'], SW / 2 + 46, SH / 2, 1.066)[0], 1 - e)
    glow = np.clip((fr - 0.25) * 1.6, 0, 1) * (1 + 2.5 * e)           # the lights concentrate as the world thins
    return np.clip(fr * (1 - 0.6 * e) + glow * np.array(WARM) * e * 0.6, 0, 1)

def sh_loading(t, s):                                               # the line opens into a drawing that paints in
    img = living(B1, L1, s)
    a = np.maximum(0.30 * ss(5.62, 6.0, t), 0.62 + (lerp(-0.2, 1.6, ss(6.0, 7.5, t)) - DS1) * 3)  # sketched, then painted from them out
    fr = view(paper(img, P1, a))[0]
    if t < 6.25: fr = squash(fr, float(ss(5.62, 6.25, t)))
    return fr + 0.12 * np.exp(-(t - 5.62) * 10)                     # a brief lift on the hit, not a bloom

def sh_rise(t, s):                                                  # KV2: follow the traces up
    u = float(ss(8.452, 10.24, t))
    fr, M = view(KV['KV2'], SW / 2 - 60 * u, SH / 2 - 150 * u, 1.0 + 0.2 * u)
    pts = []
    for k in range(9):
        ph = ((s - 8.45) * 0.45 + k / 9) % 1.0
        x, y = to_screen(M, (700 + 80 * np.sin(k * 2.3) + 220 * ph * np.sin(k), 880 - 780 * ph))
        pts.append((x, y, np.sin(np.pi * ph) * 0.9))
    return dots(fr, pts, 2.0)

def sh_city1(t, s):                                                 # human scale: windows light and go dark
    return view(living(B4, L4, s, turnover=1.0), 300 + 20 * ss(10.24, 11.981, t), 805, 2.6)[0]

# ---------------------------------------------------------------- 0:12 the city becomes the sky
ys3, xs3 = np.nonzero(M3 > 0)
pick = rng.choice(len(xs3), 70, replace=False)
T_TGT = np.stack([xs3[pick], ys3[pick]], 1).astype(np.float32)       # where each trace settles as a star
T_SRC = np.stack([rng.uniform(250, 1300, 70), rng.uniform(760, 840, 70)], 1).astype(np.float32)
T_T0 = rng.uniform(12.0, 13.3, 70); T_DUR = rng.uniform(1.6, 2.6, 70)

def sh_sky(t, s):
    reveal = np.zeros((SH, SW), np.float32); heads = []
    for k in range(70):
        u = np.clip((s - T_T0[k]) / T_DUR[k], 0, 1)
        if u <= 0: continue
        if u < 1: heads.append(T_SRC[k] + (T_TGT[k] - T_SRC[k]) * (u * u * (3 - 2 * u)) + np.array([40 * np.sin(u * 3.1 + k), 0]))
        else: cv2.circle(reveal, (int(T_TGT[k][0]), int(T_TGT[k][1])), 70, 1.0, -1)
    reveal = np.maximum(cv2.GaussianBlur(reveal, (0, 0), 25), ss(15.6, 17.2, s))
    base = kv3src(float(ss(17.75, 17.86, t))) - L3 * (1 - reveal)[..., None]
    lk = float(ss(17.9, 20.4, t))                                   # her look-up: the camera follows her eyeline
    fr, M = view(base, SW / 2, SH / 2 - 150 * lk, 1.0 + 0.25 * lk)
    return dots(fr, [(*to_screen(M, p), 0.9) for p in heads], 2.2)

def sh_b_city(t, s): return view(living(B4, L4, s, turnover=ss(21.5, 24, s)))[0]
def sh_kv1_time(t, s): return view(living(B1, L1, s, turnover=0.8))[0]

def sh_fall(t, s):                                                  # a light falls toward her open hand
    fr, M = view(B5)
    u = np.clip((t - 27.95) / (29.118 - 27.95), 0, 1)
    x, y = to_screen(M, (FLAME[0] + 30 * np.sin(u * 4) * (1 - u), -40 + (FLAME[1] + 40) * u ** 1.6))
    return dots(fr, [(x, y, 1.0)], 2.6)

def fire(s):
    fl = 0.86 + 0.14 * np.sin(s * 21) * np.sin(s * 7.7) + 0.08 * beat_pulse(s)
    return B5 + (KV['KV5'] - B5) * fl

def sh_fire(t, s): return view(fire(s))[0]                           # contact: the first fire lights her

O_NET = np.array([700.0, 520.0])                                     # the first light on the globe
def sh_network(t, s):                                               # the flame becomes the network; it holds its breath
    u = float(ss(30.929, 33.2, t))
    rad = 40 + 1500 * ss(31.1, 33.2, t) ** 1.5
    grow = np.clip((rad - np.hypot(xx - O_NET[0], yy - O_NET[1])) / 120, 0, 1)
    img = B0A * 0.8 + L0A * (grow * flick(min(s, 33.2)))[..., None]
    zoom = 2.6 - 1.6 * u; sc = W / SW * zoom
    fx, fy = FLAME[0] * W / SW, (FLAME[1] - 80) * W / SW              # where the flame was on screen
    cx = lerp(O_NET[0] - (fx - W / 2) / sc, SW / 2, u); cy = lerp(O_NET[1] - (fy - H / 2) / sc, SH / 2, u)
    fr, M = view(img, cx, cy, zoom)
    return dots(fr, [(*to_screen(M, O_NET), 1.0 - 0.5 * u)], 3.0)

# ---------------------------------------------------------------- 0:38.4 pre-chorus / chorus 1
def sh_countdown_kv1(t, s):                                         # something vast counts down: edges first
    steps = beats_in(38.5, 44.0)[1::2]
    p = sum(float(ss(b, b + 0.25, t)) for b in steps) / max(1, len(steps))
    thr = 1.35 - 1.1 * p
    g = flick(s) * (1 - 0.92 * ss(thr - 0.04, thr + 0.04, DS1))
    return view(B1 + L1 * g[..., None])[0] * (1 - 0.12 * p)

rW = np.random.default_rng(21)
WALL_X = rW.uniform(200, 1340, 26); WALL_Y0 = rW.uniform(800, 860, 26); WALL_T0 = rW.uniform(49.9, 51.2, 26)
WALL_Y = 102.0                                                      # the top of the frame: the wall
def sky_alive(s, present=None, city=None):
    g = 0.72 + 0.28 * np.sin(s * 0.8 + SLOW * 14)                    # stars are people: some fade, some come back
    if present is not None: g = g * present
    cg = flick(s) if city is None else flick(s) * city
    return B3c - L3 * (1 - g)[..., None] + L3c * cg[..., None]

def sh_wall(t, s):                                                  # the lights return; light cannot pass the edge
    fr, M = view(sky_alive(s))
    pts, segs = [], []
    for k in range(26):
        if t < WALL_T0[k]: continue
        y = max(WALL_Y, WALL_Y0[k] - 330 * (t - WALL_T0[k]))           # constant speed, no easing: then it stops
        x, ys_ = to_screen(M, (WALL_X[k], y)); pts.append((x, ys_, 0.95))
        if y > WALL_Y: segs.append(((x, ys_), (x, ys_ + 24), 0.35))
    return dots(streaks(fr, segs), pts, 2.0)

PLANCK = brightest(L4, (260, 700, 520, 900))
def sh_planck(t, s):                                                # into one window until the painting runs out
    u = float(ss(55.0, 58.4, t))
    fr = view(living(B4, L4, s), lerp(300, PLANCK[0], u), lerp(805, PLANCK[1], u), 2.6 * (8.0 / 2.6) ** u)[0]
    f = float(ss(56.6, 58.6, t))
    if f > 0:
        fr = fr * (1 - f) + cv2.GaussianBlur(fr, (0, 0), 2 + 10 * f) * f
        fr = fr * (1 - 0.3 * f) + fr.mean((0, 1)) * 0.3 * f
    return fr

def sh_lookaway(t, s): return view(living(B3c, L3c, s, turnover=1.0), 740, 784, 1.8)[0]
def sh_city_alone(t, s): return view(living(B4, L4, s, turnover=1.0), 250, 800, 3.2)[0]
def sh_unanswered(t, s): return view(living(B1, L1, s))[0]

def sh_stop(t, s):                                                  # the stop: all holds but one trace
    fr, M = view(living(B1, L1, STOP0))
    y = 700 - 140 * max(0.0, t - 71.35)
    x, ys_ = to_screen(M, (1150, y))
    return dots(streaks(fr, [((x, ys_), (x, ys_ + 20), 0.3)]), [(x, ys_, 0.95)], 2.2)

# ---------------------------------------------------------------- 1:13 verse 2
SIG = sorted(C0B, key=lambda c: -c[2])[:8]
SIG_T = beats_in(73.1, 77.2)[:8]
def sh_signals(t, s):                                               # signals leave the map; nothing answers
    fr, M = view(living(B0B, L0B, s))
    pts, segs = [], []
    for c, tb in zip(SIG, SIG_T):
        if t < tb: continue
        y = c[1][1] - 360 * (t - tb)
        x, ys_ = to_screen(M, (c[1][0], y))
        pts.append((x, ys_, 0.95)); segs.append(((x, ys_), (x, ys_ + 50), 0.4))
    return dots(streaks(fr, segs), pts, 2.0)

def win_dark(lut):
    d = cv2.GaussianBlur(lut[LAB2].astype(np.float32), (0, 0), 1.5)
    return KV['KV2'] * (1 - d[..., None] * (1 - np.array([0.22, 0.24, 0.32]))), d

def lut_out(t, steps):
    lut = np.zeros(LAB2.max() + 1, np.float32)
    for g, b in zip(GROUPS, steps):
        for j in g: lut[WIN[j][0]] = ss(b, b + 0.25, t)
    return lut

OUT_STEPS = beats_in(79.0, 82.2)[::2][:3]
def sh_windows_out(t, s): return view(win_dark(lut_out(t, OUT_STEPS))[0])[0]  # a countdown; certainty dies

def sh_sheet(t, s):                                                 # a sheet thinner than any mind
    fr = view(living(B0A, L0A, s))[0]
    return hairline(fr, (lerp(60, 266, ss(87.2, 93.7, t)) - 80) * W / SW, float(ss(87.0, 88.2, t)))

def sh_flat(t, s):                                                  # it touches the rim: everything falls flat
    yl = 266 + 760 * np.clip((t - 93.7) / 3.3, 0, 1) ** 1.5
    img = paper(living(B0A, L0A, s), P0A, np.maximum(0.62 + (yy - yl) / 110, 0.30))
    return hairline(view(img)[0], (yl - 80) * W / SW, 1.0 - ss(96.6, 97.4, t))

def sh_b_looks(t, s): return view(living(B4, L4, s))[0]            # and still she looks

LUT_ALL_OUT = lut_out(1e9, OUT_STEPS)
def kv2_paper(t, s, lut, yl):
    img, d = win_dark(lut)
    img = img * (1 - 0.25 * ss(99.9, 103.0, t))                     # the dark comes closer
    return paper(img, P2, np.maximum(0.62 + (yy - yl) / 110, 0.30), mark=P2['mark'] * (1 - d))

def sh_flat_near(t, s):
    yl = lerp(-60, 150, ss(100.2, 105.2, t))
    fr, M = view(kv2_paper(t, s, LUT_ALL_OUT, yl))
    return hairline(fr, to_screen(M, (0, yl))[1], float(ss(100.2, 100.8, t)))

UP_PATH = np.array([(768, 512), (560, 460), (470, 330), (400, 230)], float)
def along(path, u):
    seg = np.hypot(*np.diff(path, axis=0).T); c = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    i = min(len(seg) - 1, np.searchsorted(c, u, side='right') - 1); v = (u - c[i]) / (c[i + 1] - c[i])
    return path[i] + (path[i + 1] - path[i]) * v

def sh_follow_up(t, s):                                             # we follow the windows up to the edge
    lut = LUT_ALL_OUT.copy()
    for j, c in enumerate(WIN[::-1]):                               # they relight from the bottom as we climb
        lut[c[0]] = 1 - ss(105.5 + j * 4.0 / len(WIN), 105.8 + j * 4.0 / len(WIN), t)
    u = float(ss(105.2, 110.3, t)); cx, cy = along(UP_PATH, u)
    fr, M = view(kv2_paper(t, s, lut, 150.0), cx, cy, 1 + 1.1 * u)
    return hairline(fr, to_screen(M, (0, 150.0))[1], 1.0)

# ---------------------------------------------------------------- 1:50.6 chorus 2
def sh_past_stars(t, s): return view(sky_alive(s), lerp(349, 1187, ss(110.8, 116.8, t)), 300, 2.2)[0]

KEYS = [c for c in C0B if c[2] > 40]
rK = np.random.default_rng(8)
KEY_B = beats_in(117.0, 121.6); KEY_I = rK.integers(len(KEYS), size=len(KEY_B))
def sh_console(t, s):                                               # the map as a console: keys pressed, no hand
    lut = np.full(LAB0B.max() + 1, 0.35, np.float32)
    for b, i in zip(KEY_B, KEY_I):
        if t >= b: lut[KEYS[i][0]] += 0.9 * np.exp(-(t - b) * 2.2)
    return view(B0B + L0B * (lut[LAB0B] * flick(s))[..., None], 768, 470, 1.2)[0]

def sh_empty_hand(t, s): return view(B5, 600, 520, 1.4)[0]         # no one holding the keys

def sh_unfinished(t, s):                                            # an unfinished universe
    return view(paper(living(B1, L1, s), P1, 0.62 + (lerp(1.6, 1.08, ss(124.9, 126.5, t)) - DS1) * 3))[0]

# ---------------------------------------------------------------- 2:08.6 bridge
def sh_no_gods(t, s): return view(living(B0A, L0A, s), SW / 2, 432, 1.0)[0]
def sh_empty_sky(t, s): return view(sky_alive(s))[0]

rP = np.random.default_rng(9)
PRESS_B = beats_in(134.7, 137.9)
PRESS = rP.integers(len(PRESS_B), size=LAB4.max() + 1)
def sh_keys(t, s):                                                  # look who's pressing the keys
    lut = (0.22 + 0.78 * ss(PRESS_B[PRESS], PRESS_B[PRESS] + 0.15, t)).astype(np.float32)
    return view(B4 + L4 * (lut[LAB4] * flick(s))[..., None], 275, 820, 3.0)[0]

rT = np.random.default_rng(11)
CITIES = np.array([c[1] for c in C0B if c[2] > 20])
TR = []
for _ in range(44):
    a = CITIES[rT.integers(len(CITIES))]; d = np.hypot(*(CITIES - a).T)
    cand = np.nonzero((d > 110) & (d < 380))[0]
    if len(cand):
        b = CITIES[rT.choice(cand)]
        TR.append((a, b, rT.uniform(138.0, 142.6), np.hypot(*(b - a)) / rT.uniform(60, 85), rT.uniform(-0.25, 0.25)))

def tr_point(a, b, bend, u):
    m = (a + b) / 2 + np.array([-(b - a)[1], (b - a)[0]]) * bend
    return (1 - u) ** 2 * a + 2 * (1 - u) * u * m + u ** 2 * b

def paths(t, full=False, alpha=0.55):
    lay = np.zeros((SH, SW), np.float32); heads = []
    for a, b, t0, dur, bend in TR:
        u = 1.0 if full else float(np.clip((t - t0) / dur, 0, 1))
        if u <= 0: continue
        P = np.array([tr_point(a, b, bend, v) for v in np.linspace(0, u, max(2, int(16 * u)))])
        cv2.polylines(lay, [np.round(P * 4).astype(np.int32)], False, alpha, 1, cv2.LINE_AA, shift=2)
        if u < 1: heads.append(P[-1])
    return cv2.GaussianBlur(lay, (0, 0), 0.9), heads

def map_paths(t, s, full=False, alpha=0.55, lights=0.6):
    tr, heads = paths(t, full, alpha)
    img = B0B + L0B * (lights * flick(s))[..., None]
    return img + tr[..., None] * np.array(WARM) * (1 - img), heads

def sh_travellers(t, s):                                            # travellers with lanterns; their paths remain
    img, heads = map_paths(t, s)
    fr, M = view(img, 768, 480, 1.15)
    return dots(fr, [(*to_screen(M, p), 0.95) for p in heads], 1.8)

def sh_not_i(t, s): return view(living(B4, L4, s))[0]

# ---------------------------------------------------------------- 2:26.4 the break: one scale per hit
def sh_h1(t, s): return view(B4 + L4 * ((0.8 + 0.25 * ss(146.4, 150, t)) * flick(s))[..., None], 300, 805, 2.6)[0]
def sh_h2(t, s): return view(living(B4, L4, s))[0]
def sh_h3(t, s): return view(map_paths(t, s, True, lerp(0.35, 0.6, ss(153.6, 158.8, t)), 1.0)[0])[0]
def sh_h4(t, s): return view(living(B0A, L0A, s))[0]
def sh_breath(t, s): return view(B0A * lerp(1.0, 0.3, ss(160.1, 160.5, t)) + L0A * 0.8)[0]

# ---------------------------------------------------------------- 2:41.4 final chorus
rD = np.random.default_rng(17)
D_T0 = rD.uniform(163.0, 168.2, 70); D_DUR = rD.uniform(2.0, 3.2, 70)
def sh_descent(t, s):                                               # the thing that came down from the edge of the sky
    gone = np.zeros((SH, SW), np.float32); heads = []; arrived = 0
    for k in range(70):
        u = (t - D_T0[k]) / D_DUR[k]
        if u <= 0: continue
        cv2.circle(gone, (int(T_TGT[k][0]), int(T_TGT[k][1])), 70, 1.0, -1)
        if u < 1: heads.append(T_TGT[k] + (T_SRC[k] - T_TGT[k]) * float(ss(0, 1, u)) + np.array([30 * np.sin(u * 3.1 + k) * (1 - u), 0]))
        else: arrived += 1
    present = (1 - np.clip(cv2.GaussianBlur(gone, (0, 0), 25) * 1.2, 0, 1)) * (1 - ss(169.5, 171.5, t))
    img = sky_alive(s, present, 0.6 + 0.4 * arrived / 70)
    fr, M = view(img, SW / 2, lerp(346, 678, ss(162.0, 171.0, t)), 1.25)
    return dots(fr, [(*to_screen(M, p), 0.9) for p in heads], 2.2)

TRAIL = np.array([c[1] for c in WIN] + [(600, 700)], float)
TRAIL[1:-1, 0] = np.convolve(TRAIL[:, 0], [0.25, 0.5, 0.25], 'valid')   # a smooth path down the trail
def sh_every_traveller(t, s):                                       # every window a traveller; they come down
    u = float(ss(176.0, 181.5, t))
    fr, M = view(KV['KV2'], lerp(430, SW / 2, u), lerp(300, SH / 2, u), lerp(2.4, 1.0, u))
    pts = []
    for k in range(10):
        ph = ((t - 172.0) * 0.12 + k / 10) % 1.0
        pts.append((*to_screen(M, along(TRAIL, ph)), np.sin(np.pi * ph) * 0.9))
    return dots(fr, pts, 2.0)

rO = np.random.default_rng(12)
OUT4 = rO.uniform(182.3, 192.3, LAB4.max() + 1)
def lights_out(t, s):
    lut = (1 - 0.9 * ss(OUT4, OUT4 + 0.5, t)).astype(np.float32)
    return B4 + L4 * (lut[LAB4] * flick(s))[..., None]
def sh_out_crop(t, s): return view(lights_out(t, s), 300, 805, 2.6)[0]  # every light that went out
def sh_out_full(t, s): return view(lights_out(t, s))[0]              # and B watches them go

# ---------------------------------------------------------------- 3:12.5 paper, the return, the end
PAPER_END = np.clip(0.34 - 0.55 * DS1, 0, 1)                         # all paper; the girls stay in pencil
def paper_state(t): return np.maximum(PAPER_END, 0.62 + (lerp(1.7, -0.3, ss(192.6, 197.6, t)) - DS1) * 3)
def sh_paper(t, s): return view(paper(living(B1, L1, s), P1, paper_state(t)))[0]   # one day we'll be paper

RET_B = beats_in(198.9, 203.3)
def sh_return(t, s):                                                # the world repaints from its lights, pulse by pulse
    R = 30 + 110 * sum(float(ss(b, b + 0.3, t)) for b in RET_B)
    a = np.maximum(PAPER_END, 0.62 + (R - DT1) / 80)
    return view(paper(living(B1, L1, s), P1, a))[0]

def sh_together(t, s): return view(fire(s), SW / 2, 452, 1.0)[0]    # the only frame they share

CHAIN = [(fire, FLAME, 2.4),
         (lambda s: sky_alive(s), brightest(L3, (320, 180, 1216, 540)), 2.4),
         (lambda s: KV['KV2'], tuple(max([c for c in WIN if c[1][0] > 320 and c[1][1] > 180], key=lambda c: c[2])[1]), 2.4),
         (lambda s: living(B4, L4, s), brightest(L4, (256, 600, 540, 880)), 3.0),
         (lambda s: living(B1, L1, s), brightest(L1, (320, 500, 1216, 800)), 2.4),
         (lambda s: living(B0B, L0B, s), brightest(L0B, (320, 180, 1216, 844)), 2.4),
         (lambda s: living(B0A, L0A, s), brightest(L0A, (320, 180, 1216, 844)), 2.4)]
CHAIN_B = beats_in(207.3, 211.0)
def sh_chain(t, s):                                                 # one light per beat, the chain back to the globe
    k = min(int((CHAIN_B <= t).sum()), len(CHAIN) - 1)
    fn, p, z = CHAIN[k]
    if k < len(CHAIN) - 1: return view(fn(s), p[0], p[1], z)[0]
    u = float(ss(CHAIN_B[len(CHAIN) - 2], 211.0, t))                 # the last: pull back to the whole Earth
    return view(fn(s), lerp(p[0], SW / 2, u), lerp(p[1], SH / 2, u), lerp(z, 1.0, u))[0]

DO = np.hypot(xx - O_NET[0], yy - O_NET[1])
def sh_outro(t, s):                                                 # two... three... and one... still loading
    rad = lerp(1400, -120, ss(211.0, 211.9, t))
    img = paper(living(B0A, L0A, s), P0A, 0.62 + (rad - DO) / 150, mark=P0A['mark'] * (DO < rad))
    fr, M = view(img)
    blink = 1.0 if t < 211.9 else 0.6 + 0.4 * np.cos(2 * np.pi * (t - 211.9) / 0.4)
    x, y = to_screen(M, O_NET); lay = np.zeros((H, W), np.float32)
    cv2.circle(lay, (int(x * 4), int(y * 4)), 22, 1.0, -1, cv2.LINE_AA, shift=2)
    g = np.clip(cv2.GaussianBlur(lay, (0, 0), 1.5) * 1.2, 0, 1)[..., None] * blink    # on paper the last light is ink
    return fr * (1 - g) + OCHRE * g

FLAME_SCR = (FLAME[0] * W / SW, (FLAME[1] - 80) * W / SW)            # where the flame was on screen
def sp_network(t, s): return space.s_network(t, *FLAME_SCR)
def sp_wall(t, s): return space.s_wall(t)
def sh_planck_lattice(t, s):                                        # under the painting, the grid of the simulation
    k = float(ss(57.2, 57.8, t))
    if k <= 0: return sh_planck(t, s)
    if k >= 1: return space.s_lattice(t)
    return sh_planck(t, s) * (1 - k) + space.s_lattice(t) * k
SIG_B = beats_in(73.1, 77.2)[:8]
def sp_signals(t, s): return space.s_signals(t, SIG_B)
def sp_sheet(t, s): return space.s_sheet(t)
def sp_flat(t, s): return space.s_flat(t)
def sp_fly(t, s): return space.s_fly(t)
CON_B = beats_in(117.0, 121.6)
def sp_console(t, s): return space.s_console(t, CON_B)
def sp_no_gods(t, s): return space.s_no_gods(t)
def sp_threads(t, s): return space.s_threads(t)
def sp_outro(t, s): return space.s_outro(t)

SHOTS = [(0.0, sh_countdown), (5.62, sh_loading), (8.452, sh_rise), (10.24, sh_city1), (11.981, sh_sky),
         (20.863, sh_b_city), (25.913, sh_kv1_time), (27.748, sh_fall), (29.118, sh_fire), (30.929, sp_network),
         (38.4, sh_countdown_kv1), (44.1, sh_wall), (51.3, sp_wall), (54.9, sh_planck_lattice), (58.6, sh_lookaway), (61.8, sh_city_alone),
         (65.0, sh_unanswered), (STOP0, sh_stop), (73.0, sp_signals), (78.4, sh_windows_out), (86.5, sp_sheet),
         (93.7, sp_flat), (97.8, sh_b_looks), (99.9, sh_flat_near), (105.2, sh_follow_up), (110.6, sp_fly),
         (117.0, sp_console), (121.6, sh_empty_hand), (124.9, sh_unfinished), (128.6, sp_no_gods),
         (131.6, sh_empty_sky), (134.6, sh_keys), (138.0, sh_travellers), (144.6, sh_not_i), (146.4, sh_h1),
         (150.0, sh_h2), (153.6, sh_h3), (158.8, sp_threads), (161.4, sh_descent),
         (172.0, sh_every_traveller), (182.0, sh_out_crop), (187.0, sh_out_full), (192.5, sh_paper),
         (198.9, sh_return), (203.4, sh_together), (207.2, sh_chain), (211.0, sp_outro)]
STARTS = [a for a, _ in SHOTS]

def frame_at(t):
    if t >= T_BLACK: return np.zeros((H, W, 3), np.uint8)
    s = tau(t)
    fr = SHOTS[bisect.bisect_right(STARTS, t) - 1][1](t, s)
    if T_SIL0 <= t < T_SIL1 or STOP0 <= t < STOP1:                  # the world holds its breath
        g = fr.mean(-1, keepdims=True); fr = fr * 0.75 + g * 0.25
    fr = fr + np.random.default_rng(int(round(t * FPS))).normal(0, 0.007, (H, W, 1))
    return (np.clip(fr, 0, 1) * 255).astype(np.uint8)

def work(a):
    out, i = a
    cv2.imwrite(f'{out}/f{i:05d}.png', cv2.cvtColor(frame_at(i / FPS), cv2.COLOR_RGB2BGR))

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    t0, t1 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (0.0, T_END)
    with Pool(4) as p: p.map(work, [(out, i) for i in range(int(round(t0 * FPS)), int(round(t1 * FPS)))], chunksize=8)
