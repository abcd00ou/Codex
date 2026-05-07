"""
demand_mapper.py — 고객 수요 역산 에이전트

공개 데이터(CapEx 공시, GPU 출하 가이던스, DC 착공 공시)를 조합해
고객군(Tier)별 HBM/CoWoS 수요를 역산합니다.

출력: data/demand_state.json
"""

import json
import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DEMAND_STATE_PATH = DATA_DIR / "demand_state.json"

# ── 역산 파라미터 ─────────────────────────────────────────────
# GB200 NVL72 랙 기준: GPU 72개 × HBM 192GB = 13,824GB/랙
HBM_PER_GB200_NVL72_RACK_GB = 72 * 192       # 13,824 GB
HBM_PER_H100_SERVER_GB      = 8 * 80         # 640 GB (DGX H100)
HBM_PER_B200_SERVER_GB      = 8 * 192        # 1,536 GB

# CapEx 중 AI 인프라 투자 비중 (추정, 기업별 공시 발언 기반)
AI_INFRA_SHARE = {
    "Microsoft": 0.60,   # "majority of CapEx going to AI infrastructure"
    "Amazon":    0.50,   # AWS Trainium + NVIDIA 병행 투자
    "Google":    0.55,   # TPU + NVIDIA 혼용
    "Meta":      0.70,   # "all-in on AI" — Llama + 자체 MTIA
    "xAI":       0.90,   # Colossus 클러스터 전용
    "Oracle":    0.75,   # OCI GPU 클러스터 전용 확장 + OpenAI $30B 계약 수행
}

# GPU 단가 (랙 or 서버 기준 평균, USD)
GPU_SERVER_PRICE_USD = {
    "GB200_NVL72_rack": 3_000_000,
    "H100_DGX":          400_000,
    "B200_server":       800_000,
}

# 고객군 Tier 정의
TIERS = {
    1: {
        "name": "하이퍼스케일러",
        "description": "CapEx 공시로 수요 직접 역산 가능",
        "companies": ["Microsoft", "Amazon", "Google", "Meta", "xAI", "Oracle"],
        "confidence_base": 0.75,
        "priority_rank": 1,          # 공급 우선순위 (낮을수록 먼저)
        "has_long_term_contract": True,
    },
    2: {
        "name": "대형 클라우드/ODM",
        "description": "DC 착공 공시 + NVIDIA 파트너 발표로 추정",
        "companies": ["CoreWeave", "ByteDance", "OCI", "Foxconn"],
        "confidence_base": 0.50,
        "priority_rank": 2,
        "has_long_term_contract": False,   # 일부만 장기계약
    },
    3: {
        "name": "소버린 AI / 국가 프로젝트",
        "description": "G2B 계약 공시 + 국가 예산 발표로 추정",
        "companies": ["G42(UAE)", "ARAMCO AI(Saudi)", "GENCI(France)", "NDIAS(India)"],
        "confidence_base": 0.40,
        "priority_rank": 3,
        "has_long_term_contract": False,   # 장기계약 없음 → 취약
    },
    4: {
        "name": "엣지 / 기업",
        "description": "판매량 가이던스 + 시장 리서치로 추정",
        "companies": ["Qualcomm", "자동차 AI", "일반 기업"],
        "confidence_base": 0.35,
        "priority_rank": 4,
        "has_long_term_contract": False,
    },
}


def _capex_to_hbm_demand(
    company: str,
    capex_usd_bn: float,
    period: str = "2026",
) -> dict:
    """
    하이퍼스케일러 CapEx → HBM 수요 역산.

    역산 로직:
        CapEx × AI 인프라 비중 → AI 장비 예산
        → GB200 NVL72 랙 수량 (랙 단가로 나눔)
        → 랙당 HBM × 랙 수 = HBM 수요
    """
    ai_share = AI_INFRA_SHARE.get(company, 0.50)
    ai_budget_usd_bn = capex_usd_bn * ai_share

    # GB200 NVL72 위주로 역산 (2026 주력 제품 기준)
    rack_price_usd_bn = GPU_SERVER_PRICE_USD["GB200_NVL72_rack"] / 1e9
    racks_est = int((ai_budget_usd_bn * 0.7) / rack_price_usd_bn)  # 70%는 GB200

    hbm_demand_gb = racks_est * HBM_PER_GB200_NVL72_RACK_GB

    # H100/B200 잔여 수요 (30%)
    h100_budget = ai_budget_usd_bn * 0.3
    h100_servers = int((h100_budget * 1e9) / GPU_SERVER_PRICE_USD["B200_server"])
    hbm_demand_gb += h100_servers * HBM_PER_B200_SERVER_GB

    return {
        "company": company,
        "capex_usd_bn": capex_usd_bn,
        "ai_infra_share": ai_share,
        "ai_budget_usd_bn": round(ai_budget_usd_bn, 1),
        "gb200_racks_est": racks_est,
        "hbm_demand_gb": hbm_demand_gb,
        "hbm_demand_pb": round(hbm_demand_gb / 1e6, 2),
        "basis": f"CapEx ${capex_usd_bn}B × AI비중 {ai_share:.0%} → GB200 역산",
        "confidence": AI_INFRA_SHARE.get(company, 0.5) * 0.75,  # 역산 불확실성 반영
        "period": period,
    }


def compute_tier1_demand(period: str = "2026") -> dict:
    """Tier 1 — 하이퍼스케일러 수요 역산."""
    capex_data = config.HYPERSCALER_CAPEX
    results = {}
    total_hbm_pb = 0.0
    total_cowos_wpm_demand = 0

    for company in TIERS[1]["companies"]:
        if company not in capex_data:
            continue
        year_key = period if period in capex_data[company] else f"{period}_est"
        if year_key not in capex_data[company]:
            continue
        capex = capex_data[company][year_key]
        demand = _capex_to_hbm_demand(company, capex, period)
        results[company] = demand
        total_hbm_pb += demand["hbm_demand_pb"]

        # CoWoS 수요: Tier1 GPU 수량 기반 역산
        # GB200 랙당 CoWoS-L: 72 GPU ÷ 5 die/wafer = 14.4 wafers
        # B200 server당 CoWoS-S: 8 GPU ÷ 20 die/wafer = 0.4 wafers
        racks = demand.get("gb200_racks_est", 0)
        cowos_l_wpm = int(racks * 72 / 5 / 12)       # CoWoS-L (GB200 NVL72)
        cowos_s_wpm = int(racks * 0.3 * 8 / 20 / 12) # CoWoS-S (잔여 B200)
        cowos_wpm = cowos_l_wpm + cowos_s_wpm
        total_cowos_wpm_demand += cowos_wpm

    return {
        "tier": 1,
        "tier_name": TIERS[1]["name"],
        "companies": results,
        "total_hbm_demand_pb": round(total_hbm_pb, 2),
        "total_cowos_demand_wpm": total_cowos_wpm_demand,
        "confidence": TIERS[1]["confidence_base"],
        "priority_rank": TIERS[1]["priority_rank"],
        "has_long_term_contract": TIERS[1]["has_long_term_contract"],
        "vulnerability": "낮음 — 장기 공급계약 보유, 우선 배분",
    }


def compute_tier2_demand(period: str = "2026") -> dict:  # noqa: ARG001
    """Tier 2 — 대형 클라우드/ODM 수요 추정. Oracle은 Tier 1으로 이동."""
    # CoreWeave: NVIDIA GPU $12B 계약 (공시) → 역산
    coreweave_gpu_contract_usd_bn = 12
    cw_racks = int((coreweave_gpu_contract_usd_bn * 1e9) / GPU_SERVER_PRICE_USD["GB200_NVL72_rack"])
    cw_hbm_pb = round(cw_racks * HBM_PER_GB200_NVL72_RACK_GB / 1e6, 2)

    # ByteDance: 중국 시장 (H20/자체칩) — HBM 수요 낮음, 별도 추정
    bytedance_hbm_pb = 0.12   # H20 기반 (HBM 탑재량 낮음)

    total_pb = cw_hbm_pb + bytedance_hbm_pb

    return {
        "tier": 2,
        "tier_name": TIERS[2]["name"],
        "companies": {
            "CoreWeave": {"hbm_demand_pb": cw_hbm_pb, "basis": "NVIDIA GPU $12B 계약 역산"},
            "ByteDance": {"hbm_demand_pb": bytedance_hbm_pb, "basis": "H20 기반 추정 (수출 통제)"},
        },
        "total_hbm_demand_pb": round(total_pb, 2),
        "confidence": TIERS[2]["confidence_base"],
        "priority_rank": TIERS[2]["priority_rank"],
        "has_long_term_contract": TIERS[2]["has_long_term_contract"],
        "vulnerability": "중간 — 일부만 장기계약, 공급 타이트 시 후순위 가능성",
    }


def compute_tier3_demand(period: str = "2026") -> dict:  # noqa: ARG001
    """Tier 3 — 소버린 AI / 국가 프로젝트 수요 추정."""
    sovereign = config.SOVEREIGN_AI
    total_pb = 0.0
    companies = {}

    for country, data in sovereign.items():
        gpu_units = data.get("gpu_demand_est_units", 0)
        # GB200 기준 HBM 환산 (일부는 H100)
        hbm_gb = gpu_units * 192 * 0.5 + gpu_units * 80 * 0.5
        hbm_pb = round(hbm_gb / 1e6, 3)
        total_pb += hbm_pb
        companies[country] = {
            "gpu_units_est": gpu_units,
            "hbm_demand_pb": hbm_pb,
            "investment_usd_bn": data.get("investment_usd_bn", 0),
            "basis": "국가 AI 예산 공시 + GPU 수량 역산",
        }

    return {
        "tier": 3,
        "tier_name": TIERS[3]["name"],
        "countries": companies,
        "total_hbm_demand_pb": round(total_pb, 3),
        "confidence": TIERS[3]["confidence_base"],
        "priority_rank": TIERS[3]["priority_rank"],
        "has_long_term_contract": TIERS[3]["has_long_term_contract"],
        "vulnerability": "높음 — 장기계약 없음, 공급 타이트 시 후순위 배치 리스크",
    }


def compute_tier4_demand(period: str = "2026") -> dict:  # noqa: ARG001
    """Tier 4 — 엣지 / 기업 수요 추정."""
    # Qualcomm AI PC, 자동차 AI 등 — HBM이 아닌 LPDDR/GDDR 위주
    # HBM 수요는 상대적으로 작음
    edge_hbm_pb = 0.08   # 엣지 AI 가속기 일부만 HBM 탑재

    return {
        "tier": 4,
        "tier_name": TIERS[4]["name"],
        "total_hbm_demand_pb": edge_hbm_pb,
        "confidence": TIERS[4]["confidence_base"],
        "priority_rank": TIERS[4]["priority_rank"],
        "has_long_term_contract": False,
        "vulnerability": "낮음 — HBM 의존도 낮아 공급 타이트 영향 제한적",
        "notes": "엣지/기업은 주로 LPDDR5X, GDDR7 사용. HBM 수요 미미.",
    }


def collect_demand_state(period: str = "2026") -> dict:
    """전체 고객군 수요를 취합합니다."""
    t1 = compute_tier1_demand(period)
    t2 = compute_tier2_demand(period)
    t3 = compute_tier3_demand(period)
    t4 = compute_tier4_demand(period)

    total_pb = (
        t1["total_hbm_demand_pb"]
        + t2["total_hbm_demand_pb"]
        + t3["total_hbm_demand_pb"]
        + t4["total_hbm_demand_pb"]
    )

    # 가중 평균 신뢰도 (Tier별 수요 비중 × 신뢰도)
    weights = [t1["total_hbm_demand_pb"], t2["total_hbm_demand_pb"],
               t3["total_hbm_demand_pb"], t4["total_hbm_demand_pb"]]
    confs   = [t1["confidence"], t2["confidence"], t3["confidence"], t4["confidence"]]
    weighted_conf = sum(w * c for w, c in zip(weights, confs)) / max(sum(weights), 1)

    return {
        "fetched_at": datetime.date.today().isoformat(),
        "period": period,
        "tiers": {1: t1, 2: t2, 3: t3, 4: t4},
        "total_hbm_demand_pb": round(total_pb, 2),
        "total_cowos_demand_wpm": t1.get("total_cowos_demand_wpm", 0),
        "demand_confidence": round(weighted_conf, 2),
        "notes": (
            "Tier 1은 CapEx 공시 역산 (신뢰도 0.75). "
            "Tier 2~4는 간접 시그널 기반 (신뢰도 0.35~0.50). "
            "전체 수치는 하한 추정값 — 실제 수요는 10~20% 높을 수 있음."
        ),
    }


def save_demand_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DEMAND_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"  [demand_mapper] 저장 완료: {DEMAND_STATE_PATH}")


def load_demand_state() -> dict | None:
    if DEMAND_STATE_PATH.exists():
        with open(DEMAND_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def run(period: str = "2026") -> dict:
    print("[demand_mapper] 고객 수요 역산 시작...")
    state = collect_demand_state(period)
    save_demand_state(state)
    print(f"  총 HBM 수요: {state['total_hbm_demand_pb']} PB (confidence: {state['demand_confidence']})")
    return state


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", default="2026", help="분석 연도 (기본: 2026)")
    args = parser.parse_args()
    result = run(period=args.period)
    print(json.dumps(result, ensure_ascii=False, indent=2))
