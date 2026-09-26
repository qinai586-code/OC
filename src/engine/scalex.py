"""EPX / Scale2x and Scale3x pixel-art upscalers (keep hard edges, round stair-steps)."""
import numpy as np


def _key(a):
    # pack RGBA into one int for equality tests
    a = a.astype(np.uint32)
    return (a[..., 0] << 24) | (a[..., 1] << 16) | (a[..., 2] << 8) | a[..., 3]


def scale2x(a):
    k = _key(a)
    P = np.pad(k, 1, mode='edge')
    Pa = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    B, D, E, F, H = P[:-2, 1:-1], P[1:-1, :-2], P[1:-1, 1:-1], P[1:-1, 2:], P[2:, 1:-1]
    Ba, Da, Fa, Ha = Pa[:-2, 1:-1], Pa[1:-1, :-2], Pa[1:-1, 2:], Pa[2:, 1:-1]
    cond = (B != H) & (D != F)
    h, w = k.shape
    out = np.repeat(np.repeat(a, 2, 0), 2, 1).copy()
    e0 = cond & (D == B)
    e1 = cond & (B == F)
    e2 = cond & (D == H)
    e3 = cond & (H == F)
    out[0::2, 0::2][e0] = Da[e0]
    out[0::2, 1::2][e1] = Fa[e1]
    out[1::2, 0::2][e2] = Da[e2]
    out[1::2, 1::2][e3] = Fa[e3]
    return out


def scale4x(a):
    return scale2x(scale2x(a))
