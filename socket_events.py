from flask_socketio import SocketIO, emit, disconnect
from flask_jwt_extended import decode_token
from models import db, User, Message


# 原来的
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

# 更改之后,导致登录失败
#socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)

# 记录在线用户 {socket_id: user_id}
online_users = {}

@socketio.on('connect')
def handle_connect(auth):
    token = auth.get('token') if auth else None
    if not token:
        disconnect()
        return
    try:
        from flask import request
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
        user = User.query.get(user_id)
        if not user:
            disconnect()
            return
        online_users[request.sid] = user_id

        # 推送最近100条历史消息
        history = Message.query.order_by(
            Message.created_at.asc()
        ).limit(100).all()
        emit('history', [msg.to_dict() for msg in history])

        # 广播上线通知
        emit('system', {
            'message': f'{user.nickname} 加入了聊天室',
            'online_count': len(online_users)
        }, broadcast=True)

    except Exception as e:
        print(f'连接错误: {e}')
        disconnect()

@socketio.on('disconnect')
def handle_disconnect():
    from flask import request
    user_id = online_users.pop(request.sid, None)
    if user_id:
        user = User.query.get(user_id)
        if user:
            emit('system', {
                'message': f'{user.nickname} 离开了聊天室',
                'online_count': len(online_users)
            }, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    from flask import request
    user_id = online_users.get(request.sid)
    if not user_id:
        emit('error', {'message': '请先登录'})
        return
    content = data.get('content', '').strip()
    if not content or len(content) > 1000:
        return
    message = Message(user_id=user_id, content=content)
    db.session.add(message)
    db.session.commit()
    emit('new_message', message.to_dict(), broadcast=True)