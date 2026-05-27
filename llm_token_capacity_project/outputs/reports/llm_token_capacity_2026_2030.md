# Compute Capacity To Generated Output Token Supply

- 생성일: 2026-05-27
- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션
- 출력 정의: generated output tokens/day

## Core Formula

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
fleet_reference_tps_per_mw = h200_share*h200_ref + b200_share*b200_ref + gb200_share*gb200_ref + purpose_built_share*purpose_ref
serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor
generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400
```

- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.
- GPU 세대 mix는 `H200`, `B200`, `GB200`, `purpose-built`의 inference-load share이며 Excel에서 별도 입력합니다.
- InferenceX GPU별 값은 public reference이며, 상용 서비스 TPS/MW는 workload fit factor를 반영합니다.
- Purpose-built accelerator의 comparable benchmark가 없으면 B200 placeholder를 사용하며 이후 입력으로 교체합니다.

## GPU Generation Mix And Commercial Fit

| Provider | Proxy | 2030 default H200/B200/GB200/PB | Base fleet ref TPS/MW | Base fit | Base serving TPS/MW |
|---|---|---:|---:|---:|---:|
| Microsoft | gptoss120b | 6%/19%/30%/45% | 705,383 | 60% | 423,230 |
| Google | gptoss120b | 1%/4%/6%/90% | 721,384 | 60% | 432,830 |
| Meta | llama70b | 6%/19%/30%/45% | 282,958 | 90% | 254,662 |
| xAI | gptoss120b | 10%/35%/55%/0% | 689,381 | 55% | 379,160 |
| OpenAI | gptoss120b | 10%/35%/55%/0% | 689,381 | 50% | 344,690 |
| Anthropic | gptoss120b | 2%/5%/8%/85% | 719,606 | 50% | 359,803 |
| DeepSeek | dsr1 | 10%/35%/55%/0% | 443,721 | 85% | 377,163 |
| Alibaba | qwen3.5 | 10%/35%/55%/0% | 179,145 | 90% | 161,230 |
| Tencent | gptoss120b | 10%/35%/55%/0% | 689,381 | 60% | 413,629 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| OpenAI | 8.500 | 4.862 | 344,690 | 0.145 |
| Google | 6.800 | 3.651 | 432,830 | 0.137 |
| Microsoft | 6.200 | 3.333 | 423,230 | 0.122 |
| Anthropic | 5.500 | 2.966 | 359,803 | 0.092 |
| Meta | 5.800 | 3.280 | 254,662 | 0.072 |
| Tencent | 2.400 | 1.311 | 413,629 | 0.047 |
| xAI | 2.500 | 1.219 | 379,160 | 0.040 |
| Alibaba | 3.200 | 1.748 | 161,230 | 0.024 |
| DeepSeek | 1.200 | 0.651 | 377,163 | 0.021 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.054 | 0.108 | 0.173 | 0.247 | 0.332 |
| Base | 0.103 | 0.212 | 0.347 | 0.510 | 0.700 |
| Bull | 0.155 | 0.332 | 0.562 | 0.852 | 1.207 |
| Grid-Constrained / Efficiency-Upside | 0.094 | 0.186 | 0.291 | 0.407 | 0.531 |

## Workbook

- `00_Logic`: calculation steps only.
- `01_Benchmark_Input`: GPU 세대별 public reference TPS/MW와 commercial workload fit 입력.
- `02_Inputs`: 전력 및 workload allocation 입력.
- `02_GPU_Mix_Input`: H200/B200/GB200/purpose-built share를 나중에 직접 교체하는 입력 시트.
- `03_Calculation`: formula-only calculation chain.
- `04_Output`: formula-driven output tables and chart.
- `05_Checks`: formula checks.
- `06_Aggressive_View`: Bull commercial case와 public benchmark ceiling의 formula-driven upside view.
