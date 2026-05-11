# !/usr/bin/env python
# _*_ coding: utf-8 _*_

import flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from sqlalchemy import or_,and_
from flask_babel import Babel



app = flask.Flask(__name__)
babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'


class Config(object):
    """配置参数"""
    # 设置连接数据库的URL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',
                                                  'sqlite:///' + os.path.join(app.root_path, 'bilibili.db'))

    # 设置sqlalchemy自动更跟踪数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # 查询时会显示原始SQL语句
    app.config['SQLALCHEMY_ECHO'] = False
    # 禁止自动提交数据处理
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False
    app.config['SECRET_KEY'] = 'kyes'


# 读取配置
app.config.from_object(Config)

# 创建数据库sqlalchemy工具对象
db = SQLAlchemy(app)


class User(db.Model):
    # 定义表名
    __tablename__ = 'User'
    # 定义字段
    id = db.Column(db.Integer, unique=True, primary_key=True,autoincrement=True)
    name = db.Column(db.String(32),name='用户名')
    email = db.Column(db.String(32),name='邮箱')
    password = db.Column(db.String(32),name='密码')

    recommend = db.relationship("Recommend", backref="user")
    user_datetime = db.Column(db.DateTime, nullable=True, default=datetime.datetime.now)

    def __repr__(self):
        return "<{}账号>".format(self.name)


class HuiZong(db.Model):
    __tablename__ = 'HuiZong'

    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)

    author = db.Column(db.String(124),name='作者')
    url = db.Column(db.String(1240), name='链接')
    description = db.Column(db.String(124), name='简介')
    title = db.Column(db.String(124), name='标题')
    video_review = db.Column(db.Float, name='弹幕量')
    rank_score = db.Column(db.Float, name='播放量')
    pubdate = db.Column(db.DateTime, name='投稿时间')
    favorites = db.Column(db.Float, name='收藏量')
    tag = db.Column(db.String(124), name='分区')
    duration = db.Column(db.Float, name='时长')
    review = db.Column(db.Float, name='评论')
    like = db.Column(db.Float, name='点赞')
    share = db.Column(db.Float, name='转发')
    coin = db.Column(db.Float, name='投币')
    fans = db.Column(db.Float, name='粉丝数')
    datetime = db.Column(db.DateTime(), nullable=True, default=datetime.datetime.now)

    recommend = db.relationship("Recommend", backref="huizong")

    def __repr__(self):
        return "<{} 汇总信息>".format(self.title)

class Recommend(db.Model):
    __tablename__ = 'Recommend'


    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    huizong_id = db.Column(db.Integer, db.ForeignKey('HuiZong.id'))
    num = db.Column(db.Float, name='分数')
    datetime = db.Column(db.DateTime(), nullable=True, default=datetime.datetime.now)



if __name__ == '__main__':
    pass
    db.drop_all()
    db.create_all()


    db.session.add(User(name='admin',email='admin@qq.com',password='root123456'))
    db.session.commit()
