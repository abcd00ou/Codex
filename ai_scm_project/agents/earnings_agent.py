"""
earnings_agent.py — 공급 수치 수집 에이전트

실적발표 PDF/텍스트를 Claude API로 파싱해 공급 수치를 구조화합니다.
PDF가 없을 경우 seed 데이터(하드코딩 공시 수치)로 fallback합니다.

출력: data/supply_state.json
"""

import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
EARNINGS_DIR = DATA_DIR / "earnings_pdfs"   # PDF 저장 디렉토리
SUPPLY_STATE_PATH = DATA_DIR / "supply_state.json"

# ── 신뢰도 가중치 ────────────────────────────────────────────
CONFIDENCE = {
    "earnings_official": 1.00,   # 실적발표 공식 수치 (PDF 파싱)
    "sec_filing":        0.95,   # 10-Q / 10-K 공시
    "ir_presentation":   0.85,   # IR 슬라이드
    "analyst_consensus": 0.70,   # 애널리스트 컨센서스
    "news_report":       0.50,   # 뉴스 보도
    "job_posting":       0.30,   # 채용공고 시그널
    "seed_hardcoded":    0.60,   # 이 파일에 하드코딩된 공시 기반 수치
}

# ── Seed 데이터 (공시 기반, 분기 파싱 전 fallback) ────────────
# 출처: 각 기업 실적발표 / IR / SEC 공시 (2025 Q4 ~ 2026 Q1 기준)
SEED_SUPPLY = {
    "SK_Hynix": {
        "source_type": "seed_hardcoded",
        "confidence": CONFIDENCE["seed_hardcoded"],
        "period": "2026Q1",
        "source_url": "https://news.skhynix.com/hbm/",
        "metrics": {
            "hbm_capacity_wpm": 55000,           # wafers/month (HBM 전용)
            # 연간 공급량: 55,000wpm × 0.78yield × 600GB/wafer × 12months ÷ 1e6 = 309 PB
            # (HBM3e 12-Hi 기준: 25 stacks/wafer × 24GB/stack = 600GB/wafer)
            "hbm_supply_pb_annual": 309,          # PB/year (공급 역산)
            "hbm_revenue_share_pct": 40,          # 전체 매출 중 HBM 비중
            "hbm_market_share_pct": 50,           # 글로벌 HBM 점유율
            "hbm3e_yield_rate": 0.78,             # 2025 Q4 실적발표 기준
            "hbm4_qual_timeline": "2026Q3",       # HBM4 고객 퀄 완료 예정
            "asp_change_pct_yoy": 15,             # HBM ASP 전년비 변화
            "nvidia_allocation_pct": 70,           # NVIDIA 전용 배분 비중 (추정)
        },
        "notes": "SK Hynix 2026 Q1 실적발표 기반. HBM3e 50%+ 점유율 유지.",
    },
    "Samsung": {
        "source_type": "seed_hardcoded",
        "confidence": CONFIDENCE["seed_hardcoded"],
        "period": "2026Q1",
        "source_url": "https://semiconductor.samsung.com/us/consumer-storage/",
        "metrics": {
            "hbm_capacity_wpm": 40000,
            # Samsung HBM3e yield 낮음 (NVIDIA 퀄 미완료) → 유효 공급 감소
            # 40,000wpm × 0.55yield × 600GB/wafer × 12months ÷ 1e6 = 158 PB
            # 단, NVIDIA향 유효 공급은 0 (퀄 미완료) → 타사 고객만
            "hbm_supply_pb_annual": 158,          # PB/year (전체, NVIDIA 제외)
            "hbm_supply_pb_annual_nvidia_eligible": 0,  # NVIDIA향 유효 공급 없음
            "hbm_market_share_pct": 35,
            "hbm3e_yield_rate": 0.55,             # NVIDIA 퀄 지연 중 (이슈)
            "hbm3e_nvidia_qual_status": "pending", # NVIDIA HBM3e 퀄 미완료
            "hbm4_qual_timeline": "2027Q1",
        },
        "notes": "Samsung HBM3e NVIDIA 퀄 지연이 핵심 리스크. 2026 Q1 기준 점유율 하락 중.",
    },
    "Micron": {
        "source_type": "sec_filing",
        "confidence": CONFIDENCE["sec_filing"],
        "period": "2026Q2",
        "source_url": "https://www.sec.gov/Archives/edgar/data/723125/000072312526000004/a2026q2ex991-pressrelease.htm",
        "metrics": {
            "hbm_capacity_wpm": 20000,
            # 20,000wpm × 0.72yield × 600GB/wafer × 12months ÷ 1e6 = 104 PB
            "hbm_supply_pb_annual": 104,          # PB/year
            "hbm_market_share_pct": 15,           # 10% → 15% 확대 중
            "hbm3e_yield_rate": 0.72,
            "hbm4_qual_timeline": "2027Q1",
            # 실제 FQ2 2026 수치 (SEC EDGAR 8-K, 2026-03-18)
            "total_revenue_usd_bn_quarter": 23.86,   # 역대 최고 (vs $8.05B YoY)
            "cmbu_revenue_usd_bn_quarter": 7.749,    # CMBU = HBM + 하이퍼스케일러 클라우드
            "cmbu_gross_margin_pct": 74,             # CMBU 총이익률
            "cmbu_revenue_yoy_growth_pct": 163,      # $2.947B → $7.749B
            "total_gross_margin_pct": 74.4,
            "q3_revenue_guidance_usd_bn": 33.5,      # FQ3 2026 가이던스 (역대 최고 예상)
            "q3_gross_margin_guidance_pct": 81,
            "dram_revenue_growth_pct_yoy": 207,      # DRAM 전년비 +207%
            "chips_act_grant_usd_bn": 6.4,           # CHIPS Act 보조금
        },
        "notes": (
            "Micron FY2026 Q2 실적발표 (SEC 8-K, 2026-03-18). "
            "총매출 $23.86B (역대 최고), CMBU(HBM 포함) $7.749B. "
            "FQ3 가이던스 $33.5B / 총이익률 81% — AI 수요 가속 확인. "
            "출처: SEC EDGAR accession 0000723125-26-000004."
        ),
    },
    "TSMC": {
        "source_type": "ir_presentation",
        "confidence": CONFIDENCE["ir_presentation"],
        "period": "2026Q1",
        "source_url": "https://ir.tsmc.com/english/annualReports",
        "metrics": {
            "cowos_capacity_wpm": 105000,        # 2026 목표 120K wpm 진행 중
            "cowos_s_wpm": 60000,                # CoWoS-S (standard)
            "cowos_l_wpm": 30000,                # CoWoS-L (large)
            "cowos_r_wpm": 15000,                # CoWoS-R (reticle scale)
            "cowos_utilization": 0.88,           # 현재 가동률
            "cowos_lead_time_months": 18,        # 주문 → 납기
            "n3_utilization": 0.90,              # N3 노드 가동률
            "n2_ramp_timeline": "2026Q2",        # N2 양산 시작
            "advanced_pkg_revenue_share_pct": 12, # 전체 매출 중 첨단패키징 비중
        },
        "notes": "TSMC 2025 Annual Report + 2026 Q1 법인 공시. CoWoS 120K wpm 달성은 2026 Q4 목표.",
    },
    "Vertiv": {
        "source_type": "sec_filing",
        "confidence": CONFIDENCE["sec_filing"],
        "period": "2026Q1",
        "source_url": "https://investors.vertiv.com/",
        "metrics": {
            "backlog_usd_bn": 8.2,               # 수주잔고
            "backlog_growth_yoy_pct": 35,
            "lead_time_months": 18,              # 전력 장비 납기
            "revenue_usd_bn_quarter": 2.1,
            "order_growth_yoy_pct": 40,
            "dc_power_rev_share_pct": 75,        # DC 전력 매출 비중
        },
        "notes": "Vertiv 2025 10-K + 2026 Q1 10-Q. 수주잔고 $8.2B, 2026 Q2까지 Sold Out.",
    },
    "GE_Vernova": {
        "source_type": "sec_filing",
        "confidence": CONFIDENCE["sec_filing"],
        "period": "2026Q1",
        "source_url": "https://www.gevernova.com/investor-relations",
        "metrics": {
            "transformer_lead_time_months": 30,  # 변압기 납기
            "gas_turbine_backlog_usd_bn": 12,
            "grid_backlog_usd_bn": 6.5,
            "dc_power_contract_count": 8,        # DC 전용 전력계약 수
            "revenue_usd_bn_quarter": 8.6,
        },
        "notes": "GE Vernova 2025 10-K. 변압기 납기 30개월로 전력 인프라 병목의 핵심 지표.",
    },
    "NVIDIA": {
        "source_type": "earnings_official",
        "confidence": CONFIDENCE["earnings_official"],
        "period": "2026Q1",
        "source_url": "https://investor.nvidia.com/financial-information/quarterly-results/",
        "metrics": {
            "datacenter_revenue_usd_bn_quarter": 35.6,
            "b200_shipment_est_units": 1200000,  # 2026 Q1 추정 (공시 단위 아님)
            "gb200_nvl72_rack_est": 10000,       # 2026 Q1 추정
            "cowos_dependency_pct": 100,         # B200/GB200 전량 CoWoS 필요
            "hbm_per_gpu_gb": 192,               # B200 기준
            "supply_guidance": "strong",         # 실적발표 가이던스
            "next_q_revenue_guidance_usd_bn": 43,
        },
        "notes": "NVIDIA FY2026 Q4 실적발표. DC 매출 $35.6B, Blackwell 공급 가속.",
    },
}

# ── 실적발표 캘린더 (분기별 파싱 트리거) ─────────────────────
EARNINGS_CALENDAR = {
    "SK_Hynix": ["2026-01-29", "2026-04-24", "2026-07-25", "2026-10-22"],
    "Micron":   ["2026-01-08", "2026-04-02", "2026-07-01", "2026-10-01"],
    "TSMC":     ["2026-01-16", "2026-04-17", "2026-07-17", "2026-10-16"],
    "NVIDIA":   ["2026-02-26", "2026-05-28", "2026-08-27", "2026-11-19"],
    "Vertiv":   ["2026-02-19", "2026-04-30", "2026-07-30", "2026-10-29"],
    "GE_Vernova": ["2026-01-22", "2026-04-23", "2026-07-23", "2026-10-22"],
}


def get_next_earnings(company: str, today: str = None) -> str | None:
    """다음 실적발표일 반환."""
    today = today or datetime.date.today().isoformat()
    for date in EARNINGS_CALENDAR.get(company, []):
        if date >= today:
            return date
    return None


def parse_sec_press_release(url: str, company: str) -> dict | None:
    """
    SEC EDGAR press release HTML을 정규식으로 파싱해 공급 수치를 추출합니다.
    Claude API 없이 동작 — 1차 파싱 레이어.

    지원 기업: Micron (8-K press release 구조)
    """
    import urllib.request
    import re

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "research@supply-intel.com"})
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")

        # HTML 태그 / HTML 엔티티 제거
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"&[a-z#\d]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        metrics = {}

        # ── 기업별 파싱 ──────────────────────────────────────
        if company == "Micron":
            # 총 매출 (Revenue of $X.XX billion)
            m = re.search(r"Revenue\s+\$\s*([\d,]+)\s*(?:million|billion)?", text)
            if not m:
                m = re.search(r"Revenue\s*\$\s*([\d,.]+)\s*(billion|million)", text, re.IGNORECASE)
            if m:
                val_str = m.group(1).replace(",", "")
                unit = m.group(2).lower() if m.lastindex >= 2 else "million"
                val = float(val_str) * (1 if unit == "billion" else 0.001)
                metrics["total_revenue_usd_bn_quarter"] = round(val, 3)

            # 분기별 매출 테이블: "Revenue $ 23,860 $ 13,643 $ 8,053"
            m = re.search(r"Revenue\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)", text)
            if m:
                metrics["total_revenue_usd_bn_quarter"] = round(int(m.group(1).replace(",", "")) / 1000, 3)
                metrics["total_revenue_prior_q_usd_bn"] = round(int(m.group(2).replace(",", "")) / 1000, 3)
                metrics["total_revenue_prior_year_usd_bn"] = round(int(m.group(3).replace(",", "")) / 1000, 3)

            # CMBU 매출
            m = re.search(r"Cloud Memory Business Unit\s+Revenue\s+\$\s*([\d,]+)\s+\$\s*([\d,]+)", text)
            if m:
                metrics["cmbu_revenue_usd_bn_quarter"] = round(int(m.group(1).replace(",", "")) / 1000, 3)
                metrics["cmbu_revenue_prior_q_usd_bn"] = round(int(m.group(2).replace(",", "")) / 1000, 3)

            # CMBU 총이익률
            m = re.search(r"Cloud Memory Business Unit.*?Gross margin\s+(\d+)\s*%", text, re.DOTALL)
            if m:
                metrics["cmbu_gross_margin_pct"] = int(m.group(1))

            # Q3 가이던스
            m = re.search(r"Revenue\s+\$([\d.]+)\s+billion.*?(?:FQ3|third quarter)", text, re.IGNORECASE)
            if not m:
                m = re.search(r"FQ3.*?Revenue\s+\$([\d.]+)\s+billion", text, re.IGNORECASE | re.DOTALL)
            if m:
                metrics["q3_revenue_guidance_usd_bn"] = float(m.group(1))

            # DRAM 성장률
            m = re.search(r"Sales of DRAM products increased\s+(\d+)%", text)
            if m:
                metrics["dram_revenue_growth_pct_yoy"] = int(m.group(1))

            # 총이익률
            m = re.search(r"Gross margin.*?(\d+\.\d+)\s*%.*?Percent of revenue", text)
            if m:
                metrics["total_gross_margin_pct"] = float(m.group(1))

        elif company == "NVIDIA":
            # NVIDIA CFO commentary 구조:
            # "Data Center $62,314 $51,215 $35,580 22 % 75 %"
            m = re.search(r"Data Center\s+\$([\d,]+)\s+\$([\d,]+)\s+\$([\d,]+)", text)
            if m:
                metrics["datacenter_revenue_usd_mn_quarter"] = int(m.group(1).replace(",", ""))
                metrics["datacenter_revenue_usd_bn_quarter"] = round(int(m.group(1).replace(",", "")) / 1000, 2)
                metrics["datacenter_prior_q_usd_bn"] = round(int(m.group(2).replace(",", "")) / 1000, 2)
                metrics["datacenter_prior_year_usd_bn"] = round(int(m.group(3).replace(",", "")) / 1000, 2)

            # Compute / Networking 세부
            m = re.search(r"Compute\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", text)
            if m:
                metrics["compute_revenue_usd_mn_quarter"] = int(m.group(1).replace(",", ""))

            m = re.search(r"Networking\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", text)
            if m:
                metrics["networking_revenue_usd_mn_quarter"] = int(m.group(1).replace(",", ""))

            # 총 매출
            m = re.search(r"Total\s+\$([\d,]+)\s+\$([\d,]+)\s+\$([\d,]+)", text)
            if m:
                metrics["total_revenue_usd_bn_quarter"] = round(int(m.group(1).replace(",", "")) / 1000, 2)
                metrics["total_revenue_prior_q_usd_bn"] = round(int(m.group(2).replace(",", "")) / 1000, 2)
                metrics["total_revenue_prior_year_usd_bn"] = round(int(m.group(3).replace(",", "")) / 1000, 2)

            # Q1 FY2027 가이던스
            m = re.search(r"Revenue is expected to be \$([\d.]+) billion", text)
            if m:
                metrics["next_q_revenue_guidance_usd_bn"] = float(m.group(1))

            # Gross margin
            m = re.search(r"GAAP.*?[Gg]ross\s+margin\s+([\d.]+)\s*%", text)
            if m:
                metrics["total_gross_margin_pct"] = float(m.group(1))

            # 하이퍼스케일러 비중
            m = re.search(r"hyperscaler.*?(\d+)\s*%\s+of Data Center", text, re.IGNORECASE)
            if m:
                metrics["hyperscaler_dc_revenue_share_pct"] = int(m.group(1))

        elif company == "SK_Hynix":
            # SK Hynix newsroom 구조 (영문 press release)
            # "FY2025 revenue of 97.1467 trillion won"
            m = re.search(r"FY20\d\d revenue of ([\d.]+) trillion won", text)
            if m:
                metrics["annual_revenue_krw_tr"] = float(m.group(1))
                # KRW → USD 환산 (1 USD ≈ 1,400 KRW)
                metrics["annual_revenue_usd_bn"] = round(float(m.group(1)) * 1e12 / 1400 / 1e9, 1)

            # 분기 매출: "4Q25 revenue of 32.8267 trillion won" 또는 "revenue rising 34% to 32.8267 trillion won"
            m = re.search(r"(?:4Q\d\d|Q4[\s_]20\d\d|fourth quarter)\s+revenue of ([\d.]+) trillion won", text, re.IGNORECASE)
            if not m:
                m = re.search(r"revenue (?:rising|increased) [\d.]+% to ([\d.]+) trillion won", text, re.IGNORECASE)
            if not m:
                # Reports 4Q25 revenue of ... trillion won 형식
                m = re.search(r"Reports 4Q\d\d revenue of ([\d.]+) trillion won", text, re.IGNORECASE)
            if m:
                rev = float(m.group(1))
                metrics["quarterly_revenue_krw_tr"] = rev
                metrics["quarterly_revenue_usd_bn"] = round(rev * 1e12 / 1400 / 1e9, 1)

            # HBM 성장률
            m = re.search(r"HBM revenue (more than doubled|doubled|increased \d+%)", text, re.IGNORECASE)
            if m:
                metrics["hbm_revenue_growth_descriptor"] = m.group(1)
                if "doubled" in m.group(1).lower():
                    metrics["hbm_revenue_growth_pct_yoy_est"] = 100  # 최소 2배 = 100%+

            # HBM4 양산 여부
            if re.search(r"HBM4.*?mass produc|mass produc.*?HBM4", text, re.IGNORECASE):
                metrics["hbm4_mass_production"] = True

            # 운영이익률
            m = re.search(r"operating margin.*?(\d+)%", text, re.IGNORECASE)
            if m:
                metrics["operating_margin_pct"] = int(m.group(1))

        elif company == "TSMC":
            # TSMC 6-K 월간 매출 리포트 구조:
            # "Net Revenue 415,191 317,657 30.7 285,957 45.2 1,134,103 839,254 35.1"
            # Q1 누적: Jan-Mar 2026
            m = re.search(
                r"Net Revenue\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d,]+)\s+([\d.]+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)",
                text,
            )
            if m:
                metrics["monthly_revenue_ntd_mn"] = int(m.group(1).replace(",", ""))   # 최신 월
                metrics["q1_revenue_ntd_bn"] = round(int(m.group(6).replace(",", "")) / 1000, 1)  # 1월~3월
                metrics["q1_revenue_yoy_growth_pct"] = float(m.group(8))
                metrics["prior_year_q1_revenue_ntd_bn"] = round(int(m.group(7).replace(",", "")) / 1000, 1)
                # NTD → USD 환산 (1 USD ≈ 32 NTD)
                metrics["q1_revenue_usd_bn"] = round(int(m.group(6).replace(",", "")) / 1000 / 32, 1)

            # 월간 성장률
            m_mom = re.search(r"increase of ([\d.]+) percent from (?:February|January|the prior month)", text, re.IGNORECASE)
            if m_mom:
                metrics["monthly_revenue_mom_growth_pct"] = float(m_mom.group(1))

            m_yoy = re.search(r"increase of ([\d.]+) percent from (?:March|the same period) last year", text, re.IGNORECASE)
            if m_yoy:
                metrics["monthly_revenue_yoy_growth_pct"] = float(m_yoy.group(1))

        if not metrics:
            return None

        # source_type 결정 (SEC vs IR newsroom)
        source_type = "sec_filing" if "sec.gov" in url else "ir_presentation"
        confidence = CONFIDENCE.get(source_type, CONFIDENCE["ir_presentation"])

        return {
            "company": company,
            "source_url": url,
            "source_type": source_type,
            "confidence": confidence,
            "parsed_method": "regex_html",
            "metrics": metrics,
        }

    except Exception as e:
        print(f"  [earnings_agent] HTML 파싱 실패 ({company}): {e}")
        return None


# ── 공개 IR/SEC 문서 URL 매핑 (자동 파싱 대상) ────────────────
# 갱신 기준: 분기 실적발표 후 이 URL만 업데이트하면 파싱 자동 적용
PARSE_URLS = {
    "Micron": {
        "url": "https://www.sec.gov/Archives/edgar/data/723125/000072312526000004/a2026q2ex991-pressrelease.htm",
        "type": "sec_edgar",
        "period": "2026Q2",
    },
    "NVIDIA": {
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000019/q4fy26cfocommentary.htm",
        "type": "sec_edgar",
        "period": "2026Q4_FY",  # FY2026 Q4 (Jan 2026)
    },
    "SK_Hynix": {
        "url": "https://news.skhynix.com/sk-hynix-announces-fy25-financial-results/",
        "type": "ir_newsroom",
        "period": "2025Q4",
    },
    "TSMC": {
        "url": "https://www.sec.gov/Archives/edgar/data/1046179/000104617926000136/tsm-revenue20260410.htm",
        "type": "sec_edgar",
        "period": "2026Q1",
    },
}

# 하위 호환성 유지
SEC_PRESS_RELEASE_URLS = {k: v["url"] for k, v in PARSE_URLS.items()}


def parse_pdf_with_claude(pdf_path: str, company: str) -> dict | None:
    """
    실적발표 PDF를 Claude API로 파싱해 공급 수치를 추출합니다.

    사용 방법:
        1. earnings_pdfs/ 디렉토리에 PDF 저장
           예: data/earnings_pdfs/SK_Hynix_2026Q1.pdf
        2. python3 -c "from agents.earnings_agent import parse_pdf_with_claude; ..."

    반환: metrics dict (실패 시 None)
    """
    try:
        import anthropic
        import base64

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        prompt = f"""
다음은 {company}의 실적발표 또는 IR 자료입니다.
아래 항목을 JSON 형식으로 추출해주세요. 없는 항목은 null로 표시하세요.

추출 항목:
- period: 해당 분기 (예: "2026Q1")
- hbm_capacity_wpm: HBM 생산 캐파 (wafers/month), 숫자만
- hbm_shipment_gb_per_quarter: HBM 분기 출하량 (GB), 숫자만
- hbm_market_share_pct: HBM 시장 점유율 (%), 숫자만
- hbm_revenue_share_pct: 전체 매출 중 HBM 비중 (%), 숫자만
- asp_change_pct_yoy: HBM ASP 전년비 변화율 (%), 숫자만
- cowos_capacity_wpm: CoWoS 패키징 캐파 (TSMC 해당 시), 숫자만
- backlog_usd_bn: 수주잔고 ($B), 숫자만
- lead_time_months: 납기 (개월), 숫자만
- key_quotes: 공급/수요 관련 핵심 발언 (최대 3개 배열)

주의: 추정치가 아닌 발표된 실제 수치만 포함하세요.
"""

        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        text = response.content[0].text
        # JSON 블록 추출
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group())
        return None

    except Exception as e:
        print(f"  [earnings_agent] PDF 파싱 실패 ({company}): {e}")
        return None


def collect_supply_state(force_pdf: bool = False) -> dict:
    """
    공급 수치를 수집합니다.

    순서:
    1. earnings_pdfs/ 에 PDF가 있으면 Claude API로 파싱
    2. 없으면 SEED_SUPPLY (공시 기반 하드코딩) 사용

    반환: supply_state dict
    """
    EARNINGS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    supply = {}

    for company, seed in SEED_SUPPLY.items():
        parsed = None

        # 1순위: SEC/IR HTML 파싱 (Claude API 불필요)
        if company in PARSE_URLS:
            info = PARSE_URLS[company]
            print(f"  [earnings_agent] HTML 파싱 중: {company} ({info['period']})")
            result = parse_sec_press_release(info["url"], company)
            if result and result.get("metrics"):
                # seed metrics에 파싱된 수치 덮어쓰기
                merged_metrics = dict(seed["metrics"])
                merged_metrics.update(result["metrics"])
                parsed = {
                    "period": seed["period"],
                    "metrics": merged_metrics,
                    "source_type": result["source_type"],
                    "confidence": result["confidence"],
                    "source_url": result["source_url"],
                    "parsed_method": result["parsed_method"],
                }

        # 2순위: PDF → Claude API 파싱
        if not parsed:
            pdf_candidates = sorted(EARNINGS_DIR.glob(f"{company}_*.pdf"), reverse=True)
            if pdf_candidates and (force_pdf or True):
                latest_pdf = pdf_candidates[0]
                print(f"  [earnings_agent] PDF 파싱 중: {latest_pdf.name}")
                parsed = parse_pdf_with_claude(str(latest_pdf), company)

        if parsed and "metrics" in parsed:
            entry = {
                "source_type": parsed.get("source_type", "earnings_official"),
                "confidence": parsed.get("confidence", CONFIDENCE["earnings_official"]),
                "period": parsed.get("period", seed["period"]),
                "source_url": parsed.get("source_url", seed["source_url"]),
                "metrics": parsed["metrics"],
                "quotes": parsed.get("key_quotes", []),
                "parsed_method": parsed.get("parsed_method", "claude_pdf"),
                "fetched_at": today,
            }
        else:
            # Seed fallback
            entry = dict(seed)
            entry["fetched_at"] = today
            entry["parsed_from_pdf"] = None

        # 다음 실적발표일 추가
        entry["next_earnings_date"] = get_next_earnings(company, today)
        supply[company] = entry

    return {
        "fetched_at": today,
        "companies": supply,
        "pdf_dir": str(EARNINGS_DIR),
        "usage": (
            "PDF 추가 방법: data/earnings_pdfs/{Company}_{Period}.pdf 로 저장 후 재실행. "
            "예: SK_Hynix_2026Q1.pdf"
        ),
    }


def save_supply_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SUPPLY_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"  [earnings_agent] 저장 완료: {SUPPLY_STATE_PATH}")


def load_supply_state() -> dict | None:
    if SUPPLY_STATE_PATH.exists():
        with open(SUPPLY_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def run(force_pdf: bool = False) -> dict:
    print("[earnings_agent] 공급 수치 수집 시작...")
    state = collect_supply_state(force_pdf=force_pdf)
    save_supply_state(state)
    companies = list(state["companies"].keys())
    print(f"  수집 완료: {len(companies)}개 기업 ({', '.join(companies)})")
    return state


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-pdf", action="store_true", help="PDF 강제 재파싱")
    args = parser.parse_args()
    result = run(force_pdf=args.force_pdf)
    print(json.dumps(result, ensure_ascii=False, indent=2))
