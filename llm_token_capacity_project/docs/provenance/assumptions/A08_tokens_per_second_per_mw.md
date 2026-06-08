# A08 tokens_per_second_per_mw Provenance

Short name: InferenceX 기반 generated output TPS/MW

Role: 1MW inference load가 초당 몇 generated output token을 만들 수 있는지 결정한다.

Headline use: 직접 사용

Confidence rule: InferenceX는 proxy/benchmark이며 production telemetry가 아니므로 workload fit factor와 source caveat를 같이 붙인다.

## Metrics covered

`commercial_workload_fit_factor`, `fleet_reference_tps_per_mw`, `purpose_built_tps_per_mw`, `reference_serving_tps_per_mw`, `tokens_per_second_per_mw`

## Base scenario 2026 -> 2030 endpoint view

| Company | Metric | 2026 -> 2030 | Derivation | Confidence | Source IDs |
|---|---|---|---|---|---|
| Alibaba | commercial_workload_fit_factor | 0.9 -> 0.9 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | fleet_reference_tps_per_mw | 179145 -> 179145 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | purpose_built_tps_per_mw | 161230 -> 161230 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | reference_serving_tps_per_mw | 161230 -> 161230 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | tokens_per_second_per_mw | 161230 -> 161230 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | commercial_workload_fit_factor | 0.5 -> 0.5 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | fleet_reference_tps_per_mw | 656312 -> 719606 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | purpose_built_tps_per_mw | 362470 -> 362470 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | reference_serving_tps_per_mw | 328156 -> 359803 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | tokens_per_second_per_mw | 328156 -> 359803 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | commercial_workload_fit_factor | 0.85 -> 0.85 share of public reference throughput | Scenario assumption | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | fleet_reference_tps_per_mw | 110380 -> 443721 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | purpose_built_tps_per_mw | 86058 -> 86058 generated output tokens/sec/MW | Conservative no-uplift proxy | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | reference_serving_tps_per_mw | 93823 -> 377163 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | tokens_per_second_per_mw | 93823 -> 377163 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | commercial_workload_fit_factor | 0.6 -> 0.6 share of public reference throughput | Scenario assumption | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | fleet_reference_tps_per_mw | 685825 -> 721384 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | purpose_built_tps_per_mw | 434964 -> 434964 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | reference_serving_tps_per_mw | 411495 -> 432830 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | tokens_per_second_per_mw | 411495 -> 432830 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | commercial_workload_fit_factor | 0.9 -> 0.9 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | fleet_reference_tps_per_mw | 283741 -> 282958 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | purpose_built_tps_per_mw | 254574 -> 254574 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | reference_serving_tps_per_mw | 255367 -> 254662 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | tokens_per_second_per_mw | 255367 -> 254662 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | commercial_workload_fit_factor | 0.6 -> 0.6 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | fleet_reference_tps_per_mw | 548924 -> 705383 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | purpose_built_tps_per_mw | 434964 -> 434964 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | reference_serving_tps_per_mw | 329354 -> 423230 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | tokens_per_second_per_mw | 329354 -> 423230 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | commercial_workload_fit_factor | 0.5 -> 0.5 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | fleet_reference_tps_per_mw | 529367 -> 689381 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | purpose_built_tps_per_mw | 362470 -> 362470 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | reference_serving_tps_per_mw | 264684 -> 344690 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | tokens_per_second_per_mw | 264684 -> 344690 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | commercial_workload_fit_factor | 0.6 -> 0.6 share of public reference throughput | Scenario assumption | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | fleet_reference_tps_per_mw | 529367 -> 689381 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | purpose_built_tps_per_mw | 434964 -> 434964 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | reference_serving_tps_per_mw | 317620 -> 413629 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | tokens_per_second_per_mw | 317620 -> 413629 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | commercial_workload_fit_factor | 0.55 -> 0.55 share of public reference throughput | Scenario assumption | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | fleet_reference_tps_per_mw | 529367 -> 689381 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | purpose_built_tps_per_mw | 398717 -> 398717 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | reference_serving_tps_per_mw | 291152 -> 379160 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | tokens_per_second_per_mw | 291152 -> 379160 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| fleet_reference_tps_per_mw | h200_share*h200_reference + b200_share*b200_reference + gb200_share*gb200_reference + purpose_built_share*purpose_built_reference | Selected InferenceX proxy model: gptoss120b. Each GPU-generation reference is public benchmark input or documented B200 placeholder, not measured company production throughput. | Comparable production output-token throughput or a more closely matched benchmark. |
| commercial_workload_fit_factor | reference_serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor | Commercial workload class: Copilot / routed closed-model assistant. Closed-model, reasoning, long-context and SLO mismatch is made explicit rather than hiding it in the benchmark. | Matched commercial serving benchmark by product surface, context shape and latency SLO. |
| reference_serving_tps_per_mw | fleet_reference_tps_per_mw * commercial_workload_fit_factor | This is the coefficient used for headline token generation; it is intentionally below the raw public reference unless the commercial workload is closely matched. | Provider production output-token throughput with comparable workload/SLO. |
| purpose_built_tps_per_mw | purpose_built_tps_per_mw = purpose_built_reference_tps_per_mw * commercial_workload_fit_factor until comparable output-token benchmark is adopted | No comparable public output-token/MW row adopted; B200 public reference placeholder is used and remains editable. | Matched-workload generated-output benchmark for the provider purpose-built accelerator. |
| tokens_per_second_per_mw | fleet_reference_tps_per_mw * commercial_workload_fit_factor | GPT-OSS 120B B200 output-token benchmark proxy. Maia has no adopted comparable output-token/MW row, so no uplift is applied. Common filter: B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Copilot traffic mixes routed proprietary models and interactive SLOs; GPT-OSS is a reference ceiling, not direct telemetry. | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. |

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

