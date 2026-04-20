# ============================================================
# - rag_documents_with_text.csv를 불러옴
# - response_pairs_with_text.csv를 불러옴
# - rag_text를 임베딩하여 검색용 Pinecone 벡터DB 생성
# - response_example_text를 임베딩하여 응답예시용 Pinecone 벡터DB 생성
# - metadata를 함께 저장함
# ============================================================

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import pandas as pd
from langchain_openai import OpenAIEmbeddings

try:
    from .api_key_loader import load_api_key
    from .pinecone_vector_store import (
        EXAMPLE_INDEX_NAME,
        RAG_INDEX_NAME,
        clear_pinecone_index,
        get_pinecone_client,
        get_pinecone_vector_store,
    )
except ImportError:
    from api_key_loader import load_api_key
    from pinecone_vector_store import (
        EXAMPLE_INDEX_NAME,
        RAG_INDEX_NAME,
        clear_pinecone_index,
        get_pinecone_client,
        get_pinecone_vector_store,
    )


# ============================================================
# 1. 경로 설정
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAG_TEXT_PATH = PROCESSED_DATA_DIR / "rag_documents_with_text.csv"
RESPONSE_TEXT_PATH = PROCESSED_DATA_DIR / "response_pairs_with_text.csv"

MAX_TEXT_LENGTH = 4000


# ============================================================
# 2. 문자열 처리 함수
# ============================================================
def clean_text(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()


def truncate_text(text, max_len: int = MAX_TEXT_LENGTH) -> str:
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    return text[:max_len]


def build_stable_ids(prefix: str, count: int) -> list[str]:
    return [f"{prefix}-{idx:06d}" for idx in range(count)]


# ============================================================
# 3. CSV 로드
# ============================================================
def load_source_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not RAG_TEXT_PATH.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없음: {RAG_TEXT_PATH}")

    if not RESPONSE_TEXT_PATH.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없음: {RESPONSE_TEXT_PATH}")

    rag_df = pd.read_csv(RAG_TEXT_PATH)
    response_df = pd.read_csv(RESPONSE_TEXT_PATH)

    print("===== RAG CSV 로드 완료 =====")
    print(rag_df.shape)
    print(rag_df.columns.tolist())

    print("\n===== RESPONSE CSV 로드 완료 =====")
    print(response_df.shape)
    print(response_df.columns.tolist())

    if "rag_text" not in rag_df.columns:
        raise ValueError("rag_text 컬럼이 없음.")

    rag_df["rag_text"] = rag_df["rag_text"].astype(str).str.strip()
    rag_df = rag_df[rag_df["rag_text"] != ""].copy()

    print("\n===== 유효 RAG 문서 수 =====")
    print(len(rag_df))

    if "response_example_text" not in response_df.columns:
        raise ValueError("response_example_text 컬럼이 없음.")

    response_df["response_example_text"] = (
        response_df["response_example_text"].astype(str).str.strip()
    )
    response_df = response_df[response_df["response_example_text"] != ""].copy()

    print("\n===== 유효 RESPONSE 예시 수 =====")
    print(len(response_df))

    return rag_df, response_df


# ============================================================
# 4. rag texts / metadatas 준비
# ============================================================
def build_rag_texts_and_metadatas(rag_df: pd.DataFrame):
    texts = []
    metadatas = []

    for _, row in rag_df.iterrows():
        text = truncate_text(row["rag_text"], MAX_TEXT_LENGTH)
        texts.append(text)

        metadatas.append({
            "dialogue_id": clean_text(row.get("dialogue_id", "")),
            "file_name": clean_text(row.get("file_name", "")),
            "relation": clean_text(row.get("relation", "")),
            "situation": clean_text(row.get("situation", "")),
            "speaker_emotion": clean_text(row.get("speaker_emotion", "")),
            "listener_behavior": clean_text(row.get("listener_behavior", "")),
            "listener_empathy_tags": clean_text(row.get("listener_empathy_tags", "")),
            "risk_level": clean_text(row.get("risk_level", "")),
            "conflict_keywords": clean_text(row.get("conflict_keywords", "")),
            "turn_count": clean_text(row.get("turn_count", "")),
            "terminated": clean_text(row.get("terminated", "")),
        })

    return texts, metadatas


# ============================================================
# 5. response example texts / metadatas 준비
# ============================================================
def build_example_texts_and_metadatas(response_df: pd.DataFrame):
    example_texts = []
    example_metadatas = []

    for _, row in response_df.iterrows():
        text = truncate_text(row["response_example_text"], MAX_TEXT_LENGTH)
        example_texts.append(text)

        example_metadatas.append({
            "dialogue_id": clean_text(row.get("dialogue_id", "")),
            "relation": clean_text(row.get("relation", "")),
            "situation": clean_text(row.get("situation", "")),
            "speaker_emotion": clean_text(row.get("speaker_emotion", "")),
            "listener_empathy": clean_text(row.get("listener_empathy", "")),
            "terminate": clean_text(row.get("terminate", "")),
            "listener_response": clean_text(row.get("listener_response", "")),
        })

    return example_texts, example_metadatas


def rebuild_vector_store(
    index_name: str,
    texts: list[str],
    metadatas: list[dict],
    ids: list[str],
    embeddings: OpenAIEmbeddings,
    pinecone_client: Any,
) -> float:
    print(f"\n===== Pinecone 벡터DB 생성 시작: {index_name} =====")
    start_time = time.time()

    vector_store = get_pinecone_vector_store(
        index_name=index_name,
        embedding=embeddings,
        client=pinecone_client,
    )
    clear_pinecone_index(index_name, client=pinecone_client)
    vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    elapsed = time.time() - start_time
    print(f"===== Pinecone 벡터DB 생성 완료: {index_name} =====")
    print(f"소요 시간: {round(elapsed, 2)}초")

    return elapsed


def main() -> None:
    openai_api_key = load_api_key("OPENAI_API_KEY")
    pinecone_api_key = load_api_key("PINECONE_API_KEY")
    pinecone_client = get_pinecone_client(pinecone_api_key=pinecone_api_key)

    rag_df, response_df = load_source_data()

    texts, metadatas = build_rag_texts_and_metadatas(rag_df)
    example_texts, example_metadatas = build_example_texts_and_metadatas(response_df)

    print("\n===== 첫 번째 RAG metadata 샘플 =====")
    print(metadatas[0])

    print("\n===== 첫 번째 RESPONSE metadata 샘플 =====")
    print(example_metadatas[0])

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=openai_api_key,
    )

    rebuild_vector_store(
        index_name=RAG_INDEX_NAME,
        texts=texts,
        metadatas=metadatas,
        ids=build_stable_ids("rag", len(texts)),
        embeddings=embeddings,
        pinecone_client=pinecone_client,
    )

    rebuild_vector_store(
        index_name=EXAMPLE_INDEX_NAME,
        texts=example_texts,
        metadatas=example_metadatas,
        ids=build_stable_ids("example", len(example_texts)),
        embeddings=embeddings,
        pinecone_client=pinecone_client,
    )

    print("\n===== Pinecone 저장 완료 =====")
    print(RAG_INDEX_NAME)
    print(EXAMPLE_INDEX_NAME)


if __name__ == "__main__":
    main()
