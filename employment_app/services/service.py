from ..models import db, Skill, JobPostingSkill

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