"""Opening 2.50-9.00 (frames 60-215), round 2.
- frames <= 86: v6, untouched (no reframing, so no exposed border)
- frames 87-179: chroma-repaired Seedance rear shot, src f0-f92 at original speed (src = k - 87), registered once to
  v6 f86 (affine, ECC) so the cut-in lands on the same composition; afterwards only v6's own push-in (zoom in about
  PUSH_C, 5.45-7.5) is applied, which never exposes a border. The approved light is drawn with v6's exact formula.
- the rear shot ends on src f92, where A's fingertips leave the ledge (cut on the start of the action; the lift
  itself is elided: S1 opens with the palm up)
- frames >= 180: v6 (approved S1), untouched"""
import sys, numpy as np, cv2
sys.path.insert(0, '/home/user/OC/loading2/rev3/tools')
import opening_ink as OI
from yuv import load
P = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
V6 = P + '/v6/cache/f%04d.png'
OUT = P + '/m27/op/f%04d.png'
CUT, LAST_SRC = 87, 92
Y, U, V = load('dec/Opening_rear_rep.yuv')
def rgb(i):
    yuv = np.concatenate([Y[i].reshape(-1), U[i].reshape(-1), V[i].reshape(-1)]).reshape(1080, 1280)
    return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420).astype(np.float32)
ref = cv2.cvtColor(cv2.imread(V6 % (CUT - 1)), cv2.COLOR_BGR2GRAY).astype(np.float32)
A = np.eye(2, 3, dtype=np.float32)
cc, A = cv2.findTransformECC(ref, Y[0].astype(np.float32), A, cv2.MOTION_AFFINE,
                             (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-7), None, 5)
A3 = np.vstack([A, [0, 0, 1]]).astype(np.float64)                      # output (v6 framing) -> source coords
corners = np.array([[0, 0, 1], [1279, 0, 1], [0, 719, 1], [1279, 719, 1]], np.float64)
src_c = (A3 @ corners.T).T
print('ECC cc %.4f' % cc, 'A', np.round(A, 4).tolist())
print('output corners in source coords:', np.round(src_c[:, :2], 1).tolist())
# smallest extra zoom about the frame centre that keeps every output pixel inside the source
z0 = 1.0
while True:
    Z = np.array([[1 / z0, 0, 640 * (1 - 1 / z0)], [0, 1 / z0, 360 * (1 - 1 / z0)], [0, 0, 1]])
    s = (A3 @ Z @ corners.T).T
    if s[:, 0].min() >= 0 and s[:, 0].max() <= 1279 and s[:, 1].min() >= 0 and s[:, 1].max() <= 719:
        break
    z0 += 0.0005
print('extra zoom to stay inside the source: %.4f' % z0)
OI.PROF = OI.glow_profile()
op = OI.Opening()
pc = OI.PUSH_C
zc = OI.push_in(CUT / 24)[1]
oob_max = 0
for k in range(60, 216):
    t = k / 24
    if CUT <= k <= 179:
        zf = OI.push_in(t)[1] / zc                                       # v6's foreground push, relative to the cut
        Zk = np.array([[1 / zf, 0, pc[0] * (1 - 1 / zf)], [0, 1 / zf, pc[1] * (1 - 1 / zf)], [0, 0, 1]])
        Z0 = np.array([[1 / z0, 0, 640 * (1 - 1 / z0)], [0, 1 / z0, 360 * (1 - 1 / z0)], [0, 0, 1]])
        Mk = (A3 @ Z0 @ Zk)[:2].astype(np.float32)
        sc = (Mk.astype(np.float64) @ corners.T).T
        oob_max = max(oob_max, -sc[:, 0].min(), sc[:, 0].max() - 1279, -sc[:, 1].min(), sc[:, 1].max() - 719)
        img = cv2.warpAffine(rgb(k - CUT), Mk, (1280, 720), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 0, 255))   # magenta would show any gap
        cam = OI.camera(t)
        _, end_xy = op.lights(np.zeros((720, 1280, 3), np.float32), cam, t)
        p, s_, it = OI.light_path(t, end_xy)
        if it > 0:
            zb = OI.push_in(t)[0]
            img = OI.glow(img, OI.PUSH_C + (p - OI.PUSH_C) * zb, s_ * zb, it)
    else:
        img = cv2.imread(V6 % k).astype(np.float32)
    cv2.imwrite(OUT % k, np.clip(img, 0, 255).astype(np.uint8))
print('max out-of-bounds over the shot (px, <=0 means none): %.2f' % oob_max)
