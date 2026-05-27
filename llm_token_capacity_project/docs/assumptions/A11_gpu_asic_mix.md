# A11 gpu_asic_mix

**Subtitle:** How H200, B200, GB200 and purpose-built allocation bridges compute capacity into generated output tokens

**Updated:** 2026-05-27

## Why This Assumption Exists

The forecast cannot explain `tokens_per_second_per_mw` only by saying a company uses GPUs, TPUs, Trainium, Maia or MTIA. It must distinguish GPU generations such as H200, B200 and GB200 because equal MW can create materially different token throughput. At the same time, most model owners do not publish the actual production inference fleet by generation.

Accordingly, this model separates two layers:

| Layer | Meaning | Treatment |
|---|---|---|
| Platform presence | An official source confirms that a provider uses or targets a hardware platform for AI/inference | Fact anchor |
| Numeric serving mix | Percentage of modeled inference-serving accelerator load assigned to GPU versus purpose-built accelerators | Scenario until operated allocation is disclosed |
| GPU generation mix | Percentage assigned to H200, B200 and GB200 within the modeled inference load | Editable scenario until company deployment data is disclosed |

## Model Formula

```text
tokens_per_second_per_mw =
  (h200_share * h200_reference_tps_per_mw
  + b200_share * b200_reference_tps_per_mw
  + gb200_share * gb200_reference_tps_per_mw
  + purpose_built_share * purpose_built_reference_tps_per_mw)
  * commercial_workload_fit_factor
```

Hardware mix remains visible because it matters to roadmap and allocation research. H200/B200/GB200 references can influence headline output where comparable public rows are available. Purpose-built hardware creates no premium until it has a comparable generated-output benchmark; the default purpose-built reference is B200 and is explicitly editable.

## Default GPU Generation Input

The first editable starting scenario applies the following migration inside the GPU portion of inference-serving load:

| Year | H200 share of GPU portion | B200 share of GPU portion | GB200 share of GPU portion |
|---|---:|---:|---:|
| 2026 | 55% | 40% | 5% |
| 2030 | 10% | 35% | 55% |

Intermediate years interpolate linearly. These shares are not provider facts; they are scenario inputs in Excel `02_GPU_Mix_Input` to be replaced with procurement, deployment or accelerator-hour evidence.

## Current Numeric Mix Policy

| Company | Sourced Platform Direction | Base 2026 GPU / Purpose-Built | Base 2030 GPU / Purpose-Built | Derivation Type |
|---|---|---:|---:|---|
| Microsoft | Maia inference accelerator officially deployed for Microsoft AI surfaces | 90% / 10% | 55% / 45% | Numeric scenario |
| Google | TPU/Ironwood inference platform direction | 20% / 80% | 10% / 90% | Numeric scenario |
| Meta | MTIA inference-first deployment and GenAI roadmap | 90% / 10% | 55% / 45% | Numeric scenario |
| xAI | Colossus NVIDIA GPU anchor | 100% / 0% | 100% / 0% | Conservative GPU reference |
| OpenAI | Stargate NVIDIA GB200 rack delivery anchor | 100% / 0% | 100% / 0% | Conservative GPU reference |
| Anthropic | AWS Project Rainier Trainium capacity direction | 35% / 65% | 15% / 85% | Numeric scenario |
| DeepSeek | Published H800 inference service overview | 100% / 0% | 100% / 0% | Disclosed hardware reference; future mix scenario |
| Alibaba | Official Qwen GPU deployment path; operated mix not disclosed | 100% / 0% | 100% / 0% | Conservative GPU reference |
| Tencent | AI Infra/MoE direction; operated mix not disclosed | 100% / 0% | 100% / 0% | Conservative GPU reference |

## How To Interpret The Numbers

- A purpose-built share above zero means the platform direction is sourced, not that the exact percentage is publicly measured.
- Keeping a company at 100% GPU reference does not claim it owns no ASICs. It means no audited model-owner serving allocation has been adopted into Base.
- No relative efficiency uplift is applied in headline output without comparable output-token measurements at matched model, precision, input/output lengths and SLO.
- The executive workbook shows company-year GPU generation mix in `02_GPU_Mix_Input`, the formula bridge in `03_Calculation`, and aggressive ceiling interpretation in `06_Aggressive_View`; detailed rationale remains in agent records.

## Replacement Evidence Required

The numeric mix should be upgraded only when at least one of the following becomes available:

1. provider-operated inference accelerator-hours or rack allocation by model family
2. product/model routing disclosures linking commercial token surfaces to hardware
3. comparable production output-token throughput per MW by hardware and workload
4. official fleet split or capacity allocation statement with an explicit denominator

## Source Anchors

- Microsoft, *Microsoft introduces Maia 200: New inference accelerator enhances AI performance in Azure*, 2026-01-26: https://news.microsoft.com/source/emea/2026/01/microsoft-introduces-maia-200-new-inference-accelerator-enhances-ai-performance-in-azure/
- Google Cloud, *Ironwood TPU: the age of inference*, 2025-04-09: https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/
- Meta, *Expanding Meta's Custom Silicon to Power Our AI Workloads*, 2026-03-11: https://about.fb.com/news/2026/03/expanding-metas-custom-silicon-to-power-our-ai-workloads/
- OpenAI, *Five new Stargate sites*, 2025-09-23: https://openai.com/index/five-new-stargate-sites/
- Amazon Web Services, *AWS activates Project Rainier*, 2025-10-29: https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster
- DeepSeek, *V3/R1 inference system overview*, 2025-02-28: https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md
- Alibaba Cloud, *Deploy a Qwen3-32B inference service with ACS GPU computing power*, 2025-09-18: https://www.alibabacloud.com/help/doc-detail/2921971.html
- Tencent, *Tencent Unveils New AI Upgrades, Proprietary Innovations, and Global Solutions*, 2024-09-05: https://www.tencent.com/en-us/articles/2201930.html
