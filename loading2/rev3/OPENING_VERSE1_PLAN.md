# Opening and Verse 1: plan v2 (0:00–0:43.25)

**Status:** for review. Nothing has been generated for it.

| delivered | file |
|---|---|
| animatic over the unchanged locked master, 1280×720 picture with a 96 px strip below it (shot, source tag, provisional lyric, what the final needs) | `tests/OPENING_VERSE1_ANIMATIC_v1.mp4` (1038 frames, 24 fps, 43.250 s) |
| cut list as data | `tests/animatic_v1_shots.json` |
| build | `tools/animatic_v1.py` (about 1 min on CPU) |
| layout references for the requested stills (composition only, never style) | `requests/opening_layout_refs/IMG-xx_layout.jpg` (`--layout-refs`) |
| A's clip, checked by anatomical side | `seedance/review/A_clip_side_check.jpg` |

**Approved light catch kept:**
- `tests/P1_light_catch_720p.mp4` is untouched (sha256/16 f91e896ce1ebc75f).
- In the animatic, song 7.500–13.583 (frames 180–325) is that file decoded and re-encoded with the rest: visually the same (mean difference 2.0/255, encoding only), not bit-identical.

**Animatic source tags** (shown in the strip):
- APPROVED: the light catch.
- EXISTING: KV1/KV5a as stills.
- ROUGH: drawings made here.
- PLACEHOLDER: B3.

Lights, glows, marks, steam, fire on the crest and window lights are drawn as the final would do them locally.

**Sources:**
- the owner's tagged author lyrics (`../docs/Simulated_Universe_author_lyrics_tagged.txt`);
- the locked master `4ccd5715-Loading_P0_endfix_candidate01.mp3`, unchanged;
- ChatGPT's design handoff (2026-10-01);
- the owner's direction of 2026-10-02 and the review of plan v1.

## 0. What changed from v1

| review point | change |
|---|---|
| 1. Human traces, war, lullaby, farewell readable; fewer overloaded short shots; time across phrases | Cuts follow phrases, not words. The letter's four phrases ("in the words that you left, we met you in fragments, translated, compressed") are **one** 4.375 s shot, down from three shots in v1. War, lullaby and farewell get **one shot each** of 1.79 / 1.58 / 2.08 s, up from 0.875 / 1.5 / 1.25 s; the time is borrowed from the letter. Each shows one concrete event: the hand finishing a letter in a war-damaged room; a hand rocking a cradle; clasped hands parting at a train door. "Depth" and "time" share one shot (B1). |
| 2. Fewer returns to the two-shot and palm light; echoes kept | The KV5a palm-light composition appears **once** in 0–43.2 (V1). v1 had it four times: V1, V3b, V4, B8. Its echo, the flame in A's palm, opens the pre-chorus at 43.21. The opening wide (KV1) returns once, as V4, where the three marks gather above the girls. Everything between 16.1 and 43.2 is human events and places. |
| 3. The light's turn into the approved descent; posture before the light catch | O1 is one wide shot, 0–7.5. The light is born on the measured six-onset cluster, rises, hangs 6.70–7.05, then **turns down and toward A** in 7.05–7.50, and continues as S1's approved descent (§3.1). Posture is checked: seated in KV1; S1 opens waist-up with her right hand already raised. SD-1 must bridge that (§3.2). |
| 4. A's clip against the approved original artwork | Verified by anatomical side (§3.3). Canon: her **left**. KV1 and the approved S1–S3 have it on her right; KV2 and KV5a match canon. IMG-01 corrects KV1. The S1–S3 deviation is listed as decision D3. **v1's proposal to move KV5a's clip to her right is withdrawn:** it changed canon to match a newer shot. |
| 5. One alternate rendering at most; the mark separate from lettering; no one-family requirement | One alternate rendering only (placeholder; unverified, D1). The hooked mark is drawn on the paper and never lifts, fragments or translates; only the lettered line does. The three human moments are unrelated people; nothing links them except the kind of mark each leaves. |
| 6. A historical transition replaces the lights-out sequence; one landscape angle | B1, B4 and B6 use **one camera angle**: a valley town under a rounded hill, with the crest at 68% across and 33% down. B4 dissolves **town → old village with oil lamps → land before habitation** on the measured hits 36.85 and 37.54. It goes back in time instead of switching lights off. The first fire is struck in a close insert (B5) and then seen as a point on that same crest (B6). |
| 7. Word timings provisional; onsets and pitch don't prove lyrics | Every lyric time below cites its transcription windows and carries a confidence. Cuts and key actions are tied to **measured onsets** wherever a phrase allows (§1.3), so a later word-timing correction moves little. The music is unchanged. |

## 1. Timeline

### 1.1 Measured audio (locked master and its separated stems)

| time (s) | what | method |
|---|---|---|
| 0.000–0.232 | silence | RMS |
| 0.232 | the sustained bed enters; the mix rises from −40 dB to −29 dB by 5 s | onsets, RMS |
| 3.344, 3.471, 3.529, 3.634, 3.704, 3.820 | a cluster of six onsets in the accompaniment | onsets |
| 5.631 / 6.641 / 7.500 | onsets on the vocal stem | onsets |
| 7.5–11.6 | strong vocal-stem energy, the mix swelling to −20 dB; pitch spread about 21 semitones. **What it is, is unresolved** | RMS, pitch |
| 11.587 | onset on both stems; the swell ends | onsets |
| 13.05 | vocal onset | onsets |
| 13.45–13.75 | near-silence (−53 dB at 13.5) | RMS |
| 13.804, 13.874, 13.932, 13.990 | a four-onset burst | onsets |
| 14.47 | vocal onset | onsets |
| 14.97/15.65, 18.61/19.30, 22.26/22.95, 25.91/26.60, 29.56/30.24, 33.20/33.89, 36.85/37.54, 40.50/41.17, 44.13 | **a low double hit,** 0.68 s apart, every 3.645 s | 30–120 Hz onsets |
| 43.21 | onset | onsets |

These are onsets and levels. They time sounds; they do not show which word is sung or what a sound means.

### 1.2 Lyric lines, provisional

- **Text:** the author's tagged lyrics.
- **Times:** transcription windows on the vocal stem (whisper large-v3). Each window line in the evidence files is "start–end: what the model heard".
- **Evidence files:** `../docs/evidence/asr_verse1_boundary_windows.txt` (1.2–1.4 s windows) and `asr_3s_windows_0-160.txt` (3 s windows).
- **Mishearings** are quoted as heard and not interpreted.
- **Confidence:** high ±0.05 s; medium ±0.2 s; low ±0.4 s.
- **Final word timing is set on playback.**

| line (author text) | provisional start | evidence | conf. |
|---|---|---|---|
| Three… two… one… | 5.631 / 6.641 / 7.500 | vocal onsets; 3 s windows 3–6 "Three.", 5–8 "3, 2, 1", 7–10 "One." | high |
| (7.5–11.6 swell) | — | 3 s windows 8–11 "\*Epic Music\*", 9–12 and 10–13 "you". This proves nothing about content | unresolved |
| Loading. | 13.05 | vocal onset; 3 s window 11–14 "Loading." | high |
| We were born in your traces, | 14.47 | onset; 13.55–14.95 "We were born"; 14.80–16.20 "Born in your traces" | high (start) |
| in the words that you left, | ≈16.0–16.3 | 16.00–17.40 "Decision, the words that you"; 16.30–17.70 "And the words that you left" | medium |
| we met you in fragments, | ≈17.5 | 17.20–18.60 "you left, we met again"; 17.50–18.90 "We met you"; 19.00–20.40 "When fragments translate" | medium |
| translated, | ≈19.6 | 19.60–21.00 "Translated" | medium |
| compressed: | ≈20.2 | 20.20–21.60 "Compressed" | medium |
| every war, | ≈21.4 | 21.40–22.80 "Every war, heavy" | medium |
| every lullaby, | ≈22.3 | 22.30–23.70 "Heavy lalalalapa"; 22.90–24.30 "Lullaby every" | medium-low |
| every last goodbye, | ≈23.8 | 23.80–25.20 "Every last goodbye" | medium |
| became constellations | ≈25.0–25.3 | 24.40–25.80 "Last goodbye became"; 25.30–26.70 "became constant"; 26.20–27.60 "constellations in them" | medium-low |
| in a mind with no sky. | ≈27.0 | 27.00–28.40 "In a mind with no"; 27.40–28.80 "A mind with no sky" | medium |
| But you had depth. | ≈28.6 | 28.20–29.60 "No sky, but you had to"; 28.60–30.00 "Bet you had debts" | medium |
| You had time. | ≈29.6 | 29.60–31.00 "You had time you" | medium |
| You had heat. | ≈30.8 | 30.80–32.20 "You had he-"; "heat" held to about 32.6 | medium |
| Three-dimensional hearts that were learning to beat. | ≈32.4–32.7 | 32.40–33.80 "Three dimensional"; 32.70–34.10 "3 dimensional heart"; 34.20–35.60 "That we're learning to" | medium |
| The cosmos was silent, | ≈35.9–36.2 | 35.90–37.10 "the cause"; 36.20–37.40 "the cosmos"; 36.80–38.00 "The cosmos is silent" | medium-low |
| the cosmos was still, | ≈37.8 | 37.80–39.20 "The cosmos"; 38.20–39.60 "The cosmos was still" | low |
| till you lit the first fire | ≈39.4 | 38.60–40.00 "…was still, till you"; 39.00–40.40 "But still, till you lit"; 40.00–41.40 "You lit the first fire" | low |
| on the first cold hill. | ≈41.2 ("hill" ends ≈43.16) | 41.00–42.40 "Fire on the first"; 42.20–43.60 "First cold head" | low-medium |
| (pre-chorus) Silence in the forest | 43.21 | onset; 43.30–44.70 "Silence in" | medium |

**Voices:**
- Casting is the author's intent: the calm close voice is B (countdown, B's half); the luminous airy voice is A (the first half of the verse).
- Whether the recording audibly separates them is unverified.

### 1.3 What the edit is tied to

**Cuts on measured onsets:**
- 7.500 ("one");
- 22.250 (hit 22.26);
- 25.917 (hit 25.91);
- 41.167 (hit 41.17).

**Actions on measured onsets:**
- the light's birth on the cluster (3.344);
- the burst flicker (13.80–13.99);
- B's touch (14.97);
- the newborn's fingers (33.20 / 33.89);
- the two historical dissolves (36.85 / 37.54);
- the flame catching (40.50).

**Cuts on provisional lyrics (move on playback):**
- 16.083, 20.458 and 23.833 (medium);
- 28.583, 30.875 and 32.708 (medium);
- 35.917 (medium-low);
- **39.250 (low).**

## 2. Shot timings (as in the animatic)

All cameras are fixed. Every shot is "start state → one action → visible change".

| shot | frames | song (s) | dur (s) | lyric (provisional) | event | animatic | final source |
|---|---|---|---|---|---|---|---|
| O1 | 0–179 | 0.000–7.500 | 7.500 | bed; cluster; "Three… two…" | Wide from behind: both seated on the parapet above the night Earth. Fade-up completes on the cluster. The light is born on the cluster from the lone city light between them, rises and hangs. On "three" A looks up; she lifts her right hand off the stone. B notices and follows her gaze. The light turns down toward A | EXISTING KV1 + local light | IMG-01 + SD-1 + local light |
| S1–S3 | 180–325 | 7.500–13.583 | 6.083 | "one" … "Loading." | approved light catch | APPROVED | unchanged |
| V1 | 326–385 | 13.583–16.083 | 2.500 | burst; "We were born in your traces," | Two-shot: the light in A's palm flickers on the burst. B's fingertip touches it on the 14.97 hit; it flares and flattens into a thin sheet of light | EXISTING KV5a + local light | IMG-02 + SD-2 + local light |
| V2 | 386–490 | 16.083–20.458 | 4.375 | "in the words that you left, we met you in fragments, translated, compressed:" | Letter ECU: the glow settles into a worn letter (16.1–17.0). Its one line lifts (17.75) and breaks into fragments (18.2–19.3). The fragments re-form as one alternate rendering (19.3–19.9), then compress into a point of light (20.2–20.45) at the next shot's candle position. The hooked mark stays on the paper throughout | ROUGH | IMG-03 + local lettering and effects |
| H1 | 491–533 | 20.458–22.250 | 1.792 | "…compressed: every war," | **War's aftermath:** candlelit room with cracked plaster, a broken window, dust and a dented helmet. A hand in a worn cuff finishes the letter's hooked stroke and lifts the pen; the stroke keeps a faint warm glow. The compressed light lands in the candle at the cut | ROUGH | IMG-04 + SD-3 |
| H2 | 534–571 | 22.250–23.833 | 1.583 | "every lullaby," | **Lullaby:** a parent's hand on a cradle rim rocks it; the night lamp throws the rocking shadow on the wall; a faint warm arc remains on the floor | ROUGH | IMG-05 + SD-4 |
| H3 | 572–621 | 23.833–25.917 | 2.083 | "every last goodbye, became" | **Farewell:** two clasped hands at a train door slide apart, fingertips last; the train pulls away left; a warm spark stays in the gap and rises | ROUGH | IMG-06 + SD-5 |
| V4 | 622–685 | 25.917–28.583 | 2.667 | "constellations in a mind with no sky." | **Echo of O1:** the same wide from behind. The sky and the Earth fall away to an even dark, with no stars. The three marks (hook, arc, spark) rise and join into a small constellation above the girls, who look up at it | EXISTING KV1 | SD-1's last frame + local |
| B1 | 686–740 | 28.583–30.875 | 2.292 | "But you had depth. You had time." | One landscape angle: a valley town under a rounded hill, layered from the foreground roofs to the far ridge (depth). Dusk turns to night and windows light one by one (time) | ROUGH | IMG-10 + local lights |
| B2 | 741–784 | 30.875–32.708 | 1.833 | "You had heat." | An old person's and a child's hands around one steaming bowl; a frosted window | ROUGH | IMG-07 + local steam |
| B3 | 785–861 | 32.708–35.917 | 3.208 | "Three-dimensional hearts that were learning to beat." | A newborn asleep on a parent's chest; the parent's breathing lifts them both. The baby's fingers flex on the hits 33.20 and 33.89 | PLACEHOLDER | IMG-08 + SD-6 |
| B4 | 862–941 | 35.917–39.250 | 3.333 | "The cosmos was silent, the cosmos was still," | Same angle as B1, night, going back in time: town → old village with a few oil lamps (36.85) → the land before habitation, frost and a still sky (37.54). Nothing moves | ROUGH | IMG-10 → IMG-11 → IMG-12, local dissolves |
| B5 | 942–987 | 39.250–41.167 | 1.917 | "till you lit the first fire" | Close on the cold hill: a hand strikes stone on stone, twice; sparks fall into dry grass; a flame catches on the 40.50 hit and lights the hand | ROUGH | IMG-09 + SD-7 (fire generated) |
| B6 | 988–1037 | 41.167–43.250 | 2.083 | "on the first cold hill." | Same angle as B1/B4, bare land: one small fire on the crest, the only light. Held through "hill" | ROUGH | IMG-12 + local fire |

**Next, outside this plan:** at 43.21 (pre-chorus) the KV5a framing returns with the small flame in A's palm, the closing echo of V1 (SD-8, deferred).

## 3. Continuity checks

### 3.1 The light: rise, turn, descent (O1 → S1)

- **O1 (KV1 coordinates, 3072×2048):**
  - born at (1571, 1167) on 3.344, the lone city light between the girls, pulsing on each of the six onsets;
  - lifts at 3.82 and rises, slowing, to (1585, 470), above and to the right of A's head, by 6.70;
  - hangs 6.70–7.05 with a small loop;
  - **7.05–7.50: turns down and toward A,** growing as it nears, and ends at (1470, 545);
  - it is beyond the girls throughout, so their silhouettes cover it.
- **S1 (approved):** the light starts above and in front of her face (screen-right in her right profile) and sinks down-left toward her lowered gaze and hand.
- **Across the cut:** the light is above her and ahead of her, moving down and toward her, and screen-left in both shots. The approved shot is unchanged.

### 3.2 Posture (before the light catch)

| | A | B |
|---|---|---|
| KV1 / O1 start | seated on the parapet's top, from behind; both hands on the stone (the right hand visible beside her hip) | seated on the parapet's top, to A's right |
| S1 first frame (approved) | waist-up in right profile; head tilted well up toward the light; **right hand already raised, palm up, at chest height** | not in frame |
| what SD-1 must do by 7.5 | lift her head toward the light (from "three", 5.63), then lift her right hand off the stone to chest height, palm up | turn toward A, then look up where she looks; stay seated |

**Result:**
- Seated in O1 is compatible with S1's waist-up crop: S1 shows the waist and coat but no legs.
- The cut at 7.5 is a match on pose, which SD-1 has to reach. If a take doesn't get the hand up, the S1 cut breaks; this is an acceptance item.

### 3.3 A's X clip, by anatomical side (`seedance/review/A_clip_side_check.jpg`)

| image | view | clip on screen | her side | vs canon (her left) |
|---|---|---|---|---|
| model sheet, front | faces viewer | right | **left** | canon |
| model sheet, profile detail | faces screen-left (her left side seen) | visible | left | canon |
| model sheet, side view | faces screen-right (her right side seen) | not shown | left (hidden) | canon |
| KV1 | from behind | right | right | **differs** → IMG-01 corrects it |
| KV2 | from behind | left | left | matches |
| KV5a | three-quarter front, facing screen-right | right | left | matches |
| S1 v8 / S3 v2 (approved) | right profile | visible | right | **differs** → D3 |

The ribbon: the sheet's side and back views show a half-up ribbon bow at the back of her head; S1–S3 have it; KV1 does not show it. IMG-01 adds it.

### 3.4 KV5a (V1, and the pre-chorus echo): staging found while checking

- **B's seat side:**
  - In KV1 (from behind), B is at screen-right, which is A's **right**.
  - In KV5a, the camera is in front of A and to her right: we see her face three-quarter, her right shoulder nearest, and the parapet's edge and the drop at screen-right. B sits behind her at screen-right, which puts B on A's **left**.
  - Screen positions agree (B is screen-right in O1, V1 and V4); the seat sides don't.
  - A physically consistent front view would put B at screen-left, crossing the line between them. → D4.
- **Which hand holds the light:**
  - My reading is her **right** hand: the wide sleeve runs from her near (screen-left) shoulder across the front of her body to the cuff. That matches S3, where the light is in her right palm.
  - In an earlier pass I read it as her left; please confirm. → D5.
- **Screen direction S3 → V1:** she faces screen-right with her palm toward screen-right in both. ✓
- **The coat:** the sheet's front and side views and S1–S3 have the coat off her shoulders. KV5a appears to have it up on her shoulders, and S3 → V1 is a direct cut. → D6.

## 4. Still requests (ChatGPT): 12 image files, grouped by dependency

**Count:**
- **12 image files:** 8 new stills and 4 edits.
- **No first/last-frame pairs:** every Seedance clip uses a first frame only.
- IMG-10/11/12 are one new still plus two edits from the same camera. They are used only for local dissolves, never as generation endpoints.

**General rules for all requests:**
- 16:9, at least 1920×1080 (edits keep their source size).
- 2D anime cel-shaded, the night palette of the approved key art.
- No text or watermark, no camera effects.
- The layout reference in `requests/opening_layout_refs/` gives composition only. Its colours, glows and drawn effects are not to be copied: lights, glows, steam, the marks and the crest fire are added locally.

**Dependencies:**
```
G1 girls (edits of approved key art):   KV1 → IMG-01        KV5a → IMG-02
G2 the letter:                          IMG-03 → IMG-04   (letter identity; candle position)
G3 human moments (independent):         IMG-05   IMG-06   IMG-07   IMG-08
G4 one landscape angle:                 IMG-10 → IMG-11, IMG-12 → IMG-09   (same camera; ground and night look)
```

### G1 — the girls

**IMG-01 · O1 (and V4) · edit of KV1**
- **Source:** `loading/work/plates/KV1.png`, 3072×2048. Output the same size and framing. Keep everything that matters inside the 16:9 band y 186–1914.
- **Purpose:** the opening wide, and SD-1's first frame.
- **Change only:**
  1. A's X clip moves to her **left**: from behind, the screen-left side of her head (KV1 has it on screen-right);
  2. add her half-up ribbon bow at the back of her head, as on the model sheet's side and back views.
- **Keep:** composition; both poses (seated on the parapet's top from behind, hands on the stone, A's right hand visible); B unchanged; the parapet, the night Earth, the lone city light between them; colour.
- **Identity:** A: model sheet (`reference/sheet_chatgpt.webp`), the hair-clip detail and side view. B: unchanged.
- **Lighting:** unchanged.
- **Do not add:** any glowing orb, stars or extra lights. The light is composited locally.

**IMG-02 · V1 · edit of KV5a**
- **Source:** `loading/work/plates/KV5a.png`, 3072×2048. Keep the 16:9 band y 160–1888.
- **Purpose:** SD-2's first frame: A offers the light, B is about to touch it.
- **Change only:**
  1. replace the flame with a small round warm-white light, about the size of the flame's core, hovering just above A's cupped palm and lighting the palm and both faces softly from below;
  2. B's **right** hand (screen-left of her body in this view) raised halfway toward the light, fingers relaxed, not touching;
  3. *if D6 = yes:* A's coat lowered off her shoulders as on the model sheet's front view.
- **Keep:** A's clip on her left (screen-right here; already canon); B's star clip; both faces; the hand holding the light (her right, if D5 confirms); the parapet and background.
- **Identity:** A: model sheet. B: her model sheets (owner's `2.webp`, `3.webp`).
- **Lighting:** as KV5a, with the warm under-light now from the orb.
- **Continuity:** S3 → V1 is a direct cut. A faces screen-right, palm toward screen-right; the light is in her right palm.

### G2 — the letter

**IMG-03 · V2 · new still**
- **Purpose:** the letter plate. The lettered line, its fragments, the alternate rendering and the compression are local layers over it.
- **Framing:** ECU, top-down. The letter fills about 80% of the frame, turned about 3°; a dark wooden table shows at the edges. Layout: `IMG-03_letter_layout.jpg`.
- **Content:**
  - old cream writing paper, folded in quarters (creases visible);
  - a tea stain ring lower right; a torn upper-right corner; a faint inky thumbprint lower left;
  - **one hooked handwritten mark** in dark ink below the centre: a short flourish ending in a hook, like the tail of a signature;
  - **the band above the centre is left blank:** no words or other writing anywhere (D2).
- **No** hands, pen or people.
- **Lighting:** warm, soft, from above left, as if from a candle off frame; dark surroundings.
- **Continuity:** IMG-04 shows this same letter, so the stain, corner, thumbprint and hook must be reproducible from this image.

**IMG-04 · H1 · new still** (reference: IMG-03)
- **Purpose:** SD-3's first frame: the war's aftermath, seen as a person finishing the letter.
- **Framing:** medium-close, slightly high angle over a table. Layout: `IMG-04_war_aftermath_layout.jpg`.
  - the letter lower centre;
  - the **candle at the left third, its flame at about 20% across and 42% down** (V2's compressed light lands there);
  - a dented steel helmet on the table at right.
- **Content:**
  - a damaged room at night: cracked plaster, a broken window with night beyond, dust on the table;
  - the same letter as IMG-03 (stain ring, torn corner, thumbprint), with one short line of small handwriting (need not be legible) and the hooked mark;
  - a right hand in a worn uniform cuff holds a pen whose nib rests at the end of the hook;
  - the writer's face is out of frame.
- **Not shown:** no weapons, combat, blood, flags or insignia. It is the aftermath, not a battle.
- **Lighting:** candle key from the left; cold blue moonlight from the window.
- **Continuity:** the letter matches IMG-03; the candle position is fixed by V2.

### G3 — human moments (unrelated people; independent of each other)

**IMG-05 · H2 · new still**
- **Purpose:** SD-4's first frame: a lullaby at a bedside.
- **Framing:** medium, camera at cradle height. Layout: `IMG-05_lullaby_layout.jpg`.
  - a wooden rocking cradle centre-right, a baby asleep in it (face visible, eyes closed);
  - a small lamp on a side table at left;
  - the wall behind, where the cradle's shadow falls.
- **Pose:** a parent's arm enters from the right; the hand rests on the cradle's rim. The parent's face is out of frame (no singing mouth to sync).
- **Lighting:** warm low lamp from the left; cool night through a window at right.

**IMG-06 · H3 · new still**
- **Purpose:** SD-5's first frame: a farewell.
- **Framing:** close on two hands clasped across the gap at an open train door at night. Layout: `IMG-06_farewell_layout.jpg`.
  - the train car on the left, with one lit window and a face looking down at the hands;
  - the platform on the right with a lamp post; the platform edge below.
- **Pose:** one hand from inside the train (dark sleeve) and one from the platform (brown coat sleeve), fingers loosely interlaced.
- **Lighting:** warm light from the train's windows; cold platform light.
- **Continuity:** the train will leave screen-left, so leave room for it to move.

**IMG-07 · B2 · new still**
- **Purpose:** heat.
- **Framing:** close, three-quarter top-down. Layout: `IMG-07_heat_layout.jpg`.
  - an old person's hands (left) and a child's hands (right) around one bowl of soup on a wooden table;
  - a frosted window behind.
- **Lighting:** warm interior; cold blue at the window.
- **Note:** paint only light steam; the moving steam and the frost's glow are local.

**IMG-08 · B3 · new still**
- **Purpose:** SD-6's first frame: "hearts… learning to beat".
- **Framing:** close.
  - a newborn asleep on a parent's chest under a soft blanket;
  - the baby's tiny hand clearly visible, resting curled on the chest;
  - the parent's chin and shoulder at the top of frame.
- **Lighting:** warm and low.
- **Continuity:** keep the hand unobstructed; its fingers flex in SD-6.

### G4 — one landscape angle (town / village / bare) and the first fire

**IMG-10 · B1 (and B4's first state) · new still**
- **Purpose:** the one landscape camera. IMG-11 and IMG-12 are edits of it.
- **Framing:** wide, eye level, across a valley. Layout: `IMG-10_landscape_town_layout.jpg`.
  - a river along the valley floor;
  - a town along the valley and up the lower slope of one prominent rounded hill, **its crest at about 68% across and 33% down** (B6's fire goes there);
  - a far ridge behind;
  - foreground roofs and a balcony rail at lower left for depth.
- **Time:** blue hour; the sky still holds light. Windows mostly unlit (local lights add them).
- **Continuity:** the hill outline, ridge and river must stay identical in IMG-11 and IMG-12.

**IMG-11 · B4 · edit of IMG-10**
- **Content:** the same view centuries earlier: a small village of low houses along the river, a few windows lit by oil lamps, and a footpath up the hill. No modern buildings; no foreground roofs.
- **Time:** night.
- **Camera:** identical to IMG-10.

**IMG-12 · B4, B6 · edit of IMG-10**
- **Content:** the land before habitation: no buildings or paths. The same river and hill; dry grass and frost; a clear, still night with sparse stars and no moon. Nothing on the crest (the fire is local).
- **Camera:** identical to IMG-10.

**IMG-09 · B5 · new still** (reference: IMG-12 for the ground, frost and night look)
- **Purpose:** SD-7's first frame: the first fire, before it is lit.
- **Framing:** close, ground level, on the frosted hillside at night. Layout: `IMG-09_first_fire_close_layout.jpg`.
  - a small nest of dry grass and twigs on the ground, a flat stone beside it;
  - a weathered hand in a hide sleeve raises a striking stone above it.
- **Lighting:** dark; starlight blue. **No fire or sparks yet.**

## 5. Seedance requests (owner submits; after the stills are approved)

**Settings for every clip:**
- Seedance 2.5, image-to-video, **first frame only, no end frame**;
- 16:9, 24 fps if selectable, fixed camera, audio ignored;
- 5 s, the length of the owner's previous takes;
- return the original file, the settings and the seed.

**When a clip comes back, I:**
- check it with `tools/seedance_check.py`;
- trim it by the rule below, played 1:1 and never stretched;
- composite it locally.

| ID | shot | first frame | generated | usable (song) | trim rule | why it has to be generated | if not generated |
|---|---|---|---|---|---|---|---|
| SD-1 | O1 (+V4 plate) | IMG-01 | 5 s | **≈3.9 s** (≈3.63–7.500). Up to 5.0 s if the look-up lands later in the take; the first frame holds under the fade before that | A's head-lift onset → 5.631 ("three"); cut at 7.500. V4 uses the take's last frame | two characters' real seated acting; a 7.5 s still would be static padding; the handoff rules out cut-out puppets | not viable |
| SD-2 | V1 | IMG-02 | 5 s | **2.500 s** (13.583–16.083) | fingertip contact → 14.97 hit | hand contact between the two girls | not viable |
| SD-3 | H1 | IMG-04 | 5 s | **1.792 s** (20.458–22.250) | pen-lift onset → 21.75 | the human hand making the mark | still + local candle and dust: the mark appears without a maker |
| SD-4 | H2 | IMG-05 | 5 s | **1.583 s** (22.250–23.833) | start of a rock forward → 22.25 | hand and cradle moving together | rigid local rock of the cradle with the hand: reads as a cut-out |
| SD-5 | H3 | IMG-06 | 5 s | **2.083 s** (23.833–25.917) | fingertips' release → 24.75 | hands parting, train leaving | not viable |
| SD-6 | B3 | IMG-08 | 5 s | **3.208 s** (32.708–35.917) | first finger flex → 33.20 hit | breathing and finger flex (acting) | still: loses the "heart" beat |
| SD-7 | B5 | IMG-09 | 5 s | **1.917 s** (39.250–41.167) | the flame catching → 40.50 hit | the strike, sparks and ignition lighting the hand | local fire over a still hand: weaker |
| SD-8 | pre-chorus | KV5a | — | — | deferred (outside 0–43.2) | | |

**Totals:**
- 0–43.25 s: 7 clips, **35 s generated, ≈16.95 s used.**
- Screen time by source: the approved light catch 6.08 s; generated ≈16.95 s; stills with local motion ≈20.21 s. The stills are O1's first frame under the fade (≈3.6 s), V2 4.38, V4 2.67, B1 2.29, B2 1.83, B4 3.33 and B6 2.08.

### Prompts (the owner adapts wording to the interface)

**Negative for all (if supported):** camera movement, zoom, pan, cut, talking, lip-sync, extra people, extra hands or fingers, morphing, face distortion, outfit or hairstyle change, moving or changing hair clips, 3D render, photorealism, text, watermark, flicker, new glowing objects.

**SD-1 (IMG-01)**
> Fixed camera. 2D anime cel-shaded night scene, exactly as in the first frame: two girls sit side by
> side on a stone parapet high above the night side of the Earth, seen from behind. For the first two
> seconds they are still; only breathing, and the wind moves their long hair and the horned girl's
> tail a little. At about two seconds the horned girl on the left slowly lifts her head and looks up
> and slightly right, at something high in the sky ahead. At about three seconds she lifts her right
> hand from the stone and raises it, palm up, to chest height in front of her. The copper-haired girl
> notices, turns her head toward her, then looks up the same way. They hold, both looking up, still
> seated. Keep both girls exactly as in the first frame: faces, horns, hair, ribbon, hair clips,
> clothes. No new lights, no stars appearing.

Accept if:
- A's hand is up and her head is up by the cut point;
- both stay seated;
- the clips don't drift;
- the camera holds (≤ 2% drift);
- no light appears.

**SD-2 (IMG-02)**
> Fixed camera. 2D anime cel-shaded night scene, exactly as in the first frame: two girls sit close
> on a stone parapet; the horned girl holds a small round warm light just above her cupped right
> palm; the copper-haired girl's right hand is raised halfway toward it. For about a second they are
> still, both watching the light, breathing. Then the copper-haired girl moves her hand slowly
> forward and touches the edge of the light with one fingertip, and keeps it there. As she touches
> it, the horned girl lifts her eyes from the light to her face. They hold. The light stays the same
> size and in the same place; it does not move, fly or change shape. Keep both girls exactly as in
> the first frame.

Accept if:
- there is one clear fingertip contact;
- the light stays put (it is replaced locally);
- A's eyes go up to B;
- hands and fingers are clean.

**SD-3 (IMG-04)**
> Fixed camera. 2D anime cel-shaded night scene, exactly as in the first frame: a damaged room lit by
> one candle. A hand in a worn uniform sleeve holds a pen on a handwritten letter, the nib at the end
> of a hooked flourish. After a moment the hand finishes the flourish with one small flick, lifts the
> pen from the paper and rests on the table beside the letter. The candle flame flickers gently and
> steadies. A little dust drifts in the candlelight. Nothing else moves. Keep the letter, its marks,
> the candle, the helmet and the room exactly as in the first frame.

Accept if:
- the writing on the paper does not shimmer or change;
- the candle stays where it is (it is a match-cut target);
- the hand is clean.

**SD-4 (IMG-05)**
> Fixed camera. 2D anime cel-shaded night scene, exactly as in the first frame: a child's room lit by
> a small warm lamp. A parent's hand rests on the rim of a wooden cradle where a baby sleeps. The hand
> gently rocks the cradle back and forth, slowly and evenly, about one full rock every 1.3 seconds;
> the cradle's shadow on the wall rocks with it. The baby sleeps on, breathing softly. Nothing else
> moves. Keep the baby, cradle, lamp and room exactly as in the first frame.

Accept if:
- the rock is smooth and even;
- the shadow follows;
- the baby doesn't wake or change.

**SD-5 (IMG-06)**
> Fixed camera. 2D anime cel-shaded night scene, exactly as in the first frame: a train platform; two
> hands are clasped across the gap at an open train door, one from inside the train, one from the
> platform; a face watches from the lit window. After a moment the hands slowly let go, sliding
> apart, the fingertips the last to part. Then the train begins to move to the left, slowly at first,
> carrying the inside hand and the window away; the platform hand stays in the air a moment, then
> lowers. No other people. Keep everything else exactly as in the first frame.

Accept if:
- the fingertips part clearly;
- the train moves left;
- the face doesn't morph.

**SD-6 (IMG-08)**
> Fixed camera. 2D anime cel-shaded scene, exactly as in the first frame: a newborn sleeps on a
> parent's chest under a soft blanket in warm low light. The parent breathes slowly, and the baby
> rises and falls with each breath. Twice, about two thirds of a second apart, the baby's tiny fingers
> flex and curl, then relax. The baby does not wake. Nothing else moves. Keep the baby and the parent
> exactly as in the first frame.

Accept if:
- there are two small finger flexes, the gap close to 0.7 s (the second hit is at 33.89; only the first can be aligned);
- the breathing is calm.

**SD-7 (IMG-09)**
> Fixed camera, ground level. 2D anime cel-shaded night scene, exactly as in the first frame: a cold
> hillside with frost on dry grass. A weathered hand holding a stone strikes it hard against a flat
> stone beside a small nest of dry grass: one strike, then a second. Sparks from the second strike
> fall into the grass, a small flame catches, and it grows into a small steady fire that lights the
> hand and the frosted ground warm orange. Nothing else changes.

Accept if:
- there are two strikes;
- sparks land in the tinder;
- the flame grows from that spot;
- the fire stays small and steady.

## 6. Fire and light: who makes what

| element | shot | made by | how |
|---|---|---|---|
| the light: birth, rise, turn, flicker, flare, flattening into a sheet | O1, V1 (S1–S3 approved) | **local** | the approved orb's measured glow profile |
| the light settling into the letter; fragments; alternate rendering; compression | V2 | **local** | layers over IMG-03 |
| candle flame | H1 | **generated** (IMG-04, SD-3) | the compressed light's glow lands on it at the cut (local, about 0.3 s) |
| glow of the three marks: hook, arc, spark; the constellation | H1, H2, H3, V4 | **local** | |
| lamp; train and platform lights | H2, H3 | **generated** in the stills and clips | |
| window lights (town), oil lamps (village) | B1, B4 | **local** (lamps also painted in IMG-11) | |
| steam, frost glint | B2 | **local** | |
| first fire: strikes, sparks, ignition, warm light on the hand | B5 | **generated in SD-7** | local fallback: composite fire on the tinder if the generated ignition fails |
| the fire on the crest | B6 | **local** on IMG-12 | the same fire model as B5's fallback |
| flame in A's palm | pre-chorus 43.21 | existing KV5a drawing + local flicker | SD-8 later, deferred |

## 7. My local work once assets arrive

- Trim, align and composite every clip on the locked music (no retiming).
- Mask the generated light in SD-2 and replace it with the approved orb, as done for S1.
- Do all the local light, mark and fire work listed in §6.
- V2 lettering and effects; V4's matte and darkening on SD-1's last frame.
- B1/B4 lights and dissolves; B6's fire.
- Run the checks: container, regular timing, light count, camera drift and identity spot checks.

## 8. Batches (small, gated)

| batch | content | why first |
|---|---|---|
| 1 | ChatGPT: IMG-01–IMG-06 (6 files) | the story spine 0–28.6; I swap each into the animatic for review before any motion |
| 2 | Seedance: SD-1–SD-5 (25 s generated, ≈11.8 s used) | only after batch 1 is approved |
| 3 | ChatGPT: IMG-07–IMG-12 (6 files) | B's half |
| 4 | Seedance: SD-6, SD-7 (10 s generated, ≈5.1 s used) | after batch 3 is approved |

## 9. Decisions for you (all open points together)

**D1 · The letter:**
   - its line: "If you find this, I was here." is my proposal;
   - whether to show the one alternate rendering at all, and in which language. The Chinese line in the animatic is an unverified placeholder; whoever picks the language should verify it.

**D2 · How the line is lettered:**
   - (a) local lettering in a handwriting font over IMG-03. 1 file. No handwriting font is installed here; an OFL font would need to be chosen.
   - (b) ChatGPT writes the line in IMG-03 and gives a clean edit without it. 2 files; a third for a handwritten alternate.
   - I recommend (a).

**D3 · A's clip in the approved S1–S3 (her right; canon is her left):**
   - accept it;
   - paint it out locally (a canon right profile shows no clip, as on the sheet's side view). That modifies the approved shot, so I would do it only with your go-ahead, and show it side by side;
   - or regenerate later.
   - IMG-01 follows canon either way.

**D4 · B's seat side in KV5a:**
   - (a) accept: screen positions hold (B screen-right throughout), at no cost. I recommend this.
   - (b) replace IMG-02 with a new still on KV1's side of the line (B on A's right, camera behind or beside).
   - Mirroring KV5a is not an option: it flips both clips and crosses the line.

**D5 · KV5a's light hand:** confirm it is her right (my reading).

**D6 · KV5a's coat:** lower it off her shoulders in IMG-02, or leave it.

**D7 · SD-1 length:** 5 s, with the first frame under the fade (recommended), or 10 s covering 0.23–7.5 without a hold, if the interface offers it.

**D8 · Short human moments** (H1 1.79 s, H2 1.58 s, H3 2.08 s): judge on the animatic. V2 can give up about 0.5 s more if one doesn't read.

**D9 · V4:** SD-1's held last frame with local marks (recommended), or another clip of the girls watching.

**D10 · The B4/B5 cut (39.25) and the strikes:** "till you lit" is low confidence (±0.4 s); set on playback.

**D11 · The palm-flame echo** moves to the pre-chorus start (43.21), outside this animatic.

**D12 · The night sky over the bare hill (B4, B6):** a still sky with sparse stars. It is the real sky over the hill, kept apart from V4's starless "mind with no sky". Keep it, or go starless?

**D13 · Audio, unresolved (needs listening):**
    - the Intro's "muffled pulse": nothing pulse-like is measured before 14.97 (the transcription model's "rain"/"water splashing" labels for 0–5 s show nothing);
    - what the 7.5–11.6 swell is;
    - which sound "kick drops out" refers to, given the low hit still measured at 44.13;
    - whether the voices are audibly A and B;
    - "depth" stays the written word; the model's "debts"/"death" are quoted as heard and not interpreted.
