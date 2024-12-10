from flask import Blueprint

api_blueprint = Blueprint('api', __name__)

from .main_controller import *
from .auth_controller import *

# api_blueprint에 auth_bp 등록
api_blueprint.register_blueprint(auth_bp, url_prefix='/auth')