"""Pluggable search backends for case-scoped chunk retrieval."""

from __future__ import annotations

import re
import uuid
from typing import Protocol, runtime_checkable

from app.models.search_chunk import SearchChunk
from app.services.indexing.search_types import SearchHit

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@runtime_checkable
class SearchBackend(Protocol):
    """Interface for local mock and Azure AI Search backends."""

    def upsert_chunks(self, chunks: list[SearchChunk]) -> None:
        """Upload or store chunks for retrieval."""
        ...

    def search(
        self,
        case_id: uuid.UUID,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[SearchHit]:
        """Return top matching chunks scoped to a single case."""
        ...


class InMemorySearchBackend:
    """Keyword overlap search for local development and CI."""

    def __init__(self) -> None:
        self._chunks: dict[uuid.UUID, SearchChunk] = {}

    def upsert_chunks(self, chunks: list[SearchChunk]) -> None:
        for chunk in chunks:
            self._chunks[chunk.id] = chunk

    def search(
        self,
        case_id: uuid.UUID,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[SearchHit]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[SearchHit] = []
        for chunk in self._chunks.values():
            if chunk.case_id != case_id:
                continue
            chunk_tokens = _tokenize(chunk.chunk_text)
            overlap = query_tokens & chunk_tokens
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            scored.append(
                SearchHit(
                    chunk_id=chunk.id,
                    case_id=chunk.case_id,
                    artifact_id=chunk.artifact_id,
                    event_id=chunk.event_id,
                    chunk_text=chunk.chunk_text,
                    source_group=chunk.source_group,
                    provenance_pointer=chunk.provenance_pointer,
                    score=min(1.0, score),
                )
            )

        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:top_k]

    def clear(self) -> None:
        """Remove all stored chunks (tests only)."""
        self._chunks.clear()


class AzureSearchBackend:
    """Azure AI Search backend when deployed credentials are configured."""

    def __init__(
        self,
        *,
        endpoint: str,
        index_name: str,
        api_key: str,
    ) -> None:
        self._endpoint = endpoint
        self._index_name = index_name
        self._api_key = api_key

    def upsert_chunks(self, chunks: list[SearchChunk]) -> None:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient

        client = SearchClient(
            endpoint=self._endpoint,
            index_name=self._index_name,
            credential=AzureKeyCredential(self._api_key),
        )
        documents = [_chunk_to_document(chunk) for chunk in chunks]
        if documents:
            client.upload_documents(documents=documents)

    def search(
        self,
        case_id: uuid.UUID,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[SearchHit]:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient

        client = SearchClient(
            endpoint=self._endpoint,
            index_name=self._index_name,
            credential=AzureKeyCredential(self._api_key),
        )
        filter_expr = f"case_id eq '{case_id}'"
        results = client.search(
            search_text=query,
            filter=filter_expr,
            top=top_k,
        )
        hits: list[SearchHit] = []
        for result in results:
            hits.append(
                SearchHit(
                    chunk_id=uuid.UUID(str(result["id"])),
                    case_id=uuid.UUID(str(result["case_id"])),
                    artifact_id=uuid.UUID(str(result["artifact_id"])),
                    event_id=(
                        uuid.UUID(str(result["event_id"]))
                        if result.get("event_id")
                        else None
                    ),
                    chunk_text=str(result["chunk_text"]),
                    source_group=str(result.get("source_group", "unknown")),
                    provenance_pointer=result.get("provenance_pointer"),
                    score=float(result.get("@search.score", 0.0)),
                )
            )
        return hits


def _chunk_to_document(chunk: SearchChunk) -> dict[str, object]:
    return {
        "id": str(chunk.id),
        "case_id": str(chunk.case_id),
        "artifact_id": str(chunk.artifact_id),
        "event_id": str(chunk.event_id) if chunk.event_id else None,
        "chunk_text": chunk.chunk_text,
        "source_group": chunk.source_group,
        "provenance_pointer": chunk.provenance_pointer,
        "filter_metadata": chunk.filter_metadata or {},
    }


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(text.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "with"}
    }


def get_search_backend(settings: object | None = None) -> SearchBackend:
    """Build the active search backend from settings."""
    from app.core.config import Settings, get_settings

    active: Settings = settings if isinstance(settings, Settings) else get_settings()

    if (
        active.azure_search_endpoint
        and active.azure_search_index
        and active.azure_search_api_key
    ):
        return AzureSearchBackend(
            endpoint=active.azure_search_endpoint,
            index_name=active.azure_search_index,
            api_key=active.azure_search_api_key,
        )
    return InMemorySearchBackend()
