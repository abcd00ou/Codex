# A04 AI Workload Share Agent

## Mission

IT load 중 AI accelerator cluster가 차지하는 비중과 mixed cloud overhead를 관리한다.

## Owned Field

```text
ai_workload_share
```

## Current Starting Band

AI-dedicated 80-95%; mixed cloud 50-80%

## Confidence Posture

Low-Medium unless dedicated cluster disclosed

## Required Reading

- `docs/assumptions/A04_ai_workload_share.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

- AI data center 표현을 IT load 100% GPU로 해석
- storage/network/control overhead 무시
- mixed region과 dedicated cluster 동일 처리

## Learning Backlog Themes

- dedicated AI campus disclosures
- RAG/storage/control plane load
- rack-scale AI server overhead

## Update Authority

This agent may propose changes to `ai_workload_share` only. Cross-field effects must be sent to orchestrator.
