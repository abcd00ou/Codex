"""Build an InferenceX -> LLMServingSim bridge dataset.

The tool does not run LLMServingSim. It prepares the benchmark surface and
scenario table needed to turn InferenceX rows into simulator-backed workload
experiments.
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "inferencex" / "normalized" / "inferencex_benchmark_results.csv"
DEFAULT_OUT_DIR = ROOT / "outputs" / "reports"


@dataclass(frozen=True)
class SurfaceKey:
    model: str
    gpu: str
    framework: str
    precision: str
    gpu_count: str
    isl: int
    osl: int
    concurrency: str


@dataclass
class SurfaceRow:
    key: SurfaceKey
    rows: int
    output_p50: float
    output_p10: float
    output_p90: float
    input_p50: float
    total_p50: float
    tpot_p50_ms: float | None
    ttft_p50_ms: float | None
    power_w_p50: float | None
    kv_pressure_proxy: float
    decode_work_proxy: float
    baseline_output_p50: float | None = None
    realization_vs_baseline: float | None = None


def _float(value: str) -> float | None:
    if value in ("", "NA", "nan", "None", None):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int(value: str) -> int | None:
    v = _float(value)
    if v is None:
        return None
    return int(v)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    idx = (len(values) - 1) * pct
    lo = int(idx)
    hi = min(lo + 1, len(values) - 1)
    frac = idx - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def load_surface(
    input_csv: Path,
    gpus: set[str],
    benchmark_type: str,
    min_rows: int,
) -> list[SurfaceRow]:
    groups: dict[SurfaceKey, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    with input_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if benchmark_type and row.get("benchmark_type") != benchmark_type:
                continue
            gpu = (row.get("gpu") or "").lower()
            if gpus and gpu not in gpus:
                continue
            isl = _int(row.get("isl", ""))
            osl = _int(row.get("osl", ""))
            if isl is None or osl is None:
                continue
            output = _float(row.get("output_tok_s_mw", ""))
            if output is None or output <= 0:
                continue
            key = SurfaceKey(
                model=row.get("model", "") or "unknown",
                gpu=gpu,
                framework=row.get("framework", "") or "unknown",
                precision=row.get("precision", "") or "unknown",
                gpu_count=row.get("gpu_count", "") or "unknown",
                isl=isl,
                osl=osl,
                concurrency=row.get("concurrency", "") or "unknown",
            )
            bucket = groups[key]
            bucket["output"].append(output)
            for source, dest in [
                ("input_tok_s_mw", "input"),
                ("total_tok_s_mw", "total"),
                ("median_tpot_ms", "tpot"),
                ("median_ttft_ms", "ttft"),
                ("power_w", "power"),
            ]:
                v = _float(row.get(source, ""))
                if v is not None and v > 0:
                    bucket[dest].append(v)

    rows: list[SurfaceRow] = []
    for key, values in groups.items():
        if len(values["output"]) < min_rows:
            continue
        concurrency = _float(key.concurrency) or 1.0
        rows.append(
            SurfaceRow(
                key=key,
                rows=len(values["output"]),
                output_p50=statistics.median(values["output"]),
                output_p10=_percentile(values["output"], 0.10),
                output_p90=_percentile(values["output"], 0.90),
                input_p50=statistics.median(values["input"]) if values["input"] else 0.0,
                total_p50=statistics.median(values["total"]) if values["total"] else 0.0,
                tpot_p50_ms=statistics.median(values["tpot"]) if values["tpot"] else None,
                ttft_p50_ms=statistics.median(values["ttft"]) if values["ttft"] else None,
                power_w_p50=statistics.median(values["power"]) if values["power"] else None,
                kv_pressure_proxy=key.isl * concurrency,
                decode_work_proxy=key.osl * concurrency,
            )
        )

    baselines: dict[tuple[str, str, str, str, str, str], float] = {}
    for row in rows:
        if row.key.isl == 1024 and row.key.osl == 1024:
            bkey = (
                row.key.model,
                row.key.gpu,
                row.key.framework,
                row.key.precision,
                row.key.gpu_count,
                row.key.concurrency,
            )
            baselines[bkey] = row.output_p50

    for row in rows:
        bkey = (
            row.key.model,
            row.key.gpu,
            row.key.framework,
            row.key.precision,
            row.key.gpu_count,
            row.key.concurrency,
        )
        baseline = baselines.get(bkey)
        row.baseline_output_p50 = baseline
        if baseline and baseline > 0:
            row.realization_vs_baseline = row.output_p50 / baseline

    return sorted(
        rows,
        key=lambda r: (
            r.key.model,
            r.key.gpu,
            r.key.framework,
            r.key.precision,
            r.key.gpu_count,
            r.key.concurrency,
            r.key.isl,
            r.key.osl,
        ),
    )


def write_surface_csv(rows: list[SurfaceRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model",
        "gpu",
        "framework",
        "precision",
        "gpu_count",
        "isl",
        "osl",
        "concurrency",
        "rows",
        "output_p50_tok_s_mw",
        "output_p10_tok_s_mw",
        "output_p90_tok_s_mw",
        "input_p50_tok_s_mw",
        "total_p50_tok_s_mw",
        "median_tpot_ms",
        "median_ttft_ms",
        "power_w_p50",
        "kv_pressure_proxy_isl_x_concurrency",
        "decode_work_proxy_osl_x_concurrency",
        "baseline_1024_1024_output_p50_tok_s_mw",
        "realization_vs_same_config_1024_1024",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "model": r.key.model,
                    "gpu": r.key.gpu,
                    "framework": r.key.framework,
                    "precision": r.key.precision,
                    "gpu_count": r.key.gpu_count,
                    "isl": r.key.isl,
                    "osl": r.key.osl,
                    "concurrency": r.key.concurrency,
                    "rows": r.rows,
                    "output_p50_tok_s_mw": round(r.output_p50, 6),
                    "output_p10_tok_s_mw": round(r.output_p10, 6),
                    "output_p90_tok_s_mw": round(r.output_p90, 6),
                    "input_p50_tok_s_mw": round(r.input_p50, 6),
                    "total_p50_tok_s_mw": round(r.total_p50, 6),
                    "median_tpot_ms": round(r.tpot_p50_ms, 6) if r.tpot_p50_ms else "",
                    "median_ttft_ms": round(r.ttft_p50_ms, 6) if r.ttft_p50_ms else "",
                    "power_w_p50": round(r.power_w_p50, 6) if r.power_w_p50 else "",
                    "kv_pressure_proxy_isl_x_concurrency": round(r.kv_pressure_proxy, 6),
                    "decode_work_proxy_osl_x_concurrency": round(r.decode_work_proxy, 6),
                    "baseline_1024_1024_output_p50_tok_s_mw": round(r.baseline_output_p50, 6)
                    if r.baseline_output_p50
                    else "",
                    "realization_vs_same_config_1024_1024": round(r.realization_vs_baseline, 6)
                    if r.realization_vs_baseline
                    else "",
                }
            )


def write_markdown(rows: list[SurfaceRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    comparable = [r for r in rows if r.realization_vs_baseline is not None and r.key.isl != 1024]
    comparable = sorted(comparable, key=lambda r: r.realization_vs_baseline or 999)[:20]
    strongest = sorted(rows, key=lambda r: r.output_p50, reverse=True)[:20]

    lines = [
        "# LLMServingSim Bridge from InferenceX",
        "",
        "This report prepares InferenceX benchmark rows for LLMServingSim-style serving realism analysis.",
        "",
        "## Why this exists",
        "",
        "InferenceX already captures hardware, model, precision, ISL, OSL, concurrency, throughput, latency, and power-derived metrics. LLMServingSim adds the dynamic serving layer: request arrivals, batching, routing, KV cache residency, memory tiering, parallelism, and SLO behavior.",
        "",
        "## Output files",
        "",
        "- `llmservingsim_bridge_surface.csv`: grouped benchmark surface.",
        "- `llmservingsim_bridge_report.md`: this summary.",
        "",
        "## Columns to feed into future LLMServingSim scenarios",
        "",
        "| Column | Use |",
        "|---|---|",
        "| `model`, `gpu`, `framework`, `precision` | Match a profiler/hardware configuration. |",
        "| `isl`, `osl`, `concurrency` | Convert benchmark points into workload JSONL distributions. |",
        "| `output_p50_tok_s_mw` | Public benchmark anchor for generated-token capacity. |",
        "| `median_tpot_ms`, `median_ttft_ms` | Initial SLO sanity check when available. |",
        "| `kv_pressure_proxy_isl_x_concurrency` | First-order proxy for KV cache pressure. |",
        "| `realization_vs_same_config_1024_1024` | Sequence-length sensitivity before full simulation. |",
        "",
        "## Largest long-context drops vs same-config 1024/1024 baseline",
        "",
        "| Model | GPU | Framework | Precision | GPU count | Concurrency | ISL | OSL | Rows | Output p50 tok/s/MW | Realization |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in comparable:
        lines.append(
            f"| {r.key.model} | {r.key.gpu} | {r.key.framework} | {r.key.precision} | {r.key.gpu_count} | "
            f"{r.key.concurrency} | {r.key.isl} | {r.key.osl} | {r.rows} | {r.output_p50:,.0f} | "
            f"{r.realization_vs_baseline:.2f} |"
        )

    lines += [
        "",
        "## Highest output-token benchmark anchors",
        "",
        "| Model | GPU | Framework | Precision | GPU count | ISL | OSL | Concurrency | Rows | Output p50 tok/s/MW |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in strongest:
        lines.append(
            f"| {r.key.model} | {r.key.gpu} | {r.key.framework} | {r.key.precision} | {r.key.gpu_count} | "
            f"{r.key.isl} | {r.key.osl} | {r.key.concurrency} | {r.rows} | {r.output_p50:,.0f} |"
        )

    lines += [
        "",
        "## Next simulation handoff",
        "",
        "Use the CSV rows to generate LLMServingSim workloads:",
        "",
        "```json",
        '{"input_toks": 8192, "output_toks": 1024, "arrival_time_ns": 0}',
        "```",
        "",
        "For agentic workloads, convert a sequence of rows into sub-requests:",
        "",
        "```json",
        '{"session_id": "coding_agent_0", "arrival_time_ns": 0, "sub_requests": [{"input_toks": 8192, "output_toks": 512, "tool_duration_ns": 1000000000}]}',
        "```",
        "",
        "The current `kv_pressure_proxy` is intentionally simple. It is a ranking feature, not a physical KV-cache byte model. The next version should add model-layer/head/hidden-dimension metadata so KV bytes can be estimated explicitly.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--gpus", default="h200,b200,gb200")
    parser.add_argument("--benchmark-type", default="single_turn")
    parser.add_argument("--min-rows", type=int, default=10)
    args = parser.parse_args()

    gpus = {g.strip().lower() for g in args.gpus.split(",") if g.strip()}
    rows = load_surface(args.input, gpus, args.benchmark_type, args.min_rows)

    surface_csv = args.out_dir / "llmservingsim_bridge_surface.csv"
    report_md = args.out_dir / "llmservingsim_bridge_report.md"
    write_surface_csv(rows, surface_csv)
    write_markdown(rows, report_md)

    print(f"rows={len(rows)}")
    print(f"wrote={surface_csv}")
    print(f"wrote={report_md}")


if __name__ == "__main__":
    main()
