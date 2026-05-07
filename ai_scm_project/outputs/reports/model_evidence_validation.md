# AI SCM Model Evidence Validation

Generated: 2026-05-04T09:44:40

## Summary

- Total coefficients: 6
- Investment-grade candidates: 0
- Scenario-grade coefficients: 1
- Research-only coefficients: 5
- Blocking errors: 0
- Critical audit items: COEF_CAPEX_ACCELERATOR_SHARE, COEF_AVG_ACCELERATOR_ASP_USD, COEF_COWOS_WPM_PER_ACCELERATOR

## Coefficient Audit

| Coefficient | Confidence | Trust Label | Status | Priority | Sensitivity Range | Upgrade Path |
|---|---:|---|---|---|---|---|
| `COEF_CAPEX_AI_INFRA_SHARE` | 55% | scenario_grade | partially_supported | high | [0.45, 0.7] | Replace with company-quarter server/GPU/data-center/networking capex split from earnings transcripts and 10-Q cash-flow notes. Next: parse `data/sec_filings.json` filing URLs into company-quarter CapEx, segment revenue, PP&E, lease, inventory, and backlog line items. |
| `COEF_CAPEX_ACCELERATOR_SHARE` | 45% | research_only | derived_proxy | critical | [0.3, 0.6] | Infer from NVIDIA data center revenue, AMD data center GPU revenue, cloud capex timing, and estimated accelerator ASP mix. Next: parse `data/sec_filings.json` filing URLs into company-quarter CapEx, segment revenue, PP&E, lease, inventory, and backlog line items. |
| `COEF_AVG_ACCELERATOR_ASP_USD` | 40% | research_only | derived_proxy | critical | [35000, 90000] | Build explicit H100/H200/B200/GB200 shipment mix and ASP ranges, then calculate weighted average. Next: parse `data/sec_filings.json` filing URLs into company-quarter CapEx, segment revenue, PP&E, lease, inventory, and backlog line items. |
| `COEF_COWOS_WPM_PER_ACCELERATOR` | 35% | research_only | calibrated_placeholder | critical | [0.01, 0.03] | Replace with package-area model: accelerator_die_area_mm2, reticle/yield, interposer area, HBM stack count, CoWoS wafer throughput. Next: parse `data/sec_filings.json` filing URLs into company-quarter CapEx, segment revenue, PP&E, lease, inventory, and backlog line items. |
| `COEF_NETWORK_TBPS_PER_ACCELERATOR` | 45% | research_only | derived_proxy | high | [0.002, 0.008] | Split scale-up NVLink, scale-out InfiniBand/Ethernet, NIC radix, and oversubscription by cluster topology. Next: parse `data/sec_filings.json` filing URLs into company-quarter CapEx, segment revenue, PP&E, lease, inventory, and backlog line items. |
| `COEF_RAG_STORAGE_RATIO` | 30% | research_only | assumption | medium | [0.1, 0.6] | Replace with workload telemetry: RAG query share, documents retrieved per query, embedding refresh rate, KV-cache spill rate. Next: parse `data/sec_filings.json` filing URLs into company-quarter CapEx, segment revenue, PP&E, lease, inventory, and backlog line items. |

## Issues

| Severity | Coefficient | Issue |
|---|---|---|
| warning | `COEF_CAPEX_ACCELERATOR_SHARE` | low confidence; use for scenario exploration only |
| notice | `COEF_CAPEX_ACCELERATOR_SHARE` | validation status is derived_proxy |
| warning | `COEF_AVG_ACCELERATOR_ASP_USD` | low confidence; use for scenario exploration only |
| notice | `COEF_AVG_ACCELERATOR_ASP_USD` | validation status is derived_proxy |
| warning | `COEF_COWOS_WPM_PER_ACCELERATOR` | low confidence; use for scenario exploration only |
| notice | `COEF_COWOS_WPM_PER_ACCELERATOR` | validation status is calibrated_placeholder |
| warning | `COEF_NETWORK_TBPS_PER_ACCELERATOR` | low confidence; use for scenario exploration only |
| notice | `COEF_NETWORK_TBPS_PER_ACCELERATOR` | validation status is derived_proxy |
| warning | `COEF_RAG_STORAGE_RATIO` | low confidence; use for scenario exploration only |
| notice | `COEF_RAG_STORAGE_RATIO` | validation status is assumption |

## Interpretation

The model structure is usable for scenario analysis, but coefficients marked
`research_only` should not be treated as investment-grade. The highest-priority
upgrade path is:

1. Replace blended accelerator ASP with an explicit H100/H200/B200/GB200 shipment and ASP bridge.
2. Replace CoWoS normalized coefficient with package-area/yield/wafer-throughput math.
3. Split AI CapEx into building, power, networking, accelerator, storage, CPU/ASIC, and lease components by company-quarter.
4. Split network demand into scale-up NVLink and scale-out InfiniBand/Ethernet topology.
