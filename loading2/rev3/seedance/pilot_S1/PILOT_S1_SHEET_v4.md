# P1-S1 v4: footage spec, resolved timing, one minimal request. Not submitted; no credits used.

Replaces `PILOT_S1_SHEET_v3.md`. Inspection of the rejected try 1: `../P1-S1_try1_REVIEW.md`.
Timing animatic: `P1-S1_v4_timing_animatic.mp4`. Review board: `../review/P1-S1_try1_review_board.jpg`.

**The change from v3:** the light is no longer generated. The model is asked only for her
performance, from the approved frame with the light removed. The light is composited locally with
the approved orb's measured look, on a path that starts on her drawn eyeline. A follow then needs
only a small head dip, not the 18° drop try 1 produced.

## What footage I need (S1: song 7.500–9.167, 40 frames)

| | requirement |
|---|---|
| **start pose** | the approved frame exactly: right profile, chin raised, eyes up and to the right, lips softly parted, right hand open palm-up at lower chest. Profile angle as approved: the far horn stays behind the near one |
| **end pose (frame 39)** | head **5–7° chin-down** from the start, **pitch only**: same profile angle, far horn still hidden. Eyes lowered more than the head. Lips still parted. Hand where it started (≤ 15 px). Hair settling |
| **eye/head motion** | one readable beat: eyes first, then the head dips over about 0.6 s, settles and holds. No blink in the 40 frames. No turn toward the camera |
| **light** (local, not generated) | **look:** the approved orb's glow, measured from v8 (white core about 10 px radius, warm glow, faint tail to about 150 px at 1672 width). Size +10% over the shot, slow ±6% pulse.<br>**path:** from (905, 50), 32° above her eye on her drawn eyeline, sinking on a gentle curve with a ±3.5 px float sway, slightly accelerating, to (887, 176) at the cut, 18° above her eye. That is 127 px in 1.667 s.<br>It moves from the first frame and never stops. After a take is accepted, the path is fitted to her actual eyeline |
| **camera** | locked (≤ 1% of width); framing as the approved frame |
| **usable duration** | 40 frames at 1:1 = 1.667 s, on song 7.500–9.167 (song frames 180–219) |
| **continuity into S2** (9.167) | Her hand is at rest in S2's first-frame pose; the lift happens in S2.<br>At the cut the light is above her, still sinking (down, slightly left) toward her hand. In S2 it enters from the top edge, slightly right of the palm, and slows above the palm. S2's light can also be local.<br>Her lowered gaze motivates the cut to the hand insert |

## Action timing (resolved)

| window frames | song time | light | eyes | head |
|---|---|---|---|---|
| 0–5 | 7.500–7.708 | already sinking from (905, 50) | on the light | still (breathing) |
| 6–9 | 7.750–7.875 | sinking | **lower first** | still |
| 9–24 | 7.875–8.500 | sinking | following | **dips 0 → 6°**, ease in and out |
| 24–29 | 8.500–8.708 | sinking | following | settles (overshoot ≤ 0.4°) |
| 29–39 | 8.708–9.167 | still sinking, reaches (887, 176) | on the light | **holds** |
| cut | 9.167 | continues into S2 from the top | — | — |

**Why this timing:**
- The vocal "one" enters at 7.52 s and swells, with no beat hit in this span (measured). So the
  light drives the beat: it moves first, and she reacts 0.25 s later.
- The dip completes mid-phrase.
- The 0.46 s hold lets the look register before the cut.

The animatic plays this over the locked music, and its light is the proposed final design. Its
head and eye motion is a crude 2D placeholder showing *when*, not *how*.

## What is local and what is generated

- **Local, with no generation:**
  - the light (look, path, size, speed, pulse);
  - removing any light a take adds anyway;
  - one-frame texture pops (hold a neighbour);
  - registering each take to the reference (try 1 was re-framed 1.2% × 3.1%);
  - upscaling to 1080p;
  - fitting to the locked music.
- **Generated:** her performance only: the eye lead, the head dip and settle, breathing, hair and
  sleeves. Try 1 contains no usable window (measured), and a 2D rotation looks like a cut-out
  puppet.

## The one minimal generation request

**Shot:** P1-S1 performance plate. Her only; no light anywhere in frame.

**Reference:** exactly one image, used as the first frame:
- `refs_in2/P1_S1_v8_nolight.png` (1672×941, sha256 1c547cd0383355e3);
- it is the approved v8 with the light removed locally. Only sky pixels within 165 px of the old
  light changed; she is untouched (see board panel E);
- no end frame, no character reference, no S2 or S3 image.

**Settings:**

| field | value |
|---|---|
| mode | image-to-video, first frame only |
| length | the shortest offered (try 1's 5 s is fine) |
| resolution | 1080p if offered; otherwise 720p |
| fps | 24 |
| camera | fixed camera on, if offered |
| motion | low |
| audio | off |
| outputs | 1 |
| record | the seed and settings |
| return | the original or highest-quality download |

**Prompt:**

> Fixed camera, no camera movement, one continuous shot. 2D anime cel-shaded night scene above the
> Earth, exactly as in the first frame. The horned girl in right profile gazes up at the empty night
> sky ahead of her in quiet wonder. For the first second she stays still, breathing gently. Then her
> eyes lower slightly, and a moment later her head dips just a little, a small, gentle nod, keeping
> exactly the same side-profile angle. Then she holds completely still, watching, until the end of
> the shot. Her lips stay softly parted; she does not speak and does not blink. Her open right hand
> stays exactly where it is. Her long black hair with teal ends, the dark ribbon and the wide
> sleeves sway slightly in a light breeze and settle. The sky, clouds, stars and Earth stay still.
> Keep her face, horns, hair clip, hairstyle and outfit exactly as in the first frame.

**Negative:** light, glowing orb, moon, sun, sparkles, lens flare, head turning, turning toward
the camera, looking at the viewer, large head movement, repeated nodding, blinking, closed eyes,
talking, mouth movement, raising the hand, hand moving, camera movement, zoom, pan, cut, extra
characters, extra fingers, changing horns, changing hair clip, hairstyle change, outfit change, 3D
render, photorealism, text, watermark, flicker.

## Exact trim

Run the check over the whole clip. **h** is the first clip frame where her head has turned more than
1° chin-down.

- **IN = h − 9; OUT = IN + 39 (inclusive).** These 40 frames play at 1:1 on song **7.500–9.167**
  (frame IN + j → song frame 180 + j).
- **Nominal**, if the dip starts at about 1.08 s as prompted (h = 26): **clip frames 17–56**, i.e.
  clip **0.708–2.375 s**. The last frame used is frame 56, at 2.333 s.
- If h < 9 (no clean hold before the eyes) or IN + 39 runs past the clip, the take fails.
- No speed change, no blending, no interpolation.

```
python3 rev3/tools/seedance_check.py <clip> --name P1-S1_tryN_whole --in 0 --song 7.0 --dur <clip length> \
    --head 340,90,640,400 --hand 760,650,940,770
python3 rev3/tools/seedance_check.py <clip> --name P1-S1_tryN --in <IN/24> --song 7.500 --dur 1.667 \
    --head 340,90,640,400 --hand 760,650,940,770
```

## Acceptance

**Measured, on the window:**
- head 4–8° chin-down at frame 39, at least 90% of it by frame 29, never above 9°;
- hand ≤ 15 px and ≤ 5°;
- camera ≤ 1% of width;
- no light detected (the input has none). If one appears, it is removed locally and logged;
- frame pops: none, or one-frame pops repaired by a hold and logged.

**Visual, frame by frame:**
- no blink;
- no turn toward the camera (far horn stays hidden);
- the eyes move before the head;
- identity holds: horns, clip, ribbon, eyes, outfit;
- no talking.

**Your playback:** whether the beat reads, smoothness, and the eyeline with the composited light.

**After a pass (local):**
1. register frame 0 to the reference;
2. fit the light path to her eyeline;
3. repair pops;
4. upscale;
5. composite the light;
6. fit at 7.500 over the locked music;
7. build a cut preview into S2's first frame.

## Open items

1. **Your decision: the light's start position.** It moves from the approved (1205, 121) to her
   eyeline at (905, 50). The character and the rest of the frame are unchanged.
   - If the light stays at (1205, 121), any head follow means an 18° drop, as try 1 showed.
   - The alternative then is no head move at all: she holds while only the light moves, and the
     still's eyeline mismatch remains.
2. **The model may still add its own light** to the empty sky. The negative prompt covers it, and
   it is removable locally.
3. **With no target in the image, the eyes may not lead visibly.** That is acceptable if the head
   dip is right: at 720p her eye is about 25 px wide.
4. **Delivery quality:** try 1 was 720p at 541 kbps. Prefer 1080p or the highest-quality download.
5. **Clip side:** unchanged, accepted for P1 as drawn.
6. **S2 continuity depends on S2:** the hand lift, and the light entering from the top edge.
   Nothing is requested for S2 now.
