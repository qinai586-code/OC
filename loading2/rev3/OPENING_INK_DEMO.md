# Opening demo v2: the stroke becomes the lived world (0:00–0:13.583)

| file | what it is |
|---|---|
| `tests/OPENING_INK_demo_v2_720p.mp4` | the demo: 1280×720, 24 fps, 326 frames, on the unchanged locked master |
| `tests/OPENING_INK_demo_v2_strip.jpg` | 15 frames, with song time |
| `tools/opening_ink.py` | the build: about 3 min on CPU; `--check` renders single frames |

- **Generation:** none.
- **0–7.5:** code compositing over KV1, with procedural paper, ink and pen.
- **7.500–13.583:** the approved light catch, decoded unchanged. It matches the approved file to within encoding (mean difference 1.9/255); the approved file was untouched for this v2 (sha256/16 f91e896ce1ebc75f). The S2 masking leak you reported was left as asked.
  - **Later:** the leak is now fixed; see `P1_LOCAL_BUILD.md` (new sha256/16 cd7a70a62d7f869a).
  - `tests/DEMO_0-43_v3_720p.mp4` uses the fixed file. This v2 file still contains the leak.
- **v1:** `tests/OPENING_INK_demo_720p.mp4` stays in git history for comparison.

## What changed from v1

| your note | v2 |
|---|---|
| The ink should feel like a human trace | It is now a letter written by a person: two lines of earlier handwriting, dry and faded, and a fountain pen whose nib and hand shadow move with the writing. Ink pools under the nib before it starts. The flourish is quick through the swash and slows into the curl, with nib-angle width, pressure and a fine hand tremor. The pen lifts and taps a full stop. Fresh ink is glossy and dries matte with darker edges, and the edges feather into the paper fibres. A faint inky thumbprint sits where the hand rested |
| The Earth is stretched at 2.6–3.2 s | The page tilts away first (to 50°), while it is still paper. The night Earth shows through only once the view is close to KV1's own angle and scale, so the painting is no longer seen from overhead. The pull-back is spread over 1.1 s with a gentler ease, and the motion blur is shorter (0.3 of a frame) |
| Warped character edges | The triple ghost outlines came from three-sample motion blur on a fast rise. The girls now rise earlier, from just below frame, easing out, blurred with 9 samples. The Earth behind them is filled as a rounded region, so the fill no longer traces their outline |
| A's gaze and hand before the cut | On "three" (5.55–6.35) A lifts her head: from behind, the crown settles toward the nape and the horns tilt back and shorten. On "two" (6.60–7.45) her right hand leaves the stone, rises toward her chest and passes behind her body; the stone is restored under it. B turns slightly toward her (6.70–7.35). From 5.45 the camera pushes slowly toward A (girls 7.5%, Earth 4.5%, for depth). The light turns down toward her at 7.05–7.50, and the cut lands in S1 with her head up and hand raised |

## Timeline (locked music)

| song (s) | picture |
|---|---|
| 0.000–0.232 | black |
| 0.232–0.55 | out of black on the drone: a lamplit letter seen from above, the pen resting at the end of the last line |
| 0.50–1.50 | the flourish is written, then the full stop is tapped (1.44) |
| 1.50–1.85 | the pen lifts and leaves; its shadow parts from it |
| 1.45–2.20 | evening crosses the page at an even pace. Behind it, every line of ink beads into warm lights; the flourish is brightest and the full stop brightest of all |
| 1.90–2.45 | the page tilts away |
| 2.25–3.344 | the camera pulls up about 6.8× and tilts on to KV1's angle. The paper gives way to the night Earth (2.58–2.92), the surface curves, and the horizon and sky appear. The parapet and girls rise into frame (2.62–3.344) |
| 3.344–3.82 | six onsets, six lights along the flourish toward the full stop |
| 3.82–6.70 | the full stop lifts as the light and rises above the girls |
| 6.70–7.05 | the light hangs |
| 7.05–7.50 | it turns down toward A |
| 5.45–7.50 | the slow push toward A; her head (on "three") and hand (on "two"); B's turn |
| 7.500–13.583 | approved S1–S3 |

**How it relates to the lyrics and the references:**
- **The lyrics:** the intro's countdown and "Loading." happen over a world assembled from a person's writing. "We were born in your traces, in the words that you left" is set up before it is sung, and there are no words on screen. The handwriting is illegible by design; the letter's wording is still your decision (D1).
- **The references:** like V1, it opens on a premise. Like V2, it changes scale by transforming rather than cutting: fast between worlds, a slow push inside one. The only glow is the approved light.

## Still proxies

- **Paper, ink, pen and hand shadow:** procedural.
- **The Earth behind the girls and under the parapet:** filled locally. It is visible for under half a second, in motion.
- **A's head and hand, and B's turn:** small local deformations of KV1. From behind they read as a look up and a hand leaving the stone. They are not full acting; her arm is never seen rising, because her body hides it.
- **A's X clip:** still on her right in KV1, which is not canon.

## Essential missing artwork (ChatGPT)

1. **KV1 edit (1 file):** A's X clip moved to her left (from behind, the screen-left side of her head), and her half-up ribbon added at the back of her head, as on the model sheet. Nothing else changes: same framing, poses, hands and light. I then redo her matte locally and the animation carries over.

**Optional:** a clean Earth plate, the same KV1 framing with both girls and the parapet removed, to replace my fill. It is no longer essential, because the fill now shows for under half a second, in motion.

**Not needed for this opening:** a Seedance clip. The look-up and hand lift are done locally. The S1 cut is a match on pose, because her head is up and her hand has left the stone.
