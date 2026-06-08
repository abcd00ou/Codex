# A07 active_parameters Provenance

Short name: 모델 구조와 active parameter band

Role: dense/MoE/closed model의 token당 계산량과 benchmark proxy 선택의 맥락을 제공한다.

Headline use: 간접 사용: benchmark/proxy 선택 맥락

Confidence rule: 공식 model card는 high confidence, closed model band는 scenario confidence로 분리한다.

## Metrics covered

`model_parameter`

## 숫자 결정 로직

- 모델 parameter 정보는 직접 토큰 수식에 곱하는 값이라기보다, 어떤 InferenceX benchmark proxy가 더 가까운지 판단하는 구조적 근거다.
- open model card처럼 total/active parameter가 공개된 경우에는 높은 confidence의 fact anchor로 쓰고, closed model은 공개 추정 범위와 제품 특성을 반영한 scenario band로 둔다.
- dense와 MoE는 token당 계산량이 다르므로 total parameter와 active parameter를 분리해서 기록한다.
- 공식 model card, architecture disclosure, serving kernel trace가 나오면 closed model band를 교체한다.

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
| Microsoft | model_parameter | total=Phi 공개모델: 3B-14B급; MAI/대형 Copilot 모델: undisclosed band \| active=Phi: dense disclosed; MAI/Copilot: closed band | Microsoft는 Copilot 상용 표면이 크지만 model-owner attribution은 OpenAI dependency를 분리해야 함. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_MAIA200 |
| Google | model_parameter | total=Gemini closed frontier band; Gemma 공개모델 1B-27B급 \| active=Closed frontier active band; open Gemma disclosed | TPU 최적화가 tokens/MW 상향 요인. closed Gemini parameter는 band만 허용. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD |
| Meta | model_parameter | total=Llama 4 Scout 109B / Maverick 400B anchor; production routing undisclosed \| active=Llama 4 Scout/Maverick active 17B anchor; Meta AI serving mix band | Llama 4 MoE parameter facts improve model-side confidence; exact Meta AI active capacity remains scenario. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026 |
| xAI | model_parameter | total=Closed frontier band \| active=Closed frontier active band | Colossus scale is visible directionally, but active inference/training split remains scenario. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_XAI_MODELS |
| OpenAI | model_parameter | total=Closed frontier band only \| active=Closed frontier active band only | 사용량은 가장 크지만 parameter와 active capacity 공개성이 낮아 band/scenario 중심. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS |
| Anthropic | model_parameter | total=Closed frontier band only \| active=Closed active band only; benchmark proxy uses effective active band | Anthropic은 이번 통합 버전부터 core model owner로 포함. 파라미터는 closed band로만 처리. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE |
| DeepSeek | model_parameter | total=V3/R1 MoE: 671B total anchor \| active=MoE active: 약 37B anchor | 모델 구조는 투명하지만 회사 운영 capacity는 공개성이 낮아 scenario. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE |
| Alibaba | model_parameter | total=Qwen3 dense/MoE disclosed bands; flagship MoE up to 235B total anchor \| active=MoE active anchor up to 22B for flagship class | Qwen3 공개성이 높아 model band 신뢰도는 높고 power capacity는 별도 scenario. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY |
| Tencent | model_parameter | total=Hunyuan 100B+ anchor; Hy3 separate multimodal/3D family \| active=Closed active band; Hunyuan-Large MoE active parameter requires separate verification | Hunyuan 100B+와 2T+ pretraining token은 fact anchor, serving capacity는 scenario. | model card / closed-model band review | Official model card, platform disclosure, or provider attribution telemetry. | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE |

## Base scenario 2026 -> 2030 endpoint view

| Company | Year | Metric | Value | Confidence | Source IDs |
|---|---|---|---|---|---|
| Microsoft | 2026-2030 | model_parameter | total=Phi 공개모델: 3B-14B급; MAI/대형 Copilot 모델: undisclosed band \| active=Phi: dense disclosed; MAI/Copilot: closed band | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_MAIA200 |
| Google | 2026-2030 | model_parameter | total=Gemini closed frontier band; Gemma 공개모델 1B-27B급 \| active=Closed frontier active band; open Gemma disclosed | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD |
| Meta | 2026-2030 | model_parameter | total=Llama 4 Scout 109B / Maverick 400B anchor; production routing undisclosed \| active=Llama 4 Scout/Maverick active 17B anchor; Meta AI serving mix band | Medium-High for open model params, Medium for active capacity | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026 |
| xAI | 2026-2030 | model_parameter | total=Closed frontier band \| active=Closed frontier active band | Medium-Low | SRC_XAI_MODELS |
| OpenAI | 2026-2030 | model_parameter | total=Closed frontier band only \| active=Closed frontier active band only | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS |
| Anthropic | 2026-2030 | model_parameter | total=Closed frontier band only \| active=Closed active band only; benchmark proxy uses effective active band | Medium for capacity anchor, Low for parameters | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE |
| DeepSeek | 2026-2030 | model_parameter | total=V3/R1 MoE: 671B total anchor \| active=MoE active: 약 37B anchor | High for parameters, Low-Medium for capacity | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE |
| Alibaba | 2026-2030 | model_parameter | total=Qwen3 dense/MoE disclosed bands; flagship MoE up to 235B total anchor \| active=MoE active anchor up to 22B for flagship class | High for Qwen3 parameters, Medium-Low for active capacity | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY |
| Tencent | 2026-2030 | model_parameter | total=Hunyuan 100B+ anchor; Hy3 separate multimodal/3D family \| active=Closed active band; Hunyuan-Large MoE active parameter requires separate verification | Medium for Hunyuan published anchor, Medium-Low for active capacity | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| model_parameter | model card / closed-model band review | Microsoft는 Copilot 상용 표면이 크지만 model-owner attribution은 OpenAI dependency를 분리해야 함. | Official model card, platform disclosure, or provider attribution telemetry. |

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
