from __future__ import annotations

import hashlib
import html
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "ai_chip_sales"
OUTPUT_PATH = DATA_DIR / "epoch_ai_chip_sales_analysis_report.html"


METRICS = {
    "units": "Number of Units",
    "h100e": "Compute estimate in H100e (median)",
    "tdp_w": "Total TDP (W)",
    "cost": "Cost Estimate (USD)",
}


@dataclass(frozen=True)
class SourceFile:
    name: str
    path: Path
    rows: int
    cols: int
    sha256: str


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_inventory() -> list[SourceFile]:
    rows = []
    for path in sorted(DATA_DIR.glob("*.csv")):
        df = pd.read_csv(path, nrows=5)
        row_count = sum(1 for _ in path.open("rb")) - 1
        rows.append(
            SourceFile(
                name=path.name,
                path=path,
                rows=max(row_count, 0),
                cols=len(df.columns),
                sha256=file_sha256(path)[:16],
            )
        )
    return rows


def clean_timelines(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Start date"] = pd.to_datetime(out["Start date"])
    out["End date"] = pd.to_datetime(out["End date"])
    out["quarter"] = out["Start date"].dt.to_period("Q").astype(str)
    out["Incomplete"] = out["Incomplete"].fillna("").astype(str).str.lower().isin(["true", "1", "yes"])
    for col in METRICS.values():
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out["power_mw"] = out[METRICS["tdp_w"]] / 1_000_000
    out["cost_b_usd"] = out[METRICS["cost"]] / 1_000_000_000
    return out


def fmt_num(value: float, digits: int = 0) -> str:
    if pd.isna(value):
        return "-"
    abs_value = abs(float(value))
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.{digits}f}B"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.{digits}f}M"
    if abs_value >= 1_000:
        return f"{value / 1_000:.{digits}f}K"
    return f"{value:.{digits}f}"


def fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def esc(value: object) -> str:
    return html.escape("" if pd.isna(value) else str(value))


def table_html(df: pd.DataFrame, max_rows: int | None = None, classes: str = "") -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    header = "".join(f"<th>{esc(col)}</th>" for col in df.columns)
    body = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{esc(row[col])}</td>" for col in df.columns)
        body.append(f"<tr>{cells}</tr>")
    return f'<table class="{classes}"><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def bar_svg(labels: list[str], values: list[float], title: str, width: int = 920, height: int = 300) -> str:
    if not values or max(values) <= 0:
        return ""
    margin_left, margin_right, margin_top, margin_bottom = 70, 28, 34, 68
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    max_v = max(values)
    n = len(values)
    gap = 12
    bar_w = max(16, (chart_w - gap * (n - 1)) / max(n, 1))
    palette = ["#2b6cb0", "#319795", "#dd6b20", "#805ad5", "#d53f8c", "#718096"]
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{margin_left}" y="22" class="chart-title">{esc(title)}</text>',
        f'<line x1="{margin_left}" y1="{margin_top + chart_h}" x2="{width - margin_right}" y2="{margin_top + chart_h}" class="axis"/>',
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        x = margin_left + i * (bar_w + gap)
        h = chart_h * value / max_v
        y = margin_top + chart_h - h
        color = palette[i % len(palette)]
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{color}" rx="3"/>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" class="bar-label">{fmt_num(value, 1)}</text>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{margin_top + chart_h + 18}" text-anchor="middle" class="x-label">{esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def line_svg(df: pd.DataFrame, title: str, value_col: str, width: int = 920, height: int = 340) -> str:
    pivot = df.pivot_table(index="quarter", columns="Chip manufacturer", values=value_col, aggfunc="sum").fillna(0)
    if pivot.empty:
        return ""
    quarters = list(pivot.index)
    designers = list(pivot.columns)
    max_v = pivot.to_numpy().max()
    if max_v <= 0:
        return ""
    margin_left, margin_right, margin_top, margin_bottom = 74, 160, 36, 62
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    palette = ["#2b6cb0", "#319795", "#dd6b20", "#805ad5", "#d53f8c", "#718096"]
    x_step = chart_w / max(len(quarters) - 1, 1)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{margin_left}" y="22" class="chart-title">{esc(title)}</text>',
        f'<line x1="{margin_left}" y1="{margin_top + chart_h}" x2="{margin_left + chart_w}" y2="{margin_top + chart_h}" class="axis"/>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_h}" class="axis"/>',
    ]
    for i, q in enumerate(quarters):
        if i % max(1, len(quarters) // 8) == 0 or i == len(quarters) - 1:
            x = margin_left + i * x_step
            parts.append(f'<text x="{x:.1f}" y="{margin_top + chart_h + 20}" text-anchor="middle" class="x-label">{esc(q)}</text>')
    for idx, designer in enumerate(designers):
        points = []
        for i, q in enumerate(quarters):
            value = pivot.loc[q, designer]
            x = margin_left + i * x_step
            y = margin_top + chart_h - chart_h * value / max_v
            points.append(f"{x:.1f},{y:.1f}")
        color = palette[idx % len(palette)]
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        lx = margin_left + chart_w + 18
        ly = margin_top + 18 + idx * 22
        parts.append(f'<rect x="{lx}" y="{ly - 10}" width="11" height="11" fill="{color}" rx="2"/>')
        parts.append(f'<text x="{lx + 18}" y="{ly}" class="legend">{esc(designer)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def category_line_svg(
    df: pd.DataFrame,
    title: str,
    category_col: str,
    value_col: str,
    width: int = 920,
    height: int = 340,
) -> str:
    pivot = df.pivot_table(index="quarter", columns=category_col, values=value_col, aggfunc="sum").fillna(0)
    if pivot.empty:
        return ""
    pivot = pivot.loc[:, pivot.sum().sort_values(ascending=False).index[:8]]
    quarters = list(pivot.index)
    categories = list(pivot.columns)
    max_v = pivot.to_numpy().max()
    if max_v <= 0:
        return ""
    margin_left, margin_right, margin_top, margin_bottom = 74, 172, 36, 62
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom
    palette = ["#2b6cb0", "#319795", "#dd6b20", "#805ad5", "#d53f8c", "#718096", "#0f766e", "#9a3412"]
    x_step = chart_w / max(len(quarters) - 1, 1)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        f'<text x="{margin_left}" y="22" class="chart-title">{esc(title)}</text>',
        f'<line x1="{margin_left}" y1="{margin_top + chart_h}" x2="{margin_left + chart_w}" y2="{margin_top + chart_h}" class="axis"/>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + chart_h}" class="axis"/>',
    ]
    for i, q in enumerate(quarters):
        if i % max(1, len(quarters) // 6) == 0 or i == len(quarters) - 1:
            x = margin_left + i * x_step
            parts.append(f'<text x="{x:.1f}" y="{margin_top + chart_h + 20}" text-anchor="middle" class="x-label">{esc(q)}</text>')
    for idx, category in enumerate(categories):
        points = []
        for i, q in enumerate(quarters):
            value = pivot.loc[q, category]
            x = margin_left + i * x_step
            y = margin_top + chart_h - chart_h * value / max_v
            points.append(f"{x:.1f},{y:.1f}")
        color = palette[idx % len(palette)]
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        lx = margin_left + chart_w + 18
        ly = margin_top + 18 + idx * 22
        parts.append(f'<rect x="{lx}" y="{ly - 10}" width="11" height="11" fill="{color}" rx="2"/>')
        parts.append(f'<text x="{lx + 18}" y="{ly}" class="legend">{esc(category)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def company_readout(
    maker: str,
    group: pd.DataFrame,
    chip_group: pd.DataFrame,
    total_h100e: float,
    total_units: float,
    organizations: pd.DataFrame,
) -> dict[str, object]:
    q = group.groupby("quarter", as_index=False).agg(
        units=(METRICS["units"], "sum"),
        h100e=(METRICS["h100e"], "sum"),
        cost_usd=(METRICS["cost"], "sum"),
        power_mw=("power_mw", "sum"),
        incomplete=("Incomplete", "sum"),
    )
    q = q.sort_values("quarter")
    latest = q.iloc[-1]
    first = q[q["h100e"] > 0].iloc[0]
    peak = q.loc[q["h100e"].idxmax()]
    prev = q.iloc[-2] if len(q) > 1 else latest
    top_chip = chip_group.sort_values("h100e", ascending=False).iloc[0]
    country = ""
    org_match = organizations[organizations["Name"].astype(str).str.lower() == maker.lower()]
    if not org_match.empty:
        country = str(org_match.iloc[0].get("Country", ""))
    latest_delta = (latest["h100e"] / prev["h100e"] - 1) if prev["h100e"] else 0
    growth_multiple = latest["h100e"] / first["h100e"] if first["h100e"] else 0
    return {
        "maker": maker,
        "country": country,
        "first_quarter": first["quarter"],
        "latest_quarter": latest["quarter"],
        "peak_quarter": peak["quarter"],
        "latest_h100e": latest["h100e"],
        "peak_h100e": peak["h100e"],
        "latest_delta": latest_delta,
        "growth_multiple": growth_multiple,
        "total_units": group[METRICS["units"]].sum(),
        "total_h100e": group[METRICS["h100e"]].sum(),
        "total_cost": group[METRICS["cost"]].sum(),
        "total_power_mw": group["power_mw"].sum(),
        "h100e_share": group[METRICS["h100e"]].sum() / total_h100e if total_h100e else 0,
        "unit_share": group[METRICS["units"]].sum() / total_units if total_units else 0,
        "top_chip": top_chip["Chip type"],
        "top_chip_share": top_chip["h100e"] / chip_group["h100e"].sum() if chip_group["h100e"].sum() else 0,
        "records": len(group),
        "incomplete_records": int(group["Incomplete"].sum()),
        "chip_count": group["Chip type"].nunique(),
    }


def company_narrative(maker: str, readout: dict[str, object], product_df: pd.DataFrame) -> list[str]:
    top_products = product_df.sort_values("h100e", ascending=False).head(3)
    product_phrase = ", ".join(
        f"{row['Chip type']} ({fmt_pct(row['designer_h100e_share'])})"
        for _, row in top_products.iterrows()
    )
    base = [
        f"누적 H100e share는 {fmt_pct(float(readout['h100e_share']))}이고, unit share는 {fmt_pct(float(readout['unit_share']))}다. compute 기준으로는 {readout['top_chip']}가 회사 내 핵심 제품이며 제품 비중은 {fmt_pct(float(readout['top_chip_share']))}다.",
        f"판매/출하 추정치는 {readout['first_quarter']}부터 {readout['latest_quarter']}까지 이어지며, 최신 분기 H100e는 {fmt_num(float(readout['latest_h100e']), 1)}다. 첫 유의미 분기 대비 최신 분기 배율은 {float(readout['growth_multiple']):.1f}x다.",
        f"제품 포트폴리오 상위 라인은 {product_phrase} 순서다.",
    ]
    specific = {
        "Nvidia": [
            "Hopper(H100/H200)에서 Blackwell(B200/B300)로 무게중심이 이동한다. 누적 H100e에서는 B300과 B200이 가장 큰 축이고, H100/H200은 2023-2025 ramp의 핵심 기반으로 남아 있다.",
            "A800/H800/H20은 중국향·수출규제 관련 변형 제품으로 별도 집계되어 있어, Nvidia 내 제품 믹스 해석에서 mainstream accelerator와 구분해서 읽어야 한다.",
        ],
        "Google": [
            "TPU v6e가 누적 compute의 중심이고 TPU v7이 빠르게 붙으면서 2025Q4 peak 이후 2026Q1에도 높은 stock addition을 유지한다.",
            "Google TPU 수치는 공개 chip sales라기보다 Broadcom revenue와 TPU spending model에 근거한 추정이라는 점이 중요하다.",
        ],
        "AMD": [
            "MI300X가 누적 주력 제품이지만, 2025년 말에는 MI350X/MI355X/MI325X가 함께 올라오며 제품 세대 전환이 보인다.",
            "AMD는 Nvidia 대비 절대 H100e 규모는 작지만, 2024Q1 이후 최신 분기까지 증가세가 뚜렷한 challenger profile이다.",
        ],
        "Amazon": [
            "Trainium2가 Amazon 누적 H100e의 대부분을 차지한다. Trainium1은 초기 기반, Trainium2는 2025년 ramp의 중심으로 읽힌다.",
            "Epoch 문서상 Amazon은 대규모 Trainium data center와 analyst estimate 의존도가 높아, 외부 판매량이라기보다 internal deployment floor에 가까운 해석이 필요하다.",
        ],
        "Huawei": [
            "Ascend 910C가 Ascend 910B를 넘어 누적 compute의 중심으로 잡힌다. 2025년 내내 비교적 일정한 분기 H100e가 반복되는 구조다.",
            "Huawei 수치는 third-party analyst volume synthesis 성격이 강해 shipment/production/delivery 구분의 불확실성이 크다.",
        ],
        "Cambricon": [
            "Siyuan 590 단일 제품 중심의 작은 규모 포지션이다. 전체 H100e share는 낮지만 중국 내 dedicated accelerator coverage를 보완하는 항목으로 의미가 있다.",
            "Cambricon은 2025 annual report disclosure와 analyst/media corroboration에 기반한 revenue/volume model로 읽어야 한다.",
        ],
    }
    return base + specific.get(maker, [])


def build_report() -> str:
    timelines = clean_timelines(read_csv("timelines_by_chip.csv"))
    chip_types = read_csv("chip_types.csv")
    organizations = read_csv("organizations.csv")
    cumulative = read_csv("cumulative_timelines.csv")
    cumulative_by_designer = read_csv("cumulative_timelines_by_designer.csv")
    inventory = source_inventory()

    total_units = timelines[METRICS["units"]].sum()
    total_h100e = timelines[METRICS["h100e"]].sum()
    total_cost = timelines[METRICS["cost"]].sum()
    total_power_mw = timelines["power_mw"].sum()
    first_q = timelines["quarter"].min()
    last_q = timelines["quarter"].max()

    by_designer = (
        timelines.groupby("Chip manufacturer", as_index=False)
        .agg(
            units=(METRICS["units"], "sum"),
            h100e=(METRICS["h100e"], "sum"),
            cost_usd=(METRICS["cost"], "sum"),
            power_mw=("power_mw", "sum"),
            records=("Name", "count"),
            incomplete_records=("Incomplete", "sum"),
        )
        .sort_values("h100e", ascending=False)
    )
    by_designer["h100e_share"] = by_designer["h100e"] / total_h100e
    by_designer["unit_share"] = by_designer["units"] / total_units

    by_chip = (
        timelines.groupby(["Chip manufacturer", "Chip type"], as_index=False)
        .agg(
            units=(METRICS["units"], "sum"),
            h100e=(METRICS["h100e"], "sum"),
            cost_usd=(METRICS["cost"], "sum"),
            power_mw=("power_mw", "sum"),
            first_quarter=("quarter", "min"),
            last_quarter=("quarter", "max"),
            records=("Name", "count"),
        )
        .sort_values(["Chip manufacturer", "h100e"], ascending=[True, False])
    )
    by_chip["designer_h100e_share"] = by_chip["h100e"] / by_chip.groupby("Chip manufacturer")["h100e"].transform("sum")

    quarterly = (
        timelines.groupby(["quarter", "Chip manufacturer", "Chip type"], as_index=False)
        .agg(
            units=(METRICS["units"], "sum"),
            h100e=(METRICS["h100e"], "sum"),
            cost_usd=(METRICS["cost"], "sum"),
            power_mw=("power_mw", "sum"),
            incomplete=("Incomplete", "max"),
        )
        .sort_values(["quarter", "Chip manufacturer", "h100e"], ascending=[True, True, False])
    )

    latest_quarter = quarterly["quarter"].max()
    latest = quarterly[quarterly["quarter"] == latest_quarter].copy()
    latest_summary = (
        latest.groupby("Chip manufacturer", as_index=False)
        .agg(units=("units", "sum"), h100e=("h100e", "sum"), cost_usd=("cost_usd", "sum"), power_mw=("power_mw", "sum"))
        .sort_values("h100e", ascending=False)
    )

    peak_rows = []
    for (designer, chip), group in quarterly.groupby(["Chip manufacturer", "Chip type"]):
        peak = group.loc[group["h100e"].idxmax()]
        peak_rows.append(
            {
                "Chip manufacturer": designer,
                "Chip type": chip,
                "Peak quarter": peak["quarter"],
                "Peak H100e": peak["h100e"],
                "Peak units": peak["units"],
                "Peak cost USD": peak["cost_usd"],
            }
        )
    peak_df = pd.DataFrame(peak_rows).sort_values(["Chip manufacturer", "Peak H100e"], ascending=[True, False])

    main_products = (
        by_chip.sort_values(["Chip manufacturer", "h100e"], ascending=[True, False])
        .groupby("Chip manufacturer", as_index=False)
        .head(3)
    )

    chip_enriched = chip_types.copy()
    for col in ["H100e", "TDP (W) (from ML Hardware (linked))", "Memory", "Memory bandwidth", "Cost per chip (approx.)"]:
        chip_enriched[col] = pd.to_numeric(chip_enriched[col], errors="coerce")
    spec_table = chip_enriched[
        ["Name", "Designer", "H100e", "TDP (W) (from ML Hardware (linked))", "Memory", "Memory bandwidth", "Cost per chip (approx.)", "Primarily for Chinese market"]
    ].copy()
    spec_table["Memory GB"] = spec_table["Memory"] / 1_000_000_000
    spec_table["Bandwidth TB/s"] = spec_table["Memory bandwidth"] / 1_000_000_000_000
    spec_table = spec_table.drop(columns=["Memory", "Memory bandwidth"]).sort_values(["Designer", "H100e"], ascending=[True, False])

    def display_designer(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["Units"] = out["units"].map(lambda x: fmt_num(x, 1))
        out["H100e"] = out["h100e"].map(lambda x: fmt_num(x, 1))
        out["Cost"] = out["cost_usd"].map(lambda x: "$" + fmt_num(x, 1))
        out["Chip TDP power"] = out["power_mw"].map(lambda x: fmt_num(x, 1) + " MW")
        out["H100e share"] = out["h100e_share"].map(fmt_pct)
        out["Unit share"] = out["unit_share"].map(fmt_pct)
        return out[["Chip manufacturer", "Units", "H100e", "Cost", "Chip TDP power", "H100e share", "Unit share", "records", "incomplete_records"]]

    def display_chip(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["Units"] = out["units"].map(lambda x: fmt_num(x, 1))
        out["H100e"] = out["h100e"].map(lambda x: fmt_num(x, 1))
        out["Cost"] = out["cost_usd"].map(lambda x: "$" + fmt_num(x, 1))
        out["Power"] = out["power_mw"].map(lambda x: fmt_num(x, 1) + " MW")
        out["Designer share"] = out["designer_h100e_share"].map(fmt_pct)
        return out[["Chip manufacturer", "Chip type", "Units", "H100e", "Cost", "Power", "Designer share", "first_quarter", "last_quarter", "records"]]

    def display_quarterly(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["Units"] = out["units"].map(lambda x: fmt_num(x, 1))
        out["H100e"] = out["h100e"].map(lambda x: fmt_num(x, 1))
        out["Cost"] = out["cost_usd"].map(lambda x: "$" + fmt_num(x, 1))
        out["Power"] = out["power_mw"].map(lambda x: fmt_num(x, 1) + " MW")
        out["Incomplete"] = out["incomplete"].map(lambda x: "Y" if x else "")
        return out[["quarter", "Chip manufacturer", "Chip type", "Units", "H100e", "Cost", "Power", "Incomplete"]]

    def display_peak(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["Peak H100e"] = out["Peak H100e"].map(lambda x: fmt_num(x, 1))
        out["Peak units"] = out["Peak units"].map(lambda x: fmt_num(x, 1))
        out["Peak cost USD"] = out["Peak cost USD"].map(lambda x: "$" + fmt_num(x, 1))
        return out

    def display_specs(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["H100e"] = out["H100e"].map(lambda x: "-" if pd.isna(x) else f"{x:.2f}")
        out["Memory GB"] = out["Memory GB"].map(lambda x: "-" if pd.isna(x) else f"{x:.0f}")
        out["Bandwidth TB/s"] = out["Bandwidth TB/s"].map(lambda x: "-" if pd.isna(x) else f"{x:.2f}")
        out["Cost per chip (approx.)"] = out["Cost per chip (approx.)"].map(lambda x: "-" if pd.isna(x) else "$" + fmt_num(x, 1))
        out["China-market flag"] = out["Primarily for Chinese market"].fillna("").map(lambda x: "Y" if str(x).strip().lower() in ["true", "1", "yes"] else "")
        return out.drop(columns=["Primarily for Chinese market"])

    def display_company_products(df: pd.DataFrame) -> pd.DataFrame:
        out = df.sort_values("h100e", ascending=False).copy()
        out["Units"] = out["units"].map(lambda x: fmt_num(x, 1))
        out["H100e"] = out["h100e"].map(lambda x: fmt_num(x, 1))
        out["Cost"] = out["cost_usd"].map(lambda x: "$" + fmt_num(x, 1))
        out["Power"] = out["power_mw"].map(lambda x: fmt_num(x, 1) + " MW")
        out["H100e share"] = out["designer_h100e_share"].map(fmt_pct)
        return out[["Chip type", "Units", "H100e", "H100e share", "Cost", "Power", "first_quarter", "last_quarter", "records"]]

    def display_company_quarters(df: pd.DataFrame) -> pd.DataFrame:
        out = (
            df.groupby(["quarter", "Chip type"], as_index=False)
            .agg(
                units=("units", "sum"),
                h100e=("h100e", "sum"),
                cost_usd=("cost_usd", "sum"),
                power_mw=("power_mw", "sum"),
                incomplete=("incomplete", "max"),
            )
            .sort_values(["quarter", "h100e"], ascending=[False, False])
        )
        out["Units"] = out["units"].map(lambda x: fmt_num(x, 1))
        out["H100e"] = out["h100e"].map(lambda x: fmt_num(x, 1))
        out["Cost"] = out["cost_usd"].map(lambda x: "$" + fmt_num(x, 1))
        out["Power"] = out["power_mw"].map(lambda x: fmt_num(x, 1) + " MW")
        out["Incomplete"] = out["incomplete"].map(lambda x: "Y" if x else "")
        return out[["quarter", "Chip type", "Units", "H100e", "Cost", "Power", "Incomplete"]]

    company_sections = []
    for maker in by_designer["Chip manufacturer"]:
        maker_rows = timelines[timelines["Chip manufacturer"] == maker].copy()
        maker_quarterly = quarterly[quarterly["Chip manufacturer"] == maker].copy()
        maker_products = by_chip[by_chip["Chip manufacturer"] == maker].copy()
        readout = company_readout(maker, maker_rows, maker_products, total_h100e, total_units, organizations)
        narrative = company_narrative(maker, readout, maker_products)
        product_labels = maker_products.sort_values("h100e", ascending=False)["Chip type"].tolist()
        product_h100e = maker_products.sort_values("h100e", ascending=False)["h100e"].tolist()
        latest_direction = "증가" if float(readout["latest_delta"]) >= 0 else "감소"
        section = f"""
    <section class="section company-section" id="company-{esc(maker).lower()}">
      <h2>{esc(maker)} 기업별 분석</h2>
      <p class="small">Headquarters: {esc(readout["country"])} · coverage: {esc(readout["first_quarter"])} to {esc(readout["latest_quarter"])} · products: {readout["chip_count"]} · source records: {readout["records"]}</p>
      <div class="grid company-kpis">
        <div class="card"><div class="label">Cumulative H100e</div><div class="value">{fmt_num(float(readout["total_h100e"]), 1)}</div><p class="small">Global share {fmt_pct(float(readout["h100e_share"]))}</p></div>
        <div class="card"><div class="label">Cumulative units</div><div class="value">{fmt_num(float(readout["total_units"]), 1)}</div><p class="small">Global unit share {fmt_pct(float(readout["unit_share"]))}</p></div>
        <div class="card"><div class="label">Estimated spend</div><div class="value">${fmt_num(float(readout["total_cost"]), 1)}</div><p class="small">chip purchase-price proxy</p></div>
        <div class="card"><div class="label">Latest quarter</div><div class="value">{fmt_num(float(readout["latest_h100e"]), 1)}</div><p class="small">{esc(readout["latest_quarter"])} · QoQ {latest_direction} {fmt_pct(abs(float(readout["latest_delta"])))}</p></div>
      </div>
      <div class="analysis-grid">
        <div>
          <h3>해석</h3>
          <ul>
            {''.join(f'<li>{esc(item)}</li>' for item in narrative)}
          </ul>
          <p class="small">Peak quarter: {esc(readout["peak_quarter"])} / {fmt_num(float(readout["peak_h100e"]), 1)} H100e. Incomplete records: {readout["incomplete_records"]}.</p>
        </div>
        <div class="chart">{bar_svg(product_labels, product_h100e, f"{maker} cumulative H100e by product", width=760, height=300)}</div>
      </div>
      <div class="chart">{category_line_svg(maker_quarterly, f"{maker} quarterly product mix by H100e", "Chip type", "h100e")}</div>
      <h3>{esc(maker)} 제품별 누적 요약</h3>
      {table_html(display_company_products(maker_products))}
      <h3>{esc(maker)} 분기별 제품 상세</h3>
      <div class="wide-table">{table_html(display_company_quarters(maker_quarterly))}</div>
    </section>
"""
        company_sections.append(section)

    inventory_df = pd.DataFrame(
        [
            {
                "file": item.name,
                "rows": item.rows,
                "columns": item.cols,
                "sha256_prefix": item.sha256,
            }
            for item in inventory
        ]
    )

    designer_labels = by_designer["Chip manufacturer"].tolist()
    h100e_values = by_designer["h100e"].tolist()
    unit_values = by_designer["units"].tolist()
    latest_labels = latest_summary["Chip manufacturer"].tolist()
    latest_h100e_values = latest_summary["h100e"].tolist()

    top_designer = by_designer.iloc[0]
    top_chip = by_chip.sort_values("h100e", ascending=False).iloc[0]
    latest_top = latest_summary.iloc[0]
    incomplete_count = int(timelines["Incomplete"].sum())

    notes = [
        "Epoch AI describes this dataset as estimates of dedicated AI accelerator sales or shipments, not audited company unit disclosures.",
        "H100e is a normalized peak 8-bit compute proxy, not measured real-world training or inference throughput.",
        "Chip TDP power excludes server, networking, cooling, and facility overhead; Epoch notes datacenter draw can be materially higher than chip TDP alone.",
        "Quarterly timing may include interpolation where fiscal periods or source records do not align exactly with calendar quarters.",
    ]

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Epoch AI Chip Sales 분석 리포트</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #5f6b7a;
      --line: #d9e0ea;
      --paper: #ffffff;
      --band: #f4f7fb;
      --accent: #2b6cb0;
      --accent2: #319795;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #eef2f7;
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.55;
    }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    header {{
      background: linear-gradient(135deg, #10243d 0%, #1f6f78 100%);
      color: white;
      padding: 42px 28px;
      border-bottom: 1px solid rgba(255,255,255,.18);
    }}
    header .wrap {{ padding-top: 0; padding-bottom: 0; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2 {{ margin: 34px 0 14px; font-size: 23px; }}
    h3 {{ margin: 24px 0 10px; font-size: 18px; }}
    p {{ margin: 8px 0; }}
    a {{ color: var(--accent); }}
    header a {{ color: #d9f3ff; }}
    .subtitle {{ max-width: 980px; color: #dbeafe; font-size: 16px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 18px; }}
    .card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(20,30,50,.04);
    }}
    .kpi {{ background: rgba(255,255,255,.1); border-color: rgba(255,255,255,.24); color: white; }}
    .kpi .label {{ color: #c7d7e8; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .kpi .value {{ font-size: 26px; font-weight: 700; margin-top: 4px; }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
    .section {{ background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 20px; margin: 18px 0; }}
    .company-section {{ border-left: 5px solid var(--accent); }}
    .company-kpis {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .analysis-grid {{ display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(360px, .9fr); gap: 16px; align-items: start; }}
    .callout {{ border-left: 4px solid var(--accent2); background: #eefaf9; padding: 12px 14px; margin: 16px 0; }}
    .small {{ color: var(--muted); font-size: 13px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0 20px; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 8px 9px; text-align: right; vertical-align: top; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{ text-align: left; }}
    th {{ background: var(--band); color: #27364a; font-weight: 650; position: sticky; top: 0; }}
    .wide-table {{ max-height: 520px; overflow: auto; border: 1px solid var(--line); border-radius: 8px; }}
    .chart {{ border: 1px solid var(--line); border-radius: 8px; padding: 10px; margin: 12px 0; background: #fff; overflow-x: auto; }}
    .axis {{ stroke: #8390a2; stroke-width: 1; }}
    .chart-title {{ font-weight: 700; font-size: 14px; fill: #172033; }}
    .bar-label, .x-label, .legend {{ font-size: 11px; fill: #334155; }}
    ul {{ margin-top: 6px; }}
    code {{ background: #eef2f7; padding: 1px 4px; border-radius: 4px; }}
    footer {{ color: var(--muted); padding: 26px 0 40px; font-size: 13px; }}
    @media (max-width: 860px) {{
      .grid {{ grid-template-columns: repeat(2, 1fr); }}
      .company-kpis {{ grid-template-columns: repeat(2, 1fr); }}
      .analysis-grid {{ grid-template-columns: 1fr; }}
      .wrap {{ padding: 18px; }}
      h1 {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>Epoch AI Chip Sales 분석 리포트</h1>
      <p class="subtitle">로컬 <code>ai_chip_sales</code> CSV 패키지 전체를 읽어 칩메이커별 제품 판매, H100-equivalent compute, 비용, 전력 분포를 분기 단위로 요약했다. 외부 설명은 Epoch AI 데이터 허브와 문서 페이지를 기준으로 대조했다.</p>
      <p class="small">분석 범위: {esc(first_q)} to {esc(last_q)} · 생성 파일: {esc(OUTPUT_PATH.name)}</p>
      <div class="grid">
        <div class="card kpi"><div class="label">Total units</div><div class="value">{fmt_num(total_units, 1)}</div></div>
        <div class="card kpi"><div class="label">H100e compute</div><div class="value">{fmt_num(total_h100e, 1)}</div></div>
        <div class="card kpi"><div class="label">Estimated chip spend</div><div class="value">${fmt_num(total_cost, 1)}</div></div>
        <div class="card kpi"><div class="label">Chip TDP power</div><div class="value">{fmt_num(total_power_mw, 1)} MW</div></div>
      </div>
    </div>
  </header>

  <main class="wrap">
    <section class="section">
      <h2>Executive Summary</h2>
      <p>전체 H100e 기준 최대 비중은 <strong>{esc(top_designer["Chip manufacturer"])}</strong>이고, 누적 compute share는 <strong>{fmt_pct(top_designer["h100e_share"])}</strong>다. 제품 단위로는 <strong>{esc(top_chip["Chip manufacturer"])} {esc(top_chip["Chip type"])}</strong>가 가장 큰 누적 compute 기여 제품이다.</p>
      <p>최신 분기({esc(latest_quarter)}) 기준 최대 H100e 기여 칩메이커는 <strong>{esc(latest_top["Chip manufacturer"])}</strong>이며, 해당 분기 H100e는 <strong>{fmt_num(latest_top["h100e"], 1)}</strong>다.</p>
      <div class="callout">
        <strong>읽는 법:</strong> 이 리포트의 “sales”는 Epoch AI 데이터셋의 estimated sales/shipments를 따른다. 즉, 회사가 감사보고서처럼 공개한 확정 판매량이 아니라, revenue commentary, analyst estimate, media report 등을 종합한 추정치다.
      </div>
      <ul>
        <li>분기별 record 중 incomplete flag가 있는 항목은 {incomplete_count}개다. fiscal quarter와 calendar quarter가 어긋나거나 원천 정보가 기간 전체를 덮지 않는 경우가 포함된다.</li>
        <li>H100e는 H100 대비 peak 8-bit operations 기준 proxy다. 메모리, 네트워크, 소프트웨어 stack 차이 때문에 실제 workload throughput으로 직접 해석하면 안 된다.</li>
        <li>Power는 chip TDP 합계이며 datacenter 총 전력은 서버/냉각/facility overhead 때문에 더 클 수 있다.</li>
      </ul>
    </section>

    <section class="section">
      <h2>칩메이커별 누적 분포</h2>
      <div class="chart">{bar_svg(designer_labels, h100e_values, "Cumulative H100e by chip designer")}</div>
      <div class="chart">{bar_svg(designer_labels, unit_values, "Cumulative units by chip designer")}</div>
      {table_html(display_designer(by_designer))}
    </section>

    <section class="section">
      <h2>분기별 흐름</h2>
      <div class="chart">{line_svg(quarterly, "Quarterly H100e shipment estimate by designer", "h100e")}</div>
      <div class="chart">{bar_svg(latest_labels, latest_h100e_values, f"Latest quarter H100e distribution ({latest_quarter})")}</div>
      <h3>전체 분기·제품별 판매 요약</h3>
      <div class="wide-table">{table_html(display_quarterly(quarterly))}</div>
    </section>

    <section class="section">
      <h2>메인 제품과 제품 포트폴리오</h2>
      <p>아래 표는 각 칩메이커별 누적 H100e 기준 상위 3개 제품이다. 단순 unit 기준이 아니라 normalized compute 기여도를 중심으로 메인 제품을 잡았다.</p>
      {table_html(display_chip(main_products))}
      <h3>전체 제품별 누적 요약</h3>
      <div class="wide-table">{table_html(display_chip(by_chip))}</div>
      <h3>제품별 peak quarter</h3>
      <div class="wide-table">{table_html(display_peak(peak_df))}</div>
    </section>

    <section class="section">
      <h2>기업별 Deep Dive 읽는 순서</h2>
      <p>아래 기업별 섹션은 같은 구조로 반복된다. 먼저 누적 H100e와 units로 상대 규모를 보고, 그 다음 최신 분기와 peak quarter를 비교한 뒤, 제품별 bar/line chart로 세대 전환을 확인하면 된다.</p>
      <p>해석상 가장 중요한 축은 <strong>제품 믹스 전환</strong>이다. Nvidia는 Hopper에서 Blackwell, Google은 TPU v6e/v7, Amazon은 Trainium2, AMD는 MI300X 이후 MI350/MI355, Huawei는 Ascend 910C, Cambricon은 Siyuan 590 중심으로 읽힌다.</p>
    </section>

    {''.join(company_sections)}

    <section class="section">
      <h2>제품 스펙 분포</h2>
      <p>chip_types.csv 기준의 H100e, TDP, memory, bandwidth, approximate cost를 함께 붙였다. 실제 판매량 테이블과 별도로, 제품별 성능/가격 스펙의 분포를 보는 보조 테이블이다.</p>
      <div class="wide-table">{table_html(display_specs(spec_table))}</div>
    </section>

    <section class="section">
      <h2>데이터 Provenance</h2>
      <p>이 HTML은 아래 로컬 CSV만 읽어 생성했다. 원본 CSV 파일은 깃에 올리지 않는 전제로, 파일명·row count·hash prefix를 남겨 재생성 가능성을 확보했다.</p>
      {table_html(inventory_df)}
      <h3>Epoch AI 문서에서 반영한 해석 규칙</h3>
      <ul>
        {''.join(f'<li>{esc(note)}</li>' for note in notes)}
      </ul>
      <p class="small">참고: <a href="https://epoch.ai/data/ai-chip-sales">Epoch AI Data on AI Chip Sales</a>, <a href="https://epoch.ai/data/ai-chip-sales-documentation">AI Chip Sales Documentation</a>, <a href="https://epoch.ai/data/ai-chip-sales-documentation/methodology">Methodology</a>, <a href="https://epoch.ai/data/ai-chip-sales-documentation/records">Records</a>.</p>
    </section>
  </main>

  <footer class="wrap">
    Generated from local CSV files in <code>{esc(str(DATA_DIR))}</code>. Epoch AI data is credited under the Creative Commons Attribution license.
  </footer>
</body>
</html>
"""
    return html_doc


def main() -> None:
    html_doc = "\n".join(line.rstrip() for line in build_report().splitlines()) + "\n"
    OUTPUT_PATH.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
