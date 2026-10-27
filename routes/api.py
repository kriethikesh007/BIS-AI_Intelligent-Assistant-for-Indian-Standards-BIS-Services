import logging
from flask import Blueprint, request, jsonify
from services.assistant import orchestrator
from retrieval.retriever import retriever
from ml.classifier_service import intent_classifier
from database.db import db_manager

api_bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger("bis_ai.routes")

@api_bp.route("/query", methods=["POST"])
def query_assistant():
    """Main conversational answering and recommendation endpoint."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({
            "error": "Query parameter is required",
            "status": "error"
        }), 400

    try:
        from services.conversational_assistant import source_backed_assistant
        response_payload = source_backed_assistant.process_query(query)
        return jsonify({
            "status": "success",
            "data": response_payload
        }), 200
    except Exception as e:
        logger.error(f"Error processing query '{query}': {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": "Internal server processing error",
            "detail": str(e)
        }), 500

@api_bp.route("/recommend", methods=["POST"])
def recommend_standard():
    """Specific product-to-standard recommendation endpoint."""
    data = request.get_json(silent=True) or {}
    product_description = data.get("product_description", "").strip() or data.get("query", "").strip()

    if not product_description:
        return jsonify({
            "error": "product_description is required",
            "status": "error"
        }), 400

    from services.recommendation_engine import recommendation_engine
    result = recommendation_engine.recommend(product_description, top_k=5)
    return jsonify({
        "status": "success",
        "product_description": product_description,
        "extracted_analysis": result["extracted_analysis"],
        "count": len(result["top_standards"]),
        "recommendations": result["top_standards"]
    }), 200

@api_bp.route("/classify-intent", methods=["POST"])
def classify_intent():
    """Endpoint to inspect VotingClassifier ensemble intent classification."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query required"}), 400

    from ml.predict_intent import predict_intent
    result = predict_intent(query)
    return jsonify({
        "status": "success",
        "query": query,
        "intent": result["intent"],
        "confidence": result["confidence"],
        "model": result["model"]
    }), 200

@api_bp.route("/standards", methods=["GET"])
def get_standards():
    """Fetch all indexed Indian Standards with optional category filter."""
    category = request.args.get("category")
    standards = db_manager.get_collection_data("standards")
    if category:
        standards = [s for s in standards if category.lower() in s.get("category", "").lower()]
    return jsonify({
        "status": "success",
        "total": len(standards),
        "standards": standards
    }), 200

@api_bp.route("/schemes", methods=["GET"])
def get_schemes():
    """Fetch all BIS certification schemes."""
    schemes = db_manager.get_collection_data("schemes")
    return jsonify({
        "status": "success",
        "total": len(schemes),
        "schemes": schemes
    }), 200

@api_bp.route("/laboratories", methods=["GET"])
def get_laboratories():
    """Fetch testing laboratories with optional state/discipline filters."""
    state = request.args.get("state")
    labs = db_manager.get_collection_data("laboratories")
    if state:
        labs = [l for l in labs if state.lower() in l.get("state", "").lower()]
    return jsonify({
        "status": "success",
        "total": len(labs),
        "laboratories": labs
    }), 200

@api_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """Return model evaluation metrics (accuracy, precision, recall, confusion matrix)."""
    from pathlib import Path
    import json
    from config import Config

    metrics_path = Config.MODELS_DIR / "evaluation_metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    else:
        metrics = {"error": "Metrics file not found. Run training script first."}

    return jsonify({
        "status": "success",
        "metrics": metrics,
        "database_status": db_manager.get_status()
    }), 200

@api_bp.route("/data-quality", methods=["GET"])
def get_data_quality():
    """Return pipeline data quality report."""
    from pathlib import Path
    import json
    from config import Config

    report_path = Config.BASE_DIR / "data" / "data_quality_report.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    else:
        report = {"error": "Quality report not found. Run ingestion pipeline first."}

    return jsonify({
        "status": "success",
        "data_quality_report": report
    }), 200

@api_bp.route("/health", methods=["GET"])
def health_check():
    """System health and ready status."""
    return jsonify({
        "status": "healthy",
        "service": "BIS-AI Intelligence Backend",
        "version": "1.0.0",
        "database": db_manager.get_status()
    }), 200
