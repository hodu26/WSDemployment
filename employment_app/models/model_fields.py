from flask_restx import fields
from ..controllers import main_api

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

token_model = main_api.model('Token', {
    'token_id': fields.Integer(readonly=True, description="토큰의 고유 ID"),
    'user_id': fields.Integer(required=True, description="사용자 ID"),
    'access_token': fields.String(required=True, description="액세스 토큰"),
    'refresh_token': fields.String(required=True, description="리프레시 토큰"),
    'access_expires_at': fields.DateTime(description="액세스 토큰 만료 시간"),
    'refresh_expires_at': fields.DateTime(description="리프레시 토큰 만료 시간"),
    'created_at': fields.DateTime(description="토큰 생성 시간")
})

user_model = {
    'user_id': fields.Integer(readonly=True, description="사용자의 고유 ID"),
    'email': fields.String(required=True, description="사용자의 이메일 (고유해야 함)"),
    'password': fields.String(required=True, description="사용자의 비밀번호"),
    'name': fields.String(required=True, description="사용자의 이름"),
    'created_at': fields.DateTime(description="사용자가 생성된 시간"),
    'updated_at': fields.DateTime(description="사용자가 마지막으로 수정된 시간"),
    'tokens': fields.List(fields.Nested(token_model), description="사용자에 해당하는 토큰 목록")
}

company_model = {
    'company_id': fields.Integer(readonly=True, description="회사의 고유 ID"),
    'name': fields.String(required=True, description="회사의 이름"),
    'company_type': fields.String(description="회사의 유형 (예: IT, 제조업 등)"),
    'industry': fields.String(description="회사가 속한 산업"),
    'website': fields.String(description="회사의 웹사이트 주소"),
    'address': fields.String(description="회사의 주소"),
    'introduce': fields.String(description="회사의 소개")
}

job_posting_model = {
    'job_post_id': fields.Integer(readonly=True, description="구인 공고의 고유 ID"),
    'company_id': fields.Integer(required=True, description="구인 공고를 게시한 회사의 ID"),
    'trend_keywords': fields.String(description="구인 공고와 관련된 트렌드 키워드"),
    'title': fields.String(required=True, description="구인 공고 제목"),
    'link': fields.String(description="구인 공고의 링크"),
    'location': fields.String(description="구인 공고의 위치"),
    'career_level': fields.String(description="구인 공고에 요구되는 경력 수준"),
    'education': fields.String(description="구인 공고에 요구되는 교육 수준"),
    'employment_type': fields.String(description="구인 공고에 명시된 고용 형태 (정규직, 계약직 등)"),
    'deadline': fields.Date(description="구인 공고 마감일"),
    'salary_range': fields.String(description="구인 공고에서 제공하는 급여 범위"),
    'posted_date': fields.Date(description="구인 공고 게시일"),
    'status': fields.String(enum=['open', 'closed'], description="구인 공고 상태 (open: 모집 중, closed: 마감)")
}

skill_model = {
    'skill_id': fields.Integer(readonly=True, description="기술 스킬의 고유 ID"),
    'name': fields.String(required=True, description="기술 스킬의 이름")
}

job_posting_skill_model = {
    'job_post_id': fields.Integer(required=True, description="구인 공고 ID"),
    'skill_id': fields.Integer(required=True, description="기술 스킬 ID")
}

bookmark_model = {
    'bookmark_id': fields.Integer(readonly=True, description="즐겨찾기 고유 ID"),
    'user_id': fields.Integer(required=True, description="사용자 ID"),
    'job_post_id': fields.Integer(required=True, description="즐겨찾기한 구인 공고 ID"),
    'created_at': fields.DateTime(description="즐겨찾기가 생성된 시간")
}

application_model = {
    'apply_id': fields.Integer(readonly=True, description="지원서 고유 ID"),
    'user_id': fields.Integer(required=True, description="사용자 ID"),
    'job_post_id': fields.Integer(required=True, description="구인 공고 ID"),
    'company_id': fields.Integer(required=True, description="회사의 ID"),
    'status': fields.String(enum=['submitted', 'reviewed', 'accepted', 'rejected'], description="지원 상태 (submitted: 제출됨, reviewed: 검토됨, accepted: 채용됨, rejected: 거절됨)"),
    'applied_at': fields.DateTime(description="지원서 제출 시간"),
    'resume_url': fields.String(description="이력서 URL")
}