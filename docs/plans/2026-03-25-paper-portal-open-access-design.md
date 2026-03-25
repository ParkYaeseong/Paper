# Paper Portal Open Access Design

**Date:** 2026-03-25

## Goal

Show `Paper Authoring Studio` in the KBF portal `Support` section for any logged-in portal user, matching the discoverability pattern users already see for `PaperBanana` and `Paper2Slides`.

## Problem

The current portal manifest only includes `paper` when the authenticated OIDC claims include `paper-user` or `paper-admin`. That makes the service invisible to many valid portal users even though the app itself already relies on its own OIDC login flow.

## Recommended Approach

Change only `/opt/open-notebook` portal manifest rules.

- In `password` mode, include `_paper_service()` alongside the other support tools.
- In `oidc` mode, include `_paper_service()` for every authenticated user instead of gating it on `paper` client roles.
- Keep the Paper app itself unchanged.

### Why this approach

- It makes the portal card visible in the exact place users expect: `Support`.
- It keeps the Paper app’s authentication boundary intact.
- It avoids new gateway or SSO changes for a simple visibility rule.

## Behavior

### Portal card visibility

- `password` session:
  - show `paper`
- `oidc` session:
  - show `paper` for any authenticated user
- `none` session:
  - keep returning no services

### App access

- The Paper app still uses its own OIDC login flow.
- Clicking the portal card may still trigger a Paper-specific SSO login if the user does not already have a valid Paper session.
- `paper-admin` remains useful only for admin/session role mapping inside Paper.

## Components

### `/opt/open-notebook`

- `api/routers/portal.py`
  - add `_paper_service()` to the password-mode service list
  - remove the `paper` client-role gate from the OIDC branch
- `tests/test_portal_api.py`
  - assert `paper` is visible for generic OIDC sessions
  - assert `paper` is visible for password-mode sessions

## Testing Strategy

- Run `pytest tests/test_portal_api.py -q` in `/opt/open-notebook`.
- Re-run the existing portal grouping frontend test to ensure `Support` rendering still passes.

## Out Of Scope

- changing Paper backend auth requirements
- changing Keycloak roles
- changing Caddy or deployment topology
