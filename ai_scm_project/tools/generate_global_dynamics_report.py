"""
Generate an Oxford-style AI supply-chain dynamics report.

The report is intentionally formula-first: equations, variables, units,
evidence quality, and confidence appear before scenario narratives.
"""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs" / "reports"

COMPANY_EXPOSURE = {
    "AI demand owners": {
        "companies": "OpenAI, Anthropic, Google DeepMind, Meta AI, xAI",
        "model_variable": "tokens_per_day",
        "transmission": "End-user and model-training demand expands token volume and raises accelerator utilization demand.",
    },
    "Cloud procurement": {
        "companies": "Microsoft Azure, AWS, Google Cloud, Oracle Cloud, CoreWeave",
        "model_variable": "total_capex_usd, accelerators_procured",
        "transmission": "Cloud CapEx converts expected AI demand into forward accelerator procurement before utilization fully materializes.",
    },
    "Accelerators": {
        "companies": "NVIDIA, AMD, Intel Gaudi; internal ASICs: Google TPU, AWS Trainium, Microsoft Maia, Meta MTIA",
        "model_variable": "accelerator_demand, accelerator_supply",
        "transmission": "Accelerator availability sets the starting point for HBM, CoWoS, power, and networking demand.",
    },
    "HBM": {
        "companies": "SK Hynix, Samsung, Micron",
        "model_variable": "hbm_demand_pb, hbm_supply_pb, hbm_gap",
        "transmission": "HBM content per accelerator converts GPU demand into memory bit and stack allocation pressure.",
    },
    "Advanced packaging / foundry": {
        "companies": "TSMC CoWoS, TSMC, ASE, Amkor, Samsung Foundry",
        "model_variable": "cowos_demand_wpm, cowos_supply_wpm, cowos_gap",
        "transmission": "Advanced package slots and foundry flow determine how many high-end AI accelerators can ship.",
    },
    "Power infrastructure": {
        "companies": "Vertiv, Eaton, Schneider Electric, GE Vernova, ABB",
        "model_variable": "power_demand_gw, power_supply_gw, power_gap",
        "transmission": "Power and cooling determine whether purchased accelerators can be energized and deployed.",
    },
    "Networking": {
        "companies": "Broadcom, Marvell, Arista, Cisco, Mellanox/NVIDIA",
        "model_variable": "network_demand_tbps, network_supply_tbps, network_gap",
        "transmission": "Scale-up and scale-out cluster fabric demand rises with accelerator count and cluster complexity.",
    },
    "Storage": {
        "companies": "Solidigm, Samsung SSD, Kioxia, WD/SanDisk, Seagate",
        "model_variable": "storage_demand_pb_per_day",
        "transmission": "Agentic and RAG workloads create retrieval, context, and storage-flow pressure.",
    },
}


def load_json(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def pct(value: float) -> str:
    return f"{value:.0%}"


def scenario_table(dynamics: dict) -> str:
    rows = [
        "| Scenario | Year | Limiting Layer | Fulfillment | Unserved Accels | Accelerator Gap | HBM Gap | CoWoS Gap | Power Gap | Network Gap |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in ["bear", "base", "bull"]:
        for year in ["2026", "2027", "2028"]:
            s = dynamics["scenarios"][scenario][year]
            dep = s["deployment"]
            layers = s["layers"]
            rows.append(
                "| {scenario} | {year} | {limit} | {fulfill} | {unserved:,} | {accel:.2f}x | {hbm:.2f}x | {cowos:.2f}x | {power:.2f}x | {network:.2f}x |".format(
                    scenario=scenario,
                    year=year,
                    limit=dep["limiting_layer"],
                    fulfill=pct(dep["fulfillment_rate"]),
                    unserved=dep["unserved_accelerators"],
                    accel=layers["accelerator"]["gap_ratio"],
                    hbm=layers["hbm"]["gap_ratio"],
                    cowos=layers["cowos"]["gap_ratio"],
                    power=layers["power"]["gap_ratio"],
                    network=layers["networking"]["gap_ratio"],
                )
            )
    return "\n".join(rows)


def stress_table(dynamics: dict) -> str:
    """Formula-defined stress tests layered on top of the base case."""
    base = dynamics["scenarios"]["base"]["2026"]
    layers = base["layers"]
    stresses = [
        {
            "name": "HBM4 qualification delay",
            "shock": "HBM supply -15%",
            "formula": "hbm_gap_stress = hbm_gap / (1 - 0.15)",
            "gap": layers["hbm"]["gap_ratio"] / 0.85,
            "channel": "Memory allocation tightens first; accelerator deployment is capped by HBM availability.",
        },
        {
            "name": "Power interconnection delay",
            "shock": "AI-ready power supply -20%",
            "formula": "power_gap_stress = power_gap / (1 - 0.20)",
            "gap": layers["power"]["gap_ratio"] / 0.80,
            "channel": "GPU delivery can continue, but energized deployment lags and backlog shifts to data-center operators.",
        },
        {
            "name": "CoWoS ramp slippage",
            "shock": "CoWoS supply -20%",
            "formula": "cowos_gap_stress = cowos_gap / (1 - 0.20)",
            "gap": layers["cowos"]["gap_ratio"] / 0.80,
            "channel": "Advanced packaging queue lengthens; second-tier accelerator and ASIC customers face allocation risk.",
        },
        {
            "name": "CapEx air pocket",
            "shock": "AI infrastructure demand -22%",
            "formula": "gap_stress = gap * (1 - 0.22)",
            "gap": max(v["gap_ratio"] * 0.78 for k, v in layers.items() if k in {"accelerator", "hbm", "cowos", "power", "networking"}),
            "channel": "Supplier pricing pressure eases; backlog drawdown improves near-term fulfillment but reduces order visibility.",
        },
        {
            "name": "AI demand boom",
            "shock": "Demand +32%, supply ramp +6%",
            "formula": "gap_stress = gap * 1.32 / 1.06",
            "gap": max(v["gap_ratio"] * 1.32 / 1.06 for k, v in layers.items() if k in {"accelerator", "hbm", "cowos", "power", "networking"}),
            "channel": "HBM becomes the binding constraint; power and networking become second-order constraints.",
        },
    ]
    rows = [
        "| Stress Scenario | Shock | Declared Formula | Peak 2026 Gap | Implied Fulfillment | Transmission Channel |",
        "|---|---|---|---:|---:|---|",
    ]
    for s in stresses:
        fulfillment = min(1.0, 1 / s["gap"])
        rows.append(
            f"| {s['name']} | {s['shock']} | `{s['formula']}` | {s['gap']:.2f}x | {fulfillment:.0%} | {s['channel']} |"
        )
    return "\n".join(rows)


def coefficient_table(evidence: dict) -> str:
    rows = [
        "| Coefficient | Value | Unit | Confidence | Status | Sensitivity Range | Evidence IDs |",
        "|---|---:|---|---:|---|---|---|",
    ]
    for cid, c in evidence["coefficients"].items():
        rows.append(
            f"| `{cid}` | {c['value']} | {c['unit']} | {c['confidence']:.0%} | {c.get('validation_status', 'n/a')} | {c.get('sensitivity_range', 'n/a')} | {', '.join(c['evidence_ids'])} |"
        )
    return "\n".join(rows)


def formula_reliability_table(evidence: dict) -> str:
    rows = [
        "| Formula Block | Current Reliability | Why | Upgrade Needed |",
        "|---|---|---|---|",
        [
            "tokens_to_accelerators",
            "High structure / medium calibration",
            "Throughput equation is mechanically valid, but tokens/sec depends on workload mix.",
            "Replace H100-equivalent throughput with measured model/workload benchmarks.",
        ],
        [
            "capex_to_accelerators",
            "Medium-low",
            "CapEx split and blended accelerator ASP are derived proxies.",
            "Company-quarter CapEx split plus NVIDIA/AMD shipment and ASP bridge.",
        ],
        [
            "accelerators_to_hbm",
            "High structure / medium mix",
            "HBM per accelerator is product-spec based, but GPU mix is simplified.",
            "Explicit H100/H200/B200/GB200/MI300 mix and HBM stack count.",
        ],
        [
            "accelerators_to_cowos",
            "Low / placeholder",
            "Current coefficient is calibrated, not package-physics based.",
            "Die area, interposer area, package yield, wafer starts, and package throughput.",
        ],
        [
            "accelerators_to_power",
            "High structure / medium facility calibration",
            "TDP and PUE structure is sound; server overhead and energization timing need site data.",
            "Rack-level power, cooling overhead, interconnection queue, and PUE by facility.",
        ],
        [
            "accelerators_to_networking",
            "Medium-low",
            "GB200 NVL72 scale-up bandwidth is direct, but external scale-out fabric is proxied.",
            "Topology split: NVLink, InfiniBand/Ethernet, NIC count, radix, oversubscription.",
        ],
        [
            "price_pressure_index",
            "Research-only",
            "Convex shortage response is useful for scenario comparison, not a transaction price model.",
            "Historical component price elasticity by utilization and lead time.",
        ],
    ]
    for row in rows[2:]:
        pass
    return "\n".join(rows[:2] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows[2:]])


def model_use_warning(dynamics: dict) -> str:
    audit = dynamics.get("model_audit", {})
    research_only = audit.get("research_only_coefficients", [])
    critical = audit.get("critical_audit_items", [])
    return (
        f"Current model use label: **{audit.get('model_use_label', 'scenario_analysis_only')}**. "
        f"Research-only coefficients: {', '.join(research_only) if research_only else 'none'}. "
        f"Critical audit items: {', '.join(critical) if critical else 'none'}."
    )


def source_table(evidence: dict) -> str:
    rows = [
        "| Source ID | Publisher | Evidence Type | Confidence | Link |",
        "|---|---|---|---:|---|",
    ]
    for sid, s in evidence["sources"].items():
        rows.append(
            f"| `{sid}` | {s['publisher']} | {s['derivation_type']} | {s['confidence']:.0%} | [{s['title']}]({s['url']}) |"
        )
    return "\n".join(rows)


def company_exposure_table() -> str:
    rows = [
        "| Layer / Role | Representative Companies | Model Variables | Transmission Logic |",
        "|---|---|---|---|",
    ]
    for layer, data in COMPANY_EXPOSURE.items():
        rows.append(
            f"| {layer} | {data['companies']} | `{data['model_variable']}` | {data['transmission']} |"
        )
    return "\n".join(rows)


def chain_graph_svg(dynamics: dict) -> str:
    base = dynamics["scenarios"]["base"]["2026"]
    layers = base["layers"]
    dep = base["deployment"]

    def gap(layer: str) -> str:
        return f"{layers[layer]['gap_ratio']:.2f}x"

    def status_color(layer: str) -> str:
        ratio = layers[layer]["gap_ratio"]
        if ratio >= 1.1:
            return "#E03131"
        if ratio >= 0.9:
            return "#F08C00"
        return "#2B8A3E"

    nodes = [
        ("tokens", 60, 82, 205, 86, "Token Demand", "tokens/day", "OpenAI, Anthropic, Meta, xAI", "#1C7ED6"),
        ("capex", 60, 222, 205, 86, "CapEx Procurement", "prebuild demand", "MSFT, AWS, Google, Oracle", "#5F3DC4"),
        ("util", 320, 82, 205, 86, "Utilization Demand", "tokens -> GPUs", "AI services + cloud GPUs", "#1971C2"),
        ("accel", 590, 148, 220, 94, "Accelerator Demand", f"gap {gap('accelerator')}", "NVIDIA, AMD, ASICs", status_color("accelerator")),
        ("hbm", 900, 24, 190, 78, "HBM", f"gap {gap('hbm')}", "SK Hynix, Samsung, Micron", status_color("hbm")),
        ("cowos", 900, 122, 190, 78, "CoWoS / Foundry", f"gap {gap('cowos')}", "TSMC, ASE, Amkor", status_color("cowos")),
        ("power", 900, 220, 190, 78, "Power", f"gap {gap('power')}", "Vertiv, Eaton, Schneider", status_color("power")),
        ("network", 900, 318, 190, 78, "Networking", f"gap {gap('networking')}", "Broadcom, Marvell, Arista", status_color("networking")),
        ("storage", 900, 416, 190, 78, "Storage Flow", f"gap {gap('storage')}", "Solidigm, Samsung SSD", status_color("storage")),
        ("fulfill", 590, 372, 220, 96, "Fulfillment / Backlog", f"{dep['fulfillment_rate']:.0%} fulfilled; {dep['unserved_accelerators']:,} unserved", "Customer allocation risk", "#364FC7"),
    ]

    rects = []
    for _id, x, y, w, h, title, subtitle, companies, color in nodes:
        rects.append(
            f"""
  <g class="node">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{color}" opacity="0.94"/>
    <text x="{x + w / 2}" y="{y + 25}" text-anchor="middle" class="node-title">{html.escape(title)}</text>
    <text x="{x + w / 2}" y="{y + 48}" text-anchor="middle" class="node-subtitle">{html.escape(subtitle)}</text>
    <text x="{x + w / 2}" y="{y + 69}" text-anchor="middle" class="node-company">{html.escape(companies)}</text>
  </g>"""
        )

    edges = [
        (265, 125, 320, 125, "tokens / throughput"),
        (265, 265, 590, 195, "CapEx * shares / ASP"),
        (525, 125, 590, 195, "max(util, procurement)"),
        (810, 195, 900, 63, "* HBM GB"),
        (810, 195, 900, 161, "* CoWoS coef"),
        (810, 195, 900, 259, "* TDP * overhead * PUE"),
        (810, 195, 900, 357, "* fabric coef"),
        (265, 125, 900, 455, "* RAG ratio"),
        (900, 63, 810, 420, "demand / supply"),
        (900, 161, 810, 420, "demand / supply"),
        (900, 259, 810, 420, "demand / supply"),
        (900, 357, 810, 420, "demand / supply"),
        (900, 455, 810, 420, "demand / supply"),
    ]
    edge_lines = []
    for x1, y1, x2, y2, label in edges:
        midx = (x1 + x2) / 2
        midy = (y1 + y2) / 2
        edge_lines.append(
            f"""
  <g class="edge">
    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#arrow)"/>
    <text x="{midx}" y="{midy - 8}" text-anchor="middle">{html.escape(label)}</text>
  </g>"""
        )

    company_nodes = {
        "OpenAI": (70, 92, "demand"),
        "Anthropic": (70, 172, "demand"),
        "Meta AI": (70, 252, "demand"),
        "xAI": (70, 332, "demand"),
        "Microsoft Azure": (310, 72, "cloud"),
        "AWS": (310, 152, "cloud"),
        "Google Cloud": (310, 232, "cloud"),
        "Oracle Cloud": (310, 312, "cloud"),
        "CoreWeave": (310, 392, "cloud"),
        "NVIDIA": (555, 112, "accelerator"),
        "AMD": (555, 222, "accelerator"),
        "ASICs": (555, 332, "accelerator"),
        "SK Hynix": (805, 52, "hbm"),
        "Samsung": (805, 122, "hbm"),
        "Micron": (805, 192, "hbm"),
        "TSMC": (805, 292, "packaging"),
        "TSMC CoWoS": (805, 362, "packaging"),
        "Broadcom / Marvell / Arista": (1045, 132, "network"),
        "Vertiv / Eaton / Schneider": (1045, 282, "power"),
        "Solidigm / Samsung SSD": (1045, 412, "storage"),
    }
    group_colors = {
        "demand": "#1C7ED6",
        "cloud": "#5F3DC4",
        "accelerator": "#C92A2A",
        "hbm": "#F08C00",
        "packaging": "#2B8A3E",
        "network": "#0B7285",
        "power": "#495057",
        "storage": "#1971C2",
    }

    def center(name: str) -> tuple[int, int]:
        x, y, _group = company_nodes[name]
        return x + 85, y + 28

    company_edges = [
        ("OpenAI", "Microsoft Azure", "strategic cloud", "#6741D9"),
        ("OpenAI", "Oracle Cloud", "$30B cloud", "#6741D9"),
        ("OpenAI", "CoreWeave", "GPU cloud", "#6741D9"),
        ("Anthropic", "AWS", "strategic compute", "#6741D9"),
        ("Anthropic", "Google Cloud", "cloud compute", "#6741D9"),
        ("Meta AI", "NVIDIA", "GPU purchase", "#C92A2A"),
        ("xAI", "NVIDIA", "Colossus GPUs", "#C92A2A"),
        ("Microsoft Azure", "NVIDIA", "GPU supply", "#C92A2A"),
        ("AWS", "NVIDIA", "GPU supply", "#C92A2A"),
        ("Google Cloud", "NVIDIA", "GPU supply", "#C92A2A"),
        ("Oracle Cloud", "NVIDIA", "GPU supply", "#C92A2A"),
        ("CoreWeave", "NVIDIA", "GPU supply", "#C92A2A"),
        ("Microsoft Azure", "AMD", "MI300/MI325", "#E8590C"),
        ("AWS", "AMD", "GPU/ASIC mix", "#E8590C"),
        ("Google Cloud", "ASICs", "TPU demand", "#E8590C"),
        ("AWS", "ASICs", "Trainium", "#E8590C"),
        ("NVIDIA", "SK Hynix", "HBM3e/HBM4", "#F08C00"),
        ("NVIDIA", "Micron", "HBM3e", "#F08C00"),
        ("NVIDIA", "Samsung", "qualification", "#F08C00"),
        ("AMD", "SK Hynix", "HBM supply", "#F08C00"),
        ("AMD", "Samsung", "HBM supply", "#F08C00"),
        ("NVIDIA", "TSMC", "foundry", "#2B8A3E"),
        ("AMD", "TSMC", "foundry", "#2B8A3E"),
        ("NVIDIA", "TSMC CoWoS", "advanced package", "#2B8A3E"),
        ("AMD", "TSMC CoWoS", "advanced package", "#2B8A3E"),
        ("Microsoft Azure", "Broadcom / Marvell / Arista", "fabric", "#0B7285"),
        ("AWS", "Broadcom / Marvell / Arista", "fabric", "#0B7285"),
        ("Google Cloud", "Broadcom / Marvell / Arista", "fabric", "#0B7285"),
        ("Microsoft Azure", "Vertiv / Eaton / Schneider", "power chain", "#495057"),
        ("AWS", "Vertiv / Eaton / Schneider", "power chain", "#495057"),
        ("Google Cloud", "Vertiv / Eaton / Schneider", "power chain", "#495057"),
        ("OpenAI", "Solidigm / Samsung SSD", "RAG/storage pull", "#1971C2"),
    ]

    company_edge_lines = []
    for src, tgt, label, color in company_edges:
        x1, y1 = center(src)
        x2, y2 = center(tgt)
        midx = (x1 + x2) / 2
        midy = (y1 + y2) / 2
        company_edge_lines.append(
            f"""
  <g class="company-edge">
    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#arrow2)" stroke="{color}"/>
    <text x="{midx}" y="{midy - 4}" text-anchor="middle">{html.escape(label)}</text>
  </g>"""
        )

    company_rects = []
    for name, (x, y, group) in company_nodes.items():
        company_rects.append(
            f"""
  <g class="company-node">
    <rect x="{x}" y="{y}" width="170" height="56" rx="8" fill="{group_colors[group]}"/>
    <text x="{x + 85}" y="{y + 34}" text-anchor="middle">{html.escape(name)}</text>
  </g>"""
        )

    return f"""
<figure id="chain-graph" class="chain-graph">
<svg viewBox="0 0 1160 560" role="img" aria-label="AI supply chain formula graph with companies">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#486581"/>
    </marker>
  </defs>
  <rect x="18" y="12" width="1124" height="532" rx="10" fill="#F8FAFC" stroke="#BCCCDC"/>
  <text x="42" y="46" class="graph-title">Formula Chain: AI Demand to Supply Bottlenecks</text>
  {"".join(edge_lines)}
  {"".join(rects)}
  <text x="42" y="526" class="graph-note">Color key: green = surplus, orange = near/tight, red = shortage. Company labels are representative exposure points, not exhaustive coverage.</text>
</svg>
<svg viewBox="0 0 1240 520" role="img" aria-label="Representative company relationship graph">
  <defs>
    <marker id="arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#486581"/>
    </marker>
  </defs>
  <rect x="18" y="12" width="1204" height="488" rx="10" fill="#F8FAFC" stroke="#BCCCDC"/>
  <text x="42" y="46" class="graph-title">Representative Company Links: Demand, Cloud, Accelerators, and Bottlenecks</text>
  <text x="155" y="74" text-anchor="middle" class="company-column">AI demand</text>
  <text x="395" y="54" text-anchor="middle" class="company-column">Cloud / GPU procurement</text>
  <text x="640" y="82" text-anchor="middle" class="company-column">Accelerators</text>
  <text x="890" y="40" text-anchor="middle" class="company-column">HBM / Foundry / Packaging</text>
  <text x="1130" y="90" text-anchor="middle" class="company-column">Infrastructure</text>
  {"".join(company_edge_lines)}
  {"".join(company_rects)}
  <text x="42" y="484" class="graph-note">Edges are representative links from the project relationship map; labels are simplified for readability and should be read with the evidence table.</text>
</svg>
</figure>
"""


def render_markdown(dynamics: dict, evidence: dict) -> str:
    today = dt.date.today().isoformat()
    base_2026 = dynamics["scenarios"]["base"]["2026"]
    bull_2026 = dynamics["scenarios"]["bull"]["2026"]

    return f"""# AI Supply Chain Global Dynamics Model

**Report date:** {today}  
**Model as-of date:** {dynamics.get("as_of_date", "n/a")}  
**Status:** Research model, evidence-linked, not affiliated with Oxford Economics.

## Executive View

This report applies a macro-scenario style framework to the AI infrastructure supply chain. It is inspired by the public description of globally integrated scenario models, where shocks propagate through linked demand, supply, price, capacity, and investment channels. It does **not** reproduce Oxford Economics' proprietary Global Economic Model.

The base case shows a near-balanced 2026 HBM market: base HBM gap is **{base_2026['layers']['hbm']['gap_ratio']:.2f}x**, with full modeled fulfillment because no layer exceeds 1.0x. The bull case crosses into shortage: 2026 HBM gap rises to **{bull_2026['layers']['hbm']['gap_ratio']:.2f}x**, fulfillment falls to **{bull_2026['deployment']['fulfillment_rate']:.0%}**, and unserved accelerator demand reaches **{bull_2026['deployment']['unserved_accelerators']:,} H100-equivalent units**.

## 1. Declared Model Structure

The model is a linked system:

```text
AI workload demand
  -> token volume
  -> accelerator utilization demand
  -> hyperscaler CapEx procurement demand
  -> effective accelerator demand
  -> HBM, CoWoS, power, networking, and storage demand
  -> supply gap ratios
  -> fulfillment, backlog, and price-pressure indexes
```

All variables below are annual unless stated otherwise.

## 1A. Chain Graph

{chain_graph_svg(dynamics)}

## 1B. Company Exposure Map

The model treats companies as exposure points along the transmission chain. Demand-side companies create token and CapEx pull; upstream suppliers determine whether that demand can become deployed compute.

{company_exposure_table()}

## 2. Formula Book

### 2.1 Token Demand to Accelerator Utilization

```text
accelerators_required =
  tokens_per_day
  / 86,400
  / (tokens_per_second_per_accelerator * utilization)
```

**Interpretation:** actual AI workload volume becomes required accelerator service capacity.

### 2.2 CapEx to Accelerator Procurement

```text
accelerators_procured =
  total_capex_usd
  * ai_infra_share
  * accelerator_share
  / avg_accelerator_asp_usd
```

**Interpretation:** hyperscalers buy ahead of realized token demand for training runs, reserve capacity, future inference demand, redundancy, and scarce-component allocation.

### 2.3 Effective Accelerator Demand

```text
accelerator_demand =
  max(accelerators_required, accelerators_procured)
  + prior_period_backlog
```

**Interpretation:** procurement demand dominates when cloud providers prebuild capacity ahead of utilization.

### 2.4 Accelerator to HBM

```text
hbm_demand_pb =
  accelerator_demand
  * hbm_gb_per_accelerator
  / 1,000,000
```

**Unit:** PB/year.

### 2.5 Accelerator to CoWoS

```text
cowos_demand_wpm =
  accelerator_demand
  * cowos_wpm_per_accelerator
```

**Unit:** wafer starts per month.  
**Caveat:** this is currently a low-confidence normalized coefficient. The replacement model should use die area, interposer area, package yield, HBM stack count, and wafer throughput.

### 2.6 Accelerator to Power

```text
power_demand_gw =
  accelerator_demand
  * accelerator_tdp_w
  * server_overhead
  * pue
  / 1,000,000,000
```

### 2.7 Accelerator to Networking

```text
network_demand_tbps =
  accelerator_demand
  * network_tbps_per_accelerator
  * (1 + network_complexity_growth * years_after_2026)
```

### 2.8 Tokens to Storage Flow

```text
storage_demand_pb_per_day =
  tokens_per_day
  * rag_storage_ratio
  * bytes_per_token
  / 1,000
  / 1,000,000,000
```

### 2.9 Gap, Fulfillment, Backlog

```text
gap_ratio[layer] = demand[layer] / supply[layer]

limiting_gap = max(gap_ratio[accelerator],
                   gap_ratio[hbm],
                   gap_ratio[cowos],
                   gap_ratio[power],
                   gap_ratio[networking])

fulfillment_rate = min(1, 1 / limiting_gap)

unserved_accelerators =
  accelerator_demand * (1 - fulfillment_rate)

next_period_backlog =
  unserved_accelerators * backlog_carryover
```

### 2.10 Price Pressure Index

```text
shortage = max(gap_ratio - 1, 0)
surplus = max(1 - gap_ratio, 0)

price_pressure_index =
  max(80,
      100 * (1
             + price_beta * (exp(shortage) - 1)
             - 0.25 * surplus))
```

**Interpretation:** 100 is neutral; shortage pressure is convex because scarce components are rationed by allocation and price.

## 3. Evidence-Linked Coefficients

{coefficient_table(evidence)}

## 3A. Formula Reliability Matrix

{model_use_warning(dynamics)}

{formula_reliability_table(evidence)}

## 4. Baseline and Scenario Results

{scenario_table(dynamics)}

## 5. Stress Scenarios

These stress scenarios are formula-defined overlays on the base case. They are deliberately simple so the shock transmission can be audited.

{stress_table(dynamics)}

## 6. Scenario Interpretation

### Base Case

The 2026 base case is close to balance. HBM is the tightest layer, but the modeled HBM gap remains just below shortage at **{base_2026['layers']['hbm']['gap_ratio']:.2f}x**. This means the system can fulfill modeled accelerator demand, but has limited buffer if demand or qualification timing moves adversely.

### Bull AI CapEx Cycle

The bull case is the first true shortage scenario. HBM reaches **{bull_2026['layers']['hbm']['gap_ratio']:.2f}x**, making it the binding constraint. Accelerator, power, and networking also tighten, but HBM caps deployment first. The implication is that memory allocation, not only GPU supply, determines who can deploy AI clusters on time.

### HBM4 Qualification Delay

If HBM supply is delayed by 15%, the base-case 2026 HBM gap moves above 1.0x. This shifts the system from “tight but fulfillable” to “allocation-constrained,” especially for customers without long-term priority contracts.

### Power Interconnection Delay

Power is a slower-moving constraint. A power supply shock does not necessarily prevent GPU shipments, but it prevents energized deployment. The economic symptom is stranded or delayed compute capacity, higher data-center lease premiums, and longer backlog realization.

### CapEx Air Pocket

A CapEx pullback improves near-term fulfillment but weakens order visibility for upstream suppliers. Under this scenario, pricing pressure eases first in accelerators and networking, while HBM remains more resilient because memory content per accelerator continues to rise.

## 7. Strategic Implications

1. HBM is the highest-leverage variable in the current model.
2. CapEx-driven procurement demand matters more than current token utilization in near-term supply-chain stress.
3. Power and networking are second-wave bottlenecks: they bind after accelerator procurement has already happened.
4. CoWoS must be rebuilt with package-area math before the model is investment-grade.
5. The model should be refreshed whenever company CapEx guidance, NVIDIA data-center revenue, HBM bit supply, or TSMC advanced packaging capacity changes.

## 8. Evidence Register

{source_table(evidence)}

## 9. Validation Notes

- Direct product specs and company filings are treated as high-confidence inputs.
- CapEx split, accelerator ASP, CoWoS coefficient, networking coefficient, and RAG storage ratio remain derived or provisional.
- Low-confidence coefficients are retained only because they are explicit, traceable, and have a replacement path in `data/model_evidence.json`.
- The companion Excel model is formula-driven: `outputs/excel/ai_scm_supply_demand_simulator.xlsx`.
"""


def markdown_to_html(markdown: str) -> str:
    """Small, dependency-free markdown renderer for this structured report."""
    lines = markdown.splitlines()
    out: list[str] = []
    in_code = False
    in_table = False
    in_raw_svg = False
    for line in lines:
        if line.startswith("<figure") and "chain-graph" in line:
            if in_table:
                out.append("</table>")
                in_table = False
            in_raw_svg = True
            out.append(line)
            continue
        if in_raw_svg:
            out.append(line)
            if line.strip() == "</figure>":
                in_raw_svg = False
            continue
        if line.startswith("```"):
            out.append("</code></pre>" if in_code else "<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set(cells[0]) == {"-"} or (len(cells) > 1 and all(set(c.replace(":", "")) <= {"-"} for c in cells)):
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                out.append("<table>")
                in_table = True
            out.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        if line.startswith("# "):
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            out.append(f"<p>• {html.escape(line[2:])}</p>")
        elif line.strip():
            escaped = html.escape(line)
            escaped = escaped.replace("**", "")
            out.append(f"<p>{escaped}</p>")
        else:
            out.append("")
    if in_table:
        out.append("</table>")
    return """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>AI SCM Global Dynamics Model</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 42px; color: #182026; line-height: 1.55; }
h1 { color: #102A43; font-size: 30px; }
h2 { color: #243B53; border-top: 1px solid #D9E2EC; padding-top: 22px; margin-top: 30px; }
h3 { color: #334E68; }
table { border-collapse: collapse; width: 100%; margin: 16px 0 24px; font-size: 13px; }
th { background: #243B53; color: white; text-align: left; padding: 8px; }
td { border: 1px solid #D9E2EC; padding: 7px; vertical-align: top; }
pre { background: #F0F4F8; padding: 14px; overflow-x: auto; border-left: 4px solid #486581; }
code { font-family: "SFMono-Regular", Consolas, monospace; }
p { margin: 8px 0; }
.chain-graph { margin: 18px 0 30px; overflow-x: auto; padding-bottom: 8px; }
.chain-graph svg { width: 1120px; max-width: none; height: auto; }
.chain-graph .node-title { fill: #FFFFFF; font-weight: 700; font-size: 15px; }
.chain-graph .node-subtitle { fill: #F8FAFC; font-size: 12px; }
.chain-graph .node-company { fill: #F8FAFC; font-size: 10.5px; }
.chain-graph .edge line { stroke: #486581; stroke-width: 1.7; }
.chain-graph .edge text { fill: #334E68; font-size: 11px; paint-order: stroke; stroke: #F8FAFC; stroke-width: 4px; }
.chain-graph .company-edge line { stroke-width: 1.4; opacity: 0.62; }
.chain-graph .company-edge text { fill: #334E68; font-size: 9.5px; paint-order: stroke; stroke: #F8FAFC; stroke-width: 4px; }
.chain-graph .company-node rect { opacity: 0.94; }
.chain-graph .company-node text { fill: #FFFFFF; font-weight: 700; font-size: 12px; }
.chain-graph .company-column { fill: #334E68; font-weight: 700; font-size: 13px; }
.chain-graph .graph-title { fill: #102A43; font-weight: 700; font-size: 18px; }
.chain-graph .graph-note { fill: #52606D; font-size: 12px; }
</style>
</head>
<body>
""" + "\n".join(out) + "\n</body>\n</html>\n"


def main() -> None:
    dynamics = load_json("dynamics_state.json")
    evidence = load_json("model_evidence.json")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    date_str = dt.date.today().strftime("%Y%m%d")
    markdown = render_markdown(dynamics, evidence)
    md_path = OUT_DIR / f"ai_scm_global_dynamics_report_{date_str}.md"
    html_path = OUT_DIR / f"ai_scm_global_dynamics_report_{date_str}.html"
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(markdown_to_html(markdown), encoding="utf-8")
    print(md_path)
    print(html_path)


if __name__ == "__main__":
    main()
