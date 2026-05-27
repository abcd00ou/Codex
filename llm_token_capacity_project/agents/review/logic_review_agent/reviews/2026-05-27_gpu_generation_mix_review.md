# Logic Review: GPU Generation Mix Input And Fleet-Weighted TPS/MW

**Review date:** 2026-05-27
**Scope:** Executive Excel, Markdown/HTML outputs and token-supply presentation
**Status:** PASS for formula structure and scenario-input separation; provider fleet replacement remains open

## Review Decision

The earlier `gpu_share` variable distinguished GPU from purpose-built accelerators, but did not express the production-relevant difference between H200, B200 and GB200 serving capacity. This gap matters because identical inference power can produce different generated-output token capacity under different accelerator generations.

The headline logic now preserves the simple power conversion while introducing one editable hardware-composition bridge:

```text
inference_gw =
  contracted_power_gw * operational_deployment_share
  / pue * ai_workload_share * inference_power_share

fleet_reference_tps_per_mw =
  h200_share * h200_reference_tps_per_mw
  + b200_share * b200_reference_tps_per_mw
  + gb200_share * gb200_reference_tps_per_mw
  + purpose_built_share * purpose_built_reference_tps_per_mw

serving_tps_per_mw =
  fleet_reference_tps_per_mw * commercial_workload_fit_factor

generated_output_tokens_per_day =
  inference_gw * 1,000 * serving_tps_per_mw * 86,400
```

## Input Policy

- `02_GPU_Mix_Input` exposes H200, B200, GB200 and purpose-built shares by scenario, company and year.
- The shares mean percentage of modeled inference-serving accelerator load, not confirmed unit inventory or officially disclosed racks.
- The starting GPU-generation migration assumption is H200/B200/GB200 `55%/40%/5%` of the GPU portion in 2026, moving to `10%/35%/55%` in 2030.
- Where a provider is modeled with purpose-built accelerators, that share remains separate; the GPU-generation percentages apply only to the GPU portion.
- Unit inventory can later replace these shares only after translating rack/accelerator counts to serving-load or power-weighted shares.

## Benchmark Selection Rule

The public InferenceX extract is used only as a generated-output TPS/MW reference under comparable fixed conditions. A hardware-model median is selected directly only when at least 50 comparable rows are present. When the row count is insufficient or absent, the workbook uses an explicit B200 placeholder until a better comparable input is adopted. Purpose-built TPS/MW also remains at the B200 placeholder unless matched output-token evidence is available.

## Verification

- Visible Excel input sheet added: `02_GPU_Mix_Input`.
- Mix integrity check: H200 + B200 + GB200 + purpose-built equals 100% for each company-year-scenario.
- Formula bridge check: `fleet_reference_tps_per_mw` is the weighted accelerator-generation reference and `serving_tps_per_mw` applies only the explicit commercial workload fit factor.
- Headline remains free of hidden utilization, MoE, architecture-premium or software-growth multipliers.

## Replacement Path

Replace scenario shares when provider-specific rack deployment, accelerator-hour routing, procurement delivery translated to active serving capacity, or matched production serving telemetry becomes available.
