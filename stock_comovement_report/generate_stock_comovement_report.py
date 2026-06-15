from __future__ import annotations

import html
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
OUT_COVERAGE_CSV = ROOT / "ticker_coverage_used.csv"
OUT_REFERENCES_MD = ROOT / "comovement_methodology_references.md"

BASE_FREQUENCY = "monthly"
MIN_OBS = 18
YEARLY_MIN_OBS = 4
ROLLING_WINDOW = 12
STRONG_CORR = 0.65
COUPLING_CORR = 0.50
CORE_MEAN_CORR = 0.50
PARTIAL_MEAN_CORR = 0.35
STRONG_LINK_CORR = 0.65


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


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master = pd.read_excel(MASTER_PATH)
    master["ticker_norm"] = master["ticker"].map(norm_ticker)

    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query("select ticker, slug, name, segments, hq_country from companies", conn)
        prices = pd.read_sql_query(
            """
            select ticker, price_date, adj_close_usd
            from stock_prices
            where adj_close_usd is not null
            order by ticker, price_date
            """,
            conn,
        )
    prices["price_date"] = pd.to_datetime(prices["price_date"])
    prices["adj_close_usd"] = pd.to_numeric(prices["adj_close_usd"], errors="coerce")

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
    return matched, companies, prices


def price_matrix(prices: pd.DataFrame, tickers: list[str], frequency: str = "daily") -> pd.DataFrame:
    px = prices[prices["ticker"].isin(tickers)].pivot(index="price_date", columns="ticker", values="adj_close_usd").sort_index()
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


def analyze() -> tuple[list[GroupResult], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matched, companies, prices = load_data()
    matched["display_name"] = matched.apply(
        lambda row: row["name"] if str(row["company_name"]).strip().upper() == str(row["ticker_x"]).strip().upper() else row["company_name"],
        axis=1,
    )
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
        all_frequency_rows.extend(frequency_group_rows(group, prices, active_cols))

    group_results.sort(key=lambda r: (r.avg_pair_corr, r.pc1_share), reverse=True)
    pair_summary = pd.DataFrame(all_pair_rows).sort_values(["group", "pearson_corr"], ascending=[True, False])
    member_summary = pd.DataFrame(all_member_rows).sort_values(["group", "member_role", "mean_corr_to_group"], ascending=[True, True, False])
    yearly_summary = pd.DataFrame(all_yearly_rows).sort_values(["year", "avg_pair_corr"], ascending=[True, False])
    if not yearly_summary.empty:
        yearly_summary["avg_pair_corr_yoy_change"] = yearly_summary.groupby("group")["avg_pair_corr"].diff()
        yearly_summary["pc1_share_yoy_change"] = yearly_summary.groupby("group")["pc1_share"].diff()
    frequency_summary = pd.DataFrame(all_frequency_rows).sort_values(["frequency", "avg_pair_corr"], ascending=[True, False])
    if not frequency_summary.empty:
        monthly_base = frequency_summary[frequency_summary["frequency"] == "monthly"][["group", "avg_pair_corr"]].rename(columns={"avg_pair_corr": "monthly_avg_pair_corr"})
        daily_base = frequency_summary[frequency_summary["frequency"] == "daily"][["group", "avg_pair_corr"]].rename(columns={"avg_pair_corr": "daily_avg_pair_corr"})
        frequency_summary = frequency_summary.merge(monthly_base, on="group", how="left").merge(daily_base, on="group", how="left")
        frequency_summary["corr_vs_monthly_delta"] = frequency_summary["avg_pair_corr"] - frequency_summary["monthly_avg_pair_corr"]
        frequency_summary["monthly_vs_daily_delta"] = frequency_summary["monthly_avg_pair_corr"] - frequency_summary["daily_avg_pair_corr"]
    group_summary = pd.DataFrame([r.__dict__ for r in group_results])
    return group_results, pair_summary, member_summary, yearly_summary, frequency_summary, group_summary, coverage


def table_html(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    if columns is not None:
        df = df[columns]
    if max_rows is not None:
        df = df.head(max_rows)
    header = "".join(f"<th>{esc(c)}</th>" for c in df.columns)
    rows = []
    for _, row in df.iterrows():
        rows.append("<tr>" + "".join(f"<td>{esc(row[c])}</td>" for c in df.columns) + "</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


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
    pivot = yearly_summary.pivot(index="group", columns="year", values="avg_pair_corr")
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
                cells.append(f'<td style="background:{bg};color:{fg};font-weight:650">{num(float(val), 2)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


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
    pivot = frequency_summary.pivot(index="group", columns="frequency", values="avg_pair_corr")
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
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


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
    frequency_summary: pd.DataFrame,
    group_summary: pd.DataFrame,
    coverage: pd.DataFrame,
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

    high = [r for r in results if r.classification == "high coupling"]
    moderate = [r for r in results if r.classification == "moderate coupling"]
    weak = [r for r in results if r.classification == "weak / fragmented"]

    sections = []
    for r in results:
        pairs = pair_display[pair_display["group"] == r.group].head(12)
        members = member_display[member_display["group"] == r.group].copy()
        core = members[members["member_role"] == "coupling core"]
        partial = members[members["member_role"] == "partial / bridge"]
        weak_members = members[members["member_role"] == "weakly coupled"]
        sections.append(
            f"""
      <section class="group-card">
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
        <h4>Coupling core vs weak members</h4>
        <p class="small">Core: {esc(', '.join(core["company"].tolist()) or 'none')} · Partial/bridge: {esc(', '.join(partial["company"].tolist()) or 'none')} · Weak: {esc(', '.join(weak_members["company"].tolist()) or 'none')}</p>
        {table_html(members, ["company", "ticker", "member_role", "mean_corr_to_group", "max_corr_to_peer", "strong_link_count", "pc1_loading", "best_coupled_peer_company"])}
        <h4>Top pair links</h4>
        {table_html(pairs, ["left_company", "right_company", "observations", "pearson_corr", "same_direction_share", "start_date", "end_date"])}
      </section>
"""
        )

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
    .small {{ color: #5f6b7a; font-size: 13px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 12px 0; }}
    .kpis div {{ border: 1px solid #d9e0ea; border-radius: 8px; padding: 10px; background: #f8fafc; }}
    .kpis b {{ display: block; font-size: 22px; }}
    .kpis small {{ color: #5f6b7a; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid #d9e0ea; padding: 7px 8px; text-align: right; vertical-align: top; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{ text-align: left; }}
    th {{ background: #f4f7fb; color: #27364a; }}
    .chart {{ overflow-x: auto; border: 1px solid #d9e0ea; border-radius: 8px; padding: 8px; background: #fff; }}
    .chart-title {{ font-weight: 700; font-size: 14px; fill: #172033; }}
    .bar-label {{ font-size: 12px; fill: #334155; }}
    @media (max-width: 760px) {{ .kpis {{ grid-template-columns: repeat(2, 1fr); }} .wrap {{ padding: 0 14px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>Stock Comovement / Coupling Report</h1>
      <p>company_master.xlsx의 그룹 정의와 financials.db의 adjusted close 데이터를 매칭해, 데이터가 존재하는 그룹에 한해서 주가 동조화 현상을 분석했다.</p>
      <p class="small">Primary method: monthly log returns, Pearson pairwise correlation, 12-month rolling average pair correlation, PCA first component explained variance.</p>
    </div>
  </header>
  <main class="wrap">
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

    <section class="section">
      <h2>Yearly Coupling Timeline</h2>
      <p>연도별로 같은 그룹 내 <strong>monthly return coupling</strong>을 다시 계산했다. 이 표는 특정 연도에 어떤 섹션이 시장에서 같이 움직였는지, 그리고 어느 해에 coupling이 강화됐는지 보는 용도다.</p>
      <div class="chart">{yearly_heatmap_html(yearly_summary)}</div>
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
      <h2>Methodology and Literature Grounding</h2>
      <p>주가 동조화 분석은 가격 레벨보다 수익률을 기준으로 한다. 가격은 비정상 시계열인 경우가 많아 단순 가격 상관이 spurious coupling을 만들 수 있기 때문이다. 이 리포트는 adjusted close의 월별 로그수익률을 기본 단위로 만들고, 같은 그룹 내 종목들의 pairwise correlation과 12개월 rolling correlation을 계산했다.</p>
      <p>문헌상 correlation matrix, spectral/PCA, network 방식은 주식 수익률 동조화와 cluster를 보는 표준적인 도구다. PCA의 첫 번째 component가 큰 비중을 차지하면 그룹 전체를 움직이는 common factor가 강하다고 해석할 수 있다. 다만 단순 상관 증가는 contagion이 아니라 interdependence일 수 있으므로, 여기서는 causal claim 없이 coupling strength로만 표현한다.</p>
      <p class="small">References: Fenn et al., “Temporal Evolution of Financial Market Correlations”; Heimo et al., “Spectral and network methods in the analysis of correlation matrices of stock returns”; Forbes & Rigobon, “No Contagion, Only Interdependence”; recent network-correlation literature on stock return comovement.</p>
    </section>

    <section class="section">
      <h2>Group Deep Dives</h2>
      {''.join(sections)}
    </section>

    <section class="section">
      <h2>Coverage Used</h2>
      <p>아래는 company_master.xlsx에서 financials.db와 매칭된 종목이다. <code>has_price_data</code>가 false인 종목은 DB company table에는 있으나 분석에 필요한 가격 row가 부족해 coupling 계산에서 제외했다.</p>
      {table_html(coverage.rename(columns={"group_3": "group", "display_name": "company", "ticker_x": "master_ticker"}), max_rows=150)}
    </section>
  </main>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in html_doc.splitlines()) + "\n"


def main() -> None:
    results, pair_summary, member_summary, yearly_summary, frequency_summary, group_summary, coverage = analyze()
    bottleneck_summary = bottleneck_interpretation_rows(group_summary, yearly_summary)
    group_summary.to_csv(OUT_GROUP_CSV, index=False)
    pair_summary.to_csv(OUT_PAIR_CSV, index=False)
    member_summary.to_csv(OUT_MEMBER_CSV, index=False)
    yearly_summary.to_csv(OUT_YEARLY_CSV, index=False)
    frequency_summary.to_csv(OUT_FREQUENCY_CSV, index=False)
    bottleneck_summary.to_csv(OUT_BOTTLENECK_CSV, index=False)
    coverage.to_csv(OUT_COVERAGE_CSV, index=False)
    OUT_HTML.write_text(render_report(results, pair_summary, member_summary, yearly_summary, frequency_summary, group_summary, coverage), encoding="utf-8")
    print(f"groups={len(results)} pairs={len(pair_summary)}")
    print(f"wrote {OUT_HTML}")
    print(f"wrote {OUT_GROUP_CSV}")
    print(f"wrote {OUT_PAIR_CSV}")
    print(f"wrote {OUT_MEMBER_CSV}")
    print(f"wrote {OUT_YEARLY_CSV}")
    print(f"wrote {OUT_FREQUENCY_CSV}")
    print(f"wrote {OUT_BOTTLENECK_CSV}")
    print(f"wrote {OUT_COVERAGE_CSV}")


if __name__ == "__main__":
    main()
