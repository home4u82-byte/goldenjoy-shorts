# 주 피사체 중앙 배치 측정 — 사람이든 사물이든 전부 (2026-08-27 사장님 지시)
# 얼굴(YuNet) 우선, 얼굴이 없거나 작으면 사물(배경 제외 무게중심 + 엣지)로 측정한다.
# 눈대중 금지 — 이 도구의 숫자만 쓴다.
#
# 사용: 프로젝트 폴더에서
#   python3 tools/center_measure.py cuts.json out.json
# cuts.json: [{"name":"b3c0", "src":"seg_255.mkv", "t0":15.35, "t1":17.37}, ...]
# out.json:  {"b3c0": 697, ...}  (crop x 확정값)
import subprocess, sys, os, json
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = next(p for p in [os.path.join("work", "face_detection_yunet.onnx"),
                         os.path.join(HERE, "face_detection_yunet.onnx")] if os.path.exists(p))
det = cv2.FaceDetectorYN.create(MODEL, "", (1920, 800), 0.6, 0.3, 500)
TMP = os.path.join("work", "_cm.png")

def frame(src, t):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", src,
                    "-frames:v", "1", TMP], check=True)
    return cv2.imread(TMP)

def face_center(img):
    det.setInputSize((img.shape[1], img.shape[0]))
    _, f = det.detect(img)
    if f is None or len(f) == 0:
        return None, 0
    ff = max(f, key=lambda r: r[2] * r[3])
    return float(ff[0] + ff[2] / 2), int(ff[2] * ff[3])

def object_center(img):
    """배경(최빈색 평면) 제외 무게중심 x — 사물·차량·게임화면·문서 컷에 쓴다."""
    W = img.shape[1]
    sw = max(240, W // 4)
    small = cv2.resize(img, (sw, 200))
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    q = (lab // 24).reshape(-1, 3)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    bg = vals[counts.argmax()]
    mask = (np.abs(q - bg).sum(axis=1) > 2).reshape(200, sw).astype(np.uint8)
    edges = cv2.Canny(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 60, 160)
    w = mask.astype(float) * 0.6 + (edges > 0).astype(float) * 0.4
    colw = w.sum(axis=0)
    if colw.sum() < 1:
        return None
    # 800px 크롭에 대응하는 창에서 무게가 가장 몰린 지점의 중심
    win = max(8, int(sw * 800 / W))
    cs = np.convolve(colw, np.ones(win), "valid")
    i = int(cs.argmax())
    return (i + win / 2) * (W / sw)

def measure(name, src, t0, t1, n=8):
    ts = np.linspace(t0 + 0.05, max(t0 + 0.06, t1 - 0.05), n)
    fc, oc = [], []
    W = None
    for t in ts:
        img = frame(src, float(t))
        if img is None: continue
        W = img.shape[1]
        c, a = face_center(img)
        if c is not None and a > 12000:
            fc.append(c)
        v = object_center(img)
        if v is not None: oc.append(v)
    if W is None:
        print(f"{name:26s} 프레임 추출 실패"); return None
    if len(fc) >= max(2, n // 3):
        med = float(np.median(fc)); kind = f"얼굴 n={len(fc)}"
        if max(fc) - min(fc) > 300:
            kind += f" ★궤적 {min(fc):.0f}~{max(fc):.0f} — 얼굴이 크게 움직인다: 카드 시각 가중 절충 또는 컷 분할 검토"
    elif oc:
        med = float(np.median(oc)); kind = f"사물 n={len(oc)}"
    else:
        print(f"{name:26s} 측정불가 — 프레임을 직접 봐야 한다"); return None
    x = int(round(min(max(med - 400, 0), W - 800)))
    print(f"{name:26s} {kind} 중심 {med:6.0f} → x={x}")
    return x

if __name__ == "__main__":
    cuts = json.load(open(sys.argv[1]))
    out = {}
    for c in cuts:
        r = measure(c["name"], c["src"], c["t0"], c["t1"])
        if r is not None: out[c["name"]] = r
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    print(f"\n{len(out)}/{len(cuts)} 저장 → {sys.argv[2]}")
