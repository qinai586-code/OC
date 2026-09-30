"""Measure a mouth-opening curve from the master for given singer windows.

This is signal measurement, not listening. The curve is a guess at when a voice is
articulating. The mid channel's 300-3500 Hz harmonic energy, gated by pYIN voicing in
the singer's range, is pushed toward syllable onsets (a fast envelope minus a slow one),
so reverb tails and pads hold the mouth less than the raw level would.

Usage: python3 lipsync.py MASTER.mp3 OUT.json  (windows below; the singer comes from the lyric sheet)
"""
import sys, json, subprocess, numpy as np, librosa, scipy.signal as ss, imageio_ffmpeg

SR, FPS = 22050, 100
# (singer, t0, t1, f0 range): verse 1, A. The song stops for 13.4-14.45, so the mouth rests there.
WINDOWS = [('A', 7.40, 13.40, (220, 1100)), ('A', 14.45, 21.5, (220, 1100))]

def load(path):
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-i', path, '-t', '40', '-ac', '2',
                          '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32).reshape(-1, 2)
    return y.mean(1)                                             # mid: the lead vocals sit in the centre

def follower(x, att, rel):
    a, r = np.exp(-1 / (att * FPS)), np.exp(-1 / (rel * FPS)); out = np.zeros_like(x); v = 0.0
    for i, xi in enumerate(x):
        v = a * v + (1 - a) * xi if xi > v else r * v + (1 - r) * xi; out[i] = v
    return out

def curve(y, t0, t1, frange, span=(6.0, 22.0)):
    """Normalised over the whole span, so quiet and loud lines are comparable; then cut to [t0, t1)."""
    seg = y[int(span[0] * SR):int(span[1] * SR)]
    h = librosa.effects.harmonic(seg, margin=2.0)
    band = ss.sosfilt(ss.butter(4, [900, 4000], btype='band', fs=SR, output='sos'), h)   # vocal presence band
    hop = SR // FPS
    db = 20 * np.log10(librosa.feature.rms(y=band, frame_length=1024, hop_length=hop)[0] + 1e-6)
    _, _, vp = librosa.pyin(band, fmin=frange[0], fmax=frange[1], sr=SR, frame_length=2048, hop_length=hop * 4)
    vp = np.repeat(np.nan_to_num(vp), 4)
    n = min(len(db), len(vp)); db, vp = db[:n], vp[:n]
    lin = np.clip((db - np.percentile(db, 15)) / (np.percentile(db, 97) - np.percentile(db, 15) + 1e-6), 0, 1)
    fast, slow = follower(lin, 0.015, 0.07), follower(lin, 0.02, 0.45)
    art = np.clip(fast - 0.5 * slow, 0, None); art /= np.percentile(art, 97) + 1e-6
    o = np.clip(art, 0, 1) * np.clip(0.35 + vp * 1.3, 0, 1)      # voicing is a soft gate: breathy takes read unvoiced
    o = follower(o, 0.02, 0.06)                                  # mouths open fast, close a little slower
    t = span[0] + np.arange(n) / FPS; m = (t >= t0) & (t < t1)
    return t[m], np.clip(o[m], 0, 1)

def flaps(t, o, fps=30, lead=0.07, hold=3):
    """Kuchipaku: three held mouths (0 closed, 1 half, 2 open) per video frame.

    The mouth leads the sound by about 2 frames, changes at most every `hold` frames (on threes),
    and uses hysteresis so it does not chatter between two shapes. In the middle of a phrase a
    short dip only half-closes the mouth: sung vowels are held.
    """
    tf = np.arange(t[0], t[-1], 1 / fps)
    v = np.interp(tf + lead, t, o)
    v = np.convolve(np.pad(v, 1, mode='edge'), np.ones(3) / 3, mode='valid')
    phrase = np.convolve(np.pad(v, 4, mode='edge'), np.ones(9) / 9, mode='valid') > 0.22
    st, cur, since = [], 0, hold
    for x, ph in zip(v, phrase):
        up2, dn2, up1, dn1 = 0.55, 0.40, 0.20, 0.10
        want = 2 if x > (dn2 if cur == 2 else up2) else (1 if x > (dn1 if cur >= 1 else up1) else 0)
        if want == 0 and ph: want = 1
        if want != cur and since >= hold: cur, since = want, 0
        since += 1; st.append(cur)
    st = np.array(st)
    # a singer breathes in through a half-open mouth just before a phrase (after >= 0.6 s of rest)
    on = [i for i in range(1, len(st)) if st[i] > 0 and st[i - 1] == 0 and (st[max(0, i - 18):i] == 0).all() and i >= 18]
    for i in on: st[i - 8:i] = 1
    # no shape is held for less than `hold` frames: a too-short run takes the previous shape
    i = 1
    while i < len(st):
        j = i
        while j < len(st) and st[j] == st[i]: j += 1
        if st[i] != st[i - 1] and j - i < hold and j < len(st): st[i:j] = st[i - 1]
        i = j
    return tf, st

if __name__ == '__main__':
    y = load(sys.argv[1]); out = {'fps': FPS, 'note': 'measured from the master, not listened; see lipsync.py', 'tracks': []}
    for who, t0, t1, fr in WINDOWS:
        t, o = curve(y, t0, t1, fr)
        tf, fl = flaps(t, o)
        out['tracks'].append({'who': who, 't0': t0, 'open': [round(float(v), 3) for v in o],
                              'flaps30': ''.join(map(str, fl))})
        print('   flaps', ''.join('_-O'[v] for v in fl[::3]))
        line = ''.join(' .:-=+*#'[min(7, int(v * 8))] for v in o[::10])      # 10 per second
        print(f'{who} {t0:6.2f}-{t1:6.2f} |{line}|')
    json.dump(out, open(sys.argv[2], 'w'))
