from . import db
from datetime import datetime
from sqlalchemy import DateTime
from ..extensions import KST

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(16), nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.now(KST), nullable=False)  # 삽입 시 기본값
    updated_at = db.Column(DateTime, default=lambda: datetime.now(KST), onupdate=lambda: datetime.now(KST), nullable=False)  # 수정 시 갱신
    tokens = db.relationship('Token', backref='user', cascade='all, delete')


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
    views = db.Column(db.Integer, default=0)

    def to_dict(self):
        """Convert the JobPosting object to a dictionary."""
        return {
            'job_post_id': self.job_post_id,
            'company_id': self.company_id,
            'trend_keywords': self.trend_keywords,
            'title': self.title,
            'link': self.link,
            'location': self.location,
            'career_level': self.career_level,
            'education': self.education,
            'employment_type': self.employment_type,
            'deadline': self.deadline.isoformat() if self.deadline else None,  # Handle dates properly
            'salary_range': self.salary_range,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,  # Handle dates properly
            'status': self.status,
            'views': self.views
        }


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
    access_token = db.Column(db.String(512), nullable=False)
    refresh_token = db.Column(db.String(512), nullable=False)
    access_expires_at = db.Column(db.TIMESTAMP, nullable=False)
    refresh_expires_at = db.Column(db.TIMESTAMP, nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.now(KST), nullable=False)


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    bookmark_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    job_post_id = db.Column(db.Integer, db.ForeignKey('job_postings.job_post_id'), nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.now(KST), nullable=False)


class Application(db.Model):
    __tablename__ = 'applications'
    apply_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    job_post_id = db.Column(db.Integer, db.ForeignKey('job_postings.job_post_id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id'), nullable=False)
    status = db.Column(db.Enum('submitted', 'reviewed', 'accepted', 'rejected', name='application_status'))
    applied_at = db.Column(DateTime, default=lambda: datetime.now(KST), onupdate=lambda: datetime.now(KST), nullable=False)
    resume_url = db.Column(db.String(128))