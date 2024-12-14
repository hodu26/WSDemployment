from flask.views import MethodView
from flask_smorest import Blueprint as SmorestBlueprint
from datetime import datetime
from flask import current_app
from sqlalchemy.orm import joinedload
from ..models import db, Application, JobPosting, User
from ..schemas import ApplicationSchema, ApplicationListSchema, SuccessResponseSchema, ErrorResponseSchema
from ..error_log import success_response, AuthenticationError, ValidationError
from ..services import apply_sorting
from flask_jwt_extended import jwt_required, get_jwt_identity

applications_ns = SmorestBlueprint('Applications', 'Applications', url_prefix='/applications', description="공고 지원 관련 API")

@applications_ns.route("")
class ApplicationStatus(MethodView):
    @jwt_required()
    @applications_ns.doc(security=[{"accesskey": []}])
    @applications_ns.arguments(ApplicationListSchema)
    @applications_ns.response(201, SuccessResponseSchema)
    @applications_ns.response(400, ErrorResponseSchema)
    def post(self, request):
        """
        지원하기
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for email: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")

        job_post_id = request.get("job_post_id")
        
        # 중복 지원 체크
        existing_application = Application.query.filter_by(user_id=user.user_id, job_post_id=job_post_id).first()
        if existing_application:
            current_app.logger.error("already applied position")
            raise ValidationError("이미 지원한 직무입니다.")
        
        job_post = JobPosting.query.get(job_post_id)
        
        # 지원 정보 저장
        application = Application(
            user_id=user.user_id,
            job_post_id=job_post_id,
            company_id=job_post.company_id,
            status="submitted",  # 기본 상태
            resume_url=request.get("resume_url")  # 이력서 첨부 (선택)
        )
        db.session.add(application)
        db.session.commit()

        application_data = application.to_dict()

        # 로그 기록
        current_app.logger.info(f"User {user.name} applied for job posting {job_post_id} at {datetime.now()}")
        
        return success_response({"apply_id": application_data}), 201

    @jwt_required()
    @applications_ns.doc(security=[{"accesskey": []}])
    @applications_ns.arguments(ApplicationSchema, location="query")
    @applications_ns.response(200, SuccessResponseSchema)
    @applications_ns.response(404, ErrorResponseSchema)
    def get(self, request):
        """
        지원 내역 조회
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for email: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")

        status = request.get("status", None)
        page = request.get('page', 1)
        sort_order = request.get('sort', 'desc')
        
        query = Application.query.filter_by(user_id=user.user_id)
        
        if status:
            query = query.filter_by(status=status)

        # 날짜별 정렬 추가
        if sort_order.lower() == 'asc':
            query = query.order_by(Application.applied_at.asc())
        else:
            query = query.order_by(Application.applied_at.desc())

        paginated_result = query.paginate(page=page, per_page=20, error_out=False)
        applications = paginated_result.items
        
        if not applications:
            current_app.logger.error("There are no applies")
            raise ValidationError("지원 내역이 없습니다.")
        
        applications_data = [application.to_dict() for application in applications]

        pagination = {
            "currentPage": paginated_result.page,
            "totalPages": paginated_result.pages,
            "totalItems": paginated_result.total
        }
        
        return success_response({"applications": applications_data}, pagination), 200

@applications_ns.route("/<int:apply_id>")
class ApplicationCancel(MethodView):
    @jwt_required()
    @applications_ns.doc(security=[{"accesskey": []}])
    @applications_ns.response(200, SuccessResponseSchema)
    @applications_ns.response(400, ErrorResponseSchema)
    def delete(self, apply_id):
        """
        지원 취소
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()  # 이메일로 User 찾기
        
        if not user:
            current_app.logger.error(f"User not found for email: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")
        
        application = Application.query.get(apply_id)
        if not application:
            current_app.logger.error("Caanot found applied history")
            raise ValidationError("지원 내역을 찾을 수 없습니다.")
        
        # 취소 가능 여부 확인 (예시로 'submitted' 상태만 취소 가능)
        if application.status != "submitted":
            current_app.logger.error("You can cancelled only in 'submitted' status")
            raise ValidationError("지원 취소는 'submitted' 상태에서만 가능합니다.")
        
        # 상태 업데이트 (취소 상태로 변경)
        application.status = "cancelled"
        db.session.commit()

        current_app.logger.info(f"Application {apply_id} cancelled by user {application.user_id} at {datetime.now()}")

        return success_response({"message": "지원이 취소되었습니다."}), 200

