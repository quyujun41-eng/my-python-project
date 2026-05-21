import calendar
import requests
import time
import hashlib
import datetime
import urllib.parse
from functools import reduce

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52
]

KEYWORDS = [
    '美食', '游戏', '音乐', '科技', '动画', '生活', '搞笑',
    '知识', '运动', '旅游', '电影', '数码', '时尚', '健康',
    '教育', '宠物', '汽车', '财经', '历史', '编程'
]

BILIBILI_COOKIE = {
    'SESSDATA': '3c86f6eb%2C1794896384%2C7eef6%2A51',
    'bili_jct': '786321939eb3ad6d516d2b8c975e17f2',
    'DedeUserID': '389155570',
    'buvid3': 'E15A163B-91D5-8DB0-1F1B-1C38D1F2D1E841210infoc',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}


def _fetch_fans(sess, mid, cache):
    """Fetch follower count for a Bilibili user by mid, with caching."""
    if not mid:
        return 0
    if mid in cache:
        return cache[mid]
    try:
        resp = sess.get(
            'https://api.bilibili.com/x/relation/stat',
            params={'vmid': mid},
            headers=HEADERS,
            timeout=6
        )
        fans = resp.json().get('data', {}).get('follower', 0) or 0
        cache[mid] = fans
        time.sleep(0.1)
        return fans
    except Exception:
        cache[mid] = 0
        return 0


def _get_mixin_key(orig: str) -> str:
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, '')[:32]


def _sign_params(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_key = _get_mixin_key(img_key + sub_key)
    params = dict(params)
    params['wts'] = round(time.time())
    params = dict(sorted(params.items()))
    params = {k: ''.join(c for c in str(v) if c not in "!'()*") for k, v in params.items()}
    query = urllib.parse.urlencode(params)
    params['w_rid'] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return params


def _year_timestamps(year):
    """返回指定年份在CST(UTC+8)时区的起止Unix时间戳。"""
    begin_utc = datetime.datetime(year, 1, 1, 0, 0, 0) - datetime.timedelta(hours=8)
    end_utc = datetime.datetime(year, 12, 31, 23, 59, 59) - datetime.timedelta(hours=8)
    return calendar.timegm(begin_utc.timetuple()), calendar.timegm(end_utc.timetuple())


def _get_wbi_keys(session):
    resp = session.get('https://api.bilibili.com/x/web-interface/nav', timeout=10)
    wbi_img = resp.json()['data']['wbi_img']
    img_key = wbi_img['img_url'].rsplit('/', 1)[1].split('.')[0]
    sub_key = wbi_img['sub_url'].rsplit('/', 1)[1].split('.')[0]
    return img_key, sub_key


def _search_page(session, keyword, page, img_key, sub_key, pubtime_begin=None, pubtime_end=None):
    base = {
        'search_type': 'video',
        'keyword': keyword,
        'page': page,
        'page_size': 20,
        'order': 'totalrank',
    }
    if pubtime_begin:
        base['pubtime_begin_s'] = pubtime_begin
    if pubtime_end:
        base['pubtime_end_s'] = pubtime_end
    params = _sign_params(base, img_key, sub_key)
    resp = session.get(
        'https://api.bilibili.com/x/web-interface/search/type',
        params=params,
        timeout=10,
    )
    return resp.json()


def _parse_duration(dur_str) -> float:
    try:
        parts = str(dur_str).split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return 0


def _clean_title(title: str) -> str:
    return title.replace('<em class="keyword">', '').replace('</em>', '').strip()


def migrate_db(app):
    """Add new columns to HuiZong/CrawlLog if they don't exist, and backfill data_year."""
    from sqlalchemy import text
    from models import db
    with app.app_context():
        with db.engine.connect() as conn:
            for col_sql in [
                'ALTER TABLE HuiZong ADD COLUMN update_time DATETIME',
                'ALTER TABLE HuiZong ADD COLUMN crawl_id INTEGER',
                'ALTER TABLE HuiZong ADD COLUMN data_year INTEGER',
                'ALTER TABLE CrawlLog ADD COLUMN target_year INTEGER',
            ]:
                try:
                    conn.execute(text(col_sql))
                    conn.commit()
                except Exception:
                    pass
            # 回填旧数据的 data_year：无 update_time 的标为2023，有 update_time 的取年份
            try:
                conn.execute(text(
                    "UPDATE HuiZong SET data_year = 2023 "
                    "WHERE data_year IS NULL AND update_time IS NULL"
                ))
                conn.execute(text(
                    "UPDATE HuiZong SET data_year = CAST(strftime('%Y', update_time) AS INTEGER) "
                    "WHERE data_year IS NULL AND update_time IS NOT NULL"
                ))
                conn.commit()
            except Exception:
                pass


def run_crawl(app, stop_event=None, target_year=None):
    """Main crawl entry point.
    stop_event: threading.Event to signal early stop.
    target_year: int, if set, only fetch videos published in that year.
    """
    with app.app_context():
        from models import db, HuiZong, CrawlLog

        data_year = target_year or datetime.datetime.now().year
        pubtime_begin, pubtime_end = _year_timestamps(data_year)

        log = CrawlLog(start_time=datetime.datetime.now(), status='running', target_year=data_year)
        db.session.add(log)
        db.session.commit()

        sess = requests.Session()
        sess.headers.update(HEADERS)
        sess.cookies.update(BILIBILI_COOKIE)

        total_new = 0
        total_update = 0

        try:
            img_key, sub_key = _get_wbi_keys(sess)

            fans_cache = {}

            for keyword in KEYWORDS:
                if stop_event and stop_event.is_set():
                    app.logger.info('[crawler] 收到停止信号，提前终止')
                    break
                app.logger.info(f'[crawler] 关键词: {keyword} 年份: {data_year}')
                for page in range(1, 51):
                    if stop_event and stop_event.is_set():
                        break
                    try:
                        result = _search_page(sess, keyword, page, img_key, sub_key,
                                              pubtime_begin, pubtime_end)
                        if result.get('code') != 0:
                            app.logger.warning(f'[crawler] {keyword} p{page}: {result.get("message")}')
                            break

                        items = result.get('data', {}).get('result', [])
                        if not items:
                            break

                        for item in items:
                            if item.get('type') != 'video':
                                continue
                            bvid = item.get('bvid', '')
                            if not bvid:
                                continue
                            try:
                                url = f'https://www.bilibili.com/video/{bvid}'
                                try:
                                    pubdate = datetime.datetime.fromtimestamp(item.get('pubdate', 0))
                                except Exception:
                                    pubdate = None

                                mid = item.get('mid', 0)
                                real_tag = item.get('tname') or keyword
                                now = datetime.datetime.now()
                                existing = HuiZong.query.filter_by(url=url).first()

                                if existing:
                                    existing.rank_score = item.get('play', 0) or 0
                                    existing.video_review = item.get('video_review', 0) or 0
                                    existing.favorites = item.get('favorites', 0) or 0
                                    existing.like = item.get('like', 0) or 0
                                    existing.update_time = now
                                    if not existing.fans:
                                        existing.fans = _fetch_fans(sess, mid, fans_cache)
                                    total_update += 1
                                else:
                                    fans_count = _fetch_fans(sess, mid, fans_cache)
                                    db.session.add(HuiZong(
                                        author=(item.get('author', '') or '')[:124],
                                        url=url,
                                        description=(item.get('description', '') or '')[:124],
                                        title=_clean_title(item.get('title', '') or '')[:124],
                                        video_review=item.get('video_review', 0) or 0,
                                        rank_score=item.get('play', 0) or 0,
                                        pubdate=pubdate,
                                        favorites=item.get('favorites', 0) or 0,
                                        tag=real_tag,
                                        duration=_parse_duration(item.get('duration', 0)),
                                        review=item.get('review', 0) or 0,
                                        like=item.get('like', 0) or 0,
                                        share=0,
                                        coin=item.get('coin', 0) or 0,
                                        fans=fans_count,
                                        update_time=now,
                                        crawl_id=log.id,
                                        data_year=data_year,
                                    ))
                                    total_new += 1
                                db.session.commit()
                            except Exception as e:
                                db.session.rollback()
                                app.logger.error(f'[crawler] 保存单条记录失败 {bvid}: {e}')

                        time.sleep(0.8)

                    except Exception as e:
                        app.logger.error(f'[crawler] {keyword} p{page}: {e}')
                        db.session.rollback()
                        time.sleep(2)
                        continue

                time.sleep(1.5)

            if stop_event and stop_event.is_set():
                log.status = 'stopped'
            else:
                log.status = 'success'

        except Exception as e:
            log.status = 'error'
            log.error_msg = str(e)[:500]
            app.logger.error(f'[crawler] failed: {e}')

        log.end_time = datetime.datetime.now()
        log.new_count = total_new
        log.update_count = total_update
        db.session.commit()

        app.logger.info(f'[crawler] 完成. 新增={total_new} 更新={total_update}')
        return total_new, total_update
