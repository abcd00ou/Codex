# A11 gpu_asic_mix Provenance

Short name: GPU generation 및 purpose-built accelerator mix

Role: 같은 inference MW라도 H200/B200/GB200/purpose-built mix에 따라 benchmark TPS/MW가 달라진다.

Headline use: 직접 사용

Confidence rule: platform existence는 source fact, numeric share는 fleet telemetry가 없으면 editable scenario다.

## Metrics covered

`b200_share`, `gb200_share`, `gpu_share`, `h200_share`, `purpose_built_accelerator_share`

## Base scenario 2026 -> 2030 endpoint view

| Company | Metric | 2026 -> 2030 | Derivation | Confidence | Source IDs |
|---|---|---|---|---|---|
| Alibaba | b200_share | 0.4 -> 0.35 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | gb200_share | 0.05 -> 0.55 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | gpu_share | 1.0 -> 1.0 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | h200_share | 0.55 -> 0.1 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | purpose_built_accelerator_share | 0.0 -> 0.0 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | b200_share | 0.14 -> 0.052 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | gb200_share | 0.017 -> 0.083 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | gpu_share | 0.35 -> 0.15 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | h200_share | 0.193 -> 0.015 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | purpose_built_accelerator_share | 0.65 -> 0.85 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | b200_share | 0.4 -> 0.35 share of inference-serving accelerator load | Editable numeric scenario | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | gb200_share | 0.05 -> 0.55 share of inference-serving accelerator load | Editable numeric scenario | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | gpu_share | 1.0 -> 1.0 share of inference-serving accelerator load | Numeric scenario | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | h200_share | 0.55 -> 0.1 share of inference-serving accelerator load | Editable numeric scenario | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | purpose_built_accelerator_share | 0.0 -> 0.0 share of inference-serving accelerator load | Numeric scenario | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | b200_share | 0.08 -> 0.035 share of inference-serving accelerator load | Editable numeric scenario | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | gb200_share | 0.01 -> 0.055 share of inference-serving accelerator load | Editable numeric scenario | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | gpu_share | 0.2 -> 0.1 share of inference-serving accelerator load | Numeric scenario | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | h200_share | 0.11 -> 0.01 share of inference-serving accelerator load | Editable numeric scenario | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | purpose_built_accelerator_share | 0.8 -> 0.9 share of inference-serving accelerator load | Numeric scenario | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | b200_share | 0.36 -> 0.193 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | gb200_share | 0.045 -> 0.302 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | gpu_share | 0.9 -> 0.55 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | h200_share | 0.495 -> 0.055 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | purpose_built_accelerator_share | 0.1 -> 0.45 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | b200_share | 0.36 -> 0.193 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | gb200_share | 0.045 -> 0.302 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | gpu_share | 0.9 -> 0.55 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | h200_share | 0.495 -> 0.055 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | purpose_built_accelerator_share | 0.1 -> 0.45 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | b200_share | 0.4 -> 0.35 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | gb200_share | 0.05 -> 0.55 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | gpu_share | 1.0 -> 1.0 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | h200_share | 0.55 -> 0.1 share of inference-serving accelerator load | Editable numeric scenario | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | purpose_built_accelerator_share | 0.0 -> 0.0 share of inference-serving accelerator load | Numeric scenario | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | b200_share | 0.4 -> 0.35 share of inference-serving accelerator load | Editable numeric scenario | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | gb200_share | 0.05 -> 0.55 share of inference-serving accelerator load | Editable numeric scenario | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | gpu_share | 1.0 -> 1.0 share of inference-serving accelerator load | Numeric scenario | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | h200_share | 0.55 -> 0.1 share of inference-serving accelerator load | Editable numeric scenario | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | purpose_built_accelerator_share | 0.0 -> 0.0 share of inference-serving accelerator load | Numeric scenario | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | b200_share | 0.4 -> 0.35 share of inference-serving accelerator load | Editable numeric scenario | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | gb200_share | 0.05 -> 0.55 share of inference-serving accelerator load | Editable numeric scenario | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | gpu_share | 1.0 -> 1.0 share of inference-serving accelerator load | Numeric scenario | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | h200_share | 0.55 -> 0.1 share of inference-serving accelerator load | Editable numeric scenario | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | purpose_built_accelerator_share | 0.0 -> 0.0 share of inference-serving accelerator load | Numeric scenario | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_NUMERIC_ACCELERATOR_MIX |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| gpu_share | gpu_share interpolated from company 2026/2030 accelerator-mix endpoints | Maia 200 is officially designated for inference, Azure AI Foundry and Microsoft 365 Copilot. Exact serving fleet share is undisclosed; gradual Maia adoption is modeled. | Microsoft disclosure of Maia accelerator-hours or Copilot model/hardware routing mix. |
| h200_share | h200_share = gpu_share * default_gpu_generation_mix_h200 | Default GPU-generation migration assumption; executive workbook allows later manual replacement by company/year/scenario. | Company fleet inventory, accelerator-hours or procurement/deployment records by GPU generation. |
| b200_share | b200_share = gpu_share * default_gpu_generation_mix_b200 | Default GPU-generation migration assumption; executive workbook allows later manual replacement by company/year/scenario. | Company fleet inventory, accelerator-hours or procurement/deployment records by GPU generation. |
| gb200_share | gb200_share = gpu_share * default_gpu_generation_mix_gb200 | Default GPU-generation migration assumption; executive workbook allows later manual replacement by company/year/scenario. | Company fleet inventory, accelerator-hours or procurement/deployment records by GPU generation. |
| purpose_built_accelerator_share | 1 - gpu_share | Purpose-built bucket: Maia inference accelerator. Maia 200 is officially designated for inference, Azure AI Foundry and Microsoft 365 Copilot. Exact serving fleet share is undisclosed; gradual Maia adoption is modeled. | Microsoft disclosure of Maia accelerator-hours or Copilot model/hardware routing mix. |

## Source catalog for this assumption

| ID | Title/description | Publisher/category | Date | Tier | Confidence | URL/report |
|---|---|---|---|---|---|---|
| ASSUMP_NUMERIC_ACCELERATOR_MIX | GPU/ASIC mix는 운영 fleet share 공개가 없는 경우 fact가 아니라 serving-platform anchor를 바탕으로 둔 숫자 시나리오다. 공식적으로 custom accelerator deployment가 확인된 Microsoft, Google, Meta, Anthropic만 purpose-built accelerator share 상승을 Base에 반영하고, 나머지는 GPU-reference Base로 둔다. |  |  |  | 0.42 |  |
| SRC_ALIBABA_QWEN_GPU_DEPLOY | Deploy a Qwen3-32B inference service with ACS GPU computing power | Alibaba Cloud | 2025-09-18 | Tier 1 | 0.78 | https://www.alibabacloud.com/help/doc-detail/2921971.html |
| SRC_ANTHROPIC_AMAZON_COMPUTE | Anthropic and AWS expand partnership with Project Rainier | Anthropic / Amazon | 2025-2026 | Tier 1 | 0.84 | https://www.anthropic.com/news/anthropic-amazon-compute |
| SRC_ANTHROPIC_CLAUDE_DOCS | Claude model documentation | Anthropic | 2026-05-14 accessed | Tier 1 | 0.86 | https://docs.anthropic.com/en/docs/about-claude/models/overview |
| SRC_AWS_RAINIER_ACTIVE | AWS activates Project Rainier: AI compute cluster for Anthropic | Amazon Web Services / Amazon | 2025-10-29 | Tier 1 | 0.9 | https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster |
| SRC_DEEPSEEK_H800_INFERENCE | DeepSeek-V3/R1 inference system overview | DeepSeek | 2025-02-28 | Tier 1 | 0.91 | https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md |
| SRC_DEEPSEEK_R1 | DeepSeek-R1 GitHub repository | DeepSeek | 2025-01-20 | Tier 1 | 0.88 | https://github.com/deepseek-ai/DeepSeek-R1 |
| SRC_DEEPSEEK_V3 | DeepSeek-V3 GitHub repository and technical report | DeepSeek | 2024-12-26 | Tier 1 | 0.92 | https://github.com/deepseek-ai/DeepSeek-V3 |
| SRC_GOOGLE_GEMINI_TOKENS | Gemini API token documentation | Google AI for Developers | 2026-05-13 accessed | Tier 1 | 0.9 | https://ai.google.dev/gemini-api/docs/tokens |
| SRC_GOOGLE_IRONWOOD | Ironwood TPU: the age of inference | Google Cloud | 2025-04-09 | Tier 1 | 0.88 | https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ |
| SRC_GOOGLE_TPU_V6E | Cloud TPU v6e / Trillium documentation | Google Cloud | 2026-05-14 accessed | Tier 1 | 0.84 | https://cloud.google.com/tpu/docs/v6e |
| SRC_META_LLAMA | Llama model family official site and model cards | Meta AI | 2026-05-13 accessed | Tier 1 | 0.82 | https://www.llama.com/ |
| SRC_META_LLAMA4_NVIDIA | Meta Llama 4 model family optimization notes | NVIDIA Developer Blog | 2025-04-07 | Tier 2 | 0.74 | https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/ |
| SRC_META_MTIA_GENAI_2026 | Expanding Meta's Custom Silicon to Power Our AI Workloads | Meta | 2026-03-11 | Tier 1 | 0.92 | https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/ |
| SRC_MS_MAIA200 | Microsoft introduces Maia 200: New inference accelerator enhances AI performance in Azure | Microsoft | 2026-01-26 | Tier 1 | 0.91 | https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/ |
| SRC_MS_PHI | Phi model family on Azure AI Foundry / Microsoft documentation | Microsoft | 2026-05-13 accessed | Tier 1 | 0.78 | https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/concepts/models |
| SRC_MS_PHI4_TECHREPORT | Phi-4 technical report | Microsoft | 2024-12-12 | Tier 1/2 | 0.82 | https://arxiv.org/abs/2412.08905 |
| SRC_OPENAI_GPT41_DOCS | GPT-4.1 model documentation | OpenAI | 2025-04-14 | Tier 1 | 0.9 | https://platform.openai.com/docs/models/gpt-4.1 |
| SRC_OPENAI_STARGATE_ORACLE | Stargate advances with partnership with Oracle | OpenAI | 2025-07-22 | Tier 1 | 0.85 | https://openai.com/index/stargate-advances-with-partnership-with-oracle/ |
| SRC_OPENAI_STARGATE_PROGRESS | Five new Stargate sites and nearly 7 GW planned capacity | OpenAI | 2025-09-23 | Tier 1 | 0.86 | https://openai.com/index/five-new-stargate-sites/ |
| SRC_QWEN3_GITHUB | Qwen3 GitHub repository | Alibaba / Qwen Team | 2025-04-29 | Tier 1 | 0.9 | https://github.com/QwenLM/Qwen3 |
| SRC_SEMIANALYSIS_INFERENCEX | InferenceX / InferenceMAX benchmark methodology | SemiAnalysis | 2025-2026 | Tier 2 | 0.7 | https://inferencex.semianalysis.com/about |
| SRC_TENCENT_AI_INFRA_MOE | Tencent Unveils New AI Upgrades, Proprietary Innovations, and Global Solutions | Tencent | 2024-09-05 | Tier 1 | 0.84 | https://www.tencent.com/en-us/articles/2201930.html |
| SRC_TENCENT_HUNYUAN | Tencent unveils Hunyuan foundation model | Tencent | 2023-09-07 | Tier 1 | 0.82 | https://www.tencent.com/en-us/articles/2201460.html |
| SRC_TENCENT_HY3 | Tencent launches Hunyuan 3D generation model Hy3 | Tencent | 2025-01-21 | Tier 1 | 0.78 | https://www.tencent.com/en-us/articles/2202320.html |
| SRC_XAI_MODELS | xAI model documentation | xAI | 2026-05-13 accessed | Tier 1 | 0.78 | https://docs.x.ai/docs/models |
| SRC_XAI_NVIDIA_COLOSSUS | xAI's Colossus supercomputer cluster | NVIDIA | 2024-12-04 | Tier 1/2 | 0.82 | https://blogs.nvidia.com/blog/xai-colossus/ |

## Linked assumption IDs

`ASSUMP_APP_EMBEDDING`, `ASSUMP_CLOSED_MODEL_BAND`, `ASSUMP_CLUSTER_RAMP`, `ASSUMP_CN_CAPACITY_TRANSPARENCY`, `ASSUMP_CONSUMER_AI_UTILIZATION`, `ASSUMP_INFERENCE_SHARE_NOT_FACT_60`, `ASSUMP_MOE_EFFICIENCY`, `ASSUMP_MS_OPENAI_ATTRIBUTION`, `ASSUMP_NUMERIC_ACCELERATOR_MIX`, `ASSUMP_POWER_RAMP`, `ASSUMP_STARGATE_RAMP`, `ASSUMP_TPU_EFFICIENCY`

