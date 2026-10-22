# AutoBot — autobot.trading

Static site on Netlify, deployed automatically from `main`. No build step on Netlify; generated pages are committed.

## Pages

| File | What it is | Edit how |
|---|---|---|
| `index.html` | Homepage + lead form (Netlify Forms) | By hand |
| `results.html` | Client Results | **Generated** — edit `data/clients.json`, then rebuild |
| `plans.html` | Plans and prices | **Generated** — edit `tools/build_plans.py`, then rebuild |
| `login.html`, `dashboard.html` | Client portal (Clerk sign-in) | By hand |
| `admin.html` | Admin panel: clients, risk requests, monthly figures | By hand |

`/compare` redirects to `/plans` (see `netlify.toml`).

## Updating client results

1. Edit `data/clients.json` — `start` (invested), `end` (current value), `months`, and the `as_of_label` / `as_of_long` dates at the top (they fill every date on the page).
2. Run `python3 tools/build_pages.py` (Python 3, standard library only).
3. Commit `data/clients.json` and `results.html` together.

Never hand-edit `results.html` or `plans.html`; the next rebuild overwrites them. Shared nav, CTA band and footer for both live in `tools/templates/base.html`.

## Client dashboard data

- **Hyperliquid clients**: live, read from the wallet in `publicMetadata.hl_address`.
- **Monthly clients (e.g. Bybit)**: `publicMetadata.data_mode = "manual"`, entered in the admin panel:
  - `initial_capital`, `start_date` — set once.
  - `manual_snapshots: [{date, balance, deposit}]` — one per month; `deposit` is money added (negative = withdrawn).
  - Invested = `initial_capital` + all deposits. Gain is measured against invested, so deposits never count as profit.

## Adding a client

1. Clerk dashboard → Users → Create user (name, email, password).
2. Edit the user's **public metadata**:
   - Hyperliquid: `hl_address`, `initial_capital`, `risk_level`.
   - Monthly (e.g. Bybit): `exchange: "bybit"`, `risk_level`; then set the start amount, start date and monthly updates from the admin panel.
3. Admin panel → Refresh.

## Pinned versions

- Clerk script: `6.40.0` on login/admin, `4.73.14` on the dashboard. Change only on purpose, then test sign-in.
- Node `22` for functions (`netlify.toml`, `.nvmrc`).

## Server functions (`netlify/functions`)

All verify the caller's Clerk session on the server (`netlify/lib/auth.js`). Admin-only: `get-clients`, `update-client`.
Required Netlify env var: `CLERK_SECRET_KEY`. Secrets are never committed.

## Design rules

- Fonts: Playfair Display (headings), DM Sans (text), DM Mono (numbers, labels).
- Colors: cream `#f2f1ed`, ink `#0e0e0c`, grays `#8c8c89` / `#4e4e4b`; up `#1f6f4a`, down `#b4442f`.
- No taglines, eyebrows or helper captions. If a screen needs one to make sense, fix the layout instead.
- Legal and risk wording (footer disclosure, results notes, plan footnotes) stays.
