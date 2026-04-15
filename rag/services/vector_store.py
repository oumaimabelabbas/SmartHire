"""Persistent vector store backed by ChromaDB."""

import os
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import chromadb
except Exception as exc:  # pragma: no cover - import guard
    chromadb = None
    _CHROMA_IMPORT_ERROR = exc
else:
    _CHROMA_IMPORT_ERROR = None

from config import settings


@dataclass
class VectorMatch:
    text: str
    score: float
    metadata: Dict[str, Any]


class LocalVectorStore:
    """A tiny Chroma-based vector store with cosine similarity search."""

    def __init__(self, path: Optional[str] = None):
        self.path = os.path.normpath(path or settings.VECTOR_STORE_DIR)
        self._mode = "chroma"
        self._fallback_items: List[Dict[str, Any]] = []
        self._collection = None

        if chromadb is None:
            self._mode = "memory"
            return

        try:
            os.makedirs(self.path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.path)
            self._collection = self._client.get_or_create_collection(
                name="cv_chunks",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            self._mode = "memory"
            self._collection = None


    @staticmethod
    def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        safe: Dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                safe[str(key)] = value
            else:
                safe[str(key)] = str(value)
        return safe

    def upsert_chunks(
        self,
        doc_id: str,
        chunks: List[str],
        vectors: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        metadata = metadata or {}
        if not chunks or not vectors:
            return

        if self._mode == "memory":
            self._fallback_items = [item for item in self._fallback_items if item.get("doc_id") != doc_id]
            for index, chunk in enumerate(chunks):
                if index >= len(vectors):
                    break
                self._fallback_items.append(
                    {
                        "doc_id": doc_id,
                        "text": chunk,
                        "vector": vectors[index],
                        "metadata": self._sanitize_metadata({"doc_id": doc_id, "chunk_index": index, **metadata}),
                    }
                )
            return

        self._collection.delete(where={"doc_id": doc_id})

        ids: List[str] = []
        documents: List[str] = []
        embeddings: List[List[float]] = []
        metadatas: List[Dict[str, Any]] = []

        for index, chunk in enumerate(chunks):
            if index >= len(vectors):
                break
            ids.append(f"{doc_id}::{index}")
            documents.append(chunk)
            embeddings.append(vectors[index])
            row_metadata = self._sanitize_metadata({"doc_id": doc_id, "chunk_index": index, **metadata})
            metadatas.append(row_metadata)

        if ids:
            self._collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
    ) -> List[VectorMatch]:
        if self._mode == "memory":
            candidates = self._fallback_items
            if doc_id:
                candidates = [item for item in candidates if item.get("doc_id") == doc_id]
            if not candidates:
                return []

            query_norm = math.sqrt(sum(float(v) * float(v) for v in query_vector))
            if query_norm == 0:
                return []

            matches: List[VectorMatch] = []
            for item in candidates:
                vector = item.get("vector") or []
                dot = 0.0
                vec_norm_sq = 0.0
                for i, qv in enumerate(query_vector):
                    vv = float(vector[i]) if i < len(vector) else 0.0
                    qf = float(qv)
                    dot += qf * vv
                    vec_norm_sq += vv * vv
                denom = query_norm * math.sqrt(vec_norm_sq)
                score = dot / denom if denom else 0.0
                matches.append(
                    VectorMatch(
                        text=str(item.get("text", "")),
                        score=max(0.0, min(1.0, score)),
                        metadata=item.get("metadata", {}),
                    )
                )

            matches.sort(key=lambda match: match.score, reverse=True)
            return matches[:top_k]

        where_filter: Optional[Dict[str, Any]] = {"doc_id": doc_id} if doc_id else None
        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": top_k,
            "include": ["documents", "distances", "metadatas"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        result = self._collection.query(**query_kwargs)

        documents = (result.get("documents") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        if not documents:
            return []

        matches: List[VectorMatch] = []
        for index, text in enumerate(documents):
            distance = float(distances[index]) if index < len(distances) else 1.0
            score = max(0.0, min(1.0, 1.0 - distance))
            metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
            matches.append(
                VectorMatch(
                    text=str(text or ""),
                    score=score,
                    metadata=metadata,
                )
            )

        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:top_k]

