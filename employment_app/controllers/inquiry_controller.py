from flask import current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint as SmorestBlueprint
from flask_restx import Resource
from ..models import db, User, Inquiry
from ..schemas import InquirySchema, SuccessResponseSchema, ErrorResponseSchema
from ..error_log import success_response, AuthenticationError, ValidationError
from sqlalchemy.exc import IntegrityError
from datetime import datetime

inquiry_ns = SmorestBlueprint('Inquiry', 'Inquiry', url_prefix='/inquiry', description="문의 관련 API")

@inquiry_ns.route('')
class ChatAPI(Resource):
    @jwt_required()
    @inquiry_ns.doc(security=[{"accesskey": []}])
    @inquiry_ns.arguments(InquirySchema)
    @inquiry_ns.response(201, InquirySchema)
    @inquiry_ns.response(400, ErrorResponseSchema)
    def post(self, data):
        """
        사용자 문의 생성
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"[{datetime.now()}] 사용자 인증 실패 - 이메일: {identity}")
            raise AuthenticationError("사용자 인증 실패")

        try:
            new_inquiry = Inquiry(
                user_id=user.user_id,
                job_post_id=data['job_post_id'],
                title=data['title'],
                message=data['message']
            )
            db.session.add(new_inquiry)
            db.session.commit()
            return success_response({"Inquiry": new_inquiry.to_dict()}), 201
        
        except IntegrityError:
            db.session.rollback()
            current_app.logger.error(f"[{datetime.now()}] 문의 생성 중 IntegrityError 발생.")
            raise ValidationError("중복된 문의 요청입니다.")

    @jwt_required()
    @inquiry_ns.doc(security=[{"accesskey": []}])
    @inquiry_ns.response(200, InquirySchema(many=True))
    @inquiry_ns.response(404, ErrorResponseSchema)
    def get(self):
        """
        사용자 문의 목록 조회
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"[{datetime.now()}] 사용자 인증 실패 - 이메일: {identity}")
            raise AuthenticationError("사용자 인증 실패")

        inquiries = Inquiry.query.filter_by(user_id=user.user_id).all()
        if not inquiries:
            current_app.logger.warning(f"[{datetime.now()}] 문의 목록이 비어 있습니다. 사용자 ID: {user.user_id}")
            raise ValidationError("문의 목록이 없습니다.")

        return success_response({"Inquiries": [inquiry.to_dict() for inquiry in inquiries]}), 200
    
@inquiry_ns.route('/<int:id>')
class InquiryDetailAPI(Resource):
    @jwt_required()
    @inquiry_ns.doc(security=[{"accesskey": []}])
    @inquiry_ns.response(200, SuccessResponseSchema)
    @inquiry_ns.response(404, ErrorResponseSchema)
    def delete(self, id):
        """
        사용자 문의 삭제
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"[{datetime.now()}] 사용자 인증 실패 - 이메일: {identity}")
            raise AuthenticationError("사용자 인증 실패")

        # 삭제할 문의 조회
        inquiry = Inquiry.query.filter_by(inquiry_id=id, user_id=user.user_id).first()
        if not inquiry:
            current_app.logger.error(f"[{datetime.now()}] 문의 삭제 실패 - 존재하지 않거나 권한 없음. 문의 ID: {id}, 사용자 ID: {user.user_id}")
            raise ValidationError(f"ID {id}에 해당하는 문의가 없거나 권한이 없습니다.")

        try:
            db.session.delete(inquiry)
            db.session.commit()
            current_app.logger.info(f"[{datetime.now()}] 문의 삭제 성공. 문의 ID: {id}, 사용자 ID: {user.user_id}")
            return success_response({"message": f"ID {id} 문의가 성공적으로 삭제되었습니다."}), 200
        
        except Exception as e:
            current_app.logger.error(f"[{datetime.now()}] 문의 삭제 중 오류 발생: {str(e)}")
            raise ValidationError("문의 삭제 중 문제가 발생했습니다.")
