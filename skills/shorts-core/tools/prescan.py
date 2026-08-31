# 소재 사전 분석 배치 — 영화별 캐시 생성 (편당 제작에서 소재 분석 시간을 0으로)
# 캐시: <작업루트>/cache/<파일명>/ {info,crop,scenes30,scenes06,subscan}.json + words_all.json + transcript_lines.txt
# 사용: nohup python3 prescan.py [영화폴더] &   (무인 실행, 이미 있는 항목은 건너뜀)
import os, sys, json, re, subprocess, glob, time
import concurrent.futures as cf
MOVIES=sys.argv[1] if len(sys.argv)>1 else os.environ.get("MOVIES_DIR", ".")
CACHE="<작업루트>/cache"
ASR=os.path.join(os.path.dirname(os.path.abspath(__file__)),"asr_chunk.py")
PYBIN="python3"

def run(c,**k): return subprocess.run(c,capture_output=True,text=True,**k)
def probe(src):
    r=run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
           "stream=width,height,r_frame_rate","-show_entries","format=duration","-of","json",src])
    d=json.loads(r.stdout); st=d["streams"][0]
    num,den=st["r_frame_rate"].split("/")
    return {"w":st["width"],"h":st["height"],"fps":float(num)/float(den),"dur":float(d["format"]["duration"])}
def scenes(src,th,out,dur):
    tmp=out+".raw"
    run(["ffmpeg","-hide_banner","-i",src,"-vf",f"select='gt(scene,{th})',metadata=print:file={tmp}","-an","-f","null","-"])
    ts=sorted(set(round(float(m),3) for m in re.findall(r"pts_time:([0-9.]+)",open(tmp).read())))
    json.dump(ts,open(out,"w")); os.remove(tmp); return len(ts)
def cropdet(src,dur):
    vals={}
    for t in [dur*0.15,dur*0.4,dur*0.6,dur*0.85]:
        r=run(["ffmpeg","-hide_banner","-ss",str(int(t)),"-t","2","-i",src,"-vf","cropdetect=24:16:0","-f","null","-"])
        for m in re.findall(r"crop=([0-9:]+)",r.stderr): vals[m]=vals.get(m,0)+1
    return max(vals,key=vals.get) if vals else None
def subscan(src,info):
    """하드서브 탐지 — 30초 간격, 화면 하단 40%에서 밝은픽셀 행의 최상단 y (어두운 외곽선 인접)"""
    import numpy as np, io
    from PIL import Image
    H=info["h"]; tops=[]
    for t in range(120,int(info["dur"])-120,30):
        r=subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",src,"-frames:v","1",
                          "-f","image2pipe","-vcodec","png","-"],capture_output=True)  # 바이너리 캡처 (text 금지)
        try: a=np.array(Image.open(io.BytesIO(r.stdout)).convert("L")).astype(float)
        except Exception: continue
        rows=[y for y in range(int(H*0.6),H) if (a[y]>200).sum()>25]
        if rows: tops.append(rows[0])
    return {"n":len(tops),"min_top":min(tops) if tops else None,
            "hist":{str(k):tops.count(k) for k in sorted(set(tops))} if tops else {}}
def transcribe(src,dur,cdir):
    mp3=os.path.join(cdir,"_a.mp3")
    run(["ffmpeg","-y","-v","error","-i",src,"-vn","-ac","1","-ar","16000","-b:a","48k",mp3])
    segs=[]; t=0
    while t<dur: segs.append((t,min(1200,dur-t))); t+=1200
    def one(i_s):
        i,(ss,d)=i_s
        part=os.path.join(cdir,f"_a{i}.mp3"); out=os.path.join(cdir,f"_w{i}.json")
        run(["ffmpeg","-y","-v","error","-ss",str(ss),"-t",str(d),"-i",mp3,"-c","copy",part])
        for att in range(3):
            r=run([PYBIN,ASR,part,str(ss),out])
            if r.returncode==0: return out
            time.sleep(20)
        return None
    outs=[]
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        outs=list(ex.map(one,enumerate(segs)))
    words=[]
    for o in outs:
        if o and os.path.exists(o): words+=json.load(open(o))
    words.sort(key=lambda w:w[1])
    json.dump(words,open(os.path.join(cdir,"words_all.json"),"w"))
    with open(os.path.join(cdir,"transcript_lines.txt"),"w") as f:
        line=[]; start=None
        for w,s,e,sp in words:
            if start is None: start=s
            line.append(w)
            if w.endswith((".","!","?")):
                f.write(f"{int(start//60):3d}:{int(start%60):02d} {' '.join(line)}\n"); line=[]; start=None
    for g in glob.glob(os.path.join(cdir,"_a*.mp3"))+glob.glob(os.path.join(cdir,"_w*.json")): os.remove(g)
    return len(words)

SKIP=set()
_sf=os.path.join(CACHE,"skip.txt")
if os.path.exists(_sf):
    SKIP={l.strip() for l in open(_sf) if l.strip()}
for src in sorted(glob.glob(os.path.join(MOVIES,"*"))):
    if not re.search(r"\.(mp4|mkv|avi|mov)$",src,re.I): continue
    name=os.path.splitext(os.path.basename(src))[0]
    if name in SKIP:
        print(f"===== {name} (이미 제작한 영화 — 건너뜀)",flush=True); continue
    cdir=os.path.join(CACHE,name); os.makedirs(cdir,exist_ok=True)
    print(f"===== {name}",flush=True)
    ip=os.path.join(cdir,"info.json")
    info=json.load(open(ip)) if os.path.exists(ip) else probe(src)
    json.dump(info,open(ip,"w"))
    if not os.path.exists(os.path.join(cdir,"crop.json")):
        json.dump({"crop":cropdet(src,info["dur"])},open(os.path.join(cdir,"crop.json"),"w")); print("  crop ok",flush=True)
    for th,fn in [(0.30,"scenes30.json"),(0.06,"scenes06.json")]:
        if not os.path.exists(os.path.join(cdir,fn)):
            n=scenes(src,th,os.path.join(cdir,fn),info["dur"]); print(f"  scenes{th} {n}",flush=True)
    if not os.path.exists(os.path.join(cdir,"subscan.json")):
        json.dump(subscan(src,info),open(os.path.join(cdir,"subscan.json"),"w")); print("  subscan ok",flush=True)
    if not os.path.exists(os.path.join(cdir,"words_all.json")):
        n=transcribe(src,info["dur"],cdir); print(f"  transcript {n} words",flush=True)
print("PRESCAN DONE",flush=True)
