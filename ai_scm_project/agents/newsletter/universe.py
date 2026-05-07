"""
AI SCM 커버리지 유니버스 — 전 레이어 30개+ 기업
"""

UNIVERSE = {
    # ── GPU / Compute ──────────────────────────────────────────
    "GPU": [
        {"ticker": "NVDA",      "name": "NVIDIA",          "exchange": "US", "role": "GPU 설계, CUDA 생태계, NVLink"},
        {"ticker": "AMD",       "name": "AMD",             "exchange": "US", "role": "MI300X GPU, ROCm 생태계"},
        {"ticker": "INTC",      "name": "Intel",           "exchange": "US", "role": "Gaudi3 AI 가속기, CPU"},
    ],
    # ── HBM / DRAM ────────────────────────────────────────────
    "HBM": [
        {"ticker": "000660.KS", "name": "SK Hynix",        "exchange": "KR", "role": "HBM3e 50% 독점, HBM4 로드맵"},
        {"ticker": "005930.KS", "name": "Samsung",         "exchange": "KR", "role": "HBM3e 재인증, DRAM/NAND"},
        {"ticker": "MU",        "name": "Micron",          "exchange": "US", "role": "HBM3e 12%, CHIPS Act 수혜"},
    ],
    # ── Foundry / Packaging ───────────────────────────────────
    "Packaging": [
        {"ticker": "TSM",       "name": "TSMC",            "exchange": "US", "role": "CoWoS 독점, N3/N4 파운드리"},
        {"ticker": "ASX",       "name": "ASE Technology",  "exchange": "US", "role": "OSAT 1위, 일반 패키징"},
        {"ticker": "AMKR",      "name": "Amkor",           "exchange": "US", "role": "OSAT 2위, 어드밴스드 패키징"},
    ],
    # ── Networking ────────────────────────────────────────────
    "Networking": [
        {"ticker": "AVGO",      "name": "Broadcom",        "exchange": "US", "role": "커스텀 AI ASIC, 이더넷 스위치"},
        {"ticker": "MRVL",      "name": "Marvell",         "exchange": "US", "role": "AI NIC, 광트랜시버 DSP"},
        {"ticker": "ANET",      "name": "Arista Networks", "exchange": "US", "role": "800G AI 이더넷 스위치"},
        {"ticker": "CSCO",      "name": "Cisco",           "exchange": "US", "role": "네트워크 인프라, UEC"},
    ],
    # ── Power / DC Infrastructure ─────────────────────────────
    "Power": [
        {"ticker": "VRT",       "name": "Vertiv",          "exchange": "US", "role": "UPS, 액냉각, CDU"},
        {"ticker": "GEV",       "name": "GE Vernova",      "exchange": "US", "role": "변압기, 발전, 그리드"},
        {"ticker": "ETN",       "name": "Eaton",           "exchange": "US", "role": "PDU, 전력관리"},
        {"ticker": "SMCI",      "name": "Super Micro",     "exchange": "US", "role": "AI 서버, 랙 통합"},
    ],
    # ── Hyperscaler ───────────────────────────────────────────
    "Hyperscaler": [
        {"ticker": "MSFT",      "name": "Microsoft",       "exchange": "US", "role": "Azure AI, OpenAI 파트너"},
        {"ticker": "AMZN",      "name": "Amazon",          "exchange": "US", "role": "AWS, Trainium2, Anthropic"},
        {"ticker": "GOOGL",     "name": "Google",          "exchange": "US", "role": "GCP, TPUv5, Anthropic"},
        {"ticker": "META",      "name": "Meta",            "exchange": "US", "role": "Llama, MTIA ASIC"},
        {"ticker": "ORCL",      "name": "Oracle",          "exchange": "US", "role": "OCI GPU 클라우드"},
    ],
    # ── AI Model / Infra Cloud ────────────────────────────────
    "AI_Cloud": [
        {"ticker": "CRWV",      "name": "CoreWeave",       "exchange": "US", "role": "GPU 클라우드 스타트업"},
        {"ticker": "DLR",       "name": "Digital Realty",  "exchange": "US", "role": "DC REIT, 코로케이션"},
        {"ticker": "EQIX",      "name": "Equinix",         "exchange": "US", "role": "DC REIT, 글로벌 코로케이션"},
    ],
    # ── Edge AI / ASIC ────────────────────────────────────────
    "Edge_AI": [
        {"ticker": "QCOM",      "name": "Qualcomm",        "exchange": "US", "role": "스냅드래곤 온디바이스 AI"},
        {"ticker": "ARM",       "name": "Arm Holdings",    "exchange": "US", "role": "CPU IP, AI NPU 설계"},
        {"ticker": "AMAT",      "name": "Applied Materials","exchange": "US", "role": "반도체 장비, 식각/증착"},
        {"ticker": "ASML",      "name": "ASML",            "exchange": "US", "role": "EUV 리소그래피 독점"},
        {"ticker": "LRCX",      "name": "Lam Research",    "exchange": "US", "role": "식각 장비, HBM TSV"},
        {"ticker": "KLAC",      "name": "KLA Corp",        "exchange": "US", "role": "공정 제어, 계측 장비"},
    ],
}

# 전체 플랫 리스트
ALL_TICKERS = [(t["ticker"], t["name"], layer) for layer, tickers in UNIVERSE.items() for t in tickers]

# 레이어 색상
LAYER_COLOR = {
    "GPU":         "#e53e3e",
    "HBM":         "#3182ce",
    "Packaging":   "#d69e2e",
    "Networking":  "#dd6b20",
    "Power":       "#718096",
    "Hyperscaler": "#38a169",
    "AI_Cloud":    "#805ad5",
    "Edge_AI":     "#319795",
}
