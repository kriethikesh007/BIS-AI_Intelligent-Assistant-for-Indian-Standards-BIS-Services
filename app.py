import os
import sys
import logging
from pathlib import Path
from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS

# Add root directory to python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from routes.api import api_bp
from database.seed import ingest_all

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bis_ai.app")

def create_app():
    """Application factory initializing Flask app and registering routes."""
    react_dist = BASE_DIR / "frontend-react" / "dist"
    static_dir = react_dist if react_dist.exists() else (BASE_DIR / "frontend")

    app = Flask(
        __name__,
        static_folder=str(static_dir),
        static_url_path="",
        template_folder=str(static_dir)
    )

    # Enable Cross-Origin Resource Sharing with configurable origins
    cors_origins = Config.CORS_ORIGINS if Config.CORS_ORIGINS else "*"
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # Register Modular Blueprints
    from routes.chat_routes import chat_bp
    from routes.public_routes import public_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    # Also register legacy api_bp for backward compatibility
    app.register_blueprint(api_bp)

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api"):
            return {"status": "error", "error": "Endpoint not found"}, 404
        index_file = Path(app.static_folder) / "index.html"
        if index_file.exists():
            return send_from_directory(app.static_folder, "index.html")
        return {"status": "error", "error": "Endpoint not found"}, 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return {"status": "error", "error": "Internal server error"}, 500

    # Ensure dataset is loaded and indexed on launch
    ingest_all()

    # Frontend Route with client-side SPA fallback for non-API routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api/"):
            return {"status": "error", "error": "Endpoint not found"}, 404
        target = Path(app.static_folder) / path
        if path and target.exists() and not target.is_dir():
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    return app

app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting BIS-AI Server on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
