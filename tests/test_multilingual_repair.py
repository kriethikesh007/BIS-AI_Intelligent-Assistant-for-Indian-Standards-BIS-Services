import pytest
from app import create_app
from services.conversational_assistant import source_backed_assistant, FALLBACK_STRICT_MESSAGE

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_query_1_english_is4151(client):
    query = "What is IS 4151 and which product does it cover?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "4151" in data["relevant_standard"]
    assert "Helmets" in data["relevant_standard"] or "helmet" in data["answer"].lower()
    assert data["source"] is not None
    assert data["reference"] is not None

def test_query_2_hindi_is4151(client):
    query = "IS 4151 किस उत्पाद से संबंधित है?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "hi"
    assert data["answer_language"] == "hi"
    assert "4151" in data["relevant_standard"]
    # Protected code preserved
    assert "IS 4151" in data["answer"]
    # Body translated to Hindi
    assert "हेलमेट" in data["answer"] or "दोपहिया" in data["answer"]

def test_query_3_tamil_is4151(client):
    query = "IS 4151 எந்தப் பொருளுக்கான தரநிலை?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "ta"
    assert data["answer_language"] == "ta"
    assert "4151" in data["relevant_standard"]
    # Protected code preserved
    assert "IS 4151" in data["answer"]
    # Body translated to Tamil
    assert "தலைக்கவசம்" in data["answer"] or "வாகன" in data["answer"]

def test_query_4_hinglish_helmet(client):
    query = "Helmet ke liye applicable BIS standard kya hai?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "4151" in data["relevant_standard"]
    assert "helmet" in data["processed_query"].lower()
    # Separated raw retrieval relevance (uninflated) and classifier confidence
    assert data["retrieval_relevance"] > 0.35
    assert data["classifier_confidence"] >= 0.85
    assert data["intent"] == "STANDARD_RECOMMENDATION"
    assert "https://" in data["source"] and not data["source"].endswith(" ")
    assert data["match_type"] == "Product Specification Match"
    assert data["verification_status"] == "Corroborated by Catalog Product Scope"
    assert data["clause_verification"] == "Verified Clause Citation from Catalog Record"

def test_query_4b_hinglish_helmet_batao(client):
    query = "Helmet ka BIS standard batao"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "4151" in data["relevant_standard"]
    assert data["retrieval_relevance"] > 0.35
    assert data["classifier_confidence"] >= 0.85
    assert data["intent"] == "STANDARD_RECOMMENDATION"
    assert data["verification_status"] == "Corroborated by Catalog Product Scope"

def test_query_5_tanglish_helmet(client):
    query = "Helmet-ku applicable BIS standard enna?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "4151" in data["relevant_standard"]
    assert "helmet" in data["processed_query"].lower()
    assert data["retrieval_relevance"] > 0.35
    assert data["classifier_confidence"] >= 0.85
    assert data["intent"] == "STANDARD_RECOMMENDATION"
    assert "https://" in data["source"] and not data["source"].endswith(" ")
    assert data["match_type"] == "Product Specification Match"
    assert data["verification_status"] == "Corroborated by Catalog Product Scope"

def test_query_5b_tanglish_helmet_enna(client):
    query = "Helmet standard enna?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "4151" in data["relevant_standard"]
    assert data["retrieval_relevance"] > 0.35
    assert data["classifier_confidence"] >= 0.85
    assert data["intent"] == "STANDARD_RECOMMENDATION"
    assert data["verification_status"] == "Corroborated by Catalog Product Scope"

def test_query_2b_hinglish_is4151(client):
    query = "IS 4151 kis product ke liye hai?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["intent"] == "STANDARD_INFORMATION"
    assert "4151" in data["relevant_standard"]
    assert "IS 4151" in data["answer"]
    assert data["retrieval_relevance"] >= 0.95
    assert data["match_type"] == "Exact Standard Identifier Match"
    assert data["verification_status"] == "Corroborated by Catalog Standard Record"

def test_query_3b_tamil_is4151_etharkana(client):
    query = "IS 4151 எதற்கான standard?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["intent"] == "STANDARD_INFORMATION"
    assert "4151" in data["relevant_standard"]
    assert "IS 4151" in data["answer"]
    assert data["retrieval_relevance"] >= 0.95
    assert data["match_type"] == "Exact Standard Identifier Match"
    assert data["verification_status"] == "Corroborated by Catalog Standard Record"

def test_query_6_english_certification_apply(client):
    query = "How can a manufacturer apply for BIS certification?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "Scheme" in data["relevant_standard"] or "Certification" in data["relevant_standard"]
    assert "Manakonline" in data["answer"] or "application" in data["answer"].lower()

def test_query_7_tamil_certification_apply(client):
    query = "ஒரு உற்பத்தியாளர் BIS சான்றிதழுக்கு எப்படி விண்ணப்பிக்கலாம்?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "ta"
    assert "திட்டம்" in data["answer"] or "சான்றிதழ்" in data["answer"] or "விண்ணப்ப" in data["answer"]

def test_query_8_english_huid_verify(client):
    query = "What is HUID and how can a consumer verify it?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "HUID" in data["answer"]
    assert "6-digit" in data["answer"]
    assert "BIS CARE" in data["answer"]

def test_query_9_tamil_huid_verify(client):
    query = "HUID என்றால் என்ன? அதை எப்படி சரிபார்ப்பது?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["detected_language"] == "ta"
    assert "HUID" in data["answer"]
    assert "ஹால்மார்க்" in data["answer"] or "காரட்" in data["answer"] or "BIS CARE" in data["answer"]

def test_query_10_english_counterfeit_report(client):
    query = "How can I report a suspected counterfeit BIS mark?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "BIS CARE" in data["answer"]
    assert "complaint" in data["answer"].lower() or "cml" in data["answer"].lower()

def test_query_11_out_of_domain_abstention(client):
    query = "Give me an official BIS clause that does not exist in the knowledge base."
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert FALLBACK_STRICT_MESSAGE in data["answer"]
    assert data["relevant_standard"] == "None"
    assert data["confidence"] == "0%"
    assert data["verification_status"] == "Unverified / Non-cataloged"
    assert data["clause_verification"] == "Unverified / No Citation Available"

def test_query_12_weak_match_behavior(client):
    # Weak match: decorative item with no specific BIS QCO in catalog
    query = "Which Indian Standard specifies requirements for decorative ceramic flower vases?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    # Either triggers strict fallback or marks evidence as unverified/weak
    if data["relevant_standard"] == "None":
        assert data["verification_status"] == "Unverified / Non-cataloged"
    else:
        assert data["verification_status"] in ["Unverified - Weak Retrieval Evidence", "Tentative Domain Association"]

def test_query_13_unrelated_query_astronomy_abstention(client):
    # Completely unrelated domain query
    query = "What is the orbital speed of the planet Jupiter around the Sun?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["relevant_standard"] == "None"
    assert data["confidence"] == "0%"
    assert data["confidence_score"] == 0.0
    assert data["verification_status"] == "Unverified / Non-cataloged"

def test_query_14_url_sanitization_and_preservation(client):
    from utils.url_validator import sanitize_and_validate_url, is_valid_url

    # 1. Preserves legitimate percent-encoding (%20)
    url_with_encoded_space = "https://www.services.bis.gov.in/php/BIS_2.0/know%20your%20standards/4151"
    clean_encoded = sanitize_and_validate_url(url_with_encoded_space)
    assert clean_encoded == url_with_encoded_space
    assert "%20" in clean_encoded

    # 2. Trims trailing whitespace
    url_trailing_space = "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/4151   "
    clean_trailing = sanitize_and_validate_url(url_trailing_space)
    assert not clean_trailing.endswith(" ")
    assert clean_trailing == "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/4151"

    # 3. Converts unescaped internal spaces to valid %20
    url_raw_space = "https://www.services.bis.gov.in/php/know your standards"
    clean_raw_space = sanitize_and_validate_url(url_raw_space)
    assert " " not in clean_raw_space
    assert "know%20your%20standards" in clean_raw_space

    # 4. Rejects malformed and non-HTTP protocols safely
    assert sanitize_and_validate_url("javascript:alert(1)") == "https://www.services.bis.gov.in"
    assert sanitize_and_validate_url("ftp://example.com/doc") == "https://www.services.bis.gov.in"
    assert is_valid_url("https://www.bis.gov.in") is True
    assert is_valid_url("not_a_valid_url") is False

def test_query_specific_clause_verification_cataloged(client):
    # Clause 7.1 is present in catalog for IS 4151
    query = "Does Clause 7.1 of IS 4151 specify impact absorption test?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "IS 4151" in data["relevant_standard"]
    assert data["clause_verification"] == "Verified Clause Citation from Catalog Record"
    assert "7.1" in data["reference"]

def test_query_specific_clause_verification_uncataloged(client):
    # Clause 19 is NOT present in catalog for IS 4151
    query = "What does Clause 19 of IS 4151 state regarding flame retardancy?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "IS 4151" in data["relevant_standard"]
    assert data["clause_verification"] == "Unverified - Requested Clause Not Cataloged"
    assert "Requested Clause 19 uncataloged" in data["reference"]
    assert "Note on Requested Reference" in data["answer"]
    assert "does not contain verified text for Clause 19" in data["answer"]

def test_query_specific_clause_verification_decimal(client):
    # Decimal clause 4.1 in IS 14543
    query = "Does Clause 4.1 of IS 14543 specify requirements for packaged drinking water?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "IS 14543" in data["relevant_standard"]
    assert data["clause_verification"] == "Verified Clause Citation from Catalog Record"
    assert "4.1" in data["reference"]

def test_query_no_clause_specified(client):
    # General standard query without mentioning any clause
    query = "Which Indian Standard applies to protective helmets for two wheelers?"
    res = client.post("/api/chat", json={"query": query})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "IS 4151" in data["relevant_standard"]
    assert data["clause_verification"] == "Verified Clause Citation from Catalog Record"
    assert "Note on Requested Reference" not in data["answer"]

def test_colloquial_hinglish_detection_and_response(client):
    queries = [
        "Bhai helmet ka standard bata do",
        "helmet ka standard bataiye",
        "IS 4151 ke baare mein batao"
    ]
    for q in queries:
        res = client.post("/api/chat", json={"query": q})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["detected_language"] == "hi", f"Expected 'hi' for query '{q}', got {data['detected_language']}"
        assert data["answer_language"] == "hi", f"Expected 'hi' answer for query '{q}', got {data['answer_language']}"
        assert "IS 4151" in data["relevant_standard"]

def test_language_detection_integrity():
    from services.multilingual import MultilingualService
    # Ordinary English must remain English
    assert MultilingualService.detect_language("What is the standard for packaged drinking water?") == "en"
    assert MultilingualService.detect_language("Which Indian Standard applies to motorcycle helmets?") == "en"

    # Colloquial Hinglish
    assert MultilingualService.detect_language("Bhai helmet ka standard bata do") == "hi"
    assert MultilingualService.detect_language("helmet ka standard bataiye") == "hi"
    assert MultilingualService.detect_language("IS 4151 ke baare mein batao") == "hi"

    # Standard Hindi (Devanagari)
    assert MultilingualService.detect_language("दोपहिया वाहन हेलमेट के लिए कौन सा भारतीय मानक लागू होता है?") == "hi"

    # Tamil (Tamil script)
    assert MultilingualService.detect_language("ஹெல்மெட்டுக்கான இந்திய தரம் என்ன?") == "ta"

    # Tanglish
    assert MultilingualService.detect_language("helmet-ku enna standard sollunga") == "ta"


