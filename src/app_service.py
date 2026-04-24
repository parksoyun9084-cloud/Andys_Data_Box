# -*- coding: utf-8 -*-
"""
app_service.py
==============
Text-only service layer for emotion/risk analysis plus RAG reply generation.
"""

from __future__ import annotations

from copy import deepcopy

from src.app_payload_formatter import build_text_analysis_payload
from src.emotion.llm_connector import create_gemini_caller
from src.emotion.risk_analyzer import full_analysis
from src.rag.build_rag_chain import generate_recommended_reply

_ANALYSIS_CACHE: dict[str, dict] = {}


def _cache_key(user_input: str) -> str:
    return " ".join(user_input.strip().split())


def clear_analysis_cache() -> None:
    _ANALYSIS_CACHE.clear()


def _merge_rag_fields(payload: dict, rag_result: dict) -> dict:
    """
    build_text_analysis_payload()가 rag_result의 구조화 필드를 일부 누락할 수 있으므로,
    화면에 필요한 필드를 payload에 다시 보강한다.
    """
    payload = deepcopy(payload) if payload else {}
    rag_result = rag_result or {}

    # 원문 응답
    payload["result_text"] = rag_result.get("result_text", payload.get("result_text", ""))
    payload["assistant_message"] = rag_result.get(
        "assistant_message",
        payload.get("assistant_message") or payload.get("result_text", "")
    )

    # 구조화 필드
    payload["summary_text"] = rag_result.get(
        "summary_text",
        payload.get("summary_text") or rag_result.get("situation_summary", "")
    )
    payload["emotion_text"] = rag_result.get(
        "emotion_text",
        payload.get("emotion_text") or rag_result.get("main_emotion", "")
    )
    payload["risk_text"] = rag_result.get(
        "risk_text",
        payload.get("risk_text") or rag_result.get("risk_level", "")
    )

    # 추천 답변 3종
    payload["empathy_reply"] = rag_result.get("empathy_reply", payload.get("empathy_reply", ""))
    payload["advice_reply"] = rag_result.get("advice_reply", payload.get("advice_reply", ""))
    payload["buffer_reply"] = rag_result.get("buffer_reply", payload.get("buffer_reply", ""))

    # 파싱 섹션 / 표현 대체
    payload["parsed_sections"] = rag_result.get("parsed_sections", payload.get("parsed_sections", {}))
    payload["avoid_phrases"] = rag_result.get("avoid_phrases", payload.get("avoid_phrases", []))
    payload["alternative_phrases"] = rag_result.get(
        "alternative_phrases",
        payload.get("alternative_phrases", [])
    )

    # 보조 정보
    payload["search_query"] = rag_result.get("search_query", payload.get("search_query", ""))
    payload["retrieved_docs"] = rag_result.get("retrieved_docs", payload.get("retrieved_docs", []))
    payload["response_examples"] = rag_result.get("response_examples", payload.get("response_examples", ""))
    payload["situation_summary"] = rag_result.get(
        "situation_summary",
        payload.get("situation_summary", payload.get("summary_text", ""))
    )
    payload["main_emotion"] = rag_result.get(
        "main_emotion",
        payload.get("main_emotion", payload.get("emotion_text", ""))
    )
    payload["risk_level"] = rag_result.get(
        "risk_level",
        payload.get("risk_level", payload.get("risk_text", ""))
    )
    payload["query_type"] = rag_result.get("query_type", payload.get("query_type", ""))

    return payload


def run_chat_analysis(user_input: str, conflict_type: str = "") -> dict:
    if not user_input or not user_input.strip():
        raise ValueError("user_input이 비어 있습니다.")

    user_input = user_input.strip()
    cache_key = _cache_key(f"{conflict_type}::{user_input}")

    if cache_key in _ANALYSIS_CACHE:
        return deepcopy(_ANALYSIS_CACHE[cache_key])

    llm_caller = create_gemini_caller()
    emotion_risk_result = full_analysis(
        utterances=[user_input],
        dialogue_id="streamlit_chat",
        llm_caller=llm_caller,
    )

    rag_result = generate_recommended_reply(
        question=user_input,
        conflict_type=conflict_type,
        method="pinecone",
        k=3,
    )

    payload = build_text_analysis_payload(
        user_input=user_input,
        emotion_risk_result=emotion_risk_result,
        rag_result=rag_result,
    )

    payload = _merge_rag_fields(payload, rag_result)

    _ANALYSIS_CACHE[cache_key] = deepcopy(payload)
    return deepcopy(payload)
