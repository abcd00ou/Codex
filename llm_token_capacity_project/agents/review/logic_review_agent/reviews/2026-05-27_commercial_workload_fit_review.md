# Logic Review: Commercial Workload TPS/MW Bridge And Aggressive View

**Review date:** 2026-05-27  
**Scope:** Executive Excel, core report outputs, and token-supply presentation  
**Status:** PASS for formula structure and scenario separation; production benchmark replacement remains open

## Review Decision

The former direct mapping from a public InferenceX model row to several closed or differently shaped commercial LLM surfaces was too aggressive for a Base-case coefficient. The model now preserves the simple power-to-token formula while separating:

```text
inferencex_reference_tps_per_mw
* commercial_workload_fit_factor
= reference_serving_tps_per_mw
```

The public benchmark remains a transparent reference ceiling. The coefficient entering generated-output token supply is a scenario-based commercial serving reference.

## Formula Review

```text
operational_power_gw = contracted_power_gw * operational_deployment_share
inference_gw = operational_power_gw / pue * ai_workload_share * inference_power_share
reference_serving_tps_per_mw =
  inferencex_reference_tps_per_mw * commercial_workload_fit_factor
weighted_tps_per_mw =
  gpu_share * reference_serving_tps_per_mw
  + purpose_built_share * purpose_built_tps_per_mw
generated_output_tokens_per_day =
  inference_gw * 1,000 * weighted_tps_per_mw * 86,400
```

- The headline still excludes utilization, hidden MoE uplift, software CAGR and unsupported ASIC premium.
- Purpose-built TPS/MW equals the workload-adjusted serving reference unless matched output-token evidence replaces it.
- Bear/Base/Bull now move an explicit workload-fit input rather than silently assuming commercial equivalence to the public reference.

## Aggressive View Review

`06_Aggressive_View` separates two ideas:

- **Bull commercial case:** faster deployment, higher inference allocation and favorable commercial workload fit.
- **Public reference ceiling:** same Bull inference power with `commercial_workload_fit_factor = 100%`.

The ceiling is labeled as strategic upside, not a Base forecast or observed production throughput.

## Artifact Verification

- Visible Excel sheets: `00_Logic`, `01_Benchmark_Input`, `02_Inputs`, `03_Calculation`, `04_Output`, `05_Checks`, `06_Aggressive_View`.
- Formula counts: `02_Inputs` 1,080; `03_Calculation` 3,960; `04_Output` 83; `05_Checks` 14; `06_Aggressive_View` 78.
- Key formula checks passed: serving reference bridge, token/day calculation, annualization and formula-driven aggressive view.
- Generated result check: Base 2030 total `0.700 Q generated output tokens/day`; Bull 2030 total `1.212 Q/day`.
- PPT package QA passed: 12 slides, 7 native charts, no package warnings or failures.

## Open Replacement Path

The explicit fit factors should be replaced when a provider or a comparable benchmark discloses generated-output TPS/MW matched on commercial model/workload class, precision, ISL/OSL, latency SLO and serving hardware.
