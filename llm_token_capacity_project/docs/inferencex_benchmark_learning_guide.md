# InferenceX Benchmark Learning Guide

**Updated:** 2026-05-28

이 문서는 InferenceX 데이터를 처음 보는 팀원도 LLM benchmark를 읽을 수 있게 만드는 학습 자료입니다. 목적은 단순히 "어떤 GPU가 빠르다"를 외우는 것이 아니라, **속도, 지연시간, 전력 효율, 비용, 정확도, GPU 호환성**을 함께 읽는 법을 익히는 것입니다.

이 프로젝트에서 사용하는 InferenceX 데이터는 다음 위치에 정규화되어 있습니다.

```text
llm_token_capacity_project/data/inferencex/normalized/
```

가장 중요한 원칙은 하나입니다.

```text
InferenceX = public benchmark/proxy
회사 production token volume = 아님
```

즉, InferenceX는 "이 모델/이 GPU/이 precision/이 sequence 조건에서 어느 정도 처리량과 효율이 나왔는가"를 보여주는 benchmark입니다. OpenAI, Google, Anthropic, Meta 같은 회사가 실제 상용 서비스에서 몇 token을 만들었는지 직접 알려주는 telemetry가 아닙니다.

---

## 목차

1. InferenceX가 무엇인가
2. 이 프로젝트에 들어온 데이터 구성
3. 초보자를 위한 핵심 용어 사전
4. Benchmark를 읽는 기본 프레임
5. LLM 속도 지표 읽기
6. 지연시간과 사용자 경험 읽기
7. 전력 효율과 tokens/MW 읽기
8. 비용 지표와 TCO 읽기
9. 정확도 eval을 함께 봐야 하는 이유
10. GPU 호환성과 availability 읽기
11. GPU별 run success를 어떻게 해석할까
12. 대표 benchmark 숫자: 고정 조건 비교
13. 모델별 읽는 법: Llama, GPT-OSS, DeepSeek R1 계열 등
14. GPU별 읽는 법: H100/H200/B200/GB200/B300/GB300/AMD MI 계열
15. Precision별 읽는 법: BF16, FP8, FP4, INT4
16. Framework별 읽는 법: vLLM, TensorRT-LLM, SGLang, Dynamo
17. ISL/OSL과 context length가 왜 중요한가
18. 우리 token capacity 모델에 InferenceX를 연결하는 법
19. 잘못 읽기 쉬운 함정
20. 실무 체크리스트
21. 직접 분석할 때 쓰는 간단한 쿼리 예시

---

## 1. InferenceX가 무엇인가

InferenceX는 SemiAnalysis 쪽에서 제공하는 LLM inference benchmark/dashboard 계열 데이터입니다. 이 프로젝트에서는 공개 release dump를 받아 정규화했습니다.

현재 로컬 기준으로 확인된 dump는 다음과 같습니다.

| 항목 | 값 |
|---|---|
| Release tag | `db-dump/2026-06-08` |
| Dump file | `inferencex-dump-2026-06-08.tar.xz.part00` |
| Benchmark rows | `76,406` |
| Metric profile groups | `338` |
| GPU-comparable metric groups | `128` |
| Main config validation rows | `9 PASS` |
| Accuracy eval rows | `1,613` |
| Availability rows | `6,055` |
| Run stats rows | `6,221` |
| Evidence class | `Proxy/Benchmark` |

InferenceX가 유용한 이유는 benchmark row가 매우 세밀하기 때문입니다. 단순히 "B200이 빠르다"가 아니라, 아래 조합별로 볼 수 있습니다.

```text
model
gpu
framework
precision
input sequence length (ISL)
output sequence length (OSL)
concurrency
throughput
latency
power
cost
accuracy
```

이 조합을 제대로 맞춰야만 의미 있는 비교가 됩니다.

---

## 2. 이 프로젝트에 들어온 데이터 구성

### 핵심 파일

| 파일 | row 수 | 용도 |
|---|---:|---|
| `inferencex_benchmark_results.csv` | 76,406 | 원천 benchmark row. 속도, 지연시간, 전력, 비용 지표가 가장 자세히 들어 있음 |
| `inferencex_metric_profile.csv` | 338 | 모델/GPU/framework/precision/ISL/OSL별 p10/p50/p90 요약 |
| `inferencex_gpu_comparable_metric_profile.csv` | 128 | 모델별 `main_framework`/`main_precision`이 고정된 GPU 비교용 요약 |
| `inferencex_main_config_by_model.csv` | 9 | 모델별 canonical framework/precision 선택 결과 |
| `inferencex_main_config_validation.csv` | 9 | 모델별 main config 검증 결과. GPU 비교 전 PASS 확인용 |
| `inferencex_accuracy_evals.csv` | 1,613 | 정확도 eval. precision/framework 변경 시 quality guardrail |
| `inferencex_availability.csv` | 6,055 | 어떤 모델/precision/sequence/framework가 어떤 hardware에서 지원되는지 |
| `inferencex_run_stats.csv` | 6,221 | hardware별 benchmark run 성공/실패 통계 |
| `inferencex_normalized_schema.csv` | schema | normalized benchmark column 정의 |

### Raw 참고 문서

| 파일 | 읽어야 하는 이유 |
|---|---|
| `raw/INFERENCEX_APP_GPU_SPECS_DOC_gpu-specs.md` | GPU spec, topology, NVL72, SXM, scale-up/scale-out 설명 |
| `raw/INFERENCEX_APP_TCO_DOC_tco-calculator.md` | TCO calculator가 throughput/cost/token/power를 어떻게 해석하는지 |
| `raw/INFERENCEX_APP_TRANSFORMS_DOC_data-transforms.md` | dashboard용 데이터 변환 논리 확인 |
| `raw/INFERENCEX_APP_DATA_PIPELINE_DOC_data-pipeline.md` | 데이터 파이프라인 구조 확인 |

---

## 3. 초보자를 위한 핵심 용어 사전

### Token

LLM이 읽고 쓰는 작은 텍스트 단위입니다. 영어 단어 하나가 token 하나일 수도 있고, 단어 일부가 token이 될 수도 있습니다.

중요한 점은 token에도 종류가 있다는 것입니다.

| Token 종류 | 쉬운 설명 | 왜 중요한가 |
|---|---|---|
| Input token | 사용자가 모델에 넣는 prompt/context token | 긴 문서를 넣으면 input token이 많아짐 |
| Output token | 모델이 새로 생성하는 답변 token | 우리가 "token 생성량"이라고 할 때 가장 자주 보는 대상 |
| Total token | input + output을 합친 처리량 | benchmark에서는 유용하지만 output capacity로 바로 쓰면 과대평가 가능 |
| Generated output token | 모델이 실제 생성한 출력 token | 이 프로젝트 headline token capacity의 기준 |

### ISL

`Input Sequence Length`의 약자입니다.

```text
ISL = 모델에 넣는 prompt/context 길이
```

예를 들어 `ISL=1024`는 입력 prompt가 1,024 token 수준이라는 뜻입니다. `ISL=8192`는 더 긴 context를 넣는 조건입니다.

긴 ISL은 보통 prefill 부담을 키웁니다. 쉽게 말하면 "읽어야 할 자료가 길수록 답변을 시작하기 전 준비 시간이 늘어날 수 있다"는 뜻입니다.

### OSL

`Output Sequence Length`의 약자입니다.

```text
OSL = 모델이 생성하는 답변 길이
```

`OSL=1024`는 출력이 1,024 token인 benchmark 조건입니다. `OSL=8192`는 장문 생성 조건입니다.

OSL이 길면 decode 단계가 길어집니다. 실무적으로는 장문 답변, reasoning trace, code generation, report generation workload에 가깝습니다.

### Prefill

모델이 입력 prompt를 읽는 단계입니다.

```text
prefill = input token을 한 번에 읽고 KV cache를 만드는 단계
```

긴 문서 요약, RAG, agent memory, 긴 chat history에서는 prefill 부담이 커집니다.

### Decode

모델이 output token을 하나씩 생성하는 단계입니다.

```text
decode = 답변 token을 순차적으로 생성하는 단계
```

사용자 입장에서 "답변이 얼마나 빨리 흘러나오는가"와 관련이 큽니다.

### Throughput

처리량입니다. 보통 초당 token 수로 봅니다.

| 지표 | 의미 |
|---|---|
| `tok_s_gpu` | GPU 1개당 초당 처리 token |
| `tok_s_mw` | 1MW당 초당 처리 token |
| `output_tok_s_mw` | 1MW당 초당 output token |
| `input_tok_s_mw` | 1MW당 초당 input token |

이 프로젝트의 headline token capacity에는 `output_tok_s_mw`를 가장 중요하게 봅니다. 이유는 우리가 최종적으로 알고 싶은 것이 "상용 LLM이 하루에 얼마나 많은 output token을 생성할 수 있는가"이기 때문입니다.

### Latency

사용자가 느끼는 지연시간입니다.

| 지표 | 의미 | 쉬운 해석 |
|---|---|---|
| `TTFT` | Time To First Token | 사용자가 질문한 뒤 첫 token이 나오기까지 시간 |
| `TPOT` | Time Per Output Token | output token 하나를 생성하는 데 걸리는 시간 |
| `E2EL` | End-to-End Latency | 요청 시작부터 답변 완료까지 전체 시간 |
| `p99` | 99번째 백분위 | 100명 중 99번째로 느린 사용자까지 포함한 보수적 지표 |

평균 latency만 보면 위험합니다. 실제 서비스에서는 p99가 중요합니다. 사용자는 평균이 아니라 "가끔 너무 느린 경험"에 민감하기 때문입니다.

### Precision

모델 계산에 쓰는 숫자 표현 방식입니다.

| Precision | 쉬운 설명 | 장점 | 주의점 |
|---|---|---|---|
| BF16 | 비교적 높은 정밀도 | 안정적, quality 보존 | 느리고 메모리/전력 부담 큼 |
| FP8 | 낮은 정밀도 | throughput/효율 개선 | calibration 필요 |
| FP4 | 더 낮은 정밀도 | 매우 높은 throughput 가능 | accuracy guardrail 필요 |
| INT4 | integer quantization | 메모리 절약 | 모델/프레임워크별 품질 리스크 |

Precision을 낮추면 대체로 빠르고 싸질 수 있지만, 항상 좋은 것은 아닙니다. 정확도 eval을 함께 봐야 합니다.

### Framework

LLM serving을 실행하는 software stack입니다.

| Framework | 의미 |
|---|---|
| vLLM | 범용 LLM serving framework. PagedAttention 등으로 잘 알려짐 |
| TensorRT-LLM / TRT | NVIDIA 최적화 inference stack |
| SGLang | structured generation, serving optimization에 쓰이는 framework |
| Dynamo | disaggregated serving 등과 연관된 stack |

같은 GPU와 모델이라도 framework가 바뀌면 throughput, latency, 안정성이 달라질 수 있습니다.

### Concurrency

동시에 처리하는 요청 수입니다.

```text
concurrency = 동시에 들어온 사용자 요청 수
```

Concurrency가 높으면 GPU 활용률은 좋아질 수 있지만, 사용자별 latency가 나빠질 수 있습니다. 그래서 throughput만 보고 좋은 설정이라고 판단하면 안 됩니다.

### Tokens/sec/MW

전력 효율 지표입니다.

```text
tokens/sec/MW = 1MW 전력을 쓸 때 초당 몇 token을 처리하는가
```

데이터센터 관점에서 매우 중요합니다. 전력이 AI 공급의 병목이면, 같은 MW에서 더 많은 output token을 만드는 GPU/stack이 더 가치 있습니다.

### Joules/token

token 하나를 만들 때 드는 에너지입니다.

```text
joules/token = token당 에너지
```

`tokens/sec/MW`와 거의 반대 방향의 지표입니다.

```text
1 MW = 1,000,000 J/s
joules per output token ≈ 1,000,000 / output tokens/sec/MW
```

예를 들어 `output_tok_s_mw = 1,000,000`이면 output token 하나당 약 `1 J`입니다.

---

## 4. Benchmark를 읽는 기본 프레임

InferenceX benchmark row 하나를 볼 때는 아래 순서로 읽습니다.

```text
1. 어떤 model인가?
2. 어떤 GPU인가?
3. 어떤 framework인가?
4. 어떤 precision인가?
5. ISL/OSL이 몇인가?
6. concurrency는 얼마인가?
7. output throughput은 얼마인가?
8. latency는 감당 가능한가?
9. joules/token과 cost/token은 어떤가?
10. accuracy eval이 품질을 지지하는가?
```

초보자가 가장 자주 하는 실수는 7번만 보고 결론을 내리는 것입니다. 하지만 실제 상용 서비스에서는 8~10번이 같이 맞아야 합니다.

---

## 5. LLM 속도 지표 읽기

속도는 한 가지 숫자가 아닙니다.

| 질문 | 봐야 할 지표 |
|---|---|
| GPU 한 장이 얼마나 많은 token을 처리하나? | `tok_s_gpu`, `output_tok_s_gpu` |
| 전력 1MW 기준으로 얼마나 처리하나? | `tok_s_mw`, `output_tok_s_mw` |
| 사용자에게 첫 답변이 빨리 나오나? | `p99_ttft_ms` |
| 답변이 빠르게 이어지나? | `p99_tpot_ms` |
| 전체 답변 완료가 빠른가? | `p99_e2el_s` |

### 왜 output throughput이 중요한가

이 프로젝트는 `generated output tokens/day`를 forecast합니다. 그러므로 input+output total throughput을 그대로 쓰면 output 생성 능력을 과대평가할 수 있습니다.

예시:

```text
total_tok_s_mw = input token 처리 + output token 생성
output_tok_s_mw = output token 생성만
```

상용 LLM token 공급제약을 보려면 `output_tok_s_mw`가 더 직접적입니다.

---

## 6. 지연시간과 사용자 경험 읽기

throughput이 높아도 latency가 나쁘면 상용 서비스에는 부적합할 수 있습니다.

### TTFT

TTFT는 첫 token까지 걸리는 시간입니다.

```text
TTFT가 낮다 = 사용자가 "응답이 시작됐다"고 빨리 느낌
```

검색형 Q&A, chatbot, copilot에는 TTFT가 중요합니다.

### TPOT

TPOT는 output token 하나당 시간입니다.

```text
TPOT가 낮다 = 답변이 빠르게 흘러나옴
```

긴 답변, code generation, report generation에서는 TPOT가 중요합니다.

### p99를 봐야 하는 이유

평균값은 "보통 사용자"를 보여줍니다. p99는 "거의 최악에 가까운 사용자 경험"을 보여줍니다.

실제 서비스에서는 다음 둘 중 하나만 좋아서는 부족합니다.

| 상황 | 문제 |
|---|---|
| 평균은 빠른데 p99가 느림 | 일부 사용자가 매우 나쁜 경험을 함 |
| p99는 안정적인데 throughput이 낮음 | capacity와 cost가 나빠짐 |

상용 LLM serving은 throughput과 p99 latency의 균형 문제입니다.

---

## 7. 전력 효율과 tokens/MW 읽기

AI 데이터센터에서는 전력이 병목이 됩니다. 그러면 "GPU가 몇 개인가"보다 "같은 MW로 얼마나 많은 output token을 만들 수 있는가"가 중요해집니다.

### 핵심 식

```text
output_tokens_per_day =
  inference_MW
  * output_tokens_per_second_per_MW
  * 86,400
```

예를 들어 `1 MW`에서 `100,000 output tok/s/MW`가 나오면:

```text
1 * 100,000 * 86,400 = 8,640,000,000 output tokens/day
```

즉, 하루 약 `8.64B output tokens/day`입니다.

### 왜 GPU mix가 중요할까

같은 1MW라도 H200, B200, GB200, AMD MI355X 구성에 따라 `output_tok_s_mw`가 달라집니다.

그래서 이 프로젝트의 token capacity 모델은 아래처럼 계산합니다.

```text
fleet_reference_tps_per_mw =
  h200_share * h200_reference_tps_per_mw
  + b200_share * b200_reference_tps_per_mw
  + gb200_share * gb200_reference_tps_per_mw
  + purpose_built_share * purpose_built_reference_tps_per_mw
```

전력량은 "얼마나 큰 엔진을 켤 수 있는가"이고, GPU mix는 "그 엔진이 얼마나 효율적인가"입니다.

---

## 8. 비용 지표와 TCO 읽기

InferenceX에는 cost 관련 지표도 있습니다.

| 지표 | 의미 |
|---|---|
| `cost_per_million_tokens_usd` | 백만 token당 비용 |
| `cost_hyperscaler_per_mtok_usd` | hyperscaler 비용 가정 기준 |
| `cost_neocloud_per_mtok_usd` | neocloud 비용 가정 기준 |
| `cost_retail_per_mtok_usd` | retail/3년 rental류 비용 가정 기준 |

비용은 throughput과 전력, GPU 가격, 사용률 가정이 섞인 결과입니다.

초보자에게 가장 중요한 점은:

```text
cost/token은 benchmark 결과 + 비용 가정의 조합이다.
순수 성능 지표가 아니다.
```

따라서 비용 지표를 볼 때는 반드시 어떤 cost provider 가정을 썼는지 확인해야 합니다.

---

## 9. 정확도 eval을 함께 봐야 하는 이유

속도만 높이는 방법은 많습니다.

- precision을 낮춘다
- 더 공격적인 quantization을 쓴다
- latency SLO를 느슨하게 둔다
- batch/concurrency를 크게 잡는다

하지만 정확도가 나빠지면 상용 서비스에는 쓸 수 없습니다.

현재 로컬 `accuracy_evals`는 `gsm8k` 중심입니다.

| 항목 | 값 |
|---|---:|
| Accuracy eval rows | 1,048 |
| 확인된 task | `gsm8k` |
| 유효 score row | 825 |
| `n_eff` 대표값 | 1,319 |

`gsm8k`는 수학 word problem benchmark입니다. 모든 LLM 품질을 대표하지는 않습니다. 그래도 precision/framework/GPU 변경이 품질을 크게 망가뜨리지 않는지 보는 guardrail로 유용합니다.

### 예시: 정확도는 speed의 안전장치

어떤 FP4 설정이 FP8보다 훨씬 빠르더라도, accuracy가 무너지면 production에는 위험합니다.

따라서 benchmark table을 볼 때는 이렇게 읽습니다.

```text
1. output_tok_s_mw가 높은가?
2. p99 latency가 괜찮은가?
3. 같은 모델/조건에서 accuracy score가 유지되는가?
4. row_count가 충분한가?
```

---

## 10. GPU 호환성과 availability 읽기

`inferencex_availability.csv`는 "어떤 모델/precision/sequence/framework 조합이 어떤 hardware에서 available한가"를 보여줍니다.

### Availability row 분포

| Hardware | Availability rows |
|---|---:|
| B200 | 1,700 |
| H200 | 1,080 |
| MI355X | 967 |
| MI325X | 562 |
| MI300X | 557 |
| GB200 | 333 |
| H100 | 319 |
| B300 | 79 |
| GB300 | 23 |

### 모델별 availability row

| Model | Availability rows |
|---|---:|
| DSR1 | 2,657 |
| GPT-OSS-120B | 1,731 |
| Llama 70B | 872 |
| Qwen 3.5 | 100 |
| DSV4 | 82 |
| MiniMax M2.5 | 80 |
| Kimi K2.5 | 55 |
| GLM5 | 39 |
| GLM5.1 | 4 |

Availability는 performance가 아닙니다.

```text
available = 실행 가능한 조합이 존재한다
fast = 높은 throughput이 나온다
production-ready = latency/accuracy/cost/운영 안정성까지 통과한다
```

이 세 가지는 서로 다릅니다.

---

## 11. GPU별 run success를 어떻게 해석할까

`inferencex_run_stats.csv`는 benchmark run이 얼마나 성공했는지 보여줍니다.

| Hardware | Success | Total | Success rate |
|---|---:|---:|---:|
| B200 | 23,787 | 28,864 | 82.4% |
| H200 | 14,221 | 19,488 | 73.0% |
| MI355X | 15,397 | 19,341 | 79.6% |
| MI325X | 7,565 | 9,725 | 77.8% |
| MI300X | 7,133 | 9,297 | 76.7% |
| H100 | 4,716 | 6,495 | 72.6% |
| GB200 | 1,472 | 2,455 | 60.0% |
| B300 | 1,532 | 2,203 | 69.5% |
| GB300 | 188 | 203 | 92.6% |

주의할 점이 있습니다.

성공률이 높다고 항상 "상용 production이 안정적"이라는 뜻은 아닙니다. Benchmark 환경의 run success일 뿐입니다. 특히 row 수가 적은 hardware는 표본이 작기 때문에 과도한 해석을 피해야 합니다.

예를 들어 GB300 success rate는 92.6%로 높지만 total row가 203입니다. B200의 total 28,864와 비교하면 표본 크기가 훨씬 작습니다.

---

## 12. 대표 benchmark 숫자: 고정 조건 비교

비교가 공정하려면 조건을 맞춰야 합니다. 아래 표는 다음 조건으로 뽑은 대표 비교입니다.

```text
benchmark_type = single_turn
ISL = 1024
OSL = 1024
metric = output_tok_s_mw
summary = median / p50
```

이 조건은 "입력 1,024 token, 출력 1,024 token"인 비교적 표준화된 generated-output 처리량 비교입니다.

### 상위 대표 조합

| Model | GPU | Rows | p50 output tok/s/MW | p10 | p90 |
|---|---|---:|---:|---:|---:|
| GPT-OSS-120B | GB200 | 21 | 5,789,330 | 134,163 | 17,538,228 |
| DSR1 | GB200 | 1,711 | 731,323 | 26,098 | 2,431,368 |
| DSR1 | GB300 | 68 | 729,849 | 17,681 | 4,078,092 |
| GPT-OSS-120B | B200 | 1,961 | 724,940 | 138,964 | 2,613,201 |
| MiniMax M2.5 | B300 | 66 | 666,550 | 89,202 | 3,130,054 |
| GPT-OSS-120B | H200 | 1,853 | 369,352 | 110,298 | 1,182,881 |
| MiniMax M2.5 | B200 | 168 | 365,335 | 86,857 | 1,884,142 |
| Kimi K2.5 | GB200 | 50 | 349,599 | 19,352 | 3,293,724 |
| GPT-OSS-120B | MI355X | 663 | 339,009 | 91,418 | 1,972,802 |
| GPT-OSS-120B | H100 | 820 | 328,522 | 109,131 | 854,978 |
| Llama 70B | H200 | 521 | 284,640 | 68,630 | 897,618 |
| Llama 70B | B200 | 1,094 | 282,860 | 67,188 | 1,137,829 |
| GPT-OSS-120B | MI325X | 1,196 | 280,916 | 87,437 | 854,797 |
| GPT-OSS-120B | MI300X | 970 | 278,325 | 95,477 | 940,715 |
| Qwen 3.5 | B300 | 62 | 234,583 | 73,899 | 795,242 |
| MiniMax M2.5 | MI355X | 261 | 184,562 | 33,429 | 905,438 |
| Qwen 3.5 | B200 | 90 | 179,145 | 43,746 | 761,941 |
| Llama 70B | H100 | 210 | 169,703 | 48,093 | 453,224 |
| Llama 70B | MI300X | 280 | 165,680 | 53,013 | 513,406 |
| Llama 70B | MI325X | 278 | 157,592 | 46,489 | 494,307 |
| Llama 70B | MI355X | 488 | 156,666 | 41,081 | 509,533 |
| DSR1 | B200 | 2,184 | 101,245 | 28,685 | 448,974 |
| DSR1 | H200 | 662 | 60,574 | 19,998 | 140,158 |
| DSR1 | MI355X | 1,851 | 56,269 | 13,343 | 397,151 |

### 이 표를 읽을 때의 주의점

1. `GPT-OSS-120B + GB200`의 p50은 매우 높지만 row 수가 21입니다. strong signal이라기보다 "관찰된 benchmark 후보"로 읽어야 합니다.
2. `DSR1 + GB200`은 row 수가 1,711로 훨씬 많아 상대적으로 안정적으로 볼 수 있습니다.
3. 같은 GPU라도 model이 바뀌면 throughput이 크게 달라집니다.
4. p10~p90 범위가 넓으면 workload, concurrency, framework 차이의 영향이 큽니다.
5. 이 표만으로 상용 서비스 성능을 확정하면 안 됩니다. latency와 accuracy를 같이 봐야 합니다.

---

## 13. 모델별 읽는 법

### GPT-OSS-120B

로컬 benchmark row에서 가장 많은 모델입니다.

| 항목 | 값 |
|---|---:|
| Benchmark rows | 28,713 |
| 주요 GPU | B200, H200, MI355X, MI325X, MI300X, H100, GB200 |
| 특징 | 여러 GPU에서 폭넓게 측정되어 hardware 비교에 유용 |

고정조건 `ISL=1024`, `OSL=1024`에서는 B200, H200, MI 계열, H100 비교가 풍부합니다. 단, GB200 row 수는 21로 적습니다.

실무 해석:

- B200/H200/MI 계열 비교에 좋습니다.
- GB200 수치는 매우 높은 값이 있지만 row 수가 적으므로 Base coefficient로 쓰기에는 신중해야 합니다.
- 이 프로젝트에서는 row 수가 충분하지 않은 조합은 B200 placeholder를 쓰는 보수적 정책을 둡니다.

### DSR1

DeepSeek R1 계열 proxy로 사용하기 좋은 모델입니다.

| 항목 | 값 |
|---|---:|
| Benchmark rows | 21,248 |
| GB200 fixed-condition rows | 1,711 |
| B200 fixed-condition rows | 2,184 |
| H200 fixed-condition rows | 662 |

DSR1은 GB200/B200/H200 비교 row가 충분합니다. reasoning model 성격이 강한 workload를 볼 때 참고하기 좋습니다.

실무 해석:

- reasoning 계열은 output token 생성 효율이 일반 chat 모델과 다르게 보일 수 있습니다.
- 같은 GPU에서 GPT-OSS-120B보다 output tok/s/MW가 낮을 수 있습니다.
- reasoning model의 token은 단순 답변보다 길고 복잡한 decode 부담을 가질 수 있습니다.

### Llama 70B

Llama 70B는 open model benchmark의 기준점으로 유용합니다.

| 항목 | 값 |
|---|---:|
| Benchmark rows | 17,499 |
| B200 fixed-condition p50 | 282,860 output tok/s/MW |
| H200 fixed-condition p50 | 284,640 output tok/s/MW |
| MI355X fixed-condition p50 | 156,666 output tok/s/MW |

실무 해석:

- Llama 70B는 비교적 잘 알려진 dense/open model benchmark anchor입니다.
- closed frontier model 직접 proxy로 쓰기보다는 open baseline으로 쓰는 것이 안전합니다.
- H200과 B200의 fixed-condition p50이 비슷하게 보이는 구간이 있어, "항상 B200이 압도적"이라고 단순화하면 안 됩니다. 조건과 software stack을 봐야 합니다.

### Qwen 3.5

Qwen 계열은 Alibaba/Qwen workload를 생각할 때 참고하기 좋지만, 로컬 row 수는 GPT-OSS/DSR1/Llama보다 적습니다.

| 항목 | 값 |
|---|---:|
| Benchmark rows | 740 |
| B200 fixed-condition rows | 90 |
| B200 fixed-condition p50 | 179,145 output tok/s/MW |
| H200 fixed-condition rows | 29 |

실무 해석:

- Qwen workload의 직접 proxy로 유용할 수 있지만, hardware별 row coverage를 확인해야 합니다.
- H200 등 row 수가 적은 조합은 Base 입력으로 바로 쓰기보다 placeholder/보수값이 필요합니다.

---

## 14. GPU별 읽는 법

### H100

H100은 이전 세대의 기준점입니다. H200/B200/GB200으로 넘어갈 때 효율 개선을 비교하는 baseline 역할을 합니다.

### H200

H200은 HBM 용량/대역폭 측면에서 H100 대비 개선된 Hopper 계열입니다. 많은 benchmark row가 있어 B200 전환 전의 현실적 baseline으로 유용합니다.

### B200

B200은 Blackwell SXM 계열 비교의 핵심입니다.

로컬 데이터에서 B200은 benchmark row가 가장 많습니다.

| 항목 | 값 |
|---|---:|
| Benchmark rows | 22,794 |
| Availability rows | 1,700 |
| Run success | 23,787 / 28,864 |
| Success rate | 82.4% |

B200은 이 프로젝트에서 placeholder로 자주 쓰입니다. 이유는 "무조건 최고라서"가 아니라, 공개 row coverage가 가장 풍부하고 여러 모델에서 비교 가능하기 때문입니다.

### GB200

GB200 NVL72는 rack-scale NVLink domain이 핵심입니다. 단일 SXM GPU 비교와 다르게 읽어야 합니다.

Raw GPU specs 문서의 핵심:

- GB200/GB300 NVL72는 72 GPU가 하나의 NVLink domain 안에 있는 rack-scale system입니다.
- 일반적인 scale-out topology와 다르게 "rack 자체가 compute unit"입니다.
- SXM B200과 GB200 NVL72는 같은 Blackwell 계열이어도 memory, TDP, topology가 다릅니다.

실무 해석:

- GB200 benchmark는 특정 rack-scale serving 최적화의 영향을 크게 받을 수 있습니다.
- row 수가 충분하지 않은 model/GPU 조합은 보수적으로 다뤄야 합니다.
- 이 프로젝트에서는 GB200 direct row가 50개 미만이면 B200 placeholder를 우선 사용합니다.

### B300 / GB300

Blackwell Ultra 계열로 읽습니다.

Raw GPU specs 문서에서 중요한 문장:

```text
Blackwell Ultra는 FP4에서만 B200/GB200 대비 개선이 크고, FP8/BF16은 SXM 기준으로 unchanged로 취급한다.
```

실무 해석:

- B300/GB300을 볼 때 precision이 FP4인지 FP8인지 반드시 확인해야 합니다.
- 모든 precision에서 1.5배 좋아진다고 가정하면 안 됩니다.

### AMD MI300X / MI325X / MI355X

AMD 계열은 NVIDIA와 topology가 다릅니다.

Raw GPU specs 문서의 핵심:

- MI300X/MI325X/MI355X는 NVSwitch가 아니라 GPU 간 full mesh 구조로 설명됩니다.
- MI355X는 AMD GPU 중 FP4 지원과 관련해 중요한 세대입니다.

실무 해석:

- AMD는 framework/precision maturity가 성능을 크게 좌우할 수 있습니다.
- MI355X는 FP4 관련 benchmark에서 MI300X/MI325X와 다르게 봐야 합니다.
- GPU vendor 비교는 같은 model, same ISL/OSL, same precision, similar framework 조건에서만 의미가 있습니다.

---

## 15. Precision별 읽는 법

로컬 benchmark row의 precision 분포는 다음과 같습니다.

| Precision | Benchmark rows |
|---|---:|
| FP4 | 46,663 |
| FP8 | 24,747 |
| INT4 | 469 |
| BF16 | 212 |

### FP4

가장 많은 row를 차지합니다. 속도와 효율을 높이기 위한 핵심 precision입니다.

주의:

- 정확도 eval을 확인해야 합니다.
- 모델마다 FP4 안정성이 다릅니다.
- GPU마다 FP4 지원/성능이 다릅니다.

### FP8

FP4보다 보수적인 low precision입니다. production에서 품질과 성능 균형을 볼 때 중요합니다.

### BF16

row 수가 적습니다. 정확도 기준점으로는 유용하지만, InferenceX 로컬 dump에서는 주력 performance comparison으로 쓰기 어렵습니다.

### INT4

메모리와 비용에는 유리할 수 있지만 quality guardrail이 특히 중요합니다.

---

## 16. Framework별 읽는 법

로컬 benchmark row의 framework 분포는 다음과 같습니다.

| Framework | Benchmark rows |
|---|---:|
| vLLM | 36,270 |
| TRT | 17,727 |
| SGLang | 10,743 |
| Dynamo-TRT | 3,218 |
| Mori-SGLang | 1,825 |
| Dynamo-SGLang | 1,765 |
| Atom | 407 |
| Dynamo-vLLM | 136 |

Framework는 성능을 크게 바꿉니다.

예를 들어 같은 B200과 같은 model이라도 vLLM과 TRT의 latency/throughput trade-off가 다를 수 있습니다.

실무적으로는 다음 질문을 던져야 합니다.

```text
이 benchmark는 어떤 serving stack을 가정하는가?
우리 회사 또는 고객이 실제로 쓰는 stack과 같은가?
같지 않다면 workload fit factor를 얼마나 둬야 하는가?
```

---

## 17. ISL/OSL과 context length가 왜 중요한가

로컬 benchmark의 ISL/OSL 분포는 단순합니다.

| Field | 주요 값 |
|---|---|
| ISL | 1,024 또는 8,192 |
| OSL | 1,024 또는 8,192 |

row 분포:

| 조건 | Rows |
|---|---:|
| ISL 1,024 | 46,854 |
| ISL 8,192 | 25,237 |
| OSL 1,024 | 52,021 |
| OSL 8,192 | 20,070 |

### ISL이 길어질 때

입력이 길어지면 prefill 부담이 커집니다. RAG, long context chat, document analysis가 여기에 해당합니다.

### OSL이 길어질 때

출력이 길어지면 decode 부담이 커집니다. reasoning, code generation, report writing, agent planning이 여기에 해당합니다.

### 왜 같은 모델도 ISL/OSL별로 다르게 봐야 하나

`ISL=1024/OSL=1024`에서 좋은 GPU가 `ISL=8192/OSL=8192`에서도 항상 좋은 것은 아닙니다. memory bandwidth, KV cache, batching, framework optimization의 영향이 달라집니다.

---

## 18. 우리 token capacity 모델에 InferenceX를 연결하는 법

우리의 headline formula는 다음입니다.

```text
inference_gw =
  contracted_power_gw
  * operational_deployment_share
  / pue
  * ai_workload_share
  * inference_power_share

fleet_reference_tps_per_mw =
  h200_share * h200_reference_tps_per_mw
  + b200_share * b200_reference_tps_per_mw
  + gb200_share * gb200_reference_tps_per_mw
  + purpose_built_share * purpose_built_reference_tps_per_mw

serving_tps_per_mw =
  fleet_reference_tps_per_mw
  * commercial_workload_fit_factor

generated_output_tokens_per_day =
  inference_gw
  * 1,000
  * serving_tps_per_mw
  * 86,400
```

InferenceX는 이 중 `h200_reference_tps_per_mw`, `b200_reference_tps_per_mw`, `gb200_reference_tps_per_mw`의 public benchmark reference로 쓰입니다.

### 왜 바로 production 값으로 쓰지 않는가

InferenceX는 benchmark입니다. production은 다릅니다.

| 차이 | Benchmark | Production |
|---|---|---|
| 요청 패턴 | 통제된 조건 | 사용자 traffic이 불규칙 |
| context 길이 | 정해진 ISL/OSL | 요청마다 다름 |
| latency SLO | benchmark 조건 | 상품별 SLA/SLO 존재 |
| routing | 고정 config | 여러 모델/region/GPU로 분산 |
| failure handling | benchmark run | retry, failover, safety layer 포함 |
| business mix | 없음 | free/paid/API/enterprise traffic mix |

그래서 우리는 InferenceX public reference에 `commercial_workload_fit_factor`를 곱합니다.

```text
serving_tps_per_mw = public benchmark reference * commercial workload fit
```

이 fit factor는 benchmark와 실제 상용 workload 간 차이를 명시적으로 반영하는 safety layer입니다.

---

## 19. 잘못 읽기 쉬운 함정

### 함정 1. Total tokens/sec를 output token capacity로 착각

`total_tok_s_mw`는 input+output 처리량일 수 있습니다. output generation capacity에는 `output_tok_s_mw`가 더 적절합니다.

### 함정 2. row 수가 적은 최고값을 대표값으로 사용

row 수가 20개인 최고값과 row 수가 2,000개인 p50은 신뢰도가 다릅니다. 최고값보다 p50과 row_count를 먼저 보세요.

### 함정 3. p90을 production expectation으로 사용

p90은 좋은 조건의 상위 성능입니다. Base forecast에는 p50 또는 더 보수적인 값이 안전합니다.

### 함정 4. GPU 이름만 보고 비교

`B200`이라는 이름만 같아도 framework, precision, ISL/OSL, concurrency가 다르면 비교가 아닙니다.

### 함정 5. Precision을 낮추면 무조건 좋다고 생각

FP4가 빠를 수 있지만 accuracy와 안정성이 유지되어야 합니다.

### 함정 6. GB200 NVL72와 B200 SXM을 단순 칩 비교로 읽음

GB200 NVL72는 rack-scale system입니다. B200 SXM과 topology가 다르므로 "같은 Blackwell GPU" 수준으로 단순 비교하면 안 됩니다.

### 함정 7. Availability를 performance로 착각

available하다는 것은 실행 가능하다는 뜻이지 빠르다는 뜻이 아닙니다.

### 함정 8. Benchmark success rate를 production reliability로 착각

run success는 benchmark 환경의 성공률입니다. 상용 서비스 reliability와 직접 같지 않습니다.

---

## 20. 실무 체크리스트

Benchmark row를 보고 수치로 채택하기 전 아래를 확인합니다.

### 데이터 조건 체크

- model이 target workload와 유사한가?
- GPU가 target hardware와 같은가?
- framework가 production stack과 유사한가?
- precision이 production에서 쓸 수 있는 수준인가?
- ISL/OSL이 workload와 맞는가?
- concurrency가 현실적인가?
- row_count가 충분한가?

### 성능 체크

- output_tok_s_mw p50은 얼마인가?
- p10~p90 범위가 너무 넓지 않은가?
- p99 TTFT가 서비스에 적합한가?
- p99 TPOT가 답변 속도에 적합한가?
- joules/output token은 합리적인가?

### 품질 체크

- accuracy eval이 있는가?
- precision 변경 후 score가 유지되는가?
- eval task가 target service 품질을 대표할 수 있는가?

### 모델 반영 체크

- 이 값은 public benchmark인지 production telemetry인지 구분했는가?
- output token 기준인지 total token 기준인지 구분했는가?
- company-specific serving mix를 사실처럼 말하지 않았는가?
- commercial workload fit factor를 명시했는가?
- Base/Bull/Bear 중 어디에 반영할지 정했는가?

---

## 21. 직접 분석할 때 쓰는 간단한 쿼리 예시

아래 예시는 로컬 CSV를 직접 읽어보는 최소 코드입니다.

### 모델/GPU별 row 수 보기

```bash
.venv/bin/python - <<'PY'
import csv
from collections import Counter

path = 'llm_token_capacity_project/data/inferencex/normalized/inferencex_benchmark_results.csv'
with open(path, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(Counter(r['model'] for r in rows).most_common(10))
print(Counter(r['gpu'] for r in rows).most_common(10))
PY
```

### 고정 조건에서 output tok/s/MW p50 보기

```bash
.venv/bin/python - <<'PY'
import csv, statistics
from collections import defaultdict

path = 'llm_token_capacity_project/data/inferencex/normalized/inferencex_benchmark_results.csv'
groups = defaultdict(list)

with open(path, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if (
            r.get('benchmark_type') == 'single_turn'
            and r.get('isl') == '1024'
            and r.get('osl') == '1024'
            and r.get('output_tok_s_mw')
        ):
            groups[(r['model'], r['gpu'])].append(float(r['output_tok_s_mw']))

summary = []
for (model, gpu), values in groups.items():
    if len(values) >= 50:
        summary.append((statistics.median(values), len(values), model, gpu))

for p50, n, model, gpu in sorted(summary, reverse=True)[:20]:
    print(model, gpu, 'n=', n, 'p50=', round(p50))
PY
```

### Accuracy eval 상위 score 보기

```bash
.venv/bin/python - <<'PY'
import csv

path = 'llm_token_capacity_project/data/inferencex/normalized/inferencex_accuracy_evals.csv'
rows = []
with open(path, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r.get('score'):
            rows.append((float(r['score']), r['task'], r['model'], r['gpu'], r['framework'], r['precision']))

for item in sorted(rows, reverse=True)[:20]:
    print(item)
PY
```

---

## 마지막 요약

InferenceX를 잘 쓰는 방법은 "가장 큰 숫자 찾기"가 아닙니다.

좋은 benchmark 해석은 아래처럼 진행됩니다.

```text
1. 같은 model/GPU/framework/precision/ISL/OSL 조건끼리 비교한다.
2. output token 기준과 total token 기준을 구분한다.
3. p50, p10, p90, row_count를 함께 본다.
4. latency와 accuracy를 같이 본다.
5. benchmark를 production telemetry로 말하지 않는다.
6. token capacity 모델에는 public reference와 workload fit factor를 분리해서 넣는다.
```

이 문서의 결론은 단순합니다.

```text
InferenceX는 AI token supply 모델의 엔진 성능표다.
하지만 실제 도로, 운전자, 교통상황은 production workload가 결정한다.
```

따라서 InferenceX는 매우 강력한 근거이지만, 항상 `Proxy/Benchmark`로 다루고 company-specific capacity, GPU fleet mix, workload allocation과 구분해서 사용해야 합니다.
