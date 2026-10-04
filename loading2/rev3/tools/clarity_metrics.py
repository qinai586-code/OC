import numpy as np, cv2
def lum(x):
    x = np.asarray(x, np.float32)
    return 0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2]
def band(y):
    return cv2.GaussianBlur(y, (0, 0), 0.6) - cv2.GaussianBlur(y, (0, 0), 1.6)
def fine(img, r):
    """fine-detail energy: RMS of the 0.6-1.6 px difference-of-Gaussians band of luma in box r (x0, y0, x1, y1)"""
    x0, y0, x1, y1 = r
    y = lum(img)
    return float(np.sqrt((band(y)[y0:y1, x0:x1] ** 2).mean()))
def acut(img, r):
    """edge acutance: mean Scharr gradient over the strongest 5% of pixels in the box"""
    x0, y0, x1, y1 = r
    y = lum(img)
    g = np.hypot(cv2.Scharr(y, cv2.CV_32F, 1, 0), cv2.Scharr(y, cv2.CV_32F, 0, 1))[y0:y1, x0:x1] / 32.0
    return float(np.mean(np.sort(g.ravel())[-max(1, g.size // 20):]))
def psnr(a, b, r):
    x0, y0, x1, y1 = r
    e = lum(a)[y0:y1, x0:x1] - lum(b)[y0:y1, x0:x1]
    return float(20 * np.log10(255 / max(np.sqrt((e ** 2).mean()), 1e-6)))
def chroma_fine(img, r):
    """fine energy of the colour-difference planes (R-Y, B-Y): how sharp colour edges are"""
    x0, y0, x1, y1 = r
    x = np.asarray(img, np.float32); y = lum(x)
    e = [band(x[..., 2] - y), band(x[..., 0] - y)]
    return float(np.sqrt(np.mean([(c[y0:y1, x0:x1] ** 2).mean() for c in e])))
