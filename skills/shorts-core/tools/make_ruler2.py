import subprocess, os, sys, json
from PIL import Image, ImageDraw, ImageFont
SRC="segment_4759_5076.mp4"; os.makedirs("work/ruler",exist_ok=True)
TW,TH=480,200; COLS=4
try: F=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf",17)
except: F=ImageFont.load_default()
def build(name, items):
    rows=(len(items)+COLS-1)//COLS
    c=Image.new("RGB",(COLS*TW,rows*(TH+24)),"black"); d=ImageDraw.Draw(c)
    for i,(lab,t) in enumerate(items):
        tmp=f"work/ruler/_x{i}.png"
        subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",SRC,
            "-vf",f"crop=1920:800:0:140,scale={TW}:{TH}","-frames:v","1",tmp],check=True)
        im=Image.open(tmp); x0=(i%COLS)*TW; y0=(i//COLS)*(TH+24)+24
        c.paste(im,(x0,y0)); d.rectangle([x0,y0-24,x0+TW,y0],fill="#101010")
        d.text((x0+5,y0-21),f"{lab} t={t}",fill="#FFD400",font=F)
        for gx in range(0,1921,320):
            px=x0+int(gx*TW/1920); col="#FF3030" if gx==960 else "#30D0FF"
            d.line([px,y0,px,y0+TH],fill=col,width=1)
            if gx<1920: d.text((px+2,y0+2),str(gx),fill=col,font=F)
        os.remove(tmp)
    c.save(f"work/ruler/{name}.png"); print(name,len(items))
items=json.load(open(sys.argv[1]))
build(sys.argv[2],[(a,b) for a,b in items])
