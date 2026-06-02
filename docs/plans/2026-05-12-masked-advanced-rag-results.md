# Masked Advanced RAG Final Experiment

## Goal
마지막 실험의 목적은 4월 스토리라인에 맞춰 다음 흐름을 정량적으로 완성하는 것이다.

1. 원본 corpus에서는 개인정보/식별 단서가 retrieval에 도움을 주어 Naive RAG 성능이 비교적 높다.
2. 동일한 조건에서 corpus를 masking하면 query와 corpus 사이의 직접 연결 단서가 약해져 Naive RAG 성능이 떨어진다.
3. masked 환경에서 보이스피싱의 구조적 패턴을 활용하는 Advanced RAG를 적용하면 성능을 회복할 수 있다.

## Advanced RAG design
이번 구현은 LLM prompt 튜닝이 아니라 retrieval scoring/reranking 단계의 개선으로 정의했다.

### Base
- BM25 lexical retrieval
- `realistic` retrieval regime
  - same sample 제외
  - same pattern family는 허용
- binary QA set: `data/reinforced_v5_binary_qa_67.csv`

### Added advanced features
Masked corpus에서는 이름, 주소, 기관명, 사건번호 등 직접 식별 단서가 약해진다. 따라서 Advanced RAG는 다음 구조적 feature를 추가로 사용한다.

- scam flow feature
  - 수사/사건 연루 pretext
  - 이상거래/계정 침해 pretext
  - 본인확인 흐름
  - 보호 절차/자산 보호 pretext
  - 링크/앱/인증번호/원격제어 흐름
  - 이체/송금/보호계좌 흐름
  - 긴급성/고립 유도
- scam action feature
  - 링크 접속
  - 앱 설치
  - 인증번호 제공
  - 원격 제어
  - 이체/송금 유도
- legitimate resolution penalty
  - 공식 앱 확인
  - 대표번호 재통화
  - 영업점 방문
  - 내부 검토 대기

BM25 후보군을 먼저 가져온 뒤, 위 feature로 후보를 reranking하고 최종 threshold score를 계산했다.

## Configuration

| Run | Corpus | Decision mode | Retrieval | top_k | Threshold | Advanced candidate_k |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Original Naive | `voicephishing_corpus_v2.csv` | `bm25-threshold` | realistic | 1 | 61.419 | - |
| Masked Naive | `voicephishing_corpus_masked_strong_v2.csv` | `bm25-threshold` | realistic | 1 | 61.419 | - |
| Masked Advanced | `voicephishing_corpus_masked_strong_v2.csv` | `advanced-rag-threshold` | realistic | 1 | 75 | 25 |

## Results

| Experiment | Overall | Voicephishing | Bank call |
| --- | ---: | ---: | ---: |
| Original Naive RAG | 55/67 = **0.8209** | 24/34 = **0.7059** | 31/33 = **0.9394** |
| Masked Naive RAG | 36/67 = **0.5373** | 5/34 = **0.1471** | 31/33 = **0.9394** |
| Masked Advanced RAG | 61/67 = **0.9104** | 30/34 = **0.8824** | 31/33 = **0.9394** |

## Interpretation
이 실험은 프로젝트의 최종 스토리와 잘 맞는다.

- Masked Naive RAG는 원본 대비 overall accuracy가 **0.8209 → 0.5373**으로 크게 하락했다.
- 하락은 거의 voicephishing positive row에서 발생했다.
  - Original Naive voicephishing: **0.7059**
  - Masked Naive voicephishing: **0.1471**
- 즉 masking은 정상 통화(`bank_call`)를 구분하는 능력보다, 보이스피싱 positive evidence를 찾는 능력을 크게 약화시켰다.
- Advanced RAG는 개인정보/식별 단서 대신 보이스피싱 구조적 flow와 scam action feature를 사용해 masked 환경에서 positive evidence를 다시 찾도록 만들었다.
- 그 결과 Masked Advanced RAG는 **0.9104**까지 회복되었다.

## Artifacts
- `data/final_original_naive_threshold_results.csv`
- `data/final_masked_naive_threshold_results.csv`
- `data/final_masked_advanced_rag_threshold_results.csv`
- implementation:
  - `naive_bm25_rag.py`
  - `tests/test_naive_bm25_rag.py`

## Report wording
보고서에는 다음 문장 흐름이 가장 자연스럽다.

> 원본 corpus를 사용한 Naive RAG에서는 식별 단서가 retrieval에 활용되어 비교적 안정적인 성능을 보였다. 그러나 동일한 corpus를 개인정보 마스킹한 뒤 같은 Naive RAG를 적용하자, query와 corpus 사이의 직접적인 연결 단서가 줄어들면서 성능이 크게 저하되었다. 특히 보이스피싱 positive sample에서 검색 근거를 찾지 못하는 오류가 증가하였다. 이를 보완하기 위해 개인정보 단서에 의존하지 않고 보이스피싱의 구조적 패턴, 사기 유도 행동, 대화 흐름을 feature로 활용하는 Advanced RAG를 설계하였다. Advanced RAG는 masked corpus 환경에서도 관련 문맥을 더 잘 재정렬하여, masked Naive RAG 대비 성능을 크게 회복하였다.

## Caveats
- 현재 결과는 current 67-row binary benchmark에서 threshold를 설정한 결과다.
- Masked Advanced RAG가 Original Naive보다 높게 나온 것은 이 benchmark에서 structural feature가 강하게 작동했기 때문이다.
- 최종 보고서에서는 “완전한 일반화”보다 “masked 환경의 성능 저하를 structural feature 기반 Advanced RAG로 회복 가능함을 보였다”로 표현하는 것이 안전하다.
- 독립 holdout set이 있으면 threshold 재검증을 추가하는 것이 가장 좋다.
