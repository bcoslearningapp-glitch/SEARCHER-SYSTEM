"""Embedding providers for semantic retrieval (PRD §61, ADR-025).

Embedding stays behind this interface, so the model can change without touching retrieval code. The only
concrete provider runs locally (ONNX, via fastembed), so no source or query text leaves the machine; the
PRD prefers a local option to minimise disclosure. A cloud provider would have to go through the disclosure
policy, and the library is shared across projects of different sensitivity, so none is offered.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

from research_api.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingUnavailableError(Exception):
    """The configured embedding provider cannot run (missing extra, model not downloadable)."""


class EmbeddingProvider(Protocol):
    name: str
    model: str
    # Whether text stays on this machine. Only local providers may embed a shared library.
    local: bool

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedProvider:
    """A local ONNX model through fastembed. Weights are fetched once into the cache directory."""

    name = "fastembed"
    local = True

    def __init__(self, model: str, cache_dir: Path) -> None:
        self.model = model
        try:
            from fastembed import TextEmbedding  # noqa: PLC0415 - optional extra, imported only when configured
        except ImportError as exc:
            raise EmbeddingUnavailableError(
                "fastembed is not installed; install the API with the `embeddings` extra"
            ) from exc
        try:
            self._model: Any = TextEmbedding(model_name=model, cache_dir=str(cache_dir))
        except Exception as exc:  # the library raises plain exceptions for unknown or unreachable models
            raise EmbeddingUnavailableError(f"embedding model {model!r} could not be loaded: {exc}") from exc

    @staticmethod
    def _lists(vectors: Iterable[Any]) -> list[list[float]]:
        return [[float(x) for x in v] for v in vectors]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._lists(self._model.passage_embed(texts))

    def embed_query(self, text: str) -> list[float]:
        return self._lists(self._model.query_embed(text))[0]


@lru_cache(maxsize=4)
def _fastembed(model: str, cache_dir: Path) -> FastEmbedProvider:
    return FastEmbedProvider(model, cache_dir)


def configured(settings: Settings) -> EmbeddingProvider | None:
    """The configured provider, or None when semantic retrieval is off.

    A provider that is configured but cannot load (missing extra, unreachable model) is logged and treated
    as off, so search falls back to lexical instead of failing.
    """
    if settings.embedding_provider != "fastembed":
        return None
    try:
        return _fastembed(settings.embedding_model, settings.embedding_cache_dir)
    except EmbeddingUnavailableError:
        logger.warning("semantic retrieval is configured but unavailable; using lexical search", exc_info=True)
        return None
