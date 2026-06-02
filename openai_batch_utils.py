#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import os
import uuid
import urllib.request
from pathlib import Path
from typing import Any

from naive_bm25_rag import batch_result_text, merge_batch_predictions, read_csv_rows, summarize_results, write_results


OPENAI_API_BASE = "https://api.openai.com/v1"


def load_openai_api_key(dotenv_path: str | Path = ".env") -> str:
    if value := os.environ.get("OPENAI_API_KEY"):
        return value
    path = Path(dotenv_path)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == "OPENAI_API_KEY":
                return value.strip().strip('"').strip("'")
    raise RuntimeError("OPENAI_API_KEY is not set")


def auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    api_key = load_openai_api_key()
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{OPENAI_API_BASE}{path}",
        data=body,
        headers={**auth_headers(api_key), "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str) -> dict[str, Any]:
    api_key = load_openai_api_key()
    request = urllib.request.Request(f"{OPENAI_API_BASE}{path}", headers=auth_headers(api_key), method="GET")
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def get_bytes(path: str) -> bytes:
    api_key = load_openai_api_key()
    request = urllib.request.Request(f"{OPENAI_API_BASE}{path}", headers=auth_headers(api_key), method="GET")
    with urllib.request.urlopen(request) as response:
        return response.read()


def upload_file(file_path: str | Path, purpose: str = "batch") -> dict[str, Any]:
    api_key = load_openai_api_key()
    file_path = Path(file_path)
    boundary = f"----codex-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    parts = [
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="purpose"\r\n\r\n'
            f"{purpose}\r\n"
        ).encode("utf-8"),
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8"),
        file_path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    request = urllib.request.Request(
        f"{OPENAI_API_BASE}/files",
        data=body,
        headers={**auth_headers(api_key), "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def make_requests(retrieval_csv: str | Path, output_jsonl: str | Path, model: str) -> None:
    rows = read_csv_rows(retrieval_csv)
    with Path(output_jsonl).open("w", encoding="utf-8") as f:
        for row in rows:
            request = {
                "custom_id": row["qa_id"],
                "method": "POST",
                "url": "/v1/responses",
                "body": {
                    "model": model,
                    "input": [
                        {
                            "role": "user",
                            "content": [{"type": "input_text", "text": row["prompt"]}],
                        }
                    ],
                    "max_output_tokens": 20,
                    "temperature": 0,
                },
            }
            f.write(json.dumps(request, ensure_ascii=False) + "\n")


def submit_batch(requests_jsonl: str | Path, output_meta: str | Path) -> dict[str, Any]:
    uploaded = upload_file(requests_jsonl, purpose="batch")
    batch = post_json(
        "/batches",
        {
            "input_file_id": uploaded["id"],
            "endpoint": "/v1/responses",
            "completion_window": "24h",
        },
    )
    Path(output_meta).write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    return batch


def fetch_batch(batch_id: str, output_status: str | Path, output_jsonl: str | Path | None = None) -> dict[str, Any]:
    status = get_json(f"/batches/{batch_id}")
    Path(output_status).write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    if output_jsonl and status.get("output_file_id"):
        content = get_bytes(f"/files/{status['output_file_id']}/content")
        Path(output_jsonl).write_bytes(content)
    return status


def merge(retrieval_csv: str | Path, results_jsonl: str | Path, output_csv: str | Path) -> dict[str, Any]:
    retrieval_rows = read_csv_rows(retrieval_csv)
    lines = [json.loads(line) for line in Path(results_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()]
    merged = merge_batch_predictions(retrieval_rows, lines)
    write_results(output_csv, merged)
    return summarize_results(merged)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("make-requests")
    make.add_argument("--retrieval-csv", required=True)
    make.add_argument("--output-jsonl", required=True)
    make.add_argument("--model", default="gpt-4o-mini")
    submit = sub.add_parser("submit")
    submit.add_argument("--requests-jsonl", required=True)
    submit.add_argument("--output-meta", required=True)
    status = sub.add_parser("fetch")
    status.add_argument("--batch-id", required=True)
    status.add_argument("--output-status", required=True)
    status.add_argument("--output-jsonl")
    merge_parser = sub.add_parser("merge")
    merge_parser.add_argument("--retrieval-csv", required=True)
    merge_parser.add_argument("--results-jsonl", required=True)
    merge_parser.add_argument("--output-csv", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "make-requests":
        make_requests(args.retrieval_csv, args.output_jsonl, args.model)
        print(json.dumps({"output_jsonl": args.output_jsonl}, ensure_ascii=False, indent=2))
    elif args.command == "submit":
        print(json.dumps(submit_batch(args.requests_jsonl, args.output_meta), ensure_ascii=False, indent=2))
    elif args.command == "fetch":
        print(json.dumps(fetch_batch(args.batch_id, args.output_status, args.output_jsonl), ensure_ascii=False, indent=2))
    elif args.command == "merge":
        print(json.dumps(merge(args.retrieval_csv, args.results_jsonl, args.output_csv), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
