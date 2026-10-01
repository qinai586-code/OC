"""Atmosphere and light effects for the one-camera film (after the V2 reference):
a violet sky dome with a warm horizon, screen-space light rays from a source, anamorphic
flares on the big hits, words written in light, halos, dust in the light, a breathing camera,
and characters that materialize from (and dissolve into) their own particles."""
from lw import *
from acting import *
import voice

FONT_DIR = os.path.join(ROOT2, 'data', 'fonts')
VIOLET = np.array([0.55, 0.38, 0.95], np.float32)
ROSE = np.array([1.0, 0.55, 0.45], np.float32)
GOLD = np.array([1.0, 0.78, 0.42], np.float32)


# ---------------------------------------------------------------------------------- the sky
def sky(cam, haze=1.0, glow=1.0, warm=0.5, tint=None, below=1.0, w=W_OUT, h=H_OUT, horizon=0.0):
    """Background light by view direction: deep blue-black zenith, violet haze toward the
    horizon, a thin warm glow on it, a dark violet ground below. Never pure black."""
    s = 4
    ys, xs = np.mgrid[0:h // s, 0:w // s].astype(np.float32)
    d = np.stack([(xs * s - cam.cx) / cam.f, -(ys * s - cam.cy) / cam.f, np.ones_like(xs)], -1) @ cam.R.T
    e = d[..., 1] / np.linalg.norm(d, axis=-1) - horizon
    up = np.clip(e, 0, 1)
    zen = np.array([0.008, 0.010, 0.026], np.float32)
    mid = np.array([0.028, 0.022, 0.068], np.float32)
    hz = np.array([0.090, 0.055, 0.135], np.float32)
    gl = (ROSE * (1 - warm) + GOLD * warm) * 0.30
    t1 = np.exp(-up / 0.10)[..., None]
    t2 = np.exp(-up / 0.35)[..., None]
    col = zen + (mid - zen) * t2 + (hz - mid) * t1 * haze
    col = col + gl * (np.exp(-(e / 0.018) ** 2) * glow)[..., None] + gl * 0.35 * (np.exp(-(e / 0.07) ** 2) * glow)[..., None]
    dn = np.clip(-e, 0, 1)[..., None]
    ground = (hz * 0.45 * np.exp(-dn / 0.08) + np.array([0.010, 0.008, 0.020], np.float32)) * below
    col = np.where((e < 0)[..., None], ground + gl * (np.exp(-(e / 0.018) ** 2) * glow)[..., None], col)
    if tint is not None:
        col = col * np.asarray(tint, np.float32)
    return cv2.resize(col.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)


def gradient_bg(top, bottom, w=W_OUT, h=H_OUT):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return np.broadcast_to(np.asarray(top, np.float32) * (1 - y) + np.asarray(bottom, np.float32) * y, (h, w, 3)).copy()


# ---------------------------------------------------------------------------------- light rays, flares
def godrays(light, src, strength=0.5, decay=0.93, n=18, thresh=0.6):
    """Volumetric rays: the bright light smeared radially toward/away from its screen source."""
    s = 4
    small = cv2.resize(light, (light.shape[1] // s, light.shape[0] // s), interpolation=cv2.INTER_AREA)
    small = np.maximum(small - thresh, 0)
    cx, cy = src[0] / s, src[1] / s
    acc = np.zeros_like(small)
    wsum = 0.0
    for i in range(n):
        sc = 1.0 + 0.035 * i
        M = np.float32([[sc, 0, cx * (1 - sc)], [0, sc, cy * (1 - sc)]])
        wgt = decay ** i
        acc += cv2.warpAffine(small, M, (small.shape[1], small.shape[0]), flags=cv2.INTER_LINEAR) * wgt
        wsum += wgt
    acc = gblur(acc / wsum, 1.5)
    return cv2.resize(acc, (light.shape[1], light.shape[0]), interpolation=cv2.INTER_LINEAR) * strength


def flare(light, strength=0.5, tint=(0.55, 0.62, 1.0), thresh=2.0):
    """Anamorphic horizontal streak from the hottest light."""
    s = 4
    small = cv2.resize(light, (light.shape[1] // s, light.shape[0] // s), interpolation=cv2.INTER_AREA)
    hot = np.maximum(lum(small) - thresh, 0)
    st = cv2.GaussianBlur(hot, (0, 0), sigmaX=70, sigmaY=0.8) * 6 + cv2.GaussianBlur(hot, (0, 0), sigmaX=18, sigmaY=0.6) * 2
    st = cv2.resize(st, (light.shape[1], light.shape[0]), interpolation=cv2.INTER_LINEAR)
    return st[:, :, None] * np.asarray(tint, np.float32) * strength


def compose2(fr, t, bg=None, cards=(), rays=None, flare_k=0.0, exposure=1.0, gain=1.45, bloom_k=0.6,
             grain=0.012, vignette=0.30, fade=1.0, white=0.0):
    """compose() plus light rays from a source point, anamorphic flare, and fades to black/white."""
    far = fr.resolve('far')
    near = fr.resolve('near')
    out = far if bg is None else bg + far
    cover = np.zeros(far.shape[:2], np.float32)
    for rgb, a in cards:
        out = out * (1 - a[:, :, None]) + rgb * a[:, :, None]
        cover = np.maximum(cover, a)
    out = out + near
    # glow comes from the light only (characters are lit, they do not bloom); light behind a
    # character glows around her silhouette, not through her
    light = far * (1 - cover[:, :, None]) + near
    glow = bloom(light, bloom_k) - light
    if rays is not None:
        P, k = rays[0], rays[1]
        th = rays[2] if len(rays) > 2 else 0.6
        x, y, z, ok = fr.project(np.array([P], np.float64))
        if ok[0] and k > 0:
            glow = glow + godrays(light, (x[0], y[0]), k, thresh=th)
    if flare_k > 0:
        glow = glow + flare(light, flare_k)
    out = out + glow
    img = tonemap(out, exposure * gain)
    if white > 0:
        img = img + (1 - img) * white
    img = finish(img, t, grain, vignette)
    return img * fade


# ---------------------------------------------------------------------------------- camera
def drift(t, amp=1.0, seed=0.0):
    """Handheld breath: a small slow position wander and roll (degrees)."""
    a = seed
    dx = 0.012 * (np.sin(0.37 * t + a) + 0.5 * np.sin(0.83 * t + 2 * a))
    dy = 0.009 * (np.sin(0.29 * t + 1 + a) + 0.5 * np.sin(0.71 * t + 3 * a))
    roll = 0.45 * np.sin(0.21 * t + 0.5 + a) + 0.2 * np.sin(0.53 * t + a)
    return np.array([dx, dy, 0.0]) * amp, np.deg2rad(roll) * amp


def cam_at(pos, look, f=1300, t=0.0, amp=1.0, seed=0.0, roll=0.0):
    d, r = drift(t, amp, seed)
    return PCam.look_at(np.asarray(pos, float) + d, np.asarray(look, float) + d * 0.5, f=f, roll=r + roll)


# ---------------------------------------------------------------------------------- dust, halo
_dust = {}


def dust(fr, center, extent, t, n=500, col=WARM, inten=0.05, seed=0, rise=0.03, size=0.0):
    """Motes drifting slowly upward in the light (they are in the air the light passes through)."""
    key = (n, seed)
    if key not in _dust:
        rng = np.random.default_rng(seed)
        _dust[key] = (rng.random((n, 3)).astype(np.float32), rng.random(n).astype(np.float32) * 6.28)
    u, ph = _dust[key]
    ext = np.asarray(extent, float)
    P = np.asarray(center, float) + (u - 0.5) * ext
    P[:, 1] = np.asarray(center, float)[1] - ext[1] / 2 + ((u[:, 1] * ext[1] + rise * t) % ext[1])
    P[:, 0] += 0.02 * ext[0] * np.sin(0.4 * t + ph)
    tw = 0.6 + 0.4 * np.sin(1.3 * t + ph * 3)
    fr.points(P, col, inten * tw, size=size)


def ring_points(center, R, n=360, normal=(0, 0, 1)):
    q = np.linspace(0, 2 * np.pi, n, endpoint=False)
    nz = np.asarray(normal, float) / np.linalg.norm(normal)
    a = np.cross(nz, [0, 1, 0] if abs(nz[1]) < 0.9 else [1, 0, 0]); a /= np.linalg.norm(a)
    b = np.cross(nz, a)
    return np.asarray(center, float) + R * (np.cos(q)[:, None] * a + np.sin(q)[:, None] * b)


def halo(fr, center, R, t, col=GOLD, inten=0.25, normal=(0, 0, 1), n=420, spin=0.1, beads=True):
    """A thin ring of light with beads running around it (the stage halo behind a singer)."""
    P = ring_points(center, R, 220, normal)
    fr.polyline(np.vstack([P, P[:1]]), col, inten * 0.5, width=1.2)
    if beads:
        Q = ring_points(center, R * 1.0, n, normal)
        k = np.arange(n)
        b = 0.25 + 0.75 * (0.5 + 0.5 * np.sin(k * 0.21 + t * 2.0 + np.sin(k * 0.05)))
        Q = Q[(np.arange(n) + int(t * spin * n)) % n]
        fr.points(Q, col, inten * 0.6 * b)


# ---------------------------------------------------------------------------------- words of light
_font = {}


def font(size, italic=False, weight='Medium'):
    from PIL import ImageFont
    key = (size, italic, weight)
    if key not in _font:
        f = ImageFont.truetype(os.path.join(FONT_DIR, 'CormorantGaramond-Italic.ttf' if italic else 'CormorantGaramond.ttf'), size)
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
        _font[key] = f
    return _font[key]


class Words:
    """A word or line written in light points. Points are sampled from the rendered glyphs;
    each point knows its letter, so the line can be typed as it is sung."""

    def __init__(self, text, n=2600, italic=False, weight='Medium', seed=0, px=220):
        from PIL import Image, ImageDraw
        f = font(px, italic, weight)
        l, tp, r, b = f.getbbox(text)
        W, H = r - l + 40, b - tp + 40
        im = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(im)
        d.text((20 - l, 20 - tp), text, fill=255, font=f)
        m = np.asarray(im, np.float32) / 255.0
        # letter index by x position of each glyph's advance
        bounds = []
        for i in range(len(text)):
            bounds.append(f.getlength(text[:i + 1]))
        ys, xs = np.nonzero(m > 0.5)
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(xs), size=min(n, len(xs)), replace=False)
        x, y = xs[idx] + rng.random(len(idx)), ys[idx] + rng.random(len(idx))
        self.letter = np.searchsorted(np.array(bounds), x - 20, side='left').clip(0, len(text) - 1)
        vis = [i for i, ch in enumerate(text) if not ch.isspace()]
        rank = {c: k for k, c in enumerate(vis)}
        self.order = np.array([rank.get(int(c), 0) for c in self.letter], np.float32)
        self.nvis = max(1, len(vis))
        self.uv = np.stack([(x - W / 2) / H, -(y - H / 2) / H], 1).astype(np.float32)   # height-normalised, centred
        self.aspect = W / H
        self.rnd = rng.random((len(idx), 4)).astype(np.float32)

    def place(self, center, height, right=(1, 0, 0), up=(0, 1, 0)):
        r, u = np.asarray(right, float), np.asarray(up, float)
        return np.asarray(center, float) + self.uv[:, :1] * height * r + self.uv[:, 1:] * height * u

    def typed(self, t, t0, t1, lead=0.0):
        """Per-point arrival 0..1: letters appear in order, paced by the sung loudness between
        t0 and t1 (the line is typed as fast as it is sung)."""
        v = voice.V()
        m = (v['t'] >= t0) & (v['t'] <= t1)
        tt, ld = v['t'][m], np.clip(v['loud'][m] - 0.2, 0, None)
        c = np.cumsum(ld)
        c = c / max(c[-1], 1e-6)
        prog = float(np.interp(t + lead, tt, c)) if t + lead > t0 else 0.0
        x = prog * self.nvis - self.order
        return np.clip(x / 1.2, 0, 1)


# ---------------------------------------------------------------------------------- materialize
_noise = {}


def card_noise(h, w, seed=0, sweep='up'):
    """Formation order over the drawing: fine noise mixed with a direction, so the figure
    builds with a ragged, glowing front (bottom-up, top-down, or from the centre out)."""
    key = (h, w, seed, sweep)
    if key not in _noise:
        n = fbm_field(h // 4, w // 4, max(6, min(h, w) // 4 // 14), seed=seed, octaves=4)
        n = cv2.resize(n.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        g = {'up': 1 - ys / h, 'down': ys / h, 'radial': np.hypot(xs / w - 0.5, ys / h - 0.45) / 0.7}.get(sweep, 0 * ys)
        n = 0.45 * n + 0.55 * g
        _noise[key] = (n - n.min()) / (n.max() - n.min() + 1e-6)
    return _noise[key]


class Materialize:
    """A drawing that assembles from (or dissolves into) its own light: the figure appears in
    patches (noise threshold) while particles sampled from it fly in from a source set and burn
    bright at the forming edge."""

    def __init__(self, rgba, n=7000, seed=0, sweep='up'):
        self.h, self.w = rgba.shape[:2]
        self.N = card_noise(self.h, self.w, seed, sweep)
        self.card = Card(rgba)
        self.uv, self.col = self.card.particles(n, seed)
        iy = np.clip((self.uv[:, 1] * self.h).astype(int), 0, self.h - 1)
        ix = np.clip((self.uv[:, 0] * self.w).astype(int), 0, self.w - 1)
        self.nv = self.N[iy, ix]
        self.rnd = np.random.default_rng(seed).random((len(self.uv), 4)).astype(np.float32)

    def mask(self, k, soft=0.035):
        """Alpha multiplier for the drawing at formation k (0 nothing, 1 whole)."""
        e = k * (1 + 2 * soft) - soft
        return np.clip((e - self.N) / soft + 0.5, 0, 1)

    def draw(self, fr, pos, height, k, t, source=None, col=None, inten=0.6, yaw=0.0, pitch=0.0,
             anchor=(0.5, 1.0), window=0.3, curl=0.04, size=0.0, out_dir=None):
        """Particles for formation k. source: (N,3) start points (else a scattered cloud).
        out_dir: if given, the dissolve drifts away along this direction instead."""
        tgt = self.card.uv_to_world(self.uv, pos, height, yaw, pitch, anchor)
        e = k * (1 + 0.1) - 0.05
        u = np.clip((e - self.nv) / window + 1.0, 0, 1)          # 1 when the patch has formed
        u = u * u * (3 - 2 * u)
        if source is None:
            src = tgt + (self.rnd[:, :3] - 0.5) * height * 1.6 + np.array([0, -0.4 * height, 0])
        else:
            src = source[(np.arange(len(tgt)) * 7919) % len(source)]
        if out_dir is not None:
            src = tgt + np.asarray(out_dir, float) * (0.4 + self.rnd[:, :1]) + (self.rnd[:, 1:4] - 0.5) * height * 0.5
        P = src + (tgt - src) * u[:, None]
        P = P + curl_offset(P, t, 0.3, curl) * (1 - u[:, None])
        front = np.exp(-((e - self.nv) / 0.04) ** 2)
        c = self.col * 0.4 + WARM * 0.6 if col is None else col
        I = inten * (0.18 * (1 - u) + 1.6 * front) * ((u > 0.001) | (front > 0.05))
        fr.points(P, c, I, size=size)

    def render(self, fr, rgba, pos, height, k, fade_bottom=0.0, fade_sides=0.0, fade=None, opacity=1.0, **kw):
        """The drawing itself at formation k (rgba = this frame's living drawing).
        fade_bottom: fraction of the height over which a bust crop melts into the dark."""
        if k <= 0.001:
            return None
        im = rgba.copy()
        if k < 0.999:
            im[:, :, 3] = im[:, :, 3] * self.mask(k)
        if fade_bottom > 0:
            v = np.linspace(0, 1, self.h, dtype=np.float32)[:, None]
            im[:, :, 3] = im[:, :, 3] * np.clip((1 - v) / fade_bottom, 0, 1) ** 1.5
        if fade_sides > 0:
            u = np.linspace(0, 1, self.w, dtype=np.float32)[None, :]
            im[:, :, 3] = im[:, :, 3] * np.clip(np.minimum(u, 1 - u) / fade_sides, 0, 1) ** 1.5
        if fade is not None:                       # (left, right, top, bottom) fractions
            l_, r_, t_, b_ = fade
            u = np.linspace(0, 1, self.w, dtype=np.float32)[None, :]
            v = np.linspace(0, 1, self.h, dtype=np.float32)[:, None]
            m = np.ones((self.h, self.w), np.float32)
            if l_: m *= np.clip(u / l_, 0, 1)
            if r_: m *= np.clip((1 - u) / r_, 0, 1)
            if t_: m *= np.clip(v / t_, 0, 1)
            if b_: m *= np.clip((1 - v) / b_, 0, 1)
            im[:, :, 3] = im[:, :, 3] * m ** 1.5
        if opacity < 1.0:
            im[:, :, 3] = im[:, :, 3] * opacity
        return Card(im).render(fr, pos, height, **kw)


# ---------------------------------------------------------------------------------- poses
def pose(pos, look, f=1300.0):
    return (np.asarray(pos, float), np.asarray(look, float), float(f))


def lerp_pose(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u)


def cam_of(p, t, amp=1.0, roll=0.0):
    return cam_at(p[0], p[1], p[2], t, amp, 0.0, roll)


def space_bg(glow=1.0, w=W_OUT, h=H_OUT, center=(0.5, 0.5)):
    """Deep space: blue-black with a faint violet bloom where the world is (never pure black)."""
    ys, xs = np.mgrid[0:h // 4, 0:w // 4].astype(np.float32)
    d = np.hypot((xs / (w / 4) - center[0]) * 1.6, ys / (h / 4) - center[1])
    col = np.array([0.006, 0.007, 0.016], np.float32) + np.array([0.030, 0.018, 0.055], np.float32) * (np.exp(-(d / 0.45) ** 2) * glow)[..., None]
    return cv2.resize(col, (w, h), interpolation=cv2.INTER_LINEAR)
