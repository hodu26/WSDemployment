from flask import request, jsonify, current_app
from flask_restx import Namespace, Resource, fields
from . import main_api
from ..models import db, User, Token
from ..extensions import bcrypt, KST
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import re

# Namespace 생성
auth_ns = Namespace("auth", description="인증 관련 api")

# 사용되는 모델 선언
register_model = main_api.model('Register', {
    'name': fields.String(required=True, description='사용자 이름'),
    'email': fields.String(required=True, description='이메일(아이디)'),
    'password': fields.String(required=True, description='비밀번호 (대.소문자 1개 이상, 특수기호 포함, 8자리 이상)')
})

login_model = main_api.model('Login', {
    'email': fields.String(required=True, description='이메일(아이디)'),
    'password': fields.String(required=True, description='비밀번호')
})

profile_model = main_api.model('Profile', {
    'name': fields.String(required=True, description='변경할 사용자 이름'),
    'password': fields.String(required=True, description='변경할 비밀번호 (대.소문자 1개 이상, 특수기호 포함, 8자리 이상)')
})


# 이메일 검증
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# 비밀번호 검증
def is_strong_password(password):
    return (len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'[0-9]', password) and
            re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

# 회원 가입
@auth_ns.route("/register")
class Register(Resource):
    @main_api.expect(register_model)
    def post(self):
        """
        회원가입 엔드포인트
        """
        data = request.json
        username = data.get("name")
        email = data.get("email")
        password = data.get("password")

        # 이메일 형식 검증
        if not is_valid_email(email):
            current_app.logger.error(f"Invalid email format: {email} at {datetime.now()}")
            return jsonify({"message": "Invalid email format"}), 400

         # 비밀번호 검증
        if not is_strong_password(password):
            current_app.logger.error(f"Weak password for email: {email} at {datetime.now()}")
            return jsonify({"message": "Password must include at least one uppercase letter, one lowercase letter, one digit, and one special character"}), 400

        # 이메일 중복 확인
        if User.query.filter_by(email=email).first():
            current_app.logger.error(f"Email already exists: {email} at {datetime.now()}")
            return jsonify({"message": "Email already exists"}), 400

        # 비밀번호 해싱 후 사용자 저장
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(name=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"User registered successfully: {username} ({email}) at {datetime.now()}")
        return jsonify({"message": "User registered successfully"}), 201

# 로그인
@auth_ns.route("/login")
class Login(Resource):
    @main_api.expect(login_model)
    def post(self):
        """
        로그인 엔드포인트
        """
        data = request.json
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            # 실패 이력 로깅
            current_app.logger.error(f"Failed login attempt for email: {email} at {datetime.now()}")
            return jsonify({"message": "Invalid credentials"}), 401

        access_token = create_access_token(identity=str(user.email))
        refresh_token = create_refresh_token(identity=str(user.email))

        # 토큰 만료 시간 설정
        access_expires_at = datetime.now(KST) + timedelta(minutes=60)
        refresh_expires_at = datetime.now(KST) + timedelta(days=7)

        # DB에서 기존 토큰 갱신 또는 새로 생성
        token = Token.query.filter_by(user_id=user.user_id).first()
        if token:
            token.access_token = access_token
            token.refresh_token = refresh_token
            token.access_expires_at = access_expires_at
            token.refresh_expires_at = refresh_expires_at
        else:
            new_token = Token(user_id=user.user_id, access_token=access_token, refresh_token=refresh_token,
                            access_expires_at=access_expires_at, refresh_expires_at=refresh_expires_at)
            db.session.add(new_token)

        db.session.commit()

        current_app.logger.info(f"User {user.name} signed in successfully at {datetime.now()}")
        return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200

# 토큰 갱신
@auth_ns.route("/refresh")
class RefreshToken(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """
        엑세스토큰 재발급 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()  # 이메일로 User 찾기
        
        if not user:
            current_app.logger.error(f"User not found for email: {identity} at {datetime.now()}")
            return jsonify({"message": "User not found"}), 404
        
        new_access_token = create_access_token(identity=identity, expires_delta=timedelta(minutes=60))

        # DB에서 기존 토큰 갱신
        token = Token.query.filter_by(user_id=user.user_id).first()
        if token:
            token.access_token = new_access_token
            token.access_expires_at = datetime.now(KST) + timedelta(minutes=60)
            db.session.commit()

        current_app.logger.info(f"Access token refreshed for user {identity} at {datetime.now()}")
        return jsonify({"access_token": new_access_token}), 200

# 회원 정보 조회 및 삭제
@auth_ns.route("/user")
class UserInfo(Resource):
    @jwt_required()
    def get(self):
        """
        유저 정보 조회 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for id: {identity} at {datetime.now()}")
            return jsonify({"message": "User not found"}), 404

        current_app.logger.info(f"User {user.name} information retrieved successfully at {datetime.now()}")
        return jsonify({"id": user.user_id, "username": user.name, "email": user.email}), 200
    
    @jwt_required()
    def delete(self):
        """
        유저 삭제 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for id: {identity} at {datetime.now()}")
            return jsonify({"message": "User not found"}), 404

        # 사용자 삭제 (Token은 cascade 옵션으로 자동 삭제됨)
        db.session.delete(user)
        db.session.commit()

        current_app.logger.info(f"User {identity} deleted successfully at {datetime.now()}")
        return jsonify({"message": "User deleted successfully"}), 200

# 회원 정보 수정
@auth_ns.route("/profile")
class UpdateProfile(Resource):
    @jwt_required()
    @main_api.expect(profile_model)
    def put(self):
        """
        유저 정보 수정 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for id: {identity} at {datetime.now()}")
            return jsonify({"message": "User not found"}), 404

        data = request.json
        if "password" in data:
            if len(data["password"]) < 8:
                current_app.logger.error(f"Password too short for user: {identity} at {datetime.now()}")
                return jsonify({"message": "Password must be at least 8 characters"}), 400
            user.password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        if "name" in data:
            user.name = data["name"]
        db.session.commit()

        current_app.logger.info(f"User {identity} profile updated successfully at {datetime.now()}")
        return jsonify({"message": "Profile updated successfully"}), 200
    
# Namespace 등록
main_api.add_namespace(auth_ns)

# 에러 핸들링
@auth_ns.errorhandler(Exception)
def handle_error(e):
    current_app.logger.error(f"Error occurred: {str(e)} at {datetime.now()}")
    return jsonify({"message": "An error occurred"}), 500