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
| Microsoft | gptoss120b | 6%/19%/30%/45% | 45%/30%/25% | 2,796,203 | 60% | 1,677,722 |
| Google | frontier_composite | 1%/4%/6%/90% | 40%/40%/20% | 180,926 | 60% | 108,556 |
| Meta | llama70b | 6%/19%/30%/45% | 70%/20%/10% | 929,331 | 90% | 836,398 |
| xAI | gptoss120b | 10%/35%/55%/0% | 45%/35%/20% | 2,828,887 | 55% | 1,555,888 |
| OpenAI | frontier_composite | 10%/35%/55%/0% | 45%/25%/30% | 246,309 | 50% | 123,154 |
| Anthropic | frontier_composite | 2%/5%/8%/85% | 30%/30%/40% | 148,798 | 50% | 74,399 |
| DeepSeek | dsr1 | 10%/35%/55%/0% | 35%/40%/25% | 184,158 | 85% | 156,534 |
| Alibaba | qwen3.5 | 10%/35%/55%/0% | 45%/35%/20% | 634,456 | 90% | 571,010 |
| Tencent | gptoss120b | 10%/35%/55%/0% | 65%/25%/10% | 3,392,622 | 60% | 2,035,573 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| Microsoft | 6.200 | 3.333 | 1,677,722 | 0.483 |
| Meta | 5.800 | 3.280 | 836,398 | 0.237 |
| Tencent | 2.400 | 1.311 | 2,035,573 | 0.231 |
| xAI | 2.500 | 1.219 | 1,555,888 | 0.164 |
| Alibaba | 3.200 | 1.748 | 571,010 | 0.086 |
| OpenAI | 8.500 | 4.862 | 123,154 | 0.052 |
| Google | 6.800 | 3.651 | 108,556 | 0.034 |
| Anthropic | 5.500 | 2.966 | 74,399 | 0.019 |
| DeepSeek | 1.200 | 0.651 | 156,534 | 0.009 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.105 | 0.213 | 0.341 | 0.488 | 0.653 |
| Base | 0.195 | 0.403 | 0.659 | 0.963 | 1.315 |
| Bull | 0.286 | 0.615 | 1.038 | 1.566 | 2.203 |
| Grid-Constrained / Efficiency-Upside | 0.177 | 0.353 | 0.551 | 0.768 | 0.996 |

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
