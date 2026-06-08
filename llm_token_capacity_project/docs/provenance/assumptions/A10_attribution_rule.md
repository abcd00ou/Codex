# A10 attribution_rule Provenance

Short name: model-owner attribution과 host 중복 제거

Role: AWS/Oracle/CoreWeave 같은 host capacity와 model-owner output을 중복 계산하지 않도록 귀속 규칙을 정의한다.

Headline use: 간접 사용: row inclusion/exclusion

Confidence rule: 공식 ownership/hosting 관계는 source로 고정하고, capacity split은 scenario로 둔다.

## Metrics covered

`attribution_rule`

## 숫자 결정 로직

- attribution_rule은 host capacity와 model-owner output을 중복 계산하지 않기 위한 규칙이다.
- 출처는 AWS, Oracle, CoreWeave 같은 host와 model owner 사이의 platform/hosting 관계를 확인하는 데 쓰고, 정확한 capacity split을 직접 뜻하지는 않는다.
- headline forecast는 model owner가 상용 output token을 만들어내는 capacity만 세며, host-only rows는 별도 supply-side 근거로 분리한다.
- 공식 capacity ownership, reserved instance 계약, accelerator-hour attribution telemetry가 나오면 이 규칙을 더 세밀하게 바꿀 수 있다.

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
| SRC_META_LLAMA | https://www.llama.com/ | Llama model family and open model parameter disclosures where available | 0.82 |
| SRC_META_LLAMA4_NVIDIA | https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/ | Llama 4 Scout/Maverick total-active parameter anchor when official Meta page is less accessible | 0.74 |
| SRC_META_MTIA_GENAI_2026 | https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/ | Confirms hundreds of thousands of MTIA deployed for inference and MTIA 400/450/500 focus on GenAI inference production | 0.92 |
| SRC_MS_MAIA200 | https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/ | Confirms Maia 200 is an inference accelerator deployed for Microsoft AI models, Azure AI Foundry and Microsoft 365 Copilot | 0.91 |
| SRC_MS_PHI | https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/concepts/models | Microsoft-owned small language model family anchor | 0.78 |
| SRC_OPENAI_GPT41_DOCS | https://platform.openai.com/docs/models/gpt-4.1 | OpenAI commercial model family and closed-model parameter disclosure boundary | 0.9 |
| SRC_OPENAI_STARGATE_ORACLE | https://openai.com/index/stargate-advances-with-partnership-with-oracle/ | OpenAI hosting capacity ramp anchor, not a precise active IT load | 0.85 |
| SRC_OPENAI_STARGATE_PROGRESS | https://openai.com/index/five-new-stargate-sites/ | OpenAI 2030 contracted/planned capacity upper-bound anchor | 0.86 |
| SRC_QWEN3_GITHUB | https://github.com/QwenLM/Qwen3 | Qwen3 dense/MoE family and active parameter anchor | 0.9 |
| SRC_TENCENT_AI_INFRA_MOE | https://www.tencent.com/en-us/articles/2201930.html | Confirms Tencent AI Infra and Hunyuan Turbo MoE service with stated inference-cost reduction | 0.84 |
| SRC_TENCENT_HUNYUAN | https://www.tencent.com/en-us/articles/2201460.html | Tencent Hunyuan parameter and pretraining token anchor | 0.82 |
| SRC_TENCENT_HY3 | https://www.tencent.com/en-us/articles/2202320.html | Tencent Hunyuan commercial surface and model-family anchor | 0.78 |
| SRC_XAI_MODELS | https://docs.x.ai/docs/models | Grok commercial model surface and closed-model disclosure boundary | 0.78 |

### 행 단위 결정 샘플

대표 metric 행을 기준으로, 실제 trace에서 가져온 `why_this_number`, 산식, 교체 경로를 함께 붙였다. 이 표의 값은 모델 입력값이며, 공시 숫자와 scenario 숫자가 섞여 있을 수 있다.

| Company | Metric | Value | 왜 이 숫자인가 | Formula/rule | 교체 경로 | Source IDs |
|---|---|---|---|---|---|---|
| Microsoft | attribution_rule | Microsoft-owned token은 Phi/MAI/Copilot serving으로, OpenAI model output은 OpenAI row에도 별도 표기 | Commercial surface: Microsoft 365 Copilot, GitHub Copilot, Azure AI Foundry; serving platform: Azure GPU + Maia inference + OpenAI-hosted dependency split | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_MAIA200 |
| Google | attribution_rule | Google-owned Gemini token generation, Anthropic hosted capacity excluded from core | Commercial surface: Gemini app/API, Google Workspace, Cloud Vertex AI; serving platform: TPU v5/v6/Ironwood + selective NVIDIA GPU | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD |
| Meta | attribution_rule | Meta-owned consumer and open model serving; third-party hosted Llama not counted in Meta owner tokens | Commercial surface: Meta AI app, WhatsApp/Instagram/Facebook AI, open Llama ecosystem; serving platform: NVIDIA GPU fleet + MTIA inference layer | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026 |
| xAI | attribution_rule | xAI-owned Grok token generation; X social integration counted only when model generated | Commercial surface: Grok app/API, X integration, enterprise API; serving platform: Colossus-style NVIDIA GPU clusters | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_XAI_MODELS |
| OpenAI | attribution_rule | OpenAI model output counted here, including OpenAI models served through Microsoft channels when model ownership is OpenAI | Commercial surface: ChatGPT, API, enterprise, Microsoft/OpenAI distribution; serving platform: Azure + Oracle/Stargate + partner GPU clusters | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS |
| Anthropic | attribution_rule | Anthropic model output counted under Anthropic, even when served through AWS/Google host capacity | Commercial surface: Claude app/API, Amazon Bedrock, Google Cloud Vertex AI; serving platform: AWS Trainium/Rainier + Google Cloud TPU/GPU hosted capacity | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE |
| DeepSeek | attribution_rule | DeepSeek direct app/API tokens counted; third-party self-hosted derivatives excluded unless DeepSeek-operated | Commercial surface: DeepSeek app/API, open model derivatives, enterprise deployments; serving platform: GPU-constrained serving with MoE efficiency and local cloud deployments | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE |
| Alibaba | attribution_rule | Alibaba-operated Qwen serving counted; open-source third-party self-hosting excluded | Commercial surface: Alibaba Cloud Model Studio, Qwen Chat/API, enterprise cloud; serving platform: Alibaba Cloud GPU/China accelerator mix | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY |
| Tencent | attribution_rule | Tencent-operated Hunyuan/Yuanbao tokens counted; embedded non-LLM media generation separated | Commercial surface: Tencent Yuanbao, WeChat/QQ enterprise AI, Tencent Cloud; serving platform: Tencent Cloud GPU/China accelerator mix | model-owner row attribution rule | Official model card, platform disclosure, or provider attribution telemetry. | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE |

## Base scenario 2026 -> 2030 endpoint view

| Company | Year | Metric | Value | Confidence | Source IDs |
|---|---|---|---|---|---|
| Microsoft | 2026-2030 | attribution_rule | Microsoft-owned token은 Phi/MAI/Copilot serving으로, OpenAI model output은 OpenAI row에도 별도 표기 | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_MAIA200 |
| Google | 2026-2030 | attribution_rule | Google-owned Gemini token generation, Anthropic hosted capacity excluded from core | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD |
| Meta | 2026-2030 | attribution_rule | Meta-owned consumer and open model serving; third-party hosted Llama not counted in Meta owner tokens | Medium-High for open model params, Medium for active capacity | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026 |
| xAI | 2026-2030 | attribution_rule | xAI-owned Grok token generation; X social integration counted only when model generated | Medium-Low | SRC_XAI_MODELS |
| OpenAI | 2026-2030 | attribution_rule | OpenAI model output counted here, including OpenAI models served through Microsoft channels when model ownership is OpenAI | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS |
| Anthropic | 2026-2030 | attribution_rule | Anthropic model output counted under Anthropic, even when served through AWS/Google host capacity | Medium for capacity anchor, Low for parameters | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE |
| DeepSeek | 2026-2030 | attribution_rule | DeepSeek direct app/API tokens counted; third-party self-hosted derivatives excluded unless DeepSeek-operated | High for parameters, Low-Medium for capacity | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE |
| Alibaba | 2026-2030 | attribution_rule | Alibaba-operated Qwen serving counted; open-source third-party self-hosting excluded | High for Qwen3 parameters, Medium-Low for active capacity | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY |
| Tencent | 2026-2030 | attribution_rule | Tencent-operated Hunyuan/Yuanbao tokens counted; embedded non-LLM media generation separated | Medium for Hunyuan published anchor, Medium-Low for active capacity | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| attribution_rule | model-owner row attribution rule | Commercial surface: Microsoft 365 Copilot, GitHub Copilot, Azure AI Foundry; serving platform: Azure GPU + Maia inference + OpenAI-hosted dependency split | Official model card, platform disclosure, or provider attribution telemetry. |

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
| SRC_META_LLAMA | Llama model family official site and model cards | Meta AI | 2026-05-13 accessed | Tier 1 | 0.82 | https://www.llama.com/ |
| SRC_META_LLAMA4_NVIDIA | Meta Llama 4 model family optimization notes | NVIDIA Developer Blog | 2025-04-07 | Tier 2 | 0.74 | https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/ |
| SRC_META_MTIA_GENAI_2026 | Expanding Meta's Custom Silicon to Power Our AI Workloads | Meta | 2026-03-11 | Tier 1 | 0.92 | https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/ |
| SRC_MS_MAIA200 | Microsoft introduces Maia 200: New inference accelerator enhances AI performance in Azure | Microsoft | 2026-01-26 | Tier 1 | 0.91 | https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/ |
| SRC_MS_PHI | Phi model family on Azure AI Foundry / Microsoft documentation | Microsoft | 2026-05-13 accessed | Tier 1 | 0.78 | https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/concepts/models |
| SRC_OPENAI_GPT41_DOCS | GPT-4.1 model documentation | OpenAI | 2025-04-14 | Tier 1 | 0.9 | https://platform.openai.com/docs/models/gpt-4.1 |
| SRC_OPENAI_STARGATE_ORACLE | Stargate advances with partnership with Oracle | OpenAI | 2025-07-22 | Tier 1 | 0.85 | https://openai.com/index/stargate-advances-with-partnership-with-oracle/ |
| SRC_OPENAI_STARGATE_PROGRESS | Five new Stargate sites and nearly 7 GW planned capacity | OpenAI | 2025-09-23 | Tier 1 | 0.86 | https://openai.com/index/five-new-stargate-sites/ |
| SRC_QWEN3_GITHUB | Qwen3 GitHub repository | Alibaba / Qwen Team | 2025-04-29 | Tier 1 | 0.9 | https://github.com/QwenLM/Qwen3 |
| SRC_TENCENT_AI_INFRA_MOE | Tencent Unveils New AI Upgrades, Proprietary Innovations, and Global Solutions | Tencent | 2024-09-05 | Tier 1 | 0.84 | https://www.tencent.com/en-us/articles/2201930.html |
| SRC_TENCENT_HUNYUAN | Tencent unveils Hunyuan foundation model | Tencent | 2023-09-07 | Tier 1 | 0.82 | https://www.tencent.com/en-us/articles/2201460.html |
| SRC_TENCENT_HY3 | Tencent launches Hunyuan 3D generation model Hy3 | Tencent | 2025-01-21 | Tier 1 | 0.78 | https://www.tencent.com/en-us/articles/2202320.html |
| SRC_XAI_MODELS | xAI model documentation | xAI | 2026-05-13 accessed | Tier 1 | 0.78 | https://docs.x.ai/docs/models |
