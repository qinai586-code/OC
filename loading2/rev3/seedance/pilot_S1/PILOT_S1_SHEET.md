# Pilot P1-S1: ready for the owner to generate (not submitted; no credits used)

| field | value |
|---|---|
| shot | P1-S1: A notices the light |
| song time used | **7.500–9.167** (frames 180–219 at 24 fps), **1.667 s usable** |
| first frame | `refs_in/P1_S1_LOOK_UP_CANDIDATE.png`, unmodified (1672×941, sha256 093a344bad794ce9) |
| end frame | none |
| extra reference images | none for this pilot. If the interface has a character-reference slot, leave it empty rather than mixing in the S2/S3 candidates |
| generated duration | the shortest option ≥ 3.0 s (**PENDING**: check the interface) |
| handles inside the clip | 0.0–0.8 s quiet; action 0.8–2.8 s; ≥ 0.5 s quiet after |
| edit placement | the 1.667 s that ends as her gaze starts to lower is placed at 7.500. Handles are trimmed, never compressed. Speed change ≤ 10%, otherwise regenerate. The music is unchanged |

## Action, timed inside the clip

| time | action |
|---|---|
| 0.0–0.8 s | Almost still: breathing, a faint hair drift. The orb hangs at the upper right. |
| 0.8–2.8 s | The orb drifts slowly down-left from the upper right, staying **above her eye line and right of her face**, to about two-thirds of the way toward the frame centre. Her eyes follow first; her head follows a few frames later with a small downward tilt (about 5–15°). Lips stay softly parted. Hair and ribbon tails lag slightly and settle. |
| 2.8 s to the end | She keeps watching, nearly still. |

## Prompt

> Fixed camera, 2D anime cel-shaded night scene, exactly as in the first frame. The horned girl in
> right profile watches the single small golden light in the upper right of the sky. The light
> drifts slowly down and to the left, staying above her eye line. Her eyes follow it first, then
> her head tilts down slightly to keep watching it. Her lips stay softly parted in quiet wonder;
> she does not speak. Gentle breathing. Her long black hair with teal ends and the dark ribbon tails
> lag slightly and settle. Stars stay steady; the clouds barely drift. Preserve her exact face,
> horns, crossed hair clip, braid, ribbon and outfit. One continuous shot, with quiet moments at the
> start and end.

**Negative (if supported):** talking, mouth movement, lip-sync, camera movement, zoom, pan, cut,
second light, extra orb, star flicker, extra characters, changing horns, changing hair clip,
changing hairstyle, outfit change, 3D render, photorealism, text, watermark, heavy blur, face
distortion.

## Settings (PENDING the real interface; record what was used)

- **Model:** Seedance 2.5 (name the exact variant shown).
- **Mode:** image-to-video, first frame only.
- **Aspect:** 16:9. **Resolution:** the highest offered without upscaling the input.
- **fps:** 24 if selectable. **Fixed or locked camera:** on, if offered.
- **Motion strength:** low to medium.
- **Audio:** off, or ignored (the locked music is used).
- **Outputs:** 1 per attempt. **Seed:** record it.
- **Attempts:** the owner decides; I suggest at most 3 for this pilot.
- **Return:** the original downloaded file, not re-encoded, plus the settings and seed for each
  attempt.

## What I will check when the clip comes back (`tools/seedance_check.py`)

**Measured:**
- container fps, frame count, resolution, duration;
- a single warm light, its path frame by frame (must move down-left, no second light);
- camera drift from the background (≤ 2%);
- mouth-region change across frames (flags talking);
- frame-to-frame change spikes (flags pops or flicker).

**Visual (with frame strips):**
- identity: horns, clip, braid and ribbon, eyes, outfit;
- eyes lead the head; hair lag;
- the overall read of quiet wonder.

**Fit:** the chosen 1.667 s placed at 7.500 on the locked track, with burned local and song
timecode.

**Not certifiable by me:** normal-speed smoothness and emotional read. Those need a human playback
review.
