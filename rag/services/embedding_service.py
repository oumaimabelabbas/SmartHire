"""Embedding service for RAG retrieval."""

import hashlib
import json
import logging
import os
from typing import List

from sklearn.feature_extraction.text import HashingVectorizer

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingRateLimitError(Exception):
    """Exception conservée pour compatibilité interne."""


class EmbeddingService:
    """Create deterministic local embeddings for RAG retrieval."""

    _hashing_vectorizer = HashingVectorizer(
        n_features=512,
        alternate_sign=False,
        norm="l2",
    )
    _cache_loaded = False
    _cache_data = {}

    @staticmethod
    def embed_texts(texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        normalized = [text or "" for text in texts]
        cache = EmbeddingService._load_cache()
        vectors: List[List[float] | None] = [None] * len(normalized)
        missing_map = []

        for index, text in enumerate(normalized):
            key = EmbeddingService._cache_key(text)
            cached_vector = cache.get(key)
            if cached_vector is not None:
                vectors[index] = cached_vector
            else:
                missing_map.append((index, text, key))

        if missing_map:
            missing_vectors = EmbeddingService._embed_with_hashing([item[1] for item in missing_map])
            for vector_index, (_, _, key) in enumerate(missing_map):
                vector = missing_vectors[vector_index]
                vectors[missing_map[vector_index][0]] = vector
                cache[key] = vector
            EmbeddingService._save_cache()

        return [vector for vector in vectors if vector is not None]

    @staticmethod
    def _embed_with_hashing(texts: List[str]) -> List[List[float]]:
        matrix = EmbeddingService._hashing_vectorizer.transform(texts)
        return matrix.toarray().tolist()

    @staticmethod
    def _cache_key(text: str) -> str:
        raw = f"hashing:{text}".encode("utf-8")
        return hashlib.sha1(raw).hexdigest()

    @staticmethod
    def _load_cache() -> dict:
        if EmbeddingService._cache_loaded:
            return EmbeddingService._cache_data

        path = settings.EMBEDDING_CACHE_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as file:
                    EmbeddingService._cache_data = json.load(file)
            except Exception:
                EmbeddingService._cache_data = {}
        else:
            EmbeddingService._cache_data = {}

        EmbeddingService._cache_loaded = True
        return EmbeddingService._cache_data

    @staticmethod
    def _save_cache() -> None:
        if not EmbeddingService._cache_loaded:
            return
        with open(settings.EMBEDDING_CACHE_PATH, "w", encoding="utf-8") as file:
            json.dump(EmbeddingService._cache_data, file, ensure_ascii=True)


