# OpenAPI 서버 설정
swagger_servers = [
    {"url": "http://113.198.66.75:10254", "description": "Production Server"},
    {"url": "http://localhost:5000", "description": "Local Development Server"},
]

# 보안 스키마
swagger_security_schemes = {
    "accesskey": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "JWT Token (Bearer <access-token>)",
    },
    "refreshkey": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "JWT Token (Bearer <refresh-token>)",
    },
}