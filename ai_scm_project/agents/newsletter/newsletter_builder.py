"""
Newsletter Builder
실시간 데이터 + 분석 → 종합 HTML 뉴스레터
섹션: Executive Summary / Layer Scorecard / 기업 실적 / 시그널 / 뉴스
"""

import os, sys, datetime, json

_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _ROOT)

import config
from agents.newsletter.universe import UNIVERSE, LAYER_COLOR

# ============================================================
# 공통 유틸
# ============================================================
def _chg_color(v):
    if v is None: return "#a0aec0"
    return "#e53e3e" if v < 0 else "#38a169" if v > 0 else "#4a5568"

def _chg_str(v):
    if v is None: return "—"
    return f"{v:+.2f}%"

def _fmt(v, suffix="", prefix=""):
    if v is None: return "—"
    return f"{prefix}{v}{suffix}"

def _util_bar(rate, width=160):
    if rate is None: return "—"
    pct = int(rate * 100)
    w   = int(rate * width)
    c   = "#e53e3e" if pct >= 85 else "#d69e2e" if pct >= 70 else "#38a169"
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;">'
        f'<span style="display:inline-block;background:{c};width:{w}px;height:9px;border-radius:2px;"></span>'
        f'<strong style="color:{c};font-size:13px;">{pct}%</strong></span>'
    )

def _price_cell(d):
    if not d.get("price"): return "—"
    cur = "₩" if d.get("currency") == "KRW" else "$"
    p   = d["price"]
    fmt = f"{p:,.0f}" if d.get("currency")=="KRW" else f"{p:.2f}"
    return f'{cur}{fmt}'


# ============================================================
# 섹션 1: Executive Summary + 편집자 코멘트
# ============================================================
def _section_executive(state: dict, editor_comment: str) -> str:
    today    = datetime.date.today().strftime("%Y년 %m월 %d일 (월)")
    as_of    = state.get("as_of", "")
    signals  = state.get("signals", [])
    layers   = state.get("layers", {})

    # 오늘의 핵심 시그널 3개
    top3 = signals[:3]
    signal_html = ""
    for s in top3:
        chg = s.get("chg_pct", 0)
        c   = _chg_color(chg)
        signal_html += (
            f'<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;">'
            f'<span style="background:{LAYER_COLOR.get(s["layer"],"#4a5568")};color:white;'
            f'font-size:10px;padding:2px 7px;border-radius:3px;white-space:nowrap;margin-top:2px;">'
            f'{s["layer"]}</span>'
            f'<div><strong style="color:#2d3748;">{s["name"]} ({s["ticker"]})</strong>'
            f'<span style="color:{c};margin-left:8px;font-size:13px;">{_chg_str(chg)}</span>'
            f'<div style="color:#718096;font-size:12px;margin-top:2px;">'
            + " / ".join(s.get("reasons",[])) + '</div></div></div>'
        )
    if not signal_html:
        signal_html = '<p style="color:#a0aec0;font-size:13px;">시장 데이터 수집 후 자동 생성됩니다.</p>'

    # 레이어 요약 (Critical만)
    critical = [(l, d) for l, d in layers.items() if d.get("util_rate", 0) and d["util_rate"] >= 0.85]
    critical_html = "".join(
        f'<span style="background:#fff5f5;border:1px solid #fed7d7;color:#c53030;'
        f'padding:3px 10px;border-radius:12px;font-size:12px;margin:2px;">'
        f'🔴 {l} {int(d["util_rate"]*100)}%</span>'
        for l, d in critical
    )

    # 편집자 코멘트
    if editor_comment and editor_comment.strip():
        comment_html = (
            f'<div style="background:#fffaf0;border-left:4px solid #d69e2e;'
            f'padding:14px 18px;border-radius:0 6px 6px 0;margin-top:12px;">'
            f'<div style="font-size:11px;font-weight:700;color:#b7791f;'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">✍️ Editor\'s Comment</div>'
            f'<div style="font-size:14px;color:#2d3748;line-height:1.8;">{editor_comment}</div>'
            f'</div>'
        )
    else:
        comment_html = (
            f'<div style="background:#f7f8fa;border:1px dashed #e2e8f0;'
            f'padding:14px 18px;border-radius:6px;margin-top:12px;color:#a0aec0;font-size:13px;">'
            f'✍️ 편집자 코멘트 없음 — <code>run_newsletter.py --comment "..."</code>로 추가하세요.'
            f'</div>'
        )

    return f"""
<div style="margin-bottom:32px;">
  <div style="font-size:12px;font-weight:700;color:#4a5568;text-transform:uppercase;
              letter-spacing:.5px;margin-bottom:14px;">🎯 Executive Summary</div>

  <div style="margin-bottom:14px;">
    <div style="font-size:12px;color:#718096;margin-bottom:6px;">현재 병목 레이어</div>
    <div>{critical_html if critical_html else '<span style="color:#a0aec0;font-size:12px;">수집 데이터 기반 자동 업데이트</span>'}</div>
  </div>

  <div style="font-size:12px;color:#718096;margin-bottom:8px;">오늘의 주목 종목</div>
  {signal_html}

  {comment_html}
</div>"""


# ============================================================
# 섹션 2: Layer Scorecard (전 레이어 실시간)
# ============================================================
def _section_layer_scorecard(state: dict) -> str:
    layers = state.get("layers", {})
    market = state.get("market", {})

    rows = ""
    for layer, tickers_info in UNIVERSE.items():
        ld    = layers.get(layer, {})
        color = LAYER_COLOR.get(layer, "#4a5568")
        util  = ld.get("util_rate")
        chg   = ld.get("avg_chg_pct", 0)
        sig   = ld.get("signal", "⚪ Neutral")
        up    = ld.get("avg_upside")

        # 대표 종목 2개
        top_stocks = []
        for t_info in tickers_info[:2]:
            tk = t_info["ticker"]
            d  = market.get(tk, {})
            if d and "error" not in d and d.get("price"):
                top_stocks.append(
                    f'<span style="font-size:11px;color:#4a5568;">'
                    f'{tk} {_price_cell(d)} '
                    f'<span style="color:{_chg_color(d.get("chg_pct"))}">{_chg_str(d.get("chg_pct"))}</span>'
                    f'</span>'
                )

        rows += f"""
<tr>
  <td style="padding:10px 12px;white-space:nowrap;">
    <span style="background:{color};color:white;font-size:11px;
                 padding:2px 8px;border-radius:3px;">{layer}</span>
  </td>
  <td style="padding:10px 12px;">{_util_bar(util) if util else "—"}</td>
  <td style="padding:10px 12px;color:{_chg_color(chg)};font-weight:600;">
    {_chg_str(chg)}
  </td>
  <td style="padding:10px 12px;font-size:11px;">{" &nbsp; ".join(top_stocks) if top_stocks else "—"}</td>
  <td style="padding:10px 12px;font-size:12px;">{sig}</td>
</tr>"""

    return f"""
<div style="margin-bottom:32px;">
  <div style="font-size:12px;font-weight:700;color:#4a5568;text-transform:uppercase;
              letter-spacing:.5px;margin-bottom:12px;">📊 Layer Scorecard</div>
  <table style="border-collapse:collapse;width:100%;font-size:13px;">
    <thead>
      <tr style="background:#f7f8fa;border-bottom:2px solid #e2e8f0;">
        <th style="padding:8px 12px;text-align:left;color:#718096;">레이어</th>
        <th style="padding:8px 12px;text-align:left;color:#718096;">가동률</th>
        <th style="padding:8px 12px;text-align:left;color:#718096;">레이어 등락</th>
        <th style="padding:8px 12px;text-align:left;color:#718096;">대표 종목</th>
        <th style="padding:8px 12px;text-align:left;color:#718096;">시그널</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <div style="font-size:11px;color:#a0aec0;margin-top:6px;">
    가동률: config.py 2026 Q1 기준 | 등락: 전일 대비 yfinance 실시간
  </div>
</div>"""


# ============================================================
# 섹션 3: 기업별 실적 & 밸류에이션 테이블
# ============================================================
def _section_company_table(state: dict) -> str:
    market = state.get("market", {})

    blocks = ""
    for layer, tickers_info in UNIVERSE.items():
        color = LAYER_COLOR.get(layer, "#4a5568")
        rows  = ""
        any_data = False

        for t_info in tickers_info:
            tk = t_info["ticker"]
            d  = market.get(tk, {})
            if not d or "error" in d:
                rows += (
                    f'<tr><td style="padding:7px 10px;font-weight:600;">{tk}</td>'
                    f'<td style="padding:7px 10px;color:#718096;" colspan="8">'
                    f'{t_info["name"]} — 데이터 수집 실패</td></tr>'
                )
                continue
            any_data = True
            price_str = _price_cell(d)
            chg       = d.get("chg_pct")
            mkt       = f'${d["mktcap_b"]}B' if d.get("mktcap_b") else "—"
            pe_t      = _fmt(d.get("pe_trailing"), "x")
            pe_f      = _fmt(d.get("pe_forward"),  "x")
            rev       = f'${d["revenue_ttm_b"]}B' if d.get("revenue_ttm_b") else "—"
            gm        = f'{d["gross_margin_pct"]}%' if d.get("gross_margin_pct") else "—"
            up        = f'+{d["analyst_upside_pct"]:.0f}%' if d.get("analyst_upside_pct") and d["analyst_upside_pct"]>0 else (f'{d["analyst_upside_pct"]:.0f}%' if d.get("analyst_upside_pct") else "—")
            up_color  = "#38a169" if d.get("analyst_upside_pct", 0) > 0 else "#e53e3e"

            rows += f"""
<tr style="border-bottom:1px solid #f0f0f0;">
  <td style="padding:7px 10px;font-weight:700;white-space:nowrap;">{tk}</td>
  <td style="padding:7px 10px;color:#718096;font-size:11px;">{t_info['name']}</td>
  <td style="padding:7px 10px;font-weight:600;">{price_str}</td>
  <td style="padding:7px 10px;color:{_chg_color(chg)};font-weight:600;">{_chg_str(chg)}</td>
  <td style="padding:7px 10px;">{mkt}</td>
  <td style="padding:7px 10px;color:#718096;">{pe_t}</td>
  <td style="padding:7px 10px;color:#2b6cb0;">{pe_f}</td>
  <td style="padding:7px 10px;">{rev}</td>
  <td style="padding:7px 10px;">{gm}</td>
  <td style="padding:7px 10px;color:{up_color};font-weight:600;">{up}</td>
</tr>"""

        if not any_data and not rows:
            continue

        blocks += f"""
<div style="margin-bottom:20px;">
  <div style="background:{color};color:white;font-size:12px;font-weight:700;
              padding:6px 12px;border-radius:4px 4px 0 0;">{layer}</div>
  <table style="border-collapse:collapse;width:100%;font-size:12px;
                border:1px solid #e2e8f0;border-top:none;">
    <thead><tr style="background:#f7f8fa;">
      <th style="padding:6px 10px;text-align:left;">Ticker</th>
      <th style="padding:6px 10px;text-align:left;">기업</th>
      <th style="padding:6px 10px;text-align:left;">주가</th>
      <th style="padding:6px 10px;text-align:left;">전일比</th>
      <th style="padding:6px 10px;text-align:left;">시총</th>
      <th style="padding:6px 10px;text-align:left;">PER(T)</th>
      <th style="padding:6px 10px;text-align:left;">PER(F)</th>
      <th style="padding:6px 10px;text-align:left;">매출(TTM)</th>
      <th style="padding:6px 10px;text-align:left;">GM</th>
      <th style="padding:6px 10px;text-align:left;">목표가↑</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

    return f"""
<div style="margin-bottom:32px;">
  <div style="font-size:12px;font-weight:700;color:#4a5568;text-transform:uppercase;
              letter-spacing:.5px;margin-bottom:12px;">🏭 기업별 실적 & 밸류에이션</div>
  {blocks}
  <div style="font-size:11px;color:#a0aec0;">
    PER(T)=trailing 12M | PER(F)=forward 1Y | GM=Gross Margin | 목표가↑=애널리스트 컨센서스 업사이드
  </div>
</div>"""


# ============================================================
# 섹션 4: 공급망 시그널
# ============================================================
def _section_signals(state: dict) -> str:
    signals = state.get("signals", [])
    if not signals:
        return ""

    items = ""
    for s in signals:
        chg   = s.get("chg_pct", 0)
        color = LAYER_COLOR.get(s.get("layer",""), "#4a5568")
        items += f"""
<div style="display:flex;align-items:flex-start;gap:12px;
            padding:12px 0;border-bottom:1px solid #f0f0f0;">
  <div style="min-width:80px;">
    <span style="background:{color};color:white;font-size:10px;
                 padding:2px 7px;border-radius:3px;">{s.get("layer","")}</span>
  </div>
  <div style="flex:1;">
    <div style="font-weight:700;color:#2d3748;font-size:14px;">
      {s.get("name","")} <span style="color:#718096;font-weight:400;font-size:12px;">({s.get("ticker","")})</span>
      <span style="color:{_chg_color(chg)};margin-left:8px;">{_chg_str(chg)}</span>
    </div>
    <div style="color:#718096;font-size:12px;margin-top:3px;line-height:1.6;">
      {"  |  ".join(s.get("reasons",[]))}
    </div>
  </div>
</div>"""

    return f"""
<div style="margin-bottom:32px;">
  <div style="font-size:12px;font-weight:700;color:#4a5568;text-transform:uppercase;
              letter-spacing:.5px;margin-bottom:12px;">⚡ 공급망 시그널</div>
  {items}
  <div style="font-size:11px;color:#a0aec0;margin-top:8px;">
    * 주가 급등락(±3%), 52주 고저, 애널리스트 목표가 괴리 기반 자동 감지
  </div>
</div>"""


# ============================================================
# 섹션 5: 뉴스
# ============================================================
def _section_news(state: dict) -> str:
    news = state.get("news", [])
    if not news:
        return ""

    items = "".join(
        f'<li style="margin-bottom:9px;font-size:13px;line-height:1.5;">'
        f'<a href="{n.get("url","#")}" style="color:#2d3748;text-decoration:none;">{n["title"]}</a>'
        f'<span style="color:#a0aec0;font-size:11px;display:block;margin-top:2px;">'
        f'{n.get("source","")} · {n.get("date","")}</span></li>'
        for n in news[:10]
    )

    return f"""
<div style="margin-bottom:32px;">
  <div style="font-size:12px;font-weight:700;color:#4a5568;text-transform:uppercase;
              letter-spacing:.5px;margin-bottom:12px;">📰 최신 뉴스</div>
  <ul style="padding-left:0;list-style:none;margin:0;">{items}</ul>
</div>"""


# ============================================================
# 메인 빌드
# ============================================================
def build(state: dict, editor_comment: str = "") -> str:
    today   = datetime.date.today().strftime("%Y년 %m월 %d일")
    as_of   = state.get("as_of", "")
    n_mkt   = sum(1 for v in state.get("market",{}).values() if "error" not in v)
    n_sig   = len(state.get("signals",[]))

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI SCM Intelligence | {today}</title>
</head>
<body style="margin:0;padding:20px 0;background:#f0f2f5;
             font-family:'Apple SD Gothic Neo',Arial,sans-serif;">
<div style="max-width:760px;margin:0 auto;background:white;border-radius:10px;
            overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.10);">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1a202c 0%,#2d3748 100%);
              padding:28px 36px 24px;">
    <div style="color:rgba(255,255,255,.6);font-size:11px;letter-spacing:1px;
                text-transform:uppercase;margin-bottom:8px;">
      AI Supply Chain Intelligence
    </div>
    <div style="color:white;font-size:26px;font-weight:800;line-height:1.2;">
      Daily Briefing
    </div>
    <div style="color:rgba(255,255,255,.7);font-size:13px;margin-top:6px;">
      {today} &nbsp;·&nbsp; 기준 {as_of} &nbsp;·&nbsp;
      {n_mkt}개 기업 실시간 데이터 &nbsp;·&nbsp; {n_sig}개 시그널 감지
    </div>
  </div>

  <!-- 컨텐츠 -->
  <div style="padding:32px 36px;">

    {_section_executive(state, editor_comment)}

    <hr style="border:none;border-top:2px solid #edf2f7;margin:0 0 32px;">

    {_section_layer_scorecard(state)}

    <hr style="border:none;border-top:2px solid #edf2f7;margin:0 0 32px;">

    {_section_company_table(state)}

    <hr style="border:none;border-top:2px solid #edf2f7;margin:0 0 32px;">

    {_section_signals(state)}

    <hr style="border:none;border-top:2px solid #edf2f7;margin:0 0 32px;">

    {_section_news(state)}

  </div>

  <!-- Footer -->
  <div style="background:#1a202c;padding:20px 36px;font-size:11px;color:#718096;">
    <div style="color:#a0aec0;margin-bottom:4px;">
      AI SCM Intelligence Newsletter &nbsp;·&nbsp; {today}
    </div>
    <div>
      데이터: yfinance 실시간 | SEC EDGAR | config.py (2026 Q1 병목 기준) | RSS 뉴스
    </div>
  </div>

</div>
</body>
</html>"""
