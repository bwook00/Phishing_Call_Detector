#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


TARGET_PER_LABEL = 250


def _nonempty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _strip_speaker_labels(line: str) -> str:
    return (
        line.replace("고객센터:", "")
        .replace("상담원:", "")
        .replace("상담사:", "")
        .replace("직원:", "")
        .replace("사기범:", "")
        .replace("피해자:", "")
        .replace("고객:", "")
        .strip()
    )


def augment_transcript(text: str, variant: int) -> str:
    lines = _nonempty_lines(text)
    if variant == 0:
        return text
    if variant == 1:
        return "[통화 녹취 시작]\n" + text + "\n[통화 종료]"
    if variant == 2:
        return "\n".join(_strip_speaker_labels(line) for line in lines)
    if variant == 3:
        return "음, " + text.replace("\n", "\n음... ", 3)
    if variant == 4:
        return " ".join(lines)
    if variant == 5:
        return (
            text.replace("고객센터:", "상담원:")
            .replace("상담사:", "상담원:")
            .replace("사기범:", "담당자:")
            .replace("피해자:", "고객:")
        )
    if variant == 6:
        return "\n".join(line.replace(".", "").replace(",", "").replace("?", "") for line in lines)
    if variant == 7:
        return "\n".join(f"[{idx:02d}] {line}" for idx, line in enumerate(lines, start=1))
    if variant == 8:
        return "\n".join(("네, " + line) if idx % 4 == 1 else line for idx, line in enumerate(lines))
    if variant == 9:
        grouped = []
        for idx, line in enumerate(lines, start=1):
            grouped.append(line)
            if idx % 3 == 0:
                grouped.append("")
        return "\n".join(grouped).strip()
    raise ValueError(f"unknown variant: {variant}")


def build_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for variant in range(10):
        for row in rows:
            new_row = dict(row)
            new_row["qa_id"] = f"{row['qa_id']}-B{variant + 1}"
            new_row["scenario_text"] = augment_transcript(row["scenario_text"], variant)
            candidates.append(new_row)
    return candidates


def select_balanced_500(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    by_label: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        by_label[row["ground_truth"]].append(row)

    selected: list[dict[str, str]] = []
    for label in ("yes", "no"):
        rows = by_label[label]
        if len(rows) < TARGET_PER_LABEL:
            raise ValueError(f"not enough candidates for label={label}: {len(rows)}")
        selected.extend(rows[:TARGET_PER_LABEL])
    selected.sort(key=lambda row: (row["ground_truth"] != "yes", row["qa_id"]))
    return selected


def read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: str | Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/reinforced_v5_binary_qa_67.csv")
    parser.add_argument("--output", default="data/expanded_hard_binary_qa_500.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_rows(args.input)
    if not rows:
        raise ValueError("input benchmark is empty")
    candidates = build_candidates(rows)
    selected = select_balanced_500(candidates)
    write_rows(args.output, selected, list(rows[0].keys()))
    counts = defaultdict(int)
    for row in selected:
        counts[row["source_type"]] += 1
    print(f"wrote {len(selected)} rows to {args.output}")
    print(dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
