"""Small 3D helpers: pinhole camera, planes and textured quads (homographies)."""
import cv2
import numpy as np
from common import *


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class PCam:
    """Pinhole camera. World: x right, y up, z forward. Screen: x right, y down."""

    def __init__(self, pos=(0, 0, 0), yaw=0.0, pitch=0.0, roll=0.0, f=1400.0, cx=W_OUT / 2, cy=H_OUT / 2):
        self.pos = np.asarray(pos, np.float64)
        self.R = rot_y(yaw) @ rot_x(pitch) @ rot_z(roll)   # camera->world
        self.f, self.cx, self.cy = f, cx, cy

    @staticmethod
    def look_at(pos, target, f=1400.0, roll=0.0):
        pos = np.asarray(pos, np.float64)
        d = np.asarray(target, np.float64) - pos
        yaw = np.arctan2(d[0], d[2])
        pitch = -np.arctan2(d[1], np.hypot(d[0], d[2]))
        return PCam(pos, yaw, pitch, roll, f)

    def to_cam(self, P):
        P = np.atleast_2d(np.asarray(P, np.float64))
        return (P - self.pos) @ self.R   # world -> camera (R orthonormal)

    def project(self, P):
        C = self.to_cam(P)
        z = np.maximum(C[:, 2], 1e-4)
        x = self.cx + self.f * C[:, 0] / z
        y = self.cy - self.f * C[:, 1] / z
        return np.stack([x, y], 1), C[:, 2]


def warp_quad(dst, tex, quad_screen, alpha=None, opacity=1.0, interp=cv2.INTER_LINEAR):
    """Paint texture `tex` (h, w, 3) onto screen quad (4x2, order TL TR BR BL)."""
    h, w = tex.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    H = cv2.getPerspectiveTransform(src, np.float32(quad_screen))
    c = cv2.warpPerspective(tex, H, (dst.shape[1], dst.shape[0]), flags=interp, borderMode=cv2.BORDER_CONSTANT)
    a_src = np.ones((h, w), np.float32) if alpha is None else alpha
    a = cv2.warpPerspective(a_src, H, (dst.shape[1], dst.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * opacity
    return dst * (1 - a[:, :, None]) + c * a[:, :, None], a, H


def raycast_globe(tex, out_w, out_h, cx, cy, R, lon0, lat0, lat_top=84.0, lat_bot=-72.0, lon_left=-22.0, bg=None):
    """Orthographic globe by inverse mapping (good for any radius)."""
    ys, xs = np.mgrid[0:out_h, 0:out_w].astype(np.float32)
    X = (xs - cx) / R
    Y = -(ys - cy) / R
    r2 = X * X + Y * Y
    vis = r2 < 1.0
    Z = np.sqrt(np.clip(1 - r2, 0, 1))
    a = np.deg2rad(lat0)
    # undo the view tilt
    y0 = Y * np.cos(a) + Z * np.sin(a)
    z0 = -Y * np.sin(a) + Z * np.cos(a)
    lat = np.rad2deg(np.arcsin(np.clip(y0, -1, 1)))
    lon = np.rad2deg(np.arctan2(X, z0)) + lon0
    th, tw = tex.shape[:2]
    u = ((lon - lon_left) % 360.0) / 360.0 * tw
    v = (lat_top - lat) / (lat_top - lat_bot) * th
    out = cv2.remap(tex, u.astype(np.float32), np.clip(v, 0, th - 1).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    # limb darkening
    shade = 0.55 + 0.45 * np.clip(Z, 0, 1) ** 0.6
    out = out * shade[:, :, None]
    m = gblur(vis.astype(np.float32), 0.8)
    if bg is None:
        bg = np.zeros_like(out)
    return bg * (1 - m[:, :, None]) + out * m[:, :, None], m, (u, v, vis)
