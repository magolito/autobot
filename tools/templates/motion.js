/* ── Shared motion helpers (inlined by tools/build_*.py) ── */
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
document.documentElement.classList.add('rx-js');
const fmt = { usd: v => '$' + Math.round(v).toLocaleString('en-US'), pct: v => '+' + v.toFixed(1) + '%', mo: v => Math.round(v) + ' months',
              x: v => v.toFixed(1) + '×' };
function countUp(el, to, f, dur){
  if (REDUCED){ el.textContent = f(to); return; }
  const t0 = performance.now(); dur = dur || 1600;
  (function tick(t){ const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 4);
    el.textContent = f(to * e); if (p < 1) requestAnimationFrame(tick); else el.textContent = f(to); })(t0);
}
function scramble(el){
  if (REDUCED) return;
  const final = el.textContent, chars = '0123456789$%+×#/';
  let f = 0; const total = 18;
  (function step(){ el.textContent = final.split('').map((ch, i) => ch === ' ' ? ' ' : (i < f / total * final.length ? ch : chars[Math.random() * chars.length | 0])).join('');
    if (++f <= total) setTimeout(step, 34); else el.textContent = final; })();
}
function onView(els, fn, thr){
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting){ fn(e.target); io.unobserve(e.target); } }), {threshold: thr || 0.3});
  els.forEach(el => io.observe(el));
}
/* Cursor-reactive dot field. host: element that receives the pointer; ink: 'r,g,b' */
function dotField(cv, host, ink, opts){
  opts = opts || {};
  const ctx = cv.getContext('2d'), GAP = opts.gap || 22, base = opts.base || .1;
  let W, H, mx = -999, my = -999, tx = -999, ty = -999, raf = null, t0 = performance.now(), visible = true;
  function size(){ const dpr = Math.min(2, devicePixelRatio || 1); W = host.clientWidth; H = host.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + 'px'; cv.style.height = H + 'px'; ctx.setTransform(dpr,0,0,dpr,0,0); draw(performance.now()); }
  function draw(now){
    const t = (now - t0) / 1000; ctx.clearRect(0, 0, W, H);
    mx += (tx - mx) * .12; my += (ty - my) * .12;
    for (let y = GAP; y < H; y += GAP) for (let x = GAP; x < W; x += GAP){
      const d = Math.hypot(x - mx, y - my), near = Math.max(0, 1 - d / 150);
      const wave = REDUCED ? 0 : (Math.sin(x * .018 + t * .9) + Math.cos(y * .022 - t * .7)) * .25 + .5;
      const r = .7 + near * 1.9 + wave * .35, a = base + near * .55 + wave * .08;
      ctx.fillStyle = 'rgba(' + ink + ',' + a.toFixed(3) + ')';
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
    }
  }
  function loop(now){ draw(now); raf = (visible && !REDUCED) ? requestAnimationFrame(loop) : null; }
  host.addEventListener('pointermove', e => { const b = host.getBoundingClientRect(); tx = e.clientX - b.left; ty = e.clientY - b.top; if (mx < -900){ mx = tx; my = ty; } if (REDUCED) draw(performance.now()); });
  host.addEventListener('pointerleave', () => { tx = ty = -999; });
  new IntersectionObserver(es => { visible = es[0].isIntersecting; if (visible && !raf && !REDUCED) raf = requestAnimationFrame(loop); }).observe(host);
  addEventListener('resize', size); size();
}
/* Line-by-line headline reveal */
requestAnimationFrame(() => document.querySelectorAll('.rx-title').forEach(t => t.classList.add('in')));
