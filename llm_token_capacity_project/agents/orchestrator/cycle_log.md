# Orchestrator Cycle Log

| Cycle | Date | Scope | Decision | Open Flags |
|---|---|---|---|---|
| 0 | 2026-05-15 | Initial assumption-agent system setup | Agent structure created | Need first learning cycle for A01/A02 |
| 1 | 2026-05-18 | Agent learning expansion | Added 2026 energy/inference serving/rack-scale source curriculum and agent expansion pack | Need evidence promotion into individual agent evidence.md files |
| 2 | 2026-05-18 | A08/A09 first learning cycle | Promoted 2026 inference energy and serving-disaggregation sources as proxy/mechanism evidence; no Base numeric change yet | Need energy sanity layer and SLO/utilization sensitivity table |
| 3 | 2026-05-19 | InferenceX ingestion layer | Added public repo/release metadata pipeline and workbook schema sheets; no Base numeric change yet | Need full DB dump/CSV normalization and A08/A09 review before coefficient updates |
| 4 | 2026-05-19 | InferenceX full dump normalization | Verified 2026-05-11 dump digest and normalized 72,091 benchmark rows, 298 metric profile groups, 1,048 accuracy eval rows, run stats and availability tables | Need A08/A09 mapping from benchmark groups to Base/Bull/Bear coefficient bands; Base remains unchanged |
| 5 | 2026-05-20 | Logic review agent first formal review | No blockers found; formula/unit checks, scenario monotonicity, PPT token wording, source/assumption IDs passed | Major follow-ups remain for A08/A09 benchmark-to-production mapping, A05/A06 split evidence, and A10 attribution ledger |
| 6 | 2026-05-26 | Company-level numeric trace and accelerator-mix bridge | Added company-year-field rationale trace, formalized active vs capacity ceiling, added A11 GPU/ASIC mix agent and bridged numeric mix into tokens/MW | Replace scenario mix/utilization/AI-workload shares with provider telemetry when disclosed |
| 7 | 2026-05-27 | Confirmed-value vs modeled-value disclosure layer | Added company-by-metric fact/assumption audit; OpenAI 12GW and Anthropic 7GW endpoints explicitly classified as public-anchor extension scenarios | Source-line sign-off required for each numeric fact anchor before executive publication |
| 8 | 2026-05-27 | Simple core token-capacity formula | Headline token output now uses operational deployment, PUE, AI/inference allocation and fixed-condition InferenceX output TPS/MW only; utilization/MoE/software/architecture multipliers removed from headline | Replace selected proxy rows with matched production telemetry when disclosed |
| 9 | 2026-05-27 | Executive artifact simplification | Excel now exposes only Logic, Benchmark Input, Inputs, Calculation, Output and Checks; derived cells are formulas and research/audit detail stays in project records | Keep formula workbook synchronized with internal evidence ledger |
| 10 | 2026-05-27 | Commercial-serving TPS/MW correction and aggressive upside view | Separated InferenceX public reference from company workload-fit assumptions; added formula-driven Bull and public-reference ceiling view | Replace fit factors with matched production/service benchmarks when disclosed |

## Open Flags

- A01/A02: contracted vs active power conversion needs source-by-source review.
- A05/A06: 2026 inference share must remain scenario, not fact.
- A08/A09: 보고용 `01_Benchmark_Input`에서 InferenceX public reference와 commercial workload fit factor를 분리하고, production utilization은 telemetry 확보 전까지 내부 sensitivity로만 유지.
- A10: OpenAI/Microsoft and Anthropic/AWS attribution rules need recurring audit.
- AI 2027: aggressive capability/adoption scenario should be handled as a separate stress scenario, not folded into Base.
- 2026 serving sources: IBM PD disaggregation, Joule inference energy, and 2026 arXiv serving papers should be reviewed by A08/A09 before changing tokens/MW or utilization.
- InferenceX: full dump normalized; fixed B200/single_turn/ISL-OSL 1024/1024 output TPS/MW p50 proxy is used transparently in headline while remaining non-production telemetry.
- A11: numeric GPU/purpose-built accelerator mix is now explicit but remains scenario unless operated fleet-share disclosure is found.
- Fact-vs-assumption audit: do not call OpenAI 12GW or Anthropic 7GW endpoints confirmed values unless new official disclosure replaces the current anchor gap.
