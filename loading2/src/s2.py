"""VERSE 2 and CHORUS 2 (1:13-2:10): one continuous camera, continued from s1.C18 (whose last
frame is the 'home' world - the plane, the line, the two lights - seen from HOME_POSE)."""
import sys
sys.path.insert(0, '/home/user/OC/loading/src')
from world import *
from lfx import *
from face import head, HEADS, morph_head
import voice


class Shot:
    t0 = t1 = 0.0

    def setup(self):
        pass


G = ground_points()
GI = EARTH['I']
EN = len(GI)
ER = np.random.default_rng(12).random((EN, 4)).astype(np.float32)
FIRE = np.array([1.0, 0.55, 0.22], np.float32)
HOME_POSE = pose((0.0, 0.45, -5.6), (0.0, 0.0, 8.0), 1300)
AMP = 0.6


def yp_toward(src, dst):
    d = np.asarray(dst, float) - np.asarray(src, float)
    return float(np.arctan2(d[0], d[2])), float(-np.arctan2(d[1], np.hypot(d[0], d[2])))


def home_lattice():
    xs = np.arange(-60, 61, 3.0)
    zs = np.arange(-10, 120, 3.0)
    A_, B_, T_ = [], [], []
    for x in xs:
        A_.append((x, -2.2, -10)); B_.append((x, -2.2, 120)); T_.append(abs(x) / 60)
    for z in zs:
        A_.append((-60, -2.2, z)); B_.append((60, -2.2, z)); T_.append(z / 120)
    return np.array(A_), np.array(B_), np.array(T_)


# ==================================================================================== VERSE 2
BC0 = np.array([0.0, 2.6, 9.0])
R20 = np.array([1.5, 2.1, 48.0])


def bitmap_center(t):
    return BC0 + np.array([0, 0, 31.0]) * smoother(t, 76.9, 80.2)


class C19(Shot):
    """You sent out your signals into the night: one city flashes, and the Arecibo message -
    1,679 bits - rises out of it and assembles in the sky, row by row on the beat. You asked
    the dark forest for one answering light: the message flies on into a forest of thin lines;
    the stars hold still; nothing answers. Far off, one point blinks red - and we go into it."""
    t0, t1 = 73.0, 80.5

    def setup(self):
        self.LA, self.LB, self.LT = home_lattice()
        self.word = Words('unfinished', n=2400, italic=True)
        cand = np.nonzero((np.abs(G[:, 0]) < 2.5) & (G[:, 2] > 2) & (G[:, 2] < 5))[0]
        self.city = int(cand[np.argmax(GI[cand])])
        P, ys, xs = arecibo_points((0, 0, 0), cell=0.085)
        self.bits, self.rows = P, ys
        bt = beats(73.7, 76.9)
        self.bt = bt if bt else [74.0, 75.0, 76.0]
        g = np.minimum((ys * len(self.bt)) // 73, len(self.bt) - 1)
        self.arrive = np.array([self.bt[i] for i in g]) + 0.02 * (xs % 3)
        self.rnd = np.random.default_rng(19).random((len(P), 3))
        self.fA, self.fB = forest_lines(n=520, seed=5, depth=(12, 80), width=40.0, ground=-1.0)

    def pose(self, t):
        p = HOME_POSE
        p = lerp_pose(p, pose((0.0, 0.6, -5.0), (0.0, 2.2, 9.0), 1300), smoother(t, 73.3, 75.6))
        bc = bitmap_center(t)
        follow = pose(bc + np.array([0.3, -0.4, -6.5]), bc + np.array([0.1, -0.1, 10.0]), 1300)
        p = lerp_pose(p, follow, smoother(t, 76.4, 77.6))
        gate = pose(R20 - np.array([0, 0, 0.25]), R20 + np.array([0, 0, 5.0]), 1300)
        return lerp_pose(p, gate, ease_in(t, 79.9, 80.5, 2.2))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=AMP)
        fr = Frame(cam)
        gate = ease_in(t, 79.9, 80.5, 2.2)
        dim = 1 - 0.8 * gate
        home = 1 - 0.7 * smooth(t, 77.0, 79.0)
        fr.points(G, CITY_COL, GI * 1.5 * home * dim)
        ledge_line(fr, inten=0.35 * home * dim)
        for x, c in ((-0.35, TEAL), (0.35, AMBER)):
            hero(fr, np.array([x, 0.02, 0.0]), c, 0.5 * home * dim, 0.45)
        Il = 0.035 * np.clip((1.3 - self.LT) / 0.2, 0, 1) * (1 - smooth(t, 73.5, 76.0))
        fr.segments(self.LA, self.LB, STAR * 0.5 + WARM * 0.2, Il, width=1.0)
        hold = smooth(t, 77.0, 78.0)
        draw_stars(fr, t, 0.6 * dim, hold=hold)
        # the word from the last line dissolves upward into the sky
        aw = self.word.typed(t, 70.7, 72.6)
        last = self.word.order >= self.word.nvis - 3
        aw = np.where(last, np.minimum(aw, 0.55 + 0.1 * np.sin(t * 3 + self.word.rnd[:, 0] * 6)), aw)
        go = smooth(t, 73.0, 74.2)
        if go < 1:
            W = self.word.place(np.array([0.0, 0.85, 4.0]), 0.75)
            src = W + np.array([0, -1.2, 0]) + (self.word.rnd[:, :3] - 0.5) * 0.6
            ae = aw * aw * (3 - 2 * aw)
            Q = src + (W - src) * ae[:, None]
            Q = Q + np.array([0, 1.5, 0]) * go * (0.5 + self.word.rnd[:, :1]) + curl_offset(Q, t, 0.5, 0.15) * go
            fr.points(Q, WARM, 0.9 * (aw > 0) * (0.4 + 0.6 * aw) * (1 - go), min_r=0.5)
        # the signal
        cs = G[self.city]
        fl = np.exp(-((t - 73.35) / 0.12) ** 2) + 0.4 * smooth(t, 73.3, 73.5) * (1 - smooth(t, 76.5, 77.5))
        hero(fr, cs, WARM, 1.2 * fl * dim, 0.8)
        bc = bitmap_center(t)
        tgt = self.bits + bc
        dep = self.arrive - 1.0
        u = np.clip((t - dep) / (self.arrive - dep), 0, 1)
        ue = u * u * (3 - 2 * u)
        mid = (cs + tgt) / 2 + np.array([0, 1.0, 0]) + (self.rnd - 0.5) * 0.6
        Q = (1 - ue)[:, None] ** 2 * cs + 2 * ((1 - ue) * ue)[:, None] * mid + ue[:, None] ** 2 * tgt
        flash = np.exp(-np.clip(t - self.arrive, 0, None) / 0.25) * (t >= self.arrive)
        I = (1.1 + 3.0 * flash) * (u > 0) * (0.85 + 0.15 * np.sin(t * 5 + self.rnd[:, 0] * 6)) * dim
        fr.points(Q, WARM * 0.7 + STAR * 0.3, I, min_r=0.8)
        # the dark forest
        fk = smooth(t, 75.8, 77.4)
        if fk > 0:
            dz = np.clip((self.fA[:, 2] - 12) / 70, 0, 1)
            fr.segments(self.fA, self.fB, STAR * 0.5, 0.10 * (1 - 0.6 * dz) * fk * dim, width=1.0)
        blink = np.exp(-((t - 79.55) / 0.12) ** 2) + smooth(t, 79.85, 80.1)
        if blink > 0.01:
            hero(fr, R20, RED, 0.9 * blink + 0.7 * gate, 0.5 + 6.0 * gate)
        bg = sky(cam, haze=1.0 - 0.6 * fk, glow=1.0 - 0.7 * fk, warm=0.5) * (1 - 0.6 * gate)
        return compose2(fr, t, bg=bg, exposure=1.05)


# ---------------------------------------------------------------------------------- C21/C22
Z21 = np.array([0.0, 0.0, 0.0])
A21_IRIS = (617.0, 702.0)


def lattice_nodes(n=9, step=0.6, center=Z21):
    g = (np.arange(n) - (n - 1) / 2) * step
    X, Y, Z = np.meshgrid(g, g, g, indexing='ij')
    return np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1) + center


NODES = lattice_nodes()


def d21(t):
    d = 0.3 * np.exp(np.log(1.0 / 0.3) * ease_out(t, 80.5, 83.8, 2))
    return d * np.exp(np.log(6.0) * smoother(t, 84.1, 87.7))


def pose21(t):
    d = d21(t)
    side = smoother(t, 84.1, 87.7)
    return pose(Z21 + np.array([1.5 * side, 0.8 * side, -d]), Z21 + np.array([0.75 * side, 0.4 * side, 10.0]), 1500)


class C21(Shot):
    """Then a countdown burned red at the back of your eyes: out of the red light, an iris -
    A's eye, extremely close (her focused drawing, its only appearance), a ring of red ticks
    counting down inside it, one dying on each beat. And the laws stayed the same as your
    certainty died: we pull out of the eye; she comes apart into the points of a lattice that
    does not change; the lines that joined them die one by one; the points stay."""
    t0, t1 = 80.5, 87.7

    def setup(self):
        self.base = char('A_x1')
        h, w = self.base.shape[:2]
        self.anchor = (A21_IRIS[0] / w, A21_IRIS[1] / h)
        self.hc = 1.0
        self.M = Materialize(self.base, 9000, 81, sweep='radial')
        self.bt = beats(80.6, 84.1)
        rng = np.random.default_rng(21)
        self.dst = NODES[rng.integers(0, len(NODES), len(self.M.uv))]
        idx = rng.choice(len(NODES), 60, replace=False)
        segs = []
        for i in idx:
            d = np.abs(NODES - NODES[i]).sum(1)
            j = np.nonzero((d > 0.5) & (d < 0.7))[0]
            if len(j):
                segs.append((NODES[i], NODES[rng.choice(j)]))
        self.SA = np.array([s[0] for s in segs])
        self.SB = np.array([s[1] for s in segs])
        self.sdie = 85.0 + np.sort(rng.random(len(segs))) * 2.5

    def render(self, t):
        p = pose21(t)
        cam = cam_of(p, t, amp=0.15 + 0.45 * smooth(t, 83.5, 85.0))
        fr = Frame(cam, split=float(np.linalg.norm(Z21 - cam.pos)) - 0.002)
        gate = 1 - ease_out(t, 80.5, 81.3, 2)
        rr = 0.034
        n = 24
        dead = sum(1 for b in self.bt if t >= b)
        q = np.pi / 2 + 2 * np.pi * np.arange(n) / n - 0.05 * (t - 80.5)
        dirs = np.stack([np.cos(q), np.sin(q), np.zeros(n)], 1)
        alive = np.arange(n) >= dead
        ring = smooth(t, 80.7, 81.2) * (1 - smooth(t, 84.1, 84.7))
        if ring > 0:
            P = Z21 + dirs * rr + np.array([0, 0, -0.004])
            fr.segments(P[alive], P[alive] - dirs[alive] * rr * 0.3, RED, 0.9 * ring, width=2.0)
            for j in np.nonzero(~alive)[0]:
                g = np.exp(-(t - self.bt[j]) / 0.25)
                fr.points(P[j][None], RED, 0.6 * g * ring, min_r=1.5)
        pl = pulse(t, self.bt, 0.2)
        hero(fr, Z21 + np.array([0, 0, -0.003]), RED, 0.9 * gate + (0.15 + 0.35 * pl) * ring, 0.3 + 6.2 * gate)
        out = smooth(t, 84.2, 85.2)
        cards = []
        if out < 1:
            im = head('A_x1', t, sing=True, blink_seed=21, blink_extra=(82.9,), yaw=0.2 * np.sin(0.5 * t), roll=0.5 * np.sin(0.3 * t), sway=1.0)
            r = self.M.render(fr, im, Z21, self.hc, 1 - out, anchor=self.anchor, fade=(0.08, 0.08, 0.0, 0.3), ambient=0.85,
                              lights=[(tuple(Z21 + np.array([0, 0, -0.05])), RED, 0.5 * ring, 0.06)], rim=(TEAL, 0.4, (0, -1)))
            if r is not None:
                cards.append(r[:2])
        if out > 0:
            tgt = self.M.card.uv_to_world(self.M.uv, Z21, self.hc, 0, 0, self.anchor)
            u = np.clip(out * 1.5 - self.M.rnd[:, 0] * 0.5, 0, 1)[:, None]
            Q = tgt + (self.dst - tgt) * (u * u * (3 - 2 * u))
            Q = Q + curl_offset(Q, t, 0.3, 0.03) * np.sin(np.pi * u)
            fr.points(Q, self.M.col * 0.4 + TEAL * 0.6, 0.35 * (1 - u[:, 0] * 0.7) * (u[:, 0] < 1), min_r=0.4)
        lat = smooth(t, 84.4, 85.6)
        if lat > 0:
            fr.points(NODES, STAR * 0.7 + TEAL * 0.3, 1.6 * lat, min_r=1.5)
            alive_s = t < self.sdie
            ls = smooth(t, 84.6, 85.0)
            fr.segments(self.SA[alive_s], self.SB[alive_s], STAR * 0.6 + TEAL * 0.3, 0.3 * ls, width=1.0)
            for a_, b_, td in zip(self.SA, self.SB, self.sdie):
                g = np.exp(-max(0.0, t - td) / 0.2) * (t >= td)
                if g > 0.02:
                    fr.points(((a_ + b_) / 2)[None], WARM, 0.8 * g, min_r=1.0)
        draw_stars(fr, t, 0.55 * smooth(t, 83.5, 86.0), hold=1.0)
        bg = space_bg(0.5 * smooth(t, 84.0, 86.0)) + gradient_bg((0.02, 0.006, 0.01), (0.008, 0.004, 0.012)) * gate
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05)


# ---------------------------------------------------------------------------------- C23/C24/C25
K23 = np.array([8.0, 9.0, 40.0])        # where the card comes out of its sleeve
E2 = np.array([8.0, -6.0, 40.0])        # the Earth
R2 = 2.0
YF = E2[1] + R2                          # the plane the world falls into
T_HIT1, T_HIT2 = 95.42, 96.32


def foil_state(t):
    """The card: centre, yaw (turning), tilt (0 = facing us, pi/2 = lying flat, edge-on to a level eye)."""
    slide = smoother(t, 87.9, 90.4)
    c = K23 + np.array([-3.5 * (1 - slide), 0, 0])
    yaw = 0.6 * (t - 88.0)
    tilt = np.pi / 2 * smoother(t, 90.8, 92.2)
    yaw = yaw * (1 - smoother(t, 90.8, 92.2))
    drop = smoother(t, 91.8, T_HIT1)
    c = c + np.array([0, (YF - K23[1]) * drop, 0])
    return c, yaw, tilt


def pose23(t):
    a = pose21(87.7)
    b = pose(np.array([4.0, 2.0, 18.0]), K23, 1300)
    p = lerp_pose(a, b, smoother(t, 87.7, 90.6))
    c, _, _ = foil_state(t)
    follow = pose(np.array([6.0, c[1] - 0.5, 24.0]), c, 1300)
    p = lerp_pose(p, follow, smoother(t, 91.0, 92.4))
    over = pose(E2 + np.array([-2.0, 9.0, -14.0]), np.array([E2[0], YF, E2[2]]), 1200)
    return lerp_pose(p, over, smoother(t, 94.6, 97.6))


class C23(Shot):
    """And something above you drew a card from its sleeve: along the stars, a thin plane of light
    slides out from behind an edge in the dark, turning. A sheet thinner than any mind could
    believe: it turns edge-on - a hairline - and descends to the world. It touched the edge of
    everything and everything fell flat: on the hit the Earth collapses into the plane from the
    contact point and spreads out as it flattens, preserved in every light; a second wave on
    the second hit."""
    t0, t1 = 87.7, 98.5

    def setup(self):
        gx, gy = np.meshgrid(np.linspace(-1, 1, 26), np.linspace(-1, 1, 36))
        self.fp = np.stack([gx.ravel() * 2.5, gy.ravel() * 3.6], 1)

    def render(self, t):
        p = pose23(t)
        cam = cam_of(p, t, amp=AMP)
        fr = Frame(cam)
        # what remains of the lattice behind us
        lat = 1 - smooth(t, 87.7, 90.0)
        if lat > 0:
            fr.points(NODES, STAR * 0.7 + TEAL * 0.3, 1.2 * lat, min_r=0.8)
        # stars, with a dark sleeve the card comes out of
        S = STARS['P']
        b = twinkle(STARS, t, 1.0) * 0.6
        d = S / np.linalg.norm(S, axis=1, keepdims=True)
        k = (K23 - p[0]) / np.linalg.norm(K23 - p[0])
        sleeve = (np.abs(d @ np.array([1, 0, 0]) - k[0]) < 0.05) & (np.abs(d @ np.array([0, 1, 0]) - k[1]) < 0.08)
        b = b * np.where(sleeve, 0.0, 1.0)
        fr.points(S, STARS['col'], b * 0.9)
        # the card
        c, yaw, tilt = foil_state(t)
        R = rot_y(yaw) @ rot_x(tilt)
        Pf = c + np.stack([self.fp[:, 0], self.fp[:, 1], np.zeros(len(self.fp))], 1) @ R.T
        vis = smooth(t, 87.9, 88.6) * (1 - smooth(t, T_HIT1, T_HIT1 + 0.3))
        fr.points(Pf, STAR * 0.6 + WARM * 0.4, 0.16 * vis)
        corners = np.array([(-2.5, -3.6, 0), (2.5, -3.6, 0), (2.5, 3.6, 0), (-2.5, 3.6, 0), (-2.5, -3.6, 0)]) @ R.T + c
        fr.polyline(corners, STAR * 0.7 + WARM * 0.3, 0.5 * vis, width=1.2)
        # the world
        S2 = on_sphere(EARTH['lon'], EARTH['lat'], R2, 30 + 3.0 * t, -15, E2)
        top = np.array([E2[0], YF, E2[2]])
        dist = np.linalg.norm(S2 - top, axis=1) / (2 * R2)
        tf = T_HIT1 + 0.8 * dist
        f = np.clip((t - tf) / 0.25, 0, 1)
        f = f * f * (3 - 2 * f)
        rel = S2 - top
        rad = np.hypot(rel[:, 0], rel[:, 2])
        dirr = np.stack([rel[:, 0], np.zeros(EN), rel[:, 2]], 1) / np.maximum(rad, 1e-6)[:, None]
        arc = dist * 2 * R2 * np.pi / 2
        spread = 1 + 1.4 * smooth(t, T_HIT1, T_HIT1 + 1.5) + 1.6 * smoother(t, T_HIT2, T_HIT2 + 2.0)
        flat = top + dirr * (arc * spread)[:, None]
        P = S2 + (flat - S2) * f[:, None]
        front = np.clip(-(S2 - E2) @ ((p[0] - E2) / np.linalg.norm(p[0] - E2)) * -1 * 1.2 + 0.4, 0.15, 1.0)
        I = GI * 4.0 * mix(front, np.ones(EN), f) * (1 + 3.0 * np.exp(-((t - tf) / 0.12) ** 2)) * smooth(t, 89.0, 91.0)
        fr.points(P, CITY_COL, I)
        h1 = np.exp(-((t - T_HIT1) / 0.12) ** 2) + 0.6 * np.exp(-((t - T_HIT2) / 0.12) ** 2)
        if h1 > 0.01:
            hero(fr, top, WHITE, 1.2 * h1, 1.4)
        bg = space_bg(0.6) * (1 + 0.5 * smooth(t, T_HIT1, T_HIT1 + 2))
        return compose2(fr, t, bg=bg, exposure=1.05, flare_k=0.6 * h1)


def flat_world(t, spread_t=None):
    """Positions of the flattened world (after the collapse)."""
    S2 = on_sphere(EARTH['lon'], EARTH['lat'], R2, 30 + 3.0 * min(t, 98.5), -15, E2)
    top = np.array([E2[0], YF, E2[2]])
    rel = S2 - top
    dist = np.linalg.norm(rel, axis=1) / (2 * R2)
    rad = np.hypot(rel[:, 0], rel[:, 2])
    dirr = np.stack([rel[:, 0], np.zeros(EN), rel[:, 2]], 1) / np.maximum(rad, 1e-6)[:, None]
    arc = dist * 2 * R2 * np.pi / 2
    spread = 1 + 1.4 + 1.6 * smoother(min(t, 98.32), T_HIT2, T_HIT2 + 2.0)
    return top + dirr * (arc * spread)[:, None]


# ---------------------------------------------------------------------------------- C26/C27/C28
TOP = np.array([E2[0], YF, E2[2]])
B26 = TOP + np.array([0.0, 1.6, -1.0])
LOW = pose(TOP + np.array([0.0, 0.35, -4.6]), B26 + np.array([0, 0.1, 0]), 1450)


def page_R(t):
    """The flat world rises like a page: tilt from lying flat to standing (facing us), then turn
    edge-on about the vertical."""
    a = np.pi / 2 * (smoother(t, 102.6, 105.0) - smoother(t, 105.6, 106.8))
    return rot_x(-a)


def page_center(t):
    return TOP + np.array([0, 3.0, -2.0]) * smoother(t, 102.6, 105.0)


class C26(Shot):
    """Three dimensions into two, and still I looked at that: the flattened world's light rises as
    glow and B's face assembles above it, lit from below (her surprised drawing, its only
    appearance), singing. And the dark came closer and the flat came near: she comes apart into
    the flat light; the flat world stands up like a page and comes toward us while the dark
    closes in. We followed it upward to the edge of the sphere: the page turns edge-on - a line -
    and two lights, teal and amber, leave it and rise; we rise with them."""
    t0, t1 = 98.5, 108.4

    def setup(self):
        self.base = char('B_x5')
        h, w = self.base.shape[:2]
        fc = HEADS['B_x5']['face']
        self.anchor = (fc[0] / w, fc[1] / h)
        self.hb = 2.3
        self.M = Materialize(self.base, 9000, 98, sweep='up')
        self.flat = flat_world(98.5)
        self.src = self.flat[np.argsort(np.linalg.norm(self.flat - TOP, axis=1))[:4000]]

    def pose(self, t):
        p = pose23(t)
        p = lerp_pose(p, LOW, smoother(t, 98.5, 99.8))
        pc = page_center(t)
        back = pose(pc + np.array([0.0, 2.0, -42.0]), pc, 1300)
        p = lerp_pose(p, back, smoother(t, 102.2, 104.0))
        near = pose(pc + np.array([0.0, 0.5, -14.0]), pc, 1300)
        p = lerp_pose(p, near, smoother(t, 104.0, 105.6))
        level = pose(pc + np.array([0.0, 0.0, -12.0]), pc + np.array([0, 0, 10.0]), 1300)
        p = lerp_pose(p, level, smoother(t, 105.5, 106.6))
        lights_c = TOP + np.array([0, 3.0, -2.0]) + np.array([0, 1.0, 0]) * 9.0 * ease_in(t, 106.6, 108.4, 1.6)
        up = pose(lights_c + np.array([0.0, -2.2, -4.5]), lights_c + np.array([0, 1.5, 0]), 1300)
        return lerp_pose(p, up, smoother(t, 106.4, 108.4))

    def render(self, t):
        p = self.pose(t)
        cam = cam_of(p, t, amp=AMP)
        fr = Frame(cam, split=float(np.linalg.norm(B26 - cam.pos)) - 0.3)
        R = page_R(t)
        rel = self.flat - TOP
        P = page_center(t) + rel @ R.T
        dark = smooth(t, 102.4, 105.5)
        fr.points(P, CITY_COL, GI * 3.0 * (1 - 0.5 * smooth(t, 106.6, 108.0)))
        draw_stars(fr, t, 0.6 * (1 - 0.7 * dark), hold=1.0)
        cards = []
        kin = smooth(t, 98.6, 99.6)
        kout = 1 - smooth(t, 102.1, 102.9)
        k = min(kin, kout)
        yaw, pitch = yp_toward(cam.pos, B26)
        if kin < 0.999:
            self.M.draw(fr, B26, self.hb, kin, t, source=self.src, inten=1.1, yaw=yaw, pitch=pitch, anchor=self.anchor, size=0.002)
        if kout < 0.999:
            self.M.draw(fr, B26, self.hb, kout, t, out_dir=(0, -1.5, 0.3), inten=1.0, yaw=yaw, pitch=pitch, anchor=self.anchor, size=0.002)
        if k > 0:
            im = head('B_x5', t, sing=True, gain=0.9, blink_seed=26, yaw=0.3 * np.sin(0.6 * t), pitch=0.3, roll=0.8 * np.sin(0.4 * t + 1), sway=1.6)
            lights = [(tuple(TOP + np.array([0, 0.3, -0.6])), AMBER, 0.9, 1.4), (tuple(B26 + np.array([0, 1.5, -1.0])), STAR, 0.15, 2.0)]
            r = self.M.render(fr, im, B26, self.hb, k, anchor=self.anchor, yaw=yaw, pitch=pitch, fade=(0.1, 0.1, 0.0, 0.32),
                              ambient=0.62, lights=lights, rim=(WARM, 0.6, (0, 1)))
            if r is not None:
                cards.append(r[:2])
        # two lights leave the edge-on page and rise
        lk = smooth(t, 105.9, 106.6)
        if lk > 0:
            base = TOP + np.array([0, 3.0, -2.0])
            rise = 9.0 * ease_in(t, 106.6, 108.4, 1.6)
            for dx, c in ((-0.35, TEAL), (0.35, AMBER)):
                q = base + np.array([dx, rise + 0.1 * np.sin(t * 2 + dx * 9), 0])
                hero(fr, q, c, 0.6 * lk, 0.5)
        bg = space_bg(0.5) * (1 - 0.6 * dark)
        return compose2(fr, t, bg=bg, cards=cards, exposure=1.05, vignette=0.3 + 0.35 * dark * (1 - smooth(t, 106.0, 108.0)))


# ==================================================================================== CHORUS 2
LIGHTS0 = TOP + np.array([0, 3.0, -2.0])


def lights_pos(t):
    rise = 9.0 * ease_in(t, 106.6, 108.4, 1.6)
    if t > 108.4:
        rise = 9.0 + 4.0 * (t - 108.4) + 0.9 * (t - 108.4) ** 2
    return LIGHTS0 + np.array([0, rise, 0])


WALL_Y = LIGHTS0[1] + 9.0 + 4.0 * 7.0 + 0.9 * 49.0     # reached at 115.4


class C29(Shot):
    """So if we live in a simulated universe, we flew out past the stars to find who wrote the
    verse: the climb - through layer after layer of the lattice, the flat world falling away
    below, the stars streaming past - up to the wall of light, and through it in a flash."""
    t0, t1 = 108.4, 115.7

    def setup(self):
        rng = np.random.default_rng(29)
        self.layers = []
        g = np.arange(-24, 24.01, 1.2)
        X, Z = np.meshgrid(g, g)
        self.grid = np.stack([X.ravel(), Z.ravel()], 1)
        self.ys = LIGHTS0[1] + 9.0 + np.array([6, 14, 24, 36, 50, 66])
        self.dome = sphere_pts(9000, 1.0, 7)
        self.dome = self.dome[self.dome[:, 1] < -0.2]
        self.flat = flat_world(98.5)

    def render(self, t):
        lc = lights_pos(t)
        up = pose(lc + np.array([0.0, -2.2, -4.5]), lc + np.array([0, 1.5, 0]), 1300)
        p = lerp_pose(up, pose(lc + np.array([0.0, -3.0, -0.6]), lc + np.array([0, 10.0, 0.4]), 1200), smoother(t, 109.0, 111.0))
        cam = cam_of(p, t, amp=AMP)
        fr = Frame(cam)
        R = page_R(t)
        P = page_center(t) + (self.flat - TOP) @ R.T
        fr.points(P, CITY_COL, GI * 1.1 * (1 - smooth(t, 108.4, 111.0)))
        for dx, c in ((-0.35, TEAL), (0.35, AMBER)):
            hero(fr, lc + np.array([dx, 0.1 * np.sin(t * 2 + dx * 9), 0]), c, 0.6, 0.5)
        # lattice layers, each flashing as the lights pass through it
        for y in self.ys:
            Q = np.stack([self.grid[:, 0] + lc[0], np.full(len(self.grid), y), self.grid[:, 1] + lc[2]], 1)
            pas = np.exp(-((lc[1] - y) / 1.5) ** 2)
            near = np.exp(-np.clip(y - lc[1], 0, None) / 25.0)
            fr.points(Q, STAR * 0.6 + TEAL * 0.25, (0.5 + 2.0 * pas) * near, min_r=1.0)
            gl = np.arange(-24, 24.01, 4.8)
            A_ = [(lc[0] + a, y, lc[2] - 24) for a in gl] + [(lc[0] - 24, y, lc[2] + a) for a in gl]
            B_ = [(lc[0] + a, y, lc[2] + 24) for a in gl] + [(lc[0] + 24, y, lc[2] + a) for a in gl]
            fr.segments(np.array(A_), np.array(B_), STAR * 0.5 + TEAL * 0.2, (0.06 + 0.4 * pas) * near, width=1.0)
        # stars streaming past
        S = STARS['P'][:1500] * 0.12 + np.array([lc[0], 0, lc[2]])
        S[:, 1] = (S[:, 1] - (lc[1] - LIGHTS0[1]) * 2.0) % 200 - 100 + lc[1]
        sp = 4.0 + 1.8 * max(0.0, t - 108.4)
        sk = smooth(t, 108.6, 110.0)
        fr.segments(S, S + np.array([0, -0.18 * sp, 0]), STAR, STARS['b'][:1500] * 0.25 * sk, width=1.0)
        # the wall: a dome of light above
        wk = smooth(t, 111.5, 114.5)
        D = self.dome * 400 + np.array([lc[0], WALL_Y + 400, lc[2]])
        fr.points(D, STAR * 0.5 + WARM * 0.5, 0.3 * wk + 1.5 * smooth(t, 114.8, 115.4))
        white = smooth(t, 115.1, 115.4) * (1 - 0.0 * smooth(t, 115.4, 115.7))
        bg = space_bg(0.4)
        return compose2(fr, t, bg=bg, exposure=1.05 + 1.5 * smooth(t, 114.8, 115.4), white=white)


# ---------------------------------------------------------------------------------- the room
def orbit_pose(t):
    a = np.deg2rad(-35 + 95 * smooth(t, 115.7, 121.5))
    r = 2.7 - 0.3 * smooth(t, 115.7, 121.5)
    pos = CHAIR + np.array([r * np.sin(a), 0.75 + 0.2 * np.sin(t * 0.3), -r * np.cos(a)])
    return pose(pos, CHAIR + np.array([0, 0.15, 0]), 1250)


KEYS_C = KEYS.mean(0)
KEY_POSE = pose(KEYS_C + np.array([0.35, 0.55, -0.85]), KEYS_C, 1400)


def room_pose(t):
    p = orbit_pose(t)
    p = lerp_pose(p, KEY_POSE, smoother(t, 121.0, 122.6))
    d = np.exp(np.log(300.0) * ease_in(t, 124.4, 130.0, 1.6))
    away = pose(KEYS_C + (KEY_POSE[0] - KEYS_C) * d, KEYS_C, 1400)
    return lerp_pose(p, away, smoother(t, 124.2, 125.4)) if t < 125.4 else away


class C31(Shot):
    """A room at the end of the light: out of the white, a room draws itself in lines of light; a
    console of keys and an empty chair. The camera circles the chair; the two lights hover by it.
    And no one holding the keys: close on the keys, dark and still. Where we live, an
    unfinished universe: we pull back and back; the room is a point inside the lattice; on the
    drop-out the point goes out."""
    t0, t1 = 115.7, 130.5

    def setup(self):
        rng = np.random.default_rng(31)
        mid = (ROOM_A + ROOM_B) / 2
        self.reveal = np.clip(np.linalg.norm(mid - CHAIR, axis=1) / 6.0, 0, 1)
        self.big = lattice(n=9, span=160.0, center=KEYS_C)

    def render(self, t):
        p = room_pose(t)
        cam = cam_of(p, t, amp=AMP * 0.7)
        fr = Frame(cam, focus=float(np.linalg.norm(p[1] - p[0])), aperture=0.012 * (1 - smooth(t, 124.0, 125.0)))
        dr = np.clip((smooth(t, 115.6, 117.6) * 1.25 - self.reveal) / 0.25, 0, 1)
        draw_room(fr, inten=0.55, reveal=dr)
        A_, B_ = KEYSQ
        fr.segments(A_, B_, STAR * 0.5, 0.12 * smooth(t, 116.6, 117.6), width=1.0)
        for dx, c in ((-0.5, TEAL), (0.5, AMBER)):
            q = CHAIR + np.array([dx, 0.7 + 0.05 * np.sin(t * 1.3 + dx * 7), -0.2])
            hero(fr, q, c, 0.45 * smooth(t, 116.0, 117.0), 0.45)
        dust(fr, CHAIR + np.array([0, 1.0, 0.4]), (3.5, 2.0, 4.0), t, 400, WARM, 0.05, seed=31, rise=0.02)
        far = smooth(t, 125.0, 127.0)
        if far > 0:
            fr.points(self.big, STAR * 0.6 + TEAL * 0.2, 0.4 * far, min_r=0.6)
            hero(fr, KEYS_C + np.array([0, 0.8, 0]), WARM, 0.8 * smooth(t, 126.0, 127.5) * (1 - smooth(t, 130.0, 130.45)), 0.5)
        draw_stars(fr, t, 0.4 * far)
        white = 1 - smooth(t, 115.7, 116.6)
        fade = 1 - smooth(t, 130.15, 130.48)
        bg = gradient_bg((0.02, 0.016, 0.04), (0.035, 0.02, 0.03)) * (1 - far)
        return compose2(fr, t, bg=bg, exposure=1.05, white=white, fade=fade)


SHOTS = {k: v for k, v in globals().items() if k[:1] == 'C' and k[1:].isdigit()}
