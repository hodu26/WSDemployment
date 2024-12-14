from sqlalchemy import select
from sqlalchemy.orm import aliased
from ..models import db, JobPosting, Company, Skill, JobPostingSkill

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