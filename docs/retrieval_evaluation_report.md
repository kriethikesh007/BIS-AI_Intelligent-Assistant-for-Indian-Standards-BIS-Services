# BIS-AI: Information Retrieval Evaluation & Benchmark Audit Report

**Date:** 2026-10-27T09:19:04Z  
**Catalog Indexed:** 25 Verified Indian Standards  
**Evaluation Set:** 35 Queries (Exact codes, domain queries, multilingual, and out-of-catalog)  

---

## 1. Summary Performance Metrics

| Retrieval Metric | Score | Percentage | Benchmark Interpretation |
|---|---|---|---|
| **Top-1 Accuracy** | `1.0` | **100.0%** | Target standard correctly ranked first |
| **Top-3 Accuracy** | `1.0` | **100.0%** | Target standard in top 3 |
| **Top-5 Accuracy (Hit Rate@5)** | `1.0` | **100.0%** | Target standard in top 5 recommendations |
| **Mean Reciprocal Rank (MRR)** | `1.0` | **1.0000** | Average reciprocal rank of relevant standard |
| **Recall@1** | `1.0` | **100.0%** | Relevant standard captured at K=1 |
| **Recall@5** | `1.0` | **100.0%** | Relevant standard captured at K=5 |
| **Normalized Precision@3** | `1.0` | **100.0%** | Precision normalized by single-target upper bound (33.3%) |
| **Normalized Precision@5** | `1.0` | **100.0%** | Precision normalized by single-target upper bound (20.0%) |
| **Raw Precision@3** | `0.3333` | **33.3%** | Raw matches / 3 (Upper bound: 33.3%) |
| **Raw Precision@5** | `0.2` | **20.0%** | Raw matches / 5 (Upper bound: 20.0%) |
| **Out-of-Catalog Abstention** | `1.0` | **100.0%** | Safe non-recommendation on fictitious queries |

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
