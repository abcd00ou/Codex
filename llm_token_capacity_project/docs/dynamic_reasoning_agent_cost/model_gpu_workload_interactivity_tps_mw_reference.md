# Model/GPU/Workload Interactivity TPS/MW Reference

작성일: 2026-07-24

## 목적

이 표는 전력 기반 token capacity 엑셀에서 사용자가 `proxy_model`, `GPU`, `workload(short/long/agentic)`, `interactivity target`별로 output token throughput per MW를 선택할 수 있도록 만든 정리표다.

## 기준

- 단위: generated output tokens/sec/MW.
- Interactivity target: `10`, `30`, `50`, `70`, `100` tok/s/user.
- Short workload: `ISL/OSL 1024/1024`.
- Long workload: `ISL/OSL 8192/1024`.
- Agentic workload: 직접 matched agentic benchmark가 부족하므로 long workload TPS/MW를 dynamic reasoning coefficient로 보정한다.
- Agentic coefficient: `9.2x` LLM calls/request, 즉 effective throughput은 long-chat 대비 `10.9%`.
- Precision/concurrency/framework는 선택된 InferenceX row 또는 long-chat proxy row의 실제 조건을 그대로 유지한다.
- `target_met = FALSE`는 해당 interactivity에서 SLO를 만족했다고 보기 어렵다는 뜻이다. 이 경우 숫자는 sensitivity/proxy로만 쓰고, production capacity로 단정하지 않는다.

## Workload별 범위

| Workload | Rows with value | Min TPS/MW | Average TPS/MW | Max TPS/MW |
| --- | --- | --- | --- | --- |
| short | 50 | 40,586 | 809,860 | 4,516,967 |
| long | 55 | 7,963 | 432,573 | 2,629,943 |
| agentic | 55 | 866 | 28,289 | 184,775 |

## Target을 만족하는 최대 interactivity 추천 row

| Model | GPU | Workload | Max target | TPS/MW | Actual tok/s/user | Precision | Framework | Concurrency | Source type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dsr1` | B200 | long | 10 | 79,568 | 10.79 | fp8 | sglang | 16 | direct_target_row |
| `dsr1` | B200 | short | 10 | 87,925 | 11.92 | fp8 | sglang | 16 | direct_target_row |
| `dsr1` | H200 | long | 10 | 27,722 | 11.99 | fp8 | sglang | 4 | direct_target_row |
| `dsr1` | H200 | short | 10 | 47,614 | 10.30 | fp8 | sglang | 8 | direct_target_row |
| `frontier_composite` | B200 | long | 10 | 22,902 | 12.42 | int4 | vllm | 4 | direct_target_row |
| `frontier_composite` | B200 | short | 10 | 40,586 | 11.01 | int4 | vllm | 8 | direct_target_row |
| `frontier_composite` | GB200 | long | 10 | 7,963 | 16.72 | fp4 | dynamo-vllm | 1 | direct_target_row |
| `frontier_composite` | H200 | agentic | 10 | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | H200 | long | 100 | 329,414 | 142.47 | fp4 | vllm | 4 | direct_target_row |
| `frontier_composite` | H200 | short | 100 | 505,857 | 109.39 | fp4 | vllm | 8 | direct_target_row |
| `gptoss120b` | B200 | agentic | 10 | 184,775 | 12.53 | fp4 | vllm | 32 | dynamic_reasoning_proxy |
| `gptoss120b` | B200 | long | 100 | 1,699,929 | 115.28 | fp4 | vllm | 32 | direct_target_row |
| `gptoss120b` | B200 | short | 100 | 2,983,848 | 101.17 | fp4 | vllm | 64 | direct_target_row |
| `gptoss120b` | H200 | agentic | 10 | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `gptoss120b` | H200 | long | 100 | 329,414 | 142.47 | fp4 | vllm | 4 | direct_target_row |
| `gptoss120b` | H200 | short | 100 | 505,857 | 109.39 | fp4 | vllm | 8 | direct_target_row |
| `llama70b` | B200 | long | 50 | 95,773 | 51.96 | fp8 | vllm | 4 | direct_target_row |
| `llama70b` | B200 | short | 50 | 412,192 | 55.90 | fp8 | vllm | 16 | direct_target_row |
| `llama70b` | H200 | long | 30 | 83,442 | 36.09 | fp8 | vllm | 4 | direct_target_row |
| `llama70b` | H200 | short | 30 | 364,069 | 39.36 | fp8 | vllm | 16 | direct_target_row |
| `qwen3.5` | B200 | long | 30 | 132,868 | 36.04 | fp8 | sglang | 8 | direct_target_row |
| `qwen3.5` | B200 | short | 30 | 229,498 | 31.13 | fp8 | sglang | 16 | direct_target_row |
| `qwen3.5` | H200 | long | 10 | 53,892 | 11.65 | fp8 | sglang | 8 | direct_target_row |
| `qwen3.5` | H200 | short | 10 | 67,884 | 14.68 | fp8 | sglang | 8 | direct_target_row |

## 전체 reference table

| Model | GPU | Workload | Target | Target met | SLO gap | TPS/MW | Actual tok/s/user | Precision | Framework | Concurrency | Source type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dsr1` | H200 | short | 10 | Y | 0.0% | 47,614 | 10.30 | fp8 | sglang | 8 | direct_target_row |
| `dsr1` | H200 | short | 30 | N | 65.7% | 47,614 | 10.30 | fp8 | sglang | 8 | best_available_below_target |
| `dsr1` | H200 | short | 50 | N | 79.4% | 47,614 | 10.30 | fp8 | sglang | 8 | best_available_below_target |
| `dsr1` | H200 | short | 70 | N | 85.3% | 47,614 | 10.30 | fp8 | sglang | 8 | best_available_below_target |
| `dsr1` | H200 | short | 100 | N | 89.7% | 47,614 | 10.30 | fp8 | sglang | 8 | best_available_below_target |
| `dsr1` | H200 | long | 10 | Y | 0.0% | 27,722 | 11.99 | fp8 | sglang | 4 | direct_target_row |
| `dsr1` | H200 | long | 30 | N | 60.0% | 27,722 | 11.99 | fp8 | sglang | 4 | best_available_below_target |
| `dsr1` | H200 | long | 50 | N | 76.0% | 27,722 | 11.99 | fp8 | sglang | 4 | best_available_below_target |
| `dsr1` | H200 | long | 70 | N | 82.9% | 27,722 | 11.99 | fp8 | sglang | 4 | best_available_below_target |
| `dsr1` | H200 | long | 100 | N | 88.0% | 27,722 | 11.99 | fp8 | sglang | 4 | best_available_below_target |
| `dsr1` | H200 | agentic | 10 | N | 87.0% | 3,013 | 1.30 | fp8 | sglang | 4 | dynamic_reasoning_proxy |
| `dsr1` | H200 | agentic | 30 | N | 95.7% | 3,013 | 1.30 | fp8 | sglang | 4 | dynamic_reasoning_proxy |
| `dsr1` | H200 | agentic | 50 | N | 97.4% | 3,013 | 1.30 | fp8 | sglang | 4 | dynamic_reasoning_proxy |
| `dsr1` | H200 | agentic | 70 | N | 98.1% | 3,013 | 1.30 | fp8 | sglang | 4 | dynamic_reasoning_proxy |
| `dsr1` | H200 | agentic | 100 | N | 98.7% | 3,013 | 1.30 | fp8 | sglang | 4 | dynamic_reasoning_proxy |
| `dsr1` | B200 | short | 10 | Y | 0.0% | 87,925 | 11.92 | fp8 | sglang | 16 | direct_target_row |
| `dsr1` | B200 | short | 30 | N | 60.3% | 87,925 | 11.92 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | short | 50 | N | 76.2% | 87,925 | 11.92 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | short | 70 | N | 83.0% | 87,925 | 11.92 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | short | 100 | N | 88.1% | 87,925 | 11.92 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | long | 10 | Y | 0.0% | 79,568 | 10.79 | fp8 | sglang | 16 | direct_target_row |
| `dsr1` | B200 | long | 30 | N | 64.0% | 79,568 | 10.79 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | long | 50 | N | 78.4% | 79,568 | 10.79 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | long | 70 | N | 84.6% | 79,568 | 10.79 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | long | 100 | N | 89.2% | 79,568 | 10.79 | fp8 | sglang | 16 | best_available_below_target |
| `dsr1` | B200 | agentic | 10 | N | 88.3% | 8,649 | 1.17 | fp8 | sglang | 16 | dynamic_reasoning_proxy |
| `dsr1` | B200 | agentic | 30 | N | 96.1% | 8,649 | 1.17 | fp8 | sglang | 16 | dynamic_reasoning_proxy |
| `dsr1` | B200 | agentic | 50 | N | 97.7% | 8,649 | 1.17 | fp8 | sglang | 16 | dynamic_reasoning_proxy |
| `dsr1` | B200 | agentic | 70 | N | 98.3% | 8,649 | 1.17 | fp8 | sglang | 16 | dynamic_reasoning_proxy |
| `dsr1` | B200 | agentic | 100 | N | 98.8% | 8,649 | 1.17 | fp8 | sglang | 16 | dynamic_reasoning_proxy |
| `dsr1` | GB200 | short | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | short | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | short | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | short | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | short | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | long | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | long | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | long | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | long | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | long | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `dsr1` | GB200 | agentic | 10 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `dsr1` | GB200 | agentic | 30 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `dsr1` | GB200 | agentic | 50 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `dsr1` | GB200 | agentic | 70 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `dsr1` | GB200 | agentic | 100 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `frontier_composite` | H200 | short | 10 | Y | 0.0% | 1,459,609 | 39.46 | fp4 | vllm | 64 | direct_target_row |
| `frontier_composite` | H200 | short | 30 | Y | 0.0% | 1,459,609 | 39.46 | fp4 | vllm | 64 | direct_target_row |
| `frontier_composite` | H200 | short | 50 | Y | 0.0% | 1,037,487 | 56.09 | fp4 | vllm | 32 | direct_target_row |
| `frontier_composite` | H200 | short | 70 | Y | 0.0% | 728,459 | 78.76 | fp4 | vllm | 16 | direct_target_row |
| `frontier_composite` | H200 | short | 100 | Y | 0.0% | 505,857 | 109.39 | fp4 | vllm | 8 | direct_target_row |
| `frontier_composite` | H200 | long | 10 | Y | 0.0% | 1,451,169 | 39.23 | fp4 | vllm | 64 | direct_target_row |
| `frontier_composite` | H200 | long | 30 | Y | 0.0% | 1,451,169 | 39.23 | fp4 | vllm | 64 | direct_target_row |
| `frontier_composite` | H200 | long | 50 | Y | 0.0% | 1,035,150 | 55.96 | fp4 | vllm | 32 | direct_target_row |
| `frontier_composite` | H200 | long | 70 | Y | 0.0% | 649,279 | 70.20 | fp4 | vllm | 16 | direct_target_row |
| `frontier_composite` | H200 | long | 100 | Y | 0.0% | 329,414 | 142.47 | fp4 | vllm | 4 | direct_target_row |
| `frontier_composite` | H200 | agentic | 10 | Y | 0.0% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | H200 | agentic | 30 | N | 48.4% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | H200 | agentic | 50 | N | 69.0% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | H200 | agentic | 70 | N | 77.9% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | H200 | agentic | 100 | N | 84.5% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | B200 | short | 10 | Y | 0.0% | 40,586 | 11.01 | int4 | vllm | 8 | direct_target_row |
| `frontier_composite` | B200 | short | 30 | N | 63.3% | 40,586 | 11.01 | int4 | vllm | 8 | best_available_below_target |
| `frontier_composite` | B200 | short | 50 | N | 78.0% | 40,586 | 11.01 | int4 | vllm | 8 | best_available_below_target |
| `frontier_composite` | B200 | short | 70 | N | 84.3% | 40,586 | 11.01 | int4 | vllm | 8 | best_available_below_target |
| `frontier_composite` | B200 | short | 100 | N | 89.0% | 40,586 | 11.01 | int4 | vllm | 8 | best_available_below_target |
| `frontier_composite` | B200 | long | 10 | Y | 0.0% | 22,902 | 12.42 | int4 | vllm | 4 | direct_target_row |
| `frontier_composite` | B200 | long | 30 | N | 58.6% | 22,902 | 12.42 | int4 | vllm | 4 | best_available_below_target |
| `frontier_composite` | B200 | long | 50 | N | 75.2% | 22,902 | 12.42 | int4 | vllm | 4 | best_available_below_target |
| `frontier_composite` | B200 | long | 70 | N | 82.3% | 22,902 | 12.42 | int4 | vllm | 4 | best_available_below_target |
| `frontier_composite` | B200 | long | 100 | N | 87.6% | 22,902 | 12.42 | int4 | vllm | 4 | best_available_below_target |
| `frontier_composite` | B200 | agentic | 10 | N | 86.5% | 2,489 | 1.35 | int4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | B200 | agentic | 30 | N | 95.5% | 2,489 | 1.35 | int4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | B200 | agentic | 50 | N | 97.3% | 2,489 | 1.35 | int4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | B200 | agentic | 70 | N | 98.1% | 2,489 | 1.35 | int4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | B200 | agentic | 100 | N | 98.7% | 2,489 | 1.35 | int4 | vllm | 4 | dynamic_reasoning_proxy |
| `frontier_composite` | GB200 | short | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `frontier_composite` | GB200 | short | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `frontier_composite` | GB200 | short | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `frontier_composite` | GB200 | short | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `frontier_composite` | GB200 | short | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `frontier_composite` | GB200 | long | 10 | Y | 0.0% | 7,963 | 16.72 | fp4 | dynamo-vllm | 1 | direct_target_row |
| `frontier_composite` | GB200 | long | 30 | N | 44.3% | 7,963 | 16.72 | fp4 | dynamo-vllm | 1 | best_available_below_target |
| `frontier_composite` | GB200 | long | 50 | N | 66.6% | 7,963 | 16.72 | fp4 | dynamo-vllm | 1 | best_available_below_target |
| `frontier_composite` | GB200 | long | 70 | N | 76.1% | 7,963 | 16.72 | fp4 | dynamo-vllm | 1 | best_available_below_target |
| `frontier_composite` | GB200 | long | 100 | N | 83.3% | 7,963 | 16.72 | fp4 | dynamo-vllm | 1 | best_available_below_target |
| `frontier_composite` | GB200 | agentic | 10 | N | 81.8% | 866 | 1.82 | fp4 | dynamo-vllm | 1 | dynamic_reasoning_proxy |
| `frontier_composite` | GB200 | agentic | 30 | N | 93.9% | 866 | 1.82 | fp4 | dynamo-vllm | 1 | dynamic_reasoning_proxy |
| `frontier_composite` | GB200 | agentic | 50 | N | 96.4% | 866 | 1.82 | fp4 | dynamo-vllm | 1 | dynamic_reasoning_proxy |
| `frontier_composite` | GB200 | agentic | 70 | N | 97.4% | 866 | 1.82 | fp4 | dynamo-vllm | 1 | dynamic_reasoning_proxy |
| `frontier_composite` | GB200 | agentic | 100 | N | 98.2% | 866 | 1.82 | fp4 | dynamo-vllm | 1 | dynamic_reasoning_proxy |
| `gptoss120b` | H200 | short | 10 | Y | 0.0% | 1,459,609 | 39.46 | fp4 | vllm | 64 | direct_target_row |
| `gptoss120b` | H200 | short | 30 | Y | 0.0% | 1,459,609 | 39.46 | fp4 | vllm | 64 | direct_target_row |
| `gptoss120b` | H200 | short | 50 | Y | 0.0% | 1,037,487 | 56.09 | fp4 | vllm | 32 | direct_target_row |
| `gptoss120b` | H200 | short | 70 | Y | 0.0% | 728,459 | 78.76 | fp4 | vllm | 16 | direct_target_row |
| `gptoss120b` | H200 | short | 100 | Y | 0.0% | 505,857 | 109.39 | fp4 | vllm | 8 | direct_target_row |
| `gptoss120b` | H200 | long | 10 | Y | 0.0% | 1,451,169 | 39.23 | fp4 | vllm | 64 | direct_target_row |
| `gptoss120b` | H200 | long | 30 | Y | 0.0% | 1,451,169 | 39.23 | fp4 | vllm | 64 | direct_target_row |
| `gptoss120b` | H200 | long | 50 | Y | 0.0% | 1,035,150 | 55.96 | fp4 | vllm | 32 | direct_target_row |
| `gptoss120b` | H200 | long | 70 | Y | 0.0% | 649,279 | 70.20 | fp4 | vllm | 16 | direct_target_row |
| `gptoss120b` | H200 | long | 100 | Y | 0.0% | 329,414 | 142.47 | fp4 | vllm | 4 | direct_target_row |
| `gptoss120b` | H200 | agentic | 10 | Y | 0.0% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `gptoss120b` | H200 | agentic | 30 | N | 48.4% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `gptoss120b` | H200 | agentic | 50 | N | 69.0% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `gptoss120b` | H200 | agentic | 70 | N | 77.9% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `gptoss120b` | H200 | agentic | 100 | N | 84.5% | 35,806 | 15.49 | fp4 | vllm | 4 | dynamic_reasoning_proxy |
| `gptoss120b` | B200 | short | 10 | Y | 0.0% | 4,516,967 | 76.58 | fp4 | vllm | 128 | direct_target_row |
| `gptoss120b` | B200 | short | 30 | Y | 0.0% | 4,516,967 | 76.58 | fp4 | vllm | 128 | direct_target_row |
| `gptoss120b` | B200 | short | 50 | Y | 0.0% | 4,516,967 | 76.58 | fp4 | vllm | 128 | direct_target_row |
| `gptoss120b` | B200 | short | 70 | Y | 0.0% | 4,516,967 | 76.58 | fp4 | vllm | 128 | direct_target_row |
| `gptoss120b` | B200 | short | 100 | Y | 0.0% | 2,983,848 | 101.17 | fp4 | vllm | 64 | direct_target_row |
| `gptoss120b` | B200 | long | 10 | Y | 0.0% | 2,629,943 | 44.59 | fp4 | vllm | 128 | direct_target_row |
| `gptoss120b` | B200 | long | 30 | Y | 0.0% | 2,629,943 | 44.59 | fp4 | vllm | 128 | direct_target_row |
| `gptoss120b` | B200 | long | 50 | Y | 0.0% | 1,978,039 | 67.07 | fp4 | vllm | 64 | direct_target_row |
| `gptoss120b` | B200 | long | 70 | Y | 0.0% | 1,699,929 | 115.28 | fp4 | vllm | 32 | direct_target_row |
| `gptoss120b` | B200 | long | 100 | Y | 0.0% | 1,699,929 | 115.28 | fp4 | vllm | 32 | direct_target_row |
| `gptoss120b` | B200 | agentic | 10 | Y | 0.0% | 184,775 | 12.53 | fp4 | vllm | 32 | dynamic_reasoning_proxy |
| `gptoss120b` | B200 | agentic | 30 | N | 58.2% | 184,775 | 12.53 | fp4 | vllm | 32 | dynamic_reasoning_proxy |
| `gptoss120b` | B200 | agentic | 50 | N | 74.9% | 184,775 | 12.53 | fp4 | vllm | 32 | dynamic_reasoning_proxy |
| `gptoss120b` | B200 | agentic | 70 | N | 82.1% | 184,775 | 12.53 | fp4 | vllm | 32 | dynamic_reasoning_proxy |
| `gptoss120b` | B200 | agentic | 100 | N | 87.5% | 184,775 | 12.53 | fp4 | vllm | 32 | dynamic_reasoning_proxy |
| `gptoss120b` | GB200 | short | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | short | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | short | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | short | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | short | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | long | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | long | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | long | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | long | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | long | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `gptoss120b` | GB200 | agentic | 10 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `gptoss120b` | GB200 | agentic | 30 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `gptoss120b` | GB200 | agentic | 50 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `gptoss120b` | GB200 | agentic | 70 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `gptoss120b` | GB200 | agentic | 100 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `llama70b` | H200 | short | 10 | Y | 0.0% | 965,061 | 26.09 | fp8 | vllm | 64 | direct_target_row |
| `llama70b` | H200 | short | 30 | Y | 0.0% | 364,069 | 39.36 | fp8 | vllm | 16 | direct_target_row |
| `llama70b` | H200 | short | 50 | N | 21.3% | 364,069 | 39.36 | fp8 | vllm | 16 | best_available_below_target |
| `llama70b` | H200 | short | 70 | N | 43.8% | 364,069 | 39.36 | fp8 | vllm | 16 | best_available_below_target |
| `llama70b` | H200 | short | 100 | N | 60.6% | 364,069 | 39.36 | fp8 | vllm | 16 | best_available_below_target |
| `llama70b` | H200 | long | 10 | Y | 0.0% | 231,275 | 12.50 | fp8 | vllm | 32 | direct_target_row |
| `llama70b` | H200 | long | 30 | Y | 0.0% | 83,442 | 36.09 | fp8 | vllm | 4 | direct_target_row |
| `llama70b` | H200 | long | 50 | N | 27.8% | 83,442 | 36.09 | fp8 | vllm | 4 | best_available_below_target |
| `llama70b` | H200 | long | 70 | N | 48.4% | 83,442 | 36.09 | fp8 | vllm | 4 | best_available_below_target |
| `llama70b` | H200 | long | 100 | N | 63.9% | 83,442 | 36.09 | fp8 | vllm | 4 | best_available_below_target |
| `llama70b` | H200 | agentic | 10 | N | 60.8% | 9,070 | 3.92 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | H200 | agentic | 30 | N | 86.9% | 9,070 | 3.92 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | H200 | agentic | 50 | N | 92.2% | 9,070 | 3.92 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | H200 | agentic | 70 | N | 94.4% | 9,070 | 3.92 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | H200 | agentic | 100 | N | 96.1% | 9,070 | 3.92 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | B200 | short | 10 | Y | 0.0% | 1,228,515 | 41.65 | fp8 | vllm | 64 | direct_target_row |
| `llama70b` | B200 | short | 30 | Y | 0.0% | 1,228,515 | 41.65 | fp8 | vllm | 64 | direct_target_row |
| `llama70b` | B200 | short | 50 | Y | 0.0% | 412,192 | 55.90 | fp8 | vllm | 16 | direct_target_row |
| `llama70b` | B200 | short | 70 | N | 20.1% | 412,192 | 55.90 | fp8 | vllm | 16 | best_available_below_target |
| `llama70b` | B200 | short | 100 | N | 44.1% | 412,192 | 55.90 | fp8 | vllm | 16 | best_available_below_target |
| `llama70b` | B200 | long | 10 | Y | 0.0% | 384,593 | 13.04 | fp8 | vllm | 64 | direct_target_row |
| `llama70b` | B200 | long | 30 | Y | 0.0% | 247,359 | 33.55 | fp8 | vllm | 16 | direct_target_row |
| `llama70b` | B200 | long | 50 | Y | 0.0% | 95,773 | 51.96 | fp8 | vllm | 4 | direct_target_row |
| `llama70b` | B200 | long | 70 | N | 25.8% | 95,773 | 51.96 | fp8 | vllm | 4 | best_available_below_target |
| `llama70b` | B200 | long | 100 | N | 48.0% | 95,773 | 51.96 | fp8 | vllm | 4 | best_available_below_target |
| `llama70b` | B200 | agentic | 10 | N | 43.5% | 10,410 | 5.65 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | B200 | agentic | 30 | N | 81.2% | 10,410 | 5.65 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | B200 | agentic | 50 | N | 88.7% | 10,410 | 5.65 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | B200 | agentic | 70 | N | 91.9% | 10,410 | 5.65 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | B200 | agentic | 100 | N | 94.4% | 10,410 | 5.65 | fp8 | vllm | 4 | dynamic_reasoning_proxy |
| `llama70b` | GB200 | short | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | short | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | short | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | short | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | short | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | long | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | long | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | long | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | long | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | long | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `llama70b` | GB200 | agentic | 10 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `llama70b` | GB200 | agentic | 30 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `llama70b` | GB200 | agentic | 50 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `llama70b` | GB200 | agentic | 70 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `llama70b` | GB200 | agentic | 100 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `qwen3.5` | H200 | short | 10 | Y | 0.0% | 67,884 | 14.68 | fp8 | sglang | 8 | direct_target_row |
| `qwen3.5` | H200 | short | 30 | N | 51.1% | 67,884 | 14.68 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | short | 50 | N | 70.6% | 67,884 | 14.68 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | short | 70 | N | 79.0% | 67,884 | 14.68 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | short | 100 | N | 85.3% | 67,884 | 14.68 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | long | 10 | Y | 0.0% | 53,892 | 11.65 | fp8 | sglang | 8 | direct_target_row |
| `qwen3.5` | H200 | long | 30 | N | 61.2% | 53,892 | 11.65 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | long | 50 | N | 76.7% | 53,892 | 11.65 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | long | 70 | N | 83.4% | 53,892 | 11.65 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | long | 100 | N | 88.3% | 53,892 | 11.65 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | H200 | agentic | 10 | N | 87.3% | 5,858 | 1.27 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | H200 | agentic | 30 | N | 95.8% | 5,858 | 1.27 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | H200 | agentic | 50 | N | 97.5% | 5,858 | 1.27 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | H200 | agentic | 70 | N | 98.2% | 5,858 | 1.27 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | H200 | agentic | 100 | N | 98.7% | 5,858 | 1.27 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | B200 | short | 10 | Y | 0.0% | 806,272 | 13.67 | fp8 | sglang | 128 | direct_target_row |
| `qwen3.5` | B200 | short | 30 | Y | 0.0% | 229,498 | 31.13 | fp8 | sglang | 16 | direct_target_row |
| `qwen3.5` | B200 | short | 50 | N | 37.7% | 229,498 | 31.13 | fp8 | sglang | 16 | best_available_below_target |
| `qwen3.5` | B200 | short | 70 | N | 55.5% | 229,498 | 31.13 | fp8 | sglang | 16 | best_available_below_target |
| `qwen3.5` | B200 | short | 100 | N | 68.9% | 229,498 | 31.13 | fp8 | sglang | 16 | best_available_below_target |
| `qwen3.5` | B200 | long | 10 | Y | 0.0% | 345,338 | 11.71 | fp8 | sglang | 64 | direct_target_row |
| `qwen3.5` | B200 | long | 30 | Y | 0.0% | 132,868 | 36.04 | fp8 | sglang | 8 | direct_target_row |
| `qwen3.5` | B200 | long | 50 | N | 27.9% | 132,868 | 36.04 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | B200 | long | 70 | N | 48.5% | 132,868 | 36.04 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | B200 | long | 100 | N | 64.0% | 132,868 | 36.04 | fp8 | sglang | 8 | best_available_below_target |
| `qwen3.5` | B200 | agentic | 10 | N | 60.8% | 14,442 | 3.92 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | B200 | agentic | 30 | N | 86.9% | 14,442 | 3.92 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | B200 | agentic | 50 | N | 92.2% | 14,442 | 3.92 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | B200 | agentic | 70 | N | 94.4% | 14,442 | 3.92 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | B200 | agentic | 100 | N | 96.1% | 14,442 | 3.92 | fp8 | sglang | 8 | dynamic_reasoning_proxy |
| `qwen3.5` | GB200 | short | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | short | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | short | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | short | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | short | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | long | 10 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | long | 30 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | long | 50 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | long | 70 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | long | 100 | N |  |  |  |  |  |  | no_benchmark_row |
| `qwen3.5` | GB200 | agentic | 10 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `qwen3.5` | GB200 | agentic | 30 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `qwen3.5` | GB200 | agentic | 50 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `qwen3.5` | GB200 | agentic | 70 | N |  |  |  |  |  |  | no_long_chat_proxy_row |
| `qwen3.5` | GB200 | agentic | 100 | N |  |  |  |  |  |  | no_long_chat_proxy_row |

## 해석 메모

- `direct_target_row`: target interactivity 이상을 만족하는 InferenceX row에서 TPS/MW가 높은 row를 선택했다.
- `best_available_below_target`: 해당 target을 만족하는 row가 없어 같은 model/GPU/workload에서 관측 가능한 최고 tok/s/user row를 proxy로 남겼다.
- `dynamic_reasoning_proxy`: long-chat row에 AgentBench/dynamic reasoning의 agentic call multiplier를 적용한 proxy다.
- `missing`: 해당 model/GPU/workload에 사용할 benchmark 또는 long-chat proxy row가 없다.
- 이 파일은 public benchmark/proxy reference이며 OpenAI, Anthropic, Google 등 closed production serving telemetry가 아니다.

## 연결 파일

- CSV: `model_gpu_workload_interactivity_tps_mw_reference.csv`
- 엑셀 시트: `llm_token_capacity_2026_2030.xlsx`의 `00a_Proxy_TPS_MW`
