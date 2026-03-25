# Paper Authoring Studio

KBF SSO-protected manuscript authoring app for turning uploaded internal research artifacts into a citation-aware draft, evidence review workspace, and export bundle.

## What is implemented

- FastAPI backend with KBF Keycloak OIDC session handling
- Project CRUD and artifact uploads
- Ingest, plan, draft, retrieve, ground, and export pipeline stages
- Redis/RQ-backed async job execution with a dedicated worker process
- React/Vite SPA for project intake, outline review, draft editing, evidence review, and export download
- Canonical export generation for JSON, Markdown, BibTeX, and DOCX

## Current v1 behavior

- Pipeline stages are enqueued by the API and executed by a separate worker.
- If `OPENAI_API_KEY` or `GEMINI_API_KEY` is missing, the app falls back to deterministic local heuristics.
- Retrieval uses PubMed and OpenAlex directly.

## Repo layout

- `backend/`: FastAPI app, ORM models, services, tests
- `frontend/`: React SPA, Vitest tests
- `docs/plans/`: design and implementation notes
- `data/`: runtime storage for uploads and export bundles

## Local development

1. Backend

```bash
cd /opt/Paper/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
export PAPER_STORAGE_ROOT=/opt/Paper/data
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Worker

```bash
cd /opt/Paper/backend
. .venv/bin/activate
export PAPER_STORAGE_ROOT=/opt/Paper/data
python -m app.jobs
```

3. Frontend

```bash
cd /opt/Paper/frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000` by default. Override with `PAPER_DEV_API_TARGET` if needed.

## Docker preview

1. Copy `.env.example` to `.env` and fill in secrets.
2. Build and run:

```bash
cd /opt/Paper
docker compose up -d --build
```

The frontend is published on `http://127.0.0.1:18092`. The backend is also exposed on `http://127.0.0.1:18093` for direct API debugging. Redis and the worker are internal services in the same stack.

## Tests

Backend:

```bash
cd /opt/Paper/backend
. .venv/bin/activate
pytest -q
```

Frontend:

```bash
cd /opt/Paper/frontend
npm test -- --run
npm run build
```

## KBF deployment notes

### Required Keycloak client

Add a new public OIDC client to `/opt/kbf-infra/keycloak/import/kbf-realm.template.json`:

- `clientId`: `paper`
- redirect URI: `https://paper.k-biofoundrycopilot.duckdns.org/*`
- web origin: `https://paper.k-biofoundrycopilot.duckdns.org`

If you want role-aware admin behavior, also add:

- `roles.client.paper.paper-admin`
- `roles.client.paper.paper-user`

The app maps `paper-admin` to an internal admin session and treats everything else as a user session.

### Required Caddy route

Add a host block to `/opt/kbf-infra/Caddyfile`:

```caddyfile
paper.k-biofoundrycopilot.duckdns.org {
    encode gzip zstd
    import security_headers
    reverse_proxy 127.0.0.1:18092
}
```

### Suggested runtime env

Use the KBF issuer pattern already used by adjacent services:

- `PAPER_OIDC_ISSUER=https://sso.k-biofoundrycopilot.duckdns.org/realms/kbf`
- `PAPER_OIDC_CLIENT_ID=paper`
- `PAPER_SESSION_COOKIE_SECURE=true`

## Primary files

- backend app entry: `backend/app/main.py`
- backend auth: `backend/app/auth.py`
- workspace API: `backend/app/api/routes/workspace.py`
- frontend app shell: `frontend/src/App.tsx`
- pipeline workspace UI: `frontend/src/components/ProjectWorkspace.tsx`
