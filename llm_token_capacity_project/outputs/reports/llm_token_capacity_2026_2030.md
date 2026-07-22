# Compute Capacity To Generated Output Token Supply

- 생성일: 2026-07-23
- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션
- 출력 정의: generated output tokens/day

## Core Formula

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
gpu_workload_avg_tps_per_mw = short_share*gpu_short_tps_mw + long_share*gpu_long_tps_mw + agentic_share*gpu_agentic_tps_mw
fleet_reference_tps_per_mw = h200_share*h200_workload_avg + b200_share*b200_workload_avg + gb200_share*gb200_workload_avg + purpose_built_share*purpose_workload_avg
serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor
generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400
```

- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.
- GPU 세대 mix는 `H200`, `B200`, `GB200`, `purpose-built`의 inference-load share이며 Excel에서 별도 입력합니다.
- InferenceX GPU별 값은 public reference이며, 상용 서비스 TPS/MW는 short conversation, long conversation, agentic workload mix와 workload fit factor를 반영합니다.
- Purpose-built accelerator의 comparable benchmark가 없으면 B200 placeholder를 사용하며 이후 입력으로 교체합니다.

## GPU Generation Mix, Workload Mix And Commercial Fit

| Provider | Proxy | 2030 H/B/GB/PB | Short/Long/Agentic | Weighted ref TPS/MW | Fit | Serving TPS/MW |
|---|---|---:|---:|---:|---:|---:|
| Microsoft | gptoss120b | 6%/19%/30%/45% | 45%/30%/25% | 1,119,744 | 60% | 671,846 |
| Google | frontier_composite | 1%/4%/6%/90% | 40%/40%/20% | 68,985 | 60% | 41,391 |
| Meta | llama70b | 6%/19%/30%/45% | 70%/20%/10% | 424,065 | 90% | 381,658 |
| xAI | gptoss120b | 10%/35%/55%/0% | 45%/35%/20% | 1,141,925 | 55% | 628,059 |
| OpenAI | frontier_composite | 10%/35%/55%/0% | 45%/25%/30% | 64,334 | 50% | 32,167 |
| Anthropic | frontier_composite | 2%/5%/8%/85% | 30%/30%/40% | 53,784 | 50% | 26,892 |
| DeepSeek | dsr1 | 10%/35%/55%/0% | 35%/40%/25% | 75,815 | 85% | 64,443 |
| Alibaba | qwen3.5 | 10%/35%/55%/0% | 45%/35%/20% | 322,084 | 90% | 289,876 |
| Tencent | gptoss120b | 10%/35%/55%/0% | 65%/25%/10% | 1,339,259 | 60% | 803,555 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| Microsoft | 6.200 | 3.333 | 671,846 | 0.193 |
| Meta | 5.800 | 3.280 | 381,658 | 0.108 |
| Tencent | 2.400 | 1.311 | 803,555 | 0.091 |
| xAI | 2.500 | 1.219 | 628,059 | 0.066 |
| Alibaba | 3.200 | 1.748 | 289,876 | 0.044 |
| OpenAI | 8.500 | 4.862 | 32,167 | 0.014 |
| Google | 6.800 | 3.651 | 41,391 | 0.013 |
| Anthropic | 5.500 | 2.966 | 26,892 | 0.007 |
| DeepSeek | 1.200 | 0.651 | 64,443 | 0.004 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.043 | 0.086 | 0.139 | 0.200 | 0.271 |
| Base | 0.077 | 0.160 | 0.264 | 0.391 | 0.540 |
| Bull | 0.111 | 0.240 | 0.411 | 0.629 | 0.898 |
| Grid-Constrained / Efficiency-Upside | 0.070 | 0.140 | 0.221 | 0.311 | 0.409 |

## Workbook

- `00_Logic`: calculation steps only.
- `01_Benchmark_Input`: 업체별 short/long/agentic 비율, GPU별 chat-length TPS/MW, GPU별 workload 평균 TPS/MW, commercial workload fit 입력.
- `02_Inputs`: 전력 및 workload allocation 입력.
- `02_GPU_Mix_Input`: H200/B200/GB200/purpose-built share를 나중에 직접 교체하는 입력 시트.
- `03_Calculation`: formula-only calculation chain.
- `04_Output`: formula-driven 2026-2030 provider/scenario tables for tokens/day and tokens/year with charts.
- `05_Checks`: formula checks.
- `06_Aggressive_View`: Bull commercial case와 public benchmark ceiling의 formula-driven upside view.
- `07_Source_Registry`, `08_Provenance_Trace`, `09_Fact_Assumption_Audit`: expanded source/provenance layer.
