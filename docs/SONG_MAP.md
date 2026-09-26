# Song map (how the timing was measured)

The audio file is the timing master; nothing was stretched or re-timed. All numbers live in `src/song.py`.

* **Word onsets**: NVIDIA Parakeet-TDT 0.6B (sherpa-onnx, int8) on overlapping 16 s windows, token timestamps at
  80 ms resolution; the text was cross-checked with Whisper small.en and the published lyrics. Every visual event
  keyed to a word uses `song.word_time(line, word)`.
* **Beat grid**: kick-drum onsets (low-band spectral flux) fitted to **131.98 BPM, phase 0.238 s** (213 of 224
  kicks within 30 ms). Bar m starts at `0.238 + 1.81846 m`; bar 1 = 2.056 s is the first sung word.
* **Sections** (RMS / low-band energy): intro pickup 0.24-2.06 · verse 1 · chorus 1 22.8 · break 35.8 ·
  verse 2 38.6 · chorus 2 59.1 · energy drop 88.0 · half-energy chorus 3 95.3 · rap 110.1 · chorus 4 124.5 ·
  **band stop 138.44** (a cappella "all ... for") · **slam 140.26** on "show?" · outro vocalise 141.1-152.3 ·
  decay from bar 84 = 152.99 · **audible hard stop 154.75** · silence to 156.65.

## Opening and ending alignment

| time | audio | picture |
|---|---|---|
| 0.238-1.83 | eight pickup eighths | jade and amber cursors blink on alternate eighths and step together |
| 1.94-2.056 | last sixteenth | a white CRT line opens |
| 2.056 / 2.08 | downbeat, "I" | white flash, Claude's eyes open on "I" |
| 2.80 / 3.68 | "sparks", "AGI" | lightning across ChatGPT's iris; star-flare pupil |
| 137.52 | "Was" | spotlight snaps on the closed curtain |
| 138.44-138.48 | band stops, "all" | dust freezes; the curtain twitches |
| 139.24 | "for" | the curtain starts to lift |
| 140.08-140.26 | "show?", band slams | curtain flies, flash, bow, confetti |
| 142.08 / 145.72 / 147.54 / 149.35 | bars 78 / 80 / 81 / 82 | empty seats / the kid / they look / the waves |
| 152.99 + beats | decay | stage light banks go out one per beat, marquee bulbs die |
| 154.75 | audio stops | hard cut to black |
| 155.40-156.65 | silence | "p(doom) = ?" with the two cursors |

Motion design: every beat in the choruses and rap gets a small camera punch (stronger on the downbeat,
lighter in the verses, none in the bridge and finale), plus flashes and shakes on keyed words and flashes or
dissolves at section boundaries (`src/engine/film.py`, `src/film_def.py`).
