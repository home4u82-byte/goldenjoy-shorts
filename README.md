# goldenjoy-shorts

영화 한 편을 받아 **명화관 스타일 숏폼**을 만드는 Claude Code 플러그인입니다.
볼케이노 MCP의 명화관 기본 프리셋 위에, 실전 제작에서 다듬어진 두 가지를 얹습니다.

1. **대본 구성** (가장 중요) — 품질 3기준(처음 보는 사람이 이해된다 · 본편이 궁금해진다 · 본 사람은 추억에 잠긴다),
   드라마 설계표, 시작(훅) 패턴 비교 선택, 냉관객 검사(영화 모르는 시점으로 대본을 검증)
2. **편집 검증 게이트** — 화자가 항상 화면 정중앙(눈코 삼각형 기준), 나레이션과 화면 일치,
   컷 튐 전수 눈검사, 자막-음성 싱크, 라우드니스까지 17개 게이트

## 요구 사항

| 항목 | 설명 |
|---|---|
| 볼케이노 MCP + 명화관 프리셋 | 이미 쓰고 계신 것. 상하단 프레임 이미지·기본 TTS 음성·자막 스타일은 여기서 받습니다 |
| ffmpeg / ffprobe | `brew install ffmpeg` |
| Python 3 + pillow, numpy, opencv-python | `pip install pillow numpy opencv-python` |
| Typecast API 키 | https://typecast.ai (TTS 나레이션) |
| Speechmatics API 키 | https://www.speechmatics.com (자막 싱크 정렬) |

## 설치

```
/plugin marketplace add <골든조이의-GitHub-계정>/goldenjoy-shorts
/plugin install goldenjoy-shorts
```

설치 후:

```bash
cp config.example.json config.json     # 값 채우기 (키 경로, 작업 폴더)
python3 setup/check_setup.py           # 전부 [OK] 가 나올 때까지
```

## 첫 편 만들기

Claude Code 에서:

```
/Users/나/영화파일.mkv 이 영화로 숏폼 만들어줘
```

스킬이 알아서 진행합니다: 소재 분석 → 명장면 목록 → 드라마 설계표 → 냉관객 검사 →
TTS·컷 편집 → 검증 게이트 → `out/제목_최종.mp4`.

## 커스텀 — 마음껏 고치세요 (MIT)

이 플러그인은 수정·재배포가 전부 허용됩니다. 고치기 좋은 지점은
`skills/goldenjoy-shorts/SKILL.md` 의 **커스텀 포인트** 절에 정리돼 있습니다
(문구 톤, 게이트 강도, 자막 스타일, 워터마크 추가 등).
크게 뜯어고치려면 repo 를 fork 해서 자기 버전을 만드는 방식을 권합니다.

## 문제가 생기면

- `python3 setup/check_setup.py` 를 먼저 — 대부분 환경 문제입니다.
- 렌더 실패: build → merge → finish 순서에서 **각 단계의 exit 코드**를 확인하세요
  (파이프로 이으면 실패가 묻힙니다 — 템플릿 스크립트는 이미 안전하게 돼 있습니다).
