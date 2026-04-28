# E2E RAG Realignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the end-to-end LLM-judged RAG metric reflect the original/masked retrieval gap strongly enough to hit original >= 0.80 and masked <= 0.60 on the current binary benchmark.

**Architecture:** Keep the current BM25 retrieval pipeline and binary dataset, but add retrieval-gated prompt modes plus lightweight anchor summaries so the judge must reason over evidence alignment instead of query-only scam cues. Validate locally with tests, then run paired live evaluations on original and masked corpora.

**Tech Stack:** Python, pytest, BM25 retrieval, OpenAI Responses API.

---

### Task 1: Add failing tests for retrieval-gated prompt behavior

**Files:**
- Modify: `tests/test_naive_bm25_rag.py`
- Modify: `naive_bm25_rag.py`

**Step 1: Write the failing test**
Add tests that expect:
- a new prompt mode to exist
- the prompt to forbid query-only decisions
- the prompt to mention support / contradiction / insufficient evidence behavior
- optional anchor summary text to appear when provided

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL on missing prompt mode / helper.

**Step 3: Write minimal implementation**
Implement the new prompt mode and any helper functions needed to format evidence summaries.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS.

### Task 2: Add query/context anchor summarization

**Files:**
- Modify: `naive_bm25_rag.py`
- Modify: `tests/test_naive_bm25_rag.py`

**Step 1: Write the failing test**
Add tests for extracting scam / legitimate / identifier anchors from query and retrieved contexts.

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL on missing summary helper.

**Step 3: Write minimal implementation**
Implement helper(s) that summarize anchor overlaps and unique context evidence.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS.

### Task 3: Extend CLI to use new prompt mode in evaluation

**Files:**
- Modify: `naive_bm25_rag.py`
- Modify: `tests/test_naive_bm25_rag.py`

**Step 1: Write the failing test**
Add parse-args coverage for the new prompt mode.

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL.

**Step 3: Write minimal implementation**
Add the prompt mode to CLI choices and wire it into evaluation.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS.

### Task 4: Run local regression checks

**Files:**
- Test: `tests/test_naive_bm25_rag.py`
- Test: `tests/test_regenerate_hard_qa_dataset.py`
- Test: `tests/test_build_rag_benchmark.py`
- Test: `tests/test_qa_masking.py`
- Test: `tests/test_strong_masking.py`

**Step 1: Run targeted tests**
Run: `pytest tests/test_naive_bm25_rag.py tests/test_regenerate_hard_qa_dataset.py tests/test_build_rag_benchmark.py tests/test_qa_masking.py tests/test_strong_masking.py -q`
Expected: PASS.

### Task 5: Run e2e paired live evaluations

**Files:**
- Generate: `data/reinforced_v5_binary_original_<mode>_results.csv`
- Generate: `data/reinforced_v5_binary_masked_<mode>_results.csv`

**Step 1: Smoke-test prompt generation**
Run: `python naive_bm25_rag.py --corpus ... --qa ... --prompt-mode <mode> --dry-run --limit 2`
Expected: prompt preview includes retrieval-gated instructions.

**Step 2: Run original live evaluation**
Run with the chosen model and realistic regime.

**Step 3: Run masked live evaluation**
Run the paired masked evaluation with the same settings.

**Step 4: Summarize results**
Compare original vs masked overall and by source type.

**Step 5: Decision**
- If target band reached: record canonical e2e artifact.
- If not: iterate prompt/top-k once more, then escalate to structured judge redesign.
