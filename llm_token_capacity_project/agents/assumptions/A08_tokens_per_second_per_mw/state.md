# State: A08 tokens_per_second_per_mw

| Field | Value |
|---|---|
| agent_id | A08 |
| owned_field | tokens_per_second_per_mw |
| current_starting_band | wide proxy band; company production fact unavailable |
| confidence | Low-Medium; benchmark calibrated |
| last_reviewed | 2026-05-27 |
| status | Simple core mapping adopted: fixed-condition InferenceX output TPS/MW proxy; no unverified uplift |

## Current Assumption

wide proxy band; company production fact unavailable

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-18 | Keep Base tokens/MW unchanged; add future energy sanity layer and scenario sensitivity for P/D disaggregation, speculative decoding, and test-time compute | 2026 sources indicate serving efficiency is workload/SLO/model dependent. Evidence supports mechanism/proxy refinement, not a direct company production coefficient change. | A08_E002; A08_E003; A08_E004 | proposed - orchestrator review required |
| 2026-05-19 | Add InferenceX dump-derived benchmark profile table; keep Base tokens/MW unchanged | Full dump gives actual benchmark rows by model/GPU/framework/precision/ISL/OSL, but it is still benchmark/proxy rather than company production telemetry. Coefficient change needs a separate mapping from benchmark rows to model-owner serving mix. | A08_E005 | implemented as evidence layer; no Base change |
| 2026-05-26 | Compute tokens/MW through explicit GPU/purpose-built accelerator mix factor and architecture/workload factor | Former workbook described GPU/ASIC platforms but did not numerically bridge mix into tokens/MW. | A08_E005; A11_E001-A11_E009 | implemented; coefficient remains derived estimate |
| 2026-05-27 | Replace compounded efficiency bridge with fixed-condition InferenceX output-token selection | Executive headline needs reconstructable logic with the fewest unsupported coefficients. B200, single_turn, ISL/OSL 1024/1024 output TPS/MW p50 is directly inspectable in the normalized dump. | A08_E005; HC22 | implemented in headline model |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.

## Cycle 1 Notes

- Do not promote InferenceX/Joule/IBM values into Base until exact benchmark assumptions are mapped to company/model workload mix.
- `05b_inferencex_core_tps` is the direct headline TPS/MW lookup table: B200, single_turn, ISL/OSL 1024/1024, `output_tok_s_mw` p50.
- InferenceX tables to use first: `inferencex_metric_profile.csv` for p10/p50/p90 bands and `inferencex_benchmark_results.csv` for exact row-level audit.
- New formula: `gpu_share * gpu_benchmark_tps_per_mw + purpose_built_share * purpose_built_tps_per_mw`.
- Until a comparable purpose-built output-token row is adopted, `purpose_built_tps_per_mw = gpu_benchmark_tps_per_mw`; no TPU/Maia/MTIA/Trainium uplift enters headline output.
- Every company-year bridge is traceable in Excel `02b_number_trace` and `05_inference_efficiency`.
