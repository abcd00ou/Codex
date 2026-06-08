# A09 utilization Provenance

Short name: 연평균 utilization 및 serving sensitivity

Role: 이론 capacity와 실제 sustained output 사이의 차이를 공부하기 위한 sensitivity layer다.

Headline use: headline 미적용

Confidence rule: headline에는 곱하지 않는다. 중복 보정 방지를 위해 reference/sensitivity only로 유지한다.

## Metrics covered

`utilization_sensitivity`

## Base scenario 2026 -> 2030 endpoint view

| Company | Year | Metric | Value | Confidence | Source IDs |
|---|---|---|---|---|---|
| Microsoft | 2026 | utilization_sensitivity | 0.421 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| Microsoft | 2026 | utilization_sensitivity | 0.54 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |
| Microsoft | 2026 | utilization_sensitivity | 0.605 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026 |
| Microsoft | 2026 | utilization_sensitivity | 0.475 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026 |
| Microsoft | 2030 | utilization_sensitivity | 0.53 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| Microsoft | 2030 | utilization_sensitivity | 0.68 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |
| Microsoft | 2030 | utilization_sensitivity | 0.762 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026 |
| Microsoft | 2030 | utilization_sensitivity | 0.598 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026 |
| Google | 2026 | utilization_sensitivity | 0.437 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| Google | 2026 | utilization_sensitivity | 0.56 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |
| Google | 2026 | utilization_sensitivity | 0.627 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026 |
| Google | 2026 | utilization_sensitivity | 0.493 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026 |
| Google | 2030 | utilization_sensitivity | 0.546 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| Google | 2030 | utilization_sensitivity | 0.7 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |
| Google | 2030 | utilization_sensitivity | 0.784 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026 |
| Google | 2030 | utilization_sensitivity | 0.616 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026 |
| Meta | 2026 | utilization_sensitivity | 0.429 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| Meta | 2026 | utilization_sensitivity | 0.55 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |
| Meta | 2026 | utilization_sensitivity | 0.616 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026 |
| Meta | 2026 | utilization_sensitivity | 0.484 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026 |
| Meta | 2030 | utilization_sensitivity | 0.546 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| Meta | 2030 | utilization_sensitivity | 0.7 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |
| Meta | 2030 | utilization_sensitivity | 0.784 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026 |
| Meta | 2030 | utilization_sensitivity | 0.616 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026 |
| xAI | 2026 | utilization_sensitivity | 0.39 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| xAI | 2026 | utilization_sensitivity | 0.5 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |
| xAI | 2026 | utilization_sensitivity | 0.56 | Reference-only | SRC_IBM_PD_DISAGG_2026; SRC_ARXIV_SPEC_DECODING_LATENCY_2026 |
| xAI | 2026 | utilization_sensitivity | 0.44 | Reference-only | SRC_JOULE_INFERENCE_ENERGY_2026; SRC_ARXIV_PREFILL_AS_SERVICE_2026 |
| xAI | 2030 | utilization_sensitivity | 0.523 | Reference-only | SRC_ARXIV_SLO_PD_2026; SRC_IBM_PD_DISAGG_2026 |
| xAI | 2030 | utilization_sensitivity | 0.67 | Reference-only | SRC_ARXIV_INFERENCE_ENERGY; SRC_SEMIANALYSIS_INFERENCEX |

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
| SRC_IBM_PD_DISAGG_2026 | Revisiting Disaggregated Large Language Model Serving for Performance and Energy Implications | IBM Research / EuroSys | 2026 | Tier 2 | 0.72 | https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications |
| SRC_JOULE_INFERENCE_ENERGY_2026 | Energy use of AI inference, efficiency pathways, and test-time scaling | Joule / Cell Press | 2026 | Tier 2 | 0.7 | https://www.sciencedirect.com/science/article/pii/S2542435126001145 |
| SRC_SEMIANALYSIS_INFERENCEX | InferenceX / InferenceMAX benchmark methodology | SemiAnalysis | 2025-2026 | Tier 2 | 0.7 | https://inferencex.semianalysis.com/about |

## Linked assumption IDs

`A09_utilization`

