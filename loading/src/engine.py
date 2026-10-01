"""Plates, layers and the multiplane camera."""
import cv2
import numpy as np
from common import *
import dimension as dim

DER = work('derived')
os.makedirs(DER, exist_ok=True)

_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def _npy(path, fn, dtype=np.float16):
    if os.path.exists(path):
        return np.load(path).astype(np.float32)
    a = fn().astype(np.float32)
    np.save(path, a.astype(dtype))
    return a


def fill_region(img, mask, scale=4):
    """Fill `mask`==1 pixels from their surroundings (inpaint at low res + grain)."""
    h, w = mask.shape
    sm_img = cv2.resize(img, (w // scale, h // scale), interpolation=cv2.INTER_AREA)
    sm_m = cv2.resize(mask, (w // scale, h // scale), interpolation=cv2.INTER_AREA)
    sm_m = (sm_m > 0.02).astype(np.uint8)
    u8 = (np.clip(sm_img, 0, 1) * 255).astype(np.uint8)
    filled = cv2.inpaint(u8, sm_m, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255.
    filled = cv2.resize(filled, (w, h), interpolation=cv2.INTER_CUBIC)
    rng = np.random.default_rng(1)
    grain = gblur(rng.normal(0, 1, (h, w)).astype(np.float32), 0.8)[:, :, None] * 0.012
    m = gblur(mask.astype(np.float32), 2.0)[:, :, None]
    return img * (1 - m) + (filled + grain) * m


class Plate:
    """A painted key frame and everything derived from it."""

    def __init__(self, name, char_dilate=9):
        self.name = name
        self.img = cached(('img', name), lambda: imread(work('plates', name + '.png')))
        self.h, self.w = self.img.shape[:2]
        mp = work('plates', name + '_matte.png')
        dp = work('plates', name + '_depth.png')
        self.matte = cached(('matte', name), lambda: imread(mp)) if os.path.exists(mp) else None
        self.depth = cached(('depth', name), lambda: imread(dp)) if os.path.exists(dp) else None
        self.char_dilate = char_dilate

    def p(self, kind):
        return os.path.join(DER, f'{self.name}_{kind}.npy')

    @property
    def line(self):
        return cached(('line', self.name), lambda: _npy(self.p('line'), lambda: dim.line_art(self.img)))

    @property
    def flat(self):
        return cached(('flat', self.name), lambda: _npy(self.p('flat'), lambda: dim.flat_cel(self.img)))

    @property
    def lights(self):
        return cached(('lights', self.name), lambda: _npy(self.p('lights'), lambda: dim.light_mask(self.img)))

    def clean(self, mask=None, key='clean'):
        """Background with the characters (or `mask`) removed."""
        def make():
            m = mask if mask is not None else self.char_alpha
            md = cv2.dilate((m > 0.05).astype(np.uint8), np.ones((self.char_dilate * 2 + 1,) * 2, np.uint8)).astype(np.float32)
            return fill_region(self.img, md)
        return cached((key, self.name), lambda: _npy(self.p(key), make))

    @property
    def char_alpha(self):
        return cached(('calpha', self.name), lambda: np.clip((self.matte - 0.08) / 0.84, 0, 1) if self.matte is not None else None)


# ---------------------------------------------------------------- camera
class Cam:
    """Camera framing in source-plate pixels. zoom=1 frames the full plate width.
    `k` per layer = parallax coefficient relative to the focus layer (1 = focus, 0 = infinitely far)."""

    def __init__(self, cx, cy, zoom=1.0, rot=0.0, ref=None, dolly=1.0):
        self.cx, self.cy, self.zoom, self.rot = cx, cy, zoom, rot
        self.ref = ref if ref is not None else (cx, cy)
        self.dolly = dolly  # multiplicative dolly factor (affects layers by k)

    def matrix(self, k=1.0, src_w=3072, src_h=2048):
        rx, ry = self.ref
        cx = rx + (self.cx - rx) * k
        cy = ry + (self.cy - ry) * k
        z = self.zoom * (self.dolly ** k)
        return cam_matrix(cx, cy, z, self.rot, src_w=src_w, src_h=src_h)

    def sample(self, img, k=1.0, interp=cv2.INTER_LINEAR, border=cv2.BORDER_REFLECT):
        h, w = img.shape[:2]
        return affine_sample(img, self.matrix(k, w, h), border=border, interp=interp)

    def sample_depth(self, img, depth, k_far=0.6, k_near=1.0, d_far=0.0, d_near=1.0):
        """Per-pixel parallax: blend the far-plane and near-plane mappings by depth."""
        h, w = img.shape[:2]
        Mf = self.matrix(k_far, w, h)
        Mn = self.matrix(k_near, w, h)
        ys, xs = np.mgrid[0:H_OUT, 0:W_OUT].astype(np.float32)
        fx = Mf[0, 0] * xs + Mf[0, 1] * ys + Mf[0, 2]
        fy = Mf[1, 0] * xs + Mf[1, 1] * ys + Mf[1, 2]
        nx = Mn[0, 0] * xs + Mn[0, 1] * ys + Mn[0, 2]
        ny = Mn[1, 0] * xs + Mn[1, 1] * ys + Mn[1, 2]
        mid_x, mid_y = (fx + nx) / 2, (fy + ny) / 2
        d = cv2.remap(depth, mid_x, mid_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        d = np.clip((d - d_far) / (d_near - d_far + 1e-6), 0, 1)
        sx = fx + (nx - fx) * d
        sy = fy + (ny - fy) * d
        return cv2.remap(img, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def lerp_cam(t, keys):
    """keys: list of (time, dict(cx,cy,zoom,rot), ease) -> Cam params at t (smoothstep between keys)."""
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (t0, p0, *_), (t1, p1, *e) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            mode = e[0] if e else 'io'
            if mode == 'lin':
                w = lin(t, t0, t1)
            elif mode == 'out':
                w = ease_out(t, t0, t1)
            elif mode == 'in':
                w = ease_in(t, t0, t1, 2)
            else:
                w = smoother(t, t0, t1)
            out = {}
            for k in p0:
                if k == 'zoom':  # interpolate zoom geometrically
                    out[k] = float(np.exp(np.log(p0[k]) + (np.log(p1[k]) - np.log(p0[k])) * w))
                else:
                    out[k] = p0[k] + (p1[k] - p0[k]) * w
            return out
    return dict(keys[-1][1])


# ---------------------------------------------------------------- character acting helpers
def flow_between(a, b, region=None):
    """Dense flow a->b (on luminance), for in-betweening two drawn states."""
    ga = (lum(a) * 255).astype(np.uint8)
    gb = (lum(b) * 255).astype(np.uint8)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST * 0 + 2)
    f = dis.calc(ga, gb, None)
    if region is not None:
        f = f * region[:, :, None]
    return f


def inbetween(a, b, flow, s):
    """Frame at fraction s between drawings a and b (flow a->b)."""
    h, w = a.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    # backward warp approximations
    wa = cv2.remap(a, xs - flow[:, :, 0] * s, ys - flow[:, :, 1] * s, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    wb = cv2.remap(b, xs + flow[:, :, 0] * (1 - s), ys + flow[:, :, 1] * (1 - s), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return wa * (1 - s) + wb * s


def on_twos(t, fps=FPS):
    """Quantise time to drawings held for two frames (anime character timing)."""
    return np.floor(t * fps / 2) * 2 / fps


def sway_field(shape, weight, t, amp=4.0, freq=0.35, wavelen=380.0, axis_pt=(0, 0), seed=0, gust=None):
    """Displacement for hair/ribbons: a travelling wave down the strands (follow-through),
    weighted toward the tips. Returns (dx, dy) in plate pixels."""
    h, w = shape
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dist = np.hypot(xs - axis_pt[0], ys - axis_pt[1])
    ph = 2 * np.pi * (freq * t) - dist / wavelen * 2 * np.pi
    g = 1.0 if gust is None else gust
    dx = amp * g * weight * (np.sin(ph + seed) * 0.8 + 0.2 * np.sin(2.3 * ph + 1.7 + seed))
    dy = amp * 0.25 * g * weight * np.cos(ph * 0.7 + seed)
    return dx.astype(np.float32), dy.astype(np.float32)


def apply_disp(img, dx, dy):
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(img, xs - dx, ys - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
