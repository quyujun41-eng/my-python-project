# !/usr/bin/env python
# _*_ coding: utf-8 _*_
import hashlib
import json
import os
import threading

from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from sqlalchemy import or_, and_, func

import models
import xietong
from models import app, SearchHistory, UserBehavior, Comment
from sqlalchemy import desc


_crawl_stop_event = threading.Event()


def _get_year_stats():
    """返回各年份数据量列表，按 data_year 字段分组。"""
    rows = models.db.session.query(
        models.HuiZong.data_year,
        func.count().label('cnt')
    ).filter(models.HuiZong.data_year != None).group_by(models.HuiZong.data_year
    ).order_by(models.HuiZong.data_year).all()
    result = [{'year': str(row.data_year), 'count': row.cnt, 'is_latest': False} for row in rows]
    if result:
        result[-1]['is_latest'] = True
    return result


def hash_pwd(password):
    return hashlib.md5(password.encode()).hexdigest()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return redirect(url_for('login'))
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '').strip()
        year = request.args.get('year', '')

        query = models.HuiZong.query
        if year:
            query = query.filter(models.HuiZong.data_year == int(year))

        if search:
            query = query.filter(or_(
                models.HuiZong.title.like("%{}%".format(search)),
                models.HuiZong.description.like("%{}%".format(search)),
                models.HuiZong.author.like("%{}%".format(search)),
                models.HuiZong.tag.like("%{}%".format(search))
            ))
            models.db.session.add(models.SearchHistory(
                user_id=uuid, keyword=search,
                result_count=query.count()
            ))
            models.db.session.commit()

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        search_history = SearchHistory.query.filter_by(user_id=uuid)\
            .order_by(SearchHistory.search_time.desc()).limit(5).all()
        year_list = _get_year_stats()
        return render_template('index.html',
            results=pagination.items,
            pagination=pagination,
            search=search,
            year=year,
            search_history=search_history,
            year_list=year_list,
        )

@app.route('/tuijian', methods=['GET', 'POST'])
def tuijian():
    uuid = session.get('uuid')
    if uuid:
        if not models.User.query.get(uuid):
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    if request.method == 'GET':
        username = models.User.query.get(uuid).name
        results = models.HuiZong.query.order_by(desc(models.HuiZong.rank_score)).all()[:10]
        datas = ['{},{},{}'.format(reco.user_id, int(reco.num), reco.huizong_id) for reco in models.Recommend.query.all()]
        data = xietong.loadData(datas);  # 获得数据
        W = xietong.similarity(data);  # 计算物品相似矩阵
        try:
            r = xietong.recommandList(data, W, str(uuid), 5, 10);  # 推荐
        except:
            r = []
        if r:
            results = []
            for rid in r:
                results.append(models.HuiZong.query.get(rid[0]))

        like_count = UserBehavior.query.filter_by(user_id=uuid, behavior_type='like').count()
        return render_template('tuijian.html', results=results, username=username, like_count=like_count)



@app.route('/echarts1', methods=['GET', 'POST'])
def echarts1():
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return redirect(url_for('login'))
    if request.method == 'GET':
        datas = models.HuiZong.query.all()
        types = list(set([i.tag for i in datas]))
        types.sort()
        type1 = request.args.get('type1')
        if type1:
            datas = models.HuiZong.query.filter(models.HuiZong.tag==type1).all()

        #前20播放量视频
        li1 = []
        for resu in datas:
            li1.append([resu.author,resu.rank_score])
        li1.sort(key=lambda xx:xx[1],reverse=True)
        rank_score_name = []
        rank_score_count = []
        for resu in li1[:20]:
            rank_score_name.append(resu[0])
            rank_score_count.append(resu[1])

        #粉丝数前10的视频类型
        li3 = []
        for resu in types:
            da1 = models.HuiZong.query.filter(models.HuiZong.tag==resu).all()
            value = 0
            for resu1 in da1:
                value += resu1.fans

            li3.append([resu,value])
        li3.sort(key=lambda xx:xx[1],reverse=True)
        author_name = []
        author_count = []
        for resu in li3[:10]:
            author_name.append(resu[0])
            author_count.append(resu[1])


        #播放量等级与视频发布时间
        score_time = []
        for resu in datas:
            score_time.append([resu.rank_score,resu.fans,resu.title])

        li1 = [[],[],[],[],[]]
        for resu in datas:
            if resu.rank_score > 50000 and resu.rank_score < 200000:
                li1[0].append(resu.rank_score)
            elif resu.rank_score > 200000 and resu.rank_score < 500000:
                li1[1].append(resu.rank_score)
            elif resu.rank_score > 500000 and resu.rank_score < 1000000:
                li1[2].append(resu.rank_score)
            elif resu.rank_score > 1000000 and resu.rank_score < 2000000:
                li1[3].append(resu.rank_score)
            elif resu.rank_score > 2000000 :
                li1[4].append(resu.rank_score)

        # 热门搜索关键词 top10
        from sqlalchemy import func
        hot_kw = models.db.session.query(
            SearchHistory.keyword,
            func.count(SearchHistory.keyword).label('cnt')
        ).group_by(SearchHistory.keyword).order_by(func.count(SearchHistory.keyword).desc()).limit(10).all()
        hot_kw_names = [r.keyword for r in hot_kw]
        hot_kw_counts = [r.cnt for r in hot_kw]

        return render_template('charts1.html',
            types=types, type1=type1,
            rank_score_name=json.dumps(rank_score_name, ensure_ascii=False),
            rank_score_count=json.dumps(rank_score_count),
            author_name=json.dumps(author_name, ensure_ascii=False),
            author_count=json.dumps(author_count),
            score_time=json.dumps(score_time, ensure_ascii=False),
            li1=json.dumps(li1), li2=json.dumps([]), li3=json.dumps([]),
            li4=json.dumps([]), li5=json.dumps([]),
            hot_kw_names=json.dumps(hot_kw_names, ensure_ascii=False),
            hot_kw_counts=json.dumps(hot_kw_counts)
        )


@app.route('/analysis', methods=['GET'])
def analysis():
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return redirect(url_for('login'))

    keyword = request.args.get('keyword', '').strip()
    stats = {}

    if keyword:
        from collections import Counter
        results = models.HuiZong.query.filter(or_(
            models.HuiZong.title.like('%{}%'.format(keyword)),
            models.HuiZong.description.like('%{}%'.format(keyword)),
            models.HuiZong.tag.like('%{}%'.format(keyword)),
            models.HuiZong.author.like('%{}%'.format(keyword))
        )).all()

        if results:
            total = len(results)
            avg_play = round(sum(r.rank_score or 0 for r in results) / total)
            avg_like = round(sum(r.like or 0 for r in results) / total)
            avg_fans = round(sum(r.fans or 0 for r in results) / total)

            top10 = sorted(results, key=lambda x: x.rank_score or 0, reverse=True)[:10]
            top10_names = [r.title[:12] for r in top10]
            top10_plays = [r.rank_score for r in top10]
            top10_likes = [r.like for r in top10]
            top10_fans  = [r.fans for r in top10]

            tag_counter = Counter(r.tag for r in results if r.tag)
            tag_values = [{'value': v, 'name': k} for k, v in tag_counter.most_common(8)]

            stats = {
                'total': total,
                'avg_play': avg_play,
                'avg_like': avg_like,
                'avg_fans': avg_fans,
                'top10_names': json.dumps(top10_names, ensure_ascii=False),
                'top10_plays': json.dumps(top10_plays),
                'top10_likes': json.dumps(top10_likes),
                'top10_fans':  json.dumps(top10_fans),
                'tag_values':  json.dumps(tag_values, ensure_ascii=False),
            }

    return render_template('analysis.html', keyword=keyword, stats=stats)




@app.route('/login', methods=['GET', 'POST'])
def login():
    uuid = session.get('uuid')
    datas = models.User.query.get(uuid)
    if datas:
        return redirect(url_for('index'))
    if request.method=='GET':
        return render_template('login.html')
    elif request.method=='POST':
        name = request.form.get('name')
        pwd = request.form.get('pwd')
        data = models.User.query.filter(and_(models.User.name==name,models.User.password==hash_pwd(pwd))).all()
        if not data:
            return render_template('login.html',error='账号密码错误')
        else:
            session['uuid'] = data[0].id
            session.permanent = True
            return redirect(url_for('index'))


@app.route('/loginout', methods=['GET'])
def loginout():
    if request.method == 'GET':
        session['uuid'] = ''
        session.permanent = False
        return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        uuid = session.get('uuid')
        datas = models.User.query.get(uuid)
        if datas:
            return redirect(url_for('index'))
        return render_template('signup.html')
    elif request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        if not name or not pwd or not email:
            return render_template('signup.html', error='输入不能为空')
        elif len(name) < 2 or len(name) > 32:
            return render_template('signup.html', error='账号长度须在2-32位之间')
        elif len(pwd) < 6:
            return render_template('signup.html', error='密码长度不能少于6位')
        elif models.User.query.filter(models.User.name == name).first():
            return render_template('signup.html', error='账号名已被注册')
        else:
            models.db.session.add(models.User(name=name, email=email, password=hash_pwd(pwd)))
            models.db.session.commit()
            return redirect(url_for('login'))




@app.route('/dianzan', methods=['GET', 'POST'])
def dianzan():
    uuid = session.get('uuid')
    if uuid:
        if not models.User.query.get(uuid):
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    if request.method == 'GET':
        huizong_id = request.args.get('tid')
        if not models.Recommend.query.filter(and_(models.Recommend.user_id==uuid,models.Recommend.huizong_id==huizong_id)).all():
            models.db.session.add(
                models.Recommend(user_id=uuid, huizong_id=huizong_id, num=4)
            )
            models.db.session.add(
                UserBehavior(user_id=uuid, huizong_id=huizong_id, behavior_type='like')
            )
            models.db.session.commit()
            json_item = {"status":True,"content":"点赞成功"}
        else:
            json_item = {"status": True, "content": "已经点个赞了"}
        return jsonify(json.dumps(json_item))


@app.route('/crawl', methods=['GET'])
def crawl():
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return redirect(url_for('login'))

    import datetime as _dt
    from models import CrawlLog
    current_year = _dt.datetime.now().year
    crawl_year_options = list(range(2023, current_year + 1))  # 含2023

    year_stats = _get_year_stats()
    total = sum(y['count'] for y in year_stats)

    last_log = CrawlLog.query.order_by(CrawlLog.start_time.desc()).first()
    logs = CrawlLog.query.order_by(CrawlLog.start_time.desc()).limit(10).all()

    avail_years = [int(y['year']) for y in year_stats]
    cmp_a = request.args.get('cmp_a', type=int)
    cmp_b = request.args.get('cmp_b', type=int)

    compare = None
    if len(avail_years) >= 2:
        if cmp_a and cmp_b and cmp_a != cmp_b and cmp_a in avail_years and cmp_b in avail_years:
            year_old, year_new = sorted([cmp_a, cmp_b])
        else:
            year_old, year_new = avail_years[0], avail_years[-1]

        tags_old_play = dict(models.db.session.query(
            models.HuiZong.tag, func.avg(models.HuiZong.rank_score)
        ).filter(models.HuiZong.data_year == year_old, models.HuiZong.tag != None
        ).group_by(models.HuiZong.tag).all())

        tags_new_play = dict(models.db.session.query(
            models.HuiZong.tag, func.avg(models.HuiZong.rank_score)
        ).filter(models.HuiZong.data_year == year_new, models.HuiZong.tag != None
        ).group_by(models.HuiZong.tag).all())

        all_tags = sorted(set(list(tags_old_play.keys()) + list(tags_new_play.keys())))[:15]

        avg_play_old = round(models.db.session.query(func.avg(models.HuiZong.rank_score)
            ).filter(models.HuiZong.data_year == year_old).scalar() or 0)
        avg_play_new = round(models.db.session.query(func.avg(models.HuiZong.rank_score)
            ).filter(models.HuiZong.data_year == year_new).scalar() or 0)
        avg_like_old = round(models.db.session.query(func.avg(models.HuiZong.like)
            ).filter(models.HuiZong.data_year == year_old).scalar() or 0)
        avg_like_new = round(models.db.session.query(func.avg(models.HuiZong.like)
            ).filter(models.HuiZong.data_year == year_new).scalar() or 0)

        def pct(old, new):
            if not old:
                return 0
            return round((new - old) / old * 100)

        growth_tags = []
        for t in set(tags_old_play.keys()) & set(tags_new_play.keys()):
            old_v = tags_old_play.get(t) or 0
            new_v = tags_new_play.get(t) or 0
            if old_v > 0:
                growth_tags.append({'tag': t, 'growth': round((new_v - old_v) / old_v * 100)})
        growth_tags = sorted(growth_tags, key=lambda x: x['growth'], reverse=True)[:5]

        compare = {
            'year_old': year_old,
            'year_new': year_new,
            'avail_years': avail_years,
            'cmp_a': cmp_a or year_old,
            'cmp_b': cmp_b or year_new,
            'avg_play_old': avg_play_old,
            'avg_play_new': avg_play_new,
            'avg_like_old': avg_like_old,
            'avg_like_new': avg_like_new,
            'play_pct': pct(avg_play_old, avg_play_new),
            'like_pct': pct(avg_like_old, avg_like_new),
            'chart_tags': json.dumps(all_tags, ensure_ascii=False),
            'chart_old': json.dumps([round(tags_old_play.get(t, 0) or 0) for t in all_tags]),
            'chart_new': json.dumps([round(tags_new_play.get(t, 0) or 0) for t in all_tags]),
            'growth_tags': growth_tags,
        }

    return render_template('crawl.html',
        total=total,
        last_log=last_log,
        logs=logs,
        is_admin=True,
        year_stats=year_stats,
        current_year=current_year,
        crawl_year_options=crawl_year_options,
        compare=compare,
    )


@app.route('/crawl/test', methods=['GET'])
def crawl_test():
    if not session.get('uuid'):
        return jsonify({'error': '请先登录'}), 403
    try:
        import requests
        from crawler import BILIBILI_COOKIE, HEADERS, _get_wbi_keys, _sign_params
        sess = requests.Session()
        sess.headers.update(HEADERS)
        sess.cookies.update(BILIBILI_COOKIE)
        img_key, sub_key = _get_wbi_keys(sess)
        params = _sign_params({'search_type': 'video', 'keyword': '美食', 'page': 1, 'page_size': 5}, img_key, sub_key)
        resp = sess.get('https://api.bilibili.com/x/web-interface/search/type', params=params, timeout=10)
        data = resp.json()
        code = data.get('code')
        count = len(data.get('data', {}).get('result', []))
        return jsonify({'code': code, 'message': data.get('message'), 'result_count': count,
                        'ok': code == 0})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/crawl/clear_old', methods=['POST'])
def crawl_clear_old():
    if not session.get('uuid'):
        return jsonify({'error': '请先登录'}), 403
    deleted = models.HuiZong.query.filter(models.HuiZong.update_time == None).delete()
    models.db.session.commit()
    return jsonify({'status': 'ok', 'message': f'已删除 {deleted} 条2023年旧数据'})


@app.route('/crawl/clear_year/<year>', methods=['POST'])
def crawl_clear_year(year):
    if not session.get('uuid'):
        return jsonify({'error': '请先登录'}), 403
    try:
        yr = int(year)
    except ValueError:
        return jsonify({'error': '年份无效'}), 400
    deleted = models.HuiZong.query.filter(models.HuiZong.data_year == yr).delete()
    models.db.session.commit()
    return jsonify({'status': 'ok', 'message': f'已删除 {deleted} 条{yr}年数据', 'year': yr})


@app.route('/crawl/status', methods=['GET'])
def crawl_status():
    running = models.CrawlLog.query.filter_by(status='running').first()
    total = models.HuiZong.query.count()
    year_stats = _get_year_stats()
    data = {
        'is_running': running is not None,
        'total': total,
        'year_stats': year_stats,
    }
    if running:
        data['crawl_new'] = running.new_count or 0
        data['crawl_update'] = running.update_count or 0
        data['crawl_year'] = running.target_year
    return jsonify(data)


@app.route('/crawl/stop', methods=['POST'])
def crawl_stop():
    if not session.get('uuid'):
        return jsonify({'error': '请先登录'}), 403
    _crawl_stop_event.set()
    return jsonify({'status': 'ok', 'message': '已发送停止信号，爬虫将在当前页完成后停止（约1~2秒）'})


@app.route('/crawl/rollback/<int:log_id>', methods=['POST'])
def crawl_rollback(log_id):
    if not session.get('uuid'):
        return jsonify({'error': '请先登录'}), 403
    from models import CrawlLog
    log = CrawlLog.query.get(log_id)
    if not log:
        return jsonify({'error': '记录不存在'}), 404
    if log.status == 'rolled_back':
        return jsonify({'error': '已撤销过了'}), 400
    deleted = models.HuiZong.query.filter_by(crawl_id=log_id).delete()
    log.status = 'rolled_back'
    models.db.session.commit()
    return jsonify({'status': 'ok', 'message': f'已撤销，删除了 {deleted} 条新增数据'})


@app.route('/crawl/run', methods=['POST'])
def crawl_run():
    if not session.get('uuid'):
        return jsonify({'error': '请先登录'}), 403

    from models import CrawlLog
    if CrawlLog.query.filter_by(status='running').first():
        return jsonify({'status': 'running', 'message': '爬虫正在运行中，请稍后查看'})

    _crawl_stop_event.clear()

    body = request.get_json(silent=True) or {}
    try:
        target_year = int(body.get('year', 0)) or None
    except (ValueError, TypeError):
        target_year = None

    def _run():
        from crawler import run_crawl
        run_crawl(app, stop_event=_crawl_stop_event, target_year=target_year)

    threading.Thread(target=_run, daemon=True).start()
    year_label = f'{target_year}年' if target_year else '最新'
    return jsonify({'status': 'started', 'message': f'爬虫已启动！正在爬取{year_label}数据，预计需要30~60分钟'})


@app.route('/comments/<int:huizong_id>', methods=['GET'])
def get_comments(huizong_id):
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return jsonify({'error': '未登录'}), 401
    comments = Comment.query.filter_by(huizong_id=huizong_id)\
        .order_by(Comment.create_time.desc()).limit(20).all()
    return jsonify([{
        'user': models.User.query.get(c.user_id).name if models.User.query.get(c.user_id) else '用户',
        'content': c.content,
        'time': c.create_time.strftime('%m-%d %H:%M') if c.create_time else ''
    } for c in comments])


@app.route('/comment', methods=['POST'])
def comment():
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return jsonify({"error": "未登录"}), 401
    huizong_id = request.json.get('huizong_id')
    content = request.json.get('content', '').strip()
    if not content:
        return jsonify({"error": "评论内容不能为空"}), 400
    models.db.session.add(Comment(user_id=uuid, huizong_id=huizong_id, content=content))
    models.db.session.commit()
    return jsonify({"status": True, "content": "评论成功"})

