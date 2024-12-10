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
    JWT_SECRET_KEY = os.getenv("SECRET_KEY", "default-jwt-secret-key")  # JWT 비밀 키