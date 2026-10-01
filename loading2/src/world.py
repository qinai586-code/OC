"""World elements, all made of light."""
import json
from lw import *
from earth import build as earth_build, on_sphere, on_plane, great_arc
from acting import *

EARTH = earth_build()
OFF = json.load(open(w2('chars', 'offsets.json')))
STARS = starfield(7000, 900.0, 1)
ARECIBO = np.array([int(c) for c in open(os.path.join(ROOT2, 'data', 'arecibo.txt')).read().strip()], np.uint8).reshape(73, 23)

PLANE_R = rot_x(-np.pi / 2)       # map plane lying flat: its north (the bright half) toward the camera


def city_col(n, seed=0):
    rng = np.random.default_rng(seed)
    k = rng.random(n)[:, None].astype(np.float32)
    return AMBER * (1 - k) * 0.9 + WARM * k


CITY_COL = city_col(len(EARTH['lon']))


# ---------------------------------------------------------------------------------- ground of lights
def ground_points(H=1.0, z0=0.6, scale=3.2, yaw=15.0):
    """The map of human light lying flat below the horizon line."""
    P = on_plane(EARTH['lon'], EARTH['lat'] - 62, scale, yaw, (0, 0, 0), PLANE_R)
    P = P + np.array([0, -H, z0])
    return P


def draw_stars(fr, t, amp=1.0, hold=0.0, center=(0, 0, 0), mask=None):
    b = twinkle(STARS, t, hold) * amp
    if mask is not None:
        b = b * mask
    fr.points(STARS['P'] + np.asarray(center), STARS['col'], b * 0.9)


def ledge_line(fr, y=0.0, z=0.0, inten=0.35, x=60.0, col=None):
    fr.segments([(-x, y, z)], [(x, y, z)], WARM * 0.55 if col is None else col, inten, width=1.2)


# ---------------------------------------------------------------------------------- the two witnesses
def plate_card(name, z=0.0, ref_y=1690.0, scale=1000.0, cx=1536.0):
    x0, y0, x1, y1 = OFF[name]
    pos = (((x0 + x1) / 2 - cx) / scale, (ref_y - y1) / scale, z)
    return pos, (y1 - y0) / scale


def witnesses(fr, t, names=('kv1_A', 'kv1_B'), z=0.0, lights=(), ambient=0.55, rim=None, sway=2.5,
              wind=0.0, opacity=1.0, extra=None, scale=1.0, dx=0.0):
    cards = []
    for i, n in enumerate(names):
        img = extra[i] if extra is not None else secondary(char(n), t + i * 1.3, sway=sway, wind=wind, seed=i * 2.1)
        pos, h = plate_card(n, z)
        pos = (pos[0] * scale + dx, pos[1] * scale, z)
        r = Card(img).render(fr, pos, h * scale, ambient=ambient, lights=lights, rim=rim, opacity=opacity)
        if r is not None:
            cards.append(r[:2])
    return cards


# ---------------------------------------------------------------------------------- lattice, forest
def lattice(n=11, span=40.0, center=(0, 0, 0)):
    g = np.linspace(-span, span, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing='ij')
    return np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1) + np.asarray(center)


def forest_lines(n=420, seed=5, depth=(4, 70), width=60.0, ground=-1.6):
    rng = np.random.default_rng(seed)
    z = rng.uniform(*depth, n)
    x = rng.uniform(-width, width, n) * (0.3 + z / depth[1])
    h = rng.uniform(4, 11, n)
    A = np.stack([x, np.full(n, ground), z], 1)
    B = A + np.stack([np.zeros(n), h, np.zeros(n)], 1)
    return A, B


# ---------------------------------------------------------------------------------- the room
def box_edges(x0, x1, y0, y1, z0, z1):
    c = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
    E = []
    for i in range(8):
        for j in range(i + 1, 8):
            if np.sum(np.abs(c[i] - c[j]) > 1e-9) == 1:
                E.append((c[i], c[j]))
    return E


def room_edges():
    E = []
    E += box_edges(-3, 3, 0, 3, 0, 6.5)
    wx0, wx1, wy0, wy1 = -1.45, 0.05, 1.05, 2.45
    E += [((wx0, wy0, 6.5), (wx1, wy0, 6.5)), ((wx1, wy0, 6.5), (wx1, wy1, 6.5)), ((wx1, wy1, 6.5), (wx0, wy1, 6.5)),
          ((wx0, wy1, 6.5), (wx0, wy0, 6.5)), (((wx0 + wx1) / 2, wy0, 6.5), ((wx0 + wx1) / 2, wy1, 6.5))]
    E += box_edges(-1.2, 1.2, 0.72, 0.78, 4.2, 5.1)
    for lx in (-1.15, 1.09):
        for lz in (4.25, 4.99):
            E += box_edges(lx, lx + 0.06, 0.0, 0.72, lz, lz + 0.06)
    E += box_edges(-0.8, 0.8, 0.78, 0.86, 4.35, 4.85)
    cx, cz = 0.12, 3.35
    E += box_edges(cx - 0.24, cx + 0.24, 0.44, 0.48, cz - 0.24, cz + 0.24)
    for px in (cx - 0.24, cx + 0.20):
        E += box_edges(px, px + 0.04, 0.48, 1.02, cz - 0.27, cz - 0.23)
    for ry in (0.70, 0.94):
        E += [((cx - 0.20, ry, cz - 0.25), (cx + 0.20, ry, cz - 0.25))]
    for lx in (cx - 0.23, cx + 0.19):
        for lz in (cz - 0.23, cz + 0.19):
            E += [((lx + 0.02, 0, lz + 0.02), (lx + 0.02, 0.44, lz + 0.02))]
    A = np.array([e[0] for e in E], float)
    B = np.array([e[1] for e in E], float)
    return A, B


def keys():
    """Centres of the 4 x 12 keys on the console top, and their small square outlines."""
    C = []
    for r in range(4):
        for k in range(12):
            x = -0.8 + 1.6 * (k + 0.5) / 12
            z = 4.35 + 0.5 * (r + 0.5) / 4
            C.append((x, 0.87, z))
    return np.array(C)


def key_squares(C, s=0.05):
    A, B = [], []
    for c in C:
        p = [c + np.array(d) for d in ((-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s))]
        for i in range(4):
            A.append(p[i])
            B.append(p[(i + 1) % 4])
    return np.array(A), np.array(B)


ROOM_A, ROOM_B = room_edges()
KEYS = keys()
KEYSQ = key_squares(KEYS)
CHAIR = np.array([0.12, 0.75, 3.35])


def draw_room(fr, inten=0.5, col=None, reveal=None):
    c = (STAR * 0.6 + WARM * 0.4) if col is None else col
    I = np.full(len(ROOM_A), inten, np.float32)
    if reveal is not None:
        I = I * reveal
    fr.segments(ROOM_A, ROOM_B, c, I, width=1.0)


# ---------------------------------------------------------------------------------- signals
def arecibo_points(center, cell=0.06, up=(0, 1, 0), right=(1, 0, 0)):
    ys, xs = np.nonzero(ARECIBO)
    up, right = np.asarray(up, float), np.asarray(right, float)
    P = np.asarray(center, float) + (xs[:, None] - 11) * cell * right[None, :] - (ys[:, None] - 36) * cell * up[None, :]
    return P, ys, xs


def tick_ring(fr, center, R, n, alive, t, col=RED, inten=1.0, rot=0.0, normal_axis='z'):
    A, B = [], []
    for i in range(n):
        if not alive[i]:
            continue
        a = rot + 2 * np.pi * i / n
        d = np.array([np.cos(a), np.sin(a), 0.0])
        A.append(np.asarray(center) + d * R)
        B.append(np.asarray(center) + d * R * 0.93)
    if A:
        fr.segments(np.array(A), np.array(B), col, inten, width=2.0)


def ground_roads(H=1.0, z0=0.6, scale=3.2, yaw=15.0, seg=10):
    """Roads between cities on the same flat map as ground_points (polylines)."""
    out = []
    for lo1, la1, lo2, la2 in EARTH['roads']:
        arc = great_arc(lo1, la1, lo2, la2, seg)
        P = on_plane(arc[:, 0], arc[:, 1] - 62, scale, yaw, (0, 0, 0), PLANE_R) + np.array([0, -H, z0])
        if np.abs(np.diff(P[:, 0])).max() < 1.5:
            out.append(P)
    return out


def bright_cities(k=60):
    """Indices of the k brightest lights (big cities)."""
    return np.argsort(-EARTH['I'])[:k]
