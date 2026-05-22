# 계산식과 가정 Methodology

이 문서는 시뮬레이션의 계산 논리를 계속 점검하기 위한 기준 문서입니다. Excel의 `00_formula_assumptions`, `08a_scenario_definitions`, `08b_scenario_forecast`, `08d_benchmark_reference`, `11_hallucination_checklist`와 함께 봅니다.

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
