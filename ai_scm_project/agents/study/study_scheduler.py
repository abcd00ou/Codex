"""
Study Scheduler
- 학습 커리큘럼 관리 (8개 주제 × 3 라운드)
- 각 에이전트 실행 → DOCX 생성 → Gmail 발송
- 30분 간격 cron에 의해 호출됨
- 라운드 시스템: Round1(기초) → Round2(심화) → Round3(전문가)
"""

import os
import sys
import json
import datetime
import importlib.util

_DIR   = os.path.dirname(os.path.abspath(__file__))
_AGENT = os.path.dirname(_DIR)
_ROOT  = os.path.dirname(_AGENT)
for p in [_DIR, _AGENT, _ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

import config

# ============================================================
# 레벨별 설명
# ============================================================
LEVEL_META = {
    1: {"label": "Lv.1 기초", "desc": "마케터 입문 — 개념·용어·시장 구조 이해",     "emoji": "📗"},
    2: {"label": "Lv.2 심화", "desc": "정량 모델·케이스 스터디·공급망 메커니즘",     "emoji": "📘"},
    3: {"label": "Lv.3 전문가", "desc": "최신 트렌드·투자 리포트·시나리오 분석",     "emoji": "📕"},
}

# ============================================================
# 커리큘럼 정의 (8개 주제)
# ============================================================
CURRICULUM = [
    {
        "id": "hbm_deep_dive",
        "title": "HBM (High Bandwidth Memory)",
        "file": os.path.join(_DIR, "hbm_deep_dive_agent.py"),
        "output_prefix": "study_hbm_deep_dive",
    },
    {
        "id": "cowos_packaging",
        "title": "CoWoS & 첨단 패키징",
        "file": os.path.join(_DIR, "cowos_packaging_agent.py"),
        "output_prefix": "study_cowos_packaging",
    },
    {
        "id": "power_infrastructure",
        "title": "AI 데이터센터 전력 인프라",
        "file": os.path.join(_DIR, "power_infrastructure_agent.py"),
        "output_prefix": "study_power_infrastructure",
    },
    {
        "id": "nvidia_supply_chain",
        "title": "NVIDIA GPU 공급망 & 비즈니스 모델",
        "file": os.path.join(_DIR, "nvidia_supply_chain_agent.py"),
        "output_prefix": "study_nvidia_supply_chain",
    },
    {
        "id": "hyperscaler_capex",
        "title": "하이퍼스케일러 CapEx 전략 & AI 투자",
        "file": os.path.join(_DIR, "hyperscaler_capex_agent.py"),
        "output_prefix": "study_hyperscaler_capex",
    },
    {
        "id": "ai_networking",
        "title": "AI 클러스터 네트워킹 (InfiniBand & Ethernet)",
        "file": os.path.join(_DIR, "ai_networking_agent.py"),
        "output_prefix": "study_ai_networking",
    },
    {
        "id": "sovereign_ai",
        "title": "Sovereign AI & 지정학적 반도체 전략",
        "file": os.path.join(_DIR, "sovereign_ai_agent.py"),
        "output_prefix": "study_sovereign_ai",
    },
    {
        "id": "investment_framework",
        "title": "AI 공급망 투자 프레임워크 & 포트폴리오 전략",
        "file": os.path.join(_DIR, "investment_framework_agent.py"),
        "output_prefix": "study_investment_framework",
    },
]

MAX_ROUNDS  = 3          # 최대 3라운드 (Lv1→Lv2→Lv3)
STATE_FILE  = os.path.join(config.DATA_DIR, "study_state.json")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"history": [], "last_run": None, "next_index": 0, "round": 1}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def find_latest_docx(prefix: str) -> str | None:
    import glob as g
    pattern = os.path.join(config.REPORTS_DIR, f"{prefix}*.docx")
    files = sorted(g.glob(pattern), reverse=True)
    return files[0] if files else None


def run_agent(topic: dict, level: int) -> str | None:
    """에이전트 실행 — level 파라미터 전달."""
    agent_file = topic["file"]
    if not os.path.exists(agent_file):
        print(f"  [Scheduler] ⚠️  에이전트 파일 없음: {agent_file}")
        return None

    lm = LEVEL_META[level]
    print(f"  [Scheduler] 🔧 실행: {topic['title']} [{lm['label']}]")
    try:
        spec = importlib.util.spec_from_file_location(topic["id"], agent_file)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "run"):
            try:
                mod.run(level=level)
            except TypeError:
                # level 파라미터 미지원 에이전트 → 기본 실행
                mod.run()
        print(f"  [Scheduler] ✅ 완료: {topic['id']}")
    except Exception as e:
        print(f"  [Scheduler] ❌ 오류: {e}")
        import traceback; traceback.print_exc()
        return None

    return find_latest_docx(topic["output_prefix"])


def run_next():
    """다음 토픽 실행 → 이메일 발송."""
    state = load_state()
    idx   = state.get("next_index", 0)
    rnd   = state.get("round", 1)

    # 한 라운드 완료 → 다음 라운드로
    if idx >= len(CURRICULUM):
        if rnd >= MAX_ROUNDS:
            print(f"[Scheduler] 🏆 모든 라운드 완료! (총 {MAX_ROUNDS}라운드 × {len(CURRICULUM)}주제)")
            return
        rnd += 1
        idx  = 0
        state["round"] = rnd
        state["next_index"] = 0
        print(f"[Scheduler] 🔄 Round {rnd} 시작! ({LEVEL_META[rnd]['label']})")

    topic = CURRICULUM[idx]
    lm    = LEVEL_META[rnd]
    title_full = f"[{lm['label']}] {topic['title']}"

    print(f"\n[Scheduler] ▶ Round {rnd} — {idx+1}/{len(CURRICULUM)}: {topic['title']}")

    docx_path = run_agent(topic, level=rnd)

    if docx_path:
        from email_agent import send_study_doc
        overall_num = (rnd - 1) * len(CURRICULUM) + idx + 1
        overall_tot = MAX_ROUNDS * len(CURRICULUM)
        sent = send_study_doc(
            docx_path=docx_path,
            topic_title=title_full,
            topic_num=overall_num,
            total=overall_tot,
            level=rnd,
            round_num=rnd,
        )
        status = "sent" if sent else "email_failed"
    else:
        status = "agent_failed"

    state.setdefault("history", []).append({
        "id":       topic["id"],
        "title":    title_full,
        "round":    rnd,
        "level":    rnd,
        "index":    idx,
        "status":   status,
        "docx":     docx_path,
        "run_at":   str(datetime.datetime.now()),
    })
    state["last_run"]   = str(datetime.datetime.now())
    state["next_index"] = idx + 1
    state["round"]      = rnd
    save_state(state)

    print(f"[Scheduler] 완료: {topic['id']} R{rnd} → {status}")


def status_report():
    state   = load_state()
    rnd     = state.get("round", 1)
    idx     = state.get("next_index", 0)
    history = state.get("history", [])

    print(f"\n{'='*65}")
    print(f"AI SCM 학습 커리큘럼  |  현재: Round {rnd} ({LEVEL_META[min(rnd,3)]['label']})")
    print(f"{'='*65}")
    for r in range(1, MAX_ROUNDS + 1):
        lm = LEVEL_META[r]
        print(f"\n  {lm['emoji']} Round {r} — {lm['label']}: {lm['desc']}")
        for i, topic in enumerate(CURRICULUM):
            done = next(
                (h for h in reversed(history)
                 if h["id"] == topic["id"] and h["round"] == r), None
            )
            is_next = (r == rnd and i == idx)
            if done:
                icon = "  ✅" if done["status"] == "sent" else "  ⚠️ "
                print(f"{icon} {i+1}. {topic['title']} ({done['status']})")
            elif is_next:
                print(f"  ▶  {i+1}. {topic['title']} ← 다음 실행")
            elif r < rnd or (r == rnd and i < idx):
                print(f"  ✅ {i+1}. {topic['title']} (완료)")
            else:
                print(f"  ⏳ {i+1}. {topic['title']}")

    print(f"\n  마지막 실행: {state.get('last_run', '없음')}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--reset",  action="store_true")
    args = parser.parse_args()

    if args.status:
        status_report()
    elif args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        print("[Scheduler] 상태 초기화 완료")
    else:
        run_next()
