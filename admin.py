from flask_admin import Admin,AdminIndexView
from main import app
from flask_admin.contrib.sqla import ModelView
from flask import current_app,redirect,url_for,request
from models import db,User,HuiZong,Recommend

class MyModelView(ModelView):
    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

class MyUser(MyModelView):
    column_labels = dict(
        name='账号',
        email='邮箱',
        pwd='密码'
    )

class MyHuiZong(MyModelView):
    column_labels = dict(
        author = '作者',
        url = '链接',
        description = '简介',
        title = '标题',
        video_review = '弹幕量',
        rank_score = '播放量',
        pubdate = '投稿时间',
        favorites = '收藏量',
        tag = '分区',
        duration = '时长',
        review = '评论',
        like = '点赞',
        share = '转发',
        coin = '投币',
        fans = '粉丝数',
    )
    column_list = ('author', 'description', 'title', 'video_review', 'rank_score', 'pubdate', 'favorites', 'tag', 'duration', 'review')
    column_searchable_list = ('author', 'title', 'description', 'tag')

class MyRecommend(MyModelView):
    column_labels = dict(
        user_id = '用户',
        huizong_id = '视频',
        num = '分数'
    )


admin = Admin(app=app, name='后台管理系统',template_mode='bootstrap3', base_template='admin/mybase.html',index_view=AdminIndexView(
        name='导航栏',
        template='admin/welcome.html',
        url='/admin'
    ))

admin.add_view(MyHuiZong(HuiZong, db.session,name='数据管理'))
admin.add_view(MyRecommend(Recommend, db.session,name='用户行为数据管理'))
admin.add_view(MyUser(User, db.session,name='用户管理'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
