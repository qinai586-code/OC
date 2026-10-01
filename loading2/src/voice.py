"""Vocal features for lip-sync and for typing words of light, from the isolated vocal stem.

Per video frame (24 fps, sampled at 4x and filtered):
  open  - how far the jaw opens (loudness, more for open vowels: higher F1)
  wide  - front vowels (e, i: high F2 / F1) spread the mouth; back vowels (o, u) round it
  fric  - fricatives (s, sh, f): teeth nearly closed
Onsets (syllable starts) drive the typing of key words.
"""
import json
import numpy as np
import soundfile as sf
from lw import SCRATCH, w2, FPS

OUT = w2('voice.npz')


def build():
    import librosa
    y, sr = sf.read(f'{SCRATCH}/audio/stem_0.wav', always_2d=True)
    y = y.mean(1).astype(np.float32)
    sub = 4
    hop = int(round(sr / (FPS * sub)))
    n_fft = 2048
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop, center=True)) ** 2
    f = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    def band(a, b):
        return S[(f >= a) & (f < b)].sum(0) + 1e-10
    E1, E2, E3 = band(250, 950), band(1000, 2900), band(4000, 9500)
    tot = band(80, 9500)
    db = 10 * np.log10(tot)
    hi = np.percentile(db, 97)
    lo = hi - 38
    loud = np.clip((db - lo) / (hi - lo), 0, 1)
    m1 = (f >= 250) & (f < 1200)
    f1 = (S[m1] * f[m1, None]).sum(0) / (S[m1].sum(0) + 1e-10)
    f1n = np.clip((f1 - 380) / 420, 0, 1)
    ratio = np.log10(E2 / E1)
    voiced = loud > 0.25
    r0, r1 = np.percentile(ratio[voiced], [10, 90])
    wide = np.clip((ratio - r0) / (r1 - r0), 0, 1)
    fr = np.log10(E3 / (E1 + E2))
    q0, q1 = np.percentile(fr[voiced], [60, 97])
    fric = np.clip((fr - q0) / (q1 - q0), 0, 1) * (loud > 0.15)
    open_ = np.clip((loud - 0.22) / 0.6, 0, 1) ** 0.85 * (0.55 + 0.45 * f1n) * (1 - 0.75 * fric)

    def follow(x, att=0.65, rel=0.35):
        o = np.zeros_like(x)
        v = 0.0
        for i, s in enumerate(x):
            k = att if s > v else rel
            v += (s - v) * k
            o[i] = v
        return o
    open_s = follow(open_)
    wide_s = follow(wide, 0.3, 0.3)
    fric_s = follow(fric, 0.5, 0.4)
    # resample to frame rate, with the mouth leading the sound by ~1 frame
    t = np.arange(len(open_s)) * hop / sr - 1.0 / FPS
    onsets = librosa.onset.onset_detect(y=y, sr=sr, hop_length=256, backtrack=False, units='time', delta=0.08)
    np.savez(OUT, t=t.astype(np.float32), open=open_s.astype(np.float32), wide=wide_s.astype(np.float32),
             fric=fric_s.astype(np.float32), loud=loud.astype(np.float32), onsets=np.asarray(onsets, np.float32))
    print('voice features', len(t), 'onsets', len(onsets))


_V = None


def V():
    global _V
    if _V is None:
        import os
        if not os.path.exists(OUT):
            build()
        _V = dict(np.load(OUT))
    return _V


def at(t):
    """(open, wide, fric) at time t."""
    v = V()
    return tuple(float(np.interp(t, v['t'], v[k])) for k in ('open', 'wide', 'fric'))


def onsets(a, b):
    v = V()['onsets']
    return v[(v >= a) & (v < b)]


if __name__ == '__main__':
    build()
    v = V()
    for a, b in ((52.5, 56.1), (98.5, 102.1), (141.7, 143.2)):
        m = (v['t'] >= a) & (v['t'] < b)
        print(a, b, 'open>0.3 %.2f' % (v['open'][m] > 0.3).mean(), 'onsets', np.round(onsets(a, b), 2)[:20])
