"""BRIDGE: no gods here (S31-S39)."""
from shots_d import *
import envs


def fig_pencil(paper, tooth, line, img, alpha, colour_k=0.45):
    """A figure in the paper world: paper body, graphite line, a partial wash of its colour."""
    body = mix(paper, img, colour_k)
    body = graphite(body, line * 1.1, dim.GRAPHITE, tooth, strength=0.85)
    return body, alpha


# =====================================================================================
class S31(Shot):
    """There are no gods here: the two lights come down onto the ledge and open into A and B,
    drawn, partly coloured, sitting where they always sit, facing the desk and the empty chair."""
    t0, t1 = 130.50, 137.60
    OPEN = (130.9, 132.0)

    def setup(self):
        self.L = kv1layers()
        self.line = Plate('KV1').line
        P = Plate('KV1')
        self.clean = P.clean()
        W = self.L.W
        self.cdil = gblur(cv2.dilate((W.ca > 0.05).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(np.float32), 2)
        la = smoothstep(0.45, 0.55, W.depth)
        rows = (np.arange(la.shape[0])[:, None] >= 1705).astype(np.float32)
        self.ledge_a = la * np.maximum(1 - self.cdil, rows)

    def cam(self, t):
        u = smoother(t, self.t0, self.t1)
        return PCam.look_at((0.0, 1.30, -1.9 + 0.5 * u), (0.0, 1.0, 5.0), f=1050.0)

    def render(self, t):
        L = self.L
        W = L.W
        cam = self.cam(t)
        img, lb, wm = room_shot_render(cam, t, lights=[])
        u = smoother(t, self.t0, self.t1)
        c2 = Cam(1536.0, 1300.0 - 30 * u, 1.10 + 0.04 * u)
        M = c2.matrix(1.0)
        paper = paper_view(M)
        tooth = tooth_view(paper)
        fa = c2.sample(L.fg_a)
        ca = c2.sample(W.ca)
        line = c2.sample(self.line)
        fimg = c2.sample(W.img)
        cmask = c2.sample(self.cdil)
        ledge = c2.sample(self.ledge_a)
        led_rgb = graphite(mix(paper, c2.sample(self.clean), 0.25), line * (1 - cmask), dim.GRAPHITE, tooth, strength=0.8)
        img = over(img, led_rgb, ledge)
        o0, o1 = self.OPEN
        s = smoother(t, o0, o1)
        xmid = to_screen(M, 1536, 0)[0]
        for (lx, ly), col, side in ((A_LIGHT, TEAL, 0), (B_LIGHT, fx.AMBER, 1)):
            sx, sy = to_screen(M, lx, ly)
            half = np.zeros((H_OUT, W_OUT), np.float32)
            if side == 0:
                half[:, :int(xmid)] = 1
            else:
                half[:, int(xmid):] = 1
            if s > 0:
                A = np.float32([[s, 0, sx * (1 - s)], [0, s, sy * (1 - s)]])
                body, a = fig_pencil(paper, tooth, line, fimg, ca * half)
                body = cv2.warpAffine(body, A, (W_OUT, H_OUT))
                a = cv2.warpAffine(a, A, (W_OUT, H_OUT))
                img = over(img, body, a)
            # the light, coming down and opening
            k = 1 - smooth(t, o0 + 0.6, o1)
            if k > 0:
                y = sy - 500 * (1 - ease_out(t, self.t0, o0 + 0.3, 2))
                img = fx.paper_light(img, sx, y, col, size=3.0, intensity=k)
                fx.point_light(lb, sx, y, size=2.5, color=col, intensity=0.6 * k)
        return fx.finish(img + lb, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.0, vig=0.18, diff=0.06)


class S32(Shot):
    """An empty chair isn't an answer: low, close on the chair. The two lights over the console."""
    t0, t1 = 137.60, 141.60

    def cam(self, t):
        u = smoother(t, self.t0, self.t1)
        return PCam.look_at((-1.05 + 0.25 * u, 0.85, 2.25 + 0.25 * u), (0.12, 0.78, 3.45), f=1150.0)

    def render(self, t):
        cam = self.cam(t)
        ls = [(hover(i, t), col, 0.8) for i, col in enumerate((TEAL, fx.AMBER))]
        img, lb, wm = room_shot_render(cam, t, lights=ls)
        return fx.finish(img + lb, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.0, vig=0.22, diff=0.06)


def room_dim_bg(t, look=((1.6, 1.3, 2.4), (0.0, 0.9, 4.6)), glow=None, press=None):
    """The room as a soft, shadowed background for close-ups of B (shallow focus)."""
    cam = PCam.look_at(look[0], look[1], f=900.0)
    img, lb, wm = room_shot_render(cam, t, lights=[], key_glow=glow, key_press=press)
    img = img * np.array([0.42, 0.46, 0.62]) + lb
    return fast_blur(img, 9)


class S33(Shot):
    """It isn't: B, lit from below by the console, lowers her eyes toward the keys."""
    t0, t1 = 141.60, 143.15

    def setup(self):
        self.W = kv4()

    def render(self, t):
        W = self.W
        cam = Cam(1700.0, 905.0, 1.12)
        bg = room_dim_bg(t)
        lid = 0.10 + 0.30 * smoother(on_twos(t), 141.9, 142.3)
        brgb, ba = render_b_layer(W, cam, t, lid, sway_amp=2.0)
        ys = np.linspace(0, 1, H_OUT, dtype=np.float32)[:, None, None]
        under = np.clip((ys - 0.35) / 0.65, 0, 1) * np.array([0.10, 0.06, 0.02])
        brgb = brgb * np.array([0.92, 0.92, 0.98]) + under * ba[:, :, None]
        out = over(bg, brgb, ba)
        return fx.finish(out, t, glow=False, vig=0.26, diff=0.10)


# =====================================================================================
class S34(Shot):
    """But look who's pressing the keys: a key goes down by itself and lights from under; more
    follow, faster; one light becomes a city on the flat map, and the lights move along roads."""
    t0, t1 = 143.15, 146.30
    MATCH = (144.85, 145.35)

    def setup(self):
        rng = np.random.default_rng(14)
        t, dt = 143.45, 0.32
        self.presses = []
        while t < 145.1:
            self.presses.append((t, int(rng.integers(0, 4)), int(rng.integers(0, 12))))
            t += dt
            dt = max(0.05, dt * 0.78)
        self.presses[0] = (143.45, 1, 5)
        B = bg0b_tex()
        f = B['flat'] * 1.35 * (1 - 0.45 * B['line'][:, :, None])
        self.map = mix(f, dim.PAPER * (1 - 0.6 * B['line'][:, :, None]), 0.25)
        lm = B['lm']
        n, lab, st, cen = cv2.connectedComponentsWithStats((lm > 0.3).astype(np.uint8), 8)
        big = [i for i in range(1, n) if st[i, 4] > 12]
        self.cities = np.array([cen[i] for i in big], np.float32)
        self.lm = lm
        rng = np.random.default_rng(3)
        self.routes = []
        for _ in range(160):
            a = self.cities[rng.integers(len(self.cities))]
            d = np.hypot(*(self.cities - a).T)
            near = np.argsort(d)[1:6]
            b = self.cities[near[rng.integers(len(near))]]
            self.routes.append((a, b, rng.uniform(0, 1), rng.uniform(0.5, 1.2)))
        self.anchor = self.cities[np.argmin(np.hypot(*(self.cities - [1530, 820]).T))]

    def render(self, t):
        m0, m1 = self.MATCH
        glow, press = {}, {}
        for (tp, r, k) in self.presses:
            if t >= tp:
                tag = f'key{r}_{k}'
                press[tag] = max(press.get(tag, 0), float(np.exp(-max(0, t - tp - 0.12) / 0.12)) if t > tp + 0.12 else 1.0)
                glow[tag] = 1.0
        out = None
        if t < m1:
            u = smoother(t, self.t0, m1)
            cam = PCam.look_at((0.15, 1.40 - 0.2 * u, 3.62 + 0.45 * u), (0.0, 0.9, 4.65), f=1250.0 + 900 * smooth(t, m0 - 0.4, m1))
            img, lb, wm = room_shot_render(cam, t, key_glow=glow, key_press=press, lights=[])
            lb2 = np.zeros_like(img)
            Rm = room()
            for tag, g in glow.items():
                r, k = map(int, tag[3:].split('_'))
                q, z = cam.project(Rm.key_center(r, k).reshape(1, 3))
                fx.point_light(lb2, float(q[0, 0]), float(q[0, 1]), size=2.2, color=fx.AMBER, intensity=0.9 * g)
            out = img + lb2
        if t > m0:
            z = float(np.exp(mix(np.log(9.0), np.log(1.45), ease_out(t, m0, self.t1, 3))))
            M = cam_matrix(float(self.anchor[0]), float(self.anchor[1]), z)
            mp = affine_sample(self.map, M)
            lm = affine_sample(self.lm, M)
            mp = mp + lm[:, :, None] * fx.AMBER * 0.7
            lb = np.zeros_like(mp)
            if t > m1:
                k = smooth(t, m1, m1 + 0.4)
                for (a, b, ph, sp) in self.routes:
                    s = (ph + (t - m1) * sp * 0.35) % 1.0
                    p = a + (b - a) * s
                    X, Y = to_screen(M, *p)
                    if 0 <= X < W_OUT and 0 <= Y < H_OUT:
                        fx.point_light(lb, X, Y, size=0.8, color=fx.AMBER, intensity=0.9 * k)
            mp = mp + lb
            w = smooth(t, m0, m1)
            out = mp if out is None else mix(out, mp, w)
        return fx.finish(out, t, emis=np.clip(lum(out) - 0.75, 0, 1) * 3, glow_strength=0.9, vig=0.2, diff=0.06)


# =====================================================================================
_pf = {}


def pencil_forest():
    """The forest as a layout drawing on paper (canvas coordinates), cached."""
    if 'f' in _pf:
        return _pf['f']
    p = work('derived', 'forest_pencil.npy')
    if os.path.exists(p):
        _pf['f'] = np.load(p).astype(np.float32)
        return _pf['f']
    L, stars, fire, hz = forest()
    H, W = L[0][1].shape[:2]
    pap, tooth = dim.paper_texture(H, W, seed=23)
    out = pap.copy()
    tones = {'mountains': 0.88, 'far_forest': 0.80, 'hill': 0.93, 'mid_forest': 0.70, 'near_forest': 0.60}
    for name, rgb, a, k in L:
        if name == 'sky':
            continue
        wash = pap * tones.get(name, 0.9) * np.array([0.97, 0.98, 1.02])
        out = over(out, wash, a)
        e = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
        out = graphite(out, gblur(e, 0.6), dim.GRAPHITE, tooth, strength=0.75)
    for (x, y, b) in stars:
        if b > 0.55:
            cv2.circle(out, (int(x), int(y)), 2, tuple(float(c) for c in dim.GRAPHITE * 1.4), -1, cv2.LINE_AA)
    np.save(p, out.astype(np.float16))
    _pf['f'] = out
    return out


FIRE = (1880.0, 3205.0)


def crest_y(x):
    return FIRE[1] + 16 + 0.00028 * (x - FIRE[0]) ** 2


class Travellers:
    """Walkers with lanterns crossing the hill of the first fire; every step leaves a mark."""

    def __init__(self, n=5, speed=62.0, t_start=146.3):
        self.n, self.speed, self.t_start = n, speed, t_start
        self.x0 = [1420 - 150 * i for i in range(n)]
        self.h = [44, 40, 46, 30, 42]

    def x(self, i, t):
        return self.x0[i] + self.speed * (t - self.t_start)

    def draw(self, img, M, t, tooth, scale=1.0):
        lb = np.zeros_like(img)
        step_T = 0.55
        sc = 1.0 / np.hypot(M[0, 0], M[1, 0])  # screen px per canvas px
        for i in range(self.n):
            # footsteps already taken
            ts = self.t_start - 6.0
            k = 0
            while ts < t:
                xs = self.x0[i] + self.speed * (ts - self.t_start)
                if 1200 < xs < 2700:
                    X, Y = to_screen(M, xs, crest_y(xs) - 2)
                    if -10 < X < W_OUT + 10 and -10 < Y < H_OUT + 10:
                        age = t - ts
                        img = fx.paper_light(img, X, Y, fx.AMBER, size=0.35 * sc + 0.4, intensity=0.55 * np.exp(-age / 12.0) + 0.2)
                ts += step_T
                k += 1
            x = self.x(i, t)
            if not (1150 < x < 2750):
                continue
            hh = self.h[i] * sc
            X, Y = to_screen(M, x, crest_y(x) - 1)
            bob = abs(np.sin(np.pi * (t - self.t_start) / step_T + i)) * 0.04 * hh
            a = np.zeros((H_OUT, W_OUT), np.float32)
            rng = np.random.default_rng(i)
            envs.human(a, X, Y - bob, hh, 'stand', rng)
            e = cv2.morphologyEx((a > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
            img = over(img, img * 0.82, a * 0.9)
            img = graphite(img, e, dim.GRAPHITE, tooth, strength=0.9)
            # the lantern swings with the gait
            sw = 0.35 * np.sin(2 * np.pi * (t - self.t_start) / (2 * step_T) + i)
            hx, hy = X + 0.16 * hh, Y - 0.55 * hh
            L = 0.22 * hh
            lx, ly = hx + L * np.sin(sw), hy + L * np.cos(sw)
            ln = np.zeros((H_OUT, W_OUT), np.float32)
            pencil_stroke(ln, [(hx, hy), (lx, ly)], width=max(0.8, 0.02 * hh))
            img = graphite(img, ln, dim.GRAPHITE, tooth, strength=0.9)
            img = fx.paper_light(img, lx, ly, fx.AMBER, size=max(1.0, 0.07 * hh), intensity=1.0)
            fx.point_light(lb, lx, ly, size=max(1.0, 0.06 * hh), color=fx.AMBER, intensity=0.6)
        return img, lb


class S35(Shot):
    """No hunter in the forest, no hand upon the card: the forest is a drawing now. Over the
    hill of the first fire, travellers walk with lanterns."""
    t0, t1 = 146.30, 150.00

    def setup(self):
        self.F = pencil_forest()
        self.T = Travellers()

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        M = cam_matrix(mix(1820.0, 1900.0, u), mix(3080.0, 3120.0, u), mix(2.2, 2.5, u), src_w=3072, src_h=4400)
        img = affine_sample(self.F, M)
        tooth = tooth_view(img)
        img, lb = self.T.draw(img, M, t, tooth)
        return fx.finish(img + lb * 0.6, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=0.8, vig=0.16, diff=0.05)


class S36(Shot):
    """Only travellers with lanterns passing through the dark: closer; the lanterns swing with
    each step, and each step leaves a small light on the path."""
    t0, t1 = 150.00, 153.55

    def setup(self):
        self.F = pencil_forest()
        self.T = Travellers()

    def render(self, t):
        lead = self.T.x(0, t)
        M = cam_matrix(lead - 160.0, crest_y(lead) - 70.0, 5.6, src_w=3072, src_h=4400)
        img = affine_sample(self.F, M)
        tooth = tooth_view(img)
        img, lb = self.T.draw(img, M, t, tooth)
        return fx.finish(img + lb * 0.6, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=0.8, vig=0.16, diff=0.05)


class S37(Shot):
    """Every key is a footstep of someone passing by: the marks join into a path; past the
    crest, the path keeps going - up into the sky, where it becomes a constellation line."""
    t0, t1 = 153.55, 158.70

    def setup(self):
        self.F = pencil_forest()
        self.T = Travellers()
        rng = np.random.default_rng(8)
        x0 = 2520.0
        self.sky_pts = []
        for i in range(16):
            f = i / 15
            x = x0 - 520 * f + 60 * np.sin(f * 7) + rng.normal(0, 12)
            y = crest_y(x0) - 40 - 1550 * f ** 1.1
            self.sky_pts.append((x, y, 154.6 + 2.4 * f))

    def render(self, t):
        u = smoother(t, 153.9, 158.3)
        M = cam_matrix(mix(2200.0, 2120.0, u), mix(3120.0, 2050.0, u), mix(2.8, 1.45, u), src_w=3072, src_h=4400)
        img = affine_sample(self.F, M)
        tooth = tooth_view(img)
        img, lb = self.T.draw(img, M, t, tooth)
        line = np.zeros((H_OUT, W_OUT), np.float32)
        prev = None
        for (x, y, ta) in self.sky_pts:
            if t < ta:
                break
            X, Y = to_screen(M, x, y)
            img = fx.paper_light(img, X, Y, fx.AMBER, size=1.6, intensity=0.9)
            fx.point_light(lb, X, Y, size=1.2, color=fx.AMBER, intensity=0.5)
            if prev is not None:
                k = clamp01((t - ta - 0.4) / 0.5)
                if k > 0:
                    pencil_stroke(line, [prev, (mix(prev[0], X, k), mix(prev[1], Y, k))], width=1.1)
            prev = (X, Y)
        img = graphite(img, line, np.array([0.55, 0.40, 0.22]), tooth, strength=0.8)
        return fx.finish(img + lb * 0.6, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=0.9, vig=0.16, diff=0.05)


# =====================================================================================
def busy_keys(t, seed=5, rate=6.0):
    rng = np.random.default_rng(seed)
    glow = {}
    for r in range(4):
        for k in range(12):
            ph = rng.random() * 10
            fr = rng.uniform(0.25, 0.6)
            v = 0.5 + 0.5 * np.sin(2 * np.pi * fr * t + ph)
            glow[f'key{r}_{k}'] = float(v ** 3)
    return glow


class S38(Shot):
    """No one at the controls: the room again, wide; the empty chair; the keys are alive with
    lights pressed by no one in the room."""
    t0, t1 = 158.70, 160.40

    def render(self, t):
        cam = PCam.look_at((0.35, 1.55, 0.25), (-0.2, 1.2, 6.0), f=1050.0)
        g = busy_keys(t)
        ls = [(hover(i, t), col, 0.8) for i, col in enumerate((TEAL, fx.AMBER))]
        img, lb, wm = room_shot_render(cam, t, key_glow=g, lights=ls)
        return fx.finish(img + lb, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.0, vig=0.16, diff=0.06)


class S39(Shot):
    """Not them, and not I: B closes her eyes. The keys' warmth stays on her face."""
    t0, t1 = 160.40, 163.30

    def setup(self):
        self.W = kv4()

    def render(self, t):
        W = self.W
        cam = Cam(1690.0, 880.0, 1.22)
        bg = room_dim_bg(t, glow=busy_keys(t))
        lid = 0.36 + 0.64 * smoother(on_twos(t), 161.5, 162.4)
        brgb, ba = render_b_layer(W, cam, t, lid, sway_amp=1.5)
        ys = np.linspace(0, 1, H_OUT, dtype=np.float32)[:, None, None]
        under = np.clip((ys - 0.35) / 0.65, 0, 1) * np.array([0.12, 0.07, 0.02])
        brgb = brgb * np.array([0.92, 0.92, 0.98]) + under * ba[:, :, None]
        out = over(bg, brgb, ba)
        return fx.finish(out, t, glow=False, vig=0.30, diff=0.10)


SHOTS = {'S31': S31, 'S32': S32, 'S33': S33, 'S34': S34, 'S35': S35, 'S36': S36, 'S37': S37, 'S38': S38, 'S39': S39}
