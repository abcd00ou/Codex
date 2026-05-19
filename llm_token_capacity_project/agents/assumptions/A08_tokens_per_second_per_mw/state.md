# State: A08 tokens_per_second_per_mw

| Field | Value |
|---|---|
| agent_id | A08 |
| owned_field | tokens_per_second_per_mw |
| current_starting_band | wide proxy band; company production fact unavailable |
| confidence | Low-Medium; benchmark calibrated |
| last_reviewed | 2026-05-19 |
| status | InferenceX dump normalized; Base unchanged pending orchestrator review |

## Current Assumption

wide proxy band; company production fact unavailable

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-18 | Keep Base tokens/MW unchanged; add future energy sanity layer and scenario sensitivity for P/D disaggregation, speculative decoding, and test-time compute | 2026 sources indicate serving efficiency is workload/SLO/model dependent. Evidence supports mechanism/proxy refinement, not a direct company production coefficient change. | A08_E002; A08_E003; A08_E004 | proposed - orchestrator review required |
| 2026-05-19 | Add InferenceX dump-derived benchmark profile table; keep Base tokens/MW unchanged | Full dump gives actual benchmark rows by model/GPU/framework/precision/ISL/OSL, but it is still benchmark/proxy rather than company production telemetry. Coefficient change needs a separate mapping from benchmark rows to model-owner serving mix. | A08_E005 | implemented as evidence layer; no Base change |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.

## Cycle 1 Notes

- Do not promote InferenceX/Joule/IBM values into Base until exact benchmark assumptions are mapped to company/model workload mix.
- Next implementation candidate: add a secondary `energy_sanity_reference` table to compare tokens/MW forecast against joules/token or energy/query ranges.
- InferenceX tables to use first: `inferencex_metric_profile.csv` for p10/p50/p90 bands and `inferencex_benchmark_results.csv` for exact row-level audit.
