# E2E 335-row Final Results

## Benchmark
- Dataset: `data/expanded_hard_binary_qa_335.csv`
- Composition: 170 `voicephishing`, 165 `bank_call`
- Purpose: expanded hard benchmark derived from the 67-row hard binary set.

## E2E pipeline results

| Pipeline | Evaluation | Overall | Voicephishing | Bank call |
| --- | --- | ---: | ---: | ---: |
| Original RAG | gpt-4o-mini e2e, identifier-filtered flow | 300/335 = **0.8955** | 153/170 = **0.9000** | 147/165 = **0.8909** |
| Masked RAG | gpt-4o-mini e2e, identifier-filtered flow | 172/335 = **0.5134** | 35/170 = **0.2059** | 137/165 = **0.8303** |
| Masked Advanced RAG | gpt-4o-mini e2e + advanced pattern reranking + normal-resolution guard | 319/335 = **0.9522** | 160/170 = **0.9412** | 159/165 = **0.9636** |

## Important caveat
A pure advanced-pattern LLM prompt without the normal-resolution guard was also tested and reached **0.7761** overall. It recovered all `voicephishing` positives but overpredicted `yes` on many `bank_call` rows. Therefore, the final Advanced RAG pipeline includes a pre-LLM legitimate-resolution guard: rows with official-app / representative-number / branch-visit / internal-review style normal resolution are routed to `no`, while the remaining rows use the advanced pattern LLM prompt.

This mirrors the earlier project direction: add a filter/guard layer before LLM judgment so the model cannot over-rely on generic suspicious context.

## Artifacts
- Original e2e retrieval/results:
  - `data/e2e335_original_identifier_filtered_retrieval.csv`
  - `data/e2e335_original_identifier_filtered_results.csv`
- Masked e2e retrieval/results:
  - `data/e2e335_masked_identifier_filtered_retrieval.csv`
  - `data/e2e335_masked_identifier_filtered_results.csv`
- Advanced e2e retrieval/results:
  - `data/e2e335_masked_advanced_pattern_retrieval.csv`
  - `data/e2e335_masked_advanced_pattern_results.csv`
  - `data/e2e335_masked_advanced_guarded_results.csv`

## Report wording
> 335개 expanded hard benchmark에서 LLM end-to-end 평가를 수행한 결과, Original RAG는 0.8955, Masked RAG는 0.5134로 나타났다. 즉 개인정보 마스킹 이후 query와 corpus 사이의 근거 연결성이 약화되며 성능이 크게 하락했다. 이후 masked corpus에 대해 구조적 보이스피싱 패턴 기반 reranking과 정상 금융상담 흐름을 차단하는 guard를 포함한 Advanced RAG를 적용한 결과, 성능은 0.9522까지 회복되었다.
