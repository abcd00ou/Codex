# Evidence: A01 contracted_power_gw

This file stores reviewed evidence for `contracted_power_gw`.

## Evidence Table

| evidence_id | source_id | date | evidence_class | exact_claim_or_number | unit | model_field_impacted | confidence | reviewer |
|---|---|---|---|---|---|---|---|---|
| A01_E000 | baseline | 2026-05-15 | Scenario | Initial agent created from existing assumption textbook | n/a | contracted_power_gw | Low-Medium | Codex |
| A01_E001 | SRC_OPENAI_STARGATE_ORACLE | 2025-07-22 | Fact anchor | OpenAI and Oracle announced additional datacenter capacity direction; used as an upper-bound capacity anchor only | GW | contracted_power_gw | Medium-High | Codex |
| A01_E002 | SRC_OPENAI_STARGATE_PROGRESS | 2025-09-23 | Fact anchor | OpenAI stated nearly 7 GW across new sites and more than 10 GW commitment; used to bound 2030 envelope | GW planned/committed | contracted_power_gw | Medium-High | Codex |
| A01_E003 | SRC_ANTHROPIC_AMAZON_COMPUTE | 2025-2026 | Fact anchor | Anthropic/AWS hosted capacity direction provides an Anthropic model-owner ceiling anchor, not active inference GW | GW class | contracted_power_gw | Medium | Codex |

## Review Notes

- Add only source-reviewed evidence here.
- Do not paste copyrighted report text. Summarize claim, number, unit, and implication.
- Keep fact and interpretation separate.
- Workbook terminology now means: sourced committed/planned ceiling when disclosed, otherwise explicitly labeled scenario capacity envelope.
