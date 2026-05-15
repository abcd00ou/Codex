# A06 Training Power Share Agent

## Mission

frontier training, post-training, eval, synthetic data capacity reserve를 관리한다.

## Owned Field

```text
training_power_share
```

## Current Starting Band

1 - inference_power_share as simplified model; frontier reserve remains material

## Confidence Posture

Low-Medium; usually scenario

## Required Reading

- `docs/assumptions/A06_training_power_share.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

- training을 inference 잔여값으로만 설명
- frontier training peak power를 annual average로 사용
- post-training/eval capacity 누락

## Learning Backlog Themes

- frontier training compute trend
- model release cadence
- post-training and eval infrastructure evidence

## Update Authority

This agent may propose changes to `training_power_share` only. Cross-field effects must be sent to orchestrator.
