# InferenceX Interactivity x GPU Serving Summary

작성일: 2026-07-30

## 기준

- 원천 데이터: `llm_token_capacity_project/data/inferencex/normalized/inferencex_benchmark_results.csv`
- Interactivity target: `10`, `30`, `50`, `70`, `100` generated tokens/sec/user
- Source `tok_s_user`가 비어 있어 `output_tok_s_gpu / concurrency`로 per-user generated token rate를 계산한다.
- Selection: target 이상 row 중 Dynamo/TRT-LLM/MTP 계열 stack이 있으면 그 안의 최고 `output_tok_s_mw`, 없으면 public max.
- Precision/concurrency/framework는 선택된 최고 TPS/MW row의 실제 조건을 그대로 사용한다.
- `agentic_derived`는 direct 100k-input benchmark가 아니라 long_chat row에 Kimi K2.5 agentic/long ratio `10.9%`를 곱한 effective 기준이다.

## GPU별 추천 구성

각 proxy/GPU/workload에서 가능한 가장 높은 interactivity target을 먼저 선택한다. 같은 target에서는 optimized stack을 우선한다.

| Proxy | GPU | Workload | Recommended target tok/s/user | TPS/MW | Actual tok/s/user | Concurrency | Framework | Precision | Status |
|---|---:|---|---:|---:|---:|---:|---|---|---|
| `dsr1` | B200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `dsr1` | B200 | long_chat | 10 | 79,568 | 10.79 | 16 | sglang | fp8 | selected_public_max |
| `dsr1` | B200 | short_chat | 10 | 87,925 | 11.92 | 16 | sglang | fp8 | selected_public_max |
| `dsr1` | GB200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `dsr1` | GB200 | long_chat | missing |  |  |  |  |  | no target available |
| `dsr1` | GB200 | short_chat | missing |  |  |  |  |  | no target available |
| `dsr1` | H200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `dsr1` | H200 | long_chat | 10 | 27,722 | 11.99 | 4 | sglang | fp8 | selected_public_max |
| `dsr1` | H200 | short_chat | 10 | 47,614 | 10.30 | 8 | sglang | fp8 | selected_public_max |
| `frontier_composite` | B200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `frontier_composite` | B200 | long_chat | 10 | 22,902 | 12.42 | 4 | vllm | int4 | selected_public_max |
| `frontier_composite` | B200 | short_chat | 10 | 40,586 | 11.01 | 8 | vllm | int4 | selected_public_max |
| `frontier_composite` | GB200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `frontier_composite` | GB200 | long_chat | 10 | 7,963 | 16.72 | 1 | dynamo-vllm | fp4 | selected_optimized_stack |
| `frontier_composite` | GB200 | short_chat | missing |  |  |  |  |  | no target available |
| `frontier_composite` | H200 | agentic_derived | 10 | 35,806 | 15.49 | 4 | vllm | fp4 | selected_public_max |
| `frontier_composite` | H200 | long_chat | 100 | 329,414 | 142.47 | 4 | vllm | fp4 | selected_public_max |
| `frontier_composite` | H200 | short_chat | 100 | 505,857 | 109.39 | 8 | vllm | fp4 | selected_public_max |
| `gptoss120b` | B200 | agentic_derived | 10 | 184,775 | 12.53 | 32 | vllm | fp4 | selected_public_max |
| `gptoss120b` | B200 | long_chat | 100 | 1,699,929 | 115.28 | 32 | vllm | fp4 | selected_public_max |
| `gptoss120b` | B200 | short_chat | 100 | 2,983,848 | 101.17 | 64 | vllm | fp4 | selected_public_max |
| `gptoss120b` | GB200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `gptoss120b` | GB200 | long_chat | missing |  |  |  |  |  | no target available |
| `gptoss120b` | GB200 | short_chat | missing |  |  |  |  |  | no target available |
| `gptoss120b` | H200 | agentic_derived | 10 | 35,806 | 15.49 | 4 | vllm | fp4 | selected_public_max |
| `gptoss120b` | H200 | long_chat | 100 | 329,414 | 142.47 | 4 | vllm | fp4 | selected_public_max |
| `gptoss120b` | H200 | short_chat | 100 | 505,857 | 109.39 | 8 | vllm | fp4 | selected_public_max |
| `llama70b` | B200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `llama70b` | B200 | long_chat | 50 | 95,773 | 51.96 | 4 | vllm | fp8 | selected_public_max |
| `llama70b` | B200 | short_chat | 50 | 412,192 | 55.90 | 16 | vllm | fp8 | selected_public_max |
| `llama70b` | GB200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `llama70b` | GB200 | long_chat | missing |  |  |  |  |  | no target available |
| `llama70b` | GB200 | short_chat | missing |  |  |  |  |  | no target available |
| `llama70b` | H200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `llama70b` | H200 | long_chat | 30 | 83,442 | 36.09 | 4 | vllm | fp8 | selected_public_max |
| `llama70b` | H200 | short_chat | 30 | 364,069 | 39.36 | 16 | vllm | fp8 | selected_public_max |
| `qwen3.5` | B200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `qwen3.5` | B200 | long_chat | 30 | 132,868 | 36.04 | 8 | sglang | fp8 | selected_public_max |
| `qwen3.5` | B200 | short_chat | 30 | 229,498 | 31.13 | 16 | sglang | fp8 | selected_public_max |
| `qwen3.5` | GB200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `qwen3.5` | GB200 | long_chat | missing |  |  |  |  |  | no target available |
| `qwen3.5` | GB200 | short_chat | missing |  |  |  |  |  | no target available |
| `qwen3.5` | H200 | agentic_derived | missing |  |  |  |  |  | no target available |
| `qwen3.5` | H200 | long_chat | 10 | 53,892 | 11.65 | 8 | sglang | fp8 | selected_public_max |
| `qwen3.5` | H200 | short_chat | 10 | 67,884 | 14.68 | 8 | sglang | fp8 | selected_public_max |

## 전체 후보

| Proxy | GPU | Workload | Target tok/s/user | Eligible rows | Optimized rows | TPS/MW | Actual tok/s/user | Concurrency | Framework | Precision | Status | Basis |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| `gptoss120b` | H200 | short_chat | 10 | 990 | 0 | 1,459,609 | 39.46 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | short_chat | 30 | 691 | 0 | 1,459,609 | 39.46 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | short_chat | 50 | 334 | 0 | 1,037,487 | 56.09 | 32 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | short_chat | 70 | 202 | 0 | 728,459 | 78.76 | 16 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | short_chat | 100 | 73 | 0 | 505,857 | 109.39 | 8 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | long_chat | 10 | 1149 | 0 | 1,451,169 | 39.23 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | long_chat | 30 | 619 | 0 | 1,451,169 | 39.23 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | long_chat | 50 | 346 | 0 | 1,035,150 | 55.96 | 32 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | long_chat | 70 | 184 | 0 | 649,279 | 70.20 | 16 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | long_chat | 100 | 62 | 0 | 329,414 | 142.47 | 4 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | agentic_derived | 10 | 62 | 0 | 35,806 | 15.49 | 4 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | H200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | H200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | H200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | H200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | B200 | short_chat | 10 | 1102 | 0 | 4,516,967 | 76.58 | 128 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | short_chat | 30 | 1063 | 0 | 4,516,967 | 76.58 | 128 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | short_chat | 50 | 848 | 0 | 4,516,967 | 76.58 | 128 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | short_chat | 70 | 597 | 0 | 4,516,967 | 76.58 | 128 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | short_chat | 100 | 358 | 0 | 2,983,848 | 101.17 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | long_chat | 10 | 1056 | 0 | 2,629,943 | 44.59 | 128 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | long_chat | 30 | 944 | 0 | 2,629,943 | 44.59 | 128 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | long_chat | 50 | 679 | 0 | 1,978,039 | 67.07 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | long_chat | 70 | 430 | 0 | 1,699,929 | 115.28 | 32 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | long_chat | 100 | 291 | 0 | 1,699,929 | 115.28 | 32 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | agentic_derived | 10 | 305 | 0 | 184,775 | 12.53 | 32 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `gptoss120b` | B200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | B200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | B200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | B200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | short_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | long_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `gptoss120b` | GB200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | H200 | short_chat | 10 | 990 | 0 | 1,459,609 | 39.46 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | short_chat | 30 | 691 | 0 | 1,459,609 | 39.46 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | short_chat | 50 | 334 | 0 | 1,037,487 | 56.09 | 32 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | short_chat | 70 | 202 | 0 | 728,459 | 78.76 | 16 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | short_chat | 100 | 73 | 0 | 505,857 | 109.39 | 8 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | long_chat | 10 | 1149 | 0 | 1,451,169 | 39.23 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | long_chat | 30 | 619 | 0 | 1,451,169 | 39.23 | 64 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | long_chat | 50 | 346 | 0 | 1,035,150 | 55.96 | 32 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | long_chat | 70 | 184 | 0 | 649,279 | 70.20 | 16 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | long_chat | 100 | 62 | 0 | 329,414 | 142.47 | 4 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | agentic_derived | 10 | 62 | 0 | 35,806 | 15.49 | 4 | vllm | fp4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | H200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | H200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | H200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | H200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | short_chat | 10 | 8 | 0 | 40,586 | 11.01 | 8 | vllm | int4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | B200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | long_chat | 10 | 5 | 0 | 22,902 | 12.42 | 4 | vllm | int4 | selected_public_max | public max among eligible rows |
| `frontier_composite` | B200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | B200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | short_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | long_chat | 10 | 2 | 2 | 7,963 | 16.72 | 1 | dynamo-vllm | fp4 | selected_optimized_stack | Dynamo/TRT-LLM/MTP eligible max |
| `frontier_composite` | GB200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `frontier_composite` | GB200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | short_chat | 10 | 222 | 0 | 965,061 | 26.09 | 64 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | H200 | short_chat | 30 | 71 | 0 | 364,069 | 39.36 | 16 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | H200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | long_chat | 10 | 147 | 0 | 231,275 | 12.50 | 32 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | H200 | long_chat | 30 | 12 | 0 | 83,442 | 36.09 | 4 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | H200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | H200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | short_chat | 10 | 255 | 0 | 1,228,515 | 41.65 | 64 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | B200 | short_chat | 30 | 144 | 0 | 1,228,515 | 41.65 | 64 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | B200 | short_chat | 50 | 40 | 0 | 412,192 | 55.90 | 16 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | B200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | long_chat | 10 | 169 | 0 | 384,593 | 13.04 | 64 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | B200 | long_chat | 30 | 49 | 0 | 247,359 | 33.55 | 16 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | B200 | long_chat | 50 | 7 | 0 | 95,773 | 51.96 | 4 | vllm | fp8 | selected_public_max | public max among eligible rows |
| `llama70b` | B200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | B200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | short_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | long_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `llama70b` | GB200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | short_chat | 10 | 40 | 0 | 47,614 | 10.30 | 8 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `dsr1` | H200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | long_chat | 10 | 4 | 0 | 27,722 | 11.99 | 4 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `dsr1` | H200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | H200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | short_chat | 10 | 138 | 0 | 87,925 | 11.92 | 16 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `dsr1` | B200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | long_chat | 10 | 63 | 0 | 79,568 | 10.79 | 16 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `dsr1` | B200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | B200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | short_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | long_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `dsr1` | GB200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | short_chat | 10 | 18 | 0 | 67,884 | 14.68 | 8 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `qwen3.5` | H200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | long_chat | 10 | 16 | 0 | 53,892 | 11.65 | 8 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `qwen3.5` | H200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | H200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | short_chat | 10 | 45 | 0 | 806,272 | 13.67 | 128 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `qwen3.5` | B200 | short_chat | 30 | 7 | 0 | 229,498 | 31.13 | 16 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `qwen3.5` | B200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | long_chat | 10 | 38 | 0 | 345,338 | 11.71 | 64 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `qwen3.5` | B200 | long_chat | 30 | 7 | 0 | 132,868 | 36.04 | 8 | sglang | fp8 | selected_public_max | public max among eligible rows |
| `qwen3.5` | B200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | B200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | short_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | short_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | short_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | short_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | short_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | long_chat | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | long_chat | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | long_chat | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | long_chat | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | long_chat | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | agentic_derived | 10 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | agentic_derived | 30 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | agentic_derived | 50 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | agentic_derived | 70 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |
| `qwen3.5` | GB200 | agentic_derived | 100 | 0 | 0 |  |  |  |  |  | missing | no row meets target_tok_s_user |

## 해석 메모

- `selected_optimized_stack`은 Dynamo/TRT-LLM/MTP 계열 row가 target을 만족했고, 그 안에서 최고 TPS/MW를 골랐다는 뜻이다.
- `selected_public_max`는 target을 만족하는 optimized stack row가 없어 전체 public row 중 최고 TPS/MW를 골랐다는 뜻이다.
- `missing`은 해당 proxy/GPU/workload에서 target tok/s/user를 만족하는 row가 없다는 뜻이다.
- 이 summary는 엑셀 적용 후보 테이블이며, headline forecast의 workload mix를 자동으로 바꾸지는 않는다.
