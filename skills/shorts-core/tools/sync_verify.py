# 자막-음성 싱크 게이트 (G14) — 블록 오디오 샘플 정합 + 나레이션 실제 위치 교차상관 (2026-08-27 테트리스 사고로 신설)
# 사고: loudnorm 이 출력 PTS 를 뒤틀어 atrim 이 블록당 최대 92ms 를 깎았고, 뒤로 갈수록 -494ms 누적돼
#       "자막이랑 음성이랑 뒤로 갈수록 안 맞아"가 됐다. 해법: loudnorm 뒤 aresample=48000,asetpts=N/SR/TB.
#
# 사용: 프로젝트 폴더에서 (blocks 디렉토리·NARR 경로는 프로젝트에 맞게 인자로)
#   python3 tools/sync_verify.py work/v4_meta.json work/blocks24 work/tts3 work/master_sfx.wav
# 판정: ① 블록 mp4 디코드 샘플 수 = round(SEC*48000) (±48샘플)
#       ② 마스터에서 나레이션 교차상관 오프셋: 전 블록 |오프셋-중앙값| ≤ 20ms (균일 상수 오프셋은 허용)
import subprocess, sys, json
import numpy as np

META, BLK, NARR, MASTER = (sys.argv + ["work/v4_meta.json", "work/blocks24", "work/tts3", "work/master_sfx.wav"])[1:5]
meta = json.load(open(META))
fps = meta.get("fps", 30)
FR = {int(k): v for k, v in meta["frames"].items()}
order = meta["order"]

def load(f, mono=True):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, np.float32)

fail = []
# ① 블록 오디오 길이
for bi in order:
    n = len(load(f"{BLK}/b{bi:02d}.mp4"))
    want = round(FR[bi] / fps * 48000)
    if abs(n - want) > 48:
        fail.append(f"b{bi:02d} 오디오 {((n-want)/48):+.1f}ms — loudnorm 뒤 aresample=48000,asetpts=N/SR/TB 빠졌는지 확인")
print(f"① 블록 오디오 샘플 정합: {'전부 정확 ✓' if not fail else f'{len(fail)}개 불일치 ★'}")

# ② 나레이션 위치 교차상관
master = load(MASTER)
OFF = {}; t = 0.0
for bi in order: OFF[bi] = t; t += FR[bi] / fps
offs = []
import os
for bi in order:
    nf = f"{NARR}/n{bi:02d}.wav"
    if not os.path.exists(nf): continue
    n = load(nf)[:96000]
    if len(n) < 24000: continue
    o = int(OFF[bi] * 48000)
    lo = max(0, o - 24000)
    seg = master[lo:o + len(n) + 24000]
    c = np.correlate(seg, n, "valid")
    d = (np.argmax(c) - (o - lo)) / 48.0
    offs.append((bi, d))
med = float(np.median([d for _, d in offs]))
for bi, d in offs:
    mark = "" if abs(d - med) <= 20 else "★표류"
    if mark: fail.append(f"b{bi:02d} 오프셋 {d:+.1f}ms (중앙값 {med:+.1f})")
    print(f"  b{bi:02d} {d:+7.1f} ms {mark}")
print(f"② 나레이션 위치: 중앙값 {med:+.1f}ms, 표류 {'없음 ✓' if not any('표류' in f for f in fail) else '있음 ★'}")
if fail:
    print("\n★G14 실패:"); [print("  " + f) for f in fail]; sys.exit(1)
print("G14 자막-음성 싱크 OK ✓")
