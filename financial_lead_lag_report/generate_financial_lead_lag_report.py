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
OUT_HYPERSCALER_CAPEX = ROOT / "hyperscaler_capex_series.csv"
OUT_LAG_CORR = ROOT / "lead_lag_correlation_summary.csv"
OUT_BEST_SIGNALS = ROOT / "lead_lag_best_signals.csv"
OUT_COVERAGE = ROOT / "financial_data_coverage.csv"
OUT_CHAIN_EDGE_CORR = ROOT / "value_chain_edge_lag_correlations.csv"
OUT_CHAIN_EDGE_BEST = ROOT / "value_chain_edge_best_signals.csv"
OUT_DATA_DRIVEN_EDGE_CORR = ROOT / "data_driven_edge_lag_correlations.csv"
OUT_DATA_DRIVEN_EDGE_BEST = ROOT / "data_driven_edge_best_signals.csv"

ANALYSIS_START_QUARTER = "2016-Q1"
HYPERSCALER_SECTION = "Hyperscalers"
LAGS = list(range(-4, 9))
MIN_OBS = 8
MIN_SUPPLEMENTAL_OBS = 4
DATA_DRIVEN_MIN_ABS_CORR = 0.45
DATA_DRIVEN_MAX_MAP_EDGES = 22


METRICS = {
    "revenue_usd_m": "Revenue",
    "gross_profit_usd_m": "Gross profit",
    "operating_income_usd_m": "Operating income",
    "net_income_usd_m": "Net income",
}


VALUE_CHAIN_HYPOTHESES = [
    {
        "source": "Hyperscalers",
        "targets": ["Cooling", "Energy", "Server OEM", "Server ODM", "Server EMS", "Server Networking"],
        "hypothesis": "Data-center buildout pull-through into physical infrastructure, server assembly, and networking.",
        "stage": "facility_and_server_buildout",
    },
    {
        "source": "Hyperscalers",
        "targets": ["AI Chip", "CPU", "DRAM", "NAND"],
        "hypothesis": "Compute and memory procurement follows hyperscaler investment budgets.",
        "stage": "compute_and_memory_procurement",
    },
    {
        "source": "AI Chip",
        "targets": ["DRAM", "NAND", "OSAT / packiging", "foundry"],
        "hypothesis": "AI accelerator investment cycle pulls memory, advanced packaging, and foundry demand.",
        "stage": "accelerator_supply_chain",
    },
    {
        "source": "DRAM",
        "targets": ["HW equipment", "SW equipment", "meterier", "components"],
        "hypothesis": "Memory capex cycle should lead semiconductor equipment, materials, and component revenue.",
        "stage": "memory_capacity_expansion",
    },
    {
        "source": "NAND",
        "targets": ["HW equipment", "SW equipment", "meterier", "components"],
        "hypothesis": "Storage capex cycle should lead semiconductor equipment, materials, and component revenue.",
        "stage": "memory_capacity_expansion",
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
    return matched, financials


def yoy_pct(series: pd.Series) -> pd.Series:
    previous = series.shift(4)
    out = series / previous - 1.0
    out[(series <= 0) | (previous <= 0)] = np.nan
    return out.replace([np.inf, -np.inf], np.nan)


def yoy_delta(series: pd.Series) -> pd.Series:
    return (series - series.shift(4)).replace([np.inf, -np.inf], np.nan)


def qoq_pct(series: pd.Series) -> pd.Series:
    previous = series.shift(1)
    out = series / previous - 1.0
    out[(series <= 0) | (previous <= 0)] = np.nan
    return out.replace([np.inf, -np.inf], np.nan)


def aggregate_section_quarterly(financials: pd.DataFrame) -> pd.DataFrame:
    data = financials.copy()
    data["capex_investment_usd_m"] = pd.to_numeric(data["capex_usd_m"], errors="coerce").abs()
    for col in list(METRICS):
        data[col] = pd.to_numeric(data[col], errors="coerce")

    agg_spec: dict[str, tuple[str, str]] = {
        "capex_investment_usd_m": ("capex_investment_usd_m", "sum"),
        "capex_valid_companies": ("capex_investment_usd_m", lambda s: int(s.notna().sum())),
        "total_companies": ("db_ticker", "nunique"),
    }
    for metric in METRICS:
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
        sub["capex_yoy_pct"] = yoy_pct(sub["capex_investment_usd_m"])
        sub["capex_qoq_pct"] = qoq_pct(sub["capex_investment_usd_m"])
        for metric in METRICS:
            sub[f"{metric}_yoy_pct"] = yoy_pct(sub[metric])
            sub[f"{metric}_qoq_pct"] = qoq_pct(sub[metric])
            sub[f"{metric}_yoy_delta_usd_m"] = yoy_delta(sub[metric])
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
            capex_rows=("capex_usd_m", lambda s: int(s.notna().sum())),
            operating_income_rows=("operating_income_usd_m", lambda s: int(s.notna().sum())),
        )
        .reset_index()
    )
    quarter_counts = (
        section_quarterly.groupby("section")
        .agg(
            quarters=("quarter_period", "nunique"),
            revenue_yoy_obs=("revenue_usd_m_yoy_pct", lambda s: int(s.notna().sum())),
            capex_yoy_obs=("capex_yoy_pct", lambda s: int(s.notna().sum())),
        )
        .reset_index()
    )
    out = section_tickers.merge(observed, on="section", how="left").merge(quarter_counts, on="section", how="left")
    out["first_quarter"] = out["first_quarter"].astype(str).str.replace("Q", "-Q", regex=False)
    out["last_quarter"] = out["last_quarter"].astype(str).str.replace("Q", "-Q", regex=False)
    return out.sort_values(["master_companies", "section"], ascending=[False, True])


def lag_correlations(section_quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    hyper = (
        section_quarterly[section_quarterly["section"] == HYPERSCALER_SECTION]
        .set_index("quarter_period")
        .sort_index()["capex_yoy_pct"]
        .rename("hyperscaler_capex_yoy_pct")
    )
    rows = []
    for section, sub in section_quarterly.groupby("section"):
        sub = sub.set_index("quarter_period").sort_index()
        for metric, metric_label in METRICS.items():
            target_col = f"{metric}_yoy_pct" if metric in {"revenue_usd_m", "gross_profit_usd_m"} else f"{metric}_yoy_delta_usd_m"
            transform = "YoY %" if target_col.endswith("_yoy_pct") else "YoY delta USDm"
            target = sub[target_col]
            for lag in LAGS:
                aligned = pd.concat([hyper, target.shift(-lag).rename("target")], axis=1).dropna()
                if len(aligned) < MIN_OBS:
                    corr = beta = np.nan
                else:
                    corr = float(aligned["hyperscaler_capex_yoy_pct"].corr(aligned["target"]))
                    variance = float(aligned["hyperscaler_capex_yoy_pct"].var())
                    beta = float(aligned["hyperscaler_capex_yoy_pct"].cov(aligned["target"]) / variance) if variance else np.nan
                rows.append(
                    {
                        "section": section,
                        "target_metric": metric,
                        "target_metric_label": metric_label,
                        "target_transform": transform,
                        "lag_quarters": lag,
                        "lag_interpretation": lag_label(lag),
                        "observations": int(len(aligned)),
                        "corr": corr,
                        "r_squared": corr * corr if not pd.isna(corr) else np.nan,
                        "beta_target_per_1_capex_yoy": beta,
                    }
                )
    corr_df = pd.DataFrame(rows)
    best_rows = []
    for (section, metric), sub in corr_df.dropna(subset=["corr"]).groupby(["section", "target_metric"]):
        if sub.empty:
            continue
        positive = sub[sub["corr"] > 0]
        forward = sub[(sub["lag_quarters"] > 0) & (sub["corr"] > 0)]
        nonnegative = sub[(sub["lag_quarters"] >= 0) & (sub["corr"] > 0)]
        best_pos = positive.loc[positive["corr"].idxmax()] if not positive.empty else None
        best_forward = forward.loc[forward["corr"].idxmax()] if not forward.empty else None
        best_nonnegative = nonnegative.loc[nonnegative["corr"].idxmax()] if not nonnegative.empty else None
        best_abs = sub.loc[sub["corr"].abs().idxmax()]
        best_rows.append(
            {
                "section": section,
                "target_metric": metric,
                "target_metric_label": best_abs["target_metric_label"],
                "target_transform": best_abs["target_transform"],
                "best_positive_lag_quarters": int(best_pos["lag_quarters"]) if best_pos is not None else np.nan,
                "best_positive_lag_interpretation": best_pos["lag_interpretation"] if best_pos is not None else "",
                "best_positive_corr": float(best_pos["corr"]) if best_pos is not None else np.nan,
                "best_positive_observations": int(best_pos["observations"]) if best_pos is not None else 0,
                "best_forward_lag_quarters": int(best_forward["lag_quarters"]) if best_forward is not None else np.nan,
                "best_forward_lag_interpretation": best_forward["lag_interpretation"] if best_forward is not None else "",
                "best_forward_corr": float(best_forward["corr"]) if best_forward is not None else np.nan,
                "best_forward_observations": int(best_forward["observations"]) if best_forward is not None else 0,
                "best_same_or_forward_lag_quarters": int(best_nonnegative["lag_quarters"]) if best_nonnegative is not None else np.nan,
                "best_same_or_forward_lag_interpretation": best_nonnegative["lag_interpretation"] if best_nonnegative is not None else "",
                "best_same_or_forward_corr": float(best_nonnegative["corr"]) if best_nonnegative is not None else np.nan,
                "best_same_or_forward_observations": int(best_nonnegative["observations"]) if best_nonnegative is not None else 0,
                "best_abs_lag_quarters": int(best_abs["lag_quarters"]),
                "best_abs_lag_interpretation": best_abs["lag_interpretation"],
                "best_abs_corr": float(best_abs["corr"]),
                "best_abs_observations": int(best_abs["observations"]),
                "interpretation": interpret_signal(best_pos, best_forward, best_abs),
            }
        )
    best_df = pd.DataFrame(best_rows).sort_values(["target_metric", "best_positive_corr"], ascending=[True, False])
    return corr_df, best_df


def value_chain_edges() -> pd.DataFrame:
    rows = []
    for group in VALUE_CHAIN_HYPOTHESES:
        for target in group["targets"]:
            rows.append(
                {
                    "source_section": group["source"],
                    "target_section": target,
                    "stage": group["stage"],
                    "hypothesis": group["hypothesis"],
                }
            )
    return pd.DataFrame(rows).drop_duplicates(["source_section", "target_section"])


def value_chain_lag_correlations(section_quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    indexed = {
        section: sub.set_index("quarter_period").sort_index()
        for section, sub in section_quarterly.groupby("section")
    }
    rows = []
    for _, edge in value_chain_edges().iterrows():
        source = edge["source_section"]
        target = edge["target_section"]
        if source not in indexed or target not in indexed:
            for lag in LAGS:
                rows.append(edge_row(edge, lag, np.nan, 0, np.nan, "missing_section", "capex_yoy_pct", "revenue_usd_m_yoy_pct"))
            continue
        source_col = choose_source_capex_transform(indexed[source])
        target_col = "revenue_usd_m_yoy_pct"
        source_series = indexed[source][source_col].rename("source_capex_change")
        target_series = indexed[target][target_col].rename("target_revenue_yoy_pct")
        min_obs = MIN_OBS if source_col == "capex_yoy_pct" else MIN_SUPPLEMENTAL_OBS
        for lag in LAGS:
            aligned = pd.concat([source_series, target_series.shift(-lag)], axis=1).dropna()
            if len(aligned) < min_obs:
                corr = beta = np.nan
                status = "insufficient_observations"
            else:
                corr = float(aligned["source_capex_change"].corr(aligned["target_revenue_yoy_pct"]))
                variance = float(aligned["source_capex_change"].var())
                beta = float(aligned["source_capex_change"].cov(aligned["target_revenue_yoy_pct"]) / variance) if variance else np.nan
                if source_col == "capex_yoy_pct":
                    status = "ok"
                elif len(aligned) < MIN_OBS:
                    status = "exploratory_low_n_qoq_source"
                else:
                    status = "ok_supplemental_qoq_source"
            rows.append(edge_row(edge, lag, corr, int(len(aligned)), beta, status, source_col, target_col))
    corr_df = pd.DataFrame(rows)
    best_rows = []
    for (source, target), sub in corr_df.groupby(["source_section", "target_section"]):
        valid = sub.dropna(subset=["corr"])
        base = sub.iloc[0]
        if valid.empty:
            best_rows.append(
                {
                    "source_section": source,
                    "target_section": target,
                    "stage": base["stage"],
                    "hypothesis": base["hypothesis"],
                    "source_metric": base["source_metric"],
                    "target_metric": base["target_metric"],
                    "best_forward_lag_quarters": np.nan,
                    "best_forward_corr": np.nan,
                    "best_forward_observations": 0,
                    "best_same_or_forward_lag_quarters": np.nan,
                    "best_same_or_forward_corr": np.nan,
                    "best_same_or_forward_observations": 0,
                    "best_any_lag_quarters": np.nan,
                    "best_any_corr": np.nan,
                    "best_abs_lag_quarters": np.nan,
                    "best_abs_corr": np.nan,
                    "signal_class": "no data",
                    "evidence_note": "No lag had enough overlapping YoY observations.",
                }
            )
            continue
        forward = valid[(valid["lag_quarters"] > 0) & (valid["corr"] > 0)]
        same_forward = valid[(valid["lag_quarters"] >= 0) & (valid["corr"] > 0)]
        positive = valid[valid["corr"] > 0]
        best_forward = forward.loc[forward["corr"].idxmax()] if not forward.empty else None
        best_same_forward = same_forward.loc[same_forward["corr"].idxmax()] if not same_forward.empty else None
        best_any = positive.loc[positive["corr"].idxmax()] if not positive.empty else None
        best_abs = valid.loc[valid["corr"].abs().idxmax()]
        signal = classify_edge(best_forward)
        best_rows.append(
            {
                "source_section": source,
                "target_section": target,
                "stage": base["stage"],
                "hypothesis": base["hypothesis"],
                "source_metric": base["source_metric"],
                "target_metric": base["target_metric"],
                "best_forward_lag_quarters": int(best_forward["lag_quarters"]) if best_forward is not None else np.nan,
                "best_forward_corr": float(best_forward["corr"]) if best_forward is not None else np.nan,
                "best_forward_observations": int(best_forward["observations"]) if best_forward is not None else 0,
                "best_same_or_forward_lag_quarters": int(best_same_forward["lag_quarters"]) if best_same_forward is not None else np.nan,
                "best_same_or_forward_corr": float(best_same_forward["corr"]) if best_same_forward is not None else np.nan,
                "best_same_or_forward_observations": int(best_same_forward["observations"]) if best_same_forward is not None else 0,
                "best_any_lag_quarters": int(best_any["lag_quarters"]) if best_any is not None else np.nan,
                "best_any_corr": float(best_any["corr"]) if best_any is not None else np.nan,
                "best_abs_lag_quarters": int(best_abs["lag_quarters"]),
                "best_abs_corr": float(best_abs["corr"]),
                "signal_class": signal,
                "evidence_note": edge_note(best_forward, best_any, best_abs),
            }
        )
    best_df = pd.DataFrame(best_rows)
    order = {"strong": 0, "moderate": 1, "weak": 2, "very weak": 3, "exploratory low-n": 4, "no forward evidence": 5, "no data": 6}
    best_df["_order"] = best_df["signal_class"].map(order).fillna(9)
    best_df = best_df.sort_values(["_order", "best_forward_corr", "source_section", "target_section"], ascending=[True, False, True, True]).drop(columns=["_order"])
    return corr_df, best_df


def data_driven_lag_correlations(section_quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    indexed = {
        section: sub.set_index("quarter_period").sort_index()
        for section, sub in section_quarterly.groupby("section")
    }
    sections = sorted(indexed)
    rows = []
    for source in sections:
        source_col = choose_source_capex_transform(indexed[source])
        min_obs = MIN_OBS if source_col == "capex_yoy_pct" else MIN_SUPPLEMENTAL_OBS
        source_series = indexed[source][source_col].rename("source_capex_change")
        for target in sections:
            if source == target:
                continue
            target_col = "revenue_usd_m_yoy_pct"
            target_series = indexed[target][target_col].rename("target_revenue_yoy_pct")
            for lag in LAGS:
                aligned = pd.concat([source_series, target_series.shift(-lag)], axis=1).dropna()
                if len(aligned) < min_obs:
                    corr = beta = np.nan
                    status = "insufficient_observations"
                else:
                    corr = float(aligned["source_capex_change"].corr(aligned["target_revenue_yoy_pct"]))
                    variance = float(aligned["source_capex_change"].var())
                    beta = float(aligned["source_capex_change"].cov(aligned["target_revenue_yoy_pct"]) / variance) if variance else np.nan
                    if source_col == "capex_yoy_pct":
                        status = "ok"
                    elif len(aligned) < MIN_OBS:
                        status = "exploratory_low_n_qoq_source"
                    else:
                        status = "ok_supplemental_qoq_source"
                rows.append(
                    {
                        "source_section": source,
                        "target_section": target,
                        "source_metric": source_col,
                        "target_metric": target_col,
                        "lag_quarters": lag,
                        "timing": timing_label(lag),
                        "lag_interpretation": chain_lag_label(source, target, lag),
                        "observations": int(len(aligned)),
                        "corr": corr,
                        "r_squared": corr * corr if not pd.isna(corr) else np.nan,
                        "beta_revenue_yoy_per_1_capex_change": beta,
                        "status": status,
                    }
                )
    corr_df = pd.DataFrame(rows)
    best_rows = []
    for (source, target), sub in corr_df.groupby(["source_section", "target_section"]):
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
                "source_section": source,
                "target_section": target,
                "source_metric": best["source_metric"],
                "target_metric": best["target_metric"],
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
        return corr_df, best_df
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
        return "source capex leads"
    if lag < 0:
        return "target revenue leads"
    return "synchronous"


def classify_data_driven_edge(corr: float, observations: int, status: str) -> str:
    if observations < MIN_OBS or "low_n" in str(status):
        return "exploratory low-n"
    if corr >= 0.65:
        return "strong"
    if corr >= 0.50:
        return "moderate"
    if corr >= DATA_DRIVEN_MIN_ABS_CORR:
        return "weak"
    return "very weak"


def is_map_eligible(corr: float, observations: int, status: str) -> bool:
    return observations >= MIN_OBS and "low_n" not in str(status) and corr >= DATA_DRIVEN_MIN_ABS_CORR


def data_driven_note(best: pd.Series, best_abs: pd.Series) -> str:
    lag = int(best["lag_quarters"])
    corr = float(best["corr"])
    obs = int(best["observations"])
    timing = timing_label(lag)
    low_n = " Low-n exploratory result." if obs < MIN_OBS or "low_n" in str(best["status"]) else ""
    return (
        f"{timing}; best positive lag {lag:+d}Q, corr {corr:.2f}, n={obs}.{low_n} "
        f"Strongest absolute relation is lag {int(best_abs['lag_quarters']):+d}Q, corr {float(best_abs['corr']):.2f}."
    )


def edge_row(
    edge: pd.Series,
    lag: int,
    corr: float,
    observations: int,
    beta: float,
    status: str,
    source_metric: str,
    target_metric: str,
) -> dict[str, object]:
    return {
        "source_section": edge["source_section"],
        "target_section": edge["target_section"],
        "stage": edge["stage"],
        "hypothesis": edge["hypothesis"],
        "source_metric": source_metric,
        "target_metric": target_metric,
        "lag_quarters": lag,
        "lag_interpretation": chain_lag_label(edge["source_section"], edge["target_section"], lag),
        "observations": observations,
        "corr": corr,
        "r_squared": corr * corr if not pd.isna(corr) else np.nan,
        "beta_revenue_yoy_per_1_capex_yoy": beta,
        "status": status,
    }


def choose_source_capex_transform(section_df: pd.DataFrame) -> str:
    if int(section_df["capex_yoy_pct"].notna().sum()) >= MIN_OBS:
        return "capex_yoy_pct"
    return "capex_qoq_pct"


def chain_lag_label(source: str, target: str, lag: int) -> str:
    if lag > 0:
        return f"{source} capex leads {target} revenue by {lag} quarter(s)"
    if lag < 0:
        return f"{target} revenue leads {source} capex by {abs(lag)} quarter(s)"
    return f"{source} capex and {target} revenue move in the same quarter"


def classify_edge(best_forward: pd.Series | None) -> str:
    if best_forward is None or pd.isna(best_forward["corr"]):
        return "no forward evidence"
    if int(best_forward["observations"]) < MIN_OBS:
        return "exploratory low-n"
    corr = float(best_forward["corr"])
    if corr >= 0.65:
        return "strong"
    if corr >= 0.45:
        return "moderate"
    if corr >= 0.25:
        return "weak"
    return "very weak"


def edge_note(best_forward: pd.Series | None, best_any: pd.Series | None, best_abs: pd.Series) -> str:
    if best_forward is None or pd.isna(best_forward["corr"]):
        if best_any is not None and not pd.isna(best_any["corr"]):
            return f"Positive relation exists only outside forward lags; best positive lag {int(best_any['lag_quarters'])}Q, corr {float(best_any['corr']):.2f}."
        return f"No positive forward signal. Strongest absolute relation is lag {int(best_abs['lag_quarters'])}Q, corr {float(best_abs['corr']):.2f}."
    low_n = " Low-n supplemental result; use as map hypothesis only." if int(best_forward["observations"]) < MIN_OBS else ""
    return (
        f"Forward signal at +{int(best_forward['lag_quarters'])}Q, corr {float(best_forward['corr']):.2f}, "
        f"n={int(best_forward['observations'])}.{low_n} Strongest absolute relation is lag {int(best_abs['lag_quarters'])}Q, corr {float(best_abs['corr']):.2f}."
    )


def lag_label(lag: int) -> str:
    if lag > 0:
        return f"Hyperscaler capex leads target by {lag} quarter(s)"
    if lag < 0:
        return f"Target leads hyperscaler capex by {abs(lag)} quarter(s)"
    return "Same quarter"


def interpret_signal(best_pos: pd.Series | None, best_forward: pd.Series | None, best_abs: pd.Series) -> str:
    if best_pos is None or pd.isna(best_pos["corr"]):
        return "No positive lead/lag signal with enough observations."
    lag = int(best_pos["lag_quarters"])
    corr = float(best_pos["corr"])
    strength = "strong" if corr >= 0.70 else "moderate" if corr >= 0.45 else "weak"
    direction = "후행 반응" if lag > 0 else "동분기 반응" if lag == 0 else "선행 움직임"
    forward_text = ""
    if best_forward is not None and not pd.isna(best_forward["corr"]):
        forward_text = f" Hyperscaler-leads-only best is lag {int(best_forward['lag_quarters'])}Q, corr {float(best_forward['corr']):.2f}."
    return f"{direction}; positive {strength} correlation at lag {lag}Q.{forward_text} Max absolute signal is lag {int(best_abs['lag_quarters'])}Q."


def hyperscaler_capex_series(section_quarterly: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "calendar_quarter",
        "quarter_period",
        "capex_investment_usd_m",
        "capex_valid_companies",
        "revenue_usd_m",
        "revenue_usd_m_valid_companies",
        "capex_yoy_pct",
        "revenue_usd_m_yoy_pct",
    ]
    return section_quarterly[section_quarterly["section"] == HYPERSCALER_SECTION][cols].sort_values("quarter_period")


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


def value_chain_map_svg(edge_best: pd.DataFrame) -> str:
    edges = hypothesis_timeline_edges(edge_best)
    if edges.empty:
        return '<p class="note">No hypothesis-constrained edges had enough data for timeline placement.</p>'
    return timeline_chain_map_svg(edges, "Hypothesis-constrained capex revenue value chain map", marker_id="arrow_hypothesis")


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
        source, target = visual_edge_direction(row)
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
        return '<p class="note">No data-driven forward or synchronous edges passed the map filter.</p>'
    return timeline_chain_map_svg(edges, "Data-driven capex revenue value chain map", marker_id="arrow_data", style_variant="data")


def timeline_chain_map_svg(edges: pd.DataFrame, aria_label: str, marker_id: str, style_variant: str = "standard") -> str:
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
            x = 140 + (tick - min_score) / score_span * 1920
            axis_ticks.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="42" y2="670" class="tick"/><text x="{x:.1f}" y="30" text-anchor="middle" class="axis-label">t{tick:+d}Q</text>')

    return f"""
    <svg viewBox="0 0 2200 720" role="img" aria-label="{esc(aria_label)}">
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
      <rect class="map-bg" x="0" y="0" width="2200" height="1100"/>
      {map_time_bands(quarter_scores)}
      {''.join(axis_ticks)}
      {''.join(edge_parts)}
      {''.join(label_parts)}
      {''.join(node_parts)}
    </svg>
    """


def hypothesis_timeline_edges(edge_best: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, edge in edge_best.iterrows():
        if not pd.isna(edge.get("best_forward_corr")):
            lag = int(edge["best_forward_lag_quarters"])
            timing = "source capex leads" if lag > 0 else "synchronous"
            corr = float(edge["best_forward_corr"])
            obs = int(edge["best_forward_observations"])
            signal = edge["signal_class"]
        elif not pd.isna(edge.get("best_any_corr")):
            lag = int(edge["best_any_lag_quarters"])
            timing = timing_label(lag)
            corr = float(edge["best_any_corr"])
            obs = 0
            signal = "no forward evidence"
        else:
            continue
        rows.append(
            {
                "source_section": edge["source_section"],
                "target_section": edge["target_section"],
                "source_metric": edge.get("source_metric", ""),
                "target_metric": edge.get("target_metric", ""),
                "best_lag_quarters": lag,
                "timing": timing,
                "best_corr": corr,
                "best_observations": obs,
                "signal_class": signal,
                "map_eligible": True,
            }
        )
    return pd.DataFrame(rows)


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


def map_time_bands(quarter_scores: dict[str, float]) -> str:
    if not quarter_scores:
        return ""
    min_score = math.floor(min(quarter_scores.values()))
    max_score = math.ceil(max(quarter_scores.values()))
    score_span = max(max_score - min_score, 1)
    parts = []
    for idx, tick in enumerate(range(min_score, max_score)):
        if idx % 2:
            continue
        x1 = 140 + (tick - min_score) / score_span * 1920
        x2 = 140 + (tick + 1 - min_score) / score_span * 1920
        parts.append(f'<rect class="time-band" x="{x1:.1f}" y="42" width="{x2-x1:.1f}" height="628"/>')
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
        x = int(140 + raw_scores[node] / max_score * 1920)
        available = [86, 138, 190, 242, 294, 346, 398, 450, 502, 554, 606, 658]
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
    lane_offsets = [-54, 54, -108, 108, -162, 162, -216, 216]
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
    corr = float(edge["best_corr"])
    if edge["timing"] == "target revenue leads":
        return f"rev leads {abs(lag)}Q r={corr:.2f}"
    if edge["timing"] == "synchronous":
        return f"0Q r={corr:.2f}"
    return f"capex leads {lag}Q r={corr:.2f}"


def data_driven_edge_stroke(edge: pd.Series) -> tuple[str, float, str]:
    timing = edge.get("timing")
    signal = edge.get("signal_class")
    corr = edge.get("best_corr")
    if pd.isna(corr):
        return "#9aa4a0", 1.2, "5 5"
    if signal == "exploratory low-n":
        return "#6b7280", 2.0, "2 4"
    if timing == "target revenue leads":
        return "#b03737", 2.0 + 4.0 * min(float(corr), 0.8), "3 4"
    if timing == "synchronous":
        return "#2563eb", 2.0 + 4.0 * min(float(corr), 0.8), "6 3"
    if float(corr) >= 0.65:
        return "#087f5b", 2.4 + 4.0 * min(float(corr), 0.85), ""
    return "#9a6700", 1.8 + 3.5 * min(float(corr), 0.65), "8 4"


def visual_edge_direction(edge: pd.Series) -> tuple[str, str]:
    if edge.get("timing") == "target revenue leads":
        return str(edge["target_section"]), str(edge["source_section"])
    return str(edge["source_section"]), str(edge["target_section"])


def lag_profile_svg(edge_corr: pd.DataFrame, edge_best: pd.DataFrame, limit: int = 12) -> str:
    chosen = edge_best.dropna(subset=["best_forward_corr"]).sort_values("best_forward_corr", ascending=False).head(limit)
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
        sub = edge_corr[(edge_corr["source_section"] == source) & (edge_corr["target_section"] == target)].set_index("lag_quarters")
        parts.append(f'<text x="8" y="{y_zero+4}" class="row-label">{esc(source)} → {esc(target)}</text>')
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
        lag = edge.get("best_forward_lag_quarters")
        corr = edge.get("best_forward_corr")
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


def line_chart_svg(df: pd.DataFrame) -> str:
    data = df.dropna(subset=["capex_yoy_pct"]).tail(28).copy()
    if data.empty:
        return ""
    values = data["capex_yoy_pct"].clip(-1.0, 2.5)
    width, height = 760, 180
    pad_l, pad_r, pad_t, pad_b = 46, 18, 18, 34
    x_vals = np.linspace(pad_l, width - pad_r, len(values))
    vmin, vmax = min(-0.5, float(values.min())), max(1.0, float(values.max()))

    def y(v: float) -> float:
        return pad_t + (vmax - v) / (vmax - vmin) * (height - pad_t - pad_b)

    points = " ".join(f"{x:.1f},{y(float(v)):.1f}" for x, v in zip(x_vals, values))
    zero_y = y(0)
    labels = []
    for idx in np.linspace(0, len(data) - 1, min(7, len(data))).astype(int):
        labels.append(f'<text x="{x_vals[idx]:.1f}" y="{height-10}" text-anchor="middle">{esc(data.iloc[idx]["calendar_quarter"])}</text>')
    return f"""
    <svg viewBox="0 0 {width} {height}" role="img" aria-label="Hyperscaler capex YoY line chart">
      <line x1="{pad_l}" x2="{width-pad_r}" y1="{zero_y:.1f}" y2="{zero_y:.1f}" class="axis"/>
      <polyline fill="none" stroke="#087f5b" stroke-width="3" points="{points}"/>
      <text x="4" y="{y(vmax):.1f}">{pct(vmax,0)}</text>
      <text x="4" y="{zero_y:.1f}">0%</text>
      {''.join(labels)}
    </svg>
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


def build_html(
    section_quarterly: pd.DataFrame,
    hyper_series: pd.DataFrame,
    corr_df: pd.DataFrame,
    best_df: pd.DataFrame,
    coverage: pd.DataFrame,
    edge_corr_df: pd.DataFrame,
    edge_best_df: pd.DataFrame,
    data_corr_df: pd.DataFrame,
    data_best_df: pd.DataFrame,
) -> str:
    revenue_top = metric_best(best_df, "revenue_usd_m")
    revenue_forward_top = metric_best_forward(best_df, "revenue_usd_m")
    revenue_same_or_forward_top = metric_best_same_or_forward(best_df, "revenue_usd_m")
    oi_top = metric_best(best_df, "operating_income_usd_m")
    gp_top = metric_best(best_df, "gross_profit_usd_m")

    payload = {
        "generated_at": pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d %H:%M KST"),
        "source_db": str(DB_PATH),
        "source_master": str(MASTER_PATH),
        "chain_hypotheses": VALUE_CHAIN_HYPOTHESES,
        "data_driven_filter": {
            "min_observations": MIN_OBS,
            "min_corr_for_map": DATA_DRIVEN_MIN_ABS_CORR,
            "max_map_edges": DATA_DRIVEN_MAX_MAP_EDGES,
        },
        "external_references": references_payload(),
    }
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
    svg {{ width:100%; min-width:1500px; height:auto; background:#fff; border:1px solid var(--line); border-radius:8px; }}
    svg text {{ font-size:11px; fill:var(--muted); }}
    .axis {{ stroke:#aab5ae; stroke-width:1; }}
    .two {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; align-items:start; }}
    code {{ background:#edf2ee; padding:2px 4px; border-radius:4px; }}
    @media (max-width:900px) {{ header, main {{ padding-left:18px; padding-right:18px; }} .grid, .two {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<header>
  <h1>Hyperscaler Capex vs AI Supply Chain Financial Lead-Lag</h1>
  <div class="meta">Generated {esc(payload["generated_at"])} · DB: {esc(DB_PATH.name)} · Master: {esc(MASTER_PATH.name)}</div>
</header>
<main>
  <section class="grid">
    <div class="kpi"><b>{coverage["master_companies"].sum():,.0f}</b><span>matched companies in master</span></div>
    <div class="kpi"><b>{section_quarterly["section"].nunique():,.0f}</b><span>supply-chain sections</span></div>
    <div class="kpi"><b>{section_quarterly["quarter_period"].nunique():,.0f}</b><span>calendar quarters</span></div>
    <div class="kpi"><b>{len(corr_df.dropna(subset=["corr"])):,.0f}</b><span>valid lag correlations</span></div>
  </section>

  <section>
    <h2>Executive Read</h2>
    <p>이 리포트는 주가가 아니라 분기 재무제표 데이터를 기준으로, 하이퍼스케일러 capex 증가율이 AI 공급망 각 section의 매출과 이익 지표에 몇 분기 선행/후행하는지 본다. 기본 독립변수는 <code>Hyperscalers capex YoY %</code>, 핵심 종속변수는 <code>section revenue YoY %</code>다. 첫 요약은 사용자 가정에 맞춰 <code>lag &gt; 0</code>, 즉 capex가 먼저 움직이는 경우만 따로 뽑았다.</p>
    <ul>{''.join(top_summary(best_df))}</ul>
    <p class="note">해석상 주의: 이 결과는 단변량 lead-lag correlation이다. 재고 조정, 고객 mix, 환율, 회계 분기 차이, 가격 사이클, capex 단위 차이가 섞일 수 있으므로 인과관계 증명이 아니라 “어느 section의 투자가 어느 section의 매출과 시간적으로 연결되는지”를 찾는 탐색 분석으로 봐야 한다.</p>
  </section>

  <section>
    <h2>Data-Driven Value-Chain Map</h2>
    <p>이 맵은 사용자의 가설 edge를 사용하지 않고, 가능한 모든 <code>source section capex change</code>와 <code>target section revenue YoY</code> 조합을 탐색해서 만든다. 기본 맵에는 <code>n ≥ {MIN_OBS}</code>이고 <code>corr ≥ {DATA_DRIVEN_MIN_ABS_CORR}</code>인 관계를 우선 표시한다. 왼쪽일수록 먼저 움직이는 노드이고, 노드 아래의 <code>t+…Q</code>는 선택된 edge들의 lag를 동시에 맞춘 상대적인 체인 위치다. 초록은 source capex가 target revenue를 선행, 파란 점선은 동행, 붉은 점선은 target revenue가 source capex보다 먼저 움직이는 관계, 회색 짧은 점선은 low-n 탐색 신호다.</p>
    {data_driven_chain_map_svg(data_best_df)}
    <div class="tablewrap">
      {table_html(data_best_df, [
        ("source_section", "Source capex"),
        ("target_section", "Target revenue"),
        ("source_metric", "Source transform"),
        ("timing", "Timing"),
        ("best_lag_quarters", "Best lag"),
        ("best_corr", "Corr"),
        ("best_observations", "Obs"),
        ("signal_class", "Class"),
        ("map_eligible", "Map"),
        ("interpretation", "Interpretation"),
      ], limit=40)}
    </div>
  </section>

  <section>
    <h2>Data-Driven Lag Impact Profiles</h2>
    <p>아래 그래프는 데이터 기반으로 선정된 edge의 lag별 상관계수다. +Q는 source capex가 target revenue를 선행, 0Q는 동행, -Q는 target revenue가 source capex보다 먼저 움직인다는 뜻이다.</p>
    {lag_profile_svg(data_corr_df, data_best_df.rename(columns={"best_lag_quarters": "best_forward_lag_quarters", "best_corr": "best_forward_corr"}), limit=14)}
  </section>

  <section>
    <h2>Hypothesis-Constrained Value-Chain Map</h2>
    <p>아래 맵은 사용자의 가설을 edge로 고정한 뒤, 각 edge의 <code>source capex change</code>가 <code>target revenue YoY</code>에 선행하는 가장 강한 양의 lag를 붙인 것이다. 초록 실선은 상대적으로 강한 forward evidence, 황색 점선은 약한 forward evidence, 회색 짧은 점선은 low-n exploratory evidence, 적색/회색 점선은 현재 데이터에서 forward evidence가 약하거나 부족하다는 뜻이다.</p>
    {value_chain_map_svg(edge_best_df)}
    <div class="tablewrap">
      {table_html(edge_best_df, [
        ("source_section", "Source capex"),
        ("target_section", "Target revenue"),
        ("source_metric", "Source transform"),
        ("stage", "Hypothesis stage"),
        ("signal_class", "Class"),
        ("best_forward_lag_quarters", "Forward lag"),
        ("best_forward_corr", "Forward corr"),
        ("best_forward_observations", "Obs"),
        ("best_any_lag_quarters", "Best any lag"),
        ("best_any_corr", "Best any corr"),
        ("evidence_note", "Evidence note"),
      ], limit=30)}
    </div>
  </section>

  <section>
    <h2>Lag Impact Profiles by Hypothesis Edge</h2>
    <p>각 행은 하나의 가설 edge다. 막대가 0선 위면 양의 상관, 아래면 음의 상관이다. 오른쪽 라벨은 <code>lag &gt; 0</code> 중 가장 강한 양의 상관을 표시한다.</p>
    {lag_profile_svg(edge_corr_df, edge_best_df, limit=14)}
  </section>

  <section>
    <h2>Hyperscaler Capex Series</h2>
    {line_chart_svg(hyper_series)}
    <div class="tablewrap">
      {table_html(hyper_series.tail(16), [
        ("calendar_quarter", "Quarter"),
        ("capex_investment_usd_m", "Capex investment USDm"),
        ("capex_valid_companies", "Capex contributors"),
        ("capex_yoy_pct", "Capex YoY"),
        ("revenue_usd_m", "Revenue USDm"),
        ("revenue_usd_m_yoy_pct", "Revenue YoY"),
      ])}
    </div>
  </section>

  <section>
    <h2>Revenue Lead-Lag Heatmap</h2>
    <p>셀 값은 하이퍼스케일러 capex YoY와 각 section revenue YoY의 Pearson correlation이다. +4Q는 “capex 변화가 target revenue보다 4분기 앞선다”는 뜻이고, -2Q는 target revenue가 capex보다 2분기 먼저 움직였다는 뜻이다.</p>
    <div class="tablewrap">{heatmap_html(corr_df, "revenue_usd_m")}</div>
  </section>

  <section class="two">
    <div>
      <h2>Capex-Leads Revenue Signals</h2>
      {table_html(revenue_forward_top, [
        ("section", "Section"),
        ("best_forward_lag_quarters", "Forward lag"),
        ("best_forward_corr", "Corr"),
        ("best_forward_observations", "Obs"),
        ("best_forward_lag_interpretation", "Meaning"),
      ], limit=20)}
    </div>
    <div>
      <h2>Same-Quarter or Forward Revenue</h2>
      {table_html(revenue_same_or_forward_top, [
        ("section", "Section"),
        ("best_same_or_forward_lag_quarters", "Lag"),
        ("best_same_or_forward_corr", "Corr"),
        ("best_same_or_forward_observations", "Obs"),
        ("best_same_or_forward_lag_interpretation", "Meaning"),
      ], limit=20)}
    </div>
  </section>

  <section>
    <h2>Top Profit Signals</h2>
    {table_html(pd.concat([gp_top.head(10), oi_top.head(10)], ignore_index=True), [
      ("section", "Section"),
      ("target_metric_label", "Metric"),
      ("target_transform", "Transform"),
      ("best_positive_lag_quarters", "Best any lag"),
      ("best_positive_corr", "Corr"),
      ("best_forward_lag_quarters", "Best forward lag"),
      ("best_forward_corr", "Forward corr"),
      ("best_positive_observations", "Obs"),
    ])}
  </section>

  <section>
    <h2>Best Signals by Section and Metric</h2>
    <div class="tablewrap">
      {table_html(best_df.sort_values(["section", "target_metric"]), [
        ("section", "Section"),
        ("target_metric_label", "Metric"),
        ("target_transform", "Transform"),
        ("best_positive_lag_quarters", "Best positive lag"),
        ("best_positive_corr", "Best positive corr"),
        ("best_positive_observations", "Obs"),
        ("best_forward_lag_quarters", "Best capex-leads lag"),
        ("best_forward_corr", "Capex-leads corr"),
        ("best_abs_lag_quarters", "Best absolute lag"),
        ("best_abs_corr", "Best absolute corr"),
        ("interpretation", "Interpretation"),
      ])}
    </div>
  </section>

  <section>
    <h2>Financial Data Coverage</h2>
    <p>section별 회사 수, 관측 분기 수, revenue/capex row 수를 확인한다. capex row가 적은 section은 lead-lag 결과가 불안정할 수 있다.</p>
    <div class="tablewrap">
      {table_html(coverage, [
        ("section", "Section"),
        ("master_companies", "Master companies"),
        ("observed_companies", "Observed companies"),
        ("first_quarter", "First qtr"),
        ("last_quarter", "Last qtr"),
        ("quarters", "Quarters"),
        ("revenue_rows", "Revenue rows"),
        ("capex_rows", "Capex rows"),
        ("revenue_yoy_obs", "Revenue YoY obs"),
        ("capex_yoy_obs", "Capex YoY obs"),
      ])}
    </div>
  </section>

  <section>
    <h2>Methodology</h2>
    <p><b>Aggregation.</b> Company financial rows are mapped to the user-defined supply-chain section in <code>company_master.xlsx</code>. Quarterly values are summed by <code>section × calendar_quarter</code>. Capex is converted to positive investment spend using absolute value because cash-flow statements can encode capex as an outflow.</p>
    <p><b>Variable transformation.</b> For capex and revenue/gross profit, the report uses year-over-year percentage change to reduce scale and seasonality effects: <code>x_t / x_(t-4) - 1</code>. For operating income and net income, the report uses year-over-year USD delta because profit can cross zero and make percentage growth unstable.</p>
    <p><b>Lead-lag convention.</b> lag +N means hyperscaler capex at quarter t is compared with target section metric at quarter t+N. lag 0 is same-quarter coupling. lag -N means the target section moved before hyperscaler capex.</p>
    <p><b>Data-driven edge discovery.</b> The data-driven map ignores the hypothesis list and evaluates every ordered section pair: <code>source section capex change(t)</code> → <code>target section revenue YoY(t+lag)</code>. For each pair, it keeps the strongest positive correlation across -4Q to +8Q, then labels timing as source-capex-leads, synchronous, or target-revenue-leads. The map filters to <code>n ≥ {MIN_OBS}</code> and <code>corr ≥ {DATA_DRIVEN_MIN_ABS_CORR}</code> for the primary picture.</p>
    <p><b>Hypothesis edge method.</b> The hypothesis-constrained chain-map section uses the directed hypothesis list supplied by the user. It reports the same lag convention, but it does not search outside those proposed edges. This makes it useful for checking whether a prior business narrative is supported, while the data-driven map is better for discovering unexpected timing.</p>
    <p><b>Capex transform fallback.</b> The primary source investment transform is <code>capex_yoy_pct</code>. If a source section has fewer than {MIN_OBS} capex YoY observations, the chain-edge analysis falls back to <code>capex_qoq_pct</code>. QoQ fallback edges are accepted with at least {MIN_SUPPLEMENTAL_OBS} overlapping observations, but if they remain below {MIN_OBS} observations they are classified as <code>exploratory low-n</code>. This is especially relevant for AI Chip, DRAM, and NAND capex, where available quarterly capex history is sparse in the current DB.</p>
    <p><b>Signal classes.</b> Forward evidence is classified from the best positive forward-lag correlation: strong ≥ 0.65, moderate ≥ 0.45, weak ≥ 0.25, very weak &lt; 0.25, and no forward evidence when no positive forward-lag correlation has enough observations. These are analytical thresholds for exploration, not literature constants.</p>
    <p><b>Files generated.</b> CSV provenance is saved beside this HTML: <code>{esc(OUT_SECTION_QUARTERLY.name)}</code>, <code>{esc(OUT_HYPERSCALER_CAPEX.name)}</code>, <code>{esc(OUT_LAG_CORR.name)}</code>, <code>{esc(OUT_BEST_SIGNALS.name)}</code>, <code>{esc(OUT_DATA_DRIVEN_EDGE_CORR.name)}</code>, <code>{esc(OUT_DATA_DRIVEN_EDGE_BEST.name)}</code>, <code>{esc(OUT_CHAIN_EDGE_CORR.name)}</code>, <code>{esc(OUT_CHAIN_EDGE_BEST.name)}</code>, and <code>{esc(OUT_COVERAGE.name)}</code>.</p>
  </section>

  <section>
    <h2>References and Interpretation Anchors</h2>
    <p>아래 문헌은 모델 계수의 근거가 아니라, 왜 lead-lag/cross-correlation 접근을 쓰는지와 AI 인프라 공급망 edge를 어떻게 해석할지에 대한 참고 anchor다. 실제 상관계수와 lag는 이 폴더의 DB 분석 결과에서만 산출했다.</p>
    {references_html()}
  </section>

  <script type="application/json" id="report-provenance">{esc(json.dumps(payload, ensure_ascii=False, indent=2))}</script>
</main>
</body>
</html>
"""


def write_outputs() -> None:
    matched, financials = load_data()
    section_quarterly = aggregate_section_quarterly(financials)
    coverage = coverage_table(financials, section_quarterly, matched)
    hyper_series = hyperscaler_capex_series(section_quarterly)
    corr_df, best_df = lag_correlations(section_quarterly)
    edge_corr_df, edge_best_df = value_chain_lag_correlations(section_quarterly)
    data_corr_df, data_best_df = data_driven_lag_correlations(section_quarterly)

    csv_section = section_quarterly.copy()
    csv_section["quarter_period"] = csv_section["quarter_period"].astype(str)
    csv_section.to_csv(OUT_SECTION_QUARTERLY, index=False)
    hyper_csv = hyper_series.copy()
    hyper_csv["quarter_period"] = hyper_csv["quarter_period"].astype(str)
    hyper_csv.to_csv(OUT_HYPERSCALER_CAPEX, index=False)
    corr_df.to_csv(OUT_LAG_CORR, index=False)
    best_df.to_csv(OUT_BEST_SIGNALS, index=False)
    edge_corr_df.to_csv(OUT_CHAIN_EDGE_CORR, index=False)
    edge_best_df.to_csv(OUT_CHAIN_EDGE_BEST, index=False)
    data_corr_df.to_csv(OUT_DATA_DRIVEN_EDGE_CORR, index=False)
    data_best_df.to_csv(OUT_DATA_DRIVEN_EDGE_BEST, index=False)
    coverage.to_csv(OUT_COVERAGE, index=False)

    OUT_HTML.write_text(
        build_html(section_quarterly, hyper_series, corr_df, best_df, coverage, edge_corr_df, edge_best_df, data_corr_df, data_best_df),
        encoding="utf-8",
    )

    print(f"Wrote {OUT_HTML}")
    print(f"Valid lag correlations: {corr_df['corr'].notna().sum():,}")
    print("Top capex-leads revenue signals:")
    cols = ["section", "best_forward_lag_quarters", "best_forward_corr", "best_forward_observations"]
    print(metric_best_forward(best_df, "revenue_usd_m")[cols].head(10).to_string(index=False))
    print("Top value-chain edge signals:")
    edge_cols = ["source_section", "target_section", "best_forward_lag_quarters", "best_forward_corr", "signal_class"]
    print(edge_best_df[edge_cols].head(10).to_string(index=False))
    print("Top data-driven edges:")
    data_cols = ["source_section", "target_section", "best_lag_quarters", "timing", "best_corr", "best_observations", "signal_class", "map_eligible"]
    print(data_best_df[data_cols].head(12).to_string(index=False))


if __name__ == "__main__":
    write_outputs()
