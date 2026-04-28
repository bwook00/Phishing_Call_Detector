#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from naive_bm25_rag import BM25Index, corpus_rows_to_indexable, filter_retrieval_hits, read_csv_rows


BANK_CALL_KEYWORDS = (
    "계좌",
    "본인확인",
    "이상거래",
    "지급정지",
    "보안",
    "제한",
    "사고",
    "보호",
    "인증",
)

VOICEPHISHING_EASY_TOKENS = (
    "원격",
    "앱",
    "송금",
    "이체",
    "보호 계좌",
)


def keyword_bonus(text: str, keywords: tuple[str, ...]) -> float:
    return float(sum(1 for keyword in keywords if keyword in text))


def best_filtered_score(
    row: dict[str, str],
    index: BM25Index,
    top_k: int = 10,
    exclude_same_sample: bool = True,
    exclude_same_pattern: bool = True,
) -> float:
    hits = index.search(row["scenario_text"], top_k=top_k)
    hits = filter_retrieval_hits(
        hits,
        source_sample_id=row["source_sample_id"],
        exclude_same_sample=exclude_same_sample,
        exclude_same_pattern=exclude_same_pattern,
        top_k=1,
    )
    if not hits:
        return 0.0
    return float(hits[0]["score"])


def score_qa_row(
    row: dict[str, str],
    original_index: BM25Index,
    masked_index: BM25Index,
) -> dict[str, Any]:
    original_best = best_filtered_score(row, original_index)
    masked_best = best_filtered_score(row, masked_index)
    text = row["scenario_text"]
    source_type = row["source_type"]

    if source_type == "voicephishing":
        hard_score = max(original_best - masked_best, 0.0) * 2.5 + original_best
        hard_score -= keyword_bonus(text, VOICEPHISHING_EASY_TOKENS) * 0.5
    elif source_type == "bank_call":
        hard_score = masked_best * 1.5 + original_best
        hard_score += keyword_bonus(text, BANK_CALL_KEYWORDS) * 0.75
    else:
        hard_score = (original_best + masked_best) * 0.35

    return {
        **row,
        "original_best_score": f"{original_best:.6f}",
        "masked_best_score": f"{masked_best:.6f}",
        "hard_score": float(hard_score),
    }


def select_rows_by_source(scored_rows: list[dict[str, Any]], targets: dict[str, int]) -> list[dict[str, Any]]:
    selected = []
    for source_type, count in targets.items():
        candidates = [row for row in scored_rows if row["source_type"] == source_type]
        candidates.sort(key=lambda row: (-float(row["hard_score"]), row["qa_id"]))
        selected.extend(candidates[:count])
    selected.sort(key=lambda row: row["qa_id"])
    return selected


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_index(path: str | Path) -> BM25Index:
    return BM25Index.from_documents(corpus_rows_to_indexable(read_csv_rows(path)), text_key="search_text")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa", default="data/voicephishing_qa_dataset.csv")
    parser.add_argument("--original-corpus", default="data/voicephishing_corpus_v2.csv")
    parser.add_argument("--masked-corpus", default="data/voicephishing_corpus_masked.csv")
    parser.add_argument("--pilot-output", default="data/rag_hard_pilot_100.csv")
    parser.add_argument("--official-output", default="data/rag_hard_official_300.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    qa_rows = read_csv_rows(args.qa)
    original_index = build_index(args.original_corpus)
    masked_index = build_index(args.masked_corpus)
    scored_rows = [score_qa_row(row, original_index, masked_index) for row in qa_rows]

    pilot = select_rows_by_source(
        scored_rows,
        {"voicephishing": 40, "bank_call": 40, "irrelevant": 20},
    )
    official = select_rows_by_source(
        scored_rows,
        {"voicephishing": 120, "bank_call": 120, "irrelevant": 60},
    )

    write_csv(args.pilot_output, pilot)
    write_csv(args.official_output, official)
    print(
        {
            "pilot_rows": len(pilot),
            "official_rows": len(official),
            "pilot_output": args.pilot_output,
            "official_output": args.official_output,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
