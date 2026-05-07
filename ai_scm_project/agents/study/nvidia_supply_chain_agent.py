"""
NVIDIA GPU 공급망 & 비즈니스 모델 심화 Study Agent
대상: 반도체 마케팅 종사자 (비즈니스 배경 ○, 기술 기초 보완 필요)

학습 목표:
  - NVIDIA의 시장 독점 구조와 CUDA 생태계 lock-in을 정량적으로 이해
  - GPU 아키텍처 세대별 진화와 공급망 구조를 마케팅 언어로 파악
  - 경쟁 위협·수출 규제·투자 관점을 직접 도출할 수 있게 됨

출력: outputs/reports/study_nvidia_supply_chain_YYYYMMDD.docx
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
    "NVIDIA_10K_2024": (
        "NVIDIA — Annual Report (10-K) FY2024",
        "https://investor.nvidia.com/financial-information/annual-reports/default.aspx",
        "NVIDIA 사업 구조, 데이터센터 매출, 수출 규제 리스크, CUDA 비즈니스 모델 공시", "2024"
    ),
    "NVIDIA_Earnings_Q4FY25": (
        "NVIDIA Quarterly Earnings — Q4 FY2025",
        "https://investor.nvidia.com/financial-information/quarterly-results/default.aspx",
        "데이터센터 매출 $49.2B(분기), 영업이익률 60%+, Blackwell 출하 시작 확인", "2025"
    ),
    "TSMC_Tech_Symposium_2024": (
        "TSMC Technology Symposium 2024",
        "https://pr.tsmc.com/english/news/3141",
        "N4P/N3 공정, CoWoS 어드밴스드 패키징 로드맵, GB200 패키징 구조 공개", "2024"
    ),
    "SemiAnalysis_NVIDIA": (
        "SemiAnalysis — NVIDIA Deep Dive",
        "https://www.semianalysis.com/p/nvidia-deep-dive",
        "NVIDIA 공급망 전체 분석: TSMC 제조 → CoWoS → HBM 통합 → ODM → CSP 경로", "2024"
    ),
    "Bernstein_NVIDIA": (
        "Bernstein Research — NVIDIA Initiation Report",
        "https://www.bernsteinresearch.com/",
        "CUDA 생태계 lock-in 정량 분석, 개발자 3,000만 명 설치 베이스, 경쟁사 대비 해자", "2024"
    ),
    "MorganStanley_AICompute": (
        "Morgan Stanley — AI Compute Infrastructure Report",
        "https://www.morganstanley.com/ideas/artificial-intelligence-technology-infrastructure",
        "H100 → B200 성능·가격·ASP 효과 분석, AI GPU 수요 5개년 모델", "2024"
    ),
    "BIS_Export_Regulation": (
        "US BIS — Export Administration Regulations (AI Chips)",
        "https://www.bis.gov/regulations/export-administration-regulations",
        "A100/H100 중국 수출 금지, H20 규제 추가, 지역별 성능 상한선 규정", "2023-2024"
    ),
    "NVIDIA_GTC_Blackwell": (
        "NVIDIA GTC 2024 — Blackwell Architecture 발표",
        "https://www.nvidia.com/en-us/events/gtc/",
        "B200 스펙 공개: TF BF16 2,250, HBM3e 192GB, TDP 1,000W, GB200 NVL72 랙 $3M", "2024"
    ),
    "Goldman_AI_Infra": (
        "Goldman Sachs — AI Infrastructure 2024",
        "https://www.goldmansachs.com/insights/articles/AI-poised-to-drive-160-increase-in-power-demand",
        "AI 공급망 투자 분석, NVIDIA 독점 구조 지속 가능성 평가", "2024"
    ),
    "AMD_MI300X_Launch": (
        "AMD — MI300X Product Launch & Investor Day",
        "https://ir.amd.com/",
        "MI300X 192GB HBM3 스펙, NVIDIA H100 대비 메모리 용량 2.4배, 가격 경쟁력 분석", "2023-2024"
    ),
    "Google_TPU_v5": (
        "Google — TPU v5e/v5p Architecture",
        "https://cloud.google.com/tpu/docs/system-architecture-tpu-vm",
        "Google 자체 AI칩 전략, NVIDIA 의존도 감소 시도, 내부 추론 워크로드 이전", "2024"
    ),
    "Sequoia_AI_Infra": (
        "Sequoia Capital — AI's $600B Question",
        "https://www.sequoiacap.com/article/ais-600b-question/",
        "AI 인프라 투자 vs 수익화 격차 분석, NVIDIA 수혜 구조 지속성 논거", "2024"
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
        print("  [NVIDIA Study] python-docx 미설치")
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
    t = doc.add_heading(f"{level_prefix}NVIDIA GPU 공급망 & 비즈니스 모델 심화", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s = doc.add_paragraph("CUDA 생태계부터 투자 관점까지 — 반도체 마케터를 위한 완전 가이드")
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
        "\n본 문서는 NVIDIA의 GPU 공급망과 비즈니스 모델을 반도체 마케팅 관점에서 "
        "심층 학습하기 위한 자료입니다. CUDA 독점 구조·공급망 병목·경쟁 위협·투자 관점을 "
        "정량 데이터와 함께 마케팅 언어로 풀어 설명합니다."
    )
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in desc.runs:
        run.font.size = Pt(9)
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 1장. NVIDIA의 독점적 위치
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "1장. NVIDIA의 독점적 위치 — AI의 OPEC")

    doc.add_paragraph(
        "NVIDIA는 2024년 기준 AI 가속기 시장의 80%+ 점유율을 보유한 사실상 독점 기업입니다. "
        "이 독점이 단순한 하드웨어 우위가 아닌 '소프트웨어 생태계 lock-in'에 기반한다는 점이 "
        "다른 반도체 기업과 근본적으로 다릅니다."
    )

    _add_heading(doc, "1.1 CUDA — 20년 투자의 결실", 2)
    _concept(doc,
        "CUDA(Compute Unified Device Architecture): NVIDIA가 2006년 출시한 GPU 병렬 컴퓨팅 플랫폼. "
        "개발자가 GPU를 일반 프로그래밍 언어(C/C++/Python)로 활용할 수 있게 해주는 소프트웨어 레이어. "
        "AI 연구자들이 '딥러닝 = CUDA'로 인식할 만큼 생태계가 고착화됨.")
    _marketing(doc,
        "마케팅 비유: CUDA = 'Windows'이고 GPU = 'PC'. "
        "AMD GPU가 성능이 좋아도 개발자들이 CUDA 코드를 재작성해야 하는 비용이 엄청나 전환이 안 됨. "
        "NVIDIA는 하드웨어를 팔지만 실제 해자(Moat)는 소프트웨어에 있음.")

    cuda_rows = [
        ["CUDA 설치 베이스", "3,000만+ 개발자 (2024년 기준)", "AMD ROCm 대비 10배+"],
        ["지원 프레임워크", "PyTorch, TensorFlow, JAX 모두 CUDA 우선 최적화", "경쟁사 지원은 후순위"],
        ["cuDNN (딥러닝 라이브러리)", "CNN/Transformer 연산 최적화, 성능 2-5배 향상", "AMD MIOpen 격차 있음"],
        ["TensorRT (추론 최적화)", "모델 배포 시 2-8배 추론 속도 향상", "NVIDIA 전용"],
        ["NIM (AI 마이크로서비스)", "기업 AI 배포 표준화 솔루션, 2024년 출시", "신규 수익원"],
        ["NCCL (GPU 통신 라이브러리)", "멀티-GPU 학습 통신 최적화, 클러스터 필수", "NVIDIA 전용 최적화"],
    ]
    _add_table(doc, ["구성 요소", "역할 / 가치", "경쟁사 상황"], cuda_rows)

    _add_heading(doc, "1.2 시장점유율 구조", 2)
    doc.add_paragraph(
        "AI 가속기 시장 점유율 (2024년 데이터센터 GPU 매출 기준):"
    )
    share_rows = [
        ["NVIDIA", "~80-85%", "$115B (데이터센터 연간)", "GPU + CUDA 생태계 lock-in"],
        ["AMD", "~8-12%", "$5-7B (MI300X 기반)", "메모리 용량 우위, 가격 경쟁"],
        ["Google TPU", "~3-5%", "내부 사용 (외판 없음)", "Google 내부 워크로드 전용"],
        ["AWS Trainium", "~1-2%", "내부 사용 + Bedrock", "AWS 자체 추론 비용 절감"],
        ["Intel Gaudi", "~1%", "$1B 미만", "Azure 소규모 채택"],
        ["기타 ASIC", "~2-3%", "각사 내부 사용", "Meta MTIA, Microsoft Maia 등"],
    ]
    _add_table(doc, ["업체", "점유율", "매출 규모", "특이사항"], share_rows)

    _marketing(doc,
        "'AI의 OPEC' 비유: OPEC이 석유 공급을 통제해 가격 결정력을 갖듯, "
        "NVIDIA는 AI 학습에 필수인 GPU 공급을 통제합니다. "
        "단, OPEC과 달리 NVIDIA의 독점은 기술 진입장벽(CUDA)이 있어 더 지속 가능합니다. "
        "2023년 H100 가격이 $30,000에도 수요가 공급을 초과한 게 그 증거입니다.")

    _add_refs(doc, ["NVIDIA_10K_2024", "Bernstein_NVIDIA", "NVIDIA_Earnings_Q4FY25"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 2장. GPU 아키텍처 진화
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "2장. GPU 아키텍처 진화 — Volta에서 Blackwell까지")

    doc.add_paragraph(
        "NVIDIA는 약 2년 주기로 새로운 GPU 아키텍처를 출시하며 성능을 극적으로 향상시킵니다. "
        "각 세대는 이전 세대 대비 성능이 2-5배 향상되는데, 이것이 고객이 계속 업그레이드하게 "
        "만드는 '성능 treadmill' 전략입니다."
    )

    _concept(doc,
        "TF BF16(TeraFLOPS BFloat16): GPU가 초당 처리할 수 있는 AI 연산 횟수. "
        "1 TFLOP = 초당 1조 번의 부동소수점 연산. BF16은 AI 학습에 최적화된 수치 형식. "
        "숫자가 클수록 AI 모델 학습이 빨라짐.")
    _concept(doc,
        "HBM(High Bandwidth Memory): GPU 전용 고대역폭 메모리. "
        "용량(GB)이 클수록 더 큰 AI 모델을 올릴 수 있고, "
        "대역폭(TB/s)이 높을수록 데이터를 빠르게 처리함.")

    arch_rows = [
        ["Volta", "V100", "2017", "120 TF", "16~32 GB HBM2", "0.9 TB/s", "300W", "$10,000", "첫 Tensor Core, AI 학습 혁명"],
        ["Ampere", "A100", "2020", "312 TF", "40~80 GB HBM2e", "2.0 TB/s", "400W", "$15,000", "3세대 Tensor Core, MIG 기능"],
        ["Hopper", "H100", "2022", "989 TF", "80 GB HBM3", "3.35 TB/s", "700W", "$30,000", "Transformer Engine, NVLink 4.0"],
        ["Hopper+", "H200", "2024", "989 TF", "141 GB HBM3e", "4.8 TB/s", "700W", "$40,000", "메모리 용량·대역폭 대폭 증가"],
        ["Blackwell", "B200", "2024-25", "2,250 TF", "192 GB HBM3e", "8.0 TB/s", "1,000W", "$70,000", "5세대 Tensor Core, FP4 지원"],
        ["Blackwell Ultra", "B300", "2025-26", "~4,500 TF(추정)", "288 GB HBM4(추정)", "~16 TB/s", "1,200W(추정)", "미정", "HBM4 최초 탑재 예정"],
    ]
    _add_table(doc,
        ["아키텍처", "대표 칩", "출시연도", "TF BF16", "HBM 용량", "HBM 대역폭", "전력(TDP)", "가격(SXM)", "핵심 특징"],
        arch_rows)

    _add_heading(doc, "2.1 성능 향상의 비즈니스 의미", 2)
    _quant(doc,
        "H100 → B200 성능/가격 비교:\n"
        "  성능: 989 TF → 2,250 TF = 2.3배 향상\n"
        "  가격: $30,000 → $70,000 = 2.3배 상승\n"
        "  단위 성능 비용: 동일 ($30/TF 유지)\n\n"
        "H100 → B200 GB200 NVL72(랙 시스템) 기준:\n"
        "  단일 H100 대비 랙 전체 성능: 5.6배 향상\n"
        "  가격 상승: 1.4배 (72개 GPU, $3M/랙 vs H100 8-GPU DGX $300K×1.4)\n"
        "  → ASP(평균판매단가) 효과: 같은 연산에 NVIDIA가 받는 돈이 4배 늘어남")

    _marketing(doc,
        "마케팅 시사점: '성능 향상 > 가격 인상' 구조가 고객이 계속 업그레이드하게 만듦. "
        "B200은 H100 대비 추론 비용($/토큰)이 낮아서 CSP들이 도입할 수밖에 없음. "
        "NVIDIA는 이 사이클로 매 세대마다 ASP를 높이면서도 수요를 만들어냄.")

    _add_refs(doc, ["NVIDIA_GTC_Blackwell", "MorganStanley_AICompute", "TSMC_Tech_Symposium_2024"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 3장. 공급망 구조
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "3장. 공급망 구조 — TSMC에서 CSP까지")

    doc.add_paragraph(
        "H100/B200 GPU 하나가 고객에게 전달되기까지 최소 6단계의 공급망을 거칩니다. "
        "각 단계가 병목이 될 수 있으며, NVIDIA는 이 중 '설계'만 담당하는 팹리스 회사입니다."
    )

    _concept(doc,
        "팹리스(Fabless): 공장(Fab) 없이 설계만 하는 반도체 회사. "
        "NVIDIA가 설계한 칩을 TSMC가 위탁 제조. "
        "자산 경량화로 높은 자본 효율성을 실현하나, 제조 병목에 취약한 구조.")

    supply_chain_rows = [
        ["1단계", "NVIDIA (설계)", "GPU 아키텍처 설계, CUDA 소프트웨어", "NVIDIA 독점 설계", "없음 (설계만)"],
        ["2단계", "TSMC (제조)", "4nm N4P/N4X 공정으로 GPU 다이 제조", "TSMC 독점 (삼성 대안 없음)", "웨이퍼 공급 부족 시"],
        ["3단계", "CoWoS 패키징", "GPU + HBM 기판 통합 어드밴스드 패키징", "TSMC CoWoS 독점", "2023-2025 최대 병목"],
        ["4단계", "HBM 탑재", "SK Hynix(50%+)/Samsung/Micron HBM 공급", "3사 과점", "HBM 수급 2024-2025 타이트"],
        ["5단계", "ODM 조립", "Foxconn/Quanta/Wistron DGX 서버 조립", "다수 ODM 가능", "낮음"],
        ["6단계", "CSP 최종 고객", "Microsoft Azure / AWS / Google Cloud 데이터센터 설치", "다수 CSP", "낮음 (구매 경쟁)"],
    ]
    _add_table(doc,
        ["단계", "주체", "역할", "경쟁 구조", "병목 리스크"],
        supply_chain_rows)

    _add_heading(doc, "3.1 CoWoS — 가장 중요한 병목", 2)
    _concept(doc,
        "CoWoS(Chip on Wafer on Substrate): TSMC의 어드밴스드 패키징 기술. "
        "GPU 다이와 HBM 메모리를 하나의 인터포저(중간 기판) 위에 나란히 배치하여 "
        "극도로 짧은 거리(수백 μm)로 연결. 이 패키징 없이는 HBM의 대역폭 장점이 실현 불가.")
    _marketing(doc,
        "CoWoS 비유: GPU와 HBM을 하나의 '합체 로봇'으로 만드는 공정. "
        "TSMC만 양산 가능하며, 2023-2024년 이 공정 캐파 부족이 "
        "H100 출하 지연의 주요 원인이었음. "
        "2024년 TSMC가 CoWoS ASP를 20%+ 인상 → NVIDIA는 GPU 가격 인상 전가.")
    _quant(doc,
        "CoWoS 캐파 추이:\n"
        "  2023: 35,000 wafer/월\n"
        "  2024: 50,000 wafer/월\n"
        "  2025: 85,000 wafer/월 (목표 초과 달성)\n"
        "  2026E: 120,000 wafer/월\n"
        "  → 2023 대비 2026E: 3.4배 확대. 그러나 B200 수요도 동반 급증.")

    _add_refs(doc, ["TSMC_Tech_Symposium_2024", "SemiAnalysis_NVIDIA"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 4장. 수익 구조 분석
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "4장. 수익 구조 분석 — 이익률 60%의 비밀")

    doc.add_paragraph(
        "NVIDIA 데이터센터 사업부 매출은 2020년 $0.34B(분기)에서 2025년 $49.2B(분기)으로 "
        "144배 성장했습니다. 영업이익률은 60%+로, 이는 팹리스 구조와 소프트웨어 해자의 결합입니다."
    )

    revenue_rows = [
        ["2020 Q1", "$0.34B", "-", "A100 출시 전, V100 기반"],
        ["2021 Q1", "$0.82B", "+141%", "A100 대량 출하 시작"],
        ["2022 Q1", "$3.75B", "+357%", "AI 학습 수요 폭발"],
        ["2023 Q1", "$4.28B", "+14%", "H100 출하 초기"],
        ["2023 Q3", "$18.4B", "+206%", "H100 본격 출하, ChatGPT 효과"],
        ["2024 Q1", "$22.6B", "+23%", "H100/H200 풀 출하"],
        ["2024 Q3", "$30.8B", "+36%", "H200 ramping, B200 예약"],
        ["2025 Q1", "$39.3B", "+28%", "B200 출하 시작"],
        ["2025 Q4", "$49.2B", "+25%", "GB200 NVL72 대량 출하"],
    ]
    _add_table(doc,
        ["분기", "데이터센터 매출", "전분기 대비", "비고"],
        revenue_rows)

    _add_heading(doc, "4.1 팹리스 구조의 이익률 메커니즘", 2)
    _quant(doc,
        "H100 GPU 원가 분석 (추정):\n"
        "  판매가: $30,000\n"
        "  TSMC 제조비: ~$3,000 (웨이퍼 비용)\n"
        "  CoWoS 패키징: ~$1,500\n"
        "  HBM3 메모리: ~$8,000 (80GB × $14/GB × 수율 조정)\n"
        "  기타 부품: ~$2,000\n"
        "  총 원가: ~$14,500\n"
        "  NVIDIA 매출총이익: ~$15,500 → 매출총이익률 ~52%\n"
        "  (소프트웨어/CUDA 기여분 포함 시 영업이익률 60%+ 달성)")

    _add_heading(doc, "4.2 CUDA 소프트웨어 스택의 해자", 2)
    doc.add_paragraph(
        "NVIDIA의 소프트웨어 스택은 GPU 매출을 '구독형 수익' 형태로 고착시키는 역할을 합니다:"
    )
    sw_rows = [
        ["cuDNN", "딥러닝 신경망 연산 라이브러리", "무료 (GPU 구매 촉진용)", "PyTorch·TF 필수 의존"],
        ["TensorRT", "추론 최적화 엔진 (모델 배포)", "무료 (엔터프라이즈 지원 유료)", "NVIDIA GPU 전용"],
        ["NIM (AI 마이크로서비스)", "기업 AI 배포 표준화, API 형태", "유료 구독", "2024년 신규 수익원"],
        ["DGX Cloud", "NVIDIA GPU 클라우드 서비스", "GPU 시간당 과금", "H100/B200 직접 임대"],
        ["NEMO / Triton", "LLM 학습·추론 프레임워크", "오픈소스 + 엔터프라이즈 지원", "NVIDIA 에코시스템 강화"],
    ]
    _add_table(doc, ["소프트웨어", "역할", "수익 모델", "특이사항"], sw_rows)

    _marketing(doc,
        "마케팅 포인트: CUDA 생태계는 '면도기-면도날' 모델의 반대. "
        "면도기(CUDA)를 무료로 주고 면도날(GPU)을 팖. "
        "3,000만 개발자가 CUDA로 코드를 작성하면 그들이 속한 기업은 "
        "NVIDIA GPU를 살 수밖에 없는 구조가 형성됨.")

    _add_refs(doc, ["NVIDIA_Earnings_Q4FY25", "NVIDIA_10K_2024", "Bernstein_NVIDIA"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 5장. 경쟁 위협 분석
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "5장. 경쟁 위협 분석 — NVIDIA를 위협하는 것들")

    doc.add_paragraph(
        "NVIDIA의 독점에 대한 위협은 크게 세 방향에서 옵니다: "
        "① GPU 경쟁사 (AMD, Intel), ② CSP 자체 AI칩 (Google TPU, AWS Trainium), "
        "③ 신흥 AI 반도체 스타트업. "
        "각각의 실제 위협 수준을 데이터 기반으로 평가합니다."
    )

    competitor_rows = [
        ["AMD MI300X", "AMD", "1,307 TF BF16", "192 GB HBM3", "5.3 TB/s", "750W", "$20,000", "메모리 용량 강점, CUDA 호환성 ROCm 개선 중"],
        ["AMD MI350X", "AMD", "~2,600 TF(추정)", "288 GB HBM3e", "~8 TB/s", "1,000W", "미정", "2025년 출시 목표, B200 대항마"],
        ["Google TPU v5p", "Google", "~460 TF", "외부 비공개", "~4.8 TB/s(추정)", "~500W", "외판 없음", "Google 내부 전용, 외판 계획 없음"],
        ["AWS Trainium2", "Amazon", "~300 TF(추정)", "외부 비공개", "비공개", "비공개", "외판 없음", "AWS Bedrock 추론 비용 절감 목적"],
        ["Intel Gaudi 3", "Intel", "~1,835 TF BF16", "96 GB HBM2e", "3.7 TB/s", "900W", "~$10,000", "Azure 소규모 채택, 에코시스템 약함"],
        ["NVIDIA H100 (기준)", "NVIDIA", "989 TF BF16", "80 GB HBM3", "3.35 TB/s", "700W", "$30,000", "2022-2024 주력 제품 (비교 기준)"],
        ["NVIDIA B200 (현재)", "NVIDIA", "2,250 TF BF16", "192 GB HBM3e", "8.0 TB/s", "1,000W", "$70,000", "2024-2026 현재 주력 제품"],
    ]
    _add_table(doc,
        ["제품", "제조사", "TF BF16", "HBM 용량", "HBM 대역폭", "전력", "가격", "특이사항"],
        competitor_rows)

    _add_heading(doc, "5.1 AMD MI300X — 가장 현실적인 위협", 2)
    doc.add_paragraph(
        "AMD MI300X가 NVIDIA H100 대비 유리한 점:\n\n"
        "① 메모리 용량 우위: 192GB vs H100의 80GB. LLM 추론 시 더 큰 모델을 단일 GPU에 탑재 가능.\n"
        "② 가격 경쟁력: $20,000 vs H100 $30,000 (~33% 저렴).\n"
        "③ CSP 다변화 수요: Microsoft Azure, Meta가 '공급 다변화' 차원에서 MI300X 채택.\n\n"
        "AMD MI300X의 한계:\n\n"
        "① 소프트웨어 에코시스템: ROCm이 CUDA 대비 성숙도 부족. 특히 커스텀 커널 최적화.\n"
        "② 학습 성능: H100 대비 AI 학습(Training) 성능은 20-30% 낮음.\n"
        "③ 공급망: CoWoS 패키징 물량 확보 경쟁에서 NVIDIA 우선 순위."
    )
    _marketing(doc,
        "투자 시사점: AMD MI300X는 'NVIDIA 대체'가 아닌 '가격 협상 카드'. "
        "CSP들이 AMD를 구매하는 이유는 성능 때문이 아니라 "
        "NVIDIA에 대한 협상력 확보와 공급 리스크 분산입니다. "
        "NVIDIA에게는 위협이지만 AMD에게는 기회.")

    _add_heading(doc, "5.2 CSP 자체 AI칩 — 장기적 위협", 2)
    doc.add_paragraph(
        "Google, Amazon, Meta가 자체 AI칩을 개발하는 이유:\n\n"
        "① 비용: NVIDIA GPU 의존 시 데이터센터 운영비의 30-40%가 GPU 비용.\n"
        "② 특화 최적화: 범용 GPU보다 특정 워크로드(추론)에 3-10배 효율적.\n"
        "③ 전략적 독립성: NVIDIA에 대한 협상력 및 공급 리스크 감소.\n\n"
        "현실적 한계:\n"
        "① 학습(Training)에는 여전히 NVIDIA GPU 필요 (최첨단 모델 개발).\n"
        "② 추론(Inference) 전용 사용 사례로 NVIDIA 대체 가능한 범위가 제한적.\n"
        "③ 개발 비용: TPU v5 개발에 수십억 달러 투자 → 소규모 CSP는 불가능."
    )
    _risk(doc,
        "NVIDIA 장기 리스크: 추론 워크로드가 전체 AI 컴퓨팅의 80%를 차지하게 되면, "
        "CSP 자체칩이 NVIDIA 수요를 잠식할 수 있음. "
        "그러나 최신 모델 학습에는 여전히 NVIDIA GPU가 필수여서 "
        "이 리스크는 3-5년 장기 시나리오.")

    _add_refs(doc, ["AMD_MI300X_Launch", "Google_TPU_v5", "MorganStanley_AICompute"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 6장. 공급 제약 & 주요 리스크
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "6장. 공급 제약 & 주요 리스크")

    doc.add_paragraph(
        "NVIDIA의 독점적 수익성을 위협하는 공급·규제 리스크를 정량적으로 분석합니다. "
        "이 리스크들은 단기적으로 출하량을 제한하고, 장기적으로는 경쟁사에게 기회를 줄 수 있습니다."
    )

    _add_heading(doc, "6.1 CoWoS 패키징 병목", 2)
    doc.add_paragraph(
        "CoWoS가 2023-2025년 최대 공급 병목이었던 이유:\n\n"
        "① TSMC 독점: CoWoS 대규모 양산 가능한 곳이 TSMC뿐.\n"
        "② 공정 복잡성: 단일 웨이퍼에 GPU + HBM 여러 개를 수μm 정밀도로 배치.\n"
        "③ 설비 투자 리드타임: CoWoS 라인 구축에 18-24개월 소요.\n\n"
        "2026년 현황: TSMC가 CoWoS 캐파를 35,000 → 120,000 wpm으로 3.4배 확대. "
        "병목이 일부 완화되나 B200/GB200 수요 폭증으로 여전히 타이트."
    )

    _add_heading(doc, "6.2 수출 규제 — 중국 매출 붕괴", 2)
    export_rows = [
        ["2022", "A100/H100 수출 금지", "중국 수출 전면 차단", "$17B(연간 추정)", "시작"],
        ["2023 Q4", "H800/A800도 금지", "우회 제품도 차단", "$17B → 급감", "확대"],
        ["2024", "H20 일부 허용", "성능 제한 버전만 허용", "$5B(추정)", "제한적 허용"],
        ["2025-2026", "H20 추가 규제 논의", "BIS 심사 지속", "$2-3B(추정)", "추가 제한 가능"],
    ]
    _add_table(doc, ["시기", "규제 내용", "영향", "중국 매출 추정", "동향"], export_rows)

    _quant(doc,
        "수출 규제 영향 정량화:\n"
        "  2023년 중국 매출: $17B (전체 매출의 ~20%)\n"
        "  2024년 중국 매출: $5B (전체 매출의 ~4%)\n"
        "  손실 규모: $12B/년 → 그러나 미국·유럽·중동 수요로 완전 상쇄\n"
        "  역설: 수출 규제 = NVIDIA 주가 단기 악재였으나\n"
        "       중국 이외 지역 수요 폭증으로 실적은 오히려 개선됨")

    _add_heading(doc, "6.3 TSMC 집중 리스크", 2)
    _risk(doc,
        "TSMC 집중 리스크: NVIDIA 매출의 100%가 TSMC 제조에 의존. "
        "대만 지정학적 리스크(중국 위협), 자연재해, TSMC 파업 시 "
        "NVIDIA 출하 전면 중단 가능. "
        "삼성 파운드리가 기술적으로 대안이 되려면 2-3년 추가 필요.")
    _risk(doc,
        "AI 버블 리스크: CSP들이 GPU를 과잉 주문(Double booking)했다가 "
        "갑자기 취소할 경우 재고 사이클 악화. 2000년 닷컴 버블 시 "
        "시스코·시스코 유사 업체들이 경험한 수요 절벽 재현 가능성.")

    _add_refs(doc, ["BIS_Export_Regulation", "NVIDIA_10K_2024", "Sequoia_AI_Infra"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 7장. 투자 관점
    # ══════════════════════════════════════════════════════════
    _add_heading(doc, "7장. 투자 관점 — 밸류에이션과 성장 시나리오")

    doc.add_paragraph(
        "NVIDIA 주식은 2023-2025년 세계에서 가장 많이 오른 대형주 중 하나입니다. "
        "현재 밸류에이션이 정당한지, 어떤 시나리오가 투자 논거를 바꾸는지 분석합니다."
    )

    _add_heading(doc, "7.1 재무 성과 요약", 2)
    financial_rows = [
        ["FY2020 (1월 결산)", "$10.9B", "$4.3B", "39%", "$1.78", "AI 이전 시대"],
        ["FY2022", "$26.9B", "$10.0B", "37%", "$4.17", "Ampere 사이클"],
        ["FY2023", "$26.9B", "$4.2B", "16%", "$1.74", "조정 기간"],
        ["FY2024", "$60.9B", "$32.6B", "54%", "$12.96", "H100 사이클 폭발"],
        ["FY2025", "$130.5B", "$73.0B", "56%", "$29.44", "B200 본격 출하"],
        ["FY2026E (컨센서스)", "$195B(E)", "$115B(E)", "59%(E)", "$43.00(E)", "GB200 NVL72 주력"],
        ["FY2027E (컨센서스)", "$245B(E)", "$148B(E)", "60%(E)", "$55.00(E)", "Blackwell Ultra 출시"],
    ]
    _add_table(doc,
        ["회계연도", "매출", "영업이익", "영업이익률", "EPS", "비고"],
        financial_rows)

    _add_heading(doc, "7.2 밸류에이션 분석", 2)
    _quant(doc,
        "NVIDIA 밸류에이션 (2026년 3월 기준, 주가 ~$850 가정):\n"
        "  FY2026E EPS: $43.00\n"
        "  Forward P/E: ~20x (2026E 기준)\n"
        "  PEG 비율: P/E 20x ÷ EPS 성장률 46% = 0.43x → 성장 대비 매력적\n"
        "  역사적 NVIDIA P/E: 2020-2022년 30-60x → 현재 상대적 저평가\n\n"
        "Strong Buy 논거:\n"
        "  ① EPS 성장률 40-50% vs P/E 20x → PEG < 0.5x\n"
        "  ② GB200 NVL72 수요: $3M/랙 × 수십만 랙 = 수조 달러 TAM\n"
        "  ③ 소프트웨어(NIM) 매출 본격화 → 마진 추가 개선 예상")

    _marketing(doc,
        "투자 포인트: NVIDIA는 '반도체 기업'이 아닌 '플랫폼 기업'으로 재평가받고 있음. "
        "Microsoft가 Windows로 PC 시대를 지배했듯, "
        "NVIDIA는 CUDA로 AI 시대를 지배할 가능성. "
        "P/E 20x는 Microsoft(30x), Google(25x) 대비 오히려 저렴한 수준.")
    _risk(doc,
        "Bear case 시나리오: ① AMD ROCm 성숙 → CSP 전환 가속 ② CSP 자체칩 추론 대체 "
        "③ AI 투자 버블 붕괴 → GPU 수요 절벽 ④ 추가 수출 규제. "
        "이 경우 EPS 컨센서스 대비 30-50% 하향 조정 가능.")

    _add_refs(doc, ["NVIDIA_Earnings_Q4FY25", "Bernstein_NVIDIA", "MorganStanley_AICompute"])
    doc.add_page_break()

    # ══════════════════════════════════════════════════════════
    # 레벨별 심화 섹션 (8장 복습 문제 직전)
    # ══════════════════════════════════════════════════════════
    if level >= 2:
        _add_heading(doc, "심화 분석")
        doc.add_paragraph(
            "이 섹션은 Level 2 심화 과정으로, CUDA 전환 비용 정량화와 "
            "AMD 시장점유율 시나리오 모델을 다룹니다."
        )

        _add_heading(doc, "CUDA 전환 비용 정량화", 2)
        doc.add_paragraph(
            "CUDA에서 AMD ROCm 또는 다른 플랫폼으로 전환할 때 발생하는 "
            "실제 비용을 정량화합니다. 이것이 NVIDIA의 가장 강력한 해자(moat)입니다."
        )
        cuda_cost_rows = [
            ["코드 마이그레이션",
             "CUDA 코드 → HIP(ROCm) 변환",
             "프레임워크 내부 커널 코드 수십만 줄 변환 필요. "
             "PyTorch CUDA 커스텀 커널은 수동 변환 불가피",
             "시니어 엔지니어 $200K/년 × 20명 × 1-2년 = $4-8M",
             "중형 AI 연구소 기준"],
            ["성능 최적화 재작업",
             "cuBLAS → rocBLAS 성능 갭 메우기",
             "초기 전환 시 성능 20-40% 하락. "
             "cuDNN 대비 MIOpen 성능 격차 존재",
             "$5-15M (최적화 엔지니어링 비용)",
             "학습 워크로드 기준"],
            ["운영 재교육",
             "MLOps 파이프라인 전환 + 인력 교육",
             "K8s CUDA operator → ROCm 전환. "
             "인프라팀 재교육 6-12개월 필요",
             "$1-3M (교육 + 생산성 손실)",
             "100명 규모 AI팀 기준"],
            ["검증 및 테스트",
             "모델 정확도 동등성 검증",
             "FP16/BF16 연산 결과 차이 검증. "
             "모델 출력 품질 A/B 테스트 필요",
             "$2-5M (QA 및 테스트 비용)",
             "대형 언어모델 기준"],
            ["기회비용",
             "전환 기간 중 연구 생산성 손실",
             "NVIDIA 최신 기능(Flash Attention 3 등) 즉시 활용 불가",
             "$10-30M+ (연구 지연으로 인한 기회비용)",
             "빅테크 AI 연구팀 기준"],
        ]
        _add_table(doc, ["비용 항목", "내용", "세부 사항", "추정 비용", "비고"],
                   cuda_cost_rows)
        doc.add_paragraph(
            "총 CUDA 전환 비용 추정: 중형 AI 기업 $25-60M, 빅테크 $100M+. "
            "NVIDIA는 이 전환 비용이 AMD 가격 차이를 훨씬 초과함을 알고 있어 "
            "GPU 가격 프리미엄(H100 vs MI300X 30-50% 고가)을 유지 가능. "
            "Meta, Google은 자체칩 투자($5B+)로 이 전환 비용을 '내재화'하는 전략을 선택."
        )

        _add_heading(doc, "AMD 시장점유율 시나리오 모델", 2)
        doc.add_paragraph(
            "AMD MI300X 출시 이후 NVIDIA의 데이터센터 GPU 시장점유율 변화를 "
            "3가지 시나리오로 분석합니다."
        )
        amd_scenario_rows = [
            ["Bear (AMD 성공)",
             "AMD MI350X 성능 H200 수준 달성. "
             "ROCm 소프트웨어 안정화 완료. "
             "주요 클라우드(AWS, Azure) AMD 채택 확대",
             "NVIDIA 70% → 65% (2026E) → 58% (2028E)",
             "$15-20B AMD DC 매출 달성",
             "NVIDIA 주가 -20-30% 압박. "
             "단, 총 시장 확대로 절대 매출 영향 제한적"],
            ["Base (현상 유지)",
             "AMD 추론 워크로드 일부 침투. "
             "NVIDIA 학습 워크로드 독점 유지. "
             "CSP가 가격 협상 카드로 AMD 활용",
             "NVIDIA 75% → 73% (2026E) → 70% (2028E)",
             "$8-12B AMD DC 매출",
             "NVIDIA ASP 소폭 압박. "
             "점유율 하락이 아닌 성장률 둔화"],
            ["Bull (NVIDIA 독주)",
             "AMD ROCm 소프트웨어 불안정 지속. "
             "Blackwell 아키텍처 성능 격차 유지. "
             "NVLink 생태계 강화로 전환 비용 상승",
             "NVIDIA 80%+ 유지 (2028E)",
             "AMD DC GPU $3-5B 정체",
             "NVIDIA 밸류에이션 프리미엄 정당화. "
             "AMD 주가 AI 테마 소외 가능성"],
        ]
        _add_table(doc, ["시나리오", "조건", "NVIDIA 점유율 전망",
                          "AMD 매출 전망", "투자 시사점"],
                   amd_scenario_rows)
        doc.add_paragraph(
            "현재 Base 시나리오가 가장 현실적. AMD의 가장 큰 진전은 추론(Inference) 시장 — "
            "학습 대비 소프트웨어 의존도 낮고 메모리 용량이 경쟁력. "
            "모니터링: AMD 분기 데이터센터 GPU 매출 (목표: $10B+ → 시나리오 전환 신호)."
        )

    if level >= 3:
        _add_heading(doc, "전문가 심층 분석")
        doc.add_paragraph(
            "이 섹션은 Level 3 전문가 과정으로, NVIDIA의 수직통합 전략 분석 "
            "(NVLink → NVSwitch → DGX Cloud)과 반독점 규제 리스크를 다룹니다."
        )

        _add_heading(doc, "NVIDIA 수직통합 전략: NVLink → NVSwitch → DGX Cloud", 2)
        doc.add_paragraph(
            "NVIDIA는 단순 GPU 판매를 넘어 하드웨어-소프트웨어-클라우드 수직통합 구조로 "
            "진화하고 있습니다. 이는 Apple의 실리콘-iOS-앱스토어 전략과 유사한 moat 구축입니다."
        )
        vertical_rows = [
            ["레이어 1: GPU (칩)", "H100/B200/Rubin",
             "AI 연산의 핵심 하드웨어",
             "TSMC 파운드리 의존 (유일한 외부 의존), "
             "CoWoS 패키징 병목",
             "~60% 영업이익률"],
            ["레이어 2: 연결망 (NVLink/NVSwitch)", "NVLink 5.0, NVSwitch",
             "GPU 간 초고속 연결 (1.8TB/s)",
             "NVIDIA 독자 설계, 경쟁사 접근 불가. "
             "NVLink Domain: 576 GPU 직접 연결 가능",
             "별도 ASP 부과, 시스템 가격 +30-40%"],
            ["레이어 3: 시스템 (DGX/HGX)", "DGX B200, HGX B200",
             "GPU+NVLink+InfiniBand 통합 서버",
             "ODM(Foxconn, Wistron)이 조립하나 "
             "NVIDIA 설계 독점",
             "DGX B200 판가 $500K+"],
            ["레이어 4: 네트워크 (InfiniBand)", "Quantum-3, ConnectX-7",
             "클러스터 간 고속 네트워크",
             "Mellanox 2020년 $7B 인수. "
             "AI DC InfiniBand 점유율 80%+",
             "연간 $6B+ 매출 (추정)"],
            ["레이어 5: 소프트웨어 (CUDA/cuDNN)", "CUDA 12.x, TensorRT, Triton",
             "AI 개발 표준 플랫폼",
             "3,000만 개발자 설치 베이스. "
             "무료 제공으로 전환 비용 내재화",
             "간접 수익: GPU 판매 촉진"],
            ["레이어 6: 클라우드 (DGX Cloud)", "DGX Cloud (GCP/Oracle/Azure 통해)",
             "NVIDIA GPU 직접 클라우드 임대",
             "CSP 우회한 직접 고객 접촉. "
             "$37K/월/GPU (H100 기준 추정)",
             "2024년 런칭, 규모화 진행 중"],
        ]
        _add_table(doc, ["레이어", "제품", "역할", "경쟁 차별화", "수익 구조"],
                   vertical_rows)
        doc.add_paragraph(
            "수직통합 전략의 핵심 효과: 각 레이어가 아래 레이어의 수요를 창출. "
            "DGX Cloud → DGX 시스템 수요 → GPU 수요 → NVLink 수요 → CUDA 의존성 심화. "
            "이 구조가 완성되면 NVIDIA는 단순 GPU 벤더에서 AI 인프라 플랫폼으로 전환 완료. "
            "비교: AWS의 EC2→S3→Lambda→Bedrock 수직통합과 유사한 패턴."
        )

        _add_heading(doc, "NVIDIA 반독점 리스크 분석", 2)
        doc.add_paragraph(
            "NVIDIA의 AI GPU 시장 지배력이 규제 당국의 시선을 끌고 있습니다. "
            "실제 반독점 리스크를 법적 근거와 함께 분석합니다."
        )
        antitrust_rows = [
            ["미국 DOJ/FTC 조사",
             "2024년 DOJ, NVIDIA 반독점 조사 소환장 발부 (보도). "
             "혐의: 독점적 지위 남용, 고객이 AMD로 전환 시 불이익 제공 여부",
             "중간",
             "소환장 = 조사 착수, 기소 아님. "
             "Google 반독점 판결(검색) 선례 고려. "
             "NVIDIA는 소프트웨어를 무료 제공 → '자연스러운' lock-in 주장",
             "2025-2027년 심의 지속, 기소 가능성 20-30%"],
            ["EU 경쟁법 조사",
             "유럽 Commission, AI 칩 시장 지배력 예비 조사 (2024). "
             "Run:ai 인수($700M, 2024) 심사",
             "낮음~중간",
             "EU는 빅테크에 강경한 편 (Google, Meta 과징금 선례). "
             "Run:ai 인수는 AI 워크로드 관리 소프트웨어 → 독점 강화 우려",
             "과징금 가능성 있으나 사업 구조 분리 가능성 낮음"],
            ["중국 반독점 조사",
             "SAMR(시장감독총국) 조사 가능성. "
             "Mellanox 인수 승인 조건 (중국 시장 접근 제한 금지) 이행 여부",
             "중간",
             "중국 매출 제한된 상황에서 상징적 조치 가능. "
             "지정학적 보복 수단으로 활용될 소지",
             "소규모 과징금 또는 조건부 시정 조치"],
            ["고객 반독점 소송",
             "CSP, 스타트업이 NVIDIA의 독점적 가격 책정 소송 제기 가능",
             "낮음",
             "GPU 구매자가 독점 소송 제기 시 '제품 구매를 강요받지 않았다'는 논리 약함. "
             "단, CUDA 무료 + 고사양 GPU 번들 판매 강요 논란",
             "개별 사례 합의로 마무리 가능성"],
        ]
        _add_table(doc, ["조사/소송", "내용", "현재 리스크 수준",
                          "법적 근거 & 반론", "예상 전개"],
                   antitrust_rows)
        doc.add_paragraph(
            "전문가 투자 관점: 반독점 리스크는 단기 주가 이벤트 리스크이나 "
            "사업 구조 분리(Break-up) 가능성은 낮음. "
            "역사적 선례: Microsoft(2001년 분리 명령 → 항소 승소), Google(2024 판결 → 구제책 논의 중). "
            "NVIDIA의 수직통합이 '소비자 이익' 침해를 입증하기 어려운 구조 → 법적 방어력 강함. "
            "모니터링: DOJ 공식 기소 여부 → 발생 시 주가 10-20% 단기 조정 가능."
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
            "NVIDIA의 시장점유율이 80%+임에도 반독점 조사를 덜 받는 이유를 "
            "'소프트웨어 생태계'와 '자연스러운 고착화' 관점에서 설명하세요.",
            "1장 참고. CUDA 3,000만 개발자의 자발적 선택 vs. 강제적 독점을 구분하세요.",
            "비즈니스 분석 (규제·경쟁 전략)"
        ),
        (
            "H100에서 B200으로 업그레이드 시 '단위 추론 비용($/토큰)'이 어떻게 변하는지 "
            "계산하고, CSP가 업그레이드할 수밖에 없는 경제적 이유를 설명하세요.",
            "2장 계산 예제 참고. 성능 2.3배, 가격 2.3배 → 단위 비용 불변 vs. "
            "GB200 NVL72 랙 시스템 시 성능/가격 비율 차이를 비교하세요.",
            "정량 계산 (ROI 분석)"
        ),
        (
            "AMD MI300X가 NVIDIA H100 대비 메모리 용량(192GB vs 80GB)에서 2.4배 우위임에도 "
            "NVIDIA 점유율을 크게 빼앗지 못하는 이유를 3가지 제시하세요.",
            "5장 참고. 소프트웨어 에코시스템, 학습 vs. 추론 차이, CoWoS 배분 문제를 활용하세요.",
            "경쟁 분석 (기술 + 비즈니스)"
        ),
        (
            "미국 BIS의 수출 규제로 NVIDIA 중국 매출이 $17B → $5B으로 감소했음에도 "
            "NVIDIA 주가와 실적이 오히려 개선된 역설을 설명하세요.",
            "6장 참고. 중국 이외 지역 수요 폭증의 원인과 ChatGPT 출시 타이밍을 고려하세요.",
            "시나리오 분석 (지정학 + 비즈니스)"
        ),
        (
            "NVIDIA FY2026E P/E가 20x로 Microsoft(30x)보다 낮은데도 "
            "일부 애널리스트가 NVIDIA를 더 매력적이라고 보는 이유를 "
            "PEG 비율로 설명하세요.",
            "7장 계산 예제 참고. P/E를 EPS 성장률로 나눈 PEG 비율을 계산하고, "
            "0.5 이하가 왜 매력적인지 설명하세요.",
            "투자 분석 (밸류에이션)"
        ),
        (
            "CoWoS가 반도체 공급망에서 '전략적 병목(Strategic Bottleneck)'이 되는 이유와 "
            "TSMC가 이 병목을 이용해 가격 인상을 단행한 것이 왜 가능했는지 설명하세요.",
            "3장과 6장 참고. 독점 + 대체 불가 + 수요 긴급성의 3요소를 활용하세요.",
            "공급망 분석 (구조적 이해)"
        ),
        (
            "GB200 NVL72 랙이 $3M이고 NVIDIA 마진이 ~65%라면, "
            "이 랙 1,000개 출하 시 NVIDIA가 창출하는 영업이익은 얼마인가? "
            "그리고 이 매출이 FY2026E 전체 영업이익($115B)에서 차지하는 비중은?",
            "4장 수익 구조 참고. $3M × 65% × 1,000랙 = ? 그리고 $115B 대비 % 계산.",
            "정량 계산 (비즈니스 수학)"
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
         "CUDA는 개발자들이 자발적으로 선택한 생태계. '강제'가 아닌 '우월한 도구'로 고착화. "
         "반독점 = 시장 지배력 남용이 필요 → NVIDIA는 '더 좋은 제품'으로 점유율 획득. "
         "오픈소스 경쟁(ROCm)이 허용되어 있어 반독점 논거 약함."),
        ("Q2 핵심",
         "H100 vs B200 단위 비용: 989 TF/$30K = 32.9 TF/$1K vs 2,250 TF/$70K = 32.1 TF/$1K → 유사. "
         "GB200 NVL72: 90,000 TF(72B200 합산)/$3M = 30 TF/$1K → 소폭 불리해 보임. "
         "그러나 단위 전력 효율(TFLOP/W)이 2배 개선 → 전기료 절감으로 5년 TCO가 유리. CSP 업그레이드 이유."),
        ("Q3 핵심",
         "① ROCm 소프트웨어 성숙도 부족 (커스텀 커널 재작성 비용 막대). "
         "② AI 학습에서 H100 대비 20-30% 성능 열위. "
         "③ CoWoS 패키징 물량이 NVIDIA에 우선 배정 → AMD GPU도 CoWoS 경쟁에서 열위."),
        ("Q4 핵심",
         "수출 규제 타이밍(2022 하반기)이 ChatGPT 출시(2022.11)와 겹침. "
         "중국 $17B 손실보다 미국·유럽·중동의 AI 수요 폭발($50B+)이 훨씬 컸음. "
         "역설: 규제가 중국 경쟁사(화웨이 Ascend 등) 성장을 막아 NVIDIA 독점 강화에 기여."),
        ("Q5 핵심",
         "NVIDIA PEG = P/E 20x ÷ EPS 성장률 46% = 0.43x. "
         "Microsoft PEG = P/E 30x ÷ EPS 성장률 15% = 2.0x. "
         "PEG < 1.0이면 '성장 대비 저평가'. NVIDIA PEG 0.43x는 대형 성장주 중 최저 수준."),
        ("Q6 핵심",
         "CoWoS = TSMC 독점 + 대체 불가(2-3년 구축 시간) + 수요 긴급성(AI 군비경쟁). "
         "이 3요소가 구매자의 협상력을 제로로 만들어 TSMC가 20%+ 가격 인상 가능. "
         "NVIDIA도 CoWoS 비용 상승분을 GPU 가격에 전가 → 마진 유지."),
        ("Q7 핵심",
         "$3M × 65% × 1,000 = $1.95B 영업이익. "
         "$1.95B ÷ $115B = 1.7% (랙 1,000개 = 전체 영업이익의 1.7%). "
         "GB200 NVL72 출하량이 40,000랙(2026E)이면: $78B 영업이익 → 전체의 67% 기여."),
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
    out = OUTPUT_DIR / f"study_nvidia_supply_chain{level_suffix}_{today_str}.docx"
    doc.save(str(out))
    print(f"  [NVIDIA Study] 생성 완료: {out}")
    print(f"  [NVIDIA Study] 8장 구성, {len(REFS)}개 참고자료, 7문항 복습 문제 (Level {level})")
    return str(out)


def run(level=1):
    return {"word_path": build(level)}


if __name__ == "__main__":
    result = run()
    print(f"\n출력 파일: {result['word_path']}")
