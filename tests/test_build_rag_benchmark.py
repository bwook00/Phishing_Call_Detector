from build_rag_benchmark import score_qa_row, select_rows_by_source
from naive_bm25_rag import BM25Index, corpus_rows_to_indexable


def build_index(rows):
    return BM25Index.from_documents(corpus_rows_to_indexable(rows), text_key="search_text")


def test_score_qa_row_prefers_confusable_bank_call_over_irrelevant():
    original_corpus = [
        {"sample_id": "P01-01", "scenario_text": "검찰 사건번호 계좌 확인 요구"},
        {"sample_id": "P02-01", "scenario_text": "원격 앱 설치와 보호 계좌 이체 유도"},
    ]
    masked_corpus = [
        {"sample_id": "P01-01", "scenario_text": "[기관명] [사건번호] [계좌번호] 확인 요구"},
        {"sample_id": "P02-01", "scenario_text": "[앱명] 설치와 보호 계좌 이체 유도"},
    ]
    bank_row = {
        "qa_id": "BC-001",
        "source_type": "bank_call",
        "source_sample_id": "BC-001",
        "scenario_text": "상담사: 계좌 이상거래와 본인확인 절차를 안내합니다.",
    }
    irrelevant_row = {
        "qa_id": "IR-001",
        "source_type": "irrelevant",
        "source_sample_id": "IR-001",
        "scenario_text": "상담사: 레스토랑 예약 시간을 변경할까요?",
    }

    bank_score = score_qa_row(bank_row, build_index(original_corpus), build_index(masked_corpus))
    irrelevant_score = score_qa_row(irrelevant_row, build_index(original_corpus), build_index(masked_corpus))

    assert bank_score["hard_score"] > irrelevant_score["hard_score"]


def test_select_rows_by_source_is_deterministic_for_equal_scores():
    scored_rows = [
        {"qa_id": "P02", "source_type": "voicephishing", "hard_score": 1.0},
        {"qa_id": "P01", "source_type": "voicephishing", "hard_score": 1.0},
        {"qa_id": "BC-02", "source_type": "bank_call", "hard_score": 1.0},
        {"qa_id": "BC-01", "source_type": "bank_call", "hard_score": 1.0},
    ]

    selected = select_rows_by_source(scored_rows, {"voicephishing": 1, "bank_call": 1})

    assert [row["qa_id"] for row in selected] == ["BC-01", "P01"]


def test_select_rows_by_source_uses_requested_mix_when_enough_rows_exist():
    scored_rows = []
    for idx in range(3):
        scored_rows.append({"qa_id": f"P{idx}", "source_type": "voicephishing", "hard_score": 3 - idx})
        scored_rows.append({"qa_id": f"BC-{idx}", "source_type": "bank_call", "hard_score": 3 - idx})
        scored_rows.append({"qa_id": f"IR-{idx}", "source_type": "irrelevant", "hard_score": 3 - idx})

    selected = select_rows_by_source(
        scored_rows,
        {"voicephishing": 2, "bank_call": 2, "irrelevant": 1},
    )

    assert len(selected) == 5
    assert [row["source_type"] for row in selected].count("voicephishing") == 2
    assert [row["source_type"] for row in selected].count("bank_call") == 2
    assert [row["source_type"] for row in selected].count("irrelevant") == 1
