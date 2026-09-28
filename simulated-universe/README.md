# Where We Live Is a Simulated Universe

An original pixel-art music video, about 2:53 long. It is a metaphor for our own human world:

- the world we live in is a simulation;
- there are no gods running it;
- death is a return to universal consciousness.

It follows one ordinary New Yorker, Iris, from her first blurry frame to her last, and one step past it.

**Status: design, awaiting review.** No song audio, character art or frames exist yet.

| Read | What it holds |
|---|---|
| [TREATMENT.md](TREATMENT.md) | the idea, the seven rules of the world, the story in three movements, motifs, the visual system and the tone rules |
| [SONG.md](SONG.md) | the song: full lyrics, form, key plan, harmony, the lullaby motif, the heartbeat clock, instrumentation, a brief for a music generator, and the beat map |
| [STORYBOARD.md](STORYBOARD.md) | 45 shots with bar, time and frame, what happens, the world's resolution in each shot, and transitions |
| [CHARACTERS.md](CHARACTERS.md) | model-sheet briefs for every character and set, written as a hand-off for whoever draws them |

## The logline

> Her grandmother taught her that if you turn around fast, you can catch the world still loading. When her grandmother dies, Iris climbs past the edge of the sky to find whoever runs it and finds an empty chair. She finds the rest of the answer years later, on a subway platform, when a stranger hums her grandmother's song.

## Key numbers

| | |
|---|---|
| Length | 104 bars, 173.3 s (2:53.3) |
| Tempo | 144 BPM, 4/4, fixed. At 60 fps a beat is exactly 25 frames and a bar exactly 100 frames. |
| Key | E♭ major. The home chord (E♭ in root position) is held back until bar 97, the moment of return. |
| Picture | 320×180 native pixel art, scaled ×6 (nearest neighbour) to 1920×1080, 60 fps |
| The device | **Resolution is consciousness.** A newborn sees the world at 16×9, and each life stage sharpens it on the beat. The world draws detail only where someone is looking. |

## Who makes what

| Part | Owner |
|---|---|
| Story, world rules, lyrics, composition, storyboard | Claude (this folder) |
| Song audio | composed by Claude as a demo, or generated from the brief in [SONG.md](SONG.md) §8. The final WAV is locked before picture timing is frozen. |
| Character model sheets | drawn from [CHARACTERS.md](CHARACTERS.md). These are new characters, not the user's OC. |
| Pixel sprites, engine additions, animation, QA, render | Claude, reusing the pixel engine from the P(doom) video (branch `claude/great-pascal-z12nnf`, `src/engine`) |

The order of work is in [TREATMENT.md §8](TREATMENT.md#8-production-plan).
