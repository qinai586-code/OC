# Demo 0–43.25 s, v7: QX round-2 repairs

**Candidate:** `tests/DEMO_0-43_v7_720p.mp4`
- 1280×720 H.264, 24 fps, **1038 frames, 43.250 s**, no irregular frame steps;
- AAC from the locked master: waveform correlation 0.9994 at 0 ms offset over 0–43.25;
- sha256 `d46ddedac69124bcb5a091d2a9fa2f1f49eef1aa1445a85ad7bef77514ce539a`.

**Kept for comparison:** v6, v5 and earlier stay in `tests/`.

**Not changed:** no new generation, accounts or assets, and no shots outside the list below.

## Exact change log against v6 (decoded frame comparison: 279 frames differ, in four runs)

| global frames | song (s) | change | source |
|---|---|---|---|
| 87–179 | 3.625–7.458 | **Opening rear shot.** Frames ≤86 are v6, untouched, which removes the mirrored horizon kink at 78–80 (cause: the previous round shrank v6 frames toward the source framing and a reflected border filled the gap).<br>**Cut-in at 87:** the chroma-repaired Seedance rear shot, source f0–92 at original speed, registered once to v6 f86 (affine; 0.55% extra zoom so no border is ever exposed; 0 gap pixels in every frame). Then only v6's own push-in (5.45–7.5).<br>**Light:** drawn with v6's exact formula.<br>**Cut-out:** the shot ends on source f92, as A's fingertips leave the ledge | `Opening_rear_5s_seedance25.mp4` (V plane repaired) |
| 617–685 | 25.71–28.58 | **C1 near fragments.** The four large dark defocused blocks (they never left the frame) are replaced by **three** torn pieces of the letter itself. They are backlit cream paper with the handwriting in ink, a pale torn-fibre rim, a thin darker lower edge for thickness, and light defocus. They fly out of the constellation and past the lens to the side, each visible about 0.7–1.0 s, and **all gone by 27.38 s (frame 657)**. The reveal of A and B stays clean. Frames 600–616 are byte-identical to v6 | procedural (the letter page) |
| 686–730 | 28.583–30.417 | **D1.** Seedance D1, chroma-repaired, **source f20–64** at original speed:<br>- **City:** the paper unfolds from the first frames (cards rising 28.75–29.75), then the windows light left to right (29.5–29.9, persisting along optical flow).<br>- **B's light:** she starts in **cool, dim night light**. The warmth on her face, hair and near side rises only as the lit-window area grows (3-frame lag; a per-channel multiply, no blur).<br>- **No added motion.** | `D1_papercity_5s_seedance25.mp4` |
| 819–861 | 34.125–35.875 | **B3** (as accepted for review last round): Seedance B3, chroma-repaired, source f42–84: open eyes, one slow closure, a closed-eye hold | `B3_eyeclosure_5s_seedance25.mp4` |
| 1009–1037 | 42.04–43.21 | **Ending** (kept as accepted): the hill fire runs to the end and settles. No halo lead-in and no palm-orb shot. The D5→D6 cut is unchanged at frame 983 | `first_fire_hill_wide_v1.png` |

**Review spans** (`tests/m27_review/`, original speed, master audio, with the surrounding cuts):

| file | span (s) | BEFORE | AFTER |
|---|---|---|---|
| `1_Opening_*` | 2.50–9.00 | the previous round's AFTER | v7 |
| `2_C1-D1_*` | 25.00–31.67 | v6's C1, plus the previous round's D1 | v7 |

**Still frames** (`3_`–`6_*.jpg`):
- `3`: the horizon edge at 78–87;
- `4`: the hand at 176–180;
- `5`: the C1 fragments at 636/660/672/685;
- `6`: the D1 order at 686–730.

## Checked by eye in the decoded v7

- **Opening:** the left and right horizon edges at 78, 80, 84, 86, 87, 120, 160 and 179 are smooth, with no mirrored border. The light keeps its path across 86→87. Frame 179→180 cuts as the fingertips leave the stone, to the raised palm.
- **C1:** 599→600, then the fragments at 624, 636 and 648; the frame is clean at 656, 657, 660, 672 and 685.
- **D1:** 685→686→731 and 700/712/722/730: cool face before the windows, warm after.
- **B3:** 818→819 and 861→862.
- **Ending:** 982→983 and 1008/1020/1037 (fire flicker, no freeze).

## Not solved, or only partly

1. **The hand lift is not shown.** No clean source frame has A's palm up at chest height. The Seedance take raises the hand outward and up with the fingers down, then overhead. The edit therefore cuts **on the start of the action** (fingertips leaving the stone, 7.458) to S1, which opens with the palm already up. This is an elision, as the v6 brief allowed. It is not a demonstrated continuous lift or catch. A continuous lift needs new motion (prompt P1 in `M26_REPAIR_REVIEW.md`, unrun and unpaid).
2. **The light's position and size change at 7.5.** The light moves down-left toward A on both sides of the cut: (665,110)→(617,141) in the wide, (908,90)→(767,299) in S1. Its larger halo in S1 is consistent with the closer framing (A's head is about 3× larger). I kept the owner-approved S1 and the opening's light path. A screen-position match cut on the light would need one of these to change, so I have not done it without approval.
3. **D1 gaze:** B is looking down from the first frame. That is the source's starting pose, and I do not claim a gaze response. The source's only eye shift (source f10–30) happens before this section's main event, so it is not presented as a reaction. The event→reaction order is carried by the windows and her light.
4. **The 3.625 cut-in** joins two drawings of the same composition: v6's KV1 render and the softer Seedance redraw (252 kb/s). The framing matches. Detail and texture visibly change at the cut.
5. **The C1 fragments** are small and procedural. Whether they read as paper at full speed needs your viewing.
6. **Chroma:** the V-plane repair is verified at the anomaly spans of all three sources. B3 was accepted only for the inspected frames; there is no blanket chroma acceptance. A cleaner platform original is still unverified.
7. **Not verified by ear.** Word timing is from machine transcription. The next Earth sequence is still a plan only.
