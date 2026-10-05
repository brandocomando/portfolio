"""Retrieval Service: In-Memory Hybrid Search wrapper."""

import os
from pathlib import Path
from typing import List, Dict, Any

from backend.app.core.config import settings
from mlops.pipeline.hybrid_retriever import HybridRetriever


class RetrievalService:
    def __init__(self):
        index_path = settings.GOLD_INDEX_PATH
        # Fallback to local file relative to repo root if path doesn't exist
        if not index_path.exists():
            alt_path = Path(__file__).resolve().parent.parent.parent.parent / "mlops" / "data" / "gold" / "gold_index.json"
            if alt_path.exists():
                index_path = alt_path

        self.retriever = HybridRetriever(index_path=index_path)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.retriever.retrieve(query, top_k=top_k)


# Singleton instance
retrieval_service = RetrievalService()
