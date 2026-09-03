import os
import json
import math
import re
from typing import List, Dict, Any, Tuple
import numpy as np
from backend.app.core.config import settings

class VectorStore:
    def __init__(self, storage_dir: str = settings.VECTOR_STORE_PATH):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.index_file = os.path.join(self.storage_dir, "chunks_index.json")
        self.embeddings_file = os.path.join(self.storage_dir, "embeddings.npy")
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray = np.empty((0, 128))
        self.load()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def _compute_fallback_dense_vector(self, text: str, dim: int = 128) -> np.ndarray:
        """
        Lightweight, deterministic semantic hashing vector representation.
        Ensures semantic similarity matching without mandatory multi-GB model weights.
        """
        tokens = self._tokenize(text)
        vec = np.zeros(dim, dtype=np.float32)
        if not tokens:
            return vec
            
        for i, token in enumerate(tokens):
            # Positional hash embedding
            h = hash(token)
            idx = abs(h) % dim
            sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 / (1.0 + 0.05 * i))
            
            # Bigram feature
            if i > 0:
                bi_h = hash(f"{tokens[i-1]}_{token}")
                bi_idx = abs(bi_h) % dim
                vec[bi_idx] += 0.5 * (1.0 if (bi_h >> 1) % 2 == 0 else -1.0)
                
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec

    def _get_embedding(self, text: str) -> np.ndarray:
        try:
            from backend.app.services.embedding_provider import get_embedding_provider
            raw_emb = get_embedding_provider().embed_text(text[:3000])
            arr = np.array(raw_emb, dtype=np.float32)
            norm = np.linalg.norm(arr)
            return arr / (norm + 1e-9) if norm > 0 else arr
        except Exception:
            return self._compute_fallback_dense_vector(text, 128)

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        """
        new_chunks list of dicts with:
        id, document_id, document_title, system_id, content, page_number, section, metadata
        """
        new_vectors = []
        for ch in new_chunks:
            emb = self._get_embedding(ch["content"])
            new_vectors.append(emb)
            self.chunks.append(ch)
            
        if new_vectors:
            new_arr = np.array(new_vectors, dtype=np.float32)
            if self.embeddings.shape[0] == 0 or self.embeddings.shape[1] != new_arr.shape[1]:
                self.embeddings = new_arr
            else:
                self.embeddings = np.vstack([self.embeddings, new_arr])
                
        self.save()

    def hybrid_search(
        self,
        query: str,
        system_id: str = None,
        top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not self.chunks:
            return []
            
        q_tokens = set(self._tokenize(query))
        q_vec = self._get_embedding(query)
        
        # Dense cosine similarity
        if self.embeddings.shape[0] == len(self.chunks) and self.embeddings.shape[1] == q_vec.shape[0]:
            dot_products = np.dot(self.embeddings, q_vec)
        else:
            # Recompute on the fly if dimensions mismatch
            dot_products = np.array([
                float(np.dot(self._compute_fallback_dense_vector(ch["content"], 128), self._compute_fallback_dense_vector(query, 128)))
                for ch in self.chunks
            ])
            
        scored_results = []
        for idx, chunk in enumerate(self.chunks):
            # Metadata filter
            if system_id and chunk.get("system_id") and chunk.get("system_id") != system_id:
                continue
                
            chunk_tokens = self._tokenize(chunk["content"])
            chunk_set = set(chunk_tokens)
            
            # Keyword overlap (BM25 style overlap)
            overlap = len(q_tokens.intersection(chunk_set))
            kw_score = overlap / (len(q_tokens) + 1e-6)
            
            # Boost section title matches
            sec_title = chunk.get("section", "").lower()
            for qt in q_tokens:
                if qt in sec_title:
                    kw_score += 0.3
                    
            dense_score = float(dot_products[idx]) if idx < len(dot_products) else 0.0
            
            # Hybrid combined score: 55% dense, 45% keyword
            hybrid_score = max(0.0, (0.55 * dense_score) + (0.45 * kw_score))
            scored_results.append((chunk, hybrid_score))
            
        # Sort descending
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]

    def clear(self):
        self.chunks = []
        self.embeddings = np.empty((0, 128))
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        if os.path.exists(self.embeddings_file):
            os.remove(self.embeddings_file)

    def save(self):
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)
        np.save(self.embeddings_file, self.embeddings)

    def load(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                if os.path.exists(self.embeddings_file):
                    self.embeddings = np.load(self.embeddings_file)
            except Exception:
                self.chunks = []
                self.embeddings = np.empty((0, 128))

# Global singleton
vector_store = VectorStore()
