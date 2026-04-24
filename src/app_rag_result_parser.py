# -*- coding: utf-8 -*-
"""Helpers for parsing RAG text into display-ready fragments."""

from __future__ import annotations

import re
from typing import Any


def clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def normalize_sentence(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -•\n\t\"'")


def normalize_section_name(section_name: str) -> str:
    key = clean_text(section_name).replace(" ", "")
    alias_map = {
        "상황요약": "상황 요약",
        "감정": "감정",
        "위험도": "위험도",
        "공감형": "공감형",
        "조언형": "조언형",
        "갈등완충형": "갈등 완충형",
        "완화형": "갈등 완충형",
        "비난회피형": "갈등 완충형",
        "피해야할표현": "피해야 할 표현",
        "대체표현": "대체 표현",
    }
    return alias_map.get(key, clean_text(section_name))


def parse_section(text: str, section_name: str) -> str:
    if not text:
        return ""

    normalized_target = normalize_section_name(section_name)

    candidate_labels = [
        "상황 요약", "상황요약",
        "감정",
        "위험도",
        "공감형",
        "조언형",
        "갈등 완충형", "갈등완충형",
        "완화형",
        "비난 회피형", "비난회피형",
        "피해야 할 표현", "피해야할표현",
        "대체 표현", "대체표현",
        "추천 답변 1", "추천 답변 2", "추천 답변 3",
    ]

    pattern = (
        r"\[\s*(" + "|".join(map(re.escape, candidate_labels)) + r")\s*\]\s*(.*?)"
        r"(?=\n\s*\[\s*(?:" + "|".join(map(re.escape, candidate_labels)) + r")\s*\]|\Z)"
    )
    matches = re.findall(pattern, text, flags=re.DOTALL)

    for raw_label, body in matches:
        if normalize_section_name(raw_label) == normalized_target:
            return clean_text(body)

    return ""


def split_lines(block_text: str) -> list[str]:
    if not block_text:
        return []

    results = []
    for line in block_text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[\-\*\•]\s*", "", line)
        line = re.sub(r"^\d+\.\s*", "", line)
        results.append(line)

    return results


def is_question_sentence(text: str) -> bool:
    text = normalize_sentence(text)
    return (
        text.endswith("?")
        or text.endswith("까?")
        or text.endswith("나요?")
        or text.endswith("을까?")
        or text.endswith("니?")
    )


def looks_like_metadata_block(text: str) -> bool:
    text = clean_text(text)
    metadata_keywords = [
        "관계:",
        "상황:",
        "화자 감정:",
        "응답 직전 문맥:",
        "추천 가능한 청자 응답 예시:",
        "응답 공감 유형:",
        "대화 종료 여부:",
        "[응답 예시",
        "dialogue_id:",
        "[유사 사례",
    ]
    hit_count = sum(1 for kw in metadata_keywords if kw in text)
    if hit_count >= 2:
        return True
    if "\n" in text and hit_count >= 1:
        return True
    return False


def is_valid_reply_candidate(text: str) -> bool:
    text = normalize_sentence(text)
    if not text:
        return False
    if len(text) < 8:
        return False
    if len(text) > 240:
        return False
    if looks_like_metadata_block(text):
        return False
    return True


def extract_example_reply_candidates(text: str) -> list[str]:
    if not text:
        return []

    candidates = []
    matches = re.findall(
        r"추천 가능한 청자 응답 예시:\s*(.*?)(?=\n(?:응답 공감 유형|대화 종료 여부|관계:|상황:|화자 감정:|응답 직전 문맥:)|\Z)",
        text,
        flags=re.DOTALL,
    )

    for match in matches:
        candidate = normalize_sentence(match)
        if is_valid_reply_candidate(candidate) and candidate not in candidates:
            candidates.append(candidate)

    return candidates


def extract_quoted_candidates(text: str) -> list[str]:
    if not text:
        return []

    candidates = []
    quoted = re.findall(r'"([^"]{8,240})"|\'([^\']{8,240})\'', text)

    for double_q, single_q in quoted:
        q = normalize_sentence(double_q or single_q)
        if is_valid_reply_candidate(q) and q not in candidates:
            candidates.append(q)

    return candidates


def extract_reply_candidates(result_text: str, fallback_examples: str) -> list[str]:
    candidates: list[str] = []

    # 최신 태그 우선
    for section_name in ["공감형", "조언형", "갈등 완충형"]:
        value = parse_section(result_text, section_name)
        value = normalize_sentence(value)
        formatted = f"[{section_name}] {value}" if value else ""
        if is_valid_reply_candidate(value) and formatted not in candidates:
            candidates.append(formatted)

    if candidates:
        return candidates[:3]

    # 예전 태그 fallback
    for section_name in ["공감형", "완화형", "비난 회피형"]:
        value = parse_section(result_text, section_name)
        value = normalize_sentence(value)
        normalized_name = normalize_section_name(section_name)
        formatted = f"[{normalized_name}] {value}" if value else ""
        if is_valid_reply_candidate(value) and formatted not in candidates:
            candidates.append(formatted)

    if candidates:
        return candidates[:3]

    for section_name in ["추천 답변 1", "추천 답변 2", "추천 답변 3"]:
        value = parse_section(result_text, section_name)
        value = normalize_sentence(value)
        if is_valid_reply_candidate(value) and value not in candidates:
            candidates.append(value)

    for source_text in [result_text, fallback_examples]:
        extracted = extract_example_reply_candidates(source_text)
        for item in extracted:
            if item not in candidates:
                candidates.append(item)
            if len(candidates) >= 3:
                return candidates[:3]

    for source_text in [result_text, fallback_examples]:
        quoted = extract_quoted_candidates(source_text)
        for item in quoted:
            if item not in candidates:
                candidates.append(item)
            if len(candidates) >= 3:
                return candidates[:3]

    return candidates[:3]


def split_phrase_candidates(block_text: str) -> list[str]:
    """
    피해야 할 표현 / 대체 표현 같은 블록을
    1표현 = 1문자열 형태로 최대한 잘게 분리한다.
    """
    text = clean_text(block_text)
    if not text:
        return []

    candidates: list[str] = []

    # 1) 따옴표 안 표현 우선 추출
    quoted_matches = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
    for double_q, single_q in quoted_matches:
        item = normalize_sentence(double_q or single_q)
        if item and item not in candidates:
            candidates.append(item)

    if candidates:
        return candidates

    # 2) 줄 단위 분리
    lines = split_lines(text)
    if len(lines) > 1:
        for line in lines:
            item = normalize_sentence(line)
            if item and item not in candidates:
                candidates.append(item)
        if candidates:
            return candidates

    # 3) 쉼표 기준 분리
    comma_parts = re.split(r"\s*,\s*", text)
    if len(comma_parts) > 1:
        for part in comma_parts:
            item = normalize_sentence(part)
            if item and item not in candidates:
                candidates.append(item)
        if candidates:
            return candidates

    # 4) 문장 종결부호 기준 분리
    sentence_parts = re.split(r"(?<=[.!?])\s+", text)
    if len(sentence_parts) > 1:
        for part in sentence_parts:
            item = normalize_sentence(part)
            if item and item not in candidates:
                candidates.append(item)
        if candidates:
            return candidates

    single = normalize_sentence(text)
    return [single] if single else []


def parse_list_block(block_text: str, allow_questions: bool = False) -> list[str]:
    if not block_text:
        return []

    raw_items = split_phrase_candidates(block_text)

    cleaned: list[str] = []
    for item in raw_items:
        normalized = normalize_sentence(item)
        if not normalized:
            continue
        if looks_like_metadata_block(normalized):
            continue
        if not allow_questions and is_question_sentence(normalized):
            continue
        if normalized not in cleaned:
            cleaned.append(normalized)

    return cleaned[:3]
