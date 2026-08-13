"""Build the NVIDIA GPU/interactivity TPS/MW reference from live InferenceX rows.

For each proxy, workload, GPU and target interactivity, the generator selects
the actual InferenceX benchmark row with the highest generated-output TPS/MW
among rows whose median interactivity meets the target.  Precision, framework,
speculative-decoding method and concurrency therefore come from that selected
benchmark row; they are not assigned by a separate workload model.

When a GPU has no rows for that model/workload, the configured benchmark
anchor's measured NVIDIA curve is scaled by the ratio of HBM-bandwidth per
all-in kW. Interactivity, concurrency, precision and framework remain those of
the selected source benchmark row. Rows that cannot meet the requested
interactivity, or future GPUs without both editable inputs, remain blank.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = ROOT / "data" / "inferencex" / "live_api"
OUT_DIR = ROOT / "docs" / "dynamic_reasoning_agent_cost"
DETAIL_CSV = OUT_DIR / "nvidia_gpu_interactivity_tps_mw_detail.csv"
SUMMARY_CSV = OUT_DIR / "nvidia_gpu_interactivity_tps_mw_summary.csv"
SCALING_CSV = OUT_DIR / "nvidia_gpu_scaling_assumptions.csv"
SCALING_INPUT_CSV = OUT_DIR / "nvidia_gpu_scaling_inputs.csv"
OUT_JSON = OUT_DIR / "nvidia_gpu_interactivity_reference.json"

TARGETS = (30, 50, 70, 100)
DIRECT_GPUS = ("H200", "B200", "B300", "GB200", "GB300")

PROXIES = (
    {
        "proxy_model": "DeepSeek V4 Pro",
        "model_key": "dsv4",
        "file": "deepseek_v4_pro.json",
        "fallback_model_key": "",
        "fallback_file": "",
    },
    {
        "proxy_model": "Kimi K2.5",
        "model_key": "kimik2.5",
        "file": "kimi_k2_5.json",
        "fallback_model_key": "",
        "fallback_file": "",
    },
    {
        "proxy_model": "MiniMax M3",
        "model_key": "minimaxm3",
        "file": "minimax_m3.json",
        "fallback_model_key": "minimaxm2.5",
        "fallback_file": "minimax_m2_5_fallback.json",
    },
    {
        "proxy_model": "GLM 5.2",
        "model_key": "glm5.2",
        "file": "glm_5_2.json",
        "fallback_model_key": "glm5",
        "fallback_file": "glm_5_fallback.json",
    },
    {
        "proxy_model": "Qwen 3.5",
        "model_key": "qwen3.5",
        "file": "qwen_3_5.json",
        "fallback_model_key": "",
        "fallback_file": "",
    },
)

def optional_float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    parsed = float(text)
    return parsed if parsed > 0 else None


def load_gpu_scaling_inputs() -> tuple[dict[str, Any], ...]:
    with SCALING_INPUT_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    expected = set(DIRECT_GPUS) | {"R200", "VR200", "R300", "VR300", "Post Rubin"}
    actual = {row["gpu"] for row in rows}
    if actual != expected:
        raise ValueError(f"GPU scaling input mismatch: expected {sorted(expected)}, got {sorted(actual)}")
    for row in rows:
        row["hbm_bandwidth_tb_s"] = optional_float(row.get("hbm_bandwidth_tb_s"))
        row["all_in_kw"] = optional_float(row.get("all_in_kw"))
    return tuple(rows)


GPU_SCALING = load_gpu_scaling_inputs()
INFERENCEX_ALL_IN_KW = {
    row["gpu"]: float(row["all_in_kw"])
    for row in GPU_SCALING
    if row["gpu"] in DIRECT_GPUS and row["all_in_kw"] is not None
}


def bandwidth_efficiencies() -> dict[str, float]:
    return {
        row["gpu"]: float(row["hbm_bandwidth_tb_s"]) / float(row["all_in_kw"])
        for row in GPU_SCALING
        if row["hbm_bandwidth_tb_s"] is not None and row["all_in_kw"] is not None
    }


def bandwidth_efficiency_indices() -> dict[str, float]:
    """Return HBM-bandwidth/all-in-power efficiency indexed to H200."""
    efficiencies = bandwidth_efficiencies()
    h200 = efficiencies["H200"]
    return {gpu: efficiency / h200 for gpu, efficiency in efficiencies.items()}


def configured_benchmark_source(target_gpu: str, available: Iterable[str]) -> str | None:
    available_set = set(available)
    by_gpu = {row["gpu"]: row for row in GPU_SCALING}
    current = target_gpu
    visited: set[str] = set()
    while current and current not in visited:
        visited.add(current)
        anchor = str(by_gpu[current].get("anchor_gpu") or "")
        if anchor in available_set:
            return anchor
        current = anchor
    return None


def load_json_rows(filename: str) -> list[dict[str, Any]]:
    if not filename:
        return []
    payload = json.loads((LIVE_DIR / filename).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError(f"Expected a JSON array in {filename}")
    return payload


def is_workload_row(row: dict[str, Any], workload: str) -> bool:
    if workload == "short":
        return row.get("benchmark_type") == "single_turn" and row.get("isl") == 1024 and row.get("osl") == 1024
    if workload == "long":
        return row.get("benchmark_type") == "single_turn" and row.get("isl") == 8192 and row.get("osl") == 1024
    return row.get("benchmark_type") == "agentic_traces"


def valid_row(row: dict[str, Any]) -> bool:
    metrics = row.get("metrics") or {}
    return (
        str(row.get("hardware", "")).upper() in DIRECT_GPUS
        and isinstance(metrics.get("median_intvty"), (int, float))
        and metrics["median_intvty"] > 0
        and isinstance(metrics.get("output_tput_per_gpu"), (int, float))
        and metrics["output_tput_per_gpu"] > 0
    )


def workload_rows(proxy: dict[str, str], workload: str) -> tuple[list[dict[str, Any]], str, bool]:
    exact = [row for row in load_json_rows(proxy["file"]) if valid_row(row) and is_workload_row(row, workload)]
    if exact:
        return exact, proxy["model_key"], False
    fallback = [
        row
        for row in load_json_rows(proxy["fallback_file"])
        if valid_row(row) and is_workload_row(row, workload)
    ]
    return fallback, proxy["fallback_model_key"], bool(fallback)


def direct_tps_mw(row: dict[str, Any]) -> float:
    gpu = str(row["hardware"]).upper()
    return float(row["metrics"]["output_tput_per_gpu"]) * 1000 / INFERENCEX_ALL_IN_KW[gpu]


def nearest_source_gpu(target_gpu: str, available: Iterable[str], indices: dict[str, float]) -> str | None:
    candidates = list(available)
    if not candidates or target_gpu not in indices:
        return None
    comparable = [gpu for gpu in candidates if gpu in indices]
    if not comparable:
        return None
    return min(comparable, key=lambda gpu: abs(math.log(indices[target_gpu] / indices[gpu])))


def select_row(
    rows: list[dict[str, Any]], target_gpu: str, target_interactivity: int, indices: dict[str, float]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    exact_rows = [row for row in rows if str(row["hardware"]).upper() == target_gpu]
    scaled = False
    source_gpu = target_gpu
    candidates = exact_rows
    if not candidates:
        available = sorted({str(row["hardware"]).upper() for row in rows})
        source_gpu = (
            configured_benchmark_source(target_gpu, available)
            or nearest_source_gpu(target_gpu, available, indices)
            or ""
        )
        candidates = [row for row in rows if str(row["hardware"]).upper() == source_gpu]
        scaled = bool(candidates)

    scale = (
        indices[target_gpu] / indices[source_gpu]
        if source_gpu and target_gpu in indices and source_gpu in indices
        else None
    )
    evaluated = []
    for row in candidates if scale is not None else []:
        observed_intvty = float(row["metrics"]["median_intvty"])
        selected_intvty = observed_intvty
        observed_tps_mw = direct_tps_mw(row)
        selected_tps_mw = observed_tps_mw * scale
        if selected_intvty >= target_interactivity:
            evaluated.append((selected_tps_mw, selected_intvty, row, observed_tps_mw, observed_intvty))

    info = {
        "source_gpu": source_gpu,
        "scale": scale,
        "candidate_rows": len(candidates),
        "eligible_rows": len(evaluated),
        "scaled": scaled,
        "settings_missing": scale is None,
    }
    if not evaluated:
        return None, info
    selected_tps_mw, selected_intvty, row, observed_tps_mw, observed_intvty = max(
        evaluated,
        key=lambda item: (item[0], item[1], float(item[2].get("conc") or 0)),
    )
    info.update(
        {
            "selected_tps_mw": selected_tps_mw,
            "selected_intvty": selected_intvty,
            "observed_tps_mw": observed_tps_mw,
            "observed_intvty": observed_intvty,
        }
    )
    return row, info


def blank_detail(
    proxy: dict[str, str], workload: str, gpu: str, target: int, source_model: str, fallback_used: bool, info: dict[str, Any]
) -> dict[str, Any]:
    return {
        "reference_key": f"{proxy['proxy_model']}|{gpu}|{workload}|{target}",
        "proxy_model": proxy["proxy_model"],
        "source_model": source_model,
        "gpu": gpu,
        "workload": workload,
        "target_tok_s_user": target,
        "target_met": False,
        "effective_output_tps_per_mw": "",
        "selected_tok_s_user": "",
        "observed_tok_s_user": "",
        "performance_multiplier_vs_source": (
            round(float(info["scale"]), 8) if info.get("scale") is not None else ""
        ),
        "source_gpu": info.get("source_gpu", ""),
        "benchmark_id": "",
        "framework": "",
        "precision": "",
        "spec_method": "",
        "concurrency": "",
        "benchmark_type": "agentic_traces" if workload == "agentic" else "single_turn",
        "selected_isl": "" if workload == "agentic" else (1024 if workload == "short" else 8192),
        "selected_osl": "" if workload == "agentic" else 1024,
        "candidate_rows": info.get("candidate_rows", 0),
        "eligible_rows": 0,
        "selection_status": (
            "unavailable_missing_hbm_bandwidth_or_all_in_power"
            if info.get("settings_missing")
            else "unavailable_target_not_met" if info.get("candidate_rows") else "unavailable_no_benchmark_curve"
        ),
        "source_type": "InferenceX_model_fallback_unavailable" if fallback_used else "InferenceX_exact_model_unavailable",
        "benchmark_date": "",
        "run_url": "",
        "method_note": (
            "Enter both HBM bandwidth (TB/s) and all-in power (kW) in the GPU scaling inputs."
            if info.get("settings_missing")
            else "No benchmark point reaches the requested interactivity; left blank (no edge-row reuse)."
        ),
    }


def build_detail_rows() -> tuple[list[dict[str, Any]], str]:
    indices = bandwidth_efficiency_indices()
    detail: list[dict[str, Any]] = []
    max_date = ""
    for proxy in PROXIES:
        for workload in ("short", "long", "agentic"):
            rows, source_model, fallback_used = workload_rows(proxy, workload)
            for gpu_row in GPU_SCALING:
                gpu = gpu_row["gpu"]
                for target in TARGETS:
                    selected, info = select_row(rows, gpu, target, indices)
                    if selected is None:
                        detail.append(blank_detail(proxy, workload, gpu, target, source_model, fallback_used, info))
                        continue
                    benchmark_date = str(selected.get("date") or "")
                    max_date = max(max_date, benchmark_date)
                    scaled = bool(info["scaled"])
                    source_kind = "model_fallback" if fallback_used else "exact_model"
                    detail.append(
                        {
                            "reference_key": f"{proxy['proxy_model']}|{gpu}|{workload}|{target}",
                            "proxy_model": proxy["proxy_model"],
                            "source_model": source_model,
                            "gpu": gpu,
                            "workload": workload,
                            "target_tok_s_user": target,
                            "target_met": True,
                            "effective_output_tps_per_mw": round(float(info["selected_tps_mw"]), 6),
                            "selected_tok_s_user": round(float(info["selected_intvty"]), 6),
                            "observed_tok_s_user": round(float(info["observed_intvty"]), 6),
                            "performance_multiplier_vs_source": round(float(info["scale"]), 8),
                            "source_gpu": info["source_gpu"],
                            "benchmark_id": selected.get("id", ""),
                            "framework": selected.get("framework", ""),
                            "precision": selected.get("precision", ""),
                            "spec_method": selected.get("spec_method", ""),
                            "concurrency": selected.get("conc", ""),
                            "benchmark_type": selected.get("benchmark_type", ""),
                            "selected_isl": selected.get("isl", "") if selected.get("isl") is not None else "",
                            "selected_osl": selected.get("osl", "") if selected.get("osl") is not None else "",
                            "candidate_rows": info["candidate_rows"],
                            "eligible_rows": info["eligible_rows"],
                            "selection_status": f"InferenceX_{'scaled' if scaled else 'direct'}_{source_kind}_target_met",
                            "source_type": f"InferenceX_{'scaled' if scaled else 'direct'}_{source_kind}",
                            "benchmark_date": benchmark_date,
                            "run_url": selected.get("run_url", ""),
                            "method_note": (
                                f"Selected highest output TPS/MW measured row meeting median interactivity >= {target}."
                                if not scaled
                                else (
                                    f"Measured {info['source_gpu']} TPS/MW multiplied by the HBM-bandwidth/all-in-power "
                                    f"ratio {info['scale']:.4f}x; source interactivity/concurrency/precision retained, then "
                                    f"selected the highest source row meeting {target}."
                                )
                            ),
                        }
                    )
    order_proxy = {row["proxy_model"]: i for i, row in enumerate(PROXIES)}
    order_gpu = {row["gpu"]: i for i, row in enumerate(GPU_SCALING)}
    order_workload = {name: i for i, name in enumerate(("short", "long", "agentic"))}
    detail.sort(
        key=lambda row: (
            order_proxy[row["proxy_model"]],
            order_gpu[row["gpu"]],
            row["target_tok_s_user"],
            order_workload[row["workload"]],
        )
    )
    return detail, max_date


def build_summary_rows(detail: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (row["proxy_model"], row["gpu"], row["target_tok_s_user"], row["workload"]): row
        for row in detail
    }
    output = []
    for proxy in PROXIES:
        for gpu_row in GPU_SCALING:
            for target in TARGETS:
                selected = {
                    workload: by_key[(proxy["proxy_model"], gpu_row["gpu"], target, workload)]
                    for workload in ("short", "long", "agentic")
                }
                output.append(
                    {
                        "proxy_model": proxy["proxy_model"],
                        "gpu": gpu_row["gpu"],
                        "interactivity_tok_s_user": target,
                        "short_tps_per_mw": selected["short"]["effective_output_tps_per_mw"],
                        "long_tps_per_mw": selected["long"]["effective_output_tps_per_mw"],
                        "agentic_tps_per_mw": selected["agentic"]["effective_output_tps_per_mw"],
                        "short_concurrency": selected["short"]["concurrency"],
                        "long_concurrency": selected["long"]["concurrency"],
                        "agentic_concurrency": selected["agentic"]["concurrency"],
                        "short_precision": selected["short"]["precision"],
                        "long_precision": selected["long"]["precision"],
                        "agentic_precision": selected["agentic"]["precision"],
                        "short_framework": selected["short"]["framework"],
                        "long_framework": selected["long"]["framework"],
                        "agentic_framework": selected["agentic"]["framework"],
                        "short_source_type": selected["short"]["source_type"],
                        "long_source_type": selected["long"]["source_type"],
                        "agentic_source_type": selected["agentic"]["source_type"],
                    }
                )
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    detail, max_date = build_detail_rows()
    summary = build_summary_rows(detail)
    indices = bandwidth_efficiency_indices()
    efficiencies = bandwidth_efficiencies()
    scaling_rows = [
        {
            **row,
            "hbm_bandwidth_tb_s": row["hbm_bandwidth_tb_s"] or "",
            "all_in_kw": row["all_in_kw"] or "",
            "bandwidth_efficiency_tb_s_per_kw": (
                round(efficiencies[row["gpu"]], 8) if row["gpu"] in efficiencies else ""
            ),
            "scale_vs_anchor": (
                round(efficiencies[row["gpu"]] / efficiencies[row["anchor_gpu"]], 8)
                if row["gpu"] in efficiencies and row.get("anchor_gpu") in efficiencies
                else 1.0 if row["gpu"] == "H200" else ""
            ),
            "bandwidth_efficiency_index_vs_h200": (
                round(indices[row["gpu"]], 8) if row["gpu"] in indices else ""
            ),
            "benchmark_data_max_date": max_date,
            "generated_at": date.today().isoformat(),
        }
        for row in GPU_SCALING
    ]
    write_csv(DETAIL_CSV, detail)
    write_csv(SUMMARY_CSV, summary)
    write_csv(SCALING_CSV, scaling_rows)
    OUT_JSON.write_text(
        json.dumps(
            {
                "metadata": {
                    "generated_at": date.today().isoformat(),
                    "source": "https://inferencex.semianalysis.com/api/v1/benchmarks",
                    "benchmark_data_max_date": max_date,
                    "targets_tok_s_user": list(TARGETS),
                    "interactivity_metric": "metrics.median_intvty",
                    "tps_mw_metric": "metrics.output_tput_per_gpu * 1000 / InferenceX all-in kW",
                    "missing_gpu_scaling_formula": "source TPS/MW * ((target HBM TB/s / target all-in kW) / (source HBM TB/s / source all-in kW))",
                    "selection": "max output TPS/MW among measured/scaled rows meeting target; no target-range clamping",
                },
                "gpu_scaling": scaling_rows,
                "detail": detail,
                "summary": summary,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "benchmark_data_max_date": max_date,
                "detail_rows": len(detail),
                "summary_rows": len(summary),
                "direct_rows": sum(str(row["source_type"]).startswith("InferenceX_direct") for row in detail),
                "scaled_rows": sum(str(row["source_type"]).startswith("InferenceX_scaled") for row in detail),
                "blank_rows": sum(row["effective_output_tps_per_mw"] == "" for row in detail),
                "fallback_rows": sum("model_fallback" in str(row["source_type"]) for row in detail),
                "outputs": [str(DETAIL_CSV), str(SUMMARY_CSV), str(SCALING_CSV), str(OUT_JSON)],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
