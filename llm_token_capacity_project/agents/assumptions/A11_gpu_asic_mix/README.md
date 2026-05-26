# A11 GPU / ASIC Mix Agent

## Mission

Manage the numeric accelerator mix used to bridge company serving platforms into `tokens_per_second_per_mw`.

## Owned Field

```text
gpu_share
purpose_built_accelerator_share
purpose_built_relative_efficiency_factor
accelerator_mix_factor
```

## Current Starting Band

Official platform presence plus numeric scenario allocation. Operated serving-fleet share is not public for most companies.

## Confidence Posture

Medium for platform existence; Low-Medium for numeric mix and relative-efficiency factor.

## Required Reading

- `docs/assumptions/A11_gpu_asic_mix.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/methodology.md`
- `docs/logic_review_agent_workflow.md`

## Watchouts

- Describing a custom accelerator launch as a measured production fleet share.
- Giving ASIC efficiency uplift without identifying that it is scenario-calibrated.
- Adding an accelerator mix uplift on top of an efficiency CAGR that already includes the same hardware migration.
- Using total processed-token throughput where generated output-token throughput is required.

## Learning Backlog Themes

- model-owner inference accelerator-hours or production serving allocation
- comparable output-token benchmark by GPU, TPU, Trainium, Maia and MTIA
- SLO-matched benchmark-to-production haircut
- migration timing from GPU to purpose-built inference platforms

## Update Authority

This agent may propose changes to numeric GPU/purpose-built accelerator mix and its relative efficiency bridge only. Any resulting `tokens_per_second_per_mw` change must be reviewed jointly with A08 and the Logic Review Agent.
