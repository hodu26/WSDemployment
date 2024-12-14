from flask import current_app
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint as SmorestBlueprint
from flask.views import MethodView
from sqlalchemy import select
from sqlalchemy.orm import aliased
from ..models import db, JobPosting, Company, Skill, JobPostingSkill
from ..schemas import JobPostSchema, JobPostUpdateSchema, JobPostDelSchema, JobSearchfilterSchema, JobSearchSchema, JobFilterSchema, JobSortSchema, SuccessResponseSchema, ErrorResponseSchema
from ..error_log import ValidationError, success_response
from datetime import datetime

# skills 테이블 업데이트
def update_skills_table(job_sector_list):
    for sector in job_sector_list:
        for skill_name in sector:
            if skill_name.strip() != "외":
                skill = Skill.query.filter_by(name=skill_name.strip()).first()

                if not skill:
                    skill = Skill(name=skill_name.strip())
                    db.session.add(skill)
                else:
                    skill.name = skill_name.strip()
    db.session.commit()

# job_posting_skills 테이블 저장
def save_job_posting_skills(job_post_id, job_sector_list):
    for sector in job_sector_list:
        for skill_name in sector:
            skill = Skill.query.filter_by(name=skill_name).first()
            if skill:
                # job_posting_skills 테이블에 해당 job_post_id와 skill_id 조합이 이미 존재하는지 확인
                existing_record = JobPostingSkill.query.filter_by(
                    job_post_id=job_post_id, skill_id=skill.skill_id
                ).first()
                
                # 해당 조합이 없으면 새로운 레코드 추가
                if not existing_record:
                    job_posting_skill = JobPostingSkill(
                        job_post_id=job_post_id, 
                        skill_id=skill.skill_id
                    )
                    db.session.add(job_posting_skill)
    db.session.commit()


job_ns = SmorestBlueprint("Jobs", "Jobs", url_prefix="/jobs", description="채용 공고 관련 API")

# 공통 함수 정의
def apply_filters(query, filters):
    """
    필터를 쿼리에 적용
    """
    if filters.get("location"):
        query = query.filter(JobPosting.location.ilike(f"%{filters['location']}%"))
    if filters.get("career_level"):
        career_level = filters["career_level"]
        query = query.filter(JobPosting.career_level >= career_level)
    if filters.get("salary"):            
        salary = filters["salary"]
        query = query.filter(JobPosting.salary_range >= salary)
    if filters.get("status"):
        query = query.filter(JobPosting.status == filters['status'].lower())
    if filters.get("trend_keywords"):
        query = query.filter(JobPosting.trend_keywords.ilike(f"%{filters['trend_keywords']}%"))
    if filters.get("keyword"):
        keyword = filters["keyword"]
        company_alias = aliased(Company)
        skill_alias = aliased(Skill)
        query = query.join(company_alias, JobPosting.company_id == company_alias.company_id) \
            .join(JobPostingSkill, JobPosting.job_post_id == JobPostingSkill.job_post_id) \
            .join(skill_alias, JobPostingSkill.skill_id == skill_alias.skill_id) \
            .filter(
                JobPosting.title.ilike(f"%{keyword}%") |
                company_alias.name.ilike(f"%{keyword}%") |
                skill_alias.name.ilike(f"%{keyword}%")
            )
    if filters.get("skills"):
        skills = [skill.strip() for skill in filters["skills"].split(",")]
        skill_alias = aliased(Skill)
        subquery = db.session.query(JobPostingSkill.job_post_id).join(skill_alias).filter(skill_alias.name.in_(skills)).subquery()
        query = query.filter(JobPosting.job_post_id.in_(select(subquery)))
    return query

def add_skills_to_jobs(jobs):
    """
    스킬 정보를 각 공고에 추가
    """
    jobs_with_skills = []
    for job in jobs:
        job_data = job.to_dict()
        job_posting_skills = db.session.query(Skill.name).join(JobPostingSkill).filter(
            JobPostingSkill.job_post_id == job.job_post_id
        ).all()
        job_data['skills'] = [skill.name for skill in job_posting_skills]
        jobs_with_skills.append(job_data)
    return jobs_with_skills

def apply_sorting(query, sort):
    """
    정렬을 쿼리에 적용
    """
    sorting_options = {
        "deadline_asc": JobPosting.deadline.asc(),
        "deadline_desc": JobPosting.deadline.desc(),
        "posted_date_desc": JobPosting.posted_date.desc(),
        "view_desc": JobPosting.views.desc(),
        "salary_asc": JobPosting.salary_range.asc(),
        "salary_desc": JobPosting.salary_range.desc()
    }
    if sort in sorting_options:
        query = query.order_by(sorting_options[sort])
    return query

# Job 리소스 엔드포인트
@job_ns.route("")
class JobList(MethodView):
    @job_ns.arguments(JobSearchfilterSchema, location='query')
    @job_ns.response(200, SuccessResponseSchema)
    @job_ns.response(400, ErrorResponseSchema)
    def get(self, args):
        """
        채용 공고 목록 조회 기능 (검색, 필터링, 정렬, 페이지네이션)
        """
        filters = {key: args.get(key) for key in ['keyword', 'location', 'career_level', 'salary', 'skills']}
        sort = args.get('sort')
        page = args.get('page', 1)
        limit = args.get('limit', 20)

        query = apply_filters(JobPosting.query, filters)
        query = apply_sorting(query, sort)
        paginated_result = query.paginate(page=page, per_page=limit, error_out=False)

        jobs_with_skills = add_skills_to_jobs(paginated_result.items)
        pagination = {
            "currentPage": paginated_result.page,
            "totalPages": paginated_result.pages,
            "totalItems": paginated_result.total
        }

        return success_response({"jobs": jobs_with_skills}, pagination), 200

    @jwt_required()
    @job_ns.doc(security=[{"accesskey": []}])
    @job_ns.arguments(JobPostSchema)
    @job_ns.response(201, SuccessResponseSchema)
    @job_ns.response(400, ErrorResponseSchema)
    def post(self, request):
        """
        새로운 채용 공고 등록
        """
        data = request

        # 데이터 유효성 검사
        required_fields = ['title', 'location', 'salary', 'career_level', 'skills', 'company']
        for field in required_fields:
            if not data.get(field):
                current_app.logger.warning(f"{field} is a neccessary fields")
                raise ValidationError(f"{field} 필드는 필수 입력 항목입니다.")
            
        # 제목 중복 확인
        existing_job = JobPosting.query.filter_by(title=data['title']).first()
        if existing_job:
            current_app.logger.warning(f"'{data['title']}' is already exist")
            raise ValidationError(f"'{data['title']}' 제목의 공고가 이미 존재합니다.")
        
        # Company 테이블에서 회사 확인
        company = Company.query.filter_by(name=data['company']).first()
        if not company:
            company_name = data['company']
            # 회사 정보 저장
            company = Company(
                name=company_name,
                company_type='정보 없음',
                industry='정보 없음',
                website='정보 없음',
                address='정보 없음',
                introduce='정보 없음'
            )
            db.session.add(company)
            db.session.commit()

        deadline=data.get('deadline', None)

        # 새로운 JobPosting 객체 생성
        new_job = JobPosting(
            title=data['title'],
            company_id=company.company_id,
            trend_keywords=data.get('trend_keyword', ''),
            link=data.get('link', ''),
            location=data['location'],
            career_level=data['career_level'],
            education=data.get('education', ''),
            employment_type=data.get('employment', ''),
            deadline=deadline,
            salary_range=data['salary'],
            posted_date=datetime.today().date(),
            status = 'closed' if deadline and deadline < datetime.today().date() else 'open'
        )

        db.session.add(new_job)
        db.session.commit()

         # 스킬 추가
        if 'skills' in data:
            skills = [skill.strip() for skill in data['skills'].split(',')]
            update_skills_table([skills])
            save_job_posting_skills(new_job.job_post_id, [skills])

        job_data = new_job.to_dict()
        job_data['skills'] = skills

        return success_response({"job": job_data}), 201
    
    @jwt_required()
    @job_ns.doc(security=[{"accesskey": []}])
    @job_ns.arguments(JobPostUpdateSchema)
    @job_ns.response(200, SuccessResponseSchema)
    @job_ns.response(400, ErrorResponseSchema)
    @job_ns.response(404, ErrorResponseSchema)
    def put(self, request):
        """
        채용 공고 수정
        """
        data = request

        # 데이터 유효성 검사
        required_fields = ['select_post']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"{field} 필드는 필수 입력 항목입니다.")
            
        job = JobPosting.query.filter_by(title=data['select_post']).first()
        if not job:
            current_app.logger.warning(f"Cannot find job post with title '{data['select_post']}'")
            raise ValidationError("해당 채용 공고를 찾을 수 없습니다.")
        
        # `company_id`를 통해 현재 회사 이름 조회
        current_company = Company.query.get(job.company_id)
        current_company_name = current_company.name if current_company else None

        # 회사 이름 변경 시 확인 및 업데이트
        if current_company_name != data['company']:
            company = Company.query.filter_by(name=data['company']).first()
            if not company:
                company_name = data['company']
                # 회사 정보 저장
                company = Company(
                    name=company_name,
                    company_type='정보 없음',
                    industry='정보 없음',
                    website='정보 없음',
                    address='정보 없음',
                    introduce='정보 없음'
                )
                db.session.add(company)
                db.session.commit()

            job.company_id = company.company_id  # 새로운 회사 정보 연결
        
        if 'deadline' in data:
            deadline=data['deadline']
            job.deadline = deadline

        # 공고 정보 업데이트
        job.title = data.get('title', job.title)
        job.trend_keywords = data.get('trend_keywords', job.trend_keywords)
        job.link = data.get('link', job.link)
        job.location = data.get('location', job.location)
        job.career_level = data.get('career_level', job.career_level)
        job.education = data.get('education', job.education)
        job.employment_type = data.get('employment', job.employment_type)
        job.salary_range = data.get('salary_range', job.salary_range)
        job.posted_date = datetime.today().date()
        job.status = 'closed' if deadline and deadline < datetime.today().date() else 'open'

        # 스킬 업데이트
        if 'skills' in data:
            skills = [skill.strip() for skill in data['skills'].split(',')]
            # 기존 JobPostingSkill 삭제
            JobPostingSkill.query.filter_by(job_post_id=job.job_post_id).delete()
            db.session.commit()

            # 새로운 스킬 추가
            update_skills_table([skills])
            save_job_posting_skills(job.job_post_id, [skills])

        db.session.commit()

        # 업데이트된 공고 정보 반환
        updated_job = JobPosting.query.get(job.job_post_id)
        updated_job_data = updated_job.to_dict()
        updated_job_data['skills'] = skills

        # 공고와 연결된 스킬 정보 추가
        updated_job_skills = db.session.query(Skill.name).join(JobPostingSkill).filter(
            JobPostingSkill.job_post_id == updated_job.job_post_id
        ).all()
        updated_job_data['skills'] = [skill.name for skill in updated_job_skills]

        return success_response({"job": updated_job_data}), 200

    @jwt_required()
    @job_ns.doc(security=[{"accesskey": []}])
    @job_ns.arguments(JobPostDelSchema)
    @job_ns.response(200, SuccessResponseSchema)
    @job_ns.response(400, ErrorResponseSchema)
    @job_ns.response(404, ErrorResponseSchema)
    def delete(self, request):
        """
        채용 공고 삭제
        """
        data = request

        job = JobPosting.query.filter_by(title=data['select_post']).first()
        if not job:
            current_app.logger.warning(f"Cannot find job post with title '{data['select_post']}'")
            raise ValidationError("해당 채용 공고를 찾을 수 없습니다.")

        # 관련된 JobPostingSkill 먼저 삭제
        JobPostingSkill.query.filter_by(job_post_id=job.job_post_id).delete()

        # 공고 삭제
        db.session.delete(job)
        db.session.commit()

        return success_response({"message": f"Job({job.title}) deleted successfully"}), 200

@job_ns.route("/search")
class JobSearch(MethodView):
    @job_ns.arguments(JobSearchSchema, location='query')
    @job_ns.response(200, SuccessResponseSchema)
    @job_ns.response(400, ErrorResponseSchema)
    def get(self, args):
        """
        채용 공고 검색
        """
        keyword = args.get('keyword', '').strip()

        if not keyword:
            current_app.logger.warning("Search keyword is neccessary")
            raise ValidationError("검색 키워드가 필요합니다.")
        
        filters = {key: args.get(key) for key in ['keyword']}
        page = args.get('page', 1)
        limit = args.get('limit', 20)

        query = apply_filters(JobPosting.query, filters)
        paginated_result = query.paginate(page=page, per_page=limit, error_out=False)

        jobs_with_skills = add_skills_to_jobs(paginated_result.items)
        pagination = {
            "currentPage": paginated_result.page,
            "totalPages": paginated_result.pages,
            "totalItems": paginated_result.total
        }

        return success_response({"jobs": jobs_with_skills}, pagination), 200

@job_ns.route("/filter")
class JobFilter(MethodView):
    @job_ns.arguments(JobFilterSchema, location='query')
    @job_ns.response(200, SuccessResponseSchema)
    @job_ns.response(400, ErrorResponseSchema)
    def get(self, args):
        """
        채용 공고 필터링
        """
        filters = {key: args.get(key) for key in ['keyword', 'location', 'career_level', 'salary', 'status', 'trend_keywords', 'skills']}
        sort = args.get('sort')
        page = args.get('page', 1)
        limit = args.get('limit', 20)

        query = apply_filters(JobPosting.query, filters)
        query = apply_sorting(query, sort)
        paginated_result = query.paginate(page=page, per_page=limit, error_out=False)

        jobs_with_skills = add_skills_to_jobs(paginated_result.items)
        pagination = {
            "currentPage": paginated_result.page,
            "totalPages": paginated_result.pages,
            "totalItems": paginated_result.total
        }

        return success_response({"jobs": jobs_with_skills}, pagination), 200
        
@job_ns.route("/sort")
class JobSort(MethodView):
    @job_ns.arguments(JobSortSchema, location='query')
    @job_ns.response(200, SuccessResponseSchema)
    @job_ns.response(400, ErrorResponseSchema)
    def get(self, args):
        """
        채용 공고 정렬
        """
        sort = args.get('sort')

        if not sort:
            current_app.logger.warning("Sorting criteria is neccessary")
            raise ValidationError("정렬 기준이 필요합니다.")

        valid_sort_options = ['deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc']
        if sort not in valid_sort_options:
            raise ValidationError("유효하지 않은 정렬 기준입니다.")

        page = args.get('page', 1)
        limit = args.get('limit', 20)

        query = apply_sorting(JobPosting.query, sort)
        paginated_result = query.paginate(page=page, per_page=limit, error_out=False)

        jobs_with_skills = add_skills_to_jobs(paginated_result.items)
        pagination = {
            "currentPage": paginated_result.page,
            "totalPages": paginated_result.pages,
            "totalItems": paginated_result.total
        }

        return success_response({"jobs": jobs_with_skills}, pagination), 200

@job_ns.route("/<int:id>")
class JobDetail(MethodView):
    @job_ns.response(200, SuccessResponseSchema)
    @job_ns.response(404, ErrorResponseSchema)
    def get(self, id):
        """
        단일 채용 공고 상세 조회
        """
        job = JobPosting.query.get(id)
        if not job:
            current_app.logger.warning(f"Cannot find {id} job posts")
            raise ValidationError("해당 채용 공고를 찾을 수 없습니다.")

        job.views += 1  # 조회수 증가
        db.session.commit()

        job_data = job.to_dict()
        job_posting_skills = db.session.query(Skill.name).join(JobPostingSkill).filter(
            JobPostingSkill.job_post_id == job.job_post_id
        ).all()
        job_data['skills'] = [skill.name for skill in job_posting_skills]

        # 관련 공고 추천 로직
        similar_jobs = JobPosting.query.filter(
            JobPosting.company_id == job.company_id,
            JobPosting.job_post_id != id  # 현재 공고는 제외
        ).limit(5).all()

        recommended_jobs = add_skills_to_jobs(similar_jobs)

        return success_response({"job": job_data, "recommended_jobs": recommended_jobs}), 200