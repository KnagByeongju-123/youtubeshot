"""자연의 소리 실제 녹음 받기: nature_sounds/credits.json 에 적힌 원래 출처(CC0·퍼블릭 도메인·CC BY)에서 빠진 파일만 받음.
녹음이 없어도 프로그램은 합성 소리로 동작합니다."""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "nature_sounds")
UA = "ShortsNovelMaker/1.0 (https://github.com/KnagByeongju-123/youtubeshot) python-urllib"


def main():
    try:
        cr = json.load(open(os.path.join(D, "credits.json"), encoding="utf-8"))
    except OSError:
        print("nature_sounds\\credits.json 이 없습니다.")
        return 1
    todo = [(k, v) for k, v in cr.items() if not os.path.exists(os.path.join(D, v["file"]))]
    if not todo:
        print("✅ 녹음이 모두 있습니다.")
        return 0
    print(f"받을 녹음 {len(todo)}개")
    fails = 0
    for k, v in todo:
        path = os.path.join(D, v["file"])
        if "wikimedia" in v["source_url"]:
            time.sleep(15)             # 위키미디어는 빨리 연속으로 받으면 막힘
        for attempt in range(4):
            try:
                req = urllib.request.Request(v["source_url"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=180) as r, open(path + ".part", "wb") as f:
                    while True:
                        b = r.read(1 << 16)
                        if not b:
                            break
                        f.write(b)
                os.replace(path + ".part", path)
                print(f"  ✔ {k}  ({os.path.getsize(path) / 1e6:.1f}MB, {v.get('license')})")
                break
            except Exception as e:
                print(f"  다시 시도 {attempt + 1}: {k} - {str(e)[:60]}")
                time.sleep(30 * (attempt + 1))
        else:
            fails += 1
            print(f"  ✖ {k} 받기 실패 (나중에 다시 실행하세요)")
    print("완료" + (f" - 실패 {fails}개" if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
