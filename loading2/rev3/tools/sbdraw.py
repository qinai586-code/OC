"""Small drawing kit for rough storyboard panels (rev3).

Panels are drawn at 2x and downsampled; coordinates are in 1280x720 panel space. Every mark is
composited only inside its own bounding box. Pencil strokes are Catmull-Rom splines drawn twice with
a little jitter; washes multiply like marker; light is additive.

Figures (`girl`) are posed by joint angles with anime proportions (about 6.5 heads), and carry the
identity cues:  A: long dark hair with teal ends, teal horns, tail, dark coat, crossed clip.
                B: long wavy copper hair, star clip, cream cardigan, dark skirt.
"""
import numpy as np
import cv2

W, H, SS = 1280, 720, 2
INK = (0.16, 0.15, 0.18)
PAPER = (0.95, 0.93, 0.88)
TEAL = (0.22, 0.60, 0.58)
A_HAIR = (0.17, 0.18, 0.23)
A_COAT = (0.22, 0.22, 0.27)
B_HAIR = (0.88, 0.50, 0.26)
B_CARD = (0.92, 0.84, 0.68)
SKIN = (0.99, 0.88, 0.80)
SHIRT = (0.96, 0.96, 0.95)
GOLD = (1.0, 0.78, 0.38)
STONE = (0.66, 0.64, 0.62)
RED = (0.78, 0.18, 0.14)

_rng = np.random.default_rng(11)


def catmull(pts, n=10, closed=False):
    p = np.asarray(pts, np.float32)
    if len(p) < 3:
        return p
    if closed:
        p = np.vstack([p[-1:], p, p[:2]])
    else:
        p = np.vstack([p[0] * 2 - p[1], p, p[-1] * 2 - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(p[-2])
    return np.array(out, np.float32)


def rot(v, deg):
    a = np.radians(deg)
    return np.array([v[0] * np.cos(a) - v[1] * np.sin(a), v[0] * np.sin(a) + v[1] * np.cos(a)], np.float32)


class Board:
    def __init__(self, bg=PAPER, grain=0.018):
        self.img = np.empty((H * SS, W * SS, 3), np.float32)
        self.img[:] = bg
        g = _rng.normal(0, grain, (H * SS // 4, W * SS // 4)).astype(np.float32)
        self.img += cv2.resize(g, (W * SS, H * SS))[:, :, None]

    # ------------------------------------------------------------ ROI helpers
    def _roi(self, pts, margin):
        p = np.asarray(pts, np.float32) * SS
        x0 = int(max(np.floor(p[:, 0].min() - margin * SS), 0))
        y0 = int(max(np.floor(p[:, 1].min() - margin * SS), 0))
        x1 = int(min(np.ceil(p[:, 0].max() + margin * SS), W * SS))
        y1 = int(min(np.ceil(p[:, 1].max() + margin * SS), H * SS))
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1

    def _blend(self, roi, m, col, mode='over'):
        x0, y0, x1, y1 = roi
        if x1 <= x0 or y1 <= y0:
            return
        m = m[:, :, None]
        reg = self.img[y0:y1, x0:x1]
        c = np.array(col, np.float32)
        if mode == 'over':
            self.img[y0:y1, x0:x1] = reg * (1 - m) + c * m
        elif mode == 'mul':
            self.img[y0:y1, x0:x1] = reg * (1 - m) + reg * c * m
        elif mode == 'add':
            self.img[y0:y1, x0:x1] = reg + c * m

    def _poly_mask(self, pts, roi, blur):
        x0, y0, x1, y1 = roi
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        q = (np.asarray(pts, np.float32) * SS - [x0, y0]).astype(np.int32)
        cv2.fillPoly(m, [q], 1.0, cv2.LINE_AA)
        if blur:
            m = cv2.GaussianBlur(m, (0, 0), blur * SS)
        return m

    # ------------------------------------------------------------ marks
    def paint(self, pts, col, a=1.0, blur=0.5):
        roi = self._roi(pts, 4 * blur + 2)
        if roi is None:
            return
        self._blend(roi, self._poly_mask(pts, roi, blur) * a, col)

    def wash(self, pts, col, a=0.5, blur=1.5):
        roi = self._roi(pts, 4 * blur + 2)
        if roi is None:
            return
        self._blend(roi, self._poly_mask(pts, roi, blur) * a, col, 'mul')

    def rect(self, x0, y0, x1, y1, col, a=1.0):
        self.paint([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col, a, blur=0)

    def grad(self, top, bot, y0=0, y1=H):
        t = np.clip((np.arange(H * SS, dtype=np.float32) / SS - y0) / max(y1 - y0, 1), 0, 1)[:, None, None]
        noise = self.img - self.img.mean((0, 1))
        self.img = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t + noise
        self.img = np.broadcast_to(self.img, (H * SS, W * SS, 3)).copy()

    def line(self, pts, w=2.0, col=INK, a=0.9, smooth=True, jitter=0.45, passes=2, closed=False):
        p = catmull(pts, closed=closed) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        if closed and not smooth:
            p = np.vstack([p, p[:1]])
        roi = self._roi(p, w + 4)
        if roi is None:
            return
        x0, y0, x1, y1 = roi
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        for k in range(passes):
            q = p + _rng.normal(0, jitter, p.shape).astype(np.float32) * (k > 0)
            q = (q * SS - [x0, y0]).astype(np.int32)
            cv2.polylines(m, [q], closed and smooth, 1.0, max(1, int(round(w * SS * (1 - 0.3 * k)))), cv2.LINE_AA)
        self._blend(roi, np.clip(m, 0, 1) * a, col)

    def shape(self, pts, fill, w=2.0, col=INK, a=0.9, fa=1.0, smooth=True):
        p = catmull(pts, closed=True) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        if fill is not None:
            self.paint(p, fill, fa)
        if w > 0:
            self.line(np.vstack([p, p[:1]]), w, col, a, smooth=False)

    def ellipse(self, c, ax, ang=0, w=2.0, col=INK, a=0.9, fill=None, fa=1.0):
        pts = cv2.ellipse2Poly((int(c[0] * 8), int(c[1] * 8)), (max(1, int(ax[0] * 8)), max(1, int(ax[1] * 8))), int(ang), 0, 360, 6)
        pts = pts.astype(np.float32) / 8
        if fill is not None:
            self.paint(pts, fill, fa)
        if w > 0:
            self.line(np.vstack([pts, pts[:1]]), w, col, a, smooth=False)

    def hatch(self, pts, spacing=7, ang=45, col=INK, w=1.0, a=0.3):
        roi = self._roi(pts, 2)
        if roi is None:
            return
        x0, y0, x1, y1 = roi
        m = self._poly_mask(pts, roi, 0)
        h = np.zeros_like(m)
        d = np.radians(ang)
        L = (x1 - x0) + (y1 - y0)
        for s_ in np.arange(-L, L, spacing * SS):
            cx, cy = s_ * -np.sin(d), s_ * np.cos(d)
            cv2.line(h, (int(cx - L * np.cos(d)), int(cy - L * np.sin(d))), (int(cx + L * np.cos(d)), int(cy + L * np.sin(d))),
                     1.0, max(1, int(w * SS)), cv2.LINE_AA)
        self._blend(roi, m * h * a, col)

    def glow(self, c, r, col=GOLD, k=1.0, core=True):
        roi = self._roi([c], r * 1.6)
        if roi is None:
            return
        x0, y0, x1, y1 = roi
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d2 = ((xx - c[0] * SS) ** 2 + (yy - c[1] * SS) ** 2) / (r * SS) ** 2
        g = np.exp(-d2 * 2.2) * 0.6
        self._blend(roi, g * k, col, 'add')
        if core:
            self._blend(roi, np.exp(-d2 * 40.0) * 0.9 * k, (1.0, 0.98, 0.9), 'add')

    def arrow(self, p0, p1, col=RED, w=2.5, curve=None):
        pts = [p0, curve, p1] if curve is not None else [p0, p1]
        p = catmull(pts) if curve is not None else np.asarray(pts, np.float32)
        self.line(p, w, col, 0.85, smooth=False, passes=1)
        d = p[-1] - p[-2]
        d = d / (np.linalg.norm(d) + 1e-6)
        n = np.array([-d[1], d[0]])
        tip = p[-1]
        self.paint([tip + d * 4, tip - d * 13 + n * 7, tip - d * 13 - n * 7], col, 0.9, blur=0)

    def text(self, xy, s, size=22, col=INK, font='sans', bold=False):
        from PIL import Image, ImageDraw, ImageFont
        path = {'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''),
                'hand': '/home/user/OC/loading2/data/fonts/CormorantGaramond-Italic.ttf'}[font]
        f = ImageFont.truetype(path, size * SS)
        d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
        bx = d0.textbbox((0, 0), s, font=f)
        x0, y0 = int(xy[0] * SS), int(xy[1] * SS)
        w_, h_ = bx[2] + 4, bx[3] + 4
        im = Image.new('L', (w_, h_), 0)
        ImageDraw.Draw(im).text((0, 0), s, font=f, fill=255)
        m = np.asarray(im, np.float32) / 255
        x1, y1 = min(x0 + w_, W * SS), min(y0 + h_, H * SS)
        self._blend((x0, y0, x1, y1), m[:y1 - y0, :x1 - x0], col)

    def scribble(self, x0, y, x1, col=INK, w=1.3, a=0.8, amp=2.5, seed=0):
        """one line of handwriting"""
        r = np.random.default_rng(seed)
        xs = np.arange(x0, x1, 4.0)
        ys = y + amp * np.sin(xs * 0.8 + r.random() * 6) * r.uniform(0.4, 1.0, len(xs)) - amp * 0.6 * (np.sin(xs * 0.23) > 0.7)
        self.line(np.c_[xs, ys], w, col, a, smooth=True, jitter=0.2, passes=1)

    def frame_border(self):
        self.line([(2, 2), (W - 2, 2), (W - 2, H - 2), (2, H - 2), (2, 2)], 2.5, INK, 0.9, smooth=False, passes=1)

    def out(self):
        im = cv2.resize(np.clip(self.img, 0, 1), (W, H), interpolation=cv2.INTER_AREA)
        return (im[:, :, ::-1] * 255 + 0.5).astype(np.uint8)


# ---------------------------------------------------------------- figures
def _limb(b, p0, p1, w0, w1, col, lw):
    p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
    d = p1 - p0
    n = np.array([-d[1], d[0]], np.float32) / (np.linalg.norm(d) + 1e-6)
    poly = [p0 + n * w0, p1 + n * w1, p1 - n * w1, p0 - n * w0]
    b.paint(poly, col, 1.0)
    b.line([poly[0], poly[1]], lw, INK, 0.75, smooth=False, passes=1)
    b.line([poly[2], poly[3]], lw, INK, 0.75, smooth=False, passes=1)
    b.ellipse(p1, (w1, w1), 0, 0, fill=col)


def girl(b, who, x, y, s, view='side', facing=1, lean=0.0, head=0.0, legs='stand', stride=0.0,
         arm=(10, 10), arm2=(-10, 10), flat=False, lantern=None, glowk=0.0, hide_legs=False, hair_wind=0.0, shadow=None):
    """Posed figure. (x, y) = pelvis, s = head height in px.
    view: 'side' (profile toward `facing`), 'back' (from behind), 'front'.
    lean: torso lean forward (deg). head: head tilt (deg, + = chin up in side view).
    legs: 'stand' | 'walk' | 'sit' | 'kneel'. arm/arm2: (shoulder angle from straight down, + forward; elbow bend).
    lantern: 'near' | 'far' holds a paper lantern. flat: draw as a contour on the paper (no tone)."""
    f = facing
    lw = max(1.1, s / 26)
    P = np.array([x, y], np.float32)

    def d(angle):                      # unit vector: 0 = down, + = toward facing
        a = np.radians(angle)
        return np.array([np.sin(a) * f, np.cos(a)], np.float32)
    up = -d(-lean)                     # torso up vector
    up = np.array([up[0], up[1]], np.float32)
    up = -d(180 - lean) if False else np.array([np.sin(np.radians(lean)) * f, -np.cos(np.radians(lean))], np.float32)
    waist = P + up * 0.95 * s
    S_ = P + up * 2.15 * s            # shoulder centre
    N_ = P + up * 2.45 * s
    hc = N_ + rot(up, -head * f) * 0.62 * s
    hair = A_HAIR if who == 'A' else B_HAIR
    top = A_COAT if who == 'A' else B_CARD
    skirt_c = (0.22, 0.20, 0.24) if who == 'A' else (0.30, 0.22, 0.20)
    legc = (0.14, 0.13, 0.15)
    T = lambda c: tuple(np.array(c) * 0.25 + 0.75 * np.array(PAPER)) if flat else c   # contour: pale flat colour
    if shadow is not None:                                                            # printed shadow: one flat tone
        T = lambda c: shadow
        glowk = 0.0

    # joints
    side_off = np.array([0.0, 0.0], np.float32)
    sh_near = S_ + (np.array([0.32 * s * f * 0.3, 0]) if view == 'side' else np.array([0.55 * s, 0]))
    sh_far = S_ + (np.array([-0.32 * s * f * 0.3, 0]) if view == 'side' else np.array([-0.55 * s, 0]))
    if view == 'side':
        sh_near, sh_far = S_.copy(), S_.copy()

    def arm_pts(sh, a):
        el = sh + d(a[0]) * 1.0 * s
        wr = el + d(a[0] + a[1]) * 0.95 * s
        return el, wr

    def leg_pts(hip, kind, sgn):
        if kind == 'sit':
            kn = hip + d(90) * 1.55 * s
            an = kn + d(8 * sgn) * 1.5 * s
        elif kind == 'kneel':
            kn = hip + d(15) * 1.4 * s
            an = kn + d(-95) * 1.3 * s
        elif kind == 'walk':
            kn = hip + d(stride * sgn) * 1.6 * s
            an = kn + d(stride * sgn - (12 if sgn < 0 else 4)) * 1.55 * s
        else:
            kn = hip + d(2 * sgn) * 1.6 * s
            an = kn + d(0) * 1.55 * s
        return kn, an

    # ---------- A's tail (behind everything)
    if who == 'A':
        t0 = P + up * 0.35 * s + d(-90) * 0.25 * s
        if view == 'back':
            t0 = P + up * 0.3 * s
            tail = [t0, t0 + [0.5 * s, 0.9 * s], t0 + [0.1 * s, 1.9 * s], t0 + [-0.6 * s, 2.5 * s]]
        else:
            tail = [t0, t0 + d(-120) * 1.0 * s, t0 + d(-150) * 1.9 * s + [0, 0.4 * s], t0 + d(-170) * 2.4 * s + [0, 0.6 * s]]
        tp = catmull(tail)
        for i in range(len(tp) - 1):
            ww = s * 0.17 * (1 - 0.8 * i / len(tp)) + 1
            _limb(b, tp[i], tp[i + 1], ww, ww * 0.97, T(A_HAIR), 0.01)
        b.line(tp, lw * 0.7, INK, 0.6)
        tip = tp[-1]
        b.shape([tip + [-0.18 * s, 0], tip + [0, -0.12 * s], tip + [0.22 * s, 0.05 * s], tip + [0, 0.15 * s]], T(TEAL), lw * 0.6)

    # ---------- back hair (behind body in side/front views)
    L = (3.3 if who == 'B' else 2.9) * s
    if view in ('side', 'front'):
        back_dir = d(-180 + 0) if False else np.array([-0.25 * f, 1.0], np.float32)
        hb = [hc + rot(up, -95 * f) * 0.5 * s + up * 0.2 * s, hc - up * 0.1 * s + d(-90) * 0.55 * s,
              S_ + d(-90) * 0.55 * s + np.array([0, 0.6 * s]) + [hair_wind * s * -f, 0],
              S_ + d(-90) * 0.45 * s + np.array([0, L * 0.85]) + [hair_wind * s * -f * 1.6, 0],
              S_ + d(-90) * 0.0 * s + np.array([0, L * 0.9]) + [hair_wind * s * -f * 1.4, 0],
              S_ + d(90) * 0.15 * s + np.array([0, 0.4 * s]), hc + d(90) * 0.1 * s + up * 0.3 * s]
        if view == 'front':
            hb = [hc + [-0.55 * s, -0.1 * s], hc + [0, -0.6 * s], hc + [0.55 * s, -0.1 * s], S_ + [0.75 * s, L * 0.5],
                  S_ + [0.6 * s, L * 0.85], S_ + [-0.6 * s, L * 0.85], S_ + [-0.75 * s, L * 0.5]]
        b.shape(hb, T(hair), lw)
        if who == 'A':
            tip = np.array(hb[3]) * 0.5 + np.array(hb[4]) * 0.5
            b.shape([hb[3], hb[4], tip + [0, -0.5 * s], hb[3] + [0, -0.5 * s]], T(TEAL), 0, fa=0.7)

    # ---------- legs (far then near)
    hipn = P + np.array([0.12 * s, 0]) * (1 if view != 'side' else 0)
    hipf = P - np.array([0.12 * s, 0]) * (1 if view != 'side' else 0)
    if not hide_legs:
        for hip, sg in ((hipf, -1), (hipn, 1)):
            kn, an = leg_pts(hip, legs, sg)
            _limb(b, hip, kn, 0.21 * s, 0.15 * s, T(legc), lw * 0.8)
            _limb(b, kn, an, 0.15 * s, 0.09 * s, T(legc), lw * 0.8)
            foot = an + d(90) * 0.25 * s if view == 'side' else an + [0, 0.05 * s]
            b.shape([an + [-0.12 * s, -0.08 * s], foot + [0.08 * s, -0.04 * s], foot + [0.08 * s, 0.08 * s], an + [-0.12 * s, 0.1 * s]],
                    T((0.30, 0.20, 0.15)), lw * 0.7)
    # ---------- skirt
    if legs == 'sit' and view == 'back':
        sk = [P + [-0.62 * s, -0.4 * s], P + [0.62 * s, -0.4 * s], P + [0.78 * s, 0.14 * s], P + [-0.78 * s, 0.14 * s]]
    elif legs == 'sit':
        kn = hipn + d(90) * 1.55 * s
        sk = [waist + d(-90) * 0.4 * s, waist + d(90) * 0.35 * s, kn + d(0) * 0.2 * s + d(90) * 0.1 * s, kn + d(0) * 0.25 * s - d(90) * 0.2 * s,
              P + d(-90) * 0.45 * s + [0, 0.25 * s]]
    else:
        fl = 0.62 if view != 'side' else 0.5
        sk = [waist + [-0.36 * s, 0], waist + [0.36 * s, 0], P + up * -0.75 * s + [fl * s, 0], P + up * -0.75 * s + [-fl * s, 0]]
        if view == 'side':
            sk = [waist + d(-90) * 0.3 * s, waist + d(90) * 0.3 * s, P - up * 0.75 * s + d(90) * 0.55 * s, P - up * 0.8 * s + d(-90) * 0.5 * s]
    b.shape(sk, T(skirt_c), lw, smooth=False)
    # ---------- torso
    if view == 'side':
        tor = [N_ + d(-90) * 0.18 * s, N_ + d(90) * 0.16 * s, S_ + d(90) * 0.36 * s + up * -0.4 * s, waist + d(90) * 0.3 * s,
               P + d(90) * 0.36 * s - up * 0.15 * s, P + d(-90) * 0.38 * s - up * 0.15 * s, waist + d(-90) * 0.32 * s, S_ + d(-90) * 0.35 * s]
    else:
        tor = [N_ + [-0.15 * s, 0], N_ + [0.15 * s, 0], S_ + [0.58 * s, 0.12 * s], waist + [0.38 * s, 0], P + [0.42 * s, -0.1 * s],
               P + [-0.42 * s, -0.1 * s], waist + [-0.38 * s, 0], S_ + [-0.58 * s, 0.12 * s]]
    b.shape(tor, T(top), lw)
    if who == 'A' and view != 'back':        # white shirt front under the dark coat
        if view == 'side':
            b.shape([N_ + d(90) * 0.12 * s, S_ + d(90) * 0.3 * s + up * -0.4 * s, waist + d(90) * 0.24 * s, waist + d(90) * 0.1 * s,
                     S_ + d(90) * 0.08 * s], T(SHIRT), lw * 0.5)
        else:
            b.shape([N_ + [-0.12 * s, 0.05 * s], N_ + [0.12 * s, 0.05 * s], waist + [0.12 * s, 0], waist + [-0.12 * s, 0]], T(SHIRT), lw * 0.5)
    # ---------- arms (far arm hidden behind body in side view; both drawn in back/front)
    arms = [(sh_far, arm2, 'far'), (sh_near, arm, 'near')]
    hands = {}
    for sh, a, tag in arms:
        if view == 'side' and tag == 'far':
            el, wr = arm_pts(sh, a)
            hands[tag] = wr
            continue
        el, wr = arm_pts(sh, a)
        _limb(b, sh, el, 0.16 * s, 0.14 * s, T(top), lw * 0.8)
        _limb(b, el, wr, 0.14 * s, 0.12 * s, T(top), lw * 0.8)
        b.ellipse(wr + d(a[0] + a[1]) * 0.12 * s, (0.11 * s, 0.13 * s), 0, lw * 0.7, INK, 0.8, fill=T(SKIN))
        hands[tag] = wr + d(a[0] + a[1]) * 0.12 * s
    # ---------- head + hair
    if view == 'back':
        # long hair falling down the back: narrow at the nape, widening over the shoulder blades, with a
        # character-specific hem (B: soft waves; A: spiky strands with teal ends)
        hw = 0.40 if who == 'A' else 0.48
        n = 9
        xs = np.linspace(-(hw + 0.12), hw + 0.12, n)
        hem = []
        for k, xv in enumerate(xs):
            if who == 'B':
                yv = L * (0.93 + 0.05 * np.sin(k * 1.7))
            else:
                yv = L * (0.84 + (0.12 if k % 2 == 0 else 0.0))
            hem.append(S_ + [xv * s + hair_wind * s * (yv / L), yv])
        hb = [hc + [-0.34 * s, 0.25 * s], S_ + [-(hw - 0.08) * s, 0.0], S_ + [-(hw + 0.12) * s, L * 0.45]] + hem + \
             [S_ + [(hw + 0.12) * s, L * 0.45], S_ + [(hw - 0.08) * s, 0.0], hc + [0.34 * s, 0.25 * s]]
        b.shape(hb, T(hair), lw)
        if who == 'A':
            for k in range(0, n, 2):
                tip = hem[k]
                b.shape([tip + [-0.1 * s, -0.42 * s], tip + [0.1 * s, -0.42 * s], tip], T(TEAL), 0, fa=0.85, smooth=False)
        for k in range(6):
            u = (k + 0.5) / 6
            p0 = hc + [(-0.25 + 0.5 * u) * s, 0.1 * s]
            p1 = hem[min(int(u * n), n - 1)] + [0, -0.05 * s]
            b.line([p0, (p0 + p1) / 2 + [0.05 * s * np.sin(k * 2.3), 0], p1], lw * 0.5, INK, 0.35)
        # the head: a distinct round crown with a parting, slightly wider than the nape
        b.ellipse(hc, (0.44 * s, 0.5 * s), 0, lw, INK, 0.9, fill=T(hair))
        b.line([hc + [0, -0.48 * s], hc + [0.04 * s, -0.1 * s]], lw * 0.6, INK, 0.5)
        for sg in (-1, 1):
            b.line([hc + [0, -0.45 * s], hc + [sg * 0.25 * s, -0.25 * s], hc + [sg * 0.38 * s, 0.05 * s]], lw * 0.5, INK, 0.35)
    else:
        b.ellipse(hc, (0.41 * s, 0.5 * s), np.degrees(np.arctan2(up[0], -up[1])), lw, INK, 0.85, fill=T(SKIN))
        if view == 'side':
            fwd = rot(np.array([f, 0], np.float32), -head * f)
            upv = rot(np.array([0, -1], np.float32), -head * f)
            g = lambda u, v: hc + fwd * u * s + upv * v * s
            b.shape([g(-0.48, 0.1), g(-0.45, 0.42), g(0.05, 0.56), g(0.42, 0.3), g(0.46, 0.05), g(0.22, 0.14), g(0.0, -0.05), g(-0.15, -0.38),
                     g(-0.42, -0.3)], T(hair), lw)
            b.ellipse(g(0.27, -0.02), (0.055 * s, 0.075 * s), 0, 0, fill=(0.18, 0.5, 0.5) if who == 'A' else (0.65, 0.38, 0.1))
            b.line([g(0.40, -0.12), g(0.47, -0.2), g(0.43, -0.28)], lw * 0.6, INK, 0.7, smooth=False)
            hc_side = g
        else:
            b.shape([hc + [-0.5 * s, 0.35 * s], hc + [-0.52 * s, -0.2 * s], hc + [0, -0.58 * s], hc + [0.52 * s, -0.2 * s], hc + [0.5 * s, 0.35 * s],
                     hc + [0.33 * s, -0.12 * s], hc + [0.05 * s, -0.22 * s], hc + [-0.3 * s, -0.12 * s]], T(hair), lw)
            for ex in (-0.17, 0.17):
                b.ellipse(hc + [ex * s, 0.06 * s], (0.08 * s, 0.11 * s), 0, 0, fill=(0.18, 0.5, 0.5) if who == 'A' else (0.65, 0.38, 0.1))
                b.ellipse(hc + [ex * s + 0.025 * s, 0.01 * s], (0.025 * s, 0.03 * s), 0, 0, fill=(1, 1, 1))
            b.line([hc + [-0.05 * s, 0.3 * s], hc + [0.05 * s, 0.3 * s]], lw * 0.6, INK, 0.6, smooth=False)
    # ---------- identity marks
    if who == 'A':
        for sgn in (-1, 1):
            if view == 'side':
                base = hc + rot(up, (-25 if sgn < 0 else 20) * f) * 0.48 * s
                dirs = [rot(up, (-40 + 15 * sgn) * f), rot(up, (-80 + 15 * sgn) * f)]
            else:
                base = hc + [sgn * 0.28 * s, -0.4 * s]
                dirs = [np.array([sgn * 0.6, -1.0]), np.array([sgn * 0.1, -1.0])]
            p1 = base + dirs[0] * 0.38 * s
            p2 = p1 + dirs[1] * 0.38 * s
            hp = catmull([base, p1, p2])
            for i in range(len(hp) - 1):
                ww = s * 0.09 * (1 - 0.85 * i / len(hp)) + 0.7
                _limb(b, hp[i], hp[i + 1], ww, ww * 0.95, T(TEAL), 0.01)
            b.line(hp, lw * 0.55, INK, 0.7)
        if view != 'back':
            c = hc + (np.array([f * 0.12 * s, -0.25 * s]) if view == 'side' else np.array([0.25 * s, -0.25 * s]))
            r_ = 0.07 * s
            b.line([c - [r_, r_], c + [r_, r_]], max(1.2, s / 30), (0.3, 0.8, 0.75), 1, smooth=False, passes=1)
            b.line([c - [r_, -r_], c + [r_, -r_]], max(1.2, s / 30), (0.3, 0.8, 0.75), 1, smooth=False, passes=1)
    else:
        if view == 'back':
            c = hc + [0.32 * s, -0.22 * s]
        elif view == 'side':
            c = hc + np.array([-0.15 * f * s, -0.3 * s])
        else:
            c = hc + [0.3 * s, -0.3 * s]
        star = [c + 0.15 * s * np.array([np.cos(a), np.sin(a)]) * (1 if i % 2 == 0 else 0.45)
                for i, a in enumerate(np.linspace(-np.pi / 2, 1.5 * np.pi, 11)[:-1])]
        b.shape(star, T(GOLD), max(0.8, lw * 0.6), smooth=False)
        b.line([hc - up * 0.5 * s, hc - up * 0.78 * s + [0.12 * s, 0], hc - up * 0.7 * s + [0.2 * s, 0.05 * s]], lw * 0.7, INK, 0.7)
    # ---------- lantern
    if lantern is not None and lantern in hands:
        hp_ = hands[lantern]
        lp = hp_ + np.array([0, 0.55 * s])
        b.line([hp_, lp - [0, 0.22 * s]], max(1, lw * 0.6), INK, 0.8, smooth=False, passes=1)
        b.shape([lp + [-0.2 * s, -0.22 * s], lp + [0.2 * s, -0.22 * s], lp + [0.26 * s, 0.22 * s], lp + [-0.26 * s, 0.22 * s]],
                (1.0, 0.93, 0.72), max(1, lw * 0.7), smooth=False)
        if glowk > 0:
            b.glow(lp, s * 1.3, GOLD, glowk)
    return dict(head=hc, hands=hands, pelvis=P, shoulder=S_)


def hand(b, wrist, tip, w=26, col=SKIN, cuff=None, curl=0.12, line=INK):
    """a drawn open hand from wrist to fingertips (palm up/out)."""
    wrist, tip = np.asarray(wrist, np.float32), np.asarray(tip, np.float32)
    dv = tip - wrist
    L = float(np.linalg.norm(dv))
    dv /= L + 1e-6
    n = np.array([-dv[1], dv[0]], np.float32)
    if cuff is not None:
        b.shape([wrist + n * w * 0.62, wrist + n * w * 0.7 - dv * w * 1.6, wrist - n * w * 0.7 - dv * w * 1.6, wrist - n * w * 0.62],
                cuff, 1.6, smooth=False)
    fingers = []
    for k, off in enumerate((-0.42, -0.14, 0.14, 0.42)):
        base = wrist + dv * L * 0.52 + n * w * off
        ln = L * (0.46 if k in (1, 2) else 0.38)
        c_ = n * w * curl * (1 + k * 0.2)
        fingers.append([base, base + dv * ln * 0.55 + c_ * 0.5, base + dv * ln + c_ * 1.6])
    th = wrist + dv * L * 0.18 + n * w * 0.5
    thumb = [th, th + n * w * 0.45 + dv * L * 0.12, th + n * w * 0.5 + dv * L * 0.34]
    for fp in fingers + [thumb]:
        b.line(fp, w * 0.24, line, 0.85, passes=1)
    palm = [wrist + n * w * 0.5, wrist + dv * L * 0.55 + n * w * 0.58, wrist + dv * L * 0.6, wrist + dv * L * 0.55 - n * w * 0.58,
            wrist - n * w * 0.5]
    b.shape(palm, col, 1.8, line)
    for fp in fingers + [thumb]:
        b.line(fp, w * 0.17, col, 1.0, passes=1)


def letter(b, c, w, h, ang=0, worn=True, glow_at=None, seed=1, lifted=0.0):
    """a worn handwritten letter: creases, a stain ring, a torn corner. lifted (0..1): the last line peels
    off the paper as strokes."""
    c = np.asarray(c, np.float32)
    P = lambda u, v: c + rot(np.array([u * w / 2, v * h / 2], np.float32), ang)
    b.shape([P(-1, -1), P(0.78, -1), P(0.88, -0.86), P(1, -0.78), P(1, 1), P(-1, 1)], (0.96, 0.92, 0.79), 1.8, smooth=False)
    b.line([P(-1, 0.02), P(1, -0.02)], 1.0, INK, 0.22, smooth=False, passes=1)
    b.line([P(0.02, -1), P(-0.02, 1)], 1.0, INK, 0.22, smooth=False, passes=1)
    if worn:
        b.ellipse(P(0.5, 0.55), (w * 0.11, h * 0.09), ang, 2.2, (0.58, 0.42, 0.26), 0.35)
        b.wash([P(-1, 0.6), P(-0.6, 1), P(-1, 1)], (0.85, 0.78, 0.62), 0.6)
    rows = np.linspace(-0.72, 0.62, 6)
    for i, v in enumerate(rows):
        if lifted > 0 and i == 3:
            continue
        x0 = P(-0.8, v)
        x1 = P(0.72 - 0.35 * (i == 5), v)
        b.scribble(x0[0], x0[1], x1[0], INK, max(0.9, w / 260), 0.75, amp=max(1.4, h / 90), seed=seed + i)
    if lifted > 0:
        y = rows[3]
        for k in range(7):
            u = -0.8 + k * 0.22
            p0 = P(u, y)
            p1 = p0 + np.array([12 * k - 30, -lifted * (40 + 25 * k)], np.float32) * (w / 400)
            b.line([p1, p1 + np.array([10, -4]) * (w / 400), p1 + np.array([18, 3]) * (w / 400)], 2.0, GOLD, 0.9)
            b.glow(p1 + np.array([9, 0]) * (w / 400), 10 * w / 400, GOLD, 0.25 * lifted, core=False)
    if glow_at is not None:
        b.glow(P(*glow_at), w * 0.14, GOLD, 0.5)
    return P


def ledge(b, a, bb, vp, depth=0.12, h=40, col=STONE):
    """parapet block: near edge a->bb, receding toward vp (perspective); front face height h"""
    a, bb, vp = np.asarray(a, np.float32), np.asarray(bb, np.float32), np.asarray(vp, np.float32)
    a2 = a + (vp - a) * depth
    b2 = bb + (vp - bb) * depth
    b.shape([a, bb, bb + [0, h], a + [0, h]], tuple(np.array(col) * 0.78), 2, smooth=False)
    b.shape([a, bb, b2, a2], col, 2, smooth=False)
    for k in range(1, 7):
        u = k / 7
        p = a * (1 - u) + bb * u
        b.line([p, p + [0, h]], 1, INK, 0.25, smooth=False, passes=1)
    return a2, b2


def city(b, y_h, x0=0, x1=W, layers=3, flat_from=None, seed=3, scale=1.0, lit=0.35):
    """overlapping layers of buildings, far layers paler (atmospheric perspective).
    flat_from: buildings with x > flat_from are drawn flat (frontal outline, no shading, no depth face)."""
    r = np.random.default_rng(seed)
    for L in range(layers):
        k = L / max(layers - 1, 1)
        base = y_h + (25 + 80 * k) * scale
        tone = np.array((0.62, 0.64, 0.78)) * (1 - 0.42 * k)
        x = x0 - r.uniform(0, 40)
        while x < x1:
            wdt = r.uniform(28, 70) * (0.7 + 0.6 * k) * scale
            ht = r.uniform(30, 110) * (0.55 + 0.8 * k) * scale
            flat = flat_from is not None and x > flat_from
            pts = [(x, base), (x, base - ht), (x + wdt, base - ht), (x + wdt, base)]
            if flat:
                b.shape(pts, (0.97, 0.95, 0.90), 1.3, smooth=False)
                for wy in np.arange(base - ht + 9, base - 6, 13 * scale):
                    for wx in np.arange(x + 6, x + wdt - 6, 11 * scale):
                        if r.random() < lit:
                            b.ellipse((wx + 2, wy + 2), (2, 2), 0, 0, fill=(0.85, 0.6, 0.3))
            else:
                b.shape(pts, tuple(tone), 1.3, smooth=False)
                sd = 0.22 * wdt
                b.shape([(x + wdt, base), (x + wdt, base - ht), (x + wdt + sd, base - ht - 7 * scale), (x + wdt + sd, base - 7 * scale)],
                        tuple(tone * 0.72), 1.0, smooth=False)
                for wy in np.arange(base - ht + 8, base - 6, 12 * scale):
                    for wx in np.arange(x + 6, x + wdt - 6, 10 * scale):
                        if r.random() < lit:
                            b.rect(wx, wy, wx + 4 * scale, wy + 5 * scale, GOLD, 0.95)
            x += wdt * r.uniform(0.7, 1.0)


def traveler(b, x, y, s, step=0.0, alpha=0.55, lantern=True, glowk=0.4, col=(1.0, 0.86, 0.6)):
    """a small translucent passer-by carrying a lantern (warm silhouette). (x, y) = feet."""
    p = np.array([x, y], np.float32)
    head = p + [0, -s * 0.95]
    body = [p + [-s * 0.16, -s * 0.78], p + [s * 0.16, -s * 0.78], p + [s * 0.22, -s * 0.25], p + [-s * 0.22, -s * 0.25]]
    b.paint(body, col, alpha * 0.8)
    b.ellipse(head, (s * 0.12, s * 0.13), 0, 0, fill=col, fa=alpha)
    for sg in (-1, 1):
        k = p + [sg * s * 0.06, -s * 0.25]
        ft = p + [sg * s * 0.22 * np.sin(step + (sg > 0) * np.pi), 0]
        b.line([k, ft], max(1.0, s * 0.08), col, alpha, smooth=False, passes=1)
    if lantern:
        lp = p + [s * 0.3, -s * 0.45]
        b.ellipse(lp, (s * 0.07, s * 0.09), 0, 0, fill=(1, 0.95, 0.75))
        b.glow(lp, s * 0.6, GOLD, glowk, core=False)
    return p


def caption_card(img, lines, h=150, w=None):
    """append a caption strip under a panel image (BGR uint8)"""
    from PIL import Image, ImageDraw, ImageFont
    w = img.shape[1]
    card = Image.new('RGB', (w, h), (250, 248, 242))
    d = ImageDraw.Draw(card)
    y = 8
    for txt, size, bold, col in lines:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''), size)
        words, cur = txt.split(), ''
        for wd in words:
            t = (cur + ' ' + wd).strip()
            if d.textlength(t, font=f) > w - 20:
                d.text((10, y), cur, font=f, fill=col)
                y += size + 4
                cur = wd
            else:
                cur = t
        if cur:
            d.text((10, y), cur, font=f, fill=col)
            y += size + 6
    return np.vstack([img, np.asarray(card)[:, :, ::-1]])
