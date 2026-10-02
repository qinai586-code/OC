# References used for the 0–43 s demo (v3)

**Sources by kind:**
- **Watched:** footage I actually played, frame by frame on contact sheets.
- **Documented:** a creator's own written method or code, which I read but did not watch.
- **Unavailable:** a link I could not open from this container (Bilibili, YouTube, X and b23.tv are all blocked: 403 / egress blocked).

## What I could and could not inspect

| reference | status | what I used instead |
|---|---|---|
| github.com/mexicat/pdoom-video | **documented**: README, `docs/TREATMENT.md`, `docs/ENGINE.md`, `app/src/timeline.ts`, `app/src/scenes/_motifs.ts` | — |
| its rendered video (YouTube 5EoO5413dBY) | **unavailable** (YouTube blocked) | the methods above only |
| BV1SgaY64EG5 (foreground occlusion, perspective, depth) | **unavailable**. Identified by search as 穆阿蒂布, "Claude用代码搓了13015帧4K视频然后吃了你13亿Token", a code-rendered MV for Mili's "world.execute(me);". The source repos listed by search (lingcat521/world-execute-me, …-mv) return 404 | **Neonflare8052/MV** (another creator, who credits BV1SgaY64EG5 as an inspiration): **documented** methods in its README, `笔记.txt`, `claude/POLISH.md`, `train_cel_test`. Plus **V2**, **watched** |
| BV1zpaL6sEKw ?p=2 (economical key poses, varied framing) | **unavailable**; title and creator not identifiable by search | **V1**, **watched** |
| BV1P7aJ6LEJ1 (recurring compositions whose meaning changes) | **unavailable**; not identifiable by search | **V1** (watched) and pdoom-video's hook and bookends (documented) |
| V1: the PC-98-style "I'm Upping My P(doom)" MV (`gHnQCt53prC1koie.mp4`) | **watched** | — |
| V2: "Nothing Went Foom" (`w-44k0yAWFmugzpy.mp4`) | **watched** | — |

## What each one taught, and where it went

| technique | source | where it is in the demo |
|---|---|---|
| **One motif through the whole video:** pdoom's spark writes, draws, becomes a fuse and detonates | pdoom TREATMENT "Motifs" (documented) | the full stop. It becomes the light (opening), the sheet from her palm (15.0), the light that reads the letter and settles in the full stop (16.0–17.4), the cracks the page tears along (17.42), the point the fragments compress into (20.4), the candle (20.46), the lamp, the parting spark, the constellations, lit windows, the bowl's warmth, the heartbeat, the struck fire (40.5), the fire on the hill, and the flame in A's palm (E1) |
| **Visual events driven by the lyric, not illustrations of it**, each line given its own idiom | pdoom TREATMENT "Plates" (documented); V1 "I see sparks" / "roles swapped" (watched) | "words that you left": the light travels along the handwriting. "fragments": the page tears from the full stop. "translated": a scan line rewrites every fragment into another script. "compressed": the pieces fold into one point. "depth": the town pops up out of the page. "time": a day crosses it and the windows light. "silent, still": the town folds back into the page |
| **Spatial transitions instead of cuts between unrelated frames:** pdoom's camera plunges with the curve and rushes into the spark | pdoom (documented); V2's tunnel and bursts (watched) | a match cut on the point of light into the candle (20.458); B's downward gaze into the page the town rises from (D1); the crest fire landing where A's palm flame is (D6→E1, solved in code to the pixel) |
| **Foreground occlusion and depth:** near layers dark and out of focus, sorted cards, parallax | Neonflare `train_cel_test` / POLISH (documented); V2 particle and card depth (watched) | per-pixel depth of field on large cards (letter, page ground, town layers); fragments passing the lens dark and soft (A1, P1a, P1b); paper fragments crossing the lens on three cuts; the newborn on two layers with parallax; the rack focus from town to hill (D4) |
| **Dimensional change as meaning:** Neonflare's person (3D) → card (2D) → line (1D) → hole (0D) | Neonflare POLISH (documented) | the page (2D) tears into pieces in 3D, which compress to a point (0D); the town rises from the page (2D → 3D, "you had depth") and folds back flat ("silent, still") |
| **Economical key poses, varied framing:** held drawings, ECU / MCU / wide, the motion carried by cuts, camera and effects | V1 (watched) | A3 close with the palm (V1b), A1 low close looking up (A1), B in KV4 looking down (D1), B3 profile with eyes closed (D3b): held poses with slow push, drift and light, no puppeting |
| **A recurring composition whose meaning changes** (V1's chair shot "servant" → "boss"; pdoom's hook escalation and matching bookends) | V1 (watched), pdoom (documented) | KV1 from behind returns in C1 with the sky gone ("a mind with no sky") and the three memories as constellations; KV5a's palm light (V1a) returns as KV5's palm flame (E1); the same pop-up angle carries town → village → bare hill → one fire (D4, D6) |
| **Cuts on the beat grid, at or before each line's first word** | pdoom `timeline.ts` (documented: windows derived from aligned lyrics) | `SHOTS` in `tools/demo43.py`; see `OPENING_VERSE1_PLAN.md` §3 for the times |

## Not used (deliberately)

- **Lyrics as on-screen type** (pdoom's karaoke rules, V1 and V2's typography): our MV keeps words off screen. The letter's handwriting stays illegible by design.
- **pdoom's change of visual style per plate:** we keep one paper-and-ink world and the two girls' anime look.
- **Generated characters or new character art:** the girls appear only as the approved KVs and model-sheet poses.
