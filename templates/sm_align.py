# Speechmatics 배치 전사 — 나레이션 wav 어절 타임스탬프
import json, os, subprocess, time, urllib.request, mimetypes, uuid
KEY=open(os.path.expanduser("~/.volcano/keys/speechmatics")).read().strip()
BASE="https://asr.api.speechmatics.com/v2"
def api(path, method="GET", data=None, headers=None, tries=5):
    last=None
    for k in range(tries):
        try:
            req=urllib.request.Request(BASE+path, data=data, method=method,
                headers={"Authorization":f"Bearer {KEY}", **(headers or {})})
            with urllib.request.urlopen(req, timeout=300) as r: return r.read()
        except Exception as e:
            last=e; time.sleep(4*(k+1))
    raise last
def submit(path):
    boundary=uuid.uuid4().hex
    cfg=json.dumps({"type":"transcription","transcription_config":{"language":"ko","operating_point":"enhanced"}})
    body=b""
    body+=f"--{boundary}\r\nContent-Disposition: form-data; name=\"config\"\r\n\r\n{cfg}\r\n".encode()
    body+=f"--{boundary}\r\nContent-Disposition: form-data; name=\"data_file\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
    body+=open(path,"rb").read()+f"\r\n--{boundary}--\r\n".encode()
    r=json.loads(api("/jobs","POST",body,{"Content-Type":f"multipart/form-data; boundary={boundary}"}))
    return r["id"]
jobs={}
for i in (0,1,3,4,6,8,10,11,12,13,14,15,16,17,20,22):
    jobs[i]=submit(f"work/tts/n{i:02d}.wav")
    print(f"n{i:02d} job {jobs[i]}")
words={}
for i,jid in jobs.items():
    for _ in range(60):
        st=json.loads(api(f"/jobs/{jid}"))["job"].get("status")
        if st=="done": break
        if st in ("rejected","deleted"): raise SystemExit(f"job {jid} {st}")
        time.sleep(3)
    tr=json.loads(api(f"/jobs/{jid}/transcript?format=json-v2"))
    ws=[]
    for res in tr["results"]:
        if res["type"]!="word": continue
        ws.append([res["alternatives"][0]["content"], res["start_time"], res["end_time"]])
    words[i]=ws
    print(f"n{i:02d}: {' '.join(w[0] for w in ws)}")
json.dump(words, open("work/tts/words.json","w"), ensure_ascii=False)
print("DONE")
