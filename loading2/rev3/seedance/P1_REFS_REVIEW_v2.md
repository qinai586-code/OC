# P1 reference pack v2 review (MV_S1-S3.zip, 2026-10-02)

| shot | file | sha256 (16) | song time (locked edit) |
|---|---|---|---|
| S1 (owner-approved composition) | P1_S1_original_reference_v8.png | 0d4bb512df959b04 | 7.500–9.167 |
| S2 | P1_S2_HAND_START_v2.png | 35b412f1e543144d | 9.167–10.667 |
| S3 | P1_S3_HOVER_START_v2.png | c95999951285194c | 10.667–13.600 |

All are 1672×941. Each is reviewed as a **separate first frame of a separate clip**, never as a
morph endpoint. The identity authority is the original Girl A model sheet (`images/1.webp`).
Board: `review/P1_v2_review_board.jpg`.

## Measured (pixel positions in the 1672×941 frames)

| item | S1 | S2 | S3 |
|---|---|---|---|
| warm lights in the sky | 1: the orb at (1205, 121) | **0** (the orb starts off-screen above right, as specified) | 0 in the sky. The only orb is above the palm at (1029, 597) |
| duplicate orb (the v1 defect) | — | none | **none**: fixed |

## Visual judgments (mine; please confirm)

| check | result |
|---|---|
| light direction | top-right in S1 → enters top-right in S2 → above the palm in S3. One continuous path down-left; it does not reset after S1 |
| screen direction | she faces right, and the hand points right, in all three |
| identity vs the model sheet | matches the model sheet:<br>• horns: dark scaled base, teal tips; both visible in S1 and S3;<br>• hair: black with teal streaks, half-up with the dark ribbon at the back;<br>• teal eyes;<br>• off-shoulder black coat with teal lining and diamond embroidery, white shirt, straps, dark bow, skirt with belt and charm |
| S1 → S3 hairstyle | consistent now (both half-up with the ribbon). The v1 braid/bun mismatch is gone |
| hands | right hand, palm up, five digits and plausible joints in all three; S3 more cupped |
| lighting | S1 and S2 cool, with no warm light on the hand; S3 warm on the palm, a little on the face. Matches the story |
| scale progression | S1 waist-up → S2 hand insert → S3 chest-up. Each cut changes the shot size |

## Issues to settle before generating

1. **Clip side (identity; owner decision, not blocking the S1 motion test).** The model sheet puts
   the crossed X clip on her **left**: the front view and its left-facing profile detail agree.
   - S1 and S3 are right profiles, yet the clip is on her visible **right** side, so it is mirrored
     against the identity authority. S1 and S3 do agree with each other.
   - **Options:**
     - (a) accept it as a documented deviation for this sequence;
     - (b) regenerate S1 and S3 with the clip out of sight (on her far side);
     - (c) I paint it out locally, which risks smudging the hair.
   - I did **not** alter the approved S1. This needs deciding before Wave 2, because every clip will
     carry it.
2. **Hand height across the cuts (S2 continuity).** The palm is around lower-chest height in S1
   and S2 and at shoulder height in S3. The S2 action should include **a gentle lift of the hand to
   meet the light**, or the S2→S3 cut reads as a jump. This is added to the S2 note below. It does
   not affect the S1 pilot.
3. **Minor details:**
   - S2's cuff is ruffled or folded, while S1 and S3 have plain cuffs.
   - S2's coat reads browner under its light; I can match that with a grade in the edit.
4. **Size:** the frames are 1672×941. Use them as they are; no upscaling. Confirm the accepted input
   size on the real interface.
5. **Static only.** None of this establishes motion, anatomy under movement or cut continuity in
   playback. Those are judged on the returned video.

**S2 note for later** (not requested now): her open hand lifts gently, about one palm-height, as the
orb enters from the top right and slows above the palm. It ends near S3's starting hand position.

## Decision: the one motion pilot is S1 (approved frame)

See `pilot_S1/PILOT_S1_SHEET_v2.md`. It replaces the v1 sheet, which used the earlier S1 candidate.
Nothing has been submitted, uploaded or spent.
