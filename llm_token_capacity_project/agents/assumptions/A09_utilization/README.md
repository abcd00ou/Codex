# A09 Utilization Agent

## Mission

이론 inference capacity 중 실제 연평균 token으로 전환되는 비율을 관리한다.

## Owned Field

```text
utilization
```

## Current Starting Band

2026 45-65%; 2030 60-80%

## Confidence Posture

Low-Medium; production telemetry rarely public

## Required Reading

- `docs/assumptions/A09_utilization.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

- peak benchmark를 평균 utilization로 사용
- latency SLO reserve 누락
- training utilization과 inference utilization 동일 처리

## Learning Backlog Themes

- traffic shape and batching evidence
- regional SLA/failover reserve concepts
- serving scheduler improvements

## Update Authority

This agent may propose changes to `utilization` only. Cross-field effects must be sent to orchestrator.
