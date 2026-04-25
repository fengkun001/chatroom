

class Config:
    # 替换为你的 MySQL 密码
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:yourpassword@localhost/chatroom?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'change-this-to-a-random-string'
    SECRET_KEY = 'change-this-to-another-random-string'