from __future__ import annotations

import html
import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DB_PATH = Path("/Users/idongseong/Claude/agents/data/dba/financials.db")
MASTER_PATH = Path("/Users/idongseong/Downloads/company_master.xlsx")

OUT_HTML = ROOT / "financial_lead_lag_report.html"
OUT_SECTION_QUARTERLY = ROOT / "section_financial_quarterly_summary.csv"
OUT_COVERAGE = ROOT / "financial_data_coverage.csv"
OUT_DATA_DRIVEN_EDGE_CORR = ROOT / "data_driven_edge_lag_correlations.csv"
OUT_DATA_DRIVEN_EDGE_BEST = ROOT / "data_driven_edge_best_signals.csv"

OUTPUT_FILENAMES = {
    "html": "financial_lead_lag_report.html",
    "section_quarterly": "section_financial_quarterly_summary.csv",
    "coverage": "financial_data_coverage.csv",
    "data_edge_corr": "data_driven/data_driven_edge_lag_correlations.csv",
    "data_edge_best": "data_driven/data_driven_edge_best_signals.csv",
}

ANALYSIS_START_QUARTER = "2016-Q1"
HYPERSCALER_SECTION = "Hyperscalers"
LAGS = list(range(-4, 9))
MIN_CALC_OBS = 8
MIN_REPORT_OBS = 12
MIN_MAP_OBS = 16
DATA_DRIVEN_MIN_ABS_CORR = 0.45
DATA_DRIVEN_MAX_MAP_EDGES = 42


FINANCIAL_VALUE_METRICS = {
    "revenue_usd_m": "Revenue",
    "gross_profit_usd_m": "Gross profit",
    "cost_of_revenue_usd_m": "Cost of revenue",
    "operating_income_usd_m": "Operating income",
    "net_income_usd_m": "Net income",
    "inventory_usd_m": "Inventory",
}

METRICS = FINANCIAL_VALUE_METRICS

DATA_DRIVEN_LAYER_CONFIGS = [
    {
        "analysis_layer": "Procurement spend -> Supplier revenue",
        "source_metric": "Cost of revenue",
        "source_options": ["cost_of_revenue_usd_m_yoy_current_ratio"],
        "target_metric": "Revenue",
        "target_col": "revenue_usd_m_yoy_current_ratio",
        "target_transform": "YoY current-base ratio",
        "allow_same_section": False,
    },
]


NODE_POSITIONS = {
    "Hyperscalers": (70, 210),
    "Cooling": (310, 70),
    "Energy": (310, 145),
    "Server OEM": (310, 220),
    "Server ODM": (310, 295),
    "Server EMS": (310, 370),
    "Server Networking": (310, 445),
    "AI Chip": (570, 190),
    "CPU": (570, 285),
    "DRAM": (810, 165),
    "NAND": (810, 275),
    "OSAT / packiging": (810, 385),
    "foundry": (810, 485),
    "HW equipment": (1070, 175),
    "SW equipment": (1070, 255),
    "meterier": (1070, 335),
    "components": (1070, 415),
}


def esc(value: object) -> str:
    return html.escape("" if pd.isna(value) else str(value))


def num(value: float, digits: int = 2) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:,.{digits}f}"


def pct(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{value * 100:.{digits}f}%"


def norm_ticker(ticker: object) -> str:
    if pd.isna(ticker):
        return ""
    t = str(ticker).strip().upper()
    replacements = {
        ".KS": "KRX:",
        ".KQ": "KRX:",
        ".TW": "TPE:",
        ".T": "TYO:",
        ".PA": "EPA:",
        ".AS": "AMS:",
        ".DE": "ETR:",
        ".SW": "SWX:",
        ".HK": "HKG:",
        ".SS": "SHA:",
        ".SZ": "SHE:",
    }
    for suffix, prefix in replacements.items():
        if t.endswith(suffix):
            return prefix + t[: -len(suffix)]
    return t


def quarter_period(value: object) -> pd.Period | pd.NaT:
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip().upper().replace(" ", "")
    if "-Q" in text:
        year, quarter = text.split("-Q", 1)
    elif "Q" in text:
        year, quarter = text.split("Q", 1)
    else:
        return pd.NaT
    try:
        return pd.Period(f"{int(year)}Q{int(quarter)}", freq="Q")
    except Exception:
        return pd.NaT


def resolve_master_columns(master: pd.DataFrame) -> pd.DataFrame:
    section_col = "section" if "section" in master.columns else "group_3"
    company_col = "companyname" if "companyname" in master.columns else "company_name"
    required = [section_col, company_col, "ticker"]
    missing = [col for col in required if col not in master.columns]
    if missing:
        raise ValueError(f"company_master.xlsx missing required columns: {missing}")
    return master.rename(columns={section_col: "section", company_col: "company_name"}).copy()


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    master = resolve_master_columns(pd.read_excel(MASTER_PATH))
    master["section"] = master["section"].astype(str).str.strip()
    master["company_name"] = master["company_name"].astype(str).str.strip()
    master["ticker_norm"] = master["ticker"].map(norm_ticker)

    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query("select ticker, name, exchange, segments, hq_country from companies", conn)
        quarterly = pd.read_sql_query("select * from quarterly_financials", conn)

    db_tickers = set(companies["ticker"])
    suffix_lookup: dict[str, str] = {}
    for db_ticker in db_tickers:
        suffix_lookup.setdefault(db_ticker.split(":")[-1].upper(), db_ticker)

    def match_db_ticker(row: pd.Series) -> str | None:
        normalized = row["ticker_norm"]
        raw = str(row["ticker"]).strip().upper()
        if normalized in db_tickers:
            return normalized
        return suffix_lookup.get(raw)

    master["db_ticker"] = master.apply(match_db_ticker, axis=1)
    matched = master.dropna(subset=["db_ticker"]).copy()

    quarterly["quarter_period"] = quarterly["calendar_quarter"].map(quarter_period)
    quarterly = quarterly.dropna(subset=["quarter_period"])
    quarterly = quarterly[quarterly["quarter_period"] >= quarter_period(ANALYSIS_START_QUARTER)]
    financials = quarterly.merge(
        matched[["db_ticker", "section", "company_name", "ticker"]],
        left_on="ticker",
        right_on="db_ticker",
        how="inner",
        suffixes=("_db", "_master"),
    )
    financials["cost_of_revenue_usd_m"] = pd.to_numeric(financials["revenue_usd_m"], errors="coerce") - pd.to_numeric(
        financials["gross_profit_usd_m"], errors="coerce"
    )
    return matched, financials


EXTERNAL_FINANCIAL_COLUMN_ALIASES = {
    "company_name": ["companyname", "company_name", "company", "name", "회사명"],
    "section": ["section", "group", "group_3", "섹션"],
    "fs_item": ["fs_item", "item", "financial_item", "metric", "account", "계정"],
    "date": ["date", "period", "quarter", "period_end_date", "날짜"],
    "value": ["value", "amount", "usd_m", "financial_value", "값"],
}

EXTERNAL_FS_ITEM_MAP = {
    "capex": "capex_usd_m",
    "capital_expenditure": "capex_usd_m",
    "capital expenditure": "capex_usd_m",
    "capital expenditures": "capex_usd_m",
    "revenue": "revenue_usd_m",
    "sales": "revenue_usd_m",
    "매출": "revenue_usd_m",
    "gross_profit": "gross_profit_usd_m",
    "gross profit": "gross_profit_usd_m",
    "cost_of_revenue": "cost_of_revenue_usd_m",
    "cost of revenue": "cost_of_revenue_usd_m",
    "cost_of_sales": "cost_of_revenue_usd_m",
    "cost of sales": "cost_of_revenue_usd_m",
    "cogs": "cost_of_revenue_usd_m",
    "operating_income": "operating_income_usd_m",
    "operating income": "operating_income_usd_m",
    "op_income": "operating_income_usd_m",
    "net_income": "net_income_usd_m",
    "net income": "net_income_usd_m",
    "inventory": "inventory_usd_m",
    "inventories": "inventory_usd_m",
    "재고": "inventory_usd_m",
}


def _normalized_column_lookup(df: pd.DataFrame) -> dict[str, str]:
    return {str(col).strip().lower().replace("_", " "): col for col in df.columns}


def _resolve_external_column(df: pd.DataFrame, field: str) -> str:
    lookup = _normalized_column_lookup(df)
    for alias in EXTERNAL_FINANCIAL_COLUMN_ALIASES[field]:
        key = alias.strip().lower().replace("_", " ")
        if key in lookup:
            return lookup[key]
    expected = ", ".join(EXTERNAL_FINANCIAL_COLUMN_ALIASES[field])
    raise ValueError(f"Missing required dataframe column for {field}. Expected one of: {expected}")


def normalize_fs_item(value: object) -> str | None:
    if pd.isna(value):
        return None
    key = str(value).strip().lower().replace("-", "_")
    key = " ".join(key.replace("_", " ").split())
    if key in EXTERNAL_FS_ITEM_MAP:
        return EXTERNAL_FS_ITEM_MAP[key]
    compact = key.replace(" ", "_")
    return EXTERNAL_FS_ITEM_MAP.get(compact)


def company_key(value: object) -> str:
    text = "" if pd.isna(value) else str(value).strip().lower()
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text)
    return "_".join(part for part in cleaned.split("_") if part) or "unknown_company"


def parse_external_quarter(value: object) -> pd.Period | pd.NaT:
    direct = quarter_period(value)
    if not pd.isna(direct):
        return direct
    date = pd.to_datetime(value, errors="coerce")
    if pd.isna(date):
        return pd.NaT
    return pd.Period(date, freq="Q")


def normalize_financial_dataframe(
    raw: pd.DataFrame,
    analysis_start_quarter: str | None = "2012-Q1",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert a long financial DataFrame into the internal matched/financials schema.

    Required logical columns are companyname, section, fs_item, date, and value.
    fs_item should include at least capex and revenue. Optional recognized items are
    gross_profit, cost_of_revenue, inventories, operating_income, and net_income.
    """
    if raw.empty:
        raise ValueError("Input dataframe is empty.")

    company_col = _resolve_external_column(raw, "company_name")
    section_col = _resolve_external_column(raw, "section")
    item_col = _resolve_external_column(raw, "fs_item")
    date_col = _resolve_external_column(raw, "date")
    value_col = _resolve_external_column(raw, "value")

    data = raw[[company_col, section_col, item_col, date_col, value_col]].copy()
    data.columns = ["company_name", "section", "fs_item", "date", "value"]
    data["company_name"] = data["company_name"].astype(str).str.strip()
    data["section"] = data["section"].astype(str).str.strip()
    data["metric_col"] = data["fs_item"].map(normalize_fs_item)
    data["quarter_period"] = data["date"].map(parse_external_quarter)
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["company_name", "section", "metric_col", "quarter_period", "value"])
    if analysis_start_quarter:
        data = data[data["quarter_period"] >= quarter_period(analysis_start_quarter)]
    if data.empty:
        raise ValueError("No valid financial rows remain after cleaning and date filtering.")

    data["db_ticker"] = data["section"].map(company_key) + "__" + data["company_name"].map(company_key)
    data["ticker"] = data["db_ticker"]
    pivot = (
        data.pivot_table(
            index=["section", "company_name", "db_ticker", "ticker", "quarter_period"],
            columns="metric_col",
            values="value",
            aggfunc="sum",
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for col in ["capex_usd_m", *FINANCIAL_VALUE_METRICS.keys()]:
        if col not in pivot.columns:
            pivot[col] = np.nan
    if pivot["cost_of_revenue_usd_m"].isna().any():
        derived_cost = pd.to_numeric(pivot["revenue_usd_m"], errors="coerce") - pd.to_numeric(
            pivot["gross_profit_usd_m"], errors="coerce"
        )
        pivot["cost_of_revenue_usd_m"] = pivot["cost_of_revenue_usd_m"].fillna(derived_cost)
    pivot["calendar_quarter"] = pivot["quarter_period"].astype(str).str.replace("Q", "-Q", regex=False)

    matched = (
        pivot[["section", "company_name", "db_ticker", "ticker"]]
        .drop_duplicates()
        .sort_values(["section", "company_name"])
        .reset_index(drop=True)
    )
    financials = pivot.sort_values(["section", "company_name", "quarter_period"]).reset_index(drop=True)
    return matched, financials


def yoy_current_ratio(series: pd.Series) -> pd.Series:
    previous = series.shift(4)
    out = (series - previous) / series
    out[series == 0] = np.nan
    return out.replace([np.inf, -np.inf], np.nan)


def aggregate_section_quarterly(financials: pd.DataFrame) -> pd.DataFrame:
    data = financials.copy()
    data["capex_investment_usd_m"] = pd.to_numeric(data["capex_usd_m"], errors="coerce").abs()
    if "cost_of_revenue_usd_m" not in data.columns:
        data["cost_of_revenue_usd_m"] = np.nan
    derived_cost = pd.to_numeric(data.get("revenue_usd_m"), errors="coerce") - pd.to_numeric(
        data.get("gross_profit_usd_m"), errors="coerce"
    )
    data["cost_of_revenue_usd_m"] = pd.to_numeric(data["cost_of_revenue_usd_m"], errors="coerce").fillna(derived_cost)
    for col in list(FINANCIAL_VALUE_METRICS):
        if col not in data.columns:
            data[col] = np.nan
        data[col] = pd.to_numeric(data[col], errors="coerce")

    agg_spec: dict[str, tuple[str, str]] = {
        "capex_investment_usd_m": ("capex_investment_usd_m", "sum"),
        "capex_valid_companies": ("capex_investment_usd_m", lambda s: int(s.notna().sum())),
        "total_companies": ("db_ticker", "nunique"),
    }
    for metric in FINANCIAL_VALUE_METRICS:
        agg_spec[metric] = (metric, "sum")
        agg_spec[f"{metric}_valid_companies"] = (metric, lambda s: int(s.notna().sum()))

    quarterly = (
        data.groupby(["section", "quarter_period"], as_index=False)
        .agg(**agg_spec)
        .sort_values(["section", "quarter_period"])
    )
    quarterly["calendar_quarter"] = quarterly["quarter_period"].astype(str).str.replace("Q", "-Q", regex=False)

    transformed = []
    for section, sub in quarterly.groupby("section", sort=False):
        sub = sub.sort_values("quarter_period").copy()
        sub["capex_yoy_current_ratio"] = yoy_current_ratio(sub["capex_investment_usd_m"])
        for metric in FINANCIAL_VALUE_METRICS:
            sub[f"{metric}_yoy_current_ratio"] = yoy_current_ratio(sub[metric])
        transformed.append(sub)
    return pd.concat(transformed, ignore_index=True)


def coverage_table(financials: pd.DataFrame, section_quarterly: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    section_tickers = matched.groupby("section").agg(master_companies=("db_ticker", "nunique")).reset_index()
    observed = (
        financials.groupby("section")
        .agg(
            financial_rows=("db_ticker", "size"),
            observed_companies=("db_ticker", "nunique"),
            first_quarter=("quarter_period", "min"),
            last_quarter=("quarter_period", "max"),
            revenue_rows=("revenue_usd_m", lambda s: int(s.notna().sum())),
            cost_of_revenue_rows=("cost_of_revenue_usd_m", lambda s: int(s.notna().sum())),
            capex_rows=("capex_usd_m", lambda s: int(s.notna().sum())),
            inventory_rows=("inventory_usd_m", lambda s: int(s.notna().sum())),
            operating_income_rows=("operating_income_usd_m", lambda s: int(s.notna().sum())),
            net_income_rows=("net_income_usd_m", lambda s: int(s.notna().sum())),
        )
        .reset_index()
    )
    quarter_counts = (
        section_quarterly.groupby("section")
        .agg(
            quarters=("quarter_period", "nunique"),
            revenue_yoy_obs=("revenue_usd_m_yoy_current_ratio", lambda s: int(s.notna().sum())),
            cost_of_revenue_yoy_obs=("cost_of_revenue_usd_m_yoy_current_ratio", lambda s: int(s.notna().sum())),
            capex_yoy_obs=("capex_yoy_current_ratio", lambda s: int(s.notna().sum())),
            inventory_yoy_obs=("inventory_usd_m_yoy_current_ratio", lambda s: int(s.notna().sum())),
            operating_income_yoy_obs=("operating_income_usd_m_yoy_current_ratio", lambda s: int(s.notna().sum())),
            net_income_yoy_obs=("net_income_usd_m_yoy_current_ratio", lambda s: int(s.notna().sum())),
        )
        .reset_index()
    )
    out = section_tickers.merge(observed, on="section", how="left").merge(quarter_counts, on="section", how="left")
    out["first_quarter"] = out["first_quarter"].astype(str).str.replace("Q", "-Q", regex=False)
    out["last_quarter"] = out["last_quarter"].astype(str).str.replace("Q", "-Q", regex=False)
    return out.sort_values(["master_companies", "section"], ascending=[False, True])


def data_driven_lag_correlations(section_quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    indexed = {
        section: sub.set_index("quarter_period").sort_index()
        for section, sub in section_quarterly.groupby("section")
    }
    sections = sorted(indexed)
    rows = []
    for layer in DATA_DRIVEN_LAYER_CONFIGS:
        for source in sections:
            source_col = choose_source_transform(indexed[source], layer["source_options"])
            if source_col is None:
                continue
            min_obs = MIN_CALC_OBS
            source_series = indexed[source][source_col].rename("source_value")
            for target in sections:
                if source == target and not layer["allow_same_section"]:
                    continue
                target_col = str(layer["target_col"])
                if target_col not in indexed[target].columns:
                    continue
                target_series = indexed[target][target_col].rename("target_value")
                for lag in LAGS:
                    aligned = pd.concat([source_series, target_series.shift(-lag)], axis=1).dropna()
                    if len(aligned) < min_obs:
                        corr = beta = np.nan
                        status = "insufficient_observations"
                    else:
                        corr = float(aligned["source_value"].corr(aligned["target_value"]))
                        variance = float(aligned["source_value"].var())
                        beta = float(aligned["source_value"].cov(aligned["target_value"]) / variance) if variance else np.nan
                        status = transform_status(source_col, len(aligned))
                    rows.append(
                        {
                            "analysis_layer": layer["analysis_layer"],
                            "source_section": source,
                            "target_section": target,
                            "source_metric": layer["source_metric"],
                            "source_transform": source_col,
                            "target_metric": layer["target_metric"],
                            "target_transform": layer["target_transform"],
                            "target_transform_col": target_col,
                            "lag_quarters": lag,
                            "timing": timing_label(lag),
                            "lag_interpretation": metric_lag_label(source, target, layer["source_metric"], layer["target_metric"], lag),
                            "observations": int(len(aligned)),
                            "corr": corr,
                            "r_squared": corr * corr if not pd.isna(corr) else np.nan,
                            "beta_target_per_1_source": beta,
                            "status": status,
                        }
                    )
    corr_df = pd.DataFrame(rows)
    best_rows = []
    for (layer_name, source, target, source_metric, target_metric), sub in corr_df.groupby(
        ["analysis_layer", "source_section", "target_section", "source_metric", "target_metric"]
    ):
        valid = sub.dropna(subset=["corr"])
        if valid.empty:
            continue
        positive = valid[valid["corr"] > 0]
        if positive.empty:
            continue
        best = positive.loc[positive["corr"].idxmax()]
        best_abs = valid.loc[valid["corr"].abs().idxmax()]
        obs = int(best["observations"])
        corr = float(best["corr"])
        best_rows.append(
            {
                "analysis_layer": layer_name,
                "source_section": source,
                "target_section": target,
                "source_metric": source_metric,
                "source_transform": best["source_transform"],
                "target_metric": target_metric,
                "target_transform": best["target_transform"],
                "target_transform_col": best["target_transform_col"],
                "best_lag_quarters": int(best["lag_quarters"]),
                "timing": timing_label(int(best["lag_quarters"])),
                "best_corr": corr,
                "best_observations": obs,
                "best_r_squared": corr * corr,
                "best_abs_lag_quarters": int(best_abs["lag_quarters"]),
                "best_abs_corr": float(best_abs["corr"]),
                "status": best["status"],
                "signal_class": classify_data_driven_edge(corr, obs, best["status"]),
                "map_eligible": is_map_eligible(corr, obs, best["status"]),
                "interpretation": data_driven_note(best, best_abs),
            }
        )
    best_df = pd.DataFrame(best_rows)
    if best_df.empty:
        return corr_df, pd.DataFrame(
            columns=[
                "analysis_layer",
                "source_section",
                "target_section",
                "source_metric",
                "source_transform",
                "target_metric",
                "target_transform",
                "target_transform_col",
                "best_lag_quarters",
                "timing",
                "best_corr",
                "best_observations",
                "best_r_squared",
                "best_abs_lag_quarters",
                "best_abs_corr",
                "status",
                "signal_class",
                "map_eligible",
                "interpretation",
            ]
        )
    rank_order = {
        "strong": 0,
        "moderate": 1,
        "weak": 2,
        "exploratory low-n": 3,
        "very weak": 4,
    }
    best_df["_order"] = best_df["signal_class"].map(rank_order).fillna(9)
    best_df = best_df.sort_values(["map_eligible", "_order", "best_corr", "best_observations"], ascending=[False, True, False, False]).drop(columns=["_order"])
    return corr_df, best_df


def timing_label(lag: int) -> str:
    if lag > 0:
        return "source leads"
    if lag < 0:
        return "target leads"
    return "synchronous"


def choose_source_transform(section_df: pd.DataFrame, options: list[str]) -> str | None:
    for col in options:
        if col in section_df.columns and int(section_df[col].notna().sum()) >= MIN_CALC_OBS:
            return col
    return None


def transform_status(source_col: str, observations: int) -> str:
    if observations < MIN_REPORT_OBS:
        return "exploratory_low_n"
    return "ok"


def metric_lag_label(source: str, target: str, source_metric: str, target_metric: str, lag: int) -> str:
    if lag > 0:
        return f"{source} {source_metric} leads {target} {target_metric} by {lag} quarter(s)"
    if lag < 0:
        return f"{target} {target_metric} leads {source} {source_metric} by {abs(lag)} quarter(s)"
    return f"{source} {source_metric} and {target} {target_metric} move in the same quarter"


def classify_data_driven_edge(corr: float, observations: int, status: str) -> str:
    if observations < MIN_REPORT_OBS or "low_n" in str(status):
        return "exploratory low-n"
    if corr >= 0.65:
        return "strong"
    if corr >= 0.50:
        return "moderate"
    if corr >= DATA_DRIVEN_MIN_ABS_CORR:
        return "weak"
    return "very weak"


def is_map_eligible(corr: float, observations: int, status: str) -> bool:
    return observations >= MIN_MAP_OBS and "low_n" not in str(status) and corr >= DATA_DRIVEN_MIN_ABS_CORR


def data_driven_note(best: pd.Series, best_abs: pd.Series) -> str:
    lag = int(best["lag_quarters"])
    corr = float(best["corr"])
    obs = int(best["observations"])
    timing = timing_label(lag)
    low_n = " Low-n exploratory result." if obs < MIN_REPORT_OBS or "low_n" in str(best["status"]) else ""
    return (
        f"{timing}; best positive lag {lag:+d}Q, corr {corr:.2f}, n={obs}.{low_n} "
        f"Strongest absolute relation is lag {int(best_abs['lag_quarters']):+d}Q, corr {float(best_abs['corr']):.2f}."
    )


def style_corr(value: float) -> str:
    if pd.isna(value):
        return "background:#f3f4f6;color:#9ca3af"
    clipped = max(-1.0, min(1.0, value))
    if clipped >= 0:
        alpha = 0.10 + 0.75 * clipped
        return f"background:rgba(20,120,90,{alpha:.2f});color:#06261d"
    alpha = 0.10 + 0.75 * abs(clipped)
    return f"background:rgba(176,55,55,{alpha:.2f});color:#2a0909"


def heatmap_html(corr_df: pd.DataFrame, metric: str = "revenue_usd_m") -> str:
    sub = corr_df[corr_df["target_metric"] == metric].copy()
    pivot = sub.pivot(index="section", columns="lag_quarters", values="corr")
    rows = []
    for section, values in pivot.sort_index().iterrows():
        cells = [f"<th>{esc(section)}</th>"]
        for lag in LAGS:
            value = values.get(lag, np.nan)
            cells.append(f'<td style="{style_corr(value)}">{num(value, 2)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th>{lag:+d}Q</th>" for lag in LAGS)
    return f"""
    <table class="heatmap">
      <thead><tr><th>Section</th>{head}</tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    """


def edge_stroke(edge: pd.Series) -> tuple[str, float, str]:
    if edge.get("signal_class") == "exploratory low-n":
        return "#6b7280", 2.0, "2 4"
    corr = edge.get("best_forward_corr")
    if pd.isna(corr):
        return "#9aa4a0", 1.2, "5 5"
    corr = float(corr)
    if corr >= 0.45:
        return "#087f5b", 1.8 + 5.0 * min(corr, 0.85), ""
    if corr >= 0.25:
        return "#9a6700", 1.6 + 3.0 * corr, "7 4"
    return "#b03737", 1.2, "3 5"


def data_driven_map_edges(edge_best: pd.DataFrame) -> pd.DataFrame:
    if edge_best.empty:
        return edge_best
    eligible = edge_best[edge_best["map_eligible"]].copy()
    if eligible.empty:
        eligible = edge_best.dropna(subset=["best_corr"]).copy()
    eligible = eligible.sort_values(["best_corr", "best_observations"], ascending=[False, False])
    selected = []
    target_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for _, row in eligible.iterrows():
        source, target = str(row["source_section"]), str(row["target_section"])
        if source == target:
            continue
        if target_counts.get(target, 0) >= 3 or source_counts.get(source, 0) >= 4:
            continue
        selected.append(row)
        target_counts[target] = target_counts.get(target, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1
        if len(selected) >= DATA_DRIVEN_MAX_MAP_EDGES:
            break
    return pd.DataFrame(selected)


def data_driven_chain_map_svg(edge_best: pd.DataFrame) -> str:
    edges = data_driven_map_edges(edge_best)
    if edges.empty:
        return '<p class="note">No data-driven edges passed the map filter.</p>'
    return section_influence_flow_svg(edges)


def section_influence_flow_svg(edges: pd.DataFrame) -> str:
    selected = edges.sort_values(["best_corr", "best_observations"], ascending=[False, False]).head(DATA_DRIVEN_MAX_MAP_EDGES).copy()
    buyers = sorted(selected["source_section"].astype(str).unique(), key=node_sort_key)
    suppliers = sorted(selected["target_section"].astype(str).unique(), key=node_sort_key)
    cell_w = 128
    cell_h = 48
    left = 208
    top = 108
    matrix_w = cell_w * len(suppliers)
    matrix_h = cell_h * len(buyers)
    width = max(1500, left + matrix_w + 58)
    board_top = top + matrix_h + 92
    lag_col_w = 150
    lag_cols = len(LAGS)
    board_w = lag_col_w * lag_cols
    board_h = 315
    height = board_top + board_h + 48

    edge_lookup = {
        (str(row["source_section"]), str(row["target_section"])): row
        for _, row in selected.iterrows()
    }
    matrix_parts = []
    for j, supplier in enumerate(suppliers):
        x = left + j * cell_w + cell_w / 2
        matrix_parts.append(
            f'<text x="{x:.1f}" y="74" text-anchor="middle" class="col-label">{esc(short_label(supplier))}</text>'
        )
    for i, buyer in enumerate(buyers):
        y = top + i * cell_h + cell_h / 2
        matrix_parts.append(f'<text x="{left-14}" y="{y+4:.1f}" text-anchor="end" class="row-label">{esc(buyer)}</text>')
        for j, supplier in enumerate(suppliers):
            x0 = left + j * cell_w
            y0 = top + i * cell_h
            edge = edge_lookup.get((buyer, supplier))
            if edge is None:
                matrix_parts.append(f'<rect x="{x0}" y="{y0}" width="{cell_w}" height="{cell_h}" class="empty-cell"/>')
                continue
            color, opacity = lag_cell_color(edge)
            lag = int(edge["best_lag_quarters"])
            corr = float(edge["best_corr"])
            matrix_parts.append(
                f'<rect x="{x0}" y="{y0}" width="{cell_w}" height="{cell_h}" fill="{color}" opacity="{opacity:.2f}" stroke="#ffffff"/>'
            )
            matrix_parts.append(
                f'<text x="{x0+cell_w/2:.1f}" y="{y0+20:.1f}" text-anchor="middle" class="cell-main">t{lag:+d}Q</text>'
            )
            matrix_parts.append(
                f'<text x="{x0+cell_w/2:.1f}" y="{y0+36:.1f}" text-anchor="middle" class="cell-sub">r={corr:.2f} · n={int(edge["best_observations"])}</text>'
            )

    board_parts = []
    board_left = max(58, (width - board_w) / 2)
    for idx, lag in enumerate(LAGS):
        x0 = board_left + idx * lag_col_w
        fill = "#eef7f2" if lag > 0 else "#eef4ff" if lag == 0 else "#fff0ed"
        board_parts.append(f'<rect x="{x0:.1f}" y="{board_top}" width="{lag_col_w-8}" height="{board_h}" rx="8" fill="{fill}" stroke="#d8ded9"/>')
        board_parts.append(f'<text x="{x0+(lag_col_w-8)/2:.1f}" y="{board_top+24}" text-anchor="middle" class="lag-title">t{lag:+d}Q</text>')
        sub = selected[selected["best_lag_quarters"] == lag].sort_values(["best_corr", "best_observations"], ascending=[False, False]).head(4)
        for k, (_, edge) in enumerate(sub.iterrows()):
            y = board_top + 48 + k * 62
            buyer = short_label(str(edge["source_section"]), 15)
            supplier = short_label(str(edge["target_section"]), 15)
            color, opacity = lag_cell_color(edge)
            board_parts.append(
                f'<rect x="{x0+8:.1f}" y="{y:.1f}" width="{lag_col_w-24}" height="50" rx="7" fill="#ffffff" stroke="{color}" opacity="0.96"/>'
            )
            board_parts.append(f'<text x="{x0+16:.1f}" y="{y+18:.1f}" class="flow-card-main">{esc(buyer)} →</text>')
            board_parts.append(f'<text x="{x0+16:.1f}" y="{y+34:.1f}" class="flow-card-main">{esc(supplier)}</text>')
            board_parts.append(f'<text x="{x0+16:.1f}" y="{y+46:.1f}" class="flow-card-sub">r={float(edge["best_corr"]):.2f}, n={int(edge["best_observations"])}</text>')

    return f"""
    <svg viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="Section influence matrix and quarter lag flow board">
      <style>
        .map-bg {{ fill:#fbfcfb; }}
        .title {{ font-size:18px; font-weight:750; fill:#17211c; }}
        .subtitle {{ font-size:12px; fill:#68766e; }}
        .row-label, .col-label {{ font-size:12px; fill:#17211c; font-weight:650; }}
        .empty-cell {{ fill:#f3f5f3; stroke:#ffffff; }}
        .cell-main {{ font-size:14px; fill:#102018; font-weight:750; }}
        .cell-sub {{ font-size:10px; fill:#39473f; font-weight:650; }}
        .lag-title {{ font-size:13px; fill:#17211c; font-weight:750; }}
        .flow-card-main {{ font-size:11px; fill:#17211c; font-weight:700; }}
        .flow-card-sub {{ font-size:9px; fill:#68766e; font-weight:650; }}
        .legend text {{ font-size:12px; fill:#39473f; font-weight:650; }}
      </style>
      <rect class="map-bg" x="0" y="0" width="{width:.0f}" height="{height:.0f}"/>
      <text x="24" y="34" class="title">Section-to-section influence by quarter lag</text>
      <text x="24" y="56" class="subtitle">Rows are buyer cost-of-revenue sections. Columns are supplier revenue sections. Cell text shows best lag, correlation, and observations.</text>
      <g class="legend">
        <rect x="24" y="76" width="14" height="14" fill="#087f5b" opacity="0.65"/><text x="44" y="88">buyer cost leads supplier revenue</text>
        <rect x="258" y="76" width="14" height="14" fill="#2563eb" opacity="0.65"/><text x="278" y="88">same-quarter</text>
        <rect x="390" y="76" width="14" height="14" fill="#b03737" opacity="0.65"/><text x="410" y="88">supplier revenue leads buyer cost</text>
      </g>
      {''.join(matrix_parts)}
      <text x="24" y="{board_top-32}" class="title">Quarter flow board</text>
      <text x="24" y="{board_top-12}" class="subtitle">Edges are grouped by the quarter where supplier revenue is most coupled with buyer cost at t+0Q.</text>
      {''.join(board_parts)}
    </svg>
    """


def lag_cell_color(edge: pd.Series) -> tuple[str, float]:
    corr = 0.0 if pd.isna(edge.get("best_corr")) else min(float(edge["best_corr"]), 1.0)
    opacity = 0.32 + 0.58 * max(corr, DATA_DRIVEN_MIN_ABS_CORR)
    timing = edge.get("timing")
    if timing == "target leads":
        return "#b03737", opacity
    if timing == "synchronous":
        return "#2563eb", opacity
    return "#087f5b", opacity


def short_label(value: str, max_len: int = 16) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 1] + "…"


def money_flow_lag_timeline_svg(edges: pd.DataFrame) -> str:
    rows = edges.sort_values(["best_corr", "best_observations"], ascending=[False, False]).head(DATA_DRIVEN_MAX_MAP_EDGES)
    width = 2300
    left = 460
    right = 110
    top = 122
    row_h = 66
    bottom = 72
    height = top + bottom + row_h * len(rows)
    chart_w = width - left - right
    lag_min, lag_max = min(LAGS), max(LAGS)
    lag_span = lag_max - lag_min

    def x_for_lag(lag: int | float) -> float:
        return left + (float(lag) - lag_min) / lag_span * chart_w

    axis_parts = []
    for lag in LAGS:
        x = x_for_lag(lag)
        cls = "zero-tick" if lag == 0 else "tick"
        axis_parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="72" y2="{height-46}" class="{cls}"/>')
        axis_parts.append(f'<text x="{x:.1f}" y="52" text-anchor="middle" class="axis-label">t{lag:+d}Q</text>')

    edge_parts = []
    node_parts = []
    label_parts = []
    buyer_x = x_for_lag(0)
    for idx, (_, edge) in enumerate(rows.iterrows()):
        y = top + idx * row_h
        lag = int(edge["best_lag_quarters"])
        supplier_x = x_for_lag(lag)
        color, stroke_width, dash = money_flow_edge_stroke(edge)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        source = str(edge["source_section"])
        target = str(edge["target_section"])
        timing = edge_timing_label(edge)
        direction = 1 if supplier_x >= buyer_x else -1
        label_x = max(36, min(left - 28, 34 + len(f"{source} cost -> {target} revenue") * 4.3))
        edge_y = y + ((idx % 3) - 1) * 7
        c1 = buyer_x + direction * 155
        c2 = supplier_x - direction * 155
        path = f"M{buyer_x:.1f},{edge_y:.1f} C{c1:.1f},{edge_y-26:.1f} {c2:.1f},{edge_y+26:.1f} {supplier_x:.1f},{edge_y:.1f}"
        edge_parts.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{stroke_width:.1f}"{dash_attr} marker-end="url(#arrow_lag)" opacity="0.78"/>'
        )
        label_parts.append(f'<text x="24" y="{y-8}" class="row-title">{esc(source)} cost → {esc(target)} revenue</text>')
        label_parts.append(
            f'<text x="24" y="{y+12}" class="row-meta">r={num(edge["best_corr"], 2)} · n={int(edge["best_observations"])} · {esc(edge["signal_class"])}</text>'
        )
        node_parts.append(
            f'<g class="flow-node"><circle cx="{buyer_x:.1f}" cy="{edge_y:.1f}" r="9" class="buyer-dot"/><text x="{buyer_x:.1f}" y="{edge_y-15:.1f}" text-anchor="middle">cost</text></g>'
        )
        node_parts.append(
            f'<g class="flow-node"><circle cx="{supplier_x:.1f}" cy="{edge_y:.1f}" r="9" class="supplier-dot"/><text x="{supplier_x:.1f}" y="{edge_y+25:.1f}" text-anchor="middle">rev</text></g>'
        )
        tag_x = max(left + 48, min(width - right - 48, supplier_x))
        tag_y = max(82, min(height - 34, edge_y - 21 if idx % 2 == 0 else edge_y + 31))
        label_parts.append(
            f'<g class="edge-tag"><rect x="{tag_x-44:.1f}" y="{tag_y-14:.1f}" width="88" height="22" rx="11"/><text x="{tag_x:.1f}" y="{tag_y+1:.1f}" text-anchor="middle">{esc(timing)}</text></g>'
        )

    return f"""
    <svg viewBox="0 0 {width} {height}" role="img" aria-label="Organic quarter lag flow for buyer cost to supplier revenue">
      <defs>
        <marker id="arrow_lag" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L8,3 z" fill="#50615a"/>
        </marker>
      </defs>
      <style>
        .map-bg {{ fill:#fbfcfb; }}
        .tick {{ stroke:#e0e6e2; stroke-width:1; }}
        .zero-tick {{ stroke:#9fb2a7; stroke-width:2; }}
        .axis-label {{ font-size:11px; fill:#68766e; font-weight:600; }}
        .row-line {{ stroke:#edf1ee; stroke-width:1; }}
        .row-title {{ font-size:13px; fill:#17211c; font-weight:650; }}
        .row-meta {{ font-size:11px; fill:#68766e; }}
        .buyer-dot {{ fill:#2563eb; stroke:#ffffff; stroke-width:2; }}
        .supplier-dot {{ fill:#087f5b; stroke:#ffffff; stroke-width:2; }}
        .flow-node text {{ font-size:10px; fill:#53615a; font-weight:650; }}
        .legend text {{ font-size:12px; fill:#39473f; font-weight:600; }}
        .edge-tag rect {{ fill:#ffffff; stroke:#d3ddd6; opacity:0.96; }}
        .edge-tag text {{ font-size:11px; fill:#39473f; font-weight:650; }}
      </style>
      <rect class="map-bg" x="0" y="0" width="{width}" height="{height}"/>
      <text x="24" y="38" class="row-title">Buyer cost → Supplier revenue quarter-lag flow</text>
      <g class="legend">
        <circle cx="{left:.1f}" cy="24" r="7" class="buyer-dot"/><text x="{left+14:.1f}" y="28">buyer cost anchored at t+0Q</text>
        <circle cx="{left+246:.1f}" cy="24" r="7" class="supplier-dot"/><text x="{left+260:.1f}" y="28">supplier revenue placed at best lag</text>
      </g>
      {''.join(axis_parts)}
      {''.join(edge_parts)}
      {''.join(node_parts)}
      {''.join(label_parts)}
    </svg>
    """


def money_flow_map_svg(edges: pd.DataFrame) -> str:
    left_nodes = sorted(edges["source_section"].astype(str).unique(), key=node_sort_key)
    right_nodes = sorted(edges["target_section"].astype(str).unique(), key=node_sort_key)
    lane_count = max(len(left_nodes), len(right_nodes), 8)
    row_gap = 76
    top = 118
    bottom = 86
    width = 2300
    height = top + bottom + row_gap * (lane_count - 1)
    left_x = 250
    right_x = width - 250
    left_pos = {node: (left_x, top + idx * row_gap) for idx, node in enumerate(left_nodes)}
    right_pos = {node: (right_x, top + idx * row_gap) for idx, node in enumerate(right_nodes)}

    sorted_edges = edges.sort_values(["best_corr", "best_observations"], ascending=[True, True]).reset_index(drop=True)
    edge_parts = []
    label_parts = []
    for idx, (_, edge) in enumerate(sorted_edges.iterrows()):
        source = str(edge["source_section"])
        target = str(edge["target_section"])
        x1, y1 = left_pos[source]
        x2, y2 = right_pos[target]
        color, stroke_width, dash = money_flow_edge_stroke(edge)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        curve = 470 + 18 * (idx % 5)
        offset = ((idx % 7) - 3) * 8
        path = f"M{x1 + 92},{y1} C{x1 + curve},{y1 + offset} {x2 - curve},{y2 - offset} {x2 - 92},{y2}"
        edge_parts.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{stroke_width:.1f}"{dash_attr} marker-end="url(#arrow_money)" opacity="0.74"/>'
        )
        label = edge_timing_label(edge)
        label_x = width / 2
        label_y = max(72, min(height - 32, (y1 + y2) / 2 + offset * 0.45))
        label_parts.append(
            f'<g class="edge-tag"><rect x="{label_x-52:.1f}" y="{label_y-14:.1f}" width="104" height="22" rx="11"/><text x="{label_x:.1f}" y="{label_y+1:.1f}" text-anchor="middle">{esc(label)}</text></g>'
        )

    node_parts = []
    for node, (x, y) in left_pos.items():
        fill, stroke, accent = node_palette(node)
        node_parts.append(section_node_svg(node, x, y, fill, stroke, accent, "buyer cost"))
    for node, (x, y) in right_pos.items():
        fill, stroke, accent = node_palette(node)
        node_parts.append(section_node_svg(node, x, y, fill, stroke, accent, "supplier revenue"))

    return f"""
    <svg viewBox="0 0 {width} {height}" role="img" aria-label="Section cost to supplier revenue money-flow map">
      <defs>
        <marker id="arrow_money" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L8,3 z" fill="#50615a"/>
        </marker>
      </defs>
      <style>
        .map-bg {{ fill:#fbfcfb; }}
        .map-col {{ fill:#f1f6f3; stroke:#d8ded9; }}
        .map-title {{ font-size:18px; font-weight:700; fill:#17211c; }}
        .map-subtitle {{ font-size:12px; fill:#68766e; }}
        .node .node-shadow {{ fill:#102018; opacity:0.08; transform:translate(4px,5px); }}
        .node text {{ font-size:13px; font-weight:650; fill:#17211c; }}
        .node .node-q {{ font-size:10px; font-weight:500; fill:#68766e; }}
        .edge-tag rect {{ fill:#ffffff; stroke:#d3ddd6; opacity:0.96; }}
        .edge-tag text {{ font-size:11px; fill:#39473f; font-weight:650; }}
      </style>
      <rect class="map-bg" x="0" y="0" width="{width}" height="{height}"/>
      <rect class="map-col" x="54" y="54" width="392" height="{height-96}" rx="10"/>
      <rect class="map-col" x="{width-446}" y="54" width="392" height="{height-96}" rx="10"/>
      <text class="map-title" x="{left_x}" y="42" text-anchor="middle">Buyer section cost</text>
      <text class="map-subtitle" x="{left_x}" y="66" text-anchor="middle">source: cost of revenue YoY</text>
      <text class="map-title" x="{right_x}" y="42" text-anchor="middle">Supplier section revenue</text>
      <text class="map-subtitle" x="{right_x}" y="66" text-anchor="middle">target: revenue YoY</text>
      {''.join(edge_parts)}
      {''.join(label_parts)}
      {''.join(node_parts)}
    </svg>
    """


def section_node_svg(node: str, x: int, y: int, fill: str, stroke: str, accent: str, caption: str) -> str:
    return (
        f'<g class="node"><rect class="node-shadow" x="{x-95}" y="{y-26}" width="190" height="54" rx="8"/>'
        f'<rect x="{x-95}" y="{y-26}" width="190" height="54" rx="8" fill="{fill}" stroke="{stroke}"/>'
        f'<rect x="{x-95}" y="{y-26}" width="7" height="54" rx="4" fill="{accent}"/>'
        f'<text x="{x}" y="{y-4}" text-anchor="middle">{esc(node)}</text>'
        f'<text x="{x}" y="{y+15}" text-anchor="middle" class="node-q">{esc(caption)}</text></g>'
    )


def node_sort_key(node: str) -> tuple[int, str]:
    preferred = [
        "Hyperscalers",
        "Neocloud",
        "AI Platforms",
        "AI Software",
        "Server OEM",
        "Server ODM",
        "Server EMS",
        "Server Networking",
        "AI Chip",
        "CPU",
        "DRAM",
        "NAND",
        "foundry",
        "OSAT / packiging",
        "HW equipment",
        "SW equipment",
        "meterier",
        "components",
        "Cooling",
        "Energy",
    ]
    return (preferred.index(node) if node in preferred else 999, node)


def money_flow_edge_stroke(edge: pd.Series) -> tuple[str, float, str]:
    corr = edge.get("best_corr")
    if pd.isna(corr):
        return "#9aa4a0", 1.4, "5 5"
    corr = float(corr)
    if edge.get("timing") == "target leads":
        return "#b03737", 2.0 + 5.0 * min(corr, 0.9), "4 4"
    if edge.get("timing") == "synchronous":
        return "#2563eb", 2.0 + 5.0 * min(corr, 0.9), "7 4"
    return "#087f5b", 2.3 + 5.5 * min(corr, 0.9), ""


def timeline_chain_map_svg(edges: pd.DataFrame, aria_label: str, marker_id: str, style_variant: str = "standard") -> str:
    map_width = 2600
    map_height = 1080
    axis_y1 = 76
    axis_y2 = 1010
    positions, quarter_scores = timeline_layout_positions(edges)
    edge_parts = []
    label_parts = []
    sorted_edges = edges.sort_values(["best_corr", "best_observations"], ascending=[True, True]).reset_index(drop=True)
    for idx, (_, edge) in enumerate(sorted_edges.iterrows()):
        source, target = visual_edge_direction(edge)
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        color, width, dash = data_driven_edge_stroke(edge)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        path, label_x, label_y = routed_edge_path(x1, y1, x2, y2, idx)
        label_x = max(72, min(map_width - 72, label_x))
        label_y = max(74, min(map_height - 44, label_y))
        label = edge_timing_label(edge)
        label_w = max(104, min(210, len(label) * 7.2 + 18))
        edge_parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width:.1f}"{dash_attr} marker-end="url(#{marker_id})" opacity="0.78"/>')
        label_parts.append(
            f'<g class="edge-tag"><rect x="{label_x-label_w/2:.1f}" y="{label_y-14:.1f}" width="{label_w:.1f}" height="22" rx="11"/><text x="{label_x:.1f}" y="{label_y+1:.1f}" text-anchor="middle">{esc(label)}</text></g>'
        )

    node_parts = []
    for node, (x, y) in positions.items():
        score = quarter_scores.get(node, 0.0)
        fill, stroke, accent = node_palette(node)
        node_parts.append(
            f'<g class="node"><rect class="node-shadow" x="{x-88}" y="{y-24}" width="176" height="50" rx="8"/><rect x="{x-88}" y="{y-24}" width="176" height="50" rx="8" fill="{fill}" stroke="{stroke}"/><rect x="{x-88}" y="{y-24}" width="7" height="50" rx="4" fill="{accent}"/><text x="{x}" y="{y-2}" text-anchor="middle">{esc(node)}</text><text x="{x}" y="{y+15}" text-anchor="middle" class="node-q">t{score:+.1f}Q</text></g>'
        )

    axis_ticks = []
    if quarter_scores:
        min_score = math.floor(min(quarter_scores.values()))
        max_score = math.ceil(max(quarter_scores.values()))
        score_span = max(max_score - min_score, 1)
        for tick in range(min_score, max_score + 1):
            x = 180 + (tick - min_score) / score_span * 2240
            axis_ticks.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{axis_y1}" y2="{axis_y2}" class="tick"/><text x="{x:.1f}" y="38" text-anchor="middle" class="axis-label">t{tick:+d}Q</text>')

    return f"""
    <svg viewBox="0 0 {map_width} {map_height}" role="img" aria-label="{esc(aria_label)}">
      <defs>
        <marker id="{esc(marker_id)}" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L8,3 z" fill="#50615a"/>
        </marker>
      </defs>
      <style>
        .map-bg {{ fill:#fbfcfb; }}
        .time-band {{ fill:#f1f6f3; opacity:0.58; }}
        .tick {{ stroke:#d9e1dc; stroke-width:1; }}
        .axis-label {{ font-size:11px; fill:#68766e; }}
        .node .node-shadow {{ fill:#102018; opacity:0.08; transform:translate(4px,5px); }}
        .node text {{ font-size:13px; font-weight:600; fill:#17211c; }}
        .node .node-q {{ font-size:10px; font-weight:500; fill:#68766e; }}
        .edge-tag rect {{ fill:#ffffff; stroke:#d3ddd6; opacity:0.94; }}
        .edge-tag text {{ font-size:11px; fill:#39473f; font-weight:600; }}
      </style>
      <rect class="map-bg" x="0" y="0" width="{map_width}" height="{map_height}"/>
      {map_time_bands(quarter_scores, map_width=map_width, y1=axis_y1, y2=axis_y2)}
      {''.join(axis_ticks)}
      {''.join(edge_parts)}
      {''.join(label_parts)}
      {''.join(node_parts)}
    </svg>
    """


def node_palette(node: str) -> tuple[str, str, str]:
    if node in {"Hyperscalers", "Neocloud", "AI Platforms", "AI Software"}:
        return "#edf6ff", "#a8c9ee", "#1f6feb"
    if node in {"AI Chip", "CPU"}:
        return "#f1efff", "#beb7ee", "#6f58d9"
    if node in {"DRAM", "NAND"}:
        return "#fff6e8", "#e7c37a", "#b7791f"
    if node in {"Server OEM", "Server ODM", "Server EMS", "Server Networking"}:
        return "#eef4f8", "#aebfca", "#486574"
    if node in {"HW equipment", "SW equipment", "OSAT / packiging", "foundry", "meterier", "components"}:
        return "#edf8f5", "#9fcfc1", "#087f5b"
    if node in {"Energy", "Cooling"}:
        return "#fff2eb", "#ebb08d", "#c65f27"
    return "#f6f7f6", "#c8d1cb", "#68766e"


def map_time_bands(quarter_scores: dict[str, float], map_width: int = 2600, y1: int = 58, y2: int = 880) -> str:
    if not quarter_scores:
        return ""
    min_score = math.floor(min(quarter_scores.values()))
    max_score = math.ceil(max(quarter_scores.values()))
    score_span = max(max_score - min_score, 1)
    parts = []
    for idx, tick in enumerate(range(min_score, max_score)):
        if idx % 2:
            continue
        x1 = 180 + (tick - min_score) / score_span * (map_width - 360)
        x2 = 180 + (tick + 1 - min_score) / score_span * (map_width - 360)
        parts.append(f'<rect class="time-band" x="{x1:.1f}" y="{y1}" width="{x2-x1:.1f}" height="{y2-y1}"/>')
    return "".join(parts)


def timeline_layout_positions(edges: pd.DataFrame) -> tuple[dict[str, tuple[int, int]], dict[str, float]]:
    visual_edges = []
    nodes: set[str] = set()
    for _, edge in edges.iterrows():
        source, target = visual_edge_direction(edge)
        lag = abs(int(edge["best_lag_quarters"]))
        distance = 0.35 if edge["timing"] == "synchronous" else max(1.0, float(lag))
        visual_edges.append((source, target, distance, float(edge["best_corr"])))
        nodes.update([source, target])

    ordered_nodes = sorted(nodes)
    node_index = {node: idx for idx, node in enumerate(ordered_nodes)}
    rows = []
    values = []
    for source, target, distance, corr in visual_edges:
        weight = 1.0 + min(corr, 0.9)
        row = np.zeros(len(ordered_nodes))
        row[node_index[target]] = weight
        row[node_index[source]] = -weight
        rows.append(row)
        values.append(distance * weight)
    if ordered_nodes:
        anchor = np.zeros(len(ordered_nodes))
        anchor[0] = 1.0
        rows.append(anchor)
        values.append(0.0)
    solution = np.linalg.lstsq(np.vstack(rows), np.array(values), rcond=None)[0] if rows else np.array([])
    raw_scores = {node: float(solution[idx]) for node, idx in node_index.items()}
    min_score = min(raw_scores.values()) if raw_scores else 0.0
    raw_scores = {node: score - min_score for node, score in raw_scores.items()}

    max_score = max(raw_scores.values()) if raw_scores else 1.0
    if max_score <= 0:
        max_score = 1.0
    preferred_y = {node: NODE_POSITIONS.get(node, (0, 280))[1] for node in ordered_nodes}
    sorted_nodes = sorted(ordered_nodes, key=lambda n: (raw_scores[n], preferred_y[n], n))
    lanes: list[tuple[float, int]] = []
    positions: dict[str, tuple[int, int]] = {}
    for node in sorted_nodes:
        x = int(180 + raw_scores[node] / max_score * 2240)
        available = [210, 270, 330, 390, 450, 510, 570, 630, 690, 750, 810, 870]
        preferred = preferred_y[node]
        best_lane = min(available, key=lambda lane: abs(lane - preferred) + lane_penalty(x, lane, lanes))
        lanes.append((float(x), best_lane))
        positions[node] = (x, best_lane)
    return positions, raw_scores


def lane_penalty(x: int, lane: int, occupied: list[tuple[float, int]]) -> float:
    penalty = 0.0
    for other_x, other_lane in occupied:
        if abs(other_x - x) < 260 and abs(other_lane - lane) < 68:
            penalty += 320.0 - abs(other_x - x)
    return penalty


def routed_edge_path(x1: int, y1: int, x2: int, y2: int, idx: int) -> tuple[str, float, float]:
    lane_offsets = [-44, 44, -88, 88, -132, 132, -176, 176]
    offset = lane_offsets[idx % len(lane_offsets)]
    curve = max(170, min(520, abs(x2 - x1) * 0.42))
    if abs(x2 - x1) < 190:
        side = 1 if idx % 2 == 0 else -1
        loop_x = x1 + side * (190 + 28 * (idx % 4))
        path = f"M{x1 + side * 88},{y1} C{loop_x},{y1 + offset} {loop_x},{y2 - offset} {x2 + side * 88},{y2}"
        return path, loop_x, (y1 + y2) / 2 + offset * 0.22
    if x1 <= x2:
        start_x, end_x = x1 + 90, x2 - 90
        path = f"M{start_x},{y1} C{start_x+curve},{y1+offset} {end_x-curve},{y2+offset} {end_x},{y2}"
    else:
        start_x, end_x = x1 - 90, x2 + 90
        path = f"M{start_x},{y1} C{start_x-curve},{y1+offset} {end_x+curve},{y2+offset} {end_x},{y2}"
    return path, (x1 + x2) / 2, (y1 + y2) / 2 + offset


def edge_timing_label(edge: pd.Series) -> str:
    lag = int(edge["best_lag_quarters"])
    if edge["timing"] == "target leads":
        return f"t-{abs(lag)}Q"
    if edge["timing"] == "synchronous":
        return "t+0Q"
    return f"t+{lag}Q"


def data_driven_edge_stroke(edge: pd.Series) -> tuple[str, float, str]:
    timing = edge.get("timing")
    signal = edge.get("signal_class")
    corr = edge.get("best_corr")
    if pd.isna(corr):
        return "#9aa4a0", 1.2, "5 5"
    if signal == "exploratory low-n":
        return "#6b7280", 2.0, "2 4"
    if timing == "target leads":
        return "#b03737", 2.0 + 4.0 * min(float(corr), 0.8), "3 4"
    if timing == "synchronous":
        return "#2563eb", 2.0 + 4.0 * min(float(corr), 0.8), "6 3"
    if float(corr) >= 0.65:
        return "#087f5b", 2.4 + 4.0 * min(float(corr), 0.85), ""
    return "#9a6700", 1.8 + 3.5 * min(float(corr), 0.65), "8 4"


def visual_edge_direction(edge: pd.Series) -> tuple[str, str]:
    if edge.get("timing") == "target leads":
        return str(edge["target_section"]), str(edge["source_section"])
    return str(edge["source_section"]), str(edge["target_section"])


def lag_profile_svg(edge_corr: pd.DataFrame, edge_best: pd.DataFrame, limit: int = 12) -> str:
    if edge_best.empty or "best_corr" not in edge_best.columns:
        return '<p class="note">No lag profile was available for the current data.</p>'
    corr_col = "best_corr" if "best_corr" in edge_best.columns else "best_forward_corr"
    lag_col = "best_lag_quarters" if "best_lag_quarters" in edge_best.columns else "best_forward_lag_quarters"
    chosen = edge_best.dropna(subset=[corr_col]).sort_values(corr_col, ascending=False).head(limit)
    if chosen.empty:
        return ""
    width = 1060
    row_h = 54
    height = 46 + row_h * len(chosen)
    left = 230
    right = 24
    chart_w = width - left - right
    zero_y_offset = 27
    lag_count = len(LAGS)
    step = chart_w / lag_count
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Lead-lag influence profiles">',
        "<style>.row-label{font-size:12px;fill:#17211c}.axis-label{font-size:10px;fill:#68766e}.bar-label{font-size:10px;fill:#39473f}</style>",
    ]
    for i, (_, edge) in enumerate(chosen.iterrows()):
        y_top = 34 + i * row_h
        y_zero = y_top + zero_y_offset
        source = edge["source_section"]
        target = edge["target_section"]
        sub = edge_corr[(edge_corr["source_section"] == source) & (edge_corr["target_section"] == target)]
        if "analysis_layer" in edge_corr.columns and "analysis_layer" in edge:
            sub = sub[sub["analysis_layer"] == edge["analysis_layer"]]
        if "source_metric" in edge_corr.columns and "source_metric" in edge:
            sub = sub[(sub["source_metric"] == edge["source_metric"]) & (sub["target_metric"] == edge["target_metric"])]
        sub = sub.set_index("lag_quarters")
        label = f"{source} → {target}"
        if "analysis_layer" in edge:
            label = f"{edge['analysis_layer']}: {source} → {target}"
        parts.append(f'<text x="8" y="{y_zero+4}" class="row-label">{esc(label)}</text>')
        parts.append(f'<line x1="{left}" x2="{width-right}" y1="{y_zero}" y2="{y_zero}" stroke="#c8d1cb"/>')
        for j, lag in enumerate(LAGS):
            x = left + j * step + 3
            corr = sub["corr"].get(lag, np.nan) if not sub.empty else np.nan
            if pd.isna(corr):
                parts.append(f'<rect x="{x:.1f}" y="{y_zero-2}" width="{step-6:.1f}" height="4" fill="#e5e9e6"/>')
                continue
            h = min(23, abs(float(corr)) * 30)
            color = "#087f5b" if corr >= 0 else "#b03737"
            y = y_zero - h if corr >= 0 else y_zero
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{step-6:.1f}" height="{h:.1f}" fill="{color}" opacity="0.82"/>')
        lag = edge.get(lag_col)
        corr = edge.get(corr_col)
        if not pd.isna(lag) and not pd.isna(corr):
            parts.append(f'<text x="{width-right}" y="{y_zero+4}" text-anchor="end" class="bar-label">best {int(lag):+d}Q r={float(corr):.2f}</text>')
    for j, lag in enumerate(LAGS):
        x = left + j * step + step / 2
        parts.append(f'<text x="{x:.1f}" y="18" text-anchor="middle" class="axis-label">{lag:+d}Q</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def table_html(df: pd.DataFrame, columns: list[tuple[str, str]], limit: int | None = None) -> str:
    data = df.head(limit) if limit else df
    head = "".join(f"<th>{esc(label)}</th>" for _, label in columns)
    body_rows = []
    for _, row in data.iterrows():
        cells = []
        for col, _ in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                if "corr" in col or "r_squared" in col:
                    cells.append(f"<td>{num(value, 2)}</td>")
                elif col.endswith("_pct") or "share" in col:
                    cells.append(f"<td>{pct(value)}</td>")
                else:
                    cells.append(f"<td>{num(value, 1)}</td>")
            else:
                cells.append(f"<td>{esc(value)}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def metric_best(best_df: pd.DataFrame, metric: str) -> pd.DataFrame:
    return (
        best_df[best_df["target_metric"] == metric]
        .dropna(subset=["best_positive_corr"])
        .sort_values(["best_positive_corr", "best_positive_observations"], ascending=[False, False])
    )


def metric_best_forward(best_df: pd.DataFrame, metric: str) -> pd.DataFrame:
    return (
        best_df[best_df["target_metric"] == metric]
        .dropna(subset=["best_forward_corr"])
        .sort_values(["best_forward_corr", "best_forward_observations"], ascending=[False, False])
    )


def metric_best_same_or_forward(best_df: pd.DataFrame, metric: str) -> pd.DataFrame:
    return (
        best_df[best_df["target_metric"] == metric]
        .dropna(subset=["best_same_or_forward_corr"])
        .sort_values(["best_same_or_forward_corr", "best_same_or_forward_observations"], ascending=[False, False])
    )


def top_summary(best_df: pd.DataFrame) -> list[str]:
    revenue = metric_best(best_df, "revenue_usd_m")
    revenue_forward = metric_best_forward(best_df, "revenue_usd_m")
    bullets = []
    for _, row in revenue_forward.head(5).iterrows():
        bullets.append(
            f"<li><b>{esc(row['section'])}</b>: capex가 먼저 움직인 경우의 revenue 후행 신호는 <b>{int(row['best_forward_lag_quarters']):+d}Q</b> "
            f"({esc(row['best_forward_lag_interpretation'])}), corr={num(row['best_forward_corr'], 2)}, "
            f"n={int(row['best_forward_observations'])}.</li>"
        )
    if not revenue.empty:
        strongest = revenue.iloc[0]
        bullets.append(
            f"<li>전체 lag 중 가장 강한 revenue 상관은 <b>{esc(strongest['section'])}</b>의 "
            f"<b>{int(strongest['best_positive_lag_quarters']):+d}Q</b>이며, "
            f"이는 capex가 공급망 revenue를 선행했다는 뜻이 아니라 "
            f"<b>{esc(strongest['best_positive_lag_interpretation'])}</b> 신호다.</li>"
        )
    return bullets


def revenue_leads_interpretation_html(data_best_df: pd.DataFrame) -> str:
    if data_best_df.empty:
        return "<p>No data-driven timing edges were available for interpretation.</p>"
    reverse = data_best_df[(data_best_df["timing"] == "target leads") & (data_best_df["map_eligible"])].copy()
    if reverse.empty:
        return "<p>현재 필터를 통과한 supplier-revenue-leads-buyer-cost 관계는 없다.</p>"
    top_rows = reverse.sort_values(["best_corr", "best_observations"], ascending=[False, False]).head(8)
    rows = []
    for _, row in top_rows.iterrows():
        rows.append(
            f"<li><b>{esc(row['target_section'])} supplier revenue → {esc(row['source_section'])} buyer cost</b>: "
            f"{int(row['best_lag_quarters']):+d}Q, corr={num(row['best_corr'], 2)}, n={int(row['best_observations'])}</li>"
        )
    return f"""
    <p><b>중요:</b> supplier revenue가 buyer cost보다 먼저 관측된다고 해서 supplier가 buyer 비용을 원인적으로 만든다는 뜻은 아니다. 이 분석은 section aggregate 재무제표의 인식 시점 간 상관을 보는 것이므로, 아래와 같은 해석 후보로 읽어야 한다.</p>
    <ul>
      <li><b>공급업체 매출 인식이 더 빠른 경우.</b> 공급업체는 출하, 진행률, 서비스 제공 기준으로 revenue를 먼저 잡지만, 구매자 쪽 cost of revenue는 판매/사용/매칭 원칙에 따라 뒤늦게 잡힐 수 있다.</li>
      <li><b>매출원가가 직접 구매액이 아닌 경우.</b> buyer section의 cost of revenue는 원재료 구매, 제조원가, 감가상각, 물류, 인건비, 서비스 비용이 섞인 값이다. 따라서 특정 supplier section으로 흘러간 현금 지급액과 1:1로 대응하지 않는다.</li>
      <li><b>공통 수요 shock의 다른 회계 표현.</b> 같은 AI 수요 shock이 supplier에는 revenue로, buyer에는 cost of revenue로 나타나지만, 각 section의 회계 인식 시점이 다를 수 있다.</li>
      <li><b>데이터/분류 한계.</b> section aggregate는 회사 mix, fiscal quarter 차이, segment mix, 환율/통화 단위, 회계정책 차이를 포함한다. 따라서 reverse timing은 인과 결론이 아니라 “회계상 먼저 관측되는 지표” 후보로 보는 것이 맞다.</li>
    </ul>
    <p>현재 필터를 통과한 대표적인 supplier-revenue-leads-buyer-cost 관계는 다음과 같다.</p>
    <ul>{''.join(rows)}</ul>
    """


def references_payload() -> list[dict[str, str]]:
    return [
        {
            "title": "Dynamic Time Warping for Lead-Lag Relationships in Lagged Multi-Factor Models",
            "url": "https://arxiv.org/abs/2309.08800",
            "use": "Methodology anchor for treating lead-lag structure as a temporal dependency in multivariate systems.",
        },
        {
            "title": "High Frequency Lead/lag Relationships - Empirical facts",
            "url": "https://arxiv.org/abs/1111.7103",
            "use": "Methodology anchor for asymmetric cross-correlation and leader/lagger interpretation.",
        },
        {
            "title": "Quantifying and Modeling Long-Range Cross-Correlations in Multiple Time Series",
            "url": "https://arxiv.org/abs/1102.2240",
            "use": "Methodology anchor for time-lag cross-correlation and the risk of common-factor interpretation.",
        },
        {
            "title": "IEA - Energy and AI",
            "url": "https://www.iea.org/reports/energy-and-ai",
            "use": "Industry anchor for AI/data-center electricity demand, grid, and infrastructure interpretation.",
        },
        {
            "title": "Semiconductor Industry Association - State of the U.S. Semiconductor Industry",
            "url": "https://www.semiconductors.org/resources/state-of-the-u-s-semiconductor-industry/",
            "use": "Industry anchor for semiconductor supply-chain structure and capital intensity.",
        },
        {
            "title": "SEMI market data and reports",
            "url": "https://www.semi.org/en/market-data",
            "use": "Industry anchor for semiconductor equipment, fab investment, and materials cycle interpretation.",
        },
    ]


def references_html() -> str:
    rows = []
    for ref in references_payload():
        rows.append(
            f"<tr><td><a href=\"{esc(ref['url'])}\">{esc(ref['title'])}</a></td><td>{esc(ref['use'])}</td></tr>"
        )
    return f"<table><thead><tr><th>Reference</th><th>How it is used</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"


def data_layer_summary_html(data_best_df: pd.DataFrame) -> str:
    if data_best_df.empty:
        return "<p>No layer-level best signals were available.</p>"
    summary = (
        data_best_df.groupby("analysis_layer")
        .agg(
            best_signals=("analysis_layer", "size"),
            map_edges=("map_eligible", lambda s: int(s.sum())),
            median_corr=("best_corr", "median"),
            top_corr=("best_corr", "max"),
            median_observations=("best_observations", "median"),
        )
        .reset_index()
        .sort_values(["map_edges", "top_corr"], ascending=[False, False])
    )
    return table_html(
        summary,
        [
            ("analysis_layer", "Analysis layer"),
            ("best_signals", "Best signals"),
            ("map_edges", "Map edges"),
            ("median_corr", "Median corr"),
            ("top_corr", "Top corr"),
            ("median_observations", "Median obs"),
        ],
    )


def build_html(
    section_quarterly: pd.DataFrame,
    coverage: pd.DataFrame,
    data_corr_df: pd.DataFrame,
    data_best_df: pd.DataFrame,
    source_label: str = "financials.db",
    source_detail: str = str(DB_PATH),
) -> str:
    payload = {
        "generated_at": pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d %H:%M KST"),
        "source": source_detail,
        "source_master": str(MASTER_PATH),
        "data_driven_filter": {
            "min_calc_observations": MIN_CALC_OBS,
            "min_report_observations": MIN_REPORT_OBS,
            "min_map_observations": MIN_MAP_OBS,
            "min_corr_for_map": DATA_DRIVEN_MIN_ABS_CORR,
            "max_map_edges": DATA_DRIVEN_MAX_MAP_EDGES,
            "lags": LAGS,
            "analysis_layers": DATA_DRIVEN_LAYER_CONFIGS,
        },
        "external_references": references_payload(),
    }
    valid_corr_count = len(data_corr_df.dropna(subset=["corr"])) if "corr" in data_corr_df else 0
    map_edges = int(data_best_df["map_eligible"].sum()) if not data_best_df.empty and "map_eligible" in data_best_df else 0
    strong_or_moderate = (
        int(data_best_df["signal_class"].isin(["strong", "moderate"]).sum())
        if not data_best_df.empty and "signal_class" in data_best_df
        else 0
    )
    layer_summary = data_layer_summary_html(data_best_df)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Financial Lead-Lag Report</title>
  <style>
    :root {{
      --ink:#17211c; --muted:#5f6b64; --line:#d8ded9; --bg:#f8faf8;
      --panel:#ffffff; --green:#087f5b; --amber:#9a6700; --red:#b03737;
    }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:var(--bg); }}
    header {{ padding:34px 42px 22px; background:#eaf3ee; border-bottom:1px solid var(--line); }}
    h1 {{ margin:0 0 8px; font-size:30px; letter-spacing:0; }}
    h2 {{ margin:34px 0 12px; font-size:21px; }}
    h3 {{ margin:24px 0 8px; font-size:16px; }}
    p, li {{ line-height:1.55; }}
    main {{ padding:0 42px 48px; max-width:2140px; }}
    .meta {{ color:var(--muted); font-size:13px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:18px 0 8px; }}
    .kpi {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; }}
    .kpi b {{ display:block; font-size:22px; }}
    .kpi span {{ color:var(--muted); font-size:12px; }}
    .note {{ background:#fff9e8; border:1px solid #ead28a; padding:12px 14px; border-radius:8px; }}
    table {{ border-collapse:collapse; width:100%; background:var(--panel); border:1px solid var(--line); font-size:13px; }}
    th, td {{ padding:8px 9px; border-bottom:1px solid var(--line); text-align:right; vertical-align:top; }}
    th:first-child, td:first-child {{ text-align:left; }}
    thead th {{ position:sticky; top:0; background:#eef4f0; z-index:1; }}
    .tablewrap {{ overflow:auto; max-height:560px; border:1px solid var(--line); }}
    .heatmap td {{ min-width:52px; font-variant-numeric:tabular-nums; }}
    .heatmap th:first-child {{ min-width:170px; }}
    svg {{ width:100%; min-width:1900px; height:auto; background:#fff; border:1px solid var(--line); border-radius:8px; }}
    svg text {{ font-size:11px; fill:var(--muted); }}
    .axis {{ stroke:#aab5ae; stroke-width:1; }}
    .two {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; align-items:start; }}
    code {{ background:#edf2ee; padding:2px 4px; border-radius:4px; }}
    @media (max-width:900px) {{ header, main {{ padding-left:18px; padding-right:18px; }} .grid, .two {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<header>
  <h1>AI Supply Chain Financial Lead-Lag: Section Money Flow</h1>
  <div class="meta">Generated {esc(payload["generated_at"])} · Source: {esc(source_label)} · Master: {esc(MASTER_PATH.name)}</div>
</header>
<main>
  <section class="grid">
    <div class="kpi"><b>{coverage["master_companies"].sum():,.0f}</b><span>matched companies in master</span></div>
    <div class="kpi"><b>{section_quarterly["section"].nunique():,.0f}</b><span>supply-chain sections</span></div>
    <div class="kpi"><b>{section_quarterly["quarter_period"].nunique():,.0f}</b><span>calendar quarters</span></div>
    <div class="kpi"><b>{valid_corr_count:,.0f}</b><span>valid metric-layer lag correlations</span></div>
  </section>

  <section>
    <h2>Executive Read</h2>
    <p>이 버전은 “각 section의 비용이 다른 section의 매출로 어떻게 관측되는가”에 집중하기 위해 변수를 더 줄였다. 분석에 쓰는 source 지표는 <code>cost of revenue</code> 하나이고, target 지표는 <code>supplier revenue</code>로 고정한다. <code>capex</code>, <code>inventory</code>, <code>operating income</code>, <code>net income</code>은 현재 체인맵에서 제외했다.</p>
    <p class="note">핵심 산출물은 <code>data_driven/data_driven_edge_lag_correlations.csv</code>와 <code>data_driven/data_driven_edge_best_signals.csv</code>다. 현재 map filter를 통과한 edge는 <b>{map_edges:,}</b>개이고, strong/moderate로 분류된 best signal은 <b>{strong_or_moderate:,}</b>개다. 이 값은 인과관계 증명이 아니라 “buyer section의 cost of revenue 변화가 supplier section의 revenue 변화와 시간적으로 같이 움직이는 후보”를 찾는 탐색 결과다.</p>
    {layer_summary}
  </section>

  <section>
    <h2>Data-Driven Chain Map</h2>
    <h3>Section Influence Matrix</h3>
    <p>기본 그래프에는 <code>n ≥ {MIN_MAP_OBS}</code>이고 <code>corr ≥ {DATA_DRIVEN_MIN_ABS_CORR}</code>인 관계를 우선 표시한다. 위쪽 matrix는 row를 buyer cost-of-revenue section, column을 supplier revenue section으로 둔다. 각 cell의 <code>t+…Q</code>는 buyer cost를 <code>t+0Q</code>로 볼 때 supplier revenue가 어느 분기에 가장 강하게 연결되는지를 의미한다.</p>
    <p>아래 quarter flow board는 같은 edge를 lag별로 다시 묶은 것이다. 초록은 buyer cost가 supplier revenue를 선행, 파란색은 동분기, 붉은색은 supplier revenue가 buyer cost보다 먼저 관측되는 관계다. <code>n={MIN_CALC_OBS}~{MIN_REPORT_OBS - 1}</code>인 결과는 CSV에는 남기되 <code>exploratory low-n</code>으로 분리하고, <code>n ≥ {MIN_REPORT_OBS}</code>부터 table-grade signal로 분류한다.</p>
    {data_driven_chain_map_svg(data_best_df)}
    <div class="tablewrap">
      {table_html(data_best_df, [
        ("analysis_layer", "Layer"),
        ("source_section", "Buyer section"),
        ("source_metric", "Buyer cost metric"),
        ("source_transform", "Source transform"),
        ("target_section", "Supplier section"),
        ("target_metric", "Supplier metric"),
        ("timing", "Timing"),
        ("best_lag_quarters", "Best lag"),
        ("best_corr", "Corr"),
        ("best_observations", "Obs"),
        ("signal_class", "Class"),
        ("map_eligible", "Map"),
        ("interpretation", "Interpretation"),
      ], limit=40)}
    </div>
    <h3>How to Interpret Target-Leads Timing</h3>
    {revenue_leads_interpretation_html(data_best_df)}
    <h3>Data-Driven Lag Impact Profiles</h3>
    <p>아래 그래프는 데이터 기반으로 선정된 edge의 lag별 상관계수다. +Q는 buyer cost가 supplier revenue를 선행, 0Q는 동행, -Q는 supplier revenue가 buyer cost보다 먼저 움직인다는 뜻이다.</p>
    {lag_profile_svg(data_corr_df, data_best_df, limit=14)}
  </section>

  <section>
    <h2>Financial Data Coverage</h2>
    <p>section별 회사 수, 관측 분기 수, 분석에 직접 쓰는 revenue/cost row 수와 변환 가능 관측치를 확인한다. capex, inventory, profit 항목은 현재 cost-flow chain 분석에서는 사용하지 않는다.</p>
    <div class="tablewrap">
      {table_html(coverage, [
        ("section", "Section"),
        ("master_companies", "Master companies"),
        ("observed_companies", "Observed companies"),
        ("first_quarter", "First qtr"),
        ("last_quarter", "Last qtr"),
        ("quarters", "Quarters"),
        ("revenue_rows", "Revenue rows"),
        ("cost_of_revenue_rows", "Cost rows"),
        ("revenue_yoy_obs", "Revenue YoY obs"),
        ("cost_of_revenue_yoy_obs", "Cost YoY obs"),
      ])}
    </div>
  </section>

  <section>
    <h2>Methodology</h2>
    <p><b>Aggregation.</b> Company financial rows are mapped to the user-defined supply-chain section. In DB mode, the section mapping comes from <code>company_master.xlsx</code>; in DataFrame mode, the input <code>section</code> column is used directly. Quarterly values are summed by <code>section × calendar_quarter</code>. Capex is converted to positive investment spend using absolute value because cash-flow statements can encode capex as an outflow.</p>
    <p><b>Cost of revenue.</b> DB mode derives <code>cost_of_revenue_usd_m</code> as <code>revenue_usd_m - gross_profit_usd_m</code>. DataFrame mode accepts direct <code>cost_of_revenue</code>, <code>cost of sales</code>, or <code>cogs</code> rows and fills remaining gaps from revenue minus gross profit when possible.</p>
    <p><b>Variable transformation.</b> The report uses the user-defined current-base YoY ratio for every financial metric: <code>(x_t - x_(t-4)) / x_t</code>. If <code>x_t</code> is zero, the transformed observation is treated as missing.</p>
    <p><b>Lead-lag convention.</b> lag +N means source metric at quarter t is compared with target metric at quarter t+N. lag 0 is same-quarter coupling. lag -N means the target metric moved before the source metric.</p>
    <p><b>Data-driven edge discovery.</b> The report ignores predefined business edges and evaluates every ordered section pair for one money-flow layer: <code>buyer cost of revenue → supplier revenue</code>. For each source-target tuple, it keeps the strongest positive correlation across -4Q to +8Q, then labels timing as source-leads, synchronous, or target-leads. Correlations are calculated when <code>n ≥ {MIN_CALC_OBS}</code>, classified as table-grade when <code>n ≥ {MIN_REPORT_OBS}</code>, and shown on the map only when <code>n ≥ {MIN_MAP_OBS}</code> plus <code>corr ≥ {DATA_DRIVEN_MIN_ABS_CORR}</code>.</p>
    <p><b>No QoQ fallback.</b> The source spending transform is <code>cost_of_revenue_usd_m_yoy_current_ratio</code>. Sparse edges remain in the CSV as <code>exploratory low-n</code> rather than falling back to QoQ.</p>
    <p><b>Signal classes.</b> Best positive correlations are classified as strong ≥ 0.65, moderate ≥ 0.50, weak ≥ {DATA_DRIVEN_MIN_ABS_CORR}, very weak below that, and exploratory low-n when observations are below {MIN_REPORT_OBS}. These are analytical thresholds for exploration, not literature constants.</p>
    <p><b>Files generated.</b> Section-level data is saved beside this HTML: <code>{esc(OUTPUT_FILENAMES["section_quarterly"])}</code> and <code>{esc(OUTPUT_FILENAMES["coverage"])}</code>. Data-driven results are saved under <code>data_driven/</code>: <code>{esc(OUTPUT_FILENAMES["data_edge_corr"])}</code> and <code>{esc(OUTPUT_FILENAMES["data_edge_best"])}</code>.</p>
  </section>

  <section>
    <h2>References and Interpretation Anchors</h2>
    <p>아래 문헌은 모델 계수의 근거가 아니라, 왜 lead-lag/cross-correlation 접근을 쓰는지와 AI 인프라 공급망 edge를 어떻게 해석할지에 대한 참고 anchor다. 실제 상관계수와 lag는 입력 재무 데이터에서 산출했다.</p>
    {references_html()}
  </section>

  <script type="application/json" id="report-provenance">{esc(json.dumps(payload, ensure_ascii=False, indent=2))}</script>
</main>
</body>
</html>
"""


def output_paths(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: output_dir / filename for key, filename in OUTPUT_FILENAMES.items()}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    return paths


def write_report_outputs(
    matched: pd.DataFrame,
    financials: pd.DataFrame,
    output_dir: Path = ROOT,
    source_label: str = "financials.db",
    source_detail: str = str(DB_PATH),
) -> dict[str, Path]:
    paths = output_paths(output_dir)
    section_quarterly = aggregate_section_quarterly(financials)
    coverage = coverage_table(financials, section_quarterly, matched)
    data_corr_df, data_best_df = data_driven_lag_correlations(section_quarterly)

    csv_section = section_quarterly.copy()
    csv_section["quarter_period"] = csv_section["quarter_period"].astype(str)
    csv_section.to_csv(paths["section_quarterly"], index=False)
    data_corr_df.to_csv(paths["data_edge_corr"], index=False)
    data_best_df.to_csv(paths["data_edge_best"], index=False)
    coverage.to_csv(paths["coverage"], index=False)

    paths["html"].write_text(
        build_html(
            section_quarterly,
            coverage,
            data_corr_df,
            data_best_df,
            source_label=source_label,
            source_detail=source_detail,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {paths['html']}")
    print(f"Valid data-driven metric-layer lag correlations: {data_corr_df['corr'].notna().sum():,}")
    print("Top data-driven edges:")
    data_cols = [
        "analysis_layer",
        "source_section",
        "source_metric",
        "target_section",
        "target_metric",
        "best_lag_quarters",
        "timing",
        "best_corr",
        "best_observations",
        "signal_class",
        "map_eligible",
    ]
    print(data_best_df[data_cols].head(12).to_string(index=False) if not data_best_df.empty else "(none)")
    return paths


def generate_report_from_dataframe(
    df: pd.DataFrame,
    output_dir: str | Path = ROOT / "dataframe_report",
    analysis_start_quarter: str | None = "2012-Q1",
) -> dict[str, Path]:
    """Generate the same HTML/CSV report from a long financial DataFrame.

    Expected logical columns:
    - companyname
    - section
    - fs_item: capex, revenue, and optionally gross_profit, cost_of_revenue,
      inventories, operating_income, net_income
    - date: any date inside the fiscal/calendar quarter, or strings such as 2024-Q1
    - value
    """
    matched, financials = normalize_financial_dataframe(df, analysis_start_quarter=analysis_start_quarter)
    return write_report_outputs(
        matched,
        financials,
        output_dir=Path(output_dir),
        source_label="input dataframe",
        source_detail="long dataframe columns: companyname, section, fs_item, date, value",
    )


def write_outputs() -> None:
    matched, financials = load_data()
    write_report_outputs(matched, financials, output_dir=ROOT, source_label=DB_PATH.name, source_detail=str(DB_PATH))


if __name__ == "__main__":
    write_outputs()
