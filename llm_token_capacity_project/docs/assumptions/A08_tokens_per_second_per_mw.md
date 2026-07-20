# A08 tokens_per_second_per_mw

**부제:** 1MW inference load가 초당 몇 token을 만들 수 있는가

**생성일:** 2026-05-15

**학습용 starting band:** company fact가 아니라 benchmark/proxy. 모델 크기, context, hardware, serving stack에 따라 wide band 사용.

> 이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

## Executive Summary

`tokens_per_second_per_mw`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

## 정의

tokens_per_second_per_mw는 inference power 1MW가 초당 생성할 수 있는 output token 수를 의미한다. 이 변수는 token forecast의 핵심 productivity coefficient다. 하지만 단일 산업 표준값이 있는 지표가 아니다. 모델 크기, active parameter, prompt length, output length, batch shape, latency SLO, accelerator generation, memory bandwidth, interconnect, serving software에 따라 크게 달라진다.

이 값은 company-level production telemetry가 공개되지 않는 한 대부분 proxy다. 따라서 보고서에서는 'benchmark calibrated assumption' 또는 'scenario coefficient'로 표시해야 한다.

## 전문가 관점의 운영 원리

LLM serving은 prefill과 decode로 나뉜다. Prefill은 prompt를 처리하는 단계이고 decode는 output token을 하나씩 생성하는 단계다. Prefill은 compute-intensive, decode는 memory/KV-cache/latency-sensitive 성격이 강하다. PagedAttention은 KV cache memory management를 개선해 batching과 throughput을 높이는 mechanism을 제시했고, Splitwise와 DistServe는 prefill과 decode를 분리해 GPU pool을 다르게 쓰는 approach를 제시한다.

Hardware도 중요하다. H100/H200/B200/GB200, TPU Ironwood, Trainium/Inferentia는 compute precision, HBM capacity, memory bandwidth, interconnect, software stack이 다르다. Google Ironwood는 inference-oriented TPU로 발표되었고, NVIDIA GB200 NVL72는 rack-scale NVLink domain을 제공한다. 하지만 공식 hardware peak FLOPs를 그대로 tokens/sec/MW로 바꾸면 안 된다. production serving efficiency는 kernel, batching, scheduling, SLO, utilization에 의해 크게 낮아진다.

tokens/sec/MW는 결국 effective throughput 지표다. 같은 model이라도 latency SLA를 완화하고 batch를 키우면 throughput은 올라가지만 사용자 경험이 나빠질 수 있다. enterprise real-time assistant와 offline batch summarization은 완전히 다른 efficiency를 보인다.

## 현실적 숫자 범위 잡기

현실적인 접근은 세 가지 sanity check를 동시에 쓰는 것이다. 첫째, benchmark layer에서 GPU count와 model active parameter로 대략적인 tokens/sec를 역산한다. 둘째, energy layer에서 joules/token과 inference MW로 daily token을 계산한다. 셋째, service layer에서 utilization과 latency SLO를 고려해 평균 throughput을 낮춘다.

closed model은 특히 wide band가 필요하다. 공개 모델 benchmark가 있다고 해서 OpenAI, Anthropic, Google production model과 동일하게 볼 수 없다. 공개 MoE 모델은 active parameter가 있으므로 상대적으로 더 좁은 band를 둘 수 있지만, 실제 serving stack과 traffic mix는 여전히 unknown이다.

## 모델링 영향

tokens_per_second_per_mw는 active inference MW와 곱해져 token/day를 만든다. 따라서 이 값의 20% 차이는 token forecast의 20% 차이다. 특히 2030 forecast에서는 hardware generation과 serving efficiency improvement를 어떻게 가정하느냐가 큰 차이를 만든다.

이 변수는 memory marketing에도 직접 연결된다. tokens/MW가 올라가면 같은 전력으로 더 많은 token을 만들 수 있어 HBM capacity pressure가 낮아질 수도 있지만, 실제로는 demand elasticity 때문에 더 많은 inference traffic이 생겨 전체 memory demand가 다시 증가할 수 있다.

## 2026-07-20 Workload-Split Benchmark Mapping

최종 token 생성량 산식에서는 검증이 어려운 efficiency factor를 겹쳐 곱하지 않습니다. 다만 공개 benchmark를 폐쇄형 상용모델의 실제 처리량으로 오해하지 않도록, public InferenceX reference, short/long/agentic workload mix, commercial workload fit scenario를 분리합니다.

```text
fleet_reference_tps_per_mw =
  h200_share * h200_reference_tps_per_mw
  + b200_share * b200_reference_tps_per_mw
  + gb200_share * gb200_reference_tps_per_mw
  + purpose_built_share * purpose_built_reference_tps_per_mw

tokens_per_second_per_mw =
  (
    short_chat_share * short_chat_reference_tps_per_mw
    + long_chat_share * long_chat_reference_tps_per_mw
    + agentic_share * agentic_reference_tps_per_mw
  )
  * commercial_workload_fit_factor
```

- `short_chat`은 `single_turn`, `ISL=1024`, `OSL=1024`, generated output 기준 `output_tok_s_mw` p50입니다.
- `long_chat`은 가능한 경우 `ISL=8192`, `OSL=1024` InferenceX row를 사용하고, row가 부족하면 short-chat reference에 long-context haircut을 적용합니다.
- `agentic`은 InferenceX agentic trace profile의 약 100k input / 860 output token request shape를 반영합니다. 아직 matched 100k-input throughput row가 없으므로 long-chat TPS/MW에 agentic context/tooling haircut을 적용합니다.
- 보고용 Excel `01_Benchmark_Input`은 GPU별 public reference와 Bear/Base/Bull fit factor를, `02b_Workload_Mix_Input`은 업체별 short/long/agentic 비중을 보여줍니다.
- `02_GPU_Mix_Input`에서 업체·연도·시나리오별 H200/B200/GB200/purpose-built share를 추후 직접 교체할 수 있습니다.
- Meta/Tencent처럼 high-volume chat surface가 큰 경우 short-chat 비중이 높고, Anthropic/OpenAI처럼 Claude Code/Codex 등 agentic 제품 근거가 강한 경우 agentic 비중이 높습니다.
- TPU, Maia, MTIA, Trainium의 comparable output-token/MW row가 채택되기 전에는 purpose-built reference를 B200 placeholder로 두어 hardware uplift를 만들지 않습니다.
- `architecture_workload_factor`, `software_efficiency_growth`, MoE uplift와 utilization은 headline 토큰 결과에 곱하지 않고 별도 연구/sensitivity로만 관리합니다.
- 공격적 관점은 `06_Aggressive_View`에서 Bull commercial case와 public benchmark ceiling을 분리해 확인합니다. Ceiling은 전략적 상한이지 Base 추정이 아닙니다.

## Hallucination 위험

가장 큰 위험은 benchmark number를 company fact처럼 쓰는 것이다. 두 번째 위험은 peak throughput을 annual average throughput으로 쓰는 것이다. 세 번째 위험은 input token과 output token을 섞는 것이다. token forecast에서 말하는 token이 input, output, total processed 중 무엇인지 반드시 명시해야 한다.

## 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?
- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?
- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?
- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?
- low/base/high band와 confidence가 같이 기록되어 있는가?
- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

## 권장 모델 필드

- assumption_id: `A08_TOKENS_PER_SECOND_PER_MW`
- field_name: `tokens_per_second_per_mw`
- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나
- confidence: High / Medium / Low
- replacement_path: 공식 source가 나오면 교체할 경로

## 참고자료

- **PAGED_ATTENTION:** Efficient Memory Management for LLM Serving with PagedAttention, Kwon et al., arXiv, 2023. https://arxiv.org/abs/2309.06180
- **SPLITWISE:** Splitwise: Efficient generative LLM inference using phase splitting, Patel et al., arXiv, 2023. https://arxiv.org/abs/2311.18677
- **DISTSERVE:** DistServe: Disaggregating Prefill and Decoding, Zhong et al., arXiv, 2024. https://arxiv.org/abs/2401.09670
- **MS_SPLITWISE:** Splitwise improves GPU usage by splitting LLM inference phases, Microsoft Research, 2024. https://www.microsoft.com/en-us/research/blog/splitwise-improves-gpu-usage-by-splitting-llm-inference-phases/
- **GOOGLE_IRONWOOD:** Ironwood: the first Google TPU for the age of inference, Google Cloud, 2025. https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/
- **NVIDIA_H100:** NVIDIA H100 Tensor Core GPU, NVIDIA, accessed 2026-05-15. https://www.nvidia.com/en-us/data-center/h100/
- **NVIDIA_H200:** NVIDIA H200 Tensor Core GPU, NVIDIA, accessed 2026-05-15. https://www.nvidia.com/en-us/data-center/h200/
- **NVIDIA_GB200:** NVIDIA GB200 NVL72, NVIDIA, accessed 2026-05-15. https://www.nvidia.com/en-us/data-center/gb200-nvl72/

## 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
