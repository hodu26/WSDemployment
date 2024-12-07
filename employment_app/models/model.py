from . import db

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)
    updated_at = db.Column(db.TIMESTAMP)


class Company(db.Model):
    __tablename__ = 'companies'
    company_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    company_type = db.Column(db.String(255), nullable=True)
    industry = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    introduce = db.Column(db.Text, nullable=True)


class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    job_post_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'), nullable=False)
    trend_keywords = db.Column(db.String(256)) 
    title = db.Column(db.String(128), nullable=False) 
    link = db.Column(db.String(256))
    location = db.Column(db.String(32))
    career_level = db.Column(db.String(64)) 
    education = db.Column(db.String(64))
    employment_type = db.Column(db.String(64))
    deadline = db.Column(db.Date) 
    salary_range = db.Column(db.String(64)) 
    posted_date = db.Column(db.Date) 
    status = db.Column(db.Enum('open', 'closed', name='job_status'))


class Skill(db.Model):
    __tablename__ = 'skills'
    skill_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)


class JobPostingSkill(db.Model):
    __tablename__ = 'job_posting_skills'
    job_post_id = db.Column(db.Integer, db.ForeignKey('job_postings.job_post_id'), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.skill_id'), primary_key=True)


class Token(db.Model):
    __tablename__ = 'tokens'
    token_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    access_token = db.Column(db.String(64), nullable=False)
    refresh_token = db.Column(db.String(64), nullable=False)
    access_expires_at = db.Column(db.TIMESTAMP, nullable=False)
    refresh_expires_at = db.Column(db.TIMESTAMP, nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    bookmark_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    job_post_id = db.Column(db.Integer, db.ForeignKey('job_postings.job_post_id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)


class Application(db.Model):
    __tablename__ = 'applications'
    apply_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    job_post_id = db.Column(db.Integer, db.ForeignKey('job_postings.job_post_id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'), nullable=False)
    status = db.Column(db.Enum('submitted', 'reviewed', 'accepted', 'rejected', name='application_status'))
    applied_at = db.Column(db.TIMESTAMP, nullable=False)
    resume_url = db.Column(db.String(128))