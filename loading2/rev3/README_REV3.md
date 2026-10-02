# Simulated Universe: rev3 repair package (for independent review)

This is a new revision folder. Nothing in `loading2/` outside `rev3/` was changed, apart from one
`.gitignore` line for `rev3/work/`. The locked track was not edited.
- No full MV render.
- No paid generation, uploads or purchases.
- Everything ran locally (CPU, Python/OpenCV, the local isnet-anime matting model, ffmpeg).

## Deliverables

| item | file |
|---|---|
| Body/environment test, 0:07.50–0:12.50 (5.0 s) | `tests/REV3_body_light_catch.mp4` |
| Repaired singing close-up, 0:52.42–0:56.29 (same excerpt as v2) | `tests/REV3_singing_closeup.mp4` |
| Before/after at matched track timestamps (body, singing, 1:06–1:14, 2:25–2:38) | `tests/REV3_before_after.mp4` (29.7 s) |
| Drawn storyboard: 32 timed panels across the four sequences plus the 1:06–1:14 repair | `storyboard/REV3_storyboard_page01-06.jpg`, `storyboard/panels/*.jpg` |
| Timed storyboard reel over the locked audio of each span (13.6–28.9, 66.5–74.6, 89.2–103.0, 142.8–213.41) | `storyboard/REV3_storyboard_reel.mp4` (107.9 s) |
| Sung-sound evidence for the mouth timing | `docs/phoneme_evidence.png`, `docs/phoneme_features.csv` |
| Per-frame logs | `tests/rev3_body_log.json`, `tests/rev3_sing_log.json` |

Rebuild everything (frames go to `rev3/work/`, which is git-ignored):

```
python3 rev3/tools/matte.py <src.png> rev3/assets/<name>.png [--paper x0,y0,x1,y1,...]
python3 rev3/tools/phonemes.py
python3 rev3/tools/sing.py
python3 rev3/tools/body.py
python3 rev3/tools/storyboard.py --reel
python3 rev3/tools/compare.py
```

## What changed, and how

### Body/environment test (0:07.50–0:12.50)

**The action.** A watches a warm light descend, nods down to follow it, raises her forearm, and the
light settles into her open palm.

**What carries it:**
- **Two genuinely different drawn poses:** A1 (chin up, lips parted) and A3 (level gaze, palm raised).
  Each frame uses exactly one of them, so there is no crossfade. A1 is used for frames 180–212 and A3
  from frame 213.
- **One anticipation and one breakdown (smear) frame.** In this profile view a head pitch is an
  in-plane rotation, so rotation is used only for these frames and the overshoot.
- **A forearm rotation about the elbow,** below the frame, with ease-out, overshoot and settle.
- **A contact dip** when the light lands, and the palm recovers.
- **Secondary hair swing and settle.**
- **Light:** warm light on her palm and face, a cool night ambient, and a sky rim.

**Fixes from v2:**
- **Mattes** re-cut from the white-background sources. The drawings' pale halo outside the line art
  is pulled in to the drawn line and re-inked as one continuous line. This removed both the white
  fringe and a dotted outline found during review.
- **Framing:** both drawings' straight crop edges sit outside the frame.
- **Torso fill:** where the sleeve uncovers the torso, the fill comes from A1's real drawn coat and bow.
- **Plate:** the background crop of KV1 is clear of B's painted hair.

### Singing close-up (0:52.42–0:56.29)

**Mouth timing.** Mouths are chosen from the sung sounds of the author text, "What if we live in a
simulated universe:". They are timed to landmarks measured in the vocal stem (`docs/phoneme_evidence.png`):
- sibilants at 53.88–54.02, 55.72–55.92 and 56.06–56.22;
- frication at 52.80 and 53.35–53.45;
- the "m" closure at about 54.10.

Teeth appear only on f, v and s, using a narrowed, de-curled teeth drawing. The smile drawing is never
used. Drawings change one frame before the sound, on twos.

**Your note on the crooked mouth.** The face's centre line, measured from the chin tip and the jaw
midpoints, is x=521. The v2 anchor (x=538) copied the drawing's own slanted mouth stroke and sat
17 px off-centre. My first rev3 jaw warp was also centred at 512, which skewed open mouths. Now:
- every mouth sits on the face axis;
- the jaw drop is symmetric about it;
- mouths are rescaled to the face: open "A" about one fifth of the face width, the closed line about
  one eighth.

**Composition.** An over-the-shoulder close-up: A sings the question to B, whose out-of-focus copper
hair and star clip fill the right of frame. This hides the source head's straight crop edges without
inventing hair. The head lifts into the stressed "SIM" and settles on "verse". There is no forced blink.

### Storyboard

These are drawn rough layouts, staging and timing only, not animation. The four requested sequences
plus the repetition repair, with timing and author lyric under each panel:

| sequence | panels | span |
|---|---|---|
| 1 Human traces | 7 | 13.6–28.9 |
| R (repetition repair) | 4 | 66.5–74.6 |
| 2 Flattening | 5 | 89.2–103.0 |
| 3 Footsteps and keys | 6 | 142.8–163.5 |
| 4 Civilisation and return | 10 | 163.5–213.41 |

Each sequence has a beginning, a meaningful change and a resulting state:
- **1 Human traces:** the light becomes a worn letter. Its line lifts into glyphs. A match cut leads to
  the war letter, the cradle and the parting hands, and these become a constellation the girls look
  up at.
- **2 Flattening:** perspective, overlap and contact come first. Then a front crosses the city far to
  near. The girls stand on the surviving rim, and their shadows are printed on the flat world.
- **3 Footsteps and keys:** a key goes down by itself. A tiny traveller's footfall presses it. A
  kneels and B holds back. A traveller lights A's lantern, and the procession leads out through the
  window. The chair stays empty.
- **4 Civilisation and return:**
  - The earlier traces turn into roads, rivers and bridges, and accumulate into a civilisation drawn
    on the Earth.
  - The girls step into the drawing, into their own printed shadows.
  - Depth returns on "maybe".
  - They are back on an altered parapet, and the note gives the "two / three / one" beats.
- **01:06–01:14 and 02:25–02:38:** each now has four events instead of one held image.

## Story and continuity corrections

**The girls' state is a staging choice.** A surviving observer does not have to stay
three-dimensional. Keeping the girls volumetric on the rim when the world flattens is my choice, and
it holds for the whole film:

| span | world | girls |
|---|---|---|
| until 1:36 | volumetric (W3) | volumetric (V) |
| 1:36 | flattens (W2) | stay V on the rim; only their shadows become part of the drawing |
| 2:50.3 | — | step into the art and become contours (their only change) |
| 3:00–3:08.5 | depth returns | return to V on the parapet |

**"And one" is not a dimension.** A point is zero-dimensional. The outro's "and one" is staged as
togetherness, A's hand closing over B's around one light. It is not presented as a literal
dimensional demonstration.

**Vocal allocation.** A/B is creative direction taken from the author's tags. The recording itself
has not been verified as one or two voices. Chorus 1 has no tag, so A singing it is staging.

**Unresolved lines, kept.** The four main Final Chorus lines (F01–F04) stay marked as unresolved at
2:43.5–2:50.3, with the measured content shown. The panels at that point illustrate those lines'
meaning, so the staging works with or without the words. "Unanswered" vs "unfinished" at 1:10.3 stays
unresolved. The alternate ending from the lyric draft is not duplicated.

## Checks: what is measured, what is judged, what was not done

**Measured** (logs and `docs/`):

Singing:
- 93 frames; face holes (alpha < 0.5 inside the face mask) = 0 in every frame.
- Mouthless base: 1,349 of 1,725 px changed inside its region, 0 outside.
- Viseme use: E 26, small 20, F 18, U 16, A 10, closed 3. No smile drawing.
- Light-and-neutral semi-transparent edge pixels: 586 per frame on average. On frame 1300 they sit on
  the hair clip's light edges, the collar edge and a few paper specks within 20 px of the left frame
  edge.

Body:
- 120 frames: A1 for frames 180–212, A3 for 213–299. Motion-blur subsamples never mix the two drawings.

Reels and comparison: frame counts and durations were checked with ffprobe.

**Visual judgments** (my own, from key frames and contact strips; not independent):
- The body action reads as gaze, nod, raise, catch and hold.
- The hand and face outlines are now continuous lines.
- In the singing close-up, the mouths sit on the chin axis and no longer read as grins.
- B's foreground reads as B.

**Not verified:**
- I cannot listen. The phoneme timing comes from spectral landmarks, not hearing, and formant estimates
  were unreliable at this pitch, so they were not used.
- Lip-sync, naturalness, musical impact and normal-speed smoothness, including the A1→A3 snap, need a
  person to watch them.

## Remaining limitations and exact asset briefs

**Body test:**
- A1 and A3 are QC "acting references" generated separately. Small design differences (ribbon, braid)
  change at the switch.
- The fingers cannot curl around the light, and the nod has no drawn in-between.
- **Brief 1:** A, right-facing profile, same framing and scale as A3, palm cupped with fingers curled
  about 30° around a small light. White background.
- **Brief 2:** A, the same profile between A1 and A3: head pitched about 15° below A1, eyes travelling
  down, lips closing.

**Singing:**
- The front head is a 4× upscale of a 241 px drawing, so it is soft at close-up size.
- The side hair still carries paper specks; the frame hides most of them.
- There are no blink or brow drawings for this head.
- **Brief 3:** the same front head at higher resolution with complete side hair (no crop), plus a
  closed-eye and a half-lid version pixel-aligned to it.

**Storyboard to production.** These layouts need, at minimum:
- the parapet plate in the 2.1 perspective (also used by 4.6);
- three flattening states (before / during / after) of that view;
- the backstage room with separate desk, chair, window and wall layers, and a console with keys;
- the window "civilisation" drawing in its three stages (4.1, 4.2, 4.4);
- pose keys for the following:
  - seated → standing on the rim (2.4);
  - standing on the rim, from behind (2.5);
  - kneeling at the console (3.3);
  - walking with lanterns, from behind (3.5);
  - stepping through the window, volumetric and contour versions (4.3);
  - the hands for 1.1, 1.3, 4.7a–c.

  Each pose needs a start and an end key.

**Not attempted in this package:** the rest of the film, any other shot, and any audio edit.

## Production route update: Seedance 2.5 (owner-generated)

Shots that need genuine character motion move to Seedance 2.5 clips, which the owner generates.
The pilot is the light catch at 0:07.5–0:12.5. The request list, reference-image briefs and prompts
are in `seedance/SEEDANCE_PLAN_AND_PILOT.md`, with composition boards in `seedance/composition/`.

`tests/REV3b_light_catch.mp4` (`tools/body2.py`) is the local three-shot re-cut of the light catch.
It removes the in-shot pose switch and is the pilot's layout and timing reference.
