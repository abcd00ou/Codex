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
RUN_DATE = "2026-05-18"
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
    tps_per_mw_2026: float
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
            "NVIDIA GPU, Azure Maia, OpenAI-hosted frontier serving",
            "SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS",
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
            "NVIDIA GPU, MTIA for internal inference acceleration",
            "SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA",
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
            "NVIDIA GPU dominated; custom/partner accelerators TBD",
            "SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE",
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
            "AWS Trainium-heavy hosted capacity, Google TPU/GPU partner capacity",
            "SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE",
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
            "NVIDIA/China-available GPU mix, MoE efficiency emphasis",
            "SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1",
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
            "NVIDIA/China accelerators + cloud serving stack",
            "SRC_QWEN3_GITHUB",
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
            "NVIDIA/China accelerators, Tencent Cloud inference",
            "SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3",
            "Medium for Hunyuan published anchor, Medium-Low for active capacity",
            "Hunyuan 100B+와 2T+ pretraining token은 fact anchor, serving capacity는 scenario.",
        ),
    ]


def scenarios() -> list[CompanyScenario]:
    return [
        CompanyScenario("Microsoft", "US", "Phi / MAI / Copilot model mix", "Copilot + Azure AI", 4.0, 9.0, 1.8, 6.2, 0.55, 0.75, 1_050_000, 0.16, 0.54, 0.68, 1.20, 0.86, "Medium", "Estimate+Scenario", "SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT", "ASSUMP_POWER_RAMP; ASSUMP_MS_OPENAI_ATTRIBUTION"),
        CompanyScenario("Google", "US", "Gemini / Gemma", "Gemini + Workspace + Vertex", 4.5, 8.0, 2.2, 6.8, 0.55, 0.72, 1_250_000, 0.18, 0.56, 0.70, 1.18, 0.88, "Medium-High", "Estimate+Scenario", "SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E", "ASSUMP_TPU_EFFICIENCY; ASSUMP_POWER_RAMP"),
        CompanyScenario("Meta", "US", "Llama / Meta AI", "Meta AI + family apps", 3.5, 7.0, 1.6, 5.8, 0.58, 0.78, 1_120_000, 0.16, 0.55, 0.70, 1.20, 0.87, "Medium", "Estimate+Scenario", "SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA", "ASSUMP_CONSUMER_AI_UTILIZATION; ASSUMP_POWER_RAMP"),
        CompanyScenario("xAI", "US", "Grok", "Grok + X + API", 1.0, 3.0, 0.35, 2.5, 0.45, 0.70, 950_000, 0.17, 0.50, 0.67, 1.22, 0.85, "Medium-Low", "Estimate+Scenario", "SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS", "ASSUMP_CLUSTER_RAMP; ASSUMP_CLOSED_MODEL_BAND"),
        CompanyScenario("OpenAI", "US", "GPT / o-series / ChatGPT", "ChatGPT + API + enterprise", 5.0, 12.0, 1.4, 8.5, 0.58, 0.78, 1_050_000, 0.17, 0.57, 0.71, 1.20, 0.88, "Medium", "Estimate+Scenario", "SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS", "ASSUMP_STARGATE_RAMP; ASSUMP_MS_OPENAI_ATTRIBUTION"),
        CompanyScenario("Anthropic", "US", "Claude Opus / Sonnet / Haiku", "Claude + Bedrock + Vertex", 3.5, 7.0, 1.0, 5.5, 0.52, 0.74, 980_000, 0.16, 0.55, 0.70, 1.18, 0.86, "Medium", "Estimate+Scenario", "SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE", "ASSUMP_POWER_RAMP; ASSUMP_CLOSED_MODEL_BAND"),
        CompanyScenario("DeepSeek", "China", "DeepSeek-V3 / R1", "DeepSeek app/API", 0.5, 1.8, 0.15, 1.2, 0.62, 0.82, 1_450_000, 0.18, 0.48, 0.66, 1.24, 0.82, "Parameter High / Capacity Low-Medium", "Fact+Scenario", "SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1", "ASSUMP_MOE_EFFICIENCY; ASSUMP_CN_CAPACITY_TRANSPARENCY"),
        CompanyScenario("Alibaba", "China", "Qwen / Qwen3", "Model Studio + Qwen API", 1.8, 4.0, 0.65, 3.2, 0.60, 0.80, 1_350_000, 0.17, 0.52, 0.68, 1.23, 0.84, "Medium", "Fact+Scenario", "SRC_QWEN3_GITHUB", "ASSUMP_MOE_EFFICIENCY; ASSUMP_CN_CAPACITY_TRANSPARENCY"),
        CompanyScenario("Tencent", "China", "Hunyuan / Yuanbao", "Yuanbao + WeChat/Tencent Cloud", 1.2, 3.0, 0.45, 2.4, 0.60, 0.80, 1_200_000, 0.16, 0.52, 0.68, 1.23, 0.84, "Medium-Low", "Estimate+Scenario", "SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3", "ASSUMP_CN_CAPACITY_TRANSPARENCY; ASSUMP_APP_EMBEDDING"),
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
    ]


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
            "Google tps_per_mw_2026 premium과 efficiency_cagr는 TPU/Ironwood inference-optimized hardware direction으로 정당화.",
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
            "category": "Power to AI IT load",
            "formula": "it_load_gw = active_power_gw / pue",
            "meaning_kr": "계약/계획 전력이 아니라 실제 operational deploy된 전력에서 PUE를 차감해 IT load를 산출.",
            "evidence_type": "Formula",
            "source_ids": "SRC_MCKINSEY_AI_WORKLOADS; SRC_EPRI_EPOCH_AI_POWER",
        },
        {
            "category": "AI workload allocation",
            "formula": "ai_it_load_gw = it_load_gw * ai_workload_share",
            "meaning_kr": "데이터센터 전체 IT load 중 LLM serving/training에 쓰이는 AI load만 분리.",
            "evidence_type": "Scenario assumption",
            "source_ids": "ASSUMP_POWER_RAMP",
        },
        {
            "category": "Training vs inference split",
            "formula": "inference_gw = ai_it_load_gw * inference_power_share; training_gw = ai_it_load_gw * (1 - inference_power_share)",
            "meaning_kr": "inference 비중은 company fact가 아니라 상용화 성숙도와 제품 표면에 따른 시나리오 변수.",
            "evidence_type": "Scenario assumption",
            "source_ids": "SRC_MCKINSEY_AI_WORKLOADS; SRC_DELOITTE_AI_POWER; SRC_EPRI_EPOCH_AI_POWER; ASSUMP_INFERENCE_SHARE_NOT_FACT_60",
        },
        {
            "category": "Inference token capacity",
            "formula": "inference_tokens_per_day = inference_gw * 1000 * tokens_per_second_per_mw * utilization * 86,400",
            "meaning_kr": "전력 배정, serving 효율, 실제 utilization이 token 생성 capacity를 결정.",
            "evidence_type": "Model equation",
            "source_ids": "SRC_SEMIANALYSIS_INFERENCEX; SRC_ARXIV_INFERENCE_ENERGY",
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


def is_moe_company(company: str) -> bool:
    return company in {"DeepSeek", "Alibaba"}


def forecast_rows(scenario_case: str = "Base") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case = SCENARIO_CASES[scenario_case]
    for scenario in scenarios():
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
            tps_per_mw = scenario.tps_per_mw_2026 * ((1 + scenario.efficiency_cagr) ** idx) * case["tokens_per_mw_multiplier"] * moe_multiplier
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
            annual_tokens = tokens_per_day * 365
            joules_per_token = 1_000_000 / tps_per_mw_r
            training_tps_per_mw_equivalent = tps_per_mw_r * 0.22
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
                    "training_power_share": training_share_r,
                    "inference_power_share": inference_share_r,
                    "inference_gw": inference_gw_r,
                    "training_gw": training_gw_r,
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
                }
            )
    return rows


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
            "display": f"{total_day / 1e15:.2f} quadrillion tokens/day",
            "interpretation_kr": "9개 상용 LLM owner의 base case 총 생성 capacity.",
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

    src_headers = list(asdict(sources()[0]).keys())
    append_rows(sheet("01_sources"), [asdict(s) for s in sources()], src_headers)

    model_headers = list(asdict(company_models()[0]).keys())
    append_rows(sheet("02_company_models"), [asdict(m) for m in company_models()], model_headers)

    fact_headers = list(asdict(fact_anchors()[0]).keys())
    append_rows(sheet("02a_fact_anchors"), [asdict(f) for f in fact_anchors()], fact_headers)

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
        "source_ids",
        "assumption_ids",
        "confidence",
    ]
    append_rows(sheet("03_power_capacity"), data["forecast"], power_headers)

    mix_rows = [
        {
            "company": m.company,
            "gpu_asic_mix": m.gpu_asic_mix,
            "serving_platform": m.serving_platform,
            "confidence": m.confidence,
            "source_ids": m.source_ids,
        }
        for m in company_models()
    ]
    append_rows(sheet("04_gpu_asic_mix"), mix_rows, list(mix_rows[0].keys()))

    eff_headers = [
        "company",
        "year",
        "tokens_per_second_per_mw",
        "joules_per_token",
        "utilization",
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
        "inference_gw",
        "confidence",
    ]
    append_rows(sheet("06_training_inference_split"), data["forecast"], split_headers)

    forecast_headers = [
        "company",
        "region",
        "model_family",
        "commercial_surface",
        "year",
        "inference_gw",
        "tokens_per_second_per_mw",
        "joules_per_token",
        "utilization",
        "inference_tokens_per_day",
        "inference_tokens_per_year",
        "training_tokens_processed_per_day",
        "confidence",
        "derivation_type",
        "source_ids",
        "assumption_ids",
    ]
    forecast_ws = sheet("07_token_forecast_2026_2030")
    append_rows(forecast_ws, data["forecast"], forecast_headers)
    forecast_ws.conditional_formatting.add(
        "J2:J41",
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
        "inference_tokens_per_day = inference_mw * tokens_per_second_per_mw * utilization * 86,400",
        "joules_per_token = 1,000,000 / tokens_per_second_per_mw",
        "```",
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
        "- Base `tokens_per_second_per_mw` 값은 아직 변경하지 않았습니다.",
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

    navy = RGBColor(18, 32, 55)
    ink = RGBColor(30, 41, 59)
    muted = RGBColor(100, 116, 139)
    blue = RGBColor(37, 99, 235)
    green = RGBColor(15, 159, 110)
    amber = RGBColor(180, 116, 30)
    red = RGBColor(185, 56, 56)
    bg = RGBColor(247, 249, 252)
    line = RGBColor(218, 226, 236)
    pale_blue = RGBColor(235, 242, 255)
    pale_green = RGBColor(232, 248, 240)
    pale_amber = RGBColor(255, 247, 229)

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

    def add_footer(slide, note: str = "출처 기반 시뮬레이션 | Fact / Estimate / Scenario 분리"):
        tx = slide.shapes.add_textbox(Inches(0.55), Inches(7.05), Inches(12.25), Inches(0.24))
        p = tx.text_frame.paragraphs[0]
        p.text = f"{note} | 생성일 {RUN_DATE}"
        p.font.size = Pt(7.5)
        p.font.color.rgb = muted

    def add_title(slide, title: str, subtitle: str | None = None):
        tx = slide.shapes.add_textbox(Inches(0.55), Inches(0.34), Inches(12.15), Inches(0.55))
        p = tx.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(23)
        p.font.bold = True
        p.font.color.rgb = navy
        if subtitle:
            sub = slide.shapes.add_textbox(Inches(0.58), Inches(0.88), Inches(11.9), Inches(0.34))
            p2 = sub.text_frame.paragraphs[0]
            p2.text = subtitle
            p2.font.size = Pt(10)
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
        shape.line.color.rgb = line
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

    # 1. Cover
    slide = prs.slides.add_slide(blank)
    set_bg(slide, RGBColor(245, 248, 252))
    add_label(slide, 0.72, 0.62, 3.2, 0.28, "임원 보고용 시뮬레이션", 8, blue, True)
    add_label(slide, 0.72, 1.15, 7.4, 2.25, "상용 LLM 업체별\n전력·GPU·토큰 Capacity\n2026–2030", 34, navy, True)
    add_label(slide, 0.78, 3.55, 7.0, 0.65, "모델 보유 업체 기준으로 OpenAI, Anthropic, Google, Meta, Microsoft, xAI, DeepSeek, Alibaba, Tencent의 추론 capacity를 추정", 14, muted)
    metric_card(slide, 8.35, 1.03, 3.95, 1.05, "2030 기준 토큰/일", f"{total_tokens_2030/1e15:.2f}Q", "9개 상용 LLM owner 합산", pale_blue)
    metric_card(slide, 8.35, 2.32, 3.95, 1.05, "2030 기준 추론 GW", f"{total_inf_2030:.1f} GW", "AI IT load 중 추론 배정", pale_green)
    metric_card(slide, 8.35, 3.61, 3.95, 1.05, "기준 추론 비중", f"{base_summary_2026['weighted_inference_share']:.0%} → {base_summary_2030['weighted_inference_share']:.0%}", "2026은 fact가 아닌 시나리오", pale_amber)
    add_label(slide, 0.78, 6.45, 7.5, 0.35, "핵심: 공개 fact는 capacity/model 규모를 제한하고, active GW·추론 비중·tokens/MW는 명시적 시나리오로 둔다.", 10, ink, True)
    add_footer(slide)

    # 2. Executive conclusion
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "임원 요약 결론", "기준 시나리오는 2026년 0.19Q/day에서 2030년 2.55Q/day로 확대되지만, 신뢰도는 전력 가동과 serving 효율에 좌우됩니다.")
    bullets = [
        "OpenAI·Google·Meta가 2030년 기준 토큰 capacity의 상위권을 형성한다.",
        "2026년 추론 60%+는 공식 fact가 아니므로 기준은 56%, 낙관만 61%로 제한했다.",
        "2030년 기준 추론 비중 76%는 상용 serving 확대를 반영하되, 학습 GW를 계속 남긴다.",
        "MoE 공개 모델 DeepSeek/Qwen은 파라미터 근거가 강하지만, active capacity 투명성은 낮다.",
    ]
    bullet_list(slide, 0.75, 1.35, 6.1, 3.6, bullets, 15)
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in ranked_2030[:5]]
    chart_data.add_series("2030 토큰/일 (Q)", [r["inference_tokens_per_day"] / 1e15 for r in ranked_2030[:5]])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(7.0), Inches(1.35), Inches(5.65), Inches(3.75), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(9)
    add_label(slide, 7.02, 5.35, 5.4, 0.48, "2030 기준 업체 순위, quadrillion tokens/day", 9, muted)
    add_footer(slide)

    # 3. Calculation logic
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "계산 로직은 전력 funnel과 serving 효율의 곱", "계약 전력은 token capacity가 아니며, 가동 전력과 AI IT load를 거쳐 추론 GW로 내려옵니다.")
    steps = [
        ("1", "계약 전력", "계약/계획 GW\nsource anchor"),
        ("2", "가동 전력", "operational deploy\n시나리오"),
        ("3", "AI IT load", "PUE·AI workload\n차감"),
        ("4", "추론 GW", "학습/추론\nsplit"),
        ("5", "토큰/일", "tokens/sec/MW ×\nutilization"),
    ]
    x0 = 0.75
    for i, (num, title, desc) in enumerate(steps):
        x = x0 + i * 2.45
        shape = slide.shapes.add_shape(1, Inches(x), Inches(1.55), Inches(2.0), Inches(1.55))
        shape.fill.solid()
        shape.fill.fore_color.rgb = [pale_blue, RGBColor(240, 244, 248), pale_green, pale_amber, RGBColor(240, 251, 255)][i]
        shape.line.color.rgb = line
        tf = shape.text_frame
        tf.margin_left = Inches(0.12)
        tf.margin_top = Inches(0.1)
        tf.clear()
        p = tf.paragraphs[0]
        p.text = f"{num}. {title}"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = navy
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(9)
        p2.font.color.rgb = muted
        if i < len(steps) - 1:
            add_label(slide, x + 2.06, 2.08, 0.36, 0.3, "→", 18, muted, True, PP_ALIGN.CENTER)
    formula = "추론 토큰/일 = 추론 GW × 1,000 × tokens/sec/MW × utilization × 86,400"
    add_label(slide, 1.15, 4.05, 11.0, 0.45, formula, 16, navy, True, PP_ALIGN.CENTER)
    bullet_list(
        slide,
        1.1,
        5.0,
        11.0,
        1.15,
        [
            "Excel/JSON 표시값 기준 재계산도 일치하도록 rounding 후 토큰 산식을 적용했다.",
            "Closed model parameter는 단일 숫자가 아니라 band만 사용하며, MoE는 total/active parameter를 분리한다.",
        ],
        11,
        muted,
    )
    add_footer(slide)

    # 4. Scenario envelope
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "시나리오별 토큰 capacity 범위", "낙관/기준/보수 시나리오는 전력 가동 속도, 추론 비중, MoE·serving 효율을 동시에 움직입니다.")
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for scen in SCENARIO_CASES:
        chart_data.add_series(
            scenario_label_kr.get(scen, scen),
            [next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.75), Inches(1.25), Inches(8.15), Inches(4.95), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    for i, r in enumerate(scenario_2030):
        metric_card(slide, 9.25, 1.2 + i * 1.2, 3.15, 0.88, scenario_label_kr.get(r["scenario"], r["scenario"]), f"{r['inference_tokens_per_day_q']:.2f}Q/일", f"2030 비중 {r['weighted_inference_share']:.0%}", [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i % 4])
    add_footer(slide)

    # 5. Power funnel
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "2030 기준 전력 전환 구조", "토큰 capacity는 계약 전력이 아니라 실제 추론 GW에서 나온다.")
    funnel = [
        ("계약", sum(r["contracted_power_gw"] for r in base_2030)),
        ("가동", total_active_2030),
        ("AI IT load", total_ai_2030),
        ("추론", total_inf_2030),
        ("학습", total_train_2030),
    ]
    chart_data = CategoryChartData()
    chart_data.categories = [x[0] for x in funnel]
    chart_data.add_series("GW", [x[1] for x in funnel])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.9), Inches(1.35), Inches(7.6), Inches(4.7), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(9)
    metric_card(slide, 9.0, 1.35, 3.35, 1.0, "계약 → 가동", f"{total_active_2030 / sum(r['contracted_power_gw'] for r in base_2030):.0%}", "operational deployment ratio", pale_blue)
    metric_card(slide, 9.0, 2.65, 3.35, 1.0, "AI IT → 추론", f"{total_inf_2030 / total_ai_2030:.0%}", "2030 기준 split", pale_green)
    metric_card(slide, 9.0, 3.95, 3.35, 1.0, "학습 잔존", f"{total_train_2030:.1f} GW", "0으로 가정하지 않음", pale_amber)
    add_footer(slide)

    # 6. Company ranking
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "2030 기준 모델 보유 업체별 토큰 capacity", "호스팅 capacity는 모델 소유권이 명확한 경우 model owner 기준으로 귀속한다.")
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in ranked_2030]
    chart_data.add_series("Q tokens/일", [r["inference_tokens_per_day"] / 1e15 for r in ranked_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.65), Inches(1.2), Inches(12.0), Inches(4.8), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(9)
    add_label(slide, 0.8, 6.25, 11.6, 0.45, "Microsoft/OpenAI 중복 처리: OpenAI 모델 output은 OpenAI model-owner로 귀속하고, Microsoft row는 Microsoft-owned/serving burden 가정을 반영한다.", 9, muted)
    add_footer(slide)

    # 7. Fact anchors
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Fact anchor는 모델을 조여주지만 telemetry를 대체하지 않는다", "공개 fact는 모델 규모와 capacity 상한을 제한하고, active GW와 utilization은 여전히 추정치다.")
    curated = [
        ("OpenAI", "Oracle 4.5GW + Stargate 10GW", "capacity 상한"),
        ("Google", "Ironwood 9,216 chips / 42.5 exaflops", "tokens/MW premium"),
        ("DeepSeek", "671B total / 37B active", "MoE 효율"),
        ("Alibaba", "Qwen3 235B / 22B active", "MoE 효율"),
        ("xAI", "Colossus 100k Hopper GPU", "cluster scale"),
        ("Microsoft", "Phi-4 14B", "owned model anchor"),
        ("Tencent", "Hunyuan 100B+ / 2T+ tokens", "model scale"),
        ("Meta", "Llama 4 109B/400B, 17B active", "open model band"),
    ]
    for i, (company, fact, use) in enumerate(curated):
        row = i // 2
        col = i % 2
        x = 0.75 + col * 6.2
        y = 1.25 + row * 1.22
        metric_card(slide, x, y, 5.65, 0.9, company, fact, use, [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i % 4])
    add_footer(slide, "상세 출처는 Excel 01_sources 및 02a_fact_anchors에 수록")

    # 8. Benchmark sanity check
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Benchmark sanity check", "첨부 엑셀의 effective active params와 GPU count 방식을 별도 reference layer로 통합했다.")
    bench_2030 = sorted([r for r in data["benchmark_reference"] if r["year"] == 2030], key=lambda r: r["model_annual_tokens_q"], reverse=True)
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in bench_2030]
    chart_data.add_series("우리 모델 annual QTokens", [r["model_annual_tokens_q"] for r in bench_2030])
    chart_data.add_series("Benchmark reference annual QTokens", [r["benchmark_annual_tokens_q"] for r in bench_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.65), Inches(1.25), Inches(8.15), Inches(4.85), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    bullet_list(
        slide,
        9.05,
        1.45,
        3.35,
        4.2,
        [
            "Main forecast는 tokens/sec/MW 방식.",
            "Benchmark layer는 GPU 수와 effective active params로 sanity check.",
            "Closed model benchmark는 proxy이므로 결론이 아니라 guardrail.",
            "큰 괴리는 confidence downgrade 신호.",
        ],
        11,
    )
    add_footer(slide)

    # 9. Energy sanity layer
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Energy sanity layer", "A08 Cycle 1: Joule/IBM/2026 serving 논문은 Base 숫자 변경보다 energy/query 검증 레이어를 요구한다.")
    energy_2030 = [r for r in data["energy_sanity_reference"] if r["year"] == 2030 and r["company"] in ("OpenAI", "Google", "Anthropic")]
    profiles = ["Strict-SLO / long-context agentic", "Base serving mix", "Batchable / optimized serving"]
    chart_data = CategoryChartData()
    chart_data.categories = profiles
    for company in ["OpenAI", "Google", "Anthropic"]:
        chart_data.add_series(company, [next(r["energy_implied_tokens_per_day_q"] for r in energy_2030 if r["company"] == company and r["profile"] == p) for p in profiles])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.65), Inches(1.25), Inches(7.7), Inches(4.65), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    bullet_list(
        slide,
        8.65,
        1.4,
        3.8,
        4.35,
        [
            "Base tokens/MW는 아직 유지.",
            "energy/query와 joules/token으로 sanity check 추가.",
            "agentic long-context는 energy/token을 악화시킬 수 있음.",
            "optimized serving은 개선 가능하지만 company fact가 아님.",
        ],
        11,
    )
    add_footer(slide, "Sources: Joule inference energy, IBM P/D disaggregation, SemiAnalysis InferenceX")

    # 10. Utilization sensitivity
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Utilization은 GPU 점유율이 아니라 SLO 제약 평균값", "A09 Cycle 1: TTFT/TPOT, prefill-decode allocation, batchability, placement가 realized utilization을 제한한다.")
    util_2030 = [r for r in data["utilization_sensitivity"] if r["year"] == 2030 and r["company"] in ("OpenAI", "Google", "Meta")]
    util_profiles = ["Strict-SLO real-time", "Base mixed serving", "Batchable optimized", "Agentic long-context stress"]
    chart_data = CategoryChartData()
    chart_data.categories = util_profiles
    for company in ["OpenAI", "Google", "Meta"]:
        chart_data.add_series(company, [next(r["tokens_per_day_q"] for r in util_2030 if r["company"] == company and r["profile"] == p) for p in util_profiles])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.65), Inches(1.25), Inches(8.0), Inches(4.65), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    bullet_list(
        slide,
        8.9,
        1.35,
        3.55,
        4.4,
        [
            "Strict-SLO는 reserve 때문에 평균 output 하락.",
            "Batchable workload는 utilization과 tokens/MW 동시 개선 가능.",
            "Agentic long-context는 throughput과 placement를 압박.",
            "Base band는 유지하고 sensitivity로 분리.",
        ],
        11,
    )
    add_footer(slide, "Sources: IBM P/D disaggregation, SLO-aware P/D allocation, Prefill-as-a-Service")

    # 11. Inference share audit
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "추론 비중 fact-check", "이 모델은 2026년 60%+ 추론 GW를 fact로 취급하지 않는다.")
    chart_data = CategoryChartData()
    chart_data.categories = ["보수", "기준", "낙관", "전력제약"]
    chart_data.add_series("2026", [next(r for r in data["scenario_summary"] if r["scenario"] == s and r["year"] == 2026)["weighted_inference_share"] for s in SCENARIO_CASES])
    chart_data.add_series("2030", [next(r for r in data["scenario_summary"] if r["scenario"] == s and r["year"] == 2030)["weighted_inference_share"] for s in SCENARIO_CASES])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.8), Inches(1.35), Inches(7.2), Inches(4.55), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.number_format = "0%"
    bullet_list(
        slide,
        8.45,
        1.45,
        3.95,
        4.0,
        [
            "기준 2026: 56%, 60% 미만.",
            "낙관 2026: 61%, upside scenario에서만 허용.",
            "기준 2030: 76%, 상용 serving 확대 반영.",
            "모든 case에서 학습 capacity는 계속 유의미하게 남김.",
        ],
        13,
    )
    add_footer(slide)

    # 10. Model owner landscape
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "모델 보유 업체 landscape", "Core row는 데이터센터 host가 아니라 상용 LLM owner다.")
    groups = [
        ("미국 대형 플랫폼", ["OpenAI", "Anthropic", "Google", "Meta", "Microsoft"], pale_blue),
        ("미국 challenger", ["xAI"], pale_green),
        ("중국 model owner", ["DeepSeek", "Alibaba", "Tencent"], pale_amber),
    ]
    for i, (label, companies, fill) in enumerate(groups):
        x = 0.8 + i * 4.15
        shape = slide.shapes.add_shape(1, Inches(x), Inches(1.35), Inches(3.65), Inches(4.7))
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
        shape.line.color.rgb = line
        add_label(slide, x + 0.18, 1.58, 3.2, 0.32, label, 13, navy, True)
        for j, c in enumerate(companies):
            m = next(m for m in data["company_models"] if m["company"] == c)
            add_label(slide, x + 0.22, 2.18 + j * 0.82, 3.1, 0.26, c, 13, ink, True)
            add_label(slide, x + 0.22, 2.48 + j * 0.82, 3.1, 0.28, m["model_family"], 8.3, muted)
    add_footer(slide)

    # 11. Memory implications
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "메모리 마케팅 시사점", "토큰 capacity 성장은 allocation, qualification, attach-rate 영업 motion으로 전환된다.")
    motions = [
        ("HBM", "OpenAI/Google/Meta/xAI ramp → LTA, HBM4 roadmap lock-in, second-source qualification"),
        ("DDR5 / MRDIMM", "추론 fleet 확대 → CPU-side memory density와 bandwidth attach story"),
        ("Enterprise SSD / QLC", "RAG, checkpointing, vector retrieval → TCO, endurance, retrieval latency"),
        ("CXL", "고가동률 추론 cluster → memory expansion과 utilization recovery"),
    ]
    for i, (title, desc) in enumerate(motions):
        metric_card(slide, 0.8 + (i % 2) * 6.05, 1.45 + (i // 2) * 1.75, 5.55, 1.18, title, "", desc, [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i])
    add_label(slide, 0.85, 5.45, 11.7, 0.55, "권장 sales motion: model owner별 account brief, 제품별 proof pack, scenario envelope에 연결된 pricing/mix 논리.", 13, navy, True)
    add_footer(slide)

    # 12. Evidence confidence
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "근거 신뢰도 감사", "가장 강한 근거는 모델 크기와 발표 capacity이며, 가장 약한 부분은 active serving utilization이다.")
    audit_rows = [
        ("높음", "공식 model card / technical report", "DeepSeek 671B/37B, Qwen3 235B/22B, Phi-4 14B"),
        ("중간", "공식 capacity 또는 hardware 발표", "OpenAI/Stargate GW, Google Ironwood, xAI Colossus"),
        ("낮음-중간", "Active GW와 추론/학습 split", "telemetry 또는 site-level disclosure 필요"),
        ("민감도", "tokens/sec/MW와 utilization", "company fact가 아니라 scenario benchmark"),
    ]
    for i, (level, evidence, example) in enumerate(audit_rows):
        y = 1.35 + i * 1.05
        add_label(slide, 0.9, y, 1.45, 0.35, level, 14, [green, blue, amber, red][i], True)
        add_label(slide, 2.45, y, 4.2, 0.35, evidence, 13, ink, True)
        add_label(slide, 6.7, y, 5.6, 0.35, example, 11, muted)
    add_label(slide, 0.9, 6.1, 11.5, 0.45, "Replacement path: site-level MW activation, model routing mix, production API traffic, 모델/context별 실측 tokens/sec/MW.", 11, navy, True)
    add_footer(slide)

    # 13. InferenceX ingestion layer
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    latest = data["inferencex"]["manifest"].get("latest_db_dump", {})
    parsed = data["inferencex"]["manifest"].get("parsed_dump", {})
    add_title(slide, "InferenceX는 benchmark DB로 별도 수집한다", "대시보드 DOM이 아니라 GitHub release dump와 app schema를 기준으로 A08/A09 sensitivity를 갱신한다.")
    ix_cards = [
        ("최신 dump", latest.get("tag_name", "not refreshed"), latest.get("asset_name", "")),
        ("Benchmark rows", str(parsed.get("benchmark_rows", 0)), f"profile {parsed.get('metric_profile_rows', 0)} / eval {parsed.get('accuracy_eval_rows', 0)}"),
        ("Evidence class", "Proxy / Benchmark", "company production telemetry로 직접 사용 금지"),
        ("Workbook sheets", "12d / 12e / 12f", "benchmark, metric profile, accuracy evals"),
    ]
    for i, (label, value, note) in enumerate(ix_cards):
        metric_card(slide, 0.8 + (i % 2) * 6.1, 1.35 + (i // 2) * 1.65, 5.65, 1.05, label, value, note, [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i])
    tab_text = "Inference Performance → tokens/MW, latency | Accuracy Evals → precision quality guardrail | Historical Trends → software improvement CAGR | TCO/GPU Specs → cost/token and hardware sanity"
    add_label(slide, 0.9, 5.15, 11.55, 0.85, tab_text, 12, navy, True)
    add_label(slide, 0.9, 6.08, 11.55, 0.45, f"검증 digest: {parsed.get('sha256', '')[:24]}... / 원천 dump는 git ignore, 정규화 CSV만 산출물화.", 11, muted)
    add_footer(slide)

    # 14. Hallucination audit checklist
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Hallucination 체크리스트", "임원 보고 전 숫자와 문구가 fact/proxy/scenario를 혼동하지 않는지 확인합니다.")
    checklist_items = [
        ("출처 존재", "URL/title/date 직접 확인"),
        ("숫자 직접 인용", "4.5GW, 671B/37B 등 원문 매칭"),
        ("Fact/Estimate 분리", "active GW·utilization은 scenario"),
        ("Closed model", "precise parameter 금지"),
        ("Host attribution", "AWS/Oracle/Google host와 model owner 분리"),
        ("Benchmark proxy", "closed model 결론이 아니라 sanity check"),
        ("단위", "daily vs annual token 혼동 금지"),
        ("Outlier", "benchmark_vs_model ±50% 초과 review"),
    ]
    for i, (title, desc) in enumerate(checklist_items):
        x = 0.75 + (i % 2) * 6.15
        y = 1.25 + (i // 2) * 1.15
        metric_card(slide, x, y, 5.65, 0.82, title, "", desc, [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i % 4])
    add_label(slide, 0.85, 6.25, 11.6, 0.35, "전체 체크리스트는 Excel `11_hallucination_checklist`에 수록되어 있으며, source screenshot/quote pack으로 최종 sign-off해야 합니다.", 10, navy, True)
    add_footer(slide)

    # 14. Appendix
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "부록: 계산 검증 컨트롤", "전체 감사 가능한 모델은 workbook에 수록되어 있다.")
    bullet_list(
        slide,
        0.9,
        1.35,
        11.5,
        4.4,
        [
            "00_formula_assumptions: 모든 계산식과 해석 방식.",
            "02a_fact_anchors: 확인된 공개 numeric anchor, confidence, replacement path.",
            "08a/08b/08c/08d: 시나리오 정의, 업체-연도별 forecast, aggregate summary, benchmark reference.",
            "11_hallucination_checklist: fact/proxy/scenario 혼동 방지용 검토표.",
            "Validation: active power는 contracted power 이하, 학습+추론=100%, 표시값으로 token/day 재계산 일치.",
        ],
        15,
    )
    add_footer(slide)

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
        "benchmark_assumptions": benchmark_assumptions(),
        "hallucination_checklist": hallucination_checklist(),
        "scenario_definitions": scenario_definitions(),
        "forecast": rows,
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
    write_ppt(data, OUT / f"{stem}.pptx")
    write_html(slim_data, OUT / f"{stem}.html")
    write_markdown(slim_data, OUT / f"{stem}.md")
    print(json.dumps({"status": "PASS", "outputs": [str(OUT / f"{stem}.{ext}") for ext in ("json", "xlsx", "pptx", "html", "md")]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
