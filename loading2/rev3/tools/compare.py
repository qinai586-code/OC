"""Before/after at matched track timestamps (rev3).

Left = v2 acceptance package, right = rev3, both at the same frame of the locked track:
  1. body test        7.50-12.50  (v2 TEST1 frames  vs rev3 body frames)
  2. singing close-up 52.42-56.29 (v2 TEST2 frames  vs rev3 singing frames)
  3. repetition fix   66.5-74.6   (v2 storyboard animatic vs rev3 drawn panels)
  4. repetition fix   145.8-158.5 (v2 storyboard animatic vs rev3 drawn panels)
Audio: the locked track at the same times. Output: rev3/tests/REV3_before_after.mp4
"""
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
L2 = os.path.dirname(R)
sys.path.insert(0, HERE)
AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
OLD_ANIM = os.path.join(L2, 'tests', 'STORYBOARD_ANIMATIC.mp4')
OUT = os.path.join(R, 'tests', 'REV3_before_after.mp4')
FPS = 24
CW, CH = 960, 540


def fit(img):
    return cv2.resize(img, (CW, CH), interpolation=cv2.INTER_AREA)


def png(d, f):
    p = os.path.join(d, '%05d.png' % f)
    return cv2.imread(p) if os.path.exists(p) else None


def label(img, txt, col):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (CW, 34), (15, 15, 18), -1)
    cv2.putText(out, txt, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, col, 1, cv2.LINE_AA)
    return out


def panel_at(t):
    import storyboard as sb
    for p in sb.PANELS:
        if int(round(p['t0'] * 24)) <= int(round(t * 24)) < int(round(p['t1'] * 24)):
            return p['id']
    return None


def main():
    cap = cv2.VideoCapture(OLD_ANIM)
    segs = [('BODY TEST', 180, 300, lambda f: png(os.path.join(L2, 'tests', 'test1_rig'), f), lambda f: png(os.path.join(R, 'work', 'body'), f),
             'v2 TEST1: rigid tilt of unchanged drawings', 'rev3: two drawn poses, nod, forearm, contact'),
            ('SINGING', 1258, 1351, lambda f: png(os.path.join(L2, 'tests', 'test2_sing'), f), lambda f: png(os.path.join(R, 'work', 'sing'), f),
             'v2 TEST2: card edges, grin, off-centre mouth', 'rev3: sound-matched, centred mouths, framed'),
            ('01:06-01:14', 1596, 1790, None, None, 'v2 animatic: one held wide', 'rev3 storyboard: 4 events'),
            ('02:25-02:38', 3499, 3804, None, None, 'v2 animatic: one held sketch', 'rev3 storyboard: 4 events')]
    panels = {}
    tmp_segs = []
    for name, f0, f1, old_fn, new_fn, lt, rt in segs:
        tmp = os.path.join(R, 'work', 'cmp_%s.mp4' % name.replace(' ', '_').replace(':', ''))
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (2 * CW, CH + 60), '-r', str(FPS),
                               '-i', '-', '-ss', '%.4f' % (f0 / FPS), '-t', '%.4f' % ((f1 - f0) / FPS), '-i', AUDIO, '-map', '0:v', '-map', '1:a',
                               '-c:v', 'libx264', '-crf', '22', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', tmp], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            t = f / FPS
            if old_fn is None:
                cap.set(cv2.CAP_PROP_POS_FRAMES, f)
                ok, old = cap.read()
                pid = panel_at(t)
                if pid not in panels:
                    panels[pid] = cv2.imread(os.path.join(R, 'work', 'panels', 'panel_%s.png' % pid.replace('.', '_')))
                new = panels[pid]
            else:
                old, new = old_fn(f), new_fn(f)
            old = label(fit(old), 'BEFORE  ' + lt, (120, 160, 255))
            new = label(fit(new), 'AFTER   ' + rt, (140, 230, 140))
            bar = np.full((60, 2 * CW, 3), 20, np.uint8)
            cv2.putText(bar, '%s   track time %d:%05.2f   frame %d   (same frame of the locked track on both sides)' % (name, int(t // 60), t % 60, f),
                        (14, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (235, 235, 235), 1, cv2.LINE_AA)
            fr = np.vstack([np.hstack([old, new]), bar])
            ff.stdin.write(fr.tobytes())
        ff.stdin.close()
        ff.wait()
        tmp_segs.append(tmp)
    lst = os.path.join(R, 'work', 'cmp_list.txt')
    open(lst, 'w').write(''.join("file '%s'\n" % s for s in tmp_segs))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', OUT], check=True)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
