#!/usr/bin/env python3
"""Builds motion.json (the Yohaku short's motion timeline) from the measured beat map.

Cues are musical, "bar:beat+frames" (60 fps frames), so every key stays locked to the song.
Bar 1 beat 1 is the first downbeat of the cut; bar 5 is the chorus downbeat.
If the audio is re-cut, replace BEATS and run: python3 build_motion.py
"""
import json, math, pathlib

FPS = 60
# Beat times (s from clip start) measured with librosa on audio/yohaku_cut.wav (123.05 BPM, slight drift).
BEATS = [0.274, 0.762, 1.226, 1.69, 2.178, 2.666, 3.153, 3.641, 4.105, 4.593, 5.057, 5.545, 6.032, 6.497,
         6.961, 7.426, 7.937, 8.424, 8.889, 9.376, 9.864, 10.328, 10.816, 11.303, 11.791, 12.255, 12.743,
         13.207, 13.695, 14.183, 14.647, 15.111, 15.622, 16.087, 16.574, 17.062, 17.526, 18.014, 18.502,
         18.966, 19.454, 19.918, 20.406, 20.893, 21.381, 21.868, 22.333, 22.82, 23.285, 23.773, 24.26]
DUR = 27.355
IBI = (BEATS[-1] - BEATS[0]) / (len(BEATS) - 1)


def t_of(cue):
    """'5:2.5+7' -> seconds. '0' is the first frame."""
    if cue == '0':
        return 0.0
    f = 0
    for s in '+-':
        if s in cue:
            cue, fr = cue.split(s)
            f = int(fr) * (1 if s == '+' else -1)
    bar, beat = cue.split(':')
    i = 4 * (int(bar) - 1) + float(beat) - 1
    k = math.floor(i)
    if 0 <= k < len(BEATS) - 1:
        t = BEATS[k] + (i - k) * (BEATS[k + 1] - BEATS[k])
    else:
        t = BEATS[0 if k < 0 else -1] + (i - (0 if k < 0 else len(BEATS) - 1)) * IBI
    return round(max(0.0, min(DUR, t + f / FPS)), 3)


# ---- continuous channels: (cue, value, ease). ease: io | o | i | back (overshoot) | lin | cut (jump on the cut)
CH = {
 # body (h = canonical character height)
 'x':        [('0',0,'io'),('5:1-2',0,'io'),('5:1+16',.32,'o'),('5:3',.42,'io'),('5:4',.55,'io'),('7:2',2.6,'lin'),('7:2.5',2.7,'o'),('9:1.5',2.78,'io'),('9:2.5',2.9,'io')],
 'y':        [('0',0,'io'),('3:4',.012,'o'),('3:4+10',0,'back'),('5:1-2',0,'io'),('5:1+7',.11,'o'),('5:1+16',0,'i'),('8:3',.015,'o'),('8:3+8',0,'i'),('8:4',.015,'o'),('8:4+8',0,'i'),('12:1+10',.01,'io'),('12:3',0,'io')],
 'bob':      [('0',0,'io'),('4:4+8',-.045,'io'),('5:1-3',-.047,'io'),('5:1-1',0,'o'),('5:1+20',-.05,'o'),('5:2+6',0,'back'),('5:3',-.02,'io'),('5:4',0,'io'),('9:2',-.03,'io'),('9:4+20',-.03,'io'),('10:1',0,'io')],
 'lean':     [('0',-.02,'io'),('4:4+8',.12,'io'),('5:1',.18,'o'),('5:1+16',.08,'io'),('5:3',.3,'o'),('5:4',.05,'back'),('6:1',.14,'io'),('7:2',-.04,'o'),('7:3',.1,'o'),('8:1',.02,'io'),('9:2',.2,'io'),('9:4',.16,'io'),('10:2',-.05,'o'),('11:3',.08,'io'),('12:1',-.06,'io'),('13:1',.02,'io')],
 'bodyYaw':  [('0',.25,'io'),('4:4',.35,'io'),('5:1',.6,'cut'),('8:1',.45,'io'),('9:1',.3,'io'),('11:2',.05,'io')],
 'shoulderRise': [('0',.25,'io'),('1:4',.1,'io'),('4:4+10',.6,'io'),('5:1',0,'o'),('10:1+12',.1,'io'),('10:2',.9,'o'),('10:3',.6,'io'),('10:3.5',.8,'io'),('10:4',.3,'io'),('11:1',.1,'io')],
 # head (yaw -1..1 = profile left..right, pitch deg + = down, roll deg + = toward her right shoulder)
 'headYaw':  [('0',.2,'io'),('2:1',-.7,'io'),('2:2.5',-.72,'io'),('2:3',.15,'o'),('2:4',.3,'io'),('2:4+5',.02,'io'),('2:4+10',.25,'io'),('2:4+15',.1,'io'),('4:4',.45,'io'),('5:1',.6,'cut'),('5:4',.3,'o'),('6:1',.6,'io'),('7:1',.4,'io'),('11:1+8',0,'io')],
 'headPitch':[('0',6,'io'),('1:1+6',16,'io'),('1:4',10,'io'),('2:1',4,'io'),('3:1',-6,'io'),('3:2',-10,'io'),('3:3',4,'io'),('3:4',0,'o'),('4:1',14,'io'),('4:3',22,'o'),('4:3+6',10,'back'),('4:4',2,'io'),('5:1-8',6,'io'),('5:1',0,'cut'),('7:1',-8,'io'),('8:1',12,'io'),('8:2+12',4,'o'),('9:1',14,'io'),('9:4',18,'io'),('11:1',0,'io'),('12:1',-18,'io'),('12:3',0,'io'),('13:1',2,'io')],
 'headRoll': [('0',0,'io'),('1:4',8,'io'),('2:1',2,'io'),('3:2',-6,'io'),('4:2',7,'io'),('4:4',0,'io'),('5:4',-6,'o'),('6:1',0,'io'),('7:2',12,'back'),('7:4',4,'io'),('10:2',10,'o'),('10:4',4,'io'),('11:3',10,'io'),('12:1',0,'io'),('13:1',6,'io')],
 # face (gaze -1..1; eyes lead the head by 4-8 f, so gaze keys sit earlier than head keys)
 'gazeX':    [('0',.1,'io'),('2:1-6',-.9,'o'),('2:3-4',.2,'o'),('4:4-6',.8,'o'),('5:1',.6,'cut'),('5:4',-.6,'o'),('6:1',.6,'o'),('7:1+10',.3,'o'),('11:1',0,'o')],
 'gazeY':    [('0',-.2,'io'),('1:1',-.8,'o'),('2:1',-.1,'o'),('3:1+8',.7,'o'),('3:3',-.3,'io'),('4:1',-.7,'o'),('4:4-6',0,'o'),('7:1+10',.5,'o'),('8:1',-.4,'o'),('9:1',-.5,'io'),('11:1',0,'o'),('12:1',.9,'io'),('12:3',0,'io')],
 'lid':      [('0',.9,'io'),('1:3',.75,'io'),('2:1',.9,'io'),('3:2',1.15,'o'),('3:4',1.2,'o'),('4:2',.8,'io'),('4:4',1.0,'io'),('5:3',1.15,'o'),('5:4',.85,'io'),('7:3',1.1,'o'),('7:4',.6,'io'),('8:1',1.0,'io'),('8:2+12',1.15,'o'),('9:1',.9,'io'),('9:4',.85,'io'),('10:1+12',.9,'io'),('10:2',0,'o'),('10:3',.3,'io'),('11:1',1.0,'io'),('12:1',1.15,'io'),('12:3',1.0,'io'),('12:4',.15,'io'),('13:1',.95,'io'),('13:2',.95,'io'),('13:2+12',.12,'io'),('13:2+22',.12,'io'),('13:2+36',.85,'io')],
 'eyeSmile': [('0',0,'io'),('4:2',.6,'io'),('4:3+10',.2,'io'),('5:4',.4,'io'),('6:1',.3,'io'),('9:1',0,'io'),('10:3',.9,'io'),('11:1',.2,'io'),('12:4',1,'io'),('13:1',.3,'io')],
 'pupil':    [('0',.85,'io'),('3:2',1.15,'io'),('4:4',1.05,'io'),('7:3',1.2,'o'),('8:1',1.0,'io'),('8:2+12',1.15,'io'),('9:4',1.0,'io'),('12:1',1.2,'io'),('13:1',1.05,'io')],
 'brow':     [('0',0,'io'),('3:2',.6,'o'),('3:4',.8,'o'),('4:2',.2,'io'),('4:4',-.1,'io'),('5:3',.5,'o'),('6:1',0,'io'),('8:2+12',.6,'o'),('9:1',0,'io'),('12:1',.5,'io'),('12:3',0,'io')],
 'browIn':   [('0',.35,'io'),('1:4',.2,'io'),('2:4',.1,'io'),('3:2',0,'io'),('5:3',.6,'o'),('5:4',.15,'io'),('6:1',0,'io'),('9:1',.7,'io'),('9:4',.3,'io'),('10:2',0,'io')],
 'mouthOpen':[('0',0,'io'),('3:4',.35,'o'),('4:1',.05,'io'),('4:4+10',.15,'io'),('5:1',.25,'o'),('5:2',.05,'io'),('5:3',.4,'o'),('5:4',.1,'io'),('6:1',.2,'io'),('7:4',.05,'io'),('8:2+12',.4,'o'),('9:1',.08,'io'),('10:3',.45,'o'),('10:4',.15,'io'),('12:1',.35,'io'),('12:3',.1,'io'),('12:4',.2,'io'),('13:1',.05,'io')],
 'mouthSmile':[('0',0,'io'),('1:3',-.15,'io'),('1:4',.1,'io'),('4:2',.6,'io'),('4:4',.25,'io'),('5:4',.5,'io'),('6:1',.55,'io'),('7:4',.4,'io'),('8:2+12',.7,'io'),('9:1',0,'io'),('9:4',.35,'io'),('10:2',.5,'io'),('10:3',.9,'io'),('11:1',.45,'io'),('11:3',.7,'io'),('12:4',1,'io'),('13:1',.6,'io')],
 'blush':    [('0',.15,'io'),('1:3',.5,'io'),('2:4',.3,'io'),('4:2',.45,'io'),('5:4',.45,'io'),('6:2',.3,'io'),('10:2',.55,'io'),('10:4',.85,'io'),('11:3',.7,'io'),('13:1',.6,'io')],
 # cat: earRot -1 flat back .. 0 neutral .. 1 perked; earSwivel -1 openings face back .. 0 front .. 1 side
 'earRot':   [('0',-.3,'io'),('1:2',-.45,'io'),('1:4',-.25,'io'),('3:1-8',.9,'back'),('3:4',1,'o'),('4:1',.4,'io'),('4:3',.7,'back'),('4:4',.8,'io'),('5:1+4',-.2,'o'),('5:1+18',.8,'back'),('5:3',.2,'o'),('6:1',.6,'io'),('7:1',.9,'back'),('9:1',.3,'io'),('10:1+12',.3,'io'),('10:2',-.6,'o'),('10:4',.4,'back'),('11:1',.8,'io'),('13:1',.7,'io')],
 'earSwivel':[('0',0,'io'),('2:1-10',-.8,'o'),('2:3',0,'o'),('7:1',.5,'o'),('7:3',0,'o'),('9:1',0,'io')],
 # tailBase -1 wrapped round her left ankle .. 0 hanging .. 1 vertical ("tail-up": confident)
 'tailBase': [('0',-1,'io'),('1:4',-.8,'io'),('2:4',-.3,'io'),('4:3',.2,'io'),('4:4+10',1,'o'),('5:1',.3,'cut'),('7:2',.7,'io'),('9:1',-.2,'io'),('9:4',0,'io'),('11:1',.9,'io')],
 'tailCurl': [('0',.2,'io'),('1:4',.5,'io'),('2:1',.2,'io'),('4:4+10',.7,'io'),('5:1',.3,'cut'),('7:2',.6,'io'),('9:1',.1,'io'),('11:1',.6,'io'),('13:1+30',.85,'io')],
 'tailPuff': [('0',0,'io'),('3:4',.35,'o'),('3:4+20',0,'io')],
 # sleeve paws: procedural alternating knead (0.9 Hz) while nervous
 'knead':    [('0',1,'io'),('3:2',0,'io')],
 # breathing: rate Hz, amp = shoulder travel in h
 'breathHz': [('0',.42,'io'),('2:4',.36,'io'),('4:4',.3,'io'),('6:1',.62,'io'),('8:4',.45,'io'),('9:1',.28,'io'),('11:1',.34,'io'),('13:1',.3,'io')],
 'breathAmp':[('0',.006,'io'),('4:4+10',.012,'io'),('5:1',.006,'o'),('6:1',.009,'io'),('9:1',.005,'io'),('13:1',.006,'io')],
 # camera: hFrac = character height / frame height; orbit deg (0 = square to her face); height in h; tilt deg (+ up)
 'camHFrac': [('0',.8,'io'),('2:1',.95,'io'),('3:1',1.35,'io'),('4:1',2.0,'io'),('4:4',2.15,'io'),('5:1',.62,'cut'),('7:2',.9,'io'),('9:1',1.25,'io'),('10:1',1.45,'io'),('11:1',1.7,'io'),('12:1',1.4,'io'),('12:3',1.7,'io'),('13:1',1.7,'io'),('13:4',1.95,'io')],
 'camOrbit': [('0',20,'io'),('5:1',60,'cut'),('8:1',60,'io'),('9:1',25,'io'),('11:1',5,'io')],
 'camHeight':[('0',.62,'io'),('4:1',.78,'io'),('5:1',.55,'cut'),('9:1',.6,'io'),('11:1',.72,'io')],
 'camTilt':  [('0',0,'io'),('12:1',10,'io'),('12:3',0,'io')],
}

# ---- trot: tiny double-time steps on every eighth note, 6:1 .. 7:1.5 (the "toko-toko" run)
for n in range(10):
    b = 6 + n * .5
    bar, beat = 6 + int((b - 6) // 4), (b - 6) % 4 + 1
    cue = f'{bar}:{beat:g}'
    CH['bob'].append((cue, -.022, 'o'))
    CH['bob'].append((f'{bar}:{beat + .25:g}', .01, 'io'))
CH['bob'].append(('7:2', 0, 'io'))

# ---- arm key drawings (authored poses; the engine morphs between them, never rotates cutouts)
ARMS = [  # (cue, R pose, L pose, transition frames)
 ('0','chestKnead','chestKnead',0), ('3:3-10','reachUp','chest',16), ('4:1','holdPrecious','holdPrecious',14),
 ('4:4+6','swingBackPrep','swingBackPrep',14), ('5:1','hopUp','hopUp',8), ('5:1+16','landBalance','landBalance',6),
 ('5:3','stumbleWindmill','stumbleWindmill',8), ('5:4','recoverChest','recoverChest',10), ('6:1','trotCycle','trotCycle',8),
 ('7:2','trotStop','trotStop',8), ('7:3','pawSwipe','chest',6), ('7:4','clapCatch','clapCatch',6), ('8:1','peekHands','peekHands',12),
 ('8:2+12','openHands','openHands',10), ('8:4','chestHold','chestHold',12), ('9:2','reachCupLow','reachCupLow',30),
 ('9:4','cupHold','cupHold',14), ('10:4','cupOneHand','cheekTouch',14), ('11:2','offerForward','offerForward',20),
 ('12:1','liftRelease','liftRelease',14), ('12:3','handsDownChest','handsDownChest',24), ('13:1','restChest','restChest',20)]

STEPS = [('1:2','R','toeTap'),('1:2+10','R','toeDown'),('5:1-2','LR','takeoff'),('5:1+16','R','land'),('5:1+18','L','land'),
         ('5:3','R','toeCatch'),('5:3+10','L','catchStep'),('5:4','R','plant')]
STEPS += [(f'{6 + int(n * .5 // 4)}:{(n * .5) % 4 + 1:g}', 'LR'[n % 2], 'trot') for n in range(10)]
STEPS += [('7:2','L','stop'),('7:2.5','R','feetTogether'),('9:1.5','L','slowStep'),('9:2.5','R','slowStep')]

EVENTS = [  # one-shot secondary accents and blinks (blink = 4 f close, 2 f hold, 7 f open unless noted)
 ('0.95','blink'), ('2:3','blink'), ('2:4','earFlick L'), ('2:4+3','earFlick R'), ('4:1','blink'), ('4:3','earFlick LR'),
 ('6:2','blink'), ('7:1-6','blink'), ('8:2+16','tailFlick'), ('8:3','tailFlick'), ('8:3.5','tailFlick'),
 ('9:1','blink slow 10f'), ('11:1-10','blink'), ('12:3','blink'), ('13:3+2','earFlick R')]

FX = [
 ('0','world','white paper page; a pencil margin line at her toes; slow dust motes'),
 ('3:1-12','dropBlue','a pale-blue watercolour bead falls from frame top, sways 0.3 Hz'),
 ('3:3+8','dropLand','bead lands on her right fingertip; tint creeps up the cuff over 30 f'),
 ('5:1+16','bloom','watercolour wash blooms from her footprint, radius 0 to 1.2 frame widths over 1.4 s, ease-out'),
 ('6:1','trail','every trot footstep blots a small colour pool that spreads for 0.6 s'),
 ('7:1','bubbles','6-9 colour beads float at 3 depths; the near ones are soft bokeh'),
 ('7:3','bounce','swiped bead bounces off her sleeve and hangs, bobbing'),
 ('8:2+12','glow','bead glow lights her face from below, tint of the bead, 35% key'),
 ('9:1','dropFading','a nearly transparent blue bead (alpha .35, slow flicker) drifts down'),
 ('9:4','dropSaved','cupped bead steadies and brightens to alpha .9'),
 ('10:1+12','dropPink','soft-focus pink bead boops her left cheek; tiny splash becomes the blush'),
 ('12:1+6','release','held colours rise and burst into a sky wash that fills the upper frame by 12:3'),
 ('13:1','drift','slow colour petals drift down through the last frames')]

RIG = {
 'followers': {'note': 'follow(): damped 2nd-order per body level, f Hz / zeta. Ears lead the eyes (cat read order).',
   'ears': [6.0, .45], 'eyes': [9.0, .7], 'head': [3.4, .55], 'shoulders': [2.8, .6], 'torso': [2.3, .65], 'hips': [2.0, .7]},
 'chains': {'note': 'solveChain(): [root f, tip f, root zeta, tip zeta]; stiffness falls toward the tip',
   'ahoge': [4.5, 3.5, .25, .2], 'hairFront': [2.8, 2.2, .4, .35], 'hairSide': [1.8, 1.4, .38, .3], 'hairRear': [1.2, .9, .35, .3],
   'earTips': [7.0, 5.5, .35, .3], 'ribbonTails': [2.2, 1.6, .3, .25], 'tail14': [2.4, 1.1, .6, .28],
   'sleeveCuffs': [2.0, 1.6, .4, .35], 'cardiganHem': [1.8, 1.5, .45, .4], 'skirtHem': [2.4, 2.0, .6, .55]},
 'limits': {'skirtHemSwayMax_h': .03, 'camHeightMin_h': .5, 'camTiltMin_deg': 0}}

def build():
 return {
 'title': 'Yohaku (余白の向こうへ) 24.7 s motion timeline', 'fps': FPS, 'duration': DUR,
 'audio': {'file': 'audio/yohaku_cut.wav', 'source': '余白の向こうへ (user-supplied track)', 'srcIn': 39.20, 'fadeIn': 0.12,
           'splice': {'at': 23.285, 'chorusFadeOut': 0.70, 'endingSrc': [137.88, 141.95], 'endingGainDb': 4,
                      'why': 'bar 12 sits on A; the song ends on A, so the final chord rings out instead of a mid-chorus fade'}},
 'tempo': {'bpm': 123.05, 'beats': BEATS, 'bars': [BEATS[i] for i in range(0, len(BEATS), 4)], 'chorusDownbeat': t_of('5:1')},
 'shots': [{'id': 'A', 'in': 0, 'out': t_of('5:1'), 'desc': 'one continuous push-in: full body to chest-up'},
           {'id': 'B', 'in': t_of('5:1'), 'out': DUR, 'desc': 'cut on the hop; tracking side-3/4, then a slow arc to frontal'}],
 'units': {'x,y,bob,camHeight': 'h (character height)', 'lean': 'forward tilt, rad', 'yaw': '-1..1 (0 front, 1 profile)',
           'pitch,roll,tilt,orbit': 'deg', 'face': '0..1 unless noted; lid 1 = open, 1.2 = wide'},
 'rig': RIG,
 'channels': {k: [{'cue': c, 't': t_of(c), 'v': v, 'ease': e} for c, v, e in sorted(ks, key=lambda q: t_of(q[0]))] for k, ks in CH.items()},
 'arms': [{'cue': c, 't': t_of(c), 'R': r, 'L': l, 'blendF': f} for c, r, l, f in ARMS],
 'steps': [{'cue': c, 't': t_of(c), 'foot': ft, 'kind': k} for c, ft, k in STEPS],
 'events': [{'cue': c, 't': float(c) if c[0].isdigit() and ':' not in c else t_of(c), 'kind': k} for c, k in EVENTS],
 'fx': [{'cue': c, 't': t_of(c), 'kind': k, 'desc': d} for c, k, d in FX]}


def main():
  p = pathlib.Path(__file__).with_name('motion.json')
  out = build()
  p.write_text(json.dumps(out, ensure_ascii=False, indent=1))
  print('wrote', p, 'chorus downbeat', out['tempo']['chorusDownbeat'], 'keys', sum(len(v) for v in CH.values()))


if __name__ == '__main__':
    main()
