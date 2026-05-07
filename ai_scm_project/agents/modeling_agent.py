"""
Quantitative Modeling Agent
- Token -> GPU Demand
- GPU -> HBM Demand
- Memory Pressure (Context Length)
- SSD Demand (RAG + Vector DB)
- Power Demand
- Scenario Analysis (bear/base/bull)
- 2025-2027 demand forecast table
"""

import json
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ============================================================
# CORE QUANTITATIVE MODELS
# ============================================================

def token_to_gpu(tokens_per_day, gpu_model="H100_SXM5", utilization=0.85):
    """
    Convert daily token volume to required GPU count.

    Args:
        tokens_per_day: Total tokens processed per day
        gpu_model: GPU model key from GPU_SPECS
        utilization: GPU utilization rate (0-1)

    Returns:
        Number of GPUs required
    """
    spec = config.GPU_SPECS[gpu_model]
    gpu_tokens_per_sec = spec["tokens_per_sec_inference"]
    tokens_per_sec = tokens_per_day / 86400
    gpu_count = tokens_per_sec / (gpu_tokens_per_sec * utilization)
    return gpu_count


def gpu_to_hbm(gpu_count, gpu_model="H100_SXM5"):
    """
    Convert GPU count to total HBM demand in GB.

    Args:
        gpu_count: Number of GPUs
        gpu_model: GPU model key from GPU_SPECS

    Returns:
        Total HBM required in GB
    """
    spec = config.GPU_SPECS[gpu_model]
    # Handle rack-scale units
    if spec.get("unit") == "rack":
        hbm_per_unit = spec["hbm_gb"]
        units = gpu_count / spec.get("gpus_per_unit", 1)
        return units * hbm_per_unit
    hbm_per_gpu = spec["hbm_gb"]
    return gpu_count * hbm_per_gpu


def memory_pressure(context_length, concurrent_users, bytes_per_token=2):
    """
    Calculate KV cache memory requirement for given context/concurrency.

    Args:
        context_length: Tokens per conversation context
        concurrent_users: Simultaneous active users
        bytes_per_token: Bytes per token in KV cache (default 2 for FP16)

    Returns:
        KV cache size in GB
    """
    # KV cache = 2 (K+V) * context_length * concurrent_users * bytes_per_token
    kv_cache_gb = (context_length * concurrent_users * bytes_per_token * 2) / 1e9
    return kv_cache_gb


def ssd_demand(token_volume_per_day, rag_ratio=0.3, avg_doc_tokens=1000, bytes_per_token=2):
    """
    Estimate SSD storage demand from token volume (RAG + Vector DB).

    Args:
        token_volume_per_day: Total daily token volume
        rag_ratio: Fraction of queries using RAG (30% default)
        avg_doc_tokens: Average document chunk size in tokens
        bytes_per_token: Storage bytes per token

    Returns:
        Daily storage access in GB (proxy for SSD demand)
    """
    rag_tokens = token_volume_per_day * rag_ratio
    docs_retrieved = rag_tokens / avg_doc_tokens
    storage_gb = docs_retrieved * avg_doc_tokens * bytes_per_token / 1e9
    return storage_gb


def power_demand(gpu_count, gpu_model="H100_SXM5", pue=1.4):
    """
    Calculate total data center power demand.

    Args:
        gpu_count: Number of GPUs
        gpu_model: GPU model key from GPU_SPECS
        pue: Power Usage Effectiveness (1.4 default)

    Returns:
        Total power in MW
    """
    spec = config.GPU_SPECS[gpu_model]
    tdp = spec["tdp_w"]

    # Handle rack-scale units
    if spec.get("unit") == "rack":
        units = gpu_count / spec.get("gpus_per_unit", 1)
        server_power_w = units * tdp  # rack already includes everything
        return server_power_w * pue / 1e6

    server_overhead = 1.3  # cooling, networking, compute overhead per GPU
    return gpu_count * tdp * server_overhead * pue / 1e6


def gpu_capex(gpu_count, gpu_model="H100_SXM5"):
    """Estimate GPU procurement cost."""
    spec = config.GPU_SPECS[gpu_model]
    return gpu_count * spec["price_usd"]


# ============================================================
# TOTAL MARKET MODELING
# ============================================================

def compute_total_token_demand(year_offset=0, scenario="base"):
    """
    Compute total daily token demand across all AI services.

    Args:
        year_offset: Years from BASE_YEAR baseline (0=2025, 1=2026, 2=2027)
        scenario: bear / base / bull

    Returns:
        Total tokens per day
    """
    multiplier = config.SCENARIOS[scenario]["growth_multiplier"]
    total = 0
    breakdown = {}

    base_key = f"tokens_day_{config.BASE_YEAR}"
    fallback_key = "tokens_day_2024"

    for service, data in config.TOKEN_DEMAND.items():
        baseline = data.get(base_key, data.get(fallback_key, 0))
        # growth_rate_yoy is a multiplier (2.5 = 2.5x per year)
        # Apply scenario multiplier to the growth rate
        growth = data["growth_rate_yoy"] * multiplier
        # Compound growth: baseline * growth^years
        demand = baseline * (growth ** year_offset)
        breakdown[service] = demand
        total += demand

    return total, breakdown


def model_hardware_demand(year_offset=0, scenario="base", gpu_model="H100_SXM5"):
    """
    Full pipeline: Token -> GPU -> HBM -> SSD -> Power

    Returns:
        Dictionary of demand metrics
    """
    total_tokens, breakdown = compute_total_token_demand(year_offset, scenario)

    gpu_count = token_to_gpu(total_tokens, gpu_model)
    hbm_gb = gpu_to_hbm(gpu_count, gpu_model)
    ssd_gb = ssd_demand(total_tokens)
    power_mw = power_demand(gpu_count, gpu_model)
    capex_usd = gpu_capex(gpu_count, gpu_model)

    # KV cache for typical context lengths
    avg_context = 32000  # tokens (growing)
    concurrent = total_tokens / 86400 / 1000  # est. concurrent users
    kv_cache_gb = memory_pressure(avg_context, concurrent)

    return {
        "year": config.BASE_YEAR + year_offset,
        "scenario": scenario,
        "gpu_model": gpu_model,
        "total_tokens_per_day": total_tokens,
        "total_tokens_per_day_fmt": f"{total_tokens/1e12:.1f}T",
        "gpu_count_needed": int(gpu_count),
        "gpu_count_fmt": f"{gpu_count/1e6:.2f}M",
        "hbm_demand_gb": hbm_gb,
        "hbm_demand_fmt": f"{hbm_gb/1e6:.1f}PB",
        "ssd_demand_gb_day": ssd_gb,
        "ssd_demand_fmt": f"{ssd_gb/1e6:.1f}PB/day",
        "power_demand_mw": power_mw,
        "power_demand_fmt": f"{power_mw:.0f}MW",
        "kv_cache_gb": kv_cache_gb,
        "kv_cache_fmt": f"{kv_cache_gb/1e6:.1f}PB",
        "capex_gpu_usd": capex_usd,
        "capex_gpu_fmt": f"${capex_usd/1e9:.0f}B",
        "token_breakdown": {k: f"{v/1e12:.1f}T" for k, v in breakdown.items()},
    }


def build_scenario_table():
    """
    수요 예측 테이블 생성: 2025(실적) / 2026(현재) / 2027-2028(예측)
    2024는 베이스라인이므로 테이블에서 제외 (과거 실적은 seed_data 참조)
    """
    table = {}

    for scenario in ["bear", "base", "bull"]:
        table[scenario] = {}
        for year_offset in range(1, 5):  # 2025, 2026, 2027, 2028
            year = config.BASE_YEAR + year_offset
            metrics = model_hardware_demand(year_offset, scenario)
            table[scenario][str(year)] = metrics

    return table


def compute_current_snapshot():
    """현재 시점(2026년 Q1) 시장 스냅샷 계산. 기준: 2024 베이스라인 + 2년 성장."""
    return model_hardware_demand(year_offset=config.CURRENT_YEAR_OFFSET, scenario="base")


def run(market_state=None):
    """Run the modeling agent and return quantitative analysis."""
    print("[ModelingAgent] Running quantitative demand models...")

    # 현재 스냅샷 (2026년 Q1 기준)
    current = compute_current_snapshot()
    print(f"  [ModelingAgent] {config.CURRENT_YEAR} base GPU demand: {current['gpu_count_fmt']} GPUs")
    print(f"  [ModelingAgent] {config.CURRENT_YEAR} base HBM demand: {current['hbm_demand_fmt']}")
    print(f"  [ModelingAgent] {config.CURRENT_YEAR} base Power demand: {current['power_demand_fmt']}")

    # Full scenario table 2024-2027
    scenario_table = build_scenario_table()

    # Individual model outputs for each service — current_year 기준 (snapshot과 동일 연도)
    base_key = f"tokens_day_{config.BASE_YEAR}"
    multiplier_base = config.SCENARIOS["base"]["growth_multiplier"]
    service_breakdown = {}
    for service, data in config.TOKEN_DEMAND.items():
        baseline = data.get(base_key, data.get("tokens_day_2024", 0))
        # current snapshot과 동일하게 CURRENT_YEAR_OFFSET 적용
        growth = data["growth_rate_yoy"] * multiplier_base
        tokens = baseline * (growth ** config.CURRENT_YEAR_OFFSET)
        gpu_h100 = token_to_gpu(tokens, "H100_SXM5")
        gpu_b200 = token_to_gpu(tokens, "B200_SXM6")
        hbm_pb = gpu_to_hbm(gpu_h100, "H100_SXM5") / 1e6  # GB → PB
        service_breakdown[service] = {
            f"tokens_per_day_{config.CURRENT_YEAR}": tokens,
            "tokens_fmt": f"{tokens/1e12:.1f}T",
            "h100_equivalent": int(gpu_h100),
            "h100_fmt": f"{gpu_h100:,.0f}",
            "b200_equivalent": int(gpu_b200),
            "b200_fmt": f"{gpu_b200:,.0f}",
            "hbm_pb": hbm_pb,
            "hbm_gb": gpu_to_hbm(gpu_h100, "H100_SXM5"),  # 하위호환
            "power_mw": power_demand(gpu_h100, "H100_SXM5"),
        }

    # GPU 믹스 (2026년 Q1 현재: B200이 신규 출하 주력, H100은 설치베이스 잔존)
    gpu_mix_2026 = {
        "H100_SXM5": {"share": 0.35, "description": "레거시 설치베이스 잔존, 신규 출하 감소"},
        "H200_SXM5": {"share": 0.20, "description": "전환 모델, 일부 클라우드 선호"},
        "B200_SXM6": {"share": 0.35, "description": "신규 출하 주력 (Blackwell 본격 ramping)"},
        "GB200_NVL72": {"share": 0.10, "description": "대형 클러스터용, 수요 급증"},
    }

    curr_yr = config.CURRENT_YEAR
    result = {
        "current_snapshot": current,           # 현재(2026) 스냅샷
        "current_snapshot_2025": current,      # 하위호환 유지
        "scenario_table": scenario_table,
        "service_breakdown_2024": service_breakdown,   # 하위호환 키 유지
        f"service_breakdown_{config.CURRENT_YEAR}": service_breakdown,
        "gpu_mix_current": gpu_mix_2026,
        "as_of_date": config.AS_OF_DATE,
        "current_year": curr_yr,
        "model_parameters": {
            "default_gpu": "H100_SXM5",
            "utilization": 0.85,
            "rag_ratio": 0.30,
            "pue": 1.4,
            "avg_context_tokens": 32000,
        },
        "key_insights": [
            f"{curr_yr} 현재 총 토큰 수요 (base): {scenario_table['base'][str(curr_yr)]['total_tokens_per_day_fmt']}/day",
            f"{curr_yr} GPU 수요 (base): {scenario_table['base'][str(curr_yr)]['gpu_count_fmt']} H100-환산",
            f"{curr_yr} HBM 수요 (base): {scenario_table['base'][str(curr_yr)]['hbm_demand_fmt']}",
            f"2027 bull case 토큰: {scenario_table['bull']['2027']['total_tokens_per_day_fmt']}/day",
            f"2028 bull case GPU: {scenario_table['bull']['2028']['gpu_count_fmt']}",
        ],
    }

    print(f"  [ModelingAgent] Scenario table built: {len(scenario_table)} scenarios x 4 years")

    return result


if __name__ == "__main__":
    result = run()
    # Print summary only (full table is large)
    print("\n=== Current Snapshot (2025 Base) ===")
    snap = result["current_snapshot_2025"]
    for k, v in snap.items():
        if k not in ("token_breakdown",):
            print(f"  {k}: {v}")

    print("\n=== Scenario Comparison 2027 ===")
    for scenario in ["bear", "base", "bull"]:
        m = result["scenario_table"][scenario]["2027"]
        print(f"  {scenario}: {m['total_tokens_per_day_fmt']}/day | "
              f"GPU: {m['gpu_count_fmt']} | HBM: {m['hbm_demand_fmt']}")
