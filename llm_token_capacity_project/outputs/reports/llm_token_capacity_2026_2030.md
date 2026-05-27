# Compute Capacity To Generated Output Token Supply

- 생성일: 2026-05-27
- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션
- 출력 정의: generated output tokens/day

## Core Formula

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
weighted_tps_per_mw = gpu_share * gpu_benchmark_tps_per_mw + purpose_built_share * purpose_built_tps_per_mw
generated_output_tokens_per_day = inference_gw * 1,000 * weighted_tps_per_mw * 86,400
```

- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.
- Purpose-built accelerator의 comparable benchmark가 없으면 GPU proxy와 동일한 TPS/MW를 사용합니다.

## InferenceX Input

| Proxy model | 적용 업체 | Output tok/s/MW p50 | 조건 |
|---|---|---:|---|
| gptoss120b | Microsoft; Google; xAI; OpenAI; Anthropic; Tencent | 724,940 | B200, single_turn, ISL/OSL 1024/1024 |
| llama70b | Meta | 282,860 | B200, single_turn, ISL/OSL 1024/1024 |
| dsr1 | DeepSeek | 101,245 | B200, single_turn, ISL/OSL 1024/1024 |
| qwen3.5 | Alibaba | 179,145 | B200, single_turn, ISL/OSL 1024/1024 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Selected TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| OpenAI | 8.500 | 4.862 | 724,940 | 0.305 |
| Google | 6.800 | 3.651 | 724,940 | 0.229 |
| Microsoft | 6.200 | 3.333 | 724,940 | 0.209 |
| Anthropic | 5.500 | 2.966 | 724,940 | 0.186 |
| Tencent | 2.400 | 1.311 | 724,940 | 0.082 |
| Meta | 5.800 | 3.280 | 282,860 | 0.080 |
| xAI | 2.500 | 1.219 | 724,940 | 0.076 |
| Alibaba | 3.200 | 1.748 | 179,145 | 0.027 |
| DeepSeek | 1.200 | 0.651 | 101,245 | 0.006 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.155 | 0.306 | 0.473 | 0.656 | 0.853 |
| Base | 0.201 | 0.404 | 0.638 | 0.903 | 1.199 |
| Bull | 0.231 | 0.480 | 0.783 | 1.143 | 1.565 |
| Grid-Constrained / Efficiency-Upside | 0.184 | 0.354 | 0.534 | 0.721 | 0.909 |

## Workbook

- `00_Logic`: calculation steps only.
- `01_Benchmark_Input`: selected InferenceX TPS/MW inputs.
- `02_Inputs`: direct model inputs; benchmark TPS cells are formulas.
- `03_Calculation`: formula-only calculation chain.
- `04_Output`: formula-driven output tables and chart.
- `05_Checks`: formula checks.
