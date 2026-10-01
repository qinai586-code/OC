"""Render specific times of a shot into one review image.
  python3 peek.py S04 32.8 35.8 [--w 1440] [--crop x0 y0 x1 y1] [--out name]"""
import argparse
from common import *
import render as R

ap = argparse.ArgumentParser()
ap.add_argument('shot')
ap.add_argument('times', type=float, nargs='+')
ap.add_argument('--w', type=int, default=1280)
ap.add_argument('--crop', type=int, nargs=4, default=None)
ap.add_argument('--out', default='peek')
ap.add_argument('--cols', type=int, default=1)
a = ap.parse_args()
reg = R.registry()
s = reg[a.shot]()
s.setup()
ims = []
for t in a.times:
    im = np.clip(s.render(t), 0, 1)
    if a.crop:
        x0, y0, x1, y1 = a.crop
        im = im[y0:y1, x0:x1]
    h = int(im.shape[0] * a.w / im.shape[1])
    im = cv2.resize(im, (a.w, h), interpolation=cv2.INTER_AREA)
    im = (im * 255).astype(np.uint8).copy()
    cv2.putText(im, f'{a.shot} {t:.2f}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)
    im = im.astype(np.float32) / 255
    ims.append(im)
while len(ims) % a.cols:
    ims.append(np.zeros_like(ims[0]))
rows = [np.hstack(ims[i:i + a.cols]) for i in range(0, len(ims), a.cols)]
out = os.path.join(SCRATCH, a.out + '.jpg')
imwrite(out, np.vstack(rows))
print(out)
