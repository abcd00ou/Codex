# Compute Capacity To Generated Output Token Supply

- 생성일: 2026-07-20
- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션
- 출력 정의: generated output tokens/day

## Core Formula

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
fleet_reference_tps_per_mw = h200_share*h200_ref + b200_share*b200_ref + gb200_share*gb200_ref + purpose_built_share*purpose_ref
weighted_reference_tps_per_mw = short_share*short_chat_tps_mw + long_share*long_chat_tps_mw + agentic_share*agentic_tps_mw
serving_tps_per_mw = weighted_reference_tps_per_mw * commercial_workload_fit_factor
generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400
```

- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.
- GPU 세대 mix는 `H200`, `B200`, `GB200`, `purpose-built`의 inference-load share이며 Excel에서 별도 입력합니다.
- InferenceX GPU별 값은 public reference이며, 상용 서비스 TPS/MW는 short conversation, long conversation, agentic workload mix와 workload fit factor를 반영합니다.
- Purpose-built accelerator의 comparable benchmark가 없으면 B200 placeholder를 사용하며 이후 입력으로 교체합니다.

## GPU Generation Mix, Workload Mix And Commercial Fit

| Provider | Proxy | 2030 H/B/GB/PB | Short/Long/Agentic | Weighted ref TPS/MW | Fit | Serving TPS/MW |
|---|---|---:|---:|---:|---:|---:|
| Microsoft | gptoss120b | 6%/19%/30%/45% | 45%/30%/25% | 578,239 | 60% | 346,943 |
| Google | gptoss120b | 1%/4%/6%/90% | 40%/40%/20% | 589,957 | 60% | 353,974 |
| Meta | llama70b | 6%/19%/30%/45% | 70%/20%/10% | 180,858 | 90% | 162,772 |
| xAI | gptoss120b | 10%/35%/55%/0% | 45%/35%/20% | 587,060 | 55% | 322,883 |
| OpenAI | gptoss120b | 10%/35%/55%/0% | 45%/25%/30% | 559,920 | 50% | 279,960 |
| Anthropic | gptoss120b | 2%/5%/8%/85% | 30%/30%/40% | 523,692 | 50% | 261,846 |
| DeepSeek | dsr1 | 10%/35%/55%/0% | 35%/40%/25% | 51,301 | 85% | 43,606 |
| Alibaba | qwen3.5 | 10%/35%/55%/0% | 45%/35%/20% | 142,879 | 90% | 128,591 |
| Tencent | gptoss120b | 10%/35%/55%/0% | 65%/25%/10% | 631,190 | 60% | 378,714 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| OpenAI | 8.500 | 4.862 | 279,960 | 0.118 |
| Google | 6.800 | 3.651 | 353,974 | 0.112 |
| Microsoft | 6.200 | 3.333 | 346,943 | 0.100 |
| Anthropic | 5.500 | 2.966 | 261,846 | 0.067 |
| Meta | 5.800 | 3.280 | 162,772 | 0.046 |
| Tencent | 2.400 | 1.311 | 378,714 | 0.043 |
| xAI | 2.500 | 1.219 | 322,883 | 0.034 |
| Alibaba | 3.200 | 1.748 | 128,591 | 0.019 |
| DeepSeek | 1.200 | 0.651 | 43,606 | 0.002 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.041 | 0.083 | 0.132 | 0.190 | 0.254 |
| Base | 0.080 | 0.164 | 0.268 | 0.394 | 0.541 |
| Bull | 0.120 | 0.257 | 0.436 | 0.663 | 0.939 |
| Grid-Constrained / Efficiency-Upside | 0.073 | 0.143 | 0.224 | 0.314 | 0.410 |

## Workbook

- `00_Logic`: calculation steps only.
- `01_Benchmark_Input`: GPU 세대별 public reference TPS/MW와 commercial workload fit 입력.
- `02_Inputs`: 전력 및 workload allocation 입력.
- `02_GPU_Mix_Input`: H200/B200/GB200/purpose-built share를 나중에 직접 교체하는 입력 시트.
- `03_Calculation`: formula-only calculation chain.
- `04_Output`: formula-driven 2026-2030 provider/scenario tables for tokens/day and tokens/year with charts.
- `05_Checks`: formula checks.
- `06_Aggressive_View`: Bull commercial case와 public benchmark ceiling의 formula-driven upside view.
- `07_Source_Registry`, `08_Provenance_Trace`, `09_Fact_Assumption_Audit`: expanded source/provenance layer.
