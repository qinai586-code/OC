"""Faces that sing: viseme mouths driven by the vocal, blinks, and a living head.

Coordinates are in the 4x upscaled head drawings (work/chars/hd). For each head: the mouth
centre and its natural width, and the eye boxes (x0, y0, x1, y1) used by the lid warp.
"""
from acting import *
import voice

HEADS = {
    'A_x0': dict(m=(538, 855, 56), eyes=[(300, 645, 433, 745), (558, 645, 700, 737)], face=(500, 700, 330)),
    'A_x1': dict(m=(487, 865, 58), eyes=[(300, 665, 425, 748), (542, 665, 692, 740)], face=(495, 720, 330)),
    'A_x2': dict(m=(442, 853, 58), eyes=[(225, 618, 375, 727), (542, 635, 700, 735)], face=(460, 700, 330)),
    'A_x3': dict(m=(468, 849, 62), eyes=[], face=(470, 700, 330)),
    'B_x0': dict(m=(533, 885, 46), eyes=[(292, 652, 450, 777), (592, 652, 725, 767)], face=(520, 760, 360), draw_closed=True),
    'B_x1': dict(m=(455, 892, 44), eyes=[(267, 667, 383, 783), (483, 625, 617, 733)], face=(470, 760, 360)),
    'B_x2': dict(m=(514, 887, 44), eyes=[(292, 632, 417, 765), (567, 632, 717, 757)], face=(510, 750, 360)),
    'B_x3': dict(m=(544, 888, 44), eyes=[(292, 663, 433, 755), (583, 655, 733, 747)], face=(520, 760, 360)),
    'B_x4': dict(m=(520, 903, 46), eyes=[], face=(510, 770, 360)),
    'B_x5': dict(m=(444, 871, 60), eyes=[(233, 620, 358, 762), (517, 620, 683, 750)], face=(460, 740, 360), open0=0.55),
}

LIP = {'A': np.array([0.30, 0.10, 0.13], np.float32), 'B': np.array([0.42, 0.13, 0.12], np.float32)}
INNER = {'A': np.array([0.26, 0.08, 0.11], np.float32), 'B': np.array([0.36, 0.10, 0.10], np.float32)}
TONGUE = np.array([0.86, 0.47, 0.47], np.float32)
TEETH = np.array([0.97, 0.95, 0.93], np.float32)


# ---------------------------------------------------------------------------------- blinks
def lid(img, box, c):
    """Lower the upper lid over one eye box by fraction c (0 open, 1 closed): the lash band
    slides down to the lower lid and the lid skin above stretches after it."""
    if c <= 1e-3:
        return img
    x0, y0, x1, y1 = box
    H = y1 - y0
    pad = int(0.9 * H)
    X0, X1 = max(0, x0 - 8), min(img.shape[1], x1 + 8)
    Y0, Y1 = max(0, y0 - pad), min(img.shape[0], y1 + 6)
    roi = img[Y0:Y1, X0:X1]
    h, w = roi.shape[:2]
    yl = y0 + 0.30 * H - Y0            # lower edge of the lash band (open)
    band = 0.17 * H
    yb = y1 - 0.08 * H - Y0             # lower lid
    ytop = yl - band - 0.55 * H
    yn = yl + c * (yb - yl) * 0.96
    bn = band * (1 - 0.35 * c)
    ys = np.arange(h, dtype=np.float32)[:, None].repeat(w, 1)
    src = ys.copy()
    b0, b1 = yl - band, yn - bn
    sk = (ys >= ytop) & (ys < b1)
    src = np.where(sk, ytop + (ys - ytop) * (b0 - ytop) / max(b1 - ytop, 1e-3), src)
    bd = (ys >= b1) & (ys < yn)
    src = np.where(bd, b0 + (ys - b1) * (yl - b0) / max(yn - b1, 1e-3), src)
    lo = (ys >= yn) & (ys <= yb)
    src = np.where(lo, yl + (ys - yn) * (yb - yl) / max(yb - yn, 1e-3), src)
    xs = np.arange(w, dtype=np.float32)
    fx = np.clip(np.minimum(xs - (x0 - X0), (x1 - X0) - xs) / (0.16 * (x1 - x0)), 0, 1)[None]
    src = ys + (src - ys) * fx
    out = img.copy()
    out[Y0:Y1, X0:X1] = cv2.remap(roi, np.repeat(xs[None], h, 0), src.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return out


CLOSED = {'A': ('A_x3', [(230, 639, 363, 739), (488, 639, 630, 731)]),
          'B': ('B_x4', [(279, 670, 437, 795), (579, 670, 712, 785)])}
_mask = {}


def closed_eyes(img, name, k):
    """Blend in the character's own drawn closed eyes (from her eyes-closed drawing), mapped
    box-to-box onto each open eye, inside a feathered ellipse."""
    if k <= 1e-3:
        return img
    src_name, sboxes = CLOSED[name[0]]
    src = char(src_name)
    out = img.copy()
    for tb, sb in zip(HEADS[name]['eyes'], sboxes):
        x0, y0, x1, y1 = tb
        sx = (x1 - x0) / (sb[2] - sb[0])
        sy = (y1 - y0) / (sb[3] - sb[1])
        M = np.float32([[sx, 0, x0 - sb[0] * sx], [0, sy, y0 - sb[1] * sy]])
        w, h = x1 - x0, y1 - y0
        X0, Y0, X1, Y1 = int(x0 - 0.3 * w), int(y0 - 0.4 * h), int(x1 + 0.3 * w), int(y1 + 0.3 * h)
        M2 = M.copy(); M2[0, 2] -= X0; M2[1, 2] -= Y0
        patch = cv2.warpAffine(src, M2, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        key = (name, tb)
        if key not in _mask:
            m = np.zeros((Y1 - Y0, X1 - X0), np.float32)
            cv2.ellipse(m, (int((x0 + x1) / 2 - X0), int((y0 + y1) / 2 - Y0 - 0.05 * h)), (int(0.62 * w), int(0.68 * h)), 0, 0, 360, 1.0, -1)
            _mask[key] = gblur(m, 0.09 * w)[:, :, None]
        m = _mask[key] * k
        out[Y0:Y1, X0:X1, :3] = out[Y0:Y1, X0:X1, :3] * (1 - m) + patch[:, :, :3] * m
    return out


def blink_amount(t, seed=0, every=(2.4, 4.6), extra=()):
    """Closure 0..1 at time t: close in 2 frames, hold 1, open in 3 (a natural blink)."""
    rng = np.random.default_rng(seed)
    times = list(extra)
    x = rng.uniform(0.3, 1.5)
    while x < 240:
        times.append(x)
        x += rng.uniform(*every)
    c = 0.0
    for b in times:
        d = t - b
        if 0 <= d < 0.30:
            if d < 2 / 24:
                v = d / (2 / 24)
            elif d < 3 / 24:
                v = 1.0
            else:
                v = 1 - (d - 3 / 24) / (3 / 24)
            c = max(c, float(np.clip(v, 0, 1)))
    return c * c * (3 - 2 * c)


def blink(im, name, c):
    """c 0..1: the upper lids come halfway down, then the drawn closed eyes take over."""
    if c <= 1e-3:
        return im
    for box in HEADS[name]['eyes']:
        im = lid(im, box, min(c, 0.55) / 0.55 * 0.5)
    return closed_eyes(im, name, smoothstep(0.45, 0.85, c))


# ---------------------------------------------------------------------------------- mouths
def mouth(img, name, o, wd, fr=0.0, m=None):
    """Draw the sung mouth: o = open, wd = wide (e/i) vs round (o/u), fr = fricative (teeth).
    The jaw drops with the opening. Anti-aliased at 4x subpixel precision.
    m: optional (x, y, width) override (for in-between drawings)."""
    hd = HEADS[name]
    mx, my, W = (float(v) for v in (hd['m'] if m is None else m))
    who = name[0]
    o = max(o, hd.get('open0', 0.0))
    if o < 0.05 and not hd.get('draw_closed'):
        return img
    out = img
    rnd = (1 - wd) * o
    width = W * (0.62 + 0.42 * wd - 0.22 * rnd) * (1 - 0.15 * fr)
    height = W * (0.04 + 0.70 * o) * (1 - 0.35 * wd * (1 - o)) * (1 - 0.5 * fr)
    # the jaw drops: the lower face slides down a little with the opening
    jaw = 0.32 * height
    if jaw > 0.4:
        x0, x1 = int(mx - 3.0 * W), int(mx + 3.0 * W)
        y0, y1 = int(my - 0.3 * W), int(my + 2.6 * W)
        roi = out[y0:y1, x0:x1]
        h, w = roi.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        X, Y = xs + x0 - mx, ys + y0 - my
        wx = np.exp(-(X / (1.6 * W)) ** 2)
        wy = np.clip((Y + 0.3 * W) / (0.6 * W), 0, 1) * np.clip((2.6 * W - Y) / (1.4 * W), 0, 1)
        out = out.copy()
        out[y0:y1, x0:x1] = cv2.remap(roi, xs, (ys - jaw * wx * wy).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if height < 2.2:
        # closed: a short soft line (drawn only for heads whose drawing has none)
        if hd.get('draw_closed'):
            out = out.copy() if out is img else out
            pts = np.array([(mx - 0.25 * W, my), (mx, my + 0.6), (mx + 0.25 * W, my)], np.float32)
            m = np.zeros(out.shape[:2], np.float32)
            cv2.polylines(m, [(pts * 4).astype(np.int32)], False, 1.0, 9, cv2.LINE_AA, shift=2)
            m = gblur(m, 0.7) * 0.75
            out[:, :, :3] = out[:, :, :3] * (1 - m[:, :, None]) + LIP[who] * m[:, :, None]
        return out
    # outline: flatter upper lip, round lower lip (an anime "D" turned on its side)
    n = 28
    a = np.linspace(0, np.pi, n)
    top = np.stack([mx - width / 2 * np.cos(a), my - 0.18 * height - 0.10 * height * np.sin(a) * (1 - wd)], 1)
    bot = np.stack([mx + width / 2 * np.cos(a), my - 0.18 * height + height * np.sin(a) ** (0.8 + 0.6 * wd)], 1)
    poly = np.concatenate([top, bot])
    X0, Y0 = int(mx - width), int(my - height - 6)
    X1, Y1 = int(mx + width) + 2, int(my + 1.3 * height + 8)
    roi = out[Y0:Y1, X0:X1].copy()
    h, w = roi.shape[:2]
    P = ((poly - [X0, Y0]) * 4).astype(np.int32)
    fill = np.zeros((h, w), np.float32)
    cv2.fillPoly(fill, [P], 1.0, cv2.LINE_AA, shift=2)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    # interior: dark at the top, the tongue rises at the bottom when wide open
    v = np.clip((ys + Y0 - (my - 0.18 * height)) / max(height, 1), 0, 1)
    col = INNER[who][None, None, :] * (0.75 + 0.35 * v[:, :, None])
    tk = np.clip((v - 0.55) / 0.3, 0, 1) * np.clip((o - 0.3) / 0.3, 0, 1) * np.exp(-((xs + X0 - mx) / (0.36 * width)) ** 2)
    col = col * (1 - tk[:, :, None] * 0.9) + TONGUE * tk[:, :, None] * 0.9
    th = np.clip(1 - (v - 0.0) / 0.16, 0, 1) * np.clip(wd * 1.2 + fr, 0, 1) * (v > 0.0)
    col = col * (1 - th[:, :, None]) + TEETH * th[:, :, None]
    line = np.zeros((h, w), np.float32)
    cv2.polylines(line, [P], True, 1.0, 10, cv2.LINE_AA, shift=2)
    up = np.zeros((h, w), np.float32)
    cv2.polylines(up, [P[:n]], False, 1.0, 14, cv2.LINE_AA, shift=2)
    line = np.maximum(gblur(line, 0.6), gblur(up, 0.6))
    rgb = roi[:, :, :3]
    rgb = rgb * (1 - fill[:, :, None]) + col * fill[:, :, None]
    rgb = rgb * (1 - line[:, :, None] * 0.85) + LIP[who] * line[:, :, None] * 0.85
    roi[:, :, :3] = rgb
    out = out.copy() if out is img else out
    out[Y0:Y1, X0:X1] = roi
    return out


# ---------------------------------------------------------------------------------- the whole head
def head(name, t, sing=True, gain=1.0, blink_seed=0, blink_extra=(), yaw=0.0, pitch=0.0, roll=0.0,
         sway=1.6, breathe=0.004, img=None, hold_mouth=None, eyes_closed=0.0):
    """One living frame of a head: blinks + sung mouth + puppet motion + hair, on every frame."""
    hd = HEADS[name]
    im = char(name) if img is None else img
    c = max(blink_amount(t, blink_seed, extra=blink_extra), eyes_closed)
    im = blink(im, name, c)
    if hold_mouth is not None:
        o, wd, fr = hold_mouth
    elif sing:
        o, wd, fr = voice.at(t)
        o *= gain
    else:
        o, wd, fr = 0.0, 0.5, 0.0
    im = mouth(im, name, float(np.clip(o, 0, 1)), wd, fr)
    return secondary(im, t, breathe=breathe, sway=sway, seed=blink_seed, hair_from=0.38,
                     yaw=yaw, pitch=pitch, roll=roll, face=hd['face'])


def _canvas_pos(n, Wc, H, xy):
    img = char(n)
    sc = H / img.shape[0]
    x0 = (Wc - int(img.shape[1] * sc)) // 2
    return np.array([xy[0] * sc + x0, xy[1] * sc, xy[2] * sc])


def morph_head(M, names, s, t, sing=True, gain=1.0, sway=1.6, yaw=0.0, pitch=0.0, roll=0.0, seed=0, breathe=0.004):
    """A living in-between of several drawings of one head (Morph), singing: the mouth and the
    puppet's face centre follow the in-between."""
    im = M.at(s)
    H, Wc = im.shape[:2]
    i = int(np.clip(np.floor(s), 0, len(names) - 2))
    u = float(np.clip(s - i, 0, 1))
    a, b = names[i], names[i + 1]
    m = _canvas_pos(a, Wc, H, HEADS[a]['m']) * (1 - u) + _canvas_pos(b, Wc, H, HEADS[b]['m']) * u
    fc = _canvas_pos(a, Wc, H, HEADS[a]['face']) * (1 - u) + _canvas_pos(b, Wc, H, HEADS[b]['face']) * u
    dom = a if u < 0.5 else b
    if sing:
        o, wd, fr = voice.at(t)
        o *= gain
    else:
        o, wd, fr = 0.0, 0.5, 0.0
    im = mouth(im, dom, float(np.clip(o, 0, 1)), wd, fr, m=tuple(m))
    return secondary(im, t, breathe=breathe, sway=sway, seed=seed, hair_from=0.38, yaw=yaw, pitch=pitch, roll=roll, face=tuple(fc))
