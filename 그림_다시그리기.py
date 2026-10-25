"""검수에서 불합격한 컷을 이유에 맞게 주문서를 고쳐 다시 그리기 (작업_이어하기 줄에 넣어 서버가 바뀌어도 이어 그림)

  python 그림_다시그리기.py <회차.py> <그림폴더> <컷=이유[,이유..]> ...   불합격 컷 다시 그리기
  python 그림_다시그리기.py 합격 <그림폴더> <저장폴더> [c01,c02,..]      합격한 그림(png)을 jpg 로 저장 (컷을 안 쓰면 전부)

  예) python 그림_다시그리기.py 연재/두번째새벽/2화_쇠귀신.py <scratch>/ep2/out c01=복제,흰배경 c05=눈 "c17=장면:the girl riding piggyback on the robot's back"

- 이유(여러 개는 쉼표): 흰배경 복제 팔다리 머리 눈 글자 섞임 외눈 / 장면:<영어 설명 덧붙임> (장면: 은 맨 뒤에, 쉼표 써도 됨)
- 불합격 그림은 <그림폴더>/../불합격/<컷>_<n>.png 로 옮김 (다시 그리는 컷이 비어야 이어하기가 그 컷을 그림)
- 같은 컷을 다시 그릴 때마다 seed 를 바꿈 (기록: <그림폴더>/다시그리기_기록.json)
- 화풍은 애니 일러스트 (회차.py job ... 애니). 세피아면 --세피아"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, ".supertonic_venv", "bin", "python")

FIX = {    # 불합격 이유 → 주문서에 덧붙일 말 (검수 규칙 CLAUDE.md 와 같은 이름)
    "흰배경": "Detailed background environment that matches the scene with dark or natural colors, NOT a white, blank or plain background.",
    "복제": "Each character appears exactly once in the whole image, no duplicates, no look-alike copies in the background.",
    "팔다리": "Each person has exactly two arms, two hands, two legs and two feet, natural anatomy.",
    "머리": "The hair is exactly as in the reference sheet (same length, style and color).",
    "눈": "The eyes are exactly as in the reference sheet, both eyes the same color.",
    "글자": "Absolutely no letters, no writing, no numbers, no signs with text anywhere.",
    "섞임": "Clearly separate characters, do not merge their faces or bodies, each keeps their own face.",
    "외눈": "The robot has exactly ONE glowing blue eye; the other eye socket is broken and dark.",
}


def save_passed(out, dest, cuts):
    from PIL import Image
    os.makedirs(dest, exist_ok=True)
    names = sorted(f[:-4] for f in os.listdir(out) if f.endswith(".png") and f.startswith("c"))
    for c in (cuts or names):
        Image.open(os.path.join(out, c + ".png")).convert("RGB").save(os.path.join(dest, c + ".jpg"), quality=92)
    print("저장:", len(cuts or names), "장 →", dest)


def main():
    a = sys.argv[1:]
    if a[:1] == ["합격"] and len(a) >= 3:
        return save_passed(a[1], a[2], a[3].split(",") if len(a) > 3 else None)
    sepia = "--세피아" in a
    a = [x for x in a if x != "--세피아"]
    if len(a) < 3:
        sys.exit(__doc__)
    script, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    reasons = {}
    for arg in a[2:]:
        cut, _, why = arg.partition("=")
        extra = []
        why, _, scene = why.partition("장면:")             # '장면:' 뒤는 쉼표가 있어도 통째로 한 설명
        if scene.strip():
            extra.append(scene.strip().rstrip(".") + ".")
        for w in why.split(",") if why else []:
            w = w.strip()
            if w in FIX:
                extra.append(FIX[w])
            elif w:
                sys.exit(f"모르는 이유: {w} (쓸 수 있는 것: {' '.join(FIX)} 장면:...)")
        reasons[cut.strip()] = " ".join(extra)
    log_path = os.path.join(out, "다시그리기_기록.json")
    tries = json.load(open(log_path, encoding="utf-8")) if os.path.exists(log_path) else {}
    rej = os.path.join(os.path.dirname(out), "불합격")
    os.makedirs(rej, exist_ok=True)
    for c in reasons:
        tries[c] = tries.get(c, 0) + 1
        src = os.path.join(out, c + ".png")
        if os.path.exists(src):
            os.replace(src, os.path.join(rej, f"{c}_{tries[c]}.png"))
    json.dump(tries, open(log_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 회차.py 로 그 컷들의 주문서를 새로 만든 뒤 이유에 맞는 말을 덧붙이고 seed 를 바꿈
    n = max(tries[c] for c in reasons)
    job_dir = os.path.join(os.path.dirname(out), f"다시그리기_{n}_{'_'.join(sorted(reasons))[:40]}")
    cmd = [PY, script, "job", job_dir] + ([] if sepia else ["애니"]) + [",".join(reasons)]
    subprocess.run(cmd, check=True, cwd=HERE)
    jp = os.path.join(job_dir, "job.json")
    job = json.load(open(jp, encoding="utf-8"))
    for it in job["items"]:
        c = it["id"]
        it["seed"] = int(it.get("seed") or 1) + 1000 * tries[c]
        if reasons.get(c):
            it["prompt"] = it["prompt"].replace("Cinematic composition", reasons[c] + " Cinematic composition", 1)
    job["skip_done"] = True
    json.dump(job, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    name = f"다시그리기_{os.path.splitext(os.path.basename(script))[0]}_{n}_{len(reasons)}장"
    subprocess.run([PY, os.path.join(HERE, "작업_이어하기.py"), "klein", name, jp, out], check=True)
    subprocess.Popen([PY, os.path.join(HERE, "작업_이어하기.py"), "run"], cwd=HERE,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for c, r in reasons.items():
        print(f"  {c} ({tries[c]}번째): {r or '이유 없음(seed 만 바꿈)'}")
    print("줄에 넣고 이어하기를 켬:", name)


if __name__ == "__main__":
    main()
