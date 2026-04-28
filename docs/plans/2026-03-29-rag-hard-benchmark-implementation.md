# RAG Hard Benchmark Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a fast pilot benchmark workflow that can tune `original naive` and `masked naive` into the requested score bands before running the final hard benchmark.

**Architecture:** Extend the existing BM25 evaluator with retrieval exclusion controls and add a standalone benchmark builder that scores QA rows by retrieval difficulty, emits `pilot-100` and larger hard benchmark CSVs, and supports a fast experiment loop. Keep all logic local and deterministic so benchmark generation can be reproduced from the same input files.

**Tech Stack:** Python 3 standard library, local CSV files, existing `naive_bm25_rag.py`, pytest.

---

### Task 1: Lock exclusion behavior with tests

**Files:**
- Modify: `tests/test_naive_bm25_rag.py`

**Step 1: Write the failing test**

Add tests for:
- excluding the same `sample_id` from retrieval
- excluding the same pattern family prefix such as `P01-*`

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL because exclusion helpers do not exist yet

**Step 3: Write minimal implementation**

Implement exclusion helpers in `naive_bm25_rag.py` and wire them into evaluation.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS

### Task 2: Lock benchmark selection heuristics with tests

**Files:**
- Create: `tests/test_build_rag_benchmark.py`
- Create: `build_rag_benchmark.py`

**Step 1: Write the failing test**

Add tests for:
- selecting hard negatives with higher retrieval confusion score
- producing deterministic output ordering for fixed inputs
- creating a pilot subset with the requested source-type mix when enough rows exist

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_build_rag_benchmark.py -q`
Expected: FAIL because the builder module does not exist yet

**Step 3: Write minimal implementation**

Implement:
- BM25-based confusion scoring against original and masked corpora
- source-type aware ranking
- deterministic pilot subset materialization

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_build_rag_benchmark.py -q`
Expected: PASS

### Task 3: Add CLI controls for fast experiments

**Files:**
- Modify: `naive_bm25_rag.py`
- Modify: `tests/test_naive_bm25_rag.py`

**Step 1: Write the failing test**

Add parser tests for:
- `--exclude-same-sample`
- `--exclude-same-pattern`

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL on missing CLI flags

**Step 3: Write minimal implementation**

Add the flags and pass them through `evaluate()`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS

### Task 4: Materialize pilot benchmark files

**Files:**
- Create: `data/rag_hard_pilot_100.csv`
- Create: `data/rag_hard_official_300.csv`

**Step 1: Run builder**

Run the benchmark builder with:
- input QA dataset
- original and masked corpora
- deterministic seed
- requested pilot mix `40/40/20`

**Step 2: Verify composition**

Check:
- row count
- per-source counts
- deterministic ordering

**Step 3: Save outputs**

Persist pilot and official-hard CSV files under `data/`.

### Task 5: Run fast score loop for naive systems

**Files:**
- No code change required unless the loop exposes issues

**Step 1: Run original naive on `pilot-100`**

Use:
- original corpus
- `top-k=3`
- self and same-pattern exclusion

**Step 2: Run masked naive on `pilot-100`**

Use:
- masked corpus
- `top-k=1`
- self and same-pattern exclusion

**Step 3: Compare against target bands**

Targets:
- original naive: `0.75~0.85`
- masked naive: `0.45~0.6`

**Step 4: Tune if needed**

Tune only:
- pilot subset composition
- hard-negative weight
- `top-k`

Do not change the official-hard set until the pilot loop is acceptable.
