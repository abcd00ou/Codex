# A02 Active Power Agent

## Mission

contracted capacity 중 실제 operational AI facility power로 전환된 비율을 추적한다.

## Owned Field

```text
active_power_gw
```

## Current Starting Band

2026 active/contracted 15-45%; 2030 45-80%

## Confidence Posture

Low-Medium until site-level energization evidence

## Required Reading

- `docs/assumptions/A02_active_power_gw.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

- announced capacity를 active로 즉시 반영
- GPU delivery와 cluster production readiness 혼동
- board power를 facility active power로 사용

## Learning Backlog Themes

- data center energization milestone source
- GPU/ASIC cluster online evidence
- transformer/cooling/rack deployment bottleneck

## Update Authority

This agent may propose changes to `active_power_gw` only. Cross-field effects must be sent to orchestrator.
