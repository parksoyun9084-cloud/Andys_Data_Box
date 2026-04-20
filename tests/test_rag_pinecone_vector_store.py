# -*- coding: utf-8 -*-

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.rag import pinecone_vector_store as pvs


class FakeStatus:
    ready = True


class FakeDescription:
    status = FakeStatus()


class FakeServerlessSpec:
    def __init__(self, cloud: str, region: str) -> None:
        self.cloud = cloud
        self.region = region


class FakeIndex:
    def __init__(self, name: str, delete_error: Exception | None = None) -> None:
        self.name = name
        self.delete_error = delete_error
        self.deleted_all = False

    def delete(self, delete_all: bool = False) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted_all = delete_all


class FakePineconeClient:
    def __init__(self, existing_indexes: set[str] | None = None) -> None:
        self.indexes = existing_indexes or set()
        self.created_indexes = []
        self.index_handles = {}

    def has_index(self, index_name: str) -> bool:
        return index_name in self.indexes

    def create_index(self, **kwargs) -> None:
        self.created_indexes.append(kwargs)
        self.indexes.add(kwargs["name"])

    def describe_index(self, index_name: str) -> FakeDescription:
        return FakeDescription()

    def Index(self, index_name: str) -> FakeIndex:
        if index_name not in self.index_handles:
            self.index_handles[index_name] = FakeIndex(index_name)
        return self.index_handles[index_name]


class FakeVectorStore:
    def __init__(self, index, embedding) -> None:
        self.index = index
        self.embedding = embedding


class PineconeVectorStoreHelperTest(unittest.TestCase):
    def test_get_pinecone_api_key_uses_shared_loader(self) -> None:
        with patch.object(pvs, "load_api_key", return_value="pinecone-key") as loader:
            self.assertEqual(pvs.get_pinecone_api_key(), "pinecone-key")

        loader.assert_called_once_with("PINECONE_API_KEY")

    def test_ensure_pinecone_index_creates_missing_index(self) -> None:
        client = FakePineconeClient()

        index = pvs.ensure_pinecone_index(
            pvs.RAG_INDEX_NAME,
            client=client,
            serverless_spec_cls=FakeServerlessSpec,
        )

        self.assertEqual(index.name, pvs.RAG_INDEX_NAME)
        self.assertEqual(len(client.created_indexes), 1)
        created = client.created_indexes[0]
        self.assertEqual(created["name"], pvs.RAG_INDEX_NAME)
        self.assertEqual(created["dimension"], pvs.PINECONE_DIMENSION)
        self.assertEqual(created["metric"], pvs.PINECONE_METRIC)
        self.assertEqual(created["deletion_protection"], "disabled")
        self.assertEqual(created["spec"].cloud, pvs.PINECONE_CLOUD)
        self.assertEqual(created["spec"].region, pvs.PINECONE_REGION)

    def test_ensure_pinecone_index_does_not_recreate_existing_index(self) -> None:
        client = FakePineconeClient(existing_indexes={pvs.EXAMPLE_INDEX_NAME})

        index = pvs.ensure_pinecone_index(
            pvs.EXAMPLE_INDEX_NAME,
            client=client,
            serverless_spec_cls=FakeServerlessSpec,
        )

        self.assertEqual(index.name, pvs.EXAMPLE_INDEX_NAME)
        self.assertEqual(client.created_indexes, [])

    def test_get_pinecone_vector_store_uses_expected_index(self) -> None:
        client = FakePineconeClient(existing_indexes={pvs.RAG_INDEX_NAME})
        embedding = object()

        vector_store = pvs.get_pinecone_vector_store(
            index_name=pvs.RAG_INDEX_NAME,
            embedding=embedding,
            client=client,
            vector_store_cls=FakeVectorStore,
        )

        self.assertIs(vector_store.embedding, embedding)
        self.assertEqual(vector_store.index.name, pvs.RAG_INDEX_NAME)

    def test_clear_pinecone_index_deletes_all_vectors(self) -> None:
        client = FakePineconeClient(existing_indexes={pvs.RAG_INDEX_NAME})

        pvs.clear_pinecone_index(pvs.RAG_INDEX_NAME, client=client)

        self.assertTrue(client.Index(pvs.RAG_INDEX_NAME).deleted_all)

    def test_clear_pinecone_index_ignores_missing_namespace(self) -> None:
        error = Exception("Namespace not found")
        error.status = 404
        client = FakePineconeClient(existing_indexes={pvs.RAG_INDEX_NAME})
        client.index_handles[pvs.RAG_INDEX_NAME] = FakeIndex(
            pvs.RAG_INDEX_NAME,
            delete_error=error,
        )

        pvs.clear_pinecone_index(pvs.RAG_INDEX_NAME, client=client)


if __name__ == "__main__":
    unittest.main()
