from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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