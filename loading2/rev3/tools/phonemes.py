"""Measure the sung sounds in the singing excerpt (52.2-56.5 s) from the vocal stem.

Sources: vocal stem stem_0.wav (UVR-MDX-NET-Voc_FT via sherpa-onnx from song.wav, the 44.1 kHz decode of
the locked mp3). Measurements only: RMS level, pyin f0/voicing, high-band (4-10 kHz) energy ratio for
fricatives (f, v, s), and LPC formant estimates F1/F2 for vowel openness/rounding. Writes
rev3/docs/phoneme_evidence.png and rev3/docs/phoneme_features.csv. No listening is involved.
"""
import numpy as np, librosa, soundfile as sf, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

STEM = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad/audio/stem_0.wav'
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
T0, T1 = 52.2, 56.5
y, sr = sf.read(STEM, always_2d=True)
y = y.mean(1)
seg = y[int(T0 * sr):int(T1 * sr)]
seg16 = librosa.resample(seg, orig_sr=sr, target_sr=16000)
sr16 = 16000
hop = 160                       # 10 ms
f0, vflag, vprob = librosa.pyin(seg16, fmin=150, fmax=1000, sr=sr16, frame_length=1024, hop_length=hop)
rms = librosa.feature.rms(y=seg16, frame_length=640, hop_length=hop)[0]
ref = np.sqrt(np.mean(y ** 2))
db = 20 * np.log10(rms / ref + 1e-9)
S = np.abs(librosa.stft(seg, n_fft=2048, hop_length=int(sr * 0.01)))
freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
hi = S[(freqs > 4000) & (freqs < 10000)].sum(0)
tot = S[(freqs > 80) & (freqs < 10000)].sum(0) + 1e-9
hiratio = hi / tot


def formants(frame, sr, order=14):
    frame = frame * np.hamming(len(frame))
    frame = np.append(frame[0], frame[1:] - 0.63 * frame[:-1])
    a = librosa.lpc(frame, order=order)
    r = [z for z in np.roots(a) if np.imag(z) >= 0.01]
    ang = np.arctan2(np.imag(r), np.real(r))
    fr = sorted(ang * sr / (2 * np.pi))
    bw = [-0.5 * sr / np.pi * np.log(abs(z)) for z in r]
    cand = [f for f, b in sorted(zip(ang * sr / (2 * np.pi), bw)) if 250 < f < 3500 and b < 500]
    return (cand + [np.nan, np.nan])[:2]


y11 = librosa.resample(seg, orig_sr=sr, target_sr=11025)
n = len(f0)
F = np.full((n, 2), np.nan)
for i in range(n):
    c = int(i * 0.01 * 11025)
    fr = y11[c:c + 330]
    if len(fr) == 330 and db[min(i, len(db) - 1)] > -30:
        F[i] = formants(fr, 11025)
t = T0 + np.arange(n) * 0.01
m = min(n, len(db), len(hiratio))
np.savetxt(os.path.join(D, 'phoneme_features.csv'),
           np.c_[t[:m], db[:m], np.nan_to_num(f0[:m]), vprob[:m], hiratio[:m], F[:m, 0], F[:m, 1]],
           delimiter=',', header='t,level_db_re_track_rms,f0_hz,voiced_prob,hiband_ratio,F1_hz,F2_hz', fmt='%.3f', comments='')

fig, ax = plt.subplots(4, 1, figsize=(18, 13), sharex=True)
Sdb = librosa.amplitude_to_db(S, ref=np.max)
ax[0].imshow(Sdb, origin='lower', aspect='auto', extent=[T0, T0 + S.shape[1] * 0.01, 0, sr / 2], cmap='magma', vmin=-70)
ax[0].set_ylim(0, 8000); ax[0].set_ylabel('Hz (stem)')
ax[0].plot(t, f0, c='cyan', lw=1.5)
ax[1].plot(t[:len(db)], db[:n], c='k'); ax[1].set_ylabel('level dB'); ax[1].axhline(-30, c='gray', ls=':')
ax[2].plot(t[:len(hiratio)], hiratio[:n], c='m'); ax[2].set_ylabel('4-10 kHz ratio\n(fricatives)')
ax[3].plot(t, F[:, 0], '.', c='r', ms=3, label='F1 (openness)'); ax[3].plot(t, F[:, 1], '.', c='b', ms=3, label='F2 (front/back)')
ax[3].set_ylabel('LPC formants Hz'); ax[3].legend(loc='upper right'); ax[3].set_ylim(0, 3200)
for a in ax:
    a.set_xticks(np.arange(52.2, 56.55, 0.1), minor=True); a.grid(True, which='both', axis='x', alpha=0.3)
ax[3].set_xticks(np.arange(52.2, 56.6, 0.2))
ax[3].set_xlabel('seconds in the locked track')
fig.suptitle('Measured features 52.2-56.5 s (vocal stem). Author text: "What if we live in a simulated universe:" - measurements only, no listening')
plt.tight_layout(); plt.savefig(os.path.join(D, 'phoneme_evidence.png'), dpi=80)
print('ok', n)
