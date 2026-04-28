# Corpus v2 + QA 템플릿 실행 가이드 (2026-03-25)

## 1) Corpus v2 확장 템플릿
- 목표: 기존 300개 `voicephishing_corpus.csv`를 대화 길이 기준으로 자연스레 확장
- 기준:
  - short 12~15턴
  - medium 16~19턴
  - long 21~27턴
- 패턴별 보강 틀은 길이만 늘리는 것이 아니라 `확인/반박/재안내/종결` 구간을 추가
- 생성 대상은 고정:
  - [`voicephishing_corpus_v2_expansion_plan.csv`](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_v2_expansion_plan.csv)
  - 각 행은 sample 단위로 target turn range와 필요한 추가턴(min/max), 패턴 보강 블록을 제공

## 2) bank_call 템플릿 설계
- 최소 10턴 원칙 적용
- hard negative 품질을 위해 실제 은행 상담 흐름 유지
- 이상거래, 지급정지, 본인확인, 보안점검, 제한해제 등 보이스피싱과 혼동될 수 있는 신호를 의도적으로 포함
- 단, 외부 링크, 원격앱 설치, 제3자 계좌 송금, 자산 이동 유도는 금지
- 생성 큐:
  - [`bank_call_qa_template_queue.csv`](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/bank_call_qa_template_queue.csv)
- 구성 기준:
  - 대상 유형 6개 순환 배분
  - 길이 10~12 / 13~16 / 17~22 반복 분배
  - 매 샘플에 본인확인/안내/해결 흐름 명확화 필수

## 3) irrelevant 템플릿 설계
- 최소 10턴 원칙 적용
- 실제 생활 통화/안내 텍스트로 구성
- 생성 큐:
  - [`irrelevant_qa_template_queue.csv`](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/irrelevant_qa_template_queue.csv)
- 구성 기준:
  - 주제 8개 순환 배분
  - 길이 10~12 / 13~16 / 16~20 분배
  - 금융사기 신호 단어(계좌, 수사기관, 긴급 송금 등) 직접 사용 금지

## 실행 순서
- 1. `voicephishing_corpus_v2_expansion_plan.csv` 기준으로 각 샘플을 300개 재작성
- 2. 생성된 v2 voice corpus에 대해 중복/비자연어/플레이스홀더 점검
- 3. `bank_call_qa_template_queue.csv` 기반으로 `source_type=bank_call` 1,000개 생성
- 4. `irrelevant_qa_template_queue.csv` 기반으로 `source_type=irrelevant` 1,000개 생성
- 5. 모든 텍스트를 `voicephishing_qa_dataset.csv`에 병합
