"""Generate CoT/agentic TPS-per-GPU overlays from InferenceX benchmark rows.

The overlay keeps InferenceX's measured GPU, GPU count, concurrency, ISL/OSL,
framework, and precision fields unchanged. It only converts single-turn
benchmark throughput into user-visible dynamic-reasoning throughput by applying
call-count multipliers and per-user interactivity levels.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "inferencex" / "inferencex_benchmark.sqlite"
DEFAULT_OUT_DIR = ROOT / "docs" / "dynamic_reasoning_agent_cost"
DEFAULT_GITHUB_SOURCE = (
    "https://github.com/SemiAnalysisAI/InferenceX-app/releases/tag/db-dump/2026-06-08"
)


@dataclass(frozen=True)
class WorkloadScenario:
    workload_type: str
    scenario_label_kr: str
    call_multiplier: float
    source_anchor: str


SCENARIOS = [
    WorkloadScenario(
        workload_type="cot",
        scenario_label_kr="CoT/단일 추론",
        call_multiplier=1.0,
        source_anchor="CoT/ShareGPT single-pass baseline",
    ),
    WorkloadScenario(
        workload_type="agentic",
        scenario_label_kr="Agentic/ReAct 도구 사용",
        call_multiplier=9.2,
        source_anchor="Dynamic reasoning paper: agentic systems use 9.2x more LLM calls than CoT on average",
    ),
]

INTERACTIVITY_TOK_S_USER_LEVELS = [30, 50, 70]


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"{db_path} does not exist.")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_main_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT
                benchmark_id,
                dashboard_tab,
                model,
                model_family,
                gpu,
                gpu_vendor,
                gpu_count,
                framework,
                runtime,
                precision,
                main_framework,
                main_precision,
                is_main_model_config,
                main_config_reason,
                isl,
                osl,
                concurrency,
                benchmark_type,
                benchmark_date,
                tok_s_gpu,
                input_tok_s_gpu,
                output_tok_s_gpu,
                tok_s_mw,
                input_tok_s_mw,
                output_tok_s_mw,
                total_tok_s_mw,
                p99_ttft_ms,
                p99_tpot_ms,
                mean_tpot_ms,
                median_tpot_ms,
                joules_token,
                j_output_token,
                power_w,
                cost_per_million_tokens_usd,
                cost_retail_per_mtok_usd,
                source_url,
                caveat
            FROM benchmark_results
            WHERE is_main_model_config = 'yes'
              AND benchmark_type = 'single_turn'
              AND output_tok_s_gpu IS NOT NULL
              AND output_tok_s_gpu > 0
              AND osl IS NOT NULL
              AND osl > 0
            ORDER BY model, gpu, isl, osl, concurrency, gpu_count, benchmark_id
            """
        )
    )


def fnum(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def tpot_to_tok_s_user(value: Any) -> float:
    tpot = fnum(value)
    if tpot <= 0:
        return 0.0
    # InferenceX dump fields are named *_ms, but recent rows store seconds-scale
    # TPOT values such as 0.0218 for about 45.9 tok/s/user.
    return 1.0 / tpot if tpot < 1 else 1000.0 / tpot


def build_overlay_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for row in rows:
        base_output_tps_gpu = fnum(row["output_tok_s_gpu"])
        base_total_tps_gpu = fnum(row["tok_s_gpu"])
        base_input_tps_gpu = fnum(row["input_tok_s_gpu"])
        osl = fnum(row["osl"])
        realized_tok_s_user = tpot_to_tok_s_user(
            row["median_tpot_ms"] if row["median_tpot_ms"] is not None else row["mean_tpot_ms"]
        )

        for scenario in SCENARIOS:
            for tok_s_user in INTERACTIVITY_TOK_S_USER_LEVELS:
                scenario_output_tps_gpu = base_output_tps_gpu / scenario.call_multiplier
                scenario_total_tps_gpu = (
                    base_total_tps_gpu / scenario.call_multiplier
                    if base_total_tps_gpu
                    else ""
                )
                scenario_output_tps_mw = (
                    fnum(row["output_tok_s_mw"]) / scenario.call_multiplier
                    if row["output_tok_s_mw"] is not None
                    else ""
                )
                output_rows.append(
                    {
                        "benchmark_id": row["benchmark_id"],
                        "model": row["model"],
                        "model_family": row["model_family"],
                        "gpu": str(row["gpu"]).upper(),
                        "gpu_vendor": row["gpu_vendor"],
                        "gpu_count": row["gpu_count"],
                        "concurrency": row["concurrency"],
                        "isl": row["isl"],
                        "osl": row["osl"],
                        "framework": row["framework"],
                        "precision": row["precision"],
                        "main_framework": row["main_framework"],
                        "main_precision": row["main_precision"],
                        "is_main_model_config": row["is_main_model_config"],
                        "benchmark_date": row["benchmark_date"],
                        "workload_type": scenario.workload_type,
                        "scenario_label_kr": scenario.scenario_label_kr,
                        "interactivity_tok_s_user": tok_s_user,
                        "scenario_call_multiplier": scenario.call_multiplier,
                        "effective_call_multiplier": scenario.call_multiplier,
                        "base_total_tok_s_gpu": base_total_tps_gpu,
                        "base_input_tok_s_gpu": base_input_tps_gpu,
                        "base_output_tok_s_gpu": base_output_tps_gpu,
                        "scenario_output_tok_s_gpu": scenario_output_tps_gpu,
                        "scenario_total_tok_s_gpu": scenario_total_tps_gpu,
                        "realized_tok_s_user": realized_tok_s_user,
                        "target_tok_s_user_distance_pct": (
                            abs(realized_tok_s_user - tok_s_user) / tok_s_user
                            if realized_tok_s_user
                            else ""
                        ),
                        "users_per_gpu_at_interactivity": (
                            fnum(scenario_total_tps_gpu) if scenario_total_tps_gpu != "" else 0
                        )
                        / tok_s_user,
                        "requests_s_gpu_by_osl": scenario_output_tps_gpu / osl,
                        "base_output_tok_s_mw": row["output_tok_s_mw"],
                        "scenario_output_tok_s_mw": scenario_output_tps_mw,
                        "p99_ttft_ms": row["p99_ttft_ms"],
                        "p99_tpot_ms": row["p99_tpot_ms"],
                        "mean_tpot_ms": row["mean_tpot_ms"],
                        "median_tpot_ms": row["median_tpot_ms"],
                        "power_w": row["power_w"],
                        "j_output_token": row["j_output_token"],
                        "cost_per_million_tokens_usd": row[
                            "cost_per_million_tokens_usd"
                        ],
                        "cost_retail_per_mtok_usd": row["cost_retail_per_mtok_usd"],
                        "source_anchor": scenario.source_anchor,
                        "source_url": row["source_url"] or DEFAULT_GITHUB_SOURCE,
                        "method_note": (
                            "Main model-config rows only; GPU count, concurrency, ISL/OSL, "
                            "framework, and precision are preserved from InferenceX. "
                            "CoT and agentic scenarios are calculated separately; "
                            "interactivity is tokens/sec/user, not workload mix share."
                        ),
                    }
                )
    return output_rows


def percentile(values: list[float], q: float) -> float:
    clean = sorted(values)
    if not clean:
        return 0.0
    if len(clean) == 1:
        return clean[0]
    pos = (len(clean) - 1) * q
    lower = int(pos)
    upper = min(lower + 1, len(clean) - 1)
    weight = pos - lower
    return clean[lower] * (1.0 - weight) + clean[upper] * weight


def build_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["model"],
            row["gpu"],
            row["main_framework"],
            row["main_precision"],
            row["isl"],
            row["osl"],
            row["workload_type"],
            row["interactivity_tok_s_user"],
        )
        grouped.setdefault(key, []).append(row)

    summary_rows: list[dict[str, Any]] = []
    for key, items in grouped.items():
        model, gpu, main_framework, main_precision, isl, osl, workload_type, tok_s_user = key
        candidates = [item for item in items if fnum(item["realized_tok_s_user"]) > 0]
        if candidates:
            latest_date = max(str(item["benchmark_date"]) for item in candidates)
            latest_candidates = [
                item for item in candidates if str(item["benchmark_date"]) == latest_date
            ]
            selected = min(
                latest_candidates,
                key=lambda item: (
                    fnum(item["target_tok_s_user_distance_pct"], 999),
                    -fnum(item["base_total_tok_s_gpu"]),
                ),
            )
        else:
            selected = max(items, key=lambda item: str(item["benchmark_date"]))

        effective_multiplier = fnum(selected["effective_call_multiplier"])
        summary_rows.append(
            {
                "selected_benchmark_id": selected["benchmark_id"],
                "model": model,
                "gpu": gpu,
                "main_framework": main_framework,
                "main_precision": main_precision,
                "isl": isl,
                "osl": osl,
                "workload_type": workload_type,
                "target_tok_s_user": tok_s_user,
                "realized_tok_s_user": selected["realized_tok_s_user"],
                "target_tok_s_user_distance_pct": selected["target_tok_s_user_distance_pct"],
                "source_row_count": len(items),
                "benchmark_date": selected["benchmark_date"],
                "gpu_count": selected["gpu_count"],
                "concurrency": selected["concurrency"],
                "effective_call_multiplier": effective_multiplier,
                "base_total_tok_s_gpu": selected["base_total_tok_s_gpu"],
                "base_output_tok_s_gpu": selected["base_output_tok_s_gpu"],
                "scenario_total_tok_s_gpu": selected["scenario_total_tok_s_gpu"],
                "scenario_output_tok_s_gpu": selected["scenario_output_tok_s_gpu"],
                "users_per_gpu": selected["users_per_gpu_at_interactivity"],
                "requests_s_gpu_by_osl": selected["requests_s_gpu_by_osl"],
                "capacity_vs_cot_single_call": (
                    1.0 / effective_multiplier if effective_multiplier else ""
                ),
            }
        )
    return sorted(
        summary_rows,
        key=lambda item: (
            item["model"],
            item["gpu"],
            item["isl"],
            item["osl"],
            item["workload_type"],
            item["target_tok_s_user"],
        ),
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:,.0f}"
    if abs(value) >= 10:
        return f"{value:,.1f}"
    return f"{value:,.3f}".rstrip("0").rstrip(".")


def write_readme(path: Path, detail_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]]) -> None:
    model_count = len({row["model"] for row in detail_rows})
    gpu_count = len({row["gpu"] for row in detail_rows})
    base_rows = len({row["benchmark_id"] for row in detail_rows})

    headline = [
        row
        for row in summary_rows
        if row["workload_type"] == "agentic"
        and row["target_tok_s_user"] in (30, 50, 70)
        and int(row["isl"]) == 1024
        and int(row["osl"]) == 1024
    ][:18]

    table_lines = [
        "| Model | GPU | ISL/OSL | target tok/s/user | realized tok/s/user | Concurrency | Calls/request | Base total tok/s/GPU | Scenario total tok/s/GPU | Users/GPU |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in headline:
        table_lines.append(
            "| {model} | {gpu} | {isl}/{osl} | {target} | {realized} | {concurrency} | {calls} | {base} | {scenario} | {users} |".format(
                model=row["model"],
                gpu=row["gpu"],
                isl=row["isl"],
                osl=row["osl"],
                target=row["target_tok_s_user"],
                realized=fmt(fnum(row["realized_tok_s_user"])),
                concurrency=row["concurrency"],
                calls=fmt(fnum(row["effective_call_multiplier"])),
                base=fmt(fnum(row["base_total_tok_s_gpu"])),
                scenario=fmt(fnum(row["scenario_total_tok_s_gpu"])),
                users=fmt(fnum(row["users_per_gpu"])),
            )
        )

    text = f"""# InferenceX CoT / Agentic TPS per GPU Overlay

이 산출물은 InferenceX의 main model-config benchmark row를 그대로 사용해 CoT와 agentic workload별 `scenario TPS/GPU`와 `users/GPU`를 계산한 것이다.

## 핵심 가정

```text
scenario_total_tok_s_gpu
= InferenceX tok_s_gpu / scenario_call_multiplier

users_per_gpu
= scenario_total_tok_s_gpu / target_tok_s_user
```

- CoT/단일 추론: `scenario_call_multiplier = 1.0`
- Agentic/ReAct 도구 사용: `scenario_call_multiplier = 9.2`
- Interactivity: target `30`, `50`, `70` tok/s/user. 실제 row 선택은 `median_tpot`에서 역산한 realized tok/s/user가 target에 가장 가까운 최신 benchmark row를 사용한다.
- GPU, GPU 수, concurrency, ISL/OSL, framework, precision은 InferenceX 원본 row 값을 유지했다.
- 모델별 `main_framework`, `main_precision`이 맞는 `is_main_model_config = yes` row만 사용했다.

## 왜 이렇게 계산했는가

Agentic workload는 사용자 요청 하나가 내부적으로 여러 번의 LLM call을 발생시킨다. 같은 GPU가 처리할 수 있는 내부 token 처리량은 InferenceX가 측정한 값에 가깝지만, 사용자 관점에서 한 업무를 끝내기 위해 필요한 내부 LLM call 수가 늘어난다.

```text
agentic scenario_total_tok_s_gpu
= InferenceX tok_s_gpu / 9.2
```

그 다음 사용자가 기대하는 응답 속도, 즉 target interactivity를 `30/50/70 tok/s/user`로 두고 GPU 1장이 감당 가능한 동시 사용자 수를 계산한다.

## 사용 데이터

- 원천 DB: `llm_token_capacity_project/data/inferencex/inferencex_benchmark.sqlite`
- 원천 release: {DEFAULT_GITHUB_SOURCE}
- 사용 row 수: {base_rows:,}개 InferenceX benchmark row
- 확장 후 detail row 수: {len(detail_rows):,}개
- 모델 수: {model_count}
- GPU 종류 수: {gpu_count}

## 산출 파일

- `inferencex_dynamic_reasoning_tps_gpu.csv`: row-level detail. 원본 benchmark row마다 CoT/agentic x interactivity 30/50/70 tok/s/user 조합을 붙인 파일.
- `inferencex_dynamic_reasoning_tps_gpu_summary.csv`: model/GPU/ISL/OSL/workload/target tok/s/user별 최신 근접 row 요약.

## Agentic 1024/1024 샘플

{chr(10).join(table_lines)}

## 해석

- CoT와 agentic은 workload 비중을 섞지 않고 각각 계산했다.
- CoT는 call multiplier가 1.0이라 원본 InferenceX total TPS/GPU를 유지한다.
- Agentic은 call multiplier가 9.2라 scenario total TPS/GPU가 CoT 대비 10.9% 수준이다.
- Interactivity 30/50/70은 비중이 아니라 tok/s/user 요구 수준이며, 값이 높을수록 같은 TPS/GPU에서 감당 가능한 users/GPU가 줄어든다.
- 이 값은 LLMServingSim power model의 full simulation을 대체하지 않는다. tool wait, prefix cache, KV cache pressure, SLO 실패율은 아직 단순화되어 있다.
"""
    path.write_text(text, encoding="utf-8")


def select_rows(
    rows: list[dict[str, Any]],
    *,
    workload_type: str,
    target_tok_s_user: int,
    isl: int,
    osl: int,
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row["workload_type"] == workload_type
        and int(row["target_tok_s_user"]) == target_tok_s_user
        and int(row["isl"]) == isl
        and int(row["osl"]) == osl
    ]


def markdown_model_gpu_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Workload | Model | GPU | Framework | Precision | Target tok/s/user | Realized tok/s/user | Conc. | Bench ID | Base total tok/s/GPU | Scenario total tok/s/GPU | Users/GPU | Output tok/s/GPU |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(
        rows,
        key=lambda item: (
            item["model"],
            item["gpu"],
            item["workload_type"],
            int(item["target_tok_s_user"]),
        ),
    ):
        workload = "CoT" if row["workload_type"] == "cot" else "Agentic"
        lines.append(
            "| {workload} | {model} | {gpu} | {framework} | {precision} | {target} | {realized} | {concurrency} | {bench} | {base} | {scenario} | {users} | {output} |".format(
                workload=workload,
                model=row["model"],
                gpu=row["gpu"],
                framework=row["main_framework"],
                precision=row["main_precision"],
                target=row["target_tok_s_user"],
                realized=fmt(fnum(row["realized_tok_s_user"])),
                concurrency=row["concurrency"],
                bench=row["selected_benchmark_id"],
                base=fmt(fnum(row["base_total_tok_s_gpu"])),
                scenario=fmt(fnum(row["scenario_total_tok_s_gpu"])),
                users=fmt(fnum(row["users_per_gpu"])),
                output=fmt(fnum(row["base_output_tok_s_gpu"])),
            )
        )
    return "\n".join(lines)


def markdown_interactivity_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Workload | tok/s/user | Calls/request | Capacity kept vs single-call | 의미 |",
        "|---|---:|---:|---:|---|",
    ]
    seen: set[tuple[str, int]] = set()
    ordered = sorted(
        rows,
        key=lambda item: (
            item["workload_type"],
            int(item["target_tok_s_user"]),
        ),
    )
    for row in ordered:
        key = (row["workload_type"], int(row["target_tok_s_user"]))
        if key in seen:
            continue
        seen.add(key)
        workload = "CoT/단일 추론" if row["workload_type"] == "cot" else "Agentic/ReAct"
        description = (
            "원본 InferenceX TPS/GPU 기준 users/GPU 계산"
            if row["workload_type"] == "cot"
            else "9.2회 내부 LLM call을 먼저 반영한 뒤 users/GPU 계산"
        )
        lines.append(
            "| {workload} | {tok_s_user} | {calls} | {kept:.1f}% | {description} |".format(
                workload=workload,
                tok_s_user=row["target_tok_s_user"],
                calls=fmt(fnum(row["effective_call_multiplier"])),
                kept=fnum(row["capacity_vs_cot_single_call"]) * 100,
                description=description,
            )
        )
    return "\n".join(lines)


def sequence_median_rows(rows: list[dict[str, Any]], workload_type: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for isl, osl in [(1024, 1024), (8192, 1024), (1024, 8192)]:
        subset = select_rows(
            rows,
            workload_type=workload_type,
            target_tok_s_user=50,
            isl=isl,
            osl=osl,
        )
        if not subset:
            continue
        scenario_values = sorted(fnum(row["scenario_total_tok_s_gpu"]) for row in subset)
        users_values = sorted(fnum(row["users_per_gpu"]) for row in subset)
        output.append(
            {
                "workload_type": workload_type,
                "isl": isl,
                "osl": osl,
                "groups": len(subset),
                "scenario_group_median": percentile(scenario_values, 0.50),
                "users_group_median": percentile(users_values, 0.50),
            }
        )
    return output


def markdown_sequence_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Workload | ISL/OSL | Groups | Scenario total tok/s/GPU group median | Users/GPU group median at 50 tok/s/user |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        workload = "CoT" if row["workload_type"] == "cot" else "Agentic"
        lines.append(
            "| {workload} | {isl}/{osl} | {groups} | {scenario} | {users} |".format(
                workload=workload,
                isl=row["isl"],
                osl=row["osl"],
                groups=row["groups"],
                scenario=fmt(row["scenario_group_median"]),
                users=fmt(row["users_group_median"]),
            )
        )
    return "\n".join(lines)


def write_results(path: Path, summary_rows: list[dict[str, Any]]) -> None:
    all_1024 = [
        row for row in summary_rows if int(row["isl"]) == 1024 and int(row["osl"]) == 1024
    ]
    cot_1024 = [
        row
        for row in summary_rows
        if row["workload_type"] == "cot"
        and int(row["isl"]) == 1024
        and int(row["osl"]) == 1024
    ]
    agentic_1024 = [
        row
        for row in summary_rows
        if row["workload_type"] == "agentic"
        and int(row["isl"]) == 1024
        and int(row["osl"]) == 1024
    ]
    sequence_rows = sequence_median_rows(summary_rows, "cot") + sequence_median_rows(
        summary_rows, "agentic"
    )

    text = f"""# InferenceX CoT / Agentic 결과 정리

이 문서는 `inferencex_dynamic_reasoning_tps_gpu_summary.csv`를 사람이 바로 읽기 좋게 정리한 결과표다.

## 결론 먼저

- CoT/단일 추론은 call multiplier가 1.0이라 InferenceX 원본 `tok_s_gpu`를 그대로 사용한다.
- Agentic/ReAct workload는 논문 근거의 평균 `9.2x` LLM call multiplier를 적용했다.
- `30/50/70`은 workload 비중이 아니라 사용자당 요구 처리량인 `tok/s/user`다.
- CoT와 agentic의 비중을 모르므로 두 workload를 섞지 않고 각각 계산했다.
- target tok/s/user별로 최신 benchmark date에서 realized tok/s/user가 가장 가까운 row를 선택한다.
- `users/GPU = scenario_total_tok_s_gpu / target_tok_s_user`로 해석한다.
- 이 결과는 아직 tool wait, prefix cache, KV cache pressure, SLO 실패율을 반영하지 않은 1차 overlay다.

## Interactivity별 전체 효과

{markdown_interactivity_table(all_1024)}

## ISL/OSL별 중간값 효과

아래 표는 `50 tok/s/user` 기준이다. `group median`은 model/GPU 조합별 선택 row 값을 다시 중앙값으로 본 것이다.

{markdown_sequence_table(sequence_rows)}

## 1024/1024 기준 모델/GPU별 결과

아래 표는 가장 기본 비교축인 `ISL=1024`, `OSL=1024` 기준이다. GPU 수, concurrency, framework, precision은 원본 InferenceX row를 유지했고, 모델별 main framework/precision row만 사용했다.

### CoT

{markdown_model_gpu_table(cot_1024)}

### Agentic

{markdown_model_gpu_table(agentic_1024)}

## 읽는 법

- `Base total tok/s/GPU`: InferenceX의 원본 total token throughput이다. InferenceX UI의 TPS/GPU와 맞추기 위해 이 값을 기본 벤치 TPS로 사용한다.
- `Output tok/s/GPU`: 같은 row의 output token throughput이다. ISL=OSL에서는 대체로 total의 절반에 가깝다.
- `Scenario total tok/s/GPU`: CoT는 원본 total TPS/GPU, agentic은 원본 total TPS/GPU를 9.2로 나눈 값이다.
- `Users/GPU`: 해당 target tok/s/user 기준으로 GPU 1장이 감당 가능한 사용자 수 근사값이다. `scenario total tok/s/GPU / target tok/s/user`로 계산한다.
- `Realized tok/s/user`: 선택된 InferenceX row의 `median_tpot`에서 역산한 실제 tok/s/user다. target과 정확히 같지 않을 수 있다.
- 이 표는 “전력 기반 토큰 생산량”에 바로 곱할 수 있는 candidate workload factor를 제공하지만, 최종 계수로 확정하려면 LLMServingSim power model에서 idle/standby/prefix-cache/KV-cache를 추가 검증해야 한다.
"""
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with connect(args.db) as conn:
        base_rows = fetch_main_rows(conn)
    detail_rows = build_overlay_rows(base_rows)
    summary_rows = build_summary_rows(detail_rows)

    write_csv(args.out_dir / "inferencex_dynamic_reasoning_tps_gpu.csv", detail_rows)
    write_csv(
        args.out_dir / "inferencex_dynamic_reasoning_tps_gpu_summary.csv",
        summary_rows,
    )
    write_readme(
        args.out_dir / "inferencex_dynamic_reasoning_tps_gpu.md",
        detail_rows,
        summary_rows,
    )
    write_results(
        args.out_dir / "inferencex_dynamic_reasoning_results_kr.md",
        summary_rows,
    )
    print(
        f"Wrote {len(detail_rows):,} detail rows and {len(summary_rows):,} summary rows to {args.out_dir}"
    )


if __name__ == "__main__":
    main()
