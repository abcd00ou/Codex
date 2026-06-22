"""Build a local SQLite database from normalized InferenceX CSV exports."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NORM_DIR = ROOT / "data" / "inferencex" / "normalized"
DEFAULT_DB = ROOT / "data" / "inferencex" / "inferencex_benchmark.sqlite"

INT_RE = re.compile(r"^[+-]?\d+$")
REAL_RE = re.compile(
    r"^[+-]?(?:(?:\d+\.\d*)|(?:\.\d+)|(?:\d+))(?:[eE][+-]?\d+)?$"
)


def table_name(path: Path) -> str:
    name = path.stem
    if name.startswith("inferencex_"):
        name = name[len("inferencex_") :]
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


def quote_name(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def infer_type(values: list[str]) -> str:
    observed = [value.strip() for value in values if value.strip() != ""]
    if not observed:
        return "TEXT"
    if all(INT_RE.match(value) for value in observed):
        return "INTEGER"
    if all(REAL_RE.match(value) for value in observed):
        return "REAL"
    return "TEXT"


def coerce(value: str, sqlite_type: str) -> int | float | str | None:
    if value == "":
        return None
    if sqlite_type == "INTEGER":
        return int(value)
    if sqlite_type == "REAL":
        return float(value)
    return value


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def create_table(
    conn: sqlite3.Connection, name: str, headers: list[str], rows: list[dict[str, str]]
) -> int:
    if not headers:
        return 0

    column_types = {
        header: infer_type([row.get(header, "") for row in rows]) for header in headers
    }
    columns_sql = ", ".join(
        f"{quote_name(header)} {column_types[header]}" for header in headers
    )
    conn.execute(f"DROP TABLE IF EXISTS {quote_name(name)}")
    conn.execute(f"CREATE TABLE {quote_name(name)} ({columns_sql})")

    placeholders = ", ".join("?" for _ in headers)
    insert_sql = (
        f"INSERT INTO {quote_name(name)} "
        f"({', '.join(quote_name(header) for header in headers)}) VALUES ({placeholders})"
    )
    conn.executemany(
        insert_sql,
        [
            tuple(coerce(row.get(header, ""), column_types[header]) for header in headers)
            for row in rows
        ],
    )
    return len(rows)


def create_index_if_columns_exist(
    conn: sqlite3.Connection, table: str, index: str, columns: list[str]
) -> None:
    existing = {
        row[1] for row in conn.execute(f"PRAGMA table_info({quote_name(table)})").fetchall()
    }
    if not set(columns).issubset(existing):
        return
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS {quote_name(index)} ON {quote_name(table)} "
        f"({', '.join(quote_name(column) for column in columns)})"
    )


def create_views(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS v_main_benchmark_results;
        CREATE VIEW v_main_benchmark_results AS
        SELECT *
        FROM benchmark_results
        WHERE is_main_model_config = 'yes';

        DROP VIEW IF EXISTS v_gpu_comparable_main_profile;
        CREATE VIEW v_gpu_comparable_main_profile AS
        SELECT *
        FROM gpu_comparable_metric_profile
        WHERE is_main_model_config = 'yes';

        DROP VIEW IF EXISTS v_h200_b200_gb200_main_profile;
        CREATE VIEW v_h200_b200_gb200_main_profile AS
        SELECT *
        FROM gpu_comparable_metric_profile
        WHERE is_main_model_config = 'yes'
          AND lower(gpu) IN ('h200', 'b200', 'gb200');
        """
    )


def build_database(norm_dir: Path, db_path: Path) -> list[tuple[str, int]]:
    csv_paths = sorted(norm_dir.glob("inferencex_*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No normalized CSV files found in {norm_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    loaded: list[tuple[str, int]] = []
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        for path in csv_paths:
            headers, rows = read_csv(path)
            name = table_name(path)
            loaded.append((name, create_table(conn, name, headers, rows)))

        create_index_if_columns_exist(
            conn,
            "benchmark_results",
            "idx_benchmark_results_lookup",
            ["model", "gpu", "is_main_model_config", "isl", "osl", "framework", "precision"],
        )
        create_index_if_columns_exist(
            conn,
            "benchmark_results",
            "idx_benchmark_results_date",
            ["benchmark_date"],
        )
        create_index_if_columns_exist(
            conn,
            "gpu_comparable_metric_profile",
            "idx_gpu_profile_lookup",
            ["model", "gpu", "is_main_model_config", "isl", "osl"],
        )
        create_views(conn)
        conn.execute(
            "CREATE TABLE build_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.executemany(
            "INSERT INTO build_metadata (key, value) VALUES (?, ?)",
            [
                ("normalized_dir", str(norm_dir)),
                ("source_csv_count", str(len(csv_paths))),
            ],
        )
        conn.commit()
    return loaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build data/inferencex/inferencex_benchmark.sqlite from normalized InferenceX CSVs."
    )
    parser.add_argument("--normalized-dir", type=Path, default=NORM_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    loaded = build_database(args.normalized_dir, args.db)
    total_rows = sum(row_count for _, row_count in loaded)
    print(f"Created {args.db}")
    print(f"Loaded {len(loaded)} tables / {total_rows:,} rows")
    for name, row_count in loaded:
        print(f"- {name}: {row_count:,}")


if __name__ == "__main__":
    main()
