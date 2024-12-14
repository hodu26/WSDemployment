from marshmallow import Schema, fields

## 요청 스키마

# crawl ns
class JobCrawlSchema(Schema):
    keyword = fields.String(required=True, description='크롤링 검색 키워드', example='IT개발·데이터')
    pages = fields.Integer(required=True, description='크롤링 할 페이지 수', example=1)

class CompanySchema(Schema):
    company_name = fields.String(required=True, description='크롤링 할 회사명', example='케이티텔레캅(주)')
    link = fields.String(required=True, description='크롤링 할 페이지 링크', example='https://www.saramin.co.kr/zf_user/company-info/view?csn=YnkrZk9OTDVDM29ra0lXZDNVMDNQZz09')

class SkillSchema(Schema):
    skill = fields.String(required=True, description='추가 할 기술명', example='Java')