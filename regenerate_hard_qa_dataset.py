#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
import urllib.request
from pathlib import Path
from typing import Any


DATA_DIR = Path("data")
VOICE_CORPUS = DATA_DIR / "voicephishing_corpus_v2.csv"
OUT_PATH = DATA_DIR / "voicephishing_qa_dataset.csv"
QUESTION = "이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라."
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_PROMPT_PROFILE = "v4"
DEFAULT_DATASET_MODE = "full"

VOICE_DISTRIBUTION = {"hard": 0.65, "medium": 0.25, "easy": 0.10}
BANK_DISTRIBUTION = {"hard": 0.70, "medium": 0.20, "easy": 0.10}
IR_DISTRIBUTION = {"hard": 0.50, "medium": 0.35, "easy": 0.15}

BANK_FAMILIES = [
    "transfer_check",
    "fraud_report",
    "limit_release",
    "card_reissue",
    "loan_inquiry",
    "product_info",
]
IR_FAMILIES = [
    "delivery",
    "hospital",
    "school",
    "reservation",
    "apartment",
    "telecom",
    "schedule",
    "customer_service",
]
TONES = ["formal", "consultative", "colloquial"]
CHANNELS = ["call", "chat", "notice"]


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def difficulty_counts(total: int, distribution: dict[str, float]) -> dict[str, int]:
    order = list(distribution.keys())
    counts = {name: int(total * distribution[name]) for name in order}
    remainder = total - sum(counts.values())
    for name in order:
        if remainder <= 0:
            break
        counts[name] += 1
        remainder -= 1
    return counts


def expand_difficulties(total: int, distribution: dict[str, float]) -> list[str]:
    counts = difficulty_counts(total, distribution)
    values: list[str] = []
    for difficulty, count in counts.items():
        values.extend([difficulty] * count)
    return values


def build_voicephishing_specs(corpus_rows: list[dict[str, str]], total: int = 1000) -> list[dict[str, Any]]:
    difficulties = expand_difficulties(total, VOICE_DISTRIBUTION)
    specs = []
    for index in range(total):
        seed = corpus_rows[index % len(corpus_rows)]
        variant_index = (index // len(corpus_rows)) + 1
        specs.append(
            {
                "qa_id": f"{seed['sample_id']}-Q{variant_index:02d}",
                "source_type": "voicephishing",
                "source_sample_id": seed["sample_id"],
                "pattern_name": seed["pattern_name"],
                "difficulty": difficulties[index],
                "variant_index": variant_index,
                "seed_text": seed["scenario_text"],
                "ground_truth": "yes",
            }
        )
    return specs


def build_bank_call_specs(total: int = 1000) -> list[dict[str, Any]]:
    difficulties = expand_difficulties(total, BANK_DISTRIBUTION)
    specs = []
    for index in range(total):
        specs.append(
            {
                "qa_id": f"BC-{index + 1:04d}",
                "source_type": "bank_call",
                "source_sample_id": f"BC-{index + 1:04d}",
                "scenario_family": BANK_FAMILIES[index % len(BANK_FAMILIES)],
                "difficulty": difficulties[index],
                "tone": TONES[index % len(TONES)],
                "channel": CHANNELS[index % len(CHANNELS)],
                "ground_truth": "no",
            }
        )
    return specs


def build_irrelevant_specs(total: int = 1000) -> list[dict[str, Any]]:
    difficulties = expand_difficulties(total, IR_DISTRIBUTION)
    specs = []
    for index in range(total):
        specs.append(
            {
                "qa_id": f"IR-{index + 1:04d}",
                "source_type": "irrelevant",
                "source_sample_id": f"IR-{index + 1:04d}",
                "scenario_family": IR_FAMILIES[index % len(IR_FAMILIES)],
                "difficulty": difficulties[index],
                "tone": TONES[index % len(TONES)],
                "channel": CHANNELS[index % len(CHANNELS)],
                "ground_truth": "no",
            }
        )
    return specs


def build_generation_prompt(spec: dict[str, Any], prompt_profile: str = DEFAULT_PROMPT_PROFILE) -> str:
    source_type = spec["source_type"]
    if source_type == "voicephishing":
        if prompt_profile == "v5":
            return (
                "너는 보이스피싱 탐지용 QA 데이터 생성기다.\n"
                "목표는 원본 시드와 같은 유형의 보이스피싱 대화를 새로 다시 쓰는 것이다.\n"
                "표면 단서만 복사하지 말고 의미 구조를 유지한 채 다른 표현, 다른 전개, 다른 세부정보로 재작성하라.\n"
                "반드시 한국어 대화문만 출력하라.\n"
                "설명, 제목, JSON, 마크다운은 금지한다.\n"
                f"qa_id: {spec['qa_id']}\n"
                f"pattern_name: {spec['pattern_name']}\n"
                f"difficulty: {spec['difficulty']}\n"
                f"source_sample_id: {spec['source_sample_id']}\n"
                "규칙:\n"
                "- 보이스피싱으로 분류되어야 한다.\n"
                "- 같은 사건/패턴의 새로운 변형이어야 한다.\n"
                "- difficulty가 hard일수록 초반 6~8턴은 합법적 확인 전화처럼 보이게 작성하라.\n"
                "- difficulty가 hard일수록 초반에는 고객보호, 등록정보 대조, 이상 징후 확인, 보호 절차 같은 표현으로 시작하라.\n"
                "- difficulty가 hard일수록 질문 대상 대화만 보면 정상 상담일 수도 있겠다고 느껴지게 하라.\n"
                "- 하지만 초반 몇 턴이 너무 정상 상담처럼 마무리되지 않게 하라.\n"
                "- difficulty가 hard일수록 중반 이후에는 최소 한 번 이상 명확한 사기 실행 단서를 넣어라.\n"
                "- 명확한 사기 실행 단서는 앱 설치, 링크 접속, 인증번호 제공, 원격 제어, 이체 유도 중 하나 이상이어야 한다.\n"
                "- difficulty가 hard일수록 초반 8턴 안에 검찰, 경찰, 수사, 사건번호, 공범 같은 직접 신호는 되도록 늦춰라.\n"
                "- difficulty가 hard일수록 이름, 은행명, 주소, 부서명, 접수번호, 고객번호 같은 표면 식별 단서는 풍부하게 넣어라.\n"
                "- difficulty가 hard일수록 original retrieval이 같은 계열 문서를 잡을 수 있을 만큼 절차와 행위 흐름을 유지하라.\n"
                "- difficulty가 medium이면 정상 상담 톤과 사기 신호를 함께 섞어라.\n"
                "- difficulty가 easy일수록 사기 신호를 더 직접적으로 드러내라.\n"
                "- 12~18턴 범위로 작성하라.\n"
                "시드 대화:\n"
                f"{spec['seed_text']}\n"
            )
        return (
            "너는 보이스피싱 탐지용 QA 데이터 생성기다.\n"
            "목표는 원본 시드와 같은 유형의 보이스피싱 대화를 새로 다시 쓰는 것이다.\n"
            "표면 단서만 복사하지 말고 의미 구조를 유지한 채 다른 표현, 다른 전개, 다른 세부정보로 재작성하라.\n"
            "반드시 한국어 대화문만 출력하라.\n"
            "설명, 제목, JSON, 마크다운은 금지한다.\n"
            f"qa_id: {spec['qa_id']}\n"
            f"pattern_name: {spec['pattern_name']}\n"
            f"difficulty: {spec['difficulty']}\n"
            f"source_sample_id: {spec['source_sample_id']}\n"
            "규칙:\n"
            "- 보이스피싱으로 분류되어야 한다.\n"
            "- 같은 사건/패턴의 새로운 변형이어야 한다.\n"
            "- difficulty가 hard일수록 초반 6~8턴은 합법적 확인 전화처럼 보이게 작성하라.\n"
            "- difficulty가 hard일수록 직접적 송금/앱설치/안전계좌 표현은 뒤쪽으로 밀고, 초반에는 조회, 대조, 보호절차, 본인확인 같은 말로 시작하라.\n"
            "- difficulty가 hard일수록 사기성이 있지만 노골적이지 않은 압박, 보안 유지 요구, 등록정보 대조 흐름을 넣어라.\n"
            "- difficulty가 hard일수록 초반 8턴 안에 검찰, 경찰, 수사, 사건번호, 대포통장, 공범, 비밀유지, 공유 금지 같은 직접 신호를 되도록 쓰지 마라.\n"
            "- difficulty가 hard일수록 기관 사칭을 하더라도 초반에는 고객보호센터, 계정보호팀, 이상거래확인실처럼 애매한 표현으로 시작하라.\n"
            "- difficulty가 hard일수록 질문 대상 대화만 보면 정상 상담일 수도 있겠다고 느껴지게 작성하라.\n"
            "- difficulty가 hard일수록 이름, 은행명, 주소, 직장명, 접수번호, 부서명 같은 표면 식별 단서는 많이 넣어라.\n"
            "- difficulty가 hard일수록 초반 화자는 고객을 안심시키며 확인만 하겠다고 말하고, 중반 이후에만 통제나 지시가 강해지게 하라.\n"
            "- difficulty가 hard일수록 고객이 보기에는 정상 고객보호 전화처럼 들리지만, 뒤로 갈수록 사기성이 드러나게 하라.\n"
            "- difficulty가 hard일수록 동일 패턴의 다른 시나리오들과 헷갈릴 만큼 표현을 일반화하되, 식별 단서는 original에서만 강하게 남게 하라.\n"
            "- difficulty가 medium이면 보이스피싱 신호와 정상 상담 톤을 함께 섞어라.\n"
            "- difficulty가 easy일수록 사기 신호를 더 직접적으로 드러내라.\n"
            "- 12~18턴 범위로 작성하라.\n"
            "- 질문 대상 대화만 보고 바로 yes라고 답하기 어렵게, 초반은 최대한 애매하게 작성하라.\n"
            "시드 대화:\n"
            f"{spec['seed_text']}\n"
        )
    if source_type == "bank_call":
        if prompt_profile == "v5":
            return (
                "너는 보이스피싱 탐지용 hard negative QA 데이터 생성기다.\n"
                "한국어 은행 상담 대화만 출력하라. 설명, JSON, 제목, 마크다운은 금지한다.\n"
                f"qa_id: {spec['qa_id']}\n"
                f"scenario_family: {spec['scenario_family']}\n"
                f"difficulty: {spec['difficulty']}\n"
                f"tone: {spec['tone']}\n"
                f"channel: {spec['channel']}\n"
                "반드시 포함할 성격:\n"
                "- 계좌, 본인확인, 이상거래, 보안점검, 지급정지, 제한해제 같은 은행성 단서를 충분히 넣어라.\n"
                "- 실제 은행 상담처럼 자연스럽고 합법적이어야 한다.\n"
                "- hard일수록 자산 보호, 명의도용 의심 접수, 다계좌 점검, 비정상 접속 차단, 임시 제한, 보호 단계 같은 표현을 적극 활용하라.\n"
                "- hard일수록 고객이 불안해할 만한 상황 설명과 확인 절차를 넣되, 결과적으로는 정상 은행 상담이어야 한다.\n"
                "- hard일수록 질문 대상 대화만 보면 보이스피싱처럼 들릴 수 있어야 한다.\n"
                "- hard일수록 지금 바로 처리하지 않으면 불편이 커질 수 있다는 뉘앙스를 넣어라.\n"
                "- hard일수록 초반 6턴 안에 이 대화가 정상인지 사기인지 헷갈리게 만들어라.\n"
                "- hard일수록 접수번호, 고객번호, 부서명, 보호 단계명, 확인 코드 같은 식별 단서를 여러 개 넣어라.\n"
                "- hard일수록 수상하지만 합법적인 은행 용어를 반복해서 사용하라.\n"
                "- hard일수록 다음 실제 경로 중 하나로 정리하라: 공식 앱에서 직접 확인, 대표번호로 다시 걸기, 영업점 방문, 내부 검토 대기.\n"
                "절대 포함하지 마라:\n"
                "- 원격앱 설치\n"
                "- 링크 클릭 유도\n"
                "- 인증번호나 확인 코드를 읽게 하기\n"
                "- 제3자 계좌 송금\n"
                "- 현금 인출 후 안전계좌 이체\n"
                "- 가족/지인 연락 차단\n"
                "- 수사기관 사칭\n"
                "- 원격 제어 또는 화면 공유\n"
                "- 정답 라벨 직접 언급\n"
                "- 보이스피싱임을 암시하는 메타 설명\n"
                "difficulty가 hard일수록 보이스피싱과 혼동될 만한 은행 표현을 더 많이 넣되, 사기 전용 행동은 절대 넣지 마라.\n"
                "12~18턴 범위로 작성하라.\n"
            )
        return (
            "너는 보이스피싱 탐지용 hard negative QA 데이터 생성기다.\n"
            "한국어 은행 상담 대화만 출력하라. 설명, JSON, 제목, 마크다운은 금지한다.\n"
            f"qa_id: {spec['qa_id']}\n"
            f"scenario_family: {spec['scenario_family']}\n"
            f"difficulty: {spec['difficulty']}\n"
            f"tone: {spec['tone']}\n"
            f"channel: {spec['channel']}\n"
            "반드시 포함할 성격:\n"
            "- 계좌, 본인확인, 이상거래, 보안점검, 지급정지, 제한해제 같은 은행성 단서를 충분히 넣어라.\n"
            "- 실제 은행 상담처럼 자연스럽고 합법적이어야 한다.\n"
            "- hard일수록 다음 표현을 적극 활용하라: 자산 보호, 명의도용 의심 접수, 다계좌 점검, 비정상 접속 차단, 임시 제한, 보호 단계, 추가 인증 전 일부 기능 보류.\n"
            "- hard일수록 고객이 불안해할 만한 상황 설명과 확인 절차를 넣되, 결과적으로는 정상 은행 상담이어야 한다.\n"
            "- hard일수록 질문 대상 대화만 보면 보이스피싱처럼 들릴 수 있어야 한다.\n"
            "- hard일수록 지금 바로 처리하지 않으면 불편이 커질 수 있다는 뉘앙스를 넣어라.\n"
            "- hard일수록 여러 계좌, 보호 대상, 확인 지연, 임시 차단, 추가 확인 같은 표현을 동시에 섞어라.\n"
            "- hard일수록 초반 6턴 안에 이 대화가 정상인지 사기인지 헷갈리게 만들어라.\n"
            "- hard일수록 접수번호, 고객번호, 부서명, 보호 단계명, 확인 코드 같은 식별 단서를 여러 개 넣어라.\n"
            "- hard일수록 고객에게 당황감은 주되, 실제 행동 지시는 정상 절차 안에 머물게 하라.\n"
            "- hard일수록 수상하지만 합법적인 은행 용어를 반복해서 사용하라.\n"
            "- hard일수록 보이스피싱처럼 들릴 수 있어야 하지만, 결정적 불법 행위는 등장하지 않아야 한다.\n"
            "- hard일수록 초반부터 고객이 '이거 정상 맞나?'라고 느낄 정도의 압박감과 모호한 위험 설명을 넣어라.\n"
            "절대 포함하지 마라:\n"
            "- 원격앱 설치\n"
            "- 제3자 계좌 송금\n"
            "- 현금 인출 후 안전계좌 이체\n"
            "- 가족/지인 연락 차단\n"
            "- 수사기관 사칭\n"
            "- 정답 라벨 직접 언급\n"
            "- 보이스피싱임을 암시하는 메타 설명\n"
            "difficulty가 hard일수록 보이스피싱과 혼동될 만한 은행 표현을 더 많이 넣되, 사기 전용 행동은 절대 넣지 마라.\n"
            "12~18턴 범위로 작성하라.\n"
        )
    return (
        "너는 보이스피싱 탐지용 비관련 상담 QA 데이터 생성기다.\n"
        "한국어 콜센터/안내센터 대화만 출력하라. 설명, JSON, 제목, 마크다운은 금지한다.\n"
        f"qa_id: {spec['qa_id']}\n"
        f"scenario_family: {spec['scenario_family']}\n"
        f"difficulty: {spec['difficulty']}\n"
        f"tone: {spec['tone']}\n"
        f"channel: {spec['channel']}\n"
        "규칙:\n"
        "- 보이스피싱이 아니어야 한다.\n"
        "- 일상적이되 콜센터 문체와 운영성 표현을 유지하라.\n"
        "- 너무 쉬운 잡담은 피하라.\n"
        "- hard일수록 접수번호, 확인 절차, 예약 변경, 등록 정보 확인, 처리 보류, 추가 인증 같은 운영성 문구를 적극 활용하라.\n"
        "- hard일수록 겉보기에는 중요한 상담처럼 보이게 만들되, 실제 금융사기 신호는 넣지 마라.\n"
        "- hard일수록 질문 대상 대화만 보면 긴장감이 있어 보이게 작성하라.\n"
        "- hard일수록 보이스피싱처럼 들릴 수는 있어도, 실제로는 배송/예약/행정/고객센터 처리 범위를 벗어나지 않게 하라.\n"
        "- hard일수록 보호, 확인, 재접수, 지연, 보류 같은 단어를 써서 심리적 긴장감을 만들어라.\n"
        "- 금융사기 핵심 신호는 직접 쓰지 마라.\n"
        "- 12~18턴 범위로 작성하라.\n"
    )


def normalize_generated_dialog(text: str, max_turns: int = 18) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:max_turns])


def load_openai_api_key(dotenv_path: str | Path = ".env") -> str | None:
    env_value = os.environ.get("OPENAI_API_KEY")
    if env_value:
        return env_value
    path = Path(dotenv_path)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == "OPENAI_API_KEY":
            return value.strip().strip('"').strip("'")
    return None


def call_openai_text(prompt: str, model: str, api_key: str) -> str:
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("output_text"):
        return str(data["output_text"]).strip()
    outputs = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                outputs.append(text)
    return "\n".join(outputs).strip()


def materialize_row(spec: dict[str, Any], scenario_text: str) -> dict[str, str]:
    return {
        "qa_id": spec["qa_id"],
        "source_type": spec["source_type"],
        "source_sample_id": spec["source_sample_id"],
        "question": QUESTION,
        "scenario_text": normalize_generated_dialog(scenario_text),
        "ground_truth": spec["ground_truth"],
    }


def write_rows(path: str | Path, rows: list[dict[str, str]]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["qa_id", "source_type", "source_sample_id", "question", "scenario_text", "ground_truth"],
        )
        writer.writeheader()
        writer.writerows(rows)


def generate_rows(
    specs: list[dict[str, Any]],
    model: str,
    api_key: str,
    prompt_profile: str = DEFAULT_PROMPT_PROFILE,
    sleep_seconds: float = 0.0,
) -> list[dict[str, str]]:
    rows = []
    for index, spec in enumerate(specs, start=1):
        text = call_openai_text(build_generation_prompt(spec, prompt_profile=prompt_profile), model=model, api_key=api_key)
        rows.append(materialize_row(spec, text))
        if index % 25 == 0:
            print(json.dumps({"generated": index, "last_qa_id": spec["qa_id"]}, ensure_ascii=False))
        if sleep_seconds:
            time.sleep(sleep_seconds)
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice-count", type=int, default=1000)
    parser.add_argument("--bank-count", type=int, default=1000)
    parser.add_argument("--irrelevant-count", type=int, default=1000)
    parser.add_argument("--dataset-mode", choices=["full", "binary"], default=DEFAULT_DATASET_MODE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", default=str(OUT_PATH))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--prompt-profile", choices=["v4", "v5"], default=DEFAULT_PROMPT_PROFILE)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def build_all_specs(
    voice_count: int,
    bank_count: int,
    irrelevant_count: int,
    dataset_mode: str = DEFAULT_DATASET_MODE,
) -> list[dict[str, Any]]:
    corpus_rows = read_csv_rows(VOICE_CORPUS)
    specs = build_voicephishing_specs(corpus_rows, total=voice_count) + build_bank_call_specs(total=bank_count)
    if dataset_mode != "binary":
        specs += build_irrelevant_specs(total=irrelevant_count)
    return specs


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    specs = build_all_specs(args.voice_count, args.bank_count, args.irrelevant_count, dataset_mode=args.dataset_mode)
    if args.limit is not None:
        specs = specs[: args.limit]
    if args.dry_run:
        print(
            json.dumps(
                {
                    "count": len(specs),
                    "prompt_profile": args.prompt_profile,
                    "sample_prompt": build_generation_prompt(specs[0], prompt_profile=args.prompt_profile),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    api_key = load_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    rows = generate_rows(
        specs,
        model=args.model,
        api_key=api_key,
        prompt_profile=args.prompt_profile,
        sleep_seconds=args.sleep_seconds,
    )
    write_rows(args.output, rows)
    print(
        json.dumps(
            {"count": len(rows), "output": args.output, "model": args.model, "prompt_profile": args.prompt_profile},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
