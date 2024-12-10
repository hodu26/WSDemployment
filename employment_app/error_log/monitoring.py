from flask import request
import time

def monitor_performance(app):
    """성능 모니터링 설정 함수"""
    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def log_request_duration(response):
        duration = time.time() - request.start_time
        app.logger.info(f"Request took {duration:.2f} seconds.")
        return response
