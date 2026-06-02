# Phishing Call Detector

개인정보 마스킹 환경에서 보이스피싱 탐지 RAG의 성능 변화를 비교한 졸업프로젝트 코드입니다.

## Project title

**보이스피싱 탐지를 위한 개인정보 마스킹 환경의 RAG 시스템 설계**

## Summary

본 프로젝트는 보이스피싱 탐지에서 개인정보/식별 단서가 RAG retrieval 성능에 미치는 영향을 확인합니다.
동일한 hard negative benchmark에서 다음 3개 조건을 비교했습니다.

1. **Original RAG**: 원본 corpus 기반 Naive RAG
2. **Masked RAG**: 개인정보 마스킹 corpus 기반 Naive RAG
3. **Masked Advanced RAG**: 마스킹 환경에서 보이스피싱 구조적 패턴과 정상 금융상담 guard를 활용한 개선 RAG

## Final benchmark

최종 평가는 `voicephishing` positive와 `bank_call` hard negative로 구성한 1000개 증강 benchmark에서 수행했습니다.

- Dataset: `data/expanded_hard_binary_qa_1000.csv`
- Voicephishing: 500
- Bank call: 500
- Irrelevant samples are excluded from the final hard-negative comparison.

## Final results

### Retrieval-threshold evaluation

| Pipeline | Accuracy |
|---|---:|
| Original Naive RAG | 0.8210 |
| Masked Naive RAG | 0.5410 |
| Masked Advanced RAG | 0.9110 |

### End-to-end RAG evaluation

| Pipeline | Accuracy |
|---|---:|
| Original RAG | 0.8940 |
| Masked RAG | 0.5130 |
| Masked Advanced RAG | 0.9530 |

## Key files

### Core code

- `naive_bm25_rag.py` — BM25 RAG, identifier-filtered flow, advanced pattern reranking/threshold evaluation, batch merge utilities
- `qa_masking.py` — QA masking helpers
- `strong_masking.py` — strong masking helpers
- `build_rag_benchmark.py` — benchmark construction utilities
- `build_expanded_hard_benchmark_500.py` — 500-row augmented hard benchmark builder
- `build_expanded_hard_benchmark_extra_500.py` — additional 500-row non-overlap augmentation builder
- `analyze_dataset_sanity.py` — 1000-row sanity-check metric generation
- `make_sanity_svgs.py` — simple SVG chart generation for sanity-check summaries
- `openai_batch_utils.py` — OpenAI batch request/merge helper

### Final data/results

- `data/expanded_hard_binary_qa_1000.csv`
- `data/expanded1000_original_naive_threshold_results.csv`
- `data/expanded1000_masked_naive_threshold_results.csv`
- `data/expanded1000_masked_advanced_rag_threshold_results.csv`
- `data/e2e1000_original_identifier_filtered_results.csv`
- `data/e2e1000_masked_identifier_filtered_results.csv`
- `data/e2e1000_masked_advanced_guarded_results.csv`
- `docs/results/sanity_check_1000/sanity_check_report.md`
- `docs/plans/2026-05-18-e2e-1000-results.md`

## Reproduce final retrieval-threshold results

```bash
python3 naive_bm25_rag.py evaluate \
  --corpus data/voicephishing_corpus_v2.csv \
  --qa data/expanded_hard_binary_qa_1000.csv \
  --top-k 1 \
  --retrieval-regime realistic \
  --decision-mode bm25-threshold \
  --yes-threshold 61.5 \
  --output data/expanded1000_original_naive_threshold_results.csv

python3 naive_bm25_rag.py evaluate \
  --corpus data/voicephishing_corpus_masked_strong_v2.csv \
  --qa data/expanded_hard_binary_qa_1000.csv \
  --top-k 1 \
  --retrieval-regime realistic \
  --decision-mode bm25-threshold \
  --yes-threshold 61.5 \
  --output data/expanded1000_masked_naive_threshold_results.csv

python3 naive_bm25_rag.py evaluate \
  --corpus data/voicephishing_corpus_masked_strong_v2.csv \
  --qa data/expanded_hard_binary_qa_1000.csv \
  --top-k 1 \
  --retrieval-regime realistic \
  --decision-mode advanced-rag-threshold \
  --retrieval-rerank advanced-rag \
  --advanced-candidate-k 25 \
  --yes-threshold 80 \
  --output data/expanded1000_masked_advanced_rag_threshold_results.csv
```

## Dataset sanity check

```bash
python3 analyze_dataset_sanity.py
python3 make_sanity_svgs.py
```

Outputs are written to:

```text
docs/results/sanity_check_1000/
```

Sanity checks include:

- balanced benchmark composition: 500 voicephishing / 500 bank_call
- no explicit label leakage in the transcript text
- no cross-label exact transcript duplicate
- same-source sample excluded during retrieval (`retrieval_regime=realistic`)
- hard-negative lexical overlap with banking/security terms

## Tests

```bash
python3 -m pytest
```

Current verification snapshot: `74 passed`.

## Notes

- The 1000-row benchmark is an augmented hard-negative benchmark derived from seed scenarios, not a fully independent external dataset.
- OpenAI API keys are needed only for rerunning e2e LLM batch evaluations. Final merged e2e result CSVs are included for inspection.
