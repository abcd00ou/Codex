"""Create Markdown-based assumption agents for the LLM token project."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents" / "assumptions"
RUN_DATE = "2026-05-15"


AGENTS_SPEC = [
    {
        "id": "A01",
        "slug": "contracted_power_gw",
        "title": "Contracted Power Agent",
        "field": "contracted_power_gw",
        "mission": "계약, 발표, 계획, 확보된 GW capacity를 source별로 분류하고 active power의 상한으로 관리한다.",
        "current_band": "company-specific announced/planned GW; active conversion 금지",
        "confidence": "Medium where official source exists; Low where inferred",
        "primary_docs": "docs/assumptions/A01_contracted_power_gw.md",
        "watch": ["planned와 operational 혼동", "host capacity와 model owner capacity 중복", "TWh/year와 GW 혼동"],
        "learning": ["OpenAI/Stargate site별 planned vs operational milestone", "Anthropic/AWS capacity commitment definition", "Google/Meta capex와 actual energized AI capacity 연결"],
    },
    {
        "id": "A02",
        "slug": "active_power_gw",
        "title": "Active Power Agent",
        "field": "active_power_gw",
        "mission": "contracted capacity 중 실제 operational AI facility power로 전환된 비율을 추적한다.",
        "current_band": "2026 active/contracted 15-45%; 2030 45-80%",
        "confidence": "Low-Medium until site-level energization evidence",
        "primary_docs": "docs/assumptions/A02_active_power_gw.md",
        "watch": ["announced capacity를 active로 즉시 반영", "GPU delivery와 cluster production readiness 혼동", "board power를 facility active power로 사용"],
        "learning": ["data center energization milestone source", "GPU/ASIC cluster online evidence", "transformer/cooling/rack deployment bottleneck"],
    },
    {
        "id": "A03",
        "slug": "pue",
        "title": "PUE Agent",
        "field": "pue",
        "mission": "facility power를 IT load로 변환하는 PUE 가정을 site/fleet 성격별로 관리한다.",
        "current_band": "new AI hyperscale 1.08-1.25; mixed/unknown 1.15-1.35",
        "confidence": "Medium with company/site disclosure; Low-Medium otherwise",
        "primary_docs": "docs/assumptions/A03_pue.md",
        "watch": ["PUE를 GPU efficiency로 해석", "company average를 특정 AI cluster에 확정 적용", "design PUE와 annualized PUE 혼동"],
        "learning": ["Google/Meta/Microsoft data center PUE disclosures", "liquid cooling impact", "AI rack density and facility overhead"],
    },
    {
        "id": "A04",
        "slug": "ai_workload_share",
        "title": "AI Workload Share Agent",
        "field": "ai_workload_share",
        "mission": "IT load 중 AI accelerator cluster가 차지하는 비중과 mixed cloud overhead를 관리한다.",
        "current_band": "AI-dedicated 80-95%; mixed cloud 50-80%",
        "confidence": "Low-Medium unless dedicated cluster disclosed",
        "primary_docs": "docs/assumptions/A04_ai_workload_share.md",
        "watch": ["AI data center 표현을 IT load 100% GPU로 해석", "storage/network/control overhead 무시", "mixed region과 dedicated cluster 동일 처리"],
        "learning": ["dedicated AI campus disclosures", "RAG/storage/control plane load", "rack-scale AI server overhead"],
    },
    {
        "id": "A05",
        "slug": "inference_power_share",
        "title": "Inference Power Share Agent",
        "field": "inference_power_share",
        "mission": "AI IT load 중 상용 token serving에 배정되는 비중을 scenario로 관리한다.",
        "current_band": "2026 Base 50-60%; 2030 Base 65-80%",
        "confidence": "Low-Medium; usually scenario not fact",
        "primary_docs": "docs/assumptions/A05_inference_power_share.md",
        "watch": ["2026 60%+를 fact로 표현", "inference share와 utilization 혼동", "inference-oriented chip 발표를 share fact로 해석"],
        "learning": ["Gemini/Claude/GPT product surface traffic signal", "inference-optimized hardware launches", "serving quota/product availability evidence"],
    },
    {
        "id": "A06",
        "slug": "training_power_share",
        "title": "Training Power Share Agent",
        "field": "training_power_share",
        "mission": "frontier training, post-training, eval, synthetic data capacity reserve를 관리한다.",
        "current_band": "1 - inference_power_share as simplified model; frontier reserve remains material",
        "confidence": "Low-Medium; usually scenario",
        "primary_docs": "docs/assumptions/A06_training_power_share.md",
        "watch": ["training을 inference 잔여값으로만 설명", "frontier training peak power를 annual average로 사용", "post-training/eval capacity 누락"],
        "learning": ["frontier training compute trend", "model release cadence", "post-training and eval infrastructure evidence"],
    },
    {
        "id": "A07",
        "slug": "active_parameters",
        "title": "Active Parameters Agent",
        "field": "parameter_band_active",
        "mission": "Dense/MoE/closed model별 token당 active parameter 가정을 관리한다.",
        "current_band": "Dense active ~= total; MoE official active params; closed model band only",
        "confidence": "High for official open model cards; Low for closed model proxy",
        "primary_docs": "docs/assumptions/A07_active_parameters.md",
        "watch": ["closed model parameter rumor를 fact로 사용", "MoE total과 active parameter 혼동", "active parameter만 보고 memory footprint 과소평가"],
        "learning": ["DeepSeek/Qwen official model updates", "Llama/Mistral/Mixtral MoE disclosures", "closed model docs and context/pricing changes"],
    },
    {
        "id": "A08",
        "slug": "tokens_per_second_per_mw",
        "title": "Tokens per MW Agent",
        "field": "tokens_per_second_per_mw",
        "mission": "1MW inference load의 token throughput coefficient를 benchmark/proxy로 관리한다.",
        "current_band": "wide proxy band; company production fact unavailable",
        "confidence": "Low-Medium; benchmark calibrated",
        "primary_docs": "docs/assumptions/A08_tokens_per_second_per_mw.md",
        "watch": ["benchmark를 company fact로 표현", "peak throughput을 annual average로 사용", "input/output/processed token 혼동"],
        "learning": ["PagedAttention/Splitwise/DistServe updates", "InferenceX or similar benchmark changes", "hardware generation H100/H200/GB200/TPU/Trainium throughput"],
    },
    {
        "id": "A09",
        "slug": "utilization",
        "title": "Utilization Agent",
        "field": "utilization",
        "mission": "이론 inference capacity 중 실제 연평균 token으로 전환되는 비율을 관리한다.",
        "current_band": "2026 45-65%; 2030 60-80%",
        "confidence": "Low-Medium; production telemetry rarely public",
        "primary_docs": "docs/assumptions/A09_utilization.md",
        "watch": ["peak benchmark를 평균 utilization로 사용", "latency SLO reserve 누락", "training utilization과 inference utilization 동일 처리"],
        "learning": ["traffic shape and batching evidence", "regional SLA/failover reserve concepts", "serving scheduler improvements"],
    },
    {
        "id": "A10",
        "slug": "attribution_rule",
        "title": "Attribution Rule Agent",
        "field": "attribution_rule",
        "mission": "host capacity, model owner token, product owner traffic의 귀속 규칙을 관리한다.",
        "current_band": "model-owner forecast assigns token to model owner; host kept as infrastructure layer",
        "confidence": "Medium where contractual relationship is explicit; Low where routing is opaque",
        "primary_docs": "docs/assumptions/A10_attribution_rule.md",
        "watch": ["host와 model owner 중복 계산", "product owner와 model owner 혼동", "open-weight downloads를 hosted token generation으로 해석"],
        "learning": ["Microsoft/OpenAI Copilot attribution", "Anthropic AWS/Google route", "Oracle/Stargate host vs OpenAI model owner"],
    },
]


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def readme(spec: dict) -> str:
    return f"""# {spec['id']} {spec['title']}

## Mission

{spec['mission']}

## Owned Field

```text
{spec['field']}
```

## Current Starting Band

{spec['current_band']}

## Confidence Posture

{spec['confidence']}

## Required Reading

- `{spec['primary_docs']}`
- `agents/shared/evidence_rules.md`
- `agents/shared/update_protocol.md`
- `docs/hallucination_checklist.md`

## Watchouts

{bullets(spec['watch'])}

## Learning Backlog Themes

{bullets(spec['learning'])}

## Update Authority

This agent may propose changes to `{spec['field']}` only. Cross-field effects must be sent to orchestrator.
"""


def state(spec: dict) -> str:
    return f"""# State: {spec['id']} {spec['slug']}

| Field | Value |
|---|---|
| agent_id | {spec['id']} |
| owned_field | {spec['field']} |
| current_starting_band | {spec['current_band']} |
| confidence | {spec['confidence']} |
| last_reviewed | {RUN_DATE} |
| status | Initial setup |

## Current Assumption

{spec['current_band']}

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| {RUN_DATE} | Initial state created | Agent system setup | none | baseline |

## Downstream Impact Notes

- Orchestrator review required before generator values are changed.
- If this assumption moves company token forecast by more than 10%, mark as high-impact.
"""


def evidence(spec: dict) -> str:
    return f"""# Evidence: {spec['id']} {spec['slug']}

This file stores reviewed evidence for `{spec['field']}`.

## Evidence Table

| evidence_id | source_id | date | evidence_class | exact_claim_or_number | unit | model_field_impacted | confidence | reviewer |
|---|---|---|---|---|---|---|---|---|
| {spec['id']}_E000 | baseline | {RUN_DATE} | Scenario | Initial agent created from existing assumption textbook | n/a | {spec['field']} | Low-Medium | Codex |

## Review Notes

- Add only source-reviewed evidence here.
- Do not paste copyrighted report text. Summarize claim, number, unit, and implication.
- Keep fact and interpretation separate.
"""


def queue(spec: dict) -> str:
    rows = "\n".join(f"| {RUN_DATE} | {theme} | pending | Need source review | open |" for theme in spec["learning"])
    return f"""# Learning Queue: {spec['id']} {spec['slug']}

| Created | Learning task | Priority | Expected evidence | Status |
|---|---|---|---|---|
{rows}

## Next Agent Prompt

```text
You are the {spec['id']} {spec['title']} for the LLM token capacity project.
Read this folder's README.md, state.md, evidence.md, learning_queue.md, plus shared evidence rules.
Pick one open learning task, gather only high-quality sources, classify each claim as Fact/Estimate/Proxy/Scenario,
then propose whether `{spec['field']}` should change. Do not modify generator values until orchestrator review.
```
"""


def main() -> None:
    for spec in AGENTS_SPEC:
        path = AGENTS / f"{spec['id']}_{spec['slug']}"
        path.mkdir(parents=True, exist_ok=True)
        (path / "README.md").write_text(readme(spec), encoding="utf-8")
        (path / "state.md").write_text(state(spec), encoding="utf-8")
        (path / "evidence.md").write_text(evidence(spec), encoding="utf-8")
        (path / "learning_queue.md").write_text(queue(spec), encoding="utf-8")
    print({"status": "PASS", "agents": len(AGENTS_SPEC)})


if __name__ == "__main__":
    main()
