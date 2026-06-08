# A01 contracted_power_gw Provenance

Short name: 계약/발표/귀속 전력 capacity ceiling

Role: 2026-2030 전력 capacity 상한 또는 model-owner 귀속 capacity envelope를 정의한다.

Headline use: 직접 사용

Confidence rule: 공식 GW/MW 발표가 있으면 fact anchor + scenario ceiling, 없으면 scenario capacity envelope로 낮은 confidence를 유지한다.

## Metrics covered

`contracted_power_gw`

## Base scenario 2026 -> 2030 endpoint view

| Company | Metric | 2026 -> 2030 | Derivation | Confidence | Source IDs |
|---|---|---|---|---|---|
| Alibaba | contracted_power_gw | 1.8 -> 4.0 GW | Scenario capacity envelope | Medium | SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Anthropic | contracted_power_gw | 3.5 -> 7.0 GW | Fact anchor + scenario ceiling | Medium | SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_POWER_RAMP |
| DeepSeek | contracted_power_gw | 0.5 -> 1.8 GW | Scenario capacity envelope | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Google | contracted_power_gw | 4.5 -> 8.0 GW | Scenario capacity envelope | Medium-High | ASSUMP_POWER_RAMP; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Meta | contracted_power_gw | 3.5 -> 7.0 GW | Scenario capacity envelope | Medium | ASSUMP_POWER_RAMP; SRC_META_MTIA_GENAI_2026 |
| Microsoft | contracted_power_gw | 4.0 -> 9.0 GW | Scenario capacity envelope | Medium | ASSUMP_POWER_RAMP; SRC_MS_MAIA200 |
| OpenAI | contracted_power_gw | 5.0 -> 12.0 GW | Fact anchor + scenario ceiling | Medium | SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_STARGATE_RAMP |
| Tencent | contracted_power_gw | 1.2 -> 3.0 GW | Scenario capacity envelope | Medium-Low | SRC_TENCENT_AI_INFRA_MOE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| xAI | contracted_power_gw | 1.0 -> 3.0 GW | Fact anchor + scenario ceiling | Medium-Low | SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_CLUSTER_RAMP |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| contracted_power_gw | linear interpolation between 2026 and 2030 company capacity endpoints | Scenario envelope for Microsoft-controlled/Copilot serving burden; not an official contracted-GW disclosure. | Company/site-level committed MW/GW, interconnect and contract disclosure. |

## Source catalog for this assumption

| ID | Title/description | Publisher/category | Date | Tier | Confidence | URL/report |
|---|---|---|---|---|---|---|
| ASSUMP_CLUSTER_RAMP | xAI Colossus처럼 accelerator count와 expansion direction은 공개되지만 동일 범위의 contracted/active GW가 공개되지 않은 cluster는 staged operational power envelope로 모델링한다. |  |  |  | 0.46 |  |
| ASSUMP_CN_CAPACITY_TRANSPARENCY | 중국 모델 업체는 공개 capacity 투명성이 낮으므로 capacity confidence만 낮게 표시하고 모델 구조 자체는 공식 공개자료를 그대로 인정. |  |  |  | 0.48 |  |
| ASSUMP_POWER_RAMP | 계약 전력은 발표/공급망 방향성 anchor, active power는 실제 IT load 가동률 ramp로 별도 산정. |  |  |  | 0.55 |  |
| ASSUMP_STARGATE_RAMP | Stargate/Oracle capacity는 2026~2030 staged activation으로 반영. 계약/계획 전력과 active inference load를 분리. |  |  |  | 0.55 |  |
| SRC_ALIBABA_QWEN_GPU_DEPLOY | Deploy a Qwen3-32B inference service with ACS GPU computing power | Alibaba Cloud | 2025-09-18 | Tier 1 | 0.78 | https://www.alibabacloud.com/help/doc-detail/2921971.html |
| SRC_ANTHROPIC_AMAZON_COMPUTE | Anthropic and AWS expand partnership with Project Rainier | Anthropic / Amazon | 2025-2026 | Tier 1 | 0.84 | https://www.anthropic.com/news/anthropic-amazon-compute |
| SRC_AWS_RAINIER_ACTIVE | AWS activates Project Rainier: AI compute cluster for Anthropic | Amazon Web Services / Amazon | 2025-10-29 | Tier 1 | 0.9 | https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster |
| SRC_DEEPSEEK_H800_INFERENCE | DeepSeek-V3/R1 inference system overview | DeepSeek | 2025-02-28 | Tier 1 | 0.91 | https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md |
| SRC_GOOGLE_IRONWOOD | Ironwood TPU: the age of inference | Google Cloud | 2025-04-09 | Tier 1 | 0.88 | https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ |
| SRC_GOOGLE_TPU_V6E | Cloud TPU v6e / Trillium documentation | Google Cloud | 2026-05-14 accessed | Tier 1 | 0.84 | https://cloud.google.com/tpu/docs/v6e |
| SRC_META_MTIA_GENAI_2026 | Expanding Meta's Custom Silicon to Power Our AI Workloads | Meta | 2026-03-11 | Tier 1 | 0.92 | https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/ |
| SRC_MS_MAIA200 | Microsoft introduces Maia 200: New inference accelerator enhances AI performance in Azure | Microsoft | 2026-01-26 | Tier 1 | 0.91 | https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/ |
| SRC_OPENAI_STARGATE_ORACLE | Stargate advances with partnership with Oracle | OpenAI | 2025-07-22 | Tier 1 | 0.85 | https://openai.com/index/stargate-advances-with-partnership-with-oracle/ |
| SRC_OPENAI_STARGATE_PROGRESS | Five new Stargate sites and nearly 7 GW planned capacity | OpenAI | 2025-09-23 | Tier 1 | 0.86 | https://openai.com/index/five-new-stargate-sites/ |
| SRC_TENCENT_AI_INFRA_MOE | Tencent Unveils New AI Upgrades, Proprietary Innovations, and Global Solutions | Tencent | 2024-09-05 | Tier 1 | 0.84 | https://www.tencent.com/en-us/articles/2201930.html |
| SRC_XAI_NVIDIA_COLOSSUS | xAI's Colossus supercomputer cluster | NVIDIA | 2024-12-04 | Tier 1/2 | 0.82 | https://blogs.nvidia.com/blog/xai-colossus/ |

## Linked assumption IDs

`ASSUMP_APP_EMBEDDING`, `ASSUMP_CLOSED_MODEL_BAND`, `ASSUMP_CLUSTER_RAMP`, `ASSUMP_CN_CAPACITY_TRANSPARENCY`, `ASSUMP_CONSUMER_AI_UTILIZATION`, `ASSUMP_INFERENCE_SHARE_NOT_FACT_60`, `ASSUMP_MOE_EFFICIENCY`, `ASSUMP_MS_OPENAI_ATTRIBUTION`, `ASSUMP_NUMERIC_ACCELERATOR_MIX`, `ASSUMP_POWER_RAMP`, `ASSUMP_STARGATE_RAMP`, `ASSUMP_TPU_EFFICIENCY`

