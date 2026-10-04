"""v9, 6.625-7.458 s (frames 159-179): A's point of view on the light, between the wide two-shot and S1.

The wide holds the girls with their hands on the stone (it cuts on "two", 6.625). This shot is what they are watching:
the light, alone against the sky above the Earth's rim (KV1's own sky, from the same plate as the wide). It climbs to a
hover and begins to sink; on "one" (7.5) S1 opens on A, palm already raised, with the light at the same screen point
(908, 90) and moving the same way. The hand's lift happens during this shot and is not shown (an elision by cutaway,
not a demonstrated lift)."""
import os, sys
import cv2
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opening_ink as OI

T0, T1 = 159 / 24, 180 / 24
P0, PA, PE = np.array([684.0, 136.0]), np.array([936.0, 76.0]), np.array([909.0, 89.0])   # PE: S1's light on frame 180 is (908, 90)
_KV = None


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def light(t):
    if t < 7.10:
        u = smooth((t - T0) / (7.10 - T0))
        p = P0 + (PA - P0) * u
    else:
        u = smooth((t - 7.10) / (T1 - 1 / 24 - 7.10))
        p = PA + (PE - PA) * u
    hov = np.exp(-((t - 7.17) / 0.12) ** 2)                                     # a small hover at the top
    p = p + hov * np.array([5.0 * np.sin(2 * np.pi * (t - 7.05) / 0.5), -3.0 * np.sin(np.pi * (t - 7.05) / 0.5)])
    sc = 0.50 + (0.766 - 0.50) * smooth((t - T0) / (T1 - 1 / 24 - T0))
    return p, sc, 1.10 - 0.08 * smooth((t - 7.1) / 0.35)


def frame(t):
    global _KV
    if _KV is None:
        _KV = cv2.imread(OI.KV1).astype(np.float32)
        OI.PROF = OI.glow_profile()
    u = smooth((t - T0) / (T1 - T0))
    w = 1600.0 - 24.0 * u                                                        # a slow drift up and a touch closer
    x0, y0 = 1180.0 - 14.0 * u, 70.0 - 22.0 * u
    f = OI.W / w
    img = OI.aa_resize(_KV, f, OI.W, OI.H, x0, y0, border=cv2.BORDER_REFLECT)
    # the sky starts in the wide's tone (KV1, same plate) and moves 60% of the way to S1's bluer night sky over the last
    # half second (measured means: KV1 sky BGR 42.6/22.6/15.4, S1 sky 61.5/22.8/8.7), so the cut on "one" changes plate,
    # not exposure
    img = img * (np.array([61.5 / 42.6, 22.8 / 22.6, 8.7 / 15.4], np.float32) ** (0.6 * smooth((t - 7.0) / 0.45)))
    p, sc, it = light(t)
    return OI.glow(img, p, sc, it)


if __name__ == '__main__':
    out = sys.argv[1]
    for k in range(159, 180):
        cv2.imwrite(os.path.join(out, 'f%04d.png' % k), np.clip(np.round(frame(k / 24)), 0, 255).astype(np.uint8))
    print('POV frames 159-179 written; light', [tuple(np.round(light(k / 24)[0])) for k in (159, 169, 179)])
