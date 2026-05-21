# !/usr/bin/env python
# _*_ coding: utf-8 _*_

import flask
from flask_sqlalchemy import SQLAlchemy
import datetime
from sqlalchemy import or_, and_
from flask_babel import Babel

from config import Config

app = flask.Flask(__name__)
app.config.from_object(Config)
babel = Babel(app)

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
    update_time = db.Column(db.DateTime(), nullable=True)
    crawl_id = db.Column(db.Integer, nullable=True)
    data_year = db.Column(db.Integer, nullable=True)
    datetime = db.Column(db.DateTime(), nullable=True, default=datetime.datetime.now)

    recommend = db.relationship("Recommend", backref="huizong")

    def __repr__(self):
        return "<{} 汇总信息>".format(self.title)

class Recommend(db.Model):
    __tablename__ = 'Recommend'

    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    huizong_id = db.Column(db.Integer, db.ForeignKey('HuiZong.id'))
    num = db.Column(db.Float, name='分数')
    datetime = db.Column(db.DateTime(), nullable=True, default=datetime.datetime.now)


class UserBehavior(db.Model):
    """用户行为记录表：记录浏览、点赞、收藏等行为，为推荐算法提供多维度输入"""
    __tablename__ = 'UserBehavior'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    huizong_id = db.Column(db.Integer, db.ForeignKey('HuiZong.id'), nullable=False)
    behavior_type = db.Column(db.String(16), name='行为类型', nullable=False)  # view / like / collect
    behavior_time = db.Column(db.DateTime, default=datetime.datetime.now, name='行为时间')

    user = db.relationship('User', backref='behaviors')
    huizong = db.relationship('HuiZong', backref='behaviors')

    def __repr__(self):
        return "<用户{} {}了视频{}>".format(self.user_id, self.behavior_type, self.huizong_id)


class SearchHistory(db.Model):
    """搜索历史表：记录用户搜索关键词，支持关键字数据统计分析"""
    __tablename__ = 'SearchHistory'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    keyword = db.Column(db.String(128), name='搜索关键词', nullable=False)
    result_count = db.Column(db.Integer, name='结果数量', default=0)
    search_time = db.Column(db.DateTime, default=datetime.datetime.now, name='搜索时间')

    user = db.relationship('User', backref='search_histories')

    def __repr__(self):
        return "<用户{}搜索了:{}>".format(self.user_id, self.keyword)


class Comment(db.Model):
    """评论表：用户对视频发表评论，增加社交互动功能"""
    __tablename__ = 'Comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    huizong_id = db.Column(db.Integer, db.ForeignKey('HuiZong.id'), nullable=False)
    content = db.Column(db.String(500), name='评论内容', nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, name='评论时间')

    user = db.relationship('User', backref='comments')
    huizong = db.relationship('HuiZong', backref='comments')

    def __repr__(self):
        return "<用户{}评论了视频{}>".format(self.user_id, self.huizong_id)


class CrawlLog(db.Model):
    __tablename__ = 'CrawlLog'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_time = db.Column(db.DateTime, name='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, name='结束时间')
    status = db.Column(db.String(16), name='状态')
    new_count = db.Column(db.Integer, default=0, name='新增数量')
    update_count = db.Column(db.Integer, default=0, name='更新数量')
    error_msg = db.Column(db.String(500), nullable=True, name='错误信息')
    target_year = db.Column(db.Integer, nullable=True)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("数据库新表创建完成，原有数据不受影响")
