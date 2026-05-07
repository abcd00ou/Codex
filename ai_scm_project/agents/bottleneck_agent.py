"""
Bottleneck Detection Agent
- Calculate demand/capacity ratio per layer
- Score current bottleneck severity
- Predict bottleneck cascade (current -> next -> after)
- Estimate resolution timelines
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# Resolution timeline estimates (months to add meaningful capacity)
RESOLUTION_TIMELINES = {
    "HBM": {"months": 18, "reason": "New HBM fab capacity requires 18-24 months"},
    "CoWoS": {"months": 12, "reason": "TSMC CoWoS expansion underway, 12-18 months"},
    "GPU": {"months": 9, "reason": "Blackwell ramp + AMD MI300X providing relief"},
    "Power_DC": {"months": 24, "reason": "Transformer shortage + grid permitting 2-3 years"},
    "Networking": {"months": 6, "reason": "400G/800G capacity expanding"},
    "DRAM": {"months": 6, "reason": "DRAM cycle normalizing, oversupply possible"},
    "SSD": {"months": 3, "reason": "NAND oversupply, capacity available"},
    "CPU": {"months": 6, "reason": "Balanced supply/demand"},
    "Foundry_Advanced": {"months": 18, "reason": "TSMC 3nm/2nm expansion ongoing"},
    "ASIC": {"months": 12, "reason": "Custom silicon design cycles 18-24mo, then scale"},
    "Edge_AI": {"months": 6, "reason": "Early stage, ample capacity"},
}

# Bottleneck cascade order: as one is relieved, pressure moves to next
BOTTLENECK_CASCADE = [
    ("HBM", "Current primary bottleneck - packaging limited"),
    ("CoWoS", "Enables HBM - co-bottleneck"),
    ("Power_DC", "Emerging as DC power becomes scarce"),
    ("GPU", "Supply improving with Blackwell ramp"),
    ("Networking", "400G/800G upgrade cycle pressure"),
    ("Foundry_Advanced", "Advanced node capacity tight"),
]

# Investment windows per bottleneck phase
INVESTMENT_WINDOWS = {
    # 기준일 2026-03-24 기준으로 업데이트
    "HBM":               "2024~2025 (이미 진입) → 2026 H1 핵심 구간",
    "CoWoS":             "2024~2025 (이미 진입) → 2026 H1 핵심 구간",
    "Power_DC":          "2026 H1 ~ 2027 H1 ★현재 진입 중 (2차 병목)",
    "GPU":               "2023~ 지속 / B200 전환 수혜 2026",
    "Networking":        "2026 H1 ~ 2027 H1 ★현재 진입 중 (3차 병목)",
    "Foundry_Advanced":  "2025 ~ 2027 (N3 CoWoS 캐파 타이트)",
    "ASIC":              "2026 ~ 2027 (TPU v5, Trainium2, Maia 본격화)",
}


def score_bottleneck(component, utilization):
    """Score a component's bottleneck severity."""
    if utilization >= config.BOTTLENECK_THRESHOLDS["critical"]:
        return "critical"
    elif utilization >= config.BOTTLENECK_THRESHOLDS["high"]:
        return "high"
    elif utilization >= config.BOTTLENECK_THRESHOLDS["medium"]:
        return "medium"
    else:
        return "low"


def compute_bottleneck_scores(utilization_data=None):
    """Compute bottleneck scores for all components."""
    if utilization_data is None:
        utilization_data = config.CURRENT_CAPACITY_UTILIZATION

    scores = {}
    for component, util in utilization_data.items():
        severity = score_bottleneck(component, util)
        scores[component] = {
            "utilization": util,
            "severity": severity,
            "utilization_pct": f"{util:.0%}",
            "headroom": f"{(1-util):.0%}",
            "resolution_months": RESOLUTION_TIMELINES.get(component, {}).get("months", "unknown"),
            "resolution_reason": RESOLUTION_TIMELINES.get(component, {}).get("reason", ""),
            "investment_window": INVESTMENT_WINDOWS.get(component, "N/A"),
        }

    return scores


def find_primary_bottleneck(scores):
    """Find the current primary bottleneck (highest utilization)."""
    sorted_components = sorted(
        scores.items(),
        key=lambda x: x[1]["utilization"],
        reverse=True
    )
    return sorted_components[0] if sorted_components else (None, {})


def predict_cascade(scores):
    """Predict bottleneck cascade sequence."""
    # Sort by current utilization
    sorted_components = sorted(
        [(c, d) for c, d in scores.items()],
        key=lambda x: x[1]["utilization"],
        reverse=True
    )

    cascade = []
    for component, data in sorted_components[:5]:
        cascade.append({
            "component": component,
            "current_util": data["utilization"],
            "severity": data["severity"],
            "will_ease_in_months": data["resolution_months"],
        })

    return cascade


def load_gap_report() -> dict | None:
    """gap_engine이 생성한 gap_report.json을 로드합니다."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "gap_report.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def compute_supply_demand_gap(modeling_results=None, gap_report: dict | None = None):  # noqa: ARG001
    """
    레이어별 수급 갭을 반환합니다.

    gap_report(gap_engine 출력)가 있으면 해당 수치를 우선 사용합니다.
    없으면 seed 수치(하드코딩)로 fallback합니다.
    """
    # ── gap_report 기반 (공시 데이터 연동) ────────────────────
    if gap_report and "layers" in gap_report:
        layers = gap_report["layers"]
        gaps = {}

        hbm = layers.get("HBM", {})
        gaps["HBM"] = {
            "supply_pb":         hbm.get("supply_pb"),
            "demand_pb":         hbm.get("demand_pb"),
            "gap_ratio":         hbm.get("gap_ratio", 1.0),
            "gap_status":        hbm.get("gap_status", "unknown"),
            "supply_confidence": hbm.get("supply_confidence"),
            "demand_confidence": hbm.get("demand_confidence"),
            "supply_basis":      hbm.get("supply_basis", ""),
            "demand_basis":      hbm.get("demand_basis", ""),
            "note":              "gap_engine 기반 (공시 수치)",
        }

        cowos = layers.get("CoWoS", {})
        gaps["CoWoS"] = {
            "supply_wpm":        cowos.get("supply_wpm"),
            "demand_wpm":        cowos.get("demand_wpm"),
            "gap_ratio":         cowos.get("gap_ratio", 1.0),
            "gap_status":        cowos.get("gap_status", "unknown"),
            "supply_confidence": cowos.get("supply_confidence"),
            "demand_confidence": cowos.get("demand_confidence"),
            "supply_basis":      cowos.get("supply_basis", ""),
            "demand_basis":      cowos.get("demand_basis", ""),
            "note":              "gap_engine 기반 (공시 수치)",
        }

        power = layers.get("Power_DC", {})
        gaps["Power_DC"] = {
            "backlog_usd_bn":    power.get("backlog_usd_bn"),
            "lead_time_months":  power.get("lead_time_months"),
            "gap_ratio":         power.get("gap_ratio", 1.0),
            "gap_status":        power.get("gap_status", "unknown"),
            "supply_confidence": power.get("supply_confidence"),
            "note":              "gap_engine 기반 (Vertiv 10-Q)",
        }

        return gaps

    # ── Seed fallback (gap_report 없을 때) ───────────────────
    # 2026 Q1 기준 공시 기반 수치 (earnings_agent seed와 동일)
    # HBM: SK Hynix(309PB) + Samsung(158PB) + Micron(104PB) = 571 PB/year
    hbm_supply_pb = 571.0
    hbm_demand_pb = 1058.0  # demand_mapper Tier 1~4 합산

    # CoWoS: TSMC 2026 Q1 공시 105K wpm, GPU 출하 역산 수요 ~70K wpm
    cowos_supply_wpm = 105000   # TSMC IR 2026 Q1
    cowos_demand_wpm = 70000    # demand_mapper GPU 역산

    # Power: Vertiv 10-Q 기반 간접 지표
    power_backlog_bn = 8.2
    power_lead_time  = 18

    gaps = {
        "HBM": {
            "supply_pb":    hbm_supply_pb,
            "demand_pb":    hbm_demand_pb,
            "gap_ratio":    round(hbm_demand_pb / hbm_supply_pb, 3),
            "gap_status":   "critical",
            "supply_basis": "SK Hynix + Samsung + Micron 연간 출하량 (seed 추정)",
            "demand_basis": "하이퍼스케일러 CapEx 역산 (seed 추정)",
            "note":         "seed fallback — gap_report 없음",
        },
        "CoWoS": {
            "supply_wpm":   cowos_supply_wpm,
            "demand_wpm":   cowos_demand_wpm,
            "gap_ratio":    round(cowos_demand_wpm / cowos_supply_wpm, 3),
            "gap_status":   "surplus",
            "supply_basis": "TSMC IR 2026 Q1 (seed 추정)",
            "demand_basis": "GPU 출하 역산 (seed 추정)",
            "note":         "seed fallback — gap_report 없음",
        },
        "Power_DC": {
            "backlog_usd_bn":   power_backlog_bn,
            "lead_time_months": power_lead_time,
            "gap_ratio":        1.15,
            "gap_status":       "tight",
            "note":             "seed fallback — Vertiv 10-Q 기반",
        },
    }
    return gaps


def analyze_cascade_risk(scores, gap_report: dict | None = None):
    """
    Cascade 리스크 분석.

    gap_report(gap_engine 출력)가 있으면 실제 수급갭 기반 cascade를 우선 사용합니다.
    없으면 가동률 임계값 기반 heuristic으로 fallback합니다.
    """
    # ── gap_report 기반 ───────────────────────────────────────
    if gap_report:
        cascade_data = gap_report.get("cascade_analysis", {})
        active = cascade_data.get("active_cascades", [])
        if active:
            risks = []
            for c in active:
                # gap_engine 포맷 → bottleneck_agent 포맷으로 변환
                layer = c.get("layer", "")
                ratio = c.get("gap_ratio", 1.0)
                severity = "critical" if ratio >= 1.3 else "high"
                downstream = c.get("downstream_layers", [])
                risks.append({
                    "chain": f"{layer} → {' → '.join(downstream)}",
                    "description": c.get("effect", ""),
                    "severity": severity,
                    "gap_ratio": ratio,
                    "lag_months": c.get("lag_months", 0),
                    "source": "gap_engine (공시 기반)",
                })
            return risks

    # ── Heuristic fallback (gap_report 없을 때) ───────────────
    risks = []

    hbm_util   = scores.get("HBM",      {}).get("utilization", 0)
    cowos_util = scores.get("CoWoS",     {}).get("utilization", 0)
    power_util = scores.get("Power_DC",  {}).get("utilization", 0)
    gpu_util   = scores.get("GPU",       {}).get("utilization", 0)

    if hbm_util > 0.85 and cowos_util > 0.85:
        risks.append({
            "chain": "HBM → CoWoS → GPU",
            "description": "패키징 병목이 HBM 공급 제약, GPU 출하 지연으로 연쇄",
            "severity": "critical",
            "affected_companies": ["SK Hynix", "Samsung", "Micron", "NVIDIA"],
            "source": "heuristic fallback",
        })

    if power_util > 0.70:
        risks.append({
            "chain": "Power Grid → DC → GPU 가동",
            "description": "전력 제약으로 신규 DC 배포 지연, GPU 클러스터 가동 늦어짐",
            "severity": "high",
            "affected_companies": ["Microsoft Azure", "AWS", "Google Cloud", "Meta"],
            "source": "heuristic fallback",
        })

    if gpu_util > 0.85:
        risks.append({
            "chain": "GPU 수요 → HBM 가속",
            "description": "GPU 세대 전환마다 HBM 탑재량 증가 → 메모리 부족 심화",
            "severity": "high",
            "affected_companies": ["SK Hynix", "Micron", "TSMC CoWoS"],
            "source": "heuristic fallback",
        })

    return risks


def run(market_state=None, modeling_results=None):
    """Run the bottleneck detection agent."""
    print("[BottleneckAgent] Analyzing supply chain bottlenecks...")

    # gap_report 로드 (gap_engine 출력 — 공시 기반 수급갭)
    gap_report = load_gap_report()
    if gap_report:
        print("  [BottleneckAgent] gap_report 로드 완료 (공시 기반 수급갭 사용)")
    else:
        print("  [BottleneckAgent] gap_report 없음 → seed 하드코딩 fallback")

    # Get utilization data
    if market_state and "capacity_utilization" in market_state:
        utilization_data = market_state["capacity_utilization"]
    else:
        utilization_data = config.CURRENT_CAPACITY_UTILIZATION

    # gap_report의 gap_ratio로 가동률 보완 (HBM / CoWoS / Power)
    if gap_report:
        layers = gap_report.get("layers", {})
        GAP_TO_UTIL = {
            "HBM":      "HBM",
            "CoWoS":    "CoWoS",
            "Power_DC": "Power_DC",
        }
        for gap_layer, util_key in GAP_TO_UTIL.items():
            ratio = layers.get(gap_layer, {}).get("gap_ratio")
            if ratio is not None and util_key in utilization_data:
                # gap_ratio를 가동률로 변환: ratio >= 1 → util = min(ratio × 0.85, 0.99)
                # 기존 config 값과 gap_ratio 중 더 심각한 쪽을 유지
                derived_util = min(ratio * 0.85, 0.99) if ratio >= 1 else ratio * 0.85
                utilization_data = dict(utilization_data)  # config 원본 불변 유지
                utilization_data[util_key] = max(
                    utilization_data[util_key],  # 기존 config 값
                    derived_util,                # gap_ratio 파생값
                )

    # Score all components
    scores = compute_bottleneck_scores(utilization_data)

    # Find primary bottleneck
    primary_name, primary_data = find_primary_bottleneck(scores)

    # Predict cascade
    cascade = predict_cascade(scores)

    # Supply-demand gaps (gap_report 우선, 없으면 seed)
    gaps = compute_supply_demand_gap(modeling_results, gap_report=gap_report)

    # Cascade risk analysis (gap_report 우선, 없으면 heuristic)
    cascade_risks = analyze_cascade_risk(scores, gap_report=gap_report)

    # Determine next bottleneck (second highest utilization, excluding co-bottlenecks)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["utilization"], reverse=True)
    next_bottleneck = sorted_scores[1][0] if len(sorted_scores) > 1 else "Unknown"
    after_bottleneck = sorted_scores[2][0] if len(sorted_scores) > 2 else "Unknown"

    # Summary
    result = {
        "current_bottleneck": primary_name,
        "current_utilization": primary_data.get("utilization", 0),
        "current_severity": primary_data.get("severity", "unknown"),
        "next_bottleneck": next_bottleneck,
        "after_bottleneck": after_bottleneck,
        "resolution_timeline_months": primary_data.get("resolution_months", "unknown"),
        "investment_window": INVESTMENT_WINDOWS.get(primary_name, "N/A"),

        "all_scores": scores,
        "cascade_sequence": cascade,
        "cascade_risks": cascade_risks,
        "supply_demand_gaps": gaps,

        "critical_components": [
            c for c, d in scores.items() if d["severity"] == "critical"
        ],
        "high_risk_components": [
            c for c, d in scores.items() if d["severity"] == "high"
        ],

        "bottleneck_narrative": (
            f"Primary bottleneck: {primary_name} at {primary_data.get('utilization_pct','?')} utilization. "
            f"Next constraint: {next_bottleneck}. "
            f"Resolution estimated in {primary_data.get('resolution_months','?')} months."
        ),
    }

    print(f"  [BottleneckAgent] Primary bottleneck: {primary_name} ({primary_data.get('utilization_pct','?')})")
    print(f"  [BottleneckAgent] Critical: {result['critical_components']}")
    print(f"  [BottleneckAgent] High risk: {result['high_risk_components']}")

    return result


if __name__ == "__main__":
    result = run()
    print(f"\nCurrent: {result['current_bottleneck']} ({result['current_utilization']:.0%})")
    print(f"Next: {result['next_bottleneck']}")
    print(f"Resolution: {result['resolution_timeline_months']} months")
    print(f"\nCritical components: {result['critical_components']}")
    print(f"High risk: {result['high_risk_components']}")
