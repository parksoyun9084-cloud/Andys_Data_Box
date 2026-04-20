# -*- coding: utf-8 -*-
"""Pinecone vector store helpers for RAG scripts.

This module keeps Pinecone setup in one place so build-time upserts and
runtime retrieval use the same index names, dimensions, and secret loading.
"""

from __future__ import annotations

import time
from typing import Any

try:
    from .api_key_loader import load_api_key
except ImportError:
    from api_key_loader import load_api_key


RAG_INDEX_NAME = "andys-rag-documents"
EXAMPLE_INDEX_NAME = "andys-rag-examples"

PINECONE_DIMENSION = 1536
PINECONE_METRIC = "cosine"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
PINECONE_WAIT_TIMEOUT_SECONDS = 60
PINECONE_WAIT_INTERVAL_SECONDS = 2


def get_pinecone_api_key() -> str:
    """Load the Pinecone API key through the shared secrets-first loader."""

    return load_api_key("PINECONE_API_KEY")


def _load_pinecone_client_class() -> Any:
    try:
        from pinecone import Pinecone
    except ImportError as exc:
        raise ImportError(
            "Pinecone 연동 패키지가 설치되지 않았습니다. "
            "`pip install -r requirements.txt` 실행 후 다시 시도하세요."
        ) from exc
    return Pinecone


def _load_serverless_spec_class() -> Any:
    try:
        from pinecone import ServerlessSpec
    except ImportError as exc:
        raise ImportError(
            "Pinecone ServerlessSpec을 불러올 수 없습니다. "
            "`pinecone` 패키지 설치 상태를 확인하세요."
        ) from exc
    return ServerlessSpec


def _load_vector_store_class() -> Any:
    try:
        from langchain_pinecone import PineconeVectorStore
    except ImportError as exc:
        raise ImportError(
            "LangChain Pinecone 연동 패키지가 설치되지 않았습니다. "
            "`pip install -r requirements.txt` 실행 후 다시 시도하세요."
        ) from exc
    return PineconeVectorStore


def get_pinecone_client(
    pinecone_api_key: str | None = None,
    client_cls: Any | None = None,
) -> Any:
    """Create a Pinecone client without exposing the API key."""

    api_key = pinecone_api_key or get_pinecone_api_key()
    pinecone_cls = client_cls or _load_pinecone_client_class()
    return pinecone_cls(api_key=api_key)


def _has_index(client: Any, index_name: str) -> bool:
    if hasattr(client, "has_index"):
        return bool(client.has_index(index_name))

    indexes = client.list_indexes()
    if hasattr(indexes, "names"):
        return index_name in indexes.names()

    for index in indexes:
        name = getattr(index, "name", None)
        if name is None and isinstance(index, dict):
            name = index.get("name")
        if name == index_name:
            return True

    return False


def _status_ready(status: Any) -> bool:
    if status is None:
        return True
    if isinstance(status, dict):
        return bool(status.get("ready", True))
    return bool(getattr(status, "ready", True))


def wait_for_pinecone_index(
    client: Any,
    index_name: str,
    timeout_seconds: int = PINECONE_WAIT_TIMEOUT_SECONDS,
    interval_seconds: int = PINECONE_WAIT_INTERVAL_SECONDS,
) -> None:
    """Wait until Pinecone reports the index ready when the SDK supports it."""

    if not hasattr(client, "describe_index"):
        return

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        description = client.describe_index(index_name)
        if _status_ready(getattr(description, "status", None)):
            return
        time.sleep(interval_seconds)

    raise TimeoutError(f"Pinecone 인덱스가 준비되지 않았습니다: {index_name}")


def ensure_pinecone_index(
    index_name: str,
    pinecone_api_key: str | None = None,
    client: Any | None = None,
    client_cls: Any | None = None,
    serverless_spec_cls: Any | None = None,
    wait_until_ready: bool = True,
) -> Any:
    """Create the Pinecone index if missing and return the index handle."""

    pinecone_client = client or get_pinecone_client(
        pinecone_api_key=pinecone_api_key,
        client_cls=client_cls,
    )

    if not _has_index(pinecone_client, index_name):
        spec_cls = serverless_spec_cls or _load_serverless_spec_class()
        pinecone_client.create_index(
            name=index_name,
            dimension=PINECONE_DIMENSION,
            metric=PINECONE_METRIC,
            spec=spec_cls(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
            deletion_protection="disabled",
        )

    if wait_until_ready:
        wait_for_pinecone_index(pinecone_client, index_name)

    return pinecone_client.Index(index_name)


def clear_pinecone_index(
    index_name: str,
    pinecone_api_key: str | None = None,
    client: Any | None = None,
) -> None:
    """Delete all vectors in an index before a full rebuild."""

    pinecone_client = client or get_pinecone_client(pinecone_api_key=pinecone_api_key)
    index = pinecone_client.Index(index_name)
    try:
        index.delete(delete_all=True)
    except Exception as exc:
        if getattr(exc, "status", None) == 404 and "Namespace not found" in str(exc):
            return
        raise


def get_pinecone_vector_store(
    index_name: str,
    embedding: Any,
    pinecone_api_key: str | None = None,
    client: Any | None = None,
    vector_store_cls: Any | None = None,
    wait_until_ready: bool = True,
) -> Any:
    """Return a LangChain Pinecone vector store for the configured index."""

    store_cls = vector_store_cls or _load_vector_store_class()
    pinecone_client = client or get_pinecone_client(pinecone_api_key=pinecone_api_key)
    index = ensure_pinecone_index(
        index_name=index_name,
        client=pinecone_client,
        wait_until_ready=wait_until_ready,
    )
    return store_cls(index=index, embedding=embedding)
