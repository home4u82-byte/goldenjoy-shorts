import json, os, time, urllib.request, uuid, sys, socket
KEY=open(os.environ.get("SPEECHMATICS_KEY_FILE", os.path.expanduser("~/.config/goldenjoy-shorts/keys/speechmatics"))).read().strip()
BASE="https://asr.api.speechmatics.com/v2"
def api(path, method="GET", data=None, headers=None, tries=4):
    last=None
    for k in range(tries):
        try:
            req=urllib.request.Request(BASE+path, data=data, method=method,
                headers={"Authorization":"Bearer "+KEY, **(headers or {})})
            with urllib.request.urlopen(req, timeout=900) as r: return r.read()
        except Exception as e:
            last=e; time.sleep(5*(k+1))
    raise last
def submit(path):
    boundary=uuid.uuid4().hex
    cfg=json.dumps({"type":"transcription","transcription_config":{
        "language":"en","operating_point":"enhanced","diarization":"speaker"}})
    body=("--%s\r\nContent-Disposition: form-data; name=\"config\"\r\n\r\n%s\r\n"%(boundary,cfg)).encode()
    body+=("--%s\r\nContent-Disposition: form-data; name=\"data_file\"; filename=\"%s\"\r\nContent-Type: audio/mpeg\r\n\r\n"%(boundary,os.path.basename(path))).encode()
    body+=open(path,"rb").read()+("\r\n--%s--\r\n"%boundary).encode()
    return json.loads(api("/jobs","POST",body,{"Content-Type":"multipart/form-data; boundary="+boundary}))["id"]
path=sys.argv[1]; off=float(sys.argv[2]); out=sys.argv[3]
jid=submit(path); print(os.path.basename(path),"job",jid,flush=True)
for _ in range(600):
    st=json.loads(api("/jobs/"+jid))["job"].get("status")
    if st=="done": break
    if st in ("rejected","deleted"): raise SystemExit("%s %s"%(jid,st))
    time.sleep(8)
tr=json.loads(api("/jobs/%s/transcript?format=json-v2"%jid))
ws=[]
for res in tr["results"]:
    if res["type"] not in ("word","punctuation"): continue
    a=res["alternatives"][0]
    ws.append([a["content"], round(res["start_time"]+off,2), round(res["end_time"]+off,2), a.get("speaker","?")])
json.dump(ws, open(out,"w"), ensure_ascii=False)
print("DONE", os.path.basename(path), len(ws), flush=True)
