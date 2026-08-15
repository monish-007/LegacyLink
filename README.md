# LegacyLink: Verifiable SOAP-to-REST modernization

LegacyLink turns a legacy SOAP response into a typed FastAPI service that a modern
team can inspect, test, and approve. Codex accelerates the implementation; strict
runtime validation and a human deployment gate keep it accountable.

## Why it matters

Teams integrating with undocumented SOAP systems often spend days reverse-engineering
deeply nested XML before they can make a safe API change. LegacyLink demonstrates a
repeatable path from a captured SOAP contract to an OpenAPI-backed REST endpoint,
while retaining evidence that the mapping was validated.

## What a judge can verify in two minutes

1. Start the app and open `/dashboard`.
2. Click **Execute GET /v1/customer-data** to inspect the strictly typed JSON API.
3. Click **View validation evidence** to see the source digest, validated sections,
   strict types, and explicit human-approval requirement.
4. Paste a second SOAP payload into **Try an unseen SOAP payload**. LegacyLink
   discovers candidate JSON fields and types in memory, flags sensitive fields, and
   returns no source values.
5. Configure an allowlisted source and use **Analyze a configured live source** to
   fetch it server-side, analyze only its contract metadata, and optionally write an
   audit record to Supabase.
6. Open `/docs` to inspect the generated OpenAPI contract.

The raw SOAP authentication header is never exposed by either public endpoint.
The dashboard uses no build step or external CSS dependency, so it remains readable
when a demo environment has no internet access.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Call `GET /v1/customer-data`, `GET /v1/migration-report`, inspect
`http://127.0.0.1:8000/docs`, or open `http://127.0.0.1:8000/dashboard`.

## Tests

```powershell
pip install -r requirements-dev.txt
pytest
```

## Connect real SOAP sources and Supabase

1. Copy `.env.example` to your deployment's environment-variable configuration.
2. Set `LEGACYLINK_SOURCES_JSON` with an allowlisted set of server-side source IDs
   and URLs. Browser users can call only `/v1/sources/{source_id}/analyze`; they
   cannot supply arbitrary URLs.
3. Put credentials in separate environment variables, then reference their names
   with `headers_env` and `body_env` in the source configuration.
4. In Supabase SQL Editor, run `supabase/migrations/001_migration_runs.sql`.
5. Add `SUPABASE_URL` and `SUPABASE_SECRET_KEY` only to the API's server
   environment. This records contract metadata, never raw XML or credentials. A
   legacy `SUPABASE_SERVICE_ROLE_KEY` also works, but a new secret key is preferred.

For a local demo, set `LEGACYLINK_ALLOW_HTTP=true` and point a source at the mock
server. Do not enable HTTP in a public deployment.

## Publish a public demo

The repository includes a `Dockerfile` and `render.yaml` for a container host such
as Render. Connect the repository, create a web service from `rest-wrapper`, and
set the environment variables from `.env.example` in the host dashboard (never in
Git). Use the public service URL for `/dashboard` and `/docs`.

Supabase provides the audit database, not the FastAPI web host. Keep the Supabase
secret key server-only; do not place it in browser code or a repository.

### Vercel (free Hobby demo)

For a personal hackathon demo, import the `main` branch into Vercel. The
`api/index.py` file is the Vercel FastAPI entrypoint and `vercel.json` sets a
60-second function limit. Add `SUPABASE_URL` and `SUPABASE_SECRET_KEY` in Vercel's
Environment Variables before deploying. After deployment, open `/dashboard` on the
Vercel URL.

## Metering

All requests except `/health` pass through `dodo_usage_metering`. It captures the
path, status, duration, and optional `X-Customer-Id` and calls a **demonstration
placeholder** `report_usage` hook. It fails open by design. Replace that hook with
the approved Dodo Payments usage-event API/SDK call, with credentials configured
through the deployment environment rather than source control.

## Deliberate demo boundaries

- This repository uses a recorded SOAP fixture so the demo is deterministic.
- It is not a production deployment: production use needs source authentication,
  authorization, encrypted secret storage, SOAP fault handling, and a real billing
  provider integration.
- Generated changes should be reviewed and tested before deployment; LegacyLink
  makes that review checkpoint explicit rather than claiming autonomous production
  release.
