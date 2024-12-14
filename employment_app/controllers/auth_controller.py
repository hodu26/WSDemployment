from flask import request, current_app
from flask_smorest import Api, Blueprint as SmorestBlueprint
from flask.views import MethodView
from ..models import db, User, Token
from ..schemas import RegisterSchema, LoginSchema, ProfileSchema, SuccessResponseSchema, ErrorResponseSchema
from ..extensions import bcrypt, KST
from ..error_log import success_response, AuthenticationError, ValidationError
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import re

auth_ns = SmorestBlueprint("Auth", "Auth", url_prefix="/auth", description="인증 관련 API")

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
class Register(MethodView):
    @auth_ns.arguments(RegisterSchema)
    @auth_ns.response(201, SuccessResponseSchema)
    @auth_ns.response(400, ErrorResponseSchema)
    @auth_ns.response(400, ErrorResponseSchema)
    @auth_ns.response(400, ErrorResponseSchema)
    def post(self, request):
        """
        회원가입 엔드포인트
        """
        data = request
        username = data.get("name")
        email = data.get("email")
        password = data.get("password")

        # 이메일 형식 검증
        if not is_valid_email(email):
            current_app.logger.error(f"Invalid email format: {email} at {datetime.now()}")
            raise ValidationError("올바른 이메일 형식이 아닙니다.")

         # 비밀번호 검증
        if not is_strong_password(password):
            current_app.logger.error(f"Weak password for email: {email} at {datetime.now()}")
            raise ValidationError("비밀번호는 8자리 이상이어야 하며, 최소 한개의 대/소문자를 포함해야하고, 숫자 및 특수기호가 포함되어야 합니다.")

        # 이메일 중복 확인
        if User.query.filter_by(email=email).first():
            current_app.logger.error(f"Email already exists: {email} at {datetime.now()}")
            raise ValidationError("이미 존재하는 이메일입니다.")

        # 비밀번호 해싱 후 사용자 저장
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(name=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"User registered successfully: {username} ({email}) at {datetime.now()}")
        return success_response({
            "user_id": new_user.user_id,
            "name": new_user.name,
            "email": new_user.email
        }), 201

# 로그인
@auth_ns.route("/login")
class Login(MethodView):
    @auth_ns.arguments(LoginSchema)
    @auth_ns.response(200, SuccessResponseSchema)
    @auth_ns.response(401, ErrorResponseSchema)
    def post(self, request):
        """
        로그인 엔드포인트
        """
        data = request
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            current_app.logger.error(f"Failed login attempt for email: {email} at {datetime.now()}")
            raise AuthenticationError("아이디(이메일) 및 비밀번호가 일치하지 않습니다.")

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
        return success_response({"user_id": user.user_id, "access_token": access_token, "refresh_token": refresh_token}), 200



# 토큰 갱신
@auth_ns.route("/refresh")
class RefreshToken(MethodView):
    @jwt_required(refresh=True)
    @auth_ns.doc(security=[{"refreshkey": []}])
    @auth_ns.response(200, SuccessResponseSchema)
    @auth_ns.response(401, ErrorResponseSchema)
    def post(self):
        """
        엑세스토큰 재발급 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()  # 이메일로 User 찾기
        
        if not user:
            current_app.logger.error(f"User not found for email: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")
        
        new_access_token = create_access_token(identity=identity, expires_delta=timedelta(minutes=60))

        # DB에서 기존 토큰 갱신
        token = Token.query.filter_by(user_id=user.user_id).first()
        if token:
            token.access_token = new_access_token
            token.access_expires_at = datetime.now(KST) + timedelta(minutes=60)
            db.session.commit()

        current_app.logger.info(f"Access token refreshed for user {identity} at {datetime.now()}")
        return success_response({"user_id": user.user_id, "access_token": new_access_token}), 200

# 회원 정보 조회 및 삭제
@auth_ns.route("/user")
class UserInfo(MethodView):
    @jwt_required()
    @auth_ns.doc(security=[{"accesskey": []}])
    @auth_ns.response(200, SuccessResponseSchema)
    @auth_ns.response(401, ErrorResponseSchema)
    def get(self):
        """
        유저 정보 조회 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for id: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")

        current_app.logger.info(f"User {user.name} information retrieved successfully at {datetime.now()}")
        return success_response({"user_id": user.user_id, "username": user.name, "email": user.email, "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")}), 200
    
    # 회원 정보 수정
@auth_ns.route("/profile")
class UpdateProfile(MethodView):
    @jwt_required()
    @auth_ns.doc(security=[{"accesskey": []}])
    @auth_ns.arguments(ProfileSchema)
    @auth_ns.response(200, SuccessResponseSchema)
    @auth_ns.response(400, ErrorResponseSchema)
    @auth_ns.response(401, ErrorResponseSchema)
    def put(self, request):
        """
        유저 정보 수정 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for id: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")

        data = request
        if "password" in data:
            if not is_strong_password(data["password"]):
                current_app.logger.error(f"Weak password for email: {user.email} at {datetime.now()}")
                raise ValidationError("비밀번호는 8자리 이상이어야 하며, 최소 한개의 대/소문자를 포함해야하고, 숫자 및 특수기호가 포함되어야 합니다.")
            user.password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        if "name" in data:
            user.name = data["name"]
        db.session.commit()

        current_app.logger.info(f"User {identity} profile updated successfully at {datetime.now()}")
        return success_response({
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "updated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    
    @jwt_required()
    @auth_ns.doc(security=[{"accesskey": []}])
    @auth_ns.response(200, SuccessResponseSchema)
    @auth_ns.response(401, ErrorResponseSchema)
    def delete(self):
        """
        유저 삭제 엔드포인트
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for id: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")

        # 사용자 삭제 (Token은 cascade 옵션으로 자동 삭제됨)
        db.session.delete(user)
        db.session.commit()

        current_app.logger.info(f"User {identity} deleted successfully at {datetime.now()}")
        return success_response({"message": f"User({user.email}) deleted successfully"}), 200