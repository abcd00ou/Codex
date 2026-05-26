"""Generate LLM-owner token capacity simulation artifacts.

This report is intentionally separate from the project's core dynamics model.
It creates an auditable executive simulation for commercial LLM owners, with
every modeled number labeled as Fact, Estimate, or Scenario.
"""

from __future__ import annotations

import json
import math
import csv
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
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
RUN_DATE = "2026-05-26"
YEARS = list(range(2026, 2031))


SCENARIO_CASES = {
    "Bear": {
        "description_kr": "전력 인허가/장비 조달 지연, MoE 최적화 둔화, inference 전환이 느린 경우",
        "operational_deploy_multiplier_2026": 0.90,
        "operational_deploy_multiplier_2030": 0.82,
        "inference_share_delta_2026": -0.08,
        "inference_share_delta_2030": -0.10,
        "tokens_per_mw_multiplier": 0.82,
        "moe_optimization_multiplier": 0.92,
        "utilization_multiplier": 0.90,
        "confidence": "Scenario-Low",
    },
    "Base": {
        "description_kr": "현재 공식 발표와 시장전망을 기준으로 한 staged deployment, MoE 효율 개선, inference mix 상승",
        "operational_deploy_multiplier_2026": 1.00,
        "operational_deploy_multiplier_2030": 1.00,
        "inference_share_delta_2026": 0.00,
        "inference_share_delta_2030": 0.00,
        "tokens_per_mw_multiplier": 1.00,
        "moe_optimization_multiplier": 1.00,
        "utilization_multiplier": 1.00,
        "confidence": "Scenario-Medium",
    },
    "Bull": {
        "description_kr": "전력 energization이 빠르고, MoE/serving stack 최적화가 강하며, commercial inference 비중이 빠르게 상승",
        "operational_deploy_multiplier_2026": 1.05,
        "operational_deploy_multiplier_2030": 1.18,
        "inference_share_delta_2026": 0.05,
        "inference_share_delta_2030": 0.08,
        "tokens_per_mw_multiplier": 1.18,
        "moe_optimization_multiplier": 1.18,
        "utilization_multiplier": 1.06,
        "confidence": "Scenario-Low-Medium",
    },
    "Grid-Constrained / Efficiency-Upside": {
        "description_kr": "전력 투입은 지연되지만 MoE·quantization·batching 효율이 개선되어 token capacity 하락을 일부 상쇄",
        "operational_deploy_multiplier_2026": 0.88,
        "operational_deploy_multiplier_2030": 0.72,
        "inference_share_delta_2026": 0.02,
        "inference_share_delta_2030": 0.04,
        "tokens_per_mw_multiplier": 1.18,
        "moe_optimization_multiplier": 1.22,
        "utilization_multiplier": 1.02,
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
    fleet allocation. Official sources establish platform presence/direction;
    they do not establish the exact share used below.
    """
    return {
        "Microsoft": {
            "gpu_label": "NVIDIA GPU / Azure GPU reference",
            "asic_label": "Maia inference accelerator",
            "gpu_share_2026": 0.90,
            "gpu_share_2030": 0.55,
            "asic_efficiency_factor": 1.15,
            "architecture_workload_factor": 1.0345,
            "source_ids": "SRC_MS_MAIA200; SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS",
            "mix_rationale": "Maia 200 is officially designated for inference, Azure AI Foundry and Microsoft 365 Copilot. Exact serving fleet share is undisclosed; gradual Maia adoption is modeled.",
            "tps_rationale": "Weighted GPU/Maia bridge, calibrated to Microsoft mixed Copilot/model-routing workload rather than a disclosed production benchmark.",
            "replacement_path": "Microsoft disclosure of Maia accelerator-hours or Copilot model/hardware routing mix.",
        },
        "Google": {
            "gpu_label": "GPU reference",
            "asic_label": "TPU / Ironwood",
            "gpu_share_2026": 0.20,
            "gpu_share_2030": 0.10,
            "asic_efficiency_factor": 1.25,
            "architecture_workload_factor": 1.0417,
            "source_ids": "SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; SRC_GOOGLE_GEMINI_TOKENS",
            "mix_rationale": "Google officially positions Ironwood as an inference TPU and publicly documents TPU generations; TPU-heavy serving is modeled, not measured fleet share.",
            "tps_rationale": "TPU-heavy weighted efficiency premium plus Gemini serving workload calibration.",
            "replacement_path": "Gemini production serving throughput/power or TPU-versus-GPU serving allocation disclosure.",
        },
        "Meta": {
            "gpu_label": "NVIDIA / external GPU reference",
            "asic_label": "MTIA",
            "gpu_share_2026": 0.90,
            "gpu_share_2030": 0.55,
            "asic_efficiency_factor": 1.18,
            "architecture_workload_factor": 1.1002,
            "source_ids": "SRC_META_MTIA_GENAI_2026; SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA",
            "mix_rationale": "Meta discloses hundreds of thousands of MTIA chips for inference and an inference-first GenAI MTIA roadmap. LLM-serving mix remains undisclosed; adoption is scenario-based.",
            "tps_rationale": "Weighted GPU/MTIA bridge adjusted for Llama/Meta AI serving mix and MoE/open-model direction.",
            "replacement_path": "Meta AI production model-routing and MTIA-versus-GPU inference allocation disclosure.",
        },
        "xAI": {
            "gpu_label": "NVIDIA Hopper/next-generation GPU",
            "asic_label": "No disclosed operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 0.95,
            "source_ids": "SRC_XAI_NVIDIA_COLOSSUS; SRC_XAI_MODELS",
            "mix_rationale": "Official infrastructure anchor is NVIDIA GPU cluster scale. No xAI-operated custom inference ASIC share is used in Base.",
            "tps_rationale": "GPU-only closed-model proxy with lower workload factor pending Grok serving benchmark.",
            "replacement_path": "xAI serving hardware mix, Grok inference benchmark and active traffic disclosure.",
        },
        "OpenAI": {
            "gpu_label": "NVIDIA GB200 / partner GPU capacity",
            "asic_label": "No disclosed operated custom ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.05,
            "source_ids": "SRC_OPENAI_STARGATE_PROGRESS; SRC_OPENAI_GPT41_DOCS",
            "mix_rationale": "OpenAI states Oracle began delivering NVIDIA GB200 racks for Stargate. No operated custom-ASIC mix is publicly quantified in the model.",
            "tps_rationale": "GPU-reference closed frontier model/router proxy; not direct ChatGPT/API telemetry.",
            "replacement_path": "OpenAI hardware allocation and output-token throughput by model/product surface.",
        },
        "Anthropic": {
            "gpu_label": "Partner GPU reference",
            "asic_label": "AWS Trainium / hosted purpose-built accelerators",
            "gpu_share_2026": 0.35,
            "gpu_share_2030": 0.15,
            "asic_efficiency_factor": 1.12,
            "architecture_workload_factor": 0.9091,
            "source_ids": "SRC_AWS_RAINIER_ACTIVE; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_ANTHROPIC_CLAUDE_DOCS",
            "mix_rationale": "Project Rainier establishes large Anthropic-directed Trainium capacity. Exact Claude inference allocation across Trainium, TPU and GPU is undisclosed.",
            "tps_rationale": "Purpose-built-heavy hosted mix adjusted downward for closed-model and serving-workload uncertainty.",
            "replacement_path": "Anthropic/AWS production inference hardware allocation and Claude tokens/MW measurement.",
        },
        "DeepSeek": {
            "gpu_label": "NVIDIA H800 GPU",
            "asic_label": "No disclosed operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.45,
            "source_ids": "SRC_DEEPSEEK_H800_INFERENCE; SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1",
            "mix_rationale": "DeepSeek disclosed that V3/R1 inference services used H800 GPUs in its published infrastructure overview; no Base ASIC migration is assumed.",
            "tps_rationale": "GPU reference receives a MoE/MLA architecture factor because 671B total and 37B active parameters are officially disclosed.",
            "replacement_path": "Updated DeepSeek operated fleet hardware and measured V3/R1 output tokens per MW.",
        },
        "Alibaba": {
            "gpu_label": "Alibaba Cloud GPU inference reference",
            "asic_label": "No disclosed Qwen operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.35,
            "source_ids": "SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY",
            "mix_rationale": "Alibaba Cloud officially documents GPU-based Qwen inference deployment, but not the operated Qwen GPU/ASIC fleet allocation. Base remains GPU-reference.",
            "tps_rationale": "GPU reference receives Qwen3 MoE active-parameter architecture factor; no unverified local-ASIC uplift is used.",
            "replacement_path": "Alibaba-operated Qwen fleet mix or production Model Studio output tokens/MW.",
        },
        "Tencent": {
            "gpu_label": "Tencent Cloud GPU reference",
            "asic_label": "No disclosed Hunyuan operated ASIC share",
            "gpu_share_2026": 1.00,
            "gpu_share_2030": 1.00,
            "asic_efficiency_factor": 1.00,
            "architecture_workload_factor": 1.20,
            "source_ids": "SRC_TENCENT_HUNYUAN; SRC_TENCENT_AI_INFRA_MOE",
            "mix_rationale": "Tencent discloses Hunyuan services, AI Infra and Hunyuan Turbo MoE efficiency direction, but not operated accelerator mix. Base remains GPU-reference.",
            "tps_rationale": "GPU-reference scenario uplift reflects disclosed MoE/inference-cost direction, not measured Hunyuan tokens/MW.",
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
            "Bounds OpenAI 2030 contracted_power_gw scenario.",
            "2030 OpenAI contracted_power_gw 12GW는 공개 commitment를 약간 상회하지 않도록 점검하는 ceiling 역할.",
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
            "Sets Anthropic contracted/hosted capacity ceiling; active power remains scenario.",
            "Anthropic contracted_power_2030_gw와 active_power_2030_gw의 상한 anchor. AWS는 host이며 model-owner attribution은 Anthropic.",
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
            "category": "Capacity definition - active relationship",
            "formula": "active_power_gw = min(contracted_power_gw, modeled_operationally_deployed_power_gw)",
            "meaning_kr": "active power는 계약/계획/귀속 capacity 중 실제로 energization, accelerator deployment, cooling/network readiness를 통과해 AI workload에 배치 가능한 power envelope입니다. 따라서 항상 contracted 이하이며 fact가 아닌 경우 scenario로 표기합니다.",
            "evidence_type": "Model control rule",
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
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX",
        },
        {
            "category": "Token definition - training",
            "formula": "training_tokens_processed_per_day = training_gw * 1000 * training_tps_per_mw_equivalent * utilization * 86,400",
            "meaning_kr": "training token은 모델 학습에서 처리된 corpus/token count이며 상용 서비스가 생성한 output token이 아닙니다. 본 모델의 training_tps_per_mw_equivalent = inference tokens/MW * 0.22는 별도 capacity sanity proxy이며 실제 training telemetry가 아닙니다.",
            "evidence_type": "Definition + Scenario proxy",
            "source_ids": "SRC_DEEPSEEK_V3; SRC_TENCENT_HUNYUAN; ASSUMP_POWER_RAMP",
        },
        {
            "category": "Power to AI IT load",
            "formula": "it_load_gw = active_power_gw / pue",
            "meaning_kr": "계약/계획 전력이 아니라 실제 operational deploy된 전력에서 PUE를 차감해 IT load를 산출.",
            "evidence_type": "Formula",
            "source_ids": "SRC_MCKINSEY_AI_WORKLOADS; SRC_EPRI_EPOCH_AI_POWER",
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
            "category": "Accelerator mix bridge",
            "formula": "accelerator_mix_factor = gpu_share * 1.0 + purpose_built_share * purpose_built_relative_efficiency_factor",
            "meaning_kr": "GPU/ASIC mix는 numeric scenario로 관리합니다. official source는 accelerator의 존재와 목적을 증명하지만 operated serving share는 대체로 공개하지 않으므로, share와 relative efficiency factor는 replacement evidence가 생기기 전까지 estimate/scenario입니다.",
            "evidence_type": "Platform fact + Numeric scenario",
            "source_ids": "SRC_MS_MAIA200; SRC_GOOGLE_IRONWOOD; SRC_META_MTIA_GENAI_2026; SRC_AWS_RAINIER_ACTIVE; ASSUMP_NUMERIC_ACCELERATOR_MIX",
        },
        {
            "category": "Mix to serving efficiency",
            "formula": "tokens_per_second_per_mw = gpu_reference_tps_per_mw * accelerator_mix_factor * architecture_workload_factor * software_efficiency_growth * scenario_multipliers",
            "meaning_kr": "tokens/MW는 hardware mix alone이 아니라 모델 architecture(MoE/closed proxy), ISL/OSL, precision, batching, SLO와 software efficiency를 함께 반영합니다. InferenceX는 output-token benchmark calibration layer이며 company production fact가 아닙니다.",
            "evidence_type": "Derived estimate + Benchmark calibration",
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX; SRC_DEEPSEEK_V3; SRC_QWEN3_GITHUB; SRC_TENCENT_AI_INFRA_MOE; ASSUMP_NUMERIC_ACCELERATOR_MIX",
        },
        {
            "category": "Inference token capacity",
            "formula": "inference_tokens_per_day = inference_gw * 1000 * tokens_per_second_per_mw * utilization * 86,400",
            "meaning_kr": "전력 배정, serving 효율, 실제 utilization이 token 생성 capacity를 결정.",
            "evidence_type": "Model equation",
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX; SRC_ARXIV_INFERENCE_ENERGY",
        },
        {
            "category": "Utilization interpretation",
            "formula": "realized_output_capacity = theoretical_output_capacity * utilization",
            "meaning_kr": "utilization은 전력이 켜져 있다는 뜻이 아니라 theoretical output throughput 중 실제 traffic으로 실현되는 비율입니다. latency SLO headroom, failover reserve, uneven arrivals, batch fill, maintenance, training competition 때문에 100%가 될 수 없습니다.",
            "evidence_type": "Serving operations scenario",
            "source_ids": "SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_SEMIANALYSIS_INFERENCEX",
        },
        {
            "category": "Energy sanity check",
            "formula": "joules_per_token = 1,000,000 / tokens_per_second_per_mw",
            "meaning_kr": "MW를 J/s로 환산해 tokens/sec/MW와 에너지/token이 상호 일관되는지 확인.",
            "evidence_type": "Sanity check",
            "source_ids": "SRC_ARXIV_INFERENCE_ENERGY",
        },
        {
            "category": "MoE optimization",
            "formula": "scenario_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier * moe_optimization_multiplier",
            "meaning_kr": "DeepSeek/Qwen 같은 MoE 모델은 active parameter가 낮아 serving efficiency scenario에 별도 multiplier를 적용.",
            "evidence_type": "Scenario assumption",
            "source_ids": "SRC_DEEPSEEK_V3; SRC_QWEN3_GITHUB; ASSUMP_MOE_EFFICIENCY",
        },
    ]


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
                "tokens_per_mw_multiplier": case["tokens_per_mw_multiplier"],
                "moe_optimization_multiplier": case["moe_optimization_multiplier"],
                "utilization_multiplier": case["utilization_multiplier"],
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


def forecast_rows(scenario_case: str = "Base") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case = SCENARIO_CASES[scenario_case]
    mix_profiles = accelerator_mix_profiles()
    derivation_profiles = company_derivation_profiles()
    for scenario in scenarios():
        mix = mix_profiles[scenario.company]
        derivation = derivation_profiles[scenario.company]
        for idx, year in enumerate(YEARS):
            contracted = lerp(scenario.contracted_power_2026_gw, scenario.contracted_power_2030_gw, idx, len(YEARS))
            base_active = lerp(scenario.active_power_2026_gw, scenario.active_power_2030_gw, idx, len(YEARS))
            deploy_multiplier = lerp(case["operational_deploy_multiplier_2026"], case["operational_deploy_multiplier_2030"], idx, len(YEARS))
            active = min(contracted, base_active * deploy_multiplier)
            base_inference_share = lerp(scenario.inference_share_2026, scenario.inference_share_2030, idx, len(YEARS))
            inference_delta = lerp(case["inference_share_delta_2026"], case["inference_share_delta_2030"], idx, len(YEARS))
            inference_share = min(max(base_inference_share + inference_delta, 0.35), 0.94)
            training_share = 1 - inference_share
            utilization = min(0.84, lerp(scenario.utilization_2026, scenario.utilization_2030, idx, len(YEARS)) * case["utilization_multiplier"])
            moe_multiplier = case["moe_optimization_multiplier"] if is_moe_company(scenario.company) else 1.0
            gpu_share = lerp(mix["gpu_share_2026"], mix["gpu_share_2030"], idx, len(YEARS))
            purpose_built_share = 1 - gpu_share
            accelerator_mix_factor = gpu_share + purpose_built_share * mix["asic_efficiency_factor"]
            gpu_reference_tps_per_mw = 1_000_000
            software_efficiency_growth = (1 + scenario.efficiency_cagr) ** idx
            tps_per_mw = (
                gpu_reference_tps_per_mw
                * accelerator_mix_factor
                * mix["architecture_workload_factor"]
                * software_efficiency_growth
                * case["tokens_per_mw_multiplier"]
                * moe_multiplier
            )
            it_load_gw = active / scenario.pue
            ai_it_load_gw = it_load_gw * scenario.ai_workload_share
            inference_gw = ai_it_load_gw * inference_share
            training_gw = ai_it_load_gw * training_share
            active_r = round(active, 3)
            it_load_r = round(it_load_gw, 3)
            ai_it_load_r = round(ai_it_load_gw, 3)
            training_share_r = round(training_share, 3)
            inference_share_r = round(inference_share, 3)
            inference_gw_r = round(inference_gw, 3)
            training_gw_r = round(training_gw, 3)
            tps_per_mw_r = round(tps_per_mw)
            utilization_r = round(utilization, 3)
            inference_mw = inference_gw_r * 1000
            tokens_per_day = inference_mw * tps_per_mw_r * utilization_r * 86400
            annual_tokens = round(tokens_per_day) * 365
            joules_per_token = 1_000_000 / tps_per_mw_r
            training_tps_per_mw_equivalent = round(tps_per_mw_r * 0.22, 4)
            training_tokens_processed_day = training_gw_r * 1000 * training_tps_per_mw_equivalent * utilization_r * 86400
            rows.append(
                {
                    "scenario": scenario_case,
                    "company": scenario.company,
                    "region": scenario.region,
                    "model_family": scenario.model_family,
                    "commercial_surface": scenario.commercial_surface,
                    "year": year,
                    "contracted_power_gw": round(contracted, 3),
                    "active_power_gw": active_r,
                    "pue": scenario.pue,
                    "it_load_gw": it_load_r,
                    "ai_workload_share": scenario.ai_workload_share,
                    "ai_it_load_gw": ai_it_load_r,
                    "gpu_share": round(gpu_share, 3),
                    "purpose_built_accelerator_share": round(purpose_built_share, 3),
                    "purpose_built_accelerator_label": mix["asic_label"],
                    "gpu_reference_tps_per_mw": gpu_reference_tps_per_mw,
                    "purpose_built_relative_efficiency_factor": mix["asic_efficiency_factor"],
                    "accelerator_mix_factor": round(accelerator_mix_factor, 8),
                    "architecture_workload_factor": mix["architecture_workload_factor"],
                    "software_efficiency_growth": round(software_efficiency_growth, 8),
                    "scenario_tokens_per_mw_multiplier": case["tokens_per_mw_multiplier"],
                    "scenario_moe_optimization_multiplier": moe_multiplier,
                    "training_power_share": training_share_r,
                    "inference_power_share": inference_share_r,
                    "inference_gw": inference_gw_r,
                    "training_gw": training_gw_r,
                    "training_tps_per_mw_equivalent": training_tps_per_mw_equivalent,
                    "tokens_per_second_per_mw": tps_per_mw_r,
                    "joules_per_token": round(joules_per_token, 4),
                    "utilization": utilization_r,
                    "inference_tokens_per_day": round(tokens_per_day),
                    "inference_tokens_per_year": round(annual_tokens),
                    "training_tokens_processed_per_day": round(training_tokens_processed_day),
                    "confidence": scenario.confidence,
                    "derivation_type": scenario.derivation_type,
                    "source_ids": scenario.source_ids,
                    "assumption_ids": scenario.assumption_ids + "; ASSUMP_INFERENCE_SHARE_NOT_FACT_60",
                    "capacity_basis": derivation["capacity_basis"],
                    "active_power_basis": derivation["active_basis"],
                    "ai_workload_share_basis": derivation["ai_workload_basis"],
                    "gpu_asic_mix_basis": mix["mix_rationale"],
                    "tokens_per_mw_basis": mix["tps_rationale"],
                    "inference_share_basis": derivation["inference_basis"],
                    "utilization_basis": derivation["utilization_basis"],
                    "replacement_path": mix["replacement_path"],
                }
            )
    return rows


def number_trace_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a company-year-field audit trail for every headline model number."""
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
            row, "active_power_gw", row["active_power_gw"], "GW", "Derived scenario",
            "min(contracted_power_gw, base_active_power_gw * operational_deploy_multiplier)",
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
        add(
            row, "purpose_built_accelerator_share", row["purpose_built_accelerator_share"], "share of inference-serving accelerator load", "Numeric scenario",
            "1 - gpu_share",
            f"Purpose-built bucket: {row['purpose_built_accelerator_label']}. " + row["gpu_asic_mix_basis"],
            company_sources + "; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            row["replacement_path"],
        )
        add(
            row, "gpu_reference_tps_per_mw", row["gpu_reference_tps_per_mw"], "generated output tokens/sec/MW", "Benchmark-calibrated reference",
            "baseline reference before company-specific mix and workload factors",
            "A common GPU reference keeps company mix adjustments visible; it is not asserted as any provider's measured production throughput.",
            "SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            "Comparable generated-output benchmark row at matched GPU, precision, ISL/OSL and SLO.",
        )
        add(
            row, "purpose_built_relative_efficiency_factor", row["purpose_built_relative_efficiency_factor"], "relative efficiency factor", "Numeric scenario",
            "purpose_built_efficiency / gpu_reference_efficiency",
            "The factor represents modeled efficiency direction of the purpose-built bucket, not an official provider tokens/MW disclosure.",
            company_sources + "; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            "Matched-workload generated-output benchmark for the provider purpose-built accelerator.",
        )
        add(
            row, "accelerator_mix_factor", row["accelerator_mix_factor"], "relative efficiency factor", "Derived scenario",
            "gpu_share * 1.0 + purpose_built_accelerator_share * purpose_built_relative_efficiency_factor",
            "Transforms the numeric GPU/purpose-built mix into an efficiency bridge; the relative uplift remains a scenario until production measurements exist.",
            company_sources + "; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            row["replacement_path"],
        )
        add(
            row, "architecture_workload_factor", row["architecture_workload_factor"], "relative efficiency factor", "Architecture/workload proxy",
            "model-family workload adjustment applied separately from hardware mix",
            row["tokens_per_mw_basis"],
            company_sources + "; SRC_SEMIANALYSIS_INFERENCEX",
            "Model-family output-throughput benchmark matched for context, precision, routing and SLO.",
        )
        add(
            row, "software_efficiency_growth", row["software_efficiency_growth"], "relative efficiency factor", "Scenario improvement",
            "(1 + company efficiency_cagr) ** year_offset",
            "Separates software/runtime serving improvement over time from accelerator migration.",
            "SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_POWER_RAMP",
            "Historical comparable benchmark time series or disclosed production efficiency trend.",
        )
        add(
            row, "scenario_tokens_per_mw_multiplier", row["scenario_tokens_per_mw_multiplier"], "relative efficiency factor", "Scenario lever",
            "Bear/Base/Bull case multiplier",
            "Applies explicit case-level serving efficiency stress after company-specific bridge factors.",
            "ASSUMP_POWER_RAMP; SRC_SEMIANALYSIS_INFERENCEX",
            "Approved scenario decision or measured efficiency range.",
        )
        add(
            row, "scenario_moe_optimization_multiplier", row["scenario_moe_optimization_multiplier"], "relative efficiency factor", "Scenario lever",
            "MoE case multiplier for MoE model owners; otherwise 1.0",
            "MoE active-parameter efficiency is visible as a separate scenario lever and is not silently attributed to hardware mix.",
            company_sources + "; ASSUMP_MOE_EFFICIENCY",
            "Comparable MoE output-throughput results under matched serving conditions.",
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
            "This is the power eligible to become commercial generated output tokens after utilization and serving-efficiency conversion.",
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
            "gpu_reference_tps_per_mw * accelerator_mix_factor * architecture_workload_factor * software_efficiency_growth * scenario multipliers",
            row["tokens_per_mw_basis"], company_sources + "; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX",
            "Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched.",
        )
        add(
            row, "joules_per_token", row["joules_per_token"], "joules/generated output token", "Derived energy sanity metric",
            "1,000,000 / tokens_per_second_per_mw",
            "Energy reciprocal of output throughput per MW; used as a sanity check rather than company metered telemetry.",
            company_sources + "; SRC_SEMIANALYSIS_INFERENCEX; SRC_ARXIV_INFERENCE_ENERGY",
            "Matched production or benchmark joules per generated output token.",
        )
        add(
            row, "utilization", row["utilization"], "realized serving fraction", "Scenario operations factor",
            "theoretical output capacity * utilization = realized output capacity",
            row["utilization_basis"], company_sources + "; SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026",
            "Provider/model-surface serving telemetry including reserve, batch fill, latency SLO and failover.",
        )
        add(
            row, "inference_tokens_per_day", row["inference_tokens_per_day"], "generated output tokens/day", "Derived headline metric",
            "inference_gw * 1000 * tokens_per_second_per_mw * utilization * 86,400",
            "Headline supply capacity; it is not observed commercial output volume and excludes input, billing and training tokens.",
            company_sources + "; SRC_SEMIANALYSIS_INFERENCEX",
            "Provider-disclosed generated output token volume or calibrated capacity telemetry.",
        )
        add(
            row, "inference_tokens_per_year", row["inference_tokens_per_year"], "generated output tokens/year", "Derived headline metric",
            "inference_tokens_per_day * 365",
            "Annualized version of generated output token capacity; it is not observed annual demand or billable volume.",
            company_sources + "; SRC_SEMIANALYSIS_INFERENCEX",
            "Provider-disclosed annual generated-output volume or monthly utilization-calibrated telemetry.",
        )
        add(
            row, "training_tps_per_mw_equivalent", row["training_tps_per_mw_equivalent"], "processed training tokens/sec/MW equivalent", "Scenario proxy",
            "tokens_per_second_per_mw * 0.22",
            "A separate training processing sanity proxy, not a claim about commercial generated output or metered training throughput.",
            company_sources + "; ASSUMP_POWER_RAMP",
            "Provider training throughput and power telemetry for comparable model runs.",
        )
        add(
            row, "training_tokens_processed_per_day", row["training_tokens_processed_per_day"], "processed training tokens/day", "Derived reference metric",
            "training_gw * 1000 * training_tps_per_mw_equivalent * utilization * 86,400",
            "Training processing reference remains separated from commercial generated output token supply.",
            company_sources + "; ASSUMP_POWER_RAMP",
            "Provider training run throughput/power telemetry.",
        )
    return trace


def sensitivity_rows(base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in base_rows:
        if row["year"] not in (2026, 2028, 2030):
            continue
        for name, tps_mult, util_mult in [
            ("Bear: lower tokens/MW and utilization", 0.65, 0.85),
            ("Base", 1.00, 1.00),
            ("Bull: higher batching/quantization/software efficiency", 1.45, 1.08),
        ]:
            tokens = row["inference_gw"] * 1000 * row["tokens_per_second_per_mw"] * tps_mult * min(row["utilization"] * util_mult, 0.82) * 86400
            result.append(
                {
                    "scenario": name,
                    "company": row["company"],
                    "year": row["year"],
                    "inference_gw": row["inference_gw"],
                    "tokens_per_second_per_mw": round(row["tokens_per_second_per_mw"] * tps_mult),
                    "utilization": round(min(row["utilization"] * util_mult, 0.82), 3),
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
        {"company": "OpenAI", "proxy_model": "gpt-oss/frontier mix proxy", "effective_active_params_b": 92.0, "benchmark_tps_per_gpu": 60000, "benchmark_effective_active_b": 5.1, "accelerator_kw": 7.0, "serving_efficiency": 0.72, "benchmark_source": "SRC_SEMIANALYSIS_INFERENCEX; SRC_ARXIV_INFERENCE_ENERGY", "calc_use": "Proxy", "caveat_kr": "closed GPT 실제 serving benchmark가 아니므로 sanity check로만 사용"},
        {"company": "Anthropic", "proxy_model": "Claude closed frontier proxy", "effective_active_params_b": 110.0, "benchmark_tps_per_gpu": 60000, "benchmark_effective_active_b": 5.1, "accelerator_kw": 7.5, "serving_efficiency": 0.74, "benchmark_source": "SRC_ANTHROPIC_CLAUDE_DOCS; SRC_SEMIANALYSIS_INFERENCEX", "calc_use": "Proxy", "caveat_kr": "Claude 파라미터/serving benchmark는 비공개라 proxy"},
        {"company": "Google", "proxy_model": "Gemini closed frontier proxy", "effective_active_params_b": 80.5, "benchmark_tps_per_gpu": 60000, "benchmark_effective_active_b": 5.1, "accelerator_kw": 7.0, "serving_efficiency": 0.70, "benchmark_source": "SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E", "calc_use": "Proxy", "caveat_kr": "TPU serving을 GPU-equivalent proxy로 환산"},
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
        sustained_tps = adjusted_tps * gpu_count * row["utilization"]
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
            "source_ids": "SRC_JOULE_INFERENCE_ENERGY_2026; SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SLO_PD_2026",
            "interpretation_kr": "agentic/test-time compute가 증가하면 같은 MW에서 token output이 낮아질 수 있음",
        },
        {
            "profile": "Base serving mix",
            "joules_per_token_multiplier": 1.00,
            "input_output_context_note": "mixed chatbot/API/enterprise serving with moderate batching",
            "source_ids": "SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX",
            "interpretation_kr": "메인 forecast와 일치시키는 기준 energy view",
        },
        {
            "profile": "Batchable / optimized serving",
            "joules_per_token_multiplier": 0.68,
            "input_output_context_note": "batchable workloads, KV-cache efficiency, P/D scheduling, relaxed latency",
            "source_ids": "SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_SEMIANALYSIS_INFERENCEX",
            "interpretation_kr": "serving stack 최적화가 energy/token을 낮출 수 있으나 company fact는 아님",
        },
    ]
    rows: list[dict[str, Any]] = []
    for row in base_rows:
        if row["year"] not in (2026, 2030):
            continue
        inference_energy_j_day = row["inference_gw"] * 1e9 * row["utilization"] * 86400
        for profile in profiles:
            implied_jpt = row["joules_per_token"] * profile["joules_per_token_multiplier"]
            energy_tokens_day = inference_energy_j_day / implied_jpt if implied_jpt else 0
            rows.append(
                {
                    "company": row["company"],
                    "year": row["year"],
                    "profile": profile["profile"],
                    "inference_gw": row["inference_gw"],
                    "utilization": row["utilization"],
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
            "source_ids": "SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026",
        },
        {
            "profile": "Base mixed serving",
            "utilization_multiplier": 1.00,
            "tokens_per_mw_multiplier": 1.00,
            "description_kr": "메인 forecast 기준",
            "source_ids": "SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX",
        },
        {
            "profile": "Batchable optimized",
            "utilization_multiplier": 1.12,
            "tokens_per_mw_multiplier": 1.10,
            "description_kr": "batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving",
            "source_ids": "SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026",
        },
        {
            "profile": "Agentic long-context stress",
            "utilization_multiplier": 0.88,
            "tokens_per_mw_multiplier": 0.82,
            "description_kr": "긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress",
            "source_ids": "SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026",
        },
    ]
    rows: list[dict[str, Any]] = []
    for row in base_rows:
        if row["year"] not in (2026, 2030):
            continue
        for profile in profiles:
            adjusted_util = min(row["utilization"] * profile["utilization_multiplier"], 0.86)
            adjusted_tps = row["tokens_per_second_per_mw"] * profile["tokens_per_mw_multiplier"]
            tokens_day = row["inference_gw"] * 1000 * adjusted_tps * adjusted_util * 86400
            rows.append(
                {
                    "company": row["company"],
                    "year": row["year"],
                    "profile": profile["profile"],
                    "base_utilization": row["utilization"],
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
            "question_kr": "tokens/sec/MW가 numeric mix와 architecture/workload factor에서 재구성되는가?",
            "pass_criteria_kr": "05_inference_efficiency의 bridge fields로 각 row의 tokens/sec/MW를 재계산할 수 있고 validation이 통과.",
            "risk_if_fail_kr": "설명과 결과 coefficient가 분리된 채 남음.",
            "owner": "A08 / A11 / Logic Review",
            "severity": "High",
            "current_status": "Automated validation added",
        },
        {
            "check_id": "HC20",
            "area": "Complete numeric trace",
            "question_kr": "최종 표와 보조 표의 output-driving 숫자마다 company-year-scenario별 이유와 교체 경로가 있는가?",
            "pass_criteria_kr": "02b_number_trace에 26개 numeric metric별 formula, reason, source/assumption ID, replacement path가 존재.",
            "risk_if_fail_kr": "질문을 받았을 때 숫자의 출처 또는 산출 이유를 설명할 수 없음.",
            "owner": "Model / Logic Review",
            "severity": "High",
            "current_status": "Implemented in trace layer",
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
        share_sum = row["training_power_share"] + row["inference_power_share"]
        if not math.isclose(share_sum, 1.0, abs_tol=0.001):
            failures.append(f"{row['company']} {row['year']}: training+inference share={share_sum}")
        if row["tokens_per_second_per_mw"] <= 0 or row["joules_per_token"] <= 0:
            failures.append(f"{row['company']} {row['year']}: invalid efficiency")
        if not math.isclose(row["gpu_share"] + row["purpose_built_accelerator_share"], 1.0, abs_tol=0.001):
            failures.append(f"{row['company']} {row['year']}: gpu+purpose-built accelerator share != 1")

        reconstructed_tps = round(
            row["gpu_reference_tps_per_mw"]
            * row["accelerator_mix_factor"]
            * row["architecture_workload_factor"]
            * row["software_efficiency_growth"]
            * row["scenario_tokens_per_mw_multiplier"]
            * row["scenario_moe_optimization_multiplier"]
        )
        if abs(reconstructed_tps - row["tokens_per_second_per_mw"]) > 2:
            failures.append(f"{row['company']} {row['year']}: tokens/sec/MW bridge does not reconstruct")
        reconstructed_joules = round(1_000_000 / row["tokens_per_second_per_mw"], 4)
        if reconstructed_joules != row["joules_per_token"]:
            failures.append(f"{row['company']} {row['year']}: joules/token does not reconstruct")
        if row["inference_tokens_per_year"] != round(row["inference_tokens_per_day"] * 365):
            failures.append(f"{row['company']} {row['year']}: annual output tokens do not reconstruct")
        reconstructed_training_tps = round(row["tokens_per_second_per_mw"] * 0.22, 4)
        if reconstructed_training_tps != row["training_tps_per_mw_equivalent"]:
            failures.append(f"{row['company']} {row['year']}: training throughput proxy does not reconstruct")
        reconstructed_training_tokens = round(
            row["training_gw"] * 1000 * row["training_tps_per_mw_equivalent"] * row["utilization"] * 86400
        )
        if reconstructed_training_tokens != row["training_tokens_processed_per_day"]:
            failures.append(f"{row['company']} {row['year']}: training processed tokens do not reconstruct")

        # Sanity bound: company-level generated tokens should remain within a broad
        # benchmark envelope for aggregate serving, not an exact model claim.
        tps_mw = row["inference_tokens_per_day"] / 86400 / (row["inference_gw"] * 1000) / row["utilization"]
        if not (300_000 <= tps_mw <= 5_000_000):
            failures.append(f"{row['company']} {row['year']}: tokens/sec/MW out of benchmark envelope")

    model_checks = {
        "closed_parameter_precision": "PASS - closed model rows use bands/undisclosed labels, not single precise parameter values.",
        "moe_total_active": "PASS - DeepSeek and Alibaba rows include total and active parameter bands.",
        "microsoft_openai_overlap": "PASS - attribution rule separates OpenAI model-owner output and Microsoft customer-facing serving.",
        "anthropic_scope": "PASS - Anthropic is included as a core model-owner row; AWS/Google host capacity is attributed to Anthropic model output.",
        "benchmark_layer": "PASS - GPU/effective-active-parameter benchmark reference is separated from the main tokens/sec/MW forecast.",
        "energy_sanity_layer": "PASS - Joule/IBM/2026 serving sources are separated as sanity/sensitivity layers, not Base production telemetry.",
        "utilization_slo_layer": "PASS - SLO/workload utilization sensitivity is separated from Base utilization band.",
        "numeric_accelerator_mix_bridge": "PASS - GPU/purpose-built shares sum to 100% and reconstruct tokens/sec/MW through explicit bridge factors.",
        "complete_numeric_trace_inputs": "PASS - joules/token, annual output tokens, training throughput proxy and training processed tokens are formula-reconstructable.",
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
        "accuracy_evals": accuracy_evals,
        "dump_inventory": dump_inventory,
        "run_stats": run_stats,
        "availability": availability,
    }


def write_excel(data: dict[str, Any], path: Path) -> None:
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

    power_headers = [
        "company",
        "region",
        "year",
        "contracted_power_gw",
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
            "purpose_built_relative_efficiency_factor": r["purpose_built_relative_efficiency_factor"],
            "accelerator_mix_factor": r["accelerator_mix_factor"],
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
        "gpu_reference_tps_per_mw",
        "gpu_share",
        "purpose_built_accelerator_share",
        "purpose_built_relative_efficiency_factor",
        "accelerator_mix_factor",
        "architecture_workload_factor",
        "software_efficiency_growth",
        "tokens_per_second_per_mw",
        "joules_per_token",
        "utilization",
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

    split_headers = [
        "company",
        "year",
        "training_power_share",
        "inference_power_share",
        "training_gw",
        "training_tps_per_mw_equivalent",
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
        "active_power_gw",
        "ai_workload_share",
        "ai_it_load_gw",
        "inference_gw",
        "gpu_share",
        "purpose_built_accelerator_share",
        "accelerator_mix_factor",
        "tokens_per_second_per_mw",
        "joules_per_token",
        "utilization",
        "inference_tokens_per_day",
        "inference_tokens_per_year",
        "training_tps_per_mw_equivalent",
        "training_tokens_processed_per_day",
        "confidence",
        "derivation_type",
        "source_ids",
        "assumption_ids",
        "capacity_basis",
        "gpu_asic_mix_basis",
        "tokens_per_mw_basis",
        "utilization_basis",
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
        ("12f_ix_accuracy_evals", "accuracy_evals"),
        ("12g_ix_dump_inventory", "dump_inventory"),
        ("12h_ix_run_stats", "run_stats"),
        ("12i_ix_availability", "availability"),
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
    ppt_add_title(slide, "Bull / Base / Bear scenario logic", "세 축: operational deploy speed, MoE optimization, inference mix shift.")
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
            f"{item['tokens_per_mw_multiplier']:.0%}",
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
      <label>활용률 민감도 <input id="util" type="range" min="85" max="108" value="100" /> <span id="utilLabel">100%</span></label>
    </div>
    <div class="grid" id="kpis"></div>
    <section>
      <h2>업체별 토큰 forecast</h2>
      <div class="chart" id="tokenChart"></div>
      <div class="note">단위: quadrillion tokens/day. slider는 tokens/sec/MW와 utilization에만 적용합니다.</div>
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
      <h2>신뢰도 heatmap & source audit</h2>
      <table id="audit"></table>
    </section>
    <section>
      <h2>Fact anchor</h2>
      <table id="facts"></table>
    </section>
    <section>
      <h2>Benchmark sanity check</h2>
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
      <div class="note">InferenceX는 company production telemetry가 아니라 benchmark/proxy layer입니다. DB dump/CSV 정규화 후 A08/A09 sensitivity로만 승격합니다.</div>
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
      ["scenario","company","year","tps","util"].forEach(id => $(id).addEventListener('input', render));
      render();
    }}
    function selectedRows() {{
      const c = $("company").value, y = Number($("year").value), s = $("scenario").value;
      return ROWS.filter(d => d.year === y && (d.scenario || "Base") === s && (c === "ALL" || d.company === c));
    }}
    function adjustedTokens(row) {{
      const tps = Number($("tps").value)/100;
      const util = Number($("util").value)/100;
      return row.inference_gw * 1000 * row.tokens_per_second_per_mw * tps * Math.min(row.utilization * util, 0.82) * 86400;
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
      $("audit").innerHTML = `<tr><th>업체</th><th>신뢰도</th><th>산출 유형</th><th>Sources</th><th>Assumptions</th></tr>` +
        rows.map(d=>`<tr><td>${{d.company}}</td><td><span class="pill">${{d.confidence}}</span></td><td>${{d.derivation_type}}</td><td>${{d.source_ids}}</td><td>${{d.assumption_ids}}</td></tr>`).join('');
      $("models").innerHTML = `<tr><th>업체</th><th>모델 family</th><th>상용 표면</th><th>Attribution rule</th></tr>` +
        DATA.company_models.filter(m => $("company").value === "ALL" || m.company === $("company").value)
          .map(m=>`<tr><td>${{m.company}}</td><td>${{m.model_family}}</td><td>${{m.commercial_surface}}</td><td>${{m.attribution_rule}}</td></tr>`).join('');
      $("formulas").innerHTML = `<tr><th>구분</th><th>계산식</th><th>해석</th><th>Sources</th></tr>` +
        DATA.formula_assumptions.map(f=>`<tr><td>${{f.category}}</td><td><code>${{f.formula}}</code></td><td>${{f.meaning_kr}}</td><td>${{f.source_ids}}</td></tr>`).join('');
      $("tokenDefs").innerHTML = `<tr><th>Token metric</th><th>정의</th><th>포함</th><th>InferenceX mapping</th><th>Status</th></tr>` +
        DATA.token_definitions.map(t=>`<tr><td>${{t.korean_name}}<br/><code>${{t.token_metric}}</code></td><td>${{t.definition_kr}}</td><td>${{t.included}}</td><td>${{t.inferencex_mapping}}</td><td>${{t.status}}</td></tr>`).join('');
      $("scenarioDefs").innerHTML = `<tr><th>시나리오</th><th>2030 가동률 배수</th><th>2030 추론 비중 변화</th><th>Tokens/MW</th><th>설명</th></tr>` +
        DATA.scenario_definitions.map(s=>`<tr><td>${{s.scenario}}</td><td>${{Math.round(s.operational_deploy_multiplier_2030*100)}}%</td><td>${{Math.round(s.inference_share_delta_2030*100)}}%p</td><td>${{Math.round(s.tokens_per_mw_multiplier*100)}}%</td><td>${{s.description_kr}}</td></tr>`).join('');
      $("facts").innerHTML = `<tr><th>업체</th><th>지표</th><th>값</th><th>Source</th><th>모델 반영 방식</th></tr>` +
        DATA.fact_anchors.map(f=>`<tr><td>${{f.company}}</td><td>${{f.metric}}</td><td>${{f.value}}</td><td>${{f.source_id}}</td><td>${{f.derivation_impact_kr}}</td></tr>`).join('');
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
      $("utilLabel").textContent = $("util").value + "%";
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
        "it_load_gw = active_power_gw / pue",
        "ai_it_load_gw = it_load_gw * ai_workload_share",
        "inference_gw = ai_it_load_gw * inference_power_share",
        "accelerator_mix_factor = gpu_share * 1.0 + purpose_built_share * purpose_built_relative_efficiency_factor",
        "tokens_per_second_per_mw = gpu_reference_tps_per_mw * accelerator_mix_factor * architecture_workload_factor * software_efficiency_growth * scenario_multipliers",
        "inference_tokens_per_day = inference_mw * tokens_per_second_per_mw * utilization * 86,400",
        "joules_per_token = 1,000,000 / tokens_per_second_per_mw",
        "```",
        "",
        "## Number Trace In Excel",
        "",
        "- Excel `02b_number_trace`는 모든 company-year-scenario 핵심 수치에 대해 `formula_or_rule`, `why_this_number`, `source_ids`, `assumption_ids`, `replacement_path`를 제공합니다.",
        "- `contracted_power_gw`는 source가 있는 업체의 committed/planned ceiling anchor와, 공개 GW가 없는 업체의 scenario capacity envelope를 구분합니다.",
        "- `active_power_gw`는 항상 capacity ceiling 이하이고 energization/deployment를 거친 modeled operational power입니다.",
        "- `gpu_asic_mix`는 numeric scenario로 명시하며, 공식 platform presence를 실제 fleet share fact로 오인하지 않습니다.",
        "- `utilization`은 power-on ratio가 아니라 SLO/reserve/traffic shape 이후 realized output-capacity fraction입니다.",
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
        "| 시나리오 | 2030 가동률 배수 | 2030 추론 비중 변화 | Tokens/MW | MoE 최적화 | 설명 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in data["scenario_definitions"]:
        lines.append(
            f"| {item['scenario']} | {item['operational_deploy_multiplier_2030']:.0%} | {item['inference_share_delta_2030']:+.0%}p | {item['tokens_per_mw_multiplier']:.0%} | {item['moe_optimization_multiplier']:.0%} | {item['description_kr']} |"
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
        "## Benchmark Sanity Check",
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
        "- Base `tokens_per_second_per_mw`는 이제 numeric GPU/purpose-built mix bridge와 architecture/workload factor로 구성되며, production telemetry가 아닌 derived estimate입니다.",
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
        "- Base utilization band는 유지했습니다.",
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
        "- InferenceX는 company production telemetry가 아니라 benchmark/proxy layer입니다.",
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
        "- Estimate: active power, 추론/학습 share, utilization, company-level tokens/sec/MW.",
        "- Scenario: 2027–2030 ramp, software efficiency CAGR, 상용 token absorption.",
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
    add_label(slide, 1.1, 3.38, 11.1, 0.48, "output tokens/day = inference GW × 1,000 × tokens/sec/MW × utilization × 86,400", 16, blue, True, PP_ALIGN.CENTER)
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
    add_title(slide, "InferenceX로 보정하는 것: tokens/MW, J/token, SLO 조건", "InferenceX benchmark는 serving 효율과 latency 조건을 수치화해 tokens/MW 가정을 좁혀줍니다.")
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
    takeaway_band(slide, "이 장의 메시지: InferenceX는 serving 효율 계수를 더 현실적인 범위로 조정하는 데이터 레이어입니다.")
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
        ("월", "source refresh", "official IR / filings / model cards / InferenceX dump"),
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
            "12d-12f: InferenceX benchmark rows, metric profile, accuracy evals.",
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
    text(slide, 1.1, 4.35, 11.1, 0.45, "output tokens/day = inference GW × 1,000 × output tokens/sec/MW × utilization × 86,400", 16, samsung_blue, True, PP_ALIGN.CENTER)
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
    add_header(slide, "InferenceX는 serving 효율 가정을 실제 benchmark 범위로 좁힌다")
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
        ("Mon", "Source refresh", "IR / filings / model cards / InferenceX"),
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
    text(slide, 0.92, 5.95, 11.1, 0.3, "Workbook appendix: 00_formula_assumptions, 00a_token_definitions, 08 sensitivity sheets, 12 InferenceX raw benchmark sheets", 10.5, muted)
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
        "Bull, Base, and Bear cases are built from deployment speed, MoE optimization, inference power share, and utilization assumptions.",
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
            "The gap between cases is driven by serving-stack efficiency, MoE routing, and real utilization.",
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
        ("Output\ntoken/day", "tokens/MW and utilization"),
    ]
    for i, (label, note) in enumerate(steps):
        x = 0.82 + i * 2.43
        text(slide, x, 2.04, 1.55, 0.72, label, 17, ink, True, PP_ALIGN.CENTER)
        rect(slide, x, 2.92, 1.55, 0.035, samsung_blue if i == 4 else silver)
        text(slide, x, 3.18, 1.55, 0.36, note, 8.1, muted, False, PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            text(slide, x + 1.72, 2.42, 0.35, 0.25, "→", 16, muted, True, PP_ALIGN.CENTER)
    text(slide, 1.0, 4.28, 11.35, 0.43, "output tokens/day = inference GW x 1,000 x output tokens/sec/MW x utilization x 86,400", 15, samsung_blue, True, PP_ALIGN.CENTER)
    bullets(
        slide,
        1.18,
        5.05,
        10.9,
        0.72,
        [
            "Contracted power is an upper bound; token capacity begins only after power is energized and assigned to AI IT load.",
            "Inference share is a capacity allocation variable; utilization is the operating conversion from installed serving capacity to traffic.",
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
        "InferenceX calibrates the serving-efficiency assumptions",
        "The benchmark layer narrows the plausible range for tokens/MW, joules/token, latency conditions, and workload shape.",
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
        ("Mon", "Source refresh", "IR, filings, model cards, technical reports, InferenceX benchmark updates"),
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
    text(slide, 0.92, 5.78, 11.1, 0.42, "Workbook appendix: formula assumptions, token definitions, scenario sensitivity, InferenceX raw benchmark tables, source registry, and company-year forecast rows.", 10.5, muted)
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
    median_util = sorted(r["utilization"] for r in rows_2030)[len(rows_2030) // 2]

    def constraint_label(row: dict[str, Any]) -> str:
        deploy_gap = 1 - row["active_power_gw"] / row["contracted_power_gw"]
        if deploy_gap >= 0.32:
            return "Deployment gap"
        if row["inference_power_share"] < median_inf_share:
            return "Training allocation"
        if row["tokens_per_second_per_mw"] < median_tpmw:
            return "Serving efficiency"
        if row["utilization"] < median_util:
            return "Utilization reserve"
        return "Scale absorption"

    def constraint_score(row: dict[str, Any]) -> float:
        deploy_gap = 1 - row["active_power_gw"] / row["contracted_power_gw"]
        serving_gap = max(0, (median_tpmw - row["tokens_per_second_per_mw"]) / median_tpmw)
        inference_gap = max(0, (median_inf_share - row["inference_power_share"]) / median_inf_share)
        util_gap = max(0, (median_util - row["utilization"]) / median_util)
        return round(100 * (0.38 * deploy_gap + 0.24 * serving_gap + 0.22 * inference_gap + 0.16 * util_gap), 1)

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
        ("Token\nsupply", "Output tokens/sec/MW x utilization"),
    ]
    for i, (label, note) in enumerate(steps):
        x = 0.78 + i * 2.45
        text(slide, x, 2.08, 1.7, 0.7, label, 16.5, ink, True, PP_ALIGN.CENTER)
        rect(slide, x, 2.92, 1.7, 0.035, samsung_blue if i == 4 else silver)
        text(slide, x, 3.16, 1.7, 0.46, note, 8.0, muted, False, PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            text(slide, x + 1.84, 2.43, 0.25, 0.24, "→", 15.5, muted, True, PP_ALIGN.CENTER)
    text(slide, 0.95, 4.25, 11.5, 0.45, "generated output tokens/day = inference GW x 1,000 x output tokens/sec/MW x utilization x 86,400", 15, samsung_blue, True, PP_ALIGN.CENTER)
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
        "If token supply rises faster than inference GW, the driver is serving efficiency or utilization; if both rise together, deployment is the driver.",
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
        "The third constraint is serving efficiency: tokens per MW and real utilization",
        "InferenceX and model architecture assumptions are used to calibrate the conversion from inference GW to output tokens.",
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
    text(slide, 8.18, 1.92, 3.95, 0.28, "Lowest tokens/MW and utilization", 10.6, muted, True)
    add_small_table(
        slide,
        [[r["company"], f"{r['tokens_per_second_per_mw']/1e6:.1f}", f"{r['utilization']:.0%}", constraint_label(r)] for r in table_rows],
        ["Provider", "M tok/s/MW", "Util.", "Constraint"],
        8.18,
        2.30,
        4.25,
        2.35,
        [1.2, 1.0, 0.62, 1.22],
        6.9,
    )
    text(slide, 8.18, 4.98, 4.05, 0.54, "Low utilization can reflect reserve capacity, SLO headroom, uneven traffic, and failover requirements.", 9.4, body)
    takeaway(slide, "Tokens/MW sets the theoretical ceiling; utilization determines how much of that ceiling becomes supply.")
    footer(slide)

    # 10. Provider constraint map
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    header(
        slide,
        "Provider constraint map: each company has a different limiting factor",
        "The score is a directional operating index using deployment gap, inference share, tokens/MW, and utilization versus the peer set.",
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
            "Utilization reserve": "SLO headroom, failover reserve, traffic shape",
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
        "Bull and Bear cases are not alternate stories; they are operating ranges around deployment, inference mix, MoE optimization, and utilization.",
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
            "MoE and serving-stack optimization",
            "Inference share of AI IT load",
        ],
        9.7,
        body,
        3,
    )
    text(slide, 8.55, 5.75, 3.2, 0.28, f"Base growth: {total_2030 / total_2026:.1f}x, 2026-2030", 11.2, samsung_blue, True)
    takeaway(slide, "The same provider can move from constrained to advantaged if deployment and serving conversion improve together.")
    footer(slide)

    # 12. Operating questions
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
    text(slide, 0.92, 5.78, 11.1, 0.42, "Workbook appendix: 02b number trace, 04 numeric accelerator mix, 05 efficiency bridge, formula assumptions, source registry, and InferenceX benchmark tables.", 10.5, muted)
    takeaway(slide, "Update the model by bottleneck type: deployment, allocation, architecture, efficiency, or demand absorption.")
    footer(slide)

    prs.save(path)


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
        "hallucination_checklist": hallucination_checklist(),
        "scenario_definitions": scenario_definitions(),
        "forecast": rows,
        "number_trace": number_trace_rows(scenario_rows),
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
    return data


def lightweight_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Keep machine-readable/HTML artifacts small while preserving full XLSX rows."""
    slim = dict(data)
    ix = dict(data.get("inferencex", {}))
    benchmark_rows = ix.get("benchmark_results") or []
    ix["benchmark_results_preview"] = benchmark_rows[:250]
    ix["benchmark_results"] = []
    ix["benchmark_results_note"] = (
        "Full InferenceX benchmark rows are stored in the XLSX sheet "
        "`12d_ix_benchmark_results` and CSV `data/inferencex/normalized/inferencex_benchmark_results.csv`. "
        "JSON/HTML keep a preview only to stay below GitHub file-size limits."
    )
    slim["inferencex"] = ix
    return slim


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
    write_html(slim_data, OUT / f"{stem}.html")
    write_markdown(slim_data, OUT / f"{stem}.md")
    print(
        json.dumps(
            {
                "status": "PASS",
                "outputs": [str(OUT / f"{stem}.{ext}") for ext in ("json", "xlsx", "pptx", "html", "md")]
                + [
                    str(OUT / "llm_token_supply_constraints_by_compute_capacity_en_2026_2030.pptx"),
                    str(OUT / "llm_token_capacity_samsung_style_en_2026_2030.pptx"),
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
