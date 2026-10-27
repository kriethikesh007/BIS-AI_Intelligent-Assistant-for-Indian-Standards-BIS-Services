import pytest
from pathlib import Path
import sys

# Ensure root in path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app
from services.multilingual import MultilingualService
from ml.classifier_service import intent_classifier
from retrieval.retriever import retriever
from services.assistant import orchestrator, FALLBACK_MESSAGE
from database.db import db_manager

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_database_and_seed():
    """Verify database collections load properly."""
    status = db_manager.get_status()
    assert status["standards_count"] > 0
    assert status["schemes_count"] > 0
    assert status["laboratories_count"] > 0
    assert status["faqs_count"] > 0

def test_multilingual_language_detection():
    """Verify English, Hindi, and Tamil script detection."""
    assert MultilingualService.detect_language("Which standard is for helmets?") == "en"
    assert MultilingualService.detect_language("पानी की बोतल के लिए मानक क्या है?") == "hi"
    assert MultilingualService.detect_language("தங்க நகைகளுக்கான தரம் என்ன?") == "ta"

def test_multilingual_normalization():
    """Verify multilingual normalization extracts domain English words."""
    res_hi = MultilingualService.process_query("पानी की बोतल मानक")
    assert res_hi["detected_language"] == "hi"
    assert "water" in res_hi["normalized_query"] or "standard" in res_hi["normalized_query"]

def test_ensemble_intent_classifier():
    """Verify ensemble intent classifier returns recognized classes with probabilities."""
    intent, conf, all_probs = intent_classifier.predict("Which Indian standard applies to packaged drinking water?")
    assert intent in ["STANDARD_RECOMMENDATION", "STANDARD_INFORMATION"]
    assert conf > 0.0
    assert isinstance(all_probs, dict)

def test_retriever_standard_recommendation():
    """Verify hybrid retriever recommends IS 4151 for motorcycle helmets."""
    results = retriever.search_and_recommend("two wheeler motorcycle helmets", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "4151" in top["standard_code"]
    assert top["relevance_score"] >= 0.35
    assert "Impact absorption" in top["testing_parameters"]

def test_retriever_packaged_water():
    """Verify recommendation for packaged drinking water."""
    results = retriever.search_and_recommend("packaged drinking water bottle", top_k=3)
    assert len(results) > 0
    codes = [r["standard_code"] for r in results]
    assert any("14543" in c for c in codes)

def test_assistant_source_backed_answering():
    """Verify source-backed answer structure contains source document, URL, and clause."""
    resp = orchestrator.process_user_query("What standard is for motorcycle helmets?")
    assert "IS 4151" in resp["recommended_standard"]
    assert resp["source"] is not None
    assert "IS 4151" in resp["reference_document"]
    assert resp["page_section_clause"] is not None
    assert resp["confidence_score"] > 0.0

def test_hallmarking_and_huid_query():
    """Verify gold hallmarking and HUID query returns official guidelines."""
    resp = orchestrator.process_user_query("What is HUID in gold jewellery?")
    assert "HUID" in resp["answer"]
    assert "IS 1417" in resp["recommended_standard"] or "HUID" in resp["reason"]
    assert resp["source"] is not None

def test_fallback_guardrail_unsupported_query():
    """Verify system does not invent standards when no evidence is found."""
    resp = orchestrator.process_user_query("What is the standard for alien spaceship warp engines in Mars?")
    assert resp["answer"] == FALLBACK_MESSAGE
    assert resp["recommended_standard"] is None

def test_api_health_endpoint(client):
    """Verify API health endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"]["standards_count"] > 0

def test_api_query_endpoint(client):
    """Verify POST /api/query endpoint."""
    payload = {"query": "Which standard applies to electric plugs and sockets?"}
    res = client.post("/api/query", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "IS 1293" in data["data"]["recommended_standard"]

def test_api_metrics_endpoint(client):
    """Verify /api/metrics returns confusion matrix and evaluation data."""
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.get_json()
    assert "metrics" in data
    assert "confusion_matrix" in data["metrics"]
    assert "ensemble_accuracy" in data["metrics"]

def test_multilingual_entity_preservation():
    """Verify standard numbers, IS numbers, and technical codes are never corrupted in translation."""
    eng_text = "The applicable standard is IS 4151:2020 for helmets with HUID on BIS CARE under Scheme I (ISI Mark)."
    hi_trans = MultilingualService.translate_answer(eng_text, "hi")
    ta_trans = MultilingualService.translate_answer(eng_text, "ta")

    # Strict preservation checks
    for code in ["IS 4151:2020", "HUID", "BIS CARE", "ISI Mark"]:
        assert code in hi_trans, f"{code} missing in Hindi translation"
        assert code in ta_trans, f"{code} missing in Tamil translation"

def test_multilingual_unsupported_language_fallback():
    """Verify unsupported scripts fall back gracefully to English."""
    query = "ఏ భారతీయ ప్రమాణం వర్తిస్తుంది?"
    assert MultilingualService.detect_language(query) == "unsupported"
    proc = MultilingualService.process_query(query)
    assert proc["detected_language"] == "unsupported"
    assert proc["answer_language"] == "en"
