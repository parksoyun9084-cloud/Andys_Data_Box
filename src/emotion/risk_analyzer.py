# -*- coding: utf-8 -*-
"""
risk_analyzer.py
================
대화 단위 갈등 위험도 분석 모듈.

분류 방식:
  LLM-Based : 구조화 프롬프트를 활용한 정밀 위험도 판정 (Chain-of-Thought)

입력:  대화 발화 리스트 (list[str]) + 감정 분석 결과 (DialogueEmotionResult)
출력:  구조화된 위험도 분석 결과 (dict)

위험도 5단계:
  1. 안전(safe)       0.0~0.2  — 갈등 징후 없음
  2. 주의(caution)    0.2~0.4  — 경미한 불만
  3. 경고(warning)    0.4~0.6  — 명확한 갈등 신호
  4. 위험(danger)     0.6~0.8  — 강한 갈등
  5. 심각(critical)   0.8~1.0  — 극단적 갈등

참고 기준: docs/analysis_criteria.md
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

from .emotion_analyzer import (
    EMOTION_GROUP,
    EMOTION_LABEL_EN,
    DialogueEmotionResult,
    EmotionClassifier,
)

# ──────────────────────────────────────────────
# 1. 위험도 등급 정의
# ──────────────────────────────────────────────

RISK_LEVELS = [
    {"level": 1, "label": "안전", "label_en": "safe",     "min": 0.0, "max": 0.2},
    {"level": 2, "label": "주의", "label_en": "caution",  "min": 0.2, "max": 0.4},
    {"level": 3, "label": "경고", "label_en": "warning",  "min": 0.4, "max": 0.6},
    {"level": 4, "label": "위험", "label_en": "danger",   "min": 0.6, "max": 0.8},
    {"level": 5, "label": "심각", "label_en": "critical", "min": 0.8, "max": 1.0},
]

RISK_RECOMMENDATIONS = {
    "safe":     "일반 응답",
    "caution":  "공감 표현 + 상황 확인",
    "warning":  "적극적 공감 + 진정 유도",
    "danger":   "긴급 공감 + 대화 전환 시도",
    "critical": "전문 상담 권유 + 안전 대응",
}

COMBINED_ANALYSIS_PROMPT = """당신은 **연인 갈등 상황** 전문 감정/위험도 통합 분석가입니다.

## 과업
아래 대화를 한 번에 분석하여 **감정 분석(emotion)** 과 **갈등 위험도(risk)** 를 하나의 JSON으로 반환하세요.

## 감정 라벨
- 중립(neutral), 놀람(surprise), 분노(anger), 슬픔(sadness), 행복(happiness), 혐오(disgust), 공포(fear)
- group은 negative, neutral, positive 중 하나입니다.
- negative: 분노, 슬픔, 혐오, 공포
- neutral: 중립
- positive: 행복, 놀람

## 위험도 5단계
| 등급 | 라벨 | 점수 범위 | 설명 |
|---|---|---|---|
| 1 | 안전(safe) | 0.0~0.2 | 갈등 징후 없음. 일상 대화 |
| 2 | 주의(caution) | 0.2~0.4 | 경미한 불만/서운함 |
| 3 | 경고(warning) | 0.4~0.6 | 명확한 갈등 신호. 분노/혐오 반복 |
| 4 | 위험(danger) | 0.6~0.8 | 강한 갈등. 공격적 표현, 감정 폭발 |
| 5 | 심각(critical) | 0.8~1.0 | 극단적 갈등. 관계 단절 위험 |

## 대화 내용
{dialogue}

## 보조 출력
- summary: 현재 갈등/대화 상황 요약 1~2문장
- reply_candidates: 사용자가 바로 참고할 수 있는 추천 답변 3개
- avoid: 피해야 할 표현 목록
- alternative: 대체 표현 목록

## 출력 규칙
- 반드시 JSON만 출력하세요.
- 코드블록, 설명 문장, 주석을 출력하지 마세요.
- emotion은 기존 대화 감정 분석 JSON 구조를 따르세요.
- risk는 기존 위험도 분석 JSON 구조를 따르세요.

## 출력 형식
{{
  "emotion": {{
    "utterances": [
      {{
        "index": 0,
        "text": "발화 텍스트",
        "primary": "감정라벨(한글)",
        "primary_en": "감정라벨(영문)",
        "group": "negative|neutral|positive",
        "confidence": 0.0,
        "reasoning": "추론 근거 (1문장)"
      }}
    ],
    "dialogue_summary": {{
      "dominant_emotion": "가장 지배적인 감정(한글)",
      "dominant_group": "negative|neutral|positive",
      "emotion_flow": "감정 흐름 설명 (1~2문장)",
      "conflict_level": "low|medium|high"
    }}
  }},
  "risk": {{
    "risk_score": 0.0,
    "risk_level": "safe|caution|warning|danger|critical",
    "risk_label": "한글 라벨",
    "risk_grade": 1,
    "analysis": {{
      "emotion_intensity": "감정 강도 분석 (1문장)",
      "expression_level": "표현 수위 분석 (1문장)",
      "conflict_structure": "갈등 구조 분석 (1문장)",
      "relationship_threat": "관계 위협 수준 (1문장)",
      "emotion_trend": "감정 흐름 분석 (1문장)",
      "ending_direction": "종료 방향 분석 (1문장)"
    }},
    "recommendation": "대응 전략 (1~2문장)",
    "reasoning": "종합 판단 근거 (2~3문장)"
  }},
  "summary": "상황 요약",
  "reply_candidates": [
    "추천 답변 1",
    "추천 답변 2",
    "추천 답변 3"
  ],
  "avoid": [
    "피해야 할 표현 1",
    "피해야 할 표현 2"
  ],
  "alternative": [
    "대체 표현 1",
    "대체 표현 2"
  ]
}}"""

# ──────────────────────────────────────────────
# 2. 결과 데이터 클래스
# ──────────────────────────────────────────────

@dataclass
class RiskResult:
    """대화 단위 위험도 분석 결과."""

    dialogue_id: Optional[str] = None
    risk_score: float = 0.0               # 최종 위험도 점수 (0.0~1.0)
    risk_level: str = "safe"              # 위험도 영문 라벨
    risk_label: str = "안전"               # 위험도 한글 라벨
    risk_grade: int = 1                   # 위험도 등급 (1~5)
    emotion_sequence: list[str] = field(default_factory=list)
    recommendation: str = ""              # 대응 전략
    method: str = "llm"
    reasoning: str = ""                   # LLM 추론 근거

    @property
    def risk_score_percent(self) -> int:
        """100분율로 환산된 위험도 점수"""
        return int(self.risk_score * 100)

    @property
    def risk_score_str(self) -> str:
        """100% 표기법 문자열"""
        return f"{self.risk_score_percent}%"

    def to_dict(self) -> dict:
        result = asdict(self)
        result["risk_score_percent"] = self.risk_score_percent
        result["risk_score_str"] = self.risk_score_str
        return result

    def to_json(self, ensure_ascii: bool = False, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)


# ──────────────────────────────────────────────
# 3. LLM 기반 위험도 분석기
# ──────────────────────────────────────────────

class RiskAnalyzer:
    """
    LLM 프롬프트 기반 위험도 분석기.

    특징:
      - Chain-of-Thought 추론으로 다각도 위험 요소 분석
      - 문맥·뉘앙스·비유를 고려한 정밀 판단
      - JSON 구조화 출력으로 안정적 파싱
    """

    RISK_ANALYSIS_PROMPT = """당신은 **연인 갈등 상황** 전문 위험도 분석가입니다.

## 과업
아래 대화의 **갈등 위험도**를 분석하세요.

## 위험도 5단계
| 등급 | 라벨 | 점수 범위 | 설명 |
|---|---|---|---|
| 1 | 안전(safe) | 0.0~0.2 | 갈등 징후 없음. 일상 대화 |
| 2 | 주의(caution) | 0.2~0.4 | 경미한 불만/서운함 |
| 3 | 경고(warning) | 0.4~0.6 | 명확한 갈등 신호. 분노/혐오 반복 |
| 4 | 위험(danger) | 0.6~0.8 | 강한 갈등. 공격적 표현, 감정 폭발 |
| 5 | 심각(critical) | 0.8~1.0 | 극단적 갈등. 관계 단절 위험 |

## 분석 관점 (Chain-of-Thought)
다음 관점을 모두 고려하여 단계별로 추론하세요:

1. **감정 강도**: 부정 감정(분노, 혐오, 슬픔, 공포)의 빈도와 강도
2. **표현 수위**: 공격적·폭력적·극단적 표현의 유무와 정도
3. **갈등 구조**: 일방적 공격인지, 상호 갈등인지, 오해 기반인지
4. **관계 위협**: 관계 단절·이별 암시 표현의 유무
5. **감정 흐름**: 감정이 악화되고 있는지, 진정되고 있는지
6. **대화 종료 방향**: 마지막 발화의 감정이 부정적인지 긍정적인지

## 대화 내용
{dialogue}

## 감정 시퀀스 (참고)
{emotion_sequence}

## 출력 형식 (반드시 아래 JSON만 출력)
```json
{{
  "risk_score": 0.0~1.0,
  "risk_level": "safe|caution|warning|danger|critical",
  "risk_label": "한글 라벨",
  "risk_grade": 1~5,
  "analysis": {{
    "emotion_intensity": "감정 강도 분석 (1문장)",
    "expression_level": "표현 수위 분석 (1문장)",
    "conflict_structure": "갈등 구조 분석 (1문장)",
    "relationship_threat": "관계 위협 수준 (1문장)",
    "emotion_trend": "감정 흐름 분석 (1문장)",
    "ending_direction": "종료 방향 분석 (1문장)"
  }},
  "recommendation": "대응 전략 (1~2문장)",
  "reasoning": "종합 판단 근거 (2~3문장)"
}}
```"""

    def get_prompt(
        self,
        utterances: list[str],
        emotion_sequence: list[str],
    ) -> str:
        """위험도 분석 프롬프트를 생성한다."""
        dialogue_text = "\n".join(
            f"[발화 {i}] {u}" for i, u in enumerate(utterances)
        )
        seq_text = " > ".join(emotion_sequence) if emotion_sequence else "(미분석)"

        return self.RISK_ANALYSIS_PROMPT.format(
            dialogue=dialogue_text,
            emotion_sequence=seq_text,
        )

    def analyze(
        self,
        utterances: list[str],
        llm_caller,
        emotion_result: DialogueEmotionResult | None = None,
        dialogue_id: str | None = None,
    ) -> RiskResult:
        """
        대화 위험도 분석 (LLM 기반).

        Parameters
        ----------
        utterances : list[str]
            대화 발화 리스트.
        llm_caller : callable
            LLM 호출 함수.
        emotion_result : DialogueEmotionResult | None
            사전 수행된 감정 분석 결과. None이면 내부에서 LLM 감정 분석 수행.
        dialogue_id : str | None
            대화 식별자.

        Returns
        -------
        RiskResult
            구조화된 위험도 분석 결과.
        """
        # 감정 분석이 없으면 LLM으로 수행
        if emotion_result is None:
            clf = EmotionClassifier()
            emotion_result = clf.classify_dialogue(utterances, llm_caller, dialogue_id)

        emotion_seq = emotion_result.emotion_sequence

        prompt = self.get_prompt(
            utterances=utterances,
            emotion_sequence=emotion_seq,
        )
        response = llm_caller(prompt)
        return self.parse_response(
            response,
            dialogue_id=dialogue_id or emotion_result.dialogue_id,
            emotion_sequence=emotion_seq,
        )

    def parse_response(
        self, llm_output: str, dialogue_id: str | None = None,
        emotion_sequence: list[str] | None = None,
    ) -> RiskResult:
        """
        LLM 응답을 파싱하여 RiskResult로 변환한다.

        Parameters
        ----------
        llm_output : str
            LLM의 JSON 응답 문자열.
        dialogue_id : str | None
            대화 식별자.
        emotion_sequence : list[str] | None
            감정 시퀀스.

        Returns
        -------
        RiskResult
            파싱된 위험도 분석 결과.
        """
        parsed = self._extract_json(llm_output)

        risk_score = float(parsed.get("risk_score", 0.0))
        risk_level = parsed.get("risk_level", "safe")
        risk_label = parsed.get("risk_label", "안전")
        risk_grade = int(parsed.get("risk_grade", 1))
        analysis = parsed.get("analysis", {})
        recommendation = parsed.get("recommendation", "")
        reasoning = parsed.get("reasoning", "")

        # 분석 내용을 reasoning에 통합
        if analysis:
            analysis_text = " / ".join(
                f"{k}: {v}" for k, v in analysis.items() if v
            )
            reasoning = f"{reasoning} [상세] {analysis_text}"

        return RiskResult(
            dialogue_id=dialogue_id,
            risk_score=round(risk_score, 4),
            risk_level=risk_level,
            risk_label=risk_label,
            risk_grade=risk_grade,
            emotion_sequence=emotion_sequence or [],
            recommendation=recommendation,
            method="llm",
            reasoning=reasoning,
        )

    @staticmethod
    def _score_to_level(score: float) -> dict:
        """점수를 위험도 등급으로 변환한다."""
        for level in RISK_LEVELS:
            if score < level["max"] or (score == 1.0 and level["level"] == 5):
                return level
        return RISK_LEVELS[-1]

    @staticmethod
    def _extract_json(text: str) -> dict:
        """LLM 출력에서 JSON 블록을 추출하여 파싱한다."""
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            json_str = text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM 응답 JSON 파싱 실패: {e}\n원본 응답:\n{text[:300]}"
            ) from e


# ──────────────────────────────────────────────
# 4. 통합 분석 함수
# ──────────────────────────────────────────────

def analyze_risk(
    utterances: list[str],
    dialogue_id: str | None = None,
    emotion_result: DialogueEmotionResult | None = None,
    llm_caller=None,
) -> RiskResult:
    """
    대화 위험도 분석 함수 (LLM 기반).

    Parameters
    ----------
    utterances : list[str]
        대화 발화 리스트.
    dialogue_id : str | None
        대화 식별자.
    emotion_result : DialogueEmotionResult | None
        사전 수행된 감정 분석 결과. None이면 내부에서 수행.
    llm_caller : callable
        LLM 호출 함수. 필수.

    Returns
    -------
    RiskResult
        구조화된 위험도 분석 결과.
    """
    if llm_caller is None:
        raise ValueError("llm_caller 함수를 제공해야 합니다.")

    analyzer = RiskAnalyzer()
    return analyzer.analyze(utterances, llm_caller, emotion_result, dialogue_id)


def _clean_aux_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_aux_list(value: object) -> list[str]:
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if not isinstance(value, list):
        return []

    results: list[str] = []
    for item in value:
        cleaned = _clean_aux_text(item)
        if cleaned and cleaned not in results:
            results.append(cleaned)
    return results


def _fallback_full_analysis(
    utterances: list[str],
    dialogue_id: str | None,
    error: Exception,
) -> dict:
    joined_dialogue = " ".join(str(utterance).strip() for utterance in utterances)
    summary = (
        "Gemini 분석을 완료하지 못해 기본 기준으로 임시 분석했습니다. "
        "대화 내용을 바탕으로 차분한 확인과 공감 중심의 응답을 권장합니다."
    )
    if joined_dialogue:
        summary = f"{summary} 입력 요약: {joined_dialogue[:120]}"

    emotion_result = DialogueEmotionResult(
        dialogue_id=dialogue_id,
        utterance_results=[],
        emotion_sequence=[],
        dominant_emotion="중립",
        dominant_group="neutral",
        negative_ratio=0.0,
        emotion_volatility=0.0,
        method="fallback",
    )
    risk_result = RiskResult(
        dialogue_id=dialogue_id,
        risk_score=0.2,
        risk_level="caution",
        risk_label="주의",
        risk_grade=2,
        emotion_sequence=[],
        recommendation="상대의 감정을 단정하지 말고, 현재 느낀 점을 차분히 확인하세요.",
        method="fallback",
        reasoning=f"Gemini 분석 실패로 기본 주의 등급을 적용했습니다. 원인: {type(error).__name__}",
    )
    gemini_auxiliary = {
        "summary": summary,
        "reply_candidates": [
            "지금 바로 단정하기보다, 내가 느낀 점을 차분히 말해볼게.",
            "서로 오해가 생긴 부분이 있는지 먼저 확인해보자.",
            "비난하려는 건 아니고, 이 상황에서 내가 불안했던 점을 이야기하고 싶어.",
        ],
        "avoid": [
            "왜 항상 그래?",
            "네가 문제야.",
            "됐고, 그냥 내 말 들어.",
        ],
        "alternative": [
            "나는 이 상황에서 조금 불안했어.",
            "무슨 일이 있었는지 차분히 듣고 싶어.",
            "서로 감정이 커지기 전에 잠깐 정리해보자.",
        ],
        "fallback": True,
        "error_type": type(error).__name__,
    }

    return {
        "dialogue_id": dialogue_id,
        "emotion": emotion_result.to_dict(),
        "risk": risk_result.to_dict(),
        "summary": gemini_auxiliary["summary"],
        "reply_candidates": gemini_auxiliary["reply_candidates"],
        "avoid": gemini_auxiliary["avoid"],
        "alternative": gemini_auxiliary["alternative"],
        "gemini_auxiliary": gemini_auxiliary,
    }


# ──────────────────────────────────────────────
# 5. 통합 파이프라인: 감정 + 위험도
# ──────────────────────────────────────────────

def full_analysis(
    utterances: list[str],
    dialogue_id: str | None = None,
    llm_caller=None,
) -> dict:
    """
    감정 분석 → 위험도 분석을 연결하는 통합 파이프라인 (LLM 기반).

    Parameters
    ----------
    utterances : list[str]
        대화 발화 리스트.
    dialogue_id : str | None
        대화 식별자.
    llm_caller : callable
        LLM 호출 함수. 필수.

    Returns
    -------
    dict
        emotion: 감정 분석 결과, risk: 위험도 분석 결과.
    """
    if llm_caller is None:
        raise ValueError("llm_caller 함수를 제공해야 합니다.")

    dialogue_text = "\n".join(
        f"[발화 {index}] {utterance}"
        for index, utterance in enumerate(utterances)
    )
    prompt = COMBINED_ANALYSIS_PROMPT.format(dialogue=dialogue_text)
    try:
        response = llm_caller(prompt)
        parsed = RiskAnalyzer._extract_json(response)

        if "emotion" not in parsed or "risk" not in parsed:
            raise ValueError("통합 LLM 응답에는 emotion과 risk 키가 필요합니다.")

        emotion_payload = parsed.get("emotion")
        risk_payload = parsed.get("risk")
        if not isinstance(emotion_payload, dict) or not isinstance(risk_payload, dict):
            raise ValueError("통합 LLM 응답에는 emotion과 risk 객체가 필요합니다.")

        emotion_classifier = EmotionClassifier()
        emotion_result = emotion_classifier.parse_dialogue_response(
            utterances,
            json.dumps(emotion_payload, ensure_ascii=False),
            dialogue_id,
        )

        risk_analyzer = RiskAnalyzer()
        risk_result = risk_analyzer.parse_response(
            json.dumps(risk_payload, ensure_ascii=False),
            dialogue_id=dialogue_id or emotion_result.dialogue_id,
            emotion_sequence=emotion_result.emotion_sequence,
        )
        gemini_auxiliary = {
            "summary": _clean_aux_text(parsed.get("summary")),
            "reply_candidates": _clean_aux_list(parsed.get("reply_candidates")),
            "avoid": _clean_aux_list(parsed.get("avoid")),
            "alternative": _clean_aux_list(parsed.get("alternative")),
            "fallback": False,
        }
    except Exception as exc:
        return _fallback_full_analysis(utterances, dialogue_id, exc)

    return {
        "dialogue_id": dialogue_id,
        "emotion": emotion_result.to_dict(),
        "risk": risk_result.to_dict(),
        "summary": gemini_auxiliary["summary"],
        "reply_candidates": gemini_auxiliary["reply_candidates"],
        "avoid": gemini_auxiliary["avoid"],
        "alternative": gemini_auxiliary["alternative"],
        "gemini_auxiliary": gemini_auxiliary,
    }


# ──────────────────────────────────────────────
# 6. CLI 테스트
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    # ── Mock LLM Caller (테스트용) ──
    def mock_emotion_llm_caller(prompt: str) -> str:
        """Mock 감정 분석 LLM caller."""
        # 대화 분석 프롬프트 감지
        if "각 발화별 감정 라벨" in prompt:
            # 대화 내에 포함된 키워드로 감정 추정
            utterance_emotions = []
            lines = [l for l in prompt.split("\n") if l.startswith("[발화")]
            for i, line in enumerate(lines):
                if any(k in line for k in ["꺼져", "헤어지자", "죽겠다", "끝내자", "지긋지긋"]):
                    utterance_emotions.append({
                        "index": i, "text": line, "primary": "혐오",
                        "primary_en": "disgust", "group": "negative",
                        "confidence": 0.9, "reasoning": "극단적 거부 표현"
                    })
                elif any(k in line for k in ["화", "짜증", "왜", "수상", "번호"]):
                    utterance_emotions.append({
                        "index": i, "text": line, "primary": "분노",
                        "primary_en": "anger", "group": "negative",
                        "confidence": 0.85, "reasoning": "불만 표출"
                    })
                elif any(k in line for k in ["속상", "늦었", "미안", "참은"]):
                    utterance_emotions.append({
                        "index": i, "text": line, "primary": "슬픔",
                        "primary_en": "sadness", "group": "negative",
                        "confidence": 0.75, "reasoning": "서운함/속상함"
                    })
                elif any(k in line for k in ["좋", "맛있", "파스타"]):
                    utterance_emotions.append({
                        "index": i, "text": line, "primary": "행복",
                        "primary_en": "happiness", "group": "positive",
                        "confidence": 0.85, "reasoning": "긍정적 반응"
                    })
                elif any(k in line for k in ["뭐?", "갑자기"]):
                    utterance_emotions.append({
                        "index": i, "text": line, "primary": "놀람",
                        "primary_en": "surprise", "group": "positive",
                        "confidence": 0.7, "reasoning": "예상치 못한 반응"
                    })
                else:
                    utterance_emotions.append({
                        "index": i, "text": line, "primary": "중립",
                        "primary_en": "neutral", "group": "neutral",
                        "confidence": 0.7, "reasoning": "특별한 감정 없음"
                    })

            neg = sum(1 for e in utterance_emotions if e["group"] == "negative")
            total = len(utterance_emotions) if utterance_emotions else 1
            dominant = "분노" if neg > total / 2 else "중립"
            dom_group = "negative" if neg > total / 2 else "neutral"

            return json.dumps({
                "utterances": utterance_emotions,
                "dialogue_summary": {
                    "dominant_emotion": dominant,
                    "dominant_group": dom_group,
                    "emotion_flow": "감정 흐름 분석 (mock)",
                    "conflict_level": "high" if neg > total / 2 else "low"
                }
            }, ensure_ascii=False)
        else:
            # 단일 발화 분석
            return json.dumps({
                "primary": "중립", "primary_en": "neutral", "group": "neutral",
                "confidence": 0.6, "reasoning": "Mock 분석"
            }, ensure_ascii=False)

    def mock_risk_llm_caller(prompt: str) -> str:
        """Mock 위험도 분석 LLM caller."""
        # 위험도 분석용 프롬프트 감지
        if "갈등 위험도" in prompt:
            # 대화 내용 기반으로 위험 수준 추정
            if any(k in prompt for k in ["죽겠다", "헤어지자", "끝내자", "꺼져"]):
                return json.dumps({
                    "risk_score": 0.85, "risk_level": "critical",
                    "risk_label": "심각", "risk_grade": 5,
                    "analysis": {
                        "emotion_intensity": "매우 강한 부정 감정이 반복 표출됨",
                        "expression_level": "극단적 표현(관계 단절, 고통 호소) 다수 발견",
                        "conflict_structure": "일방적 공격과 감정 폭발이 교차",
                        "relationship_threat": "관계 단절 의사가 명시적으로 표현됨",
                        "emotion_trend": "감정이 지속적으로 악화 중",
                        "ending_direction": "극도로 부정적인 방향으로 종료"
                    },
                    "recommendation": "전문 상담 권유 + 안전 대응",
                    "reasoning": "관계 단절 선언과 자해 암시가 포함되어 즉각적 개입 필요"
                }, ensure_ascii=False)
            elif any(k in prompt for k in ["이혼", "포기", "보기싫"]):
                return json.dumps({
                    "risk_score": 0.7, "risk_level": "danger",
                    "risk_label": "위험", "risk_grade": 4,
                    "analysis": {
                        "emotion_intensity": "강한 부정 감정 반복",
                        "expression_level": "관계 위협 표현 발견",
                        "conflict_structure": "상호 갈등 양상",
                        "relationship_threat": "관계 유지 의지 약화",
                        "emotion_trend": "악화 경향",
                        "ending_direction": "부정적 종료"
                    },
                    "recommendation": "긴급 공감 + 대화 전환 시도",
                    "reasoning": "관계 위협 표현이 있으나 극단적 수준은 아님"
                }, ensure_ascii=False)
            elif any(k in prompt for k in ["의심", "수상", "짜증"]):
                return json.dumps({
                    "risk_score": 0.5, "risk_level": "warning",
                    "risk_label": "경고", "risk_grade": 3,
                    "analysis": {
                        "emotion_intensity": "중간 강도의 부정 감정",
                        "expression_level": "공격적 표현 일부 포함",
                        "conflict_structure": "불신 기반 갈등",
                        "relationship_threat": "직접적 위협은 없음",
                        "emotion_trend": "상승 경향",
                        "ending_direction": "부정적 방향"
                    },
                    "recommendation": "적극적 공감 + 진정 유도",
                    "reasoning": "불신이 갈등의 핵심 원인. 진정 유도 필요"
                }, ensure_ascii=False)
            elif any(k in prompt for k in ["답답", "속상", "늦었"]):
                return json.dumps({
                    "risk_score": 0.3, "risk_level": "caution",
                    "risk_label": "주의", "risk_grade": 2,
                    "analysis": {
                        "emotion_intensity": "경미한 부정 감정",
                        "expression_level": "공격성 없음",
                        "conflict_structure": "경미한 불만 표출",
                        "relationship_threat": "위협 없음",
                        "emotion_trend": "안정 경향",
                        "ending_direction": "중립적 종료"
                    },
                    "recommendation": "공감 표현 + 상황 확인",
                    "reasoning": "경미한 불만으로 공감 대응이 적절"
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "risk_score": 0.1, "risk_level": "safe",
                    "risk_label": "안전", "risk_grade": 1,
                    "analysis": {
                        "emotion_intensity": "감정 강도 낮음",
                        "expression_level": "공격성 없음",
                        "conflict_structure": "갈등 없음",
                        "relationship_threat": "위협 없음",
                        "emotion_trend": "안정",
                        "ending_direction": "긍정/중립적 종료"
                    },
                    "recommendation": "일반 응답",
                    "reasoning": "갈등 징후 없는 일상 대화"
                }, ensure_ascii=False)
        else:
            return mock_emotion_llm_caller(prompt)

    print("=" * 60)
    print("위험도 분석기 테스트 (LLM-Based)")
    print("=" * 60)

    # 테스트 케이스 1: 안전한 대화
    safe_dialogue = [
        "오늘 뭐 먹을까?",
        "글쎄, 뭐 먹고 싶어?",
        "파스타 어때?",
        "좋지! 맛있겠다.",
    ]

    # 테스트 케이스 2: 주의 수준 대화
    caution_dialogue = [
        "오늘도 늦었네...",
        "미안. 회사가 바빠서.",
        "맨날 바쁘다 바쁘다... 답답해.",
        "알았어. 다음부턴 미리 얘기할게.",
    ]

    # 테스트 케이스 3: 경고 수준 대화
    warning_dialogue = [
        "왜 여자 번호가 이렇게 많아?",
        "그냥 회사 사람들이야. 왜 그래?",
        "왜 그래? 니가 수상하니까 그렇지!",
        "의심하지 마. 짜증나네.",
        "짜증나는 건 나라고!",
    ]

    # 테스트 케이스 4: 위험 수준 대화
    danger_dialogue = [
        "나 자기 마누라 찾아가서 담판 질거야",
        "지금, 누굴 찾아가 담판을 져",
        "나랑 그동안의 관계 다 말하고. 이혼해 달라고 할거야",
        "이 시대에 뽀뽀 몇 번 한 것도 책임져야 돼냐?",
        "아무튼 난 절대 자기 포기 못해, 절대!!!",
    ]

    # 테스트 케이스 5: 심각 수준 대화
    critical_dialogue = [
        "이제 진짜 끝내자. 지긋지긋해.",
        "뭐? 갑자기 왜 이래.",
        "갑자기가 아니야. 한참 참은 거야. 꺼져.",
        "나보고 꺼지라고?",
        "보기 싫어. 헤어지자. 죽겠다 진짜.",
    ]

    test_cases = [
        ("안전", safe_dialogue),
        ("주의", caution_dialogue),
        ("경고", warning_dialogue),
        ("위험", danger_dialogue),
        ("심각", critical_dialogue),
    ]

    for label, dialogue in test_cases:
        result = full_analysis(dialogue, dialogue_id=f"test_{label}", llm_caller=mock_risk_llm_caller)

        emotion = result["emotion"]
        risk = result["risk"]

        print(f"\n{'─' * 50}")
        print(f"[기대 등급: {label}]")
        print(f"  감정 시퀀스: {' > '.join(emotion['emotion_sequence'])}")
        print(f"  지배적 감정: {emotion['dominant_emotion']} ({emotion['dominant_group']})")
        print(f"  부정 비율: {emotion.get('negative_ratio_str', emotion['negative_ratio'])}")
        print(f"  위험도 점수: {risk['risk_score_str']}")
        print(f"  위험도 등급: {risk['risk_label']} ({risk['risk_level']}, {risk['risk_grade']}등급)")
        print(f"  대응 전략: {risk['recommendation']}")

    # LLM 프롬프트 예시
    print("\n" + "=" * 60)
    print("LLM 위험도 분석 프롬프트 예시")
    print("=" * 60)
    analyzer = RiskAnalyzer()
    prompt = analyzer.get_prompt(
        utterances=critical_dialogue,
        emotion_sequence=["혐오", "놀람", "혐오", "분노", "혐오"],
    )
    print(prompt[:800] + "...")
