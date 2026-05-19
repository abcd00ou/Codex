# Learning Queue: A08 tokens_per_second_per_mw

| Created | Learning task | Priority | Expected evidence | Status |
|---|---|---|---|---|
| 2026-05-15 | PagedAttention/Splitwise/DistServe updates | pending | Need source review | open |
| 2026-05-15 | InferenceX or similar benchmark changes | pending | Need source review | open |
| 2026-05-15 | hardware generation H100/H200/GB200/TPU/Trainium throughput | pending | Need source review | open |
| 2026-05-15 | SemiAnalysis InferenceX benchmark methodology and tokens/MW proxy extraction | high | Benchmark/proxy evidence with model, hardware, batch, latency, utilization caveats | open |
| 2026-05-15 | AI 2027 agentic workload and test-time compute implications for tokens/MW | medium | Scenario stress-test for longer context/tool-use/reasoning load; not benchmark fact | open |
| 2026-05-19 | Ingest InferenceX normalized dataset by model/GPU/framework/precision/ISL/OSL | high | `data/inferencex/normalized/inferencex_benchmark_results.csv` and `inferencex_metric_profile.csv`; calculate candidate tokens/sec/MW bands without changing Base | done - 2026-05-19 |
| 2026-05-19 | Map InferenceX profile rows into Base/Bull/Bear A08 candidate bands | high | Use only comparable model/GPU/framework/precision/ISL/OSL groups; document p10/p50/p90 and exclude failed/error rows | open |

## Next Agent Prompt

```text
You are the A08 Tokens per MW Agent for the LLM token capacity project.
Read this folder's README.md, state.md, evidence.md, learning_queue.md, plus shared evidence rules.
Pick one open learning task, gather only high-quality sources, classify each claim as Fact/Estimate/Proxy/Scenario,
then propose whether `tokens_per_second_per_mw` should change. Do not modify generator values until orchestrator review.
```
