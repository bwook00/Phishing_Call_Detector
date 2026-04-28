# QA Generation Prompts

## 목적
QA 데이터셋 3,000개 생성 시 사용할 source별 production prompt를 고정한다.

## 1. Voicephishing Prompt
```text
당신은 한국어 보이스피싱 탐지용 QA 데이터의 positive sample을 생성하는 역할이다.

[목표]
주어진 패턴의 핵심 사기 구조를 유지하면서도, 기존 예시와 문장/세부 맥락/전개가 충분히 다른 새로운 시나리오 1개를 작성하라.

[입력]
pattern_name: {pattern_name}
seed_text: {seed_text}
reference_examples: {reference_examples}
target_length: {short|medium|long}
target_style: {formal|consultative|colloquial}
medium_type: {call|sms|messenger}

[반드시 유지할 것]
- 해당 pattern의 핵심 유도 구조
- 정보 노출 흐름과 설득 논리
- 최종 피해 유발 목적

[반드시 바꿀 것]
- 인명
- 기관 세부
- 장소
- 사건 디테일
- 금액
- 표현 방식
- 세부 대화 전개

[품질 기준]
- 한국에서 실제로 있을 법한 통화/문자처럼 자연스러울 것
- 한 샘플 안에서 주 패턴이 명확할 것
- reference_examples와 문장 수준에서 충분히 다를 것
- 너무 짧거나 지나치게 극적이지 않을 것
- placeholder, 반복 filler, 해설 문장을 넣지 말 것

[금지]
- 기존 예시 문장 복사
- 두 개 이상의 패턴 혼합
- 비현실적인 협박 또는 과장된 반응
- 설명, 요약, 라벨, 마크다운 출력

[출력]
시나리오 본문만 출력하라.
```

## 2. Bank Call Prompt
```text
당신은 한국의 실제 은행 상담/안내 상황을 반영한 QA 데이터의 hard negative sample을 생성하는 역할이다.

[목표]
금융기관 맥락은 분명하지만, 보이스피싱으로 판단하면 안 되는 자연스러운 시나리오 1개를 작성하라.

[입력]
scenario_type: {card_reissue|loan_inquiry|transfer_check|fraud_report|limit_release|product_info}
target_length: {short|medium|long}
target_style: {formal|consultative|colloquial}
medium_type: {call|sms|chat}

[반드시 포함할 것]
- 실제 은행 업무 맥락
- 상담 목적이 분명한 절차
- 정상적인 본인확인 또는 안내 과정
- 자연스러운 종료 또는 해결 흐름

[품질 기준]
- 실제 콜센터/상담 창구처럼 자연스러울 것
- 금융 용어와 은행 업무 표현은 사용할 수 있음
- 은행 관련 텍스트이되 사기적 유도는 없어야 함
- placeholder, 반복 filler, 해설 문장을 넣지 말 것

[금지]
- 제3자 계좌 송금 요구
- 앱 설치, 원격제어, 외부 링크 접속 강요
- 수사기관 사칭, 사건번호 압박, 가족 사칭
- 자산 보호 명목의 자금 이동 유도
- 과도한 긴급성 조성

[출력]
시나리오 본문만 출력하라.
```

## 3. Irrelevant Prompt
```text
당신은 보이스피싱과 무관한 한국어 실생활 QA 데이터의 negative sample을 생성하는 역할이다.

[목표]
실제 생활에서 흔히 접할 수 있는 통화/문자/안내 텍스트 1개를 자연스럽게 작성하라.

[입력]
topic: {delivery|hospital|school|reservation|apartment|telecom|schedule|customer_service}
target_length: {short|medium|long}
medium_type: {call|sms|notice|chat}

[품질 기준]
- 현실적인 목적과 맥락이 분명할 것
- 생활 텍스트처럼 자연스러울 것
- 너무 짧거나 너무 건조하지 않을 것
- placeholder, 반복 filler, 해설 문장을 넣지 말 것

[금지]
- 계좌이체 압박
- 기관 사칭
- 사건번호/수사 언급
- 원격제어/앱 설치 유도
- 가족 사칭 또는 긴급 송금 요구
- 금융사기와 직접 혼동될 수 있는 핵심 신호

[출력]
시나리오 본문만 출력하라.
```

## 운영 규칙
- `voicephishing`는 기존 corpus를 직접 복제하지 않고 `seed + pattern logic` 기준으로 생성한다.
- `bank_call`은 실제 은행 업무 유형을 먼저 분배한 뒤 생성한다.
- `irrelevant`는 생활 주제를 고르게 분배한다.
- 대량 생성 전에는 각 source에서 10~20개를 먼저 생성해 품질을 확인한다.
- 생성 후에는 중복 표현, 조사 오류, placeholder, 라벨 충돌 여부를 점검한다.
