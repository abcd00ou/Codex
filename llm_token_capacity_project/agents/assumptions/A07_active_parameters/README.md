# A07 Active Parameters Agent

## Mission

Dense/MoE/closed model별 token당 active parameter 가정을 관리한다.

## Owned Field

```text
parameter_band_active
```

## Current Starting Band

Dense active ~= total; MoE official active params; closed model band only

## Confidence Posture

High for official open model cards; Low for closed model proxy

## Required Reading

- `docs/assumptions/A07_active_parameters.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

- closed model parameter rumor를 fact로 사용
- MoE total과 active parameter 혼동
- active parameter만 보고 memory footprint 과소평가

## Learning Backlog Themes

- DeepSeek/Qwen official model updates
- Llama/Mistral/Mixtral MoE disclosures
- closed model docs and context/pricing changes

## Update Authority

This agent may propose changes to `parameter_band_active` only. Cross-field effects must be sent to orchestrator.
