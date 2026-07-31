# Compute Capacity To Generated Output Token Supply

- 생성일: 2026-07-31
- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션
- 출력 정의: generated output tokens/day

## Core Formula

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
gpu_workload_avg_tps_per_mw = short_share*gpu_short_tps_mw + long_share*gpu_long_tps_mw + agentic_share*gpu_agentic_tps_mw
csp_contract_inference_weight = csp_total_power_mw * ai_contract_share_of_csp * inference_share
normalized_csp_inference_power_mw = company_inference_power_mw * csp_contract_inference_weight / sum(company csp_contract_inference_weight)
accelerator_power_mw = normalized_csp_inference_power_mw * csp_accelerator_share
fleet_reference_tps_per_mw = h200_share*h200_workload_avg + b200_share*b200_workload_avg + gb200_share*gb200_workload_avg + purpose_built_share*purpose_workload_avg
serving_tps_per_mw = fleet_reference_tps_per_mw * commercial_workload_fit_factor
generated_output_tokens_per_day = inference_gw * 1,000 * serving_tps_per_mw * 86,400
```

- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.
- GPU/accelerator mix는 `02a_CSP_Contract_Alloc`의 CSP 총 전력과 AI업체 계약 비중을 먼저 곱한 뒤, 그 weight로 회사 inference power를 CSP별로 정규화하고 `02b_CSP_Accelerator_Mix`를 곱합니다.
- InferenceX GPU별 값은 public reference이며, 상용 서비스 TPS/MW는 short conversation, long conversation, agentic workload mix와 workload fit factor를 반영합니다.
- Accelerator는 long-format catalog 구조입니다. `02x_Accelerator_Catalog`에 새 accelerator, benchmark bucket, all-in kW/unit을 추가하고 `02b`에 share row를 추가하면 확장됩니다.
- R200/R300/TPU/Trainium/Maia/MTIA/other는 세부 power/count로 보이지만, comparable output-token/MW benchmark가 없으면 산출용 `purpose-or-unbenchmarked` 버킷에서 B200 placeholder를 사용합니다.

## GPU Generation Mix, Workload Mix And Commercial Fit

| Provider | Proxy | 2030 H/B/GB/PB | Short/Long/Agentic | Weighted ref TPS/MW | Fit | Serving TPS/MW |
|---|---|---:|---:|---:|---:|---:|
| Microsoft | gptoss120b | 5%/95%/0%/0% | 45%/30%/25% | 2,801,033 | 60% | 1,680,620 |
| Google | frontier_composite | 0%/9%/0%/91% | 40%/40%/20% | 167,768 | 60% | 100,661 |
| Meta | llama70b | 7%/74%/0%/19% | 70%/20%/10% | 925,083 | 90% | 832,575 |
| xAI | gptoss120b | 29%/71%/0%/0% | 45%/35%/20% | 2,476,756 | 55% | 1,362,216 |
| OpenAI | frontier_composite | 4%/79%/4%/13% | 45%/25%/30% | 172,495 | 50% | 86,248 |
| Anthropic | frontier_composite | 8%/12%/0%/80% | 30%/30%/40% | 196,472 | 50% | 98,236 |
| DeepSeek | dsr1 | 10%/35%/55%/0% | 35%/40%/25% | 184,158 | 85% | 156,534 |
| Alibaba | qwen3.5 | 100%/0%/0%/0% | 45%/35%/20% | 166,591 | 90% | 149,932 |
| Tencent | gptoss120b | 10%/35%/55%/0% | 65%/25%/10% | 3,392,622 | 60% | 2,035,573 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| Microsoft | 6.200 | 3.333 | 1,680,620 | 0.484 |
| Meta | 5.800 | 3.280 | 832,575 | 0.236 |
| Tencent | 2.400 | 1.311 | 2,035,573 | 0.231 |
| xAI | 2.500 | 1.219 | 1,362,216 | 0.143 |
| OpenAI | 8.500 | 4.862 | 86,248 | 0.036 |
| Google | 6.800 | 3.651 | 100,661 | 0.032 |
| Anthropic | 5.500 | 2.966 | 98,236 | 0.025 |
| Alibaba | 3.200 | 1.748 | 149,932 | 0.023 |
| DeepSeek | 1.200 | 0.651 | 156,534 | 0.009 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.109 | 0.210 | 0.330 | 0.460 | 0.603 |
| Base | 0.200 | 0.397 | 0.638 | 0.909 | 1.219 |
| Bull | 0.294 | 0.606 | 1.007 | 1.484 | 2.054 |
| Grid-Constrained / Efficiency-Upside | 0.183 | 0.347 | 0.533 | 0.725 | 0.923 |

## Workbook

- `00_Logic`: calculation steps only.
- `01_Benchmark_Input`: 업체별 short/long/agentic 비율, GPU별 chat-length TPS/MW, GPU별 workload 평균 TPS/MW, commercial workload fit 입력.
- `02_Inputs`: 전력 및 workload allocation 입력.
- `02x_Accelerator_Catalog`: accelerator type, benchmark bucket, all-in kW/unit catalog.
- `02a_CSP_Contract_Alloc`: CSP별 총 전력, AI업체 계약 비중, inference/training split 입력.
- `02b_CSP_Accelerator_Mix`: CSP별 accelerator share long-format 입력.
- `02c_AI_CSP_Normalized`: 회사 inference MW를 CSP 계약 weight로 정규화하는 formula bridge.
- `02d_AI_Accelerator_Power`: 회사/CSP/accelerator별 power와 unit count 산출.
- `02_GPU_Mix_Input`: 회사별 GPU/accelerator mix 자동 산출 시트. `03_Calculation`은 이 시트의 D:G를 읽습니다.
- `03_Calculation`: formula-only calculation chain.
- `04_Output`: formula-driven 2026-2030 provider/scenario tables for tokens/day and tokens/year with charts.
- `05_Checks`: formula checks.
- `06_Aggressive_View`: Bull commercial case와 public benchmark ceiling의 formula-driven upside view.
- `07_Source_Registry`, `08_Provenance_Trace`, `09_Fact_Assumption_Audit`: expanded source/provenance layer.
