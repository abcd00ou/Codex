# A01 contracted_power_gw Provenance

Short name: 계약/발표/귀속 전력 capacity ceiling

Role: 2026-2030 전력 capacity 상한 또는 model-owner 귀속 capacity envelope를 정의한다.

Headline use: 직접 사용

Confidence rule: 공식 GW/MW 발표가 있으면 fact anchor + scenario ceiling, 없으면 scenario capacity envelope로 낮은 confidence를 유지한다.

## Metrics covered

`contracted_power_gw`

## 숫자 결정 로직

- 출처 링크는 각 회사가 어느 cloud/AI platform, 데이터센터, accelerator 조달 방향을 갖는지 확인하는 fact anchor로 사용한다.
- 공식 MW/GW 수치가 있는 경우에는 그 값을 capacity ceiling의 강한 anchor로 두고, 공개 수치가 없는 회사는 model-owner가 접근 가능한 전력 envelope를 scenario로 둔다.
- 2026과 2030 endpoint를 먼저 정하고, 중간 연도는 capacity ramp가 매년 일정하게 진행된다는 보수적 보간 규칙으로 만든다.
- 따라서 이 숫자는 회사가 직접 공시한 전력 예측치가 아니라, 공개 근거와 scenario ceiling을 결합한 벤치마크용 입력값이다.

### 링크를 숫자로 읽는 방식

아래 표는 링크 자체를 그대로 숫자로 옮긴 것이 아니라, 각 출처가 어떤 판단에 쓰였는지를 기록한다. URL이 capacity 방향성만 확인해주는 경우와 실제 수치 anchor를 제공하는 경우를 구분해서 읽어야 한다.

| ID | URL/report | 숫자 결정에 쓰인 방식 | Confidence |
|---|---|---|---|
| ASSUMP_CLUSTER_RAMP |  | xAI Colossus처럼 accelerator count와 expansion direction은 공개되지만 동일 범위의 contracted/active GW가 공개되지 않은 cluster는 staged operational power envelope로 모델링한다. | 0.46 |
| ASSUMP_CN_CAPACITY_TRANSPARENCY |  | 중국 모델 업체는 공개 capacity 투명성이 낮으므로 capacity confidence만 낮게 표시하고 모델 구조 자체는 공식 공개자료를 그대로 인정. | 0.48 |
| ASSUMP_POWER_RAMP |  | 계약 전력은 발표/공급망 방향성 anchor, active power는 실제 IT load 가동률 ramp로 별도 산정. | 0.55 |
| ASSUMP_STARGATE_RAMP |  | Stargate/Oracle capacity는 2026~2030 staged activation으로 반영. 계약/계획 전력과 active inference load를 분리. | 0.55 |
| SRC_ALIBABA_QWEN_GPU_DEPLOY | https://www.alibabacloud.com/help/doc-detail/2921971.html | Confirms an official Alibaba Cloud GPU deployment path for Qwen inference; not an operated fleet-share disclosure | 0.78 |
| SRC_ANTHROPIC_AMAZON_COMPUTE | https://www.anthropic.com/news/anthropic-amazon-compute | Anthropic contracted/hosted capacity anchor; capacity attributed to Anthropic model owner | 0.84 |
| SRC_AWS_RAINIER_ACTIVE | https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster | Confirms Anthropic-dedicated Trainium2 capacity direction and purpose-built accelerator presence | 0.9 |
| SRC_DEEPSEEK_H800_INFERENCE | https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md | Confirms disclosed DeepSeek-operated V3/R1 inference services used H800 GPUs and reports peak/average node occupancy | 0.91 |
| SRC_GOOGLE_IRONWOOD | https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ | Google TPU serving platform and inference-optimized hardware direction | 0.88 |
| SRC_GOOGLE_TPU_V6E | https://cloud.google.com/tpu/docs/v6e | Google TPU serving/training platform generation anchor | 0.84 |
| SRC_META_MTIA_GENAI_2026 | https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/ | Confirms hundreds of thousands of MTIA deployed for inference and MTIA 400/450/500 focus on GenAI inference production | 0.92 |
| SRC_MS_MAIA200 | https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/ | Confirms Maia 200 is an inference accelerator deployed for Microsoft AI models, Azure AI Foundry and Microsoft 365 Copilot | 0.91 |
| SRC_OPENAI_STARGATE_ORACLE | https://openai.com/index/stargate-advances-with-partnership-with-oracle/ | OpenAI hosting capacity ramp anchor, not a precise active IT load | 0.85 |
| SRC_OPENAI_STARGATE_PROGRESS | https://openai.com/index/five-new-stargate-sites/ | OpenAI 2030 contracted/planned capacity upper-bound anchor | 0.86 |
| SRC_TENCENT_AI_INFRA_MOE | https://www.tencent.com/en-us/articles/2201930.html | Confirms Tencent AI Infra and Hunyuan Turbo MoE service with stated inference-cost reduction | 0.84 |
| SRC_XAI_NVIDIA_COLOSSUS | https://blogs.nvidia.com/blog/xai-colossus/ | xAI GPU cluster scale anchor for active power and serving/training capacity scenarios | 0.82 |

### 행 단위 결정 샘플

대표 metric 행을 기준으로, 실제 trace에서 가져온 `why_this_number`, 산식, 교체 경로를 함께 붙였다. 이 표의 값은 모델 입력값이며, 공시 숫자와 scenario 숫자가 섞여 있을 수 있다.

| Company | Metric | Value | 왜 이 숫자인가 | Formula/rule | 교체 경로 | Source IDs |
|---|---|---|---|---|---|---|
| Microsoft | contracted_power_gw | 4.0 | Scenario envelope for Microsoft-controlled/Copilot serving burden; not an official contracted-GW disclosure. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | ASSUMP_POWER_RAMP; SRC_MS_MAIA200 |
| Google | contracted_power_gw | 4.5 | Scenario envelope for Gemini-serving capacity; official TPU hardware direction is disclosed, company-level contracted GW is not. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | ASSUMP_POWER_RAMP; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Meta | contracted_power_gw | 3.5 | Scenario envelope for Meta AI/Llama serving capacity; not an official contracted-GW figure. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | ASSUMP_POWER_RAMP; SRC_META_MTIA_GENAI_2026 |
| xAI | contracted_power_gw | 1.0 | Colossus GPU-count disclosure bounds capacity direction; contracted GW values are modeled power envelopes. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_CLUSTER_RAMP |
| OpenAI | contracted_power_gw | 5.0 | 2030 envelope is bounded by official Stargate planned/committed capacity; 2026 and timing remain staged scenario values. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_STARGATE_RAMP |
| Anthropic | contracted_power_gw | 3.5 | Hosted capacity envelope is anchored by Anthropic/AWS Project Rainier direction; it is attributed to Claude outputs, not AWS as a model owner. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_POWER_RAMP |
| DeepSeek | contracted_power_gw | 0.5 | Capacity is a low-transparency scenario; official infrastructure evidence supports H800 inference hardware, not company GW. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Alibaba | contracted_power_gw | 1.8 | Alibaba Cloud/Qwen capacity is a scenario envelope; official model and deployment documentation does not state operated GW. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_CN_CAPACITY_TRANSPARENCY |
| Tencent | contracted_power_gw | 1.2 | Tencent Cloud/Hunyuan capacity is a scenario envelope because operated model-serving GW is undisclosed. | linear interpolation between 2026 and 2030 company capacity endpoints | Company/site-level committed MW/GW, interconnect and contract disclosure. | SRC_TENCENT_AI_INFRA_MOE; ASSUMP_CN_CAPACITY_TRANSPARENCY |

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

