# 컷 설계 정합 lint (게이트 G10) — 렌더 전에 "튐"을 설계 단계에서 잡는다 (2026-08-27)
# 잡는 것:
#   ① 같은 소스 인접 컷의 미세 점프 (0.04~1.2s 건너뜀 = 같은 장면인데 순간이동해 보임)
#   ② 소스 시간 겹침 = 같은 장면 반복 재생
#   ③ 같은 테이크 연속(간격≈0)인데 crop x 가 다름 = 리프레임 점프
#   ④ (scenes.json 있으면) 컷이 장면 경계를 넘거나 경계 0.15s 안까지 붙음
#
# 입력 work/cut_design.json — 빌드 스크립트가 컷 계산 직후 dump 한다 (체인 ss 해석 후의 절대시각):
#   [{"b":0,"i":0,"kind":"N","src":0,"ss":236.30,"se":237.95,"x":700}, ...]
# 빌드 스크립트 dump 예시 (컷 루프 안에서 rows.append(...) 후):
#   json.dump(rows, open("work/cut_design.json","w"))
#
# 사용: python3 tools/cut_lint.py [work/cut_design.json] [work/scenes.json]
import sys, os, json

CD = sys.argv[1] if len(sys.argv) > 1 else "work/cut_design.json"
SC = sys.argv[2] if len(sys.argv) > 2 else "work/scenes.json"
cuts = json.load(open(CD))
scenes = json.load(open(SC)) if os.path.exists(SC) else None  # {src: [경계초...]} 또는 [경계초...]

err, warn = [], []
tag = lambda c: f"b{c['b']}c{c['i']}({c['kind']},src{c.get('src',0)},{c['ss']:.2f}~{c['se']:.2f})"

# 블록·순서대로 정렬해 인접 관계 검사 (블록 경계 넘어 이어지는 것도 잡는다)
seq = sorted(cuts, key=lambda c: (c["b"], c["i"]))
for a, b in zip(seq, seq[1:]):
    if a.get("src", 0) != b.get("src", 0): continue
    gap = b["ss"] - a["se"]
    # 앞 컷의 장면이 끝나기 전에 뒤 컷이 시작해야 "같은 테이크" — sce(설계 scene_end)로 판정
    same_take = b["ss"] < a["sce"] if a.get("sce") else True
    if abs(gap) <= 0.04 and same_take:
        if a.get("x") is not None and b.get("x") is not None and a["x"] != b["x"]:
            err.append(f"리프레임 점프: {tag(a)} x={a['x']} → {tag(b)} x={b['x']} (같은 테이크는 x 동일)")
    elif 0 < gap < 1.2 and same_take:
        warn.append(f"미세 점프 {gap:.2f}s: {tag(a)} → {tag(b)} — 같은 장면 안 순간이동. 붙이거나(간격 0) 다른 장면으로")
    elif -5 < gap < 0:
        if a["b"] == b["b"]:
            err.append(f"시간 역행/겹침 {gap:.2f}s: {tag(a)} → {tag(b)}")
        else:
            warn.append(f"블록 경계 시간 역행 {gap:.2f}s: {tag(a)} → {tag(b)} — 되감기 연출이면 시간전환 표지 문장 확인")

# 전 구간 반복 재생 검사 (인접 아니어도)
for i, a in enumerate(cuts):
    for b in cuts[i + 1:]:
        if a.get("src", 0) != b.get("src", 0): continue
        ov = min(a["se"], b["se"]) - max(a["ss"], b["ss"])
        if ov > 0.3 and not (a["b"] == 0 or b["b"] == 0):  # 훅 블록(0)의 재사용은 의도적 허용
            err.append(f"같은 장면 반복 {ov:.2f}s: {tag(a)} ↔ {tag(b)}")

# 장면 경계 — 소스별 dict({src:[경계초]})일 때만. 단일 리스트는 어느 소스 기준인지 몰라 오탐이 난다
if scenes and not isinstance(scenes, dict):
    print("주의: scenes.json 이 소스별 dict 가 아니라 장면 검사 생략 (컷별 sce 값이 설계 검증을 대신한다)")
    scenes = None
if scenes:
    for c in cuts:
        bl = scenes.get(str(c.get("src", 0)), [])
        for s in bl:
            if c["ss"] < s < c["se"]:
                err.append(f"장면 경계 침범: {tag(c)} 안에 경계 {s:.2f}")
            elif 0 <= s - c["se"] < 0.15:
                warn.append(f"경계 근접 {s-c['se']:.2f}s: {tag(c)} 끝을 0.15~0.2s 더 당길 것 (검출 지연 leak)")

for w in warn: print("주의:", w)
for e in err: print("★오류:", e)
print(f"\n컷 {len(cuts)}개 — 오류 {len(err)} / 주의 {len(warn)}")
if err: sys.exit(1)
print("G10 컷 설계 정합 OK ✓ (주의 항목은 프레임을 뽑아 눈으로 판정)")
