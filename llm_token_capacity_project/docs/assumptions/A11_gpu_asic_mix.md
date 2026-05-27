# A11 gpu_asic_mix

**Subtitle:** How numeric accelerator allocation bridges compute capacity into generated output tokens

**Updated:** 2026-05-27

## Why This Assumption Exists

The forecast cannot explain `tokens_per_second_per_mw` only by saying a company uses GPUs, TPUs, Trainium, Maia or MTIA. Hardware composition must be numeric if it affects token supply. At the same time, most model owners do not publish the actual percentage of production inference traffic served by each accelerator family.

Accordingly, this model separates two layers:

| Layer | Meaning | Treatment |
|---|---|---|
| Platform presence | An official source confirms that a provider uses or targets a hardware platform for AI/inference | Fact anchor |
| Numeric serving mix | Percentage of modeled inference-serving accelerator load assigned to GPU versus purpose-built accelerators | Scenario until operated allocation is disclosed |

## Model Formula

```text
tokens_per_second_per_mw =
  gpu_share * gpu_benchmark_tps_per_mw
  + purpose_built_accelerator_share * purpose_built_tps_per_mw
```

Hardware mix remains visible because it matters to roadmap and allocation research. However, it creates no headline performance premium until the corresponding purpose-built hardware has a comparable generated-output benchmark under the adopted workload conditions. In the current core formula, `purpose_built_tps_per_mw` equals the selected GPU benchmark proxy where no matched public row is adopted.

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
- The workbook shows every company-year mix in `04_gpu_asic_mix`, the resulting bridge in `05_inference_efficiency`, and every numeric rationale in `02b_number_trace`.

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
