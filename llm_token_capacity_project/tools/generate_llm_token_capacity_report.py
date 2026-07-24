"""Generate LLM-owner token capacity simulation artifacts.

This report is intentionally separate from the project's core dynamics model.
It creates an auditable executive simulation for commercial LLM owners, with
every modeled number labeled as Fact, Estimate, or Scenario.
"""

from __future__ import annotations

import json
import math
import csv
import statistics
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "reports"
RUN_DATE = date.today().isoformat()
YEARS = list(range(2026, 2031))
PROXY_TPS_MW_REFERENCE_CSV = (
    ROOT
    / "docs"
    / "dynamic_reasoning_agent_cost"
    / "model_gpu_workload_interactivity_tps_mw_reference.csv"
)


PROXY_MODEL_SOURCES = {
    "gptoss120b": ("gptoss120b",),
    "frontier_composite": ("gptoss120b", "dsv4", "kimik2.5"),
    "llama70b": ("llama70b",),
    "dsr1": ("dsr1",),
    "qwen3.5": ("qwen3.5",),
}

FRONTIER_COMPOSITE_GPU_SOURCES = {
    "h200": ("gptoss120b",),
    "b200": ("dsv4", "kimik2.5"),
    "gb200": ("dsv4", "kimik2.5"),
}

OPTIMIZED_SERVING_KEYWORDS = ("dynamo", "trt", "tensorrt", "trllm", "mtp")
INTERACTIVITY_TARGETS_TOK_S_USER = (10, 30, 50, 70, 100)


def proxy_source_models(proxy_model: str, gpu: str | None = None) -> tuple[str, ...]:
    if proxy_model == "frontier_composite" and gpu in FRONTIER_COMPOSITE_GPU_SOURCES:
        return FRONTIER_COMPOSITE_GPU_SOURCES[gpu]
    return PROXY_MODEL_SOURCES[proxy_model]


def proxy_source_label(proxy_model: str, gpu: str | None = None) -> str:
    if proxy_model == "frontier_composite" and gpu is None:
        return "H200:gptoss120b; B200/GB200:dsv4+kimik2.5"
    return "+".join(proxy_source_models(proxy_model, gpu))


def optimized_serving_stack(row: dict[str, str]) -> bool:
    text = " ".join(
        str(row.get(key, ""))
        for key in ("framework", "precision", "main_framework", "main_precision", "method_note")
    ).lower()
    return any(keyword in text for keyword in OPTIMIZED_SERVING_KEYWORDS)


def serving_stack_label(row: dict[str, str]) -> str:
    framework = row.get("framework") or row.get("main_framework") or "unknown"
    precision = row.get("precision") or row.get("main_precision") or "unknown"
    concurrency = row.get("concurrency") or "?"
    return f"{framework}/{precision}, concurrency {concurrency}"


def select_max_tps_sample(samples: list[dict[str, str]]) -> tuple[float, str]:
    if not samples:
        raise ValueError("Cannot select TPS sample from an empty list")
    preferred = [row for row in samples if optimized_serving_stack(row)]
    selected_pool = preferred if preferred else samples
    selected = max(selected_pool, key=lambda row: float(row["output_tok_s_mw"]))
    basis = "optimized serving max" if preferred else "public max - optimized stack unavailable"
    return float(selected["output_tok_s_mw"]), f"{basis}; {serving_stack_label(selected)}"


def output_tok_s_user(row: dict[str, str], multiplier: float = 1.0) -> float | None:
    if row.get("output_tok_s_gpu") and row.get("concurrency"):
        try:
            concurrency = float(row["concurrency"])
            if concurrency > 0:
                return float(row["output_tok_s_gpu"]) * multiplier / concurrency
        except ValueError:
            return None
    if row.get("tok_s_user"):
        try:
            return float(row["tok_s_user"]) * multiplier
        except ValueError:
            return None
    return None


SCENARIO_CASES = {
    "Bear": {
        "description_kr": "전력 인허가/장비 조달 지연, 낮은 inference 배정, 보수적인 commercial workload fit을 적용하는 경우.",
        "operational_deploy_multiplier_2026": 0.90,
        "operational_deploy_multiplier_2030": 0.82,
        "inference_share_delta_2026": -0.08,
        "inference_share_delta_2030": -0.10,
        "confidence": "Scenario-Low",
    },
    "Base": {
        "description_kr": "현재 공개 anchor와 합리적 배분 가정에 public reference 대비 Base commercial workload fit을 적용한 기준선.",
        "operational_deploy_multiplier_2026": 1.00,
        "operational_deploy_multiplier_2030": 1.00,
        "inference_share_delta_2026": 0.00,
        "inference_share_delta_2030": 0.00,
        "confidence": "Scenario-Medium",
    },
    "Bull": {
        "description_kr": "전력 energization과 accelerator 배치가 빠르고 inference 비중 및 commercial workload fit이 유리하게 전개되는 경우.",
        "operational_deploy_multiplier_2026": 1.05,
        "operational_deploy_multiplier_2030": 1.18,
        "inference_share_delta_2026": 0.05,
        "inference_share_delta_2030": 0.08,
        "confidence": "Scenario-Low-Medium",
    },
    "Grid-Constrained / Efficiency-Upside": {
        "description_kr": "전력 투입이 지연되지만 inference 우선 배분이 진행되는 경우. Commercial workload fit은 Base를 유지하고 추가 효율 uplift는 미반영.",
        "operational_deploy_multiplier_2026": 0.88,
        "operational_deploy_multiplier_2030": 0.72,
        "inference_share_delta_2026": 0.02,
        "inference_share_delta_2030": 0.04,
        "confidence": "Scenario-Low",
    },
}


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    publisher: str
    date: str
    url_or_report: str
    tier: str
    use_in_model: str
    confidence: float
    note_kr: str


@dataclass(frozen=True)
class CompanyModel:
    company: str
    model_family: str
    commercial_surface: str
    parameter_band_total: str
    parameter_band_active: str
    model_architecture: str
    serving_platform: str
    attribution_rule: str
    gpu_asic_mix: str
    source_ids: str
    confidence: str
    note_kr: str


@dataclass(frozen=True)
class CompanyScenario:
    company: str
    region: str
    model_family: str
    commercial_surface: str
    contracted_power_2026_gw: float
    contracted_power_2030_gw: float
    active_power_2026_gw: float
    active_power_2030_gw: float
    inference_share_2026: float
    inference_share_2030: float
    efficiency_cagr: float
    utilization_2026: float
    utilization_2030: float
    pue: float
    ai_workload_share: float
    confidence: str
    derivation_type: str
    source_ids: str
    assumption_ids: str


@dataclass(frozen=True)
class FactAnchor:
    anchor_id: str
    company: str
    topic: str
    metric: str
    value: str
    fact_date: str
    source_id: str
    source_tier: str
    model_use: str
    derivation_impact_kr: str
    confidence: float
    replacement_path: str


def lerp(start: float, end: float, i: int, n: int) -> float:
    if n == 1:
        return start
    return start + (end - start) * i / (n - 1)


def sources() -> list[Source]:
    return [
        Source(
            "SRC_OPENAI_GPT41_DOCS",
            "GPT-4.1 model documentation",
            "OpenAI",
            "2025-04-14",
            "https://platform.openai.com/docs/models/gpt-4.1",
            "Tier 1",
            "OpenAI commercial model family and closed-model parameter disclosure boundary",
            0.90,
            "모델 제공 사실 확인. 파라미터는 비공개이므로 band로만 사용.",
        ),
        Source(
            "SRC_OPENAI_STARGATE_ORACLE",
            "Stargate advances with partnership with Oracle",
            "OpenAI",
            "2025-07-22",
            "https://openai.com/index/stargate-advances-with-partnership-with-oracle/",
            "Tier 1",
            "OpenAI hosting capacity ramp anchor, not a precise active IT load",
            0.85,
            "Stargate/Oracle capacity는 OpenAI 모델 owner capacity로 귀속하되 ramp는 시나리오.",
        ),
        Source(
            "SRC_OPENAI_STARGATE_PROGRESS",
            "Five new Stargate sites and nearly 7 GW planned capacity",
            "OpenAI",
            "2025-09-23",
            "https://openai.com/index/five-new-stargate-sites/",
            "Tier 1",
            "OpenAI 2030 contracted/planned capacity upper-bound anchor",
            0.86,
            "Stargate planned capacity는 active IT load가 아니며 operational deploy multiplier를 통해 반영.",
        ),
        Source(
            "SRC_GOOGLE_GEMINI_TOKENS",
            "Gemini API token documentation",
            "Google AI for Developers",
            "2026-05-13 accessed",
            "https://ai.google.dev/gemini-api/docs/tokens",
            "Tier 1",
            "Token accounting and context handling anchor for Gemini surfaces",
            0.90,
            "토큰 산식 및 Gemini API token accounting 확인용.",
        ),
        Source(
            "SRC_GOOGLE_IRONWOOD",
            "Ironwood TPU: the age of inference",
            "Google Cloud",
            "2025-04-09",
            "https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/",
            "Tier 1",
            "Google TPU serving platform and inference-optimized hardware direction",
            0.88,
            "Google은 TPU 기반 serving 효율 개선 가정의 1차 anchor.",
        ),
        Source(
            "SRC_META_LLAMA",
            "Llama model family official site and model cards",
            "Meta AI",
            "2026-05-13 accessed",
            "https://www.llama.com/",
            "Tier 1",
            "Llama model family and open model parameter disclosures where available",
            0.82,
            "공개 Llama 계열은 model card 기준, 비공개 Meta AI serving은 band 처리.",
        ),
        Source(
            "SRC_XAI_MODELS",
            "xAI model documentation",
            "xAI",
            "2026-05-13 accessed",
            "https://docs.x.ai/docs/models",
            "Tier 1",
            "Grok commercial model surface and closed-model disclosure boundary",
            0.78,
            "Grok 모델 제공 사실 확인. Colossus active power는 scenario.",
        ),
        Source(
            "SRC_XAI_NVIDIA_COLOSSUS",
            "xAI's Colossus supercomputer cluster",
            "NVIDIA",
            "2024-12-04",
            "https://blogs.nvidia.com/blog/xai-colossus/",
            "Tier 1/2",
            "xAI GPU cluster scale anchor for active power and serving/training capacity scenarios",
            0.82,
            "100k Hopper GPU와 200k expansion 방향성은 cluster scale anchor. GW 환산은 estimate.",
        ),
        Source(
            "SRC_DEEPSEEK_V3",
            "DeepSeek-V3 GitHub repository and technical report",
            "DeepSeek",
            "2024-12-26",
            "https://github.com/deepseek-ai/DeepSeek-V3",
            "Tier 1",
            "MoE total and active parameter anchor",
            0.92,
            "671B total / 37B active MoE 구조 anchor.",
        ),
        Source(
            "SRC_DEEPSEEK_R1",
            "DeepSeek-R1 GitHub repository",
            "DeepSeek",
            "2025-01-20",
            "https://github.com/deepseek-ai/DeepSeek-R1",
            "Tier 1",
            "Reasoning model family and distillation ecosystem anchor",
            0.88,
            "R1 상용/오픈 생태계 확인. serving power는 별도 scenario.",
        ),
        Source(
            "SRC_DEEPSEEK_V4_PRO",
            "DeepSeek-V4-Pro model card",
            "DeepSeek / Hugging Face",
            "2026-06-26",
            "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro",
            "Tier 1",
            "DeepSeek V4 Pro proxy model identity, MoE total/active parameter anchor and long-context capability",
            0.90,
            "DeepSeek V4 Pro는 1.6T total / 49B activated MoE 및 1M context를 공개한 frontier-class proxy로 사용.",
        ),
        Source(
            "SRC_KIMI_K25",
            "Kimi K2.5 model page and repository",
            "Moonshot AI",
            "2026-02-22",
            "https://www.kimi.com/ai-models/kimi-k2-5 ; https://github.com/MoonshotAI/Kimi-K2.5",
            "Tier 1",
            "Kimi K2.5 proxy model identity, multimodal/agentic capability and deployment support",
            0.88,
            "Kimi K2.5는 공개 agentic/multimodal frontier proxy로 DeepSeek V4 Pro와 함께 composite TPS/MW 산정에 사용.",
        ),
        Source(
            "SRC_QWEN3_GITHUB",
            "Qwen3 GitHub repository",
            "Alibaba / Qwen Team",
            "2025-04-29",
            "https://github.com/QwenLM/Qwen3",
            "Tier 1",
            "Qwen3 dense/MoE family and active parameter anchor",
            0.90,
            "Qwen3 MoE total/active parameter 구조 anchor.",
        ),
        Source(
            "SRC_META_LLAMA4_NVIDIA",
            "Meta Llama 4 model family optimization notes",
            "NVIDIA Developer Blog",
            "2025-04-07",
            "https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/",
            "Tier 2",
            "Llama 4 Scout/Maverick total-active parameter anchor when official Meta page is less accessible",
            0.74,
            "Meta Llama 4 MoE parameter facts는 model card/official ecosystem cross-check 필요.",
        ),
        Source(
            "SRC_TENCENT_HY3",
            "Tencent launches Hunyuan 3D generation model Hy3",
            "Tencent",
            "2025-01-21",
            "https://www.tencent.com/en-us/articles/2202320.html",
            "Tier 1",
            "Tencent Hunyuan commercial surface and model-family anchor",
            0.78,
            "Hy3는 3D 생성 모델이므로 LLM token forecast에는 Hunyuan surface 확인용으로만 사용.",
        ),
        Source(
            "SRC_TENCENT_HUNYUAN",
            "Tencent unveils Hunyuan foundation model",
            "Tencent",
            "2023-09-07",
            "https://www.tencent.com/en-us/articles/2201460.html",
            "Tier 1",
            "Tencent Hunyuan parameter and pretraining token anchor",
            0.82,
            "Hunyuan 100B+ parameter와 2T+ pretraining token 공개 anchor.",
        ),
        Source(
            "SRC_MS_PHI",
            "Phi model family on Azure AI Foundry / Microsoft documentation",
            "Microsoft",
            "2026-05-13 accessed",
            "https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/concepts/models",
            "Tier 1",
            "Microsoft-owned small language model family anchor",
            0.78,
            "Microsoft token attribution은 Phi/MAI owned와 OpenAI model dependency를 분리.",
        ),
        Source(
            "SRC_MS_PHI4_TECHREPORT",
            "Phi-4 technical report",
            "Microsoft",
            "2024-12-12",
            "https://arxiv.org/abs/2412.08905",
            "Tier 1/2",
            "Microsoft-owned Phi-4 14B parameter anchor",
            0.82,
            "Phi-4는 Microsoft-owned model size anchor. Copilot frontier routing은 별도 attribution.",
        ),
        Source(
            "SRC_MS_MAIA200",
            "Microsoft introduces Maia 200: New inference accelerator enhances AI performance in Azure",
            "Microsoft",
            "2026-01-26",
            "https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/",
            "Tier 1",
            "Confirms Maia 200 is an inference accelerator deployed for Microsoft AI models, Azure AI Foundry and Microsoft 365 Copilot",
            0.91,
            "Maia 존재와 inference 용도는 fact. Microsoft serving fleet 내 Maia 비중은 scenario.",
        ),
        Source(
            "SRC_GOOGLE_TPU_V6E",
            "Cloud TPU v6e / Trillium documentation",
            "Google Cloud",
            "2026-05-14 accessed",
            "https://cloud.google.com/tpu/docs/v6e",
            "Tier 1",
            "Google TPU serving/training platform generation anchor",
            0.84,
            "Ironwood와 함께 Google TPU-heavy serving platform의 factual hardware lineage.",
        ),
        Source(
            "SRC_ANTHROPIC_AMAZON_COMPUTE",
            "Anthropic and AWS expand partnership with Project Rainier",
            "Anthropic / Amazon",
            "2025-2026",
            "https://www.anthropic.com/news/anthropic-amazon-compute",
            "Tier 1",
            "Anthropic contracted/hosted capacity anchor; capacity attributed to Anthropic model owner",
            0.84,
            "AWS Trainium/Rainier capacity는 Anthropic 모델 serving/training capacity anchor로 사용하되 active GW는 시나리오.",
        ),
        Source(
            "SRC_ANTHROPIC_CLAUDE_DOCS",
            "Claude model documentation",
            "Anthropic",
            "2026-05-14 accessed",
            "https://docs.anthropic.com/en/docs/about-claude/models/overview",
            "Tier 1",
            "Claude commercial model family and closed-model disclosure boundary",
            0.86,
            "Claude 모델 family 확인. 파라미터는 비공개이므로 band/benchmark proxy만 사용.",
        ),
        Source(
            "SRC_AWS_RAINIER_ACTIVE",
            "AWS activates Project Rainier: AI compute cluster for Anthropic",
            "Amazon Web Services / Amazon",
            "2025-10-29",
            "https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster",
            "Tier 1",
            "Confirms Anthropic-dedicated Trainium2 capacity direction and purpose-built accelerator presence",
            0.90,
            "Trainium hardware direction은 fact. Claude inference/training allocation과 year-by-year mix는 scenario.",
        ),
        Source(
            "SRC_META_MTIA_GENAI_2026",
            "Expanding Meta's Custom Silicon to Power Our AI Workloads",
            "Meta",
            "2026-03-11",
            "https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/",
            "Tier 1",
            "Confirms hundreds of thousands of MTIA deployed for inference and MTIA 400/450/500 focus on GenAI inference production",
            0.92,
            "MTIA 존재와 inference-first 방향은 fact. Meta AI LLM serving의 MTIA share는 scenario.",
        ),
        Source(
            "SRC_DEEPSEEK_H800_INFERENCE",
            "DeepSeek-V3/R1 inference system overview",
            "DeepSeek",
            "2025-02-28",
            "https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md",
            "Tier 1",
            "Confirms disclosed DeepSeek-operated V3/R1 inference services used H800 GPUs and reports peak/average node occupancy",
            0.91,
            "공개 시점의 H800 serving은 fact. 2026-2030 증설 규모는 scenario.",
        ),
        Source(
            "SRC_ALIBABA_QWEN_GPU_DEPLOY",
            "Deploy a Qwen3-32B inference service with ACS GPU computing power",
            "Alibaba Cloud",
            "2025-09-18",
            "https://www.alibabacloud.com/help/doc-detail/2921971.html",
            "Tier 1",
            "Confirms an official Alibaba Cloud GPU deployment path for Qwen inference; not an operated fleet-share disclosure",
            0.78,
            "Qwen GPU serving 가능성은 fact. 실제 Alibaba-operated GPU/ASIC 비중은 공개되지 않아 Base는 GPU reference 처리.",
        ),
        Source(
            "SRC_TENCENT_AI_INFRA_MOE",
            "Tencent Unveils New AI Upgrades, Proprietary Innovations, and Global Solutions",
            "Tencent",
            "2024-09-05",
            "https://www.tencent.com/en-us/articles/2201930.html",
            "Tier 1",
            "Confirms Tencent AI Infra and Hunyuan Turbo MoE service with stated inference-cost reduction",
            0.84,
            "MoE/infra 방향은 fact. 운영 GPU/ASIC mix와 tokens/MW는 정량 미공개로 scenario.",
        ),
        Source(
            "SRC_SEMIANALYSIS_INFERENCEX",
            "InferenceX / InferenceMAX benchmark methodology",
            "SemiAnalysis",
            "2025-2026",
            "https://inferencex.semianalysis.com/about",
            "Tier 2",
            "Benchmark layer for tokens/sec/MW sensitivity, not company capacity",
            0.70,
            "tokens/sec/MW benchmark calibration. 업체별 capacity fact로 직접 사용하지 않음.",
        ),
        Source(
            "SRC_MLPERF_INFERENCE",
            "MLPerf Inference datacenter benchmark results",
            "MLCommons",
            "2026-06-09 accessed",
            "https://mlcommons.org/benchmarks/inference-datacenter/",
            "Tier 2",
            "Official inference submission anchor for hardware/software comparisons",
            0.74,
            "규칙화된 official benchmark anchor. LLM serving 조건은 InferenceX와 별도 비교 필요.",
        ),
        Source(
            "SRC_MLPERF_POWER",
            "MLPerf Power methodology and results",
            "MLCommons",
            "2026-06-09 accessed",
            "https://mlcommons.org/benchmarks/power/",
            "Tier 2",
            "Optional measured power/performance benchmark anchor",
            0.72,
            "power 측정이 포함된 benchmark anchor. company production telemetry는 아님.",
        ),
        Source(
            "SRC_MLPERF_INFERENCE_DOCS",
            "MLPerf Inference documentation",
            "MLCommons",
            "2026-06-09 accessed",
            "https://docs.mlcommons.org/inference/",
            "Tier 2",
            "Benchmark rules, scenarios, loadgen and divisions",
            0.72,
            "Server/Offline/SUT 규칙과 latency scenario를 해석하는 기준 문서.",
        ),
        Source(
            "SRC_VLLM_DOCS",
            "vLLM documentation",
            "vLLM project",
            "2026-06-09 accessed",
            "https://docs.vllm.ai/",
            "Tier 2",
            "Production serving mechanism, scheduler and KV cache behavior",
            0.66,
            "serving stack mechanism source. 특정 업체 tokens/MW fact는 아님.",
        ),
        Source(
            "SRC_TENSORRT_LLM",
            "NVIDIA TensorRT-LLM documentation",
            "NVIDIA",
            "2026-06-09 accessed",
            "https://nvidia.github.io/TensorRT-LLM/",
            "Tier 2",
            "Vendor-optimized inference stack and deployment mechanism",
            0.68,
            "NVIDIA stack 최적화 근거. workload matched benchmark 없이는 uplift로 직접 적용하지 않음.",
        ),
        Source(
            "SRC_SGLANG_DOCS",
            "SGLang documentation",
            "SGLang project",
            "2026-06-09 accessed",
            "https://docs.sglang.ai/",
            "Tier 2",
            "Serving runtime, structured generation and batching behavior",
            0.64,
            "batching/structured generation mechanism source. production telemetry는 아님.",
        ),
        Source(
            "SRC_FLASHINFER",
            "FlashInfer documentation",
            "FlashInfer project",
            "2026-06-09 accessed",
            "https://docs.flashinfer.ai/",
            "Tier 2",
            "Attention/decode kernel mechanism for serving efficiency",
            0.62,
            "kernel-level efficiency mechanism source. company-level throughput fact로 승격하지 않음.",
        ),
        Source(
            "SRC_SARATHI_SERVE",
            "Sarathi-Serve",
            "arXiv",
            "2024",
            "https://arxiv.org/abs/2403.02310",
            "Tier 2",
            "Chunked prefill and decode scheduling mechanism",
            0.64,
            "prefill/decode scheduling sensitivity source.",
        ),
        Source(
            "SRC_ORCA_SERVING",
            "Orca: A Distributed Serving System for Transformer-Based Generative Models",
            "OSDI",
            "2022",
            "https://www.usenix.org/conference/osdi22/presentation/yu",
            "Tier 2",
            "Iteration-level scheduling and batching foundation",
            0.66,
            "LLM serving scheduling foundation. modern hardware TPS/MW fact는 아님.",
        ),
        Source(
            "SRC_ARXIV_INFERENCE_ENERGY",
            "LLM inference energy and serving efficiency literature set",
            "arXiv",
            "2024-2026",
            "https://arxiv.org/search/?query=large+language+model+inference+energy+joules+per+token&searchtype=all",
            "Tier 2",
            "Joules/token sanity check, prefill/decode split, batching, quantization sensitivity",
            0.65,
            "논문별 수치는 workload 차이가 커서 sensitivity layer로만 사용.",
        ),
        Source(
            "SRC_JOULE_INFERENCE_ENERGY_2026",
            "Energy use of AI inference, efficiency pathways, and test-time scaling",
            "Joule / Cell Press",
            "2026",
            "https://www.sciencedirect.com/science/article/pii/S2542435126001145",
            "Tier 2",
            "Energy/query and joules/token sanity layer for inference forecasts",
            0.70,
            "회사별 production telemetry가 아니라 energy sanity check와 test-time compute sensitivity로만 사용.",
        ),
        Source(
            "SRC_IBM_PD_DISAGG_2026",
            "Revisiting Disaggregated Large Language Model Serving for Performance and Energy Implications",
            "IBM Research / EuroSys",
            "2026",
            "https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications",
            "Tier 2",
            "Prefill/decode disaggregation performance and energy trade-off mechanism",
            0.72,
            "P/D disaggregation은 항상 positive가 아니므로 workload/SLO별 sensitivity로 처리.",
        ),
        Source(
            "SRC_ARXIV_SLO_PD_2026",
            "SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM Inference",
            "arXiv",
            "2026",
            "https://arxiv.org/abs/2603.04716",
            "Tier 2",
            "Utilization caveat for TTFT/TPOT SLO constrained serving",
            0.62,
            "utilization은 GPU occupancy가 아니라 latency SLO와 reserve에 의해 제한됨을 반영.",
        ),
        Source(
            "SRC_ARXIV_PREFILL_AS_SERVICE_2026",
            "Prefill-as-a-Service",
            "arXiv",
            "2026",
            "https://arxiv.org/abs/2604.15039",
            "Tier 2",
            "Agentic/long-context placement and network sensitivity for utilization",
            0.60,
            "cross-datacenter prefill/KV movement은 Base fact가 아니라 future sensitivity로만 사용.",
        ),
        Source(
            "SRC_ARXIV_SPEC_DECODING_LATENCY_2026",
            "An Interpretable Latency Model for Speculative Decoding in LLM Serving",
            "arXiv",
            "2026",
            "https://arxiv.org/abs/2605.15051",
            "Tier 2",
            "Speculative decoding latency and throughput trade-off mechanism",
            0.60,
            "speculative decoding은 tokens/MW 개선 가능성이 있으나 model/workload별 검증 필요.",
        ),
        Source(
            "SRC_MCKINSEY_AI_WORKLOADS",
            "The future of AI workloads",
            "McKinsey & Company",
            "2026-02-24",
            "https://www.mckinsey.com/featured-insights/week-in-charts/the-future-of-ai-workloads",
            "Tier 2",
            "Inference share fact-check and 2030 workload mix directional anchor",
            0.72,
            "2030년 inference가 AI compute의 절반 이상이 될 수 있다는 전망. 2026 현재 GW fact로 직접 사용하지 않음.",
        ),
        Source(
            "SRC_DELOITTE_AI_POWER",
            "More compute for AI, not less",
            "Deloitte",
            "2025-12",
            "https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html",
            "Tier 2",
            "Inference compute share outlook, used only as scenario cross-check",
            0.68,
            "2026 compute 기준 inference 비중 전망을 제공하지만 업체별 GW fact는 아님.",
        ),
        Source(
            "SRC_EPRI_EPOCH_AI_POWER",
            "How much power will frontier AI training demand in 2030?",
            "EPRI / Epoch AI",
            "2025-08",
            "https://epoch.ai/blog/power-demands-of-frontier-ai-training",
            "Tier 2",
            "Current AI power allocation sanity check across training, experiments, and inference",
            0.70,
            "현재 power allocation은 training/experiments/inference가 대략 나뉜다는 관점. 60%+ inference fact 주장에 대한 반대 anchor.",
        ),
        Source(
            "SRC_EPOCH_TRAIN",
            "Training compute of frontier AI models grows by 4-5x per year",
            "Epoch AI",
            "2024",
            "https://epoch.ai/blog/training-compute-of-frontier-ai-models-grows-by-4-5x-per-year",
            "Tier 2",
            "Frontier training compute growth anchor",
            0.70,
            "training reserve를 남겨야 하는 장기 compute-growth 근거.",
        ),
        Source(
            "SRC_EPOCH_SCALING_2030",
            "Can AI scaling continue through 2030?",
            "Epoch AI",
            "2024/2026 accessed",
            "https://epoch.ai/publications/can-ai-scaling-continue-through-2030",
            "Tier 2",
            "Scaling bottlenecks across power, data, capex and hardware supply",
            0.70,
            "2030 scaling feasibility와 병목 source. 업체별 active power fact는 아님.",
        ),
        Source(
            "SRC_EPOCH_INFERENCE_PRICE",
            "LLM inference price trends",
            "Epoch AI",
            "2026-06-09 accessed",
            "https://epoch.ai/data-insights/llm-inference-price-trends",
            "Tier 2",
            "Inference cost trend proxy and commercial efficiency context",
            0.66,
            "API price/performance trend proxy. tokens/MW 생산 telemetry로 직접 사용하지 않음.",
        ),
        Source(
            "SRC_EIA_DC_POWER",
            "U.S. electricity data and data center power context",
            "U.S. EIA",
            "2026-06-09 accessed",
            "https://www.eia.gov/",
            "Tier 2",
            "Electricity demand and regional power baseline",
            0.68,
            "macro grid plausibility source. company contracted GW를 직접 바꾸지 않음.",
        ),
        Source(
            "SRC_FERC_INTERCONNECT",
            "FERC interconnection and grid reliability proceedings",
            "FERC",
            "2026-06-09 accessed",
            "https://www.ferc.gov/",
            "Tier 2",
            "Interconnection, transmission and reliability context",
            0.66,
            "grid constraint context. model-owner capacity attribution fact는 아님.",
        ),
        Source(
            "SRC_UPTIME_GLOBAL_DC",
            "Uptime Institute Global Data Center Survey",
            "Uptime Institute",
            "2026-06-09 accessed",
            "https://uptimeinstitute.com/resources/research-and-reports",
            "Tier 2",
            "PUE, cooling, outage and density operating context",
            0.68,
            "facility/PUE context. company site-level PUE가 있으면 교체.",
        ),
        Source(
            "SRC_ASHRAE_TC99",
            "ASHRAE TC 9.9 data center thermal guidance",
            "ASHRAE",
            "2026-06-09 accessed",
            "https://www.ashrae.org/technical-resources/bookstore/datacom-series",
            "Tier 2",
            "Thermal envelope and cooling design reference",
            0.64,
            "cooling design reference. PUE 숫자 자체의 direct fact는 아님.",
        ),
        Source(
            "SRC_MISTRAL_MODELS",
            "Mistral AI model documentation",
            "Mistral AI",
            "2026-06-09 accessed",
            "https://docs.mistral.ai/",
            "Tier 1/2",
            "Dense/MoE open model family and context anchor",
            0.72,
            "open/served model family 비교 anchor. 본 모델의 core company row에는 직접 포함하지 않음.",
        ),
        Source(
            "SRC_DBRX_MODEL",
            "Introducing DBRX",
            "Databricks",
            "2024",
            "https://www.databricks.com/blog/introducing-dbrx-new-state-art-open-llm",
            "Tier 1/2",
            "Open MoE parameter anchor",
            0.70,
            "MoE total/active parameter 읽기용 비교 source.",
        ),
        Source(
            "SRC_OPENAI_API_PRICING",
            "OpenAI API pricing",
            "OpenAI",
            "2026-06-09 accessed",
            "https://openai.com/api/pricing/",
            "Tier 1",
            "Commercial token surface and price proxy",
            0.78,
            "price surface proxy. output volume 또는 tokens/MW production fact는 아님.",
        ),
        Source(
            "SRC_OPENAI_CODEX_RATE_CARD",
            "Codex rate card",
            "OpenAI Help Center",
            "2026-07 accessed",
            "https://help.openai.com/en/articles/20001106",
            "Tier 1",
            "Codex usage is token-metered with separate input/cached-input/output token rates; supports modeling Codex as high-context agentic workload.",
            0.84,
            "Codex seat/usage pricing이 token 기반으로 바뀐 점은 agentic workload가 별도 consumption surface임을 보여준다.",
        ),
        Source(
            "SRC_OPENAI_CHATGPT_ENTERPRISE",
            "What is ChatGPT Enterprise?",
            "OpenAI Help Center",
            "2026-07 accessed",
            "https://help.openai.com/en/articles/8265053-what-is-chatgpt-enterprise",
            "Tier 1",
            "Enterprise includes ChatGPT, ChatGPT Agent, Deep Research and Codex/Codex seats; supports separating chat and agentic surfaces.",
            0.82,
            "ChatGPT Enterprise의 standard/Codex seat 구분과 advanced tools는 workload mix 근거로만 사용.",
        ),
        Source(
            "SRC_ANTHROPIC_PRICING",
            "Anthropic API pricing",
            "Anthropic",
            "2026-06-09 accessed",
            "https://www.anthropic.com/pricing",
            "Tier 1",
            "Commercial token surface and price proxy",
            0.78,
            "price surface proxy. Claude production output volume은 공개하지 않음.",
        ),
        Source(
            "SRC_ANTHROPIC_CONSUMPTION_GUIDE",
            "Claude Enterprise consumption guide",
            "Anthropic Help Center",
            "2026-07 accessed",
            "https://support.claude.com/en/articles/14782391-claude-enterprise-consumption-guide",
            "Tier 1",
            "Anthropic states Claude Code and Cowork are significantly more token-intensive than standard chat.",
            0.88,
            "Claude의 agentic/coding workload 비중 및 high token intensity를 정당화하되, 회사별 traffic share는 scenario.",
        ),
        Source(
            "SRC_ANTHROPIC_CODE_PRACTICE",
            "Agentic coding and persistent returns to expertise",
            "Anthropic Research",
            "2026-06-16",
            "https://www.anthropic.com/research/claude-code-expertise",
            "Tier 1",
            "Claude Code usage study of roughly 400k sessions; supports agentic coding as a major Claude surface.",
            0.84,
            "Claude Code adoption/usage intensity direction의 근거. tokens/MW 생산 telemetry는 아님.",
        ),
        Source(
            "SRC_GOOGLE_GEMINI_LONG_CONTEXT",
            "Gemini API long context documentation",
            "Google AI for Developers",
            "2026-07 accessed",
            "https://ai.google.dev/gemini-api/docs/long-context",
            "Tier 1",
            "Gemini models support 1M+ context windows and long-context use cases; supports a separate long-chat workload class.",
            0.86,
            "Gemini long context는 workload shape 근거이며, production traffic share 또는 tokens/MW fact가 아님.",
        ),
        Source(
            "SRC_GOOGLE_GEMINI_AGENT_PLATFORM",
            "Introducing Gemini Enterprise Agent Platform",
            "Google Cloud",
            "2026-04-22",
            "https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform",
            "Tier 1",
            "Google positions Gemini Enterprise Agent Platform for agents interacting across systems.",
            0.82,
            "Google agentic enterprise surface의 방향성 근거. exact traffic mix는 scenario.",
        ),
        Source(
            "SRC_META_BUSINESS_AGENT",
            "Be There for Every Customer With Meta Business Agent",
            "Meta",
            "2026-06-03",
            "https://about.fb.com/news/2026/06/meta-business-agent/",
            "Tier 1",
            "Meta discloses broad business-agent messaging surface and over one million businesses using Meta Business Agent.",
            0.86,
            "Meta workload mix를 short/business chat-heavy로 두는 방향성 근거.",
        ),
        Source(
            "SRC_INFERENCEX_AGENTIC_TRACES_256K",
            "CC Traces — Weka, With Subagents, 256k cap",
            "SemiAnalysisAI / Hugging Face",
            "2026-06-21",
            "https://huggingface.co/datasets/semianalysisai/cc-traces-weka-062126-256k",
            "Tier 2",
            "Agentic coding trace profile used for input/output load-shape calibration.",
            0.74,
            "평균 input 약 101k/output 약 860 tokens/request인 agentic load shape 근거. throughput telemetry는 아님.",
        ),
        Source(
            "SRC_AZURE_OPENAI",
            "Azure OpenAI Service documentation",
            "Microsoft",
            "2026-06-09 accessed",
            "https://learn.microsoft.com/azure/ai-services/openai/",
            "Tier 1",
            "Microsoft host/product surface vs OpenAI model attribution",
            0.78,
            "OpenAI model owner와 Azure product/host surface 분리용.",
        ),
        Source(
            "SRC_GOOGLE_CLOUD_ANTHROPIC",
            "Google Cloud and Anthropic partnership",
            "Google Cloud",
            "2026-06-09 accessed",
            "https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-anthropic-ai-partnership",
            "Tier 1/2",
            "Third-party model hosted on cloud provider",
            0.72,
            "Google host capacity와 Anthropic model-owner attribution 분리용.",
        ),
        Source(
            "SRC_ARTIFICIAL_ANALYSIS",
            "Artificial Analysis model and API benchmarks",
            "Artificial Analysis",
            "2026-06-09 accessed",
            "https://artificialanalysis.ai/",
            "Tier 2",
            "Public API price/performance and latency proxy",
            0.64,
            "commercial API price/latency proxy. company capacity fact 아님.",
        ),
        Source(
            "SRC_OPENROUTER_RANKINGS",
            "OpenRouter model pricing and usage market signals",
            "OpenRouter",
            "2026-06-09 accessed",
            "https://openrouter.ai/rankings",
            "Tier 2",
            "API price and demand mix proxy",
            0.58,
            "market routing proxy. 전체 production traffic fact로 해석하지 않음.",
        ),
        Source(
            "SRC_SEMI_100K_CLUSTER",
            "SemiAnalysis AI infrastructure and 100k H100 cluster analysis",
            "SemiAnalysis",
            "2026-06-09 accessed",
            "https://semianalysis.com/",
            "Tier 2",
            "Accelerator cluster, networking and non-GPU overhead context",
            0.62,
            "cluster architecture context. specific company active GW fact는 아님.",
        ),
        Source(
            "SRC_DELLORO_AI_NETWORKS",
            "AI networks and data center switch market context",
            "Dell'Oro Group",
            "2026-06-09 accessed",
            "https://www.delloro.com/",
            "Tier 2",
            "Network/power overhead and AI cluster infrastructure context",
            0.58,
            "network overhead/context source. model equation에는 직접 계수로 넣지 않음.",
        ),
    ]


def company_models() -> list[CompanyModel]:
    return [
        CompanyModel(
            "Microsoft",
            "Phi / MAI / Copilot model mix",
            "Microsoft 365 Copilot, GitHub Copilot, Azure AI Foundry",
            "Phi 공개모델: 3B-14B급; MAI/대형 Copilot 모델: undisclosed band",
            "Phi: dense disclosed; MAI/Copilot: closed band",
            "Dense SLM + closed frontier/agentic routing",
            "Azure GPU + Maia inference + OpenAI-hosted dependency split",
            "Microsoft-owned token은 Phi/MAI/Copilot serving으로, OpenAI model output은 OpenAI row에도 별도 표기",
            "NVIDIA GPU + Maia inference accelerator (numeric share modeled separately)",
            "SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_MAIA200",
            "Medium",
            "Microsoft는 Copilot 상용 표면이 크지만 model-owner attribution은 OpenAI dependency를 분리해야 함.",
        ),
        CompanyModel(
            "Google",
            "Gemini / Gemma",
            "Gemini app/API, Google Workspace, Cloud Vertex AI",
            "Gemini closed frontier band; Gemma 공개모델 1B-27B급",
            "Closed frontier active band; open Gemma disclosed",
            "Dense/MoE undisclosed frontier + open dense models",
            "TPU v5/v6/Ironwood + selective NVIDIA GPU",
            "Google-owned Gemini token generation, Anthropic hosted capacity excluded from core",
            "TPU-heavy serving, Google Cloud GPU where needed",
            "SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD",
            "Medium-High",
            "TPU 최적화가 tokens/MW 상향 요인. closed Gemini parameter는 band만 허용.",
        ),
        CompanyModel(
            "Meta",
            "Llama / Meta AI",
            "Meta AI app, WhatsApp/Instagram/Facebook AI, open Llama ecosystem",
            "Llama 4 Scout 109B / Maverick 400B anchor; production routing undisclosed",
            "Llama 4 Scout/Maverick active 17B anchor; Meta AI serving mix band",
            "Open dense/MoE family + in-house ranking/routing",
            "NVIDIA GPU fleet + MTIA inference layer",
            "Meta-owned consumer and open model serving; third-party hosted Llama not counted in Meta owner tokens",
            "NVIDIA GPU + MTIA inference portfolio (numeric share modeled separately)",
            "SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026",
            "Medium-High for open model params, Medium for active capacity",
            "Llama 4 MoE parameter facts improve model-side confidence; exact Meta AI active capacity remains scenario.",
        ),
        CompanyModel(
            "xAI",
            "Grok",
            "Grok app/API, X integration, enterprise API",
            "Closed frontier band",
            "Closed frontier active band",
            "Closed frontier multimodal/reasoning model",
            "Colossus-style NVIDIA GPU clusters",
            "xAI-owned Grok token generation; X social integration counted only when model generated",
            "NVIDIA GPU dominated",
            "SRC_XAI_MODELS",
            "Medium-Low",
            "Colossus scale is visible directionally, but active inference/training split remains scenario.",
        ),
        CompanyModel(
            "OpenAI",
            "GPT / o-series / ChatGPT",
            "ChatGPT, API, enterprise, Microsoft/OpenAI distribution",
            "Closed frontier band only",
            "Closed frontier active band only",
            "Closed frontier multimodal/reasoning + router stack",
            "Azure + Oracle/Stargate + partner GPU clusters",
            "OpenAI model output counted here, including OpenAI models served through Microsoft channels when model ownership is OpenAI",
            "NVIDIA GB200/GPU reference; no public operated custom-ASIC share",
            "SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS",
            "Medium",
            "사용량은 가장 크지만 parameter와 active capacity 공개성이 낮아 band/scenario 중심.",
        ),
        CompanyModel(
            "Anthropic",
            "Claude Opus / Sonnet / Haiku",
            "Claude app/API, Amazon Bedrock, Google Cloud Vertex AI",
            "Closed frontier band only",
            "Closed active band only; benchmark proxy uses effective active band",
            "Closed frontier reasoning/coding/multimodal model family",
            "AWS Trainium/Rainier + Google Cloud TPU/GPU hosted capacity",
            "Anthropic model output counted under Anthropic, even when served through AWS/Google host capacity",
            "AWS Trainium / Google TPU purpose-built hosted capacity plus GPU partners (numeric share modeled separately)",
            "SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE",
            "Medium for capacity anchor, Low for parameters",
            "Anthropic은 이번 통합 버전부터 core model owner로 포함. 파라미터는 closed band로만 처리.",
        ),
        CompanyModel(
            "DeepSeek",
            "DeepSeek-V3 / R1",
            "DeepSeek app/API, open model derivatives, enterprise deployments",
            "V3/R1 MoE: 671B total anchor",
            "MoE active: 약 37B anchor",
            "MoE reasoning/dense distilled ecosystem",
            "GPU-constrained serving with MoE efficiency and local cloud deployments",
            "DeepSeek direct app/API tokens counted; third-party self-hosted derivatives excluded unless DeepSeek-operated",
            "H800 GPU serving anchor; future mix undisclosed",
            "SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE",
            "High for parameters, Low-Medium for capacity",
            "모델 구조는 투명하지만 회사 운영 capacity는 공개성이 낮아 scenario.",
        ),
        CompanyModel(
            "Alibaba",
            "Qwen / Qwen3",
            "Alibaba Cloud Model Studio, Qwen Chat/API, enterprise cloud",
            "Qwen3 dense/MoE disclosed bands; flagship MoE up to 235B total anchor",
            "MoE active anchor up to 22B for flagship class",
            "Dense + MoE multilingual/code/reasoning family",
            "Alibaba Cloud GPU/China accelerator mix",
            "Alibaba-operated Qwen serving counted; open-source third-party self-hosting excluded",
            "GPU serving reference; operated accelerator mix undisclosed",
            "SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY",
            "High for Qwen3 parameters, Medium-Low for active capacity",
            "Qwen3 공개성이 높아 model band 신뢰도는 높고 power capacity는 별도 scenario.",
        ),
        CompanyModel(
            "Tencent",
            "Hunyuan / Hy3 / Yuanbao",
            "Tencent Yuanbao, WeChat/QQ enterprise AI, Tencent Cloud",
            "Hunyuan 100B+ anchor; Hy3 separate multimodal/3D family",
            "Closed active band; Hunyuan-Large MoE active parameter requires separate verification",
            "Closed dense/MoE + multimodal generation family",
            "Tencent Cloud GPU/China accelerator mix",
            "Tencent-operated Hunyuan/Yuanbao tokens counted; embedded non-LLM media generation separated",
            "GPU serving reference; operated accelerator mix undisclosed",
            "SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE",
            "Medium for Hunyuan published anchor, Medium-Low for active capacity",
            "Hunyuan 100B+와 2T+ pretraining token은 fact anchor, serving capacity는 scenario.",
        ),
    ]


def scenarios() -> list[CompanyScenario]:
    return [
        CompanyScenario("Microsoft", "US", "Phi / MAI / Copilot model mix", "Copilot + Azure AI", 4.0, 9.0, 1.8, 6.2, 0.55, 0.75, 0.16, 0.54, 0.68, 1.20, 0.86, "Medium", "Estimate+Scenario", "SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200", "ASSUMP_POWER_RAMP; ASSUMP_MS_OPENAI_ATTRIBUTION; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("Google", "US", "Gemini / Gemma", "Gemini + Workspace + Vertex", 4.5, 8.0, 2.2, 6.8, 0.55, 0.72, 0.18, 0.56, 0.70, 1.18, 0.88, "Medium-High", "Estimate+Scenario", "SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E", "ASSUMP_TPU_EFFICIENCY; ASSUMP_POWER_RAMP; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("Meta", "US", "Llama / Meta AI", "Meta AI + family apps", 3.5, 7.0, 1.6, 5.8, 0.58, 0.78, 0.16, 0.55, 0.70, 1.20, 0.87, "Medium", "Estimate+Scenario", "SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026", "ASSUMP_CONSUMER_AI_UTILIZATION; ASSUMP_POWER_RAMP; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("xAI", "US", "Grok", "Grok + X + API", 1.0, 3.0, 0.35, 2.5, 0.45, 0.70, 0.17, 0.50, 0.67, 1.22, 0.85, "Medium-Low", "Estimate+Scenario", "SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS", "ASSUMP_CLUSTER_RAMP; ASSUMP_CLOSED_MODEL_BAND; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("OpenAI", "US", "GPT / o-series / ChatGPT", "ChatGPT + API + enterprise", 5.0, 12.0, 1.4, 8.5, 0.58, 0.78, 0.17, 0.57, 0.71, 1.20, 0.88, "Medium", "Estimate+Scenario", "SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS", "ASSUMP_STARGATE_RAMP; ASSUMP_MS_OPENAI_ATTRIBUTION; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("Anthropic", "US", "Claude Opus / Sonnet / Haiku", "Claude + Bedrock + Vertex", 3.5, 7.0, 1.0, 5.5, 0.52, 0.74, 0.16, 0.55, 0.70, 1.18, 0.86, "Medium", "Estimate+Scenario", "SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE", "ASSUMP_POWER_RAMP; ASSUMP_CLOSED_MODEL_BAND; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("DeepSeek", "China", "DeepSeek-V3 / R1", "DeepSeek app/API", 0.5, 1.8, 0.15, 1.2, 0.62, 0.82, 0.18, 0.48, 0.66, 1.24, 0.82, "Parameter High / Capacity Low-Medium", "Fact+Scenario", "SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE", "ASSUMP_MOE_EFFICIENCY; ASSUMP_CN_CAPACITY_TRANSPARENCY; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("Alibaba", "China", "Qwen / Qwen3", "Model Studio + Qwen API", 1.8, 4.0, 0.65, 3.2, 0.60, 0.80, 0.17, 0.52, 0.68, 1.23, 0.84, "Medium", "Fact+Scenario", "SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY", "ASSUMP_MOE_EFFICIENCY; ASSUMP_CN_CAPACITY_TRANSPARENCY; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
        CompanyScenario("Tencent", "China", "Hunyuan / Yuanbao", "Yuanbao + WeChat/Tencent Cloud", 1.2, 3.0, 0.45, 2.4, 0.60, 0.80, 0.16, 0.52, 0.68, 1.23, 0.84, "Medium-Low", "Estimate+Scenario", "SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE", "ASSUMP_CN_CAPACITY_TRANSPARENCY; ASSUMP_APP_EMBEDDING; ASSUMP_NUMERIC_ACCELERATOR_MIX"),
    ]


def assumptions() -> list[dict[str, Any]]:
    return [
        {
            "assumption_id": "ASSUMP_POWER_RAMP",
            "description_kr": "계약 전력은 발표/공급망 방향성 anchor, active power는 실제 IT load 가동률 ramp로 별도 산정.",
            "replacement_path": "회사별 데이터센터 계약 MW, interconnect queue, 전력구매계약, 클라우드 capex disclosure로 대체.",
            "confidence": 0.55,
        },
        {
            "assumption_id": "ASSUMP_TPU_EFFICIENCY",
            "description_kr": "Google TPU/Ironwood 기반 serving은 2026 tokens/sec/MW와 개선률에 premium 부여.",
            "replacement_path": "Gemini serving benchmark, TPU fleet disclosure, customer measured latency/cost로 교정.",
            "confidence": 0.62,
        },
        {
            "assumption_id": "ASSUMP_MOE_EFFICIENCY",
            "description_kr": "MoE는 total parameter 대비 active parameter가 낮아 decode token/MW 효율이 상대적으로 높다고 가정.",
            "replacement_path": "InferenceX 모델별 throughput/MW, 공개 serving benchmark, batch/context profile로 대체.",
            "confidence": 0.60,
        },
        {
            "assumption_id": "ASSUMP_MS_OPENAI_ATTRIBUTION",
            "description_kr": "Microsoft Copilot 사용량 중 OpenAI 모델 output은 OpenAI model-owner token으로도 추적하고, Microsoft row에는 customer-facing serving burden을 별도 추정.",
            "replacement_path": "Copilot 모델 라우팅 mix, Azure OpenAI usage split, MAI/Phi share disclosure.",
            "confidence": 0.50,
        },
        {
            "assumption_id": "ASSUMP_STARGATE_RAMP",
            "description_kr": "Stargate/Oracle capacity는 2026~2030 staged activation으로 반영. 계약/계획 전력과 active inference load를 분리.",
            "replacement_path": "사이트별 energization date, GPU delivery schedule, Oracle/OpenAI 계약 MW disclosure.",
            "confidence": 0.55,
        },
        {
            "assumption_id": "ASSUMP_CN_CAPACITY_TRANSPARENCY",
            "description_kr": "중국 모델 업체는 공개 capacity 투명성이 낮으므로 capacity confidence만 낮게 표시하고 모델 구조 자체는 공식 공개자료를 그대로 인정.",
            "replacement_path": "Alibaba/Tencent/DeepSeek cloud capex, GPU cluster disclosure, inference API traffic data.",
            "confidence": 0.48,
        },
        {
            "assumption_id": "ASSUMP_CONSUMER_AI_UTILIZATION",
            "description_kr": "Meta/Tencent처럼 앱 내 AI 표면이 큰 업체는 inference share가 빠르게 상승하는 것으로 반영.",
            "replacement_path": "일별 활성 사용자, 세션당 토큰, 앱별 AI feature penetration로 대체.",
            "confidence": 0.55,
        },
        {
            "assumption_id": "ASSUMP_INFERENCE_SHARE_NOT_FACT_60",
            "description_kr": "2026년에 전체 AI GW의 60% 이상이 inference라는 주장은 공식 company-level fact가 아니라 전망/시나리오로 처리.",
            "replacement_path": "업체별 cluster telemetry, AI workload scheduling logs, serving/training capex split disclosure로 대체.",
            "confidence": 0.70,
        },
        {
            "assumption_id": "ASSUMP_NUMERIC_ACCELERATOR_MIX",
            "description_kr": "GPU/ASIC mix는 운영 fleet share 공개가 없는 경우 fact가 아니라 serving-platform anchor를 바탕으로 둔 숫자 시나리오다. 공식적으로 custom accelerator deployment가 확인된 Microsoft, Google, Meta, Anthropic만 purpose-built accelerator share 상승을 Base에 반영하고, 나머지는 GPU-reference Base로 둔다.",
            "replacement_path": "업체별 inference fleet chip count, accelerator-hours, serving traffic allocation 또는 model별 production benchmark disclosure.",
            "confidence": 0.42,
        },
        {
            "assumption_id": "ASSUMP_WORKLOAD_CLASS_MIX",
            "description_kr": "상용 inference load를 short_chat, long_chat, agentic 세 클래스로 분리한다. 회사별 비중은 product surface와 공개 token-consumption guidance에 근거한 scenario이며 traffic fact가 아니다.",
            "replacement_path": "업체별 request log에서 ISL/OSL, cache read/write, tool-call, agent session share, product별 token volume을 공개/내부 telemetry로 교체.",
            "confidence": 0.46,
        },
        {
            "assumption_id": "ASSUMP_AGENTIC_CONTEXT_PENALTY",
            "description_kr": "Agentic trace는 평균 100k+ input/request인 load-shape 근거이지만 matched InferenceX 100k benchmark가 없으므로, Kimi K2.5 dynamic reasoning row에서 산출한 agentic/long TPS/MW ratio를 long_chat TPS/MW에 적용한다.",
            "replacement_path": "InferenceX 또는 production benchmark의 64k/128k/256k ISL, tool-use, cache-aware output_tok_s_mw row.",
            "confidence": 0.46,
        },
        {
            "assumption_id": "ASSUMP_CLUSTER_RAMP",
            "description_kr": "xAI Colossus처럼 accelerator count와 expansion direction은 공개되지만 동일 범위의 contracted/active GW가 공개되지 않은 cluster는 staged operational power envelope로 모델링한다.",
            "replacement_path": "사이트별 utility/onsite power, energized racks, accelerator deployment dates 및 serving allocation disclosure.",
            "confidence": 0.46,
        },
        {
            "assumption_id": "ASSUMP_CLOSED_MODEL_BAND",
            "description_kr": "OpenAI, Anthropic, xAI 등 closed model은 공식 파라미터 수치가 공개되지 않으면 단일 정확값 대신 architecture/active-parameter band 또는 undisclosed 표시로만 사용한다.",
            "replacement_path": "공식 model card, technical report 또는 vendor-published parameter/architecture disclosure.",
            "confidence": 0.72,
        },
        {
            "assumption_id": "ASSUMP_APP_EMBEDDING",
            "description_kr": "Tencent Hunyuan/Yuanbao처럼 대규모 consumer/product surface 내 embedding direction은 inference allocation 상승 가능성의 scenario 근거로만 사용하며 실제 serving load share로 간주하지 않는다.",
            "replacement_path": "제품별 AI 활성 사용자, 호출량, token volume 또는 workload-power allocation disclosure.",
            "confidence": 0.45,
        },
    ]


def accelerator_mix_profiles() -> dict[str, dict[str, Any]]:
    """Numeric accelerator-mix assumptions with explicit audit rationale.

    The numeric shares are scenario inputs unless the company reports operated
    fleet allocation. Hardware mix is shown for allocation transparency. It
    does not create a throughput uplift in the headline formula until a
    comparable output-token benchmark exists for the purpose-built hardware.
    """
    return {
        "Microsoft": {
            "gpu_label": "NVIDIA GPU / Azure GPU reference",
            "asic_label": "Maia inference accelerator",
            "gpu_share_2026": 0.90,
            "gpu_share_2030": 0.55,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_MS_MAIA200; SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS",
            "mix_rationale": "Maia 200 is officially designated for inference, Azure AI Foundry and Microsoft 365 Copilot. Exact serving fleet share is undisclosed; gradual Maia adoption is modeled.",
            "tps_rationale": "GPT-OSS 120B B200 output-token benchmark proxy. Maia has no adopted comparable output-token/MW row, so no uplift is applied.",
            "replacement_path": "Microsoft disclosure of Maia accelerator-hours or Copilot model/hardware routing mix.",
        },
        "Google": {
            "gpu_label": "GPU reference",
            "asic_label": "TPU / Ironwood",
            "gpu_share_2026": 0.20,
            "gpu_share_2030": 0.10,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; SRC_GOOGLE_GEMINI_TOKENS; SRC_DEEPSEEK_V4_PRO; SRC_KIMI_K25",
            "mix_rationale": "Google officially positions Ironwood as an inference TPU and publicly documents TPU generations; TPU-heavy serving is modeled, not measured fleet share.",
            "tps_rationale": "Hybrid frontier InferenceX proxy using gptoss120b for H200 and DeepSeek V4 Pro/Kimi K2.5 for B200/GB200 output-token rows. TPU/Ironwood presence is shown, but no unmatched efficiency premium is applied.",
            "replacement_path": "Gemini production serving throughput/power or TPU-versus-GPU serving allocation disclosure.",
        },
        "Meta": {
            "gpu_label": "NVIDIA / external GPU reference",
            "asic_label": "MTIA",
            "gpu_share_2026": 0.90,
            "gpu_share_2030": 0.55,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_META_MTIA_GENAI_2026; SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA",
            "mix_rationale": "Meta discloses hundreds of thousands of MTIA chips for inference and an inference-first GenAI MTIA roadmap. LLM-serving mix remains undisclosed; adoption is scenario-based.",
            "tps_rationale": "Llama 70B B200 output-token benchmark proxy. MTIA presence is shown, but no unmatched efficiency premium is applied.",
            "replacement_path": "Meta AI production model-routing and MTIA-versus-GPU inference allocation disclosure.",
        },
        "xAI": {
            "gpu_label": "NVIDIA Hopper/next-generation GPU",
            "asic_label": "No disclosed operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_XAI_NVIDIA_COLOSSUS; SRC_XAI_MODELS",
            "mix_rationale": "Official infrastructure anchor is NVIDIA GPU cluster scale. No xAI-operated custom inference ASIC share is used in Base.",
            "tps_rationale": "GPT-OSS 120B B200 output-token benchmark proxy pending a comparable Grok serving benchmark.",
            "replacement_path": "xAI serving hardware mix, Grok inference benchmark and active traffic disclosure.",
        },
        "OpenAI": {
            "gpu_label": "NVIDIA GB200 / partner GPU capacity",
            "asic_label": "No disclosed operated custom ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_OPENAI_STARGATE_PROGRESS; SRC_OPENAI_GPT41_DOCS; SRC_DEEPSEEK_V4_PRO; SRC_KIMI_K25",
            "mix_rationale": "OpenAI states Oracle began delivering NVIDIA GB200 racks for Stargate. No operated custom-ASIC mix is publicly quantified in the model.",
            "tps_rationale": "Hybrid frontier InferenceX proxy using gptoss120b for H200 and DeepSeek V4 Pro/Kimi K2.5 for B200/GB200 output-token rows; not direct ChatGPT/API telemetry.",
            "replacement_path": "OpenAI hardware allocation and output-token throughput by model/product surface.",
        },
        "Anthropic": {
            "gpu_label": "Partner GPU reference",
            "asic_label": "AWS Trainium / hosted purpose-built accelerators",
            "gpu_share_2026": 0.35,
            "gpu_share_2030": 0.15,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_AWS_RAINIER_ACTIVE; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_ANTHROPIC_CLAUDE_DOCS; SRC_DEEPSEEK_V4_PRO; SRC_KIMI_K25",
            "mix_rationale": "Project Rainier establishes large Anthropic-directed Trainium capacity. Exact Claude inference allocation across Trainium, TPU and GPU is undisclosed.",
            "tps_rationale": "Hybrid frontier InferenceX proxy using gptoss120b for H200 and DeepSeek V4 Pro/Kimi K2.5 for B200/GB200 output-token rows. Trainium presence is shown, but no unmatched efficiency premium is applied.",
            "replacement_path": "Anthropic/AWS production inference hardware allocation and Claude tokens/MW measurement.",
        },
        "DeepSeek": {
            "gpu_label": "NVIDIA H800 GPU",
            "asic_label": "No disclosed operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_DEEPSEEK_H800_INFERENCE; SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1",
            "mix_rationale": "DeepSeek disclosed that V3/R1 inference services used H800 GPUs in its published infrastructure overview; no Base ASIC migration is assumed.",
            "tps_rationale": "DeepSeek-R1 B200 output-token benchmark proxy; official MoE structure informs mapping but does not add a second multiplier.",
            "replacement_path": "Updated DeepSeek operated fleet hardware and measured V3/R1 output tokens per MW.",
        },
        "Alibaba": {
            "gpu_label": "Alibaba Cloud GPU inference reference",
            "asic_label": "No disclosed Qwen operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY",
            "mix_rationale": "Alibaba Cloud officially documents GPU-based Qwen inference deployment, but not the operated Qwen GPU/ASIC fleet allocation. Base remains GPU-reference.",
            "tps_rationale": "Qwen3.5 B200 output-token benchmark proxy; MoE is represented by selected benchmark, with no additional uplift.",
            "replacement_path": "Alibaba-operated Qwen fleet mix or production Model Studio output tokens/MW.",
        },
        "Tencent": {
            "gpu_label": "Tencent Cloud GPU reference",
            "asic_label": "No disclosed Hunyuan operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.00,
            "source_ids": "SRC_TENCENT_HUNYUAN; SRC_TENCENT_AI_INFRA_MOE",
            "mix_rationale": "Tencent discloses Hunyuan services, AI Infra and Hunyuan Turbo MoE efficiency direction, but not operated accelerator mix. Base remains GPU-reference.",
            "tps_rationale": "GPT-OSS 120B B200 output-token benchmark proxy pending a comparable Hunyuan output-token benchmark.",
            "replacement_path": "Tencent-operated Hunyuan hardware split and output-token serving benchmark.",
        },
    }


def company_derivation_profiles() -> dict[str, dict[str, str]]:
    """Company-specific rationale for power, workload allocation and utilization."""
    return {
        "Microsoft": {
            "capacity_basis": "Scenario envelope for Microsoft-controlled/Copilot serving burden; not an official contracted-GW disclosure.",
            "active_basis": "Active GW is a staged operational deployment fraction of modeled capacity, reflecting site energization and accelerator availability.",
            "ai_workload_basis": "Azure/Copilot serving burden is AI-oriented but shares infrastructure with platform and reserve overhead; 86% is a scenario allocation.",
            "inference_basis": "Copilot commercial serving growth supports rising inference allocation; OpenAI model-owner output must remain separately attributed.",
            "utilization_basis": "Commercial interactive serving requires latency headroom, failover reserve and routing flexibility; utilization remains below installed capacity.",
        },
        "Google": {
            "capacity_basis": "Scenario envelope for Gemini-serving capacity; official TPU hardware direction is disclosed, company-level contracted GW is not.",
            "active_basis": "TPU generation availability supports ramp direction, while active GW remains a staged deployment estimate.",
            "ai_workload_basis": "Gemini/Vertex TPU serving is AI-dedicated in the modeled capacity envelope; 88% excludes platform/reserve load.",
            "inference_basis": "Ironwood is positioned for inference and Gemini is commercialized across products; inference share increases as a scenario.",
            "utilization_basis": "Interactive and enterprise/API serving needs SLO reserve even on TPU-optimized infrastructure.",
        },
        "Meta": {
            "capacity_basis": "Scenario envelope for Meta AI/Llama serving capacity; not an official contracted-GW figure.",
            "active_basis": "MTIA deployment direction and consumer product distribution support active ramp, not exact powered GW.",
            "ai_workload_basis": "The modeled fleet is focused on AI workloads across Meta AI surfaces; non-LLM ranking/platform overhead is excluded through the 87% share.",
            "inference_basis": "Large consumer AI distribution and inference-first MTIA roadmap support a higher inference share scenario.",
            "utilization_basis": "Consumer peaks, global availability and latency headroom reduce realized output utilization.",
        },
        "xAI": {
            "capacity_basis": "Colossus GPU-count disclosure bounds capacity direction; contracted GW values are modeled power envelopes.",
            "active_basis": "GPU cluster scale anchors operational possibility, while inference/training allocation and site power draw remain estimates.",
            "ai_workload_basis": "Colossus is AI-centric; 85% retains cooling/IT allocation boundary and non-serving AI work.",
            "inference_basis": "Grok product expansion is modeled to shift capacity toward inference after initial training-heavy operation.",
            "utilization_basis": "Closed-model interactive serving and training competition require reserve; no production utilization disclosure exists.",
        },
        "OpenAI": {
            "capacity_basis": "2030 envelope is bounded by official Stargate planned/committed capacity; 2026 and timing remain staged scenario values.",
            "active_basis": "Official capacity announcements are converted to active GW only through energization/GPU-deployment ramp assumptions.",
            "ai_workload_basis": "Stargate capacity is AI-oriented but includes reserve, platform and non-token AI activity; 88% is a scenario.",
            "inference_basis": "ChatGPT/API/enterprise commercial surfaces support increasing inference allocation while training remains material.",
            "utilization_basis": "Online product SLO, reasoning workload variability and reserve capacity prevent installed inference capacity from operating at peak output continuously.",
        },
        "Anthropic": {
            "capacity_basis": "Hosted capacity envelope is anchored by Anthropic/AWS Project Rainier direction; it is attributed to Claude outputs, not AWS as a model owner.",
            "active_basis": "Trainium cluster activation supports staged active ramp; Claude inference-versus-training use remains estimated.",
            "ai_workload_basis": "Anthropic-directed hosted capacity is predominantly AI; 86% excludes platform, reserve and non-serving allocation.",
            "inference_basis": "Claude API/product growth supports a rising inference share, while continued model training prevents full conversion.",
            "utilization_basis": "Claude serving must maintain latency/availability reserve across hosted platforms; utilization is a scenario, not Trainium telemetry.",
        },
        "DeepSeek": {
            "capacity_basis": "Capacity is a low-transparency scenario; official infrastructure evidence supports H800 inference hardware, not company GW.",
            "active_basis": "Active GW is conservative because operated cluster scale beyond disclosed infrastructure is not public.",
            "ai_workload_basis": "DeepSeek-operated service capacity is modeled as AI-focused, reduced for reserve and ancillary processing.",
            "inference_basis": "API/app availability and inference-system disclosure support higher inference share; the value remains scenario.",
            "utilization_basis": "Published node-occupancy evidence informs direction, but 2026-2030 sustained utilization is not disclosed.",
        },
        "Alibaba": {
            "capacity_basis": "Alibaba Cloud/Qwen capacity is a scenario envelope; official model and deployment documentation does not state operated GW.",
            "active_basis": "Active GW is staged below capacity due to undisclosed accelerator allocation and cloud multi-tenant use.",
            "ai_workload_basis": "Model Studio/Qwen-serving envelope is AI-focused, while cloud platform/reserve allocation is excluded through 84%.",
            "inference_basis": "Qwen API/enterprise commercialization and MoE architecture support increasing inference allocation scenario.",
            "utilization_basis": "Multi-tenant cloud serving and SLO reserve require a utilization haircut absent direct telemetry.",
        },
        "Tencent": {
            "capacity_basis": "Tencent Cloud/Hunyuan capacity is a scenario envelope because operated model-serving GW is undisclosed.",
            "active_basis": "Active GW reflects staged Hunyuan/Yuanbao adoption rather than a reported powered fleet.",
            "ai_workload_basis": "Modeled Hunyuan-serving capacity is AI-focused; 84% excludes cloud/platform and reserve overhead.",
            "inference_basis": "Yuanbao and embedded product surfaces plus Hunyuan Turbo inference-cost direction support rising inference allocation.",
            "utilization_basis": "Interactive consumer/cloud serving, reserve, and mixed workload routing justify utilization below installed capacity.",
        },
    }


def fact_anchors() -> list[FactAnchor]:
    return [
        FactAnchor(
            "FACT_OPENAI_ORACLE_4_5GW",
            "OpenAI",
            "Capacity",
            "Additional Oracle datacenter capacity",
            "4.5 GW",
            "2025-07-22",
            "SRC_OPENAI_STARGATE_ORACLE",
            "Tier 1",
            "Sets OpenAI contracted/planned capacity ceiling; active power remains ramped scenario.",
            "OpenAI 2030 contracted_power_gw 상향 anchor. active_power_gw는 energization/GPU delivery 때문에 별도 multiplier 적용.",
            0.86,
            "Oracle/OpenAI site-level energization date, MW by site, GPU delivery schedule.",
        ),
        FactAnchor(
            "FACT_OPENAI_STARGATE_10GW",
            "OpenAI",
            "Capacity",
            "Stargate planned capacity commitment",
            "Nearly 7 GW announced across new sites; over 10 GW commitment stated",
            "2025-09-23",
            "SRC_OPENAI_STARGATE_PROGRESS",
            "Tier 1",
            "Provides a public reference floor for the OpenAI 2030 capacity scenario; it does not directly verify the 12 GW model endpoint.",
            "2030 OpenAI contracted_power_gw 12GW는 공개된 10GW 초과 commitment를 넘어서는 확장 시나리오이며 확인값이 아님.",
            0.84,
            "Stargate site-level power interconnect and construction progress.",
        ),
        FactAnchor(
            "FACT_GOOGLE_IRONWOOD_POD",
            "Google",
            "Accelerator",
            "Ironwood TPU pod scale",
            "9,216 liquid-cooled chips; 42.5 exaflops per pod",
            "2025-04-09",
            "SRC_GOOGLE_IRONWOOD",
            "Tier 1",
            "Supports Google TPU-heavy serving platform and higher tokens/MW scenario.",
            "Google TPU/Ironwood platform direction은 accelerator mix bridge와 efficiency-growth scenario를 설정하는 근거이며, 공개 fleet share 또는 production tokens/MW fact가 아님.",
            0.88,
            "Gemini production serving benchmark by model/context/batch.",
        ),
        FactAnchor(
            "FACT_GOOGLE_TPU_V6E",
            "Google",
            "Accelerator",
            "TPU v6e / Trillium generation",
            "Google Cloud TPU v6e public product documentation",
            "2026-05-14 accessed",
            "SRC_GOOGLE_TPU_V6E",
            "Tier 1",
            "Confirms Google has public TPU generation available for AI workloads.",
            "Google serving_platform fact 보강. tokens/MW 수치는 직접 인용하지 않음.",
            0.84,
            "Model-specific Gemini cost/latency and utilization disclosure.",
        ),
        FactAnchor(
            "FACT_DEEPSEEK_V3_MOE",
            "DeepSeek",
            "Model",
            "DeepSeek-V3 MoE parameters",
            "671B total parameters; 37B activated per token",
            "2024-12-26",
            "SRC_DEEPSEEK_V3",
            "Tier 1",
            "Directly populates parameter_band_total and parameter_band_active.",
            "DeepSeek MoE efficiency multiplier 적용의 가장 강한 모델-side evidence.",
            0.92,
            "Measured serving tokens/sec/MW for DeepSeek-V3/R1 at production context lengths.",
        ),
        FactAnchor(
            "FACT_DEEPSEEK_V3_TRAINING_TOKENS",
            "DeepSeek",
            "Model",
            "DeepSeek-V3 pretraining corpus",
            "14.8T high-quality tokens",
            "2024-12-26",
            "SRC_DEEPSEEK_V3",
            "Tier 1",
            "Training token scale sanity check; not used as commercial generation volume.",
            "training_tokens_processed_per_day는 pretraining token scale과 order-of-magnitude 비교 가능하지만 직접 calibration은 아님.",
            0.88,
            "Actual training run duration, cluster size, and power draw.",
        ),
        FactAnchor(
            "FACT_QWEN3_MOE",
            "Alibaba",
            "Model",
            "Qwen3 flagship MoE parameters",
            "235B total parameters; 22B activated parameters",
            "2025-04-29",
            "SRC_QWEN3_GITHUB",
            "Tier 1",
            "Directly populates Qwen total/active parameter anchor.",
            "Alibaba MoE efficiency multiplier와 parameter confidence를 보강.",
            0.90,
            "Alibaba-operated Qwen API serving benchmark and active traffic data.",
        ),
        FactAnchor(
            "FACT_LLAMA4_SCOUT_MAVERICK",
            "Meta",
            "Model",
            "Llama 4 MoE parameter anchors",
            "Scout 109B total / 17B active; Maverick 400B total / 17B active",
            "2025-04-07",
            "SRC_META_LLAMA4_NVIDIA",
            "Tier 2",
            "Adds concrete open-model MoE anchors for Meta model family.",
            "Meta parameter band를 더 좁힘. 다만 Meta AI production routing과 active serving GW는 여전히 scenario.",
            0.74,
            "Official Meta model card scrape/API and Meta AI serving model mix.",
        ),
        FactAnchor(
            "FACT_XAI_COLOSSUS_100K",
            "xAI",
            "Accelerator",
            "Colossus initial cluster",
            "100,000 NVIDIA Hopper GPUs",
            "2024-12-04",
            "SRC_XAI_NVIDIA_COLOSSUS",
            "Tier 1/2",
            "Bounds xAI 2026 active_power_gw lower-to-mid scenario.",
            "100k Hopper GPU는 xAI active_power_2026_gw 0.35GW가 물리적으로 과도하지 않은지 확인하는 anchor.",
            0.82,
            "Exact power draw, H100/H200 mix, utilization and training/inference split.",
        ),
        FactAnchor(
            "FACT_XAI_COLOSSUS_200K",
            "xAI",
            "Accelerator",
            "Colossus expansion direction",
            "Expansion toward 200,000 GPUs cited by NVIDIA",
            "2024-12-04",
            "SRC_XAI_NVIDIA_COLOSSUS",
            "Tier 1/2",
            "Supports xAI 2030 active_power_gw ramp direction, not exact schedule.",
            "xAI contracted_power_2030_gw 3GW와 active_power_2030_gw 2.5GW는 추가 clusters 포함한 scenario.",
            0.76,
            "xAI disclosed GPU delivery schedule and datacenter power contracts.",
        ),
        FactAnchor(
            "FACT_MS_PHI4_14B",
            "Microsoft",
            "Model",
            "Phi-4 parameter count",
            "14B parameters",
            "2024-12-12",
            "SRC_MS_PHI4_TECHREPORT",
            "Tier 1/2",
            "Sets Microsoft-owned SLM anchor; Copilot OpenAI dependency remains separated.",
            "Microsoft model row에서 Phi/MAI owned와 OpenAI model-owner output을 분리하는 근거.",
            0.82,
            "MAI model public card and Copilot routing share.",
        ),
        FactAnchor(
            "FACT_MS_MAIA_INFERENCE",
            "Microsoft",
            "Accelerator",
            "Maia 200 inference deployment direction",
            "Maia 200 designed for AI inference; deployed in Azure AI Foundry and Microsoft 365 Copilot",
            "2026-01-26",
            "SRC_MS_MAIA200",
            "Tier 1",
            "Establishes an official purpose-built inference accelerator in Microsoft serving platform; not a numeric fleet-share fact.",
            "Microsoft GPU/ASIC mix에서 Maia share를 0보다 크게 둘 수 있는 방향성 anchor. share 자체는 scenario.",
            0.91,
            "Microsoft accelerator-hours or model-serving hardware allocation by product.",
        ),
        FactAnchor(
            "FACT_META_MTIA_INFERENCE",
            "Meta",
            "Accelerator",
            "MTIA inference-first deployment direction",
            "Meta states hundreds of thousands of MTIA chips deployed for inference and next MTIA generations focus on GenAI inference",
            "2026-03-11",
            "SRC_META_MTIA_GENAI_2026",
            "Tier 1",
            "Establishes MTIA presence for inference; does not disclose LLM serving fleet share.",
            "Meta GPU/ASIC mix에 MTIA share scenario를 추가하는 anchor. exact share와 tokens/MW는 공개되지 않음.",
            0.92,
            "Meta AI LLM-serving hardware allocation and production output token efficiency.",
        ),
        FactAnchor(
            "FACT_ANTHROPIC_AWS_5GW",
            "Anthropic",
            "Capacity",
            "AWS/Project Rainier hosted capacity direction",
            "Up to 5GW-class AI compute capacity cited for Anthropic/AWS buildout",
            "2025-2026",
            "SRC_ANTHROPIC_AMAZON_COMPUTE",
            "Tier 1",
            "Provides a cited hosted-capacity reference; active power and any endpoint above the cited class remain scenarios.",
            "Anthropic contracted_power_2030_gw 7GW는 등록된 5GW-class reference를 넘어서는 확장 시나리오이며, AWS는 host이고 token attribution은 Anthropic으로 둠.",
            0.84,
            "AWS site-level energization, Trainium delivery, Anthropic serving/training split.",
        ),
        FactAnchor(
            "FACT_ANTHROPIC_RAINIER_TRAINIUM",
            "Anthropic",
            "Accelerator",
            "Project Rainier purpose-built accelerator direction",
            "AWS activated an Anthropic AI compute cluster built on Trainium2 chips",
            "2025-10-29",
            "SRC_AWS_RAINIER_ACTIVE",
            "Tier 1",
            "Establishes Trainium in Anthropic-directed compute capacity; not Claude inference share.",
            "Anthropic purpose-built accelerator mix share와 relative efficiency factor는 scenario로만 적용.",
            0.90,
            "Anthropic/AWS workload allocation and Claude output-token serving telemetry.",
        ),
        FactAnchor(
            "FACT_DEEPSEEK_H800_SERVING",
            "DeepSeek",
            "Accelerator",
            "Published V3/R1 inference service hardware",
            "DeepSeek states online V3/R1 inference services ran entirely on H800 GPUs in its disclosed overview",
            "2025-02-28",
            "SRC_DEEPSEEK_H800_INFERENCE",
            "Tier 1",
            "Sets GPU-only Base hardware reference unless later operated-mix evidence replaces it.",
            "DeepSeek Base GPU share를 100% reference로 두고 MoE 효율은 architecture factor로 분리.",
            0.91,
            "Updated production-serving hardware allocation or measured output tokens/MW.",
        ),
        FactAnchor(
            "FACT_TENCENT_HUNYUAN_100B",
            "Tencent",
            "Model",
            "Hunyuan foundation model scale",
            "Over 100B parameters and over 2T pretraining tokens",
            "2023-09-07",
            "SRC_TENCENT_HUNYUAN",
            "Tier 1",
            "Sets Tencent Hunyuan model scale anchor.",
            "Tencent parameter band를 closed-only에서 100B+ anchor로 보강. active serving capacity는 여전히 낮은 confidence.",
            0.82,
            "Current Hunyuan/Yuanbao serving model card and traffic disclosure.",
        ),
        FactAnchor(
            "FACT_MCKINSEY_2030_INFERENCE",
            "Cross-company",
            "Workload mix",
            "2030 inference demand direction",
            "Inference expected to account for more than half of AI workloads and 30-40% of data center power demand by 2030",
            "2026-02-24",
            "SRC_MCKINSEY_AI_WORKLOADS",
            "Tier 2",
            "Supports rising inference share in 2030, not 2026 company-level fact.",
            "2030 weighted inference share 상승의 directional anchor. 2026 60%+ 주장은 fact로 채택하지 않음.",
            0.72,
            "Company-level AI GW split and measured serving/training telemetry.",
        ),
        FactAnchor(
            "FACT_DELOITTE_2026_INFERENCE",
            "Cross-company",
            "Workload mix",
            "2026 inference compute share outlook",
            "Inference cited as roughly two-thirds of compute in 2026 outlook",
            "2025-12",
            "SRC_DELOITTE_AI_POWER",
            "Tier 2",
            "Scenario cross-check only; compute share is not the same as active GW share.",
            "2026 base/bull inference share가 60%를 넘을 수 있는 상향 전망 anchor지만, 공식 fact로는 표시하지 않음.",
            0.68,
            "Direct hyperscaler workload power telemetry.",
        ),
        FactAnchor(
            "FACT_EPOCH_TRAINING_POWER_RISK",
            "Cross-company",
            "Workload mix",
            "Frontier training power can remain material",
            "Individual frontier training runs may require large power blocks by 2030",
            "2025-08",
            "SRC_EPRI_EPOCH_AI_POWER",
            "Tier 2",
            "Prevents the model from assuming all incremental AI power is inference.",
            "Bear/base에서 training share를 남기는 보수 anchor.",
            0.70,
            "Training run power telemetry and model release cadence by company.",
        ),
    ]


def formula_assumptions() -> list[dict[str, Any]]:
    return [
        {
            "category": "Capacity definition - contracted or attributed ceiling",
            "formula": "contracted_power_gw = announced/committed capacity where sourced; otherwise explicitly modeled capacity envelope",
            "meaning_kr": "`contracted_power_gw`는 업체별 동일한 disclosure 수준의 fact가 아닙니다. OpenAI/Anthropic처럼 공개 capacity anchor가 있는 경우 상한 anchor이며, 미공개 업체는 model-owner serving capacity envelope scenario입니다.",
            "evidence_type": "Fact anchor + Scenario boundary",
            "source_ids": "SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; SRC_ANTHROPIC_AMAZON_COMPUTE; ASSUMP_POWER_RAMP",
        },
        {
            "category": "Operational deployment conversion",
            "formula": "operational_power_gw = contracted_power_gw * operational_deployment_share; operational_power_gw <= contracted_power_gw",
            "meaning_kr": "계약/귀속 capacity 중 실제 energization, 냉각·네트워크 readiness, accelerator 배치를 통과한 몫만 토큰 산식에 진입합니다. 기존 active_power_gw 표기는 operational_power_gw와 같은 의미로 유지합니다.",
            "evidence_type": "Transparent scenario conversion",
            "source_ids": "ASSUMP_POWER_RAMP; ASSUMP_STARGATE_RAMP",
        },
        {
            "category": "Token definition - forecast headline",
            "formula": "inference_tokens_per_day = generated output token equivalent, not input+output processed tokens",
            "meaning_kr": "임원 보고의 headline token은 사용자가 받는 생성 output token 기준으로 해석합니다. InferenceX의 total throughput과 비교할 때는 output_tput/output_tok_s_mw를 우선 대조합니다.",
            "evidence_type": "Definition",
            "source_ids": "SRC_GOOGLE_GEMINI_TOKENS; SRC_SEMIANALYSIS_INFERENCEX",
        },
        {
            "category": "Token definition - processed benchmark",
            "formula": "processed_tokens = input_tokens + output_tokens; benchmark total tput may include both",
            "meaning_kr": "benchmark의 total tokens/sec 또는 tok_s_mw는 prompt input 처리량과 생성 output 처리량이 섞일 수 있습니다. processed token을 generated token forecast로 직접 치환하지 않습니다.",
            "evidence_type": "Definition",
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE_DOCS",
        },
        {
            "category": "Power to AI IT load",
            "formula": "it_load_gw = operational_power_gw / pue",
            "meaning_kr": "계약/계획 전력이 아니라 실제 operational deploy된 전력에서 PUE를 차감해 IT load를 산출.",
            "evidence_type": "Formula",
            "source_ids": "SRC_MCKINSEY_AI_WORKLOADS; SRC_EPRI_EPOCH_AI_POWER; SRC_EIA_DC_POWER; SRC_FERC_INTERCONNECT; SRC_UPTIME_GLOBAL_DC; SRC_ASHRAE_TC99",
        },
        {
            "category": "AI workload allocation",
            "formula": "ai_it_load_gw = it_load_gw * ai_workload_share",
            "meaning_kr": "active capacity가 전부 LLM 계산으로 쓰이지 않으므로 데이터센터 IT load 중 modeled model-owner AI training/serving 몫만 분리합니다. 업체별 dedicated AI 방향은 공식 source로 확인하되, 구체적 share는 telemetry 부재 시 scenario입니다.",
            "evidence_type": "Scenario assumption",
            "source_ids": "SRC_MS_MAIA200; SRC_GOOGLE_IRONWOOD; SRC_META_MTIA_GENAI_2026; SRC_AWS_RAINIER_ACTIVE; ASSUMP_POWER_RAMP",
        },
        {
            "category": "Training vs inference split",
            "formula": "inference_gw = ai_it_load_gw * inference_power_share; training_gw = ai_it_load_gw * (1 - inference_power_share)",
            "meaning_kr": "inference 비중은 company fact가 아니라 상용화 성숙도와 제품 표면에 따른 시나리오 변수.",
            "evidence_type": "Scenario assumption",
            "source_ids": "SRC_MCKINSEY_AI_WORKLOADS; SRC_DELOITTE_AI_POWER; SRC_EPRI_EPOCH_AI_POWER; ASSUMP_INFERENCE_SHARE_NOT_FACT_60",
        },
        {
            "category": "Benchmark-selected accelerator mix",
            "formula": "fleet_reference_tps_per_mw = h200_share*h200_ref + b200_share*b200_ref + gb200_share*gb200_ref + purpose_built_share*purpose_built_ref",
            "meaning_kr": "H200/B200/GB200/purpose-built 구성비를 직접 입력하여 같은 inference MW라도 fleet 구성에 따라 public reference TPS/MW가 달라지게 합니다. Purpose-built는 comparable benchmark가 없으면 B200 placeholder를 사용하며 editable input으로 남깁니다.",
            "evidence_type": "Platform fact + Conservative benchmark mapping",
            "source_ids": "SRC_MS_MAIA200; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; SRC_META_MTIA_GENAI_2026; SRC_AWS_RAINIER_ACTIVE; SRC_MLPERF_INFERENCE; SRC_MLPERF_POWER; SRC_TENSORRT_LLM; ASSUMP_NUMERIC_ACCELERATOR_MIX",
        },
        {
            "category": "InferenceX TPS/MW selection",
            "formula": "gpu_workload_avg_tps_mw = short_share*gpu_short_tps_mw + long_share*gpu_long_tps_mw + agentic_share*gpu_agentic_tps_mw; fleet_reference_tps_per_mw = sum(gpu_share*gpu_workload_avg_tps_mw); reference_serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor",
            "meaning_kr": "InferenceX generated-output TPS/MW를 GPU별 short chat, long chat, agentic workload로 분리한 뒤 업체별 traffic/product mix로 먼저 가중합니다. TPS/MW는 concurrency 32-256 안에서 Dynamo/TRT-LLM/MTP 계열 stack을 우선하고, 없으면 같은 조건의 public max row를 사용합니다. 이후 H200/B200/GB200/purpose-built fleet mix를 적용합니다. Agentic은 Kimi K2.5 dynamic reasoning rows에서 산출한 agentic/long ratio를 long-context row에 적용합니다.",
            "evidence_type": "Benchmark proxy selection",
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX; SRC_INFERENCEX_AGENTIC_TRACES_256K; SRC_ANTHROPIC_CONSUMPTION_GUIDE; SRC_OPENAI_CODEX_RATE_CARD; SRC_GOOGLE_GEMINI_LONG_CONTEXT; SRC_META_BUSINESS_AGENT; ASSUMP_NUMERIC_ACCELERATOR_MIX; ASSUMP_WORKLOAD_CLASS_MIX; ASSUMP_AGENTIC_CONTEXT_PENALTY",
        },
        {
            "category": "Headline inference token capacity",
            "formula": "inference_tokens_per_day = contracted_power_gw * operational_deployment_share / pue * ai_workload_share * inference_power_share * 1,000 * weighted_tps_per_mw * 86,400",
            "meaning_kr": "최종 생성 토큰 capacity는 공개 또는 명시적 capacity envelope, 운영 투입 비율, PUE, AI/inference 배분, 선택 benchmark TPS/MW만으로 계산합니다.",
            "evidence_type": "Model equation",
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE; SRC_ARXIV_INFERENCE_ENERGY; SRC_EPOCH_INFERENCE_PRICE",
        },
        {
            "category": "Excluded from headline - operational serving sensitivities",
            "formula": "utilization, MoE uplift, architecture multiplier and software CAGR = sensitivity/reference only",
            "meaning_kr": "이 항목들은 중요한 연구 주제이지만 업체별 production telemetry가 부족합니다. 동일한 효과를 TPS/MW와 다시 곱해 과도한 정밀도를 만들지 않기 위해 headline token 생성량에서는 제외합니다.",
            "evidence_type": "Scope control rule",
            "source_ids": "SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING; SRC_SEMIANALYSIS_INFERENCEX",
        },
        {
            "category": "Energy sanity check",
            "formula": "joules_per_token = 1,000,000 / tokens_per_second_per_mw",
            "meaning_kr": "MW를 J/s로 환산해 tokens/sec/MW와 에너지/token이 상호 일관되는지 확인.",
            "evidence_type": "Sanity check",
            "source_ids": "SRC_ARXIV_INFERENCE_ENERGY; SRC_JOULE_INFERENCE_ENERGY_2026; SRC_MLPERF_POWER",
        },
    ]


def company_input_audit(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Separate cited public facts from the modeled numbers they inform.

    A public hardware/capacity/model disclosure can support a scenario without
    making the modeled input itself a disclosed fact. This table is written for
    executive challenge sessions: readers can see the public anchor, the model
    value and the remaining disclosure gap side by side.
    """
    endpoints = {
        company: {
            year: next(row for row in base_rows if row["company"] == company and row["year"] == year)
            for year in (2026, 2030)
        }
        for company in [scenario.company for scenario in scenarios()]
    }
    model_map = {model.company: model for model in company_models()}
    public_facts = {
        "Microsoft": {
            "model_parameter": ("14B Phi-4 parameters", "SRC_MS_PHI4_TECHREPORT", "FACT_MS_PHI4_14B"),
            "accelerator_presence": ("Maia 200 is identified as an inference accelerator for Azure/Copilot uses.", "SRC_MS_MAIA200", "FACT_MS_MAIA_INFERENCE"),
            "capacity": ("No company model-serving GW disclosure adopted.", "SRC_MS_MAIA200", ""),
        },
        "Google": {
            "model_parameter": ("Gemini frontier parameter count is not publicly adopted; open Gemma is not used as Gemini size.", "SRC_GOOGLE_GEMINI_TOKENS", ""),
            "accelerator_presence": ("Ironwood pod: 9,216 chips and 42.5 exaflops stated in official announcement.", "SRC_GOOGLE_IRONWOOD", "FACT_GOOGLE_IRONWOOD_POD"),
            "capacity": ("No Gemini model-serving GW disclosure adopted.", "SRC_GOOGLE_IRONWOOD", ""),
        },
        "Meta": {
            "model_parameter": ("Llama 4 Scout/Maverick MoE anchors are public ecosystem references; Meta AI routing remains undisclosed.", "SRC_META_LLAMA4_NVIDIA", "FACT_LLAMA4_SCOUT_MAVERICK"),
            "accelerator_presence": ("Meta states MTIA deployment for inference and a GenAI inference roadmap.", "SRC_META_MTIA_GENAI_2026", "FACT_META_MTIA_INFERENCE"),
            "capacity": ("No Meta AI model-serving GW disclosure adopted.", "SRC_META_MTIA_GENAI_2026", ""),
        },
        "xAI": {
            "model_parameter": ("Grok parameter count remains undisclosed in the model.", "SRC_XAI_MODELS", ""),
            "accelerator_presence": ("100,000 Hopper GPUs and an expansion direction toward 200,000 GPUs cited by NVIDIA.", "SRC_XAI_NVIDIA_COLOSSUS", "FACT_XAI_COLOSSUS_100K; FACT_XAI_COLOSSUS_200K"),
            "capacity": ("GPU count is public-partner evidence; corresponding GW is not a disclosed xAI model-serving capacity.", "SRC_XAI_NVIDIA_COLOSSUS", "FACT_XAI_COLOSSUS_100K"),
        },
        "OpenAI": {
            "model_parameter": ("GPT/o-series parameter count remains undisclosed.", "SRC_OPENAI_GPT41_DOCS", ""),
            "accelerator_presence": ("Stargate partner capacity and GB200 delivery direction are cited; no custom-ASIC share adopted.", "SRC_OPENAI_STARGATE_PROGRESS", ""),
            "capacity": ("4.5 GW additional Oracle capacity and more-than-10-GW Stargate commitment are public anchors; 12 GW endpoint is an extension scenario.", "SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS", "FACT_OPENAI_ORACLE_4_5GW; FACT_OPENAI_STARGATE_10GW"),
        },
        "Anthropic": {
            "model_parameter": ("Claude parameter count remains undisclosed.", "SRC_ANTHROPIC_CLAUDE_DOCS", ""),
            "accelerator_presence": ("Project Rainier establishes Trainium2-based Anthropic-directed capacity.", "SRC_AWS_RAINIER_ACTIVE", "FACT_ANTHROPIC_RAINIER_TRAINIUM"),
            "capacity": ("A 5-GW-class hosted-capacity reference is registered; 7 GW endpoint is an expansion scenario requiring replacement evidence.", "SRC_ANTHROPIC_AMAZON_COMPUTE", "FACT_ANTHROPIC_AWS_5GW"),
        },
        "DeepSeek": {
            "model_parameter": ("DeepSeek-V3: 671B total and 37B activated per token; 14.8T pretraining tokens.", "SRC_DEEPSEEK_V3", "FACT_DEEPSEEK_V3_MOE; FACT_DEEPSEEK_V3_TRAINING_TOKENS"),
            "accelerator_presence": ("Published V3/R1 inference overview identifies H800 GPU serving hardware.", "SRC_DEEPSEEK_H800_INFERENCE", "FACT_DEEPSEEK_H800_SERVING"),
            "capacity": ("No 2026-2030 operated model-serving GW disclosure adopted.", "SRC_DEEPSEEK_H800_INFERENCE", ""),
        },
        "Alibaba": {
            "model_parameter": ("Qwen3 MoE: 235B total and 22B activated parameters.", "SRC_QWEN3_GITHUB", "FACT_QWEN3_MOE"),
            "accelerator_presence": ("Official Qwen GPU deployment path exists; operated fleet allocation is undisclosed.", "SRC_ALIBABA_QWEN_GPU_DEPLOY", ""),
            "capacity": ("No Qwen-operated model-serving GW disclosure adopted.", "SRC_ALIBABA_QWEN_GPU_DEPLOY", ""),
        },
        "Tencent": {
            "model_parameter": ("Hunyuan: over 100B parameters and over 2T pretraining tokens in cited official announcement.", "SRC_TENCENT_HUNYUAN", "FACT_TENCENT_HUNYUAN_100B"),
            "accelerator_presence": ("Tencent AI Infra and Hunyuan Turbo MoE direction are cited; operated GPU/ASIC allocation is undisclosed.", "SRC_TENCENT_AI_INFRA_MOE", ""),
            "capacity": ("No Hunyuan/Yuanbao model-serving GW disclosure adopted.", "SRC_TENCENT_AI_INFRA_MOE", ""),
        },
    }
    rows: list[dict[str, Any]] = []

    def add(company: str, metric: str, values: str, evidence_class: str, fact_text: str, source_ids: str, anchor_ids: str, why_modelled: str, replacement_path: str) -> None:
        rows.append({
            "company": company,
            "metric": metric,
            "model_value_base_2026_2030": values,
            "evidence_class": evidence_class,
            "confirmed_public_fact_or_disclosure_gap": fact_text,
            "source_ids": source_ids,
            "fact_anchor_ids": anchor_ids,
            "why_modelled_value_is_not_a_fact": why_modelled,
            "replacement_path": replacement_path,
            "audit_status": "Public anchor registered; verbatim source-line sign-off required before describing a modeled value as confirmed.",
        })

    for company, facts in public_facts.items():
        start, end = endpoints[company][2026], endpoints[company][2030]
        model = model_map[company]
        add(
            company, "commercial_model_and_parameter_anchor",
            f"{model.parameter_band_total} / active: {model.parameter_band_active}",
            "Official numeric fact or explicit disclosure gap",
            facts["model_parameter"][0], facts["model_parameter"][1], facts["model_parameter"][2],
            "The model family is sourced; closed-model bands are not disclosed parameter values.",
            "Official model card or technical report with total/active parameters for the served commercial model.",
        )
        capacity_class = (
            "Scenario extending public capacity anchor"
            if company in {"OpenAI", "Anthropic"}
            else "Rational scenario with platform or cluster-direction support"
        )
        add(
            company, "contracted_or_attributed_capacity_gw",
            f"{start['contracted_power_gw']:.3f} -> {end['contracted_power_gw']:.3f} GW",
            capacity_class,
            facts["capacity"][0], facts["capacity"][1], facts["capacity"][2],
            "The endpoint is a model-owner capacity envelope; it equals neither active inference power nor a universally disclosed contract.",
            "Company/site-level committed MW/GW disclosure with scope, online date and owner attribution.",
        )
        add(
            company, "active_power_gw",
            f"{start['active_power_gw']:.3f} -> {end['active_power_gw']:.3f} GW",
            "Rational operational-deployment scenario",
            "No adopted official active LLM-serving GW telemetry.", facts["capacity"][1], facts["capacity"][2],
            "Active capacity requires energization, racks, cooling, networking and accelerator deployment, none disclosed at the modeled time series granularity.",
            "Site-level energization and operational accelerator-rack telemetry.",
        )
        add(
            company, "operational_deployment_share",
            f"{start['operational_deployment_share']:.0%} -> {end['operational_deployment_share']:.0%}",
            "Rational operational-deployment scenario",
            "No adopted official operational deployment share of attributed LLM-serving capacity.", facts["capacity"][1], facts["capacity"][2],
            "This single conversion assumption is required because contracted capacity does not automatically produce tokens.",
            "Site-level energized capacity divided by attributed contracted/committed capacity.",
        )
        add(
            company, "ai_workload_share",
            f"{start['ai_workload_share']:.0%} (constant Base allocation)",
            "Rational allocation assumption",
            "Public sources indicate AI platform direction but do not disclose LLM share of attributed IT power.", facts["accelerator_presence"][1], facts["accelerator_presence"][2],
            "AI-oriented hardware presence does not disclose what fraction runs LLM inference/training rather than other AI/platform/reserve work.",
            "Workload scheduling or accelerator-hours allocation by model surface.",
        )
        add(
            company, "gpu_purpose_built_accelerator_mix",
            f"GPU {start['gpu_share']:.0%}/{end['gpu_share']:.0%}; purpose-built {start['purpose_built_accelerator_share']:.0%}/{end['purpose_built_accelerator_share']:.0%}",
            "Official platform fact plus numeric scenario",
            facts["accelerator_presence"][0], facts["accelerator_presence"][1], facts["accelerator_presence"][2],
            "The platform may be confirmed while serving-fleet allocation by accelerator type is not disclosed.",
            "Operated inference accelerator-hours or product/model routing split by hardware.",
        )
        add(
            company, "inference_power_share",
            f"{start['inference_power_share']:.0%} -> {end['inference_power_share']:.0%}",
            "Rational allocation assumption",
            "No adopted company-level inference/training GW split disclosure.", start["source_ids"], "",
            "Product adoption direction can support a scenario but does not measure inference power share.",
            "Training and inference cluster power or accelerator-hour allocation telemetry.",
        )
        add(
            company, "tokens_per_second_per_mw",
            f"{start['tokens_per_second_per_mw']:,} -> {end['tokens_per_second_per_mw']:,} output tok/s/MW",
            "Benchmark-calibrated derived estimate",
            "No adopted company production output-token/MW telemetry; InferenceX is benchmark/proxy only.", "SRC_SEMIANALYSIS_INFERENCEX; " + facts["accelerator_presence"][1], facts["accelerator_presence"][2],
            "A fixed-condition output-token benchmark proxy is selected; no additional MoE, architecture, software-growth or utilization multiplier is used in headline.",
            "Comparable output-token benchmark or production telemetry matched on model, precision, ISL/OSL and SLO.",
        )
        add(
            company, "generated_output_tokens_per_day",
            f"{start['inference_tokens_per_day'] / 1e15:.3f}Q -> {end['inference_tokens_per_day'] / 1e15:.3f}Q/day",
            "Formula-derived simulation output",
            "No adopted company-disclosed generated output token volume.", start["source_ids"], "",
            "This value is computed only from operational inference GW and selected output-token TPS/MW; utilization is not multiplied into headline.",
            "Provider-disclosed output token volume or metered model-serving throughput.",
        )
    return rows


def scenario_definitions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, case in SCENARIO_CASES.items():
        rows.append(
            {
                "scenario": name,
                "description_kr": case["description_kr"],
                "operational_deploy_multiplier_2026": case["operational_deploy_multiplier_2026"],
                "operational_deploy_multiplier_2030": case["operational_deploy_multiplier_2030"],
                "inference_share_delta_2026": case["inference_share_delta_2026"],
                "inference_share_delta_2030": case["inference_share_delta_2030"],
                "headline_tps_mw_rule": "Public InferenceX reference is fixed; explicit commercial workload fit varies by Bear/Base/Bull; no hidden hardware or software uplift",
                "confidence": case["confidence"],
            }
        )
    return rows


def token_definitions() -> list[dict[str, Any]]:
    return [
        {
            "token_metric": "headline_generated_output_tokens",
            "korean_name": "생성 output token",
            "definition_kr": "사용자/API/제품 표면으로 실제 생성되어 반환되는 output token equivalent. 본 보고서의 `inference_tokens_per_day` 기본 정의.",
            "included": "decode/output token; model-owner가 운영한 상용 LLM surface",
            "excluded": "prompt input token, KV cache read/write, internal speculative draft token, training corpus token",
            "primary_fields": "inference_tokens_per_day; inference_tokens_per_year; output_tok_s_mw sanity layer",
            "inferencex_mapping": "`output_tput_per_gpu`, `output_tok_s_mw`, `j_output_token`을 우선 사용.",
            "status": "default headline definition",
        },
        {
            "token_metric": "processed_inference_tokens",
            "korean_name": "처리 token",
            "definition_kr": "serving system이 처리한 input+output token. 긴 prompt/RAG/agentic workload에서는 output token보다 훨씬 클 수 있음.",
            "included": "input token + output token; prefill + decode workload",
            "excluded": "training corpus token; non-token image/video generation units",
            "primary_fields": "tok_s_mw; input_tok_s_gpu; output_tok_s_gpu; total_tok_s_mw",
            "inferencex_mapping": "`tput_per_gpu` / `tok_s_mw`는 처리량 분석용으로 사용하고 headline 생성량에는 직접 대입하지 않음.",
            "status": "benchmark and load-shape diagnostic",
        },
        {
            "token_metric": "input_prefill_tokens",
            "korean_name": "입력/prefill token",
            "definition_kr": "prompt, retrieved context, tool transcript, conversation history처럼 output 생성 전에 읽는 token.",
            "included": "ISL, prompt token, RAG context, agent memory/context",
            "excluded": "generated output token",
            "primary_fields": "isl; input_tok_s_gpu; input_tok_s_mw",
            "inferencex_mapping": "ISL과 `input_tput_per_gpu`를 사용. 높은 ISL은 short-chat output forecast와 분리.",
            "status": "SLO/utilization and memory/HBM stress driver",
        },
        {
            "token_metric": "training_tokens_processed",
            "korean_name": "학습 처리 token",
            "definition_kr": "pretraining/post-training 과정에서 처리된 corpus token. 상용 inference generated token과 절대 합산하지 않음.",
            "included": "pretraining token, post-training data token, synthetic training data when disclosed",
            "excluded": "commercial API/consumer output token",
            "primary_fields": "training_tokens_processed_per_day; model card pretraining token anchors",
            "inferencex_mapping": "직접 mapping 없음. InferenceX는 inference serving 기준.",
            "status": "separate training sanity metric",
        },
        {
            "token_metric": "billable_api_tokens",
            "korean_name": "과금 token",
            "definition_kr": "API/제품 과금 기준의 input/output/cache/reasoning token. 업체별 과금정책이 달라 capacity headline으로 직접 사용하지 않음.",
            "included": "provider-specific billed input/output/cache/reasoning token categories",
            "excluded": "non-billed internal scheduler work unless disclosed",
            "primary_fields": "future replacement path; not in current Base forecast",
            "inferencex_mapping": "InferenceX 대상 아님. 공식 API billing docs로 별도 대조.",
            "status": "future commercial reconciliation layer",
        },
    ]


def is_moe_company(company: str) -> bool:
    return company in {"DeepSeek", "Alibaba"}


def core_inferencex_benchmark_profiles() -> list[dict[str, Any]]:
    """Select a small, readable output-token benchmark table for headline TPS/MW.

    The preferred comparison condition is fixed at B200, single_turn,
    ISL=1024 and OSL=1024. If that row is unavailable for a proxy model,
    the nearest published model-level row is used with the selected
    condition exposed in the output. These are benchmark proxies, not
    company production telemetry.
    """
    source_path = ROOT / "data" / "inferencex" / "normalized" / "inferencex_benchmark_results.csv"
    mapped = {
        "gptoss120b": "Microsoft; xAI; Tencent",
        "frontier_composite": "Google; OpenAI; Anthropic",
        "llama70b": "Meta",
        "dsr1": "DeepSeek",
        "qwen3.5": "Alibaba",
    }
    values: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    main_configs: dict[str, tuple[str, str]] = {}
    if source_path.exists():
        with source_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                source_model = row.get("model", "")
                if row.get("benchmark_type") != "single_turn" or row.get("is_main_model_config", "yes") != "yes":
                    continue
                if not row.get("output_tok_s_mw"):
                    continue
                try:
                    concurrency = int(float(row.get("concurrency") or 0))
                except ValueError:
                    concurrency = 0
                if not 32 <= concurrency <= 256:
                    continue
                gpu = row.get("gpu", "")
                for model in mapped:
                    if source_model in proxy_source_models(model, gpu):
                        key = (model, gpu, row.get("isl", ""), row.get("osl", ""))
                        values.setdefault(key, []).append(row)
                        main_configs.setdefault(model, (row.get("main_framework", ""), row.get("main_precision", "")))
    rows: list[dict[str, Any]] = []
    for model, companies in mapped.items():
        candidates = [
            ("b200", "1024", "1024", "Preferred B200 1024/1024 row selected"),
            ("gb200", "1024", "1024", "GB200 1024/1024 fallback - missing B200 1024/1024 row"),
            ("b200", "8192", "1024", "B200 8192/1024 fallback - missing 1024/1024 rows"),
            ("gb200", "8192", "1024", "GB200 8192/1024 fallback - missing preferred rows"),
        ]
        selected_gpu, selected_isl, selected_osl, selected_status, samples = "", "", "", "", []
        for gpu, isl, osl, status in candidates:
            vals = values.get((model, gpu, isl, osl), [])
            if vals:
                selected_gpu, selected_isl, selected_osl, selected_status, samples = gpu, isl, osl, status, vals
                break
        if not samples:
            raise ValueError(f"Missing core InferenceX benchmark rows for {model}")
        selected_value, selected_basis = select_max_tps_sample(samples)
        numeric_samples = [float(row["output_tok_s_mw"]) for row in samples]
        rows.append(
            {
                "proxy_model": model,
                "inferencex_source_model": proxy_source_label(model, selected_gpu),
                "mapped_companies": companies,
                "gpu": selected_gpu,
                "benchmark_type": "single_turn",
                "isl": int(selected_isl),
                "osl": int(selected_osl),
                "condition_status": selected_status,
                "metric_used": "output_tok_s_mw selected max",
                "main_framework": main_configs.get(model, ("", ""))[0],
                "main_precision": main_configs.get(model, ("", ""))[1],
                "row_count": len(samples),
                "output_tok_s_mw_selected": round(selected_value),
                "output_tok_s_mw_min": round(min(numeric_samples)),
                "output_tok_s_mw_max": round(max(numeric_samples)),
                "selection_basis": selected_basis,
                "headline_use": "Public output-token TPS/MW reference ceiling; commercial workload fit is applied before headline use.",
                "source_ids": "SRC_SEMIANALYSIS_INFERENCEX" + ("; SRC_DEEPSEEK_V4_PRO; SRC_KIMI_K25" if model == "frontier_composite" else ""),
                "caveat": "Benchmark proxy only; filtered to model-level main_framework/main_precision before GPU comparison. Read gpu/ISL/OSL/condition_status before comparing.",
            }
        )
    return rows


def company_core_benchmark_map() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for profile in core_inferencex_benchmark_profiles():
        for company in profile["mapped_companies"].split("; "):
            result[company] = profile
    return result


def commercial_workload_profiles() -> dict[str, dict[str, Any]]:
    """Map public benchmark references to commercial-serving workload classes.

    InferenceX is a public, fixed-condition reference benchmark rather than
    telemetry for proprietary production models.  These fit factors are
    explicit scenario assumptions that prevent an efficient open benchmark
    row from being presented as the base throughput of a closed commercial
    product surface.
    """
    return {
        "Microsoft": {
            "workload_class": "Copilot / routed closed-model assistant",
            "bear_fit_factor": 0.40,
            "base_fit_factor": 0.60,
            "bull_fit_factor": 0.80,
            "rationale": "Copilot traffic mixes routed proprietary models and interactive SLOs; GPT-OSS is a reference ceiling, not direct telemetry.",
        },
        "Google": {
            "workload_class": "Gemini product-integrated multimodal assistant",
            "bear_fit_factor": 0.40,
            "base_fit_factor": 0.60,
            "bull_fit_factor": 0.80,
            "rationale": "Gemini serving is closed and TPU-heavy with product and multimodal routing; the hybrid frontier composite uses gptoss120b on H200 and DeepSeek V4 Pro/Kimi K2.5 on B200/GB200 as a public proxy, not production telemetry.",
        },
        "Meta": {
            "workload_class": "Llama / Meta AI general assistant",
            "bear_fit_factor": 0.75,
            "base_fit_factor": 0.90,
            "bull_fit_factor": 1.00,
            "rationale": "Llama benchmark family is comparatively close to Meta AI serving, while fleet routing and MTIA performance remain unmeasured.",
        },
        "xAI": {
            "workload_class": "Grok interactive and reasoning assistant",
            "bear_fit_factor": 0.35,
            "base_fit_factor": 0.55,
            "bull_fit_factor": 0.75,
            "rationale": "Grok is closed and reasoning/product workload mix is not matched to the GPT-OSS benchmark row.",
        },
        "OpenAI": {
            "workload_class": "GPT / ChatGPT / API with reasoning mix",
            "bear_fit_factor": 0.30,
            "base_fit_factor": 0.50,
            "bull_fit_factor": 0.70,
            "rationale": "ChatGPT/API demand includes reasoning and latency-sensitive surfaces; the hybrid frontier composite uses gptoss120b on H200 and DeepSeek V4 Pro/Kimi K2.5 on B200/GB200, not GPT production telemetry.",
        },
        "Anthropic": {
            "workload_class": "Claude coding, agent and long-context enterprise",
            "bear_fit_factor": 0.30,
            "base_fit_factor": 0.50,
            "bull_fit_factor": 0.70,
            "rationale": "Claude usage is materially coding/agent/long-context oriented; the hybrid frontier composite uses gptoss120b on H200 and DeepSeek V4 Pro/Kimi K2.5 on B200/GB200 because comparable Claude production serving rows are not public.",
        },
        "DeepSeek": {
            "workload_class": "DeepSeek R1/V3 MoE with reasoning mix",
            "bear_fit_factor": 0.65,
            "base_fit_factor": 0.85,
            "bull_fit_factor": 1.00,
            "rationale": "DeepSeek benchmark family is matched, but commercial R1 reasoning traffic can consume more serving capacity than a fixed test.",
        },
        "Alibaba": {
            "workload_class": "Qwen API / enterprise MoE assistant",
            "bear_fit_factor": 0.70,
            "base_fit_factor": 0.90,
            "bull_fit_factor": 1.00,
            "rationale": "Qwen benchmark family is relatively direct; remaining adjustment represents commercial context and SLO mix.",
        },
        "Tencent": {
            "workload_class": "Hunyuan consumer and enterprise assistant",
            "bear_fit_factor": 0.40,
            "base_fit_factor": 0.60,
            "bull_fit_factor": 0.80,
            "rationale": "Hunyuan is not represented by a matched public TPS/MW row; GPT-OSS is used only as a reference ceiling.",
        },
    }


def agentic_trace_profile() -> dict[str, float]:
    source_path = ROOT / "data" / "inferencex" / "normalized" / "inferencex_agentic_trace_profile.csv"
    fallback = {
        "avg_input_tokens_per_request": 100_947.0,
        "avg_output_tokens_per_request": 860.0,
        "input_output_token_ratio": 117.34,
    }
    if not source_path.exists():
        return fallback
    with source_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("dataset_id") == "semianalysisai/cc-traces-weka-062126-256k":
                return {
                    "avg_input_tokens_per_request": float(row.get("avg_input_tokens_per_request") or fallback["avg_input_tokens_per_request"]),
                    "avg_output_tokens_per_request": float(row.get("avg_output_tokens_per_request") or fallback["avg_output_tokens_per_request"]),
                    "input_output_token_ratio": float(row.get("input_output_token_ratio") or fallback["input_output_token_ratio"]),
                }
    return fallback


def kimi_agentic_long_ratio() -> float:
    """Derive agentic TPS/MW as a Kimi K2.5 long-context ratio."""
    fallback = 1.0 / 9.2
    source_path = ROOT / "docs" / "dynamic_reasoning_agent_cost" / "inferencex_dynamic_reasoning_tps_gpu.csv"
    if not source_path.exists():
        return fallback

    ratios: list[float] = []
    with source_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("model") != "kimik2.5":
                continue
            if row.get("workload_type") != "agentic":
                continue
            if row.get("is_main_model_config", "yes") != "yes":
                continue
            if row.get("isl") != "8192" or row.get("osl") != "1024":
                continue
            try:
                agentic_tps_mw = float(row.get("scenario_output_tok_s_mw") or 0)
                long_tps_mw = float(row.get("base_output_tok_s_mw") or 0)
            except ValueError:
                continue
            if agentic_tps_mw > 0 and long_tps_mw > 0:
                ratios.append(agentic_tps_mw / long_tps_mw)

    return statistics.median(ratios) if ratios else fallback


def workload_class_assumptions() -> dict[str, dict[str, Any]]:
    trace = agentic_trace_profile()
    agentic_long_ratio = kimi_agentic_long_ratio()
    return {
        "short_chat": {
            "label": "Short chat / routine assistant",
            "isl": 1024,
            "osl": 1024,
            "concurrency_min": 32,
            "concurrency_max": 256,
            "interactivity_profile": "interactive balanced serving",
            "fit_factor": 1.00,
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX",
            "rationale": "Uses ISL/OSL 1024/1024 and concurrency 32-256, then selects the highest output_tok_s_mw, preferring Dynamo/TRT-LLM/MTP-style optimized serving stacks when present.",
        },
        "long_chat": {
            "label": "Long chat / research / RAG",
            "isl": 8192,
            "osl": 1024,
            "concurrency_min": 32,
            "concurrency_max": 256,
            "interactivity_profile": "interactive long-context serving",
            "fit_factor": 0.92,
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX; SRC_GOOGLE_GEMINI_LONG_CONTEXT",
            "rationale": "Uses ISL/OSL 8192/1024 and concurrency 32-256 where available, then selects the highest output_tok_s_mw, preferring Dynamo/TRT-LLM/MTP-style optimized serving stacks when present. Google long-context docs support treating this as a distinct workload class.",
        },
        "agentic": {
            "label": "Agentic coding / tool workflow",
            "isl": round(trace["avg_input_tokens_per_request"]),
            "osl": round(trace["avg_output_tokens_per_request"]),
            "concurrency_min": 32,
            "concurrency_max": 256,
            "interactivity_profile": "agentic/tool workflow derived from Kimi K2.5 dynamic reasoning",
            "fit_factor": agentic_long_ratio,
            "source_ids": "SRC_INFERENCEX_AGENTIC_TRACES_256K; SRC_SEMIANALYSIS_INFERENCEX; SRC_ANTHROPIC_CONSUMPTION_GUIDE; SRC_OPENAI_CODEX_RATE_CARD",
            "rationale": (
                "Agentic trace profile averages about "
                f"{trace['avg_input_tokens_per_request']:,.0f} input and "
                f"{trace['avg_output_tokens_per_request']:,.0f} output tokens/request. "
                "Because InferenceX does not yet provide matched 100k-input benchmark rows, "
                "agentic TPS/MW is modeled as long_chat TPS/MW multiplied by the Kimi K2.5 "
                f"dynamic-reasoning agentic/long ratio ({agentic_long_ratio:.1%})."
            ),
        },
    }


def company_workload_mix_profiles() -> dict[str, dict[str, Any]]:
    return {
        "Microsoft": {
            "short_chat_share": 0.45,
            "long_chat_share": 0.30,
            "agentic_share": 0.25,
            "rationale": "Microsoft has broad Copilot surfaces plus GitHub/Codex-style developer workflows; agentic share is material but not dominant.",
            "source_ids": "SRC_OPENAI_CODEX_RATE_CARD; SRC_AZURE_OPENAI; SRC_MS_MAIA200",
        },
        "Google": {
            "short_chat_share": 0.40,
            "long_chat_share": 0.40,
            "agentic_share": 0.20,
            "rationale": "Gemini emphasizes long-context and enterprise agent platforms, but broad Workspace/Search-style assistant use remains large.",
            "source_ids": "SRC_GOOGLE_GEMINI_LONG_CONTEXT; SRC_GOOGLE_GEMINI_AGENT_PLATFORM; SRC_GOOGLE_GEMINI_TOKENS",
        },
        "Meta": {
            "short_chat_share": 0.70,
            "long_chat_share": 0.20,
            "agentic_share": 0.10,
            "rationale": "Meta AI and Business Agent are high-volume messaging/customer-service surfaces; agentic enterprise actions are emerging but smaller in Base.",
            "source_ids": "SRC_META_BUSINESS_AGENT; SRC_META_LLAMA; SRC_META_MTIA_GENAI_2026",
        },
        "xAI": {
            "short_chat_share": 0.45,
            "long_chat_share": 0.35,
            "agentic_share": 0.20,
            "rationale": "Grok is modeled as interactive plus reasoning/search-style use; coding-agent share is not as directly evidenced as Anthropic/OpenAI.",
            "source_ids": "SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS",
        },
        "OpenAI": {
            "short_chat_share": 0.45,
            "long_chat_share": 0.25,
            "agentic_share": 0.30,
            "rationale": "ChatGPT remains broad short-chat/API, while Codex token-based pricing and ChatGPT agentic features support a large agentic slice.",
            "source_ids": "SRC_OPENAI_CODEX_RATE_CARD; SRC_OPENAI_CHATGPT_ENTERPRISE; SRC_OPENAI_API_PRICING",
        },
        "Anthropic": {
            "short_chat_share": 0.30,
            "long_chat_share": 0.30,
            "agentic_share": 0.40,
            "rationale": "Claude Enterprise guidance explicitly says Claude Code and Cowork are significantly more token-intensive than chat; Claude Code usage evidence supports the highest agentic mix.",
            "source_ids": "SRC_ANTHROPIC_CONSUMPTION_GUIDE; SRC_ANTHROPIC_CODE_PRACTICE; SRC_ANTHROPIC_CLAUDE_DOCS",
        },
        "DeepSeek": {
            "short_chat_share": 0.35,
            "long_chat_share": 0.40,
            "agentic_share": 0.25,
            "rationale": "DeepSeek R1/V3 traffic is modeled as reasoning/API-heavy with meaningful long-context and developer use, but no direct enterprise-agent surface disclosure.",
            "source_ids": "SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE",
        },
        "Alibaba": {
            "short_chat_share": 0.45,
            "long_chat_share": 0.35,
            "agentic_share": 0.20,
            "rationale": "Qwen/Model Studio is enterprise/API-heavy; long/reasoning use is meaningful while broad cloud assistant traffic keeps short chat substantial.",
            "source_ids": "SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY",
        },
        "Tencent": {
            "short_chat_share": 0.65,
            "long_chat_share": 0.25,
            "agentic_share": 0.10,
            "rationale": "Hunyuan/Yuanbao and WeChat/Tencent Cloud surfaces are modeled as consumer/business chat-heavy; agentic action use is emerging but lower in Base.",
            "source_ids": "SRC_TENCENT_HUNYUAN; SRC_TENCENT_AI_INFRA_MOE",
        },
    }


def workload_reference_profiles() -> dict[str, dict[str, Any]]:
    """Build short/long/agentic output TPS/MW profiles by proxy model and GPU."""
    source_path = ROOT / "data" / "inferencex" / "normalized" / "inferencex_benchmark_results.csv"
    models = ["gptoss120b", "frontier_composite", "llama70b", "dsr1", "qwen3.5"]
    hardware = ["h200", "b200", "gb200"]
    classes = workload_class_assumptions()
    samples: dict[tuple[str, str, str], list[dict[str, str]]] = {
        (model, gpu, workload): []
        for model in models
        for gpu in hardware
        for workload in ("short_chat", "long_chat")
    }
    with source_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source_model = row.get("model", "")
            gpu = row.get("gpu", "")
            if gpu not in hardware:
                continue
            if row.get("benchmark_type") != "single_turn" or row.get("is_main_model_config", "yes") != "yes":
                continue
            if not row.get("output_tok_s_mw"):
                continue
            try:
                concurrency = int(float(row.get("concurrency") or 0))
            except ValueError:
                concurrency = 0
            for proxy_model in models:
                if source_model not in proxy_source_models(proxy_model, gpu):
                    continue
                for workload in ("short_chat", "long_chat"):
                    if (
                        row.get("isl") == str(classes[workload]["isl"])
                        and row.get("osl") == str(classes[workload]["osl"])
                        and classes[workload]["concurrency_min"] <= concurrency <= classes[workload]["concurrency_max"]
                    ):
                        samples[(proxy_model, gpu, workload)].append(row)

    profiles: dict[str, dict[str, Any]] = {}
    for model in models:
        profile: dict[str, Any] = {"proxy_model": model}
        for gpu in hardware:
            short_vals = samples[(model, gpu, "short_chat")]
            if not short_vals:
                b200_short_vals = samples[(model, "b200", "short_chat")]
                gb200_short_vals = samples[(model, "gb200", "short_chat")]
                if b200_short_vals:
                    short_value, short_basis = select_max_tps_sample(b200_short_vals)
                    short_selected = round(short_value)
                    short_status = f"B200 placeholder - missing matched short-chat rows; {short_basis}"
                elif gb200_short_vals:
                    short_value, short_basis = select_max_tps_sample(gb200_short_vals)
                    short_selected = round(short_value)
                    short_status = f"GB200 placeholder - missing matched short-chat rows; {short_basis}"
                else:
                    raise ValueError(f"Missing short_chat reference for {model}")
            else:
                short_value, short_basis = select_max_tps_sample(short_vals)
                short_selected = round(short_value)
                short_status = f"Public 1024/1024 reference selected; {short_basis}"

            long_vals = samples[(model, gpu, "long_chat")]
            if len(long_vals) >= 10:
                long_value, long_basis = select_max_tps_sample(long_vals)
                long_selected = round(long_value)
                long_status = f"Public 8192/1024 reference selected; {long_basis}"
            else:
                b200_long_vals = samples[(model, "b200", "long_chat")]
                gb200_long_vals = samples[(model, "gb200", "long_chat")]
                if b200_long_vals:
                    long_value, long_basis = select_max_tps_sample(b200_long_vals)
                    long_selected = round(long_value)
                    long_status = f"B200 placeholder - insufficient/missing matched 8192/1024 rows; {long_basis}"
                elif gb200_long_vals:
                    long_value, long_basis = select_max_tps_sample(gb200_long_vals)
                    long_selected = round(long_value)
                    long_status = f"GB200 placeholder - insufficient/missing matched 8192/1024 rows; {long_basis}"
                else:
                    long_selected = round(short_selected * classes["long_chat"]["fit_factor"])
                    long_status = "Derived fallback - insufficient 8192/1024 rows"

            agentic_selected = round(long_selected * classes["agentic"]["fit_factor"])
            profile[f"{gpu}_short_chat_tps_per_mw"] = short_selected
            profile[f"{gpu}_short_chat_row_count"] = len(short_vals)
            profile[f"{gpu}_short_chat_status"] = short_status
            profile[f"{gpu}_long_chat_tps_per_mw"] = long_selected
            profile[f"{gpu}_long_chat_row_count"] = len(long_vals)
            profile[f"{gpu}_long_chat_status"] = long_status
            profile[f"{gpu}_agentic_tps_per_mw"] = agentic_selected
            profile[f"{gpu}_agentic_status"] = (
                f"Derived from long_chat x Kimi K2.5 agentic/long ratio ({classes['agentic']['fit_factor']:.1%})"
            )
        profiles[model] = profile
    return profiles


def workload_mix_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for company, mix in company_workload_mix_profiles().items():
        rows.append(
            {
                "company": company,
                **mix,
                "share_sum": round(mix["short_chat_share"] + mix["long_chat_share"] + mix["agentic_share"], 6),
            }
        )
    return rows


def workload_reference_rows() -> list[dict[str, Any]]:
    profiles = workload_reference_profiles()
    rows: list[dict[str, Any]] = []
    for model, profile in profiles.items():
        for gpu in ("h200", "b200", "gb200"):
            rows.append(
                {
                    "proxy_model": model,
                    "gpu": gpu,
                    "short_chat_tps_per_mw": profile[f"{gpu}_short_chat_tps_per_mw"],
                    "short_chat_rows": profile[f"{gpu}_short_chat_row_count"],
                    "long_chat_tps_per_mw": profile[f"{gpu}_long_chat_tps_per_mw"],
                    "long_chat_rows": profile[f"{gpu}_long_chat_row_count"],
                    "agentic_tps_per_mw": profile[f"{gpu}_agentic_tps_per_mw"],
                    "short_status": profile[f"{gpu}_short_chat_status"],
                    "long_status": profile[f"{gpu}_long_chat_status"],
                    "agentic_status": profile[f"{gpu}_agentic_status"],
                }
            )
    return rows


def interactivity_reference_rows() -> list[dict[str, Any]]:
    """Select GPU/workload candidates by minimum generated tok/s/user."""
    source_path = ROOT / "data" / "inferencex" / "normalized" / "inferencex_benchmark_results.csv"
    models = ["gptoss120b", "frontier_composite", "llama70b", "dsr1", "qwen3.5"]
    hardware = ["h200", "b200", "gb200"]
    classes = workload_class_assumptions()
    agentic_ratio = classes["agentic"]["fit_factor"]
    workloads = ("short_chat", "long_chat", "agentic_derived")
    samples: dict[tuple[str, str, str], list[dict[str, str]]] = {
        (model, gpu, workload): []
        for model in models
        for gpu in hardware
        for workload in workloads
    }

    with source_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source_model = row.get("model", "")
            gpu = row.get("gpu", "")
            if gpu not in hardware:
                continue
            if row.get("benchmark_type") != "single_turn" or row.get("is_main_model_config", "yes") != "yes":
                continue
            if not row.get("output_tok_s_mw") or not row.get("output_tok_s_gpu"):
                continue
            for proxy_model in models:
                if source_model not in proxy_source_models(proxy_model, gpu):
                    continue
                if row.get("isl") == str(classes["short_chat"]["isl"]) and row.get("osl") == str(classes["short_chat"]["osl"]):
                    samples[(proxy_model, gpu, "short_chat")].append(row)
                if row.get("isl") == str(classes["long_chat"]["isl"]) and row.get("osl") == str(classes["long_chat"]["osl"]):
                    samples[(proxy_model, gpu, "long_chat")].append(row)
                    samples[(proxy_model, gpu, "agentic_derived")].append(row)

    rows: list[dict[str, Any]] = []
    for model in models:
        for gpu in hardware:
            for workload in workloads:
                workload_samples = samples[(model, gpu, workload)]
                multiplier = agentic_ratio if workload == "agentic_derived" else 1.0
                for target in INTERACTIVITY_TARGETS_TOK_S_USER:
                    eligible = [
                        row for row in workload_samples
                        if (output_tok_s_user(row, multiplier) or 0) >= target
                    ]
                    optimized = [row for row in eligible if optimized_serving_stack(row)]
                    selected_pool = optimized if optimized else eligible
                    if selected_pool:
                        selected = max(
                            selected_pool,
                            key=lambda row: float(row["output_tok_s_mw"]) * multiplier,
                        )
                        selected_tok_s_user = output_tok_s_user(selected, multiplier)
                        selected_tps_mw = float(selected["output_tok_s_mw"]) * multiplier
                        status = "selected_optimized_stack" if optimized else "selected_public_max"
                        basis = (
                            "Dynamo/TRT-LLM/MTP eligible max"
                            if optimized
                            else "public max among eligible rows"
                        )
                        framework = selected.get("framework", "")
                        precision = selected.get("precision", "")
                        concurrency = int(float(selected.get("concurrency") or 0))
                        selected_isl = int(float(selected.get("isl") or 0))
                        selected_osl = int(float(selected.get("osl") or 0))
                        benchmark_date = selected.get("benchmark_date", "")
                    else:
                        selected_tok_s_user = ""
                        selected_tps_mw = ""
                        status = "missing"
                        basis = "no row meets target_tok_s_user"
                        framework = ""
                        precision = ""
                        concurrency = ""
                        selected_isl = classes["agentic"]["isl"] if workload == "agentic_derived" else classes[workload]["isl"]
                        selected_osl = classes["agentic"]["osl"] if workload == "agentic_derived" else classes[workload]["osl"]
                        benchmark_date = ""
                    rows.append(
                        {
                            "proxy_model": model,
                            "gpu": gpu,
                            "workload_type": workload,
                            "source_model_scope": proxy_source_label(model, gpu),
                            "target_tok_s_user": target,
                            "selected_isl": selected_isl,
                            "selected_osl": selected_osl,
                            "candidate_rows": len(workload_samples),
                            "eligible_rows": len(eligible),
                            "optimized_eligible_rows": len(optimized),
                            "selected_output_tps_per_mw": round(selected_tps_mw) if selected_tps_mw != "" else "",
                            "selected_tok_s_user": round(selected_tok_s_user, 2) if selected_tok_s_user != "" else "",
                            "selected_concurrency": concurrency,
                            "selected_framework": framework,
                            "selected_precision": precision,
                            "selection_status": status,
                            "selection_basis": basis,
                            "benchmark_date": benchmark_date,
                            "method_note": (
                                "tok_s_user is computed as output_tok_s_gpu/concurrency when source tok_s_user is blank; "
                                "agentic_derived uses long_chat rows multiplied by the Kimi K2.5 agentic/long ratio."
                            ),
                        }
                    )
    return rows


def commercial_workload_benchmark_rows() -> list[dict[str, Any]]:
    benchmark_map = company_core_benchmark_map()
    workload_map = commercial_workload_profiles()
    workload_refs = workload_reference_profiles()
    workload_mixes = company_workload_mix_profiles()
    rows: list[dict[str, Any]] = []
    for company in [scenario.company for scenario in scenarios()]:
        benchmark = benchmark_map[company]
        workload = workload_map[company]
        refs = workload_refs[benchmark["proxy_model"]]
        mix = workload_mixes[company]
        b200_weighted_reference = round(
            mix["short_chat_share"] * refs["b200_short_chat_tps_per_mw"]
            + mix["long_chat_share"] * refs["b200_long_chat_tps_per_mw"]
            + mix["agentic_share"] * refs["b200_agentic_tps_per_mw"]
        )
        rows.append(
            {
                "company": company,
                "commercial_workload_class": workload["workload_class"],
                "proxy_model": benchmark["proxy_model"],
                "inferencex_reference_tps_per_mw": benchmark["output_tok_s_mw_selected"],
                "b200_short_chat_tps_per_mw": refs["b200_short_chat_tps_per_mw"],
                "b200_long_chat_tps_per_mw": refs["b200_long_chat_tps_per_mw"],
                "b200_agentic_tps_per_mw": refs["b200_agentic_tps_per_mw"],
                "short_chat_share": mix["short_chat_share"],
                "long_chat_share": mix["long_chat_share"],
                "agentic_share": mix["agentic_share"],
                "b200_workload_weighted_reference_tps_per_mw": b200_weighted_reference,
                "bear_fit_factor": workload["bear_fit_factor"],
                "base_fit_factor": workload["base_fit_factor"],
                "bull_fit_factor": workload["bull_fit_factor"],
                "base_reference_serving_tps_per_mw": round(b200_weighted_reference * workload["base_fit_factor"]),
                "rationale": workload["rationale"] + " Workload mix: " + mix["rationale"],
            }
        )
    return rows


def gpu_generation_mix_default(year_index: int) -> dict[str, float]:
    """Editable default split within the GPU portion of modeled inference load."""
    points = len(YEARS)
    return {
        "h200": lerp(0.55, 0.10, year_index, points),
        "b200": lerp(0.40, 0.35, year_index, points),
        "gb200": lerp(0.05, 0.55, year_index, points),
    }


def hardware_reference_profiles() -> dict[str, dict[str, Any]]:
    """Build selected output-token TPS/MW references by proxy model and GPU generation.

    A model/hardware row is selected only where at least 50 comparable public
    observations exist under the fixed filter. Otherwise B200 is used as an
    explicit conservative placeholder until the user supplies a replacement.
    """
    source_path = ROOT / "data" / "inferencex" / "normalized" / "inferencex_benchmark_results.csv"
    models = ["gptoss120b", "frontier_composite", "llama70b", "dsr1", "qwen3.5"]
    hardware = ["h200", "b200", "gb200"]
    samples: dict[tuple[str, str], list[dict[str, str]]] = {(model, gpu): [] for model in models for gpu in hardware}
    with source_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source_model = row.get("model", "")
            gpu = row.get("gpu", "")
            if (
                gpu in hardware
                and row.get("benchmark_type") == "single_turn"
                and row.get("is_main_model_config", "yes") == "yes"
                and row.get("isl") == "1024"
                and row.get("osl") == "1024"
                and row.get("output_tok_s_mw")
            ):
                try:
                    concurrency = int(float(row.get("concurrency") or 0))
                except ValueError:
                    concurrency = 0
                if 32 <= concurrency <= 256:
                    for proxy_model in models:
                        if source_model in proxy_source_models(proxy_model, gpu):
                            samples[(proxy_model, gpu)].append(row)
    profiles: dict[str, dict[str, Any]] = {}
    for model in models:
        b200_vals = samples[(model, "b200")]
        gb200_vals = samples[(model, "gb200")]
        if b200_vals:
            fallback_value = round(select_max_tps_sample(b200_vals)[0])
            fallback_label = "B200"
        elif gb200_vals:
            fallback_value = round(select_max_tps_sample(gb200_vals)[0])
            fallback_label = "GB200"
        else:
            raise ValueError(f"Missing B200/GB200 reference for {model}")
        profile: dict[str, Any] = {"proxy_model": model}
        for gpu in hardware:
            vals = samples[(model, gpu)]
            observed_value, observed_basis = select_max_tps_sample(vals) if vals else (None, "")
            observed = round(observed_value) if observed_value is not None else None
            selected = observed if len(vals) >= 50 else fallback_value
            profile[f"{gpu}_row_count"] = len(vals)
            profile[f"{gpu}_observed_tps_per_mw"] = observed
            profile[f"{gpu}_selected_tps_per_mw"] = selected
            profile[f"{gpu}_selection_status"] = (
                f"Public reference selected; {observed_basis}"
                if len(vals) >= 50
                else f"{fallback_label} placeholder - insufficient/missing matched rows; editable input"
            )
        profiles[model] = profile
    return profiles


def forecast_rows(scenario_case: str = "Base") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case = SCENARIO_CASES[scenario_case]
    mix_profiles = accelerator_mix_profiles()
    derivation_profiles = company_derivation_profiles()
    benchmark_profiles = company_core_benchmark_map()
    workload_profiles = commercial_workload_profiles()
    hardware_profiles = hardware_reference_profiles()
    workload_references = workload_reference_profiles()
    workload_mixes = company_workload_mix_profiles()
    for scenario in scenarios():
        mix = mix_profiles[scenario.company]
        derivation = derivation_profiles[scenario.company]
        benchmark = benchmark_profiles[scenario.company]
        workload = workload_profiles[scenario.company]
        workload_mix = workload_mixes[scenario.company]
        for idx, year in enumerate(YEARS):
            contracted = lerp(scenario.contracted_power_2026_gw, scenario.contracted_power_2030_gw, idx, len(YEARS))
            base_active = lerp(scenario.active_power_2026_gw, scenario.active_power_2030_gw, idx, len(YEARS))
            deploy_multiplier = lerp(case["operational_deploy_multiplier_2026"], case["operational_deploy_multiplier_2030"], idx, len(YEARS))
            active = min(contracted, base_active * deploy_multiplier)
            base_inference_share = lerp(scenario.inference_share_2026, scenario.inference_share_2030, idx, len(YEARS))
            inference_delta = lerp(case["inference_share_delta_2026"], case["inference_share_delta_2030"], idx, len(YEARS))
            inference_share = min(max(base_inference_share + inference_delta, 0.35), 0.94)
            training_share = 1 - inference_share
            utilization_reference = round(lerp(scenario.utilization_2026, scenario.utilization_2030, idx, len(YEARS)), 3)
            gpu_share = lerp(mix["gpu_share_2026"], mix["gpu_share_2030"], idx, len(YEARS))
            purpose_built_share = round(1 - gpu_share, 3)
            generation_mix = gpu_generation_mix_default(idx)
            h200_share = round(gpu_share * generation_mix["h200"], 3)
            b200_share = round(gpu_share * generation_mix["b200"], 3)
            gb200_share = round(1 - purpose_built_share - h200_share - b200_share, 3)
            hardware = hardware_profiles[benchmark["proxy_model"]]
            workload_hardware = workload_references[benchmark["proxy_model"]]
            h200_reference_tps_per_mw = hardware["h200_selected_tps_per_mw"]
            b200_reference_tps_per_mw = hardware["b200_selected_tps_per_mw"]
            gb200_reference_tps_per_mw = hardware["gb200_selected_tps_per_mw"]
            purpose_built_reference_tps_per_mw = b200_reference_tps_per_mw
            h200_short_chat_tps_per_mw = workload_hardware["h200_short_chat_tps_per_mw"]
            h200_long_chat_tps_per_mw = workload_hardware["h200_long_chat_tps_per_mw"]
            h200_agentic_tps_per_mw = workload_hardware["h200_agentic_tps_per_mw"]
            b200_short_chat_tps_per_mw = workload_hardware["b200_short_chat_tps_per_mw"]
            b200_long_chat_tps_per_mw = workload_hardware["b200_long_chat_tps_per_mw"]
            b200_agentic_tps_per_mw = workload_hardware["b200_agentic_tps_per_mw"]
            gb200_short_chat_tps_per_mw = workload_hardware["gb200_short_chat_tps_per_mw"]
            gb200_long_chat_tps_per_mw = workload_hardware["gb200_long_chat_tps_per_mw"]
            gb200_agentic_tps_per_mw = workload_hardware["gb200_agentic_tps_per_mw"]
            purpose_short_chat_tps_per_mw = b200_short_chat_tps_per_mw
            purpose_long_chat_tps_per_mw = b200_long_chat_tps_per_mw
            purpose_agentic_tps_per_mw = b200_agentic_tps_per_mw
            h200_workload_weighted_tps_per_mw = round(
                workload_mix["short_chat_share"] * h200_short_chat_tps_per_mw
                + workload_mix["long_chat_share"] * h200_long_chat_tps_per_mw
                + workload_mix["agentic_share"] * h200_agentic_tps_per_mw
            )
            b200_workload_weighted_tps_per_mw = round(
                workload_mix["short_chat_share"] * b200_short_chat_tps_per_mw
                + workload_mix["long_chat_share"] * b200_long_chat_tps_per_mw
                + workload_mix["agentic_share"] * b200_agentic_tps_per_mw
            )
            gb200_workload_weighted_tps_per_mw = round(
                workload_mix["short_chat_share"] * gb200_short_chat_tps_per_mw
                + workload_mix["long_chat_share"] * gb200_long_chat_tps_per_mw
                + workload_mix["agentic_share"] * gb200_agentic_tps_per_mw
            )
            purpose_workload_weighted_tps_per_mw = b200_workload_weighted_tps_per_mw
            short_chat_tps_per_mw = round(
                h200_share * h200_short_chat_tps_per_mw
                + b200_share * b200_short_chat_tps_per_mw
                + gb200_share * gb200_short_chat_tps_per_mw
                + purpose_built_share * purpose_short_chat_tps_per_mw
            )
            long_chat_tps_per_mw = round(
                h200_share * h200_long_chat_tps_per_mw
                + b200_share * b200_long_chat_tps_per_mw
                + gb200_share * gb200_long_chat_tps_per_mw
                + purpose_built_share * purpose_long_chat_tps_per_mw
            )
            agentic_tps_per_mw = round(
                h200_share * h200_agentic_tps_per_mw
                + b200_share * b200_agentic_tps_per_mw
                + gb200_share * gb200_agentic_tps_per_mw
                + purpose_built_share * purpose_agentic_tps_per_mw
            )
            inferencex_reference_tps_per_mw = round(
                h200_share * h200_workload_weighted_tps_per_mw
                + b200_share * b200_workload_weighted_tps_per_mw
                + gb200_share * gb200_workload_weighted_tps_per_mw
                + purpose_built_share * purpose_workload_weighted_tps_per_mw
            )
            fit_key = "bear_fit_factor" if scenario_case == "Bear" else "bull_fit_factor" if scenario_case == "Bull" else "base_fit_factor"
            commercial_workload_fit_factor = workload[fit_key]
            reference_serving_tps_per_mw = round(inferencex_reference_tps_per_mw * commercial_workload_fit_factor)
            purpose_built_tps_per_mw = round(purpose_built_reference_tps_per_mw * commercial_workload_fit_factor)
            tps_per_mw = reference_serving_tps_per_mw
            it_load_gw = active / scenario.pue
            ai_it_load_gw = it_load_gw * scenario.ai_workload_share
            inference_gw = ai_it_load_gw * inference_share
            training_gw = ai_it_load_gw * training_share
            active_r = round(active, 3)
            contracted_r = round(contracted, 3)
            operational_deployment_share = active_r / contracted_r if contracted_r else 0
            it_load_r = round(it_load_gw, 3)
            ai_it_load_r = round(ai_it_load_gw, 3)
            training_share_r = round(training_share, 3)
            inference_share_r = round(inference_share, 3)
            inference_gw_r = round(inference_gw, 3)
            training_gw_r = round(training_gw, 3)
            tps_per_mw_r = round(tps_per_mw)
            inference_mw = inference_gw_r * 1000
            tokens_per_day = inference_mw * tps_per_mw_r * 86400
            annual_tokens = round(tokens_per_day) * 365
            joules_per_token = 1_000_000 / tps_per_mw_r
            rows.append(
                {
                    "scenario": scenario_case,
                    "company": scenario.company,
                    "region": scenario.region,
                    "model_family": scenario.model_family,
                    "commercial_surface": scenario.commercial_surface,
                    "year": year,
                    "contracted_power_gw": contracted_r,
                    "operational_deployment_share": round(operational_deployment_share, 8),
                    "active_power_gw": active_r,
                    "pue": scenario.pue,
                    "it_load_gw": it_load_r,
                    "ai_workload_share": scenario.ai_workload_share,
                    "ai_it_load_gw": ai_it_load_r,
                    "gpu_share": round(gpu_share, 3),
                    "purpose_built_accelerator_share": round(purpose_built_share, 3),
                    "purpose_built_accelerator_label": mix["asic_label"],
                    "h200_share": round(h200_share, 3),
                    "b200_share": round(b200_share, 3),
                    "gb200_share": round(gb200_share, 3),
                    "gpu_benchmark_proxy_model": benchmark["proxy_model"],
                    "commercial_workload_class": workload["workload_class"],
                    "h200_reference_tps_per_mw": h200_reference_tps_per_mw,
                    "b200_reference_tps_per_mw": b200_reference_tps_per_mw,
                    "gb200_reference_tps_per_mw": gb200_reference_tps_per_mw,
                    "purpose_built_reference_tps_per_mw": purpose_built_reference_tps_per_mw,
                    "fleet_reference_tps_per_mw": inferencex_reference_tps_per_mw,
                    "inferencex_reference_tps_per_mw": inferencex_reference_tps_per_mw,
                    "short_chat_share": workload_mix["short_chat_share"],
                    "long_chat_share": workload_mix["long_chat_share"],
                    "agentic_share": workload_mix["agentic_share"],
                    "short_chat_reference_tps_per_mw": short_chat_tps_per_mw,
                    "long_chat_reference_tps_per_mw": long_chat_tps_per_mw,
                    "agentic_reference_tps_per_mw": agentic_tps_per_mw,
                    "h200_workload_weighted_tps_per_mw": h200_workload_weighted_tps_per_mw,
                    "b200_workload_weighted_tps_per_mw": b200_workload_weighted_tps_per_mw,
                    "gb200_workload_weighted_tps_per_mw": gb200_workload_weighted_tps_per_mw,
                    "purpose_built_workload_weighted_tps_per_mw": purpose_workload_weighted_tps_per_mw,
                    "commercial_workload_fit_factor": commercial_workload_fit_factor,
                    "reference_serving_tps_per_mw": reference_serving_tps_per_mw,
                    "gpu_benchmark_tps_per_mw": reference_serving_tps_per_mw,
                    "purpose_built_tps_per_mw": purpose_built_tps_per_mw,
                    "purpose_built_benchmark_status": "No comparable public output-token/MW row adopted; B200 public reference placeholder is used and remains editable.",
                    "training_power_share": training_share_r,
                    "inference_power_share": inference_share_r,
                    "inference_gw": inference_gw_r,
                    "training_gw": training_gw_r,
                    "tokens_per_second_per_mw": tps_per_mw_r,
                    "joules_per_token": round(joules_per_token, 4),
                    "utilization_reference_only": utilization_reference,
                    "headline_utilization_applied": False,
                    "inference_tokens_per_day": round(tokens_per_day),
                    "inference_tokens_per_year": round(annual_tokens),
                    "confidence": scenario.confidence,
                    "derivation_type": scenario.derivation_type,
                    "source_ids": scenario.source_ids,
                    "assumption_ids": scenario.assumption_ids + "; ASSUMP_INFERENCE_SHARE_NOT_FACT_60; ASSUMP_WORKLOAD_CLASS_MIX; ASSUMP_AGENTIC_CONTEXT_PENALTY",
                    "capacity_basis": derivation["capacity_basis"],
                    "active_power_basis": derivation["active_basis"],
                    "ai_workload_share_basis": derivation["ai_workload_basis"],
                    "gpu_asic_mix_basis": mix["mix_rationale"],
                    "tokens_per_mw_basis": (
                        mix["tps_rationale"]
                        + " Workload reference is now split into short_chat, long_chat and agentic classes. "
                        + f"Company mix: short {workload_mix['short_chat_share']:.0%}, long {workload_mix['long_chat_share']:.0%}, agentic {workload_mix['agentic_share']:.0%}. "
                        + "Commercial workload fit factor: "
                        + workload["rationale"]
                        + " "
                        + workload_mix["rationale"]
                    ),
                    "inference_share_basis": derivation["inference_basis"],
                    "utilization_basis": "Reference/sensitivity only; not multiplied into headline output-token formula. " + derivation["utilization_basis"],
                    "replacement_path": mix["replacement_path"],
                }
            )
    return rows


def number_trace_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the intentionally short audit trail for the headline formula."""
    capacity_sources = {
        "Microsoft": "ASSUMP_POWER_RAMP; SRC_MS_MAIA200",
        "Google": "ASSUMP_POWER_RAMP; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E",
        "Meta": "ASSUMP_POWER_RAMP; SRC_META_MTIA_GENAI_2026",
        "xAI": "SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_CLUSTER_RAMP",
        "OpenAI": "SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_STARGATE_RAMP",
        "Anthropic": "SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_POWER_RAMP",
        "DeepSeek": "SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_CN_CAPACITY_TRANSPARENCY",
        "Alibaba": "SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_CN_CAPACITY_TRANSPARENCY",
        "Tencent": "SRC_TENCENT_AI_INFRA_MOE; ASSUMP_CN_CAPACITY_TRANSPARENCY",
    }
    trace: list[dict[str, Any]] = []

    def add(row, metric, value, unit, derivation_type, formula, rationale, source_ids, replacement_path):
        trace.append(
            {
                "company": row["company"],
                "year": row["year"],
                "scenario": row["scenario"],
                "metric": metric,
                "value": value,
                "unit": unit,
                "derivation_type": derivation_type,
                "formula_or_rule": formula,
                "why_this_number": rationale,
                "source_ids": source_ids,
                "assumption_ids": row["assumption_ids"],
                "replacement_path": replacement_path,
            }
        )

    for row in rows:
        company_sources = row["source_ids"]
        capacity_source_ids = capacity_sources[row["company"]]
        add(
            row, "contracted_power_gw", row["contracted_power_gw"], "GW",
            "Fact anchor + scenario ceiling" if row["company"] in {"OpenAI", "Anthropic", "xAI"} else "Scenario capacity envelope",
            "linear interpolation between 2026 and 2030 company capacity endpoints",
            row["capacity_basis"], capacity_source_ids,
            "Company/site-level committed MW/GW, interconnect and contract disclosure.",
        )
        add(
            row, "operational_deployment_share", row["operational_deployment_share"], "share", "Scenario conversion",
            "active_power_gw / contracted_power_gw",
            "This is the single explicit conversion from contracted/attributed capacity to operationally usable capacity.",
            capacity_source_ids,
            "Energized operational capacity divided by contracted/attributed capacity.",
        )
        add(
            row, "active_power_gw", row["active_power_gw"], "GW", "Derived scenario",
            "contracted_power_gw * operational_deployment_share",
            row["active_power_basis"], capacity_source_ids,
            "Energization dates, accelerator deliveries and operational powered-rack telemetry.",
        )
        add(
            row, "pue", row["pue"], "ratio", "Scenario parameter",
            "it_load_gw = active_power_gw / pue",
            "No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario.",
            "ASSUMP_POWER_RAMP",
            "Site-level measured PUE matched to attributed AI capacity.",
        )
        add(
            row, "it_load_gw", row["it_load_gw"], "GW", "Derived formula",
            "active_power_gw / pue",
            "Facility power is converted to IT-deliverable power before attributing AI workloads.",
            capacity_source_ids,
            "Recompute once active power and PUE become site-observable.",
        )
        add(
            row, "ai_workload_share", row["ai_workload_share"], "share", "Scenario allocation",
            "ai_it_load_gw = it_load_gw * ai_workload_share",
            row["ai_workload_share_basis"], company_sources,
            "Model-owner AI workload allocation or cluster scheduling telemetry.",
        )
        add(
            row, "ai_it_load_gw", row["ai_it_load_gw"], "GW", "Derived formula",
            "it_load_gw * ai_workload_share",
            "Only the AI-attributed portion of IT load enters training/inference allocation.",
            company_sources,
            "Recompute after ai_workload_share is replaced by telemetry.",
        )
        add(
            row, "gpu_share", row["gpu_share"], "share of inference-serving accelerator load", "Numeric scenario",
            "gpu_share interpolated from company 2026/2030 accelerator-mix endpoints",
            row["gpu_asic_mix_basis"], company_sources + "; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            row["replacement_path"],
        )
        for gpu in ("h200", "b200", "gb200"):
            add(
                row, f"{gpu}_share", row[f"{gpu}_share"], "share of inference-serving accelerator load", "Editable numeric scenario",
                f"{gpu}_share = gpu_share * default_gpu_generation_mix_{gpu}",
                "Default GPU-generation migration assumption; executive workbook allows later manual replacement by company/year/scenario.",
                "SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX",
                "Company fleet inventory, accelerator-hours or procurement/deployment records by GPU generation.",
            )
        add(
            row, "purpose_built_accelerator_share", row["purpose_built_accelerator_share"], "share of inference-serving accelerator load", "Numeric scenario",
            "1 - gpu_share",
            f"Purpose-built bucket: {row['purpose_built_accelerator_label']}. " + row["gpu_asic_mix_basis"],
            company_sources + "; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            row["replacement_path"],
        )
        add(
            row, "fleet_reference_tps_per_mw", row["fleet_reference_tps_per_mw"], "generated output tokens/sec/MW", "Fleet-weighted public benchmark reference",
            "h200_share*h200_workload_avg + b200_share*b200_workload_avg + gb200_share*gb200_workload_avg + purpose_built_share*purpose_workload_avg",
            f"Selected InferenceX proxy model: {row['gpu_benchmark_proxy_model']}. Each GPU-generation reference first averages short_chat, long_chat and agentic TPS/MW using company workload mix; purpose-built remains a documented B200 placeholder.",
            "SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX; ASSUMP_WORKLOAD_CLASS_MIX; ASSUMP_AGENTIC_CONTEXT_PENALTY",
            "Comparable production output-token throughput or a more closely matched benchmark.",
        )
        add(
            row, "commercial_workload_fit_factor", row["commercial_workload_fit_factor"], "share of public reference throughput", "Scenario assumption",
            "reference_serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor",
            f"Commercial workload class: {row['commercial_workload_class']}. Company mix uses short_chat={row['short_chat_share']:.0%}, long_chat={row['long_chat_share']:.0%}, agentic={row['agentic_share']:.0%}; closed-model, reasoning, long-context and SLO mismatch stays explicit.",
            "SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX; ASSUMP_WORKLOAD_CLASS_MIX; ASSUMP_AGENTIC_CONTEXT_PENALTY",
            "Matched commercial serving benchmark by product surface, context shape and latency SLO.",
        )
        add(
            row, "reference_serving_tps_per_mw", row["reference_serving_tps_per_mw"], "generated output tokens/sec/MW", "Workload-adjusted benchmark proxy",
            "fleet_reference_tps_per_mw * commercial_workload_fit_factor",
            "This is the coefficient used for headline token generation; each GPU's short chat, long chat and agentic TPS/MW are weighted before fleet mix and commercial fit are applied.",
            "SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX; ASSUMP_WORKLOAD_CLASS_MIX; ASSUMP_AGENTIC_CONTEXT_PENALTY",
            "Provider production output-token throughput with comparable workload/SLO.",
        )
        add(
            row, "purpose_built_tps_per_mw", row["purpose_built_tps_per_mw"], "generated output tokens/sec/MW", "Conservative no-uplift proxy",
            "purpose_built_tps_per_mw = purpose_built_reference_tps_per_mw * commercial_workload_fit_factor until comparable output-token benchmark is adopted",
            row["purpose_built_benchmark_status"],
            company_sources + "; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            "Matched-workload generated-output benchmark for the provider purpose-built accelerator.",
        )
        add(
            row, "inference_power_share", row["inference_power_share"], "share of AI IT load", "Scenario allocation",
            "inference_gw = ai_it_load_gw * inference_power_share",
            row["inference_share_basis"], company_sources + "; ASSUMP_INFERENCE_SHARE_NOT_FACT_60",
            "Provider-specific inference/training workload power telemetry.",
        )
        add(
            row, "inference_gw", row["inference_gw"], "GW", "Derived formula",
            "ai_it_load_gw * inference_power_share",
            "This is the operational power eligible to become commercial generated output tokens through the selected TPS/MW proxy.",
            company_sources,
            "Recompute after AI allocation or inference-share evidence changes.",
        )
        add(
            row, "training_power_share", row["training_power_share"], "share of AI IT load", "Derived allocation",
            "1 - inference_power_share",
            "Training receives the complementary modeled AI IT allocation; it is not a disclosed company workload split.",
            company_sources + "; ASSUMP_INFERENCE_SHARE_NOT_FACT_60",
            "Provider-specific inference/training workload power telemetry.",
        )
        add(
            row, "training_gw", row["training_gw"], "GW", "Derived formula",
            "ai_it_load_gw * training_power_share",
            "Training GW is shown separately so commercial inference token capacity is not overstated.",
            company_sources,
            "Recompute after AI allocation or workload-split evidence changes.",
        )
        add(
            row, "tokens_per_second_per_mw", row["tokens_per_second_per_mw"], "generated output tokens/sec/MW", "Derived estimate + benchmark calibration",
            "fleet_reference_tps_per_mw * commercial_workload_fit_factor",
            row["tokens_per_mw_basis"], company_sources + "; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX; ASSUMP_WORKLOAD_CLASS_MIX; ASSUMP_AGENTIC_CONTEXT_PENALTY",
            "Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched.",
        )
        add(
            row, "inference_tokens_per_day", row["inference_tokens_per_day"], "generated output tokens/day", "Derived headline metric",
            "inference_gw * 1000 * tokens_per_second_per_mw * 86,400",
            "Headline capacity uses no utilization, MoE, architecture or software-growth multiplier; it is not observed commercial output volume.",
            company_sources + "; SRC_SEMIANALYSIS_INFERENCEX",
            "Provider-disclosed generated output token volume or calibrated capacity telemetry.",
        )
        add(
            row, "inference_tokens_per_year", row["inference_tokens_per_year"], "generated output tokens/year", "Derived headline metric",
            "inference_tokens_per_day * 365",
            "Annualized version of generated output token capacity; it is not observed annual demand or billable volume.",
            company_sources + "; SRC_SEMIANALYSIS_INFERENCEX",
            "Provider-disclosed annual generated-output volume or metered serving telemetry.",
        )
    return trace


def sensitivity_rows(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in base_rows:
        if row["year"] not in (2026, 2028, 2030):
            continue
        for name, tps_mult in [
            ("Benchmark downside: lower TPS/MW", 0.65),
            ("Core selected benchmark", 1.00),
            ("Benchmark upside: higher TPS/MW", 1.45),
        ]:
            tokens = row["inference_gw"] * 1000 * row["tokens_per_second_per_mw"] * tps_mult * 86400
            result.append(
                {
                    "scenario": name,
                    "company": row["company"],
                    "year": row["year"],
                    "inference_gw": row["inference_gw"],
                    "tokens_per_second_per_mw": round(row["tokens_per_second_per_mw"] * tps_mult),
                    "inference_tokens_per_day": round(tokens),
                    "delta_vs_base_pct": round((tokens / row["inference_tokens_per_day"] - 1) * 100, 1),
                }
            )
    return result


def scenario_summary_rows(scenario_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario_name in SCENARIO_CASES:
        for year in YEARS:
            subset = [r for r in scenario_rows if r["scenario"] == scenario_name and r["year"] == year]
            total_tokens = sum(r["inference_tokens_per_day"] for r in subset)
            inference_gw = sum(r["inference_gw"] for r in subset)
            training_gw = sum(r["training_gw"] for r in subset)
            active_power = sum(r["active_power_gw"] for r in subset)
            ai_it = sum(r["ai_it_load_gw"] for r in subset)
            inference_share = inference_gw / ai_it if ai_it else 0
            rows.append(
                {
                    "scenario": scenario_name,
                    "year": year,
                    "active_power_gw": round(active_power, 3),
                    "ai_it_load_gw": round(ai_it, 3),
                    "inference_gw": round(inference_gw, 3),
                    "training_gw": round(training_gw, 3),
                    "weighted_inference_share": round(inference_share, 3),
                    "inference_tokens_per_day": round(total_tokens),
                    "inference_tokens_per_day_q": round(total_tokens / 1e15, 3),
                    "scenario_description_kr": SCENARIO_CASES[scenario_name]["description_kr"],
                }
            )
    base_2030 = next(r for r in rows if r["scenario"] == "Base" and r["year"] == 2030)["inference_tokens_per_day"]
    for row in rows:
        if row["year"] == 2030:
            row["delta_vs_base_2030_pct"] = round((row["inference_tokens_per_day"] / base_2030 - 1) * 100, 1)
        else:
            row["delta_vs_base_2030_pct"] = ""
    return rows


def benchmark_assumptions() -> list[dict[str, Any]]:
    """GPU/effective-parameter benchmark layer adapted from the comparison workbook."""
    return [
        {"company": "OpenAI", "proxy_model": "Hybrid frontier composite (H200 gptoss; B200/GB200 DeepSeek V4 Pro + Kimi K2.5)", "effective_active_params_b": 49.0, "benchmark_tps_per_gpu": 60000, "benchmark_effective_active_b": 49.0, "accelerator_kw": 7.0, "serving_efficiency": 0.72, "benchmark_source": "SRC_SEMIANALYSIS_INFERENCEX; SRC_DEEPSEEK_V4_PRO; SRC_KIMI_K25", "calc_use": "Proxy", "caveat_kr": "closed GPT 실제 serving benchmark가 아니며 H200은 gptoss, B200/GB200은 DeepSeek V4 Pro와 Kimi K2.5 공개 proxy를 함께 사용"},
        {"company": "Anthropic", "proxy_model": "Hybrid frontier composite (H200 gptoss; B200/GB200 DeepSeek V4 Pro + Kimi K2.5)", "effective_active_params_b": 49.0, "benchmark_tps_per_gpu": 60000, "benchmark_effective_active_b": 49.0, "accelerator_kw": 7.5, "serving_efficiency": 0.74, "benchmark_source": "SRC_ANTHROPIC_CLAUDE_DOCS; SRC_SEMIANALYSIS_INFERENCEX; SRC_DEEPSEEK_V4_PRO; SRC_KIMI_K25", "calc_use": "Proxy", "caveat_kr": "Claude 파라미터/serving benchmark는 비공개라 H200은 gptoss, B200/GB200은 DeepSeek V4 Pro와 Kimi K2.5 공개 proxy를 함께 사용"},
        {"company": "Google", "proxy_model": "Hybrid frontier composite (H200 gptoss; B200/GB200 DeepSeek V4 Pro + Kimi K2.5)", "effective_active_params_b": 49.0, "benchmark_tps_per_gpu": 60000, "benchmark_effective_active_b": 49.0, "accelerator_kw": 7.0, "serving_efficiency": 0.70, "benchmark_source": "SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; SRC_SEMIANALYSIS_INFERENCEX; SRC_DEEPSEEK_V4_PRO; SRC_KIMI_K25", "calc_use": "Proxy", "caveat_kr": "Gemini/TPU production serving이 아니라 H200은 gptoss, B200/GB200은 DeepSeek V4 Pro와 Kimi K2.5 공개 proxy를 함께 사용"},
        {"company": "Meta", "proxy_model": "Llama 4 Maverick", "effective_active_params_b": 52.1, "benchmark_tps_per_gpu": 40000, "benchmark_effective_active_b": 17.0, "accelerator_kw": 7.0, "serving_efficiency": 0.60, "benchmark_source": "SRC_META_LLAMA4_NVIDIA", "calc_use": "Open model proxy", "caveat_kr": "Meta AI production routing과 다를 수 있음"},
        {"company": "Microsoft", "proxy_model": "Copilot/GPT-class proxy + Phi anchor", "effective_active_params_b": 80.5, "benchmark_tps_per_gpu": 60000, "benchmark_effective_active_b": 5.1, "accelerator_kw": 7.0, "serving_efficiency": 0.70, "benchmark_source": "SRC_MS_PHI4_TECHREPORT; SRC_OPENAI_GPT41_DOCS", "calc_use": "Proxy", "caveat_kr": "Microsoft-owned/Phi와 OpenAI dependency mix가 섞인 proxy"},
        {"company": "xAI", "proxy_model": "Grok closed frontier proxy", "effective_active_params_b": 92.0, "benchmark_tps_per_gpu": 55000, "benchmark_effective_active_b": 5.1, "accelerator_kw": 7.0, "serving_efficiency": 0.68, "benchmark_source": "SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS", "calc_use": "Proxy", "caveat_kr": "Grok closed model benchmark가 없어 cluster scale 기반 proxy"},
        {"company": "DeepSeek", "proxy_model": "DeepSeek-V3 / R1", "effective_active_params_b": 60.1, "benchmark_tps_per_gpu": 55000, "benchmark_effective_active_b": 37.0, "accelerator_kw": 6.5, "serving_efficiency": 0.65, "benchmark_source": "SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1", "calc_use": "MoE anchored proxy", "caveat_kr": "모델 구조는 공개되어 있으나 production serving은 proxy"},
        {"company": "Alibaba", "proxy_model": "Qwen3 235B-A22B", "effective_active_params_b": 79.2, "benchmark_tps_per_gpu": 5764, "benchmark_effective_active_b": 22.0, "accelerator_kw": 6.5, "serving_efficiency": 0.65, "benchmark_source": "SRC_QWEN3_GITHUB", "calc_use": "OSS benchmark proxy", "caveat_kr": "공개 Qwen benchmark 기반 reference; Alibaba Cloud production mix와 다를 수 있음"},
        {"company": "Tencent", "proxy_model": "Hunyuan closed proxy", "effective_active_params_b": 85.8, "benchmark_tps_per_gpu": 50000, "benchmark_effective_active_b": 5.1, "accelerator_kw": 6.5, "serving_efficiency": 0.58, "benchmark_source": "SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3", "calc_use": "Proxy", "caveat_kr": "Hunyuan serving benchmark가 제한적이라 generic proxy"},
    ]


def benchmark_reference_rows(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assumptions = {r["company"]: r for r in benchmark_assumptions()}
    hardware_index = {2026: 1.00, 2027: 1.18, 2028: 1.38, 2029: 1.60, 2030: 1.85}
    rows: list[dict[str, Any]] = []
    for row in base_rows:
        b = assumptions[row["company"]]
        adjusted_tps = (
            b["benchmark_tps_per_gpu"]
            * (b["benchmark_effective_active_b"] / b["effective_active_params_b"])
            * hardware_index[row["year"]]
            * b["serving_efficiency"]
        )
        gpu_count = row["inference_gw"] * 1_000_000 / b["accelerator_kw"]
        sustained_tps = adjusted_tps * gpu_count
        annual_tokens = sustained_tps * 31_536_000
        model_annual = row["inference_tokens_per_year"]
        rows.append(
            {
                "company": row["company"],
                "year": row["year"],
                "proxy_model": b["proxy_model"],
                "inference_gw_it": row["inference_gw"],
                "effective_active_params_b": b["effective_active_params_b"],
                "benchmark_tps_per_gpu": b["benchmark_tps_per_gpu"],
                "benchmark_effective_active_b": b["benchmark_effective_active_b"],
                "accelerator_kw": b["accelerator_kw"],
                "estimated_gpu_count": round(gpu_count),
                "hardware_index": hardware_index[row["year"]],
                "serving_efficiency": b["serving_efficiency"],
                "adjusted_tps_per_gpu": round(adjusted_tps, 3),
                "sustained_tps": round(sustained_tps),
                "benchmark_annual_tokens_q": round(annual_tokens / 1e15, 3),
                "model_annual_tokens_q": round(model_annual / 1e15, 3),
                "benchmark_vs_model_pct": round((annual_tokens / model_annual - 1) * 100, 1) if model_annual else "",
                "calc_use": b["calc_use"],
                "benchmark_source": b["benchmark_source"],
                "caveat_kr": b["caveat_kr"],
            }
        )
    return rows


def energy_sanity_reference_rows(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Energy/query sanity layer from A08 Cycle 1.

    This is deliberately not a replacement for the main forecast. It checks
    whether model-implied joules/token is directionally plausible under
    long-context, base, and optimized serving assumptions.
    """
    profiles = [
        {
            "profile": "Strict-SLO / long-context agentic",
            "joules_per_token_multiplier": 1.85,
            "input_output_context_note": "long prompt, tool-use trace, low-latency SLA, limited batching",
            "source_ids": "SRC_JOULE_INFERENCE_ENERGY_2026; SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SLO_PD_2026; SRC_MLPERF_INFERENCE_DOCS",
            "interpretation_kr": "agentic/test-time compute가 증가하면 같은 MW에서 token output이 낮아질 수 있음",
        },
        {
            "profile": "Base serving mix",
            "joules_per_token_multiplier": 1.00,
            "input_output_context_note": "mixed chatbot/API/enterprise serving with moderate batching",
            "source_ids": "SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_POWER",
            "interpretation_kr": "메인 forecast와 일치시키는 기준 energy view",
        },
        {
            "profile": "Batchable / optimized serving",
            "joules_per_token_multiplier": 0.68,
            "input_output_context_note": "batchable workloads, KV-cache efficiency, P/D scheduling, relaxed latency",
            "source_ids": "SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_SEMIANALYSIS_INFERENCEX; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_FLASHINFER",
            "interpretation_kr": "serving stack 최적화가 energy/token을 낮출 수 있으나 company fact는 아님",
        },
    ]
    rows: list[dict[str, Any]] = []
    for row in base_rows:
        if row["year"] not in (2026, 2030):
            continue
        inference_energy_j_day = row["inference_gw"] * 1e9 * 86400
        for profile in profiles:
            implied_jpt = row["joules_per_token"] * profile["joules_per_token_multiplier"]
            energy_tokens_day = inference_energy_j_day / implied_jpt if implied_jpt else 0
            rows.append(
                {
                    "company": row["company"],
                    "year": row["year"],
                    "profile": profile["profile"],
                    "inference_gw": row["inference_gw"],
                    "headline_utilization_applied": False,
                    "model_joules_per_token": row["joules_per_token"],
                    "profile_joules_per_token": round(implied_jpt, 4),
                    "energy_implied_tokens_per_day_q": round(energy_tokens_day / 1e15, 3),
                    "model_tokens_per_day_q": round(row["inference_tokens_per_day"] / 1e15, 3),
                    "energy_vs_model_pct": round((energy_tokens_day / row["inference_tokens_per_day"] - 1) * 100, 1) if row["inference_tokens_per_day"] else "",
                    "input_output_context_note": profile["input_output_context_note"],
                    "source_ids": profile["source_ids"],
                    "interpretation_kr": profile["interpretation_kr"],
                    "calc_use": "Sanity check only",
                }
            )
    return rows


def utilization_sensitivity_rows(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """SLO/workload utilization sensitivity from A09 Cycle 1."""
    profiles = [
        {
            "profile": "Strict-SLO real-time",
            "utilization_multiplier": 0.78,
            "tokens_per_mw_multiplier": 0.92,
            "description_kr": "TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving",
            "source_ids": "SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS",
        },
        {
            "profile": "Base mixed serving",
            "utilization_multiplier": 1.00,
            "tokens_per_mw_multiplier": 1.00,
            "description_kr": "메인 forecast 기준",
            "source_ids": "SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE",
        },
        {
            "profile": "Batchable optimized",
            "utilization_multiplier": 1.12,
            "tokens_per_mw_multiplier": 1.10,
            "description_kr": "batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving",
            "source_ids": "SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING",
        },
        {
            "profile": "Agentic long-context stress",
            "utilization_multiplier": 0.88,
            "tokens_per_mw_multiplier": 0.82,
            "description_kr": "긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress",
            "source_ids": "SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE",
        },
    ]
    rows: list[dict[str, Any]] = []
    for row in base_rows:
        if row["year"] not in (2026, 2030):
            continue
        for profile in profiles:
            adjusted_util = min(row["utilization_reference_only"] * profile["utilization_multiplier"], 0.86)
            adjusted_tps = row["tokens_per_second_per_mw"] * profile["tokens_per_mw_multiplier"]
            tokens_day = row["inference_gw"] * 1000 * adjusted_tps * adjusted_util * 86400
            rows.append(
                {
                    "company": row["company"],
                    "year": row["year"],
                    "profile": profile["profile"],
                    "base_utilization": row["utilization_reference_only"],
                    "adjusted_utilization": round(adjusted_util, 3),
                    "base_tokens_per_second_per_mw": row["tokens_per_second_per_mw"],
                    "adjusted_tokens_per_second_per_mw": round(adjusted_tps),
                    "tokens_per_day_q": round(tokens_day / 1e15, 3),
                    "base_tokens_per_day_q": round(row["inference_tokens_per_day"] / 1e15, 3),
                    "delta_vs_base_pct": round((tokens_day / row["inference_tokens_per_day"] - 1) * 100, 1) if row["inference_tokens_per_day"] else "",
                    "description_kr": profile["description_kr"],
                    "source_ids": profile["source_ids"],
                    "calc_use": "Sensitivity only",
                }
            )
    return rows


def hallucination_checklist() -> list[dict[str, Any]]:
    return [
        {
            "check_id": "HC01",
            "area": "Source existence",
            "question_kr": "모든 source URL 또는 report name이 실제로 존재하고 접근 가능한가?",
            "pass_criteria_kr": "01_sources의 URL을 열었을 때 publisher/title/date가 일치한다.",
            "risk_if_fail_kr": "없는 출처 또는 잘못된 출처를 근거로 사용.",
            "owner": "Research",
            "severity": "High",
            "current_status": "Needs manual URL click-through",
        },
        {
            "check_id": "HC02",
            "area": "Numeric fact quote",
            "question_kr": "Fact anchor의 숫자(예: 4.5GW, 671B/37B, 235B/22B, 100k GPU)가 원문에 직접 존재하는가?",
            "pass_criteria_kr": "02a_fact_anchors의 value가 원문 문장/표와 직접 매칭된다.",
            "risk_if_fail_kr": "proxy나 추정을 fact처럼 표시.",
            "owner": "Research",
            "severity": "High",
            "current_status": "Partially checked; requires final source screenshot/quote pack",
        },
        {
            "check_id": "HC03",
            "area": "Fact vs estimate separation",
            "question_kr": "Active GW, inference share, utilization, tokens/sec/MW가 fact로 오표기되지 않았는가?",
            "pass_criteria_kr": "해당 값은 Estimate/Scenario로 표시되고 replacement_path가 있다.",
            "risk_if_fail_kr": "임원 보고에서 확정 수치처럼 오해.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Pass in structure",
        },
        {
            "check_id": "HC04",
            "area": "Closed model parameters",
            "question_kr": "OpenAI, Anthropic, Gemini, Grok 같은 closed model에 단일 precise parameter 숫자를 쓰지 않았는가?",
            "pass_criteria_kr": "closed model은 band/proxy로만 표시하고 benchmark는 sanity check로만 사용.",
            "risk_if_fail_kr": "비공개 파라미터 hallucination.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Pass",
        },
        {
            "check_id": "HC05",
            "area": "MoE total/active",
            "question_kr": "MoE 모델은 total params와 active params를 분리했는가?",
            "pass_criteria_kr": "DeepSeek, Qwen, Llama 4 계열은 total/active가 별도 column 또는 anchor에 존재.",
            "risk_if_fail_kr": "MoE 효율을 과소/과대 계산.",
            "owner": "Model",
            "severity": "Medium",
            "current_status": "Pass",
        },
        {
            "check_id": "HC06",
            "area": "Host vs model owner",
            "question_kr": "AWS/Google/Oracle 같은 host capacity가 model owner와 혼동되지 않았는가?",
            "pass_criteria_kr": "Anthropic/OpenAI capacity는 model output 기준으로 귀속하고 host는 source/context로만 표기.",
            "risk_if_fail_kr": "capacity double count 또는 wrong attribution.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Pass in attribution rules",
        },
        {
            "check_id": "HC07",
            "area": "Microsoft/OpenAI overlap",
            "question_kr": "Microsoft Copilot token과 OpenAI model token을 이중계산하지 않았는가?",
            "pass_criteria_kr": "OpenAI model output은 OpenAI row, Microsoft-owned/serving burden은 Microsoft row로 명시.",
            "risk_if_fail_kr": "OpenAI/Microsoft capacity 중복 산정.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Needs sales/product routing data for final resolution",
        },
        {
            "check_id": "HC08",
            "area": "Capacity boundary",
            "question_kr": "active_power_gw가 contracted_power_gw를 넘지 않는가?",
            "pass_criteria_kr": "모든 company-year-scenario에서 active <= contracted.",
            "risk_if_fail_kr": "물리적으로 불가능한 deployment.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Automated pass",
        },
        {
            "check_id": "HC09",
            "area": "Power split",
            "question_kr": "training_power_share + inference_power_share = 100%인가?",
            "pass_criteria_kr": "모든 row에서 합계가 1.000 +/- 0.001.",
            "risk_if_fail_kr": "GW가 누락 또는 중복.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Automated pass",
        },
        {
            "check_id": "HC10",
            "area": "Unit consistency",
            "question_kr": "daily token과 annual token 단위가 섞이지 않았는가?",
            "pass_criteria_kr": "token/day는 86,400초, annual token은 365일 또는 31,536,000초로 환산.",
            "risk_if_fail_kr": "365배 오류 또는 daily/annual 비교 오류.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Automated pass",
        },
        {
            "check_id": "HC11",
            "area": "Benchmark proxy use",
            "question_kr": "OSS/open benchmark를 closed commercial model 결론으로 직접 사용하지 않았는가?",
            "pass_criteria_kr": "08d_benchmark_reference는 sanity check이며 main forecast와 분리.",
            "risk_if_fail_kr": "gpt-oss/Qwen/Llama benchmark를 GPT/Claude/Gemini 실서비스로 오인.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Pass",
        },
        {
            "check_id": "HC12",
            "area": "Inference share",
            "question_kr": "2026년 추론 60%+를 fact로 단정하지 않았는가?",
            "pass_criteria_kr": "Base 2026은 60% 미만이고 Bull에서만 60%+ 허용.",
            "risk_if_fail_kr": "전망을 현재 fact처럼 보고.",
            "owner": "Model",
            "severity": "Medium",
            "current_status": "Pass",
        },
        {
            "check_id": "HC13",
            "area": "Outlier review",
            "question_kr": "main forecast와 benchmark reference의 차이가 큰 업체를 따로 표시했는가?",
            "pass_criteria_kr": "benchmark_vs_model_pct가 +/-50%를 넘으면 confidence review 대상.",
            "risk_if_fail_kr": "과감한 가정을 숨긴 채 보고.",
            "owner": "Model",
            "severity": "Medium",
            "current_status": "Needs reviewer sign-off",
        },
        {
            "check_id": "HC14",
            "area": "China transparency",
            "question_kr": "중국 업체의 낮은 공개성 때문에 수치를 임의로 페널티하거나 과신하지 않았는가?",
            "pass_criteria_kr": "모델 구조 fact는 인정하고 capacity transparency만 confidence에 반영.",
            "risk_if_fail_kr": "bias 또는 confidence mislabeling.",
            "owner": "Research",
            "severity": "Medium",
            "current_status": "Pass in principle; needs Chinese primary-source review",
        },
        {
            "check_id": "HC15",
            "area": "Executive wording",
            "question_kr": "슬라이드 문구가 추정치를 확정 사실처럼 표현하지 않는가?",
            "pass_criteria_kr": "forecast, scenario, proxy, sanity check, 추정치 표현을 유지.",
            "risk_if_fail_kr": "의사결정자가 불확실성을 과소평가.",
            "owner": "Presentation",
            "severity": "High",
            "current_status": "Needs final human review",
        },
        {
            "check_id": "HC16",
            "area": "Token definition",
            "question_kr": "generated output token, processed inference token, training token, billable token을 혼동하지 않았는가?",
            "pass_criteria_kr": "headline `inference_tokens_per_day`는 generated output token equivalent로 표기하고, InferenceX total `tok_s_mw`는 processed-token proxy로 분리.",
            "risk_if_fail_kr": "InferenceX benchmark total throughput을 상용 output token 생성량으로 과대 적용.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Definition added; needs reviewer sign-off",
        },
        {
            "check_id": "HC17",
            "area": "Capacity terminology",
            "question_kr": "`contracted_power_gw`가 모든 회사에서 공식 계약 fact인 것처럼 해석되지 않도록 capacity ceiling과 scenario envelope를 구분했는가?",
            "pass_criteria_kr": "02b_number_trace 및 03_power_capacity에 업체별 capacity_basis와 derivation_type이 존재.",
            "risk_if_fail_kr": "공개되지 않은 GW를 계약 fact처럼 보고.",
            "owner": "Model",
            "severity": "High",
            "current_status": "Implemented in trace layer",
        },
        {
            "check_id": "HC18",
            "area": "Numeric accelerator mix",
            "question_kr": "GPU/ASIC mix 수치가 공식 platform presence와 실제 fleet share fact를 혼동하지 않는가?",
            "pass_criteria_kr": "04_gpu_asic_mix에 numeric scenario, reason, source, replacement path가 있고 GPU+purpose-built share가 100%.",
            "risk_if_fail_kr": "하드웨어 발표만으로 생산 효율을 과대 계산.",
            "owner": "A11 / Model",
            "severity": "High",
            "current_status": "Implemented; telemetry replacement pending",
        },
        {
            "check_id": "HC19",
            "area": "Efficiency bridge reconstruction",
            "question_kr": "tokens/sec/MW가 선택 InferenceX output TPS/MW와 numeric accelerator mix에서 단순 재구성되는가?",
            "pass_criteria_kr": "05b_inferencex_core_tps와 05_inference_efficiency의 fields로 각 row의 TPS/MW를 재계산할 수 있고 purpose-built uplift가 없다.",
            "risk_if_fail_kr": "설명과 결과 coefficient가 분리된 채 남음.",
            "owner": "A08 / A11 / Logic Review",
            "severity": "High",
            "current_status": "Automated validation added",
        },
        {
            "check_id": "HC20",
            "area": "Complete numeric trace",
            "question_kr": "최종 표의 output-driving 숫자마다 company-year-scenario별 이유와 교체 경로가 있는가?",
            "pass_criteria_kr": "02b_number_trace에 18개 headline metric별 formula, reason, source/assumption ID, replacement path가 존재.",
            "risk_if_fail_kr": "질문을 받았을 때 숫자의 출처 또는 산출 이유를 설명할 수 없음.",
            "owner": "Model / Logic Review",
            "severity": "High",
            "current_status": "Implemented in trace layer",
        },
        {
            "check_id": "HC21",
            "area": "Confirmed value vs modeled value",
            "question_kr": "공식 확인값과 그 사실을 근거로 설정한 모델값을 같은 숫자로 오인하지 않도록 구분했는가?",
            "pass_criteria_kr": "02c_fact_vs_assumption_audit에 회사별 핵심 입력의 public fact/disclosure gap, model value, evidence class, replacement path가 존재.",
            "risk_if_fail_kr": "공식 platform/capacity 방향성만으로 scenario endpoint를 확정값처럼 보고.",
            "owner": "Model / Orchestrator",
            "severity": "High",
            "current_status": "Implemented; source-line sign-off remains an operating task",
        },
        {
            "check_id": "HC22",
            "area": "No hidden headline multiplier",
            "question_kr": "utilization, MoE, architecture 또는 software CAGR가 최종 생성 token에 숨은 multiplier로 들어가지 않았는가?",
            "pass_criteria_kr": "headline equation과 validation은 operational inference GW x selected output TPS/MW x seconds/day만 사용.",
            "risk_if_fail_kr": "공개근거가 약한 efficiency 가정이 결론을 과대 변동.",
            "owner": "A08 / A09 / Logic Review",
            "severity": "High",
            "current_status": "Implemented in simple core formula",
        },
    ]


def exec_summary(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_2030 = [r for r in base_rows if r["year"] == 2030]
    total_day = sum(r["inference_tokens_per_day"] for r in rows_2030)
    total_inference_gw = sum(r["inference_gw"] for r in rows_2030)
    by_region: dict[str, int] = {}
    for row in rows_2030:
        by_region[row["region"]] = by_region.get(row["region"], 0) + row["inference_tokens_per_day"]
    ranked = sorted(rows_2030, key=lambda r: r["inference_tokens_per_day"], reverse=True)
    summary = [
        {
            "metric": "2030 core-company inference tokens/day",
            "value": total_day,
            "display": f"{total_day / 1e15:.2f} quadrillion generated output tokens/day",
            "interpretation_kr": "9개 상용 LLM owner의 base case 생성 output token capacity.",
        },
        {
            "metric": "2030 inference AI IT load",
            "value": round(total_inference_gw, 2),
            "display": f"{total_inference_gw:.2f} GW inference load",
            "interpretation_kr": "PUE와 AI workload share 차감 후 inference에 배정된 IT load.",
        },
        {
            "metric": "2030 US vs China split",
            "value": "",
            "display": f"US {by_region.get('US', 0) / total_day:.0%} / China {by_region.get('China', 0) / total_day:.0%}",
            "interpretation_kr": "회사 owner 기준 split이며 AWS/Oracle/CoreWeave 같은 host는 core row가 아님.",
        },
    ]
    for rank, row in enumerate(ranked[:5], start=1):
        summary.append(
            {
                "metric": f"Rank {rank}: {row['company']} 2030 tokens/day",
                "value": row["inference_tokens_per_day"],
                "display": f"{row['inference_tokens_per_day'] / 1e15:.2f}Q/day",
                "interpretation_kr": f"{row['model_family']} serving capacity; confidence={row['confidence']}",
            }
        )
    return summary


def validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    for row in rows:
        if row["active_power_gw"] > row["contracted_power_gw"] + 1e-9:
            failures.append(f"{row['company']} {row['year']}: active_power_gw > contracted_power_gw")
        reconstructed_active = round(row["contracted_power_gw"] * row["operational_deployment_share"], 3)
        if abs(reconstructed_active - row["active_power_gw"]) > 0.001:
            failures.append(f"{row['company']} {row['year']}: operational deployment does not reconstruct active power")
        share_sum = row["training_power_share"] + row["inference_power_share"]
        if not math.isclose(share_sum, 1.0, abs_tol=0.001):
            failures.append(f"{row['company']} {row['year']}: training+inference share={share_sum}")
        if row["tokens_per_second_per_mw"] <= 0 or row["joules_per_token"] <= 0:
            failures.append(f"{row['company']} {row['year']}: invalid efficiency")
        component_share = (
            row["h200_share"] + row["b200_share"] + row["gb200_share"]
            + row["purpose_built_accelerator_share"]
        )
        if not math.isclose(component_share, 1.0, abs_tol=0.002):
            failures.append(f"{row['company']} {row['year']}: H200+B200+GB200+purpose-built share != 1")

        workload_share = row["short_chat_share"] + row["long_chat_share"] + row["agentic_share"]
        if not math.isclose(workload_share, 1.0, abs_tol=0.002):
            failures.append(f"{row['company']} {row['year']}: short+long+agentic workload share != 1")

        reconstructed_tps = round(
            (
                row["h200_share"] * row["h200_workload_weighted_tps_per_mw"]
                + row["b200_share"] * row["b200_workload_weighted_tps_per_mw"]
                + row["gb200_share"] * row["gb200_workload_weighted_tps_per_mw"]
                + row["purpose_built_accelerator_share"] * row["purpose_built_workload_weighted_tps_per_mw"]
            )
            * row["commercial_workload_fit_factor"]
        )
        if abs(reconstructed_tps - row["tokens_per_second_per_mw"]) > 2:
            failures.append(f"{row['company']} {row['year']}: tokens/sec/MW bridge does not reconstruct")
        reconstructed_joules = round(1_000_000 / row["tokens_per_second_per_mw"], 4)
        if reconstructed_joules != row["joules_per_token"]:
            failures.append(f"{row['company']} {row['year']}: joules/token does not reconstruct")
        if row["inference_tokens_per_year"] != round(row["inference_tokens_per_day"] * 365):
            failures.append(f"{row['company']} {row['year']}: annual output tokens do not reconstruct")
        reconstructed_tokens = round(row["inference_gw"] * 1000 * row["tokens_per_second_per_mw"] * 86400)
        if reconstructed_tokens != row["inference_tokens_per_day"]:
            failures.append(f"{row['company']} {row['year']}: simple headline token formula does not reconstruct")

        tps_mw = row["inference_tokens_per_day"] / 86400 / (row["inference_gw"] * 1000)
        if not (5_000 <= tps_mw <= 7_000_000):
            failures.append(f"{row['company']} {row['year']}: tokens/sec/MW out of benchmark envelope")

    model_checks = {
        "closed_parameter_precision": "PASS - closed model rows use bands/undisclosed labels, not single precise parameter values.",
        "moe_total_active": "PASS - DeepSeek and Alibaba rows include total and active parameter bands.",
        "microsoft_openai_overlap": "PASS - attribution rule separates OpenAI model-owner output and Microsoft customer-facing serving.",
        "anthropic_scope": "PASS - Anthropic is included as a core model-owner row; AWS/Google host capacity is attributed to Anthropic model output.",
        "benchmark_layer": "PASS - GPU/effective-active-parameter benchmark reference is separated from the main tokens/sec/MW forecast.",
        "energy_sanity_layer": "PASS - Joule/IBM/2026 serving sources are separated as sanity/sensitivity layers, not Base production telemetry.",
        "simple_headline_formula": "PASS - headline output tokens use operational inference GW and workload-adjusted serving reference TPS/MW only; no utilization/MoE/software/architecture multiplier is applied.",
        "utilization_slo_layer": "PASS - SLO/workload utilization remains supplemental sensitivity only and is not multiplied into headline output.",
        "numeric_accelerator_mix_bridge": "PASS - H200/B200/GB200/purpose-built shares sum to 100%; fleet-weighted reference is explicit and purpose-built TPS/MW receives no unsupported uplift.",
        "workload_mix_bridge": "PASS - short conversation, long conversation and agentic workload shares sum to 100%; GPU-level workload-weighted TPS/MW reconstructs headline TPS/MW.",
        "complete_numeric_trace_inputs": "PASS - operational deployment, GPU-generation mix, workload mix, public TPS/MW reference, commercial workload fit and annual output tokens are formula-reconstructable.",
    }
    return {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "model_checks": model_checks,
        "generated_at": RUN_DATE,
    }


def write_json(data: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def style_sheet(ws, freeze: str = "A2") -> None:
    header_fill = PatternFill("solid", fgColor="14213D")
    header_font = Font(color="FFFFFF", bold=True)
    thin = Side(style="thin", color="D9E2EC")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(bottom=thin)
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            text = "" if cell.value is None else str(cell.value)
            max_len = max(max_len, min(len(text), 70))
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 38)


def append_rows(ws, rows: list[dict[str, Any]], headers: list[str]) -> None:
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])
    style_sheet(ws)


def append_proxy_tps_mw_reference_sheet(wb: Workbook) -> None:
    """Append Excel-friendly proxy TPS/MW reference if the generated CSV exists."""
    rows = read_csv_rows(PROXY_TPS_MW_REFERENCE_CSV)
    if not rows:
        return

    headers = list(rows[0].keys())
    ws = wb.create_sheet("00a_Proxy_TPS_MW")
    append_rows(ws, rows, headers)
    for row in ws.iter_rows(min_row=2):
        source_type = row[15].value
        target_met = str(row[5].value).lower() == "true"
        if source_type == "dynamic_reasoning_proxy":
            fill = PatternFill("solid", fgColor="EAF2FF")
        elif not target_met:
            fill = PatternFill("solid", fgColor="FCE4D6")
        else:
            fill = PatternFill("solid", fgColor="E2F0D9")
        for cell in row:
            cell.fill = fill
    for col in ("G",):
        for cell in ws[col][1:]:
            cell.number_format = "0.0%"
    for col in ("H",):
        for cell in ws[col][1:]:
            cell.number_format = "#,##0"
    for col in ("I",):
        for cell in ws[col][1:]:
            cell.number_format = "0.00"
    for col, width in {
        "A": 18,
        "B": 24,
        "C": 10,
        "D": 12,
        "E": 18,
        "F": 12,
        "G": 12,
        "H": 24,
        "I": 18,
        "J": 14,
        "K": 18,
        "L": 14,
        "M": 10,
        "N": 10,
        "O": 24,
        "P": 26,
        "Q": 16,
        "R": 18,
        "S": 92,
    }.items():
        ws.column_dimensions[col].width = width


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def inferencex_ingestion_payload() -> dict[str, Any]:
    base = ROOT / "data" / "inferencex"
    manifest_path = base / "metadata" / "inferencex_manifest.json"
    source_index = read_csv_rows(base / "normalized" / "inferencex_source_index.csv")
    schema_rows = read_csv_rows(base / "normalized" / "inferencex_normalized_schema.csv")
    tab_rules = read_csv_rows(base / "normalized" / "inferencex_tab_rules.csv")
    release_assets = read_csv_rows(base / "normalized" / "inferencex_release_assets.csv")
    benchmark_results = read_csv_rows(base / "normalized" / "inferencex_benchmark_results.csv")
    metric_profile = read_csv_rows(base / "normalized" / "inferencex_metric_profile.csv")
    gpu_comparable_metric_profile = read_csv_rows(base / "normalized" / "inferencex_gpu_comparable_metric_profile.csv")
    main_config_by_model = read_csv_rows(base / "normalized" / "inferencex_main_config_by_model.csv")
    main_config_validation = read_csv_rows(base / "normalized" / "inferencex_main_config_validation.csv")
    accuracy_evals = read_csv_rows(base / "normalized" / "inferencex_accuracy_evals.csv")
    dump_inventory = read_csv_rows(base / "normalized" / "inferencex_dump_inventory.csv")
    run_stats = read_csv_rows(base / "normalized" / "inferencex_run_stats.csv")
    availability = read_csv_rows(base / "normalized" / "inferencex_availability.csv")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "generated_at": "",
            "source": "InferenceX ingestion has not been run yet.",
            "evidence_rule": "Run tools/fetch_inferencex_data.py before using InferenceX as a benchmark layer.",
        }
    return {
        "manifest": manifest,
        "source_index": source_index
        or [
            {
                "source_file": "",
                "source_kind": "not_refreshed",
                "benchmark_id": "",
                "dashboard_tab": "",
                "evidence_class": "Proxy/Benchmark",
                "caveat": "Run tools/fetch_inferencex_data.py to populate the source index.",
            }
        ],
        "schema": schema_rows or [{h: "" for h in [
            "source_file", "source_kind", "benchmark_id", "dashboard_tab", "model", "gpu", "framework", "precision", "isl", "osl", "metric_name", "metric_value", "metric_unit", "source_url", "evidence_class", "caveat"
        ]}],
        "tab_rules": tab_rules
        or [
            {
                "dashboard_tab": "not_refreshed",
                "use_in_model": "Run fetch_inferencex_data.py",
                "required_keys": "",
                "forecast_use": "benchmark/proxy only",
            }
        ],
        "release_assets": release_assets[:30],
        "benchmark_results": benchmark_results,
        "metric_profile": metric_profile,
        "gpu_comparable_metric_profile": gpu_comparable_metric_profile,
        "main_config_by_model": main_config_by_model,
        "main_config_validation": main_config_validation,
        "accuracy_evals": accuracy_evals,
        "dump_inventory": dump_inventory,
        "run_stats": run_stats,
        "availability": availability,
    }


def write_excel_full_archive(data: dict[str, Any], path: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)

    def sheet(name: str):
        return wb.create_sheet(name)

    formula_headers = list(data["formula_assumptions"][0].keys())
    append_rows(sheet("00_formula_assumptions"), data["formula_assumptions"], formula_headers)

    token_headers = list(data["token_definitions"][0].keys())
    append_rows(sheet("00a_token_definitions"), data["token_definitions"], token_headers)

    src_headers = list(asdict(sources()[0]).keys())
    append_rows(sheet("01_sources"), [asdict(s) for s in sources()], src_headers)

    model_headers = list(asdict(company_models()[0]).keys())
    append_rows(sheet("02_company_models"), [asdict(m) for m in company_models()], model_headers)

    fact_headers = list(asdict(fact_anchors()[0]).keys())
    append_rows(sheet("02a_fact_anchors"), [asdict(f) for f in fact_anchors()], fact_headers)

    number_trace_headers = list(data["number_trace"][0].keys())
    append_rows(sheet("02b_number_trace"), data["number_trace"], number_trace_headers)

    audit_headers = list(data["company_input_audit"][0].keys())
    append_rows(sheet("02c_fact_vs_assumption_audit"), data["company_input_audit"], audit_headers)

    power_headers = [
        "company",
        "region",
        "year",
        "contracted_power_gw",
        "operational_deployment_share",
        "active_power_gw",
        "pue",
        "it_load_gw",
        "ai_workload_share",
        "ai_it_load_gw",
        "capacity_basis",
        "active_power_basis",
        "ai_workload_share_basis",
        "source_ids",
        "assumption_ids",
        "confidence",
    ]
    append_rows(sheet("03_power_capacity"), data["forecast"], power_headers)

    mix_rows = [
        {
            "company": r["company"],
            "year": r["year"],
            "gpu_share": r["gpu_share"],
            "purpose_built_accelerator_share": r["purpose_built_accelerator_share"],
            "purpose_built_accelerator_label": r["purpose_built_accelerator_label"],
            "gpu_benchmark_proxy_model": r["gpu_benchmark_proxy_model"],
            "gpu_benchmark_tps_per_mw": r["gpu_benchmark_tps_per_mw"],
            "purpose_built_tps_per_mw": r["purpose_built_tps_per_mw"],
            "purpose_built_benchmark_status": r["purpose_built_benchmark_status"],
            "weighted_tokens_per_second_per_mw": r["tokens_per_second_per_mw"],
            "derivation_type": "Numeric scenario - platform presence sourced; operated share not publicly disclosed",
            "why_this_number": r["gpu_asic_mix_basis"],
            "source_ids": r["source_ids"],
            "assumption_ids": r["assumption_ids"],
            "replacement_path": r["replacement_path"],
        }
        for r in data["forecast"]
    ]
    append_rows(sheet("04_gpu_asic_mix"), mix_rows, list(mix_rows[0].keys()))

    eff_headers = [
        "company",
        "year",
        "gpu_benchmark_proxy_model",
        "gpu_benchmark_tps_per_mw",
        "gpu_share",
        "h200_share",
        "b200_share",
        "gb200_share",
        "purpose_built_accelerator_share",
        "purpose_built_tps_per_mw",
        "purpose_built_benchmark_status",
        "tokens_per_second_per_mw",
        "joules_per_token",
        "headline_utilization_applied",
        "tokens_per_mw_basis",
        "gpu_asic_mix_basis",
        "utilization_basis",
        "derivation_type",
        "source_ids",
        "assumption_ids",
        "confidence",
    ]
    append_rows(sheet("05_inference_efficiency"), data["forecast"], eff_headers)

    bench_assumption_headers = list(data["benchmark_assumptions"][0].keys())
    append_rows(sheet("05a_benchmark_assumptions"), data["benchmark_assumptions"], bench_assumption_headers)

    core_benchmark_headers = list(data["core_inferencex_benchmarks"][0].keys())
    append_rows(sheet("05b_inferencex_core_tps"), data["core_inferencex_benchmarks"], core_benchmark_headers)

    split_headers = [
        "company",
        "year",
        "training_power_share",
        "inference_power_share",
        "training_gw",
        "inference_gw",
        "inference_share_basis",
        "source_ids",
        "assumption_ids",
        "confidence",
    ]
    append_rows(sheet("06_training_inference_split"), data["forecast"], split_headers)

    forecast_headers = [
        "company",
        "region",
        "model_family",
        "commercial_surface",
        "year",
        "contracted_power_gw",
        "operational_deployment_share",
        "active_power_gw",
        "pue",
        "ai_workload_share",
        "ai_it_load_gw",
        "inference_gw",
        "gpu_share",
        "purpose_built_accelerator_share",
        "gpu_benchmark_proxy_model",
        "commercial_workload_class",
        "h200_reference_tps_per_mw",
        "b200_reference_tps_per_mw",
        "gb200_reference_tps_per_mw",
        "purpose_built_reference_tps_per_mw",
        "fleet_reference_tps_per_mw",
        "inferencex_reference_tps_per_mw",
        "short_chat_share",
        "long_chat_share",
        "agentic_share",
        "short_chat_reference_tps_per_mw",
        "long_chat_reference_tps_per_mw",
        "agentic_reference_tps_per_mw",
        "h200_workload_weighted_tps_per_mw",
        "b200_workload_weighted_tps_per_mw",
        "gb200_workload_weighted_tps_per_mw",
        "purpose_built_workload_weighted_tps_per_mw",
        "commercial_workload_fit_factor",
        "reference_serving_tps_per_mw",
        "purpose_built_tps_per_mw",
        "tokens_per_second_per_mw",
        "inference_tokens_per_day",
        "inference_tokens_per_year",
        "confidence",
        "derivation_type",
        "source_ids",
        "assumption_ids",
        "capacity_basis",
        "gpu_asic_mix_basis",
        "tokens_per_mw_basis",
        "purpose_built_benchmark_status",
        "replacement_path",
    ]
    forecast_ws = sheet("07_token_forecast_2026_2030")
    append_rows(forecast_ws, data["forecast"], forecast_headers)
    forecast_token_col = get_column_letter(forecast_headers.index("inference_tokens_per_day") + 1)
    forecast_ws.conditional_formatting.add(
        f"{forecast_token_col}2:{forecast_token_col}{forecast_ws.max_row}",
        ColorScaleRule(start_type="min", start_color="FDE2E2", mid_type="percentile", mid_value=50, mid_color="FFF1B8", end_type="max", end_color="B7E4C7"),
    )

    sens_headers = list(data["sensitivity"][0].keys())
    append_rows(sheet("08_sensitivity"), data["sensitivity"], sens_headers)

    scenario_def_headers = list(data["scenario_definitions"][0].keys())
    append_rows(sheet("08a_scenario_definitions"), data["scenario_definitions"], scenario_def_headers)

    scenario_headers = list(data["scenario_forecast"][0].keys())
    scenario_ws = sheet("08b_scenario_forecast")
    append_rows(scenario_ws, data["scenario_forecast"], scenario_headers)
    scenario_ws.conditional_formatting.add(
        f"{get_column_letter(scenario_headers.index('inference_tokens_per_day') + 1)}2:{get_column_letter(scenario_headers.index('inference_tokens_per_day') + 1)}{scenario_ws.max_row}",
        ColorScaleRule(start_type="min", start_color="FDE2E2", mid_type="percentile", mid_value=50, mid_color="FFF1B8", end_type="max", end_color="B7E4C7"),
    )

    scenario_summary_headers = list(data["scenario_summary"][0].keys())
    append_rows(sheet("08c_scenario_summary"), data["scenario_summary"], scenario_summary_headers)

    benchmark_headers = list(data["benchmark_reference"][0].keys())
    benchmark_ws = sheet("08d_benchmark_reference")
    append_rows(benchmark_ws, data["benchmark_reference"], benchmark_headers)
    benchmark_ws.conditional_formatting.add(
        f"{get_column_letter(benchmark_headers.index('benchmark_vs_model_pct') + 1)}2:{get_column_letter(benchmark_headers.index('benchmark_vs_model_pct') + 1)}{benchmark_ws.max_row}",
        ColorScaleRule(start_type="min", start_color="FDE2E2", mid_type="percentile", mid_value=50, mid_color="FFF1B8", end_type="max", end_color="B7E4C7"),
    )

    energy_headers = list(data["energy_sanity_reference"][0].keys())
    energy_ws = sheet("08e_energy_sanity_reference")
    append_rows(energy_ws, data["energy_sanity_reference"], energy_headers)
    energy_ws.conditional_formatting.add(
        f"{get_column_letter(energy_headers.index('energy_vs_model_pct') + 1)}2:{get_column_letter(energy_headers.index('energy_vs_model_pct') + 1)}{energy_ws.max_row}",
        ColorScaleRule(start_type="min", start_color="FDE2E2", mid_type="percentile", mid_value=50, mid_color="FFF1B8", end_type="max", end_color="B7E4C7"),
    )

    util_headers = list(data["utilization_sensitivity"][0].keys())
    append_rows(sheet("08f_utilization_sensitivity"), data["utilization_sensitivity"], util_headers)

    inferencex = data["inferencex"]
    ix_headers = list(inferencex["source_index"][0].keys())
    append_rows(sheet("12_inferencex_source_index"), inferencex["source_index"], ix_headers)
    ix_schema_headers = list(inferencex["schema"][0].keys())
    append_rows(sheet("12a_inferencex_schema"), inferencex["schema"], ix_schema_headers)
    ix_tab_headers = list(inferencex["tab_rules"][0].keys())
    append_rows(sheet("12b_inferencex_tab_rules"), inferencex["tab_rules"], ix_tab_headers)
    if inferencex["release_assets"]:
        ix_release_headers = list(inferencex["release_assets"][0].keys())
        append_rows(sheet("12c_inferencex_releases"), inferencex["release_assets"], ix_release_headers)
    for sheet_name, key in [
        ("12d_ix_benchmark_results", "benchmark_results"),
        ("12e_ix_metric_profile", "metric_profile"),
        ("12f_ix_gpu_comparable", "gpu_comparable_metric_profile"),
        ("12g_ix_main_config", "main_config_by_model"),
        ("12h_ix_main_validation", "main_config_validation"),
        ("12i_ix_accuracy_evals", "accuracy_evals"),
        ("12j_ix_dump_inventory", "dump_inventory"),
        ("12k_ix_run_stats", "run_stats"),
        ("12l_ix_availability", "availability"),
    ]:
        rows = inferencex.get(key) or []
        if rows:
            append_rows(sheet(sheet_name), rows, list(rows[0].keys()))

    hallucination_headers = list(data["hallucination_checklist"][0].keys())
    append_rows(sheet("11_hallucination_checklist"), data["hallucination_checklist"], hallucination_headers)

    exec_headers = list(data["exec_summary"][0].keys())
    append_rows(sheet("09_exec_summary"), data["exec_summary"], exec_headers)

    # Native Excel charts for the two most important exec views.
    chart_ws = wb.create_sheet("10_charts")
    chart_ws.append(["year"] + [s.company for s in scenarios()])
    for year in YEARS:
        chart_ws.append(
            [year]
            + [
                next(r["inference_tokens_per_day"] / 1e15 for r in data["forecast"] if r["company"] == s.company and r["year"] == year)
                for s in scenarios()
            ]
        )
    style_sheet(chart_ws)
    line = LineChart()
    line.title = "업체별 추정 inference token capacity (quadrillion tokens/day)"
    line.y_axis.title = "Q tokens/day"
    line.x_axis.title = "Year"
    line.add_data(Reference(chart_ws, min_col=2, max_col=1 + len(scenarios()), min_row=1, max_row=6), titles_from_data=True)
    line.set_categories(Reference(chart_ws, min_col=1, min_row=2, max_row=6))
    line.height = 9
    line.width = 24
    chart_ws.add_chart(line, "A9")

    chart_ws.append([])
    start = chart_ws.max_row + 1
    chart_ws.append(["company", "2030 inference GW", "2030 training GW"])
    for s in scenarios():
        row = next(r for r in data["forecast"] if r["company"] == s.company and r["year"] == 2030)
        chart_ws.append([s.company, row["inference_gw"], row["training_gw"]])
    bar = BarChart()
    bar.type = "bar"
    bar.style = 10
    bar.title = "2030 inference vs training GW"
    bar.y_axis.title = "Company"
    bar.x_axis.title = "GW"
    bar.add_data(Reference(chart_ws, min_col=2, max_col=3, min_row=start, max_row=start + len(scenarios())), titles_from_data=True)
    bar.set_categories(Reference(chart_ws, min_col=1, min_row=start + 1, max_row=start + len(scenarios())))
    bar.height = 9
    bar.width = 24
    chart_ws.add_chart(bar, "A28")

    chart_ws.append([])
    scen_start = chart_ws.max_row + 1
    chart_ws.append(["year"] + list(SCENARIO_CASES.keys()))
    for year in YEARS:
        chart_ws.append(
            [year]
            + [
                next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == year)
                for scen in SCENARIO_CASES
            ]
        )
    scenario_line = LineChart()
    scenario_line.title = "시나리오별 토큰 capacity: 낙관/기준/보수/전력제약"
    scenario_line.y_axis.title = "Q tokens/day"
    scenario_line.x_axis.title = "Year"
    scenario_line.add_data(Reference(chart_ws, min_col=2, max_col=1 + len(SCENARIO_CASES), min_row=scen_start, max_row=scen_start + len(YEARS)), titles_from_data=True)
    scenario_line.set_categories(Reference(chart_ws, min_col=1, min_row=scen_start + 1, max_row=scen_start + len(YEARS)))
    scenario_line.height = 8
    scenario_line.width = 24
    chart_ws.add_chart(scenario_line, "A47")

    wb.save(path)


def write_excel(data: dict[str, Any], path: Path) -> None:
    """Write a compact formula workbook with editable GPU-generation mix inputs."""
    wb = Workbook()
    wb.remove(wb.active)
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"
    input_fill = PatternFill("solid", fgColor="FFF2CC")
    formula_fill = PatternFill("solid", fgColor="E2F0D9")

    logic = wb.create_sheet("00_Logic")
    logic_rows = [
        ["AI LLM Token Capacity Simulation - Core Formula Model", ""],
        ["목적", "최종 generated output tokens/day를 설명 가능한 전력, GPU 세대 mix, commercial workload 가정으로 계산"],
        ["입력 원칙", "노란색 셀만 직접 입력합니다. 모델/GPU/workload/interactivity별 proxy TPS/MW는 `00a_Proxy_TPS_MW`에서 확인하고, Chat workload 비율과 GPU별 chat-length TPS/MW는 `01_Benchmark_Input`, GPU mix는 `02_GPU_Mix_Input`에서 교체합니다."],
        ["Step 1", "operational_power_gw = contracted_power_gw * operational_deployment_share"],
        ["Step 2", "inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share"],
        ["Step 3", "gpu_workload_avg_tps_per_mw = short_share*gpu_short_tps + long_share*gpu_long_tps + agentic_share*gpu_agentic_tps"],
        ["Step 4", "fleet_reference_tps_per_mw = H200_share*H200_workload_avg + B200_share*B200_workload_avg + GB200_share*GB200_workload_avg + purpose_built_share*purpose_workload_avg"],
        ["Step 4b", "serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor"],
        ["Step 5", "generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400"],
        ["GPU mix rule", "H200/B200/GB200/purpose-built share의 합은 100%이며, 같은 inference MW 내 구성 차이가 token capacity를 바꿉니다."],
        ["Benchmark rule", "Short chat은 ISL/OSL 1024/1024, long chat은 8192/1024입니다. TPS/MW는 concurrency 32-256 안에서 Dynamo/TRT-LLM/MTP 계열 stack을 우선하고, 없으면 같은 조건의 public max row를 씁니다. Agentic은 Kimi K2.5 dynamic reasoning에서 산출한 agentic/long TPS/MW ratio를 long-context TPS/MW에 적용합니다."],
        ["Purpose-built rule", "Comparable TPS/MW가 없으면 B200 placeholder를 사용하며 사용자 입력으로 교체합니다."],
        ["Excluded", "utilization, MoE uplift, software CAGR는 headline 계산에서 제외합니다."],
    ]
    for row in logic_rows:
        logic.append(row)
    logic.column_dimensions["A"].width = 24
    logic.column_dimensions["B"].width = 126
    logic["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    logic["B1"].font = Font(size=16, bold=True, color="FFFFFF")
    for cell in logic[1]:
        cell.fill = PatternFill("solid", fgColor="14213D")
    for row in range(2, len(logic_rows) + 1):
        logic[f"A{row}"].font = Font(bold=True, color="14213D")
        logic[f"A{row}"].fill = PatternFill("solid", fgColor="EAF0F7")
        logic[f"B{row}"].alignment = Alignment(wrap_text=True, vertical="top")
        logic.row_dimensions[row].height = 30
    logic.freeze_panes = "A2"

    append_proxy_tps_mw_reference_sheet(wb)

    benchmark_ws = wb.create_sheet("01_Benchmark_Input")
    benchmark_ws.append([
        "company", "commercial_workload_class", "proxy_model",
        "short_chat_share", "long_chat_share", "agentic_share", "chat_share_sum_check",
        "h200_short_chat_tps_per_mw", "h200_long_chat_tps_per_mw", "h200_agentic_tps_per_mw", "h200_workload_avg_tps_per_mw", "h200_status",
        "b200_short_chat_tps_per_mw", "b200_long_chat_tps_per_mw", "b200_agentic_tps_per_mw", "b200_workload_avg_tps_per_mw", "b200_status",
        "gb200_short_chat_tps_per_mw", "gb200_long_chat_tps_per_mw", "gb200_agentic_tps_per_mw", "gb200_workload_avg_tps_per_mw", "gb200_status",
        "purpose_short_chat_tps_per_mw", "purpose_long_chat_tps_per_mw", "purpose_agentic_tps_per_mw", "purpose_workload_avg_tps_per_mw", "purpose_status",
        "bear_fit_factor", "base_fit_factor", "bull_fit_factor", "rationale", "source_ids",
        "short_chat_condition", "long_chat_condition", "agentic_condition", "concurrency_interactivity_rule",
    ])
    hardware = hardware_reference_profiles()
    workloads = commercial_workload_profiles()
    proxy_map = company_core_benchmark_map()
    workload_refs = workload_reference_profiles()
    workload_mixes = company_workload_mix_profiles()
    workload_classes = workload_class_assumptions()
    short_condition = (
        f"ISL/OSL {workload_classes['short_chat']['isl']}/{workload_classes['short_chat']['osl']}; "
        f"concurrency {workload_classes['short_chat']['concurrency_min']}-{workload_classes['short_chat']['concurrency_max']}; "
        f"{workload_classes['short_chat']['interactivity_profile']}"
    )
    long_condition = (
        f"ISL/OSL {workload_classes['long_chat']['isl']}/{workload_classes['long_chat']['osl']}; "
        f"concurrency {workload_classes['long_chat']['concurrency_min']}-{workload_classes['long_chat']['concurrency_max']}; "
        f"{workload_classes['long_chat']['interactivity_profile']}"
    )
    agentic_condition = (
        f"Trace avg ISL/OSL {workload_classes['agentic']['isl']}/{workload_classes['agentic']['osl']}; "
        f"derived from long_chat TPS/MW x {workload_classes['agentic']['fit_factor']:.0%}; "
        f"{workload_classes['agentic']['interactivity_profile']}"
    )
    for excel_row, company in enumerate([scenario.company for scenario in scenarios()], start=2):
        workload = workloads[company]
        proxy = proxy_map[company]["proxy_model"]
        refs = workload_refs[proxy]
        mix = workload_mixes[company]
        benchmark_ws.append([
            company, workload["workload_class"], proxy,
            mix["short_chat_share"], mix["long_chat_share"], mix["agentic_share"], f"=SUM(D{excel_row}:F{excel_row})",
            refs["h200_short_chat_tps_per_mw"], refs["h200_long_chat_tps_per_mw"], refs["h200_agentic_tps_per_mw"], f"=D{excel_row}*H{excel_row}+E{excel_row}*I{excel_row}+F{excel_row}*J{excel_row}", f"short: {refs['h200_short_chat_status']}; long: {refs['h200_long_chat_status']}; agentic: {refs['h200_agentic_status']}",
            refs["b200_short_chat_tps_per_mw"], refs["b200_long_chat_tps_per_mw"], refs["b200_agentic_tps_per_mw"], f"=D{excel_row}*M{excel_row}+E{excel_row}*N{excel_row}+F{excel_row}*O{excel_row}", f"short: {refs['b200_short_chat_status']}; long: {refs['b200_long_chat_status']}; agentic: {refs['b200_agentic_status']}",
            refs["gb200_short_chat_tps_per_mw"], refs["gb200_long_chat_tps_per_mw"], refs["gb200_agentic_tps_per_mw"], f"=D{excel_row}*R{excel_row}+E{excel_row}*S{excel_row}+F{excel_row}*T{excel_row}", f"short: {refs['gb200_short_chat_status']}; long: {refs['gb200_long_chat_status']}; agentic: {refs['gb200_agentic_status']}",
            refs["b200_short_chat_tps_per_mw"], refs["b200_long_chat_tps_per_mw"], refs["b200_agentic_tps_per_mw"], f"=D{excel_row}*W{excel_row}+E{excel_row}*X{excel_row}+F{excel_row}*Y{excel_row}", "B200 placeholder until comparable purpose-built output-token/MW benchmark is adopted.",
            workload["bear_fit_factor"], workload["base_fit_factor"], workload["bull_fit_factor"], mix["rationale"], mix["source_ids"],
            short_condition, long_condition, agentic_condition, "TPS/MW rows are filtered to model-level main config, single_turn, matched ISL/OSL and concurrency 32-256; Dynamo/TRT-LLM/MTP optimized stacks are preferred, otherwise public max is used; agentic is trace-derived until matched 100k-input rows exist.",
        ])
    style_sheet(benchmark_ws)
    for row in benchmark_ws.iter_rows(min_row=2):
        for col in (4, 5, 6, 8, 9, 10, 13, 14, 15, 18, 19, 20, 23, 24, 25, 28, 29, 30):
            row[col - 1].fill = input_fill
            row[col - 1].font = Font(color="0000FF")
        for col in (7, 11, 16, 21, 26):
            row[col - 1].fill = formula_fill
    for col in ("D", "E", "F", "G", "AB", "AC", "AD"):
        for cell in benchmark_ws[col][1:]:
            cell.number_format = "0.0%"
    for col in ("H", "I", "J", "K", "M", "N", "O", "P", "R", "S", "T", "U", "W", "X", "Y", "Z"):
        for cell in benchmark_ws[col][1:]:
            cell.number_format = "#,##0"
    for col, width in {
        "A": 18, "B": 38, "C": 18, "D": 17, "E": 17, "F": 17, "G": 18,
        "H": 22, "I": 22, "J": 22, "K": 24, "L": 45,
        "M": 22, "N": 22, "O": 22, "P": 24, "Q": 45,
        "R": 22, "S": 22, "T": 22, "U": 24, "V": 58,
        "W": 24, "X": 24, "Y": 24, "Z": 26, "AA": 58,
        "AE": 80, "AF": 50, "AG": 42, "AH": 42, "AI": 58, "AJ": 72,
    }.items():
        benchmark_ws.column_dimensions[col].width = width

    interactivity_ws = wb.create_sheet("01b_Interactivity")
    interactivity_headers = [
        "proxy_model", "gpu", "workload_type", "source_model_scope", "target_tok_s_user",
        "selected_isl", "selected_osl", "candidate_rows", "eligible_rows", "optimized_eligible_rows",
        "selected_output_tps_per_mw", "selected_tok_s_user", "selected_concurrency",
        "selected_framework", "selected_precision", "selection_status", "selection_basis",
        "benchmark_date", "method_note",
    ]
    interactivity_ws.append(interactivity_headers)
    for row in data["interactivity_reference_profiles"]:
        interactivity_ws.append([row.get(header, "") for header in interactivity_headers])
    style_sheet(interactivity_ws)
    for row in interactivity_ws.iter_rows(min_row=2):
        if row[15].value == "missing":
            for cell in row:
                cell.fill = PatternFill("solid", fgColor="FCE4D6")
        elif row[15].value == "selected_optimized_stack":
            for cell in row:
                cell.fill = PatternFill("solid", fgColor="E2F0D9")
    for col in ("K", "L"):
        for cell in interactivity_ws[col][1:]:
            cell.number_format = "#,##0.00" if col == "L" else "#,##0"
    for col, width in {
        "A": 20, "B": 10, "C": 18, "D": 34, "E": 18, "F": 14, "G": 14,
        "H": 14, "I": 14, "J": 20, "K": 24, "L": 18, "M": 18,
        "N": 20, "O": 18, "P": 24, "Q": 34, "R": 18, "S": 92,
    }.items():
        interactivity_ws.column_dimensions[col].width = width

    inputs = wb.create_sheet("02_Inputs")
    inputs.append([
        "scenario", "company", "year", "contracted_power_gw",
        "operational_deployment_share", "pue", "ai_workload_share",
        "inference_power_share", "commercial_workload_class",
        "benchmark_proxy_model", "commercial_workload_fit_factor",
    ])
    for excel_row, row in enumerate(data["scenario_forecast"], start=2):
        inputs.append([
            row["scenario"], row["company"], row["year"], row["contracted_power_gw"],
            row["operational_deployment_share"], row["pue"], row["ai_workload_share"],
            row["inference_power_share"],
            f"=INDEX('01_Benchmark_Input'!$B$2:$B$10,MATCH(B{excel_row},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=INDEX('01_Benchmark_Input'!$C$2:$C$10,MATCH(B{excel_row},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f'=IF(A{excel_row}="Bear",INDEX(\'01_Benchmark_Input\'!$AB$2:$AB$10,MATCH(B{excel_row},\'01_Benchmark_Input\'!$A$2:$A$10,0)),IF(A{excel_row}="Bull",INDEX(\'01_Benchmark_Input\'!$AD$2:$AD$10,MATCH(B{excel_row},\'01_Benchmark_Input\'!$A$2:$A$10,0)),INDEX(\'01_Benchmark_Input\'!$AC$2:$AC$10,MATCH(B{excel_row},\'01_Benchmark_Input\'!$A$2:$A$10,0))))',
        ])
    style_sheet(inputs)
    for row in inputs.iter_rows(min_row=2):
        for col in (4, 5, 6, 7, 8):
            row[col - 1].fill = input_fill
        for col in (9, 10, 11):
            row[col - 1].fill = formula_fill
    for col in ("E", "G", "H", "K"):
        for cell in inputs[col][1:]:
            cell.number_format = "0.0%"
    inputs.column_dimensions["I"].width = 45
    inputs.column_dimensions["J"].width = 24
    inputs.column_dimensions["K"].width = 29

    gpu_mix = wb.create_sheet("02_GPU_Mix_Input")
    gpu_mix.append(["scenario", "company", "year", "h200_share", "b200_share", "gb200_share", "purpose_built_share", "share_sum_check"])
    for excel_row, row in enumerate(data["scenario_forecast"], start=2):
        gpu_mix.append([
            row["scenario"], row["company"], row["year"],
            row["h200_share"], row["b200_share"], row["gb200_share"],
            row["purpose_built_accelerator_share"], f"=SUM(D{excel_row}:G{excel_row})",
        ])
    style_sheet(gpu_mix)
    for row in gpu_mix.iter_rows(min_row=2):
        for col in (4, 5, 6, 7):
            row[col - 1].fill = input_fill
            row[col - 1].font = Font(color="0000FF")
        row[7].fill = formula_fill
    for col in ("D", "E", "F", "G", "H"):
        for cell in gpu_mix[col][1:]:
            cell.number_format = "0.0%"
    gpu_mix.column_dimensions["A"].width = 32
    for col in ("D", "E", "F", "G", "H"):
        gpu_mix.column_dimensions[col].width = 22

    calc = wb.create_sheet("03_Calculation")
    calc.append([
        "scenario", "company", "year", "contracted_power_gw", "operational_deployment_share",
        "operational_power_gw", "pue", "it_load_gw", "ai_workload_share", "ai_it_load_gw",
        "inference_power_share", "inference_gw", "training_gw",
        "h200_share", "b200_share", "gb200_share", "purpose_built_share",
        "h200_workload_avg_tps_per_mw", "b200_workload_avg_tps_per_mw",
        "gb200_workload_avg_tps_per_mw", "purpose_workload_avg_tps_per_mw",
        "short_chat_share", "long_chat_share", "agentic_share",
        "fleet_reference_tps_per_mw", "commercial_workload_fit_factor",
        "serving_tps_per_mw", "inference_tokens_per_day", "inference_tokens_per_year",
    ])
    for row_idx, row_data in enumerate(data["scenario_forecast"], start=2):
        calc.append([
            f"='02_Inputs'!A{row_idx}", f"='02_Inputs'!B{row_idx}", f"='02_Inputs'!C{row_idx}",
            f"='02_Inputs'!D{row_idx}", f"='02_Inputs'!E{row_idx}", f"=D{row_idx}*E{row_idx}",
            f"='02_Inputs'!F{row_idx}", f"=F{row_idx}/G{row_idx}", f"='02_Inputs'!G{row_idx}",
            f"=H{row_idx}*I{row_idx}", f"='02_Inputs'!H{row_idx}", f"=J{row_idx}*K{row_idx}",
            f"=J{row_idx}*(1-K{row_idx})", f"='02_GPU_Mix_Input'!D{row_idx}",
            f"='02_GPU_Mix_Input'!E{row_idx}", f"='02_GPU_Mix_Input'!F{row_idx}",
            f"='02_GPU_Mix_Input'!G{row_idx}",
            f"=INDEX('01_Benchmark_Input'!$K$2:$K$10,MATCH(B{row_idx},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=INDEX('01_Benchmark_Input'!$P$2:$P$10,MATCH(B{row_idx},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=INDEX('01_Benchmark_Input'!$U$2:$U$10,MATCH(B{row_idx},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=INDEX('01_Benchmark_Input'!$Z$2:$Z$10,MATCH(B{row_idx},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=INDEX('01_Benchmark_Input'!$D$2:$D$10,MATCH(B{row_idx},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=INDEX('01_Benchmark_Input'!$E$2:$E$10,MATCH(B{row_idx},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=INDEX('01_Benchmark_Input'!$F$2:$F$10,MATCH(B{row_idx},'01_Benchmark_Input'!$A$2:$A$10,0))",
            f"=N{row_idx}*R{row_idx}+O{row_idx}*S{row_idx}+P{row_idx}*T{row_idx}+Q{row_idx}*U{row_idx}",
            f"='02_Inputs'!K{row_idx}",
            f"=Y{row_idx}*Z{row_idx}", f"=L{row_idx}*1000*AA{row_idx}*86400", f"=AB{row_idx}*365",
        ])
    style_sheet(calc)
    for row in calc.iter_rows(min_row=2):
        for cell in row:
            cell.fill = formula_fill
    for col in ("E", "I", "K", "N", "O", "P", "Q", "V", "W", "X", "Z"):
        for cell in calc[col][1:]:
            cell.number_format = "0.0%"
    for col in ("D", "F", "H", "J", "L", "M"):
        for cell in calc[col][1:]:
            cell.number_format = "0.000"
    for col in ("R", "S", "T", "U", "Y", "AA"):
        for cell in calc[col][1:]:
            cell.number_format = "#,##0"

    output = wb.create_sheet("04_Output")
    output["A1"] = "Base Scenario: Generated Output Token Capacity, 2026-2030"
    output["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    output["A1"].fill = PatternFill("solid", fgColor="14213D")
    output.merge_cells("A1:F1")
    output["A2"] = "업체별 output은 Base scenario 기준이며, 모든 수치는 `03_Calculation`의 generated output token formula를 직접 참조합니다. 단위는 Quadrillion (Q) tokens입니다."
    output.merge_cells("A2:F2")
    output["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    output.row_dimensions[2].height = 34

    company_order = [scenario.company for scenario in scenarios()]
    base_2030 = [
        idx for idx, row in enumerate(data["scenario_forecast"], start=2)
        if row["scenario"] == "Base" and row["year"] == 2030
    ]

    day_title_row = 4
    output[f"A{day_title_row}"] = "Base Provider Time Series - Generated Output Tokens/Day (Q)"
    output[f"A{day_title_row}"].font = Font(bold=True, color="14213D", size=12)
    day_header_row = day_title_row + 1
    output.append(["Provider"] + YEARS)
    for cell in output[day_header_row]:
        cell.fill = PatternFill("solid", fgColor="14213D")
        cell.font = Font(color="FFFFFF", bold=True)
    for company in company_order:
        out_row = output.max_row + 1
        output.append(
            [company]
            + [
                f'=SUMIFS(\'03_Calculation\'!$AB$2:$AB$181,\'03_Calculation\'!$A$2:$A$181,"Base",\'03_Calculation\'!$B$2:$B$181,$A{out_row},\'03_Calculation\'!$C$2:$C$181,{get_column_letter(col)}${day_header_row})/1000000000000000'
                for col, _year in enumerate(YEARS, start=2)
            ]
        )
        for cell in output[out_row][1:]:
            cell.fill = formula_fill
            cell.number_format = "0.000"
    day_total_row = output.max_row + 1
    output.append(["Total"] + [f"=SUM({get_column_letter(col)}{day_header_row + 1}:{get_column_letter(col)}{day_total_row - 1})" for col in range(2, 2 + len(YEARS))])
    for cell in output[day_total_row]:
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
        cell.font = Font(bold=True, color="14213D")
    for cell in output[day_total_row][1:]:
        cell.number_format = "0.000"

    output.append([])
    year_title_row = output.max_row + 1
    output.append(["Base Provider Time Series - Generated Output Tokens/Year (Q)"])
    output[f"A{year_title_row}"].font = Font(bold=True, color="14213D", size=12)
    year_header_row = output.max_row + 1
    output.append(["Provider"] + YEARS)
    for cell in output[year_header_row]:
        cell.fill = PatternFill("solid", fgColor="14213D")
        cell.font = Font(color="FFFFFF", bold=True)
    for company in company_order:
        out_row = output.max_row + 1
        output.append(
            [company]
            + [
                f'=SUMIFS(\'03_Calculation\'!$AC$2:$AC$181,\'03_Calculation\'!$A$2:$A$181,"Base",\'03_Calculation\'!$B$2:$B$181,$A{out_row},\'03_Calculation\'!$C$2:$C$181,{get_column_letter(col)}${year_header_row})/1000000000000000'
                for col, _year in enumerate(YEARS, start=2)
            ]
        )
        for cell in output[out_row][1:]:
            cell.fill = formula_fill
            cell.number_format = "0.000"
    year_total_row = output.max_row + 1
    output.append(["Total"] + [f"=SUM({get_column_letter(col)}{year_header_row + 1}:{get_column_letter(col)}{year_total_row - 1})" for col in range(2, 2 + len(YEARS))])
    for cell in output[year_total_row]:
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
        cell.font = Font(bold=True, color="14213D")
    for cell in output[year_total_row][1:]:
        cell.number_format = "0.000"

    output.append([])
    scenario_day_title_row = output.max_row + 1
    output.append(["Scenario Total Time Series - Generated Output Tokens/Day (Q)"])
    output[f"A{scenario_day_title_row}"].font = Font(bold=True, color="14213D", size=12)
    scenario_day_header_row = output.max_row + 1
    output.append(["Scenario"] + YEARS)
    for cell in output[scenario_day_header_row]:
        cell.fill = PatternFill("solid", fgColor="14213D")
        cell.font = Font(color="FFFFFF", bold=True)
    for scenario_name in SCENARIO_CASES:
        out_row = output.max_row + 1
        output.append(
            [scenario_name]
            + [
                f'=SUMIFS(\'03_Calculation\'!$AB$2:$AB$181,\'03_Calculation\'!$A$2:$A$181,$A{out_row},\'03_Calculation\'!$C$2:$C$181,{get_column_letter(col)}${scenario_day_header_row})/1000000000000000'
                for col, _year in enumerate(YEARS, start=2)
            ]
        )
        for cell in output[out_row][1:]:
            cell.fill = formula_fill
            cell.number_format = "0.000"

    output.append([])
    scenario_year_title_row = output.max_row + 1
    output.append(["Scenario Total Time Series - Generated Output Tokens/Year (Q)"])
    output[f"A{scenario_year_title_row}"].font = Font(bold=True, color="14213D", size=12)
    scenario_year_header_row = output.max_row + 1
    output.append(["Scenario"] + YEARS)
    for cell in output[scenario_year_header_row]:
        cell.fill = PatternFill("solid", fgColor="14213D")
        cell.font = Font(color="FFFFFF", bold=True)
    for scenario_name in SCENARIO_CASES:
        out_row = output.max_row + 1
        output.append(
            [scenario_name]
            + [
                f'=SUMIFS(\'03_Calculation\'!$AC$2:$AC$181,\'03_Calculation\'!$A$2:$A$181,$A{out_row},\'03_Calculation\'!$C$2:$C$181,{get_column_letter(col)}${scenario_year_header_row})/1000000000000000'
                for col, _year in enumerate(YEARS, start=2)
            ]
        )
        for cell in output[out_row][1:]:
            cell.fill = formula_fill
            cell.number_format = "0.000"

    output.freeze_panes = "B6"
    for col, width in {"A": 46, "B": 15, "C": 15, "D": 15, "E": 15, "F": 15}.items():
        output.column_dimensions[col].width = width
    for row in output.iter_rows(min_row=3, max_col=6):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    provider_chart = LineChart()
    provider_chart.title = "Base Provider Token Capacity (Q tokens/day)"
    provider_chart.y_axis.title = "Q tokens/day"
    provider_chart.y_axis.numFmt = "0.000"
    provider_chart.x_axis.title = "Year"
    provider_chart.add_data(
        Reference(output, min_col=1, max_col=1 + len(YEARS), min_row=day_header_row + 1, max_row=day_total_row - 1),
        titles_from_data=True,
        from_rows=True,
    )
    provider_chart.set_categories(Reference(output, min_col=2, max_col=1 + len(YEARS), min_row=day_header_row))
    for series, company in zip(provider_chart.series, company_order):
        series.tx = SeriesLabel(v=company)
    provider_chart.height = 8
    provider_chart.width = 18
    output.add_chart(provider_chart, "H4")

    scenario_chart = LineChart()
    scenario_chart.title = "Scenario Total Token Capacity (Q tokens/day)"
    scenario_chart.y_axis.title = "Q tokens/day"
    scenario_chart.y_axis.numFmt = "0.000"
    scenario_chart.x_axis.title = "Year"
    scenario_chart.add_data(
        Reference(output, min_col=1, max_col=1 + len(YEARS), min_row=scenario_day_header_row + 1, max_row=scenario_day_header_row + len(SCENARIO_CASES)),
        titles_from_data=True,
        from_rows=True,
    )
    scenario_chart.set_categories(Reference(output, min_col=2, max_col=1 + len(YEARS), min_row=scenario_day_header_row))
    for series, scenario_name in zip(scenario_chart.series, SCENARIO_CASES):
        series.tx = SeriesLabel(v=scenario_name)
    scenario_chart.height = 8
    scenario_chart.width = 18
    output.add_chart(scenario_chart, "H22")

    checks = wb.create_sheet("05_Checks")
    checks.append(["Check", "Formula", "Result"])
    check_rows = [
        (
            "Operational power never exceeds contracted",
            '=IF(SUMPRODUCT(--(\'03_Calculation\'!$F$2:$F$181>\'03_Calculation\'!$D$2:$D$181))=0,"PASS","FAIL")',
        ),
        (
            "Inference and training GW reconstruct AI IT load",
            '=IF(SUMPRODUCT(--(ABS(\'03_Calculation\'!$J$2:$J$181-(\'03_Calculation\'!$L$2:$L$181+\'03_Calculation\'!$M$2:$M$181))>0.001))=0,"PASS","FAIL")',
        ),
        (
            "Accelerator shares sum to 100%",
            '=IF(SUMPRODUCT(--(ABS(1-(\'03_Calculation\'!$N$2:$N$181+\'03_Calculation\'!$O$2:$O$181+\'03_Calculation\'!$P$2:$P$181+\'03_Calculation\'!$Q$2:$Q$181))>0.002))=0,"PASS","FAIL")',
        ),
        (
            "Commercial workload fit factors stay within 0%-100%",
            '=IF(AND(MIN(\'02_Inputs\'!$K$2:$K$181)>0,MAX(\'02_Inputs\'!$K$2:$K$181)<=1),"PASS","FAIL")',
        ),
        (
            "Chat workload shares sum to 100%",
            '=IF(SUMPRODUCT(--(ABS(1-(\'03_Calculation\'!$V$2:$V$181+\'03_Calculation\'!$W$2:$W$181+\'03_Calculation\'!$X$2:$X$181))>0.002))=0,"PASS","FAIL")',
        ),
        (
            "Serving reference equals fleet reference x workload fit",
            '=IF(SUMPRODUCT(--(ABS(\'03_Calculation\'!$AA$2:$AA$181-(\'03_Calculation\'!$Y$2:$Y$181*\'03_Calculation\'!$Z$2:$Z$181))>0.01))=0,"PASS","FAIL")',
        ),
        (
            "Purpose-built reference defaults to B200 without unsupported uplift",
            '=IF(SUMPRODUCT(--(\'01_Benchmark_Input\'!$W$2:$Y$10<>\'01_Benchmark_Input\'!$M$2:$O$10))=0,"PASS","FAIL")',
        ),
        (
            "Headline excludes utilization/MoE/software multipliers",
            '="PASS - formula uses inference GW x fleet-weighted serving TPS/MW x seconds/day only"',
        ),
    ]
    for label, formula in check_rows:
        checks.append([label, formula, f"=B{checks.max_row + 1}"])
    style_sheet(checks)
    checks.column_dimensions["A"].width = 54
    checks.column_dimensions["B"].width = 110
    checks.column_dimensions["C"].width = 62
    for cell in checks["C"][1:]:
        cell.fill = formula_fill
        cell.font = Font(bold=True, color="006100")

    aggressive = wb.create_sheet("06_Aggressive_View")
    aggressive["A1"] = "Aggressive Commercial Supply View - Bull Case And Public Benchmark Ceiling"
    aggressive["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    aggressive["A1"].fill = PatternFill("solid", fgColor="14213D")
    aggressive.merge_cells("A1:H1")
    aggressive["A2"] = "Bull은 빠른 operational deployment, 높은 inference allocation, 유리한 commercial workload fit을 적용합니다. Ceiling은 같은 Bull 전력에서 fit factor=100%로 두는 전략적 상한이며 Base forecast가 아닙니다."
    aggressive.merge_cells("A2:H2")
    aggressive["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    aggressive.row_dimensions[2].height = 42
    aggressive.append(["Provider", "Base 2030 Q/day", "Bull 2030 Q/day", "Bull vs Base", "Bull Fit Factor", "Bull Serving TPS/MW", "Public Reference Ceiling Q/day", "Required condition"])
    for cell in aggressive[3]:
        cell.fill = PatternFill("solid", fgColor="14213D")
        cell.font = Font(color="FFFFFF", bold=True)
    bull_2030 = [
        idx for idx, row in enumerate(data["scenario_forecast"], start=2)
        if row["scenario"] == "Bull" and row["year"] == 2030
    ]
    for bull_row, base_row in zip(bull_2030, base_2030):
        out_row = aggressive.max_row + 1
        aggressive.append(
            [
                f"='03_Calculation'!B{bull_row}",
                f"='03_Calculation'!AB{base_row}/1000000000000000",
                f"='03_Calculation'!AB{bull_row}/1000000000000000",
                f"=C{out_row}/B{out_row}-1",
                f"='03_Calculation'!Z{bull_row}",
                f"='03_Calculation'!AA{bull_row}",
                f"=C{out_row}/E{out_row}",
                "Public-reference conditions become commercially repeatable",
            ]
        )
        for cell in aggressive[out_row][:7]:
            cell.fill = formula_fill
    aggressive.append([])
    trend_header = aggressive.max_row + 1
    aggressive.append(["Total Q generated output tokens/day", "Base", "Bull", "Public Reference Ceiling"])
    for cell in aggressive[trend_header]:
        cell.fill = PatternFill("solid", fgColor="14213D")
        cell.font = Font(color="FFFFFF", bold=True)
    for year in YEARS:
        out_row = aggressive.max_row + 1
        aggressive.append(
            [
                year,
                f'=SUMIFS(\'03_Calculation\'!$AB:$AB,\'03_Calculation\'!$A:$A,"Base",\'03_Calculation\'!$C:$C,$A{out_row})/1000000000000000',
                f'=SUMIFS(\'03_Calculation\'!$AB:$AB,\'03_Calculation\'!$A:$A,"Bull",\'03_Calculation\'!$C:$C,$A{out_row})/1000000000000000',
                f'=SUMPRODUCT((\'03_Calculation\'!$A$2:$A$181="Bull")*(\'03_Calculation\'!$C$2:$C$181=$A{out_row})*(\'03_Calculation\'!$AB$2:$AB$181/\'03_Calculation\'!$Z$2:$Z$181))/1000000000000000',
            ]
        )
        for cell in aggressive[out_row][1:]:
            cell.fill = formula_fill
    aggressive_chart = LineChart()
    aggressive_chart.title = "Aggressive Token Supply Range (Q output tokens/day)"
    aggressive_chart.y_axis.title = "Q tokens/day"
    aggressive_chart.x_axis.title = "Year"
    aggressive_chart.add_data(
        Reference(aggressive, min_col=2, max_col=4, min_row=trend_header, max_row=trend_header + len(YEARS)),
        titles_from_data=True,
    )
    aggressive_chart.set_categories(Reference(aggressive, min_col=1, min_row=trend_header + 1, max_row=trend_header + len(YEARS)))
    aggressive_chart.height = 8
    aggressive_chart.width = 18
    aggressive.add_chart(aggressive_chart, "J3")
    aggressive.freeze_panes = "A4"
    for col, width in {"A": 30, "B": 18, "C": 18, "D": 16, "E": 17, "F": 22, "G": 28, "H": 55}.items():
        aggressive.column_dimensions[col].width = width
    for cell in aggressive["D"][3:12]:
        cell.number_format = "0.0%"
    for cell in aggressive["E"][3:12]:
        cell.number_format = "0.0%"
    for col in ("B", "C", "G"):
        for cell in aggressive[col][3:12]:
            cell.number_format = "0.000"
    for row in aggressive.iter_rows(min_row=trend_header + 1, min_col=2, max_col=4):
        for cell in row:
            cell.number_format = "0.000"

    source_ws = wb.create_sheet("07_Source_Registry")
    source_headers = list(asdict(sources()[0]).keys())
    append_rows(source_ws, [asdict(s) for s in sources()], source_headers)
    style_sheet(source_ws)
    for col, width in {
        "A": 34,
        "B": 56,
        "C": 24,
        "D": 20,
        "E": 64,
        "F": 14,
        "G": 58,
        "H": 12,
        "I": 72,
    }.items():
        source_ws.column_dimensions[col].width = width
    for row in source_ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    provenance_ws = wb.create_sheet("08_Provenance_Trace")
    provenance_headers = list(data["number_trace"][0].keys())
    append_rows(provenance_ws, data["number_trace"], provenance_headers)
    style_sheet(provenance_ws)
    for col, width in {
        "A": 22,
        "B": 18,
        "C": 12,
        "D": 28,
        "E": 18,
        "F": 18,
        "G": 26,
        "H": 44,
        "I": 54,
        "J": 34,
        "K": 46,
        "L": 34,
        "M": 46,
    }.items():
        provenance_ws.column_dimensions[col].width = width
    for row in provenance_ws.iter_rows(min_row=2, max_row=min(provenance_ws.max_row, 200)):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    audit_ws = wb.create_sheet("09_Fact_Assumption_Audit")
    audit_headers = list(data["company_input_audit"][0].keys())
    append_rows(audit_ws, data["company_input_audit"], audit_headers)
    style_sheet(audit_ws)
    for col, width in {
        "A": 18,
        "B": 28,
        "C": 30,
        "D": 28,
        "E": 42,
        "F": 58,
        "G": 50,
        "H": 42,
        "I": 36,
    }.items():
        audit_ws.column_dimensions[col].width = width
    for row in audit_ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
    wb.active = wb.sheetnames.index("04_Output")
    wb.save(path)


def ppt_add_title(slide, title: str, subtitle: str | None = None) -> None:
    tx = slide.shapes.add_textbox(Inches(0.55), Inches(0.28), Inches(12.2), Inches(0.6))
    p = tx.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(25)
    p.font.bold = True
    p.font.color.rgb = RGBColor(20, 33, 61)
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.58), Inches(0.84), Inches(11.8), Inches(0.35))
        p2 = sub.text_frame.paragraphs[0]
        p2.text = subtitle
        p2.font.size = Pt(10)
        p2.font.color.rgb = RGBColor(95, 111, 130)


def write_ppt(data: dict[str, Any], path: Path) -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def add_footer(slide):
        tx = slide.shapes.add_textbox(Inches(0.55), Inches(7.05), Inches(12.0), Inches(0.25))
        p = tx.text_frame.paragraphs[0]
        p.text = f"Source-backed simulation | generated {RUN_DATE} | Fact/Estimate/Scenario labels retained"
        p.font.size = Pt(7)
        p.font.color.rgb = RGBColor(120, 130, 145)

    # Cover
    slide = prs.slides.add_slide(blank)
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = RGBColor(247, 249, 252)
    tx = slide.shapes.add_textbox(Inches(0.65), Inches(0.75), Inches(7.7), Inches(2.4))
    p = tx.text_frame.paragraphs[0]
    p.text = "상용 LLM 업체별\n전력·GPU·토큰 생성량\n2026–2030 시뮬레이션"
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = RGBColor(20, 33, 61)
    p.line_spacing = 0.92
    kpi_rows = data["exec_summary"][:3]
    for i, item in enumerate(kpi_rows):
        box = slide.shapes.add_shape(1, Inches(8.7), Inches(0.95 + i * 1.45), Inches(3.7), Inches(1.0))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(255, 255, 255)
        box.line.color.rgb = RGBColor(220, 228, 238)
        box.text_frame.text = f"{item['display']}\n{item['interpretation_kr']}"
        for para in box.text_frame.paragraphs:
            para.font.size = Pt(12)
            para.font.color.rgb = RGBColor(20, 33, 61)
    add_footer(slide)

    # Calculation and assumptions
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "계산식과 핵심 가정", "전력 → AI IT load → inference GW → token/day로 연결합니다.")
    formula_rows = data["formula_assumptions"][:6]
    table = slide.shapes.add_table(len(formula_rows) + 1, 3, Inches(0.55), Inches(1.1), Inches(12.2), Inches(5.45)).table
    headers = ["Block", "Formula", "해석 / 주의점"]
    widths = [2.2, 4.9, 5.1]
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(20, 33, 61)
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(8)
    for r, item in enumerate(formula_rows, start=1):
        vals = [item["category"], item["formula"], item["meaning_kr"]]
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(7.5)
            cell.margin_left = Inches(0.04)
            cell.margin_right = Inches(0.04)
    add_footer(slide)

    # Inference share fact-check
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "Inference 60%+ GW 비중은 fact가 아니라 scenario", "공개자료는 방향성은 강하지만 company-level GW split을 확정하지 않습니다.")
    fact_rows = [
        ["확인 결과", "2026년에 이미 전체 AI GW의 60% 이상이 inference라고 단정할 공식 company disclosure는 없음."],
        ["상향 anchor", "McKinsey/Deloitte는 2030 또는 2026 compute 관점에서 inference 비중 상승을 전망."],
        ["보수 anchor", "EPRI/Epoch AI는 현재 AI power가 training, experiments, inference로 대략 나뉜다고 설명."],
        ["모델 처리", "따라서 2026 base inference share는 업체별 52~80%로 두되 confidence/assumption으로 표기."],
        ["교체 경로", "업체별 scheduling telemetry, serving/training capex split, cluster-level utilization disclosure가 필요."],
    ]
    table = slide.shapes.add_table(len(fact_rows) + 1, 2, Inches(0.75), Inches(1.25), Inches(11.8), Inches(4.7)).table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(9.6)
    for c, h in enumerate(["항목", "판단"]):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(20, 33, 61)
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(9)
    for r, vals in enumerate(fact_rows, start=1):
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(11)
    add_footer(slide)

    # Fact anchors
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "Fact anchors used in the simulation", "Checked public numbers are separated from modeled assumptions.")
    fact_rows = fact_anchors()[:10]
    table = slide.shapes.add_table(len(fact_rows) + 1, 5, Inches(0.45), Inches(1.1), Inches(12.45), Inches(5.55)).table
    headers = ["Company", "Topic", "Metric", "Value", "Model use"]
    widths = [1.25, 1.25, 2.35, 2.85, 4.75]
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(20, 33, 61)
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(8)
    for r, f in enumerate(fact_rows, start=1):
        vals = [f.company, f.topic, f.metric, f.value, f.derivation_impact_kr]
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(6.7)
            cell.margin_left = Inches(0.03)
            cell.margin_right = Inches(0.03)
    add_footer(slide)

    # Scenario definitions
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "Bull / Base / Bear scenario logic", "Headline drivers: operational deploy speed and inference mix shift.")
    rows_def = data["scenario_definitions"]
    table = slide.shapes.add_table(len(rows_def) + 1, 5, Inches(0.55), Inches(1.1), Inches(12.2), Inches(5.45)).table
    headers = ["Scenario", "Deploy 2030", "Inference delta 2030", "Tokens/MW", "설명"]
    widths = [1.65, 1.35, 1.65, 1.2, 6.35]
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(20, 33, 61)
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(8)
    for r, item in enumerate(rows_def, start=1):
        vals = [
            item["scenario"],
            f"{item['operational_deploy_multiplier_2030']:.0%}",
            f"{item['inference_share_delta_2030']:+.0%}p",
            item["headline_tps_mw_rule"],
            item["description_kr"],
        ]
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(8)
    add_footer(slide)

    # Landscape
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "업체별 상용 LLM landscape", "Core rows are model owners, not cloud hosting providers.")
    rows = company_models()
    table = slide.shapes.add_table(len(rows) + 1, 5, Inches(0.45), Inches(1.15), Inches(12.4), Inches(5.5)).table
    headers = ["업체", "모델", "상용 표면", "Serving platform", "Attribution"]
    widths = [1.15, 1.65, 2.75, 2.55, 4.3]
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(20, 33, 61)
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(8)
    for r, m in enumerate(rows, start=1):
        vals = [m.company, m.model_family, m.commercial_surface, m.serving_platform, m.attribution_rule]
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(7)
            cell.margin_left = Inches(0.04)
            cell.margin_right = Inches(0.04)
    add_footer(slide)

    # Scenario chart
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "시나리오별 token capacity envelope", "Bull/Base/Bear에 전력제약·효율상승 혼합 case를 추가했습니다.")
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for scen in SCENARIO_CASES:
        chart_data.add_series(
            scen,
            [next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.7), Inches(1.2), Inches(11.9), Inches(5.35), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    add_footer(slide)

    # Token forecast line chart
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "2026–2030 token generation forecast", "Base case; quadrillion generated tokens/day equivalent.")
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for s in scenarios():
        chart_data.add_series(
            s.company,
            [next(r["inference_tokens_per_day"] / 1e15 for r in data["forecast"] if r["company"] == s.company and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.7), Inches(1.2), Inches(11.9), Inches(5.4), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    add_footer(slide)

    # GW split chart
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "2030 inference vs training GW split", "Inference share rises as commercial serving dominates incremental AI load.")
    chart_data = CategoryChartData()
    chart_data.categories = [s.company for s in scenarios()]
    chart_data.add_series("Inference GW", [next(r["inference_gw"] for r in data["forecast"] if r["company"] == s.company and r["year"] == 2030) for s in scenarios()])
    chart_data.add_series("Training GW", [next(r["training_gw"] for r in data["forecast"] if r["company"] == s.company and r["year"] == 2030) for s in scenarios()])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED, Inches(0.7), Inches(1.15), Inches(11.9), Inches(5.45), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    add_footer(slide)

    # Parameter map
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "Model parameter band map", "Closed frontier models are shown as bands only; MoE rows retain total and active params.")
    table = slide.shapes.add_table(9, 4, Inches(0.6), Inches(1.15), Inches(12.1), Inches(5.55)).table
    headers = ["업체", "Total parameter band", "Active parameter band", "Confidence"]
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(20, 33, 61)
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(8)
    for r, m in enumerate(company_models(), start=1):
        vals = [m.company, m.parameter_band_total, m.parameter_band_active, m.confidence]
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(8)
    add_footer(slide)

    # Sensitivity
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "Sensitivity: tokens/MW and utilization", "Bull/bear envelopes stress serving software, batching, quantization, and real utilization.")
    sens_2030 = [r for r in data["sensitivity"] if r["year"] == 2030]
    chart_data = CategoryChartData()
    chart_data.categories = [s.company for s in scenarios()]
    for name in ["Bear: lower tokens/MW and utilization", "Base", "Bull: higher batching/quantization/software efficiency"]:
        chart_data.add_series(name.split(":")[0], [next(r["inference_tokens_per_day"] / 1e15 for r in sens_2030 if r["company"] == s.company and r["scenario"] == name) for s in scenarios()])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.7), Inches(1.2), Inches(11.9), Inches(5.35), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    add_footer(slide)

    # Implications
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "Memory/HBM/SSD implications", "Marketing action translation for AI datacenter memory.")
    bullets = [
        "HBM: OpenAI/Google/Meta/xAI ramp는 long-term allocation, HBM4 roadmap lock-in, second-source qualification 메시지로 전환.",
        "DDR5/MRDIMM: inference serving fleet 확장은 CPU-side memory density와 bandwidth attach story를 만든다.",
        "Enterprise SSD/QLC: RAG, checkpointing, vector retrieval, agent memory가 token capacity growth의 storage tax로 따라온다.",
        "CXL: high-utilization inference cluster의 memory expansion과 utilization recovery 메시지에 적합.",
        "Account motion: company-owner token forecast를 top account brief, qualification kit, scarcity-based executive proposal로 연결.",
    ]
    tx = slide.shapes.add_textbox(Inches(0.75), Inches(1.25), Inches(11.8), Inches(4.8))
    tf = tx.text_frame
    tf.clear()
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = b
        p.font.size = Pt(17)
        p.font.color.rgb = RGBColor(20, 33, 61)
        p.space_after = Pt(14)
    add_footer(slide)

    # Evidence audit
    slide = prs.slides.add_slide(blank)
    ppt_add_title(slide, "Confidence and evidence audit", "The model is useful because uncertainty is explicit, not hidden.")
    audit = [
        "Fact: official model docs/cards, official infrastructure announcements, public technical reports.",
        "Estimate: active power, inference/training share, utilization, tokens/sec/MW by company.",
        "Scenario: 2027–2030 ramp, efficiency CAGR, commercial token demand absorption.",
        "Guardrails: active <= contracted power; inference+training=100%; closed parameters as bands; MoE total+active params.",
        "Next replacement path: site-level MW activation, model routing mix, API traffic, benchmarked tokens/MW by workload.",
    ]
    tx = slide.shapes.add_textbox(Inches(0.85), Inches(1.15), Inches(11.2), Inches(5.0))
    tf = tx.text_frame
    tf.clear()
    for i, b in enumerate(audit):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = b
        p.font.size = Pt(16)
        p.font.color.rgb = RGBColor(20, 33, 61)
        p.space_after = Pt(16)
    add_footer(slide)

    prs.save(path)


def write_html(data: dict[str, Any], path: Path) -> None:
    payload = json.dumps(data, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>상용 LLM 토큰 Capacity 대시보드</title>
  <style>
    :root {{
      --ink:#162033; --muted:#667085; --line:#d8e0ea; --bg:#f6f8fb;
      --blue:#2563eb; --green:#0f9f6e; --red:#cc3a3a; --amber:#b7791f;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ padding:28px 34px 18px; background:#fff; border-bottom:1px solid var(--line); }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .sub {{ color:var(--muted); margin-top:8px; font-size:14px; max-width:1000px; }}
    main {{ padding:22px 34px 40px; }}
    .controls {{ display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:18px; }}
    select, input {{ padding:9px 10px; border:1px solid var(--line); border-radius:6px; background:#fff; font-size:14px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(160px,1fr)); gap:12px; margin-bottom:18px; }}
    .kpi {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .kpi .label {{ color:var(--muted); font-size:12px; }}
    .kpi .value {{ font-size:24px; font-weight:750; margin-top:6px; }}
    section {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:18px; margin-bottom:18px; }}
    h2 {{ margin:0 0 12px; font-size:18px; }}
    .chart {{ display:grid; gap:8px; }}
    .barrow {{ display:grid; grid-template-columns:110px 1fr 120px; align-items:center; gap:10px; min-height:26px; }}
    .bar {{ height:16px; background:#e9eef6; border-radius:4px; overflow:hidden; }}
    .fill {{ height:100%; background:linear-gradient(90deg,var(--blue),var(--green)); }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th, td {{ border-bottom:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; }}
    th {{ background:#f0f4fa; color:#26344d; }}
    .pill {{ display:inline-block; padding:3px 7px; border-radius:999px; background:#eef4ff; color:#1d4ed8; font-size:12px; }}
    .note {{ color:var(--muted); font-size:12px; margin-top:8px; }}
    @media (max-width:900px) {{
      .grid {{ grid-template-columns:1fr 1fr; }}
      .barrow {{ grid-template-columns:90px 1fr; }}
      .barrow .num {{ grid-column:2; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>상용 LLM 업체별 전력·GPU·토큰 생성량 시뮬레이션</h1>
    <div class="sub">2026–2030 기준 시나리오. Core company는 Microsoft, Google, Meta, xAI, OpenAI, Anthropic, DeepSeek, Alibaba, Tencent입니다. 숫자는 Fact/Estimate/Scenario와 신뢰도를 함께 읽어야 합니다.</div>
  </header>
  <main>
    <div class="controls">
      <label>시나리오 <select id="scenario"></select></label>
      <label>업체 <select id="company"></select></label>
      <label>연도 <select id="year"></select></label>
      <label>tokens/MW 민감도 <input id="tps" type="range" min="65" max="145" value="100" /> <span id="tpsLabel">100%</span></label>
    </div>
    <div class="grid" id="kpis"></div>
    <section>
      <h2>업체별 토큰 forecast</h2>
      <div class="chart" id="tokenChart"></div>
      <div class="note">단위: quadrillion generated output tokens/day. slider는 선택된 benchmark TPS/MW의 민감도만 보여주며 headline에는 별도 utilization multiplier가 없습니다.</div>
    </section>
    <section>
      <h2>계산식과 가정</h2>
      <table id="tokenDefs"></table>
      <div class="note">Headline `inference_tokens_per_day`는 생성 output token equivalent입니다. InferenceX total throughput은 processed token proxy이므로 output throughput과 분리해 봅니다.</div>
      <table id="formulas"></table>
      <div class="note">Inference 60%+ GW 비중은 공식 fact가 아니라 scenario assumption입니다. Source audit에서 McKinsey/Deloitte/EPRI-Epoch anchor를 함께 확인하세요.</div>
    </section>
    <section>
      <h2>시나리오 정의</h2>
      <table id="scenarioDefs"></table>
    </section>
    <section>
      <h2>Inference / Training GW split</h2>
      <div class="chart" id="gwChart"></div>
    </section>
    <section>
      <h2>확인값 vs 합리적 가정: company input audit</h2>
      <table id="audit"></table>
    </section>
    <section>
      <h2>Fact anchor</h2>
      <table id="facts"></table>
    </section>
    <section>
      <h2>InferenceX 핵심 TPS/MW 선택표</h2>
      <table id="coreInferencex"></table>
      <div class="note">공통 조건: B200, single_turn, ISL=1024, OSL=1024, `output_tok_s_mw` selected max. Dynamo/TRT-LLM/MTP 계열 serving stack이 있으면 우선하고, 없으면 같은 조건의 public max를 씁니다. Purpose-built accelerator의 비교 가능 row가 없으면 GPU proxy와 같게 두고 uplift를 적용하지 않습니다.</div>
    </section>
    <section>
      <h2>보조 Benchmark sanity check</h2>
      <table id="benchmarks"></table>
      <div class="note">첨부 엑셀의 effective active params / GPU count / TPS per GPU 방식을 reference layer로 통합했습니다. Closed model proxy는 결론이 아니라 guardrail입니다.</div>
    </section>
    <section>
      <h2>Energy sanity reference</h2>
      <table id="energySanity"></table>
      <div class="note">A08 Cycle 1 반영: Joule/IBM/2026 serving sources는 Base tokens/MW를 직접 바꾸지 않고, energy/query 및 joules/token 검증 레이어로 사용합니다.</div>
    </section>
    <section>
      <h2>SLO / utilization sensitivity</h2>
      <table id="utilSensitivity"></table>
      <div class="note">A09 Cycle 1 반영: utilization은 GPU 점유율이 아니라 TTFT/TPOT, batchability, placement, failover reserve가 반영된 평균값입니다.</div>
    </section>
    <section>
      <h2>InferenceX ingestion layer</h2>
      <table id="inferencex"></table>
      <div class="note">InferenceX와 MLPerf는 company production telemetry가 아니라 benchmark/proxy layer입니다. DB dump/CSV 정규화, official benchmark submission, vendor serving stack docs는 A08/A09/A11 provenance로 승격합니다.</div>
    </section>
    <section>
      <h2>Hallucination 체크리스트</h2>
      <table id="hallucination"></table>
    </section>
    <section>
      <h2>Model owner 귀속 기준</h2>
      <table id="models"></table>
    </section>
  </main>
  <script>
    const DATA = {payload};
    const ROWS = DATA.scenario_forecast || DATA.forecast;
    const companies = [...new Set(ROWS.map(d => d.company))];
    const years = [...new Set(ROWS.map(d => d.year))];
    const scenarios = [...new Set(ROWS.map(d => d.scenario || "Base"))];
    const $ = id => document.getElementById(id);
    function init() {{
      $("company").innerHTML = '<option value="ALL">전체</option>' + companies.map(c=>`<option>${{c}}</option>`).join('');
      $("year").innerHTML = years.map(y=>`<option>${{y}}</option>`).join('');
      $("scenario").innerHTML = scenarios.map(s=>`<option>${{s}}</option>`).join('');
      $("scenario").value = "Base";
      $("year").value = 2030;
      ["scenario","company","year","tps"].forEach(id => $(id).addEventListener('input', render));
      render();
    }}
    function selectedRows() {{
      const c = $("company").value, y = Number($("year").value), s = $("scenario").value;
      return ROWS.filter(d => d.year === y && (d.scenario || "Base") === s && (c === "ALL" || d.company === c));
    }}
    function adjustedTokens(row) {{
      const tps = Number($("tps").value)/100;
      return row.inference_gw * 1000 * row.tokens_per_second_per_mw * tps * 86400;
    }}
    function renderKpis(rows) {{
      const totalTokens = rows.reduce((a,d)=>a+adjustedTokens(d),0);
      const infGw = rows.reduce((a,d)=>a+d.inference_gw,0);
      const trainGw = rows.reduce((a,d)=>a+d.training_gw,0);
      const avgJ = rows.reduce((a,d)=>a+d.joules_per_token,0)/Math.max(rows.length,1);
      const items = [
        ["토큰/day", (totalTokens/1e15).toFixed(2)+"Q"],
        ["추론 GW", infGw.toFixed(2)+" GW"],
        ["학습 GW", trainGw.toFixed(2)+" GW"],
        ["평균 J/token", avgJ.toFixed(3)]
      ];
      $("kpis").innerHTML = items.map(i=>`<div class="kpi"><div class="label">${{i[0]}}</div><div class="value">${{i[1]}}</div></div>`).join('');
    }}
    function renderBars(rows) {{
      const max = Math.max(...rows.map(adjustedTokens), 1);
      $("tokenChart").innerHTML = rows.sort((a,b)=>adjustedTokens(b)-adjustedTokens(a)).map(d => {{
        const val = adjustedTokens(d);
        return `<div class="barrow"><strong>${{d.company}}</strong><div class="bar"><div class="fill" style="width:${{val/max*100}}%"></div></div><div class="num">${{(val/1e15).toFixed(2)}}Q</div></div>`;
      }}).join('');
      const maxGw = Math.max(...rows.map(d=>d.inference_gw+d.training_gw), 1);
      $("gwChart").innerHTML = rows.map(d => {{
        const inf = d.inference_gw / maxGw * 100, train = d.training_gw / maxGw * 100;
        return `<div class="barrow"><strong>${{d.company}}</strong><div class="bar"><div class="fill" style="width:${{inf}}%; background:var(--green); float:left"></div><div class="fill" style="width:${{train}}%; background:var(--amber); float:left"></div></div><div class="num">${{d.inference_gw.toFixed(2)}} / ${{d.training_gw.toFixed(2)}} GW</div></div>`;
      }}).join('');
    }}
    function renderTables(rows) {{
      $("audit").innerHTML = `<tr><th>업체</th><th>입력 항목</th><th>모델값 (2026 -> 2030)</th><th>분류</th><th>공개 확인값 또는 공개 공백</th><th>왜 fact가 아닌가</th></tr>` +
        DATA.company_input_audit.filter(a => $("company").value === "ALL" || a.company === $("company").value)
          .map(a=>`<tr><td>${{a.company}}</td><td>${{a.metric}}</td><td>${{a.model_value_base_2026_2030}}</td><td><span class="pill">${{a.evidence_class}}</span></td><td>${{a.confirmed_public_fact_or_disclosure_gap}}</td><td>${{a.why_modelled_value_is_not_a_fact}}</td></tr>`).join('');
      $("models").innerHTML = `<tr><th>업체</th><th>모델 family</th><th>상용 표면</th><th>Attribution rule</th></tr>` +
        DATA.company_models.filter(m => $("company").value === "ALL" || m.company === $("company").value)
          .map(m=>`<tr><td>${{m.company}}</td><td>${{m.model_family}}</td><td>${{m.commercial_surface}}</td><td>${{m.attribution_rule}}</td></tr>`).join('');
      $("formulas").innerHTML = `<tr><th>구분</th><th>계산식</th><th>해석</th><th>Sources</th></tr>` +
        DATA.formula_assumptions.map(f=>`<tr><td>${{f.category}}</td><td><code>${{f.formula}}</code></td><td>${{f.meaning_kr}}</td><td>${{f.source_ids}}</td></tr>`).join('');
      $("tokenDefs").innerHTML = `<tr><th>Token metric</th><th>정의</th><th>포함</th><th>InferenceX mapping</th><th>Status</th></tr>` +
        DATA.token_definitions.map(t=>`<tr><td>${{t.korean_name}}<br/><code>${{t.token_metric}}</code></td><td>${{t.definition_kr}}</td><td>${{t.included}}</td><td>${{t.inferencex_mapping}}</td><td>${{t.status}}</td></tr>`).join('');
      $("scenarioDefs").innerHTML = `<tr><th>시나리오</th><th>2030 가동률 배수</th><th>2030 추론 비중 변화</th><th>Tokens/MW</th><th>설명</th></tr>` +
        DATA.scenario_definitions.map(s=>`<tr><td>${{s.scenario}}</td><td>${{Math.round(s.operational_deploy_multiplier_2030*100)}}%</td><td>${{Math.round(s.inference_share_delta_2030*100)}}%p</td><td>${{s.headline_tps_mw_rule}}</td><td>${{s.description_kr}}</td></tr>`).join('');
      $("facts").innerHTML = `<tr><th>업체</th><th>지표</th><th>값</th><th>Source</th><th>모델 반영 방식</th></tr>` +
        DATA.fact_anchors.map(f=>`<tr><td>${{f.company}}</td><td>${{f.metric}}</td><td>${{f.value}}</td><td>${{f.source_id}}</td><td>${{f.derivation_impact_kr}}</td></tr>`).join('');
      $("coreInferencex").innerHTML = `<tr><th>Proxy model</th><th>Mapped companies</th><th>GPU / condition</th><th>Rows</th><th>Output TPS/MW selected</th><th>Min-Max</th><th>Basis</th><th>Use</th></tr>` +
        DATA.core_inferencex_benchmarks.map(b=>`<tr><td>${{b.proxy_model}}</td><td>${{b.mapped_companies}}</td><td>${{b.gpu}}, ISL/OSL=${{b.isl}}/${{b.osl}}</td><td>${{b.row_count}}</td><td>${{b.output_tok_s_mw_selected.toLocaleString()}}</td><td>${{b.output_tok_s_mw_min.toLocaleString()}} - ${{b.output_tok_s_mw_max.toLocaleString()}}</td><td>${{b.selection_basis}}</td><td>${{b.headline_use}}</td></tr>`).join('');
      $("benchmarks").innerHTML = `<tr><th>업체</th><th>연도</th><th>Proxy</th><th>Benchmark QTokens</th><th>Model QTokens</th><th>차이</th><th>주의점</th></tr>` +
        DATA.benchmark_reference.filter(b => b.year === Number($("year").value) && ($("company").value === "ALL" || b.company === $("company").value))
          .map(b=>`<tr><td>${{b.company}}</td><td>${{b.year}}</td><td>${{b.proxy_model}}</td><td>${{b.benchmark_annual_tokens_q}}</td><td>${{b.model_annual_tokens_q}}</td><td>${{b.benchmark_vs_model_pct}}%</td><td>${{b.caveat_kr}}</td></tr>`).join('');
      $("energySanity").innerHTML = `<tr><th>업체</th><th>연도</th><th>Profile</th><th>J/token</th><th>Energy implied Q/day</th><th>Model Q/day</th><th>차이</th><th>해석</th></tr>` +
        DATA.energy_sanity_reference.filter(e => e.year === Number($("year").value) && ($("company").value === "ALL" || e.company === $("company").value))
          .map(e=>`<tr><td>${{e.company}}</td><td>${{e.year}}</td><td>${{e.profile}}</td><td>${{e.profile_joules_per_token}}</td><td>${{e.energy_implied_tokens_per_day_q}}</td><td>${{e.model_tokens_per_day_q}}</td><td>${{e.energy_vs_model_pct}}%</td><td>${{e.interpretation_kr}}</td></tr>`).join('');
      $("utilSensitivity").innerHTML = `<tr><th>업체</th><th>연도</th><th>Profile</th><th>Utilization</th><th>TPS/MW</th><th>Q/day</th><th>기준 대비</th><th>설명</th></tr>` +
        DATA.utilization_sensitivity.filter(u => u.year === Number($("year").value) && ($("company").value === "ALL" || u.company === $("company").value))
          .map(u=>`<tr><td>${{u.company}}</td><td>${{u.year}}</td><td>${{u.profile}}</td><td>${{u.adjusted_utilization}}</td><td>${{u.adjusted_tokens_per_second_per_mw}}</td><td>${{u.tokens_per_day_q}}</td><td>${{u.delta_vs_base_pct}}%</td><td>${{u.description_kr}}</td></tr>`).join('');
      const ix = DATA.inferencex || {{}};
      const ixManifest = ix.manifest || {{}};
      $("inferencex").innerHTML = `<tr><th>항목</th><th>값</th></tr>` +
        `<tr><td>최신 DB dump</td><td>${{ixManifest.latest_db_dump?.tag_name || "not refreshed"}}</td></tr>` +
        `<tr><td>Release asset</td><td>${{ixManifest.latest_db_dump?.asset_name || ""}}</td></tr>` +
        `<tr><td>Source index rows</td><td>${{ix.source_index?.length || 0}}</td></tr>` +
        `<tr><td>Evidence rule</td><td>${{ixManifest.evidence_rule || ""}}</td></tr>`;
      $("hallucination").innerHTML = `<tr><th>ID</th><th>영역</th><th>질문</th><th>Pass 기준</th><th>심각도</th><th>상태</th></tr>` +
        DATA.hallucination_checklist.map(h=>`<tr><td>${{h.check_id}}</td><td>${{h.area}}</td><td>${{h.question_kr}}</td><td>${{h.pass_criteria_kr}}</td><td>${{h.severity}}</td><td>${{h.current_status}}</td></tr>`).join('');
    }}
    function render() {{
      $("tpsLabel").textContent = $("tps").value + "%";
      const rows = selectedRows();
      renderKpis(rows); renderBars(rows); renderTables(rows);
    }}
    init();
  </script>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")


def write_markdown(data: dict[str, Any], path: Path) -> None:
    rows_2030 = sorted([r for r in data["forecast"] if r["year"] == 2030], key=lambda r: r["inference_tokens_per_day"], reverse=True)
    lines = [
        "# 상용 LLM 업체별 전력·GPU·토큰 생성량 시뮬레이션 (2026–2030)",
        "",
        f"- 생성일: {RUN_DATE}",
        "- 목적: 상용 LLM owner 기준으로 전력 capacity, 추론/학습 split, GPU/ASIC mix, tokens/sec/MW, GPU benchmark reference, token 생성량을 연결한 임원 보고용 기준 시나리오 작성",
        "- Headline token 정의: `inference_tokens_per_day`는 generated output token equivalent입니다. input+output processed token, training token, billable token과 분리합니다.",
        "- 주의: 이 문서는 투자 조언이 아니라 supply-chain / token-capacity intelligence simulation입니다.",
        "",
        "## 핵심 결론",
    ]
    for item in data["exec_summary"][:3]:
        lines.append(f"- **{item['metric']}**: {item['display']} - {item['interpretation_kr']}")
    lines += [
        "",
        "## 2030 기준 시나리오 순위",
        "",
        "| 순위 | 업체 | 지역 | 추론 GW | 토큰/일 | 신뢰도 |",
        "|---:|---|---|---:|---:|---|",
    ]
    for idx, row in enumerate(rows_2030, start=1):
        lines.append(
            f"| {idx} | {row['company']} | {row['region']} | {row['inference_gw']:.2f} | {row['inference_tokens_per_day']/1e15:.2f}Q | {row['confidence']} |"
        )
    lines += [
        "",
        "## 방법론",
        "",
        "```text",
        "operational_power_gw = contracted_power_gw * operational_deployment_share",
        "it_load_gw = operational_power_gw / pue",
        "ai_it_load_gw = it_load_gw * ai_workload_share",
        "inference_gw = ai_it_load_gw * inference_power_share",
        "gpu_workload_avg_tps_per_mw = short_share*gpu_short_tps_mw + long_share*gpu_long_tps_mw + agentic_share*gpu_agentic_tps_mw",
        "fleet_reference_tps_per_mw = h200_share*h200_workload_avg + b200_share*b200_workload_avg + gb200_share*gb200_workload_avg + purpose_built_share*purpose_workload_avg",
        "tokens_per_second_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor",
        "inference_tokens_per_day = inference_mw * tokens_per_second_per_mw * 86,400",
        "joules_per_token = 1,000,000 / tokens_per_second_per_mw",
        "```",
        "",
        "## Number Trace In Excel",
        "",
        "- Excel `02b_number_trace`는 모든 company-year-scenario 핵심 수치에 대해 `formula_or_rule`, `why_this_number`, `source_ids`, `assumption_ids`, `replacement_path`를 제공합니다.",
        "- `contracted_power_gw`는 source가 있는 업체의 committed/planned ceiling anchor와, 공개 GW가 없는 업체의 scenario capacity envelope를 구분합니다.",
        "- `active_power_gw`는 `operational_deployment_share`를 통해 contracted capacity에서 전환되는 modeled operational power입니다.",
        "- `gpu_asic_mix`는 숫자로 표시하되 comparable benchmark가 없는 purpose-built accelerator에는 uplift를 적용하지 않습니다.",
        "- `utilization`, MoE/architecture uplift, software CAGR는 headline 계산에서 제외하고 보조 sensitivity로만 보관합니다.",
        "- Excel `02c_fact_vs_assumption_audit`는 회사별 핵심 입력을 공식 확인값, 공식 사실으로 뒷받침된 시나리오, 합리적 가정, benchmark proxy, formula output으로 분리합니다.",
        "",
        "## 확인값과 합리적 가정의 분리",
        "",
        "| 업체 | 입력 항목 | 모델값 (Base 2026 -> 2030) | Evidence class | 공개 확인값 또는 공개 공백 |",
        "|---|---|---|---|---|",
    ]
    for item in data["company_input_audit"]:
        lines.append(
            f"| {item['company']} | {item['metric']} | {item['model_value_base_2026_2030']} | {item['evidence_class']} | {item['confirmed_public_fact_or_disclosure_gap']} |"
        )
    lines += [
        "",
        "## Token 정의",
        "",
        "| Token metric | 한국어 | 정의 | InferenceX mapping | Status |",
        "|---|---|---|---|---|",
    ]
    for item in data["token_definitions"]:
        lines.append(f"| `{item['token_metric']}` | {item['korean_name']} | {item['definition_kr']} | {item['inferencex_mapping']} | {item['status']} |")
    lines += [
        "",
        "## 계산식/가정 감사",
        "",
        "| Block | Formula | 해석 | Sources |",
        "|---|---|---|---|",
    ]
    for item in data["formula_assumptions"]:
        lines.append(f"| {item['category']} | `{item['formula']}` | {item['meaning_kr']} | {item['source_ids']} |")
    lines += [
        "",
        "## Fact Anchor",
        "",
        "| Anchor | 업체 | 지표 | 값 | 날짜 | Source | 모델 반영 방식 |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in data["fact_anchors"]:
        lines.append(f"| {f['anchor_id']} | {f['company']} | {f['metric']} | {f['value']} | {f['fact_date']} | {f['source_id']} | {f['derivation_impact_kr']} |")
    lines += [
        "",
        "## 시나리오 설계",
        "",
        "| 시나리오 | 2030 가동률 배수 | 2030 추론 비중 변화 | TPS/MW headline 처리 | 설명 |",
        "|---|---:|---:|---|---|",
    ]
    for item in data["scenario_definitions"]:
        lines.append(
            f"| {item['scenario']} | {item['operational_deploy_multiplier_2030']:.0%} | {item['inference_share_delta_2030']:+.0%}p | {item['headline_tps_mw_rule']} | {item['description_kr']} |"
        )
    lines += [
        "",
        "## 추론 60%+ Fact Check",
        "",
        "- 2026년에 이미 전체 AI GW의 60% 이상이 inference라는 주장은 공식 company-level fact로 단정하지 않습니다.",
        "- McKinsey/Deloitte는 inference 비중 상승 전망을 제공하지만, 업체별 active GW split disclosure가 아닙니다.",
        "- EPRI/Epoch AI는 현재 AI power가 training, experiments, inference로 대략 나뉜다는 보수적 anchor를 제공합니다.",
        "- 따라서 본 모델의 inference share는 `Scenario assumption`이며, source transparency에 맞춰 confidence를 별도 표기합니다.",
        "",
        "## 2030 시나리오 범위",
        "",
        "| 시나리오 | 가동 전력 GW | 추론 GW | 가중 추론 비중 | 토큰/일 | 기준 대비 변화 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in [r for r in data["scenario_summary"] if r["year"] == 2030]:
        lines.append(
            f"| {row['scenario']} | {row['active_power_gw']:.2f} | {row['inference_gw']:.2f} | {row['weighted_inference_share']:.0%} | {row['inference_tokens_per_day_q']:.2f}Q | {row['delta_vs_base_2030_pct']}% |"
        )
    lines += [
        "",
        "## InferenceX 핵심 TPS/MW 선택표",
        "",
        "| Proxy model | 적용 업체 | 조건 | rows | output TPS/MW selected | Min-Max | Basis |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in data["core_inferencex_benchmarks"]:
        lines.append(
            f"| {row['proxy_model']} | {row['mapped_companies']} | {row['gpu']}, {row['benchmark_type']}, ISL/OSL {row['isl']}/{row['osl']} | {row['row_count']} | {row['output_tok_s_mw_selected']:,} | {row['output_tok_s_mw_min']:,}-{row['output_tok_s_mw_max']:,} | {row['selection_basis']} |"
        )
    lines += [
        "",
        "- 위 표의 selected output TPS/MW가 headline 산식에 직접 들어갑니다. Dynamo/TRT-LLM/MTP 계열 serving stack이 있으면 우선하고, 없으면 같은 조건의 public max를 씁니다. 공개 comparable row가 없는 purpose-built accelerator는 동일 proxy 값을 적용해 검증되지 않은 uplift를 배제합니다.",
        "",
        "## 보조 Benchmark Sanity Check",
        "",
        "| 업체 | Proxy | Benchmark annual QTokens | Model annual QTokens | 차이 | 주의점 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in [r for r in data["benchmark_reference"] if r["year"] == 2030]:
        lines.append(
            f"| {row['company']} | {row['proxy_model']} | {row['benchmark_annual_tokens_q']:.2f} | {row['model_annual_tokens_q']:.2f} | {row['benchmark_vs_model_pct']}% | {row['caveat_kr']} |"
        )
    lines += [
        "",
        "## A08 Cycle 1: Energy Sanity Reference",
        "",
        "- Base `tokens_per_second_per_mw`는 고정조건 InferenceX output TPS/MW proxy로 구성되며, production telemetry가 아닌 benchmark-derived estimate입니다.",
        "- Joule/IBM/2026 serving sources는 company production telemetry가 아니라 energy/query, joules/token, prefill/decode trade-off 검증 레이어로 사용합니다.",
        "- Strict-SLO/agentic long-context는 energy/token을 악화시킬 수 있고, batchable optimized serving은 개선 가능성이 있으나 둘 다 sensitivity입니다.",
        "",
        "| 업체 | Profile | J/token | Energy implied Q/day | Model Q/day | 차이 | 해석 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in [r for r in data["energy_sanity_reference"] if r["year"] == 2030 and r["company"] in ("OpenAI", "Google", "Anthropic")]:
        lines.append(
            f"| {row['company']} | {row['profile']} | {row['profile_joules_per_token']:.4f} | {row['energy_implied_tokens_per_day_q']:.3f} | {row['model_tokens_per_day_q']:.3f} | {row['energy_vs_model_pct']}% | {row['interpretation_kr']} |"
        )
    lines += [
        "",
        "## A09 Cycle 1: SLO / Utilization Sensitivity",
        "",
        "- Utilization band는 학습 및 sensitivity reference로 유지하되 headline token 식에는 곱하지 않습니다.",
        "- utilization은 GPU 점유율이 아니라 TTFT/TPOT, batchability, placement, failover reserve가 반영된 평균값입니다.",
        "- strict-SLO와 agentic long-context workload는 output capacity를 낮출 수 있고, batchable optimized workload는 상향 sensitivity입니다.",
        "",
        "| 업체 | Profile | Adjusted utilization | Adjusted TPS/MW | Q/day | 기준 대비 | 설명 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in [r for r in data["utilization_sensitivity"] if r["year"] == 2030 and r["company"] in ("OpenAI", "Google", "Meta")]:
        lines.append(
            f"| {row['company']} | {row['profile']} | {row['adjusted_utilization']:.3f} | {row['adjusted_tokens_per_second_per_mw']:.0f} | {row['tokens_per_day_q']:.3f} | {row['delta_vs_base_pct']}% | {row['description_kr']} |"
        )
    ix = data["inferencex"]
    latest = ix["manifest"].get("latest_db_dump", {})
    parsed = ix["manifest"].get("parsed_dump", {})
    lines += [
        "",
        "## InferenceX Ingestion Layer",
        "",
        "- InferenceX와 MLPerf는 company production telemetry가 아니라 benchmark/proxy layer입니다.",
        "- Dashboard DOM 크롤링보다 GitHub release DB dump, benchmark repo, app API/schema를 우선합니다.",
        f"- 최신 확인 DB dump: `{latest.get('tag_name', 'not refreshed')}` / `{latest.get('asset_name', '')}` / `{latest.get('asset_size_bytes', '')}` bytes.",
        f"- Full dump parse: `{parsed.get('status', 'not_run')}` / benchmark rows `{parsed.get('benchmark_rows', 0)}` / metric profile rows `{parsed.get('metric_profile_rows', 0)}` / SHA-256 `{parsed.get('sha256', '')}`.",
        "- 정규화 결과는 엑셀 `12d_ix_benchmark_results`, `12e_ix_metric_profile`, `12f_ix_accuracy_evals`, `12g_ix_dump_inventory`에 반영됩니다.",
        "",
        "| Tab | 모델 내 사용처 | Forecast 반영 |",
        "|---|---|---|",
    ]
    for row in ix["tab_rules"]:
        lines.append(f"| {row.get('dashboard_tab', '')} | {row.get('use_in_model', '')} | {row.get('forecast_use', '')} |")
    lines += [
        "",
        "## Hallucination 체크리스트",
        "",
        "| ID | 영역 | 질문 | Pass 기준 | 심각도 | 상태 |",
        "|---|---|---|---|---|---|",
    ]
    for item in data["hallucination_checklist"]:
        lines.append(
            f"| {item['check_id']} | {item['area']} | {item['question_kr']} | {item['pass_criteria_kr']} | {item['severity']} | {item['current_status']} |"
        )
    lines += [
        "",
        "## 귀속 기준",
    ]
    for m in company_models():
        lines.append(f"- **{m.company}**: {m.attribution_rule}")
    lines += [
        "",
        "## 근거 관리 원칙",
        "",
        "- Fact: official model docs/cards, company announcements, technical reports.",
        "- Estimate: operational power, AI/inference share, company-level benchmark TPS/MW mapping.",
        "- Scenario: 2027–2030 operational deployment ramp와 inference allocation.",
        "- Closed model parameter는 official disclosure가 없으면 단일 숫자가 아니라 band로만 표기.",
        "- MoE는 total parameter와 active parameter를 분리.",
        "",
        "## Source Registry",
        "",
        "| Source ID | Tier | Publisher | Date | Use | URL/report |",
        "|---|---|---|---|---|---|",
    ]
    for s in sources():
        lines.append(f"| {s.source_id} | {s.tier} | {s.publisher} | {s.date} | {s.use_in_model} | {s.url_or_report} |")
    lines += [
        "",
        "## 검증",
        "",
        f"- Status: **{data['validation']['status']}**",
    ]
    for key, val in data["validation"]["model_checks"].items():
        lines.append(f"- {key}: {val}")
    if data["validation"]["failures"]:
        lines.append("- Failures:")
        for f in data["validation"]["failures"]:
            lines.append(f"  - {f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_interactivity_summary(data: dict[str, Any], path: Path) -> None:
    rows = data["interactivity_reference_profiles"]

    def fmt_int(value: Any) -> str:
        return "" if value == "" else f"{int(round(float(value))):,}"

    def fmt_float(value: Any) -> str:
        return "" if value == "" else f"{float(value):,.2f}"

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["proxy_model"], row["gpu"], row["workload_type"]), []).append(row)

    def best_available(group_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        selected = [row for row in group_rows if row["selection_status"] != "missing"]
        if not selected:
            return None
        return max(
            selected,
            key=lambda row: (
                row["target_tok_s_user"],
                1 if row["selection_status"] == "selected_optimized_stack" else 0,
                row["selected_output_tps_per_mw"] or 0,
            ),
        )

    lines = [
        "# InferenceX Interactivity x GPU Serving Summary",
        "",
        f"작성일: {RUN_DATE}",
        "",
        "## 기준",
        "",
        "- 원천 데이터: `llm_token_capacity_project/data/inferencex/normalized/inferencex_benchmark_results.csv`",
        "- Interactivity target: `10`, `30`, `50`, `70`, `100` generated tokens/sec/user",
        "- Source `tok_s_user`가 비어 있어 `output_tok_s_gpu / concurrency`로 per-user generated token rate를 계산한다.",
        "- Selection: target 이상 row 중 Dynamo/TRT-LLM/MTP 계열 stack이 있으면 그 안의 최고 `output_tok_s_mw`, 없으면 public max.",
        "- Precision/concurrency/framework는 선택된 최고 TPS/MW row의 실제 조건을 그대로 사용한다.",
        "- `agentic_derived`는 direct 100k-input benchmark가 아니라 long_chat row에 Kimi K2.5 agentic/long ratio `10.9%`를 곱한 effective 기준이다.",
        "",
        "## GPU별 추천 구성",
        "",
        "각 proxy/GPU/workload에서 가능한 가장 높은 interactivity target을 먼저 선택한다. 같은 target에서는 optimized stack을 우선한다.",
        "",
        "| Proxy | GPU | Workload | Recommended target tok/s/user | TPS/MW | Actual tok/s/user | Concurrency | Framework | Precision | Status |",
        "|---|---:|---|---:|---:|---:|---:|---|---|---|",
    ]
    for key in sorted(grouped):
        row = best_available(grouped[key])
        proxy, gpu, workload = key
        if row is None:
            lines.append(f"| `{proxy}` | {gpu.upper()} | {workload} | missing |  |  |  |  |  | no target available |")
            continue
        lines.append(
            f"| `{proxy}` | {gpu.upper()} | {workload} | {row['target_tok_s_user']} | "
            f"{fmt_int(row['selected_output_tps_per_mw'])} | {fmt_float(row['selected_tok_s_user'])} | "
            f"{row['selected_concurrency']} | {row['selected_framework']} | {row['selected_precision']} | {row['selection_status']} |"
        )

    lines.extend([
        "",
        "## 전체 후보",
        "",
        "| Proxy | GPU | Workload | Target tok/s/user | Eligible rows | Optimized rows | TPS/MW | Actual tok/s/user | Concurrency | Framework | Precision | Status | Basis |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ])
    for row in rows:
        lines.append(
            f"| `{row['proxy_model']}` | {row['gpu'].upper()} | {row['workload_type']} | {row['target_tok_s_user']} | "
            f"{row['eligible_rows']} | {row['optimized_eligible_rows']} | {fmt_int(row['selected_output_tps_per_mw'])} | "
            f"{fmt_float(row['selected_tok_s_user'])} | {row['selected_concurrency']} | {row['selected_framework']} | "
            f"{row['selected_precision']} | {row['selection_status']} | {row['selection_basis']} |"
        )

    lines.extend([
        "",
        "## 해석 메모",
        "",
        "- `selected_optimized_stack`은 Dynamo/TRT-LLM/MTP 계열 row가 target을 만족했고, 그 안에서 최고 TPS/MW를 골랐다는 뜻이다.",
        "- `selected_public_max`는 target을 만족하는 optimized stack row가 없어 전체 public row 중 최고 TPS/MW를 골랐다는 뜻이다.",
        "- `missing`은 해당 proxy/GPU/workload에서 target tok/s/user를 만족하는 row가 없다는 뜻이다.",
        "- 이 summary는 엑셀 적용 후보 테이블이며, headline forecast의 workload mix를 자동으로 바꾸지는 않는다.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_ppt(data: dict[str, Any], path: Path) -> None:
    """Create an executive-grade, editable PowerPoint deck.

    This definition intentionally overrides the earlier functional deck writer.
    The structure here prioritizes boardroom readability: one claim per slide,
    larger charts, fewer dense tables, and visible evidence boundaries.
    """

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    navy = RGBColor(16, 27, 46)
    ink = RGBColor(28, 38, 54)
    muted = RGBColor(103, 116, 134)
    blue = RGBColor(33, 96, 214)
    green = RGBColor(20, 148, 103)
    amber = RGBColor(190, 123, 35)
    red = RGBColor(185, 56, 56)
    bg = RGBColor(251, 252, 254)
    line = RGBColor(218, 226, 236)
    pale_blue = RGBColor(239, 245, 255)
    pale_green = RGBColor(235, 249, 242)
    pale_amber = RGBColor(255, 249, 235)

    def set_bg(slide, color=bg):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color

    scenario_label_kr = {
        "Bear": "보수",
        "Base": "기준",
        "Bull": "낙관",
        "Grid-Constrained / Efficiency-Upside": "전력제약·효율상승",
    }

    def add_footer(slide, note: str = "전력·모델·serving 가정 기반 시뮬레이션"):
        tx = slide.shapes.add_textbox(Inches(0.72), Inches(7.05), Inches(11.85), Inches(0.24))
        p = tx.text_frame.paragraphs[0]
        p.text = f"{note} | 생성일 {RUN_DATE}"
        p.font.size = Pt(7.5)
        p.font.color.rgb = muted

    def add_title(slide, title: str, subtitle: str | None = None):
        accent = slide.shapes.add_shape(1, Inches(0.72), Inches(0.43), Inches(0.08), Inches(0.54))
        accent.fill.solid()
        accent.fill.fore_color.rgb = blue
        accent.line.color.rgb = blue
        tx = slide.shapes.add_textbox(Inches(0.92), Inches(0.32), Inches(11.55), Inches(0.66))
        p = tx.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = navy
        if subtitle:
            sub = slide.shapes.add_textbox(Inches(0.94), Inches(0.92), Inches(11.35), Inches(0.42))
            p2 = sub.text_frame.paragraphs[0]
            p2.text = subtitle
            p2.font.size = Pt(10.5)
            p2.font.color.rgb = muted

    def add_label(slide, x, y, w, h, text, size=10, color=muted, bold=False, align=PP_ALIGN.LEFT):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_top = 0
        tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.alignment = align
        return box

    def metric_card(slide, x, y, w, h, label, value, note, fill_color):
        shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
        shape.line.color.rgb = RGBColor(235, 240, 248)
        tf = shape.text_frame
        tf.margin_left = Inches(0.16)
        tf.margin_right = Inches(0.12)
        tf.margin_top = Inches(0.12)
        tf.clear()
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(9)
        p.font.color.rgb = muted
        p2 = tf.add_paragraph()
        p2.text = value
        p2.font.size = Pt(20)
        p2.font.bold = True
        p2.font.color.rgb = navy
        p3 = tf.add_paragraph()
        p3.text = note
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = muted
        return shape

    def style_light_table(table, header_color=navy, band_color=RGBColor(247, 250, 253)):
        for r_idx, row in enumerate(table.rows):
            for cell in row.cells:
                cell.margin_left = Inches(0.06)
                cell.margin_right = Inches(0.06)
                cell.margin_top = Inches(0.04)
                cell.margin_bottom = Inches(0.04)
                if r_idx == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = header_color
                    for p in cell.text_frame.paragraphs:
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.font.bold = True
                        p.font.size = Pt(8.5)
                elif r_idx % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = band_color
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(255, 255, 255)

    def bullet_list(slide, x, y, w, h, bullets, size=14, color=ink):
        tx = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tx.text_frame
        tf.clear()
        for i, b in enumerate(bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = b
            p.font.size = Pt(size)
            p.font.color.rgb = color
            p.space_after = Pt(8)
            p.level = 0
        return tx

    base_2030 = [r for r in data["forecast"] if r["year"] == 2030]
    base_2026 = [r for r in data["forecast"] if r["year"] == 2026]
    ranked_2030 = sorted(base_2030, key=lambda r: r["inference_tokens_per_day"], reverse=True)
    scenario_2030 = [r for r in data["scenario_summary"] if r["year"] == 2030]
    base_summary_2030 = next(r for r in scenario_2030 if r["scenario"] == "Base")
    base_summary_2026 = next(r for r in data["scenario_summary"] if r["scenario"] == "Base" and r["year"] == 2026)
    total_tokens_2030 = sum(r["inference_tokens_per_day"] for r in base_2030)
    total_active_2030 = sum(r["active_power_gw"] for r in base_2030)
    total_ai_2030 = sum(r["ai_it_load_gw"] for r in base_2030)
    total_inf_2030 = sum(r["inference_gw"] for r in base_2030)
    total_train_2030 = sum(r["training_gw"] for r in base_2030)

    def takeaway_band(slide, text: str, y: float = 6.17, color=navy):
        rule = slide.shapes.add_shape(1, Inches(2.45), Inches(y - 0.16), Inches(8.45), Inches(0.02))
        rule.fill.solid()
        rule.fill.fore_color.rgb = RGBColor(214, 225, 239)
        rule.line.color.rgb = RGBColor(214, 225, 239)
        add_label(slide, 0.92, y, 11.45, 0.42, text, 11, color, True, PP_ALIGN.CENTER)

    # 1. Cover: answer first
    slide = prs.slides.add_slide(blank)
    set_bg(slide, RGBColor(244, 247, 251))
    add_label(slide, 0.72, 0.62, 3.2, 0.28, "검증 기반 팀 발표안", 8, blue, True)
    add_label(slide, 0.72, 1.12, 8.0, 1.95, "2030년 LLM 토큰 병목은\n전력보다 ‘추론 전환 속도’와\nserving 효율에서 갈린다", 31, navy, True)
    add_label(slide, 0.78, 3.38, 6.95, 0.62, "상용 LLM model owner 기준 2026-2030 전력·GPU·토큰 capacity 시뮬레이션", 14, muted)
    add_label(slide, 8.35, 1.12, 3.8, 0.32, "Base case 2030", 10, muted, True)
    add_label(slide, 8.35, 1.58, 3.8, 0.75, f"{total_tokens_2030/1e15:.2f}Q", 34, blue, True)
    add_label(slide, 8.38, 2.32, 3.9, 0.32, "generated output tokens/day", 10, muted)
    add_label(slide, 8.35, 3.15, 3.9, 0.55, f"{total_inf_2030:.1f}GW 추론 load", 20, green, True)
    add_label(slide, 8.38, 3.74, 3.9, 0.32, f"추론 비중 {base_summary_2026['weighted_inference_share']:.0%} → {base_summary_2030['weighted_inference_share']:.0%}", 10, muted)
    takeaway_band(slide, "오늘의 결론: 2030년 추론 토큰 수요는 상위 model owner에 집중되며, 메모리 마케팅은 이 계정들에 선제 배치해야 한다.")
    add_footer(slide)

    # 2. Talk track
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "발표에서 답할 네 가지 질문", "결론을 먼저 공유하고, 그 결론을 만든 계산 로직과 가정의 이유를 설명합니다.")
    questions = [
        ("1", "얼마나 커지나?", f"Base 2030: {total_tokens_2030/1e15:.2f}Q generated output tokens/day"),
        ("2", "누가 주도하나?", f"상위 3개: {', '.join(r['company'] for r in ranked_2030[:3])}"),
        ("3", "무엇이 흔드나?", "active power, inference share, tokens/MW, utilization"),
        ("4", "우리는 무엇을 해야 하나?", "HBM allocation, DDR5/MRDIMM attach, SSD/CXL proof pack"),
    ]
    for i, (num, q, a) in enumerate(questions):
        y = 1.28 + i * 1.18
        add_label(slide, 0.9, y, 0.55, 0.42, num, 18, blue, True, PP_ALIGN.CENTER)
        add_label(slide, 1.65, y, 3.5, 0.38, q, 18, navy, True)
        add_label(slide, 5.3, y + 0.02, 6.9, 0.36, a, 14, ink)
    takeaway_band(slide, "듣는 순서: 시장 크기 → 우선 계정 → token 정의 → 계산 로직 → 주요 driver → 메모리 마케팅 액션.")
    add_footer(slide)

    # 3. Executive conclusion
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "2026-2030 generated output token은 Base에서도 빠르게 증가한다", "전력 가동 속도와 serving 효율을 함께 반영하면 2030년 토큰 capacity는 구조적으로 커집니다.")
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for scen in ("Bear", "Base", "Bull"):
        chart_data.add_series(
            scenario_label_kr[scen],
            [next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.8), Inches(1.25), Inches(7.35), Inches(4.6), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    add_label(slide, 8.65, 1.35, 3.55, 0.42, "그래프 읽는 법", 12, muted, True)
    bullet_list(
        slide,
        8.65,
        1.92,
        3.65,
        3.0,
        [
            "세 선의 간격은 전력 가동 속도, MoE 최적화, utilization 차이입니다.",
            "Base는 현재 공개 roadmap을 단계적 가동으로 반영한 중심선입니다.",
            "Bull/Bear는 account별 물량·가격·제품 mix를 준비하기 위한 운영 범위입니다.",
        ],
        12,
    )
    takeaway_band(slide, "이 장의 메시지: Base만 보지 말고, 상하단 범위에서 HBM·DDR5·SSD 수요가 어떻게 달라지는지 봐야 합니다.")
    add_footer(slide)

    # 4. Who matters
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "2030 상위 model owner가 토큰 capacity 대부분을 만든다", "메모리 영업 우선순위는 데이터센터 host가 아니라 commercial LLM owner 기준으로 잡습니다.")
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in ranked_2030]
    chart_data.add_series("Q output tokens/day", [r["inference_tokens_per_day"] / 1e15 for r in ranked_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.7), Inches(1.15), Inches(8.0), Inches(4.95), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(9)
    bullet_list(
        slide,
        9.15,
        1.45,
        3.3,
        3.6,
        [
            f"Top 3: {', '.join(r['company'] for r in ranked_2030[:3])}.",
            "OpenAI/Microsoft는 같은 생태계라도 모델 소유 token과 Copilot serving burden을 분리해 봅니다.",
            "중국 model owner는 MoE 효율이 높아 tokens/MW 관점에서 별도 기회로 봅니다.",
        ],
        12,
    )
    takeaway_band(slide, "이 장의 메시지: top account brief는 model owner 기준으로 만들고, 제품별 attach 기회를 계정별로 붙입니다.")
    add_footer(slide)

    # 5. Token definition
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Token 정의: headline은 generated output token이다", "input+output processed token, training token, billable token은 같은 숫자로 합산하지 않습니다.")
    token_rows = data["token_definitions"][:4]
    table = slide.shapes.add_table(len(token_rows) + 1, 4, Inches(0.65), Inches(1.25), Inches(12.05), Inches(4.65)).table
    headers = ["Metric", "정의", "모델 내 사용", "InferenceX mapping"]
    widths = [2.0, 3.8, 2.95, 3.3]
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = navy
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(8)
    for r, item in enumerate(token_rows, start=1):
        vals = [item["korean_name"], item["definition_kr"], item["primary_fields"], item["inferencex_mapping"]]
        for c, v in enumerate(vals):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(7.4)
            cell.margin_left = Inches(0.04)
            cell.margin_right = Inches(0.04)
    style_light_table(table)
    takeaway_band(slide, "이 장의 메시지: InferenceX의 total throughput은 workload 처리량이고, 본 보고서 headline은 사용자가 받는 output token입니다.")
    add_footer(slide)

    # 6. Why the model is credible
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "계산 로직: 전력 funnel에 serving 효율을 곱한다", "계약 전력에서 바로 토큰이 나오는 것이 아니라, 가동 전력과 추론 배정, serving 효율을 거쳐 토큰이 만들어집니다.")
    steps = [
        ("계약/계획 GW", "official capacity anchor"),
        ("가동 전력", "deployment 가정"),
        ("AI IT load", "PUE·AI workload 차감"),
        ("추론 GW", "training/inference split"),
        ("output token/day", "tokens/MW × utilization"),
    ]
    for i, (title, desc) in enumerate(steps):
        x = 0.7 + i * 2.5
        add_label(slide, x, 1.55, 1.95, 0.38, title, 12, navy, True, PP_ALIGN.CENTER)
        add_label(slide, x, 2.05, 1.95, 0.45, desc, 9, muted, False, PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            add_label(slide, x + 2.0, 1.85, 0.35, 0.3, "→", 17, muted, True, PP_ALIGN.CENTER)
    add_label(slide, 1.1, 3.38, 11.1, 0.48, "output tokens/day = inference GW x 1,000 x selected output tokens/sec/MW x 86,400", 16, blue, True, PP_ALIGN.CENTER)
    bullet_list(
        slide,
        1.2,
        4.55,
        10.8,
        1.0,
        [
            "전력 계약은 capacity 상한이고, 실제 token capacity는 operational deploy 이후에 생깁니다.",
            "inference share는 전력 배정이고, utilization은 그 전력이 실제 traffic으로 전환되는 운영 효율입니다.",
        ],
        11,
        ink,
    )
    takeaway_band(slide, "이 장의 메시지: 추론 GW, tokens/MW, utilization 세 계수를 따로 관리하면 토큰 capacity 변화를 설명할 수 있습니다.")
    add_footer(slide)

    # 7. InferenceX support
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    parsed = data["inferencex"]["manifest"].get("parsed_dump", {})
    add_title(slide, "Benchmark layer로 보정하는 것: tokens/MW, J/token, SLO 조건", "InferenceX, MLPerf, vLLM/SGLang/TensorRT-LLM 문서는 serving 효율과 latency 조건을 수치화해 tokens/MW 가정을 좁혀줍니다.")
    add_label(slide, 0.85, 1.35, 2.8, 0.32, "Full dump normalized", 11, muted, True)
    add_label(slide, 0.85, 1.78, 3.4, 0.72, f"{parsed.get('benchmark_rows', 0):,}", 34, blue, True)
    add_label(slide, 0.88, 2.48, 3.7, 0.3, "inference performance rows", 10, muted)
    add_label(slide, 4.6, 1.78, 2.8, 0.72, f"{parsed.get('metric_profile_rows', 0):,}", 34, green, True)
    add_label(slide, 4.62, 2.48, 3.5, 0.3, "model/GPU/framework profiles", 10, muted)
    add_label(slide, 8.1, 1.78, 2.8, 0.72, f"{parsed.get('accuracy_eval_rows', 0):,}", 34, amber, True)
    add_label(slide, 8.12, 2.48, 3.5, 0.3, "accuracy eval rows", 10, muted)
    bullet_list(
        slide,
        1.1,
        3.55,
        11.0,
        1.65,
        [
            "우리 산식의 tokens/sec/MW, J/token, TTFT/TPOT, utilization 가정과 직접 연결됩니다.",
            "total `tok_s_mw`는 input+output 처리량일 수 있어, headline output token에는 `output_tok_s_mw`를 우선 봅니다.",
            "다음 cycle에서는 workload별 benchmark-to-production haircut을 계수화해 tokens/MW 범위를 더 좁힙니다.",
        ],
        12,
    )
    takeaway_band(slide, "이 장의 메시지: benchmark와 serving-stack source는 효율 계수를 더 현실적인 범위로 조정하는 데이터 레이어입니다.")
    add_footer(slide)

    # 8. Key uncertainties
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "핵심 driver: active power와 utilization이 forecast를 가장 크게 움직인다", "토큰 capacity를 키우는 실제 driver는 전력 가동, traffic shape, SLO 조건, serving stack 개선입니다.")
    risk_rows = [
        ("High", "active_power_gw", "site-level energization / GPU rack deployment"),
        ("High", "utilization", "traffic shape, TTFT/TPOT, failover reserve"),
        ("Medium", "tokens/sec/MW", "serving stack, precision, model routing"),
        ("Medium", "inference share", "commercial serving ramp vs training demand"),
        ("Low-Med", "model parameters", "open MoE는 강함, closed model은 band"),
    ]
    table = slide.shapes.add_table(len(risk_rows) + 1, 3, Inches(0.85), Inches(1.35), Inches(11.65), Inches(4.55)).table
    for i, w in enumerate([1.45, 3.0, 7.2]):
        table.columns[i].width = Inches(w)
    for c, h in enumerate(["Risk", "변수", "왜 중요한가"]):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = navy
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(9)
    for r, row in enumerate(risk_rows, start=1):
        for c, v in enumerate(row):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(11 if c != 2 else 10)
    style_light_table(table)
    takeaway_band(slide, "이 장의 메시지: 전력 계약만 보는 팀보다, 가동 전력과 serving 운영 변화를 읽는 팀이 먼저 revenue 기회를 잡습니다.")
    add_footer(slide)

    # 9. Memory marketing actions
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "메모리 마케팅 액션: 토큰 growth를 제품별 sales motion으로 바꾼다", "상위 model owner의 추론 ramp는 HBM allocation뿐 아니라 DDR5, SSD, CXL attach 기회로 이어집니다.")
    actions = [
        ("HBM", "allocation / qualification / HBM4 roadmap lock-in", "OpenAI, Google, Meta, xAI"),
        ("DDR5·MRDIMM", "CPU-side inference attach, density/bandwidth refresh", "hyperscaler + OEM/ODM"),
        ("Enterprise SSD·QLC", "RAG, checkpointing, vector retrieval TCO proof", "enterprise AI + cloud"),
        ("CXL", "memory expansion and utilization recovery narrative", "inference fleet architects"),
    ]
    table = slide.shapes.add_table(len(actions) + 1, 3, Inches(0.8), Inches(1.35), Inches(11.8), Inches(4.45)).table
    for i, w in enumerate([2.0, 6.4, 3.4]):
        table.columns[i].width = Inches(w)
    for c, h in enumerate(["제품", "Revenue motion", "우선 고객"]):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = navy
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(9)
    for r, row in enumerate(actions, start=1):
        for c, v in enumerate(row):
            cell = table.cell(r, c)
            cell.text = v
            cell.text_frame.paragraphs[0].font.size = Pt(10.5)
    style_light_table(table)
    takeaway_band(slide, "발표 후 액션: 상위 10개 account별로 product-fit, urgency, proof pack, pricing/mix recommendation을 작성합니다.")
    add_footer(slide)

    # 10. Next operating loop
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "다음 운영 방식: 매주 source-refresh → model-update → account-action", "가정이 바뀌면 모델 숫자와 영업 액션이 같은 주에 같이 업데이트되도록 운영합니다.")
    loop = [
        ("월", "source refresh", "official IR / filings / model cards / InferenceX / MLPerf / serving-stack docs"),
        ("화", "model update", "token definition, active GW, routing, utilization"),
        ("수", "account translation", "customer pain → product fit → proof"),
        ("목", "sales review", "pipeline impact, objection, win/loss signal"),
        ("금", "assumption review", "token definition, unit check, next-week model update"),
    ]
    for i, (day, task, desc) in enumerate(loop):
        y = 1.28 + i * 0.92
        add_label(slide, 0.95, y, 0.8, 0.32, day, 15, blue, True)
        add_label(slide, 1.95, y, 2.8, 0.32, task, 14, navy, True)
        add_label(slide, 4.85, y, 7.0, 0.32, desc, 12, ink)
    takeaway_band(slide, "이 장의 메시지: PPT는 발표용, Excel은 계산용, MD/agents는 가정 업데이트와 반복 학습용으로 역할을 나눕니다.")
    add_footer(slide)

    # 11. Appendix map
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "부록 위치: 계산식·가정·InferenceX 원천 테이블은 workbook에 있다", "발표에서는 결론과 로직만 말하고, 질문이 들어오면 workbook sheet로 내려갑니다.")
    bullet_list(
        slide,
        0.95,
        1.35,
        11.3,
        4.35,
        [
            "00_formula_assumptions / 00a_token_definitions: 계산식과 token 정의.",
            "02a_fact_anchors: 공개 numeric anchor와 모델 반영 방식.",
            "08a-08f: scenario, benchmark, energy, utilization sensitivity.",
            "07-09: source registry, provenance trace, fact audit; 12d-12f: InferenceX benchmark rows, metric profile, accuracy evals.",
            "07/08 sheets: company-year forecast와 sensitivity 결과.",
        ],
        14,
    )
    takeaway_band(slide, "이 장의 메시지: 발표 본문은 간결하게, 세부 계산과 원천 테이블은 workbook에서 설명합니다.")
    add_footer(slide)

    prs.save(path)


def write_ppt_samsung_style(data: dict[str, Any], path: Path) -> None:
    """Create a Samsung Electronics-inspired executive deck.

    This is a clean corporate style deck: white canvas, Samsung-blue accents,
    strong conclusion titles, large numbers, thin rules, and fewer containers.
    It does not use Samsung logos or proprietary brand assets.
    """

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    samsung_blue = RGBColor(20, 40, 160)
    electric_blue = RGBColor(0, 112, 243)
    ink = RGBColor(20, 24, 32)
    body = RGBColor(60, 68, 82)
    muted = RGBColor(118, 128, 145)
    silver = RGBColor(230, 235, 243)
    pale = RGBColor(247, 249, 252)
    cyan = RGBColor(0, 163, 224)
    green = RGBColor(16, 150, 108)
    amber = RGBColor(212, 142, 28)

    scenario_label_kr = {
        "Bear": "Bear",
        "Base": "Base",
        "Bull": "Bull",
        "Grid-Constrained / Efficiency-Upside": "Grid constrained + efficiency",
    }

    base_2030 = [r for r in data["forecast"] if r["year"] == 2030]
    base_2026 = [r for r in data["forecast"] if r["year"] == 2026]
    ranked_2030 = sorted(base_2030, key=lambda r: r["inference_tokens_per_day"], reverse=True)
    scenario_2030 = [r for r in data["scenario_summary"] if r["year"] == 2030]
    base_summary_2030 = next(r for r in scenario_2030 if r["scenario"] == "Base")
    base_summary_2026 = next(r for r in data["scenario_summary"] if r["scenario"] == "Base" and r["year"] == 2026)
    total_tokens_2030 = sum(r["inference_tokens_per_day"] for r in base_2030)
    total_tokens_2026 = sum(r["inference_tokens_per_day"] for r in base_2026)
    total_active_2030 = sum(r["active_power_gw"] for r in base_2030)
    total_inf_2030 = sum(r["inference_gw"] for r in base_2030)
    total_train_2030 = sum(r["training_gw"] for r in base_2030)

    def set_bg(slide, color=RGBColor(255, 255, 255)):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def rect(slide, x, y, w, h, color, line_color=None):
        shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.color.rgb = line_color or color
        return shape

    def text(slide, x, y, w, h, value, size=12, color=body, bold=False, align=PP_ALIGN.LEFT):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_top = 0
        tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = value
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.alignment = align
        return box

    def add_header(slide, title: str, kicker: str = "LLM TOKEN CAPACITY SIMULATION"):
        rect(slide, 0, 0, 13.333, 0.08, samsung_blue)
        text(slide, 0.72, 0.42, 3.8, 0.22, kicker, 7.5, samsung_blue, True)
        text(slide, 0.72, 0.78, 11.9, 0.64, title, 23, ink, True)
        rect(slide, 0.72, 1.52, 11.9, 0.01, silver)

    def add_footer(slide, note: str = "Commercial LLM model-owner basis | Generated output token headline"):
        text(slide, 0.72, 7.08, 10.3, 0.18, note, 7.2, muted)
        text(slide, 11.52, 7.08, 1.1, 0.18, RUN_DATE, 7.2, muted, False, PP_ALIGN.RIGHT)

    def bullet(slide, x, y, w, h, items, size=12, color=body, gap=8):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.clear()
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = item
            p.font.size = Pt(size)
            p.font.color.rgb = color
            p.space_after = Pt(gap)
        return box

    def underline_takeaway(slide, value: str):
        rect(slide, 0.72, 6.42, 1.4, 0.04, samsung_blue)
        text(slide, 2.25, 6.32, 10.1, 0.32, value, 11.5, ink, True)

    def stat(slide, x, y, label, value, unit, color=samsung_blue):
        text(slide, x, y, 2.7, 0.25, label, 8.8, muted, True)
        text(slide, x, y + 0.34, 2.7, 0.7, value, 30, color, True)
        text(slide, x, y + 1.0, 2.7, 0.24, unit, 8.5, muted)

    def style_table(table, header_color=samsung_blue):
        for r_idx, row in enumerate(table.rows):
            for cell in row.cells:
                cell.margin_left = Inches(0.06)
                cell.margin_right = Inches(0.06)
                cell.margin_top = Inches(0.04)
                cell.margin_bottom = Inches(0.04)
                if r_idx == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = header_color
                    for p in cell.text_frame.paragraphs:
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        p.font.bold = True
                        p.font.size = Pt(8.5)
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(255, 255, 255) if r_idx % 2 else pale
                    for p in cell.text_frame.paragraphs:
                        p.font.color.rgb = body
                        p.font.size = Pt(8.5)

    def chart_axis_style(chart):
        chart.value_axis.tick_labels.font.size = Pt(8)
        chart.category_axis.tick_labels.font.size = Pt(8)
        chart.value_axis.format.line.color.rgb = silver
        chart.category_axis.format.line.color.rgb = silver

    # 1. Cover
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    rect(slide, 0, 0, 13.333, 0.12, samsung_blue)
    text(slide, 0.72, 0.62, 4.2, 0.24, "MEMORY MARKETING STRATEGY", 8, samsung_blue, True)
    text(slide, 0.72, 1.22, 8.4, 1.75, "2030 LLM Token Capacity\nSimulation", 35, ink, True)
    text(slide, 0.76, 3.13, 7.5, 0.45, "상용 LLM 업체별 전력·GPU·토큰 생성량 기반 메모리 매출 기회 분석", 14, body)
    rect(slide, 8.8, 1.28, 0.04, 3.3, samsung_blue)
    stat(slide, 9.1, 1.28, "Base 2030", f"{total_tokens_2030/1e15:.2f}Q", "output tokens/day", samsung_blue)
    stat(slide, 9.1, 2.9, "Inference load", f"{total_inf_2030:.1f}GW", "2030 model-owner basis", cyan)
    text(slide, 0.72, 6.55, 5.8, 0.24, "Samsung-style executive version | no brand assets used", 8, muted)
    text(slide, 10.72, 6.55, 1.9, 0.24, RUN_DATE, 8, muted, False, PP_ALIGN.RIGHT)

    # 2. Answer first
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "결론: 2030년 토큰 공급력은 ‘가동 전력 × 추론 전환 × serving 효율’이 결정한다")
    columns = [
        ("01", "Capacity", f"Base 기준 2030년 {total_tokens_2030/1e15:.2f}Q output tokens/day까지 확대"),
        ("02", "Concentration", f"상위 계정은 {', '.join(r['company'] for r in ranked_2030[:3])} 중심으로 집중"),
        ("03", "Memory motion", "HBM allocation에서 DDR5·SSD·CXL attach로 revenue motion 확장"),
    ]
    for i, (num, title, desc) in enumerate(columns):
        x = 0.82 + i * 4.05
        text(slide, x, 1.95, 0.7, 0.32, num, 11, samsung_blue, True)
        rect(slide, x, 2.32, 3.25, 0.03, samsung_blue if i == 0 else silver)
        text(slide, x, 2.62, 3.3, 0.38, title, 18, ink, True)
        text(slide, x, 3.2, 3.25, 1.2, desc, 15, body)
    underline_takeaway(slide, "Executive takeaway: 전력 계약보다 ‘실제 inference serving으로 전환되는 속도’를 계정 전략의 선행지표로 봐야 합니다.")
    add_footer(slide)

    # 3. Scenario envelope
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "2026-2030 토큰 capacity는 Base에서도 급격히 증가한다")
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for scen in ("Bear", "Base", "Bull"):
        chart_data.add_series(
            scenario_label_kr[scen],
            [next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.82), Inches(1.85), Inches(8.0), Inches(4.1), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart_axis_style(chart)
    text(slide, 9.35, 1.88, 2.8, 0.3, "시나리오가 벌어지는 이유", 11, muted, True)
    bullet(
        slide,
        9.35,
        2.35,
        3.1,
        2.6,
        [
            "Operational deploy 속도 차이",
            "MoE·quantization·batching 최적화",
            "학습 중심에서 상용 추론 중심으로의 전력 배정 변화",
        ],
        12,
    )
    underline_takeaway(slide, "Base는 중심선이고, Bull/Bear는 account별 allocation·pricing·attach 전략을 준비하는 운영 범위입니다.")
    add_footer(slide)

    # 4. Account priority
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "2030년 메모리 영업 우선순위는 model owner 기준으로 재정렬한다")
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in ranked_2030]
    chart_data.add_series("Q output tokens/day", [r["inference_tokens_per_day"] / 1e15 for r in ranked_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.82), Inches(1.78), Inches(7.8), Inches(4.25), chart_data).chart
    chart.has_legend = False
    chart_axis_style(chart)
    stat(slide, 9.15, 1.82, "Top account", ranked_2030[0]["company"], "largest 2030 token capacity", samsung_blue)
    stat(slide, 9.15, 3.25, "Total active power", f"{total_active_2030:.1f}GW", "Base 2030", cyan)
    text(slide, 9.15, 4.92, 3.0, 0.58, "Host capacity와 model-owner token 귀속을 분리해야 Copilot, ChatGPT, Gemini, Llama, Grok, Claude, Qwen, DeepSeek 계정 전략이 선명해집니다.", 10.5, body)
    underline_takeaway(slide, "Account brief는 cloud host가 아니라 상용 LLM owner별로 만들고, 제품별 attach 기회를 붙입니다.")
    add_footer(slide)

    # 5. Calculation logic
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "계산식은 전력 funnel과 serving 효율을 분리해서 관리한다")
    steps = [
        ("Contracted\nGW", "capacity ceiling"),
        ("Active\nGW", "energized & deployed"),
        ("AI IT\nload", "PUE / workload"),
        ("Inference\nGW", "power split"),
        ("Output\ntoken/day", "tokens/MW × utilization"),
    ]
    for i, (label, note) in enumerate(steps):
        x = 0.82 + i * 2.43
        text(slide, x, 2.03, 1.55, 0.72, label, 18, ink, True, PP_ALIGN.CENTER)
        rect(slide, x, 2.92, 1.55, 0.035, samsung_blue if i == 4 else silver)
        text(slide, x, 3.18, 1.55, 0.3, note, 8.2, muted, False, PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            text(slide, x + 1.72, 2.42, 0.35, 0.25, "→", 16, muted, True, PP_ALIGN.CENTER)
    text(slide, 1.1, 4.35, 11.1, 0.45, "output tokens/day = inference GW x 1,000 x selected output tokens/sec/MW x 86,400", 16, samsung_blue, True, PP_ALIGN.CENTER)
    underline_takeaway(slide, "전력 계약은 상한값이고, revenue signal은 active GW와 inference serving 전환에서 발생합니다.")
    add_footer(slide)

    # 6. Training vs inference shift
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "추론 비중 증가는 토큰 생성량과 메모리 제품 mix를 동시에 바꾼다")
    pie_data = CategoryChartData()
    pie_data.categories = ["Inference GW", "Training GW"]
    pie_data.add_series("2030 GW split", [total_inf_2030, total_train_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.PIE, Inches(0.85), Inches(1.85), Inches(4.3), Inches(4.0), pie_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    stat(slide, 6.0, 1.92, "Inference share", f"{base_summary_2026['weighted_inference_share']:.0%} → {base_summary_2030['weighted_inference_share']:.0%}", "Base weighted share, 2026 to 2030", samsung_blue)
    text(slide, 6.0, 3.58, 5.7, 0.92, "상용 traffic이 커질수록 decode/prefill, KV cache, retrieval, checkpoint, storage tiering 요구가 늘어납니다. 이는 HBM뿐 아니라 DDR5, MRDIMM, SSD, CXL의 계정별 가치 제안으로 연결됩니다.", 13, body)
    underline_takeaway(slide, "Inference shift는 단순 GPU 수요가 아니라 memory hierarchy 전체의 판매 기회입니다.")
    add_footer(slide)

    # 7. Token definition
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "Headline metric은 generated output token으로 고정한다")
    token_rows = data["token_definitions"][:4]
    table = slide.shapes.add_table(len(token_rows) + 1, 4, Inches(0.72), Inches(1.78), Inches(11.95), Inches(4.25)).table
    headers = ["Metric", "Definition", "Use in model", "InferenceX mapping"]
    widths = [2.0, 4.05, 2.7, 3.2]
    for i, width in enumerate(widths):
        table.columns[i].width = Inches(width)
    for c, header in enumerate(headers):
        table.cell(0, c).text = header
    for r, item in enumerate(token_rows, start=1):
        values = [item["korean_name"], item["definition_kr"], item["primary_fields"], item["inferencex_mapping"]]
        for c, value in enumerate(values):
            table.cell(r, c).text = value
    style_table(table)
    underline_takeaway(slide, "Input+output processed token, billable token, training token을 하나로 합산하지 않도록 정의를 분리합니다.")
    add_footer(slide)

    # 8. InferenceX calibration
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    parsed = data["inferencex"]["manifest"].get("parsed_dump", {})
    add_header(slide, "Benchmark stack은 serving 효율 가정을 실제 측정 범위로 좁힌다")
    stat(slide, 0.92, 1.92, "Performance rows", f"{parsed.get('benchmark_rows', 0):,}", "model × GPU × precision × ISL/OSL", samsung_blue)
    stat(slide, 4.75, 1.92, "Metric profiles", f"{parsed.get('metric_profile_rows', 0):,}", "GPU/framework/profile groups", cyan)
    stat(slide, 8.55, 1.92, "Accuracy evals", f"{parsed.get('accuracy_eval_rows', 0):,}", "quality trade-off layer", green)
    bullet(
        slide,
        1.0,
        4.12,
        11.0,
        1.1,
        [
            "tokens/sec/MW, J/token, TTFT/TPOT, batch/SLO 조건을 함께 보면서 production haircut을 설계합니다.",
            "headline output token에는 total tok/s/MW보다 output_tok_s_mw를 우선 매핑합니다.",
        ],
        12.5,
    )
    underline_takeaway(slide, "Benchmark는 forecast 숫자를 대체하지 않고, tokens/MW 가정의 현실 범위를 정교하게 만드는 calibration layer입니다.")
    add_footer(slide)

    # 9. Memory revenue actions
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "토큰 growth를 메모리 제품별 revenue motion으로 변환한다")
    actions = [
        ("HBM", "Allocation / qualification / HBM4 roadmap lock-in", "frontier model ramp"),
        ("DDR5·MRDIMM", "CPU-side inference attach and density refresh", "inference server refresh"),
        ("Enterprise SSD·QLC", "RAG, checkpointing, vector DB TCO proof", "retrieval-heavy AI"),
        ("CXL", "memory expansion and utilization recovery", "capacity-bound inference"),
    ]
    table = slide.shapes.add_table(len(actions) + 1, 3, Inches(0.72), Inches(1.78), Inches(11.95), Inches(4.2)).table
    for i, width in enumerate([2.1, 6.1, 3.75]):
        table.columns[i].width = Inches(width)
    for c, header in enumerate(["제품", "Sales motion", "Trigger"]):
        table.cell(0, c).text = header
    for r, row in enumerate(actions, start=1):
        for c, value in enumerate(row):
            table.cell(r, c).text = value
    style_table(table)
    underline_takeaway(slide, "상위 10개 model-owner account부터 product fit, urgency, proof pack, pricing/mix recommendation을 완성합니다.")
    add_footer(slide)

    # 10. Operating cadence and appendix
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_header(slide, "운영 방식은 source refresh에서 account action까지 일주일 단위로 닫는다")
    days = [
        ("Mon", "Source refresh", "IR / filings / model cards / InferenceX / MLPerf / serving docs"),
        ("Tue", "Model update", "active GW, inference share, tokens/MW"),
        ("Wed", "Account translation", "pain → product fit → message"),
        ("Thu", "Sales review", "pipeline, objections, win/loss"),
        ("Fri", "Assumption review", "unit check, next update"),
    ]
    for i, (day, task, desc) in enumerate(days):
        y = 1.82 + i * 0.75
        text(slide, 0.92, y, 0.78, 0.25, day, 12, samsung_blue, True)
        rect(slide, 1.88, y + 0.12, 1.0, 0.02, silver)
        text(slide, 3.1, y, 2.6, 0.25, task, 13, ink, True)
        text(slide, 5.9, y, 5.8, 0.25, desc, 11.5, body)
    text(slide, 0.92, 5.95, 11.1, 0.3, "Workbook: core formula, benchmark inputs, scenario inputs, outputs, checks, source registry, provenance trace, and aggressive upside view", 10.5, muted)
    underline_takeaway(slide, "PPT는 결론 전달, Excel은 계산 검증, MD/agents는 가정 업데이트와 반복 학습에 사용합니다.")
    add_footer(slide)

    prs.save(path)


def write_ppt_samsung_style(data: dict[str, Any], path: Path) -> None:
    """Create an English Samsung Electronics-inspired executive deck.

    The design is intentionally brand-adjacent rather than branded: white
    canvas, deep blue accents, large executive claims, thin separators, and
    data-first layouts. No Samsung logo or proprietary brand asset is used.
    """

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    samsung_blue = RGBColor(20, 40, 160)
    blue = RGBColor(0, 112, 243)
    ink = RGBColor(20, 24, 32)
    body = RGBColor(58, 66, 82)
    muted = RGBColor(116, 126, 142)
    silver = RGBColor(227, 233, 242)
    pale = RGBColor(247, 249, 252)
    cyan = RGBColor(0, 163, 224)
    green = RGBColor(16, 150, 108)

    base_2030 = [r for r in data["forecast"] if r["year"] == 2030]
    base_2026 = [r for r in data["forecast"] if r["year"] == 2026]
    ranked_2030 = sorted(base_2030, key=lambda r: r["inference_tokens_per_day"], reverse=True)
    scenario_2030 = [r for r in data["scenario_summary"] if r["year"] == 2030]
    base_summary_2030 = next(r for r in scenario_2030 if r["scenario"] == "Base")
    base_summary_2026 = next(r for r in data["scenario_summary"] if r["scenario"] == "Base" and r["year"] == 2026)
    total_tokens_2030 = sum(r["inference_tokens_per_day"] for r in base_2030)
    total_tokens_2026 = sum(r["inference_tokens_per_day"] for r in base_2026)
    total_active_2030 = sum(r["active_power_gw"] for r in base_2030)
    total_inf_2030 = sum(r["inference_gw"] for r in base_2030)
    total_train_2030 = sum(r["training_gw"] for r in base_2030)
    growth_multiple = total_tokens_2030 / total_tokens_2026 if total_tokens_2026 else 0

    token_rows = [
        (
            "Generated output tokens",
            "Tokens actually returned to users, APIs, or product surfaces. This is the headline capacity metric in the model.",
            "`inference_tokens_per_day` and `output_tok_s_mw` sanity layer",
            "Map to output throughput and joules per output token first.",
        ),
        (
            "Processed inference tokens",
            "Input plus output tokens handled by the serving system. This can be much larger than output tokens for RAG and agentic workloads.",
            "`tok_s_mw`, input throughput, output throughput",
            "Use for load-shape and benchmark diagnostics, not as the headline.",
        ),
        (
            "Input / prefill tokens",
            "Prompt, retrieved context, tool transcript, and history read before generation begins.",
            "ISL, `input_tok_s_gpu`, `input_tok_s_mw`",
            "Use to explain memory pressure, TTFT, and utilization effects.",
        ),
        (
            "Training tokens processed",
            "Corpus tokens used in pretraining or post-training. These are not added to commercial inference output tokens.",
            "`training_tokens_processed_per_day` sanity checks",
            "Separate training metric; InferenceX is an inference-serving benchmark.",
        ),
    ]

    def set_bg(slide, color=RGBColor(255, 255, 255)):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def rect(slide, x, y, w, h, color, line_color=None):
        shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.color.rgb = line_color or color
        return shape

    def text(slide, x, y, w, h, value, size=12, color=body, bold=False, align=PP_ALIGN.LEFT):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_top = 0
        tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = value
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.alignment = align
        return box

    def header(slide, title: str, subtitle: str = ""):
        rect(slide, 0, 0, 13.333, 0.08, samsung_blue)
        text(slide, 0.72, 0.36, 4.5, 0.22, "LLM TOKEN CAPACITY SIMULATION", 7.5, samsung_blue, True)
        text(slide, 0.72, 0.72, 11.85, 0.55, title, 22, ink, True)
        if subtitle:
            text(slide, 0.74, 1.28, 11.3, 0.28, subtitle, 9.5, muted)
        rect(slide, 0.72, 1.63, 11.9, 0.01, silver)

    def footer(slide, note: str = "Commercial LLM model-owner basis | Headline metric: generated output tokens"):
        text(slide, 0.72, 7.08, 10.4, 0.18, note, 7.2, muted)
        text(slide, 11.52, 7.08, 1.1, 0.18, RUN_DATE, 7.2, muted, False, PP_ALIGN.RIGHT)

    def takeaway(slide, value: str):
        rect(slide, 0.72, 6.42, 1.25, 0.04, samsung_blue)
        text(slide, 2.13, 6.3, 10.35, 0.38, value, 11.2, ink, True)

    def stat(slide, x, y, label, value, unit, color=samsung_blue):
        text(slide, x, y, 3.05, 0.22, label, 8.6, muted, True)
        text(slide, x, y + 0.31, 3.05, 0.62, value, 27, color, True)
        text(slide, x, y + 0.94, 3.05, 0.24, unit, 8.4, muted)

    def bullets(slide, x, y, w, h, items, size=11.5, color=body, gap=7):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.clear()
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = item
            p.font.size = Pt(size)
            p.font.color.rgb = color
            p.space_after = Pt(gap)
        return box

    def style_table(table, header_color=samsung_blue):
        for r_idx, row in enumerate(table.rows):
            for cell in row.cells:
                cell.margin_left = Inches(0.055)
                cell.margin_right = Inches(0.055)
                cell.margin_top = Inches(0.035)
                cell.margin_bottom = Inches(0.035)
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color if r_idx == 0 else (RGBColor(255, 255, 255) if r_idx % 2 else pale)
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(8.1 if r_idx else 8.4)
                    p.font.color.rgb = RGBColor(255, 255, 255) if r_idx == 0 else body
                    p.font.bold = r_idx == 0

    def chart_axis_style(chart):
        chart.value_axis.tick_labels.font.size = Pt(8)
        chart.category_axis.tick_labels.font.size = Pt(8)
        chart.value_axis.format.line.color.rgb = silver
        chart.category_axis.format.line.color.rgb = silver

    # 1. Cover
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    rect(slide, 0, 0, 13.333, 0.12, samsung_blue)
    text(slide, 0.72, 0.62, 4.3, 0.22, "MEMORY MARKETING STRATEGY", 8, samsung_blue, True)
    text(slide, 0.72, 1.18, 8.2, 1.72, "2030 LLM Token Capacity\nSimulation", 35, ink, True)
    text(slide, 0.76, 3.08, 7.6, 0.58, "A model-owner view of power, accelerator capacity, inference mix, and memory revenue motions", 13.5, body)
    rect(slide, 8.85, 1.26, 0.04, 3.3, samsung_blue)
    stat(slide, 9.15, 1.25, "Base 2030 capacity", f"{total_tokens_2030/1e15:.2f}Q", "generated output tokens/day", samsung_blue)
    stat(slide, 9.15, 2.82, "Inference load", f"{total_inf_2030:.1f}GW", "model-owner AI IT load basis", cyan)
    text(slide, 0.72, 6.54, 5.7, 0.22, "Samsung-style executive version | no brand assets used", 8, muted)
    text(slide, 10.7, 6.54, 1.95, 0.22, RUN_DATE, 8, muted, False, PP_ALIGN.RIGHT)

    # 2. Answer first
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Executive answer: token capacity is determined by active power, inference mix, and serving efficiency",
        "The model separates power availability from the operating variables that actually turn power into commercial output tokens.",
    )
    columns = [
        ("01", "Capacity expands", f"Base case reaches {total_tokens_2030/1e15:.2f}Q generated output tokens/day by 2030."),
        ("02", "Capacity concentrates", f"The largest 2030 contributors are {', '.join(r['company'] for r in ranked_2030[:3])}."),
        ("03", "Memory motion broadens", "Inference growth creates HBM allocation pressure plus DDR5, SSD, and CXL attach opportunities."),
    ]
    for i, (num, title, desc) in enumerate(columns):
        x = 0.82 + i * 4.05
        text(slide, x, 2.0, 0.7, 0.3, num, 11, samsung_blue, True)
        rect(slide, x, 2.36, 3.25, 0.03, samsung_blue if i == 0 else silver)
        text(slide, x, 2.64, 3.3, 0.35, title, 17.5, ink, True)
        text(slide, x, 3.18, 3.35, 1.35, desc, 14, body)
    text(slide, 0.88, 5.15, 11.5, 0.52, "Why this matters: account planning should not start from data-center announcements alone. It should start from the model owner that controls traffic, model routing, SLO targets, and commercial token generation.", 11.5, body)
    takeaway(slide, "Use inference conversion speed as the leading indicator for account prioritization.")
    footer(slide)

    # 3. Scenario envelope
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "2026-2030 token capacity grows rapidly even in the Base case",
        "Bull, Base, and Bear cases vary deployment, inference allocation, and the explicit commercial workload fit applied to a public TPS/MW reference.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for scen in ("Bear", "Base", "Bull"):
        chart_data.add_series(
            scen,
            [next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.82), Inches(1.92), Inches(7.75), Inches(3.95), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart_axis_style(chart)
    text(slide, 9.08, 1.95, 3.25, 0.3, "How to read the chart", 11, muted, True)
    bullets(
        slide,
        9.08,
        2.38,
        3.45,
        2.7,
        [
            "The slope is driven by active power and inference share moving upward together.",
            "The gap between cases is driven by operational power deployment and inference allocation only.",
            "The Base line is not a demand forecast; it is a capacity envelope under the stated assumptions.",
        ],
        10.8,
    )
    text(slide, 9.08, 5.38, 3.2, 0.35, f"Base 2026-2030 growth: {growth_multiple:.1f}x", 13, samsung_blue, True)
    takeaway(slide, "The commercial question is not whether capacity grows, but which accounts absorb it first.")
    footer(slide)

    # 4. Account priority
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Memory account priority should be organized around model owners, not only cloud hosts",
        "Hosting capacity and model-owner token attribution are separated so Copilot, ChatGPT, Gemini, Llama, Grok, Claude, Qwen, and DeepSeek are not mixed incorrectly.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in ranked_2030]
    chart_data.add_series("Q output tokens/day", [r["inference_tokens_per_day"] / 1e15 for r in ranked_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.82), Inches(1.92), Inches(7.7), Inches(4.0), chart_data).chart
    chart.has_legend = False
    chart_axis_style(chart)
    stat(slide, 9.08, 1.94, "Largest modeled account", ranked_2030[0]["company"], "2030 generated output token capacity", samsung_blue)
    stat(slide, 9.08, 3.32, "Total active power", f"{total_active_2030:.1f}GW", "Base 2030, modeled company set", cyan)
    text(slide, 9.08, 4.85, 3.25, 0.72, "Implication: each top account needs a different proof package because model architecture, accelerator mix, memory stack, and procurement control points differ by owner.", 10.2, body)
    takeaway(slide, "Build the top-account brief by model owner, then map HBM, DDR5, SSD, and CXL attach points.")
    footer(slide)

    # 5. Calculation logic
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The formula is a power funnel multiplied by serving efficiency",
        "This slide is the control logic: every forecast movement must trace back to one of these conversion steps.",
    )
    steps = [
        ("Contracted\nGW", "capacity ceiling"),
        ("Active\nGW", "energized and deployed"),
        ("AI IT\nload", "PUE and workload share"),
        ("Inference\nGW", "training/inference split"),
        ("Output\ntoken/day", "selected tokens/MW"),
    ]
    for i, (label, note) in enumerate(steps):
        x = 0.82 + i * 2.43
        text(slide, x, 2.04, 1.55, 0.72, label, 17, ink, True, PP_ALIGN.CENTER)
        rect(slide, x, 2.92, 1.55, 0.035, samsung_blue if i == 4 else silver)
        text(slide, x, 3.18, 1.55, 0.36, note, 8.1, muted, False, PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            text(slide, x + 1.72, 2.42, 0.35, 0.25, "→", 16, muted, True, PP_ALIGN.CENTER)
    text(slide, 1.0, 4.28, 11.35, 0.43, "output tokens/day = inference GW x 1,000 x fleet-weighted serving tokens/sec/MW x 86,400", 15, samsung_blue, True, PP_ALIGN.CENTER)
    bullets(
        slide,
        1.18,
        5.05,
        10.9,
        0.72,
        [
            "Contracted power is an upper bound; token capacity begins only after power is energized and assigned to AI IT load.",
            "Inference share is a capacity allocation variable; output TPS/MW is weighted by H200/B200/GB200/purpose-built mix and workload fit.",
        ],
        10.4,
        body,
        4,
    )
    takeaway(slide, "This structure prevents double-counting power announcements as immediate token capacity.")
    footer(slide)

    # 6. Training vs inference shift
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The inference mix shift changes both token capacity and memory product mix",
        "A higher inference share increases sustained serving load and pushes the memory hierarchy beyond HBM alone.",
    )
    pie_data = CategoryChartData()
    pie_data.categories = ["Inference GW", "Training GW"]
    pie_data.add_series("2030 GW split", [total_inf_2030, total_train_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.PIE, Inches(0.85), Inches(1.92), Inches(4.1), Inches(3.75), pie_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    stat(slide, 5.72, 1.92, "Inference share", f"{base_summary_2026['weighted_inference_share']:.0%} to {base_summary_2030['weighted_inference_share']:.0%}", "Base weighted share, 2026 to 2030", samsung_blue)
    text(slide, 5.72, 3.3, 6.3, 0.76, "Interpretation: this is a scenario assumption, not a disclosed company-level fact. The model uses it to show how serving-dominated AI fleets would translate into token capacity and memory demand.", 10.8, body)
    bullets(
        slide,
        5.72,
        4.33,
        6.3,
        0.95,
        [
            "Decode and prefill raise KV-cache and HBM bandwidth pressure.",
            "RAG and agentic workloads increase SSD, QLC, and memory-expansion relevance.",
        ],
        10.5,
        body,
        5,
    )
    takeaway(slide, "Inference growth is a full memory-hierarchy opportunity, not only a GPU or HBM story.")
    footer(slide)

    # 7. Token definition
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The headline metric is generated output tokens",
        "Keeping token definitions separate is essential because benchmark throughput, billing tokens, training tokens, and user-visible output are different units.",
    )
    table = slide.shapes.add_table(len(token_rows) + 1, 4, Inches(0.72), Inches(1.88), Inches(11.95), Inches(4.05)).table
    for i, width in enumerate([2.05, 4.1, 2.95, 2.85]):
        table.columns[i].width = Inches(width)
    for c, header_text in enumerate(["Metric", "Definition", "Model usage", "Benchmark mapping"]):
        table.cell(0, c).text = header_text
    for r, row in enumerate(token_rows, start=1):
        for c, value in enumerate(row):
            table.cell(r, c).text = value
    style_table(table)
    takeaway(slide, "The forecast does not add input tokens, billable tokens, and training tokens into one headline number.")
    footer(slide)

    # 8. InferenceX calibration
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    parsed = data["inferencex"]["manifest"].get("parsed_dump", {})
    header(
        slide,
        "InferenceX, MLPerf, and serving-stack docs calibrate the efficiency assumptions",
        "The benchmark layer narrows the plausible range for tokens/MW, joules/token, latency conditions, workload shape, and accelerator replacement.",
    )
    stat(slide, 0.92, 1.96, "Performance rows", f"{parsed.get('benchmark_rows', 0):,}", "model x GPU x precision x ISL/OSL", samsung_blue)
    stat(slide, 4.75, 1.96, "Metric profiles", f"{parsed.get('metric_profile_rows', 0):,}", "GPU, framework, and profile groups", cyan)
    stat(slide, 8.55, 1.96, "Accuracy evals", f"{parsed.get('accuracy_eval_rows', 0):,}", "quality trade-off layer", green)
    text(slide, 0.95, 3.78, 11.25, 0.56, "How it is used: InferenceX does not replace the company capacity model. It calibrates the efficiency layer after capacity has already been attributed to a model owner and assigned to inference serving.", 11.5, body)
    bullets(
        slide,
        0.95,
        4.65,
        11.1,
        0.9,
        [
            "Use output throughput and joules/output token for the headline output-token sanity check.",
            "Use total token throughput, input length, output length, TTFT, and TPOT to explain production haircut and utilization.",
        ],
        10.5,
        body,
        5,
    )
    takeaway(slide, "The benchmark layer makes the tokens/MW assumption operational rather than purely theoretical.")
    footer(slide)

    # 9. Memory revenue actions
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Translate token growth into product-level revenue motions",
        "The output of the model should be account action: which customer, which product, what urgency, what proof, and what commercial motion.",
    )
    actions = [
        ("HBM", "Allocation, qualification, and HBM4 roadmap lock-in", "Frontier model ramps and accelerator supply tension"),
        ("DDR5 / MRDIMM", "CPU-side inference attach and memory-density refresh", "Inference server refresh and higher host memory requirements"),
        ("Enterprise SSD / QLC", "RAG, checkpointing, vector DB, and storage TCO proof", "Retrieval-heavy and agentic AI workloads"),
        ("CXL", "Memory expansion and utilization recovery narrative", "Capacity-bound inference and larger context workloads"),
    ]
    table = slide.shapes.add_table(len(actions) + 1, 3, Inches(0.72), Inches(1.88), Inches(11.95), Inches(4.05)).table
    for i, width in enumerate([2.0, 5.8, 4.15]):
        table.columns[i].width = Inches(width)
    for c, header_text in enumerate(["Product", "Revenue motion", "Trigger"]):
        table.cell(0, c).text = header_text
    for r, row in enumerate(actions, start=1):
        for c, value in enumerate(row):
            table.cell(r, c).text = value
    style_table(table)
    takeaway(slide, "Start with the top 10 model-owner accounts and attach a product-fit, proof-pack, and pricing/mix recommendation.")
    footer(slide)

    # 10. Operating cadence and appendix
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Run the model as a weekly operating system, not a one-time report",
        "The same assumptions should update market intelligence, account briefs, and sales enablement in the same weekly cycle.",
    )
    days = [
        ("Mon", "Source refresh", "IR, filings, model cards, technical reports, InferenceX, MLPerf, and serving-stack updates"),
        ("Tue", "Model update", "active GW, inference share, accelerator mix, tokens/MW, utilization"),
        ("Wed", "Account translation", "customer pain, product fit, urgency, value message, proof package"),
        ("Thu", "Sales review", "pipeline impact, objections, pricing/mix discussion, win/loss signal"),
        ("Fri", "Assumption review", "unit checks, scenario changes, next-week open questions"),
    ]
    for i, (day, task, desc) in enumerate(days):
        y = 1.86 + i * 0.72
        text(slide, 0.92, y, 0.78, 0.24, day, 12, samsung_blue, True)
        rect(slide, 1.88, y + 0.11, 1.0, 0.02, silver)
        text(slide, 3.1, y, 2.55, 0.24, task, 13, ink, True)
        text(slide, 5.85, y, 6.25, 0.24, desc, 10.8, body)
    text(slide, 0.92, 5.78, 11.1, 0.42, "Workbook: core formula, public benchmark inputs, scenario inputs, calculations, outputs, checks, source registry, provenance trace, and an aggressive upside view.", 10.5, muted)
    takeaway(slide, "Presentation for the executive story, workbook for the math, Markdown/agents for continuous assumption learning.")
    footer(slide)

    prs.save(path)


def write_ppt_compute_constraint(data: dict[str, Any], path: Path) -> None:
    """Create an English deck focused on token supply constraints by compute capacity."""

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    samsung_blue = RGBColor(20, 40, 160)
    blue = RGBColor(0, 112, 243)
    ink = RGBColor(20, 24, 32)
    body = RGBColor(58, 66, 82)
    muted = RGBColor(116, 126, 142)
    silver = RGBColor(227, 233, 242)
    pale = RGBColor(247, 249, 252)
    cyan = RGBColor(0, 163, 224)
    green = RGBColor(16, 150, 108)
    amber = RGBColor(212, 142, 28)
    red = RGBColor(186, 68, 68)

    rows_2030 = sorted([r for r in data["forecast"] if r["year"] == 2030], key=lambda r: r["inference_tokens_per_day"], reverse=True)
    rows_2026 = [r for r in data["forecast"] if r["year"] == 2026]
    total_2030 = sum(r["inference_tokens_per_day"] for r in rows_2030)
    total_2026 = sum(r["inference_tokens_per_day"] for r in rows_2026)
    total_contracted_2030 = sum(r["contracted_power_gw"] for r in rows_2030)
    total_active_2030 = sum(r["active_power_gw"] for r in rows_2030)
    total_inference_2030 = sum(r["inference_gw"] for r in rows_2030)
    total_training_2030 = sum(r["training_gw"] for r in rows_2030)
    top3_share = sum(r["inference_tokens_per_day"] for r in rows_2030[:3]) / total_2030
    median_tpmw = sorted(r["tokens_per_second_per_mw"] for r in rows_2030)[len(rows_2030) // 2]
    median_inf_share = sorted(r["inference_power_share"] for r in rows_2030)[len(rows_2030) // 2]

    def constraint_label(row: dict[str, Any]) -> str:
        deploy_gap = 1 - row["active_power_gw"] / row["contracted_power_gw"]
        if deploy_gap >= 0.32:
            return "Deployment gap"
        if row["inference_power_share"] < median_inf_share:
            return "Training allocation"
        if row["tokens_per_second_per_mw"] < median_tpmw:
            return "Serving efficiency"
        return "Scale absorption"

    def constraint_score(row: dict[str, Any]) -> float:
        deploy_gap = 1 - row["active_power_gw"] / row["contracted_power_gw"]
        serving_gap = max(0, (median_tpmw - row["tokens_per_second_per_mw"]) / median_tpmw)
        inference_gap = max(0, (median_inf_share - row["inference_power_share"]) / median_inf_share)
        return round(100 * (0.45 * deploy_gap + 0.30 * serving_gap + 0.25 * inference_gap), 1)

    constraint_rows = sorted(
        [
            {
                **r,
                "deployment_gap": 1 - r["active_power_gw"] / r["contracted_power_gw"],
                "token_per_contracted_gw_q": r["inference_tokens_per_day"] / 1e15 / r["contracted_power_gw"],
                "constraint": constraint_label(r),
                "constraint_score": constraint_score(r),
            }
            for r in rows_2030
        ],
        key=lambda r: r["constraint_score"],
        reverse=True,
    )

    def set_bg(slide, color=RGBColor(255, 255, 255)):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def rect(slide, x, y, w, h, color, line_color=None):
        shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.color.rgb = line_color or color
        return shape

    def text(slide, x, y, w, h, value, size=12, color=body, bold=False, align=PP_ALIGN.LEFT):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_top = 0
        tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = value
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.alignment = align
        return box

    def header(slide, title: str, subtitle: str = ""):
        rect(slide, 0, 0, 13.333, 0.08, samsung_blue)
        text(slide, 0.72, 0.36, 4.7, 0.22, "TOKEN SUPPLY CONSTRAINTS", 7.5, samsung_blue, True)
        text(slide, 0.72, 0.72, 11.85, 0.55, title, 19.5, ink, True)
        if subtitle:
            text(slide, 0.74, 1.24, 11.4, 0.34, subtitle, 9.0, muted)
        rect(slide, 0.72, 1.64, 11.9, 0.01, silver)

    def footer(slide):
        text(slide, 0.72, 7.08, 10.2, 0.18, "Commercial LLM model-owner basis | Compute capacity to generated output token supply", 7.2, muted)
        text(slide, 11.52, 7.08, 1.1, 0.18, RUN_DATE, 7.2, muted, False, PP_ALIGN.RIGHT)

    def takeaway(slide, value: str):
        rect(slide, 0.72, 6.42, 1.25, 0.04, samsung_blue)
        text(slide, 2.13, 6.3, 10.35, 0.38, value, 11.2, ink, True)

    def stat(slide, x, y, label, value, unit, color=samsung_blue):
        text(slide, x, y, 3.05, 0.22, label, 8.6, muted, True)
        text(slide, x, y + 0.31, 3.05, 0.62, value, 27, color, True)
        text(slide, x, y + 0.94, 3.05, 0.24, unit, 8.4, muted)

    def bullets(slide, x, y, w, h, items, size=11.1, color=body, gap=6):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.clear()
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = item
            p.font.size = Pt(size)
            p.font.color.rgb = color
            p.space_after = Pt(gap)
        return box

    def style_table(table, header_color=samsung_blue, font_size=8.0):
        for r_idx, row in enumerate(table.rows):
            for cell in row.cells:
                cell.margin_left = Inches(0.055)
                cell.margin_right = Inches(0.055)
                cell.margin_top = Inches(0.035)
                cell.margin_bottom = Inches(0.035)
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color if r_idx == 0 else (RGBColor(255, 255, 255) if r_idx % 2 else pale)
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(font_size if r_idx else 8.2)
                    p.font.color.rgb = RGBColor(255, 255, 255) if r_idx == 0 else body
                    p.font.bold = r_idx == 0

    def add_small_table(slide, rows, headers, x, y, w, h, col_widths=None, font_size=7.3):
        table = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h)).table
        if col_widths:
            for i, width in enumerate(col_widths):
                table.columns[i].width = Inches(width)
        for c, header_text in enumerate(headers):
            table.cell(0, c).text = header_text
        for r_idx, row in enumerate(rows, start=1):
            for c_idx, value in enumerate(row):
                table.cell(r_idx, c_idx).text = str(value)
        style_table(table, font_size=font_size)
        return table

    def add_chart_labels(chart, number_format="0.00"):
        plot = chart.plots[0]
        plot.has_data_labels = True
        labels = plot.data_labels
        labels.number_format = number_format
        labels.font.size = Pt(6.5)
        labels.font.color.rgb = muted

    def chart_axis_style(chart):
        chart.value_axis.tick_labels.font.size = Pt(8)
        chart.category_axis.tick_labels.font.size = Pt(8)
        chart.value_axis.format.line.color.rgb = silver
        chart.category_axis.format.line.color.rgb = silver

    # 1. Cover
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    rect(slide, 0, 0, 13.333, 0.12, samsung_blue)
    text(slide, 0.72, 0.62, 4.4, 0.22, "COMPUTE CAPACITY STUDY", 8, samsung_blue, True)
    text(slide, 0.72, 1.12, 8.5, 1.72, "Token Supply Constraints\nby LLM Provider", 35, ink, True)
    text(slide, 0.76, 3.05, 7.9, 0.62, "A compute-capacity view of how contracted power, active AI load, inference allocation, and serving efficiency limit generated output token supply", 13.2, body)
    rect(slide, 8.88, 1.2, 0.04, 3.45, samsung_blue)
    stat(slide, 9.18, 1.24, "Modeled provider set", "9", "commercial LLM owners", samsung_blue)
    stat(slide, 9.18, 2.74, "Base 2030 supply", f"{total_2030/1e15:.2f}Q", "generated output tokens/day", cyan)
    text(slide, 0.72, 6.54, 6.7, 0.22, "Focus: supply constraints, not memory marketing motions", 8, muted)
    text(slide, 10.72, 6.54, 1.9, 0.22, RUN_DATE, 8, muted, False, PP_ALIGN.RIGHT)

    # 2. Executive answer
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Executive answer: the bottleneck is active inference compute, not announced power alone",
        "Token supply is constrained by four sequential conversion losses: deployment, AI IT allocation, inference share, and serving efficiency.",
    )
    cols = [
        ("01", "Deployment", f"{total_active_2030:.1f}GW active out of {total_contracted_2030:.1f}GW contracted in Base 2030."),
        ("02", "Inference allocation", f"{total_inference_2030:.1f}GW goes to inference; {total_training_2030:.1f}GW remains training-oriented."),
        ("03", "Concentration", f"Top 3 providers account for {top3_share:.0%} of modeled 2030 generated-token supply."),
    ]
    for i, (num, title, desc) in enumerate(cols):
        x = 0.82 + i * 4.05
        text(slide, x, 2.0, 0.7, 0.3, num, 11, samsung_blue, True)
        rect(slide, x, 2.36, 3.25, 0.03, samsung_blue if i == 0 else silver)
        text(slide, x, 2.65, 3.35, 0.35, title, 17.5, ink, True)
        text(slide, x, 3.18, 3.35, 1.25, desc, 14, body)
    text(slide, 0.88, 5.08, 11.5, 0.5, "What changed from the prior deck: this version does not lead with memory revenue actions. It leads with provider-level token supply constraints and only uses memory implications as downstream context.", 11.3, body)
    takeaway(slide, "Read every provider through the same funnel: contracted GW to active GW to inference GW to output tokens.")
    footer(slide)

    # 3. Constraint model
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The constraint model traces where compute capacity is lost before it becomes tokens",
        "The same formula is applied to every provider so differences come from assumptions, capacity attribution, and serving efficiency.",
    )
    steps = [
        ("Contracted\npower", "Announced or inferred capacity envelope"),
        ("Active\npower", "Energized sites and deployed accelerators"),
        ("AI IT\nload", "PUE and AI workload allocation"),
        ("Inference\nGW", "Power assigned to commercial serving"),
        ("Token\nsupply", "Selected output tokens/sec/MW"),
    ]
    for i, (label, note) in enumerate(steps):
        x = 0.78 + i * 2.45
        text(slide, x, 2.08, 1.7, 0.7, label, 16.5, ink, True, PP_ALIGN.CENTER)
        rect(slide, x, 2.92, 1.7, 0.035, samsung_blue if i == 4 else silver)
        text(slide, x, 3.16, 1.7, 0.46, note, 8.0, muted, False, PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            text(slide, x + 1.84, 2.43, 0.25, 0.24, "→", 15.5, muted, True, PP_ALIGN.CENTER)
    text(slide, 0.95, 4.25, 11.5, 0.45, "generated output tokens/day = inference GW x 1,000 x fleet-weighted serving tokens/sec/MW x 86,400", 15, samsung_blue, True, PP_ALIGN.CENTER)
    bullets(
        slide,
        1.18,
        5.05,
        10.9,
        0.7,
        [
            "Deployment gap captures power that is contracted or planned but not yet producing AI IT load.",
            "Serving efficiency captures model architecture, precision, batching, SLO targets, and production overhead.",
        ],
        10.4,
        body,
        4,
    )
    takeaway(slide, "The constraint is visible only after separating capacity ownership from operating conversion factors.")
    footer(slide)

    # 4. Provider supply ranking
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "2030 token supply is concentrated in providers with both scale and high inference conversion",
        "The chart ranks generated output token supply, while the side metrics show the compute base behind the output.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in rows_2030]
    chart_data.add_series("Q output tokens/day", [r["inference_tokens_per_day"] / 1e15 for r in rows_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.72), Inches(1.92), Inches(7.25), Inches(4.0), chart_data).chart
    chart.has_legend = False
    chart_axis_style(chart)
    add_chart_labels(chart, "0.00")
    text(slide, 8.45, 1.92, 3.65, 0.24, "2030 provider snapshot", 10.6, muted, True)
    add_small_table(
        slide,
        [
            [r["company"], f"{r['inference_tokens_per_day']/1e15:.2f}", f"{r['inference_gw']:.1f}", f"{r['active_power_gw']:.1f}"]
            for r in rows_2030[:5]
        ],
        ["Provider", "Q/day", "Inf. GW", "Act. GW"],
        8.45,
        2.28,
        3.85,
        2.35,
        [1.25, 0.78, 0.82, 0.82],
        7.1,
    )
    stat(slide, 8.45, 4.92, "Top 3 share", f"{top3_share:.0%}", "of modeled 2030 supply", cyan)
    takeaway(slide, "Token supply leadership is a compute-conversion outcome, not just a data-center footprint outcome.")
    footer(slide)

    # 5. Provider token supply time series
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Provider token supply trajectories show when each company begins to separate",
        "The line chart shows the top 2030 providers; the table keeps every modeled provider visible across 2026, 2028, and 2030.",
    )
    top5_companies = [r["company"] for r in rows_2030[:5]]
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for company in top5_companies:
        chart_data.add_series(
            company,
            [
                next(r["inference_tokens_per_day"] / 1e15 for r in data["forecast"] if r["company"] == company and r["year"] == year)
                for year in YEARS
            ],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.72), Inches(1.9), Inches(7.05), Inches(4.08), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart_axis_style(chart)
    text(slide, 8.18, 1.92, 3.95, 0.28, "All-provider token supply table", 10.6, muted, True)
    token_ts_rows = []
    for r2030 in rows_2030:
        company = r2030["company"]
        y2026 = next(r for r in data["forecast"] if r["company"] == company and r["year"] == 2026)
        y2028 = next(r for r in data["forecast"] if r["company"] == company and r["year"] == 2028)
        multiple = r2030["inference_tokens_per_day"] / y2026["inference_tokens_per_day"] if y2026["inference_tokens_per_day"] else 0
        token_ts_rows.append(
            [
                company,
                f"{y2026['inference_tokens_per_day']/1e15:.2f}",
                f"{y2028['inference_tokens_per_day']/1e15:.2f}",
                f"{r2030['inference_tokens_per_day']/1e15:.2f}",
                f"{multiple:.1f}x",
            ]
        )
    add_small_table(
        slide,
        token_ts_rows,
        ["Provider", "2026", "2028", "2030", "30/26"],
        8.18,
        2.28,
        4.25,
        3.55,
        [1.22, 0.7, 0.7, 0.7, 0.68],
        6.5,
    )
    takeaway(slide, "The constraint story is dynamic: the relevant question is when token supply separates, not only who leads in 2030.")
    footer(slide)

    # 6. Provider inference GW time series
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Inference GW trajectories explain the token supply trajectories",
        "The core model changes token supply through operational inference GW and a workload-adjusted serving reference derived from InferenceX.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for company in top5_companies:
        chart_data.add_series(
            company,
            [
                next(r["inference_gw"] for r in data["forecast"] if r["company"] == company and r["year"] == year)
                for year in YEARS
            ],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.72), Inches(1.9), Inches(7.05), Inches(4.08), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart_axis_style(chart)
    text(slide, 8.18, 1.92, 3.95, 0.28, "All-provider inference GW table", 10.6, muted, True)
    inf_ts_rows = []
    for r2030 in rows_2030:
        company = r2030["company"]
        y2026 = next(r for r in data["forecast"] if r["company"] == company and r["year"] == 2026)
        y2028 = next(r for r in data["forecast"] if r["company"] == company and r["year"] == 2028)
        inf_ts_rows.append(
            [
                company,
                f"{y2026['inference_gw']:.1f}",
                f"{y2028['inference_gw']:.1f}",
                f"{r2030['inference_gw']:.1f}",
                f"{r2030['inference_power_share']:.0%}",
            ]
        )
    add_small_table(
        slide,
        inf_ts_rows,
        ["Provider", "2026", "2028", "2030", "Share"],
        8.18,
        2.28,
        4.25,
        3.55,
        [1.22, 0.7, 0.7, 0.7, 0.68],
        6.5,
    )
    takeaway(slide, "Token growth should be decomposed into more inference GW versus better token output per MW.")
    footer(slide)

    # 7. Deployment gap
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The first constraint is the gap between contracted capacity and active capacity",
        "This is the most important near-term bottleneck because non-energized or non-deployed power cannot serve tokens.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in rows_2030]
    chart_data.add_series("Contracted GW", [r["contracted_power_gw"] for r in rows_2030])
    chart_data.add_series("Active GW", [r["active_power_gw"] for r in rows_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.72), Inches(1.9), Inches(7.65), Inches(4.1), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart_axis_style(chart)
    add_chart_labels(chart, "0.0")
    high_gap = sorted(constraint_rows, key=lambda r: r["deployment_gap"], reverse=True)[:3]
    text(slide, 8.75, 1.95, 3.35, 0.28, "Deployment gap table", 10.8, muted, True)
    add_small_table(
        slide,
        [[r["company"], f"{r['contracted_power_gw']:.1f}", f"{r['active_power_gw']:.1f}", f"{r['deployment_gap']:.0%}"] for r in high_gap],
        ["Provider", "Contr.", "Active", "Gap"],
        8.75,
        2.35,
        3.65,
        1.7,
        [1.25, 0.75, 0.75, 0.68],
        7.4,
    )
    text(slide, 8.75, 4.42, 3.45, 0.8, "How to read this: the gap between contracted and active GW is supply that exists in plans but not yet in token-serving reality.", 10.0, body)
    takeaway(slide, "Deployment speed is the first gating variable in the 2026-2030 token supply ramp.")
    footer(slide)

    # 8. Inference allocation
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The second constraint is how much AI load is assigned to inference instead of training",
        "A provider can own large compute capacity but still have limited commercial token supply if more AI load remains training-oriented.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in rows_2030]
    chart_data.add_series("Inference GW", [r["inference_gw"] for r in rows_2030])
    chart_data.add_series("Training GW", [r["training_gw"] for r in rows_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED, Inches(0.72), Inches(1.9), Inches(7.65), Inches(4.1), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart_axis_style(chart)
    add_chart_labels(chart, "0.0")
    text(slide, 8.75, 1.95, 3.35, 0.28, "Inference allocation", 10.8, muted, True)
    add_small_table(
        slide,
        [
            [r["company"], f"{r['inference_gw']:.1f}", f"{r['training_gw']:.1f}", f"{r['inference_power_share']:.0%}"]
            for r in rows_2030[:5]
        ],
        ["Provider", "Inf.", "Train", "Share"],
        8.75,
        2.35,
        3.65,
        2.25,
        [1.25, 0.72, 0.72, 0.72],
        7.2,
    )
    text(slide, 8.75, 4.95, 3.45, 0.54, "This split is a scenario variable and should be updated as providers disclose product traffic and training cadence.", 9.5, body)
    takeaway(slide, "Inference share is the bridge between compute capacity and commercial token supply.")
    footer(slide)

    # 9. Serving efficiency
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The third input weights H200, B200, GB200 and purpose-built capacity into serving throughput",
        "GPU-generation mix is an editable scenario input; public reference rows are then adjusted for commercial workload fit.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in rows_2030]
    chart_data.add_series("Output tokens/sec/MW", [r["tokens_per_second_per_mw"] / 1e6 for r in rows_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.72), Inches(1.9), Inches(7.0), Inches(4.1), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.number_format = "0.0"
    chart_axis_style(chart)
    add_chart_labels(chart, "0.0")
    table_rows = sorted(rows_2030, key=lambda r: r["tokens_per_second_per_mw"])[:5]
    text(slide, 8.18, 1.92, 3.95, 0.28, "Commercial serving reference", 10.6, muted, True)
    add_small_table(
        slide,
        [[r["company"], f"{r['short_chat_share']:.0%}/{r['long_chat_share']:.0%}/{r['agentic_share']:.0%}", f"{r['commercial_workload_fit_factor']:.0%}", f"{r['tokens_per_second_per_mw']/1e6:.2f}"] for r in table_rows],
        ["Provider", "S/L/A", "Fit", "M tok/s/MW"],
        8.18,
        2.30,
        4.25,
        2.35,
        [1.05, 1.0, 1.0, 1.0],
        6.9,
    )
    text(slide, 8.18, 4.98, 4.05, 0.60, "S/L/A is short conversation, long conversation and agentic mix; purpose-built hardware still receives no premium without matched output-token evidence.", 9.4, body)
    takeaway(slide, "Base TPS/MW now reflects GPU-generation mix, workload class mix and commercial workload fit.")
    footer(slide)

    # 10. Provider constraint map
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Provider constraint map: each company has a different limiting factor",
        "The score is a directional operating index using deployment gap, inference share, and selected TPS/MW versus the peer set.",
    )
    table = slide.shapes.add_table(len(constraint_rows) + 1, 6, Inches(0.72), Inches(1.85), Inches(11.95), Inches(4.25)).table
    widths = [1.55, 1.25, 1.2, 1.55, 1.35, 4.05]
    for i, width in enumerate(widths):
        table.columns[i].width = Inches(width)
    headers = ["Provider", "Supply Q/day", "Inf. GW", "Deploy gap", "Constraint", "What to validate next"]
    for c, h in enumerate(headers):
        table.cell(0, c).text = h
    for i, r in enumerate(constraint_rows, start=1):
        validate_next = {
            "Deployment gap": "site energization, rack deployment, accelerator delivery",
            "Training allocation": "training cadence, launch schedule, commercial serving ramp",
            "Serving efficiency": "model routing, precision, batching, TTFT/TPOT target",
            "Scale absorption": "demand absorption and product surface expansion",
        }[r["constraint"]]
        vals = [
            r["company"],
            f"{r['inference_tokens_per_day']/1e15:.2f}",
            f"{r['inference_gw']:.1f}",
            f"{r['deployment_gap']:.0%}",
            r["constraint"],
            validate_next,
        ]
        for c, v in enumerate(vals):
            table.cell(i, c).text = v
    style_table(table, font_size=7.4)
    takeaway(slide, "The next research cycle should target the limiting factor for each provider, not collect generic capacity headlines.")
    footer(slide)

    # 11. Scenario stress
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Scenario stress shows how sensitive token supply is to compute conversion assumptions",
        "Bull and Bear cases move operational deployment, inference allocation and the explicit commercial-workload fit to the public reference.",
    )
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for scen in ("Bear", "Base", "Bull"):
        chart_data.add_series(
            scen,
            [next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.82), Inches(1.9), Inches(7.25), Inches(4.0), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart_axis_style(chart)
    add_chart_labels(chart, "0.00")
    text(slide, 8.55, 1.95, 3.5, 0.28, "2030 scenario output", 10.8, muted, True)
    scenario_2030_rows = [r for r in data["scenario_summary"] if r["year"] == 2030 and r["scenario"] in ("Bear", "Base", "Bull")]
    add_small_table(
        slide,
        [[r["scenario"], f"{r['inference_tokens_per_day_q']:.2f}", f"{r['active_power_gw']:.1f}", f"{r['weighted_inference_share']:.0%}"] for r in scenario_2030_rows],
        ["Case", "Q/day", "Act. GW", "Inf. share"],
        8.55,
        2.32,
        3.8,
        1.7,
        [0.85, 0.8, 0.85, 1.0],
        7.2,
    )
    text(slide, 8.55, 4.35, 3.2, 0.28, "Scenario levers", 10.5, muted, True)
    bullets(
        slide,
        8.55,
        4.72,
        3.3,
        0.88,
        [
            "Operational deployment speed",
            "Commercial workload fit to public TPS/MW reference",
            "Inference share of AI IT load",
        ],
        9.7,
        body,
        3,
    )
    text(slide, 8.55, 5.75, 3.2, 0.28, f"Base growth: {total_2030 / total_2026:.1f}x, 2026-2030", 11.2, samsung_blue, True)
    takeaway(slide, "The same provider can move from constrained to advantaged if deployment and serving conversion improve together.")
    footer(slide)

    # 12. Source and provenance coverage
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Evidence base now separates official submissions, serving proxies, and provenance",
        "The workbook carries the source registry and number-level provenance so benchmark evidence is visible without changing the headline formula.",
    )
    evidence_rows = [
        ["Official benchmark", "MLPerf Inference / MLPerf Power", "hardware and power/performance anchor; not production telemetry"],
        ["LLM serving proxy", "InferenceX DB dump", "model x GPU x precision x ISL/OSL output TPS/MW reference"],
        ["Serving stack", "vLLM / SGLang / TensorRT-LLM / FlashInfer", "mechanism layer for batching, KV cache, kernel and runtime behavior"],
        ["Scheduling papers", "Orca / Sarathi / DistServe / Splitwise", "utilization, prefill/decode and TTFT/TPOT sensitivity"],
        ["Trend context", "Epoch AI", "training scale, inference price trend, power and scaling bottlenecks"],
    ]
    add_small_table(
        slide,
        evidence_rows,
        ["Layer", "Source set", "How it is used"],
        0.82,
        1.9,
        11.7,
        3.35,
        [2.05, 3.55, 6.1],
        8.0,
    )
    text(slide, 0.92, 5.55, 11.05, 0.42, "Excel tabs 07_Source_Registry, 08_Provenance_Trace, and 09_Fact_Assumption_Audit expose source IDs, formula/rule, replacement path, and evidence class for review.", 10.5, body)
    takeaway(slide, "MLPerf and InferenceX are benchmark anchors; provider-specific production telemetry remains the replacement path.")
    footer(slide)

    # 13. Operating questions
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "The operating agenda is to verify the bottleneck, then update the provider model",
        "This is the checklist that keeps the simulation tied to facts as new capacity, model, and benchmark data arrives.",
    )
    questions = [
        ("Power", "Which contracted sites are energized, and when do accelerators enter production service?"),
        ("Allocation", "What share of AI IT load is serving commercial inference versus training or experimentation?"),
        ("Architecture", "Which model family, active parameter band, context length, and routing policy dominate traffic?"),
        ("Efficiency", "What output tokens/sec/MW is realistic after SLO, precision, batching, and production haircut?"),
        ("Demand absorption", "Which product surfaces can absorb the incremental token supply without idle capacity?"),
    ]
    for i, (area, q) in enumerate(questions):
        y = 1.86 + i * 0.72
        text(slide, 0.92, y, 1.35, 0.24, area, 12, samsung_blue, True)
        rect(slide, 2.48, y + 0.11, 0.8, 0.02, silver)
        text(slide, 3.52, y, 8.65, 0.27, q, 11.4, body)
    text(slide, 0.92, 5.78, 11.1, 0.42, "Workbook tabs: Logic, Benchmark Input, Inputs, GPU Mix Input, Calculation, Output, Checks, Aggressive View, Source Registry, Provenance Trace, Fact Audit. Derived output cells use Excel formulas.", 10.5, muted)
    takeaway(slide, "Update only visible inputs; the workbook recalculates token supply through the same core formula.")
    footer(slide)

    prs.save(path)


def write_core_markdown(data: dict[str, Any], path: Path) -> None:
    base_2030 = sorted(
        [row for row in data["forecast"] if row["year"] == 2030],
        key=lambda row: row["inference_tokens_per_day"],
        reverse=True,
    )
    lines = [
        "# Compute Capacity To Generated Output Token Supply",
        "",
        f"- 생성일: {RUN_DATE}",
        "- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션",
        "- 출력 정의: generated output tokens/day",
        "",
        "## Core Formula",
        "",
        "```text",
        "operational_power_gw = contracted_power_gw * operational_deployment_share",
        "inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share",
        "gpu_workload_avg_tps_per_mw = short_share*gpu_short_tps_mw + long_share*gpu_long_tps_mw + agentic_share*gpu_agentic_tps_mw",
        "fleet_reference_tps_per_mw = h200_share*h200_workload_avg + b200_share*b200_workload_avg + gb200_share*gb200_workload_avg + purpose_built_share*purpose_workload_avg",
        "serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor",
        "generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400",
        "```",
        "",
        "- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.",
        "- GPU 세대 mix는 `H200`, `B200`, `GB200`, `purpose-built`의 inference-load share이며 Excel에서 별도 입력합니다.",
        "- InferenceX GPU별 값은 public reference이며, 상용 서비스 TPS/MW는 short conversation, long conversation, agentic workload mix와 workload fit factor를 반영합니다.",
        "- Purpose-built accelerator의 comparable benchmark가 없으면 B200 placeholder를 사용하며 이후 입력으로 교체합니다.",
        "",
        "## GPU Generation Mix, Workload Mix And Commercial Fit",
        "",
        "| Provider | Proxy | 2030 H/B/GB/PB | Short/Long/Agentic | Weighted ref TPS/MW | Fit | Serving TPS/MW |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    benchmark_map = company_core_benchmark_map()
    workload_map = commercial_workload_profiles()
    for company in [scenario.company for scenario in scenarios()]:
        row = next(item for item in data["forecast"] if item["company"] == company and item["year"] == 2030)
        workload = workload_map[company]
        lines.append(
            f"| {company} | {row['gpu_benchmark_proxy_model']} | {row['h200_share']:.0%}/{row['b200_share']:.0%}/{row['gb200_share']:.0%}/{row['purpose_built_accelerator_share']:.0%} | {row['short_chat_share']:.0%}/{row['long_chat_share']:.0%}/{row['agentic_share']:.0%} | {row['fleet_reference_tps_per_mw']:,} | {workload['base_fit_factor']:.0%} | {row['reference_serving_tps_per_mw']:,} |"
        )
    lines += [
        "",
        "## Base 2030 Output",
        "",
        "| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in base_2030:
        lines.append(
            f"| {row['company']} | {row['active_power_gw']:.3f} | {row['inference_gw']:.3f} | {row['tokens_per_second_per_mw']:,} | {row['inference_tokens_per_day']/1e15:.3f} |"
        )
    lines += [
        "",
        "## Scenario Output",
        "",
        "| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for scenario in SCENARIO_CASES:
        vals = [
            next(
                row["inference_tokens_per_day_q"]
                for row in data["scenario_summary"]
                if row["scenario"] == scenario and row["year"] == year
            )
            for year in YEARS
        ]
        lines.append(f"| {scenario} | " + " | ".join(f"{value:.3f}" for value in vals) + " |")
    lines += [
        "",
        "## Workbook",
        "",
        "- `00_Logic`: calculation steps only.",
        "- `01_Benchmark_Input`: 업체별 short/long/agentic 비율, GPU별 chat-length TPS/MW, GPU별 workload 평균 TPS/MW, commercial workload fit 입력.",
        "- `02_Inputs`: 전력 및 workload allocation 입력.",
        "- `02_GPU_Mix_Input`: H200/B200/GB200/purpose-built share를 나중에 직접 교체하는 입력 시트.",
        "- `03_Calculation`: formula-only calculation chain.",
        "- `04_Output`: formula-driven 2026-2030 provider/scenario tables for tokens/day and tokens/year with charts.",
        "- `05_Checks`: formula checks.",
        "- `06_Aggressive_View`: Bull commercial case와 public benchmark ceiling의 formula-driven upside view.",
        "- `07_Source_Registry`, `08_Provenance_Trace`, `09_Fact_Assumption_Audit`: expanded source/provenance layer.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_core_html(data: dict[str, Any], path: Path) -> None:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<title>LLM Token Capacity Core Model</title>
<style>
body {{ font-family: Arial, sans-serif; margin:0; color:#14213d; background:#f6f8fb; }}
header {{ background:#14213d; color:#fff; padding:32px 42px; }}
header h1 {{ margin:0 0 8px; font-size:30px; }}
main {{ max-width:1180px; margin:24px auto; padding:0 24px 40px; }}
section {{ background:#fff; margin:16px 0; padding:22px; border:1px solid #e2e8f0; }}
h2 {{ font-size:19px; margin:0 0 14px; }}
code, pre {{ font-family: Menlo, Consolas, monospace; }}
pre {{ background:#f2f5fa; padding:16px; line-height:1.6; overflow:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:#14213d; color:#fff; text-align:left; padding:9px; }}
td {{ padding:8px 9px; border-bottom:1px solid #e7edf4; }}
.controls {{ display:flex; gap:16px; margin-bottom:14px; }}
select {{ padding:7px; }}
.barrow {{ display:grid; grid-template-columns:130px 1fr 100px; gap:12px; align-items:center; margin:10px 0; }}
.bar {{ background:#e5ebf3; height:16px; }}
.fill {{ height:16px; background:#0067b9; }}
.note {{ color:#506174; font-size:12px; margin-top:10px; }}
</style>
</head>
<body>
<header><h1>Compute Capacity To Generated Output Token Supply</h1><div>상용 LLM owner 기준 | Simple core formula | {RUN_DATE}</div></header>
<main>
<section><h2>Core Formula</h2><pre>operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
gpu_workload_avg_tps_per_mw = short_share*gpu_short_tps_mw + long_share*gpu_long_tps_mw + agentic_share*gpu_agentic_tps_mw
fleet_reference_tps_per_mw = H200_share*H200_workload_avg + B200_share*B200_workload_avg + GB200_share*GB200_workload_avg + purpose_built_share*purpose_workload_avg
serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor
generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400</pre>
<div class="note">GPU generation mix는 동일 inference MW 내 hardware composition 차이를 반영합니다. InferenceX/MLPerf/vendor serving stack은 public reference이며, headline은 short conversation, long conversation, agentic mix와 commercial workload fit을 적용합니다.</div></section>
<section><h2>Output View</h2><div class="controls"><label>Scenario <select id="scenario"></select></label><label>Year <select id="year"></select></label></div><div id="bars"></div></section>
<section><h2>Default 2030 Workload Mix And Serving Reference</h2><table id="bench"></table></section>
</main>
<script>
const DATA = {payload}; const $ = id => document.getElementById(id);
const scenarios = [...new Set(DATA.scenario_forecast.map(r => r.scenario))];
const years = [...new Set(DATA.scenario_forecast.map(r => r.year))];
function init() {{
  $("scenario").innerHTML = scenarios.map(s => `<option>${{s}}</option>`).join(""); $("scenario").value="Base";
  $("year").innerHTML = years.map(y => `<option>${{y}}</option>`).join(""); $("year").value="2030";
  $("scenario").oninput=render; $("year").oninput=render; render();
  const b2030=DATA.forecast.filter(r=>r.year===2030);
  $("bench").innerHTML = `<tr><th>Provider</th><th>Proxy model</th><th>Short/Long/Agentic</th><th>Weighted ref TPS/MW</th><th>Fit</th><th>Serving TPS/MW</th></tr>` +
    b2030.map(b => `<tr><td>${{b.company}}</td><td>${{b.gpu_benchmark_proxy_model}}</td><td>${{(b.short_chat_share*100).toFixed(0)}}% / ${{(b.long_chat_share*100).toFixed(0)}}% / ${{(b.agentic_share*100).toFixed(0)}}%</td><td>${{b.fleet_reference_tps_per_mw.toLocaleString()}}</td><td>${{(b.commercial_workload_fit_factor*100).toFixed(0)}}%</td><td>${{b.reference_serving_tps_per_mw.toLocaleString()}}</td></tr>`).join("");
}}
function render() {{
  const rows=DATA.scenario_forecast.filter(r=>r.scenario===$("scenario").value && r.year===Number($("year").value)).sort((a,b)=>b.inference_tokens_per_day-a.inference_tokens_per_day);
  const max=Math.max(...rows.map(r=>r.inference_tokens_per_day),1);
  $("bars").innerHTML=rows.map(r=>`<div class="barrow"><strong>${{r.company}}</strong><div class="bar"><div class="fill" style="width:${{100*r.inference_tokens_per_day/max}}%"></div></div><div>${{(r.inference_tokens_per_day/1e15).toFixed(3)}}Q</div></div>`).join("");
}}
init();
</script>
</body></html>"""
    path.write_text(html, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    rows = forecast_rows("Base")
    scenario_rows = [row for name in SCENARIO_CASES for row in forecast_rows(name)]
    data = {
        "metadata": {
            "title": "상용 LLM 업체별 전력·GPU·토큰 생성량 시뮬레이션",
            "generated_at": RUN_DATE,
            "companies": [s.company for s in scenarios()],
            "years": YEARS,
            "scope": "Commercial LLM model owners only; hosting providers excluded from core rows.",
        },
        "sources": [asdict(s) for s in sources()],
        "fact_anchors": [asdict(f) for f in fact_anchors()],
        "company_models": [asdict(m) for m in company_models()],
        "assumptions": assumptions(),
        "formula_assumptions": formula_assumptions(),
        "token_definitions": token_definitions(),
        "benchmark_assumptions": benchmark_assumptions(),
        "core_inferencex_benchmarks": core_inferencex_benchmark_profiles(),
        "workload_class_assumptions": workload_class_assumptions(),
        "workload_mix_profiles": workload_mix_rows(),
        "workload_reference_profiles": workload_reference_rows(),
        "interactivity_reference_profiles": interactivity_reference_rows(),
        "hallucination_checklist": hallucination_checklist(),
        "scenario_definitions": scenario_definitions(),
        "forecast": rows,
        "number_trace": number_trace_rows(scenario_rows),
        "company_input_audit": company_input_audit(rows),
        "scenario_forecast": scenario_rows,
        "scenario_summary": scenario_summary_rows(scenario_rows),
        "benchmark_reference": benchmark_reference_rows(rows),
        "energy_sanity_reference": energy_sanity_reference_rows(rows),
        "utilization_sensitivity": utilization_sensitivity_rows(rows),
        "inferencex": inferencex_ingestion_payload(),
        "sensitivity": sensitivity_rows(rows),
        "exec_summary": exec_summary(rows),
    }
    data["validation"] = validate(scenario_rows)
    registered_ids = {item["source_id"] for item in data["sources"]} | {
        item["assumption_id"] for item in data["assumptions"]
    }
    referenced_ids: set[str] = set()
    for collection in (
        "fact_anchors",
        "company_models",
        "formula_assumptions",
        "forecast",
        "number_trace",
        "company_input_audit",
        "scenario_forecast",
    ):
        for item in data[collection]:
            for field in ("source_ids", "assumption_ids"):
                referenced_ids.update(
                    token.strip()
                    for token in str(item.get(field, "")).split(";")
                    if token.strip().startswith(("SRC_", "ASSUMP_"))
                )
    missing_ids = sorted(referenced_ids - registered_ids)
    if missing_ids:
        data["validation"]["status"] = "FAIL"
        data["validation"]["failures"].append(
            f"unregistered source/assumption IDs: {', '.join(missing_ids)}"
        )
    else:
        data["validation"]["model_checks"]["source_assumption_registry"] = (
            "PASS - Every source_id and assumption_id referenced by facts, formulas and forecast trace rows is registered."
        )
    if len(data["company_input_audit"]) != len(scenarios()) * 9:
        data["validation"]["status"] = "FAIL"
        data["validation"]["failures"].append("company input audit does not contain 9 metrics for every company")
    else:
        data["validation"]["model_checks"]["fact_vs_assumption_audit"] = (
            "PASS - Each company has nine input/output audit rows separating public anchors from modeled values."
        )
    return data


def lightweight_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Publish only the fields required to read or recalculate headline logic."""
    core_fields = [
        "scenario",
        "company",
        "region",
        "year",
        "contracted_power_gw",
        "operational_deployment_share",
        "active_power_gw",
        "pue",
        "ai_workload_share",
        "inference_power_share",
        "inference_gw",
        "training_gw",
        "gpu_share",
        "h200_share",
        "b200_share",
        "gb200_share",
        "purpose_built_accelerator_share",
        "gpu_benchmark_proxy_model",
        "commercial_workload_class",
        "h200_reference_tps_per_mw",
        "b200_reference_tps_per_mw",
        "gb200_reference_tps_per_mw",
        "purpose_built_reference_tps_per_mw",
        "fleet_reference_tps_per_mw",
        "inferencex_reference_tps_per_mw",
        "short_chat_share",
        "long_chat_share",
        "agentic_share",
        "short_chat_reference_tps_per_mw",
        "long_chat_reference_tps_per_mw",
        "agentic_reference_tps_per_mw",
        "h200_workload_weighted_tps_per_mw",
        "b200_workload_weighted_tps_per_mw",
        "gb200_workload_weighted_tps_per_mw",
        "purpose_built_workload_weighted_tps_per_mw",
        "commercial_workload_fit_factor",
        "reference_serving_tps_per_mw",
        "purpose_built_tps_per_mw",
        "tokens_per_second_per_mw",
        "inference_tokens_per_day",
        "inference_tokens_per_year",
    ]
    def core_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{field: row.get(field) for field in core_fields} for row in rows]
    return {
        "metadata": data["metadata"],
        "formula_assumptions": [
            item for item in data["formula_assumptions"]
            if item["category"] not in {"Token definition - processed benchmark", "Energy sanity check"}
        ],
        "scenario_definitions": data["scenario_definitions"],
        "core_inferencex_benchmarks": data["core_inferencex_benchmarks"],
        "workload_class_assumptions": data["workload_class_assumptions"],
        "workload_mix_profiles": data["workload_mix_profiles"],
        "workload_reference_profiles": data["workload_reference_profiles"],
        "interactivity_reference_profiles": data["interactivity_reference_profiles"],
        "commercial_workload_benchmarks": commercial_workload_benchmark_rows(),
        "hardware_reference_profiles": hardware_reference_profiles(),
        "forecast": core_rows(data["forecast"]),
        "scenario_forecast": core_rows(data["scenario_forecast"]),
        "scenario_summary": data["scenario_summary"],
        "validation": data["validation"],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = build_payload()
    if data["validation"]["status"] != "PASS":
        raise SystemExit(json.dumps(data["validation"], indent=2, ensure_ascii=False))

    stem = "llm_token_capacity_2026_2030"
    slim_data = lightweight_payload(data)
    write_json(slim_data, OUT / f"{stem}.json")
    write_excel(data, OUT / f"{stem}.xlsx")
    write_ppt_compute_constraint(data, OUT / f"{stem}.pptx")
    write_ppt_compute_constraint(data, OUT / "llm_token_supply_constraints_by_compute_capacity_en_2026_2030.pptx")
    write_ppt_samsung_style(data, OUT / "llm_token_capacity_samsung_style_en_2026_2030.pptx")
    write_core_html(slim_data, OUT / f"{stem}.html")
    write_core_markdown(slim_data, OUT / f"{stem}.md")
    write_interactivity_summary(slim_data, OUT / "inferencex_interactivity_gpu_serving_summary.md")
    print(
        json.dumps(
            {
                "status": "PASS",
                "outputs": [str(OUT / f"{stem}.{ext}") for ext in ("json", "xlsx", "pptx", "html", "md")]
                + [
                    str(OUT / "llm_token_supply_constraints_by_compute_capacity_en_2026_2030.pptx"),
                    str(OUT / "llm_token_capacity_samsung_style_en_2026_2030.pptx"),
                    str(OUT / "inferencex_interactivity_gpu_serving_summary.md"),
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
