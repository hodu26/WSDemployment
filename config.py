import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class Config:
    ENV = os.getenv("ENV", "prod")
    # PostgreSQL 연결 정보
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{os.getenv('DB_USER', 'username')}:"
        f"{os.getenv('DB_PASSWORD', 'password')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'database_name')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

    # JWT 설정
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", "your_jwt_secret_key")  # JWT 인증용 시크릿 키
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # 액세스 토큰 만료 시간 (초)
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 86400))  # 리프레시 토큰 만료 시간 (초)
    JWT_TOKEN_LOCATION = ["headers"]  # 토큰을 헤더에서 읽음
    JWT_HEADER_NAME = "Authorization"  # JWT 토큰의 헤더 이름
    JWT_HEADER_TYPE = "Bearer"  # JWT 토큰 타입 (Bearer)

    # Swagger/OpenAPI 설정
    API_TITLE = "Swagger UI"
    API_VERSION = "1.0.0"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_JSON_PATH = "swagger.json"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest/"
    OPENAPI_SWAGGER_UI_CONFIG = {
        "docExpansion": "list",  # 문서 확장 설정
        "filter": True,  # 검색 창 활성화
    }
    SERVER_PATH = os.getenv("SERVER_PATH", "http://localhost:5000")

    # 추가 설정 (필요 시)
    PROPAGATE_EXCEPTIONS = True