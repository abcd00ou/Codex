"""
Newsletter Data Agent
- yfinance: 주가/실적/마진/밸류에이션 (전 유니버스)
- SEC EDGAR: 미국 기업 최신 8-K (실적 발표) 파싱
- IR 스크래핑: TSMC/SK Hynix/Samsung 가이던스
- RSS: 최신 뉴스
결과를 data/newsletter_state.json에 저장
"""

import os, sys, json, datetime, time, urllib.request, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _ROOT)

import config
from agents.newsletter.universe import ALL_TICKERS, UNIVERSE, LAYER_COLOR

STATE_FILE = os.path.join(config.DATA_DIR, "newsletter_state.json")

# ============================================================
# 1. 주가 / 실적 (yfinance)
# ============================================================
def fetch_market_data() -> dict:
    try:
        import yfinance as yf
    except ImportError:
        print("  [DataAgent] yfinance 없음 → 주가 스킵")
        return {}

    results = {}
    tickers = [t for t, _, _ in ALL_TICKERS]
    print(f"  [DataAgent] yfinance {len(tickers)}개 수집 중...")

    def _fetch_one(item):
        ticker, name, layer = item
        try:
            stk  = yf.Ticker(ticker)
            info = stk.info or {}

            # 주가
            price    = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
            prev     = info.get("previousClose") or price
            chg_pct  = round((price - prev) / prev * 100, 2) if prev and price else 0

            # 52주
            hi52 = info.get("fiftyTwoWeekHigh")
            lo52 = info.get("fiftyTwoWeekLow")
            from52hi = round((price - hi52) / hi52 * 100, 1) if hi52 and price else None

            # 밸류에이션
            pe       = info.get("trailingPE")
            fwd_pe   = info.get("forwardPE")
            mktcap   = info.get("marketCap")
            mktcap_b = round(mktcap / 1e9, 1) if mktcap else None

            # 실적
            rev_ttm  = info.get("totalRevenue")
            rev_b    = round(rev_ttm / 1e9, 1) if rev_ttm else None
            gm       = info.get("grossMargins")
            gm_pct   = round(gm * 100, 1) if gm else None
            op_margin= info.get("operatingMargins")
            op_pct   = round(op_margin * 100, 1) if op_margin else None

            # 가이던스/추정
            target   = info.get("targetMeanPrice")
            upside   = round((target - price) / price * 100, 1) if target and price else None

            return ticker, {
                "name":        name,
                "layer":       layer,
                "price":       price,
                "chg_pct":     chg_pct,
                "hi52":        hi52,
                "lo52":        lo52,
                "from52hi_pct":from52hi,
                "mktcap_b":    mktcap_b,
                "pe_trailing": round(pe, 1) if pe else None,
                "pe_forward":  round(fwd_pe, 1) if fwd_pe else None,
                "revenue_ttm_b": rev_b,
                "gross_margin_pct": gm_pct,
                "op_margin_pct":    op_pct,
                "analyst_target":   target,
                "analyst_upside_pct": upside,
                "currency":    info.get("currency", "USD"),
                "fetched_at":  str(datetime.datetime.now()),
            }
        except Exception as e:
            return ticker, {"name": name, "layer": layer, "error": str(e)}

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_one, item): item for item in ALL_TICKERS}
        for fut in as_completed(futures):
            ticker, data = fut.result()
            results[ticker] = data

    ok = sum(1 for v in results.values() if "error" not in v)
    print(f"  [DataAgent] 주가 수집 완료: {ok}/{len(tickers)}개")
    return results


# ============================================================
# 2. SEC EDGAR - 최신 8-K (실적 발표) 파싱
# ============================================================
EDGAR_HEADERS = {"User-Agent": "AI-SCM-Newsletter contact@example.com"}

def _edgar_cik(ticker: str) -> str | None:
    """ticker → CIK"""
    try:
        url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2025-01-01&forms=10-K"
        # 더 안정적인 방법: company search
        url2 = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}&type=8-K&dateb=&owner=include&count=1&search_text=&output=atom"
        req = urllib.request.Request(url2, headers=EDGAR_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode()
        # CIK 파싱
        import re
        m = re.search(r'CIK=(\d+)', raw)
        return m.group(1) if m else None
    except Exception:
        return None


def fetch_sec_filings(tickers: list[str], max_per_ticker: int = 1) -> dict:
    """미국 기업 최신 8-K 제목·날짜 수집"""
    results = {}
    us_tickers = [t for t, _, _ in ALL_TICKERS if not t.endswith(".KS")][:10]  # 상위 10개만

    for ticker in us_tickers:
        try:
            # EDGAR RSS 피드 사용 (더 안정적)
            url = (f"https://www.sec.gov/cgi-bin/browse-edgar"
                   f"?action=getcompany&CIK={ticker}&type=8-K"
                   f"&dateb=&owner=include&count=3&search_text=&output=atom")
            req = urllib.request.Request(url, headers=EDGAR_HEADERS)
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read()
            root = ET.fromstring(raw)
            ns   = {"atom": "http://www.w3.org/2005/Atom"}
            entries = []
            for entry in root.findall("atom:entry", ns):
                title  = (entry.findtext("atom:title",   namespaces=ns) or "").strip()
                updated= (entry.findtext("atom:updated", namespaces=ns) or "")[:10]
                link_el = entry.find("atom:link", ns)
                link   = link_el.get("href","") if link_el is not None else ""
                if title:
                    entries.append({"title": title, "date": updated, "url": link})
            if entries:
                results[ticker] = entries[:max_per_ticker]
            time.sleep(0.3)  # EDGAR rate limit
        except Exception:
            pass

    print(f"  [DataAgent] SEC EDGAR {len(results)}개 수집")
    return results


# ============================================================
# 3. 뉴스 수집
# ============================================================
RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/technologyNews",
    "https://semiengineering.com/feed/",
    "https://www.tomshardware.com/feeds/all",
    "https://feeds.feedburner.com/TechCrunch",
]
SCM_KW = [
    "nvidia","hbm","tsmc","cowos","sk hynix","samsung","micron","gpu",
    "blackwell","gb200","b200","data center","hyperscaler","capex","broadcom",
    "vertiv","ge vernova","power","transformer","sovereign ai","ai chip",
    "semiconductor","amd","mi300","trainium","tpu","asic","infiniband",
    "arista","networking","packaging","hbm4","hbm3e","cowos-l",
]

def fetch_news(max_items: int = 12) -> list[dict]:
    all_items = []
    for url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 AI-SCM/2.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read()
            root = ET.fromstring(raw)
            for item in root.iter("item"):
                t = (item.findtext("title") or "").strip()
                l = (item.findtext("link")  or "").strip()
                d = (item.findtext("pubDate") or "")
                if t and any(k in t.lower() for k in SCM_KW):
                    try:
                        from email.utils import parsedate_to_datetime
                        date_str = parsedate_to_datetime(d).strftime("%Y-%m-%d")
                    except Exception:
                        date_str = str(datetime.date.today())
                    all_items.append({"title": t, "url": l, "date": date_str,
                                      "source": url.split("/")[2].replace("www.","").replace("feeds.","")})
        except Exception:
            pass

    seen, dedup = set(), []
    for item in all_items:
        k = item["title"][:60]
        if k not in seen:
            seen.add(k)
            dedup.append(item)
        if len(dedup) >= max_items:
            break

    print(f"  [DataAgent] 뉴스 {len(dedup)}개 수집")
    return dedup


# ============================================================
# 4. 레이어별 병목 분석 (주가 + config 통합)
# ============================================================
def analyze_layers(market: dict) -> dict:
    """레이어별 종합 점수 및 시그널 생성"""
    layer_data = {}

    for layer, tickers_info in UNIVERSE.items():
        layer_tickers = [t["ticker"] for t in tickers_info]
        stocks = [market.get(tk, {}) for tk in layer_tickers if market.get(tk) and "error" not in market.get(tk,{})]

        if not stocks:
            continue

        # 레이어 평균 등락
        chgs = [s["chg_pct"] for s in stocks if s.get("chg_pct") is not None]
        avg_chg = round(sum(chgs) / len(chgs), 2) if chgs else 0

        # 애널리스트 업사이드 평균
        upsides = [s["analyst_upside_pct"] for s in stocks if s.get("analyst_upside_pct")]
        avg_upside = round(sum(upsides) / len(upsides), 1) if upsides else None

        # config 가동률 매핑
        util_map = {
            "GPU": "GPU", "HBM": "HBM", "Packaging": "CoWoS",
            "Networking": "Networking", "Power": "Power_DC",
        }
        util_key  = util_map.get(layer)
        util_rate = config.CURRENT_CAPACITY_UTILIZATION.get(util_key) if util_key else None

        # 시그널
        if util_rate and util_rate >= 0.85:
            signal = "🔴 Critical Bottleneck"
        elif util_rate and util_rate >= 0.70:
            signal = "🟡 Tight Supply"
        elif avg_chg > 2:
            signal = "🟢 Momentum"
        else:
            signal = "⚪ Neutral"

        layer_data[layer] = {
            "color":       LAYER_COLOR.get(layer, "#4a5568"),
            "avg_chg_pct": avg_chg,
            "avg_upside":  avg_upside,
            "util_rate":   util_rate,
            "signal":      signal,
            "stock_count": len(stocks),
        }

    return layer_data


# ============================================================
# 5. 주가 움직임 기반 시그널 생성
# ============================================================
def generate_signals(market: dict) -> list[dict]:
    """주목할 종목 자동 감지"""
    signals = []
    for ticker, d in market.items():
        if "error" in d:
            continue
        chg   = d.get("chg_pct", 0) or 0
        up    = d.get("analyst_upside_pct")
        f52hi = d.get("from52hi_pct")
        pe    = d.get("pe_forward")

        reasons = []
        if abs(chg) >= 3:
            reasons.append(f"전일 대비 {chg:+.1f}% 급{'등' if chg>0 else '락'}")
        if up and up >= 20:
            reasons.append(f"애널리스트 목표가 대비 {up:.0f}% 업사이드")
        if f52hi and f52hi <= -20:
            reasons.append(f"52주 고점 대비 {f52hi:.0f}% (저가권)")
        if pe and pe < 15 and d.get("layer") in ["HBM","GPU","Packaging"]:
            reasons.append(f"fwd PER {pe}x (섹터 대비 저평가)")

        if reasons:
            signals.append({
                "ticker":  ticker,
                "name":    d.get("name",""),
                "layer":   d.get("layer",""),
                "price":   d.get("price"),
                "chg_pct": chg,
                "reasons": reasons,
            })

    return sorted(signals, key=lambda x: abs(x.get("chg_pct",0)), reverse=True)[:8]


# ============================================================
# 메인 수집 함수
# ============================================================
def collect_all(force: bool = False) -> dict:
    """전체 데이터 수집 후 state 저장"""
    # 당일 캐시 확인
    if not force and os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            cached = json.load(f)
        cached_date = cached.get("date","")
        if cached_date == str(datetime.date.today()):
            print("  [DataAgent] 당일 캐시 사용")
            return cached

    print("  [DataAgent] 전체 데이터 수집 시작...")
    market  = fetch_market_data()
    filings = fetch_sec_filings([t for t, _, _ in ALL_TICKERS])
    news    = fetch_news(max_items=12)
    layers  = analyze_layers(market)
    signals = generate_signals(market)

    state = {
        "date":      str(datetime.date.today()),
        "as_of":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "market":    market,
        "filings":   filings,
        "news":      news,
        "layers":    layers,
        "signals":   signals,
    }

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)

    print(f"  [DataAgent] 수집 완료 → {STATE_FILE}")
    return state


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    state = collect_all(force=args.force)
    print(f"\n기업: {len(state['market'])}개 | 뉴스: {len(state['news'])}개 | 시그널: {len(state['signals'])}개")
