from flask import Blueprint, request, jsonify, current_app
from ..models import db, User, Token
from ..extensions import bcrypt, jwt, KST
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import re

auth_bp = Blueprint("auth", __name__)

# 이메일 검증
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# 회원 가입
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # 이메일 형식 검증
    if not is_valid_email(email):
        current_app.logger.error(f"Invalid email format: {email} at {datetime.now()}")
        return jsonify({"message": "Invalid email format"}), 400

    # 비밀번호 길이 검증
    if len(password) < 8:
        current_app.logger.error(f"Password too short for email: {email} at {datetime.now()}")
        return jsonify({"message": "Password must be at least 8 characters"}), 400

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
@auth_bp.route("/login", methods=["POST"])
def login():
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
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
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

# 회원 정보 조회
@auth_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user():
    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first()

    if not user:
        current_app.logger.error(f"User not found for id: {identity} at {datetime.now()}")
        return jsonify({"message": "User not found"}), 404

    current_app.logger.info(f"User {user.name} information retrieved successfully at {datetime.now()}")
    return jsonify({"id": user.user_id, "username": user.name, "email": user.email}), 200

# 회원 정보 수정
@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
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

# 회원 탈퇴
@auth_bp.route("/user", methods=["DELETE"])
@jwt_required()
def delete_user():
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

# 에러 핸들링
@auth_bp.errorhandler(Exception)
def handle_error(e):
    current_app.logger.error(f"Error occurred: {str(e)} at {datetime.now()}")
    return jsonify({"message": "An error occurred"}), 500