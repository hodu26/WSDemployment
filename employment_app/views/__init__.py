from flask import Blueprint

main_blueprint = Blueprint('main', __name__)

# 해당 블루프린트에서 사용할 라우트들을 import
from .routes import *