import csv
import io
import json
import math
import urllib.error
from pathlib import Path

from naive_bm25_rag import (
    BM25Index,
    batch_result_text,
    build_default_output_path,
    build_message_batch_requests,
    build_retrieval_metadata,
    build_retrieval_evidence_summary,
    corpus_rows_to_indexable,
    compute_threshold_score,
    build_search_text,
    build_prompt,
    extract_signal_features,
    filter_retrieval_hits,
    is_openai_model,
    load_anthropic_api_key,
    load_openai_api_key,
    merge_batch_predictions,
    normalize_prediction,
    parse_args,
    predict_with_bm25_threshold,
    post_json,
    read_csv_rows,
    resolve_retrieval_exclusions,
    summarize_results,
)


def test_bm25_returns_best_matching_document_first():
    docs = [
        {"doc_id": "D1", "text": "검찰 사칭 사건번호 계좌 확인 요구"},
        {"doc_id": "D2", "text": "레스토랑 예약 시간 변경 문의"},
        {"doc_id": "D3", "text": "은행 카드 재발급 본인확인 안내"},
    ]

    index = BM25Index.from_documents(docs, text_key="text")
    results = index.search("사건번호 검찰 계좌", top_k=2)

    assert len(results) == 2
    assert results[0]["doc"]["doc_id"] == "D1"
    assert results[0]["score"] >= results[1]["score"]


def test_summarize_results_returns_accuracy_and_source_breakdown():
    rows = [
        {"source_type": "voicephishing", "ground_truth": "yes", "prediction": "yes"},
        {"source_type": "voicephishing", "ground_truth": "yes", "prediction": "no"},
        {"source_type": "bank_call", "ground_truth": "no", "prediction": "no"},
        {"source_type": "irrelevant", "ground_truth": "no", "prediction": "yes"},
    ]

    summary = summarize_results(rows)

    assert math.isclose(summary["overall_accuracy"], 0.5)
    assert math.isclose(summary["by_source"]["voicephishing"]["accuracy"], 0.5)
    assert math.isclose(summary["by_source"]["bank_call"]["accuracy"], 1.0)
    assert math.isclose(summary["by_source"]["irrelevant"]["accuracy"], 0.0)


def test_read_csv_rows_and_build_prompt(tmp_path: Path):
    corpus_path = tmp_path / "corpus.csv"
    with corpus_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "scenario_text"])
        writer.writeheader()
        writer.writerow({"sample_id": "P01", "scenario_text": "사기범: 사건번호를 확인하라고 합니다."})

    rows = read_csv_rows(corpus_path)

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="사기범이 사건번호를 말하며 계좌 확인을 요구한다.",
        retrieved_rows=rows,
    )

    assert rows[0]["sample_id"] == "P01"
    assert "Context 1" in prompt
    assert "70% 이상 유사" in prompt
    assert "사건번호" in prompt
    assert "질문 대상 대화" in prompt


def test_build_prompt_supports_evidence_mode_with_explicit_action_guidance():
    retrieved_rows = [
        {
            "doc_id": "P01-01",
            "scenario_text": "앱 설치와 인증번호 제공을 요구하며 링크 접속을 유도합니다.",
        }
    ]

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="고객보호센터라며 앱 설치를 요구했습니다.",
        retrieved_rows=retrieved_rows,
        prompt_mode="evidence",
    )

    assert "사기 전용 행동" in prompt
    assert "앱 설치" in prompt
    assert "공식 앱에서 직접 확인" in prompt
    assert "대화 원문 자체" in prompt


def test_build_prompt_supports_retrieval_gated_mode_and_forbids_query_only_decisions():
    retrieved_rows = [
        {
            "doc_id": "P01-01",
            "scenario_text": "링크 접속과 앱 설치를 유도하고 인증번호 제공을 요구했습니다.",
        }
    ]

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="고객보호센터라고 하며 앱 설치를 안내했습니다.",
        retrieved_rows=retrieved_rows,
        prompt_mode="retrieval-gated",
    )

    assert "질문 대상 대화만 보고 추정하지 마라" in prompt
    assert "support" in prompt
    assert "contradiction" in prompt
    assert "insufficient evidence" in prompt
    assert "retrieval evidence summary" in prompt


def test_build_prompt_supports_retrieval_flow_mode_for_partial_call_progression():
    retrieved_rows = [
        {
            "doc_id": "P01-01",
            "scenario_text": "보호 절차로 시작하지만 뒤에서 링크 접속과 앱 설치를 유도합니다.",
        }
    ]

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="이상거래 보호 절차라고 하며 신원 확인을 진행했습니다.",
        retrieved_rows=retrieved_rows,
        prompt_mode="retrieval-flow",
    )

    assert "대화가 아직 중간 단계에서 끝났더라도" in prompt
    assert "later scam continuation" in prompt
    assert "절차 흐름" in prompt


def test_build_prompt_supports_retrieval_anchor_flow_mode_for_identifier_plus_flow_matching():
    retrieved_rows = [
        {
            "doc_id": "P01-01",
            "scenario_text": "국민은행 김민정 고객님께 연락해 뒤에서 링크 접속과 앱 설치를 유도합니다.",
        }
    ]

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="국민은행 김민정 고객님 명의 이상거래 보호 절차라고 하며 신원 확인을 진행했습니다.",
        retrieved_rows=retrieved_rows,
        prompt_mode="retrieval-anchor-flow",
    )

    assert "shared identifier anchor" in prompt
    assert "generic banking similarity만 있으면 no" in prompt
    assert "later scam continuation" in prompt


def test_build_prompt_supports_summary_gated_mode_without_raw_context_blocks():
    retrieved_rows = [
        {
            "doc_id": "P01-01",
            "scenario_text": "국민은행 김민정 고객님께 연락해 뒤에서 링크 접속과 앱 설치를 유도합니다.",
        }
    ]

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="국민은행 김민정 고객님 명의 이상거래 보호 절차라고 하며 신원 확인을 진행했습니다.",
        retrieved_rows=retrieved_rows,
        prompt_mode="summary-gated",
    )

    assert "raw context 본문은 의도적으로 숨겨져 있다" in prompt
    assert "matched identifiers" in prompt
    assert "Context 1:" not in prompt


def test_build_prompt_supports_identifier_filtered_flow_mode_and_hides_nonmatching_context():
    retrieved_rows = [
        {
            "doc_id": "P01-01",
            "scenario_text": "국민은행 김민정 고객님께 연락해 뒤에서 링크 접속과 앱 설치를 유도합니다.",
        },
        {
            "doc_id": "P99-01",
            "scenario_text": "신한은행 박서준 고객님께 연락해 뒤에서 링크 접속을 유도합니다.",
        },
    ]

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="국민은행 김민정 고객님 명의 이상거래 보호 절차라고 하며 신원 확인을 진행했습니다.",
        retrieved_rows=retrieved_rows,
        prompt_mode="identifier-filtered-flow",
    )

    assert "shared identifier가 없는 context는 숨긴다" in prompt
    assert "Context 1:" in prompt
    assert "Context 2: filtered out (no shared identifiers)." in prompt
    assert "context 2 filtered out: no shared identifiers" in prompt


def test_identifier_filtered_flow_returns_policy_no_prompt_when_all_contexts_filtered():
    retrieved_rows = [
        {
            "doc_id": "P99-01",
            "scenario_text": "신한은행 박서준 고객님께 연락해 뒤에서 링크 접속을 유도합니다.",
        },
    ]

    prompt = build_prompt(
        question="이 텍스트는 보이스피싱으로 판단해야 하는가? yes or no로 답하라.",
        scenario_text="국민은행 김민정 고객님 명의 이상거래 보호 절차라고 하며 신원 확인을 진행했습니다.",
        retrieved_rows=retrieved_rows,
        prompt_mode="identifier-filtered-flow",
    )

    assert "No qualifying retrieval evidence remains after identifier filtering." in prompt
    assert "설명하지 말고 no만 출력하라." in prompt


def test_parse_args_uses_expected_defaults():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
        ]
    )

    assert args.top_k == 3
    assert args.limit is None
    assert args.dry_run is False
    assert args.command == "evaluate"
    assert args.prompt_mode == "similarity"


def test_parse_args_supports_retrieval_exclusion_flags():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--exclude-same-sample",
            "--exclude-same-pattern",
        ]
    )

    assert args.exclude_same_sample is True
    assert args.exclude_same_pattern is True


def test_parse_args_supports_threshold_decision_mode():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--decision-mode",
            "bm25-threshold",
            "--yes-threshold",
            "12.5",
        ]
    )

    assert args.decision_mode == "bm25-threshold"
    assert args.yes_threshold == 12.5


def test_parse_args_supports_retrieval_regime():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--retrieval-regime",
            "realistic",
        ]
    )

    assert args.retrieval_regime == "realistic"


def test_parse_args_supports_evidence_prompt_mode():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--prompt-mode",
            "evidence",
        ]
    )

    assert args.prompt_mode == "evidence"


def test_parse_args_supports_retrieval_gated_prompt_mode():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--prompt-mode",
            "retrieval-gated",
        ]
    )

    assert args.prompt_mode == "retrieval-gated"


def test_parse_args_supports_retrieval_flow_prompt_mode():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--prompt-mode",
            "retrieval-flow",
        ]
    )

    assert args.prompt_mode == "retrieval-flow"


def test_parse_args_supports_retrieval_anchor_flow_prompt_mode():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--prompt-mode",
            "retrieval-anchor-flow",
        ]
    )

    assert args.prompt_mode == "retrieval-anchor-flow"


def test_parse_args_supports_summary_gated_prompt_mode():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--prompt-mode",
            "summary-gated",
        ]
    )

    assert args.prompt_mode == "summary-gated"


def test_parse_args_supports_identifier_filtered_flow_prompt_mode():
    args = parse_args(
        [
            "--corpus",
            "data/voicephishing_corpus_v2.csv",
            "--qa",
            "data/voicephishing_qa_dataset.csv",
            "--prompt-mode",
            "identifier-filtered-flow",
        ]
    )

    assert args.prompt_mode == "identifier-filtered-flow"




def test_parse_args_supports_batch_submit_command():
    args = parse_args(
        [
            "submit-batch",
            "--retrieval-csv",
            "data/naive_rag_original_retrieval_only.csv",
            "--model",
            "claude-haiku-4-5",
        ]
    )

    assert args.command == "submit-batch"
    assert args.retrieval_csv.endswith("naive_rag_original_retrieval_only.csv")


def test_normalize_prediction_and_output_path():
    assert normalize_prediction("YES") == "yes"
    assert normalize_prediction("no.") == "no"
    assert normalize_prediction("maybe") == "unknown"
    assert build_default_output_path("data/voicephishing_corpus_masked.csv").endswith(
        "naive_rag_voicephishing_corpus_masked_results.csv"
    )


def test_load_anthropic_api_key_prefers_env_over_dotenv(tmp_path: Path, monkeypatch):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text('ANTHROPIC_API_KEY="dotenv-key"\n', encoding="utf-8")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")

    value = load_anthropic_api_key(dotenv_path)

    assert value == "env-key"


def test_load_anthropic_api_key_reads_dotenv_when_env_missing(tmp_path: Path, monkeypatch):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("ANTHROPIC_API_KEY=dotenv-key\n", encoding="utf-8")

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    value = load_anthropic_api_key(dotenv_path)

    assert value == "dotenv-key"


def test_load_openai_api_key_reads_dotenv_when_env_missing(tmp_path: Path, monkeypatch):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("OPENAI_API_KEY=openai-key\n", encoding="utf-8")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    value = load_openai_api_key(dotenv_path)

    assert value == "openai-key"


def test_build_message_batch_requests_uses_prompt_as_user_message():
    retrieval_rows = [
        {
            "qa_id": "P01-01",
            "prompt": "prompt-body",
        }
    ]

    requests = build_message_batch_requests(retrieval_rows, model="claude-haiku-4-5")

    assert requests[0]["custom_id"] == "P01-01"
    assert requests[0]["params"]["model"] == "claude-haiku-4-5"
    assert requests[0]["params"]["messages"][0]["role"] == "user"
    assert requests[0]["params"]["messages"][0]["content"] == "prompt-body"


def test_is_openai_model_detects_gpt_family():
    assert is_openai_model("gpt-5-mini") is True
    assert is_openai_model("gpt-4o-mini") is True
    assert is_openai_model("claude-haiku-4-5") is False


def test_merge_batch_predictions_matches_custom_id():
    retrieval_rows = [
        {
            "qa_id": "P01-01",
            "source_type": "voicephishing",
            "source_sample_id": "P01-01",
            "ground_truth": "yes",
            "prediction": "dry_run",
            "raw_output": "",
            "retrieved_doc_ids": "P01-01|P01-02",
            "retrieved_scores": "1.0|0.8",
            "prompt": "prompt-body",
        }
    ]
    result_lines = [
        {
            "custom_id": "P01-01",
            "result": {
                "type": "succeeded",
                "message": {
                    "content": [{"type": "text", "text": "yes"}]
                },
            },
        }
    ]

    merged = merge_batch_predictions(retrieval_rows, result_lines)

    assert merged[0]["prediction"] == "yes"
    assert merged[0]["raw_output"] == "yes"


def test_batch_result_text_handles_succeeded_and_errored_results():
    ok = {
        "result": {
            "type": "succeeded",
            "message": {"content": [{"type": "text", "text": "no"}]},
        }
    }
    err = {"result": {"type": "errored"}}

    assert batch_result_text(ok) == "no"
    assert batch_result_text(err) == ""


def test_batch_result_text_handles_openai_batch_response_shape():
    ok = {
        "custom_id": "P01-01",
        "response": {
            "status_code": 200,
            "body": {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "yes"}],
                    }
                ],
            },
        },
        "error": None,
    }
    err = {
        "custom_id": "P01-02",
        "response": {
            "status_code": 400,
            "body": {
                "status": "failed",
                "output": [],
            },
        },
        "error": {"message": "bad request"},
    }

    assert batch_result_text(ok) == "yes"
    assert batch_result_text(err) == ""


def test_filter_retrieval_hits_excludes_same_sample_and_pattern():
    hits = [
        {"doc": {"doc_id": "P01-01"}, "score": 5.0},
        {"doc": {"doc_id": "P01-02"}, "score": 4.0},
        {"doc": {"doc_id": "P02-01"}, "score": 3.0},
    ]

    sample_only = filter_retrieval_hits(
        hits,
        source_sample_id="P01-01",
        exclude_same_sample=True,
        exclude_same_pattern=False,
        top_k=2,
    )
    pattern_and_sample = filter_retrieval_hits(
        hits,
        source_sample_id="P01-01",
        exclude_same_sample=True,
        exclude_same_pattern=True,
        top_k=2,
    )

    assert [hit["doc"]["doc_id"] for hit in sample_only] == ["P01-02", "P02-01"]
    assert [hit["doc"]["doc_id"] for hit in pattern_and_sample] == ["P02-01"]


def test_predict_with_bm25_threshold_uses_top_score_cutoff():
    high_hits = [{"doc": {"doc_id": "P02-01"}, "score": 14.0}]
    low_hits = [{"doc": {"doc_id": "P02-01"}, "score": 8.0}]

    assert predict_with_bm25_threshold(high_hits, yes_threshold=10.0) == ("yes", "bm25:14.000000")
    assert predict_with_bm25_threshold(low_hits, yes_threshold=10.0) == ("no", "bm25:8.000000")
    assert predict_with_bm25_threshold([], yes_threshold=10.0) == ("no", "bm25:0.000000")


def test_resolve_retrieval_exclusions_supports_realistic_and_strict_modes():
    assert resolve_retrieval_exclusions("custom", False, True) == (False, True)
    assert resolve_retrieval_exclusions("realistic", False, True) == (True, False)
    assert resolve_retrieval_exclusions("strict", False, False) == (True, True)


def test_build_retrieval_metadata_reports_top_family_and_margin():
    hits = [
        {"doc": {"doc_id": "P02-03"}, "score": 11.0},
        {"doc": {"doc_id": "P07-01"}, "score": 8.5},
    ]

    metadata = build_retrieval_metadata(hits, source_sample_id="P02-09", retrieval_regime="realistic")

    assert metadata["top_retrieved_doc_id"] == "P02-03"
    assert metadata["top_retrieved_family"] == "P02"
    assert metadata["same_family_hit"] == "yes"
    assert metadata["top_score_margin"] == "2.500000"
    assert metadata["retrieval_regime"] == "realistic"


def test_build_search_text_filters_generic_bank_terms_but_keeps_identifiers():
    text = (
        "국민은행 고객보호센터에서 김민정 고객님께 연락해 "
        "서울 강서구 주소와 사건번호 2026형제18000을 확인했습니다."
    )

    search_text = build_search_text(text)

    assert "고객보호센터" not in search_text
    assert "국민은행" in search_text
    assert "김민정" in search_text
    assert "강서구" in search_text
    assert "2026형제18000" in search_text
    assert "확인" not in search_text


def test_build_search_text_adds_canonical_scam_action_anchors():
    text = "안내받은 링크로 접속하라고 하고 앱 설치 후 인증번호를 불러달라고 했습니다."

    search_text = build_search_text(text)

    assert "링크접속" in search_text
    assert "앱설치" in search_text
    assert "인증번호제공" in search_text


def test_compute_threshold_score_rewards_scam_action_anchors():
    hits = [{"doc": {"doc_id": "P01-01"}, "score": 50.0}]

    adjusted_score, raw_output = compute_threshold_score(
        "링크로 접속하라고 하고 앱 설치 후 인증번호를 불러달라고 했습니다.",
        hits,
    )

    assert adjusted_score > 50.0
    assert "adj:" in raw_output


def test_compute_threshold_score_penalizes_legitimate_resolution_anchors():
    hits = [{"doc": {"doc_id": "P01-01"}, "score": 50.0}]

    adjusted_score, raw_output = compute_threshold_score(
        "공식 앱에서 직접 확인하시고 대표번호로 다시 걸거나 영업점 방문을 부탁드립니다.",
        hits,
    )

    assert adjusted_score < 50.0
    assert "adj:" in raw_output


def test_post_json_retries_once_after_429(monkeypatch):
    calls = {"count": 0}

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"ok": True}).encode("utf-8")

    def fake_urlopen(request):
        calls["count"] += 1
        if calls["count"] == 1:
            raise urllib.error.HTTPError(
                request.full_url,
                429,
                "Too Many Requests",
                {"Retry-After": "0"},
                io.BytesIO(b""),
            )
        return DummyResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    data = post_json("https://example.com", {"hello": "world"}, {"Authorization": "Bearer token"})

    assert data == {"ok": True}
    assert calls["count"] == 2


def test_extract_signal_features_separates_identifier_scam_and_legitimate_signals():
    features = extract_signal_features(
        "국민은행 김민정 고객님 사건번호 2026형제18000 확인 후 링크 접속을 요구했지만 대표번호로 다시 걸라고 했습니다."
    )

    assert "국민은행" in features["identifier_anchors"]
    assert "김민정" in features["identifier_anchors"]
    assert "2026형제18000" in features["identifier_anchors"]
    assert "링크접속" in features["scam_actions"]
    assert "대표번호재통화" in features["legitimate_actions"]


def test_build_retrieval_evidence_summary_reports_overlap_and_context_only_clues():
    retrieved_rows = [
        {
            "doc_id": "P01-01",
            "scenario_text": "국민은행 김민정 고객님께 링크 접속과 앱 설치를 요구했습니다.",
        },
        {
            "doc_id": "BC-0001",
            "scenario_text": "대표번호로 다시 걸어 공식 앱에서 확인해 달라고 안내했습니다.",
        },
    ]

    summary = build_retrieval_evidence_summary(
        "국민은행 김민정 고객님께 링크 접속을 요구했습니다.",
        retrieved_rows,
    )

    assert "query scam actions: 링크접속" in summary
    assert "context 1 matched identifiers: 국민은행, 김민정" in summary
    assert "context 1 matched scam actions: 링크접속" in summary
    assert "context 1 context-only scam actions: 앱설치" in summary
    assert "context 2 context-only legitimate actions: 공식앱확인, 대표번호재통화" in summary


def test_corpus_rows_to_indexable_emphasizes_identifier_anchor_match_over_generic_overlap():
    docs = [
        {
            "sample_id": "P01-01",
            "scenario_text": (
                "국민은행 고객보호센터에서 김민정 고객님께 연락해 "
                "서울 강서구 주소와 사건번호 2026형제18000을 확인했습니다."
            ),
        },
        {
            "sample_id": "BC-0001",
            "scenario_text": (
                "고객보호센터 보호절차 확인 안내 보호절차 확인 안내 "
                "이상거래 확인 본인확인 보호절차 안내를 반복합니다."
            ),
        },
    ]

    index = BM25Index.from_documents(corpus_rows_to_indexable(docs), text_key="search_text")
    query = (
        "국민은행 고객보호센터입니다. 김민정 고객님 서울 강서구 주소와 "
        "사건번호 2026형제18000 확인이 필요합니다."
    )
    results = index.search(build_search_text(query), top_k=2)

    assert results[0]["doc"]["doc_id"] == "P01-01"
