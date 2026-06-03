---
theme: default
title: 보이스피싱 탐지를 위한 개인정보 마스킹 환경의 RAG 시스템 설계
info: |
  Graduation project final presentation slides.
class: text-slate-900
fonts:
  sans: Pretendard, Noto Sans KR, Inter
  mono: JetBrains Mono
transition: slide-left
mdc: true
---

# 보이스피싱 탐지를 위한<br/>개인정보 마스킹 환경의<br/>RAG 시스템 설계

<div class="mt-8 text-xl text-slate-600">
김병욱 · 경희대학교 전자공학과<br/>
졸업프로젝트 최종 발표
</div>

<div class="absolute bottom-10 left-14 text-sm text-slate-500">
Voicephishing Detection · Privacy Masking · Retrieval-Augmented Generation
</div>

---

# Motivation

<div class="grid grid-cols-[0.95fr_1.05fr] gap-8 mt-8 items-center">
<div class="card accent-blue hack-card">
  <div class="eyebrow">Previous Prototype</div>
  <h2>Voice Phishing<br/>MCP Server</h2>
  <p>Claude Code Hackathon에서 보이스피싱 탐지 MCP server prototype을 만들었다.</p>
</div>
<div>
  <div class="big-quote">
  작동하는 탐지 시스템을 만든 뒤,<br/>하나의 현실적인 질문이 남았다.
  </div>
  <div class="question-card mt-8">
    “민감한 통화 transcript를 다룰 때,<br/>그래도 개인정보 마스킹을 적용해야 할까?”
  </div>
  <div class="mt-6 text-slate-600 text-xl leading-relaxed">
  이 프로젝트는 그 질문에서 출발해, 마스킹이 RAG 기반 보이스피싱 탐지 성능에 미치는 영향을 실험적으로 확인했다.
  </div>
</div>
</div>

---
layout: center
---

# 핵심 질문

<div class="big-quote mt-8">
개인정보를 마스킹해도<br/>
RAG 기반 보이스피싱 탐지 성능을 유지할 수 있을까?
</div>

<div class="mt-8 grid grid-cols-3 gap-4 text-center">
  <div class="card"><div class="eyebrow">Problem</div><b>Masking</b><br/>식별 단서 제거</div>
  <div class="card"><div class="eyebrow">Impact</div><b>Retrieval</b><br/>검색 근거 약화</div>
  <div class="card"><div class="eyebrow">Solution</div><b>Advanced RAG</b><br/>구조적 패턴 활용</div>
</div>

---

# 연구 범위

<div class="mt-6 scope-flow">
  <div class="scope-step muted">
    <div class="scope-icon">☎</div>
    <b>통화 음성</b>
    <span>raw call audio</span>
  </div>
  <div class="scope-arrow">→</div>
  <div class="scope-step muted dashed">
    <div class="scope-icon">STT</div>
    <b>음성 인식</b>
    <span>assumed</span>
  </div>
  <div class="scope-arrow">→</div>
  <div class="scope-step">
    <div class="scope-icon">TXT</div>
    <b>통화 transcript</b>
    <span>project input</span>
  </div>
  <div class="scope-arrow">→</div>
  <div class="scope-step active">
    <div class="scope-icon">RAG</div>
    <b>보이스피싱 탐지</b>
    <span>yes / no</span>
  </div>
</div>

<div class="grid grid-cols-3 gap-4 mt-7">
  <div class="card accent-blue">
    <div class="eyebrow">Scope</div>
    STT 이후 생성된 <b>통화 transcript</b>를 입력으로 사용
  </div>
  <div class="card muted">
    <div class="eyebrow">Excluded</div>
    STT 모델 자체의 성능 평가는 실험 범위에서 제외
  </div>
  <div class="card">
    <div class="eyebrow">Focus</div>
    개인정보 마스킹이 RAG 탐지 성능에 미치는 영향 분석
  </div>
</div>

<div class="mt-5 callout-blue compact-callout">
음성 처리 시스템이 아니라, <b>마스킹된 transcript 환경에서의 RAG 탐지 문제</b>에 집중했다.
</div>

---

# 왜 마스킹이 문제가 되는가?

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="card">
<div class="eyebrow">Original corpus</div>

```text
서울중앙지방검찰청 형사3부 수사관입니다.
박서연 씨 명의 신한은행 계좌가
전기통신금융사기 사건에 연루됐습니다.
사건번호는 2026형제18000입니다.
현재 주소는 서울 강서구로 조회됩니다.
```

</div>
<div class="card muted">
<div class="eyebrow">Masked corpus used in final experiment</div>

```text
uiuiufawaefiiifji 형사3부 수사관입니다.
qmqmzkkvvopaa 씨 명의 bbbqrrtuuplkz 계좌가
전기통신금융사기 사건에 연루됐습니다.
사건번호는 xxyyqqppmmrrt입니다.
현재 주소는 aaeiioouuzzxx로 조회됩니다.
```

</div>
</div>

<div class="mt-5 grid grid-cols-3 gap-4">
  <div class="mask-step"><b>1. Regex masking</b><span>이름·은행명·주소 등을 placeholder로 치환</span></div>
  <div class="mask-arrow">→</div>
  <div class="mask-step strong"><b>2. Strong masking</b><span>[이름] 같은 의미 있는 토큰도 random-like string으로 치환</span></div>
</div>

<div class="mt-5 callout-red">
최종 실험에서는 <b>[이름]</b> 같은 친절한 placeholder가 아니라, 의미 없는 고정 토큰으로 바꿔 검색 연결 단서를 더 강하게 제거했다.
</div>

---

# 실험 데이터 예시: Voicephishing

<div class="grid grid-cols-[1.25fr_0.75fr] gap-6 mt-4">
<div class="transcript">
<div class="eyebrow mb-3">Positive sample</div>
<p><b>고객센터:</b> 금융보호지원센터 이상거래 확인팀입니다.</p>
<p><b>고객센터:</b> 등록된 성함이 김하늘 씨 맞으신가요?</p>
<p><b>고객센터:</b> 국민은행과 카카오뱅크에 보안 점검 이력이 남아 있습니다.</p>
<p><b>피해자:</b> 제가 한 건 아니에요. 갑자기 왜 이런 확인을 하시죠?</p>
<p><b>고객센터:</b> 전용 페이지로 접속해 보호 모듈을 설치해 주세요.</p>
<p><b>고객센터:</b> 설치 후 표시되는 6자리 확인번호를 입력해 주시면 계정 보호가 완료됩니다.</p>
</div>
<div class="space-y-3">
  <div class="tag-red">전용 페이지 접속</div>
  <div class="tag-red">보호 모듈 설치</div>
  <div class="tag-red">인증번호 입력 요구</div>
  <div class="tag-red">이상거래/보호 절차 명목</div>
</div>
</div>

<div class="mt-4 text-slate-600">
겉으로는 금융 보안 안내처럼 보이지만, 실제로는 링크·앱 설치·인증번호 입력을 유도한다.
</div>

---

# 실험 데이터 예시: Hard Negative

<div class="grid grid-cols-[1.25fr_0.75fr] gap-6 mt-4">
<div class="transcript safe">
<div class="eyebrow mb-3">Bank call hard negative</div>
<p><b>상담원:</b> 최근 비정상 접속 시도가 확인되어 보호성 제한 상태입니다.</p>
<p><b>고객:</b> 어떤 확인을 하면 되나요?</p>
<p><b>상담원:</b> 공식 앱의 알림센터에서 상태를 직접 확인해 주세요.</p>
<p><b>상담원:</b> 인증번호는 절대 말씀해 주실 필요 없습니다.</p>
<p><b>상담원:</b> 대표번호로 다시 걸어 주시면 부서 확인 후 안내드릴 수 있습니다.</p>
<p><b>상담원:</b> 필요 시 가까운 영업점 방문으로 전환하시면 됩니다.</p>
</div>
<div class="space-y-3">
  <div class="tag-green">공식 앱 직접 확인</div>
  <div class="tag-green">인증번호 공유 금지</div>
  <div class="tag-green">대표번호 재연락 가능</div>
  <div class="tag-green">영업점 방문 안내</div>
</div>
</div>

<div class="mt-4 text-slate-600">
금융·보안 표현은 비슷하지만, 사기 유도 행동이 없기 때문에 hard negative로 사용했다.
</div>

---

# Dataset Design

<div class="grid grid-cols-3 gap-5 mt-8">
  <div class="metric-card">
    <div class="metric">1,000</div>
    <div class="label">augmented hard benchmark</div>
  </div>
  <div class="metric-card red">
    <div class="metric">500</div>
    <div class="label">voicephishing positive</div>
  </div>
  <div class="metric-card green">
    <div class="metric">500</div>
    <div class="label">bank call hard negative</div>
  </div>
</div>

<div class="mt-8 callout-blue">
Irrelevant sample은 너무 쉽게 no로 분류되는 경우가 많아 최종 주요 비교에서는 제외했다.
</div>

<div class="mt-6 grid grid-cols-2 gap-4">
  <div class="card muted"><b>Easy negative</b><br/>일상 대화, 날씨, 음식 주문 → 너무 쉽게 no</div>
  <div class="card accent-blue"><b>Hard negative</b><br/>정상 금융 보안 안내 → 표현은 유사하지만 사기 행동은 없음</div>
</div>

---

# 비교한 세 가지 Pipeline

<div class="pipeline-compare mt-4">
  <div class="pipe-row original">
    <div class="pipe-title">
      <span>1</span> Original Naive RAG
    </div>
    <div class="pipe-flow">
      <div class="pipe-node">Original corpus<br/><small>개인정보 유지</small></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node">BM25 Retriever<br/><small>표면 단서 매칭</small></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node">Score / LLM<br/><small>yes · no</small></div>
    </div>
  </div>

  <div class="pipe-row masked">
    <div class="pipe-title">
      <span>2</span> Masked Naive RAG
    </div>
    <div class="pipe-flow">
      <div class="pipe-node">Masked corpus<br/><small>이름·기관명 제거</small></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node weak">BM25 Retriever<br/><small>검색 단서 약화</small></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node weak">Lower evidence<br/><small>성능 하락 예상</small></div>
    </div>
  </div>

  <div class="pipe-row advanced">
    <div class="pipe-title">
      <span>3</span> Masked Advanced RAG
    </div>
    <div class="pipe-flow">
      <div class="pipe-node">Masked corpus<br/><small>개인정보 없음</small></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node strong">Pattern Rerank<br/><small>사기 흐름·행동 신호</small></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-node strong">Guarded Decision<br/><small>정상 금융상담 구분</small></div>
    </div>
  </div>
</div>

<div class="mt-4 text-center text-lg font-semibold text-blue-700">
같은 benchmark에서 <b>Original → Masked 하락</b>과 <b>Advanced 회복</b>을 비교
</div>

---

# Two Evaluation Tracks

<div class="eval-grid mt-6">
  <div class="eval-card light">
    <div class="eyebrow">Track A · Retrieval-only</div>
    <div class="eval-flow">
      <div>Transcript</div><span>↓</span>
      <div>Retriever</div><span>↓</span>
      <div>Similarity / BM25 score</div><span>↓</span>
      <div>Threshold</div><span>↓</span>
      <div class="decision">yes / no</div>
    </div>
    <div class="eval-note">LLM 없이 빠른 1차 탐지 가능성 확인</div>
  </div>

  <div class="eval-card e2e">
    <div class="eyebrow">Track B · End-to-End RAG</div>
    <div class="eval-flow">
      <div>Transcript</div><span>↓</span>
      <div>Retriever</div><span>↓</span>
      <div>Evidence Filter</div><span>↓</span>
      <div>LLM</div><span>↓</span>
      <div class="decision">yes / no</div>
    </div>
    <div class="eval-note">실제 RAG pipeline 기준 최종 판단 평가</div>
  </div>
</div>

<div class="mt-5 callout-blue">
두 track을 분리해 <b>검색 단계의 영향</b>과 <b>LLM 포함 최종 성능</b>을 각각 확인했다.
</div>

---

# 왜 Retrieval-only도 중요한가?

<div class="grid grid-cols-[0.95fr_1.05fr] gap-8 mt-6 items-center">
<div class="reason-list">
  <div class="reason-item"><b>Cost</b><span>매 통화마다 LLM API 호출 비용 발생</span></div>
  <div class="reason-item"><b>Latency</b><span>통화 중 경고에는 즉시성 필요</span></div>
  <div class="reason-item"><b>Battery</b><span>온디바이스 LLM은 연산·배터리 부담</span></div>
  <div class="reason-item"><b>Privacy</b><span>transcript 외부 전송 부담</span></div>
</div>
<div class="retrieval-purpose">
  <div class="big-number">LLM 없이도?</div>
  <div class="purpose-grid mt-6">
    <div><b>Input</b><span>통화 transcript</span></div>
    <div><b>Signal</b><span>BM25 / similarity score</span></div>
    <div><b>Rule</b><span>threshold 기반 yes/no</span></div>
  </div>
  <div class="mt-6 callout-blue">
    Retrieval-only는 <b>경량 탐지 가능성</b>과 <b>마스킹이 검색 단계에 미치는 영향</b>을 동시에 보여준다.
  </div>
</div>
</div>

---

# Advanced RAG: 핵심 아이디어

<div class="big-quote mt-2">개인정보가 사라져도, 사기 행위의 구조는 남아 있다.</div>

<div class="advanced-flow mt-6">
  <div class="adv-node muted">Masked transcript<br/><small>식별 단서 약화</small></div>
  <div class="pipe-arrow">→</div>
  <div class="adv-node">Pattern extraction<br/><small>사칭·압박·행동 유도</small></div>
  <div class="pipe-arrow">→</div>
  <div class="adv-node">Reranking / evidence<br/><small>구조적 근거 강화</small></div>
  <div class="pipe-arrow">→</div>
  <div class="adv-node strong">Guarded decision<br/><small>정상 금융상담과 구분</small></div>
</div>

<div class="grid grid-cols-2 gap-6 mt-7">
<div class="card muted compact-list">
<div class="eyebrow">Masked Naive RAG</div>
<ul>
<li>이름·기관명·계좌번호 검색 단서 약화</li>
<li>query-context 연결 근거 부족</li>
<li>단순 score 기준에서 positive recall 하락</li>
</ul>
</div>
<div class="card accent-blue compact-list">
<div class="eyebrow">Masked Advanced RAG</div>
<div class="signal-grid">
  <span>기관 사칭</span><span>이상거래 명목</span>
  <span>링크·앱 설치</span><span>인증번호 요구</span>
  <span>송금 유도</span><span>정상상담 guard</span>
</div>
</div>
</div>

---

# Retrieval-based Result

<div class="grid grid-cols-[0.95fr_1.05fr] gap-6 mt-5 items-center">
<div>

| Pipeline | Accuracy |
|---|---:|
| Original Naive RAG | **0.8210** |
| Masked Naive RAG | **0.5410** |
| Masked Advanced RAG | **0.9110** |

<div class="mt-5 text-slate-600">
LLM 없이 retrieval score와 threshold만으로 평가했다.
</div>
</div>
<div class="space-y-5">
  <div class="result-line"><span>Original</span><div class="bar" style="width:82.1%"></div><b>0.821</b></div>
  <div class="result-line"><span>Masked</span><div class="bar red" style="width:54.1%"></div><b>0.541</b></div>
  <div class="result-line"><span>Advanced</span><div class="bar green" style="width:91.1%"></div><b>0.911</b></div>
</div>
</div>

<div class="mt-5 callout-red">
마스킹 후 Naive RAG는 검색 연결 단서 손실로 크게 하락했고, Advanced RAG는 구조적 패턴 기반으로 회복했다.
</div>

---

# End-to-End RAG Result

<div class="grid grid-cols-[0.9fr_1.1fr] gap-8 mt-7 items-center">
<div>

| Pipeline | Accuracy |
|---|---:|
| Original RAG | **0.8940** |
| Masked RAG | **0.5130** |
| Masked Advanced RAG | **0.9530** |

</div>
<div class="space-y-4">
  <div class="result-line"><span>Original</span><div class="bar" style="width:89.4%"></div><b>0.894</b></div>
  <div class="result-line"><span>Masked</span><div class="bar red" style="width:51.3%"></div><b>0.513</b></div>
  <div class="result-line"><span>Advanced</span><div class="bar green" style="width:95.3%"></div><b>0.953</b></div>
</div>
</div>

<div class="mt-8 callout-blue">
LLM 최종 판단까지 포함해도 동일한 경향이 나타났다: <b>Masked Naive 하락 → Advanced RAG 회복</b>.
</div>

---

# Sanity Check

<div class="grid grid-cols-[1fr_1fr] gap-6 mt-5">
<div class="space-y-4">
  <div class="check-card">Label balance: voicephishing 500 / bank_call 500</div>
  <div class="check-card">Transcript 내 명시적 label leakage 없음</div>
  <div class="check-card">동일 source sample 직접 retrieval 제외</div>
  <div class="check-card">대화 turn 수 중앙값 유사</div>
  <div class="check-card">bank_call도 금융/보안 표현 포함</div>
</div>
<div class="chart-box">
<img src="./assets/length_token_grouped.svg" />
</div>
</div>

<div class="mt-5 text-slate-600">
평가셋은 완전한 외부 실데이터가 아니라 seed scenario 기반 증강 benchmark이므로, 결과는 hard-negative 조건에서의 비교 evidence로 해석했다.
</div>

---

# 결론

<div class="grid grid-cols-2 gap-5 mt-8">
  <div class="conclusion-card">
    <div class="num">1</div>
    개인정보 마스킹은 RAG의 검색 연결 단서를 약화시켜 성능 저하를 만들었다.
  </div>
  <div class="conclusion-card">
    <div class="num">2</div>
    Retrieval-only 평가는 경량 탐지 가능성과 검색 단계 영향 분석에 유용했다.
  </div>
  <div class="conclusion-card">
    <div class="num">3</div>
    End-to-end RAG에서도 masked naive의 성능 하락이 확인되었다.
  </div>
  <div class="conclusion-card accent">
    <div class="num">4</div>
    Advanced RAG는 개인정보 단서 대신 보이스피싱 구조적 패턴을 활용해 masked 환경의 성능을 회복했다.
  </div>
</div>

---

# 한계 및 향후 과제

<div class="grid grid-cols-2 gap-6 mt-8">
<div class="card">
<div class="eyebrow">Limitations</div>
<ul>
<li>1000개 benchmark는 seed scenario 기반 증강 데이터</li>
<li>실제 통화 데이터 기반 검증은 추가 필요</li>
<li>보이스피싱/정상 금융 상담 유형 확장 필요</li>
</ul>
</div>
<div class="card accent-blue">
<div class="eyebrow">Future Work</div>
<ul>
<li>실제 STT noise 반영 확대</li>
<li>Advanced RAG 구성 요소별 ablation</li>
<li>실시간 탐지 threshold calibration</li>
<li>데모 UI 또는 경고 시스템 연결</li>
</ul>
</div>
</div>

---
layout: center
---

# Q&A

<div class="mt-8 text-xl text-slate-600">
GitHub: <span class="font-mono">github.com/bwook00/Phishing_Call_Detector</span>
</div>

<div class="mt-8 text-slate-500">
감사합니다.
</div>
---

# 왜 마스킹이 문제가 되는가?---

# Two Evaluation Tracks---

# 왜 Retrieval-only도 중요한가?---

# Advanced RAG: 핵심 아이디어---

# Retrieval-based Result