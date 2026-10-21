// Notifies the AutoBot team by email when a signed-in client submits a request.
//
// Security rules:
//  - Caller must be signed in; the client's name/email come from their verified
//    Clerk account, not from the request body.
//  - API secrets are NEVER put in an email. A submitted key + secret is stored
//    in the client's Clerk privateMetadata (server-only), and the email just
//    says a new key is waiting there.
//  - Everything placed in the email HTML is escaped.

var auth = require('../lib/auth');

var NOTIFY_TO = process.env.NOTIFY_EMAIL || 'autobottradingai@gmail.com';

function row(label, value) {
  return '<tr><td style="padding:10px 0;border-bottom:1px solid #eee;color:#888;width:140px">' + auth.escapeHtml(label) +
    '</td><td style="padding:10px 0;border-bottom:1px solid #eee;font-weight:600">' + auth.escapeHtml(value) + '</td></tr>';
}

function shell(title, sub, rows, footer) {
  return '<div style="font-family:sans-serif;max-width:540px;margin:0 auto;padding:32px">' +
    '<h2 style="margin:0 0 4px">' + auth.escapeHtml(title) + '</h2>' +
    '<p style="color:#666;margin:0 0 24px">' + auth.escapeHtml(sub) + '</p>' +
    '<table style="width:100%;border-collapse:collapse">' + rows + '</table>' +
    '<div style="margin-top:28px;padding:16px;background:#f9fafb;border-radius:8px;font-size:13px;color:#666">' + auth.escapeHtml(footer) + '</div></div>';
}

exports.handler = async function(event) {
  if (event.httpMethod === 'OPTIONS') return auth.corsPreflight('POST');
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'Method not allowed' };

  var gate = await auth.requireUser(event);
  if (gate.response) return gate.response;
  var user = gate.user;

  try {
    var body;
    try { body = JSON.parse(event.body || '{}'); }
    catch (e) { return auth.jsonResponse(400, { error: 'Bad request body' }); }

    var type        = body.type === 'api_key_renewal' ? 'api_key_renewal' : 'risk_request';
    var clientName  = ((user.first_name || '') + ' ' + (user.last_name || '')).trim() || auth.primaryEmail(user);
    var clientEmail = auth.primaryEmail(user) || '—';
    var submittedAt = new Date().toLocaleString('en-US', { timeZone: 'America/New_York', dateStyle: 'medium', timeStyle: 'short' }) + ' ET';
    var subject, html;

    if (type === 'api_key_renewal') {
      var apiKey = String(body.api_key || '').trim();
      var apiSecret = String(body.api_secret || '').trim();
      if (!apiKey || apiKey.length > 200 || apiSecret.length > 200) return auth.jsonResponse(400, { error: 'Invalid API key' });

      // Store the new credentials server-side on the client's own Clerk record.
      var priv = Object.assign({}, user.private_metadata || {}, {
        pending_api_key: apiKey,
        pending_api_secret: apiSecret || null,
        pending_api_key_submitted_at: new Date().toISOString()
      });
      var r = await fetch('https://api.clerk.com/v1/users/' + encodeURIComponent(user.id) + '/metadata', {
        method: 'PATCH',
        headers: { 'Authorization': 'Bearer ' + gate.secretKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({ private_metadata: priv })
      });
      if (!r.ok) throw new Error('Could not store key in Clerk (' + r.status + ')');

      subject = 'API Key Renewal — ' + clientName;
      html = shell('API Key Renewal Request', 'A client submitted a new API key.',
        row('Client', clientName) + row('Email', clientEmail) + row('Submitted', submittedAt) +
        row('Key (last 4)', '…' + apiKey.slice(-4)),
        'The full key and secret are stored on this client in Clerk → Users → ' + clientEmail +
        ' → Metadata → Private (pending_api_key / pending_api_secret). Update the bot, then update hl_api_key_expiry.');
    } else {
      var reqLevel = Number(body.requested_level);
      if (!isFinite(reqLevel) || reqLevel < 0 || reqLevel > 100) return auth.jsonResponse(400, { error: 'Invalid risk level' });
      subject = 'Risk Change Request — ' + clientName + ' → ' + reqLevel + '%';
      html = shell('Risk Change Request', 'A client submitted a new risk level request.',
        row('Client', clientName) + row('Email', clientEmail) + row('Requested level', reqLevel + '%') + row('Submitted', submittedAt),
        'Log in to the AutoBot Admin Panel to approve or reject this request.');
    }

    var resendKey = process.env.RESEND_API_KEY;
    if (!resendKey) return auth.jsonResponse(200, { success: false, message: 'Email provider not configured' });

    var res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + resendKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: 'AutoBot <onboarding@resend.dev>', to: [NOTIFY_TO], subject: subject, html: html })
    });
    if (!res.ok) throw new Error('Resend error ' + res.status + ': ' + (await res.text()));

    return auth.jsonResponse(200, { success: true });
  } catch (e) {
    console.error('send-notification:', e);
    return auth.jsonResponse(500, { error: 'Could not send notification' });
  }
};
