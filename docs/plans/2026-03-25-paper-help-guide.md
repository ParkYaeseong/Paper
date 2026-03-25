# Paper Help Guide Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a bilingual in-app help guide that explains the Paper workflow, upload expectations, and stage order from a global header entry point.

**Architecture:** Keep the feature frontend-only. Add a header trigger that opens a modal with local static content and English/Korean tabs. Manage modal open state at the `App` level so it is available for every authenticated screen without touching backend APIs.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, existing Paper CSS

---

### Task 1: Save Help Guide Content And Add Modal Tests

**Files:**
- Create: `frontend/src/components/GuideModal.tsx`
- Create: `frontend/src/lib/guide-content.ts`
- Modify: `frontend/src/App.test.tsx`

**Step 1: Write the failing tests**

Add one test that:

- renders the authenticated shell
- clicks `Help / 사용법`
- expects `Quick Start` content in English
- switches to `한국어`
- expects Korean usage text
- closes the modal and confirms it disappears

**Step 2: Run test to verify it fails**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx`

Expected: FAIL because the help button and modal do not exist yet.

**Step 3: Add minimal modal content module**

Create a small structured object with:

- `en`
- `ko`

Each should contain:

- title
- section headings
- bullet items

**Step 4: Add minimal modal component**

Create a dialog component that accepts:

- `open`
- `language`
- `onLanguageChange`
- `onClose`

**Step 5: Run test to verify it still fails for integration gaps**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx`

Expected: FAIL because the modal is not connected to the app shell yet.

**Step 6: Commit**

```bash
git add frontend/src/components/GuideModal.tsx frontend/src/lib/guide-content.ts frontend/src/App.test.tsx
git commit -m "test: add help guide modal coverage"
```

### Task 2: Wire The Header Trigger And Modal State

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Header.tsx`
- Modify: `frontend/src/components/LoginGate.tsx`
- Modify: `frontend/src/lib/auth.test.ts` if auth shell behavior changes

**Step 1: Write the minimal integration**

In `App.tsx`:

- add `isGuideOpen` state
- derive default language from `navigator.language`
- render `GuideModal`

In `Header.tsx`:

- add `Help / 사용법` button
- pass click handler from `App`

**Step 2: Run the test**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx`

Expected: PASS for help guide open, tab switch, and close behavior.

**Step 3: Keep login state clean**

Ensure the guide is only shown in the authenticated shell, not the login gate.

**Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/Header.tsx
git commit -m "feat: add global help guide trigger"
```

### Task 3: Style The Modal For Desktop And Mobile

**Files:**
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/App.test.tsx`

**Step 1: Add modal styles**

Add styles for:

- backdrop
- modal shell
- tab row
- active tab
- scrollable body
- responsive mobile spacing

**Step 2: Verify modal structure still passes tests**

Run: `cd /opt/Paper/frontend && npm test -- --run src/App.test.tsx`

Expected: PASS

**Step 3: Build the frontend**

Run: `cd /opt/Paper/frontend && npm run build`

Expected: PASS

**Step 4: Commit**

```bash
git add frontend/src/styles.css
git commit -m "style: add bilingual help guide modal"
```

### Task 4: Full Verification And Rollout

**Files:**
- Modify: none unless verification fails

**Step 1: Run full frontend verification**

Run: `cd /opt/Paper/frontend && npm test -- --run && npm run build`

Expected: all tests pass and production build succeeds

**Step 2: Run backend regression check**

Run: `cd /opt/Paper/backend && . .venv/bin/activate && pytest -q`

Expected: PASS

**Step 3: Rebuild and restart the frontend container**

Run: `docker compose -f /opt/Paper/docker-compose.yml up -d --build frontend`

Expected: frontend container restarts cleanly

**Step 4: Smoke-check the public app**

Run: `curl -sS -o /dev/null -w '%{http_code}\n' https://paper.k-biofoundrycopilot.duckdns.org/`

Expected: `200`

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add bilingual paper usage guide"
```
