# BIS-AI: Final System Evaluation & Benchmarking Report

**Generated:** 2026-10-27 09:30:34  
**System:** BIS-AI: Intelligent Assistant for Indian Standards & BIS Services  
**Overall Status:** 🟢 ALL 14 TEST SUITES PASSED

---

## 1. Machine Learning Intent Ensemble Evaluation

The intent classifier evaluates queries across 8 classes using an ensemble of **Random Forest**, **Extra Trees**, and **Gradient Boosting** united via `VotingClassifier(voting='soft')`.

### Summary Metrics

| Metric | Score | Percentage | Description |
|---|---|---|---|
| **Overall Accuracy** | `0.9442` | **94.42%** | Overall correct intent predictions |
| **Weighted Precision** | `0.947` | **94.70%** | Weighted precision across intent classes |
| **Macro Precision** | `0.9413` | **94.13%** | Unweighted mean precision |
| **Weighted Recall** | `0.9442` | **94.42%** | Weighted sensitivity |
| **Macro Recall** | `0.9397` | **93.97%** | Unweighted mean recall |
| **Weighted F1-Score** | `0.9445` | **94.45%** | Harmonic mean of precision & recall |
| **Macro F1-Score** | `0.9394` | **93.94%** | Class-balanced harmonic mean |

### 8x8 Confusion Matrix

| Actual \ Predicted | **CERTIF..** | **CONSUM..** | **GENERA..** | **HALLMA..** | **LABORA..** | **OTHER..** | **STANDA..** | **STANDA..** |
|---|---|---|---|---|---|---|---|---|
| **CERTIFICATION** | 23 | 0 | 1 | 0 | 0 | 2 | 0 | 0 |
| **CONSUMER** | 0 | 21 | 1 | 0 | 0 | 0 | 0 | 0 |
| **GENERAL_BIS** | 0 | 0 | 18 | 0 | 0 | 2 | 0 | 0 |
| **HALLMARKING** | 0 | 2 | 0 | 22 | 0 | 0 | 0 | 0 |
| **LABORATORY** | 0 | 0 | 0 | 0 | 23 | 0 | 0 | 0 |
| **OTHER** | 0 | 0 | 0 | 0 | 0 | 18 | 2 | 0 |
| **STANDARD_INFORMATION** | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 1 |
| **STANDARD_RECOMMENDATION** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 |

---

## 2. Information Retrieval & Recommendation Engine Evaluation

Evaluated on ground-truth product descriptions against official Indian Standards catalog using the 4-signal hybrid formula:
$$\text{Final Score} = 0.35 \times \text{TF-IDF} + 0.35 \times \text{Semantic} + 0.20 \times \text{Keyword} + 0.10 \times \text{Category}$$

| Retrieval Metric | Score | Percentage / Benchmark | Interpretation |
|---|---|---|---|
| **Top-1 Accuracy** | `1.0` | **100.0%** | Correct standard ranked first |
| **Top-5 Accuracy** | `1.0` | **100.0%** | Target standard in top 5 recommendations |
| **Mean Reciprocal Rank (MRR)** | `1.0` | **1.0000** | Average reciprocal rank of relevant standard |
| **Precision@1** | `1.0` | **100.0%** | Precision for top-1 retrieved result |
| **Precision@3** | `0.3333` | **33.3%** | Precision among top-3 results |
| **Precision@5** | `0.2` | **20.0%** | Precision among top-5 results |
| **Recall@1** | `1.0` | **100.0%** | Relevant standard captured at K=1 |
| **Recall@3** | `1.0` | **100.0%** | Relevant standard captured at K=3 |
| **Recall@5** | `1.0` | **100.0%** | Relevant standard captured at K=5 |

---

## 3. System Performance & Latency Benchmarks

| Operation / Component | Mean Latency | Median (P50) | P95 Latency | Min Latency | Max Latency |
|---|---|---|---|---|---|
| **Model Intent Prediction** | `3.79 ms` | `0.24 ms` | `16.92 ms` | `0.13 ms` | `20.05 ms` |
| **Hybrid Retrieval Execution** | `4.33 ms` | `4.31 ms` | `5.97 ms` | `2.98 ms` | `6.66 ms` |
| **Full API Response (Overall)** | `893.13 ms` | `10.98 ms` | `4037.6 ms` | `4.46 ms` | `6167.91 ms` |
| &bull; *POST /api/chat* | `2410.17 ms` | - | - | - | - |
| &bull; *POST /api/recommend-standard* | `10.4 ms` | - | - | - | - |
| &bull; *GET /api/standards* | `5.09 ms` | - | - | - | - |

---

## 4. Comprehensive 14 Scenario Test Results

| # | Test Scenario | Status | Verified Behavior & Details |
|---|---|---|---|
| 1 | **Intent Classification** | ✅ PASSED | Predicted: STANDARD_RECOMMENDATION (confidence: 0.9) |
| 2 | **Standard Recommendation** | ✅ PASSED | Top: IS 10322 (Part 5/Sec 8):2013 (Score: 1.00) |
| 3 | **Certification Retrieval** | ✅ PASSED | Retrieved 6 certification schemes successfully |
| 4 | **Hallmarking Queries** | ✅ PASSED | Verified 3 mandatory marks & HUID rules (1 FAQs) |
| 5 | **Laboratory Queries** | ✅ PASSED | Retrieved Central Lab with NABL accreditation and testing disciplines |
| 6 | **Consumer Queries** | ✅ PASSED | Verified BIS CARE mobile app and CML verification tools |
| 7 | **Unknown Queries (Guardrail Fallback)** | ✅ PASSED | Strict fallback message correctly triggered without hallucination |
| 8 | **Multilingual Queries** | ✅ PASSED | Validated English, Hindi, Tamil, entity preservation and unsupported fallback |
| 9 | **Empty Queries** | ✅ PASSED | Handled empty query gracefully without server crash (Status 400) |
| 10 | **Invalid Input** | ✅ PASSED | Rejected malformed JSON input with HTTP 400 Bad Request |
| 11 | **Database Failure Resilience** | ✅ PASSED | In-memory / JSON fallback successfully served 25 records when MongoDB is offline |
| 12 | **Missing Knowledge Source** | ✅ PASSED | Returned 404 Not Found for non-cataloged standard identifier |
| 13 | **Low-Confidence Prediction** | ✅ PASSED | Under-threshold query blocked with strict fallback and 0% confidence score |
| 14 | **API Errors** | ✅ PASSED | Structured error payloads verified: 404 Not Found and 401 Unauthorized |

---

## 5. Architectural Compliance & Strict Guardrails Summary

1. **Never Invent Standard Numbers:** Queries with unverified technical evidence strictly fall back to *'I could not find sufficient authoritative BIS information to answer this question reliably.'*
2. **Evidence-Grounded Citations:** All approved responses provide Authoritative Source URL, Reference Document, Clause/Section, and Confidence percentage.
3. **Multilingual Entity Protection:** Standard numbers (`IS 4151:2020`, `IS 14543:2016`), Karat grades (`22K916`), and technical codes (`HUID`, `ISI`, `CRS`) remain unmodified and protected across Hindi and Tamil translations.
4. **High Availability & Fault Tolerance:** Database manager operates seamlessly in dual-mode (MongoDB + local in-memory JSON fallback) ensuring zero downtime upon database connection disruptions.