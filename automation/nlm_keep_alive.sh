#!/bin/bash

# ==============================================================================
# NLM Session Stay-alive Script (v1.0)
# This script runs a simple NLM command to keep the Google session active.
# ==============================================================================

PROJECT_ROOT="/home/ubuntu/AI/News"
VENV_BIN="$PROJECT_ROOT/automation/venv/bin"
LOG_FILE="$PROJECT_ROOT/automation/logs/stay_alive.log"

# 이동
cd $PROJECT_ROOT

# 로깅 시작
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting NLM Stay-alive check..." >> $LOG_FILE

# NLM 명령어 실행 (세션 활동 유도)
# studio status는 구글 서버에 요청을 보내므로 세션 연장에 적합합니다.
$VENV_BIN/nlm studio status >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] NLM Stay-alive success." >> $LOG_FILE
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] NLM Stay-alive FAILED! Please check manually." >> $LOG_FILE
    # 만약 실패하면 텔레그램으로 알림을 보낼 수도 있습니다. (추후 고도화)
fi
