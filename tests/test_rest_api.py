import pytest
from app import create_app
from config import Config

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_api_chat(client):
    """POST /api/chat: Validates source-backed QA."""
    res = client.post("/api/chat", json={"query": "Which standard applies to motorcycle helmets?"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "IS 4151" in data["data"]["relevant_standard"]
    assert "why" in data["data"]
    assert "source" in data["data"]

def test_api_predict_intent(client):
    """POST /api/predict-intent: Validates Voting Ensemble classification."""
    res = client.post("/api/predict-intent", json={"query": "What is HUID in gold?"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["intent"] == "HALLMARKING"
    assert data["data"]["model"] == "Voting Ensemble"
    assert data["data"]["confidence"] > 0.0

def test_api_recommend_standard(client):
    """POST /api/recommend-standard: Validates combined 4-signal scoring engine."""
    res = client.post("/api/recommend-standard", json={"product_description": "I manufacture rechargeable LED emergency lights."})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["count"] == 5
    top = data["data"]["recommendations"][0]
    assert "10322" in top["standard_number"]
    assert "score_breakdown" in top

def test_api_standards_catalog(client):
    """GET /api/standards: Retrieves all standards."""
    res = client.get("/api/standards")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["total"] > 0

def test_api_standard_by_id(client):
    """GET /api/standards/<standard_id>: Retrieves single standard."""
    res = client.get("/api/standards/BIS-STD-003")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "4151" in data["data"]["standard_code"]

def test_api_certification(client):
    """GET /api/certification: Retrieves certification schemes."""
    res = client.get("/api/certification")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["total"] > 0

def test_api_hallmarking(client):
    """GET /api/hallmarking: Retrieves hallmarking info."""
    res = client.get("/api/hallmarking")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "key_requirements" in data["data"]

def test_api_laboratories(client):
    """GET /api/laboratories: Retrieves laboratory facilities."""
    res = client.get("/api/laboratories")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["total"] > 0

def test_api_consumer(client):
    """GET /api/consumer: Retrieves consumer FAQs and BIS CARE resources."""
    res = client.get("/api/consumer")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["total"] > 0

def test_api_health(client):
    """GET /api/health: Operational health endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] in ["healthy", "success"]

def test_api_admin_unauthorized(client):
    """Admin APIs without authorization return 401."""
    res = client.get("/api/admin/analytics")
    assert res.status_code == 401

    res = client.post("/api/admin/knowledge", json={})
    assert res.status_code == 401

def test_api_admin_analytics_authorized(client):
    """GET /api/admin/analytics with valid key succeeds."""
    headers = {"X-Admin-API-Key": Config.ADMIN_API_KEY}
    res = client.get("/api/admin/analytics", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "total_queries_logged" in data["data"]

def test_api_admin_knowledge_ingestion(client):
    """POST /api/admin/knowledge creates new entry."""
    headers = {"X-Admin-API-Key": Config.ADMIN_API_KEY}
    payload = {
        "title": "Solar Photovoltaic Inverters - Safety Specification",
        "category": "Solar Energy",
        "product": "Grid-connected solar inverters",
        "standard_number": "IS 16221:2016",
        "certification_scheme": "Scheme II (Compulsory Registration Scheme - CRS)"
    }
    res = client.post("/api/admin/knowledge", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["standard_code"] == "IS 16221:2016"

def test_api_chat_multilingual_hindi(client):
    """POST /api/chat: Validates Hindi query translation and entity preservation."""
    query_hi = "पानी की बोतल के लिए कौन सा भारतीय मानक लागू होता है?"
    res = client.post("/api/chat", json={"query": query_hi})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    item = data["data"]
    assert item["original_query"] == query_hi
    assert item["detected_language"] == "hi"
    assert item["answer_language"] == "hi"
    assert "water" in item["processed_query"].lower()
    assert "IS 14543" in item["relevant_standard"]
    # Technical IS number must be preserved
    assert "IS 14543" in item["answer"]

def test_api_chat_multilingual_tamil(client):
    """POST /api/chat: Validates Tamil query translation and entity preservation."""
    query_ta = "தங்க நகைகளுக்கான ஹால்மார்க் விதிகள் என்ன?"
    res = client.post("/api/chat", json={"query": query_ta})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    item = data["data"]
    assert item["original_query"] == query_ta
    assert item["detected_language"] == "ta"
    assert item["answer_language"] == "ta"
    assert "gold" in item["processed_query"].lower() or "hallmarking" in item["processed_query"].lower()
    # Preserves technical HUID or standard
    assert "HUID" in item["answer"] or "IS 1417" in item["relevant_standard"]

def test_api_chat_unsupported_language_fallback(client):
    """POST /api/chat: Validates unsupported language gracefully falls back to English."""
    query_unsupported = "ఏ భారతీయ ప్రమాణం వర్తిస్తుంది?"
    res = client.post("/api/chat", json={"query": query_unsupported})
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    item = data["data"]
    assert item["detected_language"] == "unsupported"
    assert item["answer_language"] == "en"

def test_api_admin_update_knowledge(client):
    """PUT /api/admin/knowledge/<id>: Updates existing record when authorized."""
    # Unauthorized check
    res_unauth = client.put("/api/admin/knowledge/IS 16221:2016", json={"title": "Updated Title"})
    assert res_unauth.status_code == 401

    headers = {"X-Admin-API-Key": Config.ADMIN_API_KEY}
    update_payload = {
        "collection": "standards",
        "title": "Solar Photovoltaic Inverters - Safety Specification (Updated)",
        "mandatory_status": "Mandatory"
    }
    res = client.put("/api/admin/knowledge/IS 16221:2016", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "IS 16221:2016" in data["message"]

def test_api_admin_delete_knowledge(client):
    """DELETE /api/admin/knowledge/<id>: Deletes record when authorized."""
    # Unauthorized check
    res_unauth = client.delete("/api/admin/knowledge/IS 16221:2016?collection=standards")
    assert res_unauth.status_code == 401

    headers = {"X-Admin-API-Key": Config.ADMIN_API_KEY}
    res = client.delete("/api/admin/knowledge/IS 16221:2016?collection=standards", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["deleted_id"] == "IS 16221:2016"

def test_api_admin_rebuild_index(client):
    """POST /api/admin/rebuild-index: Rebuilds search indices when authorized."""
    # Unauthorized check
    res_unauth = client.post("/api/admin/rebuild-index")
    assert res_unauth.status_code == 401

    headers = {"X-Admin-API-Key": Config.ADMIN_API_KEY}
    res = client.post("/api/admin/rebuild-index", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["data"]["standards_indexed"] > 0

def test_api_admin_metrics(client):
    """GET /api/admin/metrics: Retrieves full ML evaluation metrics when authorized."""
    # Unauthorized check
    res_unauth = client.get("/api/admin/metrics")
    assert res_unauth.status_code == 401

    headers = {"X-Admin-API-Key": Config.ADMIN_API_KEY}
    res = client.get("/api/admin/metrics", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "data" in data

def test_api_admin_ingest_endpoint(client):
    """POST /api/admin/ingest: Re-ingests knowledge base and rebuilds index safely."""
    # 1. Missing auth header returns 401
    res_unauth = client.post("/api/admin/ingest")
    assert res_unauth.status_code == 401

    # 2. Invalid auth key returns 403
    res_forbidden = client.post("/api/admin/ingest", headers={"X-Admin-API-Key": "wrong_key_123"})
    assert res_forbidden.status_code == 403

    # 3. Authorized request succeeds
    headers = {"X-Admin-API-Key": Config.ADMIN_API_KEY}
    res = client.post("/api/admin/ingest", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "total_ingested" in data["data"]
    assert data["data"]["total_ingested"] >= 25

def test_standards_provenance_and_schema(client):
    """GET /api/standards: Verifies expanded schema and provenance fields."""
    res = client.get("/api/standards")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    standards = data["data"]["standards"]
    assert len(standards) >= 25
    first = standards[0]
    assert "standard_number" in first or "standard_code" in first
    assert "verification_status" in first
    assert "source_url" in first


