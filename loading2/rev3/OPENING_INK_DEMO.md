# Opening demo: the stroke becomes the lived world (0:00–0:13.583)

| file | what it is |
|---|---|
| `tests/OPENING_INK_demo_720p.mp4` | the demo: 1280×720, 24 fps, 326 frames, on the unchanged locked master |
| `tests/OPENING_INK_demo_strip.jpg` | 15 frames, with song time |
| `tools/opening_ink.py` | the build (about 2 min on CPU) |

- **Generation:** none.
- **0–7.5:** new, made from KV1 and code.
- **7.500–13.583:** the approved light catch, decoded unchanged. The S2 masking leak you reported is untouched, as asked.

## The direction

**One idea, used for space, time and dimension:**
- **The trace:** a person's handwritten stroke is the first image.
- **Time:** night falls across the page like the Earth's terminator, and the wet ink beads into city lights.
- **Space:** the page tilts and curves into the night side of the Earth.
- **The light:** the stroke's last bead is the light A catches.

This sets up "We were born in your traces" before it is sung, without any text on screen. The hooked stroke is the persistent human mark from the design handoff, so the letter can carry it later.

**From the two reference videos:**
- **From V1:** open on a premise that isn't the main world; V1 opens on a boot screen.
- **From V2:**
  - change scale by transformation, not by cutting: a scene shrinks to a point; a wall folds into a floor;
  - the camera is fast between worlds and slow within one.
- **Here:** the camera moves only during the transformation, then eases to rest on the cluster. It does not push into a still portrait, and it adds no glow beyond the approved light.

| song (s) | what happens | scale / dimension |
|---|---|---|
| 0.000–0.232 | black (silence) | |
| 0.232–0.55 | out of black on the drone: lamplit paper, seen straight down | macro |
| 0.45–1.45 | a hooked stroke is written in blue-black ink, slowing into the curl | a line (1D) |
| 1.45–2.05 | a dusk edge crosses the page right to left; behind it the page is night, and the ink beads into warm lights | the page (2D); time passes |
| 1.90–3.344 | the camera pulls up about 6.8× and tilts 67°. The paper gives way to the night Earth, the surface curves, the horizon and sky appear, and the parapet and both girls rise into frame. The move lands on the first onset of the six-onset cluster | globe (3D), then a place with observers |
| 3.344–3.82 | the six onsets flash six lights along the stroke toward its end | |
| 3.82–6.70 | the last light lifts and rises above them | |
| 6.70–7.05 | it hangs | |
| 7.05–7.50 | it turns down toward A, into the approved descent | |
| 7.500–13.583 | approved S1–S3 | |

**How it lands on KV1:**
- The globe is a real sphere seen through a camera fitted to KV1's painted horizon: lens 1100 px, altitude 0.111 Earth radii, pitch 30.1°, maximum error 1.8 px.
- Its surface is KV1 itself, projected from that camera, so the final frame is KV1.
- Toward the horizon the globe hazes, as atmosphere does.
- The girls and parapet are KV1's own mattes. As the camera eases out after landing they shrink slightly more than the Earth, so the depth reads.

## Proxies in the demo

- **Paper and ink:** procedural; the stroke has no visible pen.
- **The Earth behind the girls and under the parapet:** filled locally (inpaint plus the plate's own cloud detail). It is visible for about half a second during the move.
- **Both girls:** still from 3.0 to 7.5. The cut at 7.5 therefore jumps from hands-on-stone to S1's raised hand. That is the main gap.
- **A's clip:** still on her right in KV1, which is not canon.

## Essential missing assets

1. **KV1 edit (ChatGPT, 1 file):** A's X clip moved to her left, and her half-up ribbon added. Nothing else changes.
2. **Clean Earth plate (ChatGPT edit of KV1, 1 file):** the same framing with both girls and the parapet removed, so the Earth continues behind them. It replaces my fill.
3. **Seated acting (Seedance, 5 s, from asset 1):** A looks up and lifts her right hand off the stone, palm up, by 7.5; B turns to her, then looks up. It is used from about 3.3 s to the cut at 7.5.

Everything else (paper, stroke, terminator, beads, globe, move, light) stays local.
