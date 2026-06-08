# InferenceX H200/B200/GB200 Throughput Summary

**Updated:** 2026-06-08

이 문서는 InferenceX 정규화 데이터만 사용해 H200, B200, GB200별 LLM 모델 throughput을 요약합니다.

핵심 변경: GPU별 비교가 섞이지 않도록 모든 표는 모델별 `main_framework`와 `main_precision`이 고정된 `is_main_model_config=yes` 행만 사용합니다.

## 기준 조건

```text
source = data/inferencex/normalized/inferencex_benchmark_results.csv
release = db-dump/2026-06-08
benchmark_type = single_turn
is_main_model_config = yes
GPU = H200, B200, GB200
metric = input_tok_s_mw, output_tok_s_mw, total_tok_s_mw
summary = p50 median
minimum rows displayed = 10
```

## 모델별 Main Config

| Model | Main framework | Main precision | GPU coverage | Rows |
|---|---|---|---:|---:|
| dsr1 | sglang | fp8 | 6 | 5,860 |
| dsv4 | dynamo-vllm | fp4 | 4 | 123 |
| glm5 | sglang | fp8 | 5 | 341 |
| glm5.1 | sglang | fp4 | 1 | 40 |
| gptoss120b | vllm | fp4 | 6 | 21,691 |
| kimik2.5 | vllm | int4 | 6 | 579 |
| llama70b | vllm | fp8 | 6 | 9,209 |
| minimaxm2.5 | vllm | fp8 | 7 | 1,453 |
| qwen3.5 | sglang | fp8 | 7 | 589 |

이 표의 `main_framework`/`main_precision` 조합만 사용해야 GPU별 비교가 가능합니다. 예를 들어 같은 model이라도 `trt/fp4`와 `vllm/fp8`을 섞으면 hardware 차이와 software/precision 차이가 분리되지 않습니다.

## 읽는 법

| Column | Meaning |
|---|---|
| `Input p50 tok/s/MW` | 1MW 기준 초당 input token 처리량의 중앙값 |
| `Output p50 tok/s/MW` | 1MW 기준 초당 generated output token 처리량의 중앙값 |
| `Input+Output p50 sum` | input p50과 output p50을 사람이 보기 쉽게 더한 값 |
| `InferenceX total p50` | InferenceX row의 `total_tok_s_mw` 중앙값 |
| `Output p10/p90` | output throughput의 하위 10% / 상위 10% 분위값 |
| `Main framework` | 모델별 canonical framework |
| `Main precision` | 모델별 canonical precision |

주의: `Input p50 + Output p50`은 `Total p50`과 정확히 같지 않을 수 있습니다. 각각의 분포에서 따로 중앙값을 계산하기 때문입니다.

## H200/B200/GB200 Model Throughput Table

| Model | GPU | Rows | Input p50 tok/s/MW | Output p50 tok/s/MW | Input+Output p50 sum | InferenceX total p50 | Output p10 | Output p90 | Main framework | Main precision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| dsr1 | H200 | 313 | 62,773 | 62,631 | 125,404 | 125,928 | 23,687 | 139,711 | sglang | fp8 |
| dsr1 | B200 | 358 | 64,560 | 65,077 | 129,637 | 130,377 | 24,909 | 140,179 | sglang | fp8 |
| dsv4 | GB200 | 27 | 64,325 | 64,530 | 128,855 | 64,427 | 8,410 | 1,523,908 | dynamo-vllm | fp4 |
| glm5 | H200 | 20 | 44,734 | 44,263 | 88,998 | 88,998 | 16,821 | 96,739 | sglang | fp8 |
| glm5 | B200 | 41 | 63,941 | 64,144 | 128,085 | 128,085 | 22,872 | 192,526 | sglang | fp8 |
| gptoss120b | H200 | 990 | 362,537 | 369,518 | 732,055 | 739,045 | 128,491 | 918,446 | vllm | fp4 |
| gptoss120b | B200 | 1,102 | 692,240 | 723,458 | 1,415,697 | 1,444,180 | 136,889 | 2,599,418 | vllm | fp4 |
| kimik2.5 | H200 | 50 | 68,680 | 67,957 | 136,637 | 136,637 | 26,469 | 143,934 | vllm | int4 |
| kimik2.5 | B200 | 25 | 62,021 | 61,367 | 123,388 | 123,388 | 25,306 | 128,729 | vllm | int4 |
| llama70b | H200 | 234 | 196,087 | 202,722 | 398,809 | 407,603 | 65,733 | 700,888 | vllm | fp8 |
| llama70b | B200 | 268 | 169,240 | 200,857 | 370,097 | 403,853 | 61,714 | 735,270 | vllm | fp8 |
| minimaxm2.5 | H200 | 85 | 159,199 | 159,704 | 318,903 | 318,903 | 34,292 | 585,880 | vllm | fp8 |
| minimaxm2.5 | B200 | 123 | 306,323 | 307,295 | 613,617 | 613,617 | 88,049 | 1,496,257 | vllm | fp8 |
| qwen3.5 | H200 | 51 | 90,831 | 89,934 | 180,765 | 180,765 | 35,518 | 207,679 | sglang | fp8 |
| qwen3.5 | B200 | 60 | 177,732 | 178,342 | 356,074 | 356,074 | 44,570 | 808,899 | sglang | fp8 |

## ISL/OSL별 Output Throughput 비교

아래 표도 `is_main_model_config=yes`만 사용합니다. 즉 sequence 조건이 달라도 model별 framework/precision은 고정되어 있습니다.

```text
sequence conditions = 1024/1024, 8192/1024, 1024/8192
metric = output_tok_s_mw p50
baseline = same model/GPU at ISL=1024, OSL=1024
```

| Model | GPU | ISL | OSL | Rows | Output p50 tok/s/MW | vs 1024/1024 | Output p10 | Output p90 | Main framework | Main precision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| dsr1 | H200 | 1024 | 1024 | 313 | 62,631 | baseline | 23,687 | 139,711 | sglang | fp8 |
| dsr1 | H200 | 8192 | 1024 | 305 | 49,538 | -21% | 21,152 | 83,246 | sglang | fp8 |
| dsr1 | H200 | 1024 | 8192 | 284 | 66,869 | +7% | 24,108 | 143,763 | sglang | fp8 |
| dsr1 | B200 | 1024 | 1024 | 358 | 65,077 | baseline | 24,909 | 140,179 | sglang | fp8 |
| dsr1 | B200 | 8192 | 1024 | 343 | 43,841 | -33% | 21,204 | 78,659 | sglang | fp8 |
| dsr1 | B200 | 1024 | 8192 | 292 | 68,634 | +5% | 26,049 | 150,937 | sglang | fp8 |
| dsv4 | GB200 | 1024 | 1024 | 27 | 64,530 | baseline | 8,410 | 1,523,908 | dynamo-vllm | fp4 |
| dsv4 | GB200 | 8192 | 1024 | 61 | 108,223 | +68% | 7,618 | 1,159,250 | dynamo-vllm | fp4 |
| glm5 | H200 | 1024 | 1024 | 20 | 44,263 | baseline | 16,821 | 96,739 | sglang | fp8 |
| glm5 | H200 | 8192 | 1024 | 20 | 32,997 | -25% | 14,393 | 45,733 | sglang | fp8 |
| glm5 | B200 | 1024 | 1024 | 41 | 64,144 | baseline | 22,872 | 192,526 | sglang | fp8 |
| glm5 | B200 | 8192 | 1024 | 42 | 48,984 | -24% | 19,766 | 91,487 | sglang | fp8 |
| gptoss120b | H200 | 1024 | 1024 | 990 | 369,518 | baseline | 128,491 | 918,446 | vllm | fp4 |
| gptoss120b | H200 | 8192 | 1024 | 1,164 | 302,198 | -18% | 116,495 | 679,699 | vllm | fp4 |
| gptoss120b | H200 | 1024 | 8192 | 953 | 389,915 | +6% | 132,129 | 943,813 | vllm | fp4 |
| gptoss120b | B200 | 1024 | 1024 | 1,102 | 723,458 | baseline | 136,889 | 2,599,418 | vllm | fp4 |
| gptoss120b | B200 | 8192 | 1024 | 1,056 | 590,916 | -18% | 128,871 | 1,531,779 | vllm | fp4 |
| gptoss120b | B200 | 1024 | 8192 | 993 | 737,118 | +2% | 136,063 | 2,609,298 | vllm | fp4 |
| kimik2.5 | H200 | 1024 | 1024 | 50 | 67,957 | baseline | 26,469 | 143,934 | vllm | int4 |
| kimik2.5 | H200 | 8192 | 1024 | 50 | 49,453 | -27% | 22,893 | 73,700 | vllm | int4 |
| kimik2.5 | H200 | 1024 | 8192 | 35 | 70,460 | +4% | 27,035 | 141,857 | vllm | int4 |
| kimik2.5 | B200 | 1024 | 1024 | 25 | 61,367 | baseline | 25,306 | 128,729 | vllm | int4 |
| kimik2.5 | B200 | 8192 | 1024 | 25 | 47,669 | -22% | 22,670 | 83,954 | vllm | int4 |
| kimik2.5 | B200 | 1024 | 8192 | 10 | 52,572 | -14% | 21,278 | 129,438 | vllm | int4 |
| llama70b | H200 | 1024 | 1024 | 234 | 202,722 | baseline | 65,733 | 700,888 | vllm | fp8 |
| llama70b | H200 | 8192 | 1024 | 224 | 123,814 | -39% | 53,858 | 230,332 | vllm | fp8 |
| llama70b | H200 | 1024 | 8192 | 193 | 202,901 | baseline | 59,151 | 487,887 | vllm | fp8 |
| llama70b | B200 | 1024 | 1024 | 268 | 200,857 | baseline | 61,714 | 735,270 | vllm | fp8 |
| llama70b | B200 | 8192 | 1024 | 198 | 147,708 | -26% | 52,285 | 333,131 | vllm | fp8 |
| llama70b | B200 | 1024 | 8192 | 220 | 216,100 | +8% | 63,973 | 719,325 | vllm | fp8 |
| minimaxm2.5 | H200 | 1024 | 1024 | 85 | 159,704 | baseline | 34,292 | 585,880 | vllm | fp8 |
| minimaxm2.5 | H200 | 8192 | 1024 | 86 | 125,470 | -21% | 32,479 | 299,951 | vllm | fp8 |
| minimaxm2.5 | H200 | 1024 | 8192 | 29 | 140,863 | -12% | 35,715 | 397,583 | vllm | fp8 |
| minimaxm2.5 | B200 | 1024 | 1024 | 123 | 307,295 | baseline | 88,049 | 1,496,257 | vllm | fp8 |
| minimaxm2.5 | B200 | 8192 | 1024 | 122 | 224,983 | -27% | 77,182 | 516,284 | vllm | fp8 |
| minimaxm2.5 | B200 | 1024 | 8192 | 30 | 188,540 | -39% | 84,533 | 380,884 | vllm | fp8 |
| qwen3.5 | H200 | 1024 | 1024 | 51 | 89,934 | baseline | 35,518 | 207,679 | sglang | fp8 |
| qwen3.5 | H200 | 8192 | 1024 | 49 | 77,919 | -13% | 35,709 | 126,794 | sglang | fp8 |
| qwen3.5 | B200 | 1024 | 1024 | 60 | 178,342 | baseline | 44,570 | 808,899 | sglang | fp8 |
| qwen3.5 | B200 | 8192 | 1024 | 58 | 133,590 | -25% | 43,205 | 389,233 | sglang | fp8 |
| qwen3.5 | B200 | 1024 | 8192 | 20 | 177,041 | -1% | 47,107 | 557,306 | sglang | fp8 |

## 빠른 해석

### 1. GPT-OSS-120B는 H200/B200 비교에 가장 안정적인 proxy다

`gptoss120b`는 `vllm/fp4`로 고정됩니다. H200 rows=990, B200 rows=1,102이며 B200 output p50은 723,458 tok/s/MW입니다.

### 2. Llama 70B는 fp8/vLLM 고정 후 B200 기준값이 더 보수적으로 내려간다

`llama70b`는 `vllm/fp8`로 고정됩니다. B200 output p50은 200,857 tok/s/MW이며, 혼합 overview보다 낮은 값이므로 Meta/Llama 계열 proxy에 더 보수적입니다.

### 3. DSR1은 sglang/fp8 고정 기준으로 reasoning proxy를 잡는다

`dsr1`은 `sglang/fp8`로 고정됩니다. H200 output p50은 62,631, B200 output p50은 65,077 tok/s/MW입니다.

### 4. Qwen3.5는 sglang/fp8 고정 기준으로 Alibaba proxy에 사용한다

`qwen3.5`는 `sglang/fp8`로 고정됩니다. B200 output p50은 178,342 tok/s/MW입니다.

## 이 표를 token capacity 모델에 반영할 때

headline output은 generated output token 기준이므로 `Output p50 tok/s/MW`를 우선합니다. 다만 상용 서비스는 benchmark보다 복잡하므로 모델에서는 public InferenceX reference에 `commercial_workload_fit_factor`를 곱합니다.

```text
public InferenceX reference
* commercial workload fit factor
= serving_tps_per_mw
```

## 채택 전 체크리스트

- 같은 model/GPU만 비교했는가?
- 모델별 `main_framework`와 `main_precision`이 같은 행만 사용했는가?
- ISL/OSL 조건이 target workload와 맞는가?
- row_count가 충분한가?
- output p50뿐 아니라 p10/p90 범위도 봤는가?
- latency와 accuracy를 별도로 확인했는가?
- total token throughput을 generated output token capacity로 착각하지 않았는가?
- InferenceX benchmark를 company production telemetry처럼 말하지 않았는가?

## 다음 분석 후보

1. `main_framework/main_precision` 고정 상태에서 concurrency별 frontier 비교
2. `ISL=8192`, `OSL=1024` long-context serving 비교
3. `OSL=8192` long-output/reasoning workload 비교
4. output p50뿐 아니라 p99 TTFT/TPOT를 포함한 service-fit table
5. accuracy eval과 throughput을 함께 보는 speed-quality frontier
