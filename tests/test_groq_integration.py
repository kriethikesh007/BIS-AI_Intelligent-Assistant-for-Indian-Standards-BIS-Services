import pytest
from unittest.mock import MagicMock, patch
from app import create_app
from services.groq_service import GroqService, groq_service
from services.conversational_assistant import SourceBackedAssistant


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_catalog_evidence():
    return {
        "standard_number": "IS 4151",
        "standard_title": "Protective Helmets for Two Wheeler Riders - Specification",
        "product_match": "Protective helmets for two wheeler riders and motorcyclists",
        "scope": "Covers material, construction, workmanship, finish and testing of helmets for two-wheeler riders.",
        "certification_scheme": "Scheme I",
        "mandatory_status": "Mandatory",
        "testing_parameters": "Impact absorption test (Clause 7.1), penetration test (Clause 7.2), retention system strength (Clause 7.3)",
        "page_section_clause": "Clause 5, 7.1, 7.2, 7.3, 8.2",
        "reference_document": "IS 4151:2020 Specification Document",
        "source": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/4151"
    }


def test_1_successful_groq_grounded_response(sample_catalog_evidence):
    """Test successful Groq response using retrieved catalog evidence."""
    service = GroqService()
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "IS 4151 specifies protective helmets for two-wheeler riders under mandatory Scheme I certification."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    with patch.object(service, "_get_client", return_value=mock_client):
        answer = service.generate_grounded_answer(
            query="Which Indian Standard applies to motorcycle helmets?",
            catalog_evidence=sample_catalog_evidence,
            target_language="en"
        )
        assert answer is not None
        assert "IS 4151" in answer
        assert "helmets" in answer.lower()
        mock_client.chat.completions.create.assert_called_once()
        # Verify model name used
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == service.model


def test_2_missing_api_key_safe_fallback(sample_catalog_evidence):
    """Test that when API key is missing or blank, service gracefully returns None without crashing."""
    service = GroqService()
    service.api_key = ""
    with patch.dict("os.environ", {"GROQ_API_KEY": ""}):
        assert service.is_available() is False
        assert service._get_client() is None
        answer = service.generate_grounded_answer(
            query="What is the helmet standard?",
            catalog_evidence=sample_catalog_evidence
        )
        assert answer is None


def test_3_invalid_credentials_upstream_auth_failure(sample_catalog_evidence):
    """Test handling of 401 Authentication failure from Groq upstream."""
    service = GroqService()
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized: Invalid API Key")

    with patch.object(service, "_get_client", return_value=mock_client):
        answer = service.generate_grounded_answer(
            query="Helmet standard",
            catalog_evidence=sample_catalog_evidence
        )
        # Must catch exception and safely return None without throwing or leaking key
        assert answer is None


def test_4_http_429_rate_limit_resilience(sample_catalog_evidence):
    """Test handling of HTTP 429 rate limit without crashing."""
    service = GroqService()
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("429 Too Many Requests: Rate limit reached")

    with patch.object(service, "_get_client", return_value=mock_client):
        answer = service.generate_grounded_answer(
            query="Helmet standard",
            catalog_evidence=sample_catalog_evidence
        )
        assert answer is None


def test_5_timeout_and_temporary_api_failure(sample_catalog_evidence):
    """Test handling of network timeouts and transient connection errors."""
    service = GroqService()
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = TimeoutError("Request timed out after 15.0s")

    with patch.object(service, "_get_client", return_value=mock_client):
        answer = service.generate_grounded_answer(
            query="Helmet standard",
            catalog_evidence=sample_catalog_evidence
        )
        assert answer is None


def test_6_empty_model_response(sample_catalog_evidence):
    """Test handling when model returns an empty string or empty choices."""
    service = GroqService()
    mock_client = MagicMock()
    # Empty choices
    mock_client.chat.completions.create.return_value = MagicMock(choices=[])
    with patch.object(service, "_get_client", return_value=mock_client):
        assert service.generate_grounded_answer("query", sample_catalog_evidence) is None

    # Empty content string
    mock_choice = MagicMock()
    mock_choice.message.content = "   "
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    with patch.object(service, "_get_client", return_value=mock_client):
        assert service.generate_grounded_answer("query", sample_catalog_evidence) is None


def test_7_unknown_fictitious_product_abstention(client):
    """Test safe abstention for unknown or fictitious products."""
    query = "What is the BIS standard for quantum teleportation device?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["relevant_standard"] == "None"
    assert data["ai_generated"] is False
    assert data["verification_status"] == "Unverified / Non-cataloged"
    assert "could not find sufficient authoritative bis information" in data["answer"].lower()


def test_8_unsupported_clause_handling(client):
    """Test that querying an uncataloged clause sets proper verification and warning."""
    query = "What does Clause 99 of IS 4151 state?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "IS 4151" in data["relevant_standard"]
    assert data["clause_verification"] == "Unverified - Requested Clause Not Cataloged"
    # Both template and Groq mention Clause 99 and not cataloged / not indexed
    assert "clause 99" in data["answer"].lower() or "clause\u202f99" in data["answer"].lower()
    assert ("not contain verified text" in data["answer"].lower() or 
            "not indexed" in data["answer"].lower() or 
            "uncataloged" in data["reference"].lower())


def test_9_correctly_cataloged_clause(client):
    """Test that querying a cataloged clause verifies correctly."""
    query = "Does Clause 7.1 of IS 4151 specify impact absorption test?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "IS 4151" in data["relevant_standard"]
    assert data["clause_verification"] == "Verified Clause Citation from Catalog Record"
    assert "7.1" in data["reference"]


def test_10_english_response_via_chat(client):
    """Test English response generation through /api/chat."""
    query = "Which Indian Standard specifies requirements for two wheeler helmets?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "en"
    assert data["answer_language"] == "en"
    assert "IS 4151" in data["relevant_standard"]


def test_11_hindi_response_via_chat(client):
    """Test Hindi response generation through /api/chat."""
    query = "IS 4151 किस उत्पाद से संबंधित है?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "hi"
    assert data["answer_language"] == "hi"
    assert "4151" in data["relevant_standard"]
    # Devanagari Hindi content present
    assert any('\u0900' <= c <= '\u097F' for c in data["answer"])


def test_12_tamil_response_via_chat(client):
    """Test Tamil response generation through /api/chat."""
    query = "IS 4151 எந்தப் பொருளுக்கான தரநிலை?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "ta"
    assert data["answer_language"] == "ta"
    assert "4151" in data["relevant_standard"]
    # Tamil script content present
    assert any('\u0B80' <= c <= '\u0BFF' for c in data["answer"])


def test_13_hinglish_response_via_chat(client):
    """Test Hinglish colloquial query response via /api/chat."""
    query = "Bhai helmet ka standard bata do"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "hi"
    assert data["answer_language"] == "hi"
    assert "IS 4151" in data["relevant_standard"]


def test_14_tanglish_response_via_chat(client):
    """Test Tanglish colloquial query response via /api/chat."""
    query = "helmet-ku enna standard sollunga"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "ta"
    assert data["answer_language"] == "ta"
    assert "IS 4151" in data["relevant_standard"]


def test_15_url_safety_and_evidence_labels(client):
    """Test URL safety, protocol validation, and separate evidence labels."""
    query = "IS 4151"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["source"].startswith("http://") or data["source"].startswith("https://")
    assert " " not in data["source"]
    assert data["match_type"] == "Exact Standard Identifier Match"
    assert data["verification_status"] == "Corroborated by Catalog Standard Record"
    # Raw retrieval score preserved separately
    assert "retrieval_relevance" in data
    assert "classifier_confidence" in data


def test_16_existing_flask_endpoints_and_json_fallback(client):
    """Test existing REST endpoints and JSON database fallback readiness."""
    # Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.get_json()["status"] == "healthy"

    # Standards catalog
    res_cat = client.get("/api/standards")
    assert res_cat.status_code == 200
    assert res_cat.get_json()["data"]["total"] > 0

    # Scheme
    res_cert = client.get("/api/certification")
    assert res_cert.status_code == 200

    # Hallmarking
    res_hall = client.get("/api/hallmarking")
    assert res_hall.status_code == 200

    # Laboratories
    res_lab = client.get("/api/laboratories")
    assert res_lab.status_code == 200

    # Consumer
    res_cons = client.get("/api/consumer")
    assert res_cons.status_code == 200


def test_17_exact_tamil_helmet_query_retrieval(client):
    """
    Issue 1: Exact Tamil query: 'பாதுகாப்பு தலைக்கவசத்திற்கான தரநிலை என்ன?'
    Must correctly normalize and retrieve IS 4151:2020 and respond in Tamil.
    """
    query_ta = "பாதுகாப்பு தலைக்கவசத்திற்கான தரநிலை என்ன?"
    res = client.post("/api/chat", json={"query": query_ta})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "ta"
    assert data["answer_language"] == "ta"
    assert "IS 4151" in data["relevant_standard"]
    assert data["retrieval_relevance"] > 0.35
    assert data["verification_status"] == "Corroborated by Catalog Product Scope"
    # Tamil script content present in answer
    assert any('\u0B80' <= c <= '\u0BFF' for c in data["answer"])


def test_18_english_two_wheeler_helmet_query_retrieval(client):
    """
    Issue 1 comparison: 'Which standard applies to a two-wheeler helmet?'
    Must correctly match IS 4151 and mandatory Scheme I.
    """
    query_en = "Which standard applies to a two-wheeler helmet?"
    res = client.post("/api/chat", json={"query": query_en})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "en"
    assert data["answer_language"] == "en"
    assert "IS 4151" in data["relevant_standard"]
    assert data["retrieval_relevance"] > 0.35
    assert data["match_type"] == "Product Specification Match"


def test_19_evidence_corroboration_distinct_from_legal_claim(client):
    """
    Issue 2: Verification of claims against catalog records.
    Mandatory status is corroborated by catalog record for IS 4151 (QCO Scheme I).
    """
    query = "IS 4151:2020 mandatory status"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "IS 4151" in data["relevant_standard"]
    assert data["verification_status"] in ["Corroborated by Catalog Standard Record", "Corroborated by Catalog Product Scope"]
    assert "Mandatory" in data["answer"]


def test_20_url_sanitizer_html_entity_and_trailing_space():
    """
    Issue 3: URL sanitizer corrects &#x20;, trailing spaces, and preserves %20 in legitimate URLs.
    """
    from utils.url_validator import sanitize_and_validate_url

    # Trailing encoded entity space
    url_entity = "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/4151&#x20;"
    clean_entity = sanitize_and_validate_url(url_entity)
    assert not clean_entity.endswith(" ")
    assert "&#x20;" not in clean_entity
    assert clean_entity == "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/4151"

    # Legitimate percent-encoded internal space
    url_legit = "https://www.services.bis.gov.in/php/BIS_2.0/know%20your%20standards/4151"
    clean_legit = sanitize_and_validate_url(url_legit)
    assert clean_legit == url_legit
    assert "%20" in clean_legit

    # Unsafe schemes
    assert sanitize_and_validate_url("javascript:void(0)") == "https://www.services.bis.gov.in"
    assert sanitize_and_validate_url("data:text/html;base64,PHNjcmlwdD4=") == "https://www.services.bis.gov.in"


def test_21_groq_execution_status_flag(client):
    """
    Issue 4: ai_generated flag is strictly True only when Groq returned accepted text,
    and False during automated tests or fallback.
    """
    res = client.post("/api/chat", json={"query": "Which standard applies to motorcycle helmets?"})
    assert res.status_code == 200
    data = res.get_json()["data"]
    # During automated testing, outbound Groq is disabled via test guardrail
    assert data["ai_generated"] is False

