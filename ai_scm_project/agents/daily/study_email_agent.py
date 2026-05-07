"""
Study Email Agent
- 주제별 종합 학습 이메일 생성 + 발송
- config.py 실제 데이터 기반 (시장·기술·공급망·투자·기업관계)
- 기준: 2026년 4월 현재
"""

import os, sys, smtplib, ssl, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText

_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _ROOT)

import config
from agents.daily.news_agent import get_topic_news

GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT      = os.environ.get("GMAIL_RECIPIENT", GMAIL_ADDRESS)

AS_OF = "2026년 4월 현재"

# ============================================================
# 주제 정의
# ============================================================
TOPICS = [
    {"id": "hbm_deep_dive",       "title": "HBM (High Bandwidth Memory) 심층 분석",      "color": "#3182ce"},
    {"id": "cowos_packaging",      "title": "CoWoS & 첨단 패키징 기술",                    "color": "#d69e2e"},
    {"id": "power_infrastructure", "title": "AI 데이터센터 전력 인프라",                   "color": "#718096"},
    {"id": "nvidia_supply_chain",  "title": "NVIDIA GPU 공급망 & 비즈니스 모델",           "color": "#e53e3e"},
    {"id": "hyperscaler_capex",    "title": "하이퍼스케일러 CapEx 전략 & AI 투자",         "color": "#38a169"},
    {"id": "ai_networking",        "title": "AI 클러스터 네트워킹 (InfiniBand & Ethernet)", "color": "#dd6b20"},
    {"id": "sovereign_ai",         "title": "Sovereign AI & 지정학적 반도체 전략",         "color": "#805ad5"},
    {"id": "investment_framework", "title": "AI 공급망 투자 프레임워크 & 포트폴리오",       "color": "#2d3748"},
]


# ============================================================
# 공급망 관계 추출 헬퍼 (config.py COMPANY_RELATIONSHIPS 활용)
# ============================================================
def _get_relationships_for(company: str) -> dict:
    """company가 공급하는 곳, 공급받는 곳 분리"""
    supplies_to, supplied_by = [], []
    for (frm, to, rtype, desc_ko, val, _) in config.COMPANY_RELATIONSHIPS:
        if frm == company:
            supplies_to.append((to, rtype, desc_ko, val))
        if to == company:
            supplied_by.append((frm, rtype, desc_ko, val))
    return {"supplies_to": supplies_to, "supplied_by": supplied_by}


def _scm_table_html(rows: list[tuple], header: str) -> str:
    """(company, type, desc, value) 리스트 → HTML 테이블"""
    TYPE_COLOR = {
        "hardware_supply": "#e6fffa", "investment": "#fff5f7",
        "service": "#ebf8ff",         "vc": "#f0fff4",
    }
    TYPE_LABEL = {
        "hardware_supply": "공급", "investment": "투자",
        "service": "서비스",      "vc": "VC",
    }
    if not rows:
        return ""
    body = "".join(
        f'<tr style="background:{TYPE_COLOR.get(rtype,"#fff")};">'
        f'<td style="padding:5px 10px; font-weight:600; white-space:nowrap;">{co}</td>'
        f'<td style="padding:5px 10px; color:#718096; font-size:12px;">'
        f'<span style="background:#e2e8f0; padding:1px 6px; border-radius:3px;">'
        f'{TYPE_LABEL.get(rtype, rtype)}</span></td>'
        f'<td style="padding:5px 10px; font-size:13px;">{desc}</td>'
        f'<td style="padding:5px 10px; color:#2d3748; font-weight:600; white-space:nowrap;">{val}</td>'
        f'</tr>'
        for co, rtype, desc, val in rows
    )
    return (
        f'<p style="font-weight:700; color:#2d3748; margin:14px 0 6px;">{header}</p>'
        f'<table style="border-collapse:collapse; width:100%; font-size:13px; '
        f'border:1px solid #e2e8f0; border-radius:4px;">'
        f'<thead><tr style="background:#f7f8fa;">'
        f'<th style="padding:6px 10px; text-align:left; color:#4a5568;">기업</th>'
        f'<th style="padding:6px 10px; text-align:left; color:#4a5568;">관계</th>'
        f'<th style="padding:6px 10px; text-align:left; color:#4a5568;">내용</th>'
        f'<th style="padding:6px 10px; text-align:left; color:#4a5568;">규모</th>'
        f'</tr></thead><tbody>{body}</tbody></table>'
    )


def _util_bar(key: str) -> str:
    v   = config.CURRENT_CAPACITY_UTILIZATION.get(key, 0)
    pct = int(v * 100)
    w   = int(v * 200)
    c   = "#e53e3e" if pct >= 85 else "#d69e2e" if pct >= 70 else "#38a169"
    return (
        f'<span style="display:inline-flex; align-items:center; gap:6px;">'
        f'<span style="display:inline-block; background:{c}; width:{w}px; '
        f'height:8px; border-radius:2px;"></span>'
        f'<strong style="color:{c};">{pct}%</strong></span>'
    )


def _capex_bar_html() -> str:
    """하이퍼스케일러 CapEx 비교 바 차트"""
    colors = {"Microsoft": "#00a1f1", "Google": "#4285f4",
              "Amazon": "#ff9900",    "Meta": "#1877f2", "xAI": "#1da1f2"}
    rows = []
    for co, data in config.HYPERSCALER_CAPEX.items():
        color = colors.get(co, "#718096")
        y2022 = data.get("2022", 0)
        y2024 = data.get("2024", 0)
        y2025 = data.get("2025", 0)
        y2026 = data.get("2026", 0)
        # 최대 $120B 기준 200px
        def bw(v): return max(4, int(v / 120 * 180))
        rows.append(
            f'<tr>'
            f'<td style="padding:4px 10px 4px 0; font-weight:600; color:#2d3748; width:90px;">{co}</td>'
            f'<td style="padding:4px 4px;">'
            f'<div style="display:flex; flex-direction:column; gap:2px;">'
            f'<div style="display:flex; align-items:center; gap:4px;">'
            f'<span style="font-size:10px; color:#a0aec0; width:32px;">\'22</span>'
            f'<div style="background:#e2e8f0; height:8px; width:{bw(y2022)}px; border-radius:2px;"></div>'
            f'<span style="font-size:11px; color:#718096;">${y2022}B</span></div>'
            f'<div style="display:flex; align-items:center; gap:4px;">'
            f'<span style="font-size:10px; color:#a0aec0; width:32px;">\'24</span>'
            f'<div style="background:{color}88; height:8px; width:{bw(y2024)}px; border-radius:2px;"></div>'
            f'<span style="font-size:11px; color:#718096;">${y2024}B</span></div>'
            f'<div style="display:flex; align-items:center; gap:4px;">'
            f'<span style="font-size:10px; color:#a0aec0; width:32px;">\'25</span>'
            f'<div style="background:{color}bb; height:8px; width:{bw(y2025)}px; border-radius:2px;"></div>'
            f'<span style="font-size:11px; color:#718096;">${y2025}B</span></div>'
            f'<div style="display:flex; align-items:center; gap:4px;">'
            f'<span style="font-size:10px; color:#a0aec0; width:32px;">\'26E</span>'
            f'<div style="background:{color}; height:10px; width:{bw(y2026)}px; border-radius:2px;"></div>'
            f'<span style="font-size:12px; font-weight:700; color:{color};">${y2026}B</span></div>'
            f'</div></td></tr>'
        )
    return '<table style="border-collapse:collapse; width:100%;">' + "".join(rows) + '</table>'


# ============================================================
# 주제별 콘텐츠 본문 (사실 기반, config.py 데이터 연동)
# ============================================================

def _content_hbm() -> str:
    hbm = config.HBM_MARKET
    rel_sk = _get_relationships_for("SK Hynix")
    return f"""
<h3 style="color:#3182ce; border-bottom:2px solid #3182ce; padding-bottom:6px;">⚙️ 기술 핵심</h3>
<p>HBM(High Bandwidth Memory)은 여러 DRAM 다이를 수직으로 적층하고
<strong>TSV(Through-Silicon Via, 실리콘 관통 전극)</strong>로 연결한 고대역폭 메모리입니다.
AI 모델 추론 시 대규모 행렬 연산에서 데이터를 빠르게 공급해야 하므로,
일반 GDDR6(~$960GB/s) 대비 <strong>HBM3e는 ~5TB/s 대역폭</strong>을 제공합니다.</p>

<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#ebf8ff;">
    <th style="padding:6px 10px; text-align:left;">규격</th>
    <th style="padding:6px 10px; text-align:left;">대역폭</th>
    <th style="padding:6px 10px; text-align:left;">용량/GPU</th>
    <th style="padding:6px 10px; text-align:left;">주요 탑재</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px;">HBM2e</td><td>1.6 TB/s</td><td>80 GB</td><td>A100</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px;">HBM3</td><td>3.35 TB/s</td><td>80 GB</td><td>H100 SXM5</td></tr>
    <tr><td style="padding:5px 10px;"><strong>HBM3e</strong></td><td><strong>4.8–8.0 TB/s</strong></td><td><strong>141–192 GB</strong></td><td><strong>H200, B200, MI300X</strong></td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px;">HBM4 (2026H2E)</td><td>~12 TB/s</td><td>256+ GB</td><td>Rubin (2027E)</td></tr>
  </tbody>
</table>
<p>B200 GPU 1개 = HBM3e <strong>8 스택 × 24GB = 192GB</strong>, 대역폭 <strong>8.0 TB/s</strong>.
GB200 NVL72 랙 = B200 72개 = HBM3e <strong>13,824GB</strong> 탑재.</p>
<p>HBM은 반드시 <strong>CoWoS 패키징</strong>을 통해 GPU 다이와 동일 인터포저에 물리적으로 결합됩니다.
이 때문에 HBM 생산량은 <strong>TSMC CoWoS 캐파에 의해 상한이 결정</strong>됩니다.</p>

<h3 style="color:#3182ce; border-bottom:2px solid #3182ce; padding-bottom:6px; margin-top:20px;">📊 시장 현황 ({AS_OF})</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#ebf8ff;">
    <th style="padding:6px 10px; text-align:left;">연도</th>
    <th style="padding:6px 10px; text-align:left;">HBM 시장 규모</th>
    <th style="padding:6px 10px; text-align:left;">비고</th>
  </tr></thead>
  <tbody>
    {''.join(f'<tr{"" if i%2 else " style=background:#f7f8fa;"}><td style=padding:5px_10px;>{yr}{"" if yr!="2026" else " (진행 중)"}</td><td style=padding:5px_10px;><strong>${sz}B</strong></td><td style=padding:5px_10px;color:#718096;>{"actual" if yr in ["2023","2024","2025"] else "추정"}</td></tr>' for i, (yr, sz) in enumerate(hbm["market_size_usd_bn"].items()))}
  </tbody>
</table>
<p>가동률: {_util_bar("HBM")} &nbsp;→&nbsp; CoWoS 병목에 의한 구조적 공급 제약</p>
<p>가격: HBM2e <strong>$8/GB</strong> → HBM3 <strong>$14/GB</strong> → HBM3e <strong>${hbm["price_per_gb_usd"]["HBM3e"]}/GB</strong>.
HBM4 출시 시 40% ASP 프리미엄 예상 (~$25/GB).</p>

<h3 style="color:#3182ce; border-bottom:2px solid #3182ce; padding-bottom:6px; margin-top:20px;">🏭 공급망 구조</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#ebf8ff;">
    <th style="padding:6px 10px;">제조사</th>
    <th style="padding:6px 10px;">점유율</th>
    <th style="padding:6px 10px;">WPM (2026E)</th>
    <th style="padding:6px 10px;">NVIDIA 납품 현황</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px; font-weight:700;">SK Hynix</td>
        <td style="padding:5px 10px;"><strong>50%</strong></td>
        <td style="padding:5px 10px;">{config.HBM_MARKET["capacity_wafers_per_month"]["SK_Hynix"]:,}</td>
        <td style="padding:5px 10px;">HBM3e 독점 공급 (H200, B200, GB200)</td></tr>
    <tr style="background:#f7f8fa;">
        <td style="padding:5px 10px;">Samsung</td>
        <td style="padding:5px 10px;">38%</td>
        <td style="padding:5px 10px;">{config.HBM_MARKET["capacity_wafers_per_month"]["Samsung"]:,}</td>
        <td style="padding:5px 10px;">HBM3e 재인증 후 공급 재개 (2025 H2)</td></tr>
    <tr><td style="padding:5px 10px;">Micron</td>
        <td style="padding:5px 10px;">12%</td>
        <td style="padding:5px 10px;">{config.HBM_MARKET["capacity_wafers_per_month"]["Micron"]:,}</td>
        <td style="padding:5px 10px;">HBM3e 10% 공급, CHIPS Act 보조금 증설</td></tr>
  </tbody>
</table>
{_scm_table_html(rel_sk["supplies_to"][:4], "SK Hynix → 공급처")}
<p style="margin-top:10px;"><strong>Samsung 이슈:</strong> 2024년 HBM3e 발열·소비전력 문제로 NVIDIA 퀄리피케이션 탈락.
2025 H2 재인증 성공했으나, SK Hynix 독점적 지위는 단기간 유지될 전망.</p>

<h3 style="color:#3182ce; border-bottom:2px solid #3182ce; padding-bottom:6px; margin-top:20px;">💡 핵심 수식</h3>
<div style="background:#ebf8ff; border-radius:6px; padding:12px 16px; font-family:monospace; font-size:13px; line-height:2;">
HBM_demand_GB = GPU_count × HBM_per_GPU_GB<br>
&nbsp;&nbsp;예) GB200 NVL72 1랙 = 72 × 192GB = 13,824GB HBM3e<br>
<br>
KV_Cache_GB = (context_length × concurrent_users × 2B × 2) / 1e9<br>
&nbsp;&nbsp;예) 128K ctx × 10만 사용자 × 4B = 51.2TB 상시 메모리 필요<br>
<br>
HBM 공급 상한 = TSMC CoWoS 캐파 × CoWoS yield({int(config.HBM_MARKET["yield_rate"]*100)}%)
</div>

<h3 style="color:#3182ce; border-bottom:2px solid #3182ce; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>리드타임:</strong> HBM3e 주문 → 납품 12-16주. 선발주 필수 논거.</li>
  <li><strong>병목 가시화:</strong> CoWoS 가동률 {int(config.CURRENT_CAPACITY_UTILIZATION["CoWoS"]*100)}% → HBM 증산에 구조적 한계 존재.</li>
  <li><strong>가격 논거:</strong> HBM3e $18/GB vs GDDR6X $0.5/GB — 38배 ASP 프리미엄, 대역폭 10배.</li>
  <li><strong>Micron 차별화:</strong> 미국산 HBM (Idaho 공장) → 데이터 주권·보안 강조 고객에 유효.</li>
  <li><strong>HBM4 선수 포지셔닝:</strong> 2026 H2 양산, 2027 Rubin GPU 탑재 확정 → 조기 기술 로드맵 공유.</li>
</ul>
"""


def _content_cowos() -> str:
    cw       = config.COWOS_CAPACITY
    rel_tsmc = _get_relationships_for("TSMC")
    return f"""
<h3 style="color:#d69e2e; border-bottom:2px solid #d69e2e; padding-bottom:6px;">⚙️ 기술 핵심</h3>
<p><strong>CoWoS(Chip-on-Wafer-on-Substrate)</strong>는 TSMC의 2.5D 고급 패키징 기술입니다.
GPU 다이와 HBM 다이를 <strong>실리콘 인터포저(중간 기판)</strong> 위에 나란히 배치하고,
수만 개의 마이크로 범프(직경 ~10μm)로 연결합니다. 이를 통해 GPU↔HBM 간
수 TB/s 대역폭의 고속 데이터 전송이 가능합니다.</p>
<p><strong>왜 CoWoS가 필요한가?</strong> GPU+HBM 패키지의 총 면적이 단일 다이 최대치(800~900mm²)를
초과하므로, 별도의 인터포저 위에 분리 배치 후 연결하는 방식을 사용합니다.
일반 OSAT(ASE, Amkor) 패키징 대비 비용이 20-30배이지만 대역폭이 압도적입니다.</p>

<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#fefcbf;">
    <th style="padding:6px 10px;">CoWoS 유형</th>
    <th style="padding:6px 10px;">인터포저</th>
    <th style="padding:6px 10px;">적용</th>
    <th style="padding:6px 10px;">특징</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px;"><strong>CoWoS-S</strong></td>
        <td>실리콘 인터포저</td>
        <td>H100, H200, B200, MI300X</td>
        <td>표준형. 현재 주력 생산</td></tr>
    <tr style="background:#faf7e6;"><td style="padding:5px 10px;"><strong>CoWoS-R</strong></td>
        <td>RDL 인터포저</td>
        <td>더 큰 패키지 사이즈</td>
        <td>비용↓ 크기↑</td></tr>
    <tr><td style="padding:5px 10px;"><strong>CoWoS-L</strong></td>
        <td>Local Si Interconnect</td>
        <td>Rubin(2027E), GB300</td>
        <td>최대 크기, HBM4 연동</td></tr>
  </tbody>
</table>

<h3 style="color:#d69e2e; border-bottom:2px solid #d69e2e; padding-bottom:6px; margin-top:20px;">📊 캐파 추이 ({AS_OF})</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#fefcbf;">
    <th style="padding:6px 10px;">연도</th>
    <th style="padding:6px 10px;">캐파 (WPM)</th>
    <th style="padding:6px 10px;">YoY 성장</th>
    <th style="padding:6px 10px;">비고</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px;">2023</td><td>{cw["2023_wpm"]:,}</td><td>—</td><td>GB200 이전 기준</td></tr>
    <tr style="background:#faf7e6;"><td style="padding:5px 10px;">2024</td><td>{cw["2024_wpm"]:,}</td><td>+43%</td><td>H100→H200 전환 수요 급증</td></tr>
    <tr><td style="padding:5px 10px;">2025</td><td>{cw["2025_wpm"]:,}</td><td>+70%</td><td>목표 80K 초과 달성</td></tr>
    <tr style="background:#fefcbf;"><td style="padding:5px 10px;"><strong>2026E</strong></td><td><strong>{cw["2026_wpm"]:,}</strong></td><td><strong>+41%</strong></td><td>현재 진행 중</td></tr>
    <tr><td style="padding:5px 10px;">2027E</td><td>{cw["2027_est_wpm"]:,}</td><td>+33%</td><td>CoWoS-L 전환</td></tr>
  </tbody>
</table>
<p>가동률: {_util_bar("CoWoS")} &nbsp; 리드타임: <strong>{cw["lead_time_months"]}개월</strong> &nbsp; Yield: <strong>{int(cw["yield_rate"]*100)}%</strong></p>
<p>웨이퍼 1장당 가격: <strong>$20,000~30,000</strong> (표준 패키징 $500~1,000 대비 20-60배)</p>
<p>TSMC CoWoS <strong>사실상 독점</strong>: Samsung FoCoS(5~10% 점유), Amkor InFO는 HBM 연결 미지원.</p>
{_scm_table_html(rel_tsmc["supplies_to"][:5], "TSMC → 공급처")}

<h3 style="color:#d69e2e; border-bottom:2px solid #d69e2e; padding-bottom:6px; margin-top:20px;">🚨 병목 메커니즘</h3>
<p>CoWoS는 HBM 생산의 '병목 위의 병목'입니다:</p>
<div style="background:#fefcbf; border-radius:6px; padding:12px 16px; font-size:13px; line-height:2;">
① HBM 다이 생산(SK Hynix/Samsung/Micron)<br>
② <strong>→ TSMC CoWoS 패키징 (병목 구간)</strong> ← GPU 다이와 결합<br>
③ → 완성 GPU 모듈(B200, MI300X 등)<br>
④ → NVIDIA/AMD OEM → 하이퍼스케일러
</div>
<p style="margin-top:10px;">캐파 부족 시 증설에 <strong>18개월</strong> 소요(장비 발주 → 클린룸 건설 → 공정 인증).
즉, 지금 주문해도 2027 H2에나 실제 캐파 추가 가능.</p>

<h3 style="color:#d69e2e; border-bottom:2px solid #d69e2e; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>대안 없음:</strong> CoWoS 없이 HBM 탑재 AI GPU 불가. TSMC 독점 == 가격 결정력.</li>
  <li><strong>리드타임 논거:</strong> 18개월 캐파 리드타임 → 고객의 서버 도입 계획과 역산해 발주 시점 제시.</li>
  <li><strong>2026 캐파 한계:</strong> 120K wpm이 GB200 수요 전부 충족 못함 → 배분 우선권 확보 필요성 강조.</li>
  <li><strong>ASIC 차별화:</strong> Google TPU, AWS Trainium도 CoWoS 사용 → TSMC 레버리지 동일하게 받음.</li>
</ul>
"""


def _content_power() -> str:
    dc         = config.DC_POWER
    rel_vertiv = _get_relationships_for("Vertiv")
    return f"""
<h3 style="color:#718096; border-bottom:2px solid #718096; padding-bottom:6px;">⚙️ AI 데이터센터 전력 인프라 구조</h3>
<p>AI 데이터센터는 전통 DC와 완전히 다른 전력 밀도를 요구합니다.
일반 서버 랙 1개 = 5~10kW. <strong>GB200 NVL72 랙 1개 = 120kW</strong>.
전력 밀도가 12~24배 증가하면서 모든 전력 인프라 레이어를 교체해야 합니다.</p>

<div style="background:#edf2f7; border-radius:6px; padding:12px 16px; font-size:13px; line-height:2; font-family:monospace;">
[전력망] → 변전소 → <strong>변압기</strong> (병목: 리드타임 30개월) → UPS → PDU → 서버 랙<br>
                              ↓<br>
                         냉각 시스템 (공랭 → 수랭 → 직접액냉)<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Vertiv/Eaton/Schneider
</div>

<h3 style="color:#718096; border-bottom:2px solid #718096; padding-bottom:6px; margin-top:20px;">📊 글로벌 DC 전력 추이</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#edf2f7;">
    <th style="padding:6px 10px;">연도</th>
    <th style="padding:6px 10px;">글로벌 DC 전력</th>
    <th style="padding:6px 10px;">AI 비중</th>
    <th style="padding:6px 10px;">비고</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px;">2022</td><td>{dc["2022_gw"]}GW</td><td>~5%</td><td>코로나 이전 수준</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px;">2024</td><td>{dc["2024_gw"]}GW</td><td>~20%</td><td>H100 대량 배포</td></tr>
    <tr><td style="padding:5px 10px;">2025</td><td>{dc["2025_gw"]}GW</td><td>~30%</td><td>B200 ramp 시작</td></tr>
    <tr style="background:#edf2f7;"><td style="padding:5px 10px;"><strong>2026E</strong></td><td><strong>{dc["2026_gw"]}GW</strong></td><td><strong>~40%</strong></td><td>GB200 대량 배포</td></tr>
    <tr><td style="padding:5px 10px;">2027E</td><td>{dc["2027_est_gw"]}GW</td><td>~50%</td><td>AI 전력 > 비AI</td></tr>
  </tbody>
</table>
<p>가동률: {_util_bar("Power_DC")} &nbsp; PUE 평균: <strong>{dc["pue_average"]}</strong> &nbsp; 변압기 리드타임: <strong>{dc["transformer_lead_time_months"]}개월</strong></p>

<h3 style="color:#718096; border-bottom:2px solid #718096; padding-bottom:6px; margin-top:20px;">🏭 핵심 수혜 기업</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#edf2f7;">
    <th style="padding:6px 10px;">기업</th>
    <th style="padding:6px 10px;">역할</th>
    <th style="padding:6px 10px;">주요 제품</th>
    <th style="padding:6px 10px;">투자 포인트</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px; font-weight:700;">Vertiv</td>
        <td>UPS, 열관리, PDU</td>
        <td>CDU(액냉 분배), UPS 9900</td>
        <td>수주 잔고 2년치, 25%+ 성장</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700;">GE Vernova</td>
        <td>변압기, 발전</td>
        <td>Grid 변압기, 가스터빈</td>
        <td>변압기 리드타임 30개월 독점 수혜</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700;">Eaton</td>
        <td>PDU, 전력관리</td>
        <td>9PX UPS, PDU</td>
        <td>DC 전력 분배 인프라 독점적 지위</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700;">Schneider Electric</td>
        <td>통합 인프라</td>
        <td>APC UPS, EcoStruxure</td>
        <td>하이퍼스케일러 전체 DC 솔루션</td></tr>
    <tr><td style="padding:5px 10px;">ABB</td>
        <td>변전소, 변압기</td>
        <td>Power Grids</td>
        <td>유럽 AI 인프라 수혜</td></tr>
  </tbody>
</table>
{_scm_table_html(rel_vertiv["supplies_to"], "Vertiv → 공급처")}

<h3 style="color:#718096; border-bottom:2px solid #718096; padding-bottom:6px; margin-top:20px;">🚨 변압기 병목</h3>
<p>AI DC의 <strong>숨겨진 병목</strong>: 대형 전력 변압기 리드타임이 <strong>30개월</strong>로 늘어났습니다(2019년: 12개월).
이유: 변압기 권선용 구리/알루미늄 수요 급증 + 전문 제조 인력 부족 + 공장 증설 불가.
미국 내 변압기 수요의 80%는 수입, 국내 생산 복구에 5~10년 소요.</p>
<p>결과: 신규 AI DC 허가를 받아도 전력 공급 인프라 없어서 <strong>착공 못하는 사례</strong> 급증.
미국 도심 AI DC 개발의 실질적 병목. GE Vernova, ABB, Siemens Energy 중장기 수혜.</p>

<h3 style="color:#718096; border-bottom:2px solid #718096; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>전력 = 새로운 CoWoS:</strong> 2026년부터 AI DC의 실질 제약은 GPU 수급보다 전력 수급.</li>
  <li><strong>액냉각 필수화:</strong> GB200 120kW/랙 → 공랭 불가. Vertiv CDU가 사실상 필수 부품.</li>
  <li><strong>리드타임 논거:</strong> 변압기 30개월 → DC 증설 계획 고객에게 전력 인프라 선발주 강조.</li>
  <li><strong>PUE 비용 절감:</strong> PUE 1.4 → 1.2 개선 시 100MW DC 기준 연간 전기료 $20M+ 절감.</li>
</ul>
"""


def _content_nvidia() -> str:
    gpu = config.GPU_SPECS
    ship = config.GPU_SHIPMENTS
    rel_nv = _get_relationships_for("NVIDIA")
    return f"""
<h3 style="color:#e53e3e; border-bottom:2px solid #e53e3e; padding-bottom:6px;">⚙️ NVIDIA GPU 스펙 비교</h3>
<table style="border-collapse:collapse; width:100%; font-size:12px; margin:10px 0;">
  <thead><tr style="background:#fff5f5;">
    <th style="padding:6px 8px; text-align:left;">모델</th>
    <th style="padding:6px 8px;">TFLOPS</th>
    <th style="padding:6px 8px;">HBM</th>
    <th style="padding:6px 8px;">BW</th>
    <th style="padding:6px 8px;">TDP</th>
    <th style="padding:6px 8px;">단가</th>
  </tr></thead>
  <tbody>
    {''.join(f'<tr{"" if i%2 else " style=background:#fafafa;"}><td style=padding:5px_8px;font-weight:700;>{name}</td><td style=padding:5px_8px;text-align:right;>{s["tflops_bf16"]:,}</td><td style=padding:5px_8px;text-align:right;>{s["hbm_gb"]:,}GB {s["hbm_type"]}</td><td style=padding:5px_8px;text-align:right;>{s["hbm_bw_tbps"]}TB/s</td><td style=padding:5px_8px;text-align:right;>{s["tdp_w"]:,}W</td><td style=padding:5px_8px;text-align:right;>${s["price_usd"]:,}</td></tr>' for i, (name, s) in enumerate(gpu.items()))}
  </tbody>
</table>

<h3 style="color:#e53e3e; border-bottom:2px solid #e53e3e; padding-bottom:6px; margin-top:20px;">📊 출하량 추이 & 시장 규모</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#fff5f5;">
    <th style="padding:6px 10px;">제품</th>
    <th style="padding:6px 10px;">2024</th>
    <th style="padding:6px 10px;">2025</th>
    <th style="padding:6px 10px;">2026E</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px;">H100 (개)</td>
        <td>{ship["NVIDIA_H100"]["2024"]:,}</td>
        <td>{ship["NVIDIA_H100"]["2025"]:,}</td>
        <td>{ship["NVIDIA_H100"]["2026_est"]:,} ↓ (B200로 대체)</td></tr>
    <tr style="background:#fafafa;"><td style="padding:5px 10px; font-weight:700;">B200 (개)</td>
        <td>{ship["NVIDIA_B200"]["2024"]:,}</td>
        <td>{ship["NVIDIA_B200"]["2025"]:,}</td>
        <td><strong>{ship["NVIDIA_B200"]["2026_est"]:,}</strong> (주력)</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700;">GB200 NVL72 (랙)</td>
        <td>{ship["NVIDIA_GB200_NVL72"]["2025"]:,}</td>
        <td>{ship["NVIDIA_GB200_NVL72"]["2025"]:,}</td>
        <td><strong>{ship["NVIDIA_GB200_NVL72"]["2026_est"]:,}</strong> 랙 ($3M/랙)</td></tr>
    <tr style="background:#fafafa;"><td style="padding:5px 10px;">AMD MI300X (개)</td>
        <td>{ship["AMD_MI300X"]["2024"]:,}</td>
        <td>{ship["AMD_MI300X"]["2025"]:,}</td>
        <td>{ship["AMD_MI300X"]["2026_est"]:,}</td></tr>
  </tbody>
</table>
<p>NVIDIA 데이터센터 매출: FY2024 $47.5B → FY2025E ~$130B → FY2026E ~$180B</p>

<h3 style="color:#e53e3e; border-bottom:2px solid #e53e3e; padding-bottom:6px; margin-top:20px;">🏭 NVIDIA 공급망 구조</h3>
{_scm_table_html(rel_nv["supplies_to"][:8], "NVIDIA → 공급처 (판매/투자)")}
<div style="margin-top:12px;">
{_scm_table_html([
    ("TSMC",     "hardware_supply", "4nm N4 칩 제조 + CoWoS 패키징 독점",    "독점"),
    ("SK Hynix", "hardware_supply", "HBM3e 50%+ 독점 공급 (H200/B200)",      "독점적"),
    ("Samsung",  "hardware_supply", "HBM3 공급, HBM3e 재인증 후 재개",        "미공개"),
    ("Micron",   "hardware_supply", "HBM3e 10% 공급",                         "~10%"),
    ("Broadcom", "hardware_supply", "ConnectX NIC / InfiniBand 스위치",       "미공개"),
], "↑ NVIDIA에 공급하는 기업들")}
</div>

<h3 style="color:#e53e3e; border-bottom:2px solid #e53e3e; padding-bottom:6px; margin-top:20px;">💡 비즈니스 모델 핵심</h3>
<div style="background:#fff5f5; border-radius:6px; padding:12px 16px; font-size:13px; line-height:2;">
<strong>NVIDIA의 3단 수익 구조:</strong><br>
① GPU 하드웨어 (B200 $40K, NVL72 $3M) — 매출의 ~75%<br>
② CUDA 소프트웨어 생태계 — 사실상 락인(Lock-in). PyTorch/TensorFlow 모두 CUDA 최적화<br>
③ Networking (InfiniBand, NVLink Switch) — GPU 간 연결 독점<br>
<br>
<strong>AMD 경쟁 현황:</strong> MI300X $20K로 가격 경쟁력 있으나 CUDA 생태계 장벽 유지.
OpenAI ROCm 지원 합의(6GW)로 AMD 점유율 확대 중. 2026년 AMD 시장점유율 ~18% 예상.
</div>

<h3 style="color:#e53e3e; border-bottom:2px solid #e53e3e; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>CUDA 락인:</strong> GPU 교체 시 소프트웨어 재최적화 비용 강조 → NVIDIA 계속 유리.</li>
  <li><strong>NVL72 ROI:</strong> 랙 $3M이지만 72 GPU 통합으로 랙당 TCO 절감 + 운영 단순화.</li>
  <li><strong>AMD 포지셔닝:</strong> 가격 민감 고객 (특히 추론 워크로드) → MI300X 대안 제시 가능.</li>
  <li><strong>CoWoS 제약:</strong> B200/GB200 공급 상한 = TSMC CoWoS 캐파. 재고 확보가 경쟁력.</li>
</ul>
"""


def _content_hyperscaler() -> str:
    return f"""
<h3 style="color:#38a169; border-bottom:2px solid #38a169; padding-bottom:6px;">📊 하이퍼스케일러 CapEx 추이 ({AS_OF})</h3>
{_capex_bar_html()}
<p style="margin-top:12px; font-size:13px; color:#718096;">
  * 2026E: 각사 가이던스 기준. 실제 집행은 공급 병목에 따라 변동 가능.
</p>

<h3 style="color:#38a169; border-bottom:2px solid #38a169; padding-bottom:6px; margin-top:20px;">🏭 CapEx의 구성과 흐름</h3>
<div style="background:#f0fff4; border-radius:6px; padding:12px 16px; font-size:13px; line-height:2;">
하이퍼스케일러 CapEx $1 지출 시 수혜 흐름:<br>
→ AI 칩: NVIDIA(GPU $40K~) / AMD(MI300X $20K~) / 내부 ASIC<br>
→ 패키징: TSMC CoWoS (GPU당 $500~1,000 추가)<br>
→ HBM: SK Hynix/Samsung/Micron (GB 당 $18)<br>
→ 서버: Dell, HPE, Super Micro<br>
→ 네트워킹: Broadcom, Arista, Mellanox<br>
→ 전력/냉각: Vertiv, Eaton, Schneider<br>
→ DC 부지·건설: Equinix, Digital Realty, 자체 건설
</div>

<h3 style="color:#38a169; border-bottom:2px solid #38a169; padding-bottom:6px; margin-top:20px;">🔍 각사 AI 전략 차별점</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#f0fff4;">
    <th style="padding:6px 10px;">기업</th>
    <th style="padding:6px 10px;">AI 전략</th>
    <th style="padding:6px 10px;">2026E CapEx</th>
    <th style="padding:6px 10px;">주요 투자처</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px; font-weight:700; color:#00a1f1;">Microsoft</td>
        <td>OpenAI 독점 파트너십, Azure AI 플랫폼</td>
        <td>${config.HYPERSCALER_CAPEX["Microsoft"]["2026"]}B</td>
        <td>OpenAI $13B+, GB200 대규모 배포</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700; color:#ff9900;">Amazon</td>
        <td>Trainium2 ASIC 내재화, Anthropic 파트너</td>
        <td>${config.HYPERSCALER_CAPEX["Amazon"]["2026"]}B</td>
        <td>Anthropic $4B, AWS Trainium2 증설</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700; color:#4285f4;">Google</td>
        <td>TPU v5 자체 ASIC, Gemini 생태계</td>
        <td>${config.HYPERSCALER_CAPEX["Google"]["2026"]}B</td>
        <td>Anthropic $2B, TPUv6 개발</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700; color:#1877f2;">Meta</td>
        <td>Llama OSS, MTIA ASIC, Superintelligence 팀</td>
        <td>${config.HYPERSCALER_CAPEX["Meta"]["2026"]}B</td>
        <td>B200 10만개+, MTIA v3 개발</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700; color:#1da1f2;">xAI</td>
        <td>Colossus 클러스터, Grok 모델</td>
        <td>${config.HYPERSCALER_CAPEX["xAI"]["2026"]}B</td>
        <td>H100/B200 10만개+ Memphis 클러스터</td></tr>
  </tbody>
</table>

<h3 style="color:#38a169; border-bottom:2px solid #38a169; padding-bottom:6px; margin-top:20px;">💡 ASIC 내재화 트렌드</h3>
<p>하이퍼스케일러는 특정 워크로드에서 NVIDIA GPU를 자체 ASIC으로 대체 중:</p>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  {''.join(f'<tr{"" if i%2 else " style=background:#f0fff4;"}><td style=padding:5px_10px;font-weight:700;>{co}</td><td style=padding:5px_10px;>{asic}</td><td style=padding:5px_10px;>{detail}</td></tr>' for i, (co, asic, detail) in enumerate([
    ("Google", "TPU v5p/v5e", "100+ ExaFLOPS 배포. 학습 워크로드 ~40% 자체 처리"),
    ("Amazon", "Trainium2", "2x perf/cost vs H100. AWS 자체 학습 70%+ 전환 목표"),
    ("Microsoft", "Maia 100", "Azure LLM 학습 전용. OpenAI 협력 개발"),
    ("Meta", "MTIA v2→v3", "추천시스템 추론 전용. 2027년 추론 50% 자체화 목표"),
  ]))}
</table>
<p>영향: NVIDIA 장기 수요에 압력 요인. 단, 신규 frontier 모델 학습은 여전히 NVIDIA 지배.</p>

<h3 style="color:#38a169; border-bottom:2px solid #38a169; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>수요 가시성:</strong> CapEx 가이던스는 1~2년 선행 지표 → 공급망 발주 근거로 활용.</li>
  <li><strong>ASIC 위협 한계:</strong> 커스텀 ASIC은 특정 워크로드 한정. Frontier 모델엔 여전히 NVIDIA 필요.</li>
  <li><strong>xAI 변수:</strong> Elon Musk의 xAI는 가장 빠른 CapEx 성장률 (+100% YoY). 비상장 리스크.</li>
  <li><strong>공급 제약 주지:</strong> CapEx 계획이 있어도 CoWoS/변압기 병목으로 집행이 지연되는 사례 多.</li>
</ul>
"""


def _content_networking() -> str:
    return f"""
<h3 style="color:#dd6b20; border-bottom:2px solid #dd6b20; padding-bottom:6px;">⚙️ AI 클러스터 네트워킹 구조</h3>
<p>AI 클러스터 네트워킹은 두 가지 축으로 구성됩니다:</p>
<div style="background:#fffaf0; border-radius:6px; padding:12px 16px; font-size:13px; line-height:2;">
<strong>Scale-Up (클러스터 내부):</strong> GPU ↔ GPU 고속 연결<br>
&nbsp;&nbsp;→ NVLink (NVIDIA 독점): GB200 NVL72 = 72 GPU 완전 연결, 1.8TB/s/GPU<br>
&nbsp;&nbsp;→ AMD XGMI: MI300X 8 GPU = 3.2TB/s<br>
<br>
<strong>Scale-Out (클러스터 간 연결):</strong> 랙 ↔ 랙, DC ↔ DC<br>
&nbsp;&nbsp;→ InfiniBand (NDR 400Gbps → XDR 800Gbps 전환 중) — NVIDIA Mellanox<br>
&nbsp;&nbsp;→ Ultra Ethernet (UEC): Google/Meta/Microsoft 주도 — Broadcom, Arista, Cisco<br>
</div>

<h3 style="color:#dd6b20; border-bottom:2px solid #dd6b20; padding-bottom:6px; margin-top:20px;">📊 기술 스펙 비교</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#fffaf0;">
    <th style="padding:6px 10px;">기술</th>
    <th style="padding:6px 10px;">대역폭</th>
    <th style="padding:6px 10px;">지연시간</th>
    <th style="padding:6px 10px;">주요 채택</th>
    <th style="padding:6px 10px;">공급사</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px; font-weight:700;">NVLink 4.0</td>
        <td>1.8 TB/s/GPU</td><td>~μs</td>
        <td>GB200 NVL72 (72GPU 내부)</td>
        <td>NVIDIA Mellanox</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700;">InfiniBand NDR</td>
        <td>400 Gbps/포트</td><td>~1μs</td>
        <td>xAI Colossus, CoreWeave</td>
        <td>NVIDIA Mellanox</td></tr>
    <tr><td style="padding:5px 10px;">InfiniBand XDR</td>
        <td>800 Gbps/포트</td><td>~1μs</td>
        <td>2026~2027 도입 중</td>
        <td>NVIDIA Mellanox</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px;">Ethernet 400G</td>
        <td>400 Gbps</td><td>~10μs</td>
        <td>Google, Meta, AWS</td>
        <td>Broadcom, Arista, Cisco</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700;">Ultra Ethernet (UEC)</td>
        <td>400G~800G</td><td>목표 ~2μs</td>
        <td>2026년 본격 배포 시작</td>
        <td>Broadcom, Arista</td></tr>
  </tbody>
</table>
<p>네트워킹 가동률: {_util_bar("Networking")} — NVL72 급증으로 InfiniBand 수요 +20%/year</p>

<h3 style="color:#dd6b20; border-bottom:2px solid #dd6b20; padding-bottom:6px; margin-top:20px;">🏭 핵심 기업 포지셔닝</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#fffaf0;">
    <th style="padding:6px 10px;">기업</th>
    <th style="padding:6px 10px;">핵심 제품</th>
    <th style="padding:6px 10px;">고객</th>
    <th style="padding:6px 10px;">AI 매출 비중</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px; font-weight:700;">Broadcom</td>
        <td>커스텀 AI ASIC, Tomahawk 이더넷 스위치</td>
        <td>Google(TPU), Meta(MTIA), Apple</td>
        <td>AI ASIC $12B+ (2025), 성장 중</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700;">NVIDIA Mellanox</td>
        <td>InfiniBand NDR/XDR, ConnectX NIC</td>
        <td>전체 AI 클러스터</td>
        <td>NV 매출의 ~5%, 고수익</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700;">Arista Networks</td>
        <td>800G AI 이더넷 스위치</td>
        <td>Meta, Microsoft, Google</td>
        <td>AI 매출 비중 40%+ (2026E)</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px;">Marvell</td>
        <td>커스텀 AI NIC, 광트랜시버 DSP</td>
        <td>Amazon Trainium 네트워크</td>
        <td>AI 매출 $3B+ (2026E)</td></tr>
  </tbody>
</table>

<h3 style="color:#dd6b20; border-bottom:2px solid #dd6b20; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>InfiniBand vs Ethernet:</strong> IB는 저지연·고신뢰, Ethernet은 저가·범용. 고객 워크로드에 맞춰 제시.</li>
  <li><strong>Broadcom ASIC 기회:</strong> 하이퍼스케일러의 커스텀 AI칩 수요 = Broadcom에 멀티년 수주 가시성.</li>
  <li><strong>UEC 전환 타이밍:</strong> 2026년부터 Ultra Ethernet이 InfiniBand 대안으로 부상 → Arista, Cisco 수혜.</li>
  <li><strong>네트워킹 = 숨겨진 병목:</strong> 클러스터 확장 시 GPU 뿐 아니라 스위치·NIC도 리드타임 12~16주.</li>
</ul>
"""


def _content_sovereign() -> str:
    sv   = config.SOVEREIGN_AI
    return f"""
<h3 style="color:#805ad5; border-bottom:2px solid #805ad5; padding-bottom:6px;">🌍 Sovereign AI 개요</h3>
<p>각국 정부가 AI 인프라를 자국 통제 하에 구축하는 흐름입니다.
배경: ① AI = 국가 안보 자산 ② 데이터 주권 ③ 미국 수출 통제(BIS) 회피
④ 경제 주권 (AI 서비스 수익을 자국에서 창출)</p>

<h3 style="color:#805ad5; border-bottom:2px solid #805ad5; padding-bottom:6px; margin-top:20px;">📊 국가별 AI 투자 현황</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#faf5ff;">
    <th style="padding:6px 10px;">국가</th>
    <th style="padding:6px 10px;">투자 규모</th>
    <th style="padding:6px 10px;">타임라인</th>
    <th style="padding:6px 10px;">파트너</th>
    <th style="padding:6px 10px;">GPU 수요 추정</th>
  </tr></thead>
  <tbody>
    {''.join(f'<tr{"" if i%2 else " style=background:#faf5ff;"}><td style=padding:5px_10px;font-weight:700;>{co}</td><td style=padding:5px_10px;>${d["investment_usd_bn"]}B</td><td style=padding:5px_10px;>{d["timeline"]}</td><td style=padding:5px_10px;>{", ".join(d["partners"][:2])}</td><td style=padding:5px_10px;font-weight:700;>{d["gpu_demand_est_units"]:,}개</td></tr>' for i, (co, d) in enumerate(sv.items()))}
  </tbody>
</table>
<p>합산 추가 GPU 수요: <strong>~150,000개</strong> (글로벌 수요의 15~20% 추가 요인)</p>

<h3 style="color:#805ad5; border-bottom:2px solid #805ad5; padding-bottom:6px; margin-top:20px;">🚫 미국 수출 통제 (BIS AI Diffusion Rule)</h3>
<p>2025년 1월 발효된 BIS(Bureau of Industry and Security) 규정:
AI 칩·모델 가중치의 수출을 국가별 3단계 Tier로 관리합니다.</p>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#faf5ff;">
    <th style="padding:6px 10px;">Tier</th>
    <th style="padding:6px 10px;">대상국</th>
    <th style="padding:6px 10px;">조건</th>
    <th style="padding:6px 10px;">주요 예시</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px; font-weight:700; color:#38a169;">Tier 1</td>
        <td>18개 동맹국</td>
        <td>무제한 수출</td>
        <td>한국, 일본, 영국, 호주, 독일</td></tr>
    <tr style="background:#faf5ff;"><td style="padding:5px 10px; font-weight:700; color:#d69e2e;">Tier 2</td>
        <td>~120개국</td>
        <td>총량 제한 + 협약 필요</td>
        <td>UAE, 사우디, 인도, 브라질</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700; color:#e53e3e;">Tier 3</td>
        <td>제한국</td>
        <td>사실상 금지</td>
        <td>중국, 러시아, 이란, 북한</td></tr>
  </tbody>
</table>
<p><strong>UAE 특례:</strong> G42-Microsoft 파트너십을 통해 Tier 2임에도 NVIDIA 칩 대규모 도입 협의 중.
<strong>한국:</strong> Tier 1 → 자유롭게 도입 가능. SK Hynix의 중국 수출은 HBM에 한해 별도 규제.</p>

<h3 style="color:#805ad5; border-bottom:2px solid #805ad5; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>수요 추가성:</strong> Sovereign AI는 기존 하이퍼스케일러 수요에 추가되는 신규 수요층.</li>
  <li><strong>수출 통제 컨설팅:</strong> BIS Tier 2 국가 고객에게 규정 준수 + 조달 경로 안내가 차별화 포인트.</li>
  <li><strong>한국 포지셔닝:</strong> Tier 1 위치 + SK Hynix/Samsung 로컬 제조 → 공급 안정성 강점.</li>
  <li><strong>장기 수요:</strong> 각국 정부 AI 투자는 3~5년 멀티년 계약 → 예측 가능한 장기 수요원.</li>
</ul>
"""


def _content_investment() -> str:
    ph   = config.INVESTMENT_PHASES
    util = config.CURRENT_CAPACITY_UTILIZATION
    return f"""
<h3 style="color:#2d3748; border-bottom:2px solid #2d3748; padding-bottom:6px;">📈 AI 공급망 투자 Phase 구조</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#edf2f7;">
    <th style="padding:6px 10px;">Phase</th>
    <th style="padding:6px 10px;">테마</th>
    <th style="padding:6px 10px;">기간</th>
    <th style="padding:6px 10px;">핵심 기업</th>
    <th style="padding:6px 10px;">상태</th>
  </tr></thead>
  <tbody>
    {''.join(f'<tr{"" if i%2 else " style=background:#f7f8fa;"}><td style=padding:5px_10px;font-weight:700;>Phase {i+1}</td><td style=padding:5px_10px;><strong>{p["focus"]}</strong></td><td style=padding:5px_10px;>{p["timeframe"]}</td><td style=padding:5px_10px;>{", ".join(p["key_players"])}</td><td style=padding:5px_10px;color:#38a169;>{p["status"]}</td></tr>' for i, p in enumerate(ph.values()))}
  </tbody>
</table>
<p><strong>현재 (2026년 Q1):</strong> Phase 2→3 전환기. HBM 업사이클 지속하면서 전력 인프라 병목이 Phase 3의 핵심 테마로 부상.</p>

<h3 style="color:#2d3748; border-bottom:2px solid #2d3748; padding-bottom:6px; margin-top:20px;">🚨 현재 가동률 & 병목 맵</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#edf2f7;">
    <th style="padding:6px 10px;">레이어</th>
    <th style="padding:6px 10px;">가동률</th>
    <th style="padding:6px 10px;">병목 등급</th>
    <th style="padding:6px 10px;">주요 수혜 기업</th>
  </tr></thead>
  <tbody>
    {''.join(f'<tr{"" if i%2 else " style=background:#f7f8fa;"}><td style=padding:5px_10px;font-weight:700;>{layer}</td><td style=padding:5px_10px;>{_util_bar(key)}</td><td style=padding:5px_10px;color:{"#e53e3e" if util[key]>=0.85 else "#d69e2e" if util[key]>=0.70 else "#38a169"};><strong>{"🔴 Critical" if util[key]>=0.85 else "🟡 High" if util[key]>=0.70 else "🟢 Medium"}</strong></td><td style=padding:5px_10px;font-size:12px;>{bene}</td></tr>' for i, (key, layer, bene) in enumerate([
        ("HBM","HBM","SK Hynix, Micron"),
        ("CoWoS","CoWoS 패키징","TSMC (독점)"),
        ("Power_DC","전력 인프라","Vertiv, GE Vernova, Eaton"),
        ("GPU","GPU","NVIDIA (B200), AMD (MI300X)"),
        ("Networking","Networking","Broadcom, Arista"),
        ("Foundry","Foundry","TSMC, Samsung Foundry"),
    ]))}
  </tbody>
</table>

<h3 style="color:#2d3748; border-bottom:2px solid #2d3748; padding-bottom:6px; margin-top:20px;">💰 투자 시그널 요약 ({AS_OF})</h3>
<table style="border-collapse:collapse; width:100%; font-size:13px; margin:10px 0;">
  <thead><tr style="background:#edf2f7;">
    <th style="padding:6px 10px;">기업</th>
    <th style="padding:6px 10px;">시그널</th>
    <th style="padding:6px 10px;">thesis</th>
    <th style="padding:6px 10px;">리스크</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:5px 10px; font-weight:700;">SK Hynix</td>
        <td style="color:#38a169; font-weight:700;">Strong Buy</td>
        <td>HBM3e 독점 + HBM4 로드맵 선두</td>
        <td>Samsung 재인증, 수요 둔화</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700;">TSMC</td>
        <td style="color:#38a169; font-weight:700;">Strong Buy</td>
        <td>CoWoS 독점 + 첨단 파운드리 지배</td>
        <td>지정학 리스크 (대만 해협)</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700;">Vertiv</td>
        <td style="color:#38a169; font-weight:700;">Buy</td>
        <td>DC 전력/냉각 필수 인프라</td>
        <td>경쟁사 진입, 금리 민감</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700;">Broadcom</td>
        <td style="color:#38a169; font-weight:700;">Buy</td>
        <td>AI ASIC 커스텀 설계 독점</td>
        <td>고객 내재화 시 의존도 축소</td></tr>
    <tr><td style="padding:5px 10px; font-weight:700;">GE Vernova</td>
        <td style="color:#d69e2e; font-weight:700;">Accumulate</td>
        <td>변압기 30개월 리드타임 수혜</td>
        <td>에너지 전환 속도 변수</td></tr>
    <tr style="background:#f7f8fa;"><td style="padding:5px 10px; font-weight:700;">NVIDIA</td>
        <td style="color:#38a169; font-weight:700;">Buy (hold)</td>
        <td>CUDA 락인 + 데이터센터 독점</td>
        <td>AMD 추격, 하이퍼스케일러 ASIC</td></tr>
  </tbody>
</table>

<h3 style="color:#2d3748; border-bottom:2px solid #2d3748; padding-bottom:6px; margin-top:20px;">🎯 마케터 핵심 포인트</h3>
<ul style="font-size:13px; line-height:2; color:#2d3748;">
  <li><strong>병목 = 기회:</strong> 가동률 85%+ 레이어가 투자 수익률 최고. HBM/CoWoS/전력 인프라.</li>
  <li><strong>Phase 전환 선행:</strong> 현재 투자자들은 이미 Phase 3(전력)을 매수. Phase 4(Edge) 준비 시작.</li>
  <li><strong>공급망 지도:</strong> COMPANY_RELATIONSHIPS 데이터 활용 → 어떤 기업이 병목 레이어에 노출되어 있는지 파악.</li>
  <li><strong>시나리오 분석:</strong> Bear(성장률 ×0.7)/Base(×1.0)/Bull(×1.5) → 가동률 변화로 투자 타이밍 결정.</li>
</ul>
"""


TOPIC_CONTENT_FN = {
    "hbm_deep_dive":       _content_hbm,
    "cowos_packaging":      _content_cowos,
    "power_infrastructure": _content_power,
    "nvidia_supply_chain":  _content_nvidia,
    "hyperscaler_capex":    _content_hyperscaler,
    "ai_networking":        _content_networking,
    "sovereign_ai":         _content_sovereign,
    "investment_framework": _content_investment,
}


# ============================================================
# 라운드별 심화 콘텐츠 추가 섹션
# ============================================================
ROUND_EXTRA = {
    # Lv.2 심화: 각 주제별 "더 깊이" 섹션
    2: {
        "hbm_deep_dive": """
<h3 style="border-left:4px solid #3182ce;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — 정량 모델 & 수급 메커니즘</h3>
<p><strong>HBM 수요 예측 모델:</strong></p>
<div style="background:#ebf8ff;border-radius:6px;padding:12px 16px;font-family:monospace;font-size:13px;line-height:2;">
Bear 시나리오 (×0.7): HBM 시장 $55B × 0.7 = $38.5B (2026E)<br>
Base 시나리오 (×1.0): HBM 시장 $55B (가이던스 중간값)<br>
Bull 시나리오 (×1.5): HBM 시장 $55B × 1.5 = $82.5B (GB300 조기 ramp)<br>
<br>
SK Hynix HBM4 ASP 프리미엄 효과:<br>
HBM3e $18/GB → HBM4 $25/GB (+39%) × 2026 H2 물량 비중 20%<br>
→ 평균 ASP $19.4/GB → 매출 레버리지 +7.8%
</div>
<p style="margin-top:12px;"><strong>CoWoS Yield가 HBM 공급에 미치는 영향:</strong><br>
CoWoS yield 78% 가정 시, 웨이퍼 120K wpm × 0.78 = 93,600 장 유효 생산.<br>
B200 1개 = 8 HBM3e 스택 = CoWoS 면적 약 600mm² × 8 소모.<br>
→ 120K wpm 기준 연간 B200 환산 최대 <strong>~500만 개</strong> 공급 상한.</p>
<p><strong>Samsung 재진입 시나리오:</strong> 2026년 35% 점유 회복 시<br>
SK Hynix 점유 50%→46% → ASP 압력 -5~8% 예상. 단, 수요 자체가 2.5x 성장하므로 절대 매출은 증가.</p>""",

        "cowos_packaging": """
<h3 style="border-left:4px solid #d69e2e;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — 수율·비용·경쟁 구조</h3>
<p><strong>CoWoS 웨이퍼 단가 분해:</strong></p>
<div style="background:#fefcbf;border-radius:6px;padding:12px 16px;font-size:13px;line-height:2;">
기본 웨이퍼 처리비: ~$3,000/wfr (N4 기준)<br>
실리콘 인터포저 추가: ~$8,000~12,000/wfr<br>
HBM 본딩 + 검사: ~$5,000~8,000/wfr<br>
<strong>총합: ~$20,000~30,000/wfr</strong> (일반 OSAT 대비 20~60배)<br>
<br>
GB200 NVL72 랙 패키징 비용 추산:<br>
B200 72개 × CoWoS ~$1,000/die = $72,000 (랙 $3M 중 2.4%)
</div>
<p style="margin-top:12px;"><strong>TSMC 독점 리스크 분산 시도:</strong><br>
Samsung FoCoS(Fan-out CoS): 비용 20% 저렴하나 HBM 연결 대역폭 열위.<br>
Intel EMIB: 자사 GPU(Gaudi)에만 적용. 외부 판매 없음.<br>
→ 2026~2027년간 실질적 대안 없음. TSMC 독점 지속.</p>""",

        "power_infrastructure": """
<h3 style="border-left:4px solid #718096;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — 전력 수요 정량화</h3>
<div style="background:#edf2f7;border-radius:6px;padding:12px 16px;font-family:monospace;font-size:13px;line-height:2;">
power_MW = GPU_count × TDP_W × server_overhead(1.3) × PUE(1.4) / 1,000,000<br>
<br>
GB200 NVL72 40,000 랙 기준 (2026E):<br>
= 40,000랙 × 120,000W × 1.0 / 1,000,000<br>
= <strong>4,800 MW = 4.8 GW</strong> 신규 전력 수요<br>
<br>
미국 평균 전기료 $0.07/kWh 기준:<br>
연간 전기료 = 4,800MW × 8,760h × $0.07 = <strong>$2.94B/년</strong>
</div>
<p style="margin-top:12px;"><strong>변압기 병목 정량화:</strong><br>
대형 변압기(100MVA+) 미국 내 연간 생산 능력: ~600대.<br>
AI DC 신규 수요: 연 800~1,000대 추정.<br>
→ 수요가 생산 능력의 1.3~1.7배 → 구조적 부족 2028년까지 지속 예상.</p>""",

        "nvidia_supply_chain": """
<h3 style="border-left:4px solid #e53e3e;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — NVIDIA 수익 구조 정량 분석</h3>
<div style="background:#fff5f5;border-radius:6px;padding:12px 16px;font-size:13px;line-height:2;">
<strong>GPU ASP 추이:</strong><br>
H100 SXM5: $30,000 | H200 SXM5: $40,000 | B200 SXM6: $40,000~45,000<br>
GB200 NVL72 (72GPU 랙): $3,000,000 → GPU당 환산 $41,667<br>
<br>
<strong>데이터센터 Gross Margin:</strong> ~75%+ (FY2025 기준)<br>
B200 COGS 추정: $10,000~12,000 (TSMC+HBM+패키징+테스트)<br>
→ GPU 1개당 영업이익 ~$28,000~30,000<br>
<br>
<strong>CUDA 락인 가치:</strong><br>
전 세계 AI 모델 학습의 ~90%가 CUDA 기반.<br>
ROCm(AMD) 전환 비용: 엔지니어링 6~18개월 + 성능 튜닝.
</div>""",

        "hyperscaler_capex": """
<h3 style="border-left:4px solid #38a169;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — CapEx ROI & 수익화 분석</h3>
<div style="background:#f0fff4;border-radius:6px;padding:12px 16px;font-size:13px;line-height:2;">
<strong>Microsoft Azure AI CapEx ROI 추산:</strong><br>
투자: $95B (2026E) × AI 비중 60% = $57B AI 투자<br>
AI 클라우드 매출 기여 추정: $40~50B (2026E, Azure AI 성장률 100%+ YoY)<br>
단순 회수 기간: ~1.2~1.4년 (단, 인프라 수명 10년 기준 ROI 양호)<br>
<br>
<strong>ASIC vs GPU 경제성:</strong><br>
Google TPU v5p: NVIDIA H100 대비 학습 처리량 2x, 비용 40% 절감 추정<br>
→ 특정 워크로드에서 ASIC이 GPU 대체하면 CapEx 절감 + NVIDIA 수요 압박
</div>""",

        "ai_networking": """
<h3 style="border-left:4px solid #dd6b20;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — 네트워킹 비용 & 병목 정량화</h3>
<div style="background:#fffaf0;border-radius:6px;padding:12px 16px;font-size:13px;line-height:2;">
<strong>AI 클러스터 네트워킹 비용 비중:</strong><br>
GPU 서버 1랙 $3M 기준:<br>
- InfiniBand NDR 스위치 + NIC: ~$300,000~400,000 (10~13%)<br>
- 광케이블 + 트랜시버: ~$100,000~200,000 (3~7%)<br>
→ 네트워킹 총 비용: 랙당 $400K~600K (13~20%)<br>
<br>
<strong>InfiniBand vs Ethernet 지연시간 임계점:</strong><br>
LLM 학습 시 All-Reduce 통신: IB 1μs vs ETH 10μs<br>
1만 GPU 클러스터에서 통신 대기 비율: IB ~5% vs ETH ~30%<br>
→ Frontier 모델 학습엔 IB 필수. 추론은 ETH로 충분.
</div>""",

        "sovereign_ai": """
<h3 style="border-left:4px solid #805ad5;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — 수출 통제 & 조달 경로 분석</h3>
<div style="background:#faf5ff;border-radius:6px;padding:12px 16px;font-size:13px;line-height:2;">
<strong>BIS AI Diffusion Rule 핵심 수치 (2025.01 발효):</strong><br>
Tier 2 국가 연간 허용 상한: 총 연산력 기준 ~50,000 H100 등가<br>
UAE 특례 합의: 100만 H100 등가 (G42-Microsoft 협약 통해 특별 승인)<br>
<br>
<strong>중국 우회 경로 차단:</strong><br>
A800/H800(다운그레이드 칩) → 2023.10 추가 제재<br>
Huawei Ascend 910B → 미국 기술 없이 자체 개발, H100 대비 성능 60%<br>
중국 내 AI 학습 병목: HBM 대신 LPDDR5 사용 → 대역폭 6x 열위
</div>""",

        "investment_framework": """
<h3 style="border-left:4px solid #2d3748;padding-left:10px;margin-top:24px;">📐 Lv.2 심화 — 시나리오별 투자 수익률</h3>
<div style="background:#edf2f7;border-radius:6px;padding:12px 16px;font-size:13px;line-height:2;">
<strong>Bear/Base/Bull 시나리오별 HBM 시장 (2027E):</strong><br>
Bear (×0.7): $80B × 0.7 = $56B | SK Hynix 매출 $26B<br>
Base (×1.0): $80B           | SK Hynix 매출 $37B<br>
Bull (×1.5): $80B × 1.5 = $120B | SK Hynix 매출 $56B<br>
<br>
<strong>Phase 3 (Power) 투자 적기 판단 근거:</strong><br>
변압기 수주 → 매출 인식 30개월 지연 → 지금 수주 급증 = 2027~2028 매출 가시성<br>
Vertiv 수주 잔고 2년치 = 향후 2년 매출 확정 → 실적 하방 리스크 낮음
</div>""",
    },

    # Lv.3 전문가: 최신 트렌드 + 투자자 관점
    3: {
        "hbm_deep_dive": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — 기술 로드맵 & 투자 시사점</h3>
<p><strong>HBM4 → HBM4E → HBM5 로드맵 (2026~2029):</strong></p>
<div style="background:#fff5f5;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
HBM4 (2026 H2): 12단 적층, ~12 TB/s, 256GB/GPU. NVIDIA Rubin(2027) 대응.<br>
HBM4E (2027~28): 16단 적층, ~16 TB/s. Logic die 내장(CXL 컨트롤러).<br>
HBM5 (2028~29): 3D Hybrid Bonding 도입, 공정 전환 — TSMC CoWoS-L 필수.<br>
<br>
<strong>투자자 관점 핵심 논거:</strong><br>
① SK Hynix TSV/HBM 특허 300개+ → 기술 해자 2030년까지 유효<br>
② HBM4 ASP $25/GB × 2027E 수요 180GB/GPU × 500만 GPU = $22.5B SK Hynix 단독<br>
③ Samsung HBM4 양산 경쟁 → 2028년 이후 ASP 압박 불가피. 타이밍 중요.
</div>""",

        "cowos_packaging": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — 차세대 패키징 기술 경쟁</h3>
<div style="background:#fefcbf;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
<strong>CoWoS → SoIC(System on Integrated Chips) 전환 로드맵:</strong><br>
2025~2026: CoWoS-L (더 큰 인터포저, Rubin용)<br>
2027~2028: SoIC-X (Face-to-Face 본딩, 3D 적층) — 인터포저 자체를 제거<br>
2029+:     Foveros 경쟁 (Intel), Hybrid Bonding 표준화<br>
<br>
<strong>SoIC 도입 시 공급망 변화:</strong><br>
현재: HBM 제조(SK Hynix) → CoWoS 본딩(TSMC) → GPU 완성<br>
SoIC: GPU 다이 위에 HBM 직접 적층 → 인터포저 면적 50% 축소<br>
→ TSMC 독점 강화 (CoWoS+SoIC 모두 TSMC) / OSAT(ASE, Amkor) 역할 축소
</div>""",

        "power_infrastructure": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — 핵심 기업 심층 분석</h3>
<div style="background:#edf2f7;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
<strong>Vertiv 실적 분해 (2025 추정):</strong><br>
매출 $8B | AI DC 비중 ~55% | 수주 잔고 $7B+ (약 1년치)<br>
Thermal Management(냉각): 마진 30%+ / Power(UPS·PDU): 마진 18%<br>
→ 냉각 사업 확대 = 마진 믹스 개선 + GB200 액냉각 의무화 수혜<br>
<br>
<strong>GE Vernova 변압기 백로그:</strong><br>
2025년 수주 잔고 $22B (전년 대비 +40%). 매출 인식까지 30개월.<br>
→ 2026~2027 매출 가시성 확보 완료. 실적 하방 리스크 매우 낮음.
</div>""",

        "nvidia_supply_chain": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — Blackwell 이후 로드맵 & 리스크</h3>
<div style="background:#fff5f5;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
<strong>Rubin GPU (2027) 공급망 변화:</strong><br>
TSMC N3P 공정 + CoWoS-L(더 큰 인터포저) + HBM4 12단<br>
NVLink 5.0: GPU 간 대역폭 4TB/s (Blackwell 대비 2x)<br>
→ CoWoS-L 캐파 부족 위험 재현 예상. TSMC 2026년부터 CoWoS-L 투자 집중.<br>
<br>
<strong>AMD 추격 시나리오:</strong><br>
MI400(2026E): 384GB HBM3e, ROCm 생태계 개선<br>
OpenAI 6GW 합의 → 실제 배포 시 NVIDIA 점유율 18→25% 압박<br>
<strong>단, CUDA 재작성 비용이 ROI 전환을 막는 핵심 해자.</strong>
</div>""",

        "hyperscaler_capex": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — 수익화 압박 & 구조적 변화</h3>
<div style="background:#f0fff4;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
<strong>AI 수익화 갭 (Sequoia "AI's $600B Question" 업데이트):</strong><br>
2025 AI 인프라 투자: ~$300B | AI 매출: ~$100B → 갭 $200B<br>
2026 AI 인프라 투자: ~$400B | AI 매출: ~$180B → 갭 $220B (확대 중)<br>
→ 하이퍼스케일러는 "손해보며 AI 클라우드 점유율 선점" 전략 유지.<br>
수익화 임계점: 2027~2028년 예상 (추론 워크로드 급증 + API 단가 안정화)<br>
<br>
<strong>AI Agent가 바꾸는 수요 구조:</strong><br>
지금: 주로 학습(Training) 위주 → 앞으로: 추론(Inference) 압도적 성장<br>
추론 최적화 칩(Blackwell 추론 모드, ASIC) 수요 급증 예상 2026~2027
</div>""",

        "ai_networking": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — Ultra Ethernet & 차세대 구조</h3>
<div style="background:#fffaf0;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
<strong>Ultra Ethernet Consortium (UEC) 현황 (2026):</strong><br>
참여사: Microsoft, Google, Meta, AMD, Broadcom, Arista, Cisco<br>
목표: InfiniBand 수준 지연시간(~2μs)을 표준 이더넷으로 달성<br>
UEC 1.0 스펙: 800G, RDMA over Ethernet, 혼잡 제어 강화<br>
→ 채택 시 NVIDIA Mellanox InfiniBand 독점 약화<br>
<br>
<strong>Broadcom 수혜 시나리오:</strong><br>
UEC 성공 = Broadcom Tomahawk 스위치 + NIC 수요 폭증<br>
커스텀 AI ASIC 설계(TPU, MTIA, Trainium) 독점 유지<br>
→ Broadcom은 InfiniBand 패배 시에도 이더넷으로 대체 수혜
</div>""",

        "sovereign_ai": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — 지정학 리스크 & 투자 기회</h3>
<div style="background:#faf5ff;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
<strong>중국 AI 반도체 자립 현황 (2026):</strong><br>
Huawei Ascend 910C: H100 대비 성능 ~80%, 7nm SMIC 생산<br>
연간 생산 능력: ~50만 개 (NVIDIA B200 500만 개 대비 10%)<br>
중국 내 AI DC CapEx: $50~60B (2026E) — 대부분 Huawei로 충당<br>
→ 중국 수요는 NVIDIA에서 이탈 완료. 단, 글로벌 Tier 1 수요는 영향 없음.<br>
<br>
<strong>한국 지정학 포지션 활용:</strong><br>
SK Hynix/Samsung: Tier 1 → HBM 수출 자유<br>
단, 중국향 HBM 수출은 2023.10 이후 미국 압박으로 제한<br>
→ 중국 HBM 대안 없음 = 중국 AI 모델 학습 대역폭 영구 한계
</div>""",

        "investment_framework": """
<h3 style="border-left:4px solid #b31412;padding-left:10px;margin-top:24px;">🔬 Lv.3 전문가 — 포트폴리오 구성 & 리스크 관리</h3>
<div style="background:#edf2f7;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.9;">
<strong>AI SCM 포트폴리오 구성 원칙 (2026 기준):</strong><br>
Core(50%): NVDA, TSM, AVGO — CUDA/CoWoS/ASIC 독점. 변동성 높지만 필수.<br>
Cycle(30%): 000660.KS(SK Hynix), MU — HBM 업사이클. 반도체 사이클 주의.<br>
Infra(20%): VRT, GEV — 전력 인프라. 낮은 밸류에이션 + 멀티년 수주 잔고.<br>
<br>
<strong>핵심 리스크 모니터링 지표:</strong><br>
① TSMC CoWoS 가동률 → 85% 이하로 하락 시 공급 완화 신호<br>
② SK Hynix HBM ASP 전분기 대비 하락 → 경쟁 심화 신호<br>
③ 하이퍼스케일러 CapEx 가이던스 하향 → 전체 공급망 수요 재평가<br>
④ BIS 수출 통제 완화 → 중국 수요 복원 가능성 (반전 트리거)
</div>""",
    },
}


# ============================================================
# Lv.2/3용 컴팩트 핵심 요약 (기초 전체 대신 3~4줄 요약만 표시)
# ============================================================
COMPACT_RECAP = {
    "hbm_deep_dive": [
        "HBM = DRAM 다이 수직 적층 + TSV 연결 → 일반 DDR5 대비 대역폭 14배",
        "B200 GPU 1개에 HBM3e 8스택 × 24GB = 192GB, 8.0 TB/s 탑재",
        "SK Hynix 약 55% 점유. CoWoS 패키징 없이는 HBM 탑재 불가 → TSMC가 공급 상한 결정",
        "2026년 HBM 시장 ~$55B 추정. HBM4 (2026H2) ASP $25/GB → HBM3e 대비 +39%",
    ],
    "cowos_packaging": [
        "CoWoS = GPU 다이 + HBM을 실리콘 인터포저 위에 물리적으로 결합하는 2.5D 패키징",
        "TSMC CoWoS 가동률 92%+, 실질적 대안 없음 (2026 기준) → 병목 레이어",
        "CoWoS-S(표준)/CoWoS-L(대형) → B200은 CoWoS-L 필수. 캐파 2023년 대비 3배 확장",
        "웨이퍼 1장당 CoWoS 비용 $20,000~30,000 (일반 패키징 대비 20~60배)",
    ],
    "power_infrastructure": [
        "GB200 NVL72 랙 1개 = 120kW 소비. AI DC 전력 수요 2024~2027E 4배 증가",
        "4.8GW 신규 AI 전력 수요 = 핵발전소 4기 분량. 미국 전력망 용량 한계",
        "핵심 기업: Vertiv(냉각·전력관리), GE Vernova(변압기), Eaton — 수주 2~3년 선행",
        "변압기 납기 30개월, 연 생산 600대 vs 수요 1,000대 → 구조적 부족 2028E까지",
    ],
    "nvidia_supply_chain": [
        "NVIDIA = 설계만 담당 (팹리스). TSMC N4 생산, CoWoS 패키징, SK Hynix HBM 탑재",
        "B200 ASP $40~45K, COGS $10~12K → GPU 1개당 영업이익 ~$28K~30K",
        "CUDA 생태계 락인: 전 세계 AI 학습의 90%+ CUDA 기반. AMD ROCm 전환 6~18개월 소요",
        "GB200 NVL72 랙 $3M = NVIDIA 매출 집중화. 데이터센터 사업부 Gross Margin 75%+",
    ],
    "hyperscaler_capex": [
        "2026년 하이퍼스케일러 CapEx 합계 $400B+. Microsoft $95B, Google $75B, Amazon $105B",
        "AI 수익화 갭: 투자 $400B vs AI 매출 ~$180B → 2027~2028년 임계점 예상",
        "Azure/AWS/GCP AI 클라우드 추론 수요 급증. 학습(Training) → 추론(Inference)으로 워크로드 이동",
        "ASIC 자체개발(TPU, Trainium, MTIA): 특정 워크로드에서 H100 대비 비용 40% 절감",
    ],
    "ai_networking": [
        "AI 클러스터 = GPU 서버 + InfiniBand 패브릭. 10만 GPU 이상 클러스터에서 통신이 성능 결정",
        "InfiniBand NDR 400G/800G: 지연 ~1μs. AI 학습 All-Reduce 통신 필수. NVIDIA Mellanox 독점",
        "Arista(스위치), Broadcom(ASIC/NIC): 이더넷 인프라. 추론 클러스터는 이더넷으로도 충분",
        "Ultra Ethernet Consortium(UEC): Microsoft, Google, Meta 주도 — IB 대항마 개발 중",
    ],
    "sovereign_ai": [
        "Sovereign AI = 국가가 자국 데이터·AI 인프라를 자체 통제하는 전략",
        "BIS AI Diffusion Rule(2025.01): 국가별 AI 칩 수입 상한. Tier 1(동맹국) vs Tier 2(허가 필요)",
        "중국: Huawei Ascend 910C로 자립 시도. 연 50만 개 생산 능력 (NVIDIA의 10% 수준)",
        "UAE/사우디/인도/유럽 등 Tier 2 국가 AI 투자 $30~50B+ — 공급망에 새 수요층 창출",
    ],
    "investment_framework": [
        "AI 공급망 투자 4단계: Phase1(NVDA·TSMC), Phase2(HBM), Phase3(Power), Phase4(소프트웨어)",
        "선행지표: TSMC CoWoS 가동률·SK Hynix HBM ASP·하이퍼스케일러 CapEx 가이던스",
        "Core(50%): NVDA, TSM, AVGO / Cycle(30%): 000660.KS, MU / Infra(20%): VRT, GEV",
        "Bear 신호: CapEx 가이던스 하향 | Bull 신호: HBM ASP 상승 + CoWoS 풀 가동",
    ],
}

# ============================================================
# 레벨별 Think Questions (이메일 하단 실전 질문)
# ============================================================
LEVEL_QUESTIONS = {
    "hbm_deep_dive": {
        1: [
            "HBM이 일반 GDDR6보다 AI 추론에 유리한 이유를 '대역폭'과 '메모리 벽' 두 단어로 설명해보세요.",
            "SK Hynix가 HBM 시장에서 55% 점유율을 유지하는 핵심 이유 하나는 무엇인가요?",
        ],
        2: [
            "B200 GPU 600만 개 출하 시 발생하는 HBM3e 수요를 GB 단위로 계산하고, 2026년 총 공급량과 비교하세요.",
            "CoWoS yield가 78%→85%로 개선되면 연간 GPU 출하 캐파에 어떤 변화가 생기나요?",
        ],
        3: [
            "Samsung HBM3e NVIDIA 인증 통과 뉴스가 나왔을 때, SK Hynix 단기 주가 영향과 장기 ASP 영향을 Bull/Bear로 각각 시나리오를 작성해보세요.",
            "당신이 SK Hynix 마케터라면 NVIDIA 구매팀에게 HBM4 가격 프리미엄($25/GB)을 정당화하기 위해 어떤 수치와 논리를 사용하겠습니까?",
        ],
    },
    "cowos_packaging": {
        1: [
            "CoWoS가 없으면 왜 AI GPU를 만들 수 없는지, 'GPU 다이'와 'HBM' 두 단어를 사용해 설명해보세요.",
            "TSMC가 CoWoS 시장에서 독점적 지위를 유지하는 이유는 무엇인가요?",
        ],
        2: [
            "CoWoS 캐파 120K wpm이 연간 GPU 출하 상한에 어떻게 연결되는지 계산 과정을 설명해보세요.",
            "Samsung FoCoS가 TSMC CoWoS 대비 20% 저렴하지만 채택되지 않는 기술적 이유는 무엇인가요?",
        ],
        3: [
            "SoIC(System on Integrated Chips) 도입 시 현재 CoWoS 공급망 구조가 어떻게 바뀌는지, OSAT 기업(ASE, Amkor)의 포지션 변화를 포함해 분석해보세요.",
            "TSMC CoWoS 가동률이 85% 이하로 하락하는 시그널을 본다면, 어떤 투자 포지션을 취해야 할까요?",
        ],
    },
    "power_infrastructure": {
        1: [
            "AI 데이터센터가 일반 데이터센터보다 전력을 훨씬 더 많이 소비하는 이유는 무엇인가요?",
            "변압기 납기가 30개월이라는 사실이 AI 인프라 투자자에게 왜 중요한가요?",
        ],
        2: [
            "GB200 NVL72 40,000랙 기준 전력 수요를 MW로 계산하고, 이를 커버하기 위해 필요한 발전 용량과 비교해보세요.",
            "Vertiv의 냉각 사업 마진이 UPS 사업보다 높은 구조적 이유를 설명해보세요.",
        ],
        3: [
            "GE Vernova의 수주 잔고 $22B을 분석해 2026~2028년 매출 가시성과 주가 하방 리스크를 평가해보세요.",
            "핵발전(SMR) + AI DC 조합이 2028년 이후 전력 병목을 해소할 수 있는지 Bull/Bear 시나리오를 작성해보세요.",
        ],
    },
    "nvidia_supply_chain": {
        1: [
            "NVIDIA가 '팹리스' 기업인 이유를 설명하고, 그것이 왜 경쟁 우위가 되는지 설명해보세요.",
            "CUDA 생태계 락인이란 무엇이며, AMD가 이를 뚫기 어려운 이유는?",
        ],
        2: [
            "B200 GPU의 ASP와 COGS를 분석해 NVIDIA 데이터센터 사업부 Gross Margin이 75%+를 유지하는 구조를 설명해보세요.",
            "GB200 NVL72 랙 구조에서 NVIDIA, TSMC, SK Hynix, Vertiv가 각각 어떤 비용을 담당하는지 분해해보세요.",
        ],
        3: [
            "AMD MI400(2026E) 출시 시 NVIDIA 데이터센터 매출에 미칠 영향을 점유율 변화와 ASP 압박 두 가지 관점에서 시나리오를 작성해보세요.",
            "당신이 NVIDIA 반도체 마케터라면 고객사 CTO에게 B200→Rubin 업그레이드 사이클을 어떻게 설득하겠습니까?",
        ],
    },
    "hyperscaler_capex": {
        1: [
            "하이퍼스케일러가 AI CapEx를 $400B 이상 집행하면서도 즉각적인 수익 회수를 기대하지 않는 전략적 이유는?",
            "학습(Training)과 추론(Inference) 워크로드의 차이를 하드웨어 관점에서 설명해보세요.",
        ],
        2: [
            "Microsoft Azure AI $57B 투자에 대한 단순 회수 기간을 계산하고, 이것이 합리적인 투자인지 분석해보세요.",
            "Google TPU v5p가 NVIDIA H100 대비 비용 40% 절감이 가능한 이유와, 그럼에도 GPU 수요가 줄지 않는 이유는?",
        ],
        3: [
            "AI 수익화 갭($400B 투자 vs $180B 매출)이 2027~2028년에 해소될 것이라는 가정의 핵심 드라이버 3가지를 제시하고, 각각의 리스크를 평가해보세요.",
            "AI Agent가 주도하는 추론 중심 컴퓨팅 구조로 전환 시, GPU vs ASIC 수요 비중이 어떻게 바뀌고 어떤 공급망 기업이 수혜/피해를 받을지 분석해보세요.",
        ],
    },
    "ai_networking": {
        1: [
            "AI 클러스터에서 InfiniBand가 필요한 이유를 '통신 지연'과 '학습 효율' 두 관점에서 설명해보세요.",
            "Arista Networks와 Broadcom이 AI 네트워킹 붐에서 수혜를 받는 각각의 이유는?",
        ],
        2: [
            "1만 GPU 클러스터에서 InfiniBand vs Ethernet 선택이 총 학습 시간에 미치는 차이를 계산해보세요 (통신 대기 비율 기준).",
            "AI 학습 클러스터에는 IB가, 추론 클러스터에는 이더넷이 적합한 이유를 기술적으로 설명해보세요.",
        ],
        3: [
            "Ultra Ethernet Consortium(UEC) 성공 시 NVIDIA Mellanox InfiniBand 사업과 Broadcom에게 각각 어떤 영향이 있는지 Bull/Bear로 분석해보세요.",
            "당신 회사가 10만 GPU 클러스터를 구축한다면 InfiniBand vs Ethernet 중 어느 쪽을 선택하고, 그 근거로 어떤 수치를 제시하겠습니까?",
        ],
    },
    "sovereign_ai": {
        1: [
            "Sovereign AI가 단순한 기술 투자가 아닌 '국가 안보' 문제로 다뤄지는 이유는 무엇인가요?",
            "BIS AI Diffusion Rule에서 Tier 1과 Tier 2 국가의 차이는 무엇이며, 한국은 어떤 위치인가요?",
        ],
        2: [
            "중국이 Huawei Ascend 910C로 H100 대비 성능 80%를 달성하면서도 HBM 없이 AI 대역폭 제약이 생기는 이유를 설명해보세요.",
            "UAE의 1백만 H100 특례 합의가 G42-Microsoft 거래와 어떻게 연결되며, 이것이 BIS 규칙 내에서 가능한 이유는?",
        ],
        3: [
            "사우디아라비아, 인도, EU 중 AI 인프라 투자 ROI가 가장 높을 국가를 선정하고, 공급망 수혜 기업과 함께 투자 thesis를 작성해보세요.",
            "당신이 SK Hynix의 Sovereign AI 마케팅 담당자라면 중동 국부펀드 CIO에게 HBM 기반 AI 인프라 투자의 전략적 가치를 어떻게 제안하겠습니까?",
        ],
    },
    "investment_framework": {
        1: [
            "AI 공급망 투자 4단계 Phase 중 현재(2026년 4월) 시장이 어느 Phase에 있다고 생각하나요? 이유는?",
            "선행지표 3가지(CoWoS 가동률, HBM ASP, CapEx 가이던스)가 왜 주가보다 먼저 움직이는지 설명해보세요.",
        ],
        2: [
            "Bear/Base/Bull 시나리오별 SK Hynix 2027E 예상 매출을 계산하고, 현재 밸류에이션에서 각 시나리오의 주가 함의를 분석해보세요.",
            "Vertiv의 수주 잔고 2년치가 '실적 하방 리스크가 낮다'는 주장의 논리적 근거를 설명해보세요.",
        ],
        3: [
            "2026년 4월 현재 AI 공급망 포트폴리오를 새로 구성한다면 Core/Cycle/Infra 비중을 어떻게 설정하고, 핵심 리스크 헷지는 어떻게 하겠습니까?",
            "AI 공급망 투자에서 가장 간과되고 있지만 중요한 '숨겨진 리스크' 하나를 발굴하고, 이를 모니터링할 수 있는 지표를 제안해보세요.",
        ],
    },
}


def _think_questions_html(topic_id: str, round_: int, color: str) -> str:
    questions = LEVEL_QUESTIONS.get(topic_id, {}).get(round_, [])
    if not questions:
        return ""
    items = "".join(
        f'<li style="margin-bottom:10px; padding:10px 14px; background:#f7fafc; '
        f'border-left:3px solid {color}; border-radius:0 4px 4px 0; font-size:13px; '
        f'line-height:1.7; color:#2d3748;">{q}</li>'
        for q in questions
    )
    level_verb = {1: "확인해보세요", 2: "계산/분석해보세요", 3: "시나리오를 작성해보세요"}[round_]
    return (
        f'<div style="margin-top:28px; margin-bottom:8px;">'
        f'<div style="font-size:12px; font-weight:700; color:#4a5568; '
        f'text-transform:uppercase; letter-spacing:.5px; margin-bottom:10px;">'
        f'💡 이번 학습으로 {level_verb}</div>'
        f'<ul style="padding-left:0; list-style:none; margin:0;">{items}</ul>'
        f'</div>'
    )


def _compact_recap_html(topic_id: str, color: str) -> str:
    """Lv.2/3용 — 기초 전체 대신 핵심 요약만 3~4줄"""
    points = COMPACT_RECAP.get(topic_id, [])
    if not points:
        return ""
    items = "".join(
        f'<li style="margin-bottom:6px; font-size:12px; color:#4a5568; line-height:1.6;">'
        f'<span style="color:{color}; font-weight:700; margin-right:4px;">▪</span>{p}</li>'
        for p in points
    )
    return (
        f'<div style="background:#f7fafc; border:1px solid #e2e8f0; border-radius:6px; '
        f'padding:10px 14px; margin-bottom:20px;">'
        f'<div style="font-size:10px; font-weight:700; color:#718096; '
        f'text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px;">Lv.1 기초 핵심 요약</div>'
        f'<ul style="padding-left:0; list-style:none; margin:0;">{items}</ul>'
        f'</div>'
    )


def _news_html(news: list[dict], round_: int) -> str:
    """레벨별 뉴스 프레이밍 — Lv.1: 소개, Lv.2: 시장 영향, Lv.3: 포지션 시사점"""
    if not news:
        return ""
    angle_label = {
        1: "📰 관련 뉴스",
        2: "📊 시장 영향 분석",
        3: "🎯 투자 시그널",
    }.get(round_, "📰 관련 뉴스")
    def angle_suffix(n: dict) -> str:
        if round_ == 2:
            return f' → {n["impact"]}' if n.get("impact") else ""
        if round_ == 3:
            if n.get("impact"):
                return f' → {n["impact"]} | {n.get("context","")}'
            return f' | {n.get("context","")}' if n.get("context") else ""
        return ""

    max_items = {1: 4, 2: 3, 3: 2}.get(round_, 4)
    items = "".join(
        f'<li style="margin-bottom:10px; font-size:13px;">'
        f'<span style="background:{_cat_color(n.get("category",""))}; color:white; '
        f'font-size:10px; padding:1px 6px; border-radius:3px; margin-right:6px; '
        f'white-space:nowrap;">{n.get("category","")}</span>'
        f'<a href="{n.get("url","#")}" style="color:#2d3748; text-decoration:none;">'
        f'{n["title"]}</a>'
        f'<span style="color:#a0aec0; font-size:11px; display:block; '
        f'margin-left:14px; margin-top:2px;">'
        f'{n.get("source","")} · {n.get("date","")}'
        f'{angle_suffix(n)}</span></li>'
        for n in news[:max_items]
    )
    return (
        f'<div style="margin-bottom:24px;">'
        f'<div style="font-size:12px; font-weight:700; color:#4a5568; '
        f'text-transform:uppercase; letter-spacing:.5px; margin-bottom:10px;">'
        f'{angle_label}</div>'
        f'<ul style="padding-left:0; list-style:none; margin:0;">{items}</ul>'
        f'</div>'
    )


# ============================================================
# 이전 학습 요약 배너
# ============================================================
def _prev_context_html(prev: dict | None) -> str:
    if not prev:
        return ""
    return (
        f'<div style="background:#f0fff4;border-left:4px solid #38a169;'
        f'padding:12px 16px;border-radius:0 6px 6px 0;margin-bottom:24px;">'
        f'<div style="font-size:11px;font-weight:700;color:#276749;'
        f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">'
        f'✅ 지난 학습 ({prev["round_label"]}, {prev["sent_date"]})</div>'
        f'<div style="font-size:13px;color:#2d3748;">{prev["summary"]}</div>'
        f'<div style="font-size:11px;color:#68d391;margin-top:4px;">'
        f'이번에는 한 단계 더 깊이 학습합니다 →</div>'
        f'</div>'
    )


# ============================================================
# 이메일 HTML 빌더
# ============================================================
def build_email_html(topic: dict, news: list[dict]) -> str:
    tid        = topic["id"]
    title      = topic["title"]
    color      = topic["color"]
    round_     = topic.get("round", 1)
    round_meta = topic.get("round_meta", {"label": "Lv.1 기초", "desc": ""})
    topic_num  = topic.get("num", 1)
    total      = topic.get("total", 8)
    prev       = topic.get("prev_context")
    today      = datetime.date.today().strftime("%Y년 %m월 %d일")

    # 라운드별 콘텐츠 구성
    # Lv.1: 기초 본문 전체
    # Lv.2: 핵심 요약(3~4줄) + Lv.2 심화 섹션
    # Lv.3: 핵심 요약(2줄) + Lv.3 전문가 섹션
    if round_ == 1:
        main_content = TOPIC_CONTENT_FN.get(tid, lambda: "<p>콘텐츠 준비 중</p>")()
    else:
        recap = _compact_recap_html(tid, color)
        extra = ROUND_EXTRA.get(round_, {}).get(tid, "<p>심화 콘텐츠 준비 중</p>")
        main_content = recap + f'<div style="font-size:14px;line-height:1.8;color:#2d3748;">{extra}</div>'

    # 레벨별 뉴스
    built_news = _news_html(news, round_)

    # Think Questions
    questions = _think_questions_html(tid, round_, color)

    # 라운드 배지 색상
    badge_color = {"1": "#38a169", "2": "#3182ce", "3": "#b31412"}.get(str(round_), "#4a5568")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:20px 0;background:#f0f2f5;font-family:'Apple SD Gothic Neo',Arial,sans-serif;">
<div style="max-width:700px;margin:0 auto;background:white;border-radius:10px;
            overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.10);">

  <!-- Header -->
  <div style="background:{color};padding:28px 36px 24px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
      <span style="background:{badge_color};color:white;font-size:11px;font-weight:700;
                   padding:3px 10px;border-radius:12px;">{round_meta["label"]}</span>
      <span style="color:rgba(255,255,255,.7);font-size:12px;">
        {today} &nbsp;·&nbsp; {topic_num}/{total}번째 학습
      </span>
    </div>
    <div style="color:white;font-size:24px;font-weight:800;line-height:1.3;">{title}</div>
    <div style="color:rgba(255,255,255,.75);font-size:12px;margin-top:6px;">
      {round_meta["desc"]} &nbsp;·&nbsp; 기준: {AS_OF}
    </div>
  </div>

  <div style="padding:32px 36px;">

    {_prev_context_html(prev)}

    {built_news}

    {main_content}

    {questions}

  </div>

  <div style="background:#f7f8fa;padding:14px 36px;font-size:11px;color:#a0aec0;">
    AI SCM Learning &nbsp;·&nbsp; {today} &nbsp;·&nbsp; {round_meta["label"]} — {round_meta["desc"]}
  </div>
</div>
</body>
</html>"""


def _cat_color(cat: str) -> str:
    return {
        "HBM": "#3182ce", "Packaging": "#d69e2e", "GPU": "#e53e3e",
        "Power": "#718096", "Networking": "#dd6b20", "Hyperscaler": "#38a169",
        "Sovereign AI": "#805ad5",
    }.get(cat, "#4a5568")


# ============================================================
# 발송
# ============================================================
def send_study_email(topic: dict, dry_run: bool = False) -> bool:
    news = get_topic_news(topic["id"], max_items=4)
    html = build_email_html(topic, news)

    topic_num = topic.get("num", 1)
    total     = topic.get("total", 24)
    round_lbl = topic.get("round_meta", {}).get("label", "Lv.1")
    subject = f"[AI SCM] {topic_num}/{total} {round_lbl} — {topic['title']} ({datetime.date.today()})"

    if dry_run:
        import config as cfg
        os.makedirs(cfg.REPORTS_DIR, exist_ok=True)
        out = os.path.join(cfg.REPORTS_DIR, f"study_{topic['id']}_{datetime.date.today()}.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [StudyEmail] dry-run → {out}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = RECIPIENT
        msg.attach(MIMEText(html, "html", "utf-8"))
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, RECIPIENT, msg.as_bytes())
        print(f"  [StudyEmail] ✅ 발송: {subject}")
        return True
    except Exception as e:
        print(f"  [StudyEmail] ❌ 실패: {e}")
        return False
