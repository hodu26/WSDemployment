from flask import Blueprint

# API Blueprint 정의
api_blueprint = Blueprint('api', __name__)

def init_api(main_api):
    from .main_controller import crawl_ns
    from .auth_controller import auth_ns
    from .jobs_controller import job_ns
    from .application_controller import applications_ns
    from .bookmark_controller import bookmark_ns
    from .inquiry_controller import inquiry_ns
    from .review_controller import review_ns

    main_api.register_blueprint(crawl_ns)
    main_api.register_blueprint(auth_ns)
    main_api.register_blueprint(job_ns)
    main_api.register_blueprint(applications_ns)
    main_api.register_blueprint(bookmark_ns)
    main_api.register_blueprint(inquiry_ns)
    main_api.register_blueprint(review_ns)