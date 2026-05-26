# Evidence: A08 tokens_per_second_per_mw

This file stores reviewed evidence for `tokens_per_second_per_mw`.

## Evidence Table

| evidence_id | source_id | date | evidence_class | exact_claim_or_number | unit | model_field_impacted | confidence | reviewer |
|---|---|---|---|---|---|---|---|---|
| A08_E000 | baseline | 2026-05-15 | Scenario | Initial agent created from existing assumption textbook | n/a | tokens_per_second_per_mw | Low-Medium | Codex |
| A08_E001 | WATCH_INFERENCEX | 2026-05-15 | Proxy | Candidate benchmark source for inference serving efficiency and tokens/MW sanity check; not yet promoted to numeric model input | n/a | tokens_per_second_per_mw | Low-Medium | Codex |
| A08_E002 | JOULE_INFERENCE_2026 | 2026-05-18 | Proxy | Inference energy depends on query length, response length, model choice and test-time compute; use as energy/query and joules/token sanity layer, not company telemetry | energy/query, joules/token | tokens_per_second_per_mw | Medium | Codex |
| A08_E003 | IBM_PD_2026 | 2026-05-18 | Mechanism | Prefill-decode disaggregation has performance and energy trade-offs and should be evaluated against workload shape rather than assumed universally positive | n/a | tokens_per_second_per_mw | Medium | Codex |
| A08_E004 | ARXIV_SPEC_DECODE_2605 | 2026-05-18 | Mechanism | Speculative decoding changes latency/throughput trade-offs and requires workload/model-specific latency modeling | n/a | tokens_per_second_per_mw | Low-Medium | Codex |
| A08_E005 | INFERENCEX_DUMP_2026_05_11 | 2026-05-19 | Proxy | Full InferenceX-app release dump normalized: 72,091 inference performance rows and 298 model/GPU/framework/precision/ISL/OSL profile groups; fields include tput_per_gpu, output_tput_per_gpu, tokens/sec/MW, J/token, TTFT/TPOT | tokens/s/GPU, tokens/s/MW, J/token | tokens_per_second_per_mw | Medium | Codex |
| A08_E006 | ASSUMP_NUMERIC_ACCELERATOR_MIX | 2026-05-26 | Derived scenario | Company-year tokens/MW now bridges GPU reference throughput through numeric GPU/purpose-built mix, relative hardware factor, architecture/workload factor and software-efficiency growth | output tokens/s/MW | tokens_per_second_per_mw | Low-Medium | Codex |

## Review Notes

- Add only source-reviewed evidence here.
- Do not paste copyrighted report text. Summarize claim, number, unit, and implication.
- Keep fact and interpretation separate.

## Cycle 1 Interpretation

- A08 now exposes how Base `tokens_per_second_per_mw` is composed; it is still a derived estimate rather than company production telemetry.
- Add an energy sanity layer using joules/token or energy/query before increasing tokens/MW.
- Treat prefill/decode disaggregation and speculative decoding as mechanism evidence. They justify scenario sensitivity, not company production coefficients.
- InferenceX dump rows are now usable for benchmark sanity checks, but still require SLO/workload comparability before changing Base forecast coefficients.
- The hardware-mix bridge is auditable in `04_gpu_asic_mix`, `05_inference_efficiency`, and `02b_number_trace`; numeric mix must be replaced if operated fleet-share disclosure becomes available.
