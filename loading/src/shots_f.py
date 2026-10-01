"""FINAL CHORUS and OUTRO (S40-S47)."""
from shots_e import *

KV5_A, KV5_B = (720.0, 820.0), (1160.0, 700.0)
S41_CAM = (1250.0, 950.0, 1.3)


def s41_screen(p):
    return to_screen(Cam(*S41_CAM).matrix(1.0), *p)


# =====================================================================================
class S40(Shot):
    """I...: the flat page from above, its marks glowing - thousands of them, every one a life.
    The two lights come down toward it."""
    t0, t1 = 163.30, 168.20

    def setup(self):
        B = bg0b_tex()
        f = B['flat'] * 1.35 * (1 - 0.45 * B['line'][:, :, None])
        self.map = mix(f, dim.PAPER * (1 - 0.6 * B['line'][:, :, None]), 0.25)
        self.lm = B['lm']
        h, w = self.lm.shape
        n = cv2.resize(fbm_field(h // 8, w // 8, 12, 41, 3), (w, h))
        self.T = 163.4 + 3.0 * n

    def render(self, t):
        u = smoother(t, self.t0, self.t1)
        M = cam_matrix(1536.0, 960.0, mix(1.25, 1.7, u))
        mp = affine_sample(self.map, M)
        lm = affine_sample(self.lm, M)
        T = affine_sample(self.T.astype(np.float32), M)
        g = np.clip((t - T) / 0.4, 0, 1) * 0.6 + 0.4
        out = mp + (lm * g)[:, :, None] * fx.AMBER * 0.9
        lb = np.zeros_like(out)
        for (p, col, i) in ((KV5_A, TEAL, 0), (KV5_B, fx.AMBER, 1)):
            ex, ey = s41_screen(p)
            k = ease_out(t, self.t0, self.t1, 2)
            x = mix(ex + (i - 0.5) * 300, ex, k)
            y = mix(-80.0, ey, k)
            fx.point_light(lb, x, y, size=1.5 + 2.0 * k, color=col, intensity=1.4)
        out = out + lb
        emis = np.clip(lm * g * 1.2 + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.1, vig=0.24, diff=0.08)


class KV5Line:
    def __init__(self):
        self.W = KV5World()
        self.line = Plate('KV5').line
        p = work('derived', 'KV5_drawT.npy')
        if os.path.exists(p):
            self.T = np.load(p).astype(np.float32)
        else:
            Ta = dim.stroke_order(self.line, seed=3, origin=KV5_A, speed=1800, spread=0.9)
            Tb = dim.stroke_order(self.line, seed=4, origin=KV5_B, speed=1800, spread=0.9)
            T = np.minimum(Ta, Tb)
            v = T[T < 1e5]
            lo, hi = np.percentile(v, 1), np.percentile(v, 99)
            self.T = np.clip((T - lo) / (hi - lo), 0, 1.2).astype(np.float32)
            self.T[T > 1e5] = 9
            np.save(p, self.T.astype(np.float16))
        h, w = self.line.shape
        self.wash = wash_arrival((h, w), self.W.PALM, 0.0, 1.0, seed=7)


_k5 = {}


def kv5line():
    if 'k' not in _k5:
        _k5['k'] = KV5Line()
    return _k5['k']


class S41(Shot):
    """And one day we'll be paper: the lights land and open into a pencil drawing of the two of
    them, sitting together; the flame is the one mark of colour between them."""
    t0, t1 = 168.20, 175.00

    def setup(self):
        self.K = kv5line()

    def cam(self, t):
        u = smoother(t, self.t0, self.t1)
        return Cam(S41_CAM[0] - 20 * u, S41_CAM[1] - 10 * u, S41_CAM[2] + 0.06 * u, ref=(S41_CAM[0], S41_CAM[1]))

    def render(self, t):
        K = self.K
        cam = self.cam(t)
        M = cam.matrix(1.0)
        paper = paper_view(M)
        tooth = tooth_view(paper)
        T = cam.sample(K.T, interp=cv2.INTER_NEAREST)
        L = cam.sample(K.line)
        vis = np.clip((t - (168.4 + T * 3.2)) / 0.2, 0, 1)
        out = graphite(paper, L * vis, dim.GRAPHITE, tooth, strength=0.85)
        lb = np.zeros_like(out)
        for (p, col) in ((KV5_A, TEAL), (KV5_B, fx.AMBER)):
            X, Y = to_screen(M, *p)
            k = 1 - smooth(t, 168.3, 169.6)
            if k > 0:
                out = fx.paper_light(out, X, Y, col, size=3.0, intensity=k)
        fX, fY = to_screen(M, *K.W.PALM)
        kf = smooth(t, 169.4, 170.6)
        flick = 0.9 + 0.1 * np.sin(t * 13) * np.sin(t * 4.1)
        if kf > 0:
            out = fx.paper_light(out, fX, fY - 60, fx.AMBER, size=4.5 * kf, intensity=kf * flick)
            fx.point_light(lb, fX, fY - 60, size=3.0, color=fx.AMBER, intensity=0.8 * kf * flick)
        out = out + lb
        return fx.finish(out, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.0, vig=0.18, diff=0.06)


class S42(Shot):
    """And we'll still be in the light: colour returns, outward from the flame, until the drawing
    is a painted night again - the two of them and the small fire between them."""
    t0, t1 = 175.00, 181.00

    def setup(self):
        self.K = kv5line()

    def cam(self, t):
        u = smoother(t, self.t0, self.t1)
        return Cam(S41_CAM[0] - 20 - 160 * u, S41_CAM[1] - 10 - 120 * u, S41_CAM[2] + 0.06 + 0.35 * u, ref=(S41_CAM[0], S41_CAM[1]))

    def render(self, t):
        K = self.K
        W = K.W
        cam = self.cam(t)
        M = cam.matrix(1.0)
        paper = paper_view(M)
        tooth = tooth_view(paper)
        L = cam.sample(K.line)
        base = graphite(paper, L, dim.GRAPHITE, tooth, strength=0.85)
        TT = 175.3 + cam.sample(K.wash) * 3.4
        img = cam.sample_depth(W.img, W.depth, k_far=0.9, k_near=1.0, d_far=0.3, d_near=0.8)
        out = wash_over(base, img, L * (1 - smooth(t, 178.0, 179.5)), TT, t, tooth, line_w=0.5)
        lb = np.zeros_like(out)
        fX, fY = to_screen(M, *W.PALM)
        flick = 0.9 + 0.1 * np.sin(t * 13) * np.sin(t * 4.1)
        fx.point_light(lb, fX, fY - 60, size=3.0, color=fx.AMBER, intensity=0.6 * flick)
        out = out + lb
        e = np.clip(lum(np.clip(cam.sample(W.light), 0, 1)) * 1.5 * smooth(t, 175.5, 177.0) + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=e, glow_strength=1.0, vig=mix(0.18, 0.28, smooth(t, 176, 179)), diff=0.10)


# =====================================================================================
class S43(Shot):
    """Maybe death is only a return: the flat page rolls back into a sphere; the lights return,
    spreading again from one place."""
    t0, t1 = 181.00, 188.00

    def setup(self):
        self.S = S21()
        self.S.setup()
        lm = self.S.G.lights
        gw, gh = self.S.G.gw, self.S.G.gh
        ys, xs = np.mgrid[0:gh, 0:gw].astype(np.float32)
        o = (0.38 * gw, 0.47 * gh)
        d = np.hypot((xs - o[0]) / gw, (ys - o[1]) / gh * 0.5)
        self.lT = (183.6 + 3.2 * d / d.max() * 2.2).astype(np.float32)

    def render(self, t):
        S = self.S
        fl = 1 - smoother(t, 181.3, 184.0)
        R = mix(330.0, 250.0, smooth(t, 185.5, 188.0))
        bg = space_bg(5)
        kw = dict(lon0=S.LON0 + 3.0 * max(0.0, t - 183.0), lat0=S.LAT0, flat=fl, flat_origin=S.origin, flat_center=(960.0, 430.0), spread=0.7)
        g = np.clip((t - self.lT) / 0.25, 0, 1)
        out, cov, lo = S.G.render(W_OUT, H_OUT, 960.0, 560.0, R, bg=bg.copy(), light_time=g, **kw)
        k = 1 - smooth(t, 181.2, 183.6)
        if k > 0:
            outf, _, _ = S.Gf.render(W_OUT, H_OUT, 960.0, 560.0, R, bg=bg.copy(), **kw)
            out = mix(out, outf, k)
        lb = np.zeros_like(out)
        if lo is not None:
            out = out + gblur(lo, 0.8)[:, :, None] * fx.AMBER * 0.9
        if fl < 0.98:
            atmosphere(lb, 960.0, 560.0, R, 0.8 * (1 - fl))
        out = out + lb
        emis = np.clip(lum(lb) * 2 + (gblur(lo, 1) if lo is not None else 0) * 1.4, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=1.1, vig=0.24, diff=0.08)


class S44(Shot):
    """Death is only a return: the constellation comes back - and a new line in it, two colours,
    rising from between the witnesses: their own path."""
    t0, t1 = 188.00, 192.50

    def setup(self):
        self.K = kv3ages()
        S3 = S03()
        S3.setup()
        self.Tl = S3.Tl - 25.9 + 188.6
        self.Tp = S3.Tp - 25.3 + 188.05
        rng = np.random.default_rng(2)
        self.path = []
        for i in range(12):
            f = i / 11
            self.path.append((1560 + 120 * np.sin(f * 4) + rng.normal(0, 10), 1080 - 760 * f, 188.4 + 2.6 * f))

    def cam(self, t):
        p = lerp_cam(t, [(188.0, dict(cx=1536.0, cy=1000.0, zoom=1.10)), (192.5, dict(cx=1536.0, cy=880.0, zoom=1.16))])
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 1000.0))

    def render(self, t):
        K = self.K
        cam = self.cam(t)
        base = K.plate(head_s=1.0, city=1.0)
        out = cam.sample_depth(base, K.W.depth, k_far=0.93, k_near=1.0, d_far=0.3, d_near=0.8)
        pa = np.clip((t - cam.sample(self.Tp)) / 0.2, 0, 1)
        la = np.clip((t - cam.sample(self.Tl, interp=cv2.INTER_NEAREST)) / 0.12, 0, 1)
        out = out + cam.sample(K.W.pts) * pa[:, :, None] + cam.sample(K.W.lines) * la[:, :, None] * 1.2
        M = cam.matrix(0.93)
        lb = np.zeros_like(out)
        prev = None
        for i, (x, y, ta) in enumerate(self.path):
            if t < ta:
                break
            X, Y = to_screen(M, x, y)
            col = TEAL if i % 2 == 0 else fx.AMBER
            fx.point_light(lb, X, Y, size=1.2, color=col, intensity=1.1)
            if prev is not None:
                ln = np.zeros((H_OUT, W_OUT), np.float32)
                pencil_stroke(ln, [prev, (X, Y)], width=1.0)
                lb += gblur(ln, 0.8)[:, :, None] * (0.5 * TEAL + 0.5 * fx.AMBER) * 0.5
            prev = (X, Y)
        out = out + lb
        e = np.clip(lum(cam.sample(K.W.pts)) * 3 * pa + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=e, glow_strength=1.0, vig=0.28, diff=0.10)


# =====================================================================================
class KV1States(S01):
    """The home frame in any mix of the four states."""

    def setup(self):
        S01.setup(self)

    def frame(self, cam, t, depth_a, line_k=1.0, wash_t=None, mark=1.0, keep_fig=0.0, flat_a=1.0):
        W = self.W
        M = cam.matrix(1.0)
        paper = paper_view(M)
        tooth = tooth_view(paper)
        L = cam.sample(W.line)
        out = graphite(paper, L * line_k, dim.GRAPHITE, tooth, strength=0.82)
        if wash_t is not None:
            off, sc = wash_t
            TT = off + (cam.sample(self.wash_T) - 9.5) * sc
            F = cam.sample(W.flat)
            out = mix(out, wash_over(out, F, L, TT, t, tooth, 0.55), flat_a)
        if depth_a is not None:
            D = cam.sample_depth(W.img, W.depth, k_far=0.93, k_near=1.0, d_far=0.25, d_near=0.95)
            da = depth_a if np.ndim(depth_a) else np.full((H_OUT, W_OUT), float(depth_a), np.float32)
            if keep_fig > 0:
                da = np.maximum(da, cam.sample(W.ca) * keep_fig)
            out = mix(out, D, da[:, :, None])
        mx, my = to_screen(M, *KV1_MARK)
        if mark > 0:
            out = fx.paper_light(out, mx, my, fx.AMBER, size=2.0, intensity=mark)
        return out


_k1s = {}


def kv1states():
    if 'k' not in _k1s:
        s = KV1States()
        s.setup()
        _k1s['k'] = s
    return _k1s['k']


class S45(Shot):
    """Two dimensions... three and one: the frame breathes between its states with the words -
    flat and drawn on 'two', deep again on 'three', and on 'one' everything leaves but one light."""
    t0, t1 = 192.50, 199.50

    def setup(self):
        self.K = kv1states()

    def render(self, t):
        K = self.K
        cam = Cam(1536.0, 1120.0, 1.06)
        depth = 1 - smooth(t, 192.7, 193.5) + smooth(t, 196.4, 196.9) - smooth(t, 197.9, 199.0)
        line = 1 - smooth(t, 197.9, 199.0)
        flat = 1 - smooth(t, 193.8, 195.2) + smooth(t, 196.2, 196.6) - smooth(t, 197.9, 199.0)
        out = K.frame(cam, t, np.clip(depth, 0, 1), line_k=np.clip(line, 0, 1), wash_t=(-100.0, 1.0), flat_a=float(np.clip(flat, 0, 1)), mark=smooth(t, 197.4, 198.4))
        lb = np.zeros_like(out)
        if depth > 0.01:
            twinkle(lb, cam.matrix(1.0), K.W.stars, t, amt=float(np.clip(depth, 0, 1)))
        out = out + lb
        e = np.clip(cam.sample(K.W.LM) * float(np.clip(depth, 0, 1)) * 1.3 + lum(lb) * 2, 0, 1)
        return fx.finish(out, t, emis=e, glow_strength=1.0, vig=0.2, diff=0.08)


class S46(Shot):
    """The hit: the one light is the first mark again; the layout redraws itself around it, with
    patches of colour where someone has already begun to paint."""
    t0, t1 = 199.50, 202.60

    def setup(self):
        self.K = kv1states()

    def render(self, t):
        K = self.K
        u = smoother(t, self.t0, self.t1)
        cam = Cam(mix(KV1_MARK[0], 1600.0, u), mix(KV1_MARK[1], 1180.0, u), float(np.exp(mix(np.log(2.4), np.log(1.15), ease_out(t, 199.9, 202.6, 3)))), ref=(1536.0, 1140.0))
        line = smooth(t, 199.9, 201.2)
        out = K.frame(cam, t, None, line_k=line, wash_t=(201.2, 3.6), flat_a=1.0, mark=1.0)
        return fx.finish(out, t, glow=False, vig=0.16, diff=0.05)


class S47(Shot):
    """Still loading: the colour keeps arriving but never finishes; a new light comes on; a pencil
    line keeps going past the edge of the paper. Fade."""
    t0, t1 = 202.60, 213.40
    NEW_LIGHT = (2613.0, 1180.0)

    def setup(self):
        self.K = kv1states()

    def render(self, t):
        K = self.K
        W = K.W
        u = smoother(t, self.t0, 211.5)
        cam = Cam(1600.0 - 64 * u, 1180.0 - 40 * u, 1.15 - 0.17 * u, ref=(1536.0, 1140.0))
        M = cam.matrix(1.0)
        wt = (201.2, 3.6)
        out = K.frame(cam, t, None, line_k=1.0, wash_t=wt, flat_a=1.0, mark=1.0)
        # depth arrives only where the colour has already settled longest (around the mark)
        TT = wt[0] + (cam.sample(K.wash_T) - 9.5) * wt[1]
        da = np.clip((t - TT - 1.5) / 0.6, 0, 1) * 0.85
        D = cam.sample_depth(W.img, W.depth, k_far=0.93, k_near=1.0, d_far=0.25, d_near=0.95)
        out = mix(out, D, da[:, :, None])
        X, Y = to_screen(M, *self.NEW_LIGHT)
        k = smooth(t, 205.4, 205.8)
        if k > 0:
            out = fx.paper_light(out, X, Y, fx.AMBER, size=1.6, intensity=k)
        lb = np.zeros_like(out)
        if k > 0:
            fx.point_light(lb, X, Y, size=1.2, intensity=0.8 * k + 0.6 * np.exp(-((t - 205.5) / 0.15) ** 2))
        g = np.zeros((H_OUT, W_OUT), np.float32)
        tooth = tooth_view(paper_view(M))
        grow = smooth(t, 203.0, 211.5)
        xs_ = np.linspace(3072 - 300, 3072 + 1400 * grow, 40)
        pts = [to_screen(M, xv, 1662 + 2 * np.sin(xv / 300)) for xv in xs_]
        pencil_stroke(g, pts, width=1.0)
        out = graphite(out, g, dim.GRAPHITE, tooth, strength=0.8)
        out = out + lb
        fade = 1 - smooth(t, 210.8, 213.0)
        return fx.finish(out, t, emis=np.clip(lum(lb) * 2, 0, 1), glow_strength=1.0, vig=0.18, diff=0.06) * fade


SHOTS = {'S40': S40, 'S41': S41, 'S42': S42, 'S43': S43, 'S44': S44, 'S45': S45, 'S46': S46, 'S47': S47}
