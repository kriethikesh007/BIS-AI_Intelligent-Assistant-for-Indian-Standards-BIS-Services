import json
import time
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_retrieval")

# Ground-truth evaluation benchmarks covering diverse product domains,
# exact codes, multilingual variants, and out-of-scope non-cataloged items.
COMPREHENSIVE_RETRIEVAL_BENCHMARKS = [
    # ── Exact Standard Lookups ──
    {"id": "RET-01", "query": "IS 4151 motorcycle helmets specifications", "targets": ["4151"], "type": "exact_code", "lang": "en"},
    {"id": "RET-02", "query": "IS 14543 packaged drinking water requirements", "targets": ["14543"], "type": "exact_code", "lang": "en"},
    {"id": "RET-03", "query": "IS 616 audio video and earphones safety", "targets": ["616"], "type": "exact_code", "lang": "en"},
    {"id": "RET-04", "query": "IS 2347 domestic pressure cookers", "targets": ["2347"], "type": "exact_code", "lang": "en"},
    {"id": "RET-05", "query": "IS 694 pvc insulated electric wires and cables", "targets": ["694"], "type": "exact_code", "lang": "en"},

    # ── Product-to-Standard Domain Queries ──
    {"id": "RET-06", "query": "Protective helmets for two wheeler motorcycle riders", "targets": ["4151"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-07", "query": "Commercial packaged drinking water 20 litre bottles", "targets": ["14543"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-08", "query": "Plugs and socket-outlets 16A 6A for domestic appliances", "targets": ["1293"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-09", "query": "Secondary lithium ion battery packs and power banks", "targets": ["16046"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-10", "query": "Laptops desktop computers and servers safety", "targets": ["13252"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-11", "query": "Children plastic and mechanical toys safety requirements", "targets": ["9873"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-12", "query": "Ordinary Portland Cement 43 and 53 grade for construction", "targets": ["269"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-13", "query": "TMT steel rebar deformed bars Fe 500 for concrete reinforcement", "targets": ["1786"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-14", "query": "Gold jewellery 22K 916 purity and HUID hallmarks", "targets": ["1417"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-15", "query": "Silver ornaments 925 sterling silver hallmarking fineness", "targets": ["2112"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-16", "query": "Electric dry iron and steam press household appliances", "targets": ["302"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-17", "query": "Emergency rechargeable LED lights and luminaires", "targets": ["10322"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-18", "query": "Wireless Bluetooth earphones and headphones with microphone", "targets": ["616"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-19", "query": "Crystalline silicon solar photovoltaic modules and solar panels", "targets": ["14286"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-20", "query": "Rooftop solar power converters and grid tied PV inverters", "targets": ["16221"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-21", "query": "Room air conditioner split AC unit energy and safety", "targets": ["1391"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-22", "query": "Domestic pressure cooker with pressure safety relief valve", "targets": ["2347"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-23", "query": "LPG cooking gas cylinders low carbon welded steel", "targets": ["3196"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-24", "query": "Self ballasted LED bulb retrofit B22 lamp", "targets": ["16102"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-25", "query": "House wiring copper cables 1100V single core", "targets": ["694"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-26", "query": "Residual current operated circuit breakers RCCB for shock protection", "targets": ["12640"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-27", "query": "HDPE pipes for potable water supply and agricultural irrigation", "targets": ["4984"], "type": "product_recommendation", "lang": "en"},
    {"id": "RET-28", "query": "Industrial safety shoes with steel toe cap 200 Joules", "targets": ["15298"], "type": "product_recommendation", "lang": "en"},

    # ── Multilingual & Colloquial Variants ──
    {"id": "RET-29", "query": "Two wheeler helmet manufacturing standard batao", "targets": ["4151"], "type": "multilingual_hinglish", "lang": "hi"},
    {"id": "RET-30", "query": "Packaged drinking water jar standard kya hai?", "targets": ["14543"], "type": "multilingual_hinglish", "lang": "hi"},
    {"id": "RET-31", "query": "Gold jewellery 916 hallmark standard enna?", "targets": ["1417"], "type": "multilingual_tanglish", "lang": "ta"},
    {"id": "RET-32", "query": "Pressure cooker bananeka mandatory standard", "targets": ["2347"], "type": "multilingual_hinglish", "lang": "hi"},
    {"id": "RET-33", "query": "LED bulb specification standard enna details sollu", "targets": ["16102"], "type": "multilingual_tanglish", "lang": "ta"},

    # ── Out-of-Catalog / Non-existent Concepts (Must safely yield no spurious high-confidence match) ──
    {"id": "RET-34", "query": "Intergalactic quantum teleportation warp drive engine", "targets": [], "type": "out_of_catalog", "lang": "en"},
    {"id": "RET-35", "query": "Extraterrestrial alien spaceship hyperdrive booster", "targets": [], "type": "out_of_catalog", "lang": "en"}
]

def run_retrieval_evaluation() -> Dict[str, Any]:
    from services.recommendation_engine import recommendation_engine

    logger.info("Initializing Recommendation Engine for Retrieval Benchmark...")
    recommendation_engine._load_data_and_index()
    total_indexed = len(recommendation_engine.standards)
    logger.info(f"Loaded {total_indexed} indexed Indian Standards.")

    in_catalog_queries = [b for b in COMPREHENSIVE_RETRIEVAL_BENCHMARKS if b["targets"]]
    out_of_catalog_queries = [b for b in COMPREHENSIVE_RETRIEVAL_BENCHMARKS if not b["targets"]]

    top1_correct = 0
    top3_correct = 0
    top5_correct = 0
    reciprocal_ranks = []
    precisions_at_k = {1: [], 3: [], 5: []}
    recalls_at_k = {1: [], 3: [], 5: []}
    normalized_precisions_at_k = {1: [], 3: [], 5: []}
    latencies = []

    per_query_results = []

    for b in in_catalog_queries:
        t0 = time.perf_counter()
        res = recommendation_engine.recommend(b["query"], top_k=5)
        dt = (time.perf_counter() - t0) * 1000
        latencies.append(dt)

        top_standards = res.get("top_standards", [])
        retrieved_codes = [s.get("standard_number") or s.get("standard_code", "") for s in top_standards]
        
        # Check targets
        found_rank = None
        for rank_idx, code in enumerate(retrieved_codes):
            if any(t in code for t in b["targets"]):
                found_rank = rank_idx + 1
                break

        if found_rank == 1:
            top1_correct += 1
        if found_rank is not None and found_rank <= 3:
            top3_correct += 1
        if found_rank is not None and found_rank <= 5:
            top5_correct += 1

        if found_rank is not None:
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)

        # Precision & Recall @ K
        for k in [1, 3, 5]:
            subset = retrieved_codes[:k]
            matches = sum(1 for c in subset if any(t in c for t in b["targets"]))
            precisions_at_k[k].append(matches / k)
            recalls_at_k[k].append(1.0 if matches > 0 else 0.0)
            
            # Normalized Precision: Precision / MaxPossiblePrecision(1/min(k, len(targets)))
            max_possible_prec = min(1.0, len(b["targets"]) / k)
            norm_p = (matches / k) / max_possible_prec if max_possible_prec > 0 else 0.0
            normalized_precisions_at_k[k].append(norm_p)

        per_query_results.append({
            "id": b["id"],
            "query": b["query"],
            "targets": b["targets"],
            "found_rank": found_rank,
            "top_match": retrieved_codes[0] if retrieved_codes else "None",
            "latency_ms": round(dt, 2)
        })

    # Out of catalog abstention test
    abstention_passed = 0
    for b in out_of_catalog_queries:
        res = recommendation_engine.recommend(b["query"], top_k=5)
        top_standards = res.get("top_standards", [])
        # Safe behavior: either empty or top score below relevance threshold (0.35)
        top_score = top_standards[0].get("relevance_score", 0.0) if top_standards else 0.0
        if not top_standards or top_score < 0.35:
            abstention_passed += 1

    n = len(in_catalog_queries)
    metrics = {
        "dataset_version": "2.0 (Comprehensive 25-Standard Expanded Catalog)",
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_standards_indexed": total_indexed,
        "total_evaluation_queries": len(COMPREHENSIVE_RETRIEVAL_BENCHMARKS),
        "in_catalog_queries": n,
        "out_of_catalog_queries": len(out_of_catalog_queries),
        "top_1_accuracy": round(top1_correct / n, 4),
        "top_3_accuracy": round(top3_correct / n, 4),
        "top_5_accuracy": round(top5_correct / n, 4),
        "mrr": round(float(np.mean(reciprocal_ranks)), 4),
        "precision_at_1": round(float(np.mean(precisions_at_k[1])), 4),
        "precision_at_3": round(float(np.mean(precisions_at_k[3])), 4),
        "precision_at_5": round(float(np.mean(precisions_at_k[5])), 4),
        "normalized_precision_at_3": round(float(np.mean(normalized_precisions_at_k[3])), 4),
        "normalized_precision_at_5": round(float(np.mean(normalized_precisions_at_k[5])), 4),
        "recall_at_1": round(float(np.mean(recalls_at_k[1])), 4),
        "recall_at_3": round(float(np.mean(recalls_at_k[3])), 4),
        "recall_at_5": round(float(np.mean(recalls_at_k[5])), 4),
        "out_of_catalog_abstention_rate": round(abstention_passed / max(len(out_of_catalog_queries), 1), 4),
        "mean_latency_ms": round(float(np.mean(latencies)), 2),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        "metric_definitions": {
            "top_1_accuracy": "Proportion of queries where the target standard is ranked at Rank 1.",
            "top_5_accuracy": "Proportion of queries where the target standard appears in the top 5 ranked recommendations (Hit Rate@5).",
            "mrr": "Mean Reciprocal Rank (1/rank) of the target standard.",
            "precision_at_k": "Average ratio of relevant items among top K returned results. Note: On single-target queries, max theoretical Precision@3 is 33.3% and Precision@5 is 20.0%.",
            "normalized_precision_at_k": "Precision@K divided by theoretical maximum precision for the query target count, measuring relevant ranking efficiency without single-target penalty.",
            "out_of_catalog_abstention_rate": "Proportion of fictitious or out-of-catalog queries correctly resulting in no false high-confidence recommendation."
        },
        "per_query_results": per_query_results
    }

    # Save to data/
    out_path = Path("data/retrieval_evaluation_metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Retrieval evaluation saved to {out_path}.")

    # Generate Markdown documentation report
    report_md = f"""# BIS-AI: Information Retrieval Evaluation & Benchmark Audit Report

**Date:** {metrics['evaluation_timestamp']}  
**Catalog Indexed:** {total_indexed} Verified Indian Standards  
**Evaluation Set:** {len(COMPREHENSIVE_RETRIEVAL_BENCHMARKS)} Queries (Exact codes, domain queries, multilingual, and out-of-catalog)  

---

## 1. Summary Performance Metrics

| Retrieval Metric | Score | Percentage | Benchmark Interpretation |
|---|---|---|---|
| **Top-1 Accuracy** | `{metrics['top_1_accuracy']}` | **{metrics['top_1_accuracy']*100:.1f}%** | Target standard correctly ranked first |
| **Top-3 Accuracy** | `{metrics['top_3_accuracy']}` | **{metrics['top_3_accuracy']*100:.1f}%** | Target standard in top 3 |
| **Top-5 Accuracy (Hit Rate@5)** | `{metrics['top_5_accuracy']}` | **{metrics['top_5_accuracy']*100:.1f}%** | Target standard in top 5 recommendations |
| **Mean Reciprocal Rank (MRR)** | `{metrics['mrr']}` | **{metrics['mrr']:.4f}** | Average reciprocal rank of relevant standard |
| **Recall@1** | `{metrics['recall_at_1']}` | **{metrics['recall_at_1']*100:.1f}%** | Relevant standard captured at K=1 |
| **Recall@5** | `{metrics['recall_at_5']}` | **{metrics['recall_at_5']*100:.1f}%** | Relevant standard captured at K=5 |
| **Normalized Precision@3** | `{metrics['normalized_precision_at_3']}` | **{metrics['normalized_precision_at_3']*100:.1f}%** | Precision normalized by single-target upper bound (33.3%) |
| **Normalized Precision@5** | `{metrics['normalized_precision_at_5']}` | **{metrics['normalized_precision_at_5']*100:.1f}%** | Precision normalized by single-target upper bound (20.0%) |
| **Raw Precision@3** | `{metrics['precision_at_3']}` | **{metrics['precision_at_3']*100:.1f}%** | Raw matches / 3 (Upper bound: 33.3%) |
| **Raw Precision@5** | `{metrics['precision_at_5']}` | **{metrics['precision_at_5']*100:.1f}%** | Raw matches / 5 (Upper bound: 20.0%) |
| **Out-of-Catalog Abstention** | `{metrics['out_of_catalog_abstention_rate']}` | **{metrics['out_of_catalog_abstention_rate']*100:.1f}%** | Safe non-recommendation on fictitious queries |

---

## 2. Investigation of Previous Audit Results (The 78.6% Anomaly Explained)

The previous audit reported:
- Top-1 Accuracy: 78.6%
- Top-5 Accuracy: 78.6%
- Precision@3: 26.2%
- Precision@5: 15.7%

**Audit Findings on the Anomaly:**
1. The prior evaluation script evaluated exactly 14 queries. 11 of the 14 queries retrieved their target standard at **Rank 1**. The remaining 3 queries did not match in the top 5 (because those 3 standards were unindexed in the 13-standard catalog).
2. Because all 11 successful retrievals occurred at Rank 1, exactly 11 items were present in Top-1, and exactly 11 were present in Top-5:
   Top-1 Accuracy = 11 / 14 = 78.57%, Top-5 Accuracy = 11 / 14 = 78.57%
   This was not a manufactured metric, but a direct consequence of a small single-target benchmark.
3. Similarly, because each query had exactly 1 relevant ground-truth standard, returning 3 results capped maximum possible Precision@3 at 1/3 = 33.33%:
   Precision@3 = (11 * (1/3) + 3 * 0) / 14 = 26.19%
   Precision@5 = (11 * (1/5) + 3 * 0) / 14 = 15.71%
4. The expanded catalog (25 standards) and updated evaluation benchmark resolve the unindexed targets and provide both Raw Precision@K and Normalized Precision@K for honest SIH presentation.
"""
    doc_path = Path("docs/retrieval_evaluation_report.md")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    logger.info(f"Documentation report saved to {doc_path}.")

    print("\n" + "=" * 65)
    print("      INFORMATION RETRIEVAL EVALUATION REPORT")
    print("=" * 65)
    print(f"Top-1 Accuracy: {metrics['top_1_accuracy']*100:.1f}% | Top-5 Hit Rate: {metrics['top_5_accuracy']*100:.1f}% | MRR: {metrics['mrr']:.4f}")
    print(f"Normalized Precision@3: {metrics['normalized_precision_at_3']*100:.1f}% | Normalized Precision@5: {metrics['normalized_precision_at_5']*100:.1f}%")
    print(f"Raw Precision@3: {metrics['precision_at_3']*100:.1f}% | Raw Precision@5: {metrics['precision_at_5']*100:.1f}%")
    print(f"Mean Latency: {metrics['mean_latency_ms']} ms | P95 Latency: {metrics['p95_latency_ms']} ms")
    print(f"Abstention on Fictitious Queries: {metrics['out_of_catalog_abstention_rate']*100:.1f}%")
    print("=" * 65 + "\n")

    return metrics

if __name__ == "__main__":
    run_retrieval_evaluation()
