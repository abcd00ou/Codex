from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_LAGS = list(range(-8, 9))

FS_ITEM_ALIASES = {
    "revenue": "revenue",
    "sales": "revenue",
    "매출": "revenue",
    "cost_of_revenue": "cost_of_revenue",
    "cost of revenue": "cost_of_revenue",
    "cost_of_sales": "cost_of_revenue",
    "cost of sales": "cost_of_revenue",
    "cogs": "cost_of_revenue",
    "gross_profit": "gross_profit",
    "gross profit": "gross_profit",
    "capex": "capex",
    "capital_expenditure": "capex",
    "capital expenditure": "capex",
    "inventory": "inventory",
    "inventories": "inventory",
    "operating_income": "operating_income",
    "operating income": "operating_income",
    "net_income": "net_income",
    "net income": "net_income",
}


def esc(value: object) -> str:
    return html.escape("" if pd.isna(value) else str(value))


def num(value: object, digits: int = 3) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):,.{digits}f}"


def normalize_item(value: object) -> str | None:
    if pd.isna(value):
        return None
    key = str(value).strip().lower().replace("-", "_")
    compact = "_".join(key.replace("_", " ").split())
    spaced = compact.replace("_", " ")
    return FS_ITEM_ALIASES.get(compact) or FS_ITEM_ALIASES.get(spaced)


def parse_quarter(value: object) -> pd.Period | pd.NaT:
    if pd.isna(value):
        return pd.NaT
    text = str(value).strip().upper().replace(" ", "")
    if "-Q" in text:
        year, quarter = text.split("-Q", 1)
        try:
            return pd.Period(f"{int(year)}Q{int(quarter)}", freq="Q")
        except Exception:
            return pd.NaT
    if "Q" in text and len(text) <= 7:
        year, quarter = text.split("Q", 1)
        try:
            return pd.Period(f"{int(year)}Q{int(quarter)}", freq="Q")
        except Exception:
            return pd.NaT
    date = pd.to_datetime(value, errors="coerce")
    if pd.isna(date):
        return pd.NaT
    return pd.Period(date, freq="Q")


def yoy_current_ratio(series: pd.Series) -> pd.Series:
    previous = series.shift(4)
    out = (series - previous) / series
    out[series == 0] = np.nan
    return out.replace([np.inf, -np.inf], np.nan)


def normalize_financial_long_dataframe(raw: pd.DataFrame, start_quarter: str | None = None) -> pd.DataFrame:
    """Normalize long financial rows into section-quarter metric columns.

    Expected logical columns:
    - section
    - fs_item
    - date
    - value

    Optional company-level rows are summed to section-quarter totals.
    """
    required = {"section", "fs_item", "date", "value"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Input dataframe missing required columns: {sorted(missing)}")

    data = raw[["section", "fs_item", "date", "value"]].copy()
    data["section"] = data["section"].astype(str).str.strip()
    data["metric"] = data["fs_item"].map(normalize_item)
    data["quarter_period"] = data["date"].map(parse_quarter)
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["section", "metric", "quarter_period", "value"])
    if start_quarter:
        data = data[data["quarter_period"] >= parse_quarter(start_quarter)]
    if data.empty:
        raise ValueError("No valid rows remain after normalization.")

    wide = (
        data.pivot_table(
            index=["section", "quarter_period"],
            columns="metric",
            values="value",
            aggfunc="sum",
        )
        .reset_index()
        .rename_axis(None, axis=1)
        .sort_values(["section", "quarter_period"])
    )
    if "cost_of_revenue" not in wide.columns and {"revenue", "gross_profit"} <= set(wide.columns):
        wide["cost_of_revenue"] = wide["revenue"] - wide["gross_profit"]
    wide["calendar_quarter"] = wide["quarter_period"].astype(str).str.replace("Q", "-Q", regex=False)
    return wide


def add_transforms(section_quarterly: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    out = section_quarterly.copy()
    for metric in metrics:
        if metric not in out.columns:
            raise ValueError(f"Metric '{metric}' not found in dataframe.")
        out[metric] = pd.to_numeric(out[metric], errors="coerce")
        out[f"{metric}_yoy"] = out.groupby("section", group_keys=False)[metric].transform(yoy_current_ratio)
    return out


def compute_section_pair_lags(
    section_quarterly: pd.DataFrame,
    source_section: str,
    target_section: str,
    source_metric: str = "cost_of_revenue",
    target_metric: str = "revenue",
    lags: list[int] | None = None,
    min_obs: int = 4,
) -> pd.DataFrame:
    """Compute all lead-lag correlations from -8Q to +8Q by default.

    Positive lag means source metric at t is compared with target metric at t+lag.
    Negative lag means target metric is observed before source metric.
    """
    lags = DEFAULT_LAGS if lags is None else lags
    source_col = f"{source_metric}_yoy"
    target_col = f"{target_metric}_yoy"
    data = add_transforms(section_quarterly, sorted({source_metric, target_metric}))
    source = (
        data[data["section"] == source_section]
        .set_index("quarter_period")
        .sort_index()[source_col]
        .rename("source")
    )
    target = (
        data[data["section"] == target_section]
        .set_index("quarter_period")
        .sort_index()[target_col]
        .rename("target")
    )
    if source.empty:
        raise ValueError(f"No rows found for source section '{source_section}'.")
    if target.empty:
        raise ValueError(f"No rows found for target section '{target_section}'.")

    rows = []
    for lag in lags:
        aligned = pd.concat([source, target.shift(-lag)], axis=1).dropna()
        if len(aligned) < min_obs:
            corr = beta = np.nan
        else:
            corr = float(aligned["source"].corr(aligned["target"]))
            variance = float(aligned["source"].var())
            beta = float(aligned["source"].cov(aligned["target"]) / variance) if variance else np.nan
        rows.append(
            {
                "source_section": source_section,
                "target_section": target_section,
                "source_metric": source_metric,
                "target_metric": target_metric,
                "lag_quarters": lag,
                "timing": lag_timing(lag),
                "observations": int(len(aligned)),
                "corr": corr,
                "r_squared": corr * corr if not pd.isna(corr) else np.nan,
                "beta_target_per_1_source": beta,
            }
        )
    return pd.DataFrame(rows)


def lag_timing(lag: int) -> str:
    if lag > 0:
        return "source leads"
    if lag < 0:
        return "target leads"
    return "same quarter"


def best_lag_summary(lag_df: pd.DataFrame) -> dict[str, object]:
    valid = lag_df.dropna(subset=["corr"])
    if valid.empty:
        return {}
    best_positive = valid[valid["corr"] > 0]
    best = best_positive.loc[best_positive["corr"].idxmax()] if not best_positive.empty else valid.loc[valid["corr"].abs().idxmax()]
    best_abs = valid.loc[valid["corr"].abs().idxmax()]
    return {
        "best_lag_quarters": int(best["lag_quarters"]),
        "best_timing": best["timing"],
        "best_corr": float(best["corr"]),
        "best_observations": int(best["observations"]),
        "best_abs_lag_quarters": int(best_abs["lag_quarters"]),
        "best_abs_corr": float(best_abs["corr"]),
    }


def lag_bar_svg(lag_df: pd.DataFrame, title: str) -> str:
    width = 1040
    height = 330
    left, right, top, bottom = 72, 34, 44, 56
    chart_w = width - left - right
    zero_y = top + (height - top - bottom) / 2
    step = chart_w / len(lag_df)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        "<style>.axis{stroke:#aab5ae}.tick{stroke:#e0e6e2}.label{font-size:11px;fill:#5f6b64}.title{font-size:15px;font-weight:700;fill:#17211c}.bar-label{font-size:11px;fill:#17211c;font-weight:650}</style>",
        f'<text x="{left}" y="24" class="title">{esc(title)}</text>',
        f'<line x1="{left}" x2="{width-right}" y1="{zero_y}" y2="{zero_y}" class="axis"/>',
    ]
    for i, row in lag_df.reset_index(drop=True).iterrows():
        lag = int(row["lag_quarters"])
        x = left + i * step + 4
        parts.append(f'<line x1="{x+step/2:.1f}" x2="{x+step/2:.1f}" y1="{top}" y2="{height-bottom}" class="tick"/>')
        corr = row["corr"]
        if pd.isna(corr):
            parts.append(f'<rect x="{x:.1f}" y="{zero_y-2:.1f}" width="{step-8:.1f}" height="4" fill="#e5e9e6"/>')
        else:
            bar_h = min((height - top - bottom) / 2 - 10, abs(float(corr)) * 110)
            y = zero_y - bar_h if corr >= 0 else zero_y
            color = "#087f5b" if corr >= 0 else "#b03737"
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{step-8:.1f}" height="{bar_h:.1f}" fill="{color}" opacity="0.82"/>')
        parts.append(f'<text x="{x+step/2:.1f}" y="{height-26}" text-anchor="middle" class="label">{lag:+d}Q</text>')
    parts.append(f'<text x="10" y="{zero_y-4:.1f}" class="label">corr 0</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def lag_table_html(lag_df: pd.DataFrame) -> str:
    rows = []
    for _, row in lag_df.iterrows():
        rows.append(
            "<tr>"
            f"<td>{int(row['lag_quarters']):+d}Q</td>"
            f"<td>{esc(row['timing'])}</td>"
            f"<td>{int(row['observations'])}</td>"
            f"<td>{num(row['corr'], 3)}</td>"
            f"<td>{num(row['r_squared'], 3)}</td>"
            f"<td>{num(row['beta_target_per_1_source'], 3)}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Lag</th><th>Timing</th><th>Obs</th><th>Corr</th><th>R2</th><th>Beta</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def build_pair_html(lag_df: pd.DataFrame, output_title: str) -> str:
    first = lag_df.iloc[0]
    summary = best_lag_summary(lag_df)
    summary_html = ""
    if summary:
        summary_html = (
            f"<p class=\"note\">Best positive relation: <b>{summary['best_lag_quarters']:+d}Q</b> "
            f"({esc(summary['best_timing'])}), corr={num(summary['best_corr'], 3)}, "
            f"n={summary['best_observations']}. Strongest absolute relation is "
            f"{summary['best_abs_lag_quarters']:+d}Q, corr={num(summary['best_abs_corr'], 3)}.</p>"
        )
    title = (
        output_title
        or f"{first['source_section']} {first['source_metric']} -> {first['target_section']} {first['target_metric']}"
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:#17211c; background:#f8faf8; }}
    header {{ padding:28px 38px 18px; background:#eaf3ee; border-bottom:1px solid #d8ded9; }}
    main {{ padding:0 38px 42px; max-width:1160px; }}
    h1 {{ margin:0 0 8px; font-size:26px; }}
    p {{ line-height:1.55; }}
    .meta {{ color:#5f6b64; font-size:13px; }}
    .note {{ background:#fff9e8; border:1px solid #ead28a; padding:12px 14px; border-radius:8px; }}
    table {{ border-collapse:collapse; width:100%; background:#fff; border:1px solid #d8ded9; font-size:13px; }}
    th, td {{ padding:8px 9px; border-bottom:1px solid #d8ded9; text-align:right; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align:left; }}
    thead th {{ background:#eef4f0; }}
    svg {{ width:100%; height:auto; background:#fff; border:1px solid #d8ded9; border-radius:8px; }}
    code {{ background:#edf2ee; padding:2px 4px; border-radius:4px; }}
  </style>
</head>
<body>
<header>
  <h1>{esc(title)}</h1>
  <div class="meta">Lag range: -8Q to +8Q · Transform: (x_t - x_(t-4)) / x_t</div>
</header>
<main>
  <p>Positive lag means source section at quarter t is compared with target section at t+lag. Negative lag means target moves before source.</p>
  {summary_html}
  {lag_bar_svg(lag_df, title)}
  <h2>Lag Table</h2>
  {lag_table_html(lag_df)}
</main>
</body>
</html>
"""


def analyze_section_pair(
    df: pd.DataFrame,
    source_section: str,
    target_section: str,
    source_metric: str = "cost_of_revenue",
    target_metric: str = "revenue",
    output_dir: str | Path = ROOT / "pair_analysis",
    output_name: str | None = None,
    start_quarter: str | None = None,
    min_obs: int = 4,
) -> dict[str, Path]:
    """Analyze one section pair and write CSV + HTML outputs.

    `df` can be either:
    - long rows with section, fs_item, date, value
    - section-quarter wide rows with section, quarter_period/date, and metric columns
    """
    if {"fs_item", "date", "value"} <= set(df.columns):
        section_quarterly = normalize_financial_long_dataframe(df, start_quarter=start_quarter)
    else:
        section_quarterly = df.copy()
        if "quarter_period" not in section_quarterly.columns:
            date_col = "date" if "date" in section_quarterly.columns else "calendar_quarter"
            section_quarterly["quarter_period"] = section_quarterly[date_col].map(parse_quarter)
        section_quarterly = section_quarterly.dropna(subset=["section", "quarter_period"])

    lag_df = compute_section_pair_lags(
        section_quarterly,
        source_section=source_section,
        target_section=target_section,
        source_metric=source_metric,
        target_metric=target_metric,
        lags=DEFAULT_LAGS,
        min_obs=min_obs,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = output_name or f"{source_section}_to_{target_section}_{source_metric}_to_{target_metric}"
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in safe_name).strip("_")
    csv_path = output_dir / f"{safe_name}_lag_table.csv"
    html_path = output_dir / f"{safe_name}_lead_lag.html"
    lag_df.to_csv(csv_path, index=False)
    html_path.write_text(build_pair_html(lag_df, output_title=safe_name), encoding="utf-8")
    return {"csv": csv_path, "html": html_path}


if __name__ == "__main__":
    sample_path = ROOT / "section_financial_quarterly_summary.csv"
    sample = pd.read_csv(sample_path)
    sample["quarter_period"] = sample["quarter_period"].map(parse_quarter)
    paths = analyze_section_pair(
        sample,
        source_section="Hyperscalers",
        target_section="AI Chip",
        source_metric="cost_of_revenue_usd_m",
        target_metric="revenue_usd_m",
        output_dir=ROOT / "pair_analysis",
        output_name="hyperscalers_cost_to_ai_chip_revenue",
        min_obs=4,
    )
    print(f"Wrote {paths['html']}")
