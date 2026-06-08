# LLMServingSim Bridge from InferenceX

This report prepares InferenceX benchmark rows for LLMServingSim-style serving realism analysis.

## Why this exists

InferenceX already captures hardware, model, precision, ISL, OSL, concurrency, throughput, latency, and power-derived metrics. LLMServingSim adds the dynamic serving layer: request arrivals, batching, routing, KV cache residency, memory tiering, parallelism, and SLO behavior.

## Output files

- `llmservingsim_bridge_surface.csv`: grouped benchmark surface.
- `llmservingsim_bridge_report.md`: this summary.

## Columns to feed into future LLMServingSim scenarios

| Column | Use |
|---|---|
| `model`, `gpu`, `framework`, `precision` | Match a profiler/hardware configuration. |
| `isl`, `osl`, `concurrency` | Convert benchmark points into workload JSONL distributions. |
| `output_p50_tok_s_mw` | Public benchmark anchor for generated-token capacity. |
| `median_tpot_ms`, `median_ttft_ms` | Initial SLO sanity check when available. |
| `kv_pressure_proxy_isl_x_concurrency` | First-order proxy for KV cache pressure. |
| `realization_vs_same_config_1024_1024` | Sequence-length sensitivity before full simulation. |

## Largest long-context drops vs same-config 1024/1024 baseline

| Model | GPU | Framework | Precision | GPU count | Concurrency | ISL | OSL | Rows | Output p50 tok/s/MW | Realization |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| llama70b | h200 | trt | fp8 | 1 | 128 | 8192 | 1024 | 10 | 327,544 | 0.21 |
| llama70b | h200 | vllm | fp8 | 1 | 64 | 8192 | 1024 | 10 | 240,971 | 0.26 |
| llama70b | b200 | trt | fp8 | 1 | 128 | 8192 | 1024 | 11 | 481,830 | 0.26 |
| llama70b | h200 | trt | fp8 | 2 | 128 | 8192 | 1024 | 11 | 324,109 | 0.26 |
| llama70b | h200 | trt | fp8 | 4 | 128 | 8192 | 1024 | 10 | 263,894 | 0.29 |
| llama70b | b200 | trt | fp4 | 2 | 128 | 8192 | 1024 | 10 | 551,108 | 0.30 |
| llama70b | b200 | vllm | fp8 | 1 | 64 | 8192 | 1024 | 10 | 374,050 | 0.31 |
| llama70b | h200 | trt | fp8 | 1 | 64 | 8192 | 1024 | 10 | 327,311 | 0.31 |
| llama70b | h200 | vllm | fp8 | 2 | 64 | 8192 | 1024 | 11 | 243,593 | 0.32 |
| dsr1 | gb200 | dynamo-sglang | fp8 | 72 | 4096 | 8192 | 1024 | 36 | 328,894 | 0.32 |
| llama70b | b200 | trt | fp8 | 4 | 128 | 8192 | 1024 | 10 | 337,957 | 0.32 |
| llama70b | h200 | trt | fp8 | 2 | 64 | 8192 | 1024 | 10 | 294,844 | 0.33 |
| llama70b | h200 | vllm | fp8 | 4 | 64 | 8192 | 1024 | 11 | 190,271 | 0.35 |
| llama70b | b200 | vllm | fp4 | 1 | 64 | 8192 | 1024 | 10 | 554,932 | 0.35 |
| llama70b | b200 | trt | fp8 | 1 | 64 | 8192 | 1024 | 11 | 471,057 | 0.37 |
| llama70b | b200 | vllm | fp8 | 2 | 64 | 8192 | 1024 | 10 | 330,518 | 0.37 |
| llama70b | h200 | trt | fp8 | 4 | 64 | 8192 | 1024 | 11 | 236,326 | 0.37 |
| llama70b | b200 | trt | fp4 | 1 | 64 | 8192 | 1024 | 10 | 611,350 | 0.38 |
| llama70b | b200 | vllm | fp4 | 2 | 64 | 8192 | 1024 | 10 | 412,248 | 0.40 |
| llama70b | b200 | trt | fp8 | 8 | 128 | 8192 | 1024 | 10 | 212,056 | 0.41 |

## Highest output-token benchmark anchors

| Model | GPU | Framework | Precision | GPU count | ISL | OSL | Concurrency | Rows | Output p50 tok/s/MW |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| gptoss120b | b200 | trt | fp4 | 1 | 1024 | 8192 | 128 | 30 | 4,631,496 |
| gptoss120b | b200 | trt | fp4 | 1 | 1024 | 1024 | 128 | 29 | 3,975,768 |
| gptoss120b | b200 | trt | fp4 | 2 | 1024 | 8192 | 128 | 43 | 3,764,752 |
| gptoss120b | b200 | vllm | fp4 | 1 | 1024 | 1024 | 128 | 32 | 3,740,595 |
| gptoss120b | b200 | vllm | fp4 | 1 | 1024 | 8192 | 128 | 34 | 3,651,254 |
| dsr1 | gb200 | dynamo-trt | fp4 | 12 | 1024 | 1024 | 4300 | 44 | 3,643,595 |
| dsr1 | gb200 | dynamo-trt | fp4 | 12 | 1024 | 1024 | 2252 | 44 | 3,420,175 |
| gptoss120b | b200 | trt | fp4 | 2 | 1024 | 1024 | 128 | 28 | 3,195,836 |
| dsr1 | gb200 | dynamo-trt | fp4 | 24 | 1024 | 1024 | 4300 | 44 | 3,123,965 |
| gptoss120b | b200 | vllm | fp4 | 2 | 1024 | 1024 | 128 | 32 | 2,860,797 |
| gptoss120b | b200 | vllm | fp4 | 2 | 1024 | 8192 | 128 | 34 | 2,853,048 |
| gptoss120b | b200 | trt | fp4 | 1 | 1024 | 8192 | 64 | 48 | 2,798,613 |
| dsr1 | gb200 | dynamo-trt | fp4 | 24 | 1024 | 1024 | 2150 | 45 | 2,776,704 |
| gptoss120b | b200 | trt | fp4 | 1 | 1024 | 1024 | 64 | 52 | 2,694,229 |
| gptoss120b | b200 | vllm | fp4 | 1 | 1024 | 8192 | 64 | 53 | 2,611,227 |
| gptoss120b | b200 | vllm | fp4 | 1 | 1024 | 1024 | 64 | 54 | 2,602,662 |
| llama70b | b200 | trt | fp4 | 1 | 1024 | 1024 | 128 | 12 | 2,523,423 |
| dsr1 | gb200 | dynamo-trt | fp4 | 32 | 8192 | 1024 | 2150 | 43 | 2,448,899 |
| gptoss120b | b200 | trt | fp4 | 1 | 8192 | 1024 | 128 | 32 | 2,415,092 |
| gptoss120b | b200 | trt | fp4 | 4 | 1024 | 8192 | 128 | 33 | 2,333,973 |

## Next simulation handoff

Use the CSV rows to generate LLMServingSim workloads:

```json
{"input_toks": 8192, "output_toks": 1024, "arrival_time_ns": 0}
```

For agentic workloads, convert a sequence of rows into sub-requests:

```json
{"session_id": "coding_agent_0", "arrival_time_ns": 0, "sub_requests": [{"input_toks": 8192, "output_toks": 512, "tool_duration_ns": 1000000000}]}
```

The current `kv_pressure_proxy` is intentionally simple. It is a ranking feature, not a physical KV-cache byte model. The next version should add model-layer/head/hidden-dimension metadata so KV bytes can be estimated explicitly.
