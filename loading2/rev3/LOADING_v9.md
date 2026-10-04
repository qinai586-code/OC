# LOADING v9: full-length candidate (0–213.4 s)

**Candidate:** `tests/LOADING_v9_full_720p.mp4`
- 1280×720 H.264, 24 fps, **5122 frames**, 213.417 s, 0 irregular frame steps, 79.0 MB;
- sha256 `162c58cfe022b3a92b068d7c910a3d6d53777a01a3b8236b1750ec32a65fa6a3`;
- encoded once from the lossless master (below): crf 18 (chosen to stay under GitHub's 100 MB file limit; crf 14 gave 137 MB), preset slow, aq-mode 3, BT.601 limited range (untagged, as every earlier version).
- **Audio:** the locked `Loading_P0_endfix_candidate01.mp3`, unchanged and complete (213.41 s decoded), AAC 192 kb/s.
  - Correlation with the locked file: **0.9996 at 0 ms** over the whole length; lowest 10-s window 0.9991.
  - **The reverb tail is kept:** the last 2 s have 0.997× the locked file's level. Nothing is appended after it; there is one ending.

**Lossless master:** the v9 0–43.25 master plus one lossless segment per shot (libx264rgb qp 0, RGB).
- 41 parts, 1,735 MB, in the session scratchpad (`…/scratchpad/v9/`). Not in git: too large.
- Every segment decodes bit-exactly to its rendered frames (checked when each was written).
- Content hash over all 5122 decoded frames: sha256 `73e64a7222a49cd53cdd3352530358026ce0002acce6f5b8e86d8acb811fe763` (`…/v9/LOADING_v9_full_master_parts.json`).
- One 2 GB single-file copy does not fit on this disk next to the parts. `song_v9.py` can join them when there is room.

**Kept, unchanged:** v8 and every earlier version in `tests/`; the original project's render (`out/LOADING_MV.mp4`).

**Not changed:** the music, A and B's identities, and the earlier Earth-fold, dark-block and ending fixes.
- v9's 0–43.25 differs from v8 **only** in frames 54–179, 360–379, 686–730 and 862–939.
- Every other frame of 0–43.25 is bit-identical to v8's.

**Constraints followed:** no generation, paid service, purchase or new account. The rejected code character and Astra's studies were not used.

---

## 1. How the film is built

| span | what it is | made from |
|---|---|---|
| 0–43.25 s (frames 0–1037) | the v9 opening: v8 with the six repairs in §2 | approved KV1 and plates, the approved P1 stills, the four Seedance takes already in the project, the paper town and hill material |
| 43.25–213.4 s (frames 1038–5121) | **the original project's (rev1) shots S07–S47**, following the lyrics line by line | rev1's code (`loading/src`) and its derived plates from the approved asset pack (KV1–KV5, BG0a/b), rendered again through `tools/rev1_bridge.py` |

**Why rev1 for 43–213.**
- It is the only complete full-song material in the project built from approved art.
- It was already designed against the lyrics (each shot's description quotes its line: `loading/docs/SHOTLIST.md`).
- The rev3 plan's later scenes (lantern folding, walking, hands on glass, stepping into the drawing) need character animation that does not exist and cannot be made without new generation (§5).

**The join at 43.25 s.** v9 ends on the approved hill with the first fire; S07 opens wide on the forest with the same fire on the hill.
- v9 moves S07's first camera position so the fire lands where it was on the last opening frame: **(568, 433) vs (568, 430)**, a match cut on the light.
- The camera then glides into rev1's own move by 45.0 s.
- "Silence in the forest" starts at 43.5 s.

### Changes to rev1 (all in `rev1_bridge.py`; rev1's code is untouched and still reproduces rev1)

| change | rev1 | v9 | why |
|---|---|---|---|
| finish | grain 1.6%, chromatic aberration 0.4–0.6 px, a 14-px diffusion blur screened in at 5–12%, a paper-tooth overlay, vignette 0.26 | none of them; vignette at 40%; the light's own bloom kept | restrained effects, clarity |
| resampling | 1080p float, then encoded at 1080p and scaled down for the 720p preview | rendered at 1080p float, **downscaled once** to 720p (Lanczos-3 + anti-ringing, as the opening), lossless | one resample, no extra lossy generation |
| camera zoom on the plates | up to 2.75× (S17) | **capped at 1.3×** for every shot using rev1's camera (S12 excepted, below). Where the cap applies, the frame centre and its parallax reference are kept inside the plate: the wider view at S15's off-centre framing otherwise ran past the plate edge and the mirrored border drew a kink into the Earth's limb. Not capped: S20 (the BG0a Earth plate, to 1.6×) and S40 (to 1.7×), which build their own matrices | at 1.3× the approved originals are shown at about 1.08× of their own pixels; at 2.75× they were 2.3× magnified and soft |
| S12 "the Planck scale is fog" | a 14× push until the painting showed nearest-neighbour pixel blocks, then random-noise fog | a push to 3.2× while the paint thins and defocuses into the paper it is painted on (procedural fibres) | no fake pixels or noise; the edge of what's known is the sheet itself |
| S13 / S22 unrender fronts | 5-octave noise down to 4-plate-px detail: torn, ragged lines | the same large shapes, fine raggedness removed (σ 14 plate px) | less "glitch", more paint |
| S14 painting edge | distance to the border + 300 px of 5-octave noise: a torn-paper silhouette | a brushed edge: only the large waves (σ 40), 45 px | the painting should read as unfinished, not torn |
| S19 card | paper albedo × 0.10–0.65: a flat grey quad | albedo ×1.55 + 0.05 (rev1's shading model unchanged) | it should read as paper catching earthlight |
| colour washes (S42, S46, S47) | arrival map with noise down to ~30 plate px; soak 0.07 s; wet-edge darkening 0.28 | arrival map smoothed (σ 24 plate px; the warped shape stays); soak 0.22–0.6 s; darkening 0.12 or less | rev1's fronts were torn and ragged. A wide soak alone (tried) read as smoke; the smoothed map gives a defined, organic paint edge |
| S07 opening camera | — | the match-cut offset above | continuity across 43.25 s |

---

## 2. The six items in 0–43.25 s

Native-pixel sheets: `tests/v9_evidence/*_native.png` (1:1, no scaling; context rows are marked as scaled).

| item | v8 | v9 | evidence | limitation kept |
|---|---|---|---|---|
| **3 s drag blur** | the girls slid 520 px up during 2.62–3.34 s under a 0.3-frame shutter: a 6-px smear at 3.0 s | **the slide is removed.** Before the cut only Earth and sky are in frame; the camera's push continues at a 0.075-frame shutter. The girls appear in place on the **cut** to the rear two-shot between frames 80 and 81, on the first chime (3.344 s). No sample is averaged across the cut | `1_landing_3s` | the cut replaces the landing motion; it does not animate it. The landing exposes KV1's painted "hidden Earth" fill (a darker ocean band, frames 72–80); checked at native size and kept |
| **source-soft 3.625–9 s** | 3.625–7.458 s was the Seedance rear take (soft in the file: one 69 KB I-frame, then about 1 KB per frame) | **3.375–6.6 s is the approved KV1 art** (A's small head lift 5.55–6.35 s and B's glance up 5.90–6.50 s on the art itself). **6.625–7.458 s is A's view of the light** in KV1's sky | `2_rear_3.4-6.6s` | **7.5–9.2 s is still the S1 Seedance take** and still soft (`7_9s_S1_unchanged`). It holds the approved head change, so I kept it. No sharpening or upscaling was applied; none would restore what the file lost |
| **hand/palm and light jump at 7.5 s** | the hand lifted on the soft take; the light changed position and size at the cut | A looks up → **cut to what she sees** (the light against KV1's sky, drifting to where the S1 take has it) → the S1 take with her palm raised. Light on frame 179: (909, 89); on frame 180: (908, 90) | `3_7.5s_light_cut` | **the hand lift is not shown.** The cutaway hides it; it is an elision, not an animated catch |
| **D1 gaze without a cause** | began after the strip had lit; B was already looking | starts on the dim strip (source frames 0–44): **the strip brightens (28.96 s) → B blinks (src 12–17) → her eyes drop to it (src 18–27) → the cards rise**. A warm front along the strip carries the brightening; her near side warms with it, 3 frames behind | `4_D1_event_gaze` | the reaction is the source's own small blink and eye shift. No head turn was added, and the warm front is added light, not new motion |
| **sudden paper** | the note appeared at full exposure in the air above the palm | the note rests in the palm cup under the glow; it shows as the glow shrinks (14.97–15.12 s), lifts (15.10–15.58 s) and unfolds toward the viewer in two folds, its back showing while each panel turns | `5_V1b_paper_entrance` | the fold is a four-panel card fold, not a drawn paper animation |
| **terrain/ground** | a hill crease and a road under the paper town | the approved plate's own terrain (rows 760–941) printed under the town as it lands: tiled without mirroring, low-passed tone plus a third of its detail, so its ledges don't read as stripes; the hill's occlusion softened to 0.94–1.0 | `6_D4_ground` | the print is a texture placed under the town, not a 3-D ground; the town's contact with it is by shading only |

---

## 3. Clarity: source, pre-encode and final

| span | source | pre-encode (master) | final mp4 |
|---|---|---|---|
| 3.375–6.6 s (KV1) | the approved 1536-px original at about 0.9× on screen | one antialiased resample | 39.4 dB mean (37.7 min): the finest drawn lines lose most here; the standalone `DEMO_0-43_v9_720p.mp4` (crf 10) keeps more |
| 7.5–9.2 s (S1 take) | **soft in the file** (one 45 KB I-frame, then mostly under 1 KB per frame) | bit-identical to the take where the light doesn't reach | 45.2 dB mean (43.8 min) |
| 43.25–213.4 s (rev1) | approved plates at ≤ 1.08× of their original pixels (zoom cap); procedural elements rendered at 1080p | one downscale 1080p → 720p | 42.8 dB mean (36.5 min, the S42 wash over line art) |
| whole film | — | — | **43.2 dB mean, 36.5 dB lowest frame** against the master; 113 frames below 38 dB |

**Correction to the v8 report.** v8 said `KV1.png` (3072 px) "is not an upscale". **That was wrong.**
- The 3072-px plates in `loading/work/plates` are **2× Real-ESRGAN (anime) upscales** of the approved 1536×1024 originals.
- Downscaled back, KV1 matches its original at 38.7 dB.
- So the detail limit of every plate shot is the 1536-px original. Nothing in v8 or v9 recovers detail beyond it, and I don't claim it does.

---

## 4. Lyrics and timing (uncertainty kept)

rev1's shots follow its own Whisper song map (`loading/docs/SONG_MAP.md`). Where that map and the author's text or the plan disagree, **v9 does not decide by retiming or by putting words on screen**. There is no on-screen lyric text anywhere in the film.

| item | rev1 / ASR | plan v2 / author text | in v9 |
|---|---|---|---|
| Verse 2 start, "You sent out your signals" | 73.0 s | 74.6 s (ASR window 73–76 hears "Universe, you sent out") | S15's rings start at 73.0. If the line starts at 74.6, they lead it by 1.6 s. **Not retimed** |
| Chorus 1, 70.3–70.7 s | "an unfinished universe" | "an **unanswered** universe" (ASR hears "unfinished") | S14's image (a painting unfinished at its edges) leans to "unfinished". **Unresolved; needs listening** |
| Final Chorus F01–F04 ("Where we live is a simulated universe / … every light that went out and never said goodbye") | not heard; a held "I…" 163.3–168.2 | unresolved: near silence 163.5–164.5, one held voice 165.0–168.0, harmonics to 171.2 | S40 (163.3–168.2) stays **wordless**: the page of marks and the two lights descending. The four lines are neither shown nor claimed |
| "And one day we'll be paper" | 168.2 s (vocal level returns here) | 170.3 s | S41 starts at 168.2. If the line is at 170.3, it leads by 2.1 s. **Not retimed** |
| "And we'll still be in the …" | "light / eye" | "art" | S42: colour returns to the drawing outward from the flame. The image fits either word |

**Not verified by ear.** I can't listen; every time above is from ASR, levels and the plan's measurements.

---

## 5. What is missing, and what it limits

Searched: the repo, the session's uploads and ZIPs, the scratchpad, rev1's and rev3's derived assets. **The material does not exist:**

| missing | where the lyrics/plan want it | what v9 does instead | resulting limitation |
|---|---|---|---|
| any approved animation of A or B **walking, standing, turning, flying or reaching** | travel (S24–S26), the room (S27–S34), "we flew out past the stars" | rev1's convention: they travel as **two lights** (teal and amber); in place they are the approved stills with breathing, eyelids and sway | from 43 s on, **the characters perform no body action**. Continuity of action is carried by the lights, not by the girls |
| **lip-sync** material for A or B (front or profile mouth shapes matched to the song) | sung lines | no one is shown singing | no performance shots |
| **hands** (on keys, on glass, holding a lantern, folding paper) | S34 "who's pressing the keys", the lantern scenes | keys press themselves (as the lyric says); lanterns are carried by small procedural travellers | no hand contact anywhere after 15.8 s |
| approved **room / console / chair** art | 115–143 s, 158–160 s | rev1's procedural line-drawn room on paper | these shots are bare line drawings, deliberately unpainted, and read as stark |
| approved **forest / travellers** art | 146–158 s | rev1's procedural pencil forest and travellers | S36 is a 5.6× view of a 3072×4400 procedural raster: soft lines (the zoom cap doesn't apply to procedural layers) |
| the **Bilibili references** BV1HNh265E78 and BV1Snh96jEPR | method study | not reachable from this container: the network proxy refuses both www.bilibili.com and api.bilibili.com (CONNECT 403, re-checked this round) | **not verified, so no timestamps are cited.** The two methods named in the brief (consistent wire geometry, ~1:25; one continuous path, ~1:48) were used only as described in words: S14/S30's construction lines extend the painting's own perspective, and S37's path continues from the travellers' steps into the sky as one line. Neither is claimed to follow those videos |

---

## 6. Unresolved defects (honest list)

**0–43.25 s**
1. The hand lift at 7.5 s is elided by the cutaway, not shown.
2. 7.5–9.2 s (S1), D1 and B3 are still as soft as their Seedance files.
3. D1's reaction is small: a blink and an eye shift.
4. The 3.36 s cut replaces the landing motion, and the landing shows KV1's darker hidden-Earth fill for about a third of a second.

**43.25–213.4 s (rev1 shots)**

5. **No character action.** The girls are stills (breath, eyelids, sway) or lights for 170 s. This is the largest gap, and it follows from the missing material in §5.
6. **Long dark stretches:**
   - 45–49 s: stars and a small red point;
   - 77–80 s: the dark forest;
   - 88–91 s: the black "sleeve" of sky above the Earth.
   They are on-concept (silence, no answer, the sky's edge) but low in information.
7. **S19 (87.65–91.25 s):** the card is lighter now but still reads as a plain quad sliding out of a black band.
8. **S14 (66.75–73 s):** the painting's edge is a brushed vignette with a dark pooled rim. It reads as a cut-out frame more than paint fading out.
9. **S42/S46/S47 washes:** the edge is clean now, but it is still dark night colour spreading over white paper. Around the flame (175–177 s) it can read as a shadow before the painting shows through. At 205–208 s the front crosses A, so for a moment she is half drawn, half painted.
10. **S13/S22 unrender fronts:** still blob-shaped (smooth now, not torn).
11. **S12 (61–63 s):** the paper fibres that replace rev1's pixel blocks read partly as scratches.
12. **The room (115–143, 158–160 s):** bare line drawings on grey paper.
13. **S36 (150–153.5 s):** soft procedural pencil lines (5.6× zoom on a procedural raster).
14. **The 43.25 s join** cuts from the approved hill painting to rev1's procedural forest hill: different drawing styles for the same place. The fire is matched in position, not in size.
15. **Lyric-timing items in §4:** two shots may lead their lines by 1.6 s and 2.1 s.

16. **Measured, not judged,** from `qc_v9.json`:
   - **Near-black frames** (mean luma < 8):
     - 0–6, the start;
     - 600–616 (25.0–25.7 s), unchanged from v8;
     - 1405–1429 (58.5–59.6 s), S11's pull-back before S12;
     - 2689–2729 (112.0–113.7 s), the start of S26 before the stars stream;
     - 5100–5121, the fade, with the music's tail under it.
   - **Frozen holds** (≥ 4 identical frames):
     - 2343–2363 (97.6–98.5 s, S21's flattened map, 0.9 s);
     - 4685–4709 (195.2–196.2 s, S45, 1.0 s);
     - 4776–4788 (S45's end, 0.5 s);
     - others are 0.4 s or less.
     The two longest may read as a stall.
   - **Largest frame-to-frame changes** are all planned cuts between paper and night (1752, 2536, 2602, 3436, 4037), plus v8's own 600 and 819.
   - **Smooth joins:** the S41→S42 and S46→S47 joins change by about 1 level (continuous).

---

## 7. Files

| file | what |
|---|---|
| `tests/LOADING_v9_full_720p.mp4` | the candidate |
| `tests/LOADING_v9_full_strip.jpg` | one frame every 2 s, whole film |
| `tests/v9_evidence/1…8_*_native.png` | native-pixel comparisons (§2, §3, rev1 before/after) |
| `tests/v9_evidence/qc_v9.json`, `roi_metrics.json` | QC and box metrics |
| `tools/rev1_bridge.py` | renders rev1 shots with the v9 changes |
| `tools/song_v9.py` | render → lossless segments → master parts → preview |
| `tools/qc_v9.py`, `tools/v9_evidence.py` | QC and the sheets |
| `tools/opening_ink.py` (`OI_STAGE`), `demo43.py` (`DEMO_STAGE`), `v9_pov.py`, `m26/build_d1_v3.py`, `master_v9.py` | the 0–43.25 repairs (v8 reproducible with `OI_STAGE=v8 DEMO_STAGE=v8`) |

**Reproduce:**
```
cd loading2/rev3/tools
python3 song_v9.py render          # S07..S47 -> lossless segments (verified)
python3 song_v9.py master          # parts list + content hash
python3 song_v9.py preview 18
python3 qc_v9.py && python3 v9_evidence.py
```
