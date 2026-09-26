// sheets.js: model sheets and scale sheets (the one place labels are allowed).
//   studio.html?loop=gpt_turn   · node render.mjs --loop=gpt_turn --sheet=0 --cols=1 --w=1920 --out=out/sheets/gpt_turn.jpg
(() => {
  const VIEWS = [[0, 'front'], [.5, '3/4'], [1, 'profile'], [1.5, 'back 3/4'], [-.5, '3/4 (left)']];
  function turnSheet(drawFn, name) {
    return t => {
      const h = 820, gy = 960;
      for (let i = 0; i <= 10; i++) guideLine(gy - h * i / 6.6 * (i ? 1 : 0), i ? `${i} head${i > 1 ? 's' : ''}` : 'ground');
      VIEWS.forEach(([yaw, lab], i) => {
        const x = 230 + i * 365;
        drawFn(x, gy, h, { yawH: yaw, yawC: yaw, yawP: yaw, arms: {} });
        label(lab, x, gy + 60, 24);
      });
      label(name + ' · canonical h = 820 px · 6.6 heads', SW / 2, 40, 26);
    };
  }
  LOOPS.gpt_turn = turnSheet(drawChatGPT, 'ChatGPT'); LOOPS.gpt_turn.len = 1;
  if (typeof drawClaude === 'function') { LOOPS.cl_turn = turnSheet(drawClaude, 'Claude'); LOOPS.cl_turn.len = 1; }
  LOOPS.gpt_front = t => { drawChatGPT(960, 1030, 960, { arms: {} }); };
  LOOPS.gpt_head = t => { drawChatGPT(960, 1030 + 2600, 3400, { arms: {} }); }; LOOPS.gpt_front.len = 1; LOOPS.gpt_head.len = 1;
})();
