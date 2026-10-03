import numpy as np
W_, H_ = 1280, 720
FS = W_ * H_ * 3 // 2
def load(path):
    raw = np.fromfile(path, np.uint8)
    n = raw.size // FS
    raw = raw[:n * FS].reshape(n, FS)
    Y = raw[:, :W_ * H_].reshape(n, H_, W_)
    U = raw[:, W_ * H_:W_ * H_ * 5 // 4].reshape(n, H_ // 2, W_ // 2)
    V = raw[:, W_ * H_ * 5 // 4:].reshape(n, H_ // 2, W_ // 2)
    return Y, U, V
