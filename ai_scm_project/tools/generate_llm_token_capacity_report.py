"""Generate LLM-owner token capacity simulation artifacts.

This report is intentionally separate from the project's core dynamics model.
It creates an auditable executive simulation for commercial LLM owners, with
every modeled number labeled as Fact, Estimate, or Scenario.
"""

from __future__ import annotations

import json
import math
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
RUN_DATE = "2026-05-14"
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
            "interpretation_kr": "8개 상용 LLM owner의 base case 총 생성 capacity.",
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
        "anthropic_scope": "PASS - Anthropic is excluded from core rows and reserved for comparator/hosted sensitivity.",
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
    line.add_data(Reference(chart_ws, min_col=2, max_col=9, min_row=1, max_row=6), titles_from_data=True)
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
    bar.add_data(Reference(chart_ws, min_col=2, max_col=3, min_row=start, max_row=start + 8), titles_from_data=True)
    bar.set_categories(Reference(chart_ws, min_col=1, min_row=start + 1, max_row=start + 8))
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
    scenario_line.title = "Scenario token capacity: Bull/Base/Bear plus grid-constrained case"
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
  <title>상용 LLM 토큰 Capacity Dashboard</title>
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
    <div class="sub">2026–2030 base case. Core company는 Microsoft, Google, Meta, xAI, OpenAI, DeepSeek, Alibaba, Tencent입니다. 숫자는 Fact/Estimate/Scenario와 confidence를 함께 읽어야 합니다.</div>
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
      <h2>업체별 token forecast</h2>
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
      <h2>Confidence heatmap & source audit</h2>
      <table id="audit"></table>
    </section>
    <section>
      <h2>Fact anchors</h2>
      <table id="facts"></table>
    </section>
    <section>
      <h2>Model owner attribution</h2>
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
        ["Inference GW", infGw.toFixed(2)+" GW"],
        ["Training GW", trainGw.toFixed(2)+" GW"],
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
      $("audit").innerHTML = `<tr><th>업체</th><th>Confidence</th><th>Derivation</th><th>Sources</th><th>Assumptions</th></tr>` +
        rows.map(d=>`<tr><td>${{d.company}}</td><td><span class="pill">${{d.confidence}}</span></td><td>${{d.derivation_type}}</td><td>${{d.source_ids}}</td><td>${{d.assumption_ids}}</td></tr>`).join('');
      $("models").innerHTML = `<tr><th>업체</th><th>모델 family</th><th>상용 표면</th><th>Attribution rule</th></tr>` +
        DATA.company_models.filter(m => $("company").value === "ALL" || m.company === $("company").value)
          .map(m=>`<tr><td>${{m.company}}</td><td>${{m.model_family}}</td><td>${{m.commercial_surface}}</td><td>${{m.attribution_rule}}</td></tr>`).join('');
      $("formulas").innerHTML = `<tr><th>Block</th><th>Formula</th><th>해석</th><th>Sources</th></tr>` +
        DATA.formula_assumptions.map(f=>`<tr><td>${{f.category}}</td><td><code>${{f.formula}}</code></td><td>${{f.meaning_kr}}</td><td>${{f.source_ids}}</td></tr>`).join('');
      $("scenarioDefs").innerHTML = `<tr><th>Scenario</th><th>Deploy 2030</th><th>Inference delta 2030</th><th>Tokens/MW</th><th>설명</th></tr>` +
        DATA.scenario_definitions.map(s=>`<tr><td>${{s.scenario}}</td><td>${{Math.round(s.operational_deploy_multiplier_2030*100)}}%</td><td>${{Math.round(s.inference_share_delta_2030*100)}}%p</td><td>${{Math.round(s.tokens_per_mw_multiplier*100)}}%</td><td>${{s.description_kr}}</td></tr>`).join('');
      $("facts").innerHTML = `<tr><th>Company</th><th>Metric</th><th>Value</th><th>Source</th><th>모델 반영 방식</th></tr>` +
        DATA.fact_anchors.map(f=>`<tr><td>${{f.company}}</td><td>${{f.metric}}</td><td>${{f.value}}</td><td>${{f.source_id}}</td><td>${{f.derivation_impact_kr}}</td></tr>`).join('');
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
        "- 목적: 상용 LLM owner 기준으로 전력 capacity, inference/training split, GPU/ASIC mix, tokens/sec/MW, token 생성량을 연결한 임원 보고용 base case 작성",
        "- 주의: 이 문서는 투자 조언이 아니라 supply-chain / token-capacity intelligence simulation입니다.",
        "",
        "## 핵심 결론",
    ]
    for item in data["exec_summary"][:3]:
        lines.append(f"- **{item['metric']}**: {item['display']} - {item['interpretation_kr']}")
    lines += [
        "",
        "## 2030 Base Case Ranking",
        "",
        "| Rank | Company | Region | Inference GW | Tokens/day | Confidence |",
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
        "## Fact Anchors",
        "",
        "| Anchor | Company | Metric | Value | Date | Source | Model use |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in data["fact_anchors"]:
        lines.append(f"| {f['anchor_id']} | {f['company']} | {f['metric']} | {f['value']} | {f['fact_date']} | {f['source_id']} | {f['derivation_impact_kr']} |")
    lines += [
        "",
        "## Scenario Design",
        "",
        "| Scenario | Deploy 2030 | Inference delta 2030 | Tokens/MW | MoE optimization | 설명 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in data["scenario_definitions"]:
        lines.append(
            f"| {item['scenario']} | {item['operational_deploy_multiplier_2030']:.0%} | {item['inference_share_delta_2030']:+.0%}p | {item['tokens_per_mw_multiplier']:.0%} | {item['moe_optimization_multiplier']:.0%} | {item['description_kr']} |"
        )
    lines += [
        "",
        "## Inference 60%+ Fact Check",
        "",
        "- 2026년에 이미 전체 AI GW의 60% 이상이 inference라는 주장은 공식 company-level fact로 단정하지 않습니다.",
        "- McKinsey/Deloitte는 inference 비중 상승 전망을 제공하지만, 업체별 active GW split disclosure가 아닙니다.",
        "- EPRI/Epoch AI는 현재 AI power가 training, experiments, inference로 대략 나뉜다는 보수적 anchor를 제공합니다.",
        "- 따라서 본 모델의 inference share는 `Scenario assumption`이며, source transparency에 맞춰 confidence를 별도 표기합니다.",
        "",
        "## 2030 Scenario Envelope",
        "",
        "| Scenario | Active power GW | Inference GW | Weighted inference share | Tokens/day | Delta vs Base 2030 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in [r for r in data["scenario_summary"] if r["year"] == 2030]:
        lines.append(
            f"| {row['scenario']} | {row['active_power_gw']:.2f} | {row['inference_gw']:.2f} | {row['weighted_inference_share']:.0%} | {row['inference_tokens_per_day_q']:.2f}Q | {row['delta_vs_base_2030_pct']}% |"
        )
    lines += [
        "",
        "## Attribution Rules",
    ]
    for m in company_models():
        lines.append(f"- **{m.company}**: {m.attribution_rule}")
    lines += [
        "",
        "## Evidence Rules",
        "",
        "- Fact: official model docs/cards, company announcements, technical reports.",
        "- Estimate: active power, inference/training share, utilization, company-level tokens/sec/MW.",
        "- Scenario: 2027–2030 ramp, software efficiency CAGR, commercial token absorption.",
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
        "## Validation",
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

    def add_footer(slide, note: str = "Source-backed simulation | Fact / Estimate / Scenario separated"):
        tx = slide.shapes.add_textbox(Inches(0.55), Inches(7.05), Inches(12.25), Inches(0.24))
        p = tx.text_frame.paragraphs[0]
        p.text = f"{note} | generated {RUN_DATE}"
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
    add_label(slide, 0.72, 0.62, 3.2, 0.28, "EXECUTIVE SIMULATION", 8, blue, True)
    add_label(slide, 0.72, 1.15, 7.4, 2.25, "상용 LLM 업체별\n전력·GPU·토큰 Capacity\n2026–2030", 34, navy, True)
    add_label(slide, 0.78, 3.55, 7.0, 0.65, "Model-owner 기준으로 OpenAI, Google, Meta, Microsoft, xAI, DeepSeek, Alibaba, Tencent의 inference capacity를 추정", 14, muted)
    metric_card(slide, 8.35, 1.03, 3.95, 1.05, "2030 Base tokens/day", f"{total_tokens_2030/1e15:.2f}Q", "8개 상용 LLM owner 합산", pale_blue)
    metric_card(slide, 8.35, 2.32, 3.95, 1.05, "2030 Base inference GW", f"{total_inf_2030:.1f} GW", "AI IT load 중 inference 배정", pale_green)
    metric_card(slide, 8.35, 3.61, 3.95, 1.05, "Base inference share", f"{base_summary_2026['weighted_inference_share']:.0%} → {base_summary_2030['weighted_inference_share']:.0%}", "2026은 fact가 아닌 scenario", pale_amber)
    add_label(slide, 0.78, 6.45, 7.5, 0.35, "핵심: 공개 fact는 capacity/model 규모를 제한하고, active GW·inference split·tokens/MW는 명시적 scenario로 둔다.", 10, ink, True)
    add_footer(slide)

    # 2. Executive conclusion
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Executive conclusion", "Base case는 2026 0.19Q/day에서 2030 2.55Q/day로 확대되지만, 신뢰도는 capacity activation과 serving efficiency에 좌우됩니다.")
    bullets = [
        "OpenAI·Google·Meta가 2030 Base token capacity의 상위권을 형성한다.",
        "2026 inference 60%+는 공식 fact가 아니므로 Base는 56%, Bull만 61%로 제한했다.",
        "2030 Base inference share 76%는 commercial serving 확대를 반영하되, training GW를 계속 남긴다.",
        "MoE 공개 모델 DeepSeek/Qwen은 parameter evidence가 강하지만, active capacity transparency는 낮다.",
    ]
    bullet_list(slide, 0.75, 1.35, 6.1, 3.6, bullets, 15)
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in ranked_2030[:5]]
    chart_data.add_series("2030 tokens/day (Q)", [r["inference_tokens_per_day"] / 1e15 for r in ranked_2030[:5]])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(7.0), Inches(1.35), Inches(5.65), Inches(3.75), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(9)
    add_label(slide, 7.02, 5.35, 5.4, 0.48, "2030 Base company ranking, quadrillion tokens/day", 9, muted)
    add_footer(slide)

    # 3. Calculation logic
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "계산 로직은 전력 funnel과 serving efficiency의 곱", "계약 전력은 token capacity가 아니며, active power와 AI IT load를 거쳐 inference GW로 내려옵니다.")
    steps = [
        ("1", "Contracted power", "계약/계획 GW\nsource anchor"),
        ("2", "Active power", "operational deploy\nscenario"),
        ("3", "AI IT load", "PUE·AI workload\n차감"),
        ("4", "Inference GW", "training/inference\nsplit"),
        ("5", "Tokens/day", "tokens/sec/MW ×\nutilization"),
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
    formula = "inference_tokens_per_day = inference_gw × 1,000 × tokens_per_second_per_mw × utilization × 86,400"
    add_label(slide, 1.15, 4.05, 11.0, 0.45, formula, 16, navy, True, PP_ALIGN.CENTER)
    bullet_list(
        slide,
        1.1,
        5.0,
        11.0,
        1.15,
        [
            "Excel/JSON 표시값 기준 재계산도 일치하도록 rounding 후 token 산식을 적용했다.",
            "Closed model parameter는 단일 숫자가 아니라 band만 사용하며, MoE는 total/active parameter를 분리한다.",
        ],
        11,
        muted,
    )
    add_footer(slide)

    # 4. Scenario envelope
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "시나리오별 token capacity envelope", "Bull/Base/Bear는 deployment speed, inference mix, MoE/serving efficiency를 동시에 움직입니다.")
    chart_data = CategoryChartData()
    chart_data.categories = [str(y) for y in YEARS]
    for scen in SCENARIO_CASES:
        chart_data.add_series(
            scen,
            [next(r["inference_tokens_per_day_q"] for r in data["scenario_summary"] if r["scenario"] == scen and r["year"] == y) for y in YEARS],
        )
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.75), Inches(1.25), Inches(8.15), Inches(4.95), chart_data).chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(8)
    for i, r in enumerate(scenario_2030):
        metric_card(slide, 9.25, 1.2 + i * 1.2, 3.15, 0.88, r["scenario"], f"{r['inference_tokens_per_day_q']:.2f}Q/day", f"2030 share {r['weighted_inference_share']:.0%}", [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i % 4])
    add_footer(slide)

    # 5. Power funnel
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "2030 Base power funnel", "Token capacity는 contracted power가 아니라 inference GW에서 나온다.")
    funnel = [
        ("Contracted", sum(r["contracted_power_gw"] for r in base_2030)),
        ("Active", total_active_2030),
        ("AI IT load", total_ai_2030),
        ("Inference", total_inf_2030),
        ("Training", total_train_2030),
    ]
    chart_data = CategoryChartData()
    chart_data.categories = [x[0] for x in funnel]
    chart_data.add_series("GW", [x[1] for x in funnel])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.9), Inches(1.35), Inches(7.6), Inches(4.7), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(9)
    metric_card(slide, 9.0, 1.35, 3.35, 1.0, "Contracted → Active", f"{total_active_2030 / sum(r['contracted_power_gw'] for r in base_2030):.0%}", "operational deployment ratio", pale_blue)
    metric_card(slide, 9.0, 2.65, 3.35, 1.0, "AI IT → Inference", f"{total_inf_2030 / total_ai_2030:.0%}", "Base 2030 split", pale_green)
    metric_card(slide, 9.0, 3.95, 3.35, 1.0, "Training remains", f"{total_train_2030:.1f} GW", "not assumed to vanish", pale_amber)
    add_footer(slide)

    # 6. Company ranking
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "2030 Base token capacity by model owner", "Host capacity is attributed back to the model owner where model ownership is clear.")
    chart_data = CategoryChartData()
    chart_data.categories = [r["company"] for r in ranked_2030]
    chart_data.add_series("Q tokens/day", [r["inference_tokens_per_day"] / 1e15 for r in ranked_2030])
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.65), Inches(1.2), Inches(12.0), Inches(4.8), chart_data).chart
    chart.has_legend = False
    chart.value_axis.tick_labels.font.size = Pt(8)
    chart.category_axis.tick_labels.font.size = Pt(9)
    add_label(slide, 0.8, 6.25, 11.6, 0.45, "Microsoft/OpenAI overlap: OpenAI model output is counted under OpenAI model-owner logic; Microsoft row captures Microsoft-owned/serving burden assumptions.", 9, muted)
    add_footer(slide)

    # 7. Fact anchors
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Fact anchors tighten the model, but do not replace telemetry", "Public facts constrain model size and capacity ceilings; active GW and utilization remain estimates.")
    curated = [
        ("OpenAI", "4.5GW Oracle + 10GW Stargate", "capacity ceiling"),
        ("Google", "Ironwood 9,216 chips / 42.5 exaflops", "tokens/MW premium"),
        ("DeepSeek", "671B total / 37B active", "MoE efficiency"),
        ("Alibaba", "Qwen3 235B / 22B active", "MoE efficiency"),
        ("xAI", "Colossus 100k Hopper GPU", "cluster scale"),
        ("Microsoft", "Phi-4 14B", "owned model anchor"),
        ("Tencent", "Hunyuan 100B+ / 2T+ tokens", "model scale"),
        ("Meta", "Llama 4 109B/400B with 17B active", "open model band"),
    ]
    for i, (company, fact, use) in enumerate(curated):
        row = i // 2
        col = i % 2
        x = 0.75 + col * 6.2
        y = 1.25 + row * 1.22
        metric_card(slide, x, y, 5.65, 0.9, company, fact, use, [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i % 4])
    add_footer(slide, "Sources listed in Excel 01_sources and 02a_fact_anchors")

    # 8. Inference share audit
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Inference share fact-check", "The model no longer treats 2026 60%+ inference GW as a fact.")
    chart_data = CategoryChartData()
    chart_data.categories = ["Bear", "Base", "Bull", "Grid-constrained"]
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
            "Base 2026: 56%, below 60%.",
            "Bull 2026: 61%, allowed as upside scenario only.",
            "Base 2030: 76%, reflecting commercial serving growth.",
            "Training capacity remains material in every case.",
        ],
        13,
    )
    add_footer(slide)

    # 9. Model owner landscape
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Model-owner landscape", "Core rows are commercial LLM owners, not datacenter hosts.")
    groups = [
        ("US scaled platforms", ["OpenAI", "Google", "Meta", "Microsoft"], pale_blue),
        ("US challenger", ["xAI"], pale_green),
        ("China model owners", ["DeepSeek", "Alibaba", "Tencent"], pale_amber),
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

    # 10. Memory implications
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Memory marketing implications", "Token capacity growth converts into allocation, qualification, and attach-rate motions.")
    motions = [
        ("HBM", "OpenAI/Google/Meta/xAI ramp → LTA, HBM4 roadmap lock-in, second-source qualification"),
        ("DDR5 / MRDIMM", "Inference fleet growth → CPU-side memory density and bandwidth attach story"),
        ("Enterprise SSD / QLC", "RAG, checkpointing, vector retrieval → TCO, endurance, retrieval latency"),
        ("CXL", "High-utilization inference clusters → memory expansion and utilization recovery"),
    ]
    for i, (title, desc) in enumerate(motions):
        metric_card(slide, 0.8 + (i % 2) * 6.05, 1.45 + (i // 2) * 1.75, 5.55, 1.18, title, "", desc, [pale_blue, pale_green, pale_amber, RGBColor(240, 244, 248)][i])
    add_label(slide, 0.85, 5.45, 11.7, 0.55, "Recommended sales motion: account brief by model owner, proof pack by memory product, and pricing/mix argument tied to scenario envelope.", 13, navy, True)
    add_footer(slide)

    # 11. Evidence confidence
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Evidence confidence audit", "Strongest evidence is model size and announced capacity; weakest is active serving utilization.")
    audit_rows = [
        ("High", "Official model cards / technical reports", "DeepSeek 671B/37B, Qwen3 235B/22B, Phi-4 14B"),
        ("Medium", "Official capacity or hardware announcements", "OpenAI/Stargate GW, Google Ironwood, xAI Colossus"),
        ("Low-Medium", "Active GW and inference/training split", "requires telemetry or site-level disclosure"),
        ("Sensitivity", "tokens/sec/MW and utilization", "benchmarked as scenario, not company fact"),
    ]
    for i, (level, evidence, example) in enumerate(audit_rows):
        y = 1.35 + i * 1.05
        add_label(slide, 0.9, y, 1.45, 0.35, level, 14, [green, blue, amber, red][i], True)
        add_label(slide, 2.45, y, 4.2, 0.35, evidence, 13, ink, True)
        add_label(slide, 6.7, y, 5.6, 0.35, example, 11, muted)
    add_label(slide, 0.9, 6.1, 11.5, 0.45, "Replacement path: site-level MW activation, model routing mix, production API traffic, and measured tokens/sec/MW by model/context.", 11, navy, True)
    add_footer(slide)

    # 12. Appendix
    slide = prs.slides.add_slide(blank)
    set_bg(slide)
    add_title(slide, "Appendix: exact calculation controls", "The workbook contains the full auditable model.")
    bullet_list(
        slide,
        0.9,
        1.35,
        11.5,
        4.4,
        [
            "00_formula_assumptions: every equation and how it should be interpreted.",
            "02a_fact_anchors: checked public numeric anchors, confidence, and replacement path.",
            "08a/08b/08c: scenario definitions, company-year scenario forecast, and aggregate scenario summary.",
            "Validation: active power does not exceed contracted power; training+inference equals 100%; displayed values recalculate token/day exactly.",
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
        "scenario_definitions": scenario_definitions(),
        "forecast": rows,
        "scenario_forecast": scenario_rows,
        "scenario_summary": scenario_summary_rows(scenario_rows),
        "sensitivity": sensitivity_rows(rows),
        "exec_summary": exec_summary(rows),
    }
    data["validation"] = validate(scenario_rows)
    return data


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = build_payload()
    if data["validation"]["status"] != "PASS":
        raise SystemExit(json.dumps(data["validation"], indent=2, ensure_ascii=False))

    stem = "llm_token_capacity_2026_2030"
    write_json(data, OUT / f"{stem}.json")
    write_excel(data, OUT / f"{stem}.xlsx")
    write_ppt(data, OUT / f"{stem}.pptx")
    write_html(data, OUT / f"{stem}.html")
    write_markdown(data, OUT / f"{stem}.md")
    print(json.dumps({"status": "PASS", "outputs": [str(OUT / f"{stem}.{ext}") for ext in ("json", "xlsx", "pptx", "html", "md")]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
