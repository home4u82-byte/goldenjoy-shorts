"""24fps 콘텐츠가 30fps로 늘어난 소재: 컷별 최적 위상 φ 실측.
select='not(eq(mod(n,5),φ))' 로 5중 1을 버려 시간축 보존 + 중복 제거."""
import subprocess, numpy as np
def gray_frames(src, ss, dur, w=160, h=90):
    raw=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-ss",f"{ss:.4f}",
        "-t",f"{dur:.4f}","-i",src,"-vf",f"scale={w}:{h},format=gray","-f","rawvideo","-"],
        capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.uint8).reshape(-1,h,w).astype(np.int16)
def best_phase(src, ss, dur):
    fr=gray_frames(src, ss, dur)
    if len(fr)<10: return 0, 0.0
    d=np.array([np.abs(fr[i]-fr[i-1]).mean() for i in range(1,len(fr))])  # d[i-1] = diff(f[i],f[i-1])
    best,bestv=0,None
    for phi in range(5):
        drop=[i for i in range(1,len(fr)) if i%5==phi]      # 버릴 프레임 n
        v=float(np.mean([d[i-1] for i in drop])) if drop else 9e9
        if bestv is None or v<bestv: best,bestv=phi,v
    return best, bestv
if __name__=="__main__":
    import sys,json
    src=sys.argv[1]
    for a in sys.argv[2:]:
        ss,dur=[float(x) for x in a.split(":")]
        p,v=best_phase(src,ss,dur); print(f"ss={ss} dur={dur} -> phase={p} (mean drop diff {v:.3f})")
