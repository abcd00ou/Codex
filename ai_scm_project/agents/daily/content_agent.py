"""
Content Agent - Claude API로 동적 학습 콘텐츠 생성
하드코딩 없이 매일 새로운 브리핑과 인사이트 제공
"""

import os
import sys
import json

_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _ROOT)

import config

# ============================================================
# 주제별 핵심 컨텍스트 (Claude에게 전달할 앵커 데이터)
# ============================================================
TOPIC_CONTEXT = {
    "hbm_deep_dive": {
        "key_companies": ["SK Hynix (50% 점유)", "Samsung (40%)", "Micron (10%)"],
        "key_metrics":   ["HBM_demand_GB = GPU × HBM_per_GPU", "B200 = 192GB HBM3e", "CoWoS yield 78%"],
        "bottleneck":    f"HBM 가동률 {config.CURRENT_CAPACITY_UTILIZATION['HBM']*100:.0f}%",
        "key_terms_ko":  ["고대역폭 메모리", "적층형 DRAM", "TSV(Through-Silicon Via)", "CoWoS 패키징"],
        "key_terms_en":  ["High Bandwidth Memory", "Stacked DRAM", "Through-Silicon Via", "Chip-on-Wafer-on-Substrate"],
    },
    "cowos_packaging": {
        "key_companies": ["TSMC (독점)", "ASE", "Amkor"],
        "key_metrics":   [f"캐파 120K wpm (2026)", "리드타임 18개월", f"가동률 {config.CURRENT_CAPACITY_UTILIZATION['CoWoS']*100:.0f}%"],
        "bottleneck":    f"CoWoS 가동률 {config.CURRENT_CAPACITY_UTILIZATION['CoWoS']*100:.0f}%",
        "key_terms_ko":  ["CoWoS 패키징", "Interposer", "Fan-Out WLP", "HBM 적층"],
        "key_terms_en":  ["Chip-on-Wafer-on-Substrate", "Silicon Interposer", "Fan-Out Wafer Level Package", "HBM Stacking"],
    },
    "power_infrastructure": {
        "key_companies": ["Vertiv", "Eaton", "Schneider Electric", "GE Vernova", "ABB"],
        "key_metrics":   [f"DC 전력 {config.DC_POWER['2026_gw']}GW (2026E)", "GB200 랙 1MW", "변압기 리드타임 30개월"],
        "bottleneck":    f"Power_DC 가동률 {config.CURRENT_CAPACITY_UTILIZATION['Power_DC']*100:.0f}%",
        "key_terms_ko":  ["PUE(전력사용효율)", "변압기 리드타임", "액냉각", "무정전전원장치"],
        "key_terms_en":  ["Power Usage Effectiveness", "Transformer Lead Time", "Liquid Cooling", "UPS"],
    },
    "nvidia_supply_chain": {
        "key_companies": ["NVIDIA", "TSMC (파운드리)", "SK Hynix (HBM)", "Broadcom (NIC)"],
        "key_metrics":   ["데이터센터 매출 $150B/yr", "B200 출하 500만개(2026E)", "GB200 NVL72 랙 $3M"],
        "bottleneck":    f"GPU 가동률 {config.CURRENT_CAPACITY_UTILIZATION['GPU']*100:.0f}%",
        "key_terms_ko":  ["파운드리 의존성", "HBM 독점 공급", "CoWoS 패키징", "NVLink 토폴로지"],
        "key_terms_en":  ["Foundry Dependency", "HBM Exclusive Supply", "CoWoS Packaging", "NVLink Topology"],
    },
    "hyperscaler_capex": {
        "key_companies": ["Microsoft ($95B)", "Amazon ($120B)", "Google ($90B)", "Meta ($72B)", "xAI ($30B)"],
        "key_metrics":   ["2026 총 CapEx $407B 추정", "AI 비중 60%+", "4사 합산 연 30%+ 성장"],
        "bottleneck":    "전력·부지·패키징이 집행 제약",
        "key_terms_ko":  ["자본지출", "AI 가속기 구매", "DC 임대 vs 자체 구축", "수익화 타임라인"],
        "key_terms_en":  ["Capital Expenditure", "AI Accelerator Procurement", "Leased vs Owned DC", "Monetization Timeline"],
    },
    "ai_networking": {
        "key_companies": ["Broadcom (이더넷 ASIC)", "Mellanox/NVIDIA (InfiniBand)", "Arista", "Cisco"],
        "key_metrics":   [f"Networking 가동률 {config.CURRENT_CAPACITY_UTILIZATION['Networking']*100:.0f}%", "400G→800G 전환 중", "NVL72 = 72GPU 완전연결"],
        "bottleneck":    f"Networking 가동률 {config.CURRENT_CAPACITY_UTILIZATION['Networking']*100:.0f}%",
        "key_terms_ko":  ["InfiniBand", "RDMA", "GPU-to-GPU 대역폭", "클러스터 토폴로지"],
        "key_terms_en":  ["InfiniBand", "Remote Direct Memory Access", "GPU-to-GPU Bandwidth", "Cluster Topology"],
    },
    "sovereign_ai": {
        "key_companies": ["G42 (UAE $100B)", "ARAMCO AI (사우디 $40B)", "GENCI (EU)", "NDIAS (India)"],
        "key_metrics":   ["추가 GPU 수요 15-20%", "UAE 5만대 GPU 추정", "사우디 3만대 GPU"],
        "bottleneck":    "수출 통제 + 지정학적 리스크",
        "key_terms_ko":  ["AI 주권", "수출 통제 (BIS)", "국가 AI 클러스터", "NVIDIA 수출 제한"],
        "key_terms_en":  ["AI Sovereignty", "Export Controls (BIS)", "National AI Cluster", "NVIDIA Export Restrictions"],
    },
    "investment_framework": {
        "key_companies": ["SK Hynix (Strong Buy)", "TSMC", "Vertiv", "Broadcom", "GE Vernova"],
        "key_metrics":   ["Phase 2→3 전환기", "HBM 업사이클 지속", "전력 인프라 멀티년 성장"],
        "bottleneck":    "투자 사이클: GPU→HBM→Power→Edge",
        "key_terms_ko":  ["병목 투자 프레임워크", "업스트림 수혜", "Phase 로드맵", "리스크 요인"],
        "key_terms_en":  ["Bottleneck Investment Framework", "Upstream Beneficiary", "Phase Roadmap", "Risk Factors"],
    },
}


def generate_briefing(topic: dict, news: list[dict]) -> str:
    """
    Claude API로 오늘의 학습 브리핑 HTML 생성
    API 실패 시 fallback 콘텐츠 반환
    """
    topic_id   = topic["id"]
    title      = topic["title"]
    title_en   = topic["title_en"]
    level      = topic.get("level", 1)
    level_meta = topic.get("level_meta", {})
    ctx        = TOPIC_CONTEXT.get(topic_id, {})

    news_summary = "\n".join(
        f"- {n['title']} ({n['source']}, {n['date']})"
        for n in news[:3]
    )

    if os.environ.get("DISABLE_CLAUDE_API") or not os.environ.get("ANTHROPIC_API_KEY"):
        return _fallback_briefing(topic, ctx, level_meta)

    try:
        import anthropic
        client = anthropic.Anthropic()

        level_instruction = {
            1: "개념과 용어를 쉽게 설명하는 입문자 수준. 비유와 예시 중심.",
            2: "정량 모델, 수식, 케이스 스터디 포함. 메커니즘 깊게 설명.",
            3: "최신 트렌드, 투자 리포트 관점, 시나리오 분석. 전문가 인사이트.",
        }.get(level, "")

        prompt = f"""당신은 AI 반도체 공급망 전문가이자 마케터 교육 전문가입니다.
오늘의 학습 브리핑을 생성해주세요.

주제: {title} ({title_en})
레벨: {level_meta.get('label', '')} — {level_instruction}

핵심 기업: {', '.join(ctx.get('key_companies', []))}
핵심 지표: {', '.join(ctx.get('key_metrics', []))}
현재 병목 상황: {ctx.get('bottleneck', '')}

오늘의 관련 뉴스:
{news_summary}

다음 형식으로 HTML 콘텐츠를 생성해주세요 (한영 혼합, 마케터 실용 관점):

1. **오늘의 핵심 포인트** (2-3 문장, 마케터가 고객에게 설명할 수 있는 수준)
2. **핵심 키워드** 5개 (한국어 + English + 한 줄 설명)
3. **수식/정량 모델** 1-2개 (있는 경우)
4. **마케터 실전 인사이트** 2개 (영업/제안에서 활용할 포인트)
5. **오늘 뉴스와의 연결점** (위 뉴스가 이 주제와 어떻게 연결되는지 1-2문장)

<div> 태그와 inline style만 사용하세요. <script> 없이. 이메일 HTML 형식으로."""

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text

    except Exception as e:
        print(f"  [ContentAgent] Claude API 실패 ({e}) → fallback 사용")
        return _fallback_briefing(topic, ctx, level_meta)


def generate_quiz(topic: dict) -> list[dict]:
    """
    Claude API로 객관식 퀴즈 3개 생성
    Returns: [{question, options:[A..D], answer, explanation}, ...]
    """
    topic_id   = topic["id"]
    title      = topic["title"]
    level      = topic.get("level", 1)
    ctx        = TOPIC_CONTEXT.get(topic_id, {})

    if os.environ.get("DISABLE_CLAUDE_API") or not os.environ.get("ANTHROPIC_API_KEY"):
        return _fallback_quiz(topic, ctx)

    try:
        import anthropic
        client = anthropic.Anthropic()

        prompt = f"""AI 반도체 공급망 마케터를 위한 퀴즈 3개를 생성해주세요.

주제: {title}
레벨: Lv.{level}
핵심 기업: {', '.join(ctx.get('key_companies', []))}
핵심 지표: {', '.join(ctx.get('key_metrics', []))}

요구사항:
- 객관식 4지선다 (A/B/C/D)
- 마케터가 고객과 대화할 때 실제로 필요한 지식
- 난이도: Lv.1=기초 개념, Lv.2=수치/메커니즘, Lv.3=트렌드/투자 판단

JSON 형식으로만 출력하세요 (다른 텍스트 없이):
[
  {{
    "question": "질문 텍스트",
    "options": {{"A": "보기1", "B": "보기2", "C": "보기3", "D": "보기4"}},
    "answer": "B",
    "explanation": "정답 해설 (한국어, 2-3문장)"
  }},
  ...
]"""

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()
        # JSON 파싱
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    except Exception as e:
        print(f"  [ContentAgent] 퀴즈 생성 실패 ({e}) → fallback 퀴즈")
        return _fallback_quiz(topic, ctx)


def _fallback_briefing(topic: dict, ctx: dict, level_meta: dict) -> str:
    kw_pairs = list(zip(
        ctx.get("key_terms_ko", []),
        ctx.get("key_terms_en", [])
    ))
    kw_html = "".join(
        f'<li><strong>{ko}</strong> ({en}): AI SCM의 핵심 용어</li>'
        for ko, en in kw_pairs[:5]
    )
    metrics_html = "".join(
        f'<li>{m}</li>' for m in ctx.get("key_metrics", [])
    )
    companies_str = ", ".join(ctx.get("key_companies", []))

    lv_label = level_meta.get("label", "Lv.1 기초")
    lv_color = level_meta.get("color", "#1a73e8")

    return f"""<div style="font-family:Arial,sans-serif; line-height:1.7; color:#333;">
<p style="border-left:3px solid {lv_color}; padding-left:10px; margin-bottom:14px;">
<strong>핵심 포인트 [{lv_label}]:</strong> {topic['title']}({topic['title_en']})은 AI 공급망의 핵심 레이어입니다.
현재 병목 상황: {ctx.get('bottleneck', '분석 중')}. 주요 수혜 기업: {companies_str}.</p>

<p><strong>핵심 지표:</strong></p>
<ul>{metrics_html}</ul>

<p><strong>핵심 키워드:</strong></p>
<ul>{kw_html}</ul>

<p><strong>마케터 인사이트:</strong><br>
① 이 레이어의 병목은 고객의 프로젝트 타임라인에 직접 영향을 줍니다.<br>
② 리드타임과 가동률 데이터를 근거로 공급 리스크를 정량화하세요.</p>
</div>"""


def _fallback_quiz(topic: dict, ctx: dict) -> list[dict]:
    companies = ctx.get("key_companies", ["SK Hynix", "TSMC", "NVIDIA", "Broadcom"])
    return [
        {
            "question": f"{topic['title']}에서 현재 가장 높은 시장점유율을 가진 기업은?",
            "options": {
                "A": companies[0] if len(companies) > 0 else "SK Hynix",
                "B": companies[1] if len(companies) > 1 else "Samsung",
                "C": companies[2] if len(companies) > 2 else "TSMC",
                "D": companies[3] if len(companies) > 3 else "Micron",
            },
            "answer": "A",
            "explanation": f"{companies[0]}이 현재 해당 레이어에서 선도적인 위치를 차지하고 있습니다. 병목 상황: {ctx.get('bottleneck', '')}",
        },
        {
            "question": f"AI 공급망에서 {topic['title_en']}의 현재 병목 상황은?",
            "options": {
                "A": "공급 과잉 (가동률 50% 이하)",
                "B": "균형 상태 (가동률 50~70%)",
                "C": "타이트 (가동률 70~85%)",
                "D": "심각한 병목 (가동률 85% 이상)",
            },
            "answer": "D",
            "explanation": f"현재 {ctx.get('bottleneck', '가동률이 높은 상태')}로, 공급망 병목이 지속되고 있습니다.",
        },
        {
            "question": f"{topic['title']}과 관련하여 마케터가 고객에게 가장 강조해야 할 핵심 리스크는?",
            "options": {
                "A": "가격 하락 리스크",
                "B": "리드타임 및 공급 제약",
                "C": "기술 진부화 리스크",
                "D": "수요 둔화 리스크",
            },
            "answer": "B",
            "explanation": "AI 공급망의 주요 병목은 리드타임과 생산 캐파 제약입니다. 고객에게 조기 발주와 장기 계약의 중요성을 강조하세요.",
        },
    ]
