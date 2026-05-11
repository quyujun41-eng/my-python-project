import time

import requests
import re
import json
from bs4 import BeautifulSoup
import models
import datetime

#  爬虫后，数据存储到数据库 HuiZong  表

def xinxi():
    for i in range(1,20):    #(1,20)

        #获取 "综合热门" 视频
        url = 'https://api.bilibili.com/x/web-interface/popular?ps=20&pn={}'.format(i)

        # 获取 "入站必刷" 视频
        # url = 'https://api.bilibili.com/x/web-interface/popular/precious?page_size=20&pn={}'.format(i)



        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
        }
        h1 = requests.get(url=url, headers=headers, verify=False)


        print(h1.json())
        for resu in h1.json()['data']['list']:
            time.sleep(1)
            author = resu['owner']['name']  # 作者
            url = 'https://www.bilibili.com/video/' + resu['bvid']
            description = resu['desc']  # 简介
            title = resu['title']  # 标题
            video_review = resu['stat']['danmaku']  # 弹幕量
            rank_score = resu['stat']['view']  # 播放量
            pubdate = resu['pubdate']  # 投稿时间,时间戳类型
            favorites = resu['stat']['favorite']  # 收藏量
            tag = resu['tname']  # 分区
            duration = resu['duration']  # 时长
            review = resu['stat']['reply']  # 评论
            h2 = requests.get(url=url, headers=headers, verify=False)
            initial = re.findall('__INITIAL_STATE__=({.*?});', h2.text, re.DOTALL)
            try:
                initial_json = json.loads(initial[0])
                like = initial_json['videoData']['stat']['like']  # 点赞
                share = initial_json['videoData']['stat']['share']  # 转发
                coin = initial_json['videoData']['stat']['coin']  # 转发
                fans = initial_json['upData']['fans']  # 粉丝数
            except:
                continue
            print(author, description, title, video_review, rank_score, pubdate, favorites, tag, duration,
                  review,like,share,coin,fans)
            if not models.HuiZong.query.filter(models.HuiZong.url==url).all():
                models.db.session.add(
                    models.HuiZong(
                        author = author,
                        url = url,
                        description = description,
                        title = title,
                        video_review = video_review,
                        rank_score = rank_score,
                        pubdate = datetime.datetime.fromtimestamp(int(pubdate)),
                        favorites = favorites,
                        tag = tag,
                        duration = duration,
                        review = review,
                        like = like,
                        share = share,
                        coin = coin,
                        fans = fans,
                        ))
                models.db.session.commit()



if __name__ == '__main__':
    xinxi()

