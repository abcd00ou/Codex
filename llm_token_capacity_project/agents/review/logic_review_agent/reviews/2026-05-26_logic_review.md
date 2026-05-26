# Logic Review: 2026-05-26

## Scope

- Artifacts reviewed:
  - `tools/generate_llm_token_capacity_report.py`
  - `outputs/reports/llm_token_capacity_2026_2030.json`
  - `outputs/reports/llm_token_capacity_2026_2030.xlsx`
  - `outputs/reports/llm_token_supply_constraints_by_compute_capacity_en_2026_2030.pptx`
  - A01, A02, A04, A08, A09, A10 and A11 assumption agents
- Scenario: Bear/Base/Bull
- Reviewer: Logic Review Agent

## Overall Status

`major`

No formula, unit, mix-sum, capacity-boundary or PPT package blocker was found after the evidence-trace update. The forecast is now auditable at company-year-scenario-metric level, including capacity classification, AI allocation rationale, accelerator mix bridge, tokens/MW derivation and utilization rationale. Status remains `major` because operated accelerator mix, company-level AI workload allocation and sustained utilization remain scenario values until denominated production disclosures replace them.

## Automated Review Result

| Check Area | Result |
|---|---|
| Scenario forecast rows | 180 |
| Number-trace rows | 4,680, or 26 numeric metrics per forecast row |
| Generator validation | PASS |
| Accelerator shares sum to 100% | PASS |
| tokens/MW bridge reconstruction | PASS |
| Assumption agent validation | PASS, 11 expected agents present |
| PPTX package quality | PASS, 12 slides, 7 charts, no placeholder/media/package errors |

## Blockers

| ID | Area | Finding | Evidence | Required Fix | Owner |
|---|---|---|---|---|---|
| none | none | No blocker found. | Generator validation, agent validator and PPTX package QA passed. | n/a | n/a |

## Major Findings

| ID | Area | Finding | Impact | Recommended Fix | Owner |
|---|---|---|---|---|---|
| M01 | Accelerator fleet allocation | Official sources support Maia, TPU/Ironwood, MTIA and Trainium platform direction, but not the modeled GPU/purpose-built production serving percentages. | Company tokens/MW and rank order respond to an allocation scenario, not measured fleet telemetry. | Replace A11 percentages when operated accelerator-hours, rack allocation, traffic routing or an explicit denominator is disclosed. | A11 |
| M02 | AI workload share | Platform purpose is sourced, while exact `ai_workload_share` remains company-specific scenario allocation. | AI IT GW may change materially if general cloud, ranking/recommendation or non-LLM loads occupy more of the active envelope. | Seek capacity-by-workload disclosure or constrain with product-serving evidence. | A04 |
| M03 | Utilization | `utilization` is correctly defined as realized output fraction, but provider-specific SLO/reserve telemetry is not public. | Sustained token output remains sensitive to operational haircut assumptions. | Build workload-class sensitivity using comparable output-token, TTFT/TPOT and availability constraints. | A09 |

## Formula And Unit Review

- `active_power_gw = min(contracted_power_gw, modeled_operationally_deployed_power_gw)`: pass; active power is capped and the source/estimate boundary is visible in `02b_number_trace`.
- `it_load_gw = active_power_gw / pue`: pass; PUE is applied once.
- `ai_it_load_gw = it_load_gw * ai_workload_share`: pass; allocation rationale is traceable per company.
- `accelerator_mix_factor = gpu_share * 1.0 + purpose_built_share * purpose_built_relative_efficiency_factor`: pass; share sum and bridge reconstruction are validated.
- `tokens/day = inference_gw * 1000 * tokens/sec/MW * utilization * 86400`: pass; generated output token headline is unchanged in definition.
- `training_tokens_processed_per_day`: separately traced as a proxy/reference metric; it is not combined with commercial inference output.

## Benchmark Mapping Review

- InferenceX remains a benchmark/proxy calibration layer and is not used as company production telemetry.
- Numeric accelerator fleet shares are not inferred from InferenceX rows.
- Utilization is not treated as powered-on capacity or peak benchmark throughput.

## Attribution Review

- Microsoft/OpenAI: capacity and token-owner attribution remains explicitly separated through A10.
- Anthropic hosting: Trainium/Rainier infrastructure is attributed to Claude serving capacity assumptions, not listed as AWS model-owner output.
- China model owners: platform facts and scenario labels follow the same logic; disclosure depth does not change formulas.

## Assumption Agent Routing

| Agent | Required Update | Priority |
|---|---|---|
| A04_ai_workload_share | Continue replacing scenario shares with workload denominators if disclosed. | high |
| A08_tokens_per_second_per_mw | Calibrate bridge factors with comparable generated-output benchmark profiles. | high |
| A09_utilization | Develop workload/SLO-specific realized-output haircut table. | high |
| A11_gpu_asic_mix | Track provider serving fleet disclosures and replace scenario shares. | high |
| orchestrator | Do not promote scenario allocation values as disclosed production facts. | high |

## Next Review Trigger

- operated fleet mix disclosure
- AI workload allocation disclosure
- comparable generated-output benchmark mapping
- attribution rule change
- executive deck refresh
