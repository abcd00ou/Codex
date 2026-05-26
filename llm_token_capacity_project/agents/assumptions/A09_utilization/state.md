# State: A09 utilization

| Field | Value |
|---|---|
| agent_id | A09 |
| owned_field | utilization |
| current_starting_band | 2026 45-65%; 2030 60-80% |
| confidence | Low-Medium; production telemetry rarely public |
| last_reviewed | 2026-05-26 |
| status | Utilization meaning and company-specific rationale linked into workbook trace |

## Current Assumption

2026 45-65%; 2030 60-80%

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-15 | Initial state created | Agent system setup | none | baseline |
| 2026-05-18 | Keep Base utilization band unchanged; add explicit caveat that utilization is SLO/workload/placement constrained and not equal to accelerator occupancy | 2026 prefill-decode and SLO-aware allocation sources show realized utilization depends on latency objectives, disaggregation overhead, network placement and traffic shape. | A09_E002; A09_E003; A09_E004 | proposed - orchestrator review required |
| 2026-05-19 | Add InferenceX latency/concurrency/availability evidence layer; keep Base utilization unchanged | Dump rows can support strict-SLO vs batchable utilization profiles, but benchmark concurrency and success counts are not fleet average production utilization. | A09_E005 | implemented as evidence layer; no Base change |
| 2026-05-26 | Define utilization as realized-output fraction after SLO/reserve/traffic constraints and add company rationale | Installed inference power cannot be multiplied by peak benchmark throughput continuously. | A09_E002; A09_E003; A09_E005 | implemented in workbook trace and methodology |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.

## Cycle 1 Notes

- Keep 2026 45-65% and 2030 60-80% as Base learning band for now.
- Add future sensitivity for strict-SLO versus batchable workloads.
- Use `inferencex_benchmark_results.csv` for TTFT/TPOT and concurrency, and `inferencex_run_stats.csv`/`inferencex_availability.csv` for serving-stack coverage checks.
- Utilization is not a power-on ratio; it is the fraction of theoretical output-token capacity realized under latency, batch fill, failover and traffic-shape constraints.
