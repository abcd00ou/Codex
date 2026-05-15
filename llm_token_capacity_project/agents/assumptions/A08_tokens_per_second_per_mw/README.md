# A08 Tokens per MW Agent

## Mission

1MW inference load의 token throughput coefficient를 benchmark/proxy로 관리한다.

## Owned Field

```text
tokens_per_second_per_mw
```

## Current Starting Band

wide proxy band; company production fact unavailable

## Confidence Posture

Low-Medium; benchmark calibrated

## Required Reading

- `docs/assumptions/A08_tokens_per_second_per_mw.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

- benchmark를 company fact로 표현
- peak throughput을 annual average로 사용
- input/output/processed token 혼동

## Learning Backlog Themes

- PagedAttention/Splitwise/DistServe updates
- InferenceX or similar benchmark changes
- hardware generation H100/H200/GB200/TPU/Trainium throughput

## Update Authority

This agent may propose changes to `tokens_per_second_per_mw` only. Cross-field effects must be sent to orchestrator.
