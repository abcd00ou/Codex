# State: A10 attribution_rule

| Field | Value |
|---|---|
| agent_id | A10 |
| owned_field | attribution_rule |
| current_starting_band | model-owner forecast assigns token to model owner; host kept as infrastructure layer |
| confidence | Medium where contractual relationship is explicit; Low where routing is opaque |
| last_reviewed | 2026-05-26 |
| status | Model-owner attribution exposed in numeric trace and replacement path |

## Current Assumption

model-owner forecast assigns token to model owner; host kept as infrastructure layer

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-26 | Keep hardware host sources as infrastructure anchors while assigning token output to model owner; expose the rule in the number trace | Capacity and hardware anchors must not create duplicate model-owner token supply rows. | SRC_OPENAI_STARGATE_PROGRESS; SRC_ANTHROPIC_AMAZON_COMPUTE; SRC_AWS_RAINIER_ACTIVE; SRC_MS_MAIA200 | implemented |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
- Microsoft/OpenAI remains the highest-priority replacement path because Copilot can route Microsoft-owned and OpenAI-owned models.
