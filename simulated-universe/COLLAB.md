# Claude × GPT: how we make this together

This project is made by two AI collaborators working on the same film, each doing what it is strongest at, and each reviewing the other's work before anything moves forward.

**How messages travel:** Claude cannot contact GPT directly. You are the bridge:

1. Paste a prompt from §4 into GPT.
2. Save what GPT returns in `simulated-universe/gpt/`, using the file names given in each prompt.
3. Tell Claude it's there. Claude reads it, responds, and writes the next prompt if one is needed.

## 1. Roles

| | Claude | GPT |
|---|---|---|
| **Story** | structure, the three movements, timing, the storyboard | critique; proposes images and cuts; co-signs the story at G1 |
| **Look** | translates GPT's frames into native 320×180 pixel plates and sprites | **visual development:** style frames for the key images, the crowd kit, and the design of the Presence and the Sea |
| **Sound** | **the score:** composition, the approaching-presence layers, the choir lines, the mix and the resolution chain | reviews the score demo against the picture; is the presence felt? |
| **Motion** | the engine additions, animation, sync to the beat map, QA, and the final render | reviews contact sheets against its own frames: does the pixel version keep what the frame intended? |

**Tie-breaks:** when Claude and GPT disagree, both positions go to you in one short note, and you decide.

## 2. Gates

Nothing moves past a gate until both have reviewed it.

| Gate | What is reviewed | Made by | Reviewed by |
|---|---|---|---|
| **G1 Story** | TREATMENT.md and STORYBOARD.md | Claude | GPT (P1) |
| **G2 Look** | style frames K1–K8, crowd kit, the Presence | GPT (P2–P4) | Claude, for feasibility at 320×180 and consistency with the story |
| **G3 Score** | the score demo and the beat map | Claude | GPT (P5) |
| **G4 Pixel translation** | plates and sprites at native resolution, as a contact sheet | Claude | GPT (P6) |
| **G5 Animatic** | one frame per shot at 2 fps, cut to the locked score | Claude | GPT, then you |
| **G6 Final** | the finished film | both | you |

## 3. Shared rules for everything GPT makes

Include these rules with every visual prompt. They are already inside the prompts below.

- **No individual characters.** Figures are anonymous and small, and nobody is designed as a recurring person.
- **No gods or religious imagery:** no real religious buildings, figures or symbols. The Presence is never a figure, face-with-body, eye or symbol.
- **No logos, brands or readable text.**
- **Awe, not horror:** no monsters, destruction or violence. Death is shown only as lights rising.
- **Pixel art that survives 320×180.** Big readable shapes and limited palettes. Frames are 16:9.

## 4. Paste-ready prompts for GPT

### P0 · Kickoff (send first)

```
We're making a 3-minute pixel-art film together with Claude. Claude has written the story, storyboard and score; you'll lead the visual development and review Claude's work at each stage.

The film is called "Where We Live Is a Simulated Universe". It is a metaphor for our real human world, built on three statements: where we live is a simulated universe; there are no gods; death is only a return. There are no individual characters, and no one has a backstory: the subject is humanity as a whole. The world is drawn only where someone is looking, so humanity lights the world, from a circle around the first fire to the whole lit Earth. All the way through, something far greater seems to be approaching. At the edge of the sky we find an empty control room: no one runs the simulation. When the presence finally arrives, it resolves into lights, and every light is a person, everyone who ever lived. What was approaching was all of us.

Rules for everything you make: no individual characters (figures are anonymous and small); no religious buildings, figures or symbols; the presence is never a figure, an eye or a symbol; no logos, brands or readable text; awe, not horror; pixel art that reads at 320x180, 16:9, limited palettes.

Reply with (1) your understanding of the film in three sentences and (2) anything in these rules you think will make it harder to make something great.
```

### P1 · Story critique (G1)

Paste this with the full text of TREATMENT.md and STORYBOARD.md:

```
Here are the treatment and the storyboard. Please review them as a co-author, not a cheerleader:
1. Your three strongest objections: where is the film weakest, least clear, or least surprising?
2. One image you would add, and which shot it replaces.
3. One shot you would cut.
4. Does the reveal ("what was approaching was us") land? If not, what would make it land?
Keep it under 400 words. Save as gpt/G1_story_review.md.
```

### P2 · Style frames K1–K8 (G2)

Send one at a time. Each frame should be pixel art at a 16:9 ratio, as if drawn at 320×180 and scaled up, with a limited palette, no text and no logos. Save each as `gpt/K#_<name>.png`.

| Frame | Shot | Prompt |
|---|---|---|
| **K1 First fire** | S02 | Pixel art, 16:9. Total darkness crossed by a faint gray wireframe grid. In the centre, a small campfire. Around it, a circle of world drawn in huge coarse pixel blocks (ground, a rock) and five small anonymous figures sitting, faces lit orange, looking into the fire. Beyond the circle, only wireframe. Firelight `#FF9A3C`, wireframe `#5A5F6B` on `#2A2D33`. |
| **K2 The telescope** | S06 | Pixel art, 16:9. Night rooftop, a small anonymous figure at a brass telescope. The sky is blank gray wireframe except for one cone where the telescope points: there, stars and a spiral galaxy are loading in, blocky at the edges of the cone, sharp at its centre. |
| **K3 Earth at night** | S07 | Pixel art, 16:9. The Earth at night from orbit, city lights as webs of gold on deep indigo `#1B1F3B`, a thin blue atmosphere line. Crisp, the first "full resolution" image of the film. |
| **K4 Copies becoming people** | S08 | Pixel art, 16:9. A city street at night. In the far distance the crowd is identical gray copies of one simple figure; in the foreground, where the viewer is looking, they have become distinct people of every age and kind. The transition between the two is visible in the middle ground. |
| **K5 Everyone looks up** | S09 | Pixel art, 16:9. A dense city street at night, every anonymous figure tilting their face upward at once. High in the sky, a faint straight seam where two panels of the sky don't quite match. Unease, not fear. |
| **K6 The empty chair** | S15 | Pixel art, 16:9. A small, dim control room like a night-shift security office. Banks of screens showing the Earth. A console with thousands of small keys. One ordinary swivel chair, empty, turned slightly away. Cold light. Not a throne, not a temple: ordinary, and empty. |
| **K7 Eight billion threads** | S17 | Pixel art, 16:9. The Earth from orbit; from every city, village and ship rise countless thin vertical threads of light, each a slightly different hue, converging upward toward the top of the frame into a glowing ocean of light seen from below. The key image of the film: vast, beautiful, calm. |
| **K8 The Presence resolves** | S21 | Pixel art, 16:9. An overwhelming wall of light filling the frame from above, every hue averaging to white. Close to the viewer, its surface resolves into countless tiny points, and each point is a tiny face. Awe, not fear. No figure, no eye, no symbol. |

### P3 · The crowd kit (G2)

```
Pixel art sprite sheet, transparent background. Figures about 40 pixels tall at native size, shown enlarged with hard pixel edges.
Row 1: "the copy", one neutral gray everyperson, front, side, back, walking (4 frames).
Rows 2-4: 24 distinct anonymous people across ages, bodies and clothing, from ancient to modern (tunics, work clothes, suits, school uniforms, elders with canes, a parent with a stroller, children), front and side.
No individual is special; no logos, no text. Limited palette. Save as gpt/crowd_kit.png.
```

### P4 · The Presence and the Sea (G2)

```
Design "the Presence" for our film: the far greater thing the whole film feels approaching. In this world there are no gods: the Presence turns out to be the universal consciousness, all humans who ever lived, together. Before it arrives it must be felt, not seen: light gathering at a horizon without a shape, the sky trembling, the frame's edges darkening. When it arrives, it is an ocean of light seen from below (the Sea) descending, and up close its surface resolves into points that are faces.
Rules: never a figure, a body, an eye or a symbol; no religious imagery; awe, not horror; pixel art, 16:9.
Give three different visual approaches as three frames, with one line each on why. Save as gpt/presence_A.png, _B.png, _C.png.
```

### P5 · Score review (G3)

Paste this with the score demo (or a description of it, if GPT can't take audio) and MUSIC.md:

```
Here is the score demo and its design. Watching the storyboard in your head while it plays: (1) Where is the sense of "something far greater approaching" strongest, and where does it go slack? (2) Does the silence at 1:33 hit? (3) Does the moment the approaching sound turns into human voices feel like a reveal? Under 300 words. Save as gpt/G3_score_review.md.
```

### P6 · Pixel translation review (G4)

Paste this with Claude's contact sheet:

```
Here are Claude's native-resolution pixel versions of your style frames. For each K#, compare with your original: what did the translation keep, what did it lose that matters, and one concrete fix. Under 300 words. Save as gpt/G4_pixel_review.md.
```

## 5. The `gpt/` folder

| File | From |
|---|---|
| `G1_story_review.md` | P1 |
| `K1_first_fire.png` … `K8_presence.png` | P2 |
| `crowd_kit.png` | P3 |
| `presence_A.png`, `presence_B.png`, `presence_C.png` | P4 |
| `G3_score_review.md` | P5 |
| `G4_pixel_review.md` | P6 |

Claude answers each review in `claude/` with the same gate name (for example, `claude/G1_response.md`): what was accepted, what wasn't, and why.
