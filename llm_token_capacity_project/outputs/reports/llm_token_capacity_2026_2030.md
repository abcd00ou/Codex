# Compute Capacity To Generated Output Token Supply

- 생성일: 2026-07-30
- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션
- 출력 정의: generated output tokens/day

## Core Formula

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
gpu_workload_avg_tps_per_mw = short_share*gpu_short_tps_mw + long_share*gpu_long_tps_mw + agentic_share*gpu_agentic_tps_mw
company_accelerator_share = sum(datacenter_capacity_weight * ai_capacity_share * inference_share * datacenter_accelerator_share) / sum(datacenter_capacity_weight * ai_capacity_share * inference_share)
fleet_reference_tps_per_mw = h200_share*h200_workload_avg + b200_share*b200_workload_avg + gb200_share*gb200_workload_avg + purpose_built_share*purpose_workload_avg
serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor
generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400
```

- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.
- GPU/accelerator mix는 `02a_DC_Capacity_Alloc`의 데이터센터별 AI업체 capacity 배분과 `02b_DC_Accelerator_Mix`의 데이터센터별 장비 mix를 inference-weighted average로 결합합니다.
- InferenceX GPU별 값은 public reference이며, 상용 서비스 TPS/MW는 short conversation, long conversation, agentic workload mix와 workload fit factor를 반영합니다.
- R200/R300/TPU/Trainium/Maia/MTIA/other는 세부 mix로 보이지만, comparable output-token/MW benchmark가 없으면 산출용 `purpose-or-unbenchmarked` 버킷에서 B200 placeholder를 사용합니다.

## GPU Generation Mix, Workload Mix And Commercial Fit

| Provider | Proxy | 2030 H/B/GB/PB | Short/Long/Agentic | Weighted ref TPS/MW | Fit | Serving TPS/MW |
|---|---|---:|---:|---:|---:|---:|
| Microsoft | gptoss120b | 2%/71%/0%/27% | 45%/30%/25% | 2,856,801 | 60% | 1,714,081 |
| Google | frontier_composite | 0%/8%/1%/90% | 40%/40%/20% | 170,988 | 60% | 102,593 |
| Meta | llama70b | 0%/61%/0%/39% | 70%/20%/10% | 941,060 | 90% | 846,954 |
| xAI | gptoss120b | 0%/100%/0%/0% | 45%/35%/20% | 3,010,288 | 55% | 1,655,658 |
| OpenAI | frontier_composite | 6%/52%/22%/20% | 45%/25%/30% | 197,389 | 50% | 98,694 |
| Anthropic | frontier_composite | 7%/11%/0%/82% | 30%/30%/40% | 188,100 | 50% | 94,050 |
| DeepSeek | dsr1 | 10%/35%/55%/0% | 35%/40%/25% | 184,158 | 85% | 156,534 |
| Alibaba | qwen3.5 | 100%/0%/0%/0% | 45%/35%/20% | 166,591 | 90% | 149,932 |
| Tencent | gptoss120b | 10%/35%/55%/0% | 65%/25%/10% | 3,392,622 | 60% | 2,035,573 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| Microsoft | 6.200 | 3.333 | 1,714,081 | 0.494 |
| Meta | 5.800 | 3.280 | 846,954 | 0.240 |
| Tencent | 2.400 | 1.311 | 2,035,573 | 0.231 |
| xAI | 2.500 | 1.219 | 1,655,658 | 0.174 |
| OpenAI | 8.500 | 4.862 | 98,694 | 0.041 |
| Google | 6.800 | 3.651 | 102,593 | 0.032 |
| Anthropic | 5.500 | 2.966 | 94,050 | 0.024 |
| Alibaba | 3.200 | 1.748 | 149,932 | 0.023 |
| DeepSeek | 1.200 | 0.651 | 156,534 | 0.009 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.114 | 0.221 | 0.346 | 0.479 | 0.626 |
| Base | 0.210 | 0.418 | 0.671 | 0.951 | 1.268 |
| Bull | 0.309 | 0.639 | 1.062 | 1.555 | 2.140 |
| Grid-Constrained / Efficiency-Upside | 0.192 | 0.366 | 0.561 | 0.758 | 0.961 |

## Workbook

- `00_Logic`: calculation steps only.
- `01_Benchmark_Input`: 업체별 short/long/agentic 비율, GPU별 chat-length TPS/MW, GPU별 workload 평균 TPS/MW, commercial workload fit 입력.
- `02_Inputs`: 전력 및 workload allocation 입력.
- `02a_DC_Capacity_Alloc`: 데이터센터가 계약/할당한 AI업체 capacity weight, inference/training split 입력.
- `02b_DC_Accelerator_Mix`: 데이터센터별 H200/B200/GB200/R200/TPU/Trainium/Maia/MTIA/other accelerator mix 입력.
- `02c_DC_Accel_Bridge`: capacity allocation과 accelerator mix를 연결하는 formula bridge.
- `02_GPU_Mix_Input`: 회사별 GPU/accelerator mix 자동 산출 시트. `03_Calculation`은 이 시트의 D:G를 읽습니다.
- `03_Calculation`: formula-only calculation chain.
- `04_Output`: formula-driven 2026-2030 provider/scenario tables for tokens/day and tokens/year with charts.
- `05_Checks`: formula checks.
- `06_Aggressive_View`: Bull commercial case와 public benchmark ceiling의 formula-driven upside view.
- `07_Source_Registry`, `08_Provenance_Trace`, `09_Fact_Assumption_Audit`: expanded source/provenance layer.
