"""그림 세트 요청서 — 제미나이·GPT 에게 장면 그림을 6장씩(2칸×3줄) 한 장에 그려 달라고 할 글을 만듦 (사용자 결정 2026-11-01)

  python -X utf8 그림_세트요청서.py <장면목록.txt> <결과.md> [--시트폴더 연재/<연재>/캐릭터시트] [--묶음 6]

  장면목록.txt : 한 줄에 한 장면 '번호 | 나오는 인물(쉼표, 없으면 -) | 장면 설명'
      예) c45 | 백도진,루미 | 흰 복도, 백도진이 무릎을 꿇고 흰 장갑 낀 손으로 은빛 목걸이를 루미에게 돌려줌
  - 6장씩 묶어 '세트 1, 세트 2 …' 로 나누고, 세트마다 그 세트에 나오는 인물의 캐릭터 시트(필수)를 함께 올리라고 적음
  - 받은 그림판은 `그림판_자르기.py <그림판> <폴더> --칸 2x3` 로 잘라 장면 번호에 넣고, 이 서버에서 2차 수정(fixes·다시 그리기)
"""
import os
import sys

HEAD = """내가 직접 만든 오리지널 캐릭터들의 설정 그림이야(함께 올린 캐릭터 시트). 이 캐릭터들로 정사각형 그림 한 장에
가로 2칸, 세로 3칸, 모두 6칸의 장면 모음을 그려 줘.
- 칸마다 가로로 긴 직사각형, 칸 사이에 얇은 흰 줄, 글자·숫자·말풍선·간판 글씨 없음
- 순서: 왼쪽 위 칸부터 오른쪽으로, 줄이 끝나면 다음 줄
- 그림체: 깔끔한 선과 단순한 색면의 2D 일러스트, 부드러운 그림자, 따뜻한 색감, 사람 비율
- 인물은 설정 그림과 똑같은 얼굴·머리·옷·소품 (설정에 없는 옷을 입히지 않음). 사람은 팔 2개·다리 2개, 같은 인물이 한 칸에 두 번 나오지 않음, 얼굴은 몸과 같은 방향
- 칸마다 장소를 분명히 (아래 설명 그대로)"""


def main(a):
    if len(a) < 2:
        print(__doc__)
        return 2
    src, out = a[0], a[1]
    n = int(a[a.index("--묶음") + 1]) if "--묶음" in a else 6
    sheet_dir = a[a.index("--시트폴더") + 1] if "--시트폴더" in a else ""
    rows = []
    for line in open(src, encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            p = [x.strip() for x in line.split("|")]
            if len(p) >= 3:
                rows.append((p[0], [c for c in p[1].split(",") if c.strip() and c.strip() != "-"], p[2]))
    md = [f"# 그림 세트 요청서 ({len(rows)}장, {n}장씩)\n",
          "쓰는 법: 제미나이 대화 하나에서 **캐릭터 시트를 처음에 모두 올리고**(필수) → 세트 글을 차례로 하나씩 붙여 넣기 (같은 대화라 그림체가 맞음).",
          "그림이 흐트러지거나 거절이 늘면 새 대화를 열고 그 세트의 시트를 다시 올린 뒤 이어서.",
          "받은 그림은 이 대화에 보내면 칸을 잘라 장면 번호에 넣고, 틀린 곳은 이 서버에서 2차 수정함.",
          "제미나이가 '서드 파티 권리' 로 거절하면: '일본 애니' 같은 말을 빼고 '내가 만든 오리지널 캐릭터' 를 강조해 다시.\n"]
    for k in range(0, len(rows), n):
        part = rows[k:k + n]
        cast = sorted({c for _, cs, _ in part for c in cs})
        md.append(f"---\n\n## 세트 {k // n + 1} — {part[0][0]}~{part[-1][0]}\n")
        if cast:
            files = [os.path.join(sheet_dir, c + ".png") if sheet_dir else c for c in cast]
            md.append("**먼저 올릴 캐릭터 시트(필수):** " + ", ".join(f"`{f}`" for f in files) + "\n")
        else:
            md.append("**캐릭터 시트:** 이 세트는 인물 없음 (같은 대화에서 그리면 그림체가 맞음)\n")
        md.append("```\n" + HEAD + "\n\n칸 순서대로 장면:")
        for i, (cid, cs, desc) in enumerate(part, 1):
            md.append(f"{i}번 칸 ({cid}) — {desc}" + ("" if cs else " (사람 없음)"))
        if len(part) < n:
            md.append(f"(남는 {n - len(part)}칸은 비워 둬)")
        md.append("```\n")
    open(out, "w", encoding="utf-8").write("\n".join(md))
    print(f"세트 {(len(rows) + n - 1) // n}개 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
