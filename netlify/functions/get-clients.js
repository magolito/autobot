var auth = require('../lib/auth');

exports.handler = async function(event) {
  // Allow OPTIONS for CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, OPTIONS'
      },
      body: ''
    };
  }

  if (event.httpMethod !== 'GET') {
    return { statusCode: 405, body: 'Method not allowed' };
  }

  // Admins only — verified on the server from the caller's Clerk session.
  var gate = await auth.requireAdmin(event);
  if (gate.response) return gate.response;

  try {
    var secretKey = process.env.CLERK_SECRET_KEY;

    if (!secretKey) {
      return {
        statusCode: 500,
        headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'CLERK_SECRET_KEY is not set in Netlify environment variables.' })
      };
    }

    // Fetch up to 500 users from Clerk (paginate if needed)
    var allUsers = [];
    var offset = 0;
    var limit = 100;
    var hasMore = true;

    while (hasMore) {
      var res = await fetch(
        'https://api.clerk.com/v1/users?limit=' + limit + '&offset=' + offset + '&order_by=-created_at',
        {
          headers: {
            'Authorization': 'Bearer ' + secretKey,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!res.ok) {
        var errBody = await res.text();
        throw new Error('Clerk API error ' + res.status + ': ' + errBody);
      }

      var users = await res.json();

      if (!Array.isArray(users) || users.length === 0) {
        hasMore = false;
      } else {
        allUsers = allUsers.concat(users);
        offset += limit;
        if (users.length < limit) hasMore = false;
      }
    }

    // Map Clerk users to client format
    var clients = allUsers.map(function(user) {
      var primaryEmail = '';
      if (user.email_addresses && user.email_addresses.length > 0) {
        var primary = user.email_addresses.find(function(e) {
          return e.id === user.primary_email_address_id;
        }) || user.email_addresses[0];
        primaryEmail = primary.email_address || '';
      }

      var firstName = user.first_name || '';
      var lastName  = user.last_name  || '';
      var name = (firstName + ' ' + lastName).trim() || primaryEmail.split('@')[0];
      var meta       = user.public_metadata  || {};
      var unsafeMeta = user.unsafe_metadata  || {};
      var pending    = unsafeMeta.pending_risk_request || null;

      var lastSignIn = user.last_sign_in_at
        ? new Date(user.last_sign_in_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
        : 'Never';

      var exchange = (meta.exchange || 'hyperliquid').toLowerCase();
      // Bybit clients are configured when they've been tagged with exchange=bybit
      // (their keys live in privateMetadata, which this endpoint can't see, but
      // we trust the flag — admin.html will hit bybit-proxy which validates them).
      // Hyperliquid clients are configured when an hl_address is set.
      var configured = exchange === 'bybit' ? true : !!meta.hl_address;

      return {
        id:                     user.id,
        name:                   name,
        email:                  primaryEmail,
        exchange:               exchange,
        hl_address:             meta.hl_address      || null,
        initial_capital:        meta.initial_capital || null,
        risk_level:             meta.risk_level      || 50,
        data_mode:              meta.data_mode       || (exchange === 'bybit' ? 'manual' : 'live'),
        start_date:             meta.start_date      || null,
        manual_snapshots:       Array.isArray(meta.manual_snapshots) ? meta.manual_snapshots : [],
        created_at:             user.created_at,
        last_sign_in_at:        user.last_sign_in_at,
        last_sign_in:           lastSignIn,
        banned:                 user.banned || false,
        configured:             configured,
        pending_risk_request:   pending
      };
    });

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        clients:  clients,
        total:    allUsers.length,
        configured: clients.filter(function(c){ return c.configured; }).length
      })
    };

  } catch (e) {
    console.error('get-clients:', e);
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Could not load clients' })
    };
  }
};
