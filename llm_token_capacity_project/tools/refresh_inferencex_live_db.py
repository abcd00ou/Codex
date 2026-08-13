"""Refresh the local InferenceX benchmark database from the official live API.

The public GitHub release is sometimes a split PostgreSQL dump that cannot be
consumed by the lightweight dump normalizer.  The dashboard's history endpoint
exposes the same benchmark rows for the supported scenarios, so this command
rebuilds the normalized benchmark tables from that auditable live source.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from build_inferencex_benchmark_db import build_database  # noqa: E402
from fetch_inferencex_data import (  # noqa: E402
    DUMP_BENCHMARK_HEADERS,
    DUMP_SUMMARY_HEADERS,
    GPU_REGISTRY,
    META_DIR,
    MODEL_CONFIG_VALIDATION_HEADERS,
    MODEL_MAIN_CONFIG_HEADERS,
    NORM_DIR,
    ROOT,
    apply_model_main_configs,
    as_float,
    bool_to_int,
    fetch_json,
    infer_model_main_configs,
    money_per_mtok,
    normalize_hardware_key,
    seconds_to_ms,
    summarize_benchmark_rows,
    total_gpu_count,
    validate_model_main_configs,
)

API_ROOT = "https://inferencex.semianalysis.com/api/v1"
LIVE_DIR = ROOT / "data" / "inferencex" / "live_api"
DEFAULT_DB = ROOT / "data" / "inferencex" / "inferencex_benchmark.sqlite"

COLUMN_AUDIT_HEADERS = [
    "column_name",
    "lineage_type",
    "source_field",
    "transformation",
    "unit",
    "non_null_rows",
    "total_rows",
    "coverage_pct",
    "distinct_values",
    "status",
    "null_policy",
    "notes",
]

QUALITY_CHECK_HEADERS = ["check_id", "status", "checked_rows", "failed_rows", "details"]

# Display names are the public API contract in InferenceX-app's models.ts.
DISPLAY_MODELS = (
    "DeepSeek-R1-0528",
    "gpt-oss-120b",
    "Llama-3.3-70B-Instruct-FP8",
    "Qwen-3.5-397B-A17B",
    "Kimi-K2.5",
    "Kimi-K3",
    "MiniMax-M2.5",
    "MiniMax-M3",
    "GLM-5",
    "GLM-5.2",
    "DeepSeek-V4-Pro",
)

SEQUENCES = (
    ("short", 1024, 1024),
    ("long", 8192, 1024),
    ("long_output", 1024, 8192),
)

PROXY_LATEST_FILES = {
    "DeepSeek-V4-Pro": "deepseek_v4_pro.json",
    "Kimi-K2.5": "kimi_k2_5.json",
    "MiniMax-M3": "minimax_m3.json",
    "GLM-5.2": "glm_5_2.json",
    "Qwen-3.5-397B-A17B": "qwen_3_5.json",
}


def api_url(path: str, **params: Any) -> str:
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value is not None})
    return f"{API_ROOT}/{path}?{query}" if query else f"{API_ROOT}/{path}"


def iso_date(value: Any) -> str:
    date = str(value or "")[:10]
    return f"{date}T00:00:00.000Z" if date else ""


def workflow_run_id(run_url: Any) -> str:
    match = re.search(r"/actions/runs/(\d+)", str(run_url or ""))
    return match.group(1) if match else ""


def source_label(source_url: str) -> str:
    path = urllib.parse.urlsplit(source_url).path.removeprefix("/api/v1/")
    return f"inferencex_api:{path}"


def normalize_live_row(record: dict[str, Any], source_url: str) -> dict[str, Any]:
    metrics = record.get("metrics") or {}
    hardware = normalize_hardware_key(record.get("hardware"))
    gpu = GPU_REGISTRY.get(hardware, {})
    power_kw = as_float(gpu.get("power_kw"))
    power_w = power_kw * 1000 if power_kw else None
    total_tput = as_float(metrics.get("tput_per_gpu"))
    input_tput = as_float(metrics.get("input_tput_per_gpu"))
    output_tput = as_float(metrics.get("output_tput_per_gpu"))

    def per_mw(value: float | None) -> float | None:
        return value * 1000 / power_kw if value and power_kw else None

    total_tput_mw = per_mw(total_tput)
    input_tput_mw = per_mw(input_tput)
    output_tput_mw = per_mw(output_tput)
    run_url = record.get("run_url") or ""
    return {
        "source_file": source_label(source_url),
        "source_kind": "inferencex_live_api_history",
        "benchmark_id": record.get("id"),
        "dashboard_tab": "inference_performance",
        "model": record.get("model"),
        "model_family": record.get("model"),
        "gpu": hardware,
        "gpu_vendor": gpu.get("gpu_vendor", ""),
        "gpu_count": total_gpu_count(record),
        "framework": record.get("framework"),
        "runtime": record.get("image") or "",
        "precision": record.get("precision"),
        "main_framework": "",
        "main_precision": "",
        "is_main_model_config": "",
        "main_config_reason": "",
        "isl": record.get("isl"),
        "osl": record.get("osl"),
        "concurrency": record.get("conc"),
        "batch_size": "",
        "metric_name": "tput_per_gpu",
        "metric_value": total_tput,
        "metric_unit": "tokens/s/GPU",
        "tok_s_user": metrics.get("median_intvty"),
        "tok_s_gpu": total_tput,
        "tok_s_mw": total_tput_mw,
        "input_tok_s_gpu": input_tput,
        "output_tok_s_gpu": output_tput,
        "joules_token": power_w / output_tput if power_w and output_tput else "",
        "p99_ttft_ms": seconds_to_ms(metrics.get("p99_ttft")),
        "p99_tpot_ms": seconds_to_ms(metrics.get("p99_tpot")),
        "cost_per_million_tokens_usd": money_per_mtok(as_float(gpu.get("costh")), output_tput),
        "power_w": power_w,
        "benchmark_date": iso_date(record.get("date")),
        "github_run_url": run_url,
        "source_url": source_url,
        "evidence_class": "Proxy/Benchmark",
        "caveat": (
            "InferenceX live API history row. Benchmark/proxy only; not company production telemetry. "
            "Match ISL/OSL/framework/precision before using."
        ),
        "benchmark_type": record.get("benchmark_type"),
        "spec_method": record.get("spec_method"),
        "disagg": bool_to_int(record.get("disagg")),
        "is_multinode": bool_to_int(record.get("is_multinode")),
        "offload_mode": record.get("offload_mode"),
        "prefill_tp": record.get("prefill_tp"),
        "prefill_ep": record.get("prefill_ep"),
        "prefill_dp_attention": bool_to_int(record.get("prefill_dp_attention")),
        "prefill_num_workers": record.get("prefill_num_workers"),
        "decode_tp": record.get("decode_tp"),
        "decode_ep": record.get("decode_ep"),
        "decode_dp_attention": bool_to_int(record.get("decode_dp_attention")),
        "decode_num_workers": record.get("decode_num_workers"),
        "num_prefill_gpu": record.get("num_prefill_gpu"),
        "num_decode_gpu": record.get("num_decode_gpu"),
        "config_id": "",
        "workflow_run_id": workflow_run_id(run_url),
        "error": "",
        "mean_ttft_ms": seconds_to_ms(metrics.get("mean_ttft")),
        "mean_tpot_ms": seconds_to_ms(metrics.get("mean_tpot")),
        "median_ttft_ms": seconds_to_ms(metrics.get("median_ttft")),
        "median_tpot_ms": seconds_to_ms(metrics.get("median_tpot")),
        "median_itl_ms": seconds_to_ms(metrics.get("median_itl")),
        "mean_e2el_s": metrics.get("mean_e2el"),
        "median_e2el_s": metrics.get("median_e2el"),
        "p99_e2el_s": metrics.get("p99_e2el"),
        "p99_itl_ms": seconds_to_ms(metrics.get("p99_itl")),
        "total_tok_s_mw": total_tput_mw,
        "output_tok_s_mw": output_tput_mw,
        "input_tok_s_mw": input_tput_mw,
        "j_total_token": power_w / total_tput if power_w and total_tput else "",
        "j_output_token": power_w / output_tput if power_w and output_tput else "",
        "j_input_token": power_w / input_tput if power_w and input_tput else "",
        "cost_hyperscaler_per_mtok_usd": money_per_mtok(as_float(gpu.get("costh")), output_tput),
        "cost_neocloud_per_mtok_usd": money_per_mtok(as_float(gpu.get("costn")), output_tput),
        "cost_retail_per_mtok_usd": money_per_mtok(as_float(gpu.get("costr")), output_tput),
    }


DIRECT_LINEAGE: dict[str, tuple[str, str, str, str, str]] = {
    "benchmark_id": ("id", "direct", "identifier", "required", "Globally unique InferenceX result id."),
    "model": ("model", "direct", "slug", "required", "InferenceX DB model key."),
    "model_family": ("model", "direct alias", "slug", "required", "Same source key as model."),
    "gpu": ("hardware", "lower-case base-key normalization", "slug", "required", "Validated against GPU_REGISTRY."),
    "gpu_vendor": ("hardware -> GPU_REGISTRY.vendor", "registry lookup", "name", "required", "Official InferenceX hardware registry."),
    "framework": ("framework", "direct", "slug", "required", "Serving framework/orchestrator."),
    "runtime": ("image", "direct", "container image", "source-optional", "Older rows may omit the image."),
    "precision": ("precision", "direct", "slug", "required", "Weight/serving precision."),
    "isl": ("isl", "direct", "tokens/request", "scenario-conditional", "Null only for agentic_traces."),
    "osl": ("osl", "direct", "tokens/request", "scenario-conditional", "Null only for agentic_traces."),
    "concurrency": ("conc", "direct", "concurrent requests", "required", "Benchmark sweep concurrency."),
    "tok_s_user": ("metrics.median_intvty", "direct", "tokens/s/user", "required", "Official interactivity metric."),
    "tok_s_gpu": ("metrics.tput_per_gpu", "direct", "tokens/s/GPU", "required", "Combined input+output throughput."),
    "input_tok_s_gpu": ("metrics.input_tput_per_gpu", "direct", "input tokens/s/GPU", "source-optional", "Absent in some legacy rows; never imputed."),
    "output_tok_s_gpu": ("metrics.output_tput_per_gpu", "direct", "output tokens/s/GPU", "source-optional", "Absent in some legacy rows; never imputed."),
    "p99_ttft_ms": ("metrics.p99_ttft", "seconds * 1000", "ms", "source-optional", "Raw InferenceX latency is seconds."),
    "p99_tpot_ms": ("metrics.p99_tpot", "seconds * 1000", "ms/token", "source-optional", "Raw InferenceX latency is seconds."),
    "benchmark_date": ("date", "YYYY-MM-DD -> UTC midnight ISO-8601", "UTC date", "required", "Benchmark run date."),
    "github_run_url": ("run_url", "direct", "URL", "source-optional", "Twenty legacy rows currently lack a run URL."),
    "benchmark_type": ("benchmark_type", "direct", "enum", "required", "single_turn or agentic_traces."),
    "spec_method": ("spec_method", "direct", "slug", "required", "Speculative decoding method."),
    "disagg": ("disagg", "direct", "boolean", "required", "Prefill/decode disaggregation flag."),
    "is_multinode": ("is_multinode", "direct", "boolean", "required", "Multi-node topology flag."),
    "offload_mode": ("offload_mode", "direct", "slug", "required", "KV/cache offload mode."),
    "prefill_tp": ("prefill_tp", "direct", "GPU parallel degree", "required", "Prefill tensor parallelism."),
    "prefill_ep": ("prefill_ep", "direct", "GPU parallel degree", "required", "Prefill expert parallelism."),
    "prefill_dp_attention": ("prefill_dp_attention", "direct", "boolean", "required", "Prefill attention data parallel flag."),
    "prefill_num_workers": ("prefill_num_workers", "direct", "workers", "required", "Prefill worker count."),
    "decode_tp": ("decode_tp", "direct", "GPU parallel degree", "required", "Decode tensor parallelism."),
    "decode_ep": ("decode_ep", "direct", "GPU parallel degree", "required", "Decode expert parallelism."),
    "decode_dp_attention": ("decode_dp_attention", "direct", "boolean", "required", "Decode attention data parallel flag."),
    "decode_num_workers": ("decode_num_workers", "direct", "workers", "required", "Decode worker count."),
    "num_prefill_gpu": ("num_prefill_gpu", "direct", "GPUs", "required", "Physical/logical prefill GPU count from API."),
    "num_decode_gpu": ("num_decode_gpu", "direct", "GPUs", "required", "Physical/logical decode GPU count from API."),
    "workflow_run_id": ("run_url", "extract /actions/runs/{id}", "identifier", "source-optional", "Matches GitHub workflow URL when present."),
    "mean_ttft_ms": ("metrics.mean_ttft", "seconds * 1000", "ms", "source-optional", "Enriched from latest API where available; history view omits it."),
    "mean_tpot_ms": ("metrics.mean_tpot", "seconds * 1000", "ms/token", "source-optional", "Enriched from latest API where available; history view omits it."),
    "median_ttft_ms": ("metrics.median_ttft", "seconds * 1000", "ms", "required", "Raw InferenceX latency is seconds."),
    "median_tpot_ms": ("metrics.median_tpot", "seconds * 1000", "ms/token", "required", "Raw InferenceX latency is seconds."),
    "median_itl_ms": ("metrics.median_itl", "seconds * 1000", "ms/token", "required", "Inter-token latency; agentic interactivity identity uses this field."),
    "mean_e2el_s": ("metrics.mean_e2el", "direct", "s", "source-optional", "Enriched from latest API where available; history view omits it."),
    "median_e2el_s": ("metrics.median_e2el", "direct", "s", "required", "End-to-end latency."),
    "p99_e2el_s": ("metrics.p99_e2el", "direct", "s", "source-optional", "Not emitted for agentic history rows."),
    "p99_itl_ms": ("metrics.p99_itl", "seconds * 1000", "ms/token", "source-optional", "Not emitted for some agentic history rows."),
}

DERIVED_LINEAGE: dict[str, tuple[str, str, str, str, str]] = {
    "gpu_count": ("disagg,num_prefill_gpu,num_decode_gpu", "disagg: prefill+decode; aggregated: decode or prefill", "GPUs", "required", "Total GPUs participating in a benchmark configuration."),
    "metric_value": ("metrics.tput_per_gpu", "alias of tok_s_gpu", "tokens/s/GPU", "required", "Canonical metric value."),
    "tok_s_mw": ("tok_s_gpu,power_w", "tok_s_gpu * 1,000,000 / power_w", "tokens/s/MW", "required", "All-in per-GPU power basis."),
    "total_tok_s_mw": ("tok_s_gpu,power_w", "alias of tok_s_mw", "tokens/s/MW", "required", "Combined-token energy throughput."),
    "input_tok_s_mw": ("input_tok_s_gpu,power_w", "input_tok_s_gpu * 1,000,000 / power_w", "input tokens/s/MW", "source-optional", "Null when source input throughput is absent."),
    "output_tok_s_mw": ("output_tok_s_gpu,power_w", "output_tok_s_gpu * 1,000,000 / power_w", "output tokens/s/MW", "source-optional", "Null when source output throughput is absent."),
    "power_w": ("hardware -> GPU_REGISTRY.power", "all-in kW/GPU * 1000", "W/GPU", "required", "Includes per-GPU host/NIC allocation; not chip TDP."),
    "j_total_token": ("power_w,tok_s_gpu", "power_w / tok_s_gpu", "J/total token", "required", "Combined input+output token energy."),
    "j_input_token": ("power_w,input_tok_s_gpu", "power_w / input_tok_s_gpu", "J/input token", "source-optional", "Null when input throughput is absent."),
    "j_output_token": ("power_w,output_tok_s_gpu", "power_w / output_tok_s_gpu", "J/output token", "source-optional", "Null when output throughput is absent."),
    "joules_token": ("power_w,output_tok_s_gpu", "alias of j_output_token", "J/output token", "source-optional", "Legacy generic name; output-token basis."),
    "cost_per_million_tokens_usd": ("GPU_REGISTRY.costh,output_tok_s_gpu", "costh / (output_tok_s_gpu*3600) * 1e6", "USD/million output tokens", "source-optional", "Legacy generic name; hyperscaler/output-token basis."),
    "cost_hyperscaler_per_mtok_usd": ("GPU_REGISTRY.costh,output_tok_s_gpu", "costh / (output_tok_s_gpu*3600) * 1e6", "USD/million output tokens", "source-optional", "Official hyperscaler rate assumption."),
    "cost_neocloud_per_mtok_usd": ("GPU_REGISTRY.costn,output_tok_s_gpu", "costn / (output_tok_s_gpu*3600) * 1e6", "USD/million output tokens", "source-optional", "Official neocloud rate assumption."),
    "cost_retail_per_mtok_usd": ("GPU_REGISTRY.costr,output_tok_s_gpu", "costr / (output_tok_s_gpu*3600) * 1e6", "USD/million output tokens", "source-optional", "Official retail rate assumption."),
}

UNAVAILABLE_LINEAGE: dict[str, tuple[str, str, str, str, str]] = {
    "batch_size": ("not exposed", "none", "requests/batch", "endpoint-unavailable", "Concurrency is available; batch size is not."),
    "config_id": ("not exposed", "none", "identifier", "endpoint-unavailable", "Live history API joins config fields but omits config_id."),
    "error": ("not exposed", "none", "text", "endpoint-unavailable", "Benchmark history endpoint returns successful result rows."),
}

GENERATED_LINEAGE = {
    "source_file": "Compact official API route label; source_url retains the exact request URL.",
    "source_kind": "Constant inferencex_live_api_history.",
    "dashboard_tab": "Constant inference_performance.",
    "main_framework": "Model-level canonical configuration selected after ingestion.",
    "main_precision": "Model-level canonical configuration selected after ingestion.",
    "is_main_model_config": "Derived match against model-level canonical configuration.",
    "main_config_reason": "Selection rule provenance.",
    "metric_name": "Constant tput_per_gpu.",
    "metric_unit": "Constant tokens/s/GPU.",
    "source_url": "Exact official API request URL used for the row.",
    "evidence_class": "Constant Proxy/Benchmark.",
    "caveat": "Constant benchmark-use caveat.",
}


def nonblank(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def build_column_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(rows)
    audit: list[dict[str, Any]] = []
    for column in DUMP_BENCHMARK_HEADERS:
        values = [row.get(column) for row in rows]
        present = [value for value in values if nonblank(value)]
        distinct = len({str(value) for value in present})
        if column in DIRECT_LINEAGE:
            source, transform, unit, null_policy, notes = DIRECT_LINEAGE[column]
            lineage_type = "direct"
        elif column in DERIVED_LINEAGE:
            source, transform, unit, null_policy, notes = DERIVED_LINEAGE[column]
            lineage_type = "derived"
        elif column in UNAVAILABLE_LINEAGE:
            source, transform, unit, null_policy, notes = UNAVAILABLE_LINEAGE[column]
            lineage_type = "unavailable"
        elif column in GENERATED_LINEAGE:
            source, transform, unit, null_policy, notes = (
                "pipeline metadata",
                "generated",
                "metadata",
                "required",
                GENERATED_LINEAGE[column],
            )
            lineage_type = "generated"
        else:
            source, transform, unit, null_policy, notes = "", "", "", "unknown", "Missing lineage definition."
            lineage_type = "unknown"

        coverage = len(present) / total if total else 0
        if null_policy == "endpoint-unavailable" and not present:
            status = "NOT_AVAILABLE"
        elif null_policy in {"source-optional", "scenario-conditional"}:
            status = "PASS" if present else "FAIL"
        elif null_policy == "required":
            status = "PASS" if len(present) == total else "FAIL"
        else:
            status = "FAIL"
        audit.append(
            {
                "column_name": column,
                "lineage_type": lineage_type,
                "source_field": source,
                "transformation": transform,
                "unit": unit,
                "non_null_rows": len(present),
                "total_rows": total,
                "coverage_pct": round(coverage * 100, 6),
                "distinct_values": distinct,
                "status": status,
                "null_policy": null_policy,
                "notes": notes,
            }
        )
    return audit


def run_quality_checks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, failed: int, details: str, checked: int | None = None) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "PASS" if failed == 0 else "FAIL",
                "checked_rows": len(rows) if checked is None else checked,
                "failed_rows": failed,
                "details": details,
            }
        )

    ids = [str(row.get("benchmark_id") or "") for row in rows]
    add("unique_benchmark_id", len(ids) - len(set(ids)), "benchmark_id must be globally unique")

    required = (
        "benchmark_id", "model", "gpu", "gpu_vendor", "gpu_count", "framework", "precision",
        "concurrency", "tok_s_user", "tok_s_gpu", "tok_s_mw", "power_w", "benchmark_date",
        "benchmark_type", "median_ttft_ms", "median_tpot_ms", "median_itl_ms", "median_e2el_s",
    )
    failed = sum(any(not nonblank(row.get(column)) for column in required) for row in rows)
    add("required_field_completeness", failed, ",".join(required))

    positive = ("gpu_count", "concurrency", "tok_s_user", "tok_s_gpu", "tok_s_mw", "power_w")
    failed = sum(any((as_float(row.get(column)) or 0) <= 0 for column in positive) for row in rows)
    add("positive_core_metrics", failed, ",".join(positive))

    failed = sum(not math.isclose(float(row["metric_value"]), float(row["tok_s_gpu"]), rel_tol=1e-12) for row in rows)
    add("metric_value_alias", failed, "metric_value must equal tok_s_gpu")

    failed = sum(
        not math.isclose(float(row["tok_s_mw"]), float(row["tok_s_gpu"]) * 1_000_000 / float(row["power_w"]), rel_tol=1e-12)
        for row in rows
    )
    add("total_tps_mw_formula", failed, "tok_s_mw = tok_s_gpu * 1e6 / power_w")

    failed = sum(not math.isclose(float(row["total_tok_s_mw"]), float(row["tok_s_mw"]), rel_tol=1e-12) for row in rows)
    add("total_tps_mw_alias", failed, "total_tok_s_mw must equal tok_s_mw")

    failed = sum(
        not math.isclose(float(row["j_total_token"]), float(row["power_w"]) / float(row["tok_s_gpu"]), rel_tol=1e-12)
        for row in rows
    )
    add("joules_total_formula", failed, "j_total_token = power_w / tok_s_gpu")

    output_rows = [row for row in rows if nonblank(row.get("output_tok_s_gpu"))]
    failed = sum(
        not math.isclose(float(row["output_tok_s_mw"]), float(row["output_tok_s_gpu"]) * 1_000_000 / float(row["power_w"]), rel_tol=1e-12)
        or not math.isclose(float(row["j_output_token"]), float(row["power_w"]) / float(row["output_tok_s_gpu"]), rel_tol=1e-12)
        for row in output_rows
    )
    add("output_energy_formulas", failed, "Output TPS/MW and joules/token identities", len(output_rows))

    failed = sum(not math.isclose(float(row["gpu_count"]), float(total_gpu_count(row) or 0), rel_tol=0, abs_tol=0) for row in rows)
    add("gpu_count_topology_formula", failed, "disagg uses prefill+decode; aggregated uses one shared pool")

    failed = sum(
        not math.isclose(
            float(row["tok_s_user"]),
            1000
            / float(
                row["median_itl_ms"]
                if row.get("benchmark_type") == "agentic_traces"
                else row["median_tpot_ms"]
            ),
            rel_tol=1e-9,
        )
        for row in rows
    )
    add(
        "interactivity_latency_identity",
        failed,
        "median_intvty = 1000/median_tpot_ms for single_turn and 1000/median_itl_ms for agentic_traces",
    )

    single_turn = [row for row in rows if row.get("benchmark_type") == "single_turn"]
    failed = sum(not nonblank(row.get("isl")) or not nonblank(row.get("osl")) for row in single_turn)
    add("single_turn_sequence_lengths", failed, "single_turn rows require ISL and OSL", len(single_turn))

    agentic = [row for row in rows if row.get("benchmark_type") == "agentic_traces"]
    failed = sum(nonblank(row.get("isl")) or nonblank(row.get("osl")) for row in agentic)
    add("agentic_sequence_null_policy", failed, "agentic_traces use trace shapes, so fixed ISL/OSL must be null", len(agentic))

    disagg_rows = [row for row in rows if row.get("disagg") == 1]
    failed = sum(
        not math.isclose(float(row["gpu_count"]), float(row["num_prefill_gpu"] or 0) + float(row["num_decode_gpu"] or 0), rel_tol=0, abs_tol=0)
        for row in disagg_rows
    )
    add(
        "disaggregated_gpu_sum",
        failed,
        "gpu_count = num_prefill_gpu + num_decode_gpu",
        len(disagg_rows),
    )

    failed = sum(row.get("gpu") not in GPU_REGISTRY for row in rows)
    add("known_gpu_registry", failed, "All hardware keys require official power and cost metadata")

    p99_rows = [row for row in rows if nonblank(row.get("p99_ttft_ms")) and nonblank(row.get("p99_tpot_ms"))]
    failed = sum(
        float(row["p99_ttft_ms"]) < float(row["median_ttft_ms"])
        or float(row["p99_tpot_ms"]) < float(row["median_tpot_ms"])
        for row in p99_rows
    )
    add("latency_percentile_order", failed, "p99 latency must be >= median latency", len(p99_rows))
    return checks


def write_csv_atomic(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows({header: row.get(header, "") for header in headers} for row in rows)
    os.chmod(temp_path, 0o644)
    os.replace(temp_path, path)


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
    os.chmod(temp_path, 0o644)
    os.replace(temp_path, path)


def existing_benchmark_stats() -> tuple[int, str, str]:
    path = NORM_DIR / "inferencex_benchmark_results.csv"
    if not path.exists():
        return 0, "", ""
    count = 0
    dates: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            count += 1
            if row.get("benchmark_date"):
                dates.append(row["benchmark_date"][:10])
    return count, min(dates, default=""), max(dates, default="")


def collect_history() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    availability = fetch_json(api_url("availability"))
    if not isinstance(availability, list) or not availability:
        raise RuntimeError("InferenceX availability endpoint returned no rows")

    by_id: dict[str, dict[str, Any]] = {}
    latest_proxy_rows: dict[str, list[dict[str, Any]]] = {}
    for model in DISPLAY_MODELS:
        model_count_before = len(by_id)
        for sequence, isl, osl in SEQUENCES:
            url = api_url("benchmarks/history", model=model, isl=isl, osl=osl)
            records = fetch_json(url)
            if not isinstance(records, list):
                raise RuntimeError(f"Unexpected history response for {model} {sequence}")
            for record in records:
                benchmark_id = str(record.get("id") or "")
                if benchmark_id:
                    by_id[benchmark_id] = normalize_live_row(record, url)
        agentic_url = api_url("benchmarks/history", model=model, benchmarkType="agentic_traces")
        records = fetch_json(agentic_url)
        if not isinstance(records, list):
            raise RuntimeError(f"Unexpected agentic history response for {model}")
        for record in records:
            benchmark_id = str(record.get("id") or "")
            if benchmark_id:
                by_id[benchmark_id] = normalize_live_row(record, agentic_url)
        latest_url = api_url("benchmarks", model=model)
        latest = fetch_json(latest_url)
        if not isinstance(latest, list):
            raise RuntimeError(f"Unexpected latest response for {model}")
        for record in latest:
            benchmark_id = str(record.get("id") or "")
            if benchmark_id:
                # Latest rows carry richer metric JSON than history. Replace by
                # stable benchmark id to enrich without inventing values.
                by_id[benchmark_id] = normalize_live_row(record, latest_url)
        print(f"- {model}: {len(by_id) - model_count_before:,} unique rows", flush=True)

        if model in PROXY_LATEST_FILES:
            latest_proxy_rows[model] = latest

    rows = sorted(
        by_id.values(),
        key=lambda row: (str(row.get("benchmark_date")), int(row.get("benchmark_id") or 0)),
    )
    return rows, availability, latest_proxy_rows


def validate_refresh(rows: list[dict[str, Any]], availability: list[dict[str, Any]]) -> dict[str, Any]:
    old_count, old_min, old_max = existing_benchmark_stats()
    dates = [str(row.get("benchmark_date") or "")[:10] for row in rows if row.get("benchmark_date")]
    availability_dates = [str(row.get("date") or "")[:10] for row in availability if row.get("date")]
    new_min = min(dates, default="")
    new_max = max(dates, default="")
    availability_max = max(availability_dates, default="")
    if old_count and len(rows) < int(old_count * 0.90):
        raise RuntimeError(f"Live API coverage regression: {len(rows):,} rows versus existing {old_count:,}")
    if old_min and new_min > old_min:
        raise RuntimeError(f"Live API history starts later than existing data: {new_min} > {old_min}")
    if availability_max and new_max < availability_max:
        raise RuntimeError(f"Benchmark history is stale versus availability: {new_max} < {availability_max}")
    unknown_hardware = sorted({str(row.get("gpu")) for row in rows if row.get("gpu") not in GPU_REGISTRY})
    if unknown_hardware:
        raise RuntimeError(f"Missing GPU metadata for: {', '.join(unknown_hardware)}")
    return {
        "old_rows": old_count,
        "old_date_min": old_min,
        "old_date_max": old_max,
        "new_rows": len(rows),
        "new_date_min": new_min,
        "new_date_max": new_max,
        "availability_rows": len(availability),
        "availability_date_max": availability_max,
    }


def rebuild_outputs(
    rows: list[dict[str, Any]],
    availability: list[dict[str, Any]],
    stats: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    run_date = datetime.now(timezone.utc).date().isoformat()
    main_configs = infer_model_main_configs(rows)
    apply_model_main_configs(rows, main_configs)
    validation_rows = validate_model_main_configs(rows, main_configs)
    if not validation_rows or any(row["status"] != "PASS" for row in validation_rows):
        raise RuntimeError("Main framework/precision validation failed")
    column_audit = build_column_audit(rows)
    quality_checks = run_quality_checks(rows)
    failed_columns = [row["column_name"] for row in column_audit if row["status"] == "FAIL"]
    failed_checks = [row["check_id"] for row in quality_checks if row["status"] == "FAIL"]
    if failed_columns or failed_checks:
        raise RuntimeError(
            "Data quality validation failed: "
            f"columns={failed_columns or 'none'}, checks={failed_checks or 'none'}"
        )
    summary_rows = summarize_benchmark_rows(rows, f"live-api/{run_date}")
    comparable_rows = summarize_benchmark_rows(
        [row for row in rows if row.get("is_main_model_config") == "yes"],
        f"live-api/{run_date}",
    )
    source_id = f"INFERENCEX_LIVE_API_{run_date.replace('-', '')}"
    for summary in summary_rows + comparable_rows:
        summary["source_id"] = source_id
        summary["caveat"] = (
            "Grouped live API benchmark summary; do not average across groups without weighting "
            "and SLO comparability checks."
        )

    availability_headers = sorted({key for row in availability for key in row}) or ["model"]
    write_csv_atomic(NORM_DIR / "inferencex_benchmark_results.csv", rows, DUMP_BENCHMARK_HEADERS)
    write_csv_atomic(NORM_DIR / "inferencex_metric_profile.csv", summary_rows, DUMP_SUMMARY_HEADERS)
    write_csv_atomic(NORM_DIR / "inferencex_gpu_comparable_metric_profile.csv", comparable_rows, DUMP_SUMMARY_HEADERS)
    write_csv_atomic(NORM_DIR / "inferencex_main_config_by_model.csv", main_configs, MODEL_MAIN_CONFIG_HEADERS)
    write_csv_atomic(
        NORM_DIR / "inferencex_main_config_validation.csv",
        validation_rows,
        MODEL_CONFIG_VALIDATION_HEADERS,
    )
    write_csv_atomic(NORM_DIR / "inferencex_availability.csv", availability, availability_headers)
    write_csv_atomic(NORM_DIR / "inferencex_benchmark_column_audit.csv", column_audit, COLUMN_AUDIT_HEADERS)
    write_csv_atomic(NORM_DIR / "inferencex_benchmark_quality_checks.csv", quality_checks, QUALITY_CHECK_HEADERS)

    manifest = {
        "refreshed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": API_ROOT,
        "history_scenarios": ["1k/1k", "8k/1k", "1k/8k", "agentic_traces"],
        "display_models": list(DISPLAY_MODELS),
        "gpu_power_source": (
            "InferenceX-app packages/constants/src/gpu-keys.ts fetched 2026-08-13; "
            "power is all-in kW/GPU."
        ),
        "column_audit_status": "PASS",
        "column_count": len(column_audit),
        "quality_check_status": "PASS",
        "quality_check_count": len(quality_checks),
        **stats,
    }
    write_json_atomic(META_DIR / "live_api_refresh_manifest.json", manifest)
    return column_audit, quality_checks


def rebuild_database(db_path: Path) -> list[tuple[str, int]]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=db_path.parent, suffix=".sqlite", delete=False) as handle:
        temp_db = Path(handle.name)
    try:
        loaded = build_database(NORM_DIR, temp_db)
        with sqlite3.connect(temp_db) as conn:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"SQLite integrity check failed: {integrity}")
            column_types = {
                row[1]: row[2]
                for row in conn.execute("PRAGMA table_info(benchmark_results)").fetchall()
            }
            expected_types = {
                "benchmark_id": "INTEGER",
                "gpu_count": "INTEGER",
                "concurrency": "INTEGER",
                "tok_s_user": "REAL",
                "tok_s_gpu": "REAL",
                "tok_s_mw": "REAL",
                "power_w": "REAL",
                "disagg": "INTEGER",
                "is_multinode": "INTEGER",
                "prefill_dp_attention": "INTEGER",
                "decode_dp_attention": "INTEGER",
                "median_ttft_ms": "REAL",
                "median_tpot_ms": "REAL",
                "median_itl_ms": "REAL",
                "median_e2el_s": "REAL",
            }
            type_errors = {
                column: (column_types.get(column), expected)
                for column, expected in expected_types.items()
                if column_types.get(column) != expected
            }
            if type_errors:
                raise RuntimeError(f"SQLite type contract failed: {type_errors}")
            for column in ("disagg", "is_multinode", "prefill_dp_attention", "decode_dp_attention"):
                invalid = conn.execute(
                    f'SELECT COUNT(*) FROM benchmark_results WHERE "{column}" NOT IN (0, 1) OR "{column}" IS NULL'
                ).fetchone()[0]
                if invalid:
                    raise RuntimeError(f"SQLite boolean domain failed for {column}: {invalid} rows")
            count, tok_s_user_count = conn.execute(
                "SELECT COUNT(*), COUNT(tok_s_user) FROM benchmark_results"
            ).fetchone()
            if count != tok_s_user_count:
                raise RuntimeError(
                    f"SQLite tok_s_user coverage failed: {tok_s_user_count:,}/{count:,}"
                )
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        os.chmod(temp_db, 0o644)
        os.replace(temp_db, db_path)
        return loaded
    finally:
        for artifact in (temp_db, Path(f"{temp_db}-wal"), Path(f"{temp_db}-shm")):
            if artifact.exists():
                artifact.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh normalized InferenceX history and SQLite DB")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("Fetching official InferenceX live history...", flush=True)
    rows, availability, latest_proxy_rows = collect_history()
    stats = validate_refresh(rows, availability)
    column_audit, quality_checks = rebuild_outputs(rows, availability, stats)

    write_json_atomic(LIVE_DIR / "availability.json", availability)
    for model, records in latest_proxy_rows.items():
        write_json_atomic(LIVE_DIR / PROXY_LATEST_FILES[model], records)

    loaded = rebuild_database(args.db)
    print(
        f"Refreshed {args.db}: {stats['old_rows']:,} -> {stats['new_rows']:,} benchmark rows, "
        f"latest {stats['old_date_max'] or '-'} -> {stats['new_date_max']}",
        flush=True,
    )
    print(f"Loaded {len(loaded)} normalized tables", flush=True)
    print(
        f"Data audit PASS: {len(column_audit)} columns / {len(quality_checks)} quality checks",
        flush=True,
    )


if __name__ == "__main__":
    main()
