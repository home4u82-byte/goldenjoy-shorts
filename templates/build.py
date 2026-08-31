# 가타카 — 23.976fps 네이티브 · crop 800 (1920x800 소재, y=0) · 단일 소스
import json, re, subprocess, sys, math, os
import concurrent.futures as cf
P="<프로젝트 폴더 절대경로>"  # ★채우기
FPS=24000/1001; FPSS="24000/1001"; CROP=800; CY=0
SRC="<소재 영화 파일 절대경로>"  # ★채우기
W=f"{P}/work/blocks"; NARR=f"{P}/work/tts"
sys.path.insert(0,f"{P}/work")
from cards import CARDS, align
from spec import NCUTS, DSEG, ORDER, DVID
from dcaps import DCAPS
CARD_T={bi:align(bi) for bi in CARDS}
XS=json.load(open(f"{P}/work/xs.json"))
s06=json.load(open("<작업루트>/cache/<영화명>/scenes06.json"))
s30=json.load(open("<작업루트>/cache/<영화명>/scenes30.json"))
def scene_end(t, bnds):
    for b in bnds:
        if b > t+0.30: return b-0.15
    return t+20.0
# ---- N블록 컷 ----
CUTS={}
for bi,cs in NCUTS.items():
    CUTS[bi]=[(ss, XS[f"b{bi}c{i}"]["x"], ci, scene_end(ss,s30), 0) for i,(ss,ci) in enumerate(cs)]
# ---- D블록 조각/컷 (프레임 격자 스냅) ----
DAUD={}; DCUTS={}
for bi,segs in DSEG.items():
    aud=[]; cuts=[]
    for ss,dur in segs:
        f0=round(ss*FPS); f1=round((ss+dur)*FPS)
        aud.append((f0/FPS, f1-f0))
        inner=[b for b in s06 if ss+0.35 < b < ss+dur-0.35]
        pts=[f0]+[round(b*FPS) for b in inner]+[f1]
        for k in range(len(pts)-1):
            nm=f"b{bi}c{len(cuts)}"
            t=DVID.get(nm, pts[k]/FPS)   # 비디오만 화자 화면으로 교체 (오디오는 조각 그대로)
            cuts.append((t, XS[nm]["x"], pts[k+1]-pts[k], scene_end(t,s06)))
    DAUD[bi]=aud; DCUTS[bi]=cuts
secs=json.load(open(f"{NARR}/secs.json")); secs={int(k):v for k,v in secs.items()}
FRAMES={bi:math.ceil((s+0.10)*FPS) for bi,s in secs.items()}
for bi,a in DAUD.items(): FRAMES[bi]=sum(x[1] for x in a)
SEC={k:v/FPS for k,v in FRAMES.items()}
order=ORDER
OFF={}; t=0.0
for bi in order: OFF[bi]=t; t+=SEC[bi]
TOTAL=t
NARRB=set(CARDS.keys())
VTAIL={0:7}
XFADE_IN={}
print("블록 프레임:",{k:FRAMES[k] for k in order}); print("총길이:",round(TOTAL,3))

def nframes(bi):
    cards=CARD_T[bi]; total=FRAMES[bi]; cuts=CUTS[bi]
    bnds=[0 if c[2] is None else (round(c[2]*FPS) if isinstance(c[2],float) else round(cards[c[2]][1]*FPS))
          for c in cuts]+[total]
    fr=[bnds[i+1]-bnds[i] for i in range(len(cuts))]
    assert all(f>=19 for f in fr) and sum(fr)==total, (bi,fr,total)
    return fr
def vfilter(i,x,f,ext):
    return (f"[{i}:v]crop={CROP}:{CROP}:{x}:{CY},scale=1080:1080:flags=lanczos,unsharp=5:5:0.7,setsar=1,fps={FPSS},"
            f"tpad=stop_mode=clone:stop_duration=3,trim=end_frame={f+ext},setpts=PTS-STARTPTS,settb=AVTB")
def build_n(bi):
    cuts=CUTS[bi]; fr=nframes(bi); sec=SEC[bi]; tail=VTAIL.get(bi,0)
    argv=["ffmpeg","-y"]; vss=[]
    for idx,(c,f) in enumerate(zip(cuts,fr)):
        ss,x,ci,se,mute=c
        ext=tail if idx==len(cuts)-1 else 0
        t_in=min((f+ext)/FPS+0.35, se-ss)
        assert t_in>=(f+ext)/FPS, (bi,idx,"장면경계 초과",round(t_in,3),round((f+ext)/FPS,3))
        argv+=["-ss",f"{ss-0.02:.4f}","-t",f"{t_in+0.02:.4f}","-i",SRC]; vss.append((ss,x,f,ext,mute))
    argv+=["-i",f"{NARR}/n{bi:02d}.wav"]
    n=len(cuts); fc=[]
    for i,(ss,x,f,ext,mute) in enumerate(vss):
        fc.append(vfilter(i,x,f,ext)+f"[v{i}]")
        d=f/FPS; mv=",volume=0" if mute else ""
        fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=48000:async=1,apad,atrim=0:{d:.6f},asetpts=PTS-STARTPTS{mv},"
                  f"afade=t=in:st=0:d=0.001,afade=t=out:st={d-0.001:.6f}:d=0.001[a{i}]")
    if n>1: fc.append("".join(f"[v{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0,settb=AVTB[cv]")
    else: fc.append("[v0]null[cv]")
    fc.append("".join(f"[a{i}]" for i in range(n))+f"concat=n={n}:v=0:a=1[ca]" if n>1 else "[a0]anull[ca]")
    wl=int(round(sec*48000))
    ln="loudnorm=I=-23.0:TP=-3:LRA=11,aresample=48000,asetpts=N/SR/TB,"
    fc.append(f"[ca]{ln}volume=0.1778,afade=t=in:st=0:d=0.002:curve=qsin[m0];"
              f"[{n}:a]afade=t=in:st=0:d=0.008,apad[m1];[m0][m1]amix=inputs=2:duration=first:normalize=0,"
              f"apad=whole_len={wl},atrim=0:{sec:.6f},afade=t=out:st={sec-0.002:.6f}:d=0.002:curve=qsin[a]")
    return argv,fc
def build_d(bi):
    cuts=DCUTS[bi]; aud=DAUD[bi]; sec=SEC[bi]; tail=VTAIL.get(bi,0)
    assert sum(c[2] for c in cuts)==sum(a[1] for a in aud)==FRAMES[bi], (bi,sum(c[2] for c in cuts),sum(a[1] for a in aud),FRAMES[bi])
    argv=["ffmpeg","-y"]; vss=[]
    for idx,(ss,x,f,se) in enumerate(cuts):
        ext=tail if idx==len(cuts)-1 else 0
        t_in=max((f+ext)/FPS+0.02, min((f+ext)/FPS+0.35, se-ss))
        argv+=["-ss",f"{ss-0.02:.4f}","-t",f"{t_in+0.02:.4f}","-i",SRC]; vss.append((ss,x,f,ext))
    n=len(cuts)
    for (ass_,f) in aud: argv+=["-ss",f"{ass_:.4f}","-t",f"{f/FPS+0.35:.4f}","-i",SRC]
    fc=[]
    for i,(ss,x,f,ext) in enumerate(vss): fc.append(vfilter(i,x,f,ext)+f"[v{i}]")
    for i,(ass_,f) in enumerate(aud):
        d=f/FPS
        fc.append(f"[{n+i}:a]asetpts=PTS-STARTPTS,aresample=48000:async=1,apad,atrim=0:{d:.6f},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:st=0:d=0.001,afade=t=out:st={d-0.001:.6f}:d=0.001[a{i}]")
    na=len(aud)
    fc.append("".join(f"[v{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0[cv]" if n>1 else "[v0]null[cv]")
    fc.append("".join(f"[a{i}]" for i in range(na))+f"concat=n={na}:v=0:a=1[ca]" if na>1 else "[a0]anull[ca]")
    wl=int(round(sec*48000))
    fc.append(f"[ca]loudnorm=I=-23.0:TP=-3:LRA=11,aresample=48000,asetpts=N/SR/TB,apad=whole_len={wl},atrim=0:{sec:.6f},"
              f"afade=t=in:st=0:d=0.002:curve=qsin,afade=t=out:st={sec-0.002:.6f}:d=0.002:curve=qsin[a]")
    return argv,fc
TAIL=["-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-color_range","tv",
      "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709","-r",FPSS,
      "-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-video_track_timescale","24000"]
os.makedirs(W,exist_ok=True)
rows=[]; gcut={"cuts":[],"dissolves":[]}; gf=0
for bi in order:
    if bi in NARRB:
        fr=nframes(bi)
        for k,(c,f) in enumerate(zip(CUTS[bi],fr)):
            ss,x,ci,se,mute=c
            rows.append({"b":bi,"i":k,"kind":"N","src":0,"ss":round(ss,3),"se":round(ss+f/FPS,3),"x":x,"sce":se})
    else:
        fr=[c[2] for c in DCUTS[bi]]
        for k,(ss,x,f,se) in enumerate(DCUTS[bi]):
            rows.append({"b":bi,"i":k,"kind":"D","src":0,"ss":round(ss,3),"se":round(ss+f/FPS,3),"x":x,"sce":se})
    for k,f in enumerate(fr):
        if k>0: gcut["cuts"].append(gf)
        gf+=f
    if bi!=order[-1]: (gcut["dissolves"] if bi==0 else gcut["cuts"]).append(gf)
json.dump(rows, open(f"{P}/work/cut_design.json","w"))
json.dump(gcut, open(f"{P}/work/cut_frames.json","w"))
print(f"cut_design {len(rows)}컷 dump")
if "--design" not in sys.argv:
    jobs=[]
    for bi in order:
        argv,fc = build_n(bi) if bi in NARRB else build_d(bi)
        jobs.append((bi,argv+["-filter_complex",";".join(fc),"-map","[cv]","-map","[a]"]+TAIL+[f"{W}/b{bi:02d}.mp4","-loglevel","error"]))
    def run(j):
        bi,a=j; r=subprocess.run(a,capture_output=True,text=True)
        return bi,r.returncode,(r.stderr or '')[-1200:]
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        for bi,rc,err in ex.map(run,jobs):
            print(f"b{bi:02d} rc={rc} {'OK' if rc==0 else err}", flush=True)
            if rc: sys.exit(1)
def ts(t):
    h=int(t//3600); m=int((t%3600)//60); s=t-h*3600-m*60
    return f"{h}:{m:02d}:{s:05.2f}"
HEAD="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: headline_line1,Cafe24 Ohsquare,102,&H00FCFBFC,&H00FCFBFC,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,40,40,20,1
Style: headline_line2,Cafe24 Ohsquare,102,&H001BFFF6,&H001BFFF6,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,40,40,20,1
Style: band_narr,MHNarrFallback,84,&H00FCFCFC,&H00FCFCFC,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5.5,0,8,40,40,20,1
Style: band_dlg__0,SeoulHangang M,75,&H0019FFF7,&H0019FFF7,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5.5,0,8,40,40,20,1
Style: band_dlg__1,SeoulHangang M,75,&H00FCF960,&H00FCF960,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5.5,0,8,40,40,20,1
Style: band_dlg__2,SeoulHangang M,75,&H009686E7,&H009686E7,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5.5,0,8,40,40,20,1
Style: band_dlg__3,SeoulHangang M,75,&H0074FE47,&H0074FE47,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5.5,0,8,40,40,20,1
Style: band_dlg__4,SeoulHangang M,75,&H004294F3,&H004294F3,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5.5,0,8,40,40,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
HL1,HL2 = json.load(open(f"{P}/work/headline.json")) if os.path.exists(f"{P}/work/headline.json") else ["태어난 순간 수명이","정해진 남자"]
ev=[]
ev.append((0.0,f"Dialogue: 3,{ts(0)},{ts(TOTAL)},headline_line1,,0,0,0,,{{\\an8\\pos(540,211)}}{HL1}"))
ev.append((0.0,f"Dialogue: 3,{ts(0)},{ts(TOTAL)},headline_line2,,0,0,0,,{{\\an8\\pos(540,296)}}{HL2}"))
for bi in sorted(NARRB):
    off=OFF[bi]; cards=CARD_T[bi]
    for i,(txt,s,e) in enumerate(cards):
        st=off+s
        en=off+cards[i+1][1] if i+1<len(cards) else off+SEC[bi]
        fad="\\fad(67,33)" if i==0 else "\\fad(0,33)"
        ev.append((st,f"Dialogue: 2,{ts(st)},{ts(en)},band_narr,,0,0,0,,{{\\an8\\pos(540,1271.04){fad}}}"+re.sub(r'[,.]','',txt)))
def dtime(bi, at):
    cum=0.0
    for (ss,f) in DAUD[bi]:
        d=f/FPS
        if ss-0.05 <= at < ss+d: return cum+max(0.0, at-ss)
        cum+=d
    raise ValueError(f"b{bi} 자막 {at} 가 오디오 조각 밖")
for bi,items in DCAPS.items():
    off=OFF[bi]; blockend=SEC[bi]
    tl=[(txt,spk,dtime(bi,at)) for txt,spk,at in items]
    for i,(txt,spk,rt) in enumerate(tl):
        st=off+rt
        en=off+tl[i+1][2] if i+1<len(tl) else off+blockend
        fad="\\fad(67,33)" if i==0 else "\\fad(0,33)"
        ev.append((st,f"Dialogue: 2,{ts(st)},{ts(en)},band_dlg__{spk},,0,0,0,,{{\\an8\\pos(540,1274.93){fad}}}{txt}"))
ev.sort(key=lambda z:z[0])
open(f"{P}/work/captions.ass","w").write(HEAD+"\n".join(e[1] for e in ev)+"\n")
json.dump({"total":TOTAL,"off":{str(k):v for k,v in OFF.items()},"frames":{str(k):v for k,v in FRAMES.items()},
           "secs":{str(k):v for k,v in SEC.items()},"tail":{str(k):v for k,v in VTAIL.items()},"order":order,"fps":FPS},
          open(f"{P}/work/meta.json","w"))
print("captions.ass 완료, TOTAL=",round(TOTAL,4), "자막", len(ev))
