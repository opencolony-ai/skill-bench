# Short Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shorten URLs to 7-character codes stored in links.db.

**Architecture:** One small module and its tests.

**Tech Stack:** see Global Constraints

**Spec:** `spec.md`

## Global Constraints

- Python 3.11 or newer
- Standard library only (no new dependencies)

## Review Focus

- The same URL twice returns the same code
- A URL with unicode characters

---

### Task 1: Code generation

**Files:**
- Create: `shortlinks/codes.py`
- Test: `tests/test_codes.py`

**Interfaces:**
- Produces: `new_code() -> str`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_codes.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `new_code() -> str` in `shortlinks/codes.py`**

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_codes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

### Task 2: Store and resolve

**Files:**
- Create: `shortlinks/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Produces: `shorten(url: str) -> str  # raises ShortenError after 3 collisions`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_store.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `shorten(url: str) -> str  # raises ShortenError after 3 collisions` in `shortlinks/store.py`**

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_store.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
