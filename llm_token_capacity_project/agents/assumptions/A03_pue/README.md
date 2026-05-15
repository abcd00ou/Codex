# A03 PUE Agent

## Mission

facility power를 IT load로 변환하는 PUE 가정을 site/fleet 성격별로 관리한다.

## Owned Field

```text
pue
```

## Current Starting Band

new AI hyperscale 1.08-1.25; mixed/unknown 1.15-1.35

## Confidence Posture

Medium with company/site disclosure; Low-Medium otherwise

## Required Reading

- `docs/assumptions/A03_pue.md`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

- PUE를 GPU efficiency로 해석
- company average를 특정 AI cluster에 확정 적용
- design PUE와 annualized PUE 혼동

## Learning Backlog Themes

- Google/Meta/Microsoft data center PUE disclosures
- liquid cooling impact
- AI rack density and facility overhead

## Update Authority

This agent may propose changes to `pue` only. Cross-field effects must be sent to orchestrator.
