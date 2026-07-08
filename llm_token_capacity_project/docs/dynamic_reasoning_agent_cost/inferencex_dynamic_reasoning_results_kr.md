# InferenceX CoT / Agentic 결과 정리

이 문서는 `inferencex_dynamic_reasoning_tps_gpu_summary.csv`를 사람이 바로 읽기 좋게 정리한 결과표다.

## 결론 먼저

- CoT/단일 추론은 call multiplier가 1.0이라 InferenceX 원본 `tok_s_gpu`를 그대로 사용한다.
- Agentic/ReAct workload는 논문 근거의 평균 `9.2x` LLM call multiplier를 적용했다.
- `30/50/70`은 workload 비중이 아니라 사용자당 요구 처리량인 `tok/s/user`다.
- CoT와 agentic의 비중을 모르므로 두 workload를 섞지 않고 각각 계산했다.
- target tok/s/user별로 최신 benchmark date에서 realized tok/s/user가 가장 가까운 row를 선택한다.
- `users/GPU = scenario_total_tok_s_gpu / target_tok_s_user`로 해석한다.
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

아래 표는 `50 tok/s/user` 기준이다. `group median`은 model/GPU 조합별 선택 row 값을 다시 중앙값으로 본 것이다.

| Workload | ISL/OSL | Groups | Scenario total tok/s/GPU group median | Users/GPU group median at 50 tok/s/user |
|---|---:|---:|---:|---:|
| CoT | 1024/1024 | 45 | 734 | 14.7 |
| CoT | 8192/1024 | 48 | 1,501 | 30.0 |
| CoT | 1024/8192 | 35 | 403 | 8.069 |
| Agentic | 1024/1024 | 45 | 79.8 | 1.596 |
| Agentic | 8192/1024 | 48 | 163 | 3.262 |
| Agentic | 1024/8192 | 35 | 43.9 | 0.877 |

## 1024/1024 기준 모델/GPU별 결과

아래 표는 가장 기본 비교축인 `ISL=1024`, `OSL=1024` 기준이다. GPU 수, concurrency, framework, precision은 원본 InferenceX row를 유지했고, 모델별 main framework/precision row만 사용했다.

### CoT

| Workload | Model | GPU | Framework | Precision | Target tok/s/user | Realized tok/s/user | Conc. | Bench ID | Base total tok/s/GPU | Scenario total tok/s/GPU | Users/GPU | Output tok/s/GPU |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CoT | dsr1 | B200 | sglang | fp8 | 30 | 28.8 | 256 | 415291 | 1,707 | 1,707 | 56.9 | 854 |
| CoT | dsr1 | B200 | sglang | fp8 | 50 | 45.9 | 64 | 415318 | 678 | 678 | 13.6 | 339 |
| CoT | dsr1 | B200 | sglang | fp8 | 70 | 76.2 | 16 | 415279 | 292 | 292 | 4.172 | 145 |
| CoT | dsr1 | B300 | sglang | fp8 | 30 | 30.4 | 256 | 415284 | 1,808 | 1,808 | 60.3 | 904 |
| CoT | dsr1 | B300 | sglang | fp8 | 50 | 47.2 | 64 | 415343 | 714 | 714 | 14.3 | 357 |
| CoT | dsr1 | B300 | sglang | fp8 | 70 | 64.0 | 32 | 415315 | 491 | 491 | 7.012 | 246 |
| CoT | dsr1 | H200 | sglang | fp8 | 30 | 31.8 | 64 | 413853 | 506 | 506 | 16.9 | 253 |
| CoT | dsr1 | H200 | sglang | fp8 | 50 | 44.7 | 32 | 413846 | 354 | 354 | 7.08 | 177 |
| CoT | dsr1 | H200 | sglang | fp8 | 70 | 60.8 | 16 | 413848 | 241 | 241 | 3.44 | 120 |
| CoT | dsr1 | MI300X | sglang | fp8 | 30 | 24.6 | 64 | 411089 | 377 | 377 | 12.6 | 188 |
| CoT | dsr1 | MI300X | sglang | fp8 | 50 | 47.6 | 16 | 411097 | 182 | 182 | 3.638 | 90.5 |
| CoT | dsr1 | MI300X | sglang | fp8 | 70 | 68.6 | 4 | 411091 | 63.6 | 63.6 | 0.909 | 31.6 |
| CoT | dsr1 | MI325X | sglang | fp8 | 30 | 28.8 | 64 | 412358 | 440 | 440 | 14.7 | 220 |
| CoT | dsr1 | MI325X | sglang | fp8 | 50 | 52.0 | 16 | 412359 | 200 | 200 | 4.002 | 99.5 |
| CoT | dsr1 | MI325X | sglang | fp8 | 70 | 70.4 | 4 | 410365 | 66.1 | 66.1 | 0.945 | 32.9 |
| CoT | dsr1 | MI355X | sglang | fp8 | 30 | 39.2 | 64 | 415864 | 589 | 589 | 19.6 | 294 |
| CoT | dsr1 | MI355X | sglang | fp8 | 50 | 52.6 | 32 | 415856 | 393 | 393 | 7.858 | 197 |
| CoT | dsr1 | MI355X | sglang | fp8 | 70 | 75.4 | 16 | 415865 | 281 | 281 | 4.021 | 140 |
| CoT | dsv4 | GB200 | dynamo-vllm | fp4 | 30 | 29.8 | 64 | 201985 | 221 | 221 | 7.371 | 221 |
| CoT | dsv4 | GB200 | dynamo-vllm | fp4 | 50 | 45.5 | 16 | 201981 | 76.4 | 76.4 | 1.528 | 76.0 |
| CoT | dsv4 | GB200 | dynamo-vllm | fp4 | 70 | 64.8 | 4 | 201984 | 26.0 | 26.0 | 0.372 | 25.9 |
| CoT | glm5 | B200 | sglang | fp8 | 30 | 26.4 | 128 | 412388 | 834 | 834 | 27.8 | 416 |
| CoT | glm5 | B200 | sglang | fp8 | 50 | 51.5 | 8 | 412397 | 99.4 | 99.4 | 1.988 | 49.9 |
| CoT | glm5 | B200 | sglang | fp8 | 70 | 71.5 | 16 | 412402 | 275 | 275 | 3.928 | 137 |
| CoT | glm5 | B300 | sglang | fp8 | 30 | 32.3 | 128 | 411138 | 1,005 | 1,005 | 33.5 | 502 |
| CoT | glm5 | B300 | sglang | fp8 | 50 | 47.0 | 64 | 411142 | 726 | 726 | 14.5 | 363 |
| CoT | glm5 | B300 | sglang | fp8 | 70 | 68.0 | 32 | 411131 | 519 | 519 | 7.414 | 260 |
| CoT | glm5 | H200 | sglang | fp8 | 30 | 28.4 | 32 | 413437 | 222 | 222 | 7.408 | 111 |
| CoT | glm5 | H200 | sglang | fp8 | 50 | 50.3 | 8 | 413440 | 97.1 | 97.1 | 1.941 | 48.7 |
| CoT | glm5 | H200 | sglang | fp8 | 70 | 60.5 | 4 | 413439 | 57.8 | 57.8 | 0.826 | 28.8 |
| CoT | glm5 | MI325X | sglang | fp8 | 30 | 30.6 | 8 | 413693 | 56.9 | 56.9 | 1.896 | 28.5 |
| CoT | glm5 | MI325X | sglang | fp8 | 50 | 34.5 | 4 | 413692 | 31.9 | 31.9 | 0.639 | 15.9 |
| CoT | glm5 | MI325X | sglang | fp8 | 70 | 34.5 | 4 | 413692 | 31.9 | 31.9 | 0.456 | 15.9 |
| CoT | glm5 | MI355X | sglang | fp8 | 30 | 28.0 | 32 | 413081 | 432 | 432 | 14.4 | 216 |
| CoT | glm5 | MI355X | sglang | fp8 | 50 | 48.2 | 4 | 413057 | 93.0 | 93.0 | 1.86 | 46.3 |
| CoT | glm5 | MI355X | sglang | fp8 | 70 | 75.9 | 8 | 413060 | 293 | 293 | 4.18 | 147 |
| CoT | glm5.1 | MI355X | sglang | fp4 | 30 | 31.9 | 16 | 416691 | 498 | 498 | 16.6 | 248 |
| CoT | glm5.1 | MI355X | sglang | fp4 | 50 | 50.3 | 8 | 416697 | 195 | 195 | 3.899 | 97.8 |
| CoT | glm5.1 | MI355X | sglang | fp4 | 70 | 56.6 | 4 | 416698 | 109 | 109 | 1.562 | 54.4 |
| CoT | gptoss120b | B200 | vllm | fp4 | 30 | 78.7 | 128 | 417468 | 19,625 | 19,625 | 654 | 9,802 |
| CoT | gptoss120b | B200 | vllm | fp4 | 50 | 78.7 | 128 | 417468 | 19,625 | 19,625 | 393 | 9,802 |
| CoT | gptoss120b | B200 | vllm | fp4 | 70 | 78.7 | 128 | 417468 | 19,625 | 19,625 | 280 | 9,802 |
| CoT | gptoss120b | H100 | vllm | fp4 | 30 | 66.6 | 64 | 409803 | 4,160 | 4,160 | 139 | 2,079 |
| CoT | gptoss120b | H100 | vllm | fp4 | 50 | 66.6 | 64 | 409803 | 4,160 | 4,160 | 83.2 | 2,079 |
| CoT | gptoss120b | H100 | vllm | fp4 | 70 | 66.6 | 64 | 409803 | 4,160 | 4,160 | 59.4 | 2,079 |
| CoT | gptoss120b | H200 | vllm | fp4 | 30 | 68.0 | 64 | 416861 | 4,260 | 4,260 | 142 | 2,129 |
| CoT | gptoss120b | H200 | vllm | fp4 | 50 | 68.0 | 64 | 416861 | 4,260 | 4,260 | 85.2 | 2,129 |
| CoT | gptoss120b | H200 | vllm | fp4 | 70 | 68.0 | 64 | 416861 | 4,260 | 4,260 | 60.9 | 2,129 |
| CoT | gptoss120b | MI300X | vllm | fp4 | 30 | 31.7 | 64 | 200928 | 3,963 | 3,963 | 132 | 1,981 |
| CoT | gptoss120b | MI300X | vllm | fp4 | 50 | 60.3 | 64 | 200937 | 3,739 | 3,739 | 74.8 | 1,869 |
| CoT | gptoss120b | MI300X | vllm | fp4 | 70 | 74.2 | 64 | 200935 | 2,281 | 2,281 | 32.6 | 1,140 |
| CoT | gptoss120b | MI325X | vllm | fp4 | 30 | 29.2 | 64 | 417110 | 3,648 | 3,648 | 122 | 1,824 |
| CoT | gptoss120b | MI325X | vllm | fp4 | 50 | 51.8 | 16 | 417117 | 1,626 | 1,626 | 32.5 | 809 |
| CoT | gptoss120b | MI325X | vllm | fp4 | 70 | 70.3 | 64 | 417124 | 2,136 | 2,136 | 30.5 | 1,068 |
| CoT | gptoss120b | MI355X | vllm | fp4 | 30 | 70.0 | 128 | 419973 | 17,568 | 17,568 | 586 | 8,774 |
| CoT | gptoss120b | MI355X | vllm | fp4 | 50 | 70.0 | 128 | 419973 | 17,568 | 17,568 | 351 | 8,774 |
| CoT | gptoss120b | MI355X | vllm | fp4 | 70 | 70.0 | 128 | 419973 | 17,568 | 17,568 | 251 | 8,774 |
| CoT | kimik2.5 | B200 | vllm | int4 | 30 | 37.5 | 64 | 417580 | 587 | 587 | 19.6 | 294 |
| CoT | kimik2.5 | B200 | vllm | int4 | 50 | 52.6 | 32 | 417579 | 408 | 408 | 8.169 | 205 |
| CoT | kimik2.5 | B200 | vllm | int4 | 70 | 68.9 | 16 | 417581 | 270 | 270 | 3.855 | 134 |
| CoT | kimik2.5 | B300 | vllm | int4 | 30 | 27.4 | 64 | 411789 | 862 | 862 | 28.7 | 431 |
| CoT | kimik2.5 | B300 | vllm | int4 | 50 | 53.0 | 16 | 411797 | 415 | 415 | 8.309 | 207 |
| CoT | kimik2.5 | B300 | vllm | int4 | 70 | 72.7 | 16 | 411786 | 285 | 285 | 4.075 | 142 |
| CoT | kimik2.5 | H200 | vllm | int4 | 30 | 33.2 | 64 | 416973 | 521 | 521 | 17.4 | 261 |
| CoT | kimik2.5 | H200 | vllm | int4 | 50 | 45.6 | 32 | 416971 | 354 | 354 | 7.078 | 177 |
| CoT | kimik2.5 | H200 | vllm | int4 | 70 | 64.1 | 16 | 416967 | 251 | 251 | 3.587 | 125 |
| CoT | kimik2.5 | MI300X | vllm | int4 | 30 | 28.0 | 16 | 410190 | 110 | 110 | 3.662 | 54.6 |
| CoT | kimik2.5 | MI300X | vllm | int4 | 50 | 48.9 | 4 | 410187 | 47.5 | 47.5 | 0.949 | 23.6 |
| CoT | kimik2.5 | MI300X | vllm | int4 | 70 | 48.9 | 4 | 410187 | 47.5 | 47.5 | 0.678 | 23.6 |
| CoT | kimik2.5 | MI325X | vllm | int4 | 30 | 32.7 | 16 | 410612 | 128 | 128 | 4.282 | 63.9 |
| CoT | kimik2.5 | MI325X | vllm | int4 | 50 | 51.4 | 4 | 410620 | 49.9 | 49.9 | 0.997 | 24.8 |
| CoT | kimik2.5 | MI325X | vllm | int4 | 70 | 51.4 | 4 | 410620 | 49.9 | 49.9 | 0.712 | 24.8 |
| CoT | kimik2.5 | MI355X | vllm | int4 | 30 | 30.4 | 8 | 409342 | 58.8 | 58.8 | 1.959 | 29.5 |
| CoT | kimik2.5 | MI355X | vllm | int4 | 50 | 43.5 | 4 | 409339 | 41.6 | 41.6 | 0.831 | 20.7 |
| CoT | kimik2.5 | MI355X | vllm | int4 | 70 | 43.5 | 4 | 409339 | 41.6 | 41.6 | 0.594 | 20.7 |
| CoT | llama70b | B200 | vllm | fp8 | 30 | 43.1 | 64 | 39409 | 5,255 | 5,255 | 175 | 2,627 |
| CoT | llama70b | B200 | vllm | fp8 | 50 | 51.3 | 32 | 39780 | 3,125 | 3,125 | 62.5 | 1,565 |
| CoT | llama70b | B200 | vllm | fp8 | 70 | 65.1 | 64 | 39458 | 3,822 | 3,822 | 54.6 | 1,911 |
| CoT | llama70b | H100 | vllm | fp8 | 30 | 34.4 | 64 | 42096 | 2,123 | 2,123 | 70.8 | 1,061 |
| CoT | llama70b | H100 | vllm | fp8 | 50 | 50.4 | 16 | 41533 | 785 | 785 | 15.7 | 391 |
| CoT | llama70b | H100 | vllm | fp8 | 70 | 75.4 | 16 | 41181 | 590 | 590 | 8.425 | 293 |
| CoT | llama70b | H200 | vllm | fp8 | 30 | 29.9 | 32 | 39593 | 1,851 | 1,851 | 61.7 | 927 |
| CoT | llama70b | H200 | vllm | fp8 | 50 | 48.7 | 32 | 39937 | 1,510 | 1,510 | 30.2 | 756 |
| CoT | llama70b | H200 | vllm | fp8 | 70 | 69.4 | 8 | 40319 | 536 | 536 | 7.661 | 269 |
| CoT | llama70b | MI300X | vllm | fp8 | 30 | 30.0 | 64 | 40345 | 1,873 | 1,873 | 62.4 | 936 |
| CoT | llama70b | MI300X | vllm | fp8 | 50 | 50.2 | 16 | 39912 | 783 | 783 | 15.7 | 389 |
| CoT | llama70b | MI300X | vllm | fp8 | 70 | 74.5 | 16 | 40373 | 580 | 580 | 8.291 | 289 |
| CoT | llama70b | MI325X | vllm | fp8 | 30 | 32.8 | 64 | 39819 | 2,041 | 2,041 | 68.0 | 1,021 |
| CoT | llama70b | MI325X | vllm | fp8 | 50 | 50.3 | 64 | 39711 | 1,565 | 1,565 | 31.3 | 782 |
| CoT | llama70b | MI325X | vllm | fp8 | 70 | 68.9 | 16 | 39586 | 535 | 535 | 7.649 | 266 |
| CoT | llama70b | MI355X | vllm | fp8 | 30 | 33.2 | 64 | 40006 | 4,159 | 4,159 | 139 | 2,079 |
| CoT | llama70b | MI355X | vllm | fp8 | 50 | 54.5 | 16 | 39538 | 1,696 | 1,696 | 33.9 | 844 |
| CoT | llama70b | MI355X | vllm | fp8 | 70 | 71.3 | 16 | 39640 | 1,110 | 1,110 | 15.9 | 552 |
| CoT | minimaxm2.5 | B200 | vllm | fp8 | 30 | 31.5 | 512 | 417625 | 7,805 | 7,805 | 260 | 3,904 |
| CoT | minimaxm2.5 | B200 | vllm | fp8 | 50 | 44.3 | 256 | 417610 | 5,486 | 5,486 | 110 | 2,744 |
| CoT | minimaxm2.5 | B200 | vllm | fp8 | 70 | 72.9 | 64 | 417612 | 2,265 | 2,265 | 32.4 | 1,132 |
| CoT | minimaxm2.5 | B300 | vllm | fp8 | 30 | 32.8 | 512 | 411036 | 8,107 | 8,107 | 270 | 4,055 |
| CoT | minimaxm2.5 | B300 | vllm | fp8 | 50 | 44.5 | 256 | 411033 | 5,515 | 5,515 | 110 | 2,759 |
| CoT | minimaxm2.5 | B300 | vllm | fp8 | 70 | 72.0 | 64 | 411031 | 2,232 | 2,232 | 31.9 | 1,116 |
| CoT | minimaxm2.5 | H100 | vllm | fp8 | 30 | 40.4 | 128 | 419522 | 1,267 | 1,267 | 42.2 | 633 |
| CoT | minimaxm2.5 | H100 | vllm | fp8 | 50 | 51.1 | 64 | 419545 | 800 | 800 | 16.0 | 400 |
| CoT | minimaxm2.5 | H100 | vllm | fp8 | 70 | 65.9 | 32 | 419599 | 513 | 513 | 7.327 | 257 |
| CoT | minimaxm2.5 | H200 | vllm | fp8 | 30 | 24.6 | 256 | 419846 | 3,094 | 3,094 | 103 | 1,548 |
| CoT | minimaxm2.5 | H200 | vllm | fp8 | 50 | 45.7 | 64 | 419849 | 1,430 | 1,430 | 28.6 | 715 |
| CoT | minimaxm2.5 | H200 | vllm | fp8 | 70 | 58.7 | 32 | 419836 | 914 | 914 | 13.1 | 458 |
| CoT | minimaxm2.5 | MI300X | vllm | fp8 | 30 | 26.2 | 64 | 410279 | 1,643 | 1,643 | 54.8 | 821 |
| CoT | minimaxm2.5 | MI300X | vllm | fp8 | 50 | 52.7 | 16 | 410277 | 824 | 824 | 16.5 | 410 |
| CoT | minimaxm2.5 | MI300X | vllm | fp8 | 70 | 70.4 | 16 | 410274 | 550 | 550 | 7.863 | 274 |
| CoT | minimaxm2.5 | MI325X | vllm | fp8 | 30 | 30.2 | 64 | 417053 | 1,887 | 1,887 | 62.9 | 943 |
| CoT | minimaxm2.5 | MI325X | vllm | fp8 | 50 | 48.2 | 128 | 417052 | 1,499 | 1,499 | 30.0 | 749 |
| CoT | minimaxm2.5 | MI325X | vllm | fp8 | 70 | 70.9 | 8 | 416620 | 552 | 552 | 7.88 | 277 |
| CoT | minimaxm2.5 | MI355X | vllm | fp8 | 30 | 30.3 | 256 | 417307 | 3,772 | 3,772 | 126 | 1,887 |
| CoT | minimaxm2.5 | MI355X | vllm | fp8 | 50 | 52.9 | 64 | 417290 | 1,650 | 1,650 | 33.0 | 825 |
| CoT | minimaxm2.5 | MI355X | vllm | fp8 | 70 | 70.1 | 16 | 417303 | 1,098 | 1,098 | 15.7 | 546 |
| CoT | qwen3.5 | B200 | sglang | fp8 | 30 | 29.7 | 256 | 411578 | 3,648 | 3,648 | 122 | 1,825 |
| CoT | qwen3.5 | B200 | sglang | fp8 | 50 | 51.6 | 64 | 411593 | 1,582 | 1,582 | 31.6 | 791 |
| CoT | qwen3.5 | B200 | sglang | fp8 | 70 | 65.2 | 32 | 411577 | 995 | 995 | 14.2 | 498 |
| CoT | qwen3.5 | B300 | sglang | fp8 | 30 | 29.2 | 256 | 414745 | 3,680 | 3,680 | 123 | 1,839 |
| CoT | qwen3.5 | B300 | sglang | fp8 | 50 | 52.5 | 64 | 414744 | 1,641 | 1,641 | 32.8 | 820 |
| CoT | qwen3.5 | B300 | sglang | fp8 | 70 | 70.6 | 32 | 414720 | 1,084 | 1,084 | 15.5 | 543 |
| CoT | qwen3.5 | H100 | sglang | fp8 | 30 | 28.3 | 256 | 419475 | 1,316 | 1,316 | 43.9 | 659 |
| CoT | qwen3.5 | H100 | sglang | fp8 | 50 | 52.2 | 64 | 419476 | 734 | 734 | 14.7 | 367 |
| CoT | qwen3.5 | H100 | sglang | fp8 | 70 | 66.5 | 16 | 419468 | 256 | 256 | 3.655 | 127 |
| CoT | qwen3.5 | H200 | sglang | fp8 | 30 | 33.9 | 64 | 415869 | 541 | 541 | 18.0 | 271 |
| CoT | qwen3.5 | H200 | sglang | fp8 | 50 | 49.0 | 32 | 415868 | 385 | 385 | 7.695 | 193 |
| CoT | qwen3.5 | H200 | sglang | fp8 | 70 | 67.6 | 16 | 415867 | 265 | 265 | 3.786 | 132 |
| CoT | qwen3.5 | MI300X | sglang | fp8 | 30 | 33.6 | 64 | 410213 | 509 | 509 | 17.0 | 255 |
| CoT | qwen3.5 | MI300X | sglang | fp8 | 50 | 52.2 | 16 | 410217 | 198 | 198 | 3.966 | 98.6 |
| CoT | qwen3.5 | MI300X | sglang | fp8 | 70 | 71.8 | 4 | 410219 | 66.8 | 66.8 | 0.954 | 33.2 |
| CoT | qwen3.5 | MI325X | sglang | fp8 | 30 | 36.8 | 64 | 412476 | 557 | 557 | 18.6 | 278 |
| CoT | qwen3.5 | MI325X | sglang | fp8 | 50 | 48.1 | 32 | 412475 | 364 | 364 | 7.286 | 182 |
| CoT | qwen3.5 | MI325X | sglang | fp8 | 70 | 72.7 | 4 | 412468 | 68.1 | 68.1 | 0.973 | 33.9 |
| CoT | qwen3.5 | MI355X | sglang | fp8 | 30 | 32.6 | 128 | 420036 | 2,001 | 2,001 | 66.7 | 999 |
| CoT | qwen3.5 | MI355X | sglang | fp8 | 50 | 55.5 | 32 | 420040 | 850 | 850 | 17.0 | 426 |
| CoT | qwen3.5 | MI355X | sglang | fp8 | 70 | 69.2 | 16 | 420026 | 533 | 533 | 7.62 | 265 |

### Agentic

| Workload | Model | GPU | Framework | Precision | Target tok/s/user | Realized tok/s/user | Conc. | Bench ID | Base total tok/s/GPU | Scenario total tok/s/GPU | Users/GPU | Output tok/s/GPU |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Agentic | dsr1 | B200 | sglang | fp8 | 30 | 28.8 | 256 | 415291 | 1,707 | 186 | 6.186 | 854 |
| Agentic | dsr1 | B200 | sglang | fp8 | 50 | 45.9 | 64 | 415318 | 678 | 73.7 | 1.474 | 339 |
| Agentic | dsr1 | B200 | sglang | fp8 | 70 | 76.2 | 16 | 415279 | 292 | 31.7 | 0.453 | 145 |
| Agentic | dsr1 | B300 | sglang | fp8 | 30 | 30.4 | 256 | 415284 | 1,808 | 197 | 6.551 | 904 |
| Agentic | dsr1 | B300 | sglang | fp8 | 50 | 47.2 | 64 | 415343 | 714 | 77.6 | 1.552 | 357 |
| Agentic | dsr1 | B300 | sglang | fp8 | 70 | 64.0 | 32 | 415315 | 491 | 53.4 | 0.762 | 246 |
| Agentic | dsr1 | H200 | sglang | fp8 | 30 | 31.8 | 64 | 413853 | 506 | 55.0 | 1.832 | 253 |
| Agentic | dsr1 | H200 | sglang | fp8 | 50 | 44.7 | 32 | 413846 | 354 | 38.5 | 0.77 | 177 |
| Agentic | dsr1 | H200 | sglang | fp8 | 70 | 60.8 | 16 | 413848 | 241 | 26.2 | 0.374 | 120 |
| Agentic | dsr1 | MI300X | sglang | fp8 | 30 | 24.6 | 64 | 411089 | 377 | 41.0 | 1.366 | 188 |
| Agentic | dsr1 | MI300X | sglang | fp8 | 50 | 47.6 | 16 | 411097 | 182 | 19.8 | 0.395 | 90.5 |
| Agentic | dsr1 | MI300X | sglang | fp8 | 70 | 68.6 | 4 | 411091 | 63.6 | 6.913 | 0.099 | 31.6 |
| Agentic | dsr1 | MI325X | sglang | fp8 | 30 | 28.8 | 64 | 412358 | 440 | 47.8 | 1.593 | 220 |
| Agentic | dsr1 | MI325X | sglang | fp8 | 50 | 52.0 | 16 | 412359 | 200 | 21.7 | 0.435 | 99.5 |
| Agentic | dsr1 | MI325X | sglang | fp8 | 70 | 70.4 | 4 | 410365 | 66.1 | 7.187 | 0.103 | 32.9 |
| Agentic | dsr1 | MI355X | sglang | fp8 | 30 | 39.2 | 64 | 415864 | 589 | 64.0 | 2.132 | 294 |
| Agentic | dsr1 | MI355X | sglang | fp8 | 50 | 52.6 | 32 | 415856 | 393 | 42.7 | 0.854 | 197 |
| Agentic | dsr1 | MI355X | sglang | fp8 | 70 | 75.4 | 16 | 415865 | 281 | 30.6 | 0.437 | 140 |
| Agentic | dsv4 | GB200 | dynamo-vllm | fp4 | 30 | 29.8 | 64 | 201985 | 221 | 24.0 | 0.801 | 221 |
| Agentic | dsv4 | GB200 | dynamo-vllm | fp4 | 50 | 45.5 | 16 | 201981 | 76.4 | 8.303 | 0.166 | 76.0 |
| Agentic | dsv4 | GB200 | dynamo-vllm | fp4 | 70 | 64.8 | 4 | 201984 | 26.0 | 2.831 | 0.04 | 25.9 |
| Agentic | glm5 | B200 | sglang | fp8 | 30 | 26.4 | 128 | 412388 | 834 | 90.6 | 3.021 | 416 |
| Agentic | glm5 | B200 | sglang | fp8 | 50 | 51.5 | 8 | 412397 | 99.4 | 10.8 | 0.216 | 49.9 |
| Agentic | glm5 | B200 | sglang | fp8 | 70 | 71.5 | 16 | 412402 | 275 | 29.9 | 0.427 | 137 |
| Agentic | glm5 | B300 | sglang | fp8 | 30 | 32.3 | 128 | 411138 | 1,005 | 109 | 3.64 | 502 |
| Agentic | glm5 | B300 | sglang | fp8 | 50 | 47.0 | 64 | 411142 | 726 | 78.9 | 1.577 | 363 |
| Agentic | glm5 | B300 | sglang | fp8 | 70 | 68.0 | 32 | 411131 | 519 | 56.4 | 0.806 | 260 |
| Agentic | glm5 | H200 | sglang | fp8 | 30 | 28.4 | 32 | 413437 | 222 | 24.2 | 0.805 | 111 |
| Agentic | glm5 | H200 | sglang | fp8 | 50 | 50.3 | 8 | 413440 | 97.1 | 10.6 | 0.211 | 48.7 |
| Agentic | glm5 | H200 | sglang | fp8 | 70 | 60.5 | 4 | 413439 | 57.8 | 6.282 | 0.09 | 28.8 |
| Agentic | glm5 | MI325X | sglang | fp8 | 30 | 30.6 | 8 | 413693 | 56.9 | 6.182 | 0.206 | 28.5 |
| Agentic | glm5 | MI325X | sglang | fp8 | 50 | 34.5 | 4 | 413692 | 31.9 | 3.471 | 0.069 | 15.9 |
| Agentic | glm5 | MI325X | sglang | fp8 | 70 | 34.5 | 4 | 413692 | 31.9 | 3.471 | 0.05 | 15.9 |
| Agentic | glm5 | MI355X | sglang | fp8 | 30 | 28.0 | 32 | 413081 | 432 | 46.9 | 1.564 | 216 |
| Agentic | glm5 | MI355X | sglang | fp8 | 50 | 48.2 | 4 | 413057 | 93.0 | 10.1 | 0.202 | 46.3 |
| Agentic | glm5 | MI355X | sglang | fp8 | 70 | 75.9 | 8 | 413060 | 293 | 31.8 | 0.454 | 147 |
| Agentic | glm5.1 | MI355X | sglang | fp4 | 30 | 31.9 | 16 | 416691 | 498 | 54.2 | 1.806 | 248 |
| Agentic | glm5.1 | MI355X | sglang | fp4 | 50 | 50.3 | 8 | 416697 | 195 | 21.2 | 0.424 | 97.8 |
| Agentic | glm5.1 | MI355X | sglang | fp4 | 70 | 56.6 | 4 | 416698 | 109 | 11.9 | 0.17 | 54.4 |
| Agentic | gptoss120b | B200 | vllm | fp4 | 30 | 78.7 | 128 | 417468 | 19,625 | 2,133 | 71.1 | 9,802 |
| Agentic | gptoss120b | B200 | vllm | fp4 | 50 | 78.7 | 128 | 417468 | 19,625 | 2,133 | 42.7 | 9,802 |
| Agentic | gptoss120b | B200 | vllm | fp4 | 70 | 78.7 | 128 | 417468 | 19,625 | 2,133 | 30.5 | 9,802 |
| Agentic | gptoss120b | H100 | vllm | fp4 | 30 | 66.6 | 64 | 409803 | 4,160 | 452 | 15.1 | 2,079 |
| Agentic | gptoss120b | H100 | vllm | fp4 | 50 | 66.6 | 64 | 409803 | 4,160 | 452 | 9.042 | 2,079 |
| Agentic | gptoss120b | H100 | vllm | fp4 | 70 | 66.6 | 64 | 409803 | 4,160 | 452 | 6.459 | 2,079 |
| Agentic | gptoss120b | H200 | vllm | fp4 | 30 | 68.0 | 64 | 416861 | 4,260 | 463 | 15.4 | 2,129 |
| Agentic | gptoss120b | H200 | vllm | fp4 | 50 | 68.0 | 64 | 416861 | 4,260 | 463 | 9.26 | 2,129 |
| Agentic | gptoss120b | H200 | vllm | fp4 | 70 | 68.0 | 64 | 416861 | 4,260 | 463 | 6.615 | 2,129 |
| Agentic | gptoss120b | MI300X | vllm | fp4 | 30 | 31.7 | 64 | 200928 | 3,963 | 431 | 14.4 | 1,981 |
| Agentic | gptoss120b | MI300X | vllm | fp4 | 50 | 60.3 | 64 | 200937 | 3,739 | 406 | 8.129 | 1,869 |
| Agentic | gptoss120b | MI300X | vllm | fp4 | 70 | 74.2 | 64 | 200935 | 2,281 | 248 | 3.543 | 1,140 |
| Agentic | gptoss120b | MI325X | vllm | fp4 | 30 | 29.2 | 64 | 417110 | 3,648 | 397 | 13.2 | 1,824 |
| Agentic | gptoss120b | MI325X | vllm | fp4 | 50 | 51.8 | 16 | 417117 | 1,626 | 177 | 3.535 | 809 |
| Agentic | gptoss120b | MI325X | vllm | fp4 | 70 | 70.3 | 64 | 417124 | 2,136 | 232 | 3.316 | 1,068 |
| Agentic | gptoss120b | MI355X | vllm | fp4 | 30 | 70.0 | 128 | 419973 | 17,568 | 1,910 | 63.7 | 8,774 |
| Agentic | gptoss120b | MI355X | vllm | fp4 | 50 | 70.0 | 128 | 419973 | 17,568 | 1,910 | 38.2 | 8,774 |
| Agentic | gptoss120b | MI355X | vllm | fp4 | 70 | 70.0 | 128 | 419973 | 17,568 | 1,910 | 27.3 | 8,774 |
| Agentic | kimik2.5 | B200 | vllm | int4 | 30 | 37.5 | 64 | 417580 | 587 | 63.8 | 2.128 | 294 |
| Agentic | kimik2.5 | B200 | vllm | int4 | 50 | 52.6 | 32 | 417579 | 408 | 44.4 | 0.888 | 205 |
| Agentic | kimik2.5 | B200 | vllm | int4 | 70 | 68.9 | 16 | 417581 | 270 | 29.3 | 0.419 | 134 |
| Agentic | kimik2.5 | B300 | vllm | int4 | 30 | 27.4 | 64 | 411789 | 862 | 93.7 | 3.124 | 431 |
| Agentic | kimik2.5 | B300 | vllm | int4 | 50 | 53.0 | 16 | 411797 | 415 | 45.2 | 0.903 | 207 |
| Agentic | kimik2.5 | B300 | vllm | int4 | 70 | 72.7 | 16 | 411786 | 285 | 31.0 | 0.443 | 142 |
| Agentic | kimik2.5 | H200 | vllm | int4 | 30 | 33.2 | 64 | 416973 | 521 | 56.7 | 1.889 | 261 |
| Agentic | kimik2.5 | H200 | vllm | int4 | 50 | 45.6 | 32 | 416971 | 354 | 38.5 | 0.769 | 177 |
| Agentic | kimik2.5 | H200 | vllm | int4 | 70 | 64.1 | 16 | 416967 | 251 | 27.3 | 0.39 | 125 |
| Agentic | kimik2.5 | MI300X | vllm | int4 | 30 | 28.0 | 16 | 410190 | 110 | 11.9 | 0.398 | 54.6 |
| Agentic | kimik2.5 | MI300X | vllm | int4 | 50 | 48.9 | 4 | 410187 | 47.5 | 5.16 | 0.103 | 23.6 |
| Agentic | kimik2.5 | MI300X | vllm | int4 | 70 | 48.9 | 4 | 410187 | 47.5 | 5.16 | 0.074 | 23.6 |
| Agentic | kimik2.5 | MI325X | vllm | int4 | 30 | 32.7 | 16 | 410612 | 128 | 14.0 | 0.465 | 63.9 |
| Agentic | kimik2.5 | MI325X | vllm | int4 | 50 | 51.4 | 4 | 410620 | 49.9 | 5.419 | 0.108 | 24.8 |
| Agentic | kimik2.5 | MI325X | vllm | int4 | 70 | 51.4 | 4 | 410620 | 49.9 | 5.419 | 0.077 | 24.8 |
| Agentic | kimik2.5 | MI355X | vllm | int4 | 30 | 30.4 | 8 | 409342 | 58.8 | 6.389 | 0.213 | 29.5 |
| Agentic | kimik2.5 | MI355X | vllm | int4 | 50 | 43.5 | 4 | 409339 | 41.6 | 4.519 | 0.09 | 20.7 |
| Agentic | kimik2.5 | MI355X | vllm | int4 | 70 | 43.5 | 4 | 409339 | 41.6 | 4.519 | 0.065 | 20.7 |
| Agentic | llama70b | B200 | vllm | fp8 | 30 | 43.1 | 64 | 39409 | 5,255 | 571 | 19.0 | 2,627 |
| Agentic | llama70b | B200 | vllm | fp8 | 50 | 51.3 | 32 | 39780 | 3,125 | 340 | 6.793 | 1,565 |
| Agentic | llama70b | B200 | vllm | fp8 | 70 | 65.1 | 64 | 39458 | 3,822 | 415 | 5.935 | 1,911 |
| Agentic | llama70b | H100 | vllm | fp8 | 30 | 34.4 | 64 | 42096 | 2,123 | 231 | 7.692 | 1,061 |
| Agentic | llama70b | H100 | vllm | fp8 | 50 | 50.4 | 16 | 41533 | 785 | 85.3 | 1.707 | 391 |
| Agentic | llama70b | H100 | vllm | fp8 | 70 | 75.4 | 16 | 41181 | 590 | 64.1 | 0.916 | 293 |
| Agentic | llama70b | H200 | vllm | fp8 | 30 | 29.9 | 32 | 39593 | 1,851 | 201 | 6.707 | 927 |
| Agentic | llama70b | H200 | vllm | fp8 | 50 | 48.7 | 32 | 39937 | 1,510 | 164 | 3.282 | 756 |
| Agentic | llama70b | H200 | vllm | fp8 | 70 | 69.4 | 8 | 40319 | 536 | 58.3 | 0.833 | 269 |
| Agentic | llama70b | MI300X | vllm | fp8 | 30 | 30.0 | 64 | 40345 | 1,873 | 204 | 6.786 | 936 |
| Agentic | llama70b | MI300X | vllm | fp8 | 50 | 50.2 | 16 | 39912 | 783 | 85.1 | 1.701 | 389 |
| Agentic | llama70b | MI300X | vllm | fp8 | 70 | 74.5 | 16 | 40373 | 580 | 63.1 | 0.901 | 289 |
| Agentic | llama70b | MI325X | vllm | fp8 | 30 | 32.8 | 64 | 39819 | 2,041 | 222 | 7.397 | 1,021 |
| Agentic | llama70b | MI325X | vllm | fp8 | 50 | 50.3 | 64 | 39711 | 1,565 | 170 | 3.402 | 782 |
| Agentic | llama70b | MI325X | vllm | fp8 | 70 | 68.9 | 16 | 39586 | 535 | 58.2 | 0.831 | 266 |
| Agentic | llama70b | MI355X | vllm | fp8 | 30 | 33.2 | 64 | 40006 | 4,159 | 452 | 15.1 | 2,079 |
| Agentic | llama70b | MI355X | vllm | fp8 | 50 | 54.5 | 16 | 39538 | 1,696 | 184 | 3.688 | 844 |
| Agentic | llama70b | MI355X | vllm | fp8 | 70 | 71.3 | 16 | 39640 | 1,110 | 121 | 1.723 | 552 |
| Agentic | minimaxm2.5 | B200 | vllm | fp8 | 30 | 31.5 | 512 | 417625 | 7,805 | 848 | 28.3 | 3,904 |
| Agentic | minimaxm2.5 | B200 | vllm | fp8 | 50 | 44.3 | 256 | 417610 | 5,486 | 596 | 11.9 | 2,744 |
| Agentic | minimaxm2.5 | B200 | vllm | fp8 | 70 | 72.9 | 64 | 417612 | 2,265 | 246 | 3.517 | 1,132 |
| Agentic | minimaxm2.5 | B300 | vllm | fp8 | 30 | 32.8 | 512 | 411036 | 8,107 | 881 | 29.4 | 4,055 |
| Agentic | minimaxm2.5 | B300 | vllm | fp8 | 50 | 44.5 | 256 | 411033 | 5,515 | 599 | 12.0 | 2,759 |
| Agentic | minimaxm2.5 | B300 | vllm | fp8 | 70 | 72.0 | 64 | 411031 | 2,232 | 243 | 3.465 | 1,116 |
| Agentic | minimaxm2.5 | H100 | vllm | fp8 | 30 | 40.4 | 128 | 419522 | 1,267 | 138 | 4.592 | 633 |
| Agentic | minimaxm2.5 | H100 | vllm | fp8 | 50 | 51.1 | 64 | 419545 | 800 | 86.9 | 1.738 | 400 |
| Agentic | minimaxm2.5 | H100 | vllm | fp8 | 70 | 65.9 | 32 | 419599 | 513 | 55.7 | 0.796 | 257 |
| Agentic | minimaxm2.5 | H200 | vllm | fp8 | 30 | 24.6 | 256 | 419846 | 3,094 | 336 | 11.2 | 1,548 |
| Agentic | minimaxm2.5 | H200 | vllm | fp8 | 50 | 45.7 | 64 | 419849 | 1,430 | 155 | 3.109 | 715 |
| Agentic | minimaxm2.5 | H200 | vllm | fp8 | 70 | 58.7 | 32 | 419836 | 914 | 99.4 | 1.42 | 458 |
| Agentic | minimaxm2.5 | MI300X | vllm | fp8 | 30 | 26.2 | 64 | 410279 | 1,643 | 179 | 5.953 | 821 |
| Agentic | minimaxm2.5 | MI300X | vllm | fp8 | 50 | 52.7 | 16 | 410277 | 824 | 89.5 | 1.791 | 410 |
| Agentic | minimaxm2.5 | MI300X | vllm | fp8 | 70 | 70.4 | 16 | 410274 | 550 | 59.8 | 0.855 | 274 |
| Agentic | minimaxm2.5 | MI325X | vllm | fp8 | 30 | 30.2 | 64 | 417053 | 1,887 | 205 | 6.836 | 943 |
| Agentic | minimaxm2.5 | MI325X | vllm | fp8 | 50 | 48.2 | 128 | 417052 | 1,499 | 163 | 3.26 | 749 |
| Agentic | minimaxm2.5 | MI325X | vllm | fp8 | 70 | 70.9 | 8 | 416620 | 552 | 60.0 | 0.856 | 277 |
| Agentic | minimaxm2.5 | MI355X | vllm | fp8 | 30 | 30.3 | 256 | 417307 | 3,772 | 410 | 13.7 | 1,887 |
| Agentic | minimaxm2.5 | MI355X | vllm | fp8 | 50 | 52.9 | 64 | 417290 | 1,650 | 179 | 3.588 | 825 |
| Agentic | minimaxm2.5 | MI355X | vllm | fp8 | 70 | 70.1 | 16 | 417303 | 1,098 | 119 | 1.706 | 546 |
| Agentic | qwen3.5 | B200 | sglang | fp8 | 30 | 29.7 | 256 | 411578 | 3,648 | 396 | 13.2 | 1,825 |
| Agentic | qwen3.5 | B200 | sglang | fp8 | 50 | 51.6 | 64 | 411593 | 1,582 | 172 | 3.439 | 791 |
| Agentic | qwen3.5 | B200 | sglang | fp8 | 70 | 65.2 | 32 | 411577 | 995 | 108 | 1.545 | 498 |
| Agentic | qwen3.5 | B300 | sglang | fp8 | 30 | 29.2 | 256 | 414745 | 3,680 | 400 | 13.3 | 1,839 |
| Agentic | qwen3.5 | B300 | sglang | fp8 | 50 | 52.5 | 64 | 414744 | 1,641 | 178 | 3.568 | 820 |
| Agentic | qwen3.5 | B300 | sglang | fp8 | 70 | 70.6 | 32 | 414720 | 1,084 | 118 | 1.683 | 543 |
| Agentic | qwen3.5 | H100 | sglang | fp8 | 30 | 28.3 | 256 | 419475 | 1,316 | 143 | 4.769 | 659 |
| Agentic | qwen3.5 | H100 | sglang | fp8 | 50 | 52.2 | 64 | 419476 | 734 | 79.8 | 1.596 | 367 |
| Agentic | qwen3.5 | H100 | sglang | fp8 | 70 | 66.5 | 16 | 419468 | 256 | 27.8 | 0.397 | 127 |
| Agentic | qwen3.5 | H200 | sglang | fp8 | 30 | 33.9 | 64 | 415869 | 541 | 58.8 | 1.961 | 271 |
| Agentic | qwen3.5 | H200 | sglang | fp8 | 50 | 49.0 | 32 | 415868 | 385 | 41.8 | 0.836 | 193 |
| Agentic | qwen3.5 | H200 | sglang | fp8 | 70 | 67.6 | 16 | 415867 | 265 | 28.8 | 0.411 | 132 |
| Agentic | qwen3.5 | MI300X | sglang | fp8 | 30 | 33.6 | 64 | 410213 | 509 | 55.4 | 1.845 | 255 |
| Agentic | qwen3.5 | MI300X | sglang | fp8 | 50 | 52.2 | 16 | 410217 | 198 | 21.6 | 0.431 | 98.6 |
| Agentic | qwen3.5 | MI300X | sglang | fp8 | 70 | 71.8 | 4 | 410219 | 66.8 | 7.258 | 0.104 | 33.2 |
| Agentic | qwen3.5 | MI325X | sglang | fp8 | 30 | 36.8 | 64 | 412476 | 557 | 60.5 | 2.018 | 278 |
| Agentic | qwen3.5 | MI325X | sglang | fp8 | 50 | 48.1 | 32 | 412475 | 364 | 39.6 | 0.792 | 182 |
| Agentic | qwen3.5 | MI325X | sglang | fp8 | 70 | 72.7 | 4 | 412468 | 68.1 | 7.404 | 0.106 | 33.9 |
| Agentic | qwen3.5 | MI355X | sglang | fp8 | 30 | 32.6 | 128 | 420036 | 2,001 | 217 | 7.248 | 999 |
| Agentic | qwen3.5 | MI355X | sglang | fp8 | 50 | 55.5 | 32 | 420040 | 850 | 92.4 | 1.849 | 426 |
| Agentic | qwen3.5 | MI355X | sglang | fp8 | 70 | 69.2 | 16 | 420026 | 533 | 58.0 | 0.828 | 265 |

## 읽는 법

- `Base total tok/s/GPU`: InferenceX의 원본 total token throughput이다. InferenceX UI의 TPS/GPU와 맞추기 위해 이 값을 기본 벤치 TPS로 사용한다.
- `Output tok/s/GPU`: 같은 row의 output token throughput이다. ISL=OSL에서는 대체로 total의 절반에 가깝다.
- `Scenario total tok/s/GPU`: CoT는 원본 total TPS/GPU, agentic은 원본 total TPS/GPU를 9.2로 나눈 값이다.
- `Users/GPU`: 해당 target tok/s/user 기준으로 GPU 1장이 감당 가능한 사용자 수 근사값이다. `scenario total tok/s/GPU / target tok/s/user`로 계산한다.
- `Realized tok/s/user`: 선택된 InferenceX row의 `median_tpot`에서 역산한 실제 tok/s/user다. target과 정확히 같지 않을 수 있다.
- 이 표는 “전력 기반 토큰 생산량”에 바로 곱할 수 있는 candidate workload factor를 제공하지만, 최종 계수로 확정하려면 LLMServingSim power model에서 idle/standby/prefix-cache/KV-cache를 추가 검증해야 한다.
