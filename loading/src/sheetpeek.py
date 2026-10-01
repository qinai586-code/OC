"""Render (shot, time) pairs into one small contact sheet: python3 sheetpeek.py out S31:131.5 S32:139 ..."""
import sys
from common import *
import render as R
reg = R.registry()
ims = []
cache = {}
for arg in sys.argv[2:]:
    n, t = arg.split(':')
    if n not in cache:
        cache[n] = reg[n]()
        cache[n].setup()
    try:
        im = np.clip(cache[n].render(float(t)), 0, 1)
    except Exception as e:
        import traceback; traceback.print_exc()
        im = np.zeros((H_OUT, W_OUT, 3), np.float32)
    im = (cv2.resize(im, (480, 270), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8).copy()
    cv2.putText(im, arg, (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    ims.append(im)
while len(ims) % 4:
    ims.append(np.zeros_like(ims[0]))
rows = [np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)]
cv2.imwrite(os.path.join(SCRATCH, sys.argv[1] + '.jpg'), np.vstack(rows)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 85])
print('ok')
