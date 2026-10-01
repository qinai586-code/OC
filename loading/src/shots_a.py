"""PROLOGUE and VERSE 1: S01-S04."""
from shotbase import *

KV1_MARK = (2361.0, 1236.0)            # the first mark = a city light right of B
KV1_RIM_CIRCLE = (1467.04, 6717.37, 5863.0 + 2.0)   # fitted to the painted rim (depth edge)
KV1_CITIES = [(2361, 1236), (2566, 1268), (2237, 1150), (934, 1318), (2613, 1180), (738, 1546), (484, 1443)]
KV1_GAP_X = 1525.0                      # screen gap between A and B (plate x)


def kv1_rim_circle():
    return KV1_RIM_CIRCLE


class KV1World:
    """Shared KV1 resources: the home frame of the film."""

    def __init__(self):
        self.P = Plate('KV1')
        P = self.P
        self.img = P.img
        self.depth = gblur(P.depth, 3.0)
        self.LM = P.lights
        lm_d = cv2.dilate(self.LM, np.ones((5, 5), np.uint8))
        self.line = P.line * (1 - 0.85 * lm_d)
        self.flat = P.flat
        self.ca = P.char_alpha
        self.cx, self.cy, self.r = kv1_rim_circle()
        sky = np.zeros(self.LM.shape, np.float32)
        sky[:780] = 1
        self.stars = find_stars(self.img, sky, thr=0.18, max_n=60)
        # star twinkle needs the painted star removed underneath
        self.dark_lights = None

    def lights_off(self):
        """KV1 with every human light removed (before people)."""
        def make():
            m = cv2.dilate((self.LM > 0.04).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(np.float32)
            # remove only on the Earth, not the characters
            m = m * (1 - cv2.dilate((self.ca > 0.1).astype(np.uint8), np.ones((9, 9), np.uint8)))
            out = fill_region(self.img, m, scale=2)
            # and the warm haze the cities cast on the surface
            earth = ((self.depth > 0.12) & (self.depth < 0.75)).astype(np.float32) * (1 - cv2.dilate((self.ca > 0.1).astype(np.uint8), np.ones((15, 15), np.uint8)))
            earth = gblur(earth, 4)
            warm = np.clip(out[:, :, 0] - out[:, :, 2] * 0.92, 0, 1)
            out = out - (warm * earth)[:, :, None] * np.array([1.0, 0.72, 0.15])
            return np.clip(out, 0, 1)
        return cached(('kv1dark',), lambda: np.load(work('derived', 'KV1_dark.npy')).astype(np.float32) if os.path.exists(work('derived', 'KV1_dark.npy')) else _save(work('derived', 'KV1_dark.npy'), make()))


def _save(p, a):
    np.save(p, a.astype(np.float16))
    return a


_kv1 = {}


def kv1():
    if 'w' not in _kv1:
        _kv1['w'] = KV1World()
    return _kv1['w']


def twinkle(buf, M, stars, t, amt=1.0, seed=0, freeze=None):
    rng = np.random.default_rng(seed)
    for i, (x, y, b) in enumerate(stars):
        ph = rng.random() * 6.28
        fr = 0.6 + rng.random() * 1.4
        tw = 0.5 + 0.5 * np.sin(t * fr * 2 * np.pi + ph)
        if freeze is not None:
            tw = mix(tw, 0.55, freeze)
        sx, sy = to_screen(M, x, y)
        if -10 < sx < W_OUT + 10 and -10 < sy < H_OUT + 10:
            fx.point_light(buf, sx, sy, size=0.6 + 0.6 * b, color=(0.75, 0.82, 1.0), intensity=amt * (0.15 + 0.35 * tw) * b)


def wash_arrival(shape, origin, t_start, dur, seed=0, warp=240.0):
    """Arrival time of a watercolour wash spreading from origin (organic, domain-warped front)."""
    h, w = shape
    sh, sw = h // 4, w // 4
    ys, xs = np.mgrid[0:sh, 0:sw].astype(np.float32) * 4
    n1 = fbm_field(sh, sw, 180, seed + 1, 4) - 0.5
    n2 = fbm_field(sh, sw, 180, seed + 2, 4) - 0.5
    n3 = fbm_field(sh, sw, 30, seed + 3, 3) - 0.5
    d = np.hypot(xs - origin[0] + n1 * warp * 2, ys - origin[1] + n2 * warp * 2)
    d = d / np.percentile(d, 99.5)
    n4 = fbm_field(sh, sw, 8, seed + 5, 2) - 0.5
    T = t_start + dur * (np.clip(d, 0, 1.15) + n3 * 0.05 + n4 * 0.012)
    return cv2.resize(T.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)


def wash_over(paper_img, flat, line, T, t, tooth, line_w=0.6, soak=0.07):
    """Composite cel colour over paper as a wash: damp pre-tint, pigment-pooled wet edge, then colour."""
    dt = t - T
    a = smoothstep(0.0, soak, dt)
    pre = smoothstep(-0.30, 0.0, dt) * (1 - a)
    wet = np.exp(-((dt - soak * 0.8) / (soak * 0.9)) ** 2) * a
    base = paper_img * (1 - 0.10 * pre[:, :, None]) + np.array([0.55, 0.58, 0.66]) * 0.10 * pre[:, :, None]
    col = flat * (1 - line_w * line[:, :, None]) * (0.92 + 0.08 * tooth[:, :, None])
    col = col * (1 - 0.28 * wet[:, :, None])
    return over(base, col, a)


# =====================================================================================
class S01(Shot):
    """Paper -> pencil -> cel -> depth. 'We were born in your traces'."""
    t0, t1 = 0.0, 18.0

    def setup(self):
        self.W = kv1()
        W = self.W
        h, w = W.line.shape
        p_arr = work('derived', 'S01_arrival.npy')
        if os.path.exists(p_arr):
            self.T = np.load(p_arr).astype(np.float32)
        else:
            fig = cv2.dilate((W.ca > 0.1).astype(np.uint8), np.ones((25, 25), np.uint8)).astype(np.float32)
            fig[1660:] = 1  # the ledge belongs to the figures' layer
            a_fig = dim.stroke_order(W.line * fig, seed=1, origin=(1550, 1500), speed=2600, spread=0.7)
            a_rest = dim.stroke_order(W.line * (1 - fig), seed=2, origin=KV1_MARK, speed=2200, spread=1.0)

            def norm(a):
                v = a[a < 1e5]
                lo, hi = np.percentile(v, 0.5), np.percentile(v, 99.5)
                return np.clip((a - lo) / (hi - lo + 1e-6), 0, 1.2)
            T = np.where(fig > 0.5, 6.6 + norm(a_fig) * 1.3, 7.5 + norm(a_rest) * 3.3).astype(np.float32)
            T[(a_fig > 1e5) & (a_rest > 1e5)] = 99
            self.T = T
            np.save(p_arr, T.astype(np.float16))
        self.wash_T = wash_arrival((h, w), KV1_MARK, 9.5, 3.4, seed=4)
        rng = np.random.default_rng(7)
        self.traces = []
        starts = [14.55, 14.95, 15.3, 15.75, 16.2, 16.6, 17.0]
        for (cx, cy), ts in zip(KV1_CITIES, starts):
            end_x = KV1_GAP_X + rng.uniform(-260, 260)
            self.traces.append(dict(o=(cx, cy), t=ts, ctrl=(mix(cx, end_x, 0.4) + rng.uniform(-120, 120), cy - 380),
                                    end=(end_x + rng.uniform(-80, 80), -260), dur=rng.uniform(3.2, 4.2), seed=rng.integers(1000)))

    def cam(self, t):
        keys = [(0.0, dict(cx=KV1_MARK[0], cy=KV1_MARK[1], zoom=3.4)),
                (2.0, dict(cx=KV1_MARK[0], cy=KV1_MARK[1], zoom=3.3)),
                (12.9, dict(cx=1536.0, cy=1140.0, zoom=1.04)),
                (14.3, dict(cx=1536.0, cy=1140.0, zoom=1.035)),
                (18.0, dict(cx=1536.0, cy=1118.0, zoom=1.085))]
        p = lerp_cam(t, keys)
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 1140.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        M = cam.matrix(1.0)
        paper = paper_view(M)
        tooth = tooth_view(paper)
        depth_a = smoother(t, 14.30, 14.62)
        out = paper.copy()
        if depth_a < 1:
            # --- LINE: strokes draw themselves on the count
            T = cam.sample(self.T, interp=cv2.INTER_NEAREST)
            L = cam.sample(W.line)
            vis = np.clip((t - T) / 0.16, 0, 1)
            line_a = L * vis
            # blue construction pencil: horizon, centre, the circle guide, a cross on the mark
            guide = np.zeros((H_OUT, W_OUT), np.float32)
            g_a = smooth(t, 5.4, 6.2) * (1 - smooth(t, 11.0, 13.2))
            if g_a > 0:
                ang = np.linspace(np.pi * 1.06, np.pi * 1.94, 200)
                pts = [to_screen(M, W.cx + W.r * np.cos(a) * 1.004, W.cy + W.r * np.sin(a) * 1.004) for a in ang]
                k = int(len(pts) * ease_out(t, 5.4, 6.3))
                if k > 1:
                    pencil_stroke(guide, pts[:k], width=1.1, jitter=0.5, seed=3)
                for (a, b) in [((0, 1700), (3072, 1700)), ((1536, 200), (1536, 1900))]:
                    pa, pb = to_screen(M, *a), to_screen(M, *b)
                    kk = ease_out(t, 5.6, 6.6)
                    pencil_stroke(guide, [pa, (mix(pa[0], pb[0], kk), mix(pa[1], pb[1], kk))], width=0.9)
                mx, my = to_screen(M, *KV1_MARK)
                s = 26
                pencil_stroke(guide, [(mx - s, my), (mx + s, my)], width=0.9)
                pencil_stroke(guide, [(mx, my - s), (mx, my + s)], width=0.9)
                out = graphite(out, guide * g_a * 0.55, dim.BLUE_PENCIL, tooth, strength=0.8)
            # graphite rim stroke on "3"
            rim = np.zeros((H_OUT, W_OUT), np.float32)
            k_r = ease_out(t, 5.7, 6.45)
            if k_r > 0:
                ang = np.linspace(np.pi * 1.0, np.pi * 2.0, 320)
                pts = [to_screen(M, W.cx + W.r * np.cos(a), W.cy + W.r * np.sin(a)) for a in ang]
                k = max(2, int(len(pts) * k_r))
                pr = np.ones(len(pts)) * 0.9
                pencil_stroke(rim, pts[:k], width=1.8, pressure=pr, jitter=0.35, seed=9)
            line_all = np.maximum(line_a, rim * (1 - smooth(t, 8.0, 10.5)))
            out = graphite(out, line_all, dim.GRAPHITE, tooth, strength=0.82)
            # --- the first mark (ink, before colour)
            mx, my = to_screen(M, *KV1_MARK)
            mark = np.zeros((H_OUT, W_OUT, 3), np.float32)
            sc = np.hypot(M[0, 0], M[1, 0])
            fx.splat(mark, mx, my, max(1.2, 5.0 / sc), (1, 1, 1), 1.0)
            ma = np.clip(lum(mark) * 2.2, 0, 1)[:, :, None] * smooth(t, 2.0, 3.2)
            out = out * (1 - ma) + np.array([0.80, 0.42, 0.14]) * ma
            # --- FLAT: the night bleeds into the paper from the mark outward (a wash, wet edge first)
            TT = cam.sample(self.wash_T)
            if t > 9.0:
                F = cam.sample(W.flat)
                lw = mix(0.75, 0.45, smooth(t, 11, 13.5))
                out = wash_over(out, F, L, TT, t, tooth, lw)
                out = out * (1 - ma) + np.array([0.86, 0.52, 0.20]) * ma
        if depth_a > 0:
            D = cam.sample_depth(W.img, W.depth, k_far=0.93, k_near=1.0, d_far=0.25, d_near=0.95)
            emis = cam.sample(W.LM)
            ign = smooth(t, 14.3, 15.2)
            D = fx.stamp_lights(D, emis, 0.25 * ign)
            out = mix(out, D, depth_a)
        # --- light layer (stars, rising traces, the mark's glow)
        lightbuf = np.zeros((H_OUT, W_OUT, 3), np.float32)
        if depth_a > 0:
            twinkle(lightbuf, M, W.stars, t, amt=depth_a)
            ca = cam.sample(W.ca)
            for tr in self.traces:
                u = (t - tr['t']) / tr['dur']
                if u <= 0 or u >= 1:
                    continue
                e = u * u * (3 - 2 * u) * 0.6 + u * 0.4
                (x0, y0), (x1, y1), (x2, y2) = tr['o'], tr['ctrl'], tr['end']
                x = (1 - e) ** 2 * x0 + 2 * (1 - e) * e * x1 + e * e * x2
                y = (1 - e) ** 2 * y0 + 2 * (1 - e) * e * y1 + e * e * y2
                # small sway: a light drifting in air, not a projectile
                x += 14 * np.sin(t * 1.3 + tr['seed'])
                sx, sy = to_screen(M, x, y)
                near = smooth(u, 0.0, 0.7)
                size = 0.9 + 1.0 * near
                inten = smooth(u, 0.0, 0.08) * (1 - smooth(u, 0.75, 1.0)) * 1.1
                if 0 <= int(sy) < H_OUT and 0 <= int(sx) < W_OUT:
                    occ = ca[int(sy), int(sx)] * (1 - near)
                    inten *= (1 - occ)
                fx.point_light(lightbuf, sx, sy, size=size * 1.25, intensity=inten * 1.3)
                # lift-off: the city flares as the trace leaves it (the city keeps its light)
                if u < 0.12:
                    ox, oy = to_screen(M, *tr['o'])
                    fx.point_light(lightbuf, ox, oy, size=1.4, intensity=1.2 * np.sin(u / 0.12 * np.pi))
                # a short fading tail along the path reads the trajectory
                for j in range(1, 12):
                    uu = u - j * 0.02
                    if uu <= 0:
                        break
                    ee = uu * uu * (3 - 2 * uu) * 0.6 + uu * 0.4
                    xx = (1 - ee) ** 2 * x0 + 2 * (1 - ee) * ee * x1 + ee * ee * x2 + 14 * np.sin((t - j * 0.07) * 1.3 + tr['seed'])
                    yy = (1 - ee) ** 2 * y0 + 2 * (1 - ee) * ee * y1 + ee * ee * y2
                    tx, ty = to_screen(M, xx, yy)
                    fx.splat(lightbuf, tx, ty, 0.8 * size, fx.AMBER, inten * 0.30 * (1 - j / 12) ** 1.5)
        out = out + lightbuf
        emis_glow = None
        if depth_a > 0:
            e = cam.sample(W.LM) * depth_a * smooth(t, 14.3, 15.4)
            emis_glow = np.clip(e * 1.4 + lum(lightbuf) * 2.0, 0, 1)
        expo = smoother(t, 1.2, 3.6)
        vig = mix(0.16, 0.26, depth_a)
        img = fx.finish(out, t, glow=emis_glow is not None, emis=emis_glow, glow_strength=1.1, vig=vig,
                        diff=mix(0.04, 0.10, depth_a), ca=mix(0.0, 0.6, depth_a), grain_amt=0.014)
        return img * expo



# =====================================================================================
import pickle


class S02(Shot):
    """Windows of lives rise out of the city: fragments, translated, compressed.
    war / lullaby / last goodbye happen to three windows. A watches them go up."""
    t0, t1 = 18.0, 25.2
    WAR = (884, 612)
    CHILD = (927, 302)
    COUPLE = (707, 442)
    COMPRESS = [((396, 0), 19.5), ((747, 159), 20.25), ((634, 204), 20.0), ((577, 197), 20.6), ((586, 168), 19.8)]

    def setup(self):
        self.P = Plate('KV2')
        self.bg = cached(('kv2clean',), lambda: np.load(work('derived', 'KV2_windows_clean.npy')).astype(np.float32))
        self.depth = gblur(self.P.depth, 3)
        with open(work('derived', 'KV2_sprites.pkl'), 'rb') as f:
            sp = pickle.load(f)
        self.sprites = []
        rng = np.random.default_rng(12)
        for s_ in sp:
            d = dict(s_)
            d['rgb'] = d['rgb'].astype(np.float32)
            d['core'] = d['core'].astype(np.float32)
            d['glow'] = d['glow'].astype(np.float32)
            bx, by, bw, bh = d['box']
            d['c'] = (bx + bw / 2 - d['x'], by + bh / 2 - d['y'])  # anchor in sprite coords
            d['p0'] = (bx + bw / 2, by + bh / 2)
            d['ph'] = rng.random() * 6.28
            d['v'] = 2.0 + rng.random() * 3.0 + (1 - by / 700) * 9.0  # px/s upward: barely moving low, lifting higher up
            d['key'] = (bx, by)
            self.sprites.append(d)
        # spawn pool: medium windows that will rise out of the city
        pool = [d for d in self.sprites if 700 < d['area'] < 2600 and d['box'][2] > 16]
        self.spawns = []
        for i, (ts, x, y) in enumerate([(18.3, 1060, 960), (19.4, 1010, 905), (20.6, 1090, 930), (21.7, 1030, 985), (22.9, 1075, 900), (24.0, 1000, 950)]):
            self.spawns.append(dict(t=ts, src=pool[(i * 2) % len(pool)], x=x, y=y, seed=i))
        self.compress = {k: t for k, t in self.COMPRESS}

    def cam(self, t):
        keys = [(18.0, dict(cx=1330.0, cy=860.0, zoom=1.10)),
                (20.8, dict(cx=1250.0, cy=800.0, zoom=1.22)),
                (23.4, dict(cx=1080.0, cy=640.0, zoom=1.48)),
                (25.2, dict(cx=960.0, cy=430.0, zoom=1.62))]
        p = lerp_cam(t, keys)
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1330.0, 860.0))

    def window_gain(self, d, t):
        k = d['key']
        g = 1.0
        tint = None
        if k == self.WAR:
            # firelight flicker: irregular, red-orange
            a = smooth(t, 21.4, 21.6) * (1 - smooth(t, 22.6, 23.2))
            n = 0.6 + 0.4 * np.sin(t * 23.0) * np.sin(t * 7.3 + 1) + 0.25 * np.sin(t * 41.0)
            g = mix(1.0, 0.7 + 0.9 * max(0, n), a)
            tint = mix(np.ones(3), np.array([1.25, 0.55, 0.32]), a)
        elif k == self.CHILD:
            # lullaby: the light lowers to a night-light and stays
            a = smoother(t, 22.7, 23.7)
            g = mix(1.0, 0.42, a)
            tint = mix(np.ones(3), np.array([1.1, 0.82, 0.6]), a)
        elif k == self.COUPLE:
            # last goodbye: one flicker, then it goes out
            dip = np.exp(-((t - 23.85) / 0.06) ** 2) * 0.6
            out = smoother(t, 24.15, 25.0)
            g = (1 - dip) * mix(1.0, 0.16, out)
            # an unlit window is dark glass catching the night, not a hole
            tint = mix(np.ones(3), np.array([0.55, 0.75, 1.35]), out)
        return g, tint

    def render(self, t):
        cam = self.cam(t)
        M_bg = cam.matrix(0.9)
        out = cam.sample_depth(self.bg, self.depth, k_far=0.9, k_near=1.0, d_far=0.3, d_near=0.75)
        M = cam.matrix(0.93)
        canvas = out
        lights = np.zeros_like(out)
        dt = t - self.t0
        for d in self.sprites:
            lift = d['v'] * dt + 0.35 * (1 - d['p0'][1] / 700) * dt * dt
            sway = 3.0 * np.sin(t * 0.7 + d['ph'])
            pos = (d['p0'][0] + sway - lift * 0.12, d['p0'][1] - lift)
            scale = 1.0 - 0.0006 * lift
            sx = 1.0
            g, tint = self.window_gain(d, t)
            tc = self.compress.get(d['key'])
            if tc is not None:
                u = clamp01((t - tc) / 0.7)
                sx = max(0.0, 1 - u * u * (3 - 2 * u))
                g = g * (1 + 0.8 * u)  # the light concentrates as it folds
                if u > 0:
                    # the window has folded flat: it is now a point of light that keeps rising
                    sxp, syp = to_screen(M, pos[0], pos[1] - 40 * u)
                    fx.point_light(lights, sxp, syp, size=1.1, intensity=smooth(u, 0.5, 1.0) * 1.2)
                if sx <= 0.01:
                    continue
            A = sprite_affine(M, pos, scale, sx=sx, rot=0.02 * np.sin(t * 0.5 + d['ph']), anchor=d['c'])
            blit(canvas, d['rgb'], d['core'], A, add=d['glow'], tint=tint, gain=g, opacity=min(1.0, sx * 3))
        for sp in self.spawns:
            u = t - sp['t']
            if u < 0:
                continue
            src = sp['src']
            rise = 70 * u + 9 * u * u
            pos = (sp['x'] - 0.2 * rise + 10 * np.sin(u * 0.8 + sp['seed']), sp['y'] - rise)
            scale = max(0.25, 0.75 - 0.0009 * rise)
            op = smooth(u, 0.0, 0.8)
            A = sprite_affine(M, pos, scale, anchor=src['c'])
            blit(canvas, src['rgb'], src['core'], A, add=src['glow'], opacity=op)
            # the city light it came from flares as it leaves
            if u < 0.6:
                ox, oy = to_screen(M, sp['x'], sp['y'] + 30)
                fx.point_light(lights, ox, oy, size=1.2, intensity=np.sin(u / 0.6 * np.pi) * 0.9)
        out = canvas + lights
        emis = np.clip(smoothstep(0.42, 0.75, lum(out)) * 0.8 + lum(lights) * 2, 0, 1)
        return fx.finish(out, t, emis=emis, glow_strength=0.9, vig=0.28, diff=0.10)


# =====================================================================================
import json
TIMING = json.load(open(os.path.join(SCRATCH, 'audio', 'timing.json')))
BEATS = np.array(TIMING['beats'])


def beats_between(a, b):
    return [float(x) for x in BEATS if a <= x < b]


class KV3World:
    def __init__(self, name='KV3'):
        self.P = Plate(name)
        self.name = name
        ld = lambda k: np.load(work('derived', f'{name}_{k}.npy')).astype(np.float32)
        self.sky = cached((name, 'sky'), lambda: ld('sky_clean'))
        self.pts = cached((name, 'pts'), lambda: ld('const_points'))
        self.lines = cached((name, 'lines'), lambda: ld('const_lines'))
        self.depth = gblur(Plate('KV3').depth, 3)
        self.ca = Plate('KV3').char_alpha


class S03(Shot):
    """The compressed lights arrive as points; luminous lines join them: constellations in a
    mind with no sky. Tilt down to the witnesses and the city the stars repeat."""
    t0, t1 = 25.2, 28.85

    def setup(self):
        self.W = KV3World('KV3')
        h, w = self.W.sky.shape[:2]
        pl = lum(self.W.pts)
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        noise = fbm_field(h // 4, w // 4, 20, 3, 2)
        noise = cv2.resize(noise, (w, h))
        # points arrive left -> right (where S02's lights were), with scatter
        self.Tp = 25.30 + 1.4 * np.clip((xs - 500) / 2000, 0, 1) + 0.35 * noise
        p = work('derived', 'S03_lineT.npy')
        if os.path.exists(p):
            self.Tl = np.load(p).astype(np.float32)
        else:
            ll = np.clip(lum(self.W.lines) * 6, 0, 1)
            a = dim.stroke_order(ll, seed=5, origin=(560, 330), speed=700, spread=1.2)
            v = a[a < 1e5]
            lo, hi = np.percentile(v, 1), np.percentile(v, 99)
            self.Tl = (25.9 + np.clip((a - lo) / (hi - lo), 0, 1.1) * 2.4).astype(np.float32)
            self.Tl[a > 1e5] = 99
            self.Tl = cv2.dilate(-self.Tl, np.ones((3, 3), np.uint8)) * -1
            np.save(p, self.Tl.astype(np.float16))

    def cam(self, t):
        keys = [(25.2, dict(cx=1560.0, cy=540.0, zoom=1.34)),
                (26.4, dict(cx=1560.0, cy=580.0, zoom=1.32)),
                (28.85, dict(cx=1536.0, cy=1160.0, zoom=1.04))]
        p = lerp_cam(t, keys)
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1536.0, 1160.0))

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        base = cam.sample_depth(W.sky, W.depth, k_far=0.92, k_near=1.0, d_far=0.3, d_near=0.8)
        M = cam.matrix(0.92)
        Tp = cam.sample(self.Tp)
        pts = cam.sample(W.pts)
        u = (t - Tp) / 0.18
        pa = np.clip(u, 0, 1) * (1 + 0.8 * np.exp(-((u - 1.2) / 0.6) ** 2) * (u > 0))
        Tl = cam.sample(self.Tl, interp=cv2.INTER_NEAREST)
        lines = cam.sample(W.lines)
        la = np.clip((t - Tl) / 0.12, 0, 1)
        emis = pts * pa[:, :, None] + lines * la[:, :, None] * 1.25
        out = base + emis
        e = np.clip(lum(emis) * 3, 0, 1)
        e = np.maximum(e, cam.sample(Plate('KV3').lights) * 0.7)
        return fx.finish(out, t, emis=e, glow_strength=1.0, vig=0.28, diff=0.10)


# =====================================================================================
class KV4World:
    def __init__(self):
        self.P = Plate('KV4')
        P = self.P
        self.img = P.img
        self.bg = cached(('kv4band',), lambda: np.load(work('derived', 'KV4_bandclean.npy')).astype(np.float32))
        # B is solid right of her silhouette edge; the soft matte only matters for the strands
        m = P.char_alpha
        solid = (m > 0.55).astype(np.uint8)
        solid = np.maximum.accumulate(solid, axis=1)
        solid = cv2.erode(solid, np.ones((1, 41), np.uint8)).astype(np.float32)
        self.ca = np.maximum(m, gblur(solid, 3))
        self.depth = gblur(P.depth, 4)
        # city light layer (top-hat) so lights can be switched
        def make_lights():
            city = np.zeros(self.ca.shape, np.float32)
            city[1000:] = 1
            city *= (1 - cv2.dilate((self.ca > 0.05).astype(np.uint8), np.ones((9, 9), np.uint8)))
            op = cv2.morphologyEx(self.bg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
            th = np.clip(self.bg - op, 0, 1)
            th = th * smoothstep(0.05, 0.12, lum(th))[:, :, None] * city[:, :, None]
            return th
        p = work('derived', 'KV4_citylights.npy')
        if os.path.exists(p):
            self.lights = np.load(p).astype(np.float32)
        else:
            self.lights = make_lights()
            np.save(p, self.lights.astype(np.float16))
        self.dark = np.clip(self.bg - self.lights, 0, 1)
        # light components (for per-window control)
        lm = (lum(self.lights) > 0.06).astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(lm, 8)
        self.lab = lab
        self.cen = cen
        self.n = n
        # hair weight for sway
        hsv = cv2.cvtColor((self.img * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
        hue = hsv[:, :, 0] * 2
        hairm = ((hue > 4) & (hue < 34) & (hsv[:, :, 1] > 80)).astype(np.float32) * P.char_alpha
        ys = np.arange(hairm.shape[0], dtype=np.float32)[:, None]
        xs = np.arange(hairm.shape[1], dtype=np.float32)[None, :]
        wy = np.clip((ys - 900) / 900, 0, 1) ** 1.3
        wx = np.clip((2300 - xs) / 900, 0, 1) ** 0.7  # strands in front of the face, hanging over the city
        self.hair_w = gblur(hairm * wy * wx, 6)

    def face(self, s):
        """B's face with the upper lid lowered by s (0 = as painted, 0.4 = lowered gaze)."""
        import lids
        return lids.lid_warp(self.img, s)


_kv4 = {}


def kv4():
    if 'w' not in _kv4:
        _kv4['w'] = KV4World()
    return _kv4['w']


TRAIN_PATH = [(640, 1640), (700, 1630), (850, 1612), (1000, 1618), (1080, 1675), (1200, 1700), (1320, 1716), (1460, 1748), (1560, 1770)]


def path_point(path, u):
    p = np.asarray(path, np.float32)
    seg = np.hypot(*np.diff(p, axis=0).T)
    L = np.concatenate([[0], np.cumsum(seg)])
    d = np.clip(u, 0, 1) * L[-1]
    i = int(np.clip(np.searchsorted(L, d) - 1, 0, len(seg) - 1))
    f = (d - L[i]) / (seg[i] + 1e-6)
    return p[i] + (p[i + 1] - p[i]) * f


def render_b_layer(W, cam, t, eye_s, sway_amp=4.0, gust=1.0):
    """B (KV4) as a layer: eyes state + hair breathing on twos."""
    face = W.face(eye_s)
    tt = on_twos(t)
    x0, y0, x1, y1 = 1000, 600, 2400, 2048
    roi_w = W.hair_w[y0:y1, x0:x1]
    dx, dy = sway_field(roi_w.shape, roi_w, tt, amp=sway_amp, freq=0.22, wavelen=700, axis_pt=(1300, 0), gust=gust)
    rgb = face.copy()
    a = W.ca.copy()
    rgb[y0:y1, x0:x1] = apply_disp(face[y0:y1, x0:x1], dx, dy)
    a[y0:y1, x0:x1] = apply_disp(W.ca[y0:y1, x0:x1], dx, dy)
    return cam.sample(rgb), cam.sample(a)


class S04(Shot):
    """B and the city: depth (parallax), time (a train), heat (warm bounce), hearts learning
    to beat (windows on the kick). Her eyes lower to one window. Then time rewinds."""
    t0, t1 = 28.85, 36.10
    REWIND = 35.0

    def setup(self):
        self.W = kv4()
        W = self.W
        # the beat windows: near-left blocks, switched on floor by floor
        sel = [i for i in range(1, W.n) if 90 < W.cen[i][0] < 500 and 1660 < W.cen[i][1] < 1890]
        sel.sort(key=lambda i: -W.cen[i][1])
        beats = beats_between(32.45, 34.9)
        self.beat_on = np.full(W.n, -1.0, np.float32)
        for k, i in enumerate(sel):
            self.beat_on[i] = beats[min(len(beats) - 1, k // 3)] if beats else 33.0
        # rewind order: far lights go first, the nearest last
        rng = np.random.default_rng(3)
        cy = W.cen[:, 1]
        self.off_t = (self.REWIND + 0.05 + 0.85 * np.clip((cy - 1000) / 1000, 0, 1) + rng.random(W.n) * 0.15).astype(np.float32)
        self.off_t[0] = 99

    def cam(self, t):
        keys = [(28.85, dict(cx=1740.0, cy=905.0, zoom=1.09)),
                (36.10, dict(cx=1440.0, cy=925.0, zoom=1.12))]
        p = lerp_cam(t, keys)
        return Cam(p['cx'], p['cy'], p['zoom'], ref=(1740.0, 905.0))

    def light_gain(self, t):
        W = self.W
        g = np.ones(W.n, np.float32)
        on = self.beat_on
        m = on > 0
        g[m] = np.clip((t - on[m]) / 0.06, 0, 1)
        if t > self.REWIND:
            g *= np.clip(1 - (t - self.off_t) / 0.12, 0, 1)
        g[0] = 0
        return g

    def render(self, t):
        W = self.W
        cam = self.cam(t)
        g = self.light_gain(t)
        gmap = g[W.lab]
        lights = W.lights * gmap[:, :, None]
        bg_full = W.dark + lights
        bg = cam.sample_depth(bg_full, W.depth, k_far=0.62, k_near=0.86, d_far=0.25, d_near=0.6)
        eye_s = 0.36 * smoother(on_twos(t), 34.15, 34.5)
        brgb, ba = render_b_layer(W, cam, t, eye_s, sway_amp=4.0 + 3.0 * np.exp(-((t - 34.7) / 0.4) ** 2))
        # heat: warm bounce on her face rises on "heat", and leaves when time rewinds
        warm = 1 + 0.10 * smooth(t, 31.9, 32.6) * (1 - smooth(t, self.REWIND, self.REWIND + 1.0))
        cool = smooth(t, self.REWIND + 0.2, self.REWIND + 1.1)
        brgb = brgb * np.array([warm, 1.0, 1.0 / warm])
        brgb = mix(brgb, brgb * np.array([0.78, 0.86, 1.08]), cool * 0.8)
        out = over(bg, brgb, ba)
        # the train: a pair of warm-white lights with a short trail (time)
        lb = np.zeros_like(out)
        M = cam.matrix(0.82)
        if t < self.REWIND:
            u = (t - 30.3) / 5.8
        else:
            u = (self.REWIND - 30.3) / 5.8 - ((t - self.REWIND) / 1.1) ** 2 * 0.8
        if 0 < u < 1:
            for j in range(8):
                pu = u - j * 0.006 * (1 if t < self.REWIND else -1)
                x, y = path_point(TRAIN_PATH, pu)
                sx, sy = to_screen(M, x, y)
                fx.point_light(lb, sx, sy, size=0.7 if j else 0.9, color=(1.0, 0.86, 0.62), intensity=(1.2 if j == 0 else 0.35 * (1 - j / 8)))
        out = out + lb * (1 - ba[:, :, None])
        emis = np.clip(lum(cam.sample(lights)) * 4 + lum(lb) * 2, 0, 1) * (1 - ba)
        return fx.finish(out, t, emis=emis, glow_strength=0.9, vig=0.26, diff=0.11)

SHOTS = {'S01': S01, 'S02': S02, 'S03': S03, 'S04': S04}
