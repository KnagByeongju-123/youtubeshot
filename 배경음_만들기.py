"""배경음악 후보 만들기 — ACE-Step 1.5 (공개 음악 AI, MIT) 로 가사 없는 곡을 만들어 반복용으로 다듬음
.acestep_venv/bin/python 배경음_만들기.py <저장폴더> <길이초> "이름=영어 주문[|빠르기]" ...
  예) .acestep_venv/bin/python 배경음_만들기.py 연재/엄마의텃밭/_배경음 150 "1_피아노=soft reflective piano with warm strings, calm|72"
  - 주문은 영어로, 악기는 2~3개만. 장문 다큐용은 'steady dynamics, no climax, no drums, loopable underscore' 를 붙이면 반복해도 덜 거슬림
  - 결과: <이름>_원곡.mp3 · <이름>_반복용.mp3(앞 HEAD초·뒤 TAIL초를 잘라 낸 것 → 프로젝트 settings 의 bgm_path 로)
          · <이름>_이음매듣기.mp3(반복용 곡의 끝 15초 → 처음 15초로 넘어가는 곳, 프로그램과 같은 4초 겹침) + 전체듣기.mp3
  - 그래픽카드 없는 서버: bfloat16 + VAE 조각 128 이라야 메모리 15GB 에 맞음. AMX 서버에서 30초 곡 약 65초, 10초 곡 약 22초
  - 준비: .acestep/ (github ace-step/ACE-Step-1.5), .acestep_venv (CPU torch), models/ACE-Step1.5 (CLAUDE.md 참고)"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HEAD, TAIL, XF = 6.0, 8.0, 4.0     # 잘라 낼 앞(시작 부분)·뒤(마무리 부분) 초, 이음매 겹침 초 (프로그램 loop_xfade 와 같음)
os.environ.setdefault("ACESTEP_CHECKPOINTS_DIR", os.path.join(HERE, "models", "ACE-Step1.5"))
os.environ["ACESTEP_INIT_LLM"] = "false"                       # 큰 언어모델 없이 (주문을 그대로 씀, 빠름)
os.environ.setdefault("ACESTEP_VAE_DECODE_CHUNK_SIZE", "128")  # 소리 파일로 바꿀 때 메모리 초과 방지
sys.path.insert(0, os.path.join(HERE, ".acestep"))


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout)


def main():
    out_dir, sec, jobs = sys.argv[1], float(sys.argv[2]), []
    for a in sys.argv[3:]:
        name, _, spec = a.partition("=")
        cap, _, bpm = spec.partition("|")
        jobs.append((name, cap.strip(), int(bpm) if bpm.strip() else None))
    os.makedirs(out_dir, exist_ok=True)
    import torch
    torch.set_num_threads(os.cpu_count())
    import acestep.model_downloader as md       # 안 쓰는 큰 언어모델(3.5GB)을 '없음'으로 보고 자동으로 받지 않게
    md.MAIN_MODEL_COMPONENTS[:] = [c for c in md.MAIN_MODEL_COMPONENTS if "-lm-" not in c]
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(project_root=os.path.join(HERE, ".acestep"), config_path="acestep-v15-turbo", device="cpu")
    if not ok:
        sys.exit("모델을 불러오지 못했습니다: " + str(msg))
    dit.model.to(torch.bfloat16)                                  # 메모리 절반 + AMX 계산
    if getattr(dit, "text_encoder", None) is not None:
        dit.text_encoder.to(torch.bfloat16)
    dit.dtype = torch.bfloat16
    llm, tmp, listen = LLMHandler(), os.path.join(out_dir, "_tmp"), []
    sil = os.path.join(out_dir, "_쉼.wav")
    ff("-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=48000:cl=stereo", sil)
    for name, cap, bpm in jobs:
        t = time.time()
        p = GenerationParams(caption=cap + ", instrumental", lyrics="[Instrumental]", instrumental=True, duration=sec,
                             bpm=bpm, shift=3.0, thinking=False, inference_steps=8)
        r = generate_music(dit, llm, p, GenerationConfig(batch_size=1, audio_format="mp3"), save_dir=tmp)
        if not r.success:
            print("실패", name, r.error, flush=True)
            continue
        raw, loop, seam = (os.path.join(out_dir, f"{name}_{k}.mp3") for k in ("원곡", "반복용", "이음매듣기"))
        shutil.move(r.audios[0]["path"], raw)
        ff("-i", raw, "-ss", str(HEAD), "-to", str(dur(raw) - TAIL), "-b:a", "192k", loop)
        L = dur(loop)
        ff("-sseof", str(-(15 + XF)), "-i", loop, "-t", str(15 + XF), "-i", loop,
           "-filter_complex", f"[0][1]acrossfade=d={XF}:c1=qsin:c2=qsin", "-b:a", "192k", seam)
        listen += [seam, sil]
        print(f"완료 {name} · 반복용 {L:.0f}초 · {time.time() - t:.0f}초 걸림", flush=True)
    if listen:
        ins = sum((["-i", x] for x in listen), [])
        ff(*ins, "-filter_complex", f"concat=n={len(listen)}:v=0:a=1", "-b:a", "160k", os.path.join(out_dir, "이음매_전체듣기.mp3"))
    shutil.rmtree(tmp, ignore_errors=True)
    os.remove(sil)


if __name__ == "__main__":
    main()
