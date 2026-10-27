"""
Comprehensive 14-Scenario Pytest Test Suite for BIS-AI System
Verifies:
1. Intent classification
2. Standard recommendation
3. Certification retrieval
4. Hallmarking queries
5. Laboratory queries
6. Consumer queries
7. Unknown queries
8. Multilingual queries
9. Empty queries
10. Invalid input
11. Database failure
12. Missing knowledge source
13. Low-confidence prediction
14. API errors
"""

import pytest
from app import create_app
from config import Config
from ml.predict_intent import predict_intent
from services.recommendation_engine import recommendation_engine
from services.conversational_assistant import source_backed_assistant
from services.multilingual import MultilingualService
from database.db import db_manager


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# 1. Intent Classification
def test_01_intent_classification():
    """1. Test Intent Classification: Verify ensemble classifications across multiple classes."""
    test_cases = [
        ("Which Indian standard is for motorcycle helmets?", "STANDARD_RECOMMENDATION"),
        ("What is the scope and requirements of IS 14543?", "STANDARD_INFORMATION"),
        ("How do I apply for ISI mark license under Scheme I?", "CERTIFICATION"),
        ("What is HUID in gold jewellery and how to verify purity?", "HALLMARKING"),
        ("Where is the BIS Central Laboratory located in Ghaziabad?", "LABORATORY"),
        ("How can I lodge a consumer grievance on the BIS CARE app?", "CONSUMER"),
    ]
    for query, expected_intent in test_cases:
        pred = predict_intent(query)
        assert pred["intent"] == expected_intent, f"Failed on '{query}': got {pred['intent']}"
        assert pred["confidence"] > 0.0
        assert pred["model"] == "Voting Ensemble"


# 2. Standard Recommendation
def test_02_standard_recommendation():
    """2. Test Standard Recommendation: Verify 4-signal hybrid relevance scoring & explanation."""
    desc = "I manufacture rechargeable LED emergency lights."
    res = recommendation_engine.recommend(desc, top_k=5)
    
    assert len(res["top_standards"]) > 0
    top_match = res["top_standards"][0]
    
    # Check that IS 10322 was matched
    assert "10322" in top_match["standard_number"]
    assert top_match["relevance_score"] > 0.35
    assert "score_breakdown" in top_match
    assert "tfidf_score" in top_match["score_breakdown"]
    assert "semantic_score" in top_match["score_breakdown"]
    assert "keyword_score" in top_match["score_breakdown"]
    assert "category_score" in top_match["score_breakdown"]
    assert "mandatory_status" in top_match["certification_information"] or "mandatory_status" in top_match
    assert len(top_match["recommendation_explanation"]) > 0


# 3. Certification Retrieval
def test_03_certification_retrieval(client):
    """3. Test Certification Retrieval: Verify Scheme I, Scheme II, and MSME concessions."""
    res = client.get("/api/certification")
    assert res.status_code == 200
    data = res.get_json()["data"]
    schemes = data.get("schemes", [])
    
    assert len(schemes) >= 5
    scheme_names = [s.get("scheme_name", "") for s in schemes]
    assert any("Scheme I" in name for name in scheme_names)
    assert any("Scheme II" in name for name in scheme_names)
    
    # Check MSME concessions field
    scheme1 = next(s for s in schemes if "Scheme I" in s.get("scheme_name", ""))
    assert "concessions_msme_startups" in scheme1
    assert "MSME" in scheme1["concessions_msme_startups"] or "Startup" in scheme1["concessions_msme_startups"]


# 4. Hallmarking Queries
def test_04_hallmarking_queries(client):
    """4. Test Hallmarking Queries: Verify 3 mandatory marks, purity fineness, and HUID rules."""
    res = client.get("/api/hallmarking")
    assert res.status_code == 200
    data = res.get_json()["data"]
    
    assert "key_requirements" in data
    reqs_text = " ".join(data["key_requirements"])
    assert "HUID" in reqs_text
    assert "BIS Logo" in reqs_text
    assert "Purity Fineness" in reqs_text

    # Also test via chat assistant
    chat_res = client.post("/api/chat", json={"query": "What is HUID in gold jewellery?"})
    assert chat_res.status_code == 200
    chat_data = chat_res.get_json()["data"]
    assert "HUID" in chat_data["answer"] or "IS 1417" in chat_data["relevant_standard"]


# 5. Laboratory Queries
def test_05_laboratory_queries(client):
    """5. Test Laboratory Queries: Verify testing lab discovery and discipline/city filtering."""
    res = client.get("/api/laboratories?city=Ghaziabad")
    assert res.status_code == 200
    labs = res.get_json()["data"].get("laboratories", [])
    
    assert len(labs) > 0
    central_lab = labs[0]
    assert "Central Laboratory" in central_lab["lab_name"]
    assert "Ghaziabad" in central_lab["city"]
    assert "disciplines" in central_lab
    assert len(central_lab["disciplines"]) > 0


# 6. Consumer Queries
def test_06_consumer_queries(client):
    """6. Test Consumer Queries: Verify consumer help, grievance redressal, and BIS CARE app."""
    res = client.get("/api/consumer")
    assert res.status_code == 200
    data = res.get_json()["data"]
    
    assert "consumer_resources" in data
    assert "verification_tools" in data
    assert "BIS CARE" in data["verification_tools"]["mobile_app"]
    
    # Check grievance topics
    topics = [f.get("topic", "") for f in data["consumer_resources"]]
    assert any("Counterfeit" in t or "Enforcement" in t or "Licence" in t for t in topics)


# 7. Unknown Queries
def test_07_unknown_queries(client):
    """7. Test Unknown Queries: Verify strict guardrail fallback for completely out-of-domain queries."""
    res = client.post("/api/chat", json={"query": "What is the standard for alien spaceship quantum warp drives?"})
    assert res.status_code == 200
    data = res.get_json()["data"]
    
    assert data["confidence_score"] == 0.0
    assert "could not find" in data["answer"].lower()
    assert data["relevant_standard"] == "None"


# 8. Multilingual Queries
def test_08_multilingual_queries(client):
    """8. Test Multilingual Queries: Verify Hindi, Tamil, and unsupported language fallback."""
    # A. Hindi Query
    r_hi = client.post("/api/chat", json={"query": "पानी की बोतल के लिए कौन सा भारतीय मानक लागू होता है?"})
    assert r_hi.status_code == 200
    d_hi = r_hi.get_json()["data"]
    assert d_hi["detected_language"] == "hi"
    assert d_hi["answer_language"] == "hi"
    assert "IS 14543" in d_hi["answer"]

    # B. Tamil Query
    r_ta = client.post("/api/chat", json={"query": "தங்க நகைகளுக்கான ஹால்மார்க் விதிகள் என்ன?"})
    assert r_ta.status_code == 200
    d_ta = r_ta.get_json()["data"]
    assert d_ta["detected_language"] == "ta"
    assert d_ta["answer_language"] == "ta"
    assert "HUID" in d_ta["answer"] or "IS 1417" in d_ta["relevant_standard"]

    # C. Unsupported Language Fallback
    r_un = client.post("/api/chat", json={"query": "ఏ భారతీయ ప్రమాణం వర్తిస్తుంది?"})
    assert r_un.status_code == 200
    d_un = r_un.get_json()["data"]
    assert d_un["detected_language"] == "unsupported"
    assert d_un["answer_language"] == "en"


# 9. Empty Queries
def test_09_empty_queries(client):
    """9. Test Empty Queries: Verify clean validation error without crashing."""
    r_empty = client.post("/api/chat", json={"query": ""})
    assert r_empty.status_code == 400
    assert r_empty.get_json()["status"] == "error"

    r_whitespace = client.post("/api/chat", json={"query": "     "})
    assert r_whitespace.status_code == 400
    assert r_whitespace.get_json()["status"] == "error"


# 10. Invalid Input
def test_10_invalid_input(client):
    """10. Test Invalid Input: Verify malformed payloads, non-string types, and missing fields."""
    r_malformed = client.post("/api/chat", data="not a json string", content_type="application/json")
    assert r_malformed.status_code == 400
    assert r_malformed.get_json()["status"] == "error"

    r_missing_field = client.post("/api/chat", json={"wrong_key": "some text"})
    assert r_missing_field.status_code == 400


# 11. Database Failure
def test_11_database_failure():
    """11. Test Database Failure: Verify resilient in-memory/JSON fallback when MongoDB disconnects."""
    was_connected = db_manager.is_connected
    try:
        # Force offline state
        db_manager.is_connected = False
        memory_standards = db_manager.get_collection_data("standards")
        memory_schemes = db_manager.get_collection_data("schemes")
        
        assert len(memory_standards) > 0, "Failed to load standards from in-memory fallback"
        assert len(memory_schemes) > 0, "Failed to load schemes from in-memory fallback"
    finally:
        # Restore original state
        db_manager.is_connected = was_connected


# 12. Missing Knowledge Source
def test_12_missing_knowledge_source(client):
    """12. Test Missing Knowledge Source: Verify 404 error returned for non-cataloged standard."""
    res = client.get("/api/standards/NON-EXISTENT-STD-99999")
    assert res.status_code == 404
    data = res.get_json()
    assert data["status"] == "error"
    err_msg = data.get("error") or data.get("message") or ""
    assert "not found" in err_msg.lower()


# 13. Low-Confidence Prediction
def test_13_low_confidence_prediction(client):
    """13. Test Low-Confidence Prediction: Verify under-threshold query triggers strict fallback."""
    query = "Which Indian standard applies to Martian spaceship warp coils and teleportation?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    
    # Must invoke strict fallback with 0% confidence
    assert data["confidence_score"] == 0.0
    assert "could not find" in data["answer"].lower()
    assert data["relevant_standard"] == "None"


# 14. API Errors
def test_14_api_errors(client):
    """14. Test API Errors: Verify structured error payloads for 404, 401, and 400."""
    # 404 Not Found
    r_404 = client.get("/api/completely-unknown-route-endpoint")
    assert r_404.status_code == 404
    assert r_404.get_json()["status"] == "error"

    # 401 Unauthorized
    r_401 = client.post("/api/admin/knowledge", json={"title": "Test Standard"})
    assert r_401.status_code == 401
    assert r_401.get_json()["status"] == "error"

    # 400 Bad Request
    r_400 = client.post("/api/recommend-standard", json={})
    assert r_400.status_code == 400
    assert r_400.get_json()["status"] == "error"
