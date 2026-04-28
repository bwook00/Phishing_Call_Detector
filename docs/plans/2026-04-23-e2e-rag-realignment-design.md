# E2E RAG Realignment Design

## Goal
Retrieval-threshold에서만 보이던 original/masked gap을 **LLM이 최종 yes/no를 내리는 end-to-end RAG**에서도 재현한다. 이번 iteration의 목표값은 사용자가 직전에 집착한 retrieval artifact를 기준 삼아, **original >= 0.80, masked <= 0.60**의 binary accuracy band를 우선 목표로 둔다.

## Current diagnosis
- 현재 코드의 `build_prompt()`는 similarity/evidence 두 모드만 제공하고, 둘 다 query 자체의 사기성 또는 retrieval 분위기에 크게 흔들린다.
- `docs/plans/2026-04-19-binary-benchmark-results.md` 기준으로 retrieval-threshold는 `0.8209 / 0.5373`을 달성했지만, LLM judge는 `0.7015 / 0.6567` 또는 `0.9701 / 0.9403`으로 gap이 충분히 안 났다.
- 따라서 다음 실험은 judge를 더 똑똑하게 만드는 것이 아니라, **judge가 retrieval mismatch를 무시하지 못하게 하는 입력 구조**를 만드는 데 초점을 둔다.

## Options considered

### Option A — Retrieval-gated E2E (recommended)
LLM prompt를 query-only 분류기에서 빼내고, **retrieved context에 실제로 어떤 anchor/action이 있는지 명시적으로 비교**하게 만든다. `top_k`, prompt mode, and gating rules를 바꿔 original에서는 evidence alignment가 살아 있고 masked에서는 깨지도록 유도한다.

**Pros**
- 기존 데이터와 파이프라인을 최대한 재사용한다.
- iteration cost가 낮고 빠르다.
- retrieval gap이 e2e에 반영되는지 직접 검증할 수 있다.

**Cons**
- prompt-only tuning이어서 또 실패할 수 있다.
- 잘못 설계하면 retrieval-threshold의 다른 이름이 될 수 있다.

### Option B — Two-stage structured judge
1차로 query에서 scam anchor / legitimate anchor를 추출하고, 2차로 retrieval context에서 그 anchor의 support 여부를 LLM이 판단한다. 최종 yes/no는 support가 있을 때만 가능하게 만든다.

**Pros**
- query leakage를 구조적으로 통제하기 쉽다.
- failure analysis가 쉽다.

**Cons**
- 구현량이 늘고, 사실상 prompt pipeline redesign이다.
- stage 간 결합이 강해져 brittle할 수 있다.

### Option C — New data generation first
bank_call/voicephishing QA를 다시 만들어 retrieval gap 자체를 더 크게 만든 다음, e2e judge는 최소 수정만 한다.

**Pros**
- 근본 원인(데이터)을 직접 건드린다.
- 성공 시 가장 설득력 있는 방향이다.

**Cons**
- API cost와 시간이 증가한다.
- inference-side 문제인지 data-side 문제인지 분리가 어려워진다.

## Chosen design
이번 cycle은 **Option A -> Option B -> Option C** 순서로 간다.

1. 먼저 existing binary dataset(`data/reinforced_v5_binary_qa_67.csv`)과 corpus를 유지한다.
2. `naive_bm25_rag.py`에 retrieval-gated prompt mode(s)를 추가한다.
3. same dataset에서 top-k / prompt-mode / model combinations를 빠르게 sweep한다.
4. e2e metric이 target band에 도달하면 그 구성을 canonical e2e candidate로 채택한다.
5. 도달하지 못하면 structured judge(Option B)로 확장한다.
6. 그래도 실패하면 그때 dataset regeneration(Option C)으로 넘어간다.

## Key design details
- Query는 **raw STT transcript 그대로 유지**한다.
- E2E success metric은 **binary accuracy by source type**이며, primary comparison은 original vs masked pair다.
- Judge prompt는 query-only intuition을 금지하고, retrieval context의 구체적 support / contradiction / absence를 보게 만든다.
- Retrieval side에서는 이미 검증된 `realistic` regime을 기본으로 쓰되, `top_k=1/2/3`를 비교해 masked degradation을 가장 크게 반영하는 구성을 찾는다.
- 필요시 LLM 입력에 query/retrieval에서 추출한 anchor summary를 함께 넣어 judge가 표면 분위기 대신 matching evidence를 보게 한다.

## Verification
- Unit tests: new prompt mode(s), anchor summary formatting, CLI arg parsing.
- Smoke evaluation: dry-run prompt generation.
- Live evaluation: original/masked on binary 67-row set with at least one OpenAI model.
- Success: original >= 0.80 and masked <= 0.60 on the same e2e run.
