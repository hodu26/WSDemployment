from flask import Flask, Blueprint, jsonify
from flask_smorest import Api, Blueprint as SmorestBlueprint
from marshmallow import Schema, fields

# API Blueprint 정의
api_blueprint = Blueprint('api', __name__)

def init_api(main_api):
    from .main_controller import crawl_ns
    from .auth_controller import auth_ns
    from .jobs_controller import job_ns

    main_api.register_blueprint(crawl_ns)
    main_api.register_blueprint(auth_ns)
    main_api.register_blueprint(job_ns)

# # JWT 토큰에 대한 Authorization 설정 (API 보안)
# authorizations = {
#     "accesskey": {
#         "type": "apiKey",
#         "in": "header",
#         "name": "Authorization",
#         "description": "JWT Token (Bearer <token>)"
#     },
#     "refreshkey": {
#         "type": "apiKey",
#         "in": "header",
#         "name": "Authorization",
#         "description": "JWT Token (Bearer <token>)"
#     }
# }
