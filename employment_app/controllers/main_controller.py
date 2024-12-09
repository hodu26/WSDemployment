from flask import jsonify, request, current_app
from . import api_blueprint
from ..models import db, User, Company, JobPosting, Skill, JobPostingSkill
from ..schemas.schema import UserSchema
from ..services import crawl_job_posts, crawl_company_info
from datetime import datetime

@api_blueprint.route('/update/skills', methods=['POST'])
def update_skills_table():
    data = request.json
    skill_name = data.get('skill')

    if not skill_name:
        current_app.logger.warning(f"Skill name not provided at {datetime.now()}")
        return jsonify({"message": "스킬 이름을 제공해주세요."}), 400

    try:
        skill = Skill.query.filter_by(name=skill_name).first()

        if not skill:
            skill = Skill(name=skill_name)
            db.session.add(skill)
        else:
            skill.name = skill_name
        db.session.commit()

        return jsonify({"message": "스킬 정보 업데이트 완료"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating skills at {datetime.now()}: {str(e)}")
        return jsonify({"message": "Failed to update skills"}), 500

@api_blueprint.route('/crawl/company_info', methods=['POST'])
def crawl_and_store_company_info():
    """
    사람인 회사 정보를 크롤링하여 데이터베이스에 저장하는 엔드포인트
    """
    data = request.json
    company_name = data.get('company_name')
    link = data.get('link')

    if not company_name or not link:
        current_app.logger.warning(f"Company name or link missing in request at {datetime.now()}")
        return jsonify({"message": "회사명과 링크는 필수입니다."}), 400

    try:
        company_data = crawl_company_info(company_name, link)

        # 데이터베이스에 저장
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
                db.session.commit()

        return jsonify({"message": "회사의 정보 크롤링 및 저장 완료"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error storing company info at {datetime.now()}: {str(e)}")
        return jsonify({"message": "Failed to store company info"}), 500

@api_blueprint.route('/crawl/job_posts', methods=['POST'])
def get_job_posts():
    """
    크롤링 후 데이터를 데이터베이스에 저장하는 엔드포인트
    """

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


    data = request.json
    keyword = data.get('keyword', 'IT개발·데이터')
    pages = data.get('pages', 1)

    try:
        job_data = crawl_job_posts(keyword, pages)

        # 데이터베이스에 저장
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

        db.session.commit()
        return jsonify({"message": "크롤링 및 데이터 저장 완료", "count": len(job_data)}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing job posts at {datetime.now()}: {str(e)}")
        return jsonify({"message": "Failed to process job posts"}), 500