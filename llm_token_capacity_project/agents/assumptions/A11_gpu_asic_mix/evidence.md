# Evidence: A11 gpu_asic_mix

This file stores source-reviewed platform evidence and marks numeric shares as scenarios unless a source explicitly discloses operated allocation.

## Evidence Table

| evidence_id | source_id | date | evidence_class | exact_claim_or_number | unit | model_field_impacted | confidence | reviewer |
|---|---|---|---|---|---|---|---|---|
| A11_E001 | SRC_MS_MAIA200 | 2026-01-26 | Platform fact | Maia 200 is designed for inference and deployed across Microsoft AI model/product surfaces | platform presence | purpose_built_accelerator_share | High for presence / Low for share | Codex |
| A11_E002 | SRC_GOOGLE_IRONWOOD | 2025-04-09 | Platform fact | Ironwood is positioned by Google as an inference TPU | platform presence | purpose_built_accelerator_share | High for presence / Medium-Low for share | Codex |
| A11_E003 | SRC_META_MTIA_GENAI_2026 | 2026-03-11 | Platform fact | Meta reports MTIA chips deployed for inference and GenAI inference-oriented roadmap | platform presence | purpose_built_accelerator_share | High for presence / Low for LLM share | Codex |
| A11_E004 | SRC_XAI_NVIDIA_COLOSSUS | 2024-12-04 | Hardware anchor | xAI Colossus GPU scale is anchored to NVIDIA Hopper GPUs | GPU count direction | gpu_share | Medium | Codex |
| A11_E005 | SRC_OPENAI_STARGATE_PROGRESS | 2025-09-23 | Hardware anchor | Oracle began delivery of NVIDIA GB200 racks for Stargate | rack/platform direction | gpu_share | Medium-High | Codex |
| A11_E006 | SRC_AWS_RAINIER_ACTIVE | 2025-10-29 | Platform fact | AWS activated Trainium2-based Project Rainier capacity for Anthropic workloads | platform presence | purpose_built_accelerator_share | High for presence / Low for inference share | Codex |
| A11_E007 | SRC_DEEPSEEK_H800_INFERENCE | 2025-02-28 | Hardware fact | DeepSeek disclosed V3/R1 online inference services on H800 GPUs in its overview | platform at disclosure date | gpu_share | High for disclosed service / Low for future mix | Codex |
| A11_E008 | SRC_ALIBABA_QWEN_GPU_DEPLOY | 2025-09-18 | Hardware reference | Alibaba Cloud documents Qwen inference deployment using GPU computing power | supported deployment path | gpu_share | Medium | Codex |
| A11_E009 | SRC_TENCENT_AI_INFRA_MOE | 2024-09-05 | Platform direction | Tencent discloses AI Infra and Hunyuan Turbo MoE efficiency direction without numeric accelerator split | direction only | accelerator_mix_factor | Medium for direction / Low for mix | Codex |

## Review Notes

- Numeric shares in the Base forecast are not official fleet allocation facts.
- Purpose-built relative efficiency factors are scenario coefficients until SLO-matched output-token production measurements exist.
- A08 and Logic Review Agent approval is required before materially changing this bridge.
