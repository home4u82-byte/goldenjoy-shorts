#!/bin/bash
# 영화모음 폴더 변화 감지 → 복사 완료 대기 → prescan 배치 (launchd WatchPaths 가 호출)
LOG=<작업루트>/cache/prescan_watch.log
LOCK=<작업루트>/cache/.watch_lock
exec >> "$LOG" 2>&1
echo "== $(date '+%F %T') 폴더 변화 감지"
mkdir "$LOCK" 2>/dev/null || { echo "다른 감시자 처리 중 - 종료"; exit 0; }
trap 'rmdir "$LOCK"' EXIT
# 복사 중 파일 보호: 폴더 목록(크기 포함)이 60초간 안정될 때까지 대기 (최대 30분)
for i in $(seq 1 30); do
  A=$(ls -l "${MOVIES_DIR:?감시할 영화 폴더 경로를 MOVIES_DIR 로 지정}" 2>/dev/null | md5)
  sleep 60
  B=$(ls -l "${MOVIES_DIR:?감시할 영화 폴더 경로를 MOVIES_DIR 로 지정}" 2>/dev/null | md5)
  [ "$A" = "$B" ] && break
  echo "  복사 진행 중... 대기 ($i)"
done
# 이미 도는 prescan 이 있으면 끝날 때까지 대기 (prescan 은 완료분 스킵이라 중복 무해)
while pgrep -f "prescan.py" >/dev/null; do sleep 60; done
echo "  prescan 시작"
python3 "<작업루트>/2026-08-26-8_그들만의리그/.claude/skills/shorts-core/tools/prescan.py" >> <작업루트>/cache/prescan.log 2>&1
echo "== $(date '+%F %T') prescan 종료"
