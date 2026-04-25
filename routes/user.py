import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename   # 安全处理文件名（虽然这次我们用了uuid，但保留没坏处）
from models import db, User

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """查询自己的个人信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """修改昵称"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()
    new_nickname = data.get('nickname', '').strip()

    if not new_nickname:
        return jsonify({'error': '昵称不能为空'}), 400
    if len(new_nickname) > 20:
        return jsonify({'error': '昵称不能超过20个字符'}), 400

    user.nickname = new_nickname
    db.session.commit()

    # 同步更新 localStorage 里的用户信息（前端负责）
    return jsonify({'message': '昵称修改成功', 'user': user.to_dict()}), 200


@user_bp.route('/profile/password', methods=['PUT'])
@jwt_required()
def update_password():
    """修改密码"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    # 验证旧密码
    if not user.check_password(old_password):
        return jsonify({'error': '原密码错误'}), 400
    if len(new_password) < 6:
        return jsonify({'error': '新密码不能少于6位'}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': '密码修改成功'}), 200


@user_bp.route('/search', methods=['GET'])
@jwt_required()
def search_user():
    """根据用户名查询其他用户信息"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'error': '请输入用户名'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 只返回公开信息，不返回密码hash
    return jsonify({'user': user.to_dict()}), 200

# ============ 头像上传相关 ============

# 允许上传的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否合法"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    # 1. 获取当前登录用户的ID
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 2. 检查是否有文件上传
    if 'avatar' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    # 3. 验证文件类型
    if not allowed_file(file.filename):
        return jsonify({'error': '仅支持 png, jpg, jpeg, gif, webp 格式'}), 400

    # 4. 限制文件大小（这里是 2MB）
    # 我们需要读取文件大小，但不要一次性全读入内存，用以下方法
    file.seek(0, os.SEEK_END)     # 移动光标到文件末尾
    file_length = file.tell()     # 获取当前光标位置（即文件大小）
    file.seek(0)                  # 光标复位到开头，以便后续保存
    if file_length > 2 * 1024 * 1024:   # 2MB = 2 * 1024 * 1024 字节
        return jsonify({'error': '文件不能超过 2MB'}), 400

    # 5. 生成不重复的文件名
    # 获取原始文件扩展名，例如 '.png'
    ext = file.filename.rsplit('.', 1)[1].lower()
    # 使用 uuid 加上扩展名组成新文件名，例如 'a1b2c3d4e5.png'
    filename = f"{uuid.uuid4().hex}.{ext}"

    # 6. 保存文件
    # 从 Flask 配置中获取上传文件夹的绝对路径
    upload_folder = current_app.config['UPLOAD_FOLDER']
    # 如果 uploads 文件夹不存在就创建它（双保险）
    os.makedirs(upload_folder, exist_ok=True)
    # 拼接保存的完整路径：比如 /你的项目/uploads/a1b2c3d4e5.png
    file.save(os.path.join(upload_folder, filename))

    # 7. 更新数据库中的用户头像字段
    user.avatar = filename
    db.session.commit()

    # 8. 返回成功消息和新头像文件名
    return jsonify({
        'message': '头像上传成功',
        'avatar': filename
    }), 200