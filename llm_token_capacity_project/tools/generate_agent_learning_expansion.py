"""Generate expanded learning outputs for assumption agents.

This is a study artifact: it expands each assumption agent's learning scope
with a source-backed curriculum and evidence-promotion tasks.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "outputs" / "reports"
RUN_DATE = "2026-05-18"


SOURCES = [
    ("IEA_KEY_2026", "Key Questions on Energy and AI", "IEA", "2026", "https://www.iea.org/reports/key-questions-on-energy-and-ai", "energy/policy", "A01,A02,A05"),
    ("IEA_ELEC_2026", "Electricity 2026", "IEA", "2026", "https://www.iea.org/reports/electricity-2026", "electricity market baseline", "A01,A02"),
    ("LBNL_DC_2024", "2024 United States Data Center Energy Usage Report", "LBNL / DOE", "2024", "https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report", "data center energy baseline", "A01,A02,A03,A04"),
    ("EPRI_POWERING", "Powering Intelligence", "EPRI", "2024/2026 updated access", "https://www.epri.com/research/products/000000003002028905", "grid and data center energy scenarios", "A01,A02"),
    ("UPTIME_COOLING", "Cooling Systems Survey 2024", "Uptime Institute", "2024", "https://intelligence.uptimeinstitute.com/sites/default/files/2024-05/Uptime%20Institute%20Cooling%20Systems%20Survey%202024_0.pdf", "liquid cooling adoption and constraints", "A03,A04"),
    ("AFCOM_2026_DENSITY", "Rack Density Surges as AI Overhauls Data Center Design", "AFCOM / Data Center Knowledge", "2026", "https://www.datacenterknowledge.com/data-center-construction/afcom-rack-density-and-build-outs-surge-as-ai-overhauls-data-center-design", "operator survey context for density/cooling", "A03,A04"),
    ("IBM_PD_2026", "Revisiting Disaggregated Large Language Model Serving for Performance and Energy Implications", "IBM Research / EuroSys", "2026", "https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications", "prefill-decode disaggregation energy/performance", "A08,A09"),
    ("JOULE_INFERENCE_2026", "Energy use of AI inference, efficiency pathways, and test-time scaling", "Joule / Cell Press", "2026", "https://www.sciencedirect.com/science/article/pii/S2542435126001145", "energy/query, token-length, test-time compute", "A08,A09"),
    ("ARXIV_HETEROGENEOUS_2602", "Large-Scale LLM Inference with Heterogeneous Workloads", "arXiv", "2026", "https://arxiv.org/abs/2602.02987", "prefill-decode contention and control", "A08,A09"),
    ("ARXIV_SLO_PD_2603", "SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM Inference", "arXiv", "2026", "https://arxiv.org/abs/2603.04716", "SLO-aware P/D resource allocation", "A08,A09"),
    ("ARXIV_PREFILL_SERVICE_2604", "Prefill-as-a-Service", "arXiv", "2026", "https://arxiv.org/abs/2604.15039", "cross-datacenter KV cache/prefill scenario", "A08,A09,A10"),
    ("ARXIV_SPEC_DECODE_2605", "An Interpretable Latency Model for Speculative Decoding in LLM Serving", "arXiv", "2026", "https://arxiv.org/abs/2605.15051", "speculative decoding latency model", "A08,A09"),
    ("PAGED_ATTENTION", "Efficient Memory Management for LLM Serving with PagedAttention", "arXiv", "2023", "https://arxiv.org/abs/2309.06180", "KV cache and serving throughput foundation", "A08,A09"),
    ("SPLITWISE", "Splitwise: Efficient generative LLM inference using phase splitting", "arXiv", "2023", "https://arxiv.org/abs/2311.18677", "prefill/decode phase split foundation", "A08,A09"),
    ("DISTSERVE", "DistServe: Disaggregating Prefill and Decoding", "arXiv", "2024", "https://arxiv.org/abs/2401.09670", "TTFT/TPOT and goodput", "A08,A09"),
    ("INFERENCEX", "InferenceX / InferenceMAX", "SemiAnalysis", "accessed 2026-05-18", "https://inferencex.semianalysis.com/", "benchmark/proxy for tokens/MW", "A08,A09"),
    ("NVIDIA_DGX_GB", "NVIDIA DGX GB Rack Scale Systems User Guide", "NVIDIA", "accessed 2026-05-18", "https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html", "rack power/cooling architecture", "A02,A03,A08"),
    ("NVIDIA_GB200", "NVIDIA GB200 NVL72", "NVIDIA", "accessed 2026-05-18", "https://www.nvidia.com/en-us/data-center/gb200-nvl72/", "rack-scale Blackwell system", "A02,A03,A08"),
    ("GOOGLE_IRONWOOD", "Ironwood TPU: age of inference", "Google Cloud", "2025", "https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/", "inference-optimized TPU direction", "A05,A08"),
    ("AWS_RAINIER", "AWS Project Rainier", "Amazon", "2025", "https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster", "Anthropic/AWS Trainium cluster", "A02,A06,A10"),
    ("OPENAI_STARGATE", "Five new Stargate sites", "OpenAI", "2025", "https://openai.com/index/five-new-stargate-sites/", "planned capacity and attribution", "A01,A02,A10"),
    ("DEEPSEEK_V3", "DeepSeek-V3 Technical Report / GitHub", "DeepSeek", "2024", "https://github.com/deepseek-ai/DeepSeek-V3", "MoE total/active parameter anchor", "A07,A08"),
    ("QWEN3", "Qwen3 GitHub", "Alibaba Qwen", "2025", "https://github.com/QwenLM/Qwen3", "MoE active parameter anchor", "A07,A08"),
    ("STANFORD_INDEX_2025", "AI Index Report 2025", "Stanford HAI", "2025", "https://hai.stanford.edu/ai-index/2025-ai-index-report", "macro AI compute/cost context", "A06,A08,A10"),
    ("EPOCH_POWER", "How much power will frontier AI training demand in 2030?", "Epoch AI", "2025", "https://epoch.ai/blog/power-demands-of-frontier-ai-training", "training peak power envelope", "A02,A06"),
    ("EPOCH_GPU_POWER", "GPUs account for about 40% of power usage in AI data centers", "Epoch AI", "2025", "https://epoch.ai/data-insights/gpus-power-usage-in-ai-data-centers", "facility/IT/GPU decomposition", "A03,A04"),
    ("DELOITTE_AI_DC", "AI infrastructure gaps", "Deloitte Insights", "2025", "https://www.deloitte.com/us/en/insights/industry/power-and-utilities/data-center-infrastructure-artificial-intelligence.html", "market context for infra constraints", "A01,A02,A05"),
    ("MCK_POWER_COOL", "Beyond compute: infrastructure that powers and cools AI data centers", "McKinsey", "2025", "https://www.mckinsey.com/industries/industrials-and-electronics/our-insights/beyond-compute-infrastructure-that-powers-and-cools-ai-data-centers", "power/cooling investment context", "A02,A03"),
    ("AI_2027", "AI 2027", "AI Futures Project", "2025", "https://ai-2027.com/", "stress scenario for accelerated adoption", "A05,A06,A08,A09,A10"),
]


AGENT_EXPANSIONS = [
    ("A01", "contracted_power_gw", "planned/contracted/committed/operational capacity language", ["IEA_KEY_2026", "IEA_ELEC_2026", "LBNL_DC_2024", "EPRI_POWERING", "OPENAI_STARGATE", "DELOITTE_AI_DC"], "Separate macro power-demand context from company contracted capacity facts."),
    ("A02", "active_power_gw", "energization, cluster-online evidence, deployment ratio", ["LBNL_DC_2024", "EPRI_POWERING", "NVIDIA_DGX_GB", "AWS_RAINIER", "EPOCH_POWER", "MCK_POWER_COOL"], "Build an operational-deployment scorecard before changing active GW."),
    ("A03", "pue", "cooling architecture, PUE, rack density", ["UPTIME_COOLING", "AFCOM_2026_DENSITY", "NVIDIA_DGX_GB", "NVIDIA_GB200", "EPOCH_GPU_POWER", "MCK_POWER_COOL"], "Keep PUE as facility overhead, not accelerator efficiency."),
    ("A04", "ai_workload_share", "AI cluster share of IT load and overhead decomposition", ["LBNL_DC_2024", "EPOCH_GPU_POWER", "NVIDIA_DGX_GB", "AFCOM_2026_DENSITY"], "Decompose GPU/server/network/storage/control overhead before setting AI workload share."),
    ("A05", "inference_power_share", "commercial inference adoption and inference-oriented hardware", ["GOOGLE_IRONWOOD", "IEA_KEY_2026", "DELOITTE_AI_DC", "AI_2027"], "Keep AI-2027 as stress scenario and not Base inference share."),
    ("A06", "training_power_share", "frontier training reserve and post-training/eval load", ["EPOCH_POWER", "STANFORD_INDEX_2025", "AI_2027", "AWS_RAINIER"], "Separate peak frontier training envelope from annual average training share."),
    ("A07", "active_parameters", "dense/MoE/closed-model active parameter boundaries", ["DEEPSEEK_V3", "QWEN3"], "Use official active params for open MoE, bands only for closed models."),
    ("A08", "tokens_per_second_per_mw", "benchmark/proxy, energy/query, hardware and serving stack", ["INFERENCEX", "JOULE_INFERENCE_2026", "IBM_PD_2026", "PAGED_ATTENTION", "SPLITWISE", "DISTSERVE", "ARXIV_HETEROGENEOUS_2602", "ARXIV_SPEC_DECODE_2605"], "Promote benchmark values only as proxy unless company production telemetry exists."),
    ("A09", "utilization", "average utilization, latency SLO, P/D disaggregation, batching", ["IBM_PD_2026", "ARXIV_SLO_PD_2603", "ARXIV_PREFILL_SERVICE_2604", "ARXIV_HETEROGENEOUS_2602", "PAGED_ATTENTION", "DISTSERVE"], "Separate provisioned inference share from realized average utilization."),
    ("A10", "attribution_rule", "model owner vs host provider vs product owner", ["OPENAI_STARGATE", "AWS_RAINIER", "AI_2027", "STANFORD_INDEX_2025"], "Never double count host capacity and model-owner token generation."),
]


def source_lookup() -> dict[str, tuple[str, str, str, str, str, str, str, str]]:
    return {row[0]: row for row in SOURCES}


def build_markdown() -> str:
    lookup = source_lookup()
    lines = [
        "# Agent Learning Expansion Pack",
        "",
        f"생성일: {RUN_DATE}",
        "",
        "## 목적",
        "",
        "이 산출물은 10개 assumption agent의 학습 범위를 확장하기 위한 운영 자료입니다. 최신 IEA 2026, inference energy, prefill-decode disaggregation, rack-scale power/cooling, benchmark/proxy 자료를 agent별 curriculum으로 매핑합니다.",
        "",
        "## 운영 원칙",
        "",
        "- 새 source는 바로 숫자 모델에 들어가지 않습니다.",
        "- 먼저 agent evidence로 승격하고, Fact/Derived Estimate/Proxy/Scenario를 분류합니다.",
        "- InferenceX, AI 2027, Deloitte, McKinsey 등은 유용하지만 production telemetry가 아닙니다.",
        "- A08/A09는 2026년 serving 논문을 우선 학습하고, benchmark-to-production gap을 명시해야 합니다.",
        "- A01/A02는 2026년 power/grid source를 우선 학습하고, planned와 active를 분리해야 합니다.",
        "",
        "## Agent별 확장 커리큘럼",
        "",
    ]
    for agent_id, field, theme, source_ids, rule in AGENT_EXPANSIONS:
        lines.extend([f"### {agent_id} `{field}`", "", f"**확장 주제:** {theme}", "", f"**핵심 규칙:** {rule}", "", "**읽을 source:**", ""])
        for sid in source_ids:
            _, title, publisher, year, url, purpose, agents = lookup[sid]
            lines.append(f"- **{sid}:** [{title}]({url}) - {publisher}, {year}. 목적: {purpose}.")
        lines.extend(
            [
                "",
                "**Evidence promotion task:**",
                "",
                "1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.",
                "2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.",
                "3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.",
                "4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.",
                "",
            ]
        )

    lines.extend(
        [
            "## Expanded Source Library",
            "",
            "| ID | Source | Publisher | Year | Purpose | Agents | Link |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for sid, title, publisher, year, url, purpose, agents in SOURCES:
        lines.append(f"| {sid} | {title} | {publisher} | {year} | {purpose} | {agents} | {url} |")

    lines.extend(
        [
            "",
            "## 30-Day Agent Learning Sprint",
            "",
            "### Week 1: Power and Deployment",
            "",
            "- A01, A02, A03, A04가 IEA/LBNL/EPRI/Uptime/NVIDIA DGX GB/Epoch GPU power 자료를 읽습니다.",
            "- 산출물: planned vs active capacity scorecard, PUE/context note, AI workload share decomposition.",
            "",
            "### Week 2: Inference Serving Deep Dive",
            "",
            "- A08, A09가 PagedAttention, Splitwise, DistServe, IBM PD 2026, Joule inference energy, InferenceX를 읽습니다.",
            "- 산출물: tokens/MW proxy ladder, utilization caveat sheet, benchmark-to-production gap map.",
            "",
            "### Week 3: Model Architecture and Training Reserve",
            "",
            "- A06, A07가 Epoch/Stanford/DeepSeek/Qwen 자료를 읽습니다.",
            "- 산출물: training reserve interpretation, MoE active parameter source table.",
            "",
            "### Week 4: Scenario and Attribution",
            "",
            "- A05, A10, orchestrator가 AI 2027, OpenAI Stargate, AWS Rainier, market context를 읽습니다.",
            "- 산출물: AI-2027 stress scenario memo, host/model-owner attribution map.",
            "",
            "## Orchestrator Review Output Template",
            "",
            "```text",
            "cycle:",
            "date:",
            "agents_reviewed:",
            "sources_promoted:",
            "fields_changed:",
            "confidence_upgrades:",
            "confidence_downgrades:",
            "base_case_changes:",
            "stress_scenario_changes:",
            "unresolved_flags:",
            "next_cycle:",
            "```",
        ]
    )
    return "\n".join(lines)


def add_para(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    run = p.add_run(text)
    run.font.name = "Apple SD Gothic Neo"
    run.font.size = Pt(10)


def build_docx(markdown: str, path: Path) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    styles = doc.styles
    styles["Normal"].font.name = "Apple SD Gothic Neo"
    styles["Normal"].font.size = Pt(10)
    for style_name in ["Heading 1", "Heading 2", "Heading 3"]:
        styles[style_name].font.name = "Apple SD Gothic Neo"
        styles[style_name].font.color.rgb = RGBColor(15, 23, 42)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Agent Learning Expansion Pack")
    run.bold = True
    run.font.size = Pt(21)
    run.font.name = "Apple SD Gothic Neo"
    run.font.color.rgb = RGBColor(15, 23, 42)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run(f"Assumption agents learning expansion | {RUN_DATE}")

    for line in markdown.splitlines():
        if not line.strip():
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:], level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=2)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:].replace("**", "").replace("`", ""), style="List Bullet")
        else:
            add_para(doc, line.replace("**", "").replace("`", ""))
    doc.save(path)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    md_path = DOCS / "agent_learning_expansion_pack.md"
    # Preserve the manually curated Markdown as the source of truth.
    markdown = md_path.read_text(encoding="utf-8") if md_path.exists() else build_markdown()
    docx_path = OUT / "agent_learning_expansion_pack_kr.docx"
    md_path.write_text(markdown, encoding="utf-8")
    build_docx(markdown, docx_path)
    print({"status": "PASS", "markdown": str(md_path), "docx": str(docx_path)})


if __name__ == "__main__":
    main()
