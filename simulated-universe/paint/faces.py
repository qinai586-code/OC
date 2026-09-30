"""Drawn face assets (assets/faces, by ChatGPT): cut-outs, aligned eye states, and a head plate
that takes a mouth state (0 closed, 1 half, 2 open) and an eye state (0 open, 1 half, 2 closed).

The mouth triptychs are pixel-locked outside the mouth, so a mouth change is a panel swap. The eye
triptychs are a separate drawing of the same head; they are aligned onto the mouth sheet (ECC,
affine) and only the eyelid edit (where eye panels 2/3 differ from panel 1) is carried across.
"""
import os, numpy as np, cv2
from PIL import Image

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'faces')


def _rgb(name):
    return np.array(Image.open(f'{DIR}/{name}.png').convert('RGB')).astype(np.float32) / 255


def cutout(rgb, keep_inside=True):
    """White-background art -> RGBA. Background = near-white connected to the border; stray strips
    at the edges are dropped by keeping the largest piece (and pieces inside its box)."""
    h, w = rgb.shape[:2]
    bgc = (rgb.min(-1) > 0.955).astype(np.uint8)
    n, lab = cv2.connectedComponents(bgc, connectivity=4)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    fg = (~np.isin(lab, border[border > 0])).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); x, y, bw, bh = st[big, :4]
    keep = lab == big
    if keep_inside:
        for i in range(1, n):
            xi, yi, wi, hi, ar = st[i]
            if i != big and ar > 15 and xi >= x and xi + wi <= x + bw and yi >= y and yi + hi <= y + bh: keep |= lab == i
    # white pockets enclosed by hair: near-white islands whose surrounding ring is mostly hair
    mn = rgb.min(-1)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(bgc, connectivity=4)
    for i in range(1, n2):
        if i in border or st2[i, 4] > 9000: continue
        reg = (lab2 == i).astype(np.uint8)
        ring = cv2.dilate(reg, np.ones((5, 5), np.uint8)).astype(bool) & ~reg.astype(bool)
        flat_white = mn[reg.astype(bool)].mean() > 0.985 and st2[i, 1] + st2[i, 3] < y + 0.55 * bh   # head area only
        if np.median(mn[ring]) < 0.80 or flat_white: keep &= ~reg.astype(bool)
    a = keep.astype(np.float32)
    # soft edge: in a 2 px band inside the silhouette, near-white pixels are partly transparent
    band = a.astype(bool) & cv2.dilate((1 - a).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    a[band] = np.clip((1 - mn[band]) / 0.30, 0, 1)
    a = cv2.GaussianBlur(a, (3, 3), 0.6)
    # un-mix the white matte from soft edges so they don't glow on a darker plate
    aa = np.clip(a, 1e-3, 1)[..., None]
    col = np.clip((rgb - (1 - aa)) / aa, 0, 1)
    col = np.where(a[..., None] > 0.98, rgb, col)
    return np.dstack([col, a]).astype(np.float32)


class Head:
    def __init__(self, who):
        self.who = who
        M = _rgb(f'{who}_mouth'); E = _rgb(f'{who}_eyes')
        P = lambda im, i: im[:, i * 512:(i + 1) * 512]
        self.mouth = [P(M, i) for i in range(3)]
        g = lambda im: cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        warp = np.eye(2, 3, dtype=np.float32)
        _, warp = cv2.findTransformECC(g(self.mouth[0]), g(P(E, 0)), warp, cv2.MOTION_AFFINE,
                                       (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
        al = lambda im: cv2.warpAffine(im, warp, (512, 1024), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderValue=(1, 1, 1))
        e = [al(P(E, i)) for i in range(3)]
        self.eye = [None]
        self.eye_mask = [None]
        for i in (1, 2):
            d = (np.abs(e[i] - e[0]).max(-1) > 0.03).astype(np.uint8)
            d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            d = cv2.dilate(d, np.ones((7, 7), np.uint8)).astype(np.float32)
            self.eye.append(e[i]); self.eye_mask.append(cv2.GaussianBlur(d, (0, 0), 3)[..., None])
        self.alpha = cutout(self.mouth[0])[..., 3]            # one silhouette for every state
        a = np.maximum(self.alpha, 0)
        for i in (1, 2): a = np.maximum(a, cutout(self.mouth[i])[..., 3])
        self.alpha = a

    def plate(self, mouth=0, eye=0):
        rgb = self.mouth[mouth].copy()
        if eye:
            m = self.eye_mask[eye]; rgb = rgb * (1 - m) + self.eye[eye] * m
        aa = np.clip(self.alpha, 1e-3, 1)[..., None]
        col = np.where(self.alpha[..., None] > 0.98, rgb, np.clip((rgb - (1 - aa)) / aa, 0, 1))
        return np.dstack([col, self.alpha]).astype(np.float32)


def pose(name):
    return cutout(_rgb(name))
