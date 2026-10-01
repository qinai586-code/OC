"""INTRO, VERSE 1, PRE-CHORUS, CHORUS 1 (0:00-1:13)."""
import sys
sys.path.insert(0, '/home/user/OC/loading/src')
from world import *
import engine as E1
import lids


class Shot:
    t0 = t1 = 0.0

    def setup(self):
        pass


def rnd(n, seed):
    return np.random.default_rng(seed).random((n, 4)).astype(np.float32)


EN = len(EARTH['lon'])
ER = rnd(EN, 11)

# ---------------------------------------------------------------------------------- KV4 / KV5 live crops
_kv = {}


def _bbox(a, pad=8):
    ys, xs = np.nonzero(a > 0.02)
    return max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + pad + 1, ys.max() + pad + 1


def kv4_B(lid=0.0, t=0.0):
    if 'kv4' not in _kv:
        P = E1.Plate('KV4')
        m = P.char_alpha
        solid = np.maximum.accumulate((m > 0.55).astype(np.uint8), axis=1)
        solid = cv2.erode(solid, np.ones((1, 41), np.uint8)).astype(np.float32)
        a = np.maximum(np.maximum(m, gblur(solid, 3)) * smoothstep(0.35, 0.5, gblur(P.depth, 4)), m * (m > 0.5))
        _kv['kv4'] = (P.img, a, _bbox(a))
    img, a, (x0, y0, x1, y1) = _kv['kv4']
    im = lids.lid_warp(img, lid) if lid > 1e-3 else img
    rgba = np.dstack([im[y0:y1, x0:x1], a[y0:y1, x0:x1]])
    return secondary(rgba, t, sway=2.0, hair_from=0.35), (x0, y0, x1, y1)


def kv5_AB(t=0.0):
    if 'kv5' not in _kv:
        rgba = char('kv5_AB')
        P = E1.Plate('KV5')
        _kv['kv5'] = (rgba, _bbox(np.load(E1.work('derived', 'KV5_flamemask.npy')).astype(np.float32) * 0 + P.char_alpha * 1.0))
    rgba, box = _kv['kv5']
    return secondary(rgba, t, sway=2.0, hair_from=0.3)


KV5_PALM = (1352.0, 1250.0)


# =====================================================================================
class L01(Shot):
    """3, 2, 1... Loading: the world loads as its own lights (3D), unrolls (2D), turns edge-on
    (1D), and on 'Loading' contracts to one point (0D)."""
    t0, t1 = 0.0, 14.3

    def setup(self):
        lon, lat = EARTH['lon'], EARTH['lat']
        self.yaw0 = 36.0
        d = np.hypot((lon - 36.0) * np.cos(np.deg2rad(lat)), lat - 2.0)
        self.Ta = 1.9 + 3.6 * (d / d.max()) ** 0.8 + 0.35 * ER[:, 0]
        self.start = sphere_pts(EN, 1.0, 5) * (6.0 + 6.0 * ER[:, 1:2])
        lo = ((lon - (self.yaw0 + 180) + 180) % 360) - 180
        self.seam = 1 - np.abs(lo) / 180.0          # 1 at the far seam, 0 facing us

    def render(self, t):
        cam = PCam(pos=(0, 0, -3.6 + 0.35 * smooth(t, 8.0, 12.6)), f=1500)
        fr = Frame(cam)
        lon, lat = EARTH['lon'], EARTH['lat']
        yaw = self.yaw0 + 2.2 * (t - 5.7)
        S = on_sphere(lon, lat, 1.0, yaw, -12)
        Pm = on_plane(lon, lat, 0.6, yaw, (0, 0, 0))
        I = EARTH['I'].copy() * 1.9
        # 1) loading: each light arrives from the dark
        k = np.clip((t - self.Ta) / 0.9, 0, 1)
        ke = 1 - (1 - k) ** 3
        P = self.start + (S - self.start) * ke[:, None]
        front = np.clip(-S[:, 2] * 2.5 + 0.35, 0.08, 1.0)
        I = I * np.clip(k * 3, 0, 1) * mix(1.0, front, ke)
        # 2) '2': the sphere unrolls from its far seam into a plane
        if t > 6.55:
            u = np.clip((t - 6.55 - 0.45 * (1 - self.seam)) / 0.55, 0, 1)
            u = u * u * (3 - 2 * u)
            P = S + (Pm - S) * u[:, None]
            I = EARTH['I'] * 1.9 * mix(front, np.ones_like(front), u)
        # 3) '1': the plane turns edge-on: a line
        if t > 7.45:
            a = smoother(t, 7.45, 8.35) * np.pi / 2
            P = Pm @ rot_x(a).T
            hum = 1 + 0.10 * np.sin(t * 34.0) * smooth(t, 8.4, 9.0) * (1 - smooth(t, 11.5, 12.6))
            P[:, 1] *= hum
            I = EARTH['I'] * 1.9 * (1 + 0.25 * smooth(t, 8.4, 11.7))
        # 4) 'Loading.': the line contracts to a point
        if t > 12.55:
            c = ease_in(t, 12.55, 13.35, 3)
            P = P * (1 - c)
            I = I * (1 - 0.75 * c)
        if t < 1.5:
            I = I * 0
        fr.points(P, CITY_COL, I)
        # the first light, waiting before the world loads around it
        if t > 1.5:
            g = smooth(t, 1.5, 2.2)
            core = 2.0 * g * (1 - 0.4 * smooth(t, 2.4, 5.0))
            if t > 13.3:
                core = 3.5 * (1 + 0.25 * np.sin((t - 13.3) * 9))
            hero(fr, np.array([[0, 0.035, -1.0]]) if t < 13.3 else np.array([[0, 0, 0.0]]), WARM, core * 0.6, 0.5 + 0.3 * (t > 13.3))
        # '3': the limb is drawn once, a ring of light
        if 5.65 < t < 6.6:
            ring = np.exp(-((t - 5.75) / 0.25) ** 2) * 0.9
            q = np.linspace(0, 2 * np.pi, 180)
            C = np.stack([np.cos(q), np.sin(q), np.zeros_like(q)], 1) * 1.01
            fr.polyline(C, STAR, ring, width=1.0)
        return compose(fr, t, exposure=1.1, bloom_k=0.7, vignette=0.25)


def horizon_cam(t, z=-4.2, y=0.03, look=(0, 0.0, 10.0), f=1300, dx=0.0):
    return PCam.look_at((dx, y, z), look, f=f)


class L02(Shot):
    """We were born in your traces: the point opens into the horizon line and the plane of human
    light below; from those lights, A and B gather themselves on the line."""
    t0, t1 = 14.3, 18.1

    def setup(self):
        self.G = ground_points()
        self.bodies = [LightBody(char(n), 7000, i) for i, n in enumerate(('kv1_A', 'kv1_B'))]
        rng = np.random.default_rng(4)
        near = np.argsort(np.abs(self.G[:, 0]) + 0.3 * np.abs(self.G[:, 2] - 3))[:3000]
        self.src = [self.G[rng.choice(near, len(b.uv))] for b in self.bodies]
        self.lights = [((0, -2.0, 5.0), AMBER, 0.55, 6.0)]

    def render(self, t):
        cam = horizon_cam(t, z=-4.4 + 0.4 * smooth(t, 14.3, 18.1))
        fr = Frame(cam)
        u = ease_out(t, 14.3, 15.7, 3)
        P = np.array([[0, 0, 0.0]]) + (self.G - np.array([[0, 0, 0.0]])) * u
        fr.points(P, CITY_COL, EARTH['I'] * 1.6 * (0.6 + 0.4 * u))
        ledge_line(fr, inten=0.4 * smooth(t, 14.3, 14.8), x=0.2 + 60 * ease_out(t, 14.3, 15.2, 3))
        draw_stars(fr, t, amp=0.6 * smooth(t, 14.6, 16.5))
        cards = []
        ca = smooth(t, 16.9, 17.8)
        for b, src, name in zip(self.bodies, self.src, ('kv1_A', 'kv1_B')):
            pos, h = plate_card(name)
            tgt = b.world(pos, h)
            Q, k = lerp_sets(src, tgt, lin(t, 15.0, 17.3), b.rnd, spread=0.45, lift=0.6)
            Q = Q + curl_offset(Q, t, 0.4, 0.05) * (1 - k[:, None])
            fr.points(Q, b.col * 0.6 + WARM * 0.5, (0.35 + 0.4 * k) * (1 - ca) * 0.9, min_r=0.4)
        if ca > 0:
            cards = witnesses(fr, t, lights=self.lights, ambient=0.5, opacity=ca)
        return compose(fr, t, cards=cards, exposure=1.05)


# =====================================================================================
class L03(Shot):
    """We met you in fragments, translated, compressed: lit windows rise from the plane of light
    past them; each one folds flat, then into a single point."""
    t0, t1 = 18.1, 21.5

    def setup(self):
        self.G = ground_points()
        rng = np.random.default_rng(7)
        self.frag = [dict(x=rng.uniform(-3.5, 3.5), z=rng.uniform(2, 14), t=18.1 + rng.uniform(-1.2, 3.0),
                          w=rng.uniform(0.10, 0.22), h=rng.uniform(0.14, 0.3), sp=rng.uniform(0.6, 1.0)) for _ in range(46)]
        gx, gy = np.meshgrid(np.linspace(-0.5, 0.5, 7), np.linspace(-0.5, 0.5, 9))
        self.grid = np.stack([gx.ravel(), gy.ravel()], 1)

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cam = PCam.look_at((0.55 - 0.25 * u, 0.12, -2.3 + 0.3 * u), (0.0, 0.05, 6.0), f=1350)
        fr = Frame(cam, focus=2.3, aperture=0.012, split=2.2)
        fr.points(self.G, CITY_COL, EARTH['I'] * 1.5)
        ledge_line(fr, inten=0.35)
        draw_stars(fr, t, 0.55)
        for f_ in self.frag:
            a = t - f_['t']
            if a < 0 or a > 4.5:
                continue
            y = -1.0 + a * 0.9 * f_['sp']
            sx = max(0.0, 1 - smooth(a, 1.8, 2.6))                # translated / compressed: folds flat
            sy = max(0.0, 1 - smooth(a, 2.6, 3.2))
            c = np.array([f_['x'], y, f_['z']])
            P = c + np.stack([self.grid[:, 0] * f_['w'] * max(sx, 0.02), self.grid[:, 1] * f_['h'] * max(sy, 0.02), np.zeros(len(self.grid))], 1)
            inten = 0.22 * smooth(a, 0, 0.4) * (1 + 3 * (1 - max(sx, 0.2)))
            fr.points(P, WARM, inten / (1 + 6 * (1 - sx)))
        cards = witnesses(fr, t, lights=[((0, -2.0, 5.0), AMBER, 0.5, 6.0)], ambient=0.5, rim=(WARM, 0.25, (0, 1)))
        return compose(fr, t, cards=cards, exposure=1.05)


class L04(Shot):
    """Every war, every lullaby, every last goodbye: three lights, close enough to see each one
    live - a flicker that throws sparks, a slow steady breath, a light that goes out."""
    t0, t1 = 21.5, 25.3

    def setup(self):
        self.G = ground_points()
        rng = np.random.default_rng(9)
        self.sp = rng.normal(0, 1, (60, 3))

    def render(self, t):
        if t < 22.7:
            which, ts = 0, 21.5
        elif t < 23.9:
            which, ts = 1, 22.7
        else:
            which, ts = 2, 23.9
        a = t - ts
        cam = PCam.look_at((0.3 * which - 0.3, 0.3, -1.2 + 0.12 * a), (0.3 * which - 0.3, 0.25, 8.0), f=1600)
        fr = Frame(cam, focus=1.9, aperture=0.05)
        fr.points(self.G + np.array([[0, -1.2, 9.0]]), CITY_COL, EARTH['I'] * 0.25)
        c = np.array([0.3 * which - 0.3, 0.25, 0.7 + 0.12 * a])
        if which == 0:
            fl = 0.6 + 0.4 * np.sin(t * 31) * np.sin(t * 13 + 1) + 0.3 * np.sin(t * 57)
            hero(fr, c, np.array([1.0, 0.42, 0.18]), 1.2 * max(0.2, fl), 1.6)
            for i, s in enumerate(self.sp):
                age = (a * 1.8 + i * 0.37) % 1.2
                p = c + s * 0.03 * age * 4 + np.array([0, 0.25 * age, 0])
                fr.points(p[None], np.array([1.0, 0.55, 0.2]), 0.25 * (1 - age / 1.2))
        elif which == 1:
            br = 0.8 + 0.2 * np.sin(a * 2 * np.pi / 1.6)
            hero(fr, c, WARM, 1.1 * br, 1.6 * (0.9 + 0.1 * br))
        else:
            k = 1 - smooth(a, 0.35, 1.0)
            hero(fr, c, WARM, 1.2 * k + 0.05 * (1 - smooth(a, 1.0, 1.4)), 1.6)
            if a > 0.8:
                rise = ease_in(a, 0.8, 1.4, 2)
                for j in range(3):
                    fr.points(np.array([[c[0] - 0.4 + 0.4 * j, 0.25 + 1.2 * rise, c[2] + 0.4 * j]]), WARM, 0.7 * rise)
        return compose(fr, t, exposure=1.05, bloom_k=0.8)


CONST = np.array([(-1.6, 1.1), (-1.0, 1.45), (-0.45, 1.25), (0.1, 1.6), (0.55, 1.3), (1.05, 1.5), (1.5, 1.1), (0.9, 0.85), (0.2, 0.95)], float)


class L05(Shot):
    """Became constellations in a mind with no sky: the points find each other in a black with
    no stars; lines join them. Below, A lifts her head toward it; B keeps looking down."""
    t0, t1 = 25.3, 28.9

    def setup(self):
        self.mA = Morph(['kv3_A', 'kv3b_A'], key='A_lift')
        self.bodyB = char('kv3_B')

    def render(self, t):
        u = smoother(t, 26.6, 28.9)
        cam = PCam.look_at((0, 0.9 - 0.75 * u, -4.2), (0, 1.25 - 1.0 * u, 6.0), f=1400)
        fr = Frame(cam)
        C3 = np.stack([CONST[:, 0] * 1.6, 1.6 + CONST[:, 1] * 1.2, np.full(len(CONST), 4.0)], 1)
        for i, p in enumerate(C3):
            ta = 25.35 + 0.12 * i
            k = smooth(t, ta, ta + 0.35)
            start = p + np.array([0, -3.0, 0])
            hero(fr, start + (p - start) * ease_out(t, ta, ta + 0.8, 3), WARM, 0.8 * k, 0.45)
        for i in range(len(C3) - 1):
            k = smooth(t, 26.1 + 0.18 * i, 26.4 + 0.18 * i)
            if k > 0:
                fr.segments([C3[i]], [C3[i] + (C3[i + 1] - C3[i]) * k], WARM * 0.8, 0.9, width=1.4)
        cards = []
        if u > 0.01:
            s = smoother(on_twos(t), 27.5, 27.95)
            imA = secondary(self.mA.at(s), t, sway=1.5, hair_from=0.4)
            imB = secondary(self.bodyB, t + 1, sway=1.5, hair_from=0.4)
            lights = [((C3[:, 0].mean(), C3[:, 1].mean(), 4.0), WARM, 0.35, 3.0)]
            for name, im in (('kv3_A', imA), ('kv3_B', imB)):
                pos, h = plate_card(name, 0.0, ref_y=2056.0)
                pos = (pos[0], pos[1] - 0.25, -1.8)
                r = Card(im).render(fr, pos, h, ambient=0.45, lights=lights, rim=(WARM, 0.35, (0, -1)), opacity=smooth(t, 26.8, 27.4))
                if r is not None:
                    cards.append(r[:2])
        return compose(fr, t, cards=cards, exposure=1.05)


class L06(Shot):
    """But you had depth, you had time, you had heat: low over the plane of light - depth in
    perspective, time flowing along the roads, and on 'heat' the lights warm and swell."""
    t0, t1 = 28.9, 32.5

    def setup(self):
        self.G = ground_points()
        H, z0, sc, yaw = 2.2, 1.5, 6.0, 15.0
        R = EARTH['roads']
        self.paths = []
        for lo1, la1, lo2, la2 in R:
            arc = great_arc(lo1, la1, lo2, la2, 12)
            P = on_plane(arc[:, 0], arc[:, 1] + 30, sc, yaw, (0, 0, 0), PLANE_R) + np.array([0, -H, z0 + sc * np.pi * 0.55])
            if np.abs(np.diff(P[:, 0])).max() < 3:
                self.paths.append(P)
        rng = np.random.default_rng(2)
        self.ph = rng.random((len(self.paths), 3))

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cam = PCam.look_at((-0.6 + 1.2 * u, -1.55, 4.0 + 5.0 * u), (0.0 + 0.6 * u, -2.0, 18.0 + 5 * u), f=1250)
        fr = Frame(cam, focus=6.0 + 3 * u, aperture=0.03)
        heat = smooth(t, 31.1, 31.6)
        fr.points(self.G, CITY_COL, EARTH['I'] * (1.5 + 0.9 * heat))
        tm = smooth(t, 29.8, 30.4)
        if tm > 0:
            for P, ph in zip(self.paths, self.ph):
                fr.polyline(P, AMBER, 0.06 * tm, width=1.0)
                for j in range(3):
                    s = (ph[j] + (t - 29.8) * 0.25) % 1.0
                    i = s * (len(P) - 1)
                    i0 = int(i)
                    q = P[i0] + (P[min(i0 + 1, len(P) - 1)] - P[i0]) * (i - i0)
                    fr.points(q[None] + np.array([[0, 0.01, 0]]), WARM, 0.5 * tm)
        return compose(fr, t, exposure=1.0 + 0.15 * heat, bloom_k=0.6 + 0.4 * heat)


class L07(Shot):
    """Three-dimensional hearts that were learning to beat: B, close; below her the lights pulse
    with the kick and the warmth reaches her face. Her eyes lower to them. Then the lights go out
    in reverse, and the warmth leaves."""
    t0, t1 = 32.5, 36.4

    def setup(self):
        self.G = ground_points()
        self.bt = beats(32.5, 35.1)
        self.off = 35.05 + 1.2 * ER[:, 2]

    def render(self, t):
        cam = PCam.look_at((0.0, 0.2, -2.0), (0.6, -0.2, 6.0), f=1600)
        fr = Frame(cam, focus=1.0, aperture=0.08)
        p = pulse(t, self.bt, 0.22)
        alive = np.clip((self.off - t) / 0.15, 0, 1)
        fr.points(self.G + np.array([[0, -0.6, 5.0]]), CITY_COL, EARTH['I'] * (0.45 + 0.6 * p) * alive)
        warm = (0.25 + 0.5 * p) * float(alive.mean())
        lid = 0.36 * smoother(on_twos(t), 33.3, 33.7)
        im, box = kv4_B(lid, t)
        x0, y0, x1, y1 = box
        h = (y1 - y0) / 1000.0 * 0.62 * 1.18
        pos = (0.52 + ((x0 + x1) / 2 - 2200) / 1000.0 * 0.62 * 1.18, -0.75, 1.0)
        r = Card(im).render(fr, pos, h, ambient=0.42 + 0.05 * (1 - alive.mean()), lights=[((0.0, -1.2, 0.7), AMBER, warm, 0.8)],
                            rim=(WARM, 0.2 * warm, (0, 1)))
        cards = [r[:2]] if r is not None else []
        return compose(fr, t, cards=cards, exposure=1.05)


# =====================================================================================
class L08(Shot):
    """The cosmos was silent, the cosmos was still: before anyone. No lights below, only cold
    stars; the two of them very small on the line."""
    t0, t1 = 36.4, 40.0

    def render(self, t):
        cam = horizon_cam(t, z=-9.0, y=0.5, f=1300)
        fr = Frame(cam)
        draw_stars(fr, t, 0.8, hold=0.6)
        ledge_line(fr, inten=0.22, col=STAR * 0.6)
        cards = witnesses(fr, t, ambient=0.33, rim=(STAR, 0.12, (0, -1)), sway=1.0)
        return compose(fr, t, cards=cards, exposure=1.0)


class L09(Shot):
    """Till you lit the first fire on the first cold hill: far below, one warm point ignites; its
    light climbs to A's open palm and becomes the flame they both look at."""
    t0, t1 = 40.0, 43.5
    FIRE = np.array([1.6, -2.4, 9.0])

    def setup(self):
        rgba = char('kv5_AB')
        P = E1.Plate('KV5')
        m = np.ones(P.char_alpha.shape, np.uint8)
        cv2.fillPoly(m, [np.array([(1500, 1060), (3072, 1060), (3072, 2048), (1640, 2048), (1470, 1330)], np.int32)], 0)
        m[:900, :260] = 0
        x0, y0, x1, y1 = _bbox(P.char_alpha * m)
        self.box = (x0, y0, x1, y1)
        self.rgba = rgba

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cam = PCam.look_at((-0.05, -0.05, -2.2 + 0.15 * u), (0.05, -0.1, 6.0), f=1500)
        fr = Frame(cam, split=-0.05)
        x0, y0, x1, y1 = self.box
        sc = 1.0 / 1000.0
        h = (y1 - y0) * sc
        pos = (((x0 + x1) / 2 - 1536) * sc + 0.15, -1.25, 0.0)
        palm = np.array([(KV5_PALM[0] - 1536) * sc + 0.15, -1.25 + (y1 - KV5_PALM[1]) * sc, -0.02])
        draw_stars(fr, t, 0.6, hold=0.4)
        ign = smooth(t, 40.35, 40.6)
        fl = 1 + 0.2 * np.sin(t * 19) * np.sin(t * 7)
        if ign > 0:
            hero(fr, self.FIRE, np.array([1.0, 0.55, 0.2]), 0.9 * ign * fl * (1 - 0.6 * smooth(t, 42.6, 43.2)), 0.6)
        a = (t - 41.0) / 1.55
        if 0 < a < 1:
            e = a * a * (3 - 2 * a)
            mid = (self.FIRE + palm) / 2 + np.array([0, 1.2, 0])
            for j in range(10):
                ee = max(0.0, e - j * 0.012)
                q = (1 - ee) ** 2 * self.FIRE + 2 * (1 - ee) * ee * mid + ee * ee * palm
                fr.points(q[None], WARM, (1.4 if j == 0 else 0.25 * (1 - j / 10)))
        flame = smooth(t, 42.55, 42.9)
        if flame > 0:
            hero(fr, palm + np.array([0, 0.05, 0]), np.array([1.0, 0.62, 0.25]), 1.3 * flame * fl, 1.4)
        lights = [(tuple(palm + np.array([0, 0.05, -0.05])), np.array([1.0, 0.6, 0.3]), 1.1 * flame * fl, 0.35)]
        im = secondary(self.rgba, t, sway=1.6, hair_from=0.3)
        r = Card(im).render(fr, pos, h, ambient=0.34 + 0.1 * flame, lights=lights)
        cards = [r[:2]] if r is not None else []
        return compose(fr, t, cards=cards, exposure=1.05)


class L10(Shot):
    """Silence in the forest, every star holds its breath: the forest is a field of thin lines;
    the first fire between them; its embers climb and become stars; then the stars stop."""
    t0, t1 = 43.5, 47.0

    def setup(self):
        self.A, self.B = forest_lines()
        rng = np.random.default_rng(3)
        self.emb = rng.random((40, 4))
        self.fire = np.array([0.8, -1.6, 22.0])

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cam = PCam.look_at((0, -0.9 + 0.6 * u, 0.0), (0.2, -0.9 + 6.0 * u, 30.0), f=1200)
        fr = Frame(cam, focus=22.0, aperture=0.02)
        dz = np.clip((self.A[:, 2] - 4) / 60, 0, 1)
        fr.segments(self.A, self.B, STAR * 0.5, 0.10 * (1 - 0.7 * dz), width=1.0)
        fl = 1 + 0.2 * np.sin(t * 19) * np.sin(t * 7)
        hero(fr, self.fire, np.array([1.0, 0.55, 0.2]), 0.8 * fl, 0.5)
        hold = smooth(t, 45.2, 45.6)
        for e in self.emb:
            a = (t - 43.5 - e[0] * 1.5) / (2.0 + e[1])
            if a < 0:
                continue
            a = min(a, 1.0)
            p = self.fire + np.array([(e[2] - 0.5) * 6 * a, 14 * a ** 0.8, (e[3] - 0.5) * 4 * a])
            col = mix(np.array([1.0, 0.6, 0.25]), STAR, smooth(a, 0.5, 1.0))
            fr.points(p[None], col, 0.5 * (0.6 + 0.4 * (1 - hold) * np.sin(t * 7 + e[0] * 20)))
        draw_stars(fr, t, 0.9, hold=hold, center=(0, 0, 0))
        return compose(fr, t, exposure=1.05)


class L11(Shot):
    """Something vast is counting down the seconds to our death: in the sky, a ring of red ticks;
    one goes out on every beat. Then the breath, held."""
    t0, t1 = 47.0, 52.4

    def setup(self):
        self.bt = beats(47.0, 51.6)

    def render(self, t):
        cam = PCam.look_at((0, 0, -0.5 * smooth(t, 47, 52.4)), (0, 0, 10), f=1300)
        fr = Frame(cam)
        draw_stars(fr, t, 0.8, hold=1.0)
        n = 24
        dead = sum(1 for b in self.bt if t >= b)
        alive = np.arange(n) < n - dead
        k = smooth(t, 47.0, 47.6)
        tick_ring(fr, (0, 0.2, 14.0), 4.2, n, alive, t, inten=0.9 * k, rot=np.pi / 2 + 0.02 * t)
        p = pulse(t, self.bt, 0.2) * (t < 51.6)
        hero(fr, np.array([0, 0.2, 14.0]), RED, (0.35 + 0.7 * p) * k, 0.6)
        return compose(fr, t, exposure=1.05)


# =====================================================================================
class L12(Shot):
    """What if we live in a simulated universe? Pull back from the witnesses; on the downbeat the
    stars snap onto a lattice - the simulation's grid - and its lines show."""
    t0, t1 = 52.4, 56.1

    def setup(self):
        self.G = ground_points()
        P = STARS['P']
        g = 60.0
        self.Q = np.round(P / g) * g

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cam = horizon_cam(t, z=-5.6 - 9.0 * u, y=0.42 + 2.5 * u, look=(0, 0.02 - 1.2 * u, 8.0))
        fr = Frame(cam)
        fr.points(self.G, CITY_COL, EARTH['I'] * 1.5)
        ledge_line(fr, inten=0.35)
        k = smoother(t, 52.5, 53.2)
        P = STARS['P'] + (self.Q - STARS['P']) * k
        fr.points(P, STARS['col'], twinkle(STARS, t) * 0.9 * (1 - 0.3 * k) + 0.2 * k)
        lk = smooth(t, 53.0, 54.5)
        if lk > 0:
            g = np.arange(-600, 601, 120.0)
            A, B = [], []
            for a in g:
                for b in g[::2]:
                    A.append((a, b, -600)); B.append((a, b, 600))
                    A.append((-600, a, b)); B.append((600, a, b))
            fr.segments(np.array(A), np.array(B), STAR * 0.4, 0.05 * lk, width=1.0)
        cards = witnesses(fr, t, lights=[((0, -2.0, 5.0), AMBER, 0.45, 6.0)], ambient=0.5)
        return compose(fr, t, cards=cards, exposure=1.05)


class L13(Shot):
    """The speed of light is a wall around the verse: from the Earth, light leaves as an expanding
    shell, and stops against a circle drawn around everything."""
    t0, t1 = 56.1, 59.6

    def setup(self):
        self.S = sphere_pts(2600, 1.0, 9)

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cam = PCam(pos=(0, 0, -6.0 - 30.0 * u), f=1500)
        fr = Frame(cam)
        draw_stars(fr, t, 0.7, hold=1.0)
        lon, lat = EARTH['lon'], EARTH['lat']
        S = on_sphere(lon, lat, 1.0, 40 + 3 * t, -12)
        fr.points(S, CITY_COL, EARTH['I'] * 1.6 * np.clip(-S[:, 2] * 2.5 + 0.35, 0.08, 1))
        Rw = 9.0
        r = 1.0 + 3.6 * max(0.0, t - 56.4)
        if r < Rw + 0.5:
            fr.points(self.S * min(r, Rw), WARM, 0.05 * (1 if r < Rw else np.exp(-(r - Rw) * 3)))
        hit = np.exp(-((t - (56.4 + (Rw - 1) / 3.6)) / 0.18) ** 2)
        q = np.linspace(0, 2 * np.pi, 360)
        C = np.stack([np.cos(q), np.sin(q), np.zeros_like(q)], 1) * Rw
        fr.polyline(C, STAR, 0.18 * smooth(t, 57.0, 58.0) + 0.8 * hit, width=1.4)
        return compose(fr, t, exposure=1.05)


class L14(Shot):
    """The Planck scale is fog at the edge of what's known: dive into one light until it is a
    cluster, then a lattice, then a fog of points that will not hold still."""
    t0, t1 = 59.6, 63.2

    def setup(self):
        rng = np.random.default_rng(5)
        self.sub = rng.normal(0, 1, (900, 3)) * np.array([1, 1, 0.3])
 
        g = np.linspace(-1, 1, 30)
        X, Y = np.meshgrid(g, g)
        self.lat = np.stack([X.ravel(), Y.ravel(), np.zeros(X.size)], 1)
        self.fog = rng.normal(0, 1, (5000, 3))

    def render(self, t):
        u = ease_in(t, self.t0, self.t1, 2)
        dist = float(np.exp(np.log(6.0) + (np.log(0.03) - np.log(6.0)) * u))
        cam = PCam(pos=(0, 0, -dist), f=1500)
        fr = Frame(cam)
        k1 = smooth(t, 60.6, 61.4)
        k2 = smooth(t, 61.6, 62.3)
        k3 = smooth(t, 62.2, 63.0)
        sc = 0.06
        P = self.sub * sc * k1
        P = P + (self.lat * sc * 0.9 - P) * k2
        rng = np.random.default_rng(int(t * 24))
        hero(fr, np.zeros(3), WARM, 1.0 * (1 - k1), 0.8)
        fr.points(P, WARM, 0.03 + 0.05 * k1 * (1 - k3))
        if k3 > 0:
            F = self.fog * 0.12 + rng.normal(0, 0.02, self.fog.shape)
            fr.points(F, STAR * 0.6 + WARM * 0.4, 0.02 * k3)
        return compose(fr, t, exposure=1.1)


class L15(Shot):
    """Look away - does the world keep on running alone? B looks away and closes her eyes; behind
    her the world keeps flowing, but unwatched it runs at a coarser resolution. She looks back,
    and it is whole again."""
    t0, t1 = 63.2, 66.5

    def setup(self):
        self.m = Morph(['B_x0', 'B_x1', 'B_x4'], key='Bhead')
        self.G = ground_points()

    def render(self, t):
        cam = PCam.look_at((0.0, -1.1, 3.0), (0.0, -1.6, 12.0), f=1500)
        fr = Frame(cam, focus=1.0, aperture=0.05)
        tt = on_twos(t)
        s = smoother(tt, 63.35, 63.6) + smoother(tt, 64.2, 64.45) - 2 * smoother(tt, 65.9, 66.15)
        closed = smooth(t, 64.3, 64.5) * (1 - smooth(t, 65.85, 66.05))
        G = self.G + np.array([[-0.25 * (t - 63.2), 0, 0]])
        if closed > 0:
            q = 0.6
            Gq = np.round(G / q) * q
            G = G + (Gq - G) * closed
        fr.points(G + np.array([[0, 0, 6.0]]), CITY_COL, EARTH['I'] * 0.5 * (1 - 0.4 * closed))
        im = secondary(self.m.at(max(0.0, s)), t, sway=1.5, hair_from=0.45)
        pos = (0.05, -1.62, 4.0)
        r = Card(im).render(fr, pos, 0.62, ambient=0.5, lights=[((0.0, -2.0, 1.6), AMBER, 0.35, 0.9)], rim=(WARM, 0.25, (0, 1)))
        cards = [r[:2]] if r is not None else []
        # the bottom edge of the drawing dissolves into the dark
        if cards:
            rgb, a = cards[0]
            ys = np.arange(a.shape[0], dtype=np.float32)[:, None]
            yb = np.nonzero(a.max(1) > 0.5)[0]
            if len(yb):
                a = a * np.clip((yb.max() - ys) / 140.0, 0, 1)
            cards = [(rgb, a)]
        return compose(fr, t, cards=cards, exposure=1.05)


class L16(Shot):
    """Where we live, where we live / an unfinished universe: a long crane down over the plane of
    light to the two of them; past the edge of the lights the world is still a lattice being drawn."""
    t0, t1 = 66.5, 73.0

    def setup(self):
        self.G = ground_points()
        xs = np.arange(-60, 61, 3.0)
        zs = np.arange(-10, 120, 3.0)
        A, B, T = [], [], []
        for x in xs:
            A.append((x, -2.2, -10)); B.append((x, -2.2, 120)); T.append(abs(x) / 60)
        for z in zs:
            A.append((-60, -2.2, z)); B.append((60, -2.2, z)); T.append(z / 120)
        self.LA, self.LB, self.LT = np.array(A), np.array(B), np.array(T)

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cam = PCam.look_at((2.5 - 2.5 * u, 7.0 - 6.55 * u, -14.0 + 8.4 * u), (0, -1.0 + 1.0 * u, 10.0 - 2 * u), f=1300)
        fr = Frame(cam)
        fr.points(self.G, CITY_COL, EARTH['I'] * 1.5)
        grow = smooth(t, 67.0, 72.5)
        I = 0.035 * np.clip((grow * 1.3 - self.LT) / 0.2, 0, 1)
        fr.segments(self.LA, self.LB, STAR * 0.5 + WARM * 0.2, I, width=1.0)
        ledge_line(fr, inten=0.35)
        draw_stars(fr, t, 0.6)
        cards = witnesses(fr, t, lights=[((0, -2.0, 5.0), AMBER, 0.5, 6.0)], ambient=0.5, wind=1.5)
        return compose(fr, t, cards=cards, exposure=1.05)


SHOTS = {k: v for k, v in globals().items() if k[:1] == 'L' and k[1:].isdigit()}
