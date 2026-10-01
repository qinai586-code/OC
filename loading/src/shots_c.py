"""VERSE 2: signals, the card, falling flat (S15-S24)."""
from shots_b import *
import proj
import envs

A_LIGHT = (1140.0, 1330.0)     # A's heart-light on the ledge (KV1 plate)
B_LIGHT = (1900.0, 1345.0)
TEAL = np.array([0.40, 1.0, 0.86], np.float32)


# =====================================================================================
class S15(Shot):
    """You sent out your signals into the night: rings leave a city on the beat; each one
    sends a point of light up past the witnesses, out of the frame."""
    t0, t1 = 73.00, 76.85
    SRC = [(2361.0, 1236.0), (2566.0, 1268.0), (2237.0, 1150.0), (2613.0, 1180.0)]

    def setup(self):
        self.W = kv1()
        b = beats_between(73.1, 76.4)
        self.emit = [(tb, self.SRC[i % len(self.SRC)]) for i, tb in enumerate(b[::2])]

    def cam(self, t):
        p = lerp_cam(t, [(73.0, dict(cx=1960.0, cy=1150.0, zoom=1.48)), (76.85, dict(cx=1990.0, cy=1060.0, zoom=1.52))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1960.0, 1150.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        out = cam.sample_depth(W.img, W.depth, k_far=0.9, k_near=1.0, d_far=0.25, d_near=0.95)
        M = cam.matrix(0.92)
        Mn = cam.matrix(1.0)
        ca = cam.sample(W.ca)
        lb = np.zeros_like(out)
        ring = np.zeros((H_OUT, W_OUT), np.float32)
        for te, (x, y) in self.emit:
            a = t - te
            if a < 0 or a > 2.6:
                continue
            # the city pulses as it sends
            sx, sy = to_screen(M, x, y)
            fx.point_light(lb, sx, sy, size=1.4, intensity=1.4 * np.exp(-a / 0.25))
            # a ring on the curved surface: wide and thin (grazing view)
            r = 30 + 420 * (1 - np.exp(-a / 0.8))
            pts = [to_screen(M, x + r * np.cos(q), y + 0.17 * r * np.sin(q) + 0.00012 * (r * np.cos(q)) ** 2) for q in np.linspace(0, 2 * np.pi, 160)]
            tmp = np.zeros_like(ring)
            pencil_stroke(tmp, pts, width=1.0)
            ring = np.maximum(ring, gblur(tmp, 1.6) * np.exp(-a / 0.6) * 0.8)
            # and a point that climbs past the ledge into the night
            yy = y - 420 * a - 90 * a * a
            xx = x - 60 * a
            px, py = to_screen(M, xx, yy)
            near = smooth(a, 0.0, 1.6)
            fx.point_light(lb, px, py, size=0.8 + 0.8 * near, color=(1.0, 0.82, 0.55), intensity=1.2 * smooth(a, 0, 0.1))
            for j in range(1, 8):
                aj = a - j * 0.03
                if aj < 0:
                    break
                qx, qy = to_screen(M, x - 60 * aj, y - 420 * aj - 90 * aj * aj)
                fx.splat(lb, qx, qy, 0.9 + 0.6 * near, fx.AMBER, 0.25 * (1 - j / 8))
        lb += ring[:, :, None] * np.array([1.0, 0.78, 0.45]) * 0.45 * (1 - ca[:, :, None])
        twinkle(lb, Mn, W.stars, t)
        out = out + lb
        emis = np.clip(cam.sample(W.LM) * 1.2 + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.0, vig=0.27, diff=0.10)


# =====================================================================================
class S16(Shot):
    """You asked the dark forest for one answering light: a signal crosses the sky over the
    dark forest. Nothing answers. Then, at the edge of the sky, one star blinks red."""
    t0, t1 = 76.85, 80.45
    BLINK = 79.75

    def setup(self):
        self.layers, stars, self.fire, self.hz = forest()
        self.layers = [l for l in self.layers if l[0] != 'hill']
        self.stars = [s_ for s_ in stars if s_[2] > 0.4]
        self.red = (2480.0, 1980.0)

    def render(self, t):
        cx, cy, zoom = 1536.0, mix(2700.0, 2600.0, smooth(t, self.t0, self.t1)), 1.0
        Ms = {}

        def grab(out, M):
            Ms['sky'] = M
            return out
        out = envs.composite_layers(self.layers, cx, cy, zoom, (1536.0, 2700.0), extra={'sky': grab},
                                    kmap={'sky': 0.97, 'mountains': 0.975, 'far_forest': 0.98, 'mid_forest': 0.99, 'near_forest': 1.0})
        M = Ms['sky']
        lb = np.zeros_like(out)
        # the signal: a vast circle whose centre is far below the horizon, sweeping up the sky
        a = (t - 77.0) / 3.0
        if 0 < a < 1.05:
            ccx, ccy = 1536.0, 2700.0 + 2600.0
            r = 2600.0 + 2900.0 * a
            pts = [to_screen(M, ccx + r * np.cos(q), ccy + r * np.sin(q)) for q in np.linspace(np.pi * 1.15, np.pi * 1.85, 240)]
            ring = np.zeros((H_OUT, W_OUT), np.float32)
            pencil_stroke(ring, pts, width=1.2)
            ring = gblur(ring, 2.0) + 0.25 * gblur(ring, 10.0)
            lb += ring[:, :, None] * np.array([1.0, 0.8, 0.5]) * 0.30 * (1 - smooth(a, 0.7, 1.05))
        # every star holds still; one far star answers only with red
        rng = np.random.default_rng(3)
        for (x, y, b) in self.stars:
            ph = rng.random() * 6.28
            tw = 0.75 + 0.25 * np.sin(t * (0.6 + rng.random()) * 6.28 + ph)
            X, Y = to_screen(M, x, y)
            if -5 < X < W_OUT + 5 and -5 < Y < H_OUT + 5:
                fx.splat(lb, X, Y, 0.7, (0.8, 0.86, 1.0), 0.22 * b * tw)
        if t > self.BLINK - 0.1:
            X, Y = to_screen(M, *self.red)
            k = np.exp(-((t - self.BLINK) / 0.10) ** 2) + 0.35 * smooth(t, self.BLINK + 0.1, self.BLINK + 0.4)
            fx.point_light(lb, X, Y, size=1.2, color=fx.RED, intensity=1.3 * k)
        out = out + lb
        return fx.finish(out * 1.18, t, emis=np.clip(lum(lb) * 2.5, 0, 1), glow_strength=1.0, vig=0.30, diff=0.12)


# =====================================================================================
class S17(Shot):
    """Then a countdown burned red at the back of your eyes: in B's eye the red point pulses,
    and a thin red edge finds her cheek. She does not look away."""
    t0, t1 = 80.45, 84.05
    IRIS = (1778.0, 790.0)

    def setup(self):
        self.W = kv4()
        self.beats = beats_between(80.6, 84.0)

    def cam(self, t):
        p = lerp_cam(t, [(80.45, dict(cx=1830.0, cy=820.0, zoom=2.35)), (84.05, dict(cx=1800.0, cy=800.0, zoom=2.75))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1830.0, 820.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        bg = cam.sample_depth(W.bg, W.depth, k_far=0.62, k_near=0.86, d_far=0.25, d_near=0.6)
        brgb, ba = render_b_layer(W, cam, t, 0.08 + 0.04 * np.sin(t * 0.9), sway_amp=2.0)
        pulse = 0.0
        for bt in self.beats:
            pulse = max(pulse, np.exp(-max(0, t - bt) / 0.22) * (t >= bt))
        k = smooth(t, 80.6, 81.6)
        # a red rim along the face's sky-side edge (light from the left, where the star is)
        M = cam.matrix(1.0)
        a = ba
        edge = np.clip(a - cv2.warpAffine(a, np.float32([[1, 0, 5], [0, 1, 0]]), (W_OUT, H_OUT)), 0, 1)
        edge = gblur(edge, 1.5)
        brgb = brgb + edge[:, :, None] * fx.RED * 0.35 * k * (0.6 + 0.4 * pulse)
        out = over(bg, brgb, ba)
        lb = np.zeros_like(out)
        X, Y = to_screen(M, *self.IRIS)
        z = np.hypot(M[0, 0], M[1, 0])
        fx.point_light(lb, X, Y, size=1.1 / z, color=fx.RED, intensity=k * (0.6 + 1.2 * pulse))
        out = out + lb
        return fx.finish(out, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=0.8, vig=0.30, diff=0.12)


# =====================================================================================
class S18(Shot):
    """And the laws stayed the same as your certainty died: the constellation's lines go out,
    one by one, back along the way they were drawn. The points stay. A keeps looking up."""
    t0, t1 = 84.05, 87.65

    def setup(self):
        self.K = kv3ages()
        p = work('derived', 'S03_lineT.npy')
        if not os.path.exists(p):
            S03().setup()
        Tl = np.load(p).astype(np.float32)
        v = Tl[Tl < 50]
        self.off = (84.4 + (v.max() - Tl) / (v.max() - v.min() + 1e-6) * 2.8).astype(np.float32)
        self.off[Tl >= 50] = 0

    def cam(self, t):
        p = lerp_cam(t, [(84.05, dict(cx=1536.0, cy=760.0, zoom=1.22)), (87.65, dict(cx=1536.0, cy=820.0, zoom=1.16))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 760.0))

    def render(self, t):
        K = self.K
        cam = self.cam(t)
        base = K.plate(head_s=1.0, city=1.0, const_pts=1.0, const_lines=0.0)
        out = cam.sample_depth(base, K.W.depth, k_far=0.93, k_near=1.0, d_far=0.3, d_near=0.8)
        off = cam.sample(self.off, interp=cv2.INTER_NEAREST)
        la = np.clip((off - t) / 0.15, 0, 1)
        # a dying line glows once before it goes
        flare = np.exp(-((t - off) / 0.08) ** 2) * (off > 0)
        lines = cam.sample(K.W.lines)
        out = out + lines * (la + 1.5 * flare)[:, :, None] * 1.2
        e = np.clip(lum(cam.sample(K.W.pts)) * 3 + lum(lines) * 3 * (la + flare), 0, 1)
        return fx.finish(out, t, emis=e, glow_strength=1.0, vig=0.28, diff=0.10)


# =====================================================================================
_bg0b = {}


def bg0b_tex():
    if 't' not in _bg0b:
        tex = imread(work('plates', 'BG0b.png'))
        _bg0b['t'] = tex
        p = work('derived', 'BG0b_flat.npy')
        if os.path.exists(p):
            _bg0b['flat'] = np.load(p).astype(np.float32)
        else:
            _bg0b['flat'] = dim.flat_cel(tex, n_colors=22)
            np.save(p, _bg0b['flat'].astype(np.float16))
        p = work('derived', 'BG0b_line.npy')
        if os.path.exists(p):
            _bg0b['line'] = np.load(p).astype(np.float32)
        else:
            _bg0b['line'] = dim.line_art(tex)
            np.save(p, _bg0b['line'].astype(np.float16))
        _bg0b['lm'] = dim.light_mask(tex)
    return _bg0b


def sleeve_sky(t, edge_y0=230.0, slope=0.06, seed=11):
    """A starfield whose top is cut off by a straight edge: the dark is a sleeve."""
    bg = space_bg(seed).copy()
    ys, xs = np.mgrid[0:H_OUT, 0:W_OUT].astype(np.float32)
    edge = edge_y0 + slope * (xs - 960)
    m = smoothstep(-1.5, 1.5, ys - edge)
    void = np.array([0.002, 0.003, 0.008], np.float32)
    rim = np.exp(-((ys - edge) / 2.0) ** 2) * 0.06
    return bg * 1.3 * m[:, :, None] + void * (1 - m[:, :, None]) + rim[:, :, None] * np.array([0.6, 0.7, 1.0]), edge


def card_quad(center, rot, size=(0.63, 0.88)):
    w, h = size
    R = proj.rot_y(rot[1]) @ proj.rot_x(rot[0]) @ proj.rot_z(rot[2])
    corners = np.array([[-w / 2, h / 2, 0], [w / 2, h / 2, 0], [w / 2, -h / 2, 0], [-w / 2, -h / 2, 0]])
    return corners @ R.T + np.asarray(center), R @ np.array([0, 0, 1.0])


class S19(Shot):
    """And something above you drew a card from its sleeve: the sky has an edge; out from under
    it slides a sheet of paper, turning, catching the Earth's light."""
    t0, t1 = 87.65, 91.25

    def setup(self):
        self.B = bg0b_tex()
        self.paper = paper_tex()[1]

    def render(self, t):
        bg, edge = sleeve_sky(t)
        R = 2500.0
        out, m, _ = proj.raycast_globe(self.B['t'], W_OUT, H_OUT, 960.0, 1080.0 + R - 330.0 + 30 * smooth(t, self.t0, self.t1), R, 112.0, 38.0, bg=bg)
        lb = np.zeros_like(out)
        atmosphere(lb, 960.0, 1080.0 + R - 330.0 + 30 * smooth(t, self.t0, self.t1), R, 0.7)
        out = out + lb
        cam = proj.PCam(pos=(0, 0, 0), f=1500.0)
        # slide out (88.0-89.4) then tumble down toward the Earth
        s = ease_out(t, 88.0, 89.5, 3)
        a = max(0.0, t - 89.3)
        center = (0.25 - 0.20 * s - 0.10 * a, 1.30 - 0.62 * s - 0.16 * a * a, 3.4)
        rot = (0.95 - 0.75 * s + 0.9 * a, -0.35 + 0.45 * s + 0.7 * a, 0.10 + 0.10 * a)
        P, n = card_quad(center, rot)
        q, z = cam.project(P)
        to_cam = -np.asarray(center) / np.linalg.norm(center)
        ldir = np.array([0.0, -0.8, -0.3])
        ldir /= np.linalg.norm(ldir)
        diff = abs(float(n @ ldir))
        refl = ldir - 2 * (ldir @ n) * n
        spec = max(0.0, float(refl @ to_cam)) ** 40
        shade = 0.10 + 0.55 * diff
        tex = self.paper[:512, :360] * shade
        # earthlight: warm-blue gradient across the face from the side facing the planet
        gy = np.linspace(0.0, 1.0, tex.shape[0], dtype=np.float32)[:, None, None]
        tex = tex + gy * np.array([0.10, 0.12, 0.20]) * diff + np.array([1.0, 0.92, 0.80]) * spec * 1.6
        card_img, ca, Hm = proj.warp_quad(np.zeros_like(out), tex, q)
        # the sleeve hides what has not come out yet
        ys = np.arange(H_OUT, dtype=np.float32)[:, None]
        vis = smoothstep(-1.0, 1.0, ys - edge)
        ca = ca * vis
        out = out * (1 - ca[:, :, None]) + card_img * vis[:, :, None]
        # bright paper edge
        e = np.zeros((H_OUT, W_OUT), np.float32)
        pencil_stroke(e, list(q) + [q[0]], width=0.8)
        out = out + (e * vis)[:, :, None] * np.array([0.9, 0.9, 1.0]) * (0.12 + 1.5 * spec)
        emis = np.clip((e * vis) * (0.3 + spec) + ca * spec, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.2, vig=0.26, diff=0.10)


# =====================================================================================
class S20(Shot):
    """A sheet thinner than any mind could believe: edge-on, the card is a single line of light,
    sinking toward the rim of the world."""
    t0, t1 = 91.25, 94.85
    TOUCH = (1536.0, 552.0)

    def setup(self):
        self.img = cached(('bg0a',), lambda: imread(work('plates', 'BG0a.png')))

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        cx = 1536.0
        cy = mix(760.0, 640.0, u)
        zoom = float(np.exp(mix(np.log(1.15), np.log(1.6), u)))
        M = cam_matrix(cx, cy, zoom)
        out = affine_sample(self.img, M)
        lb = np.zeros_like(out)
        # the card descends: its lower edge reaches the rim at the end of the shot
        y_low = mix(-600.0, self.TOUCH[1] - 8, ease_out(t, self.t0, self.t1 + 0.4, 2))
        L = 1150.0
        ang = 0.22 + 0.03 * np.sin(t * 0.7)
        thick = 5.0 * abs(np.sin((t - self.t0) * 1.9 + 0.4)) ** 6
        dx, dy = np.sin(ang) * L, np.cos(ang) * L
        x_low, x_top = self.TOUCH[0], self.TOUCH[0] - dx
        p0 = to_screen(M, x_low, y_low)
        p1 = to_screen(M, x_top, y_low - dy)
        line = np.zeros((H_OUT, W_OUT), np.float32)
        sc = 1.0 / np.hypot(M[0, 0], M[1, 0])
        pencil_stroke(line, [p0, p1], width=0.7 + thick * sc)
        flash = (thick / 5.0) ** 2
        lb += gblur(line, 0.5)[:, :, None] * np.array([0.9, 0.92, 1.0]) * (0.45 + 1.6 * flash)
        out = out + lb
        emis = np.clip(cv2.resize(dim.light_mask(cv2.resize(out, (960, 540))), (W_OUT, H_OUT)) + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.1, vig=0.26, diff=0.10)


# =====================================================================================
class S21(Shot):
    """It touched the edge of everything and everything fell flat: the sheet touches the top of
    the world; from that point the sphere unrolls into the flat map. The lights stop glowing
    and become marks."""
    t0, t1 = 94.85, 98.45
    TOUCH_T = 95.42
    R = 330.0
    LON0, LAT0 = 150.0, 20.0

    def setup(self):
        import globe as G
        G.LAT_TOP, G.LAT_BOT = 88.0, -88.0
        B = bg0b_tex()
        tex = B['t']
        h = tex.shape[0]

        def pad(a):
            top = cv2.flip(a[:int(h * 0.04)], 0)
            bot = cv2.flip(a[-int(h * 0.12):], 0)
            return np.vstack([gblur(top, 6), a, gblur(bot, 6)])
        tp, fp = pad(tex), pad(B['flat'])
        lm = dim.light_mask(tp)
        self.G = G.Globe(tp, lm, grid_w=2600)
        self.Gf = G.Globe(fp, None, grid_w=2600)
        self.Gl = G.Globe(np.dstack([pad(B['line'])] * 3), None, grid_w=2600)
        V0 = (88.0 - 84.0) / 176.0
        self.origin = ((self.LON0 - (-22.0)) % 360 / 360.0, 0.03)

    def render(self, t):
        fl = smoother(t, self.TOUCH_T, 97.3)
        bg = space_bg(5)
        cx, cy = 960.0, 560.0
        kw = dict(lon0=self.LON0 + 2.0 * max(0, self.TOUCH_T - t), lat0=self.LAT0, flat=fl, flat_origin=self.origin,
                  flat_center=(960.0, 430.0), spread=0.7)
        out, cov, lo = self.G.render(W_OUT, H_OUT, cx, cy, self.R, bg=bg.copy(), **kw)
        k = smooth(t, self.TOUCH_T + 0.2, 97.6)
        if k > 0:
            outf, _, _ = self.Gf.render(W_OUT, H_OUT, cx, cy, self.R, bg=bg.copy(), **kw)
            outl, _, _ = self.Gl.render(W_OUT, H_OUT, cx, cy, self.R, bg=np.zeros_like(bg), **kw)
            outf = outf * (1 - 0.45 * outl[:, :, :1])
            out = mix(out, outf, k)
        lb = np.zeros_like(out)
        glow_k = 1.0 - 0.8 * smooth(t, 96.3, 97.5)
        if lo is not None:
            out = out + gblur(lo, 0.8)[:, :, None] * fx.AMBER * mix(0.5, 0.9, glow_k)
        if fl < 0.98:
            atmosphere(lb, cx, cy, self.R, 0.8 * (1 - fl))
        # the sheet's line comes down to the top of the world
        if t < self.TOUCH_T + 0.3:
            yl = mix(-200.0, cy - self.R + 2, ease_out(t, self.t0, self.TOUCH_T, 2))
            line = np.zeros((H_OUT, W_OUT), np.float32)
            pencil_stroke(line, [(960.0, yl), (960.0 - 40, yl - 900)], width=1.4)
            fade = 1 - smooth(t, self.TOUCH_T, self.TOUCH_T + 0.3)
            lb += gblur(line, 0.6)[:, :, None] * np.array([0.9, 0.92, 1.0]) * 1.3 * fade
        # contact: one hard flash
        hit = np.exp(-((t - self.TOUCH_T) / 0.07) ** 2)
        fx.point_light(lb, 960.0, cy - self.R + 2, size=5.0, color=(1.0, 1.0, 1.0), intensity=2.5 * hit)
        out = out + lb
        emis = np.clip(lum(lb) * 2 + (gblur(lo, 1) * glow_k if lo is not None else 0), 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.0 * glow_k + 0.2, vig=0.24, diff=0.08)


# =====================================================================================
class S22(Shot):
    """Three dimensions into two and still I looked at that: the same lateral move as before
    the fall, but now the bay has no depth. It is a flat sheet, then a drawing. B keeps looking."""
    t0, t1 = 98.45, 102.05

    def setup(self):
        self.W = kv4()
        W = self.W

        def mk_flat():
            return dim.flat_cel(W.bg, n_colors=24)
        p = work('derived', 'KV4_bgflat.npy')
        if os.path.exists(p):
            self.flat = np.load(p).astype(np.float32)
        else:
            self.flat = mk_flat()
            np.save(p, self.flat.astype(np.float16))
        p = work('derived', 'KV4_bgline.npy')
        if os.path.exists(p):
            self.line = np.load(p).astype(np.float32)
        else:
            self.line = dim.line_art(W.bg)
            np.save(p, self.line.astype(np.float16))
        h, w = W.bg.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        edge = np.minimum(np.minimum(xs, w - xs) / w, np.minimum(ys, h - ys) / h * 0.8)
        n = cv2.resize(fbm_field(h // 4, w // 4, 60, 16, 5), (w, h))
        self.U = np.clip(edge * 2.2 + 0.3 * n, 0, 1)
        self.paper, self.tooth = dim.paper_texture(h, w, seed=17)

    def cam(self, t):
        p = lerp_cam(t, [(98.45, dict(cx=1740.0, cy=905.0, zoom=1.09)), (102.05, dict(cx=1440.0, cy=925.0, zoom=1.12))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1740.0, 905.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        flat = cam.sample(self.flat)            # k = 1 everywhere: no parallax
        L = cam.sample(self.line)
        bg = flat * (1 - 0.35 * L[:, :, None])
        U = cam.sample(self.U)
        k = np.clip((t - 99.9 - U * 1.6) / 0.04, 0, 1)
        if k.max() > 0:
            drawing = graphite(cam.sample(self.paper), L * 1.1, dim.GRAPHITE, cam.sample(self.tooth), strength=0.8)
            kk = gblur(k, 1.2)
            pool = np.clip(kk * (1 - kk) * 4, 0, 1)
            bg = mix(bg, drawing, kk[:, :, None]) * (1 - 0.3 * pool[:, :, None])
        brgb, ba = render_b_layer(W, cam, t, 0.36, sway_amp=2.5)
        out = over(bg, brgb, ba)
        return fx.finish(out, t, glow=False, vig=0.22, diff=0.08)


# =====================================================================================
class KV1Layers:
    """KV1 split into foreground (A, B, the ledge) and a sky with no Earth."""

    def __init__(self):
        self.W = kv1()
        W = self.W
        fg = np.maximum(W.ca, smoothstep(0.45, 0.55, W.depth))
        self.fg_a = fg
        p = work('derived', 'KV1_skyonly2.npy')
        if os.path.exists(p):
            self.sky = np.load(p).astype(np.float32)
        else:
            h, w = fg.shape
            ys = np.arange(h, dtype=np.float32)[:, None, None]
            col = W.img[600:640].mean(axis=(0, 1))
            g = np.clip((ys - 620) / 1300, 0, 1)
            low = col * (1 - 0.45 * g) + np.array([0.02, 0.025, 0.05]) * g
            k = smoothstep(560.0, 660.0, ys)
            sky = W.img * (1 - k) + low * k * np.ones((1, w, 1), np.float32)
            self.sky = sky.astype(np.float32)
            np.save(p, self.sky.astype(np.float16))


_kl = {}


def kv1layers():
    if 'l' not in _kl:
        _kl['l'] = KV1Layers()
    return _kl['l']


class S23(Shot):
    """And the dark came closer and the flat came near: the curved world below is now a flat
    sheet with a straight edge; the sheet's far edge lifts and rises toward them like a page."""
    t0, t1 = 102.05, 105.65

    def setup(self):
        self.L = kv1layers()
        B = bg0b_tex()
        f = B['flat'] * 1.35 * (1 - 0.45 * B['line'][:, :, None])
        f = mix(f, dim.PAPER * (1 - 0.6 * B['line'][:, :, None]), 0.18)
        f = f + B['lm'][:, :, None] * fx.AMBER * 0.6
        self.tex = cv2.resize(f, (1536, 1024), interpolation=cv2.INTER_AREA)
        self.tex_small = cv2.resize(f, (512, 341), interpolation=cv2.INTER_AREA)

    def cam(self, t):
        p = lerp_cam(t, [(102.05, dict(cx=1536.0, cy=1100.0, zoom=1.08)), (105.65, dict(cx=1536.0, cy=1150.0, zoom=1.16))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 1100.0))

    def render(self, t):
        L = self.L
        W = L.W
        cam = self.cam(t)
        dark = smooth(t, 102.5, 105.4)
        sky = cam.sample(L.sky) * (1 - 0.55 * dark)
        lb = np.zeros_like(sky)
        twinkle(lb, cam.matrix(1.0), W.stars, t, amt=1 - 0.7 * dark)
        out = sky + lb
        # the page: horizontal at first (its straight far edge where the curved rim was)
        th = 1.25 * ease_in(t, 102.6, 105.65, 2)
        pc = proj.PCam(pos=(0, 0, 0), pitch=0.119, f=1400.0)
        hinge_z, ydrop, D, Wd = 2.2, -1.0, 70.0, 110.0
        def P(x, d):
            return np.array([x, ydrop + d * np.sin(th), hinge_z + d * np.cos(th)])
        quad = np.array([P(-Wd / 2, D), P(Wd / 2, D), P(Wd / 2, 0), P(-Wd / 2, 0)])
        q, z = pc.project(quad)
        tex = self.tex if th > 0.4 else self.tex_small
        page, pa, _ = proj.warp_quad(np.zeros_like(out), tex, q)
        # far = hazier
        out = out * (1 - pa[:, :, None]) + page * (1 - 0.35 * (1 - smooth(th, 0, 0.9)))
        e = np.zeros((H_OUT, W_OUT), np.float32)
        pencil_stroke(e, [q[0], q[1]], width=1.0 + 3.0 * smooth(th, 0.2, 1.2))
        out = out + gblur(e, 0.8)[:, :, None] * np.array([0.95, 0.93, 0.88]) * 0.7
        fg = cam.sample(W.img)
        fa = cam.sample(L.fg_a)
        out = over(out, fg * (1 - 0.3 * dark), fa)
        emis = np.clip(lum(lb) * 2 + gblur(e, 2) * 0.8, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.0, vig=mix(0.26, 0.42, dark), diff=0.10)


# =====================================================================================
class S24(Shot):
    """We followed it upward to the edge of the sphere: in front of the page that came near,
    A and B drain to pencil from the top down, their drawings gather into two lights - teal
    and amber - and the lights rise after the page's edge."""
    t0, t1 = 105.65, 108.40
    GATHER = (106.95, 107.6)

    def setup(self):
        self.L = kv1layers()
        W = self.L.W
        self.line = Plate('KV1').line
        h, w = W.img.shape[:2]
        ys = np.arange(h, dtype=np.float32)[:, None] * np.ones((1, w), np.float32)
        n = cv2.resize(fbm_field(h // 2, w // 2, 6, 31, 2), (w, h))
        n2 = cv2.resize(fbm_field(h // 8, w // 8, 30, 32, 3), (w, h))
        self.T = 105.80 + 1.0 * np.clip((ys - 1000) / 1050, 0, 1) + 0.08 * n + 0.12 * n2
        B = bg0b_tex()
        self.page_line = B['line']

    def cam(self, t):
        p = lerp_cam(t, [(105.65, dict(cx=1530.0, cy=1330.0, zoom=1.75)), (108.40, dict(cx=1530.0, cy=1180.0, zoom=1.60))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1530.0, 1330.0))

    def render(self, t):
        L = self.L
        W = L.W
        cam = self.cam(t)
        M = cam.matrix(1.0)
        paper = paper_view(M)
        tooth = tooth_view(paper)
        # behind them: the page, close, its map in pencil (it rises slowly out of frame)
        pl = affine_sample(self.page_line, cam_matrix(1536.0, 900.0 + 300 * (t - self.t0), 0.55), border=cv2.BORDER_REFLECT)
        out = graphite(paper, pl * 0.45, dim.GRAPHITE, tooth, strength=0.6)
        line = cam.sample(self.line)
        fa = cam.sample(L.fg_a)
        ca = cam.sample(W.ca)
        ledge = np.clip(fa - ca, 0, 1)
        out = over(out, paper, ledge * 0.9)
        out = graphite(out, line * ledge * 1.1, dim.GRAPHITE, tooth, strength=0.8)
        T = cam.sample(self.T)
        drain = np.clip((t - T) / 0.06, 0, 1)
        g0, g1 = self.GATHER
        u = smoother(t, g0, g1)
        lb = np.zeros_like(out)
        xmid = to_screen(M, 1536, 0)[0]
        if u < 1:
            fig = cam.sample(W.img)
            for (lx, ly), side in ((A_LIGHT, 0), (B_LIGHT, 1)):
                sx, sy = to_screen(M, lx, ly)
                half = np.zeros((H_OUT, W_OUT), np.float32)
                if side == 0:
                    half[:, :int(xmid)] = 1
                else:
                    half[:, int(xmid):] = 1
                s = 1 - u
                A = np.float32([[s, 0, sx * (1 - s)], [0, s, sy * (1 - s)]])
                a_fig = cv2.warpAffine(ca * half, A, (W_OUT, H_OUT))
                l_fig = cv2.warpAffine(line * ca * half, A, (W_OUT, H_OUT))
                f_rgb = cv2.warpAffine(fig, A, (W_OUT, H_OUT))
                d_fig = cv2.warpAffine(drain * half, A, (W_OUT, H_OUT))
                # paper body (so the page behind does not show through), painted until drained
                body = over(paper, f_rgb, 1 - d_fig)
                out = over(out, body, a_fig * (1 - u) ** 0.5)
                out = graphite(out, l_fig * d_fig * (1 - u), dim.GRAPHITE, tooth, strength=0.85)
        for (lx, ly), col, ph in ((A_LIGHT, TEAL, 0.0), (B_LIGHT, fx.AMBER, 0.9)):
            sx, sy = to_screen(M, lx, ly)
            k = smooth(t, g0 + 0.15, g1)
            rise = max(0.0, t - g1)
            y = sy - 1100 * rise ** 1.5
            x = sx + 25 * np.sin(rise * 3 + ph) * rise
            if k > 0:
                fx.point_light(lb, x, y, size=2.2, color=col, intensity=1.3 * k)
                for j in range(1, 10):
                    rj = max(0.0, rise - j * 0.035)
                    fx.splat(lb, sx + 25 * np.sin(rj * 3 + ph) * rj, sy - 1100 * rj ** 1.5, 2.0, col, 0.25 * (1 - j / 10) * smooth(rise, 0, 0.1))
        out = out + lb
        return fx.finish(out, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.2, vig=0.18, diff=0.08)


SHOTS = {'S15': S15, 'S16': S16, 'S17': S17, 'S18': S18, 'S19': S19, 'S20': S20, 'S21': S21, 'S22': S22, 'S23': S23, 'S24': S24}
