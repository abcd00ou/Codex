# State: A02 active_power_gw

| Field | Value |
|---|---|
| agent_id | A02 |
| owned_field | active_power_gw |
| current_starting_band | 2026 active/contracted 15-45%; 2030 45-80% |
| confidence | Low-Medium until site-level energization evidence |
| last_reviewed | 2026-05-26 |
| status | Active-versus-contracted relationship formalized in audit trace |

## Current Assumption

2026 active/contracted 15-45%; 2030 45-80%

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-26 | Enforce `active_power_gw = min(contracted_power_gw, modeled operationally deployed power)` and disclose staged-ramp rationale by company | Active power requires energization and deployed accelerator readiness; it is not announced or reserved capacity. | SRC_OPENAI_STARGATE_PROGRESS; SRC_AWS_RAINIER_ACTIVE; SRC_XAI_NVIDIA_COLOSSUS | implemented |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
- Replacement evidence should include site energization, powered rack deployment, accelerator delivery and operational availability records.
