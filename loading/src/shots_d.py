"""CHORUS 2: who wrote the verse (S25-S30)."""
from shots_c import *
from room import Room
from proj import PCam

_room = {}


def room(cutaway=False):
    if cutaway not in _room:
        _room[cutaway] = Room(cutaway=cutaway)
    return _room[cutaway]


def window_view(cam, R, t, win_mask, out, earth=True):
    """Beyond the window: the painted universe they came from, small enough to fit in it."""
    if win_mask.max() <= 0:
        return out
    ys, xs = np.nonzero(win_mask > 0.5)
    if len(xs) == 0:
        return out
    cx, cy = xs.mean(), ys.mean()
    hgt = ys.max() - ys.min() + 1
    sky = space_bg(9) * 1.2
    if earth:
        B = bg0b_tex()
        r = max(6.0, hgt * 0.16)
        g, gm, _ = proj.raycast_globe(B['t'], W_OUT, H_OUT, cx + hgt * 0.12, cy + hgt * 0.18, r, 150 + 6 * t, 20.0, bg=sky)
        lb = np.zeros_like(g)
        atmosphere(lb, cx + hgt * 0.12, cy + hgt * 0.18, r, 0.8)
        sky = g + lb
    return out * (1 - win_mask[:, :, None]) + sky * win_mask[:, :, None]


def flight_lights(buf, t, pts_fn, cols, n_trail=14, dt=0.03, size=2.0):
    for i, col in enumerate(cols):
        for j in range(n_trail):
            x, y = pts_fn(i, t - j * dt)
            if j == 0:
                fx.point_light(buf, x, y, size=size, color=col, intensity=1.4)
            else:
                fx.splat(buf, x, y, size * 0.9, col, 0.30 * (1 - j / n_trail))


# =====================================================================================
class S25(Shot):
    """So if we live in a simulated universe: the two lights climb; the flat world falls away
    beneath them. B's light turns back once - toward it - then follows."""
    t0, t1 = 108.40, 112.05

    def setup(self):
        B = bg0b_tex()
        f = B['flat'] * 1.35 * (1 - 0.45 * B['line'][:, :, None])
        f = mix(f, dim.PAPER * (1 - 0.6 * B['line'][:, :, None]), 0.18) + B['lm'][:, :, None] * fx.AMBER * 0.7
        self.tex = cv2.resize(f, (1536, 1024), interpolation=cv2.INTER_AREA)
        self.stars = __import__('envs').starfield(H_OUT * 3, W_OUT, n=2600, seed=21, bright=0.9)[0]

    def pos(self, i, t):
        u = t - self.t0
        if i == 0:
            return 870 + 70 * np.sin(1.3 * u), 980 - 190 * u
        bump = np.exp(-((u - 1.9) / 0.38) ** 2)
        return 1050 + 60 * np.sin(1.1 * u + 1) + 150 * bump, 1000 - 190 * u + 260 * bump

    def render(self, t):
        u = t - self.t0
        # the sky slides down as they climb (stars far: slow)
        off = int(H_OUT * 2 - 120 * u) % (H_OUT * 2)
        sky = self.stars[off:off + H_OUT] + np.array([0.012, 0.016, 0.04])
        out = sky.copy()
        pc = PCam(pos=(0, 0, 0), pitch=0.38, f=1300.0)
        h = 2.2 + 6.0 * u ** 1.6
        D, Wd = 70.0, 110.0
        quad = np.array([(-Wd / 2, -h, D), (Wd / 2, -h, D), (Wd / 2, -h, 1.0), (-Wd / 2, -h, 1.0)])
        q, z = pc.project(quad)
        out, pa, _ = proj.warp_quad(out, self.tex, q, opacity=1.0)
        e = np.zeros((H_OUT, W_OUT), np.float32)
        pencil_stroke(e, [q[0], q[1]], width=1.2)
        out = out + e[:, :, None] * np.array([0.9, 0.88, 0.84]) * 0.6
        lb = np.zeros_like(out)
        flight_lights(lb, t, self.pos, [TEAL, fx.AMBER])
        out = out + lb
        return fx.finish(out, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.3, vig=0.26, diff=0.10)


class S26(Shot):
    """We flew out past the stars to find who wrote the verse: stars stream past; ahead, the
    pencil-drawn wall; the lights fly into the paper."""
    t0, t1 = 112.05, 115.65

    def setup(self):
        rng = np.random.default_rng(4)
        n = 900
        self.sx = rng.uniform(-1, 1, n) * 2.2
        self.sy = rng.uniform(-1, 1, n) * 1.3
        self.sz = rng.uniform(0.2, 6.0, n)
        self.sb = rng.random(n) ** 2

    def pos(self, i, t):
        u = t - self.t0
        k = smooth(t, 114.4, 115.5)
        x0, y0 = (900 + 50 * np.sin(1.5 * u), 600 + 30 * np.sin(1.1 * u)) if i == 0 else (1030 + 50 * np.sin(1.3 * u + 2), 610 + 30 * np.sin(0.9 * u + 1))
        return mix(x0, 960 + (i - 0.5) * 30, k), mix(y0, 540, k)

    def render(self, t):
        u = t - self.t0
        out = np.ones((H_OUT, W_OUT, 3), np.float32) * np.array([0.010, 0.013, 0.035])
        lb = np.zeros_like(out)
        speed = 1.2 + 1.6 * u
        z = (self.sz - (u * 1.2 + 0.8 * u * u)) % 6.0 + 0.05
        f = 700.0
        for x, y, zz, b in zip(self.sx, self.sy, z, self.sb):
            X, Y = 960 + f * x / zz, 540 + f * y / zz
            if 0 <= X < W_OUT and 0 <= Y < H_OUT:
                streak = min(40.0, speed * 30 / zz)
                d = np.array([X - 960, Y - 540])
                d = d / (np.linalg.norm(d) + 1e-6)
                a = np.zeros((H_OUT, W_OUT), np.float32)
                fx.splat(lb, X, Y, 0.6, (0.8, 0.86, 1.0), 0.5 * b * min(1, 1.5 / zz))
                if streak > 3:
                    for s_ in np.linspace(0, 1, 6):
                        fx.splat(lb, X - d[0] * streak * s_, Y - d[1] * streak * s_, 0.5, (0.8, 0.86, 1.0), 0.12 * b * (1 - s_))
        # the wall ahead: a pencil circle opening onto paper
        r = 30 + 1300 * ease_in(t, 112.6, 115.45, 3)
        ys, xs = np.ogrid[0:H_OUT, 0:W_OUT]
        d = np.sqrt((xs - 960.0) ** 2 + (ys - 540.0) ** 2)
        inside = smoothstep(r + 1.5, r - 1.5, d)
        paper = paper_view(cam_matrix(1536, 1024, min(1.6, 0.6 + 0.4 * u)))
        out = out * (1 - inside[:, :, None]) + paper * inside[:, :, None]
        c = np.zeros((H_OUT, W_OUT), np.float32)
        pts = [(960 + r * np.cos(a), 540 + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 360)]
        pencil_stroke(c, pts, width=1.6, jitter=0.4, seed=3)
        out = graphite(out, c, dim.GRAPHITE, None, strength=0.6) + c[:, :, None] * np.array([0.5, 0.55, 0.7]) * (1 - inside[:, :, None]) * 0.5
        out = out + lb * (1 - inside[:, :, None])
        lb2 = np.zeros_like(out)
        flight_lights(lb2, t, self.pos, [TEAL, fx.AMBER], n_trail=18, dt=0.04)
        for i, col in enumerate((TEAL, fx.AMBER)):
            x, y = self.pos(i, t)
            ins = float(inside[int(np.clip(y, 0, H_OUT - 1)), int(np.clip(x, 0, W_OUT - 1))])
            if ins > 0.01:
                out = mix(out, fx.paper_light(out.copy(), x, y, col, size=3.6, intensity=1.0), ins)
        out = out + lb2 * (1 - 0.7 * inside[:, :, None])
        return fx.finish(out, t, emis=np.clip(lum(lb2) * 2 + lum(lb), 0, 1), glow_strength=1.2, vig=0.22, diff=0.08)


# =====================================================================================
def room_shot_render(cam, t, key_glow=None, lights=(), reveal=None, window=True, room_obj=None, ink=1.0, key_press=None):
    Rm = room_obj or room()
    M = cam_matrix(1536, 1024, 1.0)
    paper = paper_view(M)
    tooth = tooth_view(paper)
    lp = [(p, c, s_) for (p, c, s_) in lights]
    img, wm = Rm.render(cam, paper, tooth, t=t, key_glow=key_glow, light_pos=lp, reveal=reveal, ink=ink, key_press=key_press)
    if window:
        img = window_view(cam, Rm, t, wm, img)
    lb = np.zeros_like(img)
    for (p, c, s_) in lights:
        q, z = cam.project(np.array([p]))
        if z[0] > 0.05:
            sz = max(1.2, 4.0 / max(z[0], 0.3))
            img = fx.paper_light(img, float(q[0, 0]), float(q[0, 1]), c, size=sz, intensity=s_)
            fx.point_light(lb, float(q[0, 0]), float(q[0, 1]), size=sz, color=c, intensity=0.5 * s_)
    return img, lb, wm


LIGHT_HOVER = (np.array([-0.18, 1.25, 4.45]), np.array([0.20, 1.22, 4.5]))


def hover(i, t):
    p = LIGHT_HOVER[i].copy()
    p[1] += 0.03 * np.sin(t * 1.7 + i * 2.0)
    p[0] += 0.02 * np.sin(t * 1.1 + i)
    return p


class S27(Shot):
    """A room at the end of the light: on the paper the room draws itself; the two lights come
    in past us and slow above the console."""
    t0, t1 = 115.65, 118.60

    def cam(self, t):
        u = smoother(t, self.t0, self.t1)
        return PCam.look_at((0.5 - 0.2 * u, 1.55, 0.35 - 0.3 * u), (-0.2, 1.2, 6.0), f=1050.0)

    def render(self, t):
        cam = self.cam(t)
        def reveal(c, tag):
            d = np.linalg.norm(c - np.array([0.0, 1.2, 5.0]))
            return float(np.clip((t - 115.75 - d * 0.28) / 0.45, 0, 1))
        ls = []
        for i, col in enumerate((TEAL, fx.AMBER)):
            a = ease_out(t, 116.6 + 0.2 * i, 118.3, 3)
            start = np.array([(-0.3 if i == 0 else 0.5), 1.4, 0.4])
            p = start + (hover(i, t) - start) * a
            ls.append((p, col, smooth(t, 116.6 + 0.2 * i, 116.9 + 0.2 * i)))
        img, lb, wm = room_shot_render(cam, t, lights=ls, reveal=reveal)
        out = img + lb
        return fx.finish(out, t, emis=np.clip(lum(lb) * 2 + wm * 0.3, 0, 1), glow_strength=1.2, vig=0.16, diff=0.06)


class S28(Shot):
    """A console of keys and an empty chair: the camera walks around the chair; parallax
    between chair, desk and window gives the room its depth."""
    t0, t1 = 118.60, 121.50

    def cam(self, t):
        u = smoother(t, self.t0, self.t1)
        a = np.deg2rad(-55 + 70 * u)
        c = np.array([0.0, 0.75, 3.7])
        pos = c + np.array([2.1 * np.sin(a), 0.65, -2.1 * np.cos(a)])
        return PCam.look_at(pos, c + np.array([0, 0.15, 0.35]), f=1150.0)

    def render(self, t):
        cam = self.cam(t)
        ls = [(hover(i, t), col, 0.85) for i, col in enumerate((TEAL, fx.AMBER))]
        img, lb, wm = room_shot_render(cam, t, lights=ls)
        return fx.finish(img + lb, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.2, vig=0.16, diff=0.06)


class S29(Shot):
    """And no one holding the keys: close on the keys. Nothing moves. The two lights wait."""
    t0, t1 = 121.50, 124.40

    def cam(self, t):
        u = smoother(t, self.t0, self.t1)
        return PCam.look_at((0.15, 1.42 - 0.05 * u, 3.62 + 0.12 * u), (0.0, 0.9, 4.65), f=1250.0)

    def render(self, t):
        cam = self.cam(t)
        ls = [(hover(i, t), col, 0.8) for i, col in enumerate((TEAL, fx.AMBER))]
        img, lb, wm = room_shot_render(cam, t, lights=ls)
        return fx.finish(img + lb, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.2, vig=0.18, diff=0.06)


class S30(Shot):
    """Where we live / an unfinished universe: pull back out of the room until it is a small
    drawing on a vast page, with its perspective lines still running off the paper."""
    t0, t1 = 124.40, 130.50

    def cam(self, t):
        u = smoother(t, self.t0, 130.2)
        pos = np.array([0.3, 1.5, 1.2]) * (1 - u) + np.array([7.5, 12.0, -14.0]) * u
        tgt = np.array([0.0, 0.9, 4.5]) * (1 - u) + np.array([0.0, 1.0, 3.2]) * u
        return PCam.look_at(pos, tgt, f=1150.0)

    def render(self, t):
        cam = self.cam(t)
        cut = smooth(t, 125.0, 126.0)
        Rm = room(cutaway=True) if cut > 0.5 else room()
        ls = [(hover(i, t), col, 0.8) for i, col in enumerate((TEAL, fx.AMBER))]
        img, lb, wm = room_shot_render(cam, t, lights=ls, room_obj=Rm)
        # perspective construction lines to the vanishing points, in blue pencil
        M = cam_matrix(1536, 1024, 1.0)
        tooth = tooth_view(paper_view(M))
        g = np.zeros((H_OUT, W_OUT), np.float32)
        k = smooth(t, 126.0, 128.5)
        if k > 0:
            for p0, d in [((-3, 0, 0), (0, 0, 1)), ((3, 0, 0), (0, 0, 1)), ((-3, 3, 0), (0, 0, 1)), ((-3, 0, 6.5), (1, 0, 0)), ((-3, 0, 0), (1, 0, 0)), ((-3, 0, 0), (0, 1, 0)), ((3, 0, 6.5), (0, 1, 0))]:
                p0 = np.array(p0, float)
                d = np.array(d, float)
                P = np.array([p0 - d * 30 * k, p0 + d * 40 * k])
                C = cam.to_cam(P)
                if (C[:, 2] > 0.1).all():
                    q, _ = cam.project(P)
                    pencil_stroke(g, q, width=0.8)
            img = graphite(img, g * 0.5, dim.BLUE_PENCIL, tooth, strength=0.8)
        return fx.finish(img + lb, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.2, vig=0.14, diff=0.06)


SHOTS = {'S25': S25, 'S26': S26, 'S27': S27, 'S28': S28, 'S29': S29, 'S30': S30}
