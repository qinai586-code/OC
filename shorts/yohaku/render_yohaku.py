#!/usr/bin/env python3
"""Renders the Yohaku short: 1080x1920, 60 fps, muxed with audio/yohaku_cut.wav.

The only character art is the user's OC sheet (reference/oc_yohaku_design.webp). It is animated with continuous
warp deformers whose soft weights overlap (Live2D-style mesh warping) plus spring-driven secondary motion, so no
part is ever a rigid cutout. The paper-and-watercolour world and all effects are procedural.
Every frame is a pure function of t; keys are musical cues ("bar:beat+frames") from build_motion.t_of.

  python3 render_yohaku.py                  # full render -> render/yohaku.mp4
  python3 render_yohaku.py --sheet 1,4.5,8  # contact sheet of those clip seconds -> render/sheet.jpg
"""
import math, os, subprocess, sys
import numpy as np, cv2
from multiprocessing import Pool
from build_motion import t_of

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, '..', '..', 'reference', 'oc_yohaku_design.webp')
AUDIO = os.path.join(HERE, 'audio', 'yohaku_cut.wav')
OUT = os.path.join(HERE, 'render')
W, H, FPS, DUR = 1080, 1920, 60, 27.355
CUT = t_of('5:1')
P, STEP = 160, 4                       # canvas pad around the art; coarse warp-grid step
FEET, CH_H = (510., 1495.), 1435.      # ground contact (art px) and character height
cv2.setNumThreads(1)

def T(c):
    return c if isinstance(c, (int, float)) else (0.0 if c == '0' else t_of(c))

# ---------------------------------------------------------------- keys (render version of MOTION.md, in-place acting)
# screen-left = her right side. Angles in degrees, distances in art px.
K = {
 'bodyY':   [('0',0,'io'),('3:4',14,'o'),('3:4+10',0,'back'),('5:1-2',0,'io'),('5:1+7',150,'o'),('5:1+16',0,'i'),
             ('8:3',24,'o'),('8:3+8',0,'i'),('8:4',24,'o'),('8:4+8',0,'i'),('12:1+10',10,'io'),('12:3',0,'io')],
 'crouch':  [('0',0,'io'),('4:4+8',38,'io'),('5:1-3',40,'io'),('5:1-1',0,'o'),('5:1+16',0,'io'),('5:1+20',44,'o'),
             ('5:2+6',0,'back'),('5:3',16,'io'),('5:4',0,'io'),('7:4',22,'o'),('8:1',0,'back'),('10:2',10,'o'),('10:3',0,'io')],
 'squash':  [('0',0,'io'),('4:4+8',-.025,'io'),('5:1-1',.06,'o'),('5:1+7',.015,'io'),('5:1+15',.045,'io'),('5:1+19',-.06,'o'),
             ('5:2+6',0,'back'),('8:3',.03,'o'),('8:3+8',-.025,'io'),('8:3+14',0,'io'),('8:4',.03,'o'),('8:4+8',-.025,'io'),('8:4+14',0,'io')],
 'approach':[('0',1,'io'),('5:1',1,'io'),('5:1+16',1.04,'io'),('6:1',1.04,'io'),('7:2',1.1,'io'),('11:1',1.1,'io'),('11:3',1.14,'io'),
             ('12:1',1.11,'io'),('13:1',1.12,'io')],
 'bodyRoll':[('0',0,'io'),('1:4',1.5,'io'),('2:1',0,'io'),('5:3',-5,'o'),('5:3+10',4,'io'),('5:4',0,'back'),('7:2',2,'io'),
             ('7:4',0,'io'),('10:2',-2,'o'),('10:4',0,'io'),('11:3',2.5,'io'),('13:1',1,'io'),('14:1',-.5,'io')],
 'idle':    [('0',1,'io'),('3:1',.3,'io'),('4:4',0,'io'),('9:1',.5,'io'),('10:1',.3,'io'),('13:1',.6,'io')],
 'trot':    [('0',0,'io'),('6:1-8',0,'io'),('6:1',1,'io'),('7:1.5',1,'io'),('7:2',0,'io')],
 'rise':    [('0',.3,'io'),('1:4',.1,'io'),('4:4+10',.8,'io'),('5:1-1',0,'o'),('10:1+12',.1,'io'),('10:2',1,'o'),('10:3',.6,'io'),
             ('10:3.5',.9,'io'),('10:4',.3,'io'),('11:1',.1,'io')],
 'breathHz':[('0',.42,'io'),('2:4',.36,'io'),('4:4',.3,'io'),('6:1',.62,'io'),('8:4',.45,'io'),('9:1',.28,'io'),('11:1',.34,'io'),('13:1',.28,'io')],
 'breathPx':[('0',2.2,'io'),('4:4+10',3.5,'io'),('5:1',2,'o'),('6:1',3,'io'),('9:1',1.8,'io'),('13:1',2.2,'io')],
 'headRoll':[('0',0,'io'),('1:4',7,'io'),('2:1',2,'io'),('2:1+10',-4,'io'),('2:3',1,'io'),('3:2',-5,'io'),('4:2',6,'io'),('4:4',0,'io'),
             ('5:4',-7,'o'),('6:1',0,'io'),('7:2',12,'back'),('7:4',3,'io'),('8:2',-4,'io'),('9:1',8,'io'),('10:2',-10,'o'),('10:4',-4,'io'),
             ('11:3',9,'io'),('12:1',0,'io'),('13:1',6,'io'),('14:1',-4,'io'),('14:3',2,'io')],
 'headPitch':[('0',3,'io'),('1:1+6',10,'io'),('1:4',6,'io'),('2:1',2,'io'),('3:1',-6,'io'),('3:3',-3,'io'),('3:4',0,'o'),('4:1',4,'io'),
             ('4:3',12,'o'),('4:3+6',-2,'back'),('4:4',0,'io'),('7:1',-4,'io'),('8:1',3,'io'),('9:1',6,'io'),('11:1',0,'io'),('12:1',-8,'io'),
             ('12:3',0,'io'),('13:1',1,'io')],
 'headYaw': [('0',.05,'io'),('2:1',-.9,'io'),('2:2.5',-.95,'io'),('2:3',.1,'o'),('2:4',.4,'io'),('2:4+6',-.3,'io'),('2:4+12',.3,'io'),
             ('2:4+18',0,'io'),('4:4',.3,'io'),('5:1',0,'cut'),('5:4',-.2,'io'),('6:1',0,'io'),('7:1',.5,'io'),('7:4',.2,'io'),('8:1',0,'io'),
             ('10:2',-.5,'o'),('10:4',0,'io')],
 'gazeX':   [('0',0,'io'),('2:1-6',-1,'o'),('2:3-4',.1,'o'),('3:1+8',.1,'io'),('4:4-6',.6,'o'),('5:1',0,'cut'),('7:1+4',.9,'o'),('7:3',.8,'io'),
             ('7:4',.3,'o'),('8:1',0,'io')],
 'gazeY':   [('0',.2,'io'),('1:1',.9,'o'),('1:4',.5,'io'),('2:1',.1,'io'),('3:1+8',-.9,'o'),('3:3',-.3,'io'),('3:3+14',.3,'io'),('4:1',.4,'io'),
             ('4:4-6',0,'o'),('7:1+4',.4,'o'),('7:4',-.4,'o'),('8:1',.2,'io'),('9:1',-.7,'io'),('9:3',.2,'io'),('9:4+10',.5,'io'),('10:1',0,'io'),
             ('12:1',-1,'io'),('12:3',0,'io')],
 'cross':   [('0',0,'io'),('3:3+8',0,'io'),('3:3+16',1,'o'),('4:1',.2,'io'),('4:1+10',0,'io')],
 'lid':     [('0',.92,'io'),('1:3',.78,'io'),('2:1',.92,'io'),('3:2',1,'io'),('3:3+16',.9,'io'),('3:4',1,'o'),('4:2',.8,'io'),('4:4',1,'io'),
             ('5:4',.85,'io'),('6:1',.95,'io'),('7:4',.7,'io'),('8:1',1,'io'),('9:1',.85,'io'),('10:1+12',.9,'io'),('10:2',0,'o'),
             ('10:3',.25,'io'),('10:4',.7,'io'),('11:1',1,'io'),('12:4',0,'io'),('13:1+8',.95,'io'),('13:3',.95,'io'),('13:3+12',0,'io'),
             ('13:3+22',0,'io'),('13:3+36',.92,'io')],
 'eyeSmile':[('0',0,'io'),('4:2',.5,'io'),('4:3+10',.15,'io'),('5:4',.4,'io'),('6:1',.25,'io'),('9:1',0,'io'),('10:2',.4,'io'),('10:3',1,'io'),
             ('11:1',.15,'io'),('12:4',1,'io'),('13:1+8',.25,'io'),('13:3',.35,'io'),('14:1',.3,'io')],
 'pupil':   [('0',.92,'io'),('3:2',1.12,'io'),('4:4',1.04,'io'),('7:3',1.15,'o'),('8:1',1,'io'),('9:1',1.08,'io'),('12:1',1.15,'io'),('13:1',1.04,'io')],
 'smile':   [('0',.05,'io'),('1:3',-.25,'io'),('1:4',.15,'io'),('3:4',0,'io'),('4:2',.8,'io'),('4:4',.4,'io'),('5:3',0,'io'),('5:4',.7,'io'),
             ('6:1',.6,'io'),('7:2',.3,'io'),('8:2',.9,'io'),('9:1',.2,'io'),('9:4',.6,'io'),('10:2',.5,'io'),('10:3',1,'io'),('11:1',.55,'io'),
             ('11:3',.85,'io'),('12:1',.45,'io'),('12:4',1,'io'),('13:1+8',.75,'io'),('14:1',.85,'io')],
 'mouthOpen':[('0',0,'io'),('3:3+14',0,'io'),('3:3+18',.35,'o'),('4:1',0,'io'),('4:4+10',.2,'io'),('5:1',.3,'cut'),('5:2',.1,'io'),
             ('5:3',.45,'o'),('5:4',.1,'io'),('6:1',.25,'io'),('7:1',.1,'io'),('7:3',.3,'o'),('7:4',.05,'io'),('8:2',.5,'o'),('8:4',.3,'io'),
             ('9:1',.05,'io'),('10:3',.55,'o'),('10:4',.2,'io'),('11:1',.05,'io'),('12:1',.45,'io'),('12:3',.1,'io'),('12:4',.25,'io'),('13:1+8',.08,'io'),('14:1',0,'io')],
 'blush':   [('0',.1,'io'),('1:3',.55,'io'),('2:4',.3,'io'),('3:4',.35,'io'),('4:2',.5,'io'),('5:4',.55,'io'),('6:2',.35,'io'),('10:1+14',.4,'io'),
             ('10:2',.9,'o'),('10:4',.8,'io'),('11:3',.7,'io'),('13:1',.6,'io')],
 'earRot':  [('0',-.35,'io'),('1:2',-.5,'io'),('1:4',-.3,'io'),('3:1-8',.9,'back'),('3:4',1,'o'),('4:1',.4,'io'),('4:3',.8,'back'),
             ('5:1+4',-.3,'o'),('5:1+18',.8,'back'),('5:3',0,'io'),('6:1',.5,'io'),('7:1',.9,'back'),('7:4',-.8,'o'),('8:1',.6,'back'),
             ('9:1',.2,'io'),('10:1+12',.3,'io'),('10:2',-.8,'o'),('10:4',.4,'back'),('11:1',.8,'io'),('13:1',.7,'io')],
 'earSwivel':[('0',0,'io'),('2:1-10',-1,'o'),('2:3',0,'o'),('7:1',.7,'o'),('7:4',0,'io')],
 'tailBase':[('0',0,'io'),('1:4',8,'io'),('2:4',15,'io'),('3:4',45,'o'),('3:4+20',20,'io'),('4:4+10',70,'o'),('5:1',55,'cut'),('7:2',60,'io'),
             ('9:1',20,'io'),('9:4',25,'io'),('11:1',65,'io'),('13:1',70,'io'),('14:3',60,'io')],
 'tailCurl':[('0',0,'io'),('4:4+10',50,'io'),('5:1',35,'cut'),('9:1',5,'io'),('11:1',45,'io'),('13:1+30',70,'io')],
 'armL':    [('0',2,'io'),('3:4',6,'o'),('4:1',1,'io'),('4:4+6',-2,'io'),('5:1',14,'o'),('5:1+16',8,'io'),('5:3',18,'o'),('5:3+10',4,'io'),
             ('5:4',3,'back'),('8:3',15,'o'),('8:3+8',4,'io'),('8:4',15,'o'),('8:4+8',3,'io'),('10:2',-2,'io'),('10:3',2,'io'),('11:3',5,'io'),
             ('12:1',22,'o'),('12:3',5,'io'),('13:1',2,'io')],
 'armR':    [('0',2,'io'),('3:4',6,'o'),('4:1',1,'io'),('4:4+6',-2,'io'),('5:1',14,'o'),('5:1+16',8,'io'),('5:3',4,'o'),('5:3+10',16,'io'),
             ('5:4',3,'back'),('7:3-4',2,'io'),('7:3+2',26,'o'),('7:3+12',6,'io'),('7:4',3,'io'),('8:3',15,'o'),('8:3+8',4,'io'),('8:4',15,'o'),
             ('8:4+8',3,'io'),('10:2',-2,'io'),('10:3',2,'io'),('11:3',5,'io'),('12:1',22,'o'),('12:3',5,'io'),('13:1',2,'io')],
 'knead':   [('0',1,'io'),('3:2',0,'io')],
 'liftL':   [('0',0,'io'),('1:2',14,'o'),('1:2+8',0,'i'),('1:3',10,'o'),('1:3+8',0,'i')],
 'camH':    [('0',.84,'io'),('2:1',.92,'io'),('3:1',1.08,'io'),('4:1',1.28,'io'),('4:4',1.33,'io'),('5:1',.74,'cut'),('6:1',.76,'io'),
             ('7:2',.9,'io'),('8:4',.95,'io'),('9:1',1.08,'io'),('10:1',1.16,'io'),('11:1',1.24,'io'),('11:4',1.27,'io'),('12:1',1.02,'io'),
             ('12:3+10',1.18,'io'),('13:1',1.22,'io'),('15:1',1.32,'io')],
 'camY':    [('0',780,'io'),('3:1',700,'io'),('4:1',560,'io'),('4:4',545,'io'),('5:1',720,'cut'),('7:2',660,'io'),('9:1',560,'io'),('11:1',490,'io'),
             ('12:1',330,'io'),('12:3+10',450,'io'),('13:1',440,'io'),('15:1',420,'io')],
 'camX':    [('0',510,'io'),('7:1',545,'io'),('8:1',510,'io')],
}
FOLLOW = {'headRoll': (3.4, .55), 'headPitch': (3.4, .55), 'headYaw': (3.4, .6), 'gazeX': (9, .7), 'gazeY': (9, .7),
          'earRot': (6, .45), 'earSwivel': (6, .45), 'armL': (3.2, .5), 'armR': (3.2, .5), 'tailBase': (2.2, .5),
          'tailCurl': (2, .5), 'smile': (8, .8), 'bodyRoll': (3, .6), 'camH': (1.3, .9), 'camY': (1.3, .9), 'camX': (1.3, .9)}
BLINKS = ['0:1+0', '2:3', '4:1', '6:2', '7:1-6', '9:1', '11:1-10', '12:3', '14:2']
EAR_KICKS = [('2:4', 'L', -250), ('2:4+3', 'R', 250), ('4:3', 'LR', 180), ('7:4+14', 'R', 420), ('14:1+10', 'R', 300)]
TAIL_KICKS = ['8:2+16', '8:3', '8:3.5', '14:3']

# ---------------------------------------------------------------- signals (240 Hz simulation, sampled per frame)
def ease(u, e):
    if e == 'lin': return u
    if e == 'i': return u ** 3
    if e == 'o': return 1 - (1 - u) ** 3
    if e == 'back': c = 1.7; return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2
    return .5 - .5 * np.cos(np.pi * u)

def curve(keys, ts):
    ks = sorted((T(c), v, e) for c, v, e in keys)
    out = np.full(ts.shape, float(ks[0][1]))
    for (t0, v0, _), (t1, v1, e) in zip(ks, ks[1:]):
        m = (ts >= t0) & (ts < t1)
        out[m] = v0 if e == 'cut' else v0 + (v1 - v0) * ease((ts[m] - t0) / max(t1 - t0, 1e-6), e)
    out[ts >= ks[-1][0]] = ks[-1][1]
    return out

def follow(x, f, z, dt, reset):
    w = 2 * math.pi * f; y, v = x[0], 0.0; out = np.empty_like(x)
    for i, xi in enumerate(x):
        if i == reset: y, v = xi, 0.0
        v += (w * w * (xi - y) - 2 * z * w * v) * dt; y += v * dt; out[i] = y
    return out

def spring(rx, ry, f, z, gain, dt, reset, kicks=(), wind=None, ts=None, ph=0.0):
    """2D tip offset that lags its root: o'' = -w^2 o - 2 z w o' - gain * root''."""
    ax = np.clip(np.gradient(np.gradient(rx, dt), dt), -2e4, 2e4); ay = np.clip(np.gradient(np.gradient(ry, dt), dt), -2e4, 2e4)
    ax[reset - 3:reset + 3] = 0; ay[reset - 3:reset + 3] = 0
    kick = {int(round(T(c) / dt)): k for c, k in kicks}
    w = 2 * math.pi * f; o = np.zeros(2); v = np.zeros(2); out = np.empty((len(rx), 2))
    for i in range(len(rx)):
        if i in kick: v[0] += kick[i]
        fw = wind[i] * (math.sin(1.3 * ts[i] + ph) + .6 * math.sin(2.9 * ts[i] + 1 + ph)) if wind is not None else 0
        a = -w * w * o - 2 * z * w * v - gain * np.array([ax[i] - fw * 40, ay[i]])
        v += a * dt; o += v * dt; out[i] = o
    return out

def beat_index(ts):
    from build_motion import BEATS, IBI
    b = np.array(BEATS); idx = np.interp(ts, b, np.arange(len(b)))
    return np.where(ts > b[-1], len(b) - 1 + (ts - b[-1]) / IBI, idx)

def build_signals():
    dt = 1 / 240; ts = np.arange(0, DUR + .05, dt); reset = int(round(CUT / dt))
    S = {k: curve(v, ts) for k, v in K.items()}
    for k, (f, z) in FOLLOW.items(): S[k] = follow(S[k], f, z, dt, reset)
    # procedural layers: idle rock, sleeve kneading, eighth-note trot, breathing
    S['bodyX'] = S['idle'] * 5 * np.sin(2 * np.pi * .23 * ts)
    S['bodyRoll'] = S['bodyRoll'] + S['idle'] * .8 * np.sin(2 * np.pi * .23 * ts - .6)
    kn = S['knead'] * 1.6 * np.sin(2 * np.pi * .9 * ts); S['armL'] = S['armL'] + kn; S['armR'] = S['armR'] - kn
    ph = 2 * (beat_index(ts) - beat_index(np.array([T('6:1')]))[0]); fr = np.mod(ph, 1); up = np.sin(np.pi * fr)
    odd = np.mod(np.floor(ph), 2) == 1; tr = S['trot']
    S['liftL'] = S['liftL'] + tr * 20 * up * (~odd); S['liftR'] = tr * 20 * up * odd
    S['bodyY'] = S['bodyY'] + tr * 9 * up; S['crouch'] = S['crouch'] + tr * 7 * (1 - up)
    S['bodyRoll'] = S['bodyRoll'] + tr * 2.2 * np.sin(np.pi * ph)
    S['armL'] = S['armL'] + tr * 7 * np.sin(np.pi * ph); S['armR'] = S['armR'] - tr * 7 * np.sin(np.pi * ph)
    S['breath'] = S['breathPx'] * np.sin(2 * np.pi * np.cumsum(S['breathHz']) * dt)
    bl = np.zeros_like(ts)
    for c in BLINKS:
        u = (ts - T(c)) * 60
        bl = np.maximum(bl, np.select([(u >= 0) & (u < 4), (u >= 4) & (u < 6), (u >= 6) & (u < 13)], [u / 4, 1 + 0 * u, 1 - (u - 6) / 7], 0))
    S['close'] = np.clip(1 - S['lid'] * (1 - bl), 0, 1)
    # roots for secondary motion (art px, y down)
    rl = np.radians(S['headRoll'] + S['bodyRoll'])
    hx = S['bodyX'] + 260 * np.sin(rl) + S['headYaw'] * 6; hy = -S['bodyY'] + S['crouch'] - S['squash'] * 1250 - S['rise'] * 14 + S['headPitch'] * .5
    px = S['bodyX'] + 620 * np.sin(np.radians(S['bodyRoll'])); py = -S['bodyY'] + S['crouch'] - S['squash'] * 620
    wind = np.where(ts > CUT, 1.0, .35)
    S['hairL'] = spring(hx, hy, 1.4, .33, 1.0, dt, reset, wind=wind, ts=ts)
    S['hairR'] = spring(hx, hy, 1.55, .33, 1.0, dt, reset, wind=wind, ts=ts, ph=.7)
    S['ahoge'] = spring(hx, hy, 4.5, .2, 1.2, dt, reset)
    S['earTipL'] = spring(hx, hy, 7, .35, .5, dt, reset, [(c, k) for c, s, k in EAR_KICKS if 'L' in s])
    S['earTipR'] = spring(hx, hy, 7, .35, .5, dt, reset, [(c, k) for c, s, k in EAR_KICKS if 'R' in s])
    S['cuffL'] = spring(px, py - 500, 2.0, .4, .8, dt, reset); S['cuffR'] = spring(px, py - 500, 2.1, .4, .8, dt, reset)
    S['skirt'] = np.clip(spring(px, py, 2.4, .6, .6, dt, reset), -9, 9)
    S['tail'] = spring(px, py, 1.6, .35, 1.0, dt, reset, [(c, 500) for c in TAIL_KICKS], wind=wind * .8, ts=ts, ph=2.)
    return {k: v[::4] for k, v in S.items()}

# ---------------------------------------------------------------- art, masks and warp controllers
def load_art():
    im = cv2.cvtColor(cv2.imread(ART, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]
    bgc = (im.min(2) >= 249) & (np.ptp(im, 2) <= 5)
    lab = cv2.connectedComponents(bgc.astype(np.uint8), connectivity=4)[1]
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, border[border > 0]) & bgc
    a = (~bg).astype(np.float32)
    inner = cv2.erode(a, None, iterations=2) > .5
    a = np.where(inner, 1., np.clip((252. - im.min(2)) / 45., 0, 1) * a).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), .6); a[inner] = 1
    rgba = np.zeros((h + 2 * P, w + 2 * P, 4), np.float32)
    rgba[P:P + h, P:P + w, :3] = im / 255.; rgba[P:P + h, P:P + w, 3] = a
    return rgba

def poly(pts, sig, shape):
    m = np.zeros(shape, np.float32)
    cv2.fillPoly(m, [np.int32([(x + P, y + P) for x, y in pts])], 1.0)
    return cv2.GaussianBlur(m, (0, 0), sig) if sig else m

HEAD = [(330, 30), (700, 30), (705, 230), (650, 320), (600, 350), (545, 372), (470, 372), (410, 348), (355, 315), (320, 230)]
BANGS = [(405, 140), (600, 140), (605, 250), (400, 250)]
HAIRL = [(318, 280), (410, 280), (412, 430), (405, 610), (330, 615), (315, 450)]
HAIRR = [(598, 280), (705, 280), (708, 450), (700, 615), (612, 610), (600, 430)]
EARL, EARL_P = [(350, 98), (392, 92), (428, 150), (420, 190), (378, 190), (352, 150)], (400, 182)
EARR, EARR_P = [(600, 90), (648, 88), (652, 150), (636, 188), (594, 186), (588, 140)], (615, 182)
AHOGE, AHOGE_P = [(450, 28), (500, 28), (496, 95), (458, 95)], (476, 95)
ARML, ARML_P = [(420, 405), (400, 520), (372, 700), (362, 875), (252, 875), (258, 700), (300, 520), (355, 425)], (392, 440)
ARMR, ARMR_P = [(600, 405), (622, 520), (650, 700), (662, 875), (768, 875), (760, 700), (718, 520), (665, 425)], (628, 440)
SKIRT = [(368, 790), (655, 790), (668, 885), (360, 885)]
LEGL = [(418, 1140), (506, 1140), (510, 1500), (425, 1500)]
LEGR = [(508, 1140), (610, 1140), (590, 1500), (506, 1500)]
TAIL, TAIL_B, TAIL_L = [(338, 876), (404, 876), (406, 1010), (336, 1010)], (386, 874), 128.
NECK = (500, 372)
EYES = [dict(c=(459, 268), a=31, b=21, ang=-6, i=(462, 269), r=19, side=-1),
        dict(c=(550, 254), a=28, b=21, ang=-8, i=(547, 253), r=17, side=1)]
MOUTH, NOSE, CHEEKS, BOW = (508, 307), (502, 285), [(445, 296), (576, 288)], (497, 470)

def build_rig():
    art = load_art(); shp = art.shape[:2]
    tailm = poly(TAIL, 0, shp) * art[..., 3]
    tail = art.copy(); tail[..., 3] = tailm
    body = art.copy(); body[..., 3] *= 1 - tailm
    pm = lambda a: np.dstack([a[..., :3] * a[..., 3:], a[..., 3:]])            # premultiply
    hc, wc = shp[0] // STEP, shp[1] // STEP
    gx, gy = np.meshgrid(np.arange(wc, dtype=np.float32) * STEP, np.arange(hc, dtype=np.float32) * STEP)
    ax, ay = gx - P, gy - P
    co = lambda m: cv2.resize(m, (wc, hc), interpolation=cv2.INTER_AREA)
    cl = lambda v: np.clip(v, 0, 1).astype(np.float32)
    dist = lambda p: np.hypot(ax - p[0], ay - p[1])
    face = np.zeros(shp, np.float32); cv2.ellipse(face, (500 + P, 283 + P), (82, 58), 0, 0, 360, 1, -1); face = cv2.GaussianBlur(face, (0, 0), 14)
    hl, hr = co(poly(HAIRL, 10, shp)), co(poly(HAIRR, 10, shp)); rh = cl((ay - 300) / 300)
    arml, armr = co(poly(ARML, 16, shp)), co(poly(ARMR, 16, shp))
    Wt = {
        'head': np.maximum(co(poly(HEAD, 14, shp)), (hl + hr) * (1 - rh) * .9), 'face': co(face), 'bangs': co(poly(BANGS, 12, shp)),
        'earL': co(poly(EARL, 5, shp)) * cl(dist(EARL_P) / 80) ** .8, 'earR': co(poly(EARR, 5, shp)) * cl(dist(EARR_P) / 85) ** .8,
        'ahoge': co(poly(AHOGE, 4, shp)) * cl((95 - ay) / 55),
        'hairL': hl * rh, 'hairR': hr * rh, 'upper': cl((600 - ay) / 180), 'chest': cl((650 - ay) / 250),
        'crouch': cl((FEET[1] - ay) / (FEET[1] - 880)), 'skirt': co(poly(SKIRT, 8, shp)) * cl((ay - 800) / 80),
        'legL': co(poly(LEGL, 4, shp)) * cl((ay - 1160) / 190), 'legR': co(poly(LEGR, 4, shp)) * cl((ay - 1160) / 190),
        'armL': arml * cl((ay - 440) / 230), 'armR': armr * cl((ay - 440) / 230),
        'cuffL': arml * cl((ay - 740) / 80), 'cuffR': armr * cl((ay - 740) / 80)}
    Wt['earTipL'] = Wt['earL'] ** 2; Wt['earTipR'] = Wt['earR'] ** 2
    names = list(Wt)
    skin = art[262 + P - 3:262 + P + 3, 505 + P - 3:505 + P + 3, :3].reshape(-1, 3).mean(0)
    return dict(body=pm(body), tail=pm(tail), names=names, W=np.stack([Wt[n] for n in names]).astype(np.float32),
                gx=gx, gy=gy, skin=skin, shape=shp)

# ---------------------------------------------------------------- per-frame character
def controllers(s):
    """Forward transforms per controller: (pivot, angle deg, tx, ty). Positive angle = clockwise on screen."""
    yaw, pitch = s['headYaw'], s['headPitch']
    r, sw = float(s['earRot']), float(s['earSwivel'])
    base = r * (14 if r < 0 else 5)                      # flatten = tips out and down, perk = tips in and up
    aL = base + (10 * sw if sw < 0 else 8 * sw)          # swivel < 0: both ears turn back; > 0: both lean toward screen-right
    aR = -base + (-10 * sw if sw < 0 else 8 * sw)
    return {
        'head': (NECK, s['headRoll'], yaw * 2, pitch * .5), 'face': (NECK, 0, yaw * 10, pitch * .35), 'bangs': (NECK, 0, yaw * 6, pitch * .2),
        'earL': (EARL_P, aL, 0, 0), 'earR': (EARR_P, aR, 0, 0),
        'earTipL': (EARL_P, 0, *s['earTipL']), 'earTipR': (EARR_P, 0, *s['earTipR']),
        'ahoge': (AHOGE_P, np.clip(s['ahoge'][0] * .5, -25, 25), 0, 0),
        'hairL': (NECK, 0, s['hairL'][0] * .8, s['hairL'][1] * .3), 'hairR': (NECK, 0, s['hairR'][0] * .8, s['hairR'][1] * .3),
        'upper': (NECK, 0, 0, -s['rise'] * 14), 'chest': (NECK, 0, 0, -s['breath']), 'crouch': (NECK, 0, 0, s['crouch']),
        'skirt': (NECK, 0, s['skirt'][0], 0), 'legL': (NECK, 0, 0, -s['liftL']), 'legR': (NECK, 0, 0, -s['liftR']),
        'armL': (ARML_P, s['armL'], 0, 0), 'armR': (ARMR_P, -s['armR'], 0, 0),
        'cuffL': (ARML_P, 0, *(s['cuffL'] * .7)), 'cuffR': (ARMR_P, 0, *(s['cuffR'] * .7))}

def warp_field(R, s):
    """Inverse of the forward deformation on the coarse grid, by fixed-point iteration: src = x - F(src)."""
    tr = controllers(s); names = R['names']; Wm = R['W']
    x, y = R['gx'], R['gy']; sx, sy = x.copy(), y.copy()
    for _ in range(5):
        fx = np.zeros_like(x); fy = np.zeros_like(y)
        mx, my = sx / STEP, sy / STEP
        for i, n in enumerate(names):
            (px, py), ang, tx, ty = tr[n]; px += P; py += P
            w = cv2.remap(Wm[i], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            if ang:
                c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                dx, dy = sx - px, sy - py
                fx += w * ((c - 1) * dx - sn * dy + tx); fy += w * (sn * dx + (c - 1) * dy + ty)
            else:
                fx += w * tx; fy += w * ty
        sx, sy = x - fx, y - fy
    return sx.astype(np.float32), sy.astype(np.float32)

def smoothstep(a, b, v): u = np.clip((v - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)

def edit_face(src, R, s):
    """Eyes (gaze, pupils, lids, happy squint), mouth and blush, painted into a copy of the art before the warp."""
    img = src.copy(); skin = R['skin']
    close, es, pupil, cross = float(s['close']), float(s['eyeSmile']), float(s['pupil']), float(s['cross'])
    for E in EYES:
        cx, cy = E['c'][0] + P, E['c'][1] + P; a, b = E['a'], E['b']
        x0, x1, y0, y1 = int(cx - a - 8), int(cx + a + 9), int(cy - b - 8), int(cy + b + 9)
        X, Y = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
        cth, sth = math.cos(math.radians(E['ang'])), math.sin(math.radians(E['ang']))
        u = (X - cx) * cth + (Y - cy) * sth; v = -(X - cx) * sth + (Y - cy) * cth
        k = np.sqrt((u / a) ** 2 + (v / b) ** 2); mask = np.clip((1.06 - k) / .1, 0, 1)
        half = b * np.sqrt(np.clip(1 - (u / a) ** 2, 0, 1)); vt, vb = -half, half
        c = min(close, .999)
        vl = vt + c * (vb - vt); vbe = vb - es * .45 * (vb - vt) * (1 - c) - es * .2 * (vb - vt) * c
        span = np.maximum(vbe - vl, .5)
        vs = np.where((v >= vl) & (v <= vbe), vt + (v - vl) / span * (vb - vt), v)
        # back to image coords, then gaze and pupil scale around the iris
        qx = cx + u * cth - vs * sth; qy = cy + u * sth + vs * cth
        ix, iy = E['i'][0] + P, E['i'][1] + P
        gx = 5 * float(s['gazeX']) - E['side'] * 4 * cross; gy = 3 * float(s['gazeY']) + 1.5 * cross
        d = np.hypot(qx - ix - gx, qy - iy - gy); fall = np.clip(1 - d / (E['r'] * 1.7), 0, 1) ** 1.5 * mask
        qx = qx - gx * fall; qy = qy - gy * fall
        sc = 1 + (pupil - 1) * fall; qx = ix + (qx - ix) / sc; qy = iy + (qy - iy) / sc
        patch = cv2.remap(src, qx.astype(np.float32), qy.astype(np.float32), cv2.INTER_CUBIC)
        band = ((v >= vl) & (v <= vbe)).astype(np.float32)
        band = cv2.GaussianBlur(band, (0, 0), .6) * (1 - smoothstep(.72, .93, c))
        skin_a = mask * (1 - band) * np.clip(np.maximum(smoothstep(0, .06, c), smoothstep(0, .1, es)), 0, 1)
        smp = lambda vv: cv2.remap(src, (cx + u * cth - vv * sth).astype(np.float32), (cy + u * sth + vv * cth).astype(np.float32), cv2.INTER_LINEAR)[..., :3]
        top, bot = smp(vt - 3.5), smp(vb + 6); f = np.clip((v - vt) / 4., 0, 1)[..., None]
        fill = cv2.GaussianBlur((top * (1 - f) + bot * f).astype(np.float32), (0, 0), 1.5)
        out = patch.copy()
        out[..., :3] = out[..., :3] * (1 - skin_a[..., None]) + fill * skin_a[..., None]
        # drawn lid line once the eye is nearly shut: calm = soft U, happy = arch
        lc = smoothstep(.62, .95, c)
        if lc > 0:
            curv = (1 - es) * 3.5 - es * 7
            vline = vl + curv * (1 - (u / a) ** 2) - (1 - c) * 0
            th = 1.9 * (1 - (u / a) ** 4) + .5
            la = np.clip(1 - np.abs(v - vline) / th, 0, 1) * (np.abs(u) < a * .97) * lc * mask
            out[..., :3] = out[..., :3] * (1 - la[..., None]) + np.array([.27, .23, .33]) * la[..., None]
        m3 = mask[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m3) + out * m3
    # mouth: corners lift for a smile, a small open shape for "ah"
    mx, my = MOUTH[0] + P, MOUTH[1] + P
    x0, x1, y0, y1 = mx - 22, mx + 23, my - 14, my + 16
    X, Y = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
    sm = float(s['smile']); dxm = (X - mx) / 11
    lift = sm * 2.4 * np.clip(dxm ** 2, 0, 1.4) * np.exp(-((Y - my) / 6) ** 2) * np.exp(-np.clip(np.abs(dxm) - 1.2, 0, None) ** 2 * 3)
    patch = cv2.remap(img, X, (Y + lift).astype(np.float32), cv2.INTER_CUBIC)
    o = float(s['mouthOpen'])
    if o > .02:
        rx, ry = 4 + 3.5 * o, .8 + 6.5 * o; cyo = my + 1.5 + ry * .55
        e = ((X - mx) / rx) ** 2 + ((Y - cyo) / ry) ** 2
        fa = np.clip((1 - e) * 3, 0, 1) * smoothstep(.02, .12, o)
        ln = np.clip((1.25 - np.abs(e - 1) * 4), 0, 1) * (e > .6) * smoothstep(.02, .12, o) * .8
        col = np.where((Y > cyo + ry * .15)[..., None], np.array([.9, .56, .6]), np.array([.62, .33, .4]))
        patch[..., :3] = patch[..., :3] * (1 - fa[..., None]) + col * fa[..., None] * patch[..., 3:]
        patch[..., :3] = patch[..., :3] * (1 - ln[..., None]) + np.array([.45, .25, .32]) * ln[..., None]
    img[y0:y1, x0:x1] = patch
    # blush
    bl = float(s['blush'])
    if bl > .01:
        for (bx, by) in CHEEKS:
            x0, y0 = bx + P - 34, by + P - 20
            X, Y = np.meshgrid(np.arange(68, dtype=np.float32) - 34, np.arange(40, dtype=np.float32) - 20)
            g = np.exp(-((X / 22) ** 2 + (Y / 9) ** 2) * 1.6) * bl * .42
            reg = img[y0:y0 + 40, x0:x0 + 68]
            reg[..., :3] = reg[..., :3] * (1 - g[..., None]) + np.array([1., .55, .63]) * g[..., None] * reg[..., 3:]
    return img

# ---------------------------------------------------------------- world, sprites, fx
def rng(seed): return np.random.default_rng(seed)

def fbm(shape, seed, scales=(64, 24, 8), amps=(1, .5, .25)):
    r = rng(seed); out = np.zeros(shape, np.float32)
    for s, a in zip(scales, amps):
        out += a * cv2.GaussianBlur(r.standard_normal(shape).astype(np.float32), (0, 0), s) * s ** .5
    return (out - out.mean()) / (out.std() + 1e-6)

def make_sprites():
    n = 384; X, Y = np.meshgrid(np.linspace(-1, 1, n), np.linspace(-1, 1, n)); r = np.hypot(X, Y)
    washes = []
    for i in range(4):
        sh = smoothstep(.72, .66, r + .22 * fbm((n, n), 10 + i, (40, 14, 5)) * .5)
        edge = np.clip(sh - cv2.GaussianBlur(sh, (0, 0), 5), 0, 1) * 2.2
        gran = np.clip(fbm((n, n), 20 + i, (1.5, 4), (1, .6)) * .5 + .5, 0, 1)
        washes.append(np.clip(sh * (.42 + .12 * gran) + edge * .45, 0, 1).astype(np.float32))
    m = 96; X, Y = np.meshgrid(np.linspace(-1, 1, m), np.linspace(-1, 1, m)); r = np.hypot(X, Y)
    a = np.clip((1 - r) / .06, 0, 1); body = a * (.5 + .4 * r ** 3)
    hl = np.exp(-(((X + .33) ** 2 + (Y + .38) ** 2) / .025)); rim = np.exp(-((r - .9) / .06) ** 2) * .35
    bead = dict(a=np.clip(np.maximum(body, hl * .9), 0, 1).astype(np.float32), lum=((1 - .22 * r ** 2) * (1 - rim)).astype(np.float32), hl=hl.astype(np.float32))
    k = 64; X, Y = np.meshgrid(np.linspace(-1, 1, k), np.linspace(-1, 1, k))
    star = np.maximum(np.exp(-np.abs(X) * 9) * np.exp(-Y ** 2 * 60), np.exp(-np.abs(Y) * 9) * np.exp(-X ** 2 * 60))
    star = np.clip(np.maximum(star, np.exp(-(X ** 2 + Y ** 2) * 18)), 0, 1).astype(np.float32)
    g = 128; X, Y = np.meshgrid(np.linspace(-1, 1, g), np.linspace(-1, 1, g)); glow = np.exp(-(X ** 2 + Y ** 2) * 4.5).astype(np.float32)
    return dict(washes=washes, bead=bead, star=star, glow=glow)

def blit(F, alpha, cx, cy, w, h, col, mode='over', ang=0):
    """Composite a single-channel alpha sprite tinted col into F (H,W,3), centred at screen (cx, cy)."""
    if w < 2 or h < 2: return
    rad = math.hypot(w, h) / 2 if ang else max(w, h) / 2
    xa, ya, xb, yb = max(int(cx - rad), 0), max(int(cy - rad), 0), min(int(cx + rad) + 1, W), min(int(cy + rad) + 1, H)
    if xa >= xb or ya >= yb: return
    sh, sw = alpha.shape; c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    A = np.array([[c * w / sw, -sn * h / sh], [sn * w / sw, c * h / sh]])
    M = np.hstack([A, (np.array([cx - xa, cy - ya]) - A @ np.array([sw / 2, sh / 2]))[:, None]])
    s = cv2.warpAffine(alpha, M, (xb - xa, yb - ya), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
    reg = F[ya:yb, xa:xb]; col = np.asarray(col, np.float32)
    if mode == 'mul': reg *= 1 - s * (1 - col)
    elif mode == 'add': reg += s * col
    else: reg *= 1 - s; reg += s * col

def bead(F, SP, cx, cy, d, col, alpha=1., blur=0):
    d = max(int(d), 3); B = SP['bead']
    a = cv2.resize(B['a'], (d, d)); lum = cv2.resize(B['lum'], (d, d)); hl = cv2.resize(B['hl'], (d, d))
    rgb = np.clip(np.asarray(col, np.float32) * lum[..., None] + hl[..., None] * .9, 0, 1)
    if blur:
        k = blur * d / 40
        a = cv2.GaussianBlur(a, (0, 0), k); rgb = cv2.GaussianBlur(rgb, (0, 0), k)
    x0, y0 = int(cx - d / 2), int(cy - d / 2); xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + d, W), min(y0 + d, H)
    if xa >= xb or ya >= yb: return
    s = a[ya - y0:yb - y0, xa - x0:xb - x0, None] * alpha
    F[ya:yb, xa:xb] = F[ya:yb, xa:xb] * (1 - s) + rgb[ya - y0:yb - y0, xa - x0:xb - x0] * s

PASTEL = [(.70, .84, .99), (.99, .77, .85), (.84, .78, .99), (.76, .94, .88), (1., .93, .72)]
BLUE, PINK = (.55, .76, .98), (.98, .62, .74)

def lerp_path(t, pts):
    """pts: [(time, x, y, ease)], eased segments; clamps at the ends."""
    if t <= pts[0][0]: return pts[0][1], pts[0][2]
    for (t0, x0, y0, _), (t1, x1, y1, e) in zip(pts, pts[1:]):
        if t < t1:
            u = float(ease(np.array((t - t0) / (t1 - t0)), e)); return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return pts[-1][1], pts[-1][2]

class Scene:
    def __init__(self):
        r = rng(7)
        pap = np.array([.988, .980, .962], np.float32)
        self.paper = np.clip(pap + .010 * fbm((H, W), 1, (90, 30), (1, .5))[..., None] + .005 * fbm((H, W), 2, (1, 2), (1, .5))[..., None], 0, 1).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W]; vig = 1 - .04 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.grain = (vig * (1 - .018 * np.clip(fbm((H, W), 3, (1.2, 3), (1, .5)) * .5 + .5, 0, 1)))[..., None].astype(np.float32)
        self.SP = make_sprites()
        tb = T('5:1+16')
        self.bloom = [(tb + .08 * i, 510 + dx, 1495 + dy, R, PASTEL[i % 5], i % 4, r.uniform(0, 360)) for i, (dx, dy, R) in enumerate(
            [(0, 0, 1500), (-420, -500, 1300), (430, -620, 1350), (-200, -1250, 1500), (300, -1500, 1450), (0, -800, 1700), (-600, 200, 900), (650, 150, 950)])]
        self.steps = [(T(f'{6 + int(n * .5 // 4)}:{(n * .5) % 4 + 1:g}'), -40 if n % 2 == 0 else 40, PASTEL[n % 5], r.uniform(0, 360)) for n in range(10)]
        self.float_beads = [(x, y, PASTEL[i % 5], d, r.uniform(0, 6.28), blur) for i, (x, y, d, blur) in enumerate(
            [(200, 380, 46, 0), (840, 250, 38, 0), (170, 820, 40, 0), (880, 1020, 44, 0), (120, 130, 110, 3.5), (930, 620, 90, 3), (300, 1180, 34, 0)])]
        self.sparks = [(r.uniform(0, 6.28), r.uniform(.6, 1.4), r.uniform(0, 1), PASTEL[i % 5]) for i in range(16)]
        self.petals = [(r.uniform(-100, 1100), r.uniform(-900, 0), r.uniform(.6, 1.3), PASTEL[i % 5], r.uniform(0, 6.28)) for i in range(26)]
        self.motes = [(r.uniform(0, 1020), r.uniform(-100, 1500), r.uniform(.3, 1), r.uniform(0, 6.28)) for i in range(30)]
        # the special beads
        self.drop = [(T('3:1-12'), 575, -260, 'io'), (T('3:2'), 540, 60, 'io'), (T('3:3'), 515, 200, 'io'), (T('3:3+14'), NOSE[0], NOSE[1] - 6, 'i')]
        self.swipe = [(T('7:1'), 1000, 700, 'io'), (T('7:3'), 790, 770, 'io'), (T('7:3+10'), 900, 360, 'o'), (T('7:4'), 820, 190, 'io'),
                      (T('7:4+14'), 640, 112, 'i')]
        self.fade = [(T('9:1'), 505, -160, 'io'), (T('9:3'), 500, 250, 'io'), (T('9:4'), BOW[0], BOW[1], 'io')]
        self.pink = [(T('10:1-10'), 1120, 120, 'io'), (T('10:1+14'), CHEEKS[1][0] + 6, CHEEKS[1][1], 'i')]

    def cam(self, s):
        z = s['camH'] * H / CH_H
        return lambda x, y: ((x - s['camX']) * z + W / 2, (y - s['camY']) * z + H / 2), z

    def background(self, t, s):
        F = self.paper.copy(); w2s, z = self.cam(s); SP = self.SP
        pre = t < CUT
        # notebook page: ruled lines, pink margin, pencil ground line (fade as colour takes over)
        rule_a = .22 if pre else .16 * (1 - smoothstep(T('5:2'), T('6:3'), t))
        if rule_a > .004:
            lay = np.zeros((H, W), np.uint8)
            for wy in range(-640, 1700, 64):
                sy = w2s(0, wy)[1]
                if -5 < sy < H + 5: cv2.line(lay, (0, int(sy * 16)), (W, int(sy * 16)), 255, max(1, int(1.2 * z)), cv2.LINE_AA, 4)
            mxs = w2s(860, 0)[0]; cv2.line(lay, (int(mxs * 16), 0), (int(mxs * 16), H * 16), 230, max(1, int(1.6 * z)), cv2.LINE_AA, 4)
            F *= 1 - (lay / 255. * rule_a)[..., None] * (1 - np.array([.62, .74, .9], np.float32))
            g = np.zeros((H, W), np.uint8)
            pts = np.array([w2s(x, 1497 + 2.5 * math.sin(x * .05)) for x in range(170, 860, 10)]) * 16
            cv2.polylines(g, [pts.astype(np.int32)], False, 255, max(1, int(2 * z)), cv2.LINE_AA, 4)
            F *= 1 - (g / 255. * rule_a * 1.6)[..., None] * (1 - np.array([.45, .43, .5], np.float32))
        # watercolour bloom from the landing footprint
        for (t0, wx, wy, R, col, ti, ang) in self.bloom:
            if t > t0:
                rr = R * (1 - math.exp(-(t - t0) / .5)); sx, sy = w2s(wx, wy)
                blit(F, SP['washes'][ti] * .45, sx, sy, 2 * rr * z, 2 * rr * z, col, 'over', ang + 8 * (t - t0))
        # trot: colour pools spawn under her feet and slide toward the camera
        for (t0, dx, col, ang) in self.steps:
            if t0 < t < t0 + 2.2:
                u = t - t0; sx, sy = w2s(510 + dx * (1 + 2 * u), 1500 + 700 * u * u + 200 * u)
                rr = (60 + 260 * u) * z; blit(F, SP['washes'][int(ang) % 4] * .6 * max(0, 1 - u / 2.2), sx, sy, 2 * rr, rr * .9, col, 'over', ang)
        # sky release
        ts = T('12:2')
        if t > ts:
            u = 1 - math.exp(-(t - ts) / .6)
            for i, (wx, wy) in enumerate([(510, -150), (120, 50), (900, 0), (500, -500), (250, -420), (800, -380)]):
                sx, sy = w2s(wx, wy); rr = (500 + 380 * u) * u * z * (1 + .15 * (i % 2))
                blit(F, SP['washes'][i % 4] * .6, sx, sy, 2 * rr, 2 * rr, PASTEL[(i + 1) % 5], 'over', 30 * i + 5 * t)
            blit(F, SP['glow'], *w2s(510, -250), 1800 * z * u, 1300 * z * u, (.07, .06, .05), 'add')
        # contact shadow
        hop = max(s['bodyY'], 0) / 200
        blit(F, SP['glow'], *w2s(510 + s['bodyX'], 1494), 360 * z * s['approach'] * (1 - .35 * hop), 44 * z * (1 - .35 * hop),
             (.55, .52, .64), 'mul')
        blit(F, SP['glow'], *w2s(510 + s['bodyX'], 1494), 360 * z * s['approach'] * (1 - .35 * hop), 44 * z * (1 - .35 * hop),
             (.8, .78, .86), 'mul')
        return F

    def fx_back(self, F, t, s):
        w2s, z = self.cam(s); SP = self.SP
        if t < CUT:
            for (x, y, sp, ph) in self.motes:
                sx, sy = w2s(x + 20 * math.sin(t * .4 + ph), y - 25 * t * sp)
                blit(F, SP['glow'], sx, sy, 7 * z, 7 * z, (.35, .33, .3), 'add')
        a7 = smoothstep(T('7:1-10'), T('7:1+10'), t) * (1 - smoothstep(T('12:1'), T('12:2'), t))
        if a7 > 0:
            for (x, y, col, d, ph, blur) in self.float_beads:
                if blur: continue
                lift = -900 * smoothstep(T('12:1'), T('12:2'), t)
                sx, sy = w2s(x + 14 * math.sin(t * 1.1 + ph), y + 18 * math.sin(t * 1.7 + ph) + lift)
                bead(F, SP, sx, sy, d * z * a7, col, .9 * a7)

    def fx_front(self, F, t, s):
        w2s, z = self.cam(s); SP = self.SP
        # blue drop onto her nose, then sparkles soaking in
        t1 = T('3:3+14')
        if T('3:1-12') < t < t1:
            sx, sy = w2s(*lerp_path(t, self.drop)); bead(F, SP, sx, sy, 26 * z, BLUE, .95)
        if t1 <= t < t1 + 2.2:
            u = t - t1
            for i in range(7):
                ang = i * .9 + u * 1.3; rr = 20 + 90 * u
                sx, sy = w2s(NOSE[0] + rr * math.cos(ang), NOSE[1] - 40 * u - rr * .6 * math.sin(ang))
                k = max(0, 1 - u / 2.2) * (.6 + .4 * math.sin(u * 12 + i)); blit(F, SP['star'], sx, sy, 26 * z * k, 26 * z * k, BLUE, 'add')
        # floating beads, near layer (soft focus)
        a7 = smoothstep(T('7:1-10'), T('7:1+10'), t) * (1 - smoothstep(T('12:1'), T('12:2'), t))
        if a7 > 0:
            for (x, y, col, d, ph, blur) in self.float_beads:
                if not blur: continue
                sx, sy = w2s(x + 20 * math.sin(t * .8 + ph), y + 24 * math.sin(t * 1.2 + ph))
                bead(F, SP, sx, sy, d * z, col, .55 * a7, blur)
        # the bead she swats; it bounces back and pops on her ear
        tp = T('7:4+14')
        if T('7:1') < t < tp:
            sx, sy = w2s(*lerp_path(t, self.swipe)); bead(F, SP, sx, sy, 36 * z, PASTEL[3], .95)
        if tp <= t < T('9:1'):
            u = t - tp
            for i, (ph, sp, off, col) in enumerate(self.sparks):
                rr = 40 + 230 * (1 - math.exp(-u * sp * 1.5)); ang = ph + u * .8 * sp
                sx, sy = w2s(560 + rr * math.cos(ang), 300 + rr * .8 * math.sin(ang) + 60 * u)
                k = max(0, 1 - u / 2.6) * (.55 + .45 * math.sin(u * 9 + off * 6)); blit(F, SP['star'], sx, sy, 34 * z * k, 34 * z * k, col, 'add')
        # the fading blue she keeps: it drifts to her bow and lights it
        if T('9:1') < t < T('9:4'):
            fl = .25 + .12 * math.sin(t * 23) * math.sin(t * 7)
            sx, sy = w2s(*lerp_path(t, self.fade)); bead(F, SP, sx, sy, 30 * z, BLUE, fl)
        # the pink that boops her cheek
        tb = T('10:1+14')
        if T('10:1-10') < t < tb:
            sx, sy = w2s(*lerp_path(t, self.pink)); bead(F, SP, sx, sy, 30 * z, PINK, .6, 1.2)
        if tb <= t < tb + 1.2:
            u = t - tb
            for i in range(8):
                ang = i * .785; rr = 10 + 110 * (1 - math.exp(-u * 4))
                sx, sy = w2s(CHEEKS[1][0] + 10 + rr * math.cos(ang), CHEEKS[1][1] + rr * math.sin(ang))
                k = max(0, 1 - u / 1.2); blit(F, SP['star'], sx, sy, 24 * z * k, 24 * z * k, PINK, 'add')
        # bar 11: collected colours orbit her (front half of the orbit)
        for i in range(5):
            a11 = smoothstep(T('10:4'), T('11:1'), t) * (1 - smoothstep(T('12:1'), T('12:1+20'), t))
            if a11 <= 0: break
            ang = i * 1.2566 + (t - T('11:1')) * 1.4
            if math.sin(ang) > 0:
                sx, sy = w2s(510 + 330 * math.cos(ang), 640 + 90 * math.sin(ang))
                bead(F, SP, sx, sy, (30 + 10 * math.sin(ang)) * z, PASTEL[i], .9 * a11)
        # release: colours shoot upward
        tr = T('12:1+6')
        if tr < t < tr + 1.4:
            u = t - tr
            for i in range(9):
                ui = u - .055 * ((i * 4) % 9)
                if ui <= 0: continue
                sp = .8 + .45 * ((i * 7) % 5) / 4; x = 510 + (i - 4) * 105 + 45 * math.sin(i * 1.7)
                sx, sy = w2s(x + 60 * math.sin(ui * 3 + i) * ui, 560 + 60 * abs(i - 4) - (1100 * ui * ui + 260 * ui) * sp)
                bead(F, SP, sx, sy, (24 + 4 * (i % 3)) * z, PASTEL[i % 5], max(0, 1 - ui / 1.3))
                blit(F, SP['star'], sx, sy, 22 * z, 22 * z, PASTEL[i % 5], 'add')
        # petals drifting down after the release
        tpet = T('12:2')
        if t > tpet:
            u = t - tpet
            for (x, y, sp, col, ph) in self.petals:
                sx, sy = w2s(x + 50 * math.sin(u * sp + ph), y + 220 * u * sp)
                flip = abs(math.sin(u * 2.2 * sp + ph))
                blit(F, SP['glow'], sx, sy, 22 * z * (.35 + .65 * flip), 13 * z, col, 'over' if flip > .2 else 'over')

    def lights(self, t):
        """Local lights that fall on her (world pos, colour, radius, intensity)."""
        L = []
        t1 = T('3:3+14')
        if t1 < t < t1 + 1.5: L.append((NOSE, BLUE, 100, .12 * (1 - (t - t1) / 1.5)))
        if T('9:4') - .2 < t < T('11:1'):
            k = smoothstep(T('9:4') - .2, T('9:4') + .3, t) * (1 - smoothstep(T('10:4'), T('11:1'), t))
            L.append((BOW, BLUE, 160, .22 * k * (.85 + .15 * math.sin(t * 5))))
        if T('11:1') < t < T('12:2'):
            L.append(((510, 640), (1, .85, .9), 420, .06 * smoothstep(T('11:1'), T('11:2'), t)))
        if t > T('12:1'): L.append(((510, -100), (.95, .85, 1), 900, .06 * smoothstep(T('12:1'), T('12:3'), t)))
        return L

# ---------------------------------------------------------------- frame
def body_affine(s, z, camx, camy):
    """canvas px -> screen px for the whole character (scale about the feet, squash-stretch, roll, hop), then camera."""
    app, sq, rl = s['approach'], s['squash'], math.radians(s['bodyRoll'])
    sx, sy = app * (1 - .5 * sq), app * (1 + sq); c, sn = math.cos(rl), math.sin(rl)
    A = np.array([[c * sx, -sn * sy], [sn * sx, c * sy]])
    fx, fy = FEET[0] + P, FEET[1] + P
    off = np.array([FEET[0] + s['bodyX'], FEET[1] - s['bodyY']]) - A @ np.array([fx, fy])
    M = np.hstack([A * z, ((off - [camx, camy]) * z + [W / 2, H / 2])[:, None]])
    return M

def render_character(F, R, s, t, scene):
    w2s, z = scene.cam(s)
    M = body_affine(s, z, s['camX'], s['camY']); Mi = cv2.invertAffineTransform(M)
    hc, wc = R['shape']
    corners = np.array([[0, 0, 1], [wc, 0, 1], [0, hc, 1], [wc, hc, 1]], np.float64) @ M.T
    x0, y0 = np.floor(corners.min(0)).astype(int); x1, y1 = np.ceil(corners.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if x0 >= x1 or y0 >= y1: return
    qx, qy = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
    cx = Mi[0, 0] * qx + Mi[0, 1] * qy + Mi[0, 2]; cy = Mi[1, 0] * qx + Mi[1, 1] * qy + Mi[1, 2]
    Gx, Gy = warp_field(R, s)
    mx, my = (cx / STEP).astype(np.float32), (cy / STEP).astype(np.float32)
    srcx = cv2.remap(Gx, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-9999)
    srcy = cv2.remap(Gy, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-9999)
    art = edit_face(R['body'], R, s)
    body = cv2.remap(art, srcx, srcy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    # tail: its own layer behind the body, bent by an angle that grows toward the tip
    bx, by = TAIL_B[0] + P, TAIL_B[1] + P
    tb = M @ np.array([bx, by + s['crouch'], 1.]); tr_ = TAIL_L * 1.5 * z * s['approach']
    ty0, ty1 = int(np.clip(tb[1] - tr_ - y0, 0, y1 - y0)), int(np.clip(tb[1] + tr_ - y0, 0, y1 - y0))
    tx0, tx1 = int(np.clip(tb[0] - tr_ - x0, 0, x1 - x0)), int(np.clip(tb[0] + tr_ - x0, 0, x1 - x0))
    cxt, cyt = cx[ty0:ty1, tx0:tx1], cy[ty0:ty1, tx0:tx1]
    dxs, dys = cxt - bx, cyt - (by + s['crouch'])
    rr = np.hypot(dxs, dys) / TAIL_L
    wave = 6 * math.sin(2 * math.pi * .7 * t) * np.clip(rr, 0, 1.3)
    th = np.radians(s['tailBase'] + s['tailCurl'] * np.clip(rr, 0, 1.3) ** 2 + wave + np.clip(s['tail'][0] * .35, -30, 30) * np.clip(rr, 0, 1.3) ** 1.5)
    c, sn = np.cos(th), np.sin(th)
    tsx = (bx + c * dxs + sn * dys).astype(np.float32); tsy = (by + -sn * dxs + c * dys).astype(np.float32)
    layer = body
    if tsx.size:
        tail = cv2.remap(R['tail'], tsx, tsy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        sub = layer[ty0:ty1, tx0:tx1]; sub[:] = sub + tail * (1 - sub[..., 3:])
    layer = np.clip(layer, 0, None)
    # light it with the world: ambient tint, rim light from the upper left, local glows, gentle sharpen when enlarged
    post = smoothstep(CUT, CUT + 1.5, t)
    amb = np.array([1.0, .995, .985]) * (1 - post) + np.array([.985, .985, 1.0]) * post
    rgb, a = layer[..., :3] * amb, layer[..., 3]
    zeff = z * s['approach']
    if zeff > 1.1:
        k = min((zeff - 1.1) * .5, .45); rgb = rgb + k * (rgb - cv2.GaussianBlur(rgb, (0, 0), 1.2))
    sh = max(2, int(3 * zeff))
    rim = np.clip(a - np.pad(a, ((sh, 0), (sh, 0)))[:-sh, :-sh], 0, 1)
    rimc = np.array([1, .96, .9]) * .22 * (1 - post) + np.array([.78, .86, 1]) * .24 * post
    rgb = rgb + rim[..., None] * rimc
    for (lp, col, rad, inten) in scene.lights(t):
        lx, ly = w2s(*lp); d2 = ((qx - lx) ** 2 + (qy - ly) ** 2) / (rad * z) ** 2
        rgb = rgb + (np.exp(-d2 * 2) * inten * a)[..., None] * np.asarray(col)
    reg = F[y0:y1, x0:x1]
    reg[:] = reg * (1 - a[..., None]) + np.clip(rgb, 0, None)

SIG = RIG = SCENE = None

def init():
    global SIG, RIG, SCENE
    if SIG is None: SIG, RIG, SCENE = build_signals(), build_rig(), Scene()

def frame(i):
    init(); t = i / FPS
    s = {k: v[min(i, len(v) - 1)] for k, v in SIG.items()}
    F = SCENE.background(t, s)
    SCENE.fx_back(F, t, s)
    render_character(F, RIG, s, t, SCENE)
    SCENE.fx_front(F, t, s)
    F = F * SCENE.grain
    fin = smoothstep(0, .25, t) * (1 - smoothstep(DUR - .5, DUR - .02, t))
    F = SCENE.paper * (1 - fin) + F * fin
    return (np.clip(F, 0, 1) * 255 + .5).astype(np.uint8)

def main():
    os.makedirs(OUT, exist_ok=True)
    if '--sheet' in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index('--sheet') + 1].split(',')]
        init(); ims = [cv2.resize(frame(int(round(t * FPS))), (270, 480), interpolation=cv2.INTER_AREA) for t in ts]
        for im, t in zip(ims, ts): cv2.putText(im, f'{t:.2f}', (6, 20), cv2.FONT_HERSHEY_SIMPLEX, .55, (60, 40, 60), 1, cv2.LINE_AA)
        rows = [np.hstack(ims[k:k + 6] + [np.full((480, 270, 3), 255, np.uint8)] * (6 - len(ims[k:k + 6]))) for k in range(0, len(ims), 6)]
        cv2.imwrite(os.path.join(OUT, 'sheet.jpg'), cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        return
    if '--frame' in sys.argv:
        t = float(sys.argv[sys.argv.index('--frame') + 1]); init()
        cv2.imwrite(os.path.join(OUT, 'frame.png'), cv2.cvtColor(frame(int(round(t * FPS))), cv2.COLOR_RGB2BGR)); return
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe(); n = int(round(DUR * FPS)); path = os.path.join(OUT, 'yohaku.mp4')
    p = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', AUDIO, '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                          '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    init()
    with Pool(int(os.environ.get('JOBS', os.cpu_count()))) as pool:
        for k, im in enumerate(pool.imap(frame, range(n), chunksize=4)):
            p.stdin.write(im.tobytes())
            if k % 120 == 0: print(f'{k}/{n}', flush=True)
    p.stdin.close(); p.wait(); print('wrote', path)

if __name__ == '__main__':
    main()
