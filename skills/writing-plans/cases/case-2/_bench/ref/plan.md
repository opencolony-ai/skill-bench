# Rate Limiting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Limit each API key to 100 requests per 60 s, answering 429 with Retry-After.

**Architecture:** One small module and its tests.

**Tech Stack:** see Global Constraints

**Spec:** `spec.md`

## Global Constraints

- TypeScript
- Node 20
- Tests with vitest
- In memory, no Redis

## Review Focus

- Two requests in the same millisecond at the limit
- GET /healthz under load

---

### Task 1: Token bucket

**Files:**
- Create: `src/limit/bucket.ts`
- Test: `test/bucket.test.ts`

**Interfaces:**
- Produces: `take(key: string, now: number): {ok: boolean, retryAfter: number}`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run test/bucket.test.ts`
Expected: FAIL

- [ ] **Step 3: Implement `take(key: string, now: number): {ok: boolean, retryAfter: number}` in `src/limit/bucket.ts`**

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run test/bucket.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

### Task 2: Middleware

**Files:**
- Create: `src/limit/middleware.ts`
- Test: `test/middleware.test.ts`

**Interfaces:**
- Produces: `rateLimit(): RequestHandler  // 429 + Retry-After, skips /healthz`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run test/middleware.test.ts`
Expected: FAIL

- [ ] **Step 3: Implement `rateLimit(): RequestHandler  // 429 + Retry-After, skips /healthz` in `src/limit/middleware.ts`**

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run test/middleware.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**
