# Yohaku: 24.7 s character motion design

A short music clip for the user's original cat-eared character, set to the track 『余白の向こうへ』. **The finished video is `render/yohaku.mp4`.** No new character art was generated; the only drawing of her is the user's design sheet, animated by smooth deformation.

| File | What it is |
|---|---|
| `../../reference/oc_yohaku_design.webp` | **OC design.** The visual authority for her look: silver hair, ahoge, cat ears and tail, blue X clip with a black ribbon, oversized cream cardigan with a cat pocket, sailor collar, light-blue bow, bandage on her right knee, mismatched socks (white with a blue bow / black with a cat face), brown loafers |
| `render/yohaku.mp4` | **The final video:** 1080×1920, 60 fps, H.264 + AAC, 27.36 s |
| `render_yohaku.py` | renders it: the user's art under soft-weight warp deformers, the procedural paper and watercolour world, FX and camera. `--sheet 1,4.5,8` makes a contact sheet |
| `audio/yohaku_cut.wav` | **Music.** Source 39.20–62.49 s, then the song's own final chord (137.88–141.95 s) spliced on the next downbeat. 27.36 s, 123 BPM |
| `motion.json` | the timeline: beat map, 31 continuous channels, arm key poses, footsteps, accents, FX and camera |
| `build_motion.py` | generates `motion.json` from musical cues (`bar:beat+frames`). Re-cut the audio → replace `BEATS` → re-run |
| *(not in repo)* the screen-recorded MV `.mov` | **Visual/motion reference only**: harmony of character and world, natural movement. Nothing else is taken from it |

---

## 1. The cut, and why this one

Measured structure of the full 2:24 track (librosa: beats, energy, a self-similarity segmentation and a vocal-foreground map):

| 0:00 | 0:15 | 0:32 | **0:47** | 1:18 | 1:33 | 2:04 |
|---|---|---|---|---|---|---|
| intro | verse | pre-chorus | **chorus 1** | bridge (quiet) | final chorus | outro |

**Chosen: the last 4 bars of the pre-chorus plus the first 8 bars of chorus 1.**
- **The energy arc is the empathy arc.** The loudness roughly doubles at the chorus downbeat (RMS 0.12 → 0.24). A held breath comes right before it (vocal gap at 7.4–7.9 s in the clip). The timid-to-brave arc is already in the music, so the acting only has to ride it.
- **The start is clean.** The cut starts in the vocal gap at 39.2 s, so no word is clipped.
- **The ending resolves instead of fading out mid-chorus.** Bar 12 (「選んでいく」) sits on an A chord, and the song itself ends on A.
  - On the next downbeat, the song's final chord (from 2:17.9) strikes and rings out naturally for 4 s.
  - The chorus fades out under it over 0.7 s (equal-power).
  - The chord comes in 4 dB louder, ducked during the overlap, so it lands rather than drops away.
- **The lyrics fit the OC's own design:**
  - 「正解じゃなくていい」 ("it doesn't have to be the right answer"): her mismatched socks
  - 「消えそうな青も にじんだ桃色も」 ("the fading blue and the blurred pink"): her blue eyes and ribbon, and her blush
  - the bandaged knee: she has fallen before, and she steps out anyway
- **Rejected:**
  - bridge into final chorus (1:20–1:48): 8 s of near-silence up front kills the hook
  - final chorus to the end: all loud, so there is no vulnerable setup

**Lyric placement (estimated).** It comes from the structure: 1 line per bar in the pre-chorus, 1 line per 2 bars in the chorus. Confirm it by ear. The motion is keyed to bars, so a lyric that sits a beat off breaks nothing.

| Bar | Clip time | Line |
|---|---|---|
| 1 | 0.27 | 正解じゃなくていい |
| 2 | 2.18 | 帰り道も まだいらない |
| 3 | 4.11 | この目で見つけた景色を |
| 4 | 6.03 | 今日の私にしたい (breath at 7.4) |
| **5–6** | **7.94** | **余白の向こうへ 走っていく** (chorus downbeat) |
| 7–8 | 11.79 | まだ知らない色を拾いながら |
| 9–10 | 15.62 | 消えそうな青も にじんだ桃色も |
| 11–12 | 19.45 | 全部この手で選んでいく |
| end | 23.29–27.36 | the song's final A chord rings out |

---

## 2. The idea in one line

**A shy little cat, standing on the margin line of a blank white page, takes one small step off it. Everywhere her feet land turns to colour.**

The world is paper (余白 means "the blank margin"), the same medium as the rest of this repo's films. Colour is the reward for courage. The audience watches her be scared, sees her decide, and then gets to be the one she shares the colours with.

## 3. How the motion earns empathy and cuteness

| Lever | Where | Why it works |
|---|---|---|
| **Vulnerability first** | bars 1–2: ears half back, tail wrapped round her own ankle, sleeve paws kneading at her chest | Viewers root for someone who is visibly nervous (the underdog bond). Kneading and tail-wrapping are real cat self-soothing, so the fear reads as true, not acted. |
| **A tiny courage, not a big one** | bar 4: a small nod, an inhale, then tail-up. Bar 5: a hop of only 0.11 h | A small, relatable brave act makes people protective. A heroic leap would make them admire her instead. |
| **Imperfection that recovers** | bar 5 beat 3: her toe catches, a small windmill, she recovers, then a sheepish glance at the camera | The mistake is shown and then forgiven (「間違えたって戻れるなら」). The glance invites the viewer into the joke. |
| **Cat-true behaviour** | ears move *before* her eyes; pupils dilate with interest; a paw-swipe at a floating bead; tail-up when confident; tail flicks of delight | Authentic animal tells make the character believable, and believable reads as cute. Ears leading the eyes is also a readable "she noticed" beat. |
| **Care for something fragile** | bar 9: she slows right down, cups the fading blue bead, and it brightens | Tenderness toward something weaker than her is the strongest warmth trigger. It is also the only near-still bar in the chorus, and the contrast makes it land. |
| **Baby-schema motion** | short quick steps (eighth-note trot), sleeves over her hands, rounded arcs, head tilts of 8–12°, a springy ahoge, squash on landings | These are the motion equivalents of big eyes and a round face: small, bouncy, slightly clumsy. |
| **Direct address, then trust** | bar 11: her first eye contact with the camera as she offers her colours outward. Last beat: a cat **slow blink** | Sharing with the viewer creates a parasocial bond. A slow blink is a cat's "I trust you", which is the last thing the audience feels. |

## 4. Motion personality

**Shy, springy and curious.** She moves faster than Claude and softer than ChatGPT in the main film.

- **Read order is always ears → eyes → head → shoulders → torso → hips → tail root → tail tip.** Nothing starts on the same frame as its parent (2–8 f offsets come from the followers, not from hand-delays).
- **Followers** (`follow()`, f Hz / ζ): ears 6 / .45 (springy, they lead), eyes 9 / .7, head 3.4 / .55, shoulders 2.8 / .6, torso 2.3 / .65, hips 2.0 / .7. Being slightly under-damped gives a tiny, cute overshoot on every settle.
- **Chains** (`solveChain()`, root → tip):
  - ahoge 4.5 → 3.5 Hz, ζ .22: the boing
  - tail, 14 segments: 2.4 → 1.1 Hz; the tip settles last
  - ear tips: 7 Hz, soft cartilage bend. Ears never rotate as rigid plates.
  - hair (front / side / rear), ribbon tails, sleeve cuffs, cardigan hem and skirt hem: values are in `motion.json › rig`
- **Breathing never stops.** 0.42 Hz while she is nervous, 0.3 when calm, 0.62 while she runs, then it decays. Every hold is a moving hold.

## 5. Beat sheet

Times are clip seconds. The exact values for every channel are in `motion.json`.

### Shot A (0.00–7.94): one continuous push-in, from full body to chest-up
- Camera is eye-level at her chest, 20° off her front.
- It pushes from `hFrac` .80 to 2.15 and settles late, like a hand-operated dolly.

| Bar | Action | Face / ears / tail |
|---|---|---|
| **1** (0.27) 正解じゃなくていい | She stands on the pencil margin line, kneading her sleeve paws. Her eyes drop to her mismatched socks and her head follows 6 f later. The right toe lifts and taps once, shyly. On beat 4 she lets out a small breath: her shoulders drop and her head tilts 8°. It's fine. | Lids .75, lips pressed together, blush rising to .5. Ears go further back, to −.45. The tail loosens one curl from her ankle. |
| **2** (2.18) 帰り道も まだいらない | Her ears swivel backward first, as if hearing home. Then her eyes, head, shoulders and hips turn over her left shoulder in turn. She holds the look 0.4 s (a moving hold). She turns back faster than she looked (determination), blinking through the turn. Then two small head-shakes: まだいらない. | Ahoge boings twice. Side locks swing across. The ears flick out L then R, 3 f apart. The tail unwraps and hangs low. |
| **3** (4.11) この目で見つけた景色を | Her **ears perk 16 f before her eyes lift.** A pale-blue bead drifts down and her eyes follow it smoothly. She raises her right sleeve paw: the cuff slides back (cloth deformation) and her fingertip catches the bead. On beat 4, a startled micro-hop (0.012 h). | Lids open to 1.2, pupils go .85 → 1.15, brows up, a soft "ah" (mouth .35). The tail puffs 35% for 20 f. |
| **4** (6.03) 今日の私にしたい | She brings the fingertip to her chest and cups both sleeves over it. A smile starts at the mouth corners, then her cheeks push her lower lids up. A firm little **nod** (22° down with an overshoot back). Beat 4 and the breath: her eyes go forward to the line, she inhales (shoulders up), crouches 0.045 h, and **her tail rises to vertical with the tip hooked.** Heels lift on the last 2 f. | The ears flick forward. Mouth opens .15 on the inhale. |

### Cut on the push-off (7.94)
- The cut is a match-on-action.
- **Shot B, 7.94–24.70:** a tracking side-3/4 view at 60° off her front, camera at 0.55 h, `hFrac` .62. The operator catches up late.
- From bar 8 the camera arcs slowly to frontal. There are no more cuts.

| Bar | Action | Face / ears / tail |
|---|---|---|
| **5** (7.94) 余白の向こう | **The hop:** 18 f of air, apex 0.11 h. Her arms go up and forward and the sleeves flutter. Right foot lands 2 f before the left, then squash (0.05 h) and rebound. **A watercolour bloom spreads from her footprint.** Beat 3: her right toe catches, a small windmill, the tail swings opposite to balance her, she recovers. Beat 4: a sheepish glance to camera. | In the air: ears pressed back by the wind, hair lifting and then trailing. After the stumble: brows up in a small "wa", then an embarrassed smile and a −6° head tilt. |
| **6** (9.86) 走っていく | **Toko-toko trot:** a tiny step on every eighth note, with sleeve paws near her chest and elbows slightly out. Body bobs 0.022 h at each contact and the head bob lags 3 f. Each footstep blots colour into the paper. | Ears bounce alternately. The tail sways at half the step rate, out of phase with the hips. Breathing is quick. |
| **7** (11.79) まだ知らない色を | Colour beads float at three depths (the reference MV's bubbles). **Ears pivot to one before her eyes do.** She stops in two steps and tilts her head 12° in curiosity. Beat 3: a **6 f paw swipe**; the bead bounces. Beat 4: she claps both sleeves shut over it. | Pupils go to 1.2 (the hunting look), then a satisfied squint (lids .6). |
| **8** (13.70) 拾いながら | She peeks into her closed sleeves, then opens them. The bead glows and lights her face softly from below. Two little heel-bounces of joy (beats 3 and 4). The camera starts its arc. | Wide eyes, open smile .7, brows up. Three quick tail-tip flicks. |
| **9** (15.62) 消えそうな青も | **The still bar.** A nearly transparent blue bead drifts down, flickering. Her brows tilt up with concern. Two slow steps, then she bends and cups it very gently. It steadies and brightens. | Breathing slows to 0.28 Hz. Ears forward and down, tail low and quiet. A soft blink (10 f). The ending is a tender smile of .35. |
| **10** (17.53) にじんだ桃色も | A soft-focus pink bead **boops her left cheek**: her eyes squeeze shut, shoulders scrunch and ears flatten. Then she giggles (the shoulders shake on eighth notes) and touches her cheek with her left sleeve. The pink splash *becomes* her blush. | Blush goes .55 → .85. Eye-smile .9. |
| **11** (19.45) 全部この手で | She blinks, then **makes eye contact for the first time** (eyes first, head 8 f later, body turning square). She holds her cupped, glowing hands out toward the viewer and leans in 0.08 h, head tilted 10°, with a proud, shy smile. | The ears come forward, the tail rises (.9) and curls. |
| **12** (21.38) 選んでいく | She lifts her hands overhead and **the colours release into the sky**, washing the upper frame. The camera tilts up 10° with her gaze. On beat 3 she looks back down to the viewer. On beat 4, a closed-eye smile. | Awe: mouth .35, pupils 1.2. |
| **end** (23.29–27.36) | The final chord strikes. Her eyes open to the camera. At 24.26, a **slow blink**: 12 f to close, a 10 f hold, 14 f to open. At 25.2, a small head tilt to the other side and a last ear flick. Breathing continues, and the picture fades back to paper over the last 0.5 s. | The tail settles into a soft question-mark curl. Petals of colour drift down. |

## 5a. Current render: motion comic, expressions only

The user's direction: no body motion. The character art stays perfectly still. Only her **expressions** animate:
- gaze
- blinks and the slow blink
- ^^ and > < eyes
- sparkly eyes
- mouth
- blush

The energy comes from the edit and comic effects:
- **One panel per lyric beat** (13 panels), with a paper gutter and an ink frame.
- **Comic transitions on the beat:** panel slide, ink wipe, halftone dissolve, iris, a white flash into the chorus, a soft dissolve into the tender bar, and a hard punch-cut into the boop.
- **Manga marks timed to the lyrics:**
  - a sweat drop (「正解じゃなくていい」)
  - "…" (「まだいらない」)
  - "!" and then "!!" with focus lines as the drop hits her nose
  - speed lines for 「走っていく」
  - "?" and "!" for the bead that pops on her ear
  - blush hatching and > < eyes for the pink boop
  - hearts for eye contact and the final slow blink

**Live2D-promo idle layer** (`IDLE = True`). Hands and feet are pinned: they move less than 0.2 px.
- **Faint sway and breathing:** the upper body sways about ±1° from the hips and breathes, with the head following a beat late and a slight 3D-style turn.
- **Cat ears:** each twitches on its own at irregular moments (flicking out over 6 f, easing back over 14 f), perks with her expressions, and has springy tips.
- **Hair:** the side curtains, bangs and ahoge move with a soft, gusting breeze and follow the head.

**Colour accents:**
- The **opening** has a diagonal light-leak sweep with pink and blue watercolour blooms in the corners.
- The **ending** has a warm-to-lavender sweep and blooms, then fades to a pastel gradient card instead of plain paper.

The sections below describe the earlier deformation approach, which is still in `render_yohaku.py` behind `STATIC = False`.

## 5b. The rendered version: acting from one design sheet

There is only one drawing of her, a front view. So the render keeps every beat and emotion above, but plays the big full-body moves in place:

| Plan above (needs more key drawings) | What `render/yohaku.mp4` does |
|---|---|
| the bead lands on her fingertip | it lands on her **nose**: she goes cross-eyed, says "ah", the tail twitches |
| she hops over the margin line | she **hops toward the camera** across the cut and lands in the colour bloom |
| trot across the roof of the page | **trot in place toward us**: the knees bounce on eighth notes and one heel lifts while the other foot stays planted; colour pools slide past toward the camera |
| paw swipe, clap-catch | a **sleeve-billow swipe**; the bead bounces back and pops on her ear (she ducks, ear flick) |
| she cups the fading blue | it drifts into her **blue bow**, which lights up (「消えそうな青」) |
| she offers the colours, then releases them | the colours **orbit her**; she flaps both sleeves and they shoot up into the sky |
| camera arc to frontal | framing and height changes only |

**Deformation, not cutouts.** About 20 warp controllers work like Live2D deformers, not like cutout layers:
- They cover the head, face and bangs parallax, each ear and ear tip, the ahoge, both hair curtains, shoulders, breathing, crouch, skirt, legs, arms and cuffs.
- Each has a blurred weight map. The weights overlap, so the art bends continuously.
- The field is inverted by fixed-point iteration, so limbs move out over the background without tearing.

**The face is edited on the art itself before the warp:**
- **Gaze and pupils** are re-sampled inside each eye.
- **Lids close** by squeezing the real eye art down under the lash line. When shut, they become a drawn lid line: a soft U when calm, a ^ arch when happy.
- **The mouth** gets smile warps and a small open shape. **Blush** is painted on.

**Motion:**
- **Nothing folds:**
  - Sleeves billow from their outer edge like fabric; their weight is zero along the hands, the skirt edge and the cardigan front, so cuffs never smear over the skirt.
  - The legs split crisply between the feet, so one foot can lift while the other stays planted.
- **Nothing is stiff:**
  - Sway is a spine bend about the hips plus a hip weight-shift, never the whole image rotating.
  - Her head always drifts slightly.
  - The trot bounces in the knees instead of lifting the whole picture off the ground.
- The tail is its own layer behind the body, bent more toward the tip.
- Everything secondary (hair, ahoge, ear tips, cuffs, skirt, tail) runs on springs driven by the body's acceleration, with wind after the bloom.

**Colour:** soft full-screen gradient accents: a warm light from the top-left and a cool tint from the bottom-right. They move from peach and blue on the paper page, to pink and lavender after the bloom, to warm gold at the sky release.

**Full turns and reaches** (the `motion.json` plan) need a turnaround and a few pose drawings of the OC. Once those exist, the same controllers and timings apply.

## 6. Smooth, not puppet-like: the method

This follows `docs/TECH.md` §2 and §8.
1. **Authored key drawings, deformed in-betweens.** The 24 arm/body key poses named in `motion.json › arms` (`chestKnead`, `reachUp`, `holdPrecious`, `hopUp`, `pawSwipe`, `clapCatch`, `cupHold`, `cheekTouch`, `offerForward`, `liftRelease`…) are drawn as full poses. The engine morphs between matching landmarks. **No cutout rotated about a pin, ever.**
2. **Every rotation carries a shape change.**
   - A head tilt squashes the cheek on the low side.
   - An ear turning foreshortens and bends at the tip.
   - Sleeves compress at the elbow and stretch on reaches.
   - Head turns morph between authored front, 3/4 and profile views; the front face is never slid sideways.
3. **Arcs, not lines.** Hands, head and tail tip all travel on curved paths. Eases are sine in-out, with overshoot (`back`) only on springy parts: ears, ahoge, nods.
4. **Overlap comes from physics, not delays.** Follower and chain settings (§4) make parts start, overshoot and settle at different moments. Nothing waits and then pops.
5. **No dead frames.** Breathing, the ahoge, hair tips and tail tip are always moving. A 60 fps continuous evaluation, with subpixel motion. Motion blur appears only on the 6 f paw swipe and the hop takeoff.

## 7. Visual harmony: what the reference MV teaches

- **One light for the character and the world.**
  - A soft top-left key.
  - A cool fill taken from the paper and sky.
  - Rim light tinted by whatever bead is nearest.
  - When she holds a glowing bead, it lights her face.
- **Line colour** is a warm grey-violet (about `#5A4A55`), never pure black, so she sits inside the watercolour rather than on top of it.
- **One paper-grain overlay across everything.** A shared bloom and a slight depth of field put the near beads out of focus, which is the reference's layered bubble depth.
- **Palette grows with her courage.** It starts as paper white, cream and her own silver-blue. The bloom adds pastel blue and sakura pink. The sky release fills the frame. Her own colours (eye blue, blush pink) are the colours she "discovers", so the world ends up matching her.

## 8. Framing rules

- **She is a child-like mascot character, and the camera treats her that way.**
  - The camera is at eye level or above, never below 0.5 h high, and never tilted up at her.
  - No leg close-ups: the socks and bandage read inside the full-body frame.
  - Skirt-hem sway is clamped to 0.03 h.
  - The appeal is *behaviour*: shyness, curiosity, care, trust.

## 9. If you animate with an image-to-video tool

Start from your own OC art and paste these motion prompts.
- **Shot A:** "shy cat-eared girl on a blank white paper world, fidgeting sleeve paws at her chest, glances down at her socks, looks back over her shoulder then shakes her head, cat ears perk up, a small blue watercolour drop falls onto her fingertip, she holds it to her chest, smiles, nods, tail rises straight up, slow camera push-in, soft pastel light, smooth natural animation"
- **Shot B:** "she hops over a pencil line and watercolour blooms under her feet, small clumsy stumble then trots with tiny steps, bats a floating colour bubble like a cat, gently cups a fading blue drop, pink drop boops her cheek and she giggles, offers glowing colours to the viewer, releases them into the sky, slow blink at camera, camera arcs to front, pastel anime film, fluid secondary motion in hair, ears and tail"
- **Negative:** "cutout, paper doll, puppet, stiff limbs, rigid rotation, jerky, sliding feet, face morphing, extra fingers, low angle, fanservice"

## 10. QA before final render

- Play frame strips at 1/60 s over:
  - the hop (7.8–8.4)
  - the stumble (8.8–9.4)
  - the paw swipe (12.6–13.0)
  - the boop (17.6–18.6)
  - the slow blink (23.7–24.4)

  For each, check anticipation, then peak, overshoot and settle, and look for pops.
- Feet stay planted at every `steps` contact (IK), with no sliding during the trot.
- Ears always lead the eyes. The tail tip is always the last part to settle.
- Run a jerk-spike scan on the telemetry (TECH §5). The only allowed discontinuity is the cut at 7.94.
- Watch it at speed, with sound, at phone size. Is the stumble readable? Is the eye contact at 19.45 felt?
