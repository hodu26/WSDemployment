import logging
from logging.handlers import RotatingFileHandler
from flask import request, jsonify
from datetime import datetime

def configure_logger(app):
    """로깅 설정 함수"""
    log_level = logging.DEBUG if app.config["ENV"] != "prod" else logging.ERROR
    logging.basicConfig(level=log_level)
    
    # 파일 핸들러 설정 (로그를 파일에 저장)
    file_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
    file_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 로거에 파일 핸들러 추가
    app.logger.addHandler(file_handler)

    # 요청 로깅
    @app.before_request
    def log_request():
        app.logger.info(f"Request started: {request.method} {request.url} at {datetime.now()}")

    # 응답 로깅
    @app.after_request
    def log_response(response):
        app.logger.info(f"Response: {response.status_code} at {datetime.now()}")
        return response

    # 에러 로깅
    @app.errorhandler(Exception)
    def log_error(e):
        app.logger.error(f"Error occurred: {str(e)} at {datetime.now()}")
        return jsonify({"message": "An error occurred"}), 500
