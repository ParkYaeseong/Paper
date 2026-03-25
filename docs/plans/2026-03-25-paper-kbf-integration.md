# Paper KBF SSO And Portal Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate Paper Authoring Studio into the KBF public app surface with a new subdomain, Keycloak client, portal card, and cross-app logout support.

**Architecture:** `/opt/kbf-infra` will expose the public host and register the `paper` OIDC client. `/opt/open-notebook` will show the Paper app in the portal and add it to logout fanout. `/opt/Paper` will add a static logout bridge asset so portal logout can clear the Paper session without introducing a new auth gateway.

**Tech Stack:** Caddy, Keycloak realm import JSON, FastAPI, React, Next.js, Vite, Vitest, Pytest

---

### Task 1: Add failing infra tests for the new Paper app registration

**Files:**
- Create: `/opt/kbf-infra/tests/test_paper_routes.py`

**Step 1: Write the failing test**

Add tests that assert:
- `/opt/kbf-infra/Caddyfile` contains `paper.k-biofoundrycopilot.duckdns.org`
- the host proxies to `127.0.0.1:18092`
- `/opt/kbf-infra/keycloak/import/kbf-realm.template.json` contains the `paper` client
- the realm template contains `paper-admin` and `paper-user`
- `kbf-admin` includes `paper-admin` in its composites

**Step 2: Run test to verify it fails**

Run: `cd /opt/kbf-infra && pytest tests/test_paper_routes.py -q`
Expected: FAIL because the `paper` route and client do not exist yet.

**Step 3: Write minimal implementation**

Only add the test file and assertions necessary to drive the infra changes.

**Step 4: Run test to verify it passes**

Run: `cd /opt/kbf-infra && pytest tests/test_paper_routes.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/kbf-infra
git add tests/test_paper_routes.py
git commit -m "test: add paper infra route coverage"
```

### Task 2: Register the Paper host and Keycloak client in kbf-infra

**Files:**
- Modify: `/opt/kbf-infra/Caddyfile`
- Modify: `/opt/kbf-infra/keycloak/import/kbf-realm.template.json`
- Test: `/opt/kbf-infra/tests/test_paper_routes.py`

**Step 1: Write the failing test**

Use the tests from Task 1 as the red state.

**Step 2: Run test to verify it fails**

Run: `cd /opt/kbf-infra && pytest tests/test_paper_routes.py -q`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- a `paper.k-biofoundrycopilot.duckdns.org` Caddy host
- `reverse_proxy 127.0.0.1:18092`
- a `paper` public OIDC client
- `paper-admin` and `paper-user` client roles
- `kbf-admin -> paper-admin` composite

**Step 4: Run verification**

Run: `cd /opt/kbf-infra && pytest tests/test_paper_routes.py -q`
Expected: PASS

Run: `caddy validate --config /opt/kbf-infra/Caddyfile`
Expected: Valid Caddy configuration

**Step 5: Commit**

```bash
cd /opt/kbf-infra
git add Caddyfile keycloak/import/kbf-realm.template.json tests/test_paper_routes.py
git commit -m "feat: add paper app infra registration"
```

### Task 3: Add failing portal and logout tests in open-notebook

**Files:**
- Modify: `/opt/open-notebook/tests/test_portal_api.py`
- Modify: `/opt/open-notebook/frontend/src/lib/auth/cross-app-logout.test.js`
- Modify: `/opt/open-notebook/frontend/src/lib/portal/service-groups.test.ts`

**Step 1: Write the failing test**

Add tests that assert:
- `/api/portal/services` includes `paper` when `paper-user` is present
- `/api/portal/services` hides `paper` when the `paper` client role is absent
- cross-app logout targets include `https://paper.k-biofoundrycopilot.duckdns.org`
- the `Support` group contains `paper` alongside the other support tools

**Step 2: Run test to verify it fails**

Run: `cd /opt/open-notebook && pytest tests/test_portal_api.py -q`
Expected: FAIL because the portal manifest does not know about `paper`.

Run: `cd /opt/open-notebook/frontend && npm test -- --run src/lib/auth/cross-app-logout.test.js src/lib/portal/service-groups.test.ts`
Expected: FAIL because logout targets and service grouping do not include `paper`.

**Step 3: Write minimal implementation**

Only add the assertions needed to define the target portal behavior and logout fanout.

**Step 4: Run test to verify it passes**

Run the same pytest and Vitest commands.
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/open-notebook
git add tests/test_portal_api.py frontend/src/lib/auth/cross-app-logout.test.js frontend/src/lib/portal/service-groups.test.ts
git commit -m "test: add paper portal integration coverage"
```

### Task 4: Add Paper to the portal catalog and cross-app logout fanout

**Files:**
- Modify: `/opt/open-notebook/api/routers/portal.py`
- Modify: `/opt/open-notebook/frontend/src/components/portal/ServiceCard.tsx`
- Modify: `/opt/open-notebook/frontend/src/lib/auth/cross-app-logout.js`
- Modify: `/opt/open-notebook/tests/test_portal_api.py`
- Modify: `/opt/open-notebook/frontend/src/lib/auth/cross-app-logout.test.js`
- Modify: `/opt/open-notebook/frontend/src/lib/portal/service-groups.test.ts`

**Step 1: Write the failing test**

Use the tests from Task 3 as the red state.

**Step 2: Run test to verify it fails**

Run:
- `cd /opt/open-notebook && pytest tests/test_portal_api.py -q`
- `cd /opt/open-notebook/frontend && npm test -- --run src/lib/auth/cross-app-logout.test.js src/lib/portal/service-groups.test.ts`

Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- `_paper_service()` with `Support` category metadata
- role-gated portal inclusion based on `paper-user` or `paper-admin`
- a Paper icon mapping in `ServiceCard.tsx`
- the Paper origin in cross-app logout fanout

**Step 4: Run test to verify it passes**

Run the same pytest and Vitest commands.
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/open-notebook
git add api/routers/portal.py frontend/src/components/portal/ServiceCard.tsx frontend/src/lib/auth/cross-app-logout.js tests/test_portal_api.py frontend/src/lib/auth/cross-app-logout.test.js frontend/src/lib/portal/service-groups.test.ts
git commit -m "feat: add paper to portal catalog"
```

### Task 5: Add a failing Paper logout bridge test

**Files:**
- Create: `/opt/Paper/frontend/src/logout-bridge.test.ts`

**Step 1: Write the failing test**

Add a test that asserts:
- `/opt/Paper/frontend/public/logout-bridge.html` exists
- it calls `/api/auth/logout`
- it posts `kbf:logout-bridge:complete`

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run src/logout-bridge.test.ts`
Expected: FAIL because the asset does not exist yet.

**Step 3: Write minimal implementation**

Only add the test file and file-content assertions needed to drive the asset creation.

**Step 4: Run test to verify it passes**

Run: `cd /opt/Paper/frontend && npm test -- --run src/logout-bridge.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add frontend/src/logout-bridge.test.ts
git commit -m "test: add paper logout bridge coverage"
```

### Task 6: Add the Paper logout bridge asset and docs note

**Files:**
- Create: `/opt/Paper/frontend/public/logout-bridge.html`
- Create: `/opt/Paper/frontend/src/logout-bridge.test.ts`
- Modify: `/opt/Paper/README.md`

**Step 1: Write the failing test**

Use the test from Task 5 as the red state.

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run src/logout-bridge.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- a static logout bridge that calls `/api/auth/logout`
- browser storage cleanup for the Paper auth flow
- `postMessage` completion back to the parent origin
- a short README note that the app now participates in portal logout fanout

**Step 4: Run full Paper verification**

Run: `cd /opt/Paper/frontend && npm test -- --run src/logout-bridge.test.ts src/App.test.tsx src/components/ExportPanel.test.tsx`
Expected: PASS

Run: `cd /opt/Paper/frontend && npm run build`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/Paper
git add frontend/public/logout-bridge.html frontend/src/logout-bridge.test.ts README.md
git commit -m "feat: add paper logout bridge"
```

### Task 7: Run cross-repo verification and record rollout checks

**Files:**
- Modify: `/opt/Paper/docs/plans/2026-03-25-paper-kbf-integration.md`

**Step 1: Re-run the required verification commands**

Run:
- `cd /opt/kbf-infra && pytest tests/test_paper_routes.py -q`
- `caddy validate --config /opt/kbf-infra/Caddyfile`
- `cd /opt/open-notebook && pytest tests/test_portal_api.py -q`
- `cd /opt/open-notebook/frontend && npm test -- --run src/lib/auth/cross-app-logout.test.js src/lib/portal/service-groups.test.ts`
- `cd /opt/Paper/frontend && npm test -- --run`
- `cd /opt/Paper/frontend && npm run build`

Expected: PASS for every command.

**Step 2: Update the plan notes if any command differs**

Record any changed command, missing prerequisite, or repo-specific caveat directly in this plan file before closing the work.

**Step 3: Commit**

```bash
cd /opt/Paper
git add docs/plans/2026-03-25-paper-kbf-integration.md
git commit -m "docs: finalize paper integration rollout checklist"
```
