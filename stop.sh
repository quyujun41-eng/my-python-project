#!/bin/bash
# 关闭毕设项目

cd "$(dirname "$0")"

if [ ! -f app.pid ]; then
    echo "未找到 app.pid，项目可能未通过 start.sh 启动"
    exit 1
fi

PID=$(cat app.pid)
if kill -0 $PID 2>/dev/null; then
    kill $PID
    rm -f app.pid
    echo "项目已关闭 (PID: $PID)"
else
    echo "进程不存在，清理 pid 文件"
    rm -f app.pid
fi
