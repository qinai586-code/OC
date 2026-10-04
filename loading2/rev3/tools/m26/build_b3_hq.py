"""B3 (819-861), clarity round: the accepted section (chroma-repaired source f42-84, nothing else applied), decoded with
yuv.hq_bgr instead of OpenCV's 2x2-replicated chroma."""
import numpy as np, cv2
from yuv import load, hq_bgr
P = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
Y, U, V = load('dec/B3_eyeclosure_rep.yuv')
for k in range(819, 862):
    cv2.imwrite(P + '/v8/op/f%04d.png' % k, np.clip(np.round(hq_bgr(Y, U, V, k - 819 + 42)), 0, 255).astype(np.uint8))
print('B3 819-861 written')
