from marshmallow import Schema, fields, validate

## 요청 스키마

# auth ns
class RegisterSchema(Schema):
    name = fields.String(required=True, description='사용자 이름', example='홍길동')
    email = fields.String(required=True, description='이메일(아이디)', example='hong@example.com')
    password = fields.String(
        required=True,
        description='비밀번호 (대.소문자 1개 이상, 숫자 포함, 특수기호 포함, 8자리 이상)',
        example='Password123!',
        validate=validate.Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    )

class LoginSchema(Schema):
    email = fields.String(required=True, description='이메일(아이디)', example='hong@example.com')
    password = fields.String(required=True, description='비밀번호', example='Password123!')

class ProfileSchema(Schema):
    name = fields.String(required=True, description='변경할 사용자 이름', example='김철수')
    password = fields.String(
        required=True,
        description='변경할 비밀번호 (대.소문자 1개 이상, 특수기호 포함, 8자리 이상)',
        example='NewPassword!123',
        validate=validate.Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    )