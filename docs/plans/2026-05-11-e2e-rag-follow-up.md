# E2E RAG Follow-up Memo

## 기준 상태
최근 체크포인트는 두 단계로 정리된다.

1. **Retrieval-threshold binary benchmark**
   - RAG/LLM judge 없이 retrieval score에 threshold를 적용해 yes/no를 평가했다.
   - Original: **0.8209**
   - Masked: **0.5373**
   - Canonical docs/artifacts:
     - `docs/plans/2026-04-19-binary-benchmark-results.md`
     - `data/reinforced_v5_binary_original_threshold_results.csv`
     - `data/reinforced_v5_binary_masked_threshold_results.csv`

2. **Identifier-filtered end-to-end RAG**
   - Naive RAG는 LLM이 query 자체의 사전지식/직관에 기대면서 original/masked gap이 잘 벌어지지 않았다.
   - 그래서 LLM 이전에 regex 기반 filter layer를 추가했다.
     - query와 retrieved result 사이에 shared identifier anchor가 없으면 context를 숨긴다.
     - 모든 retrieval context가 필터링되면 LLM에는 policy-no prompt만 보낸다.
     - shared identifier가 있는 context만 LLM 판정에 노출한다.
   - Full 67-row, `gpt-4o-mini`, `realistic`, `top_k=1`, `identifier-filtered-flow` 결과:
     - Original: **0.9104477612**
     - Masked: **0.5074626866**
   - Canonical docs/artifacts:
     - `docs/plans/2026-04-23-e2e-identifier-filtered-flow-results.md`
     - `data/full67_v6_original_identifier_filtered_flow_results.csv`
     - `data/full67_v6_masked_identifier_filtered_flow_results.csv`

## 검증된 세부 지표

### Overall / by class

| Condition | Overall | Voicephishing | Bank call |
| --- | ---: | ---: | ---: |
| Original | 61/67 = **0.9104** | 30/34 = **0.8824** | 31/33 = **0.9394** |
| Masked | 34/67 = **0.5075** | 7/34 = **0.2059** | 27/33 = **0.8182** |

### Confusion matrix

| Condition | TP yes→yes | FN yes→no | TN no→no | FP no→yes |
| --- | ---: | ---: | ---: | ---: |
| Original | 30 | 4 | 31 | 2 |
| Masked | 7 | 27 | 27 | 6 |

### Filter behavior

| Condition | Policy-no prompts | Voicephishing policy-no | Bank-call policy-no |
| --- | ---: | ---: | ---: |
| Original | 30/67 | 3/34 | 27/33 |
| Masked | 53/67 | 27/34 | 26/33 |

해석상 중요한 점은 masked voicephishing에서 `policy-no`가 크게 증가했다는 것이다. 즉, masking이 사기성 문맥 자체를 없앴다기보다 **query와 corpus evidence 사이의 identifier-level 연결고리**를 끊으면서 LLM까지 도달하는 positive evidence를 줄인 것으로 보는 것이 더 정확하다.

## Follow-up 해석

이번 결과는 “naive RAG가 잘 됐다”가 아니라, 다음과 같이 말하는 것이 안전하다.

> Naive RAG에서는 LLM이 query의 사기성 표현이나 사전지식에 기대면서 masked 조건에서도 성능이 유지되는 문제가 있었다.
> 이를 줄이기 위해 retrieval 결과를 그대로 LLM에 넣지 않고, query와 retrieval context 사이에 shared identifier anchor가 있는 경우에만 evidence로 인정하는 filter layer를 추가했다.
> 그 결과 end-to-end LLM yes/no 평가에서도 original은 0.9104로 유지되고 masked는 0.5075까지 낮아져, retrieval-threshold에서 보였던 original/masked gap이 RAG pipeline에서도 재현되었다.

## 현재 결론의 강도

### 강하게 주장 가능한 것
- Query-only 또는 raw-context-only RAG judge는 original/masked 차이를 충분히 반영하지 못했다.
- Identifier-aware evidence filtering을 넣으면 현재 binary 67-row benchmark에서 original/masked gap이 크게 벌어진다.
- Masking의 효과는 “LLM이 모르게 만드는 것”보다는 “retrieval evidence와 query 사이의 식별자 기반 연결성을 끊는 것”으로 설명하는 편이 더 정확하다.

### 조심해서 말해야 하는 것
- 이 결과는 engineered inference policy 결과이지, 순수 naive RAG 결과가 아니다.
- regex 기반 identifier filter가 현재 데이터셋에 맞춰진 면이 있으므로 독립 holdout 또는 ablation이 필요하다.
- `top_k=1`, current binary set, current corpus pair에 대한 결과이므로 범용 성능으로 과장하면 안 된다.
- masked 조건의 낮은 전체 accuracy는 특히 voicephishing positive row가 `no`로 떨어진 효과가 크다. 즉 “masked system이 전체적으로 나쁘다”보다 “masked positive evidence를 찾지 못한다”가 더 정확하다.

## 바로 이어갈 follow-up 실험

1. **Filter-only ablation**
   - `policy-no이면 no, 아니면 yes`인 deterministic baseline을 별도로 기록한다.
   - 현재 quick check:
     - Original: 58/67 = **0.8657**
     - Masked: 33/67 = **0.4925**
   - 이 baseline과 LLM 결과를 비교하면 LLM이 filter 이후에 얼마나 추가 기여했는지 설명할 수 있다.

2. **Visible-context subset 분석**
   - Filter를 통과해 실제 context가 보인 row만 따로 평가한다.
   - 현재 quick check:
     - Original visible-context subset: 34/37 = **0.9189**
     - Masked visible-context subset: 8/14 = **0.5714**
   - 이 값은 filter 이후에도 masked visible context가 완전히 신뢰롭지는 않다는 점을 보여준다.

3. **Ablation table 추가**
   - `retrieval-threshold`
   - `naive LLM judge`
   - `evidence prompt`
   - `identifier-filtered-flow`
   - `filter-only`
   를 한 표로 정리하면 논리 흐름이 가장 깔끔하다.

4. **Report wording 정리**
   - “RAG가 성공했다”보다 “RAG judge가 query-only shortcut을 쓰지 못하도록 evidence-alignment gate를 추가하자 gap이 재현되었다”로 기술한다.
   - Masking 효과는 “semantic removal”이 아니라 “evidence linkability degradation”으로 표현한다.

## 공유용 짧은 문안

지난 실험 follow-up입니다. Retrieval score threshold만 사용했을 때는 original 0.8209 / masked 0.5373까지 gap이 벌어졌지만, naive RAG에서는 LLM이 query 자체에 지나치게 의존해서 masked에서도 성능이 유지되는 문제가 있었습니다. 그래서 LLM에 retrieved context를 바로 넣지 않고, query와 retrieved result 사이에 shared identifier가 있는 경우에만 context를 통과시키는 filter layer를 추가했습니다. shared identifier가 없으면 해당 context는 숨기고, 모든 context가 필터링되면 LLM에는 no로 답하도록 하는 policy-no prompt만 전달했습니다.

이 설정으로 full 67-row binary benchmark를 다시 돌린 결과, end-to-end RAG에서도 original 0.9104 / masked 0.5075가 나왔습니다. 다만 이 결과는 naive RAG가 아니라 identifier-filtered RAG이므로, 보고서에는 “LLM judge의 query-only shortcut을 막기 위해 evidence-alignment gate를 추가했다”는 점을 명확히 적는 것이 좋겠습니다. 다음 단계로는 filter-only baseline과 ablation table을 추가해서, 실제 성능 차이가 retrieval/gate에서 오는지 LLM 판단에서 오는지 분리해보면 될 것 같습니다.
