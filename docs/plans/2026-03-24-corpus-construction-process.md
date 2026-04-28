# Voice Phishing Corpus Construction (Compact)

### 보이스피싱 패턴 추출 및 Seed Data 생성
참고:
- 공식 보이스피싱 대응 기관 자료 + 기존 금융사기 안내 자료를 바탕으로 10개 유형을 선정.
- 유형별 핵심 구조를 유지한 seed 시나리오를 구축해 증강의 기준축으로 사용.
- 참고 링크(섹션 변경분만 관리):  
  - https://www.fsc.go.kr/no010101/86250  
  - https://www.kisa.or.kr/1020601  
  - https://www.kebhana.com/cont/news/news01/1496774_115430.jsp
- 시드 산출물  
  - [data/voicephishing_pattern_scenarios_full.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_pattern_scenarios_full.csv)  
  - [data/voicephishing_pattern_scenarios.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_pattern_scenarios.csv)

결과:
- 패턴: 10개
- 시드 시나리오: 244행(샘플 포함)

### 증강 variable 선정 및 데이터 증강을 통한 Corpus 생성

variable:
- 공통: `interaction_length`, `victim_suspicion`, `pii_exposure_timing`, `urgency_level`, `ending_type`, `context_setting`, `language_style`, `noise_level`
- 패턴 핵심 보조축(최대 1~2개): 기관사칭형(위협 강도, 자산요구 방식), 가족자녀사칭형(핑계유형, 송금논리), 악성앱원격제어형(설치흐름, 기기통제수준), 기타 패턴은 유사 원칙 적용
- 길이 기준: short 12~15 / medium 16~19 / long 21~27턴
- 패턴당 분포: short 10 / medium 12 / long 8 (전체 short 100 / medium 120 / long 80)
  - `short/medium/long`은 패턴당 30개를 맞추기 위한 샘플 수 구성값이라 유지한다. 길이 구간(12~15/16~19/21~27)은 별도 기준이다.

Corpus 결과:
- [data/voicephishing_corpus_generation_plan.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_generation_plan.csv)  
- [data/voicephishing_corpus_v2.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_v2.csv)  
- [data/voicephishing_corpus.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus.csv)  

### Masked Corpus 생성
- 원본 corpus의 식별 단서를 토큰화해 마스킹 버전을 생성.
- 마스킹 대상: 이름/자녀/지인명, 주소, 은행명, 직장명, 학교명, 기관명, 앱명, 사건번호, 계좌번호, 링크, 금액.
- 토큰 예시: `[이름]`, `[자녀이름]`, `[지인명]`, `[주소]`, `[은행명]`, `[직장명]`, `[학교명]`, `[기관명]`, `[앱명]`, `[사건번호]`, `[계좌번호]`, `[링크]`, `[금액]`.

Masked 데이터 결과:
- [data/voicephishing_corpus_masked.csv](/Users/kimbwook/PycharmProjects/Phishing_Call_Detector/data/voicephishing_corpus_masked.csv)
