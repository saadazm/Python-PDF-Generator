# Listing this API on RapidAPI

This is a checklist for listing the deployed API on a marketplace like
RapidAPI. Creating the account, connecting payout details, and picking
final prices are all things only you can do — this just gets you to the
point of having something ready to submit.

## Prerequisite

The API must already be deployed and reachable over HTTPS (see
`DEPLOY.md`) with real API keys in place — RapidAPI calls your live server,
it doesn't host your code.

## 1. Get your machine-readable API spec

FastAPI generates this for you automatically, no extra work needed:

- OpenAPI spec: `https://your-domain.com/openapi.json`
- Interactive docs (for your own reference while filling out the listing):
  `https://your-domain.com/docs`

## 2. Create the listing

1. Sign up / log in at RapidAPI and go to **My APIs → Add New API**.
2. Choose **Import from OpenAPI/Swagger** and point it at your
   `/openapi.json` URL — this pre-fills the endpoints
   (`/v1/generate`, `/v1/generate/batch`, `/v1/templates`) from what's
   already in `api/main.py`.
3. Set the **Base URL** to `https://your-domain.com`.

## 3. Decide how auth works through RapidAPI

RapidAPI sits between the caller and your server, and it has its own
subscriber-key system. You have two options; pick one so you don't run two
uncoordinated quota systems by accident:

- **Simplest**: declare `X-API-Key` as a required header parameter on each
  endpoint in the listing, and manually hand out a real key (from
  `api/api_keys.json`) per paying customer. RapidAPI just proxies it
  through. Your own quota enforcement in `api/auth.py` keeps working
  exactly as it does today.
- **RapidAPI-native**: let RapidAPI's own plan/quota system be the source
  of truth (it meters calls per subscriber automatically) and configure
  your backend to trust anything RapidAPI forwards — e.g. check the
  `X-RapidAPI-Proxy-Secret` header RapidAPI adds instead of your own key
  header. This means adding a second auth path to `api/auth.py`; not done
  here since it depends on which of these two you pick.

## 4. Fill out the listing itself

RapidAPI requires, and only you can decide:

- Category (Business / Documents & Productivity fits).
- Title and description — plain language, not the OpenAPI description.
- Example request/response for each endpoint (use the `/docs` UI to
  generate real ones).
- Pricing plans (see suggestion below).

## 5. Suggested pricing tiers

A starting point, not a recommendation to copy exactly — check what
comparable PDF-generation APIs charge before finalizing:

| Plan  | Price   | Quota        | Notes                              |
|-------|---------|--------------|-------------------------------------|
| Free  | $0      | 20 PDFs/mo   | Matches `demo-free-key`'s default.  |
| Basic | $9/mo   | 1,000 PDFs/mo| Single-document endpoint only.      |
| Pro   | $29/mo  | 10,000 PDFs/mo | Unlocks `/v1/generate/batch`.     |

Whatever you pick, set matching `quota_limit` values in
`api/api_keys.json` (or your DB, once you've migrated off the JSON file)
so your own enforcement matches what customers were sold.

## 6. Before submitting

- Test every endpoint through RapidAPI's built-in test console — it calls
  your live server, so this also doubles as a final deploy smoke test.
- Confirm error responses (401 missing/invalid key, 402 quota exceeded,
  400 bad template/CSV) look sensible surfaced through RapidAPI's UI, not
  just via raw curl.
