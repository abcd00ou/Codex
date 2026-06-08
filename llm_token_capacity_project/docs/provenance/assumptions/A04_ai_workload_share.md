# A04 ai_workload_share Provenance

Short name: IT load 중 AI workload 몫

Role: IT load 중 model-owner AI training/serving에 귀속되는 몫만 분리한다.

Headline use: 직접 사용

Confidence rule: AI platform 방향은 source로 확인하되 workload share 수치는 telemetry 부재 시 scenario다.

## Metrics covered

`ai_it_load_gw`, `ai_workload_share`

## 숫자 결정 로직

- AI workload share는 IT load 중 model training, inference, evaluation, embedding, safety pipeline 등 AI workload에 귀속되는 몫이다.
- 출처는 회사가 AI 제품/모델/인프라를 확장하고 있다는 방향성 확인에 쓰고, 정확한 workload split은 공개 telemetry가 아니므로 scenario로 둔다.
- ai_it_load_gw는 it_load_gw에 ai_workload_share를 곱해 만든다.
- cluster scheduler 로그, accelerator-hour accounting, business unit별 power allocation이 나오면 이 assumption을 교체한다.

### 링크를 숫자로 읽는 방식

아래 표는 링크 자체를 그대로 숫자로 옮긴 것이 아니라, 각 출처가 어떤 판단에 쓰였는지를 기록한다. URL이 capacity 방향성만 확인해주는 경우와 실제 수치 anchor를 제공하는 경우를 구분해서 읽어야 한다.

| ID | URL/report | 숫자 결정에 쓰인 방식 | Confidence |
|---|---|---|---|
| SRC_ALIBABA_QWEN_GPU_DEPLOY | https://www.alibabacloud.com/help/doc-detail/2921971.html | Confirms an official Alibaba Cloud GPU deployment path for Qwen inference; not an operated fleet-share disclosure | 0.78 |
| SRC_ANTHROPIC_AMAZON_COMPUTE | https://www.anthropic.com/news/anthropic-amazon-compute | Anthropic contracted/hosted capacity anchor; capacity attributed to Anthropic model owner | 0.84 |
| SRC_ANTHROPIC_CLAUDE_DOCS | https://docs.anthropic.com/en/docs/about-claude/models/overview | Claude commercial model family and closed-model disclosure boundary | 0.86 |
| SRC_AWS_RAINIER_ACTIVE | https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster | Confirms Anthropic-dedicated Trainium2 capacity direction and purpose-built accelerator presence | 0.9 |
| SRC_DEEPSEEK_H800_INFERENCE | https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md | Confirms disclosed DeepSeek-operated V3/R1 inference services used H800 GPUs and reports peak/average node occupancy | 0.91 |
| SRC_DEEPSEEK_R1 | https://github.com/deepseek-ai/DeepSeek-R1 | Reasoning model family and distillation ecosystem anchor | 0.88 |
| SRC_DEEPSEEK_V3 | https://github.com/deepseek-ai/DeepSeek-V3 | MoE total and active parameter anchor | 0.92 |
| SRC_GOOGLE_GEMINI_TOKENS | https://ai.google.dev/gemini-api/docs/tokens | Token accounting and context handling anchor for Gemini surfaces | 0.9 |
| SRC_GOOGLE_IRONWOOD | https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ | Google TPU serving platform and inference-optimized hardware direction | 0.88 |
| SRC_GOOGLE_TPU_V6E | https://cloud.google.com/tpu/docs/v6e | Google TPU serving/training platform generation anchor | 0.84 |
| SRC_META_LLAMA | https://www.llama.com/ | Llama model family and open model parameter disclosures where available | 0.82 |
| SRC_META_LLAMA4_NVIDIA | https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/ | Llama 4 Scout/Maverick total-active parameter anchor when official Meta page is less accessible | 0.74 |
| SRC_META_MTIA_GENAI_2026 | https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/ | Confirms hundreds of thousands of MTIA deployed for inference and MTIA 400/450/500 focus on GenAI inference production | 0.92 |
| SRC_MS_MAIA200 | https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/ | Confirms Maia 200 is an inference accelerator deployed for Microsoft AI models, Azure AI Foundry and Microsoft 365 Copilot | 0.91 |
| SRC_MS_PHI | https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/concepts/models | Microsoft-owned small language model family anchor | 0.78 |
| SRC_MS_PHI4_TECHREPORT | https://arxiv.org/abs/2412.08905 | Microsoft-owned Phi-4 14B parameter anchor | 0.82 |
| SRC_OPENAI_GPT41_DOCS | https://platform.openai.com/docs/models/gpt-4.1 | OpenAI commercial model family and closed-model parameter disclosure boundary | 0.9 |
| SRC_OPENAI_STARGATE_ORACLE | https://openai.com/index/stargate-advances-with-partnership-with-oracle/ | OpenAI hosting capacity ramp anchor, not a precise active IT load | 0.85 |
| SRC_OPENAI_STARGATE_PROGRESS | https://openai.com/index/five-new-stargate-sites/ | OpenAI 2030 contracted/planned capacity upper-bound anchor | 0.86 |
| SRC_QWEN3_GITHUB | https://github.com/QwenLM/Qwen3 | Qwen3 dense/MoE family and active parameter anchor | 0.9 |
| SRC_TENCENT_AI_INFRA_MOE | https://www.tencent.com/en-us/articles/2201930.html | Confirms Tencent AI Infra and Hunyuan Turbo MoE service with stated inference-cost reduction | 0.84 |
| SRC_TENCENT_HUNYUAN | https://www.tencent.com/en-us/articles/2201460.html | Tencent Hunyuan parameter and pretraining token anchor | 0.82 |
| SRC_TENCENT_HY3 | https://www.tencent.com/en-us/articles/2202320.html | Tencent Hunyuan commercial surface and model-family anchor | 0.78 |
| SRC_XAI_MODELS | https://docs.x.ai/docs/models | Grok commercial model surface and closed-model disclosure boundary | 0.78 |
| SRC_XAI_NVIDIA_COLOSSUS | https://blogs.nvidia.com/blog/xai-colossus/ | xAI GPU cluster scale anchor for active power and serving/training capacity scenarios | 0.82 |

### 행 단위 결정 샘플

대표 metric 행을 기준으로, 실제 trace에서 가져온 `why_this_number`, 산식, 교체 경로를 함께 붙였다. 이 표의 값은 모델 입력값이며, 공시 숫자와 scenario 숫자가 섞여 있을 수 있다.

| Company | Metric | Value | 왜 이 숫자인가 | Formula/rule | 교체 경로 | Source IDs |
|---|---|---|---|---|---|---|
| Microsoft | ai_workload_share | 0.86 | Azure/Copilot serving burden is AI-oriented but shares infrastructure with platform and reserve overhead; 86% is a scenario allocation. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200 |
| Google | ai_workload_share | 0.88 | Gemini/Vertex TPU serving is AI-dedicated in the modeled capacity envelope; 88% excludes platform/reserve load. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Meta | ai_workload_share | 0.87 | The modeled fleet is focused on AI workloads across Meta AI surfaces; non-LLM ranking/platform overhead is excluded through the 87% share. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026 |
| xAI | ai_workload_share | 0.85 | Colossus is AI-centric; 85% retains cooling/IT allocation boundary and non-serving AI work. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS |
| OpenAI | ai_workload_share | 0.88 | Stargate capacity is AI-oriented but includes reserve, platform and non-token AI activity; 88% is a scenario. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS |
| Anthropic | ai_workload_share | 0.86 | Anthropic-directed hosted capacity is predominantly AI; 86% excludes platform, reserve and non-serving allocation. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE |
| DeepSeek | ai_workload_share | 0.82 | DeepSeek-operated service capacity is modeled as AI-focused, reduced for reserve and ancillary processing. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE |
| Alibaba | ai_workload_share | 0.84 | Model Studio/Qwen-serving envelope is AI-focused, while cloud platform/reserve allocation is excluded through 84%. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY |
| Tencent | ai_workload_share | 0.84 | Modeled Hunyuan-serving capacity is AI-focused; 84% excludes cloud/platform and reserve overhead. | ai_it_load_gw = it_load_gw * ai_workload_share | Model-owner AI workload allocation or cluster scheduling telemetry. | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE |

## Base scenario 2026 -> 2030 endpoint view

| Company | Metric | 2026 -> 2030 | Derivation | Confidence | Source IDs |
|---|---|---|---|---|---|
| Alibaba | ai_it_load_gw | 0.444 -> 2.185 GW | Derived formula | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY |
| Alibaba | ai_workload_share | 0.84 -> 0.84 share | Scenario allocation | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY |
| Anthropic | ai_it_load_gw | 0.729 -> 4.008 GW | Derived formula | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE |
| Anthropic | ai_workload_share | 0.86 -> 0.86 share | Scenario allocation | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE |
| DeepSeek | ai_it_load_gw | 0.099 -> 0.794 GW | Derived formula | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE |
| DeepSeek | ai_workload_share | 0.82 -> 0.82 share | Scenario allocation | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE |
| Google | ai_it_load_gw | 1.641 -> 5.071 GW | Derived formula | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Google | ai_workload_share | 0.88 -> 0.88 share | Scenario allocation | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E |
| Meta | ai_it_load_gw | 1.16 -> 4.205 GW | Derived formula | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026 |
| Meta | ai_workload_share | 0.87 -> 0.87 share | Scenario allocation | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026 |
| Microsoft | ai_it_load_gw | 1.29 -> 4.443 GW | Derived formula | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200 |
| Microsoft | ai_workload_share | 0.86 -> 0.86 share | Scenario allocation | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200 |
| OpenAI | ai_it_load_gw | 1.027 -> 6.233 GW | Derived formula | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS |
| OpenAI | ai_workload_share | 0.88 -> 0.88 share | Scenario allocation | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS |
| Tencent | ai_it_load_gw | 0.307 -> 1.639 GW | Derived formula | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE |
| Tencent | ai_workload_share | 0.84 -> 0.84 share | Scenario allocation | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE |
| xAI | ai_it_load_gw | 0.244 -> 1.742 GW | Derived formula | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS |
| xAI | ai_workload_share | 0.85 -> 0.85 share | Scenario allocation | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| ai_workload_share | ai_it_load_gw = it_load_gw * ai_workload_share | Azure/Copilot serving burden is AI-oriented but shares infrastructure with platform and reserve overhead; 86% is a scenario allocation. | Model-owner AI workload allocation or cluster scheduling telemetry. |
| ai_it_load_gw | it_load_gw * ai_workload_share | Only the AI-attributed portion of IT load enters training/inference allocation. | Recompute after ai_workload_share is replaced by telemetry. |

## Source catalog for this assumption

| ID | Title/description | Publisher/category | Date | Tier | Confidence | URL/report |
|---|---|---|---|---|---|---|
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
| SRC_TENCENT_AI_INFRA_MOE | Tencent Unveils New AI Upgrades, Proprietary Innovations, and Global Solutions | Tencent | 2024-09-05 | Tier 1 | 0.84 | https://www.tencent.com/en-us/articles/2201930.html |
| SRC_TENCENT_HUNYUAN | Tencent unveils Hunyuan foundation model | Tencent | 2023-09-07 | Tier 1 | 0.82 | https://www.tencent.com/en-us/articles/2201460.html |
| SRC_TENCENT_HY3 | Tencent launches Hunyuan 3D generation model Hy3 | Tencent | 2025-01-21 | Tier 1 | 0.78 | https://www.tencent.com/en-us/articles/2202320.html |
| SRC_XAI_MODELS | xAI model documentation | xAI | 2026-05-13 accessed | Tier 1 | 0.78 | https://docs.x.ai/docs/models |
| SRC_XAI_NVIDIA_COLOSSUS | xAI's Colossus supercomputer cluster | NVIDIA | 2024-12-04 | Tier 1/2 | 0.82 | https://blogs.nvidia.com/blog/xai-colossus/ |

## Linked assumption IDs

`ASSUMP_APP_EMBEDDING`, `ASSUMP_CLOSED_MODEL_BAND`, `ASSUMP_CLUSTER_RAMP`, `ASSUMP_CN_CAPACITY_TRANSPARENCY`, `ASSUMP_CONSUMER_AI_UTILIZATION`, `ASSUMP_INFERENCE_SHARE_NOT_FACT_60`, `ASSUMP_MOE_EFFICIENCY`, `ASSUMP_MS_OPENAI_ATTRIBUTION`, `ASSUMP_NUMERIC_ACCELERATOR_MIX`, `ASSUMP_POWER_RAMP`, `ASSUMP_STARGATE_RAMP`, `ASSUMP_TPU_EFFICIENCY`

