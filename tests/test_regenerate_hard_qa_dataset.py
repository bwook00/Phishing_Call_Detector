from regenerate_hard_qa_dataset import (
    DEFAULT_MODEL,
    build_all_specs,
    build_bank_call_specs,
    build_generation_prompt,
    build_irrelevant_specs,
    build_voicephishing_specs,
    difficulty_counts,
    normalize_generated_dialog,
    parse_args,
)


def test_default_model_prefers_gpt_5_4_mini():
    assert DEFAULT_MODEL == "gpt-5.4-mini"


def test_difficulty_counts_fill_total_and_keep_order():
    counts = difficulty_counts(10, {"hard": 0.5, "medium": 0.3, "easy": 0.2})

    assert counts == {"hard": 5, "medium": 3, "easy": 2}


def test_build_voicephishing_specs_reuses_corpus_ids_with_variants():
    corpus_rows = [
        {"sample_id": "P01-01", "pattern_name": "기관사칭형", "scenario_text": "seed-1"},
        {"sample_id": "P01-02", "pattern_name": "기관사칭형", "scenario_text": "seed-2"},
    ]

    specs = build_voicephishing_specs(corpus_rows, total=5)

    assert len(specs) == 5
    assert specs[0]["source_type"] == "voicephishing"
    assert specs[0]["source_sample_id"] == "P01-01"
    assert specs[2]["source_sample_id"] == "P01-01"
    assert specs[2]["variant_index"] == 2
    assert {spec["difficulty"] for spec in specs} == {"hard", "medium"}


def test_build_bank_call_specs_produces_1000_balanced_items():
    specs = build_bank_call_specs(total=12)

    assert len(specs) == 12
    assert specs[0]["qa_id"].startswith("BC-")
    assert all(spec["source_type"] == "bank_call" for spec in specs)
    assert {spec["difficulty"] for spec in specs} == {"hard", "medium", "easy"}
    assert len({spec["scenario_family"] for spec in specs}) >= 3


def test_build_irrelevant_specs_produces_1000_balanced_items():
    specs = build_irrelevant_specs(total=12)

    assert len(specs) == 12
    assert specs[0]["qa_id"].startswith("IR-")
    assert all(spec["source_type"] == "irrelevant" for spec in specs)
    assert {spec["difficulty"] for spec in specs} == {"hard", "medium", "easy"}
    assert len({spec["scenario_family"] for spec in specs}) >= 3


def test_build_generation_prompt_for_bank_call_forbids_scam_only_actions():
    spec = {
        "qa_id": "BC-0001",
        "source_type": "bank_call",
        "difficulty": "hard",
        "scenario_family": "transfer_check",
        "tone": "formal",
        "channel": "call",
    }

    prompt = build_generation_prompt(spec)

    assert "원격앱 설치" in prompt
    assert "절대 포함하지 마라" in prompt
    assert "계좌" in prompt
    assert "yes 또는 no" not in prompt
    assert "보이스피싱처럼 들릴 수 있어야" in prompt
    assert "정상 절차 안에 머물게" in prompt


def test_build_generation_prompt_for_voicephishing_uses_seed_text():
    spec = {
        "qa_id": "P01-01-v2",
        "source_type": "voicephishing",
        "difficulty": "hard",
        "pattern_name": "기관사칭형",
        "source_sample_id": "P01-01",
        "seed_text": "사기범: 검찰을 사칭하며 계좌 점검을 요구한다.",
    }

    prompt = build_generation_prompt(spec)

    assert "기관사칭형" in prompt
    assert "사기범: 검찰을 사칭하며 계좌 점검을 요구한다." in prompt
    assert "표면 단서만 복사하지 말고" in prompt


def test_normalize_generated_dialog_removes_blank_lines_and_caps_turns():
    text = "\n".join(["A", "", "B", "C", "D", "E", "F"])

    normalized = normalize_generated_dialog(text, max_turns=4)

    assert normalized.splitlines() == ["A", "B", "C", "D"]


def test_build_generation_prompt_for_irrelevant_pushes_similarity_without_core_fraud_actions():
    spec = {
        "qa_id": "IR-0001",
        "source_type": "irrelevant",
        "difficulty": "hard",
        "scenario_family": "delivery",
        "tone": "formal",
        "channel": "call",
    }

    prompt = build_generation_prompt(spec)

    assert "보이스피싱처럼 들릴 수는 있어도" in prompt
    assert "보호" in prompt
    assert "금융사기 핵심 신호는 직접 쓰지 마라" in prompt


def test_parse_args_accepts_v5_prompt_profile():
    args = parse_args(["--prompt-profile", "v5"])

    assert args.prompt_profile == "v5"


def test_parse_args_accepts_binary_dataset_mode():
    args = parse_args(["--dataset-mode", "binary"])

    assert args.dataset_mode == "binary"


def test_build_all_specs_binary_mode_excludes_irrelevant():
    specs = build_all_specs(4, 3, 5, dataset_mode="binary")

    assert len(specs) == 7
    assert {spec["source_type"] for spec in specs} == {"voicephishing", "bank_call"}


def test_build_generation_prompt_for_voicephishing_v5_requires_late_scam_anchor():
    spec = {
        "qa_id": "P01-01-v5",
        "source_type": "voicephishing",
        "difficulty": "hard",
        "pattern_name": "기관사칭형",
        "source_sample_id": "P01-01",
        "seed_text": "사기범: 검찰을 사칭하며 계좌 점검을 요구한다.",
    }

    prompt = build_generation_prompt(spec, prompt_profile="v5")

    assert "중반 이후에는 최소 한 번 이상 명확한 사기 실행 단서" in prompt
    assert "앱 설치, 링크 접속, 인증번호 제공, 원격 제어, 이체 유도" in prompt
    assert "초반 몇 턴이 너무 정상 상담처럼 마무리되지 않게 하라" in prompt


def test_build_generation_prompt_for_bank_call_v5_hardens_guardrails():
    spec = {
        "qa_id": "BC-0001",
        "source_type": "bank_call",
        "difficulty": "hard",
        "scenario_family": "transfer_check",
        "tone": "formal",
        "channel": "call",
    }

    prompt = build_generation_prompt(spec, prompt_profile="v5")

    assert "인증번호나 확인 코드를 읽게 하기" in prompt
    assert "공식 앱에서 직접 확인" in prompt
    assert "대표번호로 다시 걸기" in prompt
