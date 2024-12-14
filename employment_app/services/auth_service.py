import re

# 이메일 검증
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# 비밀번호 검증
def is_strong_password(password):
    return (len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'[0-9]', password) and
            re.search(r'[!@#$%^&*(),.?":{}|<>]', password))