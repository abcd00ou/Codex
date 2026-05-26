# Evidence: A10 attribution_rule

This file stores reviewed evidence for `attribution_rule`.

## Evidence Table

| evidence_id | source_id | date | evidence_class | exact_claim_or_number | unit | model_field_impacted | confidence | reviewer |
|---|---|---|---|---|---|---|---|---|
| A10_E000 | baseline | 2026-05-15 | Scenario | Initial agent created from existing assumption textbook | n/a | attribution_rule | Low-Medium | Codex |
| A10_E001 | SRC_OPENAI_STARGATE_PROGRESS | 2025-09-23 | Fact anchor | Stargate capacity supports OpenAI model-owner capacity attribution; hosting partners are infrastructure, not separate model owners | GW / infrastructure | attribution_rule | Medium-High | Codex |
| A10_E002 | SRC_AWS_RAINIER_ACTIVE | 2025-10-29 | Fact anchor | Project Rainier is built for Anthropic workloads; AWS hardware capacity is attributed to Claude model output in owner-based forecasting | infrastructure | attribution_rule | Medium-High | Codex |
| A10_E003 | SRC_MS_MAIA200 | 2026-01-26 | Fact anchor | Maia serves Microsoft products and models; Microsoft-owned routing must remain separated from OpenAI model output in Copilot contexts | infrastructure | attribution_rule | Medium | Codex |

## Review Notes

- Add only source-reviewed evidence here.
- Do not paste copyrighted report text. Summarize claim, number, unit, and implication.
- Keep fact and interpretation separate.
- Highest recurring audit priority: avoid double counting Microsoft customer-facing serving burden and OpenAI model-owner output.
