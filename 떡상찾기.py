# -*- coding: utf-8 -*-
"""
떡상찾기.py — 유튜브에서 검색어로 영상을 모아 '진짜 떡상'(작은 채널인데 조회수가 큰 영상)을 순서대로 보여 줌.

사용법:
  python -X utf8 떡상찾기.py "역사 미스터리" "조선 미스터리" ... [--개수 30] [--최소조회 50000] [--최소분 4] [--자막 5]

  · 배율 = 조회수 ÷ 구독자 수 (클수록 채널 크기보다 크게 터진 영상)
  · 하루조회 = 조회수 ÷ 올린 뒤 지난 날 (최근에 뜨는 영상)
  · --자막 N : 배율 상위 N개의 한국어 자막(시간이 붙은 대본)을 받아 둠 → 떡상분석.py 가 영상 없이 대본 구조를 분석
  · 유튜브가 요청을 막지 않게 영상 하나마다 몇 초씩 쉼. 막히면(429·로봇 확인) 잠시 뒤 다시 실행하면 받은 것은 건너뜀

결과: output/떡상분석/_찾기/<날짜>_떡상목록.md (+ .json, 자막은 _자막/)
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
YTDLP = [sys.executable, "-m", "yt_dlp", "--js-runtimes", "node"]
KEYS = ["id", "title", "view_count", "channel", "channel_id", "channel_follower_count", "upload_date", "duration",
        "like_count", "comment_count", "description", "tags"]


def run(cmd, timeout=120):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def search(q, n):
    r = run(YTDLP + ["--flat-playlist", "-j", f"ytsearch{n}:{q}"], timeout=180)
    out = []
    for l in (r.stdout if r else "").splitlines():
        try:
            j = json.loads(l)
            out.append({"id": j["id"], "view_count": j.get("view_count") or 0, "duration": j.get("duration") or 0})
        except Exception:
            pass
    return out


def meta(vid, cache):
    p = os.path.join(cache, vid + ".json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    for k in range(3):
        r = run(YTDLP + ["--skip-download", "--ignore-no-formats-error", "-j", f"https://youtu.be/{vid}"])
        if r and r.stdout.strip():
            j = json.loads(r.stdout)
            d = {k_: j.get(k_) for k_ in KEYS}
            d["description"] = (d["description"] or "")[:800]
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
            return d
        time.sleep(5 * (k + 1))
    return None


def get_subs(vid, sub_dir):
    """한국어 자막(사람이 단 것 먼저, 없으면 자동) json3 → 경로 (없으면 '')"""
    p = os.path.join(sub_dir, vid + ".ko.json3")
    if os.path.exists(p):
        return p
    run(YTDLP + ["--skip-download", "--ignore-no-formats-error", "--write-subs", "--write-auto-subs", "--sub-langs", "ko",
                 "--sub-format", "json3", "-o", os.path.join(sub_dir, "%(id)s"), f"https://youtu.be/{vid}"])
    return p if os.path.exists(p) else ""


def main():
    ap = argparse.ArgumentParser(description="떡상 영상 찾기")
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--개수", dest="n", type=int, default=30, help="검색어마다 볼 영상 수")
    ap.add_argument("--최소조회", dest="minv", type=int, default=50000)
    ap.add_argument("--최소분", dest="minm", type=float, default=4, help="이보다 짧은 영상 뺌 (쇼츠를 찾으려면 0)")
    ap.add_argument("--자막", dest="subs", type=int, default=0, help="배율 상위 N개의 자막을 받음")
    ap.add_argument("--쉼", dest="pause", type=float, default=2.0, help="영상마다 쉬는 초")
    a = ap.parse_args()

    root = os.path.join(HERE, "output", "떡상분석", "_찾기")
    cache, sub_dir = os.path.join(root, "_정보"), os.path.join(root, "_자막")
    os.makedirs(cache, exist_ok=True)
    os.makedirs(sub_dir, exist_ok=True)

    found = {}
    for q in a.queries:
        res = search(q, a.n)
        print(f"검색 '{q}': {len(res)}개", flush=True)
        for r in res:
            if r["view_count"] >= a.minv and (r["duration"] >= a.minm * 60 or not r["duration"]):
                found.setdefault(r["id"], set()).add(q)
    print(f"조건에 맞는 영상 {len(found)}개 — 자세한 정보 받는 중 (영상마다 {a.pause}초 쉼)", flush=True)

    today = datetime.date.today()
    rows = []
    for i, vid in enumerate(found):
        cached = os.path.exists(os.path.join(cache, vid + ".json"))
        d = meta(vid, cache)
        if not cached:
            time.sleep(a.pause)
        if not d or not d.get("view_count"):
            continue
        if d.get("duration") and d["duration"] < a.minm * 60:
            continue
        sub = d.get("channel_follower_count") or 0
        age = (today - datetime.datetime.strptime(d["upload_date"], "%Y%m%d").date()).days if d.get("upload_date") else 0
        d.update(ratio=round(d["view_count"] / sub, 1) if sub else 0, age=age,
                 perday=int(d["view_count"] / max(1, age)) if age else 0, queries=sorted(found[vid]))
        rows.append(d)
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(found)}", flush=True)
    rows.sort(key=lambda r: -r["ratio"])

    if a.subs:
        print(f"배율 상위 {a.subs}개 자막 받는 중…", flush=True)
        for r in rows[:a.subs]:
            r["subs"] = get_subs(r["id"], sub_dir)
            print(f"  {'○' if r['subs'] else '×'} {r['title'][:40]}", flush=True)
            time.sleep(a.pause * 3)

    stamp = today.strftime("%Y%m%d")
    base = os.path.join(root, f"{stamp}_떡상목록")
    json.dump(rows, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    L = [f"# 떡상 영상 목록 ({today})", "", "검색어: " + ", ".join(a.queries), "",
         "배율 = 조회수 ÷ 구독자 (클수록 작은 채널에서 크게 터짐) · 하루조회 = 조회수 ÷ 지난 날", "",
         "| 배율 | 조회 | 구독자 | 며칠 전 | 하루조회 | 길이 | 채널 | 제목 | 주소 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['ratio']} | {r['view_count']:,} | {(r.get('channel_follower_count') or 0):,} | {r['age']} | "
                 f"{r['perday']:,} | {(r.get('duration') or 0) // 60}분 | {r['channel']} | {r['title'].replace('|', '/')} | "
                 f"https://youtu.be/{r['id']} |")
    open(base + ".md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"\n완료 → {base}.md")
    for r in rows[:15]:
        print(f"  {r['ratio']:>7} | {r['view_count']:>9,} | 구독 {(r.get('channel_follower_count') or 0):>9,} | {r['title'][:45]}")


if __name__ == "__main__":
    main()
