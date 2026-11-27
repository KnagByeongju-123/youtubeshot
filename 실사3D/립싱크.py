"""립싱크만 따로: 나레이션 소리 + 대본 + 인물 GLB → 입이 말에 맞춰 움직이는 영상 (사용자 2026-11-27 '립씽크만 별도로 파이썬으로')
   순서 (이미 있는 도구를 차례로 부름):
     ① 음절 시각  : 실사3D/발음시각.py (받아쓰기 wav2vec2)  또는 --소리마디 → 실사3D/소리마디_시각.py (짧은 모음 연습 등 받아쓰기가 못 맞출 때)
     ② 입 모양 값 : 애니3D/입모양_프레임.py --표 실사3D/입모양표.json (배운 표, 자음·받침 닫기·ㅗㅜ 오므림 칸 포함)
     ③ 촬영       : 실사3D/야외_오르빗.py (Cycles, 그래픽카드 없이) — 모델에 AA_VI_11_E 키가 있으면 15가지 입 모양(--입방식 15), 없으면 3가지
                    여러 개로 나눠 동시에 찍음(--나누기, 메모리 15GB 서버는 2 까지)
     ④ 합치기     : ffmpeg 로 소리를 --시작 초만큼 늦춰 붙임
   사용: .supertonic_venv/bin/python 실사3D/립싱크.py <인물.glb> <나레이션.mp3|wav> <대본.txt 또는 "글"> <출력.mp4>
         [--크기 640x360] [--카메라 "0,-0.75,1.47,0,0,1.45,50"] [--입세기 0.5] [--입속 100,16,28] [--내밀기 0.85,0.8,0.6]
         [--시작 0.5] [--나누기 2] [--샘플 6] [--장소 kloofendal_48d_partly_cloudy_puresky] [--소리마디] [--시각 <음절시각.json>] [--입방식 15|3|auto]
         [--애니저장 <출력.glb>]   (영상 대신, 입·눈 움직임을 기록한 움직이는 GLB 로 저장)
   예: .supertonic_venv/bin/python 실사3D/립싱크.py models/glb/여자아나운서3.glb voice.mp3 "안녕하세요. 3D 아나운서입니다." output/립싱크.mp4
   작은 시험 영상은 640x360 (사용자 결정), 완성본만 1920x1080"""
import json, math, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PY_SD = os.path.join(ROOT, ".sd_venv/bin/python"); PY_ST = os.path.join(ROOT, ".supertonic_venv/bin/python"); PY_BPY = os.path.join(ROOT, ".bpy_venv/bin/python")
a = sys.argv[1:]
if len(a) < 4: print(__doc__); sys.exit(1)
glb, audio, text, out = (os.path.abspath(a[0]), os.path.abspath(a[1]), a[2], os.path.abspath(a[3]))
def opt(k, d): return a[a.index(k) + 1] if k in a else d
SIZE = opt("--크기", "640x360"); CAM = opt("--카메라", "0,-0.75,1.47,0,0,1.45,50"); MS = opt("--입세기", "0.5"); MOUTH = opt("--입속", "100,16,28")
START = float(opt("--시작", "0.5")); NSPLIT = int(opt("--나누기", "2")); SAMPLES = opt("--샘플", "6"); PLACE = opt("--장소", "kloofendal_48d_partly_cloudy_puresky")
MODE = opt("--입방식", "auto"); ANIM = opt("--애니저장", None)
if os.path.isfile(text): text = open(text, encoding="utf-8").read()
work = tempfile.mkdtemp(prefix="립싱크_", dir=os.path.dirname(out) or ".")
def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd)[:200]); r = subprocess.run(cmd, cwd=ROOT, **kw)
    if r.returncode: sys.exit(f"실패: {cmd[1] if len(cmd) > 1 else cmd[0]}")

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio], capture_output=True, text=True).stdout.strip())
print(f"소리 {dur:.1f}초")
# ① 음절 시각
tim = os.path.join(work, "시각.json")
if "--시각" in a: shutil.copy(os.path.abspath(opt("--시각", "")), tim)          # 이미 재 둔 음절 시각을 씀 (받아쓰기 모델 1.3GB 를 못 받을 때 — 디스크 부족 2026-11-27)
elif "--소리마디" in a: run([PY_ST, os.path.join(HERE, "소리마디_시각.py"), audio, "".join(c for c in text if "가" <= c <= "힣"), tim])
else: run([PY_SD, "-X", "utf8", os.path.join(HERE, "발음시각.py"), audio, text, tim])
# ② 입 모양 값
lip = os.path.join(work, "입.json")
run([PY_ST, os.path.join(ROOT, "애니3D/입모양_프레임.py"), tim, lip, "--소리", audio, "--표", os.path.join(HERE, "입모양표.json"), "--시작", str(START)])
# ③ 촬영
if MODE == "auto": MODE = "15" if b"AA_VI_11_E" in open(glb, "rb").read() else "3"
N = int(math.ceil((dur + START + 0.6) * 24))
base = [PY_BPY, "-I", os.path.join(HERE, "야외_오르빗.py"), glb, os.path.join(work, "fr"), "--장소", PLACE, "--세상빛", "0.5", "--조명", "0.45",
        "--자세", "모음", "--입", lip, "--입세기", MS, "--장수", str(N), "--샘플", SAMPLES, "--크기", SIZE, "--고정카메라", " " + CAM]
if MODE == "15": base += ["--입방식", "15", "--입속", MOUTH] + (["--내밀기", opt("--내밀기", "")] if "--내밀기" in a else [])
if ANIM:
    run(["xvfb-run", "-a"] + base + ["--애니저장", os.path.abspath(ANIM)]); print("→", ANIM); shutil.rmtree(work, ignore_errors=True); sys.exit(0)
print(f"촬영 {N}장 ({MODE}가지 입 모양), {NSPLIT}개로 나눠 동시에")
step = int(math.ceil(N / NSPLIT)); procs = []
for k in range(NSPLIT):
    s0, s1 = k * step, min(N, (k + 1) * step)
    if s0 >= s1: continue
    logf = open(os.path.join(work, f"촬영_{k}.log"), "w")
    procs.append(subprocess.Popen(["xvfb-run", "-a"] + base + ["--시작장", str(s0), "--끝장", str(s1)], cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT))
bad = [p for p in procs if p.wait() != 0]
if bad: sys.exit(f"촬영 실패 — 기록: {work}/촬영_*.log")
# ④ 합치기
ms = int(START * 1000)
run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(work, "fr", "f%04d.png"), "-i", audio,
     "-filter_complex", f"[1:a]adelay={ms}|{ms},apad[a]", "-map", "0:v", "-map", "[a]", "-t", f"{N / 24:.2f}",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26" if SIZE == "640x360" else "18", "-c:a", "aac", "-b:a", "96k" if SIZE == "640x360" else "192k", "-movflags", "+faststart", out])
shutil.rmtree(work, ignore_errors=True)
print("→", out)
