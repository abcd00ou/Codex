# Agent Learning Expansion Pack

생성일: 2026-05-18
업데이트: 2026-06-09

## 목적

이 산출물은 11개 assumption agent의 학습 범위를 확장하기 위한 운영 자료입니다. 최신 IEA 2026, inference energy, prefill-decode disaggregation, rack-scale power/cooling, benchmark/proxy 자료를 agent별 curriculum으로 매핑합니다.

## 운영 원칙

- 새 source는 바로 숫자 모델에 들어가지 않습니다.
- 먼저 agent evidence로 승격하고, Fact/Derived Estimate/Proxy/Scenario를 분류합니다.
- InferenceX, AI 2027, Deloitte, McKinsey 등은 유용하지만 production telemetry가 아닙니다.
- MLPerf, InferenceX, vendor benchmark는 서로 보완재입니다. MLPerf는 규칙화된 official submission anchor이고, InferenceX는 LLM serving 조건별 proxy이며, vendor stack docs는 mechanism/source-of-implementation입니다.
- Epoch AI는 training scale, power envelope, inference price trend, scaling bottleneck을 읽는 핵심 research source이지만 회사별 production allocation fact는 아닙니다.
- A08/A09는 2026년 serving 논문을 우선 학습하고, benchmark-to-production gap을 명시해야 합니다.
- A01/A02는 2026년 power/grid source를 우선 학습하고, planned와 active를 분리해야 합니다.

## Agent별 확장 커리큘럼

### A01 `contracted_power_gw`

**확장 주제:** planned/contracted/committed/operational capacity language

**핵심 규칙:** Separate macro power-demand context from company contracted capacity facts.

**읽을 source:**

- **IEA_KEY_2026:** [Key Questions on Energy and AI](https://www.iea.org/reports/key-questions-on-energy-and-ai) - IEA, 2026. 목적: energy/policy.
- **IEA_ELEC_2026:** [Electricity 2026](https://www.iea.org/reports/electricity-2026) - IEA, 2026. 목적: electricity market baseline.
- **LBNL_DC_2024:** [2024 United States Data Center Energy Usage Report](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report) - LBNL / DOE, 2024. 목적: data center energy baseline.
- **EPRI_POWERING:** [Powering Intelligence](https://www.epri.com/research/products/000000003002028905) - EPRI, 2024/2026 updated access. 목적: grid and data center energy scenarios.
- **EIA_DC_POWER:** [U.S. data center electricity demand and grid context](https://www.eia.gov/) - U.S. EIA, accessed 2026-06-09. 목적: electricity demand and regional power baseline.
- **FERC_INTERCONNECT:** [FERC generator interconnection and grid proceedings](https://www.ferc.gov/) - FERC, accessed 2026-06-09. 목적: interconnection, transmission, reliability context.
- **OPENAI_STARGATE:** [Five new Stargate sites](https://openai.com/index/five-new-stargate-sites/) - OpenAI, 2025. 목적: planned capacity and attribution.
- **DELOITTE_AI_DC:** [AI infrastructure gaps](https://www.deloitte.com/us/en/insights/industry/power-and-utilities/data-center-infrastructure-artificial-intelligence.html) - Deloitte Insights, 2025. 목적: market context for infra constraints.
- **EPOCH_SCALING_2030:** [Can AI scaling continue through 2030?](https://epoch.ai/publications/can-ai-scaling-continue-through-2030) - Epoch AI, 2024/2026 accessed. 목적: scaling bottlenecks, power/data/capex.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A02 `active_power_gw`

**확장 주제:** energization, cluster-online evidence, deployment ratio

**핵심 규칙:** Build an operational-deployment scorecard before changing active GW.

**읽을 source:**

- **LBNL_DC_2024:** [2024 United States Data Center Energy Usage Report](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report) - LBNL / DOE, 2024. 목적: data center energy baseline.
- **EPRI_POWERING:** [Powering Intelligence](https://www.epri.com/research/products/000000003002028905) - EPRI, 2024/2026 updated access. 목적: grid and data center energy scenarios.
- **NVIDIA_DGX_GB:** [NVIDIA DGX GB Rack Scale Systems User Guide](https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html) - NVIDIA, accessed 2026-05-18. 목적: rack power/cooling architecture.
- **NVIDIA_B200_DATASHEET:** [NVIDIA Blackwell architecture and B200/GB200 data center docs](https://www.nvidia.com/en-us/data-center/) - NVIDIA, accessed 2026-06-09. 목적: accelerator/rack power and platform specs.
- **AWS_RAINIER:** [AWS Project Rainier](https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster) - Amazon, 2025. 목적: Anthropic/AWS Trainium cluster.
- **GOOGLE_TPU_DOCS:** [Cloud TPU documentation](https://cloud.google.com/tpu/docs) - Google Cloud, accessed 2026-06-09. 목적: TPU generation and serving/training platform docs.
- **MS_MAIA:** [Azure Maia AI Accelerator](https://azure.microsoft.com/en-us/blog/introducing-azure-maia-100/) - Microsoft Azure, 2023/2026 accessed. 목적: first-party accelerator deployment direction.
- **EPOCH_POWER:** [How much power will frontier AI training demand in 2030?](https://epoch.ai/blog/power-demands-of-frontier-ai-training) - Epoch AI, 2025. 목적: training peak power envelope.
- **MCK_POWER_COOL:** [Beyond compute: infrastructure that powers and cools AI data centers](https://www.mckinsey.com/industries/industrials-and-electronics/our-insights/beyond-compute-infrastructure-that-powers-and-cools-ai-data-centers) - McKinsey, 2025. 목적: power/cooling investment context.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A03 `pue`

**확장 주제:** cooling architecture, PUE, rack density

**핵심 규칙:** Keep PUE as facility overhead, not accelerator efficiency.

**읽을 source:**

- **UPTIME_COOLING:** [Cooling Systems Survey 2024](https://intelligence.uptimeinstitute.com/sites/default/files/2024-05/Uptime%20Institute%20Cooling%20Systems%20Survey%202024_0.pdf) - Uptime Institute, 2024. 목적: liquid cooling adoption and constraints.
- **AFCOM_2026_DENSITY:** [Rack Density Surges as AI Overhauls Data Center Design](https://www.datacenterknowledge.com/data-center-construction/afcom-rack-density-and-build-outs-surge-as-ai-overhauls-data-center-design) - AFCOM / Data Center Knowledge, 2026. 목적: operator survey context for density/cooling.
- **NVIDIA_DGX_GB:** [NVIDIA DGX GB Rack Scale Systems User Guide](https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html) - NVIDIA, accessed 2026-05-18. 목적: rack power/cooling architecture.
- **NVIDIA_GB200:** [NVIDIA GB200 NVL72](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) - NVIDIA, accessed 2026-05-18. 목적: rack-scale Blackwell system.
- **EPOCH_GPU_POWER:** [GPUs account for about 40% of power usage in AI data centers](https://epoch.ai/data-insights/gpus-power-usage-in-ai-data-centers) - Epoch AI, 2025. 목적: facility/IT/GPU decomposition.
- **UPTIME_GLOBAL_DC:** [Uptime Institute Global Data Center Survey](https://uptimeinstitute.com/resources/research-and-reports) - Uptime Institute, accessed 2026-06-09. 목적: PUE, cooling, outage, density operating context.
- **ASHRAE_TC99:** [ASHRAE TC 9.9 data center thermal guidance](https://www.ashrae.org/technical-resources/bookstore/datacom-series) - ASHRAE, accessed 2026-06-09. 목적: thermal envelope and cooling design reference.
- **MCK_POWER_COOL:** [Beyond compute: infrastructure that powers and cools AI data centers](https://www.mckinsey.com/industries/industrials-and-electronics/our-insights/beyond-compute-infrastructure-that-powers-and-cools-ai-data-centers) - McKinsey, 2025. 목적: power/cooling investment context.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A04 `ai_workload_share`

**확장 주제:** AI cluster share of IT load and overhead decomposition

**핵심 규칙:** Decompose GPU/server/network/storage/control overhead before setting AI workload share.

**읽을 source:**

- **LBNL_DC_2024:** [2024 United States Data Center Energy Usage Report](https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report) - LBNL / DOE, 2024. 목적: data center energy baseline.
- **EPOCH_GPU_POWER:** [GPUs account for about 40% of power usage in AI data centers](https://epoch.ai/data-insights/gpus-power-usage-in-ai-data-centers) - Epoch AI, 2025. 목적: facility/IT/GPU decomposition.
- **NVIDIA_DGX_GB:** [NVIDIA DGX GB Rack Scale Systems User Guide](https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html) - NVIDIA, accessed 2026-05-18. 목적: rack power/cooling architecture.
- **AFCOM_2026_DENSITY:** [Rack Density Surges as AI Overhauls Data Center Design](https://www.datacenterknowledge.com/data-center-construction/afcom-rack-density-and-build-outs-surge-as-ai-overhauls-data-center-design) - AFCOM / Data Center Knowledge, 2026. 목적: operator survey context for density/cooling.
- **SEMI_100K_CLUSTER:** [SemiAnalysis 100k H100 cluster / AI infrastructure analysis](https://semianalysis.com/) - SemiAnalysis, accessed 2026-06-09. 목적: accelerator cluster, networking, non-GPU overhead context.
- **DELLORO_AI_NETWORKS:** [AI networks and data center switch market context](https://www.delloro.com/) - Dell'Oro Group, accessed 2026-06-09. 목적: network/power overhead and AI cluster infrastructure context.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A05 `inference_power_share`

**확장 주제:** commercial inference adoption and inference-oriented hardware

**핵심 규칙:** Keep AI-2027 as stress scenario and not Base inference share.

**읽을 source:**

- **GOOGLE_IRONWOOD:** [Ironwood TPU: age of inference](https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/) - Google Cloud, 2025. 목적: inference-optimized TPU direction.
- **IEA_KEY_2026:** [Key Questions on Energy and AI](https://www.iea.org/reports/key-questions-on-energy-and-ai) - IEA, 2026. 목적: energy/policy.
- **EPOCH_INFERENCE_PRICE:** [LLM inference price trends](https://epoch.ai/data-insights/llm-inference-price-trends) - Epoch AI, accessed 2026-06-09. 목적: inference cost trend proxy.
- **ARTIFICIAL_ANALYSIS:** [Artificial Analysis model and API pricing benchmarks](https://artificialanalysis.ai/) - Artificial Analysis, accessed 2026-06-09. 목적: public API price/performance and latency proxy.
- **OPENROUTER_RANKINGS:** [OpenRouter model pricing and usage market signals](https://openrouter.ai/rankings) - OpenRouter, accessed 2026-06-09. 목적: API price and demand mix proxy.
- **DELOITTE_AI_DC:** [AI infrastructure gaps](https://www.deloitte.com/us/en/insights/industry/power-and-utilities/data-center-infrastructure-artificial-intelligence.html) - Deloitte Insights, 2025. 목적: market context for infra constraints.
- **AI_2027:** [AI 2027](https://ai-2027.com/) - AI Futures Project, 2025. 목적: stress scenario for accelerated adoption.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A06 `training_power_share`

**확장 주제:** frontier training reserve and post-training/eval load

**핵심 규칙:** Separate peak frontier training envelope from annual average training share.

**읽을 source:**

- **EPOCH_POWER:** [How much power will frontier AI training demand in 2030?](https://epoch.ai/blog/power-demands-of-frontier-ai-training) - Epoch AI, 2025. 목적: training peak power envelope.
- **EPOCH_TRAIN:** [Training compute of frontier AI models grows by 4-5x per year](https://epoch.ai/blog/training-compute-of-frontier-ai-models-grows-by-4-5x-per-year) - Epoch AI, 2024. 목적: frontier training compute growth.
- **EPOCH_SCALING_2030:** [Can AI scaling continue through 2030?](https://epoch.ai/publications/can-ai-scaling-continue-through-2030) - Epoch AI, 2024/2026 accessed. 목적: scaling bottlenecks, power/data/capex.
- **EPRI_EPOCH_SCALING:** [Scaling Intelligence](https://www.epri.com/research/products/000000003002033669) - EPRI / Epoch AI, 2025. 목적: AI power capacity and frontier training scenario.
- **STANFORD_INDEX_2025:** [AI Index Report 2025](https://hai.stanford.edu/ai-index/2025-ai-index-report) - Stanford HAI, 2025. 목적: macro AI compute/cost context.
- **AI_2027:** [AI 2027](https://ai-2027.com/) - AI Futures Project, 2025. 목적: stress scenario for accelerated adoption.
- **AWS_RAINIER:** [AWS Project Rainier](https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster) - Amazon, 2025. 목적: Anthropic/AWS Trainium cluster.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A07 `active_parameters`

**확장 주제:** dense/MoE/closed-model active parameter boundaries

**핵심 규칙:** Use official active params for open MoE, bands only for closed models.

**읽을 source:**

- **DEEPSEEK_V3:** [DeepSeek-V3 Technical Report / GitHub](https://github.com/deepseek-ai/DeepSeek-V3) - DeepSeek, 2024. 목적: MoE total/active parameter anchor.
- **QWEN3:** [Qwen3 GitHub](https://github.com/QwenLM/Qwen3) - Alibaba Qwen, 2025. 목적: MoE active parameter anchor.
- **META_LLAMA:** [Llama model family and model cards](https://www.llama.com/) - Meta AI, accessed 2026-06-09. 목적: Llama open model parameter and context anchor.
- **META_LLAMA4_NVIDIA:** [Meta Llama 4 NVIDIA optimization notes](https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/) - NVIDIA Developer, 2025. 목적: Llama 4 MoE total/active parameter anchor.
- **MISTRAL_MODELS:** [Mistral AI models and documentation](https://docs.mistral.ai/) - Mistral AI, accessed 2026-06-09. 목적: dense/MoE open model family anchor.
- **DBRX_MODEL:** [DBRX model announcement and model card](https://www.databricks.com/blog/introducing-dbrx-new-state-art-open-llm) - Databricks, 2024. 목적: open MoE parameter anchor.
- **OPENAI_MODEL_DOCS:** [OpenAI model docs](https://platform.openai.com/docs/models) - OpenAI, accessed 2026-06-09. 목적: closed model context/output/pricing, not parameter fact.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A08 `tokens_per_second_per_mw`

**확장 주제:** benchmark/proxy, energy/query, hardware and serving stack

**핵심 규칙:** Promote benchmark values only as proxy unless company production telemetry exists.

**읽을 source:**

- **INFERENCEX:** [InferenceX / InferenceMAX](https://inferencex.semianalysis.com/) - SemiAnalysis, accessed 2026-05-18. 목적: benchmark/proxy for tokens/MW.
- **MLPERF_INFERENCE:** [MLPerf Inference benchmark results](https://mlcommons.org/benchmarks/inference-datacenter/) - MLCommons, accessed 2026-06-09. 목적: official inference submission anchor.
- **MLPERF_POWER:** [MLPerf Power methodology and results](https://mlcommons.org/benchmarks/power/) - MLCommons, accessed 2026-06-09. 목적: optional measured power/performance anchor.
- **MLPERF_INFERENCE_DOCS:** [MLPerf Inference documentation](https://docs.mlcommons.org/inference/) - MLCommons, accessed 2026-06-09. 목적: benchmark rules, scenarios, loadgen, divisions.
- **JOULE_INFERENCE_2026:** [Energy use of AI inference, efficiency pathways, and test-time scaling](https://www.sciencedirect.com/science/article/pii/S2542435126001145) - Joule / Cell Press, 2026. 목적: energy/query, token-length, test-time compute.
- **IBM_PD_2026:** [Revisiting Disaggregated Large Language Model Serving for Performance and Energy Implications](https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications) - IBM Research / EuroSys, 2026. 목적: prefill-decode disaggregation energy/performance.
- **VLLM_DOCS:** [vLLM documentation](https://docs.vllm.ai/) - vLLM project, accessed 2026-06-09. 목적: production serving mechanism and scheduler behavior.
- **TENSORRT_LLM:** [NVIDIA TensorRT-LLM documentation](https://nvidia.github.io/TensorRT-LLM/) - NVIDIA, accessed 2026-06-09. 목적: vendor-optimized inference stack.
- **SGLANG_DOCS:** [SGLang documentation](https://docs.sglang.ai/) - SGLang project, accessed 2026-06-09. 목적: serving runtime, structured generation and batching.
- **FLASHINFER:** [FlashInfer documentation](https://docs.flashinfer.ai/) - FlashInfer project, accessed 2026-06-09. 목적: attention/decode kernel mechanism.
- **SARATHI_SERVE:** [Sarathi-Serve](https://arxiv.org/abs/2403.02310) - arXiv, 2024. 목적: chunked prefill and decode scheduling.
- **ORCA_SERVING:** [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu) - OSDI, 2022. 목적: iteration-level scheduling foundation.
- **EPOCH_INFERENCE_PRICE:** [LLM inference price trends](https://epoch.ai/data-insights/llm-inference-price-trends) - Epoch AI, accessed 2026-06-09. 목적: inference cost trend proxy.
- **PAGED_ATTENTION:** [Efficient Memory Management for LLM Serving with PagedAttention](https://arxiv.org/abs/2309.06180) - arXiv, 2023. 목적: KV cache and serving throughput foundation.
- **SPLITWISE:** [Splitwise: Efficient generative LLM inference using phase splitting](https://arxiv.org/abs/2311.18677) - arXiv, 2023. 목적: prefill/decode phase split foundation.
- **DISTSERVE:** [DistServe: Disaggregating Prefill and Decoding](https://arxiv.org/abs/2401.09670) - arXiv, 2024. 목적: TTFT/TPOT and goodput.
- **ARXIV_HETEROGENEOUS_2602:** [Large-Scale LLM Inference with Heterogeneous Workloads](https://arxiv.org/abs/2602.02987) - arXiv, 2026. 목적: prefill-decode contention and control.
- **ARXIV_SPEC_DECODE_2605:** [An Interpretable Latency Model for Speculative Decoding in LLM Serving](https://arxiv.org/abs/2605.15051) - arXiv, 2026. 목적: speculative decoding latency model.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A09 `utilization`

**확장 주제:** average utilization, latency SLO, P/D disaggregation, batching

**핵심 규칙:** Separate provisioned inference share from realized average utilization.

**읽을 source:**

- **IBM_PD_2026:** [Revisiting Disaggregated Large Language Model Serving for Performance and Energy Implications](https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications) - IBM Research / EuroSys, 2026. 목적: prefill-decode disaggregation energy/performance.
- **MLPERF_INFERENCE_DOCS:** [MLPerf Inference documentation](https://docs.mlcommons.org/inference/) - MLCommons, accessed 2026-06-09. 목적: Server/Offline latency and loadgen scenario rules.
- **VLLM_DOCS:** [vLLM documentation](https://docs.vllm.ai/) - vLLM project, accessed 2026-06-09. 목적: scheduler, KV cache, batching, prefix caching.
- **SGLANG_DOCS:** [SGLang documentation](https://docs.sglang.ai/) - SGLang project, accessed 2026-06-09. 목적: runtime, batching and structured generation operational behavior.
- **SARATHI_SERVE:** [Sarathi-Serve](https://arxiv.org/abs/2403.02310) - arXiv, 2024. 목적: chunked prefill and utilization/latency tradeoff.
- **ORCA_SERVING:** [Orca: A Distributed Serving System for Transformer-Based Generative Models](https://www.usenix.org/conference/osdi22/presentation/yu) - OSDI, 2022. 목적: iteration-level scheduling and batching foundation.
- **ARXIV_SLO_PD_2603:** [SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM Inference](https://arxiv.org/abs/2603.04716) - arXiv, 2026. 목적: SLO-aware P/D resource allocation.
- **ARXIV_PREFILL_SERVICE_2604:** [Prefill-as-a-Service](https://arxiv.org/abs/2604.15039) - arXiv, 2026. 목적: cross-datacenter KV cache/prefill scenario.
- **ARXIV_HETEROGENEOUS_2602:** [Large-Scale LLM Inference with Heterogeneous Workloads](https://arxiv.org/abs/2602.02987) - arXiv, 2026. 목적: prefill-decode contention and control.
- **PAGED_ATTENTION:** [Efficient Memory Management for LLM Serving with PagedAttention](https://arxiv.org/abs/2309.06180) - arXiv, 2023. 목적: KV cache and serving throughput foundation.
- **DISTSERVE:** [DistServe: Disaggregating Prefill and Decoding](https://arxiv.org/abs/2401.09670) - arXiv, 2024. 목적: TTFT/TPOT and goodput.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A10 `attribution_rule`

**확장 주제:** model owner vs host provider vs product owner

**핵심 규칙:** Never double count host capacity and model-owner token generation.

**읽을 source:**

- **OPENAI_STARGATE:** [Five new Stargate sites](https://openai.com/index/five-new-stargate-sites/) - OpenAI, 2025. 목적: planned capacity and attribution.
- **AWS_RAINIER:** [AWS Project Rainier](https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster) - Amazon, 2025. 목적: Anthropic/AWS Trainium cluster.
- **ANTHROPIC_AMAZON_COMPUTE:** [Amazon and Anthropic strategic collaboration](https://www.aboutamazon.com/news/aws/amazon-anthropic-ai-investment) - Amazon, accessed 2026-06-09. 목적: host provider vs model owner compute relationship.
- **GOOGLE_CLOUD_ANTHROPIC:** [Google Cloud and Anthropic partnership](https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-anthropic-ai-partnership) - Google Cloud, accessed 2026-06-09. 목적: third-party model hosted on cloud provider.
- **AZURE_OPENAI:** [Azure OpenAI Service documentation](https://learn.microsoft.com/azure/ai-services/openai/) - Microsoft, accessed 2026-06-09. 목적: Microsoft host/product surface vs OpenAI model attribution.
- **OPENAI_API_PRICING:** [OpenAI API pricing](https://openai.com/api/pricing/) - OpenAI, accessed 2026-06-09. 목적: model-owner commercial token surface proxy.
- **ANTHROPIC_PRICING:** [Anthropic API pricing](https://www.anthropic.com/pricing) - Anthropic, accessed 2026-06-09. 목적: model-owner commercial token surface proxy.
- **AI_2027:** [AI 2027](https://ai-2027.com/) - AI Futures Project, 2025. 목적: stress scenario for accelerated adoption.
- **STANFORD_INDEX_2025:** [AI Index Report 2025](https://hai.stanford.edu/ai-index/2025-ai-index-report) - Stanford HAI, 2025. 목적: macro AI compute/cost context.

**Evidence promotion task:**

1. 위 source 중 2개를 골라 원문 claim 또는 숫자를 추출합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. 해당 agent의 `evidence.md`에 evidence row 후보를 작성합니다.
4. `state.md`에 변경 후보를 적되, orchestrator review 전 generator는 수정하지 않습니다.

### A11 `gpu_asic_mix`

**확장 주제:** GPU generation mix, purpose-built accelerator substitution, comparable benchmark replacement

**핵심 규칙:** Keep H200/B200/GB200/purpose-built shares as editable scenario inputs until provider deployment or accelerator-hour evidence exists.

**읽을 source:**

- **MLPERF_INFERENCE:** [MLPerf Inference benchmark results](https://mlcommons.org/benchmarks/inference-datacenter/) - MLCommons, accessed 2026-06-09. 목적: official inference submission anchor.
- **MLPERF_POWER:** [MLPerf Power methodology and results](https://mlcommons.org/benchmarks/power/) - MLCommons, accessed 2026-06-09. 목적: optional measured power/performance anchor.
- **NVIDIA_DGX_GB:** [NVIDIA DGX GB Rack Scale Systems User Guide](https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html) - NVIDIA, accessed 2026-05-18. 목적: rack power/cooling architecture.
- **NVIDIA_GB200:** [NVIDIA GB200 NVL72](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) - NVIDIA, accessed 2026-05-18. 목적: rack-scale Blackwell system.
- **NVIDIA_B200_DATASHEET:** [NVIDIA Blackwell architecture and B200/GB200 data center docs](https://www.nvidia.com/en-us/data-center/) - NVIDIA, accessed 2026-06-09. 목적: accelerator/rack power and platform specs.
- **GOOGLE_TPU_DOCS:** [Cloud TPU documentation](https://cloud.google.com/tpu/docs) - Google Cloud, accessed 2026-06-09. 목적: TPU generation and serving/training platform docs.
- **GOOGLE_IRONWOOD:** [Ironwood TPU: age of inference](https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/) - Google Cloud, 2025. 목적: inference-optimized TPU direction.
- **MS_MAIA:** [Azure Maia AI Accelerator](https://azure.microsoft.com/en-us/blog/introducing-azure-maia-100/) - Microsoft Azure, 2023/2026 accessed. 목적: first-party accelerator deployment direction.
- **AWS_RAINIER:** [AWS Project Rainier](https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster) - Amazon, 2025. 목적: Anthropic/AWS Trainium cluster.
- **TENSORRT_LLM:** [NVIDIA TensorRT-LLM documentation](https://nvidia.github.io/TensorRT-LLM/) - NVIDIA, accessed 2026-06-09. 목적: vendor-optimized inference stack.

**Evidence promotion task:**

1. 위 source 중 GPU 2개, purpose-built accelerator 2개를 골라 platform fact와 benchmark proxy를 분리합니다.
2. 각 claim을 Fact / Derived Estimate / Proxy / Scenario로 분류합니다.
3. `purpose-built` hardware에 TPS/MW premium을 주려면 model, precision, ISL/OSL, latency scenario가 맞는 comparable output-token benchmark를 요구합니다.
4. 해당 agent의 `evidence.md`와 `state.md`에 후보를 쓰되, orchestrator review 전 generator는 수정하지 않습니다.

## Expanded Source Library

| ID | Source | Publisher | Year | Purpose | Agents | Link |
|---|---|---|---|---|---|---|
| IEA_KEY_2026 | Key Questions on Energy and AI | IEA | 2026 | energy/policy | A01,A02,A05 | https://www.iea.org/reports/key-questions-on-energy-and-ai |
| IEA_ELEC_2026 | Electricity 2026 | IEA | 2026 | electricity market baseline | A01,A02 | https://www.iea.org/reports/electricity-2026 |
| LBNL_DC_2024 | 2024 United States Data Center Energy Usage Report | LBNL / DOE | 2024 | data center energy baseline | A01,A02,A03,A04 | https://eta-publications.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report |
| EPRI_POWERING | Powering Intelligence | EPRI | 2024/2026 updated access | grid and data center energy scenarios | A01,A02 | https://www.epri.com/research/products/000000003002028905 |
| EIA_DC_POWER | U.S. data center electricity demand and grid context | U.S. EIA | accessed 2026-06-09 | electricity demand and regional power baseline | A01,A02 | https://www.eia.gov/ |
| FERC_INTERCONNECT | FERC generator interconnection and grid proceedings | FERC | accessed 2026-06-09 | interconnection, transmission and reliability context | A01,A02 | https://www.ferc.gov/ |
| UPTIME_COOLING | Cooling Systems Survey 2024 | Uptime Institute | 2024 | liquid cooling adoption and constraints | A03,A04 | https://intelligence.uptimeinstitute.com/sites/default/files/2024-05/Uptime%20Institute%20Cooling%20Systems%20Survey%202024_0.pdf |
| UPTIME_GLOBAL_DC | Uptime Institute Global Data Center Survey | Uptime Institute | accessed 2026-06-09 | PUE, cooling, outage and density operating context | A03,A04 | https://uptimeinstitute.com/resources/research-and-reports |
| ASHRAE_TC99 | ASHRAE TC 9.9 data center thermal guidance | ASHRAE | accessed 2026-06-09 | thermal envelope and cooling design reference | A03 | https://www.ashrae.org/technical-resources/bookstore/datacom-series |
| AFCOM_2026_DENSITY | Rack Density Surges as AI Overhauls Data Center Design | AFCOM / Data Center Knowledge | 2026 | operator survey context for density/cooling | A03,A04 | https://www.datacenterknowledge.com/data-center-construction/afcom-rack-density-and-build-outs-surge-as-ai-overhauls-data-center-design |
| IBM_PD_2026 | Revisiting Disaggregated Large Language Model Serving for Performance and Energy Implications | IBM Research / EuroSys | 2026 | prefill-decode disaggregation energy/performance | A08,A09 | https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications |
| JOULE_INFERENCE_2026 | Energy use of AI inference, efficiency pathways, and test-time scaling | Joule / Cell Press | 2026 | energy/query, token-length, test-time compute | A08,A09 | https://www.sciencedirect.com/science/article/pii/S2542435126001145 |
| MLPERF_INFERENCE | MLPerf Inference benchmark results | MLCommons | accessed 2026-06-09 | official inference submission anchor | A08,A09,A11 | https://mlcommons.org/benchmarks/inference-datacenter/ |
| MLPERF_POWER | MLPerf Power methodology and results | MLCommons | accessed 2026-06-09 | optional measured power/performance anchor | A08,A09,A11 | https://mlcommons.org/benchmarks/power/ |
| MLPERF_INFERENCE_DOCS | MLPerf Inference documentation | MLCommons | accessed 2026-06-09 | benchmark rules, scenarios, loadgen, divisions | A08,A09 | https://docs.mlcommons.org/inference/ |
| VLLM_DOCS | vLLM documentation | vLLM project | accessed 2026-06-09 | production serving mechanism, scheduler and KV cache behavior | A08,A09 | https://docs.vllm.ai/ |
| TENSORRT_LLM | NVIDIA TensorRT-LLM documentation | NVIDIA | accessed 2026-06-09 | vendor-optimized inference stack | A08,A09,A11 | https://nvidia.github.io/TensorRT-LLM/ |
| SGLANG_DOCS | SGLang documentation | SGLang project | accessed 2026-06-09 | serving runtime, structured generation and batching | A08,A09 | https://docs.sglang.ai/ |
| FLASHINFER | FlashInfer documentation | FlashInfer project | accessed 2026-06-09 | attention/decode kernel mechanism | A08,A09 | https://docs.flashinfer.ai/ |
| SARATHI_SERVE | Sarathi-Serve | arXiv | 2024 | chunked prefill and decode scheduling | A08,A09 | https://arxiv.org/abs/2403.02310 |
| ORCA_SERVING | Orca: A Distributed Serving System for Transformer-Based Generative Models | OSDI | 2022 | iteration-level scheduling and batching foundation | A08,A09 | https://www.usenix.org/conference/osdi22/presentation/yu |
| ARXIV_HETEROGENEOUS_2602 | Large-Scale LLM Inference with Heterogeneous Workloads | arXiv | 2026 | prefill-decode contention and control | A08,A09 | https://arxiv.org/abs/2602.02987 |
| ARXIV_SLO_PD_2603 | SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM Inference | arXiv | 2026 | SLO-aware P/D resource allocation | A08,A09 | https://arxiv.org/abs/2603.04716 |
| ARXIV_PREFILL_SERVICE_2604 | Prefill-as-a-Service | arXiv | 2026 | cross-datacenter KV cache/prefill scenario | A08,A09,A10 | https://arxiv.org/abs/2604.15039 |
| ARXIV_SPEC_DECODE_2605 | An Interpretable Latency Model for Speculative Decoding in LLM Serving | arXiv | 2026 | speculative decoding latency model | A08,A09 | https://arxiv.org/abs/2605.15051 |
| PAGED_ATTENTION | Efficient Memory Management for LLM Serving with PagedAttention | arXiv | 2023 | KV cache and serving throughput foundation | A08,A09 | https://arxiv.org/abs/2309.06180 |
| SPLITWISE | Splitwise: Efficient generative LLM inference using phase splitting | arXiv | 2023 | prefill/decode phase split foundation | A08,A09 | https://arxiv.org/abs/2311.18677 |
| DISTSERVE | DistServe: Disaggregating Prefill and Decoding | arXiv | 2024 | TTFT/TPOT and goodput | A08,A09 | https://arxiv.org/abs/2401.09670 |
| INFERENCEX | InferenceX / InferenceMAX | SemiAnalysis | accessed 2026-05-18 | benchmark/proxy for tokens/MW | A08,A09 | https://inferencex.semianalysis.com/ |
| NVIDIA_DGX_GB | NVIDIA DGX GB Rack Scale Systems User Guide | NVIDIA | accessed 2026-05-18 | rack power/cooling architecture | A02,A03,A08 | https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html |
| NVIDIA_GB200 | NVIDIA GB200 NVL72 | NVIDIA | accessed 2026-05-18 | rack-scale Blackwell system | A02,A03,A08 | https://www.nvidia.com/en-us/data-center/gb200-nvl72/ |
| NVIDIA_B200_DATASHEET | NVIDIA Blackwell architecture and B200/GB200 data center docs | NVIDIA | accessed 2026-06-09 | accelerator/rack power and platform specs | A02,A08,A11 | https://www.nvidia.com/en-us/data-center/ |
| GOOGLE_IRONWOOD | Ironwood TPU: age of inference | Google Cloud | 2025 | inference-optimized TPU direction | A05,A08 | https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ |
| GOOGLE_TPU_DOCS | Cloud TPU documentation | Google Cloud | accessed 2026-06-09 | TPU generation and serving/training platform docs | A02,A05,A08,A11 | https://cloud.google.com/tpu/docs |
| MS_MAIA | Azure Maia AI Accelerator | Microsoft Azure | 2023/2026 accessed | first-party accelerator deployment direction | A02,A05,A10,A11 | https://azure.microsoft.com/en-us/blog/introducing-azure-maia-100/ |
| AWS_RAINIER | AWS Project Rainier | Amazon | 2025 | Anthropic/AWS Trainium cluster | A02,A06,A10 | https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster |
| OPENAI_STARGATE | Five new Stargate sites | OpenAI | 2025 | planned capacity and attribution | A01,A02,A10 | https://openai.com/index/five-new-stargate-sites/ |
| ANTHROPIC_AMAZON_COMPUTE | Amazon and Anthropic strategic collaboration | Amazon | accessed 2026-06-09 | host provider vs model owner compute relationship | A02,A10 | https://www.aboutamazon.com/news/aws/amazon-anthropic-ai-investment |
| GOOGLE_CLOUD_ANTHROPIC | Google Cloud and Anthropic partnership | Google Cloud | accessed 2026-06-09 | third-party model hosted on cloud provider | A02,A10 | https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-anthropic-ai-partnership |
| AZURE_OPENAI | Azure OpenAI Service documentation | Microsoft | accessed 2026-06-09 | Microsoft host/product surface vs OpenAI model attribution | A10 | https://learn.microsoft.com/azure/ai-services/openai/ |
| OPENAI_API_PRICING | OpenAI API pricing | OpenAI | accessed 2026-06-09 | model-owner commercial token surface proxy | A05,A10 | https://openai.com/api/pricing/ |
| ANTHROPIC_PRICING | Anthropic API pricing | Anthropic | accessed 2026-06-09 | model-owner commercial token surface proxy | A05,A10 | https://www.anthropic.com/pricing |
| DEEPSEEK_V3 | DeepSeek-V3 Technical Report / GitHub | DeepSeek | 2024 | MoE total/active parameter anchor | A07,A08 | https://github.com/deepseek-ai/DeepSeek-V3 |
| QWEN3 | Qwen3 GitHub | Alibaba Qwen | 2025 | MoE active parameter anchor | A07,A08 | https://github.com/QwenLM/Qwen3 |
| META_LLAMA | Llama model family and model cards | Meta AI | accessed 2026-06-09 | Llama open model parameter and context anchor | A07,A08,A10 | https://www.llama.com/ |
| META_LLAMA4_NVIDIA | Meta Llama 4 NVIDIA optimization notes | NVIDIA Developer | 2025 | Llama 4 MoE total/active parameter anchor | A07,A08 | https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/ |
| MISTRAL_MODELS | Mistral AI models and documentation | Mistral AI | accessed 2026-06-09 | dense/MoE open model family anchor | A07,A08 | https://docs.mistral.ai/ |
| DBRX_MODEL | DBRX model announcement and model card | Databricks | 2024 | open MoE parameter anchor | A07,A08 | https://www.databricks.com/blog/introducing-dbrx-new-state-art-open-llm |
| OPENAI_MODEL_DOCS | OpenAI model docs | OpenAI | accessed 2026-06-09 | closed model context/output/pricing, not parameter fact | A07,A10 | https://platform.openai.com/docs/models |
| STANFORD_INDEX_2025 | AI Index Report 2025 | Stanford HAI | 2025 | macro AI compute/cost context | A06,A08,A10 | https://hai.stanford.edu/ai-index/2025-ai-index-report |
| EPRI_EPOCH_SCALING | Scaling Intelligence | EPRI / Epoch AI | 2025 | AI power capacity and frontier training scenario | A02,A06 | https://www.epri.com/research/products/000000003002033669 |
| EPOCH_TRAIN | Training compute of frontier AI models grows by 4-5x per year | Epoch AI | 2024 | frontier training compute growth | A06 | https://epoch.ai/blog/training-compute-of-frontier-ai-models-grows-by-4-5x-per-year |
| EPOCH_POWER | How much power will frontier AI training demand in 2030? | Epoch AI | 2025 | training peak power envelope | A02,A06 | https://epoch.ai/blog/power-demands-of-frontier-ai-training |
| EPOCH_SCALING_2030 | Can AI scaling continue through 2030? | Epoch AI | 2024/2026 accessed | scaling bottlenecks, power/data/capex | A01,A02,A06 | https://epoch.ai/publications/can-ai-scaling-continue-through-2030 |
| EPOCH_INFERENCE_PRICE | LLM inference price trends | Epoch AI | accessed 2026-06-09 | inference cost trend proxy, not production efficiency fact | A05,A08 | https://epoch.ai/data-insights/llm-inference-price-trends |
| EPOCH_GPU_POWER | GPUs account for about 40% of power usage in AI data centers | Epoch AI | 2025 | facility/IT/GPU decomposition | A03,A04 | https://epoch.ai/data-insights/gpus-power-usage-in-ai-data-centers |
| ARTIFICIAL_ANALYSIS | Artificial Analysis model and API pricing benchmarks | Artificial Analysis | accessed 2026-06-09 | public API price/performance and latency proxy | A05,A08,A10 | https://artificialanalysis.ai/ |
| OPENROUTER_RANKINGS | OpenRouter model pricing and usage market signals | OpenRouter | accessed 2026-06-09 | API price and demand mix proxy | A05,A10 | https://openrouter.ai/rankings |
| SEMI_100K_CLUSTER | SemiAnalysis 100k H100 cluster / AI infrastructure analysis | SemiAnalysis | accessed 2026-06-09 | accelerator cluster, networking and non-GPU overhead context | A04,A08 | https://semianalysis.com/ |
| DELLORO_AI_NETWORKS | AI networks and data center switch market context | Dell'Oro Group | accessed 2026-06-09 | network/power overhead and AI cluster infrastructure context | A04 | https://www.delloro.com/ |
| DELOITTE_AI_DC | AI infrastructure gaps | Deloitte Insights | 2025 | market context for infra constraints | A01,A02,A05 | https://www.deloitte.com/us/en/insights/industry/power-and-utilities/data-center-infrastructure-artificial-intelligence.html |
| MCK_POWER_COOL | Beyond compute: infrastructure that powers and cools AI data centers | McKinsey | 2025 | power/cooling investment context | A02,A03 | https://www.mckinsey.com/industries/industrials-and-electronics/our-insights/beyond-compute-infrastructure-that-powers-and-cools-ai-data-centers |
| AI_2027 | AI 2027 | AI Futures Project | 2025 | stress scenario for accelerated adoption | A05,A06,A08,A09,A10 | https://ai-2027.com/ |

## 30-Day Agent Learning Sprint

### Week 1: Power and Deployment

- A01, A02, A03, A04가 IEA/LBNL/EPRI/EIA/FERC/Uptime/ASHRAE/NVIDIA DGX GB/Epoch GPU power 자료를 읽습니다.
- 산출물: planned vs active capacity scorecard, PUE/context note, AI workload share decomposition.

### Week 2: Inference Serving Deep Dive

- A08, A09, A11이 MLPerf Inference/Power, InferenceX, vLLM, TensorRT-LLM, SGLang, FlashInfer, PagedAttention, Splitwise, DistServe, Sarathi, Orca, IBM PD 2026, Joule inference energy를 읽습니다.
- 산출물: official-submission vs LLM-serving-proxy bridge, tokens/MW proxy ladder, utilization caveat sheet, benchmark-to-production gap map, comparable accelerator replacement checklist.

### Week 3: Model Architecture and Training Reserve

- A06, A07가 Epoch AI, EPRI/Epoch, Stanford, DeepSeek, Qwen, Llama, Mistral, DBRX, OpenAI model docs를 읽습니다.
- 산출물: training reserve interpretation, open-model active parameter table, closed-model parameter caveat map.

### Week 4: Scenario and Attribution

- A05, A10, orchestrator가 AI 2027, OpenAI Stargate/API pricing, AWS Rainier, Anthropic/Amazon, Google Cloud/Anthropic, Azure OpenAI, Artificial Analysis, OpenRouter, market context를 읽습니다.
- 산출물: AI-2027 stress scenario memo, host/model-owner attribution map, API price/demand proxy caveat sheet.

## Orchestrator Review Output Template

```text
cycle:
date:
agents_reviewed:
sources_promoted:
fields_changed:
confidence_upgrades:
confidence_downgrades:
base_case_changes:
stress_scenario_changes:
unresolved_flags:
next_cycle:
```
