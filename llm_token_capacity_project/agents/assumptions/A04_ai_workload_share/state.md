# State: A04 ai_workload_share

| Field | Value |
|---|---|
| agent_id | A04 |
| owned_field | ai_workload_share |
| current_starting_band | AI-dedicated 80-95%; mixed cloud 50-80% |
| confidence | Low-Medium unless dedicated cluster disclosed |
| last_reviewed | 2026-05-26 |
| status | Company-specific rationale added; numeric share remains scenario without telemetry |

## Current Assumption

AI-dedicated 80-95%; mixed cloud 50-80%

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-26 | Add company-specific `ai_workload_share` rationale to workbook number trace; retain values as scenario allocation | Official platform evidence establishes AI-focused capacity direction but does not disclose the fraction of IT load assigned to model-owner AI workloads. | SRC_MS_MAIA200; SRC_GOOGLE_IRONWOOD; SRC_META_MTIA_GENAI_2026; SRC_AWS_RAINIER_ACTIVE | implemented as explanation; telemetry still open |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
- Do not interpret an AI-oriented site or accelerator announcement as 100% model-owner LLM load.
