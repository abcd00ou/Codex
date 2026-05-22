# Logic Review: 2026-05-20

## Scope

- Artifacts reviewed:
  - `tools/generate_llm_token_capacity_report.py`
  - `outputs/reports/llm_token_capacity_2026_2030.json`
  - `outputs/reports/llm_token_supply_constraints_by_compute_capacity_en_2026_2030.pptx`
  - `agents/review/logic_review_agent/checklist.md`
- Scenario: Base/Bear/Bull plus Grid-Constrained / Efficiency-Upside sanity check
- Reviewer: Logic Review Agent

## Overall Status

`major`

No blocker was found in the current formula chain, unit conversion, scenario monotonicity, or PPT token-definition wording. The model is internally consistent under its stated assumptions. The remaining issues are major because they affect how strongly the output should be interpreted: InferenceX-to-production mapping, utilization haircut, inference/training split evidence, and Microsoft/OpenAI attribution should continue to be treated as review priorities before coefficient changes are promoted.

## Automated Review Result

| Check Area | Result |
|---|---|
| Scenario rows reviewed | 180 |
| Base forecast rows reviewed | 45 |
| Formula/unit failures | 0 |
| Bear/Base/Bull monotonicity failures | 0 |
| PPT Hangul count | 0 |
| PPT required topic terms | present |
| Source/assumption IDs on Base rows | present |

## Blockers

| ID | Area | Finding | Evidence | Required Fix | Owner |
|---|---|---|---|---|---|
| none | none | No blocker found. | Automated LR01-LR05, LR20, LR24, LR26 checks passed. | n/a | n/a |

## Major Findings

| ID | Area | Finding | Impact | Recommended Fix | Owner |
|---|---|---|---|---|---|
| M01 | Benchmark mapping | InferenceX rows are normalized and available, but they are not yet mapped into company/model-family production coefficient bands by comparable ISL/OSL, precision, GPU, latency, and workload class. | `tokens_per_second_per_mw` remains a benchmark-calibrated proxy rather than a production-derived coefficient. | Build an A08 mapping table from InferenceX rows to model-family bands, including output-token throughput, total processed throughput, TTFT/TPOT, precision, and benchmark-to-production haircut. | A08/A09 |
| M02 | Utilization haircut | Base utilization uses scenario bands and validation caps, but production utilization is not yet tied to provider-specific SLO headroom, failover reserve, traffic burstiness, or product mix. | Token supply may be overstated if peak serving availability is closer to reserve-heavy operation. | Add A09 utilization profiles by workload class: chat, coding, agentic/RAG, batch inference, and enterprise API. | A09 |
| M03 | Inference/training split | 2026 inference share above 60% appears only in Bull weighted scenario and one Base company row; the model correctly labels inference share as scenario, but provider-specific evidence remains limited. | Slide interpretation must keep inference share as a modeled allocation variable, not disclosed company fact. | A05/A06 should maintain a source table for product traffic, training cadence, model release cadence, and inference fleet disclosures. | A05/A06 |
| M04 | Attribution | Microsoft/OpenAI separation is encoded as an assumption, but it remains a high-impact attribution rule because Copilot, Azure hosting, and OpenAI model-owner tokens can overlap conceptually. | Provider ranking and supply-constraint interpretation can shift if attribution logic changes. | Add a dedicated A10 attribution ledger for OpenAI model-owner tokens, Microsoft customer-facing Copilot serving, and Azure-hosted third-party model capacity. | A10 |

## Minor Findings

| ID | Area | Finding | Recommended Fix | Owner |
|---|---|---|---|---|
| m01 | PPT traceability | PPT is clean and English-only, but it intentionally does not show derivation type or source IDs on every slide. | Keep the workbook as the drill-down artifact and mention that all chart numbers come from Base scenario generated output tokens. | PPT/orchestrator |
| m02 | Time-series explanation | The new 2026-2030 provider trajectory slides are useful, but they should be read as same-scenario comparisons, not disclosed annual production telemetry. | Keep the slide subtitle explicit that comparisons are Base scenario model outputs. | PPT |
| m03 | Closed model proxies | Closed frontier model proxy bands are separated from facts, but downstream readers may still anchor on exact table values. | Keep proxy/band language in methodology and avoid precise parameter counts in slide copy. | A07/PPT |

## Formula And Unit Review

- `it_load_gw = active_power_gw / pue`: pass. PUE is applied once in the generator.
- `ai_it_load_gw = it_load_gw * ai_workload_share`: pass. Non-AI IT load is not converted into tokens.
- `inference_gw = ai_it_load_gw * inference_power_share`: pass. Training and inference shares sum to 1.0 within tolerance.
- `tokens/day = inference_gw * 1000 * tokens/sec/MW * utilization * 86400`: pass. Automated recomputation of scenario rows found no formula mismatch.

## Token Definition Review

- Headline generated output token: pass. PPT and formula use generated output token supply as the headline.
- Processed token separation: pass with caveat. InferenceX total processed throughput is documented as benchmark/load-shape diagnostic rather than direct headline token supply.
- Training token separation: pass. Training tokens are kept as a separate sanity/reference metric.
- Billable token separation: pass. Billable API tokens are not used as the capacity headline.

## Benchmark Mapping Review

- InferenceX output throughput mapping: major follow-up required. The normalized dump is available, but A08 still needs a comparable-row mapping from benchmark output throughput to model-owner coefficient bands.
- InferenceX total processed throughput mapping: pass. The methodology separates total processed throughput from generated output tokens.
- J/token sanity layer: pass as a sanity layer, not a production fact.
- Production haircut and utilization: major follow-up required. A09 should define workload-specific haircuts tied to SLO and reserve assumptions.

## Attribution Review

- Microsoft/OpenAI: major follow-up required. The attribution rule exists and validation marks it as separated, but it should remain a recurring audit item.
- Anthropic hosting: pass. Anthropic is included as a model-owner row and hosting is not treated as a separate core model-owner row.
- Cloud host vs model owner: pass with recurring review. Hosting providers are outside core rows unless attribution is explicitly defined.
- China model-owner handling: pass. Lower disclosure transparency changes review priority and confidence posture, not the math structure.

## Scenario Review

- Bear/Base/Bull monotonicity: pass. Total and company-level token supply are monotonic for all reviewed years.
- Deployment speed: pass. Active power is capped at contracted power.
- Inference share: pass with caveat. It remains a scenario variable; 2026 >60% inference should not be presented as a company-level fact.
- MoE optimization: pass as scenario logic. DeepSeek and Alibaba receive MoE optimization only through scenario multiplier logic.
- Utilization: pass as formula logic; major follow-up remains on provider-specific production utilization evidence.

## PPT / Executive Output Review

- Headline number consistency: pass. PPT title and charts refer to generated output token supply.
- Chart/table wording: pass. Provider time-series and 2030 snapshot labels are scenario/model output language rather than production telemetry.
- Claims requiring softer language: none found as blockers. Continue to avoid saying the forecast is actual production token volume.

## Assumption Agent Routing

| Agent | Required Update | Priority |
|---|---|---|
| A05_inference_power_share | Add provider-specific evidence table for inference/training split over 2026-2030. | high |
| A06_training_power_share | Mirror A05 and track training cadence/model-release evidence. | high |
| A08_tokens_per_second_per_mw | Build benchmark-to-production mapping from InferenceX rows to company/model-family bands. | high |
| A09_utilization | Define workload-specific production haircut and SLO reserve profiles. | high |
| A10_attribution_rule | Maintain Microsoft/OpenAI/Azure and Anthropic hosting attribution ledger. | high |
| orchestrator | Treat this review as non-blocking but major; require review update before coefficient promotion. | high |

## Next Review Trigger

- coefficient change
- new benchmark ingestion
- attribution rule change
- executive deck refresh
- any claim that uses provider-specific inference share as fact
