"""
하이퍼스케일러 CapEx 전략 & AI 투자 심화 Study Agent
대상: 반도체 마케팅 종사자 (비즈니스 배경 ○, 기술 기초 보완 필요)

학습 목표:
  - 5대 하이퍼스케일러의 CapEx 규모와 AI 전략을 정량적으로 파악
  - CapEx → GPU 수요 → HBM 수요로 이어지는 계산 구조 이해
  - 투자 수익률 불확실성과 수혜 공급망 기업 식별 능력 획득

출력: outputs/reports/study_hyperscaler_capex_YYYYMMDD.docx
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
    "Microsoft_FY25_Q4": (
        "Microsoft FY2025 Q4 Earnings",
        "https://www.microsoft.com/en-us/investor/earnings/fy-2025-fourth-quarter/press-release",
        "Microsoft Azure AI 성장률, CapEx $80B 가이던스, OpenAI 파트너십 업데이트", "2025"
    ),
    "Google_10K_2024": (
        "Alphabet Q4 2024 10-K Annual Report",
        "https://abc.xyz/investor/",
        "Google CapEx $52B 확정, TPU v5 전략, Gemini 수익화 현황, DeepMind 통합", "2024"
    ),
    "Amazon_AWS_ReInvent": (
        "Amazon AWS Re:Invent 2024",
        "https://reinvent.awsevents.com/",
        "AWS CapEx 방향성, Trainium2 출시, Bedrock 성장률, Anthropic 파트너십 확대", "2024"
    ),
    "Meta_Q4_2024_Earnings": (
        "Meta Q4 2024 Earnings Call",
        "https://investor.fb.com/",
        "Meta CapEx $37B 확정, 2025 $65B 가이던스, Llama 오픈소스 전략, MTIA 칩 개발", "2024-2025"
    ),
    "Sequoia_600B": (
        "Sequoia Capital — AI's $600B Question",
        "https://www.sequoiacap.com/article/ais-600b-question/",
        "AI 인프라 투자 $600B vs 수익화 $100B 갭 분석, 'who blinks first' 딜레마", "2024"
    ),
    "Goldman_AI_Infra": (
        "Goldman Sachs — AI Infrastructure Report 2024",
        "https://www.goldmansachs.com/insights/articles/AI-poised-to-drive-160-increase-in-power-demand",
        "5대 하이퍼스케일러 CapEx 집계, 전력 수요 160% 증가 예측, 공급망 병목 분석", "2024"
    ),
    "Gartner_Cloud_2025": (
        "Gartner — Cloud Infrastructure 2025 Forecast",
        "https://www.gartner.com/en/newsroom/press-releases/2025-cloud-infrastructure-forecast",
        "퍼블릭 클라우드 지출 전망, AI 워크로드 비중 증가, 멀티클라우드 전략 분석", "2025"
    ),
    "xAI_Colossus": (
        "xAI — Colossus Supercomputer 발표",
        "https://x.ai/blog/colossus",
        "xAI Colossus: 100K H100 구축 → 200K H100 확장, Grok 3 학습 인프라", "2024-2025"
    ),
    "IEA_DC_Power": (
        "IEA — Data Centres and Data Transmission Networks",
        "https://www.iea.org/reports/data-centres-and-data-transmission-networks",
        "데이터센터 전력 수요 50GW → 100GW(2026E), AI 워크로드 전력 기여 분석", "2024"
    ),
    "CoreWeave_IPO": (
        "CoreWeave — S-1 IPO Filing",
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=CoreWeave",
        "AI 클라우드 수요·수익화 실증 데이터, NVIDIA GPU 임대 비즈니스 모델", "2025"
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
    """색상 박스 (개념 정의, 마케터 관점, 계산 예제, 주의사항)."""
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


# ──────────────────────────────────────────────────────────────
# 메인 빌드 함수
# ──────────────────────────────────────────────────────────────
def build(level=1):
    if not DOCX_AVAILABLE:
        print("  [CapEx Study] python-docx 미설치")
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
    t = doc.add_heading(f"{level_prefix}하이퍼스케일러 CapEx 전략 & AI 투자 심화", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s = doc.add_paragraph("$407B AI 군비경쟁 — 누가 이기고 누가 수혜를 받는가")
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s2 = doc.add_paragraph(
        f"대상: 반도체 마케팅 종사자  |  기준일: {config.AS_OF_DATE}  |  "
        f"난이도: 비즈니스 기초 → 중급 투자 분석"
    )
    s2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in s2.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(100, 100, 100)

    desc = doc.add_paragraph(
        "\n본 문서는 Microsoft·Google·Amazon·Meta·xAI의 AI 인프라 CapEx 전략을 "
        "반도체 마케팅 관점에서 심층 학습하기 위한 자료입니다. "
        "CapEx가 반도체 수요로 어떻게 전환되는지 정량 계산과 함께 분석합니다."
    )
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in desc.runs:
        run.font.size = Pt(9)
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 1장. CapEx 폭증의 배경
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "1장. CapEx 폭증의 배경 — AI 군비경쟁의 논리")

    doc.add_paragraph(
        "5대 하이퍼스케일러(Microsoft, Google, Amazon, Meta, xAI) 합산 CapEx가 "
        "2022년 $116B에서 2026E $407B으로 3.5배 폭증했습니다. "
        "이 투자의 배경과 '멈출 수 없는 이유'를 이해하는 것이 출발점입니다."
    )

    _add_heading(doc, "1.1 AI 군비경쟁 구조", 2)
    _concept(doc,
        "CapEx(Capital Expenditure, 자본적 지출): 기업이 장기 자산(데이터센터·서버·GPU)에 "
        "투자하는 비용. 수년에 걸쳐 감가상각됨. "
        "하이퍼스케일러 AI CapEx의 주요 구성: GPU 서버(40-50%), 데이터센터 건설(30-35%), "
        "네트워킹·스토리지(15-20%), 전력 인프라(5-10%).")

    doc.add_paragraph(
        "AI 군비경쟁이 가속화되는 3가지 구조적 이유:\n\n"
        "① 네트워크 효과: AI 서비스는 사용자·데이터가 많을수록 성능이 좋아짐 → "
        "선점 효과가 극단적으로 큼. 뒤처지면 따라잡기 불가.\n\n"
        "② 'Who Blinks First' 딜레마: 모두가 경쟁적 과잉투자 위험을 알면서도 "
        "먼저 투자를 줄이면 경쟁사에게 시장을 내줄 위험. "
        "냉전 시대 핵 군비경쟁과 동일한 게임이론 구조.\n\n"
        "③ 모델 성능 = CapEx 함수: AI 모델 성능이 컴퓨팅 예산에 비례(Scaling Law). "
        "더 많은 GPU = 더 똑똑한 AI = 더 많은 사용자 → CapEx 경쟁이 성능 경쟁."
    )

    _marketing(doc,
        "반도체 마케터 관점: 이 군비경쟁이 멈추지 않는 한 GPU·HBM 수요는 구조적으로 증가. "
        "'AI 투자 버블'이라는 비판이 있어도, "
        "Microsoft-OpenAI, Google-Gemini 경쟁이 존재하는 한 두 회사 모두 투자를 줄일 수 없음.")

    _add_heading(doc, "1.2 전체 CapEx 규모 개요", 2)
    total_rows = [
        ["2022", "$116B", "코로나 이후 클라우드 정상화, AI 본격 투자 이전"],
        ["2023", "$136B", "+17%", "ChatGPT 이후 AI GPU 주문 급증"],
        ["2024", "$219B", "+61%", "H100 대량 출하, 하이퍼스케일러 경쟁적 증설"],
        ["2025", "$340B", "+55%", "B200/GB200 출하, 데이터센터 전력 확보 경쟁"],
        ["2026E", "$407B", "+20%", "GB200 NVL72 주력, 새 데이터센터 완공 사이클"],
    ]
    # 2022는 전년 대비 없으므로 컬럼 수 맞춤
    capex_rows = [
        ["2022", "$116B", "기준", "코로나 이후 클라우드 정상화, AI 본격 투자 이전"],
        ["2023", "$136B", "+17%", "ChatGPT 이후 AI GPU 주문 급증"],
        ["2024", "$219B", "+61%", "H100 대량 출하, 하이퍼스케일러 경쟁적 증설"],
        ["2025", "$340B", "+55%", "B200/GB200 출하, 데이터센터 전력 확보 경쟁"],
        ["2026E", "$407B", "+20%", "GB200 NVL72 주력, 새 데이터센터 완공 사이클"],
    ]
    _add_table(doc, ["연도", "5사 합산 CapEx", "YoY 성장", "배경"], capex_rows)

    _add_refs(doc, ["Sequoia_600B", "Goldman_AI_Infra"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 2장. 회사별 CapEx 트렌드
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "2장. 회사별 CapEx 트렌드 & AI 전략")

    doc.add_paragraph(
        "각 하이퍼스케일러의 CapEx 규모와 AI 전략은 서로 다른 논리로 움직입니다. "
        "단순히 '많이 쓴다'가 아니라 '왜 쓰고' '무엇을 노리는지'를 파악해야 "
        "반도체 수요의 질적 차이를 이해할 수 있습니다."
    )

    company_capex_rows = [
        ["Microsoft", "$22B", "$28B", "$55B", "$80B", "$95B",
         "OpenAI 독점 파트너십, Azure AI = 핵심 성장 동력"],
        ["Google",    "$25B", "$32B", "$52B", "$75B", "$90B",
         "Gemini 수익화, TPU v5 자체칩, DeepMind 연구 주도"],
        ["Amazon",    "$38B", "$48B", "$75B", "$105B","$120B",
         "AWS Bedrock, Trainium2 자체칩, Anthropic 파트너십"],
        ["Meta",      "$31B", "$28B", "$37B", "$65B", "$72B",
         "Llama 오픈소스 전략, MTIA 자체칩, 개인화 광고 AI"],
        ["xAI",       "$0B",  "$0B",  "$6B",  "$15B", "$30B",
         "Colossus 슈퍼컴 100K→200K H100, Grok 모델 개발"],
        ["합산",      "$116B","$136B","$225B","$340B","$407B",
         "5사 합산 (중복 없음)"],
    ]
    _add_table(doc,
        ["회사", "2022", "2023", "2024", "2025", "2026E", "AI 전략 요약"],
        company_capex_rows)

    _add_heading(doc, "2.1 Microsoft — OpenAI 독점 파트너십", 2)
    doc.add_paragraph(
        "Microsoft AI 전략의 핵심:\n\n"
        "① OpenAI 투자 $13B+: Azure가 OpenAI의 유일한 클라우드 제공자. "
        "GPT-4/GPT-4o의 모든 학습과 추론이 Azure 위에서 실행.\n\n"
        "② Copilot 수익화: Office 365에 Copilot 통합($30/월 추가 과금). "
        "3억 Office 사용자 × 전환율 10% = 잠재 수익 $108B/년.\n\n"
        "③ Azure OpenAI Service: 기업 고객이 GPT-4를 API로 사용 → "
        "Azure AI 수익이 매 분기 50%+ YoY 성장 중.\n\n"
        "CapEx 특징: GPU 서버 비중이 가장 높음 (전체 CapEx의 50-55%). "
        "H100→B200 전환을 가장 빠르게 진행 중."
    )

    _add_heading(doc, "2.2 Google — Gemini + TPU 자체칩 이중 전략", 2)
    doc.add_paragraph(
        "Google AI 전략의 핵심:\n\n"
        "① Gemini Ultra/Pro/Flash: GPT-4 대항마. "
        "Google Search, Gmail, Docs에 통합 → 수십억 사용자 직접 접점.\n\n"
        "② TPU v5e/v5p 자체칩: NVIDIA 의존도 감소 시도. "
        "추론 워크로드의 50%+를 TPU로 처리하여 GPU 임대 비용 절감.\n\n"
        "③ DeepMind 통합: AlphaFold(단백질 구조), AlphaStar 등 과학 AI 분야 선도.\n\n"
        "CapEx 특징: TPU 자체 제조에 대규모 투자 → TSMC에 TPU 웨이퍼 대량 발주. "
        "NVIDIA GPU 비중을 의도적으로 줄이는 유일한 하이퍼스케일러."
    )

    _add_heading(doc, "2.3 Amazon — AWS 규모 + Anthropic 파트너십", 2)
    doc.add_paragraph(
        "Amazon AI 전략의 핵심:\n\n"
        "① AWS Bedrock: 다양한 AI 모델(Claude, Titan, Llama)을 API로 제공. "
        "'AI 모델 슈퍼마켓' 전략으로 특정 모델 lock-in 회피.\n\n"
        "② Anthropic 투자 $4B: Claude 시리즈를 AWS에서 독점 제공. "
        "AWS Bedrock의 프리미엄 모델 포지셔닝.\n\n"
        "③ Trainium2 자체칩: 추론 워크로드 비용 절감. "
        "AWS 데이터센터 내 AI 연산 비용을 3-5배 절감 목표.\n\n"
        "CapEx 특징: 5사 중 절대 규모 최대($105B, 2025). "
        "데이터센터 건설 비중이 높음 (전 세계 리전 확장)."
    )

    _add_heading(doc, "2.4 Meta — 오픈소스 + 광고 AI", 2)
    doc.add_paragraph(
        "Meta AI 전략의 핵심:\n\n"
        "① Llama 오픈소스 전략: LLM을 오픈소스로 공개 → "
        "개발자 커뮤니티가 Meta 인프라 위에 구축 → 광고 타겟팅 AI 개선 직접 수혜.\n\n"
        "② AI 광고 최적화: 유사타겟(Lookalike Audience) → AI 추천 광고. "
        "Meta 광고 매출의 70%가 AI 추천에 의존 → AI = 핵심 현금흐름.\n\n"
        "③ MTIA (Meta Training and Inference Accelerator): "
        "추천 알고리즘 전용 자체 AI칩. NVIDIA 의존도 감소 목표.\n\n"
        "CapEx 특징: 2023년 AI 투자 일시 축소($28B) 후 2025년 $65B으로 급증. "
        "Zuckerberg의 'AI Year' 선언 이후 적극 투자 전환."
    )

    _add_heading(doc, "2.5 xAI — 후발주자의 파괴적 투자", 2)
    doc.add_paragraph(
        "xAI AI 전략의 핵심:\n\n"
        "① Colossus 슈퍼컴: 2024년 100K H100 구축 → 2025년 200K H100 확장. "
        "단일 클러스터 기준 세계 최대 AI 훈련 인프라 (당시).\n\n"
        "② Grok 3 학습: 200K H100 클러스터에서 훈련. "
        "NVIDIA GPU 집중 구매로 NVIDIA 최대 고객 중 하나로 급부상.\n\n"
        "③ X(구 Twitter) 데이터 활용: 실시간 소셜 데이터로 LLM 학습 → "
        "타사 대비 실시간 정보 강점.\n\n"
        "CapEx 특징: 2024년 $6B → 2026E $30B으로 5배 급증. "
        "엘론 머스크 개인 자금 + 외부 투자 혼합."
    )

    _add_refs(doc, ["Microsoft_FY25_Q4", "Google_10K_2024", "Amazon_AWS_ReInvent",
                    "Meta_Q4_2024_Earnings", "xAI_Colossus"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 3장. CapEx ROI 분석
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "3장. CapEx ROI 분석 — 투자 대비 수익화")

    doc.add_paragraph(
        "CapEx가 폭증하는 것보다 더 중요한 질문은 '이 투자가 수익을 내고 있는가'입니다. "
        "회사별 AI 매출 성장률과 수익화 경로를 분석합니다."
    )

    _add_heading(doc, "3.1 Azure AI — 가장 빠른 수익화", 2)
    _concept(doc,
        "Azure AI 성장률: Microsoft Azure 전체 성장률 중 'AI 기여분'으로 별도 공시. "
        "2024년 매 분기 AI 기여 성장률이 50%+ YoY를 기록. "
        "2025 Q2: Azure 전체 성장 36%, 이 중 AI 기여 16%p.")
    _quant(doc,
        "Microsoft Azure AI 수익화 계산:\n"
        "  Azure 연간 매출: ~$110B (FY2025)\n"
        "  AI 기여 비중: ~30% (추정)\n"
        "  Azure AI 연간 매출: ~$33B\n"
        "  YoY 성장률: 50%+ → 2026E Azure AI: ~$50B+\n"
        "  Copilot 잠재 매출: 3억 사용자 × 10% 전환 × $30/월 × 12 = $108B (장기)")

    _add_heading(doc, "3.2 AWS Bedrock & AI 수익화", 2)
    doc.add_paragraph(
        "Amazon AI 수익화 경로:\n\n"
        "① AWS Bedrock: Claude, Titan, Llama API 과금 → 토큰당 $0.003-0.06/1K 토큰.\n"
        "② AI 검색 (Amazon Shopping AI): 상품 추천 정확도 AI 개선 → GMV 증가.\n"
        "③ Alexa AI 업그레이드: Alexa+로 LLM 기반 음성 AI 재출시.\n\n"
        "AWS 전체 성장률: 2024 Q4 +19% YoY (AI 수요가 핵심 성장 동인으로 명시)."
    )

    roi_rows = [
        ["Microsoft", "Azure AI 성장 50%+ YoY", "$33B (2025E)", "Copilot B2B 전환 가속 시 $100B+ 잠재"],
        ["Google", "Search AI Overview 광고 효율", "$25B (2025E)", "Gemini API 기업 계약 확대"],
        ["Amazon", "AWS Bedrock + AI 검색", "$20B (2025E)", "Trainium2 비용 절감 효과 극대화"],
        ["Meta", "광고 AI 최적화 직접 기여", "$20B+ (2025E)", "AI 광고 수익 전체 매출의 70%"],
        ["xAI", "Grok 구독 + X Premium", "$1-2B (2025E)", "수익화 초기 단계, 투자 대비 GAP 큼"],
    ]
    _add_table(doc, ["회사", "주요 AI 수익화 경로", "AI 관련 매출 추정", "성장 시나리오"], roi_rows)

    _marketing(doc,
        "반도체 마케터 관점: CapEx ROI가 검증될수록 투자가 지속됨. "
        "Microsoft Azure AI 성장률 50%+는 '투자가 수익을 낸다'는 증거. "
        "이것이 5사 모두 투자를 줄이지 못하는 구조적 이유 중 하나.")

    _add_refs(doc, ["Microsoft_FY25_Q4", "Google_10K_2024", "Goldman_AI_Infra"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 4장. 반도체 수요 계산
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "4장. 반도체 수요 계산 — CapEx를 GPU·HBM 수요로 전환")

    doc.add_paragraph(
        "하이퍼스케일러 CapEx가 반도체 수요로 어떻게 전환되는지를 계산하는 공식을 "
        "마스터하면, 임의의 CapEx 발표를 즉시 GPU·HBM 수요로 환산할 수 있습니다."
    )

    _add_heading(doc, "4.1 CapEx → GPU 수 변환 공식", 2)
    _quant(doc,
        "기본 공식:\n"
        "  GPU 구매비 = CapEx × GPU 비중(40-50%)\n"
        "  GPU 구매 대수 = GPU 구매비 ÷ GPU 단가\n\n"
        "Microsoft 2025 CapEx $80B 적용 예시:\n"
        "  GPU 구매비 = $80B × 45% = $36B\n"
        "  H100 기준: $36B ÷ $30,000 = 120만 개\n"
        "  B200 기준: $36B ÷ $70,000 = 51만 개\n"
        "  GB200 NVL72 랙 기준: $36B ÷ $3,000,000 = 12,000랙 (= 86만 GPU 환산)\n\n"
        "실제는 H100·H200·B200 혼합 → 평균 단가 $45,000 가정:\n"
        "  $36B ÷ $45,000 = 80만 GPU (Microsoft 2025 추정)")

    _add_heading(doc, "4.2 GPU 수 → HBM 수요 변환 공식", 2)
    _quant(doc,
        "HBM 수요 공식:\n"
        "  HBM 용량 수요(GB) = GPU 수 × GPU당 HBM 용량(GB)\n"
        "  HBM 스택 수 = HBM GB ÷ HBM 스택당 용량(24GB for HBM3e 8-Hi)\n\n"
        "Microsoft 80만 GPU 중 B200 비중 50% 가정:\n"
        "  H100 40만 개: 40만 × 80GB = 32,000,000 GB = 32 PB (HBM3)\n"
        "  B200 40만 개: 40만 × 192GB = 76,800,000 GB = 76.8 PB (HBM3e)\n"
        "  총 HBM 수요: 108.8 PB (약 109백만 GB)\n"
        "  HBM3e 스택(24GB/스택) 환산: 76.8PB ÷ 24GB = 320만 스택")

    _add_heading(doc, "4.3 5사 합산 반도체 수요 (2025 추정)", 2)
    semi_demand_rows = [
        ["Microsoft", "$80B", "$36B", "~80만 개", "~109 PB", "~320만 스택(HBM3e)"],
        ["Google", "$75B", "$30B (TPU 포함)", "GPU+TPU 혼합", "~80 PB", "~250만 스택"],
        ["Amazon", "$105B", "$35B", "~90만 개", "~100 PB", "~300만 스택"],
        ["Meta", "$65B", "$28B", "~70만 개", "~80 PB", "~230만 스택"],
        ["xAI", "$15B", "$12B (GPU 집중)", "~25만 개", "~30 PB", "~90만 스택"],
        ["합산", "$340B", "~$141B", "~365만 개", "~399 PB", "~1,190만 스택"],
    ]
    _add_table(doc,
        ["회사", "CapEx", "GPU 구매비(추정)", "GPU 대수(추정)", "HBM 수요(추정)", "HBM 스택 수"],
        semi_demand_rows)

    _marketing(doc,
        "반도체 마케터 핵심 인사이트: 5사 합산 GPU 수요 ~365만 개. "
        "2025년 NVIDIA B200 출하량 ~150만 개 감안 시 H100·H200 포함 혼합 구성. "
        "HBM 스택 1,190만 개는 2025년 전 세계 HBM 공급의 약 60-70%에 해당 → "
        "5대 하이퍼스케일러만으로도 HBM 시장을 지배.")

    _add_refs(doc, ["Microsoft_FY25_Q4", "Goldman_AI_Infra", "Gartner_Cloud_2025"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 5장. 데이터센터 건설 사이클
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "5장. 데이터센터 건설 사이클 — 30~36개월 미스매치")

    doc.add_paragraph(
        "AI 수요는 분기 단위로 폭발하지만, 데이터센터 건설은 30~36개월이 걸립니다. "
        "이 시간 미스매치가 반도체 공급·수요 불균형의 근본 원인 중 하나입니다."
    )

    _add_heading(doc, "5.1 데이터센터 건설 타임라인", 2)
    build_rows = [
        ["0-3개월", "부지 선정·취득", "토지 매입, 전력망 접속 협의, 인허가 신청", "전력 접속 대기가 가장 긴 경우 1-2년"],
        ["3-6개월", "착공 준비", "설계 확정, 냉각 시스템 발주, 전력 장비 주문", "변압기 납기 30개월+ (미국 기준)"],
        ["6-18개월", "건설 공사", "건물 구조물, 기계·전기 설비, 네트워크 인프라 설치", "건설 인력 부족 리스크"],
        ["18-24개월", "GPU 서버 설치", "GPU 수령 → 랙 조립 → 네트워크 구성 → 테스트", "GPU 납기 지연 시 대기"],
        ["24-30개월", "소프트웨어 구성", "AI 플랫폼 설치, 보안 인증, 고객 온보딩", "보안 인증 소요 시간"],
        ["30-36개월", "완전 가동", "첫 고객 워크로드 처리 시작", "총 리드타임 2.5-3년"],
    ]
    _add_table(doc,
        ["단계", "작업", "상세 내용", "주요 리스크"],
        build_rows)

    _add_heading(doc, "5.2 AI 수요 가속 vs. 건설 사이클 미스매치", 2)
    _risk(doc,
        "미스매치의 결과:\n"
        "① 단기(1-2년): GPU를 사도 설치할 데이터센터가 없어 창고 대기 ('GPU 조기 구매 현상').\n"
        "② 중기(2-3년): 2025-2026년 발주한 데이터센터가 2027-2028년 완공 → "
        "AI 수요가 그 시점에도 있어야 투자 회수 가능.\n"
        "③ 전력 병목: 미국 변압기 납기 30개월+, 전력망 접속 대기 최대 10년 → "
        "데이터센터 부지보다 전력이 진짜 병목으로 부상.")

    _quant(doc,
        "전력 수요 계산:\n"
        "  GB200 NVL72 랙 1개: 전력 120kW\n"
        "  Microsoft가 2026E 발주하는 40,000랙: 4,800 MW = 4.8 GW\n"
        "  현재 미국 전체 데이터센터 전력: ~40 GW\n"
        "  → Microsoft 단독으로 미국 DC 전력의 12% 추가 필요\n"
        "  전 세계 5사 합산: 2026E 기준 추가 15-20 GW 수요 발생 (원전 15-20기 분량)")

    _marketing(doc,
        "반도체 마케터 시사점: 전력 인프라가 새로운 'AI 공급망 병목'. "
        "Vertiv(전력관리), Schneider Electric(냉각), GE Vernova(발전)가 "
        "GPU보다 더 긴 리드타임 제약을 가짐. "
        "이 섹터가 다음 반도체 이후의 수혜 섹터.")

    _add_refs(doc, ["IEA_DC_Power", "Goldman_AI_Infra"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 6장. 투자 수익률 불확실성
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "6장. 투자 수익률 불확실성 — '$600B 질문'")

    doc.add_paragraph(
        "Sequoia Capital이 2024년 제기한 '$600B Question'은 "
        "AI 인프라 투자와 수익화의 거대한 갭을 조명합니다. "
        "이 갭이 과연 채워질 수 있는지, 그리고 채워지지 않는다면 반도체 수요에 어떤 영향이 있는지 분석합니다."
    )

    _add_heading(doc, "6.1 Sequoia '$600B Question' 요약", 2)
    _concept(doc,
        "Sequoia의 핵심 논지 (2024년 기준):\n"
        "AI 인프라 투자 합계: ~$600B (하이퍼스케일러 + AI 스타트업 합산)\n"
        "AI 서비스 수익화: ~$100B (OpenAI, Anthropic, AI API 등 합산)\n"
        "갭: $500B → '이 갭을 누가 메우는가?' 질문.")
    _quant(doc,
        "수익화 갭 계산 (2024-2025 기준):\n"
        "  AI 인프라 투자: $340B (2025 하이퍼스케일러 CapEx)\n"
        "  AI 스타트업 투자: $100B+ (벤처캐피탈 AI 투자)\n"
        "  총 공급 측 투자: ~$440B\n\n"
        "  AI 서비스 수익화:\n"
        "    OpenAI ARR: ~$3.4B (2024) → ~$12B (2025E)\n"
        "    Anthropic ARR: ~$0.5B (2024) → ~$3B (2025E)\n"
        "    하이퍼스케일러 AI 매출: ~$100B (2025E)\n"
        "    총 수익화: ~$120B\n"
        "  잔존 갭: ~$320B (공급이 수요를 3배 초과)")

    _add_heading(doc, "6.2 갭이 메워지는 시나리오", 2)
    scenario_rows = [
        ["강세 (Bull)", "가능성 40%", "Agentic AI 폭발, AI 소프트웨어 B2B 대규모 채택",
         "2026-2028년 $500B+ AI 서비스 매출 → 갭 해소"],
        ["기본 (Base)", "가능성 45%", "현재 성장률 지속, 기업 AI 점진적 도입",
         "2027-2028년 갭 축소 (~$200B 수준)"],
        ["약세 (Bear)", "가능성 15%", "AI 버블 붕괴, ROI 실망, 투자 급감",
         "2025-2026년 CapEx 축소 → GPU 수요 절벽"],
    ]
    _add_table(doc, ["시나리오", "확률", "전제 조건", "반도체 수요 영향"], scenario_rows)

    _add_heading(doc, "6.3 주요 규제 리스크", 2)
    _risk(doc,
        "EU AI Act (2024년 발효): 고위험 AI 시스템 규제 강화. "
        "하이퍼스케일러의 EU 데이터센터 투자를 일부 지연시킬 수 있음.")
    _risk(doc,
        "미국 반독점 조사: Microsoft-OpenAI 독점 관계, Google AI 검색 독점에 대한 "
        "규제 당국 조사 강화. 최악의 경우 AI 파트너십 제한 명령 가능.")
    _risk(doc,
        "에너지/환경 규제: 데이터센터 전력 소비에 대한 탄소 규제 강화. "
        "특히 EU에서 AI 서버 팜에 대한 그린 에너지 의무 비율 상향 논의.")

    _add_refs(doc, ["Sequoia_600B", "Goldman_AI_Infra", "Gartner_Cloud_2025"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 7장. 수혜 공급망 기업
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "7장. 수혜 공급망 기업 — CapEx 투자의 최종 수혜자")

    doc.add_paragraph(
        "하이퍼스케일러 CapEx $407B의 흐름은 단순히 NVIDIA만 이익을 주는 것이 아닙니다. "
        "공급망 각 레이어별로 구조적 수혜를 받는 기업들을 파악합니다."
    )

    beneficiary_rows = [
        # (섹터, 대표 기업, 수혜 이유, 2026E 성장 전망, 반도체와의 관련성)
        ["GPU·AI 가속기", "NVIDIA, AMD", "직접 수혜 최대. NVIDIA 데이터센터 매출 $49B/분기",
         "강함", "핵심 수혜"],
        ["HBM 메모리", "SK Hynix, Micron, Samsung", "GPU당 HBM 탑재량 증가, ASP 프리미엄 유지",
         "강함", "핵심 수혜"],
        ["파운드리·패키징", "TSMC, ASE, Amkor", "CoWoS 독점, N4/N3 AI 칩 수요 지속",
         "강함", "핵심 수혜"],
        ["전력 인프라", "Vertiv, Schneider Electric, Eaton", "액침냉각·PDU 수요 폭발, 리드타임 병목",
         "매우 강함", "간접 수혜"],
        ["네트워킹", "Broadcom, Marvell, Arista", "InfiniBand 대안 이더넷 AI 채택, 800G 전환",
         "강함", "간접 수혜"],
        ["건설·부동산 REIT", "Equinix, Digital Realty, Iron Mountain", "DC 부지 희소성, 임대료 상승",
         "중간", "간접 수혜"],
        ["전력 발전", "GE Vernova, Vistra, NextEra", "원전·가스 발전 수요 급증 (AI 전력 공급)",
         "강함", "간접 수혜"],
        ["반도체 장비", "ASML, AMAT, Lam Research", "TSMC CoWoS 캐파 확대 → 장비 발주",
         "중간~강함", "간접 수혜"],
        ["광학 인터커넥트", "II-VI (Coherent), Lumentum", "800G/1.6T 데이터센터 광통신 수요",
         "강함", "간접 수혜"],
    ]
    _add_table(doc,
        ["섹터", "대표 기업", "수혜 이유", "성장 전망", "반도체 연관"],
        beneficiary_rows)

    _add_heading(doc, "7.1 전력 인프라 — 새로운 핵심 병목", 2)
    doc.add_paragraph(
        "왜 전력이 반도체만큼 중요한가:\n\n"
        "① GB200 NVL72 랙 전력: 120kW/랙. 기존 서버 랙(10-15kW) 대비 8-10배.\n"
        "② 전력 밀도 대응: 기존 공냉식 냉각으로는 불가 → 액침냉각, 직접 수냉 필수.\n"
        "③ 수혜 기업: Vertiv(PDU, 냉각 시스템), Schneider Electric(전력관리), "
        "Eaton(UPS·배전반), GE Vernova(가스터빈, 전력망).\n\n"
        "Vertiv 사례: 2023 매출 $6.4B → 2025E $10B+. "
        "수주 잔고(backlog)가 매출의 3배 → 가시성 높은 성장."
    )

    _add_heading(doc, "7.2 반도체 장비 — TSMC 증설의 수혜", 2)
    doc.add_paragraph(
        "TSMC CoWoS 캐파 120,000 wpm(2026E) 달성을 위한 장비 투자:\n\n"
        "① ASML EUV 노광기: N4/N3 공정 필수. 대당 $350M. "
        "TSMC 2026E 구매 수십 대.\n"
        "② AMAT(Applied Materials): CVD·CMP 장비 CoWoS 특화 버전.\n"
        "③ Lam Research: 식각(Etch) 장비, TSV 공정용.\n"
        "④ KLA: 검사·계측 장비, CoWoS 불량률 관리 필수."
    )

    _marketing(doc,
        "반도체 마케터 인사이트: '픽앤쇼벨(Pick & Shovel)' 전략. "
        "골드러시 시대에 금을 캐는 사람이 아닌 곡괭이·삽 파는 사람이 더 안정적 수익을 냄. "
        "AI 시대에 NVIDIA 한 기업에 집중하는 대신 "
        "전력(Vertiv)·장비(ASML)·네트워킹(Broadcom)으로 분산하면 리스크 관리 가능.")

    _add_refs(doc, ["Goldman_AI_Infra", "IEA_DC_Power", "CoreWeave_IPO"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 레벨별 심화 섹션 (8장 복습 문제 직전)
    # ══════════════════════════════════════════════════════════
    if level >= 2:
        _add_heading(doc, "심화 분석")
        doc.add_paragraph(
            "이 섹션은 Level 2 심화 과정으로, CapEx → GPU 전환 공식과 실제 계산 예제 3개, "
            "AI 수익화 갭 분석을 다룹니다."
        )

        _add_heading(doc, "CapEx → GPU 전환 공식 + 실제 계산 예제 3개", 2)
        doc.add_paragraph(
            "하이퍼스케일러의 CapEx 공시 데이터를 GPU 수요로 변환하는 정량 공식을 제시합니다. "
            "이 공식은 반도체 공급망 수요 예측의 핵심 도구입니다."
        )
        doc.add_paragraph("공식:")
        formula_p = doc.add_paragraph()
        formula_p.add_run(
            "GPU 구매 CapEx = 총 CapEx × GPU 비중(%) \n"
            "GPU 대수 = GPU 구매 CapEx ÷ GPU 단가 \n"
            "HBM 수요(GB) = GPU 대수 × GPU당 HBM 용량(GB) \n"
            "HBM 스택 수 = HBM 수요(GB) ÷ 스택당 용량(GB)"
        ).bold = True
        doc.add_paragraph(
            "파라미터 가이드: GPU 비중 = 40-50% (AI 집중 투자 시), "
            "H100 단가 $35,000 / B200 단가 $70,000, "
            "H100 HBM3e 80GB / B200 HBM3e 192GB, HBM3e 스택당 24GB."
        )

        _add_heading(doc, "예제 1: Microsoft FY2025E CapEx $80B", 3)
        ms_rows = [
            ["총 CapEx", "$80B", "FY2025 가이던스"],
            ["GPU 비중", "45%", "AI DC 우선 투자"],
            ["GPU 구매 CapEx", "$36B", "$80B × 45%"],
            ["B200 대수", "~514,000대", "$36B ÷ $70,000"],
            ["HBM3e 수요", "~98.7 PB", "514K대 × 192GB"],
            ["HBM3e 스택 수", "~4.1M 스택", "98.7PB ÷ 24GB"],
            ["비고", "전체 HBM 연간 공급의 ~14%", "2025E 총 공급 ~700PB 가정"],
        ]
        _add_table(doc, ["항목", "값", "계산/비고"], ms_rows)

        _add_heading(doc, "예제 2: Google FY2025E CapEx $75B", 3)
        goog_rows = [
            ["총 CapEx", "$75B", "2025 가이던스"],
            ["GPU 비중", "35%", "TPU 자체칩으로 일부 대체"],
            ["GPU 구매 CapEx", "$26.25B", "$75B × 35%"],
            ["B200 + H100 혼합", "~450,000대 (혼합 평균 $58K)", "$26.25B ÷ $58,000"],
            ["HBM3e 수요", "~72.0 PB", "450K대 × 160GB (혼합 평균)"],
            ["비고", "TPU v5e 자체칩 비중 30% 감안",
             "NVIDIA GPU 비중 Google이 가장 낮음"],
        ]
        _add_table(doc, ["항목", "값", "계산/비고"], goog_rows)

        _add_heading(doc, "예제 3: Meta FY2025E CapEx $65B", 3)
        meta_rows = [
            ["총 CapEx", "$65B", "2025 가이던스 $60-65B 중간값"],
            ["GPU 비중", "50%", "AI 생성 콘텐츠·광고 집중 투자"],
            ["GPU 구매 CapEx", "$32.5B", "$65B × 50%"],
            ["B200 대수", "~464,000대", "$32.5B ÷ $70,000"],
            ["HBM3e 수요", "~89.1 PB", "464K대 × 192GB"],
            ["3사 합산 HBM 수요", "~260 PB (MS+Google+Meta)",
             "전체 공급의 ~37% → 공급 과잉 없음"],
        ]
        _add_table(doc, ["항목", "값", "계산/비고"], meta_rows)
        doc.add_paragraph(
            "3사 합산 시사점: Microsoft + Google + Meta만으로도 "
            "2025년 HBM 총 공급의 35-40% 흡수 예상. "
            "여기에 AWS, xAI, Oracle, CoreWeave 등 추가 시 수요 > 공급 구조 확인. "
            "HBM 공급 부족은 구조적 현상 → SK하이닉스 ASP 방어 근거."
        )

        _add_heading(doc, "AI 수익화 갭 분석", 2)
        doc.add_paragraph(
            "하이퍼스케일러 AI 투자 대비 AI 매출 실현 갭을 분석합니다. "
            "이것이 AI 버블 우려의 핵심 지표입니다."
        )
        revenue_gap_rows = [
            ["Microsoft", "$80B", "$40B (Azure AI 포함)", "0.5x",
             "Azure OpenAI, Copilot 빠른 수익화. "
             "2025년 Azure AI 매출 $30B+ 예상"],
            ["Google", "$75B", "$25B (GCP AI 포함)", "0.33x",
             "Gemini API, GCP Vertex AI. "
             "TPU를 통한 비용 절감으로 실질 ROI 개선"],
            ["Amazon", "$105B", "$15B (Bedrock+SageMaker)", "0.14x",
             "수익화 가장 느림. "
             "2026년 AWS AI 전용 매출 가시화 예상"],
            ["Meta", "$65B", "$10B (광고 AI 간접)", "0.15x",
             "직접 AI 매출 없음. "
             "광고 타겟팅 개선으로 간접 효과만 측정 가능"],
            ["5사 합산", "$407B+", "~$100B", "~0.25x",
             "Sequoia '$600B Question' 갭: "
             "수익화 $100B vs 투자 $407B+ → 4배 갭"],
        ]
        _add_table(doc, ["기업", "2025E CapEx", "2025E AI 관련 매출",
                          "수익화 비율", "비고"],
                   revenue_gap_rows)
        doc.add_paragraph(
            "갭 해소 시나리오: 2027년까지 AI 매출 CAGR 50%+ 성장 필요. "
            "Microsoft와 Google이 가장 빠른 수익화 — AWS와 Meta는 2026-2027년 본격화. "
            "투자자 관점: 수익화 비율이 0.5x 이상인 기업(Microsoft)이 "
            "AI 투자 지속 명분 강함 → CapEx 증가세 유지 가능. "
            "갭이 벌어지는 기업은 2026년 CapEx 삭감 압력."
        )

    if level >= 3:
        _add_heading(doc, "전문가 심층 분석")
        doc.add_paragraph(
            "이 섹션은 Level 3 전문가 과정으로, AI 투자 버블 지표(닷컴 버블 비교)와 "
            "수익화 임계점 모델을 다룹니다."
        )

        _add_heading(doc, "AI 투자 버블 지표: 닷컴 버블과의 비교", 2)
        doc.add_paragraph(
            "1999-2001 닷컴 버블과 현재 AI 투자 사이클을 5개 지표로 비교합니다."
        )
        bubble_rows = [
            ["인프라 투자 규모",
             "1998-2001: 광통신 인프라 $1T+ 투자",
             "2023-2027E: AI DC CapEx $1.5T+ (5사 합산)",
             "규모 유사, AI가 더 빠른 속도",
             "📊 유사"],
            ["수익화 속도",
             "닷컴: 인터넷 매출 $30B (2000) vs 인프라 $1T",
             "AI: 클라우드 AI 서비스 $100B (2025E) vs CapEx $407B",
             "AI의 수익화가 닷컴보다 3-5배 빠름",
             "✅ AI 우위"],
            ["기업 재무 건전성",
             "닷컴: 수익 없는 스타트업 IPO, P/S 100x+",
             "AI: NVIDIA P/E 20-30x, 실제 이익 $60B+",
             "닷컴은 허상, AI는 실제 이익 존재",
             "✅ AI 우위"],
            ["기술 성숙도",
             "닷컴: 56K 모뎀으로 전자상거래 도전",
             "AI: LLM이 이미 $100B+ 가치 창출 입증",
             "AI 기술의 실용성 이미 검증됨",
             "✅ AI 우위"],
            ["버블 신호",
             "닷컴: NASDAQ P/E 200x, IPO 첫날 300% 상승",
             "AI: CoreWeave IPO P/S 10x+, AI 스타트업 밸류 과대",
             "AI 스타트업 일부 닷컴 수준 거품",
             "⚠️ 주의 필요"],
            ["수요 지속성",
             "닷컴: 실제 인터넷 수요 → 2005년 회복",
             "AI: 수요 계속 확대 중 (Jevons Paradox 작동)",
             "AI 수요는 self-reinforcing 사이클",
             "✅ AI 우위"],
        ]
        _add_table(doc, ["지표", "닷컴 버블 (1999-2001)",
                          "AI 투자 사이클 (2023-2027)", "차이", "판단"],
                   bubble_rows)
        doc.add_paragraph(
            "결론: AI 투자 사이클은 닷컴 버블보다 근본적으로 건전함. "
            "그러나 AI 스타트업(비상장)과 인프라 기업 일부의 밸류에이션은 버블 징후. "
            "NVIDIA/SK하이닉스/TSMC 같은 실물 수혜 기업은 버블 리스크 낮음."
        )

        _add_heading(doc, "AI CapEx 수익화 임계점 모델", 2)
        doc.add_paragraph(
            "각 하이퍼스케일러의 AI CapEx 투자가 손익분기를 넘는 시점을 추정합니다."
        )
        breakeven_rows = [
            ["Microsoft",
             "Copilot M365 구독 $30/월, Azure OpenAI API",
             "2025년 하반기 (달성 근접)",
             "Copilot MAU 300M+ 달성 시점",
             "2025E AI 매출 $40B vs CapEx 누적 회수 2026년 예상"],
            ["Google",
             "Gemini API 사용량 과금, GCP AI 서비스",
             "2026년 상반기",
             "GCP AI 워크로드 비중 30%+ 달성",
             "검색 AI 통합으로 광고 단가 하락 리스크 상쇄 필요"],
            ["Amazon",
             "AWS Bedrock 토큰 과금, SageMaker",
             "2026년 하반기",
             "AWS AI 매출 $30B+ 달성",
             "현재 AWS AI 매출 가시성 낮음 → 2026년 공시 예상"],
            ["Meta",
             "광고 CTR 개선(AI 타겟팅), AI 직접 서비스 미약",
             "2027년 (불확실)",
             "Llama AI 생태계 수익화 모델 미확립",
             "오픈소스 전략으로 직접 수익화 어려움"],
        ]
        _add_table(doc, ["기업", "주요 수익화 경로", "임계점 도달 시기",
                          "임계점 조건", "리스크"],
                   breakeven_rows)
        doc.add_paragraph(
            "투자 전략: 수익화 임계점 도달 기업의 CapEx는 지속적으로 증가 → "
            "반도체 공급망 수요 견고. "
            "임계점 미달 기업의 CapEx 삭감 시 → 해당 기업 공급망 노출 비중 축소. "
            "2026년 Amazon AWS AI 수익화 가시화가 다음 반도체 수요 확인 시점."
        )

    # ══════════════════════════════════════════════════════════
    # 8장. 복습 문제
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "8장. 복습 문제 — 능동적 학습 (Feynman 기법)")

    doc.add_paragraph(
        "페인만 기법: 아래 질문에 '상대방에게 설명하듯' 답할 수 있으면 이해한 것입니다. "
        "막히는 부분이 있으면 해당 장으로 돌아가서 다시 읽으세요."
    )

    questions = [
        (
            "5대 하이퍼스케일러가 AI 투자가 과잉임을 알면서도 "
            "투자를 줄이지 못하는 이유를 게임이론 관점에서 설명하세요. "
            "이것이 반도체 수요에 어떤 영향을 미치는지도 포함하세요.",
            "1장 참고. 'Who Blinks First' 딜레마와 냉전 군비경쟁 구조를 활용하세요.",
            "전략 분석 (게임이론 + 반도체 수요)"
        ),
        (
            "Google이 5사 중 유일하게 NVIDIA GPU 비중을 줄이려는 전략(TPU v5)을 "
            "추진하는 이유와 그 한계를 설명하고, "
            "이것이 NVIDIA에게 단기·장기적으로 어떤 영향인지 분석하세요.",
            "2장 참고. TPU의 추론 vs. 학습 용도 제한, Google 내부 워크로드 비중을 고려하세요.",
            "경쟁 분석 (전략 + 기술)"
        ),
        (
            "Amazon CapEx $105B에서 GPU 구매비를 추정하고, "
            "이를 B200 GPU 대수와 HBM3e 스택 수로 변환하세요. "
            "(GPU 비중 45%, B200 단가 $70,000, B200당 HBM3e 192GB, 스택당 24GB 가정)",
            "4장 계산 공식 참고. $105B × 45% ÷ $70,000 = GPU 수 → × 192GB ÷ 24GB = 스택 수",
            "정량 계산 (공급망 수요 계산)"
        ),
        (
            "Sequoia '$600B Question'의 핵심 논지를 요약하고, "
            "이 갭이 메워지지 않을 경우(Bear Case) "
            "반도체 공급망 기업들(NVIDIA, SK Hynix, TSMC)에 미칠 영향을 예측하세요.",
            "6장 참고. 투자 $440B vs 수익화 $120B 갭. 재고 사이클, 닷컴 버블 사례를 활용하세요.",
            "시나리오 분석 (투자 + 반도체 수요)"
        ),
        (
            "GB200 NVL72 랙 40,000개(Microsoft 2026E 추정) 설치 시 "
            "필요한 전력(MW)을 계산하고, 이것이 왜 전력 인프라 기업(Vertiv 등)의 "
            "구조적 성장 기회가 되는지 설명하세요.",
            "5장 계산 참고. 120kW/랙 × 40,000랙 = ? MW. 미국 전체 DC 전력 40GW와 비교하세요.",
            "정량 계산 + 비즈니스 분석"
        ),
        (
            "하이퍼스케일러 CapEx 투자에서 '픽앤쇼벨 전략'으로 투자할 경우 "
            "NVIDIA에만 집중하는 것보다 리스크·수익 측면에서 어떤 장단점이 있는지 "
            "최소 3개 섹터를 들어 설명하세요.",
            "7장 참고. 전력(Vertiv), 장비(ASML), 네트워킹(Broadcom)의 "
            "수혜 이유와 NVIDIA와의 상관관계를 비교하세요.",
            "투자 분석 (포트폴리오 전략)"
        ),
    ]

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

    _add_heading(doc, "정답 핵심 요약", 2)
    doc.add_paragraph("각 문제의 핵심 답안 키워드입니다:")
    answers = [
        ("Q1 핵심",
         "'Who Blinks First' 딜레마: 모두가 게임이론적으로 투자를 줄일 수 없음. "
         "Microsoft가 줄이면 Google이 Azure AI 시장 점유 → Microsoft 생존 위협. "
         "반도체 수요: 이 딜레마가 지속되는 한 GPU/HBM 수요는 구조적 증가."),
        ("Q2 핵심",
         "Google TPU 이유: ① AWS 추론 비용 절감 ② NVIDIA 협상력 확보 ③ 특화 최적화. "
         "한계: 최첨단 LLM 학습은 여전히 NVIDIA 필요 (GPT-5급 모델 훈련은 TPU로 불가). "
         "NVIDIA 단기: 소폭 부정적 (Google GPU 주문 일부 감소). "
         "NVIDIA 장기: 영향 제한적 (학습 수요는 유지)."),
        ("Q3 핵심",
         "$105B × 45% = $47.25B. "
         "$47.25B ÷ $70,000 = 675,000 B200 GPU. "
         "675,000 × 192GB = 129.6 PB. "
         "129.6 PB ÷ 24GB = 5,400,000 HBM3e 스택 = 540만 스택."),
        ("Q4 핵심",
         "Sequoia 핵심: 투자 $440B vs 수익화 $120B = $320B 갭. "
         "Bear case: CSP들이 CapEx 30-50% 삭감 → NVIDIA GPU 수요 절벽 → "
         "HBM ASP 하락 → SK Hynix 이익률 급감 → TSMC CoWoS 수요 급감. "
         "닷컴 버블 참고: 2000-2001년 시스코 -86% 하락."),
        ("Q5 핵심",
         "120kW × 40,000 = 4,800,000 kW = 4,800 MW = 4.8 GW. "
         "미국 DC 전력 40GW의 12%. "
         "전력 기업 수혜: GB200은 기존 서버 대비 8-10배 전력 밀도 → "
         "액침냉각, PDU, UPS 모두 교체 필요 → Vertiv 수주 잔고 3년치 이미 확보."),
        ("Q6 핵심",
         "픽앤쇼벨 장점: NVIDIA 단일 리스크 분산, 수출규제·경쟁사 리스크 없음. "
         "Vertiv: AI CapEx 수혜 직접, 경쟁 없음 (액침냉각 특허). "
         "ASML: TSMC 증설 → 자동 수혜, 독점(EUV). "
         "Broadcom: 이더넷 AI 네트워크 표준화 수혜. "
         "단점: 성장률이 NVIDIA(40-50%) 대비 낮음(20-30%). 절대 수익은 낮을 수 있음."),
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
    out = OUTPUT_DIR / f"study_hyperscaler_capex{level_suffix}_{today_str}.docx"
    doc.save(str(out))
    print(f"  [CapEx Study] 생성 완료: {out}")
    print(f"  [CapEx Study] 8장 구성, {len(REFS)}개 참고자료, 6문항 복습 문제 (Level {level})")
    return str(out)


def run(level=1):
    return {"word_path": build(level)}


if __name__ == "__main__":
    result = run()
    print(f"\n출력 파일: {result['word_path']}")
