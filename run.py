#!/usr/bin/env python
"""
启动入口：python run.py 或 gunicorn run:app
"""
import atexit
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from models import app, db
import models
import main    # noqa: F401  注册所有路由
import admin   # noqa: F401  注册后台管理视图
from crawler import run_crawl, migrate_db

# 各年份每次爬取新增上限
CRAWL_PLAN = [
    {'target_year': 2023, 'max_records': 5000},
    {'target_year': 2024, 'max_records': 5000},
    {'target_year': 2025, 'max_records': 5000},
    {'target_year': 2026, 'max_records': 3000},
]


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


def _run_all_years():
    """同时爬取多个年份，每个年份一个线程，各自有新增上限"""
    threads = [
        threading.Thread(
            target=run_crawl,
            args=(app,),
            kwargs={'target_year': plan['target_year'], 'max_records': plan['max_records']},
            daemon=True
        )
        for plan in CRAWL_PLAN
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


migrate_db(app)
_cleanup_stale_crawls()

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
    func=_run_all_years,
    trigger='cron',
    hour=Config.AUTO_CRAWL_HOUR,
    minute=30,
    id='daily_crawl',
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
