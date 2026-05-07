"""
Supply Chain Mapping Agent
- Builds knowledge graph from VALUE_CHAIN config
- Maps companies to supply chain layers
- Analyzes upstream/downstream dependencies
- Tier classification: Tier-1 (direct), Tier-2 (materials/equipment), Tier-3 (energy/infra)
- Investment network graph (Bloomberg style)
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ============================================================
# 회사 투자 관계 네트워크 데이터
# ============================================================
COMPANY_RELATIONSHIPS = [
    # (from, to, type, description, value_str)
    # type: investment / hardware_supply / service / vc / partnership

    # NVIDIA 관계
    ("NVIDIA", "OpenAI", "investment", "NVIDIA, OpenAI에 최대 $1,000억 투자 합의", "$100B"),
    ("NVIDIA", "Microsoft", "hardware_supply", "H100/B200 대량 공급", "~$20B/yr"),
    ("NVIDIA", "AWS", "hardware_supply", "AWS GPU 인스턴스 핵심 공급", "~$15B/yr"),
    ("NVIDIA", "Google", "hardware_supply", "GCP GPU 클러스터 공급", "~$10B/yr"),
    ("NVIDIA", "xAI", "hardware_supply", "Colossus 클러스터 10만개+ 공급", "~$5B"),
    ("NVIDIA", "Oracle", "hardware_supply", "Oracle Cloud GPU 공급", "~$8B"),
    ("NVIDIA", "CoreWeave", "hardware_supply", "GPU 클라우드 핵심 인프라", "~$12B"),

    # Microsoft 관계
    ("Microsoft", "OpenAI", "investment", "OpenAI 누적 투자 $130억+", "$13B+"),
    ("Microsoft", "NVIDIA", "investment", "NVIDIA 지분 보유", "지분"),
    ("Microsoft", "Mistral", "investment", "Mistral AI Series A 투자", "$16M"),

    # OpenAI 관계
    ("OpenAI", "Oracle", "service", "OpenAI-Oracle $300억 클라우드 계약", "$30B"),
    ("OpenAI", "CoreWeave", "service", "OpenAI CoreWeave 클라우드 $115억 계약", "$11.5B"),
    ("OpenAI", "Ambience Healthcare", "vc", "헬스케어 AI 투자", "미공개"),
    ("OpenAI", "Harvey AI", "vc", "리걸 AI 투자", "미공개"),
    ("OpenAI", "Anysphere", "vc", "Cursor IDE 투자", "미공개"),
    ("OpenAI", "Figure AI", "vc", "피지컬 AI 로봇 투자", "$675M"),

    # AMD 관계
    ("AMD", "OpenAI", "hardware_supply", "AMD GPU 6 gigawatt 배포 합의, 주식 1.6억주 옵션", "6GW"),
    ("AMD", "Microsoft", "hardware_supply", "Azure MI300X 공급", "~$3B"),

    # Oracle 관계
    ("Oracle", "NVIDIA", "hardware_supply", "수십억달러 규모 NVIDIA 칩 구매", "수십 $B"),
    ("Oracle", "OpenAI", "service", "클라우드 서비스 제공", "$30B"),

    # Google 관계
    ("Google", "Anthropic", "investment", "Google Anthropic 최대 $20억 투자", "$2B"),
    ("Google", "xAI", "service", "Google Cloud xAI 파트너십", "미공개"),
    ("Google", "Mistral", "investment", "Mistral 투자 참여", "미공개"),

    # Amazon 관계
    ("Amazon", "Anthropic", "investment", "Amazon Anthropic 최대 $40억 투자", "$4B"),
    ("Amazon", "Mistral", "investment", "Mistral 투자 참여", "미공개"),

    # Meta 관계
    ("Meta", "NVIDIA", "hardware_supply", "H100/B200 대규모 구매", "~$10B/yr"),
    ("Meta", "AMD", "hardware_supply", "AI 인프라 다양화", "미공개"),

    # Intel 관계
    ("Intel", "Microsoft", "hardware_supply", "Gaudi3 Azure 공급", "미공개"),
    ("Intel", "AWS", "hardware_supply", "Gaudi3 AWS 공급", "미공개"),

    # xAI 관계
    ("xAI", "NVIDIA", "hardware_supply", "Colossus 100K GPU 클러스터", "~$5B"),
    ("xAI", "CoreWeave", "service", "추가 클라우드 인프라", "미공개"),

    # SK Hynix 관계
    ("SK Hynix", "NVIDIA", "hardware_supply", "HBM3e 50%+ 공급, H200/B200 전용 공급", "독점적"),
    ("SK Hynix", "AMD", "hardware_supply", "MI300X HBM3 공급", "미공개"),

    # Samsung 관계
    ("Samsung", "NVIDIA", "hardware_supply", "HBM3 공급 (HBM3e 인증 중)", "미공개"),
    ("Samsung", "AMD", "hardware_supply", "HBM3 공급", "미공개"),

    # TSMC 관계
    ("TSMC", "NVIDIA", "hardware_supply", "4nm CoWoS 패키징, 칩 제조", "독점"),
    ("TSMC", "AMD", "hardware_supply", "5nm 칩 제조", "미공개"),
    ("TSMC", "Apple", "hardware_supply", "M-시리즈 칩 제조", "미공개"),
    ("TSMC", "Google", "hardware_supply", "TPU 제조", "미공개"),

    # Nebius 관계
    ("Nebius", "NVIDIA", "hardware_supply", "GPU 클라우드 인프라", "미공개"),
    ("Microsoft", "Nebius", "investment", "Microsoft Nebius 투자", "미공개"),

    # Nscale 관계
    ("NVIDIA", "Nscale", "investment", "NVIDIA Nscale 투자", "미공개"),

    # Mistral 관계
    ("Microsoft", "Mistral", "investment", "Azure 파트너십 + 투자", "$16M"),
    ("Google", "Mistral", "investment", "투자 참여", "미공개"),
    ("Amazon", "Mistral", "investment", "투자 참여", "미공개"),
]

COMPANY_MARKET_CAP = {
    "NVIDIA": 4500, "Microsoft": 3900, "Google": 2200, "Amazon": 2100,
    "Meta": 1600, "AMD": 300, "Intel": 100, "Oracle": 500,
    "TSMC": 900, "SK Hynix": 100, "Samsung": 280,
    "OpenAI": 500, "Anthropic": 60, "xAI": 80,
    "CoreWeave": 35, "Mistral": 6, "Nebius": 5,
    "Anysphere": 10, "Harvey AI": 3, "Ambience Healthcare": 2,
    "Figure AI": 3, "Nscale": 1, "Micron": 110,
    "Broadcom": 700, "Marvell": 80, "Arista": 150,
    "Vertiv": 40, "Solidigm": 5, "Apple": 3500,
    "AWS": 500,
}

COMPANY_COLORS = {
    "gpu_server": "#E53E3E",       # 빨강 - GPU
    "hbm": "#3182CE",              # 파랑 - 메모리
    "cloud_dc": "#38A169",         # 초록 - 클라우드
    "end_customer": "#805AD5",     # 보라 - AI 서비스
    "ai_service": "#805AD5",
    "packaging": "#D69E2E",        # 노랑 - 패키징
    "foundry": "#D69E2E",
    "networking": "#DD6B20",       # 주황 - 네트워크
    "power": "#718096",            # 회색 - 전력
    "dram": "#3182CE",
    "ssd_storage": "#4299E1",
    "cpu": "#E53E3E",
    "asic": "#E53E3E",
    "edge_ai": "#48BB78",
    "sovereign_ai": "#9F7AEA",
}

RELATIONSHIP_COLORS = {
    "investment": "#FF69B4",       # 핑크 - 투자
    "hardware_supply": "#00CED1",  # 청록 - 하드웨어 공급
    "service": "#4169E1",          # 파랑 - 서비스
    "vc": "#32CD32",               # 초록 - VC
    "partnership": "#FFD700",      # 금색 - 파트너십
}


# Layer adjacency: upstream dependencies
LAYER_UPSTREAM = {
    "end_customer":  ["ai_service", "cloud_dc"],
    "ai_service":    ["cloud_dc", "gpu_server"],
    "cloud_dc":      ["gpu_server", "networking", "power", "ssd_storage", "dram"],
    "gpu_server":    ["hbm", "packaging", "foundry", "networking"],
    "asic":          ["foundry", "packaging", "hbm"],
    "hbm":           ["packaging", "foundry"],
    "dram":          ["foundry"],
    "ssd_storage":   ["foundry"],
    "cpu":           ["foundry"],
    "networking":    ["foundry"],
    "packaging":     ["foundry"],
    "power":         [],
    "foundry":       [],
    "edge_ai":       ["foundry", "packaging"],
    "sovereign_ai":  ["cloud_dc", "gpu_server"],
}

# Tier classification by layer
LAYER_TIER = {
    "end_customer":  1,
    "ai_service":    1,
    "cloud_dc":      1,
    "gpu_server":    1,
    "asic":          1,
    "hbm":           1,
    "dram":          1,
    "ssd_storage":   1,
    "cpu":           1,
    "networking":    1,
    "packaging":     2,
    "power":         2,
    "foundry":       2,
    "edge_ai":       1,
    "sovereign_ai":  3,
}

# Key company to layer mappings (explicit)
COMPANY_LAYER_MAP = {
    "NVIDIA": "gpu_server",
    "AMD": "gpu_server",
    "Intel Gaudi": "gpu_server",
    "SK Hynix": "hbm",
    "Samsung": "hbm",  # also DRAM, SSD, Foundry
    "Micron": "hbm",   # also DRAM
    "TSMC": "foundry",
    "TSMC CoWoS": "packaging",
    "ASE": "packaging",
    "Amkor": "packaging",
    "Microsoft Azure": "cloud_dc",
    "AWS": "cloud_dc",
    "Google Cloud": "cloud_dc",
    "Oracle Cloud": "cloud_dc",
    "CoreWeave": "cloud_dc",
    "OpenAI": "end_customer",
    "Anthropic": "end_customer",
    "Google DeepMind": "end_customer",
    "Meta AI": "end_customer",
    "xAI": "end_customer",
    "Broadcom": "networking",
    "Marvell": "networking",
    "Arista": "networking",
    "Vertiv": "power",
    "Eaton": "power",
    "Schneider Electric": "power",
    "GE Vernova": "power",
    "ABB": "power",
    "Solidigm": "ssd_storage",
    "Samsung SSD": "ssd_storage",
    "Kioxia": "ssd_storage",
    "Intel": "cpu",
    "Qualcomm": "edge_ai",
    "Apple": "edge_ai",
    "Google TPU": "asic",
    "AWS Trainium": "asic",
    "Microsoft Maia": "asic",
    "Meta MTIA": "asic",
}

# Key upstream dependencies per company
COMPANY_UPSTREAM = {
    "NVIDIA": ["TSMC", "SK Hynix", "Broadcom", "TSMC CoWoS"],
    "AMD": ["TSMC", "SK Hynix", "Samsung", "TSMC CoWoS"],
    "SK Hynix": ["TSMC CoWoS", "TSMC"],
    "Samsung": ["Samsung Foundry", "TSMC CoWoS"],
    "Micron": ["TSMC CoWoS", "TSMC"],
    "TSMC": [],
    "TSMC CoWoS": ["TSMC"],
    "Microsoft Azure": ["NVIDIA", "AMD", "Vertiv", "Broadcom"],
    "AWS": ["NVIDIA", "AMD", "Vertiv", "Broadcom", "AWS Trainium"],
    "Google Cloud": ["NVIDIA", "AMD", "Google TPU", "Vertiv", "Broadcom"],
    "Broadcom": ["TSMC"],
    "Marvell": ["TSMC"],
    "Vertiv": [],
    "Schneider Electric": [],
    "OpenAI": ["Microsoft Azure"],
    "Anthropic": ["AWS", "Google Cloud"],
    "Meta AI": ["AWS", "Google Cloud", "NVIDIA"],
    "Google DeepMind": ["Google Cloud", "Google TPU"],
    "Qualcomm": ["TSMC", "Samsung Foundry"],
    "Intel": ["Intel Foundry", "TSMC"],
}

# Key downstream customers per company
COMPANY_DOWNSTREAM = {
    "NVIDIA": ["Microsoft Azure", "AWS", "Google Cloud", "CoreWeave", "xAI"],
    "AMD": ["Microsoft Azure", "AWS", "Google Cloud"],
    "SK Hynix": ["NVIDIA", "AMD", "Google TPU"],
    "Samsung": ["NVIDIA", "AMD", "Various"],
    "Micron": ["NVIDIA", "AMD", "Various"],
    "TSMC": ["NVIDIA", "AMD", "Apple", "Broadcom", "Marvell"],
    "TSMC CoWoS": ["NVIDIA", "AMD", "SK Hynix", "Micron"],
    "Microsoft Azure": ["OpenAI", "Enterprise customers"],
    "AWS": ["Anthropic", "Enterprise customers"],
    "Google Cloud": ["Google DeepMind", "Enterprise customers"],
    "Broadcom": ["Microsoft Azure", "AWS", "Google Cloud", "Meta"],
    "Marvell": ["AWS", "Google Cloud", "Microsoft Azure"],
    "Vertiv": ["Microsoft Azure", "AWS", "Google Cloud", "Meta"],
}


def build_company_graph():
    """Build complete company-to-supply-chain knowledge graph."""
    graph = {}

    # Start with VALUE_CHAIN definition
    for layer_name, layer_data in config.VALUE_CHAIN.items():
        tier = LAYER_TIER.get(layer_name, 1)
        for company in layer_data["companies"]:
            # Determine upstream/downstream
            upstream = COMPANY_UPSTREAM.get(company, [])
            downstream = COMPANY_DOWNSTREAM.get(company, [])

            # If not explicitly mapped, use layer adjacency
            if not upstream:
                upstream_layers = LAYER_UPSTREAM.get(layer_name, [])
                for ul in upstream_layers:
                    if ul in config.VALUE_CHAIN:
                        upstream.extend(config.VALUE_CHAIN[ul]["companies"][:2])

            graph[company] = {
                "layer": layer_name,
                "tier": tier,
                "upstream": list(set(upstream)),
                "downstream": list(set(downstream)),
                "bottleneck_risk": layer_data["bottleneck_risk"],
                "description": layer_data.get("description", ""),
            }

    return graph


def get_bottleneck_companies(graph):
    """Get companies in critical/high bottleneck layers."""
    critical = []
    high = []

    for company, data in graph.items():
        risk = data["bottleneck_risk"]
        if risk == "critical":
            critical.append(company)
        elif risk == "high":
            high.append(company)

    return {"critical": critical, "high": high}


def get_layer_summary(graph):
    """Summarize companies per layer."""
    layers = {}
    for company, data in graph.items():
        layer = data["layer"]
        if layer not in layers:
            layers[layer] = {
                "companies": [],
                "bottleneck_risk": data["bottleneck_risk"],
                "tier": data["tier"],
            }
        layers[layer]["companies"].append(company)
    return layers


def build_network_graph():
    """Bloomberg 스타일 회사 투자관계 네트워크 그래프 생성."""

    # ── 노드 집합 구성 (관계에 등장하는 모든 회사) ──────────────────────
    company_set = set()
    for rel in COMPANY_RELATIONSHIPS:
        company_set.add(rel[0])
        company_set.add(rel[1])

    # 회사별 레이어 추론 (COMPANY_LAYER_MAP 우선, 없으면 heuristic)
    _extra_layer = {
        "Microsoft": "cloud_dc",
        "Google":    "cloud_dc",
        "Amazon":    "cloud_dc",
        "AWS":       "cloud_dc",
        "Oracle":    "cloud_dc",
        "CoreWeave": "cloud_dc",
        "Nebius":    "cloud_dc",
        "Nscale":    "cloud_dc",
        "OpenAI":    "end_customer",
        "Anthropic": "end_customer",
        "xAI":       "end_customer",
        "Meta":      "end_customer",
        "Apple":     "edge_ai",
        "Mistral":   "ai_service",
        "Anysphere": "ai_service",
        "Harvey AI": "ai_service",
        "Ambience Healthcare": "ai_service",
        "Figure AI": "edge_ai",
        "NVIDIA":    "gpu_server",
        "AMD":       "gpu_server",
        "Intel":     "cpu",
        "TSMC":      "foundry",
        "SK Hynix":  "hbm",
        "Samsung":   "hbm",
        "Micron":    "hbm",
        "Broadcom":  "networking",
        "Marvell":   "networking",
        "Arista":    "networking",
        "Vertiv":    "power",
        "Solidigm":  "ssd_storage",
    }

    def _get_layer(company):
        if company in COMPANY_LAYER_MAP:
            return COMPANY_LAYER_MAP[company]
        return _extra_layer.get(company, "end_customer")

    # ── log-scale 노드 크기 계산 ─────────────────────────────────────────
    mc_values = [COMPANY_MARKET_CAP.get(c, 1) for c in company_set]
    log_min = math.log(max(min(mc_values), 1))
    log_max = math.log(max(mc_values) + 1)
    size_min, size_max = 10, 80

    def _node_size(company):
        mc = COMPANY_MARKET_CAP.get(company, 1)
        if log_max == log_min:
            return (size_min + size_max) / 2
        ratio = (math.log(max(mc, 1)) - log_min) / (log_max - log_min)
        return round(size_min + ratio * (size_max - size_min), 1)

    # ── 노드 목록 생성 ───────────────────────────────────────────────────
    nodes = []
    for company in sorted(company_set):
        layer = _get_layer(company)
        tier = LAYER_TIER.get(layer, 1)
        nodes.append({
            "id":           company,
            "label":        company,
            "market_cap_b": COMPANY_MARKET_CAP.get(company, 1),
            "layer":        layer,
            "color":        COMPANY_COLORS.get(layer, "#888888"),
            "size":         _node_size(company),
            "tier":         tier,
        })

    # ── 엣지 목록 생성 (중복 제거) ───────────────────────────────────────
    edges = []
    seen_edges = set()
    for rel in COMPANY_RELATIONSHIPS:
        src, tgt, rtype = rel[0], rel[1], rel[2]
        desc    = rel[3] if len(rel) > 3 else ""
        value   = rel[4] if len(rel) > 4 else "미공개"
        url_key = rel[5] if len(rel) > 5 else ""
        key = (src, tgt, rtype)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        edges.append({
            "source":      src,
            "target":      tgt,
            "type":        rtype,
            "color":       RELATIONSHIP_COLORS.get(rtype, "#888888"),
            "description": desc,
            "value":       value,
            "source_url":  config.REFERENCE_URLS.get(url_key, ""),
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "legend": {
            "node_colors": COMPANY_COLORS,
            "edge_colors": RELATIONSHIP_COLORS,
        },
    }


def run(market_state=None):
    """Run the mapping agent and return supply chain graph."""
    print("[MappingAgent] 공급망 지식 그래프 구축 중...")

    graph = build_company_graph()
    bottlenecks = get_bottleneck_companies(graph)
    layer_summary = get_layer_summary(graph)
    network_graph = build_network_graph()

    # company_map: {company_name: {layer, tier}} — DB agent 및 Word agent용
    company_map = {
        name: {"layer": data.get("layer", ""), "tier": data.get("tier", 0)}
        for name, data in graph.items()
    }

    result = {
        "company_graph": graph,
        "company_map": company_map,
        "bottleneck_companies": bottlenecks,
        "layer_summary": layer_summary,
        "total_companies": len(graph),
        "total_layers": len(layer_summary),
        "layer_order": [
            "end_customer", "ai_service", "cloud_dc", "gpu_server", "asic",
            "hbm", "dram", "ssd_storage", "cpu", "networking",
            "packaging", "power", "foundry", "edge_ai", "sovereign_ai"
        ],
        "network_graph": network_graph,
    }

    print(f"  [MappingAgent] {len(graph)}개 회사 × {len(layer_summary)}개 레이어 매핑 완료")
    print(f"  [MappingAgent] Critical 병목 회사: {len(bottlenecks['critical'])}개")
    print(f"  [MappingAgent] High risk 회사: {len(bottlenecks['high'])}개")
    print(f"  [MappingAgent] 투자 네트워크: 노드 {len(network_graph['nodes'])}개, 엣지 {len(network_graph['edges'])}개")

    return result


if __name__ == "__main__":
    result = run()
    # network_graph 는 크므로 요약만 출력
    summary = {k: v for k, v in result.items() if k != "company_graph"}
    summary["network_graph"] = {
        "nodes_count": len(result["network_graph"]["nodes"]),
        "edges_count": len(result["network_graph"]["edges"]),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
