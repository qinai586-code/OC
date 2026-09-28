"""Style test: the apartment block at 3 a.m. (storyboard shots 4, 5 and 9).

Only the windows where a screen is lit are fully painted; the rest of the
building falls back to flat colour, pencil and bare paper.
"""
import sys
from painter import Scene, W, H

s = Scene(seed=7)

# long construction lines across the whole page
for y in (110, 930):
    s.construction([(0, y), (W, y)])
for x in (160, 1760):
    s.construction([(x, 0), (x, H)])

SKY, BRICK, BRICK2, CORNICE = (27, 31, 59), (58, 46, 66), (50, 40, 58), (40, 34, 50)
DARKWIN, SILL, WALK, IRON = (22, 24, 38), (70, 62, 78), (38, 40, 56), (18, 18, 26)

s.rect((0, 0, W, 108), SKY, outline=False)
s.rect((160, 92, 1760, 930), BRICK)
s.rect((140, 80, 1780, 118), CORNICE)
s.rect((0, 930, W, H), WALK)
s.line([(0, 1000), (W, 1000)])  # kerb

# brick courses, sketched
for y in range(140, 930, 26):
    s.line([(165, y), (1755, y)], weight=45, passes=1, overshoot=0)

cols = [230 + 228 * i for i in range(7)]
rows = [150 + 152 * j for j in range(5)]
WW, WH = 124, 118

# who is awake: (col, row) -> scene inside
awake = {
    (1, 1): 'student', (4, 0): 'old_man', (5, 2): 'parent',
    (2, 3): 'nurse', (6, 1): 'crying', (3, 4): 'cat_laptop',
}

SCREEN = (205, 228, 255)
LAMP = (255, 196, 120)
ROOM_DIM = (40, 48, 82)
ROOM_WARM = (120, 82, 58)
SIL = (14, 15, 24)


def person(x, y, scale=1.0, hunched=False):
    """A seated silhouette facing a screen on the left; x,y = seat point."""
    k = scale
    hy = y - (62 if not hunched else 50) * k
    s.ellipse((x - 13 * k, hy - 14 * k, x + 13 * k, hy + 14 * k), SIL)
    tilt = 8 * k if hunched else 0
    s.poly([(x - 22 * k, y), (x - 18 * k - tilt, hy + 12 * k), (x + 16 * k - tilt, hy + 12 * k), (x + 24 * k, y)], SIL, outline=False)
    # the screen lights the edge of the face and shoulder nearest to it
    s.ellipse((x - 14 * k, hy - 11 * k, x - 7 * k, hy + 10 * k), (150, 175, 215))
    s.poly([(x - 21 * k, y - 2), (x - 18 * k - tilt, hy + 13 * k), (x - 13 * k - tilt, hy + 13 * k), (x - 16 * k, y - 2)], (70, 85, 120), outline=False)


for i, cx in enumerate(cols):
    for j, cy in enumerate(rows):
        box = (cx - WW // 2, cy, cx + WW // 2, cy + WH)
        s.rect((box[0] - 8, box[3], box[2] + 8, box[3] + 10), SILL)  # sill
        what = awake.get((i, j))
        if what is None:
            s.rect(box, DARKWIN)
            s.line([(cx, box[1]), (cx, box[3])], weight=90, passes=1)  # mullion
            continue
        warm = what in ('parent', 'cat_laptop')
        s.rect(box, ROOM_WARM if warm else ROOM_DIM)
        x0, y0, x1, y1 = box
        if what == 'student':
            s.rect((x0 + 8, y1 - 30, x1 - 8, y1 - 24), (70, 55, 50))            # desk
            s.rect((x0 + 18, y1 - 58, x0 + 52, y1 - 30), SCREEN, outline=False)  # laptop
            s.glow((x0 + 18, y1 - 58, x0 + 52, y1 - 30), SCREEN, 1.3)
            s.rect((x1 - 34, y1 - 46, x1 - 14, y1 - 30), (150, 90, 70))         # books
            person(x0 + 80, y1 - 26, 0.8)
        elif what == 'old_man':
            s.rect((x0 + 10, y1 - 70, x0 + 56, y1 - 36), SCREEN, outline=False)  # monitor
            s.glow((x0 + 10, y1 - 70, x0 + 56, y1 - 36), SCREEN, 1.2)
            s.rect((x0 + 8, y1 - 30, x1 - 8, y1 - 24), (70, 55, 50))
            person(x0 + 86, y1 - 26, 0.8)
            s.rect((x0 + 72, y1 - 76, x0 + 100, y1 - 72), (200, 200, 210), outline=False)  # glasses glint
        elif what == 'parent':
            s.rect((x0 + 20, y1 - 30, x1 - 20, y1 - 10), (90, 60, 50))  # armchair
            person(cx, y1 - 14, 0.9)
            s.ellipse((cx - 20, y1 - 60, cx + 8, y1 - 44), (235, 225, 210))  # swaddled baby
            s.rect((cx + 14, y1 - 58, cx + 24, y1 - 42), SCREEN, outline=False)  # phone
            s.glow((cx + 14, y1 - 58, cx + 24, y1 - 42), SCREEN, 0.8)
            s.glow((x0, y0, x1, y1), LAMP, 0.35)
        elif what == 'nurse':
            s.rect((x0 + 6, y1 - 34, x1 - 6, y1 - 12), (200, 205, 215))  # bed edge
            s.ellipse((cx - 13, y1 - 96, cx + 13, y1 - 68), SIL)
            s.poly([(cx - 24, y1 - 30), (cx - 18, y1 - 72), (cx + 18, y1 - 72), (cx + 24, y1 - 30)], (46, 128, 132), outline=False)  # teal scrubs
            s.rect((cx - 6, y1 - 64, cx + 6, y1 - 50), SCREEN, outline=False)  # phone
            s.glow((cx - 6, y1 - 64, cx + 6, y1 - 50), SCREEN, 1.0)
        elif what == 'crying':
            s.rect((x0 + 10, y1 - 22, x1 - 10, y1 - 8), (60, 58, 80))  # floor cushion
            person(cx, y1 - 10, 0.85, hunched=True)
            s.rect((cx - 30, y1 - 44, cx - 20, y1 - 30), SCREEN, outline=False)  # phone in lap
            s.glow((cx - 30, y1 - 44, cx - 20, y1 - 30), SCREEN, 0.9)
        elif what == 'cat_laptop':
            s.rect((x0 + 8, y1 - 30, x1 - 8, y1 - 24), (90, 70, 55))  # kitchen table
            s.rect((x0 + 22, y1 - 54, x0 + 54, y1 - 30), SCREEN, outline=False)
            s.glow((x0 + 22, y1 - 54, x0 + 54, y1 - 30), SCREEN, 1.1)
            person(x0 + 84, y1 - 26, 0.8)
            s.ellipse((x1 - 30, y1 - 22, x1 - 8, y1 - 4), SIL)  # cat on the sill
            s.poly([(x1 - 28, y1 - 18), (x1 - 26, y1 - 28), (x1 - 22, y1 - 20)], SIL, outline=False)
            s.glow((x0, y0, x1, y1), LAMP, 0.25)
        s.line([(cx, y0), (cx, y1)], weight=60, passes=1)  # mullion
        s.look(cx, cy + WH / 2, 105)

# fire escape between columns 4 and 5, sketched only (nobody is looking there)
for j, cy in enumerate(rows[:-1]):
    y = cy + WH + 14
    s.rect((cols[4] + 40, y, cols[5] - 40, y + 6), IRON)
    s.line([(cols[4] + 40, y - 40), (cols[5] - 40, y - 40)], weight=110, passes=1)
    s.line([(cols[4] + 50, y), (cols[5] - 50, y + 146)], weight=110, passes=1)

# door and stoop
s.rect((cols[3] - 60, 800, cols[3] + 60, 930), (30, 26, 40))
for k in range(3):
    s.rect((cols[3] - 90 - k * 16, 930 + k * 18, cols[3] + 90 + k * 16, 948 + k * 18), (70, 66, 80))

# a streetlamp at the left kerb, lit, so the pavement under it is looked at a little
s.rect((70, 420, 82, 1000), IRON)
s.poly([(52, 404), (100, 404), (90, 424), (62, 424)], IRON)
s.glow((58, 424, 94, 432), (255, 180, 90), 2.0)
s.look(76, 700, 110, 0.55)
s.sketched((120, 60, 1800, 1010))

img = s.render()
out = sys.argv[1] if len(sys.argv) > 1 else '../frames/k4_3am_styletest.png'
img.save(out)
print('saved', out)
