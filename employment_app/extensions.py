from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import pytz
from enum import Enum

# bycrpt 초기화
bcrypt = Bcrypt()

#jwt 초기화
jwt = JWTManager()

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 채용 공고 상태 설정
class JobStatus(Enum):
    OPEN = 'open'
    CLOSED = 'closed'

# 공고 지원 상태 설정
class ApplicationStatus(Enum):
    SUBMIT = 'submitted'
    REVIEW = 'reviewed'
    ACCEPT = 'accepted'
    REJECT = 'rejected'
    CANCEL = 'cancelled'