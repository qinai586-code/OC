# Demo 0–43.25 s, v4: supplied memory art integrated; review items 1–7

| file | what it is |
|---|---|
| `tests/DEMO_0-43_v4_720p.mp4` | 1280×720, 24 fps, 1038 frames, on the unchanged locked master |
| `tests/DEMO_0-43_v4_strip.jpg`, `tests/DEMO_0-43_v4_shots.json` | one frame per shot; the shot list |
| `tests/DEMO_0-43_v3_720p.mp4` | **the previous version, kept for comparison** (its code is commit e496f3f) |
| `tools/demo43.py` | the build. `--shots ID,…` re-renders only those shots into a frame cache (4 workers); `--assemble` encodes one continuous file |
| `art/memory_cards/*.png` | the nine supplied candidates, byte-identical to the MV_Cards zips |
| `art/memory_cards_hold/newborn_hand_open.png` | kept out of the loader: disabled, as asked |

## Asset intake (checked, not assumed)

- **Files:**
  - Both zips pass their CRC test, and all ten PNGs match `MANIFEST.json` by SHA-256.
  - All decode at 1536×1024.
  - The `.tar.xz` you uploaded earlier wraps the same PNGs in a custom `.bxp` format. The pixels decode correctly (the stored Adler-32 matches), but I used the zip originals.
- **Alpha, measured:**
  - The opaque plates are RGB.
  - The four RGBA layers peak at 254, and 2.4–4.9% of their pixels are partial.
  - They composite cleanly over a checkerboard, with no dark halo.
  - The alpha is not binary, and I make no claim that it is pixel-perfect.
- **Anchors, measured on the art (canvas px), not taken from the placeholder brief:**

| shot | anchor | value |
|---|---|---|
| lullaby | rocker's lowest floor contact | (752, 845) |
| lullaby | rocker curvature radius | ≈1290 |
| lullaby | parent's fingers on the rim | x 1080–1185 |
| lullaby | sleeve exits the canvas | x 1535 |
| lullaby | lamp light | (202, 410) |
| farewell | passenger's index fingertip | (842, 585) |
| farewell | platform hand's index fingertip | (913, 577); gap 71 px |
| bowl | opening centre | (770, 540), half-width ≈205 |
| fire | held stone's striking tip | (885, 540) |
| fire | lower stone's top face | (613, 667)–(747, 687) |
| fire | tinder centre | (787, 695) |

## Changes, by time (what to look at)

| song (s) | shot | change | review item |
|---|---|---|---|
| 14.96–15.88 | V1b | (from v3) the sheet arrives as the lit letter | 2 |
| 15.88–18.63 | P1a | Cracks are now thin dark creases, not glowing lines. The tear runs across the page from its left edge (17.55) and reaches the spiral shard last (17.98), so it is asymmetric. 50 shards: smaller where the tear starts, one large shard holding the whole spiral and the full stop (an assertion fails if a tear ever crosses it). Shards flex along their middle as paper and lift at varied heights. Soft shadows fall on the page while they are low. The light is smaller | 2 |
| 18.63–19.54 | A1 | Her mouth is closed (voice-over, below). The shards in front pass low, below her face. The only light is the small rising point she looks at | 2, 7 |
| 19.54–20.46 | P1b | "Translated": the rewriting edge is a pen-shadow line, not a glow, and the spiral is kept. "Compressed": the other shards gather onto the spiral shard, which folds to a point. Paper colour throughout, nothing heats to white. The full stop's light lands on the candle's wick | 2 |
| 20.46–22.25 | M1 | Paper-card framing, kept on purpose. The arriving point lights the wick (20.47–20.62), then the candle reveals the room. The camera drifts the candle to where M2's lamp will be | 2, 3 |
| 22.25–23.83 | M2 | **Full frame, supplied art.** One push at 22.32: the cradle rolls on its rocker radius about the measured contact, so the feet stay on the floor line. ±1.1°, settling (amplitude decays over ≈1.1 s). The hand rides the rim; the forearm bends toward the sleeve end, which stays at the frame edge (no rigid lever). A restrained contact shadow under the rockers, no wall shadow. The lamp brightens a little on the cut, matching M1's candle on screen | 3, 5 |
| 23.83–25.00 | M3 | **Full frame, close on the hands.** The carriage starts 60 px right, so the fingertips are ≈11 px apart and never cross. They part at 24.15–24.55, then the carriage pulls away left with slow acceleration. Only the carriage moves; no arm is stretched. A small spark stays at the measured gap and rises | 3, 5 |
| 25.00–28.58 | C1 | The spark rises from its M3 screen position to the first mark. The constellations take the new art's shapes (candle and helmet; lamp, cradle and rockers; two reaching hands with a gap). They are traced as uneven dashes with unequal stars | 6 |
| 28.58–30.46 | D1 | **B's transparency fixed:** KV4's matte was 0.6–0.8 inside her hair. Its interior is now solid; real gaps (under her chin) stay open. Ordering is explicit: page, then town, then B. Her soft shadow falls on what lies behind her. The town gains an oblique street of house cards, near roofs in front (out of focus), and fold-root shadows | 1, 4 |
| 30.46–32.29 | D2 | **Full frame, supplied art.** Seven thin steam wisps rise from the measured opening and drift. Warmth stays near the bowl, the window stays cold, and the push is small (2.6%). No glow | 3, 5, 6 |
| 32.29–34.13 | D3 | **Full frame, supplied art.** The back plate and the whole connected baby layer share one breath transform (the parent's 3.1 s breath, plus the baby's smaller 1.15 s breath on the baby layer). No detached head, no held alternate, no chest light | 5, 6 |
| 34.13–35.92 | D3b | B3, voice-over. The glow blob and the "heartbeat" pulse are removed | 6, 7 |
| 35.92–39.25 | D4 | History read backward. Windows go dark one by one (36.2–36.9), the paper yellows, and the town and street fold back away from us like a closing spread (36.85), then the village (37.54). It is not crushed toward the viewer, so it stays distinct from a later destructive flattening. Focus racks to the hill | 4 |
| 39.25–41.17 | D5 | **Full frame, supplied art.** A down-left arc brings the stone tip to the lower stone's top at 39.59, a small recoil, then a second strike at 40.05. Sparks start at the contact and fall into the tinder, an ember follows, the flame catches on the 40.50 hit, and light rises on the hand. The hand is desaturated to match the cards. The forearm is mirror-extended past the canvas edge, so it is never cut | 4, 5 |
| 41.17–42.75 | D6 | The same fire on the crest. The camera is re-aimed every frame, so the fire holds the struck flame's screen point (566, 438 → 444) | 4 |
| 42.75 | E1 | Unchanged match to the palm flame (566, 445) | 4 |

**Removed:** the three decorative paper wipes (22.25, 23.83, 30.46) and the central glow blobs (D2, D3, D3b, A1). Each cut is now motivated by a match, for example the point of light that becomes the candle and then the lamp.

**Kept:** the meaningful returns to the Earth view (V1a, C1, E1).

## Singing or voice-over (item 7)

- **Decision:** there is no on-screen singing in 0–43.25. Every character shot is voice-over with an observing expression.
- **Why:** none of these shots is long enough on a single vocal line to carry a performance, and a frozen open mouth reads as an error.
- **The only open mouth was A1 (18.63–19.54), the model sheet's "ah" singing pose.** It is now closed (`close_mouth_a1`):
  - **Jaw:** it rotates up 5.5° about its hinge, near the ear, which is low in this raised-chin pose. It fades into the neck so the collar stays put.
  - **Opening:** what is left of it becomes skin.
  - **Profile:** rebuilt to A's own closed panel (`A_mouth.png`, panel 1) and the usual rules for an anime profile: the lips sit on a near-straight nose-to-chin line, the upper lip is a touch forward, a small notch marks the junction, the outline breaks there, and one short reddish-brown mouth line is drawn. There is no line across the cheek.
- **Other characters:** KV4, KV5a, KV5 and B3 already have closed mouths.
- **No lip sync is used or claimed in this demo.**

## QC

(see the measured table below, filled from the actual render)

## Mouth reference research (anime closed mouth in profile)

This container's network policy blocks the tutorial sites themselves (animeoutline.com, quotetheanime.com, gvaat.com, tips.clip-studio.com, clipstudio.net, oekaki-zukan.com, ichi-up.net, atwiki, togetter, Yahoo!知恵袋, ja.wikipedia.org and others). The rules below come from the search results' summaries of those pages, checked against A's own mouth sheet. I did not read the full articles.

**Closed mouth, profile:**
- It is mostly the silhouette.
- Draw the line from the nose tip to the chin and keep the lips on it (or just inside it).
- The upper lip sticks out slightly more than the lower. The upper lip is slightly angular, the lower a little rounder.
- The mouth is "suggestive": often one very slightly curved short line, with the outline broken (途切れ) at the lips rather than a sharp division.
- A common error is pushing the lips out too far.

**Anime convention:**
- In profile, the mouth is often placed slightly inside the face contour ("on the cheek"), a stylisation.
- In TV production this also lets lip flaps change without moving the jaw.
- Lip flaps are usually closed, half and open mouths (閉じ口・中口・大口). The half mouth is drawn nearly closed for crisper motion.
- (For a visible performance later in the MV, these are the shapes to draw. Your front-view chart covers the closed line, smile, small, half, open, teeth and "o" mouths.)

**Applied to A1:**
- The lips sit about 3 px inside the nose-to-chin line, the upper lip about 1 px further forward than the lower.
- A notch of about 1.5 px; the outline breaks at it.
- One reddish-brown mouth line of about 10 px, tapered.

**Sources** (search results; pages not opened):
- [AnimeOutline: mouths, side view](https://www.animeoutline.com/how-to-draw-anime-mouths-side-view/)
- [QTA: anime and manga mouths, side view](https://quotetheanime.com/drawing/how-to-draw-anime-and-manga-mouths-side-view/)
- [GVAAT: anime mouths and lips](https://gvaat.com/blog/how-to-draw-anime-lips-and-mouths-with-expressions-step-by-step/)
- [お絵かき図鑑: 口の描き方・横顔の口](https://oekaki-zukan.com/articles/41124)
- [ichi-up: かわいい横顔の描き方](https://ichi-up.net/2019/13)
- [CLIP STUDIO TIPS: 横顔の描き方](https://tips.clip-studio.com/ja-jp/articles/8004)
- [CLIP STUDIO: 横顔の描き方](https://www.clipstudio.net/oekaki/archives/151365)
- [ani-emo: アニメ横顔の口はなぜあの位置？](https://ani-emo.com/archives/1630)
- [アニメ制作メモ: 口パク](https://w.atwiki.jp/aniken/pages/462.html)
- [キャラクターを喋らせたい！口パクを描く時のポイント](https://saraemi.com/1608kutipaku/)
- [Rhubarb Lip Sync: mouth shapes](https://github.com/meshonline/rhubarb-lip-sync) (the one page that opened)
