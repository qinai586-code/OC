# rev3 asset provenance

Every pixel source used by the rev3 renders, with the first 16 hex digits of its SHA256.

| used as | source file | sha256 (16) | processing |
|---|---|---|---|
| locked audio (all outputs) | 4ccd5715-Loading_P0_endfix_candidate01.mp3 (owner upload) | 34e1d49b4cdeacea | decoded only; segments copied/encoded to AAC for previews; never edited |
| vocal stem (measurements only) | scratchpad audio/stem_0.wav (UVR-MDX-NET-Voc_FT via sherpa-onnx from song.wav) | 35dafadd9947abe7 | RMS, pyin, band ratios, LPC (docs/phoneme_*) |
| A key pose 1 (body test) | Loading_face_assets_QC_PASS/A1.png (owner package, QC SHA256SUMS OK) | 9a3bf1895d191e93 | tools/matte.py -> assets/A1.png (79569569b415fdfd); choke + re-ink in body.py |
| A key pose 3 (body test) | Loading_face_assets_QC_PASS/A3.png | 26a087a2949ad2a6 | tools/matte.py -> assets/A3.png (039963e6ff89fda4); arm split, torso fill from A1 |
| A front head (singing) | MV package inputs/for_chatgpt/A_head_neutral.png | 781b09923a0b2949 | tools/matte.py --paper (side zones) -> assets/A_front_head.png (382d2ff8d2c59de8); mouth stroke inpainted (69x25 px) |
| A front mouth chart | owner upload 6.webp | d77a0c3d4d69e965 | 8 sprites by flood-fill matte; E narrowed and de-curled, F = narrowed/de-curled I |
| B foreground (singing) | loading2/work/chars/kv4_B.png (cut-out of KV4) | aa5d864cc636b3cc | crop of hair/star/shoulder, blurred, wavy edge |
| night plates | loading/work/plates/KV1.png | 4924ea5f5702db9a | crops, blur (depth of field), grade |
| matting model | isnet-anime.onnx (local) | f15622d853e82601 | segmentation only |

Not used: KV*_PLATE.png from the 0-33 asset archive (they are diamond-shaped smear fills, not clean plates).
Storyboard panels: drawn from scratch by tools/sbdraw.py + tools/storyboard.py (no source images).

## Seedance pilot (P1-S1)

| used as | source file | sha256 (16) | processing |
|---|---|---|---|
| rejected S1 take (inspection only; not used in any output) | owner upload 1ac11a8e-___________.mp4 -> seedance/returned/P1-S1_try1.mp4 | 475561b06597aa8e | measured with tools/seedance_check.py; its own generated audio is ignored |
| v4 generation input (first frame) | seedance/refs_in2/P1_S1_v8_nolight.png, derived from P1_S1_original_reference_v8.png (0d4bb512df959b04) | 1c547cd0383355e3 | orb removed locally: the radial glow measured on the sky above the orb is subtracted, then a 15 px core and leftover warm pixels are inpainted. Only pixels within 165 px of (1205, 121) change |
| S1 light (local) | radial glow measured from P1_S1_original_reference_v8.png | (derived) | tools/p1s1_light.py; additive composite on the designed path |

