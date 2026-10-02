# P1-S1 try 1: inspection (rejected by the owner; not accepted footage)

Board: `review/P1-S1_try1_review_board.jpg`. The checker ran over the whole clip and over the v3
window: `checks/P1-S1_try1_whole/`, `checks/P1-S1_try1/`.

| item | value |
|---|---|
| file | `returned/P1-S1_try1.mp4` (owner upload, unmodified copy). sha256 475561b06597aa8e |
| video | H.264 High, 1280×720, 24 fps, 121 frames, 5.042 s, **541 kbps** (low; compression is visible on the hair) |
| audio | AAC 44.1 kHz stereo, **not silent** (mean −29.0 dB, peak −11.4 dB): generated sound. Discarded; only the locked music is used |
| first frame | the approved S1 image, slightly re-framed by the model. After an affine fit, the mean difference is 2.3/255. The fit is 1.2% wider and 3.1% taller, a 1.9% vertical stretch |

The owner rejects the head movement and the light's behaviour. The measurements below agree, and
show why.

## Measured

| check | result | spec (v3) |
|---|---|---|
| camera | locked: background shift ≤ 2.2 px over 5 s (ECC on sky and Earth, light masked) | ≤ 2% ✔ |
| head pitch (chin-down) | starts at clip 0.79 s. 2.8° at 1.0 s, 8.3° at 1.5 s, 12.8° at 2.0 s, 14.7° at 2.5 s, **17.7° at 5.0 s**. Still drifting at the end. (The tracker is noisy at 3.6–4.1 s) | 4–15°, then hold ✘ |
| head in the v3 window (clip 0.500–2.167) | 13.5°, turn starting at window frame 8 | ✘ (no settle) |
| blink | eyes closed at **clip frames 32–36** (1.33–1.50 s), inside the window | none in the window ✘ |
| hand | rotation up to 4.5°, shift up to 18.5 px (16.3 px in the window) | ≤ 15 px ✘ (slightly) |
| light count | exactly one in all 121 frames | ✔ |
| light motion | **constant speed 1.90 px/frame** (sd 0.47) on a straight line from (1187, 118) to (997, 242), at constant size | — |
| light in the v3 window | 74.5 px of travel | ≥ 60 ✔, but see below |
| frame pops | **one-frame texture pops at frames 10, 60 and 110** (one every 50 frames; the following frame returns). Frame 60's change is 1.63 against a median of 0.47 | none ✘ |
| any usable window | **none.** Every 40-frame window starting near the approved pose (frames 0–24) has a 9.6–13.6° turn and includes the blink. The only windows with a settled 4–8° dip start at frames 37–48, where she is already 9–12° down and turned toward the camera | — |

## Visual (my judgment; please confirm)

- **Head:** a slow, continuous lowering with no clear beat. The eyes do not visibly lead the head.
  - It also **turns toward the camera**: the far horn separates from the near one. The horn-tip
    gap grows from about 45 to about 72 px; this is a rough measure.
  - By the end her eyes look level, under the light. The approved profile angle is lost.
- **Light:** it reads as a moon sliding on a rail. It has a constant speed, a straight path, a
  constant size and a big halo.
  - Its path aims at her face rather than her hand, so it cannot lead into S2 (hand) and S3 (palm).
- **Identity:** horns, clip side, ribbon, eyes and outfit hold up. The texture pops show as a
  reddish crosshatch on the hair and coat.
- **Mouth:** lips stay parted with no speech. The mouth metric (about 18) is driven by the head
  moving through a fixed box, not by talking; its note in the checker now says so.

## Why it failed (this includes my spec)

1. **Eyeline geometry in the approved frame.** Her drawn gaze points about 30–40° up (a visual
   estimate), but the light sits 15° above her eye (measured from pixel positions).
   - Asked to "follow the light", the model dropped her head about 18° until her eyes reached it,
     turning her toward the camera on the way.
   - The v3 sheet called this a "visual note". It was in fact the cause of the head failure.
2. **The light was asked to move "slowly and steadily for the whole shot".** The model did
   exactly that, so her head kept following for the whole shot. The model drives the light and the
   head together, so neither can be timed on its own.
3. **The light's look and motion were left to the model.** It produced a rail-straight,
   constant-speed moon.

## Local vs new footage

| item | local repair? | how |
|---|---|---|
| light: look, path, size, speed, pulse | **yes, entirely** | composited locally with the glow measured from the approved orb (`tools/p1s1_light.py`). It is not generated at all in v4 |
| a generated light, if a take has one | yes | the camera is locked, so the sky patch is replaced from the light-free plate and the designed light is drawn on top |
| one-frame texture pops | yes | hold the neighbouring frame (24 fps; anime timing hides a one-frame hold) |
| 720p delivery | yes, with a cost | upscale ×1.5 to 1080p. Better: download the original or highest-quality file, or generate at 1080p if offered |
| re-framing / 1.9% stretch | yes | register each take to the reference (affine fit on frame 0) before placing the light; correct the stretch if visible |
| head motion: amount, turn toward camera, eyes leading, settle | **no** | baked into the pixels together with hair and horns. Time remapping cannot remove the turn or the blink, and no window qualifies (measured). A 2D head rotation is only good enough as a timing placeholder (see the v4 animatic) |
| blink inside the window | no | it can only be avoided by choosing a window, and in this take no window qualifies |

**Conclusion:** try 1 is not usable. The one new generation needed is her performance only, with
no light, from the approved frame with the light removed. See `pilot_S1/PILOT_S1_SHEET_v4.md`.
