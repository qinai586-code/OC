# Repair round for QX: three supplied shots, the ending, and a next-scene proposal (plan only)

**Status:** these are small repairs for review, **not an integrated new demo**. Nothing here replaces v6 until QX accepts it. v6 (`tests/DEMO_0-43_v6_720p.mp4`) is unchanged.

**What is changed:**
- the chroma (V plane) of the three supplied clips;
- which source frames are placed in the timeline;
- local window light in D1;
- the ending (E1 removed, D6 continued).

**What is not changed:** the music, the timing of every other shot, both characters' identities, and any generated material. No new generation was run, and nothing was paid for.

**Review files** (`tests/m26_review/`): each excerpt plays at original speed with the locked master's audio at the correct song time, including the surrounding cuts.

| file | song (s) | what to look at |
|---|---|---|
| `1_Opening_BEFORE_preview_2.50-9.00s.mp4` / `1_Opening_AFTER_…` | 2.50–9.00 | KV1 landing → Seedance rear shot → cut to S1 at 7.50 |
| `2_D1_BEFORE_preview_27.50-31.63s.mp4` / `2_D1_AFTER_…` | 27.50–31.63 | C1 → D1 (686–730) → D2 |
| `3_B3_BEFORE_preview_33.00-37.04s.mp4` / `3_B3_AFTER_…` | 33.00–37.04 | D3 → B3 (819–861) → D4 |
| `4_Ending_BEFORE_v6_39.25-43.25s.mp4` / `4_Ending_AFTER_…` | 39.25–43.25 | D5 → D6, now to the end |
| `5_chroma_*_native_before_after.png` | — | native-scale crops at source f60 / f10 / f110, colour unaltered except for the repair itself |
| `6_*_sheet.jpg`, `6_D1_window_light_sequence_716-730.jpg` | — | cut frames, window-light sequence, ending continuation |

---

## 1. Inventory: three shots (six MP4s)

The package's 27 files match `SHA256SUMS.txt`. I decoded the three sources myself (FFmpeg 6.1.1, `-hwaccel none`, raw YUV420P): **121 frames each, no errors.**

| shot | source (actual) | preview (existing trim) | measured mapping (package, accepted) | status |
|---|---|---|---|---|
| Opening | `Opening_rear_5s_seedance25.mp4`, HEVC 1280×720 24 fps, 121 f, 277 kb/s | `preview_Opening_trim_src0.833-4.958_100f.mp4`, H.264, 100 f | src 20–119 → prev 0–99 | **Chroma: repaired locally.** **Pose at the 7.5 s cut:** the preview's ending does not work; a usable source section exists (§3). **Overhead hand: not used.** |
| D1 paper city | `D1_papercity_5s_seedance25.mp4`, HEVC, 121 f, 252 kb/s, 1 invalid-NALU warning (package) | `preview_D1_trim_src1.0-2.833_45f.mp4`, H.264, 45 f | src 24–68 → prev 0–44 | **Chroma: repaired locally.** **Section:** src 8–52 gives the required action (§4). **Window light:** missing in the source, added locally. |
| B3 eye closure | `B3_eyeclosure_5s_seedance25.mp4`, HEVC, 121 f, 262 kb/s | `preview_B3_trim_src1.917-3.667_43f.mp4`, H.264, 43 f | src 46–88 → prev 0–42 | **Chroma: repaired locally.** **Section:** src 42–84 gives open → one slow closure → hold (§5). **New material:** none needed. |

### Chroma anomaly: what I verified independently

**Where the spikes are:** in all three sources the V-plane spikes sit at **8–12, 56–64 and 108–112** (V high-frequency energy up to 1.95×, 1.77× and 2.30× each clip's median). The neighbours step up toward a peak at 10, 60 and 110; Opening 59–62 is included.

**U and Y:** U is flat in every frame. Luma barely moves at those frames (Opening's luma residual at f60 is 0.13 against V's 1.70).

**Codec structure:** in every source, frames 8, 12, 56, 64, 108 and 112 are larger B-frames (2–8 KB), and 10, 60 and 110 are mid-size B-frames (1.3–4.8 KB) between them. The anomaly therefore follows the GOP structure, not the picture content: the same frame numbers are affected in three clips with different content.

**Not established:**
- the root cause (encoder, model or exporter);
- whether a cleaner platform download exists. I could not check the platform. **A cleaner original download is the first thing to try, and it remains unverified.**

### Detail and softness

- The sources' bitrate (252–277 kb/s) limits fine detail, especially D1's cards, which are also defocused by design.
- B3's eye, lashes and star clip, and D1's face, are stable at native scale.
- Nothing is regenerated for softness alone.

---

## 2. Local chroma repair (authorized, applied, verified)

**Method (`chroma_repair.py`):** only the V plane is changed, only in the three spans above, in YUV, before any RGB conversion. For each damaged frame:
1. A reference V is warped from the nearest clean frames on both sides, using luma optical flow.
2. Each anchor is weighted by how well its warped luma agrees with this frame.
3. Where neither agrees (eyelids, rising cards, the hand), the reference is a luma-guided filter of the frame itself. That applies to at most 2.5% of pixels.
4. The frame keeps its own low-frequency V. Only the fine chroma texture (finer than about 8 half-res px) comes from the clean neighbours.

**Unchanged:** Y and U are untouched, byte for byte. Frames outside the spans are byte-identical. No frame is deleted, interpolated or blurred.

**Measured on the repaired sources (V high-frequency peak ÷ clip median, 1.00 = no spike):**

| clip | before | after |
|---|---|---|
| B3 | 1.95 | 1.00 |
| D1 | 1.77 | 1.01 |
| Opening | 2.30 | 1.02 |

**Measured on the encoded review excerpts, within each shot's own frames:**

| shot | BEFORE (preview) | AFTER |
|---|---|---|
| Opening | 2.16 | 1.03 |
| D1 | 1.80 | 1.24 |
| B3 | 1.85 | 1.07 |

**Seen at native scale** (`5_chroma_*`):
- **Mottling:** the pink-green mottling on skin, hair and the black coat is gone.
- **Detail kept:** linework, eyes, lashes, star clip, horn highlights, city lights and window outlines are unchanged.
- **D1 limit:** D1 keeps a faint low-frequency tint variation at f60 (residual 1.24), because the rising cards move too fast for the flow to carry fine chroma reliably. I left it rather than blur it.

---

## 3. Opening and the 7.5 s cut

**Before** (the supplied preview, src 20–119 at 3.33–7.50):
- the preview ends with A's hand raised **above her head** (src f110–119);
- S1 at 7.50 has a **palm at chest height**.

The poses don't match, as the brief says.

**Measured in the source:**
- **Cameras:** both the source and v6's KV1 landing are static, with zero sky and parapet motion.
- **The two views:** the source frame is v6's KV1 frame at a 0.985 × 0.967 scale, so it is the same composition, re-drawn.
- **A's head and horns:** stable through f80 (mean luma change 2.5/255, the same as B's head). From f88 the hand rises and the head region changes, because the sleeve passes behind it.

**Usable continuous section:** **src f0–f98** at original speed, cut at 3.375 → 7.458 (timeline frames 81–179):
- From f0 to f72 both girls are still, apart from a breath, with B's slight head turn.
- From about f82 A's hand **releases the stone and lifts with the sleeve**, with a visible elbow and shoulder.
- **f98** (the last frame before the cut) has the palm turned up at **about chest height**, in front of her body. That is the same pose S1 opens on.
- The overhead reach (f104–120) is not used.

**Assembly:**
- **Landing:** v6's KV1 landing plays to 3.33. Over its last 8 frames the measured 1.5–3.4% scale difference is eased in. The cut at 3.375 lands on an identical composition.
- **Hand:** v6's own local hand lift (6.6–7.46) is replaced by the source's real motion.
- **Light:** the approved opening's rising light is drawn on top in the source's framing (same path, size and brightness), so the light catch that follows is unchanged.

**Not proven:** whether the 3.375 cut reads as invisible at speed (both are rear views of the same composition, but the Seedance frame is a redraw), and whether f82–98 reads as a natural lift. It is the source's own motion, but at 252 kb/s.

**If QX rejects this**, the smallest replacement is a new 4–5 s generation from the same rear composition (prompt P1 below), not a remake of the opening.

---

## 4. D1 paper city (686–730, 28.583–30.417)

**Before:** src 24–68. The city is already half built at 28.58, and her head move (src f14–30) happens before the shot starts.

**After:** src **8–52** at original speed.

| song (s) | what happens |
|---|---|
| 28.58 | Dark: one paper strip on the page; B watching |
| 29.0–29.8 | The strip lifts. Her **eyes move first** (the eye region tracks about 9 px up and left, against about 4 px for the face), then her **head follows slightly and settles** (src f14–30, about 1.25 s) as the street of cards unfolds toward her |
| 29.8–30.2 | The street rises; the far row begins |
| 30.17–30.42 | Windows light from left to right, local and warm. A **restrained warm light reaches her near cheek and hair** (up to 16%, near side only) |

**Window light: missing material.** The source cards never light; their window outlines stay empty to f120. I added the light locally:
- **Which pixels:** only the window interiors detected inside each card's own ink outline. A window that has lit stays lit: it is carried by optical flow, frame to frame.
- **What is unchanged:** the cards' shape, motion and blur. Her face, eye and star clip are untouched.

**Accepted from the source as is:**
- **Card edges:** some defocused card edges are soft. That is the source's lens blur, not melting.
- **No paper defects:** I saw no interpenetration or floating cutouts in 686–730.

**Missing action:** **none for this window.** If QX wants the far row to rise inside 686–730 too, that needs src 53–80, which would push past 30.46 and squeeze the shot. I have not done that.

---

## 5. B3 eye closure (819–861, 34.125–35.875)

**Before:** src 46–88. The eyes are already half-lidded at 34.13 and fully closed by about 34.9.

**After:** src **42–84** at original speed:
- **34.13–34.6:** eyes open (src f42–54);
- **34.6–35.2:** one slow closure (f54–70, the lid descends steadily, 0.67 s);
- **35.2–35.9:** a quiet closed-eye hold (f70–84). The face only shifts about 2 px as she settles, and the hair on the right is still (0.3 px).

**What it avoids:** no reopening, no smile, no canvas breathing, no head-width pulsing.

**Lighting and background:**
- The **source's own** night lighting (warm parapet glow, cool sky) is kept as delivered. This is a single-plate clip, so no matte is involved.
- **Limitation:** the source background is a soft parapet and starfield, not v6's KV5a crop. The two are similar in tone and composition, and B's edge in the source is clean.

---

## 6. Ending (39.25–43.25)

**D5 → D6 cut:** unchanged, at **frame 983 = 40.958 s**, verified in v6 and in this candidate. The fire's screen point moves from (567, 438) to (567, 437).

**D6 now runs frames 983–1037, to 43.25:**
- **The pull-back:** unchanged from v6 (to 42.02).
- **Settle:** after it, the camera opens a further 1.2% and comes to rest. Frame-to-frame change stays 0.24–0.59/255 through the last frame, so the image never freezes.
- **The fire:** keeps flickering and lights only the ground around the tinder. It stays small in the landscape at (567, 430).

**Removed:**
- **E1 (1014–1037):** the two-person palm-orb shot, and the halo enlargement that led into it.

**Not added:** no new catch, no spark into a hand, no fade to black. Nothing is looped or reversed.

---

## 7. Next scene: proposal only (needs approval before any production)

**Song timing, measured in the project, not invented:**
- **The lyric:** "on the first cold hill" ends around 42.9.
- **The pre-chorus:** begins with an onset at **43.21** (`OPENING_VERSE1_PLAN.md`), and "Silence in the forest…" starts about 43.3.
- **Machine transcription** (`docs/evidence/asr_3s_windows_0-160.txt`) agrees with the author text:
  - "Silence in the forest, every star holds its breath" is heard in 43–47 s;
  - "something vast is counting down the seconds to our depth" in 46–51 s;
  - Chorus 1 starts about 52.4.
- **Word level:** transcription confidence is medium. Word-level timing is **unverified by ear**.

**Proposal: "from one fire to the lights of everyone"**

**Purpose:** let the cold-hill line land on the fire, then cross time and scale to the people who came after it, and only then show the two observers. The first verse ends on one human fire. The pre-chorus opens on all human light, seen from the cosmic railing.

| song (s) | shot | camera / action | spatial and causal logic |
|---|---|---|---|
| 42.25–43.21 | D6 (this round) | the hill, the fire flickering, the camera settled | "cold hill" lands; quiet before the cut |
| **43.21 cut** | **PC1** | **match cut on the warm light's screen position:** the hill fire at (567, 430) cuts to one warm cluster of night-city lights at the same pixel, on the night side of Earth seen from orbit, tightly framed (no horizon, no characters) | a time-and-scale montage, legible because the frame changes completely while the warm point stays. **The cut is the time jump** (thousands of years and a planet's scale), not a zoom |
| 43.3–46.8 | PC1 continues | slow pull-back (about 4 s, ease-out): the cluster becomes one of many; coastlines and cloud shapes appear; the curve of the Earth enters at the top | "Silence in the forest, every star holds its breath": the scene stays dark and still; only the city lights shimmer slightly |
| 46.8–52.4 | PC2 | the pull-back continues past the **original cosmic railing**: the parapet's top edge enters as a dark foreground occluder, then A and B from behind, small, seated, hands resting on the stone, looking down at those lights. Hold | "counting down the seconds to our depth": the observers are revealed **after** the human light. Their scale against the Earth carries the shot. No sphere in a hand |
| 52.4 → | Chorus 1 | as planned (S08) | — |

**Why it works:**
- **One idea:** the shot is about the warm point. The verse ends on a single fire, and the pre-chorus begins on all human light in the same place on screen. The audience reads the cause (that fire) and the result (these cities) without being told.
- **The reveal order:** Earth first, then the railing, then the girls. That makes the scale change legible and keeps the dark negative space.

**Material needed (missing):**
- **PC1:** a night-Earth close of a warm city cluster, from orbit. Planned as **local**, from the existing night-Earth art: KV1's own globe texture and the opening's fitted globe camera can render this path and its pull-back procedurally. That needs a test.
- **PC2:** the railing reveal with A and B from behind, seated, hands on stone. The existing Message 23 rear candidates and the KV1 globe can composite this locally. The unapproved Earth still is a **reference only** (not a plate).
- **Only if** a local composite can't reach the needed quality: a generated continuous pull-back (prompt P4 below), after approval.

**Not done:** nothing for the next scene has been produced, rendered or integrated. The 43.25 excerpt is not extended.

---

## 8. Remaining full-song plan and material gaps

**Basis:** the shot list is `docs/PRODUCTION_PLAN_SIMULATED_UNIVERSE_v2.md` Table 2 (S07–S30), with lyrics from the author text. Times are machine-measured cues, not verified by ear.

| section | song (s) | shot purpose (from the plan) | material status |
|---|---|---|---|
| Pre-chorus | 43.2–52.4 | fire → city lights → observers (§7, replaces S07's forest idea) | **local test needed**; P4 only if needed |
| Chorus 1 | 52.4–74.6 | A sings (front close-up), the light front stops at a boundary; B studies the grain; wide two-shot, open question | **missing:** singing close-up performance (a test exists from rev2, not accepted); boundary/grain effects local |
| Verse 2 A | 74.6–89.2 | a signal rises; B folds the note into a lantern; a red countdown cue | **missing:** a lantern-folding hands insert (new motion) |
| Verse 2 B | 89.2–103.0 | the edge-on sheet descends; the world flattens far to near | flattening can be local (paper-world tools); **the climax must not reuse this section's memory imagery** |
| Pre-chorus 2 | 103.0–109.6 | the flat plane rises; they walk the rim | **missing:** walking motion (new generation) |
| Chorus 2 | 109.6–133.8 | float past the stars; the room, console, empty chair | **missing:** room/console/chair plates; float motion |
| Bridge | 133.8–162.5 | spoken lines; keys pressed by passing footprints; lanterns | **missing:** reverse-shot profiles speaking (no lip sync needed if voice-over); console plate |
| Final chorus | 162.5–192.0 | F01–F04 **disputed** (audio check needed); step into the drawing; return to the parapet; both sing | **unverified lyric/audio alignment** for 162–171; **missing:** step-through and return motion |
| Outro | 193.0–213.4 | two… three… one; "still loading" written in the trace's hand | local (ink tools exist) |

**Open gaps:**
- **Not available yet:**
  - a confirmed original-platform master for the three clips;
  - word-level lyric timing checked by ear;
  - the disputed final-chorus lines;
  - continuous footage for the Earth scene.
- **No approval yet:** the next-scene plan.

---

## 9. Generation prompts for review (not run; no paid generation without approval)

**Recorded platform controls:** Seedance 2.5, image-to-video, **first frame only, no end-frame slot used** (`OPENING_VERSE1_PLAN.md`, `seedance/` sheets). Output 1280×720, 24 fps, 121 frames (5.04 s), HEVC about 260 kb/s.

**Please confirm on the interface:**
- the exact duration options;
- whether an end frame or character reference is offered;
- whether a higher bitrate or resolution download exists.

**Only P1 and P4 are proposed, and P4 only if the local test fails.**

**P1: Opening hand release (only if QX rejects §3)**
- **Source / first frame:** Opening source f0, chroma-repaired (rear view, both seated, hands on the railing), exported as PNG.
- **Target:** 5 s generated; about 4.1 s used, at original speed.
- **Start pose:** as the first frame.
- **Action:** after about 2 s of stillness (breath only), A's right hand releases the stone. The fingers lift first, then the wrist; hand and sleeve rise naturally with the elbow bending and the shoulder following, to a palm-up hand at chest height in front of her body. Everything else stays still: B, the railing, Earth, the camera.
- **End pose:** palm up, at chest height, held still for the last 0.5 s.
- **Continuity:** A's skull, horns, X clip and hair length unchanged; body scale and the railing unchanged; static camera; night grade as the frame.
- **Negative:** no overhead reach, no pointing, no catching or holding light, no head turn, no horn or head deformation, no camera move, no fade, no added glow or particles.

**P4: Earth pull-back to the observers (only if the local test fails; needs approval of §7 first)**
- **First frame:** a local still of the warm city cluster from orbit, at the matched screen position, made from KV1's Earth.
- **Target:** 5 s generated, used about 3.5 s at original speed (43.3–46.8).
- **Action:** a slow, steady pull-back; the cluster becomes one of many, coastlines emerge, the Earth's curve enters at the top.
- **End pose:** the Earth's lower curve with dark space above, no characters (they are composited in PC2 from the approved rear views).
- **Continuity:** the same night-Earth style as KV1 (painted clouds, warm city lights).
- **Negative:** no characters, no text, no lens flares, no particles, no sudden lights.

---

## 10. QC summary

| check | result | how |
|---|---|---|
| package integrity | 27/27 files match `SHA256SUMS.txt` | `sha256sum -c` |
| source decode | 121 frames × 3; Y/U unchanged by repair; frames outside spans identical | software decode, byte compare |
| chroma spikes | removed in all spans (numbers in §2) | per-frame V high-frequency energy, before RGB |
| frame counts | excerpts 156/100/97/96 frames, as intended | `ffprobe -count_frames` |
| original music | each excerpt's audio matches the locked master at the right song time (correlation 0.978–0.999, offset 0 ms) | waveform cross-correlation |
| cut endpoints | Opening 3.375 (composition matched), 7.50 (palm at chest → S1 palm); D5 → D6 at 40.958 unchanged; D6 ends at 1037 without freezing | frames, registration, frame-to-frame change |
| single catch | the light is caught once (13.04); no palm-orb ending | frames |
| **not verified** | lyric/word timing by ear; whether the 3.375 cut and the f82–98 lift read naturally at speed; the D1 window-light timing feel; the cause of the chroma fault; whether a cleaner platform original exists | — |

**After QX accepts:** I'll integrate the accepted pieces into one 0–43.25 candidate (one render of the affected frames only) and then write the detailed next-scene plan.
