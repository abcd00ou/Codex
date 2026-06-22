"""Query helper for the local InferenceX SQLite benchmark database."""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "inferencex" / "inferencex_benchmark.sqlite"
DEFAULT_SEQUENCE_CONDITIONS = "1024/1024,8192/1024,1024/8192"
DEFAULT_GPUS = "H200,B200,GB200"


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"{db_path} does not exist. Run tools/build_inferencex_benchmark_db.py first."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def quote_name(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_sequence_conditions(value: str) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for item in split_csv(value):
        if "/" not in item:
            raise ValueError(f"Sequence condition must be ISL/OSL, got {item!r}")
        isl, osl = item.split("/", 1)
        pairs.append((int(isl), int(osl)))
    return pairs


def add_in_filter(
    clauses: list[str], params: list[Any], column: str, values: list[str], lower: bool = False
) -> None:
    if not values:
        return
    placeholders = ", ".join("?" for _ in values)
    if lower:
        clauses.append(f"lower({column}) IN ({placeholders})")
        params.extend(value.lower() for value in values)
    else:
        clauses.append(f"{column} IN ({placeholders})")
        params.extend(values)


def add_sequence_filter(
    clauses: list[str], params: list[Any], pairs: list[tuple[int, int]]
) -> None:
    if not pairs:
        return
    clauses.append(
        "("
        + " OR ".join("(isl = ? AND osl = ?)" for _ in pairs)
        + ")"
    )
    for isl, osl in pairs:
        params.extend([isl, osl])


def format_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if abs(value) >= 100:
            return f"{value:,.0f}"
        return f"{value:,.3f}".rstrip("0").rstrip(".")
    return str(value)


def percentile(values: list[float], q: float) -> float | None:
    clean = sorted(value for value in values if value is not None)
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    position = (len(clean) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(clean) - 1)
    weight = position - lower
    return clean[lower] * (1 - weight) + clean[upper] * weight


def summarize_raw_groups(
    rows: list[sqlite3.Row],
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    metrics = [
        "input_tok_s_mw",
        "output_tok_s_mw",
        "total_tok_s_mw",
        "p99_ttft_ms",
        "p99_tpot_ms",
    ]
    for row in rows:
        key = (
            row["model"],
            row["gpu"].upper(),
            row["isl"],
            row["osl"],
            row["main_framework"],
            row["main_precision"],
        )
        group = groups.setdefault(
            key,
            {
                "model": row["model"],
                "gpu": row["gpu"].upper(),
                "isl": row["isl"],
                "osl": row["osl"],
                "main_framework": row["main_framework"],
                "main_precision": row["main_precision"],
                "_values": {metric: [] for metric in metrics},
            },
        )
        for metric in metrics:
            if row[metric] is not None:
                group["_values"][metric].append(row[metric])

    summaries: list[dict[str, Any]] = []
    for group in groups.values():
        values = group.pop("_values")
        output_values = values["output_tok_s_mw"]
        group["row_count"] = len(output_values)
        for metric, metric_values in values.items():
            group[f"{metric}_p10"] = percentile(metric_values, 0.10)
            group[f"{metric}_p50"] = percentile(metric_values, 0.50)
            group[f"{metric}_p90"] = percentile(metric_values, 0.90)
        summaries.append(group)
    return sorted(
        summaries,
        key=lambda item: (item["model"], item["gpu"], item["isl"], item["osl"]),
    )


def fetch_raw_summary_rows(
    conn: sqlite3.Connection,
    *,
    models: str,
    gpus: str,
    sequence_conditions: str,
    benchmark_type: str,
    min_rows: int,
) -> list[dict[str, Any]]:
    clauses = ["is_main_model_config = 'yes'", "output_tok_s_mw IS NOT NULL"]
    params: list[Any] = []
    if benchmark_type:
        clauses.append("benchmark_type = ?")
        params.append(benchmark_type)
    add_in_filter(clauses, params, "model", split_csv(models))
    add_in_filter(clauses, params, "gpu", split_csv(gpus), lower=True)
    add_sequence_filter(clauses, params, parse_sequence_conditions(sequence_conditions))

    rows = list(
        conn.execute(
            f"""
            SELECT
                model,
                gpu,
                isl,
                osl,
                main_framework,
                main_precision,
                input_tok_s_mw,
                output_tok_s_mw,
                total_tok_s_mw,
                p99_ttft_ms,
                p99_tpot_ms
            FROM benchmark_results
            WHERE {' AND '.join(clauses)}
            """,
            params,
        )
    )
    return [
        row
        for row in summarize_raw_groups(rows)
        if row["row_count"] >= min_rows
    ]


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def print_table(rows: list[dict[str, Any]], output_format: str) -> None:
    if not rows:
        print("(no rows)")
        return

    headers = list(rows[0].keys())
    if output_format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        return

    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        print("| " + " | ".join(format_number(row[header]) for header in headers) + " |")


def command_tables(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    rows = rows_to_dicts(
        conn.execute(
            """
            SELECT name, type
            FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        )
    )
    print_table(rows, args.format)


def command_schema(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    rows = rows_to_dicts(conn.execute(f"PRAGMA table_info({quote_name(args.table)})"))
    print_table(rows, args.format)


def command_sql(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    sql = args.sql.strip().rstrip(";")
    allowed_prefixes = ("select", "with", "pragma")
    if not sql.lower().startswith(allowed_prefixes):
        raise ValueError("Only SELECT, WITH, and PRAGMA queries are allowed.")
    if args.limit and sql.lower().startswith(("select", "with")) and " limit " not in sql.lower():
        sql = f"{sql} LIMIT {args.limit}"
    rows = rows_to_dicts(conn.execute(sql))
    print_table(rows, args.format)


def command_gpu_summary(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    summaries = fetch_raw_summary_rows(
        conn,
        models=args.models,
        gpus=args.gpus,
        sequence_conditions=args.sequence_conditions,
        benchmark_type=args.benchmark_type,
        min_rows=args.min_rows,
    )
    rows = [
        {
            "Model": row["model"],
            "GPU": row["gpu"],
            "ISL": row["isl"],
            "OSL": row["osl"],
            "Rows": row["row_count"],
            "Input p50 tok/s/MW": row["input_tok_s_mw_p50"],
            "Output p50 tok/s/MW": row["output_tok_s_mw_p50"],
            "Input+Output p50 sum": (
                row["input_tok_s_mw_p50"] + row["output_tok_s_mw_p50"]
                if row["input_tok_s_mw_p50"] is not None
                and row["output_tok_s_mw_p50"] is not None
                else None
            ),
            "InferenceX total p50": row["total_tok_s_mw_p50"],
            "Output p10": row["output_tok_s_mw_p10"],
            "Output p90": row["output_tok_s_mw_p90"],
            "p99 TTFT p50 ms": row["p99_ttft_ms_p50"],
            "p99 TPOT p50 ms": row["p99_tpot_ms_p50"],
            "Main framework": row["main_framework"],
            "Main precision": row["main_precision"],
        }
        for row in summaries
    ]
    print_table(rows, args.format)


def command_isl_osl(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    baseline_isl, baseline_osl = args.baseline.split("/", 1)
    raw_rows = fetch_raw_summary_rows(
        conn,
        models=args.models,
        gpus=args.gpus,
        sequence_conditions=args.sequence_conditions,
        benchmark_type=args.benchmark_type,
        min_rows=args.min_rows,
    )

    baseline: dict[tuple[str, str], float] = {}
    for row in raw_rows:
        if row["isl"] == int(baseline_isl) and row["osl"] == int(baseline_osl):
            baseline[(row["model"], row["gpu"])] = row["output_tok_s_mw_p50"]

    rows: list[dict[str, Any]] = []
    for row in raw_rows:
        base = baseline.get((row["model"], row["gpu"]))
        if base is None or base == 0:
            vs_baseline = ""
        elif row["isl"] == int(baseline_isl) and row["osl"] == int(baseline_osl):
            vs_baseline = "baseline"
        else:
            vs_baseline = f"{((row['output_tok_s_mw_p50'] / base) - 1) * 100:+.0f}%"
        rows.append(
            {
                "Model": row["model"],
                "GPU": row["gpu"],
                "ISL": row["isl"],
                "OSL": row["osl"],
                "Rows": row["row_count"],
                "Output p50 tok/s/MW": row["output_tok_s_mw_p50"],
                f"vs {args.baseline}": vs_baseline,
                "Output p10": row["output_tok_s_mw_p10"],
                "Output p90": row["output_tok_s_mw_p90"],
                "p99 TTFT p50 ms": row["p99_ttft_ms_p50"],
                "p99 TPOT p50 ms": row["p99_tpot_ms_p50"],
                "Main framework": row["main_framework"],
                "Main precision": row["main_precision"],
            }
        )
    print_table(rows, args.format)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    subparsers = parser.add_subparsers(dest="command", required=True)

    tables = subparsers.add_parser("tables", help="List available tables and views.")
    tables.add_argument("--format", choices=["md", "csv"], default="md")
    tables.set_defaults(func=command_tables)

    schema = subparsers.add_parser("schema", help="Show table or view columns.")
    schema.add_argument("table")
    schema.add_argument("--format", choices=["md", "csv"], default="md")
    schema.set_defaults(func=command_schema)

    sql = subparsers.add_parser("sql", help="Run a SQL SELECT query.")
    sql.add_argument("sql")
    sql.add_argument("--limit", type=int, default=100)
    sql.add_argument("--format", choices=["md", "csv"], default="md")
    sql.set_defaults(func=command_sql)

    gpu_summary = subparsers.add_parser(
        "gpu-summary", help="Summarize main-config GPU-comparable rows."
    )
    gpu_summary.add_argument("--models", default="")
    gpu_summary.add_argument("--gpus", default=DEFAULT_GPUS)
    gpu_summary.add_argument("--sequence-conditions", default="1024/1024")
    gpu_summary.add_argument("--benchmark-type", default="single_turn")
    gpu_summary.add_argument("--min-rows", type=int, default=10)
    gpu_summary.add_argument("--format", choices=["md", "csv"], default="md")
    gpu_summary.set_defaults(func=command_gpu_summary)

    isl_osl = subparsers.add_parser(
        "isl-osl", help="Compare output throughput across ISL/OSL conditions."
    )
    isl_osl.add_argument("--models", default="")
    isl_osl.add_argument("--gpus", default=DEFAULT_GPUS)
    isl_osl.add_argument("--sequence-conditions", default=DEFAULT_SEQUENCE_CONDITIONS)
    isl_osl.add_argument("--baseline", default="1024/1024")
    isl_osl.add_argument("--benchmark-type", default="single_turn")
    isl_osl.add_argument("--min-rows", type=int, default=10)
    isl_osl.add_argument("--format", choices=["md", "csv"], default="md")
    isl_osl.set_defaults(func=command_isl_osl)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    with connect(args.db) as conn:
        args.func(conn, args)


if __name__ == "__main__":
    main()
