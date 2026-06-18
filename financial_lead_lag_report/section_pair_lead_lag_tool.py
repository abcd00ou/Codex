from __future__ import annotations

import html
import json
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
            source_variance = float(aligned["source"].var())
            target_variance = float(aligned["target"].var())
            if source_variance <= 0 or target_variance <= 0:
                corr = beta = np.nan
            else:
                corr = float(aligned["source"].corr(aligned["target"]))
                beta = float(aligned["source"].cov(aligned["target"]) / source_variance)
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


def compute_all_section_pair_lags(
    section_quarterly: pd.DataFrame,
    sections: list[str] | None = None,
    source_metric: str = "cost_of_revenue",
    target_metric: str = "revenue",
    lags: list[int] | None = None,
    min_obs: int = 4,
    include_self: bool = False,
) -> pd.DataFrame:
    """Compute lead-lag rows for every ordered section pair."""
    if sections is None:
        sections = sorted(section_quarterly["section"].dropna().astype(str).unique())
    else:
        sections = [str(section) for section in sections]

    rows = []
    for source_section in sections:
        for target_section in sections:
            if not include_self and source_section == target_section:
                continue
            lag_df = compute_section_pair_lags(
                section_quarterly,
                source_section=source_section,
                target_section=target_section,
                source_metric=source_metric,
                target_metric=target_metric,
                lags=lags,
                min_obs=min_obs,
            )
            rows.append(lag_df)

    if not rows:
        return pd.DataFrame(
            columns=[
                "source_section",
                "target_section",
                "source_metric",
                "target_metric",
                "lag_quarters",
                "timing",
                "observations",
                "corr",
                "r_squared",
                "beta_target_per_1_source",
            ]
        )
    return pd.concat(rows, ignore_index=True)


def best_summary_for_all_pairs(all_lags: pd.DataFrame) -> pd.DataFrame:
    """One best-lag summary row per source-target pair."""
    rows = []
    group_cols = ["source_section", "target_section", "source_metric", "target_metric"]
    for keys, lag_df in all_lags.groupby(group_cols, dropna=False):
        summary = best_lag_summary(lag_df)
        if not summary:
            continue
        row = dict(zip(group_cols, keys))
        row.update(summary)
        rows.append(row)
    if not rows:
        return pd.DataFrame(
            columns=group_cols
            + [
                "best_lag_quarters",
                "best_timing",
                "best_corr",
                "best_observations",
                "best_abs_lag_quarters",
                "best_abs_corr",
            ]
        )
    summary = pd.DataFrame(rows)
    summary["abs_best_corr"] = summary["best_corr"].abs()
    return summary.sort_values(["abs_best_corr", "best_observations"], ascending=[False, False]).reset_index(drop=True)


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


def prepare_dashboard_records(df: pd.DataFrame) -> list[dict[str, object]]:
    records = df.replace({np.nan: None}).to_dict(orient="records")
    for row in records:
        for key in ("lag_quarters", "observations", "best_lag_quarters", "best_observations", "best_abs_lag_quarters"):
            if key in row and row[key] is not None:
                row[key] = int(row[key])
        for key in ("corr", "r_squared", "beta_target_per_1_source", "best_corr", "best_abs_corr", "abs_best_corr"):
            if key in row and row[key] is not None:
                row[key] = float(row[key])
    return records


def build_all_pairs_dashboard_html(all_lags: pd.DataFrame, summary: pd.DataFrame, title: str) -> str:
    sections = sorted(
        set(all_lags["source_section"].dropna().astype(str)).union(all_lags["target_section"].dropna().astype(str))
    )
    lag_records_json = json.dumps(prepare_dashboard_records(all_lags), ensure_ascii=False)
    summary_records_json = json.dumps(prepare_dashboard_records(summary), ensure_ascii=False)
    sections_json = json.dumps(sections, ensure_ascii=False)
    first = all_lags.iloc[0] if not all_lags.empty else {}
    source_metric = first.get("source_metric", "source_metric") if hasattr(first, "get") else "source_metric"
    target_metric = first.get("target_metric", "target_metric") if hasattr(first, "get") else "target_metric"
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{
      --ink:#17211c; --muted:#5f6b64; --line:#d7ded8; --panel:#ffffff;
      --bg:#f7faf7; --soft:#edf5f0; --green:#087f5b; --red:#b03737; --blue:#2457a6;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:var(--bg); }}
    header {{ padding:26px 36px 18px; background:#e7f1eb; border-bottom:1px solid var(--line); }}
    main {{ padding:22px 36px 44px; max-width:1480px; }}
    h1 {{ margin:0 0 8px; font-size:26px; letter-spacing:0; }}
    h2 {{ margin:24px 0 10px; font-size:18px; }}
    p {{ line-height:1.55; }}
    .meta {{ color:var(--muted); font-size:13px; }}
    .controls {{ display:grid; grid-template-columns:1fr 1fr auto; gap:12px; align-items:end; margin:18px 0; }}
    label {{ display:block; color:var(--muted); font-size:12px; font-weight:700; margin-bottom:5px; }}
    select, button {{ width:100%; border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:7px; padding:10px 11px; font-size:14px; }}
    button {{ width:auto; cursor:pointer; font-weight:700; background:#f9fbfa; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:10px 0 18px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px 14px; min-height:82px; }}
    .card .k {{ color:var(--muted); font-size:12px; font-weight:700; }}
    .card .v {{ font-size:22px; font-weight:760; margin-top:7px; }}
    .card .s {{ color:var(--muted); font-size:12px; margin-top:5px; }}
    .grid {{ display:grid; grid-template-columns:minmax(0,1.35fr) minmax(420px,0.65fr); gap:16px; align-items:start; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; overflow:hidden; }}
    .chart-wrap {{ overflow-x:auto; }}
    svg {{ width:100%; min-width:980px; height:auto; display:block; background:#fff; }}
    table {{ border-collapse:collapse; width:100%; background:#fff; font-size:13px; }}
    th, td {{ padding:8px 9px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{ text-align:left; }}
    thead th {{ position:sticky; top:0; background:#eef4f0; z-index:1; }}
    tbody tr.clickable {{ cursor:pointer; }}
    tbody tr.clickable:hover {{ background:#f2f7f4; }}
    .scroll {{ max-height:520px; overflow:auto; border:1px solid var(--line); border-radius:8px; }}
    .note {{ background:#fff9e8; border:1px solid #ead28a; padding:12px 14px; border-radius:8px; }}
    .legend {{ display:flex; gap:14px; flex-wrap:wrap; color:var(--muted); font-size:12px; margin:7px 0 0; }}
    .dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:5px; vertical-align:-1px; }}
    .empty {{ color:var(--muted); padding:20px; text-align:center; }}
    code {{ background:#edf2ee; padding:2px 4px; border-radius:4px; }}
    @media (max-width: 980px) {{
      main, header {{ padding-left:18px; padding-right:18px; }}
      .controls, .grid, .cards {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>
<header>
  <h1>{esc(title)}</h1>
  <div class="meta">All ordered section pairs · Lag range -8Q to +8Q · Transform: <code>(x_t - x_(t-4)) / x_t</code></div>
</header>
<main>
  <p class="note">해석 기준: positive lag는 source section의 <b>{esc(source_metric)}</b> 변화가 target section의 <b>{esc(target_metric)}</b> 변화보다 n분기 먼저 관측된다는 뜻입니다. negative lag는 target이 먼저 움직인 경우이고, 0Q는 동행입니다.</p>
  <div class="controls">
    <div>
      <label for="sourceSelect">Source section</label>
      <select id="sourceSelect"></select>
    </div>
    <div>
      <label for="targetSelect">Target section</label>
      <select id="targetSelect"></select>
    </div>
    <button id="swapBtn" type="button">Swap</button>
  </div>
  <div class="cards" id="summaryCards"></div>
  <div class="grid">
    <section class="panel">
      <h2>Lag Profile</h2>
      <div class="legend">
        <span><i class="dot" style="background:var(--green)"></i>Positive correlation</span>
        <span><i class="dot" style="background:var(--red)"></i>Negative correlation</span>
        <span><i class="dot" style="background:#c8d0ca"></i>Not enough observations</span>
      </div>
      <div class="chart-wrap" id="chart"></div>
    </section>
    <section class="panel">
      <h2>Lag Table</h2>
      <div class="scroll" id="lagTable"></div>
    </section>
  </div>
  <section class="panel" style="margin-top:16px;">
    <h2>Strongest Pair Ranking</h2>
    <div class="scroll" id="rankingTable"></div>
  </section>
</main>
<script>
const SECTIONS = {sections_json};
const LAG_DATA = {lag_records_json};
const SUMMARY_DATA = {summary_records_json};
const LAGS = Array.from(new Set(LAG_DATA.map(d => d.lag_quarters))).sort((a,b) => a-b);

const sourceSelect = document.getElementById("sourceSelect");
const targetSelect = document.getElementById("targetSelect");
const chart = document.getElementById("chart");
const lagTable = document.getElementById("lagTable");
const rankingTable = document.getElementById("rankingTable");
const summaryCards = document.getElementById("summaryCards");

function fmt(value, digits=3) {{
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return Number(value).toLocaleString(undefined, {{maximumFractionDigits: digits, minimumFractionDigits: digits}});
}}
function fmtLag(value) {{ return value > 0 ? `+${{value}}Q` : `${{value}}Q`; }}
function timingText(lag) {{
  if (lag > 0) return "source leads";
  if (lag < 0) return "target leads";
  return "same quarter";
}}
function optionHtml(value) {{ return `<option value="${{String(value).replaceAll('"', '&quot;')}}">${{value}}</option>`; }}
function pairRows() {{
  return LAG_DATA.filter(d => d.source_section === sourceSelect.value && d.target_section === targetSelect.value)
    .sort((a,b) => a.lag_quarters - b.lag_quarters);
}}
function pairSummary() {{
  return SUMMARY_DATA.find(d => d.source_section === sourceSelect.value && d.target_section === targetSelect.value);
}}
function renderCards(summary, rows) {{
  const best = summary || {{}};
  const valid = rows.filter(d => d.corr !== null && d.corr !== undefined);
  const maxObs = valid.length ? Math.max(...valid.map(d => d.observations || 0)) : 0;
  summaryCards.innerHTML = [
    ["Best lag", best.best_lag_quarters !== undefined ? fmtLag(best.best_lag_quarters) : "-", best.best_timing || "insufficient data"],
    ["Correlation", fmt(best.best_corr), `n=${{best.best_observations || maxObs || "-"}}`],
    ["Strongest absolute", best.best_abs_lag_quarters !== undefined ? fmtLag(best.best_abs_lag_quarters) : "-", `corr=${{fmt(best.best_abs_corr)}}`],
    ["Direction", sourceSelect.value + " -> " + targetSelect.value, "{esc(source_metric)} to {esc(target_metric)}"],
  ].map(([k,v,s]) => `<div class="card"><div class="k">${{k}}</div><div class="v">${{v}}</div><div class="s">${{s}}</div></div>`).join("");
}}
function renderChart(rows) {{
  if (!rows.length) {{
    chart.innerHTML = '<div class="empty">No pair data.</div>';
    return;
  }}
  const width = 1120, height = 360, left = 70, right = 30, top = 34, bottom = 62;
  const chartW = width - left - right;
  const zeroY = top + (height - top - bottom) / 2;
  const step = chartW / LAGS.length;
  const byLag = new Map(rows.map(d => [d.lag_quarters, d]));
  let parts = [`<svg viewBox="0 0 ${{width}} ${{height}}" role="img" aria-label="lead lag chart">`];
  parts.push(`<line x1="${{left}}" x2="${{width-right}}" y1="${{zeroY}}" y2="${{zeroY}}" stroke="#aab5ae"/>`);
  parts.push(`<text x="12" y="${{zeroY-5}}" fill="#5f6b64" font-size="12">corr 0</text>`);
  LAGS.forEach((lag, i) => {{
    const row = byLag.get(lag);
    const x = left + i * step + 4;
    const mid = x + step / 2;
    parts.push(`<line x1="${{mid}}" x2="${{mid}}" y1="${{top}}" y2="${{height-bottom}}" stroke="#e0e6e2"/>`);
    if (!row || row.corr === null || row.corr === undefined) {{
      parts.push(`<rect x="${{x}}" y="${{zeroY-2}}" width="${{Math.max(5, step-8)}}" height="4" fill="#c8d0ca"/>`);
    }} else {{
      const barH = Math.min((height - top - bottom) / 2 - 12, Math.abs(row.corr) * 124);
      const y = row.corr >= 0 ? zeroY - barH : zeroY;
      const color = row.corr >= 0 ? "#087f5b" : "#b03737";
      parts.push(`<rect x="${{x}}" y="${{y}}" width="${{Math.max(5, step-8)}}" height="${{barH}}" fill="${{color}}" opacity="0.86"><title>${{fmtLag(lag)}} corr=${{fmt(row.corr)}} n=${{row.observations}}</title></rect>`);
      parts.push(`<text x="${{mid}}" y="${{row.corr >= 0 ? y - 5 : y + barH + 14}}" text-anchor="middle" fill="#17211c" font-size="10">${{fmt(row.corr,2)}}</text>`);
    }}
    parts.push(`<text x="${{mid}}" y="${{height-28}}" text-anchor="middle" fill="#5f6b64" font-size="11">${{fmtLag(lag)}}</text>`);
  }});
  parts.push(`<text x="${{left}}" y="20" fill="#17211c" font-size="14" font-weight="700">${{sourceSelect.value}} cost flow vs ${{targetSelect.value}} revenue response</text>`);
  parts.push(`</svg>`);
  chart.innerHTML = parts.join("");
}}
function renderLagTable(rows) {{
  if (!rows.length) {{
    lagTable.innerHTML = '<div class="empty">No pair data.</div>';
    return;
  }}
  lagTable.innerHTML = `<table><thead><tr><th>Lag</th><th>Timing</th><th>Obs</th><th>Corr</th><th>R2</th><th>Beta</th></tr></thead><tbody>` +
    rows.map(r => `<tr><td>${{fmtLag(r.lag_quarters)}}</td><td>${{timingText(r.lag_quarters)}}</td><td>${{r.observations}}</td><td>${{fmt(r.corr)}}</td><td>${{fmt(r.r_squared)}}</td><td>${{fmt(r.beta_target_per_1_source)}}</td></tr>`).join("") +
    `</tbody></table>`;
}}
function renderRanking() {{
  const top = SUMMARY_DATA.slice(0, 80);
  rankingTable.innerHTML = `<table><thead><tr><th>Source</th><th>Target</th><th>Best lag</th><th>Timing</th><th>Corr</th><th>Obs</th><th>Abs lag</th><th>Abs corr</th></tr></thead><tbody>` +
    top.map(r => `<tr class="clickable" data-source="${{r.source_section}}" data-target="${{r.target_section}}"><td>${{r.source_section}}</td><td>${{r.target_section}}</td><td>${{fmtLag(r.best_lag_quarters)}}</td><td>${{r.best_timing}}</td><td>${{fmt(r.best_corr)}}</td><td>${{r.best_observations}}</td><td>${{fmtLag(r.best_abs_lag_quarters)}}</td><td>${{fmt(r.best_abs_corr)}}</td></tr>`).join("") +
    `</tbody></table>`;
  rankingTable.querySelectorAll("tr.clickable").forEach(row => {{
    row.addEventListener("click", () => {{
      sourceSelect.value = row.dataset.source;
      targetSelect.value = row.dataset.target;
      renderSelected();
      window.scrollTo({{top:0, behavior:"smooth"}});
    }});
  }});
}}
function renderSelected() {{
  const rows = pairRows();
  renderCards(pairSummary(), rows);
  renderChart(rows);
  renderLagTable(rows);
}}
function init() {{
  sourceSelect.innerHTML = SECTIONS.map(optionHtml).join("");
  targetSelect.innerHTML = SECTIONS.map(optionHtml).join("");
  const preferred = SUMMARY_DATA.find(d => d.source_section === "Hyperscalers" && d.target_section === "AI Chip") || SUMMARY_DATA[0];
  sourceSelect.value = preferred ? preferred.source_section : SECTIONS[0];
  targetSelect.value = preferred ? preferred.target_section : SECTIONS.find(s => s !== sourceSelect.value) || SECTIONS[0];
  sourceSelect.addEventListener("change", renderSelected);
  targetSelect.addEventListener("change", renderSelected);
  document.getElementById("swapBtn").addEventListener("click", () => {{
    const source = sourceSelect.value;
    sourceSelect.value = targetSelect.value;
    targetSelect.value = source;
    renderSelected();
  }});
  renderSelected();
  renderRanking();
}}
init();
</script>
</body>
</html>
"""


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


def prepare_section_quarterly(
    df: pd.DataFrame,
    start_quarter: str | None = None,
) -> pd.DataFrame:
    """Accept long or section-quarter wide data and return normalized quarter rows."""
    if {"fs_item", "date", "value"} <= set(df.columns):
        return normalize_financial_long_dataframe(df, start_quarter=start_quarter)

    section_quarterly = df.copy()
    if "quarter_period" not in section_quarterly.columns:
        date_col = "date" if "date" in section_quarterly.columns else "calendar_quarter"
        section_quarterly["quarter_period"] = section_quarterly[date_col].map(parse_quarter)
    else:
        section_quarterly["quarter_period"] = section_quarterly["quarter_period"].map(parse_quarter)
    section_quarterly = section_quarterly.dropna(subset=["section", "quarter_period"])
    if start_quarter:
        section_quarterly = section_quarterly[section_quarterly["quarter_period"] >= parse_quarter(start_quarter)]
    return section_quarterly


def analyze_all_section_pairs(
    df: pd.DataFrame,
    source_metric: str = "cost_of_revenue",
    target_metric: str = "revenue",
    output_dir: str | Path = ROOT / "pair_analysis",
    output_name: str = "all_section_pair",
    start_quarter: str | None = None,
    min_obs: int = 4,
    include_self: bool = False,
) -> dict[str, Path]:
    """Analyze every ordered section pair and write dashboard + backing CSVs.

    `df` can be either:
    - long rows with section, fs_item, date, value
    - section-quarter wide rows with section, quarter_period/date, and metric columns
    """
    section_quarterly = prepare_section_quarterly(df, start_quarter=start_quarter)
    all_lags = compute_all_section_pair_lags(
        section_quarterly,
        source_metric=source_metric,
        target_metric=target_metric,
        lags=DEFAULT_LAGS,
        min_obs=min_obs,
        include_self=include_self,
    )
    summary = best_summary_for_all_pairs(all_lags)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in output_name).strip("_")
    lag_csv_path = output_dir / f"{safe_name}_lag_table.csv"
    summary_csv_path = output_dir / f"{safe_name}_best_summary.csv"
    html_path = output_dir / f"{safe_name}_lead_lag_dashboard.html"
    all_lags.to_csv(lag_csv_path, index=False)
    summary.to_csv(summary_csv_path, index=False)
    html_path.write_text(
        build_all_pairs_dashboard_html(all_lags, summary, title="All Section Pair Lead-Lag Dashboard"),
        encoding="utf-8",
    )
    return {"lag_csv": lag_csv_path, "summary_csv": summary_csv_path, "html": html_path}


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
    dashboard_paths = analyze_all_section_pairs(
        sample,
        source_metric="cost_of_revenue_usd_m",
        target_metric="revenue_usd_m",
        output_dir=ROOT / "pair_analysis",
        output_name="all_section_pair",
        min_obs=4,
    )
    print(f"Wrote {dashboard_paths['html']}")
