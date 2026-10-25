"""오래 걸리는 일(그림·영상)을 줄 세워 두고, 서버가 바뀌어 프로그램이 꺼져도 남은 일부터 저절로 다시 돌림
(클라우드 세션은 쉬는 동안 서버가 다른 컴퓨터로 옮겨지면 파일은 남지만 돌던 프로그램은 꺼짐)

  python 작업_이어하기.py klein <이름> <작업.json> <저장폴더>      그림 주문서 (다 그린 컷은 건너뜀)
  python 작업_이어하기.py add <이름> -- <명령...>                 아무 명령 (끝까지 성공하면 끝난 일로)
  python 작업_이어하기.py run                                     줄 선 일 중 안 끝난 것을 차례로 (뒤에서 계속 돎. 이미 돌고 있으면 그냥 나감)
  python 작업_이어하기.py list                                    줄 선 일과 상태
  python 작업_이어하기.py done <이름>                              끝난 일로 표시 (손으로 직접 끝냈을 때)
  python 작업_이어하기.py clear                                   끝난 일 지우기 (clear all = 전부)

- 세션이 시작될 때 .claude/hooks/session-start.sh 가 'run' 을 뒤에서 켬 → 서버가 바뀌어도 남은 일을 이어서 함
- add 로 넣은 명령은 다시 돌려도 되는 것이어야 함 (render_project.py 는 다 된 나레이션·구간을 건너뛰므로 됨)
- 줄: .이어하기.json, 기록: .이어하기_기록/<이름>.log (둘 다 깃에 안 올림)"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, ".이어하기.json")
LOGS = os.path.join(HERE, ".이어하기_기록")
PIDF = os.path.join(HERE, ".이어하기.pid")
KLEIN = [os.path.join(HERE, ".sd_venv", "bin", "python"), os.path.join(HERE, "klein_worker.py"), os.path.join(HERE, "models", "FLUX2_klein_4B")]


def load():
    try:
        return json.load(open(QUEUE, encoding="utf-8"))
    except (OSError, ValueError):
        return []


def save(q):
    tmp = QUEUE + ".tmp"
    json.dump(q, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, QUEUE)


def boot_id():
    try:
        return open("/proc/sys/kernel/random/boot_id").read().strip()
    except OSError:
        return ""


def runner_alive():
    """이 컴퓨터에서 run 이 이미 돌고 있나 (서버가 바뀌면 boot_id 가 달라 예전 기록은 무시)"""
    try:
        pid, bid = open(PIDF).read().split()
        return bid == boot_id() and os.path.exists(f"/proc/{int(pid)}")
    except (OSError, ValueError):
        return False


def klein_done(job, out):
    try:
        items = json.load(open(job, encoding="utf-8")).get("items") or []
    except (OSError, ValueError):
        return False
    return all(os.path.exists(os.path.join(out, f"{it.get('id')}.png")) for it in items)


def is_done(t):
    if t.get("done"):
        return True
    return t.get("kind") == "klein" and klein_done(t["job"], t["out"])


def add(task):
    q = [t for t in load() if t["name"] != task["name"]]
    if task.get("kind") == "klein":       # 같은 저장 폴더를 그리던 예전 그림 줄은 끝냄 — 그림을 치우면 예전 주문서로 다시 그려 버림(c34 사고)
        for t in q:
            if t.get("kind") == "klein" and os.path.abspath(t.get("out", "")) == task["out"] and not t.get("done"):
                t["done"] = True
                print("  예전 줄 끝냄:", t["name"])
    q.append(task)
    save(q)
    print("줄에 넣음:", task["name"])


def run():
    if runner_alive():
        print("이미 돌고 있음")
        return
    open(PIDF, "w").write(f"{os.getpid()} {boot_id()}")
    os.makedirs(LOGS, exist_ok=True)
    while True:
        todo = [t for t in load() if not is_done(t)]
        if not todo:
            break
        t = todo[0]
        if t.get("kind") == "klein":
            job = json.load(open(t["job"], encoding="utf-8"))
            if not job.get("skip_done"):
                job["skip_done"] = True
                json.dump(job, open(t["job"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            cmd = KLEIN + [t["job"], t["out"]]
        else:
            cmd = t["cmd"]
        with open(os.path.join(LOGS, t["name"] + ".log"), "a", encoding="utf-8") as log:
            log.write(f"\n=== {time.strftime('%m-%d %H:%M:%S')} 시작 (boot {boot_id()[:8]}) ===\n")
            log.flush()
            rc = subprocess.call(cmd, cwd=t.get("cwd") or HERE, stdout=log, stderr=subprocess.STDOUT)
            log.write(f"=== {time.strftime('%m-%d %H:%M:%S')} 끝 (rc {rc}) ===\n")
        q = load()
        for x in q:
            if x["name"] == t["name"]:
                x["runs"] = x.get("runs", 0) + 1
                if t.get("kind") != "klein" and rc == 0:
                    x["done"] = True
                if x["runs"] >= 3 and not is_done(x):      # 세 번 돌아도 안 끝나면 멈춰서 사람이 보게
                    x["done"], x["failed"] = True, True
        save(q)
    os.remove(PIDF)


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "list"
    if cmd == "klein" and len(a) >= 4:
        add({"name": a[1], "kind": "klein", "job": os.path.abspath(a[2]), "out": os.path.abspath(a[3])})
    elif cmd == "add" and "--" in a and len(a) > a.index("--") + 1:
        add({"name": a[1], "kind": "cmd", "cmd": a[a.index("--") + 1:], "cwd": os.getcwd()})
    elif cmd == "done" and len(a) >= 2:
        q = load()
        for t in q:
            if t["name"] == a[1]:
                t["done"] = True
        save(q)
    elif cmd == "run":
        run()
    elif cmd == "clear":
        save([] if a[1:2] == ["all"] else [t for t in load() if not is_done(t)])
    else:
        print("돌고 있음" if runner_alive() else "쉬는 중")
        for t in load():
            state = "실패(3번)" if t.get("failed") else "끝" if is_done(t) else "남음"
            print(f"  [{state}] {t['name']}  (돌린 횟수 {t.get('runs', 0)})")


if __name__ == "__main__":
    main()
