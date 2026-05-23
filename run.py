#!/usr/bin/env python
"""
启动入口：python run.py 或 gunicorn run:app
"""
import atexit
import datetime
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from models import app, db
import models
import main    # noqa: F401  注册所有路由
import admin   # noqa: F401  注册后台管理视图
from crawler import run_crawl, migrate_db, KEYWORDS

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
    """同时爬取多个年份，历史年份只爬与当前同期的月份范围"""
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year

    def kwargs_for(plan):
        year = plan['target_year']
        em = current_month if year < current_year else None
        max_rec = plan['max_records']
        # 每分区上限 = 总量 / 分区数，保证各分区数据均匀
        per_kw = max(1, max_rec // len(KEYWORDS))
        return {'target_year': year, 'max_records': max_rec, 'end_month': em, 'max_per_keyword': per_kw}

    threads = [
        threading.Thread(target=run_crawl, args=(app,), kwargs=kwargs_for(plan), daemon=True)
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
    minute=53,
    id='daily_crawl',
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, host='0.0.0.0')
