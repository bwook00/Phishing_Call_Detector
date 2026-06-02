# Expanded Hard Benchmark 500 Results

## Dataset
- Source: `data/reinforced_v5_binary_qa_67.csv`
- Output: `data/expanded_hard_binary_qa_500.csv`
- Construction: transcript/format-preserving augmentation from the hard binary benchmark.
- Composition: 500 rows total
  - `voicephishing`: 250
  - `bank_call`: 250
  - `irrelevant`: excluded

The 500-row set is an augmented hard benchmark, not a fully independent 500-scenario external test set. It is intended to verify whether the 335-row result trend remains stable under additional transcript-style surface variation.

## Retrieval-threshold results

| Experiment | Overall | Voicephishing | Bank call |
| --- | ---: | ---: | ---: |
| Original Naive RAG | 409/500 = **0.8180** | 174/250 = **0.6960** | 235/250 = **0.9400** |
| Masked Naive RAG | 271/500 = **0.5420** | 36/250 = **0.1440** | 235/250 = **0.9400** |
| Masked Advanced RAG | 455/500 = **0.9100** | 221/250 = **0.8840** | 234/250 = **0.9360** |

## Confusion summary

| Experiment | TP | FN | TN | FP |
| --- | ---: | ---: | ---: | ---: |
| Original Naive RAG | 174 | 76 | 235 | 15 |
| Masked Naive RAG | 36 | 214 | 235 | 15 |
| Masked Advanced RAG | 221 | 29 | 234 | 16 |

## Interpretation
The 500-row augmented benchmark preserves the 335-row trend:

1. Original Naive RAG remains around 0.82.
2. Masked Naive RAG remains around 0.54, with a sharp drop on voicephishing positives.
3. Masked Advanced RAG remains around 0.91 and recovers most of the masked positive recall.

This supports the claim that the observed result is not limited to the initial 335-row augmented set, at least under additional transcript-style surface variations.

## Artifacts
- Generation script: `build_expanded_hard_benchmark_500.py`
- Dataset: `data/expanded_hard_binary_qa_500.csv`
- Result CSVs:
  - `data/expanded500_original_naive_threshold_results.csv`
  - `data/expanded500_masked_naive_threshold_results.csv`
  - `data/expanded500_masked_advanced_rag_threshold_results.csv`
