import sys, numpy as np, cv2
sys.path.insert(0, '/home/user/OC/loading2/rev3/tools')
import opening_ink as OI
from yuv import load
P = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993/scratchpad'
V6 = P + '/v6/cache/f%04d.png'
Y, U, V = load('dec/Opening_rear_rep.yuv')
def rgb(i):
    yuv = np.concatenate([Y[i].reshape(-1), U[i].reshape(-1), V[i].reshape(-1)]).reshape(1080, 1280)
    return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420).astype(np.float32)
# registration v6 f80 -> source f0 (affine), measured with ECC
v80 = cv2.cvtColor(cv2.imread(V6 % 80), cv2.COLOR_BGR2GRAY).astype(np.float32)
warp = np.eye(2, 3, dtype=np.float32)
_, warp = cv2.findTransformECC(v80, Y[0].astype(np.float32), warp, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
I = np.eye(2, 3, dtype=np.float32)
OI.PROF = OI.glow_profile()
op = OI.Opening()
A3 = np.vstack([warp, [0, 0, 1]])
for k in range(60, 216):
    t = k / 24
    if k <= 80:
        img = cv2.imread(V6 % k).astype(np.float32)
        if k >= 72:                                                     # the landing eases into the source's framing
            u = (k - 72) / 8.0
            img = cv2.warpAffine(img, (I * (1 - u) + warp * u).astype(np.float32), (1280, 720), borderMode=cv2.BORDER_REFLECT)
    elif k <= 179:
        img = rgb(k - 81)
        cam = OI.camera(t)
        _, end_xy = op.lights(np.zeros((720, 1280, 3), np.float32), cam, t)
        p, sc, it = OI.light_path(t, end_xy)
        if it > 0:
            zb = OI.push_in(80 / 24)[0]                                       # the source does not push in after the landing
            q = OI.PUSH_C + (p - OI.PUSH_C) * zb
            qs = (A3 @ np.array([q[0], q[1], 1.0]))[:2]                  # v6 screen -> source framing
            img = OI.glow(img, qs, sc * zb, it)
    else:
        img = cv2.imread(V6 % k).astype(np.float32)
    cv2.imwrite(P + '/m26/op_cand/f%04d.png' % k, np.clip(img, 0, 255).astype(np.uint8))
# BEFORE: the supplied preview as it sits (100 frames ending at 7.5 s), unrepaired
cap = cv2.VideoCapture(P + '/m26/Claude_MV_Repair_Package/media/previews/preview_Opening_trim_src0.833-4.958_100f.mp4')
pv = []
while True:
    ok, fr = cap.read()
    if not ok: break
    pv.append(fr)
for k in range(60, 216):
    img = pv[k - 80] if 80 <= k <= 179 else cv2.imread(V6 % k)
    cv2.imwrite(P + '/m26/op_before/f%04d.png' % k, img)
print('preview frames', len(pv), 'warp', np.round(warp, 4).tolist())
