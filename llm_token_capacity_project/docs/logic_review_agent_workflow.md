# Logic Review Agent Workflow

This document explains how to use the Logic Review Agent for the LLM token capacity simulation.

## Purpose

The Logic Review Agent is a high-skepticism reviewer for the model logic. It is designed to catch mistakes that can survive normal report generation:

- wrong unit conversion
- double-counted capacity
- benchmark metric mapped to the wrong token definition
- MoE active/total parameter confusion
- overconfident inference-share assumptions
- scenario multipliers that move the wrong variable
- PPT wording that makes an estimate sound like a disclosed fact

## When To Run

Run a logic review before:

1. changing `tools/generate_llm_token_capacity_report.py`
2. changing any A01-A10 assumption state
3. ingesting a new InferenceX dump or benchmark source
4. changing Microsoft/OpenAI/Anthropic/cloud-host attribution
5. publishing a new PPT or Excel to executives

## Inputs

The agent should read:

- `agents/review/logic_review_agent/README.md`
- `agents/review/logic_review_agent/checklist.md`
- `agents/review/logic_review_agent/prompt.md`
- `docs/methodology.md`
- `docs/inferencex_ingestion_plan.md`
- `docs/hallucination_checklist.md`
- `tools/generate_llm_token_capacity_report.py`
- `outputs/reports/llm_token_capacity_2026_2030.json`
- `outputs/reports/llm_token_capacity_2026_2030.xlsx`
- `outputs/reports/llm_token_supply_constraints_by_compute_capacity_en_2026_2030.pptx`

## Review Procedure

```text
1. Check formula and unit integrity.
2. Check token definition consistency.
3. Check model architecture and serving logic.
4. Check capacity attribution.
5. Check scenario and sensitivity logic.
6. Check executive output wording.
7. Route findings to A01-A10, orchestrator, generator, or PPT.
```

## Output

Create a dated review note from:

```text
agents/review/logic_review_agent/output_template.md
```

Recommended destination:

```text
llm_token_capacity_project/agents/review/logic_review_agent/reviews/YYYY-MM-DD_logic_review.md
```

## Decision Rules

| Status | Meaning | Report Action |
|---|---|---|
| pass | No material logic issue found | publish allowed |
| minor | Documentation or wording issue only | publish allowed after quick fix |
| major | Assumption or sensitivity issue affects interpretation | orchestrator approval required |
| blocker | formula, unit, attribution, or benchmark mapping issue affects headline math | do not publish |

## Minimum Review Questions

1. Does the power funnel preserve units from GW to tokens/day?
2. Is generated output token supply clearly separated from processed, billable, and training tokens?
3. Are InferenceX benchmark rows used as benchmark/proxy, not company production telemetry?
4. Are closed model parameters treated as bands or proxies?
5. Are MoE active parameters used where FLOPs/token sanity checks require active parameters?
6. Is Microsoft/OpenAI capacity attribution explicitly separated?
7. Do Bear/Base/Bull scenarios move only the variables they claim to move?
8. Are 2026-2030 time-series comparisons based on the same scenario and token definition?
9. Does the PPT state estimates as estimates and scenarios as scenarios?
10. Can every challenged number be traced to source IDs or assumption IDs?

## Validation Command

```bash
.venv/bin/python llm_token_capacity_project/tools/validate_assumption_agents.py
```

Expected result:

```json
{
  "status": "PASS",
  "review_agent": "present"
}
```
