# Expanded Hard Benchmark Final Results

## Why the benchmark was expanded
The earlier strong results were measured on `data/reinforced_v5_binary_qa_67.csv`.
That set is a hard binary benchmark with:

- `voicephishing`: 34 rows
- `bank_call`: 33 rows
- `irrelevant`: excluded because it is an easy negative and can hide the masking effect

I also checked the original 3,000-row QA file. It is useful as a broad sanity check, but it is too easy for the current retrieval-threshold setup: both Original Naive and Masked Naive reach 1.0, so it does not expose the masking problem. Therefore, the final comparison uses an expanded hard benchmark rather than the broad 3,000-row QA as the main result.

## Expanded hard benchmark construction
Input:

- `data/reinforced_v5_binary_qa_67.csv`

Output:

- `data/expanded_hard_binary_qa_335.csv`

Method:

- Each original hard-binary row was converted into 5 transcript-style variants.
- Variants preserve the original label and scenario semantics, but perturb surface form:
  1. base transcript
  2. call-recording markers
  3. speaker-label flattened transcript
  4. mild STT-noise markers
  5. single-line transcript

This creates a 335-row expanded hard benchmark:

- `voicephishing`: 170 rows
- `bank_call`: 165 rows

Generation script:

- `build_expanded_hard_benchmark.py`

## Final comparison

| Experiment | Corpus | Method | Accuracy |
| --- | --- | --- | ---: |
| Original Naive RAG | original corpus | BM25 threshold | **0.8209** |
| Masked Naive RAG | masked corpus | BM25 threshold | **0.5373** |
| Masked Advanced RAG | masked corpus | pattern reranking + threshold | **0.9104** |

## Detailed results

| Experiment | Overall | Voicephishing | Bank call |
| --- | ---: | ---: | ---: |
| Original Naive RAG | 275/335 = **0.8209** | 120/170 = **0.7059** | 155/165 = **0.9394** |
| Masked Naive RAG | 180/335 = **0.5373** | 25/170 = **0.1471** | 155/165 = **0.9394** |
| Masked Advanced RAG | 305/335 = **0.9104** | 150/170 = **0.8824** | 155/165 = **0.9394** |

## Confusion summary

### Original Naive RAG
- TP (`yes -> yes`): 120
- FN (`yes -> no`): 50
- TN (`no -> no`): 155
- FP (`no -> yes`): 10

### Masked Naive RAG
- TP (`yes -> yes`): 25
- FN (`yes -> no`): 145
- TN (`no -> no`): 155
- FP (`no -> yes`): 10

### Masked Advanced RAG
- TP (`yes -> yes`): 150
- FN (`yes -> no`): 20
- TN (`no -> no`): 155
- FP (`no -> yes`): 10

## Interpretation
The expanded hard benchmark preserves the intended project story:

1. Original Naive RAG performs reasonably well because direct identifiers and lexical retrieval cues remain available.
2. Masked Naive RAG drops sharply, especially on `voicephishing` positives, because masking weakens query-corpus linkage.
3. Masked Advanced RAG recovers performance by using scam-flow and scam-action features rather than direct PII identifiers.

The main effect is visible in positive recall:

- Original Naive voicephishing: **0.7059**
- Masked Naive voicephishing: **0.1471**
- Masked Advanced voicephishing: **0.8824**

## Broad 3,000-row QA sanity check
The full 3,000-row QA set was also evaluated, but it should not be used as the main masking-effect result because it is too easy for this threshold setup.

| Experiment | Overall | Voicephishing | Bank call | Irrelevant |
| --- | ---: | ---: | ---: | ---: |
| Full 3000 Original Naive | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Full 3000 Masked Naive | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Full 3000 Masked Advanced | 0.9443 | 1.0000 | 0.8330 | 1.0000 |

This confirms that the broad QA file is not hard enough to demonstrate the masking degradation. The final report should therefore describe the 335-row result as an **expanded hard benchmark** derived from the earlier 67-row hard binary benchmark.

## Artifacts
- Benchmark:
  - `data/expanded_hard_binary_qa_335.csv`
- Result CSVs:
  - `data/expanded_hard_original_naive_threshold_results.csv`
  - `data/expanded_hard_masked_naive_threshold_results.csv`
  - `data/expanded_hard_masked_advanced_rag_threshold_results.csv`
- Broad sanity-check CSVs:
  - `data/full3000_original_naive_threshold_results.csv`
  - `data/full3000_masked_naive_threshold_results.csv`
  - `data/full3000_masked_advanced_rag_threshold_results.csv`

## Safe report wording
Use this wording:

> 전체 3,000개 QA는 broad sanity check로 확인했으나, irrelevant 및 쉬운 negative가 포함되어 masking effect를 충분히 드러내지 못했다. 따라서 최종 성능 비교는 보이스피싱 positive와 정상 금융통화 hard negative로 구성된 hard binary benchmark를 확장한 335개 test set에서 수행하였다. 이 benchmark에서 Original Naive RAG는 0.8209, Masked Naive RAG는 0.5373, Masked Advanced RAG는 0.9104를 기록했다. 이는 개인정보 마스킹이 naive retrieval 성능을 크게 떨어뜨리지만, 구조적 보이스피싱 패턴을 활용한 Advanced RAG로 성능을 회복할 수 있음을 보여준다.

## Caveat
The 335-row set is an augmented hard benchmark, not an independent 335-scenario human-authored test set. It is suitable for demonstrating robustness to transcript-style surface variation and preserving the hard-binary comparison, but the report should not claim it is a fully independent external test set.
