"""v9: render the original project's (rev1, loading/src) shots S07-S47 (43.25-213.4 s) into the v9 frame set.

Changes against rev1, applied here so rev1's own code stays reproducible:
  - clean finish: no diffusion (a 14 px blur screened in at 5-12%), no chromatic aberration (0.4-0.6 px), no grain,
    no paper-tooth overlay; vignette at 40% of rev1's. Bloom stays (it comes only from the emissive lights).
  - camera zoom on the plates is capped at ZMAX = 1.3 (= the 1536-px approved original at about 1.08x on a 1280 frame;
    rev1 went to 2.75 in S17); where the cap applies, the frame centre is kept inside the plate. S12 keeps its push into
    the painting (that shot is about where the picture ends).
  - colour washes arrive with a softer edge (soak 0.07 -> 0.22 s, wet-edge pooling 0.28 -> 0.12), so they read as paint
    coming in, not as torn paper.
  - one resample: rev1 renders 1920x1080 float; this downscales once to 1280x720 (Lanczos-3 + anti-ringing, as the
    opening) and writes PNG.
  python3 rev1_bridge.py OUTDIR S07 S09 ... [--frames a-b] [--step n] [--jobs 4]"""
import os, sys, time
os.environ['LOADING_V9'] = '1'
REV1 = '/home/user/OC/loading/src'
sys.path.insert(0, REV1)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
import multiprocessing as mp

ZMAX = 1.3
NOCLAMP = {'S12'}
# wash soak per shot, in seconds of the shot's own arrival map: where the wash front crosses the frame slowly
# (S42 3.4 s, S46/S47 12 s per unit of distance) a 0.22 s soak left a hard, ragged dark blob on white paper
S07_SHIFT = (185.0, 126.0)
SOAK = {'S42': 0.40, 'S46': 0.9, 'S47': 0.9}
_CUR = {'shot': None}


def _patch():
    import fx, engine, shots_a
    f0 = fx.finish

    def finish(img, t, glow=True, emis=None, glow_strength=0.9, grain_amt=0.016, vig=0.26, diff=0.10, ca=0.6, tooth=True):
        return f0(img, t, glow=glow, emis=emis, glow_strength=glow_strength, grain_amt=0.0, vig=vig * 0.4, diff=0.0, ca=0.0, tooth=False)
    fx.finish = finish
    c0 = engine.Cam.__init__

    def cam_init(self, cx, cy, zoom=1.0, *a, **k):
        capped = _CUR['shot'] not in NOCLAMP and zoom > ZMAX
        if capped:
            # a wider view at rev1's off-centre framing can run past the plate (S15: up to 84 plate px past the right edge),
            # where BORDER_REFLECT draws a mirrored kink into the Earth's limb. Keep the frame - and its parallax reference,
            # which every layer's centre lies between - inside the 3072 x 2048 plate.
            zoom = ZMAX
            hw, hh = 1536.0 / zoom * 1.02, 864.0 / zoom * 1.02
            cx, cy = float(np.clip(cx, hw, 3072 - hw)), float(np.clip(cy, hh, 2048 - hh))
            if k.get('ref') is not None:
                k['ref'] = (float(np.clip(k['ref'][0], hw, 3072 - hw)), float(np.clip(k['ref'][1], hh, 2048 - hh)))
        c0(self, cx, cy, zoom, *a, **k)
    engine.Cam.__init__ = cam_init
    w0 = shots_a.wash_over

    def wash_over(paper_img, flat, line, T, t, tooth, line_w=0.6, soak=0.07):
        dt = t - T
        soak = max(soak, SOAK.get(_CUR['shot'], 0.22))
        a = shots_a.smoothstep(0.0, soak, dt)
        pre = shots_a.smoothstep(-0.30, 0.0, dt) * (1 - a)
        wet = np.exp(-((dt - soak * 0.8) / (soak * 0.9)) ** 2) * a
        base = paper_img * (1 - 0.10 * pre[:, :, None]) + np.array([0.55, 0.58, 0.66]) * 0.10 * pre[:, :, None]
        col = flat * (1 - line_w * line[:, :, None]) * (0.92 + 0.08 * tooth[:, :, None])
        col = col * (1 - 0.12 * min(1.0, 0.3 / soak) * wet[:, :, None])
        return shots_a.over(base, col, a)
    shots_a.wash_over = wash_over
    # S12: rev1 pushed 14x into the painting, then showed its pixels (nearest-neighbour blocks) and random-noise fog.
    # v9: a gentler push (to 3.2x) while the paint thins, defocused, into the paper it is painted on: long fibres and
    # tooth, procedural and sharp at this scale (the edge of what's known is the sheet itself). No pixel blocks, no noise.
    import shots_b, shots_c
    from common import W_OUT, H_OUT

    def s12_render(self, t):
        u = shots_b.smoother(t, self.t0, self.t1)
        zoom = float(np.exp(np.log(1.05) + (np.log(3.2) - np.log(1.05)) * (u ** 1.3)))
        cx = shots_b.mix(1536.0, self.EYE[0], shots_b.smooth(t, self.t0, self.t0 + 2.2))
        cy = shots_b.mix(1150.0, self.EYE[1], shots_b.smooth(t, self.t0, self.t0 + 2.2))
        M = shots_b.cam_matrix(cx, cy, zoom, 0.12 * u ** 2)
        out = shots_b.affine_sample(self.img, M)
        k = shots_b.smooth(t, 61.0, 62.9)
        if k > 0:
            if not hasattr(self, '_fib'):
                rng = np.random.default_rng(12)
                fib = np.zeros((H_OUT, W_OUT), np.float32)
                for _ in range(1400):
                    x, y = rng.uniform(0, W_OUT), rng.uniform(0, H_OUT)
                    L, a = rng.uniform(60, 320), rng.uniform(0, np.pi)
                    cv2.line(fib, (int(x), int(y)), (int(x + L * np.cos(a)), int(y + L * np.sin(a))), float(rng.uniform(-1, 1)),
                             int(rng.integers(1, 3)), cv2.LINE_AA)
                fib = cv2.GaussianBlur(fib, (0, 0), 1.1)
                blot = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (H_OUT // 16, W_OUT // 16)).astype(np.float32), (0, 0), 3), (W_OUT, H_OUT))
                self._fib = 1 + 0.10 * fib + 0.05 * blot
            tone = np.array([0.30, 0.34, 0.46], np.float32) * 1.05                 # the night paint's own tone, thinned
            paper = tone[None, None, :] * self._fib[..., None]
            soft = cv2.GaussianBlur(out, (0, 0), 1 + 9 * k)
            out = out * (1 - k) + (soft * 0.35 + paper * 0.65) * k
        return fx.finish(out, t, glow=False, vig=0.25, diff=0.0, ca=0.0)
    shots_b.S12.render = s12_render
    # S13/S22: the unrender front followed 5-octave noise down to 4-plate-px detail (a ragged, torn line); keep the
    # large shape, drop the fine raggedness
    for cls in (shots_b.S13, shots_c.S22):
        def setup(self, _s0=cls.setup):
            _s0(self)
            self.U = cv2.GaussianBlur(self.U, (0, 0), 14)
        cls.setup = setup
    # S14: the painting's edge was distance-to-border + 300 px of 5-octave noise: a torn-paper silhouette. Now a
    # brushed vignette: only the large waves of the same noise (blurred), 120 px, no fine octave
    from shots_a import fbm_field

    def s14_setup(self, _s0=shots_b.S14.setup):
        _s0(self)
        h, w = self.W.img.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        de = np.minimum(np.minimum(xs, w - 1 - xs), np.minimum(ys, h - 1 - ys))
        n = cv2.GaussianBlur(cv2.resize(fbm_field(h // 4, w // 4, 70, 9, 5), (w, h)), (0, 0), 40)
        n = (n - n.mean()) / (n.std() + 1e-6)
        self.edge = de + n * 45
    shots_b.S14.setup = s14_setup
    # S19: the card was shaded 0.10-0.65 of a mid paper texture: a flat grey quad. Lift it to read as white paper
    # catching earthlight (the shading model is rev1's; only the paper's albedo changes)
    def s19_setup(self, _s0=shots_c.S19.setup):
        _s0(self)
        self.paper = np.clip(self.paper * 1.55 + 0.05, 0, 1.2)
    shots_c.S19.setup = s19_setup
    # S07 (cut from v9's hill close-up at 43.25 s): rev1 framed the first fire about 94 px right of and 64 px below where
    # v9's last frame has it. Start the camera offset so the fire lands in the same place across the cut (a match cut on
    # the light), then glide into rev1's own move by 45.0 s. Offset in plate px (0.508 screen px per plate px at zoom 1.22).
    c07 = shots_b.S07.cam

    def s07_cam(self, t, _c=c07):
        p = dict(_c(self, t))
        w = 1.0 - shots_b.smoother(t, 43.25, 45.0)
        p['cx'] += S07_SHIFT[0] * w
        p['cy'] += S07_SHIFT[1] * w
        return p
    shots_b.S07.cam = s07_cam
    for m in ('shots_b', 'shots_c', 'shots_d', 'shots_e', 'shots_f'):        # modules that imported the names directly
        mod = __import__(m)
        if hasattr(mod, 'wash_over'):
            mod.wash_over = wash_over
        if hasattr(mod, 'Cam'):
            pass                                                              # same class object: patched in place


_shots = {}


def _init():
    os.chdir(REV1)
    sys.path.insert(0, REV1)
    cv2.setNumThreads(1)
    _patch()


def _frame(args):
    name, f, out = args
    import render as R
    import opening_ink as OI
    _CUR['shot'] = name
    if name not in _shots:
        s = R.registry()[name]()
        s.setup()
        _shots[name] = s
    img = np.clip(_shots[name].render(f / 24.0), 0, 1).astype(np.float32)[:, :, ::-1]   # RGB -> BGR
    small = OI.aa_resize(np.ascontiguousarray(img * 255.0), 1280 / 1920.0, 1280, 720)
    cv2.imwrite(os.path.join(out, 'f%04d.png' % f), np.clip(np.round(small), 0, 255).astype(np.uint8))
    return f


def frames_of(name, a=None, b=None):
    sys.path.insert(0, REV1)
    os.chdir(REV1)
    import render as R
    cls = R.registry()[name]
    f0, f1 = int(round(cls.t0 * 24)), int(round(cls.t1 * 24))
    if name == 'S07':
        f0 = 1038                                                            # v9's opening ends on frame 1037 (43.25 s)
    fr = list(range(f0, f1))
    if a is not None:
        fr = [f for f in fr if a <= f <= b]
    return fr


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    names = [a for a in sys.argv[2:] if a.startswith('S')]
    a = b = None
    if '--frames' in sys.argv:
        a, b = map(int, sys.argv[sys.argv.index('--frames') + 1].split('-'))
    step = int(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 1
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 4
    tasks = []
    for n in names:
        tasks += [(n, f, out) for f in frames_of(n, a, b)[::step]]
    t0 = time.time()
    with mp.get_context('spawn').Pool(jobs, initializer=_init) as pool:         # spawn: no OpenCV thread pool inherited across fork
        for k, _ in enumerate(pool.imap_unordered(_frame, tasks, chunksize=1)):
            if k % 100 == 0:
                print('rendered %d of %d (%.0fs)' % (k, len(tasks), time.time() - t0), flush=True)
    print('done %d frames in %.0fs' % (len(tasks), time.time() - t0))
