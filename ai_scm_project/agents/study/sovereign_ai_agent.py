"""
Sovereign AI & 지정학적 반도체 전략 심화 Study Agent
대상: 반도체 마케팅 종사자 (비즈니스 배경 ○, 지정학적 맥락 보완 필요)

학습 목표:
  - 국가별 AI 주권 전략과 반도체 수요 규모를 파악
  - 미-중 반도체 전쟁과 수출 규제가 시장에 미치는 영향 분석
  - 지정학적 리스크/기회를 투자 관점으로 전환하는 프레임워크 습득

출력: outputs/reports/study_sovereign_ai_YYYYMMDD.docx
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
    "NVIDIA_SovereignAI": (
        "NVIDIA — Sovereign AI 개념 및 전략",
        "https://www.nvidia.com/en-us/industries/sovereign-ai/",
        "Jensen Huang의 Sovereign AI 정의, 국가별 파트너십 사례, GPU 수요 전망", "2024"
    ),
    "BIS_Export_Rules": (
        "U.S. Bureau of Industry and Security (BIS) — Export Control Rules",
        "https://www.bis.doc.gov/index.php/regulations/export-administration-regulations-ear",
        "반도체 수출 규제 상세: H100/A100 중국 수출 금지, 개정 이력", "2023-2024"
    ),
    "CHIPS_Act": (
        "U.S. CHIPS and Science Act — 공식 문서",
        "https://www.commerce.gov/tags/chips-and-science-act",
        "$53B 반도체 제조 보조금, TSMC/삼성/인텔 미국 팹 건설 지원", "2022-2025"
    ),
    "EU_Chips_Act": (
        "European Chips Act — 공식 문서",
        "https://digital-strategy.ec.europa.eu/en/policies/european-chips-act",
        "€43B 투자, EU 반도체 자급률 2030년까지 20% 목표", "2023"
    ),
    "UAE_AI_Strategy": (
        "UAE AI Office — National AI Strategy 2031",
        "https://ai.gov.ae/",
        "UAE AI 국가전략, G42 파트너십, NVIDIA GPU 100만개 계약 배경", "2024"
    ),
    "Saudi_Vision2030_AI": (
        "Saudi Vision 2030 — AI & Technology",
        "https://www.vision2030.gov.sa/en/",
        "사우디 $40B AI 투자 계획, NEOM AI 인프라, Humain AI 회사 설립", "2024"
    ),
    "Huawei_Ascend": (
        "Huawei — Ascend AI Processor",
        "https://www.huawei.com/en/technology/ascend-ai",
        "Ascend 910B 스펙, 중국 자국 AI 칩 전략, H100 대비 성능 비교", "2024"
    ),
    "DeepSeek_R1": (
        "DeepSeek — R1 Technical Report",
        "https://arxiv.org/abs/2501.12948",
        "H800 2,048개로 GPT-4급 성능 달성, 효율화 쇼크, 비용 $6M 학습", "2025"
    ),
    "TSMC_USA_Fab": (
        "TSMC — Arizona Fab Investment",
        "https://pr.tsmc.com/english/news/arizona",
        "미국 3개 팹 건설 $65B 투자, 2nm 공정 포함, 2028년 완공 목표", "2024"
    ),
    "SemiAnalysis_China": (
        "SemiAnalysis — China Semiconductor Self-Sufficiency",
        "https://www.semianalysis.com/p/china-semiconductor-self-sufficiency",
        "중국 AI 칩 자립 현황 분석, SMIC 7nm 수율, 실제 달성률 ~30%", "2024"
    ),
    "NVIDIA_H20": (
        "NVIDIA — H20 China Export Product",
        "https://www.nvidia.com/",
        "H20 스펙(H100 다운그레이드), 중국 시장 수익 변화, 규제 준수 전략", "2024"
    ),
    "India_AI_Mission": (
        "India AI Mission — Government of India",
        "https://indiaai.gov.in/",
        "India AI Mission $1.25B 예산, 10,000 GPU 클러스터 구축, NVIDIA 협력", "2024"
    ),
    "Japan_AI_Strategy": (
        "Japan Digital Agency — AI Strategy",
        "https://www.digital.go.jp/en/",
        "일본 $7B AI 인프라 투자, Rapidus 2nm 파운드리, TSMC 구마모토 JV", "2024"
    ),
    "SK_Hynix_Export": (
        "SK Hynix — HBM Export & Global Strategy",
        "https://www.skhynix.com/eng/ir/",
        "SK하이닉스 HBM 수출 전략, 미국·유럽 얼라이언스 공급 확대", "2024"
    ),
    "Goldman_Geopolitics": (
        "Goldman Sachs — Geopolitical Risk in Semiconductors",
        "https://www.goldmansachs.com/insights/articles/geopolitics-semiconductors",
        "반도체 지정학 리스크 분석, 공급망 다변화 수혜주 선정", "2024"
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
        print("  [Sovereign AI Study] python-docx 미설치")
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
    t = doc.add_heading(f"{level_prefix}Sovereign AI & 지정학적 반도체 전략 심화", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s = doc.add_paragraph("국가 AI 주권부터 미-중 반도체 전쟁까지 — 투자 시사점 분석")
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s2 = doc.add_paragraph(
        f"대상: 반도체 마케팅 종사자  |  기준일: {config.AS_OF_DATE}  |  "
        f"난이도: 비즈니스 → 지정학 심화"
    )
    s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in s2.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(100, 100, 100)

    desc = doc.add_paragraph(
        "\n본 문서는 Sovereign AI(국가 AI 주권) 트렌드와 지정학적 반도체 전략을 "
        "반도체 마케팅 관점에서 심화 분석하는 학습 자료입니다. "
        "국가별 AI 투자 규모, 수출 규제의 시장 영향, 중국 자립화 현황, "
        "한국의 포지션까지 체계적으로 다룹니다."
    )
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in desc.runs:
        run.font.size = Pt(9)
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 1장. Sovereign AI란?
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "1장. Sovereign AI란? — 국가 안보와 AI 주권의 교차점")

    doc.add_paragraph(
        "2024년 가장 주목받는 반도체 수요 트렌드 중 하나는 "
        "'Sovereign AI' — 국가가 자국의 AI 인프라를 직접 구축하고 통제하려는 움직임입니다. "
        "이 트렌드는 단순한 기술 투자를 넘어 안보, 경제, 데이터 주권과 연결됩니다."
    )

    _add_heading(doc, "1.1 Jensen Huang의 Sovereign AI 정의", 2)
    _concept(doc,
        "NVIDIA CEO Jensen Huang (2024 GTC 키노트): "
        "'모든 국가는 자국의 데이터, 문화, 가치관을 담은 AI를 소유해야 합니다. "
        "AI는 새로운 전기(電氣)이고, 국가 AI 인프라는 새로운 공공재입니다.' "
        "이 발언은 단순 홍보가 아닌 전략적 메시지: 각 국가에 AI GPU를 팔겠다는 선언.")
    _marketing(doc,
        "마케터 관점: Sovereign AI = NVIDIA의 새로운 시장 세그먼트. "
        "기존 고객(Microsoft, Google, Amazon)에 더해 "
        "190개 국가 정부가 잠재 고객이 됩니다. "
        "단가(GPU 단가)가 아닌 국가 계약 규모($10B~100B+)로 거래가 성사됩니다.")

    _add_heading(doc, "1.2 데이터 주권이 핵심인 이유", 2)
    _concept(doc,
        "데이터 주권(Data Sovereignty): 자국 데이터가 외국 서버(미국 클라우드)에 "
        "저장·처리되는 것에 대한 법적·안보적 우려. "
        "GDPR(유럽), 중국 사이버보안법, UAE 데이터 현지화 법 등이 대표 사례.")
    _concept(doc,
        "AI 학습 데이터에는 국가 안보와 직결되는 정보가 포함될 수 있습니다:\n"
        "• 군사·외교 문서 → 외국 AI에 학습시킬 수 없음\n"
        "• 의료·금융 데이터 → 개인정보보호법 위반 우려\n"
        "• 문화·언어 정체성 → 외국 AI가 자국어를 제대로 이해 못할 수 있음")
    _marketing(doc,
        "비즈니스 임팩트: 이 우려를 해소하는 방법은 하나 — 자국 데이터센터에 "
        "AI GPU를 직접 구매·운영하는 것. NVIDIA의 판매 메시지가 여기에 맞춰져 있습니다.")

    _add_refs(doc, ["NVIDIA_SovereignAI"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 2장. 주요 국가별 AI 프로그램
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "2장. 주요 국가별 Sovereign AI 프로그램")

    doc.add_paragraph(
        "2024-2025년 전 세계 주요 국가들이 대규모 AI 인프라 투자를 발표하고 있습니다. "
        "각 국가의 투자 규모, 목표, 파트너십을 분석하면 GPU 수요의 지역별 분포가 보입니다."
    )

    _add_heading(doc, "2.1 국가별 AI 투자 비교표", 2)
    country_rows = [
        ["UAE",    "$100B",  "중동 AI 허브, 글로벌 데이터센터",  "NVIDIA, Microsoft, G42",  "GPU 100만+개 (최대 규모)"],
        ["사우디",  "$40B",   "Vision 2030 AI 전환, NEOM",      "NVIDIA, Google, Humain",  "GPU 30만~50만개 추정"],
        ["EU",     "€20B",   "EU AI 자립, 2030년 제조 20%",    "TSMC(아일랜드·독일), 인텔", "분산 투자, 규제 중심"],
        ["일본",   "$7B",    "반도체 자립, Rapidus 2nm",        "TSMC, NVIDIA, ARM",       "GPU 10만개 + 국내 팹"],
        ["인도",   "$1.25B", "인도어 AI, 10만 GPU 클러스터",    "NVIDIA, Google, Microsoft","GPU 10만개 (Phase 1)"],
        ["한국",   "$2B+",   "국가 AI 컴퓨팅 센터, K-AI",      "SK하이닉스, 삼성, NAVER",  "GPU 수만 개 + HBM 수출"],
        ["프랑스", "€6B",    "AI 주권, Mistral AI 육성",        "Microsoft($4B), NVIDIA",   "GPU 2만개+ 국가 클러스터"],
        ["싱가포르","$1B+",  "아시아 AI 허브",                  "NVIDIA, Google, AWS",     "GPU 수만 개 + 규제 프리존"],
    ]
    _add_table(doc,
        ["국가", "투자규모", "목표", "파트너", "GPU 수요"],
        country_rows)

    _add_heading(doc, "2.2 UAE — 가장 큰 Sovereign AI 고객", 2)
    _concept(doc,
        "UAE AI 전략의 핵심 수치:\n"
        "• Microsoft-UAE 파트너십: $1.5T 규모 AI 투자 파트너십 (2024년 발표)\n"
        "• G42(Abu Dhabi): NVIDIA와 GPU 100만개 이상 구매 계약\n"
        "• 투자 재원: 석유 수출 수익의 AI 재투자 ('오일머니 → AI머니')\n"
        "• 목표: 2031년까지 글로벌 AI 허브 Top 5 진입")
    _marketing(doc,
        "UAE의 전략적 의미: 수출 규제 없음(비중국권 동맹국). "
        "최고 사양 NVIDIA GPU(H100, B200) 무제한 구매 가능. "
        "중동 자본 + 미국 기술의 결합 → NVIDIA에게 가장 이상적인 국가 고객.")

    _add_heading(doc, "2.3 사우디 — 오일머니의 AI 전환", 2)
    doc.add_paragraph(
        "사우디아라비아 AI 투자 현황:\n\n"
        "• $40B AI 인프라 투자 계획 (Vision 2030의 디지털 전환 축)\n"
        "• Humain AI: 2024년 설립한 국영 AI 회사, NVIDIA와 파트너십\n"
        "• NEOM(스마트시티): AI 기반 도시 운영 → 대규모 GPU 클러스터 필요\n"
        "• Google Cloud: $2B 사우디 투자 약속, AI 인프라 공동 구축"
    )

    _add_refs(doc, ["UAE_AI_Strategy", "Saudi_Vision2030_AI", "NVIDIA_SovereignAI"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 3장. 수출 규제 & 반도체 전쟁
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "3장. 수출 규제 & 반도체 전쟁 — BIS 규제의 시장 영향")

    doc.add_paragraph(
        "미국 상무부 BIS(Bureau of Industry and Security)의 반도체 수출 규제는 "
        "AI 반도체 시장의 지형을 근본적으로 바꾸고 있습니다. "
        "규제의 배경, 구체적 내용, 시장 영향을 분석합니다."
    )

    _add_heading(doc, "3.1 BIS 수출 규제 연혁", 2)
    bis_rows = [
        ["2022.10", "1차 규제", "A100/H100 중국 수출 금지. 성능 기준(TFLOP 기반) 도입"],
        ["2023.10", "2차 강화", "A800/H800 등 우회 칩도 규제. 40개국 '우려 국가' 리스트"],
        ["2024.01", "VEU 제도", "Verified End User — 검증된 해외 기업에만 허가 방식 도입"],
        ["2024.10", "3차 강화", "H20 규제 포함 검토, 동맹국 외 전면 허가제 강화"],
        ["2025~",   "추가 규제", "차세대 GPU(B200) 규제, 클라우드 접근 제한 논의 중"],
    ]
    _add_table(doc, ["시기", "규제명", "내용"], bis_rows)

    _add_heading(doc, "3.2 CHIPS Act & EU Chips Act", 2)
    _concept(doc,
        "CHIPS and Science Act (2022): 미국 내 반도체 제조 강화를 위한 $53B 투자법.\n"
        "• 제조 보조금: $39B (TSMC, 삼성, 인텔, Micron 미국 팹 건설 지원)\n"
        "• R&D 지원: $11B (NIST, NSF 반도체 연구)\n"
        "• 인력 교육: $2B\n"
        "• 가드레일: 보조금 수령 기업은 10년간 중국 팹 확장 불가")
    _concept(doc,
        "EU Chips Act (2023): 유럽 반도체 자급률 2030년 10% → 20% 목표.\n"
        "• 총 €43B 공공·민간 투자 동원\n"
        "• TSMC 독일 드레스덴 팹 (€10B), 인텔 독일 마그데부르크 팹 (€30B)\n"
        "• 실질 진전: 인텔 팹 지연, TSMC 독일 팹만 2027년 가동 예정")
    _marketing(doc,
        "마케터 관점: CHIPS Act = 미국·유럽에서 반도체 제조 재건. "
        "삼성·SK하이닉스 미국 팹 건설 → 미국 고객에게 '미국산' HBM/메모리 판매 가능. "
        "지정학적 인증이 곧 새로운 영업 무기가 됩니다.")

    _add_refs(doc, ["BIS_Export_Rules", "CHIPS_Act", "EU_Chips_Act"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 4장. 한국의 포지션
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "4장. 한국의 포지션 — AI 공급망 핵심 허브")

    doc.add_paragraph(
        "한국은 AI 반도체 공급망에서 독특한 위치를 점하고 있습니다. "
        "HBM(SK하이닉스 1위, 삼성 2위) 공급에서 국내 AI 인프라 구축까지, "
        "한국의 전략적 가치와 리스크를 분석합니다."
    )

    _add_heading(doc, "4.1 SK하이닉스 — HBM 수출 전략", 2)
    _concept(doc,
        "SK하이닉스 HBM 글로벌 위상 (2024 기준):\n"
        "• HBM 시장점유율: ~52% (세계 1위)\n"
        "• NVIDIA H100/H200/B200의 주요 HBM 공급사\n"
        "• HBM 매출 비중: 2023 ~5% → 2025 ~40%+\n"
        "• 미국 인디애나 팹 패키징 투자: CHIPS Act 보조금 신청")
    _marketing(doc,
        "SK하이닉스의 지정학 전략: '동맹국 편'. "
        "미국·일본·유럽 동맹 고객에 우선 공급, 중국 HBM 공급 극도로 제한. "
        "이 포지션 덕분에 미국 정부의 규제 위험에서 벗어나 있고, "
        "CHIPS Act 보조금도 수혜 가능.")

    _add_heading(doc, "4.2 삼성 — 도전과 재건", 2)
    doc.add_paragraph(
        "삼성의 현재 상황과 전략:\n\n"
        "• HBM3e 인증 지연: NVIDIA 공급 비중 낮음 (SK하이닉스 대비 열위)\n"
        "• TSMC 대안: 삼성 파운드리 SF3/SF2 공정 개선 중 (4nm 수율 개선)\n"
        "• 미국 텍사스 테일러 팹: $25B 투자, 2nm+ 공정 목표, 2026~\n"
        "• 전략적 재건: HBM4에서 기술 격차 만회 시도, 비NVIDIA 고객 다변화"
    )
    _risk(doc,
        "삼성 리스크: HBM 인증 지연 장기화 시 HBM4 경쟁에서도 뒤처질 가능성. "
        "파운드리 적자 지속. 중국 시장 매출 의존도 규제로 압박.")

    _add_heading(doc, "4.3 국내 AI 인프라 현황", 2)
    korea_rows = [
        ["NAVER Cloud", "국내 최대 AI 클러스터", "H100 수천개, 한국어 LLM HyperCLOVA X"],
        ["KT·SKT",      "통신사 AI 데이터센터",  "기업 AI 서비스, GPU 서버 임대"],
        ["정부(NHN)",   "국가 AI 컴퓨팅 센터",  "2024~2025 구축, 연구자 AI 컴퓨팅 지원"],
        ["대학·연구소", "KAIST·포스텍 등",       "국가 연구 클러스터, GPU 소규모"],
    ]
    _add_table(doc, ["기관", "역할", "현황"], korea_rows)

    _add_refs(doc, ["SK_Hynix_Export", "CHIPS_Act"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 5장. 중국 AI 반도체 자립
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "5장. 중국 AI 반도체 자립 — 현실과 격차")

    doc.add_paragraph(
        "중국 정부는 2025년까지 AI 칩 자국 생산 70% 목표를 발표했습니다. "
        "실제 달성률은 ~30% 수준입니다. "
        "중국 AI 칩 자립의 현황, 한계, 그리고 DeepSeek 쇼크를 분석합니다."
    )

    _add_heading(doc, "5.1 중국 AI 칩 생태계", 2)
    china_chips = [
        ["Huawei Ascend 910B", "AI 학습 GPU",     "H100 대비 60-70% 성능 추정",     "SMIC 7nm(N+2)"],
        ["Biren BR100",        "AI GPU",           "H100급 목표, 양산 불확실",        "TSMC 7nm (규제 전)"],
        ["Cambricon 580",      "AI 추론 가속기",   "엣지·서버 추론 특화",            "7nm급"],
        ["Alibaba Hanguang 910","추론 전용 ASIC",  "자체 클라우드 최적화",           "7nm"],
        ["Baidu ERNIE 칩",     "AI 학습 지원",     "바이두 자체 AI 최적화",          "7nm급"],
    ]
    _add_table(doc, ["칩명", "용도", "성능 수준", "공정"], china_chips)

    _add_heading(doc, "5.2 SMIC — 제재 속의 중국 파운드리", 2)
    _concept(doc,
        "SMIC(중국 최대 파운드리): ASML EUV 장비 수입 금지로 첨단 공정 개발 제약.\n"
        "• 7nm(N+2): DUV 멀티패터닝으로 구현. 수율 낮음(추정 40-60%).\n"
        "• 5nm 이하: 현재로서는 양산 불가. EUV 없이 5nm 구현 난이도 극단적.\n"
        "• Huawei Mate 60 Pro: SMIC 7nm Kirin 9000S → '금지선 돌파' 논란 유발.")
    _risk(doc,
        "투자 리스크: 중국이 SMIC 7nm 수율을 빠르게 개선할 경우 "
        "H100 대비 성능은 낮지만 '충분히 싼' AI 칩을 대량 공급 가능. "
        "단, TSMC 5nm 대비 성능·전력 효율 격차는 수년간 좁혀지기 어려움.")

    _add_heading(doc, "5.3 DeepSeek 쇼크 — 효율화의 역설", 2)
    _concept(doc,
        "DeepSeek R1 (2025.01 발표):\n"
        "• 학습 비용: H800 2,048개 × 약 55일 = 총 비용 ~$6M\n"
        "• 성능: 수학·코딩 벤치마크에서 GPT-4o, Claude 3.5와 동급\n"
        "• 비교: OpenAI GPT-4 학습 비용 추정 $100M+ 대비 1/17\n"
        "• 방법론: MoE(Mixture of Experts) + 강화학습(GRPO) 최적화")
    _marketing(doc,
        "DeepSeek의 투자 시사점 (두 가지 상반된 해석):\n"
        "① 약세론: AI 칩 효율화로 GPU 수요 감소 → NVIDIA 주가 -17% (단기)\n"
        "② 강세론: 효율화는 더 많은 AI 사용 → Jevons Paradox → "
        "GPU 총 수요 오히려 증가 (장기)\n"
        "현재 컨센서스: ②가 우세. AI 수요의 '규모 확장'이 효율화를 상쇄.")

    _add_refs(doc, ["DeepSeek_R1", "Huawei_Ascend", "SemiAnalysis_China"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 6장. NVIDIA 수출 규제 영향
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "6장. NVIDIA 수출 규제 영향 — H20과 중국 전략")

    doc.add_paragraph(
        "수출 규제로 H100/A100을 중국에 팔 수 없게 된 NVIDIA는 "
        "규제 기준선 바로 아래 성능의 '중국 전용 다운그레이드 칩' 전략을 펼칩니다."
    )

    _add_heading(doc, "6.1 다운그레이드 칩 전략", 2)
    downgrade_rows = [
        ["H100 (글로벌)",  "989 TFLOPS (BF16)", "80/141GB HBM3/3e", "3.35/4.8TB/s", "규제로 중국 판매 불가"],
        ["A800 (구중국용)","312 TFLOPS (BF16)", "80GB HBM2e",       "2TB/s",        "2023.10 규제로 금지됨"],
        ["H800 (구중국용)","989 TFLOPS",        "80GB",             "3.35TB/s",     "인터커넥트 대역폭 제한, 금지됨"],
        ["H20 (현중국용)", "296 TFLOPS (BF16)", "96GB HBM3",        "4.0TB/s",      "현재 판매 가능, 규제 검토 중"],
    ]
    _add_table(doc, ["칩명", "연산 성능", "메모리", "대역폭", "현황"], downgrade_rows)

    _add_heading(doc, "6.2 중국 시장 매출 영향", 2)
    _quant(doc,
        "NVIDIA 중국 매출 변화 분석:\n"
        "  2022 중국 매출 비중: ~26% (전체 매출 $27B × 26% = ~$7B)\n"
        "  2024 중국 매출 비중: ~12% (전체 매출 $130B+ × 12% = ~$15B)\n"
        "  → 비중은 줄었지만 절대액은 오히려 증가: 비중국 시장 폭발적 성장 덕분\n"
        "  H20만으로 중국 매출 연간 $10B+ 추정 (2024): 여전히 무시할 수 없는 규모")
    _risk(doc,
        "H20 추가 규제 시나리오: 2024~2025년 BIS가 H20도 규제하면 "
        "NVIDIA 연간 매출 $10B+ 손실 가능. "
        "이 리스크는 NVIDIA 주가의 최대 단기 불확실성 중 하나.")

    _add_heading(doc, "6.3 TSMC의 지정학 포지션", 2)
    _concept(doc,
        "TSMC의 다극화 전략:\n"
        "• 대만(본사): 최첨단 2nm/3nm 공정. 지정학 리스크 최고.\n"
        "• 미국 애리조나: 3개 팹 건설 $65B 투자. 2nm 포함. 2028년 완공.\n"
        "• 일본 구마모토: Sony와 JV, 28nm/12nm. 1공장 2024년 완공, 2공장 2027년.\n"
        "• 독일 드레스덴: 보쉬·인피니언·NXP JV, 28nm. 2027~2028년.")
    _marketing(doc,
        "투자 포인트: TSMC는 지정학 리스크 헤지를 하면서 동시에 "
        "각 지역 정부로부터 막대한 보조금을 받는 '이중 수혜' 구조. "
        "미국 팹 가동 시 CHIPS Act 최대 수혜자. "
        "삼성 파운드리보다 TSMC가 구조적으로 유리한 이유.")

    _add_refs(doc, ["NVIDIA_H20", "TSMC_USA_Fab", "BIS_Export_Rules"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 7장. 투자 시사점
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "7장. 투자 시사점 — 지정학 프리미엄과 공급망 수혜주")

    doc.add_paragraph(
        "지정학적 변화는 단기 리스크이자 장기 기회입니다. "
        "공급망 다변화, 동맹국 파운드리 육성, Sovereign AI 수요가 "
        "특정 기업에 구조적 프리미엄을 부여합니다."
    )

    _add_heading(doc, "7.1 지정학 프리미엄 수혜 구조", 2)
    geo_premium = [
        ["NVIDIA",        "Sovereign AI 수요 직접 수혜",        "중국 규제, H20 추가 규제"],
        ["TSMC",          "미국·일본 팹 CHIPS Act 보조금",       "대만 지정학 리스크, 팹 건설 비용"],
        ["SK하이닉스",     "HBM 동맹국 공급, 미국 팹 진출",       "삼성과의 경쟁, 한반도 리스크"],
        ["Micron",         "미국산 HBM, CHIPS Act 최대 수혜",    "기술 격차, 중국 매출 제한"],
        ["ASML",           "EUV 독점 → 비중국 수요 집중",         "중국 DUV 수출도 추가 규제 우려"],
        ["인텔",           "미국 파운드리 유일 → 정부 수요",      "기술 경쟁력 회복 불확실"],
    ]
    _add_table(doc, ["기업", "지정학 수혜 요인", "지정학 리스크"], geo_premium)

    _add_heading(doc, "7.2 공급망 다변화 테마 종목", 2)
    _marketing(doc,
        "탈중국 수혜: TSMC(대만 의존 완화 → 미국·일본 팹), "
        "Micron(중국 의존 없는 미국산 메모리), "
        "Applied Materials·Lam Research(중국 수출 금지 → 비중국 장비 수요 집중).")
    _marketing(doc,
        "Sovereign AI 직접 수혜 종목: NVIDIA(GPU 독점 공급), "
        "SK하이닉스(HBM 필수 공급), TSMC(파운드리 독점), "
        "Vertiv(데이터센터 인프라).")
    _risk(doc,
        "지정학 리스크 집중 종목: 대만 집중도 높은 기업(TSMC, ASE, MediaTek), "
        "중국 매출 비중 높은 기업(Qualcomm 66%, Broadcom 35%, Micron 50%→규제 후 20%). "
        "이들은 긴장 고조 시 멀티플 압축 우선 대상.")

    _add_heading(doc, "7.3 시나리오별 투자 포지셔닝", 2)
    scenario_rows = [
        ["미-중 긴장 완화",  "중국 규제 완화, H20 판매 확대",       "NVIDIA, Qualcomm, TSMC 전체"],
        ["현상 유지(기본)",  "H20 규제 유지, Sovereign AI 지속",    "NVIDIA, SK하이닉스, Broadcom"],
        ["긴장 고조",        "H20 추가 규제, 대만 위기 우려 증가",  "Micron(미국산), 인텔, ASML"],
        ["기술 분리 가속",   "미-중 기술 완전 디커플링",            "미국 동맹국 전체 AI 공급망"],
    ]
    _add_table(doc, ["시나리오", "내용", "수혜 종목"], scenario_rows)

    _add_refs(doc, ["Goldman_Geopolitics", "CHIPS_Act", "TSMC_USA_Fab"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 레벨별 심화 섹션 (8장 복습 문제 직전)
    # ══════════════════════════════════════════════════════════
    if level >= 2:
        _add_heading(doc, "심화 분석")
        doc.add_paragraph(
            "이 섹션은 Level 2 심화 과정으로, 반도체 수출 규제 이력 타임라인 표와 "
            "중국의 반도체 자립 달성 시나리오를 다룹니다."
        )

        _add_heading(doc, "반도체 수출 규제 이력 타임라인", 2)
        doc.add_paragraph(
            "미국 BIS(Bureau of Industry and Security)의 대중국 반도체 수출 규제 연대기를 "
            "정리합니다. 각 규제가 시장에 미친 영향도 포함합니다."
        )
        regulation_rows = [
            ["2019.05",
             "Huawei Entity List 추가",
             "TSMC, Qualcomm의 Huawei 거래 중단. "
             "Huawei Kirin 칩 생산 불가",
             "Huawei 스마트폰 점유율 15% → 3%로 급락",
             "중국 자체 칩 개발 가속화 촉발"],
            ["2020.09",
             "SMIC Entity List 추가",
             "ASML EUV 장비 공급 차단. "
             "미국 기술 포함 장비 SMIC 수출 금지",
             "SMIC 7nm 이하 진입 사실상 불가",
             "중국 파운드리 최대 타격"],
            ["2022.10",
             "A100/H100 수출 규제 (CCL)",
             "A100 급 (≥4,800 TOPS) 중국 수출 금지. "
             "장비 규제 강화 (KrF/ArF 이머전 포함)",
             "NVIDIA 중국 매출 즉시 $4B 감소",
             "A800/H800 다운그레이드 버전 개발"],
            ["2023.10",
             "H800/A800 추가 규제",
             "다운그레이드 버전도 금지. "
             "40Gbps 이상 칩-투-칩 대역폭 기준 추가",
             "NVIDIA 중국 매출 $5B → 거의 0",
             "H20만 허용 (대역폭 896GB/s)"],
            ["2024.01",
             "AI 모델 가중치 수출 규제 논의",
             "오픈소스 모델 포함 규제 검토. "
             "최종 규제는 미적용 (2024년 기준)",
             "Meta Llama 오픈소스 정책 논란",
             "소프트웨어 규제로 확대 가능성"],
            ["2024.09",
             "미국 동맹국 협조 요청 강화",
             "일본·네덜란드에 추가 장비 규제 압박. "
             "ASML EUV 외에 DUV(ArF)도 제한 요청",
             "SMIC DUV 확보 경쟁 가속",
             "ASML 단기 수혜 (선주문 급증)"],
        ]
        _add_table(doc, ["시기", "규제 내용", "핵심 조치",
                          "즉각 영향", "장기 영향"],
                   regulation_rows)
        doc.add_paragraph(
            "규제 에스컬레이션 패턴: 중국이 우회로를 찾으면 BIS가 규제를 강화하는 '고양이-쥐 게임'. "
            "투자 시사점: 규제 발표 시 NVIDIA 단기 하락 → 매수 기회 (비중국 수요로 대체). "
            "중국 규제 강화 = 비중국 지역 AI 투자 가속 → 반도체 수요 전체 상향."
        )

        _add_heading(doc, "중국 반도체 자립 달성 시나리오", 2)
        doc.add_paragraph(
            "중국의 자국 반도체 기술 독립 달성 가능성을 3개 시나리오로 분석합니다."
        )
        china_scenarios = [
            ["Bear (자립 성공)",
             "SMIC 7nm 수율 개선 → 2027년 5nm 달성. "
             "화웨이 Ascend 910C NVIDIA H100 성능 80% 달성. "
             "중국 내 AI 수요를 자국 칩으로 충당",
             "낮음 (15-20%)",
             "EUV 없이 멀티패터닝 7nm 수율 35-40%로 경제성 없음. "
             "HBM 자체 생산 불가 (CXMT HBM 수율 미검증)",
             "NVIDIA 중국 영구 퇴출 리스크. "
             "한국 메모리 대중 수출 타격"],
            ["Base (부분 자립)",
             "AI 추론(Inference) 전용 저사양 칩 자립. "
             "학습(Training) 고사양 칩은 제한적으로 밀수입 지속. "
             "중국 AI 발전 속도 서방 대비 18-24개월 지연",
             "높음 (55-60%)",
             "현재 화웨이 Ascend 910B 일부 자립. "
             "추론용 Huawei+Baidu+Alibaba 자체칩 운영 중",
             "장기 공존 구조. "
             "중국 AI 시장은 자국 칩 생태계 형성"],
            ["Bull (자립 실패)",
             "미국·일본·네덜란드 규제 완전 공조. "
             "중국 AI 개발 기술적 한계에 봉착. "
             "DeepSeek 식 효율화에도 한계",
             "낮음 (20-25%)",
             "서방 동맹 결속력에 의존. "
             "내부 인재 유출 지속",
             "NVIDIA의 중국 외 지역 독점 완성. "
             "한국 HBM의 중국 외 수출 집중"],
        ]
        _add_table(doc, ["시나리오", "조건", "확률", "현재 증거", "한국 반도체 영향"],
                   china_scenarios)
        doc.add_paragraph(
            "현재 Base 시나리오(부분 자립)가 가장 현실적. "
            "중국은 추론(낮은 정밀도, 소규모 모델)에서는 자립 가능하나 "
            "GPT-4/Gemini 수준 학습은 2028년 이전 독자 달성 불가 전망. "
            "한국 투자자 관점: SK하이닉스 HBM의 중국 매출 비중 감소 → 미국·유럽·중동 확대로 보완."
        )

    if level >= 3:
        _add_heading(doc, "전문가 심층 분석")
        doc.add_paragraph(
            "이 섹션은 Level 3 전문가 과정으로, 미중 반도체 전쟁 3가지 시나리오와 "
            "한국 반도체의 지정학적 포지셔닝 전략을 다룹니다."
        )

        _add_heading(doc, "미중 반도체 전쟁 시나리오 3가지", 2)
        doc.add_paragraph(
            "미중 기술 패권 경쟁의 장기 전개 방향을 3개 시나리오로 분석합니다. "
            "각 시나리오가 글로벌 반도체 공급망에 미치는 영향을 포함합니다."
        )
        us_china_rows = [
            ["시나리오 1: 냉전형 기술 분리 (Decoupling)",
             "미국이 동맹국과 협력해 중국을 첨단 반도체 생태계에서 완전 배제. "
             "중국도 독자 생태계 구축 가속 (화웨이·CXMT·SMIC 중심). "
             "두 개의 평행 반도체 생태계 공존",
             "30-35%",
             "2027-2030년",
             "한국: 미국 생태계 편입 강요 → 중국 시장 포기. "
             "수익성: 미국 시장 ASP 상승(희소성)으로 단기 수혜. "
             "TSMC 미국·일본·유럽 팹 분산 → 한국 공급망 지위 변화",
             "단기 수혜, 중기 불확실"],
            ["시나리오 2: 관리된 긴장 (Managed Tension) — Base Case",
             "미국이 첨단 칩(3nm 이하, HBM4+) 만 규제. "
             "성숙 공정(28nm+)은 허용. "
             "중국이 규제 내에서 AI 발전 지속 (DeepSeek 효율화 방식)",
             "45-50%",
             "2025-2028년 (현재 경로)",
             "한국: HBM3e/HBM4 중국 판매 계속 제한. "
             "성숙 공정 메모리는 대중 수출 가능. "
             "이중 시장(미국+중국 비규제 제품) 유지",
             "현상 유지, 예측 가능"],
            ["시나리오 3: 급격한 긴장 완화 (Détente)",
             "미중 무역협상으로 일부 규제 완화. "
             "중국의 대미 희토류·소재 수출 제한 협상 카드 활용. "
             "H20급 이하 규제 철회 합의",
             "15-20%",
             "2026년 이후 (정치 변수)",
             "단기 NVIDIA 주가 급등 (중국 매출 회복). "
             "SK하이닉스 중국 수출 재개 → 단기 물량 증가. "
             "장기: 중국 AI 생태계 강화 → 서방 경쟁 심화",
             "단기 강한 수혜"],
        ]
        _add_table(doc, ["시나리오", "내용", "확률", "발생 시기",
                          "한국 반도체 영향", "투자 전략"],
                   us_china_rows)

        _add_heading(doc, "한국 반도체의 지정학적 포지셔닝 전략", 2)
        doc.add_paragraph(
            "한국 반도체 기업(SK하이닉스·삼성)이 미중 패권 경쟁에서 "
            "최적 포지션을 유지하기 위한 전략을 분석합니다."
        )
        korea_strategy_rows = [
            ["HBM 기술 독점 유지",
             "HBM4/HBM4e 세대 전환 속도 유지",
             "미국 AI 생태계의 핵심 부품 공급자 위치 확보. "
             "미국이 한국 HBM을 전략 자산으로 인식 → 외교 레버리지",
             "기술 투자 지속 + 삼성 경쟁 견제",
             "높음 (SK하이닉스 기술 우위)"],
            ["미국 현지 생산 투자",
             "SK하이닉스 인디애나 HBM 조립 공장 ($3.87B)",
             "CHIPS Act 인센티브 활용. "
             "미국 공급망 편입으로 규제 면제 지위 강화",
             "2028년 가동 목표 (현재 건설 중)",
             "중간 (투자 대비 효율 논란)"],
            ["중국 노출 축소",
             "성숙 공정(DDR4, LPDDR4) 매출 중국 의존도 단계적 감소",
             "규제 리스크 헤지. "
             "미국 정부의 한국 반도체 기업 신뢰 구축",
             "중국 DRAM 매출 30% → 2027년 15% 목표",
             "단기 수익성 희생 필요"],
            ["중동·인도 신시장 개척",
             "UAE·사우디·인도 Sovereign AI 수요 공략",
             "중국 규제 공백 채우는 수요 창출. "
             "NVIDIA 파트너로서 HBM 패키지 판매",
             "SK하이닉스 중동 현지 세일즈 강화",
             "높음 (성장성)"],
            ["기술 표준 참여",
             "JEDEC HBM 표준 위원회 주도권 유지",
             "한국 기업이 HBM 세대 스펙 결정에 영향력 행사. "
             "NVIDIA와의 JDP(Joint Development Program) 강화",
             "SK하이닉스 JEDEC 활동 인력 증원",
             "높음 (장기 경쟁력)"],
        ]
        _add_table(doc, ["전략", "세부 내용", "지정학적 이점", "실행 현황", "효과성"],
                   korea_strategy_rows)
        doc.add_paragraph(
            "결론: 한국 반도체의 최적 전략은 '친미·비적대적 대중' 포지션 유지. "
            "HBM 기술 독점을 외교 레버리지로 활용하면서, "
            "미국 현지 투자로 CHIPS Act 수혜국 지위 확보. "
            "중동·인도 신시장 개척으로 중국 매출 감소분 보완. "
            "투자자 관점: 이 전략이 성공적으로 실행되는 기업(SK하이닉스 > 삼성) 비중 확대."
        )

    # ══════════════════════════════════════════════════════════
    # 8장. 복습 문제
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "8장. 복습 문제 & 종합 정리")

    questions = [
        (
            "Sovereign AI가 단순한 기술 투자가 아닌 안보 전략인 이유를 "
            "데이터 주권 개념과 연결하여 설명하라. "
            "마케터라면 이 트렌드를 어떻게 영업 메시지로 전환하겠는가?",
            "1장의 Jensen Huang 정의와 데이터 주권 개념을 활용하세요. "
            "고객이 '왜 자국 데이터센터에 GPU를 사야 하는가'를 설명하는 방식으로 생각해보세요.",
            "개념 이해 + 실무 적용"
        ),
        (
            "UAE가 $100B 규모의 AI 투자를 하는 이유를 경제·안보·기술 관점에서 각각 설명하고, "
            "이 투자가 NVIDIA 외에 어떤 기업들에게 수혜를 주는지 분석하라.",
            "2장의 UAE 사례와 파트너 기업 리스트를 참고하세요. "
            "데이터센터 구축에 필요한 전체 공급망(GPU, 메모리, 냉각, 전력, 네트워킹)을 생각해보세요.",
            "시장 분석"
        ),
        (
            "CHIPS Act $53B의 주요 수혜 기업을 나열하고, "
            "각 기업이 어떤 방식으로 수혜를 받는지 설명하라. "
            "한국 기업(SK하이닉스, 삼성)은 어떤 수혜를 받을 수 있나?",
            "3장의 CHIPS Act 내용과 4장의 한국 포지션을 연결하세요. "
            "'가드레일 조항'(중국 팹 확장 제한)이 한국 기업에 미치는 영향도 고려하세요.",
            "정책 분석 + 기업 영향"
        ),
        (
            "DeepSeek R1이 '효율화 쇼크'를 주었음에도 불구하고 "
            "AI GPU 수요가 장기적으로 증가한다는 주장을 Jevons Paradox와 연결하여 설명하라.",
            "5장의 DeepSeek 섹션을 참고하세요. "
            "과거 인터넷 대역폭 효율화가 오히려 트래픽을 증가시킨 역사적 사례를 생각해보세요.",
            "경제 논리 + AI 수요 분석"
        ),
        (
            "NVIDIA의 H20 '다운그레이드 칩' 전략의 장단점을 분석하라. "
            "H20에 추가 수출 규제가 적용될 경우 NVIDIA에 미치는 재무적 영향을 추산하라.",
            "6장의 매출 분석 데이터를 활용하세요. "
            "현재 H20 매출 규모와 비중국 시장 성장률을 비교하여 순영향을 계산해보세요.",
            "재무 분석"
        ),
        (
            "지정학적 관점에서 반도체 투자 포트폴리오를 구성하려 한다. "
            "미-중 긴장 '현상 유지' 시나리오와 '긴장 고조' 시나리오에서 "
            "각각 어떤 종목을 오버웨이트/언더웨이트하겠는가?",
            "7장의 시나리오 테이블과 지정학 프리미엄 수혜 구조를 활용하세요. "
            "헤지 수단(예: 대만 관련주 비중 조절)도 고려해보세요.",
            "포트폴리오 전략"
        ),
    ]
    _quiz_section(doc, questions)

    _add_heading(doc, "정답 가이드 (핵심 포인트)", 2)
    answers = [
        ("Q1 핵심",
         "안보: 군사·외교 데이터는 외국 AI에 학습 불가. "
         "경제: 자국 AI 역량이 미래 경쟁력(의료, 금융, 제조 자동화). "
         "주권: 문화·언어 AI는 자국민을 가장 잘 이해함. "
         "영업 메시지: '귀국 데이터는 귀국 데이터센터에서, 귀국 언어로 학습된 AI로' — NVIDIA GPU를 직접 구매하는 이유."),
        ("Q2 핵심",
         "경제: 석유 수출 수익의 AI 재투자로 탈탄소 시대 신성장동력 확보. "
         "안보: 미국 클라우드 의존 탈피, 데이터 자국 보관. "
         "기술: 글로벌 AI 허브 포지션 확보. "
         "수혜: NVIDIA(GPU), Vertiv·施耐德(전력·냉각), Arista(네트워킹), SK하이닉스(HBM), TSMC(GPU 파운드리)."),
        ("Q3 핵심",
         "TSMC: 애리조나 $6.6B 보조금 (3개 팹), 2nm 생산 포함. "
         "인텔: ~$8.5B 최대 수혜, 미국 제조 재건 핵심. "
         "삼성: 텍사스 $6.4B 보조금 (테일러 팹). "
         "Micron: $6.1B (아이다호, 뉴욕). "
         "SK하이닉스: 인디애나 HBM 패키징 $450M. 가드레일: 보조금 받으면 중국 팹 확장 불가 → SK하이닉스의 무관한 우시 DRAM 팹은 제한적 영향."),
        ("Q4 핵심",
         "Jevons Paradox: 자원 효율이 높아지면 사용량이 증가. "
         "DeepSeek으로 AI 훈련 비용 1/17 → 더 많은 기업이 AI 도입 → 총 GPU 수요 증가. "
         "역사: 인터넷 압축 효율화 → 더 많은 동영상 소비 → 대역폭 수요 폭증. "
         "결론: 단기 주가 충격(실제 발생)이나 장기 수요는 오히려 확대."),
        ("Q5 핵심",
         "H20 전략 장점: 규제 기준선 내에서 중국 매출 $10B+ 유지. "
         "단점: 성능 제한으로 중국 AI 기업의 Ascend 910B 전환 가속화 우려. "
         "재무 추산: H20 추가 규제 → 연간 $10-15B 매출 손실. "
         "FY2025 총매출 $180B+ 대비 ~8% → 주가 영향 10-15% 예상 (이미 일부 반영)."),
        ("Q6 핵심",
         "현상 유지 시나리오: 오버웨이트 — NVIDIA, SK하이닉스, Broadcom (AI 수요 지속). "
         "언더웨이트 — 중국 매출 고의존 기업 (Qualcomm 중국 비중 66%). "
         "긴장 고조 시나리오: 오버웨이트 — Micron(미국산), 인텔(미국 제조), ASML 중단기. "
         "언더웨이트 — TSMC(대만 리스크), 중국 수출 비중 높은 장비사. "
         "헤지: TSMC vs 인텔 비중 조절, 대만 ETF 쇼트 등."),
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
    out = OUTPUT_DIR / f"study_sovereign_ai{level_suffix}_{today_str}.docx"
    doc.save(str(out))
    print(f"  [Sovereign AI Study] 생성 완료: {out}")
    print(f"  [Sovereign AI Study] 8장 구성, {len(REFS)}개 참고자료, 6문항 복습 문제 (Level {level})")
    return str(out)


def run(level=1):
    return {"word_path": build(level)}


if __name__ == "__main__":
    result = run()
    print(f"\n출력 파일: {result['word_path']}")
