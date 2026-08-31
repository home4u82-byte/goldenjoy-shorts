# 전 컷 얼굴 중앙 오차 감사 — 감마 보정 후 YuNet, 낮은 임계값, 다중 시각
import json, subprocess, os
import numpy as np, cv2
SRC="<소재 영화 파일 절대경로>"  # ★채우기
MODEL="work/face_detection_yunet.onnx" if os.path.exists("work/face_detection_yunet.onnx") else "tools/face_detection_yunet.onnx"
det=cv2.FaceDetectorYN.create(MODEL,"",(800,800),0.45,0.3,500)
rows=json.load(open("work/cut_design.json"))
X=json.load(open("work/cut_x.json"))
G=json.load(open("work/cut_gamma.json"))
out=[]
for r in rows:
    name=f"b{r['b']}c{r['i']}"; x=X.get(name,560); g=G.get(name,1.0)
    eq=f"eq=gamma={g:.2f}:gamma_weight=0.72," if g>1.001 else ""
    cents=[]; areas=[]
    for k in (0.2,0.4,0.5,0.6,0.8):
        t=r['ss']+(r['se']-r['ss'])*k
        subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{t:.3f}","-i",SRC,
            "-vf",f"crop=800:800:{x}:0,{eq}scale=800:800","-frames:v","1","work/_fa.png"],check=True)
        im=cv2.imread("work/_fa.png")
        det.setInputSize((800,800))
        _,f=det.detect(im)
        if f is not None and len(f):
            ff=max(f,key=lambda q:q[2]*q[3])
            if ff[2]*ff[3]>2500:
                cents.append(float(ff[0]+ff[2]/2)); areas.append(float(ff[2]*ff[3]))
    if cents:
        c=float(np.median(cents)); err=round(c-400)
        out.append({"name":name,"kind":r['kind'],"n":len(cents),"cx":round(c),"err":err,
                    "area":round(np.median(areas)),"x":x,"newx":max(0,min(1120,x+err))})
    else:
        out.append({"name":name,"kind":r['kind'],"n":0,"err":None,"x":x})
json.dump(out,open("work/face_audit.json","w"),indent=1,ensure_ascii=False)
print(f"{'컷':8s} {'유형':3s} {'검출':>3s} {'중심':>5s} {'오차':>6s} {'면적':>7s} {'현재x':>6s} {'제안x':>6s}")
for o in out:
    if o["err"] is None: print(f"{o['name']:8s} {o['kind']:3s}   0     -      -        -  {o['x']:6d}   (얼굴 미검출)")
    else:
        mark="  ★" if abs(o['err'])>60 else ""
        print(f"{o['name']:8s} {o['kind']:3s} {o['n']:3d} {o['cx']:5d} {o['err']:+6d} {o['area']:7d} {o['x']:6d} {o['newx']:6d}{mark}")
