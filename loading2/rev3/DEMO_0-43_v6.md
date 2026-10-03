# Demo 0–43.25 s, v6: the owner's repair brief (`REPAIR_BRIEF_EN.md`)

| file | what it is |
|---|---|
| `tests/DEMO_0-43_v6_720p.mp4` | 1280×720, 24 fps, 1038 frames, 43.250 s, on the unchanged locked master. sha256 `94cede0b6b09c67d504215da37fd8fa6a437925c0e3ad22012e2f6d2bdc647d7` |
| `tests/v6_evidence/*.jpg` | BEFORE (v5) / AFTER (v6) pairs from the decoded frames, one sheet per brief item |
| `tests/DEMO_0-43_v6_strip.jpg`, `_shots.json` | one frame per shot, and the shot list |

**Package intake:** the ZIP's 11 files all match `MANIFEST.json` (bytes and SHA-256). The v5 hash quoted in the brief matches the delivered v5.

**Scope:** only affected frames were re-rendered (396 of 1038): opening frames 156–179, V1b, C1, D1, D3b, D4, D5, D6 and E1. Everything else comes from v5's frames. v5, v4 and v3 stay in `tests/`. **Generation:** none.

## Brief item → source asset → shot → change → evidence

| # | source asset (unchanged) | shot, song (s) | change | evidence |
|---|---|---|---|---|
| 1 | `B3.png` (pose sheet) | D3b 34.13–35.92 | **Cause of the face damage:** v5's matte let the background grow into pale pockets and enclosed white regions bordered by hair. B3's forehead highlight between the bangs and the white corners of her closed eyes qualify, so they became transparent and showed the navy behind her.<br>**Fix:** her face and cardigan interiors (the convex hull of the face skin, extended under the bangs, and of the cardigan, extended over the collar) are protected. White pockets bordered by skin or collar white are kept.<br>**Kept as gaps:** the real gaps between her outer strands stay open. Checked on light, dark and neutral backgrounds and in the scene.<br>**Other poses:** A1 and A3 were checked separately. Their face zones have no interior holes (the few flagged pixels are the hair-and-sky edge outside the face line), so the fix is not applied to them | `1_B3_face.jpg` (top) |
| 2 | `KV5a.png` background, `B3.png` | D3b | **Setting:** B on the parapet: KV5a's own stone runs past her lower left, with the night Earth beyond, both out of focus.<br>**Light:** it comes from A's palm, off frame below-left: warm on the near cheek, jaw and front hair, cool and darker on the back of her head, with a warm rim on her near edge.<br>**Motion:** one slow breath; the hair hanging in front follows about 0.2 s later. No turn, no lip motion | `1_B3_face.jpg` (bottom) |
| 2 | `KV4.png` | D1 28.58–30.46 | **Head:** her eyes lead (29.25–29.55), then her chin lowers 1.2° about the neck (29.35–29.85), following the street as it unfolds. This is a local warp of the head only.<br>**Light:** when the windows come on (30.0–30.4), their warm light reaches her near side. The thin lower hair is unchanged from v4's repaired matte | `2_D1_ground.jpg` |
| 2 | rear A/B candidates | C1 end | **Contact shadows:** under both figures where they touch the parapet. The figures are not brightened | `3b_C1_observers.jpg` |
| 3 | the letter page, M3, cradle and war art (as in v5) | C1 25.00–28.58 | **Near:** four torn shards of the letter's own paper pass the lens as the camera pulls back past them. They are dark, out of focus, rimmed by the light, and they cover what is behind them.<br>**Middle:** the hands (brightest first, then dimming), the war room, the cradle and the letter's mark at unequal brightness. Each sheds a few words of the handwriting, which drift from it.<br>**Far:** v5's evenly scattered words are gone. The letter's handwriting now lies along the three arms of one vast spiral (the letter's mark, enlarged), on a disk about 150 units deep. It opens from its centre outward and turns slowly.<br>**Observers:** A and B end small under all of it | `3_C1_depth.jpg` |
| 3 | procedural paper town | D1, D4 | **Base tabs:** each town and street card now has a glued tab on the page in front of its fold.<br>**Side walls:** each has a side wall at the end facing the camera, which folds with the card (its depth follows the fold angle).<br>**Kept:** the braces and fold-root shadows from v5.<br>**History reversal:** unchanged. The town folds back onto the same terrain, the hill of the first fire | (in `2_D1_ground.jpg`; full frames in the video) |
| 4 | `KV1.png` (A's hand layer) | opening 6.60–7.46 | **Release:** v5's hand moved about 15 px and dissolved. Now the fingertips come up off the stone first (turning about the wrist), then the hand and cuff rise together.<br>**Cut:** the cut to S1's raised palm comes on that motion. Nothing fades. This is an action-elision cut, not a continuous articulated lift: the hand stays one drawing | `4_hand_release.jpg` |
| 4 | side-palm candidate, letter page | V1b 14.96–15.88 | **Float:** the sheet beside her is turned about 16° and gently flexed, so it reads as paper, not a flat panel.<br>**Arrival:** its last approach is computed from P1a's own camera. Frame 380 now has P1a's page pose (same tilt, text scale and depth of field) and the reader light at P1a's position, so 380→381 continues.<br>**Kept:** the clear face and the single fingertip contour, through 15.71 | `5_paper_380_381.jpg` |
| 5 | `fire_bg/fire_hand`, `first_fire_hill_wide_v1`, `KV5a` | D5 / D6 / E1 | **Night fill:** D5's warm night fill is now the hill wide's night blue. D5's fire light is trimmed and D6's local fire light raised, so exposure carries across the cut.<br>**Retime (picture only, music unchanged):** D5 ends when its flame is established (40.958). D6 is 40.958–42.25, and E1 is now **1.0 s** (42.25–43.25) instead of 0.5 s.<br>**The return:** in D6's last 5 frames the fire's halo gathers to the palm light's size at the same screen point. E1 opens with that warmth, which settles into A's palm light over 0.4 s, with a slight push-in.<br>No second catch, fall or reach | `6_fire_return.jpg` |

## QC of the actual render

**Measured** (decoded from the mp4):

| check | result |
|---|---|
| container | 1280×720 H.264, 24 fps, 1038 frames, 43.250 s; AAC 43.250 s from the locked master; 0 irregular frame steps |
| approved S1–S2 (frames 180–255) | mean difference 1.89, max 1.94 against `P1_light_catch_720p.mp4` (encoding only); S3 differs only by v5's settle (max 0.61) |
| frame-to-frame change | **Median:** 0.76.<br>**Changes above 16 outside a cut:**<br>- the unchanged opening (frames 8–13);<br>- the P1b fold (486–488);<br>- the approved S2 hand and the S2 → S3 cut (220, 256);<br>- V1b's last approach into P1a (378–379, intended: the sheet comes to the lens) |
| one light across the cuts | **P1b → M1:** (261, 264) → (260, 262).<br>**M1 → M2:** (168, 247) → (169, 242).<br>**D5 → D6:** (567, 438) → (567, 437).<br>**D6 → E1:** (567, 431) → (567, 436).<br>E1 holds (567, 436) to its last frame |
| halo across D6 → E1 | brightness at radius 0/8/16/32 px: D6's last frame 253/213/144/101, E1's first 254/215/170/109 (v5: 252/167/74/78 against 255/203/155/96) |
| single catch | the light is caught once (S3, 13.04). E1 has no fall, reach or catch; the only motion is the push-in and the glow settling |

**Seen in the rendered frames:**
- **B3:** the forehead and eye-corner areas are intact in frames 819–861.
- **The two seams:** the hand leaves the ledge before the cut, and frame 380 matches 381.
- **C1:** reads as near shards, middle memories and a far spiral, then the observers.
- **D5–D6:** the night colour carries across the cut.

**Not verified by ear:** I cannot listen. The retime only changes picture boundaries (D5/D6 and D6/E1); the music is unchanged.

## Remaining limitations

- **The opening hand is still one drawing.** It releases and starts to lift, then the cut carries the action. It is an elision, not a full articulated lift.
- **C1's near shards** are dark against a dark sky, so they mainly read where they cross the lit lines. The spiral is procedural (the letter's own handwriting and mark); whether the reveal lands as awe needs your viewing.
- **The paper town's side walls are narrow** from this near-frontal camera. They read best on the street cards at left.
- **B3's grounding** comes from light, place and breath. There is still no drawn body motion.
- **D1's head response** is a small local warp; please judge it at speed.
- **E1 is 1.0 s, the minimum the brief asked for.** It is taken from D6 and D5's post-ignition frames, and the "hill" cut is now at 42.25 instead of 42.75. A longer return would need the next section; I have not extended the deliverable.

**Next lyric section:** not planned or rendered, per the brief. I'll write that plan after QX accepts this candidate.
