# P1-S1 v5: the opening shot's performance, for the owner to generate in Seedance 2.5

Replaces `PILOT_S1_SHEET_v4.md`. S2 and S3 stay as built locally (`tests/P1_local_720p.mp4`). Only S1
needs generated footage: her nod. The light is added locally afterwards, so the clip must contain no
light.

**Reference (first frame only):** `refs_in2/P1_S1_v8_nolight.png`
- 1672×941, sha256 1c547cd0383355e3;
- this is the approved S1 frame with only the light removed from the sky;
- no end frame, no other images.

Why no light: in try 1 the model dropped her head 18° to meet the light, and moved the light like a
moon on a rail.

**Settings:**

| field | value |
|---|---|
| mode | image-to-video, first frame only |
| length | the shortest offered (5 s is fine) |
| resolution | 720p is enough |
| fps | 24 |
| camera | fixed camera on, if offered |
| motion | low |
| audio | off |
| outputs | 1 |
| return | the original file, plus the seed and settings |

## Prompt

> Fixed camera, no camera movement, one continuous shot. 2D anime cel-shaded night scene above the
> Earth, exactly as in the first frame. The horned girl in right profile gazes up at the empty night
> sky in quiet wonder. For the first second she stays still, breathing gently. Then her eyes lower
> first, and a moment later she gently nods her head down, like a real person lowering their gaze:
> her head turns in place on her neck, her chin tucks slightly, and her gaze comes down from high in
> the sky to only slightly above the horizon. Her head does not lean or push forward, her neck keeps
> its shape, and her shoulders and body stay completely still. Then she holds still, watching, until
> the end of the shot. She keeps exactly the same side-profile angle and does not turn toward the
> viewer. Her lips stay softly parted; she does not speak and does not blink. Her open right hand
> stays exactly where it is. Her long black hair with teal ends and the dark ribbon follow the head
> gently and settle. The sky, clouds, stars and Earth stay still. Keep her face, horns, hair clip,
> hairstyle and outfit exactly as in the first frame.

**Negative (if the field exists):** light, glowing orb, moon, sun, sparkles, lens flare, head
pushing forward, leaning forward, neck stretching, neck shrinking, shoulders moving, body moving,
turning toward the camera, looking at the viewer, repeated nodding, blinking, closed eyes, talking,
mouth movement, raising the hand, hand moving, camera movement, zoom, pan, cut, warping, morphing,
extra characters, extra fingers, changing horns, changing hair clip, hairstyle change, outfit
change, 3D render, photorealism, text, watermark, flicker.

## What I do with the returned clip

1. **Measure it** with `tools/seedance_check.py` over the whole clip: the head turn and its start
   frame, how far the head moves forward, camera, hand and body stillness, blinks, frame pops.
2. **Trim:**
   - **IN = the frame where her head first turns more than 1°, minus 9 frames.**
   - 40 frames at 1:1 on song 7.500–9.167.
   - If the turn starts at about 1.08 s, that is clip frames 17–56.
3. **Composite the light** with the approved orb's measured look, its path fitted to her actual
   gaze.
4. **Cut it into the local S2 and S3** over the locked music, and send the result for your
   playback.

## What makes the take usable

- **Head:**
  - a chin-down nod of about 10–18° that settles and holds within the 40 frames;
  - the head turns in place: no forward slide, no turn toward the camera;
  - the neck keeps its length.
- **Stillness:** body, collar, bow and hand still (≤ 15 px); camera locked.
- **Eyes:** no blink in the 40 frames.
- **Identity:** horns, clip, ribbon, eyes and outfit stable.
