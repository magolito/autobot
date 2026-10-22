#!/usr/bin/env python3
"""Builds plans.html (Plans page). Prices and plan copy live in this file. Run: python3 tools/build_pages.py"""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
base=(ROOT / 'tools' / 'templates' / 'base.html').read_text(encoding='utf-8')
I=base.index
head=base[:I('<style>')+len('<style>')]
head=head.replace('<title>Client Results — AutoBot</title>','<title>Plans — AutoBot</title>')
head=re.sub(r'<meta name="description" content="[^"]*">','<meta name="description" content="AutoBot and AutoBot Pro: two plans, one engine. Both trade 24/7 inside your own Bybit or Hyperliquid account. Compare what each plan watches, how it sizes trades, and what it costs.">',head)
head=re.sub(r'(property="og:title" content=")[^"]*','\\1Plans — AutoBot',head); head=re.sub(r'(name="twitter:title" content=")[^"]*','\\1Plans — AutoBot',head)
head=re.sub(r'(property="og:url" content=")[^"]*','\\1https://autobot.trading/plans',head)
head=re.sub(r'(property="og:description" content=")[^"]*','\\1Two plans, one engine. Compare AutoBot and AutoBot Pro.',head)
head=re.sub(r'(name="twitter:description" content=")[^"]*','\\1Two plans, one engine. Compare AutoBot and AutoBot Pro.',head)
css=base[I('<style>')+len('<style>'):I('/* STORY GRID */')]+base[I('/* DISCLAIMER */'):I('/* ── KEVIN HARSH CARD')]+base[I('.fade-up {'):I('</style>')]
css='\n'.join(l for l in css.split('\n') if not re.search(r'\.(story|stories|brand-|modal)',l))
nav=base[I('<nav>'):I('<div class="page-header')]
nav=nav.replace('class="nav-link active">Client results','class="nav-link">Client results').replace('<a href="plans.html" class="nav-link">Plans</a>','<a href="plans.html" class="nav-link active">Plans</a>')
foot=base[I('<footer>'):I('<script>')]
menu_js=base[base.rindex('<script>'):]

CSS=(ROOT / 'tools' / 'templates' / 'plans.css').read_text(encoding='utf-8')
fn=lambda n:'<sup class="fn"><a href="#fn%d" aria-label="Note %d">%d</a></sup>'%(n,n,n)
CHECK='<svg class="ck" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5l3.2 3L13 4.5"/></svg>'

def card(cls, name, price, items, cta, canvas=False):
    lis=''.join(f'<li{" class=\"plus\"" if plus else ""}>{CHECK}<span>{t}</span></li>' for t,plus in items)
    return f"""    <article class="pc {cls}">
      {'<canvas class="pc-field" aria-hidden="true"></canvas>' if canvas else ''}
      <h2 class="pc-name">{name}</h2>
      <div class="pc-price"><span class="pc-cur">$</span><b data-count="{price}">{price:,}</b><small>/ year</small></div>
      <ul class="pc-list">{lis}</ul>
      <a class="pc-btn" href="index.html#contact"><span>{cta}</span><i aria-hidden="true">→</i></a>
    </article>"""

SAME=[('Where it trades','Your Bybit or Hyperliquid account',''),('Who holds your money','You. Funds never leave your exchange',fn(3)),
      ('Hours','24/7',''),('Order speed','Under 50ms',fn(4)),('Your risk level','You choose, 50% to 100%','')]
DIFF=[('Built-in AI','Not included','Analyzes the market and adjusts continuously'),('What it watches','Price and trend','Price and trend, social sentiment, news, on-chain flows'),
      ('Position size','The same on every trade','Larger when signals agree, smaller when they don’t'),
      ('How it adapts','Our team reviews it periodically','Adjusts automatically as signals change'),
      ('Support','Standard','Priority'),('Price','$5,000 per year','$10,000 per year')]
rows=''.join(f'<div class="sx-row is-diff"><span class="sx-k">{k}</span><span class="sx-a">{a}</span><span class="sx-b">{b_}</span></div>' for k,a,b_ in DIFF)
rows+=''.join(f'<div class="sx-row is-same"><span class="sx-k">{k}</span><span class="sx-both"><span>{v}{n}</span></span></div>' for k,v,n in SAME)

SIG=[('trend','Price and trend','Chart patterns and momentum across every pair.',False,
      '<svg viewBox="0 0 120 48"><path class="sg-line" d="M2 40 L18 34 L30 37 L44 24 L56 28 L70 16 L84 20 L98 8 L118 12"/></svg>'),
     ('social','Social sentiment','What traders and crypto voices are saying, as it happens.',True,
      '<svg viewBox="0 0 120 48">'+''.join(f'<rect class="sg-bar" x="{8+i*16}" y="8" width="8" height="36" style="--i:{i}"/>' for i in range(7))+'</svg>'),
     ('news','News and macro','Headlines and events that can move the market quickly.',True,
      '<svg viewBox="0 0 120 48"><g class="sg-feed">'+''.join(f'<rect x="4" y="{4+i*12}" width="{[96,70,104,58,88,76,100,64][i]}" height="3" rx="1.5"/>' for i in range(8))+'</g></svg>'),
     ('chain','On-chain flows','Where large wallets are moving money on the blockchain.',True,
      '<svg viewBox="0 0 120 48"><path class="sg-link" id="sgp" d="M10 24 C34 2, 50 46, 60 24 S 92 4, 110 24"/><circle cx="10" cy="24" r="3.5"/><circle cx="60" cy="24" r="3.5"/><circle cx="110" cy="24" r="3.5"/><circle class="sg-pulse" r="2.6"><animateMotion dur="2.8s" repeatCount="indefinite" path="M10 24 C34 2, 50 46, 60 24 S 92 4, 110 24"/></circle></svg>')]
sig=''.join(f'<div class="sg sg-{k}{" sg-chain" if k=="chain" else ""}"><div class="sg-vis" aria-hidden="true">{svg}</div><div class="sg-top"><h3>{t}</h3><span class="sg-who{" pro" if pro else ""}">{"Pro" if pro else "Both plans"}</span></div><p>{d}</p></div>' for k,t,d,pro,svg in SIG)

import runpy
AI_ART=runpy.run_path(str(ROOT / 'tools' / 'art' / 'ai_chip.py'))['SVG']
MAIN=f'''<header class="pl-head">
  <h1 class="rx-title"><span class="ln"><span>Two plans.</span></span><span class="ln"><span>One engine.</span></span></h1>
</header>

<div class="pl-wrap">


  <section class="ai" aria-labelledby="ai-h">
    <div class="ai-copy">
      <span class="ai-k"><i></i>AutoBot Pro</span>
      <h2 id="ai-h">Built-in AI that adjusts<br>to the market, all the time</h2>
      <div class="ai-stats">
        <div><b>24/7</b><span>Always analyzing</span></div>
        <div><b>4</b><span>Signal types</span></div>
        <div><b>&lt;50ms</b><span>Signal to order{fn(4)}</span></div>
      </div>
    </div>
    <div class="ai-art">{AI_ART}</div>
  </section>

  <section class="pl-sec" aria-labelledby="diff">
    <div class="sx-head"><h2 id="diff">Side by side</h2><span>AutoBot</span><span class="sx-pro">AutoBot Pro</span></div>
    <div class="sx">{rows}</div>
  </section>

  <section class="pl-sec" aria-labelledby="sig">
    <div class="pl-sec-head"><h2 id="sig">What each plan watches</h2></div>
    <div class="sgs">{sig}</div>
  </section>

  <section class="pl-sec" aria-labelledby="pick"><div class="pl-sec-head"><h2 id="pick">Choose your plan</h2></div>
  <div class="pc-grid">
{card('pc-std','AutoBot',5000,[('Trades 24/7 in your own exchange account',0),('Follows price and trend signals',0),('Same position size on every trade',0),('Built-in risk controls'+fn(1),0),('Client dashboard and monthly statements',0),('Standard support',0)],'Start with AutoBot')}
{card('pc-pro','AutoBot Pro',10000,[('Everything in AutoBot',0),('Built-in AI that analyzes the market around the clock'+fn(5),1),('Also reads social sentiment, news and on-chain flows'+fn(2),1),('Sizes up when signals agree, down when they don’t',1),('Adjusts as conditions change, not on a review cycle',1),('Priority support',1)],'Start with AutoBot Pro',canvas=True)}
  </div></section>
</div>
<section class="pl-notes" aria-labelledby="notes">
  <p id="notes">Notes</p>
  <ol>
    <li id="fn1">Risk controls include stop-losses, position size limits and a drawdown limit, applied automatically on every trade. They reduce risk but cannot prevent losses.</li>
    <li id="fn2">Additional signals inform position size and timing. Using more signals does not guarantee better or faster returns.</li>
    <li id="fn3">AutoBot connects with an exchange API key that can place trades but cannot withdraw or transfer funds. You can revoke it at any time from your exchange.</li>
    <li id="fn4">Typical time from a signal to the order being sent to the exchange. Fill times depend on the exchange and market conditions.</li>
    <li id="fn5">The AI informs analysis, position size and timing within the risk limits you set. It does not guarantee returns and can be wrong.</li>
    <li>Prices are per year and exclude exchange fees. Trading crypto involves substantial risk of loss. Past performance, including client results on this site, does not guarantee future results. AutoBot is not investment advice.</li>
  </ol>
</section>

<div class="cta-band">
  <div class="cta-text">
    <h2>Not sure which<br><em>fits you?</em></h2>
  </div>
  <div class="cta-actions">
    <a href="index.html#contact" class="btn-w">Start Investing</a>
    <a href="results.html" class="btn-o">See client results</a>
  </div>
</div>

'''

JS="<script>\n"+(ROOT / 'tools' / 'templates' / 'motion.js').read_text(encoding='utf-8')+"""
/* Plans: Pro card field, price roll-up, reveals */
document.querySelectorAll('.pc-field').forEach(cv => dotField(cv, cv.parentElement, '242,241,237', {base: .14}));
onView(document.querySelectorAll('.pc'), c => { c.classList.add('in'); const b = c.querySelector('[data-count]'); countUp(b, +b.dataset.count, v => Math.round(v).toLocaleString('en-US'), 1500); }, 0.25);
onView(document.querySelectorAll('.sx-row, .sg'), el => el.classList.add('in'), 0.2);
</script>
"""
out=head+css+CSS+'\n</style>\n</head>\n<body>\n\n'+nav+MAIN+foot+JS+menu_js
(ROOT / 'plans.html').write_text(out, encoding='utf-8'); print('plans.html written', len(out))
