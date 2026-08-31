# 얼굴 중앙 = 양쪽 눈 + 코 삼각형 무게중심 (2026-08-30 사장님 지시)
# YuNet 랜드마크: f[4],f[5]=오른눈 f[6],f[7]=왼눈 f[8],f[9]=코끝
import subprocess, sys, os, json, tempfile
import concurrent.futures as cf
import numpy as np, cv2
MODEL="work/face_detection_yunet.onnx"
det=cv2.FaceDetectorYN.create(MODEL,"",(1920,1080),0.45,0.3,500)
SRC="<소재 영화 파일 절대경로>"  # ★채우기
TMP="work/_tri.png"
def frame(t, gamma=1.0, out=None):
    out=out or TMP
    vf=f"eq=gamma={gamma}:gamma_weight=0.72," if gamma>1.001 else ""
    subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{t:.3f}","-i",SRC,
                    "-vf",f"{vf}null" if vf else "null","-frames:v","1",out],check=True)
    return cv2.imread(out)
def frames_par(ts, gamma=1.0, workers=8):
    """여러 시각 병렬 추출 → {t: ndarray}. 검출은 호출부에서 직렬로 (cv2 detector 비스레드세이프)."""
    def one(i_t):
        i,t=i_t
        p=os.path.join("work", f"_tri{i}.png")
        frame(t, gamma, p)
        img=cv2.imread(p)
        return t, img
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        return dict(ex.map(one, enumerate(ts)))
def tri_centers(img):
    """프레임 내 모든 얼굴의 (삼각형중심x, 면적) 목록 — 큰 순"""
    det.setInputSize((img.shape[1],img.shape[0]))
    _,fs=det.detect(img)
    if fs is None: return []
    out=[]
    for f in fs:
        cx=(f[4]+f[6]+f[8])/3.0   # 눈눈코 삼각형 무게중심 x
        out.append((float(cx), float(f[2]*f[3]), float(f[0]), float(f[0]+f[2])))
    out.sort(key=lambda z:-z[1])
    return out
def measure(name, t0, t1, n=5, gamma=1.0, pick=0):
    ts=[float(t) for t in np.linspace(t0+0.04, max(t0+0.05,t1-0.04), n)]
    imgs=frames_par(ts, gamma)
    cs=[]
    for t in ts:
        img=imgs.get(t)
        if img is None: continue
        fs=tri_centers(img)
        if len(fs)>pick and fs[pick][1]>2500: cs.append(fs[pick][0])
    if not cs: return None, 0
    return float(np.median(cs)), len(cs)
if __name__=="__main__":
    rows=json.load(open(sys.argv[1]))
    out={}
    for r in rows:
        c,n = measure(r["name"], r["t0"], r["t1"], gamma=r.get("gamma",1.0), pick=r.get("pick",0))
        if c is None:
            c2,n2=measure(r["name"], r["t0"], r["t1"], gamma=1.7, pick=r.get("pick",0))
            if c2 is not None: c,n=c2,n2
        if c is None:
            print(f'{r["name"]:10s} 미검출'); continue
        x=int(round(min(max(c-430,0),2582-860)))
        out[r["name"]]=x
        print(f'{r["name"]:10s} n={n} 삼각중심 {c:7.1f} → x={x}')
    json.dump(out,open(sys.argv[2],"w"))
