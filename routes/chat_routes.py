import logging
from flask import Blueprint, request
from utils.response import api_response, api_error
from services.conversational_assistant import source_backed_assistant
from services.recommendation_engine import recommendation_engine
from ml.predict_intent import predict_intent

chat_bp = Blueprint("chat", __name__, url_prefix="/api")
logger = logging.getLogger("bis_ai.routes.chat")

@chat_bp.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    POST /api/chat
    Main conversational QA endpoint adhering to the 8-step source-backed workflow.
    """
    body = request.get_json(silent=True)
    if not body or not isinstance(body, dict):
        return api_error("Invalid JSON body", status_code=400)

    query = body.get("query", "").strip() or body.get("message", "").strip()
    if not query:
        return api_error("Field 'query' or 'message' is required", status_code=400)

    preferred_language = body.get("preferred_language") or body.get("language")
    history = body.get("history") or body.get("conversation_history") or []

    try:
        response_payload = source_backed_assistant.process_query(
            query,
            preferred_lang=preferred_language,
            history=history
        )
        return api_response(data=response_payload, status_code=200)
    except Exception as e:
        logger.error(f"Error handling /api/chat: {e}", exc_info=True)
        return api_error("Failed to process conversational query", details=str(e), status_code=500)

@chat_bp.route("/diagnostics", methods=["GET"])
@chat_bp.route("/grok/status", methods=["GET"])
def diagnostics_endpoint():
    """
    GET /api/diagnostics or /api/grok/status
    Safe system diagnostics showing Grok API configuration, models, and database health.
    """
    from services.grok_service import grok_service
    from database.db import db_manager

    diag = {
        "status": "online",
        "grok_api": grok_service.get_diagnostics(),
        "database": db_manager.get_status()
    }
    return api_response(data=diag, status_code=200)

@chat_bp.route("/predict-intent", methods=["POST"])
def predict_intent_endpoint():
    """
    POST /api/predict-intent
    Voting ensemble intent classifier endpoint.
    Returns:
    {
      "intent": "...",
      "confidence": 0.0,
      "model": "Voting Ensemble"
    }
    """
    body = request.get_json(silent=True)
    if not body or not isinstance(body, dict):
        return api_error("Invalid JSON body", status_code=400)

    query = body.get("query", "").strip() or body.get("text", "").strip()
    if not query:
        return api_error("Field 'query' or 'text' is required", status_code=400)

    try:
        prediction = predict_intent(query)
        return api_response(data=prediction, status_code=200)
    except Exception as e:
        logger.error(f"Error handling /api/predict-intent: {e}", exc_info=True)
        return api_error("Failed to predict query intent", details=str(e), status_code=500)

@chat_bp.route("/recommend-standard", methods=["POST"])
def recommend_standard_endpoint():
    """
    POST /api/recommend-standard
    Candidate retrieval & combined relevance scoring engine.
    """
    body = request.get_json(silent=True)
    if not body or not isinstance(body, dict):
        return api_error("Invalid JSON body", status_code=400)

    product_desc = body.get("product_description", "").strip() or body.get("query", "").strip()
    if not product_desc:
        return api_error("Field 'product_description' is required", status_code=400)

    try:
        top_k = int(body.get("top_k", 5))
        result = recommendation_engine.recommend(product_desc, top_k=top_k)
        result["count"] = len(result.get("top_standards", []))
        result["recommendations"] = result.get("top_standards", [])
        return api_response(data=result, status_code=200)
    except Exception as e:
        logger.error(f"Error handling /api/recommend-standard: {e}", exc_info=True)
        return api_error("Failed to recommend standard", details=str(e), status_code=500)
