# Corpus Generation Guide

## 목적
보이스피싱 RAG 실험용 원본 corpus를 만들 때, 패턴 수를 늘리는 것보다 각 패턴 내부 대화 구조를 충분히 다양화하기 위한 기준을 정리한다.

## 기본 방향
- 패턴은 10개로 고정한다.
- 각 패턴 내부에서 대화 길이, 피해자 반응, 정보 노출 시점, 압박 강도를 다르게 만든다.
- 표면 문장만 바꾸지 않고 상호작용 구조 자체를 바꾼다.
- 원본 corpus에는 검색 단서가 되는 식별 정보를 일부러 남긴다.

## 목표 수량
- 총 300개
- 패턴당 30개

## 공통 증강 변수
실제 생성과 관리에 필요한 변수만 남긴다.

- `interaction_length`: short / medium / long
- `victim_suspicion`: low / medium / high
- `pii_exposure_timing`: early / mid / late
- `urgency_level`: low / medium / high
- `ending_type`: comply / hesitate / abort
- `context_setting`: home / work / commute / other
- `language_style`: formal / consultative / colloquial
- `noise_level`: clean / light-disfluency

## 패턴별 핵심 변수
패턴별로는 설명력이 큰 축만 1~2개 사용한다.

- 기관사칭형: `asset_request_type`, `threat_intensity`
- 고립유도형: `movement_control`, `call_continuity_pressure`
- 가족자녀사칭형: `excuse_type`, `transfer_target_reason`
- 납치빙자AI음성형: `fear_trigger_type`, `payment_deadline`
- 대환대출사칭형: `loan_context`, `prepayment_structure`
- 선입금요구형: `fee_label`, `refund_promise_strength`
- 악성앱원격제어형: `device_control_level`, `channel_flow`
- 카드배송사칭형: `delivery_context`, `handoff_path`
- 법원등기우편사칭형: `legal_seriousness`, `link_pressure`
- 스미싱큐싱연계형: `delivery_urgency`, `requested_info_scope`

## 분포 원칙
패턴당 30개는 아래처럼 섞는다.

- length: short 10 / medium 12 / long 8
- suspicion: low 10 / medium 10 / high 10
- pii timing: early 10 / mid 10 / late 10
- urgency: low 8 / medium 12 / high 10
- ending: comply 10 / hesitate 10 / abort 10
- 전체 기준으로 length 분포는 short 100 / medium 120 / long 80으로 반영된다.

완벽한 조합 균형까지 맞출 필요는 없지만, 특정 조합만 반복되면 안 된다.

## 패턴 유지 원칙
- 각 샘플은 주 패턴이 하나여야 한다.
- 최종 요구 행동은 해당 패턴의 핵심 구조와 일치해야 한다.
- 다른 패턴의 대표 장치를 과도하게 섞지 않는다.

예시:
- 기관사칭형은 자산 확인/이전 요구가 핵심이다.
- 고립유도형은 이동 지시와 외부 연락 차단이 핵심이다.
- 가족자녀사칭형은 가족 사칭과 제3자 계좌 송금 논리가 핵심이다.

## 품질 기준
좋은 샘플은 아래 조건을 만족해야 한다.

- 주 패턴이 명확하다.
- 대화 흐름이 자연스럽다.
- 같은 패턴 내 다른 샘플과 구조적으로 다르다.
- 검색 단서가 최소 3개 이상 들어 있다.
- 한국어 실제 통화/문자 맥락에서 지나치게 부자연스럽지 않다.

아래 경우는 수정하거나 제외한다.

- 문장만 바뀌고 구조가 사실상 동일한 경우
- 대화가 너무 짧아 핵심 단서가 부족한 경우
- 여러 패턴이 동등하게 섞여 보이는 경우
- 지나치게 극적이거나 비현실적인 경우

## 다음 단계
1. 패턴별 seed scenario 작성
2. 공통 변수와 패턴별 핵심 변수 배정
3. 원본 corpus 300개 생성
4. 품질 보정
5. masked corpus 생성
