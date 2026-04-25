from flask import Flask, render_template, send_from_directory
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from socket_events import socketio
from routes.auth import auth_bp
from routes.user import user_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 确保上传目录配置
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

    db.init_app(app)
    JWTManager(app)
    socketio.init_app(app, cors_allowed_origins="*")  # 可加 cors 配置

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    # 提供上传文件的访问
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)