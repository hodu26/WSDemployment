from flask import Blueprint, render_template

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def main():
    return render_template('main.html')

@main_blueprint.route("/detail/<int:job_id>")
def detail(job_id):
    # 예시 데이터 (실제 데이터베이스 연동 필요)
    job_data = {
        "job_title": "Software Engineer",
        "company": "Tech Innovators Inc.",
        "description": "We are looking for a skilled software engineer to join our dynamic team.",
        "requirements": ["Proficient in Python", "Experience with Flask", "Understanding of REST APIs"]
    }
    return render_template("detail.html", **job_data)