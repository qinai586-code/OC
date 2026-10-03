"""Restrained chroma repair for the Seedance 2.5 sources: V plane only, in the affected spans.
V_new = V_ref + lowpass(V_i - V_ref, 8 half-res px), where V_ref is V from the nearest clean frames on either side,
warped to frame i by luma optical flow and weighted by temporal distance. Where the luma warp disagrees with frame i
(occlusion, eyelids, a rising hand, growing cards), V_ref is replaced by a luma-guided filter of V_i itself.
Y and U are copied unchanged."""
import numpy as np, cv2, sys
from yuv import load
SPANS = [(8, 12), (56, 64), (108, 112)]


def flow_warp(plane, Y_from, Y_to, half):
    flow = cv2.calcOpticalFlowFarneback(Y_to, Y_from, None, 0.5, 4, 21, 3, 7, 1.5, 0)
    if half:
        flow = cv2.resize(flow, (plane.shape[1], plane.shape[0])) / 2
    h, w = plane.shape
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(plane.astype(np.float32), gx + flow[..., 0], gy + flow[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def repair(name):
    Y, U, V = load('dec/%s.yuv' % name)
    Vout = V.astype(np.float32).copy()
    fallback_frac = {}
    for s0, s1 in SPANS:
        a, b = s0 - 1, s1 + 1
        for i in range(s0, s1 + 1):
            wa = (b - i) / (b - a)
            Yi = Y[i]
            Va, Vb = flow_warp(V[a], Y[a], Yi, True), flow_warp(V[b], Y[b], Yi, True)
            Ya, Yb = flow_warp(Y[a], Y[a], Yi, False), flow_warp(Y[b], Y[b], Yi, False)
            ea = cv2.resize(cv2.GaussianBlur(np.abs(Ya - Yi), (0, 0), 3), (640, 360), interpolation=cv2.INTER_AREA)
            eb = cv2.resize(cv2.GaussianBlur(np.abs(Yb - Yi), (0, 0), 3), (640, 360), interpolation=cv2.INTER_AREA)
            # per-pixel anchor weights: trust the anchor whose warped luma agrees with frame i
            ka, kb = wa * np.exp(-(ea / 6.0) ** 2), (1 - wa) * np.exp(-(eb / 6.0) ** 2)
            ref = (ka * Va + kb * Vb) / np.maximum(ka + kb, 1e-6)
            trust = np.clip((ka + kb) / 0.5, 0, 1)                                      # low where neither anchor agrees
            Ys = cv2.resize(Yi, (640, 360), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
            gf = cv2.ximgproc.guidedFilter(Ys, V[i].astype(np.float32) / 255, 4, 1e-3) * 255
            ref = ref * trust + gf * (1 - trust)
            Vi = V[i].astype(np.float32)
            Vout[i] = ref + cv2.GaussianBlur(Vi - ref, (0, 0), 8)
            fallback_frac[i] = round(float((trust < 0.5).mean()), 4)
    out = np.concatenate([Y.reshape(len(Y), -1), U.reshape(len(U), -1), np.clip(np.round(Vout), 0, 255).astype(np.uint8).reshape(len(V), -1)], 1)
    out.tofile('dec/%s_rep.yuv' % name)
    return fallback_frac


if __name__ == '__main__':
    for n in sys.argv[1:]:
        fb = repair(n)
        print(n, 'fallback fraction per repaired frame:', fb)
