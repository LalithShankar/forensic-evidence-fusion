"""Pluggable LLM backends for grounded assistant answers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.services.indexing.search_types import SearchHit


@runtime_checkable
class LLMBackend(Protocol):
    """Interface for mock and Azure OpenAI chat backends."""

    @property
    def model_name(self) -> str:
        """Return the model identifier for audit logs."""
        ...

    def complete(self, *, system: str, user: str, context: str) -> str:
        """Generate an answer from separated instruction and evidence context."""
        ...


class MockLLMBackend:
    """Deterministic template answers for local development and CI."""

    @property
    def model_name(self) -> str:
        return "mock-local"

    def complete(self, *, system: str, user: str, context: str) -> str:
        return (
            "Based on the indexed evidence below, here is a grounded summary.\n\n"
            f"Question: {user.strip()}\n\n"
            f"Evidence:\n{context.strip()}\n\n"
            "This response is generated from retrieved case evidence only."
        )


class AzureOpenAIBackend:
    """Azure OpenAI chat completion backend."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str,
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._deployment = deployment
        self._api_version = api_version

    @property
    def model_name(self) -> str:
        return self._deployment

    def complete(self, *, system: str, user: str, context: str) -> str:
        from openai import AzureOpenAI

        client = AzureOpenAI(
            azure_endpoint=self._endpoint,
            api_key=self._api_key,
            api_version=self._api_version,
        )
        response = client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": (
                        "Use ONLY the evidence context below.\n\n"
                        f"Question: {user}\n\nEvidence:\n{context}"
                    ),
                },
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


def format_hits_context(hits: list[SearchHit]) -> str:
    """Format retrieved hits for prompt context and citation verification."""
    lines: list[str] = []
    for hit in hits:
        lines.append(
            f"[chunk_id={hit.chunk_id} artifact_id={hit.artifact_id}"
            f"{f' event_id={hit.event_id}' if hit.event_id else ''}] "
            f"{hit.chunk_text}"
        )
    return "\n".join(lines)


def get_llm_backend(settings: object | None = None) -> LLMBackend:
    """Build the active LLM backend from settings."""
    from app.core.config import Settings, get_settings

    active: Settings = settings if isinstance(settings, Settings) else get_settings()

    if active.azure_openai_configured:
        return AzureOpenAIBackend(
            endpoint=active.azure_openai_endpoint or "",
            api_key=active.azure_openai_api_key or "",
            deployment=active.azure_openai_chat_deployment or "",
            api_version=active.azure_openai_api_version,
        )
    return MockLLMBackend()
