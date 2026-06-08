# A02 active_power_gw Provenance

Short name: 운영 투입 전력 전환

Role: 계약/계획 capacity 중 실제 energization, 냉각, 네트워크, accelerator 배치를 통과한 몫만 토큰 산식에 넣는다.

Headline use: 직접 사용

Confidence rule: site-level operational telemetry가 없으면 scenario conversion으로 둔다.

## Metrics covered

`active_power_gw`, `it_load_gw`, `operational_deployment_share`

## Base scenario 2026 -> 2030 endpoint view

| Company | Metric | 2026 -> 2030 | Derivation | Confidence | Source IDs |
|---|---|---|---|---|---|
| Alibaba | active_power_gw | 0.65 -> 3.2 GW | Derived scenario | Medium | SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Alibaba | it_load_gw | 0.528 -> 2.602 GW | Derived formula | Medium | SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Alibaba | operational_deployment_share | 0.36111111 -> 0.8 share | Scenario conversion | Medium | SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Anthropic | active_power_gw | 1.0 -> 5.5 GW | Derived scenario | Medium | SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_POWER_RAMP |
| Anthropic | it_load_gw | 0.847 -> 4.661 GW | Derived formula | Medium | SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_POWER_RAMP |
| Anthropic | operational_deployment_share | 0.28571429 -> 0.78571429 share | Scenario conversion | Medium | SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_POWER_RAMP |
| DeepSeek | active_power_gw | 0.15 -> 1.2 GW | Derived scenario | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| DeepSeek | it_load_gw | 0.121 -> 0.968 GW | Derived formula | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| DeepSeek | operational_deployment_share | 0.3 -> 0.66666667 share | Scenario conversion | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Google | active_power_gw | 2.2 -> 6.8 GW | Derived scenario | Medium-High | ASSUMP_POWER_RAMP; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Google | it_load_gw | 1.864 -> 5.763 GW | Derived formula | Medium-High | ASSUMP_POWER_RAMP; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Google | operational_deployment_share | 0.48888889 -> 0.85 share | Scenario conversion | Medium-High | ASSUMP_POWER_RAMP; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Meta | active_power_gw | 1.6 -> 5.8 GW | Derived scenario | Medium | ASSUMP_POWER_RAMP; SRC_META_MTIA_GENAI_2026 |
| Meta | it_load_gw | 1.333 -> 4.833 GW | Derived formula | Medium | ASSUMP_POWER_RAMP; SRC_META_MTIA_GENAI_2026 |
| Meta | operational_deployment_share | 0.45714286 -> 0.82857143 share | Scenario conversion | Medium | ASSUMP_POWER_RAMP; SRC_META_MTIA_GENAI_2026 |
| Microsoft | active_power_gw | 1.8 -> 6.2 GW | Derived scenario | Medium | ASSUMP_POWER_RAMP; SRC_MS_MAIA200 |
| Microsoft | it_load_gw | 1.5 -> 5.167 GW | Derived formula | Medium | ASSUMP_POWER_RAMP; SRC_MS_MAIA200 |
| Microsoft | operational_deployment_share | 0.45 -> 0.68888889 share | Scenario conversion | Medium | ASSUMP_POWER_RAMP; SRC_MS_MAIA200 |
| OpenAI | active_power_gw | 1.4 -> 8.5 GW | Derived scenario | Medium | SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_STARGATE_RAMP |
| OpenAI | it_load_gw | 1.167 -> 7.083 GW | Derived formula | Medium | SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_STARGATE_RAMP |
| OpenAI | operational_deployment_share | 0.28 -> 0.70833333 share | Scenario conversion | Medium | SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_STARGATE_RAMP |
| Tencent | active_power_gw | 0.45 -> 2.4 GW | Derived scenario | Medium-Low | SRC_TENCENT_AI_INFRA_MOE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Tencent | it_load_gw | 0.366 -> 1.951 GW | Derived formula | Medium-Low | SRC_TENCENT_AI_INFRA_MOE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Tencent | operational_deployment_share | 0.375 -> 0.8 share | Scenario conversion | Medium-Low | SRC_TENCENT_AI_INFRA_MOE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| xAI | active_power_gw | 0.35 -> 2.5 GW | Derived scenario | Medium-Low | SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_CLUSTER_RAMP |
| xAI | it_load_gw | 0.287 -> 2.049 GW | Derived formula | Medium-Low | SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_CLUSTER_RAMP |
| xAI | operational_deployment_share | 0.35 -> 0.83333333 share | Scenario conversion | Medium-Low | SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_CLUSTER_RAMP |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| operational_deployment_share | active_power_gw / contracted_power_gw | This is the single explicit conversion from contracted/attributed capacity to operationally usable capacity. | Energized operational capacity divided by contracted/attributed capacity. |
| active_power_gw | contracted_power_gw * operational_deployment_share | Active GW is a staged operational deployment fraction of modeled capacity, reflecting site energization and accelerator availability. | Energization dates, accelerator deliveries and operational powered-rack telemetry. |
| it_load_gw | active_power_gw / pue | Facility power is converted to IT-deliverable power before attributing AI workloads. | Recompute once active power and PUE become site-observable. |

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

