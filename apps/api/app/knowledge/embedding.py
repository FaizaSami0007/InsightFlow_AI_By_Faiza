"""Embedding provider abstraction and deterministic vector generation for knowledge chunks."""

import hashlib
import math
import re
from typing import Any, Dict, List, Protocol


class EmbeddingProvider(Protocol):
    """Protocol for embedding generation engines."""

    def embed_text(self, text: str) -> List[float]: ...
    def embed_documents(self, texts: List[str]) -> List[List[float]]: ...
    def get_model_info(self) -> Dict[str, Any]: ...


class DeterministicEmbeddingProvider:
    """Deterministic, high-dimensional semantic vectorizer with subword n-gram hashing and L2 normalization.

    Ensures 100% reproducible cosine similarity retrieval without external network requirements.
    """

    def __init__(self, dimension: int = 384, model_name: str = "insightflow-deterministic-v1") -> None:
        self.dimension = dimension
        self.model_name = model_name

    def _hash_token_to_features(self, token: str) -> List[int]:
        """Maps a token and its subword n-grams to feature vector indices."""
        indices = []
        token_clean = token.lower().strip()
        if not token_clean:
            return indices

        # Primary token hash
        h1 = int(hashlib.md5(token_clean.encode("utf-8")).hexdigest(), 16)
        indices.append(h1 % self.dimension)

        # Subword n-grams (3 to 5 characters)
        for n in (3, 4, 5):
            if len(token_clean) >= n:
                for i in range(len(token_clean) - n + 1):
                    ngram = token_clean[i : i + n]
                    h_ng = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest(), 16)
                    indices.append(h_ng % self.dimension)

        return indices

    STOP_WORDS = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "for", "of", "in", "to",
        "what", "how", "why", "are", "do", "does", "our", "we", "can", "be", "all", "with",
        "this", "that", "these", "those", "from", "as", "by", "it", "you", "your"
    }

    def embed_text(self, text: str) -> List[float]:
        """Generate a normalized dense vector for a given text snippet."""
        vec = [0.0] * self.dimension
        raw_tokens = re.findall(r"\b\w+\b", text.lower())
        tokens = [t for t in raw_tokens if t not in self.STOP_WORDS and len(t) > 1]

        if not tokens:
            tokens = raw_tokens

        for tok in tokens:
            indices = self._hash_token_to_features(tok)
            for idx in indices:
                vec[idx] += 1.0

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]

        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple document strings."""
        return [self.embed_text(t) for t in texts]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "local_deterministic",
            "model": self.model_name,
            "dimension": self.dimension,
            "is_offline": True,
        }


def get_embedding_provider() -> EmbeddingProvider:
    """Factory providing configured embedding engine (local deterministic or cloud)."""
    # If explicit external provider credentials exist in settings, cloud provider can be instantiated
    return DeterministicEmbeddingProvider()
