# 빌드 템플릿

가타카 편(23.976fps·1920×800 소재·DVID 포함)에서 검증된 최신 스크립트다.
새 프로젝트 폴더에 복사한 뒤 **`★채우기` 표시된 상수만** 바꿔 쓴다 — 로직을 새로 짜지 마라.

| 파일 | 역할 |
|---|---|
| build.py | 블록 렌더 + 자막(ass) 생성. CUTS/DSEG/DVID 는 spec.py 에 |
| spec.py | 컷 테이블 (N컷·D조각·순서·DVID 오버라이드) — 편마다 새로 작성 |
| cards.py | 나레이션 카드 텍스트 + 정렬 |
| dcaps.py | 대사 자막 (화자색 포함) |
| tts.py | Typecast TTS 생성 + 후처리 (키: config 참조) |
| sm_align.py | Speechmatics 어절 정렬 |
| merge.py | 블록 조립 + 경계 디졸브 → merged.mkv |
| make_sfx.py | 효과음 3종 합성 |
| finish.sh | 마스터링 + 최종 합성 |

주의: 소재 fps 가 다르면 FPS 상수와 모든 fps 하드코딩을 실측값으로 바꾼다 (스킬 절대 규칙 16).
실행은 단계별로 exit 코드를 확인한다 — 파이프로 잇지 마라.
