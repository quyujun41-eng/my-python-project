import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # ----- Flask -----
    SECRET_KEY = os.getenv('SECRET_KEY', 'bilibili-analysis-2026-ZxK9mPqR7vNw')

    # ----- 数据库 -----
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'bilibili.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False
    BABEL_DEFAULT_LOCALE = 'zh_CN'

    # ----- B站登录凭据 -----
    # 生产环境通过环境变量注入，本地开发用默认值
    BILIBILI_COOKIE = {
        'SESSDATA':   os.getenv('BILI_SESSDATA',  '3c86f6eb%2C1794896384%2C7eef6%2A51'),
        'bili_jct':   os.getenv('BILI_JCT',       '786321939eb3ad6d516d2b8c975e17f2'),
        'DedeUserID': os.getenv('BILI_UID',        '389155570'),
        'buvid3':     os.getenv('BILI_BUVID3',     'E15A163B-91D5-8DB0-1F1B-1C38D1F2D1E841210infoc'),
    }

    # ----- 爬虫参数 -----
    CRAWL_KEYWORDS = [
        '美食', '游戏', '音乐', '科技', '动画', '生活', '搞笑',
        '知识', '运动', '旅游', '电影', '数码', '时尚', '健康',
        '教育', '宠物', '汽车', '财经', '历史', '编程',
    ]
    CRAWL_MAX_PAGES = 50
    AUTO_CRAWL_HOUR = 3
