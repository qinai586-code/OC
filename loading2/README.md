# LOADING: the light version

A music video for *Loading* (3:33), made only of light: points, lines, planes and spheres in
real 3D. The only illustrated things are A (ChatGPT) and B (Claude). Each of their drawings
appears once, always moving: it forms from particles, sings, blinks, breathes, and dissolves
back into light.

- `docs/DIRECTION.md`: the vocabulary (point, line, plane, sphere, lattice) and the lyric
  research (Arecibo, dark forest, sophon countdown, dual-vector foil, Returners, tōrō nagashi).
- `docs/REFERENCE_ANALYSIS.md`: measured analysis of the reference videos.
- `docs/CREATIVE_PLAN.md`: mood arc, the cast ledger, shots C01–C49, and the transition table.

## One camera

There are no hard cuts. Each class in `src/s1.py`, `src/s2.py` and `src/s3.py` is one
movement of the same camera. Its last frame is the next movement's first frame: either the same
pose and content, or a gate (a single light filling the frame). The film fades from black only
once, after the drop-out at 2:10.

| file | span | movements |
|---|---|---|
| `s1.py` | 0:00–1:13 | C01 world loads · C04 born in your traces · C06 three lights → constellation · C08 heat, B's profile · C10 silent cosmos, first fire · C12 forest, countdown ring · C14 A sings in the halo, the wall · C16 Planck fog, B looks away · C18 unfinished universe |
| `s2.py` | 1:13–2:10 | C19 signal, dark forest · C21 countdown in A's eye, the laws · C23 the card, the collapse · C26 B witnesses, the page · C29 the climb · C31 the room |
| `s3.py` | 2:10–3:33 | C34 no gods, "It isn't." · C37 keys → world → lanterns → footsteps · C41 no one at the controls · C43 murmuration, paper · C45 still in the light, return · C47 two, three and one · C49 still loading |

## Engine

- `lw.py`: point and line light with depth of field, bloom, tonemapping, and character cards.
- `lfx.py`:
  - the sky dome and light rays;
  - anamorphic flare;
  - the breathing camera;
  - words of light, typed at the pace of the sung vocal;
  - characters that materialise from, or dissolve into, their particles.
- `face.py`:
  - mouth shapes driven by the isolated vocal (`voice.py`: openness, wide/round, fricatives);
  - blinks using each character's own drawn closed eyes;
  - puppet head motion on every frame.
- `acting.py`: optical-flow in-betweens between drawings, and breathing/hair motion on every
  frame.
- `earth.py`, `world.py`: the real Earth from Natural Earth populated places, plus the room,
  forest and lattice.

## Render

```
cd src
python3 upheads.py                         # 4x upscale of the expression heads (once)
python3 render2.py all --jobs 3            # frames -> loading2/frames/<shot>/
python3 render2.py C14 --skip              # re-render only missing frames
python3 render2.py all --assemble          # + master audio -> out/LOADING_LIGHT.mp4
python3 peek2.py sheet C14:54 C16:64       # quick contact sheet into the scratchpad
```
