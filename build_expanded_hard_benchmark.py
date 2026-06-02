#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path


AUGMENTATION_SUFFIXES = ("base", "marked", "flattened", "stt-noise", "single-line")


def augment_transcript(text: str, variant: int) -> str:
    lines = text.splitlines()
    if variant == 0:
        return text
    if variant == 1:
        return "[통화 녹취 시작]\n" + text + "\n[통화 종료]"
    if variant == 2:
        return "\n".join(
            line.replace("고객센터:", "")
            .replace("상담원:", "")
            .replace("사기범:", "")
            .replace("피해자:", "")
            .strip()
            for line in lines
            if line.strip()
        )
    if variant == 3:
        return "음, " + text.replace("\n", "\n음... ", 3)
    if variant == 4:
        return " ".join(line.strip() for line in lines if line.strip())
    raise ValueError(f"unknown variant: {variant}")


def build_expanded_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    expanded = []
    for row in rows:
        for idx, _suffix in enumerate(AUGMENTATION_SUFFIXES, start=1):
            new_row = dict(row)
            new_row["qa_id"] = f"{row['qa_id']}-A{idx}"
            new_row["scenario_text"] = augment_transcript(row["scenario_text"], idx - 1)
            expanded.append(new_row)
    return expanded


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
    parser.add_argument("--output", default="data/expanded_hard_binary_qa_335.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_rows(args.input)
    if not rows:
        raise ValueError("input benchmark is empty")
    expanded = build_expanded_rows(rows)
    write_rows(args.output, expanded, list(rows[0].keys()))
    print(f"wrote {len(expanded)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
