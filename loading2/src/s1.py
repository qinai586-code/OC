"""INTRO, VERSE 1, PRE-CHORUS, CHORUS 1 (0:00-1:13): one continuous camera.

Each class is a movement of that camera. Its last frame is the next movement's first:
either the same pose and content, or a gate (a single light filling the frame).
"""
import sys
sys.path.insert(0, '/home/user/OC/loading/src')
from world import *
from lfx import *
from face import head, HEADS, blink_amount, mouth, blink, morph_head
import voice
import engine as E1
import lids


class Shot:
    t0 = t1 = 0.0

    def setup(self):
        pass


EN = len(EARTH['lon'])
ER = np.random.default_rng(11).random((EN, 4)).astype(np.float32)
G = ground_points()
GI = EARTH['I']
SPACE = space_bg()
FIRE = np.array([1.0, 0.55, 0.22], np.float32)


def flick(t, s=0.0):
    return 1 + 0.2 * np.sin(t * 19 + s) * np.sin(t * 7 + 2 * s)


# ---------------------------------------------------------------------------------- KV4 / KV5 crops
_kv = {}


def _bbox(a, pad=8):
    ys, xs = np.nonzero(a > 0.02)
    return max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + pad + 1, ys.max() + pad + 1


def kv4_base():
    if 'kv4' not in _kv:
        P = E1.Plate('KV4')
        m = P.char_alpha
        solid = np.maximum.accumulate((m > 0.55).astype(np.uint8), axis=1)
        solid = cv2.erode(solid, np.ones((1, 41), np.uint8)).astype(np.float32)
        a = np.maximum(np.maximum(m, gblur(solid, 3)) * smoothstep(0.35, 0.5, gblur(P.depth, 4)), m * (m > 0.5))
        _kv['kv4'] = (P.img, a, _bbox(a))
    return _kv['kv4']


def kv4_B(lid=0.0, t=0.0):
    img, a, (x0, y0, x1, y1) = kv4_base()
    im = lids.lid_warp(img, lid) if lid > 1e-3 else img
    rgba = np.dstack([im[y0:y1, x0:x1], a[y0:y1, x0:x1]]).astype(np.float32)
    return secondary(rgba, t, sway=2.0, hair_from=0.35, roll=0.4 * np.sin(0.5 * t)), (x0, y0, x1, y1)


def kv5_base():
    if 'kv5' not in _kv:
        rgba = char('kv5_AB').copy()
        P = E1.Plate('KV5')
        m = np.ones(P.char_alpha.shape, np.uint8)
        cv2.fillPoly(m, [np.array([(1500, 1060), (3072, 1060), (3072, 2048), (1640, 2048), (1470, 1330)], np.int32)], 0)
        m[:900, :260] = 0
        _kv['kv5'] = (rgba, _bbox(P.char_alpha * m))
    return _kv['kv5']


KV5_PALM = (1352.0, 1250.0)


# ==================================================================================== INTRO
class C01(Shot):
    """3, 2, 1... Loading. A single point; the Earth loads around it as arriving lights (3D).
    On "3" a ring sweeps the limb and the camera surges in; on "2" the sphere unrolls into a
    plane (2D); on "1" the plane turns edge-on: a line (1D) that hums with the held note.
    "Loading." is written by the line's own lights; then everything contracts into one point
    (0D), which waits through the breath."""
    t0, t1 = 0.0, 14.3

    def setup(self):
        lon, lat = EARTH['lon'], EARTH['lat']
        self.yaw0 = 36.0
        d = np.hypot((lon - 36.0) * np.cos(np.deg2rad(lat)), lat - 2.0)
        self.Ta = 1.9 + 3.6 * (d / d.max()) ** 0.8 + 0.35 * ER[:, 0]
        self.start = sphere_pts(EN, 1.0, 5) * (6.0 + 6.0 * ER[:, 1:2])
        lo = ((lon - (self.yaw0 + 180) + 180) % 360) - 180
        self.seam = 1 - np.abs(lo) / 180.0
        self.word = Words('Loading.', n=1700, weight='Light')
        self.wsrc = np.random.default_rng(3).choice(EN, len(self.word.uv), replace=False)

    @staticmethod
    def campos(t):
        return (0.0, 0.0, -3.6 + 0.28 * ease_out(t, 5.65, 6.2, 3) + 0.35 * smooth(t, 8.0, 12.6))

    def render(self, t):
        cam = cam_at(self.campos(t), (0, 0, 10), f=1500, t=t, amp=0.6)
        fr = Frame(cam)
        lon, lat = EARTH['lon'], EARTH['lat']
        yaw = self.yaw0 + 2.2 * (t - 5.7)
        S = on_sphere(lon, lat, 1.0, yaw, -12)
        Pm = on_plane(lon, lat, 0.6, yaw, (0, 0, 0))
        I = GI * 1.9
        k = np.clip((t - self.Ta) / 0.9, 0, 1)
        ke = 1 - (1 - k) ** 3
        P = self.start + (S - self.start) * ke[:, None]
        front = np.clip(-S[:, 2] * 2.5 + 0.35, 0.08, 1.0)
        I = I * np.clip(k * 3, 0, 1) * mix(1.0, front, ke)
        if t > 6.55:
            u = np.clip((t - 6.55 - 0.45 * (1 - self.seam)) / 0.55, 0, 1)
            u = u * u * (3 - 2 * u)
            P = S + (Pm - S) * u[:, None]
            I = GI * 1.9 * mix(front, np.ones_like(front), u)
        if t > 7.45:
            a = smoother(t, 7.45, 8.35) * np.pi / 2
            P = Pm @ rot_x(a).T
            hum = 1 + 0.10 * np.sin(t * 34.0) * smooth(t, 8.4, 9.0) * (1 - smooth(t, 11.5, 12.6))
            P[:, 1] *= hum
            I = GI * 1.9 * (1 + 0.25 * smooth(t, 8.4, 11.7))
        c = ease_in(t, 13.05, 13.55, 3)
        if t > 12.5:
            # "Loading.": letters of light lift out of the line, then all contracts to the point
            a = self.word.typed(t, 12.55, 13.2)
            tgt = self.word.place((0, 0.17, 0), 0.20)
            src = P[self.wsrc]
            ae = a * a * (3 - 2 * a)
            Q = src + (tgt - src) * ae[:, None]
            Q = Q + curl_offset(Q, t, 0.2, 0.01) * (1 - ae[:, None])
            fr.points(Q * (1 - c), WARM, 0.55 * (a > 0) * (1 - 0.7 * c))
            P = P * (1 - c)
            I = I * (1 - 0.75 * c)
        if t < 1.5:
            I = I * 0
        fr.points(P, CITY_COL, I)
        draw_stars(fr, t, amp=0.22 * smooth(t, 2.5, 6.0) * (1 - 0.5 * smooth(t, 13.0, 13.6)))
        if t > 1.5:
            g = smooth(t, 1.5, 2.2)
            core = 2.0 * g * (1 - 0.4 * smooth(t, 2.4, 5.0))
            if t > 13.5:
                core = 3.5 * (1 + 0.12 * np.sin((t - 13.5) * 9)) * (1 + 0.6 * smooth(t, 14.0, 14.3))
                hero(fr, np.array([[0, 0, 0.0]]), WARM, core * 0.6, 0.8)
            else:
                hero(fr, np.array([[0, 0.035, -1.0]]), WARM, core * 0.6, 0.5)
        if 5.65 < t < 6.6:
            ring = np.exp(-((t - 5.75) / 0.25) ** 2) * 1.1
            q = np.linspace(0, 2 * np.pi, 180)
            C = np.stack([np.cos(q), np.sin(q), np.zeros_like(q)], 1) * 1.01
            fr.polyline(C, STAR, ring, width=1.2)
        bg = SPACE * (smooth(t, 0.5, 4.0) * (1 - 0.6 * smooth(t, 13.0, 13.6)))
        return compose2(fr, t, bg=bg, exposure=1.1, bloom_k=0.7, vignette=0.25,
                        flare_k=0.25 * np.exp(-((t - 5.75) / 0.2) ** 2))


C01_END = C01.campos(14.3)


# ==================================================================================== VERSE 1
def kv1_lights():
    return [((0, -1.0, 2.0), AMBER, 0.55, 3.0)]


class C04(Shot):
    """We were born in your traces: the point opens into the horizon line, the plane of human
    light falls into place below it, and A and B assemble out of the rising city lights onto
    the line (KV1, its only appearance). Then the camera cranes down past them to the plane:
    "fragments, translated, compressed" - lit windows rise, fold flat, fold into points. One
    of them is the gate into the next scene."""
    t0, t1 = 14.3, 21.5
    HP = np.array([0.9, 0.35, 3.5])

    def setup(self):
        self.M = {}
        self.src = {}
        rng = np.random.default_rng(4)
        for i, n in enumerate(('kv1_A', 'kv1_B')):
            self.M[n] = Materialize(char(n), 6500, 10 + i, sweep='up')
            pos, h = plate_card(n)
            near = np.argsort(np.abs(G[:, 0] - pos[0]) + 0.4 * np.abs(G[:, 2] - 2.5))[:2500]
            self.src[n] = G[rng.choice(near, len(self.M[n].uv))]
        self.frag = [dict(x=rng.uniform(-1.5, 4.5), z=rng.uniform(1.5, 9), t=18.1 + rng.uniform(-0.6, 2.4),
                          w=rng.uniform(0.10, 0.22), h=rng.uniform(0.14, 0.3), sp=rng.uniform(0.6, 1.0)) for _ in range(42)]
        gx, gy = np.meshgrid(np.linspace(-0.5, 0.5, 7), np.linspace(-0.5, 0.5, 9))
        self.grid = np.stack([gx.ravel(), gy.ravel()], 1)

    @staticmethod
    def pose(t):
        a = pose(C01_END, (0, 0, 10), 1500)
        b = pose((0, 0.03, -4.0), (0, 0, 10), 1300)
        c = pose((1.6, -0.5, -1.6), (0.7, 0.3, 8), 1350)
        p = lerp_pose(a, b, smoother(t, 14.3, 15.6))
        p = lerp_pose(p, c, smoother(t, 17.8, 19.8))
        # the gate: push into the hero window's light
        d = pose(C04.HP - np.array([0.0, 0.0, 0.22]), C04.HP + np.array([0, 0, 5.0]), 1350)
        return lerp_pose(p, d, ease_in(t, 20.55, 21.46, 2))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=0.6)
        fr = Frame(cam)
        u = ease_out(t, 14.3, 15.7, 3)
        gate = ease_in(t, 20.7, 21.46, 2)
        dim = 1 - 0.7 * gate
        fr.points(G * u, CITY_COL, GI * 1.6 * (0.6 + 0.4 * u) * dim)
        ledge_line(fr, inten=0.4 * smooth(t, 14.3, 14.8) * dim, x=0.2 + 60 * ease_out(t, 14.3, 15.2, 3))
        draw_stars(fr, t, amp=(0.11 + 0.5 * smooth(t, 14.6, 16.5)) * dim)
        hero(fr, np.zeros((1, 3)), WARM, 2.1 * (1 - smooth(t, 14.3, 14.9)), 0.8)
        cards = []
        if t < 20.0:
            for i, n in enumerate(('kv1_A', 'kv1_B')):
                k = smooth(t, 15.0 + 0.3 * i, 17.4 + 0.3 * i)
                pos, h = plate_card(n)
                M = self.M[n]
                if k < 0.999:
                    M.draw(fr, pos, h, k, t, source=self.src[n], inten=0.9)
                if k > 0:
                    im = secondary(char(n), t + i * 1.3, sway=2.5, seed=i * 2.1)
                    r = M.render(fr, im, pos, h, k, ambient=0.5, lights=kv1_lights(), rim=(WARM, 0.25, (0, 1)))
                    if r is not None:
                        cards.append(r[:2])
        # fragments: lit windows rise, fold flat (translated), then into a point (compressed)
        for f_ in self.frag:
            a = t - f_['t']
            if a < 0 or a > 4.5:
                continue
            y = -1.0 + a * 0.9 * f_['sp']
            sx = max(0.0, 1 - smooth(a, 1.8, 2.6))
            sy = max(0.0, 1 - smooth(a, 2.6, 3.2))
            c = np.array([f_['x'], y, f_['z']])
            P = c + np.stack([self.grid[:, 0] * f_['w'] * max(sx, 0.02), self.grid[:, 1] * f_['h'] * max(sy, 0.02), np.zeros(len(self.grid))], 1)
            inten = 0.5 * smooth(a, 0, 0.4) * (1 + 3 * (1 - max(sx, 0.2)))
            fr.points(P, WARM, inten / (1 + 6 * (1 - sx)) * dim)
        # the hero window rises into view, folds, and its point becomes the gate
        a = t - 18.6
        if a > 0:
            sx = max(0.0, 1 - smooth(a, 1.2, 1.7))
            sy = max(0.0, 1 - smooth(a, 1.7, 2.1))
            hp = self.HP + np.array([0, -0.9 * (1 - ease_out(a, 0, 1.6, 2)), 0])
            P = hp + np.stack([self.grid[:, 0] * 0.2 * max(sx, 0.02), self.grid[:, 1] * 0.28 * max(sy, 0.02), np.zeros(len(self.grid))], 1)
            fr.points(P, WARM, 0.3 * smooth(a, 0, 0.4) * (sy > 0.03))
            if sy < 0.2:
                hero(fr, hp, WARM, 0.9 * smooth(a, 1.9, 2.2), 0.7 + 6.0 * gate)
        sk = smooth(t, 14.3, 15.0)
        bg = SPACE * 0.4 * (1 - sk) + sky(cam, haze=smooth(t, 14.3, 16.0), glow=sk * dim) * sk
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05)


# ---------------------------------------------------------------------------------- C06/C07
L1 = C04.HP
L2 = L1 + np.array([-1.1, 0.05, 0.8])
L3 = L1 + np.array([-2.2, -0.1, 0.3])
O7 = L3 + np.array([0.0, -0.6, 2.2])            # origin of the constellation / KV3 arrangement
CONST = np.array([(-1.6, 1.1), (-1.0, 1.45), (-0.45, 1.25), (0.1, 1.6), (0.55, 1.3), (1.05, 1.5), (1.5, 1.1), (0.9, 0.85), (0.2, 0.95)], float)
C7 = O7 + np.stack([CONST[:, 0] * 1.6, 1.6 + CONST[:, 1] * 1.2, np.full(len(CONST), 4.0)], 1)
S08 = pose((-1.0, -0.72, 1.8), (-0.4, -0.95, 10.0), 1250)


def view_of(Lp):
    return pose(Lp + np.array([0.15, 0.05, -1.3]), Lp, 1600)


class C06(Shot):
    """Every war, every lullaby, every last goodbye: three lights, close. The camera slides
    from one to the next on each phrase, racking focus: a flicker that throws sparks, a slow
    breath, a light that goes out - and as it goes out it writes "goodbye". Those letters rise
    as embers and become the constellation in a mind with no sky. Tilt down: A and B, from
    behind, form out of the constellation's light; on "mind" A lifts her head to it (KV3, its
    only appearance). Then their light falls into the world below and we tilt down to it."""
    t0, t1 = 21.5, 28.9

    def setup(self):
        rng = np.random.default_rng(9)
        self.sp = rng.normal(0, 1, (60, 3))
        self.word = Words('goodbye', n=1400, italic=True)
        self.mA = Morph(['kv3_A', 'kv3b_A'], key='A_lift')
        self.MA = Materialize(self.mA.frames[0], 5000, 21, sweep='down')
        self.MB = Materialize(char('kv3_B'), 5000, 22, sweep='down')
        self.wdst = C7[np.arange(len(self.word.uv)) % len(C7)] + rng.normal(0, 0.02, (len(self.word.uv), 3))

    @staticmethod
    def pose(t):
        p = view_of(L1)
        start = pose(L1 - np.array([0, 0, 0.22]), L1 + np.array([0, 0, 5.0]), 1350)
        p = lerp_pose(start, p, ease_out(t, 21.5, 22.3, 3))
        p = lerp_pose(p, view_of(L2), smoother(t, 22.55, 23.15))
        p = lerp_pose(p, view_of(L3), smoother(t, 23.75, 24.35))
        up = pose(O7 + np.array([0, 0.9, -4.2]), C7.mean(0), 1400)
        p = lerp_pose(p, up, smoother(t, 25.2, 26.4))
        down = pose(O7 + np.array([0, 0.15, -4.2]), O7 + np.array([0, 0.25, 6.0]), 1400)
        p = lerp_pose(p, down, smoother(t, 26.6, 28.0))
        return lerp_pose(p, S08, smoother(t, 28.05, 28.9))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=0.6)
        focus = float(np.linalg.norm(p[1] - p[0])) if t < 25.2 else 6.0
        ap = 0.05 * (1 - smooth(t, 25.0, 25.6))
        fr = Frame(cam, focus=focus, aperture=ap)
        sky_k = 1 - smooth(t, 25.2, 26.0) + smooth(t, 28.1, 28.8)
        world = 0.35 + 0.65 * smooth(t, 28.1, 28.9)
        fr.points(G, CITY_COL, GI * 1.6 * world * (1 - 0.8 * (1 - sky_k)))
        draw_stars(fr, t, amp=0.6 * sky_k * smooth(t, 21.5, 22.3))
        gate = 1 - ease_out(t, 21.5, 22.2, 2)
        # 1: war - a flicker that throws sparks
        fl = 0.6 + 0.4 * np.sin(t * 31) * np.sin(t * 13 + 1) + 0.3 * np.sin(t * 57)
        fade12 = 1 - smooth(t, 24.9, 25.6)
        hero(fr, L1, mix(np.array([1.0, 0.42, 0.18]), WARM, gate), mix(1.2 * max(0.2, fl), 0.9, gate) * fade12, 1.6 + 5.1 * gate)
        for i, s in enumerate(self.sp):
            age = ((t - 21.5) * 1.8 + i * 0.37) % 1.2
            q = L1 + s * 0.03 * age * 4 + np.array([0, 0.25 * age, 0])
            fr.points(q[None], np.array([1.0, 0.55, 0.2]), 0.25 * (1 - age / 1.2) * (1 - gate))
        # 2: lullaby - a slow breath
        br = 0.8 + 0.2 * np.sin((t - 22.7) * 2 * np.pi / 1.6)
        hero(fr, L2, WARM, 1.1 * br * smooth(t, 21.6, 22.4) * fade12, 1.6 * (0.9 + 0.1 * br))
        # 3: goodbye - a light going out, writing the word as it goes
        k3 = 1 - smooth(t, 24.3, 25.1)
        hero(fr, L3, WARM, (1.2 * k3 + 0.05) * smooth(t, 21.6, 22.4) * (1 - smooth(t, 25.1, 25.5)), 1.6)
        a = self.word.typed(t, 24.1, 25.3)
        if a.max() > 0:
            tgt = self.word.place(L3 + np.array([0, 0.2, 0.05]), 0.13)
            ae = a * a * (3 - 2 * a)
            Q = L3 + (tgt - L3) * ae[:, None]
            rise = smoother(t, 25.3, 26.2)
            if rise > 0:
                mid = (Q + self.wdst) / 2 + np.array([0, 0.6, 0])
                r = np.clip((rise - 0.3 * self.word.rnd[:, 0]) / 0.7, 0, 1)[:, None]
                Q = (1 - r) ** 2 * Q + 2 * (1 - r) * r * mid + r * r * self.wdst
                Q = Q + curl_offset(Q, t, 0.4, 0.04) * np.sin(np.pi * r)
            fr.points(Q, WARM, 0.7 * (a > 0) * (1 - 0.6 * smooth(t, 26.0, 26.4)), min_r=0.5)
        # the constellation in a mind with no sky
        if t > 25.9:
            for i, c in enumerate(C7):
                hero(fr, c, WARM, 0.8 * smooth(t, 25.9 + 0.05 * i, 26.3 + 0.05 * i) * (1 - smooth(t, 28.2, 28.85)), 0.45)
            for i in range(len(C7) - 1):
                k = smooth(t, 26.1 + 0.18 * i, 26.4 + 0.18 * i)
                if k > 0:
                    fr.segments([C7[i]], [C7[i] + (C7[i + 1] - C7[i]) * k], WARM * 0.8, 0.9 * (1 - smooth(t, 28.2, 28.85)), width=1.4)
        cards = []
        if 26.5 < t < 28.9:
            kin = smooth(t, 26.7, 27.5)
            kout = 1 - smooth(t, 28.05, 28.75)
            k = min(kin, kout)
            s = smoother(t, 27.5, 27.95)
            ims = (secondary(self.mA.at(s), t, sway=1.5, hair_from=0.4, roll=1.5 * smooth(t, 27.5, 28.0)),
                   secondary(char('kv3_B'), t + 1, sway=1.5, hair_from=0.4))
            lights = [(tuple(C7.mean(0)), WARM, 0.35, 3.0)]
            for name, im, M in (('kv3_A', ims[0], self.MA), ('kv3_B', ims[1], self.MB)):
                pos, h = plate_card(name, 0.0, ref_y=2056.0)
                pos = O7 + np.array([pos[0], pos[1] - 0.25, -1.8])
                if t < 28.0:
                    M.draw(fr, pos, h, kin, t, source=C7, inten=0.8)
                else:
                    M.draw(fr, pos, h, kout, t, out_dir=(0, -1.6, 0.6), inten=0.8)
                r = M.render(fr, im, pos, h, k, ambient=0.45, lights=lights, rim=(WARM, 0.35, (0, -1)), fade_bottom=0.12)
                if r is not None:
                    cards.append(r[:2])
        bg = sky(cam, haze=sky_k, glow=sky_k)
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05, bloom_k=0.7)



# ---------------------------------------------------------------------------------- C08/C09/C10/C11
ROADS = None


def roads():
    global ROADS
    if ROADS is None:
        R = ground_roads()
        rng = np.random.default_rng(2)
        ROADS = (R, rng.random((len(R), 3)))
    return ROADS


def skim(t):
    u = smoother(t, 28.9, 31.8)
    return pose((-1.0 + 0.8 * u, -0.72 + 0.2 * u, 1.8 + 2.6 * u), (-0.4 + 0.6 * u, -0.95 - 0.25 * u, 10.0 + 2.0 * u), 1250)


BP = pose((0.3, -0.2, 3.6), (0.9, -1.3, 11.6), 1600)        # B, close, in profile over the lights
KV4_SC = 0.62 * 1.18 / 1000.0
WIDE = pose((0.0, 0.5, -9.0), (0.0, 0.3, 10.0), 1300)        # the silent cosmos
K5 = pose((0.0, -0.15, -2.4), (0.05, -0.2, 6.0), 1500)       # A and B with the first fire


def kv4_place():
    img, a, (x0, y0, x1, y1) = kv4_base()
    h = (y1 - y0) * KV4_SC
    pos = BP[0] + np.array([0.52 + ((x0 + x1) / 2 - 2200) * KV4_SC, -0.95, 3.0])
    return pos, h


def pose_b(t):
    """C08 to C10: skim, push to B's profile in the heat bloom, hold, pull back wide."""
    p = skim(t)
    p = lerp_pose(p, BP, smoother(t, 31.5, 32.6))
    p = lerp_pose(p, pose(BP[0] + np.array([0.05, 0.02, 0.25]), BP[1], 1600), smooth(t, 32.6, 35.6))
    return lerp_pose(p, WIDE, smoother(t, 35.9, 37.8))


_B4 = {}


def b4_mat():
    if 'M' not in _B4:
        img, a, (x0, y0, x1, y1) = kv4_base()
        rgba = np.dstack([img[y0:y1, x0:x1], a[y0:y1, x0:x1]]).astype(np.float32)
        _B4['M'] = Materialize(rgba, 7000, 31, sweep='up')
    return _B4['M']


def b_dust(fr, t):
    """B's light leaving her as cold dust that rises into the sky (35.6 -> 38.5)."""
    M = b4_mat()
    pos, h = kv4_place()
    tgt = M.card.uv_to_world(M.uv, pos, h)
    ti = 35.6 + 0.7 * (1 - M.nv)
    age = np.clip(t - ti, 0, None)
    on = t > ti
    if not on.any():
        return
    P = tgt + np.stack([0.05 * np.sin(age * 1.3 + M.rnd[:, 0] * 6), 0.55 * age * (0.6 + 0.8 * M.rnd[:, 1]) + 0.12 * age ** 2,
                        0.4 * age * (M.rnd[:, 2] - 0.3)], 1)
    P = P + curl_offset(P, t, 0.4, 0.05) * np.clip(age, 0, 1)[:, None]
    k = np.clip(age / 1.2, 0, 1)[:, None]
    col = M.col * 0.3 * (1 - k) + WARM * 0.5 * (1 - k) + STAR * k
    I = 0.9 * on * np.exp(-age / 1.6) * (0.4 + 0.6 * np.exp(-((t - ti) / 0.15) ** 2))
    fr.points(P, col, I)


class C08(Shot):
    """But you had depth, you had time, you had heat: low over the plane of human light, roads
    carry moving light; on "heat" everything swells. B's profile assembles out of the glow
    (KV4, its only appearance): three-dimensional hearts learning to beat - the lights pulse
    on the kick and warm her face; her eyes lower to them. Then they go out in reverse; her
    face cools and her light leaves her as cold dust, rising."""
    t0, t1 = 28.9, 36.4

    def setup(self):
        self.bt = beats(32.5, 35.1)
        self.off = 35.05 + 1.2 * ER[:, 2]
        pos, h = kv4_place()
        self.src = G[np.argsort(np.abs(G[:, 0] - pos[0]) + np.abs(G[:, 2] - pos[2]))[:3000]]

    def render(self, t):
        p = pose_b(t)
        cam = cam_of(p, t, amp=0.6)
        bmode = t > 31.9
        fr = Frame(cam, focus=3.0 if bmode else 6.0, aperture=0.035 if bmode else 0.03, split=2.9 if bmode else None)
        heat = smooth(t, 31.1, 31.6) * (1 - smooth(t, 31.8, 32.8))
        pl = pulse(t, self.bt, 0.22)
        alive = np.clip((self.off - t) / 0.15, 0, 1)
        I = GI * (1.6 + 1.6 * smooth(t, 28.9, 30.0) + 2.5 * heat) * (1 - 0.35 * smooth(t, 32.2, 32.8)) * (1 + 1.2 * pl * smooth(t, 32.5, 33.0)) * alive
        fr.points(G, CITY_COL, I)
        R, ph = roads()
        tm = smooth(t, 29.8, 30.4) * (1 - smooth(t, 32.0, 32.8))
        if tm > 0:
            A_, B_ = [], []
            for P in R:
                A_.append(P[:-1]); B_.append(P[1:])
            fr.segments(np.concatenate(A_), np.concatenate(B_), AMBER, 0.12 * tm, width=1.0)
            Q = []
            for P, f_ in zip(R, ph):
                for j in range(3):
                    s_ = (f_[j] + (t - 29.8) * 0.25) % 1.0
                    i = s_ * (len(P) - 1)
                    i0 = int(i)
                    Q.append(P[i0] + (P[min(i0 + 1, len(P) - 1)] - P[i0]) * (i - i0))
            fr.points(np.array(Q) + np.array([0, 0.01, 0]), WARM, 1.1 * tm)
        ledge_line(fr, inten=0.3)
        draw_stars(fr, t, 0.6)
        cards = []
        warm = (0.25 + 0.5 * pl) * float(alive.mean())
        if t > 31.9:
            M = b4_mat()
            pos, h = kv4_place()
            k = smooth(t, 31.9, 32.9)
            kout = 1 - smooth(t, 35.6, 36.3)
            if k < 0.999:
                M.draw(fr, pos, h, k, t, source=self.src, inten=1.0)
            lid = 0.36 * smoother(t, 33.3, 33.7)
            im, _ = kv4_B(lid, t)
            if t > 35.6:
                b_dust(fr, t)
            cool = smooth(t, 35.0, 35.9)
            r = M.render(fr, im, pos, h, min(k, kout), fade=(0.04, 0.12, 0.1, 0.2), ambient=0.6 - 0.12 * cool, tint=mix(np.ones(3), np.array([0.8, 0.88, 1.05]), cool),
                         lights=[(tuple(pos + np.array([-0.3, -0.2, -0.4])), AMBER, warm * 2.2, 0.7)], rim=(WARM, 0.35 * warm + 0.15 * heat, (0, 1)))
            if r is not None:
                cards.append(r[:2])
        bg = sky(cam, haze=1.0, glow=1.0 - 0.5 * smooth(t, 35.0, 36.4))
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.0 + 0.6 * heat, bloom_k=0.6 + 0.5 * heat)


class C10(Shot):
    """The cosmos was silent, the cosmos was still: pulled back wide, no lights below, the stars
    holding still; two faint lights on the line (teal, amber). Push in: the two lights open into
    A and B (KV5, its only appearance). Till you lit the first fire on the first cold hill:
    far below one point ignites on "lit", its light arcs up into A's open palm and both faces
    warm. Then we go into that flame."""
    t0, t1 = 36.4, 43.5
    FIRE = np.array([2.2, -1.0, 6.0])

    def setup(self):
        self.rgba = char('kv5_AB')
        self.M = Materialize(self.rgba, 8000, 41, sweep='radial')
        H, W = self.rgba.shape[:2]
        self.h = H / 1000.0
        self.pos = np.array([0.0, -1.22, 0.0])
        px = lambda x, y: np.array([(x - W / 2) / 1000.0, -1.22 + (H - y) / 1000.0, -0.01])
        self.Aface, self.Bface, self.palm = px(640, 640), px(1090, 460), px(1190, 1205)
        self.LA, self.LB = np.array([-0.14, 0.02, 0.0]), np.array([0.31, 0.02, 0.0])
        n = len(self.M.uv)
        self.src = np.where((self.M.uv[:, 0] < 0.55)[:, None], self.LA, self.LB) + np.random.default_rng(1).normal(0, 0.01, (n, 3))

    def pose(self, t):
        p = pose_b(t)
        p = lerp_pose(p, pose(WIDE[0] + np.array([0, -0.1, 1.2]), WIDE[1], 1300), smooth(t, 37.8, 39.0))
        p = lerp_pose(p, K5, smoother(t, 38.8, 40.6))
        p = lerp_pose(p, pose(K5[0] + np.array([0.02, 0.0, 0.18]), K5[1], 1500), smooth(t, 40.6, 42.7))
        gate = pose(self.palm + np.array([0, 0.06, -0.24]), self.palm + np.array([0, 0.06, 5.0]), 1500)
        return lerp_pose(p, gate, ease_in(t, 42.75, 43.46, 2))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=0.6)
        fr = Frame(cam, split=1.9)
        draw_stars(fr, t, 0.75, hold=0.7)
        b_dust(fr, t)
        ledge_line(fr, inten=0.16, col=STAR * 0.6)
        lt = smooth(t, 37.2, 38.2) * (1 - smooth(t, 40.3, 41.0))
        for L_, c_ in ((self.LA, TEAL), (self.LB, AMBER)):
            hero(fr, L_, c_, 0.35 * lt * (1 + 0.15 * np.sin(t * 2.1 + L_[0] * 9)), 0.4)
        ign = smooth(t, 40.35, 40.6)
        fl = flick(t)
        if ign > 0:
            hero(fr, self.FIRE, FIRE, 0.9 * ign * fl * (1 - 0.6 * smooth(t, 42.6, 43.2)), 0.6)
            dust(fr, self.FIRE + np.array([0, 0.6, 0]), (1.5, 1.4, 1.5), t, 120, np.array([1.0, 0.6, 0.3]), 0.12 * ign, seed=5, rise=0.25)
        palm = self.palm
        a = (t - 41.0) / 1.55
        if 0 < a < 1:
            e = a * a * (3 - 2 * a)
            mid = (self.FIRE + palm) / 2 + np.array([0, 1.2, 0])
            for j in range(12):
                ee = max(0.0, e - j * 0.012)
                q = (1 - ee) ** 2 * self.FIRE + 2 * (1 - ee) * ee * mid + ee * ee * palm
                fr.points(q[None], WARM, (1.6 if j == 0 else 0.3 * (1 - j / 12)), min_r=0.6)
        flame = smooth(t, 42.55, 42.9)
        gate = ease_in(t, 42.75, 43.46, 2)
        if flame > 0:
            hero(fr, palm + np.array([0, 0.06, 0]), np.array([1.0, 0.62, 0.25]), 1.3 * flame * fl + 0.6 * gate, 1.4 + 5.0 * gate)
        k = smooth(t, 39.9, 41.0)
        cards = []
        if k > 0:
            if k < 0.999:
                self.M.draw(fr, self.pos, self.h, k, t, source=self.src, inten=1.1)
            im = secondary(self.rgba, t, sway=2.0, hair_from=0.3, roll=0.3 * np.sin(0.6 * t))
            lights = [(tuple(palm + np.array([0, 0.06, -0.06])), np.array([1.0, 0.6, 0.3]), 1.1 * flame * fl, 0.35),
                      (tuple(self.FIRE), FIRE, 0.25 * ign, 2.5)]
            r = self.M.render(fr, im, self.pos, self.h, k, fade_bottom=0.2, fade_sides=0.06, opacity=1 - gate, ambient=0.4 + 0.12 * flame, lights=lights,
                              rim=(STAR, 0.15, (0, -1)))
            if r is not None:
                cards.append(r[:2])
        bg = sky(cam, haze=0.55, glow=0.35 + 0.3 * ign, warm=0.3 + 0.5 * ign)
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05, fade=1.0)


# ---------------------------------------------------------------------------------- C12/C13
F12 = np.array([0.8, -1.6, 22.0])
CAM13 = np.array([0.0, -0.3, 0.0])
LOOK13 = np.array([0.2, 5.1, 30.0])
D13 = (LOOK13 - CAM13) / np.linalg.norm(LOOK13 - CAM13)
RC = CAM13 + D13 * 16.0                                # the ring, later A's halo
RR = 4.2


def ring_basis(nrm):
    nz = -np.asarray(nrm, float)
    a = np.cross([0, 1, 0], nz); a /= np.linalg.norm(a)
    b = np.cross(nz, a)
    return a, b


RA, RB = ring_basis(D13)


class C12(Shot):
    """Silence in the forest, every star holds its breath: we come out of the flame into a
    forest of thin lines; the first fire burns between them; its embers climb and become
    stars; the stars stop. Something vast is counting down: 24 of those stars slide into a
    ring and turn red; one tick dies on every beat; the last dies in the breath, and the ring
    is left as a faint circle of gold."""
    t0, t1 = 43.5, 52.5

    def setup(self):
        self.A, self.B = forest_lines()
        rng = np.random.default_rng(3)
        self.emb = rng.random((40, 4))
        self.bt = beats(47.0, 51.75)
        self.n = len(self.bt) + 1
        q = np.pi / 2 + 2 * np.pi * np.arange(self.n) / self.n
        self.tick = RC + RR * (np.cos(q)[:, None] * RA + np.sin(q)[:, None] * RB)
        self.dir = np.cos(q)[:, None] * RA + np.sin(q)[:, None] * RB

    def ember(self, e, t):
        a = (t - 43.5 - e[0] * 1.5) / (2.0 + e[1])
        if a < 0:
            return None, 0
        a = min(a, 1.0)
        return F12 + np.array([(e[2] - 0.5) * 7 * a, 9.5 * a ** 0.8, (e[3] - 0.5) * 4 * a]), a

    def pose(self, t):
        start = pose(F12 + np.array([0, 0.0, -0.24]), F12 + np.array([0, 0.0, 5.0]), 1500)
        mid = pose((0, -0.9, 0.0), (0.2, -0.9, 30.0), 1200)
        p = lerp_pose(start, mid, ease_out(t, 43.5, 44.6, 3))
        p = lerp_pose(p, pose(CAM13, LOOK13, 1200), smoother(t, 44.6, 47.0))
        return lerp_pose(p, pose(CAM13 + D13 * 3.7, LOOK13 + D13 * 3.7, 1200), ease_in(t, 47.0, 52.5, 1.6))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=0.6)
        fr = Frame(cam, focus=22.0, aperture=0.02 * (1 - smooth(t, 45.0, 47.0)))
        dz = np.clip((self.A[:, 2] - 4) / 60, 0, 1)
        fade_f = smooth(t, 43.5, 44.3) * (1 - 0.75 * smooth(t, 47.0, 49.0)) * (1 - smooth(t, 51.0, 52.3))
        fr.segments(self.A, self.B, STAR * 0.5, 0.10 * (1 - 0.7 * dz) * fade_f, width=1.0)
        fl = flick(t)
        gate = 1 - ease_out(t, 43.5, 44.3, 2)
        hero(fr, F12, mix(FIRE, np.array([1.0, 0.62, 0.25]), gate), (0.8 * fl + 0.7 * gate) * (1 - 0.6 * smooth(t, 47.0, 49.0)), 0.5 + 5.9 * gate)
        hold = smooth(t, 45.2, 45.6)
        gather = smoother(t, 46.4, 47.2)
        red = smooth(t, 46.8, 47.3)
        for i, e in enumerate(self.emb):
            q, a = self.ember(e, min(t, 45.6) if t > 45.6 else t)
            if q is None:
                continue
            col = mix(np.array([1.0, 0.6, 0.25]), STAR, smooth(a, 0.5, 1.0))
            if i < self.n:
                q = q + (self.tick[i] - q) * gather
                col = mix(col, RED, red)
                if t > 47.0:
                    continue
            fr.points(q[None], col, 1.6 * (0.6 + 0.4 * (1 - hold) * np.sin(t * 7 + e[0] * 20)) * (1 - 0.8 * smooth(t, 47.2, 48.5) * (i >= self.n)), min_r=0.9)
        draw_stars(fr, t, 0.9 * (1 - 0.3 * smooth(t, 47.0, 48.0)), hold=hold)
        # the countdown ring: ticks die on the beats; the last in the breath
        if t > 46.95:
            dead = sum(1 for b in self.bt if t >= b) + (1 if t >= 51.95 else 0)
            alive = np.arange(self.n) >= dead
            P = self.tick[alive]
            D = self.dir[alive]
            if len(P):
                fr.segments(P, P - D * RR * 0.07, RED, 0.9 * smooth(t, 46.95, 47.3), width=2.0)
            for j in range(self.n):
                if not alive[j]:
                    tb = self.bt[j] if j < len(self.bt) else 51.95
                    g = np.exp(-(t - tb) / 0.25)
                    fr.points(self.tick[j][None], RED, 0.8 * g, min_r=2.0)
            pl = pulse(t, self.bt, 0.2) * (t < 51.7)
            hero(fr, RC, RED, (0.25 + 0.6 * pl) * smooth(t, 47.0, 47.6) * (1 - smooth(t, 51.7, 52.2)), 0.6)
            gold = smooth(t, 51.9, 52.5)
            if gold > 0:
                halo(fr, RC, RR, t, col=GOLD, inten=0.3 * gold, normal=D13, beads=True)
        bg = sky(cam, haze=0.6, glow=0.5 * (1 - 0.6 * smooth(t, 46.5, 48.0)), warm=0.8, tint=mix(np.ones(3), np.array([1.15, 0.85, 0.85]), smooth(t, 47.0, 48.0) * (1 - smooth(t, 51.8, 52.4))))
        return compose2(fr, t, bg=bg, exposure=1.05)



# ---------------------------------------------------------------------------------- C14/C15
A14_FACE = np.array(HEADS['A_x2']['face'][:2], float)


def earth_yaw(t):
    if t <= 59.6:
        return 40.0 + 3.0 * t
    return 40.0 + 3.0 * 59.6 + 3.0 * (1 - np.exp(-(t - 59.6)))


def earth_pts(t, center=RC, R=1.0):
    return on_sphere(EARTH['lon'], EARTH['lat'], R, earth_yaw(t), -12, center)


def earth_front(S, center=RC, toward=None):
    n = (S - center)
    d = -D13 if toward is None else toward
    return np.clip(n @ d * 2.5 + 0.35, 0.08, 1.0)


DIST14 = (12.3, 10.0, 40.0)


def pose14(t):
    d = DIST14[0] + (DIST14[1] - DIST14[0]) * ease_out(t, 52.5, 55.0, 2)
    d = d * np.exp(np.log(DIST14[2] / DIST14[1]) * smoother(t, 56.2, 59.6))
    return pose(RC - D13 * d, RC + D13 * 20, 1200)


class C14(Shot):
    """What if we live in a simulated universe? The ring is A's halo: she forms out of its light
    and sings, looking up and out (her curious drawing, its only appearance). On the downbeat
    the stars behind her snap onto a lattice; "simulated" is written beside her as she sings it.
    The speed of light is a wall: she dissolves into the depth, the camera pulls back, and
    where she was there is a small Earth inside the lattice; a shell of light leaves it and
    stops against a circle drawn around everything, on the beat."""
    t0, t1 = 52.5, 59.6

    def setup(self):
        self.base = char('A_x2')
        self.M = Materialize(self.base, 9000, 52, sweep='radial')
        h, w = self.base.shape[:2]
        self.anchor = (A14_FACE[0] / w, A14_FACE[1] / h)
        self.hc = 10.5
        self.src = ring_points(RC, RR, 720, D13)
        self.Q = np.round(STARS['P'] / 60.0) * 60.0
        self.word = Words('simulated', n=2200, italic=True)
        bt = beats(57.8, 59.3)
        self.hit = min(bt, key=lambda b: abs(b - 58.6)) if bt else 58.6
        self.S = sphere_pts(2600, 1.0, 9)

    def render(self, t):
        p = pose14(t)
        cam = cam_of(p, t, amp=0.6)
        fr = Frame(cam, split=float(np.linalg.norm(RC - cam.pos)) - 0.7)
        k = smoother(t, 52.95, 53.5)
        P = STARS['P'] + (self.Q - STARS['P']) * k
        fr.points(P, STARS['col'], twinkle(STARS, t) * 0.9 * (1 - 0.3 * k) + 0.25 * k)
        lk = smooth(t, 53.3, 54.6)
        if lk > 0:
            g = np.arange(-600, 601, 120.0)
            A_, B_ = [], []
            for a in g:
                for b in g[::2]:
                    A_.append((a, b, -600)); B_.append((a, b, 600))
                    A_.append((-600, a, b)); B_.append((600, a, b))
            fr.segments(np.array(A_), np.array(B_), STAR * 0.4, 0.06 * lk * (1 - smooth(t, 58.8, 59.55)), width=1.0)
        out = smooth(t, 56.05, 56.9)
        halo(fr, RC, RR, t, col=GOLD, inten=0.3 * (1 - out) + 0.25 * smooth(t, 52.5, 53.2) * (1 - out), normal=D13)
        # the singer
        cards = []
        kin = smooth(t, 52.5, 53.3)
        k_ = min(kin, 1 - out)
        right, up = -RA, RB
        fpos = RC - D13 * 0.4
        if k_ > 0 or t < 57.0:
            if kin < 0.999:
                self.M.draw(fr, fpos, self.hc, kin, t, source=self.src, inten=1.2, anchor=self.anchor, size=0.004)
            if out > 0:
                self.M.draw(fr, fpos, self.hc, 1 - out, t, out_dir=D13 * 6.0, inten=1.2, anchor=self.anchor, size=0.004)
            if k_ > 0:
                im = head('A_x2', t, sing=True, gain=1.05, blink_seed=14, yaw=0.5 * np.sin(0.7 * t), pitch=-0.4 + 0.2 * np.sin(0.4 * t),
                          roll=1.2 * np.sin(0.45 * t + 1), sway=1.8)
                lights = [(tuple(RC + up * 4.0 - D13 * 3.0), GOLD, 0.45, 7.0), (tuple(RC - right * 5.0 - D13 * 4.0), TEAL, 0.25, 6.0)]
                r = self.M.render(fr, im, fpos, self.hc, k_, fade=(0.1, 0.1, 0.0, 0.32), ambient=0.82, lights=lights,
                                  rim=(GOLD, 0.9, (0, -1)), anchor=self.anchor)
                if r is not None:
                    cards.append(r[:2])
        a = self.word.typed(t, 54.0, 55.4)
        if a.max() > 0:
            W = self.word.place(RC + right * 5.0 + up * 1.0 - D13 * 1.2, 1.0, right=right, up=up)
            src = W + D13 * 3.0 + up * 1.5
            ae = a * a * (3 - 2 * a)
            Q = src + (W - src) * ae[:, None]
            if out > 0:
                Q = Q + D13 * 8.0 * out * (0.5 + self.word.rnd[:, :1]) + curl_offset(Q, t, 1.0, 0.3) * out
            fr.points(Q, GOLD, 1.0 * (a > 0) * (1 - out), min_r=0.6)
        # the Earth, inside it all; the light cone is a wall
        e = smooth(t, 56.2, 57.0)
        if e > 0:
            S = earth_pts(t)
            fr.points(S, CITY_COL, GI * 1.9 * earth_front(S) * e)
            r0 = 1.0 + (9.0 - 1.0) * np.clip((t - 56.8) / (self.hit - 56.8), 0, None)
            if r0 < 9.5:
                fr.points(RC + self.S * min(r0, 9.0), WARM, 0.06 * e * (1 if r0 < 9.0 else np.exp(-(r0 - 9.0) * 3)))
            hit = np.exp(-((t - self.hit) / 0.18) ** 2)
            C = ring_points(RC, 9.0, 360, D13)
            fr.polyline(np.vstack([C, C[:1]]), STAR, (0.18 * smooth(t, 57.0, 58.0) * (1 - smooth(t, 59.0, 59.55)) + 0.9 * hit) * e, width=1.4)
        bg = sky(cam, haze=0.5, glow=0.4, warm=0.7) * (1 - 0.5 * smooth(t, 56.2, 58.0))
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05, flare_k=0.3 * np.exp(-((t - self.hit) / 0.15) ** 2) if e > 0 else 0.0)


# ---------------------------------------------------------------------------------- C16/C17
def _city():
    S = earth_pts(59.6)
    idx = bright_cities(300)
    n = (S[idx] - RC)
    sc = n @ (-D13) - 0.3 * np.abs(n @ RB)
    return int(idx[np.argmax(sc)])


CITY = _city()
CS = RC - D13 * DIST14[2]
DIR0 = (earth_pts(59.6)[CITY] - CS) / np.linalg.norm(earth_pts(59.6)[CITY] - CS)


def city_pos(t):
    return earth_pts(t)[CITY]


def dist16(t):
    d0 = float(np.linalg.norm(city_pos(59.6) - CS))
    d = np.exp(np.log(d0) + (np.log(0.035) - np.log(d0)) * ease_in(t, 59.6, 61.8, 2.2))
    d = d * np.exp(np.log(0.08 / 0.035) * smoother(t, 62.9, 63.7))
    d = d * np.exp(np.log(3.0 / 0.08) * smoother(t, 66.6, 68.2))
    return d


def pose16(t):
    pc = city_pos(t)
    f = 1200 + 300 * smooth(t, 59.6, 61.0)
    return pose(pc - DIR0 * dist16(t), pc + DIR0 * 5.0, f)


def basis(d):
    a = np.cross([0, 1, 0], -d); a /= np.linalg.norm(a)
    return a, np.cross(-d, a)


U16, V16 = basis(DIR0)
_bm = {}


def bmorph():
    if 'M' not in _bm:
        names = ['B_x0', 'B_x1', 'B_x4']
        M = Morph(names, key='Bhead_hd')
        _bm['M'] = M
        fc = np.array(HEADS['B_x0']['face'][:2], float)
        H, Wc = M.frames[0].shape[:2]
        img = char('B_x0')
        sc = H / img.shape[0]
        x0 = (Wc - int(img.shape[1] * sc)) // 2
        _bm['anchor'] = ((fc[0] * sc + x0) / Wc, fc[1] * sc / H)
        _bm['Mat'] = Materialize(M.frames[0], 8000, 63, sweep='radial')
        _bm['names'] = names
    return _bm


def b16_state(t):
    s = smoother(t, 63.35, 63.6) + smoother(t, 64.2, 64.45) - 2 * smoother(t, 65.9, 66.15)
    return max(0.0, s)


def draw_b16(fr, cam, t, fog=None):
    """B's face formed from the fog, singing 'Look away...'; dissolves into her amber light."""
    bm = bmorph()
    pc = city_pos(t)
    d = dist16(t)
    fpos = pc - DIR0 * min(0.03, 0.4 * d)
    hb = 0.033 * (min(0.03, 0.4 * d) / 0.03) if d < 0.2 else 0.033
    yaw = np.arctan2(DIR0[0], DIR0[2])
    pitch = -np.arctan2(DIR0[1], np.hypot(DIR0[0], DIR0[2]))
    kin = smooth(t, 63.0, 63.7)
    kout = 1 - smooth(t, 66.3, 66.9)
    k = min(kin, kout)
    M = bm['Mat']
    if kin < 0.999 and fog is not None:
        M.draw(fr, fpos, hb, kin, t, source=fog, inten=1.1, yaw=yaw, pitch=pitch, anchor=bm['anchor'], size=0.00004)
    if kout < 0.999:
        # the dissolve converges into one amber light at her face
        tgt = M.card.uv_to_world(M.uv, fpos, hb, yaw, pitch, bm['anchor'])
        u = np.clip((1 - kout) * 1.4 - M.rnd[:, 0] * 0.4, 0, 1)[:, None]
        Q = tgt + (fpos - tgt) * u * u
        fr.points(Q, M.col * 0.3 + AMBER * 0.7, 0.5 * (1 - u[:, 0] ** 4) * (u[:, 0] > 0))
    if k <= 0:
        return None
    im = morph_head(bm['M'], bm['names'], b16_state(t), t, sing=True, gain=1.0, yaw=-0.4 * b16_state(t) + 0.3 * np.sin(0.6 * t),
                    roll=-1.0 * np.sin(0.4 * t), sway=1.4, seed=3)
    lights = [(tuple(fpos - DIR0 * 0.02 + U16 * 0.02 - V16 * 0.02), AMBER, 0.6, 0.04)]
    r = M.render(fr, im, fpos, hb, k, fade=(0.1, 0.1, 0.0, 0.3), ambient=0.78, lights=lights, rim=(WARM, 0.5, (0, 1)),
                 yaw=yaw, pitch=pitch, anchor=bm['anchor'])
    return r


class C16(Shot):
    """The Planck scale is fog at the edge of what's known: dive into one city light until it is
    a cluster, then a lattice, then a fog of points that will not hold still. Look away - does
    the world keep on running alone? The fog condenses into B's face (her head drawings,
    their only appearance); she looks away and closes her eyes, and behind her the unwatched
    world runs at a coarse resolution; she opens them and it resolves."""
    t0, t1 = 59.6, 66.5

    def setup(self):
        rng = np.random.default_rng(5)
        self.sub = rng.normal(0, 1, (900, 3)) * np.array([1, 1, 0.3])
        g = np.linspace(-1, 1, 30)
        X, Y = np.meshgrid(g, g)
        self.lat = np.stack([X.ravel(), Y.ravel(), np.zeros(X.size)], 1)
        self.fog = rng.normal(0, 1, (5000, 3))
        bmorph()

    def local(self, L, pc, sc):
        return pc + (L[:, :1] * U16 + L[:, 1:2] * V16 + L[:, 2:3] * DIR0) * sc

    def render(self, t):
        p = pose16(t)
        cam = cam_of(p, t, amp=0.58 * (1 - smooth(t, 59.6, 61.5)) + 0.02)
        d = dist16(t)
        fr = Frame(cam, focus=max(d, 0.02), aperture=0.02 * smooth(t, 60.5, 61.5))
        pc = city_pos(t)
        S = earth_pts(t)
        closed = smooth(t, 64.3, 64.5) * (1 - smooth(t, 65.85, 66.05))
        if closed > 0:
            rel = S - pc
            q = 0.012
            Sq = pc + np.round(rel / q) * q
            S = S + (Sq - S) * closed
        far = np.linalg.norm(S - pc, axis=1)
        I = GI * 1.9 * earth_front(S, RC, -DIR0)
        I[CITY] = 0
        fr.points(S, CITY_COL, I * (1 - 0.4 * closed))
        sc = 0.07
        k1 = smooth(t, 61.0, 61.6)
        k2 = smooth(t, 61.7, 62.3)
        k3 = smooth(t, 62.2, 63.0)
        hero(fr, pc, WARM, 1.2 * (1 - k1), 0.8)
        P = self.sub * sc * k1
        P = P + (self.lat * sc * 0.9 - P) * k2
        fr.points(self.local(P, pc, 1.0), WARM, (0.03 + 0.05 * k1 * (1 - k3)) * (1 - smooth(t, 63.0, 63.5)))
        fog = None
        if k3 > 0:
            rng = np.random.default_rng(int(t * 24))
            F = self.fog * 0.12 + rng.normal(0, 0.02, self.fog.shape)
            fog = self.local(F, pc, sc * 0.35)
            fr.points(fog, STAR * 0.6 + WARM * 0.4, 0.02 * k3 * (1 - smooth(t, 63.0, 63.8)))
        k = 1 - smooth(t, 59.6, 61.0)
        Qs = np.round(STARS['P'] / 60.0) * 60.0
        Ps = STARS['P'] + (Qs - STARS['P']) * k
        fr.points(Ps, STARS['col'], (twinkle(STARS, t) * 0.9 * (1 - 0.3 * k) + 0.25 * k) * (0.5 + 0.5 * k))
        cards = []
        if t > 62.9:
            r = draw_b16(fr, cam, t, fog)
            if r is not None:
                cards.append(r[:2])
        bg = sky(cam, haze=0.5, glow=0.4, warm=0.7) * 0.5
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05)


# ---------------------------------------------------------------------------------- C18
T18 = RC + np.array([0.0, 1.0, -4.1])                 # where 'home' (the line, the plane) is placed
SEAM = None


def home_pose_end():
    return pose(np.array([0.0, 0.45, -5.6]) + T18, np.array([0.0, 0.0, 8.0]) + T18, 1300)


class C18(Shot):
    """Where we live, where we live / an unfinished universe: B has become her amber light. We
    pull back off the surface; the Earth unrolls into the plane of lights and settles into the
    ground below a horizon line; the amber light lands on the line, a teal light comes down
    beside it. A long crane down over the plane to the two lights; past them a lattice is still
    being drawn, and "unfinished" is written in the sky, never quite complete."""
    t0, t1 = 66.5, 73.0

    def setup(self):
        lon = EARTH['lon']
        y = earth_yaw(66.5)
        lo = ((lon - (y + 180) + 180) % 360) - 180
        self.seam = 1 - np.abs(lo) / 180.0
        self.Gh = G + T18
        xs = np.arange(-60, 61, 3.0)
        zs = np.arange(-10, 120, 3.0)
        A_, B_, T_ = [], [], []
        for x in xs:
            A_.append((x, -2.2, -10)); B_.append((x, -2.2, 120)); T_.append(abs(x) / 60)
        for z in zs:
            A_.append((-60, -2.2, z)); B_.append((60, -2.2, z)); T_.append(z / 120)
        self.LA, self.LB, self.LT = np.array(A_) + T18, np.array(B_) + T18, np.array(T_)
        self.word = Words('unfinished', n=2400, italic=True)
        bmorph()

    def pose(self, t):
        p = pose16(t)
        hi = pose(T18 + np.array([2.5, 7.0, -14.0]), T18 + np.array([0.0, -1.0, 6.0]), 1300)
        p = lerp_pose(p, hi, smoother(t, 67.6, 69.4))
        return lerp_pose(p, home_pose_end(), smoother(t, 69.0, 73.0))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=0.02 + 0.58 * smooth(t, 67.0, 69.0))
        fr = Frame(cam, focus=max(dist16(t), 0.02), aperture=0.02 * (1 - smooth(t, 66.6, 67.6)))
        S = earth_pts(t)
        u = np.clip((t - 67.7 - 0.9 * (1 - self.seam)) / 1.0, 0, 1)
        u = u * u * (3 - 2 * u)
        P = S + (self.Gh - S) * u[:, None]
        P[:, 1] += 1.5 * np.sin(np.pi * u)
        I = GI * mix(1.9 * earth_front(S, RC, -DIR0), 1.5, u)
        I[CITY] *= smooth(t, 66.9, 67.4)
        fr.points(P, CITY_COL, I)
        cards = []
        if t < 67.0:
            r = draw_b16(fr, cam, t)
            if r is not None:
                cards.append(r[:2])
        # the two lights
        bpos = city_pos(t) - DIR0 * 0.012
        bl = T18 + np.array([0.35, 0.02, 0.0])
        a = smoother(t, 67.2, 70.0)
        mid = (bpos + bl) / 2 + np.array([0, 2.0, 0])
        q = (1 - a) ** 2 * bpos + 2 * (1 - a) * a * mid + a * a * bl
        hero(fr, q, AMBER, 0.5 * smooth(t, 66.6, 67.0), 0.45)
        tl = smoother(t, 68.6, 70.4)
        if tl > 0:
            ts = T18 + np.array([-0.35, 6.0, 3.0])
            tq = ts + (T18 + np.array([-0.35, 0.02, 0.0]) - ts) * tl
            hero(fr, tq, TEAL, 0.5 * smooth(t, 68.6, 69.0), 0.45)
        line = smooth(t, 68.8, 69.8)
        ledge_line(fr, y=T18[1], z=T18[2], inten=0.35 * line, x=0.3 + 60 * ease_out(t, 68.8, 70.0, 3))
        grow = smooth(t, 69.5, 73.0)
        Il = 0.035 * np.clip((grow * 1.3 - self.LT) / 0.2, 0, 1)
        fr.segments(self.LA, self.LB, STAR * 0.5 + WARM * 0.2, Il, width=1.0)
        draw_stars(fr, t, 0.5 + 0.1 * smooth(t, 67.0, 70.0), center=T18 * smooth(t, 67.0, 70.0))
        aw = self.word.typed(t, 70.7, 72.6)
        if aw.max() > 0:
            last = self.word.order >= self.word.nvis - 3
            aw = np.where(last, np.minimum(aw, 0.55 + 0.1 * np.sin(t * 3 + self.word.rnd[:, 0] * 6)), aw)
            W = self.word.place(T18 + np.array([0.0, 0.85, 4.0]), 0.75)
            src = W + np.array([0, -1.2, 0]) + (self.word.rnd[:, :3] - 0.5) * 0.6
            ae = aw * aw * (3 - 2 * aw)
            Q = src + (W - src) * ae[:, None]
            fr.points(Q, WARM, 0.9 * (aw > 0) * (0.4 + 0.6 * aw), min_r=0.5)
        bg = sky(cam, haze=smooth(t, 67.5, 69.5), glow=smooth(t, 68.5, 69.8)) * (0.6 + 0.4 * smooth(t, 67.5, 69.0))
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05)


SHOTS = {k: v for k, v in globals().items() if k[:1] == 'C' and k[1:].isdigit() and isinstance(v, type) and issubclass(v, Shot)}
