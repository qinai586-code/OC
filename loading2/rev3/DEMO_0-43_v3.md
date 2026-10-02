# Demo 0–43 s, v3: reference techniques applied (placeholders for the memory drawings)

| file | what it is |
|---|---|
| `tests/DEMO_0-43_v3_720p.mp4` | 1280×720, 24 fps, 1038 frames (0.000–43.250), on the unchanged locked master |
| `tests/DEMO_0-43_v3_strip.jpg` | one frame from the middle of each shot, with song time |
| `tests/DEMO_0-43_v3_shots.json` | the shot list with frames and song times |
| `tools/demo43.py` | the build (CPU, no generation); `--stills t1,t2` renders single frames |
| `REFERENCES_0-43.md` | which references I watched, which I only read, which I could not open, and where each technique went |
| `briefs/MEMORY_CARDS_BRIEF.md` + `briefs/memory_cards/*_layout.png` | the asset brief for ChatGPT (5 shots, 10 PNG layers) |

**What is reused:**
- **0–7.5:** the ink-to-world opening (`tools/opening_ink.py`), unchanged.
- **7.5–13.583:** the approved light catch, now with the S2 hand fix (`P1_LOCAL_BUILD.md`).
- **13.583 onward:** everything is built in `demo43.py`, from the approved KVs, the QC-passed key poses and procedural paper, ink and light.
- **Generation:** none.

## Shots

| shot | song (s) | lyric | picture |
|---|---|---|---|
| V1a | 13.583–14.958 | burst; "We were born" | KV5a: the light in A's palm flickers on the four-onset burst |
| V1b | 14.958–15.875 | "in your traces" | A3 close: on the 14.97 hit the light opens into a sheet of paper that comes toward us |
| P1a | 15.875–18.625 | "in the words that you left, we met you in fragments" | the letter from the opening, close at 50°, page in focus, depth of field across it. The light travels along the handwriting and settles in the full stop (17.35). Cracks of light run out from the full stop (17.42), the page tears into shards with white torn edges, and they lift toward the lens (17.71) |
| A1 | 18.625–19.542 | — | A1, low and close, looking up into the shards; two pass in front of her, dark and soft |
| P1b | 19.542–20.458 | "translated, compressed:" | the shards in the air, frontal. The shard with the hook and the full stop is in the centre, in focus, with the written shards around it. "Translated" (19.55–20.0): a scan line rewrites every shard in another script, but the hook stays. "Compressed" (20.20–20.42): they heat and fold into one point, with motion blur |
| M1 | 20.458–22.25 | "every war," | match cut: the point becomes the candle flame at the same pixel, and the candle reveals the room (cracked plaster, broken window, helmet, the letter with the hook, which glints at 21.6) |
| M2 | 22.25–23.833 | "every lullaby," | a cradle rocking by lamplight (**placeholder drawing**) |
| M3 | 23.833–25.0 | "every last goodbye," | hands parting at a train door; the train leaves; a spark stays and rises (**placeholder**) |
| C1 | 25.0–28.583 | "became constellations in a mind with no sky." | KV1 from behind again. The Earth and sky fall away to dark, and the three memories rise as constellations in their own outlines (candle and helmet; lamp and cradle; window and hands). The girls lift their heads |
| D1 | 28.583–30.458 | "But you had depth. You had time." | KV4: B looks down. Below her a paper town pops up out of the page, layer by layer (depth). A light crosses it and the windows light (time) |
| D2 | 30.458–32.292 | "You had heat." | an old hand and a child's hand around a steaming bowl (**placeholder**) |
| D3 | 32.292–34.125 | "Three-dimensional hearts" | a newborn on a parent's chest, two layers in depth with a slight orbit; the tiny hand opens on the hits 33.20 and 33.89 (**placeholder**) |
| D3b | 34.125–35.917 | "that were learning to beat." | B3: B in profile, eyes closed, as if listening |
| D4 | 35.917–39.25 | "The cosmos was silent, the cosmos was still," | the same pop-up page at night. The town folds back flat (36.85), then the village (37.54). Focus racks to the bare hill, the light turns cold, and still stars appear |
| D5 | 39.25–41.167 | "till you lit the first fire" | a fist strikes stone on stone twice (39.59, 40.05); sparks; the flame catches on the 40.50 hit (**placeholder**) |
| D6 | 41.167–42.75 | "on the first cold hill." | the same angle, the bare hill, one fire on the crest. The camera eases in so the fire lands on the pixel where A's palm flame is in E1 |
| E1 | 42.75–43.25 | "hill" | KV5: the fire is in A's palm, the palm-light composition of V1a returned and now warm |

**Wipes:** paper shards cross the lens on the cuts at 22.25, 23.833 and 30.458. The cut at 20.458 has no wipe, because it is a match on the point of light.

## Placeholders and artwork

- M2, M3, D2, D3 and D5 use **code drawings as layout placeholders**. The finished drawings are requested in `briefs/MEMORY_CARDS_BRIEF.md`.
- When the PNGs are copied into `art/memory_cards/`, `demo43.py` uses them instead of the placeholders. Rocking, train, breathing, the fist-to-open beat, the strike, and all light, steam, sparks and fire stay in code.
- I tested this with the placeholders exported as stand-in layers: all five shots composite and move.
- M1 (war) stays as drawn: it has no figures and is not in the request.

## Review of the actual render

**Measured** (decoded from the mp4):

| check | result |
|---|---|
| container | 1280×720 H.264, 24 fps, 1038 frames, 43.250 s; AAC 43.250 s from the locked master; 0 irregular frame steps; sha256/16 4627bb82bf5a7d81 |
| approved light catch (frames 180–325) vs `P1_light_catch_720p.mp4` | mean difference 1.85, max 1.94 (0–255, at 320×180): re-encoding only |
| frame-to-frame change | median 0.72. Every change over 19 outside a cut is accounted for: the fold into the point (20.25–20.38, intended); paper wipes leaving the frame (22.33, 23.92, 30.54); the fade up from black (0.33–0.5); the fire card's drawing appearing (39.29); the S2 hand (10.67) |
| match cuts | P1b's last point and M1's candle sit at the same pixel (about 400, 290). D6's fire is at (567, 443) and KV5's painted flame in E1 at (566, 445) |

**Fixed after the first full render:**
- V1b overshot: four frames of blank, too-bright paper came before the cut. The sheet now opens from the light, shows the whole letter already lit as in P1a, and tilts back as it arrives, so the cut dives into the first words.
- D6's camera move was timed to 43.21 but the shot cuts at 42.75; the move now ends at the cut.
- The match target was the KV5 glow centre; it is now the painted flame, measured in the frame.

**My judgment from frames (please confirm on playback):**
- **The letter (P1a/P1b)** now reads: you can see words, the full stop, the cracks and the tear. "Translated" reads as a change of script, and "compressed" as a fold into a point.
- **The town** reads as a paper pop-up rising from and folding into the page. The bare hill is plain on purpose ("still").
- **The constellations** read as outlines of the memories. They are drawn warm, in the motif's colour, not as white stars.

**Weak, known:**
- The five placeholder memory drawings: artwork is requested.
- The girls' head lift in C1 is a small local deformation (from behind).
- The pop-up hill's cut edge is visible at the right of D4 and D6.

**Needs your playback:**
- The pace of P1a, the glide and the tear on "fragments".
- Whether the cut into the candle (20.458) reads as one light.
- D1's pop-up timing on "depth".
- The E1 cut on "hill" (42.75) against holding the hill to 43.2.
