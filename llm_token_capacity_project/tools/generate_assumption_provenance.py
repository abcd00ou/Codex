"""Generate per-assumption provenance packs for 2026-2030 model inputs.

This tool is deliberately read-only with respect to model logic. It imports the
current capacity generator, reuses its full audit payload, and writes a
human-readable plus machine-readable provenance layer.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DOCS_OUT = ROOT / "docs" / "provenance"
ASSUMPTION_DOCS_OUT = DOCS_OUT / "assumptions"
REPORTS_OUT = ROOT / "outputs" / "reports"
YEARS = list(range(2026, 2031))


@dataclass(frozen=True)
class AssumptionSpec:
    assumption_id: str
    title: str
    short_name: str
    metrics: tuple[str, ...]
    role_kr: str
    confidence_rule_kr: str
    direct_headline_use: str


ASSUMPTIONS: tuple[AssumptionSpec, ...] = (
    AssumptionSpec(
        "A01",
        "contracted_power_gw",
        "계약/발표/귀속 전력 capacity ceiling",
        ("contracted_power_gw",),
        "2026-2030 전력 capacity 상한 또는 model-owner 귀속 capacity envelope를 정의한다.",
        "공식 GW/MW 발표가 있으면 fact anchor + scenario ceiling, 없으면 scenario capacity envelope로 낮은 confidence를 유지한다.",
        "직접 사용",
    ),
    AssumptionSpec(
        "A02",
        "active_power_gw",
        "운영 투입 전력 전환",
        ("operational_deployment_share", "active_power_gw", "it_load_gw"),
        "계약/계획 capacity 중 실제 energization, 냉각, 네트워크, accelerator 배치를 통과한 몫만 토큰 산식에 넣는다.",
        "site-level operational telemetry가 없으면 scenario conversion으로 둔다.",
        "직접 사용",
    ),
    AssumptionSpec(
        "A03",
        "pue",
        "facility power -> IT load 전환",
        ("pue", "it_load_gw"),
        "active facility power를 IT load로 바꾼다.",
        "업체/사이트별 measured PUE가 없으면 scenario parameter로 유지한다.",
        "직접 사용",
    ),
    AssumptionSpec(
        "A04",
        "ai_workload_share",
        "IT load 중 AI workload 몫",
        ("ai_workload_share", "ai_it_load_gw"),
        "IT load 중 model-owner AI training/serving에 귀속되는 몫만 분리한다.",
        "AI platform 방향은 source로 확인하되 workload share 수치는 telemetry 부재 시 scenario다.",
        "직접 사용",
    ),
    AssumptionSpec(
        "A05",
        "inference_power_share",
        "AI IT load 중 inference 몫",
        ("inference_power_share", "inference_gw"),
        "상용 generated output token capacity에 들어가는 inference power를 산출한다.",
        "company-level inference/training split 공시가 없으므로 scenario allocation이다.",
        "직접 사용",
    ),
    AssumptionSpec(
        "A06",
        "training_power_share",
        "AI IT load 중 training/eval 몫",
        ("training_power_share", "training_gw"),
        "frontier training, post-training, eval, reserve capacity를 inference와 분리해 과대계산을 막는다.",
        "A05의 보수적 보완값이며, provider telemetry가 나오면 교체한다.",
        "직접 사용: inference 과대계산 방지",
    ),
    AssumptionSpec(
        "A07",
        "active_parameters",
        "모델 구조와 active parameter band",
        ("model_parameter",),
        "dense/MoE/closed model의 token당 계산량과 benchmark proxy 선택의 맥락을 제공한다.",
        "공식 model card는 high confidence, closed model band는 scenario confidence로 분리한다.",
        "간접 사용: benchmark/proxy 선택 맥락",
    ),
    AssumptionSpec(
        "A08",
        "tokens_per_second_per_mw",
        "InferenceX 기반 generated output TPS/MW",
        (
            "fleet_reference_tps_per_mw",
            "commercial_workload_fit_factor",
            "reference_serving_tps_per_mw",
            "purpose_built_tps_per_mw",
            "tokens_per_second_per_mw",
        ),
        "1MW inference load가 초당 몇 generated output token을 만들 수 있는지 결정한다.",
        "InferenceX는 proxy/benchmark이며 production telemetry가 아니므로 workload fit factor와 source caveat를 같이 붙인다.",
        "직접 사용",
    ),
    AssumptionSpec(
        "A09",
        "utilization",
        "연평균 utilization 및 serving sensitivity",
        ("utilization_reference_only", "headline_utilization_applied"),
        "이론 capacity와 실제 sustained output 사이의 차이를 공부하기 위한 sensitivity layer다.",
        "headline에는 곱하지 않는다. 중복 보정 방지를 위해 reference/sensitivity only로 유지한다.",
        "headline 미적용",
    ),
    AssumptionSpec(
        "A10",
        "attribution_rule",
        "model-owner attribution과 host 중복 제거",
        ("attribution_rule",),
        "AWS/Oracle/CoreWeave 같은 host capacity와 model-owner output을 중복 계산하지 않도록 귀속 규칙을 정의한다.",
        "공식 ownership/hosting 관계는 source로 고정하고, capacity split은 scenario로 둔다.",
        "간접 사용: row inclusion/exclusion",
    ),
    AssumptionSpec(
        "A11",
        "gpu_asic_mix",
        "GPU generation 및 purpose-built accelerator mix",
        ("gpu_share", "h200_share", "b200_share", "gb200_share", "purpose_built_accelerator_share"),
        "같은 inference MW라도 H200/B200/GB200/purpose-built mix에 따라 benchmark TPS/MW가 달라진다.",
        "platform existence는 source fact, numeric share는 fleet telemetry가 없으면 editable scenario다.",
        "직접 사용",
    ),
)


PRIMARY_METRIC_BY_ASSUMPTION = {
    "A01": "contracted_power_gw",
    "A02": "active_power_gw",
    "A03": "pue",
    "A04": "ai_workload_share",
    "A05": "inference_power_share",
    "A06": "training_power_share",
    "A07": "model_parameter",
    "A08": "tokens_per_second_per_mw",
    "A09": "utilization_sensitivity",
    "A10": "attribution_rule",
    "A11": "gpu_share",
}


DECISION_LOGIC_KR = {
    "A01": [
        "출처 링크는 각 회사가 어느 cloud/AI platform, 데이터센터, accelerator 조달 방향을 갖는지 확인하는 fact anchor로 사용한다.",
        "공식 MW/GW 수치가 있는 경우에는 그 값을 capacity ceiling의 강한 anchor로 두고, 공개 수치가 없는 회사는 model-owner가 접근 가능한 전력 envelope를 scenario로 둔다.",
        "2026과 2030 endpoint를 먼저 정하고, 중간 연도는 capacity ramp가 매년 일정하게 진행된다는 보수적 보간 규칙으로 만든다.",
        "따라서 이 숫자는 회사가 직접 공시한 전력 예측치가 아니라, 공개 근거와 scenario ceiling을 결합한 벤치마크용 입력값이다.",
    ],
    "A02": [
        "계약/발표 capacity 전체가 바로 inference에 투입된다고 보지 않고, energization, 냉각, 네트워크, accelerator 설치, 클러스터 bring-up을 통과한 몫만 active power로 전환한다.",
        "operational_deployment_share는 공개 telemetry가 없는 부분을 메우는 scenario 계수이며, 출처 링크는 capacity ramp가 존재하는지와 플랫폼 확장 방향을 확인하는 용도다.",
        "active_power_gw는 contracted_power_gw에 operational_deployment_share를 곱해 만들며, 이후 PUE를 통해 IT load로 내려간다.",
        "site-level 전력 계량, GPU cluster 가동률, 실제 energized MW가 확보되면 이 계수와 active power는 우선 교체 대상이다.",
    ],
    "A03": [
        "PUE는 facility power를 IT load로 변환하는 계수다. 링크가 데이터센터 효율 또는 인프라 방향을 보여주더라도, 회사/사이트별 measured PUE가 없으면 수치는 scenario다.",
        "전력 총량을 accelerator가 소비하는 IT load로 과대 해석하지 않기 위해 PUE를 별도 assumption으로 분리했다.",
        "it_load_gw는 active_power_gw / pue로 계산한다. 낮은 PUE일수록 같은 facility power에서 더 많은 IT load가 나온다.",
        "실제 site PUE, 냉각 방식, 계절별 PUE가 확보되면 이 값은 사이트별로 교체해야 한다.",
    ],
    "A04": [
        "AI workload share는 IT load 중 model training, inference, evaluation, embedding, safety pipeline 등 AI workload에 귀속되는 몫이다.",
        "출처는 회사가 AI 제품/모델/인프라를 확장하고 있다는 방향성 확인에 쓰고, 정확한 workload split은 공개 telemetry가 아니므로 scenario로 둔다.",
        "ai_it_load_gw는 it_load_gw에 ai_workload_share를 곱해 만든다.",
        "cluster scheduler 로그, accelerator-hour accounting, business unit별 power allocation이 나오면 이 assumption을 교체한다.",
    ],
    "A05": [
        "inference_power_share는 AI IT load 중 상용 generated output token을 만드는 serving 영역의 몫이다.",
        "링크는 상용 서비스, API, assistant, cloud AI product가 존재한다는 근거로 쓰며, 회사별 inference/training 전력 분할을 직접 공시한 것으로 보지 않는다.",
        "inference_gw는 ai_it_load_gw에 inference_power_share를 곱한다. 이 값이 TPS/MW와 곱해져 headline token capacity가 된다.",
        "실제 serving accelerator-hour, request mix, prefill/decode 분리 telemetry가 확보되면 우선 교체해야 한다.",
    ],
    "A06": [
        "training_power_share는 A05와 짝을 이루는 보완 계수다. 모든 AI 전력이 바로 inference token으로 변환된다는 과대계산을 막기 위해 남겨둔다.",
        "frontier training, post-training, evaluation, synthetic data generation, reserve capacity는 generated output headline에 직접 넣지 않는다.",
        "기본 구조는 training_power_share = 1 - inference_power_share다.",
        "회사별 training/inference accelerator-hour split이나 workload accounting이 나오면 A05와 함께 다시 맞춰야 한다.",
    ],
    "A07": [
        "모델 parameter 정보는 직접 토큰 수식에 곱하는 값이라기보다, 어떤 InferenceX benchmark proxy가 더 가까운지 판단하는 구조적 근거다.",
        "open model card처럼 total/active parameter가 공개된 경우에는 높은 confidence의 fact anchor로 쓰고, closed model은 공개 추정 범위와 제품 특성을 반영한 scenario band로 둔다.",
        "dense와 MoE는 token당 계산량이 다르므로 total parameter와 active parameter를 분리해서 기록한다.",
        "공식 model card, architecture disclosure, serving kernel trace가 나오면 closed model band를 교체한다.",
    ],
    "A08": [
        "TPS/MW는 InferenceX 공개 benchmark를 그대로 생산 telemetry로 간주하지 않고, H200/B200/GB200 reference 성능을 상용 workload에 맞게 낮춘 proxy로 사용한다.",
        "fleet_reference_tps_per_mw는 GPU generation mix에서 나온 raw benchmark 기준이고, commercial_workload_fit_factor는 closed model, 긴 context, SLO, batching 제약, prefill/decode 불균형을 반영하는 보정 계수다.",
        "tokens_per_second_per_mw는 reference_serving_tps_per_mw와 purpose_built_tps_per_mw를 fleet mix로 결합한 최종 입력값이다.",
        "LLMServingSim 2.0 방식의 trace-driven prefill/decode simulation, KV cache pressure, interconnect contention, scheduling 정책이 확보되면 fit factor를 더 구조적인 계수로 쪼갤 수 있다.",
    ],
    "A09": [
        "utilization은 headline 산식에 곱하지 않는다. 이미 A08의 commercial workload fit factor가 sustained serving 성능을 낮추기 때문이다.",
        "이 assumption은 공부와 sensitivity 분석을 위한 reference layer이며, 같은 보정을 두 번 적용하는 double counting을 막기 위해 headline_utilization_applied를 False로 둔다.",
        "utilization_sensitivity는 특정 운영 profile에서 TPS/MW가 얼마나 달라지는지 보는 보조 테이블이다.",
        "실제 SLO별 cluster utilization, queueing, admission control, idle reserve telemetry가 나오면 sensitivity profile을 교체한다.",
    ],
    "A10": [
        "attribution_rule은 host capacity와 model-owner output을 중복 계산하지 않기 위한 규칙이다.",
        "출처는 AWS, Oracle, CoreWeave 같은 host와 model owner 사이의 platform/hosting 관계를 확인하는 데 쓰고, 정확한 capacity split을 직접 뜻하지는 않는다.",
        "headline forecast는 model owner가 상용 output token을 만들어내는 capacity만 세며, host-only rows는 별도 supply-side 근거로 분리한다.",
        "공식 capacity ownership, reserved instance 계약, accelerator-hour attribution telemetry가 나오면 이 규칙을 더 세밀하게 바꿀 수 있다.",
    ],
    "A11": [
        "GPU/ASIC mix는 같은 MW라도 H200, B200, GB200, purpose-built accelerator 비중에 따라 TPS/MW가 달라지기 때문에 필요하다.",
        "출처 링크는 특정 platform이나 accelerator generation이 존재한다는 fact anchor이고, exact fleet share는 공개되지 않으면 scenario다.",
        "purpose-built accelerator share는 비교 가능한 public serving benchmark가 부족하면 별도 uplift를 과하게 주지 않고 보수적으로 둔다.",
        "fleet inventory, accelerator-hour split, per-generation serving benchmark가 나오면 A08의 TPS/MW와 함께 다시 계산해야 한다.",
    ],
}


def load_generator_payload() -> dict[str, Any]:
    module_path = TOOLS / "generate_llm_token_capacity_report.py"
    spec = importlib.util.spec_from_file_location("llm_capacity_generator_for_provenance", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.build_payload()


def split_ids(value: str) -> list[str]:
    return [token.strip() for token in str(value or "").split(";") if token.strip()]


def source_lookup(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup = {item["source_id"]: item for item in data["sources"]}
    lookup.update({item["assumption_id"]: item for item in data["assumptions"]})
    return lookup


def spec_for_metric(metric: str) -> AssumptionSpec | None:
    for spec in ASSUMPTIONS:
        if metric in spec.metrics:
            return spec
    return None


def build_trace_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    forecast_index = {
        (row["scenario"], row["company"], row["year"]): row for row in data["scenario_forecast"]
    }
    out: list[dict[str, Any]] = []
    for trace in data["number_trace"]:
        spec = spec_for_metric(trace["metric"])
        if spec is None:
            continue
        frow = forecast_index.get((trace["scenario"], trace["company"], trace["year"]), {})
        out.append(
            {
                "assumption_id": spec.assumption_id,
                "assumption_title": spec.title,
                "scenario": trace["scenario"],
                "company": trace["company"],
                "year": trace["year"],
                "metric": trace["metric"],
                "value": trace["value"],
                "unit": trace["unit"],
                "derivation_type": trace["derivation_type"],
                "confidence": frow.get("confidence", ""),
                "formula_or_rule": trace["formula_or_rule"],
                "why_this_number": trace["why_this_number"],
                "source_ids": trace["source_ids"],
                "assumption_ids": trace["assumption_ids"],
                "replacement_path": trace["replacement_path"],
            }
        )

    # Add non-number-trace provenance for model structure and attribution.
    for model in data["company_models"]:
        for spec, metric, value, rule, why in [
            (
                next(s for s in ASSUMPTIONS if s.assumption_id == "A07"),
                "model_parameter",
                f"total={model['parameter_band_total']} | active={model['parameter_band_active']}",
                "model card / closed-model band review",
                model["note_kr"],
            ),
            (
                next(s for s in ASSUMPTIONS if s.assumption_id == "A10"),
                "attribution_rule",
                model["attribution_rule"],
                "model-owner row attribution rule",
                f"Commercial surface: {model['commercial_surface']}; serving platform: {model['serving_platform']}",
            ),
        ]:
            out.append(
                {
                    "assumption_id": spec.assumption_id,
                    "assumption_title": spec.title,
                    "scenario": "All",
                    "company": model["company"],
                    "year": "2026-2030",
                    "metric": metric,
                    "value": value,
                    "unit": "text",
                    "derivation_type": "Fact anchor + scenario boundary",
                    "confidence": model["confidence"],
                    "formula_or_rule": rule,
                    "why_this_number": why,
                    "source_ids": model["source_ids"],
                    "assumption_ids": "",
                    "replacement_path": "Official model card, platform disclosure, or provider attribution telemetry.",
                }
            )

    # Add A09 utilization sensitivity records because headline forecast explicitly excludes utilization.
    spec = next(s for s in ASSUMPTIONS if s.assumption_id == "A09")
    for item in data.get("utilization_sensitivity", []):
        out.append(
            {
                "assumption_id": spec.assumption_id,
                "assumption_title": spec.title,
                "scenario": item.get("profile", ""),
                "company": item.get("company", ""),
                "year": item.get("year", ""),
                "metric": "utilization_sensitivity",
                "value": item.get("adjusted_utilization", ""),
                "unit": "share",
                "derivation_type": "Sensitivity only",
                "confidence": "Reference-only",
                "formula_or_rule": "adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier",
                "why_this_number": item.get("description_kr", ""),
                "source_ids": item.get("source_ids", ""),
                "assumption_ids": "A09_utilization",
                "replacement_path": "Provider utilization telemetry and SLO-level serving traces.",
            }
        )
    return out


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "assumption_id",
        "assumption_title",
        "scenario",
        "company",
        "year",
        "metric",
        "value",
        "unit",
        "derivation_type",
        "confidence",
        "formula_or_rule",
        "why_this_number",
        "source_ids",
        "assumption_ids",
        "replacement_path",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        cells = [str(cell).replace("\n", " ").replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def source_summary(source_ids: str, lookup: dict[str, dict[str, Any]]) -> str:
    parts = []
    for sid in split_ids(source_ids):
        item = lookup.get(sid)
        if not item:
            parts.append(f"`{sid}`")
            continue
        title = item.get("title") or item.get("description_kr") or item.get("assumption_id", sid)
        tier = item.get("tier") or item.get("category", "")
        parts.append(f"`{sid}`: {title} ({tier})")
    return "<br>".join(parts)


def compact_text(value: Any, limit: int = 420) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def source_use_detail(item: dict[str, Any]) -> str:
    return compact_text(
        item.get("use_in_model")
        or item.get("note_kr")
        or item.get("description_kr")
        or item.get("category")
        or "",
        360,
    )


def decision_sample_rows(spec: AssumptionSpec, items: list[dict[str, Any]]) -> list[list[Any]]:
    primary_metric = PRIMARY_METRIC_BY_ASSUMPTION.get(spec.assumption_id)
    candidates = [r for r in items if r["metric"] == primary_metric]
    base_candidates = [r for r in candidates if r["scenario"] == "Base" and r["year"] in (2026, "2026-2030")]
    if base_candidates:
        candidates = base_candidates
    if not candidates:
        candidates = items

    rows = []
    seen: set[tuple[Any, Any, Any]] = set()
    for row in candidates:
        key = (row["company"], row["metric"], row["scenario"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            [
                row["company"],
                row["metric"],
                row["value"],
                compact_text(row["why_this_number"], 360),
                compact_text(row["formula_or_rule"], 220),
                compact_text(row["replacement_path"], 260),
                row["source_ids"],
            ]
        )
        if len(rows) >= 14:
            break
    return rows


def source_logic_rows(source_ids: list[str], lookup: dict[str, dict[str, Any]]) -> list[list[Any]]:
    rows = []
    for sid in source_ids:
        item = lookup.get(sid, {})
        rows.append(
            [
                sid,
                item.get("url_or_report", ""),
                source_use_detail(item),
                item.get("confidence", ""),
            ]
        )
    return rows


def write_assumption_docs(rows: list[dict[str, Any]], data: dict[str, Any]) -> None:
    ASSUMPTION_DOCS_OUT.mkdir(parents=True, exist_ok=True)
    lookup = source_lookup(data)
    by_assumption: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_assumption[row["assumption_id"]].append(row)

    for spec in ASSUMPTIONS:
        items = by_assumption.get(spec.assumption_id, [])
        base_items = [r for r in items if r["scenario"] == "Base"]
        metrics = sorted({r["metric"] for r in items})
        source_ids = sorted({sid for r in items for sid in split_ids(r["source_ids"])})
        assumption_ids = sorted({sid for r in items for sid in split_ids(r["assumption_ids"])})

        lines = [
            f"# {spec.assumption_id} {spec.title} Provenance",
            "",
            f"Short name: {spec.short_name}",
            "",
            f"Role: {spec.role_kr}",
            "",
            f"Headline use: {spec.direct_headline_use}",
            "",
            f"Confidence rule: {spec.confidence_rule_kr}",
            "",
            "## Metrics covered",
            "",
            ", ".join(f"`{metric}`" for metric in metrics) if metrics else "No rows.",
            "",
            "## 숫자 결정 로직",
            "",
        ]

        for bullet in DECISION_LOGIC_KR.get(spec.assumption_id, []):
            lines.append(f"- {bullet}")

        source_logic = source_logic_rows(source_ids, lookup)
        if source_logic:
            lines += [
                "",
                "### 링크를 숫자로 읽는 방식",
                "",
                "아래 표는 링크 자체를 그대로 숫자로 옮긴 것이 아니라, 각 출처가 어떤 판단에 쓰였는지를 기록한다. URL이 capacity 방향성만 확인해주는 경우와 실제 수치 anchor를 제공하는 경우를 구분해서 읽어야 한다.",
                "",
                md_table(["ID", "URL/report", "숫자 결정에 쓰인 방식", "Confidence"], source_logic),
                "",
            ]

        sample_rows = decision_sample_rows(spec, items)
        if sample_rows:
            lines += [
                "### 행 단위 결정 샘플",
                "",
                "대표 metric 행을 기준으로, 실제 trace에서 가져온 `why_this_number`, 산식, 교체 경로를 함께 붙였다. 이 표의 값은 모델 입력값이며, 공시 숫자와 scenario 숫자가 섞여 있을 수 있다.",
                "",
                md_table(
                    [
                        "Company",
                        "Metric",
                        "Value",
                        "왜 이 숫자인가",
                        "Formula/rule",
                        "교체 경로",
                        "Source IDs",
                    ],
                    sample_rows,
                ),
                "",
            ]

        lines += [
            "## Base scenario 2026 -> 2030 endpoint view",
            "",
        ]

        endpoint_rows: list[list[Any]] = []
        endpoint_index: dict[tuple[str, str], dict[int, dict[str, Any]]] = defaultdict(dict)
        for row in base_items:
            if isinstance(row["year"], int):
                endpoint_index[(row["company"], row["metric"])][row["year"]] = row
        for (company, metric), year_rows in sorted(endpoint_index.items()):
            start = year_rows.get(2026)
            end = year_rows.get(2030)
            if not start or not end:
                continue
            endpoint_rows.append(
                [
                    company,
                    metric,
                    f"{start['value']} -> {end['value']} {start['unit']}",
                    start["derivation_type"],
                    start["confidence"],
                    start["source_ids"],
                ]
            )
        if endpoint_rows:
            lines.append(
                md_table(
                    ["Company", "Metric", "2026 -> 2030", "Derivation", "Confidence", "Source IDs"],
                    endpoint_rows,
                )
            )
        else:
            text_rows = [
                [
                    r["company"],
                    r["year"],
                    r["metric"],
                    r["value"],
                    r["confidence"],
                    r["source_ids"],
                ]
                for r in items[:30]
            ]
            lines.append(md_table(["Company", "Year", "Metric", "Value", "Confidence", "Source IDs"], text_rows))

        lines += [
            "",
            "## Formula/rule examples",
            "",
        ]
        examples = []
        seen_rules = set()
        for row in items:
            key = (row["metric"], row["formula_or_rule"])
            if key in seen_rules:
                continue
            seen_rules.add(key)
            examples.append(
                [
                    row["metric"],
                    row["formula_or_rule"],
                    row["why_this_number"],
                    row["replacement_path"],
                ]
            )
            if len(examples) >= 8:
                break
        lines.append(md_table(["Metric", "Formula or rule", "Why this number", "Replacement path"], examples))

        lines += [
            "",
            "## Source catalog for this assumption",
            "",
        ]
        source_rows = []
        for sid in source_ids:
            item = lookup.get(sid, {})
            source_rows.append(
                [
                    sid,
                    item.get("title") or item.get("description_kr") or item.get("assumption_id", ""),
                    item.get("publisher", item.get("category", "")),
                    item.get("date", ""),
                    item.get("tier", ""),
                    item.get("confidence", ""),
                    item.get("url_or_report", ""),
                ]
            )
        lines.append(md_table(["ID", "Title/description", "Publisher/category", "Date", "Tier", "Confidence", "URL/report"], source_rows))

        if assumption_ids:
            lines += [
                "",
                "## Linked assumption IDs",
                "",
                ", ".join(f"`{sid}`" for sid in assumption_ids),
                "",
            ]

        path = ASSUMPTION_DOCS_OUT / f"{spec.assumption_id}_{spec.title}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(rows: list[dict[str, Any]], data: dict[str, Any]) -> None:
    DOCS_OUT.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(int)
    for row in rows:
        counts[row["assumption_id"]] += 1
    lines = [
        "# LLM Token Capacity Assumption Provenance",
        "",
        f"Generated from `{TOOLS / 'generate_llm_token_capacity_report.py'}` full audit payload.",
        "",
        "This folder separates each 2026-2030 model assumption into auditable provenance files. It does not change forecast logic.",
        "",
        "## Files",
        "",
        "- `assumptions/`: per-assumption Markdown packs.",
        "- `outputs/reports/assumption_provenance_2026_2030.csv`: machine-readable full trace.",
        "- `outputs/reports/assumption_provenance_2026_2030.json`: machine-readable full trace plus source registry.",
        "",
        "## Assumption map",
        "",
        md_table(
            ["ID", "Title", "Headline use", "Trace rows", "Role"],
            [
                [spec.assumption_id, spec.title, spec.direct_headline_use, counts[spec.assumption_id], spec.role_kr]
                for spec in ASSUMPTIONS
            ],
        ),
        "",
        "## Important interpretation rules",
        "",
        "- `Fact anchor` does not mean every value in the row is a public fact; it means the scenario is anchored to a public source.",
        "- `Scenario capacity envelope` means the numeric value is model-created and must not be quoted as company disclosure.",
        "- InferenceX is benchmark/proxy evidence, not company production telemetry.",
        "- A09 utilization is intentionally excluded from the headline token formula to avoid double counting.",
        "- A11 purpose-built accelerator share is a numeric scenario unless company accelerator-hours or fleet split is disclosed.",
        "",
    ]
    (DOCS_OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_json(rows: list[dict[str, Any]], data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_from": "generate_llm_token_capacity_report.py build_payload()",
            "source_model_generated_at": data["metadata"]["generated_at"],
            "years": YEARS,
            "scope": data["metadata"]["scope"],
        },
        "assumption_specs": [spec.__dict__ for spec in ASSUMPTIONS],
        "sources": data["sources"],
        "registered_assumptions": data["assumptions"],
        "trace": rows,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    data = load_generator_payload()
    rows = build_trace_rows(data)
    write_csv(rows, REPORTS_OUT / "assumption_provenance_2026_2030.csv")
    write_json(rows, data, REPORTS_OUT / "assumption_provenance_2026_2030.json")
    write_assumption_docs(rows, data)
    write_readme(rows, data)
    print(f"trace_rows={len(rows)}")
    print(f"assumption_docs={len(ASSUMPTIONS)}")
    print(f"wrote={DOCS_OUT}")
    print(f"wrote={REPORTS_OUT / 'assumption_provenance_2026_2030.csv'}")
    print(f"wrote={REPORTS_OUT / 'assumption_provenance_2026_2030.json'}")


if __name__ == "__main__":
    main()
