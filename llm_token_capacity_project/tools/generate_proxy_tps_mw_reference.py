"""Build model/GPU/workload/interactivity TPS/MW reference outputs.

This script converts the report JSON interactivity profiles into a compact
reference table for Excel proxy-model selection. It keeps direct InferenceX
rows when available and derives agentic rows from long-chat rows with the
dynamic-reasoning call multiplier.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "outputs" / "reports" / "llm_token_capacity_2026_2030.json"
OUT_DIR = ROOT / "docs" / "dynamic_reasoning_agent_cost"
COEFFICIENTS_CSV = OUT_DIR / "dynamic_reasoning_scenario_coefficients.csv"
OUT_CSV = OUT_DIR / "model_gpu_workload_interactivity_tps_mw_reference.csv"
OUT_MD = OUT_DIR / "model_gpu_workload_interactivity_tps_mw_reference.md"

OUTPUT_COLUMNS = [
    "proxy_model",
    "source_model_scope",
    "gpu",
    "workload",
    "target_tok_s_user",
    "target_met",
    "slo_gap_pct",
    "effective_output_tps_per_mw",
    "selected_tok_s_user",
    "precision",
    "framework",
    "concurrency",
    "isl",
    "osl",
    "selection_status",
    "source_type",
    "confidence",
    "benchmark_date",
    "method_note",
]


def read_agentic_multiplier() -> float:
    with COEFFICIENTS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["scenario"] == "react_tool_agent":
                return float(row["llm_call_multiplier_vs_static"])
    return 9.2


def fnum(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def fmt_num(value: Any, decimals: int = 0) -> str:
    num = fnum(value)
    if num is None:
        return ""
    if decimals == 0:
        return f"{num:,.0f}"
    return f"{num:,.{decimals}f}"


def fmt_pct(value: Any) -> str:
    num = fnum(value)
    if num is None:
        return ""
    return f"{num:.1%}"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def get_best_profile(
    profiles: dict[tuple[str, str, str, int], dict[str, Any]],
    proxy_model: str,
    gpu: str,
    workload_type: str,
    target: int,
) -> tuple[dict[str, Any] | None, str]:
    exact = profiles.get((proxy_model, gpu, workload_type, target))
    if exact and fnum(exact.get("selected_output_tps_per_mw")) is not None:
        return exact, "target_met_row"

    candidates = [
        row
        for (p, g, w, _), row in profiles.items()
        if p == proxy_model
        and g == gpu
        and w == workload_type
        and fnum(row.get("selected_output_tps_per_mw")) is not None
    ]
    if not candidates:
        return None, "no_reference_row"
    return max(candidates, key=lambda row: fnum(row.get("selected_tok_s_user")) or 0), "best_available_below_target"


def get_agentic_parent_profile(
    profiles: dict[tuple[str, str, str, int], dict[str, Any]],
    proxy_model: str,
    gpu: str,
    target: int,
    call_multiplier: float,
) -> tuple[dict[str, Any] | None, str]:
    candidates = [
        row
        for (p, g, w, _), row in profiles.items()
        if p == proxy_model
        and g == gpu
        and w == "long_chat"
        and fnum(row.get("selected_output_tps_per_mw")) is not None
        and fnum(row.get("selected_tok_s_user")) is not None
    ]
    if not candidates:
        return None, "no_reference_row"

    eligible = [
        row for row in candidates if (fnum(row.get("selected_tok_s_user")) or 0) / call_multiplier >= target
    ]
    if eligible:
        return (
            max(eligible, key=lambda row: fnum(row.get("selected_output_tps_per_mw")) or 0),
            "agentic_target_met_from_long_chat",
        )
    return (
        max(candidates, key=lambda row: (fnum(row.get("selected_tok_s_user")) or 0) / call_multiplier),
        "agentic_best_available_below_target",
    )


def normalize_direct_row(row: dict[str, Any], target: int, source_type: str) -> dict[str, Any]:
    selected_tok_s_user = fnum(row.get("selected_tok_s_user"))
    target_met = bool(selected_tok_s_user is not None and selected_tok_s_user >= target)
    gap = 0.0 if target_met else (target - (selected_tok_s_user or 0)) / target
    workload = str(row["workload_type"]).replace("_chat", "").replace("agentic_derived", "agentic")
    return {
        "proxy_model": row["proxy_model"],
        "source_model_scope": row.get("source_model_scope", ""),
        "gpu": str(row["gpu"]).upper(),
        "workload": workload,
        "target_tok_s_user": target,
        "target_met": target_met,
        "slo_gap_pct": gap,
        "effective_output_tps_per_mw": fnum(row.get("selected_output_tps_per_mw")),
        "selected_tok_s_user": selected_tok_s_user,
        "precision": row.get("selected_precision", ""),
        "framework": row.get("selected_framework", ""),
        "concurrency": row.get("selected_concurrency", ""),
        "isl": row.get("selected_isl", ""),
        "osl": row.get("selected_osl", ""),
        "selection_status": row.get("selection_status", ""),
        "source_type": source_type,
        "confidence": "medium" if target_met else "low_target_gap",
        "benchmark_date": row.get("benchmark_date", ""),
        "method_note": row.get("method_note", ""),
    }


def build_rows() -> list[dict[str, Any]]:
    data = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    raw_profiles = data["interactivity_reference_profiles"]
    agentic_multiplier = read_agentic_multiplier()
    profiles = {
        (row["proxy_model"], row["gpu"], row["workload_type"], int(row["target_tok_s_user"])): row
        for row in raw_profiles
    }

    proxy_models = sorted({row["proxy_model"] for row in raw_profiles})
    gpus = ["h200", "b200", "gb200"]
    targets = [10, 30, 50, 70, 100]
    output: list[dict[str, Any]] = []

    for proxy_model in proxy_models:
        for gpu in gpus:
            for workload_type in ("short_chat", "long_chat"):
                for target in targets:
                    row, source_kind = get_best_profile(profiles, proxy_model, gpu, workload_type, target)
                    if row is None:
                        output.append(
                            {
                                "proxy_model": proxy_model,
                                "source_model_scope": "",
                                "gpu": gpu.upper(),
                                "workload": workload_type.replace("_chat", ""),
                                "target_tok_s_user": target,
                                "target_met": False,
                                "slo_gap_pct": "",
                                "effective_output_tps_per_mw": "",
                                "selected_tok_s_user": "",
                                "precision": "",
                                "framework": "",
                                "concurrency": "",
                                "isl": "",
                                "osl": "",
                                "selection_status": "missing",
                                "source_type": "no_benchmark_row",
                                "confidence": "missing",
                                "benchmark_date": "",
                                "method_note": "No model/GPU/workload benchmark row was available.",
                            }
                        )
                    else:
                        source_type = "direct_target_row" if source_kind == "target_met_row" else "best_available_below_target"
                        output.append(normalize_direct_row(row, target, source_type))

            for target in targets:
                long_row, source_kind = get_agentic_parent_profile(
                    profiles,
                    proxy_model,
                    gpu,
                    target,
                    agentic_multiplier,
                )
                if long_row is None:
                    output.append(
                        {
                            "proxy_model": proxy_model,
                            "source_model_scope": "",
                            "gpu": gpu.upper(),
                            "workload": "agentic",
                            "target_tok_s_user": target,
                            "target_met": False,
                            "slo_gap_pct": "",
                            "effective_output_tps_per_mw": "",
                            "selected_tok_s_user": "",
                            "precision": "",
                            "framework": "",
                            "concurrency": "",
                            "isl": "",
                            "osl": "",
                            "selection_status": "missing",
                            "source_type": "no_long_chat_proxy_row",
                            "confidence": "missing",
                            "benchmark_date": "",
                            "method_note": "Agentic proxy could not be derived because no long-chat benchmark row was available.",
                        }
                    )
                    continue

                base_tps = fnum(long_row.get("selected_output_tps_per_mw"))
                base_tok_s_user = fnum(long_row.get("selected_tok_s_user"))
                agent_tps = base_tps / agentic_multiplier if base_tps is not None else None
                agent_tok_s_user = base_tok_s_user / agentic_multiplier if base_tok_s_user is not None else None
                target_met = bool(agent_tok_s_user is not None and agent_tok_s_user >= target)
                gap = 0.0 if target_met else (target - (agent_tok_s_user or 0)) / target
                output.append(
                    {
                        "proxy_model": proxy_model,
                        "source_model_scope": long_row.get("source_model_scope", ""),
                        "gpu": gpu.upper(),
                        "workload": "agentic",
                        "target_tok_s_user": target,
                        "target_met": target_met,
                        "slo_gap_pct": gap,
                        "effective_output_tps_per_mw": agent_tps,
                        "selected_tok_s_user": agent_tok_s_user,
                        "precision": long_row.get("selected_precision", ""),
                        "framework": long_row.get("selected_framework", ""),
                        "concurrency": long_row.get("selected_concurrency", ""),
                        "isl": long_row.get("selected_isl", ""),
                        "osl": long_row.get("selected_osl", ""),
                        "selection_status": "agentic_from_long_chat",
                        "source_type": "dynamic_reasoning_proxy",
                        "confidence": "medium_low" if target_met else "low_target_gap",
                        "benchmark_date": long_row.get("benchmark_date", ""),
                        "method_note": (
                            f"Agentic throughput = long-chat output TPS/MW divided by {agentic_multiplier:.1f}x "
                            "LLM call multiplier from dynamic reasoning / AgentBench analysis. "
                            f"Long-chat source selection: {long_row.get('selection_status', '')}; {source_kind}."
                        ),
                    }
                )

    return output


def write_csv(rows: list[dict[str, Any]]) -> None:
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in OUTPUT_COLUMNS})


def write_markdown(rows: list[dict[str, Any]]) -> None:
    generated = date.today().isoformat()
    agentic_multiplier = read_agentic_multiplier()
    selected = [
        row
        for row in rows
        if row["selection_status"] != "missing"
        and row["target_tok_s_user"] in (10, 30, 50, 70, 100)
    ]
    by_workload = []
    for workload in ("short", "long", "agentic"):
        vals = [
            fnum(row["effective_output_tps_per_mw"])
            for row in selected
            if row["workload"] == workload and fnum(row["effective_output_tps_per_mw"]) is not None
        ]
        by_workload.append(
            [
                workload,
                len(vals),
                fmt_num(min(vals) if vals else None),
                fmt_num(sum(vals) / len(vals) if vals else None),
                fmt_num(max(vals) if vals else None),
            ]
        )

    recommended_rows = []
    for row in rows:
        if row["selection_status"] == "missing":
            continue
        if row["target_met"]:
            recommended_rows.append(row)
    recommended_rows.sort(
        key=lambda row: (
            row["proxy_model"],
            row["gpu"],
            row["workload"],
            -int(row["target_tok_s_user"]),
            -(fnum(row["effective_output_tps_per_mw"]) or 0),
        )
    )
    best_by_combo: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in recommended_rows:
        best_by_combo.setdefault((row["proxy_model"], row["gpu"], row["workload"]), row)

    full_rows = []
    for row in rows:
        full_rows.append(
            [
                f"`{row['proxy_model']}`",
                row["gpu"],
                row["workload"],
                row["target_tok_s_user"],
                "Y" if row["target_met"] else "N",
                fmt_pct(row["slo_gap_pct"]),
                fmt_num(row["effective_output_tps_per_mw"]),
                fmt_num(row["selected_tok_s_user"], 2),
                row["precision"],
                row["framework"],
                row["concurrency"],
                row["source_type"],
            ]
        )

    best_rows = []
    for row in sorted(best_by_combo.values(), key=lambda r: (r["proxy_model"], r["gpu"], r["workload"])):
        best_rows.append(
            [
                f"`{row['proxy_model']}`",
                row["gpu"],
                row["workload"],
                row["target_tok_s_user"],
                fmt_num(row["effective_output_tps_per_mw"]),
                fmt_num(row["selected_tok_s_user"], 2),
                row["precision"],
                row["framework"],
                row["concurrency"],
                row["source_type"],
            ]
        )

    text = f"""# Model/GPU/Workload Interactivity TPS/MW Reference

작성일: {generated}

## 목적

이 표는 전력 기반 token capacity 엑셀에서 사용자가 `proxy_model`, `GPU`, `workload(short/long/agentic)`, `interactivity target`별로 output token throughput per MW를 선택할 수 있도록 만든 정리표다.

## 기준

- 단위: generated output tokens/sec/MW.
- Interactivity target: `10`, `30`, `50`, `70`, `100` tok/s/user.
- Short workload: `ISL/OSL 1024/1024`.
- Long workload: `ISL/OSL 8192/1024`.
- Agentic workload: 직접 matched agentic benchmark가 부족하므로 long workload TPS/MW를 dynamic reasoning coefficient로 보정한다.
- Agentic coefficient: `{agentic_multiplier:.1f}x` LLM calls/request, 즉 effective throughput은 long-chat 대비 `{1 / agentic_multiplier:.1%}`.
- Precision/concurrency/framework는 선택된 InferenceX row 또는 long-chat proxy row의 실제 조건을 그대로 유지한다.
- `target_met = FALSE`는 해당 interactivity에서 SLO를 만족했다고 보기 어렵다는 뜻이다. 이 경우 숫자는 sensitivity/proxy로만 쓰고, production capacity로 단정하지 않는다.

## Workload별 범위

{md_table(["Workload", "Rows with value", "Min TPS/MW", "Average TPS/MW", "Max TPS/MW"], by_workload)}

## Target을 만족하는 최대 interactivity 추천 row

{md_table(["Model", "GPU", "Workload", "Max target", "TPS/MW", "Actual tok/s/user", "Precision", "Framework", "Concurrency", "Source type"], best_rows)}

## 전체 reference table

{md_table(["Model", "GPU", "Workload", "Target", "Target met", "SLO gap", "TPS/MW", "Actual tok/s/user", "Precision", "Framework", "Concurrency", "Source type"], full_rows)}

## 해석 메모

- `direct_target_row`: target interactivity 이상을 만족하는 InferenceX row에서 TPS/MW가 높은 row를 선택했다.
- `best_available_below_target`: 해당 target을 만족하는 row가 없어 같은 model/GPU/workload에서 관측 가능한 최고 tok/s/user row를 proxy로 남겼다.
- `dynamic_reasoning_proxy`: long-chat row에 AgentBench/dynamic reasoning의 agentic call multiplier를 적용한 proxy다.
- `missing`: 해당 model/GPU/workload에 사용할 benchmark 또는 long-chat proxy row가 없다.
- 이 파일은 public benchmark/proxy reference이며 OpenAI, Anthropic, Google 등 closed production serving telemetry가 아니다.

## 연결 파일

- CSV: `model_gpu_workload_interactivity_tps_mw_reference.csv`
- 엑셀 시트: `llm_token_capacity_2026_2030.xlsx`의 `00a_Proxy_TPS_MW`
"""
    OUT_MD.write_text(text, encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} rows")
    print(OUT_CSV)
    print(OUT_MD)


if __name__ == "__main__":
    main()
