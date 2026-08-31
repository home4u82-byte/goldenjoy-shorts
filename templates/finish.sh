#!/bin/bash
set -e
P="<프로젝트 폴더 절대경로>"  # ★채우기
cd "$P"
PY=python3
OUT="${1:-가타카_돌아갈힘.mp4}"
LIM="${2:-0.841}"
$PY merge.py
TOT=$($PY -c "import json;print(json.load(open('work/meta.json'))['total'])")
WL=$($PY -c "print(int(round($TOT*48000)))")
echo "총길이 $TOT / $WL 샘플"
ffmpeg -y -v error -i work/blocks/merged.mkv -vn \
 -filter_complex "[0:a]acrossover=split=120 720 4800[b0][b1][b2][b3];\
[b0]acompressor=threshold=-20dB:ratio=3:attack=20:release=250:makeup=1[c0];\
[b1]acompressor=threshold=-18dB:ratio=2.5:attack=10:release=200:makeup=1[c1];\
[b2]acompressor=threshold=-18dB:ratio=2.5:attack=5:release=150:makeup=1[c2];\
[b3]acompressor=threshold=-20dB:ratio=2:attack=3:release=100:makeup=1[c3];\
[c0][c1][c2][c3]amix=inputs=4:normalize=0[m]" -map "[m]" -c:a pcm_s24le -ar 48000 -ac 2 work/mbc.wav
M=$(ffmpeg -hide_banner -i work/mbc.wav -af "loudnorm=I=-13.41:TP=-1.9:LRA=11:print_format=json" -f null - 2>&1 | \
    $PY -c "import sys,json;t=sys.stdin.read();d=json.loads(t[t.rindex('{'):t.rindex('}')+1]);print(f\"{d['input_i']}|{d['input_tp']}|{d['input_lra']}|{d['input_thresh']}|{d['target_offset']}\")")
IFS='|' read MI MTP MLRA MTH MOFF <<< "$M"
echo "측정 I=$MI TP=$MTP LRA=$MLRA TH=$MTH OFF=$MOFF"
ffmpeg -y -v error -i work/mbc.wav -af "loudnorm=I=-13.41:TP=-1.9:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$MOFF:linear=true,alimiter=limit=0.803526:level=disabled,apad=whole_len=$WL,atrim=0:$TOT" \
 -c:a pcm_s24le -ar 48000 -ac 2 work/master.wav
$PY make_sfx.py work/meta.json
IM=$($PY -c "import json;print(int(json.load(open('work/sfx_times.json'))['impact']*1000))")
WH=$($PY -c "import json;print(int(json.load(open('work/sfx_times.json'))['whoosh']*1000))")
SW=$($PY -c "import json;print(int(json.load(open('work/sfx_times.json'))['swell']*1000))")
ffmpeg -y -v error -i work/master.wav -i work/sfx_impact.wav -i work/sfx_whoosh.wav -i work/sfx_swell.wav \
 -filter_complex "[1:a]adelay=$IM|$IM[s1];[2:a]adelay=$WH|$WH[s2];[3:a]adelay=$SW|$SW[s3];\
[0:a][s1][s2][s3]amix=inputs=4:duration=first:normalize=0,alimiter=limit=$LIM:level=disabled,apad,atrim=0:$TOT[a]" \
 -map "[a]" -c:a pcm_s24le -ar 48000 -ac 2 work/master_sfx.wav
ffmpeg -y -v error -i work/blocks/merged.mkv -i chrome/top.png -i chrome/bottom.png -i work/master_sfx.wav \
 -filter_complex "[0:v]setpts=PTS-STARTPTS,fps=24000/1001[v];\
color=c=black:s=1080x1920:r=24000/1001:d=$TOT,format=yuv420p[bg];\
[bg][v]overlay=0:420:shortest=1[o1];\
[o1][1:v]overlay=0:0[o2];\
[o2][2:v]overlay=0:1500[o3];\
[o3]ass=work/captions.ass:fontsdir=fonts_final,format=yuv420p[out]" \
 -map "[out]" -map 3:a \
 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
 -r 24000/1001 -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart -video_track_timescale 24000 "$OUT"
echo "== 라우드니스 =="
ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -E "^    I:|^    Peak:|^    LRA:"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
