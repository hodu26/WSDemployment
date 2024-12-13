from flask import jsonify, request
from flask_jwt_extended.exceptions import NoAuthorizationError, WrongTokenError
from werkzeug.exceptions import HTTPException

# HTTP 상태 코드에 대한 문자열 코드 매핑
error_codes = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
}

# 성공 응답 생성 함수
def success_response(data=None, pagination=None):
    """성공적인 응답 형식"""
    response = {
        "status": "success",
        "data": data or {},
    }
    if pagination:
        response["pagination"] = pagination
    return jsonify(response).get_json()

# 실패 응답 생성 함수
def error_response(message, status_code=400):
    """실패 응답 형식"""
    response = {
        "status": "error",
        "message": message,
        "code": error_codes.get(status_code, "UNKNOWN_ERROR")
    }
    return jsonify(response).get_json(), status_code

# 커스텀 오류 기본 클래스
class CustomError(HTTPException):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status = "error"
        self.message = message
        self.code = status_code  # HTTP 상태 코드 사용

    def get_json_response(self):
        # HTTP 코드에 해당하는 문자열 코드로 변환하여 반환
        print(error_response(self.message, self.code))
        return error_response(self.message, self.code)

# 인증 오류 클래스 (401 Unauthorized)
class AuthenticationError(CustomError):
    def __init__(self, message="인증 실패"):
        super().__init__(message, status_code=401)

# 검증 오류 클래스 (400 Bad Request)
class ValidationError(CustomError):
    def __init__(self, message="데이터 형식이 올바르지 않습니다."):
        super().__init__(message, status_code=400,)

# 서버 오류 클래스 (500 Internal Server Error)
class ServerError(CustomError):
    def __init__(self, message="서버 내부 오류"):
        super().__init__(message, status_code=500)

# 글로벌 오류 처리 함수
def configure_error_handlers(app):
    @app.errorhandler(CustomError)
    def handle_custom_error(e):
        return e.get_json_response()

    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(e):
        return e.get_json_response()

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return e.get_json_response()
    
    @app.errorhandler(NoAuthorizationError)
    def handle_missing_token(e):
        """JWT 토큰 누락 오류 처리"""
        app.logger.warning(f"JWT 토큰 누락: {request.method} {request.url}")
        return error_response("토큰이 없습니다. 인증 헤더를 추가해주세요.", 401)
    
    @app.errorhandler(WrongTokenError)
    def handle_wrong_token_error(e):
        return error_response("잘못된 토큰이 제공되었습니다.", 401)
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        app.logger.error(f"예외 발생: {str(e)}", exc_info=True)
        return error_response("서버 내부 오류가 발생했습니다.", 500)

    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.warning(f"404 페이지 찾을 수 없음: {request.method} {request.url}")
        return error_response("페이지를 찾을 수 없습니다.", 404)