from flask import Blueprint
from flask_restx import Api

api_blueprint = Blueprint('api', __name__)

main_api = Api(api_blueprint, title="WD_employment_3", version="1.0", description="웹서비스 설계 과제 3", doc="/api-docs")

from .main_controller import *
from .auth_controller import *

# # api_blueprint에 auth_bp 등록
# api_blueprint.register_blueprint(auth_bp, url_prefix='/auth')