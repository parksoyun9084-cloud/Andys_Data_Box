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
# - LLM 출력 태그 파싱 / 누락 스타일 자동 재생성 추가
# - 상담형 문체 감지 / 답장형 검증 강화
# ============================================================

from pathlib import Path
from collections import Counter, defaultdict
from typing import Any
import re

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
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_section_label(label: str) -> str:
    label = clean_text(label).replace(" ", "")
    alias_map = {
        "상황요약": "상황 요약",
        "감정": "감정",
        "위험도": "위험도",
        "공감형": "공감형",
        "조언형": "조언형",
        "갈등완충형": "갈등 완충형",
        "피해야할표현": "피해야 할 표현",
        "대체표현": "대체 표현",
    }
    return alias_map.get(label, clean_text(label))


def parse_llm_sections(text: str) -> dict[str, str]:
    if not text:
        return {}

    safe_text = clean_text(text).replace("\r\n", "\n").replace("\r", "\n")

    raw_labels = [
        "상황 요약", "상황요약",
        "감정",
        "위험도",
        "공감형",
        "조언형",
        "갈등 완충형", "갈등완충형",
        "피해야 할 표현", "피해야할표현",
        "대체 표현", "대체표현",
    ]

    pattern = r"\[\s*(" + "|".join(map(re.escape, raw_labels)) + r")\s*\]"
    parts = re.split(pattern, safe_text)

    sections: dict[str, str] = {}
    for i in range(1, len(parts), 2):
        raw_label = clean_text(parts[i])
        content = clean_text(parts[i + 1]) if i + 1 < len(parts) else ""
        normalized = normalize_section_label(raw_label)
        sections[normalized] = content

    return sections


def split_lines_as_list(text: str) -> list[str]:
    if not text:
        return []

    normalized = clean_text(text).replace("•", "\n• ").replace(" - ", "\n- ")
    lines = []
    for line in normalized.split("\n"):
        cleaned = clean_text(line).lstrip("-").lstrip("•").strip()
        if cleaned:
            lines.append(cleaned)

    return lines


def is_reply_to_user_instead_of_partner(text: str) -> bool:
    """
    사용자를 위로하거나 상담하는 문체인지 감지한다.
    목표는 '상대방에게 보낼 답장'이어야 하므로 이런 문체는 실패 처리한다.
    """
    t = clean_text(text)

    counseling_phrases = [
        "네가 느끼는",
        "네 마음",
        "많이 힘들었겠다",
        "얼마나 힘들",
        "이해해",
        "당연해",
        "지쳤겠",
        "속상했겠",
        "마음이 아플",
        "그럴 수밖에 없",
        "힘들 것 같",
        "상처였을 것 같",
        "그 상황이면",
        "많이 속상했겠",
        "정말 힘들겠",
        "얼마나 속상",
    ]

    if t.startswith("너") or t.startswith("네가"):
        return True

    return any(x in t for x in counseling_phrases)


def is_not_using_i_statement(text: str) -> bool:
    """
    답장은 기본적으로 '나/내/우리' 화법이어야 한다.
    해당 표현이 전혀 없으면 훈계형/설명형일 가능성이 높다.
    """
    t = clean_text(text)

    i_statement_tokens = ["나 ", "내 ", "나는", "내가", "내 입장", "우리", "나는 ", "내가 "]
    return not any(token in t for token in i_statement_tokens)


def ensure_style_labels_present(sections: dict[str, str]) -> bool:
    if not all(clean_text(sections.get(style, "")) for style in TARGET_RESPONSE_STYLES):
        return False

    for style in TARGET_RESPONSE_STYLES:
        text = clean_text(sections.get(style, ""))

        if is_reply_to_user_instead_of_partner(text):
            return False

        if is_not_using_i_statement(text):
            return False

    return True


def classify_relationship_query(question: str) -> str:
    q = clean_text(question)

    lover_keywords = [
        "남자친구", "여자친구", "남친", "여친", "썸",
        "읽씹", "답장", "헤어지", "이별", "커플", "애인", "연인"
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
    if any(kw in q for kw in ["불안", "걱정", "의심"]):
        return "불안"
    if any(kw in q for kw in ["답답", "지쳐"]):
        return "답답함"
    return ""


def extract_keywords_from_question(question: str) -> list[str]:
    candidates = [
        "서운", "속상", "무시", "안 들어", "대충", "화", "상처",
        "답답", "공감", "진지", "읽씹", "답장", "회피", "장난", "집중",
        "연락", "말다툼", "반복", "지쳐", "헤어지자", "잠수", "정떨어짐",
        "의심", "거짓말", "불안"
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
        if any(x in combined_text for x in ["연애", "이별", "싸움", "서운", "의심"]):
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

    if method == "bm25":
        raise ValueError("BM25 requires local CSV files and is disabled for Streamlit runtime.")

    dense_results = dense_search(question, vector_db=vector_db, k=search_k)

    bm25_results = []
    if bm25 is not None and rag_df is not None:
        bm25_results = bm25_search(question, rag_df=rag_df, bm25=bm25, k=search_k)

    if method == "rrf":
        fused = reciprocal_rank_fusion(
            [bm25_results, dense_results],
            top_n=search_k
        )
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

    has_empathy = any(k in empathy_text for k in ["위로", "동조", "공감"])
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
        if any(k in listener_empathy for k in ["위로", "동조", "공감"]):
            score += 5
        if any(k in listener_response for k in ["속상", "힘들", "서운", "이해"]):
            score += 3

    elif target_style == "조언형":
        if any(k in listener_empathy for k in ["조언", "격려", "방법", "해결"]):
            score += 6
        if any(k in listener_response for k in ["해보", "시도", "천천히", "같이", "방법"]):
            score += 4

    elif target_style == "갈등 완충형":
        if any(k in listener_empathy for k in ["조언", "격려", "위로", "동조", "완화", "중재", "배려", "공감"]):
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
너는 연인 갈등 상황에서 사용자가 연인에게 실제로 보낼 답장을 추천하는 AI다.

반드시 연인/커플/남녀 관계 갈등 상황으로만 해석할 것.
미용실, 정치, 사회 일반 의미로 해석하지 말 것.
사용자가 작성한 상황에 대해 혼자만의 상상으로 상황을 만들지 말 것.
검색 결과가 없거나 관련성이 낮으면 검색 문서를 무시하고 사용자의 입력만을 기준으로 작성할 것.

중요:
너의 역할은 사용자를 위로하거나 상담하는 것이 아니다.
반드시 "사용자가 상대방에게 직접 보낼 수 있는 메시지"를 작성해야 한다.

--------------------------------------------------
[핵심 규칙]
- 공감형 / 조언형 / 갈등 완충형 3개 답변을 반드시 모두 작성할 것
- 세 답변은 모두 "상대에게 보내는 답장"이어야 한다
- 세 답변은 서로 문장 구조와 표현이 겹치면 안 된다
- 각 답변은 실제 카톡에 바로 복붙할 수 있게 자연스럽게 작성할 것
- 각 답변은 반드시 "문자 그대로 상대에게 보낼 수 있는 문장"만 작성할 것
- 설명문 금지, 해설문 금지, 상담문 금지
- 너무 상담사처럼 말하지 말 것
- 공격적 / 비난 / 훈계 말투 금지
- 각 답변은 2~4문장
- 답변은 반드시 "나 / 내" 화법을 기본으로 작성할 것
- 필요하면 "너", "우리"를 사용할 수 있다
- "네가 느끼는", "네 마음", "많이 힘들었겠다", "이해해", "당연해"처럼
  사용자를 위로하는 상담형 문장은 쓰지 말 것
- 유사 사례와 응답 예시는 참고만 하고 그대로 복사 금지
- 참고 응답 예시는 "상대에게 보낼 메시지의 말투"만 참고할 것
- 아래 태그 형식을 반드시 정확히 지킬 것: [공감형], [조언형], [갈등 완충형]

--------------------------------------------------
[스타일 정의]

[공감형]
- 상대를 비난하지 않고 내 감정을 전달하는 답장
- 해결책 제시보다 감정 전달이 중심
- 예: 서운함, 속상함, 답답함을 "내 입장"에서 담백하게 표현

[조언형]
- 관계를 풀기 위해 내가 바라는 점이나 요청을 분명히 담는 답장
- 문제 해결 중심
- 어떻게 해줬으면 하는지 구체적으로 포함
- 공감 표현은 짧게, 요청은 분명하게

[갈등 완충형]
- 싸움이 커지지 않도록 부드럽게 말하는 답장
- 내 감정 + 상대 배려 + 대화 이어가기 포함
- 부담스럽지 않게 대화의 문을 여는 말투

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

REPAIR_PROMPT = PromptTemplate.from_template(
"""
아래 초안은 연인 갈등 답변 추천 결과다.
하지만 형식이 불완전하거나 일부 스타일이 누락되었거나,
사용자에게 상담하듯 말하는 문장이 섞여 있거나,
상대에게 바로 보낼 수 없는 설명형 문장이 들어 있다.

너는 반드시 아래 8개 태그를 모두 포함해 다시 작성해야 한다.
태그명은 한 글자도 바꾸지 마라.

반드시 포함할 태그:
[상황 요약]
[감정]
[위험도]
[공감형]
[조언형]
[갈등 완충형]
[피해야 할 표현]
[대체 표현]

중요 규칙:
- 공감형 / 조언형 / 갈등 완충형은 반드시 모두 작성
- 세 답변은 모두 "사용자가 상대방에게 직접 보내는 메시지"여야 함
- 사용자에게 설명하거나 위로하는 상담형 문장 금지
- "네가 느끼는", "네 마음", "많이 힘들었겠다", "이해해", "당연해" 금지
- 답변은 "나 / 내" 화법 중심
- 각 답변은 문자 그대로 상대에게 복붙 가능한 문장만 작성
- 공감형은 감정 전달 중심
- 조언형은 행동 요청 중심
- 갈등 완충형은 감정 + 상대 배려 + 대화 연결
- 각 답변은 2~4문장
- 실제 카톡처럼 자연스럽게

원래 사용자 질문:
{question}

보조 정보:
상황 요약: {situation_summary}
대표 감정: {main_emotion}
위험도: {risk_level}

초안:
{draft}
"""
)


# ============================================================
# 8. LLM 출력 보정
# ============================================================
def build_structured_result_from_sections(
    question: str,
    query_type: str,
    search_query: str,
    retrieved_docs: list[dict],
    situation_summary: str,
    main_emotion: str,
    risk_level: str,
    response_examples: str,
    raw_text: str,
    sections: dict[str, str],
    method: str = "pinecone",
    recommended_replies: list[dict] | None = None,
) -> dict:
    return {
        "question": question,
        "query_type": query_type,
        "method": method,
        "search_query": search_query,
        "retrieved_docs": retrieved_docs,
        "situation_summary": situation_summary,
        "main_emotion": main_emotion,
        "risk_level": risk_level,
        "response_examples": response_examples,
        "recommended_replies": recommended_replies or [],
        "result_text": raw_text,
        "assistant_message": raw_text,
        "summary_text": clean_text(sections.get("상황 요약")) or situation_summary,
        "emotion_text": clean_text(sections.get("감정")) or main_emotion,
        "risk_text": clean_text(sections.get("위험도")) or risk_level,
        "empathy_reply": clean_text(sections.get("공감형")),
        "advice_reply": clean_text(sections.get("조언형")),
        "buffer_reply": clean_text(sections.get("갈등 완충형")),
        "avoid_phrases": split_lines_as_list(sections.get("피해야 할 표현", "")),
        "alternative_phrases": split_lines_as_list(sections.get("대체 표현", "")),
        "parsed_sections": sections,
    }


def repair_llm_output_if_needed(
    llm: ChatOpenAI,
    question: str,
    situation_summary: str,
    main_emotion: str,
    risk_level: str,
    raw_text: str,
) -> tuple[str, dict[str, str]]:
    sections = parse_llm_sections(raw_text)

    if ensure_style_labels_present(sections):
        return raw_text, sections

    repair_prompt = REPAIR_PROMPT.format(
        question=question,
        situation_summary=situation_summary,
        main_emotion=main_emotion,
        risk_level=risk_level,
        draft=raw_text,
    )

    repaired = llm.invoke(repair_prompt)
    repaired_text = clean_text(repaired.content)
    repaired_sections = parse_llm_sections(repaired_text)

    if ensure_style_labels_present(repaired_sections):
        return repaired_text, repaired_sections

    return raw_text, sections


# ============================================================
# 9. 메인 생성 함수
# ============================================================
def generate_recommended_reply(
    question: str,
    conflict_type: str = "",
    method: str = "pinecone",
    k: int = 3,
    use_local_csv: bool = False,
) -> dict:

    openai_api_key = load_api_key()

    query_type = classify_relationship_query(question)
    if query_type != "relationship":
        return {
            "question": question,
            "query_type": query_type,
            "method": method,
            "result_text": "연애/커플 상황이 아닙니다.",
            "assistant_message": "연애/커플 상황이 아닙니다.",
            "summary_text": "",
            "emotion_text": "",
            "risk_text": "",
            "empathy_reply": "",
            "advice_reply": "",
            "buffer_reply": "",
            "recommended_replies": [],
            "avoid_phrases": [],
            "alternative_phrases": [],
            "parsed_sections": {},
        }

    if use_local_csv:
        raise ValueError("Streamlit runtime is Pinecone-only. Local CSV loading is disabled.")

    rag_df = response_df = bm25 = None

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

    recommended_replies = get_labeled_response_examples(
        response_df=response_df,
        retrieved_docs=retrieved_docs,
        emotion=main_emotion,
        question=question,
        example_vector_db=example_vector_db,
    )
    if recommended_replies:
        response_examples = format_labeled_response_examples(recommended_replies[:3])
    else:
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
    raw_text = clean_text(result.content)

    repaired_text, sections = repair_llm_output_if_needed(
        llm=llm,
        question=question,
        situation_summary=situation_summary,
        main_emotion=main_emotion,
        risk_level=risk_level,
        raw_text=raw_text,
    )

    return build_structured_result_from_sections(
        question=question,
        query_type=query_type,
        search_query=search_query,
        retrieved_docs=retrieved_docs,
        situation_summary=situation_summary,
        main_emotion=main_emotion,
        risk_level=risk_level,
        response_examples=response_examples,
        raw_text=repaired_text,
        sections=sections,
        method=method,
        recommended_replies=recommended_replies,
    )


# ============================================================
# 10. 단독 실행 테스트
# ============================================================
def main() -> None:
    test_question = "남자친구가 내 말을 제대로 안 들어주는 것 같아서 서운해. 어떻게 보내면 좋을까?"
    output = generate_recommended_reply(test_question, method="pinecone", k=3)

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

    print("\n===== 공감형 =====")
    print(output["empathy_reply"])

    print("\n===== 조언형 =====")
    print(output["advice_reply"])

    print("\n===== 갈등 완충형 =====")
    print(output["buffer_reply"])

    print("\n===== 최종 생성 결과 =====")
    print(output["result_text"])


if __name__ == "__main__":
    main()
