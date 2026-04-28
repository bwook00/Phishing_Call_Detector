# V5 Hard Benchmark Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a reproducible `v5` QA prompt profile that keeps old `v4` behavior intact and enables a new pilot dataset tuned to restore positive recall.

**Architecture:** Extend prompt construction in `regenerate_hard_qa_dataset.py` with an explicit profile parameter. Preserve the current prompt wording as the legacy path, and route new experiments through a separate `v5` ruleset. Lock the change with prompt-focused tests first.

**Tech Stack:** Python, pytest, CSV-based dataset generation, OpenAI Responses API

---

### Task 1: Lock the new prompt-profile surface with tests

**Files:**
- Modify: `tests/test_regenerate_hard_qa_dataset.py`

**Step 1: Write failing tests**

- Add a test that `parse_args(["--prompt-profile", "v5"])` accepts the new flag.
- Add a test that `build_generation_prompt(..., prompt_profile="v5")` for `voicephishing` includes a late scam-anchor requirement.
- Add a test that `build_generation_prompt(..., prompt_profile="v5")` for `bank_call` forbids code readback and link/app actions.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_regenerate_hard_qa_dataset.py -q`

Expected: FAIL because the new flag or prompt-profile behavior does not exist yet.

### Task 2: Implement the `v5` profile with legacy compatibility

**Files:**
- Modify: `regenerate_hard_qa_dataset.py`

**Step 1: Add the profile flag**

- Add `--prompt-profile` with `v4` and `v5` choices.
- Thread the value into prompt construction.

**Step 2: Split prompt rendering**

- Keep current prompt behavior as the `v4` branch.
- Add a `v5` branch for:
  - stronger late scam anchors in `voicephishing`
  - stronger scam-action prohibitions in `bank_call`

**Step 3: Run tests**

Run: `python3 -m pytest tests/test_regenerate_hard_qa_dataset.py -q`

Expected: PASS

### Task 3: Verify the repo still passes

**Files:**
- No code changes required

**Step 1: Run full tests**

Run: `python3 -m pytest tests -q`

Expected: PASS

**Step 2: Dry-run the new profile**

Run: `python3 regenerate_hard_qa_dataset.py --prompt-profile v5 --limit 1 --dry-run`

Expected: prompt preview shows the `v5` rule set.

### Task 4: Materialize the next pilot dataset

**Files:**
- Create: `data/reinforced_v5_qa_100.csv`

**Step 1: Generate the pilot**

Run: `python3 regenerate_hard_qa_dataset.py --prompt-profile v5 --voice-count 34 --bank-count 33 --irrelevant-count 33 --output data/reinforced_v5_qa_100.csv`

Expected: a new 100-row pilot dataset.

**Step 2: Sanity-check composition**

Run a quick CSV summary to confirm:
- `34 voicephishing`
- `33 bank_call`
- `33 irrelevant`

**Step 3: Prepare for evaluation**

- Reuse the existing naive RAG evaluation flow against original and hard-masked corpora.
