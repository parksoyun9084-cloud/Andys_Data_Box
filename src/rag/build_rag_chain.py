# ============================================================
# - BM25 / Dense / RRF 기반 검색
# - response example 연결
# - example vector DB 기반 응답 예시 검색 추가
# - LLM으로 추천 답변 생성
# - 상황 요약 / 감정 / 위험도 / 추천 답변 / 피해야 할 표현 출력 강화
# - 연애/관계 갈등 전용 입력 분류 게이트 추가
# - 질문 정규화(normalize) 추가
# - 검색 결과 연인 관계 필터링 추가
# - 공감형 / 조언형 / 갈등 완충형 예시 선택 로직 보정
# ============================================================

from pathlib import Path
from collections import Counter, defaultdict
from typing import Any

import pandas as pd

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate

try:
    from .api_key_loader import load_api_key
    from .pinecone_vector_store import (
        EXAMPLE_INDEX_NAME,
        RAG_INDEX_NAME,
        get_pinecone_vector_store,
    )
except ImportError:
    from api_key_loader import load_api_key
    from pinecone_vector_store import (
        EXAMPLE_INDEX_NAME,
        RAG_INDEX_NAME,
        get_pinecone_vector_store,
    )


# ============================================================
# 1. 경로 설정
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAG_TEXT_PATH = PROCESSED_DATA_DIR / "rag_documents_with_text.csv"
RESPONSE_TEXT_PATH = PROCESSED_DATA_DIR / "response_pairs_with_text.csv"
TARGET_RESPONSE_STYLES = ("공감형", "조언형", "갈등 완충형")


# ============================================================
# 2. 유틸
# ============================================================
def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def classify_relationship_query(question: str) -> str:
    q = clean_text(question)

    lover_keywords = [
        "남자친구", "여자친구", "남친", "여친", "썸",
        "읽씹", "답장", "헤어지", "이별", "커플", "애인"
    ]

    if any(k in q for k in lover_keywords):
        return "relationship"

    return "unknown"


def normalize_relationship_query(question: str) -> str:
    q = clean_text(question)

    rules = [
        ("헤어", "연인 이별 갈등 감정 정리"),
        ("읽씹", "연인 연락 무시 답장 없음 서운함"),
        ("답장", "연인 연락 텍스트 무응답 갈등"),
        ("무시", "연인 감정 무시 서운함"),
        ("싸움", "연인 말다툼 감정 충돌"),
        ("잠수", "연인 연락 두절 회피 갈등"),
        ("정떨어", "연인 감정 소원 거리감"),
        ("차단", "연인 차단 갈등 이별 가능성"),
    ]

    expanded = []

    for key, value in rules:
        if key in q:
            expanded.append(value)

    if not expanded:
        return q

    return " ".join(expanded)


def build_search_query(question: str, conflict_type: str = "") -> str:
    base = normalize_relationship_query(question)

    query_parts = [base]

    if conflict_type:
        query_parts.append(conflict_type)

    return " ".join(query_parts)


def infer_emotion_from_question(question: str) -> str:
    q = clean_text(question)

    if any(kw in q for kw in ["서운", "속상", "상처"]):
        return "슬픔"
    if any(kw in q for kw in ["화", "짜증", "무시", "열받"]):
        return "분노"
    if any(kw in q for kw in ["불안", "걱정"]):
        return "불안"
    if any(kw in q for kw in ["답답", "지쳐"]):
        return "답답함"
    return ""


def extract_keywords_from_question(question: str) -> list[str]:
    candidates = [
        "서운", "속상", "무시", "안 들어", "대충", "화", "상처",
        "답답", "공감", "진지", "읽씹", "답장", "회피", "장난", "집중",
        "연락", "말다툼", "반복", "지쳐", "헤어지자", "잠수", "정떨어짐"
    ]
    return [kw for kw in candidates if kw in question]


# ============================================================
# 3. 데이터/모델 로드
# ============================================================
def load_dataframes() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not RAG_TEXT_PATH.exists():
        raise FileNotFoundError(f"파일이 없습니다: {RAG_TEXT_PATH}")
    if not RESPONSE_TEXT_PATH.exists():
        raise FileNotFoundError(f"파일이 없습니다: {RESPONSE_TEXT_PATH}")

    rag_df = pd.read_csv(RAG_TEXT_PATH)
    response_df = pd.read_csv(RESPONSE_TEXT_PATH)

    if "rag_text" not in rag_df.columns:
        raise ValueError("rag_df에 rag_text 컬럼이 없습니다.")

    rag_df["rag_text"] = rag_df["rag_text"].astype(str).str.strip()
    rag_df = rag_df[rag_df["rag_text"] != ""].copy()
    rag_df = rag_df.reset_index(drop=True)

    return rag_df, response_df


def build_bm25(rag_df: pd.DataFrame) -> Any:
    try:
        from rank_bm25 import BM25Okapi
    except ImportError as exc:
        raise ImportError(
            "rank_bm25 패키지가 설치되지 않았습니다. "
            "`pip install -r requirements.txt` 또는 `pip install rank-bm25`를 실행하세요."
        ) from exc

    rag_texts = rag_df["rag_text"].tolist()
    tokenized_rag_texts = [rag_text.split() for rag_text in rag_texts]
    return BM25Okapi(tokenized_rag_texts)


def load_vector_db(openai_api_key: str) -> Any:
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=openai_api_key,
    )

    vector_db = get_pinecone_vector_store(
        index_name=RAG_INDEX_NAME,
        embedding=embedding_model,
        pinecone_api_key=load_api_key("PINECONE_API_KEY"),
    )
    return vector_db


def load_example_vector_db(openai_api_key: str) -> Any:
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=openai_api_key,
    )

    example_vector_db = get_pinecone_vector_store(
        index_name=EXAMPLE_INDEX_NAME,
        embedding=embedding_model,
        pinecone_api_key=load_api_key("PINECONE_API_KEY"),
    )
    return example_vector_db


def load_llm(openai_api_key: str) -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        api_key=openai_api_key,
    )


# ============================================================
# 4. 검색 함수
# ============================================================
def bm25_search(query: str, rag_df: pd.DataFrame, bm25: Any, k: int = 3) -> list[dict]:
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)

    result_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:k]

    results = []
    for idx in result_indices:
        row = rag_df.iloc[idx]
        results.append({
            "dialogue_id": clean_text(row.get("dialogue_id", "")),
            "relation": clean_text(row.get("relation", "")),
            "situation": clean_text(row.get("situation", "")),
            "speaker_emotion": clean_text(row.get("speaker_emotion", "")),
            "risk_level": clean_text(row.get("risk_level", "")),
            "page_content": clean_text(row.get("rag_text", "")),
        })
    return results


def dense_search(query: str, vector_db: Any, k: int = 3) -> list[dict]:
    retrieved_docs = vector_db.similarity_search(query, k=k)

    results = []
    for retrieved_doc in retrieved_docs:
        results.append({
            "dialogue_id": clean_text(retrieved_doc.metadata.get("dialogue_id", "")),
            "relation": clean_text(retrieved_doc.metadata.get("relation", "")),
            "situation": clean_text(retrieved_doc.metadata.get("situation", "")),
            "speaker_emotion": clean_text(retrieved_doc.metadata.get("speaker_emotion", "")),
            "risk_level": clean_text(retrieved_doc.metadata.get("risk_level", "")),
            "page_content": clean_text(retrieved_doc.page_content),
        })
    return results


def example_dense_search(question: str, example_vector_db: Any, k: int = 5) -> list[dict]:
    retrieved_examples = example_vector_db.similarity_search(question, k=k)

    results = []
    for retrieved_doc in retrieved_examples:
        results.append({
            "dialogue_id": clean_text(retrieved_doc.metadata.get("dialogue_id", "")),
            "relation": clean_text(retrieved_doc.metadata.get("relation", "")),
            "situation": clean_text(retrieved_doc.metadata.get("situation", "")),
            "speaker_emotion": clean_text(retrieved_doc.metadata.get("speaker_emotion", "")),
            "listener_empathy": clean_text(retrieved_doc.metadata.get("listener_empathy", "")),
            "terminate": clean_text(retrieved_doc.metadata.get("terminate", "")),
            "listener_response": clean_text(retrieved_doc.metadata.get("listener_response", "")),
            "response_example_text": clean_text(retrieved_doc.page_content),
        })
    return results


def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60, top_n: int = 3) -> list[dict]:
    fused_scores = defaultdict(float)
    item_lookup = {}

    for result_list in result_lists:
        for rank, item in enumerate(result_list, start=1):
            dialogue_id = item["dialogue_id"]
            if not dialogue_id:
                continue
            fused_scores[dialogue_id] += 1 / (k + rank)
            item_lookup[dialogue_id] = item

    ranked_ids = sorted(
        fused_scores.keys(),
        key=lambda x: fused_scores[x],
        reverse=True
    )[:top_n]

    return [item_lookup[dialogue_id] for dialogue_id in ranked_ids]


def filter_relationship_documents(results: list[dict], k: int) -> list[dict]:
    if not results:
        return []

    filtered = []

    for doc in results:
        combined_text = " ".join([
            clean_text(doc.get("relation", "")),
            clean_text(doc.get("situation", "")),
            clean_text(doc.get("page_content", "")),
            clean_text(doc.get("speaker_emotion", "")),
        ])

        score = 0
        if "연인" in combined_text:
            score += 2
        if any(x in combined_text for x in ["남자친구", "여자친구", "커플"]):
            score += 2
        if any(x in combined_text for x in ["연애", "이별", "싸움", "서운"]):
            score += 1

        if score > 0:
            filtered.append((score, doc))

    if filtered:
        filtered.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in filtered[:k]]

    return results[:k]


def retrieve_documents(
    question: str,
    rag_df: pd.DataFrame | None,
    bm25: Any | None,
    vector_db: Any,
    method: str = "rrf",
    k: int = 3
) -> list[dict]:

    search_k = max(k * 4, 12)

    dense_results = dense_search(question, vector_db=vector_db, k=search_k)

    bm25_results = []
    if bm25 is not None and rag_df is not None:
        bm25_results = bm25_search(question, rag_df=rag_df, bm25=bm25, k=search_k)

    if method == "rrf":
        fused = reciprocal_rank_fusion(
            [bm25_results, dense_results],
            top_n=search_k
        )
    elif method == "bm25":
        fused = bm25_results
    else:
        fused = dense_results

    fused = filter_relationship_documents(fused, k=search_k)

    return fused[:k]


# ============================================================
# 5. 감정 / 위험도 / 상황 요약
# ============================================================
def get_main_emotion(question: str, retrieved_docs: list[dict]) -> str:
    question_emotion = infer_emotion_from_question(question)
    if question_emotion:
        return question_emotion

    emotions = [
        clean_text(doc.get("speaker_emotion", ""))
        for doc in retrieved_docs
        if clean_text(doc.get("speaker_emotion", ""))
    ]

    if not emotions:
        return "미상"

    return Counter(emotions).most_common(1)[0][0]


def get_main_risk_level(retrieved_docs: list[dict]) -> str:
    risk_levels = [
        clean_text(doc.get("risk_level", ""))
        for doc in retrieved_docs
        if clean_text(doc.get("risk_level", ""))
    ]

    if not risk_levels:
        return "미상"

    normalized = []
    risk_map = {
        "낮음": "낮음",
        "보통": "보통",
        "중간": "보통",
        "높음": "높음",
    }

    for risk in risk_levels:
        normalized.append(risk_map.get(risk, risk))

    counter = Counter(normalized)
    return counter.most_common(1)[0][0]


def summarize_current_situation(question: str, retrieved_docs: list[dict]) -> str:
    if not retrieved_docs:
        return clean_text(question)

    top_doc = retrieved_docs[0]
    relation = clean_text(top_doc.get("relation", "연인"))
    situation = clean_text(top_doc.get("situation", ""))
    emotion = clean_text(top_doc.get("speaker_emotion", ""))

    parts = []
    if relation:
        parts.append(f"{relation} 관계에서")
    if situation:
        parts.append(situation)
    if emotion:
        parts.append(f"주된 감정은 {emotion}")

    if parts:
        return ", ".join(parts)

    return clean_text(question)


# ============================================================
# 6. response example 연결
# ============================================================
def filter_response_examples_by_dialogue_ids(
    response_df: pd.DataFrame,
    dialogue_ids: list[str]
) -> pd.DataFrame:

    if response_df is None or response_df.empty:
        return pd.DataFrame()

    if "dialogue_id" not in response_df.columns:
        return response_df.copy()

    return response_df[
        response_df["dialogue_id"].astype(str).isin(dialogue_ids)
    ].copy()


def score_response_example(
    row: pd.Series,
    emotion: str,
    question_keywords: list[str]
) -> int:

    score = 0

    relation = clean_text(row.get("relation", ""))
    situation = clean_text(row.get("situation", ""))
    speaker_emotion = clean_text(row.get("speaker_emotion", ""))
    context_before_response = clean_text(row.get("context_before_response", ""))
    listener_response = clean_text(row.get("listener_response", ""))
    listener_empathy = clean_text(row.get("listener_empathy", ""))
    response_example_text = clean_text(row.get("response_example_text", ""))

    merged_text = " ".join([
        relation,
        situation,
        speaker_emotion,
        context_before_response,
        listener_response,
        listener_empathy,
        response_example_text,
    ])

    if "연인" in relation or "커플" in relation:
        score += 2

    if emotion and emotion in speaker_emotion:
        score += 3

    for kw in question_keywords:
        if kw in merged_text:
            score += 2

    if listener_empathy and listener_empathy != "미분류":
        score += 1

    if listener_response:
        score += 1

    return score


def map_listener_empathy_to_response_styles(listener_empathy: str) -> list[str]:
    empathy_text = clean_text(listener_empathy)

    if not empathy_text or empathy_text == "미분류":
        return []

    styles = []

    has_empathy = any(k in empathy_text for k in ["위로", "동조"])
    has_advice = any(k in empathy_text for k in ["조언", "격려", "방법", "해결", "해보자"])
    has_buffer = any(k in empathy_text for k in ["완화", "중재", "배려", "부드럽", "대화유지"])

    if has_empathy:
        styles.append("공감형")

    if has_advice:
        styles.append("조언형")

    if has_buffer or (has_empathy and has_advice):
        styles.append("갈등 완충형")

    return list(dict.fromkeys(styles))


def score_response_style_match(row: pd.Series, target_style: str) -> int:
    listener_empathy = clean_text(row.get("listener_empathy", ""))
    listener_response = clean_text(row.get("listener_response", ""))
    response_example_text = clean_text(row.get("response_example_text", ""))

    mapped_styles = map_listener_empathy_to_response_styles(listener_empathy)

    score = 0

    if target_style not in mapped_styles:
        score -= 5
    else:
        score += 8

    if target_style == "공감형":
        if any(k in listener_empathy for k in ["위로", "동조"]):
            score += 5
        if any(k in listener_response for k in ["속상", "힘들", "서운", "이해"]):
            score += 3

    elif target_style == "조언형":
        if any(k in listener_empathy for k in ["조언", "격려", "방법", "해결"]):
            score += 6
        if any(k in listener_response for k in ["해보", "시도", "천천히", "같이", "방법"]):
            score += 4

    elif target_style == "갈등 완충형":
        if any(k in listener_empathy for k in ["조언", "격려", "위로", "동조", "완화", "중재", "배려"]):
            score += 4

        soft_text = listener_response + " " + response_example_text

        if not any(k in soft_text for k in ["왜", "맨날", "항상", "네가", "니가"]):
            score += 4

        if any(k in soft_text for k in ["괜찮", "이해", "천천히", "같이", "부담", "편할 때"]):
            score += 3

    return score


def _response_text_from_row(row: pd.Series) -> str:
    listener_response = clean_text(row.get("listener_response", ""))

    if listener_response:
        return listener_response

    return clean_text(row.get("response_example_text", ""))


def build_response_example_candidates(
    response_df: pd.DataFrame | None,
    retrieved_docs: list[dict],
    emotion: str,
    question: str,
    example_vector_db: Any,
) -> pd.DataFrame:

    dialogue_ids = [
        clean_text(doc.get("dialogue_id", ""))
        for doc in retrieved_docs
        if clean_text(doc.get("dialogue_id", ""))
    ]

    base_df = pd.DataFrame()

    if response_df is not None and not response_df.empty:
        base_df = filter_response_examples_by_dialogue_ids(response_df, dialogue_ids)

    vector_candidates = example_dense_search(question, example_vector_db, k=5)
    vector_df = pd.DataFrame(vector_candidates)

    if not base_df.empty and not vector_df.empty:
        base_df = pd.concat([base_df, vector_df], ignore_index=True)
    elif base_df.empty:
        base_df = vector_df

    if base_df.empty:
        return base_df

    question_keywords = extract_keywords_from_question(question)

    base_df["score"] = base_df.apply(
        lambda row: score_response_example(row, emotion, question_keywords),
        axis=1
    )

    return base_df


def select_style_labeled_response_examples(
    candidate_df: pd.DataFrame | None,
    target_styles=TARGET_RESPONSE_STYLES,
) -> list[dict]:
    if candidate_df is None or candidate_df.empty:
        return []

    selected = []
    used_texts = set()

    for style in target_styles:
        rows = []

        for _, row in candidate_df.iterrows():
            mapped = map_listener_empathy_to_response_styles(
                row.get("listener_empathy", "")
            )

            if style not in mapped:
                continue

            text = _response_text_from_row(row)
            if not text:
                continue

            if text in used_texts:
                continue

            score = int(row.get("score", 0)) + score_response_style_match(row, style)
            rows.append((score, row))

        rows.sort(key=lambda x: x[0], reverse=True)

        if rows:
            best = rows[0][1]
            text = _response_text_from_row(best)

            used_texts.add(text)

            selected.append({
                "label": style,
                "text": text,
                "dialogue_id": clean_text(best.get("dialogue_id", "")),
            })

    return selected


def format_labeled_response_examples(recommended_replies: list[dict]) -> str:
    return "\n\n".join([
        f"[응답 예시 {i + 1} - {r['label']}]\n{r['text']}"
        for i, r in enumerate(recommended_replies)
    ])


def get_labeled_response_examples(
    response_df: pd.DataFrame | None,
    retrieved_docs: list[dict],
    emotion: str,
    question: str,
    example_vector_db: Any,
) -> list[dict]:

    candidate_df = build_response_example_candidates(
        response_df=response_df,
        retrieved_docs=retrieved_docs,
        emotion=emotion,
        question=question,
        example_vector_db=example_vector_db,
    )

    return select_style_labeled_response_examples(candidate_df)


def get_response_examples(
    response_df: pd.DataFrame | None,
    retrieved_docs: list[dict],
    emotion: str,
    question: str,
    example_vector_db: Any,
    top_n: int = 3
) -> str:

    recommended_replies = get_labeled_response_examples(
        response_df=response_df,
        retrieved_docs=retrieved_docs,
        emotion=emotion,
        question=question,
        example_vector_db=example_vector_db,
    )

    if recommended_replies:
        return format_labeled_response_examples(recommended_replies[:top_n])

    candidate_df = build_response_example_candidates(
        response_df=response_df,
        retrieved_docs=retrieved_docs,
        emotion=emotion,
        question=question,
        example_vector_db=example_vector_db,
    )

    if candidate_df.empty:
        return ""

    text_col = (
        "response_example_text"
        if "response_example_text" in candidate_df.columns
        else "listener_response"
    )

    selected = candidate_df.sort_values(
        by="score",
        ascending=False
    ).head(top_n)[text_col].astype(str).tolist()

    return "\n\n".join([
        f"[응답 예시 {i + 1}]\n{ex}"
        for i, ex in enumerate(selected)
    ])


def format_docs(docs: list[dict]) -> str:
    formatted = []

    for i, doc in enumerate(docs, start=1):
        block = [
            f"[유사 사례 {i}]",
            f"dialogue_id: {doc.get('dialogue_id', '')}",
            f"관계: {doc.get('relation', '')}",
            f"상황: {doc.get('situation', '')}",
            f"화자 감정: {doc.get('speaker_emotion', '')}",
            f"위험도: {doc.get('risk_level', '')}",
            f"본문 일부: {doc.get('page_content', '')[:500]}",
        ]

        formatted.append("\n".join(block))

    return "\n\n".join(formatted)


# ============================================================
# 7. 프롬프트
# ============================================================
PROMPT = PromptTemplate.from_template(
"""
너는 연인 갈등 상황에서 사용자가 연인에게 보낼 답장을 추천하는 AI다.

반드시 연인/커플/남녀 관계 갈등 상황으로만 해석할 것.
미용실, 정치, 사회 일반 의미로 해석하지 말 것.
사용자가 작성한 상황에 대해 혼자만의 상상으로 상황을 만들지 말 것.
검색 결과가 없거나 관련성이 낮으면 검색 문서를 무시하고 사용자의 입력만을 기준으로 작성할 것.

사용자가 연인과의 갈등 상황을 설명하면
현재 상황 요약, 감정, 위험도,
그리고 반드시 서로 다른 스타일의 AI 추천 답변 3개를 생성해야 한다.

--------------------------------------------------
[핵심 규칙]
- 공감형 / 조언형 / 갈등 완충형 3개 답변을 반드시 모두 작성할 것
- 세 답변은 서로 문장 구조와 표현이 겹치면 안 된다
- 각 답변은 실제 카톡에 바로 보낼 수 있게 자연스럽게 작성할 것
- 너무 상담사처럼 말하지 말 것
- 공격적 / 비난 / 훈계 말투 금지
- 각 답변은 2~4문장
- 첫 문장은 사용자의 감정을 이해하는 말로 시작할 것
- 유사 사례와 응답 예시는 참고만 하고 그대로 복사 금지
- 아래 태그 형식을 반드시 정확히 지킬 것: [공감형], [조언형], [갈등 완충형]

--------------------------------------------------
[스타일 정의]

[공감형]
- 감정 위로 중심
- 해결책 제시하지 말 것
- 서운함, 속상함, 답답함을 이해해주는 말투

[조언형]
- 문제 해결 중심
- 어떻게 말하면 좋을지 제안
- 행동 방법 제시
- 공감은 짧게 1문장만

[갈등 완충형]
- 싸움이 커지지 않도록 부드럽게 전달
- 내 감정 + 상대 배려 동시 포함
- 대화 이어갈 수 있게 작성

--------------------------------------------------
사용자 입력:
{question}

상황 요약:
{situation_summary}

대표 감정:
{main_emotion}

갈등 위험도:
{risk_level}

유사 사례:
{context}

참고 응답 예시:
{response_examples}

--------------------------------------------------
반드시 아래 형식 그대로 출력할 것.

[상황 요약]
...

[감정]
...

[위험도]
...

[공감형]
...

[조언형]
...

[갈등 완충형]
...

[피해야 할 표현]
...

[대체 표현]
...
"""
)


# ============================================================
# 8. 메인 생성 함수
# ============================================================
def generate_recommended_reply(
    question: str,
    conflict_type: str = "",
    method: str = "rrf",
    k: int = 3,
    use_local_csv: bool = False,
) -> dict:

    openai_api_key = load_api_key()

    query_type = classify_relationship_query(question)
    if query_type != "relationship":
        return {
            "question": question,
            "query_type": query_type,
            "result_text": "연애/커플 상황이 아닙니다."
        }

    rag_df = response_df = bm25 = None

    if use_local_csv or method in ("bm25", "rrf"):
        rag_df, response_df = load_dataframes()
        bm25 = build_bm25(rag_df)

    vector_db = load_vector_db(openai_api_key)
    example_vector_db = load_example_vector_db(openai_api_key)
    llm = load_llm(openai_api_key)

    search_query = build_search_query(question, conflict_type)

    retrieved_docs = retrieve_documents(
        question=search_query,
        rag_df=rag_df,
        bm25=bm25,
        vector_db=vector_db,
        method=method,
        k=k,
    )

    situation_summary = summarize_current_situation(question, retrieved_docs)
    main_emotion = get_main_emotion(question, retrieved_docs)
    risk_level = get_main_risk_level(retrieved_docs)

    context = format_docs(retrieved_docs) if retrieved_docs else "검색 결과 없음"

    response_examples = get_response_examples(
        response_df=response_df,
        retrieved_docs=retrieved_docs,
        emotion=main_emotion,
        question=question,
        example_vector_db=example_vector_db,
    )

    prompt = PROMPT.format(
        question=question,
        situation_summary=situation_summary,
        main_emotion=main_emotion,
        risk_level=risk_level,
        context=context,
        response_examples=response_examples,
    )

    result = llm.invoke(prompt)

    return {
        "question": question,
        "query_type": query_type,
        "search_query": search_query,
        "retrieved_docs": retrieved_docs,
        "situation_summary": situation_summary,
        "main_emotion": main_emotion,
        "risk_level": risk_level,
        "response_examples": response_examples,
        "result_text": result.content,
    }


# ============================================================
# 9. 단독 실행 테스트
# ============================================================
def main() -> None:
    test_question = "남자친구가 내 말을 제대로 안 들어주는 것 같아서 서운해. 어떻게 보내면 좋을까?"
    output = generate_recommended_reply(test_question, method="rrf", k=3)

    print("\n===== 입력 질문 =====")
    print(output["question"])

    print("\n===== 입력 분류 =====")
    print(output["query_type"])

    print("\n===== 정규화 검색어 =====")
    print(output["search_query"])

    print("\n===== 검색된 유사 사례 수 =====")
    print(len(output["retrieved_docs"]))

    print("\n===== 상황 요약 =====")
    print(output["situation_summary"])

    print("\n===== 대표 감정 =====")
    print(output["main_emotion"])

    print("\n===== 갈등 위험도 =====")
    print(output["risk_level"])

    print("\n===== 응답 예시 =====")
    print(output["response_examples"])

    print("\n===== 최종 생성 결과 =====")
    print(output["result_text"])


if __name__ == "__main__":
    main()