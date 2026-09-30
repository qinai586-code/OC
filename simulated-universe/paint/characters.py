"""Clean character cutouts and build the three paint stages: pencil, flat, painted.

Source: the side views on reference/sheet_chatgpt.webp and reference/sheet_claude_b.webp,
cut directly from the sheets (the older assets/cut side views were cropped too tight and
carried slivers of the neighbouring 3/4 view and background). Every stage is RGBA at the requested height, so the renderer can dissolve
pencil -> flat -> painted with a noise mask.
"""
import numpy as np, cv2
from PIL import Image

ROOT = __file__.rsplit('/simulated-universe/', 1)[0]


# side views on the approved sheets: crop box, and neighbour cuts (drop x < x_min for sheet rows y0..y1)
SHEETS = {
    'A': ('reference/sheet_chatgpt.webp', (740, 0, 1028, 1000), [(784, 0, 1000), (797, 540, 1000)]),
    'B': ('reference/sheet_claude_b.webp', (560, 60, 868, 1010), [(616, 0, 1010), (642, 0, 128)]),
}


def _cut(which):
    """Cut a side view straight from its model sheet.

    Background = pale, unsaturated pixels connected to the crop border (the sheet has a soft
    vignette, so a colour threshold beats a fixed-range flood fill). Anything left of the
    neighbour cuts (the 3/4 view, panel lines, the "SIDE" label) is removed, then only the
    figure and the hair islands inside its bounding box are kept.
    """
    src, (bx0, by0, bx1, by1), cuts = SHEETS[which]
    rgb = np.array(Image.open(f'{ROOT}/{src}').convert('RGB'))[by0:by1, bx0:bx1].astype(np.float32)
    h, w = rgb.shape[:2]
    lum = rgb.mean(-1); sat = rgb.max(-1) - rgb.min(-1)
    # line art is the wall: dilated edges close the small gaps a pale shirt would leak through
    edges = cv2.dilate(cv2.Canny(lum.astype(np.uint8), 25, 70), np.ones((3, 3), np.uint8)) > 0
    cand = ((lum > 178) & (sat < 30) & ~edges).astype(np.uint8)
    n, lab = cv2.connectedComponents(cand, connectivity=4)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, border[border > 0])
    fg = ~bg
    ys, xs = np.mgrid[0:h, 0:w]
    for xm, ya, yb in cuts:
        fg &= ~((xs + bx0 < xm) & (ys + by0 >= ya) & (ys + by0 < yb))
    pale = (lum > 170) & (sat < 34)
    for _ in range(3):                                   # peel the pale rim the edge barrier left behind
        rim = fg & cv2.dilate((~fg).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & pale
        fg &= ~rim
    fg = cv2.morphologyEx(fg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, bw, bh = st[big, :4]
    keep = lab == big
    for i in range(1, n):   # detached hair strands inside the figure's box
        xi, yi, wi, hi, ar = st[i]
        if i != big and ar > 25 and xi >= x and xi + wi <= x + bw and yi >= y and yi + hi <= y + bh:
            keep |= lab == i
    keep[(ys > h * 0.9) & (lum > 150) & (sat < 25)] = False                 # floor shadow
    m = cv2.GaussianBlur(cv2.erode(keep.astype(np.uint8) * 255, np.ones((2, 2), np.uint8)), (3, 3), 0)
    solid = m > 250                                                            # pull edge colour from inside
    rgb8 = rgb.astype(np.uint8)
    fixed = cv2.inpaint(rgb8, ((m < 251) & (m > 0)).astype(np.uint8) * 255, 2, cv2.INPAINT_TELEA)
    fixed[solid] = rgb8[solid]
    out = np.dstack([fixed.astype(np.float32), m.astype(np.float32)])
    x0, y0, x1, y1 = Image.fromarray(m).getbbox()
    return out[y0:y1, x0:x1]


def stages(which, height):
    """Return dict of RGBA float32 [0,1] images: painted, flat, pencil."""
    im = _cut(which)                # the sheets already face each other: A right, B left
    s = height / im.shape[0]
    im = cv2.resize(im, (max(1, int(im.shape[1] * s)), height), interpolation=cv2.INTER_AREA)
    rgb, a = im[..., :3] / 255.0, im[..., 3:] / 255.0
    painted = np.dstack([rgb, a])
    # flat: colour quantised into a few flat fills (a first wash)
    px = (rgb.reshape(-1, 3) * 255).astype(np.float32)
    sel = a.reshape(-1) > 0.5
    k = 9
    _, lab, cen = cv2.kmeans(px[sel], k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
    q = px.copy(); q[sel] = cen[lab.ravel()]
    flat_rgb = q.reshape(rgb.shape) / 255.0
    flat_rgb = cv2.bilateralFilter(flat_rgb.astype(np.float32), 7, 0.15, 5)
    flat = np.dstack([flat_rgb * 0.85 + 0.15 * np.array([0.95, 0.93, 0.89]), a])
    # pencil: graphite contour lines from luminance edges, on transparent ground
    g = cv2.GaussianBlur((rgb.mean(-1) * 255).astype(np.uint8), (3, 3), 0)
    e = cv2.Canny(g, 40, 110).astype(np.float32) / 255.0
    outline = cv2.Canny((a[..., 0] * 255).astype(np.uint8), 50, 150).astype(np.float32) / 255.0
    line = np.clip(e * 0.7 + outline, 0, 1)
    line = cv2.GaussianBlur(line, (3, 3), 0.6)
    pencil = np.dstack([np.full(rgb.shape, 0.24), line * 0.9])
    return {'painted': painted.astype(np.float32), 'flat': flat.astype(np.float32), 'pencil': pencil.astype(np.float32)}


if __name__ == '__main__':
    import sys
    for w in 'AB':
        st = stages(w, 520)
        row = np.concatenate([st[k] for k in ('pencil', 'flat', 'painted')], 1)
        bg = np.ones(row.shape[:2] + (3,)) * np.array([0.95, 0.93, 0.89])
        comp = bg * (1 - row[..., 3:]) + row[..., :3] * row[..., 3:]
        Image.fromarray((comp * 255).astype(np.uint8)).save(sys.argv[1] + f'/stages_{w}.png')
