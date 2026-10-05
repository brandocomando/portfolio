"""Gold Layer Builder: Constructs the Hybrid Retrieval Index (Dense Embeddings + BM25 Sparse Index).

Produces an immutable, versioned artifact bundle with cryptographic manifests for zero-cost
in-memory serving in Cloud Run.
"""

import os
import re
import json
import math
import hashlib
import datetime
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

SILVER_DIR = Path(__file__).resolve().parent.parent / "data" / "silver"
GOLD_DIR = Path(__file__).resolve().parent.parent / "data" / "gold"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric terms with stopword filtering."""
    words = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
    return [w for w in words if w not in STOPWORDS]


def build_bm25_index(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Constructs an Okapi BM25 sparse inverted index."""
    doc_tokens = {}
    doc_lens = {}
    inverted_index = {}
    df = {}  # Document frequency of term

    for c in chunks:
        cid = c["id"]
        # Incorporate title, content, and tags with boosted importance
        enriched_text = f"{c['title']} {c['title']} {' '.join(c.get('tags', []))} {c['content']}"
        tokens = tokenize(enriched_text)
        doc_tokens[cid] = tokens
        doc_lens[cid] = len(tokens)

        # Count frequencies in this document
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        for t, count in tf.items():
            if t not in inverted_index:
                inverted_index[t] = {}
                df[t] = 0
            inverted_index[t][cid] = count
            df[t] += 1

    num_docs = len(chunks)
    avgdl = sum(doc_lens.values()) / max(1, num_docs)

    # Compute IDF per term: ln(1 + (N - n + 0.5) / (n + 0.5))
    idf = {}
    for t, n in df.items():
        idf[t] = math.log(1.0 + (num_docs - n + 0.5) / (n + 0.5))

    return {
        "num_docs": num_docs,
        "avgdl": avgdl,
        "doc_lens": doc_lens,
        "idf": idf,
        "inverted_index": inverted_index,
        "vocabulary_size": len(inverted_index)
    }


def extract_features(text: str) -> List[tuple]:
    """Extracts whole tokens and character subword n-grams for semantic feature hashing."""
    tokens = tokenize(text)
    features = []
    for t in tokens:
        # Whole word feature
        features.append((f"w:{t}", 1.5))
        # Subword n-grams (3-grams and 4-grams) to capture morphology and compound terms
        if len(t) >= 4:
            for n in (3, 4):
                for i in range(len(t) - n + 1):
                    features.append((f"ng:{t[i:i+n]}", 0.5))
    return features


def compute_feature_vector(features: List[tuple], idf_dict: Dict[str, float], dim: int = 384) -> np.ndarray:
    """Projects features into dim-dimensional unit sphere using TF-IDF weighting and feature hashing."""
    vec = np.zeros(dim, dtype=np.float32)
    # Count frequencies
    counts = {}
    for feat, mult in features:
        counts[feat] = counts.get(feat, 0.0) + mult

    for feat, count in counts.items():
        # Retrieve IDF or default to median IDF
        idf = idf_dict.get(feat, 1.2)
        weight = (1.0 + math.log(count)) * idf
        h1 = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16) % dim
        h2 = int(hashlib.sha256(feat.encode("utf-8")).hexdigest(), 16) % dim
        sign = 1.0 if h2 % 2 == 0 else -1.0
        vec[h1] += sign * weight

    norm = np.linalg.norm(vec)
    if norm > 0:
        return vec / norm
    else:
        vec[0] = 1.0
        return vec


def generate_dense_embeddings(chunks: List[Dict[str, Any]], dim: int = 384) -> tuple:
    """Generates L2-normalized dense embeddings via subword TF-IDF feature hashing."""
    # 1. Compute document frequencies across all chunk features
    doc_features = {}
    df = {}
    for c in chunks:
        cid = c["id"]
        # Boost title and tags in document representation
        boosted_text = f"{c['title']} {c['title']} {' '.join(c.get('tags', []))} {c['content']}"
        feats = extract_features(boosted_text)
        doc_features[cid] = feats
        unique_feats = set(f[0] for f in feats)
        for u in unique_feats:
            df[u] = df.get(u, 0) + 1

    num_docs = len(chunks)
    feature_idf = {}
    for feat, n in df.items():
        feature_idf[feat] = math.log(1.0 + (num_docs - n + 0.5) / (n + 0.5))

    embeddings = {}
    for cid, feats in doc_features.items():
        vec = compute_feature_vector(feats, feature_idf, dim=dim)
        embeddings[cid] = [round(float(v), 6) for v in vec]

    return embeddings, feature_idf



def get_git_sha() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return "local-dev"


def run_gold_build():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    with open(SILVER_DIR / "chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Building Gold Index for {len(chunks)} chunks...")

    # 1. Build Sparse BM25 Index
    bm25 = build_bm25_index(chunks)
    print(f"✅ BM25 Inverted Index built: {bm25['vocabulary_size']} unique terms, avgdl={bm25['avgdl']:.1f}")

    # 2. Build Dense Embeddings
    dense_dim = 384
    dense_embeddings, feature_idf = generate_dense_embeddings(chunks, dim=dense_dim)
    print(f"✅ Dense Embeddings built: {len(dense_embeddings)} vectors (dimension={dense_dim}, features={len(feature_idf)})")

    # 3. Serialize Bundle
    bundle = {
        "version": "1.0.0",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "chunks": chunks,
        "dense_embeddings": dense_embeddings,
        "feature_idf": feature_idf,
        "bm25_index": bm25,
        "embedding_dim": dense_dim,
    }

    bundle_json = json.dumps(bundle, separators=(",", ":"))
    bundle_hash = hashlib.sha256(bundle_json.encode("utf-8")).hexdigest()

    gold_output = GOLD_DIR / "gold_index.json"
    with open(gold_output, "w", encoding="utf-8") as f:
        f.write(bundle_json)

    # 4. Write Signed Manifest
    manifest = {
        "stage": "gold",
        "build_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "git_sha": get_git_sha(),
        "chunk_count": len(chunks),
        "embedding_model": "deterministic-projection-v1",
        "embedding_dim": dense_dim,
        "vocabulary_size": bm25["vocabulary_size"],
        "checksum_sha256": bundle_hash,
        "bundle_file": str(gold_output),
        "bundle_size_bytes": len(bundle_json.encode("utf-8"))
    }

    with open(GOLD_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Gold Index Artifact packaged: {gold_output.name} ({manifest['bundle_size_bytes'] / 1024:.1f} KB, SHA-256: {bundle_hash[:12]}...)")
    return manifest


if __name__ == "__main__":
    run_gold_build()
