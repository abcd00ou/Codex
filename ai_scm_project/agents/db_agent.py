"""
DB Agent — PostgreSQL ai_scm 데이터베이스 연동
psycopg2 없거나 DB 연결 실패 시 조용히 fallback
시계열 분석을 위한 확장 테이블 포함
"""
import os, sys, json
from datetime import date

try:
    import psycopg2
    import psycopg2.extras
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

DB_URL = os.environ.get("AI_SCM_DB", "postgresql://localhost:5432/ai_scm")

DDL = """
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    layer VARCHAR(50),
    tier INTEGER,
    market_cap_billion FLOAT,
    description_ko TEXT,
    source_url TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS supply_chain_edges (
    id SERIAL PRIMARY KEY,
    from_company VARCHAR(100),
    to_company VARCHAR(100),
    relationship_type VARCHAR(50),
    description_ko TEXT,
    value_str VARCHAR(100),
    source_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS market_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    company VARCHAR(100),
    value_usd FLOAT,
    year INTEGER,
    description_ko TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS bottleneck_scores (
    id SERIAL PRIMARY KEY,
    layer VARCHAR(50),
    utilization_pct FLOAT,
    severity VARCHAR(20),
    description_ko TEXT,
    resolution_months INTEGER,
    run_date DATE DEFAULT CURRENT_DATE
);
CREATE TABLE IF NOT EXISTS investment_signals (
    id SERIAL PRIMARY KEY,
    company VARCHAR(100),
    layer VARCHAR(50),
    signal VARCHAR(30),
    thesis_ko TEXT,
    catalyst_ko TEXT,
    risk_ko TEXT,
    timeframe VARCHAR(50),
    source_url TEXT,
    run_date DATE DEFAULT CURRENT_DATE
);
CREATE TABLE IF NOT EXISTS model_results (
    id SERIAL PRIMARY KEY,
    scenario VARCHAR(20),
    year INTEGER,
    metric VARCHAR(50),
    value FLOAT,
    unit VARCHAR(20),
    run_date DATE DEFAULT CURRENT_DATE
);
CREATE TABLE IF NOT EXISTS hyperscaler_capex (
    id SERIAL PRIMARY KEY,
    company VARCHAR(100),
    year INTEGER,
    value_billion FLOAT,
    data_type VARCHAR(20),
    source_url TEXT,
    UNIQUE(company, year)
);
CREATE TABLE IF NOT EXISTS hyperscaler_capex_quarterly (
    id SERIAL PRIMARY KEY,
    company VARCHAR(10),
    quarter VARCHAR(10),
    value_billion FLOAT,
    UNIQUE(company, quarter)
);
CREATE TABLE IF NOT EXISTS network_nodes (
    id SERIAL PRIMARY KEY,
    company VARCHAR(100),
    layer VARCHAR(50),
    market_cap_billion FLOAT,
    tier INTEGER,
    run_date DATE DEFAULT CURRENT_DATE
);
CREATE TABLE IF NOT EXISTS network_edges (
    id SERIAL PRIMARY KEY,
    from_company VARCHAR(100),
    to_company VARCHAR(100),
    relationship_type VARCHAR(50),
    description_ko TEXT,
    value_str VARCHAR(100),
    source_url TEXT,
    run_date DATE DEFAULT CURRENT_DATE
);
-- 시계열 분석용 신규 테이블
CREATE TABLE IF NOT EXISTS nvidia_revenue_quarterly (
    id SERIAL PRIMARY KEY,
    quarter VARCHAR(10) UNIQUE NOT NULL,
    datacenter_usd_bn FLOAT,
    total_usd_bn FLOAT,
    yoy_growth_pct FLOAT,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS gpu_shipments_annual (
    id SERIAL PRIMARY KEY,
    gpu_model VARCHAR(50),
    year INTEGER,
    units INTEGER,
    data_type VARCHAR(20),
    source VARCHAR(100),
    UNIQUE(gpu_model, year)
);
CREATE TABLE IF NOT EXISTS hbm_market_annual (
    id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,
    market_size_usd_bn FLOAT,
    sk_hynix_share FLOAT,
    samsung_share FLOAT,
    micron_share FLOAT,
    data_type VARCHAR(20),
    source VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product VARCHAR(50),
    quarter VARCHAR(10),
    price_usd FLOAT,
    unit VARCHAR(50),
    source VARCHAR(100),
    UNIQUE(product, quarter)
);
CREATE TABLE IF NOT EXISTS capacity_utilization_timeseries (
    id SERIAL PRIMARY KEY,
    layer VARCHAR(50),
    quarter VARCHAR(10),
    utilization_pct FLOAT,
    source VARCHAR(100),
    UNIQUE(layer, quarter)
);
CREATE TABLE IF NOT EXISTS ai_model_timeline (
    id SERIAL PRIMARY KEY,
    release_date DATE,
    model_name VARCHAR(100),
    organization VARCHAR(100),
    parameter_count BIGINT,
    significance_ko TEXT,
    hardware_impact VARCHAR(200),
    source VARCHAR(200),
    UNIQUE(model_name, organization)
);
CREATE TABLE IF NOT EXISTS dc_power_annual (
    id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,
    global_gw FLOAT,
    ai_fraction FLOAT,
    data_type VARCHAR(20),
    source VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS token_demand_annual (
    id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,
    total_tokens_per_day BIGINT,
    data_type VARCHAR(20),
    notes TEXT,
    source VARCHAR(200)
);
"""


def _connect():
    if not DB_AVAILABLE:
        return None
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception:
        return None


def init_db():
    conn = _connect()
    if not conn:
        print("  [DB] PostgreSQL 연결 불가 — 파일 기반으로 fallback")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(DDL)
        conn.commit()
        conn.close()
        print("  [DB] ai_scm DB 초기화 완료 (시계열 테이블 포함)")
        return True
    except Exception as e:
        print(f"  [DB] 초기화 실패: {e}")
        conn.close()
        return False


def load_historical_data(conn):
    """seed_data.json의 과거 시계열 데이터를 DB에 bulk insert."""
    import os
    seed_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "seed_data.json"
    )
    try:
        with open(seed_path) as f:
            seed = json.load(f)
    except Exception as e:
        print(f"  [DB] seed_data.json 로드 실패: {e}")
        return False

    today = date.today()
    loaded = 0

    with conn.cursor() as cur:
        # NVIDIA 분기 매출
        for qtr, val in seed.get("nvidia_datacenter_revenue_quarterly_usd_bn", {}).items():
            if qtr.startswith("_"):
                continue
            total = seed.get("nvidia_total_revenue_quarterly_usd_bn", {}).get(qtr)
            cur.execute("""
                INSERT INTO nvidia_revenue_quarterly
                (quarter, datacenter_usd_bn, total_usd_bn, source)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (quarter) DO UPDATE SET
                    datacenter_usd_bn=EXCLUDED.datacenter_usd_bn,
                    total_usd_bn=EXCLUDED.total_usd_bn
            """, (qtr, val, total, "NVIDIA quarterly 10-Q"))
            loaded += 1

        # 하이퍼스케일러 분기 CapEx
        for company, qtrs in seed.get("hyperscaler_capex_quarterly_usd_bn", {}).items():
            if company.startswith("_"):
                continue
            for qtr, val in qtrs.items():
                cur.execute("""
                    INSERT INTO hyperscaler_capex_quarterly (company, quarter, value_billion)
                    VALUES (%s,%s,%s)
                    ON CONFLICT (company, quarter) DO UPDATE SET value_billion=EXCLUDED.value_billion
                """, (company, qtr, val))
                loaded += 1

        # GPU 출하 연간
        for model, years in seed.get("gpu_shipments", {}).items():
            if model.startswith("_"):
                continue
            for yr, units in years.items():
                dtype = "estimate" if yr.endswith("E") else "actual"
                yr_int = int(yr.replace("E", ""))
                cur.execute("""
                    INSERT INTO gpu_shipments_annual (gpu_model, year, units, data_type, source)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT (gpu_model, year) DO UPDATE SET units=EXCLUDED.units
                """, (model, yr_int, units, dtype, "IDC/JPMorgan analyst estimates"))
                loaded += 1

        # HBM 시장 연간
        hbm = seed.get("hbm_market", {})
        for yr, size in hbm.get("market_size_usd_bn", {}).items():
            if yr.startswith("_"):
                continue
            dtype = "estimate" if yr.endswith("E") else "actual"
            yr_int = int(yr.replace("E", ""))
            share = hbm.get("market_share_annual", {}).get(yr, {})
            cur.execute("""
                INSERT INTO hbm_market_annual
                (year, market_size_usd_bn, sk_hynix_share, samsung_share, micron_share, data_type, source)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (year) DO UPDATE SET
                    market_size_usd_bn=EXCLUDED.market_size_usd_bn,
                    sk_hynix_share=EXCLUDED.sk_hynix_share
            """, (yr_int, size,
                  share.get("SK_Hynix"), share.get("Samsung"), share.get("Micron"),
                  dtype, "Omdia HBM Market Report 2024"))
            loaded += 1

        # DRAM/NAND 가격 시계열
        for qtr, price in seed.get("dram_price_index", {}).get("DDR4_8Gb_spot_usd", {}).items():
            cur.execute("""
                INSERT INTO price_history (product, quarter, price_usd, unit, source)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (product, quarter) DO UPDATE SET price_usd=EXCLUDED.price_usd
            """, ("DDR4_8Gb", qtr, price, "USD/chip", "TrendForce DRAM"))
            loaded += 1

        for qtr, price in seed.get("nand_price_index", {}).get("MLC_128Gb_spot_usd", {}).items():
            cur.execute("""
                INSERT INTO price_history (product, quarter, price_usd, unit, source)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (product, quarter) DO UPDATE SET price_usd=EXCLUDED.price_usd
            """, ("NAND_MLC_128Gb", qtr, price, "USD/chip", "TrendForce NAND"))
            loaded += 1

        # 가동률 시계열
        for layer, qtrs in seed.get("capacity_utilization_time_series", {}).items():
            if layer.startswith("_"):
                continue
            for qtr, util in qtrs.items():
                cur.execute("""
                    INSERT INTO capacity_utilization_timeseries (layer, quarter, utilization_pct, source)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (layer, quarter) DO UPDATE SET utilization_pct=EXCLUDED.utilization_pct
                """, (layer, qtr, util * 100, "AI SCM internal model"))
                loaded += 1

        # AI 모델 마일스톤
        for m in seed.get("ai_model_milestones", []):
            try:
                rel_date = m["date"] + "-01" if len(m["date"]) == 7 else m["date"]
                params = m.get("params", m.get("params_est", 0))
                cur.execute("""
                    INSERT INTO ai_model_timeline
                    (release_date, model_name, organization, parameter_count, significance_ko, source)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (model_name, organization) DO UPDATE SET
                        significance_ko=EXCLUDED.significance_ko
                """, (rel_date, m["model"], m["org"], params or 0,
                      m.get("significance", ""), "public announcements"))
                loaded += 1
            except Exception:
                pass

        # DC 전력 연간
        for yr, gw in seed.get("datacenter_power", {}).get("global_gw", {}).items():
            if yr.startswith("_"):
                continue
            dtype = "estimate" if yr.endswith("E") else "actual"
            yr_int = int(yr.replace("E", ""))
            ai_frac = seed.get("datacenter_power", {}).get("ai_workload_fraction", {})
            ai_f = ai_frac.get(yr) if isinstance(ai_frac, dict) else None
            cur.execute("""
                INSERT INTO dc_power_annual (year, global_gw, ai_fraction, data_type, source)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (year) DO UPDATE SET global_gw=EXCLUDED.global_gw
            """, (yr_int, gw, ai_f, dtype, "IEA Electricity 2024"))
            loaded += 1

        # 토큰 수요 연간
        for yr_key, total in seed.get("token_demand_annual_estimates", {}).items():
            if yr_key.startswith("_"):
                continue
            yr_str = yr_key.split("_")[0]
            if not yr_str.isdigit():
                continue
            dtype = "base_estimate"
            if "actual" in yr_key or int(yr_str) <= 2025:
                dtype = "actual_estimate"
            cur.execute("""
                INSERT INTO token_demand_annual (year, total_tokens_per_day, data_type, source)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (year) DO UPDATE SET total_tokens_per_day=EXCLUDED.total_tokens_per_day
            """, (int(yr_str), int(total), dtype, "Sequoia Capital AI Infra 2024; analyst estimates"))
            loaded += 1

    return loaded


def save_all(mapping_result=None, modeling_result=None,
             bottleneck_result=None, strategy_result=None):
    conn = _connect()
    if not conn:
        return False
    today = date.today()
    try:
        with conn.cursor() as cur:
            # 회사 정보 upsert
            if mapping_result and "company_map" in mapping_result:
                for name, info in mapping_result["company_map"].items():
                    cur.execute("""
                        INSERT INTO companies (name, layer, tier, updated_at)
                        VALUES (%s,%s,%s,NOW())
                        ON CONFLICT (name) DO UPDATE SET layer=EXCLUDED.layer, updated_at=NOW()
                    """, (name, info.get("layer",""), info.get("tier",0)))

            # 네트워크 노드/엣지
            if mapping_result and "network_graph" in mapping_result:
                ng = mapping_result["network_graph"]
                for node in ng.get("nodes", []):
                    cur.execute("""
                        INSERT INTO network_nodes (company, layer, market_cap_billion, tier, run_date)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (node["id"], node.get("layer",""), node.get("market_cap_b",0), 0, today))
                for edge in ng.get("edges", []):
                    cur.execute("""
                        INSERT INTO network_edges
                        (from_company, to_company, relationship_type, description_ko, value_str, source_url, run_date)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (edge["source"], edge["target"], edge["type"],
                          edge.get("description",""), edge.get("value",""),
                          edge.get("source_url",""), today))

            # 병목 스코어
            if bottleneck_result and "all_scores" in bottleneck_result:
                for layer, info in bottleneck_result["all_scores"].items():
                    cur.execute("""
                        INSERT INTO bottleneck_scores
                        (layer, utilization_pct, severity, description_ko, resolution_months, run_date)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (layer, info.get("utilization",0)*100,
                          info.get("severity",""), info.get("resolution_reason",""),
                          info.get("resolution_months", 0), today))

            # 투자 시그널
            if strategy_result:
                for sig in strategy_result.get("investment_signals", []):
                    cur.execute("""
                        INSERT INTO investment_signals
                        (company, layer, signal, thesis_ko, catalyst_ko, risk_ko, timeframe, run_date)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (sig.get("company",""), sig.get("layer",""),
                          sig.get("signal",""), sig.get("thesis",""),
                          sig.get("catalyst",""), sig.get("risk",""),
                          sig.get("timeframe",""), today))

            # CapEx 데이터 (config + seed)
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import config
            for company, years in config.HYPERSCALER_CAPEX.items():
                for yr, val in years.items():
                    year_int = int(yr.replace("_est",""))
                    dtype = "estimate" if "est" in yr else "actual"
                    url = config.REFERENCE_URLS.get(f"{company}_CapEx", "")
                    cur.execute("""
                        INSERT INTO hyperscaler_capex (company, year, value_billion, data_type, source_url)
                        VALUES (%s,%s,%s,%s,%s)
                        ON CONFLICT (company, year) DO UPDATE SET value_billion=EXCLUDED.value_billion
                    """, (company, year_int, val, dtype, url))

            # 모델 결과 (scenario_table)
            if modeling_result:
                scenario_tbl = modeling_result.get("scenario_table", {})
                for scenario, years_data in scenario_tbl.items():
                    for year, metrics in years_data.items():
                        if not isinstance(metrics, dict):
                            continue
                        for metric, value in metrics.items():
                            if isinstance(value, (int, float)):
                                cur.execute("""
                                    INSERT INTO model_results (scenario, year, metric, value, unit, run_date)
                                    VALUES (%s,%s,%s,%s,%s,%s)
                                """, (scenario, int(year), metric, float(value), "", today))

        conn.commit()

        # 과거 시계열 데이터 bulk insert
        hist_count = load_historical_data(conn)
        conn.commit()
        conn.close()
        print(f"  [DB] 모든 데이터 저장 완료 (과거 시계열 {hist_count}건)")
        return True
    except Exception as e:
        print(f"  [DB] 저장 실패: {e}")
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return False


def run():
    """DB 초기화 및 상태 반환"""
    ok = init_db()
    return {"db_available": ok, "db_url": DB_URL if ok else "unavailable"}
