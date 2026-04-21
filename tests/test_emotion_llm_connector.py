# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from src.emotion import analyze_emotion, full_analysis
from src.emotion.llm_connector import (
    GeminiFunctionCallingRouter,
    GeminiConnectorError,
    _SlidingWindowRateLimiter,
    create_gemini_caller,
    load_secret,
)


def fake_emotion_llm(prompt: str) -> str:
    if "갈등 위험도" in prompt:
        return json.dumps(
            {
                "risk_score": 0.3,
                "risk_level": "caution",
                "risk_label": "주의",
                "risk_grade": 2,
                "analysis": {},
                "recommendation": "상황을 확인한다.",
                "reasoning": "mock risk",
            },
            ensure_ascii=False,
        )
    if "dialogue_summary" in prompt or "대화 전체" in prompt:
        return json.dumps(
            {
                "utterances": [
                    {
                        "primary": "중립",
                        "primary_en": "neutral",
                        "group": "neutral",
                        "confidence": 0.9,
                        "reasoning": "mock dialogue emotion",
                    }
                ],
                "dialogue_summary": {
                    "dominant_emotion": "중립",
                    "dominant_group": "neutral",
                },
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "primary": "중립",
            "primary_en": "neutral",
            "group": "neutral",
            "confidence": 0.9,
            "reasoning": "mock single emotion",
        },
        ensure_ascii=False,
    )


class FakeResponse:
    text = '{"ok": true}'


class FakeModels:
    def __init__(self) -> None:
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse()


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModels()


class RetryableGeminiError(Exception):
    def __init__(self, message: str = "503 Service Unavailable", status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


class FakeSequentialModels:
    def __init__(self, outcomes) -> None:
        self.calls = []
        self._outcomes = list(outcomes)

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeSequentialClient:
    def __init__(self, outcomes) -> None:
        self.models = FakeSequentialModels(outcomes)


class EmotionLLMConnectorTest(unittest.TestCase):
    def test_existing_public_api_still_accepts_injected_llm_caller(self) -> None:
        result = analyze_emotion("안녕", llm_caller=fake_emotion_llm)
        self.assertEqual(result.primary, "중립")
        self.assertEqual(result.method, "llm")

    def test_full_analysis_still_accepts_injected_llm_caller(self) -> None:
        result = full_analysis(["안녕"], dialogue_id="d1", llm_caller=fake_emotion_llm)
        self.assertEqual(result["dialogue_id"], "d1")
        self.assertIn("emotion", result)
        self.assertIn("risk", result)

    def test_load_secret_reads_streamlit_toml_without_printing_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".streamlit").mkdir()
            (root / ".streamlit" / "secrets.toml").write_text(
                'GEMINI_API_KEY = "real-test-key"\n', encoding="utf-8"
            )
            self.assertEqual(
                load_secret(
                    "GEMINI_API_KEY",
                    project_root=root,
                    include_streamlit_runtime=False,
                ),
                "real-test-key",
            )

    def test_load_secret_skips_placeholders_and_falls_back_to_env(self) -> None:
        previous_gemini_api_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "env-test-key"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".streamlit").mkdir()
                (root / ".streamlit" / "secrets.toml").write_text(
                    'GEMINI_API_KEY = "<your_api_key>"\n', encoding="utf-8"
                )
                self.assertEqual(
                    load_secret(
                        "GEMINI_API_KEY",
                        project_root=root,
                        include_streamlit_runtime=False,
                    ),
                    "env-test-key",
                )
        finally:
            if previous_gemini_api_key is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = previous_gemini_api_key

    def test_create_gemini_caller_supports_fake_client_without_network(self) -> None:
        fake_client = FakeClient()
        caller = create_gemini_caller(client=fake_client)
        self.assertEqual(caller("Return JSON"), '{"ok": true}')
        self.assertEqual(fake_client.models.calls[0]["model"], "gemini-2.5-flash")

    def test_create_gemini_caller_waits_for_next_rpm_slot(self) -> None:
        current_time = [100.0]
        sleep_calls = []

        def fake_now() -> float:
            return current_time[0]

        def fake_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)
            current_time[0] += seconds

        limiter = _SlidingWindowRateLimiter(
            max_calls=5,
            window_seconds=60.0,
            time_func=fake_now,
            sleep_func=fake_sleep,
        )
        fake_client = FakeClient()
        caller = create_gemini_caller(
            client=fake_client,
            rate_limiter=limiter,
            sleep_func=fake_sleep,
        )

        for _ in range(6):
            self.assertEqual(caller("Return JSON"), '{"ok": true}')

        self.assertEqual(len(fake_client.models.calls), 6)
        self.assertEqual(sleep_calls, [60.0])

    def test_create_gemini_caller_retries_retryable_503_then_succeeds(self) -> None:
        sleep_calls = []
        limiter = _SlidingWindowRateLimiter(
            max_calls=10,
            window_seconds=60.0,
            time_func=lambda: 100.0,
            sleep_func=lambda seconds: None,
        )
        fake_client = FakeSequentialClient(
            [RetryableGeminiError(), FakeResponse()]
        )
        caller = create_gemini_caller(
            client=fake_client,
            rate_limiter=limiter,
            retry_limit=2,
            initial_backoff_seconds=0.5,
            max_backoff_seconds=1.0,
            sleep_func=sleep_calls.append,
        )

        self.assertEqual(caller("Return JSON"), '{"ok": true}')
        self.assertEqual(len(fake_client.models.calls), 2)
        self.assertEqual(sleep_calls, [0.5])

    def test_create_gemini_caller_raises_clear_error_after_retry_exhaustion(self) -> None:
        sleep_calls = []
        limiter = _SlidingWindowRateLimiter(
            max_calls=10,
            window_seconds=60.0,
            time_func=lambda: 100.0,
            sleep_func=lambda seconds: None,
        )
        fake_client = FakeSequentialClient(
            [RetryableGeminiError(), RetryableGeminiError(), RetryableGeminiError()]
        )
        caller = create_gemini_caller(
            client=fake_client,
            rate_limiter=limiter,
            retry_limit=2,
            initial_backoff_seconds=0.5,
            max_backoff_seconds=1.0,
            sleep_func=sleep_calls.append,
        )

        with self.assertRaises(GeminiConnectorError) as exc_info:
            caller("Return JSON")

        self.assertIn("temporarily unavailable", str(exc_info.exception))
        self.assertEqual(len(fake_client.models.calls), 3)
        self.assertEqual(sleep_calls, [0.5, 1.0])

    def test_router_dispatches_full_analysis_tool_locally(self) -> None:
        router = GeminiFunctionCallingRouter(llm_caller=fake_emotion_llm)
        dispatched = router.dispatch_tool(
            "full_dialogue_analysis", utterances=["안녕"], dialogue_id="d2"
        )
        self.assertEqual(dispatched.tool_name, "full_dialogue_analysis")
        self.assertIn("emotion", dispatched.result)
        self.assertIn("risk", dispatched.result)

    def test_router_rejects_unknown_tool(self) -> None:
        router = GeminiFunctionCallingRouter(llm_caller=fake_emotion_llm)
        with self.assertRaises(ValueError):
            router.dispatch_tool("unknown_tool")


if __name__ == "__main__":
    unittest.main()
