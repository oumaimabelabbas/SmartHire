"""Text chunking utility for RAG retrieval."""

from typing import List


class TextChunker:
    """Split text into overlapping word chunks."""

    @staticmethod
    def chunk_text(text: str, chunk_size_words: int = 120, overlap_words: int = 30) -> List[str]:
        if not text or not text.strip():
            return []

        words = text.split()
        if len(words) <= chunk_size_words:
            return [" ".join(words)]

        if overlap_words >= chunk_size_words:
            overlap_words = max(0, chunk_size_words // 4)

        step = max(1, chunk_size_words - overlap_words)
        chunks: List[str] = []

        for start in range(0, len(words), step):
            end = start + chunk_size_words
            chunk_words = words[start:end]
            if not chunk_words:
                break
            chunks.append(" ".join(chunk_words))
            if end >= len(words):
                break

        return chunks

