import hashlib
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingProvider(ABC):
    """Abstract base class for vector embedding generation."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass


class LocalDeterministicEmbeddingProvider(EmbeddingProvider):
    """
    High-reliability, deterministic local embedding provider.
    Computes a 384-dimensional normalized vector using keyword-frequency distribution
    and SHA-256 semantic token hashing.
    Ensures zero external network dependencies for 100% offline hackathon uptime.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dim
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = text.lower().split()
        for i, token in enumerate(tokens):
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            weight = 1.0 / (1.0 + (i * 0.005))
            vec[idx] += weight
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class OpenRouterEmbeddingProvider(EmbeddingProvider):
    """
    OpenRouter-compatible dense embedding provider with automatic fallback to local provider.
    """
    def __init__(self):
        self.fallback = LocalDeterministicEmbeddingProvider()
        self.api_key = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception as e:
                logger.warning(f"Could not initialize OpenRouter embedding client: {e}")
                self.client = None

    def embed_text(self, text: str) -> List[float]:
        if self.client and self.api_key:
            try:
                resp = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return resp.data[0].embedding
            except Exception as err:
                logger.warning(f"OpenRouter embedding call failed: {err}. Using local deterministic fallback.")
        return self.fallback.embed_text(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.client and self.api_key:
            try:
                resp = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts
                )
                return [d.embedding for d in resp.data]
            except Exception as err:
                logger.warning(f"OpenRouter batch embedding failed: {err}. Using local fallback.")
        return self.fallback.embed_documents(texts)


# Global singleton
_embedding_provider_instance: Optional[EmbeddingProvider] = None

def get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider_instance
    if _embedding_provider_instance is None:
        if settings.EMBEDDING_PROVIDER.lower() == "openrouter" and (settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY):
            _embedding_provider_instance = OpenRouterEmbeddingProvider()
        else:
            _embedding_provider_instance = LocalDeterministicEmbeddingProvider()
    return _embedding_provider_instance
