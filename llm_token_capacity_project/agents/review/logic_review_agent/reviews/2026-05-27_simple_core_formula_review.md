# Logic Review: Simple Core Token Formula

**Review date:** 2026-05-27  
**Artifact scope:** Excel, Markdown, HTML and English executive PPT outputs generated from `tools/generate_llm_token_capacity_report.py`  
**Overall status:** pass for formula integrity; proxy replacement work remains open

## Conclusion

The headline token-capacity model is now materially easier to defend in an executive review. The result is calculated from operationally deployable capacity, PUE, AI workload allocation, inference allocation and one selected InferenceX generated-output TPS/MW proxy. The prior compounded utilization, MoE, architecture and software-improvement multipliers do not enter the headline output.

## Headline Formula Review

```text
active_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = active_power_gw / pue * ai_workload_share * inference_power_share
tokens_per_second_per_mw =
  gpu_share * gpu_benchmark_tps_per_mw
  + purpose_built_share * purpose_built_tps_per_mw
inference_tokens_per_day =
  inference_gw * 1,000 * tokens_per_second_per_mw * 86,400
```

Checks passed:

- `active_power_gw <= contracted_power_gw` and the displayed deployment share reconstructs active GW.
- `training_power_share + inference_power_share = 100%`.
- GPU and purpose-built accelerator shares sum to 100%.
- TPS/MW and daily/annual token results reconstruct exactly from displayed core values.
- Purpose-built accelerators receive no unsupported TPS/MW uplift without a comparable adopted output-token benchmark.

## InferenceX Mapping Review

The new `05b_inferencex_core_tps` sheet exposes the selected comparison rows under one consistent condition: `B200`, `single_turn`, `ISL=1024`, `OSL=1024`, `output_tok_s_mw` median.

| Proxy model | Output tok/s/MW p50 | Mapped use |
|---|---:|---|
| gptoss120b | 724,940 | Microsoft, Google, xAI, OpenAI, Anthropic, Tencent closed/general proxy |
| llama70b | 282,860 | Meta proxy |
| dsr1 | 101,245 | DeepSeek proxy |
| qwen3.5 | 179,145 | Alibaba proxy |

These are benchmark proxies, not measured company sustained production throughput. Replacement requires matched production telemetry or a more directly comparable model/hardware benchmark.

## Artifact Verification

- Generator validation: PASS.
- Assumption agent structure validation: PASS for 11 agents.
- Executive workbook now exposes only `00_Logic`, `01_Benchmark_Input`, `02_Inputs`, `03_Calculation`, `04_Output`, `05_Checks`.
- `03_Calculation`: 3,600 formula cells; `04_Output`: 83 formula cells; `05_Checks`: 10 formula cells.
- Direct numeric input is confined to assumption and selected benchmark input areas; calculated output is not pasted as values.
- Detailed trace and fact/assumption audit remain in internal project records instead of being shown in the executive workbook.
- PPTX package check: 12 slides, 7 charts, no zero-byte/invalid media, placeholders, slide-number placeholders or debug-line warnings.

## Open Follow-Ups

- Replace proxy TPS/MW with provider/model matched output-token throughput where evidence becomes available.
- Replace operational deployment and inference allocation scenarios with official site-level or workload telemetry.
- Keep utilization and production SLO effects in sensitivity research until suitable denominated evidence exists.
