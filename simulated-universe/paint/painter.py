"""The painting that finishes itself: shared painter for the backgrounds.

A scene is drawn once as three layers (pencil lines, a flat-colour label map and
an emissive light map), then composited against an attention map:
    fully painted  >  flat colour  >  pencil  >  bare paper
Everything is deterministic from the seed.
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

W, H = 1920, 1080
PAPER = np.array([243, 238, 227]) / 255.0
GRAPHITE = np.array([62, 60, 66]) / 255.0


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise(rng, scale, shape=(H, W)):
    """Value noise in 0..1 with feature size about `scale` px."""
    n = ndi.gaussian_filter(rng.random(shape), scale)
    n -= n.min()
    return n / (n.max() + 1e-9)


class Scene:
    def __init__(self, seed=1):
        self.rng = np.random.default_rng(seed)
        self.palette = [(0, 0, 0)]
        self.labels = Image.new('I', (W, H), 0)
        self.ld = ImageDraw.Draw(self.labels)
        self.pencil = Image.new('L', (W, H), 0)
        self.pd = ImageDraw.Draw(self.pencil)
        self.emit = np.zeros((H, W, 3))
        self.attn = np.zeros((H, W))
        self.sketch = Image.new('L', (W, H), 0)

    # --- flat colour regions -------------------------------------------------
    def colour(self, rgb):
        self.palette.append(rgb)
        return len(self.palette) - 1

    def rect(self, box, rgb, outline=True):
        self.ld.rectangle(box, fill=self.colour(rgb))
        if outline:
            x0, y0, x1, y1 = box
            self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])

    def poly(self, pts, rgb, outline=True):
        self.ld.polygon(pts, fill=self.colour(rgb))
        if outline:
            self.line(list(pts) + [pts[0]])

    def ellipse(self, box, rgb, outline=False):
        self.ld.ellipse(box, fill=self.colour(rgb))
        if outline:
            self.pd.ellipse(box, outline=150, width=2)

    # --- pencil --------------------------------------------------------------
    def line(self, pts, weight=150, passes=2, overshoot=10):
        """A sketched line: two jittered passes that overshoot the corners."""
        r = self.rng
        for _ in range(passes):
            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
                d = np.hypot(x1 - x0, y1 - y0) + 1e-9
                ux, uy = (x1 - x0) / d, (y1 - y0) / d
                o0, o1 = r.uniform(0, overshoot, 2)
                j = r.normal(0, 1.2, 4)
                self.pd.line([(x0 - ux * o0 + j[0], y0 - uy * o0 + j[1]),
                              (x1 + ux * o1 + j[2], y1 + uy * o1 + j[3])],
                             fill=int(weight * r.uniform(0.6, 1.0)), width=2)

    def construction(self, pts, weight=55):
        self.pd.line(pts, fill=weight, width=1)

    # --- light and attention ------------------------------------------------
    def glow(self, box, rgb, strength=1.0):
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).rectangle(box, fill=255)
        self.emit += (np.asarray(m, float)[..., None] / 255.0) * np.array(rgb) / 255.0 * strength

    def look(self, cx, cy, sigma, weight=1.0):
        yy, xx = np.mgrid[0:H, 0:W]
        self.attn += weight * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2))

    def sketched(self, box):
        """Mark an area as drawn in pencil even where nobody is looking."""
        ImageDraw.Draw(self.sketch).rectangle(box, fill=255)

    # --- composite -----------------------------------------------------------
    def render(self, t_paint=0.62, t_flat=0.40, t_pencil=0.16, attn=None):
        """Composite against the scene's own attention map, or against `attn` (an H x W array) when
        given, so a moving gaze can paint the world frame by frame. The costly layers are cached."""
        if not hasattr(self, '_cache'): self._cache = self._layers()
        c = self._cache
        return self._compose(c, self.attn if attn is None else attn, t_paint, t_flat, t_pencil)

    def _layers(self):
        r = self.rng
        lab = np.asarray(self.labels, np.int64)
        pal = np.array(self.palette, float) / 255.0
        flat = pal[lab]; flat[lab == 0] = PAPER
        wash = 1 + (noise(r, 60) - 0.5) * 0.22 + (noise(r, 9) - 0.5) * 0.08
        gran = 1 + (r.random((H, W)) - 0.5) * 0.06
        edges = ndi.gaussian_filter((ndi.sobel(lab.astype(float), 0) ** 2 + ndi.sobel(lab.astype(float), 1) ** 2 > 0).astype(float), 2.5)
        painted = flat * (wash * gran)[..., None] * (1 - 0.18 * edges)[..., None]
        light = ndi.gaussian_filter(self.emit, (60, 60, 0)) * 1.6 + ndi.gaussian_filter(self.emit, (10, 10, 0)) * 0.9
        painted = np.clip(painted + light * (0.6 + 0.4 * flat) + self.emit * 0.55, 0, 1)
        m = flat.mean(-1, keepdims=True)
        flat_tier = PAPER * (1 - 0.42 * (1 - np.clip(m + (flat - m) * 2.2, 0, 1)))
        sk = ndi.gaussian_filter(np.asarray(self.sketch, float) / 255.0, 40) + (noise(r, 25) - 0.5) * 0.3
        return dict(painted=painted.astype(np.float32), flat=flat_tier.astype(np.float32), sk=sk,
                    edge=((noise(r, 18) - 0.5) * 0.16 + (noise(r, 4) - 0.5) * 0.05).astype(np.float32),
                    pen=np.asarray(self.pencil, float) / 255.0,
                    paper=(1 + (noise(r, 1.2) - 0.5) * 0.05 + (noise(r, 40) - 0.5) * 0.04).astype(np.float32))

    def _compose(self, c, attn, t_paint, t_flat, t_pencil):
        a = np.clip(attn, 0, 1.2) + c['edge']
        w_paint = smooth(t_paint - 0.03, t_paint + 0.03, a); w_flat = smooth(t_flat - 0.03, t_flat + 0.03, a)
        w_pencil = np.maximum(smooth(t_pencil - 0.06, t_pencil + 0.06, a), smooth(0.45, 0.6, c['sk']))
        out = np.broadcast_to(PAPER, (H, W, 3)).copy()
        out = out * (1 - w_flat[..., None]) + c['flat'] * w_flat[..., None]
        out = out * (1 - w_paint[..., None]) + c['painted'] * w_paint[..., None]
        rim = np.clip(np.abs(ndi.gaussian_filter(w_paint, 1.5) - ndi.gaussian_filter(w_paint, 5)) * 3, 0, 1)
        out *= (1 - 0.10 * rim)[..., None]
        pen_vis = c['pen'] * np.maximum(w_pencil * (1 - 0.8 * w_paint), 0.35 * (c['pen'] < 0.3))
        out = out * (1 - pen_vis[..., None]) + GRAPHITE * pen_vis[..., None]
        out *= c['paper'][..., None]
        return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))

    def render_legacy(self, t_paint=0.62, t_flat=0.40, t_pencil=0.16):
        r = self.rng
        lab = np.asarray(self.labels, np.int64)
        pal = np.array(self.palette, float) / 255.0
        flat = pal[lab]
        flat[lab == 0] = PAPER

        # attention, with a ragged brush-like edge
        a = np.clip(self.attn, 0, 1.2) + (noise(r, 18) - 0.5) * 0.16 + (noise(r, 4) - 0.5) * 0.05
        w_paint = smooth(t_paint - 0.03, t_paint + 0.03, a)
        w_flat = smooth(t_flat - 0.03, t_flat + 0.03, a)
        sk = ndi.gaussian_filter(np.asarray(self.sketch, float) / 255.0, 40) + (noise(r, 25) - 0.5) * 0.3
        w_pencil = np.maximum(smooth(t_pencil - 0.06, t_pencil + 0.06, a), smooth(0.45, 0.6, sk))

        # painted: watercolour variation, granulation, edge darkening, light
        wash = 1 + (noise(r, 60) - 0.5) * 0.22 + (noise(r, 9) - 0.5) * 0.08
        gran = 1 + (r.random((H, W)) - 0.5) * 0.06
        edges = ndi.gaussian_filter((ndi.sobel(lab.astype(float), 0) ** 2 + ndi.sobel(lab.astype(float), 1) ** 2 > 0).astype(float), 2.5)
        painted = flat * (wash * gran)[..., None] * (1 - 0.18 * edges)[..., None]
        light = ndi.gaussian_filter(self.emit, (60, 60, 0)) * 1.6 + ndi.gaussian_filter(self.emit, (10, 10, 0)) * 0.9
        painted = painted + light * (0.6 + 0.4 * flat) + self.emit * 0.55
        painted = np.clip(painted, 0, 1)

        # flat tier: the same colours, unshaded, a little lighter, like a first wash
        m = flat.mean(-1, keepdims=True)
        vivid = np.clip(m + (flat - m) * 2.2, 0, 1)
        flat_tier = PAPER * (1 - 0.42 * (1 - vivid))   # a transparent tint, like a first wash

        paper_tex = 1 + (noise(r, 1.2) - 0.5) * 0.05 + (noise(r, 40) - 0.5) * 0.04
        out = np.broadcast_to(PAPER, (H, W, 3)).copy()
        out = out * (1 - w_flat[..., None]) + flat_tier * w_flat[..., None]
        out = out * (1 - w_paint[..., None]) + painted * w_paint[..., None]
        # a darker bloom where the paint stops, as watercolour does
        rim = np.clip(np.abs(ndi.gaussian_filter(w_paint, 1.5) - ndi.gaussian_filter(w_paint, 5)) * 3, 0, 1)
        out *= (1 - 0.10 * rim)[..., None]

        # pencil sits on top wherever the paint hasn't fully covered it
        pen = np.asarray(self.pencil, float) / 255.0
        pen_vis = pen * np.maximum(w_pencil * (1 - 0.8 * w_paint), 0.35 * (pen < 0.3))
        out = out * (1 - pen_vis[..., None]) + GRAPHITE * pen_vis[..., None]
        out *= paper_tex[..., None]
        return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
