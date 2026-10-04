# Demo 0–43.25 s, v8: clarity round

**Candidate:** `tests/DEMO_0-43_v8_720p.mp4`
- 1280×720 H.264, 24 fps, **1038 frames, 43.250 s**, no irregular frame steps, 35.9 MB;
- sha256 `e66bc80a057084aed51ea526c8d3ef38b6d7302a5932c8389015a2c43f511216`;
- **Encoded from a lossless master** (below).
- **Audio:** the locked master, unchanged (AAC 192 kb/s as before); waveform correlation 0.9997 at 0 ms over 0–43.25 s.

**Lossless master:** `DEMO_0-43_v8_master_lossless.mkv` (RGB 4:4:4, libx264rgb qp 0, music as FLAC).
- It is in the session scratchpad (`…/scratchpad/v8/`), not in git: 263 MB is over GitHub's file limit.
- sha256 `b20d840f117f65d396e2c7c256a01e49bd9de0bd8e4e89c2041959bf1b04d4df`.
- It decodes to exactly the 1038 rendered frames (0 differing frames).

**Kept for comparison:** v7, v6 and earlier, unchanged in `tests/`.

**Not changed:** content, timing, music, A/B identities and the fixes from earlier rounds. Pre-encode frames differ from v7 only in 62–255, 686–730 and 819–861, and only by resampling and decoding (details below). No generation, purchases, accounts or new assets.

## Short answer

**Where the softness came from:**

| span | in the source | added by processing | added by the encode |
|---|---|---|---|
| **3.0–3.58 s** | no: KV1 is sharp | aliasing that broke up strands and outlines | yes |
| **3.625–7.458 s** | **yes, mostly** | about 3% | yes |
| **9 s** | **yes, mostly** | none on the face | two lossy encodes, the first one avoidable |

**What v8 removes:**
- the aliasing at 3.0–3.58 s;
- the extra encode generation at 7.5–10.6 s;
- the 2×2-block colour decode of the Seedance files;
- the final encode's losses and its ~0.9-level darkening.

**What v8 does not do:** it does not make the Seedance shots (3.625–9.17 s, D1, B3) sharp. Their softness is in the files we have. I did not sharpen or upscale, and nothing here restores detail those files lost.

## Diagnosis, stage by stage

Measured on native pixels in boxes on the eye, hair silhouette, horns, cloth and railing (`tests/clarity_v8/*.json`):
- **fine detail:** RMS of the 0.6–1.6 px band of luma;
- **acutance:** the strongest 5% of gradients;
- **colour-edge detail:** the same band on the colour-difference planes.

### 3.0–3.58 s: the opening landing (frames 62–86, rendered from `KV1.png`)

| stage | finding |
|---|---|
| **Source** | `KV1.png`, 3072×2048 lossless. Its spectrum falls off gradually up to 0.5 cycles/px; it is not an upscale. It has more than enough detail for 720p |
| **Scale chain** | **One** resample, 3072 → 0.42–0.56×. v6 asked OpenCV's `warpAffine`/`remap` for `INTER_AREA`. In warps, OpenCV silently replaces that with **bilinear and no prefilter** (verified: identical output). At 2.3:1 that skips source pixels, so hair strands break into dotted segments and the horn outlines stair-step. That is aliasing, not blur, and it reads as crunchy and smeared once encoded |
| **Blur / bloom / denoise** | **Deliberate landing motion blur** (0.3-frame shutter): at **3.000 s** the figures move 16–20 px per frame, a ~6 px smear; 2.4 px at 3.125 s; under 0.5 px from 3.25 s. The Earth smears ~3 px at 3.0 s. **I kept it**: without it a 17 px/frame move strobes. No bloom or denoise touches the figures; the light's glow is local to the light |
| **Encoding** | v7's crf 18, preset medium kept only 48–68% of the colour-edge detail in these boxes. It also darkened the frame by 0.9 levels: the default RGB→YUV conversion rounds down |

### 3.625–7.458 s: the rear two-shot (frames 87–179, Seedance `Opening_rear`)

| stage | finding |
|---|---|
| **Source** | Seedance 1280×720 HEVC, 277 kb/s: **one 69 KB I-frame, then about 0.9 KB per frame** for the other 120.<br>Against v6's KV1 render of the same composition, the file has **72–83% of the fine detail, 74–89% of the acutance and 40–54% of the colour-edge detail**. **The softness is in this file** |
| **Scale chain** | One warp (registration, 0.55% zoom and the push-in, composed into a single affine). Together with the decode it costs at most 3% of fine detail. The decode repeated each colour sample over 2×2 pixels and rounded to 8 bits |
| **Blur / denoise** | The round-1 colour repair low-passes only the V plane, only at source frames 8–12 and 56–64 (timeline 95–99 and 143–151). It never touches luma |
| **Encoding** | v7: 40–42 dB in the boxes; colour-edge detail −2 to −13% |

### 9 s: A's profile (frames 180–219, Seedance take v2)

| stage | finding |
|---|---|
| **Source** | `P1-S1_v5_take_v2.mp4`, HEVC 278 kb/s: **one 45 KB I-frame, then B-frames of 0–11 KB, most under 1 KB**. Static parts stay a copy of frame 0. Her turning head is rebuilt from motion-compensated blocks with almost no new detail.<br>The **generation itself** already lost detail: the take's first frame has **74% (eye), 80% (collar) and 85% (horn)** of the fine detail of the approved still it was made from |
| **Processing** | The light mask and the light do not reach the eye, profile, hair or collar boxes: those pixels are bit-identical to the take |
| **Encoding** | **Two lossy generations**: `P1_light_catch_720p.mp4` (crf 16), decoded, then crf 18 again.<br>Against the lossless frames: **PSNR 34.6–35.2 dB**, colour-edge detail −23 to −28%, and about 2 levels darker. **The first generation was avoidable** |

### The whole candidate: the final encode

Same decoder for both files; each mp4 is compared with its own pre-encode frames:

| shots | v7 (crf 18, medium, default conversion) | v8 (from the master: crf 10, slow, aq-mode 3, accurate conversion) |
|---|---|---|
| all 18 shots | **43.8–50.9 dB**, level bias −0.40 to −0.61 | **49.3–56.6 dB**, level bias −0.11 to +0.15 |

Per shot: `tests/clarity_v8/qc_v8.json`. Encoder settings test: `encode_settings_test.json`.

## What changed (render settings, before → after)

| frames | before (v7) | after (v8) | code |
|---|---|---|---|
| 62–86 (KV1 landing) | `warpAffine`/`remap` bilinear point sampling of the 3072-px plates | **Figures:** PIL Lanczos-3 with its support widened for the reduction, then clamped to the range of the source pixels underneath, so no ringing halos.<br>**Earth and sky:** sampled from a pre-filtered level at the frame's own scale (on whole pixels once landed).<br>**Unchanged:** the same geometry (alignment with v6 within 0.03 px, horizon within 1 px) and the same motion blur | `opening_ink.py` (`AA`, `aa_resize`, `plate_sample`); `OI_AA=0` reproduces v6 bit-exactly |
| 87–179 (rear shot) | OpenCV 4:2:0 decode (2×2 colour blocks, 8-bit), bicubic warp | **Decode:** cubic colour interpolation at the files' **measured** sample position (centred; checked against luma edges in all three sources), in float.<br>**Warp:** one Lanczos-4 warp.<br>**Unchanged:** the same registration matrix (reproduced exactly) and the same light. 50.7 dB from v7 (frame 90, whole frame) | `m26/yuv.py` `hq_bgr`, `m26/build_opening_v3.py` |
| 180–255 (S1–S2) | decoded from `P1_light_catch_720p.mp4` (crf 16) | **Built losslessly** by the same builders.<br>**Check:** the S3 rebuild is bit-identical to v7's S3; S1–S2 differ from the approved file only by that file's encode loss (39.7–40.2 dB, +2.0 levels, largest at the light's saturated core) | `p1_s1_clip.build_s1_clip`, `p1_local.build_s2` |
| 686–730 (D1), 819–861 (B3) | OpenCV decode | **Decode:** `hq_bgr`.<br>**D1:** window detection and flow still run on round 2's decode, so **the same windows light in the same order** (the legacy path reproduces v7 D1 bit-exactly); worst local difference 2.7 levels.<br>**B3:** 2.0 levels | `m26/build_d1_v2.py`, `m26/build_b3_hq.py` |
| all | crf 18, preset medium, default RGB→YUV (rounds down) | **Master:** lossless RGB.<br>**Preview:** encoded from the master; BT.601 limited range as in every earlier version (colours unchanged), with accurate rounding and Lanczos chroma filtering; libx264 crf 10, preset slow, aq-mode 3, yuv420p; AAC 192k | `master_v8.py` |

## Native-pixel comparisons (`tests/clarity_v8/`)

**How to read the sheets:**
- **Files:** `*_native.png` are 1:1 pixels; `*_2x.png` are the same sheets enlarged 2× (nearest neighbour) for inspection.
- **Columns:**
  - **SOURCE:** native pixels of the file the frame is made from;
  - **v7 pre-encode**, **v7 final mp4**;
  - **v8 pre-encode** (= the master), **v8 final mp4**.
- **Decoding:** both mp4s go through the same accurate decoder.

| sheet | frames | boxes |
|---|---|---|
| `1_3s_KV1_landing` | 3.000 s (landing, motion blur) and 3.500 s (landed). SOURCE is KV1 at its own 3072-px scale (2.3×) | A: horns and hair silhouette; B: star clip, ribbon and hair; railing, hands and cloth |
| `2_3.625-7.458s_Seedance_rear` | 3.625 s (the cut-in), 5.000 s, 7.083 s | A: horns and hair; B: star clip and hair; railing; A's hand on the ledge |
| `3_9s_S1_profile` | 9.000 s, plus **the take's frame 0 next to the approved still it was generated from** | eye and lashes; horn and hair silhouette; profile; collar, ribbon and suspender |

**What the sheets show:**

| span | before (v7) | after (v8) | measured |
|---|---|---|---|
| 3.5 s | dotted strands, stair-stepped horns | continuous strands, clean horns | acutance unchanged; the lower fine-band number is the aliasing removed |
| 3.000 s | both are dominated by the deliberate landing smear | (same) | — |
| final mp4 at 3.0–3.5 s | — | — | colour-edge detail +22 to +46% over v7 |
| 3.625–7.458 s | — | **looks the same as v7**: the SOURCE column is already this soft | equal within ~1% |
| 9 s | — | slightly cleaner: one fewer lossy generation, 15–24% more colour-edge detail in the final | — |
| take's frame 0 vs the approved still (bottom rows) | — | — | what was lost at generation, before any of our processing |

## Higher-quality originals

I searched the repo, every uploaded ZIP and the scratchpad.

**Seedance takes:**
- The files we have are the only copies. The upload copies are byte-identical:
  - the S1 take = `horned_girl_night_5s_v2.mp4`, sha256/16 `76792d17a4d9102e`;
  - the rear, D1 and B3 sources = the repair package's `media/sources`.
- **All four have the same structure:** 252–278 kb/s, 32–70 KB first frame, about 1 KB per later frame. Nothing larger or higher-bitrate exists locally.

**Approved stills:** `KV1.png`, the three approved P1 stills (1672×941), the candidates and the plates are lossless originals. v8 uses them without the extra losses.

**What would actually fix the Seedance shots, without new generation:** a **higher-bitrate or original-quality download of the same four takes**, if the Seedance account offers one. I can't access that account.

## QC of the actual render

- **Container:** 1038 frames, 43.250 s, 0 irregular steps.
- **Audio:** correlation 0.9997 at 0 ms.
- **Master:** decodes to exactly the 1038 frames.
- **Changed frames:** pre-encode frames differ from v7 in exactly 62–255, 686–730 and 819–861 (282 frames).
- **Every other frame:** bit-identical to v7's, including:
  - C1 with the round-2 fragments;
  - the hill ending;
  - S3 with the v5 settle.

**Checked by eye in the decoded v8 (with the frames listed):**

| span | frames checked | finding |
|---|---|---|
| boundaries | 85–88, 178–181, 219/220, 255/256, 685/686, 730/731, 818/819, 861/862 | same content and cuts as v7 |
| horizon edges | 76–86 | **match v6's accepted horizon within 1 px**: the round-2 mirrored-kink fix holds |
| D1 | 686–730 | same windows, same cool → warm order |

## Not solved, or only partly

1. **Clarity is still limited at 3.625–9.17 s, and in D1 and B3, by the Seedance files.** v8 removes what our pipeline added; it does not make these shots sharp, and I am not claiming it does. The remaining options all need your approval:
   - **a.** A higher-quality download of the same takes (see above).
   - **b.** Regeneration at a higher resolution or bitrate (paid; not done).
   - **c.** For the rear shot only: use the KV1 drawing for the ~95% of the frame that does not move (Earth, sky, parapet, most of both bodies), and keep the Seedance pixels only where the take moves (B's head turn, A's horns/head, A's fingertips). This changes which drawing is shown for most of the shot and would leave the moving heads soft next to sharp still areas, so I have not done it.
2. **The 3.625 cut-in** still joins two drawings (KV1 → the softer Seedance redraw). The KV1 side now has cleaner lines; the change in detail at the cut remains.
3. **The same unfiltered downscale exists elsewhere in `demo43.py`,** outside this round's spans:
   - C1's small seated observers (0.16× scale, end of C1): strong;
   - A1 (≈0.85×), V1b (0.79×) and `to_screen` plates (0.83×): mild.

   Not changed in this round; the same fix applies.
4. **Colour tagging:** the mp4 is untagged BT.601 like every earlier version, so v7 and v8 compare 1:1. Players that assume BT.709 for untagged HD shift hues slightly in all versions. The tagging decision is open.
5. **Continuity limitations, unchanged by this round:**
   - **The hand lift is not shown:** the cut at 7.458 s is an elision from the fingertips leaving the stone to S1's raised palm, not a demonstrated catch.
   - **The light's position and size change at the 7.5 s cut.**
   - **D1:** B looks down from the first frame; no gaze response is claimed.
   - **The C1 fragments'** readability at speed still needs your viewing.
   - **Chroma:** the colour repair is verified only at the anomaly spans.
6. **Not verified by ear.** The next Earth sequence remains a plan only.
