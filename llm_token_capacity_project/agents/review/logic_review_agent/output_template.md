# Logic Review Output Template

Copy this file into a dated review note when a formal review is run.

```markdown
# Logic Review: YYYY-MM-DD

## Scope

- Artifacts reviewed:
- Scenario:
- Reviewer:

## Overall Status

`pass | minor | major | blocker`

## Executive Summary

One paragraph explaining whether the simulation is safe to present and what must be fixed first.

## Blockers

| ID | Area | Finding | Evidence | Required Fix | Owner |
|---|---|---|---|---|---|
| none | none | No blocker found. | n/a | n/a | n/a |

## Major Findings

| ID | Area | Finding | Impact | Recommended Fix | Owner |
|---|---|---|---|---|---|

## Minor Findings

| ID | Area | Finding | Recommended Fix | Owner |
|---|---|---|---|---|

## Formula And Unit Review

- `it_load_gw = active_power_gw / pue`:
- `ai_it_load_gw = it_load_gw * ai_workload_share`:
- `inference_gw = ai_it_load_gw * inference_power_share`:
- `active_power_gw = contracted_power_gw * operational_deployment_share`:
- `tokens/day = inference_gw * 1000 * selected output tokens/sec/MW * 86400`:

## Token Definition Review

- Headline generated output token:
- Processed token separation:
- Training token separation:
- Billable token separation:

## Benchmark Mapping Review

- InferenceX output throughput mapping:
- InferenceX total processed throughput mapping:
- J/token sanity layer:
- Production haircut and utilization sensitivity only:

## Attribution Review

- Microsoft/OpenAI:
- Anthropic hosting:
- Cloud host vs model owner:
- China model-owner handling:

## Scenario Review

- Bear/Base/Bull monotonicity:
- Deployment speed:
- Inference share:
- Selected TPS/MW proxy mapping:
- Hidden headline multiplier exclusion:

## PPT / Executive Output Review

- Headline number consistency:
- Chart/table wording:
- Claims requiring softer language:

## Assumption Agent Routing

| Agent | Required Update | Priority |
|---|---|---|

## Next Review Trigger

- coefficient change
- new benchmark ingestion
- attribution rule change
- executive deck refresh
```
