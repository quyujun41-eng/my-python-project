#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B站数据 AI 问答引擎
演示3种真实项目中会遇到的故障及修复方式
"""

import sqlite3
import json
import re
import anthropic

DB_PATH = 'bilibili.db'
client = anthropic.Anthropic()

# ─────────────────────────────────────────
# 数据库结构说明（喂给 AI 的"地图"）
# 这是 Text-to-SQL 最关键的部分：
# AI 必须知道表名、列名、数据类型、示例值，才能生成正确 SQL
# ─────────────────────────────────────────
SCHEMA = """
数据库：SQLite，文件名 bilibili.db

表名：HuiZong（B站热门视频，共527条记录）
列名如下（注意：列名全部是中文）：
  id       INTEGER  主键
  作者      TEXT     UP主名字，如：盗月社食遇记
  标题      TEXT     视频标题
  简介      TEXT     视频简介
  链接      TEXT     视频URL
  播放量    FLOAT    播放次数，数值较大，如：1049070
  弹幕量    FLOAT    弹幕数量
  收藏量    FLOAT    收藏数
  点赞      FLOAT    点赞数
  评论      FLOAT    评论数
  转发      FLOAT    转发数
  投币      FLOAT    投币数
  粉丝数    FLOAT    UP主粉丝数
  时长      FLOAT    视频时长（单位：秒）
  分区      TEXT     视频分类，可选值有：
                     搞笑、美食侦探、手机游戏、出行、小剧场、日常、健身、
                     亲子、电子竞技、影视杂谈、美食制作、MV、穿搭、
                     单机游戏、美食记录、音乐综合、手工、网络游戏 等
  投稿时间  DATETIME 发布时间，格式：2023-04-11 17:20:21

业务词汇定义（必须遵守）：
  "最受欢迎" = 播放量最高
  "最火"     = 播放量最高
  "互动最好" = 点赞 + 评论 + 转发 + 投币 之和最高
  "涨粉潜力" = 粉丝数 / 播放量 比值（越高说明转化越好）
"""


# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────

def run_sql(sql: str):
    """执行 SQL，返回 (列名列表, 数据行列表) 或抛出异常"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    finally:
        conn.close()


def extract_sql(text: str) -> str:
    """从 AI 回复里提取 SQL 语句"""
    # 先找代码块里的 SQL
    match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 再找 SELECT 开头的语句
    match = re.search(r'(SELECT\s+.*?;)', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


# ─────────────────────────────────────────
# 【版本1】最简单的实现 —— 用来演示"故障1"
# 故障：AI 不知道列名是中文，生成了英文列名的 SQL，直接报错
# ─────────────────────────────────────────

def ask_v1_broken(question: str) -> dict:
    """
    故障版本：没有给 AI 提供数据库结构信息
    AI 会凭空猜测列名，大概率生成错误 SQL
    """
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"把这个问题转成 SQLite SQL 语句：{question}\n只输出 SQL，不要解释。"
        }]
    )
    sql = extract_sql(response.content[0].text)
    try:
        columns, rows = run_sql(sql)
        return {"status": "ok", "sql": sql, "columns": columns, "rows": rows}
    except Exception as e:
        return {"status": "error", "sql": sql, "error": str(e)}


# ─────────────────────────────────────────
# 【版本2】加入 Schema —— 修复故障1，但引入"故障2"
# 故障：AI 输出格式不稳定，有时返回 SQL，有时返回解释性文字
# ─────────────────────────────────────────

def ask_v2_unstable(question: str) -> dict:
    """
    加入了 Schema，SQL 基本正确了
    但 AI 输出格式不受控制：
      有时输出 ```sql ... ```
      有时直接输出 SQL
      有时输出"好的，以下是SQL语句：SELECT..."
    导致 extract_sql 解析失败
    """
    prompt = f"""你是一个 SQLite 专家。

数据库结构：
{SCHEMA}

把用户的问题转成 SQL 语句。
问题：{question}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text
    sql = extract_sql(raw)
    try:
        columns, rows = run_sql(sql)
        return {"status": "ok", "sql": sql, "columns": columns, "rows": rows, "raw": raw}
    except Exception as e:
        return {"status": "error", "sql": sql, "error": str(e), "raw": raw}


# ─────────────────────────────────────────
# 【版本3】完整修复版 —— 生产可用
# 修复点：
#   1. 提供完整 Schema（解决列名问题）
#   2. 强制 JSON 输出格式（解决格式不稳定问题）
#   3. SQL 执行失败时自动让 AI 修正（解决边界错误）
#   4. 二次调用 AI 用自然语言解读结果（解决"数字对但解读错"问题）
# ─────────────────────────────────────────

def ask_v3_production(question: str) -> dict:
    """生产级版本：稳定、可修正、有解读"""

    # ── 第一步：自然语言 → SQL ──
    sql_prompt = f"""你是一个 SQLite 专家。

{SCHEMA}

用户问题：{question}

要求：
1. 只输出一个 JSON 对象，格式如下，不要输出任何其他内容：
{{"sql": "SELECT ... FROM HuiZong ...", "explanation": "我查的是什么"}}
2. SQL 必须可以直接在 SQLite 中执行
3. 列名必须用中文，和 Schema 完全一致
4. LIMIT 默认不超过 20 条"""

    resp1 = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": sql_prompt}]
    )

    try:
        parsed = json.loads(resp1.content[0].text.strip())
        sql = parsed["sql"]
        explanation = parsed.get("explanation", "")
    except Exception:
        # JSON 解析失败时，退回正则提取
        sql = extract_sql(resp1.content[0].text)
        explanation = ""

    # ── 第二步：执行 SQL，失败时让 AI 自动修正 ──
    columns, rows, error = None, None, None
    for attempt in range(2):
        try:
            columns, rows = run_sql(sql)
            error = None
            break
        except Exception as e:
            error = str(e)
            if attempt == 0:
                # 把报错信息反馈给 AI，让它修正 SQL
                fix_prompt = f"""以下 SQL 执行时报错：

SQL：{sql}
错误：{error}

数据库结构：
{SCHEMA}

请修正 SQL，只输出修正后的 SQL 语句，不要解释。"""
                resp_fix = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=256,
                    messages=[{"role": "user", "content": fix_prompt}]
                )
                sql = extract_sql(resp_fix.content[0].text)

    if error:
        return {"status": "error", "sql": sql, "error": error}

    # ── 第三步：让 AI 用自然语言解读查询结果 ──
    if not rows:
        answer = "数据库中没有符合条件的数据。"
    else:
        rows_preview = rows[:10]
        interpret_prompt = f"""用户问题：{question}

查询结果（前{len(rows_preview)}条，共{len(rows)}条）：
列名：{columns}
数据：{rows_preview}

请用1~3句自然语言回答用户的问题，要具体（带数字），不要照抄原始数据。"""

        resp2 = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": interpret_prompt}]
        )
        answer = resp2.content[0].text.strip()

    return {
        "status": "ok",
        "question": question,
        "sql": sql,
        "explanation": explanation,
        "columns": columns,
        "rows": rows[:10],
        "total": len(rows),
        "answer": answer
    }
