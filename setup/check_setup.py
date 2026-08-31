#!/usr/bin/env python3
"""goldenjoy-shorts 설치 점검 — 처음 받은 분은 이것부터 실행하세요.

    python3 setup/check_setup.py

빠진 것을 한국어로 알려줍니다. 전부 OK 가 나오면 제작을 시작할 수 있습니다.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

OK, NG, WARN = "  [OK]", "★ [빠짐]", "  [선택]"
problems = 0


def check(label, ok, fix, optional=False):
    global problems
    if ok:
        print(f"{OK} {label}")
    elif optional:
        print(f"{WARN} {label} — {fix}")
    else:
        print(f"{NG} {label}\n        해결: {fix}")
        problems += 1


def has_cmd(name):
    return shutil.which(os.path.expanduser(name)) is not None


def main():
    print("=== goldenjoy-shorts 설치 점검 ===\n")

    # 1. config
    root = Path(__file__).resolve().parent.parent
    cfg_path = root / "config.json"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
            print(f"{OK} config.json 읽음")
        except Exception as e:
            check("config.json 형식", False, f"JSON 문법 오류: {e}")
    else:
        check("config.json", False, "config.example.json 을 config.json 으로 복사한 뒤 값을 채우세요")

    # 2. 필수 실행 파일
    check("ffmpeg", has_cmd(cfg.get("ffmpeg", "ffmpeg")), "https://ffmpeg.org 또는 `brew install ffmpeg`")
    check("ffprobe", has_cmd("ffprobe"), "ffmpeg 과 함께 설치됩니다")

    # 3. 파이썬 패키지
    for mod, why in [("PIL", "자막·시트 이미지 처리 (`pip install pillow`)"),
                     ("numpy", "오디오·프레임 계산 (`pip install numpy`)"),
                     ("cv2", "얼굴 검출·중앙 배치 (`pip install opencv-python`)")]:
        try:
            __import__(mod)
            print(f"{OK} python 패키지 {mod}")
        except ImportError:
            check(f"python 패키지 {mod}", False, why)

    # 4. API 키
    for name, url in [("typecast", "https://typecast.ai 에서 발급 (TTS 나레이션)"),
                      ("speechmatics", "https://www.speechmatics.com 에서 발급 (자막 싱크 정렬)")]:
        p = cfg.get("keys", {}).get(name, "")
        ok = bool(p) and Path(os.path.expanduser(p)).exists()
        check(f"{name} API 키 파일", ok, f"{url} → 키를 파일로 저장하고 config.json 의 keys.{name} 에 경로 기입")

    # 5. 작업 폴더
    wr = cfg.get("work_root", "")
    check("작업 폴더 (work_root)", bool(wr) and Path(os.path.expanduser(wr)).parent.exists(),
          "config.json 의 work_root 에 프로젝트 폴더들을 만들 위치를 기입 (예: ~/shorts-work)")

    # 6. 볼케이노 MCP (안내만 — 여기서는 접속 확인 불가)
    print(f"{WARN} 볼케이노 MCP + 명화관 프리셋 — Claude Code 에서 volcano_video 도구가 보이는지 확인하세요."
          " 상하단 프레임 이미지·기본 음성·자막 스타일은 볼케이노 기본 프리셋에서 받습니다.")

    print()
    if problems:
        print(f"필수 항목 {problems}개가 빠져 있습니다. 위의 '해결'을 따라 채운 뒤 다시 실행하세요.")
        sys.exit(1)
    print("전부 준비됐습니다. Claude Code 에서 영화 파일 경로와 함께 \"숏폼 만들어줘\" 라고 하면 시작됩니다.")


if __name__ == "__main__":
    main()
