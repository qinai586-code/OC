# Motion pilot P1-S1 (v3): final, for the owner to generate. Not submitted; no credits used.

Replaces `PILOT_S1_SHEET_v2.md`. Board: `PILOT_S1_v3_board.jpg`.

## The mismatch, and how v3 resolves it

The v2 sheet had 2.2 s of action inside the clip:
- the light drifts from 0.8 to 2.6 s;
- the hand starts to lift from 2.6 to 3.0 s.

That had to play in a 1.667 s slot (song 7.500–9.167). Fitting it means a 32% speed-up (the limit is
10%) or cutting part of the action off. v3 does both of the following:

1. **One action only.** S1 is: the light drifts, her eyes follow, then her head tilts slightly down
   and holds. **The hand lift is removed from S1.**
   - In all three approved frames her hand is already out, palm up. The lift that matters (lower
     chest to shoulder) is between S2 and S3, so it belongs to S2.
   - A lift started at the end of S1 would have to be still moving in S2's first frame. S2 is
     generated from a still image, so it starts at rest, and the move would stall on the cut.
   - The cut S1→S2 is carried instead by **the light**: still moving down-left at the cut, it enters
     S2 from the top right, and her gaze is following it.
2. **A fixed 40-frame window.** The action takes about 1.2 s inside it. The light moves for the
   whole clip, so the window never starts or ends on a light that has stopped.

## Inputs and settings

| field | value |
|---|---|
| first frame | `refs_in2/P1_S1_original_reference_v8.png`, unmodified (1672×941, sha256 0d4bb512df959b04) |
| end frame | none |
| other references | none. S2 and S3 are **not** attached; they only define where S1 must end. No character-reference image either: the first frame carries identity |
| length | the shortest option ≥ 3 s (needed: 0.5 s lead + 1.667 s + ≥ 0.5 s tail = 2.67 s) |
| mode / camera | image-to-video, first frame only; fixed camera on, if offered; motion low to medium |
| aspect / size / fps | 16:9; highest resolution offered without upscaling the input; 24 fps if selectable |
| audio | off or ignored (the locked music is used) |
| outputs | 1 per attempt; record the seed and settings; return the original file (no re-encode) |
| attempts | the owner decides; I suggest at most 3 |

Interface details are still **PENDING** (minimum length, fps, whether a negative-prompt field
exists, accepted input size). Only fps affects the trim, and the check handles any fps by time.

## Final generation prompt

> Fixed camera, no camera movement, one continuous shot. 2D anime cel-shaded night scene above the
> Earth, exactly as in the first frame. The small warm golden light in the upper right of the sky
> drifts slowly and steadily down and to the left for the whole shot, staying high in the sky, well
> above the girl's eyes. The horned girl in right profile watches it in quiet wonder: after a brief
> moment her eyes follow it, and a beat later her head tilts slightly down to keep watching it; then
> she holds still, watching, while the light keeps drifting. Her lips stay softly parted; she does
> not speak. Her open right hand stays where it is. Gentle breathing. Her long black hair with teal
> ends, the dark ribbon and the wide sleeves sway slightly and settle. Stars stay steady; clouds
> barely drift. Keep her face, horns, hair clip, hairstyle and outfit exactly as in the first frame.

**Negative (if the field exists):** talking, singing, mouth movement, lip-sync, raising the hand,
reaching, camera movement, zoom, pan, cut, second light, extra orb, moon, static light, light near
her face or hand, star flicker, extra characters, extra fingers, changing horns, moving or changing
hair clip, hairstyle change, outfit change, 3D render, photorealism, text, watermark, heavy blur,
face distortion.

## Exact trim

| | value |
|---|---|
| **clip in** | **0.500 s = clip frame 12** (24 fps) |
| **clip out** | **2.167 s**; the last frame used is **clip frame 51** |
| length | **40 frames at 1:1**: no speed change, no blending, no frame interpolation |
| song placement | **7.500–9.167** (song frames 180–219): clip frame 12 + j → song frame 180 + j, for j = 0…39. The cut to S2 is at 9.167 |
| source not at 24 fps | frame k (k = 0…39) is the source frame nearest to 0.500 + k/24 s |
| handles | clip 0–0.5 s before (it would cover song 7.0–7.5, which belongs to the previous shot); everything after 2.167 s |

**Why 0.500 s in.** An image-to-video clip starts at rest and its motion ramps up from zero. Starting
0.5 s in, the cut lands on a light that is already moving. Frames that early are still very close to
the approved image.

**One slide rule, for a take whose timing is off.** First run the check once over the whole clip
(`--in 0 --dur <clip length>`). This finds the clip frame where her head first turns more than 1°:
- If that happens between clip frames 18 and 30 (0.75–1.25 s), keep the trim above.
- Otherwise, start the same 40-frame window 12 frames (0.5 s) before the head turn, never before frame
  0. Run the window check with that `--in`.
- If no 40-frame window passes the measured checks below, the take fails. Regenerate; never speed it
  up or blend frames.

The music: the vocal "one" enters at 7.52 s (measured on the vocal stem) and swells through the shot.
The onset detector finds no beat hit between 6.64 and 13.10 s, so there is no sync point the head
turn has to land on.

## Check command

```
python3 rev3/tools/seedance_check.py <clip.mp4> --name P1-S1_tryN --in 0.500 --song 7.500 --dur 1.667 \
    --mouth 565,325,600,360 --light-box 950,0,1672,260 --min-move 60 \
    --head 340,90,640,400 --hand 760,650,940,770
```

It writes `report.json` (whole clip plus the 40-frame window), `strip.jpg`, and `fit.mp4`. `fit.mp4`
is the window at 1:1 over the unchanged music, with local and song timecodes burned in.

## Acceptance

**Measured on the window** (coordinates in the 1672×941 first frame):

| check | pass |
|---|---|
| lights | exactly one in each of the 40 frames |
| light path | net travel down-left of 60–300 px (target 100–200); no quarter-second under 3 px (no stall); inside the box x 950–1672, y 0–260 (above her eyes, right of her hand) |
| head | turns +4° to +15° chin-down by the end of the window (target 8–10°); the turn starts at clip 0.75–1.25 s, or the window is slid as above |
| hand | moves ≤ 15 px and rotates ≤ 5° (breathing only) |
| camera | shift ≤ 2% of the frame width |
| frame-change spikes | none |
| mouth | the change is reported, but there is no calibrated threshold; judged visually |

**Visual (I check from the strip and frames; you confirm):**
- the eyes move before the head;
- identity is stable: horns, the clip (no flicker or drift), half-up hair with ribbon, teal eyes,
  outfit;
- hair and sleeves lag and settle;
- no extra fingers, no face distortion, no talking;
- 2D cel look, no text or watermark.

**Your playback only:** smoothness at normal speed, the feeling of quiet wonder, and whether the cut
into S2 reads.

## Open items

**Nothing is blocking generation except your approval.** The input frame passes, and the prompt,
trim and checks are fixed.

**Risks only a take can answer** (each has a measured fail condition above):
1. **The light may be treated as a moon.** The model may keep it fixed or move the camera instead.
   - Caught by the travel, stall and camera checks.
   - This is the likeliest failure.
2. **A long minimum clip length (≥ 5 s) can spread the head turn thinly**, so the window sees less
   than 4°.
   - The prompt asks for the turn and then a hold to counter this. Slide the window, or regenerate.
3. **The open palm invites reaching.** Caught by the hand check.
4. **Identity drift as the hair moves**, especially the clip. Visual check.

**Visual notes on the approved frame (not blocking):**
- **Eyeline.** Her eye is at about (517, 292) and the light at (1205, 121), so the light sits about
  14° above her eye level (measured from pixel positions). Her drawn gaze points much higher, at
  roughly 35–45° (a visual estimate).
  - She reads as looking at the sky just above the light. The chin-down tilt narrows the gap.
  - If playback reads as "looking past it", the options are a larger tilt (up to about 15°, more
    risk of face distortion) or accepting it.
- **Clip side.** The X clip is on her visible right; the model sheet has it on her left. I'm
  treating your approval of S1–S3 as accepting this for P1. It still needs a decision before Wave 2.

**Depends on S2:** S2 must carry the hand lift (about one palm-height, to S3's height). The light
should also enter early in S2's used window. If S2 doesn't lift the hand, the S2→S3 cut will jump.

**Limits of the checker:**
- **Tested on stills:** S1, S2 and S3 at three sizes, with light counts of 1, 0 and 1 as expected.
- **Tested on synthetic clips made from the S1 frame:**
  - a second light and a stall planted in the window were both flagged;
  - a planted 9° head tilt was measured as 8.55°, with its onset within one frame;
  - a still hand measured 0 px.
- **Reproduce with** `python3 rev3/tools/seedance_check_selftest.py` (about 1 min; asserts all of the
  above).
- **Not yet tested on real Seedance output.** If the detector or tracker fails on a real clip, I
  fall back to a frame-by-frame visual check and say so.
