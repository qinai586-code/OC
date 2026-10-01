# LOADING — music video

A complete music video for the locked master *Loading* (3:33), built on ChatGPT's asset pack
*simulated_universe 0–33*. Direction, extra material and the edit by Claude.

| Read | What it holds |
|---|---|
| [docs/DIRECTION.md](docs/DIRECTION.md) | the film in one sentence, the one universe, the four dimensional states, motif chains, attention rules, motion, camera/edit, satsuei rules, research notes |
| [docs/SONG_MAP.md](docs/SONG_MAP.md) | transcribed lyrics with timings, sections, breaths and silences |
| [docs/SHOTLIST.md](docs/SHOTLIST.md) | every shot with time, state, event, and what carries into the next shot |

## Rendering

The renderer is plain Python (NumPy + OpenCV); no GPU needed.

```
pip install numpy opencv-contrib-python-headless scipy pillow
cd loading/src
python3 prep_plates.py KV1 KV2 KV3 KV4 KV5 KV3b KV4b KV5a BG0a BG0b   # needs the upscaled plates
python3 prep_kv2.py && python3 prep_misc.py KV3 KV3b KV5 band:KV4
python3 render.py all --jobs 4          # frames -> loading/frames/<shot>/
python3 render.py all --assemble        # -> out/LOADING_MV.mp4 with the master audio
python3 peek.py S07 44.0 47.5           # render single times of one shot for review
```

The asset pack, the 2× anime upscale (Real-ESRGAN x4plus anime 6B), the character mattes
(isnet-anime) and the depth maps (Depth Anything V2) are produced outside the repo; paths are in
`src/common.py` (`LOADING_SCRATCH`).

| module | contents |
|---|---|
| `common.py` | IO, easing, noise, camera matrices |
| `dimension.py` | the four states: paper, pencil line art, flat cel, light masks, stroke order, wash timing |
| `engine.py` | plates and derived layers, multiplane/depth camera, in-betweening, hair sway |
| `fx.py` | satsuei: transmitted-light glow, diffusion, grain, paper tooth, point lights, lights on paper |
| `globe.py`, `proj.py` | the Earth as a sphere that unrolls into the flat map; pinhole camera, textured planes |
| `envs.py` | the procedurally painted forest and starfields |
| `room.py` | the room at the end of the light: a true-3D layout drawing with hidden lines |
| `lids.py` | B's eyelid states (lowered gaze, closed) drawn from the painted eye |
| `shots_a…f.py` | the 46 shots |
