from marshmallow import Schema, fields

## 응답 스키마

class SuccessResponseSchema(Schema):
    status = fields.String(required=True, description='응답 상태', example='success')
    data = fields.Raw(required=True, description='응답 데이터', example={})
    pagination = fields.Raw(description='페이징 데이터', example={})

class ErrorResponseSchema(Schema):
    status = fields.String(required=True, description='응답 상태', default='error', example='error')
    message = fields.String(required=True, description='에러 메시지', example='에러가 발생했습니다.')
    code = fields.String(required=True, description='에러 코드', example='400')