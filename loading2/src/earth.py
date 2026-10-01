"""Human light, from real data: 7,300 populated places (Natural Earth), each lit in proportion
to its population, plus faint rural light over land, plus the road network between cities.
Every light knows its latitude/longitude, so it can live on a sphere, a plane, a line or a point."""
import json
import pickle
import cv2
import numpy as np
from lw import *

DATA = os.path.join(SCRATCH, 'data')


def land_mask(w=2048, h=1024):
    gj = json.load(open(os.path.join(DATA, 'ne_50m_land.geojson')))
    m = np.zeros((h, w), np.uint8)
    for f in gj['features']:
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            for ring in poly[:1]:
                pts = np.array([((lon + 180) / 360 * w, (90 - lat) / 180 * h) for lon, lat in ring], np.float32)
                cv2.fillPoly(m, [(pts * 16).astype(np.int32)], 1, cv2.LINE_AA, shift=4)
    return m


def coastlines(step=1):
    gj = json.load(open(os.path.join(DATA, 'ne_110m_land.geojson')))
    rings = []
    for f in gj['features']:
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            r = np.array(poly[0], np.float32)[::step]
            rings.append(r)  # (lon, lat)
    return rings


def build(seed=3):
    p = w2('earth.pkl')
    if os.path.exists(p):
        return pickle.load(open(p, 'rb'))
    rng = np.random.default_rng(seed)
    gj = json.load(open(os.path.join(DATA, 'ne_10m_populated_places_simple.geojson')))
    cities = []
    for f in gj['features']:
        pr = f['properties']
        pop = pr.get('pop_max') or pr.get('pop_min') or 0
        lon, lat = f['geometry']['coordinates'][:2]
        if pop and pop > 0:
            cities.append((lon, lat, float(pop)))
    cities = np.array(cities, np.float64)
    lons, lats, pops = [], [], []
    inten, size = [], []
    for lon, lat, pop in cities:
        n = int(np.clip((pop / 6e4) ** 0.55, 1, 90))
        rad = 0.10 + 0.55 * (pop / 1e7) ** 0.45            # degrees
        dl = rng.normal(0, rad, (n, 2)) * np.array([1 / max(0.2, np.cos(np.deg2rad(lat))), 1.0])
        core = np.exp(-(dl ** 2).sum(1) / (2 * rad * rad))
        lons.append(lon + dl[:, 0])
        lats.append(lat + dl[:, 1])
        inten.append((0.25 + 0.75 * core) * (0.35 + 0.65 * min(1.0, (pop / 2e6) ** 0.35)))
        pops.append(np.full(n, pop))
    lon = np.concatenate(lons)
    lat = np.clip(np.concatenate(lats), -85, 85)
    I = np.concatenate(inten).astype(np.float32)
    POP = np.concatenate(pops)
    # rural glow: sparse, faint, on land, denser near cities
    m = land_mask()
    h, w = m.shape
    dist = cv2.distanceTransform((1 - (cv2.dilate(m, np.ones((3, 3), np.uint8)) * 0)).astype(np.uint8), cv2.DIST_L2, 3)
    city_img = np.zeros((h, w), np.uint8)
    for lo, la, pp in cities:
        if pp > 5e4:
            city_img[int((90 - la) / 180 * h) % h, int((lo + 180) / 360 * w) % w] = 1
    dcity = cv2.distanceTransform(1 - city_img, cv2.DIST_L2, 5)
    prob = m * np.exp(-dcity / 18.0)
    prob = prob / prob.sum()
    k = rng.choice(h * w, size=26000, p=prob.ravel())
    ry, rx = np.divmod(k, w)
    rlon = (rx + rng.random(len(k))) / w * 360 - 180
    rlat = 90 - (ry + rng.random(len(k))) / h * 180
    lon = np.concatenate([lon, rlon])
    lat = np.concatenate([lat, rlat])
    I = np.concatenate([I, rng.uniform(0.05, 0.16, len(k)).astype(np.float32)])
    POP = np.concatenate([POP, np.zeros(len(k))])
    # roads: link big cities to their nearest big neighbours
    big = cities[cities[:, 2] > 4e5]
    roads = []
    for i, (lo, la, pp) in enumerate(big):
        d = np.hypot((big[:, 0] - lo) * np.cos(np.deg2rad(la)), big[:, 1] - la)
        d[i] = 1e9
        for j in np.argsort(d)[:2]:
            if d[j] < 9.0 and i < j or (d[j] < 9.0 and j not in [int(x) for x in np.argsort(np.hypot((big[:, 0] - big[j, 0]) * np.cos(np.deg2rad(big[j, 1])), big[:, 1] - big[j, 1]))[:3]]):
                roads.append((lo, la, big[j, 0], big[j, 1]))
    E = dict(lon=lon.astype(np.float32), lat=lat.astype(np.float32), I=I, pop=POP.astype(np.float32),
             cities=cities.astype(np.float32), roads=np.array(roads, np.float32))
    pickle.dump(E, open(p, 'wb'))
    return E


# ---------------------------------------------------------------------------------- placements
def on_sphere(lon, lat, R=1.0, yaw=0.0, pitch=0.0, center=(0, 0, 0)):
    """Earth with longitude `yaw` (deg) facing -z (toward a camera on -z) and tilted by pitch."""
    lo = np.deg2rad(lon - yaw)
    la = np.deg2rad(lat)
    x = np.cos(la) * np.sin(lo)
    y = np.sin(la)
    z = -np.cos(la) * np.cos(lo)
    P = np.stack([x, y, z], 1) * R
    P = P @ rot_x(np.deg2rad(pitch)).T
    return P + np.asarray(center)


def on_plane(lon, lat, scale=1.0, yaw=0.0, center=(0, 0, 0), R=None):
    """Equirectangular map in a plane facing -z (x right, y up), centred on longitude yaw."""
    lo = ((lon - yaw + 180) % 360) - 180
    x = np.deg2rad(lo) * scale
    y = np.deg2rad(lat) * scale
    P = np.stack([x, y, np.zeros_like(x)], 1)
    if R is not None:
        P = P @ R.T
    return P + np.asarray(center)


def facing(P, R):
    """Visibility weight for sphere points (front hemisphere bright, back dim)."""
    n = P / (np.linalg.norm(P, axis=1, keepdims=True) + 1e-9)
    return n


def great_arc(lo1, la1, lo2, la2, n=24):
    def xyz(lo, la):
        lo, la = np.deg2rad(lo), np.deg2rad(la)
        return np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
    a, b = xyz(lo1, la1), xyz(lo2, la2)
    om = np.arccos(np.clip(a @ b, -1, 1))
    if om < 1e-6:
        return np.array([[lo1, la1], [lo2, la2]])
    ts = np.linspace(0, 1, n)
    P = (np.sin((1 - ts) * om)[:, None] * a + np.sin(ts * om)[:, None] * b) / np.sin(om)
    lat = np.rad2deg(np.arcsin(P[:, 2]))
    lon = np.rad2deg(np.arctan2(P[:, 1], P[:, 0]))
    return np.stack([lon, lat], 1)
