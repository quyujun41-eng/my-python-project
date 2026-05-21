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
    # 按 B站官方分区顺序，覆盖全部主分区和子分区（超高清为画质标签，非分区，已跳过）
    CRAWL_PARTITIONS = {
        '番剧':    13,
        '国创':    167,
        '综艺':    71,
        '动画':    1,
        '鬼畜':    119,
        '舞蹈':    129,
        '娱乐':    5,
        '科技数码': 188,
        '美食':    211,
        '汽车':    223,
        '体育运动': 234,
        '电影':    23,
        '电视剧':  11,
        '纪录片':  177,
        '游戏':    4,
        '音乐':    3,
        '影视':    181,
        '知识':    36,
        '资讯':    202,
        '小剧场':  241,
        '时尚美妆': 155,
        '动物':    217,
        '家装房产': 239,
        '旅游出行': 250,
        '情感':    252,
        'vlog':    185,
        '户外潮流': 257,
        '三农':    316,
        '生活兴趣': 253,
        '视频播客': 330,
        '绘画':    161,
        '健身':    164,
        '亲子':    225,
        '生活经验': 254,
        '人工智能': 210,
        '手工':    162,
        '健康':    163,
        '公益':    165,
    }
    CRAWL_MAX_PAGES = 50
    AUTO_CRAWL_HOUR = 3
