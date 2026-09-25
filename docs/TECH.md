# Technical plan

## Scope and status

| Part | Owner | Status |
|---|---|---|
| Story, relationship, song, lyrics, beat map, storyboard | Claude | written: [TREATMENT.md](TREATMENT.md), [SONG.md](SONG.md), [STORYBOARD.md](../STORYBOARD.md) |
| **Character design and character drawing** | **ChatGPT (per the user's direction)** | handed off. The interface they must meet is below. |
| 60 fps engine, motion system, camera, backgrounds, transitions, rendering, QA | Claude | engine core written (`src/core.js`, `src/dyn.js`); backgrounds and scenes not started |

`src/rig.js`, `src/body.js`, `src/costume.js`, `src/hair.js`, `src/chatgpt.js` and `src/sheets.js` hold my **prototype** character construction. It is superseded by the character work being handed to ChatGPT. It stays in the repo only as a working example of the interface below: it renders at about 30 ms per frame, which proves the character layer is cheap enough for 60 fps. Delete it once the real characters land.

---

## 1. Rendering architecture: stable cels over a painted world

**Measured on this machine (no GPU, software WebGL):** a ClaudeAnimationBase demo frame with p5.brush watercolour fills takes about 25–35 s. At 60 fps a 2:05 film is 7,488 frames, which would be roughly 60 hours. So the film is split the way anime production is split:

| Layer | How it is drawn | How often it changes |
|---|---|---|
| **Backgrounds** (sky, town, roofs, sea) | p5.brush watercolour, painted once into **cached plates** (PNG files keyed by shot, layer and a hash of the painter's code). Each boiling layer gets a 3-drawing boil cycle, like a traditional boil loop. | Texture boils at **8 Hz**. The camera moves the plates continuously at 60 fps, with parallax per layer. |
| **Characters and props** | Canvas2D cel layer: clean tapered line art and flat cel colour | **Every frame, continuous at 60 fps. No boil, ever.** |
| **Paper and grain** | static paper under everything, grain multiplied over the top | never (it is the "screen") |

- Frame cost is one composite of the cached plates plus the cel layer: about 30–60 ms, so the full film at 60 fps is minutes per worker rather than days.
- p5.brush stays where its texture belongs: in the painted world.
- The film's pipeline therefore gains a pre-pass: `render.mjs --plates` renders any missing plates in parallel; frames then load them.

## 2. The motion contract (what makes it smoother than the reference)

**Frames are pure functions of absolute time t** (a ClaudeAnimationBase rule, kept). What changes:

1. **Nothing is quantised.**
   - No `onTwos()`. No 12 Hz pose stepping. No boil on character geometry.
   - Every position, rotation, camera value and secondary motion is evaluated at the exact frame time at 60 fps.
   - At 150 BPM one beat is exactly 24 frames, so hits land on frames.
2. **Deterministic physics without frame-to-frame state: `simulate()` in `src/core.js`.**
   - Secondary motion *is* integrated, on a fixed 240 Hz grid **anchored to absolute time**. Each frame re-integrates a window of history (about 1.2–3 s) that ends at t.
   - Overlapping frames therefore compute the *same* trajectory, so the result is continuous, frame-rate independent and reproducible in any render order.
   - The start-up transient of the window decays to about 1e-3 before it reaches t.
3. **Overlapping action from followers, not delays: `follow()`.**
   - Each body level follows the same intent signal through its own damped second-order filter, with its own frequency f and damping ζ.
   - ChatGPT: eyes (f 10) → head (4) → shoulders (3) → torso (2.6) → hips (2.2).
   - Claude: eyes (4) → head (1.8) → shoulders (1.3) → torso (1.1) → hips (1.0).
   - Parts start, overshoot and settle at different moments, continuously. Nothing waits and then pops.
4. **Chains for the tail and hair: `solveChain()` in `src/dyn.js`.**
   - These are angle-space chains driven by the actual root trajectory: the pelvis for the tail, the head for hair.
   - Each segment follows its parent's bend or hangs with gravity. It also gets an inertial push from the root's acceleration, plus a deterministic wind field.
   - Stiffness and damping fall toward the tip, so **the tip responds last and settles last**, with no hand-keyed "kicks".
   - Claude's hair uses separately tuned groups: the rear mass (≈1.1 Hz, ζ .35), side locks (≈1.6 Hz), front strands (≈2.6 Hz, light), and extra tip lag.
5. **Faces are continuous channels.** Lids, lower lids, brows, each mouth corner, mouth opening, gaze and pupil size each have their own easing. Expressions never swap between frames.
6. **Contacts are solved, not approximated.**
   - 2-bone IK plants the feet: a stance foot's world position is fixed, so feet never slide.
   - Held paper is drawn at the solved fingertip point.
7. **The camera eases.**
   - Every move goes through eased keys plus a follower, so tracking shots start late and overshoot slightly, like a human operator.
   - Shake is smoothed noise, not per-frame random jumps.

## 3. Scale system

- **One canonical character height `h` drives every proportion.** Both characters share one proportion table: 6.6 heads, measured from `reference/chatgpt_dragon_ref.png`, the anchor.
  - Your two references disagree on proportions: the ChatGPT art is about 6.1 heads and the Claude art about 7.3.
  - Claude is refitted to ChatGPT's anatomy: same shoulders, limbs, hands, eyes and line weight. Only her hair and silhouette styling differ.
- **A camera changes how big `h` looks, never the ratios.** The shot scale targets on the 1920×1080 frame (the head is `h`/6.6):

| Shot | `h` on screen | Framing |
|---|---|---|
| extreme wide | 90–160 px | the town and sky; the characters are marks on the roofline |
| wide / two-shot full | 380–520 px | both head-to-toe with the roof; feet visible for contact |
| medium | 900–1200 px | waist up; tail and hair acting both readable |
| close-up | 2200–2800 px | head and shoulders |
| extreme close-up | 5000+ px | eyes, hands, paper |

- **Ground contact:** both characters stand on the same world groundY. Relative height is fixed: identical body height, and ChatGPT's horns add +0.03h to her silhouette.

## 4. Character interface for the externally designed characters

For the characters to animate *smoothly* in this engine, they must be **drawing functions**, not finished images. Moving a PNG sprite cannot produce overlapping action, hair lag or tail drag. Whatever ChatGPT delivers should meet this contract. It can be written as p5/Canvas2D code, or as layered art I can rebuild into it.

```js
drawChatGPT(x, groundY, h, pose, dyn)   // (x, groundY): world point between the feet; h: canonical height px
drawClaude (x, groundY, h, pose, dyn)
```

- **`pose`**, every field continuous (floats):
  - `yawH`, `yawC`, `yawP`: head, chest and pelvis turns (0 front, ±1 profile, ±2 back), so turns can be staggered
  - `lean`, `tilt`, `bob`, `headDx` / `headDy`
  - `gazeX` / `gazeY`, `lid` (or `lidL` / `lidR`), `lower`, `brow`, `browTilt`, `mouthOpen`, `mouthSmile`, `mouthAsym`, `pupil`, `blush`
  - `arms.{R,L}`: `{ a, b, w, hand }` (upper-arm and forearm angles, the hand pose name) or `{ ik: [x, y] }`
  - `feet.{R,L}`: `[u, lift]` foot targets
- **`dyn`**: the engine supplies the solved secondary motion as world points: `tail` (14 points), `hair.{rear[], side[], front[], tips[]}` (chains), `skirtSway`, `coatSway`, `tieSway`. The drawing function draws **through** those points, and never invents its own motion.
- **Layers the art must keep separate**, so the engine can move them independently:
  - eyes, lids and mouth separate from the face
  - hair split into rear mass, side locks, front strands and tips
  - the tail as a chain of about 14 segments
  - sleeves and hems as separate shapes
- **Views:** front, 3/4 and profile are required, and back 3/4 is required for S30 and S36. These can be authored key shapes that the rig morphs between; they do not have to be projected.
- **Stability:** no random or time-based jitter inside the character. The same pose must produce the same drawing.

## 5. QA plan (runs on every shot before the full render)

- **Contact sheets per shot**, at a fixed 0.1 s step, read like a viewer: is each read given enough time?
- **Frame strips at 1/60 s** for every signature action (the list is in TREATMENT §6). In each strip, inspect the anticipation, acceleration, peak, deceleration, overshoot and settle, and look for pops, snaps, sliding feet, hair or tail snapping, and scale jumps.
- **Motion telemetry.** Every actor can export its joint positions per frame. A script flags any jerk spike (a discontinuity in acceleration) across the whole film. This is a numeric check for pops the eye might miss on a sheet.
- **Face crops and contact crops** (feet, hands on paper) that follow the world point through the camera (`--crop-at`).
- **Transition checks**: the last and first 0.5 s of every seam.
- **Playback check**: a 60 fps preview encode of each finished section, watched at speed.

## 6. Render budget

| Item | Estimate |
|---|---|
| Plates | about 37 shots × about 4 layers × up to 3 boil variants. Many layers are reused, since there is one rooftop set and one town. Roughly 1–3 h, one-time and cached. |
| Frames | 7,488 at 60 fps × about 0.1–0.3 s (composite + encode) ≈ 15–40 min with 4 workers |
| Output | 1920×1080, 60 fps, H.264 CRF 17, muxed with the song once it exists (the film is locked to the beat map in SONG.md, so picture can be built before the audio arrives) |
