"""Layout sheets for the five memory cards that ChatGPT will draw (briefs/MEMORY_CARDS_BRIEF.md).

  python3 rev3/tools/memory_layouts.py              ->  rev3/briefs/memory_cards/<shot>_layout.png (1536x1024, annotated)
  python3 rev3/tools/memory_layouts.py --layers DIR ->  also the placeholder layers as <name>.png in DIR, in the same
                                                        files and names the finished artwork will use (tests the drop-in)

The drawings are the demo's placeholders. They fix layout only: where things sit, what is a separate layer, the pivot
or travel of each moving layer, and where the code adds light, steam, sparks and fire.
"""
import os
import sys

import cv2
import numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
import demo43 as D  # noqa: E402

CW, CH = 1536, 1024                                             # the card canvas (3:2); card units: x 0..1.5, y 0..1
OUT = os.path.join(R, 'briefs', 'memory_cards')
PAPER = D.paper(CW, CH, 7, tone=(0.86, 0.92, 0.95))


def mask_of(items):
    m = np.zeros((CH, CW), np.uint8)
    for it in items:
        if it[0] == 'shape':
            for q in it[1]:
                if q[0] == 'poly':
                    cv2.fillPoly(m, [np.int32(np.asarray(q[1]) * CH)], 255, cv2.LINE_AA)
                elif q[0] in ('ell', 'half'):
                    c = np.asarray(q[1]) * CH
                    a0, a1 = (0, 360) if q[0] == 'ell' else (180, 360)
                    rot = np.degrees(q[4]) if q[0] == 'ell' else 0
                    cv2.ellipse(m, (int(c[0]), int(c[1])), (int(q[2] * CH), int(q[3] * CH)), rot, a0, a1, 255, -1, cv2.LINE_AA)
                elif q[0] == 'cap':
                    cv2.line(m, tuple(np.int32(np.asarray(q[1]) * CH)), tuple(np.int32(np.asarray(q[2]) * CH)), 255,
                             max(1, int(2 * q[3] * CH)), cv2.LINE_AA)
        else:
            pts = np.asarray(it[1], np.float64)
            if it[3] and len(pts) > 2:
                pts = D.catmull(pts, 12)
            cv2.polylines(m, [np.int32(pts * CH)], False, 255, 5, cv2.LINE_AA)
    return cv2.dilate(m, np.ones((5, 5), np.uint8)).astype(np.float32) / 255.0


def layer(items, opaque=False):
    can = np.dstack([PAPER.copy(), np.ones((CH, CW), np.float32)])
    can = D.render_art(can, items, CH, 1.0, seed=5)
    if not opaque:
        can[..., 3] = mask_of(items)
    return can


def over(dst, lay):
    a = lay[..., 3:4]
    return dst * (1 - a) + lay[..., :3] * a


def u8(x):
    return np.ascontiguousarray(np.clip(x, 0, 255).astype(np.uint8))


def P(x, y):
    return int(x * CH), int(y * CH)


def label(img, txt, xy, col, scale=0.9):
    x, y = P(*xy)
    cv2.putText(img, txt, (x + 2, y + 2), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 5, cv2.LINE_AA)
    cv2.putText(img, txt, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, col, 2, cv2.LINE_AA)


def outline(img, a, col):
    cs, _ = cv2.findContours((a > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, cs, -1, col, 3, cv2.LINE_AA)


def arrow(img, p0, p1, col):
    cv2.arrowedLine(img, P(*p0), P(*p1), col, 4, cv2.LINE_AA, tipLength=0.25)


def code_mark(img, xy, txt):
    x, y = P(*xy)
    cv2.circle(img, (x, y), 16, (0, 140, 255), 3, cv2.LINE_AA)
    label(img, txt, (xy[0] + 0.02, xy[1] - 0.02), (0, 110, 230), 0.75)


BLUE, RED, GREEN, PURPLE = (200, 90, 0), (40, 40, 220), (40, 150, 40), (160, 40, 150)


def build():
    sheets, layers = {}, {}
    # M2 lullaby: room (bg) / cradle + baby + the parent's hand (rocks about the rocker)
    A = D.art_lullaby(22.5, 0.0)
    bg, cr = layer(A[:7], True), layer(A[7:])
    layers.update(lullaby_bg=bg, lullaby_cradle=cr)
    img = u8(over(bg[..., :3], cr) * 255)
    outline(img, cr[..., 3], RED)
    label(img, 'lullaby_cradle: cradle + baby + parent hand (one layer)', (0.40, 0.95), RED)
    cv2.drawMarker(img, P(0.78, 0.80), RED, cv2.MARKER_CROSS, 40, 4)
    label(img, 'pivot: rocks +/-4 deg', (0.80, 0.86), RED, 0.75)
    code_mark(img, (0.20, 0.36), 'lamp light: code')
    label(img, 'lullaby_bg: room, lamp, window, floor, faint cradle shadow on the wall', (0.03, 0.05), BLUE)
    sheets['lullaby'] = img
    # M3 farewell: platform (bg, incl. the platform hand) / train car with the door hand (slides left)
    A = D.art_farewell(24.0, 0.0, 0.0)
    bg, tr = layer(A[:3] + A[-6:], True), layer(A[3:-6])
    layers.update(farewell_bg=bg, farewell_train=tr)
    img = u8(over(bg[..., :3], tr) * 255)
    outline(img, tr[..., 3], RED)
    label(img, 'farewell_train: car, open door, lit window, a face, the hand from the door', (0.02, 0.97), RED, 0.8)
    arrow(img, (0.30, 0.50), (0.05, 0.50), RED)
    label(img, 'slides left, then pulls away', (0.04, 0.47), RED, 0.75)
    label(img, 'farewell_bg: platform, lamp post, the hand from the platform', (0.66, 0.05), BLUE, 0.75)
    code_mark(img, (0.875, 0.575), 'spark: code')
    sheets['farewell'] = img
    # D2 warm bowl: one layer; steam is code
    A = [it for it in D.art_heat(31.0) if not (it[0] == 'line' and len(it[1]) == 20)]
    bw = layer(A, True)
    layers.update(bowl=bw)
    img = u8(bw[..., :3] * 255)
    label(img, 'bowl: one layer (table, frosted window, bowl, an old hand left, a child\'s hand right)', (0.02, 0.05), BLUE, 0.75)
    code_mark(img, (0.75, 0.40), 'steam + warm light: code')
    sheets['bowl'] = img
    # D3 newborn: back (parent, blanket, parent's hand, the tiny hand closed) / baby (front, parallax) / tiny hand open
    back_i, baby_i = D.art_newborn(33.0, False)
    open_i = D.art_newborn(33.0, True)[0][-4:]
    bk, by, ho = layer(back_i, True), layer(baby_i), layer(open_i)
    layers.update(newborn_back=bk, newborn_baby=by, newborn_hand_open=ho)
    img = u8(over(bk[..., :3], by) * 255)
    outline(img, by[..., 3], RED)
    outline(img, ho[..., 3], GREEN)
    label(img, 'newborn_baby: head (front layer, own alpha)', (0.30, 0.31), RED, 0.75)
    label(img, 'newborn_hand_open: same tiny hand, fingers open (overlay)', (0.05, 0.96), GREEN, 0.75)
    label(img, 'newborn_back: parent\'s chest, blanket, parent\'s hand, tiny hand as a fist', (0.03, 0.05), BLUE, 0.75)
    sheets['newborn'] = img
    # D5 fire: hilltop (bg) / fist holding the striking stone (moves down 0.20 to strike)
    A = D.art_fire(39.5, False)
    bg, hd = layer(A[:62], True), layer(A[62:])
    layers.update(fire_bg=bg, fire_hand=hd)
    img = u8(over(bg[..., :3], hd) * 255)
    outline(img, hd[..., 3], RED)
    arrow(img, (1.25, 0.30), (1.25, 0.50), RED)
    label(img, 'fire_hand: fist + striking stone, raised; strikes down', (0.70, 0.12), RED, 0.75)
    label(img, 'fire_bg: night sky, hilltop, dry grass, lower stone, tinder', (0.03, 0.95), BLUE, 0.75)
    code_mark(img, (0.66, 0.665), 'sparks + flame: code')
    sheets['fire'] = img
    return sheets, layers


def main():
    D.PROF = D.glow_profile()
    os.makedirs(OUT, exist_ok=True)
    sheets, layers = build()
    for k, img in sheets.items():
        cv2.imwrite(os.path.join(OUT, k + '_layout.png'), np.clip(img, 0, 255).astype(np.uint8))
    if '--layers' in sys.argv:
        d = sys.argv[sys.argv.index('--layers') + 1]
        os.makedirs(d, exist_ok=True)
        for k, lay in layers.items():
            rgba = np.dstack([lay[..., :3], lay[..., 3]]) * 255
            cv2.imwrite(os.path.join(d, k + '.png'), np.clip(rgba, 0, 255).astype(np.uint8))
    print('wrote', sorted(sheets))


if __name__ == '__main__':
    main()
