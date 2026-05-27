# 계산식과 가정 Methodology

이 문서는 시뮬레이션의 계산 논리를 계속 점검하기 위한 기준 문서입니다. 보고용 Excel은 `00_Logic`, `01_Benchmark_Input`, `02_Inputs`, `03_Calculation`, `04_Output`, `05_Checks` 여섯 시트만 노출합니다. 상세 source/audit/agent 기록은 프로젝트 Markdown과 정규화 CSV에 보관하며 보고용 workbook 화면에는 싣지 않습니다.

## 보고용 Excel 원칙

- 직접 입력되는 숫자는 `02_Inputs`의 scenario 입력값과 `01_Benchmark_Input`의 선택 benchmark 값뿐입니다.
- `operational_power_gw`, `inference_gw`, `weighted_tps_per_mw`, `inference_tokens_per_day`, 연간 토큰 및 시나리오 합계는 Excel 수식으로 계산합니다.
- `03_Calculation`은 행 단위 계산 추적표이고, `04_Output`은 그 수식을 참조하는 출력표와 차트입니다.
- `05_Checks`는 capacity bound, power split, accelerator share, purpose-built no-uplift 및 headline formula 범위를 수식으로 검증합니다.

## Excel 근거 추적 방법

상세 내부 검수 기록은 agent와 Markdown 문서에서 유지합니다. 보고용 Excel에서는 `03_Calculation`의 셀 수식을 열어 **모든 company-year-scenario 핵심 숫자**를 직접 재계산합니다.

| Field | Meaning |
|---|---|
| `metric`, `value`, `unit` | 어떤 숫자를 검수하는지 |
| `derivation_type` | fact anchor, scenario, derived formula, benchmark-calibrated estimate 중 무엇인지 |
| `formula_or_rule` | 그 숫자가 생성되는 식 또는 원칙 |
| `why_this_number` | 왜 해당 업체에 그 값을 배정했는지 |
| `source_ids`, `assumption_ids` | 출처와 가정의 trace |
| `replacement_path` | 어떤 공개/내부 데이터가 나오면 교체할지 |

따라서 임원 질문에 답할 때는 `04_Output` 결과 셀에서 `03_Calculation`, `02_Inputs`, `01_Benchmark_Input` 순서로 formula precedent를 따라가면 됩니다.

### 확인값과 합리적 가정의 구분

Fact/assumption audit는 내부 검수 기록으로 유지하고, 보고용 Excel에는 핵심 계산에 필요한 입력과 수식만 표시합니다. 내부 audit는 업체별 다음 항목을 관리합니다.

| 항목 | Official fact로 인정 가능한 것 | Model에서 별도 분리하는 것 |
|---|---|---|
| 모델/파라미터 | 공식 model card·technical report가 공개한 parameter 또는 명시적 undisclosed 상태 | closed-model parameter band |
| capacity | 공식 발표된 commitment, announced capacity, GPU/cluster count | 2026/2030 company endpoint, operational ramp |
| active power | site-level energized/operational disclosure가 있는 경우에만 fact 가능 | 공개 telemetry 없는 모든 active GW |
| AI workload share | 공식 workload denominator가 있을 때만 fact 가능 | dedicated AI 방향성에서 추론한 share |
| GPU/ASIC mix | Maia/TPU/MTIA/Trainium/H800 등 platform 존재 | serving fleet 비중 |
| inference share | company-level workload power split 공시 | inference adoption 기반 share |
| tokens/MW | matched production output throughput 공시 | 고정 조건 InferenceX `output_tok_s_mw` proxy |
| utilization | provider surface별 realized serving telemetry | 보조 sensitivity로만 보관하며 headline 계산에는 미적용 |
| output tokens | 공개 output token volume | 본 simulation 계산 결과 |

공식 source가 존재한다는 사실만으로 모델 입력 숫자가 `Fact`가 되는 것은 아닙니다. 예를 들어 OpenAI의 2030 `12 GW`는 공개된 `10 GW 초과` commitment를 참조하지만 그 자체가 공개 숫자는 아니며, Anthropic의 `7 GW` endpoint도 등록된 `5 GW-class` reference 위의 확장 시나리오입니다. 이 둘은 `Scenario extending public capacity anchor`로만 읽습니다.

## 핵심 구조

모델은 다음 순서로 계산합니다.

```text
contracted_power_gw
-> operational_deployment_share -> active_power_gw
-> IT load
-> AI workload load
-> inference/training split
-> inference MW
-> selected InferenceX output tokens/sec/MW
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
| sourced committed/planned capacity anchor | 공식 발표나 partner 발표로 용량 방향을 확인할 수 있는 경우 | OpenAI Stargate, Anthropic/AWS Rainier | public anchor와 model endpoint를 분리하고 active ramp는 scenario 처리 |
| modeled capacity envelope | model owner의 상용 서비스와 hardware 방향은 확인되지만 회사별 GW가 공개되지 않은 경우 | Microsoft, Google, Meta, Alibaba, Tencent | scenario capacity envelope |

관계는 아래처럼 한 줄로 고정합니다.

```text
active_power_gw = operational_power_gw
                = contracted_power_gw * operational_deployment_share
active_power_gw <= contracted_power_gw
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
- 보고용 Excel에는 업체별 입력값만 `02_Inputs`에 표시하고, 배정 이유와 source/replacement path는 내부 agent 기록에서 관리

이 share를 fact로 승격하려면 model-owner별 cluster scheduling telemetry, allocated accelerator-hours 또는 공식 workload allocation disclosure가 필요합니다.

## 3. Numeric GPU / ASIC Mix

현재 모델은 GPU와 purpose-built accelerator 비중을 숫자로 명시합니다. 다만 mix를 보인다는 것과 성능 uplift를 주장한다는 것은 분리합니다.

```text
tokens_per_second_per_mw =
  gpu_share * gpu_benchmark_tps_per_mw
  + purpose_built_accelerator_share * purpose_built_tps_per_mw
```

중요한 구분:

- Microsoft Maia, Google TPU/Ironwood, Meta MTIA, Anthropic/AWS Trainium처럼 official platform presence가 확인된 것은 fact anchor입니다.
- 그 platform이 회사의 실제 inference serving load 중 차지하는 백분율은 대체로 미공개이므로 numeric scenario입니다.
- TPU, Maia, MTIA, Trainium의 matched `output_tok_s_mw` 비교자료가 채택되기 전에는 `purpose_built_tps_per_mw = gpu_benchmark_tps_per_mw`로 두며 uplift를 만들지 않습니다.
- xAI, OpenAI, DeepSeek, Alibaba, Tencent는 Base에서 확인 가능한 GPU reference를 우선 적용하고, 공개되지 않은 ASIC share uplift를 억지로 넣지 않습니다.

업체·연도별 `gpu_share`와 `purpose_built_share`는 보고용 Excel `02_Inputs`에 표시합니다. 산정 이유와 교체 경로는 `A11_gpu_asic_mix` agent 기록에서 관리합니다.

## 4. GPU/ASIC Mix에서 `tokens_per_second_per_mw`로 가는 식

핵심 TPS/MW는 Excel `01_Benchmark_Input`에서 바로 읽습니다. 공통 비교 조건은 `B200`, `single_turn`, `ISL=1024`, `OSL=1024`, metric은 generated-output 기준 `output_tok_s_mw`의 중앙값입니다. 업체별 상용 모델과 가장 가까운 공개 proxy model을 매핑하되, 특정 업체의 sustained production fact라고 표현하지 않습니다.

MoE 구조, precision, batching, TTFT/TPOT, SLO, 소프트웨어 개선은 모두 중요합니다. 그러나 해당 영향을 선택 benchmark 위에 다시 곱하면 같은 효율을 중복 반영할 위험이 있으므로 headline 계산에서는 제외하고 후속 sensitivity 연구 대상으로 분리합니다.

## 토큰 생성량 계산

```text
inference_tokens_per_day =
  contracted_power_gw
  * operational_deployment_share
  / pue
  * ai_workload_share
  * inference_power_share
  * 1,000
  * tokens_per_second_per_mw
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
- utilization, MoE uplift, architecture/software multiplier가 headline 식에 숨어 들어가지 않았는지 확인

### 5. `utilization`을 headline에서 제외한 이유

`tokens_per_second_per_mw`는 특정 serving 조건에서 가능한 theoretical throughput coefficient입니다. 그러나 실제 상용 서비스는 다음 이유로 peak output을 매초 실현하지 못합니다.

- 사용자 traffic arrival이 불균일하고 batch가 항상 가득 차지 않음
- TTFT/TPOT latency SLO를 지키기 위해 headroom을 남겨야 함
- failover, maintenance, 장애 대응과 regional redundancy reserve가 필요함
- prefill/decode workload shape, 긴 context, RAG/agentic traffic이 serving capacity 사용률을 변화시킴
- training, eval 또는 routing 전략이 같은 capacity pool의 활용을 제한할 수 있음

이 변수는 운영 연구에는 유효하지만 업체별 sustained telemetry가 공개되지 않은 상태에서 headline 산식에 곱하면 토큰 결과를 크게 바꾸는 추가 가정을 만듭니다. 또한 InferenceX output TPS/MW 자체가 benchmark 실행조건에서 관측된 결과이므로 utilization을 다시 곱하는 방식은 임원 보고에서 직관성을 떨어뜨립니다.

따라서 `utilization`은 내부 연구 문서의 SLO/traffic sensitivity 주제로만 유지하고, 보고용 workbook과 기본 토큰 생성량에는 적용하지 않습니다.

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
  * 86,400
```

해석:

- 메인 모델은 tokens/sec/MW 기반
- benchmark layer는 GPU count, effective active params, serving efficiency 기반
- closed model benchmark는 proxy이며 결론으로 쓰지 않음
- benchmark와 main model의 괴리가 큰 경우 confidence downgrade 또는 재검토

## 시나리오

### Bear

전력 인허가, energization, transformer, cooling, rack deployment가 지연되고 inference 배정이 낮아지는 경우입니다.

주요 방향:

- operational deployment 낮음
- inference share 상승 느림
- selected tokens/sec/MW는 Base와 동일하게 고정

### Base

공식 발표와 공개 roadmap을 기준으로 staged deployment와 점진적 inference mix 상승을 반영합니다.

주요 방향:

- planned capacity 일부만 active로 반영
- inference share는 2026년부터 2030년까지 상승
- selected tokens/sec/MW는 Base 기준 proxy로 고정

### Bull

전력 투입이 빠르고 inference 우선 배정이 빠르게 진행되는 경우입니다.

주요 방향:

- operational deployment 빠름
- inference share 상승 빠름
- selected tokens/sec/MW는 Base와 동일하게 고정

### Grid-Constrained / Efficiency-Upside

전력 투입은 지연되지만 제한된 AI load에서 inference 우선 배정이 진행되는 경우입니다.

주요 방향:

- active power ramp는 낮음
- selected tokens/sec/MW는 Base와 동일하게 고정
- 전력 병목과 inference 우선 배분이 동시에 존재

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
