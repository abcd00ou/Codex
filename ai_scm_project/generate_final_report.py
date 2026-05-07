#!/usr/bin/env python3
"""
AI 공급망 컨설팅 최종 보고서 생성기
- PowerPoint (PPTX) — 임원 보고용 슬라이드
- Word (DOCX)       — 상세 최종 보고서
"""

import datetime
import os
from pathlib import Path

# ── 출력 경로 ──────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
OUT_DIR     = BASE_DIR / "outputs" / "final"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TODAY       = datetime.date(2026, 4, 9)
DATE_STR    = TODAY.strftime("%Y%m%d")
DATE_KR     = TODAY.strftime("%Y년 %m월 %d일")

# ══════════════════════════════════════════════════════════════
# 분석 데이터 (프로젝트 전체 실적 기반)
# ══════════════════════════════════════════════════════════════

HYPERSCALER_CAPEX = [
    ("Microsoft",  80,  90, "Azure AI + OpenAI 인프라 확장"),
    ("Amazon",    105, 120, "AWS Trainium/Inferentia 자체 칩 확대"),
    ("Google",     75,  85, "TPU v5 + Gemini 인프라"),
    ("Meta",       65,  72, "Llama 오픈소스 + 자체 MTIA 칩"),
    ("xAI",        15,  25, "Grok 모델 + Colossus 클러스터"),
]
TOTAL_25 = sum(v[1] for v in HYPERSCALER_CAPEX)
TOTAL_26 = sum(v[2] for v in HYPERSCALER_CAPEX)

BOTTLENECKS = [
    ("HBM",              0.92, "critical", "SK Hynix 독점 수혜 · GB200 NVL72 전용 공급",        "18개월"),
    ("CoWoS 패키징",     0.88, "critical", "TSMC 독점 · 120K wpm(2026) 캐파 확대 중",           "12개월"),
    ("전력 인프라",      0.85, "high",     "트랜스포머 납기 30개월 · 냉각 솔루션 병목",         "24개월"),
    ("GPU 컴퓨팅",       0.88, "critical", "H100→B200 전환 · AMD MI300X 공급 증가",             "9개월"),
    ("AI 네트워킹",      0.72, "high",     "400G/800G InfiniBand 교체 사이클",                  "6개월"),
    ("첨단 파운드리",    0.78, "high",     "TSMC N3/N2 수요 집중 · CoWoS 연동 병목",            "18개월"),
]

SIGNALS = [
    ("SK Hynix",   "000660.KS", "HBM",             "Strong Buy", "+40%", "HBM3e 50% 점유율, GB200 핵심 수혜, HBM4 퀄 2026",         "6~18개월",  2),
    ("Vertiv",     "VRT",       "전력 인프라",       "Buy",        "+35%", "DC 전력 병목 직접 수혜, 2026년까지 Sold Out",              "6~18개월",  3),
    ("Marvell",    "MRVL",      "AI 네트워킹",       "Buy",        "+35%", "AWS Trainium3·Google TPU용 커스텀 ASIC",                  "12~24개월", 2),
    ("Micron",     "MU",        "HBM",             "Buy",        "+30%", "HBM3e 점유율 10→20%+ 확대, CHIPS Act 수혜",               "12~24개월", 2),
    ("GE Vernova", "GEV",       "전력 인프라",       "Buy",        "+30%", "가스터빈·변압기 납기 30개월, 핵에너지 DC 계약",           "12~24개월", 3),
    ("TSMC",       "TSM",       "패키징/파운드리",   "Buy",        "+25%", "CoWoS 92% 가동률, N3/N2 가격 결정력",                    "12~36개월", 2),
    ("Broadcom",   "AVGO",      "AI 네트워킹",       "Buy",        "+20%", "Google/Meta/Apple 커스텀 ASIC, 800G 스위치",             "12~24개월", 2),
    ("Eaton",      "ETN",       "전력 인프라",       "Buy",        "+20%", "DC 전력관리 인프라, UPS·PDU 수요 급증",                  "12~24개월", 3),
    ("NVIDIA",     "NVDA",      "GPU",             "Hold",       "+15%", "B200/GB200 플랫폼 전환, Phase 1 밸류 반영",              "24개월+",   1),
    ("Qualcomm",   "QCOM",      "엣지 AI",          "Watch",      "+25%", "온디바이스 AI 추론 리더, PC AI 사이클 대기",              "18~36개월", 4),
]

PHASES = [
    (1, "GPU 컴퓨팅",    "2023~2024",  "H100 공급 부족 해소 진행 중",    "#e53e3e", "NVDA (Hold)"),
    (2, "HBM & 패키징",  "2024~2026★", "현재 가장 타이트한 병목 구간",   "#dd6b20", "SK Hynix, TSMC, Micron, Broadcom, Marvell"),
    (3, "전력 인프라",   "2026~2027★", "2차 병목 진입 중, 24개월 해소",  "#38a169", "Vertiv, GE Vernova, Eaton"),
    (4, "엣지 AI",       "2027~2028",  "온디바이스 AI 본격화",           "#805ad5", "Qualcomm, Apple, ARM"),
]

QUANT_MODEL = {
    "tokens_per_day_T":  250,   # Trillion tokens/day (2026 전체 AI 서비스 추정)
    "gpu_h100_needed_k": 890,   # K units (H100 등가)
    "hbm_demand_tb":    142,   # PB 단위 → TB 환산
    "power_demand_gw":   85,   # GW (DC 전체 AI 워크로드)
    "ssd_demand_eb":      2.1,  # EB (RAG + 벡터 DB)
}

CURRICULUM = [
    ("HBM 심층 분석",         "Lv.1~3 완료", "HBM2→HBM3e→HBM4 로드맵, 8-Hi 스택, TSV 구조"),
    ("CoWoS 패키징",          "Lv.1~3 완료", "TSMC CoWoS-S/L/R, Fan-out WLP, 120K wpm 확장"),
    ("AI 네트워킹",            "Lv.1~3 완료", "InfiniBand vs RoCE, 400G/800G, NVLink 비교"),
    ("하이퍼스케일러 CapEx",   "Lv.1~3 완료", "$340B 투자 분해, Phase별 수혜 기업 매핑"),
    ("NVIDIA 공급망",          "Lv.1~3 완료", "B200/GB200 NVL72 아키텍처, CoWoS 의존성"),
    ("전력 인프라",            "Lv.1~3 완료", "데이터센터 전력 수요 2배, 트랜스포머 병목"),
    ("소버린 AI",              "Lv.1~3 완료", "UAE/Saudi 국가 AI 인프라, Geopolitical 리스크"),
    ("투자 프레임워크",        "Lv.1~3 완료", "Phase 1~4 로드맵, 병목→투자 시그널 연결 로직"),
]

# 14개 공급망 레이어 전체 (히트맵용)
SUPPLY_CHAIN_LAYERS_FULL = [
    # (레이어명, 가동률, 2026방향: ↑↓→)
    ("HBM",              0.92, "↑"),
    ("CoWoS 패키징",     0.88, "↑"),
    ("GPU 컴퓨팅",       0.88, "→"),
    ("전력 인프라",      0.85, "↑"),
    ("첨단 파운드리",    0.78, "→"),
    ("AI 네트워킹",      0.72, "↑"),
    ("냉각/열관리",      0.70, "↑"),
    ("ASIC/커스텀칩",    0.62, "↑"),
    ("광 인터커넥트",    0.58, "→"),
    ("DRAM",             0.55, "→"),
    ("소버린 AI 인프라", 0.42, "↑"),
    ("CPU",              0.45, "↓"),
    ("엣지 AI 칩",       0.30, "↑"),
    ("SSD 스토리지",     0.35, "→"),
]

# 리스크 매트릭스
RISKS = {
    "HH": [  # 고확률 · 고영향
        "HBM 공급 타이트 지속 (SK Hynix 독점 구조)",
        "DC 전력 인허가 지연 (트랜스포머 30개월)",
        "미중 무역 긴장 심화 (TSMC 지정학)",
    ],
    "LH": [  # 저확률 · 고영향
        "대만 지정학 이벤트 (TSMC 생산 중단)",
        "AGI 조기 진입 (수요 폭발·공급망 재편)",
        "PIM/CXL 조기 도입 (HBM 수요 구조 변화)",
    ],
    "HL": [  # 고확률 · 저영향
        "NVIDIA 경쟁 심화 (AMD MI300X)",
        "하이퍼스케일러 CapEx 미세 조정",
    ],
    "LL": [  # 저확률 · 저영향
        "엣지 AI 보급 지연 (2028+ 이동)",
        "클라우드 업체 칩 내재화 가속",
    ],
}


# ══════════════════════════════════════════════════════════════
# PART 1: PowerPoint 생성
# ══════════════════════════════════════════════════════════════

def make_pptx():
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    # ── 색상 팔레트 ──────────────────────────────────────────
    NAVY   = RGBColor(0x1a, 0x36, 0x5d)
    DARK   = RGBColor(0x2d, 0x37, 0x48)
    BLUE   = RGBColor(0x31, 0x82, 0xce)
    ORANGE = RGBColor(0xdd, 0x6b, 0x20)
    GREEN  = RGBColor(0x38, 0xa1, 0x69)
    RED    = RGBColor(0xe5, 0x3e, 0x3e)
    PURPLE = RGBColor(0x80, 0x5a, 0xd5)
    GRAY   = RGBColor(0x71, 0x80, 0x96)
    LGRAY  = RGBColor(0xed, 0xf2, 0xf7)
    WHITE  = RGBColor(0xff, 0xff, 0xff)
    YELLOW = RGBColor(0xf6, 0xad, 0x55)

    BLANK = prs.slide_layouts[6]  # blank layout

    def add_rect(slide, x, y, w, h, fill_rgb, alpha=None):
        shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.line.fill.background()
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_rgb
        return shape

    def add_text(slide, text, x, y, w, h, size, bold=False, color=None, align=PP_ALIGN.LEFT, wrap=True):
        txb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        txb.word_wrap = wrap
        tf = txb.text_frame
        tf.word_wrap = wrap
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = color
        return txb

    def slide_header(slide, title, subtitle="", accent=NAVY):
        add_rect(slide, 0, 0, 13.33, 1.15, accent)
        add_text(slide, title, 0.4, 0.08, 10, 0.65, 26, bold=True, color=WHITE)
        if subtitle:
            add_text(slide, subtitle, 0.4, 0.72, 12, 0.38, 12, color=RGBColor(0xbe, 0xd0, 0xe8))
        add_rect(slide, 0, 1.15, 13.33, 0.04, BLUE)

    def add_slide_num(slide, num, total=12):
        """슬라이드 번호 + 보고서명 푸터"""
        add_rect(slide, 0, 7.32, 13.33, 0.18, RGBColor(0xed, 0xf2, 0xf7))
        add_text(slide, "AI 공급망 인텔리전스 | 최종 컨설팅 보고서",
                 0.3, 7.33, 9.0, 0.16, 8, color=GRAY)
        add_text(slide, f"{num}  /  {total}",
                 12.0, 7.33, 1.1, 0.16, 9, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)

    # ══════════════════════════════════════════════════════
    # Slide 1 — 표지
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    add_rect(sl, 0, 0, 13.33, 7.5, NAVY)
    add_rect(sl, 0, 0, 13.33, 0.06, BLUE)
    add_rect(sl, 0, 7.44, 13.33, 0.06, ORANGE)
    # 장식 박스
    add_rect(sl, 9.8, 1.5, 3.1, 4.5, RGBColor(0x22, 0x44, 0x70))

    add_text(sl, "AI 공급망 인텔리전스", 0.7, 1.4, 9, 0.9, 42, bold=True, color=WHITE)
    add_text(sl, "컨설팅 최종 보고서", 0.7, 2.3, 9, 0.8, 36, bold=True, color=YELLOW)
    add_text(sl, "AI Supply Chain Intelligence — Final Consulting Report", 0.7, 3.15, 9, 0.5, 14, color=RGBColor(0x90, 0xb4, 0xd8))
    add_text(sl, "━" * 55, 0.7, 3.65, 9, 0.3, 10, color=BLUE)

    add_text(sl, f"보고일: {DATE_KR}", 0.7, 4.05, 6, 0.4, 13, color=RGBColor(0xbe, 0xd0, 0xe8))
    add_text(sl, "분석 범위: AI 공급망 14개 레이어 · 61개 기업 · 8개 전략 주제", 0.7, 4.45, 9, 0.4, 12, color=GRAY)
    add_text(sl, "데이터 출처: NVIDIA IR · SK Hynix · TSMC · Goldman Sachs · Sequoia Capital · IDC", 0.7, 4.82, 9, 0.4, 11, color=GRAY)

    add_text(sl, "핵심 결론", 10.1, 1.9, 2.8, 0.4, 12, bold=True, color=YELLOW)
    key_pts = ["• 현재 Phase 2~3 전환기", "• 1차 병목: HBM (92%)", "• 2차 병목: 전력 인프라", "• Strong Buy: SK Hynix", "• $340B CapEx 집행 중"]
    for i, pt in enumerate(key_pts):
        add_text(sl, pt, 10.1, 2.35 + i * 0.55, 2.8, 0.45, 11, color=WHITE)

    # ══════════════════════════════════════════════════════
    # Slide 2 — 목차
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "목차 (Table of Contents)", "AI 공급망 인텔리전스 최종 보고서 구성")
    add_rect(sl, 0, 1.19, 13.33, 6.31, LGRAY)

    items = [
        ("01", "하이퍼스케일러 CapEx 현황",    "2025/2026 투자 규모 및 방향성 분석"),
        ("02", "AI 공급망 병목 분석",           "14개 레이어 가동률 · 병목 카스케이드"),
        ("03", "정량 모델 결과",                "Token→GPU→HBM→전력 수요 모델 3개 시나리오"),
        ("04", "투자 Phase 로드맵",             "Phase 1~4 전환 타임라인 및 현재 위치"),
        ("05", "기업별 투자 시그널",            "Strong Buy/Buy/Hold 10개 기업 분석"),
        ("06", "AI 학습 커리큘럼 완료 현황",   "8개 주제 × Lv.1~3 = 24단계 완료"),
        ("07", "결론 및 전략 권고",             "Phase별 투자 우선순위 및 리스크"),
    ]
    cols = [(0.4, 6.3), (6.8, 6.1)]
    for idx, (num, title, desc) in enumerate(items):
        col_x, col_w = cols[0] if idx < 4 else cols[1]
        row = idx if idx < 4 else idx - 4
        y = 1.45 + row * 1.22
        add_rect(sl, col_x, y, 0.62, 0.65, NAVY)
        add_text(sl, num, col_x + 0.05, y + 0.05, 0.52, 0.55, 22, bold=True, color=YELLOW, align=PP_ALIGN.CENTER)
        add_rect(sl, col_x + 0.68, y, col_w - 0.68, 0.65, WHITE)
        add_text(sl, title, col_x + 0.8, y + 0.02, col_w - 0.9, 0.35, 14, bold=True, color=DARK)
        add_text(sl, desc,  col_x + 0.8, y + 0.35, col_w - 0.9, 0.28, 10, color=GRAY)

    # ══════════════════════════════════════════════════════
    # Slide 3 — 하이퍼스케일러 CapEx
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "01. 하이퍼스케일러 AI CapEx 현황 ($B)", "2025 실적 vs 2026 가이던스 — 총 $340B → $392B (+15.2%)")
    add_rect(sl, 0, 1.19, 13.33, 6.31, RGBColor(0xf8, 0xf9, 0xfc))

    bar_colors = [BLUE, GREEN, ORANGE, PURPLE, RED]
    max_v = 120
    for i, (co, v25, v26, note) in enumerate(HYPERSCALER_CAPEX):
        y = 1.45 + i * 1.0
        add_text(sl, co, 0.3, y + 0.05, 1.5, 0.4, 13, bold=True, color=DARK)
        # 2025 bar
        w25 = (v25 / max_v) * 5.5
        add_rect(sl, 1.9, y, w25, 0.32, bar_colors[i])
        add_text(sl, f"${v25}B", 1.9 + w25 + 0.05, y, 0.8, 0.32, 12, bold=True, color=bar_colors[i])
        # 2026 bar (lighter)
        w26 = (v26 / max_v) * 5.5
        c = bar_colors[i]
        lighter = RGBColor(min(c[0] + 60, 255), min(c[1] + 60, 255), min(c[2] + 60, 255))
        add_rect(sl, 1.9, y + 0.38, w26, 0.32, lighter)
        add_text(sl, f"${v26}B  ▲{int((v26/v25-1)*100)}%", 1.9 + w26 + 0.05, y + 0.38, 1.5, 0.32, 11, color=GRAY)
        add_text(sl, note, 8.0, y + 0.1, 5.0, 0.55, 10, color=GRAY)

    # 범례
    add_rect(sl, 1.9, 6.75, 0.22, 0.14, BLUE)
    add_text(sl, "2025 실적", 2.18, 6.73, 1.2, 0.2, 10, color=DARK)
    add_rect(sl, 3.5, 6.75, 0.22, 0.14, RGBColor(0xa0, 0xc4, 0xe8))
    add_text(sl, "2026 가이던스", 3.78, 6.73, 1.6, 0.2, 10, color=DARK)
    add_text(sl, f"합계: ${TOTAL_25}B → ${TOTAL_26}B  (+{int((TOTAL_26/TOTAL_25-1)*100)}%)",
             7.5, 6.73, 5.5, 0.2, 12, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)

    # ══════════════════════════════════════════════════════
    # Slide 4 — 병목 분석
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "02. AI 공급망 병목 분석 — 레이어별 가동률", "2026년 Q1 기준 · 병목 카스케이드: HBM → 전력 인프라 → AI 네트워킹")
    add_rect(sl, 0, 1.19, 13.33, 6.31, RGBColor(0xf8, 0xf9, 0xfc))

    sev_color = {"critical": RED, "high": ORANGE, "medium": BLUE, "low": GREEN}
    sev_label = {"critical": "위험", "high": "경고", "medium": "주의", "low": "안정"}

    for i, (comp, util, sev, desc, resolution) in enumerate(BOTTLENECKS):
        y = 1.45 + i * 0.86
        # 가동률 바
        add_rect(sl, 0.3, y + 0.12, 3.8, 0.36, WHITE)
        add_rect(sl, 0.3, y + 0.12, 3.8 * util, 0.36, sev_color[sev])
        add_text(sl, comp, 0.3, y - 0.02, 2.5, 0.3, 12, bold=True, color=DARK)
        add_text(sl, f"{int(util*100)}%", 4.18, y + 0.12, 0.55, 0.36, 13, bold=True, color=sev_color[sev])
        # 상태 뱃지
        add_rect(sl, 4.82, y + 0.12, 0.7, 0.34, sev_color[sev])
        add_text(sl, sev_label[sev], 4.82, y + 0.12, 0.7, 0.34, 10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(sl, desc, 5.62, y + 0.04, 5.5, 0.28, 10, color=DARK)
        add_text(sl, f"해소 예상: {resolution}", 5.62, y + 0.36, 3.0, 0.22, 9, color=GRAY)
        add_text(sl, f"▶ 투자 윈도우", 9.2, y + 0.36, 2.5, 0.22, 9, bold=True, color=ORANGE)

    # ══════════════════════════════════════════════════════
    # Slide 5 — 정량 모델
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "03. 정량 수요 모델 결과 (2026 기준)", "Token → GPU → HBM → 전력 Bottom-up 모델 | Bear / Base / Bull 3개 시나리오")
    add_rect(sl, 0, 1.19, 13.33, 6.31, RGBColor(0xf8, 0xf9, 0xfc))

    # 수식 흐름
    flow = [
        ("토큰 수요",    "250T tokens/day",  BLUE),
        ("GPU 수요",     "890K H100-eq.",     ORANGE),
        ("HBM 수요",     "142PB",             RED),
        ("전력 수요",    "85GW",              GREEN),
        ("SSD 수요",     "2.1EB",             PURPLE),
    ]
    for i, (lbl, val, col) in enumerate(flow):
        x = 0.3 + i * 2.52
        add_rect(sl, x, 1.35, 2.2, 1.0, col)
        add_text(sl, lbl, x, 1.38, 2.2, 0.38, 12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(sl, val, x, 1.75, 2.2, 0.55, 14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        if i < 4:
            add_text(sl, "→", x + 2.2, 1.65, 0.32, 0.4, 18, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # 시나리오 테이블
    scenarios = [
        ("Bear",  "공급 확대 / 경기 침체",    "0.6T", "650K", "95PB",  "60GW",  "1.4EB"),
        ("Base",  "AI 수요 지속 성장",        "1.8T", "890K", "142PB", "85GW",  "2.1EB"),
        ("Bull",  "AGI 진입 / 제약 없는 스케일", "4.2T", "1.5M", "245PB", "160GW", "4.0EB"),
    ]
    hdr_y = 2.6
    add_rect(sl, 0.3, hdr_y, 12.7, 0.4, NAVY)
    for i, h in enumerate(["시나리오", "가정", "토큰/일", "GPU", "HBM", "전력", "SSD"]):
        xs = [0.3, 1.6, 4.1, 5.5, 6.9, 8.1, 9.5, 10.8]
        add_text(sl, h, xs[i] + 0.05, hdr_y + 0.05, xs[i+1]-xs[i]-0.05, 0.3, 10, bold=True, color=WHITE)
    s_colors = [RED, BLUE, GREEN]
    for ri, (sc, asmp, tok, gpu, hbm, pw, ssd) in enumerate(scenarios):
        y = hdr_y + 0.4 + ri * 0.6
        bg = RGBColor(0xff, 0xf5, 0xf5) if ri == 0 else (RGBColor(0xeb, 0xf8, 0xff) if ri == 1 else RGBColor(0xf0, 0xff, 0xf4))
        add_rect(sl, 0.3, y, 12.7, 0.56, bg)
        add_rect(sl, 0.3, y, 1.25, 0.56, s_colors[ri])
        add_text(sl, sc, 0.3, y + 0.1, 1.25, 0.36, 13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        vals = [asmp, tok, gpu, hbm, pw, ssd]
        xs2  = [1.62, 4.12, 5.52, 6.92, 8.12, 9.52]
        ws2  = [2.45, 1.35, 1.35, 1.15, 1.35, 2.5]
        for j, (vl, xi, wi) in enumerate(zip(vals, xs2, ws2)):
            add_text(sl, vl, xi, y + 0.1, wi, 0.36, 11, bold=(j > 0), color=DARK)

    add_text(sl, "* 2026년 전체 AI 서비스 통합 추정치 | 수식: GPU = Tokens/day ÷ (tokens/sec × 가동률) | HBM = GPU수 × GPU당 HBM",
             0.3, 6.5, 12.7, 0.3, 9, color=GRAY)

    # ══════════════════════════════════════════════════════
    # Slide 6 — Phase 로드맵
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "04. AI 공급망 투자 Phase 로드맵", "병목 카스케이드 기반 투자 타임라인 — 현재: Phase 2~3 전환기")
    add_rect(sl, 0, 1.19, 13.33, 6.31, RGBColor(0xf8, 0xf9, 0xfc))

    phase_colors = [RGBColor(0xe5, 0x3e, 0x3e), RGBColor(0xdd, 0x6b, 0x20), RGBColor(0x38, 0xa1, 0x69), RGBColor(0x80, 0x5a, 0xd5)]
    phase_data   = PHASES
    for i, (ph, name, period, desc, _col, stocks) in enumerate(phase_data):
        x = 0.25 + i * 3.22
        is_current = (ph in [2, 3])
        # 현재 페이즈 강조
        bg = RGBColor(0xff, 0xf3, 0xe0) if is_current else WHITE
        add_rect(sl, x, 1.35, 3.0, 5.8, bg)
        add_rect(sl, x, 1.35, 3.0, 0.7, phase_colors[i])
        add_text(sl, f"Phase {ph}", x + 0.1, 1.38, 2.8, 0.35, 15, bold=True, color=WHITE)
        add_text(sl, name, x + 0.1, 1.73, 2.8, 0.28, 10, color=WHITE)
        if is_current:
            add_text(sl, "★ 현재", x + 2.2, 1.38, 0.7, 0.35, 10, bold=True, color=YELLOW)
        add_text(sl, period, x + 0.1, 2.15, 2.8, 0.3, 12, bold=True, color=phase_colors[i])
        add_text(sl, desc,   x + 0.1, 2.5, 2.8, 0.55, 10, color=DARK, wrap=True)
        add_text(sl, "핵심 투자처:", x + 0.1, 3.18, 2.8, 0.28, 10, bold=True, color=DARK)
        # 개별 종목
        for si, stk in enumerate(stocks.split(", ")):
            sy = 3.5 + si * 0.47
            if sy > 6.9: break
            add_rect(sl, x + 0.1, sy, 2.75, 0.38, RGBColor(0xed, 0xf2, 0xf7))
            add_text(sl, stk, x + 0.18, sy + 0.04, 2.6, 0.3, 11, color=DARK)

    # 화살표 타임라인
    add_rect(sl, 0.25, 7.1, 12.8, 0.06, NAVY)
    add_text(sl, "2023 ──────── 2024 ──────── 2025 ──────── 2026 ──────── 2027 ──────── 2028 ──────── 2029",
             0.3, 7.18, 12.8, 0.25, 10, color=NAVY)

    # ══════════════════════════════════════════════════════
    # Slide 7 — 투자 시그널
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "05. 기업별 투자 시그널 (10개)", "공급망 병목 분석 기반 Bottom-up 투자 시그널 | 2026년 Q1 기준")
    add_rect(sl, 0, 1.19, 13.33, 6.31, RGBColor(0xf8, 0xf9, 0xfc))

    sig_colors = {"Strong Buy": GREEN, "Buy": BLUE, "Hold": ORANGE, "Watch": PURPLE}
    # 헤더
    hdr_y2 = 1.28
    add_rect(sl, 0.2, hdr_y2, 12.9, 0.36, NAVY)
    for lbl, xi in [("기업", 0.25), ("레이어", 1.9), ("시그널", 3.4), ("목표수익", 4.65),
                    ("기간", 5.55), ("투자 논거", 7.05)]:
        add_text(sl, lbl, xi, hdr_y2 + 0.04, 1.3, 0.28, 10, bold=True, color=WHITE)

    for ri, (co, tkr, layer, sig, upside, thesis, tf, ph) in enumerate(SIGNALS):
        y = 1.64 + ri * 0.56
        bg = RGBColor(0xf7, 0xf8, 0xfa) if ri % 2 == 0 else WHITE
        add_rect(sl, 0.2, y, 12.9, 0.52, bg)
        add_text(sl, co,  0.28, y + 0.08, 1.55, 0.36, 11, bold=True, color=DARK)
        add_text(sl, tkr, 0.28, y + 0.34, 1.55, 0.18, 8,  color=GRAY)
        add_text(sl, layer, 1.9, y + 0.12, 1.4, 0.28, 10, color=DARK)
        sc = sig_colors.get(sig, GRAY)
        add_rect(sl, 3.4, y + 0.08, 1.15, 0.32, sc)
        add_text(sl, sig, 3.4, y + 0.08, 1.15, 0.32, 9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(sl, upside, 4.68, y + 0.1, 0.78, 0.32, 13, bold=True, color=sc)
        add_text(sl, tf,     5.55, y + 0.1, 1.4, 0.32, 9, color=DARK)
        add_text(sl, f"Ph.{ph}", 7.03, y + 0.1, 0.45, 0.32, 9, bold=True, color=ORANGE)
        add_text(sl, thesis, 7.52, y + 0.08, 5.5, 0.36, 9, color=DARK, wrap=True)

    # ══════════════════════════════════════════════════════
    # Slide 8 — 학습 커리큘럼 완료
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "06. AI SCM 학습 커리큘럼 — 전 과정 완료", "8개 전략 주제 × Lv.1(기초)~Lv.3(전문가) = 24단계 | 30분 cron 자동화 이메일 시스템")
    add_rect(sl, 0, 1.19, 13.33, 6.31, RGBColor(0xf8, 0xf9, 0xfc))

    lv_colors = [RGBColor(0x48, 0xbb, 0x78), RGBColor(0x63, 0xb3, 0xed), RGBColor(0x9f, 0x7a, 0xea)]
    for i, (topic, status, detail) in enumerate(CURRICULUM):
        col = i % 2
        row = i // 2
        x = 0.3 + col * 6.55
        y = 1.4 + row * 1.35
        add_rect(sl, x, y, 6.1, 1.2, WHITE)
        add_rect(sl, x, y, 0.18, 1.2, GREEN)
        add_text(sl, f"{i+1:02d}", x + 0.25, y + 0.06, 0.6, 0.4, 15, bold=True, color=NAVY)
        add_text(sl, topic, x + 0.9, y + 0.06, 4.8, 0.38, 12, bold=True, color=DARK)
        # Lv 뱃지
        for li, (lv, lc) in enumerate([("Lv.1", lv_colors[0]), ("Lv.2", lv_colors[1]), ("Lv.3", lv_colors[2])]):
            add_rect(sl, x + 0.9 + li * 0.72, y + 0.5, 0.64, 0.22, lc)
            add_text(sl, lv, x + 0.9 + li * 0.72, y + 0.5, 0.64, 0.22, 8, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(sl, detail, x + 0.25, y + 0.8, 5.7, 0.32, 9, color=GRAY, wrap=True)

    # 요약 박스
    add_rect(sl, 0.3, 6.75, 12.7, 0.5, NAVY)
    add_text(sl, "✓ 총 24단계 완료 (8 주제 × 3 라운드)   ✓ 매 30분 cron 자동 발송   ✓ 뉴스 연동 + 레벨별 싱크 심화   ✓ Word/HTML 리포트 동시 생성",
             0.5, 6.83, 12.4, 0.34, 11, color=WHITE)

    # ══════════════════════════════════════════════════════
    # Slide 9 — 결론 및 전략 권고
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "07. 결론 및 전략 권고", "AI 공급망 컨설팅 최종 결론 | 2026년 Q1 기준 · 6~18개월 액션 플랜")
    add_rect(sl, 0, 1.19, 13.33, 6.31, RGBColor(0xf8, 0xf9, 0xfc))

    conclusions = [
        (ORANGE, "현재 포지션: Phase 2~3 전환기",
         "HBM·CoWoS 병목(Phase 2)이 아직 해소되지 않은 상태에서 전력 인프라(Phase 3) 병목이 동시 진입.\n"
         "역사적으로 두 병목이 겹치는 구간이 가장 강한 투자 수익을 기록함."),
        (RED, "단기 (6~12개월): HBM·CoWoS 집중",
         "SK Hynix(HBM3e 50% 점유) + TSMC CoWoS(92% 가동률) — 공급 제약이 가장 명확한 레이어.\n"
         "Marvell(AWS/Google ASIC)·Broadcom(800G) 네트워킹 업그레이드 병행 진입 유효."),
        (GREEN, "중기 (12~24개월): 전력 인프라 확대",
         "Vertiv·GE Vernova·Eaton — 트랜스포머 납기 30개월, DC 전력 수요 2배 확대 예정.\n"
         "현재 수주잔고 기반 Visibility 가장 높은 섹터. CAPEX 사이클 2026~2027 피크."),
        (PURPLE, "장기 (24개월+): 엣지 AI & 소버린 AI",
         "온디바이스 AI 침투 + 국가 단위 AI 인프라 투자(UAE/Saudi/EU).\n"
         "Qualcomm·ARM·로컬 클라우드 사업자 — Phase 4 포지셔닝 시작 타이밍."),
    ]
    for i, (col, title, body) in enumerate(conclusions):
        y = 1.38 + i * 1.45
        add_rect(sl, 0.3, y, 0.2, 1.2, col)
        add_rect(sl, 0.55, y, 12.5, 1.2, WHITE)
        add_text(sl, title, 0.7, y + 0.06, 12.2, 0.38, 13, bold=True, color=col)
        add_text(sl, body,  0.7, y + 0.46, 12.2, 0.68, 10, color=DARK, wrap=True)

    # ══════════════════════════════════════════════════════
    # Slide 10 — 14개 레이어 병목 히트맵
    # ══════════════════════════════════════════════════════
    TOTAL_SLIDES = 12
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "08. AI 공급망 14개 레이어 — 병목 히트맵", "2026년 Q1 가동률 기준 | 색상: 🔴 위험(≥88%) · 🟠 경고(75~87%) · 🟡 주의(60~74%) · 🟢 안정(<60%)")
    add_rect(sl, 0, 1.19, 13.33, 6.0, RGBColor(0xf8, 0xf9, 0xfc))
    add_slide_num(sl, 10, TOTAL_SLIDES)

    def util_color(u):
        if u >= 0.88: return RGBColor(0xe5, 0x3e, 0x3e)
        if u >= 0.75: return RGBColor(0xdd, 0x6b, 0x20)
        if u >= 0.60: return RGBColor(0xd6, 0x9e, 0x00)
        return RGBColor(0x38, 0xa1, 0x69)

    # 7개씩 2열 배치
    for i, (layer, util, trend) in enumerate(SUPPLY_CHAIN_LAYERS_FULL):
        col = i % 2
        row = i // 2
        x = 0.3 + col * 6.55
        y = 1.35 + row * 0.75
        uc = util_color(util)
        bar_w = 3.8 * util
        # 배경
        add_rect(sl, x, y, 6.1, 0.62, WHITE)
        # 레이어명
        add_text(sl, layer, x + 0.12, y + 0.06, 2.0, 0.28, 11, bold=True, color=DARK)
        # 추세 화살표
        t_col = RED if trend == "↑" else (GREEN if trend == "↓" else GRAY)
        add_text(sl, trend, x + 2.15, y + 0.06, 0.28, 0.28, 13, bold=True, color=t_col)
        # 가동률 바
        add_rect(sl, x + 2.5, y + 0.12, 3.2, 0.26, RGBColor(0xed, 0xf2, 0xf7))
        add_rect(sl, x + 2.5, y + 0.12, 3.2 * util, 0.26, uc)
        # 수치
        add_text(sl, f"{int(util*100)}%", x + 5.78, y + 0.1, 0.28, 0.3, 11, bold=True, color=uc)

    # 범례
    for label, col in [("위험 ≥88%", RED), ("경고 75~87%", ORANGE),
                        ("주의 60~74%", RGBColor(0xd6, 0x9e, 0x00)), ("안정 <60%", GREEN)]:
        xi = 0.3 + [("위험 ≥88%", RED), ("경고 75~87%", ORANGE),
                    ("주의 60~74%", RGBColor(0xd6, 0x9e, 0x00)), ("안정 <60%", GREEN)].index((label, col)) * 3.0
        add_rect(sl, xi, 7.08, 0.2, 0.14, col)
        add_text(sl, label, xi + 0.26, 7.06, 2.5, 0.18, 9, color=DARK)

    # ══════════════════════════════════════════════════════
    # Slide 11 — 리스크 매트릭스
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    slide_header(sl, "09. 리스크 매트릭스 (2×2)", "확률(Likelihood) × 영향(Impact) 기준 | AI 공급망 핵심 리스크 분류")
    add_rect(sl, 0, 1.19, 13.33, 6.0, RGBColor(0xf8, 0xf9, 0xfc))
    add_slide_num(sl, 11, TOTAL_SLIDES)

    # 축 레이블
    add_text(sl, "↑ 영향(Impact) 높음", 0.25, 1.28, 1.4, 4.0, 10, bold=True,
             color=NAVY, align=PP_ALIGN.CENTER)
    add_text(sl, "확률(Likelihood) →", 2.0, 6.95, 9.0, 0.25, 10, bold=True, color=NAVY)
    add_text(sl, "낮음", 1.8, 6.93, 1.0, 0.18, 9, color=GRAY)
    add_text(sl, "높음", 10.6, 6.93, 0.9, 0.18, 9, color=GRAY)

    quadrants = [
        # (x, y, w, h, bg_color, header, header_color, items_key, label)
        (2.0, 1.28, 5.0, 2.7,  RGBColor(0xff, 0xf5, 0xf5), "고영향 · 저확률 (모니터링)", RED,    "LH", "WATCH"),
        (7.1, 1.28, 5.9, 2.7,  RGBColor(0xff, 0xeb, 0xd0), "고영향 · 고확률 (즉시 대응)", ORANGE, "HH", "ACTION"),
        (2.0, 4.08, 5.0, 2.72, RGBColor(0xf0, 0xff, 0xf4), "저영향 · 저확률 (관찰)",     GREEN,  "LL", "WATCH"),
        (7.1, 4.08, 5.9, 2.72, RGBColor(0xeb, 0xf8, 0xff), "저영향 · 고확률 (관리)",     BLUE,   "HL", "MANAGE"),
    ]
    for (qx, qy, qw, qh, qbg, qtitle, qcol, qkey, qlabel) in quadrants:
        add_rect(sl, qx, qy, qw, qh, qbg)
        add_rect(sl, qx, qy, qw, 0.35, qcol)
        add_text(sl, qtitle, qx + 0.12, qy + 0.04, qw - 0.2, 0.28, 10, bold=True, color=WHITE)
        add_rect(sl, qx + qw - 0.85, qy + 0.04, 0.78, 0.26, WHITE)
        add_text(sl, qlabel, qx + qw - 0.85, qy + 0.04, 0.78, 0.26, 8, bold=True,
                 color=qcol, align=PP_ALIGN.CENTER)
        for ri, item in enumerate(RISKS.get(qkey, [])):
            iy = qy + 0.44 + ri * 0.72
            if iy + 0.62 > qy + qh: break
            add_rect(sl, qx + 0.12, iy, qw - 0.24, 0.62, WHITE)
            add_rect(sl, qx + 0.12, iy, 0.06, 0.62, qcol)
            add_text(sl, item, qx + 0.25, iy + 0.08, qw - 0.42, 0.46, 9,
                     color=DARK, wrap=True)

    # ══════════════════════════════════════════════════════
    # Slide 12 — 마지막 슬라이드
    # ══════════════════════════════════════════════════════
    sl = prs.slides.add_slide(BLANK)
    add_rect(sl, 0, 0, 13.33, 7.5, NAVY)
    add_rect(sl, 0, 0, 13.33, 0.06, ORANGE)
    add_rect(sl, 0, 7.44, 13.33, 0.06, BLUE)
    add_text(sl, "AI 공급망 인텔리전스 컨설팅", 1.5, 1.8, 10, 0.8, 36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(sl, "최종 보고서 완료", 1.5, 2.65, 10, 0.65, 28, bold=True, color=YELLOW, align=PP_ALIGN.CENTER)
    add_text(sl, "━" * 70, 1.5, 3.38, 10, 0.3, 10, color=BLUE, align=PP_ALIGN.CENTER)
    add_text(sl, f"분석 기준일: {DATE_KR}  ·  14개 공급망 레이어  ·  61개 기업  ·  8개 전략 주제",
             1.0, 3.75, 11.3, 0.4, 12, color=RGBColor(0xbe, 0xd0, 0xe8), align=PP_ALIGN.CENTER)
    add_text(sl, "본 보고서는 공개 데이터 및 AI 분석 기반이며 투자 권유가 아닙니다.",
             1.0, 6.9, 11.3, 0.35, 10, color=GRAY, align=PP_ALIGN.CENTER)

    # 기존 슬라이드에 번호 소급 적용 (표지/마지막 제외 = index 1~10)
    for idx, slide_obj in enumerate(prs.slides):
        slide_num = idx + 1
        if slide_num in (1, TOTAL_SLIDES):
            continue  # 표지·마지막은 번호 없음
        add_slide_num(slide_obj, slide_num, TOTAL_SLIDES)

    out = OUT_DIR / f"AI_SCM_Final_Report_{DATE_STR}.pptx"
    prs.save(str(out))
    print(f"  PPTX: {out}")
    return out


# ══════════════════════════════════════════════════════════════
# PART 2: Word 문서 생성
# ══════════════════════════════════════════════════════════════

def make_docx():
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    import copy

    doc = Document()

    # ── 페이지 여백 + 푸터(페이지 번호) 설정 ─────────────
    from docx.oxml.ns import qn as _qn
    from docx.oxml import OxmlElement as _OxmlElement

    def _add_page_number_footer(section):
        """섹션 푸터에 페이지 번호 + 보고서명 삽입"""
        footer = section.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.clear()
        # 보고서명
        r_label = p.add_run("AI 공급망 인텔리전스 최종 보고서   |   ")
        r_label.font.size = Pt(8)
        r_label.font.color.rgb = RGBColor(0xa0, 0xae, 0xc0)
        # 페이지 번호 필드
        fldChar1 = _OxmlElement('w:fldChar')
        fldChar1.set(_qn('w:fldCharType'), 'begin')
        instrText = _OxmlElement('w:instrText')
        instrText.set(_qn('xml:space'), 'preserve')
        instrText.text = ' PAGE '
        fldChar2 = _OxmlElement('w:fldChar')
        fldChar2.set(_qn('w:fldCharType'), 'end')
        r_page = p.add_run()
        r_page.font.size = Pt(8)
        r_page.font.bold = True
        r_page.font.color.rgb = RGBColor(0x1a, 0x36, 0x5d)
        r_page._r.append(fldChar1)
        r_page._r.append(instrText)
        r_page._r.append(fldChar2)

    for sec in doc.sections:
        sec.top_margin    = Cm(2.0)
        sec.bottom_margin = Cm(2.0)
        sec.left_margin   = Cm(2.5)
        sec.right_margin  = Cm(2.5)
        _add_page_number_footer(sec)

    def set_cell_bg(cell, hex_color):
        tc   = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd  = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), hex_color)
        tcPr.append(shd)

    def h1(text):
        p = doc.add_heading(text, level=1)
        p.runs[0].font.color.rgb = RGBColor(0x1a, 0x36, 0x5d)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after  = Pt(6)

    def h2(text):
        p = doc.add_heading(text, level=2)
        p.runs[0].font.color.rgb = RGBColor(0x2d, 0x37, 0x48)
        p.paragraph_format.space_before = Pt(14)

    def h3(text):
        p = doc.add_heading(text, level=3)
        p.runs[0].font.color.rgb = RGBColor(0x31, 0x82, 0xce)

    def body(text, bold=False, color=None):
        p = doc.add_paragraph(text)
        p.paragraph_format.space_after = Pt(4)
        if bold or color:
            for run in p.runs:
                run.font.bold = bold
                if color:
                    run.font.color.rgb = RGBColor(*color)
        return p

    def bullet(text, level=0):
        p = doc.add_paragraph(text, style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.25 * (level + 1))
        p.paragraph_format.space_after = Pt(2)

    def divider():
        p = doc.add_paragraph("─" * 80)
        p.runs[0].font.size = Pt(7)
        p.runs[0].font.color.rgb = RGBColor(0xcc, 0xcc, 0xcc)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after  = Pt(4)

    def add_table_row(tbl, cells, bold_first=False, bg=None, sizes=None):
        row = tbl.add_row()
        for i, (cell, text) in enumerate(zip(row.cells, cells)):
            cell.text = str(text)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = cell.paragraphs[0].runs[0] if cell.paragraphs[0].runs else cell.paragraphs[0].add_run(str(text))
            run.font.size = Pt(10)
            if bold_first and i == 0:
                run.font.bold = True
            if bg:
                set_cell_bg(cell, bg)
        return row

    # ══════════════════════════════════════════════════════
    # 표지
    # ══════════════════════════════════════════════════════
    doc.add_paragraph("")
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("AI 공급망 인텔리전스 컨설팅")
    r.font.size = Pt(28)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1a, 0x36, 0x5d)

    t2 = doc.add_paragraph()
    t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = t2.add_run("최 종 보 고 서")
    r2.font.size = Pt(22)
    r2.font.bold = True
    r2.font.color.rgb = RGBColor(0xdd, 0x6b, 0x20)

    doc.add_paragraph("")
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    mr = meta.add_run(f"보고일: {DATE_KR}   |   분석 범위: 2026년 Q1 기준")
    mr.font.size = Pt(12)
    mr.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    doc.add_paragraph("")
    divider()

    # ══════════════════════════════════════════════════════
    # 1. 경영진 요약 (Executive Summary)
    # ══════════════════════════════════════════════════════
    h1("1. 경영진 요약 (Executive Summary)")

    body("본 보고서는 AI 인프라 공급망 전체를 14개 레이어·61개 기업으로 매핑하고, "
         "Bottom-up 정량 모델을 통해 2026~2028년 수요를 예측하며, 현재 병목 구조를 분석하여 "
         "Phase별 투자 시그널을 도출한 종합 컨설팅 결과물입니다.")

    # ── KPI 하이라이트 박스 ─────────────────────────────
    doc.add_paragraph("")
    kpi_tbl = doc.add_table(rows=1, cols=5)
    kpi_tbl.style = 'Table Grid'
    kpi_items = [
        ("$392B", "하이퍼스케일러\n2026 CapEx"),
        ("92%", "HBM 가동률\n(1차 병목)"),
        ("Phase 2~3", "현재\n투자 국면"),
        ("+40%", "SK Hynix\nStrong Buy"),
        ("8개 주제", "커리큘럼\n전 과정 완료"),
    ]
    kpi_colors = ["1A365D", "E53E3E", "DD6B20", "38A169", "805AD5"]
    kpi_row = kpi_tbl.rows[0]
    for j, ((val, lbl), bg) in enumerate(zip(kpi_items, kpi_colors)):
        cell = kpi_row.cells[j]
        cell.text = ""
        set_cell_bg(cell, bg)
        # 수치
        p_val = cell.add_paragraph(val)
        p_val.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_val = p_val.runs[0]
        r_val.font.size = Pt(18)
        r_val.font.bold = True
        r_val.font.color.rgb = RGBColor(0xff, 0xff, 0xff)
        # 레이블
        p_lbl = cell.add_paragraph(lbl)
        p_lbl.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_lbl = p_lbl.runs[0]
        r_lbl.font.size = Pt(8)
        r_lbl.font.color.rgb = RGBColor(0xcc, 0xdd, 0xee)

    doc.add_paragraph("")
    h2("핵심 발견 사항")

    findings = [
        ("현재 투자 국면", "Phase 2~3 동시 진입기 (HBM·CoWoS 병목 진행 중 + 전력 인프라 병목 개시)"),
        ("1차 병목", "HBM — 92% 가동률, SK Hynix 50% 독점, 해소까지 18개월"),
        ("2차 병목", "전력 인프라 — 85% 가동률, 트랜스포머 납기 30개월, 해소까지 24개월"),
        ("3차 병목", "CoWoS 패키징 — 88% 가동률, TSMC 독점, 12~18개월 캐파 확장 중"),
        ("CapEx 규모", f"하이퍼스케일러 5개사 2025년 합계 ${TOTAL_25}B → 2026년 ${TOTAL_26}B (+{int((TOTAL_26/TOTAL_25-1)*100)}%)"),
        ("최고 시그널", "SK Hynix (Strong Buy +40%) — HBM3e 공급 독점 + GB200 핵심 수혜"),
    ]
    tbl = doc.add_table(rows=0, cols=2)
    tbl.style = 'Table Grid'
    tbl.columns[0].width = Inches(2.2)
    tbl.columns[1].width = Inches(4.8)
    for i, (k, v) in enumerate(findings):
        row = tbl.add_row()
        row.cells[0].text = k
        row.cells[1].text = v
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[0].paragraphs[0].runs[0].font.size = Pt(10)
        row.cells[1].paragraphs[0].runs[0].font.size = Pt(10)
        bg = "EBF8FF" if i % 2 == 0 else "FFFFFF"
        set_cell_bg(row.cells[0], bg)
        set_cell_bg(row.cells[1], bg)

    # ══════════════════════════════════════════════════════
    # 2. 하이퍼스케일러 CapEx 분석
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("2. 하이퍼스케일러 AI CapEx 분석")

    body("글로벌 AI 인프라 투자의 핵심 드라이버는 하이퍼스케일러 5개사(Microsoft, Amazon, Google, Meta, xAI)의 "
         "데이터센터 CapEx입니다. 2025년 합계 $340B에서 2026년 $392B으로 15.2% 성장이 예상됩니다.")

    doc.add_paragraph("")
    tbl2 = doc.add_table(rows=0, cols=4)
    tbl2.style = 'Table Grid'
    # 헤더
    hrow = tbl2.add_row()
    for i, h in enumerate(["기업", "2025 (실적, $B)", "2026 (가이던스, $B)", "전략 방향"]):
        hrow.cells[i].text = h
        hrow.cells[i].paragraphs[0].runs[0].font.bold = True
        hrow.cells[i].paragraphs[0].runs[0].font.size = Pt(10)
        set_cell_bg(hrow.cells[i], "1A365D")
        hrow.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)

    for i, (co, v25, v26, note) in enumerate(HYPERSCALER_CAPEX):
        row = tbl2.add_row()
        chg = f"+{int((v26/v25-1)*100)}%"
        vals = [co, f"${v25}B", f"${v26}B ({chg})", note]
        bg = "EBF8FF" if i % 2 == 0 else "FFFFFF"
        for j, val in enumerate(vals):
            row.cells[j].text = val
            row.cells[j].paragraphs[0].runs[0].font.size = Pt(10)
            if j == 0:
                row.cells[j].paragraphs[0].runs[0].font.bold = True
            set_cell_bg(row.cells[j], bg)

    # 합계 행
    tot_row = tbl2.add_row()
    set_cell_bg(tot_row.cells[0], "2D3748")
    set_cell_bg(tot_row.cells[1], "2D3748")
    set_cell_bg(tot_row.cells[2], "2D3748")
    set_cell_bg(tot_row.cells[3], "2D3748")
    tot_vals = ["합계", f"${TOTAL_25}B", f"${TOTAL_26}B (+{int((TOTAL_26/TOTAL_25-1)*100)}%)", "AI 인프라 전방위 투자 집행"]
    for j, v in enumerate(tot_vals):
        tot_row.cells[j].text = v
        r = tot_row.cells[j].paragraphs[0].runs[0]
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xff, 0xff, 0xff)

    doc.add_paragraph("")
    body("주목 포인트:")
    bullet("Amazon: AWS Trainium/Inferentia 자체 칩 확대로 NVIDIA 의존도 분산 — Marvell 수혜")
    bullet("Microsoft: OpenAI 파트너십 유지 + 자체 Maia 칩 개발 병행 (2026 양산 예정)")
    bullet("xAI: Grok 모델 학습용 Colossus 클러스터 ($25B) — NAND/HBM 수요 급증 촉발")

    # ══════════════════════════════════════════════════════
    # 3. 공급망 병목 분석
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("3. AI 공급망 병목 분석")

    body("AI 공급망 14개 레이어를 분석한 결과, 현재 가장 심각한 병목은 HBM(92%)·CoWoS(88%)·전력 인프라(85%)의 "
         "3중 병목 구조입니다. 특히 HBM과 CoWoS는 상호 연결된 '공동 병목(Co-bottleneck)'으로 동시 해소가 필요합니다.")

    doc.add_paragraph("")

    tbl3 = doc.add_table(rows=0, cols=5)
    tbl3.style = 'Table Grid'
    hrow3 = tbl3.add_row()
    for i, h in enumerate(["레이어", "가동률", "심각도", "핵심 설명", "해소 예상"]):
        hrow3.cells[i].text = h
        hrow3.cells[i].paragraphs[0].runs[0].font.bold = True
        hrow3.cells[i].paragraphs[0].runs[0].font.size = Pt(10)
        set_cell_bg(hrow3.cells[i], "1A365D")
        hrow3.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)

    sev_bg = {"critical": "FFF5F5", "high": "FFFAF0", "medium": "EBF8FF"}
    for comp, util, sev, desc, res in BOTTLENECKS:
        row = tbl3.add_row()
        sev_kr = {"critical": "⚠️ 위험", "high": "⚡ 경고", "medium": "📊 주의"}.get(sev, sev)
        vals = [comp, f"{int(util*100)}%", sev_kr, desc, res]
        bg = sev_bg.get(sev, "FFFFFF")
        for j, v in enumerate(vals):
            row.cells[j].text = v
            row.cells[j].paragraphs[0].runs[0].font.size = Pt(10)
            if j == 0:
                row.cells[j].paragraphs[0].runs[0].font.bold = True
            set_cell_bg(row.cells[j], bg)

    doc.add_paragraph("")
    h2("병목 카스케이드 메커니즘")
    body("병목은 순차적으로 이동하는 '카스케이드' 구조를 보입니다:")
    bullet("Phase 1 (2023~2024): GPU 공급 부족 → H100 waiting list 12개월+")
    bullet("Phase 2 (2024~2026 현재): HBM·CoWoS 병목 — AI칩 성능 限界 = 패키징·메모리 한계")
    bullet("Phase 3 (2026~2027 진입 중): 전력 인프라 — 데이터센터 전력 수요 2배, 트랜스포머 납기 30개월")
    bullet("Phase 4 (2027~2028): 엣지 AI — 온디바이스 추론 확산, AI PC·스마트폰 NPU 업그레이드 사이클")

    # ══════════════════════════════════════════════════════
    # 4. 정량 수요 모델
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("4. 정량 수요 모델 (2026 기준)")

    h2("4.1 핵심 수식")
    body("Bottom-up 정량 모델은 AI 서비스 Token 수요에서 출발하여 공급망 전체를 역산합니다.")
    doc.add_paragraph("")

    eqs = [
        ("Token → GPU", "GPU 수 = 토큰/일 ÷ (GPU당 토큰/초 × 가동률)"),
        ("GPU → HBM",   "HBM(GB) = GPU 수 × GPU당 HBM 용량"),
        ("KV Cache",    "KV Cache = 컨텍스트 × 사용자 × 2(byte) × 2(K+V)"),
        ("SSD 수요",    "SSD(TB) = RAG 토큰 수 × byte/token × retention days"),
        ("전력 수요",   "전력(MW) = GPU 수 × TDP(W) × 1.3(overhead) × PUE ÷ 10⁶"),
    ]
    tbl4 = doc.add_table(rows=0, cols=2)
    tbl4.style = 'Table Grid'
    for k, v in eqs:
        row = tbl4.add_row()
        row.cells[0].text = k
        row.cells[1].text = v
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[0].paragraphs[0].runs[0].font.size = Pt(10)
        row.cells[1].paragraphs[0].runs[0].font.size = Pt(10)
        row.cells[1].paragraphs[0].runs[0].font.name = "Courier New"

    doc.add_paragraph("")
    h2("4.2 시나리오별 결과 (2026E)")

    tbl5 = doc.add_table(rows=0, cols=7)
    tbl5.style = 'Table Grid'
    hrow5 = tbl5.add_row()
    for i, h in enumerate(["시나리오", "가정", "토큰/일", "GPU", "HBM", "전력", "SSD"]):
        hrow5.cells[i].text = h
        hrow5.cells[i].paragraphs[0].runs[0].font.bold = True
        hrow5.cells[i].paragraphs[0].runs[0].font.size = Pt(10)
        set_cell_bg(hrow5.cells[i], "2D3748")
        hrow5.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)

    sc_data = [
        ("Bear",  "공급 확대·경기 침체", "0.6T", "650K",  "95PB",  "60GW",  "1.4EB", "FFF5F5"),
        ("Base",  "AI 수요 지속 성장",   "1.8T", "890K",  "142PB", "85GW",  "2.1EB", "EBF8FF"),
        ("Bull",  "AGI 진입·제약 無스케일", "4.2T", "1.5M", "245PB", "160GW", "4.0EB", "F0FFF4"),
    ]
    for sc, asmp, tok, gpu, hbm, pw, ssd, bg in sc_data:
        row = tbl5.add_row()
        for j, v in enumerate([sc, asmp, tok, gpu, hbm, pw, ssd]):
            row.cells[j].text = v
            r = row.cells[j].paragraphs[0].runs[0]
            r.font.size = Pt(10)
            if j == 0:
                r.font.bold = True
            set_cell_bg(row.cells[j], bg)

    # ══════════════════════════════════════════════════════
    # 5. 투자 Phase 로드맵
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("5. 투자 Phase 로드맵")

    body("AI 공급망 투자는 병목 카스케이드를 따라 단계적으로 이동합니다. "
         "현재는 Phase 2(HBM·패키징)와 Phase 3(전력 인프라)가 동시 진행 중인 가장 밀집된 투자 구간입니다.")
    doc.add_paragraph("")

    for ph, name, period, desc, _, stocks in PHASES:
        is_current = ph in [2, 3]
        prefix = "★ [현재 진입]" if is_current else ""
        h3(f"Phase {ph}: {name}  {prefix}")
        body(f"투자 기간: {period}")
        body(desc)
        body(f"핵심 투자처: {stocks}", bold=True)
        doc.add_paragraph("")

    # ══════════════════════════════════════════════════════
    # 6. 기업별 투자 시그널
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("6. 기업별 투자 시그널 (10개)")

    body("공급망 병목 분석에서 도출된 Bottom-up 투자 시그널입니다. 강도: Strong Buy > Buy > Hold > Watch")
    doc.add_paragraph("")

    tbl6 = doc.add_table(rows=0, cols=7)
    tbl6.style = 'Table Grid'
    hrow6 = tbl6.add_row()
    for i, h in enumerate(["기업", "티커", "레이어", "시그널", "목표수익", "투자 기간", "투자 논거"]):
        hrow6.cells[i].text = h
        hrow6.cells[i].paragraphs[0].runs[0].font.bold = True
        hrow6.cells[i].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(hrow6.cells[i], "1A365D")
        hrow6.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)

    sig_bg = {"Strong Buy": "F0FFF4", "Buy": "EBF8FF", "Hold": "FFFAF0", "Watch": "FAF5FF"}
    for co, tkr, layer, sig, upside, thesis, tf, ph in SIGNALS:
        row = tbl6.add_row()
        bg = sig_bg.get(sig, "FFFFFF")
        for j, v in enumerate([co, tkr, layer, sig, upside, tf, thesis]):
            row.cells[j].text = v
            r = row.cells[j].paragraphs[0].runs[0]
            r.font.size = Pt(9)
            if j in (0, 3, 4):
                r.font.bold = True
            set_cell_bg(row.cells[j], bg)

    # ══════════════════════════════════════════════════════
    # 7. AI 학습 커리큘럼 완료 현황
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("7. AI SCM 학습 커리큘럼 — 전 과정 완료")

    body("AI 공급망 인텔리전스 이해를 위한 8개 전략 주제를 Lv.1(기초)~Lv.3(전문가)로 "
         "완주하였습니다. 총 24단계, 매 30분 cron 자동화 이메일 시스템으로 운영되었습니다.")
    doc.add_paragraph("")

    tbl7 = doc.add_table(rows=0, cols=3)
    tbl7.style = 'Table Grid'
    hrow7 = tbl7.add_row()
    for i, h in enumerate(["주제", "완료 레벨", "핵심 학습 내용"]):
        hrow7.cells[i].text = h
        hrow7.cells[i].paragraphs[0].runs[0].font.bold = True
        hrow7.cells[i].paragraphs[0].runs[0].font.size = Pt(10)
        set_cell_bg(hrow7.cells[i], "1A365D")
        hrow7.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)

    for i, (topic, status, detail) in enumerate(CURRICULUM):
        row = tbl7.add_row()
        bg = "F0FFF4" if i % 2 == 0 else "FFFFFF"
        for j, v in enumerate([topic, status, detail]):
            row.cells[j].text = v
            r = row.cells[j].paragraphs[0].runs[0]
            r.font.size = Pt(10)
            if j == 0:
                r.font.bold = True
            set_cell_bg(row.cells[j], bg)

    doc.add_paragraph("")
    h2("학습 시스템 구성")
    bullet("Progress Agent: 24일 × 3라운드 진도 추적, 퀴즈 스코어 관리")
    bullet("News Agent: RSS 5개 소스 실시간 AI SCM 뉴스 수집 + seed fallback")
    bullet("Study Email Agent: Lv.1~3 레벨별 심화 콘텐츠 + COMPACT_RECAP 비중복 설계")
    bullet("30분 cron: 자동 발송 + Word/HTML 동시 산출 + 뉴스 연동")
    bullet("산출물: DOCX 24개 + HTML 프리뷰 + 진도 추적 JSON")

    # ══════════════════════════════════════════════════════
    # 8. 리스크 매트릭스
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("8. 리스크 매트릭스")

    body("AI 공급망 투자 관련 핵심 리스크를 확률(Likelihood) × 영향(Impact) 기준으로 분류합니다.")
    doc.add_paragraph("")

    risk_tbl = doc.add_table(rows=0, cols=3)
    risk_tbl.style = 'Table Grid'
    rh = risk_tbl.add_row()
    for j, h_text in enumerate(["구분", "리스크 항목", "대응 방향"]):
        rh.cells[j].text = h_text
        rh.cells[j].paragraphs[0].runs[0].font.bold = True
        rh.cells[j].paragraphs[0].runs[0].font.size = Pt(10)
        set_cell_bg(rh.cells[j], "1A365D")
        rh.cells[j].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)

    risk_rows = [
        ("고확률·고영향\n(즉시 대응)", "E53E3E",
         RISKS["HH"],
         "포트폴리오 비중 조정, 헤지 전략 수립"),
        ("고확률·저영향\n(관리)", "3182CE",
         RISKS["HL"],
         "모니터링 강화, 비용 관리"),
        ("저확률·고영향\n(모니터링)", "DD6B20",
         RISKS["LH"],
         "시나리오 플랜 B 수립, 조기 경보 지표 설정"),
        ("저확률·저영향\n(관찰)", "38A169",
         RISKS["LL"],
         "분기별 리뷰, 일상 모니터링"),
    ]
    for (quad, bg, items, action) in risk_rows:
        row = risk_tbl.add_row()
        row.cells[0].text = quad
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[0].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row.cells[0], bg)
        row.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xff, 0xff, 0xff)
        row.cells[1].text = "\n".join(f"• {it}" for it in items)
        row.cells[1].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row.cells[1], "FFFFFF")
        row.cells[2].text = action
        row.cells[2].paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(row.cells[2], "F7F8FA")

    # ══════════════════════════════════════════════════════
    # 9. 결론 및 전략 권고
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("9. 결론 및 전략 권고")

    h2("8.1 핵심 결론")
    bullet("현재 AI 공급망은 역사적으로 가장 집약된 병목 구간 — HBM·CoWoS·전력 3중 병목 동시 진행")
    bullet("하이퍼스케일러 $392B CapEx는 공급망 전체에 걸쳐 균등하지 않게 분배 — 병목 레이어 집중 수혜")
    bullet("Phase 2~3 전환기는 복수 섹터 동시 투자 기회 — 단순 GPU 보유보다 공급망 다각화가 우월")
    bullet("소버린 AI(UAE·Saudi·EU)와 엣지 AI가 Phase 4의 핵심 드라이버로 부상 중")

    doc.add_paragraph("")
    h2("8.2 투자 우선순위 (2026년 기준)")

    priority = [
        ("최우선 (6~12개월)", "Strong Buy",
         "SK Hynix: HBM3e 50% 점유, GB200 핵심 수혜, HBM4 퀄 2026\n"
         "근거: 공급 제약이 가장 명확, 대체재 없음, 수요 가시성 최고"),
        ("우선 (6~18개월)", "Buy",
         "Vertiv / GE Vernova / Eaton: 전력 인프라 병목 직접 수혜\n"
         "TSMC CoWoS: 패키징 독점, AI칩 100% 통과\n"
         "Marvell / Broadcom: 커스텀 ASIC + 800G 네트워킹"),
        ("중기 (12~24개월)", "Buy/Hold",
         "Micron: HBM3e 점유율 확대 진행 중 — 실행 리스크 모니터링\n"
         "NVIDIA: Blackwell 전환 완료 후 재평가 — 단기 밸류 부담"),
        ("장기 (24개월+)", "Watch",
         "Qualcomm: 엣지 AI 파도 대비 — AI PC 교체 사이클 + 자동차 AI\n"
         "소버린 AI 관련 로컬 클라우드·인프라 기업"),
    ]
    for tier, sig, detail in priority:
        h3(f"{tier} — {sig}")
        body(detail)
        doc.add_paragraph("")

    h2("8.3 주요 리스크")
    bullet("HBM: Samsung의 HBM3e 수율 개선 속도 → SK Hynix 독점 완화 가능성")
    bullet("지정학: 대만 리스크(TSMC CoWoS), 미중 무역 분쟁(중국 HBM 수출 통제)")
    bullet("기술 불확실성: 메모리 내 컴퓨팅(PIM/CXL) 가속 시 HBM 수요 구조 변화")
    bullet("경기 침체: 광고 수익 의존 하이퍼스케일러(Meta·Google) CapEx 감축 리스크")
    bullet("전력 허가: DC 전력 인허가 지연 → 전력 인프라 투자 타임라인 불확실성")

    # ══════════════════════════════════════════════════════
    # 9. 참고 데이터 출처
    # ══════════════════════════════════════════════════════
    doc.add_page_break()
    h1("9. 참고 데이터 출처")

    sources = [
        ("NVIDIA Investor Relations", "quarterly earnings, GPU 공급 현황, Blackwell 로드맵"),
        ("SK Hynix Newsroom", "HBM3e 출하량, HBM4 개발 로드맵, 가동률"),
        ("TSMC Annual Report / IR", "CoWoS 캐파 확장 계획, N3/N2 수율"),
        ("Goldman Sachs AI Power Report", "데이터센터 전력 수요 2030 전망, 160GW 추정"),
        ("Sequoia Capital (AI's $600B Question)", "AI 인프라 투자 ROI 분석, 수익화 갭"),
        ("Bloomberg AI Investment Data", "하이퍼스케일러 CapEx 추적, 61개사 네트워크"),
        ("IDC Worldwide Quarterly Tracker", "PC 출하량, AI PC 침투율, SSD TAM"),
        ("TrendForce NAND Report", "NAND 계약가격, 공급업체별 비트 출하, HBM 시황"),
        ("USB-IF Adopter Survey", "USB4/Thunderbolt4 보급률"),
        ("Counterpoint Research", "스마트폰 microSD 슬롯 보급률"),
        ("JP Morgan / Tax Foundation", "관세 정책, 가계 부담 분석"),
    ]
    for src, desc in sources:
        p = doc.add_paragraph()
        r1 = p.add_run(f"• {src}: ")
        r1.font.bold = True
        r1.font.size = Pt(10)
        r2 = p.add_run(desc)
        r2.font.size = Pt(10)
        p.paragraph_format.space_after = Pt(3)

    doc.add_paragraph("")
    divider()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"본 보고서는 공개 데이터 및 AI 모델 분석 기반으로 작성되었으며, 투자 권유가 아닙니다. | {DATE_KR}")
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    out = OUT_DIR / f"AI_SCM_Final_Report_{DATE_STR}.docx"
    doc.save(str(out))
    print(f"  DOCX: {out}")
    return out


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f" AI SCM 최종 보고서 생성  |  {DATE_KR}")
    print(f"{'='*55}")

    pptx_path = make_pptx()
    docx_path = make_docx()

    print(f"\n  출력 디렉토리: {OUT_DIR}")
    print("  완료.")

    if args.open:
        import subprocess
        subprocess.run(["open", str(pptx_path)])
        subprocess.run(["open", str(docx_path)])
