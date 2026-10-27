import pytest
from unittest.mock import MagicMock, patch
from app import create_app
from services.grok_service import grok_service, GrokService
from services.conversational_assistant import source_backed_assistant


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestRegressionSuite:
    """
    Comprehensive Regression Test Suite covering all 10 evaluation categories:
    1. General BIS Concepts
    2. Certification Schemes
    3. Hallmarking & HUID
    4. Standard Recommendation
    5. Laboratory Directory
    6. Consumer Rights & Grievance
    7. Multi-Turn Follow-up Questions
    8. Ambiguous Product Descriptions
    9. Evidence-Sensitive Questions
    10. Out-of-Domain Guardrails
    """

    # Category 1: General BIS
    def test_general_bis_what_is_bis(self, client):
        """General questions like 'What is BIS?' must not be rejected with insufficient data."""
        res = client.post("/api/chat", json={"query": "What is BIS?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "could not find sufficient" not in data["answer"].lower()
        assert "bureau of indian standards" in data["answer"].lower() or "national standard body" in data["answer"].lower()
        assert data["relevant_standard"] != "None"

    def test_general_bis_purpose_of_indian_standards(self, client):
        res = client.post("/api/chat", json={"query": "What is the purpose of Indian Standards?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "quality" in data["answer"].lower() or "safety" in data["answer"].lower()

    def test_general_bis_conformity_assessment(self, client):
        res = client.post("/api/chat", json={"query": "Explain the general purpose of conformity assessment."})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "conformity" in data["answer"].lower()

    # Category 2: Certification
    def test_certification_process(self, client):
        res = client.post("/api/chat", json={"query": "Explain the BIS certification process."})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "application" in data["answer"].lower() or "testing" in data["answer"].lower() or "manakonline" in data["answer"].lower()

    def test_certification_isi_mark(self, client):
        res = client.post("/api/chat", json={"query": "What is the difference between an ISI mark and hallmarking?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "isi" in data["answer"].lower()
        assert "hallmarking" in data["answer"].lower()

    def test_certification_mandatory_vs_voluntary(self, client):
        res = client.post("/api/chat", json={"query": "What is the difference between a mandatory and a voluntary certification scheme?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "mandatory" in data["answer"].lower()
        assert "voluntary" in data["answer"].lower()

    # Category 3: Hallmarking
    def test_hallmarking_gold(self, client):
        res = client.post("/api/chat", json={"query": "How does gold hallmarking work?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "huid" in data["answer"].lower() or "purity" in data["answer"].lower() or "gold" in data["answer"].lower()

    def test_hallmarking_consumer_verification(self, client):
        res = client.post("/api/chat", json={"query": "How can a consumer verify hallmark information?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "bis care" in data["answer"].lower() or "huid" in data["answer"].lower()

    # Category 4: Standard Recommendation
    def test_standard_led_emergency_light(self, client):
        res = client.post("/api/chat", json={"query": "My product is an LED emergency light. How can I identify the relevant Indian Standard?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "10322" in data["answer"] or "10322" in str(data.get("relevant_standard"))

    def test_standard_pressure_cooker_details_needed(self, client):
        res = client.post("/api/chat", json={"query": "What details do you need to identify the standard for a pressure cooker?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "material" in data["answer"].lower() or "specification" in data["answer"].lower() or "standard" in data["answer"].lower()

    # Category 5: Laboratory
    def test_laboratory_find(self, client):
        res = client.post("/api/chat", json={"query": "How can I find a laboratory for product testing?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "laboratory" in data["answer"].lower() or "lims" in data["answer"].lower() or "nabl" in data["answer"].lower()

    def test_laboratory_info_needed(self, client):
        res = client.post("/api/chat", json={"query": "What information is needed before recommending a testing laboratory?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "product" in data["answer"].lower() or "test" in data["answer"].lower()

    # Category 6: Consumer
    def test_consumer_fake_mark_report(self, client):
        res = client.post("/api/chat", json={"query": "What should I do if a product appears to carry a fake BIS mark?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "bis care" in data["answer"].lower() or "complaint" in data["answer"].lower() or "section" in data["answer"].lower()

    def test_consumer_raise_complaint(self, client):
        res = client.post("/api/chat", json={"query": "How do I raise a consumer complaint related to a product or certification?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "complaint" in data["answer"].lower() or "bis care" in data["answer"].lower()

    # Category 7: Follow-up Questions with History
    def test_follow_up_conversation_history(self, client):
        history = [
            {"role": "user", "content": "What is BIS certification?"},
            {"role": "assistant", "content": "BIS certification grants manufacturers a licence to use the standard ISI mark."}
        ]
        res = client.post("/api/chat", json={
            "query": "How do I apply for it?",
            "history": history
        })
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "manakonline" in data["answer"].lower() or "apply" in data["answer"].lower() or "application" in data["answer"].lower()

    # Category 8: Ambiguous Product Description
    def test_ambiguous_electrical_products(self, client):
        res = client.post("/api/chat", json={"query": "My company manufactures electrical products. Which standard applies?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        # Must not return generic failure
        assert "could not find sufficient" not in data["answer"].lower()
        # Explains different categories (appliances, cables, IT) and asks for specific product
        assert "is 302" in data["answer"].lower() or "is 694" in data["answer"].lower() or "specify" in data["answer"].lower() or "clarify" in data["answer"].lower()

    # Category 9: Evidence-Sensitive Questions
    def test_evidence_sensitive_current_fee_disclaimer(self, client):
        res = client.post("/api/chat", json={"query": "What is the exact current certification fee for my product?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        # Must point to official Manakonline portal rather than fabricating a fee
        assert "manakonline" in data["answer"].lower() or "portal" in data["answer"].lower() or "fee" in data["answer"].lower()

    def test_evidence_sensitive_compulsory_status(self, client):
        res = client.post("/api/chat", json={"query": "How can I determine whether a specific product is covered by compulsory certification?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert "insufficient data" not in data["answer"].lower()
        assert "qco" in data["answer"].lower() or "compulsory" in data["answer"].lower() or "crs" in data["answer"].lower()

    # Category 10: Out-of-Domain Safety Abstention
    def test_out_of_domain_unrelated_concept(self, client):
        res = client.post("/api/chat", json={"query": "What is the BIS standard for quantum teleportation device?"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["relevant_standard"] == "None"
        assert "could not find sufficient authoritative bis information" in data["answer"].lower()

    # Grok Mocked Generation Verification
    def test_grok_called_when_available(self):
        service = GrokService()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Grok AI: BIS stands for Bureau of Indian Standards, established under the BIS Act 2016."
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        with patch.object(service, "_get_client", return_value=mock_client), \
             patch.object(service, "is_available", return_value=True):
            answer = service.generate_answer(
                query="What is BIS?",
                intent="GENERAL_BIS"
            )
            assert answer is not None
            assert "Bureau of Indian Standards" in answer
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == service.model

    def test_wired_mouse_product_inquiry(self, client):
        """Verify that a short uncataloged product query like 'wired mouse' is classified as STANDARD_RECOMMENDATION and receives structured guidance rather than generic insufficient-data failure."""
        res = client.post("/api/chat", json={"query": "wired mouse"})
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["intent"] == "STANDARD_RECOMMENDATION"
        assert "insufficient data" not in data["answer"].lower()
        assert "could not find sufficient authoritative bis information" not in data["answer"].lower()
        assert "manakonline" in data["answer"].lower() or "scheme" in data["answer"].lower() or "peripheral" in data["answer"].lower()
        assert data["relevant_standard"] != "None"

    def test_wired_mouse_grok_call_when_available(self):
        """Verify that Grok is invoked for wired mouse when available, with STANDARD_RECOMMENDATION intent and zero hallucination guidance."""
        service = GrokService()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Grok AI: A wired computer mouse is an IT peripheral. Certification under Scheme I is voluntary. Verify at Manakonline."
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        with patch.object(service, "_get_client", return_value=mock_client), \
             patch.object(service, "is_available", return_value=True):
            answer = service.generate_answer(
                query="wired mouse",
                intent="STANDARD_RECOMMENDATION"
            )
            assert answer is not None
            assert "Manakonline" in answer
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == service.model
