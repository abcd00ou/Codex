# LLMServingSim 2.0로 InferenceX 벤치마크를 고도화하는 구조

작성일: 2026-06-05  
목적: InferenceX의 조건부 benchmark grid를 production-like serving capacity로 보정하기 위해 LLMServingSim 2.0에서 어떤 구조와 데이터를 수집해야 하는지 정리한다.

## 1. 핵심 결론

InferenceX와 LLMServingSim 2.0은 경쟁 관계가 아니라 계층 관계로 쓰는 것이 좋다.

```text
InferenceX
-> hardware/model/quantization/ISL/OSL/batch 조건별 benchmark anchor

LLMServingSim 2.0
-> request arrival, scheduler, KV cache, memory tier, parallelism, SLO, network를 반영한 serving realism layer

프로젝트 모델
-> production-like tokens/sec/MW, company workload fit factor, HBM/CXL/PIM sensitivity
```

InferenceX가 이미 `GPU`, `model`, `quantization`, `ISL`, `OSL`, `batch/concurrency`, `output_tok_s_mw`를 갖고 있다면, LLMServingSim은 그 조건들을 대체하지 않는다. 대신 그 조건들이 실제 서비스처럼 섞일 때 생기는 system loss와 mitigation upside를 계산하는 보정층이다.

## 2. LLMServingSim 2.0 구조

공식 문서 기준 LLMServingSim은 크게 두 부분으로 나뉜다.

| 계층 | 역할 | 프로젝트에서 의미 |
|---|---|---|
| Python serving frontend | request scheduling, batching, trace generation, prefix caching, memory accounting | production serving behavior를 만든다 |
| ASTRA-Sim C++ backend | compute 및 collective communication cycle simulation | GPU 간 통신, topology, parallelism cost를 반영한다 |

흐름은 다음과 같다.

```text
workload JSONL
-> router
-> per-instance scheduler
-> batch 생성
-> per-layer trace 생성
-> Chakra graph 변환
-> ASTRA-Sim 실행
-> request별 TTFT/TPOT/latency/throughput output
```

LLMServingSim 2.0의 중요한 점은 vLLM-style continuous batching을 모사하고, profiler로 얻은 hardware/model별 layer latency를 simulation input으로 사용한다는 것이다. 즉 단순 수식 simulator가 아니라 실제 vLLM profile 기반의 serving simulator에 가깝다.

## 3. LLMServingSim에서 수집해야 할 데이터

### A. Hardware/profile data

InferenceX benchmark와 연결하려면 먼저 같은 hardware/model/quantization 조건의 profile data가 필요하다.

| 데이터 | 설명 | InferenceX와 연결 |
|---|---|---|
| `hardware` | H100, H200, B200, GB200, RTXPRO6000 등 | InferenceX hardware key와 매핑 |
| `model` | Llama, Qwen, Mixtral/MoE 등 | InferenceX model key와 매핑 |
| `variant` | bf16, fp8, kvfp8 등 | quantization 또는 KV cache precision과 매핑 |
| `tp<N>` | tensor parallel degree별 profile | multi-GPU scaling 보정 |
| `dense.csv` | token count -> dense layer latency | prefill/FFN/GEMM 계열 비용 |
| `attention.csv` | prompt/decode/KV shape별 attention latency | KV cache 및 context length 보정 |
| `moe.csv` | MoE token/expert latency | expert routing overhead |
| `skew_fit.csv` | heterogeneous decode correction | mixed sequence length batch 보정 |
| `meta.yaml` | engine flags, sweep spec, profile summary | benchmark reproducibility |

가장 중요한 파일은 `attention.csv`다. InferenceX의 ISL/OSL benchmark를 long-context production workload로 바꿀 때 KV cache와 attention latency가 핵심 보정값이 된다.

### B. Workload trace data

LLMServingSim은 workload를 JSONL로 받는다. 이 데이터가 InferenceX와 LLMServingSim의 가장 큰 차이를 만든다.

Flat request format:

```json
{"input_toks": 1472, "output_toks": 133, "arrival_time_ns": 4059740}
```

Agentic session format:

```json
{
  "session_id": "session_0",
  "arrival_time_ns": 4059740,
  "sub_requests": [
    {"input_toks": 1472, "output_toks": 133, "tool_duration_ns": 127348767},
    {"input_toks": 1582, "output_toks": 125, "tool_duration_ns": 197295027},
    {"input_toks": 1734, "output_toks": 77, "tool_duration_ns": 0}
  ]
}
```

수집해야 할 workload fields:

| 필드 | 의미 | 프로젝트에서 쓰임 |
|---|---|---|
| `input_toks` | prompt/input token 수 | InferenceX ISL distribution으로 연결 |
| `output_toks` | generated token 수 | InferenceX OSL distribution으로 연결 |
| `arrival_time_ns` | request arrival pattern | queueing/SLO pressure 계산 |
| `input_tok_ids` | prefix cache matching용 token IDs | prefix caching 효과 |
| `session_id` | agentic session 식별자 | tool-use/coding/RAG workload |
| `sub_requests` | 하나의 session 내 여러 LLM call | agentic workload realism |
| `tool_duration_ns` | tool call 또는 user think time | request dependency와 idle gap |

InferenceX가 고정된 ISL/OSL point라면, LLMServingSim workload는 ISL/OSL distribution과 request arrival process다. 이 차이가 중요하다.

### C. Cluster/config data

Benchmark 고도화에는 hardware 하나의 성능뿐 아니라 serving cluster 구조가 필요하다.

| 데이터 | 설명 | 왜 필요한가 |
|---|---|---|
| `num_nodes` | node 수 | cluster scale |
| instance layout | prefill/decode instance 구성 | disaggregated serving |
| NPU/GPU mapping | accelerator가 instance에 어떻게 배정되는지 | resource utilization |
| topology | network shape, bandwidth, latency | TP/PP/EP communication overhead |
| memory expansion | CPU/CXL/PIM tier 구성 | HBM spill, KV offload |
| power block | NPU/CPU/DRAM/link/base power | tokens/sec/MW 계산 |
| parallelism strategy | TP, PP, EP, DP, DP+EP | MoE/large model serving cost |
| feature flags | prefix caching, attention offloading 등 | optimization scenario |

InferenceX의 benchmark는 대개 fixed setup의 결과다. LLMServingSim은 이 fixed setup을 production cluster setting으로 확장한다.

### D. Output data

LLMServingSim output은 benchmark 고도화의 핵심 산출물이다.

Per-request CSV 주요 columns:

| column | 의미 | 프로젝트 적용 |
|---|---|---|
| `instance id` | 어떤 serving instance가 처리했는지 | load balancing |
| `model` | model name | benchmark mapping |
| `input` | prompt tokens | ISL validation |
| `output` | generated tokens | OSL validation |
| `arrival` | request arrival time | queueing |
| `end_time` | completion time | total duration |
| `latency` | end-to-end latency | SLO pass/fail |
| `queuing_delay` | queue wait | saturation signal |
| `TTFT` | time to first token | user-facing latency |
| `TPOT` | time per output token | decode performance |
| `ITL` | inter-token latency list | tail decode behavior |

Throughput log에서 봐야 할 fields:

| field | 의미 |
|---|---|
| `prompt_t` | prompt/input token throughput |
| `decode_t` | generated/output token throughput |
| `npu_mem` | accelerator memory footprint |
| `prefix_hit` | prefix cache hit rate |
| `alltoall` | MoE/EP communication size |
| `pim_busy` | PIM utilization/bottleneck |
| `cxl_mem` | CXL memory usage |
| `power` | system power |

최종 power summary가 있으면 component별 energy를 볼 수 있다.

## 4. InferenceX 필드와 LLMServingSim 필드 매핑

| InferenceX field | LLMServingSim field | 해석 |
|---|---|---|
| hardware | profile hardware, cluster accelerator | 동일 hardware 기준 profile 필요 |
| model | profile model, output model | tokenizer/model architecture 일치 필요 |
| quantization | variant, profile CSV, KV precision | bf16/fp8/kvfp8 등으로 매핑 |
| ISL | `input_toks` distribution | 단일 point에서 distribution으로 확장 |
| OSL | `output_toks` distribution | generated token length distribution |
| batch/concurrency | scheduler batch, arrival rate | fixed batch에서 dynamic batching으로 전환 |
| output tok/s | `decode_t`, output token throughput | production-like generated token throughput |
| tok/s/MW | output throughput / power | power block 필요 |
| latency if present | TTFT, TPOT, latency | SLO 기준으로 재해석 |

## 5. 고도화용 실험 설계 예시

### Experiment 1. ISL/OSL grid를 production workload로 변환

InferenceX에서 다음 grid를 가져온다.

```text
hardware x model x quantization x ISL x OSL x batch -> output_tok_s_mw
```

LLMServingSim에서는 같은 ISL/OSL point를 flat workload distribution으로 바꾼다.

```text
short chat: ISL 1K, OSL 256
RAG: ISL 8K-32K, OSL 512-2K
coding agent: ISL 16K-64K, OSL 1K-4K
long-context agent: ISL 64K-128K, OSL 2K-8K
```

산출물:

```text
benchmark_output_tok_s_mw
serving_decode_tps
TTFT_p50/p95/p99
TPOT_p50/p95/p99
SLO_pass_rate
realization_factor = serving_decode_tps / benchmark_output_tps
```

### Experiment 2. KV cache/HBM sensitivity

고정 hardware/model/quantization에서 context length를 늘리며 본다.

```text
4K -> 16K -> 32K -> 64K -> 128K
```

비교 scenario:

```text
HBM only
HBM + FP8 KV cache
HBM + CXL spill
HBM + PIM attention offload
```

해석:

```text
GB200 benchmark uplift가 long-context에서도 유지되는가?
HBM capacity가 부족해 CXL로 넘어갈 때 TPOT가 얼마나 나빠지는가?
KV cache quantization은 throughput을 얼마나 회복하는가?
```

### Experiment 3. Company workload fit factor

회사별 workload mix를 설정한다.

| workload class | proxy |
|---|---|
| consumer short chat | short flat ShareGPT |
| enterprise RAG | medium/long ISL flat workload |
| coding agent | agentic session with tool durations |
| long-context reasoning | long ISL + long OSL |
| multimodal proxy | large prefill-equivalent input cost |

회사별 factor:

```text
company_serving_factor =
  sum(workload_share_i * realization_factor_i)
```

이 값을 기존 `commercial_workload_fit_factor`의 근거로 쓸 수 있다.

## 6. 수집 테이블 초안

### `llmservingsim_profile_catalog.csv`

| column | example |
|---|---|
| source_id | llmservingsim_profile_h200_llama70b_fp8 |
| hardware | H200 |
| model | Llama-70B |
| variant | fp8 |
| tp_degree | 1/2/4/8 |
| has_dense_csv | true |
| has_attention_csv | true |
| has_moe_csv | false |
| profile_source_path | profiler/perf/... |
| notes | tokenizer/model version |

### `llmservingsim_workload_scenarios.csv`

| column | example |
|---|---|
| scenario_id | enterprise_rag_32k |
| workload_class | RAG |
| input_toks_p50 | 8192 |
| input_toks_p95 | 32768 |
| output_toks_p50 | 768 |
| output_toks_p95 | 2048 |
| arrival_rate_rps | 10 |
| agentic | false |
| prefix_cache_expected | medium |
| source_basis | ShareGPT / synthetic / internal assumption |

### `llmservingsim_results.csv`

| column | example |
|---|---|
| run_id | h200_llama70b_fp8_rag32k_hbm |
| hardware | H200 |
| model | Llama-70B |
| variant | fp8 |
| workload_scenario | enterprise_rag_32k |
| memory_scenario | hbm_only |
| parallelism | tp4 |
| decode_tps | 12345 |
| prompt_tps | 67890 |
| ttft_p50_ms | 450 |
| ttft_p95_ms | 1200 |
| tpot_p50_ms | 25 |
| tpot_p95_ms | 80 |
| output_toks_per_mw | 123456 |
| benchmark_ref_id | inferencex_h200_llama70b_fp8_isl8192_osl1024 |
| realization_factor | 0.52 |

## 7. 프로젝트 계산식 연결

기존:

```text
fleet_reference_tps_per_mw =
  sum(gpu_generation_share * InferenceX_reference_tps_per_mw)

serving_tps_per_mw =
  fleet_reference_tps_per_mw * commercial_workload_fit_factor
```

고도화 후:

```text
benchmark_surface =
  InferenceX(hardware, model, quantization, ISL, OSL, batch)

serving_realization_factor =
  LLMServingSim(workload_trace, scheduler, memory_tier, parallelism, SLO)
  / matched_InferenceX_benchmark

production_like_tps_per_mw =
  benchmark_surface * serving_realization_factor
```

핵심은 `commercial_workload_fit_factor`를 감으로 넣지 않고, workload class별 LLMServingSim result로 근거화하는 것이다.

## 8. 우선 수집 순서

1. InferenceX에서 현재 쓰는 benchmark rows를 뽑는다.
   - hardware, model, quantization, ISL, OSL, batch, output_tok_s_mw.
2. LLMServingSim에서 같은 model/hardware/variant profile이 있는지 확인한다.
3. 없으면 profile data 수집 계획을 만든다.
4. workload scenario 4개를 만든다.
   - short chat, enterprise RAG, coding agent, long-context agent.
5. 각 scenario에 대해 HBM-only baseline을 돌린다.
6. KV FP8, CXL, PIM offload scenario를 추가한다.
7. realization factor를 계산한다.
8. 회사별 workload mix로 weighted factor를 만든다.

## 9. 해석할 때 조심할 점

- LLMServingSim 결과도 production telemetry는 아니다. Simulator-calibrated estimate로 분류해야 한다.
- InferenceX와 LLMServingSim의 tokenizer/model version이 다르면 ISL/OSL mapping이 흔들린다.
- Power block이 없으면 tokens/sec/MW가 아니라 tokens/sec까지만 비교해야 한다.
- CXL/PIM scenario는 hardware availability와 software maturity를 별도 confidence로 둬야 한다.
- Agentic workload는 tool duration, retry, sub-request dependency에 민감하다.

## 10. 참고 source

- LLMServingSim overview: https://llmservingsim.ai/docs/getting-started/overview
- LLMServingSim GitHub: https://github.com/casys-kaist/LLMServingSim
- Architecture overview: https://llmservingsim.ai/docs/simulator/architecture
- Profiler overview: https://llmservingsim.ai/docs/profiler/overview
- Workload JSONL format: https://llmservingsim.ai/docs/workloads/jsonl-format
- Reading the output: https://llmservingsim.ai/docs/simulator/reading-output
