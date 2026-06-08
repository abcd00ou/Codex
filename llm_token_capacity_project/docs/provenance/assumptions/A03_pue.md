# A03 pue Provenance

Short name: facility power -> IT load 전환

Role: active facility power를 IT load로 바꾼다.

Headline use: 직접 사용

Confidence rule: 업체/사이트별 measured PUE가 없으면 scenario parameter로 유지한다.

## Metrics covered

`pue`

## Base scenario 2026 -> 2030 endpoint view

| Company | Metric | 2026 -> 2030 | Derivation | Confidence | Source IDs |
|---|---|---|---|---|---|
| Alibaba | pue | 1.23 -> 1.23 ratio | Scenario parameter | Medium | ASSUMP_POWER_RAMP |
| Anthropic | pue | 1.18 -> 1.18 ratio | Scenario parameter | Medium | ASSUMP_POWER_RAMP |
| DeepSeek | pue | 1.24 -> 1.24 ratio | Scenario parameter | Parameter High / Capacity Low-Medium | ASSUMP_POWER_RAMP |
| Google | pue | 1.18 -> 1.18 ratio | Scenario parameter | Medium-High | ASSUMP_POWER_RAMP |
| Meta | pue | 1.2 -> 1.2 ratio | Scenario parameter | Medium | ASSUMP_POWER_RAMP |
| Microsoft | pue | 1.2 -> 1.2 ratio | Scenario parameter | Medium | ASSUMP_POWER_RAMP |
| OpenAI | pue | 1.2 -> 1.2 ratio | Scenario parameter | Medium | ASSUMP_POWER_RAMP |
| Tencent | pue | 1.23 -> 1.23 ratio | Scenario parameter | Medium-Low | ASSUMP_POWER_RAMP |
| xAI | pue | 1.22 -> 1.22 ratio | Scenario parameter | Medium-Low | ASSUMP_POWER_RAMP |

## Formula/rule examples

| Metric | Formula or rule | Why this number | Replacement path |
|---|---|---|---|
| pue | it_load_gw = active_power_gw / pue | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | Site-level measured PUE matched to attributed AI capacity. |

## Source catalog for this assumption

| ID | Title/description | Publisher/category | Date | Tier | Confidence | URL/report |
|---|---|---|---|---|---|---|
| ASSUMP_POWER_RAMP | 계약 전력은 발표/공급망 방향성 anchor, active power는 실제 IT load 가동률 ramp로 별도 산정. |  |  |  | 0.55 |  |

## Linked assumption IDs

`ASSUMP_APP_EMBEDDING`, `ASSUMP_CLOSED_MODEL_BAND`, `ASSUMP_CLUSTER_RAMP`, `ASSUMP_CN_CAPACITY_TRANSPARENCY`, `ASSUMP_CONSUMER_AI_UTILIZATION`, `ASSUMP_INFERENCE_SHARE_NOT_FACT_60`, `ASSUMP_MOE_EFFICIENCY`, `ASSUMP_MS_OPENAI_ATTRIBUTION`, `ASSUMP_NUMERIC_ACCELERATOR_MIX`, `ASSUMP_POWER_RAMP`, `ASSUMP_STARGATE_RAMP`, `ASSUMP_TPU_EFFICIENCY`

