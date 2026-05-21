#!/usr/bin/env python
"""
启动入口：python run.py
"""
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from models import app, db
import models
import main    # noqa: F401  注册所有路由
import admin   # noqa: F401  注册后台管理视图
from crawler import run_crawl, migrate_db


def _cleanup_stale_crawls():
    with app.app_context():
        stale = models.CrawlLog.query.filter_by(status='running').all()
        for s in stale:
            s.status = 'error'
            s.error_msg = '服务器重启导致任务中断'
            actual = models.HuiZong.query.filter_by(crawl_id=s.id).count()
            if actual > 0:
                s.new_count = actual
        if stale:
            db.session.commit()


if __name__ == '__main__':
    migrate_db(app)
    _cleanup_stale_crawls()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=lambda: run_crawl(app),
        trigger='cron',
        hour=Config.AUTO_CRAWL_HOUR,
        minute=0,
        id='daily_crawl',
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

    app.run(debug=False, use_reloader=False)
