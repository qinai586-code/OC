"""Compose head cels: base + eye overlays + mouth overlay -> RGBA array (+ neck anchor)."""
from functools import lru_cache
import numpy as np
from engine.px import parse_ascii
from art import heads as HD
from art import palette as PAL

CHAR = {
    'claude': dict(base=HD.CL, neck=HD.CL_NECK, eyes=HD.CL_EYES, mouth=HD.CL_MOUTH, key=PAL.CLAUDE, alias={}),
    'gpt': dict(base=HD.GP, neck=HD.GP_NECK, eyes=HD.GP_EYES, mouth=HD.GP_MOUTH, key=PAL.GPT, alias={'h': 'k'}),
}


def _stamp(rows, over, x0, y0, alias):
    for dy, r in enumerate(over):
        for dx, ch in enumerate(r):
            if ch == '.':
                continue
            y, x = y0 + dy, x0 + dx
            if 0 <= y < len(rows) and 0 <= x < len(rows[y]):
                rows[y][x] = alias.get(ch, ch)


@lru_cache(maxsize=512)
def head(who, view='F', eyes='open', mouth='none', look=0):
    """Return (rgba, neck_x, neck_y). look shifts irises by -1/0/+1 px (F view only, cheap eye darts)."""
    c = CHAR[who]
    rows = [list(r) for r in c['base'][view]]
    if view != 'B':
        boxes = c['eyes'][view]
        if view == 'F':
            l, r = HD.EYES[who][eyes]
            _stamp(rows, l, *boxes[0], c['alias'])
            _stamp(rows, r, *boxes[1], c['alias'])
        elif view == 'Q':
            l, _ = HD.EYES[who][eyes]
            _stamp(rows, l, *boxes[0], c['alias'])
            _stamp(rows, HD.EYES_NARROW[who][eyes], *boxes[1], c['alias'])
        else:
            _stamp(rows, HD.EYES_PROFILE[who].get(eyes, HD.EYES_PROFILE[who]['open']), *boxes[0], c['alias'])
        mx, my = c['mouth'][view]
        _stamp(rows, HD.MOUTHS[mouth], mx - 1, my, c['alias'])
        if look and view == 'F':
            # shift iris colours sideways inside each eye box
            for (bx, by) in boxes:
                for yy in range(by + 1, by + 3):
                    seg = rows[yy][bx:bx + 5]
                    inner = seg[1:4]
                    inner = (inner[1:] + inner[:1]) if look > 0 else (inner[-1:] + inner[:-1])
                    rows[yy][bx + 1:bx + 4] = inner
    arr = parse_ascii([''.join(r) for r in rows], c['key'])
    nx, ny = c['neck'][view]
    return arr, nx, ny
