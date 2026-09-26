"""Close-up portraits: the canonical sprite (same pose system) upscaled with Scale2x, then
hand-drawn 2x eyes and mouths stamped on. Guarantees close-ups match the full-body design."""
from functools import lru_cache
import numpy as np
from engine.px import parse_ascii, Sprite, ascii_block as A
from engine.scalex import scale2x
from art.body import render, make_pose, AX, AY, NECK_Y
from art import heads as HD
from art import palette as PAL

KEY = {'claude': PAL.CLAUDE, 'gpt': PAL.GPT}

# 10 x 8 left-eye boxes ('.' = skin). Right eye = mirror with highlight kept on the left.
E2 = {}
E2['claude'] = {
    'open': A("""
        ..........
        .eeeeeeee.
        eeeeeeeeee
        .eAwwaaAe.
        .eawwaaAe.
        .eaauuaae.
        ..eauuae..
        ...eeee...
        """),
    'calm': A("""
        ..........
        ..........
        .eeeeeeee.
        eeeeeeeeee
        .eAwwaaAe.
        .eaauuaae.
        ..eaaaae..
        ...eeee...
        """),
    'wide': A("""
        ..eeeeee..
        .eeeeeeee.
        .ewaaaawe.
        .ewawAAwe.
        .ewaAAawe.
        .ewwuuwwe.
        ..ewwwwe..
        ...eeee...
        """),
    'worried': A("""
        ......eee.
        ...eeeeeee
        .eeAAAAAe.
        .eAwwaaAe.
        .eawwaaAe.
        .eaauuaae.
        ..eauuae..
        ...eeee...
        """),
    'closed': A("""
        ..........
        ..........
        ..........
        ..........
        ee........
        .eeeeeeee.
        ...eeeeee.
        ..........
        """),
    'happy': A("""
        ..........
        ..........
        ...eeee...
        ..eeeeee..
        .ee....ee.
        .e......e.
        ..........
        ..........
        """),
    'side': A("""
        ..........
        .eeeeeeee.
        eeeeeeeeee
        .eaaAwwAe.
        .eaaAwwae.
        .eaaauuae.
        ..eaauae..
        ...eeee...
        """),
    'down': A("""
        ..........
        ..........
        ..........
        .eeeeeeee.
        eeeeeeeeee
        .eAaauuAe.
        ..eeeeee..
        ..........
        """),
}
E2['gpt'] = {
    'open': A("""
        ..eeeeee..
        .eeeeeeeee
        eeaAAAAAe.
        .eawwAAae.
        .eawwaaAe.
        .eaaIIaae.
        ..eaIIae..
        ...eeee...
        """),
    'calm': A("""
        ..........
        ..........
        .eeeeeeeee
        eeaAAAAAe.
        .eawwaaAe.
        .eaaIIaae.
        ..eaIIae..
        ...eeee...
        """),
    'sharp': A("""
        ..........
        ..........
        .eeeeeeeee
        eeAwwaaAe.
        .eaaIIaAe.
        ..eeeeee..
        ..........
        ..........
        """),
    'wide': A("""
        ..eeeeee..
        .eeeeeeee.
        .ewaaaawe.
        .ewawAAwe.
        .ewaAAawe.
        .ewwIIwwe.
        ..ewwwwe..
        ...eeee...
        """),
    'worried': A("""
        ......eee.
        ...eeeeeee
        .eeAAAAAe.
        .eawwaaAe.
        .eawwaaAe.
        .eaaIIaae.
        ..eaIIae..
        ...eeee...
        """),
    'closed': A("""
        ..........
        ..........
        ..........
        ..........
        ee........
        .eeeeeeee.
        ...eeeeee.
        ..........
        """),
    'happy': A("""
        ..........
        ..........
        ...eeee...
        ..eeeeee..
        .ee....ee.
        .e......e.
        ..........
        ..........
        """),
    'side': A("""
        ..eeeeee..
        .eeeeeeeee
        eeaAAAAAe.
        .eaaAwwae.
        .eaaAwwae.
        .eaaaIIae.
        ..eaaIae..
        ...eeee...
        """),
    'down': A("""
        ..........
        ..........
        ..........
        .eeeeeeeee
        eeeeeeeeee
        .eaAAIIae.
        ..eeeeee..
        ..........
        """),
    'glow': A("""
        ..eeeeee..
        .eeeeeeeee
        eeIIIIIIe.
        .eIwwIIIe.
        .eIwwwwIe.
        .eIIwwIIe.
        ..eIIIIe..
        ...eeee...
        """),
}
M2 = {  # 6 x 4 mouths ('.' = skin)
    'none': A("""
        ......
        """),
    'small': A("""
        ......
        ..mm..
        """),
    'flat': A("""
        ......
        .mmmm.
        """),
    'smile': A("""
        .m..m.
        ..mm..
        """),
    'grin': A("""
        mmmmmm
        .MMMM.
        ..mm..
        """),
    'open': A("""
        ..mm..
        .mMMm.
        ..mm..
        """),
    'o': A("""
        ..mm..
        .mMMm.
        .mMMm.
        ..mm..
        """),
    'shout': A("""
        .mmmm.
        mMMMMm
        mM99Mm
        .mmmm.
        """),
    'frown': A("""
        ..mm..
        .m..m.
        """),
    'wavy': A("""
        ......
        .m.m.m
        m.m.m.
        """),
    'chew': A("""
        .mmmm.
        .m..m.
        """),
}


def _mirror(rows):
    out = []
    for r in rows:
        R = list(r[::-1])
        if 'w' in R:
            n = R.count('w')
            idx = [q for q, c in enumerate(R) if c == 'w']
            # move highlight run to the left side of the iris
            R = [('a' if c == 'w' else c) for c in R]
            iris = [q for q, c in enumerate(R) if c in 'aAIu']
            for q in iris[:n]:
                R[q] = 'w'
        out.append(''.join(R))
    return out


def _stamp(a, rows, x0, y0, key):
    skin = key['S']
    for dy, r in enumerate(rows):
        for dx, ch in enumerate(r):
            y, x = y0 + dy, x0 + dx
            if not (0 <= y < a.shape[0] and 0 <= x < a.shape[1]):
                continue
            col = skin if ch == '.' else key[ch]
            if a[y, x, 3] == 0:
                continue
            c = col.lstrip('#')
            a[y, x] = (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


HEAD_TOP = 26  # sprite rows above the neck included in the bust


@lru_cache(maxsize=256)
def bust(who, view='Q', eyes='open', mouth='small', blush=False, pose_key=None, bottom=-30):
    """Scale2x bust (head + shoulders) as a Sprite anchored at the neck point (x2 coords)."""
    from art.headkit import CHAR
    p = make_pose(view, eyes='blank', mouth='none')
    if pose_key:
        p.update(dict(pose_key))
    spr = render(who, p)
    top = AY + NECK_Y - HEAD_TOP
    crop = spr.arr[top:AY + bottom].copy()
    big = scale2x(crop)
    key = KEY[who]
    # eye / mouth positions: head cel is placed with its neck pixel at (AX + lean + hx, AY + NECK_Y + bob + hy)
    c = CHAR[who]
    nx, ny = c['neck'][view]
    hx = AX + p['lean'] + p['hx'] - nx
    hy = AY + NECK_Y + p['bob'] + p['hy'] - ny - top
    if view != 'B':
        boxes = c['eyes'][view]
        L = E2[who][eyes]
        if view == 'F':
            _stamp(big, L, 2 * (hx + boxes[0][0]), 2 * (hy + boxes[0][1]), key)
            _stamp(big, _mirror(L), 2 * (hx + boxes[1][0]), 2 * (hy + boxes[1][1]), key)
        elif view == 'Q':
            _stamp(big, L, 2 * (hx + boxes[0][0]), 2 * (hy + boxes[0][1]), key)
            R = [r[2:] for r in L]
            _stamp(big, R, 2 * (hx + boxes[1][0]), 2 * (hy + boxes[1][1]), key)
        mx, my = c['mouth'][view]
        _stamp(big, M2[mouth], 2 * (hx + mx) - 3 + (1 if view == 'Q' else 0), 2 * (hy + my) - 1, key)
    return Sprite(big, 2 * AX, 2 * (AY + NECK_Y - top))
