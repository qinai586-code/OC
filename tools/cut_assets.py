"""cut_assets.py: cut the approved model-sheet side views into rig layers (deterministic, re-runnable).

Sources (the only visual authority):
  reference/sheet_chatgpt.webp   ChatGPT model sheet (side view faces right; TAIL (SIDE) detail)
  reference/sheet_claude_b.webp  Claude model sheet "Claude ✦" (side view faces left)

Outputs (assets/cut/), all in each character's own texture space (= sheet pixels of the side-view crop):
  gpt_body.png   body + head (skinned to hip/chest/neck/head bones); near forearm removed and back-filled
  gpt_rear.png   rear hair (chain-skinned)          gpt_arm.png   near bell sleeve / forearm (elbow bone)
  gpt_collar.png the dropped coat band over the elbow (drawn over the arm)
  gpt_iris.png   iris sprite                         gpt_tail.png  tail from the TAIL (SIDE) detail, mirrored
  cl_body.png, cl_rear.png, cl_lock.png (side lock), cl_arm.png (near sleeve), cl_iris.png
Run: python3 tools/cut_assets.py
"""
import numpy as np, cv2
from PIL import Image

OUT = 'assets/cut/'

def cutout(src, box, tol=10):
    im = np.array(Image.open(src).convert('RGB'))[box[1]:box[3], box[0]:box[2]].copy()
    h, w = im.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE
    seeds = [(x, 0) for x in range(0, w, 7)] + [(x, h - 1) for x in range(0, w, 7)] + [(0, y) for y in range(0, h, 7)] + [(w - 1, y) for y in range(0, h, 7)]
    for (x, y) in seeds:
        if mask[y + 1, x + 1] == 0:
            cv2.floodFill(im.copy(), mask, (x, y), 0, (tol,) * 3, (tol,) * 3, flags)
    fg = (mask[1:-1, 1:-1] == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
    big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    x, y, bw, bh = st[big, :4]
    keep = lab == big
    for i in range(1, n):   # hair islands inside the figure's box
        xi, yi, wi, hi, ar = st[i]
        if i != big and ar > 20 and xi > x + 20 and xi + wi < x + bw and yi > y and yi + hi < y + bh: keep |= lab == i
    a = keep.astype(np.uint8) * 255
    a = cv2.erode(a, np.ones((2, 2), np.uint8))            # drop the pale background rim
    a = cv2.GaussianBlur(a, (3, 3), 0)
    # decontaminate edge colours: pull interior colour outward so soft edges don't carry the sheet's cream
    solid = (a > 250).astype(np.uint8)
    rgb = cv2.inpaint(im, ((a < 251) & (a > 0)).astype(np.uint8) * 255, 2, cv2.INPAINT_TELEA)
    rgb[solid > 0] = im[solid > 0]
    return np.dstack([rgb, a])

def poly_mask(shape, pts):
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 255)
    return m > 0

def feather(m, r=1.2):
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), r)

def save(arr, name):
    Image.fromarray(arr.astype(np.uint8)).save(OUT + name)

def layer(src, m):
    out = src.copy(); out[..., 3] = (src[..., 3] * m).astype(np.uint8); return out

def hsv(rgb):
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

# ---------------------------------------------------------------- ChatGPT
G = cutout('reference/sheet_chatgpt.webp', (770, 0, 1030, 1000))
ARM_G = [(104, 336), (150, 322), (186, 324), (206, 340), (226, 400), (238, 460), (241, 518), (228, 538), (206, 528), (190, 540), (140, 540), (112, 500), (98, 440), (96, 380)]
HAND_G = [(162, 478), (204, 474), (214, 500), (208, 532), (178, 536), (160, 512)]
COLLAR_G = [(88, 300), (150, 298), (202, 304), (208, 338), (150, 344), (96, 342)]
REAR_G = [(18, 150), (58, 172), (96, 190), (106, 206), (110, 250), (106, 300), (96, 330), (66, 370), (20, 360), (0, 330), (0, 230), (6, 180)]
BEHIND_G = [(96, 316), (150, 314), (206, 320), (210, 430), (202, 560), (60, 560), (58, 400)]   # coat/skirt behind the forearm

arm = poly_mask(G.shape, ARM_G) & ~poly_mask(G.shape, HAND_G)
save(layer(G, feather(arm) * (G[..., 3] > 0)), 'gpt_arm.png')
save(layer(G, feather(poly_mask(G.shape, COLLAR_G))), 'gpt_collar.png')
rear = poly_mask(G.shape, REAR_G)
save(layer(G, feather(rear)), 'gpt_rear.png')
body = G.copy()
hole = poly_mask(G.shape, ARM_G) | poly_mask(G.shape, HAND_G)
behind = poly_mask(G.shape, BEHIND_G)
fill = hole & behind
# painted fill: the coat body hanging behind the arm (flat coat colour, darker toward the back, a few long folds)
yy, xx = np.mgrid[0:G.shape[0], 0:G.shape[1]]
coat = np.array([48, 48, 57], np.float32)
g = (1 - 0.35 * np.clip((150 - xx) / 60.0, 0, 1))[..., None]
paint = coat * g
for fx, k in [(128, .02), (160, -.03), (184, .01)]:
    d = np.abs(xx - (fx + (yy - 330) * k))
    paint = np.where((d < 1.2)[..., None] & (yy > 340)[..., None], np.array([30, 30, 37], np.float32), paint)
paint = np.where((np.abs(xx - (200 + (yy - 330) * .02)) < 1.5)[..., None], np.array([20, 20, 26], np.float32), paint)   # front edge line
body[..., :3] = np.where(fill[..., None], paint, body[..., :3])
a = body[..., 3].astype(np.float32)
a[hole & ~behind] = 0; a[fill] = 255
a *= 1 - feather(rear, 1.0) * 0.999   # rear hair lives in its own layer
body[..., 3] = a.clip(0, 255)
# the iris: pixels teal-ish inside the eye box become a sprite; the base eye gets painted white there
eye_box = poly_mask(G.shape, [(149, 138), (174, 137), (174, 159), (149, 159)])
hv = hsv(G[..., :3])
iris = eye_box & (hv[..., 1] > 60) & (hv[..., 0] > 70) & (hv[..., 0] < 105)
iris = cv2.dilate(iris.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
iris &= eye_box
save(layer(G, feather(iris, .6)), 'gpt_iris.png')
body[..., :3][iris] = (246, 246, 244)
save(body, 'gpt_body.png')

# tail from the TAIL (SIDE) detail, mirrored so the root is on the right (it trails behind her, to screen-left)
T = cutout('reference/sheet_chatgpt.webp', (1036, 410, 1330, 552), tol=9)
T = T[:, ::-1].copy()
save(T, 'gpt_tail.png')

# ---------------------------------------------------------------- Claude
C = cutout('reference/sheet_claude_b.webp', (590, 70, 880, 1000))
hv = hsv(C[..., :3])
copper = (hv[..., 0] <= 22) & (hv[..., 1] > 70) & (hv[..., 2] > 150)
copper = cv2.morphologyEx(copper.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
ARM_C = [(108, 190), (150, 183), (186, 191), (203, 224), (207, 300), (212, 380), (214, 440), (206, 480), (198, 498), (160, 500), (125, 496), (114, 470), (109, 400), (106, 300), (104, 230)]
HAND_C = [(118, 476), (158, 476), (164, 510), (118, 510)]
LOCK_C = [(68, 162), (98, 168), (100, 200), (92, 220), (88, 248), (72, 262), (63, 290), (57, 318), (53, 345), (49, 372), (45, 398), (30, 406), (21, 392), (25, 360), (30, 330), (38, 300), (44, 270), (50, 240), (58, 212), (64, 185)]
FRONT_C = [(66, 160), (100, 160), (100, 420), (40, 420), (36, 330), (54, 280), (60, 230), (66, 200)]   # body behind the lock
REAR_C = [(186, 118), (232, 108), (290, 170), (290, 930), (150, 930), (190, 510), (206, 300), (192, 200)]
BEHIND_C = [(104, 196), (190, 198), (200, 250), (201, 482), (104, 482)]

arm = poly_mask(C.shape, ARM_C) & ~poly_mask(C.shape, HAND_C) & ~(copper & ~poly_mask(C.shape, [(108, 186), (206, 186), (206, 500), (108, 500)]))
save(layer(C, feather(arm) * (C[..., 3] > 0)), 'cl_arm.png')
lock = poly_mask(C.shape, LOCK_C) & (hv[..., 2] > 90) & (C[..., 3] > 0)
save(layer(C, feather(lock, .8)), 'cl_lock.png')
rear = poly_mask(C.shape, REAR_C) & (copper | (poly_mask(C.shape, [(206, 170), (290, 170), (290, 930), (206, 930)]) & (C[..., 3] > 0)))
rear = cv2.dilate(rear.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
rear &= poly_mask(C.shape, REAR_C) & ~arm
save(layer(C, feather(rear, .8)), 'cl_rear.png')
body = C.copy()
hole = poly_mask(C.shape, ARM_C) | poly_mask(C.shape, HAND_C)
behind = poly_mask(C.shape, BEHIND_C)
# behind the sleeve is the side of the cardigan: flat knit colour, a soft shade toward the back, and her back line
card = np.array([236, 219, 196], np.float32)
yy, xx = np.mgrid[0:C.shape[0], 0:C.shape[1]]
shade = np.clip((xx - 140) / 60.0, 0, 1)[..., None]
fillc = card * (1 - 0.12 * shade)
body[..., :3] = np.where((hole & behind)[..., None], fillc, body[..., :3])
for fx in [150, 172]:   # faint knit ribs
    d = np.abs(xx - fx); body[..., :3] = np.where(((d < .8) & (hole & behind) & (yy < 450))[..., None], fillc * .93, body[..., :3])
rib = (hole & behind) & (yy > 452)
body[..., :3] = np.where(rib[..., None], np.where(((xx % 5) < 1)[..., None], card * .86, card * .97), body[..., :3])
cv2.polylines(body, [np.array([(106, 452), (200, 452)], np.int32)], False, (170, 140, 115, 255), 1, cv2.LINE_AA)
under = lock & poly_mask(C.shape, FRONT_C)
body[..., :3] = cv2.inpaint(body[..., :3], cv2.dilate(under.astype(np.uint8), np.ones((3, 3), np.uint8)) * 255, 4, cv2.INPAINT_TELEA)
a = body[..., 3].astype(np.float32)
a[hole & ~behind] = 0; a[hole & behind] = 255
a[lock & ~poly_mask(C.shape, FRONT_C)] = 0
a *= 1 - feather(rear & ~poly_mask(C.shape, [(104, 180), (200, 180), (200, 500), (104, 500)]), 1.0) * 0.999
body[..., 3] = a.clip(0, 255)
cv2.polylines(body, [np.array([(196, 205), (199, 300), (201, 400), (200, 480)], np.int32)], False, (150, 115, 95, 255), 1, cv2.LINE_AA)
eye_box = poly_mask(C.shape, [(103, 116), (115, 116), (115, 130), (103, 130)])
hv2 = hsv(C[..., :3])
iris = eye_box & (hv2[..., 1] > 90) & (hv2[..., 0] < 30) & (hv2[..., 2] < 215)
iris = cv2.dilate(iris.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
iris &= eye_box
save(layer(C, feather(iris, .6)), 'cl_iris.png')
body[..., :3][iris] = (250, 246, 242)
save(body, 'cl_body.png')

for n, arr in [('gpt', G), ('cl', C)]:
    ys = np.where(arr[..., 3].max(axis=1) > 128)[0]
    print(n, 'alpha rows', ys.min(), ys.max())
print('tail', T.shape)
