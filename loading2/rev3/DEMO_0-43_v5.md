# Demo 0–43.25 s, v5: war and hill plates, candidates, and the second round of repairs

| file | what it is |
|---|---|
| `tests/DEMO_0-43_v5_720p.mp4` | 1280×720, 24 fps, 1038 frames, 43.250 s, on the unchanged locked master. sha256/16 `18f871dd6752f901` |
| `tests/DEMO_0-43_v5_strip.jpg`, `_shots.json` | one frame per shot; the shot list with frames and song times |
| `tests/v5_evidence/*.jpg` | asset → shot evidence and before/after pairs (below) |
| `tools/demo43.py`, `tools/p1_local.py` | the build. v4 and v3 stay in `tests/` for comparison |

**How it was built:** only the affected shots were re-rendered (605 of 1038 frames). The rest come from the v4 frame cache unchanged: O, S1–S2, V1a, P1a, M2, M3, D2, D3. **Generation:** none.

## Assets → shots

| asset (file, size) | shot(s) | processing | evidence |
|---|---|---|---|
| `art/plates_v5/war_memory_v1.png` 1672×941, opaque | **M1** 20.46–22.25 | **Wick:** measured. The tip is at (289, 351) and the base at (292, 390).<br>**Opening:** the letter's point lands on the unlit tip at the same pixel. P1b's last frame is (261, 264); M1's first is (260, 262).<br>**Flame:** a candle flame is drawn on the tip (20.47–20.62).<br>**Reveal:** candlelight then finds the wax, the letter (with its stroke), the helmet and the ruins. The window keeps a cold moon fill.<br>**Framing:** the view opens from 1150 to 1500 px of plate width. The candle drifts to M2's lamp: M1's last frame is (168, 244), M2's first is (169, 242) | `M1_war.jpg` |
| `art/plates_v5/first_fire_hill_wide_v1.png` 1672×941, opaque | **D1 / D4** hill card<br>**D4** end<br>**D6** 41.17–42.75 | **Skyline:** measured on the plate.<br>**D1/D4:** the land below it is printed on paper as the pop-up hill, so the town and the village stand in front of the same terrain as the first fire.<br>**D4 end:** the gaze lifts to the hill card and squares to it. The print becomes the painted plate under its own sky (38.55–39.15), on exactly D6's last framing.<br>**D6:** the tinder (724, 596) and the flat stone are measured. The flame sits on the tinder. The view opens from 760 to 1540 px of plate width, starting on D5's flame point (566, 439 → 567, 439) and ending on the palm-light point (567, 430) | `D4_D6_hill.jpg`, `D6_E1.jpg` |
| `art/candidates_m23/Girl_A_side_palm_candidate_v1.png` 1672×941 RGBA | **V1b** 14.96–15.88 (replaces A3 there) | **Alpha:** source alpha inside the figure is 251–254, so it is rescaled (251 counts as opaque). Pixels more than 2.5 px from the transparent background are made opaque, which fixed 1667 partly transparent interior pixels. Real gaps and the anti-aliased edge are kept.<br>**Scale and position:** matched to A3's close by the X clip and the iris: scale 0.867, same angle.<br>**Grade:** night grade with warm palm light.<br>**Doubled contour:** the doubled fingertip contour is gone; it was in A3's drawing | `side_palm_V1b.jpg` |
| `art/candidates_m23/Girl_A_rear_seated_candidate_v1.png` 1024×1536 RGBA | **C1** observers (replaces KV1's old cut-out of A) | **Alpha:** same fix (569 interior pixels). The horn and head gaps stay open.<br>**Scale:** head-to-seat about 160 px; v4's KV1 figure was 145.<br>**Placement:** hands on the parapet line (candidate y 1075), left of B as in KV1.<br>**Grade:** cool night fill, with faint warm light from the constellation above | `rear_AB_C1.jpg`, `rear_AB_C1_zoom.jpg` |
| `art/candidates_m23/Girl_B_rear_seated_candidate_v1.png` 1024×1536 RGBA | **C1** observers (replaces KV1's old cut-out of B) | **Alpha:** same fix (376 pixels).<br>**Placement:** hands on the same line (y 1099), right of A. The star clip and ribbon read at this size | same |

**Where the rear views do not fit:**
- **Side and three-quarter shots:** A1 (A looks up in profile), D1 (KV4: B close, looking down), D3b (B3: profile, eyes closed), and V1a/E1 (KV5a: both seated, three-quarter front, A holding the light). A rear view shows neither face nor the palm, so it cannot replace them.
- **The approved opening (0–7.5):** it lands on KV1 by a fitted camera. A's right hand lifts off the stone at 6.6–7.45, while the rear candidate has both hands flat. Using it would mean re-posing the hand, which would be puppeting, and re-approving the opening.
- **The smallest adaptation:** none needed. The opening's figures sit on their own plate, so its matte never shows sky around the horns. The leak showed only in C1 v4, where the sky went dark behind the cut-out, and that is where the candidates now replace it.

**Key-pose mattes (A1, A3, B3; no candidate exists for these angles):** v4 eroded the white matte and faded the sides, which left a pale fringe and the white gaps between strands. The new `pose_matte` builds the matte from the drawing itself:
- **Background:** the white joined to the corners, plus white pockets enclosed by hair.
- **Pale pockets:** paper-like pockets joined to the background through narrow necks.
- **A's gaps:** for A, white gaps within 12 px of the outline that are mostly surrounded by dark hair, such as beside the horns and head and behind the braid.
- **Kept:** enclosed white bounded by line art stays (collar, shirt, ribbon stripes, eye highlights).
- **Edges:** edge pixels take an alpha estimated from the distance to paper white, with the white removed from their colour. There is no erosion and no fade.

I checked them on dark, neutral and light backgrounds and in the scene (`A1.jpg`, `B3_D3b.jpg`).

## Changes by time

| song (s) | shot | change |
|---|---|---|
| 7.50–9.08 | S1 | unchanged (the approved downward head and gaze) |
| 10.67–13.54 | S3 | **Gaze:** the iris lowers about 1.2 px on screen toward the sinking light (11.75–12.88).<br>**Wrist:** after the touch (13.04), the hand rolls about 2° toward her about the wrist and settles with a small damped overshoot.<br>**Fingers:** the fingertips close about 3 px around the light, then relax by a third.<br>No new reach or catch. The light is caught once, at 13.04 |
| 14.96–15.88 | V1b | **Asset:** the side-palm candidate.<br>**Sheet:** the light opens into the sheet, which rises *beside* her (its centre ends at x 935), so her face stays clear through 15.71 (frame 377).<br>**Response:** her eyes lift first (14.99–15.22), then her head 2° (15.06–15.46). The hanging hair follows later, and the hand eases as the light leaves.<br>**Dive:** the sheet reaches the lens only in the last 6 frames (15.625–15.875), arriving as P1a's first frame |
| 18.63–19.54 | A1 | new matte (the back-hair white patches and the gaps by the horn are fixed); the closed-mouth edit is unchanged |
| 19.54–20.46 | P1b | the fold lands on the war plate's measured wick |
| 20.46–22.25 | M1 | war_memory_v1 (above) |
| 25.00–28.58 | C1 | **First reveal.**<br>**Hands:** the parting hands of M3 are traced in light on the very pixels where M3 left them.<br>**Pull-back:** the camera dollies back. The war room (candle and flame, dish, the letter with its stroke, helmet and strap) and the cradle with its lamp are traced from their art. The spark leaves the hands' gap and becomes the full stop of the letter's mark. Threads tie the mark to the flame, the lamp and the hands.<br>**Field:** behind them, the letter's own handwriting in pieces, 230 fragments in depth.<br>**Observers:** last, A and B (rear candidates), small on the parapet |
| 28.58–30.46 | D1 | **Town:** three segments, the left one turned to face down the street.<br>**Street:** a cobbled road is printed on the page, walled by house cards on both sides.<br>**Supports:** a paper brace behind each standing piece.<br>**Occlusion:** all pieces are depth-sorted, so near pieces cover far ones.<br>**Landmark:** the hill card is the first fire's hill |
| 34.13–35.92 | D3b | **Place:** B3 (new matte) in her place on the parapet, with the night Earth behind her (KV5a's own background, out of focus).<br>**Breath:** one slow breath; the chest rises 2.6 px and the head less.<br>**Warmth:** A's light, off frame at her lower left, grows on her face. No rotation, no lip motion |
| 35.92–39.25 | D4 | **Second reveal:**<br>- **The past recedes:** the windows go dark, the paper yellows, and the town folds back (36.85), then the village (37.54).<br>- **The same place:** the gaze lifts to the hill, which is the same hill as the first fire's.<br>- **The plate:** the print becomes the painted place under its own still sky |
| 39.25–41.17 | D5 | **Preparation:** the fist lifts with the wrist cocked back (up to 4.5°), with a slow-in hold at the top.<br>**Strike:** it accelerates into contact on frames 950–951 and 961–962; the stone tip is on the lower stone, exactly as before.<br>**Rebound:** fast out, decelerating, with the wrist giving.<br>**Forearm:** it swings about the off-frame elbow (about 3°), so the arm is no longer one sliding block. Nothing is stretched |
| 41.17–42.75 | D6 | the hill plate (above). The fire holds its screen point while the place around it grows; the last 0.35 s is quiet |
| 42.75–43.25 | E1 | **Same light:** KV5a with the light still in A's palm, the light first caught in the opening. There is no new catch, fall or reach.<br>**Grade:** warm now; it settles and holds into the next section |

## QC of the actual render

**Measured** (decoded from the mp4):

| check | result |
|---|---|
| container | 1280×720 H.264, 24 fps, 1038 frames, 43.250 s; AAC 43.250 s from the locked master; 0 irregular frame steps |
| approved S1–S2 (frames 180–255) | mean difference 1.89, max 1.94 against `P1_light_catch_720p.mp4` (encoding only) |
| S3 (frames 256–325) | max mean difference 0.61 against the approved file: only the intended small settle |
| frame-to-frame change | **Median:** 0.76.<br>**Changes above 16 outside a cut:**<br>- the unchanged opening (frames 8–13);<br>- the P1b fold (486–488);<br>- the approved S2 hand (220);<br>- V1b's 6-frame dive into the letter (380, intended) |
| one light across the cuts | **P1b → M1:** (261, 264) → (260, 262).<br>**M1 → M2:** (168, 244) → (169, 242).<br>**D5 → D6:** (566, 439) → (567, 439).<br>**D6 → E1:** (567, 430) → (567, 436) |
| strike contact | the stone tip is on the lower stone on frames 950–951 and 961–962 |

**Seen in the rendered frames:** transition pairs at all 14 cuts, plus the stills in `tests/v5_evidence/`:
- **V1b:** the face is clear and the fingertip contour is single.
- **B3:** no pale fringe and no fade.
- **A1:** the horn and back-hair gaps are open.
- **C1:** the rear A and B show no sky leak around the horns.
- **M1:** the wick is lit at the measured tip.
- **D4 → D6:** the same terrain, then the fire, then the palm.

**Not verified by ear:** I cannot listen. The timings use the plan's word times (machine transcription) and onset analysis, including the strikes at 39.58 and 40.04 and the touch at 13.04. No character sings, so there is no lip sync to verify.

## Remaining limitations

- **The motion is small and procedural.** The S3 settle, the V1b gaze and head lift, the D3b breath and the D5 wrist all come from local warps of single drawings. They are restrained on purpose; whether they read as natural needs your playback.
- **D5's arm is still one drawing.** The elbow pivot and wrist bend add an arc and an angle change, but the hand cannot open or regrip.
- **C1's observers are small** (about 160 px). The rear candidates are flat-lit art graded to night, with no contact shadow beyond the parapet line.
- **B3 is still a key pose.** Grounding comes from her place and light, not from new body motion. A drawn breathing or turning layer would be needed for more.
- **B3 has one small drawn highlight** inside a hair pocket (lower left). It stays because it is not paper white.
- **The hill print in D1/D4** is the plate's own land, toned onto paper. Its "photographic" detail differs from the procedural town cards. That difference is intended (the place that outlasts the town), but please judge it.
- **E1 holds a still for 0.5 s.** It carries only the glow's slow pulse into the next section.
