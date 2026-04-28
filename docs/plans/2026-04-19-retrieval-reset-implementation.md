# Retrieval Reset Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add retrieval-regime controls, retrieval audit metadata, and stronger masking bundles so the next pilot can optimize masked degradation at the retrieval layer.

**Architecture:** Extend `naive_bm25_rag.py` with explicit realistic/strict retrieval regimes and row-level audit metadata. Extend masking so identifier-rich bundles collapse more aggressively before strong-token replacement.

**Tech Stack:** Python 3, pytest, CSV-based benchmark utilities

---

### Task 1: Lock retrieval-regime parsing and audit metadata with tests

**Files:**
- Modify: `tests/test_naive_bm25_rag.py`

**Step 1: Write the failing test**

- Add parser coverage for `--retrieval-regime realistic`.
- Add helper coverage for realistic vs strict exclusion behavior.
- Add retrieval metadata coverage for top-family and margin fields.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_naive_bm25_rag.py -q`

Expected: FAIL because the regime helper and metadata fields do not exist yet.

### Task 2: Lock stronger bundle masking with tests

**Files:**
- Modify: `tests/test_qa_masking.py`
- Modify: `tests/test_strong_masking.py`

**Step 1: Write the failing test**

- Add coverage for institution bundle compression.
- Add coverage for identifier bundle compression.
- Add coverage for strong-token replacement of new bundle placeholders.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_qa_masking.py tests/test_strong_masking.py -q`

Expected: FAIL because the bundle placeholders do not exist yet.

### Task 3: Implement minimal retrieval reset

**Files:**
- Modify: `naive_bm25_rag.py`
- Modify: `qa_masking.py`
- Modify: `strong_masking.py`

**Step 1: Add retrieval regime helper and metadata**

- Add a regime helper for `custom`, `realistic`, and `strict`.
- Add retrieval audit fields to result rows.

**Step 2: Add bundle masking**

- Add institution/contact bundle masking.
- Add personal identifier and case/receipt bundle masking.
- Keep backward compatibility for the existing placeholder-level masking.

**Step 3: Run focused tests**

Run: `python3 -m pytest tests/test_naive_bm25_rag.py tests/test_qa_masking.py tests/test_strong_masking.py -q`

Expected: PASS

### Task 4: Verify repo health

**Files:**
- No code changes required

**Step 1: Run full test suite**

Run: `python3 -m pytest tests -q`

Expected: PASS

### Task 5: Prepare next experiment commands

**Files:**
- No code changes required

**Step 1: Document next-run commands**

- Dry-run retrieval in `realistic` mode
- Dry-run retrieval in `strict` mode
- Rebuild strong-masked corpus after masking changes

**Step 2: Save command set in final handoff**

- Include the exact benchmark commands needed for the next pilot.
