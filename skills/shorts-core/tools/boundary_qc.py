# G15 경계 지각 검사 (신설 2026-08-27) — 전 컷 경계의 앞 2f+뒤 2f 스트립 + 기계 측정
# 잡는 것: ① 30도 법칙 위반(경계 전후가 너무 비슷 = 같은 피사체 비슷한 앵글) ② 밝기 급변
#          ③ 모션 방향 충돌 ④ (디졸브 구간은 별도 육안)
# 사용: python3 tools/boundary_qc.py <최종본.mp4> <cut_frames.json> [출력접두]
import subprocess, sys, json, os
import numpy as np, cv2
from PIL import Image, ImageDraw

VIDEO, CUTS = sys.argv[1], sys.argv[2]
PFX = sys.argv[3] if len(sys.argv) > 3 else "work/g15"
cuts = json.load(open(CUTS))["cuts"]
FPS = 24.0

# 전 프레임 그레이 로드 (저해상)
r = subprocess.run(["ffmpeg","-v","error","-i",VIDEO,"-vf","crop=1080:1080:0:420,scale=160:160","-f","rawvideo","-pix_fmt","gray","-"],capture_output=True)
buf = np.frombuffer(r.stdout, np.uint8)
N = len(buf)//(160*160)
F = buf[:N*160*160].reshape(N,160,160).astype(np.float32)
print(f"프레임 {N}개 로드")

def flow_dir(a,b):
    f = cv2.calcOpticalFlowFarneback(a,b,None,0.5,3,15,3,5,1.2,0)
    fx,fy = f[...,0].mean(), f[...,1].mean()
    mag = float(np.hypot(fx,fy))
    return fx,fy,mag

flags=[]; rows=[]
bounds=[c for c in cuts if c>0]
for bi,f0 in enumerate(bounds):
    if f0>=N: continue
    a2,a1,b1,b2 = F[max(f0-2,0)],F[f0-1],F[f0],F[min(f0+1,N-1)]
    d_cut = float(np.abs(b1-a1).mean())               # 경계 diff
    d_in  = (float(np.abs(a1-a2).mean())+float(np.abs(b2-b1).mean()))/2  # 샷 내부 diff
    dbri  = float(b1.mean()-a1.mean())                # 밝기 점프
    issues=[]
    if d_cut < max(6.0, d_in*1.6): issues.append(f"유사경계(30도?) d={d_cut:.1f}/in{d_in:.1f}")
    if abs(dbri) > 60: issues.append(f"밝기급변 {dbri:+.0f}")
    fxa,fya,ma = flow_dir(a2,a1); fxb,fyb,mb = flow_dir(b1,b2)
    if ma>0.8 and mb>0.8:
        cosang = (fxa*fxb+fya*fyb)/(ma*mb+1e-9)
        if cosang < -0.5: issues.append(f"모션역전 cos={cosang:.2f}")
    rows.append((f0,d_cut,d_in,dbri,issues))
    if issues: flags.append((f0,issues))

# 스트립 시트 (플래그 경계만 + 전체 미니맵)
os.makedirs("work",exist_ok=True)
def grab(fr):
    t=fr/FPS
    subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{t:.4f}","-i",VIDEO,"-frames:v","1","-vf","crop=1080:1080:0:420,scale=180:180","work/_bq.png"])
    return Image.open("work/_bq.png").copy()
if flags:
    per=6
    for si in range(0,len(flags),per):
        part=flags[si:si+per]
        im=Image.new('RGB',(180*4+40,200*len(part)),(15,15,15)); dr=ImageDraw.Draw(im)
        for r_,(f0,iss) in enumerate(part):
            for c_,fr in enumerate([f0-2,f0-1,f0,f0+1]):
                im.paste(grab(fr),(180*c_+(40 if c_>=2 else 0),200*r_+18))
            dr.text((4,200*r_+2),f"f{f0} {f0/FPS:.2f}s "+";".join(iss),fill=(255,220,0))
        im.save(f"{PFX}_flag{si//per}.png")
print(f"\n경계 {len(bounds)}곳 검사 — 플래그 {len(flags)}건")
for f0,iss in flags: print(f"  f{f0} ({f0/FPS:.2f}s): {'; '.join(iss)}")
print("판정: 플래그 스트립(work/g15_flag*.png)을 눈으로 보고 기각/수정 결정")
