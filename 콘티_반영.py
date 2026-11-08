r"""장면 무빙 콘티(웹 페이지) → <제목>_카메라무빙.txt 반영 (사용자 결정 2026-11-08: 장면별 카메라 무빙·장면 전환을 드롭다운으로 고르고 직접 입력도)

사용: python 콘티_반영.py <제목>_카메라무빙.txt <콘티 폴더>
  <콘티 폴더> = Claude 가 ArtifactData list(collection "scenes", out_dir=<폴더>) 로 받은 곳 (<폴더>/scenes/<번호>.json)
  각 문서: {n, move, trans, moveCustom, transCustom} — move/trans 는 'auto'(자동) · 무빙/전환 이름 · 'custom'(직접 입력)
결과: 고른 장면은 '수동:<이름>', 'auto' 는 '자동:…' 으로 되돌림. 직접 입력은 그대로 적을 수 없으니 목록으로 출력 →
      Claude 가 가장 가까운 무빙·전환으로 바꾸거나(파일의 무빙 칸을 고침) 새 무빙을 만들어 넣음
"""
import glob
import json
import os
import sys


def main():
    plan_path, d = sys.argv[1], sys.argv[2]
    picks = {}
    for f in glob.glob(os.path.join(d, "**", "*.json"), recursive=True):
        try:
            v = json.load(open(f, encoding="utf-8"))
            v = v.get("data", v) if isinstance(v, dict) else {}
            n = int(v.get("n") or os.path.splitext(os.path.basename(f))[0])
            picks[n] = v
        except Exception:
            continue
    lines = open(plan_path, encoding="utf-8").read().splitlines()
    out, customs, changed = [], [], 0
    for ln in lines:
        p = [x.strip() for x in ln.split("|")]
        if len(p) < 4 or not p[0].isdigit():
            out.append(ln.replace("# 번호 | 무빙 | 사진 설명 | 고른 이유", "# 번호 | 무빙 | 전환 | 사진 설명 | 고른 이유"))
            continue
        n = int(p[0])
        if len(p) == 4:                                  # 예전 줄(전환 칸 없음) → 전환 칸 넣기
            p = [p[0], p[1], "자동:물감", p[2], p[3]]
        mv, tr = p[1], p[2]
        v = picks.get(n)
        if v:
            m_, t_ = str(v.get("move") or "auto"), str(v.get("trans") or "auto")
            if m_ == "auto":
                mv = mv if mv.startswith("자동") or mv == "-" else "자동:" + mv.replace("수동:", "")
            elif m_ == "custom":
                customs.append(f"#{n} 무빙 직접 입력: {v.get('moveCustom', '')}")
            else:
                mv = "수동:" + m_
            if t_ == "auto":
                tr = tr if tr.startswith("자동") else "자동:물감"
            elif t_ == "custom":
                customs.append(f"#{n} 전환 직접 입력: {v.get('transCustom', '')}")
            else:
                tr = "수동:" + t_
            if (mv, tr) != (p[1], p[2]):
                changed += 1
        out.append(" | ".join([p[0], mv, tr] + p[3:]))
    open(plan_path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"반영: 고른 장면 {len(picks)}개 중 바뀐 줄 {changed}개 → {plan_path}")
    for c in customs:
        print("직접 입력(Claude 가 처리):", c)


if __name__ == "__main__":
    main()
