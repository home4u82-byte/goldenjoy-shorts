# 효과음 3종 합성 — ① 오프닝 임팩트 ② 플래시백 되감기 whoosh ③ 킥 장면 저음 스웰
import numpy as np, wave, json
SR=48000
def save(name, x, peak_db):
    x=x/ (np.abs(x).max()+1e-9) * (10**(peak_db/20))
    st=np.stack([x,x],1)
    d=(st*32767).astype(np.int16)
    w=wave.open(f"work/sfx_{name}.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(d.tobytes()); w.close()
    print(name, round(len(x)/SR,2),"s")
rng=np.random.default_rng(7)

# ① 임팩트: 서브 붐(58Hz 지수감쇠) + 노이즈 트랜지언트
t=np.arange(int(SR*0.5))/SR
boom=np.sin(2*np.pi*(58*t - 18*t*t))*np.exp(-t*9)          # 피치 살짝 떨어지는 붐
nz=rng.standard_normal(int(SR*0.06))*np.exp(-np.arange(int(SR*0.06))/ (SR*0.012))
imp=boom.copy(); imp[:len(nz)]+=nz*0.5
# 로우패스 느낌: 이동평균
k=24; imp=np.convolve(imp, np.ones(k)/k, 'same')
save("impact", imp, -10)

# ② whoosh: 노이즈 STFT 대역 스윕 (400→2800Hz 올라갔다 사라짐)
dur=0.7; n=int(SR*dur)
nz=rng.standard_normal(n)
X=np.fft.rfft(nz); f=np.fft.rfftfreq(n,1/SR)
# 시간영역 스윕은 조각 합성으로
seg=2048; hop=512; out=np.zeros(n)
win=np.hanning(seg)
for i,st in enumerate(range(0,n-seg,hop)):
    p=st/n
    c=350+2600*(p**1.6)          # 중심주파수 스윕
    bw=c*0.7
    s=nz[st:st+seg]*win
    S=np.fft.rfft(s); fs=np.fft.rfftfreq(seg,1/SR)
    S*=np.exp(-((fs-c)/bw)**2)
    out[st:st+seg]+=np.fft.irfft(S)
env=np.sin(np.pi*np.clip(np.arange(n)/n,0,1)**0.8)**1.5    # 업다운 엔벨로프
save("whoosh", out*env, -16)

# ③ 저음 스웰: 48+96Hz 디튠, 느린 어택
dur=1.6; t=np.arange(int(SR*dur))/SR
sw=(np.sin(2*np.pi*48*t)+0.5*np.sin(2*np.pi*96.5*t)+0.25*np.sin(2*np.pi*144*t))
env=np.clip(t/0.9,0,1)**2 * np.exp(-np.clip(t-1.0,0,None)*4)
save("swell", sw*env, -16)

import sys
meta=json.load(open(sys.argv[1] if len(sys.argv)>1 else "work/v3_meta.json"))
FR={int(k):v for k,v in meta["frames"].items()}
FPS=meta.get("fps",30)
OFF={}; t=0.0
for bi in meta["order"]: OFF[bi]=t; t+=FR[bi]/FPS
whoosh=OFF[18]-0.30           # v2는 시간순이라 되감기 없음 → 형제 대면 진입 지점
# 절정 = b21 마지막 조각(펀치라인 "이게 내 방법이야") 직전
import sys as _s; _s.path.insert(0,"work")
from spec import DSEG
_pre=sum(round((a+d)*FPS)-round(a*FPS) for a,d in DSEG[21][:-1])
kick=OFF[21]+_pre/FPS-0.45
print("배치: impact=0.03s | whoosh=%.2fs | swell=%.2fs" % (whoosh, kick))
json.dump({"impact":0.03,"whoosh":round(whoosh,3),"swell":round(kick,3)}, open("work/sfx_times.json","w"))
