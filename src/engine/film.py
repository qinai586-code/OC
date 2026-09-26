"""Timeline and frame context.

A film is a list of Shots. A shot draws one native frame at any time t (frames are pure functions of t,
so any frame can be rendered in any order, in parallel). Shots draw in *view coordinates*: (0,0)-(320,180)
is what the camera sees at zoom 1; the canvas has a MARGIN on every side so the post stage can pan by
sub-pixel amounts, shake, zoom and tilt without revealing an edge.
"""
import math
import numpy as np
from .px import Canvas, W, H, rgb

MARGIN = 12
CW, CH = W + 2 * MARGIN, H + 2 * MARGIN
FPS = 60


class Frame:
    """What a shot's draw() receives."""

    def __init__(self, t, shot):
        self.t = t                    # global time (s)
        self.lt = t - shot.start      # local time (s)
        self.dur = shot.end - shot.start
        self.u = self.lt / self.dur if self.dur > 0 else 0   # 0..1 progress through the shot
        self.cv = Canvas(CW, CH, (0, 0, 0), ox=MARGIN, oy=MARGIN)
        # camera: centre of the screen in view coords, zoom (>=1 zooms in), rotation (radians)
        self.cam = dict(x=W / 2, y=H / 2, zoom=1.0, rot=0.0)
        self.shake = (0.0, 0.0)
        self.flash = 0.0              # 0..1 white (ordered-dither) flash in post
        self.fade = 0.0               # 0..1 to black (ordered dither) in post
        self.lyrics = True
        self.shot = shot

    # timing helpers ----------------------------------------------------
    def at(self, t_global):
        """Seconds since global time t_global (negative before)."""
        return self.t - t_global

    def since(self, t_global, dur=None):
        """0..1 progress of an event that starts at t_global and lasts dur (clamped)."""
        x = self.t - t_global
        if dur is None:
            return x
        return max(0.0, min(1.0, x / dur))

    def step(self, fps=12, t=None):
        """Quantised time for authored animation: which drawing (integer) at `fps` drawings/s."""
        return int(math.floor(((self.t if t is None else t)) * fps + 1e-6))

    def hold(self, fps=12):
        return math.floor(self.lt * fps + 1e-6) / fps


class Shot:
    def __init__(self, name, start, end, draw, transition='cut', tdur=0.0, lyrics=True):
        self.name, self.start, self.end, self.draw = name, start, end, draw
        self.transition, self.tdur, self.lyrics = transition, tdur, lyrics

    def render(self, t):
        f = Frame(t, self)
        f.lyrics = self.lyrics
        self.draw(f)
        return f


class Film:
    def __init__(self, shots, duration):
        self.shots = sorted(shots, key=lambda s: s.start)
        self.duration = duration
        for a, b in zip(self.shots, self.shots[1:]):
            a.end = b.start
        self.shots[-1].end = duration

    def shot_at(self, t):
        for i, s in enumerate(self.shots):
            if s.start <= t < s.end:
                return i, s
        return len(self.shots) - 1, self.shots[-1]

    def frame(self, t):
        """Render the native frame at t -> (rgb canvas CH x CW x 3, post params)."""
        i, s = self.shot_at(t)
        f = s.render(t)
        img = np.array(f.cv.im)[..., :3]
        # incoming transitions
        if s.transition != 'cut' and i > 0 and t - s.start < s.tdur:
            k = (t - s.start) / s.tdur
            prev = self.shots[i - 1]
            if s.transition == 'dither':
                pf = prev.render(t)
                pimg = np.array(pf.cv.im)[..., :3]
                from .px import dither_mask
                m = dither_mask(CW, CH, k)
                img = np.where(m[..., None], img, pimg)
            elif s.transition == 'flash':
                f.flash = max(f.flash, 1.0 - k)
            elif s.transition == 'black':
                f.fade = max(f.fade, 1.0 - k)
            elif s.transition == 'wipe':
                pf = prev.render(t)
                pimg = np.array(pf.cv.im)[..., :3]
                x = int(CW * k)
                img = img.copy()
                img[:, x:] = pimg[:, x:]
        post = dict(cam=f.cam, shake=f.shake, flash=f.flash, fade=f.fade, lyrics=f.lyrics, shot=s.name)
        return img, post
