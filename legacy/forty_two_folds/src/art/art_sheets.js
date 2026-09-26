// art_sheets.js: reference sheets for the ART MODEL GATE (labels allowed here only).
(() => {
  const REF = 'reference/chatgpt_dragon_ref.png';
  // side-by-side with the reference at the same scale, plus an onion-skin overlay
  LOOPS.gpt_art_compare = async t => {
    const im = await loadImg(REF), s = 1040 / 1536, top = 20;
    if (im) X.drawImage(im, 20, top, 1024 * s, 1536 * s);
    drawGPTFront(700 + 500 * s - 500 * s + 500 * s - 162, top + 1512 * s, MODEL.h * s);
    // overlay: reference, then the model at 55% on an offscreen layer
    const ox = 1250;
    if (im) X.drawImage(im, ox, top, 1024 * s, 1536 * s);
    const off = document.createElement('canvas'); off.width = SW; off.height = SH; const oc = off.getContext('2d'), keep = X; X = oc;
    drawGPTFront(ox + 500 * s, top + 1512 * s, MODEL.h * s); X = keep;
    X.save(); X.globalAlpha = .55; X.drawImage(off, 0, 0); X.restore();
    label('reference', 20 + 512 * s, 1070, 18); label('layered cel model (front)', 700 + 175, 1070, 18); label('overlay', ox + 512 * s, 1070, 18);
  };
  LOOPS.gpt_art_compare.len = 1;
  LOOPS.gpt_art_front = t => { drawGPTFront(960, 1060, 1000); };
  LOOPS.gpt_art_front.len = 1;
  LOOPS.gpt_art_zoom = t => { drawGPTFront(960, 1060 + 900, 2000); };   // upper body at 2x
  LOOPS.gpt_art_zoom.len = 1;
  LOOPS.gpt_art_legs = t => { drawGPTFront(960, 1060, 2000); };         // lower body at 2x
  LOOPS.gpt_art_legs.len = 1;
})();
