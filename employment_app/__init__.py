from flask import Flask, jsonify
from flask_migrate import Migrate
from config import Config
from flask_smorest import Api
from .views.main_routes import main_blueprint
from .controllers import api_blueprint, init_api
from .models import db # models에 선언된 db 객체 사용
from .schemas import swagger_security_schemes
from .extensions import bcrypt, jwt # 확장 프로그램 사용
from .error_log import configure_error_handlers, configure_logger, monitor_performance
from sqlalchemy.exc import OperationalError
from sqlalchemy import text  # text를 import
from flask_marshmallow import Marshmallow
from redis import Redis  # Redis 임포트

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

    ma = Marshmallow(app)

    # 모델 임포트
    from .models.model import User, Company, JobPosting, Skill, JobPostingSkill, Token, Bookmark, Application

    # 데이터베이스 초기화
    db.init_app(app)
    Migrate(app, db)

    # extensions(확장) 초기화 
    bcrypt.init_app(app)
    jwt.init_app(app)

    # OpenAPI 서버 설정
    swagger_servers = [
        {"url": app.config['SERVER_PATH'], "description": "Production Server"},
        {"url": "http://localhost:5000", "description": "Local Development Server"},
]

    # Swagger API 설정
    api = Api(app)
    api.spec.components.security_schemes.update(swagger_security_schemes)  # 보안 스키마 추가
    api.spec.options["servers"] = swagger_servers  # 서버 추가
    api.spec.options["security"] = [{"accesskey": []}, {"refreshkey": []}]  # 'Authorize' 버튼 활성화

    # 블루프린트 및 네임스페이스 초기화
    init_api(api)  # `api` 객체를 전달하여 네임스페이스 등록

    # 블루프린트 등록
    app.register_blueprint(main_blueprint)  # 기본 라우트 등록
    app.register_blueprint(api_blueprint, url_prefix='/api')  # API 관련 라우트 등록

    # Redis 클라이언트 초기화
    def get_redis_client():
        return Redis(host=app.config['REDIS_HOST'], 
                     port=app.config['REDIS_PORT'], 
                     db=app.config['REDIS_DB'], 
                     password=app.config['REDIS_PASSWORD'], 
                     decode_responses=True)

    # 애플리케이션에 Redis 클라이언트 추가
    app.redis_client = get_redis_client()

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
