# 프레임 단위 흐름 스캔 (게이트 G11) — "미세하게 뚝뚝 끊기는 부분"을 기계로 잡는다 (2026-08-27 사장님 지시)
# 최종본의 모든 인접 프레임 차이를 재서
#   ① 설계에 없는 하드컷(의도 밖 점프 = 튐)
#   ② 중복(정지) 프레임 구간 = 스터터
#   ③ 설계 컷경계인데 화면이 안 바뀌는 곳(전환 누락·중복 렌더 의심)
# 을 전부 보고한다.
#
# 사용: 프로젝트 폴더에서
#   python3 tools/flow_scan.py <최종본.mp4> [work/cut_frames.json]
# cut_frames.json: 설계상 새 컷이 시작하는 "전역 프레임 번호" 정렬 리스트 (빌드 스크립트가 dump).
#   디졸브 경계는 {"cuts":[...], "dissolves":[...]} 로 나눠 줘도 된다 — 디졸브는 스파이크가 없어도 정상.
# 종료코드: 문제 0건이면 0, 아니면 1.
import subprocess, sys, os, json
import numpy as np

VIDEO = sys.argv[1]
r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=avg_frame_rate", "-of", "csv=p=0", VIDEO],
                   capture_output=True, text=True).stdout.strip().split(",")[0]
num, den = (r.split("/") + ["1"])[:2]
FPS = float(num) / float(den)
# 영화 화면부만 스캔 (자막 y1271·헤드라인 상단 제외 → 카드 전환이 스파이크로 잡히지 않게)
CROP = "crop=1080:680:0:440"

design_cuts, design_diss = set(), set()
if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
    d = json.load(open(sys.argv[2]))
    if isinstance(d, dict):
        design_cuts = set(d.get("cuts", [])); design_diss = set(d.get("dissolves", []))
    else:
        design_cuts = set(d)

proc = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-i", VIDEO, "-vf", f"{CROP},scale=270:170,format=gray",
     "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
frames = []
FSZ = 270 * 170
while True:
    buf = proc.stdout.read(FSZ)
    if len(buf) < FSZ: break
    frames.append(np.frombuffer(buf, np.uint8).astype(np.int16))
proc.wait()
N = len(frames)
print(f"프레임 {N}개 ({N/FPS:.2f}s) 스캔")

d = np.array([np.abs(frames[i + 1] - frames[i]).mean() for i in range(N - 1)])

# ① 하드컷 스파이크: 국소 중앙값 대비 급등
issues = []
spikes = []
for i in range(len(d)):
    lo, hi = max(0, i - 8), min(len(d), i + 9)
    nb = np.delete(d[lo:hi], i - lo)
    med = max(1.0, float(np.median(nb)))
    if d[i] > 14 and d[i] > 4.5 * med:
        spikes.append(i + 1)  # 프레임 i+1 에서 새 화면 시작

near = lambda f, S, tol=1: any(abs(f - c) <= tol for c in S)
for f in spikes:
    if design_cuts and not near(f, design_cuts) and not near(f, design_diss, 10):
        issues.append(f"의도 밖 하드컷(튐): 프레임 {f} = {f/FPS:.2f}s (diff {d[f-1]:.1f})")

# ② 중복(정지) 프레임 — 두 갈래로 판정한다:
#   (a) 초당 중복 수가 주기적으로 나오면 fps 변환 판정(24→30 = 정확히 초당 6장) → 오류
#   (b) 3연속 이상 정지 run 은 눈검사 대상(게임화면·문서 등 원본이 디지털 정지화면일 수 있다) → 주의
warns = []
dup = d < 0.35
persec = [int(dup[i:i + int(FPS)].sum()) for i in range(0, max(1, len(dup) - int(FPS)), int(FPS))]
med_dup = int(np.median(persec)) if persec else 0
if med_dup >= 3:
    issues.append(f"fps 변환 중복 프레임: 초당 중복 중앙값 {med_dup}장 — 소스 fps 그대로 렌더했는지 확인 (24→30 강제 금지)")
run = 0
for i in range(len(d)):
    if dup[i]:
        run += 1
    else:
        if run >= 3 and i < len(d) - 5:
            warns.append(f"정지 {run+1}장: {(i-run)/FPS:.2f}~{i/FPS:.2f}s — 원본이 정지 화면인지 눈으로 확인")
        run = 0

# ③ 설계 컷경계에 스파이크 없음 (디졸브 제외)
missing = [c for c in sorted(design_cuts) if 0 < c < N and not near(c, set(spikes), 2)]
for c in missing:
    print(f"  참고: 설계 컷경계 {c}({c/FPS:.2f}s)에 화면 변화 약함 (같은 장면 연속 컷이면 정상)")

print(f"\n검출 하드컷 {len(spikes)}곳" + (f" / 설계 {len(design_cuts)}곳" if design_cuts else " (설계표 없음 — 눈으로 대조)"))
if not design_cuts:
    print("스파이크 시각:", " ".join(f"{f/FPS:.2f}" for f in spikes))
for w in warns[:40]:
    print("주의:", w)
if len(warns) > 40: print(f"주의 … 외 {len(warns)-40}건")
if issues:
    print("\n★ 문제 " + str(len(issues)) + "건:")
    for x in issues: print("  " + x)
    sys.exit(1)
print("G11 프레임 흐름 OK ✓")
