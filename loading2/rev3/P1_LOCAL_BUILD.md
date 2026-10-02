# P1 light catch: local build from the approved stills (no generated video)

Owner decision (2026-10-02): no more generation for this sequence. Use the approved S1–S3 images
directly, and deliver at 720p.

| file | what it is |
|---|---|
| `tests/P1_local_720p.mp4` | 1280×720, 24 fps, 146 frames: song 7.500–13.583 on the locked music, one continuous encode |
| `tests/P1_local_strip.jpg` | 10 frames with song time |
| `tests/p1_local_log.json`, `tests/p1_local_checks.json` | build log and measurements |
| `tools/p1_local.py` | the build (about 1 min on CPU) |

| shot | song (frames) | source (unmodified approved still) | action |
|---|---|---|---|
| S1 | 7.500–9.167 (180–219) | P1_S1 v8, light removed locally | The light sinks from her eyeline. Her eyes lower first (7.75); her head dips 6° (7.875–8.5), settles and holds. The back hair, the strands in front of her shoulder and the hair ends follow |
| S2 | 9.167–10.667 (220–255) | P1_S2_HAND_START_v2 | The light enters from the top and slows to a hover above the palm. The hand lifts gently (the fingertips rise 51 px), and warm light grows on the hand |
| S3 | 10.667–13.600 (256–325) | P1_S3_HOVER_START_v2 | The light hovers, then sinks into the palm on "Loading." The touch is at 13.042, against the measured vocal onset at 13.05. The palm gives 4.5 px and recovers; the glow flares, then stays brighter on the palm and a little on her face. Her hair sways and she breathes |

## Method

Limited animation of the approved drawings. Nothing is redrawn.

- **S1:** a smooth warp rotates the head about the upper neck, with delayed follow on the back hair,
  the front strands and the hair ends. The dark sky moves with it invisibly; the hand is excluded.
- **S2:** the arm is a cut-out over the original image.
  - The model reads the dark coat as half-transparent, so the matte is completed by hand: sleeve
    and cuff solid from their top edge to the bottom of frame, bounded by the cuff lining's edge,
    measured row by row.
  - Background uncovered by the lift is copied from further along the Earth's limb (a fit with
    95th-percentile residual 3.8 px), so the limb and cloud texture continue behind the hand.
- **S3:** a smooth warp moves the palm and the smooth sky above it. The Earth below is covered,
  never uncovered.
- **Light:** composited with radial glows measured from the approved orbs: S1 uses v8's, S2 and S3
  use S3's, scaled 1.25–1.65× for the closer S2 insert.

## Measured (`tests/p1_local_checks.json`)

| check | result |
|---|---|
| container | 1280×720, 24 fps, 146 frames, 6.083 s; AAC 48 kHz, 6.083 s; 0 irregular frame steps |
| first frame of each shot vs its approved still (mean / p99 difference, 0–255) | S1 2.19 / 5.0 (light-free still, away from the new light); S2 2.32 / 6.7; S3 2.28 / 6.3. These differences are resizing and encoding |
| S1 head turn (tracker) | 0° to frame 9; 0.6° at frame 12; 3.7° at 18; 5.6° at 24; 5.8° at 29 and 39 (designed: 6°, settled by 29). Hand moves 0 px |
| S2 hand | 45 px shift and 3.9° lift by the end |
| frame-to-frame change | the only large changes are the two cuts (output frames 40 and 76); otherwise at most 1.1 against a median of 0.15 |
| S1 light brightness | within 2.1% from frame to frame (no flicker) |
| light detector | no extra light in any frame. It misses the light in 2 S1 frames (the core splits at its threshold; brightness is steady), before the light enters S2 (frames 40–41, expected), and once the light is over the warm palm in S3 (detector limit). These are visual checks, not failures |

## Visual (my judgment from frames; please confirm)

- S1: the head dip reads as a dip. The face, horns and clip stay intact, with no warping marks.
- S2: the sleeve, cuff and hand move as one piece with clean edges. The limb and clouds continue
  behind the lifted hand.
- S3: the light sits in the cupped palm after the touch.

## Needs your playback

- Whether the motion reads naturally at speed.
- The feel of the touch on "Loading.".
- The cuts S1→S2→S3.
- Whether the hand lift in S2 is enough to bridge to S3's higher hand.

## Notes and limits

- **Timing correction.** The plan put "Loading." at 12.6. The vocal stem and mix both have their
  onset at 13.05, and the earlier transcription windows agree (the word appears only after 13.0).
  The touch is timed to 13.05.
- **Light start.** The S1 light starts on her drawn eyeline at (905, 50), not at the approved
  (1205, 121): from the old spot, a follow needs about an 18° head drop. It is one line in
  `p1s1_light.path` if you want the old spot back.
- **Not animated:** S3's lips and eyes (no drawn variants exist); no blinks; no finger
  articulation.
- **Generated video:** none. Seedance try 1 is not used anywhere.
