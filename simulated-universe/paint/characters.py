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


# ---------------------------------------------------------------- living rig
# Anchors in native cut pixels (read off 6x zooms of the cuts). A faces right (+x), B faces left.
ANCHORS = {
    'A': dict(face=+1, mouth=(164.5, 136.5), mouth_depth=5.0, hinge=(128, 122), chin=155, face_x=171, pivot=(140, 172),
              chest=200, waist=330, hair_x=95, hair_y=(165, 345), tail_root=(45, 545),
              breath=3.7, sway=2.9, phase=0.0),
    'B': dict(face=-1, mouth=(58.0, 139.5), mouth_depth=5.0, hinge=(98, 124), chin=153, face_x=-49, pivot=(84, 172),
              chest=200, waist=330, hair_x=168, hair_y=(150, 545), tail_root=None,
              breath=4.2, sway=3.4, phase=1.7),
}


def _ss(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x)


class Rig:
    """Live2D-style secondary motion on a single painted pose: breath, head tilt, hair and tail
    sway and a profile mouth. It gives life, not acting: new poses, blinks and expressions
    need drawn frames."""

    def __init__(self, which, height):
        self.w_ = which; self.st = stages(which, height)
        native_h = _cut(which).shape[0]; k = self.k = height / native_h
        self.A = A = {kk: v for kk, v in ANCHORS[which].items()}
        h, w = self.st['painted'].shape[:2]; self.h, self.w = h, w
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32); self.xs, self.ys = xs, ys
        yn, xn = ys / k, xs / k                                                  # native coords
        self.w_head = (1 - _ss(150, 205, yn)).astype(np.float32)
        self.w_breath = (1 - _ss(A['chest'], A['waist'], yn)).astype(np.float32)
        back = (A['hair_x'] - xn) if A['face'] > 0 else (xn - A['hair_x'])      # behind the back line
        self.w_hair = (_ss(A['hair_y'][0], A['hair_y'][1], yn) * np.clip(back / 35, 0, 1)
                       * (1 - _ss(A['hair_y'][1] - 20, A['hair_y'][1] + 30, yn))).astype(np.float32)
        # the lower jaw: below the lip line, in front of the hinge, down to just under the chin
        hx, hy = A['hinge']; ym = A['mouth'][1]; front = (xn - hx) * A['face']
        self.w_jaw = (_ss(ym - 1.0, ym + 0.8, yn) * (1 - _ss(A['chin'] + 3, A['chin'] + 15, yn))
                      * _ss(-6, 8, front) * (1 - _ss(A['face_x'] - 3, A['face_x'] + 3, front + hx * A['face']))).astype(np.float32)
        self.w_tail = None
        if A['tail_root'] is not None:                                           # the dragon tail, by colour
            rgb = (self.st['painted'][..., :3] * 255).astype(np.uint8)
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
            teal = (hsv[..., 0] > 70) & (hsv[..., 0] < 105) & (hsv[..., 1] > 35) & (yn > 520)
            dark = (hsv[..., 2] < 95) & (yn > 530) & (xn < 75)                   # the scaled upper tail
            m = cv2.dilate((teal | dark).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
            m = cv2.GaussianBlur(m, (0, 0), 6 * k)
            rx, ry = A['tail_root']
            self.w_tail = (m * np.clip(np.hypot(xn - rx, yn - ry) / 320, 0, 1)).astype(np.float32)
    JAW_DEG = 5.0                                                               # open mouth: lower lip drops ~3 px

    def _draw_opening(self, img, jaw, off=(0.0, 0.0)):
        """The mouth opening in profile, drawn after the jaw warp: a small dark shape between the
        still upper lip and the dropped lower lip, set back from the profile line. 4x supersampled."""
        if jaw < 0.05: return
        A, k, f = self.A, self.k, self.A['face']
        ex, ey = A['mouth']; hx, hy = A['hinge']
        th = np.radians(self.JAW_DEG * jaw) * f
        rx, ry = ex - hx, ey + 0.6 - hy                                              # lower lip rides the jaw
        lx, ly = hx + np.cos(th) * rx - np.sin(th) * ry, hy + np.sin(th) * rx + np.cos(th) * ry
        pts = np.array([[ex + 0.2 * f, ey - 0.1], [ex - f * A['mouth_depth'], ey + 0.45 * (ly - ey)],
                        [lx - 0.5 * f, ly], [lx + 0.1 * f, ly - 0.35 * (ly - ey)]])
        pts = pts + np.array(off) / k
        S = 4
        X0, Y0 = int((pts[:, 0].min() - 2) * k), int((pts[:, 1].min() - 2) * k)
        X1, Y1 = int((pts[:, 0].max() + 2) * k) + 1, int((pts[:, 1].max() + 2) * k) + 1
        m = np.zeros(((Y1 - Y0) * S, (X1 - X0) * S), np.float32)
        cv2.fillPoly(m, [((pts * k - [X0, Y0]) * S).astype(np.int32)], 1.0, cv2.LINE_AA)
        m = cv2.resize(m, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_AREA)[..., None] * min(1.0, jaw * 1.6)
        reg = img[Y0:Y1, X0:X1]
        yy = np.linspace(0, 1, Y1 - Y0)[:, None, None]
        col = np.array([0.26, 0.12, 0.13]) * (1 - yy) + np.array([0.42, 0.20, 0.21]) * yy    # dark, warmer low
        a = reg[..., 3:] > 0.4
        reg[..., :3] = np.where(a, reg[..., :3] * (1 - m) + col * m, reg[..., :3])

    def pose(self, t, mouth=0.0, sing=0.0):
        """Return {'painted','flat','pencil'} at time t. sing (0-1) lifts the chin a little."""
        A, k = self.A, self.k
        ph = A['phase']
        b = np.sin(2 * np.pi * t / A['breath'] + ph)
        th = np.radians(0.9 * np.sin(2 * np.pi * t / 5.3 + ph) + 1.6 * sing) * A['face'] * -1  # chin up when singing
        px, py = A['pivot'][0] * k, A['pivot'][1] * k
        c, s = np.cos(th), np.sin(th)
        rx, ry = self.xs - px, self.ys - py
        dx = ((c * rx - s * ry) - rx) * self.w_head
        dy = ((s * rx + c * ry) - ry) * self.w_head
        dy += -1.1 * k * (b * 0.5 + 0.5) * self.w_breath                               # shoulders and head rise
        wind = 0.7 + 0.3 * np.sin(2 * np.pi * t / 7.1 + ph)
        dx += 3.2 * k * wind * np.sin(2 * np.pi * t / A['sway'] - self.ys / (140 * k) + ph) * self.w_hair
        dy += 0.8 * k * np.sin(2 * np.pi * t / A['sway'] + 1.3 - self.ys / (140 * k) + ph) * self.w_hair
        if self.w_tail is not None:
            ta = np.radians(3.0 * np.sin(2 * np.pi * t / 3.3 + 0.5) + 1.2 * np.sin(2 * np.pi * t / 1.9))
            trx, try_ = A['tail_root'][0] * k, A['tail_root'][1] * k
            qx, qy = self.xs - trx, self.ys - try_
            dx += ((np.cos(ta) * qx - np.sin(ta) * qy) - qx) * self.w_tail
            dy += ((np.sin(ta) * qx + np.cos(ta) * qy) - qy) * self.w_tail
        if mouth > 0.01:                                                                # the jaw swings on its hinge
            tj = np.radians(self.JAW_DEG * mouth) * A['face']
            hx, hy = A['hinge'][0] * k, A['hinge'][1] * k
            qx, qy = self.xs - hx, self.ys - hy
            wj = self.w_jaw
            dx += ((np.cos(tj * wj) * qx - np.sin(tj * wj) * qy) - qx) * self.w_head
            dy += ((np.sin(tj * wj) * qx + np.cos(tj * wj) * qy) - qy) * self.w_head
        mx, my = (self.xs - dx).astype(np.float32), (self.ys - dy).astype(np.float32)
        out = {}
        for key in ('painted', 'flat', 'pencil'):
            out[key] = cv2.remap(self.st[key], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            if key != 'pencil' and mouth > 0.05:
                # the opening lives in warped space: carry it by the head/breath warp at the lip
                ex, ey = int(A['mouth'][0] * k), int(A['mouth'][1] * k) - 2
                self._draw_opening(out[key], mouth, (float(dx[ey, ex]), float(dy[ey, ex])))
        return out

