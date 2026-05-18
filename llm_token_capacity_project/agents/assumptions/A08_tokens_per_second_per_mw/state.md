# State: A08 tokens_per_second_per_mw

| Field | Value |
|---|---|
| agent_id | A08 |
| owned_field | tokens_per_second_per_mw |
| current_starting_band | wide proxy band; company production fact unavailable |
| confidence | Low-Medium; benchmark calibrated |
| last_reviewed | 2026-05-15 |
| status | Initial setup |

## Current Assumption

wide proxy band; company production fact unavailable

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-18 | Keep Base tokens/MW unchanged; add future energy sanity layer and scenario sensitivity for P/D disaggregation, speculative decoding, and test-time compute | 2026 sources indicate serving efficiency is workload/SLO/model dependent. Evidence supports mechanism/proxy refinement, not a direct company production coefficient change. | A08_E002; A08_E003; A08_E004 | proposed - orchestrator review required |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.

## Cycle 1 Notes

- Do not promote InferenceX/Joule/IBM values into Base until exact benchmark assumptions are extracted.
- Next implementation candidate: add a secondary `energy_sanity_reference` table to compare tokens/MW forecast against joules/token or energy/query ranges.
