"""
AI 공급망 투자 프레임워크 & 포트폴리오 전략 심화 Study Agent
대상: 반도체 마케팅 종사자 (비즈니스 배경 ○, 투자 프레임워크 심화)

학습 목표:
  - AI 공급망 투자 파동(Phase 1~5)을 체계적으로 이해
  - 레이어별 투자 타이밍과 핵심 지표를 도출하는 프레임워크 습득
  - 종목별 투자 매트릭스와 포트폴리오 구성 전략 실무 적용

출력: outputs/reports/study_investment_framework_YYYYMMDD.docx
"""
import os, sys
from datetime import date
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

OUTPUT_DIR = Path(__file__).parent.parent.parent / "outputs" / "reports"

# ──────────────────────────────────────────────────────────────
# 참고자료
# ──────────────────────────────────────────────────────────────
REFS = {
    "JPMorgan_AI_Supercycle": (
        "JP Morgan — AI Supercycle Report 2025",
        "https://www.jpmorgan.com/insights/technology/artificial-intelligence/ai-supercycle",
        "AI 투자 사이클 5단계 프레임워크, 2025-2027 CapEx 전망, 종목별 목표주가", "2025"
    ),
    "Goldman_AI_200B": (
        "Goldman Sachs — AI Infrastructure $200B Opportunity",
        "https://www.goldmansachs.com/insights/articles/generative-ai-infrastructure",
        "AI 인프라 $200B 시장 규모 분석, 공급망 레이어별 수혜 종목 분류", "2024"
    ),
    "Bernstein_Semis": (
        "Bernstein Research — Semiconductor Deep Dive 2024",
        "https://www.bernsteinresearch.com/semiconductor-deep-dive",
        "NVDA, AVGO, MU, SKH 등 반도체 종목 밸류에이션·성장률 심층 분석", "2024"
    ),
    "Morgan_Stanley_AI": (
        "Morgan Stanley — AI Winners & Losers 2025",
        "https://www.morganstanley.com/ideas/ai-winners-losers",
        "AI 공급망 수혜·피해 종목 분류, Phase별 투자 전략, 리스크 분석", "2025"
    ),
    "Gartner_HypeCycle": (
        "Gartner — Hype Cycle for Artificial Intelligence 2025",
        "https://www.gartner.com/en/articles/what-s-new-in-artificial-intelligence-from-the-2024-gartner-hype-cycle",
        "AI 기술 성숙도 곡선, 버블 리스크 평가, 실질 가치 창출 타임라인", "2025"
    ),
    "Bloomberg_AI_Tracker": (
        "Bloomberg Intelligence — AI Investment Tracker",
        "https://www.bloomberg.com/professional/blog/ai-investment-tracker/",
        "하이퍼스케일러 CapEx 분기별 추적, AI 인프라 지출 선행 지표", "2024-2025"
    ),
    "NVIDIA_IR": (
        "NVIDIA — Investor Relations",
        "https://investor.nvidia.com/",
        "NVDA 분기 실적, 데이터센터 매출, 가이던스. 주가 $15(2023초) → $135(2025초)", "2025"
    ),
    "SKHynix_IR_2024": (
        "SK Hynix — Investor Relations FY2024",
        "https://www.skhynix.com/eng/ir/financialHighlights.do",
        "HBM 매출 비중 2023 5% → 2025 40%+, ASP 프리미엄 추이", "2024-2025"
    ),
    "TSMC_IR": (
        "TSMC — Investor Relations",
        "https://investor.tsmc.com/",
        "CoWoS 캐파, 선단 공정 가동률, CapEx 계획. AI 수요 가시성 코멘트", "2024-2025"
    ),
    "Vertiv_IR": (
        "Vertiv Holdings — Investor Relations",
        "https://ir.vertiv.com/",
        "AI 데이터센터 전력·냉각 인프라 수주잔고, Phase 3 수혜 정량화", "2024-2025"
    ),
    "AMD_IR": (
        "AMD — Investor Relations",
        "https://ir.amd.com/",
        "MI300X AI GPU 출하, NVIDIA 대안 포지션, 데이터센터 매출 성장", "2024-2025"
    ),
    "Micron_IR": (
        "Micron Technology — Investor Relations",
        "https://investors.micron.com/",
        "HBM3e 수율 개선, CHIPS Act 보조금, AI 서버 DRAM 수요 전망", "2024-2025"
    ),
    "SemiAnalysis_CapEx": (
        "SemiAnalysis — Hyperscaler CapEx Deep Dive",
        "https://www.semianalysis.com/p/hyperscaler-capex-deep-dive",
        "AWS·Azure·GCP·Meta CapEx 분기별 분석, AI 인프라 구성 비율", "2024"
    ),
    "TrendForce_AI_Server": (
        "TrendForce — AI Server Shipment Forecast",
        "https://www.trendforce.com/research/server.html",
        "AI 서버 출하량 2023-2027 전망, GPU 서버 vs 일반 서버 비중", "2024"
    ),
    "GE_Vernova_IR": (
        "GE Vernova — Investor Relations",
        "https://www.gevernova.com/investors",
        "AI 데이터센터 전력 수요로 Grid 장비 수주잔고 급증 데이터", "2024-2025"
    ),
}


# ──────────────────────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────────────────────
def _add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    return h

def _add_table(doc, headers, rows):
    if not rows:
        return
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = "Table Grid"
    for i, h in enumerate(headers):
        c = tbl.rows[0].cells[i]
        c.text = h
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "1F4E79")
        c._tc.get_or_add_tcPr().append(shd)
        for run in c.paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(10)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for ri, row in enumerate(rows):
        tr = tbl.rows[ri + 1]
        for ci, val in enumerate(row):
            tr.cells[ci].text = str(val)
            if tr.cells[ci].paragraphs[0].runs:
                tr.cells[ci].paragraphs[0].runs[0].font.size = Pt(9)
    doc.add_paragraph()

def _box(doc, label, color_fill, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Cm(0.8)
    p.paragraph_format.right_indent = Cm(0.8)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color_fill)
    p._p.get_or_add_pPr().append(shd)
    r1 = p.add_run(f"[{label}] ")
    r1.bold = True
    r1.font.size = Pt(9)
    r2 = p.add_run(text)
    r2.font.size = Pt(9)
    r2.italic = True

def _concept(doc, text):
    _box(doc, "개념", "E8F0FE", text)

def _marketing(doc, text):
    _box(doc, "마케터 관점", "E8F5E9", text)

def _quant(doc, text):
    _box(doc, "계산 예제", "FFF9C4", text)

def _risk(doc, text):
    _box(doc, "주의", "FFF3E0", text)

def _add_refs(doc, keys):
    refs = [REFS[k] for k in keys if k in REFS]
    if not refs:
        return
    doc.add_paragraph("참고자료", style="Heading 3")
    rows = [(n, url, desc, yr) for n, url, desc, yr in refs]
    tbl = doc.add_table(rows=1 + len(rows), cols=4)
    tbl.style = "Table Grid"
    for i, h in enumerate(["출처", "URL", "설명", "연도"]):
        c = tbl.rows[0].cells[i]
        c.text = h
        for r in c.paragraphs[0].runs:
            r.bold = True
            r.font.size = Pt(9)
    for ri, (name, url, desc, yr) in enumerate(rows):
        tr = tbl.rows[ri + 1]
        tr.cells[0].text = name
        p = tr.cells[1].paragraphs[0]
        run = p.add_run(url)
        run.font.color.rgb = RGBColor(0, 70, 180)
        run.font.size = Pt(7)
        tr.cells[2].text = desc
        tr.cells[3].text = yr
        for ci in [0, 2, 3]:
            if tr.cells[ci].paragraphs[0].runs:
                tr.cells[ci].paragraphs[0].runs[0].font.size = Pt(8)
    doc.add_paragraph()

def _quiz_section(doc, questions):
    _add_heading(doc, "복습 문제 (능동적 학습)", 2)
    doc.add_paragraph(
        "아래 질문에 먼저 스스로 답해보고, 힌트를 확인하세요. "
        "답을 '설명할 수 있으면' 이해한 것입니다 (페인만 기법)."
    )
    for i, (q, hint, answer_type) in enumerate(questions, 1):
        p = doc.add_paragraph()
        r = p.add_run(f"Q{i}. {q}")
        r.bold = True
        r.font.size = Pt(10)
        p2 = doc.add_paragraph()
        r2 = p2.add_run(f"  힌트: {hint}")
        r2.font.size = Pt(9)
        r2.font.color.rgb = RGBColor(80, 80, 80)
        r2.italic = True
        p3 = doc.add_paragraph()
        r3 = p3.add_run(f"  유형: {answer_type}")
        r3.font.size = Pt(8)
        r3.font.color.rgb = RGBColor(120, 120, 120)
        doc.add_paragraph()


# ──────────────────────────────────────────────────────────────
# 메인 빌드 함수
# ──────────────────────────────────────────────────────────────
def build(level=1):
    if not DOCX_AVAILABLE:
        print("  [Investment Framework Study] python-docx 미설치")
        return None

    level_prefix = {1: "", 2: "[Lv.2 심화] ", 3: "[Lv.3 전문가] "}.get(level, "")

    doc = Document()
    for s in doc.sections:
        s.top_margin    = Cm(2.5)
        s.bottom_margin = Cm(2.5)
        s.left_margin   = Cm(3.0)
        s.right_margin  = Cm(2.5)

    # ── 표지 ──────────────────────────────────────────────────
    doc.add_paragraph()
    t = doc.add_heading(f"{level_prefix}AI 공급망 투자 프레임워크 & 포트폴리오 전략", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s = doc.add_paragraph("Phase별 투자 파동 분석부터 종목 매트릭스까지 — 실전 포트폴리오 구성")
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s2 = doc.add_paragraph(
        f"대상: 반도체 마케팅 종사자  |  기준일: {config.AS_OF_DATE}  |  "
        f"난이도: 투자 기초 → 실전 프레임워크"
    )
    s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in s2.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(100, 100, 100)

    desc = doc.add_paragraph(
        "\n본 문서는 AI 공급망 투자를 체계적으로 접근하기 위한 프레임워크 학습 자료입니다. "
        "8주간의 AI 공급망 학습(HBM, 전력·냉각, 파운드리, 네트워킹, 지정학)을 투자 관점으로 "
        "통합하고, 실전 포트폴리오 구성 전략을 제시합니다."
    )
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in desc.runs:
        run.font.size = Pt(9)
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 1장. 투자 파동 프레임워크
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "1장. 투자 파동 프레임워크 — AI 공급망 5단계 사이클")

    doc.add_paragraph(
        "AI 인프라 투자는 단일 사건이 아니라 '파동(Wave)'으로 진행됩니다. "
        "각 파동은 직전 파동의 병목을 해소하며 다음 병목을 드러냅니다. "
        "이 구조를 이해하면 '지금 어느 파동에 있는가'를 진단하고 "
        "다음 수혜 섹터를 선행적으로 포지셔닝할 수 있습니다."
    )

    _add_heading(doc, "1.1 Phase 1~5 전체 지도", 2)
    phase_rows = [
        ["Phase 1", "GPU 확보 전쟁",        "2022-2023",
         "H100 수요 폭발, TSMC 4nm 병목",
         "NVIDIA (+400%), TSMC (+80%)",
         "GPU 가용성, TSMC 수주잔고"],
        ["Phase 2", "메모리 병목 해소",      "2023-2024",
         "HBM3e 공급 부족, CoWoS 캐파 제약",
         "SK하이닉스 (+150%), TSMC",
         "HBM 리드타임, CoWoS WPM"],
        ["Phase 3", "전력·냉각 인프라",      "2024-2025",
         "AI 데이터센터 전력 수요 급증",
         "Vertiv (+300%), GE Vernova (+200%)",
         "전력 수주잔고, 냉각 리드타임"],
        ["Phase 4", "네트워킹 업그레이드",   "2025-2026",
         "NDR→XDR, 800GbE AI 클러스터",
         "Broadcom, Arista, NVIDIA IB",
         "GB200 출하, UEC 표준 확정"],
        ["Phase 5", "엣지·추론·로보틱스",    "2026-2027",
         "온디바이스 AI, 자율주행, 휴머노이드",
         "ARM, Qualcomm, Marvell, Boston Dynamics",
         "추론칩 출하, 엣지 AI 침투율"],
    ]
    _add_table(doc,
        ["단계", "테마", "주요 시기", "핵심 내용", "주요 수혜 (예시)", "선행 지표"],
        phase_rows)

    _add_heading(doc, "1.2 파동의 논리 — 왜 순차적으로 발생하는가", 2)
    _concept(doc,
        "파동이 순차적으로 발생하는 이유:\n"
        "① 병목 해소 → 새 병목 노출: GPU를 충분히 확보하면 메모리(HBM)가 부족해짐.\n"
        "② 설비 투자 리드타임: 공장 증설에 12-24개월 필요 → 선행 투자 선행 수혜.\n"
        "③ 수요 가시성: 하이퍼스케일러 CapEx 발표 → 6-12개월 후 부품 주문 → 수혜 반영.")
    _marketing(doc,
        "반도체 마케팅 관점: '지금 고객사의 병목이 무엇인가'를 파악하면 "
        "다음 파동의 수혜 제품을 예측할 수 있습니다. "
        "Phase 3(전력) 병목 해소 중인 지금(2025), Phase 4(네트워킹) 제품 포지셔닝이 필요합니다.")
    _quant(doc,
        "파동별 주가 선행성:\n"
        "  관찰: 병목 인식 시점에서 해당 섹터 주가 피크까지 평균 6-9개월\n"
        "  Phase 1 예시: 2022.11 ChatGPT 출시 → 2023.05 NVIDIA 주가 +200%\n"
        "  Phase 2 예시: 2023.Q3 HBM 병목 확인 → 2024.Q1 SK하이닉스 최고점\n"
        "  Phase 3 예시: 2024.Q1 전력 부족 뉴스 → 2024.Q3 Vertiv 최고점 (+300%)")

    _add_refs(doc, ["JPMorgan_AI_Supercycle", "Goldman_AI_200B"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 2장. 공급망 레이어별 투자 타이밍
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "2장. 공급망 레이어별 투자 타이밍 — 병목 사이클 vs 주가")

    doc.add_paragraph(
        "AI 공급망은 여러 레이어로 구성됩니다. "
        "각 레이어의 병목 발생 → 주가 선행 → 피크 → 해소 사이클을 "
        "이해하면 레이어 간 로테이션(Rotation) 전략을 구사할 수 있습니다."
    )

    _add_heading(doc, "2.1 공급망 레이어 구조", 2)
    layer_rows = [
        ["L1: 설계/IP",     "ARM, Synopsys, Cadence",    "GPU·AI칩 설계 IP",  "높음", "낮음",  "경기 방어적, 프리미엄 유지"],
        ["L2: 파운드리",     "TSMC, 삼성, 인텔",           "GPU·HBM 제조",      "높음", "중간",  "CoWoS 캐파가 핵심 지표"],
        ["L3: 소재/장비",    "ASML, AMAT, Lam, KLA",      "팹 장비·소재",      "중간", "높음",  "TSMC CapEx와 12개월 시차"],
        ["L4: 메모리",       "SK하이닉스, 삼성, Micron",   "HBM, DRAM, NAND",   "높음", "높음",  "HBM ASP·수율이 핵심"],
        ["L5: GPU·AI칩",     "NVIDIA, AMD, Intel",         "AI 가속기",         "높음", "높음",  "데이터센터 매출 가이던스"],
        ["L6: 패키징",       "ASE, Amkor, TSMC CoWoS",    "CoWoS, SoIC 패키징", "높음", "중간", "CoWoS WPM, 리드타임"],
        ["L7: 시스템",       "Supermicro, Dell, HP",      "AI 서버·랙",        "중간", "높음",  "출하량, 수주잔고"],
        ["L8: 네트워킹",     "NVIDIA IB, Broadcom, Arista","AI 클러스터 연결",  "낮음", "높음",  "GB200 채택, 800GbE 전환"],
        ["L9: 전력·냉각",    "Vertiv, Eaton, GE Vernova", "데이터센터 인프라",  "낮음", "중간",  "수주잔고 증가율"],
        ["L10: 클라우드",    "AWS, Azure, GCP, Meta",     "AI 서비스 플랫폼",   "낮음", "낮음",  "CapEx 규모, AI 매출화"],
    ]
    _add_table(doc,
        ["레이어", "주요 기업", "역할", "AI 수혜 강도", "변동성", "핵심 관찰 지표"],
        layer_rows)

    _add_heading(doc, "2.2 레이어별 투자 타이밍 원칙", 2)
    _marketing(doc,
        "원칙 1 — 선행 레이어부터 투자: 설비 투자(L3 장비) → 제조(L2 파운드리) → "
        "부품(L4 메모리, L6 패키징) → 완제품(L5 GPU) → 시스템(L7) → 인프라(L8~L9).")
    _marketing(doc,
        "원칙 2 — 병목 레이어 집중: 현재 병목인 레이어가 최고 마진·최대 주가 상승 구간. "
        "병목 해소 신호가 나오면 다음 레이어로 로테이션 준비.")
    _marketing(doc,
        "원칙 3 — CapEx 발표 추적: 하이퍼스케일러(AWS, Azure, GCP, Meta) CapEx 발표 → "
        "6개월 후 L3(장비) 주문, 12개월 후 L4(메모리) 주문, 18개월 후 L5(GPU) 출하.")

    _add_refs(doc, ["Bloomberg_AI_Tracker", "SemiAnalysis_CapEx", "JPMorgan_AI_Supercycle"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 3장. 핵심 투자 지표
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "3장. 핵심 투자 지표 — 무엇을 보면 사이클을 알 수 있나")

    doc.add_paragraph(
        "AI 공급망 투자에서 사이클 위치를 판단하는 정량 지표들을 정리합니다. "
        "이 지표들은 분기 실적 발표, IR 자료, 업계 리포트에서 직접 확인할 수 있습니다."
    )

    _add_heading(doc, "3.1 CapEx 성장률 — 가장 강력한 선행 지표", 2)
    _concept(doc,
        "하이퍼스케일러 CapEx(자본지출)는 AI 공급망 수요의 원천입니다. "
        "이들이 'AI에 얼마나 쓰겠다'고 발표하는 순간 공급망 전체가 반응합니다.")
    capex_rows = [
        ["Microsoft",  "$75B (FY2025E)",  "+50% YoY", "Azure AI, Copilot 인프라"],
        ["Meta",       "$60-65B (2025E)", "+55% YoY", "AI 추천, LLaMA 학습 클러스터"],
        ["Google",     "$75B (2025E)",    "+43% YoY", "GCP AI, TPU 확장"],
        ["Amazon",     "$100B (2025E)",   "+36% YoY", "AWS AI, Trainium/Inferentia"],
        ["합계",       "~$310B (2025E)",  "+44% YoY", "역대 최대 규모"],
    ]
    _add_table(doc, ["기업", "CapEx 규모", "성장률", "주요 용도"], capex_rows)

    _add_heading(doc, "3.2 가동률 & 리드타임 — 공급 병목 실시간 지표", 2)
    _concept(doc,
        "가동률(Utilization Rate): 생산 설비가 얼마나 사용되고 있는가.\n"
        "• 90%+ = 심각한 공급 부족 → 가격 상승, 마진 확대\n"
        "• 80-90% = 타이트한 공급 → 공급사 우위\n"
        "• 70-80% = 균형\n"
        "• 70% 미만 = 공급 과잉 → 가격 하락 압력")
    util_rows = [
        ["TSMC CoWoS",          "~95% (2024)",  "AI GPU 패키징 극심한 병목", "18개월"],
        ["SK하이닉스 HBM 전용라인","~98% (2024)", "수요 > 공급 지속",         "12-18개월"],
        ["TSMC 3nm/4nm",        "~85% (2024)",  "AI GPU + 스마트폰 혼재",   "6-12개월"],
        ["메모리 DDR5 (범용)",   "~75% (2024)",  "AI외 수요 회복 중",        "3-6개월"],
        ["Vertiv 냉각 장비",     "~90% (2024)",  "AI 데이터센터 급증 대응",  "12-18개월"],
    ]
    _add_table(doc, ["부문", "추정 가동률", "현황", "리드타임"], util_rows)

    _add_heading(doc, "3.3 재고 사이클 — 다운사이클 조기 경보", 2)
    _concept(doc,
        "반도체 재고 사이클: 공급이 수요를 초과하면 채널 재고가 쌓이고 가격이 하락합니다.\n"
        "• 재고 증가 + 가이던스 하향 → 주가 선행 하락 (통상 2-3분기 전)\n"
        "• 재고 소진 + 가이던스 상향 → 주가 반등 시작")
    _risk(doc,
        "AI 사이클의 재고 위험: 하이퍼스케일러들이 GPU를 과도하게 선주문(Over-ordering)하는 경향이 있습니다. "
        "실제 사용률이 주문량에 미치지 못하면 취소/연기 → 공급사 실적 충격. "
        "Gartner Hype Cycle 상단 도달 시 이 위험이 가장 높습니다.")

    _add_refs(doc, ["Gartner_HypeCycle", "Bernstein_Semis", "TrendForce_AI_Server"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 4장. 종목별 투자 매트릭스
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "4장. 종목별 투자 매트릭스")

    doc.add_paragraph(
        "AI 공급망 핵심 9개 종목을 레이어, 투자 등급, 목표주가, 촉매, 리스크로 정리합니다. "
        "컨센서스 데이터(기준일: 2025년 초)를 기반으로 하며, 투자 판단 전 최신 데이터 확인이 필요합니다."
    )

    _add_heading(doc, "4.1 핵심 9개 종목 매트릭스", 2)
    stock_matrix = [
        ["NVIDIA (NVDA)",
         "L5 GPU·AI칩",
         "Strong Buy",
         "$200-250 (컨센서스 중앙값 $220)",
         "GB200 출하 가속, Sovereign AI, 소프트웨어(CUDA) 해자",
         "중국 규제 강화, AMD MI300X 점유율 확대, 밸류에이션 부담"],
        ["SK하이닉스 (000660.KS)",
         "L4 HBM 메모리",
         "Strong Buy",
         "₩250,000-300,000 (컨센서스 ₩270,000)",
         "HBM4 독점 공급, ASP 프리미엄 지속, NVIDIA 전용 공급자 지위",
         "삼성 HBM 인증 완료 시 점유율 일부 잠식, 한반도 지정학"],
        ["TSMC (TSM)",
         "L2 파운드리, L6 CoWoS",
         "Buy",
         "$200-220 ADR (컨센서스 $210)",
         "CoWoS 독점, 2nm 양산, CHIPS Act 보조금",
         "대만 지정학 리스크, 미국 팹 원가 상승, 인텔 경쟁"],
        ["Vertiv (VRT)",
         "L9 전력·냉각",
         "Buy",
         "$130-160 (컨센서스 $145)",
         "AI 데이터센터 전력 수요 폭증, 수주잔고 사상 최대",
         "AI 수요 둔화 시 수주잔고 연기, 원자재 비용 상승"],
        ["Broadcom (AVGO)",
         "L8 네트워킹 ASIC + 커스텀 AI 칩",
         "Buy",
         "$2,200-2,600 (분할 전 환산, 컨센서스 $2,400)",
         "하이퍼스케일러 커스텀 AI ASIC, 이더넷 스위칭 독점",
         "NVIDIA 이더넷 진출, 하이퍼스케일러 내재화"],
        ["Marvell (MRVL)",
         "L8 네트워킹 + 커스텀 AI 칩",
         "Buy",
         "$90-110 (컨센서스 $100)",
         "Amazon Trainium 네트워킹 수주, 800G 이더넷 PHY",
         "커스텀 ASIC 수주 집중 → 대형 고객 의존도 높음"],
        ["AMD (AMD)",
         "L5 GPU·AI칩 (NVIDIA 대안)",
         "Neutral~Buy",
         "$180-220 (컨센서스 $195)",
         "MI300X 대형 클라우드 채택 확대, ROCm 생태계 개선",
         "CUDA 생태계 장벽, NVIDIA 가격 인하 시 경쟁력 약화"],
        ["Micron (MU)",
         "L4 HBM + DRAM",
         "Buy (중장기)",
         "$130-160 (컨센서스 $145)",
         "CHIPS Act $6.1B 보조금, HBM3e 수율 개선, 미국산 프리미엄",
         "HBM 기술 격차, 범용 DRAM 가격 하락 위험"],
        ["GE Vernova (GEV)",
         "L9 전력 그리드",
         "Buy",
         "$300-380 (컨센서스 $340)",
         "AI 데이터센터 전력 수요로 Grid 장비 수주잔고 급증",
         "AI 수요 둔화, 에너지 정책 변화, 원자재 비용"],
    ]
    _add_table(doc,
        ["종목", "레이어", "투자 등급", "목표주가 컨센서스", "주요 촉매", "주요 리스크"],
        stock_matrix)

    _add_heading(doc, "4.2 NVIDIA 주가 여정 — 9배 상승의 교훈", 2)
    _quant(doc,
        "NVIDIA 주가 분석 (2023.01 → 2025.01):\n"
        "  시작: ~$15 (2023년 초, 분할 조정 기준)\n"
        "  최고점: ~$150 (2025년 초)\n"
        "  상승률: +900%+\n"
        "  핵심 드라이버: ChatGPT → H100 수요 → GB200 발표 → Sovereign AI\n"
        "  밸류에이션 변화: P/E 30x → P/E 45x (멀티플 확장 + 실적 성장 동시)\n"
        "  교훈: '비싸다'고 팔지 않고 촉매 추적이 더 중요했던 케이스")
    _marketing(doc,
        "반도체 마케터가 NVIDIA 주가 분석에서 유리한 점: "
        "GPU 수급 타이트함(리드타임 6개월 → 12개월)이 주가 상승의 선행 신호임을 "
        "현장에서 먼저 파악할 수 있습니다. '고객이 GPU 못 구한다'는 뉴스가 매수 신호.")

    _add_refs(doc, ["NVIDIA_IR", "SKHynix_IR_2024", "Bernstein_Semis", "Morgan_Stanley_AI"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 5장. 리스크 매트릭스
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "5장. 리스크 매트릭스 — AI 공급망 투자의 5대 위험")

    doc.add_paragraph(
        "모든 강세론은 리스크를 내포합니다. "
        "AI 공급망 투자의 5대 리스크를 발생 가능성 × 임팩트로 평가합니다."
    )

    risk_rows = [
        ["AI 버블 붕괴",
         "ROI 미증명, 하이퍼스케일러 CapEx 삭감",
         "중간 (30%)",
         "매우 높음 (-50%+)",
         "높음",
         "CapEx 가이던스 하향, 클라우드 AI 매출화 지연 신호 시 포지션 축소"],
        ["공급 과잉",
         "HBM/GPU 과잉 투자로 가격 급락",
         "중간 (35%)",
         "높음 (-30~50%)",
         "높음",
         "재고 일수 증가, 리드타임 단축, 가격 하락 추세 시 조기 경보"],
        ["수출 규제 강화",
         "H20 규제, 동맹국 포함 추가 제한",
         "높음 (55%)",
         "중간 (-15~25%)",
         "중간",
         "BIS 발표 모니터링, 중국 의존도 낮은 기업 비중 확대"],
        ["기술 전환 충격",
         "DeepSeek류 효율화, 새 아키텍처로 GPU 수요 감소",
         "낮음 (20%)",
         "중간 (-20~30%)",
         "중간",
         "새 모델 출시 시 GPU 수요 데이터 추적, Jevons Paradox 효과 확인"],
        ["에너지 정책",
         "탄소세, 데이터센터 전력 규제",
         "중간 (40%)",
         "낮음 (-10~20%)",
         "낮음",
         "에너지 효율 기술 수혜(액냉, 소형 원자로) 포지션 병행"],
    ]
    _add_table(doc,
        ["리스크", "설명", "발생 가능성", "임팩트(주가)", "종합 우선도", "대응 전략"],
        risk_rows)

    _add_heading(doc, "5.1 AI 버블 리스크 — Gartner Hype Cycle 위치", 2)
    _concept(doc,
        "Gartner Hype Cycle 2025 기준 생성형 AI 위치:\n"
        "• 현재: 'Peak of Inflated Expectations' 정상 또는 직전 단계\n"
        "• 다음: 'Trough of Disillusionment' (환멸 구간) 진입 가능성\n"
        "• 그러나 AI는 인터넷, 모바일과 유사하게 '실제 가치 창출' 단계 진입도 동시 진행\n"
        "• 핵심 구분: 하이퍼스케일러의 ROI 증거(AI로 인한 매출 증가) 확인이 필수")
    _risk(doc,
        "버블 신호 체크리스트:\n"
        "① 하이퍼스케일러 AI 매출화 지연 코멘트\n"
        "② GPU 리드타임 급격히 단축 (공급 증가 > 수요)\n"
        "③ 반도체 재고 일수 증가 추세 (3분기 연속)\n"
        "④ AI 스타트업 투자 급감 (선행 수요 지표)\n"
        "⑤ 애널리스트 컨센서스 목표주가 하향 추세")

    _add_refs(doc, ["Gartner_HypeCycle", "Goldman_AI_200B"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 6장. 시나리오 분석
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "6장. 시나리오 분석 — Bear/Base/Bull 수요 전망")

    doc.add_paragraph(
        "3개 시나리오로 2025-2027년 AI 반도체 수요를 전망하고 "
        "각 시나리오에서의 최적 투자 포지셔닝을 제시합니다."
    )

    _add_heading(doc, "6.1 3대 시나리오 비교", 2)
    scenario_rows = [
        ["Bull 시나리오",
         "30%",
         "AI 생산성 ROI 조기 증명, AGI 근접 발표",
         "GPU 수요 2x 초과, HBM 극심한 부족 지속",
         "NVDA $300+, SKH ₩350,000+",
         "NVIDIA, SK하이닉스, TSMC, Vertiv 모두 오버웨이트"],
        ["Base 시나리오",
         "50%",
         "AI 수요 견조, 효율화 병행, 규제 현상 유지",
         "GPU 수요 완만 성장, HBM 공급-수요 균형 접근",
         "NVDA $180-220, SKH ₩200,000-250,000",
         "품질 중심 선별 투자, Phase 4(네트워킹) 비중 확대"],
        ["Bear 시나리오",
         "20%",
         "AI ROI 미증명, CapEx 삭감, 중국 규제 강화",
         "GPU 과잉 공급, HBM 가격 급락",
         "NVDA $100 이하, SKH ₩120,000 이하",
         "방어적 포지션, 소프트웨어/서비스 헤지, 비중 축소"],
    ]
    _add_table(doc,
        ["시나리오", "확률", "핵심 가정", "반도체 수요", "예상 주가", "포지셔닝"],
        scenario_rows)

    _add_heading(doc, "6.2 Base 시나리오 상세 전망", 2)
    _quant(doc,
        "Base 시나리오 수요 추산 (AI GPU 기준):\n"
        "  2024 AI GPU 출하: H100급 ~150만개 + B100급 ~30만개\n"
        "  2025 AI GPU 출하 예상: H100급 ~100만개 + B200급 ~50-80만개\n"
        "  2026 AI GPU 출하 예상: B200급 ~100만개 + Rubin 조기 물량\n"
        "  HBM 수요 (2026E): ~$35-40B (2023 $5B 대비 7-8배)\n"
        "  AI 네트워킹 수요 (2026E): ~$22-25B (2023 $5B 대비 4-5배)")
    _marketing(doc,
        "Base 시나리오에서 최적 포지션:\n"
        "• 확신 보유(Conviction Hold): NVIDIA, SK하이닉스, TSMC (핵심 병목 공급자)\n"
        "• 비중 확대: Broadcom, Arista (Phase 4 네트워킹 전환 수혜)\n"
        "• 선택적 보유: Vertiv (Phase 3 이익 실현 후 비중 조정), Micron (장기 HBM 베팅)")

    _add_refs(doc, ["JPMorgan_AI_Supercycle", "Morgan_Stanley_AI", "TrendForce_AI_Server"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 7장. 포트폴리오 구성
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "7장. 포트폴리오 구성 — AI 공급망 집중형 vs 분산형")

    doc.add_paragraph(
        "AI 공급망 투자 포트폴리오를 어떻게 구성하는가에 따라 "
        "리스크 대비 수익 프로파일이 크게 달라집니다. "
        "두 가지 접근법을 비교하고 헤지 전략을 제시합니다."
    )

    _add_heading(doc, "7.1 집중형 포트폴리오 — 핵심 병목 집중", 2)
    _concept(doc,
        "집중형 전략: AI 공급망의 가장 확실한 병목(HBM + GPU + 파운드리)에 "
        "70-80% 비중을 집중합니다.")
    concentrate_rows = [
        ["NVIDIA",     "30%", "GPU 독점, 소프트웨어 해자, Phase 1-5 전 구간 수혜"],
        ["SK하이닉스", "20%", "HBM 1위, NVIDIA 전용 공급자, 구조적 ASP 우위"],
        ["TSMC",       "20%", "파운드리 독점, CoWoS 독점, CHIPS Act 보조금"],
        ["Broadcom",   "15%", "이더넷 ASIC + 커스텀 AI 칩 이중 수혜"],
        ["현금/헤지",   "15%", "버블 리스크 대비, 재진입 기회 확보"],
    ]
    _add_table(doc, ["종목/자산", "비중", "근거"], concentrate_rows)

    _add_heading(doc, "7.2 분산형 포트폴리오 — 파동 로테이션", 2)
    _concept(doc,
        "분산형 전략: AI 공급망 5개 레이어에 분산 투자하고, "
        "파동 변화에 따라 비중을 조절하는 적극적 관리 방식.")
    diversify_rows = [
        ["L5 GPU·AI칩",    "NVIDIA, AMD",               "25%", "Phase 1 핵심, 장기 보유"],
        ["L4 메모리",      "SK하이닉스, Micron",          "20%", "Phase 2 핵심, 중장기 보유"],
        ["L2/L6 파운드리", "TSMC",                       "15%", "Phase 1-4 전 구간 안정 수혜"],
        ["L8 네트워킹",    "Broadcom, Arista, Marvell",  "15%", "Phase 4 선행 포지셔닝"],
        ["L9 전력·냉각",   "Vertiv, GE Vernova",         "10%", "Phase 3 후반, 비중 점진 축소"],
        ["L3 장비",        "ASML, AMAT, Lam",            "5%",  "TSMC CapEx 선행 지표"],
        ["방어/헤지",      "현금, 국채, AI ETF 역방향",  "10%", "버블 헤지, 재진입 기회"],
    ]
    _add_table(doc, ["레이어", "종목", "비중", "전략"], diversify_rows)

    _add_heading(doc, "7.3 헤지 전략", 2)
    _marketing(doc,
        "헤지 도구 1 — 반도체 인버스 ETF: SOXS(3배 인버스) 소량 보유로 버블 붕괴 시 손실 제한. "
        "단, 레버리지 ETF는 장기 보유에 비적합 (음의 복리 효과).")
    _marketing(doc,
        "헤지 도구 2 — 소프트웨어 AI 수혜주 병행: MSFT, GOOGL은 AI CapEx를 지출하지만 "
        "AI 매출화 수혜도 직접 받음. 반도체 수요 둔화 시에도 일부 방어 기능.")
    _risk(doc,
        "집중형 포트폴리오의 위험: AI 버블 붕괴 시 상관관계 1에 수렴(동반 하락). "
        "현금 비중 15%+를 유지하고, 고점 대비 20%+ 하락 시 단계적 추가 매수 계획을 사전에 수립하세요.")

    _add_refs(doc, ["Goldman_AI_200B", "Morgan_Stanley_AI", "NVIDIA_IR"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 레벨별 심화 섹션 (8장 복습 문제 직전)
    # ══════════════════════════════════════════════════════════
    if level >= 2:
        _add_heading(doc, "심화 분석")
        doc.add_paragraph(
            "이 섹션은 Level 2 심화 과정으로, DCF 기반 AI 반도체 밸류에이션 방법과 "
            "Bottleneck 사이클에서의 주가 선행 패턴을 다룹니다."
        )

        _add_heading(doc, "DCF 기반 AI 반도체 밸류에이션 방법", 2)
        doc.add_paragraph(
            "AI 반도체 기업의 주가는 단순 P/E보다 DCF(Discounted Cash Flow)로 "
            "내재 가치를 추정하는 것이 더 정확합니다. "
            "SK하이닉스를 예시로 DCF 밸류에이션을 수행합니다."
        )
        doc.add_paragraph(
            "DCF 가정 (SK하이닉스, 2025년 기준):"
        )
        dcf_assumptions = [
            ["FCF (잉여현금흐름)", "2025E: ~12조원", "영업이익 20조 - CapEx 8조"],
            ["성장률 (Phase 2, 2025-2027)", "연 30%", "HBM4 수요 급증 구간"],
            ["성장률 (Phase 3, 2028-2030)", "연 15%", "HBM 시장 성숙"],
            ["성장률 (Terminal, 2031+)", "연 4%", "반도체 산업 장기 성장률"],
            ["할인율 (WACC)", "10%", "한국 대형주 + 반도체 리스크 프리미엄"],
            ["순차입금/자산", "2024년 기준 약 -5조 (순현금)", "IR 데이터"],
            ["발행주식수", "7.28억 주", "2024년 기준"],
        ]
        _add_table(doc, ["항목", "값", "근거"], dcf_assumptions)

        doc.add_paragraph("DCF 계산 결과:")
        dcf_result_rows = [
            ["2025E FCF", "12조원", ""],
            ["2026E FCF", "12 × 1.3 = 15.6조원", "+30% 성장"],
            ["2027E FCF", "15.6 × 1.3 = 20.3조원", "+30% 성장"],
            ["2028E FCF", "20.3 × 1.15 = 23.3조원", "+15% 성장"],
            ["2029E FCF", "23.3 × 1.15 = 26.8조원", "+15% 성장"],
            ["2030E FCF", "26.8 × 1.15 = 30.8조원", "+15% 성장"],
            ["Terminal Value (2031+)", "30.8조 × 1.04 / (0.10 - 0.04) = 533조원",
             "Gordon Growth Model"],
            ["5년 FCF PV 합계", "약 75조원", "할인율 10% 적용"],
            ["Terminal Value PV", "533조 / 1.1^6 ≈ 301조원", "6년 할인"],
            ["Enterprise Value", "약 376조원", "FCF PV + Terminal Value PV"],
            ["순현금 가산", "+5조원", "순차입금 반영"],
            ["Equity Value", "약 381조원", ""],
            ["주당 내재가치", "381조 ÷ 7.28억 = 약 52만원/주",
             "2025년 3월 시가 약 17만원 → 상당한 upside"],
        ]
        _add_table(doc, ["항목", "값", "비고"], dcf_result_rows)
        doc.add_paragraph(
            "주의사항: DCF는 가정에 매우 민감합니다. "
            "WACC 1% 변화 → 목표주가 10-15% 변동. "
            "성장률 가정이 실현되지 않으면 (AI 수요 둔화 시) 목표주가 급락. "
            "실무 활용: 목표주가 절대값보다 '현재 시장가 대비 implied 성장률'이 더 유용. "
            "17만원에서 implied 성장률 역산 → 시장이 너무 보수적인지 점검."
        )

        _add_heading(doc, "Bottleneck 사이클 주가 선행 패턴", 2)
        doc.add_paragraph(
            "AI 공급망에서 병목(Bottleneck)이 발생하고 해소되는 사이클에서 "
            "관련 기업 주가가 어떻게 선행하는지 패턴을 분석합니다."
        )
        bottleneck_rows = [
            ["병목 형성 신호",
             "① 리드타임 급증 (8주 → 18주 이상)\n"
             "② 공급사 가동률 90%+ 보도\n"
             "③ 고객사 재고 감소 + 구매 선계약 증가",
             "공식 발표 전 2-3개월",
             "수요 확인 후 주가 이미 선반영 시작"],
            ["주가 선행 1단계",
             "공급 병목 뉴스 플로우 증가. "
             "애널리스트 목표주가 상향 러시",
             "병목 공식 인정 시점",
             "이미 주가 30-50% 상승 후 뉴스 발표"],
            ["주가 피크",
             "공급사 CEO '수요가 공급 초과' 발언 최다 시점. "
             "증설 투자 발표 집중",
             "병목 최고점 (리드타임 최장)",
             "이미 6-9개월 전 주가 피크 가능"],
            ["병목 해소 신호",
             "① 증설 캐파 가동 시작\n"
             "② 리드타임 단축 (18주 → 12주)\n"
             "③ 재고 정상화 뉴스",
             "캐파 완공 후 3-6개월",
             "주가는 이미 6개월 전부터 하락 가능"],
            ["매도 타이밍",
             "CapEx 증설 발표 → 완공 예정일 역산 → "
             "완공 6개월 전부터 포지션 축소",
             "증설 착공 발표 후 12-18개월",
             "완공 시점이 아닌 '수요 회복 기대' 소멸 시점"],
        ]
        _add_table(doc, ["사이클 단계", "신호", "발생 시점", "투자 함의"],
                   bottleneck_rows)
        doc.add_paragraph(
            "실제 사례: HBM 병목 (2023-2024). "
            "SK하이닉스 주가: 2023년 1월 최저 → 2024년 7월 최고 (+250%). "
            "병목 뉴스 절정: 2024년 3-4월. 이미 주가는 최고점 근처. "
            "CoWoS 병목: TSMC 주가 선행 6개월. "
            "패턴 활용법: 병목 형성 초기(리드타임 급증 시점)에 매수, "
            "증설 발표 6개월 후 매도."
        )

    if level >= 3:
        _add_heading(doc, "전문가 심층 분석")
        doc.add_paragraph(
            "이 섹션은 Level 3 전문가 과정으로, Kelly Criterion을 AI 반도체 포트폴리오에 "
            "적용하는 방법과 Phase 5(물리적 AI·로보틱스) 투자 준비를 다룹니다."
        )

        _add_heading(doc, "Kelly Criterion 적용 AI 반도체 포트폴리오", 2)
        doc.add_paragraph(
            "Kelly Criterion은 수학적으로 최적 배팅 비율을 계산하는 공식입니다. "
            "AI 반도체 투자에 적용하여 포트폴리오 비중을 결정합니다."
        )
        doc.add_paragraph("Kelly 공식: f* = (bp - q) / b")
        doc.add_paragraph(
            "여기서: f* = 최적 투자 비중, b = 승리 시 이익 배율 (목표주가/현재가 - 1), "
            "p = 승리 확률, q = 패배 확률 (1 - p)"
        )
        doc.add_paragraph("주요 AI 반도체 종목별 Kelly 계산 (2025년 3월 기준 예시):")
        kelly_rows = [
            ["SK하이닉스",
             "목표주가 22만원, 현재 17만원 → b = 0.29",
             "p = 0.65 (HBM4 순조로운 전환 가정)",
             "f* = (0.29×0.65 - 0.35) / 0.29 = 0.45 → 45%",
             "Half-Kelly(실용적): 22.5%",
             "병목 사이클 확인 후 적용"],
            ["NVIDIA",
             "목표주가 $180, 현재 $130 → b = 0.38",
             "p = 0.60 (Blackwell 출하 정상화)",
             "f* = (0.38×0.60 - 0.40) / 0.38 = 0.55 → 55%",
             "Half-Kelly: 27.5%",
             "반독점 리스크 감안 Half-Kelly 권장"],
            ["TSMC",
             "목표주가 $300, 현재 $190 → b = 0.58",
             "p = 0.70 (CoWoS 독점 유지)",
             "f* = (0.58×0.70 - 0.30) / 0.58 = 0.18 → 18%",
             "Half-Kelly: 9%",
             "지정학 리스크로 확률 70% 보수적 적용"],
            ["Broadcom",
             "목표주가 $310, 현재 $230 → b = 0.35",
             "p = 0.55 (UEC 점유율 확대)",
             "f* = (0.35×0.55 - 0.45) / 0.35 = 0.26 → 26%",
             "Half-Kelly: 13%",
             "AI 네트워킹 전환 가속 가정"],
        ]
        _add_table(doc, ["종목", "이익 배율(b)", "승률(p)", "Full Kelly",
                          "Half Kelly (권장)", "비고"],
                   kelly_rows)
        doc.add_paragraph(
            "Half-Kelly 총 합계: 22.5% + 27.5% + 9% + 13% = 72%. "
            "나머지 28%는 현금/채권(헤지). "
            "Kelly의 실무 적용 주의: Full Kelly는 변동성 극도로 높음. "
            "Half Kelly 또는 Quarter Kelly가 실용적. "
            "확률 추정이 틀릴 수 있음 → 분산 투자로 리스크 제어. "
            "분기마다 p, b 값 재추정 → 비중 리밸런싱 필요."
        )

        _add_heading(doc, "Phase 5: 물리적 AI·로보틱스 투자 준비", 2)
        doc.add_paragraph(
            "AI 공급망 투자의 Phase 5는 AI가 디지털 세계를 넘어 "
            "물리적 세계(로봇, 자율주행, 제조)로 확장하는 단계입니다. "
            "이 Phase의 반도체 수요를 선행 분석합니다."
        )
        phase5_rows = [
            ["휴머노이드 로봇",
             "Figure AI, Tesla Optimus, Boston Dynamics, 1X Technologies",
             "2025-2028년",
             "로봇 1대당 AI SoC $200-500 + 모터 제어 칩 $100-200. "
             "2030년 100만 대 생산 시 반도체 수요 $3-7B/년",
             "NVIDIA (로봇 학습 GPU), Qualcomm (엣지 SoC), "
             "ISSI, ON Semi (모터 제어)"],
            ["자율주행 레벨 4-5",
             "Tesla FSD, Waymo, Mobileye, Baidu Apollo",
             "2026-2030년",
             "차량당 AI 반도체 $1,000-3,000. "
             "2030년 자율주행차 1,000만 대 시 $10-30B/년",
             "Mobileye (비전 AI), NVIDIA DRIVE, "
             "자율주행 SoC 파운드리 (TSMC N4)"],
            ["스마트 공장 (AI 제조)",
             "Fanuc, ABB, Siemens, 국내 HD현대",
             "2026-2029년",
             "생산라인당 AI 가속기 $50-200K. "
             "글로벌 스마트 공장 시장 $500B+ (2030)",
             "NVIDIA Jetson, Intel Movidius, "
             "산업용 엣지 AI 칩"],
            ["AR/VR (공간 컴퓨팅)",
             "Apple Vision Pro, Meta Quest, 삼성 XR",
             "2025-2028년",
             "헤드셋당 AI SoC $100-300. "
             "2028년 1억 대 판매 시 $10-30B/년",
             "Apple M4 SoC, Qualcomm Snapdragon XR, "
             "마이크론 LPDDR5X"],
        ]
        _add_table(doc, ["응용 분야", "주요 플레이어", "상용화 시기",
                          "반도체 수요 추정", "수혜 반도체 기업"],
                   phase5_rows)
        doc.add_paragraph(
            "Phase 5 투자 타이밍 신호:"
        )
        p5_signals = [
            "Tesla Optimus 양산 발표 + 수주 공개 → 로봇 AI 반도체 수요 가시화",
            "Waymo 또는 경쟁사 Level 4 상업화 도시 확장 → 자율주행 칩 대량 수요",
            "NVIDIA의 로봇 사업부 매출이 데이터센터의 10% 달성 → Phase 5 공식화",
            "주요 제조사의 AI 공장 라인 투자 CapEx $1B+ 발표 집중",
        ]
        for sig in p5_signals:
            doc.add_paragraph(f"• {sig}", style='List Bullet')
        doc.add_paragraph(
            "Phase 5 준비 포트폴리오 액션: "
            "현재 포트폴리오의 5-10%를 Phase 5 준비 종목으로 배분. "
            "NVIDIA (로봇 학습 GPU 이미 판매 중), Qualcomm (엣지 AI), "
            "Mobileye (자율주행 선두). "
            "국내 수혜: 레인보우로보틱스 (삼성 투자), 에스피지, HD현대로보틱스."
        )

    # ══════════════════════════════════════════════════════════
    # 8장. 퀴즈 & 종합 정리
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "8장. 퀴즈 & 8주 학습 종합 복습")

    doc.add_paragraph(
        "이 챕터는 8주간의 AI 공급망 학습(HBM 심화, 전력·냉각, 파운드리, "
        "네트워킹, 지정학, 투자 프레임워크)을 종합 복습합니다. "
        "각 주제의 핵심 포인트를 연결하여 통합적 투자 관점을 완성합니다."
    )

    _add_heading(doc, "8.1 8주 학습 핵심 키워드 총정리", 2)
    summary_rows = [
        ["Week 1: HBM 심화",
         "메모리 벽, TSV, CoWoS, SK하이닉스 52%, HBM3e 1,229GB/s, Phase 2 병목"],
        ["Week 2: AI 전력·냉각",
         "GB200 1kW/GPU, 액침냉각, 데이터센터 PUE, Vertiv Phase 3, 전력 수주잔고"],
        ["Week 3: TSMC & 파운드리",
         "CoWoS 독점, 2nm GAA, CHIPS Act, TSMC 60% 점유, 지정학 리스크"],
        ["Week 4: AI 소프트웨어 스택",
         "CUDA 독점, ROCm 도전, 추론 최적화, vLLM, TensorRT-LLM"],
        ["Week 5: AI 서버 & 시스템",
         "Supermicro, 랙급 설계, 액냉 통합, GB200 NVL72 구조"],
        ["Week 6: AI 네트워킹",
         "InfiniBand 80%, NVLink 5.0 1.8TB/s, UEC, Broadcom $8B, Phase 4"],
        ["Week 7: Sovereign AI & 지정학",
         "UAE $100B, CHIPS Act $53B, 중국 자립 30%, DeepSeek 쇼크, H20"],
        ["Week 8: 투자 프레임워크",
         "Phase 1-5 파동, CapEx $310B, 레이어 로테이션, Bear/Base/Bull, 포트폴리오"],
    ]
    _add_table(doc, ["주차/주제", "핵심 키워드 & 데이터"], summary_rows)

    questions = [
        (
            "AI 공급망 투자 Phase 1~5 중 현재(2025년 기준)가 어느 단계이며, "
            "다음 단계로의 전환을 알리는 3가지 선행 지표를 제시하라.",
            "1장의 Phase 테이블과 2장의 핵심 지표를 연결하세요. "
            "'현재 Phase 3 병목이 해소되고 있다'는 증거를 찾아보세요.",
            "사이클 분석 + 선행 지표"
        ),
        (
            "하이퍼스케일러 4개사(AWS, Azure, GCP, Meta)의 2025년 합산 CapEx $310B 중 "
            "AI GPU, HBM, 네트워킹, 전력·냉각에 각각 얼마가 배분되는지 추산하고, "
            "레이어별 수혜 기업을 연결하라.",
            "3장의 CapEx 데이터와 4장의 종목 매트릭스를 활용하세요. "
            "'AI 서버 비중 ~40%, 그 중 GPU ~60%, 메모리 ~20%' 구성을 참고하세요.",
            "정량 추산 + 기업 연결"
        ),
        (
            "NVIDIA 주가가 2023-2025년 9배 상승하는 동안 언제 매도 또는 비중 축소를 "
            "고려했어야 하는가? 구체적인 신호와 타이밍을 제시하라.",
            "5장의 리스크 매트릭스와 버블 신호 체크리스트를 활용하세요. "
            "'재고 일수', '리드타임', '가이던스' 변화를 중심으로 생각해보세요.",
            "매도 타이밍 분석"
        ),
        (
            "Bear 시나리오(확률 20%)에서 AI GPU 수요가 급감한다면 "
            "SK하이닉스, TSMC, Vertiv에 각각 어떤 영향이 있으며, "
            "이 시나리오에서 가장 방어적인 종목은 무엇인가?",
            "6장의 시나리오 분석과 각 기업의 AI 의존도를 비교하세요. "
            "'AI 비중이 낮을수록 방어적'이라는 단순 논리를 넘어서 "
            "각 기업의 대안 수요도 고려하세요.",
            "시나리오 분석 + 기업 비교"
        ),
        (
            "AI 공급망 집중형 포트폴리오(NVDA 30%, SKH 20%, TSMC 20%, AVGO 15%, 현금 15%)를 "
            "보유 중이다. DeepSeek R1 발표 직후 (NVDA -17% 하락) 어떻게 대응해야 하는가? "
            "매도, 보유, 추가 매수 중 하나를 선택하고 논리를 전개하라.",
            "Week 7의 DeepSeek 분석(Jevons Paradox)과 Week 8의 포트폴리오 헤지 전략을 활용하세요. "
            "'단기 충격 vs 장기 수요'를 구분하는 것이 핵심입니다.",
            "실전 의사결정"
        ),
        (
            "반도체 마케팅 담당자가 AI 공급망 투자에서 가진 정보 우위를 3가지 구체적으로 "
            "서술하고, 이를 어떻게 투자 알파(초과 수익)로 전환할 수 있는지 설명하라.",
            "매 챕터에 나온 '마케터 관점' 박스를 돌아보세요. "
            "고객 리드타임 정보, 설계 승인(Design Win), 재고 동향 중 "
            "어떤 것이 가장 귀중한 선행 정보인지 생각해보세요.",
            "실무 적용 + 정보 우위 분석"
        ),
        (
            "2027년 Phase 5(엣지·로보틱스) 투자 파동에 대비하기 위해 "
            "지금(2025년) 어떤 종목을 '씨앗(Seed)' 포지션으로 편입해야 하는가? "
            "3개 종목을 근거와 함께 제시하라.",
            "1장의 Phase 5 수혜 기업(ARM, Qualcomm, Marvell, Boston Dynamics 파트너사)을 "
            "참고하세요. '씨앗 포지션'은 전체 포트폴리오의 5% 이하로 시작합니다.",
            "장기 포지셔닝"
        ),
        (
            "8주 학습을 마친 반도체 마케팅 담당자가 내일 당장 영업 현장에서 "
            "활용할 수 있는 '투자자 설득 포인트' 3가지를 만들어라. "
            "(대상 고객: 반도체 섹터 투자를 검토하는 기관투자자)",
            "8주간 학습한 수치(HBM 대역폭, CapEx $310B, Phase 로드맵 등)를 "
            "조합하여 설득력 있는 스토리를 구성해보세요.",
            "실전 스토리텔링 (종합)"
        ),
    ]
    _quiz_section(doc, questions)

    _add_heading(doc, "정답 가이드 (핵심 포인트)", 2)
    answers = [
        ("Q1 핵심",
         "현재 위치: Phase 3(전력·냉각) 진행 중, Phase 4(네트워킹) 초입. "
         "Phase 4 전환 신호: ① GB200 분기 출하량 급증 뉴스 "
         "② Broadcom/Arista AI 관련 수주잔고 가이던스 상향 "
         "③ InfiniBand XDR 400Gbps 이상 NIC 출하량 증가."),
        ("Q2 핵심",
         "$310B × 40%(AI 서버 비중) = $124B AI 서버 시장. "
         "구성: GPU 60% ($74B) → NVIDIA 수혜. "
         "메모리 20% ($25B) → SK하이닉스/Micron. "
         "네트워킹 10% ($12B) → NVIDIA IB + Broadcom. "
         "전력·냉각 10% ($12B) → Vertiv + GE Vernova."),
        ("Q3 핵심",
         "비중 축소 신호 타이밍: ① H100 리드타임 12개월 → 6개월 단축 시 (공급 증가) "
         "② NVIDIA 분기 가이던스 성장률 둔화 시 (50%+ → 20%대) "
         "③ 하이퍼스케일러 CapEx 가이던스 하향 시. "
         "실제로 2024.11 주가 고점 후 위 신호들이 순차 등장. 전량 매도보다 비중 축소가 정답."),
        ("Q4 핵심",
         "SK하이닉스: HBM AI 의존 ~90% → Bear에서 가장 취약. 단, HBM4 수요 선점으로 일부 방어. "
         "TSMC: AI는 매출의 ~30%, 스마트폰/HPC 60%+ → 상대적 방어. "
         "Vertiv: AI 데이터센터 의존 ~60%, 기존 서버 냉각 40% → 중간 방어력. "
         "가장 방어적: TSMC (비AI 수요 다변화 + CHIPS Act 보조금)."),
        ("Q5 핵심",
         "권장 대응: 보유(Hold) + 일부 추가 매수. "
         "근거: DeepSeek = 효율화 쇼크이나 Jevons Paradox로 장기 GPU 수요 증가. "
         "단기 -17%는 감정적 과반응. AI 수요 펀더멘털 변화 없음. "
         "단, 현금 비중 15% 유지 → -25% 추가 하락 시 추가 매수 예정 유지."),
        ("Q6 핵심",
         "① 리드타임 정보 우위: 고객사 GPU 리드타임 연장 = 수요 과열 선행 신호 → 매수. "
         "② 설계 승인(Design Win) 정보: SK하이닉스 HBM 특정 GPU에 독점 선정 뉴스 → 매수. "
         "③ 재고 동향: 공급사 채널 재고 누적 → 선제 매도 시그널. "
         "전환: 공개 발표 전 6-12개월 앞서 파악 가능한 정보 = 합법적 알파 원천."),
        ("Q7 핵심",
         "씨앗 포지션 3가지 (각 1-2%):\n"
         "① ARM Holdings (ARMH): 엣지 AI 칩 설계 IP 독점, Cortex AI 로드맵.\n"
         "② Qualcomm (QCOM): 온디바이스 AI 추론 최강자, Snapdragon AI 플랫폼.\n"
         "③ Marvell (MRVL): 엣지 AI 네트워킹 + 커스텀 ASIC, 로보틱스 통신 칩."),
        ("Q8 핵심",
         "설득 포인트 예시:\n"
         "① 'AI CapEx $310B는 역대 최대. NVIDIA·SK하이닉스·TSMC 3개사가 90%+ 공급 독점.' "
         "→ 독점 구조 + 규모 강조.\n"
         "② 'Phase 4(네트워킹) 전환 임박. $25B 시장이 2027년까지 성장. "
         "Broadcom·Arista는 아직 밸류에이션 반영 미흡.' → 타이밍 + 상대 밸류.\n"
         "③ 'Sovereign AI가 190개국 수요를 창출. 중동 $140B+, 아시아 $10B+. "
         "하이퍼스케일러 외 새로운 성장 축.' → 수요 다변화 + 지속성."),
    ]
    for key, ans in answers:
        p = doc.add_paragraph()
        r = p.add_run(f"[{key}] ")
        r.bold = True
        r.font.size = Pt(9)
        r2 = p.add_run(ans)
        r2.font.size = Pt(9)

    doc.add_page_break()

    # ── 종합 참고문헌 ──────────────────────────────────────────
    _add_heading(doc, "종합 참고문헌")
    ref_rows = [(n, url, desc, yr) for n, url, desc, yr in REFS.values()]
    _add_table(doc, ["출처명", "URL", "설명", "연도"], ref_rows)

    # ── 저장 ─────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today_str = date.today().strftime("%Y%m%d")
    level_suffix = {1: "", 2: "_lv2", 3: "_lv3"}.get(level, "")
    out = OUTPUT_DIR / f"study_investment_framework{level_suffix}_{today_str}.docx"
    doc.save(str(out))
    print(f"  [Investment Framework Study] 생성 완료: {out}")
    print(f"  [Investment Framework Study] 8장 구성, {len(REFS)}개 참고자료, 8문항 복습 문제 (Level {level})")
    return str(out)


def run(level=1):
    return {"word_path": build(level)}


if __name__ == "__main__":
    result = run()
    print(f"\n출력 파일: {result['word_path']}")
