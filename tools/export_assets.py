"""Export palettes (.gpl + swatch PNG) and character sprite sheets (native PNG) to assets/."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from PIL import Image
from engine.px import Canvas, rgb, to_rgb
from art.body import render, make_pose
from art.portrait import bust
from art import poses as PO, palette as PAL

os.makedirs('assets/palettes', exist_ok=True)
os.makedirs('assets/sprites', exist_ok=True)
pals = {'chatgpt': PAL.GPT, 'claude': PAL.CLAUDE, 'kid': PAL.KID}
ramps = {k: getattr(PAL, k) for k in ('NIGHT', 'WARM', 'JADE', 'PAPER', 'DOOM', 'STEEL', 'PINK', 'GOLD')}
for name, d in list(pals.items()) + [(k.lower(), {str(i): c for i, c in enumerate(v)}) for k, v in ramps.items()]:
    with open(f'assets/palettes/{name}.gpl', 'w') as fh:
        fh.write(f'GIMP Palette\nName: {name}\nColumns: 8\n#\n')
        for key, c in d.items():
            r, g, b = rgb(c)
            fh.write(f'{r:3d} {g:3d} {b:3d}\t{key}\n')
    cols = list(d.values())
    sw = np.zeros((16, 16 * len(cols), 3), np.uint8)
    for i, c in enumerate(cols):
        sw[:, i * 16:(i + 1) * 16] = rgb(c)
    Image.fromarray(sw).save(f'assets/palettes/{name}.png')
for who in ('gpt', 'claude'):
    frames = [make_pose(v) for v in 'FQPB'] + [PO.run(i, who) for i in range(8)] + [PO.walk(i, who) for i in range(8)] + \
             [PO.point(who), PO.plead(who), PO.think(who), PO.surprise(who), PO.reach_up(who), PO.wave(0, who), PO.wave(1, who),
              PO.bow(1, who, 'F'), PO.bow(2, who, 'F'), PO.fall(0, who), PO.fall(1, who)]
    cell = 96
    cols = 8
    rows = (len(frames) + cols - 1) // cols
    sheet = np.zeros((rows * 112, cols * cell, 4), np.uint8)
    for i, p in enumerate(frames):
        a = render(who, p).arr
        r_, c_ = divmod(i, cols)
        sheet[r_ * 112:r_ * 112 + a.shape[0], c_ * cell:c_ * cell + a.shape[1]] = a[:, :cell]
    Image.fromarray(sheet, 'RGBA').save(f'assets/sprites/{who}_sheet.png')
    busts = [bust(who, 'Q', e, m).arr for e, m in (('open', 'small'), ('calm', 'none'), ('wide', 'o'), ('happy', 'smile'), ('worried', 'wavy'), ('closed', 'small'))]
    h = max(b.shape[0] for b in busts)
    strip = np.zeros((h, sum(b.shape[1] for b in busts), 4), np.uint8)
    x = 0
    for b in busts:
        strip[:b.shape[0], x:x + b.shape[1]] = b
        x += b.shape[1]
    Image.fromarray(strip, 'RGBA').save(f'assets/sprites/{who}_portraits_2x.png')
print('ok')
