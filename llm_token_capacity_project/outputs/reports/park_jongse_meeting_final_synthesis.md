# 박종세 교수 미팅 최종 정리본

작성일: 2026-07-22

통합한 자료:
- 사전 질문지: `output/doc/jongse_park_llm_serving_questions_expected_answers.docx`
- 미팅 요약: `llm_token_capacity_project/outputs/reports/park_jongse_interview_summary.md`
- 관련 프로젝트 맥락: InferenceX benchmark, agentic traces, LLMServingSim, 전력 기반 token capacity model

## 1. 최종 결론

박종세 교수님과의 미팅에서 확인된 핵심은 다음이다.

LLM token capacity를 전력과 GPU 수요로 역산하는 접근은 방향성이 맞다. 하지만 닫힌 상용 모델의 파라미터 수, serving architecture, batching 정책, cache 정책, GPU topology, prefill/decode 분리 방식이 공개되어 있지 않기 때문에, 순수 이론식이나 public benchmark 하나만으로 정확한 production token capacity를 계산하기는 어렵다.

따라서 현재 프로젝트의 TPS/MW 산식은 다음 원칙으로 정리해야 한다.

1. InferenceX는 production telemetry가 아니라 public benchmark/proxy로 사용한다.
2. GPU/model/framework/precision/ISL/OSL/concurrency 조건을 맞춘 row만 비교한다.
3. headline token capacity는 generated output token 기준으로 유지하되, input/prefill pressure는 별도 진단 지표로 둔다.
4. short chat, long chat, agentic workload를 분리하는 것은 타당하다.
5. agentic workload는 단순 output TPS만 보면 안 되고, call depth, tool wait, prefix/KV cache, long context, p95 latency를 함께 봐야 한다.
6. LLMServingSim은 정확한 회사별 생산량 예측기가 아니라, benchmark를 production-like workload로 보정하기 위한 system-level calibration 도구로 보는 것이 맞다.

## 2. 사전 질문지와 실제 미팅 답변의 대응

### 질문 1. 작은 실험 환경의 LLMServingSim 결과를 대규모 H100/B200 데이터센터로 외삽할 수 있는가?

사전 가설:
LLMServingSim은 특정 GPU SKU의 절대 성능을 맞히기보다 serving 구조의 병목을 보는 도구다. 대규모 외삽에는 interconnect, scheduler, memory pressure, parallelism mapping, power cap, software stack 보정이 필요하다.

미팅 후 확인:
이 가설은 대체로 맞다. 교수님은 simulator의 목적이 실제 대규모 시스템의 절대 TPS를 정확히 맞히는 것이 아니라, 서로 다른 system configuration의 우열과 병목 방향을 보는 것에 가깝다고 설명했다. 실제 GPU 실험은 변동성이 크고, 논문에서도 극단값 제거, median/average 처리, calibration이 필요하다.

프로젝트 반영:
InferenceX TPS/MW를 회사별 production TPS/MW로 직접 대입하지 않는다. 공개 benchmark를 기준점으로 두고 workload fit factor, latency/SLO filter, cache/memory pressure correction을 별도 계층으로 둔다.

### 질문 2. 작은 infra에서 LLM serving을 benchmark하는 이유는 무엇인가?

사전 가설:
작은 infra는 production scale을 재현하기보다 prefill/decode, KV cache, batching, tensor/pipeline parallelism의 병목 구조를 분리해서 보기 위한 것이다.

미팅 후 확인:
교수님은 대형 hyperscaler가 실제로는 NVIDIA prototype server를 받아 hardware/software co-design 팀이 붙어 configuration을 계속 튜닝한다고 설명했다. 작은 실험은 그 전체 과정을 대체하지 못하지만, 어떤 요소가 throughput과 latency를 흔드는지 보는 데 의미가 있다.

프로젝트 반영:
GPU 수가 많아진다고 token throughput이 선형으로 증가한다고 가정하지 않는다. cluster scale에서는 topology, communication, memory residency, scheduler가 별도 discount 요인이 된다.

### 질문 3. PIM/NPU/custom accelerator가 상용 LLM serving에 얼마나 중요해지는가?

사전 가설:
GPU/TPU가 중심이고, PIM/NPU는 memory-bound subtask 또는 upside scenario로 보는 것이 안전하다.

미팅 후 확인:
교수님은 하드웨어별로 software stack을 맞추는 일이 매우 어렵다고 설명했다. TPU는 Google Cloud에서 제공하는 stack을 쓰므로 비교적 사용 경로가 정리되어 있지만, 국내 NPU 등은 vLLM 같은 serving layer에 효율적으로 붙이는 것 자체가 큰 과제다.

프로젝트 반영:
custom accelerator는 base case에서 과도하게 효율 uplift를 주지 않는다. GPU/TPU 외 hardware는 `purpose-built` 또는 `future replacement path`로 두고, 실제 benchmark가 생기면 교체한다.

### 질문 4. Tensor/pipeline/hybrid parallelism 결과를 benchmark 비교에 반영해야 하는가?

사전 가설:
GPU별 비교는 framework/precision뿐 아니라 TP/EP/worker 수, disaggregated serving 여부까지 맞춰야 의미가 있다.

미팅 후 확인:
교수님은 대형 모델은 GPU 수를 늘려가며 목표 throughput에 도달하는 방식의 정방향 탐색은 가능하지만, 목표 TPS에서 최적 GPU/메모리 구성을 자동으로 찾는 역방향 설계는 변수가 많아 어렵다고 설명했다.

프로젝트 반영:
현재 모델은 “필요 GPU 수의 정확한 최적 설계”가 아니라 “전력 envelope에서 가능한 token capacity scenario”로 표현한다. InferenceX row selection에는 GPU count, concurrency, framework, precision, ISL/OSL, 가능하면 TP/EP/disagg 조건을 남겨야 한다.

### 질문 5. LLMServingSim에서 이전 step 결과 재사용은 어떤 의미인가?

사전 가설:
반복되는 transformer block, non-attention layer, static shape 결과를 cache하고, sequence length/KV cache/attention-dependent 부분만 갱신하는 것으로 이해했다.

미팅 후 확인:
미팅에서 이 부분을 깊게 기술적으로 확정하지는 못했다. 다만 교수님은 serving simulation이 실제 시스템을 완벽히 재현하는 것보다 반복되는 구조와 병목을 빠르게 탐색하는 용도에 가깝다는 점을 강조했다.

프로젝트 반영:
향후 LLMServingSim을 직접 사용할 경우, model/GPU/framework/precision은 고정하고 ISL/OSL, concurrency, cache hit, prefill/decode split만 바꾸는 scenario sweep 구조가 적절하다.

### 질문 6. Power model은 어느 수준까지 결합할 수 있는가?

사전 가설:
GPU TDP만 곱하는 방식은 부족하고, prefill/decode utilization, memory bandwidth, interconnect, offload, power cap, PUE를 분리해야 한다.

미팅 후 확인:
교수님 설명에 따르면 token 생성 산식에서 FLOPS만 보는 것은 지나치게 단순하다. Decode는 memory bandwidth 병목이 중요하고, batch inference에서는 weights는 공유되지만 KV cache는 request별로 증가한다. 따라서 power와 TPS/MW는 FLOPS, HBM bandwidth, KV cache, batch size, serving stack의 함수다.

프로젝트 반영:
전력 기반 산식은 `inference_gw * TPS/MW`를 유지하되, TPS/MW의 근거는 단순 FLOPS가 아니라 benchmark-derived output TPS/MW로 둔다. GPU board TDP가 아니라 all-in serving power 또는 최소한 서버/랙 power basis로 통일해야 한다.

### 질문 7. 아직 출시되지 않은 미래 GPU도 FLOPS/HBM만 있으면 forecast에 넣을 수 있는가?

사전 가설:
first-order bound는 가능하지만 calibrated prediction은 어렵다.

미팅 후 확인:
교수님은 새로운 GPU에서 simulator가 실제 성능을 보장할 수는 없다고 설명했다. 논문 실험도 B200 같은 최신 GPU를 충분히 빌려 검증하기 어렵고, H100조차 제한적으로 사용했다고 언급했다.

프로젝트 반영:
미래 GPU는 point estimate가 아니라 low/base/high envelope로 둔다. FLOPS/HBM은 upper bound, software maturity와 serving stack 안정성은 discount factor로 처리한다.

### 질문 8. InferenceX 같은 public benchmark를 어떻게 봐야 하는가?

사전 가설:
유용하지만 production telemetry는 아니며, condition matching과 caveat가 필요하다.

미팅 후 확인:
교수님은 “시스템 specification 없이 TPS만 있는 리더보드는 의미가 약하다”고 설명했다. 반대로 GPU 수, 모델, batch/concurrency, ISL/OSL, framework, precision이 명시된 실측값은 capacity 추정의 기준점으로 쓸 수 있다.

프로젝트 반영:
InferenceX는 A08 `tokens_per_second_per_mw`의 benchmark layer로 유지한다. 모든 보고서에는 `benchmark/proxy only`, `not company production telemetry`, `match condition before use`를 명시한다.

### 질문 9. Agentic trace의 cache hit ratio를 어떻게 써야 하는가?

사전 가설:
serving-level prefix/KV cache hit로 해석하고, GPU hit는 prefill 절감, CPU hit는 latency penalty와 함께 봐야 한다.

미팅 후 확인:
미팅에서 cache hit 정의 자체는 확정하지 못했다. 다만 agentic workload는 긴 context와 반복 call, tool result accumulation 때문에 KV cache와 prefill pressure가 커진다는 방향은 교수님 설명과 일치한다.

프로젝트 반영:
agentic trace는 throughput telemetry가 아니라 workload shape 근거로 사용한다. 평균 input/output token, call depth, subagent/tool loop를 반영하고, cache hit는 추후 LLMServingSim 또는 serving benchmark로 보정한다.

### 질문 10. Agentic/COT에서 output TPS와 total TPS 중 무엇을 capacity 기준으로 삼아야 하는가?

사전 가설:
사용자에게 반환되는 generated token capacity는 output TPS를 쓰고, infrastructure load는 input/total TPS를 별도로 봐야 한다.

미팅 후 확인:
교수님 설명상 이 구분은 매우 중요하다. Decode는 output token 생성과 직접 연결되고, prefill/input은 long context와 KV cache pressure를 만든다. Total TPS가 커도 대부분 input token이면 generated token capacity로 그대로 쓰면 안 된다.

프로젝트 반영:
headline은 generated output tokens/day로 유지한다. 다만 agentic/long-context workload에서는 input/prefill pressure, KV memory, TTFT/TPOT를 별도 diagnostic으로 둔다.

## 3. 사업적 시사점

### 3.1 시장은 코딩 에이전트만으로 끝나지 않을 가능성

교수님은 코딩 에이전트가 현재 token을 많이 쓰는 대표 영역이지만, 교육, 의료, 업무 자동화 등 다른 도메인에서도 agentic AI가 확장될 수 있다고 보았다. 따라서 agentic workload는 단기 유행이 아니라 장기 token demand를 키울 수 있는 중요한 축이다.

### 3.2 핵심 고객은 hyperscaler가 아닌 대형 IT 기업

Google, Meta, OpenAI, Anthropic 같은 hyperscaler/frontier lab은 자체 연구와 인프라 역량이 강하다. 반면 수천 명의 엔지니어를 가진 대형 IT 기업은 Claude/OpenAI API 비용 부담이 커질 경우 오픈소스 모델, 네오클라우드, GPU 서버, serving software 조합을 찾을 가능성이 있다.

### 3.3 스타트업 기회는 hardware 자체보다 serving software layer

네오클라우드는 데이터센터, 전력, 냉각, GPU 서버를 담당한다. 별도의 기회는 그 위에서 open model을 GPU/TPU/NPU에 맞게 효율적으로 serving하는 software layer에 있다. 하드웨어가 달라질수록 software optimization 난도가 커지며, 이 부분이 차별화 포인트가 될 수 있다.

## 4. 전력 기반 token capacity 모델에 반영할 최종 원칙

### 4.1 핵심 산식

```text
generated_output_tokens_per_day
= inference_gw * 1,000 * serving_output_tps_per_mw * 86,400
```

이 산식은 유지하되, `serving_output_tps_per_mw`는 단일 상수가 아니라 다음 계층으로 만든다.

```text
serving_output_tps_per_mw
= fleet_reference_tps_per_mw * commercial_workload_fit_factor

fleet_reference_tps_per_mw
= sum(gpu_generation_share * workload_weighted_gpu_tps_per_mw)

workload_weighted_gpu_tps_per_mw
= short_share * short_chat_tps_per_mw
 + long_share * long_chat_tps_per_mw
 + agentic_share * agentic_tps_per_mw
```

### 4.2 Workload 분리

| Workload | 의미 | 현재 모델 사용 |
|---|---|---|
| Short chat | 짧은 대화/API 응답, latency 민감 | ISL/OSL 1024/1024 benchmark anchor |
| Long chat | RAG, research, 긴 문맥 | ISL/OSL 8192/1024 또는 long-context haircut |
| Agentic | coding/tool/subagent/multi-call workflow | agentic trace의 긴 input shape + long-context TPS haircut |

### 4.3 Interactivity와 concurrency

미팅 후 결론은 interactivity/concurrency를 숨기면 안 된다는 것이다. TPS/MW를 고를 때 다음 정보를 같이 남겨야 한다.

- target tok/s/user 또는 realized tok/s/user
- concurrency
- GPU count
- TTFT, TPOT, p95/p99 latency
- benchmark row id
- framework/precision
- ISL/OSL
- offline/online 또는 interactive serving 여부

현재 headline 모델은 p50 TPS/MW 기준의 scenario estimate로 두되, 다음 버전에서는 row selection sheet를 만들어 benchmark 조건을 추적 가능하게 해야 한다.

### 4.4 Agentic workload 보정

Agentic workload는 단순히 output token이 많은 것이 아니라, 내부 call 수와 input context가 늘어나는 workload다.

반영해야 할 요소:

- calls/request 증가
- tool wait로 인한 GPU idle/standby
- prefix caching hit rate
- KV cache memory pressure
- long input/prefill cost
- branch concurrency
- SLO-valid throughput

현재는 agentic trace를 throughput telemetry가 아니라 workload shape proxy로 쓰는 것이 맞다.

## 5. 남은 후속 질문

다음 미팅 또는 follow-up에서 확인하면 좋은 질문은 다음이다.

1. InferenceX row selection에서 interactivity를 `30/50/70 tok/s/user`로 나누는 방식이 serving-system 관점에서 적절한가?
2. Agentic `calls/request` 증가를 단순 multiplier로 넣어도 되는가, 아니면 LLMServingSim trace로 풀어야 하는가?
3. Tool wait로 인한 GPU idle/standby power를 TPS/MW에 어떻게 반영해야 하는가?
4. Prefix caching은 prefill latency 절감과 KV memory pressure 완화를 어떻게 나눠 모델링해야 하는가?
5. Agentic workload에서 output token capacity보다 KV cache memory가 먼저 병목이 되는 조건은 무엇인가?
6. Closed model의 parameter size를 모를 때, proxy model을 어떤 기준으로 선택해야 하는가?
7. GPU 수를 늘리는 정방향 sweep으로 목표 TPS를 맞추는 최소 GPU 수 추정은 어느 정도까지 신뢰 가능한가?
8. All-in power/MW 기준으로 전환할 때 GPU board power, server power, rack power, facility IT load를 어떻게 분리해야 하는가?

## 6. 최종 메시지

박종세 교수님 미팅을 통해 프로젝트의 방향은 더 명확해졌다. 전력 기반 token capacity forecast는 할 수 있지만, “정확한 회사별 생산량”처럼 말하면 위험하다. 더 적절한 표현은 다음이다.

> 공개 benchmark, 전력 capacity envelope, GPU generation mix, workload mix, commercial workload fit을 결합한 scenario-based generated output token capacity estimate.

이 표현이 현재 프로젝트의 신뢰도를 가장 잘 지킨다. 숫자는 계속 바뀔 수 있지만, 구조는 유지해야 한다.

