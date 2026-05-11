# !/usr/bin/env python
# _*_ coding: utf-8 _*_
from flask import Flask, request, render_template,jsonify,abort,session,redirect, url_for
import os
import models
from models import app
import time
from sqlalchemy import or_,and_
import json


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return redirect(url_for('login'))
    if request.method == 'GET':
        results = models.HuiZong.query.all()
        search = request.args.get('search')
        if search:
            results = models.HuiZong.query.filter(or_(models.HuiZong.title.like("%{}%".format(search)),models.HuiZong.description.like("%{}%".format(search)),models.HuiZong.author.like("%{}%".format(search))))

        return render_template('index.html',results=results)

import xietong
from sqlalchemy import desc
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
        print(r)
        if r:
            results = []
            for rid in r:
                results.append(models.HuiZong.query.get(rid[0]))

        return render_template('tuijian.html',results = results,username=username)



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

        return render_template('charts1.html', **locals())





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
        data = models.User.query.filter(and_(models.User.name==name,models.User.password==pwd)).all()
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
        if models.User.query.filter(models.User.name == name).all():
            return render_template('signup.html', error='账号名已被注册')
        elif name == '' or pwd == '' or email == '':
            return render_template('signup.html', error='输入不能为空')
        else:
            models.db.session.add(models.User(name=name,email=email,password=pwd))
            models.db.session.commit()
            return redirect(url_for('login'))


import ai_chat

@app.route('/ai', methods=['GET'])
def ai_page():
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return redirect(url_for('login'))
    return render_template('ai_chat.html')

@app.route('/ai/ask', methods=['POST'])
def ai_ask():
    """
    接收前端问题，调用三个版本的引擎
    version=1 → 故障版（无Schema）
    version=2 → 半修复版（有Schema但格式不稳定）
    version=3 → 生产版（完整修复）
    """
    uuid = session.get('uuid')
    if not models.User.query.get(uuid):
        return jsonify({"error": "未登录"}), 401

    question = request.json.get('question', '').strip()
    version = request.json.get('version', 3)

    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    if version == 1:
        result = ai_chat.ask_v1_broken(question)
    elif version == 2:
        result = ai_chat.ask_v2_unstable(question)
    else:
        result = ai_chat.ask_v3_production(question)

    return jsonify(result)


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
                models.Recommend(
                    user_id=uuid,
                    huizong_id=huizong_id,
                    num=4
                )
            )
            models.db.session.commit()
            json_item = {"status":True,"content":"点赞成功"}
        else:
            json_item = {"status": True, "content": "已经点个赞了"}
        return jsonify(json.dumps(json_item))

