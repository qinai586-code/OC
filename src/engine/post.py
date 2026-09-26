"""Post stage: native canvas -> 1920x1080 with nearest-neighbour sampling only.

The camera (centre, zoom, rotation, shake) is applied here as a nearest-neighbour resample, so pans can move
by sub-native-pixel steps at 60 fps while every native pixel stays a crisp square. Flashes and fades are
ordered-dither patterns on the native pixel grid, never blends. Lyrics are drawn on the 6x output grid.
"""
import math
from functools import lru_cache
import numpy as np
from .px import SCALE, BAYER4, rgb
from .film import MARGIN, CW, CH
from . import font

OW, OH = 1920, 1080

_X = np.arange(OW) - OW / 2 + 0.5
_Y = np.arange(OH) - OH / 2 + 0.5


def sample(img, cam, shake=(0, 0)):
    z = max(1e-3, cam.get('zoom', 1.0))
    cx = cam['x'] + MARGIN + shake[0]
    cy = cam['y'] + MARGIN + shake[1]
    rot = cam.get('rot', 0.0)
    s = SCALE * z
    if abs(rot) < 1e-4:
        ix = np.floor(cx + _X / s).astype(np.int32).clip(0, CW - 1)
        iy = np.floor(cy + _Y / s).astype(np.int32).clip(0, CH - 1)
        return img[iy[:, None], ix[None, :]]
    c, sn = math.cos(rot), math.sin(rot)
    X, Y = np.meshgrid(_X, _Y)
    u = cx + (X * c + Y * sn) / s
    v = cy + (-X * sn + Y * c) / s
    return img[np.floor(v).astype(np.int32).clip(0, CH - 1), np.floor(u).astype(np.int32).clip(0, CW - 1)]


@lru_cache(maxsize=1)
def _bayer_out():
    # dither on the 6x output grid, one threshold per native pixel
    t = np.tile(BAYER4, (OH // (4 * SCALE) + 2, OW // (4 * SCALE) + 2))
    return np.repeat(np.repeat(t, SCALE, 0), SCALE, 1)[:OH, :OW]


def dither_to(out, level, colour):
    if level <= 0:
        return out
    m = _bayer_out() < level
    out[m] = rgb(colour)
    return out


# ----------------------------------------------------------------- lyrics
LYRIC_Y = OH - 66          # top of the text line (output px)
LS = SCALE                  # 1 native px of font = 6 output px


@lru_cache(maxsize=256)
def _word_masks(text):
    return font.text_mask(text, '5')


def draw_lyrics(out, t, lyrics):
    """Word-by-word reveal of the current line, centred at the bottom."""
    line = None
    for ln in lyrics:
        s, e, txt, words = ln
        if s - 0.05 <= t < e + 0.35:
            line = ln
    if line is None:
        return out
    s, e, txt, words = line
    shown = [w for w, wt in words if t >= wt - 0.04]
    if not shown:
        return out
    full = ' '.join(w for w, _ in words)
    wfull, _ = font.text_size(full, '5')
    x0 = OW // 2 - (wfull * LS) // 2
    x0 -= x0 % LS
    cur = len(shown) - 1
    fade_out = t > e + 0.2
    x = x0
    for i, (w, wt) in enumerate(words):
        if i >= len(shown):
            break
        m = _word_masks(w)
        big = np.repeat(np.repeat(m, LS, 0), LS, 1)
        h, ww = big.shape
        col = (255, 226, 150) if (i == cur and t - wt < 0.35) else (244, 240, 232)
        if fade_out:
            col = (150, 148, 160)
        # shadow (1 native px down-right), then glyphs
        for dx, dy, c in ((LS, LS, (10, 10, 18)), (0, 0, col)):
            y0, xx = LYRIC_Y + dy, x + dx
            reg = out[y0:y0 + h, xx:xx + ww]
            reg[big[:reg.shape[0], :reg.shape[1]]] = c
        x += (font.text_size(w + ' ', '5')[0] + 1) * LS
    return out


def compose(img, post, t, lyrics=None):
    out = sample(img, post['cam'], post.get('shake', (0, 0))).copy()
    if post.get('flash', 0) > 0:
        dither_to(out, post['flash'], (250, 248, 240))
    if post.get('fade', 0) > 0:
        dither_to(out, post['fade'], (4, 4, 8))
    if lyrics is not None and post.get('lyrics', True):
        draw_lyrics(out, t, lyrics)
    return out
