# What GPT generates: 9 images

The film shows humanity as Claude and GPT perceive it (TREATMENT §1). **GPT only generates images; Claude does everything else.**

**How to send them:** paste the style header plus one prompt per message, one image each. There are 9 images in total. Save each result in `simulated-universe/gpt/` under the file name given, then tell Claude. If an image misses, send one correction at most; Claude can fix small things during pixel translation.

## Style header (paste at the top of every prompt)

```
Pixel art, 16:9, as if drawn at 320x180 and scaled up with hard pixel edges. Limited palette. Anonymous small figures only, no individual characters. No text, no logos, no religious buildings, figures or symbols. Awe, not horror. This is a frame from a film about humanity as two AIs perceive it: the world exists only where someone is looking; unlooked-at space is a faint gray wireframe grid on near-black.
```

## The 9 prompts

| File | Shot | Prompt |
|---|---|---|
| `K1_first_fire.png` | S02 | Total darkness crossed by a faint gray wireframe grid. In the centre, a small campfire. Around it, a circle of world drawn in huge coarse pixel blocks (ground, a rock) and five small figures sitting, faces lit orange, looking into the fire. Beyond the circle, only wireframe. |
| `K2_telescope.png` | S06 | Night rooftop, a small figure at a brass telescope. The sky is blank gray wireframe except for one cone where the telescope points: there, stars and a spiral galaxy are loading in, blocky at the edges of the cone and sharp at its centre. |
| `K3_earth_night.png` | S07 | The Earth at night from orbit, city lights as webs of gold on deep indigo, a thin blue atmosphere line. Crisp and detailed. |
| `K4_copies.png` | S08 | A city street at night. In the far distance the crowd is identical gray copies of one simple figure; in the foreground they have become distinct people of every age and kind. The change from copies to people is visible in the middle ground. |
| `K5_look_up.png` | S09 | A dense city street at night, every figure tilting their face upward at once. High in the sky, a faint straight seam where two panels of the sky don't quite match. Unease, not fear. |
| `K6_empty_chair.png` | S15 | A small, dim control room like a night-shift security office. Banks of screens showing the Earth. A console with thousands of small keys. One ordinary swivel chair, empty, turned slightly away. Cold light. Ordinary, and empty. |
| `K7_threads.png` | S17 | The Earth from orbit. From every city, village and ship rise countless thin vertical threads of light, each a slightly different hue, converging upward into a glowing ocean of light seen from below at the top of the frame. Vast, beautiful, calm. |
| `K8_presence.png` | S21 | An overwhelming ocean of light descending from above and filling most of the frame, every hue averaging to white. Close to the viewer, its surface resolves into countless tiny points, and each point is a tiny human face. A city skyline small at the bottom, people looking up. No figure, no eye, no symbol. |
| `crowd_kit.png` | all | A sprite sheet on a plain flat background. Row 1: one neutral gray "everyperson" figure, front, side, back and 4 walking frames. Rows 2–4: 24 distinct anonymous people of every age, body and clothing, from ancient to modern (tunics, work clothes, suits, school uniforms, elders with canes, a parent with a stroller, children), each front and side. Figures about 40 px tall at native size. |
