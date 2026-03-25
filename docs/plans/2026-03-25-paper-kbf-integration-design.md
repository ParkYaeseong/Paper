# Paper KBF SSO And Portal Integration Design

**Date:** 2026-03-25

## Goal

Expose `Paper Authoring Studio` at `https://paper.k-biofoundrycopilot.duckdns.org`, register it as a first-class KBF SSO application, show it in the shared portal for authorized users, and include it in cross-app logout without adding a redundant auth gateway.

## Recommended Approach

Reuse the existing OIDC session flow already implemented inside `/opt/Paper`, and limit KBF integration work to:

- a new public Caddy host in `/opt/kbf-infra`
- a new `paper` Keycloak OIDC client plus client roles
- portal catalog and logout updates in `/opt/open-notebook`
- a static logout bridge asset in `/opt/Paper/frontend/public`

### Why this approach

- `Paper` already performs authorization-code exchange and session-cookie issuance internally, so a second gateway would duplicate login logic.
- KBF already manages public app exposure through `Caddyfile` and realm import templates.
- The portal already owns service discoverability and logout fanout, so adding `paper` there keeps user behavior consistent with adjacent apps.

## Architecture

### Public entrypoint

- Add a new Caddy virtual host:
  - `paper.k-biofoundrycopilot.duckdns.org`
- Route the public host directly to the internal Paper frontend port:
  - `127.0.0.1:18092`
- Keep the backend API on:
  - `127.0.0.1:18093`
- Do not expose the backend directly through Caddy.

### Identity and authorization

- Reuse the shared `kbf` Keycloak realm.
- Add a new public OIDC client:
  - `paper`
- Register redirect and origin values:
  - `https://paper.k-biofoundrycopilot.duckdns.org/*`
  - `https://paper.k-biofoundrycopilot.duckdns.org`
- Add client roles:
  - `paper-admin`
  - `paper-user`
- Extend the `kbf-admin` composite realm role so KBF admins inherit:
  - `paper-admin`
- Keep the current Paper app authorization model:
  - `paper-admin` maps to internal admin session
  - every other authenticated `paper` user maps to internal user session

### Portal catalog integration

- Add `Paper Authoring Studio` to the portal service manifest in `/opt/open-notebook`.
- Show the card only when the authenticated user has:
  - `paper-user`
  - or `paper-admin`
- Categorize the service as:
  - `Support`
- Use the service metadata:
  - `id = paper`
  - `title = Paper Authoring Studio`
  - `url = https://paper.k-biofoundrycopilot.duckdns.org`
  - `theme = coral`

### Cross-app logout

- Add `https://paper.k-biofoundrycopilot.duckdns.org` to the portal’s cross-app logout fanout list.
- Serve `logout-bridge.html` from the Paper frontend static assets.
- The logout bridge will:
  - call `/api/auth/logout`
  - clear app-local session state
  - post `kbf:logout-bridge:complete` back to the parent portal origin
- Do not add a portal-driven Keycloak end-session hop for Paper. The app bridge only needs to clear the Paper session, matching the current KBF portal pattern.

## Components

### `/opt/kbf-infra`

- `Caddyfile`
  - add the `paper.k-biofoundrycopilot.duckdns.org` host
  - proxy to `127.0.0.1:18092`
- `keycloak/import/kbf-realm.template.json`
  - add the `paper` OIDC client
  - add `paper-admin` and `paper-user` client roles
  - add `paper-admin` to the `kbf-admin` realm composite
- `tests/`
  - add a dedicated route/config test for `paper`

### `/opt/open-notebook`

- `api/routers/portal.py`
  - add `_paper_service()`
  - include `paper` in the role-gated portal manifest
- `frontend/src/components/portal/ServiceCard.tsx`
  - add a dedicated icon mapping for `paper`
- `frontend/src/lib/auth/cross-app-logout.js`
  - add the `paper` origin
- tests
  - extend portal manifest tests
  - extend service grouping tests if ordering expectations change
  - extend logout fanout tests

### `/opt/Paper`

- `frontend/public/logout-bridge.html`
  - add a static logout bridge for portal fanout
- `frontend`
  - add a small test that asserts the bridge exists and calls `/api/auth/logout`
- docs
  - update deployment notes if the public integration details change

## Request And Auth Flow

1. User signs in through the KBF portal.
2. The portal loads `/api/portal/services`.
3. `open-notebook` includes `paper` only when `paper-user` or `paper-admin` is present in `resource_access.paper.roles`.
4. User opens `https://paper.k-biofoundrycopilot.duckdns.org`.
5. Caddy proxies the request to `127.0.0.1:18092`.
6. The Paper frontend loads and requests OIDC config from its backend via `/api/auth/oidc/config`.
7. If no valid Paper session exists, the app redirects to Keycloak, completes the code exchange through `/api/auth/oidc/exchange`, and sets the Paper session cookie.
8. The SPA continues using the Paper backend under `/api`.

## Error Handling

- Missing Paper client role:
  - portal card stays hidden
  - direct app access still depends on Paper’s own session behavior and Keycloak-issued token audience
- Caddy route missing:
  - public host fails fast with infra-level error
- Invalid or missing OIDC client config:
  - Paper login flow fails during OIDC config or token exchange
- Logout bridge failure:
  - portal fanout records a failed origin but still completes logout for other apps

## Testing Strategy

### `/opt/kbf-infra`

- Assert the `paper` Caddy host proxies to `127.0.0.1:18092`.
- Assert the realm template contains:
  - the `paper` client
  - the correct redirect URI
  - the correct web origin
  - `paper-admin`
  - `paper-user`
  - `kbf-admin -> paper-admin`

### `/opt/open-notebook`

- Assert `/api/portal/services` includes `paper` when `paper-user` is present.
- Assert `/api/portal/services` hides `paper` when the role is absent.
- Assert cross-app logout includes the `paper` origin.
- Assert portal grouping still produces the expected `Support` section contents.

### `/opt/Paper`

- Assert `frontend/public/logout-bridge.html` exists.
- Assert it calls `/api/auth/logout`.
- Assert it posts the completion message back to the parent window.
- Re-run the current frontend build so the asset lands in the production bundle.

## Rollout Verification

- Validate the updated Caddy config:
  - `caddy validate --config /opt/kbf-infra/Caddyfile`
- Run the relevant infra tests in `/opt/kbf-infra`.
- Run portal API and frontend logout tests in `/opt/open-notebook`.
- Run Paper frontend tests and build in `/opt/Paper`.
- Manually verify:
  - the portal shows `Paper Authoring Studio`
  - the Paper app signs in through KBF SSO
  - portal logout clears the Paper session through `logout-bridge.html`

## Out Of Scope

- adding a separate Paper auth gateway
- changing Paper’s internal OIDC flow to forward-auth
- journal-specific provisioning or per-user authorization beyond current client roles
