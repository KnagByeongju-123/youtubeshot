"""유튜브 썸네일: ChatGPT 그림 + 프로그램 글자. Codex가 배경을 그리고 Claude가 큰 문구를 얹음.

  py -3.11 -X utf8 thumb_tool.py prompt <프로젝트.json>
      → 썸네일 문구 3안을 정하고, 배경 그림 ChatGPT 프롬프트(글자 없이)를 만들어
        _ai공유/claude가codex에게.md 와 <프로젝트폴더>/썸네일_요청.txt 에 적음. 문구는 썸네일_문구.json 에 저장.
  py -3.11 -X utf8 thumb_tool.py apply <프로젝트.json> <배경그림.png> [문구번호]
      → 배경 그림에 문구(기본 1안)를 얹어 <영상제목>_썸네일_유튜브.jpg 로 저장
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
spec = importlib.util.spec_from_file_location("m", os.path.join(HERE, "shorts_novel_maker_supertonic.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

THUMB_BG_SYSTEM = """너는 구독자 100만 유튜브 채널의 썸네일 아트 디렉터다. 아래 영상의 썸네일 배경 그림 프롬프트를 만든다.
- 글자는 넣지 않는다(문구는 프로그램이 따로 얹는다). no text, no letters, no words, no numbers, no watermark 를 반드시 포함.
- 인기 썸네일 구도: 피사체 하나(감정이 보이는 인물 얼굴 클로즈업, 또는 강한 상징물)가 화면을 크게 채우고, 배경은 단순하고 대비가 강하게.
  문구가 들어갈 한쪽(왼쪽이나 위)을 비교적 비워 둔다. 표정·분위기가 영상 주제와 감정을 한눈에 전하게.
- 영상의 그림 화풍과 같은 화풍으로. 가로 16:9.
- big/big2: 썸네일에 얹을 아주 짧고 강한 한국어 문구(궁금증·반전·금기어, 결과는 숨김). ko: 장면 한 줄 설명.
반드시 JSON만 출력: {"variants": [{"big": "", "big2": "", "ko": "", "prompt": "영어 배경 프롬프트"}]}  (3안)"""


def load_proj(p):
    d = json.load(open(p, encoding="utf-8"))
    return d, d.get("title") or "제목", d.get("story") or "", d.get("settings") or {}


def cmd_prompt(p):
    d, title, story, s = load_proj(p)
    style = s.get("image_style_preset", "")
    sk = m.style_vec_ko(style) if hasattr(m, "style_vec_ko") else style
    model = (m.SCRIPT_ENGINE.get("s") or {}).get("script_engine", "Claude")
    body = m.story_text_only(story)[:2500]
    d2 = m.ask_script_json("opus", THUMB_BG_SYSTEM, f"[제목] {title}\n[영상 화풍] {sk}\n\n[본문]\n{body}")
    vs = [v for v in (d2.get("variants") or []) if isinstance(v, dict) and v.get("big") and v.get("prompt")][:3]
    if not vs:
        print("썸네일 문구를 만들지 못했습니다")
        return 1
    pd = os.path.dirname(p)
    json.dump({"title": title, "variants": vs, "style": style}, open(os.path.join(pd, "썸네일_문구.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tail = "" if not sk else f" 화풍: {sk}"
    lines = [f"[유튜브 썸네일 배경 그림 - '{title}']", "글자 없이 배경만 그려 주세요(문구는 프로그램이 얹습니다). 가로 16:9. 1안을 먼저, 마음에 들면 1장만 그려도 됩니다.", ""]
    for i, v in enumerate(vs):
        lines += [f"{i + 1}안 (얹을 문구: {v.get('big', '')} {v.get('big2', '')})", "이미지를 그려 줘: " + v["prompt"] + " no text, no letters, no numbers, no watermark." + tail, ""]
    txt = "\n".join(lines)
    with open(os.path.join(pd, "썸네일_요청.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    try:
        msg = "# Claude → Codex 쪽지함\n\n## 썸네일 배경 그림 요청\n저장 위치: short_\\_ai공유\\받은그림\\썸네일\\  (1.png 등)\n\n" + txt
        with open(os.path.join(HERE, "_ai공유", "claude가codex에게.md"), "w", encoding="utf-8") as f:
            f.write(msg)
        os.makedirs(os.path.join(HERE, "_ai공유", "받은그림", "썸네일"), exist_ok=True)
    except Exception:
        pass
    print("문구 3안·배경 프롬프트 작성 →", os.path.join(pd, "썸네일_요청.txt"))
    print("PROMPTS " + os.path.join(pd, "썸네일_문구.json"))
    return 0


def cmd_apply(p, bg_path, idx=1):
    d, title, story, s = load_proj(p)
    pd = os.path.dirname(p)
    fj = os.path.join(pd, "썸네일_문구.json")
    vs = json.load(open(fj, encoding="utf-8"))["variants"] if os.path.exists(fj) else [{"big": title[:12], "big2": "", "mood": ""}]
    v = vs[max(0, min(len(vs) - 1, int(idx) - 1))]
    from PIL import Image
    bg = Image.open(bg_path).convert("RGB")
    im = m.render_thumb(v, s, bg, size=(1280, 720), style=s.get("thumb_style") or "기본(사진 꽉 + 큰 글자)")
    base = os.path.join(s.get("out_dir") or os.path.join(HERE, "output"), "장문", m.safe_name(title))
    out = base + "_썸네일_유튜브.jpg"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    m._save_jpg_2mb(im.convert("RGB"), out)
    im.convert("RGB").save(base + "_썸네일_AI.png")      # publish_kit 이 덮어쓰지 않게 표시
    print("DONE 썸네일:", out)
    return 0


def main(a):
    if len(a) >= 2 and a[0] == "prompt":
        return cmd_prompt(os.path.abspath(a[1]))
    if len(a) >= 3 and a[0] == "apply":
        return cmd_apply(os.path.abspath(a[1]), os.path.abspath(a[2]), a[3] if len(a) > 3 else 1)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
