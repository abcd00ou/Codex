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
import urllib.error
import urllib.request
import zipfile
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
RUN_DATE = "2026-05-19"

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
    body, _headers = fetch_bytes(url)
    target.write_bytes(body)
    extract_dir = RAW_DIR / target.stem
    extracted_files: list[str] = []
    if zipfile.is_zipfile(target):
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target) as zf:
            for member in zf.infolist():
                if member.file_size > 250_000_000:
                    continue
                zf.extract(member, extract_dir)
                extracted_files.append(str((extract_dir / member.filename).relative_to(ROOT)))
    return {
        "status": "downloaded",
        "asset_name": latest["asset_name"],
        "asset_size_bytes": latest["asset_size_bytes"],
        "local_path": str(target.relative_to(ROOT)),
        "sha256": sha256(target),
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
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, help="Optional local InferenceX dump/export directory to index.")
    parser.add_argument("--download-latest-dump", action="store_true", help="Download the latest InferenceX-app DB dump asset.")
    parser.add_argument("--max-rows-per-file", type=int, default=50_000, help="Maximum CSV/JSON rows to normalize per input file.")
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
    write_csv(NORM_DIR / "inferencex_source_index.csv", normalized_rows, NORMALIZED_HEADERS)
    write_csv(NORM_DIR / "inferencex_normalized_schema.csv", [{h: "" for h in NORMALIZED_HEADERS}], NORMALIZED_HEADERS)
    write_csv(NORM_DIR / "inferencex_tab_rules.csv", TAB_RULES, list(TAB_RULES[0].keys()))
    write_csv(
        NORM_DIR / "inferencex_raw_file_index.csv",
        raw_rows,
        list(raw_rows[0].keys()) if raw_rows else ["source_id"],
    )

    manifest = build_manifest(raw_rows, releases, downloaded_asset, normalized_rows)
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
