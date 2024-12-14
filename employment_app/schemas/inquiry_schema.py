from marshmallow import Schema, fields

class InquirySchema(Schema):
    job_post_id = fields.Int(required=True, description='문의 공고 id', example=100)
    title = fields.String(required=True, description='문의 제목', example='공고 지원 서류 관련 문의입니다.')
    message = fields.Str(required=True, description='문의 내용', example='가족관계증명서는 초본과 등본 중 어떤걸로 제출해야 할까요?')