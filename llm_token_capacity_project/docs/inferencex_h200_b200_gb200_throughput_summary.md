# InferenceX H200/B200/GB200 Throughput Summary

**Updated:** 2026-05-28

이 문서는 InferenceX 정규화 데이터만 사용해 H200, B200, GB200별 LLM 모델 throughput을 요약합니다.

## 기준 조건

아래 표는 비교가 너무 섞이지 않도록 다음 조건으로 필터링했습니다.

```text
source = InferenceX normalized benchmark results
file = data/inferencex/normalized/inferencex_benchmark_results.csv
benchmark_type = single_turn
ISL = 1024
OSL = 1024
GPU = H200, B200, GB200
metric = input_tok_s_mw, output_tok_s_mw, total_tok_s_mw
summary = p50 median
minimum rows displayed = 10
```

## 읽는 법

| Column | Meaning |
|---|---|
| `Input p50 tok/s/MW` | 1MW 기준 초당 input token 처리량의 중앙값 |
| `Output p50 tok/s/MW` | 1MW 기준 초당 generated output token 처리량의 중앙값 |
| `Input+Output p50 sum` | input p50과 output p50을 사람이 보기 쉽게 더한 값 |
| `InferenceX total p50` | InferenceX row의 `total_tok_s_mw` 중앙값 |
| `Output p10/p90` | output throughput의 하위 10% / 상위 10% 분위값 |
| `Main framework` | 해당 model/GPU 조합에서 row 수가 가장 많은 framework |
| `Main precision` | 해당 model/GPU 조합에서 row 수가 가장 많은 precision |

주의할 점:

```text
Input+Output p50 sum != InferenceX total p50
```

이유는 중앙값을 계산하는 방식 때문입니다. `Input p50`, `Output p50`, `Total p50`은 각각의 분포에서 따로 중앙값을 구합니다. 그래서 `input p50 + output p50`이 row 단위 `total p50`과 정확히 같지 않을 수 있습니다.

또한 이 표는 overview입니다. 같은 model/GPU 안에서도 framework, precision, concurrency가 섞여 있습니다. 엄밀한 coefficient 채택 전에는 반드시 framework, precision, concurrency까지 고정해 다시 봐야 합니다.

## H200/B200/GB200 Model Throughput Table

| Model | GPU | Rows | Input p50 tok/s/MW | Output p50 tok/s/MW | Input+Output p50 sum | InferenceX total p50 | Output p10 | Output p90 | Main framework | Main precision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| dsr1 | H200 | 622 | 65,215 | 61,074 | 126,289 | 121,793 | 19,998 | 140,258 | sglang | fp8 |
| dsr1 | B200 | 2,040 | 114,907 | 101,826 | 216,734 | 202,124 | 28,703 | 450,233 | trt | fp4 |
| dsr1 | GB200 | 1,595 | 1,345,368 | 716,038 | 2,061,406 | 1,331,264 | 23,728 | 2,520,737 | dynamo-trt | fp4 |
| dsv4 | H200 | 74 | 39,786 | 39,387 | 79,173 | 79,173 | 9,554 | 83,998 | vllm | fp8 |
| dsv4 | B200 | 181 | 92,218 | 92,506 | 184,724 | 184,724 | 8,354 | 718,459 | vllm | fp4 |
| dsv4 | GB200 | 27 | 64,325 | 64,530 | 128,855 | 64,427 | 2,509 | 1,712,253 | dynamo-vllm | fp4 |
| glm5 | B200 | 68 | 90,016 | 89,068 | 179,083 | 179,083 | 22,835 | 425,222 | sglang | fp4 |
| gptoss120b | H200 | 1,709 | 368,772 | 369,352 | 738,124 | 738,715 | 110,359 | 1,182,572 | vllm | fp4 |
| gptoss120b | B200 | 1,821 | 728,156 | 727,217 | 1,455,374 | 1,454,656 | 139,215 | 2,676,067 | vllm | fp4 |
| gptoss120b | GB200 | 21 | 22,612,404 | 5,789,330 | 28,401,733 | 8,975,733 | 134,163 | 17,538,228 | dynamo-trt | fp4 |
| kimik2.5 | H200 | 35 | 68,680 | 67,957 | 136,637 | 136,637 | 26,469 | 143,934 | vllm | int4 |
| kimik2.5 | B200 | 58 | 83,830 | 84,454 | 168,284 | 168,284 | 29,450 | 256,275 | vllm | fp4 |
| kimik2.5 | GB200 | 50 | 2,302,566 | 349,599 | 2,652,165 | 610,270 | 19,352 | 3,293,724 | dynamo-trt | fp4 |
| llama70b | H200 | 433 | 287,670 | 284,640 | 572,310 | 572,310 | 68,630 | 899,716 | trt | fp8 |
| llama70b | B200 | 918 | 280,534 | 280,639 | 561,173 | 561,405 | 67,133 | 1,133,755 | trt | fp8 |
| minimaxm2.5 | H200 | 29 | 144,056 | 142,538 | 286,594 | 286,594 | 34,517 | 376,447 | vllm | fp8 |
| minimaxm2.5 | B200 | 168 | 366,750 | 365,335 | 732,085 | 732,085 | 86,857 | 1,884,142 | vllm | fp8 |
| qwen3.5 | H200 | 29 | 88,620 | 87,745 | 176,365 | 176,365 | 34,986 | 207,679 | sglang | fp8 |
| qwen3.5 | B200 | 90 | 181,188 | 179,145 | 360,333 | 360,333 | 43,746 | 761,941 | sglang | fp8 |

## 빠른 해석

### 1. GPT-OSS-120B는 H200/B200 비교에 매우 유용하다

GPT-OSS-120B는 H200과 B200 모두 row 수가 많습니다.

| GPU | Rows | Output p50 tok/s/MW |
|---|---:|---:|
| H200 | 1,709 | 369,352 |
| B200 | 1,821 | 727,217 |
| GB200 | 21 | 5,789,330 |

B200은 H200 대비 output p50 기준 약 2배 수준입니다. 다만 GB200은 row 수가 21개라 매우 높은 값이 관찰되더라도 Base coefficient로 바로 쓰기에는 약합니다.

### 2. DSR1은 GB200 row가 많아 reasoning 계열 비교에 중요하다

DSR1은 GB200 row가 1,595개로 충분합니다.

| GPU | Rows | Output p50 tok/s/MW |
|---|---:|---:|
| H200 | 622 | 61,074 |
| B200 | 2,040 | 101,826 |
| GB200 | 1,595 | 716,038 |

reasoning 계열 proxy로 보면 GB200의 output throughput 개선이 매우 크게 나타납니다. 다만 output p10~p90 범위가 넓으므로 framework/precision/concurrency별 재분해가 필요합니다.

### 3. Llama 70B에서는 H200과 B200 p50이 비슷하게 보인다

| GPU | Rows | Output p50 tok/s/MW |
|---|---:|---:|
| H200 | 433 | 284,640 |
| B200 | 918 | 280,639 |

이 결과는 "B200은 모든 모델에서 항상 훨씬 빠르다"는 단순화를 막아줍니다. 같은 GPU라도 모델, framework, precision, concurrency 조건을 반드시 같이 봐야 합니다.

### 4. GB200 row는 모델별로 신뢰도가 크게 다르다

| Model | GB200 rows | Comment |
|---|---:|---|
| DSR1 | 1,595 | 충분히 큰 표본 |
| Kimi K2.5 | 50 | 최소 기준선 수준 |
| DSV4 | 27 | 낮은 표본 |
| GPT-OSS-120B | 21 | 낮은 표본 |

GB200 수치는 매우 매력적이지만, 모델별 row coverage 차이를 반드시 봐야 합니다.

## 이 표를 token capacity 모델에 반영할 때

우리의 headline output은 generated output token 기준입니다. 따라서 기본적으로 `Output p50 tok/s/MW`를 가장 우선합니다.

```text
generated_output_tokens_per_day =
  inference_gw
  * 1,000
  * output_tokens_per_second_per_mw
  * 86,400
```

단, 상용 서비스는 benchmark보다 더 복잡합니다. 그래서 실제 모델에서는 다음 layer를 분리합니다.

```text
public InferenceX reference
* commercial workload fit factor
= serving_tps_per_mw
```

## 채택 전 체크리스트

- 같은 model/GPU만 비교했는가?
- ISL=1024, OSL=1024 조건이 target workload와 맞는가?
- framework와 precision이 섞여 있는 overview 숫자임을 인지했는가?
- row_count가 충분한가?
- output p50뿐 아니라 p10/p90 범위도 봤는가?
- latency와 accuracy를 별도로 확인했는가?
- total token throughput을 generated output token capacity로 착각하지 않았는가?
- InferenceX benchmark를 company production telemetry처럼 말하지 않았는가?

## 다음 분석 후보

이 overview 다음에는 아래처럼 더 좁혀보는 것이 좋습니다.

1. `framework + precision`까지 고정한 H200/B200/GB200 비교
2. `ISL=8192`, `OSL=1024` long-context serving 비교
3. `OSL=8192` long-output/reasoning workload 비교
4. output p50뿐 아니라 p99 TTFT/TPOT를 포함한 service-fit table
5. accuracy eval과 throughput을 함께 보는 speed-quality frontier
