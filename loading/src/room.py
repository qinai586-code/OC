"""The room at the end of the light: a layout drawing in true 3D perspective.

Faces are filled with toned paper (painter's algorithm, near-plane clipped) and their edges are
drawn in graphite, so hidden lines are hidden the way a layout artist would hide them.
"""
import cv2
import numpy as np
from common import *
import dimension as dim
import fx
from proj import PCam
from shotbase import pencil_stroke, graphite


def box(x0, x1, y0, y1, z0, z1, tone=1.0, tag=None, skip=()):
    """Six quads of an axis-aligned box: (verts, normal, tone, tag)."""
    v = lambda x, y, z: (x, y, z)
    F = {
        'front': ([v(x0, y0, z0), v(x1, y0, z0), v(x1, y1, z0), v(x0, y1, z0)], (0, 0, -1)),
        'back': ([v(x1, y0, z1), v(x0, y0, z1), v(x0, y1, z1), v(x1, y1, z1)], (0, 0, 1)),
        'left': ([v(x0, y0, z1), v(x0, y0, z0), v(x0, y1, z0), v(x0, y1, z1)], (-1, 0, 0)),
        'right': ([v(x1, y0, z0), v(x1, y0, z1), v(x1, y1, z1), v(x1, y1, z0)], (1, 0, 0)),
        'top': ([v(x0, y1, z0), v(x1, y1, z0), v(x1, y1, z1), v(x0, y1, z1)], (0, 1, 0)),
        'bottom': ([v(x0, y0, z1), v(x1, y0, z1), v(x1, y0, z0), v(x0, y0, z0)], (0, -1, 0)),
    }
    return [(np.array(p, np.float64), np.array(n, np.float64), tone, tag) for k, (p, n) in F.items() if k not in skip]


def quad(p, n, tone=1.0, tag=None):
    return [(np.array(p, np.float64), np.array(n, np.float64), tone, tag)]


class Room:
    W, D, H = 6.0, 6.5, 3.0       # x in [-3, 3], z in [0, 6.5], y in [0, 3]
    WINDOW = (-1.45, 0.05, 1.05, 2.45)   # x0, x1, y0, y1 on the back wall
    KEY_ROWS, KEY_COLS = 4, 12

    def __init__(self, cutaway=False):
        self.faces = []
        hw = self.W / 2
        D, H = self.D, self.H
        wx0, wx1, wy0, wy1 = self.WINDOW
        # walls: floor, ceiling, left, right, back (with the window cut out as 4 quads)
        self.faces += quad([(-hw, 0, 0), (hw, 0, 0), (hw, 0, D), (-hw, 0, D)], (0, 1, 0), 0.97, 'floor')
        if not cutaway:
            self.faces += quad([(-hw, H, D), (hw, H, D), (hw, H, 0), (-hw, H, 0)], (0, -1, 0), 0.80, 'ceiling')
            self.faces += quad([(hw, 0, 0), (hw, H, 0), (hw, H, D), (hw, 0, D)], (-1, 0, 0), 0.86, 'wallR')
        self.faces += quad([(-hw, 0, D), (-hw, H, D), (-hw, H, 0), (-hw, 0, 0)], (1, 0, 0), 0.90, 'wallL')
        back = [((-hw, 0), (hw, wy0)), ((-hw, wy1), (hw, H)), ((-hw, wy0), (wx0, wy1)), ((wx1, wy0), (hw, wy1))]
        for (a, b) in back:
            self.faces += quad([(a[0], a[1], D), (b[0], a[1], D), (b[0], b[1], D), (a[0], b[1], D)], (0, 0, -1), 0.93, 'back')
        # window frame: sill and mullion
        self.faces += box(wx0 - 0.06, wx1 + 0.06, wy0 - 0.06, wy0, D - 0.12, D, 0.85, 'sill')
        self.faces += box((wx0 + wx1) / 2 - 0.02, (wx0 + wx1) / 2 + 0.02, wy0, wy1, D - 0.05, D, 0.8, 'mullion', skip=('back',))
        # desk
        dz0, dz1 = 4.2, 5.1
        self.faces += box(-1.2, 1.2, 0.72, 0.78, dz0, dz1, 0.95, 'desk')
        for lx in (-1.15, 1.09):
            for lz in (dz0 + 0.05, dz1 - 0.11):
                self.faces += box(lx, lx + 0.06, 0.0, 0.72, lz, lz + 0.06, 0.8, 'leg')
        # console: a slanted block with a key field
        self.cons = dict(x0=-0.8, x1=0.8, z0=4.35, z1=4.85, y0=0.78, y_front=0.84, y_back=1.02)
        c = self.cons
        top = [(c['x0'], c['y_front'], c['z0']), (c['x1'], c['y_front'], c['z0']), (c['x1'], c['y_back'], c['z1']), (c['x0'], c['y_back'], c['z1'])]
        nrm = np.cross(np.subtract(top[1], top[0]), np.subtract(top[3], top[0]))
        nrm = -nrm / np.linalg.norm(nrm)     # facing up
        self.faces += quad(top, nrm, 0.92, 'console_top')
        self.faces += quad([(c['x0'], c['y0'], c['z0']), (c['x1'], c['y0'], c['z0']), (c['x1'], c['y_front'], c['z0']), (c['x0'], c['y_front'], c['z0'])], (0, 0, -1), 0.82, 'console')
        self.faces += quad([(c['x0'], c['y0'], c['z1']), (c['x0'], c['y0'], c['z0']), (c['x0'], c['y_front'], c['z0']), (c['x0'], c['y_back'], c['z1'])], (-1, 0, 0), 0.78, 'console')
        self.faces += quad([(c['x1'], c['y0'], c['z0']), (c['x1'], c['y0'], c['z1']), (c['x1'], c['y_back'], c['z1']), (c['x1'], c['y_front'], c['z0'])], (1, 0, 0), 0.78, 'console')
        # keys
        self.keys = []
        R, C = self.KEY_ROWS, self.KEY_COLS
        for r in range(R):
            for k in range(C):
                u0, u1 = (k + 0.12) / C, (k + 0.88) / C
                v0, v1 = (r + 0.15) / R, (r + 0.85) / R
                def P(u, v, lift=0.012):
                    x = c['x0'] + (c['x1'] - c['x0']) * u
                    z = c['z0'] + (c['z1'] - c['z0']) * v
                    y = c['y_front'] + (c['y_back'] - c['y_front']) * v + lift
                    return (x, y, z)
                self.keys.append(dict(r=r, k=k, P=P, u=(u0, u1), v=(v0, v1), n=nrm))
        # the chair: seat, back, legs (empty)
        cx, cz = 0.12, 3.35          # pulled out from the desk, a little off-centre: left, not tucked in
        self.chair = (cx, cz)
        self.faces += box(cx - 0.24, cx + 0.24, 0.44, 0.48, cz - 0.24, cz + 0.24, 0.9, 'chair')
        # ladder back: two posts and two rails, so the empty seat shows through
        for px in (cx - 0.24, cx + 0.20):
            self.faces += box(px, px + 0.04, 0.48, 1.02, cz - 0.27, cz - 0.23, 0.85, 'chair')
        for ry in (0.70, 0.94):
            self.faces += box(cx - 0.20, cx + 0.20, ry, ry + 0.07, cz - 0.265, cz - 0.235, 0.85, 'chair')
        for lx in (cx - 0.23, cx + 0.19):
            for lz in (cz - 0.23, cz + 0.19):
                self.faces += box(lx, lx + 0.04, 0.0, 0.44, lz, lz + 0.04, 0.75, 'chair')

    # ------------------------------------------------------------------ rendering
    @staticmethod
    def clip_near(C, near=0.05):
        """Sutherland-Hodgman against z = near in camera space."""
        out = []
        n = len(C)
        for i in range(n):
            a, b = C[i], C[(i + 1) % n]
            ina, inb = a[2] >= near, b[2] >= near
            if ina:
                out.append(a)
            if ina != inb:
                t = (near - a[2]) / (b[2] - a[2])
                out.append(a + (b - a) * t)
        return np.array(out) if len(out) >= 3 else None

    def render(self, cam, paper, tooth, t=0.0, key_glow=None, light_pos=(), window_img=None, line_w=1.0,
               ink=1.0, fill=1.0, tone_k=1.0, warm=(1.0, 0.72, 0.38), key_press=None, extra_faces=(), reveal=None):
        """paper: screen-space paper image (H, W, 3). key_glow: dict (r,k)->[0,1].
        light_pos: list of (world xyz, rgb, strength) lights that tint nearby faces.
        Returns image and a screen-space window mask."""
        out = paper.copy()
        lines = np.zeros((H_OUT, W_OUT), np.float32)
        win_mask = np.zeros((H_OUT, W_OUT), np.float32)
        items = []
        faces = list(self.faces) + list(extra_faces)
        for (P, n, tone, tag) in faces:
            C = cam.to_cam(P)
            # back-face cull for closed solids only (walls are always seen from inside)
            centre = P.mean(0)
            if tag not in ('floor', 'ceiling', 'wallL', 'wallR', 'back') and np.dot(n, cam.pos - centre) < 0:
                continue
            Cc = self.clip_near(C)
            if Cc is None:
                continue
            items.append((float(np.linalg.norm(cam.pos - centre)), Cc, n, tone, tag, centre))
        d_ct = [it[0] for it in items if it[4] == 'console_top']
        d_ct = d_ct[0] if d_ct else None
        kitems = []
        for item in self._keys(key_press):
            P, n, tone, tag = item
            C = cam.to_cam(P)
            Cc = self.clip_near(C)
            if Cc is not None and d_ct is not None:
                kitems.append((float(np.linalg.norm(cam.pos - P.mean(0))), Cc, n, tone, tag, P.mean(0)))
        kitems.sort(key=lambda it: -it[0])
        for i, it in enumerate(kitems):
            items.append((d_ct - 1e-4 * (i + 1),) + it[1:])
        items.sort(key=lambda it: -it[0])
        key_dir = np.array([0.4, 0.7, -0.6])
        key_dir /= np.linalg.norm(key_dir)
        warm = np.asarray(warm, np.float32)
        for d, Cc, n, tone, tag, centre in items:
            z = np.maximum(Cc[:, 2], 1e-4)
            sx = cam.cx + cam.f * Cc[:, 0] / z
            sy = cam.cy - cam.f * Cc[:, 1] / z
            pts = np.stack([sx, sy], 1)
            shade = (0.82 + 0.18 * max(0.0, float(n @ key_dir))) * tone
            shade = 1 - (1 - shade) * tone_k
            col = dim.PAPER * shade
            for (lp, lc, ls) in light_pos:
                dd = np.linalg.norm(centre - np.asarray(lp)) + 0.3
                col = col + np.asarray(lc) * ls * 0.045 / (dd * dd)
            if tag and tag.startswith('key'):
                g = 0.0 if key_glow is None else key_glow.get(tag, 0.0)
                col = col * (1 - 0.1 * g) + warm * 0.55 * g
            bx0 = int(max(0, np.floor(pts[:, 0].min()) - 2))
            by0 = int(max(0, np.floor(pts[:, 1].min()) - 2))
            bx1 = int(min(W_OUT, np.ceil(pts[:, 0].max()) + 2))
            by1 = int(min(H_OUT, np.ceil(pts[:, 1].max()) + 2))
            if bx1 <= bx0 or by1 <= by0:
                continue
            poly = ((pts - [bx0, by0]) * 16).astype(np.int64)
            if np.abs(poly).max() > 2 ** 30:
                continue
            m = np.zeros((by1 - by0, bx1 - bx0), np.float32)
            cv2.fillPoly(m, [poly.astype(np.int32)], 1.0, cv2.LINE_AA, shift=4)
            rv = 1.0 if reveal is None else float(reveal(centre, tag))
            if rv <= 0.001:
                continue
            o = out[by0:by1, bx0:bx1]
            pp = paper[by0:by1, bx0:bx1]
            mf = m * fill * min(1.0, rv * 1.5)
            o[:] = o * (1 - mf[:, :, None]) + (pp * (col / dim.PAPER)) * mf[:, :, None]
            lines[by0:by1, bx0:bx1] *= (1 - m * min(1.0, rv * 1.5))          # nearer faces hide farther lines
            pl = list(pts) + [pts[0]]
            if rv < 1.0:
                # the outline draws itself around the face
                L_ = np.cumsum([0] + [np.hypot(*(pl[i + 1] - pl[i])) for i in range(len(pl) - 1)])
                cut = rv * L_[-1]
                k = int(np.searchsorted(L_, cut))
                pl = pl[:max(2, k)]
            wid = line_w * (1.0 if not (tag and tag.startswith('key')) else 0.7)
            pencil_stroke(lines, pl, width=wid, jitter=0.25, seed=int(abs(centre[0] * 97 + centre[2] * 31)) % 9999)
        # the window: whatever is beyond it (computed from its projected quad)
        wx0, wx1, wy0, wy1 = self.WINDOW
        Pw = np.array([(wx0, wy1, self.D), (wx1, wy1, self.D), (wx1, wy0, self.D), (wx0, wy0, self.D)])
        Cw = cam.to_cam(Pw)
        if (Cw[:, 2] > 0.05).all():
            q, _ = cam.project(Pw)
            m = np.zeros((H_OUT, W_OUT), np.float32)
            cv2.fillPoly(m, [(q * 16).astype(np.int32)], 1.0, cv2.LINE_AA, shift=4)
            # occlusion by nearer geometry is approximated: the window is on the far wall
            win_mask = m * (1 - np.clip(self._occluders(cam), 0, 1))
        out = graphite(out, lines * ink, dim.GRAPHITE, tooth, strength=0.85)
        return out, win_mask

    def _occluders(self, cam):
        m = np.zeros((H_OUT, W_OUT), np.float32)
        for (P, n, tone, tag) in self.faces:
            if tag in ('floor', 'ceiling', 'wallL', 'wallR', 'back', 'sill'):
                continue
            C = cam.to_cam(P)
            Cc = self.clip_near(C)
            if Cc is None:
                continue
            z = np.maximum(Cc[:, 2], 1e-4)
            pts = np.stack([cam.cx + cam.f * Cc[:, 0] / z, cam.cy - cam.f * Cc[:, 1] / z], 1)
            cv2.fillPoly(m, [(pts * 16).astype(np.int32)], 1.0, cv2.LINE_AA, shift=4)
        return m

    def _keys(self, key_press=None):
        out = []
        for kd in self.keys:
            u0, u1 = kd['u']
            v0, v1 = kd['v']
            tag = f"key{kd['r']}_{kd['k']}"
            lift = 0.012 - (0.009 * key_press.get(tag, 0.0) if key_press else 0.0)
            P = kd['P']
            q = np.array([P(u0, v0, lift), P(u1, v0, lift), P(u1, v1, lift), P(u0, v1, lift)])
            out.append((q, kd['n'], 0.98, tag))
        return out

    def key_center(self, r, k, lift=0.02):
        kd = self.keys[r * self.KEY_COLS + k]
        u = sum(kd['u']) / 2
        v = sum(kd['v']) / 2
        return np.array(kd['P'](u, v, lift))
