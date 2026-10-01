# Reference analysis: the two Claude MVs

Both files are 960×540, 30 fps. They were measured with frame differencing, colour histograms,
sparse optical flow (camera zoom, pan and roll), beat tracking, and a vocal stem separated with
UVR-MDX. Mouths and lyric typing were also checked frame by frame. The scripts are in the
scratchpad, `ref2/`.

| | **V1** "I'm upping my P(doom)" (2:36) | **V2** "Nothing Went Foom" (5:00) |
|---|---|---|
| look | late-80s/90s cel anime, PC-98 pixel grain, UI windows and HUDs | a world of light: violet haze, gold particle floors, kinetic typography |
| hard cuts | 92 (one every 1.7 s), plus glitch cuts | **3 in 5 minutes** (49.4, 65.5, 124.2 s) |
| scene changes | every 1.7 s, by cutting | 52 (one every 5.8 s), all but 2 are moves or transformations |
| camera | mostly locked within short shots | **moving in 91 % of frames**: push-ins 48 %, pull-outs 28 %, constant slight roll drift |
| near-identical consecutive frames | 1 % | 0 % |
| what it syncs to | cuts on beats (51 % within 2 frames of a beat; chance is 29 %) | words: lyrics type on as they are sung, and mouths move on syllables (visual accents are *not* beat-locked: 12 % against 16 % chance) |
| mean brightness | 80/255 | 85/255 (dark, but never black) |

## V2: how it moves without cutting (the main reference)

There are 52 scene changes. By type:

| type | count | example |
|---|---|---|
| **particle dissolve → re-form** | 28 | 22.1–23.9: the "AGAIN" screen breaks into pixel particles, they swirl into a vortex, and the vortex re-forms as the singer jumping |
| **pull-out reveal** | 8 | 236: a golden wall of cracks tilts down and becomes the floor plane; the scene was a wall, now it is the ground |
| **through dark** | 7 | 220: the singer dissolves into drifting text, which shrinks to a radiant point; the point becomes a sun on the horizon with figures walking |
| **push through light** | 4 | 149: the camera pushes into the window light until the frame is white; the whiteboard room grows out of the white |
| **whip / slide** | 3 | 156, 177: lateral slides along the whiteboards |
| hard cut | 2 | |

Other transitions are **in-place transformations**. At 191.7 the whiteboard's colour turns to a blue
grid while the text breaks into digits that spiral into a HUD ring: same layout, new world. At
257 a horizontal flare and a radial burst give way to the singer standing on a particle stage.

The camera never rests. Median zoom is 6 % per second, with bursts of 60 %+ per second only
during transitions. Median pan is 17 px/s (at 960 px wide). Roll drifts about 0.6° per second, so
the frame always breathes. Speed is used as punctuation: slow push-ins inside a scene, fast
push-throughs between scenes.

## V2: the character

- **She is never a still picture.** She moves like a puppet (head tilt, hair sway, shoulders and
  breathing) while the camera also moves, so no two frames match.
- **Entrances and exits are made of particles.** Her edges dissolve into, or assemble out of, gold
  particles (104.9–105.7). She stands on a particle stage inside a **halo ring**, back-lit by a
  sun or point with rays (62, 68, 258, 293).
- **Lip-sync is viseme-based, not "open/close".** Frame by frame (138.4–140.7) the mouth uses at
  least four shapes: closed line, small round "o", mid, and wide "a". It changes every 2–4 frames
  (8–12 changes per second), with in-betweens. It closes on consonants (140.20–140.27) and opens on
  vowels. The face is tracked by a moving camera, so an automatic correlation was inconclusive
  (the face was tracked in only 28 % of frames). The frame-by-frame check shows the shapes
  following the sung syllables.
- **Eyes and expression change with the meaning of the line** (open-mouthed joy, closed-eye
  smile, surprise), not only with loudness.

## V2: sync to the music

- Lyrics appear **syllable by syllable as they are sung** (220.1–221.8: "She doesn't need to own
  the sun,"). Key words are larger and gold ("sun", "STILL", "EXPONENTIAL"). After the line ends,
  **the words break into particles** and drift into the next image.
- Scene changes ride section and line changes, not every beat. Bursts and flares are kept for
  the big hits.
- Result: the picture follows the *voice* (words, mouth, phrase), and the camera carries the
  groove.

## V2: particles, space, dimension, light

- **Particles:** gold and white glitter makes the ground (a particle floor that recedes to the
  horizon). Text, objects and the character are all made of particles, so every transition is
  material changing state (screen → dust → vortex → body). Particles drift slowly upward in the
  haze.
- **Space:** a deep, horizon-based world. There is almost always a ground plane of light and a
  glowing horizon line. Objects stand on it as frames, screens, rings, hourglasses and gates.
  The camera flies between them.
- **Dimension:** walls fold into floors (236). A flat whiteboard becomes a 3D room (149). A
  scene shrinks to a point and opens into a horizon (220). Text and pictures are flat planes in
  3D space, seen at angles.
- **Light:** violet/indigo atmosphere with a warm horizon glow. A back-light behind every
  subject (sun, halo, window), with volumetric rays. Anamorphic horizontal flare on bursts. Strong
  bloom. Gold against violet is the main contrast. Brightness stays dark but never pure black.

## V1: what to take, what to leave

- **Take:**
  - every line gets its own concrete visual idea (P(doom) meter, FLOPS counter, paperclip,
    shoggoth);
  - the character is always acting (pointing, running, flying, singing into the mic);
  - strong graphic colour pops.
- **Leave:** the hard-cut, beat-locked editing (one cut every 1.7 s) and the glitch cuts. Shots are
  too short for sustained lip-sync, and the cutting conflicts with "no hard cuts".

## What changes in LOADING because of this

1. **One continuous camera; no hard cuts.** Every change of place is one of the motivated
   transitions above, and each one also carries the film's dimension grammar (see
   `CREATIVE_PLAN.md` §5):
   - **point gate:** push through a light, 3D → 0D → 3D;
   - **fold:** sphere → plane → line;
   - **particle state change:** body → dust → body;
   - **pull-out reveal:** the scene was inside a key, an eye or a lantern.
2. **Animation on ones.** Character drawings deform every frame (breathing, hair, head tilt).
   Expression morphs are fluid in-betweens, not on twos, and the camera drifts and rolls slightly
   in every frame.
3. **Viseme lip-sync** (closed / o / mid / a) from the isolated vocal:
   - loudness controls how open;
   - the spectral shape picks round versus wide;
   - consonant dips close the mouth;
   - shapes change every 2–3 frames, with in-betweens and a slight anticipation.
4. **Characters enter and leave as particles**, always back-lit (halo, point, horizon), standing
   in a light environment rather than on black.
5. **Light palette:** deep indigo-violet atmosphere and a warm horizon glow behind black-blue
   space. Amber/gold city lights against it. Teal and amber stay A and B. Red is still used only
   three times.
6. **Words of light, sparingly:** about 12 key words across the song, written by the scene's own
   particles as they are sung. They break back into the scene after the line, never as subtitles.
