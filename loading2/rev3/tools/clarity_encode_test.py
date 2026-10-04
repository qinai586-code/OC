"""final-encode test on frames 84-329 (3.5-13.75 s) of the v8 frame set: bitrate, ROI fidelity and level bias vs the PNGs."""
import os, sys, subprocess, json, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clarity_metrics import fine, psnr, chroma_fine
S = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
def src(f):
    p = S + '/v8/op/f%04d.png' % f
    return p if os.path.exists(p) else S + '/v7/cache/f%04d.png' % f
F0, F1 = 84, 330
ACC = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:out_range=tv:out_color_matrix=bt601'
variants = {
    'A v7 recipe: crf18 medium, default conversion': ([], ['-crf', '18', '-preset', 'medium']),
    'B crf18 medium, accurate conversion': (['-vf', ACC], ['-crf', '18', '-preset', 'medium']),
    'C crf14 slow, accurate': (['-vf', ACC], ['-crf', '14', '-preset', 'slow']),
    'D crf12 slow aq3, accurate': (['-vf', ACC], ['-crf', '12', '-preset', 'slow', '-x264-params', 'aq-mode=3']),
    'E crf10 slow aq3, accurate': (['-vf', ACC], ['-crf', '10', '-preset', 'slow', '-x264-params', 'aq-mode=3']),
}
probe = {86: {'A_horns_hair': (415, 330, 545, 470), 'B_hair_edge': (800, 380, 900, 560), 'railing': (880, 612, 1200, 700)},
         120: {'A_horns_hair': (415, 330, 545, 470), 'B_hair_edge': (800, 380, 900, 560), 'cloth_hands': (560, 590, 760, 660)},
         216: {'eye': (405, 240, 465, 280), 'horn_hair': (395, 50, 505, 160), 'profile': (455, 255, 515, 350), 'cloth': (290, 370, 480, 470)},
         300: {'whole': (0, 0, 1280, 720)}}
ref = {f: cv2.imread(src(f)).astype(np.float32) for f in probe}
DEC = 'scale=flags=accurate_rnd+full_chroma_int+lanczos:in_range=tv:in_color_matrix=bt601'
res = {}
for name, (vf, x) in variants.items():
    out = S + '/enc/t_%s.mp4' % name[0]
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1280x720', '-r', '24', '-i', '-']
                          + vf + ['-c:v', 'libx264'] + x + ['-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(F0, F1):
        ff.stdin.write(cv2.imread(src(f)).tobytes())
    ff.stdin.close(); ff.wait()
    kbps = os.path.getsize(out) * 8 / ((F1 - F0) / 24) / 1000
    d = {'kbps': round(kbps)}
    for f, rois in probe.items():
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', out, '-vf', DEC + ',select=eq(n\\,%d)' % (f - F0), '-vsync', '0',
                                       '-frames:v', '1', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'])
        im = np.frombuffer(raw, np.uint8).reshape(720, 1280, 3).astype(np.float32)
        d[f] = {r: dict(psnr=round(psnr(im, ref[f], b), 2), fine=round(fine(im, b) / fine(ref[f], b), 3),
                        chroma=round(chroma_fine(im, b) / max(chroma_fine(ref[f], b), 1e-6), 3)) for r, b in rois.items()}
        d[f]['bias'] = round(float((im - ref[f]).mean()), 2)
    res[name] = d
    print(name, d['kbps'], 'kb/s')
    for f in probe:
        print('   f%d bias %+.2f  ' % (f, d[f]['bias']) + '  '.join('%s psnr %.1f fine %.3f chroma %.3f' % (r, v['psnr'], v['fine'], v['chroma'])
                                                          for r, v in d[f].items() if r != 'bias'))
json.dump(res, open(S + '/clar/enc_test.json', 'w'), indent=1)
