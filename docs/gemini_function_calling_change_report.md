# Gemini Function Calling 변경 리포트

---

## 1. 개요

### 대상 파일
- `src/emotion/llm_connector.py`
- `tests/test_emotion_llm_connector.py`

### 변경 목적
- 기존 `llm_caller` 주입 구조 유지
- Gemini API 연동 기능 추가
- Function Calling 기반 router 구조 도입
- 네트워크 없이 테스트 가능한 구조 설계

---

## 2. llm_connector.py

### 2.1 역할
- Gemini API 연결
- API Key 로딩
- 기존 emotion / risk 분석 함수와 연동
- Function Calling Router 제공

---

### 2.2 주요 구성

| 구성 요소 | 설명 |
|---|---|
| load_secret() | Gemini API Key 로딩 |
| create_gemini_caller() | 기존 llm_caller(prompt) 형태 유지 |
| GeminiFunctionCallingRouter | Function Calling Router |
| dispatch_tool() | 로컬 함수 실행 |
| analyze_with_gemini_tools() | Router 진입점 |

---

### 2.3 API Key 로딩 우선순위

1. Streamlit runtime secrets  
2. `.streamlit/secrets.toml`  
3. 환경 변수  
4. `data/.env`  
5. 루트 `.env`

---

### 2.4 Placeholder 처리

다음 값은 무효 처리:
- 빈 문자열
- `<...>`
- `your_...`
- `TODO`, `TBD`
- `REPLACE_ME`, `CHANGEME`

---

### 2.5 Gemini Caller 구조

```python
llm_caller(prompt: str) -> str
```

기존 함수와 호환:
- analyze_emotion
- analyze_dialogue_emotion
- analyze_risk
- full_analysis

---

### 2.6 Function Calling Router

| Tool Name | 연결 함수 |
|---|---|
| analyze_single_emotion | analyze_emotion |
| analyze_dialogue_emotion | analyze_dialogue_emotion |
| analyze_dialogue_risk | analyze_risk |
| full_dialogue_analysis | full_analysis |

---

### 2.7 Local Dispatch

- API 호출 없이 테스트 가능
- 네트워크 의존 제거
- 실제 실행 경로 유지

---

### 2.8 예외 처리

```python
GeminiConnectorError
```

발생 조건:
- API Key 없음
- google-genai 미설치
- 응답 실패
- 응답 text 없음

---

### 2.9 설계 원칙

- 기존 코드 수정 최소화
- API 유지
- Gemini 연결 분리
- Secret 출력 금지
- Fake Client 테스트 가능

---

## 3. test_emotion_llm_connector.py

### 3.1 역할
- Connector 동작 검증
- API 호환성 확인
- Secret 로딩 검증
- Router Dispatch 검증

---

### 3.2 테스트 방식

- unittest 사용
- Fake LLM / Fake Client 사용
- 네트워크 호출 없음

---

### 3.3 주요 테스트

| 테스트 | 내용 |
|---|---|
| test_existing_public_api_still_accepts_injected_llm_caller | 기존 API 유지 |
| test_full_analysis_still_accepts_injected_llm_caller | full_analysis 유지 |
| test_load_secret_reads_streamlit_toml | secrets.toml 로딩 |
| test_load_secret_skips_placeholders | placeholder 처리 |
| test_create_gemini_caller_supports_fake_client | fake client |
| test_router_dispatches_full_analysis_tool_locally | dispatch |
| test_router_rejects_unknown_tool | 예외 |

---

### 3.4 Fake LLM

- prompt별 JSON 반환

---

### 3.5 Fake Client

- generate_content 호출 기록
- 고정 JSON 반환
- 네트워크 없음

---

### 3.6 검증 범위

포함:
- API 유지
- Secret 로딩
- Caller 구조
- Router Dispatch

제외:
- 실제 API 품질
- Function Calling round-trip
- UI / RAG 연동

---

## 4. 부수 변경

### emotion/__init__.py

추가 export:
- DEFAULT_GEMINI_MODEL
- GeminiConnectorError
- GeminiFunctionCallingRouter
- ToolDispatchResult
- analyze_with_gemini_tools
- create_gemini_caller
- create_gemini_function_router
- load_secret

---

### requirements.txt

```text
google-genai
```

---

## 5. 사용 예시

### 기존 방식

```python
from src.emotion import create_gemini_caller, full_analysis

caller = create_gemini_caller()

result = full_analysis(
    ["너 왜 또 늦었어?", "미안해, 일이 늦게 끝났어."],
    dialogue_id="sample_001",
    llm_caller=caller,
)
```

---

### Router 방식

```python
from src.emotion import create_gemini_function_router

router = create_gemini_function_router()
response = router.route("대화의 감정과 갈등 위험도를 분석")
```

---

### Local Dispatch

```python
from src.emotion import GeminiFunctionCallingRouter

router = GeminiFunctionCallingRouter(llm_caller=fake_llm)

result = router.dispatch_tool(
    "full_dialogue_analysis",
    utterances=["너 왜 또 늦었어?", "미안해."],
    dialogue_id="local_sample",
)
```

---

## 6. 검증 결과

### 컴파일

```bash
python -m py_compile src/emotion/*.py
```

결과:
```
성공
```

---

### 테스트

```bash
python -m unittest discover -s tests
```

결과:
```
Ran 7 tests
OK
```

---

## 7. 향후 개선

- 실제 API 검증
- Function Calling round-trip
- Streamlit 연동
- RAG 연결
- 에러 메시지 개선

---

## 8. 결론

- 기존 코드와 호환 유지
- Gemini 확장 구조 확보
- Function Calling 구조 도입
- 테스트 가능 구조 완성

👉 확장성과 안정성을 모두 확보한 구조