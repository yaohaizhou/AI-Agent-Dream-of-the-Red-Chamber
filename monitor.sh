#!/bin/bash
# 监控红楼梦续写进程的脚本

LOG_FILE="/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/monitor.log"
PID_FILE="/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/continuation.pid"

# 记录监控开始
echo "$(date): 开始监控红楼梦续写进程" >> $LOG_FILE

while true; do
    # 检查进程是否存在
    if pgrep -f "run_continuation.py" > /dev/null; then
        echo "$(date): 续写进程仍在运行" >> $LOG_FILE
        # 检查输出目录是否有进展
        if [ -d "/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/output" ]; then
            echo "$(date): 输出目录存在，检查进度..." >> $LOG_FILE
            ls -la /home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/output >> $LOG_FILE 2>&1
        fi
    else
        echo "$(date): 续写进程已完成或已终止" >> $LOG_FILE
        # 检查是否成功完成
        if [ -d "/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/output" ]; then
            echo "$(date): 任务完成，输出目录已创建" >> $LOG_FILE
            ls -la /home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber/output >> $LOG_FILE 2>&1
            break
        else
            echo "$(date): 任务可能未正常完成" >> $LOG_FILE
            break
        fi
    fi
    
    # 等待10分钟后再次检查
    sleep 600
done

echo "$(date): 监控结束" >> $LOG_FILE