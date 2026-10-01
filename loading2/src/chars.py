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
    import sys as _s
    if '--sheets-only' not in _s.argv:
        pass
    img, a = kv('KV1')
    save('kv1_A', img, a, (0, 0, 1536, 2048))
    save('kv1_B', img, a, (1536, 0, 3072, 2048))
    img, a = kv('KV3')
    save('kv3_A', img, a, (0, 0, 1560, 2048))
    save('kv3_B', img, a, (1560, 0, 3072, 2048))
    i3b = imread(E1.work('plates', 'KV3b.png'))
    save('kv3b_A', i3b, a, (0, 0, 1560, 2048))
    P4 = E1.Plate('KV4')
    a = solid_right(P4) * smoothstep(0.35, 0.5, gblur(P4.depth, 4))
    save('kv4_B', P4.img, np.maximum(a, P4.char_alpha * (P4.char_alpha > 0.5)))
    unlit = np.load(E1.work('derived', 'KV5_unlit.npy')).astype(np.float32)
    img, a = kv('KV5', src=unlit)
    m = np.ones(a.shape, np.uint8)
    cv2.fillPoly(m, [np.array([(1500, 1060), (3072, 1060), (3072, 2048), (1640, 2048), (1470, 1330)], np.int32)], 0)
    m[:900, :260] = 0
    save('kv5_AB', img, a * m)
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
    crops = {'sheet_claude_a': [('B_closed', (1188, 1540, 1448, 1880)), ('B_smile', (908, 1540, 1168, 1880)), ('B_look', (348, 1540, 608, 1880)),
                                ('B_side_full', (1248, 120, 1648, 1430))],
             'sheet_chatgpt': [('A_smile', (2800, 1180, 3048, 1480)), ('A_curious', (2560, 1180, 2800, 1480)), ('A_side_full', (1580, 30, 2010, 1930))]}
    for sh, lst in crops.items():
        img = imread(os.path.join(up, sh + '.png'))
        for name, (x0, y0, x1, y1) in lst:
            c = img[y0:y1, x0:x1]
            save(name, c, matte(c))
    for name, f in (('A_full', 'chatgpt_dragon_ref.png'), ('B_full', 'claude_cold_ref.png')):
        im = imread(os.path.join('/home/user/OC/reference', f))
        save(name, im[:, :, :3], im[:, :, 3])
