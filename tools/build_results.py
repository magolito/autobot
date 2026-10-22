#!/usr/bin/env python3
"""Builds results.html (Client Results page) from data/clients.json.

Edit client figures in data/clients.json, then run:  python3 tools/build_pages.py
Standard library only. Shared page chrome (nav, CTA band, footer) comes from
tools/templates/base.html; page-specific styles from tools/templates/results.css.
"""
import re, html, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / 'tools' / 'templates'
s=(TPL / 'base.html').read_text(encoding='utf-8')
I=s.index
head = s[:I('<style>')+len('<style>')]
css = s[I('<style>')+len('<style>'):I('/* STORY GRID */')] + s[I('/* DISCLAIMER */'):I('/* ── KEVIN HARSH CARD')] + s[I('.fade-up {'):I('</style>')]
css = '\n'.join(l for l in css.split('\n') if not re.search(r'\.(story|stories|brand-|modal)', l))
css = css.replace('.page-consent','.page-consent-unused')
css += (TPL / 'results.css').read_text(encoding='utf-8')
nav = s[I('<nav>'):I('<div class="page-header')].replace('class="nav-link">Client results','class="nav-link active">Client results',1)
tail = s[I('<div class="disclaimer'):I('<script>')]
menu_js = s[s.rindex('<script>'):]

_data = json.load(open(ROOT / 'data' / 'clients.json', encoding='utf-8'))
C = _data['clients']
ASOF, ASOF_LONG = _data['as_of_label'], _data['as_of_long']
def money(v): return '${:,}'.format(v)
def k(v): return ('$%gM' % round(v/1e6,2)) if v>=1e6 else ('$%gK' % round(v/1e3))
for c in C:
    c['gain']=round((c['end']/c['start']-1)*100,1); c['mult']=round(c['end']/c['start'],1)
tot_s=sum(c['start'] for c in C); tot_e=sum(c['end'] for c in C); tot_g=round((tot_e/tot_s-1)*100,1)
e=html.escape
rows=[]
for c in sorted(C,key=lambda c:-c['gain']):
    body=[f'<p>{c["months"]} months on {e(c["ex"])}, running since {c["since"]}.' + (f' {e(c["note"])}' if c.get('note') else '') + '</p>']
    right=[]
    if c['quote']: right.append(f'<blockquote>“{e(c["quote"])}”</blockquote>')
    right.append(f'<button type="button" class="shot-btn" data-dash="{c["id"]}">View dashboard</button>')
    rows.append(f'''    <details class="row" id="client-{c["id"]}" data-id="{c["id"]}" data-gain="{c["gain"]}" data-size="{c["end"]}" data-months="{c["months"]}">
      <summary>
        <span><span class="row-name">{e(c["name"])}</span>{"<span class=\"row-meta\"><span class=\"founder\">Owner’s account</span></span>" if c.get("founder") else ""}</span>
        <span class="num n-start">{money(c["start"])}</span>
        <span class="num n-end" data-from="{k(c["start"])}">{money(c["end"])}</span>
        <span class="num gain">+{c["gain"]}%</span>
        <span class="num n-mult">{c["mult"]}×</span>
        <span class="chev" aria-hidden="true"></span>
      </summary>
      <div class="row-body">
        {''.join(body)}
        <div>{''.join(right)}</div>
      </div>
    </details>''')

kev=C[0]
main=f'''<header class="page-header">
  <h1>See how traders are<br>growing with AutoBot.</h1>
</header>

<figure class="slope" id="slope">
  <svg class="slope-svg" id="slope-svg" role="img" aria-labelledby="slope-title slope-desc">
    <title id="slope-title">Each client's account, from starting amount to @@ASOF@@ value</title>
    <desc id="slope-desc">{e('; '.join(f"{c['name']}: {money(c['start'])} to {money(c['end'])}, +{c['gain']}%" for c in C))}.</desc>
  </svg>
</figure>

<figure class="pull">
  <span class="pull-mark" aria-hidden="true">“</span>
  <blockquote>“{e(kev["quote"])}”</blockquote>
  <figcaption><b>{e(kev["name"])}</b></figcaption>
</figure>

<section class="ledger" aria-labelledby="ledger-title">
  <div class="ledger-top">
    <h2 id="ledger-title">Every account</h2>
    <div class="sorter" role="group" aria-label="Sort accounts">
      <button type="button" data-sort="gain" aria-pressed="true">Gain</button>
      <button type="button" data-sort="size" aria-pressed="false">Account size</button>
      <button type="button" data-sort="months" aria-pressed="false">Time running</button>
    </div>
  </div>
  <div class="cols" aria-hidden="true"><span>Client</span><span>Invested</span><span>@@ASOF@@</span><span>Gain</span><span>Growth</span><span></span></div>
  <div id="rows">
{chr(10).join(rows)}
  </div>
  <div class="ledger-total">
    <span class="row-name">All eight accounts</span>
    <span class="num n-start">{money(tot_s)}</span>
    <span class="num n-end" data-from="{k(tot_s)}">{money(tot_e)}</span>
    <span class="num gain">+{tot_g}%</span>
    <span class="num n-mult">{round(tot_e/tot_s,1)}×</span>
    <span class="spacer"></span>
  </div>
</section>

'''
dialog='''<dialog class="dash" id="dash" aria-labelledby="dash-name">
  <div class="dash-card" id="dash-card"></div>
</dialog>
'''
chart_data=json.dumps([dict({k2:c[k2] for k2 in ('id','name','short','start','end','gain','mult','ex','since','months','quote','shot')}, founder=bool(c.get('founder'))) for c in C])
js='''<script>
const CLIENTS = %s;

/* ── Slope chart: start → @@ASOF@@, log scale ── */
(function(){
  const fig = document.getElementById('slope'), svg = document.getElementById('slope-svg');
  const NS = 'http://www.w3.org/2000/svg';
  const fmtK = v => v >= 1e6 ? '$' + (v/1e6).toFixed(2).replace(/0$/,'') + 'M' : '$' + Math.round(v/1e3) + 'K';
  function el(name, attrs, parent){ const n = document.createElementNS(NS, name); for (const a in attrs) n.setAttribute(a, attrs[a]); if (parent) parent.appendChild(n); return n; }
  // keep labels from overlapping: push apart to a minimum gap, then keep inside bounds
  function spread(items, gap, lo, hi){
    items.sort((a,b) => a.y - b.y);
    for (let it = 0; it < 60; it++){
      let moved = false;
      for (let i = 1; i < items.length; i++){
        const d = items[i].y - items[i-1].y;
        if (d < gap){ const push = (gap - d)/2; items[i-1].y -= push; items[i].y += push; moved = true; }
      }
      if (items[0].y < lo){ const s = lo - items[0].y; items.forEach(x => x.y += s); }
      const last = items[items.length-1]; if (last.y > hi){ const s = last.y - hi; items.forEach(x => x.y -= s); }
      if (!moved) break;
    }
    return items;
  }
  function draw(animate){
    const W = fig.clientWidth, narrow = W < 640;
    const H = narrow ? 420 : 500, top = 40, bottom = H - 18;
    const xL = narrow ? 52 : 92, xR = W - (narrow ? 112 : 275);
    const lo = Math.log(15000), hi = Math.log(1500000);
    const y = v => bottom - (Math.log(v) - lo) / (hi - lo) * (bottom - top);
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('height', H);
    [...svg.querySelectorAll(':scope > g')].forEach(g => g.remove());
    const base = el('g', {}, svg);
    el('line', {x1:xL, x2:xL, y1:top-14, y2:bottom, class:'slope-rail'}, base);
    el('line', {x1:xR, x2:xR, y1:top-14, y2:bottom, class:'slope-rail'}, base);
    el('text', {x:xL, y:16, 'text-anchor':'middle', class:'slope-head'}, base).textContent = 'Invested';
    el('text', {x:xR, y:16, 'text-anchor':'middle', class:'slope-head'}, base).textContent = '@@ASOF@@';
    const L = spread(CLIENTS.map(c => ({c, y: y(c.start)})), 17, top, bottom);
    const R = spread(CLIENTS.map(c => ({c, y: y(c.end)})), narrow ? 19 : 22, top, bottom);
    const order = [...CLIENTS].sort((a,b) => b.gain - a.gain).map(c => c.id);
    CLIENTS.forEach(c => {
      const g = el('g', {class:'slope-client', 'data-id':c.id, tabindex:'0', role:'button', 'aria-label': c.name + ', ' + fmtK(c.start) + ' to ' + fmtK(c.end) + ', plus ' + c.gain + ' percent. Show details.'}, svg);
      g.style.setProperty('--delay', (order.indexOf(c.id) * 0.07) + 's');
      const y1 = y(c.start), y2 = y(c.end);
      const line = el('line', {x1:xL, y1, x2:xR, y2, class:'slope-line'}, g);
      line.style.setProperty('--len', Math.hypot(xR-xL, y2-y1));
      el('circle', {cx:xL, cy:y1, r:3.6, class:'slope-dot-start'}, g);
      el('circle', {cx:xR, cy:y2, r:3.6, class:'slope-dot-end'}, g);
      const l = L.find(o => o.c === c), r = R.find(o => o.c === c);
      const lab = el('g', {class:'slope-label'}, g);
      if (Math.abs(l.y - y1) > 1) el('line', {x1:xL-6, y1:y1, x2:xL-12, y2:l.y, class:'slope-leader'}, lab);
      el('text', {x:xL-14, y:l.y+4, 'text-anchor':'end', class:'slope-amt'}, lab).textContent = fmtK(c.start);
      if (Math.abs(r.y - y2) > 1) el('line', {x1:xR+6, y1:y2, x2:xR+12, y2:r.y, class:'slope-leader'}, lab);
      const t = el('text', {x:xR+14, y:r.y+4.5, class:'slope-name'}, lab);
      t.textContent = c.founder ? (narrow ? 'Owner' : c.name + ' (owner)') : (narrow ? c.short : c.name);
      const gain = el('tspan', {class:'slope-gain', dx:'8'}, t); gain.textContent = '+' + Math.round(c.gain) + '%%';
      if (!narrow){ const amt = el('tspan', {class:'slope-gain', dx:'8'}, t); amt.textContent = fmtK(c.end); }
    });
    fig.classList.toggle('animate', !!animate);
  }
  let drawn = false, lastW = 0;
  const io = new IntersectionObserver(es => { if (es[0].isIntersecting && !drawn){ drawn = true; draw(true); io.disconnect(); } }, {threshold: 0.25});
  draw(false); lastW = fig.clientWidth; io.observe(fig);
  window.addEventListener('resize', () => { if (fig.clientWidth !== lastW){ lastW = fig.clientWidth; draw(false); } });

  /* link chart ↔ rows */
  function focus(id){ fig.classList.toggle('is-focusing', !!id);
    svg.querySelectorAll('.slope-client').forEach(g => g.classList.toggle('is-on', g.dataset.id === id));
    document.querySelectorAll('.row').forEach(r => r.classList.toggle('is-on', r.dataset.id === id)); }
  svg.addEventListener('mouseover', e => { const g = e.target.closest('.slope-client'); if (g) focus(g.dataset.id); });
  svg.addEventListener('mouseleave', () => focus(null));
  svg.addEventListener('focusin', e => { const g = e.target.closest('.slope-client'); if (g) focus(g.dataset.id); });
  svg.addEventListener('focusout', () => focus(null));
  function openRow(id){ const r = document.getElementById('client-' + id); if (!r) return; r.open = true; r.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block:'center'}); r.querySelector('summary').focus({preventScroll:true}); }
  svg.addEventListener('click', e => { const g = e.target.closest('.slope-client'); if (g) openRow(g.dataset.id); });
  svg.addEventListener('keydown', e => { const g = e.target.closest('.slope-client'); if (g && (e.key === 'Enter' || e.key === ' ')){ e.preventDefault(); openRow(g.dataset.id); } });
  document.getElementById('rows').addEventListener('mouseover', e => { const r = e.target.closest('.row'); if (r) focus(r.dataset.id); });
  document.getElementById('rows').addEventListener('mouseleave', () => focus(null));
})();

/* ── Sorting ── */
document.querySelectorAll('.sorter button').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.sorter button').forEach(x => x.setAttribute('aria-pressed', x === b));
  const key = b.dataset.sort, wrap = document.getElementById('rows');
  [...wrap.children].sort((a,c) => parseFloat(c.dataset[key]) - parseFloat(a.dataset[key])).forEach(r => wrap.appendChild(r));
}));

/* ── Client dashboard card (real figures only) ── */
(function(){
  const dlg = document.getElementById('dash'), card = document.getElementById('dash-card');
  const usd = v => '$' + Math.round(v).toLocaleString('en-US');
  const esc = t => String(t).replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  function render(c){
    const pctS = (c.start / c.end * 100).toFixed(1);
    card.innerHTML = `
      <div class="dash-bar"><span><strong>AutoBot</strong>Client account</span><button type="button" class="dash-close" data-close>Close</button></div>
      <div class="dash-head">
        <h2 class="dash-name" id="dash-name">${esc(c.name)}${c.founder ? '<span class="dash-owner">Owner’s account</span>' : ''}</h2>
        <p class="dash-meta">${esc(c.ex)}, ${c.since} to @@ASOF@@, ${c.months} months${c.founder ? '. $50,000 to start, $50,000 added after 12 months' : ''}</p>
      </div>
      <div class="dash-hero"><span class="dash-gain">+${c.gain.toFixed(1)}%%</span><span class="dash-path">${usd(c.start)} → ${usd(c.end)}</span></div>
      <div class="dash-bars" aria-hidden="true">
        <span>Invested</span><span class="dash-track"><span class="dash-fill" style="width:${pctS}%%"></span></span><span class="v">${usd(c.start)}</span>
        <span>@@ASOF@@</span><span class="dash-track"><span class="dash-fill end" style="width:100%%"></span></span><span class="v">${usd(c.end)}</span>
      </div>
      <div class="dash-stats">
        <div class="dash-stat"><span>Invested</span><b>${usd(c.start)}</b></div>
        <div class="dash-stat"><span>@@ASOF@@ value</span><b>${usd(c.end)}</b></div>
        <div class="dash-stat"><span>Net gain</span><b class="up">+${usd(c.end - c.start)}</b></div>
        <div class="dash-stat"><span>Growth</span><b>${c.mult}×</b></div>
      </div>
      ${c.quote ? `<blockquote class="dash-quote">“${esc(c.quote)}”<cite>${esc(c.name)}</cite></blockquote>` : ''}
      <div class="dash-foot"><span>Past performance does not guarantee future results.</span>${c.shot ? '<button type="button" class="dash-full" data-full>Full dashboard from May 2026</button>' : ''}</div>`;
    const full = card.querySelector('[data-full]');
    if (full) full.addEventListener('click', () => {
      full.remove();
      const img = new Image(); img.className = 'dash-img'; img.src = c.shot; img.alt = c.name + "'s full AutoBot dashboard";
      card.appendChild(img);
    });
  }
  document.querySelectorAll('[data-dash]').forEach(b => b.addEventListener('click', () => {
    render(CLIENTS.find(c => c.id === b.dataset.dash)); dlg.showModal(); dlg.scrollTop = 0;
    card.querySelector('[data-close]').focus();
  }));
  dlg.addEventListener('click', e => { if (e.target === dlg || e.target.closest('[data-close]')) dlg.close(); });
})();

/* Fade-in for the closing sections */
const observer = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting){ e.target.classList.add('visible'); observer.unobserve(e.target); } }), { threshold: 0.05 });
document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
</script>
''' % chart_data
head = head.replace('Real, verified AutoBot client results — live account screenshots and returns from real Bybit, Hyperliquid, and Binance accounts.', 'AutoBot client results: what seven clients and our founder invested, and what their accounts held in @@ASOF@@, shared with their consent.')
head = head.replace('Real, verified client results from real exchange accounts.', 'What AutoBot clients invested, and what their accounts held in @@ASOF@@. Shared with their consent.')
tail = tail.replace('All results shown are from real AutoBot users sourced from verified client dashboards.', 'Results are from real AutoBot clients and our founder’s own account. Figures are provided by each client and shown with their consent.')
import re as _re
tail = _re.sub(r'<div class="disclaimer[^"]*">.*?</div>\s*', '''<section class="notes" aria-labelledby="notes-h">
  <p id="notes-h" class="notes-h">Notes</p>
  <ol>
    <li>Figures are as of @@ASOFLONG@@, provided by each client and shown with their consent. The founder's account is included and labelled.</li>
    <li>Gain is the current account value compared with the total amount invested, including any money added later.</li>
    <li>Results vary with market conditions, capital, plan and the risk level each client chooses. Past performance does not guarantee future results.</li>
    <li>Trading crypto involves substantial risk of loss. AutoBot is not investment advice.</li>
  </ol>
</section>

''', tail, count=1, flags=_re.S)
out = head + css + '\n</style>\n</head>\n<body>\n\n' + nav + main + tail + dialog + js + menu_js
out = out.replace('@@ASOF@@', ASOF).replace('@@ASOFLONG@@', ASOF_LONG)
(ROOT / 'results.html').write_text(out, encoding='utf-8')
print('written', len(out), 'bytes; totals', tot_s, tot_e, tot_g)
