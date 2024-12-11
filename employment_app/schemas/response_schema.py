from flask_restx import fields
from ..controllers import main_api

## 응답 스키마

# successResponse 모델 정의 (pagination 포함)
success_response_model = main_api.model('SuccessResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'data': fields.Raw(required=True, description='응답 데이터', example={}),
    'pagination': fields.Raw(description='페이징 데이터', example={}),
})

# ErrorResponse 모델 정의
error_response_model = main_api.model('ErrorResponse', {
    'status': fields.String(required=True, description='응답 상태', default='error', example='success'),
    'message': fields.String(required=True, description='에러 메시지', example=''),
    'code': fields.String(required=True, description='에러 코드', example=''),
})