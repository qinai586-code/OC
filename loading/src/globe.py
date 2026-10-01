"""The Earth as a real sphere textured with the painted flat map (BG0b), so it can
rotate, show civilisation's lights arriving over time, and physically unroll into the
flat map (3D -> 2D) when the sheet touches it.

Rendering is forward splatting of a dense lat/lon grid with a z-buffer, which lets us
interpolate every surface point between its sphere position and its map position.
"""
import cv2
import numpy as np
from common import *

LAT_TOP, LAT_BOT = 84.0, -72.0      # latitude range painted in BG0b
LON_LEFT = -22.0                     # longitude at the map's left edge (painting wraps 360)


class Globe:
    def __init__(self, tex, lights=None, grid_w=2400):
        self.tex = tex
        th, tw = tex.shape[:2]
        gw = grid_w
        gh = int(gw * (LAT_TOP - LAT_BOT) / 360.0)
        self.gw, self.gh = gw, gh
        u = (np.arange(gw) + 0.5) / gw
        v = (np.arange(gh) + 0.5) / gh
        U, V = np.meshgrid(u, v)
        self.lon = np.deg2rad(LON_LEFT + U * 360.0).astype(np.float32)
        self.lat = np.deg2rad(LAT_TOP + V * (LAT_BOT - LAT_TOP)).astype(np.float32)
        self.U, self.V = U.astype(np.float32), V.astype(np.float32)
        self.col = cv2.resize(tex, (gw, gh), interpolation=cv2.INTER_AREA)
        self.lights = None if lights is None else cv2.resize(lights, (gw, gh), interpolation=cv2.INTER_AREA)

    def sphere_xyz(self, lon0, lat0):
        """Unit-sphere coords in camera space for a view centred on (lon0, lat0) [deg]."""
        lo = self.lon - np.deg2rad(lon0)
        x = np.cos(self.lat) * np.sin(lo)
        y = np.sin(self.lat)
        z = np.cos(self.lat) * np.cos(lo)
        a = np.deg2rad(lat0)
        y2 = y * np.cos(a) - z * np.sin(a)
        z2 = y * np.sin(a) + z * np.cos(a)
        return x, y2, z2

    def render(self, out_w, out_h, cx, cy, R, lon0=150.0, lat0=20.0, flat=0.0, flat_origin=(0.0, 0.0),
               flat_center=None, flat_scale=None, light_gain=None, light_time=None, bg=None, spread=0.55):
        """flat: 0 = sphere, 1 = fully unrolled map. flat_origin = (u,v) of the contact point:
        the collapse propagates outward from it. light_time: per-texel arrival times (gw x gh) to
        gate lights; light_gain(t) handled by caller via light_time threshold."""
        x, y, z = self.sphere_xyz(lon0, lat0)
        sx = cx + R * x
        sy = cy - R * y
        sz = z
        if flat > 0:
            if flat_center is None:
                flat_center = (cx, cy)
            if flat_scale is None:
                flat_scale = 2 * np.pi * R / self.gw  # preserve equator length
            # map positions: keep the map's centre longitude under the view centre
            du = ((self.lon - np.deg2rad(lon0) + np.pi) % (2 * np.pi) - np.pi) / (2 * np.pi) * self.gw
            dv = (self.V - (LAT_TOP - lat0) / (LAT_TOP - LAT_BOT)) * self.gh
            mx = flat_center[0] + du * flat_scale
            my = flat_center[1] + dv * flat_scale
            # propagation from contact point
            d = np.hypot((self.U - flat_origin[0]) * 2, (self.V - flat_origin[1]))
            d = d / d.max()
            g = np.clip((flat * (1 + spread) - d * spread), 0, 1)
            g = g * g * (3 - 2 * g)
            sx = sx * (1 - g) + mx * g
            sy = sy * (1 - g) + my * g
            sz = sz * (1 - g) + 1.5 * g
        vis = sz > -0.02
        col = self.col
        if self.lights is not None and light_time is not None:
            lm = self.lights * light_time
        else:
            lm = self.lights
        # splat with z-order
        xs = np.round(sx[vis]).astype(np.int32)
        ys = np.round(sy[vis]).astype(np.int32)
        zs = sz[vis]
        ok = (xs >= 0) & (xs < out_w) & (ys >= 0) & (ys < out_h)
        xs, ys, zs = xs[ok], ys[ok], zs[ok]
        order = np.argsort(zs, kind='stable')
        xs, ys = xs[order], ys[order]
        c = col[vis][ok][order]
        out = np.zeros((out_h, out_w, 3), np.float32) if bg is None else bg.copy()
        cov = np.zeros((out_h, out_w), np.float32)
        out[ys, xs] = c
        cov[ys, xs] = 1
        lo = None
        if lm is not None:
            lo = np.zeros((out_h, out_w), np.float32)
            lv = lm[vis][ok][order]
            lo[ys, xs] = lv
        # close pin holes
        hole = (cov == 0).astype(np.uint8)
        if hole.any():
            filled = cv2.dilate(out, np.ones((3, 3), np.uint8))
            cov_d = cv2.dilate(cov, np.ones((3, 3), np.uint8))
            m = (hole.astype(bool) & (cov_d > 0))
            out[m] = filled[m]
            cov[m] = 1
            if lo is not None:
                lo2 = cv2.dilate(lo, np.ones((3, 3), np.uint8))
                lo[m] = lo2[m]
        return out, cov, lo
