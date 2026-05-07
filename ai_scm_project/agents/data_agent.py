"""
Data Intelligence Agent
- Loads seed data
- Attempts web scraping for latest market data
- Classifies events: capex / earnings / supply_update / demand_signal
- Updates market_state.json
"""

import json
import os
import sys
import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Optional imports - graceful fallback
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_ENABLED = True
except ImportError:
    WEB_ENABLED = False


def load_seed_data():
    """Load seed data from JSON file."""
    try:
        with open(config.SEED_DATA_PATH, "r") as f:
            data = json.load(f)
        print(f"  [DataAgent] Seed data loaded: {config.SEED_DATA_PATH}")
        return data
    except Exception as e:
        print(f"  [DataAgent] WARNING: Could not load seed data: {e}")
        return {}


def scrape_reuters_ai_news():
    """Attempt to scrape Reuters AI news headlines."""
    if not WEB_ENABLED:
        return []

    events = []
    urls = [
        "https://www.reuters.com/technology/artificial-intelligence/",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Extract headlines
                for tag in soup.find_all(["h3", "h2"], limit=20):
                    text = tag.get_text(strip=True)
                    if len(text) > 20:
                        event = classify_headline(text)
                        if event:
                            events.append(event)
                print(f"  [DataAgent] Scraped {len(events)} events from {url}")
                break
        except Exception as e:
            print(f"  [DataAgent] Scrape failed for {url}: {e}")

    return events


def classify_headline(text):
    """Classify a news headline into event type."""
    text_lower = text.lower()

    capex_keywords = ["capex", "invest", "billion", "data center", "infrastructure", "spend"]
    supply_keywords = ["supply", "shortage", "constraint", "hbm", "packaging", "cowos", "shipment"]
    demand_keywords = ["demand", "token", "inference", "usage", "deploy", "adopt"]
    earnings_keywords = ["earnings", "revenue", "profit", "quarterly", "guidance", "forecast"]

    event_type = None
    if any(k in text_lower for k in capex_keywords):
        event_type = "capex"
    elif any(k in text_lower for k in supply_keywords):
        event_type = "supply_update"
    elif any(k in text_lower for k in demand_keywords):
        event_type = "demand_signal"
    elif any(k in text_lower for k in earnings_keywords):
        event_type = "earnings"

    if event_type:
        return {
            "event": event_type,
            "headline": text[:200],
            "source": "reuters",
            "date": str(datetime.date.today()),
        }
    return None


def build_market_events(seed_data):
    """Build structured market events from seed data."""
    events = []

    # CapEx events (2025 actual + 2026 guidance)
    for company, years in seed_data.get("hyperscaler_capex_usd_bn", {}).items():
        if company.startswith("_"):
            continue
        for year, value in years.items():
            if year in ["2025", "2026", "2026_est"]:
                yr_clean = year.replace("_est", "")
                events.append({
                    "event": "capex",
                    "company": company,
                    "value": value * 1e9,
                    "year": yr_clean,
                    "source": "seed_data",
                    "confidence": "actual" if year == "2025" else "guidance",
                })

    # Supply constraint events from current utilization
    util = config.CURRENT_CAPACITY_UTILIZATION
    for component, util_rate in util.items():
        if util_rate >= config.BOTTLENECK_THRESHOLDS["critical"]:
            severity = "critical"
        elif util_rate >= config.BOTTLENECK_THRESHOLDS["high"]:
            severity = "high"
        elif util_rate >= config.BOTTLENECK_THRESHOLDS["medium"]:
            severity = "medium"
        else:
            severity = "low"

        if util_rate >= config.BOTTLENECK_THRESHOLDS["high"]:
            events.append({
                "event": "supply_constraint",
                "component": component,
                "severity": severity,
                "utilization": util_rate,
                "detail": f"{component} at {util_rate:.0%} utilization",
                "source": "config_current",
            })

    # Key timeline events
    for evt in seed_data.get("key_events_timeline", []):
        events.append({
            "event": evt.get("category", "other"),
            "headline": evt.get("event", ""),
            "date": evt.get("date", ""),
            "impact": evt.get("impact", ""),
            "source": "seed_data",
        })

    return events


def build_timeseries_summary(seed_data):
    """과거 시계열 데이터 요약 — 시계열 분석용."""
    ts = {}

    # NVIDIA 분기 매출
    nvidia_dc = seed_data.get("nvidia_datacenter_revenue_quarterly_usd_bn", {})
    if nvidia_dc:
        filtered = {k: v for k, v in nvidia_dc.items() if not k.startswith("_")}
        ts["nvidia_datacenter_qtrly"] = filtered
        ts["nvidia_latest_quarter_usd_bn"] = max(
            ((q, v) for q, v in filtered.items()),
            key=lambda x: x[0]
        ) if filtered else None

    # HBM 시장 규모
    hbm_size = seed_data.get("hbm_market", {}).get("market_size_usd_bn", {})
    ts["hbm_market_annual"] = {k: v for k, v in hbm_size.items() if not k.startswith("_")}

    # DC 전력
    dc_power = seed_data.get("datacenter_power", {}).get("global_gw", {})
    ts["datacenter_power_gw"] = {k: v for k, v in dc_power.items() if not k.startswith("_")}

    # 토큰 수요 연간
    token_ann = seed_data.get("token_demand_annual_estimates", {})
    ts["token_demand_annual"] = {k: v for k, v in token_ann.items() if not k.startswith("_")}

    # 가동률 시계열
    util_ts = seed_data.get("capacity_utilization_time_series", {})
    ts["capacity_utilization_timeseries"] = {
        k: v for k, v in util_ts.items() if not k.startswith("_")
    }

    # GPU 출하
    gpu_ship = seed_data.get("gpu_shipments", {})
    ts["gpu_shipments"] = {k: v for k, v in gpu_ship.items() if not k.startswith("_")}

    # AI 모델 파라미터 트렌드
    models = seed_data.get("ai_model_milestones", [])
    ts["ai_model_count"] = len(models)
    ts["ai_model_milestones_summary"] = [
        {"date": m["date"], "model": m["model"], "org": m["org"],
         "params": m.get("params", m.get("params_est", 0))}
        for m in models
    ]

    return ts


def run(quick=False):
    """Run the data agent and return market state."""
    print("[DataAgent] Starting data collection...")

    seed_data = load_seed_data()

    # Build events from seed data
    events = build_market_events(seed_data)

    # Attempt web scraping unless quick mode
    web_events = []
    if not quick and WEB_ENABLED:
        print("  [DataAgent] Attempting web scraping...")
        web_events = scrape_reuters_ai_news()
    elif quick:
        print("  [DataAgent] Quick mode: skipping web scraping")
    else:
        print("  [DataAgent] Web scraping disabled (requests/bs4 not available)")

    all_events = events + web_events

    # Build timeseries summary
    timeseries = build_timeseries_summary(seed_data)

    # Build market state
    market_state = {
        "events": all_events,
        "hyperscaler_capex": seed_data.get("hyperscaler_capex_usd_bn", {}),
        "gpu_shipments": seed_data.get("gpu_shipments", {}),
        "hbm_market": seed_data.get("hbm_market", {}),
        # config.CURRENT_CAPACITY_UTILIZATION이 항상 최신값 (2026 Q1 기준)
        "capacity_utilization": config.CURRENT_CAPACITY_UTILIZATION,
        "token_demand": seed_data.get("token_demand_estimates", {}),
        "cowos_capacity": seed_data.get("cowos_capacity", {}),
        "datacenter_power": seed_data.get("datacenter_power", {}),
        "investment_signals_seed": seed_data.get("investment_signals_seed", []),
        "sovereign_ai": seed_data.get("sovereign_ai_programs", {}),
        "key_events": seed_data.get("key_events_timeline", []),
        "ai_model_milestones": seed_data.get("ai_model_milestones", []),
        "timeseries": timeseries,
        "last_updated": str(datetime.date.today()),
        "as_of_date": config.AS_OF_DATE,
        "web_scraping_enabled": not quick and WEB_ENABLED,
        "event_counts": {
            "total": len(all_events),
            "from_seed": len(events),
            "from_web": len(web_events),
        },
    }

    # Save market state
    os.makedirs(os.path.dirname(config.MARKET_STATE_PATH), exist_ok=True)
    with open(config.MARKET_STATE_PATH, "w") as f:
        json.dump(market_state, f, indent=2)

    print(f"  [DataAgent] Market state saved: {len(all_events)} events")
    print(f"  [DataAgent] Seed events: {len(events)}, Web events: {len(web_events)}")

    return market_state


if __name__ == "__main__":
    result = run(quick=True)
    print(json.dumps(result, indent=2, default=str))
