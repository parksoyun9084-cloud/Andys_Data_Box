# -*- coding: utf-8 -*-
"""Build the app-facing payload from emotion/risk and RAG outputs."""

from __future__ import annotations

from src.app_rag_result_parser import (
    clean_text,
    extract_reply_candidates,
    normalize_sentence,
    parse_list_block,
    parse_section,
)


def _safe_int_percent(value, default: int = 0) -> int:
    try:
        return max(0, min(int(float(value) * 100), 100))
    except Exception:
        return default


def normalize_emotion_label(label: str) -> str:
    mapping = {
        "neutral": "중립",
        "sadness": "슬픔",
        "anger": "분노",
        "fear": "불안",
        "joy": "행복",
        "surprise": "놀람",
        "disgust": "혐오",
    }
    label = clean_text(label)
    return mapping.get(label.lower(), label) if label else "미분석"


def normalize_risk_label(label: str) -> str:
    mapping = {
        "normal": "보통",
        "low": "안전",
        "medium": "주의",
        "high": "위험",
        "critical": "심각",
    }
    label = clean_text(label)
    return mapping.get(label.lower(), label) if label else "미분석"


def extract_emotion_score(emotion_dict: dict, dominant: str) -> int:
    """
    negative_ratio만 쓰면 중립일 때 0%가 자주 떠서 UX가 어색하므로,
    confidence 계열 값이 있으면 우선 사용하고, 없으면 fallback을 준다.
    """
    utterance_results = emotion_dict.get("utterance_results", [])
    if utterance_results and isinstance(utterance_results, list):
        first_item = utterance_results[0]
        if isinstance(first_item, dict):
            for key in ["confidence", "score", "probability", "primary_confidence"]:
                if key in first_item:
                    try:
                        val = float(first_item[key])
                        if 0 <= val <= 1:
                            return max(0, min(int(val * 100), 100))
                        if 0 <= val <= 100:
                            return max(0, min(int(val), 100))
                    except Exception:
                        pass

    negative_ratio = emotion_dict.get("negative_ratio", None)
    if negative_ratio is not None:
        score = _safe_int_percent(negative_ratio, default=0)
        if score > 0:
            return score

    if dominant and dominant != "미분석":
        return 65

    return 0


def extract_risk_score(risk_dict: dict, label: str) -> int:
    score_raw = risk_dict.get("risk_score", None)
    if score_raw is not None:
        score = _safe_int_percent(score_raw, default=0)
        if score > 0:
            return score

    fallback = {
        "안전": 20,
        "주의": 45,
        "보통": 50,
        "위험": 75,
        "심각": 90,
        "미분석": 0,
    }
    return fallback.get(label, 0)


def normalize_emotion(emotion_dict: dict) -> dict:
    dominant = clean_text(emotion_dict.get("dominant_emotion"), "미분석")

    if dominant == "미분석":
        utterance_results = emotion_dict.get("utterance_results", [])
        if utterance_results and isinstance(utterance_results, list):
            first_item = utterance_results[0]
            if isinstance(first_item, dict):
                dominant = clean_text(first_item.get("primary"), "미분석")

    dominant = normalize_emotion_label(dominant)
    confidence = extract_emotion_score(emotion_dict, dominant)

    return {
        "label": dominant if dominant else "미분석",
        "score": max(0, min(confidence, 100)),
        "raw": emotion_dict,
    }


def normalize_risk(risk_dict: dict) -> dict:
    label = normalize_risk_label(clean_text(risk_dict.get("risk_label"), "미분석"))
    score = extract_risk_score(risk_dict, label)
    recommendation = clean_text(risk_dict.get("recommendation"), "")

    return {
        "label": label if label else "미분석",
        "score": max(0, min(score, 100)),
        "recommendation": recommendation,
        "raw": risk_dict,
    }


def format_risk_text(raw_risk_text: str, risk_label: str) -> str:
    raw = normalize_sentence(raw_risk_text).lower()
    label = normalize_risk_label(normalize_sentence(risk_label))

    if "critical" in raw or raw == "심각":
        return "감정적 대립이 매우 큰 상태라 즉각적인 설득보다 상황을 진정시키는 접근이 더 중요합니다."
    if "high" in raw or raw == "위험":
        return "현재 대화가 갈등으로 빠르게 번질 수 있어 자극적인 표현을 피하고 감정 진정이 우선입니다."
    if "normal" in raw or raw == "보통":
        return "현재 감정 충돌이 커질 가능성이 있어 표현을 부드럽게 조정하며 대화하는 것이 좋습니다."
    if "low" in raw or "safe" in raw or raw in {"안전", "주의"}:
        return "현재 갈등이 아주 심각한 수준은 아니지만, 감정이 누적되지 않도록 차분한 대화가 필요합니다."

    if label == "심각":
        return "감정적 대립이 매우 큰 상태라 즉각적인 설득보다 상황을 진정시키는 접근이 더 중요합니다."
    if label == "위험":
        return "현재 대화가 갈등으로 빠르게 번질 수 있어 자극적인 표현을 피하고 감정 진정이 우선입니다."
    if label == "보통":
        return "현재 감정 충돌이 커질 가능성이 있어 표현을 부드럽게 조정하며 대화하는 것이 좋습니다."
    if label in {"주의", "안전"}:
        return "현재 갈등이 아주 심각한 수준은 아니지만, 감정이 누적되지 않도록 차분한 대화가 필요합니다."

    return normalize_risk_label(clean_text(raw_risk_text))


def format_retrieved_cases(retrieved_docs: list) -> list[dict]:
    retrieved_cases = []
    for doc in retrieved_docs[:3]:
        if not isinstance(doc, dict):
            continue

        retrieved_cases.append(
            {
                "dialogue_id": clean_text(doc.get("dialogue_id")),
                "relation": clean_text(doc.get("relation")),
                "situation": clean_text(doc.get("situation")),
                "speaker_emotion": clean_text(doc.get("speaker_emotion")),
                "risk_level": clean_text(doc.get("risk_level")),
            }
        )

    return retrieved_cases


def normalize_recommended_replies(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        if not isinstance(item, dict):
            continue

        label = clean_text(item.get("label"))
        text = clean_text(item.get("text"))
        if not label or not text:
            continue

        normalized.append(
            {
                "label": label,
                "text": text,
                "source_listener_empathy": clean_text(item.get("source_listener_empathy")),
                "dialogue_id": clean_text(item.get("dialogue_id")),
            }
        )

    return normalized


def normalize_text_list(value: object) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        text = clean_text(item)
        if text and text not in normalized:
            normalized.append(text)
    return normalized[:3]


def build_text_analysis_payload(
    *,
    user_input: str,
    emotion_risk_result: dict,
    rag_result: dict,
) -> dict:
    emotion_result = emotion_risk_result.get("emotion", {})
    risk_result = emotion_risk_result.get("risk", {})
    gemini_auxiliary = emotion_risk_result.get("gemini_auxiliary", {})
    if not isinstance(gemini_auxiliary, dict):
        gemini_auxiliary = {}

    normalized_emotion = normalize_emotion(emotion_result)
    normalized_risk = normalize_risk(risk_result)

    result_text = clean_text(rag_result.get("result_text"), "")
    response_examples = clean_text(rag_result.get("response_examples"), "")
    recommended_replies = normalize_recommended_replies(
        rag_result.get("recommended_replies")
    )

    reply_candidates = extract_reply_candidates(result_text, response_examples)
    if not reply_candidates and recommended_replies:
        reply_candidates = [
            f"[{reply['label']}] {reply['text']}"
            for reply in recommended_replies
        ]

    gemini_reply_candidates = normalize_text_list(
        gemini_auxiliary.get("reply_candidates")
        or emotion_risk_result.get("reply_candidates")
    )
    if not reply_candidates and gemini_reply_candidates:
        reply_candidates = gemini_reply_candidates

    summary_text = clean_text(
        rag_result.get("summary_text")
        or parse_section(result_text, "상황 요약")
        or rag_result.get("situation_summary")
        or gemini_auxiliary.get("summary")
        or emotion_risk_result.get("summary"),
        user_input,
    )

    emotion_text = clean_text(
        rag_result.get("emotion_text")
        or normalized_emotion["label"]
        or parse_section(result_text, "감정")
        or rag_result.get("main_emotion"),
        "",
    )

    raw_risk_text = clean_text(
        rag_result.get("risk_text")
        or parse_section(result_text, "위험도")
        or rag_result.get("risk_level"),
        "",
    )
    risk_text = format_risk_text(raw_risk_text, normalized_risk["label"])

    empathy_reply = clean_text(
        rag_result.get("empathy_reply")
        or parse_section(result_text, "공감형")
    )
    advice_reply = clean_text(
        rag_result.get("advice_reply")
        or parse_section(result_text, "조언형")
    )
    buffer_reply = clean_text(
        rag_result.get("buffer_reply")
        or parse_section(result_text, "갈등 완충형")
        or parse_section(result_text, "완화형")
        or parse_section(result_text, "비난 회피형")
    )

    avoid_text = clean_text(
        parse_section(result_text, "피해야 할 표현")
        or rag_result.get("avoid_text")
    )
    alternative_text = clean_text(
        parse_section(result_text, "대체 표현")
        or rag_result.get("alternative_text")
    )

    avoid_phrases = rag_result.get("avoid_phrases", [])
    alternative_phrases = rag_result.get("alternative_phrases", [])

    if not avoid_phrases:
        avoid_phrases = parse_list_block(avoid_text, allow_questions=False)
    if not alternative_phrases:
        alternative_phrases = parse_list_block(alternative_text, allow_questions=False)

    if not avoid_phrases:
        avoid_phrases = normalize_text_list(
            gemini_auxiliary.get("avoid") or emotion_risk_result.get("avoid")
        )
    if not alternative_phrases:
        alternative_phrases = normalize_text_list(
            gemini_auxiliary.get("alternative")
            or emotion_risk_result.get("alternative")
        )

    retrieved_cases = format_retrieved_cases(rag_result.get("retrieved_docs", []))
    assistant_message = result_text

    return {
        "user_input": user_input,
        "assistant_message": assistant_message,
        "result_text": result_text,
        "emotion": normalized_emotion,
        "risk": normalized_risk,
        "summary_text": summary_text,
        "emotion_text": emotion_text,
        "risk_text": risk_text,
        "empathy_reply": empathy_reply,
        "advice_reply": advice_reply,
        "buffer_reply": buffer_reply,
        "reply_candidates": reply_candidates,
        "recommended_replies": recommended_replies,
        "avoid_phrases": avoid_phrases,
        "alternative_phrases": alternative_phrases,
        "retrieved_cases": retrieved_cases,
        "gemini_auxiliary": gemini_auxiliary,
        "rag_raw": rag_result,
        "emotion_risk_raw": emotion_risk_result,
    }