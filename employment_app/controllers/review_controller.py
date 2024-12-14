from flask import current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint as SmorestBlueprint
from flask_restx import Resource
from ..models import db, User, Review
from ..schemas import ReviewSchema, ReviewCompanyIdSchema, SuccessResponseSchema, ErrorResponseSchema
from ..error_log import success_response, AuthenticationError, ValidationError
from sqlalchemy.exc import IntegrityError
from datetime import datetime

review_ns = SmorestBlueprint('Reviews', 'Reviews', url_prefix='/reviews', description="리뷰 관련 API")

@review_ns.route('')
class ReviewAPI(Resource):
    @jwt_required()
    @review_ns.doc(security=[{"accesskey": []}])
    @review_ns.arguments(ReviewSchema)
    @review_ns.response(201, SuccessResponseSchema)
    @review_ns.response(400, ErrorResponseSchema)
    @review_ns.response(401, ErrorResponseSchema)
    def post(self, data):
        """
        회사 리뷰 작성
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            # 로그에 날짜와 시간 포함
            current_app.logger.error(f"[{datetime.now()}] 사용자 인증 실패 - 이메일: {identity}")
            raise AuthenticationError("사용자 인증 실패")

        try:
            new_review = Review(
                user_id=user.user_id,
                company_id=data['company_id'],
                rating=data['rating'],
                review_text=data.get('review_text', '')
            )
            db.session.add(new_review)
            db.session.commit()
            return success_response({"Review": new_review.to_dict()}), 201
        
        except IntegrityError:
            db.session.rollback()
            current_app.logger.error(f"[{datetime.now()}] 데이터 무결성 오류 - 사용자 ID: {user.user_id} - 리뷰 작성 실패")
            raise ValidationError("리뷰 작성 중 데이터 무결성 오류가 발생했습니다.")

    @review_ns.arguments(ReviewCompanyIdSchema, location='query')
    @review_ns.response(200, SuccessResponseSchema)
    @review_ns.response(404, ErrorResponseSchema)
    def get(self, args):
        """
        회사 리뷰 목록 조회
        """
        company_id = args.get('company_id')
        reviews = Review.query.filter_by(company_id=company_id).all() if company_id else Review.query.all()

        if not reviews:
            current_app.logger.error(f"[{datetime.now()}] 해당 조건에 맞는 리뷰 없음 - company_id: {company_id}")
            raise ValidationError("해당 조건에 맞는 리뷰가 없습니다.")

        return success_response({"Reviews": [review.to_dict() for review in reviews]}), 200

@review_ns.route('/<int:id>')
class ReviewDetailAPI(Resource):
    @jwt_required()
    @review_ns.doc(security=[{"accesskey": []}])
    @review_ns.response(200, SuccessResponseSchema)
    @review_ns.response(404, ErrorResponseSchema)
    @review_ns.response(401, ErrorResponseSchema)
    def delete(self, id):
        """
        리뷰 삭제
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"[{datetime.now()}] 사용자 인증 실패 - 이메일: {identity}")
            raise AuthenticationError("사용자 인증 실패")

        review = Review.query.filter_by(review_id=id, user_id=user.user_id).first()
        if not review:
            current_app.logger.error(f"[{datetime.now()}] 리뷰 삭제 실패 - 리뷰 ID: {id} - 권한 없음 또는 리뷰 없음")
            raise ValidationError(f"ID {id}에 해당하는 리뷰가 없거나 권한이 없습니다.")

        db.session.delete(review)
        db.session.commit()
        current_app.logger.info(f"[{datetime.now()}] 리뷰 삭제 성공 - 리뷰 ID: {id}")
        return success_response({"message": f"ID {id} 리뷰가 성공적으로 삭제되었습니다."}), 200
