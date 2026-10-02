"""Clean RGBA layers from drawings on a white background (rev3).

alpha = max(isnet-anime segmentation, ink-vs-white key) inside a dilated isnet region, so the gaps
between hair strands that show the white paper become transparent instead of a white fringe. Edge
colours are un-mixed from white (C = (I - (1 - a) * white) / a) and then pulled from the nearest
solid interior colour, so no light halo remains when the layer sits on a dark night background.

  python3 rev3/tools/matte.py SRC.png OUT.png [--crop x0 y0 x1 y1]
"""
import os
import sys

import cv2
import numpy as np
import onnxruntime as ort

MODEL = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad/models/isnet-anime.onnx'
_seg = None


def isnet(img):
    global _seg
    if _seg is None:
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        _seg = ort.InferenceSession(MODEL, so, providers=['CPUExecutionProvider'])
    x = cv2.resize(img, (1024, 1024), interpolation=cv2.INTER_AREA) - 0.5
    m = _seg.run(None, {_seg.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = (m - m.min()) / (m.max() - m.min() + 1e-9)
    return cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC).clip(0, 1)


def matte_white(img, core_erode=5, paper_zones=()):
    """img float32 RGB 0..1 on white. Returns RGBA float32 (straight colour).

    Coloured pixels (skin, teal hair, horns, eyes) and the confident interior are opaque. Neutral light
    pixels outside the interior (paper showing between strands, the soft grey halo around the line art)
    get alpha from their darkness relative to the nearby ink, and take the ink's colour, so on a dark
    background they read as a faint line instead of a light fringe."""
    seg = isnet(img)
    lum = cv2.GaussianBlur(img.mean(2), (3, 3), 0)
    chroma = img.max(2) - img.min(2)
    core = cv2.erode((seg > 0.9).astype(np.uint8), np.ones((2 * core_erode + 1,) * 2, np.uint8)) > 0
    region = cv2.dilate((seg > 0.25).astype(np.uint8), np.ones((11, 11), np.uint8)) > 0
    k = np.ones((11, 11), np.uint8)
    inkmin = np.minimum(cv2.erode(lum, k), 0.6)
    a_lin = np.clip((1 - lum) / (1 - inkmin + 1e-3), 0, 1)
    coloured = (chroma > 0.07) & (lum < 0.97)
    a = np.where(core | coloured, 1.0, a_lin) * region
    a = np.where(region, a, 0.0).astype(np.float32)
    # colour for the semi-transparent neutral band: the nearby ink colour (per-channel local minimum)
    ink = np.dstack([cv2.erode(img[:, :, c], k) for c in range(3)])
    band = (~core) & (~coloured)
    rgb = img.copy()
    rgb[band] = ink[band]
    # opaque pixels that are neutral and very light but outside the core: paper between strands
    paper = band & (lum > 0.9)
    a[paper] = np.minimum(a[paper], a_lin[paper])
    # optional zones (e.g. side hair of a cropped head) where light neutral pixels inside the interior
    # are paper seen between strands, not shirt or eye white
    for x0, y0, x1, y1 in paper_zones:
        z = np.zeros_like(core)
        z[y0:y1, x0:x1] = True
        pz = z & (lum > 0.80) & (chroma < 0.06)
        a[pz] = np.minimum(a[pz], a_lin[pz])
        rgb[pz] = ink[pz]
    # smooth only the semi-transparent band (removes speckle), keep the interior crisp
    ab = cv2.GaussianBlur(a, (5, 5), 0)
    a = np.where(band | (a < 0.999), ab, a)
    a = cv2.GaussianBlur(a, (3, 3), 0).clip(0, 1)
    return np.dstack([rgb, a]).astype(np.float32)


def load_rgb(path):
    return cv2.imread(path)[:, :, ::-1].astype(np.float32) / 255.0


def save_rgba(path, rgba):
    out = (np.clip(rgba, 0, 1) * 65535 + 0.5).astype(np.uint16)
    cv2.imwrite(path, out[:, :, [2, 1, 0, 3]])


def load_rgba(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32)
    a /= 65535.0 if a.max() > 255 else 255.0
    return a[:, :, [2, 1, 0, 3]]


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    img = load_rgb(src)
    if '--crop' in sys.argv:
        x0, y0, x1, y1 = map(int, sys.argv[sys.argv.index('--crop') + 1:][:4])
        img = img[y0:y1, x0:x1]
    zones = []
    if '--paper' in sys.argv:
        v = list(map(int, sys.argv[sys.argv.index('--paper') + 1].split(',')))
        zones = [tuple(v[i:i + 4]) for i in range(0, len(v), 4)]
    save_rgba(out, matte_white(img, paper_zones=zones))
    print('wrote', out, img.shape)
