from functools import wraps
import hmac
from flask import request, jsonify
from config import Config

def require_admin_auth(f):
    """
    Decorator enforcing API Key authentication for administrative endpoints.
    Accepts:
    - Header: 'X-Admin-API-Key: <token>' or 'Authorization: Bearer <token>'
    Enforces constant-time comparison to prevent timing attacks and rejects
    missing, empty, or whitespace credentials.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-Admin-API-Key")
        auth_header = request.headers.get("Authorization")
        
        if not api_key and auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ", 1)[1].strip()

        if not api_key or not str(api_key).strip():
            return jsonify({
                "status": "error",
                "error": "Unauthorized",
                "message": "Missing administrative API Key in 'X-Admin-API-Key' or 'Authorization: Bearer <token>' header."
            }), 401

        configured_key = (Config.ADMIN_API_KEY or "").strip()
        if not configured_key:
            return jsonify({
                "status": "error",
                "error": "Forbidden",
                "message": "Administrative operations are not configured on this server."
            }), 403

        # Constant-time comparison to eliminate timing side-channel attacks
        if not hmac.compare_digest(api_key.strip(), configured_key):
            return jsonify({
                "status": "error",
                "error": "Forbidden",
                "message": "Invalid administrative API Key credentials."
            }), 403

        return f(*args, **kwargs)
    return decorated_function
