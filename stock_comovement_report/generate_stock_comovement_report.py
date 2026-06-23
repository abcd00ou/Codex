from __future__ import annotations

import html
import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DB_PATH = Path("/Users/idongseong/Claude/agents/data/dba/financials.db")
MASTER_PATH = Path("/Users/idongseong/Downloads/company_master.xlsx")
OUT_HTML = ROOT / "stock_comovement_coupling_report.html"
OUT_GROUP_CSV = ROOT / "group_comovement_summary.csv"
OUT_PAIR_CSV = ROOT / "pairwise_comovement_summary.csv"
OUT_MEMBER_CSV = ROOT / "member_coupling_summary.csv"
OUT_YEARLY_CSV = ROOT / "yearly_group_coupling_summary.csv"
OUT_FREQUENCY_CSV = ROOT / "frequency_group_coupling_summary.csv"
OUT_BOTTLENECK_CSV = ROOT / "bottleneck_interpretation_summary.csv"
OUT_ROLE_DEEPDIVE_CSV = ROOT / "member_role_financial_deepdive.csv"
OUT_COMPANY_WEIGHT_CSV = ROOT / "member_company_financial_weights.csv"
OUT_ANNUAL_BALANCE_CSV = ROOT / "annual_financial_balance_vs_coupling.csv"
OUT_FUNDAMENTAL_MOMENTUM_CSV = ROOT / "section_fundamental_momentum_vs_comovement.csv"
OUT_COMPANY_YEARLY_GROWTH_CSV = ROOT / "company_yearly_growth_vs_comovement.csv"
OUT_COVERAGE_CSV = ROOT / "ticker_coverage_used.csv"
OUT_REFERENCES_MD = ROOT / "comovement_methodology_references.md"

ANALYSIS_START_DATE = "2016-01-01"
BASE_FREQUENCY = "monthly"
MIN_OBS = 18
YEARLY_MIN_OBS = 4
ROLLING_WINDOW = 12
STRONG_CORR = 0.65
COUPLING_CORR = 0.50
CORE_MEAN_CORR = 0.50
PARTIAL_MEAN_CORR = 0.35
STRONG_LINK_CORR = 0.65
FINANCIAL_WEIGHT_YEAR = 2025
FINANCIAL_WEIGHT_QUARTER = 4

EXTERNAL_COLUMN_ALIASES = {
    "date": ["date", "price_date", "날짜"],
    "section": ["section", "group", "group_3", "섹션"],
    "company_name": ["companyname", "company_name", "company", "name", "회사명"],
    "ticker": ["ticker", "symbol", "티커"],
    "item": ["item", "fs_item", "metric", "항목"],
    "value": ["value", "값"],
    "adjusted_close": ["adjusted close", "adjusted_close", "adj_close", "adj_close_usd", "close", "수정종가"],
}

ITEM_ALIASES = {
    "adjusted_close": "adjusted_close",
    "adjusted close": "adjusted_close",
    "adj_close": "adjusted_close",
    "adj close": "adjusted_close",
    "adj_close_usd": "adjusted_close",
    "close": "adjusted_close",
    "revenue": "revenue_usd_m",
    "sales": "revenue_usd_m",
    "매출": "revenue_usd_m",
    "capex": "capex_usd_m",
    "capital expenditure": "capex_usd_m",
    "capital_expenditure": "capex_usd_m",
    "operating income": "operating_income_usd_m",
    "operating_income": "operating_income_usd_m",
    "operating_income_usd_m": "operating_income_usd_m",
    "net income": "net_income_usd_m",
    "net_income": "net_income_usd_m",
    "net_income_usd_m": "net_income_usd_m",
}

FX_LOCAL_PER_USD_APPROX = {
    "USD": {year: 1.0 for year in range(2016, 2027)},
    "KRW": {2016: 1160, 2017: 1130, 2018: 1100, 2019: 1165, 2020: 1180, 2021: 1145, 2022: 1290, 2023: 1305, 2024: 1365, 2025: 1380, 2026: 1370},
    "TWD": {2016: 32.3, 2017: 30.4, 2018: 30.2, 2019: 30.9, 2020: 29.5, 2021: 28.0, 2022: 29.8, 2023: 31.2, 2024: 32.1, 2025: 32.5, 2026: 32.3},
    "JPY": {2016: 109, 2017: 112, 2018: 110, 2019: 109, 2020: 107, 2021: 110, 2022: 131, 2023: 141, 2024: 151, 2025: 149, 2026: 145},
    "EUR": {2016: 0.90, 2017: 0.89, 2018: 0.85, 2019: 0.89, 2020: 0.88, 2021: 0.85, 2022: 0.95, 2023: 0.92, 2024: 0.92, 2025: 0.92, 2026: 0.92},
    "CNY": {2016: 6.64, 2017: 6.76, 2018: 6.62, 2019: 6.91, 2020: 6.90, 2021: 6.45, 2022: 6.73, 2023: 7.08, 2024: 7.20, 2025: 7.20, 2026: 7.15},
    "HKD": {year: 7.80 for year in range(2016, 2027)},
    "SEK": {2016: 8.56, 2017: 8.54, 2018: 8.69, 2019: 9.46, 2020: 9.20, 2021: 8.58, 2022: 10.10, 2023: 10.60, 2024: 10.50, 2025: 10.50, 2026: 10.40},
    "CHF": {2016: 0.99, 2017: 0.98, 2018: 0.98, 2019: 0.99, 2020: 0.94, 2021: 0.91, 2022: 0.95, 2023: 0.90, 2024: 0.88, 2025: 0.88, 2026: 0.88},
}


@dataclass(frozen=True)
class GroupResult:
    group: str
    tickers: list[str]
    companies: list[str]
    n_assets: int
    common_days: int
    start_date: str
    end_date: str
    avg_pair_corr: float
    median_pair_corr: float
    max_pair_corr: float
    min_pair_corr: float
    strong_pair_share: float
    pc1_share: float
    latest_rolling_corr: float
    rolling_min: float
    rolling_max: float
    classification: str
    interpretation: str


def esc(x: object) -> str:
    return html.escape("" if pd.isna(x) else str(x))


def pct(x: float) -> str:
    if pd.isna(x):
        return "-"
    return f"{x * 100:.1f}%"


def num(x: float, digits: int = 2) -> str:
    if pd.isna(x):
        return "-"
    return f"{x:.{digits}f}"


def norm_ticker(ticker: str) -> str:
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


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master = pd.read_excel(MASTER_PATH)
    master["ticker_norm"] = master["ticker"].map(norm_ticker)

    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query("select ticker, slug, name, segments, hq_country from companies", conn)
        prices = pd.read_sql_query(
            """
            select ticker, price_date, adj_close_usd, market_cap_usd_b, currency
            from stock_prices
            where adj_close_usd is not null
            order by ticker, price_date
            """,
            conn,
        )
        quarterly_financials = pd.read_sql_query(
            """
            select ticker, fiscal_year, fiscal_quarter, period_end_date, calendar_quarter,
                   revenue_usd_m, operating_income_usd_m, net_income_usd_m
            from quarterly_financials
            order by ticker, fiscal_year, fiscal_quarter, period_end_date
            """,
            conn,
        )
        annual_financials = pd.read_sql_query(
            """
            select ticker, fiscal_year, period_end_date,
                   revenue_usd_m, operating_income_usd_m, net_income_usd_m
            from annual_financials
            order by ticker, fiscal_year, period_end_date
            """,
            conn,
        )
    prices["price_date"] = pd.to_datetime(prices["price_date"])
    prices["adj_close_usd"] = pd.to_numeric(prices["adj_close_usd"], errors="coerce")
    prices = prices[prices["price_date"] >= pd.Timestamp(ANALYSIS_START_DATE)]

    db_tickers = set(companies["ticker"])
    suffix_lookup = {}
    for db_ticker in db_tickers:
        suffix_lookup.setdefault(db_ticker.split(":")[-1].upper(), db_ticker)

    def match_db_ticker(row: pd.Series) -> str | None:
        n = row["ticker_norm"]
        if n in db_tickers:
            return n
        raw = str(row["ticker"]).strip().upper()
        if raw in suffix_lookup:
            return suffix_lookup[raw]
        return None

    master["db_ticker"] = master.apply(match_db_ticker, axis=1)
    matched = master.dropna(subset=["db_ticker"]).merge(companies, left_on="db_ticker", right_on="ticker", how="left")
    return matched, companies, prices, quarterly_financials, annual_financials


def _normalized_column_lookup(df: pd.DataFrame) -> dict[str, str]:
    return {str(col).strip().lower().replace("_", " "): col for col in df.columns}


def _resolve_external_column(df: pd.DataFrame, field: str) -> str:
    lookup = _normalized_column_lookup(df)
    for alias in EXTERNAL_COLUMN_ALIASES[field]:
        key = alias.strip().lower().replace("_", " ")
        if key in lookup:
            return lookup[key]
    expected = ", ".join(EXTERNAL_COLUMN_ALIASES[field])
    raise ValueError(f"Missing required dataframe column for {field}. Expected one of: {expected}")


def _optional_external_column(df: pd.DataFrame, field: str) -> str | None:
    try:
        return _resolve_external_column(df, field)
    except ValueError:
        return None


def normalize_external_item(value: object) -> str | None:
    if pd.isna(value):
        return None
    key = str(value).strip().lower().replace("-", " ").replace("_", " ")
    key = " ".join(key.split())
    return ITEM_ALIASES.get(key) or ITEM_ALIASES.get(key.replace(" ", "_"))


def normalize_price_dataframe(raw: pd.DataFrame, analysis_start_date: str | None = "2012-01-01") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert a generic price DataFrame into the internal matched/prices schema.

    Required logical columns are date, section, ticker, and adjusted close.
    companyname is optional; ticker is used as the display name when absent.
    Column names are matched case-insensitively and may use spaces or underscores.
    """
    if raw.empty:
        raise ValueError("Input dataframe is empty.")

    date_col = _resolve_external_column(raw, "date")
    section_col = _resolve_external_column(raw, "section")
    company_col = _optional_external_column(raw, "company_name")
    ticker_col = _resolve_external_column(raw, "ticker")
    price_col = _resolve_external_column(raw, "adjusted_close")

    columns = [date_col, section_col, ticker_col, price_col]
    if company_col:
        columns.insert(2, company_col)
    data = raw[columns].copy()
    data.columns = ["price_date", "group_3", "company_name", "ticker", "adj_close_usd"] if company_col else ["price_date", "group_3", "ticker", "adj_close_usd"]
    data["price_date"] = pd.to_datetime(data["price_date"], errors="coerce")
    data["group_3"] = data["group_3"].astype(str).str.strip()
    data["ticker"] = data["ticker"].astype(str).str.strip().str.upper()
    if "company_name" not in data.columns:
        data["company_name"] = data["ticker"]
    data["company_name"] = data["company_name"].astype(str).str.strip()
    data["adj_close_usd"] = pd.to_numeric(data["adj_close_usd"], errors="coerce")
    data = data.dropna(subset=["price_date", "group_3", "company_name", "ticker", "adj_close_usd"])
    if analysis_start_date:
        data = data[data["price_date"] >= pd.Timestamp(analysis_start_date)]
    if data.empty:
        raise ValueError("No valid price rows remain after cleaning and date filtering.")
    data = data.sort_values(["ticker", "price_date", "group_3", "company_name"])

    matched = (
        data[["group_3", "company_name", "ticker"]]
        .drop_duplicates()
        .rename(columns={"ticker": "ticker_x"})
        .sort_values(["group_3", "company_name", "ticker_x"])
    )
    matched["db_ticker"] = matched["ticker_x"]
    matched["display_name"] = matched["company_name"]

    prices = (
        data.rename(columns={"ticker": "db_ticker"})[["db_ticker", "price_date", "adj_close_usd"]]
        .rename(columns={"db_ticker": "ticker"})
        .sort_values(["ticker", "price_date"])
    )
    prices["market_cap_usd_b"] = np.nan
    return matched, prices


def normalize_long_item_dataframe(
    raw: pd.DataFrame,
    analysis_start_date: str | None = "2012-01-01",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Normalize ticker-section-item-date-value rows into price and financial inputs.

    Expected logical columns:
    - ticker
    - section
    - item
    - date
    - value

    Supported item values include adjusted_close, revenue, capex, operating income, and net income.
    Financial rows are converted into both quarterly inputs and annual inputs:
    - quarterly rows feed section momentum and 2025 Q4 financial-weight views
    - annual rows feed company annual YoY growth views; if the input is quarterly,
      annual values are summed by ticker-year.
    """
    if raw.empty:
        raise ValueError("Input dataframe is empty.")
    ticker_col = _resolve_external_column(raw, "ticker")
    section_col = _resolve_external_column(raw, "section")
    item_col = _resolve_external_column(raw, "item")
    date_col = _resolve_external_column(raw, "date")
    value_col = _resolve_external_column(raw, "value")
    company_col = _optional_external_column(raw, "company_name")

    columns = [ticker_col, section_col, item_col, date_col, value_col]
    if company_col:
        columns.append(company_col)
    data = raw[columns].copy()
    rename = {
        ticker_col: "ticker",
        section_col: "group_3",
        item_col: "item",
        date_col: "date",
        value_col: "value",
    }
    if company_col:
        rename[company_col] = "company_name"
    data = data.rename(columns=rename)
    data["ticker"] = data["ticker"].astype(str).str.strip().str.upper()
    data["group_3"] = data["group_3"].astype(str).str.strip()
    data["metric"] = data["item"].map(normalize_external_item)
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    if "company_name" not in data.columns:
        data["company_name"] = data["ticker"]
    data["company_name"] = data["company_name"].astype(str).str.strip()
    data = data.dropna(subset=["ticker", "group_3", "metric", "date", "value"])
    if analysis_start_date:
        data = data[data["date"] >= pd.Timestamp(analysis_start_date)]
    if data.empty:
        raise ValueError("No valid rows remain after cleaning and date filtering.")

    price_rows = data[data["metric"] == "adjusted_close"].copy()
    if price_rows.empty:
        raise ValueError("Long dataframe must include item='adjusted_close' rows for price comovement.")
    price_wide = price_rows.rename(columns={"date": "price_date", "value": "adj_close_usd"})[
        ["price_date", "group_3", "company_name", "ticker", "adj_close_usd"]
    ]
    matched, prices = normalize_price_dataframe(price_wide, analysis_start_date=None)

    financial_rows = data[data["metric"].isin(["revenue_usd_m", "capex_usd_m", "operating_income_usd_m", "net_income_usd_m"])].copy()
    if financial_rows.empty:
        quarterly_financials = pd.DataFrame(
            columns=["ticker", "fiscal_year", "fiscal_quarter", "period_end_date", "calendar_quarter", "revenue_usd_m", "capex_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        )
        annual_financials = pd.DataFrame(
            columns=["ticker", "fiscal_year", "period_end_date", "revenue_usd_m", "capex_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        )
    else:
        financial_rows["fiscal_year"] = financial_rows["date"].dt.year
        financial_rows["fiscal_quarter"] = financial_rows["date"].dt.quarter
        financial_rows["calendar_quarter"] = financial_rows["date"].dt.to_period("Q").astype(str)
        quarterly_financials = (
            financial_rows.pivot_table(
                index=["ticker", "fiscal_year", "fiscal_quarter", "calendar_quarter"],
                columns="metric",
                values="value",
                aggfunc="last",
            )
            .reset_index()
            .rename_axis(None, axis=1)
        )
        period_end = financial_rows.groupby(["ticker", "fiscal_year", "fiscal_quarter"])["date"].max().reset_index().rename(columns={"date": "period_end_date"})
        quarterly_financials = quarterly_financials.merge(period_end, on=["ticker", "fiscal_year", "fiscal_quarter"], how="left")
        for col in ["revenue_usd_m", "capex_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
            if col not in quarterly_financials.columns:
                quarterly_financials[col] = np.nan
        quarterly_financials = quarterly_financials[
            ["ticker", "fiscal_year", "fiscal_quarter", "period_end_date", "calendar_quarter", "revenue_usd_m", "capex_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        ]
        annual_financials = (
            financial_rows.pivot_table(
                index=["ticker", "fiscal_year"],
                columns="metric",
                values="value",
                aggfunc="sum",
            )
            .reset_index()
            .rename_axis(None, axis=1)
        )
        annual_period_end = financial_rows.groupby(["ticker", "fiscal_year"])["date"].max().reset_index().rename(columns={"date": "period_end_date"})
        annual_financials = annual_financials.merge(annual_period_end, on=["ticker", "fiscal_year"], how="left")
        for col in ["revenue_usd_m", "capex_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
            if col not in annual_financials.columns:
                annual_financials[col] = np.nan
        annual_financials = annual_financials[
            ["ticker", "fiscal_year", "period_end_date", "revenue_usd_m", "capex_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        ]
    return matched, prices, quarterly_financials, annual_financials


def price_matrix(prices: pd.DataFrame, tickers: list[str], frequency: str = "daily") -> pd.DataFrame:
    px_data = prices[prices["ticker"].isin(tickers)].copy()
    px_data["price_date"] = pd.to_datetime(px_data["price_date"], errors="coerce")
    px_data["adj_close_usd"] = pd.to_numeric(px_data["adj_close_usd"], errors="coerce")
    px_data = px_data.dropna(subset=["ticker", "price_date", "adj_close_usd"])
    px = px_data.pivot_table(
        index="price_date",
        columns="ticker",
        values="adj_close_usd",
        aggfunc="last",
    ).sort_index()
    if frequency == "weekly":
        px = px.resample("W-FRI").last()
    elif frequency == "monthly":
        monthly = px.resample("ME").last()
        actual_month_ends = px.dropna(how="all").groupby(px.dropna(how="all").index.to_period("M")).apply(lambda frame: frame.index.max())
        monthly.index = pd.DatetimeIndex([actual_month_ends.get(period, label) for period, label in zip(monthly.index.to_period("M"), monthly.index)])
        px = monthly
    elif frequency != "daily":
        raise ValueError(f"Unsupported frequency: {frequency}")
    returns = np.log(px).diff()
    returns = returns.replace([np.inf, -np.inf], np.nan)
    return returns


def pairwise_rows(group: str, returns: pd.DataFrame, names: dict[str, str]) -> list[dict[str, object]]:
    rows = []
    cols = list(returns.columns)
    for i, left in enumerate(cols):
        for right in cols[i + 1 :]:
            pair = returns[[left, right]].dropna()
            if len(pair) < MIN_OBS:
                continue
            corr = pair[left].corr(pair[right])
            beta = pair[left].cov(pair[right]) / pair[right].var() if pair[right].var() else np.nan
            same_direction = (np.sign(pair[left]) == np.sign(pair[right])).mean()
            rows.append(
                {
                    "group": group,
                    "left_ticker": left,
                    "left_company": names.get(left, left),
                    "right_ticker": right,
                    "right_company": names.get(right, right),
                    "observations": len(pair),
                    "start_date": pair.index.min().date().isoformat(),
                    "end_date": pair.index.max().date().isoformat(),
                    "pearson_corr": corr,
                    "beta_left_to_right": beta,
                    "same_direction_share": same_direction,
                }
            )
    return rows


def rolling_avg_pair_corr(returns: pd.DataFrame, window: int = ROLLING_WINDOW) -> pd.Series:
    cols = list(returns.columns)
    values = []
    dates = []
    for end in range(window, len(returns) + 1):
        sub = returns.iloc[end - window : end].dropna(axis=1, thresh=max(6, window // 2))
        if sub.shape[1] < 2:
            continue
        corr = sub.corr()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
        if len(upper):
            values.append(float(upper.mean()))
            dates.append(returns.index[end - 1])
    return pd.Series(values, index=dates, dtype=float)


def pc1_explained_share(returns: pd.DataFrame, min_obs: int = MIN_OBS) -> float:
    clean = returns.dropna()
    if clean.shape[0] < min_obs or clean.shape[1] < 2:
        return np.nan
    z = (clean - clean.mean()) / clean.std(ddof=0)
    z = z.dropna(axis=1)
    if z.shape[1] < 2:
        return np.nan
    corr = np.corrcoef(z.values, rowvar=False)
    eigvals = np.linalg.eigvalsh(corr)
    return float(eigvals[-1] / eigvals.sum())


def pc1_loadings(returns: pd.DataFrame) -> dict[str, float]:
    clean = returns.dropna()
    if clean.shape[0] < MIN_OBS or clean.shape[1] < 2:
        return {}
    z = (clean - clean.mean()) / clean.std(ddof=0)
    z = z.dropna(axis=1)
    if z.shape[1] < 2:
        return {}
    corr = np.corrcoef(z.values, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(corr)
    vec = eigvecs[:, np.argmax(eigvals)]
    if vec.sum() < 0:
        vec = -vec
    return {ticker: float(loading) for ticker, loading in zip(z.columns, vec)}


def member_rows(group: str, returns: pd.DataFrame, pair_df: pd.DataFrame, names: dict[str, str]) -> list[dict[str, object]]:
    loadings = pc1_loadings(returns)
    rows = []
    for ticker in returns.columns:
        pair_subset = pair_df[(pair_df["left_ticker"] == ticker) | (pair_df["right_ticker"] == ticker)]
        if pair_subset.empty:
            continue
        mean_corr = float(pair_subset["pearson_corr"].mean())
        median_corr = float(pair_subset["pearson_corr"].median())
        max_corr = float(pair_subset["pearson_corr"].max())
        strong_links = int((pair_subset["pearson_corr"] >= STRONG_LINK_CORR).sum())
        if mean_corr >= CORE_MEAN_CORR or strong_links >= 2:
            role = "coupling core"
        elif mean_corr >= PARTIAL_MEAN_CORR or max_corr >= 0.55:
            role = "partial / bridge"
        else:
            role = "weakly coupled"
        best_row = pair_subset.loc[pair_subset["pearson_corr"].idxmax()]
        peer = best_row["right_ticker"] if best_row["left_ticker"] == ticker else best_row["left_ticker"]
        rows.append(
            {
                "group": group,
                "ticker": ticker,
                "company": names.get(ticker, ticker),
                "member_role": role,
                "mean_corr_to_group": mean_corr,
                "median_corr_to_group": median_corr,
                "max_corr_to_peer": max_corr,
                "strong_link_count": strong_links,
                "pc1_loading": loadings.get(ticker, np.nan),
                "best_coupled_peer": peer,
                "best_coupled_peer_company": names.get(peer, peer),
            }
        )
    return rows


def yearly_group_rows(group: str, returns: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for year, sub in returns.groupby(returns.index.year):
        sub = sub.dropna(axis=1, thresh=YEARLY_MIN_OBS)
        if sub.shape[1] < 2 or len(sub) < YEARLY_MIN_OBS:
            continue
        pair_corrs = []
        cols = list(sub.columns)
        for i, left in enumerate(cols):
            for right in cols[i + 1 :]:
                pair = sub[[left, right]].dropna()
                if len(pair) >= YEARLY_MIN_OBS:
                    pair_corrs.append(pair[left].corr(pair[right]))
        if not pair_corrs:
            continue
        pc1 = pc1_explained_share(sub, min_obs=YEARLY_MIN_OBS)
        rows.append(
            {
                "group": group,
                "year": int(year),
                "n_assets": len(cols),
                "observations": int(len(sub)),
                "avg_pair_corr": float(np.nanmean(pair_corrs)),
                "median_pair_corr": float(np.nanmedian(pair_corrs)),
                "max_pair_corr": float(np.nanmax(pair_corrs)),
                "min_pair_corr": float(np.nanmin(pair_corrs)),
                "pc1_share": pc1,
                "strong_pair_share": float(np.mean([x >= STRONG_LINK_CORR for x in pair_corrs])),
            }
        )
    return rows


def yearly_scatter_rows(group: str, returns: pd.DataFrame, names: dict[str, str]) -> list[dict[str, object]]:
    rows = []
    for year, sub in returns.groupby(returns.index.year):
        sub = sub.dropna(axis=1, thresh=YEARLY_MIN_OBS)
        if sub.shape[1] < 2 or len(sub) < YEARLY_MIN_OBS:
            continue
        group_avg = sub.mean(axis=1, skipna=True)
        for date, values in sub.iterrows():
            avg = group_avg.loc[date]
            if pd.isna(avg):
                continue
            for ticker, value in values.dropna().items():
                rows.append(
                    {
                        "group": group,
                        "year": int(year),
                        "date": date.date().isoformat(),
                        "ticker": ticker,
                        "company": names.get(ticker, ticker),
                        "group_return_pct": float(avg * 100),
                        "company_return_pct": float(value * 100),
                    }
                )
    return rows


def summarize_group_frequency(group: str, returns: pd.DataFrame, min_obs: int) -> dict[str, object] | None:
    returns = returns.dropna(axis=1, thresh=min_obs)
    if returns.shape[1] < 2:
        return None
    pair_corrs = []
    cols = list(returns.columns)
    for i, left in enumerate(cols):
        for right in cols[i + 1 :]:
            pair = returns[[left, right]].dropna()
            if len(pair) >= min_obs:
                pair_corrs.append(pair[left].corr(pair[right]))
    if not pair_corrs:
        return None
    common = returns.dropna()
    if len(common) < min_obs:
        common = returns.dropna(thresh=2)
    pc1 = pc1_explained_share(returns) if len(common) >= min_obs else np.nan
    return {
        "group": group,
        "n_assets": len(cols),
        "observations": int(len(common)),
        "start_date": common.index.min().date().isoformat() if len(common) else "",
        "end_date": common.index.max().date().isoformat() if len(common) else "",
        "avg_pair_corr": float(np.nanmean(pair_corrs)),
        "median_pair_corr": float(np.nanmedian(pair_corrs)),
        "max_pair_corr": float(np.nanmax(pair_corrs)),
        "min_pair_corr": float(np.nanmin(pair_corrs)),
        "pc1_share": pc1,
        "strong_pair_share": float(np.mean([x >= STRONG_LINK_CORR for x in pair_corrs])),
    }


def frequency_group_rows(group: str, prices: pd.DataFrame, tickers: list[str]) -> list[dict[str, object]]:
    configs = [
        ("daily", MIN_OBS),
        ("weekly", 52),
        ("monthly", MIN_OBS),
    ]
    rows = []
    for frequency, min_obs in configs:
        returns = price_matrix(prices, tickers, frequency=frequency)
        summary = summarize_group_frequency(group, returns, min_obs=min_obs)
        if summary is not None:
            summary["frequency"] = frequency
            rows.append(summary)
    return rows


def selected_quarter_financials(
    quarterly_financials: pd.DataFrame | None,
    fiscal_year: int = FINANCIAL_WEIGHT_YEAR,
    fiscal_quarter: int = FINANCIAL_WEIGHT_QUARTER,
) -> pd.DataFrame:
    if quarterly_financials is None or quarterly_financials.empty:
        return pd.DataFrame(
            columns=["ticker_x", "financial_year", "financial_quarter", "financial_period", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        )
    fin = quarterly_financials.copy()
    fin["ticker_x"] = fin["ticker"].astype(str).str.strip().str.upper()
    fin["period_end_date"] = pd.to_datetime(fin["period_end_date"], errors="coerce")
    if "fiscal_quarter" not in fin.columns:
        fin["fiscal_quarter"] = fin["period_end_date"].dt.quarter
    if "calendar_quarter" not in fin.columns:
        fin["calendar_quarter"] = pd.to_datetime(fin["period_end_date"], errors="coerce").dt.to_period("Q").astype(str)
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        fin[col] = pd.to_numeric(fin[col], errors="coerce")
    fin = fin.dropna(subset=["ticker_x", "fiscal_year", "fiscal_quarter"])
    fin["_has_metric"] = fin[["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]].notna().any(axis=1)
    fin = fin[fin["_has_metric"]]
    if fin.empty:
        return pd.DataFrame(
            columns=["ticker_x", "financial_year", "financial_quarter", "financial_period", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        )
    fin = fin[(fin["fiscal_year"].astype(int) == int(fiscal_year)) & (fin["fiscal_quarter"].astype(int) == int(fiscal_quarter))]
    if fin.empty:
        return pd.DataFrame(
            columns=["ticker_x", "financial_year", "financial_quarter", "financial_period", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        )
    fin = fin.sort_values(["ticker_x", "fiscal_year", "fiscal_quarter", "period_end_date"])
    selected = fin.groupby("ticker_x", as_index=False).tail(1)
    selected = selected.rename(columns={"fiscal_year": "financial_year", "fiscal_quarter": "financial_quarter", "calendar_quarter": "financial_period"})
    return selected[
        ["ticker_x", "financial_year", "financial_quarter", "financial_period", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
    ]


def selected_annual_financials(annual_financials: pd.DataFrame | None, fiscal_year: int = FINANCIAL_WEIGHT_YEAR) -> pd.DataFrame:
    if annual_financials is None or annual_financials.empty:
        return pd.DataFrame(
            columns=["ticker_x", "financial_year", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        )
    fin = annual_financials.copy()
    fin["ticker_x"] = fin["ticker"].astype(str).str.strip().str.upper()
    fin["period_end_date"] = pd.to_datetime(fin["period_end_date"], errors="coerce")
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        fin[col] = pd.to_numeric(fin[col], errors="coerce")
    fin = fin.dropna(subset=["ticker_x", "fiscal_year"])
    fin = fin[fin["fiscal_year"].astype(int) == int(fiscal_year)]
    fin["_has_metric"] = fin[["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]].notna().any(axis=1)
    fin = fin[fin["_has_metric"]]
    if fin.empty:
        return pd.DataFrame(
            columns=["ticker_x", "financial_year", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
        )
    selected = fin.sort_values(["ticker_x", "fiscal_year", "period_end_date"]).groupby("ticker_x", as_index=False).tail(1)
    return selected.rename(columns={"fiscal_year": "financial_year"})[
        ["ticker_x", "financial_year", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
    ]


def latest_market_caps(prices: pd.DataFrame) -> pd.DataFrame:
    if "market_cap_usd_b" not in prices.columns:
        return pd.DataFrame(columns=["db_ticker", "market_cap_date", "market_cap_usd_b"])
    caps = prices[["ticker", "price_date", "market_cap_usd_b"]].copy()
    caps["market_cap_usd_b"] = pd.to_numeric(caps["market_cap_usd_b"], errors="coerce")
    caps["price_date"] = pd.to_datetime(caps["price_date"], errors="coerce")
    caps = caps.dropna(subset=["ticker", "price_date", "market_cap_usd_b"])
    if caps.empty:
        return pd.DataFrame(columns=["db_ticker", "market_cap_date", "market_cap_usd_b"])
    caps = caps.sort_values(["ticker", "price_date"]).groupby("ticker", as_index=False).tail(1)
    return caps.rename(columns={"ticker": "db_ticker", "price_date": "market_cap_date"})


def latest_price_currency(prices: pd.DataFrame) -> pd.DataFrame:
    if "currency" not in prices.columns:
        return pd.DataFrame(columns=["db_ticker", "financial_currency"])
    data = prices[["ticker", "price_date", "currency"]].copy()
    data["price_date"] = pd.to_datetime(data["price_date"], errors="coerce")
    data["currency"] = data["currency"].astype(str).str.strip().str.upper()
    data = data.dropna(subset=["ticker", "price_date", "currency"])
    data = data[data["currency"] != ""]
    if data.empty:
        return pd.DataFrame(columns=["db_ticker", "financial_currency"])
    latest = data.sort_values(["ticker", "price_date"]).groupby("ticker", as_index=False).tail(1)
    return latest.rename(columns={"ticker": "db_ticker", "currency": "financial_currency"})[["db_ticker", "financial_currency"]]


def approximate_fx_local_per_usd(currency: object, year: object) -> float:
    if pd.isna(currency):
        return np.nan
    currency_key = str(currency).strip().upper()
    if currency_key not in FX_LOCAL_PER_USD_APPROX:
        return np.nan
    try:
        year_int = int(year)
    except Exception:
        return np.nan
    rates = FX_LOCAL_PER_USD_APPROX[currency_key]
    if year_int in rates:
        return float(rates[year_int])
    nearest_year = min(rates, key=lambda candidate: abs(candidate - year_int))
    return float(rates[nearest_year])


def role_financial_deepdive_rows(
    member_summary: pd.DataFrame,
    matched: pd.DataFrame,
    prices: pd.DataFrame,
    financials_source: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attach latest scale metrics to coupling roles and aggregate by section-role."""
    if member_summary.empty:
        return pd.DataFrame(), pd.DataFrame()

    member_keys = (
        matched[["group_3", "ticker_x", "db_ticker"]]
        .drop_duplicates()
        .rename(columns={"group_3": "group"})
    )
    member_keys["ticker_x"] = member_keys["ticker_x"].astype(str).str.strip().str.upper()
    member_detail = member_summary.merge(member_keys, on=["group", "company", "db_ticker"], how="left") if "db_ticker" in member_summary.columns else member_summary.merge(
        member_keys,
        left_on=["group", "ticker"],
        right_on=["group", "db_ticker"],
        how="left",
    )
    if "ticker_x" not in member_detail.columns:
        member_detail["ticker_x"] = member_detail["ticker"]
    member_detail["ticker_x"] = member_detail["ticker_x"].fillna(member_detail["ticker"]).astype(str).str.strip().str.upper()

    financials = selected_quarter_financials(financials_source)
    caps = latest_market_caps(prices)
    currencies = latest_price_currency(prices)
    member_detail = (
        member_detail.merge(financials, on="ticker_x", how="left")
        .merge(caps, left_on="ticker", right_on="db_ticker", how="left")
        .merge(currencies, left_on="ticker", right_on="db_ticker", how="left", suffixes=("", "_currency"))
    )

    for col in ["market_cap_usd_b", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        if col not in member_detail.columns:
            member_detail[col] = np.nan
        member_detail[col] = pd.to_numeric(member_detail[col], errors="coerce")

    member_detail["has_financial_metric"] = member_detail[["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]].notna().any(axis=1)
    member_detail["fx_rate_local_per_usd"] = member_detail.apply(
        lambda row: approximate_fx_local_per_usd(row.get("financial_currency"), row.get("financial_year")),
        axis=1,
    )
    member_detail["financial_fx_normalized"] = member_detail["has_financial_metric"] & member_detail["fx_rate_local_per_usd"].notna()
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        member_detail[f"{col}_reported"] = member_detail[col]
        member_detail[col] = np.where(
            member_detail["financial_fx_normalized"] & member_detail[col].notna(),
            member_detail[col] / member_detail["fx_rate_local_per_usd"],
            member_detail[col],
        )

    metrics = ["market_cap_usd_b", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]
    currency_counts = member_detail.groupby("group")["financial_currency"].transform(lambda s: s.dropna().nunique())
    member_detail["mixed_financial_currency"] = currency_counts > 1
    member_detail["missing_fx_rate"] = member_detail["has_financial_metric"] & member_detail["financial_currency"].notna() & member_detail["fx_rate_local_per_usd"].isna()
    missing_fx_in_group = member_detail.groupby("group")["missing_fx_rate"].transform("any")
    for metric in metrics:
        totals = member_detail.groupby("group")[metric].transform(lambda s: s.sum(min_count=1))
        member_detail[f"{metric}_share_of_group"] = np.where(
            totals.notna() & (totals != 0) & member_detail[metric].notna() & ~missing_fx_in_group,
            member_detail[metric] / totals,
            np.nan,
        )
        share_col = f"{metric}_share_of_group"
        member_detail.loc[
            member_detail[share_col].notna() & ~member_detail[share_col].between(0, 1),
            share_col,
        ] = np.nan

    role_rows = []
    for (group, role), sub in member_detail.groupby(["group", "member_role"], dropna=False):
        group_all = member_detail[member_detail["group"] == group]
        row = {
            "group": group,
            "member_role": role,
            "members": int(len(sub)),
            "companies": ", ".join(sub["company"].dropna().astype(str).tolist()),
            "avg_mean_corr_to_group": float(sub["mean_corr_to_group"].mean()),
            "avg_pc1_loading": float(sub["pc1_loading"].mean()),
        }
        for metric in metrics:
            total = group_all[metric].sum(min_count=1)
            value = sub[metric].sum(min_count=1)
            missing_fx = bool(group_all["missing_fx_rate"].any())
            row[metric] = value
            share_value = (
                float(value / total) if not missing_fx and pd.notna(total) and total != 0 and pd.notna(value) else np.nan
            )
            row[f"{metric}_share_of_group"] = share_value if pd.isna(share_value) or 0 <= share_value <= 1 else np.nan
            row[f"{metric}_coverage"] = int(sub[metric].notna().sum())
        row["financial_currency"] = ", ".join(sorted(group_all["financial_currency"].dropna().unique()))
        row["financial_year"] = ", ".join(sorted(group_all["financial_year"].dropna().astype(int).astype(str).unique())) if "financial_year" in group_all else ""
        row["financial_quarter"] = ", ".join(sorted(group_all["financial_quarter"].dropna().astype(int).astype(str).unique())) if "financial_quarter" in group_all else ""
        row["financial_period"] = ", ".join(sorted(group_all["financial_period"].dropna().astype(str).unique())) if "financial_period" in group_all else ""
        row["mixed_financial_currency"] = bool(group_all["mixed_financial_currency"].any())
        row["financial_fx_normalized"] = bool(group_all["financial_fx_normalized"].any())
        row["missing_fx_rate"] = bool(group_all["missing_fx_rate"].any())
        role_rows.append(row)

    role_summary = pd.DataFrame(role_rows).sort_values(["group", "member_role"])
    return role_summary, member_detail


def annual_financial_balance_rows(
    member_summary: pd.DataFrame,
    matched: pd.DataFrame,
    prices: pd.DataFrame,
    annual_financials: pd.DataFrame | None,
    group_summary: pd.DataFrame,
) -> pd.DataFrame:
    if member_summary.empty or annual_financials is None or annual_financials.empty:
        return pd.DataFrame()

    member_keys = (
        matched[["group_3", "ticker_x", "db_ticker"]]
        .drop_duplicates()
        .rename(columns={"group_3": "group"})
    )
    member_keys["ticker_x"] = member_keys["ticker_x"].astype(str).str.strip().str.upper()
    detail = member_summary.merge(member_keys, on=["group", "company", "db_ticker"], how="left") if "db_ticker" in member_summary.columns else member_summary.merge(
        member_keys,
        left_on=["group", "ticker"],
        right_on=["group", "db_ticker"],
        how="left",
    )
    if "ticker_x" not in detail.columns:
        detail["ticker_x"] = detail["ticker"]
    detail["ticker_x"] = detail["ticker_x"].fillna(detail["ticker"]).astype(str).str.strip().str.upper()

    financials = selected_annual_financials(annual_financials)
    currencies = latest_price_currency(prices)
    detail = detail.merge(financials, on="ticker_x", how="left").merge(currencies, left_on="ticker", right_on="db_ticker", how="left", suffixes=("", "_currency"))
    detail["fx_rate_local_per_usd"] = detail.apply(
        lambda row: approximate_fx_local_per_usd(row.get("financial_currency"), row.get("financial_year")),
        axis=1,
    )
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        detail[col] = pd.to_numeric(detail[col], errors="coerce")
        detail[f"{col}_reported"] = detail[col]
        detail[col] = np.where(detail[col].notna() & detail["fx_rate_local_per_usd"].notna(), detail[col] / detail["fx_rate_local_per_usd"], detail[col])

    def metric_stats(sub: pd.DataFrame, metric: str) -> dict[str, object]:
        values = pd.to_numeric(sub[metric], errors="coerce").dropna()
        values = values[values > 0]
        prefix = "annual_revenue" if metric == "revenue_usd_m" else "annual_op_income"
        if values.empty:
            return {
                f"{prefix}_coverage": 0,
                f"{prefix}_hhi": np.nan,
                f"{prefix}_effective_n": np.nan,
                f"{prefix}_evenness": np.nan,
                f"{prefix}_top1_share": np.nan,
            }
        shares = values / values.sum()
        hhi = float((shares**2).sum())
        effective_n = float(1 / hhi) if hhi > 0 else np.nan
        coverage = int(len(values))
        return {
            f"{prefix}_coverage": coverage,
            f"{prefix}_hhi": hhi,
            f"{prefix}_effective_n": effective_n,
            f"{prefix}_evenness": float(effective_n / coverage) if coverage else np.nan,
            f"{prefix}_top1_share": float(shares.max()),
        }

    rows = []
    for group, sub in detail.groupby("group"):
        row = {"group": group, "financial_year": FINANCIAL_WEIGHT_YEAR}
        row.update(metric_stats(sub, "revenue_usd_m"))
        row.update(metric_stats(sub, "operating_income_usd_m"))
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    coupling_cols = ["group", "classification", "n_assets", "avg_pair_corr", "pc1_share", "strong_pair_share"]
    out = out.merge(group_summary[coupling_cols], on="group", how="left")

    def read(row: pd.Series) -> str:
        even = row.get("annual_revenue_evenness", np.nan)
        corr = row.get("avg_pair_corr", np.nan)
        if pd.isna(even) or pd.isna(corr):
            return "insufficient annual financial coverage"
        if even >= 0.55 and corr >= 0.50:
            return "consistent: balanced revenue mix with strong/moderate coupling"
        if even >= 0.55 and corr < 0.35:
            return "counterexample: balanced revenue mix but weak coupling"
        if even < 0.35 and corr >= 0.50:
            return "counterexample: concentrated revenue mix but strong/moderate coupling"
        return "mixed / inconclusive"

    out["hypothesis_read"] = out.apply(read, axis=1)
    return out.sort_values(["annual_revenue_evenness", "avg_pair_corr"], ascending=[False, False])


def quarterly_fundamental_growth_base(
    matched: pd.DataFrame,
    prices: pd.DataFrame,
    quarterly_financials: pd.DataFrame | None,
) -> pd.DataFrame:
    if quarterly_financials is None or quarterly_financials.empty:
        return pd.DataFrame()
    member_keys = (
        matched[["group_3", "display_name", "ticker_x", "db_ticker"]]
        .drop_duplicates()
        .rename(columns={"group_3": "group", "display_name": "company"})
    )
    member_keys["ticker_x"] = member_keys["ticker_x"].astype(str).str.strip().str.upper()

    fin = quarterly_financials.copy()
    fin["ticker_x"] = fin["ticker"].astype(str).str.strip().str.upper()
    fin["period_end_date"] = pd.to_datetime(fin["period_end_date"], errors="coerce")
    if "fiscal_quarter" not in fin.columns:
        fin["fiscal_quarter"] = fin["period_end_date"].dt.quarter
    if "calendar_quarter" not in fin.columns:
        fin["calendar_quarter"] = fin["period_end_date"].dt.to_period("Q").astype(str)
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        if col not in fin.columns:
            fin[col] = np.nan
        fin[col] = pd.to_numeric(fin[col], errors="coerce")

    currencies = latest_price_currency(prices)
    fin = fin.merge(member_keys, on="ticker_x", how="inner").merge(currencies, on="db_ticker", how="left")
    fin["fx_rate_local_per_usd"] = fin.apply(
        lambda row: approximate_fx_local_per_usd(row.get("financial_currency"), row.get("fiscal_year")),
        axis=1,
    )
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        fin[col] = np.where(fin[col].notna() & fin["fx_rate_local_per_usd"].notna(), fin[col] / fin["fx_rate_local_per_usd"], fin[col])
    fin["fiscal_year"] = fin["fiscal_year"].astype(int)
    fin["fiscal_quarter"] = fin["fiscal_quarter"].astype(int)
    fin["period_key"] = fin["fiscal_year"].astype(int).astype(str) + "Q" + fin["fiscal_quarter"].astype(int).astype(str)
    fin = fin.sort_values(["group", "ticker_x", "fiscal_year", "fiscal_quarter", "period_end_date"])
    for metric in ["revenue_usd_m", "operating_income_usd_m"]:
        fin[f"{metric}_qoq_base"] = fin.groupby(["group", "ticker_x"])[metric].shift(1)
        fin[f"{metric}_yoy_base"] = fin.groupby(["group", "ticker_x", "fiscal_quarter"])[metric].shift(1)
        fin[f"{metric}_qoq_growth"] = np.where(fin[f"{metric}_qoq_base"] > 0, fin[metric] / fin[f"{metric}_qoq_base"] - 1, np.nan)
        fin[f"{metric}_yoy_growth"] = np.where(fin[f"{metric}_yoy_base"] > 0, fin[metric] / fin[f"{metric}_yoy_base"] - 1, np.nan)
    return fin


def section_fundamental_momentum_rows(
    matched: pd.DataFrame,
    prices: pd.DataFrame,
    quarterly_financials: pd.DataFrame | None,
    yearly_summary: pd.DataFrame,
    group_summary: pd.DataFrame,
) -> pd.DataFrame:
    if yearly_summary.empty:
        return pd.DataFrame()
    fin = quarterly_fundamental_growth_base(matched, prices, quarterly_financials)
    if fin.empty:
        return pd.DataFrame()

    grouped = (
        fin.groupby(["group", "fiscal_year", "fiscal_quarter", "period_key"], as_index=False)
        .agg(
            revenue_usd_m=("revenue_usd_m", lambda s: s.sum(min_count=1)),
            operating_income_usd_m=("operating_income_usd_m", lambda s: s.sum(min_count=1)),
            company_coverage=("ticker_x", "nunique"),
            revenue_yoy_growth=("revenue_usd_m_yoy_growth", "mean"),
            revenue_qoq_growth=("revenue_usd_m_qoq_growth", "mean"),
            op_income_yoy_growth=("operating_income_usd_m_yoy_growth", "mean"),
            op_income_qoq_growth=("operating_income_usd_m_qoq_growth", "mean"),
        )
    )
    rows = []
    for row in grouped.itertuples(index=False):
        out = row._asdict()
        candidates = {
            "revenue YoY": out["revenue_yoy_growth"],
            "revenue QoQ": out["revenue_qoq_growth"],
            "op income YoY": out["op_income_yoy_growth"],
            "op income QoQ": out["op_income_qoq_growth"],
        }
        valid = {k: v for k, v in candidates.items() if pd.notna(v) and -1 <= float(v) <= 5}
        if valid:
            best_metric, best_growth = max(valid.items(), key=lambda item: item[1])
        else:
            best_metric, best_growth = "", np.nan
        out["best_growth_metric"] = best_metric
        out["best_growth_rate"] = best_growth
        rows.append(out)
    out_df = pd.DataFrame(rows)
    coupling_cols = ["group", "avg_pair_corr", "pc1_share", "strong_pair_share"]
    yearly = yearly_summary.rename(columns={"year": "fiscal_year"})
    out_df = out_df.merge(yearly[coupling_cols + ["fiscal_year"]], on=["group", "fiscal_year"], how="inner")
    out_df = out_df.merge(group_summary[["group", "classification", "n_assets"]], on="group", how="left")

    def read(row: pd.Series) -> str:
        corr = row.get("avg_pair_corr", np.nan)
        growth_rate = row.get("best_growth_rate", np.nan)
        if pd.isna(corr) or pd.isna(growth_rate):
            return "insufficient momentum coverage"
        if corr >= 0.50 and growth_rate >= 0.15:
            return "strong coupling with positive fundamental momentum"
        if corr >= 0.50 and growth_rate < 0:
            return "coupling strong despite weak fundamentals"
        if corr < 0.35 and growth_rate >= 0.15:
            return "fundamental momentum present but stock coupling weak"
        return "mixed / modest signal"

    out_df["momentum_read"] = out_df.apply(read, axis=1)
    return out_df.sort_values(["fiscal_year", "fiscal_quarter", "avg_pair_corr"], ascending=[True, True, False])


def company_yearly_growth_rows(
    matched: pd.DataFrame,
    prices: pd.DataFrame,
    annual_financials: pd.DataFrame | None,
    yearly_summary: pd.DataFrame,
) -> pd.DataFrame:
    if yearly_summary.empty or annual_financials is None or annual_financials.empty:
        return pd.DataFrame()

    member_keys = (
        matched[["group_3", "display_name", "ticker_x", "db_ticker"]]
        .drop_duplicates()
        .rename(columns={"group_3": "group", "display_name": "company"})
    )
    member_keys["ticker_x"] = member_keys["ticker_x"].astype(str).str.strip().str.upper()

    fin = annual_financials.copy()
    fin["ticker_x"] = fin["ticker"].astype(str).str.strip().str.upper()
    fin["period_end_date"] = pd.to_datetime(fin["period_end_date"], errors="coerce")
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        if col not in fin.columns:
            fin[col] = np.nan
        fin[col] = pd.to_numeric(fin[col], errors="coerce")
    fin = fin.dropna(subset=["ticker_x", "fiscal_year"])
    fin["fiscal_year"] = fin["fiscal_year"].astype(int)
    fin = fin.sort_values(["ticker_x", "fiscal_year", "period_end_date"]).groupby(["ticker_x", "fiscal_year"], as_index=False).tail(1)

    currencies = latest_price_currency(prices)
    fin = fin.merge(member_keys, on="ticker_x", how="inner").merge(currencies, on="db_ticker", how="left")
    fin["fx_rate_local_per_usd"] = fin.apply(
        lambda row: approximate_fx_local_per_usd(row.get("financial_currency"), row.get("fiscal_year")),
        axis=1,
    )
    for col in ["revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
        fin[col] = np.where(fin[col].notna() & fin["fx_rate_local_per_usd"].notna(), fin[col] / fin["fx_rate_local_per_usd"], fin[col])

    fin = fin.sort_values(["group", "ticker_x", "fiscal_year"])
    for metric in ["revenue_usd_m", "operating_income_usd_m"]:
        base_col = f"{metric}_prior_year"
        growth_col = f"{metric}_annual_growth"
        fin[base_col] = fin.groupby(["group", "ticker_x"])[metric].shift(1)
        fin[growth_col] = np.where(fin[base_col] > 0, fin[metric] / fin[base_col] - 1, np.nan)

    grouped = (
        fin.groupby(["group", "company", "ticker_x", "db_ticker", "fiscal_year"], as_index=False)
        .agg(
            revenue_annual_growth=("revenue_usd_m_annual_growth", "mean"),
            op_income_annual_growth=("operating_income_usd_m_annual_growth", "mean"),
            annual_observations=("period_end_date", "count"),
        )
    )
    for metric_col, prefix in [("revenue_annual_growth", "revenue"), ("op_income_annual_growth", "op_income")]:
        grouped[f"{prefix}_growth_bucket_floor"] = np.floor(grouped[metric_col] / 0.10) * 0.10
        grouped.loc[~grouped[metric_col].between(-1, 5), f"{prefix}_growth_bucket_floor"] = np.nan
        grouped[f"{prefix}_growth_bucket_label"] = grouped[f"{prefix}_growth_bucket_floor"].map(
            lambda x: "" if pd.isna(x) else f"{x * 100:.0f}%~{(x + 0.10) * 100:.0f}%"
        )
    rows = []
    for row in grouped.itertuples(index=False):
        out = row._asdict()
        out["company_best_growth_metric"] = "annual revenue YoY" if pd.notna(out["revenue_annual_growth"]) else "annual op income YoY"
        out["company_avg_growth_rate"] = out["revenue_annual_growth"] if pd.notna(out["revenue_annual_growth"]) else out["op_income_annual_growth"]
        rows.append(out)
    out_df = pd.DataFrame(rows)
    yearly = yearly_summary.rename(columns={"year": "fiscal_year"})
    coupling_cols = ["group", "fiscal_year", "avg_pair_corr", "pc1_share", "strong_pair_share"]
    out_df = out_df.merge(yearly[coupling_cols], on=["group", "fiscal_year"], how="inner")
    return out_df.sort_values(["group", "fiscal_year", "company"])


def classify(avg_corr: float, pc1_share: float, strong_pair_share: float) -> str:
    if avg_corr >= 0.60 and pc1_share >= 0.60:
        return "high coupling"
    if avg_corr >= 0.35 or (pc1_share >= 0.55 and strong_pair_share >= 0.25):
        return "moderate coupling"
    return "weak / fragmented"


def interpretation(group: str, result: GroupResult) -> str:
    if result.classification == "high coupling":
        return f"{group}는 그룹 공통요인이 강하게 작동한다. 평균 상관과 PC1 설명력이 모두 높아, 개별 종목보다 섹터/테마 단위로 같이 움직인 기간이 많다."
    if result.classification == "moderate coupling":
        return f"{group}는 부분적 동조화가 있다. 일부 페어 또는 특정 기간에는 coupling이 강하지만, 그룹 전체가 하나의 factor처럼 움직인다고 보기는 어렵다."
    return f"{group}는 동조화가 약하거나 내부 하위 테마가 갈린다. 같은 그룹이어도 국가, 상장시장, business mix, 데이터 기간 차이가 수익률 상관을 낮춘다."


def analyze_dataset(
    matched: pd.DataFrame,
    prices: pd.DataFrame,
    financials_source: pd.DataFrame | None = None,
    annual_financials: pd.DataFrame | None = None,
) -> tuple[list[GroupResult], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matched = matched.copy()
    prices = prices.copy()
    prices["price_date"] = pd.to_datetime(prices["price_date"])
    prices["adj_close_usd"] = pd.to_numeric(prices["adj_close_usd"], errors="coerce")
    prices = prices.dropna(subset=["ticker", "price_date", "adj_close_usd"])

    if "display_name" not in matched.columns:
        if "name" in matched.columns:
            matched["display_name"] = matched.apply(
                lambda row: row["name"] if str(row["company_name"]).strip().upper() == str(row["ticker_x"]).strip().upper() else row["company_name"],
                axis=1,
            )
        else:
            matched["display_name"] = matched["company_name"]
    matched["ticker_x"] = matched["ticker_x"].astype(str).str.strip().str.upper()
    names = dict(zip(matched["db_ticker"], matched["display_name"]))

    coverage = (
        matched.groupby(["group_3", "display_name", "ticker_x", "db_ticker"], as_index=False)
        .size()
        .drop(columns=["size"])
        .sort_values(["group_3", "display_name"])
    )
    price_coverage = prices.groupby("ticker").agg(price_rows=("adj_close_usd", "count"), start=("price_date", "min"), end=("price_date", "max"))
    coverage = coverage.merge(price_coverage, left_on="db_ticker", right_index=True, how="left")
    coverage["has_price_data"] = coverage["price_rows"].fillna(0).astype(int) >= MIN_OBS
    coverage["start"] = coverage["start"].dt.date.astype(str).replace("NaT", "")
    coverage["end"] = coverage["end"].dt.date.astype(str).replace("NaT", "")

    group_results: list[GroupResult] = []
    all_pair_rows: list[dict[str, object]] = []
    all_member_rows: list[dict[str, object]] = []
    all_yearly_rows: list[dict[str, object]] = []
    all_yearly_scatter_rows: list[dict[str, object]] = []
    all_frequency_rows: list[dict[str, object]] = []

    for group, members in matched.groupby("group_3"):
        tickers = sorted(members["db_ticker"].unique())
        if len(tickers) < 2:
            continue
        returns = price_matrix(prices, tickers, frequency=BASE_FREQUENCY)
        active_cols = [c for c in returns.columns if returns[c].notna().sum() >= MIN_OBS]
        returns = returns[active_cols]
        if returns.shape[1] < 2:
            continue

        pair_rows = pairwise_rows(group, returns, names)
        if not pair_rows:
            continue
        pair_df = pd.DataFrame(pair_rows)
        member_summary = member_rows(group, returns, pair_df, names)
        common = returns.dropna()
        if len(common) < MIN_OBS:
            common = returns.dropna(thresh=2)
        analysis_start = common.index.min().date().isoformat() if len(common) else returns.index.min().date().isoformat()
        analysis_end = common.index.max().date().isoformat() if len(common) else returns.index.max().date().isoformat()

        rolling = rolling_avg_pair_corr(returns)
        pc1 = pc1_explained_share(returns)
        avg_corr = float(pair_df["pearson_corr"].mean())
        median_corr = float(pair_df["pearson_corr"].median())
        strong_share = float((pair_df["pearson_corr"] >= STRONG_CORR).mean())
        klass = classify(avg_corr, pc1, strong_share)
        res = GroupResult(
            group=group,
            tickers=active_cols,
            companies=[names.get(t, t) for t in active_cols],
            n_assets=len(active_cols),
            common_days=len(common),
            start_date=analysis_start,
            end_date=analysis_end,
            avg_pair_corr=avg_corr,
            median_pair_corr=median_corr,
            max_pair_corr=float(pair_df["pearson_corr"].max()),
            min_pair_corr=float(pair_df["pearson_corr"].min()),
            strong_pair_share=strong_share,
            pc1_share=pc1,
            latest_rolling_corr=float(rolling.iloc[-1]) if len(rolling) else np.nan,
            rolling_min=float(rolling.min()) if len(rolling) else np.nan,
            rolling_max=float(rolling.max()) if len(rolling) else np.nan,
            classification=klass,
            interpretation="",
        )
        res = GroupResult(**{**res.__dict__, "interpretation": interpretation(group, res)})
        group_results.append(res)
        all_pair_rows.extend(pair_rows)
        all_member_rows.extend(member_summary)
        all_yearly_rows.extend(yearly_group_rows(group, returns))
        all_yearly_scatter_rows.extend(yearly_scatter_rows(group, returns, names))
        all_frequency_rows.extend(frequency_group_rows(group, prices, active_cols))

    group_results.sort(key=lambda r: (r.avg_pair_corr, r.pc1_share), reverse=True)
    pair_summary = pd.DataFrame(all_pair_rows).sort_values(["group", "pearson_corr"], ascending=[True, False])
    member_summary = pd.DataFrame(all_member_rows).sort_values(["group", "member_role", "mean_corr_to_group"], ascending=[True, True, False])
    yearly_summary = pd.DataFrame(all_yearly_rows).sort_values(["year", "avg_pair_corr"], ascending=[True, False])
    if not yearly_summary.empty:
        yearly_summary["avg_pair_corr_yoy_change"] = yearly_summary.groupby("group")["avg_pair_corr"].diff()
        yearly_summary["pc1_share_yoy_change"] = yearly_summary.groupby("group")["pc1_share"].diff()
    yearly_scatter = pd.DataFrame(all_yearly_scatter_rows)
    frequency_summary = pd.DataFrame(all_frequency_rows).sort_values(["frequency", "avg_pair_corr"], ascending=[True, False])
    if not frequency_summary.empty:
        monthly_base = frequency_summary[frequency_summary["frequency"] == "monthly"][["group", "avg_pair_corr"]].rename(columns={"avg_pair_corr": "monthly_avg_pair_corr"})
        daily_base = frequency_summary[frequency_summary["frequency"] == "daily"][["group", "avg_pair_corr"]].rename(columns={"avg_pair_corr": "daily_avg_pair_corr"})
        frequency_summary = frequency_summary.merge(monthly_base, on="group", how="left").merge(daily_base, on="group", how="left")
        frequency_summary["corr_vs_monthly_delta"] = frequency_summary["avg_pair_corr"] - frequency_summary["monthly_avg_pair_corr"]
        frequency_summary["monthly_vs_daily_delta"] = frequency_summary["monthly_avg_pair_corr"] - frequency_summary["daily_avg_pair_corr"]
    group_summary = pd.DataFrame([r.__dict__ for r in group_results])
    role_deepdive, member_financial_detail = role_financial_deepdive_rows(member_summary, matched, prices, financials_source)
    annual_balance = annual_financial_balance_rows(member_summary, matched, prices, annual_financials, group_summary)
    fundamental_momentum = section_fundamental_momentum_rows(matched, prices, financials_source, yearly_summary, group_summary)
    company_yearly_growth = company_yearly_growth_rows(matched, prices, annual_financials, yearly_summary)
    return group_results, pair_summary, member_summary, yearly_summary, yearly_scatter, frequency_summary, group_summary, coverage, role_deepdive, member_financial_detail, annual_balance, fundamental_momentum, company_yearly_growth


def analyze() -> tuple[list[GroupResult], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matched, _companies, prices, financials_source, annual_financials = load_data()
    return analyze_dataset(matched, prices, financials_source=financials_source, annual_financials=annual_financials)


def table_html(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    if columns is not None:
        df = df[columns]
    if max_rows is not None:
        df = df.head(max_rows)
    header = "".join(f"<th>{esc(c)}</th>" for c in df.columns)
    rows = []
    for _, row in df.iterrows():
        rows.append("<tr>" + "".join(f"<td>{esc(row[c])}</td>" for c in df.columns) + "</tr>")
    return f"<div class=\"table-scroll\"><table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def bar_svg(results: list[GroupResult], metric: str, title: str) -> str:
    data = sorted(results, key=lambda r: getattr(r, metric), reverse=True)
    width, height = 980, max(300, 34 * len(data) + 70)
    left, right, top, bottom = 210, 40, 42, 36
    chart_w = width - left - right
    max_v = max([getattr(r, metric) for r in data] + [0.01])
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{left}" y="24" class="chart-title">{esc(title)}</text>',
    ]
    for i, r in enumerate(data):
        y = top + i * 34
        val = getattr(r, metric)
        w = chart_w * val / max_v if max_v else 0
        color = "#2b6cb0" if r.classification == "high coupling" else "#319795" if r.classification == "moderate coupling" else "#718096"
        parts.append(f'<text x="{left - 10}" y="{y + 15}" text-anchor="end" class="bar-label">{esc(r.group)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="20" fill="{color}" rx="3"/>')
        parts.append(f'<text x="{left + w + 8:.1f}" y="{y + 15}" class="bar-label">{num(val, 2)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def yearly_heatmap_html(yearly_summary: pd.DataFrame) -> str:
    if yearly_summary.empty:
        return "<p>No yearly summary available.</p>"
    pivot = yearly_summary.pivot_table(index="group", columns="year", values="avg_pair_corr", aggfunc="mean")
    ordered = pivot.mean(axis=1).sort_values(ascending=False).index
    pivot = pivot.loc[ordered]
    years = list(pivot.columns)
    header = "<th>group</th>" + "".join(f"<th>{year}</th>" for year in years)
    rows = []
    for group, row in pivot.iterrows():
        cells = [f"<td>{esc(group)}</td>"]
        for year in years:
            val = row.get(year)
            if pd.isna(val):
                cells.append("<td></td>")
            else:
                intensity = max(0, min(1, float(val)))
                bg = f"rgba(43, 108, 176, {0.12 + intensity * 0.72:.2f})"
                fg = "#fff" if intensity > 0.55 else "#172033"
                cells.append(
                    f'<td class="heatmap-cell" data-group="{esc(group)}" data-year="{int(year)}" '
                    f'tabindex="0" role="button" title="Show company scatter: {esc(group)} {int(year)}" '
                    f'style="background:{bg};color:{fg};font-weight:650">{num(float(val), 2)}</td>'
                )
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<div class=\"table-scroll table-scroll-compact\"><table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def yearly_scatter_payload(yearly_scatter: pd.DataFrame) -> str:
    if yearly_scatter.empty:
        return "{}"
    payload: dict[str, list[dict[str, object]]] = {}
    for (group, year), sub in yearly_scatter.groupby(["group", "year"]):
        payload[f"{group}||{int(year)}"] = [
            {
                "date": row.date,
                "ticker": row.ticker,
                "company": row.company,
                "x": round(float(row.group_return_pct), 4),
                "y": round(float(row.company_return_pct), 4),
            }
            for row in sub.itertuples(index=False)
        ]
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def yearly_story_html(yearly_summary: pd.DataFrame) -> str:
    if yearly_summary.empty:
        return ""
    parts = []
    for year, sub in yearly_summary.groupby("year"):
        sub = sub.sort_values("avg_pair_corr", ascending=False)
        top = sub.head(3)
        changed = sub.dropna(subset=["avg_pair_corr_yoy_change"]).sort_values("avg_pair_corr_yoy_change", ascending=False).head(3)
        top_phrase = "; ".join(f"{row.group} {row.avg_pair_corr:.2f}" for row in top.itertuples())
        change_phrase = "; ".join(f"{row.group} +{row.avg_pair_corr_yoy_change:.2f}" for row in changed.itertuples() if row.avg_pair_corr_yoy_change > 0)
        if not change_phrase:
            change_phrase = "no clear positive YoY strengthening signal"
        parts.append(f"<li><strong>{int(year)}</strong>: strongest groups: {esc(top_phrase)}. Strengthening vs prior year: {esc(change_phrase)}.</li>")
    return "<ul>" + "".join(parts) + "</ul>"


def frequency_pivot_html(frequency_summary: pd.DataFrame) -> str:
    if frequency_summary.empty:
        return "<p>No frequency comparison available.</p>"
    pivot = frequency_summary.pivot_table(index="group", columns="frequency", values="avg_pair_corr", aggfunc="mean")
    order_cols = [c for c in ["daily", "weekly", "monthly"] if c in pivot.columns]
    pivot = pivot[order_cols]
    pivot = pivot.sort_values(order_cols[-1] if order_cols else pivot.columns[0], ascending=False)
    header = "<th>group</th>" + "".join(f"<th>{col}</th>" for col in order_cols) + "<th>monthly - daily</th>"
    rows = []
    for group, row in pivot.iterrows():
        cells = [f"<td>{esc(group)}</td>"]
        for col in order_cols:
            cells.append(f"<td>{num(row[col], 2)}</td>")
        delta = row.get("monthly", np.nan) - row.get("daily", np.nan)
        cells.append(f"<td>{num(delta, 2)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<div class=\"table-scroll table-scroll-compact\"><table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def frequency_story_html(frequency_summary: pd.DataFrame) -> str:
    if frequency_summary.empty:
        return ""
    monthly = frequency_summary[frequency_summary["frequency"] == "monthly"].sort_values("avg_pair_corr", ascending=False).head(5)
    weekly = frequency_summary[frequency_summary["frequency"] == "weekly"].sort_values("avg_pair_corr", ascending=False).head(5)
    delta = frequency_summary[frequency_summary["frequency"] == "monthly"].sort_values("monthly_vs_daily_delta", ascending=False).head(5)
    monthly_phrase = "; ".join(f"{row.group} {row.avg_pair_corr:.2f}" for row in monthly.itertuples())
    weekly_phrase = "; ".join(f"{row.group} {row.avg_pair_corr:.2f}" for row in weekly.itertuples())
    delta_phrase = "; ".join(f"{row.group} +{row.monthly_vs_daily_delta:.2f}" for row in delta.itertuples())
    return f"""
      <ul>
        <li><strong>Monthly strongest:</strong> {esc(monthly_phrase)}</li>
        <li><strong>Weekly strongest:</strong> {esc(weekly_phrase)}</li>
        <li><strong>Monthly uplift vs daily:</strong> {esc(delta_phrase)}</li>
      </ul>
"""


def role_share_svg(role_deepdive: pd.DataFrame, metric_share_col: str, title: str) -> str:
    if role_deepdive.empty or metric_share_col not in role_deepdive.columns:
        return "<p>No role deep-dive data available.</p>"
    data = role_deepdive.dropna(subset=[metric_share_col]).copy()
    if data.empty:
        return "<p>No role deep-dive data available for this metric.</p>"
    roles = ["coupling core", "partial / bridge", "weakly coupled"]
    colors = {"coupling core": "#2563eb", "partial / bridge": "#0f766e", "weakly coupled": "#b45309"}
    groups = sorted(data["group"].unique())
    width = 1120
    row_h = 34
    height = max(260, 72 + row_h * len(groups))
    left, right, top = 190, 80, 46
    chart_w = width - left - right
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{left}" y="24" class="chart-title">{esc(title)}</text>',
    ]
    for i, group in enumerate(groups):
        y = top + i * row_h
        parts.append(f'<text x="{left - 12}" y="{y + 17}" text-anchor="end" class="bar-label">{esc(group)}</text>')
        x = left
        group_rows = data[data["group"] == group].set_index("member_role")
        for role in roles:
            if role not in group_rows.index:
                continue
            val = group_rows.loc[role, metric_share_col]
            if pd.isna(val) or val <= 0:
                continue
            w = chart_w * min(1, float(val))
            parts.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" fill="{colors[role]}" opacity="0.86">'
                f'<title>{esc(group)} · {esc(role)} · {pct(float(val))}</title></rect>'
            )
            if w > 34:
                parts.append(f'<text x="{x + w / 2:.1f}" y="{y + 15}" text-anchor="middle" fill="#fff" font-size="11">{pct(float(val))}</text>')
            x += w
        parts.append(f'<line x1="{left}" x2="{left + chart_w}" y1="{y + 27}" y2="{y + 27}" stroke="#e2e8f0"/>')
    legend_x = left
    legend_y = height - 18
    for role in roles:
        parts.append(f'<rect x="{legend_x}" y="{legend_y - 10}" width="10" height="10" fill="{colors[role]}"/>')
        parts.append(f'<text x="{legend_x + 16}" y="{legend_y}" class="bar-label">{esc(role)}</text>')
        legend_x += 150
    parts.append("</svg>")
    return "".join(parts)


def role_financial_weight_svg(role_deepdive: pd.DataFrame, title: str, group: str | None = None) -> str:
    if role_deepdive.empty:
        return "<p>No role deep-dive data available.</p>"
    data = role_deepdive.copy()
    if group is not None:
        data = data[data["group"] == group]
    required = {"revenue_usd_m_share_of_group", "operating_income_usd_m_share_of_group", "member_role"}
    if data.empty or not required <= set(data.columns):
        return "<p>No comparable role financial-weight data available.</p>"

    roles = ["coupling core", "partial / bridge", "weakly coupled"]
    colors = {"coupling core": "#2563eb", "partial / bridge": "#0f766e", "weakly coupled": "#b45309"}
    metrics = [
        ("revenue_usd_m_share_of_group", "Revenue"),
        ("operating_income_usd_m_share_of_group", "Op income"),
    ]
    groups = [group] if group is not None else sorted(data["group"].dropna().unique())
    width = 1160
    row_h = 58
    height = max(210, 72 + row_h * len(groups))
    left, right, top = 190, 80, 48
    chart_w = width - left - right
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{left}" y="24" class="chart-title">{esc(title)}</text>',
        f'<text x="{left}" y="40" class="bar-label">Segment width is each role share inside the same section. Tooltip includes average member coupling strength.</text>',
    ]
    for i, group_name in enumerate(groups):
        group_rows = data[data["group"] == group_name].set_index("member_role")
        y0 = top + i * row_h
        parts.append(f'<text x="{left - 12}" y="{y0 + 23}" text-anchor="end" class="bar-label">{esc(group_name)}</text>')
        for metric_i, (metric_col, metric_label) in enumerate(metrics):
            y = y0 + metric_i * 24
            parts.append(f'<text x="{left - 124}" y="{y + 15}" class="bar-label">{esc(metric_label)}</text>')
            x = left
            for role in roles:
                if role not in group_rows.index:
                    continue
                val = group_rows.loc[role, metric_col]
                if pd.isna(val):
                    continue
                display_val = max(0, min(1, float(val)))
                w = chart_w * display_val
                if w <= 0:
                    continue
                corr = group_rows.loc[role, "avg_mean_corr_to_group"] if "avg_mean_corr_to_group" in group_rows.columns else np.nan
                members = group_rows.loc[role, "members"] if "members" in group_rows.columns else np.nan
                parts.append(
                    f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="18" fill="{colors[role]}" opacity="0.86">'
                    f'<title>{esc(group_name)} · {esc(metric_label)} · {esc(role)} · share {pct(float(val))} · avg corr {num(corr, 2)} · members {esc(members)}</title></rect>'
                )
                if w > 42:
                    parts.append(f'<text x="{x + w / 2:.1f}" y="{y + 13}" text-anchor="middle" fill="#fff" font-size="11">{pct(float(val))}</text>')
                x += w
            parts.append(f'<rect x="{left}" y="{y}" width="{chart_w}" height="18" fill="none" stroke="#d9e0ea"/>')
        parts.append(f'<line x1="{left}" x2="{left + chart_w}" y1="{y0 + 50}" y2="{y0 + 50}" stroke="#e2e8f0"/>')
    legend_x = left
    legend_y = height - 18
    for role in roles:
        parts.append(f'<rect x="{legend_x}" y="{legend_y - 10}" width="10" height="10" fill="{colors[role]}"/>')
        parts.append(f'<text x="{legend_x + 16}" y="{legend_y}" class="bar-label">{esc(role)}</text>')
        legend_x += 150
    parts.append("</svg>")
    return "".join(parts)


def company_financial_weight_svg(member_financial_detail: pd.DataFrame, title: str, group: str | None = None) -> str:
    if member_financial_detail.empty:
        return "<p>No company financial-weight data available.</p>"
    data = member_financial_detail.copy()
    if group is not None:
        data = data[data["group"] == group]
    required = {"company", "ticker", "revenue_usd_m_share_of_group", "operating_income_usd_m_share_of_group"}
    if data.empty or not required <= set(data.columns):
        return "<p>No comparable company financial-weight data available.</p>"

    metrics = [
        ("revenue_usd_m_share_of_group", "매출"),
        ("operating_income_usd_m_share_of_group", "영업이익"),
    ]
    metric_cols = [col for col, _label in metrics]
    data = data[data[metric_cols].notna().any(axis=1)]
    if data.empty:
        return f"<p>No {FINANCIAL_WEIGHT_YEAR} Q{FINANCIAL_WEIGHT_QUARTER} comparable company financial-weight data available.</p>"
    groups = [group] if group is not None else sorted(data["group"].dropna().unique())
    palette = [
        "#2563eb",
        "#dc2626",
        "#059669",
        "#7c3aed",
        "#ea580c",
        "#0891b2",
        "#be123c",
        "#4d7c0f",
        "#9333ea",
        "#0f766e",
        "#b45309",
        "#64748b",
        "#0e7490",
        "#a21caf",
        "#15803d",
        "#b91c1c",
        "#1d4ed8",
        "#6d28d9",
    ]
    width = 1160
    row_h = 58
    height = max(210, 72 + row_h * len(groups))
    left, right, top = 255, 80, 48
    chart_w = width - left - right
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{left}" y="24" class="chart-title">{esc(title)}</text>',
        f'<text x="{left}" y="40" class="bar-label">Each segment is an individual company share inside the section. Hover for company, ticker, and coupling stats.</text>',
    ]
    for i, group_name in enumerate(groups):
        group_rows = data[data["group"] == group_name].copy()
        group_rows = group_rows.sort_values("revenue_usd_m_share_of_group", ascending=False, na_position="last")
        y0 = top + i * row_h
        missing_fx = bool(group_rows["missing_fx_rate"].fillna(False).any()) if "missing_fx_rate" in group_rows else False
        mixed_currency = bool(group_rows["mixed_financial_currency"].fillna(False).any()) if "mixed_financial_currency" in group_rows else False
        currencies = ", ".join(sorted(group_rows["financial_currency"].dropna().astype(str).unique())) if "financial_currency" in group_rows else ""
        if missing_fx:
            parts.append(
                f'<rect x="{left}" y="{y0}" width="{chart_w}" height="42" fill="#fff7ed" stroke="#fed7aa"/>'
                f'<text x="{left + 12}" y="{y0 + 17}" class="bar-label">Mixed reporting currencies: {esc(currencies)}.</text>'
                f'<text x="{left + 12}" y="{y0 + 36}" class="bar-label">Revenue/op-income shares are hidden because one or more FX rates are unavailable.</text>'
            )
            parts.append(f'<line x1="{left}" x2="{left + chart_w}" y1="{y0 + 50}" y2="{y0 + 50}" stroke="#e2e8f0"/>')
            continue
        if mixed_currency:
            parts.append(f'<text x="{left}" y="{y0 - 2}" class="bar-label">Approx FX-normalized: {esc(currencies)}</text>')
        color_map = {ticker: palette[j % len(palette)] for j, ticker in enumerate(group_rows["ticker"].astype(str).tolist())}
        for metric_i, (metric_col, metric_label) in enumerate(metrics):
            y = y0 + metric_i * 24
            row_label = f"{group_name} · {metric_label}"
            parts.append(f'<text x="{left - 12}" y="{y + 14}" text-anchor="end" class="bar-label financial-row-label">{esc(row_label)}</text>')
            x = left
            for row in group_rows.itertuples(index=False):
                val = getattr(row, metric_col, np.nan)
                if pd.isna(val) or float(val) < 0 or float(val) > 1:
                    continue
                w = chart_w * float(val)
                if w <= 0:
                    continue
                ticker = str(getattr(row, "ticker"))
                company = getattr(row, "company")
                corr = getattr(row, "mean_corr_to_group", np.nan)
                max_corr = getattr(row, "max_corr_to_peer", np.nan)
                currency = getattr(row, "financial_currency", "")
                fx_rate = getattr(row, "fx_rate_local_per_usd", np.nan)
                parts.append(
                    f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="18" fill="{color_map[ticker]}" opacity="0.86">'
                    f'<title>{esc(group_name)} · {esc(metric_label)} · {esc(company)} ({esc(ticker)}) · share {pct(float(val))} · currency {esc(currency)} · FX local/USD {num(fx_rate, 2)} · mean corr {num(corr, 2)} · max peer corr {num(max_corr, 2)}</title></rect>'
                )
                if w > 44:
                    label = ticker if len(ticker) <= 8 else ticker[:8]
                    parts.append(f'<text x="{x + w / 2:.1f}" y="{y + 13}" text-anchor="middle" fill="#fff" font-size="10">{esc(label)}</text>')
                x += w
            parts.append(f'<rect x="{left}" y="{y}" width="{chart_w}" height="18" fill="none" stroke="#d9e0ea"/>')
        parts.append(f'<line x1="{left}" x2="{left + chart_w}" y1="{y0 + 50}" y2="{y0 + 50}" stroke="#e2e8f0"/>')
    parts.append("</svg>")
    return "".join(parts)


def section_fundamental_momentum_svg(momentum: pd.DataFrame, title: str, group: str | None = None, metric_family: str = "revenue") -> str:
    if momentum.empty:
        return "<p>No section fundamental momentum data available.</p>"
    data = momentum.copy()
    if group is not None:
        data = data[data["group"] == group]
    metric_config = {
        "revenue": {
            "yoy": "revenue_yoy_growth",
            "qoq": "revenue_qoq_growth",
            "label": "revenue",
            "colors": {"YoY": "#2563eb", "QoQ": "#0891b2"},
        },
        "op_income": {
            "yoy": "op_income_yoy_growth",
            "qoq": "op_income_qoq_growth",
            "label": "operating income",
            "colors": {"YoY": "#dc2626", "QoQ": "#ea580c"},
        },
    }
    cfg = metric_config.get(metric_family, metric_config["revenue"])
    required = {"group", "fiscal_year", "fiscal_quarter", "avg_pair_corr", cfg["yoy"], cfg["qoq"]}
    if data.empty or not required <= set(data.columns):
        return "<p>No comparable section fundamental momentum data available.</p>"
    data["plot_growth_rate"] = data.apply(
        lambda row: max(
            [v for v in [row.get(cfg["yoy"], np.nan), row.get(cfg["qoq"], np.nan)] if pd.notna(v) and -1 <= float(v) <= 5],
            default=np.nan,
        ),
        axis=1,
    )
    data["plot_growth_metric"] = np.where(
        pd.to_numeric(data[cfg["yoy"]], errors="coerce") == data["plot_growth_rate"],
        "YoY",
        "QoQ",
    )
    data = data.dropna(subset=["avg_pair_corr", "plot_growth_rate"]).copy()
    if data.empty:
        return "<p>No section-quarter growth observations available for this view.</p>"
    data = data.sort_values(["fiscal_year", "fiscal_quarter", "avg_pair_corr"])
    width = 1180
    height = 520
    margin = {"left": 82, "right": 220, "top": 58, "bottom": 72}
    inner_w = width - margin["left"] - margin["right"]
    inner_h = height - margin["top"] - margin["bottom"]
    x_vals = pd.to_numeric(data["avg_pair_corr"], errors="coerce")
    growth_vals = pd.to_numeric(data["plot_growth_rate"], errors="coerce")
    x_min = min(0.0, float(x_vals.min()))
    x_max = max(0.75, float(x_vals.max()))
    y_min = min(-0.25, float(growth_vals.min()))
    y_max = max(0.75, float(growth_vals.max()))
    y_pad = max(0.08, (y_max - y_min) * 0.12)
    y_min -= y_pad
    y_max += y_pad
    if y_min == y_max:
        y_min, y_max = -0.25, 0.75

    def sx(x: float) -> float:
        return margin["left"] + ((x - x_min) / (x_max - x_min)) * inner_w

    def sy(y: float) -> float:
        return margin["top"] + inner_h - ((y - y_min) / (y_max - y_min)) * inner_h

    colors = cfg["colors"]
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{margin["left"]}" y="24" class="chart-title">{esc(title)}</text>',
        f'<text x="{margin["left"]}" y="42" class="bar-label">Each point is one section-quarter. X is that year average pair correlation; Y is average quarterly {esc(cfg["label"])} growth.</text>',
        f'<line x1="{margin["left"]}" y1="{margin["top"] + inner_h}" x2="{margin["left"] + inner_w}" y2="{margin["top"] + inner_h}" class="scatter-axis"/>',
        f'<line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{margin["top"] + inner_h}" class="scatter-axis"/>',
    ]
    x_ticks = np.linspace(x_min, x_max, 5)
    y_ticks = np.linspace(y_min, y_max, 5)
    for tick in x_ticks:
        x = sx(float(tick))
        parts.append(f'<line x1="{x:.1f}" y1="{margin["top"]}" x2="{x:.1f}" y2="{margin["top"] + inner_h}" class="scatter-grid"/>')
        parts.append(f'<text x="{x:.1f}" y="{height - 42}" text-anchor="middle" class="bar-label">{num(float(tick), 2)}</text>')
    for tick in y_ticks:
        y = sy(float(tick))
        parts.append(f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{margin["left"] + inner_w}" y2="{y:.1f}" class="scatter-grid"/>')
        parts.append(f'<text x="{margin["left"] - 10}" y="{y + 4:.1f}" text-anchor="end" class="bar-label">{pct(float(tick))}</text>')
    parts.append(f'<text x="{margin["left"] + inner_w / 2:.1f}" y="{height - 14}" text-anchor="middle" class="bar-label">year average pair correlation</text>')
    parts.append(f'<text transform="translate(20 {margin["top"] + inner_h / 2:.1f}) rotate(-90)" text-anchor="middle" class="bar-label">quarterly average growth</text>')

    for row in data.itertuples(index=False):
        group_name = getattr(row, "group")
        corr = float(getattr(row, "avg_pair_corr"))
        growth = float(getattr(row, "plot_growth_rate"))
        metric = str(getattr(row, "plot_growth_metric", ""))
        year = int(getattr(row, "fiscal_year"))
        quarter = int(getattr(row, "fiscal_quarter"))
        color = colors.get(metric, "#64748b")
        x = sx(corr)
        y = sy(growth)
        label = group_name if group is None and corr >= 0.55 else ""
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.8" fill="{color}" opacity="0.82">'
            f'<title>{esc(group_name)} · {year}Q{quarter} · corr {num(corr, 2)} · {esc(cfg["label"])} {esc(metric)} {pct(growth)}</title></circle>'
        )
        if label:
            parts.append(f'<text x="{x + 8:.1f}" y="{y - 7:.1f}" class="bar-label">{esc(label)}</text>')
    legend_y = 78
    legend_x = width - margin["right"] + 28
    for metric, color in colors.items():
        parts.append(f'<circle cx="{legend_x}" cy="{legend_y - 4}" r="5" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 10}" y="{legend_y}" class="bar-label">{esc(metric)}</text>')
        legend_y += 22
    if group is not None:
        latest = data.sort_values(["fiscal_year", "fiscal_quarter"]).tail(1).iloc[0]
        parts.append(f'<text x="{legend_x}" y="{legend_y + 16}" class="bar-label">latest: {int(latest.fiscal_year)}Q{int(latest.fiscal_quarter)}</text>')
        parts.append(f'<text x="{legend_x}" y="{legend_y + 34}" class="bar-label">corr {num(latest.avg_pair_corr, 2)} · growth {pct(latest.plot_growth_rate)}</text>')
        parts.append(f'<text x="{legend_x}" y="{legend_y + 52}" class="bar-label">{esc(cfg["label"])} {esc(latest.plot_growth_metric)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def company_yearly_growth_scatter_svg(company_growth: pd.DataFrame, title: str, group: str | None = None, metric_family: str = "revenue") -> str:
    if company_growth.empty:
        return "<p>No company yearly growth data available.</p>"
    data = company_growth.copy()
    if group is not None:
        data = data[data["group"] == group]
    metric_config = {
        "revenue": {
            "growth": "revenue_annual_growth",
            "label": "revenue",
        },
        "op_income": {
            "growth": "op_income_annual_growth",
            "label": "operating income",
        },
    }
    cfg = metric_config.get(metric_family, metric_config["revenue"])
    required = {"company", "fiscal_year", "avg_pair_corr", cfg["growth"]}
    if data.empty or not required <= set(data.columns):
        return "<p>No comparable company yearly growth data available.</p>"
    data["plot_growth_rate"] = pd.to_numeric(data[cfg["growth"]], errors="coerce")
    data.loc[~data["plot_growth_rate"].between(-1, 5), "plot_growth_rate"] = np.nan
    data["plot_growth_metric"] = "annual YoY"
    data = data.dropna(subset=["avg_pair_corr", "plot_growth_rate"]).copy()
    if data.empty:
        return "<p>No company-year growth observations available for this view.</p>"
    data["growth_bucket_floor"] = np.floor(data["plot_growth_rate"] / 0.10) * 0.10
    data["growth_bucket_mid"] = data["growth_bucket_floor"] + 0.05
    data["growth_bucket_label"] = data["growth_bucket_floor"].map(lambda x: f"{x * 100:.0f}%~{(x + 0.10) * 100:.0f}%")
    width, height = 1180, 520
    margin = {"left": 82, "right": 190, "top": 58, "bottom": 72}
    inner_w = width - margin["left"] - margin["right"]
    inner_h = height - margin["top"] - margin["bottom"]
    y_vals = pd.to_numeric(data["growth_bucket_mid"], errors="coerce")
    y_min, y_max = min(-0.25, float(y_vals.min())), max(0.75, float(y_vals.max()))
    y_pad = max(0.08, (y_max - y_min) * 0.12)
    y_min -= y_pad
    y_max += y_pad

    def sy(y: float) -> float:
        return margin["top"] + inner_h - ((y - y_min) / (y_max - y_min)) * inner_h

    palette = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#ea580c", "#0891b2", "#be123c", "#4d7c0f", "#9333ea", "#0f766e", "#b45309", "#64748b"]
    companies = list(dict.fromkeys(data["company"].astype(str).tolist()))
    color_map = {company: palette[i % len(palette)] for i, company in enumerate(companies)}
    years = sorted(data["fiscal_year"].dropna().astype(int).unique().tolist())
    if not years:
        return "<p>No company-year growth observations available for this view.</p>"
    year_step = inner_w / max(1, len(years))
    bar_w = min(54, year_step * 0.58)
    year_x = {year: margin["left"] + year_step * i + year_step / 2 for i, year in enumerate(years)}
    corr_by_year = data.groupby("fiscal_year")["avg_pair_corr"].mean()
    max_corr = max(0.75, float(corr_by_year.max()))

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{margin["left"]}" y="24" class="chart-title">{esc(title)}</text>',
        f'<text x="{margin["left"]}" y="42" class="bar-label">Bars are yearly average pair correlation. Dots are company annual {esc(cfg["label"])} YoY growth bucketed by 10%.</text>',
    ]
    for tick in np.linspace(y_min, y_max, 5):
        y = sy(float(tick))
        parts.append(f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{margin["left"] + inner_w}" y2="{y:.1f}" class="scatter-grid"/>')
        parts.append(f'<text x="{margin["left"] - 10}" y="{y + 4:.1f}" text-anchor="end" class="bar-label">{pct(float(tick))}</text>')
    parts.append(f'<line x1="{margin["left"]}" y1="{margin["top"] + inner_h}" x2="{margin["left"] + inner_w}" y2="{margin["top"] + inner_h}" class="scatter-axis"/>')
    parts.append(f'<line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{margin["top"] + inner_h}" class="scatter-axis"/>')
    parts.append(f'<line x1="{margin["left"] + inner_w}" y1="{margin["top"]}" x2="{margin["left"] + inner_w}" y2="{margin["top"] + inner_h}" class="scatter-axis"/>')
    for year in years:
        x = year_x[year]
        corr = float(corr_by_year.get(year, np.nan))
        bar_h = inner_h * max(0, corr) / max_corr if pd.notna(corr) else 0
        parts.append(
            f'<rect x="{x - bar_w / 2:.1f}" y="{margin["top"] + inner_h - bar_h:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="#cbd5e1" opacity="0.78" rx="3">'
            f'<title>{year} avg pair corr {num(corr, 2)}</title></rect>'
        )
        parts.append(f'<text x="{x:.1f}" y="{height - 42}" text-anchor="middle" class="bar-label">{year}</text>')
        parts.append(f'<text x="{x:.1f}" y="{margin["top"] + inner_h - bar_h - 6:.1f}" text-anchor="middle" class="bar-label">{num(corr, 2)}</text>')

    point_r = 4.6
    point_x: dict[int, float] = {}
    for (_year, _bucket), sub in data.groupby(["fiscal_year", "growth_bucket_label"], dropna=False):
        center = year_x[int(_year)]
        slots = len(sub)
        usable_w = max(point_r * 2, bar_w - point_r * 2)
        if slots == 1:
            offsets = [0.0]
        else:
            offsets = np.linspace(-usable_w / 2, usable_w / 2, slots)
        for idx, offset in zip(sub.index.tolist(), offsets):
            point_x[idx] = center + float(offset)

    for row in data.reset_index().itertuples(index=False):
        idx = int(getattr(row, "index"))
        company = str(getattr(row, "company"))
        year = int(getattr(row, "fiscal_year"))
        x = point_x.get(idx, year_x.get(year, margin["left"]))
        y = sy(float(getattr(row, "growth_bucket_mid")))
        metric = str(getattr(row, "plot_growth_metric", ""))
        bucket_label = str(getattr(row, "growth_bucket_label", ""))
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{point_r:.1f}" fill="{color_map[company]}" opacity="0.78">'
            f'<title>{esc(company)} · {year} · corr {num(float(getattr(row, "avg_pair_corr")), 2)} · {esc(cfg["label"])} {esc(metric)} {pct(float(getattr(row, "plot_growth_rate")))} · bucket {esc(bucket_label)}</title></circle>'
        )
    parts.append(f'<text x="{margin["left"] + inner_w / 2:.1f}" y="{height - 14}" text-anchor="middle" class="bar-label">fiscal year</text>')
    parts.append(f'<text transform="translate(20 {margin["top"] + inner_h / 2:.1f}) rotate(-90)" text-anchor="middle" class="bar-label">company annual {esc(cfg["label"])} YoY growth bucket</text>')
    parts.append(f'<text transform="translate({width - 18} {margin["top"] + inner_h / 2:.1f}) rotate(90)" text-anchor="middle" class="bar-label">avg pair corr bar</text>')
    legend_x = width - margin["right"] + 18
    legend_y = 78
    for company in companies[:14]:
        parts.append(f'<circle cx="{legend_x}" cy="{legend_y - 4}" r="5" fill="{color_map[company]}"/>')
        parts.append(f'<text x="{legend_x + 10}" y="{legend_y}" class="bar-label">{esc(company[:24])}</text>')
        legend_y += 20
    parts.append("</svg>")
    return "".join(parts)


def role_deepdive_story(role_deepdive: pd.DataFrame) -> str:
    if role_deepdive.empty:
        return "<p>No role deep-dive data available.</p>"
    rows = []
    for group, sub in role_deepdive.groupby("group"):
        core = sub[sub["member_role"] == "coupling core"]
        weak = sub[sub["member_role"] == "weakly coupled"]
        core_rev = core["revenue_usd_m_share_of_group"].iloc[0] if not core.empty and "revenue_usd_m_share_of_group" in core else np.nan
        weak_rev = weak["revenue_usd_m_share_of_group"].iloc[0] if not weak.empty and "revenue_usd_m_share_of_group" in weak else np.nan
        core_profit = core["operating_income_usd_m_share_of_group"].iloc[0] if not core.empty and "operating_income_usd_m_share_of_group" in core else np.nan
        weak_profit = weak["operating_income_usd_m_share_of_group"].iloc[0] if not weak.empty and "operating_income_usd_m_share_of_group" in weak else np.nan
        if pd.isna(core_rev) and pd.isna(weak_rev):
            continue
        rows.append(
            f"<li><strong>{esc(group)}</strong>: coupling core revenue share {pct(core_rev)}, weak-member revenue share {pct(weak_rev)}, "
            f"core operating-income share {pct(core_profit)}, weak operating-income share {pct(weak_profit)}.</li>"
        )
    return "<ul>" + "".join(rows[:18]) + "</ul>" if rows else "<p>No comparable revenue/profit role split available.</p>"


def company_financial_weight_story(member_financial_detail: pd.DataFrame) -> str:
    if member_financial_detail.empty:
        return "<p>No company financial-weight data available.</p>"
    rows = []
    for group, sub in member_financial_detail.groupby("group"):
        rev = sub.dropna(subset=["revenue_usd_m_share_of_group"]).sort_values("revenue_usd_m_share_of_group", ascending=False)
        op = sub.dropna(subset=["operating_income_usd_m_share_of_group"]).sort_values("operating_income_usd_m_share_of_group", ascending=False)
        if rev.empty and op.empty:
            continue
        rev_phrase = "n/a"
        op_phrase = "n/a"
        if not rev.empty:
            top = rev.head(2)
            rev_phrase = ", ".join(f"{row.company} {pct(row.revenue_usd_m_share_of_group)}" for row in top.itertuples())
        if not op.empty:
            top = op.head(2)
            op_phrase = ", ".join(f"{row.company} {pct(row.operating_income_usd_m_share_of_group)}" for row in top.itertuples())
        rows.append(f"<li><strong>{esc(group)}</strong>: revenue leaders {esc(rev_phrase)}; op-income leaders {esc(op_phrase)}.</li>")
    return "<ul>" + "".join(rows[:18]) + "</ul>" if rows else "<p>No company-level revenue/profit split available.</p>"


BOTTLENECK_CONTEXT = {
    "DRAM": {
        "supply_chain_role": "HBM / DRAM memory layer",
        "bottleneck_sensitivity": "high",
        "bottleneck_proxy_to_verify": "HBM allocation, DRAM ASP, customer prepayments, wafer starts, inventory days",
        "interpretation": "High coupling here can be consistent with market-wide memory shortage or HBM allocation narratives, but price data alone cannot prove shortage.",
        "evidence_needed": "HBM capacity by vendor, contract backlog, ASP trend, lead time, memory inventory, hyperscaler purchase commitments",
    },
    "NAND": {
        "supply_chain_role": "AI storage / enterprise SSD / memory-adjacent layer",
        "bottleneck_sensitivity": "medium-high",
        "bottleneck_proxy_to_verify": "Enterprise SSD pricing, NAND bit supply growth, HDD nearline demand, hyperscaler storage capex",
        "interpretation": "Strong coupling suggests the market is pricing storage vendors as one supply/demand factor; validate against storage shortage and pricing data.",
        "evidence_needed": "NAND ASP, enterprise SSD backlog, HDD nearline shipments, hyperscaler storage procurement commentary",
    },
    "AI Chip": {
        "supply_chain_role": "Accelerator / custom silicon demand layer",
        "bottleneck_sensitivity": "high",
        "bottleneck_proxy_to_verify": "GPU/ASIC allocation, foundry capacity, HBM attach availability, packaging capacity",
        "interpretation": "Moderate-to-rising coupling can reflect common AI accelerator demand, but individual product cycle and export control exposure still matter.",
        "evidence_needed": "GPU lead time, accelerator shipment mix, foundry allocation, HBM attach supply, export-control exposure",
    },
    "HW equipment": {
        "supply_chain_role": "Semiconductor equipment / process capacity enabler",
        "bottleneck_sensitivity": "high",
        "bottleneck_proxy_to_verify": "WFE capex, EUV/advanced-node equipment availability, advanced packaging equipment demand",
        "interpretation": "High coupling is consistent with a capacity-expansion factor: if fabs and packaging capacity are bottlenecks, equipment suppliers tend to re-rate together.",
        "evidence_needed": "WFE order backlog, EUV shipment outlook, advanced packaging tool orders, foundry capex guidance",
    },
    "OSAT / packiging": {
        "supply_chain_role": "Advanced packaging / test layer",
        "bottleneck_sensitivity": "high",
        "bottleneck_proxy_to_verify": "CoWoS/2.5D capacity, substrate supply, test capacity, package lead time",
        "interpretation": "Packaging can be a binding constraint for AI accelerators; moderate coupling suggests the section is partly priced as an AI capacity bottleneck.",
        "evidence_needed": "CoWoS capacity, advanced substrate supply, OSAT utilization, package/test lead times",
    },
    "components": {
        "supply_chain_role": "Substrates, passives, connectors, power components",
        "bottleneck_sensitivity": "medium",
        "bottleneck_proxy_to_verify": "ABF/substrate utilization, connector demand, power component availability",
        "interpretation": "Moderate coupling suggests some AI infrastructure factor, but this basket is broad and can split by component category.",
        "evidence_needed": "ABF substrate utilization, connector backlog, power IC demand, customer concentration by AI server exposure",
    },
    "Cooling": {
        "supply_chain_role": "Thermal management / data center cooling",
        "bottleneck_sensitivity": "high",
        "bottleneck_proxy_to_verify": "Rack power density, liquid cooling adoption, chiller/cold-plate lead time, data center PUE constraints",
        "interpretation": "Rising coupling can be interpreted as market recognition that thermal capacity is a shared AI infrastructure constraint.",
        "evidence_needed": "Liquid cooling attach rate, rack density trend, cooling equipment backlog, data center PUE and water constraints",
    },
    "Energy": {
        "supply_chain_role": "Power, grid, electrical equipment, data center energy supply",
        "bottleneck_sensitivity": "high",
        "bottleneck_proxy_to_verify": "Interconnection queue, transformer lead time, firm power availability, utility load growth",
        "interpretation": "Moderate coupling with a strong 2026 YTD move can fit the power bottleneck story, but the group also contains utilities and industrials with different drivers.",
        "evidence_needed": "Grid interconnection delays, transformer/switchgear backlog, utility capex plans, data center load commitments",
    },
    "Server Networking": {
        "supply_chain_role": "AI cluster networking / optical interconnect",
        "bottleneck_sensitivity": "medium-high",
        "bottleneck_proxy_to_verify": "800G/1.6T optical demand, switch ASIC availability, transceiver lead time",
        "interpretation": "Moderate coupling can reflect AI cluster buildout pressure, but optical, switching, and telecom exposures differ.",
        "evidence_needed": "Optical transceiver backlog, Ethernet/InfiniBand switch demand, hyperscaler networking capex",
    },
    "Server OEM/EMS/ODM": {
        "supply_chain_role": "AI server integration / rack assembly",
        "bottleneck_sensitivity": "medium",
        "bottleneck_proxy_to_verify": "AI server backlog, rack-scale integration capacity, customer concentration, GPU allocation",
        "interpretation": "Weak-to-moderate coupling usually means execution and customer mix matter as much as the AI server theme.",
        "evidence_needed": "AI server revenue mix, rack backlog, ODM allocation, gross margin by AI program",
    },
    "Server OEM": {
        "supply_chain_role": "Branded server OEM / enterprise systems",
        "bottleneck_sensitivity": "medium",
        "bottleneck_proxy_to_verify": "AI server orders, enterprise backlog, GPU allocation, channel inventory, margin by AI system",
        "interpretation": "OEM coupling indicates whether branded system vendors are being priced as a common AI server demand channel rather than as separate enterprise hardware stories.",
        "evidence_needed": "AI server revenue mix, enterprise backlog, GPU allocation, channel inventory, services attach rate",
    },
    "Server ODM": {
        "supply_chain_role": "Cloud server ODM / rack-scale integration",
        "bottleneck_sensitivity": "medium-high",
        "bottleneck_proxy_to_verify": "Hyperscaler rack orders, AI server build schedule, rack-scale integration capacity, GPU allocation",
        "interpretation": "ODM coupling is more directly tied to hyperscaler AI buildouts; strong coupling can screen for shared rack-scale integration or allocation constraints.",
        "evidence_needed": "AI rack backlog, hyperscaler customer mix, GPU allocation, rack delivery schedule, ODM utilization",
    },
    "Server EMS": {
        "supply_chain_role": "Electronics manufacturing services / assembly",
        "bottleneck_sensitivity": "medium",
        "bottleneck_proxy_to_verify": "Assembly capacity, customer concentration, component availability, AI program margins",
        "interpretation": "EMS coupling can reflect shared manufacturing exposure, but large customers and non-AI product mix can dilute the AI infrastructure signal.",
        "evidence_needed": "AI program revenue mix, assembly utilization, customer concentration, component lead times, margin by program",
    },
    "Neocloud": {
        "supply_chain_role": "GPU cloud / compute capacity monetization",
        "bottleneck_sensitivity": "medium-high",
        "bottleneck_proxy_to_verify": "Contracted GPU capacity, utilization, financing spread, power access",
        "interpretation": "High full-period coupling but weaker 2026 YTD coupling suggests the theme can fragment when financing, utilization, and execution risk diverge.",
        "evidence_needed": "Contracted capacity, utilization, debt cost, power contracts, GPU fleet delivery schedule",
    },
    "AI Platforms": {
        "supply_chain_role": "AI software / application demand layer",
        "bottleneck_sensitivity": "medium",
        "bottleneck_proxy_to_verify": "AI monetization, inference cost, cloud spend efficiency, enterprise adoption",
        "interpretation": "Coupling here is more demand/narrative-side than physical shortage-side; strong moves may reflect AI revenue expectations rather than supply bottlenecks.",
        "evidence_needed": "AI ARR, inference gross margin, cloud cost ratios, enterprise deployment metrics",
    },
    "Hyperscalers": {
        "supply_chain_role": "AI capex sponsor / cloud demand layer",
        "bottleneck_sensitivity": "medium",
        "bottleneck_proxy_to_verify": "Capex, data center delivery, power availability, AI revenue conversion",
        "interpretation": "Lower coupling can happen because hyperscalers differ in balance sheet, ads/cloud mix, and AI monetization despite sharing the same supply chain constraints.",
        "evidence_needed": "AI capex split, cloud growth, data center delivery schedule, power procurement",
    },
}


def bottleneck_interpretation_rows(group_summary: pd.DataFrame, yearly_summary: pd.DataFrame) -> pd.DataFrame:
    ytd = pd.DataFrame()
    if not yearly_summary.empty:
        latest_year = int(yearly_summary["year"].max())
        ytd = yearly_summary[yearly_summary["year"] == latest_year][["group", "avg_pair_corr", "avg_pair_corr_yoy_change", "observations"]].rename(
            columns={
                "avg_pair_corr": "latest_year_avg_pair_corr",
                "avg_pair_corr_yoy_change": "latest_year_yoy_change",
                "observations": "latest_year_months",
            }
        )
    rows = []
    for row in group_summary.itertuples(index=False):
        context = BOTTLENECK_CONTEXT.get(
            row.group,
            {
                "supply_chain_role": "AI supply-chain adjacent section",
                "bottleneck_sensitivity": "low-medium",
                "bottleneck_proxy_to_verify": "Section-specific lead time, pricing, backlog, and utilization",
                "interpretation": "Use coupling as a screening signal only; section-level bottleneck relevance needs external operating data.",
                "evidence_needed": "Pricing, backlog, utilization, inventory, and customer commentary",
            },
        )
        if row.classification == "high coupling":
            signal = "strong market coupling"
        elif row.classification == "moderate coupling":
            signal = "moderate market coupling"
        else:
            signal = "weak / fragmented market coupling"
        rows.append(
            {
                "group": row.group,
                "supply_chain_role": context["supply_chain_role"],
                "bottleneck_sensitivity": context["bottleneck_sensitivity"],
                "current_coupling_signal": signal,
                "avg_pair_corr": row.avg_pair_corr,
                "pc1_share": row.pc1_share,
                "latest_12m_avg_pair_corr": row.latest_rolling_corr,
                "bottleneck_proxy_to_verify": context["bottleneck_proxy_to_verify"],
                "price_data_interpretation": context["interpretation"],
                "evidence_needed_before_claiming_bottleneck": context["evidence_needed"],
            }
        )
    out = pd.DataFrame(rows)
    if not ytd.empty:
        out = out.merge(ytd, on="group", how="left")
    priority = {"high": 0, "medium-high": 1, "medium": 2, "low-medium": 3}
    out["_priority"] = out["bottleneck_sensitivity"].map(priority).fillna(9)
    out = out.sort_values(["_priority", "avg_pair_corr"], ascending=[True, False]).drop(columns=["_priority"])
    return out


def render_report(
    results: list[GroupResult],
    pair_summary: pd.DataFrame,
    member_summary: pd.DataFrame,
    yearly_summary: pd.DataFrame,
    yearly_scatter: pd.DataFrame,
    frequency_summary: pd.DataFrame,
    group_summary: pd.DataFrame,
    coverage: pd.DataFrame,
    role_deepdive: pd.DataFrame,
    member_financial_detail: pd.DataFrame,
    annual_balance: pd.DataFrame,
    fundamental_momentum: pd.DataFrame,
    company_yearly_growth: pd.DataFrame,
    analysis_start_date: str = ANALYSIS_START_DATE,
) -> str:
    bottleneck_summary = bottleneck_interpretation_rows(group_summary, yearly_summary)
    bottleneck_display = bottleneck_summary.copy()
    for col in ["avg_pair_corr", "pc1_share", "latest_12m_avg_pair_corr", "latest_year_avg_pair_corr", "latest_year_yoy_change"]:
        if col in bottleneck_display:
            bottleneck_display[col] = bottleneck_display[col].map(lambda x: num(x, 2))

    display_group = group_summary.copy()
    for col in ["avg_pair_corr", "median_pair_corr", "max_pair_corr", "min_pair_corr", "pc1_share", "latest_rolling_corr", "rolling_min", "rolling_max"]:
        display_group[col] = display_group[col].map(lambda x: num(x, 2))
    display_group["strong_pair_share"] = display_group["strong_pair_share"].map(pct)
    display_group["tickers"] = display_group["tickers"].map(lambda xs: ", ".join(xs))
    display_group["companies"] = display_group["companies"].map(lambda xs: ", ".join(xs))

    pair_display = pair_summary.copy()
    for col in ["pearson_corr", "beta_left_to_right", "same_direction_share"]:
        pair_display[col] = pair_display[col].map(lambda x: num(x, 2))

    member_display = member_summary.copy()
    for col in ["mean_corr_to_group", "median_corr_to_group", "max_corr_to_peer", "pc1_loading"]:
        member_display[col] = member_display[col].map(lambda x: num(x, 2))

    yearly_display = yearly_summary.copy()
    if not yearly_display.empty:
        for col in [
            "avg_pair_corr",
            "median_pair_corr",
            "max_pair_corr",
            "min_pair_corr",
            "pc1_share",
            "strong_pair_share",
            "avg_pair_corr_yoy_change",
            "pc1_share_yoy_change",
        ]:
            yearly_display[col] = yearly_display[col].map(lambda x: num(x, 2))

    frequency_display = frequency_summary.copy()
    if not frequency_display.empty:
        for col in [
            "avg_pair_corr",
            "median_pair_corr",
            "max_pair_corr",
            "min_pair_corr",
            "pc1_share",
            "strong_pair_share",
            "monthly_avg_pair_corr",
            "daily_avg_pair_corr",
            "corr_vs_monthly_delta",
            "monthly_vs_daily_delta",
        ]:
            frequency_display[col] = frequency_display[col].map(lambda x: num(x, 2))

    role_display = role_deepdive.copy()
    if not role_display.empty:
        for col in ["avg_mean_corr_to_group", "avg_pc1_loading"]:
            role_display[col] = role_display[col].map(lambda x: num(x, 2))
        for col in ["market_cap_usd_b", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
            if col in role_display:
                role_display[col] = role_display[col].map(lambda x: num(x, 1))
        for col in [
            "market_cap_usd_b_share_of_group",
            "revenue_usd_m_share_of_group",
            "operating_income_usd_m_share_of_group",
            "net_income_usd_m_share_of_group",
        ]:
            if col in role_display:
                role_display[col] = role_display[col].map(pct)

    member_financial_display = member_financial_detail.copy()
    if not member_financial_display.empty:
        for col in ["mean_corr_to_group", "max_corr_to_peer", "revenue_usd_m", "operating_income_usd_m", "net_income_usd_m"]:
            if col in member_financial_display:
                member_financial_display[col] = member_financial_display[col].map(lambda x: num(x, 2))
        for col in ["revenue_usd_m_share_of_group", "operating_income_usd_m_share_of_group", "net_income_usd_m_share_of_group"]:
            if col in member_financial_display:
                member_financial_display[col] = member_financial_display[col].map(pct)

    annual_balance_display = annual_balance.copy()
    annual_balance_story = "<p>No annual revenue/profit balance analysis available.</p>"
    if not annual_balance_display.empty:
        corr_revenue = annual_balance["annual_revenue_evenness"].corr(annual_balance["avg_pair_corr"]) if annual_balance["annual_revenue_evenness"].notna().sum() >= 3 else np.nan
        corr_profit = annual_balance["annual_op_income_evenness"].corr(annual_balance["avg_pair_corr"]) if annual_balance["annual_op_income_evenness"].notna().sum() >= 3 else np.nan
        consistent = int(annual_balance["hypothesis_read"].astype(str).str.startswith("consistent").sum())
        counter = int(annual_balance["hypothesis_read"].astype(str).str.startswith("counterexample").sum())
        annual_balance_story = (
            f"<p>가정 체크: section 내 연간 매출 비중이 더 고르게 분산될수록 avg pair corr가 높아지는지 봤다. "
            f"현재 표본에서 revenue evenness와 avg pair corr의 단순 상관은 <strong>{num(corr_revenue, 2)}</strong>, "
            f"operating-income evenness와 avg pair corr의 단순 상관은 <strong>{num(corr_profit, 2)}</strong>이다. "
            f"consistent case {consistent}개, counterexample {counter}개로, 인과라기보다 추가 확인용 screening signal로 읽는 것이 맞다.</p>"
        )
        for col in [
            "annual_revenue_hhi",
            "annual_revenue_effective_n",
            "annual_revenue_evenness",
            "annual_revenue_top1_share",
            "annual_op_income_hhi",
            "annual_op_income_effective_n",
            "annual_op_income_evenness",
            "annual_op_income_top1_share",
            "avg_pair_corr",
            "pc1_share",
            "strong_pair_share",
        ]:
            if col in annual_balance_display:
                annual_balance_display[col] = annual_balance_display[col].map(lambda x: num(x, 2))

    momentum_display = fundamental_momentum.copy()
    momentum_story = "<p>No section fundamental momentum data available.</p>"
    if not momentum_display.empty:
        revenue_plot_growth = fundamental_momentum[["revenue_yoy_growth", "revenue_qoq_growth"]].apply(
            lambda row: max([v for v in row if pd.notna(v) and -1 <= float(v) <= 5], default=np.nan),
            axis=1,
        )
        op_plot_growth = fundamental_momentum[["op_income_yoy_growth", "op_income_qoq_growth"]].apply(
            lambda row: max([v for v in row if pd.notna(v) and -1 <= float(v) <= 5], default=np.nan),
            axis=1,
        )
        corr_revenue_growth = revenue_plot_growth.corr(fundamental_momentum["avg_pair_corr"]) if revenue_plot_growth.notna().sum() >= 3 else np.nan
        corr_op_growth = op_plot_growth.corr(fundamental_momentum["avg_pair_corr"]) if op_plot_growth.notna().sum() >= 3 else np.nan
        top = fundamental_momentum.sort_values("avg_pair_corr", ascending=False).head(5)
        top_phrase = "; ".join(
            f"{row.group} {int(row.fiscal_year)}Q{int(row.fiscal_quarter)} corr {row.avg_pair_corr:.2f}, {row.best_growth_metric} {row.best_growth_rate * 100:.1f}%"
            for row in top.itertuples()
            if pd.notna(row.best_growth_rate)
        )
        momentum_story = (
            f"<p>각 분기마다 section 내 기업별 revenue/op-income YoY/QoQ 성장률의 평균을 계산하고, 해당 분기가 속한 연도의 avg pair corr와 매칭했다. "
            f"그래프는 revenue와 operating income을 분리했고, 각 그래프 안에서는 안정적인 범위(-100%~+500%) 안의 YoY/QoQ 중 큰 값을 사용한다. "
            f"revenue growth와 같은 연도 avg pair corr의 단순 상관은 <strong>{num(corr_revenue_growth, 2)}</strong>, "
            f"operating-income growth와의 단순 상관은 <strong>{num(corr_op_growth, 2)}</strong>이다. "
            f"상위 coupling 관측치: {esc(top_phrase)}.</p>"
        )
        for col in [
            "revenue_usd_m",
            "operating_income_usd_m",
            "revenue_yoy_growth",
            "revenue_qoq_growth",
            "op_income_yoy_growth",
            "op_income_qoq_growth",
            "best_growth_rate",
            "avg_pair_corr",
            "pc1_share",
            "strong_pair_share",
        ]:
            if col in momentum_display:
                if col.endswith("_growth") or col in {"best_growth_rate", "strong_pair_share"}:
                    momentum_display[col] = momentum_display[col].map(pct)
                else:
                    momentum_display[col] = momentum_display[col].map(lambda x: num(x, 2))

    company_growth_display = company_yearly_growth.copy()
    if not company_growth_display.empty:
        for col in [
            "revenue_annual_growth",
            "op_income_annual_growth",
            "company_avg_growth_rate",
            "strong_pair_share",
        ]:
            if col in company_growth_display:
                company_growth_display[col] = company_growth_display[col].map(pct)
        for col in ["avg_pair_corr", "pc1_share"]:
            if col in company_growth_display:
                company_growth_display[col] = company_growth_display[col].map(lambda x: num(x, 2))

    high = [r for r in results if r.classification == "high coupling"]
    moderate = [r for r in results if r.classification == "moderate coupling"]
    weak = [r for r in results if r.classification == "weak / fragmented"]
    scatter_json = yearly_scatter_payload(yearly_scatter)

    sections = []
    for r in results:
        pairs = pair_display[pair_display["group"] == r.group].head(12)
        members = member_display[member_display["group"] == r.group].copy()
        company_weight_detail = member_financial_display[member_financial_display["group"] == r.group].copy()
        core = members[members["member_role"] == "coupling core"]
        partial = members[members["member_role"] == "partial / bridge"]
        weak_members = members[members["member_role"] == "weakly coupled"]
        sections.append(
            f"""
      <section class="group-card" data-group="{esc(r.group)}">
        <h3>{esc(r.group)} <span>{esc(r.classification)}</span></h3>
        <p>{esc(r.interpretation)}</p>
        <div class="kpis">
          <div><b>{num(r.avg_pair_corr, 2)}</b><small>avg pair corr</small></div>
          <div><b>{num(r.pc1_share, 2)}</b><small>PC1 share</small></div>
          <div><b>{pct(r.strong_pair_share)}</b><small>strong pairs</small></div>
          <div><b>{r.n_assets}</b><small>stocks used</small></div>
        </div>
        <p class="small">Coverage: {esc(r.start_date)} to {esc(r.end_date)} · latest 12M avg pair corr {num(r.latest_rolling_corr, 2)} · rolling range {num(r.rolling_min, 2)} to {num(r.rolling_max, 2)}</p>
        <p class="small">Companies: {esc(', '.join(r.companies))}</p>
        <h4>Company yearly revenue growth vs yearly coupling</h4>
        <div class="chart">{company_yearly_growth_scatter_svg(company_yearly_growth, f"{r.group} company yearly revenue growth vs coupling", group=r.group, metric_family="revenue")}</div>
        <h4>Company yearly operating income growth vs yearly coupling</h4>
        <div class="chart">{company_yearly_growth_scatter_svg(company_yearly_growth, f"{r.group} company yearly operating income growth vs coupling", group=r.group, metric_family="op_income")}</div>
        {table_html(company_growth_display[company_growth_display["group"] == r.group], ["company", "fiscal_year", "annual_observations", "revenue_annual_growth", "revenue_growth_bucket_label", "op_income_annual_growth", "op_income_growth_bucket_label", "avg_pair_corr", "pc1_share"], max_rows=80) if not company_growth_display.empty else "<p class='small'>No company yearly growth data available.</p>"}
        <h4>Member coupling roles</h4>
        {table_html(members, ["company", "ticker", "member_role", "mean_corr_to_group", "max_corr_to_peer", "strong_link_count", "pc1_loading", "best_coupled_peer_company"])}
        <h4>Top pair links</h4>
        {table_html(pairs, ["left_company", "right_company", "observations", "pearson_corr", "same_direction_share", "start_date", "end_date"])}
      </section>
"""
        )

    group_options = "".join(f'<option value="{esc(r.group)}">{esc(r.group)}</option>' for r in results)
    role_financial_section = f"""
    <section class="section">
      <h2>Section Fundamental vs Comovement</h2>
      <p>여기서는 고정된 한 분기가 아니라 모든 분기의 section 평균 fundamental growth를 계산하고, 그 분기가 속한 연도의 평균 상관계수와 비교한다. 매출과 영업이익은 서로 성격이 달라서 그래프를 분리했다.</p>
      <p class="small">Revenue와 operating income은 DB의 quarterly financials를 사용한다. 각 기업별 YoY/QoQ growth를 먼저 계산한 뒤 section 평균을 만든다. 각 그래프는 해당 지표의 YoY/QoQ 중 안정적인 범위(-100%~+500%) 안에서 더 큰 값을 사용한다.</p>
      <h3>Revenue Growth vs Comovement</h3>
      <div class="chart">{section_fundamental_momentum_svg(fundamental_momentum, "Quarterly Section Revenue Growth vs Yearly Average Pair Correlation", metric_family="revenue")}</div>
      <h3>Operating Income Growth vs Comovement</h3>
      <div class="chart">{section_fundamental_momentum_svg(fundamental_momentum, "Quarterly Section Operating Income Growth vs Yearly Average Pair Correlation", metric_family="op_income")}</div>
      <h3>Interpretive read</h3>
      {momentum_story}
      <h3>Section momentum table</h3>
      {table_html(momentum_display, ["group", "fiscal_year", "fiscal_quarter", "period_key", "company_coverage", "revenue_yoy_growth", "revenue_qoq_growth", "op_income_yoy_growth", "op_income_qoq_growth", "best_growth_metric", "best_growth_rate", "avg_pair_corr", "pc1_share", "classification", "momentum_read"], max_rows=240) if not momentum_display.empty else "<p>No section momentum table available.</p>"}
    </section>
    <section class="section">
      <h2>Annual Revenue / Profit Balance Hypothesis</h2>
      <p>가정: 같은 section 안에서 연간 매출 또는 이익 비중이 특정 대형주 한두 개에 집중되지 않고 비슷하게 분포하면, 시장이 그 section을 더 하나의 공통 factor로 가격화해 주가 동조화가 강해질 수 있다.</p>
      <p class="small">이 분석은 <strong>{FINANCIAL_WEIGHT_YEAR} annual financials</strong>를 사용한다. Revenue/profit balance는 HHI와 effective N으로 측정한다. evenness는 effective N / coverage이며, 1에 가까울수록 기업별 비중이 고르게 퍼져 있다는 뜻이다.</p>
      {annual_balance_story}
      {table_html(annual_balance_display, ["group", "financial_year", "annual_revenue_coverage", "annual_revenue_evenness", "annual_revenue_top1_share", "annual_op_income_coverage", "annual_op_income_evenness", "annual_op_income_top1_share", "avg_pair_corr", "pc1_share", "classification", "hypothesis_read"], max_rows=80) if not annual_balance_display.empty else "<p>No annual balance table available.</p>"}
    </section>
"""

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stock Comovement / Coupling Report</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #172033; background: #eef2f7; line-height: 1.55; }}
    header {{ background: #10243d; color: #fff; padding: 36px 0; }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    h2 {{ margin: 32px 0 12px; }}
    h3 {{ margin: 0 0 8px; font-size: 20px; }}
    h4 {{ margin: 16px 0 6px; }}
    h3 span {{ font-size: 12px; color: #4a5568; background: #edf2f7; padding: 3px 7px; border-radius: 999px; margin-left: 8px; vertical-align: middle; }}
    a {{ color: #2b6cb0; }}
    main {{ padding: 24px 0 46px; }}
    .section, .group-card {{ background: #fff; border: 1px solid #d9e0ea; border-radius: 8px; padding: 18px; margin: 16px 0; }}
    .tabs {{ position: sticky; top: 0; z-index: 5; display: flex; gap: 8px; flex-wrap: wrap; background: rgba(238, 242, 247, 0.96); padding: 10px 0; backdrop-filter: blur(8px); }}
    .tab-button {{ border: 1px solid #cbd5e1; background: #fff; color: #26364d; border-radius: 7px; padding: 9px 12px; font-weight: 700; cursor: pointer; }}
    .tab-button.active {{ background: #10243d; color: #fff; border-color: #10243d; }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .filter-row {{ display: flex; gap: 10px; align-items: end; flex-wrap: wrap; margin: 10px 0 16px; }}
    .filter-row label {{ display: block; color: #5f6b7a; font-size: 12px; font-weight: 700; margin-bottom: 4px; }}
    .filter-row select {{ min-width: 260px; border: 1px solid #cbd5e1; border-radius: 7px; padding: 9px 10px; background: #fff; color: #172033; font-size: 14px; }}
    .small {{ color: #5f6b7a; font-size: 13px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 12px 0; }}
    .kpis div {{ border: 1px solid #d9e0ea; border-radius: 8px; padding: 10px; background: #f8fafc; }}
    .kpis b {{ display: block; font-size: 22px; }}
    .kpis small {{ color: #5f6b7a; }}
    .table-scroll {{ max-height: 360px; overflow: auto; border: 1px solid #d9e0ea; border-radius: 8px; margin-top: 10px; background: #fff; }}
    .table-scroll-compact {{ max-height: 420px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #d9e0ea; padding: 7px 8px; text-align: right; vertical-align: top; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{ text-align: left; }}
    th {{ position: sticky; top: 0; z-index: 1; background: #f4f7fb; color: #27364a; }}
    .chart {{ overflow-x: auto; border: 1px solid #d9e0ea; border-radius: 8px; padding: 8px; background: #fff; }}
    .heatmap-cell {{ cursor: pointer; transition: transform 120ms ease, outline-color 120ms ease; }}
    .heatmap-cell:hover, .heatmap-cell:focus {{ outline: 2px solid #111827; outline-offset: -2px; transform: translateY(-1px); }}
    .scatter-panel {{ margin-top: 12px; border: 1px solid #d9e0ea; border-radius: 8px; background: #fff; padding: 12px; }}
    .scatter-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; flex-wrap: wrap; }}
    .scatter-head h3 {{ margin: 0; }}
    .scatter-wrap {{ overflow-x: auto; }}
    .scatter-svg text {{ font-size: 12px; fill: #334155; }}
    .scatter-axis {{ stroke: #94a3b8; stroke-width: 1; }}
    .scatter-grid {{ stroke: #e2e8f0; stroke-width: 1; }}
    .scatter-point {{ opacity: 0.82; stroke: #fff; stroke-width: 1; }}
    .scatter-point:hover {{ opacity: 1; stroke: #111827; stroke-width: 1.5; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 8px 14px; margin-top: 8px; }}
    .legend-item {{ display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: #475569; }}
    .legend-swatch {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
    .chart-title {{ font-weight: 700; font-size: 14px; fill: #172033; }}
    .bar-label {{ font-size: 12px; fill: #334155; }}
    .financial-row-label {{ font-size: 11px; }}
    @media (max-width: 760px) {{ .kpis {{ grid-template-columns: repeat(2, 1fr); }} .wrap {{ padding: 0 14px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>Stock Comovement / Coupling Report</h1>
      <p>company_master.xlsx의 그룹 정의와 financials.db의 adjusted close 데이터를 매칭해, 데이터가 존재하는 그룹에 한해서 주가 동조화 현상을 분석했다.</p>
      <p class="small">Analysis window: {esc(analysis_start_date)} onward · Primary method: monthly log returns, Pearson pairwise correlation, 12-month rolling average pair correlation, PCA first component explained variance.</p>
    </div>
  </header>
  <main class="wrap">
    <nav class="tabs" aria-label="Report tabs">
      <button class="tab-button active" data-tab="comovement" type="button">Comovement</button>
      <button class="tab-button" data-tab="deepdive" type="button">Deep Dive</button>
      <button class="tab-button" data-tab="methodology" type="button">Methodology</button>
      <button class="tab-button" data-tab="coverage" type="button">Coverage</button>
    </nav>

    <section class="tab-panel active" id="tab-comovement">
    <section class="section">
      <h2>Executive Takeaways</h2>
      <p>분석 대상은 그룹 내 가격 데이터가 2개 종목 이상 존재하는 경우로 제한했다. 총 {len(results)}개 그룹이 분석 가능했고, high coupling {len(high)}개, moderate coupling {len(moderate)}개, weak/fragmented {len(weak)}개로 분류됐다.</p>
      <ul>
        <li><strong>가장 강한 동조화:</strong> {esc(results[0].group)} / avg pair corr {num(results[0].avg_pair_corr, 2)} / PC1 share {num(results[0].pc1_share, 2)}</li>
        <li><strong>해석 기준:</strong> 평균 pair correlation은 그룹 내 종목들이 월별 수익률 기준 얼마나 같이 움직였는지, PC1 share는 하나의 공통요인이 그룹 변동을 얼마나 설명하는지 보여준다.</li>
        <li><strong>주의:</strong> 상관은 coupling의 증거지만 인과관계는 아니다. 국가별 휴장일, 환율, 상장시장, 데이터 시작일 차이가 그룹별 결과에 영향을 준다.</li>
      </ul>
    </section>

    <section class="section">
      <h2>Classification Criteria</h2>
      <p>그룹 등급은 <strong>월별 수익률</strong> 기준 전체 평균 pair correlation과 PCA 공통요인 설명력을 함께 본다. <strong>High coupling</strong>은 avg pair corr ≥ 0.60 및 PC1 share ≥ 0.60, <strong>moderate coupling</strong>은 avg pair corr ≥ 0.35 또는 PC1/strong-pair 보조조건을 만족하는 경우, 그 외는 <strong>weak / fragmented</strong>로 분류했다.</p>
      <p>기업별 역할은 그룹 내 평균 연결도로 나눴다. <strong>Coupling core</strong>는 평균 대그룹 상관 ≥ {CORE_MEAN_CORR:.2f} 또는 strong link가 2개 이상인 종목, <strong>partial / bridge</strong>는 평균 상관 ≥ {PARTIAL_MEAN_CORR:.2f} 또는 특정 peer와 max corr ≥ 0.55인 종목, 나머지는 <strong>weakly coupled</strong>로 분류했다.</p>
      <p class="small">이 기준은 투자 판단용 절대 기준이 아니라, 같은 데이터셋 안에서 그룹과 구성원을 일관되게 분리하기 위한 operational threshold다.</p>
    </section>

    <section class="section">
      <h2>Yearly Coupling Timeline</h2>
      <p>연도별로 같은 그룹 내 <strong>monthly return coupling</strong>을 다시 계산했다. 이 표는 특정 연도에 어떤 섹션이 시장에서 같이 움직였는지, 그리고 어느 해에 coupling이 강화됐는지 보는 용도다.</p>
      <div class="chart">{yearly_heatmap_html(yearly_summary)}</div>
      <div class="scatter-panel" id="yearlyScatterPanel">
        <div class="scatter-head">
          <h3 id="scatterTitle">Company Return Scatter</h3>
          <p class="small" id="scatterMeta">Heatmap 셀을 클릭하면 해당 section/year의 기업별 월간 수익률 분포가 표시된다.</p>
        </div>
        <p class="small">x축은 해당 section의 동일월 평균 수익률, y축은 개별 기업 월간 수익률이다. 점들이 우상향 대각선 주변에 모이면 그 해에 기업들이 section factor와 함께 움직였다는 뜻이다.</p>
        <div class="scatter-wrap" id="scatterChart"></div>
        <div class="legend" id="scatterLegend"></div>
      </div>
      <h3>Year-by-year story</h3>
      {yearly_story_html(yearly_summary)}
      <h3>Yearly detail</h3>
      {table_html(yearly_display, ["year", "group", "n_assets", "observations", "avg_pair_corr", "pc1_share", "strong_pair_share", "avg_pair_corr_yoy_change"], max_rows=120)}
    </section>

    <section class="section">
      <h2>Group Ranking</h2>
      <div class="chart">{bar_svg(results, "avg_pair_corr", "Average Pairwise Correlation by Group")}</div>
      {table_html(display_group, ["group", "classification", "n_assets", "common_days", "avg_pair_corr", "median_pair_corr", "pc1_share", "strong_pair_share", "latest_rolling_corr", "tickers"])}
    </section>

    <section class="section">
      <h2>Frequency Cross-Check</h2>
      <p>메인 분석은 monthly return으로 통일했다. 아래 표는 daily/weekly/monthly 결과를 보조적으로 비교해, 월별 기준에서 잡히는 중기 coupling이 단기 noise 때문인지 아닌지 확인하기 위한 cross-check다.</p>
      {frequency_pivot_html(frequency_summary)}
      {frequency_story_html(frequency_summary)}
      <h3>Frequency detail</h3>
      {table_html(frequency_display, ["frequency", "group", "n_assets", "observations", "avg_pair_corr", "pc1_share", "strong_pair_share", "corr_vs_monthly_delta"], max_rows=90)}
    </section>

    <section class="section">
      <h2>Supply Chain Bottleneck Lens</h2>
      <p>이 리포트의 가격 데이터만으로 현재 병목 위치를 확정하지는 않는다. 대신 각 AI 공급망 section이 병목/shortage narrative에 얼마나 민감한지 사전 분류하고, 그 section의 월별 주가 coupling이 강한지 확인하는 <strong>screening framework</strong>로 사용한다.</p>
      <p>해석 규칙은 보수적으로 잡았다. <strong>Coupling 강화</strong>는 해당 section이 시장에서 하나의 병목 또는 공통 factor로 가격 반영되고 있다는 후보 신호다. 실제 shortage claim은 lead time, ASP, backlog, utilization, inventory, capex, grid interconnection 같은 운영 데이터가 붙어야 한다.</p>
      {table_html(bottleneck_display, ["group", "supply_chain_role", "bottleneck_sensitivity", "current_coupling_signal", "avg_pair_corr", "pc1_share", "latest_12m_avg_pair_corr", "latest_year_avg_pair_corr", "latest_year_yoy_change", "bottleneck_proxy_to_verify", "price_data_interpretation", "evidence_needed_before_claiming_bottleneck"], max_rows=30)}
      <p class="small">External grounding: IEA-reported data-center electricity demand growth; AI data-center power-system stress literature; public reporting on HBM/memory shortages; AI cooling and power-density literature. See methodology references file for URLs.</p>
    </section>
    </section>

    <section class="tab-panel" id="tab-deepdive">
    <section class="section">
      <h2>Group Deep Dives</h2>
      <div class="filter-row">
        <div>
          <label for="deepDiveGroupSelect">Section</label>
          <select id="deepDiveGroupSelect">
            {group_options}
          </select>
        </div>
        <p class="small" id="deepDiveFilterMeta"></p>
      </div>
      {''.join(sections)}
    </section>
    </section>

    <section class="tab-panel" id="tab-methodology">
    <section class="section">
      <h2>Methodology and Literature Grounding</h2>
      <p>주가 동조화 분석은 가격 레벨보다 수익률을 기준으로 한다. 가격은 비정상 시계열인 경우가 많아 단순 가격 상관이 spurious coupling을 만들 수 있기 때문이다. 이 리포트는 adjusted close의 월별 로그수익률을 기본 단위로 만들고, 같은 그룹 내 종목들의 pairwise correlation과 12개월 rolling correlation을 계산했다.</p>
      <p>문헌상 correlation matrix, spectral/PCA, network 방식은 주식 수익률 동조화와 cluster를 보는 표준적인 도구다. PCA의 첫 번째 component가 큰 비중을 차지하면 그룹 전체를 움직이는 common factor가 강하다고 해석할 수 있다. 다만 단순 상관 증가는 contagion이 아니라 interdependence일 수 있으므로, 여기서는 causal claim 없이 coupling strength로만 표현한다.</p>
      <p class="small">References: Fenn et al., “Temporal Evolution of Financial Market Correlations”; Heimo et al., “Spectral and network methods in the analysis of correlation matrices of stock returns”; Forbes & Rigobon, “No Contagion, Only Interdependence”; recent network-correlation literature on stock return comovement.</p>
    </section>
    </section>

    <section class="tab-panel" id="tab-coverage">
    <section class="section">
      <h2>Coverage Used</h2>
      <p>아래는 company_master.xlsx에서 financials.db와 매칭된 종목이다. <code>has_price_data</code>가 false인 종목은 DB company table에는 있으나 분석에 필요한 가격 row가 부족해 coupling 계산에서 제외했다.</p>
      {table_html(coverage.rename(columns={"group_3": "group", "display_name": "company", "ticker_x": "master_ticker"}), max_rows=150)}
    </section>
    </section>
  </main>
  <script id="yearlyScatterData" type="application/json">{scatter_json}</script>
  <script>
    (() => {{
      document.querySelectorAll(".tab-button").forEach(button => {{
        button.addEventListener("click", () => {{
          document.querySelectorAll(".tab-button").forEach(el => el.classList.remove("active"));
          document.querySelectorAll(".tab-panel").forEach(el => el.classList.remove("active"));
          button.classList.add("active");
          document.getElementById(`tab-${{button.dataset.tab}}`).classList.add("active");
          window.scrollTo({{ top: 0, behavior: "smooth" }});
        }});
      }});

      const deepDiveSelect = document.getElementById("deepDiveGroupSelect");
      const deepDiveMeta = document.getElementById("deepDiveFilterMeta");
      function applyDeepDiveFilter() {{
        if (!deepDiveSelect) return;
        const selected = deepDiveSelect.value;
        let visible = 0;
        document.querySelectorAll("#tab-deepdive .group-card").forEach(card => {{
          const show = card.dataset.group === selected;
          card.style.display = show ? "" : "none";
          if (show) visible += 1;
        }});
        if (deepDiveMeta) {{
          deepDiveMeta.textContent = visible ? `${{selected}} section detail only` : "No section detail available.";
        }}
      }}
      if (deepDiveSelect) {{
        deepDiveSelect.addEventListener("change", applyDeepDiveFilter);
        applyDeepDiveFilter();
      }}

      const data = JSON.parse(document.getElementById("yearlyScatterData").textContent || "{{}}");
      const chart = document.getElementById("scatterChart");
      const title = document.getElementById("scatterTitle");
      const meta = document.getElementById("scatterMeta");
      const legend = document.getElementById("scatterLegend");
      const colors = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#ea580c", "#0891b2", "#be123c", "#4d7c0f", "#9333ea", "#0f766e", "#b45309", "#64748b"];

      function extent(values) {{
        let min = Math.min(...values, 0);
        let max = Math.max(...values, 0);
        if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {{
          min = -5;
          max = 5;
        }}
        const pad = Math.max(2, (max - min) * 0.12);
        return [min - pad, max + pad];
      }}

      function draw(group, year) {{
        const key = `${{group}}||${{year}}`;
        const points = data[key] || [];
        title.textContent = `${{group}} · ${{year}} Company Return Scatter`;
        meta.textContent = points.length ? `${{points.length}} monthly company observations` : "No scatter observations available.";
        if (!points.length) {{
          chart.innerHTML = "<p class='small'>No scatter data for this cell.</p>";
          legend.innerHTML = "";
          return;
        }}
        const companies = [...new Set(points.map(p => p.company))];
        const colorMap = new Map(companies.map((c, i) => [c, colors[i % colors.length]]));
        const width = 920, height = 520;
        const margin = {{ left: 72, right: 34, top: 30, bottom: 62 }};
        const innerW = width - margin.left - margin.right;
        const innerH = height - margin.top - margin.bottom;
        const [xMin, xMax] = extent(points.map(p => p.x));
        const [yMin, yMax] = extent(points.map(p => p.y));
        const sx = x => margin.left + ((x - xMin) / (xMax - xMin)) * innerW;
        const sy = y => margin.top + innerH - ((y - yMin) / (yMax - yMin)) * innerH;
        const ticks = [-60, -40, -20, 0, 20, 40, 60].filter(t => t >= xMin && t <= xMax);
        const yTicks = [-80, -60, -40, -20, 0, 20, 40, 60, 80].filter(t => t >= yMin && t <= yMax);
        const diagStart = Math.max(xMin, yMin);
        const diagEnd = Math.min(xMax, yMax);
        let svg = `<svg class="scatter-svg" viewBox="0 0 ${{width}} ${{height}}" role="img" aria-label="Company return scatter for ${{group}} ${{year}}">`;
        for (const t of ticks) {{
          svg += `<line class="scatter-grid" x1="${{sx(t).toFixed(1)}}" y1="${{margin.top}}" x2="${{sx(t).toFixed(1)}}" y2="${{margin.top + innerH}}"></line>`;
          svg += `<text x="${{sx(t).toFixed(1)}}" y="${{height - 38}}" text-anchor="middle">${{t}}%</text>`;
        }}
        for (const t of yTicks) {{
          svg += `<line class="scatter-grid" x1="${{margin.left}}" y1="${{sy(t).toFixed(1)}}" x2="${{margin.left + innerW}}" y2="${{sy(t).toFixed(1)}}"></line>`;
          svg += `<text x="${{margin.left - 10}}" y="${{sy(t).toFixed(1)}}" text-anchor="end" dominant-baseline="middle">${{t}}%</text>`;
        }}
        svg += `<line class="scatter-axis" x1="${{margin.left}}" y1="${{sy(0).toFixed(1)}}" x2="${{margin.left + innerW}}" y2="${{sy(0).toFixed(1)}}"></line>`;
        svg += `<line class="scatter-axis" x1="${{sx(0).toFixed(1)}}" y1="${{margin.top}}" x2="${{sx(0).toFixed(1)}}" y2="${{margin.top + innerH}}"></line>`;
        if (diagStart < diagEnd) {{
          svg += `<line x1="${{sx(diagStart).toFixed(1)}}" y1="${{sy(diagStart).toFixed(1)}}" x2="${{sx(diagEnd).toFixed(1)}}" y2="${{sy(diagEnd).toFixed(1)}}" stroke="#0f172a" stroke-width="1.2" stroke-dasharray="5 5" opacity="0.55"></line>`;
        }}
        for (const p of points) {{
          const tip = `${{p.company}} (${{p.ticker}}) · ${{p.date}}\\nsection avg: ${{p.x.toFixed(1)}}%\\ncompany: ${{p.y.toFixed(1)}}%`;
          svg += `<circle class="scatter-point" cx="${{sx(p.x).toFixed(1)}}" cy="${{sy(p.y).toFixed(1)}}" r="4.2" fill="${{colorMap.get(p.company)}}"><title>${{tip}}</title></circle>`;
        }}
        svg += `<text x="${{margin.left + innerW / 2}}" y="${{height - 12}}" text-anchor="middle">Section average monthly return</text>`;
        svg += `<text transform="translate(18 ${{margin.top + innerH / 2}}) rotate(-90)" text-anchor="middle">Company monthly return</text>`;
        svg += "</svg>";
        chart.innerHTML = svg;
        legend.innerHTML = companies.map(c => `<span class="legend-item"><span class="legend-swatch" style="background:${{colorMap.get(c)}}"></span>${{c}}</span>`).join("");
      }}

      document.querySelectorAll(".heatmap-cell").forEach(cell => {{
        const activate = () => {{
          document.querySelectorAll(".heatmap-cell").forEach(c => c.classList.remove("active"));
          cell.classList.add("active");
          draw(cell.dataset.group, cell.dataset.year);
          document.getElementById("yearlyScatterPanel").scrollIntoView({{ behavior: "smooth", block: "nearest" }});
        }};
        cell.addEventListener("click", activate);
        cell.addEventListener("keydown", event => {{
          if (event.key === "Enter" || event.key === " ") {{
            event.preventDefault();
            activate();
          }}
        }});
      }});
      const firstCell = document.querySelector(".heatmap-cell");
      if (firstCell) {{
        draw(firstCell.dataset.group, firstCell.dataset.year);
      }}
    }})();
  </script>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in html_doc.splitlines()) + "\n"


def output_paths(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    return {
        "html": root / "stock_comovement_coupling_report.html",
        "group": root / "group_comovement_summary.csv",
        "pair": root / "pairwise_comovement_summary.csv",
        "member": root / "member_coupling_summary.csv",
        "yearly": root / "yearly_group_coupling_summary.csv",
        "frequency": root / "frequency_group_coupling_summary.csv",
        "bottleneck": root / "bottleneck_interpretation_summary.csv",
        "role_deepdive": root / "member_role_financial_deepdive.csv",
        "company_weight": root / "member_company_financial_weights.csv",
        "annual_balance": root / "annual_financial_balance_vs_coupling.csv",
        "fundamental_momentum": root / "section_fundamental_momentum_vs_comovement.csv",
        "company_yearly_growth": root / "company_yearly_growth_vs_comovement.csv",
        "coverage": root / "ticker_coverage_used.csv",
    }


def write_report_outputs(
    results: list[GroupResult],
    pair_summary: pd.DataFrame,
    member_summary: pd.DataFrame,
    yearly_summary: pd.DataFrame,
    yearly_scatter: pd.DataFrame,
    frequency_summary: pd.DataFrame,
    group_summary: pd.DataFrame,
    coverage: pd.DataFrame,
    role_deepdive: pd.DataFrame,
    member_financial_detail: pd.DataFrame,
    annual_balance: pd.DataFrame,
    fundamental_momentum: pd.DataFrame,
    company_yearly_growth: pd.DataFrame,
    output_dir: str | Path = ROOT,
    analysis_start_date: str = ANALYSIS_START_DATE,
) -> dict[str, Path]:
    paths = output_paths(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    bottleneck_summary = bottleneck_interpretation_rows(group_summary, yearly_summary)
    group_summary.to_csv(paths["group"], index=False)
    pair_summary.to_csv(paths["pair"], index=False)
    member_summary.to_csv(paths["member"], index=False)
    yearly_summary.to_csv(paths["yearly"], index=False)
    frequency_summary.to_csv(paths["frequency"], index=False)
    bottleneck_summary.to_csv(paths["bottleneck"], index=False)
    role_deepdive.to_csv(paths["role_deepdive"], index=False)
    member_financial_detail.to_csv(paths["company_weight"], index=False)
    annual_balance.to_csv(paths["annual_balance"], index=False)
    fundamental_momentum.to_csv(paths["fundamental_momentum"], index=False)
    company_yearly_growth.to_csv(paths["company_yearly_growth"], index=False)
    coverage.to_csv(paths["coverage"], index=False)
    paths["html"].write_text(
        render_report(
            results,
            pair_summary,
            member_summary,
            yearly_summary,
            yearly_scatter,
            frequency_summary,
            group_summary,
            coverage,
            role_deepdive,
            member_financial_detail,
            annual_balance,
            fundamental_momentum,
            company_yearly_growth,
            analysis_start_date=analysis_start_date,
        ),
        encoding="utf-8",
    )
    return paths


def generate_report_from_dataframe(
    df: pd.DataFrame,
    output_dir: str | Path,
    analysis_start_date: str | None = "2012-01-01",
) -> dict[str, Path]:
    """Run the full comovement analysis from a generic DataFrame and write HTML/CSV outputs.

    Supported input shapes:
    - price-wide rows: date, section, optional companyname, ticker, adjusted close
    - long item rows: ticker, section, item, date, value

    For long item rows, adjusted_close drives the stock comovement analysis.
    Quarterly financial rows feed section momentum and financial weights; annual
    financial rows are also built by ticker-year and feed company annual YoY
    growth in the Deep Dive. If the input has quarterly revenue/profit rows,
    annual revenue/profit is approximated by summing the quarters per year.

    Example:
        paths = generate_report_from_dataframe(my_df, "outputs/comovement", analysis_start_date="2012-01-01")
        print(paths["html"])
    """
    is_long_item = all(_optional_external_column(df, field) for field in ["ticker", "section", "item", "date", "value"])
    if is_long_item:
        matched, prices, financials_source, annual_financials = normalize_long_item_dataframe(df, analysis_start_date=analysis_start_date)
    else:
        matched, prices = normalize_price_dataframe(df, analysis_start_date=analysis_start_date)
        financials_source = None
        annual_financials = None
    results, pair_summary, member_summary, yearly_summary, yearly_scatter, frequency_summary, group_summary, coverage, role_deepdive, member_financial_detail, annual_balance, fundamental_momentum, company_yearly_growth = analyze_dataset(
        matched,
        prices,
        financials_source=financials_source,
        annual_financials=annual_financials,
    )
    if not results:
        raise ValueError("No analyzable sections found. Need at least two tickers per section with enough observations.")
    return write_report_outputs(
        results,
        pair_summary,
        member_summary,
        yearly_summary,
        yearly_scatter,
        frequency_summary,
        group_summary,
        coverage,
        role_deepdive,
        member_financial_detail,
        annual_balance,
        fundamental_momentum,
        company_yearly_growth,
        output_dir=output_dir,
        analysis_start_date=analysis_start_date or "",
    )


def main() -> None:
    results, pair_summary, member_summary, yearly_summary, yearly_scatter, frequency_summary, group_summary, coverage, role_deepdive, member_financial_detail, annual_balance, fundamental_momentum, company_yearly_growth = analyze()
    paths = write_report_outputs(results, pair_summary, member_summary, yearly_summary, yearly_scatter, frequency_summary, group_summary, coverage, role_deepdive, member_financial_detail, annual_balance, fundamental_momentum, company_yearly_growth, output_dir=ROOT, analysis_start_date=ANALYSIS_START_DATE)
    print(f"groups={len(results)} pairs={len(pair_summary)}")
    for path in paths.values():
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
