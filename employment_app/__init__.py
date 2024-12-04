from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from employment_app.views.route import main_blueprint
from employment_app.apis.api import api_blueprint
from sqlalchemy.exc import OperationalError
from sqlalchemy import text  # text를 import

# DB 객체 생성
db = SQLAlchemy()

def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    
    # Flask 앱 초기화
    app = Flask(
        __name__,
        template_folder="templates",  # templates 폴더 경로
        static_folder="static"        # static 폴더 경로
    )

    # Flask 설정을 로드합니다.
    app.config.from_object(Config)

    # 데이터베이스 초기화
    db.init_app(app)
    Migrate(app, db)

    # 블루프린트 등록
    app.register_blueprint(main_blueprint)  # 기본 라우트 등록
    app.register_blueprint(api_blueprint, url_prefix='/api')  # API 관련 라우트 등록

    # 데이터베이스 연결 확인
    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))  # 데이터베이스 연결 확인 쿼리
            print("Database connected successfully!")
        except OperationalError as e:
            print("Database connection failed:", e)

    return app
