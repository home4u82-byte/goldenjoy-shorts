# 렌더 결과 중앙 배치 검증 (G3) — 얼굴 + 사물 전부. face_verify.py 후속판.
# 카드 중앙 시각마다 최종본에서 주 피사체를 재검출해 화면중앙(540) 오차를 보고한다.
#
# 사용: 프로젝트 폴더에서
#   python3 tools/center_verify.py <최종본.mp4> [work/captions3.ass]
# 기준: 단독 얼굴 컷 / 사물 컷 오차 ≤ ±90px. 투샷·와이드는 ◇ 표시만 하고 통과.
import subprocess, re, sys, os
import numpy as np, cv2

VIDEO = sys.argv[1]
ASS = sys.argv[2] if len(sys.argv) > 2 else "work/captions3.ass"
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = next(p for p in [os.path.join("work", "face_detection_yunet.onnx"),
                         os.path.join(HERE, "face_detection_yunet.onnx")] if os.path.exists(p))
det = cv2.FaceDetectorYN.create(MODEL, "", (1080, 1080), 0.6, 0.3, 500)
TMP = "work/_cv.png"

def sec(x):
    h, m, s = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)

rows = []
for line in open(ASS):
    if not line.startswith("Dialogue:") or "headline" in line: continue
    p = line.split(",", 9)
    rows.append((sec(p[1]), sec(p[2]), re.sub(r"\{[^}]*\}", "", p[9]).strip()))
rows.sort()

def object_center_1080(img):
    """자막 띠 위쪽(상단 800px)만으로 배경 제외 무게중심 x를 잰다."""
    top = img[0:800]
    small = cv2.resize(top, (270, 200))
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    q = (lab // 24).reshape(-1, 3)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    bg = vals[counts.argmax()]
    mask = (np.abs(q - bg).sum(axis=1) > 2).reshape(200, 270).astype(float)
    edges = (cv2.Canny(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 60, 160) > 0).astype(float)
    w = mask * 0.6 + edges * 0.4
    colw = w.sum(axis=0)
    if colw.sum() < 1: return None
    xs = np.arange(270)
    return float((colw * xs).sum() / colw.sum()) * 4.0

bad = []
for s, e, txt in rows:
    m = (s + e) / 2
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{m:.2f}", "-i", VIDEO,
                    "-vf", "crop=1080:1080:0:420", "-frames:v", "1", TMP], check=True)
    img = cv2.imread(TMP)
    det.setInputSize((img.shape[1], img.shape[0]))
    _, f = det.detect(img)
    if f is not None and len(f) > 0:
        ff = max(f, key=lambda r: r[2] * r[3])
        cx = ff[0] + ff[2] / 2; off = cx - 540
        mark = "✓" if abs(off) <= 90 else ("◇다인" if len(f) > 1 else "★치우침")
        if abs(off) > 90 and len(f) == 1: bad.append((m, txt, off, "얼굴"))
        print(f"{m:6.1f}s  얼굴 {cx:5.0f}  오차 {off:+5.0f}  {mark} (얼굴{len(f)})  {txt[:26]}")
    else:
        oc = object_center_1080(img)
        if oc is None:
            print(f"{m:6.1f}s  측정불가 — 프레임 직접 확인  {txt[:26]}"); continue
        off = oc - 540
        mark = "✓" if abs(off) <= 90 else "★치우침"
        if abs(off) > 90: bad.append((m, txt, off, "사물"))
        print(f"{m:6.1f}s  사물 {oc:5.0f}  오차 {off:+5.0f}  {mark}          {txt[:26]}")

print()
if bad:
    print("치우침(>90px) — 전부 x 재조정 대상:")
    for m, t, o, k in bad: print(f"  {m:6.1f}s  [{k}] {int(o):+d}px  {t[:20]}")
    sys.exit(1)
print("전 컷 중앙 배치 OK ✓")
