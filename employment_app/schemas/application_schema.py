from marshmallow import Schema, fields, validate
from ..extensions import ApplicationStatus

class ApplicationSchema(Schema):
    job_post_id = fields.Int(required=True, description='채용 공고 id', default='100', example='100')
    status = fields.Str(
        missing=ApplicationStatus.SUBMIT.value,
        validate=validate.OneOf(
            [status.value for status in ApplicationStatus]
        ),
        description='지원 상태'
    )
    sort = fields.Str(
        missing='desc',
        validate=validate.OneOf(
            ['desc', 'asc']
        ),
        description='날짜별 정렬'
    )
    resume_url = fields.Str(missing=None, description='이력서 url', default='http://loacalhost:5000', example='http://loacalhost:5000')  # 이력서 첨부 (선택 사항)

class ApplicationListSchema(Schema):
    job_post_id = fields.Int(required=True, description='채용 공고 id', example='100')
    status = fields.Str(
        example=ApplicationStatus.SUBMIT.value,
        missing=ApplicationStatus.SUBMIT.value,
        validate=validate.OneOf(
            [status.value for status in ApplicationStatus]
        ),
        description='지원 상태'
    )
    resume_url = fields.Str(missing=None, description='이력서 url', example='http://loacalhost:5000')  # 이력서 첨부 (선택 사항)
    page = fields.Int(missing=1, description='페이지 번호', example=1)