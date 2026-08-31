# 소리 밸런스 게이트 (G13) — 나레이션 블록과 대사 블록의 데시벨을 똑같게 (2026-08-27 사장님 지시)
# 최종 마스터에서 블록별 통합 라우드니스(LUFS)를 실측해 표로 보고한다.
#
# 사용: 프로젝트 폴더에서
#   python3 tools/audio_balance.py work/master_sfx.wav work/v4_meta.json work/cut_design.json
# 기준: ① 대사(D) 블록 중앙값과 나레이션(N) 블록 중앙값 차 ≤ 2.0 LU
#       ② 개별 블록이 자기 그룹 중앙값에서 ±3.0 LU 초과하면 플래그 (음악만 잡힌 블록·무음 블록 검출)
import subprocess, sys, json, re

WAV = sys.argv[1] if len(sys.argv) > 1 else "work/master_sfx.wav"
META = sys.argv[2] if len(sys.argv) > 2 else "work/v4_meta.json"
CD = sys.argv[3] if len(sys.argv) > 3 else "work/cut_design.json"
meta = json.load(open(META))
fps = meta.get("fps", 30)
FR = {int(k): v for k, v in meta["frames"].items()}
order = meta["order"]
kind = {}
for c in json.load(open(CD)): kind.setdefault(c["b"], c["kind"])

def lufs(ss, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{ss:.4f}", "-t", f"{dur:.4f}", "-i", WAV,
                        "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", r)
    return float(m.group(1)) if m else None

rows = []; t = 0.0
for bi in order:
    dur = FR[bi] / fps
    v = lufs(t, dur)
    rows.append((bi, kind.get(bi, "?"), t, dur, v))
    t += dur

import statistics
Ns = [v for _, k, _, _, v in rows if k == "N" and v is not None]
Ds = [v for _, k, _, _, v in rows if k == "D" and v is not None]
mN = statistics.median(Ns); mD = statistics.median(Ds)
bad = []
for bi, k, ss, dur, v in rows:
    ref = mN if k == "N" else mD
    flag = ""
    if v is None: flag = "★측정불가"
    elif abs(v - ref) > 3.0: flag = f"★그룹 중앙값과 {v-ref:+.1f} LU — 음악/무음 의심, 원본 확인"
    if flag: bad.append(bi)
    print(f"b{bi:02d} {k}  {ss:7.2f}s ~{dur:5.2f}s  I={v if v is not None else '--':>6} LUFS  {flag}")
d = mD - mN
print(f"\n나레이션 중앙값 {mN:.1f} / 대사 중앙값 {mD:.1f} → 차이 {d:+.1f} LU (기준 ≤ ±2.0)")
if abs(d) > 2.0 or bad:
    print("★G13 실패 — 대사·나레이션 레벨을 맞추거나 플래그 블록의 오디오 컷을 재확인하라")
    sys.exit(1)
print("G13 소리 밸런스 OK ✓")
