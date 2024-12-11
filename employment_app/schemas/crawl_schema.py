from flask_restx import fields
from ..controllers import main_api

## 요청 스키마

# crawl ns
job_post_model = main_api.model('Job_post', {
    'keyword': fields.String(required=True, description='크롤링 검색 키워드', example='IT개발·데이터'),
    'pages': fields.Integer(required=True, description='크롤링 할 페이지 수', example=1)
})

company_model = main_api.model('Company', {
    'company_name': fields.String(required=True, description='크롤링 할 회사명', example='케이티텔레캅(주)'),
    'link': fields.String(required=True, description='크롤링 할 페이지 링크', example='https://www.saramin.co.kr/zf_user/company-info/view?csn=YnkrZk9OTDVDM29ra0lXZDNVMDNQZz09')
})

skill_model = main_api.model('Skill', {
    'skill': fields.String(required=True, description='추가 할 기술명', example='Java'),
})