# Compute Capacity To Generated Output Token Supply

- 생성일: 2026-05-27
- 범위: 상용 LLM model owner 기준 2026-2030 시뮬레이션
- 출력 정의: generated output tokens/day

## Core Formula

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
reference_serving_tps_per_mw = inferencex_reference_tps_per_mw * commercial_workload_fit_factor
weighted_tps_per_mw = gpu_share * reference_serving_tps_per_mw + purpose_built_share * purpose_built_tps_per_mw
generated_output_tokens_per_day = inference_gw * 1,000 * weighted_tps_per_mw * 86,400
```

- Headline 계산에는 `utilization`, MoE uplift, architecture multiplier, software CAGR를 적용하지 않습니다.
- InferenceX raw value는 public reference ceiling이며, 상용 서비스에 쓰는 TPS/MW는 workload fit factor를 반영합니다.
- Purpose-built accelerator의 comparable benchmark가 없으면 workload-adjusted serving reference와 동일한 TPS/MW를 사용합니다.

## Public Benchmark Reference And Commercial Fit

| Provider | Workload class | Proxy model | Public reference TPS/MW | Base fit | Base serving reference TPS/MW |
|---|---|---|---:|---:|---:|
| Microsoft | Copilot / routed closed-model assistant | gptoss120b | 724,940 | 60% | 434,964 |
| Google | Gemini product-integrated multimodal assistant | gptoss120b | 724,940 | 60% | 434,964 |
| Meta | Llama / Meta AI general assistant | llama70b | 282,860 | 90% | 254,574 |
| xAI | Grok interactive and reasoning assistant | gptoss120b | 724,940 | 55% | 398,717 |
| OpenAI | GPT / ChatGPT / API with reasoning mix | gptoss120b | 724,940 | 50% | 362,470 |
| Anthropic | Claude coding, agent and long-context enterprise | gptoss120b | 724,940 | 50% | 362,470 |
| DeepSeek | DeepSeek R1/V3 MoE with reasoning mix | dsr1 | 101,245 | 85% | 86,058 |
| Alibaba | Qwen API / enterprise MoE assistant | qwen3.5 | 179,145 | 90% | 161,230 |
| Tencent | Hunyuan consumer and enterprise assistant | gptoss120b | 724,940 | 60% | 434,964 |

## Base 2030 Output

| Provider | Operational GW | Inference GW | Serving Reference TPS/MW | Tokens/day (Q) |
|---|---:|---:|---:|---:|
| OpenAI | 8.500 | 4.862 | 362,470 | 0.152 |
| Google | 6.800 | 3.651 | 434,964 | 0.137 |
| Microsoft | 6.200 | 3.333 | 434,964 | 0.125 |
| Anthropic | 5.500 | 2.966 | 362,470 | 0.093 |
| Meta | 5.800 | 3.280 | 254,574 | 0.072 |
| Tencent | 2.400 | 1.311 | 434,964 | 0.049 |
| xAI | 2.500 | 1.219 | 398,717 | 0.042 |
| Alibaba | 3.200 | 1.748 | 161,230 | 0.024 |
| DeepSeek | 1.200 | 0.651 | 86,058 | 0.005 |

## Scenario Output

| Scenario | 2026 Q/day | 2027 Q/day | 2028 Q/day | 2029 Q/day | 2030 Q/day |
|---|---:|---:|---:|---:|---:|
| Bear | 0.063 | 0.121 | 0.185 | 0.255 | 0.330 |
| Base | 0.121 | 0.239 | 0.375 | 0.529 | 0.700 |
| Bull | 0.182 | 0.374 | 0.608 | 0.887 | 1.212 |
| Grid-Constrained / Efficiency-Upside | 0.110 | 0.209 | 0.314 | 0.422 | 0.531 |

## Workbook

- `00_Logic`: calculation steps only.
- `01_Benchmark_Input`: public InferenceX reference와 commercial workload fit scenario 입력.
- `02_Inputs`: direct model inputs; serving reference TPS/MW cells are formulas.
- `03_Calculation`: formula-only calculation chain.
- `04_Output`: formula-driven output tables and chart.
- `05_Checks`: formula checks.
- `06_Aggressive_View`: Bull commercial case와 public benchmark ceiling의 formula-driven upside view.
