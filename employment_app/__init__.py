from flask import Flask
from flask_migrate import Migrate
from config import Config
from flask_restx import Api
from .views.main_routes import main_blueprint
from .controllers import api_blueprint, main_api
from .models import db # models에 선언된 db 객체 사용
from .extensions import bcrypt, jwt # 확장 프로그램 사용
from .error_log import configure_error_handlers, configure_logger, monitor_performance
from sqlalchemy.exc import OperationalError
from sqlalchemy import text  # text를 import

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

    # 모델 임포트
    from .models.model import User, Company, JobPosting, Skill, JobPostingSkill, Token, Bookmark, Application

    # 데이터베이스 초기화
    db.init_app(app)
    Migrate(app, db)

    # extensions(확장) 초기화 
    bcrypt.init_app(app)
    jwt.init_app(app)

    # PROPAGATE_EXCEPTIONS 설정
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['RESTX_MASK_SWAGGER'] = False

    # Swagger API 설정
    api = main_api

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

    # 로깅 설정
    configure_logger(app)

    # 성능 모니터링
    monitor_performance(app)

    # 에러 핸들러 설정
    configure_error_handlers(app)

    return app
