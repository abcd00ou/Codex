# Logic Review Checklist

Use this checklist before publishing a new simulation cycle or presentation deck.

## 1. Unit And Formula Integrity

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR01 | Does every power conversion preserve units from GW to MW to generated output tokens/day? | `inference_gw * 1000 * selected output tokens/sec/MW * 86400` is dimensionally valid. | blocker |
| LR02 | Is `active_power_gw <= contracted_power_gw` for every company-year-scenario? | No active power exceeds contracted/planned capacity. | blocker |
| LR03 | Do `training_power_share + inference_power_share = 100%` after rounding tolerance? | Sum equals 1.0 within validation tolerance. | blocker |
| LR04 | Is PUE applied only once? | `it_load_gw = active_power_gw / pue`; no second PUE adjustment later. | blocker |
| LR05 | Is AI workload share separate from data-center IT load? | `ai_it_load_gw = it_load_gw * ai_workload_share`; non-AI IT is not converted into tokens. | major |

## 2. Token Definition Integrity

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR06 | Is headline token supply generated output tokens only? | Headline `inference_tokens_per_day` excludes input, billable, cache, and training tokens. | blocker |
| LR07 | Are processed-token benchmark metrics kept separate? | InferenceX total `tok_s_mw` is not directly used as headline output token supply. | blocker |
| LR08 | Are training tokens separated from commercial inference output tokens? | Headline formula converts only inference GW into generated output tokens. | blocker |
| LR09 | Are ISL/OSL assumptions visible when benchmark rows are used? | Benchmark mapping records input length, output length, precision, and latency context where available. | major |

## 3. LLM Architecture And Serving Logic

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR10 | Are MoE models using active parameters for per-token compute sanity checks? | Total and active parameters are separated; active parameters drive FLOPs/token sanity logic. | blocker |
| LR11 | Are closed frontier models shown as bands or proxies? | No closed model uses a fake precise parameter count as fact. | major |
| LR12 | Does headline tokens/MW avoid unsupported production adjustments? | Output TPS/MW is a named benchmark proxy; production overhead remains supplemental sensitivity, not a hidden multiplier. | major |
| LR13 | Does the forecast label benchmark-derived capacity correctly? | Selected benchmark output TPS/MW is not worded as observed commercial token volume. | blocker |
| LR14 | Is latency relevant to the benchmark mapping? | TTFT/TPOT or SLO caveat is included when using InferenceX performance data. | major |
| LR27 | Does numeric accelerator mix separate platform presence facts from operated fleet-share scenarios? | Executive Excel shows mix as input only; A11 internal record keeps reason and replacement evidence. | blocker |
| LR28 | Can headline TPS/MW be reconstructed through the simple benchmark bridge? | `reference_serving_tps_per_mw = inferencex_reference_tps_per_mw * commercial_workload_fit_factor`, then GPU/purpose-built weighting, with no unsupported hardware uplift. | blocker |
| LR30 | Are hidden multipliers excluded from the headline formula? | Utilization, MoE, architecture and software CAGR do not multiply headline generated output token supply. | blocker |

## 4. Capacity Attribution

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR15 | Is capacity attributed to the model owner, not just the cloud host? | OpenAI, Microsoft, Anthropic, Google, Meta, xAI, DeepSeek, Alibaba, Tencent rules are explicit. | blocker |
| LR16 | Is Microsoft/OpenAI overlap handled explicitly? | Copilot serving tokens, OpenAI model-owner tokens, and Azure-hosted third-party tokens are separated. | blocker |
| LR17 | Are Oracle/CoreWeave/AWS hosting references kept out of core model-owner rows unless attribution is defined? | Hosting providers appear only as capacity sources or sensitivity layers. | major |
| LR18 | Are China model owners treated consistently despite lower disclosure transparency? | Lower transparency changes confidence, not the math structure. | major |

## 5. Scenario And Sensitivity Logic

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR19 | Do Bear/Base/Bull scenarios move the correct variables? | Operational deployment, inference share and explicit commercial workload fit move transparently; public reference itself is unchanged. | major |
| LR20 | Are scenario multipliers monotonic where expected? | Bear <= Base <= Bull for total token capacity unless a documented exception exists. | major |
| LR21 | Is 2026 inference share above 60% treated as scenario, not fact? | No company-level disclosure is implied unless source exists. | blocker |
| LR22 | Does sensitivity isolate one variable at a time where claimed? | A sensitivity table does not silently combine multiple variable changes. | major |

## 6. Executive Output Safety

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR23 | Does PPT wording match derivation type? | Scenario/estimate/proxy values are not worded as disclosed production facts. | major |
| LR24 | Are charts and tables using the same token definition? | PPT, Excel, JSON, and Markdown all use generated output tokens for headline supply. | blocker |
| LR25 | Are company rankings based on the same year and scenario? | Ranking labels specify Base 2030 or the applicable scenario/year. | major |
| LR26 | Are source paths available for every input that might be challenged? | Project Markdown/agent records trace source IDs and replacement paths without cluttering the executive workbook. | major |
| LR29 | Are public anchors separated from modeled endpoints internally? | Agent audit records nine core metric rows per company and labels public-anchor extension scenarios explicitly; executive workbook presents inputs as inputs only. | blocker |
| LR31 | Is the executive workbook formula-driven and logic-only? | Visible tabs are `00_Logic` through `06_Aggressive_View`; all derived outputs are cell formulas. | blocker |
| LR32 | Is the aggressive upside view separated from Base? | Bull commercial case and 100% public-reference ceiling are separately labeled and formula-driven; ceiling is not presented as production fact. | blocker |

## Review Result Template

```text
review_date:
reviewer:
artifact_scope:
overall_status: pass | minor | major | blocker

blockers:
- none

major_findings:
- none

minor_findings:
- none

recommended_owner:
- A01/A02/.../A11/orchestrator/generator/PPT

next_review_trigger:
- coefficient change
- new benchmark ingestion
- attribution rule change
- executive deck refresh
```
