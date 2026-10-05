"""Hybrid Retrieval Engine: Dense Vector + BM25 Sparse Search + Reciprocal Rank Fusion (RRF).

Provides sub-millisecond in-memory retrieval with transparent score attribution.
Can be run standalone or imported into the FastAPI backend service.
"""

import math
import json
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from mlops.pipeline.build_gold_index import tokenize, STOPWORDS, extract_features, compute_feature_vector


class HybridRetriever:
    def __init__(self, index_path: Optional[Path] = None):
        if index_path is None:
            index_path = Path(__file__).resolve().parent.parent / "data" / "gold" / "gold_index.json"

        if not index_path.exists():
            raise FileNotFoundError(f"Gold index not found at: {index_path}. Run MLOps pipeline first.")

        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.version = data.get("version", "1.0.0")
        self.chunks_map: Dict[str, Dict[str, Any]] = {c["id"]: c for c in data["chunks"]}
        self.dense_embeddings: Dict[str, np.ndarray] = {
            cid: np.array(vec, dtype=np.float32) for cid, vec in data["dense_embeddings"].items()
        }
        self.feature_idf: Dict[str, float] = data.get("feature_idf", {})
        self.bm25 = data["bm25_index"]
        self.dim = data.get("embedding_dim", 384)

        # Pre-compute document matrix for batch vector dot products
        self.doc_ids = list(self.dense_embeddings.keys())
        self.doc_matrix = np.stack([self.dense_embeddings[cid] for cid in self.doc_ids])

    def _query_vector(self, query: str) -> np.ndarray:
        """Projects query text into the normalized embedding space using TF-IDF subword feature hashing."""
        feats = extract_features(query)
        return compute_feature_vector(feats, self.feature_idf, dim=self.dim)

    def _bm25_search(self, query: str, top_n: int = 15, k1: float = 1.5, b: float = 0.75) -> List[tuple]:
        """Calculates Okapi BM25 scores for query tokens across inverted index."""
        tokens = tokenize(query)
        if not tokens:
            return []

        scores = {}
        avgdl = self.bm25["avgdl"]
        doc_lens = self.bm25["doc_lens"]
        idf_dict = self.bm25["idf"]
        inverted_index = self.bm25["inverted_index"]

        for token in tokens:
            if token not in inverted_index:
                continue
            idf = idf_dict.get(token, 0.0)
            postings = inverted_index[token]

            for doc_id, tf in postings.items():
                dl = doc_lens.get(doc_id, avgdl)
                # Okapi BM25 formula
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (dl / avgdl))
                score_term = idf * (numerator / denominator)
                scores[doc_id] = scores.get(doc_id, 0.0) + score_term

        # Sort descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]

    def _dense_search(self, query: str, top_n: int = 15) -> List[tuple]:
        """Computes cosine similarity against all documents."""
        q_vec = self._query_vector(query)
        # Cosine similarities = dot products of normalized vectors
        sims = np.dot(self.doc_matrix, q_vec)
        top_indices = np.argsort(sims)[::-1][:top_n]
        return [(self.doc_ids[idx], float(sims[idx])) for idx in top_indices]

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """Executes Hybrid Search combining Dense and BM25 candidate lists via Reciprocal Rank Fusion (RRF).

        Formula:
            RRF_score(d) = sum(1 / (rrf_k + rank_i(d)))
        """
        dense_results = self._dense_search(query, top_n=20)
        bm25_results = self._bm25_search(query, top_n=20)

        # Build rank maps (1-indexed)
        dense_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(dense_results)}
        bm25_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(bm25_results)}

        all_doc_ids = set(dense_ranks.keys()).union(set(bm25_ranks.keys()))
        rrf_scores = {}

        for doc_id in all_doc_ids:
            score = 0.0
            if doc_id in dense_ranks:
                score += 1.0 / (rrf_k + dense_ranks[doc_id])
            if doc_id in bm25_ranks:
                score += 1.0 / (rrf_k + bm25_ranks[doc_id])
            rrf_scores[doc_id] = score

        # Sort by final RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for doc_id, score in sorted_docs:
            chunk = self.chunks_map.get(doc_id, {})
            results.append({
                "id": doc_id,
                "title": chunk.get("title", ""),
                "category": chunk.get("category", ""),
                "content": chunk.get("content", ""),
                "tags": chunk.get("tags", []),
                "metadata": chunk.get("metadata", {}),
                "rrf_score": round(score, 6),
                "dense_rank": dense_ranks.get(doc_id, None),
                "bm25_rank": bm25_ranks.get(doc_id, None),
            })

        return results


if __name__ == "__main__":
    import sys
    retriever = HybridRetriever()
    test_query = sys.argv[1] if len(sys.argv) > 1 else "Tell me about Brandon's experience with Kubernetes and Terraform"
    print(f"\n--- Testing Hybrid Retrieval for query: '{test_query}' ---")
    hits = retriever.retrieve(test_query, top_k=3)
    for i, hit in enumerate(hits, 1):
        print(f"\n[{i}] {hit['title']} (RRF Score: {hit['rrf_score']})")
        print(f"    Dense Rank: {hit['dense_rank']} | BM25 Rank: {hit['bm25_rank']}")
        print(f"    Category: {hit['category']} | Tags: {hit['tags'][:5]}")
        print(f"    Excerpt: {hit['content'][:140]}...")
