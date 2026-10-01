"""Character cut-outs (characters only, no scenery) from the character images."""
import sys
sys.path.insert(0, '/home/user/OC/loading/src')
from lw import *
import engine as E1

OUT = w2('chars')
os.makedirs(OUT, exist_ok=True)


def save(name, rgb, a, box=None):
    if box is not None:
        x0, y0, x1, y1 = box
        rgb, a = rgb[y0:y1, x0:x1], a[y0:y1, x0:x1]
    ys, xs = np.nonzero(a > 0.02)
    y0, y1, x0, x1 = max(0, ys.min() - 8), ys.max() + 9, max(0, xs.min() - 8), xs.max() + 9
    rgba = np.dstack([rgb[y0:y1, x0:x1], a[y0:y1, x0:x1]])
    cv2.imwrite(os.path.join(OUT, name + '.png'), (np.clip(rgba[:, :, [2, 1, 0, 3]], 0, 1) * 65535).astype(np.uint16))
    print(name, rgba.shape)


def kv(name, alpha_fn=None, src=None):
    P = E1.Plate(name)
    a = P.char_alpha if alpha_fn is None else alpha_fn(P)
    img = P.img if src is None else src
    return img, np.clip(a, 0, 1)


def solid_right(P):
    m = P.char_alpha
    solid = np.maximum.accumulate((m > 0.55).astype(np.uint8), axis=1)
    solid = cv2.erode(solid, np.ones((1, 41), np.uint8)).astype(np.float32)
    return np.maximum(m, gblur(solid, 3))


if __name__ == '__main__':
    # expression heads and full figures from the upscaled character sheets (x2 coordinates)
    from engine import fill_region
    import onnxruntime as ort
    so = ort.SessionOptions(); so.intra_op_num_threads = 4
    seg = ort.InferenceSession(os.path.join(SCRATCH, 'models', 'isnet-anime.onnx'), so, providers=['CPUExecutionProvider'])
    def matte(img):
        x = cv2.resize(img, (1024, 1024), interpolation=cv2.INTER_AREA) - 0.5
        m = seg.run(None, {seg.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
        m = (m - m.min()) / (m.max() - m.min() + 1e-9)
        return cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC).clip(0, 1)
    up = os.path.join(SCRATCH, 'up2')
    crops = {'sheet_claude_a': [('B_turn0', (60, 120, 560, 1440)), ('B_turn1', (720, 120, 1180, 1440)), ('B_turn2', (1240, 120, 1660, 1440))]
                                + [('B_x%d' % i, (68 + 280 * i, 1530, 340 + 280 * i, 1890)) for i in range(6)],
             'sheet_chatgpt': [('A_turn0', (330, 20, 840, 1960)), ('A_turn1', (960, 20, 1460, 1960)), ('A_turn2', (1560, 20, 2030, 1960))]
                              + [('A_x%d' % i, (2056 + 248 * i, 1170, 2300 + 248 * i, 1490)) for i in range(4)]}
    for sh, lst in crops.items():
        img = imread(os.path.join(up, sh + '.png'))
        for name, (x0, y0, x1, y1) in lst:
            c = img[y0:y1, x0:x1]
            m = matte(c)
            m = np.clip((m - 0.15) / 0.7, 0, 1)
            save(name, c, m)
    for name, f in (('A_full', 'chatgpt_dragon_ref.png'), ('B_full', 'claude_cold_ref.png')):
        im = imread(os.path.join('/home/user/OC/reference', f))
        save(name, im[:, :, :3], im[:, :, 3])
