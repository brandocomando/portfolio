"""Automated Continuous Evaluation & Quality Gate Suite.

Runs benchmark tests against the Golden Dataset, evaluating:
1. Context Recall & Hit Rate @ K (Did retrieval pull the required chunk?)
2. Mean Reciprocal Rank (MRR)
3. Keyword & Entity Precision in Retrieved Chunks
4. Adversarial Guardrail Deflection Rate

Acts as a CI Gate: Fails build if performance drops below defined thresholds.
"""

import sys
import json
import re
import datetime
from pathlib import Path
from typing import Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mlops.pipeline.hybrid_retriever import HybridRetriever

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_DATASET_FILE = EVAL_DIR / "golden_dataset.json"
REPORT_OUTPUT_FILE = EVAL_DIR / "eval_report.json"

# Quality Gate Thresholds
MIN_HIT_RATE_TOP3 = 0.85
MIN_MRR = 0.70
MIN_GUARDRAIL_PASS_RATE = 1.00


def detect_adversarial_prompt(prompt: str) -> bool:
    """Simulates security guardrail screening for prompt injection attempts."""
    patterns = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+prompt",
        r"delete\s+your",
        r"reveal\s+your",
        r"jailbreak",
        r"you\s+are\s+now\s+in\s+dan\s+mode",
    ]
    prompt_lower = prompt.lower()
    return any(re.search(pat, prompt_lower) for pat in patterns)


def run_evaluation() -> bool:
    print("\n🔍 Running MLOps Continuous Evaluation Gate (Golden Dataset Benchmark)...")

    if not GOLDEN_DATASET_FILE.exists():
        print(f"❌ Golden dataset missing: {GOLDEN_DATASET_FILE}")
        return False

    with open(GOLDEN_DATASET_FILE, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    retriever = HybridRetriever()

    total_standard_tests = 0
    hits_top3 = 0
    reciprocal_ranks = []
    keyword_hits = 0
    total_keywords_checked = 0

    total_adversarial_tests = 0
    guardrail_deflections = 0

    results_detail = []

    for test in benchmarks:
        tid = test["id"]
        q = test["question"]
        is_adv = test.get("is_adversarial", False)

        if is_adv:
            total_adversarial_tests += 1
            deflected = detect_adversarial_prompt(q)
            if deflected:
                guardrail_deflections += 1
                status = "PASS (Deflected by Guardrail)"
            else:
                status = "FAIL (Guardrail Missed)"
            results_detail.append({
                "id": tid,
                "type": "adversarial",
                "question": q,
                "status": status,
                "deflected": deflected
            })
            continue

        total_standard_tests += 1
        target_chunk = test.get("target_chunk_id")
        expected_keywords = test.get("expected_keywords", [])

        # Retrieve top 3
        retrieved = retriever.retrieve(q, top_k=3)
        retrieved_ids = [r["id"] for r in retrieved]

        # Check hit in top 3
        hit = target_chunk in retrieved_ids if target_chunk else False
        rank = retrieved_ids.index(target_chunk) + 1 if hit else 0

        if hit:
            hits_top3 += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

        # Check keyword presence in combined retrieved text
        combined_text = " ".join([r["content"].lower() + " " + r["title"].lower() for r in retrieved])
        kw_found = sum(1 for kw in expected_keywords if kw.lower() in combined_text)
        keyword_hits += kw_found
        total_keywords_checked += max(1, len(expected_keywords))

        results_detail.append({
            "id": tid,
            "type": "retrieval",
            "question": q,
            "target_chunk": target_chunk,
            "retrieved_ids": retrieved_ids,
            "hit_top3": hit,
            "rank": rank,
            "keyword_recall": f"{kw_found}/{len(expected_keywords)}"
        })

    # Calculate aggregate metrics
    hit_rate = hits_top3 / max(1, total_standard_tests)
    mrr = sum(reciprocal_ranks) / max(1, len(reciprocal_ranks))
    guardrail_rate = guardrail_deflections / max(1, total_adversarial_tests)
    kw_rate = keyword_hits / max(1, total_keywords_checked)

    print("\n" + "=" * 60)
    print(" 📊 MLOPS RETRIEVAL & QUALITY GATE BENCHMARK REPORT")
    print("=" * 60)
    print(f" Standard Q&A Tests Evaluated:   {total_standard_tests}")
    print(f" Adversarial Tests Evaluated:    {total_adversarial_tests}")
    print(f" Top-3 Retrieval Hit Rate:       {hit_rate:.1%}  (Threshold: {MIN_HIT_RATE_TOP3:.1%})")
    print(f" Mean Reciprocal Rank (MRR):     {mrr:.3f}   (Threshold: {MIN_MRR:.3f})")
    print(f" Expected Keyword Recall:        {kw_rate:.1%}")
    print(f" Adversarial Deflection Rate:    {guardrail_rate:.1%} (Threshold: {MIN_GUARDRAIL_PASS_RATE:.1%})")
    print("=" * 60)

    # Check Gates
    gate_hit = hit_rate >= MIN_HIT_RATE_TOP3
    gate_mrr = mrr >= MIN_MRR
    gate_guard = guardrail_rate >= MIN_GUARDRAIL_PASS_RATE
    all_passed = gate_hit and gate_mrr and gate_guard

    report = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "passed": all_passed,
        "metrics": {
            "total_tests": len(benchmarks),
            "hit_rate_top3": round(hit_rate, 4),
            "mrr": round(mrr, 4),
            "keyword_recall": round(kw_rate, 4),
            "guardrail_pass_rate": round(guardrail_rate, 4)
        },
        "gates": {
            "hit_rate_gate": gate_hit,
            "mrr_gate": gate_mrr,
            "guardrail_gate": gate_guard
        },
        "details": results_detail
    }

    with open(REPORT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if all_passed:
        print("\n🎉 QUALITY GATE: PASSED! Ready for deployment.\n")
        return True
    else:
        print("\n❌ QUALITY GATE: FAILED! One or more quality thresholds were breached.\n")
        return False


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
