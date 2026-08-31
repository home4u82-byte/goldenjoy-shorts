# 구간별 프레임 시트 — 컷 재선정용 (활성화면 1920x800 크롭 기준)
import subprocess, sys, os
from PIL import Image, ImageDraw

SRC = "segment_4759_5076.mp4"
os.makedirs("work/sheets", exist_ok=True)

def sheet(name, times, cols=5, w=384, h=160):
    tiles = []
    for t in times:
        out = f"work/sheets/_tmp_{t}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", SRC,
                        "-vf", f"crop=1920:800:0:140,scale={w}:{h}",
                        "-frames:v", "1", out], check=True)
        tiles.append((t, out))
    rows = (len(tiles) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * w, rows * h), "black")
    for i, (t, p) in enumerate(tiles):
        im = Image.open(p)
        x, y = (i % cols) * w, (i // cols) * h
        canvas.paste(im, (x, y))
        d = ImageDraw.Draw(canvas)
        d.rectangle([x, y, x + 62, y + 20], fill="black")
        d.text((x + 4, y + 4), f"{t}", fill="yellow")
        os.remove(p)
    canvas.save(f"work/sheets/{name}.png")
    print(name, len(tiles))

region = sys.argv[1]
if region == "A":      # 도입 0~33
    sheet("A", [round(0.5 + i * 1.6, 1) for i in range(20)])
elif region == "B":    # 혈투 33~140
    sheet("B", [round(33.6 + i * 5.3, 1) for i in range(20)])
elif region == "B2":   # 혈투 정밀
    sheet("B2", [float(t) for t in sys.argv[2:]])
elif region == "C":    # 정리~포커 140~230
    sheet("C", [round(140 + i * 4.6, 1) for i in range(20)])
elif region == "D":    # 방~샤워 226~316
    sheet("D", [round(226.5 + i * 4.6, 1) for i in range(20)])
elif region == "X":    # 임의 시각 목록
    sheet(sys.argv[2], [float(t) for t in sys.argv[3:]])
