"""BRIDGE, FINAL CHORUS, OUTRO (2:10-3:33): one continuous camera after the drop-out to black."""
import sys
sys.path.insert(0, '/home/user/OC/loading/src')
from world import *
from lfx import *
from face import head, HEADS, morph_head, blink
import voice


class Shot:
    t0 = t1 = 0.0

    def setup(self):
        pass


G = ground_points()
GI = EARTH['I']
EN = len(GI)
ER = np.random.default_rng(13).random((EN, 4)).astype(np.float32)
AMP = 0.6

LT = CHAIR + np.array([-0.45, 0.75, -0.25])        # A's light
LB = CHAIR + np.array([0.45, 0.75, -0.25])         # B's light
KEYS_C = KEYS.mean(0)
EDGE_MID = (ROOM_A + ROOM_B) / 2


def yp_toward(src, dst):
    d = np.asarray(dst, float) - np.asarray(src, float)
    return float(np.arctan2(d[0], d[2])), float(-np.arctan2(d[1], np.hypot(d[0], d[2])))


def bob(p, t, s):
    return p + np.array([0.0, 0.04 * np.sin(t * 1.3 + s), 0.0])


def room_lit(fr, inten, lights=(LT, LB), floor=0.04):
    """The room drawn only as far as the two lights reach (no one else is here)."""
    d = np.min([np.linalg.norm(EDGE_MID - L, axis=1) for L in lights], axis=0)
    I = inten * (0.55 * np.exp(-d / 1.4) + floor)
    fr.segments(ROOM_A, ROOM_B, STAR * 0.55 + WARM * 0.45, I, width=1.0)


# ==================================================================================== BRIDGE
def pose34(t):
    a = pose(CHAIR + np.array([-1.2, 0.35, -2.0]), CHAIR + np.array([0, 0.25, 0]), 1300)
    a = lerp_pose(a, pose(CHAIR + np.array([-1.0, 0.33, -1.7]), CHAIR + np.array([0, 0.25, 0]), 1300), smooth(t, 130.5, 137.7))
    ang = np.deg2rad(-30 + 75 * smoother(t, 137.7, 141.6))
    r = 1.9
    orb = pose(CHAIR + np.array([r * np.sin(ang), 0.3, -r * np.cos(ang)]), CHAIR + np.array([0, 0.35, 0]), 1300)
    p = lerp_pose(a, orb, smoother(t, 137.2, 138.4))
    face = pose(LB + np.array([-0.15, 0.02, -0.95]), LB + np.array([0, 0.02, 0]), 1400)
    return lerp_pose(p, face, smoother(t, 141.2, 141.9))


B36_ANCH = None


class C34(Shot):
    """There are no gods here: out of the black, two lights - teal and amber - before an empty
    chair; the room is only there where their light reaches. An empty chair isn't an answer: a
    low orbit around the chair. It isn't: the amber light opens into B's face and she says it
    (her thinking drawing, its only appearance), then folds back into her light."""
    t0, t1 = 130.5, 143.2

    def setup(self):
        self.base = char('B_x2')
        h, w = self.base.shape[:2]
        fc = HEADS['B_x2']['face']
        self.anchor = (fc[0] / w, fc[1] / h)
        self.M = Materialize(self.base, 8000, 136, sweep='radial')

    def render(self, t):
        p = pose34(t)
        cam = cam_of(p, t, amp=AMP * 0.6)
        fr = Frame(cam, focus=float(np.linalg.norm(LB - p[0])), aperture=0.01, split=float(np.linalg.norm(LB - cam.pos)) - 0.05)
        up = smooth(t, 130.6, 132.2)
        room_lit(fr, smooth(t, 131.0, 133.5))
        A_, B_ = KEYSQ
        fr.segments(A_, B_, STAR * 0.5, 0.05 * smooth(t, 132.0, 134.0), width=1.0)
        lt, lb = bob(LT, t, 0.0), bob(LB, t, 1.7)
        b_on = smooth(t, 141.45, 141.9) * (1 - smooth(t, 142.85, 143.2))
        hero(fr, lt, TEAL, 0.5 * up, 0.5)
        hero(fr, lb, AMBER, 0.5 * up * (1 - 0.7 * b_on), 0.5)
        dust(fr, CHAIR + np.array([0, 0.9, -0.2]), (2.0, 1.4, 1.6), t, 300, WARM, 0.05 * up, seed=34, rise=0.02)
        cards = []
        hb = 0.62
        pos = lb + np.array([0, 0.0, 0.05])
        yaw, pitch = yp_toward(cam.pos, pos)
        kin = smooth(t, 141.45, 141.95)
        kout = 1 - smooth(t, 142.85, 143.2)
        k = min(kin, kout)
        if kin < 0.999 and t < 142.5:
            self.M.draw(fr, pos, hb, kin, t, source=lb[None], inten=1.0, yaw=yaw, pitch=pitch, anchor=self.anchor, size=0.0005)
        if kout < 0.999:
            tgt = self.M.card.uv_to_world(self.M.uv, pos, hb, yaw, pitch, self.anchor)
            u = np.clip((1 - kout) * 1.4 - self.M.rnd[:, 0] * 0.4, 0, 1)[:, None]
            fr.points(tgt + (lb - tgt) * u * u, self.M.col * 0.3 + AMBER * 0.7, 0.5 * (1 - u[:, 0] ** 4) * (u[:, 0] > 0))
        if k > 0:
            im = head('B_x2', t, sing=True, gain=1.0, blink_seed=36, yaw=0.3 * np.sin(0.8 * t), roll=-1.0 * np.sin(0.5 * t), sway=1.2)
            r = self.M.render(fr, im, pos, hb, k, anchor=self.anchor, yaw=yaw, pitch=pitch, fade=(0.1, 0.1, 0.0, 0.3), ambient=0.6,
                              lights=[(tuple(lb + np.array([0.15, -0.1, -0.2])), AMBER, 0.7, 0.4), (tuple(lt), TEAL, 0.3, 0.6)],
                              rim=(WARM, 0.5, (0, -1)))
            if r is not None:
                cards.append(r[:2])
        bg = gradient_bg((0.015, 0.012, 0.03), (0.025, 0.016, 0.026)) * up
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05, fade=smooth(t, 130.5, 131.3))


# ---------------------------------------------------------------------------------- C37-C40
def key_space(P):
    """Where each point of the map sits on the console: the keys are a small model of the world."""
    x = np.clip(P[:, 0] / 10.0, -1, 1) * 0.8
    z = 4.35 + np.clip((P[:, 2] + 0.55) / 9.4, 0, 1) * 0.5
    return np.stack([x, np.full(len(P), 0.875), z], 1)


KEY_POSE = pose(KEYS_C + np.array([0.35, 0.55, -0.85]), KEYS_C, 1400)
HIGH = pose(np.array([1.5, 3.2, -4.5]), np.array([0.0, -1.0, 6.0]), 1250)
TRAV = 7


def travellers(t):
    """Lantern positions (walking through the forest), with swing."""
    k = np.arange(TRAV)
    x0 = -5.0 + 10.0 * (k + 0.5) / TRAV + 0.6 * np.sin(k * 2.3)
    z0 = 13.0 + 3.0 * np.cos(k * 1.7)
    dirx = 0.25 * np.sin(k * 1.1)
    sp = 0.55 + 0.1 * np.cos(k * 0.9)
    tt = t - 146.4
    x = x0 + dirx * sp * tt
    z = z0 + sp * tt
    sw = 0.05 * np.sin(tt * 2 * np.pi / 0.9 + k)
    return np.stack([x + sw, -0.45 + 0.03 * np.abs(np.sin(tt * np.pi / 0.45 + k)), z], 1), np.stack([x, z], 1)


def footsteps(t, upto):
    """Footstep lights left behind by each traveller every 0.45 s (alternating left/right)."""
    steps = []
    for s_t in np.arange(146.6, min(t, upto), 0.45):
        _, xz = travellers(s_t)
        side = 0.07 * (1 if int((s_t - 146.6) / 0.45) % 2 else -1)
        for k in range(TRAV):
            steps.append((k, s_t, xz[k, 0] + side, xz[k, 1]))
    return steps


def pose37(t):
    p = pose34(143.2)
    p = lerp_pose(p, KEY_POSE, smoother(t, 143.2, 144.3))
    p = lerp_pose(p, HIGH, smoother(t, 145.0, 147.4))
    lc = travellers(t)[0].mean(0)
    walk = pose(lc + np.array([0.6, 0.35, -3.6]), lc + np.array([0, -0.2, 4.0]), 1300)
    p = lerp_pose(p, walk, smoother(t, 147.2, 149.6))
    close = pose(travellers(t)[0][3] + np.array([0.9, 0.15, -1.6]), travellers(t)[0][3] + np.array([0, -0.1, 1.0]), 1350)
    p = lerp_pose(p, close, smoother(t, 150.0, 151.8))
    lf = travellers(155.0)[0].mean(0)
    sky_ = pose(lf + np.array([0.0, 0.0, -10.0]), lf + np.array([0, 6.5, 1.0]), 1250)
    return lerp_pose(p, sky_, smoother(t, 154.8, 157.4))


class C37(Shot):
    """But look who's pressing the keys: the amber light drifts down onto the console and the
    keys begin to light by themselves, faster and faster; pull back - they unfold into the city
    lights of the world. No hunter in the forest, no hand upon the card - only travellers with
    lanterns passing through the dark: lanterns swing between the thin lines of the forest; each
    step leaves a light. Every key is a footstep of someone passing by: the footsteps join into
    paths, and the paths lift into the sky as constellation lines."""
    t0, t1 = 143.2, 158.8

    def setup(self):
        rng = np.random.default_rng(37)
        times = [143.7]
        while times[-1] < 147.0:
            rate = 2.0 + 38.0 * ((times[-1] - 143.7) / 2.4) ** 2
            times.append(times[-1] + rng.exponential(1.0 / rate))
        self.press = np.array(times)
        self.pkey = rng.integers(0, len(KEYS), len(times))
        self.KS = key_space(G)
        self.fA, self.fB = forest_lines(n=460, seed=8, depth=(9, 60), width=30.0, ground=-1.0)

    def render(self, t):
        p = pose37(t)
        cam = cam_of(p, t, amp=AMP * (0.6 + 0.4 * smooth(t, 143.2, 144.5)))
        ap = 0.01 * (1 - smooth(t, 143.2, 144.2))
        fr = Frame(cam, focus=float(np.linalg.norm(LB - p[0])), aperture=ap)
        rk = 1 - smooth(t, 145.6, 146.8)
        a = smoother(t, 143.2, 144.0)
        lb = bob(LB, t, 1.7)
        q = lb + (KEYS_C + np.array([0, 0.06, 0]) - lb) * a
        if rk > 0:
            room_lit(fr, rk, lights=(LT, q))
            A_, B_ = KEYSQ
            fr.segments(A_, B_, STAR * 0.5, (0.05 + 0.04 * smooth(t, 143.4, 144.2)) * rk, width=1.0)
            hero(fr, bob(LT, t, 0.0), TEAL, 0.5 * rk, 0.5)
            dust(fr, CHAIR + np.array([0, 0.9, -0.2]), (2.0, 1.4, 1.6), t, 300, WARM, 0.05 * rk, seed=34, rise=0.02)
        # the amber light drifts down onto the keys
        hero(fr, q, AMBER, 0.5 * (1 - smooth(t, 144.0, 144.6)), 0.5)
        # keys light by themselves, faster and faster
        kl = np.zeros(len(KEYS))
        for tp, kk in zip(self.press, self.pkey):
            if tp <= t:
                kl[kk] = max(kl[kk], np.exp(-(t - tp) / 0.3))
        kl = kl * (1 - smooth(t, 145.6, 146.4))
        if kl.max() > 0.01:
            fr.points(KEYS + np.array([0, 0.005, 0]), WARM, 1.2 * kl, min_r=1.0)
        # they unfold into the world's lights
        u = np.clip((t - 145.2 - 0.9 * ER[:, 0]) / 1.2, 0, 1)
        u = u * u * (3 - 2 * u)
        P = self.KS + (G - self.KS) * u[:, None]
        P[:, 1] += 0.6 * np.sin(np.pi * u)
        on = smooth(t, 145.1, 145.6)
        fr.points(P, CITY_COL, GI * mix(0.3, 1.6, u) * on * (1 - 0.5 * smooth(t, 148.0, 150.0)))
        # the forest, the lanterns, the footsteps
        fk = smooth(t, 146.6, 148.0)
        if fk > 0:
            self.forest(fr, t, fk)
            st = footsteps(t, 155.0)
            if st:
                S = np.array([(x, -0.995, z) for _, s_t, x, z in st])
                age = np.array([t - s_t for _, s_t, _, _ in st])
                lift = smoother(t, 155.0, 157.6)
                kidx = np.array([k for k, _, _, _ in st])
                Sy = S.copy()
                Sy[:, 1] = S[:, 1] + lift * (6.5 + 0.6 * kidx + 0.25 * np.sin(S[:, 2] * 1.3))
                fr.points(Sy, WARM, (1.4 * np.exp(-age / 6.0) + 0.6) * fk * (1 - 0.3 * lift), min_r=1.2)
                pk = smooth(t, 153.6, 155.0)
                if pk > 0:
                    for k in range(TRAV):
                        idx = np.nonzero(kidx == k)[0][::2]
                        if len(idx) > 1:
                            n = max(2, int(len(idx) * pk))
                            fr.polyline(Sy[idx[:n]], WARM * 0.8, 0.5 * pk, width=1.3)
        draw_stars(fr, t, 0.55 * smooth(t, 145.5, 147.0), hold=0.5)
        sk = smooth(t, 145.4, 147.0)
        return compose2(fr, t, bg=sky(cam, haze=0.8, glow=0.7, warm=0.6) * sk + gradient_bg((0.015, 0.012, 0.03), (0.025, 0.016, 0.026)) * (1 - sk), exposure=1.05)

    def forest(self, fr, t, fk):
        dz = np.clip((self.fA[:, 2] - 9) / 50, 0, 1)
        fr.segments(self.fA, self.fB, STAR * 0.5, 0.10 * (1 - 0.6 * dz) * fk, width=1.0)
        L, _ = travellers(t)
        for k in range(TRAV):
            hero(fr, L[k], np.array([1.0, 0.7, 0.35]), 1.0 * fk * (1 + 0.1 * np.sin(t * 9 + k)), 0.8)
            dust(fr, L[k] + np.array([0, 0.1, 0]), (0.8, 0.8, 0.8), t, 40, np.array([1.0, 0.7, 0.35]), 0.15 * fk, seed=70 + k, rise=0.1)



# ---------------------------------------------------------------------------------- C41/C42
ROOM_WIDE = pose(np.array([2.3, 2.1, 0.3]), np.array([0.0, 0.55, 4.0]), 1250)


class C41(Shot):
    """No one at the controls: the paths in the sky come down and settle into the keys; the room,
    seen wide, floats over the world's lights, every key softly lit. Not them, and not I: the
    two lights by the chair dim almost to nothing; near silence."""
    t0, t1 = 158.8, 163.3

    def setup(self):
        self.c37 = C37()
        self.c37.setup()
        st = footsteps(155.0, 155.0)
        self.S = np.array([(x, -0.995, z) for _, _, x, z in st])
        self.k = np.array([k for k, _, _, _ in st])
        self.S[:, 1] += 6.5 + 0.6 * self.k + 0.25 * np.sin(self.S[:, 2] * 1.3)
        self.dst = KEYS[(np.arange(len(self.S)) * 7) % len(KEYS)]

    def render(self, t):
        p = lerp_pose(pose37(t), ROOM_WIDE, smoother(t, 158.8, 160.4))
        cam = cam_of(p, t, amp=AMP * (1 - 0.6 * smooth(t, 160.4, 161.5)))
        fr = Frame(cam)
        fo = 1 - smooth(t, 158.8, 159.8)
        if fo > 0:
            self.c37.forest(fr, t, fo)
        u = smoother(t, 158.9, 160.2)
        Q = self.S + (self.dst - self.S) * (u - 0.15 * np.sin(np.pi * u))
        fr.points(Q, WARM, 1.3 * (1 - smooth(t, 160.0, 160.5)), min_r=1.2)
        for k in range(TRAV):
            idx = np.nonzero(self.k == k)[0][::2]
            fr.polyline(Q[idx], WARM * 0.8, 0.5 * (1 - smooth(t, 159.2, 159.9)), width=1.3)
        quiet = smooth(t, 160.4, 162.6)
        room_lit(fr, smooth(t, 159.2, 160.2) * (1 - 0.6 * quiet), floor=0.12)
        A_, B_ = KEYSQ
        fr.segments(A_, B_, STAR * 0.5, 0.1 * smooth(t, 159.5, 160.3), width=1.0)
        fr.points(KEYS + np.array([0, 0.005, 0]), WARM, (0.35 * smooth(t, 159.8, 160.4)) * (1 - 0.75 * quiet), min_r=0.9)
        fr.points(G, CITY_COL, GI * 0.8 * (1 - 0.6 * quiet))
        li = smooth(t, 159.4, 160.2) * (1 - 0.85 * quiet)
        hero(fr, bob(LT, t, 0.0), TEAL, 0.5 * li, 0.5)
        hero(fr, bob(LB, t, 1.7), AMBER, 0.5 * li * (1 - 0.3 * smooth(t, 161.3, 161.8)), 0.5)
        draw_stars(fr, t, 0.55 - 0.35 * smooth(t, 159.0, 162.0), hold=0.5 + 0.5 * smooth(t, 158.8, 160.0))
        bg = sky(cam, haze=0.8, glow=0.7, warm=0.6) * (1 - 0.6 * quiet)
        return compose2(fr, t, bg=bg, exposure=1.05)


# ==================================================================================== FINAL CHORUS
FIG_Z = 3.0
POS_A = np.array([-0.5, -1.0, FIG_Z])
POS_B = np.array([0.5, -1.0, FIG_Z])
LOWP = pose(np.array([0.0, -0.62, 0.15]), np.array([0.0, 0.05, FIG_Z]), 1300)


def murmur(t, base=None):
    """Every light rises: a murmuration (positions of the world's lights in the updraft)."""
    P = G if base is None else base
    r = smoother(t, 163.3, 166.5) - smoother(t, 181.5, 184.5)
    if r <= 0:
        return P.copy(), 0.0
    h = r * (1.0 + 7.0 * ER[:, 0] ** 1.5)
    c = np.array([0.0, -1.0, FIG_Z])
    rel = P - c
    ang = r * (0.6 + 0.8 * ER[:, 1]) * (1.0 / (1.0 + 0.15 * np.hypot(rel[:, 0], rel[:, 2])))
    ca, sa = np.cos(ang), np.sin(ang)
    x = rel[:, 0] * ca - rel[:, 2] * sa
    z = rel[:, 0] * sa + rel[:, 2] * ca
    shrink = 1 - 0.55 * r * ER[:, 2]
    Q = c + np.stack([x * shrink, h, z * shrink], 1)
    Q = Q + curl_offset(Q, t * 0.6, 1.2, 0.25) * r
    return Q, r


class C43(Shot):
    """The held "I...": every light in the world rises at once, a murmuration, and A and B stand
    full-figure inside it, hair lifted by the updraft (full figures, their only appearance).
    And one day we'll be paper: they come apart and re-form as their turnaround drawings and
    turn - front, three-quarter, side - and then edge-on: two lines of light, paper-thin."""
    t0, t1 = 163.3, 175.0

    def setup(self):
        self.full = {'A': char('A_full'), 'B': char('B_full')}
        self.hf = {'A': 1.75, 'B': 1.62}
        self.MF = {k: Materialize(v, 9000, 160 + i, sweep='up') for i, (k, v) in enumerate(self.full.items())}
        self.turn = {'A': Morph(['A_turn0', 'A_turn1', 'A_turn2'], key='Aturn'), 'B': Morph(['B_turn0', 'B_turn1', 'B_turn2'], key='Bturn')}
        self.MT = {k: Materialize(v.frames[0], 9000, 170 + i, sweep='down') for i, (k, v) in enumerate(self.turn.items())}
        self.word = Words('paper', n=1800, italic=True)
        self.src = {k: G[np.argsort(np.abs(G[:, 0] - pos[0]) + np.abs(G[:, 2] - FIG_Z))[:3000]] for k, pos in (('A', POS_A), ('B', POS_B))}

    def pose(self, t):
        p = lerp_pose(pose(ROOM_WIDE[0], ROOM_WIDE[1], 1250), LOWP, smoother(t, 163.3, 165.2))
        ang = np.deg2rad(32 * smoother(t, 168.2, 172.6))
        c = np.array([0.0, 0.0, FIG_Z])
        orb = pose(c + np.array([-2.85 * np.sin(ang), -0.62, -2.85 * np.cos(ang)]), c + np.array([0, 0.05, 0]), 1300)
        p = lerp_pose(p, orb, smooth(t, 167.8, 168.6))
        return p

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=AMP * (0.4 + 0.6 * smooth(t, 163.3, 164.5)))
        fr = Frame(cam, split=float(np.linalg.norm(np.array([0, 0, FIG_Z]) - cam.pos)) - 0.3)
        P, r = murmur(t)
        roomk = 1 - smooth(t, 163.3, 164.2)
        if roomk > 0:
            room_lit(fr, 0.4 * roomk, floor=0.12)
            A_, B_ = KEYSQ
            fr.segments(A_, B_, STAR * 0.5, 0.1 * roomk, width=1.0)
            fr.points(KEYS + np.array([0, 0.005, 0]), WARM, 0.0875 * roomk, min_r=0.9)
            hero(fr, bob(LT, t, 0.0), TEAL, 0.075 * roomk, 0.5)
            hero(fr, bob(LB, t, 1.7), AMBER, 0.0525 * roomk, 0.5)
        fr.points(P, CITY_COL, GI * (0.32 + 1.6 * smooth(t, 163.3, 164.2)) * (1 + 1.6 * r), min_r=0.6 * r)
        draw_stars(fr, t, 0.2 + 0.3 * smooth(t, 163.3, 164.5), hold=1 - smooth(t, 163.3, 164.5))
        cards = []
        out_f = smooth(t, 167.9, 168.6)
        in_t = smooth(t, 168.3, 169.0)
        s = smoother(t, 169.0, 171.4) * 2.0
        edge = smoother(t, 171.6, 172.8)
        for who, pos, cl in (('A', POS_A, TEAL), ('B', POS_B, AMBER)):
            h = self.hf[who]
            yaw0, _ = yp_toward(cam.pos, pos + np.array([0, h / 2, 0]))
            kin = smooth(t, 163.6, 165.0)
            M = self.MF[who]
            if t < 168.7:
                k = min(kin, 1 - out_f)
                if kin < 0.999:
                    M.draw(fr, pos, h, kin, t, source=self.src[who], inten=1.0, yaw=yaw0, size=0.002)
                if out_f > 0:
                    M.draw(fr, pos, h, 1 - out_f, t, out_dir=(0, 0.8, 0), inten=0.9, yaw=yaw0, size=0.002)
                if k > 0:
                    im = secondary(self.full[who], t, sway=5.0, wind=3.0 * r, hair_from=0.08, seed=ord(who), breathe=0.006)
                    rr = M.render(fr, im, pos, h, k, yaw=yaw0, ambient=0.7, lights=[(tuple(pos + np.array([0, -0.2, -0.4])), AMBER, 0.6, 1.2)],
                                  rim=(cl * 0.5 + WARM * 0.5, 0.7, (0, 1)), fade=(0, 0, 0, 0.08))
                    if rr is not None:
                        cards.append(rr[:2])
            if t > 168.2:
                MT = self.MT[who]
                yaw = yaw0 + (np.pi / 2 - 0.04) * edge
                k2 = in_t
                if k2 < 0.999:
                    MT.draw(fr, pos, h, k2, t, inten=1.0, yaw=yaw, size=0.002)
                im = secondary(self.turn[who].at(s), t, sway=4.0, wind=2.0, hair_from=0.08, seed=ord(who) + 3, breathe=0.006)
                rr = MT.render(fr, im, pos, h, k2, yaw=yaw, ambient=0.7, lights=[(tuple(pos + np.array([0, -0.2, -0.4])), AMBER, 0.6, 1.2)],
                               rim=(cl * 0.5 + WARM * 0.5, 0.7, (0, 1)), fade=(0, 0, 0, 0.08), opacity=1 - smooth(t, 172.4, 172.9))
                if rr is not None:
                    cards.append(rr[:2])
                if edge > 0.5:
                    top = pos + np.array([0, h, 0])
                    fr.segments([pos + np.array([0, 0.02, 0])], [top], WHITE * 0.5 + cl * 0.5, 1.2 * smooth(t, 172.2, 172.9), width=2.0)
        aw = self.word.typed(t, 169.2, 171.2)
        if aw.max() > 0:
            W = self.word.place(np.array([0.0, 1.25, FIG_Z + 0.4]), 0.45, right=np.array([np.cos(np.deg2rad(32 * smoother(t, 168.2, 172.6))), 0, np.sin(np.deg2rad(32 * smoother(t, 168.2, 172.6)))]))
            src = W + np.array([0, -1.0, 0]) + (self.word.rnd[:, :3] - 0.5) * 0.5
            ae = aw * aw * (3 - 2 * aw)
            go = smooth(t, 173.6, 174.9)
            Q = src + (W - src) * ae[:, None]
            Q = Q + np.array([0, 1.2, 0]) * go * (0.5 + self.word.rnd[:, :1]) + curl_offset(Q, t, 0.5, 0.15) * go
            fr.points(Q, WARM, 0.9 * (aw > 0) * (1 - go), min_r=0.6)
        sk = smooth(t, 163.3, 164.5)
        bg = sky(cam, haze=0.8 + 0.2 * sk, glow=0.7 + 0.3 * sk, warm=0.6 + 0.1 * sk) * (0.4 + 0.6 * sk)
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05 + 0.15 * smooth(t, 163.3, 164.0), rays=((0.0, 3.5, FIG_Z + 2.0), 0.35 * r, 0.4),
                        flare_k=0.25 * np.exp(-((t - 163.4) / 0.25) ** 2))


# ---------------------------------------------------------------------------------- C45/C46
E3 = np.array([0.0, 0.5, 4.1])
R3 = 1.2
HA = np.array([-0.42, 0.05, FIG_Z])
HB = np.array([0.42, 0.05, FIG_Z])


def roll_up(t):
    """The plane rolls back into the sphere (the return)."""
    lon, lat = EARTH['lon'], EARTH['lat']
    S = on_sphere(lon, lat, R3, 20 + 2.0 * (t - 184.0), -12, E3)
    lo = ((lon - (20 + 180) + 180) % 360) - 180
    seam = 1 - np.abs(lo) / 180.0
    u = np.clip((t - 184.6 - 1.6 * seam) / 1.4, 0, 1)
    return S, u * u * (3 - 2 * u)


class C45(Shot):
    """And we'll still be in the light: the two lines bloom back into faces, close, side by side
    in the rising light; they sing; A's eyes close into a smile, B smiles (their last drawings).
    Maybe death is only a return: they come apart; every particle flies home; the risen lights
    fall back into the plane, and the plane rolls back up into the sphere."""
    t0, t1 = 175.0, 188.0

    def setup(self):
        self.mA = Morph(['A_x0', 'A_x3'], key='A_smile')
        self.baseB = char('B_x3')
        fa = HEADS['A_x0']['face']
        H, Wc = self.mA.frames[0].shape[:2]
        ia = char('A_x0')
        sc = H / ia.shape[0]
        x0 = (Wc - int(ia.shape[1] * sc)) // 2
        self.anA = ((fa[0] * sc + x0) / Wc, fa[1] * sc / H)
        fb = HEADS['B_x3']['face']
        self.anB = (fb[0] / self.baseB.shape[1], fb[1] / self.baseB.shape[0])
        self.MA = Materialize(self.mA.frames[0], 9000, 175, sweep='radial')
        self.MB = Materialize(self.baseB, 9000, 176, sweep='radial')
        self.word = Words('return', n=1800, italic=True)
        self.c43 = C43()

    def pose(self, t):
        p = self.c43.pose(min(t, 175.0))
        close = pose(np.array([0.0, 0.08, FIG_Z - 1.15]), np.array([0.0, 0.08, FIG_Z + 5.0]), 1300)
        p = lerp_pose(p, close, smoother(t, 174.8, 176.0))
        p = lerp_pose(p, pose(np.array([0.0, 0.1, FIG_Z - 1.0]), np.array([0.0, 0.1, FIG_Z + 5.0]), 1300), smooth(t, 176.0, 181.0))
        back = pose(np.array([0.0, 2.2, -3.5]), np.array([0.0, -0.4, 4.5]), 1300)
        p = lerp_pose(p, back, smoother(t, 181.2, 184.0))
        sph = pose(E3 + np.array([0.0, 0.0, -3.6]), E3 + np.array([0.0, 0.0, 10.0]), 1500)
        return lerp_pose(p, sph, smoother(t, 184.0, 187.6))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=AMP * (1 - 0.3 * smooth(t, 184.0, 187.6)))
        fr = Frame(cam, split=float(np.linalg.norm(np.array([0, 0.05, FIG_Z]) - cam.pos)) - 0.15)
        P, r = murmur(t)
        S, u = roll_up(t)
        P = P + (S - P) * u[:, None]
        I = GI * (1.9 * (1 + 0.3 * r)) * (1 + 0.7 * r * (1 - smooth(t, 181.5, 184.0)))
        if t > 184.5:
            I = I * mix(np.ones(EN), np.clip(-(S - E3)[:, 2] / R3 * 2.5 + 0.35, 0.08, 1.0), u)
        fr.points(P, CITY_COL, I)
        draw_stars(fr, t, 0.5)
        # the two lines of light, blooming into faces
        lines = 1 - smooth(t, 175.0, 175.6)
        if lines > 0:
            for pos, cl, hh in ((POS_A, TEAL, 1.75), (POS_B, AMBER, 1.62)):
                fr.segments([pos + np.array([0, 0.02, 0])], [pos + np.array([0, hh, 0])], WHITE * 0.5 + cl * 0.5, 1.2 * lines, width=2.0)
        cards = []
        kin = smooth(t, 175.1, 175.9)
        kout = 1 - smooth(t, 181.0, 182.2)
        k = min(kin, kout)
        hb = 0.78
        for who in ('A', 'B'):
            pos = HA if who == 'A' else HB
            M = self.MA if who == 'A' else self.MB
            an = self.anA if who == 'A' else self.anB
            src = np.array([POS_A if who == 'A' else POS_B]) + np.stack([np.zeros(200), np.linspace(0, 1.7, 200), np.zeros(200)], 1)
            if kin < 0.999:
                M.draw(fr, pos, hb, kin, t, source=src, inten=1.0, anchor=an, size=0.001)
            if kout < 0.999:
                M.draw(fr, pos, hb, kout, t, out_dir=(0, -1.2, 0.8), inten=1.0, anchor=an, size=0.001)
            if k > 0:
                if who == 'A':
                    im = morph_head(self.mA, ['A_x0', 'A_x3'], smoother(t, 178.4, 178.9), t, sing=True, gain=0.95,
                                    yaw=0.4 * np.sin(0.5 * t), pitch=-0.2, roll=1.0 * np.sin(0.4 * t), seed=45)
                else:
                    im = head('B_x3', t, sing=True, gain=0.8, blink_seed=46, yaw=-0.3 * np.sin(0.45 * t + 1), roll=-0.8 * np.sin(0.35 * t), sway=1.6)
                cl = TEAL if who == 'A' else AMBER
                rr = M.render(fr, im, pos, hb, k, anchor=an, fade=(0.12, 0.12, 0.0, 0.3), ambient=0.82,
                              lights=[(tuple(pos + np.array([0, 0.9, -0.4])), WARM, 0.5, 1.0)], rim=(cl * 0.4 + WARM * 0.6, 0.8, (0, -1)))
                if rr is not None:
                    cards.append(rr[:2])
        aw = self.word.typed(t, 182.4, 184.4)
        if aw.max() > 0:
            W = self.word.place(np.array([0.0, 1.8, 6.0]), 0.6)
            go = smooth(t, 186.0, 187.5)
            src = W + np.array([0, -1.5, 0])
            ae = aw * aw * (3 - 2 * aw)
            Q = src + (W - src) * ae[:, None]
            Q = Q + (E3 - Q) * go
            fr.points(Q, WARM, 0.9 * (aw > 0) * (1 - go), min_r=0.6)
        sp = smooth(t, 184.0, 187.0)
        bg = sky(cam, haze=1.0, glow=1.0, warm=0.7) * (1 - sp) + space_bg(0.7) * sp
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05 + 0.15 * (1 - smooth(t, 181.0, 183.0)), rays=((0.0, 3.0, FIG_Z + 1.5), 0.35 * r * (1 - smooth(t, 181.0, 182.5)), 0.4))


# ==================================================================================== OUTRO
CON = np.array([(-1.6, 1.1), (-1.0, 1.45), (-0.45, 1.25), (0.1, 1.6), (0.55, 1.3), (1.05, 1.5), (1.5, 1.1), (0.9, 0.85), (0.2, 0.95)], float)
CON3 = E3 + np.stack([CON[:, 0] * 1.5, (CON[:, 1] - 1.2) * 2.4, np.full(len(CON), 0.8)], 1)
POINT_T = (198.6, 199.3)


class C47(Shot):
    """Death is only a return: the constellation forms again around the world, and through it now
    runs a path - the two lights' journey. Two dimensions: the sphere unrolls into a plane.
    Three: it rolls back. And one: plane, edge-on line, point. The point flares on the hit."""
    t0, t1 = 188.0, 202.7

    def setup(self):
        lon = EARTH['lon']
        self.yaw0 = 20 + 2.0 * (188.0 - 184.0)
        lo = ((lon - (self.yaw0 + 180) + 180) % 360) - 180
        self.seam = 1 - np.abs(lo) / 180.0
        q = np.linspace(0, 1, 120)
        idx = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        self.path = np.concatenate([CON3[i] + (CON3[j] - CON3[i]) * q[:, None] for i, j in zip(idx[:-1], idx[1:])])

    def render(self, t):
        z = -3.6 + 0.3 * smooth(t, 188.0, 196.0) + 0.25 * ease_out(t, 192.5, 193.0, 3) - 0.2 * ease_out(t, 196.5, 197.0, 3)
        cam = cam_at(E3 + np.array([0.0, 0.0, z]), E3 + np.array([0, 0, 10.0]), f=1500, t=t, amp=AMP * 0.7)
        fr = Frame(cam)
        lon, lat = EARTH['lon'], EARTH['lat']
        yaw = self.yaw0 + 2.0 * (t - 188.0)
        S = on_sphere(lon, lat, R3, yaw, -12, E3)
        Pm = on_plane(lon, lat, 0.72, yaw, E3)
        front = np.clip(-(S - E3)[:, 2] / R3 * 2.5 + 0.35, 0.08, 1.0)
        # two: unroll; three: roll back; one: unroll, edge-on, point
        u2 = np.clip((t - 192.55 - 0.45 * (1 - self.seam)) / 0.55, 0, 1)
        u3 = smoother(t, 196.5, 197.1)
        u1 = np.clip((t - 197.3 - 0.3 * (1 - self.seam)) / 0.4, 0, 1)
        u = np.maximum(u2 * (1 - u3), u1)
        u = u * u * (3 - 2 * u)
        P = S + (Pm - S) * u[:, None]
        I = GI * 1.9 * mix(front, np.ones(EN), u)
        e = smoother(t, 197.8, 198.5) * np.pi / 2
        if e > 0:
            P = E3 + (P - E3) @ rot_x(e).T
        c = ease_in(t, POINT_T[0], POINT_T[1], 3)
        P = E3 + (P - E3) * (1 - c)
        I = I * (1 - c) ** 2
        fr.points(P, CITY_COL, I)
        # the constellation and the path of the two lights
        ck = smooth(t, 188.2, 189.4) * (1 - smooth(t, 192.3, 192.8))
        if ck > 0:
            for i, cc in enumerate(CON3):
                hero(fr, cc, WARM, 0.7 * ck * smooth(t, 188.2 + 0.08 * i, 188.6 + 0.08 * i), 0.4)
            n = int(len(self.path) * smoother(t, 189.0, 191.8))
            if n > 1:
                fr.polyline(self.path[:n], WARM * 0.8, 0.6 * ck, width=1.3)
                for off, cl in ((0, AMBER), (8, TEAL)):
                    hero(fr, self.path[max(0, n - 1 - off)], cl, 0.5 * ck, 0.45)
        # the point, and the flare
        if t > POINT_T[1] - 0.1:
            fl = np.exp(-((t - 199.9) / 0.25) ** 2)
            core = 3.0 * (1 + 0.1 * np.sin(t * 9)) + 10.0 * fl
            hero(fr, E3, WARM, core * 0.6, 0.8 + 3.0 * fl)
        if 192.45 < t < 193.3:
            ring = np.exp(-((t - 192.55) / 0.25) ** 2) * 1.1
            C = ring_points(E3, R3 * 1.01, 180, (0, 0, 1))
            fr.polyline(np.vstack([C, C[:1]]), STAR, ring, width=1.2)
        draw_stars(fr, t, 0.5 * (1 - 0.5 * c))
        fl = np.exp(-((t - 199.9) / 0.2) ** 2)
        return compose2(fr, t, bg=space_bg(0.7 * (1 - 0.5 * c)), exposure=1.05, flare_k=0.9 * fl, white=0.35 * fl)


class C49(Shot):
    """Still loading: from the point, the horizon opens again and the world begins to load around
    two small lights - a new light among them - and it never finishes. Fade."""
    t0, t1 = 202.7, 213.4

    def setup(self):
        self.Gh = G + E3
        self.order = np.random.default_rng(49).random(EN)
        self.word = Words('still loading', n=2600, italic=True)

    def render(self, t):
        a = pose(E3 + np.array([0.0, 0.0, -3.6 + 0.3 + 0.25 - 0.2]), E3 + np.array([0, 0, 10.0]), 1500)
        b = pose(E3 + np.array([0.0, 0.05, -4.6]), E3 + np.array([0.0, 0.0, 10.0]), 1300)
        p = lerp_pose(a, b, smoother(t, 202.7, 206.0))
        p = lerp_pose(p, pose(E3 + np.array([0.0, 0.25, -5.4]), E3 + np.array([0.0, -0.1, 10.0]), 1300), smooth(t, 206.0, 213.4))
        cam = cam_of(p, t, amp=AMP * 0.7)
        fr = Frame(cam)
        hero(fr, E3, WARM, 1.8 * (1 - smooth(t, 202.8, 204.0)) + 0.0, 0.8)
        line = ease_out(t, 202.9, 204.2, 3)
        ledge_line(fr, y=E3[1], z=E3[2], inten=0.4 * smooth(t, 202.8, 203.3), x=0.2 + 60 * line)
        # the world loads, slowly, and never completes
        loaded = 0.55 * smooth(t, 203.5, 211.0)
        arr = np.clip((loaded - self.order * 0.9) / 0.05, 0, 1)
        start = E3 + (self.Gh - E3) * 0.0
        k = np.clip(arr, 0, 1)
        Q = E3 + (self.Gh - E3) * (0.2 + 0.8 * k[:, None])
        fr.points(Q, CITY_COL, GI * 1.6 * k)
        lt = smooth(t, 203.6, 204.6)
        for dx, cl in ((-0.35, TEAL), (0.35, AMBER)):
            hero(fr, E3 + np.array([dx, 0.02, 0.0]), cl, 0.5 * lt, 0.45)
        new = smooth(t, 207.6, 208.6)
        if new > 0:
            hero(fr, E3 + np.array([0.0, 0.02, 0.0]), WHITE * 0.6 + WARM * 0.4, 0.35 * new * (1 + 0.2 * np.sin(t * 3)), 0.35)
        aw = self.word.typed(t, 202.75, 205.0)
        last = self.word.order >= self.word.nvis - 3
        aw = np.where(last, np.minimum(aw, 0.5 + 0.12 * np.sin(t * 2.5 + self.word.rnd[:, 0] * 6)), aw)
        if aw.max() > 0:
            W = self.word.place(E3 + np.array([0.0, 0.75, 3.0]), 0.5)
            src = E3 + (self.word.rnd[:, :3] - 0.5) * 0.2
            ae = aw * aw * (3 - 2 * aw)
            fr.points(src + (W - src) * ae[:, None], WARM, 0.9 * (aw > 0) * (0.4 + 0.6 * aw), min_r=0.6)
        draw_stars(fr, t, 0.25 + 0.3 * smooth(t, 203.0, 206.0))
        sk = smooth(t, 202.8, 204.5)
        bg = space_bg(0.35) * (1 - sk) + sky(cam, haze=sk, glow=sk, horizon=0.0) * sk
        return compose2(fr, t, bg=bg, exposure=1.05, fade=1 - smooth(t, 211.6, 213.35))


SHOTS = {k: v for k, v in globals().items() if k[:1] == 'C' and k[1:].isdigit() and isinstance(v, type) and issubclass(v, Shot)}
