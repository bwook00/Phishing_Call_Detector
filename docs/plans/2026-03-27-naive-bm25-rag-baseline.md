# Naive BM25 RAG Baseline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a minimal BM25-based RAG baseline that evaluates `voicephishing_qa_dataset.csv` against `voicephishing_corpus_v2.csv` and `voicephishing_corpus_masked.csv`.

**Architecture:** A single Python entrypoint loads one corpus CSV, tokenizes each scenario, builds a simple BM25 retriever, retrieves top-k corpus rows for each QA scenario, formats a strict yes/no classification prompt with retrieved context, calls the model once per row, and writes a results CSV plus summary metrics. The implementation stays intentionally small so the only major experimental variable is `original` vs `masked` corpus.

**Tech Stack:** Python 3 standard library, OpenAI Responses API client if available, local CSV files, lightweight BM25 implementation in-repo.

---

### Task 1: Add Retrieval Tests

**Files:**
- Create: `tests/test_naive_bm25_rag.py`

**Step 1: Write the failing test**

Add tests for:
- BM25 index creation from tiny in-memory documents
- top-k retrieval returning the expected matching document first
- summary metric computation from toy yes/no predictions

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL because the module does not exist yet

**Step 3: Write minimal implementation**

Create the module skeleton referenced by the tests with placeholder functions/classes.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS

### Task 2: Implement Naive BM25 Pipeline

**Files:**
- Create: `naive_bm25_rag.py`
- Modify: `tests/test_naive_bm25_rag.py`

**Step 1: Write the failing test**

Add one higher-level test for:
- loading a tiny corpus CSV
- building the retriever
- generating a prompt payload from a toy QA row

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL on missing loader/prompt functions

**Step 3: Write minimal implementation**

Implement:
- corpus/qa CSV loaders
- simple tokenizer
- BM25 scorer
- top-k retrieval
- prompt builder
- metric summarizer

Keep LLM call code isolated behind one function so dry-run testing stays simple.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS

### Task 3: Add CLI for Evaluation

**Files:**
- Modify: `naive_bm25_rag.py`

**Step 1: Write the failing test**

Add one CLI-oriented test that checks argument parsing or output path defaults.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: FAIL on missing CLI utility

**Step 3: Write minimal implementation**

Add CLI arguments for:
- `--corpus`
- `--qa`
- `--top-k`
- `--output`
- `--model`
- `--limit`
- `--dry-run`

Outputs:
- per-row results CSV
- small summary text/json block printed to stdout

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_naive_bm25_rag.py -q`
Expected: PASS

### Task 4: Dry-Run Verification

**Files:**
- Modify: `naive_bm25_rag.py` if needed

**Step 1: Run retrieval-only dry run**

Run:

```bash
python naive_bm25_rag.py \
  --corpus data/voicephishing_corpus_v2.csv \
  --qa data/voicephishing_qa_dataset.csv \
  --top-k 3 \
  --limit 5 \
  --dry-run
```

Expected:
- no API call
- prompt preview / retrieval metadata prints cleanly
- output schema is valid

**Step 2: Run masked dry run**

Run:

```bash
python naive_bm25_rag.py \
  --corpus data/voicephishing_corpus_masked.csv \
  --qa data/voicephishing_qa_dataset.csv \
  --top-k 3 \
  --limit 5 \
  --dry-run
```

Expected:
- same flow works with masked corpus

### Task 5: Real Evaluation Commands

**Files:**
- No code change required unless dry-run finds issues

**Step 1: Run original corpus evaluation**

```bash
python naive_bm25_rag.py \
  --corpus data/voicephishing_corpus_v2.csv \
  --qa data/voicephishing_qa_dataset.csv \
  --top-k 3 \
  --model <model_name> \
  --output data/naive_rag_original_results.csv
```

**Step 2: Run masked corpus evaluation**

```bash
python naive_bm25_rag.py \
  --corpus data/voicephishing_corpus_masked.csv \
  --qa data/voicephishing_qa_dataset.csv \
  --top-k 3 \
  --model <model_name> \
  --output data/naive_rag_masked_results.csv
```

**Step 3: Compare**

Compare:
- overall accuracy
- source-type metrics
- false positives on `bank_call`
- false negatives on `voicephishing`

