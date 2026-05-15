# State: A02 active_power_gw

| Field | Value |
|---|---|
| agent_id | A02 |
| owned_field | active_power_gw |
| current_starting_band | 2026 active/contracted 15-45%; 2030 45-80% |
| confidence | Low-Medium until site-level energization evidence |
| last_reviewed | 2026-05-15 |
| status | Initial setup |

## Current Assumption

2026 active/contracted 15-45%; 2030 45-80%

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
