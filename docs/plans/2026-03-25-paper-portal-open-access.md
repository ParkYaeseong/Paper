# Paper Portal Open Access Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `Paper Authoring Studio` visible in the portal `Support` section for any logged-in user.

**Architecture:** Only the open-notebook portal manifest rules change. The portal will include `paper` for password-mode sessions and all authenticated OIDC sessions, while the Paper app keeps its existing OIDC login flow and role handling.

**Tech Stack:** FastAPI, Pytest, Next.js portal frontend tests

---

### Task 1: Add failing portal API tests for generic visibility

**Files:**
- Modify: `/opt/open-notebook/tests/test_portal_api.py`

**Step 1: Write the failing test**

Add tests asserting:
- `paper` is included for an OIDC session that has `kbf-portal` but no `paper` role
- `paper` is included for a `password` mode portal session

**Step 2: Run test to verify it fails**

Run: `cd /opt/open-notebook && . .venv/bin/activate && pytest tests/test_portal_api.py -q`
Expected: FAIL because the portal still gates `paper` on explicit client roles and omits it in password mode.

**Step 3: Write minimal implementation**

Only adjust the tests needed to define the new visibility rule.

**Step 4: Run test to verify it passes**

Run: `cd /opt/open-notebook && . .venv/bin/activate && pytest tests/test_portal_api.py -q`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/open-notebook
git add tests/test_portal_api.py
git commit -m "test: cover open paper portal visibility"
```

### Task 2: Remove portal-only gating for Paper

**Files:**
- Modify: `/opt/open-notebook/api/routers/portal.py`
- Modify: `/opt/open-notebook/tests/test_portal_api.py`

**Step 1: Write the failing test**

Use the tests from Task 1 as the red state.

**Step 2: Run test to verify it fails**

Run: `cd /opt/open-notebook && . .venv/bin/activate && pytest tests/test_portal_api.py -q`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- add `_paper_service()` to the `password` mode service list
- always append `_paper_service()` for authenticated OIDC users
- keep all other service gates unchanged

**Step 4: Run verification**

Run: `cd /opt/open-notebook && . .venv/bin/activate && pytest tests/test_portal_api.py -q`
Expected: PASS

Run: `cd /opt/open-notebook/frontend && npm test -- --run src/lib/portal/service-groups.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
cd /opt/open-notebook
git add api/routers/portal.py tests/test_portal_api.py
git commit -m "feat: show paper for logged-in portal users"
```
