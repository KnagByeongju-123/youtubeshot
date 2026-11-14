"""찬송가 연주곡 영상 만들기 — 곡마다 그림 한 장, 아주 천천히 확대(잠들기 좋게), 곡 사이 부드럽게 어두워졌다 밝아짐
곡 시작 10초 동안 왼쪽 아래에 곡 제목을 작게 (흰 글자 + 은은한 그림자)

사용법: xvfb 필요 없음
  python -X utf8 찬송가_연주영상.py <연주곡.mp3> <곡순서.txt> <그림 폴더> <결과.mp4> [--반복 N]
  곡순서.txt 한 줄 = 'H:MM:SS 제목' (가야금_찬송가_수면.py 가 만든 것). 그림은 이름순으로 곡에 차례로 (곡이 더 많으면 처음부터 다시)
  --이야기 <파일> : 한 줄 = '제목|이야기' → 그 곡이 처음 나올 때 제목 아래에 작게 (곡에 얽힌 역사 한 줄)
  --반복 N : 완성 영상을 N번 이어 붙인 긴 판도 만듦 (다시 인코딩 없이 이어 붙여 빠름, 예: 3시간 수면용)
"""
import glob
import os
import re
import subprocess
import sys

FPS = 24
FONT = "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf"


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout
    return float(out.strip())


def dt(text, size, y, alpha, color="white@0.85"):
    safe = text.replace("\\", "").replace(":", "\\:").replace("'", "’").replace(",", "\\,")
    return (f"drawtext=fontfile={FONT}:text='{safe}':fontsize={size}:fontcolor={color}:shadowcolor=black@0.7:shadowx=2:shadowy=2:box=1:boxcolor=black@0.45:boxborderw=14:"
            f"x=70:y=h-{y}:alpha='{alpha}'")


def segment(img, sec, title, out, k, story=""):
    n = int(round(sec * FPS))
    zin = k % 2 == 0   # 번갈아 확대·축소 (같은 움직임이 반복되지 않게)
    z = f"1+0.08*on/{n}" if zin else f"1.08-0.08*on/{n}"
    fade = min(2.5, sec / 4)
    vf = (f"scale=2880:1620:flags=lanczos,"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps={FPS},"
          + dt(title, 38, 150 if story else 110, "if(lt(t,1.5),t/1.5,if(lt(t,9),1,if(lt(t,11),(11-t)/2,0)))") + ","
          + (dt(story, 28, 95, "if(lt(t,2.5),0,if(lt(t,4),(t-2.5)/1.5,if(lt(t,13),1,if(lt(t,15),(15-t)/2,0))))", "white@0.75") + "," if story else "")
          + f"fade=t=in:st=0:d={fade},fade=t=out:st={sec - fade:.3f}:d={fade},format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", img, "-vf", vf,
                    "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "23", out], check=True)


def main(a):
    mp3, chap, img_dir, out = a[:4]
    rep = int(a[a.index("--반복") + 1]) if "--반복" in a else 0
    total = probe(mp3)
    rows = []
    for line in open(chap, encoding="utf-8"):
        m = re.match(r"(\d+):(\d+):(\d+)\s+(.*)", line.strip())
        if m:
            rows.append((int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]), re.sub(r"\s*\(2부\)$", "", m[4])))
    stories = {}
    if "--이야기" in a:
        for line in open(a[a.index("--이야기") + 1], encoding="utf-8"):
            if "|" in line:
                kk, vv = line.strip().split("|", 1)
                stories[kk.strip()] = vv.strip()
    seen = set()
    imgs = sorted(glob.glob(os.path.join(img_dir, "*.png")))
    tmp = out + "_조각"
    os.makedirs(tmp, exist_ok=True)
    parts = []
    for k, (st, title) in enumerate(rows):
        end = rows[k + 1][0] if k + 1 < len(rows) else total
        p = os.path.join(tmp, f"{k:02d}.mp4")
        key = re.sub(r"\s*\(.*$", "", title)
        story = stories.get(key, "") if key not in seen else ""
        seen.add(key)
        segment(imgs[k % len(imgs)], end - st, title, p, k, story)
        parts.append(p)
        print(f"{k + 1}/{len(rows)} {title} {end - st:.0f}초", flush=True)
    lst = os.path.join(tmp, "목록.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", mp3,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print("완성:", out, f"{probe(out) / 60:.1f}분")
    if rep > 1:
        long = out[:-4] + f"_{rep}회반복.mp4"
        with open(lst, "w", encoding="utf-8") as f:
            f.writelines(f"file '{os.path.abspath(out)}'\n" for _ in range(rep))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", long], check=True)
        print("긴 판:", long, f"{probe(long) / 60:.1f}분")
    for p in parts + [lst]:
        os.remove(p)
    os.rmdir(tmp)


if __name__ == "__main__":
    main(sys.argv[1:])
