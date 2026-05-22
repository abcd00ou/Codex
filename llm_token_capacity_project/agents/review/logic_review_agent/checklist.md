# Logic Review Checklist

Use this checklist before publishing a new simulation cycle or presentation deck.

## 1. Unit And Formula Integrity

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR01 | Does every power conversion preserve units from GW to MW to joules/day? | `inference_gw * 1000 * tokens/sec/MW * utilization * 86400` is dimensionally valid. | blocker |
| LR02 | Is `active_power_gw <= contracted_power_gw` for every company-year-scenario? | No active power exceeds contracted/planned capacity. | blocker |
| LR03 | Do `training_power_share + inference_power_share = 100%` after rounding tolerance? | Sum equals 1.0 within validation tolerance. | blocker |
| LR04 | Is PUE applied only once? | `it_load_gw = active_power_gw / pue`; no second PUE adjustment later. | blocker |
| LR05 | Is AI workload share separate from data-center IT load? | `ai_it_load_gw = it_load_gw * ai_workload_share`; non-AI IT is not converted into tokens. | major |

## 2. Token Definition Integrity

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR06 | Is headline token supply generated output tokens only? | Headline `inference_tokens_per_day` excludes input, billable, cache, and training tokens. | blocker |
| LR07 | Are processed-token benchmark metrics kept separate? | InferenceX total `tok_s_mw` is not directly used as headline output token supply. | blocker |
| LR08 | Are training tokens separated from commercial inference output tokens? | `training_tokens_processed_per_day` is sanity/reference only. | blocker |
| LR09 | Are ISL/OSL assumptions visible when benchmark rows are used? | Benchmark mapping records input length, output length, precision, and latency context where available. | major |

## 3. LLM Architecture And Serving Logic

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR10 | Are MoE models using active parameters for per-token compute sanity checks? | Total and active parameters are separated; active parameters drive FLOPs/token sanity logic. | blocker |
| LR11 | Are closed frontier models shown as bands or proxies? | No closed model uses a fake precise parameter count as fact. | major |
| LR12 | Does tokens/MW account for production overhead? | Utilization or haircut reflects SLO, batching, routing, reserve capacity, and failover. | major |
| LR13 | Does the forecast avoid peak-throughput-to-annual-average conversion errors? | Peak benchmark numbers are not treated as sustained fleet average without haircut. | blocker |
| LR14 | Is latency relevant to the benchmark mapping? | TTFT/TPOT or SLO caveat is included when using InferenceX performance data. | major |

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
| LR19 | Do Bear/Base/Bull scenarios move the correct variables? | Deployment, inference share, tokens/MW, MoE optimization, and utilization move transparently. | major |
| LR20 | Are scenario multipliers monotonic where expected? | Bear <= Base <= Bull for total token capacity unless a documented exception exists. | major |
| LR21 | Is 2026 inference share above 60% treated as scenario, not fact? | No company-level disclosure is implied unless source exists. | blocker |
| LR22 | Does sensitivity isolate one variable at a time where claimed? | A sensitivity table does not silently combine multiple variable changes. | major |

## 6. Executive Output Safety

| Check ID | Question | Pass Criteria | Severity |
|---|---|---|---|
| LR23 | Does PPT wording match derivation type? | Scenario/estimate/proxy values are not worded as disclosed production facts. | major |
| LR24 | Are charts and tables using the same token definition? | PPT, Excel, JSON, and Markdown all use generated output tokens for headline supply. | blocker |
| LR25 | Are company rankings based on the same year and scenario? | Ranking labels specify Base 2030 or the applicable scenario/year. | major |
| LR26 | Are source paths available for every number that might be challenged? | Workbook/source registry can trace the number to source IDs or assumption IDs. | major |

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
- A01/A02/.../A10/orchestrator/generator/PPT

next_review_trigger:
- coefficient change
- new benchmark ingestion
- attribution rule change
- executive deck refresh
```
