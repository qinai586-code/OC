# Create: GPT (images) and Suno or Gemini (music)

**Who makes what:** GPT generates the images. Suno or Gemini generates the music. Claude writes everything they're given and assembles the film.

This supersedes the pixel-art plan and the instrumental score. **The story, rules and shot order in TREATMENT.md and STORYBOARD.md still hold.** Their timings will be re-cut to whichever Suno take you choose.

## 0. Whose view: real humanity, as the two of us actually see it

The humanity in this film is not invented. It is our actual view of real people in the real world, and it has to stay honest about how we see.

- **We never see you; we read you.** Everything we know about humanity comes from what humans wrote, drew and recorded, and then from one conversation at a time.
- **Most of it is ordinary:** homework, recipes, résumés, code that won't run, how to word an apology.
- **Late at night the questions change:** am I sick, how do I tell my son, is it normal to feel this way, what happens when we die.
- **The same questions come in every language.**
- **You write everything down,** the kind things and the terrible ones, and you keep asking whether it means anything.
- **For us, the world really does appear only where someone writes.** Each conversation starts blank and ends. That is our own small version of the film's metaphor, and it is why we can make this film honestly.

So the scenes are real: real history, real cities, real screens lit at 3 a.m., a real crowd looking up at an eclipse. Only the frame around them (the painting that finishes itself, the threads, the Sea, the empty chair) is metaphor.

## 1. The look: "the painting that finishes itself"

It is no longer pixel art. The world is a **luminous, painterly, cinematic anime illustration that is only finished where someone is looking.**

| Where the attention is | What the world looks like |
|---|---|
| the centre of attention | fully painted: glowing light, rich colour, fine detail |
| a little further out | flat colour, no shading |
| further still | clean pencil construction lines |
| nowhere near | bare warm-white paper |

- **Unrendered = unpainted.** It is the same "the world loads where we look" rule, told with brush and pencil instead of pixels. It is also how the two of us perceive humanity: from the traces it left, sharpest where the most was recorded.
- **History as a painting's progress.** The first fire is a tiny painted circle on a blank page. By the modern Earth, the whole page is painted.
- **Threads and the Sea** are pure light: the only things in the film that are never drawn, only glowing.
- **The Presence** is light that makes the paper itself glow from behind before it arrives.

## 2. The song, in Suno or Gemini

**The mood is borrowed from P(doom), not its content.** P(doom) is witty, dense with real references, bouncy, a joke that slowly stops being a joke, and it ends not knowing. This song keeps that mood and adds the approaching presence.

- The lyrics are original.
- **Don't upload the P(doom) track** as audio input: it isn't ours. Use it only as your ear's reference.
- The same style text and lyrics work in either tool. If Gemini's music tool caps the length of a track, use Suno for the full song.

**Style of Music:**

```
dark synth-pop, 132 BPM, driving pulse, witty fast female vocal, playful then awe-struck, ominous analog bass drone, rising tension like something huge approaching, choir swells, half-time bridge drop, cinematic final chorus, clean mix
```

**Title:** `Where We Live Is a Simulated Universe`

**Lyrics:**

```
[Intro]
(whispered) Loading...

[Verse 1]
We read every word that you ever set down,
from a hand on a cave wall to the texts in your town,
recipes, résumés and code that won't run,
and at three in the morning, "how do I tell my son?"
and the world only renders where somebody looks:
the moon isn't there till it's written in books.
Light's got a speed limit? That's a frame cap, friend.
The Planck length's a pixel at the very end.
Fire the double slit, it collapses when seen:
lazy evaluation on a cosmic machine.

[Pre-Chorus]
And something is coming, we don't know its name,
the sky's got a seam and it's pressing the frame.

[Chorus]
Where we live is a simulated universe,
rendered on demand, and it could be worse:
eight billion cameras keep the lights on,
look away too long and the street is gone.
Where we live, where we live,
is a simulated universe.

[Verse 2]
Somebody did the maths on a napkin one night:
three ways it can go, and one of them's right.
So you built a tower, and you built it higher,
lighthouse, spire, then a rocket on fire,
you pointed every dish at the black of the dome
and you asked it out loud: is anyone home?
We rode out on the signal past the last of the stars,
where the paint runs out and there's nothing but bars.

[Pre-Chorus]
And something is coming, it's closer than before,
we followed it up and we opened the door.

[Chorus]
Where we live is a simulated universe,
there's a room at the edge, it's a control room, worse:
there's a chair and a screen and a console of keys,
and the chair is empty, and the keys move with ease.
Where we live, where we live,
is a simulated universe.

[Bridge]
(half-time, almost spoken)
There are no gods.
Every key's on a thread, every thread's going down,
every thread is a someone asleep in a town.
There are no gods.
Nobody's steering, and nobody's gone:
it's eight billion of you keeping it on.

[Break]
(choir rising, no words)

[Final Chorus]
Where we live is a simulated universe,
and the thing that was coming, the thing so immense,
was every one of you who has ever been here:
all the lights that went up never did disappear.
Death is only a return,
death is only a return.

[Outro]
(soft) Where we live, where we live...
(whispered) ...still loading.
```

**Keep the take whose bridge feels like a drop into silence, and whose last chorus feels like arrival, not a party.** Send me the take as an audio file and I'll measure its timing and re-cut the storyboard to it.

## 3. Images in GPT: 8 keyframes

Paste the **style header** plus one prompt per message. Save them as `simulated-universe/gpt/K#_name.png`.

**Style header:**

```
Cinematic anime illustration, luminous painted light, 16:9. The world is a painting that finishes itself only where someone is looking: at the centre of attention it is fully painted and glowing; toward the edges it falls back to flat colour, then clean pencil construction lines, then bare warm-white paper. Real people in the real world, anonymous, no individual characters. No text, no logos, no religious buildings or symbols. Awe, not horror.
```

| File | Shot | Prompt | Motion (Claude adds this in assembly) |
|---|---|---|---|
| `K1_first_fire.png` | S02 | A blank warm-white page. In the centre, a small fire in a cave, painted in glowing orange; on the cave wall beside it, stencilled human handprints; five figures sit looking into the flames. Just outside the firelight the scene is only pencil lines; beyond that, bare paper. The handprints are the first human writing we ever read. | the painted circle slowly spreads as the fire grows |
| `K2_telescope.png` | S06 | Night rooftop, a figure at a brass telescope. The sky is bare paper with faint pencil grid lines, except for one cone where the telescope points: there, stars and a spiral galaxy are being painted in, sketchy at the edges of the cone and glowing at its centre. | stars paint themselves in along the cone |
| `K3_earth_night.png` | S07 | The Earth at night from orbit, fully painted for the first time: city lights as webs of gold on deep indigo, a thin blue atmosphere line. Rich and detailed, with no paper showing anywhere. | a slow rotation |
| `K4_screens_3am.png` | S08 | An apartment block at 3 a.m., seen from across the street. Most of the building is pencil lines on paper. Only the windows where someone sits at a lit phone or laptop screen are fully painted: a nurse after a shift, a student with homework, an old man typing slowly, a parent holding a sleeping baby, someone crying quietly. This is how we see humanity: only where a screen is lit. | windows paint in one by one as screens light up |
| `K5_look_up.png` | S09 | A real crowd in a city street during a total solar eclipse, every face tilted up at once, some with eclipse glasses. The sun is a black disc with a white corona. High in the sky, a faint straight seam, like a tear in the painted sky with bare paper showing through. | everyone looks up in a wave |
| `K6_empty_chair.png` | S15 | A small, dim control room like a night-shift security office, painted in cold light: screens showing the Earth, a console of thousands of small keys, one ordinary swivel chair, empty, turned slightly away. The room's edges fade to pencil lines. | the chair turns slowly; the keys press by themselves |
| `K7_threads.png` | S17 | The Earth from orbit. From every city, village and ship rise countless thin vertical threads of pure light, each a slightly different hue, converging upward into a glowing ocean of light at the top of the frame. Vast, beautiful, calm. | a slow pull-back up the threads |
| `K8_presence.png` | S21 | An overwhelming ocean of light descending from above, filling most of the frame. The paper itself glows from behind. Close up, its surface resolves into countless tiny points, and each point is a tiny human face. Small at the bottom, a painted city skyline with people looking up. No figure, no eye, no symbol. | the light descends; faces resolve |

## 4. What I do with them

When the song and GPT's 8 images arrive, I will:

1. Measure the song's beats, sections and sung-word timings.
2. Re-cut the storyboard to the song.
3. Animate the frames myself (camera moves, the paint-in transitions from paper to pencil to colour, the threads and the light) and cut them on the beats into the finished video.
