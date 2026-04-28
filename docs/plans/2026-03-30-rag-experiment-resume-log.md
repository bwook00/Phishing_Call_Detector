# RAG Experiment Resume Log

**Date:** 2026-03-30  
**Goal:** Produce a large gap between `Original Naive RAG` and `Masked Naive RAG`, ideally with original high and masked significantly lower.  
**Current reality:** Many prompt-only interventions move both scores together. The most reliable gap so far came from the BM25 threshold baseline, not the LLM-judged RAG runs.

---

## Current Ground Truth

### Data / corpus state
- Original corpus: [data/voicephishing_corpus_v2.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_v2.csv)
- Placeholder-masked corpus: [data/voicephishing_corpus_masked.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_masked.csv)
- Strong-masked corpus: [data/voicephishing_corpus_masked_strong.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_masked_strong.csv)

### Strong masking status
Strong masking is definitely applied. Placeholder tokens such as:
- `[기관명]`
- `[이름]`
- `[은행명]`
- `[사건번호]`
- `[주소]`

were replaced with opaque strings such as:
- `uiuiufawaefiiifji`
- `qmqmzkkvvopaa`
- `bbbqrrtuuplkz`
- `xxyyqqppmmrrt`
- `aaeiioouuzzxx`

Verification:
- [data/voicephishing_corpus_masked_strong.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_masked_strong.csv)
- placeholder counts in strong corpus were confirmed to be `0`

---

## Important Interpretation

### Why original often dropped too low
In several late experiments, the prompt was intentionally turned into a **stress-test similarity judge** rather than a normal phishing classifier.

Examples:
- `70% similarity threshold`
- `80% similarity threshold`
- `direct evidence only`

These settings were useful for diagnosis, but they were **not** the same as the desired “reasonable operational RAG setting.” They often pushed original down along with masked.

### Main diagnosis so far
1. Query text still carries too much structural signal, so LLMs often judge from the query itself.
2. If the prompt is weak, both original and masked stay high.
3. If the prompt is too strict, both original and masked drop.
4. Strong masking alone did **not** reliably lower masked when the query remained unmasked.
5. Model changes (`gpt-4o-mini`, `gpt-5.4-mini`, `claude-haiku-4-5`) did **not** solve the core issue by themselves.

---

## Best Completed Results So Far

### BM25-threshold baseline
- Original: **0.79**
- Masked: **0.46**
- Files:
  - [data/pilot_original_naive_threshold_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/pilot_original_naive_threshold_results.csv)
  - [data/pilot_masked_naive_threshold_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/pilot_masked_naive_threshold_results.csv)
- Interpretation:
  - This is the cleanest separation found so far.
  - But it is a retrieval-threshold baseline, not the final LLM-judged RAG result.

### LLM-judged pilot results

#### Basic RAG with query + retrieval
- Original: **1.00**
- Masked: **1.00**
- Files:
  - [data/pilot_original_with_query_gpt4omini_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/pilot_original_with_query_gpt4omini_results.csv)
  - [data/pilot_masked_with_query_gpt4omini_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/pilot_masked_with_query_gpt4omini_results.csv)
- Interpretation:
  - Too easy. Query text leaked too much direct phishing signal.

#### Reinforced v2 QA, weaker retrieval-dependent prompts
- Original: **0.77**
- Masked: **0.84**
- Files:
  - [data/reinforced_v2_original_gpt4omini_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v2_original_gpt4omini_results.csv)
  - [data/reinforced_v2_masked_gpt4omini_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v2_masked_gpt4omini_results.csv)
- Interpretation:
  - Original acceptable.
  - Masked still too high.

#### Reinforced v2, stricter retrieval-dependent prompts
- v3-like prompt:
  - Original: **0.66**
  - Masked: **0.68**
- v5 direct-evidence prompt:
  - Original: **0.72**
  - Masked: **0.71**
- Files:
  - [data/reinforced_v2_original_gpt4omini_v3_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v2_original_gpt4omini_v3_results.csv)
  - [data/reinforced_v2_masked_gpt4omini_v3_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v2_masked_gpt4omini_v3_results.csv)
  - [data/reinforced_v2_original_gpt4omini_v5_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v2_original_gpt4omini_v5_results.csv)
  - [data/reinforced_v2_masked_gpt4omini_v5_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v2_masked_gpt4omini_v5_results.csv)
- Interpretation:
  - Prompt-only changes mostly move both original and masked together.

#### Reinforced v3 QA, 70% threshold
- Original: **0.66**
- Hard masked: **0.71**
- Files:
  - [data/reinforced_v3_original_gpt4omini_v7_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v3_original_gpt4omini_v7_results.csv)
  - [data/reinforced_v3_masked_strong_gpt4omini_v7_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v3_masked_strong_gpt4omini_v7_results.csv)
- Interpretation:
  - Even hard masked did not create the desired direction.

### Model comparison
- `gpt-4o-mini`: frequently made masked higher than expected
- `gpt-5.4-mini`: did not fix the gap problem by itself
  - Files:
    - [data/reinforced_v3_original_gpt54mini_sim_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v3_original_gpt54mini_sim_results.csv)
    - [data/reinforced_v3_masked_gpt54mini_sim_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v3_masked_gpt54mini_sim_results.csv)
- `claude-haiku-4-5`: made original and hard-masked collapse to the same result
  - Original: **0.66**
  - Hard masked: **0.66**
  - Files:
    - [data/reinforced_v3_original_haiku_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v3_original_haiku_results.csv)
    - [data/reinforced_v3_masked_strong_haiku_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v3_masked_strong_haiku_results.csv)

---

## What Was Learned

### What did **not** work
- Using only stronger masking on the corpus while leaving query unmasked
- Relying on similarity prompts alone to create the gap
- Switching the judge model alone
- Overly strict prompts such as:
  - `80% similarity`
  - `direct evidence only`

### What did work partially
- Making `voicephishing` less explicit can reduce model shortcutting
- Making `bank_call` more suspicious can push more false positives
- The strongest clean gap was still the BM25 threshold baseline

---

## Current Active Work

### Active batch jobs to resume after restart

#### Reinforced v4 QA generation
- Batch ID: `batch_69ca0ebf2408819097775ce1747c9d55`
- Last checked status: `completed`
- Output file id: `file-BZmsrqPxEWpd2Vv6dBB3yD`
- Result CSV already materialized:
  - [data/reinforced_v4_qa_100.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_qa_100.csv)

#### Reinforced v4 evaluation
- Not yet completed at the time of this note
- Need to continue from:
  - retrieval-only generation
  - original vs hard masked batch evaluation

### Important current files for resume
- [data/reinforced_v4_qa_100.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_qa_100.csv)
- [data/voicephishing_corpus_v2.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_v2.csv)
- [data/voicephishing_corpus_masked.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_masked.csv)
- [data/voicephishing_corpus_masked_strong.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_masked_strong.csv)
- [naive_bm25_rag.py](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/naive_bm25_rag.py)
- [regenerate_hard_qa_dataset.py](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/regenerate_hard_qa_dataset.py)
- [strong_masking.py](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/strong_masking.py)
- [qa_masking.py](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/qa_masking.py)

---

## Resume Instructions

### If resuming the exact same line of work
1. Check active batch state for any unfinished OpenAI jobs.
2. If an evaluation batch is completed, download its output file.
3. Merge it with the matching retrieval-only CSV.
4. Summarize accuracy by source type.

### Suggested next move after reboot
My recommendation after reboot is:
1. Do **not** keep cycling only prompt wording.
2. Use the BM25 threshold result as the most stable reference gap.
3. For LLM-judged RAG, focus on:
   - making `bank_call` much more suspicious
   - making `voicephishing` high in identifiers but less explicit in scam actions
   - keeping original query strong and masked conditions paired from the same base dialogue
4. Evaluate only on `100` rows until a convincing gap appears.

### If professor update is needed immediately
Safe summary:
- “Prompt-only changes moved both original and masked together.”
- “The clearest separation so far came from the retrieval-threshold baseline.”
- “LLM-judged RAG needs a better-balanced dataset with stronger hard negatives.”

---

## Bottom Line

The experiments did **not** show a simple prompt or model switch that cleanly yields `high original / low masked`.
The strongest evidence so far is:
- the problem is mostly **data/query design**, not just model choice
- the BM25 threshold baseline currently provides the clearest gap
- stronger masking or stronger prompts alone do not reliably lower masked in the desired way

---

## Resume Continuation Update

### What was recovered and fixed
- The saved `reinforced_v4` evaluation request files already existed:
  - [data/reinforced_v4_original_gpt4omini_v7_batch_requests.jsonl](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_original_gpt4omini_v7_batch_requests.jsonl)
  - [data/reinforced_v4_masked_strong_gpt4omini_v7_batch_requests.jsonl](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_masked_strong_gpt4omini_v7_batch_requests.jsonl)
- The earlier `v4` evaluation batches were not recoverable because both had been cancelled before any request completed:
  - original: `batch_69ca9d57b2108190b1a6f3d3a7c86c5a`
  - hard masked: `batch_69ca9d5918248190a5843a4145ca3aa3`
  - both showed:
    - status: `cancelled`
    - completed requests: `0 / 100`
    - output file: none
- `naive_bm25_rag.py` batch merge support was updated so local merge now works with OpenAI batch output JSONL, not only Anthropic-style result lines.

### New resumed v4 batch run
- Resubmitted original batch:
  - batch id: `batch_69cb54ccb5f48190ab18fd66aa67f7c2`
  - output file id: `file-BdUWDi7wJG8ExaiWz4GNPH`
  - meta file:
    - [data/reinforced_v4_original_gpt4omini_v7_batch_meta.json](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_original_gpt4omini_v7_batch_meta.json)
- Resubmitted hard-masked batch:
  - batch id: `batch_69cb54cd2b0c8190bed73d760665d750`
  - output file id: `file-YHLekjW2zarkfgxcoC6oPM`
  - meta file:
    - [data/reinforced_v4_masked_strong_gpt4omini_v7_batch_meta.json](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_masked_strong_gpt4omini_v7_batch_meta.json)
- Both resumed batches completed successfully:
  - completed requests: `100 / 100`
  - failed requests: `0`

### Materialized v4 results
- Downloaded output JSONL files:
  - [data/reinforced_v4_original_gpt4omini_v7_batch_output.jsonl](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_original_gpt4omini_v7_batch_output.jsonl)
  - [data/reinforced_v4_masked_strong_gpt4omini_v7_batch_output.jsonl](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_masked_strong_gpt4omini_v7_batch_output.jsonl)
- Merged result CSV files:
  - [data/reinforced_v4_original_gpt4omini_v7_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_original_gpt4omini_v7_results.csv)
  - [data/reinforced_v4_masked_strong_gpt4omini_v7_results.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/reinforced_v4_masked_strong_gpt4omini_v7_results.csv)

### v4 outcome summary
- Original: **0.66**
- Hard masked: **0.66**
- Interpretation:
  - This `v4` run again failed to produce the desired separation.
  - The total score is identical even though retrieval differed on every row.
  - Predictions were not completely identical:
    - prediction differences between original and hard masked: `8 / 100`
  - But those differences cancelled out at the aggregate accuracy level.

### Original v4 class behavior snapshot
- `voicephishing`: `2 / 34` correct (`0.0588`)
- `bank_call`: `31 / 33` correct (`0.9394`)
- `irrelevant`: `33 / 33` correct (`1.0000`)
- Interpretation:
  - The main collapse came from almost all `voicephishing` rows being judged `no`.
  - This means the current retrieval-dependent similarity prompt is now too strict for the positive class on this `v4` dataset.

### Practical next move
- Do not treat `v4` as a masked-collapse success case.
- Use the recovered `v4` result as further evidence that:
  - retrieval can differ substantially between original and hard masked
  - but the current judge prompt still collapses both systems to almost the same aggregate accuracy
- Best next direction remains:
  - adjust dataset/query balance so original positives stay recoverable
  - avoid a prompt that wipes out `voicephishing` recall for both settings
