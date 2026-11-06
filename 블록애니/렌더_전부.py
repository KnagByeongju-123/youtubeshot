"""블록 애니: 장면목록.json 의 모든 장면을 타이밍.json 길이대로 렌더링 (CPU 코어마다 하나씩 동시에, 끝난 장면은 건너뜀)
python3 블록애니/렌더_전부.py <작품폴더>  → <작품폴더>/장면영상/s00.mp4 ..."""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
W = os.path.abspath(sys.argv[1]); ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tm = json.load(open(os.path.join(W, "타이밍.json"), encoding="utf-8"))
out_dir = os.path.join(W, "장면영상"); os.makedirs(out_dir, exist_ok=True)
jobs = []
for i, sh in enumerate(tm["shots"]):
    dur = sh["t1"] - sh["t0"] + 0.5      # 이어 붙일 때 모자라지 않게 0.5초 여유
    out = os.path.join(out_dir, f"s{i:02d}.mp4")
    if not os.path.exists(out + ".done"):
        jobs.append((dur, i, out))
jobs.sort(reverse=True)
N = os.cpu_count() or 4
def run(j):
    dur, i, out = j
    t0 = time.time()
    env = dict(os.environ, LP_NUM_THREADS="1")
    r = subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1280x720x24", "blender", "-b", "-t", "1", "-P", os.path.join(ROOT, "블록애니", "장면.py"), "--",
                        os.path.join(W, "장면목록.json"), str(i), f"{dur:.3f}", out], cwd=ROOT, env=env, capture_output=True, text=True)
    ok = os.path.exists(out) and os.path.getsize(out) > 1000
    if ok:
        open(out + ".done", "w").write("ok")
    print(f"장면 {i:02d} {'완료' if ok else '실패'} {dur:.1f}초 → {time.time() - t0:.0f}초 걸림", flush=True)
    if not ok:
        print(r.stdout[-1500:], r.stderr[-1500:], flush=True)
with ThreadPoolExecutor(N) as ex:
    list(ex.map(run, jobs))
print("전부 끝", flush=True)
