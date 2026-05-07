"""
Generate an interactive AI supply-chain company dashboard.

The dashboard is static HTML: top = clickable company chain graph,
bottom = chronological evidence/news/reference timeline for the selected
company or supply-chain layer.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs" / "reports"


COMPANY_NODES: list[dict[str, Any]] = [
    {"id": "openai", "name": "OpenAI", "layer": "AI demand", "x": 70, "y": 100, "aliases": ["openai", "chatgpt", "gpt"]},
    {"id": "anthropic", "name": "Anthropic", "layer": "AI demand", "x": 70, "y": 178, "aliases": ["anthropic", "claude"]},
    {"id": "meta", "name": "Meta AI", "layer": "AI demand", "x": 70, "y": 256, "aliases": ["meta", "llama"]},
    {"id": "xai", "name": "xAI", "layer": "AI demand", "x": 70, "y": 334, "aliases": ["xai", "x.ai", "colossus"]},
    {"id": "microsoft", "name": "Microsoft Azure", "layer": "Cloud procurement", "x": 315, "y": 76, "aliases": ["microsoft", "azure", "msft"]},
    {"id": "aws", "name": "AWS", "layer": "Cloud procurement", "x": 315, "y": 154, "aliases": ["aws", "amazon", "trainium"]},
    {"id": "google", "name": "Google Cloud", "layer": "Cloud procurement", "x": 315, "y": 232, "aliases": ["google", "alphabet", "gcp", "tpu", "deepmind"]},
    {"id": "oracle", "name": "Oracle Cloud", "layer": "Cloud procurement", "x": 315, "y": 310, "aliases": ["oracle", "oci"]},
    {"id": "coreweave", "name": "CoreWeave", "layer": "Cloud procurement", "x": 315, "y": 388, "aliases": ["coreweave"]},
    {"id": "nvidia", "name": "NVIDIA", "layer": "Accelerators", "x": 565, "y": 106, "aliases": ["nvidia", "h100", "h200", "blackwell", "gb200", "b200", "gb300", "cuda"]},
    {"id": "amd", "name": "AMD", "layer": "Accelerators", "x": 565, "y": 224, "aliases": ["amd", "mi300", "mi325"]},
    {"id": "asic", "name": "Custom ASICs", "layer": "Accelerators", "x": 565, "y": 342, "aliases": ["asic", "tpu", "trainium", "maia", "mtia"]},
    {"id": "sk_hynix", "name": "SK Hynix", "layer": "HBM", "x": 815, "y": 58, "aliases": ["sk hynix", "sk hynix", "hynix", "hbm4"]},
    {"id": "samsung", "name": "Samsung", "layer": "HBM / Storage", "x": 815, "y": 138, "aliases": ["samsung", "samsung electronics", "samsung ssd"]},
    {"id": "micron", "name": "Micron", "layer": "HBM", "x": 815, "y": 218, "aliases": ["micron", "mu"]},
    {"id": "tsmc", "name": "TSMC", "layer": "Foundry", "x": 815, "y": 318, "aliases": ["tsmc", "foundry", "n2", "3nm", "2nm"]},
    {"id": "cowos", "name": "TSMC CoWoS", "layer": "Advanced packaging", "x": 815, "y": 398, "aliases": ["cowos", "advanced packaging", "package", "interposer"]},
    {"id": "networking", "name": "Broadcom / Marvell / Arista", "layer": "Networking", "x": 1060, "y": 142, "aliases": ["broadcom", "marvell", "arista", "networking", "ethernet", "infiniband", "fabric", "avgo", "mrvl"]},
    {"id": "power", "name": "Vertiv / Eaton / Schneider", "layer": "Power infrastructure", "x": 1060, "y": 302, "aliases": ["vertiv", "eaton", "schneider", "power", "cooling", "ge vernova", "grid", "interconnection"]},
    {"id": "storage", "name": "Solidigm / Samsung SSD", "layer": "Storage", "x": 1060, "y": 440, "aliases": ["solidigm", "ssd", "storage", "nand", "kioxia", "seagate", "wd", "sandisk", "rag"]},
]


COMPANY_EDGES = [
    ("openai", "microsoft", "strategic cloud", "demand"),
    ("openai", "oracle", "cloud capacity", "demand"),
    ("openai", "coreweave", "GPU cloud", "demand"),
    ("anthropic", "aws", "strategic compute", "demand"),
    ("anthropic", "google", "cloud compute", "demand"),
    ("meta", "nvidia", "GPU purchase", "accelerator"),
    ("xai", "nvidia", "cluster GPUs", "accelerator"),
    ("microsoft", "nvidia", "GPU supply", "accelerator"),
    ("aws", "nvidia", "GPU supply", "accelerator"),
    ("google", "nvidia", "GPU supply", "accelerator"),
    ("oracle", "nvidia", "GPU supply", "accelerator"),
    ("coreweave", "nvidia", "GPU supply", "accelerator"),
    ("microsoft", "amd", "MI-series option", "accelerator"),
    ("aws", "asic", "Trainium", "accelerator"),
    ("google", "asic", "TPU", "accelerator"),
    ("microsoft", "asic", "Maia", "accelerator"),
    ("meta", "asic", "MTIA", "accelerator"),
    ("nvidia", "sk_hynix", "HBM3e/HBM4", "memory"),
    ("nvidia", "micron", "HBM3e", "memory"),
    ("nvidia", "samsung", "qualification", "memory"),
    ("amd", "sk_hynix", "HBM supply", "memory"),
    ("amd", "samsung", "HBM supply", "memory"),
    ("nvidia", "tsmc", "foundry", "packaging"),
    ("amd", "tsmc", "foundry", "packaging"),
    ("nvidia", "cowos", "CoWoS slots", "packaging"),
    ("amd", "cowos", "advanced package", "packaging"),
    ("microsoft", "networking", "fabric", "infra"),
    ("aws", "networking", "fabric", "infra"),
    ("google", "networking", "fabric", "infra"),
    ("microsoft", "power", "power chain", "infra"),
    ("aws", "power", "power chain", "infra"),
    ("google", "power", "power chain", "infra"),
    ("openai", "storage", "RAG/storage pull", "infra"),
    ("meta", "storage", "model + content data", "infra"),
]


GROUP_COLORS = {
    "AI demand": "#1C7ED6",
    "Cloud procurement": "#6741D9",
    "Accelerators": "#C92A2A",
    "HBM": "#F08C00",
    "HBM / Storage": "#D9480F",
    "Foundry": "#2B8A3E",
    "Advanced packaging": "#2F9E44",
    "Networking": "#0B7285",
    "Power infrastructure": "#495057",
    "Storage": "#1971C2",
}


def load_json(name: str) -> dict[str, Any]:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def sort_key(period: str) -> tuple[int, int, int]:
    match = re.match(r"(\d{4})(?:[- ]?Q([1-4])|-(\d{2}))?", period or "")
    if not match:
        return (9999, 12, 31)
    year = int(match.group(1))
    if match.group(2):
        month = (int(match.group(2)) - 1) * 3 + 1
    elif match.group(3):
        month = int(match.group(3))
    else:
        month = 1
    return (year, month, 1)


def normalize_text(*parts: Any) -> str:
    return " ".join(str(p).lower() for p in parts if p is not None)


def matching_companies(text: str) -> list[str]:
    found: list[str] = []
    low = text.lower()
    for node in COMPANY_NODES:
        if any(alias.lower() in low for alias in node["aliases"]):
            found.append(node["id"])
    if "hbm" in low and not any(c in found for c in ["sk_hynix", "samsung", "micron"]):
        found.extend(["sk_hynix", "samsung", "micron"])
    if "gpu" in low and "nvidia" not in found:
        found.append("nvidia")
    return list(dict.fromkeys(found))


def infer_source_period(source_id: str, source: dict[str, Any]) -> tuple[str, str]:
    observations = source.get("observations", {})
    if observations.get("period"):
        return str(observations["period"]), "declared_in_filing_metadata"
    text = normalize_text(source_id, source.get("title"), source.get("publisher"))
    if "h100" in text:
        return "2022-03", "inferred_from_product_launch"
    if "h200" in text:
        return "2023-11", "inferred_from_product_launch"
    if "gb200" in text:
        return "2024-03", "inferred_from_product_launch"
    if "fy2026_q4" in text or "fiscal 2026" in text:
        return "2026", "inferred_from_fiscal_title"
    if "fy2026_q1" in text or "q1 2026" in text or "first quarter 2026" in text:
        return "2026-Q1", "inferred_from_fiscal_title"
    return "undated", "not_declared_in_source_table"


def add_item(items: list[dict[str, Any]], item: dict[str, Any]) -> None:
    companies = item.get("companies") or []
    if not companies:
        companies = matching_companies(normalize_text(item.get("title"), item.get("summary"), item.get("publisher"), item.get("category")))
    item["companies"] = companies
    item["period_sort"] = sort_key(item.get("period", "undated"))
    items.append(item)


def build_reference_items(
    market: dict[str, Any],
    evidence: dict[str, Any],
    sec_filings: dict[str, Any] | None = None,
    sec_financials: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    sec_filings = sec_filings or {}
    sec_financials = sec_financials or {}

    for event in market.get("events", []):
        if event.get("event") == "capex":
            if not event.get("company") or not event.get("year"):
                continue
            company = str(event.get("company", ""))
            add_item(
                items,
                {
                    "period": str(event.get("year", "undated")),
                    "kind": "capex data",
                    "category": "capex",
                    "title": f"{company} CapEx {event.get('confidence', 'estimate')}",
                    "summary": f"{company} CapEx value: ${float(event.get('value', 0)) / 1e9:,.0f}B.",
                    "publisher": str(event.get("source", "market_state")),
                    "url": "",
                    "confidence": str(event.get("confidence", "n/a")),
                    "companies": matching_companies(company),
                },
            )
        elif event.get("event") == "supply_constraint":
            if not event.get("component"):
                continue
            component = str(event.get("component", "Supply"))
            add_item(
                items,
                {
                    "period": market.get("as_of_date", "undated"),
                    "kind": "capacity signal",
                    "category": "supply_constraint",
                    "title": event.get("detail", f"{component} utilization"),
                    "summary": f"Utilization: {float(event.get('utilization', 0)):.0%}; severity: {event.get('severity', 'n/a')}.",
                    "publisher": str(event.get("source", "market_state")),
                    "url": "",
                    "confidence": str(event.get("severity", "n/a")),
                    "companies": matching_companies(component),
                },
            )

    for event in market.get("key_events", []):
        add_item(
            items,
            {
                "period": event.get("date", "undated"),
                "kind": "market event",
                "category": event.get("category", "event"),
                "title": event.get("event", "Untitled event"),
                "summary": event.get("impact", ""),
                "publisher": "market_state.key_events",
                "url": "",
                "confidence": "project reference",
                "companies": matching_companies(normalize_text(event.get("event"), event.get("impact"), event.get("category"))),
            },
        )

    for milestone in market.get("ai_model_milestones", []):
        add_item(
            items,
            {
                "period": milestone.get("date", "undated"),
                "kind": "AI model milestone",
                "category": "demand_signal",
                "title": milestone.get("model", "AI model milestone"),
                "summary": milestone.get("significance", ""),
                "publisher": milestone.get("org", "AI model milestone"),
                "url": "",
                "confidence": "context",
                "companies": matching_companies(normalize_text(milestone.get("model"), milestone.get("org"), milestone.get("significance"))),
            },
        )

    for signal in market.get("investment_signals_seed", []):
        company_text = normalize_text(signal.get("company"), signal.get("layer"))
        add_item(
            items,
            {
                "period": market.get("as_of_date", "undated"),
                "kind": "company thesis",
                "category": signal.get("layer", "company"),
                "title": f"{signal.get('company')} - {signal.get('signal')}",
                "summary": f"Thesis: {signal.get('thesis', '')} Catalyst: {signal.get('catalyst', '')} Risk: {signal.get('risk', '')}",
                "publisher": "market_state.investment_signals_seed",
                "url": "",
                "confidence": signal.get("timeframe", "n/a"),
                "companies": matching_companies(company_text),
            },
        )

    for source_id, source in evidence.get("sources", {}).items():
        period, period_note = infer_source_period(source_id, source)
        observation_bits = []
        for key, value in source.get("observations", {}).items():
            observation_bits.append(f"{key}: {value}")
        add_item(
            items,
            {
                "period": period,
                "kind": "formula evidence",
                "category": source.get("derivation_type", "source"),
                "title": source.get("title", source_id),
                "summary": "; ".join(observation_bits[:5]),
                "publisher": source.get("publisher", "source"),
                "url": source.get("url", ""),
                "confidence": f"{float(source.get('confidence', 0)):.0%}",
                "period_note": period_note,
                "source_id": source_id,
                "companies": matching_companies(normalize_text(source_id, source.get("publisher"), source.get("title"), source.get("url"), json.dumps(source.get("observations", {})))),
            },
        )

    for filing in sec_filings.get("filings", []):
        company = filing.get("company", "Company")
        form = filing.get("form", "filing")
        period = filing.get("period") or filing.get("report_date") or filing.get("filing_date") or "undated"
        add_item(
            items,
            {
                "period": period,
                "kind": "SEC filing",
                "category": form,
                "title": f"{company} {form} - {period}",
                "summary": (
                    f"Filed {filing.get('filing_date', 'n/a')}; report date {filing.get('report_date', 'n/a')}; "
                    f"accession {filing.get('accession_number', 'n/a')}. Use this as a filing anchor for CapEx, segment revenue, "
                    "PP&E, lease, backlog, inventory, and risk-factor extraction."
                ),
                "publisher": "SEC EDGAR",
                "url": filing.get("sec_url", ""),
                "confidence": filing.get("source_type", "SEC_EDGAR"),
                "source_id": filing.get("accession_number", ""),
                "companies": [filing["node"]] if filing.get("node") else matching_companies(company),
            },
        )

    for company in sec_filings.get("companies", []):
        if company.get("status") == "fetched":
            continue
        add_item(
            items,
            {
                "period": sec_filings.get("metadata", {}).get("generated_at", "undated")[:10],
                "kind": "filing coverage note",
                "category": company.get("reporting_basis", "reporting"),
                "title": f"{company.get('company')} reporting basis",
                "summary": company.get("notes", company.get("reason", "")),
                "publisher": "AI SCM filing coverage map",
                "url": "",
                "confidence": company.get("reason", "coverage note"),
                "companies": [company["node"]] if company.get("node") else matching_companies(company.get("company", "")),
            },
        )

    financial_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for record in sec_financials.get("records", []):
        key = (
            record.get("node", ""),
            record.get("company", ""),
            record.get("period", "undated"),
            record.get("form", ""),
        )
        financial_groups.setdefault(key, []).append(record)

    for (node, company, period, form), records in financial_groups.items():
        records = sorted(records, key=lambda item: item.get("metric", ""))
        metric_bits = []
        for record in records[:10]:
            value = record.get("value")
            unit = record.get("unit", "")
            if isinstance(value, (int, float)) and unit == "USD":
                rendered_value = f"${value / 1e9:,.2f}B"
            elif isinstance(value, (int, float)):
                rendered_value = f"{value:,.0f} {unit}".strip()
            else:
                rendered_value = f"{value} {unit}".strip()
            metric_bits.append(f"{record.get('metric')}: {rendered_value}")
        filed = max((record.get("filed", "") for record in records), default="")
        add_item(
            items,
            {
                "period": period,
                "kind": "SEC financial statement",
                "category": form,
                "title": f"{company} financial statement facts - {period}",
                "summary": f"Filed {filed or 'n/a'}. " + "; ".join(metric_bits),
                "publisher": "SEC XBRL companyfacts",
                "url": "",
                "confidence": "SEC_XBRL_companyfacts",
                "source_id": ", ".join(sorted({record.get("accession_number", "") for record in records if record.get("accession_number")})),
                "companies": [node] if node else matching_companies(company),
            },
        )

    dedup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in items:
        key = (item.get("period", ""), item.get("title", ""), item.get("publisher", ""))
        if key in dedup:
            dedup[key]["companies"] = sorted(set(dedup[key].get("companies", []) + item.get("companies", [])))
        else:
            dedup[key] = item

    return sorted(dedup.values(), key=lambda x: (x["period_sort"], x.get("title", "")))


def graph_svg() -> str:
    node_by_id = {node["id"]: node for node in COMPANY_NODES}

    def center(node_id: str) -> tuple[int, int]:
        node = node_by_id[node_id]
        return node["x"] + 86, node["y"] + 28

    edges = []
    for source, target, label, group in COMPANY_EDGES:
        x1, y1 = center(source)
        x2, y2 = center(target)
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        edges.append(
            f"""
    <g class="edge edge-{html.escape(source)} edge-{html.escape(target)}" data-source="{html.escape(source)}" data-target="{html.escape(target)}" data-group="{html.escape(group)}">
      <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#arrow)"></line>
      <text x="{mx}" y="{my - 5}" text-anchor="middle">{html.escape(label)}</text>
    </g>"""
        )

    nodes = []
    for node in COMPANY_NODES:
        color = GROUP_COLORS[node["layer"]]
        nodes.append(
            f"""
    <g class="company-node" data-company="{html.escape(node['id'])}" tabindex="0" role="button" aria-label="{html.escape(node['name'])}">
      <rect x="{node['x']}" y="{node['y']}" width="172" height="58" rx="7" fill="{color}"></rect>
      <text x="{node['x'] + 86}" y="{node['y'] + 25}" text-anchor="middle" class="company-name">{html.escape(node['name'])}</text>
      <text x="{node['x'] + 86}" y="{node['y'] + 43}" text-anchor="middle" class="company-layer">{html.escape(node['layer'])}</text>
    </g>"""
        )

    return f"""
  <svg id="chainGraph" viewBox="0 0 1260 540" role="img" aria-label="Clickable AI supply-chain company graph">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z"></path>
      </marker>
    </defs>
    <rect x="18" y="18" width="1224" height="500" rx="8" class="graph-frame"></rect>
    <text x="46" y="54" class="graph-title">AI Supply Chain: Company Links and Evidence Timeline</text>
    <text x="156" y="86" class="column-label">AI demand</text>
    <text x="401" y="62" class="column-label">Cloud procurement</text>
    <text x="651" y="92" class="column-label">Accelerators</text>
    <text x="901" y="48" class="column-label">HBM / Foundry / Packaging</text>
    <text x="1146" y="116" class="column-label">Infrastructure</text>
    {"".join(edges)}
    {"".join(nodes)}
  </svg>"""


def render_dashboard(market: dict[str, Any], evidence: dict[str, Any], items: list[dict[str, Any]]) -> str:
    today = dt.date.today().isoformat()
    payload = {
        "nodes": COMPANY_NODES,
        "edges": COMPANY_EDGES,
        "items": items,
        "asOfDate": market.get("as_of_date") or evidence.get("metadata", {}).get("created"),
    }
    payload_json = (
        json.dumps(payload, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    total_refs = len(items)
    companies_with_refs = len({company for item in items for company in item.get("companies", [])})
    sec_count = sum(1 for item in items if item.get("kind") == "SEC filing")
    financial_count = sum(1 for item in items if item.get("kind") == "SEC financial statement")

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI SCM Company Chain Dashboard</title>
  <style>
    :root {{
      --ink: #17212b;
      --muted: #5b6876;
      --line: #ccd6e0;
      --panel: #ffffff;
      --band: #f3f6f9;
      --accent: #1c7ed6;
      --orange: #f08c00;
      --green: #2b8a3e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #eef2f5;
    }}
    header {{
      padding: 24px 28px 16px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      letter-spacing: 0;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      max-width: 980px;
      line-height: 1.55;
    }}
    .metrics {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      padding: 16px 28px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    .metric {{
      min-width: 150px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fafcfd;
    }}
    .metric strong {{ display: block; font-size: 18px; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    main {{ padding: 18px 28px 36px; }}
    .graph-wrap {{
      width: 100%;
      overflow-x: auto;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    svg {{ min-width: 1040px; display: block; }}
    .graph-frame {{ fill: #f8fafc; stroke: #bcccdc; }}
    .graph-title {{ font-size: 22px; font-weight: 760; fill: #17212b; }}
    .column-label {{ font-size: 13px; font-weight: 760; fill: #52606d; text-anchor: middle; }}
    marker path {{ fill: #657789; }}
    .edge line {{ stroke: #7b8794; stroke-width: 1.9; opacity: .46; }}
    .edge text {{ display: none; }}
    .edge.is-active line {{ stroke: #111827; stroke-width: 3.2; opacity: .95; }}
    .company-node {{ cursor: pointer; outline: none; }}
    .company-node rect {{ stroke: rgba(255,255,255,.86); stroke-width: 1.4; filter: drop-shadow(0 2px 3px rgba(15, 23, 42, .16)); }}
    .company-node text {{ pointer-events: none; fill: #fff; }}
    .company-name {{ font-size: 14px; font-weight: 760; }}
    .company-layer {{ font-size: 10.5px; opacity: .88; }}
    .company-node.is-selected rect {{ stroke: #111827; stroke-width: 3; }}
    .company-node.is-dimmed {{ opacity: .34; }}
    .controls {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      padding: 14px 0;
    }}
    .search {{
      flex: 1 1 280px;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 8px 10px;
      font-size: 14px;
    }}
    .filter-button {{
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 7px;
      min-height: 38px;
      padding: 8px 11px;
      font-weight: 650;
      color: #273444;
      cursor: pointer;
    }}
    .filter-button.is-active {{ border-color: var(--accent); color: var(--accent); background: #e7f2ff; }}
    .detail-grid {{
      display: grid;
      grid-template-columns: minmax(240px, 330px) minmax(0, 1fr);
      gap: 16px;
      align-items: start;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .selected-title {{ margin: 0 0 8px; font-size: 20px; }}
    .selected-meta {{ color: var(--muted); line-height: 1.45; margin: 0 0 12px; }}
    .linked-list {{ display: grid; gap: 7px; }}
    .linked-item {{
      border: 1px solid #d8e0e8;
      background: #f8fafc;
      border-radius: 7px;
      padding: 8px;
      font-size: 13px;
    }}
    .timeline {{
      display: grid;
      gap: 10px;
    }}
    .timeline-item {{
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 12px;
      padding: 13px;
      border: 1px solid #d8e0e8;
      border-radius: 8px;
      background: #ffffff;
    }}
    .period {{
      color: #17212b;
      font-weight: 760;
      font-size: 13px;
    }}
    .item-title {{
      margin: 0 0 6px;
      font-size: 15px;
      line-height: 1.35;
    }}
    .item-summary {{
      margin: 0 0 8px;
      color: #3f4d5a;
      line-height: 1.5;
      font-size: 13px;
    }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      border: 1px solid #d8e0e8;
      background: #f3f6f9;
      border-radius: 999px;
      padding: 3px 8px;
      color: #52606d;
      font-size: 11px;
      font-weight: 650;
    }}
    a {{ color: #1864ab; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .empty {{
      padding: 28px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed #bcccdc;
      border-radius: 8px;
      background: #f8fafc;
    }}
    @media (max-width: 860px) {{
      header, .metrics, main {{ padding-left: 16px; padding-right: 16px; }}
      .detail-grid {{ grid-template-columns: 1fr; }}
      .timeline-item {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AI 공급망 기업 체인 대시보드</h1>
    <p class="subtitle">상단 그래프에서 기업을 클릭하면 해당 기업과 연결된 CapEx, 공급 제약, 제품 스펙, earnings, 모델 milestone, 프로젝트 참고자료가 아래에 시간순으로 정렬됩니다. 날짜가 명시되지 않은 공식 출처는 제목/제품 출시 맥락에서 추정한 기간을 별도 표시했습니다.</p>
  </header>
  <section class="metrics" aria-label="dashboard metrics">
    <div class="metric"><strong>{html.escape(str(market.get("as_of_date", "n/a")))}</strong><span>market data as-of</span></div>
    <div class="metric"><strong>{total_refs}</strong><span>timeline references</span></div>
    <div class="metric"><strong>{sec_count}</strong><span>SEC filing anchors</span></div>
    <div class="metric"><strong>{financial_count}</strong><span>financial statement periods</span></div>
    <div class="metric"><strong>{companies_with_refs}</strong><span>companies with mapped refs</span></div>
    <div class="metric"><strong>{today}</strong><span>dashboard generated</span></div>
  </section>
  <main>
    <section class="graph-wrap" aria-label="supply chain graph">
      {graph_svg()}
    </section>
    <section class="controls" aria-label="timeline controls">
      <input id="searchBox" class="search" type="search" placeholder="자료 검색: company, HBM, CapEx, CoWoS, power..." aria-label="Search references">
      <button class="filter-button is-active" data-kind="all">All</button>
      <button class="filter-button" data-kind="capex">CapEx</button>
      <button class="filter-button" data-kind="supply_constraint">Supply constraint</button>
      <button class="filter-button" data-kind="SEC filing">SEC filings</button>
      <button class="filter-button" data-kind="10-Q">10-Q</button>
      <button class="filter-button" data-kind="10-K">10-K</button>
      <button class="filter-button" data-kind="SEC financial statement">Financials</button>
      <button class="filter-button" data-kind="formula evidence">Formula evidence</button>
      <button class="filter-button" data-kind="market event">Market events</button>
    </section>
    <section class="detail-grid">
      <aside class="panel">
        <h2 id="selectedTitle" class="selected-title">전체 공급망</h2>
        <p id="selectedMeta" class="selected-meta">기업을 클릭하면 연결 관계와 자료 타임라인이 좁혀집니다.</p>
        <div id="linkedList" class="linked-list"></div>
      </aside>
      <section class="panel">
        <div id="timeline" class="timeline"></div>
      </section>
    </section>
  </main>
  <script id="dashboardData" type="application/json">{payload_json}</script>
  <script>
    const data = JSON.parse(document.getElementById('dashboardData').textContent);
    let selectedCompany = null;
    let selectedKind = 'all';
    const nodes = Array.from(document.querySelectorAll('.company-node'));
    const edges = Array.from(document.querySelectorAll('.edge'));
    const timeline = document.getElementById('timeline');
    const selectedTitle = document.getElementById('selectedTitle');
    const selectedMeta = document.getElementById('selectedMeta');
    const linkedList = document.getElementById('linkedList');
    const searchBox = document.getElementById('searchBox');
    const nodeById = Object.fromEntries(data.nodes.map(node => [node.id, node]));

    function esc(value) {{
      return String(value ?? '').replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}

    function itemMatches(item) {{
      const query = searchBox.value.trim().toLowerCase();
      const companyOk = !selectedCompany || item.companies.includes(selectedCompany);
      const kindOk = selectedKind === 'all' || item.category === selectedKind || item.kind === selectedKind;
      const text = [item.period, item.kind, item.category, item.title, item.summary, item.publisher, item.source_id].join(' ').toLowerCase();
      const queryOk = !query || text.includes(query);
      return companyOk && kindOk && queryOk;
    }}

    function renderLinked() {{
      linkedList.innerHTML = '';
      const links = selectedCompany
        ? data.edges.filter(edge => edge[0] === selectedCompany || edge[1] === selectedCompany)
        : data.edges.slice(0, 8);
      if (!links.length) {{
        linkedList.innerHTML = '<div class="empty">표시할 연결 관계가 없습니다.</div>';
        return;
      }}
      for (const edge of links) {{
        const source = nodeById[edge[0]]?.name || edge[0];
        const target = nodeById[edge[1]]?.name || edge[1];
        const div = document.createElement('div');
        div.className = 'linked-item';
        div.innerHTML = `<strong>${{esc(source)}} -> ${{esc(target)}}</strong><br>${{esc(edge[2])}}`;
        linkedList.appendChild(div);
      }}
    }}

    function renderTimeline() {{
      const visible = data.items.filter(itemMatches);
      if (!visible.length) {{
        timeline.innerHTML = '<div class="empty">선택한 조건에 맞는 자료가 없습니다.</div>';
        return;
      }}
      timeline.innerHTML = visible.map(item => {{
        const link = item.url ? `<a href="${{esc(item.url)}}" target="_blank" rel="noreferrer">${{esc(item.publisher)}}</a>` : esc(item.publisher);
        const companies = item.companies.map(id => nodeById[id]?.name || id).join(', ');
        const periodNote = item.period_note ? `<span class="badge">${{esc(item.period_note)}}</span>` : '';
        const sourceId = item.source_id ? `<span class="badge">${{esc(item.source_id)}}</span>` : '';
        return `
          <article class="timeline-item">
            <div class="period">${{esc(item.period)}}</div>
            <div>
              <h3 class="item-title">${{esc(item.title)}}</h3>
              <p class="item-summary">${{esc(item.summary)}}</p>
              <div class="badges">
                <span class="badge">${{esc(item.kind)}}</span>
                <span class="badge">${{esc(item.category)}}</span>
                <span class="badge">${{esc(item.confidence)}}</span>
                <span class="badge">${{link}}</span>
                <span class="badge">${{esc(companies || 'unmapped')}}</span>
                ${{periodNote}}
                ${{sourceId}}
              </div>
            </div>
          </article>`;
      }}).join('');
    }}

    function applySelection(companyId) {{
      selectedCompany = selectedCompany === companyId ? null : companyId;
      for (const node of nodes) {{
        const id = node.dataset.company;
        node.classList.toggle('is-selected', id === selectedCompany);
        node.classList.toggle('is-dimmed', Boolean(selectedCompany) && id !== selectedCompany);
      }}
      for (const edge of edges) {{
        const active = selectedCompany && (edge.dataset.source === selectedCompany || edge.dataset.target === selectedCompany);
        edge.classList.toggle('is-active', Boolean(active));
      }}
      if (selectedCompany) {{
        const node = nodeById[selectedCompany];
        const count = data.items.filter(item => item.companies.includes(selectedCompany)).length;
        selectedTitle.textContent = node.name;
        selectedMeta.textContent = `${{node.layer}} / mapped references: ${{count}}`;
      }} else {{
        selectedTitle.textContent = '전체 공급망';
        selectedMeta.textContent = '기업을 클릭하면 연결 관계와 자료 타임라인이 좁혀집니다.';
      }}
      renderLinked();
      renderTimeline();
    }}

    for (const node of nodes) {{
      node.addEventListener('click', () => applySelection(node.dataset.company));
      node.addEventListener('keydown', event => {{
        if (event.key === 'Enter' || event.key === ' ') {{
          event.preventDefault();
          applySelection(node.dataset.company);
        }}
      }});
    }}
    for (const button of document.querySelectorAll('.filter-button')) {{
      button.addEventListener('click', () => {{
        selectedKind = button.dataset.kind;
        document.querySelectorAll('.filter-button').forEach(btn => btn.classList.toggle('is-active', btn === button));
        renderTimeline();
      }});
    }}
    searchBox.addEventListener('input', renderTimeline);
    renderLinked();
    renderTimeline();
  </script>
</body>
</html>
"""


def main() -> None:
    market = load_json("market_state.json")
    evidence = load_json("model_evidence.json")
    sec_filings = load_json("sec_filings.json")
    sec_financials = load_json("sec_financials.json")
    items = build_reference_items(market, evidence, sec_filings, sec_financials)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date_stamp = dt.date.today().strftime("%Y%m%d")
    out_path = OUT_DIR / f"ai_scm_supply_chain_dashboard_{date_stamp}.html"
    out_path.write_text(render_dashboard(market, evidence, items), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
