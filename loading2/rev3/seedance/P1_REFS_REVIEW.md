# P1 reference pack review (MV_P1_refs.zip, 2026-10-02)

| file | sha256 (16) | size |
|---|---|---|
| P1_S1_LOOK_UP_CANDIDATE.png | 093a344bad794ce9 | 1672×941 |
| P1_S2_HAND_CANDIDATE.png | 52f2afac24dc4119 | 1672×941 |
| P1_S3_HOVER_CANDIDATE.png | ce622fce38da0d89 | 1672×941 |

All three are reviewed as **separate first-frame candidates** for three separate clips, not as
endpoints of one morph. Board: `review/P1_refs_review_board.jpg`.

## Checks

**Measured** (pixel positions in the 1672×941 frames):

| item | S1 | S2 | S3 |
|---|---|---|---|
| orb | (1256, 120), core r≈15 px; the only warm light | none, but a warm point at (1249, 157), r≈9 | orb above the palm at about (1006, 605); **plus a warm point at (1249, 158), r≈7: the same spot and same sky as S2** |
| light path | starts top-right | — | a dotted trail runs from the top right down to the orb: top-right → down-left, consistent |

**Visual judgments** (mine; a human should confirm):

| item | S1 → S2 → S3 | verdict |
|---|---|---|
| screen direction | faces right / hand points right / faces right | consistent |
| horns | the same dark-based, teal translucent, scale-textured design, at similar size relative to the head | consistent |
| crossed clip | same placement relative to the eye on the visible side | consistent; the front-view side question is still open, as the README says |
| eyes, face | teal eyes; lips parted in S1, nearly closed in S3 | consistent |
| outfit | dark coat, white shirt, dark suspender straps, teal bow; the same white cuff under the dark sleeve in S2 and S3 | consistent |
| hairstyle (back of head) | S1: a braid running back to a ribbon. S3: a **coiled braid bun** with the ribbon below it | **minor mismatch**; visible because the back of the head is in frame in both |
| hands | S2 and S3: right hand, palm up, thumb plus four fingers, clean joints; S3 slightly more cupped | consistent and anatomically sound |
| lighting | S1: no warm light on her (the orb is far). S2: cool, neutral hand. S3: warm light on the palm, chin and cheek | consistent with the story |
| background | S2 and S3 share the same sky and cloud layout; S1's clouds differ. The Earth limb has a similar slope in all three | acceptable across cuts (the sky is effectively at infinity) |

## Issues flagged before generation

1. **S3: duplicate orb (blocks S3).** The warm point at (1249, 158) will read as a second orb, or be
   animated as one, while the real orb is at her palm.
   - Optional local fix: `refs_fixed/P1_S3_HOVER_CANDIDATE_noUR.png`. Only a 20 px radius was
     inpainted (1,249 px changed, 0 outside the mask). It leaves a faint soft patch at that spot.
   - The owner may instead regenerate S3 without the point.
2. **S2: the same warm point.** Choose one before generating S2:
   - **(a) keep it as the distant orb.** It sits at S1's orb position, a good match. The prompt then
     says "the small warm light at upper right drifts down-left to the palm". **Recommended:** the
     generator moves an existing object more reliably than it invents a new one.
   - **(b) remove it** and let the orb enter from off-frame.
3. **S2 start pose.** The hand is already raised to mid-height; the plan had it rising from low.
   - The raise is elided across the S1→S2 cut, and the insert's own motion is small ("rises slightly
     and cups").
   - Acceptable and lower-risk. If the cut reads as a jump, an S2 start frame with the hand lower
     is the remedy.
4. **Hairstyle mismatch (minor).** S1 has a braid; S3 has a coiled bun. Not blocking for the S1
   pilot. Settle it before S3 and the identity sheet: regenerate one of them, or accept it.
5. **S3 hold to 13.600: covered by the edit.** The span 12.500–13.600 (with "Loading." at 12.6)
   ends at the next shot, so S3's usable range is **10.667–13.600 (2.93 s)**. The before/after
   comparison still stops at 12.500.
6. **Size.** The frames are 1672×941, close to 16:9. Use them as they are; no upscaling. The output
   is conformed to 1920×1080 in the edit, and the upscale is noted.
7. **No identity sheet in the pack.** That is fine for a single-shot pilot, where the first frame
   carries identity. It is needed before S3 is cut against S1, and before Wave 2.
8. **REV3b_light_catch.mp4.** Agreed: its smoothness has not been independently checked, and it is
   not labelled as passed.

## Decision: first pilot shot = P1-S1

- Its start frame is clean: one orb, no edits needed.
- It tests the exact failure from rev3, a real head movement (eyes leading, head following),
  together with identity stability and hair follow-through.
- S3 (contact) follows once S1's result sets the identity baseline and the S3 frame is fixed.

The sheet is `pilot_S1/PILOT_S1_SHEET.md`. Nothing has been submitted or spent.
