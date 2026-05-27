# State: A11 gpu_asic_mix

| Field | Value |
|---|---|
| agent_id | A11 |
| owned_field | h200_share; b200_share; gb200_share; purpose_built_accelerator_share; hardware reference TPS/MW replacement path |
| current_starting_band | sourced platform presence with numeric scenario mix |
| confidence | Medium for platform direction; Low-Medium for operated share |
| last_reviewed | 2026-05-27 |
| status | GPU-generation mix editable; public H200/B200/GB200 reference bridge visible; no unsupported purpose-built uplift |

## Current Assumption

The Base model uses numeric GPU/purpose-built accelerator shares only when they are visibly labeled as scenarios. Official sources establish platform presence and direction; they do not establish exact company serving-fleet allocation.

## Current Base Mix Policy

| Company | 2026 GPU / Purpose-Built | 2030 GPU / Purpose-Built | Purpose-Built Label | Why |
|---|---:|---:|---|---|
| Microsoft | 90% / 10% | 55% / 45% | Maia | Official inference accelerator direction; share is scenario. |
| Google | 20% / 80% | 10% / 90% | TPU / Ironwood | TPU-heavy platform is official direction; share is scenario. |
| Meta | 90% / 10% | 55% / 45% | MTIA | MTIA inference-first deployment direction is official; share is scenario. |
| xAI | 100% / 0% | 100% / 0% | none disclosed | NVIDIA GPU anchor only in Base. |
| OpenAI | 100% / 0% | 100% / 0% | none disclosed | Stargate GB200 GPU anchor; no quantified custom mix. |
| Anthropic | 35% / 65% | 15% / 85% | Trainium / hosted purpose-built | Project Rainier anchors Trainium direction; share is scenario. |
| DeepSeek | 100% / 0% | 100% / 0% | none disclosed | Published H800 inference service anchor. |
| Alibaba | 100% / 0% | 100% / 0% | none disclosed | Official GPU-serving example; operated mix undisclosed. |
| Tencent | 100% / 0% | 100% / 0% | none disclosed | AI infra/MoE direction disclosed; operated mix undisclosed. |

## Proposed Changes

| Date | Proposed change | Reason | Evidence IDs | Status |
|---|---|---|---|---|
| 2026-05-26 | Add numeric accelerator mix and efficiency bridge into forecast model | Previous report described hardware without numerically tracing it into tokens/MW. | A11_E001-A11_E009 | implemented |
| 2026-05-27 | Remove unsupported purpose-built accelerator efficiency premium from headline | Platform presence and modeled mix do not establish comparable generated-output TPS/MW uplift. | A11_E001-A11_E009; HC22 | implemented |
| 2026-05-27 | Apply no-uplift rule after commercial-workload benchmark adjustment | Hardware mix must not cause public reference throughput to be read as closed-model production performance. | A11_E001-A11_E009; A08_E005; LR28 | implemented; purpose-built TPS equals serving reference until replaced |
| 2026-05-27 | Split GPU bucket into editable H200/B200/GB200 generation mix | Equal inference MW yields materially different token capacity by installed GPU generation; prior GPU-versus-ASIC split could not express this. | A08_E005; A11_E001-A11_E009 | implemented in `02_GPU_Mix_Input`; provider fleet facts pending |

## Downstream Impact Notes

- A11 changes feed A08 `tokens_per_second_per_mw` and headline token supply.
- Hardware-share changes remain visible, while unverified purpose-built or software uplift does not enter headline output. H200/B200/GB200 public references are weighted before commercial workload fit is applied.
- Replacement evidence priority is operated inference accelerator-hours or model-level output tokens/MW.
