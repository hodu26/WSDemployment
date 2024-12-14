from marshmallow import Schema, fields, validate
from ..extensions import JobStatus

## 요청 스키마

# job ns
class JobPostSchema(Schema):
    title = fields.String(required=True, description='채용 공고 제목', example='24년 하반기 경력직 상시채용222')
    company = fields.String(required=True, description='회사명', example='홍길동(주)')
    location = fields.String(required=True, description='근무 지역', example='서울 서초구')
    salary = fields.String(required=True, description='급여', example='2,000만원')
    skills = fields.String(required=True, description='기술 목록', example="Python,Django,AWS")
    career_level = fields.String(required=True, description='경력', example='경력2년↑')
    education = fields.String(description='학력', example='초대졸↑')
    employment_type = fields.String(description='채용 대상', example='정규직·계약직')
    trend_keyword = fields.String(description='트렌드 키워드', example='인기있는')
    deadline = fields.Date(description='지원 마감 기한', example='2025-03-01')
    link = fields.String(description='공고 링크', example='http://localhost:5000')

class JobPostUpdateSchema(Schema):
    select_post = fields.String(required=True, description='수정할 채용 공고 제목', example='24년 하반기 경력직 상시채용222')
    title = fields.String(description='채용 공고 제목', example='25년 상반기 경력직 상시채용222')
    company = fields.String(description='회사명', example='김철수(주)')
    location = fields.String(description='근무 지역', example='서울 강남구')
    salary = fields.String(description='급여', example='1,000만원')
    skills = fields.String(description='기술 목록', example="Python,DevOps")
    career_level = fields.String(description='경력', example='경력5년↑')
    education = fields.String(description='학력', example='초대졸↑')
    employment_type = fields.String(description='채용 대상', example='정규직·계약직')
    trend_keyword = fields.String(description='트렌드 키워드', example='취업축하금금')
    deadline = fields.Date(description='지원 마감 기한', example='2025-08-01')
    link = fields.String(description='공고 링크', example='http://localhost:5000')

class JobPostDelSchema(Schema):
    select_post = fields.String(required=True, description='수정할 채용 공고 제목', example='25년 상반기 경력직 상시채용222')


class JobSearchfilterSchema(Schema):
    keyword = fields.Str(default='채용', missing='채용', description='키워드 검색 (title, company, position(skill) ...)')
    location = fields.Str(default='서울', missing='서울', description='지역 필터링')
    career_level = fields.Str(default='2년', missing='2년', description='최소 경력 필터링')
    salary = fields.Str(default='1000만원', missing='1000만원', description='최소 급여 필터링')
    skills = fields.Str(default='C++,웹개발', missing='C++,웹개발', description='필요한 스킬 리스트 (쉼표로 구분)')
    sort = fields.Str(
        missing='view_desc',
        validate=validate.OneOf(
            ['deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc']
        ),
        description='정렬 기준 선택'
    )
    page = fields.Int(default=1, missing=1, description='페이지 번호')
    limit = fields.Int(default=20, missing=20, description='한 페이지당 개수')

class JobSearchSchema(Schema):
    keyword = fields.Str(default='채용', missing='채용', description='키워드 검색 (title, company, position(skill) ...)')
    page = fields.Int(default=1, missing=1, description='페이지 번호')
    limit = fields.Int(default=20, missing=20, description='한 페이지당 개수')

class JobFilterSchema(Schema):
    keyword = fields.Str(default='채용', missing='채용', description='키워드 검색 (title, company, position(skill) ...)')
    location = fields.Str(default='서울', missing='서울', description='지역 필터링')
    career_level = fields.Str(default='2년', missing='2년', description='최소 경력 필터링')
    salary = fields.Str(default='1000만원', missing='1000만원', description='최소 급여 필터링')
    status = fields.Str(
        missing=JobStatus.OPEN.value,
        validate=validate.OneOf(
            [status.value for status in JobStatus]
        ),
        description='상태 필터링'
    )
    trend_keywords = fields.Str(default='취업', missing='취업', description='트렌드 키워드 필터링')
    skills = fields.Str(default='C++,웹개발', missing='C++,웹개발', description='필요한 스킬 리스트 (쉼표로 구분)')
    sort = fields.Str(
        missing='view_desc',
        validate=validate.OneOf(
            ['deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc']
        ),
        description='정렬 기준 선택'
    )
    page = fields.Int(default=1, missing=1, description='페이지 번호')
    limit = fields.Int(default=20, missing=20, description='한 페이지당 개수')


class JobSortSchema(Schema):
    sort = fields.Str(
        missing='view_desc',
        validate=validate.OneOf(
            ['deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc']
        ),
        description='정렬 기준 선택'
    )
    page = fields.Int(default=1, missing=1, description='페이지 번호')
    limit = fields.Int(default=20, missing=20, description='한 페이지당 개수')