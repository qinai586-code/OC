# Forty-Two Folds (四十二回、折ったら)

An original animated music short, about 2:05 long, starring fictional anime personifications of ChatGPT and Claude. It is not an official depiction of either product or company.

**Status: pre-production, awaiting review.** No film frames have been rendered yet.

| Read | What it holds |
|---|---|
| [docs/TREATMENT.md](docs/TREATMENT.md) | theme, the two characters, their relationship, core idea, animation, camera and transition plans |
| [docs/SONG.md](docs/SONG.md) | the song concept, the full original lyrics, the production brief (150 BPM, D major, instrumentation, vocals) and the beat map |
| [STORYBOARD.md](STORYBOARD.md) | 37 shots with timings, the reads for each, camera and transitions |
| [docs/TECH.md](docs/TECH.md) | the 60 fps engine, the motion contract, the scale system, the character interface (character design is handed to ChatGPT) and the QA plan |
| [shorts/yohaku/MOTION.md](shorts/yohaku/MOTION.md) | a separate 27.4 s clip for the user's cat-eared OC: the final video (`shorts/yohaku/render/yohaku.mp4`), the music cut, the motion design and the renderer |

The engine is based on [ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) (MIT; see LICENSE), reorganised for 60 fps continuous motion.

The character reference art the user supplied is in `reference/`.
