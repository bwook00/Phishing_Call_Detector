#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PLACEHOLDER_TOKEN_MAP = {
    "[기관명]": "uiuiufawaefiiifji",
    "[이름]": "qmqmzkkvvopaa",
    "[은행명]": "bbbqrrtuuplkz",
    "[사건번호]": "xxyyqqppmmrrt",
    "[주소]": "aaeiioouuzzxx",
    "[직장명]": "ppqqrrssttllm",
    "[앱명]": "vvxxccnnmmqqp",
    "[계좌번호]": "zzllkkjjhhggf",
    "[금액]": "ooqquuiirrppa",
    "[링크]": "mmnnooppqqrrs",
    "[시간]": "ttwwyyuuiiopp",
    "[자녀이름]": "hhjjkkllzzxxc",
    "[지인명]": "ccvvbbnnmmqqw",
    "[학교명]": "llkkjjhhggffd",
    "[기관연락처]": "jjhhggffdssaa",
    "[개인식별묶음]": "ppttuuzzllkkq",
    "[사건접수식별자]": "vvbnnmmqqwwee",
}


def apply_strong_masking(text: str) -> str:
    for placeholder, token in PLACEHOLDER_TOKEN_MAP.items():
        text = text.replace(placeholder, token)
    return text


def transform_csv(infile: str | Path, outfile: str | Path, field: str = "scenario_text") -> None:
    with Path(infile).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return
    for row in rows:
        row[field] = apply_strong_masking(row[field])
    with Path(outfile).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--field", default="scenario_text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    transform_csv(args.input, args.output, field=args.field)
    print({"input": args.input, "output": args.output, "field": args.field})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
