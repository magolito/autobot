exports.handler = async function(event) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method not allowed' };
  }

  try {
    var body = JSON.parse(event.body);
    var address = body.address;
    if (!address) return { statusCode: 400, body: JSON.stringify({ error: 'Missing address' }) };

    var base = 'https://api.hyperliquid.xyz/info';
    var headers = { 'Content-Type': 'application/json' };

    var [stateRes, fillsRes] = await Promise.all([
      fetch(base, { method: 'POST', headers, body: JSON.stringify({ type: 'clearinghouseState', user: address }) }),
      fetch(base, { method: 'POST', headers, body: JSON.stringify({ type: 'userFills', user: address }) })
    ]);

    var state = await stateRes.json();
    var fills = await fillsRes.json();

    return {
      statusCode: 200,
      headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' },
      body: JSON.stringify({ state, fills })
    };
  } catch(e) {
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: e.message })
    };
  }
};
