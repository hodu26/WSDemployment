from flask import jsonify, request
from werkzeug.exceptions import HTTPException

# 커스텀 에러 클래스
class CustomError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class AuthenticationError(CustomError):
    def __init__(self, message="Authentication failed"):
        super().__init__(message, 401)

class ValidationError(CustomError):
    def __init__(self, message="Invalid data format"):
        super().__init__(message, 400)

# 에러 처리 핸들러
def handle_custom_error(error):
    """커스텀 에러 처리 함수"""
    status_code = 500
    message = str(error)

    if isinstance(error, CustomError):
        status_code = error.status_code
        message = error.message

    return jsonify({
        "status": status_code,
        "error": error.__class__.__name__,
        "message": message
    }), status_code

def configure_error_handlers(app):
    """글로벌 에러 핸들러 설정."""
    @app.errorhandler(Exception)
    def handle_exception(e):
        """모든 예외에 대한 글로벌 에러 핸들러."""
        if isinstance(e, CustomError):
            return handle_custom_error(e)

        # 기본 예외 처리
        app.logger.error(f"Exception: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.warning(f"404 Not Found: {request.method} {request.url}")
        return jsonify({"error": "Page not found"}), 404