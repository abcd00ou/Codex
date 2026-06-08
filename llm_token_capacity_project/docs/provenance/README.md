# LLM Token Capacity Assumption Provenance

Generated from `/Users/idongseong/Documents/New project/llm_token_capacity_project/tools/generate_llm_token_capacity_report.py` full audit payload.

This folder separates each 2026-2030 model assumption into auditable provenance files. It does not change forecast logic.

## Files

- `assumptions/`: per-assumption Markdown packs.
- `outputs/reports/assumption_provenance_2026_2030.csv`: machine-readable full trace.
- `outputs/reports/assumption_provenance_2026_2030.json`: machine-readable full trace plus source registry.

## Assumption map

| ID | Title | Headline use | Trace rows | Role |
|---|---|---|---|---|
| A01 | contracted_power_gw | 직접 사용 | 180 | 2026-2030 전력 capacity 상한 또는 model-owner 귀속 capacity envelope를 정의한다. |
| A02 | active_power_gw | 직접 사용 | 540 | 계약/계획 capacity 중 실제 energization, 냉각, 네트워크, accelerator 배치를 통과한 몫만 토큰 산식에 넣는다. |
| A03 | pue | 직접 사용 | 180 | active facility power를 IT load로 바꾼다. |
| A04 | ai_workload_share | 직접 사용 | 360 | IT load 중 model-owner AI training/serving에 귀속되는 몫만 분리한다. |
| A05 | inference_power_share | 직접 사용 | 360 | 상용 generated output token capacity에 들어가는 inference power를 산출한다. |
| A06 | training_power_share | 직접 사용: inference 과대계산 방지 | 360 | frontier training, post-training, eval, reserve capacity를 inference와 분리해 과대계산을 막는다. |
| A07 | active_parameters | 간접 사용: benchmark/proxy 선택 맥락 | 9 | dense/MoE/closed model의 token당 계산량과 benchmark proxy 선택의 맥락을 제공한다. |
| A08 | tokens_per_second_per_mw | 직접 사용 | 900 | 1MW inference load가 초당 몇 generated output token을 만들 수 있는지 결정한다. |
| A09 | utilization | headline 미적용 | 72 | 이론 capacity와 실제 sustained output 사이의 차이를 공부하기 위한 sensitivity layer다. |
| A10 | attribution_rule | 간접 사용: row inclusion/exclusion | 9 | AWS/Oracle/CoreWeave 같은 host capacity와 model-owner output을 중복 계산하지 않도록 귀속 규칙을 정의한다. |
| A11 | gpu_asic_mix | 직접 사용 | 900 | 같은 inference MW라도 H200/B200/GB200/purpose-built mix에 따라 benchmark TPS/MW가 달라진다. |

## Important interpretation rules

- `Fact anchor` does not mean every value in the row is a public fact; it means the scenario is anchored to a public source.
- `Scenario capacity envelope` means the numeric value is model-created and must not be quoted as company disclosure.
- InferenceX, MLPerf and vendor serving-stack docs are benchmark/proxy evidence, not company production telemetry.
- A09 utilization is intentionally excluded from the headline token formula to avoid double counting.
- A11 purpose-built accelerator share is a numeric scenario unless company accelerator-hours or fleet split is disclosed.
