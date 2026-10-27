from flask import jsonify

def api_response(data=None, message=None, status_code=200):
    """Standardized successful JSON response."""
    payload = {"status": "success"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code

def api_error(error_message, details=None, status_code=400):
    """Standardized error JSON response."""
    payload = {
        "status": "error",
        "error": error_message
    }
    if details:
        payload["details"] = details
    return jsonify(payload), status_code
