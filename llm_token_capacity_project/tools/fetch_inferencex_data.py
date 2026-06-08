"""Fetch and index public InferenceX data sources.

The goal is not to scrape dashboard HTML. InferenceX publishes an open benchmark
repo and the dashboard app publishes weekly database dumps as GitHub releases.
This tool records those auditable source surfaces and creates a normalized
schema target that A08/A09 can use once a dump or CSV export is downloaded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import tarfile
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "inferencex"
RAW_DIR = DATA_DIR / "raw"
NORM_DIR = DATA_DIR / "normalized"
META_DIR = DATA_DIR / "metadata"
DOC_PATH = ROOT / "docs" / "inferencex_ingestion_plan.md"

USER_AGENT = "llm-token-capacity-project/0.1"
RUN_DATE = datetime.now(timezone.utc).date().isoformat()

BENCHMARK_REPO = "SemiAnalysisAI/InferenceX"
APP_REPO = "SemiAnalysisAI/InferenceX-app"
GITHUB_API = "https://api.github.com"

RAW_FILES = [
    {
        "source_id": "INFERENCEX_BENCHMARK_README",
        "repo": BENCHMARK_REPO,
        "branch": "main",
        "path": "README.md",
        "dashboard_tab": "methodology",
        "source_kind": "benchmark_repo_readme",
    },
    {
        "source_id": "INFERENCEX_BENCHMARK_AGENTS",
        "repo": BENCHMARK_REPO,
        "branch": "main",
        "path": "AGENTS.md",
        "dashboard_tab": "methodology",
        "source_kind": "benchmark_repo_operating_rules",
    },
    {
        "source_id": "INFERENCEX_PERF_CHANGELOG",
        "repo": BENCHMARK_REPO,
        "branch": "main",
        "path": "perf-changelog.yaml",
        "dashboard_tab": "historical_trends",
        "source_kind": "benchmark_changelog",
    },
    {
        "source_id": "INFERENCEX_APP_README",
        "repo": APP_REPO,
        "branch": "master",
        "path": "README.md",
        "dashboard_tab": "data_pipeline",
        "source_kind": "dashboard_app_readme",
    },
    {
        "source_id": "INFERENCEX_APP_ENV_EXAMPLE",
        "repo": APP_REPO,
        "branch": "master",
        "path": ".env.example",
        "dashboard_tab": "data_pipeline",
        "source_kind": "dashboard_app_config",
    },
    {
        "source_id": "INFERENCEX_APP_PACKAGE",
        "repo": APP_REPO,
        "branch": "master",
        "path": "package.json",
        "dashboard_tab": "data_pipeline",
        "source_kind": "dashboard_app_scripts",
    },
    {
        "source_id": "INFERENCEX_APP_DATA_PIPELINE_DOC",
        "repo": APP_REPO,
        "branch": "master",
        "path": "docs/data-pipeline.md",
        "dashboard_tab": "data_pipeline",
        "source_kind": "dashboard_app_doc",
    },
    {
        "source_id": "INFERENCEX_APP_TRANSFORMS_DOC",
        "repo": APP_REPO,
        "branch": "master",
        "path": "docs/data-transforms.md",
        "dashboard_tab": "data_pipeline",
        "source_kind": "dashboard_app_doc",
    },
    {
        "source_id": "INFERENCEX_APP_GPU_SPECS_DOC",
        "repo": APP_REPO,
        "branch": "master",
        "path": "docs/gpu-specs.md",
        "dashboard_tab": "gpu_specs",
        "source_kind": "dashboard_app_doc",
    },
    {
        "source_id": "INFERENCEX_APP_TCO_DOC",
        "repo": APP_REPO,
        "branch": "master",
        "path": "docs/tco-calculator.md",
        "dashboard_tab": "tco_calculator",
        "source_kind": "dashboard_app_doc",
    },
]

NORMALIZED_HEADERS = [
    "source_file",
    "source_kind",
    "benchmark_id",
    "dashboard_tab",
    "model",
    "model_family",
    "gpu",
    "gpu_vendor",
    "gpu_count",
    "framework",
    "runtime",
    "precision",
    "main_framework",
    "main_precision",
    "is_main_model_config",
    "main_config_reason",
    "isl",
    "osl",
    "concurrency",
    "batch_size",
    "metric_name",
    "metric_value",
    "metric_unit",
    "tok_s_user",
    "tok_s_gpu",
    "tok_s_mw",
    "input_tok_s_gpu",
    "output_tok_s_gpu",
    "joules_token",
    "p99_ttft_ms",
    "p99_tpot_ms",
    "cost_per_million_tokens_usd",
    "power_w",
    "benchmark_date",
    "github_run_url",
    "source_url",
    "evidence_class",
    "caveat",
]

DUMP_BENCHMARK_HEADERS = NORMALIZED_HEADERS + [
    "benchmark_type",
    "config_id",
    "workflow_run_id",
    "error",
    "mean_ttft_ms",
    "mean_tpot_ms",
    "median_ttft_ms",
    "median_tpot_ms",
    "mean_e2el_s",
    "p99_e2el_s",
    "total_tok_s_mw",
    "output_tok_s_mw",
    "input_tok_s_mw",
    "j_total_token",
    "j_output_token",
    "j_input_token",
    "cost_hyperscaler_per_mtok_usd",
    "cost_neocloud_per_mtok_usd",
    "cost_retail_per_mtok_usd",
]

DUMP_SUMMARY_HEADERS = [
    "group_key",
    "model",
    "gpu",
    "gpu_vendor",
    "framework",
    "precision",
    "main_framework",
    "main_precision",
    "is_main_model_config",
    "isl",
    "osl",
    "row_count",
    "date_min",
    "date_max",
    "tok_s_gpu_p10",
    "tok_s_gpu_p50",
    "tok_s_gpu_p90",
    "tok_s_mw_p10",
    "tok_s_mw_p50",
    "tok_s_mw_p90",
    "output_tok_s_mw_p10",
    "output_tok_s_mw_p50",
    "output_tok_s_mw_p90",
    "p99_ttft_ms_p50",
    "p99_tpot_ms_p50",
    "j_output_token_p50",
    "source_id",
    "caveat",
]

MODEL_MAIN_CONFIG_HEADERS = [
    "model",
    "main_framework",
    "main_precision",
    "distinct_gpu_count",
    "row_count",
    "date_min",
    "date_max",
    "selection_rule",
]

MODEL_CONFIG_VALIDATION_HEADERS = [
    "model",
    "status",
    "main_framework",
    "main_precision",
    "main_rows",
    "non_main_rows",
    "distinct_framework_precision_pairs",
    "reason",
]

DUMP_EVAL_HEADERS = [
    "source_file",
    "eval_id",
    "workflow_run_id",
    "config_id",
    "task",
    "model",
    "gpu",
    "gpu_vendor",
    "framework",
    "precision",
    "isl",
    "osl",
    "concurrency",
    "score",
    "score_se",
    "n_eff",
    "benchmark_date",
    "source_url",
    "evidence_class",
    "caveat",
]

DUMP_INVENTORY_HEADERS = [
    "source_file",
    "file_size_bytes",
    "compressed_size_bytes",
    "record_count",
    "parse_status",
    "notes",
]

GPU_REGISTRY = {
    # Source: InferenceX-app packages/constants/src/gpu-keys.ts, fetched 2026-05-19.
    # power is kW per GPU and is intentionally higher than chip TDP because the
    # dashboard models datacenter system-level power for energy/cost charts.
    "h100": {"gpu_vendor": "NVIDIA", "label": "H100", "tdp_w": 700, "power_kw": 1.73, "costh": 1.30, "costn": 1.69, "costr": 1.30},
    "h200": {"gpu_vendor": "NVIDIA", "label": "H200", "tdp_w": 700, "power_kw": 1.73, "costh": 1.41, "costn": 1.74, "costr": 1.60},
    "b200": {"gpu_vendor": "NVIDIA", "label": "B200", "tdp_w": 1000, "power_kw": 2.17, "costh": 1.95, "costn": 2.34, "costr": 2.90},
    "b300": {"gpu_vendor": "NVIDIA", "label": "B300", "tdp_w": 1200, "power_kw": 2.17, "costh": 2.34, "costn": 2.808, "costr": 3.48},
    "gb200": {"gpu_vendor": "NVIDIA", "label": "GB200 NVL72", "tdp_w": 1200, "power_kw": 2.10, "costh": 2.21, "costn": 2.75, "costr": 3.30},
    "gb300": {"gpu_vendor": "NVIDIA", "label": "GB300 NVL72", "tdp_w": 1400, "power_kw": 2.10, "costh": 2.652, "costn": 3.30, "costr": 3.96},
    "mi300x": {"gpu_vendor": "AMD", "label": "MI300X", "tdp_w": 750, "power_kw": 1.79, "costh": 1.12, "costn": 1.40, "costr": 1.55},
    "mi325x": {"gpu_vendor": "AMD", "label": "MI325X", "tdp_w": 1000, "power_kw": 2.18, "costh": 1.28, "costn": 1.59, "costr": 1.80},
    "mi355x": {"gpu_vendor": "AMD", "label": "MI355X", "tdp_w": 1400, "power_kw": 2.65, "costh": 1.48, "costn": 1.90, "costr": 2.10},
}

FIELD_ALIASES = {
    "model": ["model", "model_name", "model_key", "scenario_model", "hf_model_id"],
    "model_family": ["model_family", "family", "model_group"],
    "gpu": ["gpu", "gpu_name", "hardware", "accelerator", "gpu_type"],
    "gpu_vendor": ["gpu_vendor", "vendor", "hardware_vendor"],
    "gpu_count": ["gpu_count", "num_gpus", "n_gpus", "tp_size", "tensor_parallel_size"],
    "framework": ["framework", "engine", "inference_engine"],
    "runtime": ["runtime", "container", "image", "software_version"],
    "precision": ["precision", "dtype", "quantization", "weight_dtype"],
    "isl": ["isl", "input_len", "input_length", "input_tokens", "input_sequence_length"],
    "osl": ["osl", "output_len", "output_length", "output_tokens", "output_sequence_length"],
    "concurrency": ["concurrency", "max_concurrency", "num_concurrent_requests"],
    "batch_size": ["batch_size", "batch"],
    "metric_name": ["metric_name", "metric", "name"],
    "metric_value": ["metric_value", "value", "score"],
    "metric_unit": ["metric_unit", "unit"],
    "tok_s_user": ["tok_s_user", "tokens_per_second_user", "user_tokens_per_second"],
    "tok_s_gpu": ["tok_s_gpu", "tokens_per_second_per_gpu", "output_tokens_per_second_per_gpu"],
    "tok_s_mw": ["tok_s_mw", "tokens_per_second_per_mw", "tokens_per_mw"],
    "input_tok_s_gpu": ["input_tok_s_gpu", "input_tokens_per_second_per_gpu"],
    "output_tok_s_gpu": ["output_tok_s_gpu", "output_tokens_per_second_per_gpu"],
    "joules_token": ["joules_token", "joules_per_token", "j_per_token"],
    "p99_ttft_ms": ["p99_ttft_ms", "ttft_p99_ms", "p99_time_to_first_token_ms"],
    "p99_tpot_ms": ["p99_tpot_ms", "tpot_p99_ms", "p99_time_per_output_token_ms"],
    "cost_per_million_tokens_usd": ["cost_per_million_tokens_usd", "usd_per_million_tokens", "cost_per_mt"],
    "power_w": ["power_w", "tdp_w", "gpu_power_w", "system_power_w"],
    "benchmark_date": ["benchmark_date", "date", "created_at", "run_date"],
    "github_run_url": ["github_run_url", "run_url", "workflow_url", "artifact_url"],
    "source_url": ["source_url", "url"],
}

TAB_RULES = [
    {
        "dashboard_tab": "inference_performance",
        "use_in_model": "A08 tokens/sec/MW, A09 latency/utilization sensitivity",
        "required_keys": "model, gpu, framework/runtime, precision, ISL, OSL, concurrency, throughput, latency",
        "forecast_use": "benchmark/proxy only",
    },
    {
        "dashboard_tab": "accuracy_evals",
        "use_in_model": "model quality guardrail when comparing precision/quantization choices",
        "required_keys": "model, precision, benchmark, score, date",
        "forecast_use": "quality sanity check; not token capacity",
    },
    {
        "dashboard_tab": "historical_trends",
        "use_in_model": "software improvement CAGR, SGLang/vLLM/TRT-LLM version step changes",
        "required_keys": "config key, software version, benchmark date, PR/run URL",
        "forecast_use": "scenario support for Bull/Base/Bear tokens/MW improvement",
    },
    {
        "dashboard_tab": "tco_calculator",
        "use_in_model": "cost/token and memory marketing implications",
        "required_keys": "GPU, system cost, power, throughput, utilization, amortization",
        "forecast_use": "commercial sensitivity layer, not production volume",
    },
    {
        "dashboard_tab": "gpu_specs",
        "use_in_model": "GPU generation, memory capacity/bandwidth, TDP cross-check",
        "required_keys": "GPU, vendor, memory, bandwidth, power/TDP",
        "forecast_use": "hardware sanity check for GPU/ASIC mix",
    },
]


def request(url: str) -> urllib.request.Request:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def fetch_bytes(url: str) -> tuple[bytes, dict[str, str]]:
    with urllib.request.urlopen(request(url), timeout=60) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.read(), headers


def fetch_json(url: str) -> Any:
    body, _headers = fetch_bytes(url)
    return json.loads(body.decode("utf-8"))


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def read_json_from_zip(zip_path: Path, member: str) -> Any:
    with zipfile.ZipFile(zip_path) as zf:
        return json.loads(zf.read(member).decode("utf-8"))


def archive_names(path: Path) -> list[str]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return [name for name in zf.namelist() if not name.endswith("/")]
    with tarfile.open(path, "r:*") as tf:
        return [member.name for member in tf.getmembers() if member.isfile()]


def read_json_from_archive(path: Path, member: str) -> Any:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return json.loads(zf.read(member).decode("utf-8"))
    with tarfile.open(path, "r:*") as tf:
        extracted = tf.extractfile(member)
        if extracted is None:
            raise FileNotFoundError(member)
        return json.loads(extracted.read().decode("utf-8"))


def read_json_members_from_archive(path: Path, members: list[str]) -> dict[str, Any]:
    wanted = set(members)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            return {member: json.loads(zf.read(member).decode("utf-8")) for member in members}

    out: dict[str, Any] = {}
    with tarfile.open(path, "r:*") as tf:
        for member in tf:
            if not member.isfile() or member.name not in wanted:
                continue
            extracted = tf.extractfile(member)
            if extracted is None:
                continue
            out[member.name] = json.loads(extracted.read().decode("utf-8"))
            if len(out) == len(wanted):
                break
    missing = wanted - set(out)
    if missing:
        raise FileNotFoundError(f"missing archive members: {sorted(missing)}")
    return out


def dump_prefix(path: Path) -> str:
    for name in archive_names(path):
        if name.endswith("/benchmark_results.json"):
            return name.rsplit("/", 1)[0]
    raise FileNotFoundError("benchmark_results.json not found in InferenceX dump archive")


def as_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def percentile(values: list[float], pct: float) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * pct
    lo = int(pos)
    hi = min(lo + 1, len(vals) - 1)
    frac = pos - lo
    return vals[lo] * (1 - frac) + vals[hi] * frac


def money_per_mtok(cost_per_gpu_hour: float | None, output_tok_s_gpu: float | None) -> float | None:
    if not cost_per_gpu_hour or not output_tok_s_gpu:
        return None
    return cost_per_gpu_hour / (output_tok_s_gpu * 3600) * 1_000_000


def date_key(value: Any) -> str:
    return str(value or "")[:10]


def build_config_maps(configs: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["id"]): row for row in configs if row.get("id") is not None}


def normalize_hardware_key(hardware: Any) -> str:
    return str(hardware or "").lower().split("_")[0].split("-")[0]


def source_url_for_dump(tag_name: str | None) -> str:
    tag = tag_name or "db-dump/2026-05-11"
    return f"https://github.com/{APP_REPO}/releases/tag/{tag}"


def source_id_for_release(tag_name: str | None) -> str:
    suffix = safe_name(str(tag_name or "db-dump_unknown")).upper()
    return f"INFERENCEX_{suffix}"


def normalize_inferencex_benchmark_row(
    record: dict[str, Any],
    config: dict[str, Any],
    zip_path: Path,
    release_tag: str | None,
) -> dict[str, Any]:
    metrics = record.get("metrics") or {}
    hardware = normalize_hardware_key(config.get("hardware"))
    gpu = GPU_REGISTRY.get(hardware, {})
    power_kw = as_float(gpu.get("power_kw"))
    power_w = power_kw * 1000 if power_kw else None
    total_tput = as_float(metrics.get("tput_per_gpu"))
    input_tput = as_float(metrics.get("input_tput_per_gpu"))
    output_tput = as_float(metrics.get("output_tput_per_gpu"))
    tok_s_mw = total_tput * 1000 / power_kw if total_tput and power_kw else None
    input_tok_s_mw = input_tput * 1000 / power_kw if input_tput and power_kw else None
    output_tok_s_mw = output_tput * 1000 / power_kw if output_tput and power_kw else None
    source_file = f"{zip_path.name}:benchmark_results.json"
    return {
        "source_file": source_file,
        "source_kind": "inferencex_db_dump",
        "benchmark_id": record.get("id"),
        "dashboard_tab": "inference_performance",
        "model": config.get("model"),
        "model_family": config.get("model"),
        "gpu": hardware,
        "gpu_vendor": gpu.get("gpu_vendor", ""),
        "gpu_count": config.get("num_decode_gpu") or config.get("num_prefill_gpu"),
        "framework": config.get("framework"),
        "runtime": record.get("image") or "",
        "precision": config.get("precision"),
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
        "tok_s_mw": tok_s_mw,
        "input_tok_s_gpu": input_tput,
        "output_tok_s_gpu": output_tput,
        "joules_token": power_w / output_tput if power_w and output_tput else "",
        "p99_ttft_ms": metrics.get("p99_ttft"),
        "p99_tpot_ms": metrics.get("p99_tpot"),
        "cost_per_million_tokens_usd": money_per_mtok(as_float(gpu.get("costh")), output_tput),
        "power_w": power_w,
        "benchmark_date": record.get("date"),
        "github_run_url": "",
        "source_url": source_url_for_dump(release_tag),
        "evidence_class": "Proxy/Benchmark",
        "caveat": "InferenceX dump row. Benchmark/proxy only; not company production telemetry. Match ISL/OSL/framework/precision before using.",
        "benchmark_type": record.get("benchmark_type"),
        "config_id": record.get("config_id"),
        "workflow_run_id": record.get("workflow_run_id"),
        "error": record.get("error"),
        "mean_ttft_ms": metrics.get("mean_ttft"),
        "mean_tpot_ms": metrics.get("mean_tpot"),
        "median_ttft_ms": metrics.get("median_ttft"),
        "median_tpot_ms": metrics.get("median_tpot"),
        "mean_e2el_s": metrics.get("mean_e2el"),
        "p99_e2el_s": metrics.get("p99_e2el"),
        "total_tok_s_mw": tok_s_mw,
        "output_tok_s_mw": output_tok_s_mw,
        "input_tok_s_mw": input_tok_s_mw,
        "j_total_token": power_w / total_tput if power_w and total_tput else "",
        "j_output_token": power_w / output_tput if power_w and output_tput else "",
        "j_input_token": power_w / input_tput if power_w and input_tput else "",
        "cost_hyperscaler_per_mtok_usd": money_per_mtok(as_float(gpu.get("costh")), output_tput),
        "cost_neocloud_per_mtok_usd": money_per_mtok(as_float(gpu.get("costn")), output_tput),
        "cost_retail_per_mtok_usd": money_per_mtok(as_float(gpu.get("costr")), output_tput),
    }


def infer_model_main_configs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        model = str(row.get("model") or "")
        framework = str(row.get("framework") or "")
        precision = str(row.get("precision") or "")
        if not model or not framework or not precision:
            continue
        groups[(model, framework, precision)].append(row)

    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (model, framework, precision), items in groups.items():
        dates = [date_key(row.get("benchmark_date")) for row in items if row.get("benchmark_date")]
        by_model[model].append(
            {
                "model": model,
                "main_framework": framework,
                "main_precision": precision,
                "distinct_gpu_count": len({row.get("gpu") for row in items if row.get("gpu")}),
                "row_count": len(items),
                "date_min": min(dates) if dates else "",
                "date_max": max(dates) if dates else "",
                "selection_rule": "max distinct GPUs, then max row count, then latest benchmark date",
            }
        )

    selected = []
    for model, candidates in by_model.items():
        candidates.sort(
            key=lambda row: (
                int(row["distinct_gpu_count"]),
                int(row["row_count"]),
                str(row["date_max"]),
                str(row["main_framework"]),
                str(row["main_precision"]),
            ),
            reverse=True,
        )
        selected.append(candidates[0])
    return sorted(selected, key=lambda row: row["model"])


def apply_model_main_configs(
    rows: list[dict[str, Any]],
    main_configs: list[dict[str, Any]],
) -> None:
    by_model = {row["model"]: row for row in main_configs}
    for row in rows:
        config = by_model.get(row.get("model"))
        if not config:
            row["main_framework"] = ""
            row["main_precision"] = ""
            row["is_main_model_config"] = "unknown"
            row["main_config_reason"] = "no model-level main config could be inferred"
            continue
        row["main_framework"] = config["main_framework"]
        row["main_precision"] = config["main_precision"]
        is_main = row.get("framework") == config["main_framework"] and row.get("precision") == config["main_precision"]
        row["is_main_model_config"] = "yes" if is_main else "no"
        row["main_config_reason"] = (
            "model-level canonical framework/precision for GPU comparison; "
            f"selected by {config['selection_rule']}"
        )


def validate_model_main_configs(
    rows: list[dict[str, Any]],
    main_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_model_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_model_rows[str(row.get("model") or "")].append(row)
    config_by_model = {row["model"]: row for row in main_configs}
    out = []
    for model, items in sorted(by_model_rows.items()):
        if not model:
            continue
        config = config_by_model.get(model, {})
        pairs = {(row.get("framework"), row.get("precision")) for row in items}
        main_rows = [row for row in items if row.get("is_main_model_config") == "yes"]
        non_main_rows = [row for row in items if row.get("is_main_model_config") == "no"]
        status = "PASS" if config and main_rows else "FAIL"
        reason = "one model-level main framework/precision selected and rows flagged"
        if not config:
            reason = "missing model-level main framework/precision"
        elif not main_rows:
            reason = "main framework/precision selected but no rows matched it"
        out.append(
            {
                "model": model,
                "status": status,
                "main_framework": config.get("main_framework", ""),
                "main_precision": config.get("main_precision", ""),
                "main_rows": len(main_rows),
                "non_main_rows": len(non_main_rows),
                "distinct_framework_precision_pairs": len(pairs),
                "reason": reason,
            }
        )
    return out


def summarize_benchmark_rows(rows: list[dict[str, Any]], release_tag: str | None) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row.get("model"),
            row.get("gpu"),
            row.get("gpu_vendor"),
            row.get("framework"),
            row.get("precision"),
            row.get("main_framework"),
            row.get("main_precision"),
            row.get("is_main_model_config"),
            row.get("isl"),
            row.get("osl"),
        )
        groups[key].append(row)
    out: list[dict[str, Any]] = []
    for key, items in sorted(groups.items(), key=lambda kv: (str(kv[0]), -len(kv[1]))):
        model, gpu, vendor, framework, precision, main_framework, main_precision, is_main_model_config, isl, osl = key
        dates = [str(i.get("benchmark_date") or "")[:10] for i in items if i.get("benchmark_date")]
        def vals(field: str) -> list[float]:
            return [v for v in (as_float(i.get(field)) for i in items) if v is not None]
        row = {
            "group_key": "|".join(str(x) for x in key),
            "model": model,
            "gpu": gpu,
            "gpu_vendor": vendor,
            "framework": framework,
            "precision": precision,
            "main_framework": main_framework,
            "main_precision": main_precision,
            "is_main_model_config": is_main_model_config,
            "isl": isl,
            "osl": osl,
            "row_count": len(items),
            "date_min": min(dates) if dates else "",
            "date_max": max(dates) if dates else "",
            "tok_s_gpu_p10": percentile(vals("tok_s_gpu"), 0.10),
            "tok_s_gpu_p50": percentile(vals("tok_s_gpu"), 0.50),
            "tok_s_gpu_p90": percentile(vals("tok_s_gpu"), 0.90),
            "tok_s_mw_p10": percentile(vals("tok_s_mw"), 0.10),
            "tok_s_mw_p50": percentile(vals("tok_s_mw"), 0.50),
            "tok_s_mw_p90": percentile(vals("tok_s_mw"), 0.90),
            "output_tok_s_mw_p10": percentile(vals("output_tok_s_mw"), 0.10),
            "output_tok_s_mw_p50": percentile(vals("output_tok_s_mw"), 0.50),
            "output_tok_s_mw_p90": percentile(vals("output_tok_s_mw"), 0.90),
            "p99_ttft_ms_p50": percentile(vals("p99_ttft_ms"), 0.50),
            "p99_tpot_ms_p50": percentile(vals("p99_tpot_ms"), 0.50),
            "j_output_token_p50": percentile(vals("j_output_token"), 0.50),
            "source_id": source_id_for_release(release_tag),
            "caveat": "Grouped benchmark summary; do not average across groups without weighting and SLO comparability checks.",
        }
        out.append(row)
    return out


def normalize_inferencex_eval_row(
    record: dict[str, Any],
    config: dict[str, Any],
    zip_path: Path,
    release_tag: str | None,
) -> dict[str, Any]:
    metrics = record.get("metrics") or {}
    hardware = normalize_hardware_key(config.get("hardware"))
    gpu = GPU_REGISTRY.get(hardware, {})
    return {
        "source_file": f"{zip_path.name}:eval_results.json",
        "eval_id": record.get("id"),
        "workflow_run_id": record.get("workflow_run_id"),
        "config_id": record.get("config_id"),
        "task": record.get("task"),
        "model": config.get("model"),
        "gpu": hardware,
        "gpu_vendor": gpu.get("gpu_vendor", ""),
        "framework": config.get("framework"),
        "precision": config.get("precision"),
        "isl": record.get("isl"),
        "osl": record.get("osl"),
        "concurrency": record.get("conc"),
        "score": metrics.get("score"),
        "score_se": metrics.get("score_se"),
        "n_eff": metrics.get("n_eff"),
        "benchmark_date": record.get("date"),
        "source_url": source_url_for_dump(release_tag),
        "evidence_class": "Proxy/Benchmark",
        "caveat": "Accuracy eval proxy. Use as quality guardrail when precision/framework changes throughput.",
    }


def process_inferencex_dump_zip(zip_path: Path, release_tag: str | None, max_rows: int) -> dict[str, Any]:
    if not zip_path.exists():
        return {"status": "skipped", "reason": f"dump archive not found: {zip_path}", "benchmark_rows": []}
    prefix = dump_prefix(zip_path)
    inventory: list[dict[str, Any]] = []
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path) as zf:
            members = [
                {
                    "name": info.filename,
                    "file_size": info.file_size,
                    "compressed_size": info.compress_size,
                }
                for info in zf.infolist()
                if not info.is_dir()
            ]
    else:
        with tarfile.open(zip_path, "r:*") as tf:
            members = [
                {
                    "name": member.name,
                    "file_size": member.size,
                    "compressed_size": "",
                }
                for member in tf.getmembers()
                if member.isfile()
            ]
    for info in members:
        record_count = ""
        status = "indexed"
        notes = ""
        if info["name"].endswith((".json", ".jsonl")) and int(info["file_size"]) <= 100_000_000:
            try:
                obj = read_json_from_archive(zip_path, info["name"])
                record_count = len(obj) if isinstance(obj, list) else 1
                status = "parsed"
            except Exception as exc:  # noqa: BLE001 - inventory should not fail the run.
                status = "parse_error"
                notes = str(exc)[:200]
        elif int(info["file_size"]) > 100_000_000:
            notes = "Large table kept in raw archive; parse only with dedicated streaming job."
        inventory.append(
            {
                "source_file": info["name"],
                "file_size_bytes": info["file_size"],
                "compressed_size_bytes": info["compressed_size"],
                "record_count": record_count,
                "parse_status": status,
                "notes": notes,
            }
        )

    table_members = [
        f"{prefix}/configs.json",
        f"{prefix}/benchmark_results.json",
        f"{prefix}/eval_results.json",
        f"{prefix}/run_stats.json",
        f"{prefix}/availability.json",
    ]
    tables = read_json_members_from_archive(zip_path, table_members)
    configs = tables[f"{prefix}/configs.json"]
    config_by_id = build_config_maps(configs)
    benchmark_records = tables[f"{prefix}/benchmark_results.json"]
    benchmark_rows = [
        normalize_inferencex_benchmark_row(record, config_by_id.get(int(record.get("config_id", -1)), {}), zip_path, release_tag)
        for record in benchmark_records[:max_rows]
    ]
    main_configs = infer_model_main_configs(benchmark_rows)
    apply_model_main_configs(benchmark_rows, main_configs)
    validation_rows = validate_model_main_configs(benchmark_rows, main_configs)
    summary_rows = summarize_benchmark_rows(benchmark_rows, release_tag)
    comparable_summary_rows = summarize_benchmark_rows(
        [row for row in benchmark_rows if row.get("is_main_model_config") == "yes"],
        release_tag,
    )
    eval_records = tables[f"{prefix}/eval_results.json"]
    eval_rows = [
        normalize_inferencex_eval_row(record, config_by_id.get(int(record.get("config_id", -1)), {}), zip_path, release_tag)
        for record in eval_records[:max_rows]
    ]
    run_stats = tables[f"{prefix}/run_stats.json"]
    availability = tables[f"{prefix}/availability.json"]

    write_csv(NORM_DIR / "inferencex_dump_inventory.csv", inventory, DUMP_INVENTORY_HEADERS)
    write_csv(NORM_DIR / "inferencex_benchmark_results.csv", benchmark_rows, DUMP_BENCHMARK_HEADERS)
    write_csv(NORM_DIR / "inferencex_metric_profile.csv", summary_rows, DUMP_SUMMARY_HEADERS)
    write_csv(NORM_DIR / "inferencex_gpu_comparable_metric_profile.csv", comparable_summary_rows, DUMP_SUMMARY_HEADERS)
    write_csv(NORM_DIR / "inferencex_main_config_by_model.csv", main_configs, MODEL_MAIN_CONFIG_HEADERS)
    write_csv(NORM_DIR / "inferencex_main_config_validation.csv", validation_rows, MODEL_CONFIG_VALIDATION_HEADERS)
    write_csv(NORM_DIR / "inferencex_accuracy_evals.csv", eval_rows, DUMP_EVAL_HEADERS)
    write_csv(NORM_DIR / "inferencex_run_stats.csv", run_stats, list(run_stats[0].keys()) if run_stats else ["id"])
    write_csv(NORM_DIR / "inferencex_availability.csv", availability, list(availability[0].keys()) if availability else ["model"])

    return {
        "status": "parsed",
        "zip_path": str(zip_path.relative_to(ROOT)) if zip_path.is_relative_to(ROOT) else str(zip_path),
        "prefix": prefix,
        "sha256": sha256(zip_path),
        "inventory_rows": len(inventory),
        "benchmark_rows": len(benchmark_rows),
        "benchmark_records_total": len(benchmark_records),
        "metric_profile_rows": len(summary_rows),
        "gpu_comparable_metric_profile_rows": len(comparable_summary_rows),
        "main_config_rows": len(main_configs),
        "main_config_validation_status": "PASS" if all(row["status"] == "PASS" for row in validation_rows) else "FAIL",
        "accuracy_eval_rows": len(eval_rows),
        "run_stats_rows": len(run_stats),
        "availability_rows": len(availability),
        "gpu_power_source": "InferenceX-app packages/constants/src/gpu-keys.ts; power field is kW/GPU used by dashboard energy and TCO transforms.",
    }


def collect_releases(repo: str) -> list[dict[str, Any]]:
    releases = fetch_json(f"{GITHUB_API}/repos/{repo}/releases?per_page=30")
    rows = []
    for release in releases:
        for asset in release.get("assets", []):
            rows.append(
                {
                    "repo": repo,
                    "tag_name": release.get("tag_name"),
                    "name": release.get("name"),
                    "published_at": release.get("published_at"),
                    "asset_name": asset.get("name"),
                    "asset_size_bytes": asset.get("size"),
                    "asset_digest": asset.get("digest"),
                    "download_count": asset.get("download_count"),
                    "browser_download_url": asset.get("browser_download_url"),
                    "html_url": release.get("html_url"),
                    "body": release.get("body"),
                }
            )
    return rows


def download_raw_files() -> list[dict[str, Any]]:
    rows = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for item in RAW_FILES:
        url = f"https://raw.githubusercontent.com/{item['repo']}/{item['branch']}/{item['path']}"
        target = RAW_DIR / f"{safe_name(item['source_id'])}_{safe_name(Path(item['path']).name)}"
        try:
            body, headers = fetch_bytes(url)
            target.write_bytes(body)
            status = "downloaded"
            error = ""
        except urllib.error.HTTPError as exc:
            status = "error"
            error = f"HTTP {exc.code}: {exc.reason}"
            headers = {}
        except urllib.error.URLError as exc:
            status = "error"
            error = str(exc.reason)
            headers = {}
        row = {
            **item,
            "url": url,
            "local_path": str(target.relative_to(ROOT)) if target.exists() else "",
            "status": status,
            "error": error,
            "bytes": target.stat().st_size if target.exists() else "",
            "sha256": sha256(target) if target.exists() else "",
            "etag": headers.get("etag", ""),
            "last_modified": headers.get("last-modified", ""),
        }
        rows.append(row)
    return rows


def download_latest_release_asset(releases: list[dict[str, Any]]) -> dict[str, Any]:
    if not releases:
        return {"status": "skipped", "reason": "no release assets found"}
    latest = releases[0]
    url = latest.get("browser_download_url")
    if not url:
        return {"status": "skipped", "reason": "latest release has no asset URL"}
    target = RAW_DIR / safe_name(latest["asset_name"])
    req = request(url)
    bytes_written = 0
    with urllib.request.urlopen(req, timeout=120) as resp, target.open("wb") as f:
        while True:
            chunk = resp.read(1024 * 1024 * 8)
            if not chunk:
                break
            f.write(chunk)
            bytes_written += len(chunk)
    extract_dir = RAW_DIR / target.stem
    extracted_files: list[str] = []
    zip_members: list[dict[str, Any]] = []
    if zipfile.is_zipfile(target):
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target) as zf:
            for member in zf.infolist():
                zip_members.append(
                    {
                        "filename": member.filename,
                        "file_size": member.file_size,
                        "compress_size": member.compress_size,
                    }
                )
                if member.file_size > 250_000_000:
                    continue
                zf.extract(member, extract_dir)
                extracted_files.append(str((extract_dir / member.filename).relative_to(ROOT)))
    return {
        "status": "downloaded",
        "asset_name": latest["asset_name"],
        "asset_size_bytes": latest["asset_size_bytes"],
        "bytes_written": bytes_written,
        "local_path": str(target.relative_to(ROOT)),
        "sha256": sha256(target),
        "zip_members": zip_members[:500],
        "extracted_files": extracted_files[:200],
    }


def infer_normalized_row(path: Path, source_kind: str, dashboard_tab: str) -> dict[str, Any]:
    text = path.name.lower()
    model = ""
    for token in ["deepseek", "dsr1", "qwen", "llama", "gptoss", "kimi", "glm", "minimax"]:
        if token in text:
            model = token
            break
    gpu = ""
    for token in ["gb300", "gb200", "b300", "b200", "h200", "h100", "mi355x", "mi325x", "mi300x"]:
        if token in text:
            gpu = token.upper()
            break
    precision = ""
    for token in ["fp4", "fp8", "bf16", "int4"]:
        if token in text:
            precision = token.upper()
            break
    framework = ""
    for token in ["sglang", "vllm", "trt", "dynamo", "atom"]:
        if token in text:
            framework = token
            break
    return {
        "source_file": str(path.relative_to(ROOT)),
        "source_kind": source_kind,
        "benchmark_id": path.stem,
        "dashboard_tab": dashboard_tab,
        "model": model,
        "model_family": model,
        "gpu": gpu,
        "gpu_vendor": "NVIDIA" if gpu.startswith(("B", "G", "H")) else ("AMD" if gpu.startswith("MI") else ""),
        "framework": framework,
        "precision": precision,
        "source_url": "",
        "evidence_class": "Proxy/Benchmark",
        "caveat": "Auto-indexed file-level row; metric values require DB/CSV normalization before use in forecast.",
    }


def pick(row: dict[str, Any], field: str) -> Any:
    lowered = {str(k).lower(): v for k, v in row.items()}
    for alias in FIELD_ALIASES.get(field, [field]):
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return ""


def normalize_record(path: Path, record: dict[str, Any], source_kind: str, dashboard_tab: str) -> dict[str, Any]:
    base = infer_normalized_row(path, source_kind, dashboard_tab)
    for field in FIELD_ALIASES:
        value = pick(record, field)
        if value != "":
            base[field] = value
    base["source_file"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    base["source_kind"] = source_kind
    base["dashboard_tab"] = pick(record, "dashboard_tab") or dashboard_tab
    base["benchmark_id"] = pick(record, "benchmark_id") or base["benchmark_id"]
    base["evidence_class"] = "Proxy/Benchmark"
    base["caveat"] = "Normalized benchmark/export row; use only after checking model/GPU/framework/precision/ISL/OSL comparability."
    return base


def normalize_csv(path: Path, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        for i, record in enumerate(csv.DictReader(f)):
            if i >= limit:
                break
            rows.append(normalize_record(path, record, "user_supplied_csv_export", "inference_performance"))
    return rows


def normalize_json(path: Path, limit: int) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    records: list[dict[str, Any]] = []
    if path.suffix.lower() == ".jsonl":
        for line in text.splitlines():
            if line.strip():
                item = json.loads(line)
                if isinstance(item, dict):
                    records.append(item)
    else:
        item = json.loads(text)
        if isinstance(item, list):
            records = [r for r in item if isinstance(r, dict)]
        elif isinstance(item, dict):
            for key in ("rows", "data", "benchmarks", "results", "items"):
                if isinstance(item.get(key), list):
                    records = [r for r in item[key] if isinstance(r, dict)]
                    break
            if not records:
                records = [item]
    return [normalize_record(path, record, "user_supplied_json_export", "inference_performance") for record in records[:limit]]


def normalize_input_dir(input_dir: Path | None, max_rows_per_file: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in RAW_FILES:
        local = RAW_DIR / f"{safe_name(item['source_id'])}_{safe_name(Path(item['path']).name)}"
        if local.exists():
            rows.append(infer_normalized_row(local, item["source_kind"], item["dashboard_tab"]))
            rows[-1]["source_url"] = f"https://github.com/{item['repo']}/blob/{item['branch']}/{item['path']}"

    if input_dir and input_dir.exists():
        for path in sorted(input_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".csv", ".json", ".jsonl", ".parquet", ".duckdb", ".sqlite", ".db"}:
                if path.suffix.lower() == ".csv":
                    rows.extend(normalize_csv(path, max_rows_per_file))
                elif path.suffix.lower() in {".json", ".jsonl"}:
                    rows.extend(normalize_json(path, max_rows_per_file))
                else:
                    row = infer_normalized_row(path, "user_supplied_dump_or_export", "inference_performance")
                    row["source_url"] = str(path)
                    rows.append(row)
    return rows


def build_manifest(
    raw_rows: list[dict[str, Any]],
    releases: list[dict[str, Any]],
    downloaded_asset: dict[str, Any],
    normalized_rows: list[dict[str, Any]],
    parsed_dump: dict[str, Any],
) -> dict[str, Any]:
    latest_release = releases[0] if releases else {}
    return {
        "generated_at": RUN_DATE,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "InferenceX public GitHub repos and dashboard DB dump releases",
        "benchmark_repo": f"https://github.com/{BENCHMARK_REPO}",
        "app_repo": f"https://github.com/{APP_REPO}",
        "dashboard": "https://inferencex.semianalysis.com/",
        "latest_db_dump": {
            "tag_name": latest_release.get("tag_name"),
            "published_at": latest_release.get("published_at"),
            "asset_name": latest_release.get("asset_name"),
            "asset_size_bytes": latest_release.get("asset_size_bytes"),
            "asset_digest": latest_release.get("asset_digest"),
            "download_url": latest_release.get("browser_download_url"),
            "downloaded_in_this_run": downloaded_asset,
        },
        "raw_file_count": len(raw_rows),
        "release_asset_count": len(releases),
        "normalized_index_rows": len(normalized_rows),
        "parsed_dump": parsed_dump,
        "dashboard_tabs": TAB_RULES,
        "evidence_rule": "InferenceX is benchmark/proxy data. It can calibrate tokens/sec/MW and utilization sensitivity, but not company-specific production telemetry.",
    }


def write_docs(manifest: dict[str, Any]) -> None:
    latest = manifest["latest_db_dump"]
    lines = [
        "# InferenceX 데이터 수집 및 정규화 계획",
        "",
        f"- 기준일: {RUN_DATE}",
        "- 목적: InferenceX의 공개 benchmark/app/dump 자료를 A08 tokens/sec/MW, A09 utilization, GPU spec, TCO sanity layer로 반복 수집합니다.",
        "- 핵심 원칙: dashboard DOM 크롤링보다 GitHub repo, API route, weekly DB dump release, raw CSV/export를 우선합니다.",
        "",
        "## 확인된 공개 소스",
        "",
        f"- Benchmark repo: https://github.com/{BENCHMARK_REPO}",
        f"- Dashboard app repo: https://github.com/{APP_REPO}",
        "- Dashboard: https://inferencex.semianalysis.com/",
        f"- 최신 확인 DB dump: `{latest.get('tag_name')}` / `{latest.get('asset_name')}` / {latest.get('asset_size_bytes')} bytes",
        "- App README 기준: dashboard는 Neon PostgreSQL 또는 static JSON dump를 데이터 소스로 사용합니다.",
        f"- Full dump parse status: `{manifest.get('parsed_dump', {}).get('status', 'not_run')}`",
        f"- Full dump benchmark rows: `{manifest.get('parsed_dump', {}).get('benchmark_rows', 0)}` / total records `{manifest.get('parsed_dump', {}).get('benchmark_records_total', 0)}`",
        f"- Full dump SHA-256: `{manifest.get('parsed_dump', {}).get('sha256', '')}`",
        "",
        "## Source 우선순위",
        "",
        "| 우선순위 | Source | 사용 방식 | 비고 |",
        "|---:|---|---|---|",
        "| 1 | GitHub release DB dump / raw CSV export | 정규화 후 benchmark table 생성 | 대용량이므로 명시 옵션으로 다운로드 |",
        "| 2 | InferenceX benchmark repo / GitHub Actions artifacts | benchmark provenance, run URL, config 추적 | public run/artifact가 열려 있을 때 사용 |",
        "| 3 | Dashboard app API route / docs / schema | table 의미, API field mapping | source code로 schema 확인 |",
        "| 4 | Dashboard DOM | 마지막 fallback | 표가 동적으로 바뀌므로 기본 금지 |",
        "",
        "## Dashboard tab mapping",
        "",
        "| Tab | 모델 내 사용처 | 필요한 key | Forecast 반영 |",
        "|---|---|---|---|",
    ]
    for row in TAB_RULES:
        lines.append(f"| {row['dashboard_tab']} | {row['use_in_model']} | {row['required_keys']} | {row['forecast_use']} |")
    lines += [
        "",
        "## 정규화 스키마",
        "",
        "정규화 파일은 `data/inferencex/normalized/inferencex_normalized_schema.csv`를 기준으로 합니다.",
        "",
        "```text",
        ", ".join(NORMALIZED_HEADERS),
        "```",
        "",
        "## 사용 규칙",
        "",
        "- InferenceX 수치는 `Proxy/Benchmark`입니다. 특정 회사의 production token telemetry로 쓰지 않습니다.",
        "- ISL/OSL, precision, framework, GPU, concurrency가 다른 값을 한 숫자로 평균 내지 않습니다.",
        "- GPU별 비교는 반드시 모델별 `main_framework`와 `main_precision`이 같은 행만 사용합니다.",
        "- `inferencex_gpu_comparable_metric_profile.csv`는 `is_main_model_config=yes` 행만 모은 GPU 비교용 summary입니다.",
        "- tokens/sec/MW는 A08 sensitivity 또는 benchmark sanity layer에만 먼저 반영합니다.",
        "- latency/SLO, concurrency, P/D disaggregation 정보는 A09 utilization sensitivity로 분리합니다.",
        "- TCO calculator 값은 memory marketing 및 cost/token narrative용이며 company capacity forecast를 직접 바꾸지 않습니다.",
        "",
        "## 실행",
        "",
        "```bash",
        ".venv/bin/python llm_token_capacity_project/tools/fetch_inferencex_data.py",
        ".venv/bin/python llm_token_capacity_project/tools/fetch_inferencex_data.py --input-dir /path/to/inferencex-dump",
        ".venv/bin/python llm_token_capacity_project/tools/fetch_inferencex_data.py --download-latest-dump",
        "```",
        "",
        "`--download-latest-dump`는 최신 release asset이 1GB 이상일 수 있으므로 필요할 때만 실행합니다.",
        "",
        "## 산출물",
        "",
        "- `data/inferencex/metadata/inferencex_manifest.json`",
        "- `data/inferencex/normalized/inferencex_source_index.csv`",
        "- `data/inferencex/normalized/inferencex_normalized_schema.csv`",
        "- main simulation workbook의 `12_inferencex_source_index`, `12a_inferencex_schema`, `12b_inferencex_tab_rules`",
        "- full dump 처리 시 `inferencex_benchmark_results.csv`, `inferencex_metric_profile.csv`, `inferencex_accuracy_evals.csv`, `inferencex_dump_inventory.csv`",
        "- GPU 비교 전용: `inferencex_main_config_by_model.csv`, `inferencex_main_config_validation.csv`, `inferencex_gpu_comparable_metric_profile.csv`",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, help="Optional local InferenceX dump/export directory to index.")
    parser.add_argument("--dump-zip", type=Path, help="Optional local InferenceX DB dump zip to parse without extracting huge files.")
    parser.add_argument("--download-latest-dump", action="store_true", help="Download the latest InferenceX-app DB dump asset.")
    parser.add_argument("--max-rows-per-file", type=int, default=50_000, help="Maximum CSV/JSON rows to normalize per input file.")
    parser.add_argument("--max-dump-rows", type=int, default=100_000, help="Maximum benchmark/eval rows to normalize from a DB dump zip.")
    args = parser.parse_args()

    for path in (RAW_DIR, NORM_DIR, META_DIR):
        path.mkdir(parents=True, exist_ok=True)

    raw_rows = download_raw_files()
    releases = collect_releases(APP_REPO)
    write_csv(NORM_DIR / "inferencex_release_assets.csv", releases, list(releases[0].keys()) if releases else ["repo"])

    downloaded_asset = {"status": "skipped", "reason": "use --download-latest-dump for large weekly DB dump assets"}
    if args.download_latest_dump:
        downloaded_asset = download_latest_release_asset(releases)

    normalized_rows = normalize_input_dir(args.input_dir, args.max_rows_per_file)
    latest_asset = releases[0].get("asset_name") if releases else ""
    default_zip = RAW_DIR / safe_name(latest_asset) if latest_asset else Path()
    dump_zip = args.dump_zip or (default_zip if default_zip.exists() else None)
    parsed_dump = {"status": "skipped", "reason": "no local dump zip found; pass --dump-zip or --download-latest-dump"}
    if dump_zip:
        parsed_dump = process_inferencex_dump_zip(dump_zip, releases[0].get("tag_name") if releases else None, args.max_dump_rows)
    write_csv(NORM_DIR / "inferencex_source_index.csv", normalized_rows, NORMALIZED_HEADERS)
    write_csv(NORM_DIR / "inferencex_normalized_schema.csv", [{h: "" for h in NORMALIZED_HEADERS}], NORMALIZED_HEADERS)
    write_csv(NORM_DIR / "inferencex_tab_rules.csv", TAB_RULES, list(TAB_RULES[0].keys()))
    write_csv(
        NORM_DIR / "inferencex_raw_file_index.csv",
        raw_rows,
        list(raw_rows[0].keys()) if raw_rows else ["source_id"],
    )

    manifest = build_manifest(raw_rows, releases, downloaded_asset, normalized_rows, parsed_dump)
    (META_DIR / "inferencex_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    write_docs(manifest)

    # Keep a stable latest copy path if a user later downloads/extracts a dump outside this tree.
    latest_pointer = DATA_DIR / "LATEST_README.txt"
    latest_pointer.write_text(
        "InferenceX ingestion metadata was refreshed.\n"
        f"Latest release tag: {manifest['latest_db_dump'].get('tag_name')}\n"
        f"Latest release URL: {manifest['latest_db_dump'].get('download_url')}\n",
        encoding="utf-8",
    )

    print(json.dumps({"status": "PASS", "manifest": str((META_DIR / "inferencex_manifest.json").relative_to(ROOT)), "rows": len(normalized_rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
