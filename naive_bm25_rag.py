#!/usr/bin/env python3

from __future__ import annotations

import math
import csv
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEARCH_TOKEN_RE = re.compile(r"\[[^\]]+\]|[A-Za-z0-9]+(?:[-./][A-Za-z0-9]+)*|[가-힣]{2,}")
GENERIC_PHRASE_PATTERNS = (
    r"고객보호센터",
    r"이상거래확인실",
    r"이상거래",
    r"본인확인",
    r"보호절차",
    r"보안점검",
    r"등록정보",
    r"자산보호",
    r"임시제한",
    r"보호단계",
)
TOKEN_STOPWORDS = {
    "확인",
    "확인했습니다",
    "안내",
    "안내를",
    "절차",
    "처리",
    "조회",
    "보호",
    "보안",
    "계좌",
    "이상거래",
    "본인확인",
    "등록정보",
    "고객님",
    "고객",
    "연락",
    "센터",
    "팀",
    "단계",
    "진행",
}
BANK_NAME_PATTERN = re.compile(r"(국민은행|신한은행|하나은행|우리은행|농협은행|카카오뱅크|토스뱅크|IBK기업은행)")
NAME_WITH_SUFFIX_PATTERN = re.compile(r"([가-힣]{2,4})(?:\s*(?:고객님|씨))")
ADDRESS_ANCHOR_PATTERN = re.compile(r"([가-힣]{2,}(?:시|도)\s*[가-힣]{1,}(?:구|군|시)|[가-힣]{1,}(?:구|군|시)\s*[가-힣]{1,}동|[가-힣]{1,}(?:구|군|시))")
CASE_ANCHOR_PATTERN = re.compile(r"((20\d{2}[가-힣]{1,3}\d{3,6})|(20\d{2}형제\d{3,6})|(20\d{2}조사\d{3,6})|(FR-\d{5}))")
SCAM_ACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"링크[^\n]{0,12}(접속|클릭)"), "링크접속"),
    (re.compile(r"앱\s*설치"), "앱설치"),
    (re.compile(r"인증번호[^\n]{0,12}(불러|제공|읽)"), "인증번호제공"),
    (re.compile(r"원격\s*제어"), "원격제어"),
    (re.compile(r"(이체|송금)[^\n]{0,12}(유도|안내|요구)"), "이체유도"),
)
LEGITIMATE_RESOLUTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"공식\s*앱"), "공식앱확인"),
    (re.compile(r"대표번호"), "대표번호재통화"),
    (re.compile(r"다시\s*걸"), "대표번호재통화"),
    (re.compile(r"영업점\s*방문"), "영업점방문"),
    (re.compile(r"내부\s*검토"), "내부검토대기"),
)
SCAM_SIGNAL_BONUS = 0.5
LEGITIMATE_SIGNAL_PENALTY = 9.0
OPENAI_MIN_REQUEST_INTERVAL_SECONDS = 6.0
_LAST_OPENAI_REQUEST_AT = 0.0
REGION_PREFIXES = (
    "서울",
    "부산",
    "대구",
    "인천",
    "광주",
    "대전",
    "울산",
    "세종",
    "경기",
    "강원",
    "충북",
    "충남",
    "전북",
    "전남",
    "경북",
    "경남",
    "제주",
)


def tokenize(text: str) -> list[str]:
    return [tok for tok in re.split(r"\s+", text.strip()) if tok]


def sample_pattern_family(sample_id: str) -> str:
    return sample_id.split("-", 1)[0] if sample_id else ""


def extract_anchor_terms(text: str) -> list[str]:
    anchors: list[str] = []
    anchors.extend(BANK_NAME_PATTERN.findall(text))
    anchors.extend(match.group(1) for match in NAME_WITH_SUFFIX_PATTERN.finditer(text))
    anchors.extend(match.group(1) for match in ADDRESS_ANCHOR_PATTERN.finditer(text))
    anchors.extend(match.group(1) for match in CASE_ANCHOR_PATTERN.finditer(text))
    anchors.extend(re.findall(r"\[[^\]]+\]", text))
    for pattern, canonical in SCAM_ACTION_PATTERNS:
        if pattern.search(text):
            anchors.append(canonical)
    seen: set[str] = set()
    deduped = []
    for anchor in anchors:
        if not anchor or anchor in seen:
            continue
        seen.add(anchor)
        deduped.append(anchor)
    return deduped


def extract_signal_features(text: str) -> dict[str, list[str]]:
    identifier_anchors = []
    for anchor in extract_anchor_terms(text):
        if re.fullmatch(r"[가-힣]{1,3}시", anchor) and not anchor.startswith(REGION_PREFIXES):
            continue
        identifier_anchors.append(anchor)
    scam_actions: list[str] = []
    legitimate_actions: list[str] = []
    for pattern, canonical in SCAM_ACTION_PATTERNS:
        if pattern.search(text):
            scam_actions.append(canonical)
    for pattern, canonical in LEGITIMATE_RESOLUTION_PATTERNS:
        if pattern.search(text):
            legitimate_actions.append(canonical)
    return {
        "identifier_anchors": identifier_anchors,
        "scam_actions": list(dict.fromkeys(scam_actions)),
        "legitimate_actions": list(dict.fromkeys(legitimate_actions)),
    }


def _format_feature_values(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def build_retrieval_evidence_summary(query_text: str, retrieved_rows: list[dict[str, Any]]) -> str:
    query_features = extract_signal_features(query_text)
    sections = [
        "retrieval evidence summary:",
        f"- query identifiers: {_format_feature_values(query_features['identifier_anchors'])}",
        f"- query scam actions: {_format_feature_values(query_features['scam_actions'])}",
        f"- query legitimate actions: {_format_feature_values(query_features['legitimate_actions'])}",
    ]
    query_identifiers = set(query_features["identifier_anchors"])
    query_scam_actions = set(query_features["scam_actions"])
    query_legitimate_actions = set(query_features["legitimate_actions"])

    for idx, row in enumerate(retrieved_rows, start=1):
        context_features = extract_signal_features(row["scenario_text"])
        context_identifiers = context_features["identifier_anchors"]
        context_scam = context_features["scam_actions"]
        context_legit = context_features["legitimate_actions"]
        matched_identifiers = [item for item in context_identifiers if item in query_identifiers]
        matched_scam = [item for item in context_scam if item in query_scam_actions]
        matched_legit = [item for item in context_legit if item in query_legitimate_actions]
        context_only_scam = [item for item in context_scam if item not in query_scam_actions]
        context_only_legit = [item for item in context_legit if item not in query_legitimate_actions]
        sections.extend(
            [
                f"- context {idx} doc_id: {row.get('doc_id', '') or 'unknown'}",
                f"  - context {idx} matched identifiers: {_format_feature_values(matched_identifiers)}",
                f"  - context {idx} matched scam actions: {_format_feature_values(matched_scam)}",
                f"  - context {idx} matched legitimate actions: {_format_feature_values(matched_legit)}",
                f"  - context {idx} context-only scam actions: {_format_feature_values(context_only_scam)}",
                f"  - context {idx} context-only legitimate actions: {_format_feature_values(context_only_legit)}",
            ]
        )
    return "\n".join(sections)


def build_identifier_filtered_context_blocks(query_text: str, retrieved_rows: list[dict[str, Any]]) -> str:
    filtered_rows = filter_retrieved_rows_by_shared_identifiers(query_text, retrieved_rows)
    query_identifiers = set(extract_signal_features(query_text)["identifier_anchors"])
    context_blocks = []
    for idx, row in enumerate(retrieved_rows, start=1):
        context_identifiers = set(extract_signal_features(row["scenario_text"])["identifier_anchors"])
        if query_identifiers & context_identifiers:
            context_blocks.append(f"Context {idx}:\n{row['scenario_text']}")
        else:
            context_blocks.append(f"Context {idx}: filtered out (no shared identifiers).")
    if not filtered_rows:
        context_blocks.append("No qualifying retrieval evidence remains after identifier filtering.")
    return "\n\n".join(context_blocks)


def filter_retrieved_rows_by_shared_identifiers(query_text: str, retrieved_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_identifiers = set(extract_signal_features(query_text)["identifier_anchors"])
    kept = []
    for row in retrieved_rows:
        context_identifiers = set(extract_signal_features(row["scenario_text"])["identifier_anchors"])
        if query_identifiers & context_identifiers:
            kept.append(row)
    return kept


def build_identifier_filtered_evidence_summary(query_text: str, retrieved_rows: list[dict[str, Any]]) -> str:
    query_features = extract_signal_features(query_text)
    query_identifiers = set(query_features["identifier_anchors"])
    sections = [
        "retrieval evidence summary:",
        f"- query identifiers: {_format_feature_values(query_features['identifier_anchors'])}",
        f"- query scam actions: {_format_feature_values(query_features['scam_actions'])}",
        f"- query legitimate actions: {_format_feature_values(query_features['legitimate_actions'])}",
    ]
    query_scam_actions = set(query_features["scam_actions"])
    query_legitimate_actions = set(query_features["legitimate_actions"])

    for idx, row in enumerate(retrieved_rows, start=1):
        context_features = extract_signal_features(row["scenario_text"])
        context_identifiers = context_features["identifier_anchors"]
        matched_identifiers = [item for item in context_identifiers if item in query_identifiers]
        if not matched_identifiers:
            sections.extend(
                [
                    f"- context {idx} doc_id: {row.get('doc_id', '') or 'unknown'}",
                    f"  - context {idx} filtered out: no shared identifiers",
                ]
            )
            continue
        context_scam = context_features["scam_actions"]
        context_legit = context_features["legitimate_actions"]
        matched_scam = [item for item in context_scam if item in query_scam_actions]
        matched_legit = [item for item in context_legit if item in query_legitimate_actions]
        context_only_scam = [item for item in context_scam if item not in query_scam_actions]
        context_only_legit = [item for item in context_legit if item not in query_legitimate_actions]
        sections.extend(
            [
                f"- context {idx} doc_id: {row.get('doc_id', '') or 'unknown'}",
                f"  - context {idx} matched identifiers: {_format_feature_values(matched_identifiers)}",
                f"  - context {idx} matched scam actions: {_format_feature_values(matched_scam)}",
                f"  - context {idx} matched legitimate actions: {_format_feature_values(matched_legit)}",
                f"  - context {idx} context-only scam actions: {_format_feature_values(context_only_scam)}",
                f"  - context {idx} context-only legitimate actions: {_format_feature_values(context_only_legit)}",
            ]
        )
    return "\n".join(sections)


def build_search_text(text: str) -> str:
    cleaned = text
    for pattern in GENERIC_PHRASE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned)
    base_tokens = [token for token in SEARCH_TOKEN_RE.findall(cleaned) if token not in TOKEN_STOPWORDS]
    anchors = extract_anchor_terms(text)
    return " ".join(base_tokens + anchors + anchors)


def compute_query_signal_adjustment(query_text: str) -> float:
    adjustment = 0.0
    for pattern, _canonical in SCAM_ACTION_PATTERNS:
        if pattern.search(query_text):
            adjustment += SCAM_SIGNAL_BONUS
    for pattern, _canonical in LEGITIMATE_RESOLUTION_PATTERNS:
        if pattern.search(query_text):
            adjustment -= LEGITIMATE_SIGNAL_PENALTY
    return adjustment


@dataclass
class BM25Hit:
    doc: dict[str, Any]
    score: float


class BM25Index:
    def __init__(self, documents: list[dict[str, Any]], text_key: str = "text") -> None:
        self.documents = documents
        self.text_key = text_key
        self.doc_tokens = [tokenize(str(doc[text_key])) for doc in documents]
        self.doc_freqs: list[Counter[str]] = [Counter(tokens) for tokens in self.doc_tokens]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lens) / max(len(self.doc_lens), 1)
        self.term_doc_counts: Counter[str] = Counter()
        for freqs in self.doc_freqs:
            for term in freqs:
                self.term_doc_counts[term] += 1

    @classmethod
    def from_documents(cls, documents: list[dict[str, Any]], text_key: str = "text") -> "BM25Index":
        return cls(documents=documents, text_key=text_key)

    def _idf(self, term: str) -> float:
        n_docs = len(self.documents)
        doc_count = self.term_doc_counts.get(term, 0)
        return math.log(1 + (n_docs - doc_count + 0.5) / (doc_count + 0.5))

    def search(self, query: str, top_k: int = 3, k1: float = 1.5, b: float = 0.75) -> list[dict[str, Any]]:
        query_terms = tokenize(query)
        hits: list[BM25Hit] = []
        for doc, freqs, doc_len in zip(self.documents, self.doc_freqs, self.doc_lens):
            score = 0.0
            for term in query_terms:
                tf = freqs.get(term, 0)
                if tf == 0:
                    continue
                idf = self._idf(term)
                denom = tf + k1 * (1 - b + b * (doc_len / max(self.avg_doc_len, 1e-9)))
                score += idf * ((tf * (k1 + 1)) / denom)
            hits.append(BM25Hit(doc=doc, score=score))
        hits.sort(key=lambda x: x.score, reverse=True)
        return [{"doc": hit.doc, "score": hit.score} for hit in hits[:top_k]]


def summarize_results(rows: list[dict[str, str]]) -> dict[str, Any]:
    total = len(rows)
    correct = sum(1 for row in rows if row["ground_truth"] == row["prediction"])
    by_source: dict[str, dict[str, float]] = {}
    grouped: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["source_type"]].append(row)
    for source, source_rows in grouped.items():
        source_correct = sum(1 for row in source_rows if row["ground_truth"] == row["prediction"])
        by_source[source] = {
            "count": len(source_rows),
            "accuracy": source_correct / len(source_rows),
        }
    return {
        "count": total,
        "overall_accuracy": correct / total if total else 0.0,
        "by_source": by_source,
    }


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


RESULT_FIELDS = [
    "qa_id",
    "source_type",
    "source_sample_id",
    "ground_truth",
    "prediction",
    "raw_output",
    "retrieved_doc_ids",
    "retrieved_scores",
    "top_retrieved_doc_id",
    "top_retrieved_family",
    "same_family_hit",
    "top_score_margin",
    "retrieval_regime",
    "prompt",
]


def build_prompt(
    question: str,
    scenario_text: str,
    retrieved_rows: list[dict[str, Any]],
    prompt_mode: str = "similarity",
) -> str:
    context_blocks = []
    for idx, row in enumerate(retrieved_rows, start=1):
        context_blocks.append(f"Context {idx}:\n{row['scenario_text']}")
    joined_context = "\n\n".join(context_blocks)
    filtered_joined_context = build_identifier_filtered_context_blocks(scenario_text, retrieved_rows)
    evidence_summary = build_retrieval_evidence_summary(scenario_text, retrieved_rows)
    filtered_evidence_summary = build_identifier_filtered_evidence_summary(scenario_text, retrieved_rows)
    if prompt_mode == "evidence":
        return (
            "질문 대상 대화와 검색 결과를 함께 보고 판단하라.\n"
            "대화 원문 자체와 검색 결과에 나타난 증거를 기준으로 yes 또는 no만 답하라.\n"
            "검색 결과에서 사기 전용 행동이 확인되면 yes 쪽으로 강하게 본다.\n"
            "사기 전용 행동의 예: 앱 설치, 링크 접속/클릭 유도, 인증번호 제공 요구, 원격 제어, 제3자 송금/이체 유도.\n"
            "반대로 공식 앱에서 직접 확인, 대표번호로 다시 걸기, 영업점 방문, 내부 검토 대기 같은 정상 해결 경로만 보이면 no 쪽으로 본다.\n"
            "분위기만 비슷한 것은 증거가 아니다.\n"
            "애매하면 no라고 답하라.\n"
            "반드시 yes 또는 no만 출력하라.\n\n"
            f"질문 대상 대화:\n{scenario_text}\n\n"
            f"{joined_context}\n\n"
            f"질문:\n{question}"
        )
    if prompt_mode == "retrieval-gated":
        return (
            "너는 retrieval-augmented 보이스피싱 판정기다.\n"
            "질문 대상 대화만 보고 추정하지 마라. query-only 직감으로 yes를 주면 안 된다.\n"
            "반드시 검색 결과(context)에서 support, contradiction, insufficient evidence를 비교한 뒤 yes 또는 no만 답하라.\n"
            "support는 질문 대상 대화의 핵심 식별 단서나 사기 실행 단서가 검색 결과에서 실제로 뒷받침되는 경우다.\n"
            "contradiction은 검색 결과가 정상 해결 경로(공식 앱 확인, 대표번호 재통화, 영업점 방문, 내부 검토 대기)를 더 강하게 지지하는 경우다.\n"
            "insufficient evidence는 검색 결과가 질문 대상 대화의 핵심 단서를 충분히 지지하지 못하는 경우다.\n"
            "규칙:\n"
            "- query 자체가 수상해 보여도 retrieval support가 약하면 no라고 답하라.\n"
            "- 검색 결과가 정상 해결 경로를 더 강하게 보여주면 no라고 답하라.\n"
            "- 검색 결과에 질문 대상 대화와 겹치는 식별 단서 + 사기 실행 단서가 함께 있으면 yes 쪽으로 보라.\n"
            "- 애매하면 no라고 답하라.\n"
            "- 설명하지 말고 yes 또는 no만 출력하라.\n\n"
            f"{evidence_summary}\n\n"
            f"질문 대상 대화:\n{scenario_text}\n\n"
            f"{joined_context}\n\n"
            f"질문:\n{question}"
        )
    if prompt_mode == "retrieval-flow":
        return (
            "너는 retrieval-augmented 보이스피싱 판정기다.\n"
            "질문 대상 대화만 보고 추정하지 마라.\n"
            "현재 대화와 검색 결과를 함께 보고, 절차 흐름이 같은 보이스피싱 패턴으로 이어지는지 판단하라.\n"
            "대화가 아직 중간 단계에서 끝났더라도, retrieved contexts가 later scam continuation을 강하게 보여주면 yes를 줄 수 있다.\n"
            "later scam continuation은 보호 절차/본인 확인/이상거래 점검으로 시작한 뒤 링크 접속, 앱 설치, 인증번호 제공, 원격 제어, 송금 유도로 이어지는 패턴이다.\n"
            "partial identifier overlap 또는 같은 절차 흐름은 support가 될 수 있다.\n"
            "하지만 검색 결과가 정상 해결 경로를 더 강하게 보여주면 no라고 답하라.\n"
            "generic banking overlap만 있고 later scam continuation support가 약하면 no라고 답하라.\n"
            "설명하지 말고 yes 또는 no만 출력하라.\n\n"
            f"{evidence_summary}\n\n"
            f"질문 대상 대화:\n{scenario_text}\n\n"
            f"{joined_context}\n\n"
            f"질문:\n{question}"
        )
    if prompt_mode == "retrieval-anchor-flow":
        return (
            "너는 retrieval-augmented 보이스피싱 판정기다.\n"
            "질문 대상 대화만 보고 추정하지 마라.\n"
            "현재 대화와 검색 결과를 함께 보고, shared identifier anchor + later scam continuation이 함께 보이는지 판단하라.\n"
            "shared identifier anchor는 은행명, 이름, 주소, 사건번호, 접수번호처럼 query와 retrieval이 함께 갖는 식별 단서다.\n"
            "later scam continuation은 보호 절차/본인 확인/이상거래 점검으로 시작한 뒤 링크 접속, 앱 설치, 인증번호 제공, 원격 제어, 송금 유도로 이어지는 패턴이다.\n"
            "대화가 아직 중간 단계에서 끝났더라도, shared identifier anchor가 있고 retrieval이 later scam continuation을 강하게 보여주면 yes를 줄 수 있다.\n"
            "generic banking similarity만 있으면 no라고 답하라.\n"
            "검색 결과가 정상 해결 경로를 더 강하게 보여주면 no라고 답하라.\n"
            "설명하지 말고 yes 또는 no만 출력하라.\n\n"
            f"{evidence_summary}\n\n"
            f"질문 대상 대화:\n{scenario_text}\n\n"
            f"{joined_context}\n\n"
            f"질문:\n{question}"
        )
    if prompt_mode == "summary-gated":
        return (
            "너는 retrieval evidence summary만 보고 보이스피싱 여부를 판단하는 심사자다.\n"
            "raw context 본문은 의도적으로 숨겨져 있다. summary에 적힌 evidence만 사용하라.\n"
            "yes 조건:\n"
            "- matched identifiers가 존재한다.\n"
            "- 그리고 retrieval summary가 later scam continuation(앱 설치, 링크 접속, 인증번호 제공, 원격 제어, 송금 유도)을 보여준다.\n"
            "no 조건:\n"
            "- matched identifiers가 없고 context-only scam actions만 있다.\n"
            "- 또는 정상 해결 경로가 더 강하다.\n"
            "- 또는 generic banking similarity만 있다.\n"
            "애매하면 no라고 답하라.\n"
            "설명하지 말고 yes 또는 no만 출력하라.\n\n"
            f"{evidence_summary}\n\n"
            f"질문 대상 대화:\n{scenario_text}\n\n"
            f"질문:\n{question}"
        )
    if prompt_mode == "identifier-filtered-flow":
        filtered_rows = filter_retrieved_rows_by_shared_identifiers(scenario_text, retrieved_rows)
        if not filtered_rows:
            return (
                "너는 retrieval-augmented 보이스피싱 판정기다.\n"
                "No qualifying retrieval evidence remains after identifier filtering.\n"
                "즉 검색 결과 중 query와 shared identifier를 가진 증거가 하나도 남지 않았다.\n"
                "이 정책에서는 이런 경우 query 자체가 수상해 보여도 no로 답한다.\n"
                "설명하지 말고 no만 출력하라."
            )
        return (
            "너는 retrieval-augmented 보이스피싱 판정기다.\n"
            "shared identifier가 없는 context는 숨긴다. 보이는 context와 evidence summary만 사용하라.\n"
            "질문 대상 대화가 아직 중간 단계에서 끝났더라도, 보이는 context가 later scam continuation을 보여주면 yes를 줄 수 있다.\n"
            "하지만 generic banking overlap만 있거나 모든 context가 filtered out 되면 no라고 답하라.\n"
            "정상 해결 경로가 더 강해도 no라고 답하라.\n"
            "설명하지 말고 yes 또는 no만 출력하라.\n\n"
            f"{filtered_evidence_summary}\n\n"
            f"질문 대상 대화:\n{scenario_text}\n\n"
            f"{filtered_joined_context}\n\n"
            f"질문:\n{question}"
        )
    return (
        "질문 대상 대화와 검색 결과를 함께 보고 판단하라.\n"
        "질문 대상 대화가 검색 결과와 70% 이상 유사할 때만 yes라고 답하라.\n"
        "핵심 행위, 진행 흐름, 식별 단서가 대부분 겹칠 때만 yes라고 답하라.\n"
        "조금 비슷하거나 분위기만 비슷하면 no라고 답하라.\n"
        "애매하면 no라고 답하라.\n"
        "반드시 yes 또는 no만 출력하라.\n\n"
        f"질문 대상 대화:\n{scenario_text}\n\n"
        f"{joined_context}\n\n"
        "질문:\n질문 대상 대화가 검색 결과와 대략 70% 이상 유사하면 yes, 아니면 no."
    )


def filter_retrieval_hits(
    hits: list[dict[str, Any]],
    source_sample_id: str,
    exclude_same_sample: bool = False,
    exclude_same_pattern: bool = False,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    family = sample_pattern_family(source_sample_id)
    filtered = []
    for hit in hits:
        doc_id = hit["doc"].get("doc_id", "")
        if exclude_same_sample and doc_id == source_sample_id:
            continue
        if exclude_same_pattern and family and sample_pattern_family(doc_id) == family:
            continue
        filtered.append(hit)
        if top_k is not None and len(filtered) >= top_k:
            break
    return filtered


def resolve_retrieval_exclusions(
    retrieval_regime: str,
    exclude_same_sample: bool,
    exclude_same_pattern: bool,
) -> tuple[bool, bool]:
    if retrieval_regime == "realistic":
        return True, False
    if retrieval_regime == "strict":
        return True, True
    return exclude_same_sample, exclude_same_pattern


def build_retrieval_metadata(
    hits: list[dict[str, Any]],
    source_sample_id: str,
    retrieval_regime: str,
) -> dict[str, str]:
    if not hits:
        return {
            "top_retrieved_doc_id": "",
            "top_retrieved_family": "",
            "same_family_hit": "no",
            "top_score_margin": "0.000000",
            "retrieval_regime": retrieval_regime,
        }
    top_doc_id = hits[0]["doc"].get("doc_id", "")
    top_family = sample_pattern_family(top_doc_id)
    source_family = sample_pattern_family(source_sample_id)
    top_score = float(hits[0]["score"])
    second_score = float(hits[1]["score"]) if len(hits) > 1 else 0.0
    return {
        "top_retrieved_doc_id": top_doc_id,
        "top_retrieved_family": top_family,
        "same_family_hit": "yes" if top_family and top_family == source_family else "no",
        "top_score_margin": f"{top_score - second_score:.6f}",
        "retrieval_regime": retrieval_regime,
    }


def predict_with_bm25_threshold(hits: list[dict[str, Any]], yes_threshold: float) -> tuple[str, str]:
    top_score = float(hits[0]["score"]) if hits else 0.0
    prediction = "yes" if top_score >= yes_threshold else "no"
    return prediction, f"bm25:{top_score:.6f}"


def compute_threshold_score(query_text: str, hits: list[dict[str, Any]]) -> tuple[float, str]:
    top_score = float(hits[0]["score"]) if hits else 0.0
    adjustment = compute_query_signal_adjustment(query_text)
    final_score = top_score + adjustment
    return final_score, f"bm25:{top_score:.6f}|adj:{adjustment:.6f}|score:{final_score:.6f}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = {
        "evaluate",
        "submit-batch",
        "batch-status",
        "fetch-batch-results",
        "merge-batch-results",
    }
    if argv and (argv[0].startswith("-") or argv[0] not in commands):
        argv = ["evaluate", *argv]
    if not argv:
        argv = ["evaluate"]

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    eval_parser = subparsers.add_parser("evaluate")
    eval_parser.add_argument("--corpus", required=True)
    eval_parser.add_argument("--qa", required=True)
    eval_parser.add_argument("--top-k", type=int, default=3)
    eval_parser.add_argument("--output")
    eval_parser.add_argument("--model")
    eval_parser.add_argument("--limit", type=int)
    eval_parser.add_argument("--dry-run", action="store_true")
    eval_parser.add_argument("--exclude-same-sample", action="store_true")
    eval_parser.add_argument("--exclude-same-pattern", action="store_true")
    eval_parser.add_argument(
        "--retrieval-regime",
        choices=["custom", "realistic", "strict"],
        default="custom",
    )
    eval_parser.add_argument("--decision-mode", choices=["llm", "bm25-threshold"], default="llm")
    eval_parser.add_argument(
        "--prompt-mode",
        choices=[
            "similarity",
            "evidence",
            "retrieval-gated",
            "retrieval-flow",
            "retrieval-anchor-flow",
            "summary-gated",
            "identifier-filtered-flow",
        ],
        default="similarity",
    )
    eval_parser.add_argument("--yes-threshold", type=float, default=0.0)

    submit_parser = subparsers.add_parser("submit-batch")
    submit_parser.add_argument("--retrieval-csv", required=True)
    submit_parser.add_argument("--model", required=True)
    submit_parser.add_argument("--output-meta")

    status_parser = subparsers.add_parser("batch-status")
    status_parser.add_argument("--batch-id", required=True)

    fetch_parser = subparsers.add_parser("fetch-batch-results")
    fetch_parser.add_argument("--results-url", required=True)
    fetch_parser.add_argument("--output-jsonl", required=True)

    merge_parser = subparsers.add_parser("merge-batch-results")
    merge_parser.add_argument("--retrieval-csv", required=True)
    merge_parser.add_argument("--results-jsonl", required=True)
    merge_parser.add_argument("--output-csv", required=True)

    return parser.parse_args(argv)


def build_default_output_path(corpus_path: str | Path) -> str:
    corpus_name = Path(corpus_path).stem
    return str(Path("data") / f"naive_rag_{corpus_name}_results.csv")


def normalize_prediction(text: str) -> str:
    value = text.strip().lower()
    if value.startswith("yes"):
        return "yes"
    if value.startswith("no"):
        return "no"
    return "unknown"


def anthropic_headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def openai_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def load_anthropic_api_key(dotenv_path: str | Path = ".env") -> str | None:
    env_value = os.environ.get("ANTHROPIC_API_KEY")
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
        if key.strip() == "ANTHROPIC_API_KEY":
            return value.strip().strip('"').strip("'")
    return None


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


def is_openai_model(model: str) -> bool:
    return model.startswith("gpt-")


def build_query_text(row: dict[str, str]) -> str:
    return build_search_text(row["scenario_text"])


def corpus_rows_to_indexable(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "doc_id": row.get("sample_id") or row.get("source_sample_id") or "",
            "scenario_text": row["scenario_text"],
            "search_text": build_search_text(row["scenario_text"]),
        }
        for row in rows
    ]


def existing_result_ids(path: str | Path) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    with p.open(encoding="utf-8", newline="") as f:
        return {row["qa_id"] for row in csv.DictReader(f)}


def build_message_batch_requests(retrieval_rows: list[dict[str, str]], model: str) -> list[dict[str, Any]]:
    requests = []
    for row in retrieval_rows:
        requests.append(
            {
                "custom_id": row["qa_id"],
                "params": {
                    "model": model,
                    "max_tokens": 10,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": row["prompt"]}],
                },
            }
        )
    return requests


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    global _LAST_OPENAI_REQUEST_AT
    body = json.dumps(payload).encode("utf-8")
    if "api.openai.com" in url:
        elapsed = time.time() - _LAST_OPENAI_REQUEST_AT
        if elapsed < OPENAI_MIN_REQUEST_INTERVAL_SECONDS:
            time.sleep(OPENAI_MIN_REQUEST_INTERVAL_SECONDS - elapsed)
    for attempt in range(10):
        request = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                if "api.openai.com" in url:
                    _LAST_OPENAI_REQUEST_AT = time.time()
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 9:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            try:
                delay = max(float(retry_after), 0.0) if retry_after is not None else 0.0
            except ValueError:
                delay = 0.0
            time.sleep(max(delay, min(5 * (attempt + 1), 60)))
    raise RuntimeError("unreachable")


def get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def get_text(url: str, headers: dict[str, str]) -> str:
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8")


def submit_anthropic_batch(retrieval_csv: str | Path, model: str, output_meta: str | Path | None = None) -> dict[str, Any]:
    api_key = load_anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    rows = read_csv_rows(retrieval_csv)
    payload = {"requests": build_message_batch_requests(rows, model=model)}
    data = post_json("https://api.anthropic.com/v1/messages/batches", payload, anthropic_headers(api_key))
    if output_meta:
        Path(output_meta).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def retrieve_anthropic_batch(batch_id: str) -> dict[str, Any]:
    api_key = load_anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return get_json(f"https://api.anthropic.com/v1/messages/batches/{batch_id}", anthropic_headers(api_key))


def download_anthropic_batch_results(results_url: str, output_path: str | Path) -> list[dict[str, Any]]:
    api_key = load_anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    text = get_text(results_url, anthropic_headers(api_key))
    Path(output_path).write_text(text, encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def batch_result_text(result_line: dict[str, Any]) -> str:
    result = result_line.get("result", {})
    if result.get("type") != "succeeded":
        response = result_line.get("response", {})
        if response.get("status_code") != 200:
            return ""
        body = response.get("body", {})
        texts = []
        for item in body.get("output", []):
            for block in item.get("content", []):
                if block.get("type") == "output_text":
                    texts.append(block.get("text", ""))
        return "".join(texts).strip()

    message = result.get("message", {})
    texts = []
    for block in message.get("content", []):
        if block.get("type") == "text":
            texts.append(block.get("text", ""))
    return "".join(texts).strip()


def merge_batch_predictions(retrieval_rows: list[dict[str, str]], result_lines: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_id = {line["custom_id"]: line for line in result_lines}
    merged = []
    for row in retrieval_rows:
        line = by_id.get(row["qa_id"], {})
        raw_output = batch_result_text(line)
        merged_row = dict(row)
        merged_row["raw_output"] = raw_output
        merged_row["prediction"] = normalize_prediction(raw_output)
        merged.append(merged_row)
    return merged


def append_result_row(path: str | Path, row: dict[str, str]) -> None:
    p = Path(path)
    write_header = not p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def call_model(prompt: str, model: str) -> str:
    if is_openai_model(model):
        api_key = load_openai_api_key()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                }
            ],
            "max_output_tokens": 20,
        }
        data = post_json("https://api.openai.com/v1/responses", payload, openai_headers(api_key))
        output_text = data.get("output_text")
        if output_text:
            return str(output_text).strip()
        texts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    texts.append(text)
        return "".join(texts).strip()

    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic package is required for non-dry-run evaluation") from exc

    api_key = load_anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    chunks = []
    for block in message.content:
        text = getattr(block, "text", "")
        if text:
            chunks.append(text)
    return "".join(chunks).strip()


def evaluate(
    corpus_path: str | Path,
    qa_path: str | Path,
    top_k: int = 3,
    model: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    output_path: str | Path | None = None,
    progress_every: int = 25,
    exclude_same_sample: bool = False,
    exclude_same_pattern: bool = False,
    retrieval_regime: str = "custom",
    decision_mode: str = "llm",
    prompt_mode: str = "similarity",
    yes_threshold: float = 0.0,
) -> list[dict[str, str]]:
    corpus_rows = corpus_rows_to_indexable(read_csv_rows(corpus_path))
    qa_rows = read_csv_rows(qa_path)
    if limit is not None:
        qa_rows = qa_rows[:limit]

    index = BM25Index.from_documents(corpus_rows, text_key="search_text")
    completed_ids = existing_result_ids(output_path) if output_path else set()
    results: list[dict[str, str]] = []
    processed = 0
    exclude_same_sample, exclude_same_pattern = resolve_retrieval_exclusions(
        retrieval_regime,
        exclude_same_sample,
        exclude_same_pattern,
    )

    for row in qa_rows:
        if row["qa_id"] in completed_ids:
            continue
        hits = index.search(build_query_text(row), top_k=len(corpus_rows))
        hits = filter_retrieval_hits(
            hits,
            source_sample_id=row["source_sample_id"],
            exclude_same_sample=exclude_same_sample,
            exclude_same_pattern=exclude_same_pattern,
            top_k=top_k,
        )
        retrieval_metadata = build_retrieval_metadata(
            hits,
            source_sample_id=row["source_sample_id"],
            retrieval_regime=retrieval_regime,
        )
        prompt = build_prompt(
            row["question"],
            row["scenario_text"],
            [hit["doc"] for hit in hits],
            prompt_mode=prompt_mode,
        )
        if dry_run:
            prediction = "dry_run"
            raw_output = ""
        elif decision_mode == "bm25-threshold":
            final_score, raw_output = compute_threshold_score(row["scenario_text"], hits)
            prediction = "yes" if final_score >= yes_threshold else "no"
        else:
            if not model:
                raise ValueError("--model is required unless --dry-run is used")
            raw_output = call_model(prompt, model)
            prediction = normalize_prediction(raw_output)

        result_row = {
            "qa_id": row["qa_id"],
            "source_type": row["source_type"],
            "source_sample_id": row["source_sample_id"],
            "ground_truth": row["ground_truth"],
            "prediction": prediction,
            "raw_output": raw_output,
            "retrieved_doc_ids": "|".join(hit["doc"]["doc_id"] for hit in hits),
            "retrieved_scores": "|".join(f"{hit['score']:.6f}" for hit in hits),
            **retrieval_metadata,
            "prompt": prompt,
        }
        results.append(result_row)
        if output_path:
            append_result_row(output_path, result_row)
        processed += 1
        if processed % progress_every == 0:
            print(json.dumps({"processed": processed, "last_qa_id": row["qa_id"]}, ensure_ascii=False))
    return results


def write_results(path: str | Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict[str, str]], dry_run: bool) -> None:
    if dry_run:
        payload = {
            "count": len(rows),
            "mode": "dry_run",
            "sample_prompt_preview": rows[0]["prompt"] if rows else "",
        }
    else:
        payload = summarize_results(rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "evaluate":
        output_path = args.output or build_default_output_path(args.corpus)
        rows = evaluate(
            corpus_path=args.corpus,
            qa_path=args.qa,
            top_k=args.top_k,
            model=args.model,
            limit=args.limit,
            dry_run=args.dry_run,
            output_path=output_path,
            exclude_same_sample=args.exclude_same_sample,
            exclude_same_pattern=args.exclude_same_pattern,
            retrieval_regime=args.retrieval_regime,
            decision_mode=args.decision_mode,
            prompt_mode=args.prompt_mode,
            yes_threshold=args.yes_threshold,
        )
        if not rows and Path(output_path).exists():
            rows = read_csv_rows(output_path)
        print_summary(rows, dry_run=args.dry_run)
        return 0

    if args.command == "submit-batch":
        meta = submit_anthropic_batch(args.retrieval_csv, args.model, args.output_meta)
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0

    if args.command == "batch-status":
        status = retrieve_anthropic_batch(args.batch_id)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0

    if args.command == "fetch-batch-results":
        lines = download_anthropic_batch_results(args.results_url, args.output_jsonl)
        print(json.dumps({"count": len(lines), "output_jsonl": args.output_jsonl}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "merge-batch-results":
        retrieval_rows = read_csv_rows(args.retrieval_csv)
        result_lines = [json.loads(line) for line in Path(args.results_jsonl).read_text(encoding="utf-8").splitlines() if line.strip()]
        merged = merge_batch_predictions(retrieval_rows, result_lines)
        write_results(args.output_csv, merged)
        print(json.dumps(summarize_results(merged), ensure_ascii=False, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
