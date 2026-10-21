// Server-side auth for AutoBot Netlify functions.
//
// The browser sends its Clerk session token as `Authorization: Bearer <token>`.
// We verify that token's RS256 signature against Clerk's public keys (JWKS),
// check it hasn't expired, then load the user from Clerk. Admin status is decided
// HERE, on the server — never trust an "is admin" check done in the browser.
//
// No npm dependencies: uses Node's built-in crypto.

var crypto = require('crypto');

var CLERK_API = 'https://api.clerk.com/v1';
var CLOCK_SKEW_S = 10;
var JWKS_TTL_MS = 60 * 60 * 1000;

var DEFAULT_ADMIN_EMAILS = ['autobottradingai@gmail.com', 'manuelavila2311@gmail.com'];
var DEFAULT_ALLOWED_ORIGINS = ['https://autobot.trading', 'https://www.autobot.trading'];

var _jwks = null, _jwksAt = 0;

function listFromEnv(name, fallback) {
  var v = process.env[name];
  if (!v) return fallback;
  return v.split(',').map(function (s) { return s.trim().toLowerCase(); }).filter(Boolean);
}

function b64urlDecode(s) {
  return Buffer.from(String(s).replace(/-/g, '+').replace(/_/g, '/'), 'base64');
}

function jsonResponse(statusCode, obj) {
  return {
    statusCode: statusCode,
    headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
    body: JSON.stringify(obj)
  };
}

function corsPreflight(methods) {
  return {
    statusCode: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Allow-Methods': methods + ', OPTIONS'
    },
    body: ''
  };
}

async function clerkGet(path, secretKey) {
  var r = await fetch(CLERK_API + path, { headers: { Authorization: 'Bearer ' + secretKey } });
  if (!r.ok) throw new Error('Clerk ' + path + ' failed (' + r.status + ')');
  return r.json();
}

async function getJwks(secretKey, forceRefresh) {
  if (!forceRefresh && _jwks && Date.now() - _jwksAt < JWKS_TTL_MS) return _jwks;
  var data = await clerkGet('/jwks', secretKey);
  _jwks = (data && data.keys) || [];
  _jwksAt = Date.now();
  return _jwks;
}

// Verifies a Clerk session JWT. Returns its payload, or throws.
// `opts.getKeys(kid)` can be injected for tests.
async function verifySessionToken(token, opts) {
  opts = opts || {};
  var parts = String(token || '').split('.');
  if (parts.length !== 3) throw new Error('malformed token');

  var header, payload;
  try {
    header = JSON.parse(b64urlDecode(parts[0]).toString('utf8'));
    payload = JSON.parse(b64urlDecode(parts[1]).toString('utf8'));
  } catch (e) { throw new Error('malformed token'); }
  if (header.alg !== 'RS256') throw new Error('unexpected alg');

  var findKey = opts.getKeys || async function (kid) {
    var keys = await getJwks(opts.secretKey);
    var k = keys.find(function (x) { return x.kid === kid; });
    if (!k) { keys = await getJwks(opts.secretKey, true); k = keys.find(function (x) { return x.kid === kid; }); }
    return k;
  };
  var jwk = await findKey(header.kid);
  if (!jwk) throw new Error('unknown signing key');

  var publicKey = crypto.createPublicKey({ key: jwk, format: 'jwk' });
  var ok = crypto.verify('RSA-SHA256', Buffer.from(parts[0] + '.' + parts[1]), publicKey, b64urlDecode(parts[2]));
  if (!ok) throw new Error('bad signature');

  var now = Math.floor((opts.now || Date.now()) / 1000);
  if (typeof payload.exp !== 'number' || payload.exp + CLOCK_SKEW_S < now) throw new Error('token expired');
  if (typeof payload.nbf === 'number' && payload.nbf - CLOCK_SKEW_S > now) throw new Error('token not yet valid');
  if (!payload.sub) throw new Error('token has no subject');

  var allowed = opts.allowedOrigins || listFromEnv('ALLOWED_ORIGINS', DEFAULT_ALLOWED_ORIGINS);
  if (payload.azp && allowed.indexOf(String(payload.azp).toLowerCase()) === -1) throw new Error('token from unexpected origin');

  return payload;
}

function primaryEmail(user) {
  var list = (user && user.email_addresses) || [];
  var p = list.find(function (e) { return e.id === user.primary_email_address_id; }) || list[0];
  return p ? String(p.email_address || '').toLowerCase() : '';
}

function isAdminUser(user) {
  if (!user) return false;
  // public_metadata can only be written server-side (Clerk dashboard / backend API), so it's safe to trust.
  // Never use unsafe_metadata here — the user can edit that themselves.
  if (user.public_metadata && user.public_metadata.is_admin === true) return true;
  var admins = listFromEnv('ADMIN_EMAILS', DEFAULT_ADMIN_EMAILS);
  var email = primaryEmail(user);
  if (!email) return false;
  var addr = (user.email_addresses || []).find(function (e) { return String(e.email_address).toLowerCase() === email; });
  var verified = !addr || !addr.verification || addr.verification.status === 'verified';
  return verified && admins.indexOf(email) !== -1;
}

// Returns { user, claims } on success, or { response } with a 401/403/500 to return as-is.
async function requireUser(event, opts) {
  opts = opts || {};
  var secretKey = process.env.CLERK_SECRET_KEY;
  if (!secretKey) return { response: jsonResponse(500, { error: 'Server not configured' }) };

  var h = event.headers || {};
  var auth = h.authorization || h.Authorization || '';
  var m = /^Bearer\s+(.+)$/i.exec(auth);
  if (!m) return { response: jsonResponse(401, { error: 'Sign in required' }) };

  var claims;
  try { claims = await verifySessionToken(m[1], { secretKey: secretKey }); }
  catch (e) { return { response: jsonResponse(401, { error: 'Session invalid or expired — please sign in again' }) }; }

  var user;
  try { user = await clerkGet('/users/' + encodeURIComponent(claims.sub), secretKey); }
  catch (e) { return { response: jsonResponse(401, { error: 'Account not found' }) }; }
  if (user.banned || user.locked) return { response: jsonResponse(403, { error: 'Account disabled' }) };

  if (opts.admin && !isAdminUser(user)) return { response: jsonResponse(403, { error: 'Admins only' }) };
  return { user: user, claims: claims, isAdmin: isAdminUser(user), secretKey: secretKey };
}

function requireAdmin(event) { return requireUser(event, { admin: true }); }

function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}

module.exports = {
  verifySessionToken: verifySessionToken,
  requireUser: requireUser,
  requireAdmin: requireAdmin,
  isAdminUser: isAdminUser,
  primaryEmail: primaryEmail,
  jsonResponse: jsonResponse,
  corsPreflight: corsPreflight,
  escapeHtml: escapeHtml
};
