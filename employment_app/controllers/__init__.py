from flask import Blueprint
from flask_restx import Api

api_blueprint = Blueprint('api', __name__)

authorizations = {
    "accesskey": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "JWT Token (Bearer <token>)"
    },
    "refreshkey": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "JWT Token (Bearer <token>)"
    }
}

# CustomApi 클래스 정의 (handle_error 오버라이드)
class CustomApi(Api):
    def handle_error(self, e):
        """Flask 글로벌 핸들러와 통합된 에러 처리"""
        # 특정 예외를 Flask 글로벌 핸들러로 전달
        if hasattr(e, 'get_json_response'):  # CustomError와 같은 예외 처리
            return e.get_json_response()
        
        # 일반적인 예외 처리
        response = {
            "status": "error",
            "message": str(e),
            "code": getattr(e, 'code', 500)  # HTTP 상태 코드가 없으면 500으로 기본 설정
        }
        return jsonify(response), getattr(e, 'code', 500)

# API 객체 생성 시 securityDefinitions 추가
main_api = CustomApi(
    api_blueprint,
    title="WD_employment_3",
    version="1.0",
    description="웹서비스 설계 과제 3",
    doc="/api-docs",
    authorizations=authorizations
)

from .main_controller import *
from .auth_controller import *

# # api_blueprint에 auth_bp 등록
# api_blueprint.register_blueprint(auth_bp, url_prefix='/auth')