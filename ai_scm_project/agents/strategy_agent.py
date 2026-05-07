"""
Strategy / Investment Agent
- Maps bottleneck analysis to investment phases
- Generates company-level investment signals
- Analyzes risk factors
- Signal strength: Strong Buy / Buy / Hold / Watch
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# Signal logic: utilization thresholds -> signal
SIGNAL_MAP = {
    "critical": "Strong Buy",
    "high": "Buy",
    "medium": "Hold",
    "low": "Watch",
}

# Supplementary signals from seed data
SUPPLEMENTARY_SIGNALS = [
    {
        "company": "SK Hynix",
        "ticker": "000660.KS",
        "layer": "HBM",
        "signal": "Strong Buy",
        "thesis": "HBM3e dominant supplier (50% share), 95% utilization, 2.5x demand growth YoY, GB200 key beneficiary",
        "catalyst": "GB200 NVL72 rack ramp H2 2025; HBM4 qualification 2026",
        "risk": "Samsung HBM capacity catch-up; CoWoS yield risk; US export control escalation",
        "timeframe": "6-18 months",
        "phase": 2,
        "upside_pct": 40,
    },
    {
        "company": "Micron",
        "ticker": "MU",
        "layer": "HBM",
        "signal": "Buy",
        "thesis": "HBM3e market share gain 10% -> 20%+; CHIPS Act domestic fab beneficiary; NVIDIA supply diversification",
        "catalyst": "NVIDIA HBM3e dual-source approval; 1-beta node transition",
        "risk": "Execution risk; SK Hynix yield/performance gap",
        "timeframe": "12-24 months",
        "phase": 2,
        "upside_pct": 30,
    },
    {
        "company": "TSMC",
        "ticker": "TSM",
        "layer": "Packaging/Foundry",
        "signal": "Buy",
        "thesis": "CoWoS monopoly for AI packaging (92% util); N3/N2 pricing power; AI chips 20%+ of revenue",
        "catalyst": "CoWoS 50K->80K wpm expansion 2025; N2 ramp 2025",
        "risk": "Taiwan geopolitical risk; Intel Foundry Services competition; SMIC gap closing",
        "timeframe": "12-36 months",
        "phase": 2,
        "upside_pct": 25,
    },
    {
        "company": "Vertiv",
        "ticker": "VRT",
        "layer": "Power",
        "signal": "Buy",
        "thesis": "DC power infrastructure bottleneck; sold out through 2026; AI-driven thermal mgmt demand",
        "catalyst": "Hyperscaler DC buildout $500B+ 2026; liquid cooling adoption",
        "risk": "Execution risk at scale; margin pressure; new entrants (Eaton, Schneider)",
        "timeframe": "6-18 months",
        "phase": 3,
        "upside_pct": 35,
    },
    {
        "company": "GE Vernova",
        "ticker": "GEV",
        "layer": "Power",
        "signal": "Buy",
        "thesis": "Gas turbine + grid equipment; transformer shortage 30mo lead time; nuclear AI data center deals",
        "catalyst": "Hyperscaler nuclear/gas power deals; grid modernization IRA spending",
        "risk": "Regulatory/permitting; commodity input costs",
        "timeframe": "12-24 months",
        "phase": 3,
        "upside_pct": 30,
    },
    {
        "company": "Broadcom",
        "ticker": "AVGO",
        "layer": "Networking",
        "signal": "Buy",
        "thesis": "InfiniBand/Ethernet dominance; custom ASIC design wins at Google, Meta, Apple; 400G/800G cycle",
        "catalyst": "800G switch ramp 2025; hyperscaler custom ASIC revenue $10B+ by 2026",
        "risk": "NVIDIA NVLink competitive; high valuation; customer concentration",
        "timeframe": "12-24 months",
        "phase": 2,
        "upside_pct": 20,
    },
    {
        "company": "Marvell",
        "ticker": "MRVL",
        "layer": "Networking",
        "signal": "Buy",
        "thesis": "Custom ASIC/SerDes for AWS Trainium3 and Google TPU; optical interconnect opportunity",
        "catalyst": "AWS custom ASIC ramp; 1.6Tbps transceiver wins",
        "risk": "Broadcom direct competition; customer concentration (Amazon, Google)",
        "timeframe": "12-24 months",
        "phase": 2,
        "upside_pct": 35,
    },
    {
        "company": "NVIDIA",
        "ticker": "NVDA",
        "layer": "GPU",
        "signal": "Hold",
        "thesis": "Dominant platform (88% util) but Phase 1 largely priced; CUDA moat durable; Blackwell ramp key",
        "catalyst": "B200/GB200 full adoption; NIM software monetization; agentic AI workload growth",
        "risk": "Extreme valuation; custom ASIC displacement 20-30% by 2027; export controls",
        "timeframe": "24+ months for next valuation leg",
        "phase": 1,
        "upside_pct": 15,
    },
    {
        "company": "Eaton",
        "ticker": "ETN",
        "layer": "Power",
        "signal": "Buy",
        "thesis": "Electrical power management for data centers; UPS and PDU critical infrastructure",
        "catalyst": "DC power demand doubling 2024-2026; electrification mega-trend",
        "risk": "Valuation premium; slower revenue recognition vs bookings",
        "timeframe": "12-24 months",
        "phase": 3,
        "upside_pct": 20,
    },
    {
        "company": "Qualcomm",
        "ticker": "QCOM",
        "layer": "Edge AI",
        "signal": "Watch",
        "thesis": "On-device AI inference leader; Snapdragon X Elite for PC AI; automotive AI opportunity",
        "catalyst": "Windows AI PC upgrade cycle; edge LLM deployment wave 2026",
        "risk": "Smartphone exposure; Apple in-house silicon; Intel AI PC competition",
        "timeframe": "18-36 months",
        "phase": 4,
        "upside_pct": 25,
    },
]


def determine_phase_position(bottleneck_results):
    """Determine current investment cycle phase based on bottleneck."""
    if not bottleneck_results:
        return "Phase 2 (HBM)", 2

    primary = bottleneck_results.get("current_bottleneck", "HBM")
    next_b = bottleneck_results.get("next_bottleneck", "Power_DC")

    if primary in ["HBM", "CoWoS"]:
        phase = 2
        phase_name = "Phase 2 (HBM & Packaging)"
    elif primary in ["Power_DC"]:
        phase = 3
        phase_name = "Phase 3 (Power Infrastructure)"
    elif primary in ["GPU"]:
        phase = 1
        phase_name = "Phase 1 (GPU Compute)"
    elif primary in ["Edge_AI"]:
        phase = 4
        phase_name = "Phase 4 (Edge & Physical AI)"
    else:
        phase = 2
        phase_name = "Phase 2 (HBM & Packaging)"

    return phase_name, phase


def generate_signals_from_bottlenecks(bottleneck_results, mapping_results):
    """Generate investment signals based on bottleneck analysis."""
    signals = []

    if not bottleneck_results:
        return signals

    all_scores = bottleneck_results.get("all_scores", {})

    # Map bottleneck component to investment layer
    component_to_layer = {
        "HBM": "hbm",
        "CoWoS": "packaging",
        "GPU": "gpu_server",
        "Power_DC": "power",
        "Networking": "networking",
        "DRAM": "dram",
        "SSD": "ssd_storage",
        "Foundry_Advanced": "foundry",
        "ASIC": "asic",
        "Edge_AI": "edge_ai",
    }

    for component, score_data in all_scores.items():
        severity = score_data.get("severity", "low")
        signal = SIGNAL_MAP.get(severity, "Watch")
        layer = component_to_layer.get(component, "")

        if not layer or severity == "low":
            continue

        # Get companies in this layer
        layer_info = config.VALUE_CHAIN.get(layer, {})
        companies = layer_info.get("companies", [])[:3]  # top 3

        for company in companies:
            signals.append({
                "company": company,
                "layer": component,
                "signal": signal,
                "thesis": f"{component} at {score_data['utilization_pct']} utilization ({severity} bottleneck)",
                "catalyst": f"Resolution in ~{score_data.get('resolution_months', '?')} months",
                "risk": score_data.get("resolution_reason", ""),
                "timeframe": f"0-{score_data.get('resolution_months', 12)} months",
                "investment_window": score_data.get("investment_window", ""),
                "source": "bottleneck_analysis",
            })

    return signals


def analyze_key_themes(bottleneck_results, modeling_results):
    """Identify key investment themes."""
    themes = []

    # HBM upcycle
    if bottleneck_results:
        hbm_util = bottleneck_results.get("all_scores", {}).get("HBM", {}).get("utilization", 0)
        if hbm_util > 0.85:
            themes.append("Memory Upcycle (HBM shortage persists through 2025)")

    # Power infrastructure
    power_util = bottleneck_results.get("all_scores", {}).get("Power_DC", {}).get("utilization", 0) if bottleneck_results else 0
    if power_util > 0.70:
        themes.append("Power Infrastructure Scarcity (transformer/grid bottleneck)")

    # Sovereign AI
    themes.append("Sovereign AI Wave (UAE, Saudi, EU $150B+ government investment)")

    # Custom silicon
    themes.append("Custom Silicon Efficiency Race (Google TPU, AWS Trainium, MSFT Maia)")

    # Physical AI
    themes.append("Physical AI / Robotics (Inference at edge 2026-2027)")

    # CapEx super-cycle
    themes.append("Hyperscaler CapEx Super-Cycle ($500B+ in 2026)")

    return themes


def analyze_risks():
    """Analyze key risk factors."""
    return [
        {
            "risk": "Geopolitical: Taiwan/TSMC Risk",
            "severity": "critical",
            "description": "TSMC produces 90%+ of AI chips; Taiwan strait tension = systemic risk",
            "mitigation": "TSMC Arizona/Japan fabs; Intel Foundry; diversification push",
        },
        {
            "risk": "Export Controls: US-China AI chip restrictions",
            "severity": "high",
            "description": "H800/H20 restrictions limit NVIDIA China revenue; future controls possible",
            "mitigation": "NVIDIA US-legal compliant chips; AMD compliance; domestic Chinese ASICs",
        },
        {
            "risk": "Demand Disappointment: AI ROI not materializing",
            "severity": "high",
            "description": "If enterprise AI ROI lags, hyperscaler CapEx pullback possible",
            "mitigation": "Diversified AI revenue streams; agent/agentic AI driving new demand",
        },
        {
            "risk": "Technology: LLM efficiency gains reduce hardware demand",
            "severity": "medium",
            "description": "Techniques like MoE, quantization, speculative decoding reduce GPU requirements",
            "mitigation": "Jevons paradox: efficiency -> more usage -> net demand up",
        },
        {
            "risk": "Competition: Samsung HBM3e qualification",
            "severity": "medium",
            "description": "If Samsung qualifies for GB200, SK Hynix market share at risk",
            "mitigation": "SK Hynix technology lead; HBM4 roadmap advantage",
        },
        {
            "risk": "Custom ASIC displacement of commodity GPU",
            "severity": "medium",
            "description": "20-30% of hyperscaler AI workloads shifting to custom ASICs by 2027",
            "mitigation": "NVIDIA software moat (CUDA); diversified to ASIC players (Broadcom, Marvell)",
        },
        {
            "risk": "Power: Regulatory/permitting delays",
            "severity": "medium",
            "description": "Grid interconnection 3-5 years; NIMBYism delays DC approvals",
            "mitigation": "Nuclear deals; distributed DC strategy; efficiency improvements",
        },
    ]


def run(bottleneck_results=None, modeling_results=None, mapping_results=None, market_state=None):
    """Run the strategy agent and generate investment signals."""
    print("[StrategyAgent] Generating investment strategy and signals...")

    # Determine phase position
    phase_name, phase_number = determine_phase_position(bottleneck_results)

    # Generate signals from bottleneck analysis
    derived_signals = generate_signals_from_bottlenecks(bottleneck_results, mapping_results)

    # Use supplementary curated signals
    all_signals = SUPPLEMENTARY_SIGNALS[:]  # start with curated signals

    # Merge derived signals for components not already covered
    covered_layers = {s["layer"] for s in all_signals}
    for sig in derived_signals:
        if sig["layer"] not in covered_layers:
            all_signals.append(sig)

    # Key themes
    themes = analyze_key_themes(bottleneck_results, modeling_results)

    # Risk analysis
    risks = analyze_risks()

    # Phase roadmap from config
    phase_roadmap = []
    for phase_num, phase_data in config.INVESTMENT_PHASES.items():
        phase_roadmap.append({
            "phase": phase_num,
            "focus": phase_data["focus"],
            "timeframe": phase_data["timeframe"],
            "status": phase_data["status"],
            "key_players": phase_data["key_players"],
            "description": phase_data["description"],
            "is_current": phase_num == phase_number,
        })

    # Strong Buy and Buy signals summary
    strong_buys = [s["company"] for s in all_signals if s["signal"] == "Strong Buy"]
    buys = [s["company"] for s in all_signals if s["signal"] == "Buy"]

    result = {
        "phase_position": phase_name,
        "current_phase_number": phase_number,
        "investment_signals": all_signals,
        "key_themes": themes,
        "risk_factors": risks,
        "phase_roadmap": phase_roadmap,
        "strong_buy_companies": strong_buys,
        "buy_companies": buys,
        "signal_summary": {
            "Strong Buy": len(strong_buys),
            "Buy": len(buys),
            "Hold": len([s for s in all_signals if s["signal"] == "Hold"]),
            "Watch": len([s for s in all_signals if s["signal"] == "Watch"]),
        },
        "portfolio_thesis": (
            f"Currently in {phase_name}. "
            f"HBM bottleneck drives memory upcycle; "
            f"Power infrastructure emerging as next constraint. "
            f"Sovereign AI provides 15-20% demand upside. "
            f"Key risks: Taiwan geopolitical, export controls, AI ROI."
        ),
    }

    print(f"  [StrategyAgent] Phase: {phase_name}")
    print(f"  [StrategyAgent] Signals: {len(all_signals)} total")
    print(f"  [StrategyAgent] Strong Buy: {len(strong_buys)}, Buy: {len(buys)}")

    return result


if __name__ == "__main__":
    result = run()
    print(f"\nPhase: {result['phase_position']}")
    print(f"\nKey themes: {result['key_themes']}")
    print(f"\nSignal summary: {result['signal_summary']}")
    print(f"\nStrong Buy: {result['strong_buy_companies']}")
    print(f"Buy: {result['buy_companies']}")
