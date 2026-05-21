from flask_admin import Admin,AdminIndexView
from main import app
from flask_admin.contrib.sqla import ModelView
from flask import current_app, redirect, url_for, request, session
from models import db, User, HuiZong, Recommend, UserBehavior, SearchHistory, Comment, CrawlLog

class MyModelView(ModelView):
    def is_accessible(self):
        return session.get('uuid') == 1

    def inaccessible_callback(self, name, **kwargs):
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

class MyUserBehavior(MyModelView):
    column_labels = dict(
        user_id='用户',
        huizong_id='视频',
        behavior_type='行为类型',
        behavior_time='行为时间'
    )
    column_list = ('user_id', 'huizong_id', 'behavior_type', 'behavior_time')

class MySearchHistory(MyModelView):
    column_labels = dict(
        user_id='用户',
        keyword='搜索关键词',
        result_count='结果数量',
        search_time='搜索时间'
    )
    column_list = ('user_id', 'keyword', 'result_count', 'search_time')
    column_searchable_list = ('keyword',)

class MyComment(MyModelView):
    column_labels = dict(
        user_id='用户',
        huizong_id='视频',
        content='评论内容',
        create_time='评论时间'
    )
    column_list = ('user_id', 'huizong_id', 'content', 'create_time')


admin = Admin(app=app, name='后台管理系统',template_mode='bootstrap3', base_template='admin/mybase.html',index_view=AdminIndexView(
        name='导航栏',
        template='admin/welcome.html',
        url='/admin'
    ))

admin.add_view(MyHuiZong(HuiZong, db.session, name='视频数据管理'))
admin.add_view(MyRecommend(Recommend, db.session, name='推荐记录管理'))
admin.add_view(MyUserBehavior(UserBehavior, db.session, name='用户行为管理'))
admin.add_view(MySearchHistory(SearchHistory, db.session, name='搜索历史管理'))
admin.add_view(MyComment(Comment, db.session, name='评论管理'))
admin.add_view(MyUser(User, db.session, name='用户管理'))

class MyCrawlLog(MyModelView):
    column_labels = dict(
        start_time='开始时间', end_time='结束时间', status='状态',
        new_count='新增数量', update_count='更新数量', error_msg='错误信息',
        target_year='目标年份'
    )
    column_list = ('start_time', 'end_time', 'target_year', 'status', 'new_count', 'update_count')
    can_create = False
    can_edit = False

admin.add_view(MyCrawlLog(CrawlLog, db.session, name='爬取记录管理'))

if __name__ == '__main__':
    import atexit
    from apscheduler.schedulers.background import BackgroundScheduler
    from crawler import run_crawl, migrate_db

    migrate_db(app)

    # 清理上次异常中断留下的running状态，并补齐实际新增数量
    with app.app_context():
        stale = CrawlLog.query.filter_by(status='running').all()
        for s in stale:
            s.status = 'error'
            s.error_msg = '服务器重启导致任务中断'
            # 按crawl_id统计实际已入库的条数（逐条提交的数据不会丢失）
            actual = models.HuiZong.query.filter_by(crawl_id=s.id).count()
            if actual > 0:
                s.new_count = actual
        if stale:
            db.session.commit()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(func=lambda: run_crawl(app), trigger='cron', hour=3, minute=0, id='daily_crawl')
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

    app.run(debug=False, use_reloader=False)
