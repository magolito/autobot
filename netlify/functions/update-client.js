var auth = require('../lib/auth');

var ACTIONS = ['approve', 'reject', 'update_expiry', 'set_manual_base', 'add_snapshot', 'delete_snapshot'];
var DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
function money(v) { var n = Number(v); return isFinite(n) ? Math.round(n * 100) / 100 : NaN; }

exports.handler = async function(event) {
  if (event.httpMethod === 'OPTIONS') return auth.corsPreflight('POST');
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'Method not allowed' };

  // Admins only — verified on the server from the caller's Clerk session.
  var gate = await auth.requireAdmin(event);
  if (gate.response) return gate.response;
  var secretKey = gate.secretKey;

  try {
    var body;
    try { body = JSON.parse(event.body || '{}'); }
    catch (e) { return auth.jsonResponse(400, { error: 'Bad request body' }); }

    var userId     = body.userId;
    var action     = body.action;      // 'approve', 'reject', or 'update_expiry'
    var newRisk    = body.risk_level;
    var expiryDate = body.expiry_date; // ISO date string e.g. '2026-10-01'

    if (!userId || typeof userId !== 'string' || !/^user_[A-Za-z0-9]+$/.test(userId)) {
      return auth.jsonResponse(400, { error: 'Missing or invalid userId.' });
    }
    if (ACTIONS.indexOf(action) === -1) {
      return auth.jsonResponse(400, { error: 'Unknown action.' });
    }
    if (action === 'approve' && newRisk !== undefined) {
      newRisk = Number(newRisk);
      if (!isFinite(newRisk) || newRisk < 0 || newRisk > 100) return auth.jsonResponse(400, { error: 'risk_level must be 0–100.' });
    }
    if (action === 'update_expiry' && !DATE_RE.test(String(expiryDate || ''))) {
      return auth.jsonResponse(400, { error: 'expiry_date must be YYYY-MM-DD.' });
    }
    // Monthly figures (for accounts we can't read live, e.g. Bybit)
    var snapDate = String(body.date || ''), balance = money(body.balance), deposit = money(body.deposit || 0);
    var baseCap = money(body.initial_capital), startDate = String(body.start_date || '');
    if (action === 'set_manual_base') {
      if (!(baseCap > 0)) return auth.jsonResponse(400, { error: 'Starting amount must be more than 0.' });
      if (!DATE_RE.test(startDate)) return auth.jsonResponse(400, { error: 'Start date must be YYYY-MM-DD.' });
    }
    if (action === 'add_snapshot') {
      if (!DATE_RE.test(snapDate)) return auth.jsonResponse(400, { error: 'Date must be YYYY-MM-DD.' });
      if (!(balance > 0)) return auth.jsonResponse(400, { error: 'Balance must be more than 0.' });
      if (!isFinite(deposit)) return auth.jsonResponse(400, { error: 'Money added must be a number (negative for a withdrawal).' });
    }
    if (action === 'delete_snapshot' && !DATE_RE.test(snapDate)) return auth.jsonResponse(400, { error: 'Date must be YYYY-MM-DD.' });

    // 1. Fetch the current user so we can merge metadata
    var getRes = await fetch('https://api.clerk.com/v1/users/' + encodeURIComponent(userId), {
      headers: { 'Authorization': 'Bearer ' + secretKey }
    });
    if (!getRes.ok) throw new Error('Could not fetch user from Clerk: ' + getRes.status);
    var user = await getRes.json();

    var currentPublic = user.public_metadata || {};
    var currentUnsafe = user.unsafe_metadata || {};
    var pending       = currentUnsafe.pending_risk_request || {};

    // 2. Build updated metadata
    var resolvedAt = new Date().toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
    var updatedPublic = Object.assign({}, currentPublic);
    var updatedUnsafe = currentUnsafe;

    if (action === 'approve' || action === 'reject') {
      updatedUnsafe = Object.assign({}, currentUnsafe, {
        pending_risk_request: Object.assign({}, pending, {
          status:      action === 'approve' ? 'approved' : 'rejected',
          resolved_at: resolvedAt
        })
      });
      if (action === 'approve' && newRisk !== undefined) updatedPublic.risk_level = newRisk;
    }
    if (action === 'update_expiry') updatedPublic.hl_api_key_expiry = expiryDate;
    if (action === 'set_manual_base') {
      updatedPublic.initial_capital = baseCap;
      updatedPublic.start_date = startDate;
      updatedPublic.data_mode = 'manual';
    }
    if (action === 'add_snapshot' || action === 'delete_snapshot') {
      var snaps = Array.isArray(currentPublic.manual_snapshots) ? currentPublic.manual_snapshots.slice() : [];
      snaps = snaps.filter(function (x) { return x && x.date !== snapDate; });   // same date = replace
      if (action === 'add_snapshot') snaps.push({ date: snapDate, balance: balance, deposit: deposit || 0 });
      snaps.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
      if (snaps.length > 120) snaps = snaps.slice(-120);                          // 10 years of monthly updates
      updatedPublic.manual_snapshots = snaps;
      updatedPublic.data_mode = 'manual';
    }

    // 3. Patch the user in Clerk
    var patchRes = await fetch('https://api.clerk.com/v1/users/' + encodeURIComponent(userId), {
      method: 'PATCH',
      headers: { 'Authorization': 'Bearer ' + secretKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ public_metadata: updatedPublic, unsafe_metadata: updatedUnsafe })
    });
    if (!patchRes.ok) throw new Error('Clerk PATCH failed ' + patchRes.status + ': ' + (await patchRes.text()));
    var updated = await patchRes.json();

    return auth.jsonResponse(200, {
      success:     true,
      action:      action,
      risk_level:  updated.public_metadata.risk_level,
      initial_capital: updated.public_metadata.initial_capital,
      start_date: updated.public_metadata.start_date,
      manual_snapshots: updated.public_metadata.manual_snapshots || [],
      resolved_at: resolvedAt
    });
  } catch (e) {
    console.error('update-client:', e);
    return auth.jsonResponse(500, { error: 'Update failed' });
  }
};
