"""
AI 데이터센터 전력 인프라 심화 Study Agent
대상: 반도체 마케팅 종사자 (비즈니스 배경 ○, 기술 기초 보완 필요)

학습 목표:
  - AI 데이터센터가 전력 인프라에 미치는 구조적 충격을 정량적으로 이해
  - 전력 공급망 구조와 핵심 병목(변압기, 냉각)을 마케팅 언어로 파악
  - 수혜 기업과 투자 프레임워크를 직접 도출할 수 있게 됨

출력: outputs/reports/study_power_infrastructure_YYYYMMDD.docx
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

OUTPUT_DIR = Path(config.REPORTS_DIR)

# ──────────────────────────────────────────────────────────────
# 참고자료
# ──────────────────────────────────────────────────────────────
REFS = {
    "IEA_Electricity_2024": (
        "IEA — Electricity 2024 Report",
        "https://www.iea.org/reports/electricity-2024",
        "글로벌 데이터센터 전력 수요 전망: 2022→2026 추정치, AI 기여분 정량화", "2024"
    ),
    "Goldman_AI_Power": (
        "Goldman Sachs — 'Generational Growth' AI Power Report",
        "https://www.goldmansachs.com/insights/articles/AI-poised-to-drive-160-increase-in-power-demand",
        "미국 전력망 투자 필요액 $3.5T, AI DC 전력 수요 160% 증가 시나리오", "2024"
    ),
    "Vertiv_IR": (
        "Vertiv Investor Relations — FY2024 Annual Report",
        "https://ir.vertiv.com/",
        "Vertiv 2024 매출 $7.5B, 2025E $8.5B, 수주 잔고 $7B+ 상세 데이터", "2024"
    ),
    "GE_Vernova_AR": (
        "GE Vernova — 2024 Annual Report",
        "https://www.gevernova.com/investors",
        "Grid 사업부 전력 변압기 수주 잔고, 리드타임 현황, AI DC 수혜 분석", "2024"
    ),
    "LBNL_DC_Energy": (
        "Lawrence Berkeley National Laboratory — US Data Center Energy Use Report",
        "https://eta.lbl.gov/publications/united-states-data-center-energy",
        "미국 DC 전력 소비 실측 데이터, PUE 추이, 2026 전망", "2024"
    ),
    "DOE_Grid": (
        "DOE Grid Deployment Office — National Transmission Needs Study",
        "https://www.energy.gov/gdo/national-transmission-needs-study",
        "미국 전력망 업그레이드 필요성, 변압기 공급망 현황, 투자 로드맵", "2023"
    ),
    "NVIDIA_GB200_Power": (
        "NVIDIA GB200 NVL72 Technical Brief",
        "https://www.nvidia.com/en-us/data-center/gb200-nvl72/",
        "GB200 NVL72: 120kW/랙 전력 소비, 직접 수냉 필수 사양 공개", "2024"
    ),
    "Schneider_WP": (
        "Schneider Electric — AI Data Center Power White Paper 2024",
        "https://www.se.com/ww/en/work/insights/ai-data-center-power/",
        "AI DC 전력 밀도 변화, 냉각 기술 비교, UPS/PDU 용량 계획 가이드", "2024"
    ),
    "Eaton_IR": (
        "Eaton Corporation — FY2024 Earnings & IR",
        "https://www.eaton.com/us/en-us/company/investor-relations.html",
        "DC 전력 관리 수주 잔고, 변압기 리드타임 언급, 2025 가이던스", "2024"
    ),
    "Hyundai_Electric_IR": (
        "현대일렉트릭 — 2024 사업보고서 및 IR",
        "https://www.hyundai-electric.com/kr/ir/",
        "변압기 수주 잔고 사상 최대, 미국 수출 비중 확대, AI DC 수혜 정량화", "2024"
    ),
    "ABB_AR": (
        "ABB Ltd — 2024 Annual Report",
        "https://investors.abb.com/annual-reports",
        "Electrification 사업부 성장, DC 전력 솔루션, 변압기·차단기 수주", "2024"
    ),
    "Uptime_PUE": (
        "Uptime Institute — Global Data Center Survey 2024",
        "https://uptimeinstitute.com/2024-data-center-industry-survey",
        "글로벌 DC PUE 평균 1.58, 하이퍼스케일러 1.1~1.2 달성 현황", "2024"
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
    """색상 박스 (개념 정의, 마케터 관점, 기술 원리 구분)."""
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
    """파란 박스: 기술 개념 설명."""
    _box(doc, "개념", "E8F0FE", text)

def _marketing(doc, text):
    """초록 박스: 마케터 관점 해석."""
    _box(doc, "마케터 관점", "E8F5E9", text)

def _quant(doc, text):
    """노란 박스: 정량 계산 예제."""
    _box(doc, "계산 예제", "FFF9C4", text)

def _risk(doc, text):
    """주황 박스: 리스크/주의사항."""
    _box(doc, "주의", "FFF3E0", text)

def _add_refs(doc, keys):
    refs = [REFS[k] for k in keys if k in REFS]
    if not refs:
        return
    doc.add_paragraph("참고자료", style="Heading 3")
    tbl = doc.add_table(rows=1 + len(refs), cols=4)
    tbl.style = "Table Grid"
    for i, h in enumerate(["출처", "URL", "설명", "연도"]):
        c = tbl.rows[0].cells[i]
        c.text = h
        for r in c.paragraphs[0].runs:
            r.bold = True
            r.font.size = Pt(9)
    for ri, (name, url, desc, yr) in enumerate(refs):
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
    """복습 문제 섹션."""
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
        print("  [Power Infra Study] python-docx 미설치")
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
    t = doc.add_heading(f"{level_prefix}AI 데이터센터 전력 인프라 심층 분석", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s = doc.add_paragraph("Power Infrastructure — 전력이 AI 확장의 새로운 병목이 된 이유")
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s2 = doc.add_paragraph(
        f"대상: 반도체 마케팅 종사자  |  기준일: {config.AS_OF_DATE}  |  "
        f"난이도: 기술 기초 → 중급"
    )
    s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in s2.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(100, 100, 100)

    desc = doc.add_paragraph(
        "\n본 문서는 AI 데이터센터 전력 인프라를 반도체 마케팅 관점에서 이해하기 위한 "
        "심층 학습 자료입니다. GB200 등 차세대 GPU가 요구하는 전력 규모, "
        "전력 공급망 구조, 핵심 병목과 수혜 기업, 투자 프레임워크를 다룹니다."
    )
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in desc.runs:
        run.font.size = Pt(9)
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 1장. 전력 위기의 배경
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "1장. 전력 위기의 배경 — 1MW/랙이 바꾸는 모든 것")

    doc.add_paragraph(
        "반도체 마케팅 담당자에게 '전력'은 낯선 주제처럼 느껴질 수 있습니다. "
        "그러나 2024년부터 AI GPU 고객사(구글, MS, 아마존, 메타)들이 "
        "반도체 도입을 늦추는 이유가 '전력 부족'이라고 언급하기 시작했습니다. "
        "GPU 공급망의 최종 수요를 결정하는 전력 인프라를 이해해야 합니다."
    )

    _add_heading(doc, "1.1 GB200 NVL72 — 1랙 1MW의 충격", 2)
    _concept(doc,
        "GB200 NVL72: NVIDIA의 2024년 발표 AI 컴퓨팅 랙 시스템. "
        "한 랙(=서버 선반 1개)에 GPU 72개 + NVSwitch 18개 + CoWoS 패키징이 통합. "
        "소비 전력: ~120kW(작동 시) ~ 최대 1MW(피크, 전체 냉각·전력 설비 포함).")
    _concept(doc,
        "PUE(Power Usage Effectiveness): 데이터센터 전체 전력 ÷ IT 장비 전력. "
        "PUE 1.0 = 완벽 효율(이론). 현실: 기존 DC PUE ~1.5, 구글/MS 하이퍼스케일 ~1.1~1.2. "
        "GB200 랙 120kW × PUE 1.2 = 144kW/랙 (냉각·전력 인프라 포함).")

    rack_rows = [
        ["기존 서버 랙\n(일반 DC)",   "5-15 kW/랙",    "2-3kW",      "공랭 가능",     "PUE ~1.5"],
        ["AI 학습용 A100 랙",         "20-30 kW/랙",   "700W/GPU",   "공랭 한계",     "PUE ~1.3"],
        ["H100 DGX H100 랙",          "~40-50 kW/랙",  "700W/GPU",   "수냉 필요",     "PUE ~1.2"],
        ["B200 DGX B200 랙",          "~120 kW/랙",    "1,000W/GPU", "직접 수냉 필수","PUE ~1.15"],
        ["GB200 NVL72 랙\n(풀 시스템)","~120kW~1MW",   "120kW/랙",   "직접 수냉 필수","PUE ~1.1 목표"],
    ]
    _add_table(doc,
        ["랙 유형", "전력 밀도", "GPU 소비 전력", "냉각 방식", "PUE 목표"],
        rack_rows)

    _add_heading(doc, "1.2 전통 DC vs AI DC — 무엇이 다른가", 2)
    _concept(doc,
        "전통 데이터센터: 1MW = 전체 DC 건물 전력 예산. "
        "100~200개 랙, 랙당 5-10kW. 공랭으로 충분. 전력 밀도 낮음.")
    _concept(doc,
        "AI 데이터센터(하이퍼스케일): 1MW = 랙 1개의 전력 소비. "
        "동일 건물에 1,000개 랙 = 1GW 필요. 중소 도시 전체 전력 소비와 동급. "
        "이 구조적 변화가 전력 인프라 전체를 재편해야 하는 이유입니다.")
    _marketing(doc,
        "마케터 관점: GB200 NVL72 랙 1개 도입 = 기존 DC 건물 전체 전력 도입. "
        "고객사(빅테크)가 GPU 주문을 늘릴수록 전력 인프라 투자도 비례 증가. "
        "반도체 수요의 '배후 수요'로서 전력 인프라 기업이 동반 성장.")

    _add_refs(doc, ["NVIDIA_GB200_Power", "LBNL_DC_Energy", "Schneider_WP"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 2장. 전력 수요 정량화
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "2장. 전력 수요 정량화 — 얼마나 크고 얼마나 빠른가")

    doc.add_paragraph(
        "AI DC 전력 수요가 '크다'는 것은 알겠는데, 얼마나 큰지 수치로 봐야 합니다. "
        "IEA와 Goldman Sachs의 데이터를 중심으로 규모를 정량화합니다."
    )

    _add_heading(doc, "2.1 글로벌 DC 전력 수요 추이", 2)
    global_power_rows = [
        ["2022", "~30 GW",     "~240 TWh/년",  "AI 이전: 일반 클라우드·스트리밍 중심"],
        ["2023", "~38 GW",     "~460 TWh/년",  "ChatGPT 등장 → AI 추론 수요 폭증 시작"],
        ["2024", "~50 GW",     "~600 TWh/년",  "H100 랙 대규모 구축, 신규 DC 착공 급증"],
        ["2026E","~100 GW",    "~1,000 TWh/년","B200/GB200 배포 본격화, IEA 기준 전망"],
        ["2027E","~140 GW",    "~1,400 TWh/년","Goldman Sachs 시나리오 (적극 AI 투자 가정)"],
    ]
    _add_table(doc,
        ["연도", "설치 용량", "연간 전력 소비", "비고"],
        global_power_rows)

    _quant(doc,
        "수요 성장 속도 계산:\n"
        "  2022→2026E: 30GW → 100GW = 3.3배 증가, 4년간 CAGR +35%\n"
        "  비교: 전 세계 전력 소비 연간 증가율 ~2-3%의 10배 이상 속도\n"
        "  2026E 100GW = 한국 전체 발전 설비 용량(~140GW)의 70%\n"
        "  → AI DC 전력이 국가 단위 전력망 설계를 바꾸는 수준")

    _add_heading(doc, "2.2 GPU별 전력 소비 증가 추이", 2)
    gpu_power_rows = [
        ["A100 (2020)", "400W",   "DGX A100: 6.5kW/박스",    "H100 대비 기준"],
        ["H100 (2022)", "700W",   "DGX H100: 10.2kW/박스",   "A100 대비 +75%"],
        ["H200 (2024)", "700W",   "H100과 동일",              "메모리(HBM3e)만 업그레이드"],
        ["B200 (2024)", "1,000W", "DGX B200: ~14.3kW/박스",  "H100 대비 +43%"],
        ["GB200 NVL72", "120,000W/랙", "GPU 72개 통합 랙",   "B200 단일 대비 랙당 기준"],
        ["Rubin (2026E)","1,200W+ 추정", "미공개",            "B200 대비 +20% 추정"],
    ]
    _add_table(doc,
        ["GPU", "TDP(열설계전력)", "시스템 전력", "비고"],
        gpu_power_rows)

    _concept(doc,
        "TDP(Thermal Design Power, 열설계전력): GPU/CPU가 최대 부하 시 발생시키는 열량. "
        "W(와트) 단위. 냉각 시스템 설계의 기준값. "
        "TDP가 높을수록 더 강력한 냉각·전력 공급 인프라 필요.")

    _add_refs(doc, ["IEA_Electricity_2024", "Goldman_AI_Power", "NVIDIA_GB200_Power"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 3장. 전력 공급망 구조
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "3장. 전력 공급망 구조 — 발전소에서 GPU까지")

    doc.add_paragraph(
        "AI GPU가 전기를 먹는다는 것은 알겠는데, "
        "그 전기가 어디서 어떻게 오는지를 알아야 어느 기업이 수혜를 받는지 보입니다. "
        "전력 공급망을 단계별로 분해합니다."
    )

    _add_heading(doc, "3.1 전력 흐름 다이어그램 (텍스트 형식)", 2)
    doc.add_paragraph(
        "[발전소] → (초고압 송전: 345kV-765kV)\n"
        "  → [변전소 1단계 (Grid Substation)] — 초고압→고압 변환 (변압기)\n"
        "  → [변전소 2단계 (Distribution Substation)] — 고압→배전압 변환\n"
        "  → [데이터센터 진입 변압기 (Site Transformer)] — 배전압→DC 내부 전압\n"
        "  → [UPS (무정전전원장치)] — 순간 정전 대비 배터리 버퍼\n"
        "  → [PDU (전력 분배 장치)] — 랙 단위 전력 분배\n"
        "  → [서버 랙 내 PSU (전원 공급 장치)] — GPU·CPU 직접 공급\n"
        "  → [GPU/HBM] ← 여기서 연산 발생\n\n"
        "각 단계에서 전력 손실 발생 → PUE = 최종 IT 전력 / 총 입력 전력"
    )

    supply_chain_rows = [
        ["발전소", "전력 생산",
         "GE Vernova, Siemens Energy", "가스터빈, 태양광, 핵발전"],
        ["초고압 변압기\n(Grid Transformer)",
         "전압 변환 (스텝다운)",
         "현대일렉트릭, GE Vernova, ABB",
         "리드타임 30개월\n핵심 병목"],
        ["UPS\n(무정전전원장치)",
         "정전 대비 배터리 백업",
         "Vertiv, Eaton, Schneider",
         "AI DC용 대용량 UPS\n급성장 중"],
        ["PDU\n(전력 분배 장치)",
         "랙 단위 전력 분배·모니터링",
         "Vertiv, Raritan, Schneider",
         "스마트 PDU 수요 증가"],
        ["냉각 시스템\n(Cooling)",
         "GPU 발열 제거",
         "Vertiv, Munters, CoolIT",
         "수냉·액침냉각 전환\n가속화"],
        ["전력 케이블·버스바",
         "전력 전송 배선",
         "넥상스, LS전선, 프리즈미안",
         "DC 내 고전압 배선\n특수 케이블"],
    ]
    _add_table(doc,
        ["공급망 단계", "기능", "주요 기업", "AI DC 특이사항"],
        supply_chain_rows)

    _marketing(doc,
        "투자 지도: 전력 공급망 각 단계마다 독립적인 수혜 기업이 있습니다. "
        "NVIDIA GPU 주문 1건 = 변압기 + UPS + PDU + 냉각 + 케이블 수주 연쇄 발생. "
        "반도체 주식이 비싸 보일 때 이 '배후 공급망'이 대안 투자처입니다.")

    _add_refs(doc, ["DOE_Grid", "Schneider_WP", "LBNL_DC_Energy"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 4장. 핵심 병목: 변압기
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "4장. 핵심 병목: 변압기 — AI DC의 숨겨진 제약")

    doc.add_paragraph(
        "전력망에서 가장 만들기 어렵고 오래 걸리는 것이 변압기입니다. "
        "CoWoS 리드타임이 18개월인 것처럼, 대형 변압기는 리드타임이 30개월입니다. "
        "이 하나의 부품이 수조 달러 규모의 AI DC 투자를 막고 있습니다."
    )

    _add_heading(doc, "4.1 변압기 공급 위기의 원인", 2)
    _concept(doc,
        "변압기(Transformer): 교류 전압을 높이거나 낮추는 전력 설비. "
        "AI DC용 대형 변압기(100MVA급)는 수개월의 맞춤 제작이 필요. "
        "내부 코어(코일)는 특수 규소강판 필요 — 제조사 극소수.")
    transformer_crisis_rows = [
        ["미국 리드타임",     "과거 12개월",   "현재 28-36개월",  "3배 증가"],
        ["유럽 리드타임",     "과거 9개월",    "현재 18-24개월",  "2배 증가"],
        ["글로벌 백로그",     "과거 6개월분",  "현재 24개월분+",  "4배 증가"],
        ["미국 내 생산 비중", "과거 ~60%",     "현재 ~30%",       "제조업 공동화"],
        ["특수 규소강판 공급", "여유 있음",     "타이트, 일부 부족","소재까지 병목"],
    ]
    _add_table(doc, ["항목", "2019년", "2024년", "변화"], transformer_crisis_rows)

    _quant(doc,
        "변압기 병목이 AI DC 투자에 미치는 영향 계산:\n"
        "  계획 중인 AI DC 신규 용량: 글로벌 50GW+ (2025-2027E)\n"
        "  50GW 연결에 필요한 대형 변압기(100MVA 기준): ~500개 이상\n"
        "  현재 글로벌 대형 변압기 연간 생산량: ~300-400개(추정)\n"
        "  → 2-3년치 수요가 이미 적체 → 변압기 제조사 수주 잔고 폭증")

    _add_heading(doc, "4.2 현대일렉트릭 — 국내 최대 수혜", 2)
    _marketing(doc,
        "현대일렉트릭은 대형 변압기 제조사 중 글로벌 5위권. "
        "미국 수출 비중이 빠르게 확대(2024 미국 수주 비중 40%+ 추정). "
        "2024년 수주 잔고가 사상 최대치 갱신. "
        "AI DC 투자 → 변압기 수요 → 현대일렉트릭 수주가 직접 연결되는 구조.")
    _risk(doc,
        "리스크: 2026-2027년 변압기 증설 완료 시 공급 과잉 가능성. "
        "또한 도널드 트럼프 관세 정책이 미국 수출에 영향을 줄 수 있음. "
        "수주 잔고 소화 속도와 신규 수주 모멘텀을 동시에 모니터링 필요.")

    _add_refs(doc, ["Goldman_AI_Power", "DOE_Grid", "Hyundai_Electric_IR", "GE_Vernova_AR"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 5장. 냉각 기술 진화
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "5장. 냉각 기술 진화 — 공랭에서 액침냉각까지")

    doc.add_paragraph(
        "GPU가 발열을 이기는 것이 성능 확장의 물리적 한계입니다. "
        "GB200처럼 1랙 120kW가 되면 기존 공랭으로는 절대 불가합니다. "
        "냉각 기술의 진화가 AI GPU 채택의 필수 전제 조건입니다."
    )

    cooling_rows = [
        ["공랭\n(Air Cooling)",
         "팬으로 차가운 공기를 순환",
         "<5 kW/랙",
         "저비용, 기존 DC 호환",
         "한계 용량 초과 불가",
         "서버·스토리지"],
        ["수냉\n(Direct Water Cooling)",
         "냉각수 파이프를 서버 내부에 설치",
         "10-50 kW/랙",
         "공랭 대비 20-30배 효율",
         "배관 설비 투자 필요",
         "H100, B200 서버"],
        ["후면 도어 열교환기\n(Rear Door HX)",
         "랙 뒤에 냉각 패널 장착",
         "20-30 kW/랙",
         "기존 DC 부분 적용 가능",
         "용량 한계",
         "혼합 환경 과도기"],
        ["직접 수냉\n(Direct Liquid Cooling)",
         "CPU/GPU 칩에 냉각수 직접 접촉",
         "50-150 kW/랙",
         "GB200 필수 방식",
         "설계 변경 필요",
         "GB200 NVL72"],
        ["액침냉각\n(Immersion Cooling)",
         "서버 전체를 절연 액체에 담금",
         "100 kW/랙 이상",
         "최고 효율, PUE ~1.03",
         "초기 비용 높음\n운영 복잡",
         "실험적 도입 확산"],
    ]
    _add_table(doc,
        ["냉각 방식", "원리", "냉각 용량", "장점", "단점/제약", "적용 예"],
        cooling_rows)

    _add_heading(doc, "5.1 GB200이 직접 수냉을 강제하는 이유", 2)
    _concept(doc,
        "GB200 NVL72 랙 전력 밀도: ~120kW/랙 (IT 기준). "
        "공랭 최대 용량: ~30kW/랙. → 공랭으로는 120kW 처리 불가(4배 초과). "
        "NVIDIA GB200 스펙시트에 명시: '직접 액체 냉각 필수(Liquid Cooling Required)'. "
        "Vertiv의 CDU(냉각 분배 장치)가 사실상 GB200 랙의 필수 구성품.")
    _marketing(doc,
        "비즈니스 임팩트: NVIDIA GB200 랙 도입 = Vertiv/CoolIT CDU 동시 구매 필수. "
        "GB200 랙 1개($3-5M) 구매 시 냉각 설비 추가 $300-500K 동반 지출. "
        "Vertiv 입장에서 NVIDIA GB200 출하량 = 자사 CDU 수주와 1:1 연동.")

    _add_heading(doc, "5.2 PUE와 냉각 효율의 경제학", 2)
    _concept(doc,
        "PUE(Power Usage Effectiveness) = 전체 DC 전력 / IT 장비 전력. "
        "PUE 1.5 = IT 전력 100kW에 냉각·인프라 50kW 추가 = 총 150kW 사용. "
        "PUE 1.1 = IT 전력 100kW에 냉각·인프라 10kW 추가 = 총 110kW 사용. "
        "PUE 0.4 개선 = 연간 전력비 27% 절감 → 대규모 DC에서 연 수백억 원 차이.")
    _quant(doc,
        "PUE 개선의 경제적 가치 계산:\n"
        "  1GW DC 건물, PUE 1.5 → 1.1 전환:\n"
        "  절감 전력: 1GW × (1.5-1.1)/1.5 = 267MW\n"
        "  연간 전력비: 267MW × 8,760시간 × $0.07/kWh = $163M/년 절감\n"
        "  → 냉각 설비 교체 비용 $50-100M이 1년 미만에 회수")

    _add_refs(doc, ["Schneider_WP", "NVIDIA_GB200_Power", "Uptime_PUE", "Vertiv_IR"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 6장. 수혜 기업 분석
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "6장. 수혜 기업 분석 — 전력 인프라 투자 지도")

    doc.add_paragraph(
        "AI DC 전력 투자의 수혜는 NVIDIA·TSMC처럼 주목받지 못하지만, "
        "Vertiv, GE Vernova, 현대일렉트릭은 2023년 이후 폭발적 주가 상승을 기록했습니다. "
        "각 기업의 포지션과 투자 포인트를 정리합니다."
    )

    company_rows = [
        ["Vertiv\n(VRT)",
         "UPS, PDU, 냉각(CDU)", "미국 나스닥",
         "$7.5B (2024)\n$8.5B (2025E)",
         "+40%+ (2023-2024)",
         "~30x",
         "구글, MS, 아마존 DC\nGB200 냉각 필수 공급사"],
        ["Eaton\n(ETN)",
         "전력 관리, 변압기, UPS", "미국 NYSE",
         "$24B (2024)",
         "+20%+",
         "~25x",
         "분산 전력 관리\nDC + 산업 전반"],
        ["Schneider Electric\n(SU)",
         "전력·냉각·DC 관리 솔루션", "프랑스 CAC40",
         "$40B+ (2024)",
         "+25%+",
         "~28x",
         "DCIM 소프트웨어\n전체 DC 솔루션 통합"],
        ["GE Vernova\n(GEV)",
         "발전기, 변압기, 그리드", "미국 NYSE",
         "$34B (2024)",
         "+80%+ (스핀오프 후)",
         "~40x",
         "전력망 투자 확대\n변압기 수주 잔고 폭증"],
        ["ABB\n(ABBN)",
         "변압기, 모터, 전력 기기", "스위스 SIX",
         "$32B (2024)",
         "+30%+",
         "~25x",
         "글로벌 전력 인프라\n폭넓은 포트폴리오"],
        ["현대일렉트릭\n(267260.KS)",
         "대형 변압기, 배전반", "한국 코스피",
         "~2.5조원 (2024)",
         "+200%+ (2023-2024)",
         "~15x",
         "미국 수출 급증\n국내 밸류에이션 디스카운트"],
    ]
    _add_table(doc,
        ["기업 (티커)", "주요 제품", "상장 시장",
         "매출/규모", "2023-2024 주가 수익률", "PER(배)", "AI DC 포지션"],
        company_rows)

    _add_heading(doc, "6.1 Vertiv — AI DC 전력의 핵심 인프라 기업", 2)
    _marketing(doc,
        "Vertiv의 핵심 경쟁 우위: GB200 NVL72 냉각의 사실상 유일 공급사(CDU). "
        "2024 수주 잔고 $7B+는 2024 매출의 ~1년치. 즉 2025-2026년 매출이 이미 확보됨. "
        "NVIDIA 출하량 증가 = Vertiv 수주 자동 증가 구조. '두 번째 NVIDIA' 별명.")

    _add_heading(doc, "6.2 현대일렉트릭 — 국내 투자자에게 가장 접근하기 쉬운 수혜주", 2)
    _marketing(doc,
        "현대일렉트릭은 미국 대형 변압기 시장에서 후발주자였으나, "
        "공급 부족으로 글로벌 1-2위(ABB, 지멘스)가 수요를 감당 못 하면서 반사 수혜. "
        "2024년 미국 수주 비중 40%+, 수주 잔고 1.5-2조원 돌파(추정). "
        "한국 상장 = 글로벌 대비 밸류에이션 할인 → 추가 리레이팅 여력.")

    _add_refs(doc, ["Vertiv_IR", "GE_Vernova_AR", "ABB_AR", "Eaton_IR", "Hyundai_Electric_IR"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 7장. 투자 프레임워크
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "7장. 투자 프레임워크 — Phase 3 투자 파동")

    doc.add_paragraph(
        "AI 인프라 투자는 '파동(Wave)'으로 이해하면 타이밍 판단이 쉬워집니다. "
        "반도체 → 서버 → 전력·냉각 순서로 투자가 확대되는 패턴이 반복됩니다."
    )

    _add_heading(doc, "7.1 AI 인프라 투자 3단계 파동", 2)
    phase_rows = [
        ["Phase 1\n(2022-2023)",
         "GPU·HBM 부족",
         "NVIDIA, SK Hynix\nTSMC CoWoS",
         "H100 품귀\n리드타임 52주",
         "이미 선반영"],
        ["Phase 2\n(2023-2024)",
         "서버·네트워크 부족",
         "슈퍼마이크로, Arista\nBroadcom, Marvell",
         "AI 서버 납기 6-12개월",
         "선반영 많음"],
        ["Phase 3\n(2025-2026)",
         "전력·냉각·변압기 부족",
         "Vertiv, GE Vernova\nABB, 현대일렉트릭",
         "변압기 리드타임 30개월\n냉각 수주 잔고 증가",
         "현재 진행 중 ★"],
        ["Phase 4\n(2026-2027E)",
         "재생에너지·SMR\n전력 생산 부족",
         "GE Vernova, Talen\nVistra, NuScale",
         "AI DC + 전력 생산 직접 계약",
         "초기 단계"],
    ]
    _add_table(doc,
        ["단계", "병목 레이어", "수혜 기업 예시", "시장 증거", "투자 타이밍"],
        phase_rows)

    _marketing(doc,
        "2026년 현재 우리는 Phase 3의 한복판에 있습니다. "
        "반도체(Phase 1)는 이미 고평가, 서버(Phase 2)도 일부 선반영. "
        "전력 인프라(Phase 3)는 아직 주목도가 낮아 '상대적 저평가' 구간 가능성. "
        "Phase 3 기업들의 수주 잔고와 리드타임을 추적하면 사이클 확인 가능.")

    _add_heading(doc, "7.2 재생에너지 + AI DC 조합 투자 논리", 2)
    _concept(doc,
        "빅테크들의 탄소 중립 약속 + AI DC 전력 수요 폭증 = 재생에너지 직접 구매 계약(PPA) 급증. "
        "구글: 2023년 전력 거래량 1위 (태양광·풍력 PPA). "
        "마이크로소프트: SMR(소형 모듈 원자로) 계약 (스리마일 아일랜드 재가동). "
        "아마존: 글로벌 최대 재생에너지 구매 기업.")
    _quant(doc,
        "AI DC 전력 비용 계산 (2026E 기준):\n"
        "  글로벌 AI DC 전력 1,000 TWh/년 × $0.06/kWh (평균 전력단가)\n"
        "  = $60B/년 — 빅테크의 연간 전력 지출\n"
        "  이 비용을 줄이기 위해 PPA + 자가 발전 투자 = GE Vernova 등 수혜\n"
        "  Goldman Sachs: 미국만 $3.5T 전력망 투자 필요 (2030까지)")

    _add_heading(doc, "7.3 핵심 모니터링 지표", 2)
    monitor_rows = [
        ["변압기 리드타임\n(US Grid Transformer)",
         "Eaton/GE Vernova 실적 발표 코멘트",
         "30개월 이상 유지 시 Phase 3 지속\n단축 시 공급 정상화 신호"],
        ["Vertiv 수주 잔고",
         "분기 실적 발표",
         "$7B 이상 유지 = 매수 신호\n감소 시 AI CapEx 둔화 선행 지표"],
        ["빅테크 CapEx 가이던스\n(구글/MS/아마존/메타)",
         "분기 실적 발표 (1-2월, 4-5월)",
         "CapEx 상향 = 전력 인프라 수요 확인\n하향 = 즉시 포지션 재검토"],
        ["IEA/EIA DC 전력 수요 업데이트",
         "IEA 연간 Electricity 보고서 (2-3월)",
         "전망 상향 = 구조적 수요 확인"],
        ["현대일렉트릭 미국 수주 비중",
         "분기 IR 및 실적 발표",
         "미국 수주 40%+ 유지 시 수혜 지속\n하락 시 경쟁 심화 신호"],
    ]
    _add_table(doc,
        ["지표", "데이터 소스", "해석 기준"],
        monitor_rows)

    _add_refs(doc, ["Goldman_AI_Power", "IEA_Electricity_2024", "Vertiv_IR", "GE_Vernova_AR"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 레벨별 심화 섹션 (8장 복습 문제 직전)
    # ══════════════════════════════════════════════════════════
    if level >= 2:
        _add_heading(doc, "심화 분석")
        doc.add_paragraph(
            "이 섹션은 Level 2 심화 과정으로, PUE 별 TCO 비교 계산과 "
            "직접수냉(DLC) vs 공랭 방식의 CapEx 비교를 다룹니다."
        )

        _add_heading(doc, "PUE 별 TCO 비교 계산", 2)
        doc.add_paragraph(
            "PUE(Power Usage Effectiveness)는 데이터센터 전체 전력 소비를 "
            "IT 장비 전력 소비로 나눈 값입니다. PUE 개선 1포인트가 TCO에 미치는 영향을 계산합니다."
        )
        doc.add_paragraph(
            "가정 조건: 10MW IT 부하 데이터센터, 전기요금 $0.06/kWh, "
            "연간 8,760시간 운영, 10년 TCO 계산."
        )
        pue_rows = [
            ["PUE 2.0 (구형)", "20 MW", "10 MW", "$10.5M/년", "$105M", "냉각 비용 = IT 비용과 동일"],
            ["PUE 1.5 (평균)", "15 MW", "5 MW", "$7.9M/년", "$79M", "표준 공랭 현대 DC"],
            ["PUE 1.3 (효율형)", "13 MW", "3 MW", "$6.8M/년", "$68M", "프리쿨링 적용"],
            ["PUE 1.15 (DLC)", "11.5 MW", "1.5 MW", "$6.0M/년", "$60M", "직접수냉(DLC) 적용"],
            ["PUE 1.05 (침수냉각)", "10.5 MW", "0.5 MW", "$5.5M/년", "$55M", "액침냉각 최고 효율"],
        ]
        _add_table(doc, ["PUE", "총 전력", "냉각 전력", "전기요금/년", "10년 TCO", "비고"],
                   pue_rows)
        doc.add_paragraph(
            "TCO 절감 계산: PUE 2.0 → 1.15 전환 시 10년 절감액 = $105M - $60M = $45M. "
            "DLC 초기 투자 비용 $10-15M 고려 시 ROI = ($45M - $12.5M) / $12.5M = 260%. "
            "GB200 NVL72 랙(120kW/랙)에서는 공랭 자체가 불가 → DLC 강제 선택. "
            "2025년 이후 신규 AI DC의 90%+가 DLC 채택 예상 (Vertiv IR 인용)."
        )

        _add_heading(doc, "직접수냉(DLC) vs 공랭 CapEx 비교표", 2)
        doc.add_paragraph(
            "동일한 10MW IT 부하 데이터센터 기준 초기 투자 비용(CapEx) 비교:"
        )
        cooling_rows = [
            ["공랭 (Air)", "~$4M", "~$2M", "~$6M", "PUE 1.4-1.6",
             "50kW/랙 이하 적합"],
            ["공랭+Rear Door HX", "~$5M", "~$2.5M", "~$7.5M", "PUE 1.3-1.4",
             "80kW/랙까지"],
            ["직접수냉 DLC (CDU방식)", "~$8M", "~$4M", "~$12M", "PUE 1.15-1.2",
             "120kW/랙 (GB200 NVL72)"],
            ["액침냉각 (단상)", "~$15M", "~$5M", "~$20M", "PUE 1.05-1.1",
             "고밀도 AI 전용"],
            ["액침냉각 (이상)", "~$25M", "~$6M", "~$31M", "PUE 1.02-1.05",
             "차세대 초고밀도"],
        ]
        _add_table(doc, ["냉각 방식", "냉각 장비 CapEx", "배관/설비 CapEx",
                          "총 냉각 CapEx", "달성 PUE", "적합 랙 밀도"],
                   cooling_rows)
        doc.add_paragraph(
            "투자 시사점: DLC CapEx는 공랭 대비 2배이나, 10년 TCO 기준 절감액이 CapEx 초과. "
            "수혜 기업: Vertiv(CDU 제조 글로벌 1위), CoolIT Systems(DLC 전문), "
            "국내 에코캡(냉각 유체 공급). "
            "GB200 NVL72의 강제 채택으로 DLC 시장 2024-2027년 CAGR 35%+ 예상."
        )

    if level >= 3:
        _add_heading(doc, "전문가 심층 분석")
        doc.add_paragraph(
            "이 섹션은 Level 3 전문가 과정으로, 핵융합·SMR(소형모듈원자로)의 "
            "데이터센터 전력 공급 가능성과 2030년 글로벌 전력망 임팩트 분석을 다룹니다."
        )

        _add_heading(doc, "핵융합/SMR 데이터센터 전력 시나리오", 2)
        doc.add_paragraph(
            "AI 데이터센터의 폭발적 전력 수요가 기존 전력망 한계를 초과하면서 "
            "차세대 발전 기술이 주목받고 있습니다."
        )
        power_tech_rows = [
            ["SMR (소형모듈원자로)",
             "Kairos Power, NuScale, X-energy",
             "300-500MW급, 건설기간 5-7년",
             "Google: 2030년까지 7기(500MW) 계약 (Kairos Power). "
             "Microsoft: Constellation TMI 재가동 계약. "
             "Amazon: X-energy 협력 발표",
             "2030년 소수 DC에 공급 시작 가능",
             "높음 (장기)"],
            ["핵융합 발전",
             "Commonwealth Fusion (SPARC), TAE Technologies",
             "100MW급 시범, 2035년 이후",
             "Google·Microsoft 탄소중립 목표 달성 카드. "
             "Microsoft: Helion Energy $1B 투자 (2023)",
             "2035년 이후 일부 DC 공급 가능",
             "낮음 (장기 실험)"],
            ["지열 발전",
             "Fervo Energy, Quaise Energy",
             "Enhanced Geothermal System (EGS)",
             "Google: Fervo Energy 계약 (30MW, 네바다). "
             "24시간 무탄소 전력 공급 가능",
             "현재 소규모, 2027년 확장 예정",
             "중간 (지역 제한)"],
            ["오프그리드 AI DC",
             "자체 발전 + 배터리 BESS 결합",
             "전력망 독립, 재생에너지 + 저장",
             "Meta 텍사스 150MW 태양광 직접 연결 DC. "
             "Microsoft 아이슬란드 지열 DC",
             "소수 선진 케이스",
             "높음 (특정 지역)"],
        ]
        _add_table(doc, ["기술", "주요 플레이어", "규모/일정",
                          "실제 사례", "현실적 기여 시점", "가능성"],
                   power_tech_rows)
        doc.add_paragraph(
            "전문가 관점: SMR은 2030년대 이후 AI DC 전력의 10-15%를 담당할 수 있는 "
            "유일한 현실적 대안. 핵융합은 2040년 이전 상업화 가능성 낮음. "
            "단기(2025-2028): 천연가스 Peaker Plant + 재생에너지 혼합이 현실적 해법. "
            "투자 기회: SMR 관련주 (BWX Technologies, NuScale) — 장기 포지션."
        )

        _add_heading(doc, "2030 글로벌 전력망 임팩트 분석", 2)
        doc.add_paragraph(
            "AI 데이터센터 급증이 글로벌 전력망에 미칠 구조적 영향을 2030년까지 분석합니다."
        )
        grid_impact_rows = [
            ["미국", "현재 4,500 TWh/년",
             "AI DC 추가 수요 2030E: +500-800 TWh/년 (+11-18%)",
             "전력망 투자 $3.5T 필요 (Goldman). "
             "텍사스 ERCOT 피크 수요 2026년 사상 최고 예상. "
             "변압기 리드타임 70-100주 → 신규 연결 지연",
             "중단기 전력 요금 상승 → AI DC OpEx 증가"],
            ["유럽", "현재 2,800 TWh/년",
             "+200-350 TWh/년 (+7-12%)",
             "재생에너지 비중 높아 탄소중립 유리. "
             "독일 탈원전 후 전력 부족 심화. "
             "아일랜드: DC가 국가 전력 소비 21%",
             "DC 신규 허가 제한 강화 가능성"],
            ["아시아 (한국/일본/대만)", "한국 현재 580 TWh/년",
             "한국 +30-50 TWh/년 (AI DC + 반도체 공장)",
             "한국 RE100 달성 2050년 목표 → AI DC 탄소 압박. "
             "TSMC 대만 공장 전력 부족 → 정전 리스크. "
             "일본 원전 재가동으로 일부 완화",
             "반도체 공장 + AI DC 이중 수요 → 전력 부족 구조화"],
            ["중국", "현재 8,800 TWh/년",
             "+600-900 TWh/년 (+7-10%)",
             "석탄 발전 여전히 60%. AI DC 탄소 집약도 높음. "
             "신재생 투자 세계 최대, 수급 불균형 해소 중",
             "서방 대비 전력 비용 낮음 → AI 비용 경쟁력"],
        ]
        _add_table(doc, ["지역", "현재 전력 소비", "AI DC 추가 수요",
                          "주요 이슈", "투자 시사점"],
                   grid_impact_rows)
        doc.add_paragraph(
            "2030년 글로벌 AI DC 전력 수요 총합: 500-1,200 TWh/년 (현재 글로벌 소비 ~29,000 TWh의 1.7-4.1%). "
            "단일 산업으로는 전례 없는 수요 급증. "
            "수혜 투자 테마: 전력 인프라 (GE Vernova, Eaton, ABB), "
            "에너지 저장 (Tesla Megapack, Fluence), "
            "전력 유틸리티 (NextEra Energy, Constellation Energy)."
        )

    # ══════════════════════════════════════════════════════════
    # 8장. 복습 문제
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "8장. 복습 문제 — 능동적 학습")

    doc.add_paragraph(
        "페인만 기법: 아래 질문에 '상대방에게 설명하듯' 답할 수 있으면 이해한 것입니다. "
        "막히는 부분이 있으면 해당 장으로 돌아가서 다시 읽으세요."
    )

    questions = [
        (
            "GB200 NVL72 랙 1개의 전력 소비(120kW)가 '전통 DC 건물 전체' 전력과 비교될 때 "
            "어떤 수치가 맞는지 계산하고, 이것이 데이터센터 설계에 의미하는 바를 설명하세요.",
            "1장 참고. 전통 DC 랙 평균 5-10kW와 GB200 120kW를 비교하세요. "
            "1,000랙 규모 AI DC의 총 전력 = 몇 GW인지 계산해보세요.",
            "정량 계산 (비즈니스 수학)"
        ),
        (
            "PUE 1.5와 PUE 1.1의 차이가 1GW 데이터센터에서 연간 전력 비용에 "
            "얼마나 영향을 미치는지 계산하고, 액침냉각 도입을 정당화할 수 있는지 논하세요.",
            "5장 계산 예제 참고. 전력단가 $0.07/kWh, 연간 8,760시간으로 계산하세요.",
            "정량 계산 + 투자 분석"
        ),
        (
            "미국 대형 변압기 리드타임이 30개월인 이유를 3가지 구조적 원인으로 설명하고, "
            "이 병목이 글로벌 AI DC 건설 일정에 어떤 영향을 미치는지 설명하세요.",
            "4장 참고. 제조 공정, 소재(규소강판), 미국 내 생산 공동화를 연결하세요.",
            "경쟁 분석 (공급망 병목)"
        ),
        (
            "Vertiv의 수주 잔고 $7B+가 왜 '주가 선행 지표'로 해석되는지 "
            "B2B 반도체 산업의 수주-출하 선행 패턴과 연결해 설명하세요.",
            "6장 + 7장 참고. 수주 잔고 = 미래 확정 매출. "
            "반도체 마케팅에서 Design Win과의 유사성을 생각해보세요.",
            "비즈니스 분석 (선행 지표)"
        ),
        (
            "'Phase 3 투자 파동' 논리에서 전력 인프라가 Phase 1(GPU)보다 "
            "늦게 주목받는 이유를 투자자의 심리와 정보 비대칭 관점에서 설명하세요.",
            "7장 참고. 병목이 전환되는 시점, 미디어 보도 타이밍, "
            "일반 투자자의 정보 접근성을 고려하세요.",
            "투자 분석 (사이클 이해)"
        ),
        (
            "당신이 현대일렉트릭의 B2B 마케팅 담당자라면, "
            "미국 하이퍼스케일 DC 고객에게 현대일렉트릭 변압기 선택을 설득하기 위해 "
            "어떤 논리와 데이터를 사용하겠습니까? (ABB, GE Vernova 대비 차별화 포함)",
            "4장 + 6장 참고. 리드타임 단축 가능성, 가격 경쟁력, "
            "미국 수출 실적(신뢰성 증거)을 활용하세요.",
            "실무 적용 (마케터 관점)"
        ),
    ]
    _quiz_section(doc, questions)

    # ── 정답 가이드 ──────────────────────────────────────────
    _add_heading(doc, "정답 가이드 (핵심 포인트)", 2)
    answers = [
        ("Q1 핵심",
         "1,000랙 AI DC × 120kW = 120MW. "
         "기존 DC 1,000랙 × 7.5kW = 7.5MW (16배 차이). "
         "AI DC 설계 영향: ① 전력 인입 용량 16배 확대. "
         "② 냉각 시스템 전면 교체(공랭→수냉). "
         "③ 건물 구조(바닥 하중) 강화. ④ 변압기 신규 발주 필수."),
        ("Q2 핵심",
         "PUE 1.5 총 전력: 1GW × 1.5 = 1.5GW. "
         "PUE 1.1 총 전력: 1GW × 1.1 = 1.1GW. "
         "절감: 400MW × 8,760h × $0.07 = $245M/년. "
         "액침냉각 설치비 ~$100M → 0.4년 만에 회수 → 경제적 정당화 충분."),
        ("Q3 핵심",
         "① 미국 내 대형 변압기 제조사 감소 (제조업 공동화). "
         "② 핵심 소재(규소강판) 공급망 집중 (일본·한국 소수). "
         "③ 대형 변압기는 맞춤 제작 필수 (표준화 불가). "
         "AI DC 영향: 건설 완료 후 전력 연결까지 30개월 추가 대기 → "
         "2025년 착공 DC는 빨라야 2027-2028년 전력 확보."),
        ("Q4 핵심",
         "수주 잔고 = 이미 계약된 미래 매출 (취소 어려운 B2B 계약). "
         "반도체 Design Win과 동일 구조: 선정 → 설계 → 납품 사이클. "
         "$7B / $8.5B(2025E 매출) = 0.8년치 확정. "
         "즉 2025년 예상 매출의 80%가 이미 확보 → 실적 가시성 높음 → PER 프리미엄 정당화."),
        ("Q5 핵심",
         "Phase 1(GPU)이 먼저 보이는 이유: ① 제품 발표·미디어 노출 집중. "
         "② 반도체 투자자·애널리스트가 먼저 추적. "
         "Phase 3이 늦게 주목받는 이유: ① '전력'은 반도체 투자자에게 낯선 섹터. "
         "② 변압기·냉각 기업은 산업재 섹터 → 다른 투자자 그룹. "
         "③ 정보 연결 필요: GPU 수요 → DC 건설 → 전력 수요 추론 필요. "
         "이 정보 비대칭이 Phase 3의 초과 수익 기회를 만듦."),
        ("Q6 핵심",
         "차별화 논리: ① 리드타임: 현대일렉트릭 24개월 vs 서방 경쟁사 30-36개월 → "
         "6-12개월 빠른 DC 가동 = 수억 달러 조기 수익 실현. "
         "② 가격: 한국 제조 기반 → 동급 대비 10-20% 낮은 가격. "
         "③ 신뢰성: 미국 수출 실적(마이크로소프트, 구글 공급 사례 제시). "
         "④ CHIPS Act/IRA 보조금 적격 가능성 언급."),
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
    out = OUTPUT_DIR / f"study_power_infrastructure{level_suffix}_{today_str}.docx"
    doc.save(str(out))
    print(f"  [Power Infra Study] 생성 완료: {out}")
    print(f"  [Power Infra Study] 8장 구성, {len(REFS)}개 참고자료, 6문항 복습 문제 (Level {level})")
    return str(out)


def run(level=1):
    return {"word_path": build(level)}


if __name__ == "__main__":
    run()
