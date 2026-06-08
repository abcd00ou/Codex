# A03 pue Provenance

Short name: facility power -> IT load 전환

Role: active facility power를 IT load로 바꾼다.

Headline use: 직접 사용

Confidence rule: 업체/사이트별 measured PUE가 없으면 scenario parameter로 유지한다.

## Metrics covered

`pue`

## 숫자 결정 로직

- PUE는 facility power를 IT load로 변환하는 계수다. 링크가 데이터센터 효율 또는 인프라 방향을 보여주더라도, 회사/사이트별 measured PUE가 없으면 수치는 scenario다.
- 전력 총량을 accelerator가 소비하는 IT load로 과대 해석하지 않기 위해 PUE를 별도 assumption으로 분리했다.
- it_load_gw는 active_power_gw / pue로 계산한다. 낮은 PUE일수록 같은 facility power에서 더 많은 IT load가 나온다.
- 실제 site PUE, 냉각 방식, 계절별 PUE가 확보되면 이 값은 사이트별로 교체해야 한다.

### 링크를 숫자로 읽는 방식

아래 표는 링크 자체를 그대로 숫자로 옮긴 것이 아니라, 각 출처가 어떤 판단에 쓰였는지를 기록한다. URL이 capacity 방향성만 확인해주는 경우와 실제 수치 anchor를 제공하는 경우를 구분해서 읽어야 한다.

| ID | URL/report | 숫자 결정에 쓰인 방식 | Confidence |
|---|---|---|---|
| ASSUMP_POWER_RAMP |  | 계약 전력은 발표/공급망 방향성 anchor, active power는 실제 IT load 가동률 ramp로 별도 산정. | 0.55 |

### 행 단위 결정 샘플

대표 metric 행을 기준으로, 실제 trace에서 가져온 `why_this_number`, 산식, 교체 경로를 함께 붙였다. 이 표의 값은 모델 입력값이며, 공시 숫자와 scenario 숫자가 섞여 있을 수 있다.

| Company | Metric | Value | 왜 이 숫자인가 | Formula/rule | 교체 경로 | Source IDs |
|---|---|---|---|---|---|---|
| Microsoft | pue | 1.2 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| Google | pue | 1.18 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| Meta | pue | 1.2 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| xAI | pue | 1.22 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| OpenAI | pue | 1.2 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| Anthropic | pue | 1.18 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| DeepSeek | pue | 1.24 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| Alibaba | pue | 1.23 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |
| Tencent | pue | 1.23 | No provider-wide site-level PUE is used as a disclosed fact; PUE represents facility-to-IT conversion within the scenario. | it_load_gw = active_power_gw / pue | Site-level measured PUE matched to attributed AI capacity. | ASSUMP_POWER_RAMP |

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

