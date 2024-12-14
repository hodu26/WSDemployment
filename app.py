from employment_app import create_app

if __name__ == "__main__":
    app = create_app()  # create_app() 호출하여 앱 초기화
    app.run(debug=True, host="0.0.0.0", port=8080)  # 서버 실행
