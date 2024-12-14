# OpenAPI 서버 설정
swagger_servers = [
    {"url": "https://api.example.com/v1", "description": "Production Server"},
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