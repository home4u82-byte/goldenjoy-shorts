# 가타카 — 명화관 남자 음성 나레이션
import json, os, subprocess, sys, time, urllib.request
KEY=open(os.path.expanduser("~/.config/goldenjoy-shorts/keys/typecast")).read().strip()
EP="https://api.typecast.ai/v1/text-to-speech"
VOICE="tc_68662745779b66ba84fc4d84"
TEXTS={
 0:"태어난 순간 병원이, 아이의 수명부터 정해줬습니다.",
 1:"부모는 사랑으로 아이를 가졌지만, 세상은 유전자로 사람을 걸렀습니다.",
 3:"부모는 다음 아이만큼은 실험실에서 고르기로 했습니다. 완벽하게 설계된 동생 안톤이었죠.",
 4:"형이 동생을 이겨볼 수 있는 곳은 바다뿐이었습니다. 유전자로는 이미 진 승부였지만, 물에서는 누가 먼저 겁먹는지로 겨뤘거든요. 먼저 돌아서는 쪽이 지는 겁니다. 지는 쪽은 언제나 형이었죠.",
 6:"형은 우주에 가고 싶었습니다. 부모의 대답은 이랬죠.",
 8:"그러던 어느 날, 동생이 마지막 시합을 걸어왔습니다.",
 10:"그런데 그날은 달랐습니다. 동생이 아무리 앞서 나가려 해도, 형이 계속 옆에 붙어 있었죠.",
 11:"먼저 가라앉은 건 동생이었고, 형이 그를 끌고 뭍으로 나왔습니다. 그날 형은 자기가 약하지 않다는 걸 알았습니다.",
 12:"어른이 된 형은, 남의 인생을 통째로 빌립니다. 돈이 필요했던 남자와 거래한 거죠.",
 13:"완벽한 유전자를 타고났지만, 사고로 다리를 쓰지 못하게 된 남자였죠. 형은 그의 피와 소변, 머리카락을 매일 몸에 붙이고 출근했습니다.",
 14:"키까지 맞춰야 했습니다. 양쪽 다리를 부러뜨려 늘리는 수술이었죠.",
 15:"그렇게 그는 우주 회사에 들어갔고, 토성의 위성으로 떠나는 비행사로 뽑혔습니다.",
 16:"출발을 코앞에 두고 회사 간부가 살해당했습니다. 현장에 떨어진 속눈썹 하나가, 하필 형의 것이었죠.",
 17:"수사를 맡은 형사는, 놀랍게도 그 동생이었습니다.",
 22:"진범은 따로 잡혔지만, 동생은 형을 놓아주지 않았습니다. 동생에게 형은, 여전히 구해줘야 할 사람이었거든요.",
 20:"형제는 다시 바다로 들어갔습니다.",
}
D="work/tts"; os.makedirs(D, exist_ok=True)
secs={}
for i,txt in TEXTS.items():
    raw=f"{D}/m{i:02d}.raw.wav"
    if not (os.path.exists(raw) and os.path.getsize(raw)>2000):
        body={"voice_id":VOICE,"text":txt,"model":"ssfm-v30","language":"KOR",
              "prompt":{"emotion_type":"preset","emotion_preset":"tonedown","emotion_intensity":1.5},
              "output":{"volume":100,"audio_pitch":0,"audio_tempo":1.2,"audio_format":"wav"}}
        for att in range(4):
            try:
                req=urllib.request.Request(EP,data=json.dumps(body).encode(),
                    headers={"X-API-KEY":KEY,"Content-Type":"application/json"},method="POST")
                with urllib.request.urlopen(req,timeout=120) as r: data=r.read()
                open(raw,"wb").write(data); break
            except urllib.error.HTTPError as e:
                print(f"[{i}] HTTP {e.code}", e.read().decode('utf-8','ignore')[:200])
                if e.code in (500,502,503,504) and att<3: time.sleep([2,4,8,16][att]); continue
                sys.exit(1)
    norm=f"{D}/m{i:02d}.norm.wav"; out=f"{D}/n{i:02d}.wav"
    subprocess.run(["ffmpeg","-y","-i",raw,"-af","loudnorm=I=-23.0:TP=-3:LRA=9","-ar","48000","-ac","1",norm],check=True,capture_output=True)
    subprocess.run(["ffmpeg","-y","-i",norm,"-af","silenceremove=start_periods=1:start_threshold=-38dB:start_silence=0.02:stop_periods=-1:stop_threshold=-38dB:stop_duration=0.20:stop_silence=0.02,loudnorm=I=-23:TP=-3:LRA=9","-ar","48000","-ac","2",out],check=True,capture_output=True)
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",out],capture_output=True,text=True)
    secs[i]=round(float(p.stdout.strip()),3)
    print(f"n{i:02d}.wav {secs[i]}s", flush=True)
json.dump(secs,open(f"{D}/secs.json","w")); print("TTS DONE 총", round(sum(secs.values()),2),"초")
