"""Full-song STORYBOARD animatic from tools/shotmap.py (not final animation).

One panel per shot, built only from existing local material (KV/BG plates, the supplied character
drawings, rough layout sketches where a plate is missing). Two places play the acceptance-test
renders (I01 = Test 1, F03 = Test 2), labelled as such. Every other action insert or face segment
is flagged on screen as NOT ANIMATED while it is active. Timed frame-exactly at 24 fps over all
5122 frames and muxed with the locked master mp3 (stream copy, unaltered).

  python3 tools/animatic.py            -> tests/STORYBOARD_ANIMATIC.mp4 + tests/storyboard_panels.jpg
"""
import os
import subprocess
import sys
import textwrap

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
L2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from shotmap import S, END, FPS, check  # noqa: E402

AUDIO = '/root/.claude/uploads/c9b74a57-085e-5ad1-8a57-5167fd743993/4ccd5715-Loading_P0_endfix_candidate01.mp3'
PL = '/home/user/OC/loading/work/plates'
DER = '/home/user/OC/loading/work/derived'
CH = os.path.join(L2, 'work', 'chars')
SESS = '/tmp/claude-0/-home-user-OC/c9b74a57-085e-5ad1-8a57-5167fd743993'
IMG = os.path.join(SESS, 'images')
QC = os.path.join(SESS, 'scratchpad/mvpack/inputs/Loading_face_assets_QC_PASS')
EVID = os.path.join(L2, 'docs', 'evidence', 'audio_evidence_ending.png')
T1 = os.path.join(L2, 'tests', 'test1_rig')
T2 = os.path.join(L2, 'tests', 'test2_sing')
OUT = os.path.join(L2, 'tests', 'STORYBOARD_ANIMATIC.mp4')
SHEET = os.path.join(L2, 'tests', 'storyboard_panels.jpg')

W, H = 960, 540
IX, IY, IW, IH = 12, 36, 624, 351          # picture area
RX, RW = 648, 300                          # right column
NF = int(round(END * FPS))

SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SANSB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SERIF = os.path.join(L2, 'data', 'fonts', 'CormorantGaramond.ttf')
SERIFI = os.path.join(L2, 'data', 'fonts', 'CormorantGaramond-Italic.ttf')
F = {k: ImageFont.truetype(p, s) for k, (p, s) in dict(
    hdr=(SANSB, 13), small=(SANS, 11), smallb=(SANSB, 11), col=(SANS, 11), colb=(SANSB, 13),
    lyr=(SERIFI, 19), tag=(SANSB, 12), big=(SERIFI, 64), sk=(SANS, 12)).items()}

INK = (235, 230, 220)
DIM = (150, 150, 160)
WARM = (255, 196, 120)
RED = (235, 90, 80)
BLUE = (110, 170, 255)
YEL = (240, 215, 90)
ORANGE = (255, 150, 60)


def t2tc(t):
    m = int(t // 60)
    return '%d:%04.1f' % (m, t - 60 * m)


# ---------------------------------------------------------------- picture sources

def fit16x9(img, cx=0.5, cy=0.5, zoom=1.0):
    """Crop img (H,W,3 uint8 RGB) to 16:9 around (cx,cy) fractions with zoom, resize to IW x IH."""
    h, w = img.shape[:2]
    cw = min(w, h * 16 / 9) / zoom
    ch = cw * 9 / 16
    x0 = int(np.clip(cx * w - cw / 2, 0, w - cw))
    y0 = int(np.clip(cy * h - ch / 2, 0, h - ch))
    return cv2.resize(img[y0:y0 + int(ch), x0:x0 + int(cw)], (IW, IH), interpolation=cv2.INTER_AREA)


def rgb8(path):
    return cv2.imread(path)[:, :, ::-1].copy()


def npy8(name):
    a = np.load(os.path.join(DER, name + '.npy')).astype(np.float32)
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def rgba16(name):
    a = cv2.imread(os.path.join(CH, name + '.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535.0
    return a[:, :, [2, 1, 0, 3]]


def sketch(lines, title):
    """Rough layout sketch on a dark board: list of ('line'|'rect'|'circle'|'text', ...) in 0..1 coords."""
    im = np.full((IH, IW, 3), (22, 24, 34), np.uint8)
    for it in lines:
        k = it[0]
        if k == 'line':
            _, a, b, c = it
            cv2.line(im, (int(a[0] * IW), int(a[1] * IH)), (int(b[0] * IW), int(b[1] * IH)), c, 2, cv2.LINE_AA)
        elif k == 'rect':
            _, a, b, c = it
            cv2.rectangle(im, (int(a[0] * IW), int(a[1] * IH)), (int(b[0] * IW), int(b[1] * IH)), c, 2, cv2.LINE_AA)
        elif k == 'circle':
            _, a, r, c, fill = it
            cv2.circle(im, (int(a[0] * IW), int(a[1] * IH)), int(r * IW), c, -1 if fill else 2, cv2.LINE_AA)
    pim = Image.fromarray(im)
    d = ImageDraw.Draw(pim)
    for it in lines:
        if it[0] == 'text':
            _, a, s, c = it
            d.text((int(a[0] * IW), int(a[1] * IH)), s, font=F['sk'], fill=c)
    d.rectangle([4, 4, IW - 5, IH - 5], outline=(90, 90, 110))
    d.text((12, IH - 22), title, font=F['smallb'], fill=YEL)
    return np.array(pim)


L = (200, 200, 210)
G = (255, 200, 120)
SK = {
    'schematic:MEMORY VIGNETTES (plates missing)': [
        ('rect', (0.03, 0.08), (0.32, 0.62), L), ('rect', (0.355, 0.08), (0.645, 0.62), L), ('rect', (0.68, 0.08), (0.97, 0.62), L),
        ('text', (0.05, 0.10), '1  war (21.0)', INK), ('text', (0.375, 0.10), '2  lullaby (22.5)', INK), ('text', (0.70, 0.10), '3  goodbye (23.6)', INK),
        ('text', (0.05, 0.50), 'pen presses a letter', DIM), ('text', (0.375, 0.50), 'hand rocks a cradle', DIM), ('text', (0.70, 0.50), 'hand lets go of a hand', DIM),
        ('circle', (0.175, 0.35), 0.012, G, True), ('circle', (0.50, 0.35), 0.012, G, True), ('circle', (0.825, 0.35), 0.012, G, True),
        ('line', (0.175, 0.74), (0.50, 0.70), G), ('line', (0.50, 0.70), (0.825, 0.76), G), ('circle', (0.50, 0.70), 0.008, G, True),
        ('circle', (0.175, 0.74), 0.006, G, True), ('circle', (0.825, 0.76), 0.006, G, True),
        ('text', (0.30, 0.80), '25.3: the marks join N as one constellation (no sky)', INK)],
    'schematic:RIM PATH (plate missing)': [
        ('line', (0.0, 0.92), (0.55, 0.78), L), ('line', (0.55, 0.78), (0.85, 0.45), L), ('line', (0.85, 0.45), (0.97, 0.15), L),
        ('line', (0.0, 0.97), (0.55, 0.84), L), ('line', (0.55, 0.84), (0.85, 0.52), L),
        ('text', (0.05, 0.40), 'the flattened world rises like a page', DIM), ('line', (0.0, 0.70), (0.45, 0.62), (120, 120, 140)),
        ('text', (0.60, 0.60), 'rim = surviving boundary strip', INK), ('text', (0.70, 0.10), 'edge of the sphere', INK)],
    'schematic:STARLIGHT PATH -> THRESHOLD': [
        ('circle', (0.18, 0.75), 0.01, G, True), ('line', (0.18, 0.75), (0.80, 0.25), (150, 140, 110)),
        ('rect', (0.78, 0.10), (0.92, 0.42), G), ('text', (0.66, 0.46), 'threshold (plate P06 missing)', INK),
        ('text', (0.05, 0.84), 'LB lantern leads; torso first, legs + hair lag (I12)', INK),
        ('text', (0.05, 0.10), 'step off the rim -> float (no support)', DIM)],
    'room': [
        ('rect', (0.06, 0.08), (0.36, 0.48), L), ('text', (0.08, 0.10), 'window: the flat world', DIM),
        ('line', (0.0, 0.66), (1.0, 0.66), L), ('rect', (0.45, 0.58), (0.92, 0.70), L), ('text', (0.55, 0.52), 'desk + console', INK),
        ('rect', (0.62, 0.36), (0.72, 0.58), L), ('line', (0.62, 0.58), (0.62, 0.80), L), ('line', (0.72, 0.58), (0.72, 0.80), L),
        ('text', (0.74, 0.40), 'empty chair', INK), ('text', (0.05, 0.86), 'girls stop behind the desk line (occlusion) - room plate P07 missing', YEL)],
    'keys': [
        ('rect', (0.08, 0.40), (0.92, 0.75), L)] + [('rect', (0.10 + 0.068 * i, 0.50), (0.16 + 0.068 * i, 0.68), L) for i in range(12)] + [
        ('circle', (0.13 + 0.068 * i, 0.45), 0.008, G, True) for i in (2, 3, 5, 6, 8)] + [
        ('text', (0.08, 0.20), 'keys go down one by one under warm footprints of passing travellers', INK),
        ('text', (0.08, 0.82), 'console plate missing; A/B head-and-shoulder turn (I15) needs drawings', YEL)],
    'lanterns': [
        ('line', (0.0, 0.75), (1.0, 0.65), L)] + [('circle', (0.08 * i + 0.05, 0.74 - 0.008 * i), 0.006, G, True) for i in range(12)] + [
        ('circle', (0.40, 0.45), 0.018, G, False), ('circle', (0.55, 0.43), 0.018, G, False),
        ('text', (0.33, 0.30), 'LA (lit from a footstep)   LB', INK),
        ('text', (0.05, 0.85), 'two planted steps with lanterns along the lit traces (I16)', YEL)],
    'schematic:WINDOW -> ARTWORK OF ALL TRACES (plate missing)': [
        ('rect', (0.10, 0.06), (0.90, 0.80), L),
        ('text', (0.14, 0.12), 'letter', DIM), ('text', (0.36, 0.20), 'cradle', DIM), ('text', (0.60, 0.12), 'parting hands', DIM),
        ('text', (0.18, 0.44), 'first fire', DIM), ('text', (0.46, 0.50), 'signal', DIM), ('text', (0.68, 0.44), 'footsteps', DIM),
        ('circle', (0.62, 0.68), 0.01, (90, 90, 100), True), ('text', (0.64, 0.66), 'one light goes out; its mark stays', INK),
        ('text', (0.12, 0.86), 'B hand to the glass (I17); lanterns lifted', YEL)],
    'schematic:THE GIRLS STEP INTO THE ART (states missing)': [
        ('rect', (0.42, 0.05), (0.98, 0.85), L), ('text', (0.45, 0.08), 'the plane (art)', DIM),
        ('text', (0.03, 0.88), 'volumetric -> drawn contour, by choice, holding hands (I18): states missing', YEL)],
    'schematic:NOTE IN B\'S HANDS: 2 -> 3 -> 1': [
        ('rect', (0.06, 0.30), (0.28, 0.62), L), ('text', (0.08, 0.66), 'two: unfolded flat', INK),
        ('line', (0.38, 0.62), (0.50, 0.32), L), ('line', (0.50, 0.32), (0.62, 0.62), L), ('line', (0.38, 0.62), (0.62, 0.62), L),
        ('text', (0.38, 0.66), 'three: folded lantern', INK),
        ('circle', (0.83, 0.46), 0.012, G, True), ('text', (0.74, 0.66), 'one: a point (199.9)', INK),
        ('text', (0.05, 0.86), 'hand + paper fold drawings missing (I20)', YEL)],
}


def card(img, x, yb, hf, label, base):
    """Paste an existing drawing as a framed reference card (white background kept, labelled)."""
    hh = int(hf * IH)
    ww = int(img.shape[1] * hh / img.shape[0])
    sm = cv2.resize(img, (ww, hh), interpolation=cv2.INTER_AREA)
    x0 = int(np.clip(x * IW - ww / 2, 0, IW - ww))
    y0 = int(np.clip(yb * IH - hh, 0, IH - hh))
    base[y0:y0 + hh, x0:x0 + ww] = sm
    cv2.rectangle(base, (x0, y0), (x0 + ww - 1, y0 + hh - 1), (200, 200, 210), 1)
    cv2.putText(base, label, (x0 + 4, y0 + hh - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (40, 40, 40), 1, cv2.LINE_AA)


def cutout(name, x, yb, hf, base):
    a = rgba16(name)
    hh = int(hf * IH)
    ww = int(a.shape[1] * hh / a.shape[0])
    sm = cv2.resize(a, (ww, hh), interpolation=cv2.INTER_AREA)
    x0 = int(np.clip(x * IW - ww / 2, 0, IW - ww))
    y0 = int(np.clip(yb * IH - hh, 0, IH - hh))
    reg = base[y0:y0 + hh, x0:x0 + ww].astype(np.float32) / 255
    al = sm[:, :, 3:4]
    base[y0:y0 + hh, x0:x0 + ww] = ((reg * (1 - al) + sm[:, :, :3] * al) * 255 + 0.5).astype(np.uint8)


KV1_FRAMING = {'S02': (0.5, 0.62, 1.15), 'S10': (0.5, 0.55, 1.0), 'S12': (0.62, 0.45, 1.8), 'S30': (0.5, 0.5, 0.9)}

CARDS = {'B1': (os.path.join(QC, 'B1.png'), 'B1 (QC drawing)'), 'B2': (os.path.join(QC, 'B2.png'), 'B2 (QC drawing)'),
         'A_sing': (os.path.join(IMG, '4.webp'), 'A singing head 3/4 (no matching mouths)'),
         'B_sing': (os.path.join(IMG, '5.webp'), 'B singing head 3/4 (no matching mouths)')}


def picture(s):
    bg = s['bg']
    note = ''
    if bg == 'bg0a':
        im = fit16x9(rgb8(os.path.join(PL, 'BG0a.png')))
        note = 'BG0a night Earth (existing)'
    elif bg == 'bg0b':
        im = fit16x9(rgb8(os.path.join(PL, 'BG0b.png')))
        note = 'BG0b (existing)'
    elif bg == 'kv1_clean':
        cx, cy, z = KV1_FRAMING.get(s['id'], (0.5, 0.62, 1.15))
        im = fit16x9(rgb8(os.path.join(PL, 'KV1.png')), cx, cy, z)
        note = 'KV1 key visual (girls painted in; clean plate P02 missing)'
        if s['id'] == 'S12':
            cv2.circle(im, (int(IW * 0.80), int(IH * 0.30)), 4, (255, 60, 50), -1, cv2.LINE_AA)
            note += ' - red horizon cue'
        if s['id'] == 'S30':
            im = (im.astype(np.float32) * 0.55).astype(np.uint8)
            note += ' - darkened: city partly reloaded'
        if s['id'] == 'S28':
            im = (im.astype(np.float32) * 0.45).astype(np.uint8)
            cv2.circle(im, (int(IW * 0.60), int(IH * 0.72)), 7, (255, 220, 160), -1, cv2.LINE_AA)
            note += ' - darkened; point of light'
    elif bg == 'kv1_clean_close':
        im = fit16x9(rgb8(os.path.join(PL, 'KV1.png')), 0.58, 0.72, 2.4)
        note = 'KV1 crop (existing)'
    elif bg == 'kv3':
        im = fit16x9(rgb8(os.path.join(PL, 'KV3.png')))
        note = 'KV3 (existing; forest plates P04 missing)'
    elif bg == 'kv4':
        im = fit16x9(rgb8(os.path.join(PL, 'KV4.png')))
        note = 'KV4 (existing)'
    elif bg == 'kv5':
        im = fit16x9(rgb8(os.path.join(PL, 'KV5a.png')))
        note = 'KV5a shared palm light (existing; contact drawings missing)'
    elif bg == 'test2':
        im = fit16x9(rgb8(os.path.join(T2, '01300.png')))
        note = 'Test 2 frame (local render)'
    elif bg == 'flat':
        im = fit16x9(npy8('BG0b_flat'), 0.5, 0.5, 1.0)
        cv2.line(im, (0, int(IH * 0.93)), (IW, int(IH * 0.90)), (230, 220, 200), 3, cv2.LINE_AA)
        note = 'BG0b_flat (earlier derived flat state) + rim line; P05a-c missing'
    elif bg == 'triptych':
        a = rgb8(os.path.join(QC, 'A_mouth.png'))
        b = rgb8(os.path.join(QC, 'B_mouth.png'))
        im = np.full((IH, IW, 3), 245, np.uint8)
        im[:IH // 2] = cv2.resize(a, (IW, IH // 2), interpolation=cv2.INTER_AREA)
        im[IH // 2:] = cv2.resize(b, (IW, IH - IH // 2), interpolation=cv2.INTER_AREA)
        note = 'A / B side mouth triptychs (3 states each; existing)'
    elif bg == 'text':
        pim = Image.new('RGB', (IW, IH), (14, 14, 22))
        d = ImageDraw.Draw(pim)
        d.text((IW // 2, IH // 2), 'still loading', font=F['big'], fill=(255, 214, 160), anchor='mm')
        im = np.array(pim)
        note = 'text in the note\'s handwriting (style missing; serif placeholder)'
    else:
        im = sketch(SK.get(bg, []), 'LAYOUT SKETCH - ' + (bg.split(':', 1)[1] if ':' in bg else bg.upper() + ' PLATE MISSING'))
        note = 'rough layout sketch (no plate exists)'
    im = im.copy()
    for name, x, yb, hf in s['chars']:
        if name in ('kv1_A', 'kv1_B'):
            continue                       # already painted into KV1
        if name in CARDS:
            p, lab = CARDS[name]
            card(rgb8(p), x, yb, hf, lab, im)
        else:
            cutout(name, x, yb, hf, im)
    if s['id'] == 'S23':
        ev = rgb8(EVID)[0:335, :]
        ev = cv2.resize(ev, (IW - 20, int(ev.shape[0] * (IW - 20) / ev.shape[1])), interpolation=cv2.INTER_AREA)
        y0 = IH - ev.shape[0] - 30
        im[y0:y0 + ev.shape[0], 10:10 + ev.shape[1]] = ev
        note = 'audio evidence 158-172 s (vocal stem spectrogram, pyin, ASR) + layout'
    return im, note


# ---------------------------------------------------------------- static panel

def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def panel(s):
    im, note = picture(s)
    pim = Image.new('RGB', (W, H), (10, 10, 14))
    pim.paste(Image.fromarray(im), (IX, IY))
    d = ImageDraw.Draw(pim)
    d.text((IX, 10), 'STORYBOARD ANIMATIC - NOT FINAL ANIMATION   |   Simulated Universe   |   locked track 213.41 s',
           font=F['hdr'], fill=YEL)
    d.text((IX, IY + IH + 3), 'picture: ' + note, font=F['small'], fill=DIM)

    y = IY
    d.text((RX, y), '%s   %s - %s   (%.1f s)' % (s['id'], t2tc(s['t0']), t2tc(s['t1']), s['t1'] - s['t0']), font=F['colb'], fill=INK)
    y += 18
    d.text((RX, y), s['sec'], font=F['smallb'], fill=ORANGE if 'DISPUTED' in s['sec'] else WARM)
    y += 15
    rows = [('voice', s['voice']), ('state', 'world %s | bodies %s | place %s' % (s['W'], s['B'], s['P'])),
            ('support', s['sup']), ('trace', s['T']), ('action', s['act']), ('change', s['chg'])]
    boxes = {}
    for k, v in rows:
        for i, ln in enumerate(wrap(d, k + ': ' + v, F['col'], RW)):
            if y > IY + IH - 70:
                break
            d.text((RX, y), ln, font=F['col'], fill=DIM if k in ('voice', 'support', 'trace') else INK)
            y += 13
        y += 2
    y = max(y, IY + IH - 66)
    for iid, a, b, desc in s['ins']:
        txt = 'INSERT %s %s-%s %s' % (iid, '%.1f' % a, '%.1f' % b, desc)
        ln = wrap(d, txt, F['small'], RW - 6)[0]
        boxes[iid] = (RX - 3, y - 1, RX + RW, y + 13, a, b, 'ins')
        d.text((RX, y), ln, font=F['small'], fill=RED)
        y += 14
    for fid, a, b, desc, compat in s['face']:
        txt = 'FACE %s %s-%s %s' % (fid, '%.1f' % a, '%.1f' % b, desc)
        ln = wrap(d, txt, F['small'], RW - 6)[0]
        boxes[fid] = (RX - 3, y - 1, RX + RW, y + 13, a, b, 'face')
        d.text((RX, y), ln, font=F['small'], fill=BLUE)
        y += 14

    # lyric strip (author text)
    ly = IY + IH + 20
    col = ORANGE if 'UNRESOLVED' in s['lyric'] else (255, 236, 205)
    for ln in wrap(d, s['lyric'], F['lyr'], W - 2 * IX)[:3]:
        d.text((IX, ly), ln, font=F['lyr'], fill=col)
        ly += 21
    return np.array(pim)[:, :, ::-1].copy(), boxes


# ---------------------------------------------------------------- timeline + per-frame overlays

TL_Y, TL_X0, TL_X1 = 508, IX, W - IX
UNASSIGNED = [(179.5, 180.0), (200.0, 202.5), (203.7, 204.0)]


def tx(t):
    return int(TL_X0 + (TL_X1 - TL_X0) * t / END)


def timeline_base():
    tl = np.zeros((H, W, 3), np.uint8)
    cv2.rectangle(tl, (TL_X0, TL_Y), (TL_X1, TL_Y + 12), (60, 60, 70), -1)
    for s in S:
        for _, a, b, _ in s['ins']:
            cv2.rectangle(tl, (tx(a), TL_Y), (tx(b), TL_Y + 5), (80, 90, 235), -1)
        for _, a, b, _, _ in s['face']:
            cv2.rectangle(tl, (tx(a), TL_Y + 7), (tx(b), TL_Y + 12), (255, 170, 110), -1)
        if 'DISPUTED' in s['sec']:
            cv2.rectangle(tl, (tx(s['t0']), TL_Y - 4), (tx(s['t1']), TL_Y - 1), (60, 150, 255), -1)
    for a, b in UNASSIGNED:
        cv2.rectangle(tl, (tx(a), TL_Y - 4), (max(tx(b), tx(a) + 2), TL_Y - 1), (240, 215, 90), -1)
    for s in S:
        cv2.line(tl, (tx(s['t0']), TL_Y - 6), (tx(s['t0']), TL_Y + 14), (200, 200, 200), 1)
    return tl


def tag(fr, text, color):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
    x0, y0 = IX + 6, IY + 6
    sub = fr[y0:y0 + th + 10, x0:x0 + tw + 10].astype(np.float32)
    fr[y0:y0 + th + 10, x0:x0 + tw + 10] = (sub * 0.25).astype(np.uint8)
    cv2.rectangle(fr, (x0, y0), (x0 + tw + 10, y0 + th + 10), color, 1)
    cv2.putText(fr, text, (x0 + 5, y0 + th + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)


def test_frame(dirp, f):
    p = os.path.join(dirp, '%05d.png' % f)
    if not os.path.exists(p):
        return None
    return fit16x9(cv2.imread(p))   # BGR in, BGR out


def main():
    assert check() == NF
    panels = {}
    for s in S:
        panels[s['id']] = panel(s)
    # contact sheet of panels for the written review
    th = [cv2.resize(panels[s['id']][0], (480, 270), interpolation=cv2.INTER_AREA) for s in S]
    rows = [np.hstack(th[i:i + 3]) for i in range(0, len(th), 3)]
    cv2.imwrite(SHEET, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
    if '--sheet' in sys.argv:
        return

    tl = timeline_base()
    tlm = tl.any(axis=2)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H),
                           '-r', str(FPS), '-i', '-', '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                           '-preset', 'medium', '-crf', '28', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', OUT],
                          stdin=subprocess.PIPE)
    si = 0
    for f in range(NF):
        t = f / FPS
        while not (S[si]['t0'] - 1e-9 <= t < S[si]['t1'] - 1e-9) and si < len(S) - 1:
            si += 1
        s = S[si]
        base, boxes = panels[s['id']]
        fr = base.copy()
        fr[tlm] = tl[tlm]
        active = [(k, v) for k, v in boxes.items() if v[4] - 1e-9 <= t < v[5] - 1e-9]
        shown = False
        for k, (x0, y0, x1, y1, a, b, kind) in active:
            cv2.rectangle(fr, (x0, y0), (x1, y1), (80, 90, 235) if kind == 'ins' else (255, 170, 110), 1)
            if k == 'I01':
                tf = test_frame(T1, f)
                if tf is not None:
                    fr[IY:IY + IH, IX:IX + IW] = tf
                    tag(fr, 'TEST 1 local rig render - FAILED body turn + hair follow-through (see report)', (90, 200, 255))
                    shown = True
                    continue
            if k == 'F03':
                tf = test_frame(T2, f)
                if tf is not None:
                    fr[IY:IY + IH, IX:IX + IW] = tf
                    tag(fr, 'TEST 2 local render - automated checks only, lip-sync NOT reviewed', (90, 200, 255))
                    shown = True
                    continue
            if not shown:
                if kind == 'ins':
                    tag(fr, 'ACTION INSERT %s - NOT ANIMATED (needs drawings or approved i2v)' % k, (80, 90, 235))
                else:
                    tag(fr, 'FACE %s - NOT ANIMATED in this storyboard' % k, (255, 170, 110))
                shown = True
        for a, b in UNASSIGNED:
            if a - 1e-9 <= t < b - 1e-9:
                cv2.putText(fr, 'previously unassigned %.1f-%.1f s -> %s' % (a, b, s['id']), (IX + 330, TL_Y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (240, 215, 90), 1, cv2.LINE_AA)
        x = tx(t)
        cv2.line(fr, (x, TL_Y - 7), (x, TL_Y + 15), (255, 255, 255), 2)
        cv2.putText(fr, '%s   frame %d / %d   %s' % (t2tc(t), f, NF, s['id']), (IX, H - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)
        cv2.putText(fr, 'red: action insert  blue: face  orange: unresolved lyric  cyan: formerly unassigned', (IX + 330, H - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (170, 170, 170), 1, cv2.LINE_AA)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB;', SHEET)


if __name__ == '__main__':
    main()
