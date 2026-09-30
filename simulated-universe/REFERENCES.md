# Visual references: the opening (0:00–0:21) and beyond

Research for the brief "3D, dimensionality, particles, time, space", mapped to what we
actually use. The test render is `paint/opening.py`; the character cutouts are made by
`paint/characters.py`.

| Idea | Reference | Used in the opening as |
|---|---|---|
| Dimensional collapse (3 → 2 → 1) | *The Three-Body Problem*, dual-vector foil ([wiki](https://three-body-problem.fandom.com/wiki/Dual-vector_foil), [VFX Voice on the Netflix series](https://vfxvoice.com/seizing-the-opportunity-to-visualize-the-3-body-problem/)) | "Three / two / one": the galaxy loses thickness, then height, then becomes a line. A sheen sweeps the plane as it flattens. |
| Particles as living pigment | Refik Anadol, *Machine Hallucinations* ([Sphere](https://refikanadol.com/works/machine-hallucinations-sphere/), [Nature Dreams](https://refikanadol.com/works/machine-hallucinations-nature-dreams/)) | "Loading": particles from the line stream into the two silhouettes and settle as gold before the paint arrives. |
| 2D and 3D in one frame | *Spider-Verse* 2D FX ([Toon Boom](https://www.toonboom.com/behind-the-amazing-2dfx-in-spider-man-across-the-spider-verse)), 2.5D ([VFX Apprentice](https://www.vfxapprentice.com/blog/what-is-2-5d-animation-games)) | Hand-drawn characters on a flat page, set inside a 3D space with depth of field, parallax and a moving camera. |
| Time as a physical direction | *Interstellar*, the tesseract ([IndieWire](https://www.indiewire.com/features/general/inside-the-making-of-the-spectacular-tesseract-in-interstellar-189771/), [fxguide](https://www.fxguide.com/fxfeatured/interstellar-inside-the-black-art/)) | The silence at 13.4–14.45: story time stops while the camera keeps moving, and each ember's recent path hangs in the air as a filament. |
| Nonlinear time, meaning in shapes | *Arrival* logograms ([Wolfram blog](https://blog.wolfram.com/2017/01/31/analyzing-and-translating-an-alien-language-arrival-logograms-and-the-wolfram-language/)) | Held for the bridge and the convergence (circular, self-closing figures). Not used yet. |
| Flow fields | Curl noise ([al-ro](https://al-ro.github.io/projects/particles/), [Emil Dziewanowski](https://emildziewanowski.com/curl-noise/), [SideFX](https://www.sidefx.com/tutorials/curl-noise-flow/)) | Embers drift on layered sine flow. True curl noise is the planned upgrade. |
| Speed through space | Slit-scan and the *2001* Stargate ([RedShark](https://www.redsharknews.com/douglas-trumbull-and-how-slit-scan-changed-sfx), [Neil Oseman](https://neiloseman.com/slit-scan-and-the-legacy-of-douglas-trumbull/)) | Held for the chorus 1 entrance at 0:44. Not used yet. |
| Volumetric light on 2D drawings | *Klaus* ([80.lv](https://80.lv/articles/klaus-look-development-simulating-3d-effects-in-2d)) | The page is dark except for two pools of light on A and B. The rest of the paper stays unlit, where the painting has not finished itself. |
| Light as an actor | Makoto Shinkai ([canmom](https://canmom.art/films/animation-night/132-makoto-shinkai-2)) | The flash on the hit, the warm glow behind A that pulses on the tracked beats, and the constellations lighting up. |

## Opening beat map (master timing)

| Time (s) | Audio (measured or estimated) | Picture |
|---|---|---|
| 0.0–1.0 | Silence, then "Three" at about 1.0–1.8 | A galaxy core in the dark. Dust drifts past the lens. |
| 1.0–3.3 | "Three" | The galaxy ignites from the core outward. The camera pulls back and orbits. |
| 3.3–4.5 | "two" | The thickness collapses into a plane. The camera swings toward face-on. |
| 4.5–5.62 | "one" | The plane collapses into a line across the frame. |
| 5.62 | Bass hit | The line is the hinge of a sheet of paper that swings up. Flash, shake. The galaxy scatters. |
| about 6.3–7.55 | "Loading" | The camera pulls back to show the page floating in space. The line pours into two gold silhouettes. |
| 7.55 | Downbeat | Pencil, then flat colour, then paint. The lights come up on A and B. |
| 7.55–13.4 | Verse 1 (A) | Embers lift off the page into depth and brighten on the tracked beats. |
| 13.4–14.45 | Full silence | Time freezes (bullet time) and the embers' paths show as filaments. |
| 14.45–21 | Re-entry | The embers snap into constellations in front of and above the page. The camera cranes up. |

## Character cutouts

`characters.py` cuts both side views directly from `reference/sheet_*.webp`:

- A colour-and-connectivity background fill, with the line art used as a barrier.
- Explicit cuts that remove the neighbouring 3/4 view and the "SIDE" label.
- Peeling of the pale edge rim.

The older `assets/cut/*_side.png` files were cropped too tight: hair was cut off at the box edge, and they carried slivers of the neighbouring view and background. They are left untouched for the rig tools that still use them.
