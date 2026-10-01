"""Upscale the small expression heads x4 (anime Real-ESRGAN) so close-ups stay sharp.
RGB: transparent areas are filled by normalized-blur colour extension before upscaling;
alpha: cubic upscale, lightly re-sharpened."""
import subprocess, sys
from acting import *
SP = SCRATCH
HD = w2('chars', 'hd')
os.makedirs(HD, exist_ok=True)
names = sys.argv[1:] or ['A_x0', 'A_x1', 'A_x2', 'A_x3', 'B_x0', 'B_x1', 'B_x2', 'B_x3', 'B_x4', 'B_x5']
tmp = os.path.join(SP, 'uph')
os.makedirs(tmp, exist_ok=True)
for n in names:
    im = char(n)
    a = im[:, :, 3:4]
    rgb = im[:, :, :3]
    acc, wa = rgb * a, a.copy()
    for r in (2, 4, 8, 16, 32):
        acc2, wa2 = gblur(rgb * a, r), gblur(a[:, :, 0], r)[:, :, None]
        fill = acc2 / np.maximum(wa2, 1e-4)
        rgb = np.where(a > 0.98, rgb, rgb * a + fill * (1 - a)) if r == 2 else rgb * a + fill * (1 - a)
    cv2.imwrite(os.path.join(tmp, n + '.png'), (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)[:, :, ::-1])
os.makedirs(os.path.join(tmp, 'out'), exist_ok=True)
subprocess.run([sys.executable, os.path.join(SP, 'upscale4.py'), os.path.join(SP, 'models', 'RealESRGAN_x4plus_anime_6B.pth'),
                os.path.join(tmp, 'out')] + [os.path.join(tmp, n + '.png') for n in names], check=True)
for n in names:
    im = char(n)
    up = cv2.imread(os.path.join(tmp, 'out', n + '.png'))[:, :, ::-1].astype(np.float32) / 255.0   # 4x
    h, w = im.shape[:2]
    a = cv2.resize(im[:, :, 3], (w * 4, h * 4), interpolation=cv2.INTER_CUBIC)
    a = np.clip((a - 0.5) * 1.25 + 0.5, 0, 1)
    out = np.dstack([np.clip(up, 0, 1), a])[:, :, [2, 1, 0, 3]]
    cv2.imwrite(os.path.join(HD, n + '.png'), (out * 65535 + 0.5).astype(np.uint16))
    print(n, up.shape)
