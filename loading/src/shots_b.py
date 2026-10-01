"""PRE-CHORUS and CHORUS 1: S05-S14."""
from shots_a import *


# =====================================================================================
class S05(Shot):
    """The cosmos was silent, the cosmos was still: the home frame before people. Locked."""
    t0, t1 = 36.10, 39.70

    def setup(self):
        self.W = kv1()
        self.dark = self.W.lights_off()

    def cam(self, t):
        p = lerp_cam(t, [(36.10, dict(cx=1536.0, cy=1130.0, zoom=1.10)), (39.70, dict(cx=1536.0, cy=1128.0, zoom=1.115))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 1130.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        out = cam.sample_depth(self.dark, W.depth, k_far=0.95, k_near=1.0, d_far=0.25, d_near=0.95)
        lb = np.zeros_like(out)
        # stars barely breathe (stillness, not a freeze)
        twinkle(lb, cam.matrix(1.0), W.stars, t, amt=0.7, freeze=0.6)
        out = (out + lb) * np.array([0.90, 0.93, 1.0])   # before people: a colder world
        return fx.finish(out, t, emis=np.clip(lum(lb) * 3, 0, 1), glow_strength=0.8, vig=0.30, diff=0.10)


# =====================================================================================
class KV5World:
    def __init__(self):
        self.P = Plate('KV5')
        ld = lambda k: cached(('kv5', k), lambda: np.load(work('derived', f'KV5_{k}.npy')).astype(np.float32))
        self.img = self.P.img
        self.unlit = ld('unlit')
        self.dark = ld('dark')            # unlit, and the hill fire / paths removed
        self.hill = ld('hill_emis')
        self.flame_mask = ld('flamemask')
        self.depth = gblur(self.P.depth, 3)
        self.ca = self.P.char_alpha
        self.light = self.img - self.unlit   # everything the flame adds (flame + bounce); signed so k=1 is exact
        self.FIRE = (2303.0, 1452.0)
        self.PALM = (1352.0, 1262.0)
        h, w = self.img.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.hypot(xs - self.FIRE[0], ys - self.FIRE[1])
        self.core = (r < 60).astype(np.float32)
        def fill_core():
            m = (r < 75).astype(np.uint8)
            u8 = (np.clip(self.dark, 0, 1) * 255).astype(np.uint8)
            x0, y0 = int(self.FIRE[0]) - 200, int(self.FIRE[1]) - 200
            sub = cv2.inpaint(u8[y0:y0 + 400, x0:x0 + 400], m[y0:y0 + 400, x0:x0 + 400], 15, cv2.INPAINT_TELEA)
            d = self.dark.copy()
            f = gblur(m.astype(np.float32), 6)[y0:y0 + 400, x0:x0 + 400, None]
            d[y0:y0 + 400, x0:x0 + 400] = d[y0:y0 + 400, x0:x0 + 400] * (1 - f) + sub.astype(np.float32) / 255. * f
            return d
        self.dark_core = cached(('kv5', 'darkcore'), fill_core)
        p = work('derived', 'KV5_pathT.npy')
        if os.path.exists(p):
            self.pathT = np.load(p).astype(np.float32)
        else:
            em = np.clip(lum(self.hill) * 8, 0, 1) * (1 - self.core)
            a = dim.stroke_order(em, seed=8, origin=self.FIRE, speed=500, spread=0.4)
            a[a > 1e5] = 99
            # paths spread outward from the fire: arrival grows with distance
            T = (r / 700.0) + 0.15 * np.clip(a, 0, 3)
            T[em < 0.05] = 99
            self.pathT = T.astype(np.float32)
            np.save(p, self.pathT.astype(np.float16))

    def compose(self, t_fire, t_flame, t, flame_k=None, path_k=1.0):
        """t_fire: time the hill fire ignites; t_flame: time the flame blooms in A's palm."""
        f_on = smooth(t, t_fire, t_fire + 0.35)
        flick = 0.85 + 0.15 * np.sin(t * 17.0) * np.sin(t * 5.3 + 1.0)
        hill = self.hill * (self.core * f_on * flick)[:, :, None]
        paths = self.hill * (1 - self.core)[:, :, None] * np.clip((t - t_fire - 0.6 - self.pathT * 1.6) / 0.25, 0, 1)[:, :, None] * path_k
        base = self.dark_core + hill + paths
        k = smooth(t, t_flame, t_flame + 0.30) if flame_k is None else flame_k
        if k > 0:
            # the flame lives: its light breathes, the flame body flickers upward
            kk = k * (1 + 0.08 * np.sin(t * 9.0) * np.sin(t * 3.1))
            base = base + self.light * kk
        return base


class S06(Shot):
    """The first fire is lit on the cold land below. Its light rises to A's waiting palm and
    becomes the small flame both of them look at. A did not make it; she receives it."""
    t0, t1 = 39.70, 43.30
    T_FIRE = 40.35
    T_RISE = (41.0, 42.55)

    def setup(self):
        self.W = KV5World()

    def cam(self, t):
        p = lerp_cam(t, [(39.70, dict(cx=1660.0, cy=1060.0, zoom=1.06)),
                         (43.30, dict(cx=1540.0, cy=1010.0, zoom=1.16))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1660.0, 1060.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        plate = W.compose(self.T_FIRE, self.T_RISE[1], t)
        out = cam.sample_depth(plate, W.depth, k_far=0.9, k_near=1.0, d_far=0.3, d_near=0.8)
        M = cam.matrix(1.0)
        lb = np.zeros_like(out)
        a, b = self.T_RISE
        u = (t - a) / (b - a)
        if 0 < u < 1:
            e = u * u * (3 - 2 * u)
            x0, y0 = W.FIRE
            x2, y2 = W.PALM
            x1, y1 = (x0 * 0.55 + x2 * 0.45, min(y0, y2) - 380)
            for j in range(10):
                ee = max(0.0, e - j * 0.012)
                x = (1 - ee) ** 2 * x0 + 2 * (1 - ee) * ee * x1 + ee * ee * x2
                y = (1 - ee) ** 2 * y0 + 2 * (1 - ee) * ee * y1 + ee * ee * y2
                sx, sy = to_screen(M, x, y)
                size = 0.6 + 1.4 * ee  # it comes toward us: from far below to the near ledge
                fx.point_light(lb, sx, sy, size=size, intensity=(1.3 if j == 0 else 0.35 * (1 - j / 10)) * smooth(u, 0, 0.1))
        if t > b - 0.05:
            # the touch: one soft flash as it settles into the palm
            px, py = to_screen(M, *W.PALM)
            fx.point_light(lb, px, py - 40, size=3.0, intensity=1.2 * np.exp(-((t - b - 0.05) / 0.12) ** 2))
        out = out + lb
        emis = np.clip(lum(np.clip(cam.sample(W.light), 0, 1)) * 1.5 * smooth(t, b, b + 0.3) + lum(cam.sample(W.hill)) * 3 + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.0, vig=0.30, diff=0.10)



# =====================================================================================
import pickle
from envs import composite_layers

_forest = {}


def forest():
    if 'f' not in _forest:
        with open(work('derived', 'forest.pkl'), 'rb') as f:
            _forest['f'] = pickle.load(f)
    return _forest['f']


def fire_flame(buf, x, y, t, scale=1.0, inten=1.0, seed=0):
    """A small campfire seen from far: flickering core lights."""
    for i in range(5):
        ph = seed + i * 1.7
        dx = (i - 2) * 3.0 * scale + 1.5 * np.sin(t * 11 + ph) * scale
        dy = -abs(np.sin(t * 7.3 + ph)) * 6 * scale - i % 2 * 3 * scale
        fx.point_light(buf, x + dx, y + dy, size=0.8 * scale, color=(1.0, 0.55 + 0.1 * np.sin(t * 13 + ph), 0.18),
                       intensity=inten * (0.7 + 0.3 * np.sin(t * 17 + ph)))
    fx.point_light(buf, x, y - 3 * scale, size=2.6 * scale, color=(1.0, 0.5, 0.15), intensity=inten * 0.5)


class Sparks:
    """Embers from a fire: buoyant, wind-drifted, cooling. A few chosen ones climb to the sky."""

    def __init__(self, origin, t_start, rate=9.0, seed=3, wind=(30.0, 0.0), chosen=()):
        rng = np.random.default_rng(seed)
        self.p = []
        t = t_start
        while t < t_start + 8.0:
            self.p.append(dict(t=t, vx=rng.normal(0, 22), vy=-rng.uniform(80, 150), life=rng.uniform(1.0, 2.4), ph=rng.random() * 6.28, sz=rng.uniform(0.5, 1.0)))
            t += rng.exponential(1.0 / rate)
        self.origin = origin
        self.wind = wind
        self.chosen = chosen  # list of (t_launch, target_xy, duration)

    def draw(self, buf, M, t, freeze_t=None, gain=1.0):
        ox, oy = self.origin
        for q in self.p:
            a = t - q['t']
            if a < 0 or a > q['life']:
                continue
            # buoyant rise slows as it cools; wind pushes; small turbulence
            x = ox + q['vx'] * a + self.wind[0] * a * a * 0.5 + 6 * np.sin(a * 5 + q['ph'])
            y = oy + q['vy'] * a + 18 * a * a
            cool = a / q['life']
            col = (1.0, 0.75 - 0.4 * cool, 0.3 - 0.25 * cool)
            sx, sy = to_screen(M, x, y)
            fx.point_light(buf, sx, sy, size=0.45 * q['sz'], color=col, intensity=gain * (1 - cool) ** 1.5 * 0.9)
        for (tl, (tx, ty), dur) in self.chosen:
            a = (t - tl) / dur
            if a < 0:
                continue
            u = min(1.0, a)
            e = 1 - (1 - u) ** 2.2
            x = ox + (tx - ox) * e + 25 * np.sin(u * 7 + tl) * (1 - u)
            y = oy + (ty - oy) * e
            sx, sy = to_screen(M, x, y)
            warm = 1 - smooth(u, 0.6, 1.0)
            col = (1.0, 0.85 - 0.1 * warm, 0.6 - 0.35 * warm)
            col = tuple(mix(np.array(col), np.array([0.8, 0.86, 1.0]), smooth(u, 0.7, 1.0)))
            fx.point_light(buf, sx, sy, size=0.75, color=col, intensity=gain * (1.4 - 0.5 * smooth(u, 0.5, 1.0)))


class S07(Shot):
    """Silence in the forest. The first fire's sparks climb into the sky and become stars;
    every star holds its breath; then one of them goes red and starts counting."""
    t0, t1 = 43.30, 49.40
    HOLD = 45.40
    RED = 46.95

    def setup(self):
        self.layers, stars, self.fire, self.hz = forest()
        rng = np.random.default_rng(5)
        self.stars = [s_ for s_ in stars if s_[2] > 0.45]
        targets = [(1700, 1720), (2020, 1600), (1880, 1880), (2220, 1800), (1560, 1500)]
        chosen = [(43.6 + i * 0.32, tg, 2.6 + 0.2 * i) for i, tg in enumerate(targets)]
        self.sparks = Sparks(self.fire, 43.0, rate=10, chosen=chosen)
        # the red star: high, slightly right — where the camera ends
        self.red = (2060.0, 1120.0)
        self.beats = beats_between(self.RED, 49.4)

    def cam(self, t):
        keys = [(43.30, dict(cx=1840.0, cy=2930.0, zoom=1.22)),
                (44.00, dict(cx=1840.0, cy=2900.0, zoom=1.22)),
                (46.70, dict(cx=1960.0, cy=1600.0, zoom=1.12)),
                (49.40, dict(cx=2040.0, cy=1180.0, zoom=1.40))]
        return lerp_cam(t, keys)

    def render(self, t):
        p = self.cam(t)
        ref = (1840.0, 3060.0)
        hill_M = {}

        def grab(name):
            def f(out, M):
                hill_M[name] = M
                return out
            return f
        kmap = {'sky': 0.97, 'mountains': 0.975, 'far_forest': 0.98, 'hill': 0.985, 'mid_forest': 0.99, 'near_forest': 1.0}
        out = composite_layers(self.layers, p['cx'], p['cy'], p['zoom'], ref, src_w=3072, extra={'hill': grab('hill'), 'sky': grab('sky')}, kmap=kmap)
        lb = np.zeros_like(out)
        Mh = hill_M['hill']
        sx, sy = to_screen(Mh, *self.fire)
        fire_flame(lb, sx, sy, t, scale=1.0 * p['zoom'] / 1.3, inten=1.1)
        self.sparks.draw(lb, Mh, t)
        # the sky: twinkling until the stars hold their breath
        Ms = hill_M['sky']
        freeze = smooth(t, self.HOLD - 0.2, self.HOLD + 0.3)
        rng = np.random.default_rng(9)
        for (x, y, b) in self.stars:
            ph = rng.random() * 6.28
            fr = 0.5 + rng.random() * 1.6
            tw = 0.5 + 0.5 * np.sin(t * fr * 6.28 + ph)
            tw = mix(tw, 0.6, freeze)
            X, Y = to_screen(Ms, x, y)
            if -5 < X < W_OUT + 5 and -5 < Y < H_OUT + 5:
                fx.splat(lb, X, Y, 0.7, (0.8, 0.86, 1.0), 0.25 * b * tw)
        # something vast counts down
        if t > self.RED - 0.6:
            X, Y = to_screen(Ms, *self.red)
            k = smooth(t, self.RED - 0.6, self.RED)
            pulse = 0.0
            for bt in self.beats:
                pulse = max(pulse, np.exp(-max(0, t - bt) / 0.18) * (t >= bt))
            col = tuple(mix(np.array([0.85, 0.88, 1.0]), fx.RED, k))
            fx.point_light(lb, X, Y, size=1.2 + 0.9 * k, color=col, intensity=0.8 + k * (0.6 + 1.2 * pulse), star=0.5 * k, star_len=14, star_angle=0.3)
            if k > 0:
                fx.splat(lb, X, Y, 26.0, fx.RED, 0.05 * k * (0.6 + pulse))
                fx.splat(lb, X, Y, 70.0, fx.RED, 0.012 * k * (0.6 + pulse))
        out = out + lb
        emis = np.clip(lum(lb) * 2.5, 0, 1)
        return fx.finish(out * 1.18, t, emis=emis, glow_strength=1.0, vig=0.30, diff=0.12)


# =====================================================================================
class KV3Ages:
    """KV3 across time: city lights on/off, constellation on/off, A's head down/up."""
    HEAD = (930, 1080, 1420, 1470)   # roi of A's head change

    def __init__(self):
        self.W = KV3World('KV3')
        W = self.W
        self.skyb = cached(('KV3b', 'sky'), lambda: np.load(work('derived', 'KV3b_sky_clean.npy')).astype(np.float32))
        x0, y0, x1, y1 = self.HEAD
        a = W.sky[y0:y1, x0:x1]
        b = self.skyb[y0:y1, x0:x1]
        reg = np.zeros(a.shape[:2], np.float32)
        reg[24:-24, 24:-24] = 1
        self.reg = gblur(reg, 12)
        self.flow = flow_between(a, b) * self.reg[:, :, None]
        P = Plate('KV3')
        def dark():
            lm = P.lights.copy()
            lm[:1400] = 0
            m = cv2.dilate((lm > 0.04).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(np.float32)
            m *= (1 - cv2.dilate(((W.ca > 0.05) | (W.depth > 0.45)).astype(np.uint8), np.ones((15, 15), np.uint8)))
            out = fill_region(W.sky, m, scale=2)
            land = np.zeros(m.shape, np.float32)
            land[1450:] = 1
            near = ((W.ca > 0.05) | (W.depth > 0.45)).astype(np.uint8)
            land *= (1 - cv2.dilate(near, np.ones((25, 25), np.uint8)))
            land = gblur(land, 6)
            warm = np.clip(out[:, :, 0] - out[:, :, 2] * 0.95, 0, 1)
            out = out - (warm * land)[:, :, None] * np.array([1.0, 0.75, 0.2])
            return np.clip(out, 0, 1)
        p = work('derived', 'KV3_dark.npy')
        if os.path.exists(p):
            self.dark = np.load(p).astype(np.float32)
        else:
            self.dark = dark()
            np.save(p, self.dark.astype(np.float16))
        self.city = np.clip(W.sky - self.dark, -1, 1)

    def plate(self, head_s=0.0, city=1.0, const_pts=0.0, const_lines=0.0):
        base = self.dark + self.city * city
        if head_s > 0:
            x0, y0, x1, y1 = self.HEAD
            src_a = base[y0:y1, x0:x1]
            src_b = (self.skyb[y0:y1, x0:x1] - self.W.sky[y0:y1, x0:x1]) + src_a
            ib = inbetween(src_a, src_b, self.flow, head_s)
            base = base.copy()
            r = self.reg[:, :, None]
            base[y0:y1, x0:x1] = src_a * (1 - r) + ib * r
        if const_pts > 0:
            base = base + self.W.pts * const_pts
        if const_lines > 0:
            base = base + self.W.lines * const_lines
        return base


_kv3a = {}


def kv3ages():
    if 'w' not in _kv3a:
        _kv3a['w'] = KV3Ages()
    return _kv3a['w']


class S09(Shot):
    """Before people, the same ruin: A lifts her head to the red star (outward); B keeps
    watching the dark land where the fire is (back toward people). Then the held breath."""
    t0, t1 = 49.40, 52.40
    LIFT = (49.85, 50.45)
    RED = (1930.0, 430.0)

    def setup(self):
        self.K = kv3ages()
        self.beats = beats_between(49.4, 51.6)

    def cam(self, t):
        p = lerp_cam(t, [(49.40, dict(cx=1540.0, cy=1000.0, zoom=1.10)), (52.40, dict(cx=1500.0, cy=1030.0, zoom=1.17))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1540.0, 1000.0))

    def render(self, t):
        K = self.K
        cam = self.cam(t)
        tt = on_twos(t)
        s_ = ease_out(tt, *self.LIFT, p=2)
        base = K.plate(head_s=s_, city=0.0)
        out = cam.sample_depth(base, K.W.depth, k_far=0.93, k_near=1.0, d_far=0.3, d_near=0.8)
        lb = np.zeros_like(out)
        X, Y = to_screen(cam.matrix(0.93), *self.RED)
        pulse = 0.0
        for bt in self.beats:
            pulse = max(pulse, np.exp(-max(0, t - bt) / 0.18) * (t >= bt))
        hold = smooth(t, 51.6, 51.9)
        pulse *= (1 - hold)
        fx.point_light(lb, X, Y, size=1.6, color=fx.RED, intensity=1.0 + 1.0 * pulse + 0.4 * hold, star=0.4, star_len=12, star_angle=0.3)
        fx.splat(lb, X, Y, 30.0, fx.RED, 0.05 * (0.6 + pulse))
        out = out + lb
        # a faint red cast where the sky light falls on the upturned face side
        return fx.finish(out * np.array([0.92, 0.94, 1.0]), t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.0, vig=0.30, diff=0.10)


# =====================================================================================
FIRST_FIRE_KV1 = (934.0, 1318.0)


class S10(Shot):
    """What if we live in a simulated universe? On the downbeat civilisation spreads from the
    first fire's place across the continents. Crane up and back from their backs to the curve."""
    t0, t1 = 52.40, 56.05

    def setup(self):
        self.W = kv1()
        W = self.W
        self.dark = W.lights_off()
        self.light = W.img - self.dark
        h, w = W.img.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot(xs - FIRST_FIRE_KV1[0], (ys - FIRST_FIRE_KV1[1]) * 1.6)
        n = cv2.resize(fbm_field(h // 8, w // 8, 30, 4, 3), (w, h))
        self.T = 52.42 + 2.0 * (d / 2600.0) ** 0.8 + 0.35 * n

    def cam(self, t):
        p = lerp_cam(t, [(52.40, dict(cx=1530.0, cy=1390.0, zoom=1.75)),
                         (56.05, dict(cx=1536.0, cy=1090.0, zoom=1.02))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 1100.0), dolly=1.0)

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        g = np.clip((t - self.T) / 0.12, 0, 1)
        flash = np.exp(-((t - self.T - 0.1) / 0.12) ** 2) * 0.8
        plate = self.dark + self.light * (g + flash)[:, :, None]
        out = cam.sample_depth(plate, W.depth, k_far=0.88, k_near=1.0, d_far=0.25, d_near=0.95)
        lb = np.zeros_like(out)
        twinkle(lb, cam.matrix(1.0), W.stars, t, amt=1.0)
        out = out + lb
        emis = np.clip(cam.sample(W.LM) * cam.sample(g.astype(np.float32)) * 1.4 + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.1, vig=0.26, diff=0.10)


# =====================================================================================
_glb = {}


def globe():
    if 'g' not in _glb:
        tex = imread(work('plates', 'BG0b.png'))
        # pad the polar caps so the sphere has no holes
        h, w = tex.shape[:2]
        top = cv2.flip(tex[:int(h * 0.04)], 0)
        bot = cv2.flip(tex[-int(h * 0.12):], 0)
        texp = np.vstack([gblur(top, 6), tex, gblur(bot, 6)])
        lm = dim.light_mask(texp)
        import globe as G
        G.LAT_TOP, G.LAT_BOT = 88.0, -88.0
        _glb['g'] = G.Globe(texp, lm, grid_w=2600)
        _glb['tex'] = tex
        _glb['lm'] = lm
    return _glb['g']


_space = {}


def space_bg(seed=7):
    if seed not in _space:
        img, stars = __import__('envs').starfield(H_OUT, W_OUT, n=1600, seed=seed, bright=0.8)
        bg = np.ones((H_OUT, W_OUT, 3), np.float32) * np.array([0.012, 0.016, 0.04]) + img * 0.8
        _space[seed] = bg
    return _space[seed]


def atmosphere(buf, cx, cy, R, strength=1.0, col=(0.35, 0.55, 1.0)):
    h, w = buf.shape[:2]
    ys, xs = np.ogrid[0:h, 0:w]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) - R
    ring = np.exp(-(d / max(1.2, R * 0.012)) ** 2) * (d > -R * 0.03)
    outer = np.exp(-np.maximum(d, 0) / max(2.0, R * 0.025)) * (d > 0)
    buf += (ring * 0.35 + outer * 0.12)[:, :, None] * np.array(col, np.float32) * strength


def chalk_circle(buf, cx, cy, r, frac, t, col=(0.75, 0.82, 1.0), inten=0.6, a0=-1.6):
    """A hand-drawn circle: two passes that don't quite agree, and don't quite close."""
    a = np.zeros(buf.shape[:2], np.float32)
    for k, (dr, off, wd, pr) in enumerate([(0.0, 0.0, 1.3, 1.0), (0.006, 0.35, 0.9, 0.55)]):
        n = max(2, int(400 * frac))
        ang = a0 + off + np.linspace(0, 2 * np.pi * frac * (0.985 if k == 0 else 0.93), n)
        wob = 1 + dr + 0.004 * np.sin(ang * 3 + k)
        pts = [(cx + r * w_ * np.cos(q), cy + r * w_ * np.sin(q)) for q, w_ in zip(ang, wob)]
        pencil_stroke(a, pts, width=wd, pressure=np.full(n, pr), jitter=0.5, seed=4 + k)
    rng = np.random.default_rng(int(t * 24) % 3)
    tooth = 0.55 + 0.45 * rng.random(a.shape).astype(np.float32)
    buf += (a * tooth)[:, :, None] * np.array(col, np.float32) * inten
    return a


class S11(Shot):
    """The speed of light is a wall around the verse. Pull back from the Earth; its light leaves
    as a ring and stops against a circle that was only ever drawn in pencil."""
    t0, t1 = 56.05, 59.60
    T_RING = 56.35
    WALL = 7.4

    def setup(self):
        self.G = globe()

    def R(self, t):
        u = smoother(t, self.t0, self.t1 - 0.3)
        return float(np.exp(np.log(640) + (np.log(68) - np.log(640)) * u))

    def render(self, t):
        R = self.R(t)
        cx, cy = 960.0, 560.0 + 40 * (1 - smooth(t, self.t0, self.t1))
        bg = space_bg().copy()
        # outside the wall there are no stars: the painted universe ends there
        wall_px = self.WALL * R
        ys, xs = np.ogrid[0:H_OUT, 0:W_OUT]
        dd = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        inside = smoothstep(wall_px + 6, wall_px - 6, dd)
        bg = bg * (0.25 + 0.75 * inside[:, :, None])
        out, cov, lo = self.G.render(W_OUT, H_OUT, cx, cy, R, lon0=128 + 4 * (t - self.t0), lat0=18, light_time=None, bg=bg)
        lb = np.zeros_like(out)
        if lo is not None:
            out = out + gblur(lo, 0.8)[:, :, None] * fx.AMBER * 0.9
        atmosphere(lb, cx, cy, R, 0.9)
        # the light leaves as a ring
        rw = 1.0 + 3.1 * max(0.0, t - self.T_RING)
        contact = 1.0 + 3.1 * (58.45 - self.T_RING)
        if t > self.T_RING and rw < self.WALL + 0.4:
            rr = min(rw, self.WALL) * R
            ring = np.exp(-((dd - rr) / 3.0) ** 2) + 0.35 * np.exp(-((dd - rr + 10) / 14.0) ** 2) * (dd < rr)
            fade = 1.0 if rw < self.WALL else np.exp(-(rw - self.WALL) * 4)
            lb += ring[:, :, None] * np.array([1.0, 0.85, 0.62]) * 0.9 * fade
        # the wall: drawn as the camera discovers it
        fr = smooth(t, 57.2, 58.4)
        if fr > 0:
            hit = np.exp(-((t - 58.5) / 0.35) ** 2) if t > 58.0 else 0.0
            chalk_circle(lb, cx, cy, wall_px, fr, t, inten=0.22 + 0.6 * hit)
        out = out + lb
        emis = np.clip(lum(lb) * 2.5 + (gblur(lo, 1) if lo is not None else 0) * 1.5, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.0, vig=0.25, diff=0.08, ca=0.4)


# =====================================================================================
class S12(Shot):
    """The Planck scale is fog at the edge of what's known: push into the storm's eye until the
    painting is tiles, then pixels, then fog."""
    t0, t1 = 59.60, 63.15
    EYE = (2080.0, 1900.0)

    def setup(self):
        self.img = cached(('bg0a',), lambda: imread(work('plates', 'BG0a.png')))

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        zoom = float(np.exp(np.log(1.05) + (np.log(14.0) - np.log(1.05)) * (u ** 1.4)))
        cx = mix(1536.0, self.EYE[0], smooth(t, self.t0, self.t0 + 2.2))
        cy = mix(1150.0, self.EYE[1], smooth(t, self.t0, self.t0 + 2.2))
        rot = 0.25 * u ** 2   # the spiral draws us in
        M = cam_matrix(cx, cy, zoom, rot)
        out = affine_sample(self.img, M)
        # resolution limit: beyond ~5x the world shows its pixels (cells of 1 plate px grow on screen)
        px = smooth(t, 61.0, 62.0)
        if px > 0:
            near = affine_sample(self.img, M, interp=cv2.INTER_NEAREST)
            cell = max(2, int(np.hypot(*np.linalg.inv(np.vstack([M, [0, 0, 1]]))[:2, :2][0]) * 3))
            small = cv2.resize(near, (W_OUT // cell, H_OUT // cell), interpolation=cv2.INTER_AREA)
            pix = cv2.resize(small, (W_OUT, H_OUT), interpolation=cv2.INTER_NEAREST)
            out = mix(out, pix, px)
        fog = smooth(t, 62.0, 63.0)
        if fog > 0:
            rng = np.random.default_rng(int(t * 24))
            n = cv2.resize(rng.random((27, 48)).astype(np.float32), (W_OUT, H_OUT), interpolation=cv2.INTER_CUBIC)
            n2 = cv2.resize(rng.random((9, 16)).astype(np.float32), (W_OUT, H_OUT), interpolation=cv2.INTER_CUBIC)
            fogc = np.array([0.30, 0.34, 0.46]) * (0.55 + 0.35 * n + 0.25 * n2)[:, :, None]
            out = mix(fast_blur(out, 30 * fog), fogc, fog * 0.9)
        return fx.finish(out, t, glow=False, vig=0.25, diff=0.12, ca=0.0)


# =====================================================================================
class S13(Shot):
    """Look away - does the world keep on running alone? B lowers her gaze; the far city
    unrenders into pencil; a train light keeps running through the drawing. She looks back: it
    loads again."""
    t0, t1 = 63.15, 66.75

    def setup(self):
        self.W = kv4()
        W = self.W
        self.line = Plate('KV4').line
        h, w = W.img.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        # outer edges unrender first; nearest to her gaze last
        edge = np.minimum(np.minimum(xs, w - xs) / w, np.minimum(ys, h - ys) / h * 0.8)
        n = cv2.resize(fbm_field(h // 4, w // 4, 60, 6, 5), (w, h))
        n2 = cv2.resize(fbm_field(h // 2, w // 2, 6, 7, 2), (w, h))
        self.U = np.clip(edge * 2.2 + 0.30 * n + 0.04 * n2, 0, 1)   # 0 = first to go
        self.paper, self.tooth = dim.paper_texture(h, w, seed=13)

    def cam(self, t):
        p = lerp_cam(t, [(63.15, dict(cx=1600.0, cy=930.0, zoom=1.14)), (66.75, dict(cx=1560.0, cy=935.0, zoom=1.19))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1600.0, 930.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        bg = cam.sample_depth(W.bg, W.depth, k_far=0.62, k_near=0.86, d_far=0.25, d_near=0.6)
        # unrender: 63.9 -> 65.4 from the edges in; reload 66.05 -> 66.7 from the centre out
        U = cam.sample(self.U)
        go = np.clip((t - 63.9 - U * 1.5) / 0.04, 0, 1)
        back = np.clip((t - 66.05 - (1 - U) * 0.6) / 0.04, 0, 1)
        k = go * (1 - back)
        if k.max() > 0:
            L = cam.sample(self.line)
            pap = cam.sample(self.paper)
            too = cam.sample(self.tooth)
            drawing = graphite(pap, L * 1.1, dim.GRAPHITE, too, strength=0.8)
            kk = gblur(k, 1.2)
            # the retreating paint leaves a pooled pigment edge
            edge = np.clip(kk * (1 - kk) * 4, 0, 1)
            bg = mix(bg, drawing, kk[:, :, None]) * (1 - 0.35 * edge[:, :, None])
        lid = 0.45 * smoother(on_twos(t), 63.3, 63.75) * (1 - smoother(on_twos(t), 65.95, 66.35)) + 0.10 * smooth(t, 66.2, 66.6)
        brgb, ba = render_b_layer(W, cam, t, lid, sway_amp=3.0)
        out = over(bg, brgb, ba)
        # the world keeps running: the train light crosses the shore, drawn or not
        lb = np.zeros_like(out)
        M = cam.matrix(0.82)
        u = (t - 63.2) / 3.6
        if 0 < u < 1:
            for j in range(8):
                x, y = path_point(TRAIN_PATH, u - j * 0.006)
                sx, sy = to_screen(M, x, y)
                fx.point_light(lb, sx, sy, size=0.8 if j == 0 else 0.6, color=(1.0, 0.82, 0.55), intensity=(1.3 if j == 0 else 0.35 * (1 - j / 8)))
        out = out + lb * (1 - ba[:, :, None])
        emis = np.clip(lum(lb) * 2 + cam.sample(lum(W.lights)) * 3 * (1 - k) * (1 - ba), 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=0.9, vig=mix(0.26, 0.18, float(k.mean())), diff=0.10)


# =====================================================================================
class S14(Shot):
    """Where we live / an unfinished universe: pull back past the frame. The world is painted
    only where it is looked at; beyond, it is pencil layout on paper, and the lines keep going."""
    t0, t1 = 66.75, 73.00

    def setup(self):
        self.W = kv1()
        W = self.W
        h, w = W.img.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        de = np.minimum(np.minimum(xs, w - 1 - xs), np.minimum(ys, h - 1 - ys))
        n = cv2.resize(fbm_field(h // 4, w // 4, 70, 9, 5), (w, h))
        n2 = cv2.resize(fbm_field(h // 2, w // 2, 5, 10, 2), (w, h))
        self.edge = de + (n - 0.5) * 300 + (n2 - 0.5) * 30    # distance from the painting's edge, ragged brush
        self.flat = W.flat
        self.line = W.line
        self.rim = kv1_rim_circle()

    def cam(self, t):
        p = lerp_cam(t, [(66.75, dict(cx=1536.0, cy=1100.0, zoom=1.03)),
                         (70.6, dict(cx=1536.0, cy=1180.0, zoom=0.62)),
                         (73.0, dict(cx=1536.0, cy=1200.0, zoom=0.56))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 1100.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        M = cam.matrix(1.0)
        paper = paper_view(M)
        tooth = tooth_view(paper)
        depth_img = cam.sample_depth(W.img, W.depth, k_far=0.92, k_near=1.0, d_far=0.25, d_near=0.95)
        # the plate's own coverage on screen
        cov = affine_sample(np.ones(W.img.shape[:2], np.float32), M, border=cv2.BORDER_CONSTANT)
        E = affine_sample(self.edge, M, border=cv2.BORDER_CONSTANT)
        F = cam.sample(self.flat)
        L = cam.sample(self.line)
        reveal = smooth(t, 67.3, 68.6)                 # how much of the margin is shown as unfinished
        band = 560.0 * reveal
        sc = np.hypot(M[0, 0], M[1, 0])                # plate px per screen px
        a_depth = smoothstep(band - 3 * sc, band + 3 * sc, E) if band > 1 else np.ones_like(E)
        a_flat = smoothstep(band * 0.45 - 3 * sc, band * 0.45 + 3 * sc, E) if band > 1 else np.ones_like(E)
        out = graphite(paper, L * cov * 1.15, dim.GRAPHITE, tooth, strength=0.85)
        flat = F * (1 - 0.5 * L[:, :, None]) * (0.92 + 0.08 * tooth[:, :, None])
        pool_f = np.clip(a_flat * (1 - a_flat) * 4, 0, 1)
        out = over(out, flat, a_flat * cov) * (1 - 0.25 * pool_f[:, :, None])
        pool_d = np.clip(a_depth * (1 - a_depth) * 4, 0, 1)
        out = over(out, depth_img, a_depth * cov) * (1 - 0.30 * pool_d[:, :, None])
        # construction keeps extending beyond the painting (unfinished, still being drawn)
        g = np.zeros((H_OUT, W_OUT), np.float32)
        grow = smooth(t, 67.6, 72.8)
        cx, cy, r = self.rim
        a0 = np.pi * 1.5
        span = 0.255 + 0.13 * grow
        ang = np.linspace(a0 - span, a0 + span, 500)
        pts = [to_screen(M, cx + r * np.cos(q), cy + r * np.sin(q)) for q in ang]
        pr = np.clip(np.sin(np.linspace(0, np.pi, len(pts))) * 1.6, 0.15, 1.0) * 0.8
        pencil_stroke(g, pts, width=1.0, pressure=pr, jitter=0.4, seed=2)
        for yy, x0e in ((1662.0, -700), (1702.0, -260), (2040.0, -500)):
            # the ledge's layout lines run on past the painting, tapering where the hand lifts
            xs_ = np.linspace(x0e * grow - 10, 3072 + 800 * grow + 10, 60)
            ptsl = [to_screen(M, xv, yy + 3 * np.sin(xv / 400.0)) for xv in xs_]
            prl = np.clip(np.minimum(np.linspace(0, 6, 60), np.linspace(6, 0, 60)), 0, 1) * 0.55
            pencil_stroke(g, ptsl, width=0.8, pressure=prl, jitter=0.3, seed=int(yy))
        out = graphite(out, g * (1 - cov * a_flat), dim.GRAPHITE, tooth, strength=0.7)
        b = np.zeros((H_OUT, W_OUT), np.float32)
        vp = (1536.0, 853.0 - 2400)
        for xb in (-1400, -600, 3672, 4472):
            pa = to_screen(M, xb, 2400)
            pb = to_screen(M, mix(xb, vp[0], 0.35 + 0.4 * grow), mix(2400, vp[1], 0.35 + 0.4 * grow))
            pencil_stroke(b, [pa, pb], width=0.8, seed=xb)
        pa, pb = to_screen(M, 1536, -700), to_screen(M, 1536, 2700)
        pencil_stroke(b, [pa, pb], width=0.8)
        out = graphite(out, b * 0.35 * smooth(t, 67.4, 68.4) * (1 - cov * a_flat), dim.BLUE_PENCIL, tooth, strength=0.8)
        lb = np.zeros_like(out)
        twinkle(lb, M, W.stars, t, amt=1.0)
        out = out + lb * (cov * a_depth)[:, :, None]
        emis = np.clip(cam.sample(W.LM) * 1.3 * cov * a_depth + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.0, vig=mix(0.26, 0.14, reveal), diff=0.08)

SHOTS = {'S05': S05, 'S06': S06, 'S07': S07, 'S09': S09, 'S10': S10, 'S11': S11, 'S12': S12, 'S13': S13, 'S14': S14}
