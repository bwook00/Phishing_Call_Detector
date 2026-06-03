# 보이스피싱 탐지를 위한 개인정보 마스킹 환경의 RAG 시스템 설계

> 개인정보를 마스킹하면 RAG 기반 보이스피싱 탐지 성능은 떨어지는가?  
> 떨어진다면, 개인정보 단서 대신 **보이스피싱의 구조적 패턴**을 활용해 성능을 회복할 수 있는가?

본 저장소는 경희대학교 전자공학과 졸업프로젝트 **「보이스피싱 탐지를 위한 개인정보 마스킹 환경의 RAG 시스템 설계」**의 코드, 데이터, 실험 결과, 발표자료, 최종보고서를 정리한 저장소입니다.

---

## Quick Links

| 구분 | 링크 |
|---|---|
| **Live Demo** | [No-STT Live Call Simulation Demo](https://bwook00.github.io/Phishing_Call_Detector/demo/live-call-simulation.html) |
| **발표자료 PDF** | [`slides/voicephishing-rag-final-slides.pdf`](slides/voicephishing-rag-final-slides.pdf) |
| **발표 대본** | [`slides/presentation-script-ko.md`](slides/presentation-script-ko.md) |
| **최종보고서 PDF** | [`docs/final-report/voicephishing-rag-final-report.pdf`](docs/final-report/voicephishing-rag-final-report.pdf) |
| **Sanity Check Report** | [`docs/results/sanity_check_1000/sanity_check_report.md`](docs/results/sanity_check_1000/sanity_check_report.md) |
| **최종 결과 요약** | [`docs/plans/2026-05-18-e2e-1000-results.md`](docs/plans/2026-05-18-e2e-1000-results.md) |

---

## 1. 프로젝트 요약

보이스피싱 탐지 시스템은 실제 통화 transcript에 포함된 이름, 주소, 기관명, 은행명, 사건번호 등 민감한 식별 정보를 다룰 수 있습니다. 이러한 정보는 RAG 검색 단계에서는 강한 단서가 되지만, 실제 시스템에서는 개인정보 보호를 위해 마스킹하는 것이 더 안전합니다.

본 프로젝트는 다음 세 가지 조건을 비교했습니다.

1. **Original RAG**  
   개인정보가 유지된 원본 corpus 기반 Naive RAG
2. **Masked RAG**  
   개인정보/식별 단서를 강하게 마스킹한 corpus 기반 Naive RAG
3. **Masked Advanced RAG**  
   마스킹 환경에서 개인정보 단서 대신 보이스피싱의 구조적 패턴과 정상 금융상담 guard를 활용한 개선 RAG

핵심 결론은 다음과 같습니다.

- 개인정보 마스킹은 Naive RAG의 검색 연결 단서를 약화시켜 성능 하락을 만들었습니다.
- 하지만 Advanced RAG는 앱/링크 설치 요구, 인증번호 요구, 정상 절차 우회, 긴급성 압박 등 사기 구조를 활용해 masked 환경에서도 성능을 회복했습니다.
- Advanced RAG의 성능 향상은 마스킹 자체 때문이 아니라, **구조적 패턴 기반 검색/판단을 추가했기 때문**입니다.

---

## 2. Demo

### No-STT Live Call Simulation

데모 링크:

```text
https://bwook00.github.io/Phishing_Call_Detector/demo/live-call-simulation.html
```

이 데모는 실제 STT 엔진이나 마이크를 사용하지 않습니다.  
**STT 이후 transcript가 실시간으로 들어오는 상황을 가정한 simulation**입니다.

데모에서 확인할 수 있는 내용:

- 전화 통화처럼 transcript가 한 줄씩 표시됨
- 현재 발화의 `Original / Masked` preview 표시
- `Original RAG / Masked RAG / Masked Advanced RAG` 결과 비교
- 위험 신호 chip 활성화
  - 앱/링크 설치 요구
  - 인증번호 요구
  - 긴급성 압박
  - 정상 절차 우회
  - 대표번호 확인 회피
- 보이스피싱 예시는 최종 `YES`
- 정상 금융통화 hard negative 예시는 최종 `NO`

> 본 프로젝트의 범위는 음성 인식이 아니라 **transcript 기반 RAG 탐지**입니다.

---

## 3. 전체 시스템 개요

```text
통화 transcript
      ↓
개인정보 마스킹
      ↓
RAG Retrieval
      ↓
Evidence Filter / Pattern-based Rerank
      ↓
yes / no 보이스피싱 판단
```

### 비교한 pipeline

| Pipeline | 설명 |
|---|---|
| Original RAG | 개인정보가 유지된 original corpus 기반 Naive RAG |
| Masked RAG | 개인정보를 random-like token으로 치환한 masked corpus 기반 Naive RAG |
| Masked Advanced RAG | masked corpus에서 보이스피싱 구조적 패턴과 정상 금융상담 guard를 활용 |

---

## 4. 최종 Benchmark

최종 평가는 `voicephishing` positive와 `bank_call` hard negative로 구성한 1,000개 증강 benchmark에서 수행했습니다.

| Label | 역할 | 수량 |
|---|---|---:|
| `voicephishing` | positive sample | 500 |
| `bank_call` | hard negative sample | 500 |
| `irrelevant` | 최종 주요 비교에서 제외 | 0 |

`bank_call`은 정상 금융상담이지만 이상거래, 보안점검, 본인확인 같은 표현을 포함할 수 있으므로 단순 irrelevant보다 더 어려운 negative class입니다.

데이터셋:

```text
data/expanded_hard_binary_qa_1000.csv
```

---

## 5. 최종 실험 결과

### 5.1 Retrieval-threshold evaluation

LLM을 사용하지 않고 retrieval score와 threshold만으로 yes/no를 판단한 평가입니다.

| Pipeline | Accuracy | Voicephishing | Bank call |
|---|---:|---:|---:|
| Original Naive RAG | **0.8210** | 0.7040 | 0.9380 |
| Masked Naive RAG | **0.5410** | 0.1440 | 0.9380 |
| Masked Advanced RAG | **0.9110** | 0.8840 | 0.9380 |

### 5.2 End-to-end RAG evaluation

Retrieval, evidence filter, LLM yes/no 판단까지 포함한 end-to-end 평가입니다.

| Pipeline | Accuracy | Voicephishing | Bank call |
|---|---:|---:|---:|
| Original RAG | **0.8940** | 0.9000 | 0.8880 |
| Masked RAG | **0.5130** | 0.2060 | 0.8200 |
| Masked Advanced RAG | **0.9530** | 0.9440 | 0.9620 |

### 5.3 Scale stability

| Pipeline | 335 e2e | 500 e2e | 1000 e2e |
|---|---:|---:|---:|
| Original RAG | 0.8955 | 0.8920 | **0.8940** |
| Masked RAG | 0.5134 | 0.5120 | **0.5130** |
| Masked Advanced RAG | 0.9522 | 0.9520 | **0.9530** |

---

## 6. Dataset Sanity Check

교수님 피드백을 반영하여 데이터셋이 과도하게 쉬운 방식으로 구성되지 않았는지 확인했습니다.

확인한 항목:

- Label balance: `voicephishing 500 / bank_call 500`
- Transcript 내 명시적 label leakage 없음
- Cross-label exact duplicate 없음
- 동일 source sample 직접 retrieval 제외
- 대화 turn 수 중앙값 유사
- `bank_call`도 금융/보안 표현을 포함하는 hard negative로 구성

자세한 내용:

```text
docs/results/sanity_check_1000/sanity_check_report.md
```

---

## 7. 주요 파일 구조

```text
.
├── demo/
│   ├── live-call-simulation.html      # No-STT live call simulation demo
│   └── README.md
├── slides/
│   ├── voicephishing-rag-final-slides.pdf
│   ├── slides.md
│   └── presentation-script-ko.md
├── docs/
│   ├── final-report/
│   │   └── voicephishing-rag-final-report.pdf
│   └── results/sanity_check_1000/
├── data/
│   ├── expanded_hard_binary_qa_1000.csv
│   ├── expanded1000_original_naive_threshold_results.csv
│   ├── expanded1000_masked_naive_threshold_results.csv
│   ├── expanded1000_masked_advanced_rag_threshold_results.csv
│   ├── e2e1000_original_identifier_filtered_results.csv
│   ├── e2e1000_masked_identifier_filtered_results.csv
│   └── e2e1000_masked_advanced_guarded_results.csv
├── naive_bm25_rag.py
├── qa_masking.py
├── strong_masking.py
├── analyze_dataset_sanity.py
└── make_sanity_svgs.py
```

---

## 8. Reproduce

### 8.1 Install dependencies

```bash
pip install -r requirements.txt
```

### 8.2 Run tests

```bash
python3 -m pytest
```

Current verification snapshot:

```text
74 passed
```

### 8.3 Reproduce retrieval-threshold results

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

### 8.4 Run dataset sanity check

```bash
python3 analyze_dataset_sanity.py
python3 make_sanity_svgs.py
```

Outputs:

```text
docs/results/sanity_check_1000/
```

---

## 9. Notes and Limitations

- 본 프로젝트는 STT 모델을 평가하지 않습니다. 입력은 STT 이후 생성된 transcript라고 가정합니다.
- Demo는 deterministic, precomputed simulation이며 production live detector가 아닙니다.
- 1,000개 benchmark는 seed scenario 기반 증강 hard-negative benchmark입니다. 완전히 독립적인 실제 통화 1,000개를 의미하지는 않습니다.
- OpenAI API key는 end-to-end LLM batch evaluation을 새로 재실행할 때만 필요합니다. 최종 merged e2e 결과 CSV는 저장소에 포함되어 있습니다.

---

## 10. Author

김병욱  
경희대학교 전자공학과  
Graduation Project, 2026
