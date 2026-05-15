# State: A07 active_parameters

| Field | Value |
|---|---|
| agent_id | A07 |
| owned_field | parameter_band_active |
| current_starting_band | Dense active ~= total; MoE official active params; closed model band only |
| confidence | High for official open model cards; Low for closed model proxy |
| last_reviewed | 2026-05-15 |
| status | Initial setup |

## Current Assumption

Dense active ~= total; MoE official active params; closed model band only

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
