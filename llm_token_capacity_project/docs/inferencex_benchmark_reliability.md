# InferenceX Benchmark Reliability Note

작성일: 2026-07-20

이 문서는 `llm_token_capacity_project`에서 InferenceX를 왜 전력 기반 token 생성량 모델의 benchmark/proxy layer로 채택하는지 설명한다. 결론부터 말하면 InferenceX는 특정 업체의 production telemetry는 아니지만, LLM serving 성능을 좌우하는 조건을 실제 benchmark 축으로 노출한다는 점에서 단순 GPU spec sheet나 단일 peak throughput보다 훨씬 믿을 만한 reference다.

## Executive Takeaway

InferenceX가 유용한 이유는 세 가지다.

첫째, 단일 숫자 benchmark가 아니라 throughput과 interactivity/latency의 Pareto curve를 본다. 상용 LLM serving에서는 "가장 높은 tok/s"만으로는 의미가 부족하다. 사용자 1명에게 얼마나 빨리 token이 도착하는지, 즉 `tok/s/user`, `TTFT`, `TPOT`이 함께 중요하다. InferenceX v2 article은 inference에는 one-size-fits-all이 없고, throughput은 interactivity level별 curve로 읽어야 한다고 설명한다. 특히 real-time speech와 basic QA chatbot은 허용 latency가 다르므로 같은 hardware라도 최적점이 다르다. Source: [InferenceX v2 article](https://inferencex.semianalysis.com/blog/inferencex-v2-nvidia-blackwell-vs-amd-vs-hopper).

둘째, InferenceX는 `ISL`, `OSL`, concurrency, framework, precision, GPU generation을 분리한다. 이 프로젝트의 normalized DB에는 `benchmark_results` 76,406개 row가 있고, `b200`, `h200`, `gb200` 등 9개 GPU, 9개 model, 9개 framework가 들어 있다. 같은 B200이라도 `ISL=1024/OSL=1024`와 `ISL=8192/OSL=1024`의 output TPS/MW가 다르므로, short chat과 long context를 하나의 coefficient로 묶으면 모델이 틀어진다.

셋째, agentic workload를 별도 shape로 다룰 근거가 생겼다. SemiAnalysis의 Hugging Face dataset `cc-traces-weka-062126-256k`는 Claude Code proxy traces에서 온 agentic/multi-turn/KV-cache workload dataset이다. Anthropic이 공개한 production telemetry는 아니므로 "Claude Code 계열 proxy trace"로 표기한다. 이 프로젝트 DB의 `agentic_trace_profile` 기준 256k-capped profile은 393 traces, 68,266 model requests, 평균 input 100,947 tokens/request, 평균 output 860 tokens/request다. 이는 agentic workload가 일반 chat보다 훨씬 prefill/context-heavy하다는 강한 수치 근거다. Source: [HF 256k dataset](https://huggingface.co/datasets/semianalysisai/cc-traces-weka-062126-256k), [uncapped dataset](https://huggingface.co/datasets/semianalysisai/cc-traces-weka-062126).

## What Makes InferenceX Different

| Reliability dimension | Why it matters | Evidence |
|---|---|---|
| Continuous benchmark | LLM serving software changes weekly; static benchmark goes stale quickly. | InferenceX positions itself as open-source continuous inference benchmark and tracks software improvements over time. |
| Curve, not point estimate | Production buyers care about throughput at a target latency/interactivity, not only peak throughput. | InferenceX v2 explains throughput vs interactivity tradeoff and publishes curves by interactivity. |
| Workload shape explicit | `ISL` drives prefill; `OSL` drives decode. | Local normalized benchmark rows include `isl`, `osl`, `p99_ttft_ms`, `p99_tpot_ms`, `output_tok_s_mw`. |
| Stack-aware | vLLM, SGLang, TensorRT-LLM, Dynamo, precision, runtime all materially change output. | InferenceX app/repo tracks framework, precision, runtime, and canonical config. |
| Power normalized | `output_tok_s_mw` can connect serving performance to power-based token capacity models. | Local SQLite exposes `output_tok_s_mw`, `input_tok_s_mw`, `total_tok_s_mw`, joules/token fields. |
| Agentic traces | Agent workloads have long context, multi-turn, fan-out, and KV-cache pressure. | HF Claude Code proxy trace dataset includes subagent groups and per-request token stats. |

## Local Evidence From The Project DB

Current local normalized snapshot:

| Metric | Value |
|---|---:|
| `benchmark_results` rows | 76,406 |
| GPU SKUs | 9 |
| Models | 9 |
| Frameworks | 9 |
| Agentic trace profiles | 2 |

H200/B200/GB200 output TPS/MW differs materially by ISL/OSL:

| GPU | ISL | OSL | Rows | Avg output tok/s/MW |
|---|---:|---:|---:|---:|
| B200 | 1,024 | 1,024 | 8,668 | 542,405 |
| B200 | 8,192 | 1,024 | 8,074 | 373,653 |
| B200 | 1,024 | 8,192 | 7,025 | 595,145 |
| H200 | 1,024 | 1,024 | 4,800 | 366,491 |
| H200 | 8,192 | 1,024 | 5,035 | 265,995 |
| GB200 | 1,024 | 1,024 | 2,320 | 1,024,231 |
| GB200 | 8,192 | 1,024 | 1,984 | 418,432 |

Agentic trace profile:

| Dataset | Requests | Avg input/request | Avg output/request | Input/output ratio |
|---|---:|---:|---:|---:|
| `semianalysisai/cc-traces-weka-062126-256k` | 68,266 | 100,947 | 860 | 117 |
| `semianalysisai/cc-traces-weka-062126` | 98,827 | 218,922 | 1,077 | 203 |

Interpretation: agentic traces are not a throughput benchmark by themselves. They are workload-shape evidence. They say "what kind of request mix should be benchmarked or haircutted", not "how many tokens/sec/MW production Claude Code achieves".

## Why Interactivity Changes Which GPU/Recipe Looks Best

LLM serving has a throughput-latency tradeoff. Higher concurrency and larger batches improve total throughput because fixed model-weight load and GPU-hour cost are amortized across more users. But each user gets tokens more slowly. Low-latency products need high interactivity, so the optimal recipe may sacrifice peak throughput to reduce `TPOT` and tail latency.

This is why different GPUs or recipes can win at different interactivity levels:

- High interactivity: smaller batches, tighter TPOT, more sensitivity to per-token latency, kernel overhead, network overhead, and scale-up fabric.
- Low interactivity / batch serving: larger batches, better utilization, higher total tok/s, and more room to amortize memory movement.
- Long input / RAG / agentic: prefill becomes a bigger bottleneck, so compute-heavy prompt processing matters more.
- Long output / high concurrency: decode becomes a bigger bottleneck, so memory bandwidth, KV cache capacity, and decode worker scaling matter more.

InferenceX is more useful than a single peak number because it exposes this curve. The PyTorch/SGLang DeepSeek-V4 post explicitly frames improvements as throughput at the same interactivity, and reports that June 2026 curves sustained much higher throughput in the 40-80 tok/s/user region that deployments target. Source: [PyTorch SGLang DeepSeek-V4 post](https://pytorch.org/blog/serving-deepseek-v4-on-gb300-with-sglang-5x-higher-throughput-at-the-same-interactivity-since-day-0/).

## Why Prefill And Decode Need Different GPU Counts

Prefill and decode are different computational phases.

- Prefill processes the input prompt and creates the initial KV cache. It scales with input length, prompt reuse, and context size.
- Decode generates output tokens using the KV cache. It scales with concurrency, output length, active KV memory, and memory bandwidth.

NVIDIA Dynamo's disaggregated serving guide makes this separation explicit: prefill and decode can be split into independently scalable worker pools, and disaggregation is useful when long prompts make prefill expensive, long generations or high concurrency make decode the bottleneck, or large models need different parallelism for prompt processing and generation. Source: [NVIDIA Dynamo disaggregated serving](https://docs.nvidia.com/dynamo/dev/user-guides/disaggregated-serving).

Academic systems literature says the same thing. DistServe argues that colocating prefill and decode creates interference and couples resource allocation. Its analysis says decode is bandwidth-bound, batching is important for goodput, and disaggregation enables multiple prefill instances to feed a decode instance without sacrificing TPOT. Source: [DistServe paper page](https://www.alphaxiv.org/abs/2401.09670).

The practical implication:

```text
short chat:
  modest prefill, modest decode
  -> balanced/aggregated recipes can be adequate

long conversation / RAG:
  heavy prefill, moderate decode
  -> more prefill capacity can be optimal

agentic coding:
  very heavy context, multi-turn, subagent fan-out, cache reuse
  -> prefill, KV transfer, routing, and decode concurrency all matter

long generation:
  moderate prefill, heavy decode
  -> more decode workers / memory bandwidth can be optimal
```

InferenceX is credible here because its app pipeline explicitly handles disaggregated serving metadata. The app docs preserve prefill/decode worker roles through orchestrator adapters and document schema fields such as `prefill_tp`, `decode_tp`, `num_prefill_gpu`, and `num_decode_gpu` for v2 artifacts. That means the benchmark design is aware of the exact resource split that modern production serving systems tune.

## Why Framework-Level Optimization Matters

The benchmark is not only "which GPU is faster". It measures the full stack:

- vLLM: PagedAttention, continuous batching, CUDA/HIP graphs, optimized kernels, distributed inference support. Source: [vLLM docs](https://docs.vllm.ai/en/v0.5.0.post1/).
- ORCA: iteration-level scheduling for autoregressive generation; the paper reports much higher throughput at the same latency versus FasterTransformer for GPT-3 175B. Source: [USENIX OSDI ORCA](https://www.usenix.org/conference/osdi22/presentation/yu).
- Dynamo/SGLang/TensorRT-LLM: disaggregated serving, KV transfer, routing, backend-specific kernels, MoE/EP/TP/DP recipe choices.

This matters because serving performance is often software-limited, not only hardware-limited. InferenceX's own article highlights continuous improvements across framework versions and recipes, and the PyTorch/SGLang post shows public InferenceX curves moving significantly after kernel/runtime/recipe fixes. That is exactly the behavior we want from a benchmark used in a forward-looking token capacity model: it captures the moving software frontier instead of freezing a stale hardware-only estimate.

## How This Project Should Use InferenceX

Use InferenceX as:

1. `output_tok_s_mw` benchmark reference for generated-output capacity.
2. ISL/OSL-specific evidence for short vs long workload classes.
3. GPU generation comparison layer for H200/B200/GB200 and future GB300/B300.
4. Framework/precision sensitivity layer, not as company production telemetry.
5. Agentic trace shape evidence when no matched 100k-input throughput row exists.

Do not use InferenceX as:

1. Direct OpenAI/Anthropic/Google/Meta production throughput.
2. A single universal TPS/MW number.
3. Evidence that custom accelerators deserve an automatic uplift without matched output-token/MW data.
4. A replacement for provider-disclosed utilization, SLO, traffic mix, cache-hit rate, or deployed fleet share.

## Recommended Model Rule

For token capacity forecasting:

```text
short_chat_tps_mw:
  InferenceX output_tok_s_mw at ISL=1024, OSL=1024

long_chat_tps_mw:
  InferenceX output_tok_s_mw at ISL=8192, OSL=1024 where enough rows exist
  otherwise short_chat_tps_mw with documented long-context haircut

gpu_agentic_tps_mw:
  gpu_long_chat_tps_mw with additional context/tooling haircut
  calibrated by Claude Code proxy trace request shape

gpu_workload_avg_tps_mw:
  short_share * gpu_short_chat_tps_mw
  + long_share * gpu_long_chat_tps_mw
  + agentic_share * gpu_agentic_tps_mw

serving_tps_mw:
  sum(gpu_share * gpu_workload_avg_tps_mw)
  * commercial_workload_fit_factor
```

This rule is intentionally conservative. It lets InferenceX carry what it is good at: transparent benchmark frontier by model/GPU/framework/ISL/OSL/interactivity. It lets the forecast model carry what InferenceX does not directly disclose: company-specific traffic mix, closed-model routing, production SLO, cache hit rate, and actual deployed fleet share.

## Reproducibility Queries

The local numbers above can be reproduced from `data/inferencex/inferencex_benchmark.sqlite`:

```bash
python3 llm_token_capacity_project/tools/query_inferencex_benchmark_db.py sql \
  "SELECT benchmark_type, COUNT(*) AS rows, COUNT(DISTINCT gpu) AS gpus, COUNT(DISTINCT model) AS models, COUNT(DISTINCT framework) AS frameworks FROM benchmark_results GROUP BY benchmark_type ORDER BY rows DESC"

python3 llm_token_capacity_project/tools/query_inferencex_benchmark_db.py sql \
  "SELECT gpu, isl, osl, COUNT(*) AS rows, ROUND(AVG(output_tok_s_mw),0) AS avg_out FROM benchmark_results WHERE gpu IN ('h200','b200','gb200') GROUP BY gpu, isl, osl ORDER BY rows DESC"

python3 llm_token_capacity_project/tools/query_inferencex_benchmark_db.py sql \
  "SELECT dataset_id, total_model_requests, ROUND(avg_input_tokens_per_request,0) AS avg_input, ROUND(avg_output_tokens_per_request,0) AS avg_output, ROUND(input_output_token_ratio,2) AS io_ratio FROM agentic_trace_profile ORDER BY total_model_requests"
```

## Source Map

| Source | What it supports |
|---|---|
| [InferenceX GitHub repo](https://github.com/SemiAnalysisAI/InferenceX) | Open-source continuous inference benchmark scope, supported hardware/framework orientation. |
| [InferenceX app repo](https://github.com/SemiAnalysisAI/InferenceX-app) | Dashboard, DB-backed ETL, chart and metric pipeline. |
| [InferenceX v2 article](https://inferencex.semianalysis.com/blog/inferencex-v2-nvidia-blackwell-vs-amd-vs-hopper) | Interactivity curve, prefill/decode explanation, disaggregated serving, framework comparisons. |
| [HF Claude Code proxy traces 256k](https://huggingface.co/datasets/semianalysisai/cc-traces-weka-062126-256k) | Agentic workload shape: multi-turn, subagents, 256k cap, request/token stats. |
| [HF Claude Code proxy traces uncapped](https://huggingface.co/datasets/semianalysisai/cc-traces-weka-062126) | Heavier context tail reference. |
| [NVIDIA Dynamo disaggregated serving](https://docs.nvidia.com/dynamo/dev/user-guides/disaggregated-serving) | Why prefill/decode are separately scalable worker pools. |
| [DistServe](https://www.alphaxiv.org/abs/2401.09670) | Academic support for prefill/decode interference and goodput-optimized disaggregation. |
| [vLLM docs](https://docs.vllm.ai/en/v0.5.0.post1/) | PagedAttention, continuous batching, optimized serving stack. |
| [ORCA OSDI 2022](https://www.usenix.org/conference/osdi22/presentation/yu) | Iteration-level scheduling for autoregressive generation. |
| [PyTorch/SGLang DeepSeek-V4 post](https://pytorch.org/blog/serving-deepseek-v4-on-gb300-with-sglang-5x-higher-throughput-at-the-same-interactivity-since-day-0/) | Same-interactivity public curve improvement and recipe optimization evidence. |
