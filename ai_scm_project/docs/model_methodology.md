# Evidence-Based Supply Chain Dynamics Methodology

This project should treat every model number as auditable. A coefficient is allowed in the dynamics model only when it has:

- `evidence_ids`: source records in `data/model_evidence.json`
- `derivation_type`: direct spec, direct company result, derived estimate, or internal synthesis
- `confidence`: numeric quality score
- `replacement_path`: how to improve or replace the coefficient

## Core Equations

### Token Demand to Accelerator Utilization

```text
accelerators_required =
  tokens_per_day / 86400 / (tokens_per_second_per_accelerator * utilization)
```

This captures utilization pull from actual AI workload volume.

### CapEx to Accelerator Procurement

```text
accelerators_procured =
  total_capex_usd
  * ai_infra_share
  * accelerator_share
  / avg_accelerator_asp_usd
```

This captures strategic prebuild demand: training clusters, reserve capacity, future inference demand, and scarce component allocation.

### Effective Accelerator Demand

```text
accelerator_demand = max(accelerators_required, accelerators_procured)
```

The model uses the larger of utilization demand and procurement demand because hyperscalers often buy capacity before token usage fully materializes.

### Accelerator to HBM

```text
hbm_pb = accelerator_units * hbm_gb_per_accelerator / 1e6
```

HBM per accelerator should come from product specs or a weighted accelerator mix.

### Accelerator to CoWoS

```text
cowos_wpm = accelerator_units * cowos_wpm_per_accelerator
```

This is currently a low-confidence normalized coefficient. It should be replaced by package-level modeling:

```text
cowos_capacity =
  wafer_starts
  * usable_interposer_area
  * yield
  / package_area_per_accelerator
```

### Accelerator to Power

```text
power_gw =
  accelerator_units
  * accelerator_tdp_w
  * server_overhead
  * pue
  / 1e9
```

TDP should come from product specs. Server overhead and PUE need facility-level evidence.

### Gap, Fulfillment, and Backlog

```text
gap_ratio = demand / supply
fulfillment_rate = min(1, 1 / max_layer_gap_ratio)
unserved_accelerators = requested_accelerators * (1 - fulfillment_rate)
next_year_backlog = unserved_accelerators * backlog_carryover
```

The tightest layer caps deployment. Unserved demand carries into the next period as backlog.

## Evidence Quality Rules

- Direct company product specs and SEC filings: `0.90-0.98`
- Earnings-call commentary with numeric values: `0.80-0.92`
- Analyst or industry estimate with clear method: `0.55-0.75`
- Internal synthesis or temporary calibration: `0.30-0.65`

Low-confidence coefficients are allowed only if they are explicit and have a replacement path.
