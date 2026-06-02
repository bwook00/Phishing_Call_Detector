#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from build_expanded_hard_benchmark_500 import augment_transcript as base_augment


TARGET_PER_LABEL = 250


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def augment_transcript(text: str, variant: int) -> str:
    if variant < 10:
        return base_augment(text, variant)
    lines = _lines(text)
    if variant == 10:
        return "\n".join(f"- {line}" for line in lines)
    if variant == 11:
        return "\n".join(f"[00:{idx:02d}] {line}" for idx, line in enumerate(lines, start=1))
    if variant == 12:
        return text.replace("고객센터:", "은행직원:").replace("상담사:", "은행직원:").replace("피해자:", "고객:")
    if variant == 13:
        return text.replace(": ", ":")
    if variant == 14:
        return "\n".join(line + (" [잡음]" if idx % 5 == 0 else "") for idx, line in enumerate(lines, start=1))
    if variant == 15:
        return "\n".join(("잠시만요. " + line) if idx % 6 == 0 else line for idx, line in enumerate(lines, start=1))
    if variant == 16:
        return text.replace("네,", "예,").replace("네.", "예.")
    if variant == 17:
        return "\n".join(f"발화{idx}: {line.split(':', 1)[-1].strip()}" for idx, line in enumerate(lines, start=1))
    if variant == 18:
        return " / ".join(lines)
    if variant == 19:
        return "[자동 전사본]\n" + "\n".join(line.replace("  ", " ") for line in lines)
    raise ValueError(f"unknown variant: {variant}")


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: str | Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_candidates(rows: list[dict[str, str]], variant_count: int = 20) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for variant in range(variant_count):
        for row in rows:
            new_row = dict(row)
            new_row["qa_id"] = f"{row['qa_id']}-B{variant + 1}"
            new_row["scenario_text"] = augment_transcript(row["scenario_text"], variant)
            candidates.append(new_row)
    return candidates


def select_extra_500(candidates: list[dict[str, str]], existing_ids: set[str]) -> list[dict[str, str]]:
    by_label: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        if row["qa_id"] in existing_ids:
            continue
        by_label[row["ground_truth"]].append(row)

    selected: list[dict[str, str]] = []
    for label in ("yes", "no"):
        rows = by_label[label]
        if len(rows) < TARGET_PER_LABEL:
            raise ValueError(f"not enough extra candidates for label={label}: {len(rows)}")
        selected.extend(rows[:TARGET_PER_LABEL])
    selected.sort(key=lambda row: (row["ground_truth"] != "yes", row["qa_id"]))
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/reinforced_v5_binary_qa_67.csv")
    parser.add_argument("--existing", default="data/expanded_hard_binary_qa_500.csv")
    parser.add_argument("--output", default="data/expanded_hard_binary_qa_extra500.csv")
    parser.add_argument("--combined-output", default="data/expanded_hard_binary_qa_1000.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_rows = read_rows(args.input)
    existing_rows = read_rows(args.existing)
    existing_ids = {row["qa_id"] for row in existing_rows}
    selected = select_extra_500(build_candidates(base_rows), existing_ids)
    write_rows(args.output, selected, list(base_rows[0].keys()))
    combined = existing_rows + selected
    write_rows(args.combined_output, combined, list(base_rows[0].keys()))
    for path, rows in [(args.output, selected), (args.combined_output, combined)]:
        counts = defaultdict(int)
        for row in rows:
            counts[row["source_type"]] += 1
        print(f"wrote {len(rows)} rows to {path}: {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
