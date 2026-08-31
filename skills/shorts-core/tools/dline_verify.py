# 게이트 G12: 전 D블록 재전사 검증 — 오디오 컷 안에 그 대사가 실제로 있는지 (2026-08-27 테트리스 사고로 신설)
# 사고: b22 오디오를 지도 시각(6.72)으로 잘랐는데 실제 대사는 11.96 — 자막만 나오고 음악이 울렸다.
# 사용법: 프로젝트 work/ 에 복사 → P·SEGS(블록, 소스, 시작초, 길이)를 그 프로젝트 D블록 범위로 채우고 실행.
# 출력의 어절 시각과 DAUD 의 (audio_ss, frames) 가 전부 일치해야 통과. asr_chunk.py 가 같은 폴더에 있어야 한다.
import subprocess, json, concurrent.futures as cf
P="<작업루트>/2026-08-26-10_테트리스"
SEGS=[("b1","seg_2450.mkv",4,20),("b5","seg_2150.mkv",9,16),("b8","seg_2670.mkv",8,26),
      ("b11","seg_5605.mkv",24,15),("b13","seg_5875.mkv",44,23),("b15","seg_5875.mkv",71,13),
      ("b17","seg_5875.mkv",244,13),("b22","seg_6645.mkv",0,30)]
def run(seg):
    tag,src,ss,dur=seg
    mp3=f"_vd{tag}.mp3"; out=f"_vd{tag}.json"
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(ss),"-i",f"{P}/{src}","-t",str(dur),
                    "-vn","-ac","1","-ar","16000","-b:a","48k",mp3],check=True)
    subprocess.run(["python3","asr_chunk.py",mp3,str(ss),out],
                   check=True,capture_output=True)
    return tag
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(run,SEGS))
for tag,src,_,_ in SEGS:
    print("=====",tag,src)
    line=[]; last=None
    for w,s,e,spk in json.load(open(f"_vd{tag}.json")):
        if last is not None and s-last>0.9:
            print(" ".join(line)); line=[]
        if not line: line=[f"[{s:6.2f}]"]
        line.append(w); last=e
    if line: print(" ".join(line))
