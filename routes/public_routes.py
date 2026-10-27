import json
import logging
from flask import Blueprint, request
from utils.response import api_response, api_error
from database.db import db_manager
from config import Config

public_bp = Blueprint("public", __name__, url_prefix="/api")
logger = logging.getLogger("bis_ai.routes.public")

@public_bp.route("/standards", methods=["GET"])
def get_standards():
    """GET /api/standards: Retrieves all Indian Standards with optional category query."""
    category = request.args.get("category")
    standards = db_manager.get_collection_data("standards")
    if category:
        standards = [s for s in standards if category.lower() in s.get("category", "").lower()]
    return api_response(data={"total": len(standards), "standards": standards})

@public_bp.route("/standards/<standard_id>", methods=["GET"])
def get_standard_by_id(standard_id):
    """GET /api/standards/<standard_id>: Retrieves single standard by id or code."""
    standards = db_manager.get_collection_data("standards")
    normalized_id = standard_id.lower().replace(":", " ").replace("-", " ")
    
    match = None
    for s in standards:
        sid = s.get("id", "").lower()
        scode = s.get("standard_code", "").lower().replace(":", " ").replace("-", " ")
        if standard_id.lower() == sid or normalized_id in scode or scode in normalized_id:
            match = s
            break

    if not match:
        return api_error(f"Standard with identifier '{standard_id}' not found", status_code=404)

    return api_response(data=match)

@public_bp.route("/certification", methods=["GET"])
def get_certification_schemes():
    """GET /api/certification: Retrieves all BIS certification schemes."""
    schemes = db_manager.get_collection_data("schemes")
    return api_response(data={"total": len(schemes), "schemes": schemes})

@public_bp.route("/hallmarking", methods=["GET"])
def get_hallmarking_data():
    """GET /api/hallmarking: Retrieves hallmarking standards and guidelines."""
    # Retrieve standards with Hallmarking tag or hallmarking FAQs
    standards = db_manager.get_collection_data("standards")
    hallmarking_standards = [s for s in standards if "hallmarking" in s.get("category", "").lower()]
    faqs = db_manager.get_collection_data("faqs")
    hallmarking_faqs = [f for f in faqs if "hallmarking" in f.get("topic", "").lower() or "huid" in f.get("topic", "").lower()]
    
    return api_response(data={
        "standards": hallmarking_standards,
        "guidelines_and_faqs": hallmarking_faqs,
        "key_requirements": [
            "Mandatory 3 marks: BIS Logo, Purity Fineness (e.g. 22K916), 6-digit alphanumeric HUID",
            "Fire Assay testing under IS 1418 at accredited Assaying & Hallmarking Centres (AHC)",
            "Consumer purity verification via official BIS CARE Mobile Application"
        ]
    })

@public_bp.route("/laboratories", methods=["GET"])
def get_laboratories():
    """GET /api/laboratories: Retrieves testing laboratories with optional state/city filter."""
    state = request.args.get("state")
    city = request.args.get("city")
    labs = db_manager.get_collection_data("laboratories")
    
    if state:
        labs = [l for l in labs if state.lower() in l.get("state", "").lower()]
    if city:
        labs = [l for l in labs if city.lower() in l.get("city", "").lower()]

    return api_response(data={"total": len(labs), "laboratories": labs})

@public_bp.route("/consumer", methods=["GET"])
def get_consumer_faqs():
    """GET /api/consumer: Retrieves consumer grievance, verification, and FAQ procedures."""
    faqs = db_manager.get_collection_data("faqs")
    return api_response(data={
        "total": len(faqs),
        "consumer_resources": faqs,
        "verification_tools": {
            "mobile_app": "BIS CARE (Available on Android & iOS)",
            "web_portal": "https://www.manakonline.in",
            "standards_portal": "https://standardsbis.bsbedge.com"
        }
    })

@public_bp.route("/health", methods=["GET"])
def health_check():
    """GET /api/health: Returns operational health and database connection status."""
    payload = {
        "status": "healthy",
        "service": "BIS-AI Intelligence Backend",
        "version": "1.0.0",
        "database": db_manager.get_status()
    }
    # Direct dictionary response for standard health check expectations
    return payload, 200

@public_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """GET /api/metrics: Returns ML model comparison and evaluation metrics."""
    metrics_path = Config.MODELS_DIR / "evaluation_metrics.json"
    comparison_path = Config.MODELS_DIR / "model_comparison.json"
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)
    comparison_data = {}
    if comparison_path.exists():
        with open(comparison_path, "r", encoding="utf-8") as f:
            comparison_data = json.load(f)

    return {
        "status": "success",
        "metrics": metrics,
        "data": comparison_data,
        "database_status": db_manager.get_status()
    }, 200
