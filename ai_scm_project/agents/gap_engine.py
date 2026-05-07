"""
gap_engine.py — 수급 갭 + 병목 구조 설명 엔진

earnings_agent (공급) + demand_mapper (수요)를 받아:
  1. 레이어별 수급 갭 계산
  2. 우선순위 구조 (누가 먼저 받는가)
  3. 취약 고객군 식별
  4. Cascade 메커니즘 (병목이 어떻게 연쇄되는가)
  5. 사업 기회 레이어 식별

출력: data/gap_report.json
"""

import json
import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GAP_REPORT_PATH = DATA_DIR / "gap_report.json"

# ── 공급 우선순위 구조 ────────────────────────────────────────
# 병목 상황에서 실제 배분 순서 (공시 + 업계 상식 기반)
SUPPLY_PRIORITY = {
    "HBM": {
        "SK_Hynix": [
            {"rank": 1, "customer": "NVIDIA",  "basis": "장기 독점 공급계약 (GB200 NVL72 전용)", "alloc_pct": 70},
            {"rank": 2, "customer": "AMD",     "basis": "MI300X/MI350 공급계약",                "alloc_pct": 15},
            {"rank": 3, "customer": "Intel",   "basis": "Gaudi 소량 공급",                      "alloc_pct": 5},
            {"rank": 4, "customer": "기타",    "basis": "잔여 물량 — 납기 불확실",               "alloc_pct": 10},
        ],
        "Samsung": [
            {"rank": 1, "customer": "자체 GPU", "basis": "삼성 자체 소비 (Mach-1 등)",          "alloc_pct": 30},
            {"rank": 2, "customer": "기타 팹리스", "basis": "NVIDIA 외 고객",                   "alloc_pct": 70},
        ],
        "Micron": [
            {"rank": 1, "customer": "NVIDIA",  "basis": "HBM3e 10% 점유율 계약",               "alloc_pct": 60},
            {"rank": 2, "customer": "기타",    "basis": "잔여",                                 "alloc_pct": 40},
        ],
    },
    "CoWoS": {
        "TSMC": [
            {"rank": 1, "customer": "NVIDIA",  "basis": "B200/GB200 CoWoS 독점 의존 (100%)",   "alloc_pct": 65},
            {"rank": 2, "customer": "AMD",     "basis": "MI300X/MI350 CoWoS",                  "alloc_pct": 15},
            {"rank": 3, "customer": "Google",  "basis": "TPU v5/v6 CoWoS",                     "alloc_pct": 10},
            {"rank": 4, "customer": "기타",    "basis": "Marvell, Broadcom ASIC 등",            "alloc_pct": 10},
        ],
    },
}

# ── Cascade 메커니즘 정의 ─────────────────────────────────────
CASCADE_CHAIN = [
    {
        "layer": "HBM",
        "trigger": "gap_ratio > 1.2",
        "effect": "NVIDIA GB200 생산 제약 → 출하 지연",
        "downstream": ["CoWoS", "Power_DC"],
        "lag_months": 2,
    },
    {
        "layer": "CoWoS",
        "trigger": "gap_ratio > 1.1",
        "effect": "첨단 AI 칩 패키징 큐 경합 심화 → TSMC N3 추가 압박",
        "downstream": ["GPU", "Foundry"],
        "lag_months": 3,
    },
    {
        "layer": "Power_DC",
        "trigger": "gap_ratio > 1.05",
        "effect": "DC 전력 제약으로 GPU 클러스터 배포 지연 → 수요 누적 가속",
        "downstream": ["Networking"],
        "lag_months": 6,
    },
    {
        "layer": "GPU",
        "trigger": "gap_ratio > 1.15",
        "effect": "대기 수요 누적 → HBM/CoWoS 추가 수요 폭발",
        "downstream": ["HBM", "CoWoS"],
        "lag_months": 1,
    },
]


def compute_gap_ratio(supply_pb: float, demand_pb: float) -> float:
    """수급 갭 비율. 1.0 초과 = 수요 > 공급 (병목)."""
    if supply_pb <= 0:
        return 999.0
    return round(demand_pb / supply_pb, 3)


def classify_gap(ratio: float) -> str:
    if ratio >= 1.30:  return "critical"
    if ratio >= 1.10:  return "tight"
    if ratio >= 0.90:  return "balanced"
    return "surplus"


def identify_vulnerable_customers(tier_data: dict, gap_ratio: float) -> list:
    """
    수급 갭 기반 취약 고객군 식별.
    장기계약 없고 우선순위 낮은 Tier가 위험.
    """
    vulnerable = []
    for tier_id, tier in tier_data.items():
        if isinstance(tier_id, str) and not tier_id.isdigit():
            continue
        has_contract = tier.get("has_long_term_contract", False)
        priority = tier.get("priority_rank", 4)
        hbm_demand = tier.get("total_hbm_demand_pb", 0)

        if gap_ratio > 1.1 and not has_contract and priority >= 3:
            risk_level = "high" if gap_ratio > 1.2 else "medium"
            vulnerable.append({
                "tier": tier.get("tier_name", f"Tier {tier_id}"),
                "risk_level": risk_level,
                "reason": f"장기계약 없음 + 우선순위 {priority}순위",
                "hbm_demand_pb": hbm_demand,
                "implication": (
                    f"HBM 수급 갭 {gap_ratio:.1%} 상황에서 "
                    f"{tier.get('vulnerability', '납기 지연 가능성')}"
                ),
            })
    return vulnerable


def identify_opportunities(gap_data: dict) -> list:
    """
    갭이 큰 레이어에서 사업 기회를 식별합니다.
    """
    opportunities = []
    for layer, data in gap_data.items():
        ratio = data.get("gap_ratio", 1.0)
        if ratio >= 1.1:
            opportunities.append({
                "layer": layer,
                "gap_ratio": ratio,
                "opportunity_type": _classify_opportunity(layer, ratio),
                "target_customers": data.get("vulnerable_customers", []),
                "timeframe": data.get("resolution_months", 12),
            })
    return sorted(opportunities, key=lambda x: x["gap_ratio"], reverse=True)


def _classify_opportunity(layer: str, ratio: float = 1.0) -> str:  # noqa: ARG001
    mapping = {
        "HBM":       "대안 메모리 솔루션 (GDDR7, CXL 확장), 재고 최적화 컨설팅",
        "CoWoS":     "Panel-level 패키징 대안 소싱, 패키징 멀티소싱 전략",
        "Power_DC":  "모듈형 전력 솔루션, 전력 효율화 컨설팅, 에너지 계약 중개",
        "GPU":       "AMD MI300X 전환 지원, 클라우드 버스팅 중개",
        "Networking":"100G→400G 업그레이드 프로젝트, InfiniBand 대안 소싱",
    }
    return mapping.get(layer, f"{layer} 공급 부족 대응 솔루션")


def build_gap_report(supply_state: dict, demand_state: dict) -> dict:
    """
    공급(supply_state) + 수요(demand_state) → 수급 갭 보고서 생성.
    """
    today = datetime.date.today().isoformat()
    companies = supply_state.get("companies", {})

    # ── HBM 수급 갭 ──────────────────────────────────────────
    # 공급: SK Hynix + Samsung + Micron 연간 공급량 합산 (PB)
    # hbm_supply_pb_annual = wpm × yield × GB/wafer × 12months ÷ 1e6
    hbm_supply_pb = sum(
        companies.get(c, {}).get("metrics", {}).get("hbm_supply_pb_annual", 0)
        for c in ["SK_Hynix", "Samsung", "Micron"]
    )
    if hbm_supply_pb == 0:
        hbm_supply_pb = 571.0  # fallback (309 + 158 + 104)

    hbm_demand_pb = demand_state.get("total_hbm_demand_pb", 2.50)
    hbm_ratio = compute_gap_ratio(hbm_supply_pb, hbm_demand_pb)

    # 공급 신뢰도 평균
    supply_conf = sum(
        companies.get(c, {}).get("confidence", 0.6)
        for c in ["SK_Hynix", "Samsung", "Micron"]
    ) / 3

    hbm_gap = {
        "layer": "HBM",
        "supply_pb": hbm_supply_pb,
        "supply_confidence": round(supply_conf, 2),
        "supply_basis": "SK Hynix + Samsung + Micron 분기 출하량 × 4 (연간 환산)",
        "demand_pb": hbm_demand_pb,
        "demand_confidence": demand_state.get("demand_confidence", 0.65),
        "demand_basis": "하이퍼스케일러 CapEx 역산 + 소버린 AI 공시",
        "gap_ratio": hbm_ratio,
        "gap_status": classify_gap(hbm_ratio),
        "priority_structure": SUPPLY_PRIORITY["HBM"],
        "resolution_months": companies.get("SK_Hynix", {}).get("metrics", {}).get(
            "hbm4_qual_timeline", "2026Q3"
        ),
        "vulnerable_customers": identify_vulnerable_customers(
            demand_state.get("tiers", {}), hbm_ratio
        ),
        "narrative": _hbm_narrative(hbm_ratio, hbm_supply_pb, hbm_demand_pb),
    }

    # ── CoWoS 수급 갭 ─────────────────────────────────────────
    cowos_supply_wpm = companies.get("TSMC", {}).get("metrics", {}).get("cowos_capacity_wpm", 105000)
    cowos_demand_wpm = demand_state.get("total_cowos_demand_wpm", 92000)
    cowos_ratio = compute_gap_ratio(cowos_supply_wpm, cowos_demand_wpm)

    cowos_gap = {
        "layer": "CoWoS",
        "supply_wpm": cowos_supply_wpm,
        "supply_confidence": companies.get("TSMC", {}).get("confidence", 0.85),
        "supply_basis": "TSMC IR 발표 (2026 목표 120K wpm, 현재 105K wpm)",
        "demand_wpm": cowos_demand_wpm,
        "demand_confidence": demand_state.get("tiers", {}).get(1, {}).get("confidence", 0.75),
        "demand_basis": "Tier 1 HBM 수요 역산 → CoWoS 환산",
        "gap_ratio": cowos_ratio,
        "gap_status": classify_gap(cowos_ratio),
        "priority_structure": SUPPLY_PRIORITY["CoWoS"],
        "resolution_months": 18,
        "vulnerable_customers": identify_vulnerable_customers(
            demand_state.get("tiers", {}), cowos_ratio
        ),
        "narrative": _cowos_narrative(cowos_ratio, cowos_supply_wpm, cowos_demand_wpm),
    }

    # ── 전력 인프라 갭 ────────────────────────────────────────
    vertiv = companies.get("Vertiv", {}).get("metrics", {})
    power_gap = {
        "layer": "Power_DC",
        "supply_indicator": "backlog_driven",
        "backlog_usd_bn": vertiv.get("backlog_usd_bn", 8.2),
        "lead_time_months": vertiv.get("lead_time_months", 18),
        "supply_confidence": companies.get("Vertiv", {}).get("confidence", 0.95),
        "gap_ratio": 1.15,    # 전력 병목 직접 수치 없음 — DC 전력 가동률 기반
        "gap_status": "tight",
        "resolution_months": 24,
        "narrative": (
            f"Vertiv 수주잔고 ${vertiv.get('backlog_usd_bn', 8.2)}B, 납기 {vertiv.get('lead_time_months', 18)}개월. "
            "GE Vernova 변압기 납기 30개월. DC 전력 제약이 GPU 클러스터 배포를 지연시키는 2차 병목."
        ),
    }

    # ── Cascade 분석 ─────────────────────────────────────────
    cascade_active = []
    gap_ratios = {"HBM": hbm_ratio, "CoWoS": cowos_ratio, "Power_DC": 1.15}

    for chain in CASCADE_CHAIN:
        layer = chain["layer"]
        ratio = gap_ratios.get(layer, 1.0)
        trigger_threshold = float(chain["trigger"].split("> ")[1])
        if ratio > trigger_threshold:
            cascade_active.append({
                "layer": layer,
                "gap_ratio": ratio,
                "effect": chain["effect"],
                "downstream_layers": chain["downstream"],
                "lag_months": chain["lag_months"],
                "status": "active",
            })

    # ── 사업 기회 ─────────────────────────────────────────────
    all_gaps = {"HBM": hbm_gap, "CoWoS": cowos_gap, "Power_DC": power_gap}
    opportunities = identify_opportunities(all_gaps)

    return {
        "generated_at": today,
        "period": demand_state.get("period", "2026"),
        "layers": {
            "HBM":      hbm_gap,
            "CoWoS":    cowos_gap,
            "Power_DC": power_gap,
        },
        "cascade_analysis": {
            "active_cascades": cascade_active,
            "cascade_count": len(cascade_active),
            "summary": (
                f"{len(cascade_active)}개 레이어에서 병목 cascade 활성. "
                "HBM → CoWoS → 전력 순서로 연쇄."
            ) if cascade_active else "현재 주요 cascade 없음.",
        },
        "opportunities": opportunities,
        "executive_summary": _build_executive_summary(hbm_gap, cowos_gap, power_gap, cascade_active),
        "data_sources": {
            "supply": "earnings_agent (실적발표 파싱 / seed 하드코딩)",
            "demand": "demand_mapper (CapEx 역산 + 공시)",
            "confidence_note": (
                "수치 옆 confidence는 데이터 품질 지표. "
                "1.0=공식 공시, 0.6=seed 추정, 0.4 미만=간접 시그널."
            ),
        },
    }


def _hbm_narrative(ratio: float, supply: float, demand: float) -> str:
    return (
        f"HBM 연간 공급 {supply:.2f}PB 대비 수요 {demand:.2f}PB — 수급갭 {ratio:.2f}x. "
        f"SK Hynix 출하량의 70%는 NVIDIA 장기계약으로 선점. "
        f"장기계약 없는 Tier 3(소버린 AI) 고객은 12~18개월 납기 리스크. "
        f"Samsung HBM3e NVIDIA 퀄 미완료로 실질 공급 집중도 심화."
    )


def _cowos_narrative(ratio: float, supply: int, demand: int) -> str:
    return (
        f"TSMC CoWoS 현재 캐파 {supply:,}wpm, 추정 수요 {demand:,}wpm — 갭 {ratio:.2f}x. "
        f"NVIDIA GB200 전량이 CoWoS 의존 (100%). "
        f"2026 Q4 120K wpm 달성 전까지 후발 고객 패키징 큐 대기 불가피. "
        f"대안: Panel-level 패키징(2027~), 칩렛 분산 구성."
    )


def _build_executive_summary(hbm: dict, cowos: dict, power: dict, cascades: list) -> str:
    lines = [
        f"[HBM] 수급갭 {hbm['gap_ratio']:.2f}x ({hbm['gap_status']}) — "
        f"공급 {hbm['supply_pb']}PB vs 수요 {hbm['demand_pb']}PB. "
        f"SK Hynix 70% NVIDIA 선점. 장기계약 없는 고객 납기 불확실.",

        f"[CoWoS] 수급갭 {cowos['gap_ratio']:.2f}x ({cowos['gap_status']}) — "
        f"TSMC {cowos['supply_wpm']:,}wpm vs 수요 {cowos['demand_wpm']:,}wpm. "
        f"120K wpm 달성은 2026 Q4. 후발 발주 고객 2027 Q1 납기 리스크.",

        f"[전력] 납기 18~30개월 (tight) — "
        f"Vertiv 수주잔고 ${power['backlog_usd_bn']}B. "
        f"DC 배포 속도 제약, GPU 클러스터 가동 지연 유발.",

        f"Cascade: {len(cascades)}개 병목 연쇄 활성. "
        f"HBM 타이트 → CoWoS 큐 경합 → 전력 병목 순서로 파급.",
    ]
    return " | ".join(lines)


def save_gap_report(report: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(GAP_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  [gap_engine] 저장 완료: {GAP_REPORT_PATH}")


def load_gap_report() -> dict | None:
    if GAP_REPORT_PATH.exists():
        with open(GAP_REPORT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def run(supply_state: dict = None, demand_state: dict = None) -> dict:
    print("[gap_engine] 수급 갭 분석 시작...")

    if supply_state is None:
        from agents.earnings_agent import load_supply_state, run as earnings_run
        supply_state = load_supply_state() or earnings_run()

    if demand_state is None:
        from agents.demand_mapper import load_demand_state, run as demand_run
        demand_state = load_demand_state() or demand_run()

    report = build_gap_report(supply_state, demand_state)
    save_gap_report(report)

    # 요약 출력
    for layer, data in report["layers"].items():
        ratio = data.get("gap_ratio", 0)
        status = data.get("gap_status", "?")
        print(f"  [{layer}] gap_ratio={ratio:.2f} ({status})")

    print(f"  Cascade 활성: {report['cascade_analysis']['cascade_count']}개")
    print(f"  사업 기회: {len(report['opportunities'])}개 레이어")
    return report


if __name__ == "__main__":
    result = run()
    print("\n─── Executive Summary ───")
    print(result["executive_summary"])
