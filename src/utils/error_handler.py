from flask import Flask, request, jsonify
from api_error import ApiError

alert_filter = "ERROR:"

def global_api_error_handler(app: Flask):
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        status = error.status or 500
        print(alert_filter, status, error.message)

        body = {
            "message": error.message or "An error occurred during the request",
            "name": error.name,
            "status": status
        }

        return jsonify(body), status

def global_error_handler(message: str, error: Exception = None):
    if error:
        print(alert_filter, message, error)
    else:
        print(alert_filter, message)
    return error
