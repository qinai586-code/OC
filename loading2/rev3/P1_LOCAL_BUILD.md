# P1 light catch: local build from the approved stills (no generated video)

Owner decision (2026-10-02): no more generation for this sequence. Use the approved S1–S3 images
directly, and deliver at 720p.

| file | what it is |
|---|---|
| `tests/P1_local_720p.mp4` | 1280×720, 24 fps, 146 frames: song 7.500–13.583 on the locked music, one continuous encode |
| `tests/P1_local_strip.jpg` | 10 frames with song time |
| `tests/p1_local_log.json`, `tests/p1_local_checks.json` | build log and measurements |
| `tools/p1_local.py` | the build (about 1 min on CPU). Amplitudes are constants at its top |

| shot | song (frames) | source (unmodified approved still) | action |
|---|---|---|---|
| S1 | 7.500–9.167 (180–219) | P1_S1 v8, light removed locally | The light sinks from her eyeline. Her eyes lower first (7.75). She **nods down 14°** (7.875–8.5), settles and holds, and the light ends on her lowered gaze. The hair follows |
| S2 | 9.167–10.667 (220–255) | P1_S2_HAND_START_v2 | The light enters from the top and slows to a hover above the palm. The hand lifts (the fingertips rise 84 px), and warm light grows on the hand |
| S3 | 10.667–13.600 (256–325) | P1_S3_HOVER_START_v2 | The light hovers, then sinks into the palm on "Loading." The touch is at 13.042, against the measured vocal onset at 13.05. The palm gives 7 px and recovers; the glow flares, then stays brighter. Her hair sways and she breathes |

## Revisions after the owner's review

- **The jump from S1 to S3 was too large.** S1's head moved only 6°, but S3's head sits about 34°
  further down. The measure is the eye–mouth line: 37.8° in S1, 72° in S3.
  - Amplitudes were raised with the same beats and frame timing: nod 6° → 14°, iris 3 → 5 px,
    light travel 127 → 190 px, S2 lift 51 → 84 px, S3 palm give 4.5 → 7 px.
  - The remaining difference falls inside the S2 insert.
- **"Not pulled forward; a real nod":**
  - The pivot is now inside the head (400, 300), behind its centre (444, 257), so the head turns
    nearly in place: the face drops and the chin tucks.
  - The earlier throat-level pivot slid the whole head forward.
- **"Keep the image stable, don't break the model":**
  - The head is rigid: no part of the face or jaw bends.
  - The hair regions stop at the shirt, collar, bow and coat, which measure 0.0 px of movement.
  - The long hair follows with a long, smooth falloff (no waves), lagging 3 frames.
  - The sky is a static plate under her, so clouds never bend.
- **The neck:**
  - The face, chin and jaw are a rigid layer over the still neck. The chin tucks in front of the
    throat, and the neck keeps its length instead of being squashed.
  - The head outline takes in the sky just under the chin, so no piece of the jaw's outline is
    left behind.
- **The S2 hand cut-out:**
  - The model reads the dark coat as half-transparent. The sleeve and cuff are made solid down to
    the bottom of frame, bounded by the cuff lining's edge, measured row by row.
  - Uncovered background is copied from further along the Earth's limb (a fit with
    95th-percentile residual 3.8 px).

## Measured (`tests/p1_local_checks.json`)

| check | result |
|---|---|
| container | 1280×720, 24 fps, 146 frames, 6.083 s; AAC 48 kHz, 6.083 s; 0 irregular frame steps |
| first frame of each shot vs its approved still (mean / p99 difference, 0–255) | S1 2.19 / 5.0 (light-free still, away from the light); S2 2.33 / 7.0; S3 2.28 / 6.3. These are resizing and encoding |
| S1 nod (tracker on the head) | 0° to frame 9; 1.4° at 12; 8.5° at 18; 12.7° at 24, then held. The tracker reads a little under the designed 14° because its box includes hair |
| S1 at the end: what moved | face 39 px, horns 34 px. **Collar, bow, coat, hand, sky: 0.0 px** |
| S2 hand | 75 px shift and 6.7° lift by the end |
| frame-to-frame change | the only large changes are the two cuts (output frames 40 and 76); otherwise at most 1.3 against a median of 0.17 |

## Visual (my judgment from frames; please confirm)

- **S1:** the head nods in place. The jaw passes in front of the throat, and the neck keeps its
  length. The back hair lifts slightly with the back of the head, with no waves; the body is still.
- **S2:** the sleeve, cuff and hand move as one piece with clean edges. The limb and clouds continue
  behind the lifted hand.
- **S3:** the light sits in the cupped palm after the touch.

## Needs your playback

- Whether the nod reads as natural at speed.
- The S1→S2→S3 cuts.
- The touch on "Loading.".

## Notes and limits

- **Timing correction.** "Loading." is at 13.05 (vocal stem, mix and the earlier transcription
  windows agree), not 12.6 as in the plan.
- **Light start.** The S1 light starts on her drawn eyeline at (905, 50), not at the approved
  (1205, 121). One constant restores it.
- **Not animated:** S3's lips and eyes; blinks; finger articulation.
- **Generated video:** none. Seedance try 1 is not used anywhere.
