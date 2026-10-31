"""장문 다큐 웹 조사: 조사원 여러 명이 서로 다른 관점으로 동시에 조사한 뒤 결과를 합침
research_with_agents(ask_json_alive, system, base, model, tools, log, state_path) → {"topic", "facts", "stories", "questions", "myths", "recent", "sources"}
조사원마다 끝나면 state_path(대본_진행.json 옆의 _조사.json)에 저장 → 꺼졌다 켜도 끝난 조사원은 건너뜀"""
import json
import os
import threading

FOCUS = [
    ("기본 사실", "주제의 핵심 사실·인물·연도·장소를 폭넓게 모은다. 원 기록(실록·정사 등)이 있으면 어느 권·편·날짜에 적혔는지 확인한다."),
    ("일화와 오해", "이야기로 풀기 좋은 실제 일화, 그리고 소설·드라마·야사로 퍼진 오해와 실제 기록의 차이를 집중해서 찾는다."),
    ("최신 연구", "오늘 날짜 기준 최근 1~3년의 새 연구·발굴·발표·학계 논쟁을 집중해서 찾는다. 없으면 recent 는 빈 배열."),
]
KEYS = ("facts", "stories", "questions", "myths", "recent", "sources")


def research_with_agents(ask_json_alive, system, base, model, tools, log, state_path=None):
    part_path = (os.path.splitext(state_path)[0] + "_조사.json") if state_path else None
    parts = {}
    if part_path and os.path.exists(part_path):
        try:
            parts = json.load(open(part_path, encoding="utf-8"))
        except Exception:
            parts = {}
    lock = threading.Lock()

    def run(name, focus):
        try:
            r = ask_json_alive(model, system, base + f"\n\n[이번 조사원의 담당: {name}] {focus}", tools=tools, log=log, label=f"웹 조사({name})")
            if isinstance(r, dict):
                with lock:
                    parts[name] = r
                    if part_path:
                        json.dump(parts, open(part_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                log(f"  ✓ 조사원 '{name}' 끝 (사실 {len(r.get('facts') or [])}개)")
        except Exception as e:
            log(f"  ⚠ 조사원 '{name}' 실패: {str(e).splitlines()[0][:100] if str(e) else e}")
    todo = [(n, f) for n, f in FOCUS if n not in parts]
    ths = [threading.Thread(target=run, args=nf, daemon=True) for nf in todo]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    if not parts:
        raise RuntimeError("웹 조사에 모두 실패했습니다 (Claude 연결·로그인 확인)")
    out = {"topic": next((str(p.get("topic")) for p in parts.values() if p.get("topic")), "")}
    for k in KEYS:                       # 겹치는 줄은 한 번만
        seen, lst = set(), []
        for n, _ in FOCUS:
            for x in (parts.get(n) or {}).get(k) or []:
                x = str(x).strip()
                if x and x not in seen:
                    seen.add(x)
                    lst.append(x)
        out[k] = lst
    return out
