// Bybit V5 Unified Trading Account proxy for AutoBot.
var crypto = require('crypto');

var BYBIT_BASE = process.env.BYBIT_BASE || 'https://api.bytick.com';
var RECV_WINDOW = '5000';

function sign(apiKey, apiSecret, timestamp, queryString) {
  var payload = timestamp + apiKey + RECV_WINDOW + (queryString || '');
  return crypto.createHmac('sha256', apiSecret).update(payload).digest('hex');
}

async function bybitGet(path, params, apiKey, apiSecret) {
  var qs = Object.keys(params || {})
    .sort()
    .map(function(k){ return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]); })
    .join('&');
  var ts = Date.now().toString();
  var signature = sign(apiKey, apiSecret, ts, qs);
  var url = BYBIT_BASE + path + (qs ? ('?' + qs) : '');
  var r = await fetch(url, {
    method: 'GET',
    headers: {
      'X-BAPI-API-KEY': apiKey,
      'X-BAPI-SIGN': signature,
      'X-BAPI-TIMESTAMP': ts,
      'X-BAPI-RECV-WINDOW': RECV_WINDOW,
      'X-BAPI-SIGN-TYPE': '2',
      'Content-Type': 'application/json'
    }
  });
  var txt = await r.text();
  try { return JSON.parse(txt); }
  catch (e) {
    throw new Error('Bybit ' + path + ' returned non-JSON (status ' + r.status + '): ' + txt.slice(0, 200));
  }
}

function stripQuote(sym) {
  if (!sym) return '?';
  return String(sym).replace(/(USDT|USDC|USD|PERP)$/i, '') || sym;
}

function mapPositions(bybitPositions) {
  if (!Array.isArray(bybitPositions)) return [];
  return bybitPositions
    .filter(function(p){ return parseFloat(p.size || 0) > 0; })
    .map(function(p) {
      var size = parseFloat(p.size || 0);
      var isLong = (p.side || '').toLowerCase() === 'buy';
      var szi = isLong ? size : -size;
      var lev = parseFloat(p.leverage || 0) || 0;
      return {
        position: {
          coin: stripQuote(p.symbol),
          szi: szi.toString(),
          entryPx: String(p.avgPrice || p.entryPrice || 0),
          unrealizedPnl: String(p.unrealisedPnl || 0),
          positionValue: String(p.positionValue || 0),
          leverage: { value: lev, type: (p.tradeMode === 1 ? 'isolated' : 'cross') }
        }
      };
    });
}

function mapClosedPnlToFills(bybitClosed) {
  if (!Array.isArray(bybitClosed)) return [];
  return bybitClosed.map(function(r) {
    var closeSide = (r.side || '').toLowerCase();
    var wasLong = closeSide === 'sell';
    var dir = wasLong ? 'Close Long' : 'Close Short';
    var hlSide = wasLong ? 'A' : 'B';
    var pnl = parseFloat(r.closedPnl || 0);
    var exitPx = parseFloat(r.avgExitPrice || r.orderPrice || 0);
    var qty = parseFloat(r.qty || r.closedSize || 0);
    var t = parseInt(r.updatedTime || r.createdTime || 0, 10);
    return { closedPnl: pnl, dir: dir, side: hlSide, px: exitPx, sz: qty, time: t, coin: stripQuote(r.symbol) };
  });
}

async function fetchClerkUser(userId, secretKey) {
  var res = await fetch('https://api.clerk.com/v1/users/' + encodeURIComponent(userId), {
    headers: { 'Authorization': 'Bearer ' + secretKey, 'Content-Type': 'application/json' }
  });
  var txt = await res.text();
  if (!res.ok) throw new Error('Clerk user lookup failed (' + res.status + '): ' + txt.slice(0, 300));
  try { return JSON.parse(txt); }
  catch (e) { throw new Error('Clerk returned non-JSON for user ' + userId + ': ' + txt.slice(0, 200)); }
}

var auth = require('../lib/auth');

exports.handler = async function(event) {
  if (event.httpMethod === 'OPTIONS') return auth.corsPreflight('POST');
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'Method not allowed' };

  // Must be signed in. Clients may only read their OWN account; admins may read any client's.
  var gate = await auth.requireUser(event);
  if (gate.response) return gate.response;

  var cors = { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' };
  var stage = 'init';
  try {
    stage = 'parse-body';
    var body;
    try { body = JSON.parse(event.body || '{}'); }
    catch (eBody) { return { statusCode: 400, headers: cors, body: JSON.stringify({ error: 'Bad request body', stage: stage }) }; }
    var userId = body.user_id || gate.user.id;
    if (userId !== gate.user.id && !gate.isAdmin) {
      return { statusCode: 403, headers: cors, body: JSON.stringify({ error: 'Not allowed' }) };
    }

    var secretKey = gate.secretKey;

    stage = 'fetch-clerk-user';
    var user = await fetchClerkUser(userId, secretKey);

    stage = 'read-metadata';
    var priv = user.private_metadata;
    if (typeof priv === 'string') {
      try { priv = JSON.parse(priv); }
      catch (ePriv) { return { statusCode: 500, headers: cors, body: JSON.stringify({ error: 'Clerk private_metadata is not valid JSON: ' + ePriv.message, stage: stage }) }; }
    }
    priv = priv || {};

    var apiKey = priv.bybit_api_key;
    var apiSecret = priv.bybit_api_secret;
    if (!apiKey || !apiSecret) return { statusCode: 400, headers: cors, body: JSON.stringify({ error: 'Bybit API credentials not set for this client', stage: stage }) };

    stage = 'bybit-call';
    var results = await Promise.all([
      bybitGet('/v5/account/wallet-balance', { accountType: 'UNIFIED' }, apiKey, apiSecret),
      bybitGet('/v5/position/list', { category: 'linear', settleCoin: 'USDT' }, apiKey, apiSecret),
      bybitGet('/v5/position/closed-pnl', { category: 'linear', limit: '100' }, apiKey, apiSecret)
    ]);

    var walletResp = results[0] || {}, positionResp = results[1] || {}, closedResp = results[2] || {};
    var firstErr = [walletResp, positionResp, closedResp].find(function(r){ return r && r.retCode !== 0; });
    if (firstErr) return { statusCode: 502, headers: cors, body: JSON.stringify({ error: 'Bybit API error: ' + (firstErr.retMsg || 'unknown') + ' (code ' + firstErr.retCode + ')' }) };

    var walletList = (walletResp.result && walletResp.result.list) || [];
    var unified = walletList.find(function(w){ return (w.accountType || '').toUpperCase() === 'UNIFIED'; }) || walletList[0] || {};
    var totalEquity = parseFloat(unified.totalEquity || 0);

    var state = {
      marginSummary: { accountValue: totalEquity.toString(), totalRawUsd: totalEquity.toString(), totalNtlPos: unified.totalPerpValue || '0', totalMarginUsed: unified.totalInitialMargin || '0' },
      assetPositions: mapPositions((positionResp.result && positionResp.result.list) || []),
      withdrawable: (parseFloat(unified.totalAvailableBalance || 0)).toString()
    };
    var fills = mapClosedPnlToFills((closedResp.result && closedResp.result.list) || []);

    return { statusCode: 200, headers: cors, body: JSON.stringify({ state: state, fills: fills, _exchange: 'bybit' }) };
  } catch (e) {
    console.error('bybit-proxy [' + stage + ']:', e);
    return { statusCode: 500, headers: cors, body: JSON.stringify({ error: 'Could not load Bybit data (' + stage + ')', stage: stage }) };
  }
};
