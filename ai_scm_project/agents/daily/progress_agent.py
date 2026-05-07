"""
Progress Agent - 학습 순서 관리
- 8개 주제 × 3라운드 (Lv1→Lv2→Lv3)
- 라운드별 콘텐츠 깊이 자동 조정
- 중복 발송 방지 (30분 이내 동일 주제 차단)
- 이전 발송 이력 기반 "지난번 내용 요약" 생성
"""
import os, sys, json, datetime

_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _ROOT)
import config

from agents.daily.study_email_agent import TOPICS

MAX_ROUNDS = 3
STATE_FILE = os.path.join(config.DATA_DIR, "progress_state.json")

ROUND_META = {
    1: {"label": "Lv.1 기초",   "desc": "개념·용어·시장 구조",         "depth": "입문"},
    2: {"label": "Lv.2 심화",   "desc": "정량 모델·메커니즘·케이스",   "depth": "심화"},
    3: {"label": "Lv.3 전문가", "desc": "투자 리포트·시나리오·트렌드", "depth": "전문가"},
}


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "topic_index":  0,
        "round":        1,
        "sent_count":   0,
        "history":      [],
        "start_date":   str(datetime.date.today()),
    }


def save_state(s: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)


def _last_sent_entry(state: dict, topic_id: str, round_: int) -> dict | None:
    """특정 주제+라운드의 마지막 발송 이력"""
    for h in reversed(state.get("history", [])):
        if h.get("topic_id") == topic_id and h.get("round") == round_:
            return h
    return None


def is_duplicate(state: dict, topic_id: str, round_: int, min_gap_minutes: int = 25) -> bool:
    """같은 주제+라운드를 min_gap_minutes 이내에 보낸 적 있으면 True"""
    last = _last_sent_entry(state, topic_id, round_)
    if not last:
        return False
    try:
        sent_at = datetime.datetime.fromisoformat(last["sent_at"])
        gap = (datetime.datetime.now() - sent_at).total_seconds() / 60
        return gap < min_gap_minutes
    except Exception:
        return False


def get_current_topic() -> dict:
    """
    다음에 보낼 주제 반환.
    중복이면 자동으로 advance 후 재시도.
    """
    state = load_state()

    # 최대 len(TOPICS)*MAX_ROUNDS 번 시도
    max_tries = len(TOPICS) * MAX_ROUNDS
    for _ in range(max_tries):
        idx   = state.get("topic_index", 0) % len(TOPICS)
        round_= state.get("round", 1)
        topic = TOPICS[idx]

        if not is_duplicate(state, topic["id"], round_):
            prev = _get_previous_context(state, topic["id"], round_)
            return {
                **topic,
                "round":       round_,
                "round_meta":  ROUND_META[round_],
                "num":         (state.get("sent_count", 0) % (len(TOPICS) * MAX_ROUNDS)) + 1,
                "total":       len(TOPICS) * MAX_ROUNDS,
                "prev_context": prev,
            }

        # 중복 → 강제 advance
        _do_advance(state)
        state = load_state()

    # 모든 주제가 중복이면 그냥 현재 반환 (방어)
    idx   = state.get("topic_index", 0) % len(TOPICS)
    round_= state.get("round", 1)
    return {
        **TOPICS[idx],
        "round":       round_,
        "round_meta":  ROUND_META[round_],
        "num":         state.get("sent_count", 0) + 1,
        "total":       len(TOPICS) * MAX_ROUNDS,
        "prev_context": None,
    }


def _get_previous_context(state: dict, topic_id: str, current_round: int) -> dict | None:
    """
    같은 주제의 이전 라운드 발송 이력 요약.
    2라운드 이상일 때만 의미 있음.
    """
    if current_round <= 1:
        return None
    prev_round = current_round - 1
    last = _last_sent_entry(state, topic_id, prev_round)
    if not last:
        return None
    return {
        "round":      prev_round,
        "round_label": ROUND_META[prev_round]["label"],
        "sent_date":  last.get("sent_at", "")[:10],
        "summary":    last.get("summary", f"Lv.{prev_round} 기본 개념 및 시장 구조 학습 완료"),
    }


def _do_advance(state: dict):
    """상태를 다음 주제로 이동."""
    idx   = state.get("topic_index", 0)
    round_= state.get("round", 1)

    next_idx = idx + 1
    next_round = round_

    if next_idx >= len(TOPICS):
        next_idx = 0
        next_round = round_ + 1
        if next_round > MAX_ROUNDS:
            next_round = MAX_ROUNDS  # 마지막 라운드에서 순환
            next_idx = 0

    state["topic_index"] = next_idx
    state["round"]       = next_round
    save_state(state)


def advance(topic_id: str, round_: int, summary: str = ""):
    """발송 완료 후 호출. 이력 기록 + 다음 주제로 이동."""
    state = load_state()
    state["sent_count"] = state.get("sent_count", 0) + 1
    state.setdefault("history", []).append({
        "topic_id": topic_id,
        "round":    round_,
        "sent_at":  str(datetime.datetime.now()),
        "summary":  summary,
    })
    _do_advance(state)


def print_status():
    state  = load_state()
    topic  = get_current_topic()
    total_sent = state.get("sent_count", 0)
    round_ = state.get("round", 1)

    print(f"\n{'='*60}")
    print(f"AI SCM 학습 현황")
    print(f"총 발송: {total_sent}회 | 현재 라운드: {ROUND_META[min(round_, MAX_ROUNDS)]['label']}")
    print(f"다음 주제: [{topic['num']}] {topic['title']}")
    print(f"{'='*60}")

    print("\n발송 이력 (최근 10개):")
    for h in reversed(state.get("history", [])[-10:]):
        rm = ROUND_META.get(h.get("round", 1), {})
        print(f"  {h['sent_at'][:16]}  [{rm.get('label','')}] {h['topic_id']}")
    print()
