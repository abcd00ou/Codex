# A04 ai_workload_share

**부제:** IT load 중 실제 AI training/inference cluster가 차지하는 비중

**생성일:** 2026-05-15

**학습용 starting band:** AI-dedicated facility: 80-95%, mixed cloud facility: 50-80%, model owner attribution 불명확 시 confidence downgrade.

> 이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

## Executive Summary

`ai_workload_share`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

## 정의

ai_workload_share는 IT load 중 AI accelerator cluster가 차지하는 비중이다. IT load에는 GPU/ASIC 서버뿐 아니라 CPU 서버, storage, network, control plane, security, monitoring, data pipeline, non-AI cloud workload가 포함될 수 있다. AI 전용으로 설계된 신규 campus라면 이 비중이 높을 수 있지만, mixed cloud region이라면 낮아질 수 있다.

이 변수는 active_power_gw와 inference_share 사이의 다리다. active_power_gw를 PUE로 나눠 IT load를 만든 뒤, 그중 AI workload에 해당하는 몫을 잡아야 training/inference 계산을 시작할 수 있다.

## 전문가 관점의 운영 원리

AI workload라고 해도 모두 GPU compute는 아니다. 대형 LLM 서비스에는 data ingestion, retrieval index, storage, embedding pipeline, safety classifier, logging, monitoring, load balancer, orchestration service가 필요하다. 특히 RAG와 agent workload가 커질수록 storage와 CPU-side serving infrastructure도 중요해진다. 그러나 token generation capacity를 계산할 때는 이 보조 load가 accelerator inference load와 구분되어야 한다.

Google TPU v5e 문서는 training과 serving workload가 같은 TPU product 내에서도 다르게 provision될 수 있음을 보여준다. AWS Project Rainier처럼 Anthropic용 Trainium2 cluster가 명시되는 경우 AI workload share가 높다고 볼 수 있지만, 그 cluster 안에서도 training과 inference, eval, post-training이 나뉜다. NVIDIA GB200 NVL72 같은 rack-scale system은 AI accelerator load의 직접 신호지만, facility 전체의 storage/network/control plane overhead는 별도로 남는다.

## 현실적 숫자 범위 잡기

AI-dedicated campus 또는 partner-specific cluster라면 ai_workload_share를 80-95%로 시작할 수 있다. 하지만 hyperscaler region 전체나 mixed-use data center라면 50-80%가 더 안전하다. 공개자료가 'AI data center'라고 말하더라도 모든 IT load가 token-generating accelerator라고 가정하면 안 된다.

이 가정은 architecture maturity에 따라 바뀐다. 대형 AI cluster가 rack-scale로 통합될수록 accelerator share가 높아질 수 있지만, agentic AI와 RAG가 커질수록 storage, retrieval, networking, CPU orchestration load도 증가한다. 따라서 AI workload share를 무조건 100%에 가깝게 두는 것은 위험하다.

## 모델링 영향

ai_workload_share는 inference_gw를 선형적으로 움직인다. active_power_gw와 PUE가 같을 때 ai_workload_share가 0.8에서 0.9로 오르면 AI IT load와 downstream token capacity가 12.5% 증가한다. 따라서 이 값은 생각보다 큰 민감도를 갖는다.

이 가정은 memory marketing에도 중요하다. AI workload share가 높을수록 HBM과 accelerator attach가 커지고, mixed workload share가 높을수록 DDR5, enterprise SSD, network/storage infrastructure 기회도 커진다.

## 2026-05-26 Workbook 반영 방식

최종 Excel은 company별 `ai_workload_share` 값을 단독 숫자로만 두지 않습니다. `02b_number_trace`와 `03_power_capacity`에 각 업체의 `why_this_number`, `source_ids`, `derivation_type`, `replacement_path`를 기록합니다.

- 공식 AI/inference accelerator 발표는 AI-focused direction의 근거입니다.
- 공식 발표가 AI IT load의 정확한 비율을 공개한 것으로 해석하지 않습니다.
- 현재 share는 scenario allocation이며, company-level scheduling 또는 allocated accelerator-hour telemetry가 나오면 교체합니다.

## Hallucination 위험

가장 큰 위험은 AI data center라는 표현을 보고 IT load 전체를 GPU inference로 간주하는 것이다. 두 번째 위험은 storage와 networking overhead를 무시하는 것이다. 세 번째 위험은 hyperscaler region 전체와 model-owner-dedicated cluster를 같은 share로 처리하는 것이다.

## 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?
- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?
- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?
- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?
- low/base/high band와 confidence가 같이 기록되어 있는가?
- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

## 권장 모델 필드

- assumption_id: `A04_AI_WORKLOAD_SHARE`
- field_name: `ai_workload_share`
- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나
- confidence: High / Medium / Low
- replacement_path: 공식 source가 나오면 교체할 경로

## 참고자료

- **LBNL_DC:** 2024 United States Data Center Energy Usage Report, LBNL / DOE, 2024. https://buildings.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report
- **GOOGLE_TPU_V5E:** Cloud TPU v5e documentation, Google Cloud, accessed 2026-05-15. https://docs.cloud.google.com/tpu/docs/v5e
- **AWS_RAINIER:** AWS activates Project Rainier, Amazon, 2025. https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster
- **NVIDIA_GB200:** NVIDIA GB200 NVL72, NVIDIA, accessed 2026-05-15. https://www.nvidia.com/en-us/data-center/gb200-nvl72/
- **GOOGLE_IRONWOOD:** Ironwood: the first Google TPU for the age of inference, Google Cloud, 2025. https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/

## 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
