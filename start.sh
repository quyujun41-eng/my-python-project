#!/bin/bash
# 启动毕设项目

cd "$(dirname "$0")"

if [ -f app.pid ] && kill -0 $(cat app.pid) 2>/dev/null; then
    echo "项目已在运行中 (PID: $(cat app.pid))"
    exit 0
fi

nohup python3 run.py > app.log 2>&1 &
echo $! > app.pid
echo "项目已启动 (PID: $!)"
echo "日志文件: app.log"
