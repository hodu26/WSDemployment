from flask import current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint as SmorestBlueprint
from flask_restx import Resource
from ..models import db, User, Bookmark
from ..schemas import BookmarkSchema, BookmarkListSchema, SuccessResponseSchema, ErrorResponseSchema
from ..error_log import success_response, AuthenticationError, ValidationError
from sqlalchemy.exc import IntegrityError
from datetime import datetime

bookmark_ns = SmorestBlueprint('Bookmarks', 'Bookmarks', url_prefix='/bookmarks', description="북마크 관련 API")

@bookmark_ns.route('')
class BookmarkToggleAPI(Resource):
    @jwt_required()
    @bookmark_ns.doc(security=[{"accesskey": []}])
    @bookmark_ns.arguments(BookmarkSchema)  # Bookmark 요청 스키마
    @bookmark_ns.response(201, SuccessResponseSchema)
    @bookmark_ns.response(400, ErrorResponseSchema)
    def post(self, request):
        """
        북마크 추가/제거
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            current_app.logger.error(f"User not found for email: {identity} at {datetime.now()}")
            raise AuthenticationError("사용자 인증 실패")

        data = request
        job_post_id = data.get('job_post_id')

        if not job_post_id:
            current_app.logger.error("Job posting ID is required.")
            raise ValidationError("채용 공고 ID가 필요합니다.")

        bookmark = Bookmark.query.filter_by(user_id=user.user_id, job_post_id=job_post_id).first()

        if bookmark:
            bookmark_data = bookmark.to_dict()
            # 북마크 제거
            db.session.delete(bookmark)
            db.session.commit()
            return success_response({"message": "북마크가 제거되었습니다.", "bookmarks": bookmark_data}), 200
        else:
            # 북마크 추가
            new_bookmark = Bookmark(user_id=user.user_id, job_post_id=job_post_id)
            try:
                db.session.add(new_bookmark)
                db.session.commit()
                
                # Bookmark를 직렬화하여 반환
                return success_response({"message": "북마크가 추가되었습니다.", "bookmarks": new_bookmark.to_dict()}), 201
            except IntegrityError:
                db.session.rollback()
                raise ValidationError("중복된 북마크 요청입니다.")
            
@bookmark_ns.route('')
class BookmarkListAPI(Resource):
    @jwt_required()
    @bookmark_ns.doc(security=[{"accesskey": []}])
    @bookmark_ns.arguments(BookmarkListSchema, location="query")
    @bookmark_ns.response(200, SuccessResponseSchema)
    @bookmark_ns.response(404, ErrorResponseSchema)
    def get(self, args):
        """
        북마크 목록 조회
        """
        identity = get_jwt_identity()
        user = User.query.filter_by(email=identity).first()

        if not user:
            raise AuthenticationError("사용자 인증 실패")

        page = args.get('page', 1)
        per_page = 20
        sort_order = args.get('sort', 'desc')  # 'asc' 또는 'desc'

        query = Bookmark.query.filter_by(user_id=user.user_id)

        # 최신순 또는 오래된 순으로 정렬
        if sort_order.lower() == 'asc':
            query = query.order_by(Bookmark.created_at.asc())
        else:
            query = query.order_by(Bookmark.created_at.desc())

        paginated_result = query.paginate(page=page, per_page=per_page, error_out=False)
        bookmarks = paginated_result.items

        bookmarks_data = [
            {"bookmark": bookmark.to_dict()} for bookmark in bookmarks
        ]

        pagination = {
            "currentPage": paginated_result.page,
            "totalPages": paginated_result.pages,
            "totalItems": paginated_result.total
        }

        return success_response({"bookmarks": bookmarks_data}, pagination), 200

