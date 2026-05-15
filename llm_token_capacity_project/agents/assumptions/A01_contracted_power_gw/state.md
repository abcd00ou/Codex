# State: A01 contracted_power_gw

| Field | Value |
|---|---|
| agent_id | A01 |
| owned_field | contracted_power_gw |
| current_starting_band | company-specific announced/planned GW; active conversion 금지 |
| confidence | Medium where official source exists; Low where inferred |
| last_reviewed | 2026-05-15 |
| status | Initial setup |

## Current Assumption

company-specific announced/planned GW; active conversion 금지

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
