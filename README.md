# I'm Upping My P(doom) — ChatGPT × Claude (pixel-art music video)

An original pixel-art music video for the song "I'm Upping My P(doom)", starring pixel personifications of
**ChatGPT** (dark jade dragon) and **Claude** (long copper hair). It is a fictional artistic interpretation,
not an official depiction of either product or company.

* 156.65 s, 1920x1080, 60 fps, H.264 + AAC. Drawn at **320x180 native**; every pixel is an exact 6x6 block
  (nearest-neighbour only). Character drawings update at 8-15 fps; camera, particles and effects move at 60 fps.
* Output: `out/final_pdoom_pixel_chatgpt_claude.mp4` (local only: it contains the song, which stays out of the repo).

| Read | What it holds |
|---|---|
| [STORYBOARD.md](STORYBOARD.md) | the idea, the three through-lines, all 58 shots with their lyric times |
| [docs/SONG_MAP.md](docs/SONG_MAP.md) | how the timing was measured (ASR word onsets, 131.98 BPM kick grid, sections) |
| [docs/CHAPTER_GUIDE.md](docs/CHAPTER_GUIDE.md) | engine / character API and the pixel rules every shot follows |
| [qa/QA_NOTES.md](qa/QA_NOTES.md) | self-review notes, known compromises |
| `qa/identity_sheet.png`, `qa/overview.png`, `qa/ch0*_sheet.png` | identity sheet and contact sheets |
| `assets/sprites`, `assets/palettes` | exported sprite sheets, 2x portraits, palettes (.gpl + swatches) |

## Render it

Put the track at `audio/pdoom.mp3` (gitignored), then from `src/`:

```
pip install numpy pillow imageio-ffmpeg        # ffmpeg with libx264 must be on PATH
python3 render.py frames --workers 4           # native frames -> cache/native (about 5 min)
python3 render.py encode                        # -> out/final_pdoom_pixel_chatgpt_claude.mp4
python3 render.py sheet 23.6,25.7,140.3 --out ../qa/x.png   # contact sheets for QA
```

Code: `src/song.py` (timing master), `src/engine` (canvas, fonts, timeline, nearest-neighbour post stage),
`src/art` (hand-authored head cels, pose painter, portraits, ECU eyes), `src/scenes` (one module per chapter,
shared kit and props). The old "Forty-Two Folds" pre-production is kept in `legacy/`.
