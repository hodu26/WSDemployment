from flask import current_app
from flask_smorest import Blueprint as SmorestBlueprint
from flask.views import MethodView
from ..models import db, Company, JobPosting, Skill
from ..schemas import JobCrawlSchema, CompanySchema, SkillSchema, SuccessResponseSchema, ErrorResponseSchema
from ..services import crawl_job_posts, crawl_company_info, update_skills_table, save_job_posting_skills
from ..error_log import success_response, CustomError, ValidationError
from datetime import datetime

crawl_ns = SmorestBlueprint("Crawl", "Crawl", url_prefix="/crawl", description="크롤링 관련 API")

@crawl_ns.route("/update/skills")
class update_skills_table(MethodView):
    @crawl_ns.arguments(SkillSchema)
    @crawl_ns.response(200, SuccessResponseSchema)
    @crawl_ns.response(400, ErrorResponseSchema)
    @crawl_ns.response(500, ErrorResponseSchema)
    def post(self, request):
        """
        기술명을 추가하는 엔드포인트
        """
        data = request
        skill_name = data.get('skill')

        if not skill_name:
            current_app.logger.warning(f"Skill name not provided at {datetime.now()}")
            raise ValidationError("스킬 이름을 제공해주세요.")

        try:
            skill = Skill.query.filter_by(name=skill_name).first()

            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            else:
                skill.name = skill_name
            db.session.commit()

            return success_response({"message": "스킬 정보 업데이트 성공", "skill_name": skill.name}), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating skills at {datetime.now()}: {str(e)}")
            raise CustomError("기술 업데이트 실패", 500)

@crawl_ns.route("/company_info")
class crawl_and_store_company_info(MethodView):
    @crawl_ns.arguments(CompanySchema)
    @crawl_ns.response(200, SuccessResponseSchema)
    @crawl_ns.response(400, ErrorResponseSchema)
    def post(self, request):
        """
        사람인 회사 정보를 크롤링하여 데이터베이스에 저장하는 엔드포인트
        """
        data = request
        print(data)
        company_name = data.get('company_name')
        link = data.get('link')

        if not company_name or not link:
            current_app.logger.warning(f"Company name or link missing in request at {datetime.now()}")
            raise ValidationError("회사명과 링크는 필수입니다.")

        try:
            company_data = crawl_company_info(company_name, link)

            # 데이터베이스에 저장
            saved_companies = []
            for company in company_data:
                existing_company = Company.query.filter_by(name=company['회사명']).first()

                if not existing_company:
                    new_company = Company(
                        name=company['회사명'],
                        company_type=company.get('기업 형태', '정보 없음'),
                        industry=company.get('업종', '정보 없음'),
                        website=company.get('홈페이지', '정보 없음'),
                        address=company.get('주소', '정보 없음'),
                        introduce=company.get('기업 설명', '정보 없음')
                    )
                    db.session.add(new_company)
                    saved_companies.append(new_company)
                    db.session.commit()

            return success_response({
                "message": "회사 정보 크롤링 및 저장 완료",
                "companies": [{"company_name": company.name, "company_type": company.company_type} for company in saved_companies]
            }), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error storing company info at {datetime.now()}: {str(e)}")
            raise CustomError("회사 정보 저장 실패", 500)

@crawl_ns.route("/job_posts")
class get_job_posts(MethodView):
    @crawl_ns.arguments(JobCrawlSchema)
    @crawl_ns.response(200, SuccessResponseSchema)
    @crawl_ns.response(400, ErrorResponseSchema)
    @crawl_ns.response(500, ErrorResponseSchema)
    def post(self, request):
        """
        사람인 키워드별 채용 정보를 크롤링하여 데이터베이스에 저장하는 엔드포인트
        """
        data = request
        keyword = data.get('keyword', 'IT개발·데이터')
        pages = data.get('pages', 1)

        try:
            job_data = crawl_job_posts(keyword, pages)

            # 데이터베이스에 저장
            saved_jobs = []
            for job in job_data:
                # 1. Company 테이블에 회사 이름 확인
                company = Company.query.filter_by(name=job['회사명']).first()
                if not company:
                    # 회사가 없으면 크롤링 API 호출하여 회사 정보 가져오기
                    company_name = job['회사명']
                    company_link = job['회사 정보']  # 회사 링크도 job 데이터에 있어야 합니다.

                    company_data = crawl_company_info(company_name, company_link)

                    if company_data:
                        company_info = company_data[0]

                        # 회사 정보 저장
                        company = Company(
                            name=company_info['회사명'],
                            company_type=company_info.get('기업 형태', '정보 없음'),
                            industry=company_info.get('업종', '정보 없음'),
                            website=company_info.get('홈페이지', '정보 없음'),
                            address=company_info.get('주소', '정보 없음'),
                            introduce=company_info.get('기업 설명', '정보 없음')
                        )
                        db.session.add(company)
                        db.session.commit()

                # 2. JobPosting 중복 확인
                existing_posting = JobPosting.query.filter_by(
                    company_id=company.company_id,
                    title=job['제목']
                ).first()

                if existing_posting:
                    continue

                # 3. JobPosting 테이블에 데이터 저장
                posting = JobPosting(
                    company_id=company.company_id,
                    trend_keywords=job['트렌드_키워드'],
                    title=job['제목'],
                    link=job['공고 링크'],
                    location=job['지역'],
                    career_level=job['경력'],
                    education=job['학력'],
                    employment_type=job['고용형태'],
                    deadline=job['마감일'],
                    salary_range=job['연봉정보'],
                    posted_date=job['작성날짜'],
                    status=job['상태']
                )
                db.session.add(posting)

                # skills 테이블 업데이트
                update_skills_table([job['직무분야']])
                save_job_posting_skills(posting.job_post_id, [job['직무분야']])

                posting.company_name = company.name
                saved_jobs.append(posting)

            db.session.commit()
            return success_response({
                "message": "크롤링 및 데이터 저장 완료",
                "jobs": [{
                    "job_title": job.title,
                    "company_name": job.company_name,
                    "location": job.location
                } for job in saved_jobs],
                "count": len(saved_jobs)
            }), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing job posts at {datetime.now()}: {str(e)}")
            raise CustomError("채용 공고 크롤링 실패", 500)