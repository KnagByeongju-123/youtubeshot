r"""영상자료 — 장문 다큐에 넣을 '움직이는 영상 자료'(저작권 끝난 옛 영상)를 찾고, 미리 보고, 잘라서, 대본에 넣는 도구
(사용자 요청 2026-11-07: 참고 영상은 사진보다 동영상이 많음 → 사진 자리 상당수를 영상으로)

  python 영상자료.py 찾기 "<영어 검색어>" [--n 8]
      인터넷 아카이브에서 저작권 걱정 없는 곳만: 프렐링거 자료실, 옛 TV 광고 모음(classic_tv_commercials, 퍼블릭 도메인 표시),
      미국 국립기록원·정부 영상(퍼블릭 도메인 표시). → 번호 · 아이디 · 연도 · 길이 · 제목
  python 영상자료.py 받기 <아이디> [--간격 5]
      가장 가벼운 mp4 를 output/영상자료/원본/<아이디>.mp4 로 받고, 장면 모음표(시각 적힌 칸) <아이디>_장면.jpg 를 만듦 → Claude 가 열어 보고 쓸 구간을 고름
  python 영상자료.py 자르기 <아이디> <시작초> <길이초> <이름>
      → output/영상자료/<이름>.mp4 (소리 없음, 24fps, 폭 960, 10~16초 권장)
  python 영상자료.py 넣기 <프로젝트.json> "<문단 앞글자>" <이름> "<설명 (연도)>" [--대신]
      그 문단 앞 사진 묶음 맨 앞에 영상 줄을 넣음(빈 줄 포함). --대신 이면 그 문단 앞 사진 묶음을 영상으로 바꿈.
      출처는 아카이브 주소·'Internet Archive · Public Domain' 으로 자동

규칙 (장문다큐.md 4장): 1964년 전 TV 광고·미국 정부 영상·프렐링거만. 유명 배우·다른 업체 워터마크·1964년 뒤 광고는 쓰지 않음.
장면 모음표를 보고 글자 워터마크('ClassicTVAds' 등)가 있으면 버림. 소리는 쓰지 않음(나레이션이 덮음)
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output", "영상자료")
RAW = os.path.join(OUT, "원본")
UA = {"User-Agent": "youtubeshot-footage/1.0 (personal documentary tool)"}
TRUSTED = ("(collection:prelinger OR (collection:classic_tv_commercials AND licenseurl:*publicdomain*) "
           "OR ((collection:usnationalarchives OR collection:gov.archives.arc OR collection:fedflix OR collection:usgovernmentdocuments) "
           "AND licenseurl:*publicdomain*))")
FONT = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"


def get_json(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))


def find(q, n=8):
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        {"q": f"({q}) AND mediatype:movies AND {TRUSTED}", "fl[]": ["identifier", "title", "year", "collection"],
         "rows": n, "output": "json", "sort[]": "downloads desc"}, doseq=True)
    docs = get_json(url)["response"]["docs"]
    for i, d in enumerate(docs, 1):
        col = d.get("collection")
        col = ",".join(col) if isinstance(col, list) else str(col or "")
        print(f"{i:2}. {d['identifier'][:48]:48} | {str(d.get('year', ''))[:4]:4} | {col[:28]:28} | {str(d.get('title'))[:70]}")
    return docs


def pick_file(meta):
    vids = [f for f in meta.get("files", []) if str(f.get("name", "")).lower().endswith(".mp4")]
    if not vids:
        return None
    return min(vids, key=lambda f: int(f.get("size") or 1 << 40))


def fetch(ident, gap=5):
    os.makedirs(RAW, exist_ok=True)
    meta = get_json(f"https://archive.org/metadata/{urllib.parse.quote(ident)}")
    m = meta.get("metadata", {})
    f = pick_file(meta)
    if not f:
        print("mp4 없음")
        return 1
    dst = os.path.join(RAW, ident + ".mp4")
    if not os.path.exists(dst):
        size = int(f.get("size") or 0)
        print(f"받는 중: {f['name']} ({size / 1e6:.0f}MB)")
        subprocess.run(["curl", "-sSL", "-o", dst, f"https://archive.org/download/{urllib.parse.quote(ident)}/{urllib.parse.quote(f['name'])}"], check=True)
    json.dump({"identifier": ident, "title": m.get("title"), "date": m.get("date") or m.get("year"),
               "license": m.get("licenseurl", ""), "collection": m.get("collection")},
              open(dst + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst],
                               capture_output=True, text=True).stdout.strip() or 0)
    gap = max(gap, dur / 48)                     # 칸은 최대 48개
    cols = 8
    rows = max(1, min(6, int(dur / gap) // cols + 1))
    sheet = os.path.join(OUT, ident + "_장면.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dst, "-vf",
                    f"fps=1/{gap:.2f},scale=240:-2,drawtext=text='%{{pts\\:hms}}':fontcolor=yellow:fontsize=16:x=4:y=4:box=1:boxcolor=black@0.5,tile={cols}x{rows}",
                    "-frames:v", "1", sheet], check=False)
    print(f"제목: {m.get('title')} · {m.get('date') or m.get('year')} · {dur:.0f}초 · {m.get('licenseurl', '')}")
    print("장면 모음표:", sheet)
    return 0


def cut(ident, start, length, name):
    src = os.path.join(RAW, ident + ".mp4")
    dst = os.path.join(OUT, name + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", src, "-t", str(length), "-an",
                    "-vf", "fps=24,scale=960:-2", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", dst], check=True)
    info = json.load(open(src + ".json", encoding="utf-8")) if os.path.exists(src + ".json") else {"identifier": ident}
    json.dump(dict(info, start=start, length=length), open(dst + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("OK", dst)


def insert(proj, key, name, caption, replace=False):
    c = json.load(open(proj, encoding="utf-8"))
    clip = os.path.join(OUT, name + ".mp4")
    info = json.load(open(clip + ".json", encoding="utf-8")) if os.path.exists(clip + ".json") else {}
    ident = info.get("identifier", "")
    title = str(info.get("title") or "").replace("|", "/")
    rel = os.path.relpath(clip, HERE).replace("\\", "/")
    line = f"[사진: {rel} | {caption} | Internet Archive · Public Domain ({title[:50]}) | https://archive.org/details/{ident}]"
    L = c["story"].split("\n")
    idx = [k for k, l in enumerate(L) if l.strip().startswith(key)]
    if len(idx) != 1:
        print(f"'{key}' 로 시작하는 문단이 {len(idx)}개 — 더 길게 적어 주세요")
        return 1
    i = j = idx[0]
    while j > 0 and (L[j - 1].strip().startswith("[사진:") or not L[j - 1].strip()):
        j -= 1
    if replace:                                   # 그 문단 앞 사진 묶음을 영상 하나로
        del L[j:i]
        L[j:j] = ["", line, ""]
    else:
        L[j:j] = ["", line, ""]
    s = re.sub(r"\n{3,}", "\n\n", "\n".join(L))
    c["story"] = s
    json.dump(c, open(proj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("넣음:", line[:120])
    return 0


def main(a):
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    opt = lambda k, d: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
    if cmd == "찾기":
        find(a[1], int(opt("--n", 8)))
    elif cmd == "받기":
        return fetch(a[1], float(opt("--간격", 5)))
    elif cmd == "자르기":
        cut(a[1], float(a[2]), float(a[3]), a[4])
    elif cmd == "넣기":
        return insert(a[1], a[2], a[3], a[4], "--대신" in a)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
