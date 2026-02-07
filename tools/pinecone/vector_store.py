"""Pinecone vector store — upsert, query, delete, stats.

Embedding-agnostic: pass in an ``embed_fn`` callable that turns text into
a vector, or supply pre-computed vectors directly.  This keeps the module
decoupled from any specific embedding provider (OpenAI, Cohere, local, etc.).

Usage
-----
    from tools.pinecone.config       import PineconeConfig
    from tools.pinecone.vector_store import VectorStore

    cfg   = PineconeConfig.from_env()
    store = VectorStore(cfg)

    # -- upsert pre-computed vectors --
    store.upsert_vectors([
        {"id": "doc-1", "values": [0.1, 0.2, ...], "metadata": {"text": "hello"}},
    ])

    # -- upsert text (requires an embed function) --
    store.upsert_texts(
        texts=[{"id": "doc-1", "text": "hello world"}],
        embed_fn=my_embed_function,      # str -> list[float]
    )

    # -- query with a pre-computed vector --
    results = store.query(vector=[0.1, 0.2, ...], top_k=5)

    # -- query with text --
    results = store.query_text("search terms", embed_fn=my_embed, top_k=5)
"""

from __future__ import annotations

import logging
from typing import Callable

from tools.pinecone.config import PineconeConfig
from tools.pinecone.client import get_index

logger = logging.getLogger(__name__)

# Type alias: a function that turns a string into a float vector.
EmbedFn = Callable[[str], list[float]]


class VectorStore:
    """Wraps a Pinecone index for vector upsert, query, and management."""

    def __init__(
        self,
        config: PineconeConfig,
        embed_fn: EmbedFn | None = None,
    ) -> None:
        """
        Args:
            config:   Pinecone connection settings.
            embed_fn: Optional default embedding function (str -> list[float]).
                      Can also be passed per-call on upsert_texts / query_text.
        """
        self._config = config
        self._index = get_index(config)
        self._namespace = config.namespace
        self._embed_fn = embed_fn

    # ── helpers ────────────────────────────────────────────────────────────

    def _resolve_embed_fn(self, embed_fn: EmbedFn | None) -> EmbedFn:
        fn = embed_fn or self._embed_fn
        if fn is None:
            raise ValueError(
                "No embed_fn provided. Pass one to the VectorStore constructor "
                "or directly to this method."
            )
        return fn

    # ── upsert ─────────────────────────────────────────────────────────────

    def upsert_vectors(
        self,
        vectors: list[dict],
        namespace: str | None = None,
    ) -> None:
        """Upsert pre-computed vectors into Pinecone.

        Each dict in *vectors* must have keys ``id`` and ``values``,
        and optionally ``metadata``.

        Args:
            vectors:   List of {"id": str, "values": list[float], "metadata": dict}.
            namespace: Override the default namespace.
        """
        ns = namespace or self._namespace
        batch_size = 100
        total = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self._index.upsert(vectors=batch, namespace=ns)
            total += len(batch)
            logger.info("Upserted batch %d–%d", i + 1, i + len(batch))

        logger.info("Upserted %d vectors into namespace '%s'.", total, ns)

    def upsert_texts(
        self,
        texts: list[dict],
        embed_fn: EmbedFn | None = None,
        namespace: str | None = None,
    ) -> None:
        """Embed text items and upsert them into Pinecone.

        Each dict in *texts* must have keys ``id`` and ``text``.
        Any extra keys are stored as metadata alongside ``text``.

        Args:
            texts:    List of {"id": str, "text": str, ...extra metadata}.
            embed_fn: Embedding function (str -> list[float]).
            namespace: Override the default namespace.
        """
        fn = self._resolve_embed_fn(embed_fn)
        vectors = []

        for item in texts:
            doc_id = item["id"]
            text = item["text"]
            metadata = {k: v for k, v in item.items() if k != "id"}
            embedding = fn(text)
            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": metadata,
            })

        self.upsert_vectors(vectors, namespace=namespace)

    # ── query ──────────────────────────────────────────────────────────────

    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        namespace: str | None = None,
        include_metadata: bool = True,
        filter: dict | None = None,
        include_values: bool = False,
    ) -> list[dict]:
        """Query the index with a pre-computed vector.

        Parameters
        ----------
        vector : list[float]
            Query vector.
        top_k : int
            Number of results to return.
        namespace : str | None
            Override the default namespace.
        include_metadata : bool
            Include metadata in results.
        filter : dict | None
            Pinecone metadata filter. Uses Pinecone's filter syntax::

                {"type": {"$eq": "support"}}
                {"$and": [{"type": {"$eq": "faq"}}, {"lang": {"$eq": "en"}}]}

        include_values : bool
            Include embedding vectors in results.

        Returns
        -------
        list[dict]
            List of ``{"id", "score", "metadata"}`` dicts (plus ``"values"``
            if *include_values* is True).
        """
        ns = namespace or self._namespace
        kwargs = {
            "vector": vector,
            "top_k": top_k,
            "include_metadata": include_metadata,
            "include_values": include_values,
            "namespace": ns,
        }
        if filter:
            kwargs["filter"] = filter

        results = self._index.query(**kwargs)
        output = []
        for m in results.get("matches", []):
            entry = {
                "id": m["id"],
                "score": m["score"],
                "metadata": m.get("metadata", {}),
            }
            if include_values:
                entry["values"] = m.get("values", [])
            output.append(entry)
        return output

    def query_text(
        self,
        text: str,
        embed_fn: EmbedFn | None = None,
        top_k: int = 5,
        namespace: str | None = None,
        filter: dict | None = None,
    ) -> list[dict]:
        """Embed *text* then query the index.

        Convenience wrapper around :meth:`query`.

        Parameters
        ----------
        text : str
            Text to embed and search.
        embed_fn : EmbedFn | None
            Override embedding function.
        top_k : int
            Number of results.
        namespace : str | None
            Namespace override.
        filter : dict | None
            Metadata filter.
        """
        fn = self._resolve_embed_fn(embed_fn)
        vector = fn(text)
        return self.query(vector, top_k=top_k, namespace=namespace, filter=filter)

    def query_batch(
        self,
        texts: list[str],
        embed_fn: EmbedFn | None = None,
        top_k: int = 5,
        namespace: str | None = None,
        filter: dict | None = None,
    ) -> list[list[dict]]:
        """Query the index with multiple texts in sequence.

        Parameters
        ----------
        texts : list[str]
            List of query texts.
        embed_fn : EmbedFn | None
            Override embedding function.
        top_k : int
            Results per query.
        namespace : str | None
            Namespace override.
        filter : dict | None
            Metadata filter applied to every query.

        Returns
        -------
        list[list[dict]]
            One result list per input text.
        """
        fn = self._resolve_embed_fn(embed_fn)
        all_results = []
        for text in texts:
            vector = fn(text)
            matches = self.query(
                vector, top_k=top_k, namespace=namespace, filter=filter,
            )
            all_results.append(matches)
        return all_results

    def get_context(
        self,
        text: str,
        embed_fn: EmbedFn | None = None,
        top_k: int = 5,
        namespace: str | None = None,
        filter: dict | None = None,
        min_score: float = 0.0,
    ) -> str:
        """Return retrieved context formatted as a numbered string.

        Useful for injecting into an LLM prompt.

        Parameters
        ----------
        text : str
            Query text.
        embed_fn : EmbedFn | None
            Override embedding function.
        top_k : int
            Number of chunks to retrieve.
        namespace : str | None
            Namespace override.
        filter : dict | None
            Metadata filter.
        min_score : float
            Minimum similarity score to include (0.0 to 1.0).
        """
        docs = self.query_text(text, embed_fn=embed_fn, top_k=top_k,
                               namespace=namespace, filter=filter)
        if not docs:
            return ""
        chunks = []
        for i, doc in enumerate(docs, 1):
            if doc["score"] < min_score:
                continue
            doc_text = doc["metadata"].get("text", "")
            chunks.append(f"[{i}] {doc_text}")
        return "\n\n".join(chunks)

    # ── delete ─────────────────────────────────────────────────────────────

    def delete_vectors(
        self,
        ids: list[str],
        namespace: str | None = None,
    ) -> None:
        """Delete specific vectors by ID."""
        ns = namespace or self._namespace
        self._index.delete(ids=ids, namespace=ns)
        logger.info("Deleted %d vector(s) from namespace '%s'.", len(ids), ns)

    def delete_all(
        self,
        namespace: str | None = None,
        skip_confirm: bool = False,
    ) -> None:
        """Delete every vector in a namespace."""
        ns = namespace or self._namespace

        if not skip_confirm:
            answer = input(
                f"\nDelete ALL vectors in namespace '{ns}' of index "
                f"'{self._config.index_name}'? This is irreversible. [y/N] "
            )
            if answer.strip().lower() not in ("y", "yes"):
                logger.info("Aborted.")
                return

        self._index.delete(delete_all=True, namespace=ns)
        logger.info("Deleted all vectors in namespace '%s'.", ns)

    # ── metadata ───────────────────────────────────────────────────────────

    def update_metadata(
        self,
        vector_id: str,
        metadata: dict,
        namespace: str | None = None,
    ) -> None:
        """Update metadata on an existing vector without changing its values."""
        ns = namespace or self._namespace
        self._index.update(id=vector_id, set_metadata=metadata, namespace=ns)
        logger.info("Updated metadata for '%s' in namespace '%s'.", vector_id, ns)

    # ── fetch ──────────────────────────────────────────────────────────────

    def fetch(
        self,
        ids: list[str],
        namespace: str | None = None,
    ) -> list[dict]:
        """Fetch vectors by their IDs (not a similarity search).

        Parameters
        ----------
        ids : list[str]
            Vector IDs to fetch.
        namespace : str | None
            Namespace override.

        Returns
        -------
        list[dict]
            ``{"id", "values", "metadata"}`` for each found ID.
        """
        ns = namespace or self._namespace
        response = self._index.fetch(ids=ids, namespace=ns)
        vectors = response.get("vectors", {})
        results = []
        for vec_id, vec_data in vectors.items():
            results.append({
                "id": vec_id,
                "values": vec_data.get("values", []),
                "metadata": vec_data.get("metadata", {}),
            })
        logger.info("Fetched %d of %d vector(s).", len(results), len(ids))
        return results

    # ── stats ──────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return index statistics (total vectors, per-namespace counts, etc.)."""
        return self._index.describe_index_stats()
