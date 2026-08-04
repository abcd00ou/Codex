"""Generate a research-institution style power, token and HBM report.

The report is intentionally downstream of generate_llm_token_capacity_report.py:
that workbook remains the formula source of truth, while this script reshapes
the same payload into an institutional narrative with charts and HBM-equivalent
supply estimates.
"""

from __future__ import annotations

import csv
import html
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from generate_llm_token_capacity_report import OUT, build_payload


REPORT_STEM = "llm_power_token_hbm_research_report_2026_2030"
CHART_DIR = OUT / "charts" / REPORT_STEM
RUN_DATE = date.today().isoformat()

HBM_ASSUMPTIONS = {
    "H100/H200/A100 class": {
        "hbm_gb_per_unit": 141.0,
        "power_kw_per_unit": 1.73,
        "basis": "H200-class HBM3e proxy; legacy A100/H100 rows are not separately modeled in this report.",
        "confidence": "Medium",
    },
    "B200/B300 class": {
        "hbm_gb_per_unit": 180.0,
        "power_kw_per_unit": 2.17,
        "basis": "DGX B200 memory proxy, mapped to B200/B300 benchmark bucket.",
        "confidence": "Medium",
    },
    "GB200/GB300 class": {
        "hbm_gb_per_unit": 186.0,
        "power_kw_per_unit": 2.10,
        "basis": "GB200/GB300 rack-scale Blackwell proxy, normalized per GPU-equivalent accelerator unit.",
        "confidence": "Medium",
    },
    "R200/R300 future": {
        "hbm_gb_per_unit": 288.0,
        "power_kw_per_unit": 2.17,
        "basis": "Future accelerator placeholder; replace with disclosed Rubin-class memory and all-in power.",
        "confidence": "Low",
    },
    "TPU": {
        "hbm_gb_per_unit": 192.0,
        "power_kw_per_unit": 2.17,
        "basis": "Custom accelerator HBM-equivalent placeholder; replace with TPU generation-specific HBM and all-in power.",
        "confidence": "Low",
    },
    "Trainium": {
        "hbm_gb_per_unit": 192.0,
        "power_kw_per_unit": 2.17,
        "basis": "Custom accelerator HBM-equivalent placeholder; replace with Trainium generation-specific HBM and all-in power.",
        "confidence": "Low",
    },
    "Maia": {
        "hbm_gb_per_unit": 192.0,
        "power_kw_per_unit": 2.17,
        "basis": "Custom accelerator HBM-equivalent placeholder; replace with Maia generation-specific HBM and all-in power.",
        "confidence": "Low",
    },
    "MTIA": {
        "hbm_gb_per_unit": 192.0,
        "power_kw_per_unit": 2.17,
        "basis": "Custom accelerator HBM-equivalent placeholder; replace with MTIA generation-specific HBM and all-in power.",
        "confidence": "Low",
    },
    "Ascend": {
        "hbm_gb_per_unit": 192.0,
        "power_kw_per_unit": 2.17,
        "basis": "China accelerator HBM-equivalent placeholder; replace with generation-specific HBM and all-in power.",
        "confidence": "Low",
    },
    "Other / unknown accelerator": {
        "hbm_gb_per_unit": 192.0,
        "power_kw_per_unit": 2.17,
        "basis": "Fallback HBM-equivalent placeholder for unmapped accelerator rows.",
        "confidence": "Low",
    },
}

SOURCES = [
    {
        "id": "Epoch AI data centers",
        "use": "CSP/user capacity attribution, current/contracted IT power and completion timing seed.",
        "url": "https://epoch.ai/data/ai-data-centers",
    },
    {
        "id": "InferenceX benchmark dump",
        "use": "Public output-token TPS/MW benchmark proxy by model, GPU, ISL/OSL, concurrency and serving stack.",
        "url": "https://inferencex.com/",
    },
    {
        "id": "NVIDIA H200",
        "use": "H200 141GB HBM3e memory and hardware generation reference.",
        "url": "https://www.nvidia.com/en-gb/data-center/h200/",
    },
    {
        "id": "NVIDIA DGX B200",
        "use": "B200 system memory reference used for B200-class HBM proxy.",
        "url": "https://docs.nvidia.com/dgx/dgxb200-user-guide/introduction-to-dgxb200.html",
    },
    {
        "id": "NVIDIA GB200 NVL72",
        "use": "GB200 rack-scale Blackwell HBM reference.",
        "url": "https://www.nvidia.com/en-us/data-center/gb200-nvl72/",
    },
]

FOCUS_COMPANIES = ["OpenAI", "Anthropic", "Google", "Microsoft", "xAI"]

COMPANY_READS = {
    "OpenAI": {
        "title": "OpenAI: 멀티 CSP 기반의 frontier serving capacity",
        "read": "OpenAI는 본 모델에서 가장 넓은 외부 계약 전력 구조를 가진 사업자로 처리한다. Microsoft, Oracle, CoreWeave, G42, SoftBank 계열의 capacity path가 OpenAI의 inference pool로 정규화되어 들어오며, 핵심은 OpenAI의 토큰 공급량이 특정 CSP 한 곳의 전력이나 GPU mix로 설명되지 않는다는 점이다. 따라서 OpenAI의 결과값은 각 CSP의 계약 전력 비중과 해당 CSP의 accelerator mix가 결합된 가중 평균으로 읽어야 한다.",
        "watch": "TPS/MW는 의도적으로 보수적으로 잡았다. 작은 open model의 최대 benchmark가 아니라 frontier급 모델 라우팅을 proxy로 사용하기 때문이다. 따라서 OpenAI의 토큰 공급량은 proxy model 교체, B200/GB200 전환 속도, 그리고 실제 production traffic 중 더 작은 routed model이 차지하는 비중에 매우 민감하다.",
    },
    "Anthropic": {
        "title": "Anthropic: Amazon/custom accelerator 노출과 agentic-heavy mix",
        "read": "Anthropic은 일반 짧은 대화보다 long-context 및 agentic workload 비중이 높은 사업자로 모델링했다. Claude 사용처가 코딩, 리서치, 도구 사용 세션에 구조적으로 많이 노출되어 있기 때문이다. 따라서 단순 GW보다 capacity attribution이 중요하다. 특히 Trainium 비중이 높은 CSP mix에서는 NVIDIA GPU만으로 읽는 경우와 HBM 및 TPS/MW 결과가 크게 달라질 수 있다.",
        "watch": "Trainium과 같은 custom accelerator의 HBM 및 TPS/MW는 현재 낮은 신뢰도의 placeholder다. 비교 가능한 Trainium serving telemetry 또는 Claude production throughput이 확보되면 가장 먼저 교체해야 한다.",
    },
    "Google": {
        "title": "Google: TPU-first internal fleet economics",
        "read": "Google은 TPU-first 내부 fleet으로 읽는 것이 적절하다. Gemini와 Google Cloud serving은 내부 최적화된 TPU infrastructure를 활용할 수 있으므로, 순수 NVIDIA benchmark와 동일하게 취급하지 않았다. 이 때문에 본 보고서에서는 Google의 purpose-built accelerator 노출이 높고, public GPU-only benchmark와의 비교 가능성은 상대적으로 낮다.",
        "watch": "핵심 대체 데이터는 TPU 세대별 HBM, all-in power, Gemini serving TPS/MW다. 이 값이 들어오기 전까지 Google의 토큰 추정치는 방향성 판단에는 유용하지만 NVIDIA 기반 row보다 감사 가능성은 낮다.",
    },
    "Microsoft": {
        "title": "Microsoft: OpenAI attribution 이후의 Copilot/Azure AI serving burden",
        "read": "Microsoft는 OpenAI 모델 소유자 capacity를 분리한 뒤, 자체 Copilot 및 Azure AI serving surface로 모델링했다. 현재 dataset에서는 routed assistant workload에 가까운 proxy와 B200-heavy accelerator mix가 결합되어 높은 token-supply contribution이 나온다.",
        "watch": "가장 큰 모델링 리스크는 Microsoft platform power와 OpenAI model-owner power의 중복 계산이다. 따라서 CSP contract allocation sheet가 Microsoft와 OpenAI를 분리하는 핵심 control point다.",
    },
    "xAI": {
        "title": "xAI: 집중형 GPU buildout과 높은 serving leverage",
        "read": "xAI는 상대적으로 집중된 NVIDIA GPU fleet으로 모델링했다. TPU/Trainium처럼 custom accelerator 가정이 많이 개입되는 경우보다 계약 전력에서 accelerator unit과 HBM으로 이어지는 계산 경로가 더 투명하다. 현재 파일에서는 광범위한 CSP diversification보다는 active power ramp와 inference share 상승이 xAI의 token supply를 주로 움직인다.",
        "watch": "초기 ramp 구간에서는 training demand가 inference capacity를 밀어낼 수 있다. Grok traffic 또는 enterprise/API demand가 training cluster 재배치보다 빠르게 증가한다면, inference share가 가장 먼저 재검토해야 할 sensitivity다.",
    },
}


def fmt_num(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}"


def fmt_pct(value: float, digits: int = 0) -> str:
    return f"{value * 100:.{digits}f}%"


def qtokens(value: float) -> float:
    return value / 1e15


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def base_rows(data: dict[str, Any], year: int = 2030) -> list[dict[str, Any]]:
    return [row for row in data["forecast"] if row["year"] == year]


def estimate_hbm_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in data["ai_accelerator_power"]:
        if row["scenario"] != "Base":
            continue
        assumption = HBM_ASSUMPTIONS.get(row["accelerator_type"], HBM_ASSUMPTIONS["Other / unknown accelerator"])
        power_kw = row["all_in_kw_per_unit"] or assumption["power_kw_per_unit"]
        try:
            power_kw_f = float(power_kw)
        except (TypeError, ValueError):
            power_kw_f = assumption["power_kw_per_unit"]
        accelerator_power_mw = float(row["accelerator_power_mw"])
        accelerator_units = accelerator_power_mw * 1000 / power_kw_f if power_kw_f else 0.0
        hbm_gb = accelerator_units * assumption["hbm_gb_per_unit"]
        rows.append(
            {
                **row,
                "power_kw_per_unit_used": power_kw_f,
                "accelerator_units_estimated": accelerator_units,
                "hbm_gb_per_unit": assumption["hbm_gb_per_unit"],
                "hbm_pb": hbm_gb / 1_000_000,
                "hbm_24gb_stack_equiv_m": hbm_gb / 24 / 1_000_000,
                "hbm_basis": assumption["basis"],
                "hbm_confidence": assumption["confidence"],
            }
        )
    return rows


def aggregate_hbm_by_company(hbm_rows: list[dict[str, Any]], year: int = 2030) -> list[dict[str, Any]]:
    agg: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in hbm_rows:
        if row["year"] != year:
            continue
        company = row["company"]
        agg[company]["accelerator_power_mw"] += float(row["accelerator_power_mw"])
        agg[company]["accelerator_units_estimated"] += float(row["accelerator_units_estimated"])
        agg[company]["hbm_pb"] += float(row["hbm_pb"])
        agg[company]["hbm_24gb_stack_equiv_m"] += float(row["hbm_24gb_stack_equiv_m"])
    return [
        {"company": company, **values}
        for company, values in sorted(agg.items(), key=lambda item: item[1]["hbm_pb"], reverse=True)
    ]


def aggregate_hbm_by_year(hbm_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agg: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in hbm_rows:
        year = row["year"]
        agg[year]["accelerator_power_mw"] += float(row["accelerator_power_mw"])
        agg[year]["accelerator_units_estimated"] += float(row["accelerator_units_estimated"])
        agg[year]["hbm_pb"] += float(row["hbm_pb"])
        agg[year]["hbm_24gb_stack_equiv_m"] += float(row["hbm_24gb_stack_equiv_m"])
    return [{"year": year, **agg[year]} for year in sorted(agg)]


def aggregate_hbm_by_company_year(hbm_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agg: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in hbm_rows:
        key = (row["company"], row["year"])
        agg[key]["accelerator_power_mw"] += float(row["accelerator_power_mw"])
        agg[key]["accelerator_units_estimated"] += float(row["accelerator_units_estimated"])
        agg[key]["hbm_pb"] += float(row["hbm_pb"])
        agg[key]["hbm_24gb_stack_equiv_m"] += float(row["hbm_24gb_stack_equiv_m"])
    return [
        {"company": company, "year": year, **values}
        for (company, year), values in sorted(agg.items(), key=lambda item: (item[0][0], item[0][1]))
    ]


def hbm_lookup_by_company_year(hbm_rows: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, float]]:
    return {
        (row["company"], row["year"]): row
        for row in aggregate_hbm_by_company_year(hbm_rows)
    }


def base_company_year_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in data["forecast"]
        if row["scenario"] == "Base" and row["company"] in FOCUS_COMPANIES
    ]


def base_company_rows_by_name(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {company: [] for company in FOCUS_COMPANIES}
    for row in base_company_year_rows(data):
        grouped[row["company"]].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: row["year"])
    return grouped


def aggregate_base_market_by_year(data: dict[str, Any], hbm_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hbm_by_year = {row["year"]: row for row in aggregate_hbm_by_year(hbm_rows)}
    rows: list[dict[str, Any]] = []
    for year in sorted({row["year"] for row in data["forecast"] if row["scenario"] == "Base"}):
        forecast_rows = [row for row in data["forecast"] if row["scenario"] == "Base" and row["year"] == year]
        active_power_gw = sum(float(row["active_power_gw"]) for row in forecast_rows)
        contracted_power_gw = sum(float(row["contracted_power_gw"]) for row in forecast_rows)
        inference_gw = sum(float(row["inference_gw"]) for row in forecast_rows)
        training_gw = sum(float(row["training_gw"]) for row in forecast_rows)
        tokens_per_day = sum(float(row["inference_tokens_per_day"]) for row in forecast_rows)
        weighted_dcie = sum((1 / row["pue"]) * row["active_power_gw"] for row in forecast_rows) / max(active_power_gw, 1e-9)
        hbm = hbm_by_year.get(year, {})
        rows.append(
            {
                "year": year,
                "contracted_power_gw": contracted_power_gw,
                "active_power_gw": active_power_gw,
                "inference_gw": inference_gw,
                "training_gw": training_gw,
                "weighted_inference_share": inference_gw / max(inference_gw + training_gw, 1e-9),
                "weighted_dcie": weighted_dcie,
                "inference_tokens_per_day": tokens_per_day,
                "hbm_pb": float(hbm.get("hbm_pb", 0.0)),
                "hbm_24gb_stack_equiv_m": float(hbm.get("hbm_24gb_stack_equiv_m", 0.0)),
            }
        )
    return rows


def accelerator_mix_by_company_year(data: dict[str, Any], company: str) -> list[dict[str, Any]]:
    rows = [
        row for row in data["ai_accelerator_power"]
        if row["scenario"] == "Base" and row["company"] == company
    ]
    agg: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in rows:
        year = row["year"]
        accelerator_type = row["accelerator_type"]
        agg[year]["total_mw"] += float(row["accelerator_power_mw"])
        agg[year][accelerator_type] += float(row["accelerator_power_mw"])
    out: list[dict[str, Any]] = []
    for year, values in sorted(agg.items()):
        total = max(values["total_mw"], 1e-9)
        out.append(
            {
                "year": year,
                "h200_share": values.get("H100/H200/A100 class", 0.0) / total,
                "b200_share": values.get("B200/B300 class", 0.0) / total,
                "gb200_share": values.get("GB200/GB300 class", 0.0) / total,
                "purpose_built_share": sum(
                    values.get(name, 0.0)
                    for name in ["TPU", "Trainium", "Maia", "MTIA", "Ascend", "R200/R300 future", "Other / unknown accelerator"]
                ) / total,
            }
        )
    return out


def csp_mix_by_company_year(data: dict[str, Any], company: str) -> list[dict[str, Any]]:
    rows = [
        row for row in data["ai_csp_normalized_power"]
        if row["scenario"] == "Base" and row["company"] == company
    ]
    out: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda row: (row["year"], -row["normalized_csp_inference_power_mw"])):
        out.append(
            {
                "year": row["year"],
                "csp": row["csp"],
                "contract_share": row["ai_contract_share_of_csp"],
                "normalized_csp_share": row["normalized_csp_share"],
                "normalized_csp_inference_power_mw": row["normalized_csp_inference_power_mw"],
            }
        )
    return out


def aggregate_supplier_power_by_year(data: dict[str, Any], hbm_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_power: dict[tuple[str, int], float] = defaultdict(float)
    contract_power: dict[tuple[str, int], float] = defaultdict(float)
    contract_inference_weight: dict[tuple[str, int], float] = defaultdict(float)
    normalized_inference: dict[tuple[str, int], float] = defaultdict(float)
    hbm: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    accelerators: dict[tuple[str, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for row in data["csp_contract_allocations"]:
        if row["scenario"] != "Base":
            continue
        key = (row["csp"], row["year"])
        total_power[key] = max(total_power[key], float(row["csp_total_power_mw"]))
        contract_power[key] += float(row["ai_contract_power_mw"])
        contract_inference_weight[key] += float(row["contract_inference_weight_mw"])

    for row in data["ai_csp_normalized_power"]:
        if row["scenario"] != "Base":
            continue
        key = (row["csp"], row["year"])
        normalized_inference[key] += float(row["normalized_csp_inference_power_mw"])

    for row in hbm_rows:
        key = (row["csp"], row["year"])
        hbm[key]["accelerator_power_mw"] += float(row["accelerator_power_mw"])
        hbm[key]["accelerator_units_estimated"] += float(row["accelerator_units_estimated"])
        hbm[key]["hbm_pb"] += float(row["hbm_pb"])
        hbm[key]["hbm_24gb_stack_equiv_m"] += float(row["hbm_24gb_stack_equiv_m"])
        accelerators[key][row["accelerator_type"]] += float(row["accelerator_power_mw"])

    rows: list[dict[str, Any]] = []
    for key in sorted(total_power):
        csp, year = key
        total_mw = total_power[key]
        accelerator_total = max(hbm[key]["accelerator_power_mw"], 1e-9)
        rows.append(
            {
                "supplier": csp,
                "year": year,
                "supplier_scope": "legacy_company_envelope" if csp.startswith("Legacy company envelope") else "epoch_supplier",
                "csp_total_power_mw": total_mw,
                "ai_contract_power_mw": contract_power[key],
                "contract_power_utilization": contract_power[key] / max(total_mw, 1e-9),
                "contract_inference_weight_mw": contract_inference_weight[key],
                "normalized_supplier_inference_mw": normalized_inference[key],
                "accelerator_power_mw": hbm[key]["accelerator_power_mw"],
                "accelerator_units_estimated": hbm[key]["accelerator_units_estimated"],
                "hbm_pb": hbm[key]["hbm_pb"],
                "hbm_24gb_stack_equiv_m": hbm[key]["hbm_24gb_stack_equiv_m"],
                "h200_share": accelerators[key].get("H100/H200/A100 class", 0.0) / accelerator_total,
                "b200_share": accelerators[key].get("B200/B300 class", 0.0) / accelerator_total,
                "gb200_share": accelerators[key].get("GB200/GB300 class", 0.0) / accelerator_total,
                "purpose_built_share": sum(
                    accelerators[key].get(name, 0.0)
                    for name in ["TPU", "Trainium", "Maia", "MTIA", "Ascend", "R200/R300 future", "Other / unknown accelerator"]
                ) / accelerator_total,
            }
        )
    return rows


def supplier_customer_exposure_rows(data: dict[str, Any], year: int = 2030) -> list[dict[str, Any]]:
    totals: dict[str, float] = defaultdict(float)
    rows: list[dict[str, Any]] = []
    for row in data["ai_csp_normalized_power"]:
        if row["scenario"] != "Base" or row["year"] != year:
            continue
        supplier = row["csp"]
        totals[supplier] += float(row["normalized_csp_inference_power_mw"])
        rows.append(
            {
                "supplier": supplier,
                "company": row["company"],
                "year": year,
                "csp_total_power_mw": float(row["csp_total_power_mw"]),
                "ai_contract_power_mw": float(row["ai_contract_power_mw"]),
                "ai_contract_share_of_csp": float(row["ai_contract_share_of_csp"]),
                "normalized_supplier_inference_mw": float(row["normalized_csp_inference_power_mw"]),
            }
        )
    for row in rows:
        row["supplier_customer_inference_share"] = row["normalized_supplier_inference_mw"] / max(totals[row["supplier"]], 1e-9)
    return sorted(rows, key=lambda row: (row["supplier"], -row["normalized_supplier_inference_mw"], row["company"]))


def html_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def svg_line_chart(
    path: Path,
    title: str,
    series: dict[str, list[tuple[int, float]]],
    unit: str,
) -> str:
    width, height = 980, 520
    left, right, top, bottom = 74, 28, 74, 70
    chart_w = width - left - right
    chart_h = height - top - bottom
    years = sorted({year for values in series.values() for year, _ in values})
    min_year, max_year = min(years), max(years)
    max_value = max((value for values in series.values() for _, value in values), default=1.0)
    max_value = max(max_value, 1e-9)
    colors = ["#2563eb", "#dc2626", "#16a34a", "#7c3aed", "#ea580c", "#0891b2", "#475569"]

    def xy(year: int, value: float) -> tuple[float, float]:
        x = left + (year - min_year) / max(max_year - min_year, 1) * chart_w
        y = top + chart_h - (value / max_value) * chart_h
        return x, y

    items = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="28" y="38" font-family="Arial" font-size="22" font-weight="700" fill="#0f172a">{esc(title)}</text>',
        f'<text x="28" y="60" font-family="Arial" font-size="13" fill="#475569">Base scenario, 2026-2030. Unit: {esc(unit)}.</text>',
        f'<line x1="{left}" y1="{top + chart_h}" x2="{width - right}" y2="{top + chart_h}" stroke="#94a3b8"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="#94a3b8"/>',
    ]
    for year in years:
        x, _ = xy(year, 0)
        items.append(f'<text x="{x}" y="{height - 36}" font-family="Arial" font-size="12" fill="#334155" text-anchor="middle">{year}</text>')
        items.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + chart_h}" stroke="#e2e8f0"/>')
    for tick in range(5):
        value = max_value * tick / 4
        y = top + chart_h - (value / max_value) * chart_h
        items.append(f'<line x1="{left}" y1="{y}" x2="{width - right}" y2="{y}" stroke="#e2e8f0"/>')
        items.append(f'<text x="{left - 12}" y="{y + 4}" font-family="Arial" font-size="11" fill="#475569" text-anchor="end">{fmt_num(value, 2)}</text>')
    for idx, (name, values) in enumerate(series.items()):
        color = colors[idx % len(colors)]
        points = [xy(year, value) for year, value in sorted(values)]
        path_d = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points))
        items.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in points:
            items.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
        legend_x = 760
        legend_y = 94 + idx * 24
        items.append(f'<rect x="{legend_x}" y="{legend_y - 10}" width="12" height="12" fill="{color}"/>')
        items.append(f'<text x="{legend_x + 18}" y="{legend_y}" font-family="Arial" font-size="13" fill="#0f172a">{esc(name)}</text>')
    items.append("</svg>")
    svg = "\n".join(items)
    path.write_text(svg, encoding="utf-8")
    return svg


def top_csp_contract_rows(data: dict[str, Any], year: int = 2030, limit: int = 20) -> list[dict[str, Any]]:
    rows = [
        row for row in data["ai_csp_normalized_power"]
        if row["scenario"] == "Base" and row["year"] == year
    ]
    return sorted(rows, key=lambda row: row["normalized_csp_inference_power_mw"], reverse=True)[:limit]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def svg_bar_chart(path: Path, title: str, rows: list[dict[str, Any]], label_key: str, value_key: str, unit: str) -> str:
    width, height = 920, 520
    margin_left, margin_top = 190, 70
    row_h = 38
    max_v = max((float(row[value_key]) for row in rows), default=1.0)
    chart_w = width - margin_left - 70
    items = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="28" y="38" font-family="Arial" font-size="22" font-weight="700" fill="#0f172a">{esc(title)}</text>',
    ]
    for i, row in enumerate(rows[:10]):
        y = margin_top + i * row_h
        value = float(row[value_key])
        bar_w = chart_w * value / max_v if max_v else 0
        items.append(f'<text x="28" y="{y + 23}" font-family="Arial" font-size="14" fill="#334155">{esc(row[label_key])}</text>')
        items.append(f'<rect x="{margin_left}" y="{y + 6}" width="{bar_w:.1f}" height="22" rx="3" fill="#2563eb"/>')
        items.append(f'<text x="{margin_left + bar_w + 8:.1f}" y="{y + 23}" font-family="Arial" font-size="13" fill="#0f172a">{fmt_num(value, 2)} {esc(unit)}</text>')
    items.append("</svg>")
    svg = "\n".join(items)
    path.write_text(svg, encoding="utf-8")
    return svg


def svg_bubble_chart(path: Path, rows: list[dict[str, Any]], year: int = 2030) -> str:
    companies = sorted({row["company"] for row in rows})
    csps = sorted({row["csp"] for row in rows})
    width = max(980, 150 + len(csps) * 115)
    height = max(560, 120 + len(companies) * 64)
    left, top = 145, 92
    cell_w, cell_h = 110, 62
    max_mw = max((float(row["normalized_csp_inference_power_mw"]) for row in rows), default=1.0)
    color_map = {
        "OpenAI": "#2563eb",
        "Anthropic": "#dc2626",
        "Google": "#16a34a",
        "Microsoft": "#7c3aed",
        "Meta": "#0891b2",
        "xAI": "#ea580c",
    }
    items = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="28" y="38" font-family="Arial" font-size="22" font-weight="700" fill="#0f172a">CSP-to-LLM contract power normalization, Base {year}</text>',
        '<text x="28" y="62" font-family="Arial" font-size="13" fill="#475569">Bubble size = normalized CSP inference MW after applying CSP total power, AI contract share, and inference share.</text>',
    ]
    for i, csp in enumerate(csps):
        x = left + i * cell_w + cell_w / 2
        items.append(f'<text x="{x}" y="{top - 18}" font-family="Arial" font-size="12" fill="#334155" text-anchor="middle" transform="rotate(-35 {x} {top - 18})">{esc(csp)}</text>')
        items.append(f'<line x1="{x}" y1="{top - 5}" x2="{x}" y2="{height - 60}" stroke="#e2e8f0"/>')
    for j, company in enumerate(companies):
        y = top + j * cell_h + cell_h / 2
        items.append(f'<text x="28" y="{y + 5}" font-family="Arial" font-size="14" font-weight="700" fill="#0f172a">{esc(company)}</text>')
        items.append(f'<line x1="{left - 15}" y1="{y}" x2="{width - 45}" y2="{y}" stroke="#e2e8f0"/>')
    for row in rows:
        i = csps.index(row["csp"])
        j = companies.index(row["company"])
        x = left + i * cell_w + cell_w / 2
        y = top + j * cell_h + cell_h / 2
        mw = float(row["normalized_csp_inference_power_mw"])
        r = 5 + 28 * math.sqrt(mw / max_mw) if max_mw else 5
        color = color_map.get(row["company"], "#64748b")
        label = f"{mw:,.0f}MW"
        items.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{color}" fill-opacity="0.72" stroke="#0f172a" stroke-opacity="0.16"/>')
        if r > 15:
            items.append(f'<text x="{x}" y="{y + 4}" font-family="Arial" font-size="10" fill="#ffffff" text-anchor="middle">{esc(label)}</text>')
    items.append("</svg>")
    svg = "\n".join(items)
    path.write_text(svg, encoding="utf-8")
    return svg


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def write_report(data: dict[str, Any]) -> dict[str, Path]:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    hbm_rows = estimate_hbm_rows(data)
    hbm_company_2030 = aggregate_hbm_by_company(hbm_rows, 2030)
    hbm_company_year = aggregate_hbm_by_company_year(hbm_rows)
    hbm_company_year_lookup = hbm_lookup_by_company_year(hbm_rows)
    hbm_years = aggregate_hbm_by_year(hbm_rows)
    market_years = aggregate_base_market_by_year(data, hbm_rows)
    supplier_years = aggregate_supplier_power_by_year(data, hbm_rows)
    supplier_customer_2030 = supplier_customer_exposure_rows(data, 2030)
    forecast_2030 = sorted(base_rows(data, 2030), key=lambda row: row["inference_tokens_per_day"], reverse=True)
    focus_rows_by_company = base_company_rows_by_name(data)
    focus_timeseries_rows: list[dict[str, Any]] = []
    for company, rows in focus_rows_by_company.items():
        for row in rows:
            hbm = hbm_company_year_lookup.get((company, row["year"]), {})
            focus_timeseries_rows.append(
                {
                    "company": company,
                    "year": row["year"],
                    "contracted_power_gw": row["contracted_power_gw"],
                    "active_power_gw": row["active_power_gw"],
                    "inference_gw": row["inference_gw"],
                    "training_gw": row["training_gw"],
                    "inference_power_share": row["inference_power_share"],
                    "reference_serving_tps_per_mw": row["reference_serving_tps_per_mw"],
                    "inference_tokens_per_day_q": qtokens(row["inference_tokens_per_day"]),
                    "hbm_pb": hbm.get("hbm_pb", 0.0),
                }
            )
    contract_top_2026 = top_csp_contract_rows(data, 2026, 24)
    contract_top_2030 = top_csp_contract_rows(data, 2030, 24)
    csp_focus_rows: list[dict[str, Any]] = []
    for company in FOCUS_COMPANIES:
        csp_focus_rows.extend(csp_mix_by_company_year(data, company))
    scenario_summary = [row for row in data["scenario_summary"] if row["year"] == 2030]

    write_csv(OUT / f"{REPORT_STEM}_hbm_company_2030.csv", hbm_company_2030)
    write_csv(OUT / f"{REPORT_STEM}_hbm_company_year.csv", hbm_company_year)
    write_csv(OUT / f"{REPORT_STEM}_hbm_detail.csv", hbm_rows)
    write_csv(OUT / f"{REPORT_STEM}_focus_company_timeseries.csv", focus_timeseries_rows)
    write_csv(OUT / f"{REPORT_STEM}_base_market_timeseries.csv", market_years)
    write_csv(OUT / f"{REPORT_STEM}_supplier_power_timeseries.csv", supplier_years)
    write_csv(OUT / f"{REPORT_STEM}_supplier_customer_exposure_2030.csv", supplier_customer_2030)
    write_csv(OUT / f"{REPORT_STEM}_focus_csp_contract_timeseries.csv", csp_focus_rows)
    write_csv(OUT / f"{REPORT_STEM}_csp_contract_bubbles_2030.csv", contract_top_2030)

    token_svg = svg_bar_chart(
        CHART_DIR / "token_supply_2030.svg",
        "Generated output token supply by LLM owner, Base 2030",
        [{"company": row["company"], "tokens_q_day": qtokens(row["inference_tokens_per_day"])} for row in forecast_2030],
        "company",
        "tokens_q_day",
        "Q tokens/day",
    )
    hbm_svg = svg_bar_chart(
        CHART_DIR / "hbm_supply_2030.svg",
        "Power-derived HBM-equivalent demand by LLM owner, Base 2030",
        hbm_company_2030,
        "company",
        "hbm_pb",
        "PB HBM",
    )
    bubble_2026_svg = svg_bubble_chart(CHART_DIR / "csp_contract_bubble_2026.svg", contract_top_2026, 2026)
    bubble_2030_svg = svg_bubble_chart(CHART_DIR / "csp_contract_bubble_2030.svg", contract_top_2030, 2030)
    token_ts_svg = svg_line_chart(
        CHART_DIR / "token_supply_timeseries_focus.svg",
        "Generated output token supply by company",
        {
            company: [(row["year"], qtokens(row["inference_tokens_per_day"])) for row in rows]
            for company, rows in focus_rows_by_company.items()
        },
        "Q tokens/day",
    )
    inference_ts_svg = svg_line_chart(
        CHART_DIR / "inference_power_timeseries_focus.svg",
        "Operational inference power by company",
        {
            company: [(row["year"], row["inference_gw"]) for row in rows]
            for company, rows in focus_rows_by_company.items()
        },
        "GW",
    )
    hbm_ts_svg = svg_line_chart(
        CHART_DIR / "hbm_supply_timeseries_focus.svg",
        "Power-derived HBM-equivalent supply by company",
        {
            company: [
                (row["year"], hbm_company_year_lookup.get((company, row["year"]), {}).get("hbm_pb", 0.0))
                for row in rows
            ]
            for company, rows in focus_rows_by_company.items()
        },
        "PB",
    )
    top_suppliers_2030 = sorted(
        [row for row in supplier_years if row["year"] == 2030 and row["supplier_scope"] == "epoch_supplier"],
        key=lambda row: row["normalized_supplier_inference_mw"],
        reverse=True,
    )[:6]
    top_supplier_names = [row["supplier"] for row in top_suppliers_2030]
    supplier_power_ts_svg = svg_line_chart(
        CHART_DIR / "supplier_inference_power_timeseries.svg",
        "Supplier-side normalized inference power",
        {
            supplier: [
                (row["year"], row["normalized_supplier_inference_mw"] / 1000)
                for row in supplier_years
                if row["supplier"] == supplier
            ]
            for supplier in top_supplier_names
        },
        "GW",
    )

    total_2030 = sum(row["inference_tokens_per_day"] for row in forecast_2030)
    total_hbm_2030 = sum(row["hbm_pb"] for row in hbm_company_2030)
    total_hbm_stacks_2030 = sum(row["hbm_24gb_stack_equiv_m"] for row in hbm_company_2030)
    weighted_inference_gw = sum(row["inference_gw"] for row in forecast_2030)
    weighted_training_gw = sum(row["training_gw"] for row in forecast_2030)
    avg_dcie = sum((1 / row["pue"]) * row["active_power_gw"] for row in forecast_2030) / max(sum(row["active_power_gw"] for row in forecast_2030), 1e-9)

    def company_timeseries_table(company: str) -> list[str]:
        rows = focus_rows_by_company[company]
        return markdown_table(
            ["연도", "Contracted GW", "Active GW", "Inference GW", "Training GW", "Inf. share", "TPS/MW", "Tokens/day", "HBM PB"],
            [
                [
                    str(row["year"]),
                    fmt_num(row["contracted_power_gw"], 2),
                    fmt_num(row["active_power_gw"], 2),
                    fmt_num(row["inference_gw"], 2),
                    fmt_num(row["training_gw"], 2),
                    fmt_pct(row["inference_power_share"], 0),
                    fmt_num(row["reference_serving_tps_per_mw"], 0),
                    f"{fmt_num(qtokens(row['inference_tokens_per_day']), 4)}Q",
                    fmt_num(hbm_company_year_lookup.get((company, row["year"]), {}).get("hbm_pb", 0.0), 2),
                ]
                for row in rows
            ],
        )

    def company_accelerator_table(company: str) -> list[str]:
        return markdown_table(
            ["연도", "H200/A100/H100", "B200/B300", "GB200/GB300", "Purpose/custom/future"],
            [
                [
                    str(row["year"]),
                    fmt_pct(row["h200_share"], 1),
                    fmt_pct(row["b200_share"], 1),
                    fmt_pct(row["gb200_share"], 1),
                    fmt_pct(row["purpose_built_share"], 1),
                ]
                for row in accelerator_mix_by_company_year(data, company)
            ],
        )

    def company_csp_table(company: str) -> list[str]:
        rows = csp_mix_by_company_year(data, company)
        top_rows = [row for row in rows if row["year"] in [2026, 2030]]
        return markdown_table(
            ["연도", "CSP", "CSP contract share", "Normalized share", "Inference MW"],
            [
                [
                    str(row["year"]),
                    row["csp"],
                    fmt_pct(row["contract_share"], 1),
                    fmt_pct(row["normalized_csp_share"], 1),
                    fmt_num(row["normalized_csp_inference_power_mw"], 0),
                ]
                for row in top_rows
            ],
        )

    lines: list[str] = [
        "# 전력 기반 LLM 토큰 처리량 및 HBM 공급량 리포트",
        "",
        f"_생성일: {RUN_DATE}. 범위: 주요 상용 LLM 사업자, 2026-2030년, Base/Bear/Bull 시나리오 모델._",
        "",
        "## Executive Summary",
        "",
        f"Base case 기준으로 모델링 대상 LLM 사업자의 active AI power는 **2026년 {fmt_num(market_years[0]['active_power_gw'], 1)} GW**에서 **2030년 {fmt_num(market_years[-1]['active_power_gw'], 1)} GW**로 확대된다. 이 중 token generation으로 직접 연결되는 inference power는 **{fmt_num(market_years[0]['inference_gw'], 1)} GW**에서 **{fmt_num(weighted_inference_gw, 1)} GW**로 증가하며, 2030년에도 training/reserve power가 **{fmt_num(weighted_training_gw, 1)} GW**로 의미 있게 남아 있다.",
        "",
        f"Generated-output token supply는 2030년에 **{fmt_num(qtokens(total_2030), 2)} quadrillion tokens/day**까지 증가한다. 다만 이 리포트에서 더 중요한 것은 2030년 단일 값이 아니라 slope다. 2026년은 capacity buildout 초기 단계이고, 2029-2030년으로 갈수록 fleet이 inference 중심으로 재배치되는 구조다. 전력 기반 HBM-equivalent demand는 2030년에 **{fmt_num(total_hbm_2030, 1)} PB**, 즉 **24GB HBM stack-equivalent {fmt_num(total_hbm_stacks_2030, 2)} million개** 수준으로 계산된다.",
        "",
        f"2030년 weighted DCiE는 **{fmt_pct(avg_dcie, 1)}**다. DCiE는 `1/PUE`로, facility power를 IT-deliverable power로 변환하는 값이지 accelerator-only utilization은 아니다. 따라서 가장 큰 불확실성은 계산식 자체보다 대체 입력 데이터에 있다. 특히 AI company별 CSP contract allocation, 연도별 accelerator procurement mix, production short/long/agentic traffic share, 실제 serving tokens/MW가 핵심 replacement data다.",
        "",
        "## Methodology",
        "",
        "```text",
        "CSP contract inference weight = CSP total AI power MW * AI-company contract share of CSP * inference share",
        "Normalized CSP inference power = AI-company inference MW * CSP contract inference weight / sum(company CSP contract inference weights)",
        "AI accelerator power = normalized CSP inference power * CSP accelerator share",
        "Fleet TPS/MW = H200 share*H200 workload TPS/MW + B200 share*B200 workload TPS/MW + GB200 share*GB200 workload TPS/MW + unbenchmarked share*placeholder TPS/MW",
        "Output tokens/day = inference GW * 1,000 * serving TPS/MW * 86,400",
        "HBM-equivalent PB = accelerator power MW * 1,000 / all-in kW per unit * HBM GB per unit / 1,000,000",
        "```",
        "",
        "## 2026-2030 Market Time Series",
        "",
        "아래 표가 전체 리포트의 핵심 readout이다. 2030년 endpoint만 보는 것이 아니라 2026-2030년의 capacity ramp를 그대로 보여준다. Contracted GW는 중장기 계약 전력 envelope, Active GW는 실제 energization/available power, Inference GW는 token throughput으로 환산되는 전력이다.",
        "",
    ]
    lines += markdown_table(
        ["연도", "Contracted GW", "Active GW", "Inference GW", "Training GW", "Inference share", "DCiE", "Tokens/day", "HBM PB"],
        [
            [
                str(row["year"]),
                fmt_num(row["contracted_power_gw"], 1),
                fmt_num(row["active_power_gw"], 1),
                fmt_num(row["inference_gw"], 1),
                fmt_num(row["training_gw"], 1),
                fmt_pct(row["weighted_inference_share"], 1),
                fmt_pct(row["weighted_dcie"], 1),
                f"{fmt_num(qtokens(row['inference_tokens_per_day']), 3)}Q",
                fmt_num(row["hbm_pb"], 1),
            ]
            for row in market_years
        ],
    )
    lines += [
        "",
        f"![Token supply time series](charts/{REPORT_STEM}/token_supply_timeseries_focus.svg)",
        "",
        f"![Inference power time series](charts/{REPORT_STEM}/inference_power_timeseries_focus.svg)",
        "",
        f"![HBM time series](charts/{REPORT_STEM}/hbm_supply_timeseries_focus.svg)",
        "",
        "## Contract Power, DCiE And Training/Inference Split",
        "",
    ]
    lines += markdown_table(
        ["회사", "Contracted GW", "Operational GW", "DCiE", "Inference GW", "Training GW", "Inference share", "Tokens/day"],
        [
            [
                row["company"],
                fmt_num(row["contracted_power_gw"], 1),
                fmt_num(row["active_power_gw"], 1),
                fmt_pct(1 / row["pue"], 1),
                fmt_num(row["inference_gw"], 1),
                fmt_num(row["training_gw"], 1),
                fmt_pct(row["inference_power_share"], 0),
                f"{fmt_num(qtokens(row['inference_tokens_per_day']), 3)}Q",
            ]
            for row in forecast_2030
        ],
    )
    lines += [
        "",
        "## CSP Contract Normalization",
        "",
        "CSP allocation logic은 각 CSP의 total AI power에서 시작해 해당 CSP 안에서 특정 AI company가 계약한 share를 곱한다. 이후 inference/training split을 적용하고, 그 weight를 AI company의 자체 inference GW로 다시 정규화한다. 이 방식은 예를 들어 OpenAI의 1 GW를 단일 generic accelerator pool처럼 처리하지 않고, Microsoft/Oracle/CoreWeave 등 각 공급자의 accelerator mix로 나누어 해석하게 해준다.",
        "",
        "Bubble chart는 시각적 비교를 위한 snapshot이다. 세부 판단은 아래 회사별 섹션의 2026년 및 2030년 CSP-normalized table을 함께 보는 것이 좋다.",
        "",
        f"![CSP contract bubble 2026](charts/{REPORT_STEM}/csp_contract_bubble_2026.svg)",
        "",
        f"![CSP contract bubble 2030](charts/{REPORT_STEM}/csp_contract_bubble_2030.svg)",
        "",
        "## InferenceX Benchmark Proxy",
        "",
        "InferenceX는 public serving benchmark proxy로 사용했으며, production telemetry로 간주하지 않는다. 모델은 proxy model, GPU, precision, ISL/OSL, concurrency, serving stack별 generated-output TPS/MW를 선택한 뒤 commercial workload fit factor를 적용한다. 실제 traffic에는 latency SLO, routing overhead, model mix, reserve capacity가 들어가기 때문이다.",
        "",
        "Workload layer는 다음 세 가지로 명시적으로 분리했다.",
        "",
        "- **Short conversation:** ISL/OSL 1,024/1,024 성격의 row로, 일반 assistant turn에 가깝다.",
        "- **Long conversation:** ISL/OSL 8,192/1,024 성격의 row로, long-context RAG, 요약, enterprise context에 가깝다.",
        "- **Agentic:** dynamic reasoning/tool-use proxy다. 직접 관측 데이터가 아직 적기 때문에 long-context derivative로 보수적으로 처리했다.",
        "",
    ]
    lines += markdown_table(
        ["회사", "Proxy", "Short", "Long", "Agentic", "Fleet ref TPS/MW", "Fit", "Serving TPS/MW", "Confidence"],
        [
            [
                row["company"],
                row["gpu_benchmark_proxy_model"],
                fmt_pct(row["short_chat_share"], 0),
                fmt_pct(row["long_chat_share"], 0),
                fmt_pct(row["agentic_share"], 0),
                fmt_num(row["fleet_reference_tps_per_mw"], 0),
                fmt_pct(row["commercial_workload_fit_factor"], 0),
                fmt_num(row["reference_serving_tps_per_mw"], 0),
                row["confidence"],
            ]
            for row in forecast_2030
        ],
    )
    lines += [
        "",
        "## Token Supply Result",
        "",
        f"![Token supply](charts/{REPORT_STEM}/token_supply_2030.svg)",
        "",
    ]
    lines += markdown_table(
        ["Scenario", "2030 tokens/day", "Active GW", "Inference GW", "Weighted inference share"],
        [
            [
                row["scenario"],
                f"{fmt_num(row['inference_tokens_per_day_q'], 3)}Q",
                fmt_num(row["active_power_gw"], 1),
                fmt_num(row["inference_gw"], 1),
                fmt_pct(row["weighted_inference_share"], 1),
            ]
            for row in sorted(scenario_summary, key=lambda row: row["inference_tokens_per_day"], reverse=True)
        ],
    )
    lines += [
        "",
        "## Company Detail Sections",
        "",
        "아래 회사별 섹션은 단순 데이터 표가 아니라 읽는 리포트 형식으로 구성했다. 각 회사마다 power envelope, active ramp, inference split, workload proxy, accelerator mix, HBM implication이 한 번에 보이도록 했다.",
        "",
    ]
    for company in FOCUS_COMPANIES:
        rows = focus_rows_by_company[company]
        first, last = rows[0], rows[-1]
        hbm_first = hbm_company_year_lookup.get((company, first["year"]), {}).get("hbm_pb", 0.0)
        hbm_last = hbm_company_year_lookup.get((company, last["year"]), {}).get("hbm_pb", 0.0)
        read = COMPANY_READS[company]
        lines += [
            f"### {read['title']}",
            "",
            read["read"],
            "",
            f"2026년에서 2030년까지 contracted power는 **{fmt_num(first['contracted_power_gw'], 2)} GW**에서 **{fmt_num(last['contracted_power_gw'], 2)} GW**로, active power는 **{fmt_num(first['active_power_gw'], 2)} GW**에서 **{fmt_num(last['active_power_gw'], 2)} GW**로 증가한다. 모델링된 inference power는 **{fmt_num(first['inference_gw'], 2)} GW**에서 **{fmt_num(last['inference_gw'], 2)} GW**로 확대된다. Token estimate는 **{fmt_num(qtokens(first['inference_tokens_per_day']), 4)}Q tokens/day**에서 **{fmt_num(qtokens(last['inference_tokens_per_day']), 4)}Q tokens/day**로 증가하며, HBM-equivalent demand는 **{fmt_num(hbm_first, 2)} PB**에서 **{fmt_num(hbm_last, 2)} PB**로 올라간다.",
            "",
            read["watch"],
            "",
            "**회사별 시계열**",
            "",
        ]
        lines += company_timeseries_table(company)
        lines += [
            "",
            "**모델링된 inference power 기준 accelerator mix**",
            "",
        ]
        lines += company_accelerator_table(company)
        lines += [
            "",
            "**CSP-normalized inference power, 2026년 및 2030년**",
            "",
        ]
        lines += company_csp_table(company)
        lines += [
            "",
        ]
    lines += [
        "## Power-Based HBM Supply Implication",
        "",
        "HBM demand는 token volume에서 직접 산출하지 않고 accelerator power에서 추정한다. 이렇게 하면 고정된 HBM-per-token 관계를 가정하지 않아도 된다. 계산은 accelerator power를 all-in kW/unit으로 나누어 accelerator unit을 추정한 뒤, HBM GB/unit을 곱하는 방식이다. Benchmark가 없는 custom accelerator는 HBM과 all-in power를 명시적인 placeholder로 둔다.",
        "",
        f"![HBM supply](charts/{REPORT_STEM}/hbm_supply_2030.svg)",
        "",
    ]
    lines += markdown_table(
        ["Company", "Accelerator MW", "Units est.", "HBM PB", "24GB stack-equiv."],
        [
            [
                row["company"],
                fmt_num(row["accelerator_power_mw"], 0),
                fmt_num(row["accelerator_units_estimated"], 0),
                fmt_num(row["hbm_pb"], 2),
                f"{fmt_num(row['hbm_24gb_stack_equiv_m'], 3)}M",
            ]
            for row in hbm_company_2030
        ],
    )
    lines += [
        "",
        "### HBM Assumption Table",
        "",
    ]
    lines += markdown_table(
        ["Accelerator", "kW/unit", "HBM GB/unit", "Confidence", "Basis"],
        [
            [
                name,
                fmt_num(values["power_kw_per_unit"], 2),
                fmt_num(values["hbm_gb_per_unit"], 0),
                values["confidence"],
                values["basis"],
            ]
            for name, values in HBM_ASSUMPTIONS.items()
        ],
    )
    lines += [
        "",
        "## Replacement Data Path",
        "",
        "1. `02a_CSP_Contract_Alloc`의 CSP total AI power와 AI-company contract share를 실제 중장기 계약 dataset으로 교체한다.",
        "2. `02b_CSP_Accelerator_Mix`의 CSP accelerator mix를 연도별 procurement/build plan share로 교체한다.",
        "3. 신규 accelerator는 `02x_Accelerator_Catalog`에 benchmark bucket, all-in power, HBM GB/unit을 추가하면 확장된다.",
        "4. InferenceX 또는 production telemetry에서 비교 가능한 output-token row가 확보되면 unbenchmarked accelerator TPS/MW placeholder를 교체한다.",
        "5. 회사별 traffic telemetry가 확보되면 short/long/agentic workload share를 product surface별로 분리한다.",
        "",
        "## Sources",
        "",
    ]
    lines += [f"- {source['id']}: {source['use']} {source['url']}" for source in SOURCES]
    lines += [
        "",
        "## Caveats",
        "",
        "- 이 결과는 scenario model이며, 각 회사가 공개한 production telemetry가 아니다.",
        "- DCiE/PUE는 facility power를 IT power로 변환하는 값이며 accelerator utilization을 의미하지 않는다.",
        "- TPU, Trainium, Maia, MTIA, Ascend 및 future Rubin-class row의 HBM 추정치는 세대별 all-in power와 HBM disclosure가 들어오기 전까지 placeholder다.",
        "- InferenceX public row는 benchmark reference다. 실제 production serving은 SLO, traffic burstiness, cache hit rate, prefill/decode scheduling, software stack에 따라 달라진다.",
        "",
    ]

    def latest_accelerator_mix_sentence(company: str) -> str:
        mixes = accelerator_mix_by_company_year(data, company)
        if not mixes:
            return "accelerator mix는 현재 입력 데이터에서 별도 분해가 필요하다."
        mix = mixes[-1]
        return (
            f"2030년 inference power 기준 accelerator mix는 H200/A100/H100 {fmt_pct(mix['h200_share'], 1)}, "
            f"B200/B300 {fmt_pct(mix['b200_share'], 1)}, GB200/GB300 {fmt_pct(mix['gb200_share'], 1)}, "
            f"purpose-built/custom/future {fmt_pct(mix['purpose_built_share'], 1)}로 모델링된다."
        )

    def csp_concentration_sentence(company: str) -> str:
        rows = [row for row in csp_mix_by_company_year(data, company) if row["year"] == 2030]
        if not rows:
            return "2030년 CSP-normalized inference power는 별도 입력이 필요하다."
        top = rows[:3]
        parts = [
            f"{row['csp']} {fmt_pct(row['normalized_csp_share'], 1)}"
            for row in top
        ]
        return f"2030년 CSP-normalized inference power는 {' / '.join(parts)} 순으로 크다."

    def company_narrative(company: str) -> list[str]:
        rows = focus_rows_by_company[company]
        first, mid, last = rows[0], rows[len(rows) // 2], rows[-1]
        hbm_first = hbm_company_year_lookup.get((company, first["year"]), {}).get("hbm_pb", 0.0)
        hbm_last = hbm_company_year_lookup.get((company, last["year"]), {}).get("hbm_pb", 0.0)
        read = COMPANY_READS[company]
        return [
            f"### {read['title']}",
            "",
            read["read"],
            "",
            (
                f"Capacity ramp는 2026년 active power {fmt_num(first['active_power_gw'], 2)} GW에서 "
                f"2028년 {fmt_num(mid['active_power_gw'], 2)} GW, 2030년 {fmt_num(last['active_power_gw'], 2)} GW로 이어진다. "
                f"같은 기간 inference power는 {fmt_num(first['inference_gw'], 2)} GW에서 "
                f"{fmt_num(last['inference_gw'], 2)} GW로 증가한다. 이 변화는 단순한 설비 증설만이 아니라 "
                f"training 중심 buildout에서 serving 중심 운영으로 이동하는 효과를 함께 반영한다."
            ),
            "",
            (
                f"Token supply는 2026년 {fmt_num(qtokens(first['inference_tokens_per_day']), 4)}Q/day에서 "
                f"2030년 {fmt_num(qtokens(last['inference_tokens_per_day']), 4)}Q/day로 증가한다. "
                f"HBM-equivalent demand는 같은 기간 {fmt_num(hbm_first, 2)} PB에서 {fmt_num(hbm_last, 2)} PB로 늘어난다. "
                f"{latest_accelerator_mix_sentence(company)} {csp_concentration_sentence(company)}"
            ),
            "",
            read["watch"],
            "",
        ]

    top_token_company = forecast_2030[0]
    base_2026, base_2030 = market_years[0], market_years[-1]
    epoch_supplier_2026 = [row for row in supplier_years if row["year"] == 2026 and row["supplier_scope"] == "epoch_supplier"]
    epoch_supplier_2030 = [row for row in supplier_years if row["year"] == 2030 and row["supplier_scope"] == "epoch_supplier"]
    supplier_inference_2026 = sum(row["normalized_supplier_inference_mw"] for row in epoch_supplier_2026) / 1000
    supplier_inference_2030 = sum(row["normalized_supplier_inference_mw"] for row in epoch_supplier_2030) / 1000
    supplier_total_power_2030 = sum(row["csp_total_power_mw"] for row in epoch_supplier_2030) / 1000
    supplier_contract_power_2030 = sum(row["ai_contract_power_mw"] for row in epoch_supplier_2030) / 1000

    def supplier_customer_sentence(supplier: str) -> str:
        rows = [row for row in supplier_customer_2030 if row["supplier"] == supplier]
        if not rows:
            return "2030년 customer exposure는 현재 입력 데이터에서 별도 분해가 필요하다."
        parts = [
            f"{row['company']} {fmt_pct(row['supplier_customer_inference_share'], 1)}"
            for row in rows[:3]
        ]
        return f"2030년 normalized inference exposure는 {' / '.join(parts)} 순이다."

    def supplier_accelerator_sentence(row: dict[str, Any]) -> str:
        return (
            f"Accelerator mix는 H200/A100/H100 {fmt_pct(row['h200_share'], 1)}, "
            f"B200/B300 {fmt_pct(row['b200_share'], 1)}, GB200/GB300 {fmt_pct(row['gb200_share'], 1)}, "
            f"purpose-built/custom/future {fmt_pct(row['purpose_built_share'], 1)}로 계산된다."
        )

    def supplier_narrative(row: dict[str, Any]) -> list[str]:
        supplier = row["supplier"]
        history = [item for item in supplier_years if item["supplier"] == supplier and item["supplier_scope"] == "epoch_supplier"]
        first = history[0]
        return [
            f"### {supplier}",
            "",
            (
                f"{supplier}의 공급자 관점 power는 user별 LLM owner power를 다시 CSP side로 돌려 본 값이다. "
                f"2026년 normalized supplier inference power는 {fmt_num(first['normalized_supplier_inference_mw'] / 1000, 2)} GW였고, "
                f"2030년에는 {fmt_num(row['normalized_supplier_inference_mw'] / 1000, 2)} GW로 증가한다. "
                f"2030년 CSP total AI power seed는 {fmt_num(row['csp_total_power_mw'] / 1000, 2)} GW, "
                f"AI-company contract power 합계는 {fmt_num(row['ai_contract_power_mw'] / 1000, 2)} GW다."
            ),
            "",
            (
                f"{supplier_customer_sentence(supplier)} {supplier_accelerator_sentence(row)} "
                f"HBM-equivalent demand는 2030년 {fmt_num(row['hbm_pb'], 2)} PB로 추정된다. "
                "이 값은 해당 공급자의 capacity가 어느 AI user로 흘러가는지와 그 공급자의 accelerator mix가 무엇인지에 의해 결정된다."
            ),
            "",
        ]

    narrative_lines: list[str] = [
        "# 전력 기반 LLM 토큰 처리량 및 HBM 공급량 분석 리포트",
        "",
        f"_작성일: {RUN_DATE}. 범위: 주요 상용 LLM 사업자, 2026-2030년 Base/Bear/Bull 시나리오. 상세 테이블은 대시보드/CSV 산출물로 분리._",
        "",
        "## Executive Summary",
        "",
        (
            f"AI datacenter 전력은 더 이상 단순한 capacity headline으로만 해석하기 어렵다. 본 모델의 Base case에서 "
            f"covered LLM owner들의 active AI power는 2026년 {fmt_num(base_2026['active_power_gw'], 1)} GW에서 "
            f"2030년 {fmt_num(base_2030['active_power_gw'], 1)} GW로 확대된다. 그러나 토큰 공급량을 결정하는 것은 "
            f"gross GW가 아니라 DCiE를 거친 IT power, training/inference split, CSP별 계약 비중, accelerator mix, "
            f"그리고 workload별 TPS/MW다."
        ),
        "",
        (
            f"2030년 Base case의 generated-output token supply는 {fmt_num(qtokens(total_2030), 2)}Q tokens/day다. "
            f"동시에 inference power는 {fmt_num(weighted_inference_gw, 1)} GW, training/reserve power는 "
            f"{fmt_num(weighted_training_gw, 1)} GW로 계산된다. 이 구조는 2026년 buildout 초기에는 training과 reserve가 "
            f"크게 남아 있지만, 2029-2030년으로 갈수록 inference allocation이 빠르게 커지는 형태다."
        ),
        "",
        (
            f"HBM 관점에서는 2030년 power-derived HBM-equivalent demand가 {fmt_num(total_hbm_2030, 1)} PB, "
            f"24GB stack-equivalent 기준 {fmt_num(total_hbm_stacks_2030, 2)} million개에 이른다. 이 값은 "
            f"token volume에서 직접 역산한 것이 아니라, normalized accelerator power를 all-in kW/unit과 HBM GB/unit으로 "
            f"환산한 결과다. 따라서 HBM 공급량 논의에서는 토큰 수요보다 accelerator procurement mix가 더 직접적인 driver다."
        ),
        "",
        "## 분석 프레임워크",
        "",
        (
            "본 리포트는 세 개의 층으로 전력 기반 토큰 공급량을 산출한다. 첫째, datacenter와 CSP 계약 전력을 AI company별 "
            "가용 inference power로 정규화한다. 둘째, 각 CSP가 보유하거나 build할 accelerator mix를 적용해 H200, B200, "
            "GB200, TPU, Trainium 등으로 전력을 분해한다. 셋째, InferenceX public benchmark를 short, long, agentic "
            "workload proxy로 나누어 TPS/MW를 부여하고 commercial workload fit factor를 적용한다."
        ),
        "",
        "```text",
        "Output tokens/day = inference GW * 1,000 * serving TPS/MW * 86,400",
        "HBM-equivalent PB = accelerator MW * 1,000 / all-in kW per unit * HBM GB per unit / 1,000,000",
        "```",
        "",
        (
            f"Weighted DCiE는 2030년 {fmt_pct(avg_dcie, 1)} 수준으로 계산된다. DCiE는 `1/PUE`이므로 facility power를 "
            "IT-deliverable power로 바꾸는 변환 계수다. 이는 accelerator utilization이 아니며, 실제 serving 효율은 "
            "latency SLO, prefill/decode scheduling, cache hit rate, concurrency, model routing에 의해 다시 조정된다."
        ),
        "",
        "## 2026-2030년 전력과 토큰 공급량의 변화",
        "",
        (
            f"Base case에서 contracted power envelope는 2026년 {fmt_num(base_2026['contracted_power_gw'], 1)} GW에서 "
            f"2030년 {fmt_num(base_2030['contracted_power_gw'], 1)} GW로 확대된다. Active power는 같은 기간 "
            f"{fmt_num(base_2026['active_power_gw'], 1)} GW에서 {fmt_num(base_2030['active_power_gw'], 1)} GW로 증가한다. "
            f"더 중요한 변화는 inference share다. Inference power는 {fmt_num(base_2026['inference_gw'], 1)} GW에서 "
            f"{fmt_num(base_2030['inference_gw'], 1)} GW로 커지고, weighted inference share는 "
            f"{fmt_pct(base_2026['weighted_inference_share'], 1)}에서 {fmt_pct(base_2030['weighted_inference_share'], 1)}로 상승한다."
        ),
        "",
        (
            f"토큰 공급량은 2026년 {fmt_num(qtokens(base_2026['inference_tokens_per_day']), 3)}Q/day에서 "
            f"2030년 {fmt_num(qtokens(base_2030['inference_tokens_per_day']), 3)}Q/day로 증가한다. 이 증가율은 단순 power ramp보다 크다. "
            "전력이 증가하는 동시에 B200/GB200급 accelerator 비중이 높아지고, 일부 사업자는 commercial serving mix가 "
            "더 높은 TPS/MW proxy로 이동하기 때문이다."
        ),
        "",
        f"![Token supply time series](charts/{REPORT_STEM}/token_supply_timeseries_focus.svg)",
        "",
        f"![Inference power time series](charts/{REPORT_STEM}/inference_power_timeseries_focus.svg)",
        "",
        "## 공급자 관점: Epoch AI capacity를 CSP side로 다시 읽기",
        "",
        (
            "기존 user 관점은 OpenAI, Anthropic, Google, Microsoft, xAI 같은 LLM owner가 확보한 전력과 token supply를 보여준다. "
            "반대로 공급자 관점은 같은 전력을 Microsoft, Oracle, Amazon, Google, CoreWeave, SpaceXAI 같은 CSP/datacenter provider가 "
            "어떤 AI user에게 공급하는지 보여준다. 이 관점은 HBM과 accelerator procurement를 추정할 때 특히 중요하다. "
            "HBM 수요는 최종 user의 token volume보다 공급자 fleet의 accelerator mix에 더 직접적으로 연결되기 때문이다."
        ),
        "",
        (
            f"Epoch 기반 supplier scope만 보면, normalized supplier inference power는 2026년 {fmt_num(supplier_inference_2026, 2)} GW에서 "
            f"2030년 {fmt_num(supplier_inference_2030, 2)} GW로 증가한다. 2030년 supplier-side total AI power seed는 "
            f"{fmt_num(supplier_total_power_2030, 2)} GW이고, AI-company contract power 합계는 {fmt_num(supplier_contract_power_2030, 2)} GW다. "
            "여기에는 Epoch attribution이 충분하지 않아 legacy company envelope로 보완된 row는 제외했다."
        ),
        "",
        f"![Supplier inference power time series](charts/{REPORT_STEM}/supplier_inference_power_timeseries.svg)",
        "",
    ]
    for row in top_suppliers_2030[:5]:
        narrative_lines.extend(supplier_narrative(row))
    narrative_lines.extend([
        "## 기업별 분석",
        "",
    ])
    for company in FOCUS_COMPANIES:
        narrative_lines.extend(company_narrative(company))
    narrative_lines.extend(
        [
            "## Benchmark Proxy와 해석상 주의점",
            "",
            (
                "InferenceX는 production telemetry가 아니라 public serving benchmark proxy다. 따라서 본 모델은 benchmark를 "
                "그대로 매출 또는 실제 production token으로 보지 않는다. Short conversation, long conversation, agentic workload를 "
                "분리하고, 각 company별 traffic 성격에 따라 workload share와 commercial fit factor를 적용한다."
            ),
            "",
            (
                "특히 agentic workload는 현재 공개 benchmark data가 상대적으로 부족하다. 본 모델에서는 long-context 및 dynamic reasoning "
                "proxy를 사용하되, direct evidence가 적은 영역이라는 점을 명시적으로 낮은 confidence로 남긴다. 향후 agentic traces가 더 축적되면 "
                "short/long/agentic 간 TPS/MW 비율은 가장 먼저 업데이트해야 하는 입력이다."
            ),
            "",
            "## HBM 공급량 관점의 시사점",
            "",
            (
                f"HBM-equivalent demand는 2026년 {fmt_num(base_2026['hbm_pb'], 1)} PB에서 2030년 "
                f"{fmt_num(base_2030['hbm_pb'], 1)} PB로 증가한다. 이 값은 token volume의 함수라기보다 accelerator unit 수의 함수에 가깝다. "
                "따라서 HBM 공급량을 추정할 때는 AI company의 토큰 처리량만 보는 것보다, CSP별 accelerator mix와 세대별 all-in power, "
                "HBM GB/unit을 함께 보는 것이 더 정확하다."
            ),
            "",
            f"![HBM time series](charts/{REPORT_STEM}/hbm_supply_timeseries_focus.svg)",
            "",
            "## 결론",
            "",
            (
                "전력 기반 token capacity 모델은 AI datacenter headline을 LLM 공급량으로 번역하는 중간 언어다. 계약 전력은 시작점이지만, "
                "실제 token supply는 CSP 계약 attribution, DCiE, inference share, accelerator mix, serving benchmark proxy가 "
                "결합될 때 비로소 해석 가능하다. 본 리포트의 목적은 특정 2030년 숫자를 고정된 예측치로 제시하는 것이 아니라, 각 입력값이 "
                "토큰 공급량과 HBM 수요를 어떤 방향으로 움직이는지 설명하는 것이다."
            ),
            "",
            "## 데이터 산출물",
            "",
            f"- 전체 시장 시계열 CSV: `{REPORT_STEM}_base_market_timeseries.csv`",
            f"- 5개 focus company 시계열 CSV: `{REPORT_STEM}_focus_company_timeseries.csv`",
            f"- 공급자/CSP 관점 전력 시계열 CSV: `{REPORT_STEM}_supplier_power_timeseries.csv`",
            f"- 공급자별 AI user exposure CSV: `{REPORT_STEM}_supplier_customer_exposure_2030.csv`",
            f"- CSP 계약 정규화 시계열 CSV: `{REPORT_STEM}_focus_csp_contract_timeseries.csv`",
            f"- 회사/연도별 HBM CSV: `{REPORT_STEM}_hbm_company_year.csv`",
            f"- 세부 accelerator power/HBM CSV: `{REPORT_STEM}_hbm_detail.csv`",
            "",
            "## Sources And Caveats",
            "",
        ]
    )
    narrative_lines += [f"- {source['id']}: {source['use']} {source['url']}" for source in SOURCES]
    narrative_lines += [
        "",
        "- 이 결과는 scenario model이며 각 회사의 disclosed production telemetry가 아니다.",
        "- Custom accelerator의 HBM 및 TPS/MW는 generation-specific disclosure가 확보되기 전까지 placeholder다.",
        "- InferenceX public benchmark는 비교 가능한 proxy로 사용했으며, real serving은 SLO, concurrency, cache, routing, prefill/decode scheduling에 따라 달라질 수 있다.",
        "",
    ]
    lines = narrative_lines
    md_path = OUT / f"{REPORT_STEM}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    html_market_table = html_table(
        ["연도", "Contracted GW", "Active GW", "Inference GW", "Training GW", "Inference share", "DCiE", "Tokens/day", "HBM PB"],
        [
            [
                str(row["year"]),
                fmt_num(row["contracted_power_gw"], 1),
                fmt_num(row["active_power_gw"], 1),
                fmt_num(row["inference_gw"], 1),
                fmt_num(row["training_gw"], 1),
                fmt_pct(row["weighted_inference_share"], 1),
                fmt_pct(row["weighted_dcie"], 1),
                f"{fmt_num(qtokens(row['inference_tokens_per_day']), 3)}Q",
                fmt_num(row["hbm_pb"], 1),
            ]
            for row in market_years
        ],
    )
    html_company_sections: list[str] = []
    for company in FOCUS_COMPANIES:
        rows = focus_rows_by_company[company]
        first, last = rows[0], rows[-1]
        hbm_first = hbm_company_year_lookup.get((company, first["year"]), {}).get("hbm_pb", 0.0)
        hbm_last = hbm_company_year_lookup.get((company, last["year"]), {}).get("hbm_pb", 0.0)
        read = COMPANY_READS[company]
        html_company_sections.extend(
            [
                f"<section><h2>{esc(read['title'])}</h2>",
                f"<p>{esc(read['read'])}</p>",
                f"<p>2026년에서 2030년까지 contracted power는 <b>{fmt_num(first['contracted_power_gw'], 2)} GW</b>에서 <b>{fmt_num(last['contracted_power_gw'], 2)} GW</b>로, active power는 <b>{fmt_num(first['active_power_gw'], 2)} GW</b>에서 <b>{fmt_num(last['active_power_gw'], 2)} GW</b>로 증가한다. 모델링된 inference power는 <b>{fmt_num(first['inference_gw'], 2)} GW</b>에서 <b>{fmt_num(last['inference_gw'], 2)} GW</b>로 확대된다. Token supply는 <b>{fmt_num(qtokens(first['inference_tokens_per_day']), 4)}Q/day</b>에서 <b>{fmt_num(qtokens(last['inference_tokens_per_day']), 4)}Q/day</b>로, HBM-equivalent demand는 <b>{fmt_num(hbm_first, 2)} PB</b>에서 <b>{fmt_num(hbm_last, 2)} PB</b>로 증가한다.</p>",
                f"<p>{esc(read['watch'])}</p>",
                "<h3>회사별 시계열</h3>",
                html_table(
                    ["연도", "Contracted GW", "Active GW", "Inference GW", "Training GW", "Inf. share", "TPS/MW", "Tokens/day", "HBM PB"],
                    [
                        [
                            str(row["year"]),
                            fmt_num(row["contracted_power_gw"], 2),
                            fmt_num(row["active_power_gw"], 2),
                            fmt_num(row["inference_gw"], 2),
                            fmt_num(row["training_gw"], 2),
                            fmt_pct(row["inference_power_share"], 0),
                            fmt_num(row["reference_serving_tps_per_mw"], 0),
                            f"{fmt_num(qtokens(row['inference_tokens_per_day']), 4)}Q",
                            fmt_num(hbm_company_year_lookup.get((company, row["year"]), {}).get("hbm_pb", 0.0), 2),
                        ]
                        for row in rows
                    ],
                ),
                "<h3>모델링된 inference power 기준 accelerator mix</h3>",
                html_table(
                    ["연도", "H200/A100/H100", "B200/B300", "GB200/GB300", "Purpose/custom/future"],
                    [
                        [
                            str(row["year"]),
                            fmt_pct(row["h200_share"], 1),
                            fmt_pct(row["b200_share"], 1),
                            fmt_pct(row["gb200_share"], 1),
                            fmt_pct(row["purpose_built_share"], 1),
                        ]
                        for row in accelerator_mix_by_company_year(data, company)
                    ],
                ),
                "<h3>CSP-normalized inference power, 2026년 및 2030년</h3>",
                html_table(
                    ["연도", "CSP", "CSP contract share", "Normalized share", "Inference MW"],
                    [
                        [
                            str(row["year"]),
                            row["csp"],
                            fmt_pct(row["contract_share"], 1),
                            fmt_pct(row["normalized_csp_share"], 1),
                            fmt_num(row["normalized_csp_inference_power_mw"], 0),
                        ]
                        for row in csp_mix_by_company_year(data, company)
                        if row["year"] in [2026, 2030]
                    ],
                ),
                "</section>",
            ]
        )

    html_supplier_narrative: list[str] = []
    for row in top_suppliers_2030[:5]:
        supplier = row["supplier"]
        history = [item for item in supplier_years if item["supplier"] == supplier and item["supplier_scope"] == "epoch_supplier"]
        first = history[0]
        html_supplier_narrative.extend(
            [
                f"<section><h2>{esc(supplier)}</h2>",
                (
                    f"<p>{esc(supplier)}의 공급자 관점 power는 user별 LLM owner power를 CSP side로 다시 집계한 값이다. "
                    f"2026년 normalized supplier inference power는 <b>{fmt_num(first['normalized_supplier_inference_mw'] / 1000, 2)} GW</b>, "
                    f"2030년은 <b>{fmt_num(row['normalized_supplier_inference_mw'] / 1000, 2)} GW</b>다. "
                    f"2030년 CSP total AI power seed는 <b>{fmt_num(row['csp_total_power_mw'] / 1000, 2)} GW</b>, "
                    f"AI-company contract power 합계는 <b>{fmt_num(row['ai_contract_power_mw'] / 1000, 2)} GW</b>다.</p>"
                ),
                (
                    f"<p>{esc(supplier_customer_sentence(supplier))} {esc(supplier_accelerator_sentence(row))} "
                    f"HBM-equivalent demand는 2030년 <b>{fmt_num(row['hbm_pb'], 2)} PB</b>로 추정된다.</p>"
                ),
                "</section>",
            ]
        )

    html_body = "\n".join(
        [
            "<!doctype html><html><head><meta charset='utf-8'>",
            "<title>전력 기반 LLM 토큰 처리량 및 HBM 공급량 리포트</title>",
            "<style>body{font-family:Arial,sans-serif;margin:0;background:#f8fafc;color:#0f172a}main{max-width:1120px;margin:auto;padding:36px}section{margin:34px 0}h1{font-size:38px;letter-spacing:0}h2{font-size:24px;margin-top:34px;letter-spacing:0}h3{font-size:17px;margin-top:22px;letter-spacing:0}p,li{font-size:15px;line-height:1.58}table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;margin:10px 0 20px}th{background:#0f172a;color:#fff;text-align:left;padding:8px}td{border-bottom:1px solid #e2e8f0;padding:8px}.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.kpi div{background:#fff;border:1px solid #e2e8f0;padding:16px}.kpi b{font-size:24px;display:block}pre{background:#0f172a;color:#e2e8f0;padding:18px;overflow:auto}.chart{background:#fff;border:1px solid #e2e8f0;margin:14px 0;overflow:auto}.lede{font-size:17px;line-height:1.65}@media(max-width:760px){main{padding:20px}.kpi{grid-template-columns:1fr}h1{font-size:30px}table{font-size:12px;display:block;overflow-x:auto}}</style>",
            "</head><body><main>",
            "<h1>전력 기반 LLM 토큰 처리량 및 HBM 공급량 리포트</h1>",
            f"<p>생성일 {esc(RUN_DATE)}. 범위: 주요 상용 LLM 사업자, 2026-2030년 시나리오 모델.</p>",
            "<div class='kpi'>",
            f"<div><span>Base 2030 tokens/day</span><b>{fmt_num(qtokens(total_2030), 2)}Q</b></div>",
            f"<div><span>Inference power</span><b>{fmt_num(weighted_inference_gw, 1)}GW</b></div>",
            f"<div><span>Weighted DCiE</span><b>{fmt_pct(avg_dcie, 1)}</b></div>",
            f"<div><span>HBM-equivalent</span><b>{fmt_num(total_hbm_2030, 1)}PB</b></div>",
            "</div>",
            f"<section><h2>Executive Summary</h2><p class='lede'>Base case 기준 active AI power는 <b>2026년 {fmt_num(market_years[0]['active_power_gw'], 1)} GW</b>에서 <b>2030년 {fmt_num(market_years[-1]['active_power_gw'], 1)} GW</b>로 확대된다. Inference power는 <b>{fmt_num(market_years[0]['inference_gw'], 1)} GW</b>에서 <b>{fmt_num(weighted_inference_gw, 1)} GW</b>로 증가한다. 이 리포트는 2030년 endpoint만이 아니라 2026-2030년 path를 읽기 위한 형태로 구성했다.</p></section>",
            "<section><h2>Methodology</h2><pre>CSP contract inference weight = CSP total AI power MW * AI-company contract share of CSP * inference share\nNormalized CSP inference power = AI-company inference MW * CSP contract inference weight / sum(company CSP contract inference weights)\nAI accelerator power = normalized CSP inference power * CSP accelerator share\nOutput tokens/day = inference GW * 1,000 * serving TPS/MW * 86,400\nHBM-equivalent PB = accelerator power MW * 1,000 / all-in kW per unit * HBM GB per unit / 1,000,000</pre></section>",
            f"<section><h2>2026-2030 Market Time Series</h2><p>아래 표는 forecast path를 유지해서 보여준다. Contracted GW는 중장기 capacity envelope, Active GW는 energization된 가용 전력, Inference GW는 token throughput으로 환산되는 전력이다.</p>{html_market_table}<div class='chart'>{token_ts_svg}</div><div class='chart'>{inference_ts_svg}</div><div class='chart'>{hbm_ts_svg}</div></section>",
            f"<section><h2>CSP Contract Normalization</h2><p>Bubble size는 CSP total power, AI-company contract share, inference split을 적용한 normalized inference MW를 의미한다. 시각화는 snapshot이고, 회사별 섹션의 표에서 2026년과 2030년 세부 구성을 확인할 수 있다.</p><div class='chart'>{bubble_2026_svg}</div><div class='chart'>{bubble_2030_svg}</div></section>",
            f"<section><h2>Token Supply</h2><div class='chart'>{token_svg}</div></section>",
            *html_company_sections,
            f"<section><h2>HBM Supply</h2><div class='chart'>{hbm_svg}</div></section>",
            "<section><h2>Sources</h2><ul>",
            *[f"<li><b>{esc(source['id'])}</b>: {esc(source['use'])} <a href='{esc(source['url'])}'>{esc(source['url'])}</a></li>" for source in SOURCES],
            "</ul></section>",
            "</main></body></html>",
        ]
    )
    html_company_narrative: list[str] = []
    for company in FOCUS_COMPANIES:
        rows = focus_rows_by_company[company]
        first, mid, last = rows[0], rows[len(rows) // 2], rows[-1]
        hbm_first = hbm_company_year_lookup.get((company, first["year"]), {}).get("hbm_pb", 0.0)
        hbm_last = hbm_company_year_lookup.get((company, last["year"]), {}).get("hbm_pb", 0.0)
        read = COMPANY_READS[company]
        html_company_narrative.extend(
            [
                f"<section><h2>{esc(read['title'])}</h2>",
                f"<p>{esc(read['read'])}</p>",
                (
                    f"<p>Capacity ramp는 2026년 active power <b>{fmt_num(first['active_power_gw'], 2)} GW</b>에서 "
                    f"2028년 <b>{fmt_num(mid['active_power_gw'], 2)} GW</b>, 2030년 <b>{fmt_num(last['active_power_gw'], 2)} GW</b>로 이어진다. "
                    f"Inference power는 <b>{fmt_num(first['inference_gw'], 2)} GW</b>에서 <b>{fmt_num(last['inference_gw'], 2)} GW</b>로 확대된다.</p>"
                ),
                (
                    f"<p>Token supply는 2026년 <b>{fmt_num(qtokens(first['inference_tokens_per_day']), 4)}Q/day</b>에서 "
                    f"2030년 <b>{fmt_num(qtokens(last['inference_tokens_per_day']), 4)}Q/day</b>로 증가한다. "
                    f"HBM-equivalent demand는 <b>{fmt_num(hbm_first, 2)} PB</b>에서 <b>{fmt_num(hbm_last, 2)} PB</b>로 늘어난다. "
                    f"{esc(latest_accelerator_mix_sentence(company))} {esc(csp_concentration_sentence(company))}</p>"
                ),
                f"<p>{esc(read['watch'])}</p>",
                "</section>",
            ]
        )

    html_body = "\n".join(
        [
            "<!doctype html><html><head><meta charset='utf-8'>",
            "<title>전력 기반 LLM 토큰 처리량 및 HBM 공급량 분석 리포트</title>",
            "<style>body{font-family:Arial,sans-serif;margin:0;background:#f7f8fb;color:#111827}main{max-width:980px;margin:auto;padding:44px 32px}h1{font-size:38px;line-height:1.16;letter-spacing:0;margin:0 0 10px}h2{font-size:24px;line-height:1.25;letter-spacing:0;margin:42px 0 12px}p,li{font-size:16px;line-height:1.72}.meta{color:#4b5563}.lede{font-size:18px;line-height:1.7}.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0 34px}.kpi div{background:#fff;border:1px solid #d8dee8;padding:16px}.kpi span{display:block;color:#4b5563;font-size:13px}.kpi b{display:block;font-size:24px;margin-top:6px}.chart{background:#fff;border:1px solid #d8dee8;margin:18px 0 26px;overflow:auto}pre{background:#111827;color:#e5e7eb;padding:18px;overflow:auto;font-size:13px;line-height:1.55}.sources li{font-size:14px}@media(max-width:760px){main{padding:24px 18px}h1{font-size:30px}.kpi{grid-template-columns:1fr}}</style>",
            "</head><body><main>",
            "<h1>전력 기반 LLM 토큰 처리량 및 HBM 공급량 분석 리포트</h1>",
            f"<p class='meta'>작성일 {esc(RUN_DATE)}. 주요 상용 LLM 사업자, 2026-2030년 Base/Bear/Bull 시나리오. 상세 테이블은 대시보드/CSV 산출물로 분리.</p>",
            "<div class='kpi'>",
            f"<div><span>2030 tokens/day</span><b>{fmt_num(qtokens(total_2030), 2)}Q</b></div>",
            f"<div><span>2030 inference power</span><b>{fmt_num(weighted_inference_gw, 1)}GW</b></div>",
            f"<div><span>2030 weighted DCiE</span><b>{fmt_pct(avg_dcie, 1)}</b></div>",
            f"<div><span>2030 HBM-equivalent</span><b>{fmt_num(total_hbm_2030, 1)}PB</b></div>",
            "</div>",
            "<section><h2>Executive Summary</h2>",
            (
                f"<p class='lede'>Base case에서 covered LLM owner들의 active AI power는 2026년 <b>{fmt_num(base_2026['active_power_gw'], 1)} GW</b>에서 "
                f"2030년 <b>{fmt_num(base_2030['active_power_gw'], 1)} GW</b>로 확대된다. 그러나 토큰 공급량을 결정하는 것은 gross GW가 아니라 "
                "DCiE, training/inference split, CSP별 계약 비중, accelerator mix, workload별 TPS/MW가 결합된 결과다.</p>"
            ),
            (
                f"<p>2030년 Base case generated-output token supply는 <b>{fmt_num(qtokens(total_2030), 2)}Q tokens/day</b>다. "
                f"Inference power는 <b>{fmt_num(weighted_inference_gw, 1)} GW</b>, training/reserve power는 "
                f"<b>{fmt_num(weighted_training_gw, 1)} GW</b>로 계산된다. HBM-equivalent demand는 "
                f"<b>{fmt_num(total_hbm_2030, 1)} PB</b>로, 24GB stack-equivalent 기준 <b>{fmt_num(total_hbm_stacks_2030, 2)} million개</b> 수준이다.</p>"
            ),
            "</section>",
            "<section><h2>분석 프레임워크</h2>",
            "<p>모델은 datacenter와 CSP 계약 전력을 AI company별 inference power로 정규화하고, CSP별 accelerator mix를 적용한 뒤, InferenceX benchmark proxy를 short, long, agentic workload로 나누어 TPS/MW를 부여한다.</p>",
            "<pre>Output tokens/day = inference GW * 1,000 * serving TPS/MW * 86,400\nHBM-equivalent PB = accelerator MW * 1,000 / all-in kW per unit * HBM GB per unit / 1,000,000</pre>",
            "</section>",
            "<section><h2>2026-2030년 전력과 토큰 공급량의 변화</h2>",
            (
                f"<p>Contracted power envelope는 2026년 <b>{fmt_num(base_2026['contracted_power_gw'], 1)} GW</b>에서 "
                f"2030년 <b>{fmt_num(base_2030['contracted_power_gw'], 1)} GW</b>로 확대된다. Active power는 "
                f"<b>{fmt_num(base_2026['active_power_gw'], 1)} GW</b>에서 <b>{fmt_num(base_2030['active_power_gw'], 1)} GW</b>로 증가하고, "
                f"weighted inference share는 <b>{fmt_pct(base_2026['weighted_inference_share'], 1)}</b>에서 "
                f"<b>{fmt_pct(base_2030['weighted_inference_share'], 1)}</b>로 상승한다.</p>"
            ),
            f"<div class='chart'>{token_ts_svg}</div>",
            f"<div class='chart'>{inference_ts_svg}</div>",
            "</section>",
            "<section><h2>공급자 관점: Epoch AI capacity를 CSP side로 다시 읽기</h2>",
            (
                "<p>기존 user 관점은 LLM owner가 확보한 전력과 token supply를 보여준다. 공급자 관점은 같은 전력을 CSP/datacenter provider가 "
                "어떤 AI user에게 공급하는지 보여준다. 이 관점은 HBM과 accelerator procurement를 추정할 때 중요하다.</p>"
            ),
            (
                f"<p>Epoch 기반 supplier scope의 normalized supplier inference power는 2026년 <b>{fmt_num(supplier_inference_2026, 2)} GW</b>에서 "
                f"2030년 <b>{fmt_num(supplier_inference_2030, 2)} GW</b>로 증가한다. 2030년 supplier-side total AI power seed는 "
                f"<b>{fmt_num(supplier_total_power_2030, 2)} GW</b>, AI-company contract power 합계는 "
                f"<b>{fmt_num(supplier_contract_power_2030, 2)} GW</b>다. Legacy company envelope row는 이 supplier scope에서 제외했다.</p>"
            ),
            f"<div class='chart'>{supplier_power_ts_svg}</div>",
            "</section>",
            *html_supplier_narrative,
            "<section><h2>기업별 분석</h2><p>아래 섹션은 표 대신 각 기업의 capacity path, CSP 의존도, accelerator mix, benchmark uncertainty를 중심으로 해석한다.</p></section>",
            *html_company_narrative,
            "<section><h2>Benchmark Proxy와 해석상 주의점</h2>",
            "<p>InferenceX는 production telemetry가 아니라 public serving benchmark proxy다. Short conversation, long conversation, agentic workload를 분리하고 company별 traffic 성격에 따라 workload share와 commercial fit factor를 적용했다.</p>",
            "<p>Agentic workload는 공개 benchmark data가 부족하기 때문에 낮은 confidence 영역으로 남겨야 한다. 향후 agentic traces가 더 축적되면 short/long/agentic 간 TPS/MW 비율이 가장 먼저 업데이트되어야 한다.</p>",
            "</section>",
            "<section><h2>HBM 공급량 관점의 시사점</h2>",
            (
                f"<p>HBM-equivalent demand는 2026년 <b>{fmt_num(base_2026['hbm_pb'], 1)} PB</b>에서 "
                f"2030년 <b>{fmt_num(base_2030['hbm_pb'], 1)} PB</b>로 증가한다. 이 값은 token volume보다 accelerator unit 수에 직접 연결되므로, "
                "HBM 공급량을 추정할 때는 CSP별 accelerator mix와 세대별 all-in power, HBM GB/unit을 함께 봐야 한다.</p>"
            ),
            f"<div class='chart'>{hbm_ts_svg}</div>",
            "</section>",
            "<section><h2>데이터 산출물</h2><ul>",
            f"<li>{REPORT_STEM}_base_market_timeseries.csv</li>",
            f"<li>{REPORT_STEM}_focus_company_timeseries.csv</li>",
            f"<li>{REPORT_STEM}_supplier_power_timeseries.csv</li>",
            f"<li>{REPORT_STEM}_supplier_customer_exposure_2030.csv</li>",
            f"<li>{REPORT_STEM}_focus_csp_contract_timeseries.csv</li>",
            f"<li>{REPORT_STEM}_hbm_company_year.csv</li>",
            f"<li>{REPORT_STEM}_hbm_detail.csv</li>",
            "</ul></section>",
            "<section><h2>Sources And Caveats</h2><ul class='sources'>",
            *[f"<li><b>{esc(source['id'])}</b>: {esc(source['use'])} <a href='{esc(source['url'])}'>{esc(source['url'])}</a></li>" for source in SOURCES],
            "</ul><p>이 결과는 scenario model이며 각 회사의 disclosed production telemetry가 아니다. Custom accelerator의 HBM 및 TPS/MW는 generation-specific disclosure가 확보되기 전까지 placeholder다.</p></section>",
            "</main></body></html>",
        ]
    )
    html_path = OUT / f"{REPORT_STEM}.html"
    html_path.write_text(html_body, encoding="utf-8")

    return {
        "markdown": md_path,
        "html": html_path,
        "token_svg": CHART_DIR / "token_supply_2030.svg",
        "hbm_svg": CHART_DIR / "hbm_supply_2030.svg",
        "bubble_2026_svg": CHART_DIR / "csp_contract_bubble_2026.svg",
        "bubble_2030_svg": CHART_DIR / "csp_contract_bubble_2030.svg",
        "token_ts_svg": CHART_DIR / "token_supply_timeseries_focus.svg",
        "inference_ts_svg": CHART_DIR / "inference_power_timeseries_focus.svg",
        "hbm_ts_svg": CHART_DIR / "hbm_supply_timeseries_focus.svg",
        "supplier_power_ts_svg": CHART_DIR / "supplier_inference_power_timeseries.svg",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = build_payload()
    if data["validation"]["status"] != "PASS":
        raise SystemExit(json.dumps(data["validation"], indent=2, ensure_ascii=False))
    outputs = write_report(data)
    print(json.dumps({key: str(path) for key, path in outputs.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
