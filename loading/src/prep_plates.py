"""Prepare working plates (3072x2048) from the asset pack.

- colour-match the AI-upscaled frames to the originals (low frequencies from the original,
  crisp line detail from the upscale), so the film keeps the painted tonal balance
- upsample mattes and depth with edge-aware refinement
"""
import sys
import cv2
import numpy as np
from common import *


def colour_match(name):
    up = imread(os.path.join(UP, name + '.png'))
    org = imread(os.path.join(PACK, name + '.png'))
    H, W = up.shape[:2]
    org_up = cv2.resize(org, (W, H), interpolation=cv2.INTER_LANCZOS4)
    diff = gblur(org_up - up, 5.0)
    out = np.clip(up + diff, 0, 1)
    # keep a touch of the original's paper grain (high-pass of original) so it isn't plastic
    grain = org_up - gblur(org_up, 1.2)
    out = np.clip(out + 0.35 * grain, 0, 1)
    imwrite(work('plates', name + '.png'), out)
    return out


def refine(name, plate):
    H, W = plate.shape[:2]
    for kind in ['matte', 'depth']:
        p = os.path.join(PREP, f'{name}_{kind}.png')
        if not os.path.exists(p):
            continue
        m = imread(p)
        if m.ndim == 3:
            m = m[:, :, 0]
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_CUBIC)
        guide = lum(plate).astype(np.float32)
        r = cv2.ximgproc.guidedFilter(guide, m.astype(np.float32), 4, 2e-3)
        if not np.isfinite(r).all():
            bad = ~np.isfinite(r)
            r[bad] = m[bad]
            print(name, kind, 'guided filter non-finite px:', int(bad.sum()))
        m = np.clip(r, 0, 1)
        cv2.imwrite(work('plates', f'{name}_{kind}.png'), (m * 65535).astype(np.uint16))


if __name__ == '__main__':
    os.makedirs(work('plates'), exist_ok=True)
    only_refine = '--refine' in sys.argv
    for n in [a for a in sys.argv[1:] if not a.startswith('--')]:
        pl = imread(work('plates', n + '.png')) if only_refine else colour_match(n)
        refine(n, pl)
        print(n, 'ok', flush=True)
