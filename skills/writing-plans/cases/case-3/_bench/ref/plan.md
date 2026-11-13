# Contact Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import contacts from CSV with dedupe by email and a summary line.

**Architecture:** One small module and its tests.

**Tech Stack:** see Global Constraints

**Spec:** `spec.md`

## Global Constraints

- Go 1.22
- No third-party modules

## Review Focus

- A CSV with a byte-order mark
- Emails differing only in case

---

### Task 1: Read and validate rows

**Files:**
- Create: `importer/read.go`
- Test: `importer/read_test.go`

**Interfaces:**
- Produces: `ReadRows(r io.Reader) ([]Row, []Rejected, error)  // refuses more than 10,000 rows`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./importer -run TestReadRows`
Expected: FAIL

- [ ] **Step 3: Implement `ReadRows(r io.Reader) ([]Row, []Rejected, error)  // refuses more than 10,000 rows` in `importer/read.go`**

- [ ] **Step 4: Run test to verify it passes**

Run: `go test ./importer -run TestReadRows`
Expected: PASS

- [ ] **Step 5: Commit**

### Task 2: Dedupe and report

**Files:**
- Create: `importer/report.go`
- Test: `importer/report_test.go`

**Interfaces:**
- Produces: `Summary(imported, dup, rej int) string  // "imported N, duplicates D, rejected R"`

- [ ] **Step 1: Write the failing test**

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./importer -run TestSummary`
Expected: FAIL

- [ ] **Step 3: Implement `Summary(imported, dup, rej int) string  // "imported N, duplicates D, rejected R"` in `importer/report.go`**

- [ ] **Step 4: Run test to verify it passes**

Run: `go test ./importer -run TestSummary`
Expected: PASS

- [ ] **Step 5: Commit**
