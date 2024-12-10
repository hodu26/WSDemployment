from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import pytz

# bycrpt 초기화
bcrypt = Bcrypt()

#jwt 초기화
jwt = JWTManager()

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')
