# 블록 조립 v4 — 24fps 네이티브. b0→b1 훅→본편 교차 디졸브 (타이밍 보존)
# xfade offset 은 -1e-4 보정(.6f), 최종 프레임 수 trim 강제 (스킬 ★xfade 프레임 밀림 규칙)
import json, subprocess, sys
meta=json.load(open("work/meta.json"))
FPS=meta["fps"]
FR={int(k):v for k,v in meta["frames"].items()}
SECS={int(k):v for k,v in meta["secs"].items()}
order=meta["order"]
XF=[(0,7)]   # b0→b1 훅→본편 (7f@24 ≈ 0.29s)
argv=["ffmpeg","-y"]
for bi in order: argv+=["-i",f"work/blocks/b{bi:02d}.mp4"]
fc=[]
for i,bi in enumerate(order):
    wl=round(SECS[bi]*48000)
    fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,apad=whole_len={wl},atrim=0:{SECS[bi]:.6f}[a{i}]")
fc.append("".join(f"[a{i}]" for i in range(len(order)))+f"concat=n={len(order)}:v=0:a=1[a]")
xf_after={b:d for b,d in XF}
groups=[]; cur=[]
for bi in order:
    cur.append(bi)
    if bi in xf_after: groups.append(cur); cur=[]
groups.append(cur)
acc=None; acc_frames=0
for gi,g in enumerate(groups):
    ins="".join(f"[{order.index(bi)}:v]" for bi in g)
    gl=f"[g{gi}]"
    if len(g)>1: fc.append(ins+f"concat=n={len(g)}:v=1:a=0,settb=AVTB{gl}")
    else: fc.append(f"[{order.index(g[0])}:v]settb=AVTB{gl}")
    if acc is None:
        acc=gl; acc_frames=sum(FR[bi] for bi in g)
    else:
        prev_b=groups[gi-1][-1]; d=xf_after[prev_b]
        off=acc_frames/FPS - 1e-4
        out=f"[x{gi}]"
        fc.append(f"{acc}{gl}xfade=transition=fade:duration={d/FPS:.6f}:offset={off:.6f},settb=AVTB{out}")
        acc=out; acc_frames+=sum(FR[bi] for bi in g)
fc.append(f"{acc}fps={FPS},trim=end_frame={sum(FR[bi] for bi in order)},setpts=PTS-STARTPTS[v]")
argv+=["-filter_complex",";".join(fc),"-map","[v]","-map","[a]",
 "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p",
 "-color_range","tv","-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
 "-r",str(FPS),"-c:a","pcm_s16le","-video_track_timescale","24000","work/blocks/merged.mkv","-loglevel","error"]
r=subprocess.run(argv,capture_output=True,text=True)
print("merge rc=",r.returncode, (r.stderr or '')[-500:] if r.returncode else "")
sys.exit(r.returncode)
