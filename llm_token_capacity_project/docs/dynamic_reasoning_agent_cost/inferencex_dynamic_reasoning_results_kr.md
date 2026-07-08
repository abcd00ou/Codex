# InferenceX CoT / Agentic 결과 정리

이 문서는 `inferencex_dynamic_reasoning_tps_gpu_summary.csv`를 사람이 바로 읽기 좋게 정리한 결과표다.

## 결론 먼저

- CoT/단일 추론은 call multiplier가 1.0이라 InferenceX 원본 `output_tok_s_gpu`를 그대로 사용한다.
- Agentic/ReAct workload는 논문 근거의 평균 `9.2x` LLM call multiplier를 적용했다.
- `30/50/70`은 workload 비중이 아니라 사용자당 요구 처리량인 `tok/s/user`다.
- CoT와 agentic의 비중을 모르므로 두 workload를 섞지 않고 각각 계산했다.
- `users/GPU = scenario_output_tok_s_gpu / tok_s_user`로 해석한다.
- 이 결과는 아직 tool wait, prefix cache, KV cache pressure, SLO 실패율을 반영하지 않은 1차 overlay다.

## Interactivity별 전체 효과

| Workload | tok/s/user | Calls/request | Capacity kept vs single-call | 의미 |
|---|---:|---:|---:|---|
| Agentic/ReAct | 30 | 9.2 | 10.9% | 9.2회 내부 LLM call을 먼저 반영한 뒤 users/GPU 계산 |
| Agentic/ReAct | 50 | 9.2 | 10.9% | 9.2회 내부 LLM call을 먼저 반영한 뒤 users/GPU 계산 |
| Agentic/ReAct | 70 | 9.2 | 10.9% | 9.2회 내부 LLM call을 먼저 반영한 뒤 users/GPU 계산 |
| CoT/단일 추론 | 30 | 1 | 100.0% | 원본 InferenceX TPS/GPU 기준 users/GPU 계산 |
| CoT/단일 추론 | 50 | 1 | 100.0% | 원본 InferenceX TPS/GPU 기준 users/GPU 계산 |
| CoT/단일 추론 | 70 | 1 | 100.0% | 원본 InferenceX TPS/GPU 기준 users/GPU 계산 |

## ISL/OSL별 중간값 효과

아래 표는 `50 tok/s/user` 기준이다. `group median`은 model/GPU 조합별 p50 값을 다시 중앙값으로 본 것이다.

| Workload | ISL/OSL | Groups | Scenario output tok/s/GPU group median | Users/GPU group median at 50 tok/s/user |
|---|---:|---:|---:|---:|
| CoT | 1024/1024 | 45 | 214 | 4.276 |
| CoT | 8192/1024 | 48 | 173 | 3.454 |
| CoT | 1024/8192 | 35 | 242 | 4.849 |
| Agentic | 1024/1024 | 45 | 23.2 | 0.465 |
| Agentic | 8192/1024 | 48 | 18.8 | 0.375 |
| Agentic | 1024/8192 | 35 | 26.4 | 0.527 |

## 1024/1024 기준 모델/GPU별 결과

아래 표는 가장 기본 비교축인 `ISL=1024`, `OSL=1024` 기준이다. GPU 수, concurrency, framework, precision은 원본 InferenceX row를 유지했고, 모델별 main framework/precision row만 사용했다.

### CoT

| Workload | Model | GPU | Main framework | Main precision | tok/s/user | Rows | Scenario output tok/s/GPU p50 | Users/GPU p50 | Req/s/GPU by OSL p50 |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| CoT | dsr1 | B200 | sglang | fp8 | 30 | 358 | 141 | 4.707 | 0.138 |
| CoT | dsr1 | B200 | sglang | fp8 | 50 | 358 | 141 | 2.824 | 0.138 |
| CoT | dsr1 | B200 | sglang | fp8 | 70 | 358 | 141 | 2.017 | 0.138 |
| CoT | dsr1 | B300 | sglang | fp8 | 30 | 69 | 202 | 6.741 | 0.197 |
| CoT | dsr1 | B300 | sglang | fp8 | 50 | 69 | 202 | 4.045 | 0.197 |
| CoT | dsr1 | B300 | sglang | fp8 | 70 | 69 | 202 | 2.889 | 0.197 |
| CoT | dsr1 | H200 | sglang | fp8 | 30 | 313 | 108 | 3.612 | 0.106 |
| CoT | dsr1 | H200 | sglang | fp8 | 50 | 313 | 108 | 2.167 | 0.106 |
| CoT | dsr1 | H200 | sglang | fp8 | 70 | 313 | 108 | 1.548 | 0.106 |
| CoT | dsr1 | MI300X | sglang | fp8 | 30 | 305 | 72.2 | 2.407 | 0.071 |
| CoT | dsr1 | MI300X | sglang | fp8 | 50 | 305 | 72.2 | 1.444 | 0.071 |
| CoT | dsr1 | MI300X | sglang | fp8 | 70 | 305 | 72.2 | 1.032 | 0.071 |
| CoT | dsr1 | MI325X | sglang | fp8 | 30 | 314 | 76.8 | 2.559 | 0.075 |
| CoT | dsr1 | MI325X | sglang | fp8 | 50 | 314 | 76.8 | 1.535 | 0.075 |
| CoT | dsr1 | MI325X | sglang | fp8 | 70 | 314 | 76.8 | 1.097 | 0.075 |
| CoT | dsr1 | MI355X | sglang | fp8 | 30 | 314 | 87.5 | 2.916 | 0.085 |
| CoT | dsr1 | MI355X | sglang | fp8 | 50 | 314 | 87.5 | 1.75 | 0.085 |
| CoT | dsr1 | MI355X | sglang | fp8 | 70 | 314 | 87.5 | 1.25 | 0.085 |
| CoT | dsv4 | GB200 | dynamo-vllm | fp4 | 30 | 27 | 136 | 4.517 | 0.132 |
| CoT | dsv4 | GB200 | dynamo-vllm | fp4 | 50 | 27 | 136 | 2.71 | 0.132 |
| CoT | dsv4 | GB200 | dynamo-vllm | fp4 | 70 | 27 | 136 | 1.936 | 0.132 |
| CoT | glm5 | B200 | sglang | fp8 | 30 | 41 | 139 | 4.64 | 0.136 |
| CoT | glm5 | B200 | sglang | fp8 | 50 | 41 | 139 | 2.784 | 0.136 |
| CoT | glm5 | B200 | sglang | fp8 | 70 | 41 | 139 | 1.988 | 0.136 |
| CoT | glm5 | B300 | sglang | fp8 | 30 | 42 | 214 | 7.126 | 0.209 |
| CoT | glm5 | B300 | sglang | fp8 | 50 | 42 | 214 | 4.276 | 0.209 |
| CoT | glm5 | B300 | sglang | fp8 | 70 | 42 | 214 | 3.054 | 0.209 |
| CoT | glm5 | H200 | sglang | fp8 | 30 | 20 | 76.6 | 2.553 | 0.075 |
| CoT | glm5 | H200 | sglang | fp8 | 50 | 20 | 76.6 | 1.532 | 0.075 |
| CoT | glm5 | H200 | sglang | fp8 | 70 | 20 | 76.6 | 1.094 | 0.075 |
| CoT | glm5 | MI325X | sglang | fp8 | 30 | 10 | 48.8 | 1.626 | 0.048 |
| CoT | glm5 | MI325X | sglang | fp8 | 50 | 10 | 48.8 | 0.975 | 0.048 |
| CoT | glm5 | MI325X | sglang | fp8 | 70 | 10 | 48.8 | 0.697 | 0.048 |
| CoT | glm5 | MI355X | sglang | fp8 | 30 | 48 | 131 | 4.365 | 0.128 |
| CoT | glm5 | MI355X | sglang | fp8 | 50 | 48 | 131 | 2.619 | 0.128 |
| CoT | glm5 | MI355X | sglang | fp8 | 70 | 48 | 131 | 1.871 | 0.128 |
| CoT | glm5.1 | MI355X | sglang | fp4 | 30 | 20 | 195 | 6.511 | 0.191 |
| CoT | glm5.1 | MI355X | sglang | fp4 | 50 | 20 | 195 | 3.907 | 0.191 |
| CoT | glm5.1 | MI355X | sglang | fp4 | 70 | 20 | 195 | 2.791 | 0.191 |
| CoT | gptoss120b | B200 | vllm | fp4 | 30 | 1102 | 1,570 | 52.3 | 1.533 |
| CoT | gptoss120b | B200 | vllm | fp4 | 50 | 1102 | 1,570 | 31.4 | 1.533 |
| CoT | gptoss120b | B200 | vllm | fp4 | 70 | 1102 | 1,570 | 22.4 | 1.533 |
| CoT | gptoss120b | H100 | vllm | fp4 | 30 | 850 | 569 | 19.0 | 0.556 |
| CoT | gptoss120b | H100 | vllm | fp4 | 50 | 850 | 569 | 11.4 | 0.556 |
| CoT | gptoss120b | H100 | vllm | fp4 | 70 | 850 | 569 | 8.132 | 0.556 |
| CoT | gptoss120b | H200 | vllm | fp4 | 30 | 990 | 639 | 21.3 | 0.624 |
| CoT | gptoss120b | H200 | vllm | fp4 | 50 | 990 | 639 | 12.8 | 0.624 |
| CoT | gptoss120b | H200 | vllm | fp4 | 70 | 990 | 639 | 9.132 | 0.624 |
| CoT | gptoss120b | MI300X | vllm | fp4 | 30 | 970 | 498 | 16.6 | 0.487 |
| CoT | gptoss120b | MI300X | vllm | fp4 | 50 | 970 | 498 | 9.964 | 0.487 |
| CoT | gptoss120b | MI300X | vllm | fp4 | 70 | 970 | 498 | 7.117 | 0.487 |
| CoT | gptoss120b | MI325X | vllm | fp4 | 30 | 1236 | 594 | 19.8 | 0.58 |
| CoT | gptoss120b | MI325X | vllm | fp4 | 50 | 1236 | 594 | 11.9 | 0.58 |
| CoT | gptoss120b | MI325X | vllm | fp4 | 70 | 1236 | 594 | 8.49 | 0.58 |
| CoT | gptoss120b | MI355X | vllm | fp4 | 30 | 688 | 898 | 29.9 | 0.877 |
| CoT | gptoss120b | MI355X | vllm | fp4 | 50 | 688 | 898 | 18.0 | 0.877 |
| CoT | gptoss120b | MI355X | vllm | fp4 | 70 | 688 | 898 | 12.8 | 0.877 |
| CoT | kimik2.5 | B200 | vllm | int4 | 30 | 25 | 133 | 4.439 | 0.13 |
| CoT | kimik2.5 | B200 | vllm | int4 | 50 | 25 | 133 | 2.663 | 0.13 |
| CoT | kimik2.5 | B200 | vllm | int4 | 70 | 25 | 133 | 1.902 | 0.13 |
| CoT | kimik2.5 | B300 | vllm | int4 | 30 | 30 | 178 | 5.95 | 0.174 |
| CoT | kimik2.5 | B300 | vllm | int4 | 50 | 30 | 178 | 3.57 | 0.174 |
| CoT | kimik2.5 | B300 | vllm | int4 | 70 | 30 | 178 | 2.55 | 0.174 |
| CoT | kimik2.5 | H200 | vllm | int4 | 30 | 50 | 118 | 3.919 | 0.115 |
| CoT | kimik2.5 | H200 | vllm | int4 | 50 | 50 | 118 | 2.351 | 0.115 |
| CoT | kimik2.5 | H200 | vllm | int4 | 70 | 50 | 118 | 1.679 | 0.115 |
| CoT | kimik2.5 | MI300X | vllm | int4 | 30 | 10 | 31.0 | 1.034 | 0.03 |
| CoT | kimik2.5 | MI300X | vllm | int4 | 50 | 10 | 31.0 | 0.62 | 0.03 |
| CoT | kimik2.5 | MI300X | vllm | int4 | 70 | 10 | 31.0 | 0.443 | 0.03 |
| CoT | kimik2.5 | MI325X | vllm | int4 | 30 | 65 | 20.7 | 0.689 | 0.02 |
| CoT | kimik2.5 | MI325X | vllm | int4 | 50 | 65 | 20.7 | 0.414 | 0.02 |
| CoT | kimik2.5 | MI325X | vllm | int4 | 70 | 65 | 20.7 | 0.295 | 0.02 |
| CoT | kimik2.5 | MI355X | vllm | int4 | 30 | 45 | 49.8 | 1.661 | 0.049 |
| CoT | kimik2.5 | MI355X | vllm | int4 | 50 | 45 | 49.8 | 0.996 | 0.049 |
| CoT | kimik2.5 | MI355X | vllm | int4 | 70 | 45 | 49.8 | 0.712 | 0.049 |
| CoT | llama70b | B200 | vllm | fp8 | 30 | 268 | 436 | 14.5 | 0.426 |
| CoT | llama70b | B200 | vllm | fp8 | 50 | 268 | 436 | 8.717 | 0.426 |
| CoT | llama70b | B200 | vllm | fp8 | 70 | 268 | 436 | 6.227 | 0.426 |
| CoT | llama70b | H100 | vllm | fp8 | 30 | 210 | 294 | 9.786 | 0.287 |
| CoT | llama70b | H100 | vllm | fp8 | 50 | 210 | 294 | 5.872 | 0.287 |
| CoT | llama70b | H100 | vllm | fp8 | 70 | 210 | 294 | 4.194 | 0.287 |
| CoT | llama70b | H200 | vllm | fp8 | 30 | 234 | 351 | 11.7 | 0.342 |
| CoT | llama70b | H200 | vllm | fp8 | 50 | 234 | 351 | 7.014 | 0.342 |
| CoT | llama70b | H200 | vllm | fp8 | 70 | 234 | 351 | 5.01 | 0.342 |
| CoT | llama70b | MI300X | vllm | fp8 | 30 | 280 | 297 | 9.886 | 0.29 |
| CoT | llama70b | MI300X | vllm | fp8 | 50 | 280 | 297 | 5.931 | 0.29 |
| CoT | llama70b | MI300X | vllm | fp8 | 70 | 280 | 297 | 4.237 | 0.29 |
| CoT | llama70b | MI325X | vllm | fp8 | 30 | 278 | 344 | 11.5 | 0.335 |
| CoT | llama70b | MI325X | vllm | fp8 | 50 | 278 | 344 | 6.871 | 0.335 |
| CoT | llama70b | MI325X | vllm | fp8 | 70 | 278 | 344 | 4.908 | 0.335 |
| CoT | llama70b | MI355X | vllm | fp8 | 30 | 240 | 415 | 13.8 | 0.405 |
| CoT | llama70b | MI355X | vllm | fp8 | 50 | 240 | 415 | 8.303 | 0.405 |
| CoT | llama70b | MI355X | vllm | fp8 | 70 | 240 | 415 | 5.931 | 0.405 |
| CoT | minimaxm2.5 | B200 | vllm | fp8 | 30 | 123 | 667 | 22.2 | 0.651 |
| CoT | minimaxm2.5 | B200 | vllm | fp8 | 50 | 123 | 667 | 13.3 | 0.651 |
| CoT | minimaxm2.5 | B200 | vllm | fp8 | 70 | 123 | 667 | 9.526 | 0.651 |
| CoT | minimaxm2.5 | B300 | vllm | fp8 | 30 | 41 | 1,623 | 54.1 | 1.585 |
| CoT | minimaxm2.5 | B300 | vllm | fp8 | 50 | 41 | 1,623 | 32.5 | 1.585 |
| CoT | minimaxm2.5 | B300 | vllm | fp8 | 70 | 41 | 1,623 | 23.2 | 1.585 |
| CoT | minimaxm2.5 | H100 | vllm | fp8 | 30 | 48 | 251 | 8.361 | 0.245 |
| CoT | minimaxm2.5 | H100 | vllm | fp8 | 50 | 48 | 251 | 5.016 | 0.245 |
| CoT | minimaxm2.5 | H100 | vllm | fp8 | 70 | 48 | 251 | 3.583 | 0.245 |
| CoT | minimaxm2.5 | H200 | vllm | fp8 | 30 | 85 | 276 | 9.21 | 0.27 |
| CoT | minimaxm2.5 | H200 | vllm | fp8 | 50 | 85 | 276 | 5.526 | 0.27 |
| CoT | minimaxm2.5 | H200 | vllm | fp8 | 70 | 85 | 276 | 3.947 | 0.27 |
| CoT | minimaxm2.5 | MI300X | vllm | fp8 | 30 | 40 | 272 | 9.058 | 0.265 |
| CoT | minimaxm2.5 | MI300X | vllm | fp8 | 50 | 40 | 272 | 5.435 | 0.265 |
| CoT | minimaxm2.5 | MI300X | vllm | fp8 | 70 | 40 | 272 | 3.882 | 0.265 |
| CoT | minimaxm2.5 | MI325X | vllm | fp8 | 30 | 82 | 293 | 9.772 | 0.286 |
| CoT | minimaxm2.5 | MI325X | vllm | fp8 | 50 | 82 | 293 | 5.863 | 0.286 |
| CoT | minimaxm2.5 | MI325X | vllm | fp8 | 70 | 82 | 293 | 4.188 | 0.286 |
| CoT | minimaxm2.5 | MI355X | vllm | fp8 | 30 | 222 | 479 | 16.0 | 0.468 |
| CoT | minimaxm2.5 | MI355X | vllm | fp8 | 50 | 222 | 479 | 9.577 | 0.468 |
| CoT | minimaxm2.5 | MI355X | vllm | fp8 | 70 | 222 | 479 | 6.841 | 0.468 |
| CoT | qwen3.5 | B200 | sglang | fp8 | 30 | 60 | 387 | 12.9 | 0.378 |
| CoT | qwen3.5 | B200 | sglang | fp8 | 50 | 60 | 387 | 7.74 | 0.378 |
| CoT | qwen3.5 | B200 | sglang | fp8 | 70 | 60 | 387 | 5.529 | 0.378 |
| CoT | qwen3.5 | B300 | sglang | fp8 | 30 | 39 | 774 | 25.8 | 0.756 |
| CoT | qwen3.5 | B300 | sglang | fp8 | 50 | 39 | 774 | 15.5 | 0.756 |
| CoT | qwen3.5 | B300 | sglang | fp8 | 70 | 39 | 774 | 11.1 | 0.756 |
| CoT | qwen3.5 | H100 | sglang | fp8 | 30 | 17 | 121 | 4.03 | 0.118 |
| CoT | qwen3.5 | H100 | sglang | fp8 | 50 | 17 | 121 | 2.418 | 0.118 |
| CoT | qwen3.5 | H100 | sglang | fp8 | 70 | 17 | 121 | 1.727 | 0.118 |
| CoT | qwen3.5 | H200 | sglang | fp8 | 30 | 51 | 156 | 5.186 | 0.152 |
| CoT | qwen3.5 | H200 | sglang | fp8 | 50 | 51 | 156 | 3.112 | 0.152 |
| CoT | qwen3.5 | H200 | sglang | fp8 | 70 | 51 | 156 | 2.223 | 0.152 |
| CoT | qwen3.5 | MI300X | sglang | fp8 | 30 | 25 | 73.7 | 2.458 | 0.072 |
| CoT | qwen3.5 | MI300X | sglang | fp8 | 50 | 25 | 73.7 | 1.475 | 0.072 |
| CoT | qwen3.5 | MI300X | sglang | fp8 | 70 | 25 | 73.7 | 1.053 | 0.072 |
| CoT | qwen3.5 | MI325X | sglang | fp8 | 30 | 30 | 78.5 | 2.617 | 0.077 |
| CoT | qwen3.5 | MI325X | sglang | fp8 | 50 | 30 | 78.5 | 1.57 | 0.077 |
| CoT | qwen3.5 | MI325X | sglang | fp8 | 70 | 30 | 78.5 | 1.122 | 0.077 |
| CoT | qwen3.5 | MI355X | sglang | fp8 | 30 | 55 | 356 | 11.9 | 0.348 |
| CoT | qwen3.5 | MI355X | sglang | fp8 | 50 | 55 | 356 | 7.12 | 0.348 |
| CoT | qwen3.5 | MI355X | sglang | fp8 | 70 | 55 | 356 | 5.086 | 0.348 |

### Agentic

| Workload | Model | GPU | Main framework | Main precision | tok/s/user | Rows | Scenario output tok/s/GPU p50 | Users/GPU p50 | Req/s/GPU by OSL p50 |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| Agentic | dsr1 | B200 | sglang | fp8 | 30 | 358 | 15.3 | 0.512 | 0.015 |
| Agentic | dsr1 | B200 | sglang | fp8 | 50 | 358 | 15.3 | 0.307 | 0.015 |
| Agentic | dsr1 | B200 | sglang | fp8 | 70 | 358 | 15.3 | 0.219 | 0.015 |
| Agentic | dsr1 | B300 | sglang | fp8 | 30 | 69 | 22.0 | 0.733 | 0.021 |
| Agentic | dsr1 | B300 | sglang | fp8 | 50 | 69 | 22.0 | 0.44 | 0.021 |
| Agentic | dsr1 | B300 | sglang | fp8 | 70 | 69 | 22.0 | 0.314 | 0.021 |
| Agentic | dsr1 | H200 | sglang | fp8 | 30 | 313 | 11.8 | 0.393 | 0.012 |
| Agentic | dsr1 | H200 | sglang | fp8 | 50 | 313 | 11.8 | 0.236 | 0.012 |
| Agentic | dsr1 | H200 | sglang | fp8 | 70 | 313 | 11.8 | 0.168 | 0.012 |
| Agentic | dsr1 | MI300X | sglang | fp8 | 30 | 305 | 7.85 | 0.262 | 0.008 |
| Agentic | dsr1 | MI300X | sglang | fp8 | 50 | 305 | 7.85 | 0.157 | 0.008 |
| Agentic | dsr1 | MI300X | sglang | fp8 | 70 | 305 | 7.85 | 0.112 | 0.008 |
| Agentic | dsr1 | MI325X | sglang | fp8 | 30 | 314 | 8.344 | 0.278 | 0.008 |
| Agentic | dsr1 | MI325X | sglang | fp8 | 50 | 314 | 8.344 | 0.167 | 0.008 |
| Agentic | dsr1 | MI325X | sglang | fp8 | 70 | 314 | 8.344 | 0.119 | 0.008 |
| Agentic | dsr1 | MI355X | sglang | fp8 | 30 | 314 | 9.508 | 0.317 | 0.009 |
| Agentic | dsr1 | MI355X | sglang | fp8 | 50 | 314 | 9.508 | 0.19 | 0.009 |
| Agentic | dsr1 | MI355X | sglang | fp8 | 70 | 314 | 9.508 | 0.136 | 0.009 |
| Agentic | dsv4 | GB200 | dynamo-vllm | fp4 | 30 | 27 | 14.7 | 0.491 | 0.014 |
| Agentic | dsv4 | GB200 | dynamo-vllm | fp4 | 50 | 27 | 14.7 | 0.295 | 0.014 |
| Agentic | dsv4 | GB200 | dynamo-vllm | fp4 | 70 | 27 | 14.7 | 0.21 | 0.014 |
| Agentic | glm5 | B200 | sglang | fp8 | 30 | 41 | 15.1 | 0.504 | 0.015 |
| Agentic | glm5 | B200 | sglang | fp8 | 50 | 41 | 15.1 | 0.303 | 0.015 |
| Agentic | glm5 | B200 | sglang | fp8 | 70 | 41 | 15.1 | 0.216 | 0.015 |
| Agentic | glm5 | B300 | sglang | fp8 | 30 | 42 | 23.2 | 0.775 | 0.023 |
| Agentic | glm5 | B300 | sglang | fp8 | 50 | 42 | 23.2 | 0.465 | 0.023 |
| Agentic | glm5 | B300 | sglang | fp8 | 70 | 42 | 23.2 | 0.332 | 0.023 |
| Agentic | glm5 | H200 | sglang | fp8 | 30 | 20 | 8.323 | 0.277 | 0.008 |
| Agentic | glm5 | H200 | sglang | fp8 | 50 | 20 | 8.323 | 0.166 | 0.008 |
| Agentic | glm5 | H200 | sglang | fp8 | 70 | 20 | 8.323 | 0.119 | 0.008 |
| Agentic | glm5 | MI325X | sglang | fp8 | 30 | 10 | 5.301 | 0.177 | 0.005 |
| Agentic | glm5 | MI325X | sglang | fp8 | 50 | 10 | 5.301 | 0.106 | 0.005 |
| Agentic | glm5 | MI325X | sglang | fp8 | 70 | 10 | 5.301 | 0.076 | 0.005 |
| Agentic | glm5 | MI355X | sglang | fp8 | 30 | 48 | 14.2 | 0.474 | 0.014 |
| Agentic | glm5 | MI355X | sglang | fp8 | 50 | 48 | 14.2 | 0.285 | 0.014 |
| Agentic | glm5 | MI355X | sglang | fp8 | 70 | 48 | 14.2 | 0.203 | 0.014 |
| Agentic | glm5.1 | MI355X | sglang | fp4 | 30 | 20 | 21.2 | 0.708 | 0.021 |
| Agentic | glm5.1 | MI355X | sglang | fp4 | 50 | 20 | 21.2 | 0.425 | 0.021 |
| Agentic | glm5.1 | MI355X | sglang | fp4 | 70 | 20 | 21.2 | 0.303 | 0.021 |
| Agentic | gptoss120b | B200 | vllm | fp4 | 30 | 1102 | 171 | 5.688 | 0.167 |
| Agentic | gptoss120b | B200 | vllm | fp4 | 50 | 1102 | 171 | 3.413 | 0.167 |
| Agentic | gptoss120b | B200 | vllm | fp4 | 70 | 1102 | 171 | 2.438 | 0.167 |
| Agentic | gptoss120b | H100 | vllm | fp4 | 30 | 850 | 61.9 | 2.063 | 0.06 |
| Agentic | gptoss120b | H100 | vllm | fp4 | 50 | 850 | 61.9 | 1.238 | 0.06 |
| Agentic | gptoss120b | H100 | vllm | fp4 | 70 | 850 | 61.9 | 0.884 | 0.06 |
| Agentic | gptoss120b | H200 | vllm | fp4 | 30 | 990 | 69.5 | 2.316 | 0.068 |
| Agentic | gptoss120b | H200 | vllm | fp4 | 50 | 990 | 69.5 | 1.39 | 0.068 |
| Agentic | gptoss120b | H200 | vllm | fp4 | 70 | 990 | 69.5 | 0.993 | 0.068 |
| Agentic | gptoss120b | MI300X | vllm | fp4 | 30 | 970 | 54.2 | 1.805 | 0.053 |
| Agentic | gptoss120b | MI300X | vllm | fp4 | 50 | 970 | 54.2 | 1.083 | 0.053 |
| Agentic | gptoss120b | MI300X | vllm | fp4 | 70 | 970 | 54.2 | 0.774 | 0.053 |
| Agentic | gptoss120b | MI325X | vllm | fp4 | 30 | 1236 | 64.6 | 2.153 | 0.063 |
| Agentic | gptoss120b | MI325X | vllm | fp4 | 50 | 1236 | 64.6 | 1.292 | 0.063 |
| Agentic | gptoss120b | MI325X | vllm | fp4 | 70 | 1236 | 64.6 | 0.923 | 0.063 |
| Agentic | gptoss120b | MI355X | vllm | fp4 | 30 | 688 | 97.6 | 3.254 | 0.095 |
| Agentic | gptoss120b | MI355X | vllm | fp4 | 50 | 688 | 97.6 | 1.953 | 0.095 |
| Agentic | gptoss120b | MI355X | vllm | fp4 | 70 | 688 | 97.6 | 1.395 | 0.095 |
| Agentic | kimik2.5 | B200 | vllm | int4 | 30 | 25 | 14.5 | 0.482 | 0.014 |
| Agentic | kimik2.5 | B200 | vllm | int4 | 50 | 25 | 14.5 | 0.289 | 0.014 |
| Agentic | kimik2.5 | B200 | vllm | int4 | 70 | 25 | 14.5 | 0.207 | 0.014 |
| Agentic | kimik2.5 | B300 | vllm | int4 | 30 | 30 | 19.4 | 0.647 | 0.019 |
| Agentic | kimik2.5 | B300 | vllm | int4 | 50 | 30 | 19.4 | 0.388 | 0.019 |
| Agentic | kimik2.5 | B300 | vllm | int4 | 70 | 30 | 19.4 | 0.277 | 0.019 |
| Agentic | kimik2.5 | H200 | vllm | int4 | 30 | 50 | 12.8 | 0.426 | 0.012 |
| Agentic | kimik2.5 | H200 | vllm | int4 | 50 | 50 | 12.8 | 0.256 | 0.012 |
| Agentic | kimik2.5 | H200 | vllm | int4 | 70 | 50 | 12.8 | 0.183 | 0.012 |
| Agentic | kimik2.5 | MI300X | vllm | int4 | 30 | 10 | 3.371 | 0.112 | 0.003 |
| Agentic | kimik2.5 | MI300X | vllm | int4 | 50 | 10 | 3.371 | 0.067 | 0.003 |
| Agentic | kimik2.5 | MI300X | vllm | int4 | 70 | 10 | 3.371 | 0.048 | 0.003 |
| Agentic | kimik2.5 | MI325X | vllm | int4 | 30 | 65 | 2.248 | 0.075 | 0.002 |
| Agentic | kimik2.5 | MI325X | vllm | int4 | 50 | 65 | 2.248 | 0.045 | 0.002 |
| Agentic | kimik2.5 | MI325X | vllm | int4 | 70 | 65 | 2.248 | 0.032 | 0.002 |
| Agentic | kimik2.5 | MI355X | vllm | int4 | 30 | 45 | 5.415 | 0.18 | 0.005 |
| Agentic | kimik2.5 | MI355X | vllm | int4 | 50 | 45 | 5.415 | 0.108 | 0.005 |
| Agentic | kimik2.5 | MI355X | vllm | int4 | 70 | 45 | 5.415 | 0.077 | 0.005 |
| Agentic | llama70b | B200 | vllm | fp8 | 30 | 268 | 47.4 | 1.579 | 0.046 |
| Agentic | llama70b | B200 | vllm | fp8 | 50 | 268 | 47.4 | 0.948 | 0.046 |
| Agentic | llama70b | B200 | vllm | fp8 | 70 | 268 | 47.4 | 0.677 | 0.046 |
| Agentic | llama70b | H100 | vllm | fp8 | 30 | 210 | 31.9 | 1.064 | 0.031 |
| Agentic | llama70b | H100 | vllm | fp8 | 50 | 210 | 31.9 | 0.638 | 0.031 |
| Agentic | llama70b | H100 | vllm | fp8 | 70 | 210 | 31.9 | 0.456 | 0.031 |
| Agentic | llama70b | H200 | vllm | fp8 | 30 | 234 | 38.1 | 1.271 | 0.037 |
| Agentic | llama70b | H200 | vllm | fp8 | 50 | 234 | 38.1 | 0.762 | 0.037 |
| Agentic | llama70b | H200 | vllm | fp8 | 70 | 234 | 38.1 | 0.545 | 0.037 |
| Agentic | llama70b | MI300X | vllm | fp8 | 30 | 280 | 32.2 | 1.075 | 0.031 |
| Agentic | llama70b | MI300X | vllm | fp8 | 50 | 280 | 32.2 | 0.645 | 0.031 |
| Agentic | llama70b | MI300X | vllm | fp8 | 70 | 280 | 32.2 | 0.461 | 0.031 |
| Agentic | llama70b | MI325X | vllm | fp8 | 30 | 278 | 37.3 | 1.245 | 0.036 |
| Agentic | llama70b | MI325X | vllm | fp8 | 50 | 278 | 37.3 | 0.747 | 0.036 |
| Agentic | llama70b | MI325X | vllm | fp8 | 70 | 278 | 37.3 | 0.533 | 0.036 |
| Agentic | llama70b | MI355X | vllm | fp8 | 30 | 240 | 45.1 | 1.504 | 0.044 |
| Agentic | llama70b | MI355X | vllm | fp8 | 50 | 240 | 45.1 | 0.903 | 0.044 |
| Agentic | llama70b | MI355X | vllm | fp8 | 70 | 240 | 45.1 | 0.645 | 0.044 |
| Agentic | minimaxm2.5 | B200 | vllm | fp8 | 30 | 123 | 72.5 | 2.416 | 0.071 |
| Agentic | minimaxm2.5 | B200 | vllm | fp8 | 50 | 123 | 72.5 | 1.45 | 0.071 |
| Agentic | minimaxm2.5 | B200 | vllm | fp8 | 70 | 123 | 72.5 | 1.035 | 0.071 |
| Agentic | minimaxm2.5 | B300 | vllm | fp8 | 30 | 41 | 176 | 5.88 | 0.172 |
| Agentic | minimaxm2.5 | B300 | vllm | fp8 | 50 | 41 | 176 | 3.528 | 0.172 |
| Agentic | minimaxm2.5 | B300 | vllm | fp8 | 70 | 41 | 176 | 2.52 | 0.172 |
| Agentic | minimaxm2.5 | H100 | vllm | fp8 | 30 | 48 | 27.3 | 0.909 | 0.027 |
| Agentic | minimaxm2.5 | H100 | vllm | fp8 | 50 | 48 | 27.3 | 0.545 | 0.027 |
| Agentic | minimaxm2.5 | H100 | vllm | fp8 | 70 | 48 | 27.3 | 0.389 | 0.027 |
| Agentic | minimaxm2.5 | H200 | vllm | fp8 | 30 | 85 | 30.0 | 1.001 | 0.029 |
| Agentic | minimaxm2.5 | H200 | vllm | fp8 | 50 | 85 | 30.0 | 0.601 | 0.029 |
| Agentic | minimaxm2.5 | H200 | vllm | fp8 | 70 | 85 | 30.0 | 0.429 | 0.029 |
| Agentic | minimaxm2.5 | MI300X | vllm | fp8 | 30 | 40 | 29.5 | 0.985 | 0.029 |
| Agentic | minimaxm2.5 | MI300X | vllm | fp8 | 50 | 40 | 29.5 | 0.591 | 0.029 |
| Agentic | minimaxm2.5 | MI300X | vllm | fp8 | 70 | 40 | 29.5 | 0.422 | 0.029 |
| Agentic | minimaxm2.5 | MI325X | vllm | fp8 | 30 | 82 | 31.9 | 1.062 | 0.031 |
| Agentic | minimaxm2.5 | MI325X | vllm | fp8 | 50 | 82 | 31.9 | 0.637 | 0.031 |
| Agentic | minimaxm2.5 | MI325X | vllm | fp8 | 70 | 82 | 31.9 | 0.455 | 0.031 |
| Agentic | minimaxm2.5 | MI355X | vllm | fp8 | 30 | 222 | 52.0 | 1.735 | 0.051 |
| Agentic | minimaxm2.5 | MI355X | vllm | fp8 | 50 | 222 | 52.0 | 1.041 | 0.051 |
| Agentic | minimaxm2.5 | MI355X | vllm | fp8 | 70 | 222 | 52.0 | 0.744 | 0.051 |
| Agentic | qwen3.5 | B200 | sglang | fp8 | 30 | 60 | 42.1 | 1.402 | 0.041 |
| Agentic | qwen3.5 | B200 | sglang | fp8 | 50 | 60 | 42.1 | 0.841 | 0.041 |
| Agentic | qwen3.5 | B200 | sglang | fp8 | 70 | 60 | 42.1 | 0.601 | 0.041 |
| Agentic | qwen3.5 | B300 | sglang | fp8 | 30 | 39 | 84.1 | 2.805 | 0.082 |
| Agentic | qwen3.5 | B300 | sglang | fp8 | 50 | 39 | 84.1 | 1.683 | 0.082 |
| Agentic | qwen3.5 | B300 | sglang | fp8 | 70 | 39 | 84.1 | 1.202 | 0.082 |
| Agentic | qwen3.5 | H100 | sglang | fp8 | 30 | 17 | 13.1 | 0.438 | 0.013 |
| Agentic | qwen3.5 | H100 | sglang | fp8 | 50 | 17 | 13.1 | 0.263 | 0.013 |
| Agentic | qwen3.5 | H100 | sglang | fp8 | 70 | 17 | 13.1 | 0.188 | 0.013 |
| Agentic | qwen3.5 | H200 | sglang | fp8 | 30 | 51 | 16.9 | 0.564 | 0.017 |
| Agentic | qwen3.5 | H200 | sglang | fp8 | 50 | 51 | 16.9 | 0.338 | 0.017 |
| Agentic | qwen3.5 | H200 | sglang | fp8 | 70 | 51 | 16.9 | 0.242 | 0.017 |
| Agentic | qwen3.5 | MI300X | sglang | fp8 | 30 | 25 | 8.016 | 0.267 | 0.008 |
| Agentic | qwen3.5 | MI300X | sglang | fp8 | 50 | 25 | 8.016 | 0.16 | 0.008 |
| Agentic | qwen3.5 | MI300X | sglang | fp8 | 70 | 25 | 8.016 | 0.115 | 0.008 |
| Agentic | qwen3.5 | MI325X | sglang | fp8 | 30 | 30 | 8.533 | 0.284 | 0.008 |
| Agentic | qwen3.5 | MI325X | sglang | fp8 | 50 | 30 | 8.533 | 0.171 | 0.008 |
| Agentic | qwen3.5 | MI325X | sglang | fp8 | 70 | 30 | 8.533 | 0.122 | 0.008 |
| Agentic | qwen3.5 | MI355X | sglang | fp8 | 30 | 55 | 38.7 | 1.29 | 0.038 |
| Agentic | qwen3.5 | MI355X | sglang | fp8 | 50 | 55 | 38.7 | 0.774 | 0.038 |
| Agentic | qwen3.5 | MI355X | sglang | fp8 | 70 | 55 | 38.7 | 0.553 | 0.038 |

## 읽는 법

- `Base output tok/s/GPU p50`: InferenceX의 원본 output token throughput 중간값이다.
- `Scenario output tok/s/GPU p50`: CoT는 원본 output TPS/GPU, agentic은 원본 output TPS/GPU를 9.2로 나눈 값이다.
- `Users/GPU p50`: 해당 interactivity 기준으로 GPU 1장이 감당 가능한 사용자 수 근사값이다. `scenario output tok/s/GPU / tok/s/user`로 계산한다.
- `Req/s/GPU by OSL p50`: 해당 OSL 기준으로 GPU 1장이 초당 처리할 수 있는 output-token 기반 요청 수 근사값이다. `scenario output tok/s/GPU / OSL`로 계산한다.
- 이 표는 “전력 기반 토큰 생산량”에 바로 곱할 수 있는 candidate workload factor를 제공하지만, 최종 계수로 확정하려면 LLMServingSim power model에서 idle/standby/prefix-cache/KV-cache를 추가 검증해야 한다.
