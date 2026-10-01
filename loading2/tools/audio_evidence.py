"""Audio evidence for the disputed / unassigned intervals of the locked track.

Sources (all local, reproducible):
  mix   : scratchpad/audio/song.wav  = 44.1 kHz decode of Loading_P0_endfix_candidate01.mp3
          (SHA256 of the mp3 34e1d49b4cdeaceab6d3ab841f0eaca01d891329b7edb9458ff99b6d987d857f)
  vocal : scratchpad/audio/stem_0.wav = UVR-MDX-NET-Voc_FT separation (sherpa-onnx) of that decode
  ASR   : sherpa-onnx Whisper large-v3 int8, language=en, 3 s windows every 1 s on the vocal stem
          (docs/evidence/asr_3s_windows_0-160.txt, asr_3s_windows_158-213.txt)
  pitch : librosa.pyin fmin 80 fmax 900 Hz, 16 kHz, hop 20 ms; level = RMS dB re track max
No human listening is represented here.
"""
import sys, os, re
import numpy as np, soundfile as sf, librosa
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SP = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad/audio'
EV = '/home/user/OC/loading2/docs/evidence'
y, sr = sf.read(os.path.join(SP, 'stem_0.wav'), always_2d=True); y = y.mean(1)
m, _ = sf.read(os.path.join(SP, 'song.wav'), always_2d=True); m = m.mean(1)
asr = []
for f in ('asr_3s_windows_0-160.txt', 'asr_3s_windows_158-213.txt'):
    for line in open(os.path.join(EV, f)):
        g = re.match(r'\s*([\d.]+)-\s*([\d.]+)\s*(.*)', line)
        if g:
            asr.append((float(g.group(1)), float(g.group(2)), g.group(3).strip()))
gmax = 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)

WINDOWS = [(158.0, 172.0, 'Bridge end -> break -> "And one day" (main Final Chorus lines F01-F04 disputed here)'),
           (176.0, 183.0, '"...in the art" -> unassigned 2:59.5-3:00.0 -> "maybe"'),
           (190.0, 213.41, '"...only a return" -> whisper -> unassigned 3:20.0-3:22.5 -> "still loading" -> 3:23.7-3:24.0 -> tail')]
rows = []
fig, axes = plt.subplots(len(WINDOWS), 1, figsize=(16, 4.2 * len(WINDOWS)))
for ax, (a, b, title) in zip(axes, WINDOWS):
    seg = y[int(a * sr):int(b * sr)]
    y16 = librosa.resample(seg, orig_sr=sr, target_sr=16000)
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y16, n_fft=1024, hop_length=160)), ref=np.max)
    f = librosa.fft_frequencies(sr=16000, n_fft=1024)
    keep = f <= 4000
    ax.imshow(S[keep], origin='lower', aspect='auto', extent=[a, b, 0, 4000], cmap='magma', vmin=-70, vmax=0)
    f0, vflag, vprob = librosa.pyin(y16, fmin=80, fmax=900, sr=16000, frame_length=1024, hop_length=320)
    t = a + np.arange(len(f0)) * 320 / 16000
    ax.plot(t, np.where(vflag, f0, np.nan), color='cyan', lw=1.5, label='pitch (pyin, voiced)')
    rms = librosa.feature.rms(y=y16, frame_length=1024, hop_length=320)[0]
    db = 20 * np.log10(rms + 1e-9) - gmax
    ax2 = ax.twinx(); ax2.plot(t[:len(db)], db, color='white', lw=0.8, alpha=0.8); ax2.set_ylim(-60, 25); ax2.set_ylabel('vocal level dB re mean')
    for (wa, wb, txt) in asr:
        if wa >= a - 1 and wb <= b + 1:
            ax.text((wa + wb) / 2, 3700 - 260 * (int(wa) % 4), txt[:22], color='lime', fontsize=7, ha='center')
    for (u0, u1) in ((179.5, 180.0), (200.0, 202.5), (203.7, 204.0)):
        if a <= u0 <= b:
            ax.axvspan(u0, u1, color='yellow', alpha=0.25)
    ax.set_title(title, fontsize=10); ax.set_ylabel('Hz (vocal stem)'); ax.set_xlabel('seconds in locked track')
    for i in range(len(t[:len(db)])):
        if i % 5 == 0:
            rows.append((round(t[i], 2), round(float(db[i]), 1), round(float(vprob[i]), 2), (round(float(f0[i]), 1) if vflag[i] else '')))
axes[0].legend(loc='upper right', fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(EV, 'audio_evidence_ending.png'), dpi=80)
with open(os.path.join(EV, 'vocal_level_pitch_0p1s.csv'), 'w') as fh:
    fh.write('t_s,vocal_db_re_mean,voiced_prob,f0_hz\n')
    for r in rows:
        fh.write(','.join(str(v) for v in r) + '\n')
print('ok', len(rows))
