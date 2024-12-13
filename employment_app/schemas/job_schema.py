from flask_restx import fields
from ..controllers import job_ns

## 요청 스키마

# job ns
job_post_model = job_ns.model('Job_post', {
    'title': fields.String(required=True, description='채용 공고 제목', example='24년 하반기 경력직 상시채용222'),
    'company': fields.String(required=True, description='회사명', example='홍길동(주)'),
    'location': fields.String(required=True, description='근무 지역', example='서울 서초구'),
    'salary': fields.String(required=True, description='급여', example='2,000만원'),
    'skills': fields.String(required=True, description='기술 목록', example="Python,Django,AWS"),
    'career_level': fields.String(required=True, description='경력', example='경력2년↑'),
    'education': fields.String(description='학력', example='초대졸↑'),
    'employment_type': fields.String(description='채용 대상', example='정규직·계약직'),
    'trend_keyword': fields.String(description='트렌드 키워드', example='인기있는'),
    'deadline': fields.Date(description='지원 마감 기한', example='2025-03-01'),
    'link': fields.String(description='공고 링크', example='http://localhost:5000'),
})

job_post_update_model = job_ns.model('Job_post_update', {
    'select_post': fields.String(required=True, description='수정할 채용 공고 제목', example='24년 하반기 경력직 상시채용222'),
    'title': fields.String(description='채용 공고 제목', example='25년 상반기 경력직 상시채용222'),
    'company': fields.String(description='회사명', example='김철수(주)'),
    'location': fields.String(description='근무 지역', example='서울 강남구'),
    'salary': fields.String(description='급여', example='1,000만원'),
    'skills': fields.String(description='기술 목록', example="Python,DevOps"),
    'career_level': fields.String(description='경력', example='경력5년↑'),
    'education': fields.String(description='학력', example='초대졸↑'),
    'employment_type': fields.String(description='채용 대상', example='정규직·계약직'),
    'trend_keyword': fields.String(description='트렌드 키워드', example='취업축하금금'),
    'deadline': fields.Date(description='지원 마감 기한', example='2025-08-01'),
    'link': fields.String(description='공고 링크', example='http://localhost:5000'),
})

job_post_del_model = job_ns.model('Job_post_del', {
    'select_post': fields.String(required=True, description='수정할 채용 공고 제목', example='25년 상반기 경력직 상시채용222')
})