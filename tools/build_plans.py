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

CSS='''
/* ── Plans ── */
.pl-head{padding:148px 64px 0;max-width:1312px;margin:0 auto;}
.pl-label{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--gray);margin-bottom:20px;}
.pl-head h1{font-family:'Playfair Display',serif;font-weight:400;font-size:clamp(36px,4.3vw,60px);line-height:1.07;letter-spacing:-.025em;}
.pl-head p{font-size:17px;line-height:1.65;color:var(--gray-mid);max-width:34em;margin-top:22px;}
.pl-wrap{max-width:1312px;margin:0 auto;padding:0 64px;}
.pl-cards{display:grid;grid-template-columns:1fr 1fr;margin-top:64px;border-top:1px solid var(--black);}
.pl-card{padding:40px 40px 44px 0;display:flex;flex-direction:column;}
.pl-card+.pl-card{padding-left:40px;padding-right:40px;background:var(--black);color:var(--white);}
.pl-name{font-family:'Playfair Display',serif;font-size:30px;letter-spacing:-.015em;}
.pl-tag{font-size:13px;color:var(--gray);margin-top:6px;}
.pl-card+.pl-card .pl-tag{color:rgba(242,241,237,.55);}
.pl-price{font-family:'Playfair Display',serif;font-size:clamp(56px,6vw,80px);line-height:1;letter-spacing:-.03em;margin-top:34px;}
.pl-price small{font-family:'DM Sans',sans-serif;font-size:15px;letter-spacing:0;color:var(--gray);margin-left:8px;}
.pl-card+.pl-card .pl-price small{color:rgba(242,241,237,.55);}
.pl-list{list-style:none;margin:30px 0 34px;padding:0;border-top:1px solid var(--border);}
.pl-card+.pl-card .pl-list{border-color:rgba(242,241,237,.14);}
.pl-list li{padding:12px 0 12px 17px;border-bottom:1px solid var(--border);font-size:15px;position:relative;}
.pl-card+.pl-card .pl-list li{border-color:rgba(242,241,237,.14);}
.pl-list li::before{content:'';position:absolute;left:0;top:21px;width:5px;height:5px;border-radius:50%;background:currentColor;opacity:.6;}
.pl-list li.plus{font-weight:500;}
.pl-btn{margin-top:auto;align-self:flex-start;font:500 15px 'DM Sans',sans-serif;text-decoration:none;padding:15px 30px;background:var(--black);color:var(--white);}
.pl-card+.pl-card .pl-btn{background:var(--white);color:var(--black);}
.pl-btn:hover{opacity:.85;}
sup.fn{font-family:'DM Mono',monospace;font-size:.62em;margin-left:2px;}
sup.fn a{color:inherit;text-decoration:none;opacity:.6;}
.pl-sec{margin-top:110px;}
.pl-sec-head{display:flex;justify-content:space-between;align-items:baseline;gap:24px;flex-wrap:wrap;padding-bottom:16px;border-bottom:1px solid var(--black);}
.pl-sec-head h2{font-family:'Playfair Display',serif;font-weight:400;font-size:clamp(28px,2.6vw,36px);letter-spacing:-.02em;}
.pl-sec-head p{font-size:14px;color:var(--gray);}
.pl-table{width:100%;border-collapse:collapse;font-size:15px;}
.pl-table th{font-weight:400;text-align:left;font-size:12px;color:var(--gray);padding:14px 16px 12px 0;border-bottom:1px solid var(--border);}
.pl-table td{padding:18px 16px 18px 0;border-bottom:1px solid var(--border);vertical-align:top;line-height:1.5;}
.pl-table td:first-child{color:var(--gray-mid);width:30%;}
.pl-table td:nth-child(2){width:32%;}
.pl-table td.pro{font-weight:500;}
.pl-signals{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));}
.pl-sig{padding:28px 24px 30px 0;border-bottom:1px solid var(--border);}
.pl-sig+.pl-sig{padding-left:24px;border-left:1px solid var(--border);}
.pl-sig h3{font-family:'Playfair Display',serif;font-weight:400;font-size:22px;letter-spacing:-.01em;}
.pl-sig p{font-size:14px;line-height:1.6;color:var(--gray-mid);margin-top:8px;}
.pl-who{display:inline-block;margin-top:16px;font-size:12px;border:1px solid var(--border);border-radius:999px;padding:3px 10px;color:var(--gray-mid);}
.pl-who.pro{background:var(--black);color:var(--white);border-color:var(--black);}
.pl-notes{margin:110px auto 56px;max-width:1312px;padding:0 64px;}
.pl-notes ol{margin:14px 0 0;padding-left:18px;max-width:880px;}
.pl-notes li{font-size:12.5px;line-height:1.7;color:var(--gray);margin-bottom:6px;}
.pl-notes p{font-size:12px;color:var(--gray);text-transform:uppercase;font-family:'DM Mono',monospace;letter-spacing:.08em;}
@media(max-width:1024px) and (min-width:769px){.pl-head{padding:120px 40px 0;}.pl-wrap,.pl-notes{padding:0 40px;}}
@media(max-width:768px){
 .pl-head{padding:100px 24px 0;}.pl-wrap,.pl-notes{padding:0 16px;}
 .pl-cards{grid-template-columns:1fr;}
 .pl-card{padding:32px 0 36px;}
 .pl-card+.pl-card{margin:0 -16px;padding:32px 16px 36px;}
 .pl-signals{grid-template-columns:1fr 1fr;}
 .pl-sig,.pl-sig+.pl-sig{padding:22px 12px 24px 0;border-left:none;}
 .pl-sig:nth-child(even){padding-left:12px;border-left:1px solid var(--border);}
 .pl-table td:first-child{width:auto;}
 .pl-table thead{display:none;}
 .pl-table tr{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid var(--border);padding:14px 0;}
 .pl-table td,.pl-table td:first-child,.pl-table td:nth-child(2){border:none;padding:0 10px 0 0;width:auto;}
 .pl-table td:first-child{grid-column:1/-1;font-size:13px;margin-bottom:6px;}
 .pl-table td:nth-child(2)::before{content:'AutoBot';display:block;font-size:11px;color:var(--gray);}
 .pl-table td:nth-child(3)::before{content:'AutoBot Pro';display:block;font-size:11px;color:var(--gray);}
 .pl-sec{margin-top:80px;}
}
'''
fn=lambda n:'<sup class="fn"><a href="#fn%d" aria-label="Note %d">%d</a></sup>'%(n,n,n)
MAIN=f'''<header class="pl-head">
  <h1>Two plans.<br>One engine.</h1>
</header>

<div class="pl-wrap">
  <section class="pl-cards" aria-label="Plans and prices">
    <div class="pl-card">
      <div class="pl-name">AutoBot</div>
      <div class="pl-price">$5,000<small>per year</small></div>
      <ul class="pl-list">
        <li>Trades 24/7 in your own exchange account</li>
        <li>Follows price and trend signals</li>
        <li>Same position size on every trade</li>
        <li>Built-in risk controls{fn(1)}</li>
        <li>Client dashboard and monthly statements</li>
        <li>Standard support</li>
      </ul>
      <a class="pl-btn" href="index.html#contact">Start with AutoBot</a>
    </div>
    <div class="pl-card">
      <div class="pl-name">AutoBot Pro</div>
      <div class="pl-price">$10,000<small>per year</small></div>
      <ul class="pl-list">
        <li>Everything in AutoBot</li>
        <li class="plus">Also reads social sentiment, news and on-chain flows{fn(2)}</li>
        <li class="plus">Sizes up when signals agree, down when they don't</li>
        <li class="plus">Adjusts as conditions change, not on a review cycle</li>
        <li class="plus">Priority support</li>
      </ul>
      <a class="pl-btn" href="index.html#contact">Start with AutoBot Pro</a>
    </div>
  </section>

  <section class="pl-sec" aria-labelledby="diff">
    <div class="pl-sec-head"><h2 id="diff">Side by side</h2></div>
    <table class="pl-table">
      <thead><tr><th></th><th>AutoBot</th><th>AutoBot Pro</th></tr></thead>
      <tbody>
        <tr><td>Where it trades</td><td>Your Bybit or Hyperliquid account</td><td>Your Bybit or Hyperliquid account</td></tr>
        <tr><td>Who holds your money</td><td>You. Funds never leave your exchange{fn(3)}</td><td>You. Funds never leave your exchange{fn(3)}</td></tr>
        <tr><td>Hours</td><td>24/7</td><td>24/7</td></tr>
        <tr><td>Order speed</td><td>Under 50ms{fn(4)}</td><td>Under 50ms{fn(4)}</td></tr>
        <tr><td>What it watches</td><td>Price and trend</td><td class="pro">Price and trend, social sentiment, news, on-chain flows</td></tr>
        <tr><td>Position size</td><td>The same on every trade</td><td class="pro">Larger when signals agree, smaller when they don't</td></tr>
        <tr><td>How it adapts</td><td>Our team reviews it periodically</td><td class="pro">Adjusts automatically as signals change</td></tr>
        <tr><td>Your risk level</td><td>You choose, 50% to 100%</td><td>You choose, 50% to 100%</td></tr>
        <tr><td>Support</td><td>Standard</td><td class="pro">Priority</td></tr>
        <tr><td>Price</td><td>$5,000 per year</td><td class="pro">$10,000 per year</td></tr>
      </tbody>
    </table>
  </section>

  <section class="pl-sec" aria-labelledby="sig">
    <div class="pl-sec-head"><h2 id="sig">What each plan watches</h2></div>
    <div class="pl-signals">
      <div class="pl-sig"><h3>Price and trend</h3><p>Chart patterns and momentum across every pair.</p><span class="pl-who">Both plans</span></div>
      <div class="pl-sig"><h3>Social sentiment</h3><p>What traders and crypto voices are saying, as it happens.</p><span class="pl-who pro">Pro</span></div>
      <div class="pl-sig"><h3>News and macro</h3><p>Headlines and events that can move the market quickly.</p><span class="pl-who pro">Pro</span></div>
      <div class="pl-sig"><h3>On-chain flows</h3><p>Where large wallets are moving money on the blockchain.</p><span class="pl-who pro">Pro</span></div>
    </div>
  </section>
</div>

<section class="pl-notes" aria-labelledby="notes">
  <p id="notes">Notes</p>
  <ol>
    <li id="fn1">Risk controls include stop-losses, position size limits and a drawdown limit, applied automatically on every trade. They reduce risk but cannot prevent losses.</li>
    <li id="fn2">Additional signals inform position size and timing. Using more signals does not guarantee better or faster returns.</li>
    <li id="fn3">AutoBot connects with an exchange API key that can place trades but cannot withdraw or transfer funds. You can revoke it at any time from your exchange.</li>
    <li id="fn4">Typical time from a signal to the order being sent to the exchange. Fill times depend on the exchange and market conditions.</li>
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
out=head+css+CSS+'\n</style>\n</head>\n<body>\n\n'+nav+MAIN+foot+menu_js
(ROOT / 'plans.html').write_text(out, encoding='utf-8'); print('plans.html written', len(out))
