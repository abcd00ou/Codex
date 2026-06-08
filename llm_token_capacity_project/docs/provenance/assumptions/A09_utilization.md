# A09 utilization Provenance

Short name: 연평균 utilization 및 serving sensitivity

Role: 이론 capacity와 실제 sustained output 사이의 차이를 공부하기 위한 sensitivity layer다.

Headline use: headline 미적용

Confidence rule: headline에는 곱하지 않는다. 중복 보정 방지를 위해 reference/sensitivity only로 유지한다.

## Metrics covered

`utilization_sensitivity`

## 숫자 결정 로직

- utilization은 headline 산식에 곱하지 않는다. 이미 A08의 commercial workload fit factor가 sustained serving 성능을 낮추기 때문이다.
- 이 assumption은 공부와 sensitivity 분석을 위한 reference layer이며, 같은 보정을 두 번 적용하는 double counting을 막기 위해 headline_utilization_applied를 False로 둔다.
- utilization_sensitivity는 특정 운영 profile에서 TPS/MW가 얼마나 달라지는지 보는 보조 테이블이다.
- 실제 SLO별 cluster utilization, queueing, admission control, idle reserve telemetry가 나오면 sensitivity profile을 교체한다.

### 링크를 숫자로 읽는 방식

아래 표는 링크 자체를 그대로 숫자로 옮긴 것이 아니라, 각 출처가 어떤 판단에 쓰였는지를 기록한다. URL이 capacity 방향성만 확인해주는 경우와 실제 수치 anchor를 제공하는 경우를 구분해서 읽어야 한다.

| ID | URL/report | 숫자 결정에 쓰인 방식 | Confidence |
|---|---|---|---|
| SRC_ARXIV_INFERENCE_ENERGY | https://arxiv.org/search/?query=large+language+model+inference+energy+joules+per+token&searchtype=all | Joules/token sanity check, prefill/decode split, batching, quantization sensitivity | 0.65 |
| SRC_ARXIV_PREFILL_AS_SERVICE_2026 | https://arxiv.org/abs/2604.15039 | Agentic/long-context placement and network sensitivity for utilization | 0.6 |
| SRC_ARXIV_SLO_PD_2026 | https://arxiv.org/abs/2603.04716 | Utilization caveat for TTFT/TPOT SLO constrained serving | 0.62 |
| SRC_ARXIV_SPEC_DECODING_LATENCY_2026 | https://arxiv.org/abs/2605.15051 | Speculative decoding latency and throughput trade-off mechanism | 0.6 |
| SRC_EPOCH_INFERENCE_PRICE | https://epoch.ai/data-insights/llm-inference-price-trends | Inference cost trend proxy and commercial efficiency context | 0.66 |
| SRC_IBM_PD_DISAGG_2026 | https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications | Prefill/decode disaggregation performance and energy trade-off mechanism | 0.72 |
| SRC_JOULE_INFERENCE_ENERGY_2026 | https://www.sciencedirect.com/science/article/pii/S2542435126001145 | Energy/query and joules/token sanity layer for inference forecasts | 0.7 |
| SRC_MLPERF_INFERENCE | https://mlcommons.org/benchmarks/inference-datacenter/ | Official inference submission anchor for hardware/software comparisons | 0.74 |
| SRC_MLPERF_INFERENCE_DOCS | https://docs.mlcommons.org/inference/ | Benchmark rules, scenarios, loadgen and divisions | 0.72 |
| SRC_ORCA_SERVING | https://www.usenix.org/conference/osdi22/presentation/yu | Iteration-level scheduling and batching foundation | 0.66 |
| SRC_SARATHI_SERVE | https://arxiv.org/abs/2403.02310 | Chunked prefill and decode scheduling mechanism | 0.64 |
| SRC_SEMIANALYSIS_INFERENCEX | https://inferencex.semianalysis.com/about | Benchmark layer for tokens/sec/MW sensitivity, not company capacity | 0.7 |
| SRC_SGLANG_DOCS | https://docs.sglang.ai/ | Serving runtime, structured generation and batching behavior | 0.64 |
| SRC_VLLM_DOCS | https://docs.vllm.ai/ | Production serving mechanism, scheduler and KV cache behavior | 0.66 |

### 행 단위 결정 샘플

대표 metric 행을 기준으로, 실제 trace에서 가져온 `why_this_number`, 산식, 교체 경로를 함께 붙였다. 이 표의 값은 모델 입력값이며, 공시 숫자와 scenario 숫자가 섞여 있을 수 있다.

| Company | Metric | Value | 왜 이 숫자인가 | Formula/rule | 교체 경로 | Source IDs |
|---|---|---|---|---|---|---|
| Microsoft | utilization_sensitivity | 0.421 | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Microsoft | utilization_sensitivity | 0.54 | 메인 forecast 기준 | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Microsoft | utilization_sensitivity | 0.605 | batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Microsoft | utilization_sensitivity | 0.475 | 긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| Google | utilization_sensitivity | 0.437 | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Google | utilization_sensitivity | 0.56 | 메인 forecast 기준 | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Google | utilization_sensitivity | 0.627 | batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Google | utilization_sensitivity | 0.493 | 긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| Meta | utilization_sensitivity | 0.429 | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Meta | utilization_sensitivity | 0.55 | 메인 forecast 기준 | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Meta | utilization_sensitivity | 0.616 | batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Meta | utilization_sensitivity | 0.484 | 긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| xAI | utilization_sensitivity | 0.39 | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| xAI | utilization_sensitivity | 0.5 | 메인 forecast 기준 | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | Provider utilization telemetry and SLO-level serving traces. | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |

## Base scenario 2026 -> 2030 endpoint view

| Company | Year | Metric | Value | Confidence | Source IDs |
|---|---|---|---|---|---|
| Microsoft | 2026 | utilization_sensitivity | 0.421 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Microsoft | 2026 | utilization_sensitivity | 0.54 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Microsoft | 2026 | utilization_sensitivity | 0.605 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Microsoft | 2026 | utilization_sensitivity | 0.475 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| Microsoft | 2030 | utilization_sensitivity | 0.53 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Microsoft | 2030 | utilization_sensitivity | 0.68 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Microsoft | 2030 | utilization_sensitivity | 0.762 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Microsoft | 2030 | utilization_sensitivity | 0.598 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| Google | 2026 | utilization_sensitivity | 0.437 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Google | 2026 | utilization_sensitivity | 0.56 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Google | 2026 | utilization_sensitivity | 0.627 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Google | 2026 | utilization_sensitivity | 0.493 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| Google | 2030 | utilization_sensitivity | 0.546 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Google | 2030 | utilization_sensitivity | 0.7 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Google | 2030 | utilization_sensitivity | 0.784 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Google | 2030 | utilization_sensitivity | 0.616 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| Meta | 2026 | utilization_sensitivity | 0.429 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Meta | 2026 | utilization_sensitivity | 0.55 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Meta | 2026 | utilization_sensitivity | 0.616 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Meta | 2026 | utilization_sensitivity | 0.484 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| Meta | 2030 | utilization_sensitivity | 0.546 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| Meta | 2030 | utilization_sensitivity | 0.7 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| Meta | 2030 | utilization_sensitivity | 0.784 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| Meta | 2030 | utilization_sensitivity | 0.616 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| xAI | 2026 | utilization_sensitivity | 0.39 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| xAI | 2026 | utilization_sensitivity | 0.5 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |
| xAI | 2026 | utilization_sensitivity | 0.56 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026; SRC_VLLM_DOCS; SRC_SGLANG_DOCS; SRC_SARATHI_SERVE; SRC_ORCA_SERVING |
| xAI | 2026 | utilization_sensitivity | 0.44 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026; SRC_EPOCH_INFERENCE_PRICE |
| xAI | 2030 | utilization_sensitivity | 0.523 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026; SRC_MLPERF_INFERENCE_DOCS |
| xAI | 2030 | utilization_sensitivity | 0.67 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX; SRC_MLPERF_INFERENCE |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| utilization_sensitivity | adjusted_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving | Provider utilization telemetry and SLO-level serving traces. |

## Source catalog for this assumption

| ID | Title/description | Publisher/category | Date | Tier | Confidence | URL/report |
|---|---|---|---|---|---|---|
| SRC_ARXIV_INFERENCE_ENERGY | LLM inference energy and serving efficiency literature set | arXiv | 2024-2026 | Tier 2 | 0.65 | https://arxiv.org/search/?query=large+language+model+inference+energy+joules+per+token&searchtype=all |
| SRC_ARXIV_PREFILL_AS_SERVICE_2026 | Prefill-as-a-Service | arXiv | 2026 | Tier 2 | 0.6 | https://arxiv.org/abs/2604.15039 |
| SRC_ARXIV_SLO_PD_2026 | SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM Inference | arXiv | 2026 | Tier 2 | 0.62 | https://arxiv.org/abs/2603.04716 |
| SRC_ARXIV_SPEC_DECODING_LATENCY_2026 | An Interpretable Latency Model for Speculative Decoding in LLM Serving | arXiv | 2026 | Tier 2 | 0.6 | https://arxiv.org/abs/2605.15051 |
| SRC_EPOCH_INFERENCE_PRICE | LLM inference price trends | Epoch AI | 2026-06-09 accessed | Tier 2 | 0.66 | https://epoch.ai/data-insights/llm-inference-price-trends |
| SRC_IBM_PD_DISAGG_2026 | Revisiting Disaggregated Large Language Model Serving for Performance and Energy Implications | IBM Research / EuroSys | 2026 | Tier 2 | 0.72 | https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications |
| SRC_JOULE_INFERENCE_ENERGY_2026 | Energy use of AI inference, efficiency pathways, and test-time scaling | Joule / Cell Press | 2026 | Tier 2 | 0.7 | https://www.sciencedirect.com/science/article/pii/S2542435126001145 |
| SRC_MLPERF_INFERENCE | MLPerf Inference datacenter benchmark results | MLCommons | 2026-06-09 accessed | Tier 2 | 0.74 | https://mlcommons.org/benchmarks/inference-datacenter/ |
| SRC_MLPERF_INFERENCE_DOCS | MLPerf Inference documentation | MLCommons | 2026-06-09 accessed | Tier 2 | 0.72 | https://docs.mlcommons.org/inference/ |
| SRC_ORCA_SERVING | Orca: A Distributed Serving System for Transformer-Based Generative Models | OSDI | 2022 | Tier 2 | 0.66 | https://www.usenix.org/conference/osdi22/presentation/yu |
| SRC_SARATHI_SERVE | Sarathi-Serve | arXiv | 2024 | Tier 2 | 0.64 | https://arxiv.org/abs/2403.02310 |
| SRC_SEMIANALYSIS_INFERENCEX | InferenceX / InferenceMAX benchmark methodology | SemiAnalysis | 2025-2026 | Tier 2 | 0.7 | https://inferencex.semianalysis.com/about |
| SRC_SGLANG_DOCS | SGLang documentation | SGLang project | 2026-06-09 accessed | Tier 2 | 0.64 | https://docs.sglang.ai/ |
| SRC_VLLM_DOCS | vLLM documentation | vLLM project | 2026-06-09 accessed | Tier 2 | 0.66 | https://docs.vllm.ai/ |

## Linked assumption IDs

`A09_utilization`

