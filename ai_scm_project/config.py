"""
AI Supply Chain Intelligence System - Configuration
All constants, parameters, and company mappings
"""

# ============================================================
# GPU SPECIFICATIONS (2025-2026 baseline)
# ============================================================
GPU_SPECS = {
    "H100_SXM5": {
        "tflops_bf16": 989,
        "hbm_gb": 80,
        "hbm_type": "HBM3",
        "hbm_bw_tbps": 3.35,
        "tdp_w": 700,
        "tokens_per_sec_inference": 2000,
        "price_usd": 30000,
        "nm_node": "4nm",
        "vendor": "NVIDIA",
        "gpus_per_unit": 1,
    },
    "H200_SXM5": {
        "tflops_bf16": 989,
        "hbm_gb": 141,
        "hbm_type": "HBM3e",
        "hbm_bw_tbps": 4.8,
        "tdp_w": 700,
        "tokens_per_sec_inference": 2800,
        "price_usd": 40000,
        "nm_node": "4nm",
        "vendor": "NVIDIA",
        "gpus_per_unit": 1,
    },
    "B200_SXM6": {
        "tflops_bf16": 2250,
        "hbm_gb": 192,
        "hbm_type": "HBM3e",
        "hbm_bw_tbps": 8.0,
        "tdp_w": 1000,
        "tokens_per_sec_inference": 4500,
        "price_usd": 70000,
        "nm_node": "4nm",
        "vendor": "NVIDIA",
        "gpus_per_unit": 1,
    },
    "MI300X": {
        "tflops_bf16": 1307,
        "hbm_gb": 192,
        "hbm_type": "HBM3",
        "hbm_bw_tbps": 5.3,
        "tdp_w": 750,
        "tokens_per_sec_inference": 2500,
        "price_usd": 20000,
        "nm_node": "5nm",
        "vendor": "AMD",
        "gpus_per_unit": 1,
    },
    "GB200_NVL72": {
        "tflops_bf16": 90000,
        "hbm_gb": 13824,
        "hbm_type": "HBM3e",
        "hbm_bw_tbps": 576.0,
        "tdp_w": 120000,  # full rack
        "tokens_per_sec_inference": 200000,
        "price_usd": 3000000,
        "nm_node": "4nm",
        "vendor": "NVIDIA",
        "unit": "rack",
        "gpus_per_unit": 72,
    },
}

# ============================================================
# HYPERSCALER CAPEX (USD billion, actual + guidance)
# ============================================================
HYPERSCALER_CAPEX = {
    # 2022-2025: 실제 집행 (actual), 2026: Q1 2026 실적 기반 가이던스 (raised), 2027: 추정
    # 2026 업데이트 (2026-04-28): Q1 2026 실적 발표 후 전면 상향 조정
    #   Microsoft: $95B → $190B (Azure +39% CC, AI run-rate $37B; FY2026 Q3 guidance 상향)
    #   Google: $90B → $190B (Cloud +63% YoY >$20B; Q1 2026 CapEx $35.7B)
    #   Amazon: $130B → $200B (AWS +28% $37.6B; Q1 2026 CapEx $44.2B)
    #   Meta: $72B → $135B (Q1 CapEx $19.84B; FY guidance $125-145B 중점)
    "Microsoft": {"2022": 22, "2023": 28, "2024": 55, "2025": 80,  "2026": 190, "2027_est": 230},
    "Google":    {"2022": 25, "2023": 32, "2024": 52, "2025": 75,  "2026": 190, "2027_est": 250},
    "Amazon":    {"2022": 38, "2023": 48, "2024": 75, "2025": 105, "2026": 200, "2027_est": 240},
    "Meta":      {"2022": 31, "2023": 28, "2024": 37, "2025": 65,  "2026": 135, "2027_est": 165},
    "xAI":       {"2022": 0,  "2023": 0,  "2024": 6,  "2025": 15,  "2026": 30,  "2027_est": 50},
    # Oracle: OpenAI $30B 클라우드 계약 수주 + OCI GPU 클러스터 공격적 확장
    "Oracle":    {"2022": 4,  "2023": 7,  "2024": 11, "2025": 16,  "2026": 20,  "2027_est": 25},
}
# 연도별 데이터 유형 (actual=실적, guidance=가이던스, estimate=추정)
HYPERSCALER_CAPEX_TYPE = {
    "2022": "actual", "2023": "actual", "2024": "actual",
    "2025": "actual", "2026": "guidance", "2027_est": "estimate",
}

# ============================================================
# HBM MARKET DATA
# ============================================================
HBM_MARKET = {
    "market_share": {
        "SK_Hynix": 0.50,
        "Samsung": 0.35,
        "Micron": 0.15,
    },
    "capacity_wafers_per_month": {
        "SK_Hynix": 50000,
        "Samsung": 40000,
        "Micron": 20000,
    },
    "price_per_gb_usd": {
        "HBM2e": 8,
        "HBM3": 14,
        "HBM3e": 18,
    },
    "market_size_usd_bn": {
        "2023": 14,   # actual
        "2024": 22,   # actual
        "2025": 35,   # actual (확정)
        "2026": 55,   # 현재연도 추정 (진행 중)
        "2027_est": 80,
    },
    "cowos_dependency": True,   # TSMC CoWoS required
    "yield_rate": 0.75,          # HBM on CoWoS yield
    "demand_growth_yoy": 2.5,    # annual demand growth multiplier
}

# ============================================================
# TOKEN DEMAND ESTIMATES (2025 actual baseline)
# 방법론:
#   ChatGPT — Sam Altman 공식 발언 기반 (가장 신뢰도 높음)
#   나머지  — GPU 출하량 기반 역산: GPU fleet × tok/sec × 가동률 × 86400s
#             GPU fleet = 하이퍼스케일러 CapEx 공시 or 투자 공시에서 추정
# ============================================================
TOKEN_DEMAND = {
    "ChatGPT": {
        "tokens_day_2024": 10e12,
        "tokens_day_2025": 25e12,
        # Sam Altman, X(Twitter) Jan 2025: "over 1 trillion queries per week"
        # 1T queries/week ÷ 7 = 143B queries/day × ~175 tokens/query (avg input+output) = ~25T
        # growth_rate_yoy: 연간 성장 배율 (1.5 = 50% YoY). NVIDIA DC 매출 ~75% YoY 기준 보수적 설정
        "growth_rate_yoy": 1.5,
        "model": "GPT-4o/o1/o3",
        "operator": "OpenAI",
        "source": "sam_altman_statement",
        "source_detail": "Sam Altman, X(Twitter), Jan 2025: 1T queries/week → ×175 tokens/query",
        "confidence": 0.75,
        "methodology": "official_statement",
        "gpu_fleet_h100_equiv_est": None,
    },
    "Claude": {
        "tokens_day_2024": 2e12,
        "tokens_day_2025": 7e12,
        # GPU fleet 역산:
        #   Amazon-Anthropic $4B 투자 → AWS Trainium2 + H100 fleet ~80K H100-equiv
        #   80K × 2,000 tok/s × 0.55 util × 86,400s ≈ 7.6T → 7T
        "growth_rate_yoy": 1.8,   # 80% YoY: API 채택 급증, 소형 모델 확산
        "model": "Claude 3.5/3.7 Sonnet",
        "operator": "Anthropic",
        "source": "gpu_fleet_estimate",
        "source_detail": "Amazon $4B Anthropic 투자 공시 → AWS Trainium2+H100 fleet 역산 (80K H100-equiv × 2K tok/s × 0.55 util)",
        "confidence": 0.45,
        "methodology": "gpu_fleet_reverse",
        "gpu_fleet_h100_equiv_est": 80000,
    },
    "Gemini": {
        "tokens_day_2024": 3e12,
        "tokens_day_2025": 10e12,
        # GPU fleet 역산:
        #   Google 2025 CapEx $75B × AI 인프라 55% = ~$41B
        #   GPU fleet ~700K H100-equiv, Gemini 할당 ~15% = 105K
        #   105K × 2,000 tok/s × 0.55 util × 86,400s ≈ 10T
        "growth_rate_yoy": 1.7,   # 70% YoY: Gemini 2.0 확산, Workspace 통합
        "model": "Gemini 2.0 Pro/Flash/Ultra",
        "operator": "Google",
        "source": "gpu_fleet_estimate",
        "source_detail": "Google CapEx $75B 공시 → H100+TPU fleet 역산 (105K H100-equiv × 2K tok/s × 0.55 util)",
        "confidence": 0.45,
        "methodology": "gpu_fleet_reverse",
        "gpu_fleet_h100_equiv_est": 105000,
    },
    "Llama_OSS": {
        "tokens_day_2024": 5e12,
        "tokens_day_2025": 18e12,
        # GPU fleet 역산:
        #   Meta GPU fleet ~600K H100-equiv ($65B CapEx), Llama 서빙 ~30% = 180K
        #   커뮤니티 (Together AI, Groq, Fireworks, 자체설치) ~50K
        #   230K × 2,000 tok/s × 0.45 util × 86,400s ≈ 18T
        "growth_rate_yoy": 1.6,   # 60% YoY: OSS 채택 지속, DeepSeek 포함
        "model": "Llama 3.3/4.x + DeepSeek V3/R1",
        "operator": "Meta/Community",
        "source": "gpu_fleet_estimate",
        "source_detail": "Meta CapEx $65B 공시 → fleet 역산 + 커뮤니티 추정 (230K H100-equiv × 2K tok/s × 0.45 util). 분산 OSS 특성상 불확실성 높음",
        "confidence": 0.35,
        "methodology": "gpu_fleet_reverse",
        "gpu_fleet_h100_equiv_est": 230000,
    },
    "Other": {
        "tokens_day_2024": 5e12,
        "tokens_day_2025": 12e12,
        # GPU fleet 역산:
        #   NVIDIA DC 잔여 fleet: xAI Grok 100K + Mistral/Cohere 30K + 기업 내부 LLM 70K = 200K
        #   200K × 2,000 tok/s × 0.40 util × 86,400s ≈ 13.8T → 12T (보수적 하한)
        "growth_rate_yoy": 1.4,   # 40% YoY: 기업 AI 도입 확산, 효율화로 상쇄
        "model": "Grok / Mistral / DeepSeek / 기업 내부 LLM",
        "operator": "xAI / Mistral / Various",
        "source": "gpu_fleet_estimate",
        "source_detail": "NVIDIA DC 매출 잔여 fleet 역산 — xAI 100K + Mistral/Cohere 30K + 기업 70K H100-equiv × 2K tok/s × 0.40 util",
        "confidence": 0.35,
        "methodology": "gpu_fleet_reverse",
        "gpu_fleet_h100_equiv_est": 200000,
    },
    # ── 합계 ─────────────────────────────────────────────────────────────────
    # 2025 실제: ~72T tokens/day (ChatGPT 25T 공식 발언 + 나머지 GPU fleet 역산)
    # 2026 예측: ~108T tokens/day (base case, 서비스별 40~80% YoY 성장)
    # growth_rate_yoy: 연간 성장 배율 (1.5 = +50%/yr). 2024→2025 실제: +190%였으나
    #   2025→ 이후는 시장 성숙·효율화로 40~80% 수준으로 둔화 가정 (NVIDIA DC 매출 ~75% YoY 기반)
    # 방법론 신뢰도: ChatGPT 0.75 / 나머지 0.35~0.45
}

# ============================================================
# VALUE CHAIN DEFINITION
# ============================================================
VALUE_CHAIN = {
    "end_customer": {
        "companies": ["OpenAI", "Anthropic", "Google DeepMind", "Meta AI", "xAI"],
        "bottleneck_risk": "low",
        "description": "AI model developers and end-user services",
    },
    "ai_service": {
        "companies": ["OpenAI API", "Anthropic API", "Cohere", "Mistral", "Together AI"],
        "bottleneck_risk": "medium",
        "description": "AI API and inference services",
    },
    "cloud_dc": {
        "companies": ["Microsoft Azure", "AWS", "Google Cloud", "Oracle Cloud", "CoreWeave"],
        "bottleneck_risk": "high",
        "description": "Cloud and data center operators",
    },
    "gpu_server": {
        "companies": ["NVIDIA", "AMD", "Intel Gaudi"],
        "bottleneck_risk": "critical",
        "description": "GPU compute hardware",
    },
    "asic": {
        "companies": ["Google TPU", "AWS Trainium", "Microsoft Maia", "Meta MTIA", "Apple Neural Engine"],
        "bottleneck_risk": "medium",
        "description": "Custom AI accelerator ASICs",
    },
    "hbm": {
        "companies": ["SK Hynix", "Samsung", "Micron"],
        "bottleneck_risk": "critical",
        "description": "High Bandwidth Memory for AI GPUs",
    },
    "dram": {
        "companies": ["Samsung", "SK Hynix", "Micron"],
        "bottleneck_risk": "medium",
        "description": "Standard DRAM for CPU and system memory",
    },
    "ssd_storage": {
        "companies": ["Solidigm", "Samsung SSD", "Kioxia", "WD/SanDisk", "Seagate"],
        "bottleneck_risk": "low",
        "description": "NVMe SSD for AI training datasets and RAG",
    },
    "cpu": {
        "companies": ["Intel", "AMD", "Ampere", "ARM"],
        "bottleneck_risk": "low",
        "description": "CPU for AI inference and orchestration",
    },
    "networking": {
        "companies": ["Broadcom", "Marvell", "Arista", "Cisco", "Mellanox/NVIDIA"],
        "bottleneck_risk": "high",
        "description": "High-speed interconnect for AI clusters",
    },
    "packaging": {
        "companies": ["TSMC CoWoS", "ASE", "Amkor", "Samsung Foundry"],
        "bottleneck_risk": "critical",
        "description": "Advanced packaging (CoWoS) for HBM+GPU integration",
    },
    "power": {
        "companies": ["Vertiv", "Eaton", "Schneider Electric", "GE Vernova", "ABB"],
        "bottleneck_risk": "high",
        "description": "Power infrastructure for data centers",
    },
    "foundry": {
        "companies": ["TSMC", "Samsung Foundry", "SMIC", "Intel Foundry"],
        "bottleneck_risk": "high",
        "description": "Semiconductor foundries",
    },
    "edge_ai": {
        "companies": ["Qualcomm", "Apple", "Samsung LSI", "MediaTek", "Arm"],
        "bottleneck_risk": "low",
        "description": "Edge AI NPUs and mobile processors",
    },
    "sovereign_ai": {
        "companies": ["G42 (UAE)", "ARAMCO AI (Saudi)", "GENCI (France)", "DFKI (Germany)", "NDIAS (India)"],
        "bottleneck_risk": "medium",
        "description": "National AI compute initiatives",
    },
}

# ============================================================
# BOTTLENECK SCORING THRESHOLDS
# ============================================================
BOTTLENECK_THRESHOLDS = {
    "critical": 0.85,   # demand/capacity > 85%
    "high": 0.70,
    "medium": 0.50,
    "low": 0.30,
}

# ============================================================
# 현재 시점 앵커 (리포트 기준일)
# ============================================================
AS_OF_DATE    = "2026-04-28"   # 리포트 기준일
CURRENT_YEAR  = 2026           # 현재 연도
BASE_YEAR     = 2025           # 토큰 수요 베이스라인 연도 (2025 실제 데이터)
CURRENT_YEAR_OFFSET = 1        # 2025 + 1 = 2026

# Current capacity utilization (2026년 Q1 기준)
# 2025년 대비 변화: CoWoS 캐파 증설로 HBM 소폭 완화,
# 그러나 B200/GB200 수요 폭증으로 Power/Networking이 새 병목으로 부상
CURRENT_CAPACITY_UTILIZATION = {
    # gap_engine 공시 기반 수치 우선, 나머지는 시장 추정
    "HBM":        0.99,   # gap_engine: 공급 571PB vs 수요 1,058PB → 1.85x 초과 수요 (공시 기반)
    "CoWoS":      0.66,   # gap_engine: 공급 105K wpm vs 수요 69K wpm → 0.66x 공급 우위
    "Power_DC":   0.87,   # gap_engine: 1.15x tight (Vertiv 수주잔고 $8.2B, 납기 18개월)
    "Networking": 0.80,   # 추정: GB200 NVL72 InfiniBand/NVLink 수요 급증
    "GPU":        0.85,   # 추정: B200/GB200 출하 증가에도 수요 동반 급증
    "Foundry":    0.84,   # 추정: N3/N4 CoWoS 수요 여전히 타이트
    "ASIC":       0.78,   # 추정: TPU v5, Trainium2, Maia 100 본격 ramping
    "DRAM":       0.62,   # 추정: 상대적 균형 유지
    "SSD":        0.42,   # 추정: 공급 우위 지속
    "CPU":        0.48,   # 추정: 안정적
    "Edge_AI":    0.60,   # 추정: 스마트폰/자동차 AI 수요 증가
}

# ============================================================
# GPU SHIPMENT ESTIMATES
# ============================================================
GPU_SHIPMENTS = {
    # actual = 확정 실적 | estimate = 추정
    "NVIDIA_H100": {
        "2023": 500000,    # actual
        "2024": 3000000,   # actual
        "2025": 5000000,   # actual
        "2026_est": 3000000,  # H100 레거시 전환, B200으로 교체 중
        "2027_est": 1000000,  # 단종 수순
    },
    "NVIDIA_B200": {
        "2024": 50000,       # actual (초기 출하)
        "2025": 1500000,     # actual (대량 ramp)
        "2026_est": 5000000, # 현재 주력 제품 (GB200 NVL72 포함)
        "2027_est": 7000000,
    },
    "NVIDIA_GB200_NVL72": {
        "2025": 5000,        # actual (랙 단위, ~36만 GPU 환산)
        "2026_est": 40000,   # 현재 주력 출하 형태 (랙 단위)
        "2027_est": 80000,
    },
    "AMD_MI300X": {
        "2024": 200000,      # actual
        "2025": 600000,      # actual
        "2026_est": 1500000, # MI325X 출시로 모멘텀
        "2027_est": 2500000,
    },
}

# ============================================================
# COWOS CAPACITY (TSMC)
# ============================================================
COWOS_CAPACITY = {
    "2023_wpm": 35000,    # actual
    "2024_wpm": 50000,    # actual
    "2025_wpm": 85000,    # actual (목표 80K 초과 달성)
    "2026_wpm": 120000,   # 현재 목표 (진행 중)
    "2027_est_wpm": 160000,
    "yield_rate": 0.78,   # 2025 개선 (2024: 0.75)
    "lead_time_months": 18,
}

# ============================================================
# DATA CENTER POWER (Global)
# ============================================================
DC_POWER = {
    "2022_gw": 30,    # actual
    "2023_gw": 40,    # actual
    "2024_gw": 50,    # actual
    "2025_gw": 70,    # actual
    "2026_gw": 100,   # 현재연도 추정 (진행 중)
    "2027_est_gw": 140,
    "ai_fraction": 0.40,  # AI workloads share of DC power
    "transformer_lead_time_months": 30,  # US transformer lead time
    "pue_average": 1.4,
}

# ============================================================
# INVESTMENT PHASES
# ============================================================
INVESTMENT_PHASES = {
    1: {
        "focus": "GPU Compute",
        "timeframe": "2023-2024",
        "key_players": ["NVIDIA", "AMD", "TSMC"],
        "status": "Peak",
        "description": "Core GPU demand wave, NVIDIA dominance established",
    },
    2: {
        "focus": "HBM & Memory",
        "timeframe": "2024-2025",
        "key_players": ["SK Hynix", "Micron", "Samsung"],
        "status": "Active",
        "description": "HBM bottleneck creates memory upcycle opportunity",
    },
    3: {
        "focus": "Power Infrastructure",
        "timeframe": "2025-2026",
        "key_players": ["Vertiv", "Schneider Electric", "GE Vernova", "Eaton"],
        "status": "Emerging",
        "description": "Data center power constraints drive infrastructure investment",
    },
    4: {
        "focus": "Edge & Physical AI",
        "timeframe": "2026-2027",
        "key_players": ["Qualcomm", "Arm", "ASML", "Applied Materials"],
        "status": "Early",
        "description": "AI moves to edge devices and physical world (robotics, autos)",
    },
}

# ============================================================
# SCENARIO MULTIPLIERS
# ============================================================
SCENARIOS = {
    "bear": {
        "growth_multiplier": 0.7,
        "description": "Macro slowdown, AI investment pullback, efficiency gains offset demand",
    },
    "base": {
        "growth_multiplier": 1.0,
        "description": "Current trajectory, 2024 growth rates maintained",
    },
    "bull": {
        "growth_multiplier": 1.5,
        "description": "AGI acceleration, agentic AI, Sovereign AI drives upside",
    },
}

# ============================================================
# SOVEREIGN AI PROGRAMS
# ============================================================
SOVEREIGN_AI = {
    "UAE": {
        "investment_usd_bn": 100,
        "timeline": "2025-2030",
        "partners": ["Microsoft", "NVIDIA", "G42"],
        "gpu_demand_est_units": 50000,
    },
    "Saudi_Arabia": {
        "investment_usd_bn": 40,
        "timeline": "2024-2027",
        "partners": ["NVIDIA", "Qualcomm", "Huawei"],
        "gpu_demand_est_units": 30000,
    },
    "EU": {
        "investment_usd_bn": 20,
        "timeline": "2025-2030",
        "partners": ["Multiple"],
        "gpu_demand_est_units": 40000,
    },
    "Japan": {
        "investment_usd_bn": 7,
        "timeline": "2024-2026",
        "partners": ["RAPIDUS", "NVIDIA", "Microsoft"],
        "gpu_demand_est_units": 20000,
    },
    "India": {
        "investment_usd_bn": 1.25,
        "timeline": "2024-2027",
        "partners": ["NVIDIA", "AMD", "Multiple"],
        "gpu_demand_est_units": 10000,
    },
}

# ============================================================
# OUTPUT PATHS
# ============================================================
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
REPORTS_DIR = os.path.join(OUTPUTS_DIR, "reports")
PPTX_DIR = os.path.join(OUTPUTS_DIR, "pptx")

SEED_DATA_PATH = os.path.join(DATA_DIR, "seed_data.json")
MARKET_STATE_PATH = os.path.join(DATA_DIR, "market_state.json")
RUN_STATE_PATH = os.path.join(DATA_DIR, "run_state.json")

# ============================================================
# REFERENCE URLs (각 데이터 출처)
# ============================================================
REFERENCE_URLS = {
    # 하이퍼스케일러 CapEx
    "Microsoft_CapEx": "https://www.microsoft.com/en-us/investor/earnings/fy-2025-fourth-quarter/press-release",
    "Google_CapEx": "https://abc.xyz/investor/",
    "Amazon_CapEx": "https://ir.aboutamazon.com/",
    "Meta_CapEx": "https://investor.fb.com/",

    # GPU / NVIDIA
    "NVIDIA_DataCenter": "https://investor.nvidia.com/financial-information/quarterly-results/default.aspx",
    "NVIDIA_B200": "https://www.nvidia.com/en-us/data-center/gb200-nvl72/",
    "NVIDIA_H100": "https://www.nvidia.com/en-us/data-center/h100/",

    # HBM 시장
    "SKHynix_HBM": "https://news.skhynix.com/hbm/",
    "HBM_Market_Size": "https://www.precedenceresearch.com/high-bandwidth-memory-market",
    "Micron_HBM": "https://investors.micron.com/",

    # TSMC CoWoS
    "TSMC_CoWoS": "https://ir.tsmc.com/english/annualReports",
    "TSMC_Capacity": "https://www.tsmc.com/english/dedicatedFoundry/technology/cowos",

    # AI 투자 관계
    "NVIDIA_OpenAI_Investment": "https://www.bloomberg.com/news/articles/2025-01-23/nvidia-agrees-to-invest-in-openai",
    "Microsoft_OpenAI": "https://blogs.microsoft.com/blog/2023/01/23/microsoftandopenaiextendpartnership/",
    "Google_Anthropic": "https://www.blog.google/technology/ai/google-investment-anthropic/",
    "Amazon_Anthropic": "https://www.aboutamazon.com/news/aws/amazon-anthropic-ai-investment",
    "AMD_OpenAI_GPU": "https://ir.amd.com/news-releases/news-release-details/amd-openai-partnership",

    # 토큰 수요
    "OpenAI_Usage": "https://openai.com/blog/chatgpt",
    "AI_Token_Growth": "https://www.sequoiacap.com/article/ai-energy-usage/",

    # 전력/데이터센터
    "DC_Power_IEA": "https://www.iea.org/reports/electricity-2024",
    "Goldman_DC_Power": "https://www.goldmansachs.com/insights/articles/AI-poised-to-drive-160-increase-in-power-demand",

    # 시장 조사
    "IDC_GPU_Market": "https://www.idc.com/getdoc.jsp?containerId=prUS52540424",
    "Bloomberg_AI_Chart": "https://www.bloomberg.com/graphics/2025-ai-investment-chart/",
    "Sequoia_AI_Infra": "https://www.sequoiacap.com/article/ais-600b-question/",
    "HBM_Supply_Chain": "https://www.techinsights.com/blog/hbm-memory-ai-supply-chain",
}

# ============================================================
# 회사 투자/공급 관계 네트워크
# ============================================================
COMPANY_RELATIONSHIPS = [
    # (from, to, type, description_ko, value_str, source_url_key)
    ("NVIDIA",     "OpenAI",    "investment",      "NVIDIA, OpenAI에 최대 $1,000억 투자 합의",       "$100B",    "NVIDIA_OpenAI_Investment"),
    ("NVIDIA",     "Microsoft", "hardware_supply", "H100/B200 대량 공급 (데이터센터 매출 $150B/yr)", "~$20B/yr", "NVIDIA_DataCenter"),
    ("NVIDIA",     "AWS",       "hardware_supply", "AWS GPU 인스턴스 핵심 공급",                    "~$15B/yr", "NVIDIA_DataCenter"),
    ("NVIDIA",     "Google",    "hardware_supply", "GCP GPU 클러스터 공급",                         "~$10B/yr", "NVIDIA_DataCenter"),
    ("NVIDIA",     "xAI",       "hardware_supply", "Colossus 클러스터 10만개+ GPU 공급",            "~$5B",     "NVIDIA_DataCenter"),
    ("NVIDIA",     "Oracle",    "hardware_supply", "Oracle Cloud GPU 공급",                        "~$8B",     "NVIDIA_DataCenter"),
    ("NVIDIA",     "CoreWeave", "hardware_supply", "GPU 클라우드 핵심 인프라 공급",                 "~$12B",    "NVIDIA_DataCenter"),
    ("NVIDIA",     "Nscale",    "investment",      "NVIDIA Nscale 투자 참여",                       "미공개",    "NVIDIA_DataCenter"),
    ("NVIDIA",     "Nebius",    "investment",      "NVIDIA Nebius 투자 참여",                       "미공개",    "NVIDIA_DataCenter"),
    ("Microsoft",  "OpenAI",    "investment",      "OpenAI 누적 투자 $130억+, Azure 독점 공급",     "$13B+",    "Microsoft_OpenAI"),
    ("Microsoft",  "Mistral",   "investment",      "Mistral AI 투자 + Azure 파트너십",              "$16M",     "Microsoft_OpenAI"),
    ("Microsoft",  "Nebius",    "investment",      "Nebius AI 클라우드 투자",                       "미공개",    "Microsoft_CapEx"),
    ("OpenAI",     "Oracle",    "service",         "OpenAI-Oracle $300억 클라우드 계약",            "$30B",     "Amazon_CapEx"),
    ("OpenAI",     "CoreWeave", "service",         "OpenAI CoreWeave 클라우드 $115억 계약",         "$11.5B",   "OpenAI_Usage"),
    ("OpenAI",     "Figure AI", "vc",              "피지컬 AI 로봇 스타트업 투자",                  "$675M",    "OpenAI_Usage"),
    ("OpenAI",     "Anysphere", "vc",              "Cursor IDE (AI 코딩) 투자",                    "미공개",    "OpenAI_Usage"),
    ("OpenAI",     "Harvey AI", "vc",              "리걸 AI 스타트업 투자",                         "미공개",    "OpenAI_Usage"),
    ("AMD",        "OpenAI",    "hardware_supply", "AMD GPU 6GW 배포 합의, 주식 옵션 1.6억주",      "6GW GPU",  "AMD_OpenAI_GPU"),
    ("AMD",        "Microsoft", "hardware_supply", "Azure MI300X 공급",                            "~$3B",     "AMD_OpenAI_GPU"),
    ("Oracle",     "NVIDIA",    "hardware_supply", "Oracle, 수십억달러 규모 NVIDIA 칩 구매",        "수십 $B",   "NVIDIA_DataCenter"),
    ("Google",     "Anthropic", "investment",      "Google, Anthropic 최대 $20억 투자",            "$2B",      "Google_Anthropic"),
    ("Amazon",     "Anthropic", "investment",      "Amazon, Anthropic 최대 $40억 투자",            "$4B",      "Amazon_Anthropic"),
    ("Meta",       "NVIDIA",    "hardware_supply", "H100/B200 대규모 구매 ($65B CapEx의 핵심)",    "~$10B/yr", "Meta_CapEx"),
    ("Intel",      "Microsoft", "hardware_supply", "Gaudi3 Azure 공급",                            "미공개",    "NVIDIA_DataCenter"),
    ("SK Hynix",   "NVIDIA",    "hardware_supply", "HBM3e 50%+ 독점 공급, H200/B200 전용",        "독점적",    "SKHynix_HBM"),
    ("SK Hynix",   "AMD",       "hardware_supply", "MI300X HBM3 공급",                            "미공개",    "SKHynix_HBM"),
    ("Samsung",    "NVIDIA",    "hardware_supply", "HBM3 공급 (HBM3e 인증 진행 중)",              "미공개",    "HBM_Market_Size"),
    ("Micron",     "NVIDIA",    "hardware_supply", "HBM3e 공급 (10% 점유율)",                     "~10%",     "Micron_HBM"),
    ("TSMC",       "NVIDIA",    "hardware_supply", "4nm CoWoS 패키징 + 칩 제조 (독점)",           "독점",      "TSMC_CoWoS"),
    ("TSMC",       "AMD",       "hardware_supply", "5nm 칩 제조",                                 "미공개",    "TSMC_Capacity"),
    ("TSMC",       "Google",    "hardware_supply", "TPU v5 제조",                                 "미공개",    "TSMC_Capacity"),
    ("Broadcom",   "Google",    "hardware_supply", "TPU 네트워킹 칩 + AI ASIC 공동 개발",          "미공개",    "IDC_GPU_Market"),
    ("Broadcom",   "Meta",      "hardware_supply", "MTIA ASIC 파트너십",                          "미공개",    "IDC_GPU_Market"),
    ("Vertiv",     "Microsoft", "hardware_supply", "데이터센터 전력/냉각 인프라 공급",             "미공개",    "Goldman_DC_Power"),
    ("Vertiv",     "Google",    "hardware_supply", "DC 전력관리 시스템 공급",                     "미공개",    "Goldman_DC_Power"),
]

COMPANY_MARKET_CAP = {
    "NVIDIA": 4500, "Microsoft": 3900, "Google": 2200, "Amazon": 2100,
    "Meta": 1600, "AMD": 300, "Intel": 100, "Oracle": 500,
    "TSMC": 900, "SK Hynix": 100, "Samsung": 280, "Micron": 110,
    "OpenAI": 500, "Anthropic": 60, "xAI": 80,
    "CoreWeave": 35, "Mistral": 6, "Nebius": 5,
    "Anysphere": 10, "Harvey AI": 3, "Figure AI": 3,
    "Broadcom": 700, "Marvell": 80, "Arista": 150, "Nscale": 1,
    "Vertiv": 40, "Solidigm": 5,
}

RELATIONSHIP_COLORS = {
    "investment":      "#FF69B4",
    "hardware_supply": "#00CED1",
    "service":         "#4169E1",
    "vc":              "#32CD32",
    "partnership":     "#FFD700",
}

COMPANY_LAYER_COLORS = {
    "gpu_server":  "#E53E3E",
    "hbm":         "#3182CE",
    "cloud_dc":    "#38A169",
    "end_customer":"#805AD5",
    "ai_service":  "#805AD5",
    "packaging":   "#D69E2E",
    "foundry":     "#D69E2E",
    "networking":  "#DD6B20",
    "power":       "#718096",
    "dram":        "#3182CE",
    "ssd_storage": "#4299E1",
    "cpu":         "#E53E3E",
    "asic":        "#9F7AEA",
    "edge_ai":     "#48BB78",
    "sovereign_ai":"#9F7AEA",
}
