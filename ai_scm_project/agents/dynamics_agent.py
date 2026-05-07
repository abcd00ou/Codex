"""
Supply-demand dynamics agent.

This module turns the AI supply chain into a numeric flow model:
token demand -> accelerator demand -> HBM / CoWoS / power / networking / storage.

It is intentionally data-driven and conservative. The model favors explicit
coefficients and source notes over hidden assumptions so the numbers can be
replaced as better filings, IR decks, or analyst datasets become available.
"""

from __future__ import annotations

import datetime
import json
import math
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from agents import modeling_agent


BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DYNAMICS_STATE_PATH = DATA_DIR / "dynamics_state.json"
SEED_DATA_PATH = DATA_DIR / "seed_data.json"
MODEL_EVIDENCE_PATH = DATA_DIR / "model_evidence.json"


LAYER_ORDER = [
    "tokens",
    "accelerator",
    "hbm",
    "cowos",
    "foundry",
    "networking",
    "power",
    "storage",
]


SOURCE_REGISTRY = {
    "nvidia_fy2026_q4": {
        "title": "NVIDIA FY2026 Q4 results",
        "url": "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026",
        "note": "Reported Q4 revenue $68.1B and Data Center revenue $62.3B.",
        "confidence": 0.95,
    },
    "nvidia_fy2026_q3": {
        "title": "NVIDIA FY2026 Q3 results",
        "url": "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-third-quarter-fiscal-2026",
        "note": "Reported Q3 revenue $57.0B and Data Center revenue $51.2B.",
        "confidence": 0.95,
    },
    "seed_data": {
        "title": "Local seed_data.json",
        "url": str(SEED_DATA_PATH),
        "note": "Local historical time series and working assumptions.",
        "confidence": 0.65,
    },
}


SCENARIO_SETTINGS = {
    "bear": {
        "demand_multiplier": 0.78,
        "supply_ramp_multiplier": 0.92,
        "backlog_carryover": 0.55,
        "price_beta": 0.65,
    },
    "base": {
        "demand_multiplier": 1.00,
        "supply_ramp_multiplier": 1.00,
        "backlog_carryover": 0.70,
        "price_beta": 0.85,
    },
    "bull": {
        "demand_multiplier": 1.32,
        "supply_ramp_multiplier": 1.06,
        "backlog_carryover": 0.82,
        "price_beta": 1.10,
    },
}


UTILIZATION_ANCHORS = {
    "accelerator_units": ("GPU", "accelerator"),
    "hbm_pb": ("HBM", "hbm"),
    "cowos_wpm": ("CoWoS", "cowos"),
    "ai_power_gw": ("Power_DC", "power"),
    "networking_tbps": ("Networking", "networking"),
}


def _load_seed_data() -> dict[str, Any]:
    if not SEED_DATA_PATH.exists():
        return {}
    with open(SEED_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_model_evidence() -> dict[str, Any]:
    if not MODEL_EVIDENCE_PATH.exists():
        return {"sources": {}, "coefficients": {}, "formula_templates": {}}
    with open(MODEL_EVIDENCE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _coefficient(evidence: dict[str, Any], coefficient_id: str) -> float:
    coefficients = evidence.get("coefficients", {})
    sources = evidence.get("sources", {})
    if coefficient_id not in coefficients:
        raise KeyError(f"Missing coefficient evidence: {coefficient_id}")
    item = coefficients[coefficient_id]
    if not item.get("evidence_ids"):
        raise ValueError(f"Coefficient has no evidence_ids: {coefficient_id}")
    missing_sources = [src for src in item["evidence_ids"] if src not in sources]
    if missing_sources:
        raise ValueError(
            f"Coefficient {coefficient_id} references missing sources: {missing_sources}"
        )
    return float(item["value"])


def _trust_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "investment_grade_candidate"
    if confidence >= 0.50:
        return "scenario_grade"
    return "research_only"


def _model_audit(evidence: dict[str, Any]) -> dict[str, Any]:
    coefficients = evidence.get("coefficients", {})
    audited = []
    for coefficient_id, item in coefficients.items():
        confidence = float(item.get("confidence", 0))
        audited.append({
            "coefficient_id": coefficient_id,
            "confidence": confidence,
            "trust_label": _trust_label(confidence),
            "validation_status": item.get("validation_status", "unspecified"),
            "audit_priority": item.get("audit_priority", "unspecified"),
            "sensitivity_range": item.get("sensitivity_range"),
            "replacement_path": item.get("replacement_path", ""),
        })
    return {
        "lowest_confidence": min((x["confidence"] for x in audited), default=None),
        "research_only_coefficients": [
            x["coefficient_id"] for x in audited
            if x["trust_label"] == "research_only"
        ],
        "critical_audit_items": [
            x["coefficient_id"] for x in audited
            if x["audit_priority"] == "critical"
        ],
        "coefficient_audit": audited,
        "model_use_label": (
            "scenario_analysis_only"
            if any(x["trust_label"] == "research_only" for x in audited)
            else "investment_grade_candidate"
        ),
    }


def _year_value(series: dict[str, Any], year: int, fallback: float = 0.0) -> float:
    keys = [str(year), f"{year}E", f"{year}_est"]
    for key in keys:
        value = series.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    numeric_values = [
        float(v) for v in series.values()
        if isinstance(v, (int, float))
    ]
    return numeric_values[-1] if numeric_values else fallback


def _cagr_extrapolate(prev: float, years_after_known: int, growth: float) -> float:
    return prev * ((1 + growth) ** max(years_after_known, 0))


def _capacity_series(seed: dict[str, Any], year: int, scenario: str) -> dict[str, Any]:
    settings = SCENARIO_SETTINGS[scenario]

    hbm_market = seed.get("hbm_market", {})
    hbm_wpm_by_company = hbm_market.get("production_wpm_by_company", {})
    hbm_wpm = sum(_year_value(v, year) for v in hbm_wpm_by_company.values())
    if hbm_wpm <= 0:
        hbm_wpm = 95000
    if year > 2026:
        hbm_wpm = _cagr_extrapolate(hbm_wpm, year - 2026, 0.28)

    hbm_yield = float(hbm_market.get("yield_rate_cowos", 0.75))
    gb_per_wafer = 680
    hbm_supply_pb = hbm_wpm * hbm_yield * gb_per_wafer * 12 / 1e6

    cowos = seed.get("cowos_capacity", {})
    cowos_wpm = _year_value(cowos.get("tsmc_wpm", {}), year, 120000)
    if year > 2026:
        cowos_wpm = _cagr_extrapolate(cowos_wpm, year - 2026, 0.22)

    power = seed.get("datacenter_power", {})
    dc_power_gw = _year_value(power.get("global_gw", {}), year, 100)
    ai_fraction = _year_value(power.get("ai_workload_fraction", {}), year, 0.55)
    if year > 2026:
        dc_power_gw = _cagr_extrapolate(dc_power_gw, year - 2026, 0.30)
        ai_fraction = min(0.70, ai_fraction + 0.05 * (year - 2026))

    shipments = seed.get("gpu_shipments", {})
    gpu_supply_units = 0.0
    for model_name, series in shipments.items():
        if not isinstance(series, dict) or model_name.startswith("_"):
            continue
        units = _year_value(series, year)
        if "GB200_rack" in model_name:
            units *= 72
        gpu_supply_units += units
    if year > 2026:
        gpu_supply_units = _cagr_extrapolate(gpu_supply_units, year - 2026, 0.20)

    ramp = settings["supply_ramp_multiplier"]
    return {
        "accelerator_units": gpu_supply_units * ramp,
        "hbm_pb": hbm_supply_pb * ramp,
        "cowos_wpm": cowos_wpm * ramp,
        "ai_power_gw": dc_power_gw * ai_fraction * ramp,
        "networking_tbps": gpu_supply_units * 0.004 * ramp,
        "storage_pb_day": gpu_supply_units * 0.0009 * ramp,
    }


def _capex_implied_accelerator_demand(
    year: int,
    scenario: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Estimate accelerator procurement demand from hyperscaler CapEx.

    Token demand captures utilization pull. CapEx captures prebuild behavior:
    hyperscalers buy ahead of immediate token volume for training runs, reserve
    capacity, sovereign deals, redundancy, and strategic scarcity.
    """
    settings = SCENARIO_SETTINGS[scenario]
    capex = getattr(config, "HYPERSCALER_CAPEX", {})
    total_capex_bn = 0.0
    company_breakdown = {}
    for company, series in capex.items():
        value = _year_value(series, year)
        if year > 2027 and not value:
            value = _year_value(series, 2027) * ((1 + 0.18) ** (year - 2027))
        if value:
            company_breakdown[company] = value
            total_capex_bn += value

    # Working split: not all CapEx is GPUs. Land/buildings/network/electrical
    # are major portions, and some compute is ASIC or CPU.
    ai_capex_share = _coefficient(evidence, "COEF_CAPEX_AI_INFRA_SHARE")
    accelerator_share = _coefficient(evidence, "COEF_CAPEX_ACCELERATOR_SHARE")
    avg_accelerator_asp = _coefficient(evidence, "COEF_AVG_ACCELERATOR_ASP_USD")
    accelerator_units = (
        total_capex_bn
        * 1e9
        * ai_capex_share
        * accelerator_share
        / avg_accelerator_asp
        * settings["demand_multiplier"]
    )
    return {
        "accelerator_units": accelerator_units,
        "total_capex_usd_bn": total_capex_bn,
        "ai_capex_share": ai_capex_share,
        "accelerator_share": accelerator_share,
        "avg_accelerator_asp": avg_accelerator_asp,
        "company_breakdown_usd_bn": company_breakdown,
    }


def _demand_from_tokens(
    tokens_per_day: float,
    year: int,
    scenario: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    settings = SCENARIO_SETTINGS[scenario]
    tokens = tokens_per_day * settings["demand_multiplier"]

    utilization_accelerators = modeling_agent.token_to_gpu(tokens, "H100_SXM5")
    procurement = _capex_implied_accelerator_demand(year, scenario, evidence)
    accelerator_units = max(
        utilization_accelerators,
        procurement["accelerator_units"],
    )
    hbm_pb = modeling_agent.gpu_to_hbm(accelerator_units, "H100_SXM5") / 1e6
    power_gw = modeling_agent.power_demand(accelerator_units, "H100_SXM5") / 1000

    # CoWoS is modeled as wafer starts per month required to sustain annual
    # accelerator deployments. The coefficient is a working average across
    # H100/H200/B200/GB200 packages and should be tightened with package-level BOMs.
    cowos_wpm = accelerator_units * _coefficient(evidence, "COEF_COWOS_WPM_PER_ACCELERATOR")

    # Networking grows superlinearly with cluster size because distributed
    # training and inference need east-west fabric, not only host NICs.
    networking_tbps = (
        accelerator_units
        * _coefficient(evidence, "COEF_NETWORK_TBPS_PER_ACCELERATOR")
        * (1 + 0.035 * max(year - 2026, 0))
    )

    # RAG/agent workloads add storage pressure as a flow metric, not installed base.
    storage_pb_day = (
        modeling_agent.ssd_demand(
            tokens,
            rag_ratio=_coefficient(evidence, "COEF_RAG_STORAGE_RATIO"),
        )
        / 1e6
    )

    return {
        "tokens_per_day": tokens,
        "accelerator_units": accelerator_units,
        "utilization_implied_accelerators": utilization_accelerators,
        "capex_implied_accelerators": procurement["accelerator_units"],
        "capex_total_usd_bn": procurement["total_capex_usd_bn"],
        "hbm_pb": hbm_pb,
        "cowos_wpm": cowos_wpm,
        "ai_power_gw": power_gw,
        "networking_tbps": networking_tbps,
        "storage_pb_day": storage_pb_day,
    }


def _calibrate_supply_to_current_anchors(
    supply: dict[str, float],
    demand: dict[str, float],
    year: int,
    scenario: str,
) -> dict[str, float]:
    """Blend raw supply data with current utilization anchors.

    The local seed data mixes physical capacity, market-size estimates, and
    shipment estimates. Utilization anchors keep the model aligned with the
    project's current bottleneck view while preserving raw series direction.
    """
    if year < config.CURRENT_YEAR:
        return supply

    calibrated = dict(supply)
    years_forward = max(year - config.CURRENT_YEAR, 0)
    annual_supply_ramp = {
        "accelerator_units": 0.20,
        "hbm_pb": 0.28,
        "cowos_wpm": 0.22,
        "ai_power_gw": 0.30,
        "networking_tbps": 0.24,
    }

    for metric, (anchor_key, _layer) in UTILIZATION_ANCHORS.items():
        target_util = config.CURRENT_CAPACITY_UTILIZATION.get(anchor_key)
        if not target_util:
            continue
        anchored_capacity = demand.get(metric, 0.0) / target_util
        anchored_capacity *= (1 + annual_supply_ramp.get(metric, 0.18)) ** years_forward
        if scenario == "bear":
            anchored_capacity *= 0.96
        elif scenario == "bull":
            anchored_capacity *= 1.03

        # Prefer utilization anchors because the seed series mixes physical
        # units and market estimates. Raw series still remain in the saved
        # model via method notes and can replace anchors once normalized.
        calibrated[metric] = anchored_capacity

    return calibrated


def _ratio(demand: float, supply: float) -> float:
    if supply <= 0:
        return 999.0
    return demand / supply


def _status(ratio: float) -> str:
    if ratio >= 1.30:
        return "critical"
    if ratio >= 1.10:
        return "tight"
    if ratio >= 0.90:
        return "balanced"
    return "surplus"


def _price_pressure(ratio: float, beta: float) -> float:
    # Returns an index where 100 = neutral. Oversupply bottoms near 80;
    # shortage becomes convex because scarce components get allocated by price.
    shortage = max(ratio - 1.0, 0.0)
    surplus = max(1.0 - ratio, 0.0)
    return round(max(80.0, 100 * (1 + beta * (math.exp(shortage) - 1) - 0.25 * surplus)), 1)


def _layer_rows(demand: dict[str, float], supply: dict[str, float], scenario: str) -> dict[str, Any]:
    settings = SCENARIO_SETTINGS[scenario]
    mapping = {
        "accelerator": ("accelerator_units", "units"),
        "hbm": ("hbm_pb", "PB/year"),
        "cowos": ("cowos_wpm", "wafers/month"),
        "networking": ("networking_tbps", "Tbps fabric"),
        "power": ("ai_power_gw", "GW"),
        "storage": ("storage_pb_day", "PB/day"),
    }
    rows = {}
    for layer, (metric, unit) in mapping.items():
        d = float(demand.get(metric, 0.0))
        s = float(supply.get(metric, 0.0))
        r = _ratio(d, s)
        rows[layer] = {
            "metric": metric,
            "unit": unit,
            "demand": round(d, 3),
            "supply": round(s, 3),
            "gap_ratio": round(r, 3),
            "gap_status": _status(r),
            "shortfall": round(max(d - s, 0.0), 3),
            "surplus": round(max(s - d, 0.0), 3),
            "price_pressure_index": _price_pressure(r, settings["price_beta"]),
        }
    return rows


def _effective_deployment(demand: dict[str, float], rows: dict[str, Any]) -> dict[str, Any]:
    constraints = {
        layer: min(1.0, 1.0 / max(data["gap_ratio"], 0.0001))
        for layer, data in rows.items()
        if layer in {"accelerator", "hbm", "cowos", "networking", "power"}
    }
    limiting_layer = min(constraints, key=constraints.get)
    fulfillment = constraints[limiting_layer]
    requested_accelerators = demand["accelerator_units"]
    deployed_accelerators = requested_accelerators * fulfillment
    return {
        "requested_accelerators": round(requested_accelerators),
        "deployed_accelerators": round(deployed_accelerators),
        "unserved_accelerators": round(max(requested_accelerators - deployed_accelerators, 0)),
        "fulfillment_rate": round(fulfillment, 3),
        "limiting_layer": limiting_layer,
        "constraint_scores": {k: round(v, 3) for k, v in constraints.items()},
    }


def _relationship_edges() -> list[dict[str, Any]]:
    return [
        {
            "source": "tokens",
            "target": "accelerator",
            "coefficient": "tokens_per_day / (gpu_tokens_per_sec * utilization * 86400)",
            "interpretation": "Inference/training demand becomes accelerator capacity demand.",
        },
        {
            "source": "accelerator",
            "target": "hbm",
            "coefficient": "GPU count * HBM GB per accelerator",
            "interpretation": "Accelerator mix determines HBM bit demand and memory maker allocation.",
        },
        {
            "source": "accelerator",
            "target": "cowos",
            "coefficient": "GPU count * advanced-package wafer-start factor",
            "interpretation": "High-end AI accelerators consume advanced packaging slots.",
        },
        {
            "source": "accelerator",
            "target": "power",
            "coefficient": "GPU count * TDP * server overhead * PUE",
            "interpretation": "Cluster deployment is capped by power delivery and cooling.",
        },
        {
            "source": "accelerator",
            "target": "networking",
            "coefficient": "GPU count * fabric bandwidth factor",
            "interpretation": "Large clusters create east-west network demand.",
        },
        {
            "source": "tokens",
            "target": "storage",
            "coefficient": "tokens * RAG ratio * bytes per token",
            "interpretation": "Agentic/RAG workloads add storage and retrieval pressure.",
        },
    ]


def build_dynamics(
    modeling_results: dict[str, Any] | None = None,
    years: list[int] | None = None,
) -> dict[str, Any]:
    seed = _load_seed_data()
    evidence = _load_model_evidence()
    years = years or [2026, 2027, 2028]
    base_year = config.BASE_YEAR

    simulations = {}
    for scenario in ["bear", "base", "bull"]:
        simulations[scenario] = {}
        backlog_accelerators = 0.0
        for year in years:
            offset = year - base_year
            if modeling_results and str(year) in modeling_results.get("scenario_table", {}).get(scenario, {}):
                tokens = modeling_results["scenario_table"][scenario][str(year)]["total_tokens_per_day"]
            else:
                tokens, _ = modeling_agent.compute_total_token_demand(offset, scenario)

            demand = _demand_from_tokens(tokens, year, scenario, evidence)
            if backlog_accelerators:
                demand["accelerator_units"] += backlog_accelerators
                demand["hbm_pb"] += modeling_agent.gpu_to_hbm(backlog_accelerators, "H100_SXM5") / 1e6
                demand["cowos_wpm"] += (
                    backlog_accelerators
                    * _coefficient(evidence, "COEF_COWOS_WPM_PER_ACCELERATOR")
                )
                demand["ai_power_gw"] += modeling_agent.power_demand(backlog_accelerators, "H100_SXM5") / 1000

            supply = _capacity_series(seed, year, scenario)
            base_tokens, _ = modeling_agent.compute_total_token_demand(offset, "base")
            base_demand_anchor = _demand_from_tokens(base_tokens, year, "base", evidence)
            supply = _calibrate_supply_to_current_anchors(
                supply,
                base_demand_anchor,
                year,
                scenario,
            )
            rows = _layer_rows(demand, supply, scenario)
            deployment = _effective_deployment(demand, rows)

            backlog_accelerators = (
                deployment["unserved_accelerators"]
                * SCENARIO_SETTINGS[scenario]["backlog_carryover"]
            )

            simulations[scenario][str(year)] = {
                "demand": {k: round(v, 3) for k, v in demand.items()},
                "supply": {k: round(v, 3) for k, v in supply.items()},
                "layers": rows,
                "deployment": deployment,
                "next_year_backlog_accelerators": round(backlog_accelerators),
            }

    base_2026 = simulations["base"].get("2026", {})
    return {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "as_of_date": config.AS_OF_DATE,
        "model_version": "0.1",
        "layer_order": LAYER_ORDER,
        "relationship_edges": _relationship_edges(),
        "scenarios": simulations,
        "executive_summary": _summary(base_2026),
        "source_registry": SOURCE_REGISTRY,
        "model_audit": _model_audit(evidence),
        "evidence_registry": {
            "path": str(MODEL_EVIDENCE_PATH),
            "sources": evidence.get("sources", {}),
            "coefficients": evidence.get("coefficients", {}),
            "formula_templates": evidence.get("formula_templates", {}),
        },
        "method_notes": [
            "Demand is modeled from token volume and converted into infrastructure components through explicit coefficients.",
            "Supply is assembled from local seed time series and extrapolated after 2026 with scenario-specific ramp factors.",
            "Effective deployment is capped by the tightest non-token layer, creating backlog into the next period.",
            "Price pressure is an index, not a forecasted transaction price.",
        ],
    }


def _summary(base_year_state: dict[str, Any]) -> str:
    if not base_year_state:
        return "No base-year simulation available."
    deployment = base_year_state["deployment"]
    layers = base_year_state["layers"]
    limiting = deployment["limiting_layer"]
    limiting_data = layers.get(limiting, {})
    return (
        f"Base case limiting layer is {limiting} with gap ratio "
        f"{limiting_data.get('gap_ratio')}x. Fulfillment rate is "
        f"{deployment['fulfillment_rate']:.1%}, leaving "
        f"{deployment['unserved_accelerators']:,} H100-equivalent accelerators unserved."
    )


def save_dynamics_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DYNAMICS_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"  [DynamicsAgent] 저장 완료: {DYNAMICS_STATE_PATH}")


def load_dynamics_state() -> dict[str, Any] | None:
    if not DYNAMICS_STATE_PATH.exists():
        return None
    with open(DYNAMICS_STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def run(modeling_results: dict[str, Any] | None = None) -> dict[str, Any]:
    print("[DynamicsAgent] 공급망 수요-공급 동역학 시뮬레이션 중...")
    state = build_dynamics(modeling_results=modeling_results)
    save_dynamics_state(state)

    base_2026 = state["scenarios"]["base"]["2026"]
    print(f"  [DynamicsAgent] {state['executive_summary']}")
    for layer, row in base_2026["layers"].items():
        print(f"  [{layer:11s}] gap={row['gap_ratio']:.2f}x status={row['gap_status']}")
    return state


if __name__ == "__main__":
    result = run()
    print(result["executive_summary"])
