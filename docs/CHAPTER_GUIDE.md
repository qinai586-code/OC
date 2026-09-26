# Chapter guide (for everyone writing shots)

Read this, `STORYBOARD.md`, and `src/scenes/ch01_lab.py` (the reference chapter) before writing a shot.

## The film in one paragraph

A 156.65 s pixel-art music video for "I'm Upping My P(doom)". It is drawn at **320x180 native**, and every
native pixel becomes a crisp 6x6 block at 1920x1080. The protagonists are pixel personifications of **ChatGPT**
(near-black teal hair, two small jade horns, jade eyes, ONE dark dragon tail with a jade fin, long black coat
with teal lining, white blouse, dark skirt, asymmetric black legwear) and **Claude** (very long copper hair,
amber eyes, human: no horns, ears or tail, cream cardigan, dark brown skirt, one white and one dark
stocking). The recurring threads are the P(DOOM) knob, scale (the world shrinks around them) and the kid
in the yellow raincoat. Tone: clever and funny first, then accelerating, then consequences, then not knowing.

## Files

```
src/song.py              timing master: song.word_time(line_prefix, word), song.beat(n), song.bar(m), LYRICS
src/engine/px.py         Canvas (PIL-backed RGBA, hard edges), Sprite, dither helpers
src/engine/film.py       Shot, Frame (what your draw function receives)
src/engine/post.py       camera sampling to 1080p + lyric subtitles (you don't call this)
src/art/body.py          render(who, pose) -> Sprite ; make_pose(view, **kw)
src/art/poses.py         stand/idle/blink/run/walk/point/plead/think/surprise/reach_up/wave/bow/fall
src/art/portrait.py      bust(who, view, eyes, mouth, pose_key=..., bottom=-30) -> 2x close-up Sprite
src/art/ecu.py           draw_eye(cv, cx, cy, width, who, open_, look, flip, star, glow, pupil, t)
src/art/palette.py       GPT / CLAUDE / KID colour keys, world ramps NIGHT WARM JADE PAPER DOOM STEEL PINK GOLD
src/scenes/kit.py        easing, R(seed) randomness, dgrad (dithered gradient), dfill, dither_overlay, grade,
                         stars, moon, sparks_bolt, confetti, speed_lines, puff, text_big, kid(pose), folk(seed,pose)
src/scenes/props.py      knob (P(DOOM)), town, mascot, smiley_mask, marquee, paperclip, paperclip_field, crowd
src/scenes/chXX_*.py     one module per chapter, exporting SHOTS = [Shot(name, start, 0, draw_fn), ...]
src/film_def.py          lists the chapter modules in order
```

**Do not edit** anything under `src/engine`, `src/art`, `src/scenes/kit.py`, `src/scenes/props.py`,
`src/song.py` or other chapters' files. If you need a helper, put it in your own chapter file. If you think
a shared file has a bug, say so in your QA notes instead of changing it. Only the lead redefines characters.

## Writing a shot

```python
def s12(f):                        # f is a Frame
    cv = f.cv                      # draw in VIEW coords: (0,0)-(320,180); ~12 px margin exists outside
    cv.fill('#101018')
    t_room = song.word_time('Trapped in', 'room')   # exact sung onset of "room"
    k = f.t - t_room                                 # seconds since the word (negative before)
    ...
    cv.blit(render('gpt', make_pose('Q', eyes='wide')), x, ground_y, flip=True)  # flip -> faces left
    f.cam['x'], f.cam['y'] = 160, 90   # camera centre (view coords), may be fractional (sub-pixel pans)
    f.cam['zoom'] = 1.0                # >1 zooms in (nearest-neighbour). Use sparingly, ideally <= 1.15,
                                       # or integer 2.0 for a deliberate chunky punch-in
    f.shake = (dx, dy)                 # native px, short impacts only
    f.flash = 0..1                     # dithered white flash (impacts), f.fade = 0..1 to black
    f.lyrics = False                   # hide subtitles for this frame (rarely)

SHOTS = [Shot('12_chinese_room', 26.30, 0, s12), ...]   # end times are filled in from the next shot
```

Frame fields: `f.t` global seconds, `f.lt` seconds since the shot started, `f.u` 0..1 through the shot,
`f.dur`, `f.step(fps)` integer drawing index for authored animation at `fps`.

Timing: **every lyric event uses `song.word_time`** (or `song.beat`/`song.bar` for musical hits). Never hard-code
a guessed time. Cuts are already set in the storyboard; keep the shot names and start times you are given.

## Characters

```python
from art.body import render, make_pose
from art import poses as PO
p = make_pose('Q', eyes='open', mouth='none')   # views F (front), Q (3/4 right), P (profile right), B (back)
p['arm_f'] = [(5,-50), (11,-51), (17,-53)]      # shoulder, elbow, hand in sprite px (origin = ground point, y up = negative)
p['arms_front'] = True                          # draw the far arm in front of the body (reaching/pointing)
spr = render('claude', p)                       # cached Sprite; blit with its anchor on the ground line
```

* The sprites are about 76 px tall (ground to hair top). Anchor = the ground point between the feet.
* Eyes: open calm wide closed happy worried side dot down sharp (ChatGPT only) blank. Mouths: none small flat
  smile open o shout frown wavy.
* Useful pose keys: `bob` (px, positive = crouch the upper body down), `lean`, `hx/hy` (head offset), `hair`
  (sway px; negative streams left/back), `tail` (ChatGPT, list of 6 control points), `sit=True` (then give
  leg_n/leg_f with horizontal thighs), `skirt`, `coat`.
* Ready-made: `PO.run(i, who)` (8 drawings), `PO.walk(i, who)`, `PO.point`, `PO.plead`, `PO.think`, `PO.surprise`,
  `PO.reach_up`, `PO.wave(i)`, `PO.bow(0|1|2)`, `PO.fall(i)`. Drive with `f.step(10..12)` so drawings are held
  (pixel animation), never interpolated.
* Close-ups: `bust(who, 'Q', eyes, mouth, pose_key=(('arms_front', True), ('arm_f', ((5,-50),(10,-52),(14,-56)))), bottom=-20)`
  returns a 2x Sprite anchored at the neck. The head spans about 52 px above the anchor and the bust about 2*(-54-bottom)
  px below. For a medium close-up, put the neck at y of about 110-125.
* Extreme close-up eyes: `draw_eye` (see ch01 s02/s03).
* The kid: `kid('stand'|'wave'|'wave2'|'clap'|'up'|'sit')` (about 21 px tall). Townsfolk: `folk(seed, pose, frame)` (about 13 px).

If a pose looks broken (limbs through the body, a wrong facing), **change the shot** (closer bust, silhouette, back
view, a prop, cutaway) rather than forcing it.

## Pixel rules (non-negotiable)

* Hard edges only. No blur, no anti-aliasing, no alpha blending, no gradients except ordered dither (`dgrad`, `dfill`, `dither_overlay`).
* Limited palettes: pick colours from `art/palette.py` ramps or a few scene-specific hexes. No neon soup, no glow blur.
* Backgrounds serve the focal action: lower contrast and fewer details than the characters.
* One focal action per shot that reads in under a second. Something must happen in every shot.
* Text in the world (signs, labels) uses the bitmap fonts: `cv.text(s, x, y, col, font='3'|'5')` or `text_big(cv, s, x, y, col, scale)`.
* Characters animate at 8-15 drawings/s via `f.step`; camera, particles and effects may move every frame (60 fps).

## Performance

A native frame should take under about 60 ms. Cache static layers: build them once in an
`@functools.lru_cache` function that returns an RGBA numpy array, then `cv.blit(arr, x, y)`. Don't loop in
Python over every pixel of the screen per frame (numpy is fine).

## QA loop (do this for every shot)

Run from `src/`:

```
python3 render.py shots --only 12,13 --out ../qa/contact      # 5 frames per shot -> qa/contact/<shot>.png
python3 render.py strip 26.3:28.0 --every 4 --cols 8 --out ../qa/strip_12.png   # motion check
python3 render.py sheet 26.4,27.0,27.6 --k 2 --out ../qa/check.png              # half-res stills (closer look)
```

Open the PNGs with the Read tool and actually look at them. Ask: does the lyric read? Is there one clear focal
action? Are both characters on-model (see `qa/identity_sheet.png`)? Is anything ugly? Fix, re-render, repeat.
Then write 5-10 lines of notes to `qa/notes/<chapter>.md` (what each shot does, known compromises).

Do not render the full video, do not run `frames`/`encode`, and do not commit. The lead integrates.
