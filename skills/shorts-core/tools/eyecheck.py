# 전 컷 경계 눈 검사 — 최종본에서 경계 앞 2f + 뒤 2f 를 뽑아 시트로
import json, subprocess, io, sys
import concurrent.futures as cf
from PIL import Image, ImageDraw
V="테트리스2_약속_v1.mp4"
gc=json.load(open("work/cut_frames.json"))
bounds=sorted(gc["cuts"]+gc["dissolves"])
FPS=24
def grab(fr,w=235):
    t=fr/FPS
    p=subprocess.run(["ffmpeg","-v","error","-ss",f"{max(0,t-0.021):.4f}","-i",V,"-frames:v","1",
                      "-vf",f"crop=1080:1080:0:420,scale={w}:{w}","-f","image2pipe","-vcodec","png","-"],capture_output=True).stdout
    return Image.open(io.BytesIO(p))
per=12
frames=sorted({f for b in bounds for f in (b-2,b-1,b,b+1) if f>=0})
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    imgs=dict(zip(frames, ex.map(grab, frames)))
for gi in range(0, len(bounds), per):
    grp=bounds[gi:gi+per]; W=235
    sh=Image.new("RGB",(W*4+30,W*len(grp)),"black")
    d=ImageDraw.Draw(sh)
    for r,b in enumerate(grp):
        for c,fr in enumerate([b-2,b-1,b,b+1]):
            im=imgs[fr].copy()
            dd=ImageDraw.Draw(im)
            if c==2: dd.rectangle([0,0,im.width-1,im.height-1],outline="red",width=3)
            sh.paste(im,(30+W*c,W*r))
        d.text((2,W*r+4),f"{b}\n{b/24:.2f}s",fill="yellow")
    sh.save(f"work/eye_{gi//per}.png")
    print(f"eye_{gi//per}.png {len(grp)}경계")
print("경계 총", len(bounds))
