from flask import request, current_app
from flask_jwt_extended import jwt_required
from flask_restx import Resource
from sqlalchemy.orm import aliased
from . import job_ns
from ..models import db, JobPosting, Company, Skill, JobPostingSkill
from ..schemas import job_post_model, job_post_update_model, job_post_del_model, success_response_model, error_response_model
from ..extensions import JobStatus
from ..error_log import ValidationError, success_response
from datetime import datetime

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
        query = query.filter(JobPosting.job_post_id.in_(subquery))
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
class JobList(Resource):
    @job_ns.expect(job_ns.parser()
                   .add_argument('keyword', type=str, help='키워드 검색 (title, company, position(skill) ...)', default='채용')
                   .add_argument('location', type=str, help='지역 필터링', default='서울')
                   .add_argument('career_level', type=str, help='최소 경력 필터링', default='2년')
                   .add_argument('salary', type=str, help='최소 급여 필터링', default='1000만원')
                   .add_argument('skills', type=str, help='필요한 스킬 리스트 (쉼표로 구분)', default='C++,웹개발')
                   .add_argument('sort', type=str, choices=('deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc'), help='정렬 기준 선택', default='view_desc')
                   .add_argument('page', type=int, help='페이지 번호', default=1)
                   .add_argument('limit', type=int, help='한 페이지당 개수', default=20))
    @job_ns.response(200, 'Success', model=success_response_model)
    @job_ns.response(400, 'Validation Error', model=error_response_model)
    def get(self):
        """
        채용 공고 목록 조회 기능 (검색, 필터링, 정렬, 페이지네이션)
        """
        args = request.args
        filters = {key: args.get(key) for key in ['keyword', 'location', 'career_level', 'salary', 'skills']}
        sort = args.get('sort')
        page = args.get('page', 1, type=int)
        limit = args.get('limit', 20, type=int)

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
    @job_ns.doc(security='accesskey')
    @job_ns.response(201, '채용 공고 등록 성공', model=success_response_model)
    @job_ns.response(400, 'Validation Error', model=error_response_model)
    @job_ns.expect(job_post_model, validate=True)
    def post(self):
        """
        새로운 채용 공고 등록
        """
        data = request.json

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

        deadline=data.get('deadline', '')
        deadline=datetime.strptime(deadline, "%Y-%m-%d").date()

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
            skills = [skill.strip(',').strip() for skill in data['skills'].split()]
            # 새로운 스킬 추가
            for skill_name in skills:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                    db.session.commit()
                job_skill = JobPostingSkill(job_post_id=new_job.job_post_id, skill_id=skill.skill_id)
                db.session.add(job_skill)
            db.session.commit()

        job_data = new_job.to_dict()
        job_data['skills'] = skills

        return success_response({"job": job_data}), 201
    
    @jwt_required()
    @job_ns.doc(security='accesskey')
    @job_ns.expect(job_post_update_model, validate=True)
    @job_ns.response(200, '채용 공고 수정 성공', model=success_response_model)
    @job_ns.response(400, 'Validation Error', model=error_response_model)
    @job_ns.response(404, '해당 채용 공고 없음', model=error_response_model)
    def put(self):
        """
        채용 공고 수정
        """
        data = request.json

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
            deadline=datetime.strptime(data['deadline'], "%Y-%m-%d").date()
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
            skills = [skill.strip(',').strip() for skill in data['skills'].split()]
            # 기존 JobPostingSkill 삭제
            JobPostingSkill.query.filter_by(job_post_id=job.job_post_id).delete()
            db.session.commit()

            # 새로운 스킬 추가
            for skill_name in skills:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                    db.session.commit()
                job_skill = JobPostingSkill(job_post_id=job.job_post_id, skill_id=skill.skill_id)
                db.session.add(job_skill)

        db.session.commit()

        # 업데이트된 공고 정보 반환
        updated_job = JobPosting.query.get(job.job_post_id)
        updated_job_data = updated_job.to_dict()

        # 공고와 연결된 스킬 정보 추가
        updated_job_skills = db.session.query(Skill.name).join(JobPostingSkill).filter(
            JobPostingSkill.job_post_id == updated_job.job_post_id
        ).all()
        updated_job_data['skills'] = [skill.name for skill in updated_job_skills]

        return success_response({"job": updated_job_data}), 200

    @jwt_required()
    @job_ns.doc(security='accesskey')
    @job_ns.expect(job_post_del_model, validate=True)
    @job_ns.response(200, '채용 공고 삭제 성공', model=success_response_model)
    @job_ns.response(400, 'Validation Error', model=error_response_model)
    @job_ns.response(404, '해당 채용 공고 없음', model=error_response_model)
    def delete(self):
        """
        채용 공고 삭제
        """
        data = request.json

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
class JobSearch(Resource):
    @job_ns.expect(job_ns.parser()
                   .add_argument('keyword', type=str, help='키워드 검색 (title, company, position(skill) ...)', default='채용')
                   .add_argument('page', type=int, help='페이지 번호', default=1)
                   .add_argument('limit', type=int, help='한 페이지당 개수', default=20))
    @job_ns.response(200, 'Success', model=success_response_model)
    @job_ns.response(400, 'Validation Error', model=error_response_model)
    def get(self):
        """
        채용 공고 검색
        """
        args = request.args
        keyword = args.get('keyword', '').strip()

        if not keyword:
            current_app.logger.warning("Search keyword is neccessary")
            raise ValidationError("검색 키워드가 필요합니다.")
        
        filters = {key: args.get(key) for key in ['keyword']}
        page = args.get('page', 1, type=int)
        limit = args.get('limit', 20, type=int)

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
class JobFilter(Resource):
    @job_ns.expect(job_ns.parser()
                   .add_argument('keyword', type=str, help='키워드 검색 (title, company, position(skill) ...)', default='채용')
                   .add_argument('location', type=str, help='지역 필터링', default='서울')
                   .add_argument('career_level', type=str, help='최소 경력 필터링', default='2년')
                   .add_argument('salary', type=str, help='최소 급여 필터링', default='1000만원')
                   .add_argument('status', type=JobStatus, help='상태 필터링', choices=[status.value for status in JobStatus], default=JobStatus.OPEN.value)
                   .add_argument('trend_keywords', type=str, help='트렌드 키워드 필터링', default='취업')
                   .add_argument('skills', type=str, help='필요한 스킬 리스트 (쉼표로 구분)', default='C++,웹개발')
                   .add_argument('sort', type=str, choices=('deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc'), help='정렬 기준 선택', default='view_desc')
                   .add_argument('page', type=int, help='페이지 번호', default=1)
                   .add_argument('limit', type=int, help='한 페이지당 개수', default=20))
    @job_ns.response(200, 'Success', model=success_response_model)
    @job_ns.response(400, 'Validation Error', model=error_response_model)
    def get(self):
        """
        채용 공고 필터링
        """
        args = request.args
        filters = {key: args.get(key) for key in ['keyword', 'location', 'career_level', 'salary', 'status', 'trend_keywords', 'skills']}
        sort = args.get('sort')
        page = args.get('page', 1, type=int)
        limit = args.get('limit', 20, type=int)

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
class JobSort(Resource):
    @job_ns.expect(job_ns.parser()
                   .add_argument('sort', type=str, choices=('deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc'), help='정렬 기준 선택', default='view_desc')
                   .add_argument('page', type=int, help='페이지 번호', default=1)
                   .add_argument('limit', type=int, help='한 페이지당 개수', default=20))
    @job_ns.response(200, 'Success', model=success_response_model)
    @job_ns.response(400, 'Validation Error', model=error_response_model)
    def get(self):
        """
        채용 공고 정렬
        """
        args = request.args
        sort = args.get('sort')

        if not sort:
            current_app.logger.warning("Sorting criteria is neccessary")
            raise ValidationError("정렬 기준이 필요합니다.")

        valid_sort_options = ['deadline_asc', 'deadline_desc', 'posted_date_desc', 'view_desc', 'salary_asc', 'salary_desc']
        if sort not in valid_sort_options:
            raise ValidationError("유효하지 않은 정렬 기준입니다.")

        page = args.get('page', 1, type=int)
        limit = args.get('limit', 20, type=int)

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
class JobDetail(Resource):
    @job_ns.response(200, 'Success', model=success_response_model)
    @job_ns.response(404, '해당 채용 공고 없음', model=error_response_model)
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