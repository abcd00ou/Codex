# Evidence: A09 utilization

This file stores reviewed evidence for `utilization`.

## Evidence Table

| evidence_id | source_id | date | evidence_class | exact_claim_or_number | unit | model_field_impacted | confidence | reviewer |
|---|---|---|---|---|---|---|---|---|
| A09_E000 | baseline | 2026-05-15 | Scenario | Initial agent created from existing assumption textbook | n/a | utilization | Low-Medium | Codex |
| A09_E001 | WATCH_INFERENCEX | 2026-05-15 | Proxy | Candidate benchmark/context source for utilization, batching and benchmark-to-production gap; not yet promoted to numeric model input | n/a | utilization | Low-Medium | Codex |
| A09_E002 | IBM_PD_2026 | 2026-05-18 | Mechanism | Prefill-decode disaggregation can change both performance and energy; utilization assumptions must account for workload shape and allocation overhead | n/a | utilization | Medium | Codex |
| A09_E003 | ARXIV_SLO_PD_2603 | 2026-05-18 | Mechanism | SLO-aware resource allocation for prefill/decode disaggregated inference implies utilization is constrained by TTFT/TPOT and SLA reserve, not just available GPU capacity | n/a | utilization | Low-Medium | Codex |
| A09_E004 | ARXIV_PREFILL_SERVICE_2604 | 2026-05-18 | Scenario | Prefill-as-a-service and cross-datacenter prefill/KV movement imply future agentic workloads may alter utilization through network and placement constraints | n/a | utilization | Low-Medium | Codex |
| A09_E005 | INFERENCEX_DUMP_2026_05_11 | 2026-05-19 | Proxy | Full InferenceX-app release dump normalized: benchmark rows include concurrency, ISL/OSL, p99 TTFT, p99 TPOT, p99 end-to-end latency, run stats and availability rows for serving-stack comparability | concurrency, TTFT/TPOT latency, availability | utilization | Medium | Codex |

## Review Notes

- Add only source-reviewed evidence here.
- Do not paste copyrighted report text. Summarize claim, number, unit, and implication.
- Keep fact and interpretation separate.

## Cycle 1 Interpretation

- A09 should keep Base utilization band unchanged until benchmark-to-production mapping is explicit.
- 2026 serving papers support adding utilization caveats: TTFT/TPOT SLO, P/D allocation, peak reserve, network placement and agentic workload shape.
- Future Bull scenario may improve utilization through better scheduling, while agentic long-context workloads may also increase reserve needs.
- InferenceX can calibrate strict-SLO versus batchable profiles, but observed benchmark concurrency is not the same as fleet-wide annual utilization.
