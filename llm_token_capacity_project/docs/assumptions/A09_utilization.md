# A09 utilization

**부제:** 이론 capacity 중 실제 연평균 토큰으로 전환되는 비율

**생성일:** 2026-05-15

**학습용 starting band:** 2026 inference utilization 45-65%, 2030 60-80%. Peak benchmark를 평균 utilization로 사용 금지.

> 이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

## Executive Summary

`utilization`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

## 정의

utilization은 이론적으로 provisioned된 inference capacity 중 실제 token generation으로 전환되는 평균 비율이다. 여기서 평균은 보통 연중 또는 일중 평균을 의미한다. utilization이 낮다고 반드시 운영이 나쁘다는 뜻은 아니다. latency SLO, failover reserve, regional redundancy, traffic burst, model routing 때문에 의도적으로 여유 capacity를 둔다.

utilization은 inference_power_share와 다르다. inference_power_share는 AI IT load 중 inference에 배정된 전력이고, utilization은 그 inference capacity가 실제 traffic 처리에 사용되는 평균 비율이다.

## 전문가 관점의 운영 원리

LLM inference traffic은 시간대, 지역, 제품 surface에 따라 변동한다. consumer chatbot은 peak/off-peak 차이가 있고, enterprise workload는 업무시간과 batch job 패턴이 다르며, coding agent는 긴 session과 tool call을 동반할 수 있다. latency SLO를 맞추려면 peak traffic을 처리할 headroom이 필요하고, 장애 시 failover를 위한 reserve도 필요하다.

Serving system은 utilization과 latency 사이에서 trade-off를 가진다. batch를 크게 만들면 throughput과 utilization은 좋아지지만 first-token latency가 나빠질 수 있다. PagedAttention, Splitwise, DistServe 같은 연구는 이 trade-off를 개선하려는 방향이다. 하지만 production system이 항상 paper benchmark처럼 움직인다고 볼 수는 없다.

TPU/Trainium/Inferentia/GPU 같은 accelerator는 workload shape에 따라 utilization이 다르다. training은 long-running job으로 high utilization을 목표로 할 수 있지만, inference는 SLO와 burst reserve 때문에 평균 utilization이 낮아질 수 있다. 따라서 training cluster와 inference fleet utilization을 같은 값으로 두면 안 된다.

## 현실적 숫자 범위 잡기

초기 상용 서비스는 traffic 예측이 불확실하고 software stack이 안정화 중이므로 utilization을 낮게 두는 것이 안전하다. 시간이 지나 model routing, batching, KV cache management, regional load balancing이 개선되면 utilization은 상승할 수 있다. 그러나 100%에 가까운 연평균 utilization은 일반적으로 비현실적이다.

2026년 45-65%, 2030년 60-80%는 학습용 band다. paid API 비중이 높고 batchable workload가 많으면 상단에 가까울 수 있다. free consumer chatbot이나 strict latency real-time workload가 많으면 하단에 가까울 수 있다.

## 모델링 영향

utilization은 token forecast에 선형적으로 작용한다. tokens/sec/MW가 같더라도 utilization이 0.55에서 0.70으로 오르면 annual token은 27% 증가한다. 이 값은 software optimization과 demand smoothing의 효과를 반영하는 핵심 coefficient다.

utilization 상승은 capacity 부족을 일부 완화할 수 있다. 전력 ramp가 지연되어도 batching, disaggregation, model routing이 개선되면 token output 감소를 줄일 수 있다. 그래서 grid-constrained / efficiency-upside 시나리오가 필요하다.

## 2026-05-26 Utilization 해석 보강

본 모델의 `utilization`은 전력이 켜져 있거나 GPU가 배치되어 있다는 비율이 아니다. 이는 이론적인 generated output token throughput 중 실제 상용 traffic으로 실현되는 비율이다.

감산 요인은 다음과 같다.

- latency SLO를 지키기 위한 headroom
- batch fill 부족과 traffic arrival 변동
- failover 및 regional redundancy reserve
- 긴 context, RAG, agentic workload의 prefill/decode 변화
- maintenance, orchestration, model routing 제약

Excel `05_inference_efficiency`와 `02b_number_trace`에는 업체별 utilization 값과 해당 값을 둔 운영 논리, 교체에 필요한 telemetry를 기록합니다.

## Hallucination 위험

peak benchmark throughput을 utilization 100%로 연중 곱하는 것이 가장 위험하다. 두 번째 위험은 utilization을 전력 사용률처럼 해석하는 것이다. inference fleet은 전력을 쓰고 있어도 SLO reserve로 일부 capacity가 비어 있을 수 있다.

## 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?
- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?
- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?
- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?
- low/base/high band와 confidence가 같이 기록되어 있는가?
- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

## 권장 모델 필드

- assumption_id: `A09_UTILIZATION`
- field_name: `utilization`
- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나
- confidence: High / Medium / Low
- replacement_path: 공식 source가 나오면 교체할 경로

## 참고자료

- **PAGED_ATTENTION:** Efficient Memory Management for LLM Serving with PagedAttention, Kwon et al., arXiv, 2023. https://arxiv.org/abs/2309.06180
- **SPLITWISE:** Splitwise: Efficient generative LLM inference using phase splitting, Patel et al., arXiv, 2023. https://arxiv.org/abs/2311.18677
- **DISTSERVE:** DistServe: Disaggregating Prefill and Decoding, Zhong et al., arXiv, 2024. https://arxiv.org/abs/2401.09670
- **GOOGLE_TPU_V5E:** Cloud TPU v5e documentation, Google Cloud, accessed 2026-05-15. https://docs.cloud.google.com/tpu/docs/v5e
- **AWS_INF2:** Amazon EC2 Inf2 instances, AWS, accessed 2026-05-15. https://aws.amazon.com/ec2/instance-types/inf2/
- **AWS_TRN2:** Amazon EC2 Trn2 instances, AWS, accessed 2026-05-15. https://aws.amazon.com/ec2/instance-types/trn2/

## 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
