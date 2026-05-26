# 계산식과 가정 Methodology

이 문서는 시뮬레이션의 계산 논리를 계속 점검하기 위한 기준 문서입니다. Excel의 `00_formula_assumptions`, `02b_number_trace`, `03_power_capacity`, `04_gpu_asic_mix`, `05_inference_efficiency`, `06_training_inference_split`, `08a_scenario_definitions`, `08b_scenario_forecast`, `08d_benchmark_reference`, `11_hallucination_checklist`와 함께 봅니다.

## Excel 근거 추적 방법

최종 숫자를 검수할 때는 `07_token_forecast_2026_2030`만 보지 않습니다. 새로운 `02b_number_trace` sheet에는 **모든 company-year-scenario 핵심 숫자**에 대해 다음 필드를 기록합니다.

| Field | Meaning |
|---|---|
| `metric`, `value`, `unit` | 어떤 숫자를 검수하는지 |
| `derivation_type` | fact anchor, scenario, derived formula, benchmark-calibrated estimate 중 무엇인지 |
| `formula_or_rule` | 그 숫자가 생성되는 식 또는 원칙 |
| `why_this_number` | 왜 해당 업체에 그 값을 배정했는지 |
| `source_ids`, `assumption_ids` | 출처와 가정의 trace |
| `replacement_path` | 어떤 공개/내부 데이터가 나오면 교체할지 |

따라서 임원 질문에 답할 때는 forecast row의 숫자를 `02b_number_trace`로 내려가 업체별로 설명할 수 있습니다.

## 핵심 구조

모델은 다음 순서로 계산합니다.

```text
contracted_power_gw
-> active_power_gw
-> IT load
-> AI workload load
-> inference/training split
-> inference MW
-> tokens/sec/MW
-> utilization
-> daily / annual tokens
```

## 토큰 정의

본 보고서의 headline `inference_tokens_per_day`는 **generated output token equivalent**입니다. 사용자가 API, 앱, Copilot, 챗봇, enterprise surface에서 실제로 받는 생성 output token capacity를 의미합니다.

토큰 정의는 반드시 아래처럼 분리합니다.

| 구분 | 정의 | 포함 | 제외 | InferenceX mapping |
|---|---|---|---|---|
| 생성 output token | 상용 LLM이 사용자/API/제품 표면으로 반환하는 output token. 본 보고서의 headline 정의 | decode/output token, model-owner 운영 surface | prompt input, KV cache read/write, speculative draft token, training token | `output_tput_per_gpu`, `output_tok_s_mw`, `j_output_token` 우선 사용 |
| 처리 inference token | serving system이 처리한 input+output token | prompt/prefill input + generated output | training corpus token | `tput_per_gpu`, `tok_s_mw`, `input_tput_per_gpu`, `output_tput_per_gpu` |
| 입력/prefill token | output 생성 전에 읽는 prompt/context token | prompt, RAG context, tool transcript, conversation history | generated output token | `isl`, `input_tput_per_gpu`, `input_tok_s_mw` |
| 학습 처리 token | pretraining/post-training 중 처리된 corpus token | model card의 pretraining token, synthetic training data when disclosed | 상용 inference output token | InferenceX 직접 mapping 없음 |
| 과금 token | API/제품 billing 기준 token | provider별 input/output/cache/reasoning token | 비과금 internal work unless disclosed | 공식 API billing docs로만 reconciliation |

따라서 InferenceX의 total `tok_s_mw`를 headline token 생성량으로 직접 치환하지 않습니다. InferenceX는 `output_tok_s_mw`로 generated-token sanity check를 하고, total `tok_s_mw`는 processed-token workload 및 전력부하 진단에 사용합니다.

## 전력 계산

```text
it_load_gw = active_power_gw / pue
ai_it_load_gw = it_load_gw * ai_workload_share
inference_gw = ai_it_load_gw * inference_power_share
training_gw = ai_it_load_gw * training_power_share
```

검증 조건:

- `active_power_gw <= contracted_power_gw`
- `training_power_share + inference_power_share = 100%`
- PUE는 site-specific fact가 없으면 assumption으로 표시
- contracted/planned GW는 곧바로 active AI IT load가 아님

### 1. `contracted_power_gw`와 `active_power_gw`의 정확한 관계

`contracted_power_gw`라는 열 이름은 계산상 ceiling 역할을 하지만, 모든 업체에 동일한 수준의 법적 계약 fact를 의미하지 않습니다.

| 분류 | 의미 | 예시 | 모델 처리 |
|---|---|---|---|
| sourced committed/planned capacity anchor | 공식 발표나 partner 발표로 용량 방향을 확인할 수 있는 경우 | OpenAI Stargate, Anthropic/AWS Rainier | capacity ceiling fact anchor + active ramp scenario |
| modeled capacity envelope | model owner의 상용 서비스와 hardware 방향은 확인되지만 회사별 GW가 공개되지 않은 경우 | Microsoft, Google, Meta, Alibaba, Tencent | scenario capacity envelope |

관계는 아래처럼 고정합니다.

```text
active_power_gw =
  min(contracted_power_gw,
      modeled_operationally_deployed_power_gw)
```

`active_power_gw`는 energization, transformer/cooling/network readiness, accelerator delivery, cluster deployment를 통과해 실제 AI workload 배치가 가능한 modeled power envelope입니다. 따라서 `active_power_gw`는 항상 `contracted_power_gw`보다 작거나 같아야 하며, 발표된 capacity를 즉시 active token capacity로 해석하지 않습니다.

### 2. `ai_workload_share`의 근거와 한계

```text
ai_it_load_gw = it_load_gw * ai_workload_share
```

이 항목은 active IT capacity 중에서 해당 model-owner의 AI training/inference workload로 귀속시키는 share입니다. 공식 자료가 Maia, Ironwood, MTIA, Rainier 같은 AI/inference-oriented platform의 존재와 방향을 알려줄 수는 있지만, 대부분의 회사는 IT load의 몇 퍼센트가 실제 LLM workload인지 공개하지 않습니다.

따라서 현재 값은 다음 원칙으로 설정합니다.

- dedicated AI/model-serving capacity direction이 확인된 경우: 80-90%대의 scenario share를 허용하되 fact로 쓰지 않음
- cloud/multi-purpose 또는 attribution 불투명성이 큰 경우: 더 낮은 share 또는 낮은 confidence 적용
- storage, networking, orchestration, safety/eval, reserve와 non-token AI work를 제외하기 위해 100%를 사용하지 않음
- 업체별 배정 이유는 Excel `02b_number_trace`와 `03_power_capacity`에 기록

이 share를 fact로 승격하려면 model-owner별 cluster scheduling telemetry, allocated accelerator-hours 또는 공식 workload allocation disclosure가 필요합니다.

## 3. Numeric GPU / ASIC Mix

이전 버전의 `gpu_asic_mix`는 설명 문자열만 존재해 token coefficient와 연결되지 않았습니다. 현재 모델은 숫자 mix를 명시합니다.

```text
accelerator_mix_factor =
  gpu_share * 1.0
  + purpose_built_accelerator_share * purpose_built_relative_efficiency_factor
```

중요한 구분:

- Microsoft Maia, Google TPU/Ironwood, Meta MTIA, Anthropic/AWS Trainium처럼 official platform presence가 확인된 것은 fact anchor입니다.
- 그 platform이 회사의 실제 inference serving load 중 차지하는 백분율은 대체로 미공개이므로 numeric scenario입니다.
- xAI, OpenAI, DeepSeek, Alibaba, Tencent는 Base에서 확인 가능한 GPU reference를 우선 적용하고, 공개되지 않은 ASIC share uplift를 억지로 넣지 않습니다.

업체·연도별 `gpu_share`, `purpose_built_accelerator_share`, purpose-built label, relative efficiency factor, 산정 이유와 교체 경로는 Excel `04_gpu_asic_mix`에 기록합니다. 이 분야는 `A11_gpu_asic_mix` agent가 소유합니다.

## 4. GPU/ASIC Mix에서 `tokens_per_second_per_mw`로 가는 식

```text
tokens_per_second_per_mw =
  gpu_reference_tps_per_mw
  * accelerator_mix_factor
  * architecture_workload_factor
  * software_efficiency_growth
  * scenario_multipliers
```

각 항의 의미:

| Term | Meaning | Current Evidence Posture |
|---|---|---|
| `gpu_reference_tps_per_mw` | generated output token 기준 GPU reference baseline | benchmark-calibrated starting reference |
| `accelerator_mix_factor` | GPU 대비 purpose-built accelerator 조합의 상대 효율 | hardware direction sourced; numeric share/uplift scenario |
| `architecture_workload_factor` | MoE active parameter, closed-model proxy, routing/traffic shape 영향 | official MoE anchor 또는 closed-model proxy |
| `software_efficiency_growth` | 연도별 batching/kernel/serving-stack 향상 | scenario, hardware migration과 분리 |
| `scenario_multipliers` | Bull/Base/Bear의 deploy/optimization 변화 | explicit scenario |

InferenceX 자료는 `output_tok_s_mw`, J/output token, TTFT/TPOT, ISL/OSL를 사용해 이 식의 현실 범위를 보정하는 benchmark layer입니다. InferenceX의 benchmark row를 특정 회사의 sustained production fact로 간주하지 않습니다.

`training_tokens_processed_per_day`는 commercial generated-output supply와 합산하지 않는 별도 sanity metric입니다. 현재 `training_tps_per_mw_equivalent = tokens_per_second_per_mw * 0.22`는 공개된 업체별 training telemetry가 아닌 scenario proxy이며, `02b_number_trace`에 이 경계와 교체 근거를 표시합니다.

## 토큰 생성량 계산

```text
inference_tokens_per_day =
  inference_mw
  * tokens_per_second_per_mw
  * utilization
  * 86,400
```

연간 토큰:

```text
annual_tokens = inference_tokens_per_day * 365
```

검증 조건:

- MW, GW, seconds/day 단위 변환이 맞는지 확인
- daily token과 annual token을 혼동하지 않음
- generated output token과 processed token을 혼동하지 않음
- utilization은 fact가 아니라 scenario 계수로 취급

### 5. `utilization`을 왜 쓰는가

`tokens_per_second_per_mw`는 특정 serving 조건에서 가능한 theoretical throughput coefficient입니다. 그러나 실제 상용 서비스는 다음 이유로 peak output을 매초 실현하지 못합니다.

- 사용자 traffic arrival이 불균일하고 batch가 항상 가득 차지 않음
- TTFT/TPOT latency SLO를 지키기 위해 headroom을 남겨야 함
- failover, maintenance, 장애 대응과 regional redundancy reserve가 필요함
- prefill/decode workload shape, 긴 context, RAG/agentic traffic이 serving capacity 사용률을 변화시킴
- training, eval 또는 routing 전략이 같은 capacity pool의 활용을 제한할 수 있음

따라서:

```text
realized_output_token_capacity =
  theoretical_output_token_capacity * utilization
```

`utilization`은 단순히 서버가 켜져 있는 비율이 아니라, **설치된 inference capacity가 generated output token으로 실현되는 비율**입니다. 업체별 값은 Excel `02b_number_trace`와 `05_inference_efficiency`에 이유·source·replacement path를 함께 제공합니다.

## 파라미터 기반 sanity check

모델 파라미터와 계산량이 토큰 산출량과 모순되지 않는지 확인합니다.

```text
flops_per_output_token ~= 2 * active_parameters
tokens_per_second ~= effective_inference_flops_per_second / flops_per_output_token * serving_efficiency
```

MoE 모델은 반드시 total parameter와 active parameter를 분리합니다.

예:

- DeepSeek-V3/R1: total과 active parameter를 분리
- Qwen3 MoE: total과 active parameter를 분리
- closed model: 공식 공개가 없으면 precise parameter 숫자 금지

## Benchmark reference layer

Benchmark layer는 메인 forecast가 아니라 sanity check입니다.

```text
estimated_gpu_count =
  inference_mw * 1000 / accelerator_kw

benchmark_tokens_per_day =
  estimated_gpu_count
  * adjusted_tokens_per_second_per_gpu
  * utilization
  * 86,400
```

해석:

- 메인 모델은 tokens/sec/MW 기반
- benchmark layer는 GPU count, effective active params, serving efficiency 기반
- closed model benchmark는 proxy이며 결론으로 쓰지 않음
- benchmark와 main model의 괴리가 큰 경우 confidence downgrade 또는 재검토

## 시나리오

### Bear

전력 인허가, energization, transformer, cooling, rack deployment가 지연되고 serving stack 최적화가 늦어지는 경우입니다.

주요 방향:

- operational deployment 낮음
- inference share 상승 느림
- tokens/sec/MW 개선 낮음
- utilization 낮음

### Base

공식 발표와 공개 roadmap을 기준으로 staged deployment와 점진적 inference mix 상승을 반영합니다.

주요 방향:

- planned capacity 일부만 active로 반영
- inference share는 2026년부터 2030년까지 상승
- MoE/serving 효율은 점진 개선

### Bull

전력 투입이 빠르고, MoE/quantization/batching/speculative decoding 등 serving 최적화가 강하게 작동하는 경우입니다.

주요 방향:

- operational deployment 빠름
- inference share 상승 빠름
- tokens/sec/MW 개선 강함
- utilization 개선

### Grid-Constrained / Efficiency-Upside

전력 투입은 지연되지만 software efficiency가 개선되어 토큰 capacity 하락을 일부 상쇄하는 경우입니다.

주요 방향:

- active power ramp는 낮음
- tokens/sec/MW와 MoE 최적화는 높음
- 전력 병목과 효율 개선이 동시에 존재

## Inference share에 대한 현재 입장

현재 모델은 “전체 GW 중 inference가 이미 60% 이상”을 fact로 취급하지 않습니다.

- 2026년 Base inference share는 60% 미만으로 둠
- 2026년 60% 이상은 Bull 또는 특정 업체별 upside scenario에서만 허용
- 2030년에는 commercial serving 확대에 따라 inference share 상승을 scenario로 반영

이 값은 company-level telemetry가 공개되면 가장 먼저 교체해야 할 핵심 assumption입니다.

## 업데이트 시 반드시 같이 바꿀 문서

계산식, 계수, 출처, confidence 중 하나라도 변경하면 다음 파일을 함께 확인합니다.

- `tools/generate_llm_token_capacity_report.py`
- `docs/methodology.md`
- `docs/hallucination_checklist.md`
- `data/assumption_change_log.md`
- `data/source_review_log.md`
- `agents/assumptions/A11_gpu_asic_mix/`
