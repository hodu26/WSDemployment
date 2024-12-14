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