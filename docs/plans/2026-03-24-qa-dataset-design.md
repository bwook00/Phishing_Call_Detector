# Voice Phishing QA Dataset Design

## 목적
RAG 기반 보이스피싱 탐지 실험을 위해, 동일한 질문 형식에서 `yes/no` 이진 분류 성능을 평가할 수 있는 QA 데이터셋을 설계한다.

## 기본 구성
- 총 3,000개 샘플로 구성한다.
- source는 세 가지로 나눈다.
  - `voicephishing`: 보이스피싱 시나리오 1,000개
  - `bank_call`: 실제 은행 통화 시나리오 1,000개
  - `irrelevant`: 맥락과 무관한 일반 텍스트 1,000개
- 최종 정답 라벨은 `yes/no` 이진 분류로 통일한다.
  - `voicephishing` -> `yes`
  - `bank_call` -> `no`
  - `irrelevant` -> `no`

## 질문 형식
- 모든 샘플에 동일한 질문을 사용한다.
- 고정 질문:
  - `이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.`
- 질문을 고정하는 이유는 prompt variation을 줄이고, 원본 corpus와 masked corpus 간 비교를 단순하게 유지하기 위함이다.

## 왜 3-way source인가
- `voicephishing`은 positive sample이다.
- `bank_call`은 금융 맥락은 유사하지만 사기가 아닌 hard negative이다.
- `irrelevant`는 보이스피싱 맥락과 무관한 easy negative이다.
- 따라서 전체 accuracy뿐 아니라, 어떤 종류의 `no`에서 오류가 나는지도 분리해서 볼 수 있다.

## 데이터 스키마
```csv
qa_id,source_type,source_sample_id,question,scenario_text,ground_truth
```

## 생성 원칙
- `voicephishing`은 기존 corpus 및 masked corpus와 정합적으로 연결되도록 sample id를 유지한다.
- `bank_call`은 실제 금융기관 통화처럼 자연스럽지만 사기 유도는 없는 시나리오로 구성한다.
- `bank_call`은 hard negative 강화를 위해 이상거래, 지급정지, 본인확인, 보안점검, 제한해제 같은 혼동 신호를 포함한다.
- 단, `bank_call`에서는 외부 링크 접속, 원격제어 앱 설치, 제3자 계좌 송금, 자산 이전 요구는 끝까지 배제한다.
- `irrelevant`는 일상 대화, 공지, 배송 안내, 예약 안내, 민원 응대 등 비금융/비사기 텍스트를 포함한다.
- 각 source 내부에서도 표현 방식, 길이, 말투를 적절히 섞어 데이터 편향을 줄인다.

## 생성 운영 방식
- 실제 3,000개 QA 생성 시에는 세 source를 순차 처리하지 않고 병렬로 생성한다.
- 이 세션에서는 아래 3개 스트림을 동시에 운영하는 방식으로 진행한다.
  - `voicephishing` 1,000개
  - `bank_call` 1,000개
  - `irrelevant` 1,000개
- 이렇게 하면 생성 속도를 높일 수 있고, 한 source에 과도하게 끌려가는 표현 편향도 줄일 수 있다.
- 생성이 끝나면 세 스트림을 하나의 QA CSV로 합치고, `source_type` 기준으로 수량과 라벨 분포를 다시 검증한다.

## 평가 관점
- 전체 `yes/no` 성능을 기본 지표로 본다.
- 추가로 `bank_call`과 `irrelevant`를 분리해 false positive 양상을 확인한다.
- 원본 corpus 기반 RAG와 masked corpus 기반 RAG를 동일한 QA셋에서 비교한다.
