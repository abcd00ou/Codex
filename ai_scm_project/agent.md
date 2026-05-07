# AI 공급망 인텔리전스 시스템 (AI SCM)

## 프로젝트 개요

AI 공급망 인텔리전스 시스템은 두 가지 축으로 구성됩니다:

1. **Intelligence Pipeline** — 토큰 수요 → 하드웨어 수요 정량화 + 병목 탐지 + 투자 시그널
2. **Daily Learning System** — 매일 2회 이메일 (아침: 학습 브리핑 / 저녁: 퀴즈 + 뉴스)

**Daily 학습 도구 실행**
```bash
cd /Users/idongseong/Documents/New project/ai_scm_project
python3 run_daily.py --status           # 학습 진도 확인
python3 run_daily.py --morning          # 아침 이메일 발송
python3 run_daily.py --evening          # 저녁 퀴즈 이메일 발송
python3 run_daily.py --morning --dry-run  # HTML 미리보기
python3 run_daily.py --preview morning  # 브라우저 미리보기
```

**Daily Crontab 설정**
```bash
# crontab -e
0 7  * * * cd /Users/idongseong/Documents/New project/ai_scm_project && python3 run_daily.py --morning >> /tmp/ai_scm_morning.log 2>&1
0 20 * * * cd /Users/idongseong/Documents/New project/ai_scm_project && python3 run_daily.py --evening >> /tmp/ai_scm_evening.log 2>&1
```

**Intelligence Pipeline 실행**
```bash
cd /Users/idongseong/Documents/New project/ai_scm_project
python3 run.py --quick        # 빠른 실행 (SEC/IR 파싱 포함)
python3 run.py                # 전체 실행 (웹 스크래핑 포함)
python3 run.py --report-only  # 마지막 결과로 리포트 재생성
python3 run.py --db-only      # DB 저장만 실행
python3 run.py --skip-supply  # Supply-Demand Engine 건너뜀
```

**Supply-Demand Intelligence Engine 단독 실행**
```bash
python3 -m agents.earnings_agent   # 공급 수치 수집 → data/supply_state.json
python3 -m agents.demand_mapper    # 수요 역산 → data/demand_state.json
python3 -m agents.gap_engine       # 수급갭 분석 → data/gap_report.json
```

**분기 실적발표 후 URL 업데이트** (agents/earnings_agent.py 상단 `PARSE_URLS`):
```python
PARSE_URLS = {
    "Micron":   {"url": "...", "period": "2026Q3"},  # ← 새 8-K URL로 교체
    "NVIDIA":   {"url": "...", "period": "2027Q1_FY"},
    "SK_Hynix": {"url": "...", "period": "2026Q1"},
    "TSMC":     {"url": "...", "period": "2026Q2"},
}
```

## Daily 학습 시스템 구성 (agents/daily/)

| 에이전트 | 파일 | 역할 | 출력 |
|---------|------|------|------|
| Progress | agents/daily/progress_agent.py | 진도 추적 (24일 × 3라운드), 퀴즈 스코어 관리 | progress_state.json |
| News | agents/daily/news_agent.py | AI SCM 뉴스 수집 (RSS 5개 소스 + seed fallback) | news list |
| Content | agents/daily/content_agent.py | Claude API로 학습 브리핑 + 퀴즈 동적 생성 | HTML 콘텐츠 |
| Morning | agents/daily/morning_agent.py | 아침 이메일 (학습 브리핑 + 뉴스 + 병목 현황) | Gmail HTML |
| Evening | agents/daily/evening_agent.py | 저녁 이메일 (퀴즈 3문항 + 뉴스 요약 + 내일 예고) | Gmail HTML |

**Daily 학습 플로우**
```
아침 7시: NewsAgent → ContentAgent(Claude API) → MorningAgent → Gmail
저녁 8시: ContentAgent(퀴즈) → NewsAgent → EveningAgent → Gmail
상태 추적: ProgressAgent → progress_state.json
```

**8개 커리큘럼 × 3라운드 = 24일**
| Round | 레벨 | 내용 |
|-------|------|------|
| 1 | Lv.1 기초 | 개념·용어·시장 구조 (마케터 입문) |
| 2 | Lv.2 심화 | 정량 모델·케이스 스터디·메커니즘 |
| 3 | Lv.3 전문가 | 최신 트렌드·투자 리포트·시나리오 분석 |

## Intelligence Pipeline 에이전트 구성 (11 Steps)

**Supply-Demand Intelligence Engine** (공시 기반 수급갭 분석 — 2026-04 추가)

| Step | 에이전트 | 파일 | 역할 | 출력 | 신뢰도 |
|------|---------|------|------|------|--------|
| 4 | Earnings | agents/earnings_agent.py | SEC/IR HTML 파싱 → 공급 수치 수집 | supply_state.json | 0.85~0.95 |
| 5 | Demand Mapper | agents/demand_mapper.py | CapEx 역산 → 고객군(Tier 1~4) 수요 계산 | demand_state.json | 0.35~0.75 |
| 6 | Gap Engine | agents/gap_engine.py | 수급갭 · 우선순위 · cascade · 기회 분석 | gap_report.json | — |

**파싱 지원 기업 (Claude API 없이 동작):**
| 기업 | 출처 | 기간 | 핵심 지표 |
|------|------|------|----------|
| Micron | SEC 8-K press release | 2026Q2 | 총매출 $23.86B, CMBU $7.75B, Q3 가이던스 $33.5B |
| NVIDIA | SEC 8-K CFO commentary | 2026Q4 FY | DC $62.3B, Compute $51.3B, Q1 FY27 가이던스 $78B |
| SK Hynix | IR newsroom (영문) | 2025Q4 | 분기 KRW 32.8조, HBM 매출 2배+, HBM4 양산 중 |
| TSMC | SEC 6-K 월간매출 | 2026Q1 | Q1 누적 NT$1,134B (+35.1% YoY) |

**기존 에이전트:**

| Step | 에이전트 | 파일 | 역할 | 출력 |
|------|---------|------|------|------|
| 1 | Data | agents/data_agent.py | 시장 데이터 수집 (Reuters 스크래핑 + seed fallback) | market_state.json |
| 2 | Mapping | agents/mapping_agent.py | 61개 회사 → 14개 레이어 매핑 + 투자 네트워크 그래프 | company_map + network_graph |
| 3 | Modeling | agents/modeling_agent.py | Token→GPU→HBM→Power 정량 모델 (3개 시나리오) | scenarios (2025-2028) |
| 7 | Bottleneck | agents/bottleneck_agent.py | gap_report 연동 → 레이어별 가동률, cascade 예측 | bottleneck + timeline |
| 8 | Strategy | agents/strategy_agent.py | 투자 시그널 10개, Phase 로드맵, 리스크 분석 | investment_signals |
| 9 | DB | agents/db_agent.py | PostgreSQL ai_scm DB 저장 (psycopg2 fallback) | DB 저장 |
| 10 | Report | agents/report_agent.py | HTML 대시보드 (D3.js 네트워크 그래프 포함) + PPT 8슬라이드 | HTML + PPTX |
| 11 | Word | agents/word_agent.py | 한국어 학습용 Word 문서 | DOCX |

## 파이프라인 흐름

```
Data → Mapping → Modeling
                         ↓
                 [Supply-Demand Intelligence Engine]
                 Earnings (SEC/IR 파싱)
                         ↓
                 Demand Mapper (CapEx 역산)
                         ↓
                 Gap Engine (수급갭 + cascade)
                         ↓
Bottleneck (gap_report 자동 연동) → Strategy → DB → Report(HTML+PPT) + Word
```

**신뢰도 체계:**
```
earnings_official (1.00) → sec_filing (0.95) → ir_presentation (0.85)
→ analyst_consensus (0.70) → news_report (0.50) → seed_hardcoded (0.60)
```

## 핵심 분석 수식

| 수식 | 공식 |
|------|------|
| Token → GPU | GPU = Tokens/day ÷ (tokens/sec × 가동률) |
| GPU → HBM | HBM(GB) = GPU 수 × GPU당 HBM |
| 메모리 압력 | KV Cache = 컨텍스트 × 사용자 × 2B × 2 |
| SSD 수요 | SSD = RAG 토큰 × 바이트/토큰 |
| 전력 수요 | MW = GPU × TDP × 1.3 × PUE ÷ 10⁶ |

## 2026년 Q1 현재 분석 결과 (기준일: 2026-04-11, 공시 기반)

**수급갭 분석 (gap_engine 기준):**
| 레이어 | 공급 | 수요 | gap_ratio | 상태 | 공급 신뢰도 |
|--------|------|------|-----------|------|------------|
| HBM | 571 PB/yr | 1,058 PB/yr | **1.85x** | 🔴 critical | 0.80 |
| CoWoS | 105K wpm | 69K wpm | 0.66x | 🟢 surplus | 0.95 |
| Power_DC | — | — | 1.15x | 🟡 tight | 0.95 |

**Cascade 활성:** HBM → CoWoS → Power_DC (lag 2개월)

**병목 분석 (bottleneck_agent 기준):**
- **1차 병목**: HBM (99% 가동률, gap_engine 공시 기반) — NVIDIA 70% 선배분
- **2차 병목**: Power_DC (Vertiv 수주잔고 $8.2B, 납기 18개월)
- **취약 고객군**: Tier 3 소버린 AI (장기계약 없음), Tier 4 엣지/기업
- **투자 국면**: Phase 2 (HBM & Packaging)
- **Strong Buy**: SK Hynix, TSMC CoWoS, ASE, Amkor, Vertiv, Eaton, Schneider Electric

## 산출물 경로

```
outputs/
├── reports/
│   ├── ai_scm_dashboard_YYYYMMDD.html  # D3.js 인터랙티브 대시보드
│   ├── latest.html                     # 최신 대시보드 링크
│   └── ai_scm_study_YYYYMMDD.docx      # 한국어 학습 Word 문서
└── pptx/
    └── ai_scm_YYYYMMDD.pptx            # 임원 보고용 PPT (8슬라이드)

data/
├── supply_state.json   # 공급 수치 (earnings_agent 출력)
├── demand_state.json   # 고객 수요 역산 (demand_mapper 출력)
└── gap_report.json     # 수급갭 + cascade + 기회 (gap_engine 출력)
```

## PostgreSQL DB (ai_scm)

| 테이블 | 내용 |
|--------|------|
| companies | 회사 마스터 (레이어, 시가총액) |
| supply_chain_edges | 공급망 관계 (공급/투자/서비스) |
| network_nodes / network_edges | 투자 네트워크 그래프 스냅샷 |
| bottleneck_scores | 병목 점수 시계열 |
| investment_signals | 투자 시그널 히스토리 |
| model_results | 정량 모델 시나리오 결과 |
| hyperscaler_capex | 하이퍼스케일러 CapEx 데이터 |

연결: `postgresql://localhost:5432/ai_scm`
psycopg2 미설치 또는 DB 연결 실패 시 파일 기반으로 자동 fallback

## 참고 데이터 출처

- NVIDIA 실적: https://investor.nvidia.com/
- SK Hynix HBM: https://news.skhynix.com/hbm/
- TSMC CoWoS: https://ir.tsmc.com/english/annualReports
- Goldman DC 전력: https://www.goldmansachs.com/insights/articles/AI-poised-to-drive-160-increase-in-power-demand
- Bloomberg AI 네트워크: https://www.bloomberg.com/graphics/2025-ai-investment-chart/
- Sequoia AI 인프라: https://www.sequoiacap.com/article/ais-600b-question/
