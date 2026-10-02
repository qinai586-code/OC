# Motion pilot P1-S1 (v2): superseded by `PILOT_S1_SHEET_v3.md`

**Do not generate from this sheet.** Its action ran 2.2 s for a 1.667 s slot. v3 resolves that.

This replaces `PILOT_S1_SHEET.md`, which used the earlier S1 candidate.

| field | value |
|---|---|
| shot | P1-S1: A notices the light |
| song time used | **7.500–9.167** (frames 180–219 at 24 fps), **1.667 s usable**. The music is locked and never retimed |
| first frame | `refs_in2/P1_S1_original_reference_v8.png`: owner-approved, unmodified (1672×941, sha256 0d4bb512df959b04) |
| end frame | **none** (no morph endpoints) |
| extra reference images | none. Do not attach S2 or S3 to this clip. If the interface has a character-reference slot, the model sheet (`images/1.webp`) is the only allowed identity reference. Using it is optional; test first without it |
| generated duration | the shortest option ≥ 3.0 s (**PENDING**: check the interface) |
| edit placement | the 1.667 s that ends just after her hand begins to lift is placed at 7.500, and the cut to S2 continues that lift (match on action). Handles are trimmed, never compressed; speed change ≤ 10%, otherwise regenerate |

## Action, timed inside the clip

| time | action |
|---|---|
| 0.0–0.8 s | Nearly still: breathing, a faint drift in her hair and coat. The orb hangs at the upper right. Her open right hand rests where it is. |
| 0.8–2.6 s | The orb drifts slowly down-left. It stays in the upper right, above her eye line, and never crosses her face; it ends about at the green arrow's tip on the board. Her eyes follow first; her head follows a few frames later with a small downward tilt (about 5–12°). Lips stay softly parted. Hair, ribbon and coat lag slightly and settle. |
| 2.6–3.0 s | Her open right hand begins to lift slightly toward the light, fingers easing open. This is the cut point into S2. |
| 3.0 s to the end | Quiet handle. |

## Prompt (owner adapts the wording to the interface)

> Fixed camera. 2D anime cel-shaded night scene above the Earth, exactly as in the first frame.
> The horned girl in right profile watches the single small golden light in the upper right of the
> sky. The light drifts slowly down and to the left, staying above her eye line. Her eyes follow it
> first, then her head tilts down slightly. Near the end, her open right hand lifts a little toward
> the light, fingers easing open. Her lips stay softly parted in quiet wonder; she does not speak.
> Gentle breathing. Her long black hair with teal ends, the dark ribbon and the loose coat sway
> slightly and settle. Stars stay steady; the clouds barely drift. Keep her face, horns, hair clip,
> hairstyle and outfit exactly as in the first frame. One continuous shot with quiet moments at the
> start and end.

**Negative (if supported):** talking, mouth movement, lip-sync, camera movement, zoom, pan, cut,
second light, extra orb, light passing in front of her face, star flicker, extra characters, extra
hands or fingers, changing horns, moving or changing hair clip, hairstyle change, outfit change, 3D
render, photorealism, text, watermark, heavy blur, face distortion.

## Settings (PENDING the real interface; record what was used)

- **Model:** Seedance 2.5 (exact variant name).
- **Mode:** image-to-video, first frame only.
- **Aspect:** 16:9. **Resolution:** the highest offered without upscaling the input.
- **fps:** 24 if selectable.
- **Fixed camera:** on, if offered. **Motion strength:** low to medium.
- **Audio:** off or ignored.
- **Outputs:** 1 per attempt. **Seed:** record it.
- **Attempts:** the owner decides; I suggest at most 3.
- **Return:** the original downloaded file (no re-encode), plus the settings and seed.

## Acceptance (judged on the returned video)

1. **Identity is stable in every frame** (checked against the first frame and the model sheet):
   horns, hairstyle and ribbon, the clip (no drift or flicker), teal eyes, outfit.
2. **Single light:** it moves down-left and stays above her eye line. No second light; no reset.
3. **Motion:**
   - the eyes lead and the head follows (5–12°);
   - the hand lift at the end is small and anatomically plausible;
   - hair and coat lag and settle;
   - no jitter, pops or morphing.
4. **No speaking.** The mouth stays softly parted.
5. **Fixed camera** (≤ 2% drift). No cuts.
6. **Style:** 2D cel look, night palette. No text or watermark.
7. **Duration:** covers 1.667 s usable plus ≥ 0.5 s handles. The fit to 7.500 needs ≤ 10% speed change.

## When the clip comes back

```
python3 rev3/tools/seedance_check.py <clip.mp4> --name P1-S1_tryN --in <seconds> --song 7.500 --dur 1.667 \
    --mouth 565,325,600,360
```

**Measured:** container facts, the light count and path per frame, camera drift, mouth-region
change, and frame-change spikes.

**Output:** a frame strip, plus a 24 fps fit at 7.500 over the unchanged music with local and song
timecode.

**Not certifiable by me:** smoothness at normal speed and the emotional read. Those need your
playback review.
