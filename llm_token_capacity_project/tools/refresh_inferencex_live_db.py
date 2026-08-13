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
    fetch_json,
    infer_model_main_configs,
    money_per_mtok,
    normalize_hardware_key,
    summarize_benchmark_rows,
    validate_model_main_configs,
)

API_ROOT = "https://inferencex.semianalysis.com/api/v1"
LIVE_DIR = ROOT / "data" / "inferencex" / "live_api"
DEFAULT_DB = ROOT / "data" / "inferencex" / "inferencex_benchmark.sqlite"

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
        "source_file": source_url,
        "source_kind": "inferencex_live_api_history",
        "benchmark_id": record.get("id"),
        "dashboard_tab": "inference_performance",
        "model": record.get("model"),
        "model_family": record.get("model"),
        "gpu": hardware,
        "gpu_vendor": gpu.get("gpu_vendor", ""),
        "gpu_count": record.get("num_decode_gpu") or record.get("num_prefill_gpu"),
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
        "tok_s_user": "",
        "tok_s_gpu": total_tput,
        "tok_s_mw": total_tput_mw,
        "input_tok_s_gpu": input_tput,
        "output_tok_s_gpu": output_tput,
        "joules_token": power_w / output_tput if power_w and output_tput else "",
        "p99_ttft_ms": metrics.get("p99_ttft"),
        "p99_tpot_ms": metrics.get("p99_tpot"),
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
        "config_id": "",
        "workflow_run_id": workflow_run_id(run_url),
        "error": "",
        "mean_ttft_ms": metrics.get("mean_ttft"),
        "mean_tpot_ms": metrics.get("mean_tpot"),
        "median_ttft_ms": metrics.get("median_ttft"),
        "median_tpot_ms": metrics.get("median_tpot"),
        "mean_e2el_s": metrics.get("mean_e2el"),
        "p99_e2el_s": metrics.get("p99_e2el"),
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
        print(f"- {model}: {len(by_id) - model_count_before:,} unique history rows", flush=True)

        if model in PROXY_LATEST_FILES:
            latest = fetch_json(api_url("benchmarks", model=model))
            if not isinstance(latest, list):
                raise RuntimeError(f"Unexpected latest response for {model}")
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


def rebuild_outputs(rows: list[dict[str, Any]], availability: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    run_date = datetime.now(timezone.utc).date().isoformat()
    main_configs = infer_model_main_configs(rows)
    apply_model_main_configs(rows, main_configs)
    validation_rows = validate_model_main_configs(rows, main_configs)
    if not validation_rows or any(row["status"] != "PASS" for row in validation_rows):
        raise RuntimeError("Main framework/precision validation failed")
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

    manifest = {
        "refreshed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": API_ROOT,
        "history_scenarios": ["1k/1k", "8k/1k", "1k/8k", "agentic_traces"],
        "display_models": list(DISPLAY_MODELS),
        "gpu_power_source": (
            "InferenceX-app packages/constants/src/gpu-keys.ts fetched 2026-08-13; "
            "power is all-in kW/GPU."
        ),
        **stats,
    }
    write_json_atomic(META_DIR / "live_api_refresh_manifest.json", manifest)


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
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
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
    rebuild_outputs(rows, availability, stats)

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


if __name__ == "__main__":
    main()
