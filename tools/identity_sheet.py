"""Render the pixel identity sheet -> qa/identity_sheet.png (native x6) and a native copy."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np
from PIL import Image
from engine.px import Canvas, upscale, to_rgb
from art.body import render, make_pose
from art.portrait import bust
from art import poses as PO
from art import palette as PAL

W, H = 480, 270
cv = Canvas(W, H, PAL.NIGHT[1])
cv.rect(0, 118, W, 1, PAL.NIGHT[3]); cv.rect(0, 250, W, 1, PAL.NIGHT[3])
cv.text("ChatGPT", 6, 4, PAL.JADE[6], shadow=PAL.NIGHT[0])
cv.text("Claude", 6, 124, PAL.WARM[6], shadow=PAL.NIGHT[0])
lab = ['front', '3/4', 'side', 'back', 'action', 'blink']
def row(who, y, action, portrait_eyes):
    xs = [28, 70, 108, 150, 196]
    for x, p, lb in zip(xs, [make_pose('F'), make_pose('Q'), make_pose('P'), make_pose('B'), action], lab):
        cv.blit(render(who, p), x, y)
        cv.text(lb, x, y + 3, PAL.NIGHT[5], font='3', align='center')
    # run strip: 8 drawings in a row, small spacing
    for i in range(8):
        cv.blit(render(who, PO.run(i, who)), 246 + i * 25, y - 38 if i % 2 else y)
    cv.text('run x8 (12 fps)', 246, y + 3, PAL.NIGHT[5], font='3')
    # 2x portraits
    for k, (e, m) in enumerate(portrait_eyes):
        b = bust(who, 'Q', e, m)
        cv.blit(b, 452 - k * 0, y - 20) if k == 0 else None
row('gpt', 112, PO.point('gpt'), [('open', 'small')])
row('claude', 244, PO.plead('claude'), [('calm', 'small')])
a = np.array(cv.im)
os.makedirs('qa', exist_ok=True)
Image.fromarray(upscale(to_rgb(a), 6)).save('qa/identity_sheet.png')
Image.fromarray(to_rgb(a)).save('qa/identity_sheet_native.png')
print('ok')
