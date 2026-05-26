# Evidence: A02 active_power_gw

This file stores reviewed evidence for `active_power_gw`.

## Evidence Table

| evidence_id | source_id | date | evidence_class | exact_claim_or_number | unit | model_field_impacted | confidence | reviewer |
|---|---|---|---|---|---|---|---|---|
| A02_E000 | baseline | 2026-05-15 | Scenario | Initial agent created from existing assumption textbook | n/a | active_power_gw | Low-Medium | Codex |
| A02_E001 | SRC_OPENAI_STARGATE_PROGRESS | 2025-09-23 | Fact anchor | OpenAI announced new Stargate site capacity commitments; planned capacity is a ceiling rather than active serving power | GW planned/committed | contracted_power_gw -> active_power_gw | Medium-High | Codex |
| A02_E002 | SRC_AWS_RAINIER_ACTIVE | 2025-10-29 | Fact anchor | AWS activated Trainium2-based Project Rainier capacity for Anthropic; activation supports active-capacity direction but not inference allocation | accelerator cluster | active_power_gw | High | Codex |

## Review Notes

- Add only source-reviewed evidence here.
- Do not paste copyrighted report text. Summarize claim, number, unit, and implication.
- Keep fact and interpretation separate.
- Rule adopted 2026-05-26: `active_power_gw` must be less than or equal to `contracted_power_gw` and requires an operational deployment rationale.
