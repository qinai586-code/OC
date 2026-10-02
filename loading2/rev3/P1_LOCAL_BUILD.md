# P1 light catch: S1 from the owner's Seedance take, S2 and S3 built locally

**Current output: `tests/P1_light_catch_720p.mp4`.** 1280×720, 24 fps, 146 frames, song 7.500–13.583
on the locked music, one continuous encode. Strip: `tests/P1_light_catch_strip.jpg`. Build:
`tools/p1_local.py`. S1 comes from `tools/p1_s1_clip.py`; `P1_S1_SOURCE=local` switches back to the
local 2D nod.

## S2 hand leak fixed (2026-10-02, after approval)

- **What you reported:** a sliver of the original hand showed through the thumb–index gap while the hand lifted (output frames 52–64).
- **Cause:** the background behind the hand was filled only where the hand had moved away at the top of the lift. While the hand moved, the gaps between the fingers showed the original thumb edge.
- **Fix:** `tools/p1_local.py` (`build_s2`) now also fills under the whole original hand (its matte right of x = 600, grown 5 px) before the moving hand goes on top.
- **Result:** the approved file is rebuilt: sha256/16 **cd7a70a62d7f869a** (was f91e896ce1ebc75f).
  - S1 differs only by re-encoding (max mean frame difference 0.56/255), and S3 is unchanged.
  - Only S2's background under the hand changed.

## S1 from the owner's Seedance 2.5 takes (2026-10-02)

| take | file (sha256/16) | measured | visual | verdict |
|---|---|---|---|---|
| v2 | `seedance/returned/P1-S1_v5_take_v2.mp4` (76792d17a4d9102e) | Still until frame 60; the head turn starts at frame 61 (> 1°). One nod to about 37°, settled by frame 98. Camera 0.13 px. One light, fixed at (907, 89) in every frame | One smooth nod in profile, ending looking forward and slightly down. The jaw tucks and the neck reads naturally. Eyes close during frames 70–78 as the nod starts | **chosen** |
| v3 | `seedance/returned/P1-S1_v5_take_v3.mp4` (3a6ec42f647245e9) | The head drifts from frame 12. Two eye closures (around 46 and 82–90). Tracking reads up to 66° with large head travel | Ends in a deep bow, the face moving far forward and almost out of the head crop | not used |

Both are 1280×720 HEVC, 24 fps, 121 frames, about 280 kbps. Both carry generated audio, which is
discarded. Both were made from the approved S1 *with* its light, and the model kept that light fixed.

**Masking and compositing (`tools/p1_s1_clip.py`):**
- **Trim:** the rule is the head-turn frame (61) minus 9, so clip frames **52–91** play at 1:1 on song
  7.500–9.167. The nod is about 33° at the cut and settles (37°) just after it. The cut to the hand
  insert comes on the last part of the nod.
- **Generated light masked out:** inside a disc around (907, 89), the sky comes from the light-free
  approved frame. It is aligned to the take (affine fit on frame 0) and colour-matched on the ring
  where it fades out (r 120–155 px). Measuring the take's own glow left faint rings, because that
  light sits too close to the top of frame.
- **Designed light composited:** it has the approved orb's measured look. It starts exactly where the
  approved light is (at most 0.5 px from the take's), sinks ahead of her nod (leading her measured
  nod curve by 4 frames, along a gentle curve with a slow float and pulse), and ends in front of her
  lowered gaze, above her hand (approved-frame coordinates (1010, 425)). In S2 it enters from the
  top.

**Measured on the output:**
- 146 frames, 0 irregular steps; audio 6.083 s.
- S1: the old light's spot is empty in every frame, and the new light is the only light.
- Head turn: 1.6° at frame 10, 8.9° at 20, 16.7° at 26, 25.5° at 32, 33.2° at 39.
- Sky shift 0.0 px.
- The take's body follows the nod slightly: the collar moves 8.7 px and the hand 24.8 px by the cut.
- Frame-to-frame change: the two cuts dominate. Inside S1 there are steps of up to 2.6, because the
  take moves on threes.

**For your playback:**
- **The eye closure** during the nod (song 8.25–8.58). It reads like a natural blink with a gaze shift.
  If you don't want it, the only fix is another take.
- **The motion on threes** (the take's own animation) against the smooth local S2 and S3.
- **The S1→S2 cut** on the end of the nod.

---

## Earlier local build notes (S1 local 2D nod, kept as fallback)


Owner decision (2026-10-02): no more generation for this sequence. Use the approved S1–S3 images
directly, and deliver at 720p.

| file | what it is |
|---|---|
| `tests/P1_light_catch_720p.mp4` (S1 local when built with P1_S1_SOURCE=local) | 1280×720, 24 fps, 146 frames: song 7.500–13.583 on the locked music, one continuous encode |
| `tests/P1_light_catch_strip.jpg` | 10 frames with song time |
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
