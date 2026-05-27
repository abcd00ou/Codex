# State: A01 contracted_power_gw

| Field | Value |
|---|---|
| agent_id | A01 |
| owned_field | contracted_power_gw |
| current_starting_band | company-specific announced/planned GW; active conversion 금지 |
| confidence | Medium where official source exists; Low where inferred |
| last_reviewed | 2026-05-27 |
| status | Capacity public anchors and modeled endpoints explicitly separated in company audit |

## Current Assumption

company-specific announced/planned GW; active conversion 금지

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-26 | Define `contracted_power_gw` as sourced committed/planned ceiling where disclosed, otherwise explicit model-owner capacity envelope scenario | Not every company publishes comparable contract GW; a common numeric field must not imply common fact quality. | FACT_OPENAI_ORACLE_4_5GW; FACT_OPENAI_STARGATE_10GW; FACT_ANTHROPIC_AWS_5GW; FACT_XAI_COLOSSUS_100K | implemented in workbook trace layer |
| 2026-05-27 | Add company input audit and flag public-anchor extension endpoints | Public anchor existence does not make OpenAI 12GW or Anthropic 7GW a disclosed value. | FACT_OPENAI_STARGATE_10GW; FACT_ANTHROPIC_AWS_5GW | implemented in `02c_fact_vs_assumption_audit` |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
- OpenAI 12GW and Anthropic 7GW endpoints are extension scenarios beyond their registered public anchors; they must not be described as confirmed company figures.
