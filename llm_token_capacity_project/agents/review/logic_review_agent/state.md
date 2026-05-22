# State: Logic Review Agent

| Field | Value |
|---|---|
| agent_id | LR01_logic_review_agent |
| role | principal LLM infrastructure and model-serving logic reviewer |
| owned_field | cross-assumption review only; no direct coefficient ownership |
| current_scope | compute capacity -> inference GW -> generated output token supply simulation |
| confidence | Medium for structure review; Low for undisclosed company production telemetry |
| last_reviewed | 2026-05-20 |
| status | first formal review completed; no blockers, major follow-up items routed |

## Current Review Position

The current model structure is reviewable because it separates:

- contracted power from active power
- IT load from AI IT load
- inference power from training power
- generated output tokens from processed/billable/training tokens
- model-owner token attribution from hosting capacity
- benchmark/proxy layers from company production facts

The weakest logic areas remain:

1. mapping InferenceX benchmark rows into company-level sustained `tokens_per_second_per_mw`
2. Microsoft/OpenAI hosted/model-owner attribution under Copilot and Azure
3. company-specific inference/training split over time
4. production utilization and SLO headroom
5. closed frontier model active-parameter proxy bands

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-20 | Add Logic Review Agent as independent reviewer | The simulation now drives executive PPT conclusions and needs formula/unit/serving sanity review beyond assumption-specific agents. | internal-agent-system | implemented |
| 2026-05-20 | Require logic review before coefficient or attribution changes are promoted | Prevent benchmark-to-production overreach, double attribution, and token-definition confusion. | internal-agent-system | proposed - orchestrator adoption |

## Current Blocker Register

| ID | Area | Finding | Owner | Status |
|---|---|---|---|---|
| none | none | No blocker found in 2026-05-20 formal review. | logic_review_agent | closed |

## Latest Formal Review

| Field | Value |
|---|---|
| review_note | `agents/review/logic_review_agent/reviews/2026-05-20_logic_review.md` |
| overall_status | major |
| blocker_count | 0 |
| major_finding_count | 4 |
| minor_finding_count | 3 |
| automated_formula_failures | 0 |
| automated_scenario_monotonicity_failures | 0 |
| ppt_hangul_count | 0 |

## Open Review Questions

| ID | Question | Likely Owner | Priority |
|---|---|---|---|
| LRQ01 | Which InferenceX rows should map to output-token `tokens_per_second_per_mw` for each model family? | A08 | high |
| LRQ02 | What production haircut should be applied for SLO, failover, and uneven traffic? | A09 | high |
| LRQ03 | How should Microsoft Copilot tokens be separated from OpenAI model-owner tokens? | A10 | high |
| LRQ04 | What evidence can bound company-specific inference/training split from 2026 to 2030? | A05/A06 | high |
| LRQ05 | Which closed-model parameter proxy bands are defensible enough for FLOPs/token sanity checks? | A07 | medium |

## Downstream Impact Notes

- A blocker should stop PPT/Excel promotion until resolved or explicitly overridden by the orchestrator.
- A major finding should create an assumption-agent learning task before the next cycle.
- A minor finding can be documented in the review output and repaired in the next normal update.

## Next Formal Review Scope

Review the current Base/Bear/Bull simulation and the `Token Supply Constraints by LLM Provider` PPT for:

1. unit integrity
2. token definition consistency
3. attribution duplication
4. benchmark-to-production mapping
5. scenario monotonicity
6. executive chart wording
