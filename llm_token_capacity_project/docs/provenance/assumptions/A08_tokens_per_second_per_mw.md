# A08 tokens_per_second_per_mw Provenance

Short name: InferenceX 기반 generated output TPS/MW

Role: 1MW inference load가 초당 몇 generated output token을 만들 수 있는지 결정한다.

Headline use: 직접 사용

Confidence rule: InferenceX/MLPerf/vendor serving stack은 proxy/benchmark이며 production telemetry가 아니므로 workload fit factor와 source caveat를 같이 붙인다.

## Metrics covered

`commercial_workload_fit_factor`, `fleet_reference_tps_per_mw`, `purpose_built_tps_per_mw`, `reference_serving_tps_per_mw`, `tokens_per_second_per_mw`

## 숫자 결정 로직

- TPS/MW는 InferenceX, MLPerf, vendor serving stack을 그대로 생산 telemetry로 간주하지 않고, H200/B200/GB200 reference 성능을 상용 workload에 맞게 낮춘 proxy로 사용한다.
- fleet_reference_tps_per_mw는 GPU generation mix에서 나온 raw benchmark 기준이고, commercial_workload_fit_factor는 closed model, 긴 context, SLO, batching 제약, prefill/decode 불균형을 반영하는 보정 계수다.
- tokens_per_second_per_mw는 reference_serving_tps_per_mw와 purpose_built_tps_per_mw를 fleet mix로 결합한 최종 입력값이다.
- LLMServingSim 2.0 방식의 trace-driven prefill/decode simulation, KV cache pressure, interconnect contention, scheduling 정책 또는 MLPerf/serving-stack matched benchmark가 확보되면 fit factor를 더 구조적인 계수로 쪼갤 수 있다.

### 링크를 숫자로 읽는 방식

아래 표는 링크 자체를 그대로 숫자로 옮긴 것이 아니라, 각 출처가 어떤 판단에 쓰였는지를 기록한다. URL이 capacity 방향성만 확인해주는 경우와 실제 수치 anchor를 제공하는 경우를 구분해서 읽어야 한다.

| ID | URL/report | 숫자 결정에 쓰인 방식 | Confidence |
|---|---|---|---|
| ASSUMP_NUMERIC_ACCELERATOR_MIX |  | GPU/ASIC mix는 운영 fleet share 공개가 없는 경우 fact가 아니라 serving-platform anchor를 바탕으로 둔 숫자 시나리오다. 공식적으로 custom accelerator deployment가 확인된 Microsoft, Google, Meta, Anthropic만 purpose-built accelerator share 상승을 Base에 반영하고, 나머지는 GPU-reference Base로 둔다. | 0.42 |
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
| SRC_SEMIANALYSIS_INFERENCEX | https://inferencex.semianalysis.com/about | Benchmark layer for tokens/sec/MW sensitivity, not company capacity | 0.7 |
| SRC_TENCENT_AI_INFRA_MOE | https://www.tencent.com/en-us/articles/2201930.html | Confirms Tencent AI Infra and Hunyuan Turbo MoE service with stated inference-cost reduction | 0.84 |
| SRC_TENCENT_HUNYUAN | https://www.tencent.com/en-us/articles/2201460.html | Tencent Hunyuan parameter and pretraining token anchor | 0.82 |
| SRC_TENCENT_HY3 | https://www.tencent.com/en-us/articles/2202320.html | Tencent Hunyuan commercial surface and model-family anchor | 0.78 |
| SRC_XAI_MODELS | https://docs.x.ai/docs/models | Grok commercial model surface and closed-model disclosure boundary | 0.78 |
| SRC_XAI_NVIDIA_COLOSSUS | https://blogs.nvidia.com/blog/xai-colossus/ | xAI GPU cluster scale anchor for active power and serving/training capacity scenarios | 0.82 |

### 행 단위 결정 샘플

대표 metric 행을 기준으로, 실제 trace에서 가져온 `why_this_number`, 산식, 교체 경로를 함께 붙였다. 이 표의 값은 모델 입력값이며, 공시 숫자와 scenario 숫자가 섞여 있을 수 있다.

| Company | Metric | Value | 왜 이 숫자인가 | Formula/rule | 교체 경로 | Source IDs |
|---|---|---|---|---|---|---|
| Microsoft | tokens_per_second_per_mw | 328955 | GPT-OSS 120B B200 output-token benchmark proxy. Maia has no adopted comparable output-token/MW row, so no uplift is applied. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Copilot traffic mixes routed proprietary models and interactive SLOs; GPT-OSS... | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | tokens_per_second_per_mw | 410715 | GPT-OSS 120B B200 output-token benchmark proxy. TPU/Ironwood presence is shown, but no unmatched efficiency premium is applied. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Gemini serving is closed and TPU-heavy with product and multimodal routing... | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | tokens_per_second_per_mw | 181602 | Llama 70B B200 output-token benchmark proxy. MTIA presence is shown, but no unmatched efficiency premium is applied. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Llama benchmark family is comparatively close to Meta AI serving, while fleet routing... | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | tokens_per_second_per_mw | 290835 | GPT-OSS 120B B200 output-token benchmark proxy pending a comparable Grok serving benchmark. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Grok is closed and reasoning/product workload mix is not matched to the GPT-OSS benchmark row. | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | tokens_per_second_per_mw | 264396 | GPT-OSS 120B B200 output-token benchmark proxy; not direct ChatGPT/API telemetry. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: ChatGPT/API demand includes reasoning and latency-sensitive surfaces; GPT-OSS throughput is not GPT production telemetry. | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | tokens_per_second_per_mw | 327574 | GPT-OSS 120B B200 output-token benchmark proxy. Trainium presence is shown, but no unmatched efficiency premium is applied. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Claude usage is materially coding/agent/long-context oriented and no comparabl... | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | tokens_per_second_per_mw | 54172 | DeepSeek-R1 B200 output-token benchmark proxy; official MoE structure informs mapping but does not add a second multiplier. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: DeepSeek benchmark family is matched, but commercial R1 reasoning traffic can... | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | tokens_per_second_per_mw | 116746 | Qwen3.5 B200 output-token benchmark proxy; MoE is represented by selected benchmark, with no additional uplift. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Qwen benchmark family is relatively direct; remaining adjustment represents commercial con... | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | tokens_per_second_per_mw | 317275 | GPT-OSS 120B B200 output-token benchmark proxy pending a comparable Hunyuan output-token benchmark. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Hunyuan is not represented by a matched public TPS/MW row; GPT-OSS is used only as a reference ceiling. | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |

## Base scenario 2026 -> 2030 endpoint view

| Company | Metric | 2026 -> 2030 | Derivation | Confidence | Source IDs |
|---|---|---|---|---|---|
| Alibaba | commercial_workload_fit_factor | 0.9 -> 0.9 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | fleet_reference_tps_per_mw | 129718 -> 169501 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | purpose_built_tps_per_mw | 160508 -> 160508 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | reference_serving_tps_per_mw | 116746 -> 152551 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Alibaba | tokens_per_second_per_mw | 116746 -> 152551 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_QWEN3_GITHUB; SRC_ALIBABA_QWEN_GPU_DEPLOY; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | commercial_workload_fit_factor | 0.5 -> 0.5 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | fleet_reference_tps_per_mw | 655148 -> 718149 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | purpose_built_tps_per_mw | 361729 -> 361729 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | reference_serving_tps_per_mw | 327574 -> 359074 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Anthropic | tokens_per_second_per_mw | 327574 -> 359074 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_ANTHROPIC_CLAUDE_DOCS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | commercial_workload_fit_factor | 0.85 -> 0.85 share of public reference throughput | Scenario assumption | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | fleet_reference_tps_per_mw | 63732 -> 64832 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | purpose_built_tps_per_mw | 55315 -> 55315 generated output tokens/sec/MW | Conservative no-uplift proxy | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | reference_serving_tps_per_mw | 54172 -> 55107 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Parameter High / Capacity Low-Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| DeepSeek | tokens_per_second_per_mw | 54172 -> 55107 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Parameter High / Capacity Low-Medium | SRC_DEEPSEEK_V3; SRC_DEEPSEEK_R1; SRC_DEEPSEEK_H800_INFERENCE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | commercial_workload_fit_factor | 0.6 -> 0.6 share of public reference throughput | Scenario assumption | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | fleet_reference_tps_per_mw | 684525 -> 719919 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | purpose_built_tps_per_mw | 434075 -> 434075 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | reference_serving_tps_per_mw | 410715 -> 431951 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium-High | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Google | tokens_per_second_per_mw | 410715 -> 431951 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium-High | SRC_GOOGLE_GEMINI_TOKENS; SRC_GOOGLE_IRONWOOD; SRC_GOOGLE_TPU_V6E; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | commercial_workload_fit_factor | 0.9 -> 0.9 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | fleet_reference_tps_per_mw | 201780 -> 200960 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | purpose_built_tps_per_mw | 180771 -> 180771 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | reference_serving_tps_per_mw | 181602 -> 180864 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Meta | tokens_per_second_per_mw | 181602 -> 180864 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_META_LLAMA; SRC_META_LLAMA4_NVIDIA; SRC_META_MTIA_GENAI_2026; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | commercial_workload_fit_factor | 0.6 -> 0.6 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | fleet_reference_tps_per_mw | 548258 -> 703991 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | purpose_built_tps_per_mw | 434075 -> 434075 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | reference_serving_tps_per_mw | 328955 -> 422395 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Microsoft | tokens_per_second_per_mw | 328955 -> 422395 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_MS_PHI; SRC_OPENAI_GPT41_DOCS; SRC_MS_PHI4_TECHREPORT; SRC_MS_MAIA200; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | commercial_workload_fit_factor | 0.5 -> 0.5 share of public reference throughput | Scenario assumption | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | fleet_reference_tps_per_mw | 528791 -> 688064 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | purpose_built_tps_per_mw | 361729 -> 361729 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | reference_serving_tps_per_mw | 264396 -> 344032 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| OpenAI | tokens_per_second_per_mw | 264396 -> 344032 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium | SRC_OPENAI_GPT41_DOCS; SRC_OPENAI_STARGATE_ORACLE; SRC_OPENAI_STARGATE_PROGRESS; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | commercial_workload_fit_factor | 0.6 -> 0.6 share of public reference throughput | Scenario assumption | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | fleet_reference_tps_per_mw | 528791 -> 688064 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | purpose_built_tps_per_mw | 434075 -> 434075 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | reference_serving_tps_per_mw | 317275 -> 412838 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| Tencent | tokens_per_second_per_mw | 317275 -> 412838 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium-Low | SRC_TENCENT_HUNYUAN; SRC_TENCENT_HY3; SRC_TENCENT_AI_INFRA_MOE; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | commercial_workload_fit_factor | 0.55 -> 0.55 share of public reference throughput | Scenario assumption | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | fleet_reference_tps_per_mw | 528791 -> 688064 generated output tokens/sec/MW | Fleet-weighted public benchmark reference | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | purpose_built_tps_per_mw | 397902 -> 397902 generated output tokens/sec/MW | Conservative no-uplift proxy | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | reference_serving_tps_per_mw | 290835 -> 378435 generated output tokens/sec/MW | Workload-adjusted benchmark proxy | Medium-Low | SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |
| xAI | tokens_per_second_per_mw | 290835 -> 378435 generated output tokens/sec/MW | Derived estimate + benchmark calibration | Medium-Low | SRC_XAI_MODELS; SRC_XAI_NVIDIA_COLOSSUS; SRC_SEMIANALYSIS_INFERENCEX; ASSUMP_NUMERIC_ACCELERATOR_MIX |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| fleet_reference_tps_per_mw | h200_share*h200_reference + b200_share*b200_reference + gb200_share*gb200_reference + purpose_built_share*purpose_built_reference | Selected InferenceX proxy model: gptoss120b. Each GPU-generation reference is public benchmark input or documented B200 placeholder, not measured company production throughput. | Comparable production output-token throughput or a more closely matched benchmark. |
| commercial_workload_fit_factor | reference_serving_tps_per_mw = weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | Commercial workload class: Copilot / routed closed-model assistant. Closed-model, reasoning, long-context and SLO mismatch is made explicit rather than hiding it in the benchmark. | Matched commercial serving benchmark by product surface, context shape and latency SLO. |
| reference_serving_tps_per_mw | weighted_reference_tps_per_mw * commercial_workload_fit_factor | This is the coefficient used for headline token generation after short chat, long chat and agentic workload references are weighted. | Provider production output-token throughput with comparable workload/SLO. |
| purpose_built_tps_per_mw | purpose_built_tps_per_mw = purpose_built_reference_tps_per_mw * commercial_workload_fit_factor until comparable output-token benchmark is adopted | No comparable public output-token/MW row adopted; B200 public reference placeholder is used and remains editable. | Matched-workload generated-output benchmark for the provider purpose-built accelerator. |
| tokens_per_second_per_mw | weighted(short_chat,long_chat,agentic TPS/MW) * commercial_workload_fit_factor | GPT-OSS 120B B200 output-token benchmark proxy. Maia has no adopted comparable output-token/MW row, so no uplift is applied. Common filter: model-level main_framework/main_precision only, B200, single_turn, ISL=1024, OSL=1024, output_tok_s_mw p50. Commercial workload fit factor: Copilot traffic mixes routed proprietary models and interactive SLOs; GPT-OSS is a reference ceiling, not direct telemetry. | Comparable production output-token throughput with model, hardware, precision, ISL/OSL and SLO matched. |

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
