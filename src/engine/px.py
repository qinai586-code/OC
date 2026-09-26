"""Core pixel toolkit: crisp (never anti-aliased) drawing on RGBA numpy/PIL canvases.

Conventions
  * Native resolution is 320x180. Everything is drawn at native resolution with hard edges.
  * Colours are (r, g, b) tuples or '#rrggbb' strings.
  * Alpha is binary (0 or 255) for all artwork. Only the final post stage mixes colours
    (and only via ordered dither patterns, never blur).
"""
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw

W, H = 320, 180
SCALE = 6


def rgb(c):
    if isinstance(c, str):
        c = c.lstrip('#')
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    return tuple(int(v) for v in c[:3])


def rgba(c, a=255):
    return rgb(c) + (a,)


# ---------------------------------------------------------------- canvas
class Canvas:
    """An RGBA drawing surface. `im` is a PIL image, `a` lazily a numpy view."""

    def __init__(self, w, h, fill=None, ox=0, oy=0):
        self.w, self.h = w, h
        self.ox, self.oy = ox, oy      # drawing origin: all primitives are offset by (ox, oy)
        self.im = Image.new('RGBA', (w, h), rgba(fill) if fill is not None else (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    @classmethod
    def from_array(cls, arr):
        c = cls(arr.shape[1], arr.shape[0])
        c.im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        c.d = ImageDraw.Draw(c.im)
        return c

    def arr(self):
        return np.array(self.im)

    def set_arr(self, arr):
        self.im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        self.d = ImageDraw.Draw(self.im)

    # primitives (PIL draws without anti-aliasing)
    def px(self, x, y, c):
        x, y = int(round(x + self.ox)), int(round(y + self.oy))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im.putpixel((x, y), rgba(c))

    def fill(self, c):
        self.d.rectangle([0, 0, self.w, self.h], fill=rgba(c))

    def rect(self, x, y, w, h, c):
        x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        if w <= 0 or h <= 0:
            return
        x += self.ox
        y += self.oy
        self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=rgba(c))

    def frame(self, x, y, w, h, c):
        self.rect(x, y, w, 1, c); self.rect(x, y + h - 1, w, 1, c)
        self.rect(x, y, 1, h, c); self.rect(x + w - 1, y, 1, h, c)

    def poly(self, pts, c):
        self.d.polygon([(round(x + self.ox), round(y + self.oy)) for x, y in pts], fill=rgba(c))

    def line(self, x0, y0, x1, y1, c, width=1):
        self.d.line([(round(x0 + self.ox), round(y0 + self.oy)), (round(x1 + self.ox), round(y1 + self.oy))], fill=rgba(c), width=width)

    def lines(self, pts, c, width=1):
        self.d.line([(round(x + self.ox), round(y + self.oy)) for x, y in pts], fill=rgba(c), width=width)

    def ellipse(self, x0, y0, x1, y1, c):
        self.d.ellipse([round(x0 + self.ox), round(y0 + self.oy), round(x1 + self.ox), round(y1 + self.oy)], fill=rgba(c))

    def circle(self, cx, cy, r, c):
        if r < 0.5:
            self.px(cx, cy, c)
            return
        cx, cy = cx + self.ox, cy + self.oy
        self.d.ellipse([round(cx - r), round(cy - r), round(cx + r), round(cy + r)], fill=rgba(c))

    def ring(self, cx, cy, r, c, width=1):
        cx, cy = cx + self.ox, cy + self.oy
        self.d.ellipse([round(cx - r), round(cy - r), round(cx + r), round(cy + r)], outline=rgba(c), width=width)

    def blit(self, spr, x, y, flip=False):
        """Paste a Sprite (anchor at (x, y)) or an RGBA array (top-left at (x, y))."""
        if isinstance(spr, Sprite):
            a = spr.arr[:, ::-1] if flip else spr.arr
            ax = (spr.arr.shape[1] - 1 - spr.ax) if flip else spr.ax
            x, y = int(round(x)) - ax, int(round(y)) - spr.ay
        else:
            a = spr[:, ::-1] if flip else spr
            x, y = int(round(x)), int(round(y))
        paste(self, a, x + self.ox, y + self.oy)

    def text(self, s, x, y, c, font='5', shadow=None, align='left'):
        from .font import draw_text
        draw_text(self, s, x, y, c, font=font, shadow=shadow, align=align)

    def mask_fill(self, m, c, x=0, y=0):
        """Colour the True pixels of boolean mask m, top-left at (x, y)."""
        a = np.array(self.im)
        x, y = int(round(x + self.ox)), int(round(y + self.oy))
        h, w = m.shape
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
            a[y0:y1, x0:x1][sub] = rgba(c)
            self.set_arr(a)


def paste(canvas, a, x, y):
    """Composite RGBA array a onto canvas at integer (x, y) using binary alpha."""
    dst = np.array(canvas.im)
    h, w = a.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.w, x + w), min(canvas.h, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    src = a[y0 - y:y1 - y, x0 - x:x1 - x]
    m = src[..., 3] > 127
    reg = dst[y0:y1, x0:x1]
    reg[m] = src[m]
    canvas.set_arr(dst)


# ---------------------------------------------------------------- sprites
class Sprite:
    """RGBA array + anchor point (ax, ay), usually the point between the feet on the ground."""

    def __init__(self, arr, ax=0, ay=0):
        self.arr = arr
        self.ax, self.ay = ax, ay

    @property
    def w(self):
        return self.arr.shape[1]

    @property
    def h(self):
        return self.arr.shape[0]

    def flipped(self):
        return Sprite(self.arr[:, ::-1].copy(), self.w - 1 - self.ax, self.ay)


def parse_ascii(rows, key):
    """ASCII art -> RGBA array. `key` maps chars to colours; '.' and ' ' are transparent."""
    rows = [r for r in rows]
    h = len(rows)
    w = max(len(r) for r in rows)
    a = np.zeros((h, w, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in '. ':
                continue
            if ch not in key:
                raise KeyError(f'no colour for {ch!r} (row {y}: {r})')
            a[y, x] = rgba(key[ch])
    return a


def ascii_block(s):
    """Dedent a triple-quoted block into rows (keeps leading dots)."""
    lines = [l.rstrip() for l in s.strip('\n').split('\n')]
    ind = min((len(l) - len(l.lstrip(' ')) for l in lines if l.strip()), default=0)
    return [l[ind:] for l in lines]


# ---------------------------------------------------------------- mask helpers
def alpha(a):
    return a[..., 3] > 127


def dilate4(m):
    o = m.copy()
    o[1:] |= m[:-1]
    o[:-1] |= m[1:]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    return o


def dilate8(m):
    o = dilate4(m)
    o[1:, 1:] |= m[:-1, :-1]
    o[1:, :-1] |= m[:-1, 1:]
    o[:-1, 1:] |= m[1:, :-1]
    o[:-1, :-1] |= m[1:, 1:]
    return o


def outline(a, c, pad=1, diag=False):
    """Add a 1 px outline of colour c around the opaque region (grows the array by pad)."""
    h, w = a.shape[:2]
    b = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.uint8)
    b[pad:pad + h, pad:pad + w] = a
    m = alpha(b)
    ring = (dilate8(m) if diag else dilate4(m)) & ~m
    b[ring] = rgba(c)
    return b


def recolor(a, mapping):
    """Swap exact colours: mapping {old: new}."""
    o = a.copy()
    for old, new in mapping.items():
        oc = np.array(rgb(old), np.uint8)
        m = np.all(a[..., :3] == oc, axis=-1) & alpha(a)
        o[m, :3] = rgb(new)
    return o


def silhouette(a, c):
    o = a.copy()
    m = alpha(a)
    o[m, :3] = rgb(c)
    return o


def crop_to_content(a):
    m = alpha(a)
    ys, xs = np.where(m)
    if len(ys) == 0:
        return a, 0, 0
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return a[y0:y1, x0:x1], x0, y0


# ---------------------------------------------------------------- dithering
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32


@lru_cache(maxsize=8)
def bayer_tile(w, h):
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def dither_mask(w, h, level, ox=0, oy=0):
    """Boolean mask, True where an ordered dither of `level` (0..1) is on."""
    t = np.tile(BAYER4, (h // 4 + 2, w // 4 + 2))
    t = np.roll(np.roll(t, oy % 4, 0), ox % 4, 1)[:h, :w]
    return t < level


def dither_mix(a, b, level):
    """Ordered-dither dissolve between two RGB(A) arrays of equal shape."""
    h, w = a.shape[:2]
    m = dither_mask(w, h, level)
    o = a.copy()
    o[m] = b[m]
    return o


def to_rgb(a, bg=(0, 0, 0)):
    """Flatten RGBA onto a solid colour."""
    o = np.empty(a.shape[:2] + (3,), np.uint8)
    o[:] = rgb(bg)
    m = alpha(a)
    o[m] = a[m, :3]
    return o


def upscale(a, s=SCALE):
    return a.repeat(s, 0).repeat(s, 1)


def save_preview(a, path, s=6, bg=(40, 40, 46)):
    if a.shape[-1] == 4:
        a = to_rgb(a, bg)
    Image.fromarray(upscale(a, s)).save(path)
