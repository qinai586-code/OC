"""Character acting from still drawings.

- Morph: in-betweens between drawings of the same character (expressions, turnaround views)
  with dense optical flow; drawings change on twos like limited animation.
- breathe / sway: small, continuous secondary motion (no frame is ever identical).
- Particle forms: a character becomes her own light and can re-form as another drawing.
"""
from lw import *

CH = w2('chars')
_img = {}


def char(name):
    if name not in _img:
        _img[name] = imread(os.path.join(CH, name + '.png')).astype(np.float32)
    return _img[name]


def on_twos(t):
    return np.floor(t * 12) / 12.0


def fit_canvas(imgs, h=None, pad=0.06):
    """Scale RGBA images to the same height and centre them on one canvas (feet/centre aligned)."""
    if h is None:
        h = max(i.shape[0] for i in imgs)
    sc = [cv2.resize(i, (max(1, int(i.shape[1] * h / i.shape[0])), h), interpolation=cv2.INTER_AREA) for i in imgs]
    W = int(max(s.shape[1] for s in sc) * (1 + pad))
    out = []
    for s in sc:
        c = np.zeros((h, W, 4), np.float32)
        x0 = (W - s.shape[1]) // 2
        c[:, x0:x0 + s.shape[1]] = s
        out.append(c)
    return out


class Morph:
    """A sequence of drawings; state s in [0, n-1] gives an in-between (flow warp + blend)."""

    def __init__(self, names, h=None, key=None):
        imgs = [char(n) for n in names]
        self.frames = fit_canvas(imgs, h)
        p = w2('morph_' + (key or '_'.join(names)) + '.npy')
        if os.path.exists(p):
            self.flows = list(np.load(p, allow_pickle=True))
        else:
            self.flows = []
            for a, b in zip(self.frames[:-1], self.frames[1:]):
                self.flows.append(self._flow(a, b))
            np.save(p, np.array(self.flows, dtype=object), allow_pickle=True)

    @staticmethod
    def _flow(a, b):
        def g(x):
            return (np.clip(lum(x[:, :, :3]) * x[:, :, 3] + 0.15 * x[:, :, 3], 0, 1) * 255).astype(np.uint8)
        dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        fab = dis.calc(g(a), g(b), None)
        fba = dis.calc(g(b), g(a), None)
        return np.stack([fab, fba]).astype(np.float16)

    def at(self, s):
        n = len(self.frames)
        s = float(np.clip(s, 0, n - 1))
        i = min(int(np.floor(s)), n - 2)
        u = s - i
        if n == 1:
            return self.frames[0]
        if u < 1e-3:
            return self.frames[i]
        if u > 1 - 1e-3:
            return self.frames[i + 1]
        a, b = self.frames[i], self.frames[i + 1]
        fab, fba = self.flows[i].astype(np.float32)
        h, w = a.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        # backward warps toward the in-between position
        wa = cv2.remap(a, xs + fba[:, :, 0] * u, ys + fba[:, :, 1] * u, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        wb = cv2.remap(b, xs + fab[:, :, 0] * (1 - u), ys + fab[:, :, 1] * (1 - u), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        k = u * u * (3 - 2 * u)
        return wa * (1 - k) + wb * k


def secondary(rgba, t, breathe=0.004, sway=3.0, wind=0.0, seed=0, axis=0.5, hair_from=0.25):
    """Breathing (slow vertical scale from the base) + hair/cloth sway that grows toward the
    outline and the lower hair; returned image is the same size."""
    h, w = rgba.shape[:2]
    tt = on_twos(t)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    br = 1 + breathe * np.sin(2 * np.pi * tt / 4.2 + seed)
    sy = h - (h - ys) / br                         # scale about the bottom edge
    a = rgba[:, :, 3]
    edge = 1 - gblur(cv2.erode((a > 0.5).astype(np.uint8), np.ones((31, 31), np.uint8)).astype(np.float32), 12)
    vy = np.clip((ys / h - hair_from) / (1 - hair_from), 0, 1)
    wgt = (0.35 + 0.65 * edge) * vy
    ph = 2 * np.pi * (0.23 * tt) - ys / h * 3.0 + seed
    dx = (sway * np.sin(ph) + wind * (0.6 + 0.4 * np.sin(ph * 1.7 + 1))) * wgt * (h / 1000.0)
    dy = 0.3 * sway * np.cos(ph * 0.8) * wgt * (h / 1000.0)
    return cv2.remap(rgba, (xs - dx).astype(np.float32), (sy - dy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


class LightBody:
    """A character as light points: sampled from a drawing, they can scatter, travel and
    re-form as another drawing. Correspondence: both sets sorted by a space-filling order."""

    def __init__(self, rgba, n=9000, seed=0):
        self.card = Card(rgba)
        self.uv, self.col = self.card.particles(n, seed)
        order = np.lexsort((self.uv[:, 0], np.round(self.uv[:, 1] * 40)))
        self.uv, self.col = self.uv[order], self.col[order]
        rng = np.random.default_rng(seed)
        self.rnd = rng.random((len(self.uv), 4)).astype(np.float32)

    def world(self, pos, height, yaw=0.0, pitch=0.0, anchor=(0.5, 1.0)):
        return self.card.uv_to_world(self.uv, pos, height, yaw, pitch, anchor)


def curl_offset(P, t, scale=1.0, amp=1.0, seed=0):
    """Cheap divergence-free-ish turbulence: sum of rotating sinusoids (deterministic)."""
    x, y, z = P[:, 0] / scale, P[:, 1] / scale, P[:, 2] / scale
    s = seed
    dx = np.sin(1.7 * y + 0.9 * t + s) + 0.5 * np.sin(2.9 * z - 0.6 * t + 2 * s)
    dy = np.sin(1.3 * z + 0.7 * t + 3 * s) + 0.5 * np.sin(2.3 * x + 0.8 * t)
    dz = np.sin(1.1 * x - 0.5 * t + s) + 0.5 * np.sin(2.1 * y + 0.4 * t + s)
    return np.stack([dx, dy, dz], 1) * amp


def lerp_sets(A, B, u, rnd, spread=0.35, lift=0.0):
    """Per-particle staggered travel from A to B (each particle has its own start)."""
    st = rnd[:, 0] * spread
    k = np.clip((u - st) / max(1e-3, 1 - spread), 0, 1)
    k = k * k * (3 - 2 * k)
    P = A + (B - A) * k[:, None]
    if lift:
        P[:, 1] += lift * np.sin(np.pi * k)
    return P, k
