#!/usr/bin/python
# -*- coding: UTF-8 -*-
from math import sqrt
import operator

#1.构建用户-->视频的倒排
def loadData(files):
    data ={};
    for line in files:
        user,score,item=line.split(",");
        data.setdefault(user,{});
        data[user][item]=score;
    return data

#2.计算
# 2.1 构造视频-->视频的共现矩阵
# 2.2 计算视频与视频的相似矩阵
def similarity(data):
    # 2.1 构造视频：视频的共现矩阵
    N={};#喜欢视频i的总人数
    C={};#喜欢视频i也喜欢视频j的人数
    for user,item in data.items():
        for i,score in item.items():
            N.setdefault(i,0);
            N[i]+=1;
            C.setdefault(i,{});
            for j,scores in item.items():
                if j not in i:
                    C[i].setdefault(j,0);
                    C[i][j]+=1;


    #2.2 计算视频与视频的相似矩阵
    W={};
    for i,item in C.items():
        W.setdefault(i,{});
        for j,item2 in item.items():
            W[i].setdefault(j,0);
            W[i][j]=C[i][j]/sqrt(N[i]*N[j]);
    return W

#3.根据用户的历史记录，给用户推荐视频     （基于用户的协同过滤推荐算法）
def recommandList(data,W,user,k=3,N=10):
    rank={};
    for i,score in data[user].items():     #获得用户user历史记录，如A用户的历史记录为{'a': '1', 'b': '1', 'd': '1'}
        for j,w in sorted(W[i].items(),key=operator.itemgetter(1),reverse=True)[0:k]:    #获得与视频i相似的k个视频
            if j not in data[user].keys():    #该相似的视频不在用户user的记录里
                rank.setdefault(j,0);
                rank[j]+=float(score) * w;

    return sorted(rank.items(),key=operator.itemgetter(1),reverse=True)[0:N];

if __name__=='__main__':
    #用户，兴趣度，视频
    # uid_score_bid = ['A,1,a', 'A,1,b', 'A,1,d', 'B,1,b', 'B,1,c', 'B,1,e']

    uid_score_bid = ['5,1,5','2,1,5', '2,1,38', '2,1,40', '2,1,44', '2,1,63', '2,1,107', '2,1,6', '2,1,14', '2,1,27', '2,1,32', '2,1,56', '2,1,77', '2,1,89', '2,1,92', '2,1,94', '2,1,111', '2,1,123', '2,1,124', '4,1,9', '4,1,15', '4,1,20', '4,1,22', '4,1,85', '4,1,95', '4,1,99', '4,1,131', '4,1,5', '4,1,38', '4,1,40', '4,1,44', '4,1,63', '4,1,107', '4,1,13', '4,1,17', '4,1,58', '4,1,8', '4,1,18', '4,1,21', '4,1,26', '4,1,34', '4,1,48', '4,1,51', '4,1,64', '4,1,70', '4,1,79', '4,1,84', '4,1,101', '4,1,106', '4,1,116', '4,1,117', '4,1,119', '4,1,126', '2,1,8', '2,1,18', '2,1,21', '2,1,26', '2,1,34', '2,1,48', '2,1,51', '2,1,64', '2,1,70', '2,1,79', '2,1,84', '2,1,101', '2,1,106', '2,1,116', '2,1,117', '2,1,119', '2,1,126']

    data=loadData(uid_score_bid);#获得数据
    W=similarity(data);#计算视频相似矩阵
    a = recommandList(data,W,'5',5,10);#推荐
    print(a)