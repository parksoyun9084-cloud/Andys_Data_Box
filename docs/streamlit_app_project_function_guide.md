# Streamlit App 프로젝트 함수 사용 가이드

## 1. 문서 목적

본 문서는 `app/streamlit_app.py`를 기준으로, 프로젝트에 구현된 감정 분석, 위험도 분석, RAG 추천 답변 생성 기능을 Streamlit UI와 연결하는 방법을 정리한 문서이다.

현재 Streamlit 앱은 UI 구조가 먼저 구성된 상태이며, 실제 서비스 동작을 위해서는 `src/emotion`, `src/rag`, `src/app_service.py`의 기능을 연결해야 한다.

---

## 2. 현재 Streamlit App 구조

### 대상 파일

```text
app/streamlit_app.py
```

### 주요 함수

| 함수 | 역할 | 현재 상태 |
|---|---|---|
| `apply_custom_css()` | 화면 CSS 적용 | 사용 중 |
| `render_analysis_card()` | 감정/위험도 카드 렌더링 | 동적 데이터 연결 필요 |
| `render_history_item()` | 히스토리 항목 렌더링 | 세션 데이터 연결 필요 |
| `main()` | 전체 화면 구성 | 분석 로직 연결 필요 |

---

## 3. 우선 연결할 기능

1. 사용자 입력 저장
2. 갈등 유형 선택값 저장
3. 감정 및 위험도 분석
4. RAG 기반 추천 답변 생성
5. 분석 결과 payload 생성
6. 감정/위험도 카드 동적 표시
7. 추천 답변 동적 표시
8. 대화 히스토리 저장 및 표시

---

## 4. 권장 통합 방식

현재 프로젝트에는 전체 분석 흐름을 연결하는 서비스 함수가 존재한다.

```python
from src.app_service import run_chat_analysis
```

`run_chat_analysis()`는 사용자 입력과 갈등 유형을 받아 다음 흐름을 수행한다.

```text
사용자 입력
→ Gemini 감정/위험도 분석
→ RAG 추천 답변 생성
→ 결과 payload 정리
→ Streamlit UI 출력용 데이터 반환
```

따라서 Streamlit 앱에서는 개별 함수를 직접 모두 호출하기보다, 우선 `run_chat_analysis()`를 중심으로 연결하는 방식을 권장한다.

---

## 5. 프로젝트 import 경로 설정

`app/streamlit_app.py`가 `app/` 폴더 안에 있으므로, `src` 모듈 import를 위해 프로젝트 루트를 path에 추가한다.

```python
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
```

---

## 6. Streamlit 캐시 적용

동일한 입력을 반복 분석하지 않도록 Streamlit 캐시를 적용한다.

```python
import streamlit as st
from src.app_service import run_chat_analysis

@st.cache_data(ttl=600, show_spinner=False)
def cached_analysis(user_text: str, conflict_type: str):
    return run_chat_analysis(user_text, conflict_type=conflict_type)
```

---

## 7. 사용자 입력 처리 예시

```python
if prompt := st.chat_input("현재 상황을 입력해주세요."):
    prompt = prompt.strip()

    if not prompt:
        st.stop()

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    st.session_state.pending_prompt = prompt
    st.session_state.pending_conflict_type = st.session_state.conflict_type

    st.rerun()
```

---

## 8. 분석 실행 예시

```python
if st.session_state.pending_prompt:
    with st.spinner("AI 분석 중..."):
        try:
            prompt = st.session_state.pending_prompt
            conflict_type = st.session_state.pending_conflict_type

            result = cached_analysis(prompt, conflict_type)

            result["user_input"] = prompt
            result["conflict_type"] = conflict_type

            st.session_state.latest_result = result

            st.session_state.messages.append({
                "role": "assistant",
                "avatar": "🎁",
                "content": "분석이 완료됐어요. 오른쪽 패널에서 결과를 확인해보세요.",
            })

            st.session_state.history.insert(0, result)

            st.session_state.pending_prompt = None
            st.session_state.pending_conflict_type = None

            st.rerun()

        except Exception as e:
            st.session_state.error_message = str(e)
            st.session_state.pending_prompt = None
            st.session_state.pending_conflict_type = None
            st.rerun()
```

---

## 9. 감정/위험도 카드 연결

`latest_result`에서 감정과 위험도 정보를 가져와 카드에 표시한다.

```python
latest = st.session_state.latest_result

if latest:
    emotion_info = latest.get("emotion", {})
    risk_info = latest.get("risk", {})

    emotion_label = emotion_info.get("label", "미분석")
    emotion_score = int(emotion_info.get("score", 0))

    risk_label = risk_info.get("label", "미분석")
    risk_score = int(risk_info.get("score", 0))
else:
    emotion_label = "대기 중"
    emotion_score = 0
    risk_label = "대기 중"
    risk_score = 0
```

카드 렌더링 예시:

```python
render_analysis_card(
    title="감정 분석",
    emoji="🙂",
    label=emotion_label,
    score=emotion_score,
    color="#5C7CFA",
)

render_analysis_card(
    title="위험도 분석",
    emoji="⏱️",
    label=risk_label,
    score=risk_score,
    color="#E74C3C",
)
```

---

## 10. 분석 리포트 연결

```python
if latest:
    render_report_item("🏷️", "갈등유형", latest.get("conflict_type", "미선택"))
    render_report_item("📝", "상황 요약", latest.get("summary_text", ""))
    render_report_item("💬", "감정 해석", latest.get("emotion_text", ""))
    render_report_item("⚠️", "위험도 해석", latest.get("risk_text", ""))

    risk_obj = latest.get("risk", {})
    if isinstance(risk_obj, dict) and risk_obj.get("recommendation"):
        render_report_item("🧭", "대응 가이드", risk_obj["recommendation"])
```

---

## 11. 추천 답변 연결

`run_chat_analysis()` 결과에는 추천 답변 3종이 포함된다.

```python
styles = [
    ("공감형", "💛", latest.get("empathy_reply", "")),
    ("조언형", "🗣️", latest.get("advice_reply", "")),
    ("갈등 완충형", "🤝", latest.get("buffer_reply", "")),
]
```

렌더링 예시:

```python
for label, icon, reply in styles:
    if reply:
        st.markdown(
            f"""
            <div class="list-item">
                <div class="item-icon">{icon}</div>
                <div class="item-content" style="padding-right:0;">
                    <strong>{label}</strong><br>{reply}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
```

---

## 12. 피해야 할 표현 / 대체 표현 연결

```python
avoid_phrases = latest.get("avoid_phrases", [])
alternative_phrases = latest.get("alternative_phrases", [])
```

렌더링 예시:

```python
render_phrase_box(
    "피해야 할 표현",
    avoid_phrases[:3],
    "없음",
)

render_phrase_box(
    "대체 표현",
    alternative_phrases[:3],
    "없음",
)
```

---

## 13. 대화 히스토리 연결

```python
if st.session_state.history:
    for index, item in enumerate(st.session_state.history[:3]):
        title = f"[{item.get('conflict_type', '미선택')}] {item.get('user_input', '')[:24]}"
        preview = "오른쪽 패널에서 결과를 확인해보세요."

        render_history_item(
            "👩🏻‍❤️‍🧑🏻",
            title,
            "방금" if index == 0 else f"{index + 1}분전",
            preview,
            is_active=(index == 0),
        )
else:
    render_history_item(
        "👩🏻‍❤️‍🧑🏻",
        "히스토리 없음",
        "-",
        "첫 분석을 시작해보세요.",
        True,
    )
```

---

## 14. 개별 함수 직접 호출 방식

필요한 경우 아래 프로젝트 함수를 직접 사용할 수 있다.

### 14.1 RAG 추천 답변 생성

```python
from src.rag.build_rag_chain import generate_recommended_reply

rag_result = generate_recommended_reply(
    question="남자친구가 내 말을 제대로 안 들어줘서 서운해.",
    conflict_type="연락 문제 > 답장 지연",
    method="rrf",
    k=3,
)
```

---

### 14.2 Gemini 감정/위험도 통합 분석

```python
from src.emotion import create_gemini_caller, full_analysis

llm_caller = create_gemini_caller()

analysis = full_analysis(
    ["너 왜 또 늦었어?", "미안해. 일이 늦게 끝났어."],
    dialogue_id="chat_001",
    llm_caller=llm_caller,
)
```

---

### 14.3 Gemini Function Calling Router

```python
from src.emotion import create_gemini_function_router

router = create_gemini_function_router()

response = router.route(
    "다음 대화의 감정 흐름과 갈등 위험도를 분석해줘."
)
```

---

## 15. 기능별 사용 판단표

| Streamlit 기능 | 사용할 함수 또는 데이터 | 비고 |
|---|---|---|
| 전체 분석 실행 | `run_chat_analysis()` | 권장 통합 방식 |
| 추천 답변 생성 | `generate_recommended_reply()` | 개별 호출 시 사용 |
| 감정/위험도 분석 | `full_analysis()` | 개별 호출 시 사용 |
| Gemini caller 생성 | `create_gemini_caller()` | Gemini API Key 필요 |
| Function Calling | `create_gemini_function_router()` | 자유 분석 요청용 |
| 검색 문서 표시 | `retrieved_docs` | 근거 표시용 |
| 추천 예시 표시 | `response_examples` | UI 확장용 |

---

## 16. 최소 구현 순서

1. 프로젝트 루트 path 설정
2. `run_chat_analysis()` import
3. `cached_analysis()` 추가
4. 사용자 입력 저장
5. pending 상태 저장
6. 분석 실행 후 `latest_result` 저장
7. 감정/위험도 카드 동적 연결
8. 추천 답변 3종 연결
9. 피해야 할 표현/대체 표현 연결
10. 히스토리 저장 및 표시
11. 에러 메시지 처리
12. API Key 기반 smoke test

---

## 17. 주의 사항

### 17.1 API Key

- Secret 값은 출력하지 않는다.
- `.streamlit/secrets.toml`을 우선 사용한다.
- `.env`는 fallback 용도로 사용한다.

### 17.2 비용

`run_chat_analysis()`는 Gemini 분석과 RAG 답변 생성을 함께 수행하므로 LLM 호출 비용이 발생한다.

따라서 사용자 입력 시에만 실행하고, 동일 입력은 캐시를 활용한다.

### 17.3 속도

RAG 검색 및 벡터 DB 로딩은 시간이 걸릴 수 있다.  
Streamlit에서는 `st.cache_data`, `st.cache_resource`를 적극 활용한다.

예시:

```python
@st.cache_resource
def get_gemini_caller():
    from src.emotion import create_gemini_caller
    return create_gemini_caller()
```

---

## 18. 최종 정리

현재 Streamlit 앱은 UI 구조가 먼저 구현된 상태이며, 이후 핵심 작업은 프로젝트 함수와 실제 분석 결과를 연결하는 것이다.

최종적으로 Streamlit 앱은 다음 흐름으로 동작한다.

```text
갈등 유형 선택
→ 사용자 상황 입력
→ 감정/위험도 분석
→ RAG 기반 답변 생성
→ UI 출력
→ 히스토리 저장
```