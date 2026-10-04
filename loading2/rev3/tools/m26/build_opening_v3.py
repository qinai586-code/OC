"""Opening rear shot, frames 87-179 (3.625-7.458), clarity round. Content, timing, registration and light are those of
build_opening_v2 (round 2); only the pixel path changes:
  - decode: hq_bgr (cubic chroma at the measured siting, float) instead of OpenCV's 2x2-replicated chroma, 8-bit
  - warp: the one resample (registration to v6 f86 + 0.55% zoom + v6's push-in, composed into a single affine) uses
    Lanczos-4 instead of bicubic. The output never leaves the source (checked per frame), so the border mode is never
    used for any visible pixel.
Run from the scratchpad's m26 directory (dec/Opening_rear_rep.yuv)."""
import sys, numpy as np, cv2
sys.path.insert(0, '/home/user/OC/loading2/rev3/tools')
sys.path.insert(0, '/home/user/OC/loading2/rev3/tools/m26')
import opening_ink as OI
from yuv import load, hq_bgr
P = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
V6 = P + '/v6/cache/f%04d.png'
OUT = P + '/v8/op/f%04d.png'
CUT, LAST_SRC = 87, 92
Y, U, V = load('dec/Opening_rear_rep.yuv')
ref = cv2.cvtColor(cv2.imread(V6 % (CUT - 1)), cv2.COLOR_BGR2GRAY).astype(np.float32)
A = np.eye(2, 3, dtype=np.float32)
cc, A = cv2.findTransformECC(ref, Y[0].astype(np.float32), A, cv2.MOTION_AFFINE,
                             (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-7), None, 5)
A3 = np.vstack([A, [0, 0, 1]]).astype(np.float64)
corners = np.array([[0, 0, 1], [1279, 0, 1], [0, 719, 1], [1279, 719, 1]], np.float64)
print('ECC cc %.4f' % cc, 'A', np.round(A, 4).tolist())
z0 = 1.0
while True:
    Z = np.array([[1 / z0, 0, 640 * (1 - 1 / z0)], [0, 1 / z0, 360 * (1 - 1 / z0)], [0, 0, 1]])
    s = (A3 @ Z @ corners.T).T
    if s[:, 0].min() >= 0 and s[:, 0].max() <= 1279 and s[:, 1].min() >= 0 and s[:, 1].max() <= 719:
        break
    z0 += 0.0005
print('extra zoom %.4f' % z0)
OI.PROF = OI.glow_profile()
op = OI.Opening()
pc = OI.PUSH_C
zc = OI.push_in(CUT / 24)[1]
margin = []
for k in range(CUT, 180):
    t = k / 24
    zf = OI.push_in(t)[1] / zc
    Zk = np.array([[1 / zf, 0, pc[0] * (1 - 1 / zf)], [0, 1 / zf, pc[1] * (1 - 1 / zf)], [0, 0, 1]])
    Z0 = np.array([[1 / z0, 0, 640 * (1 - 1 / z0)], [0, 1 / z0, 360 * (1 - 1 / z0)], [0, 0, 1]])
    Mk = (A3 @ Z0 @ Zk)[:2].astype(np.float32)
    sc = (Mk.astype(np.float64) @ corners.T).T
    margin.append(min(sc[:, 0].min(), 1279 - sc[:, 0].max(), sc[:, 1].min(), 719 - sc[:, 1].max()))
    img = cv2.warpAffine(hq_bgr(Y, U, V, k - CUT), Mk, (1280, 720), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_REFLECT_101)
    cam = OI.camera(t)
    _, end_xy = op.lights(np.zeros((720, 1280, 3), np.float32), cam, t)
    p, s_, it = OI.light_path(t, end_xy)
    if it > 0:
        zb = OI.push_in(t)[0]
        img = OI.glow(img, OI.PUSH_C + (p - OI.PUSH_C) * zb, s_ * zb, it)
    cv2.imwrite(OUT % k, np.clip(np.round(img), 0, 255).astype(np.uint8))
print('smallest margin of the output corners inside the source over the shot: %.2f px' % min(margin))
