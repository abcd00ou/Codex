<!-- Converted from A06_training_power_share.docx -->

A06 training_power_share

frontier training, post-training, eval capacity를 어떻게 남길 것인가

# Executive Summary

학습용 starting band: training_power_share = 1 - inference_power_share로 시작하되, frontier lab은 2026-2030에도 의미 있는 reserve 유지.

이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

`training_power_share`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

# 정의

training_power_share는 AI IT load 중 모델 weight 업데이트, pretraining, post-training, fine-tuning, RL, eval, synthetic data generation 등 학습 관련 workload에 배정되는 비중이다. 간단한 모델에서는 1 - inference_power_share로 계산하지만, 실제로는 eval/reserve/post-training을 별도 category로 두는 것이 더 정확하다.

이 변수는 token generation forecast에서는 inference의 반대편처럼 보이지만, AI 기업의 전략에서는 핵심이다. training capacity는 다음 모델 세대, 성능 우위, 제품 차별화, 장기 경쟁력을 만든다.

# 전문가 관점의 운영 원리

Kaplan scaling law와 Chinchilla는 training compute allocation을 이해하는 기초 이론이다. 모델 성능은 parameter, data, compute scaling과 연결되고, compute-optimal training은 단순히 모델을 키우는 것이 아니라 학습 토큰과 모델 크기를 균형 있게 조정해야 함을 보여준다. 이 이론은 왜 frontier lab이 상용 inference가 커져도 training을 계속하는지 설명한다.

Epoch AI의 frontier training compute 분석은 training run의 compute와 power demand가 계속 커질 수 있음을 보여준다. 다만 이 숫자는 연중 평균 training share가 아니라 특정 frontier run의 envelope로 읽어야 한다. peak training power와 annual average power allocation을 섞으면 잘못된 결론이 나온다.

Training workload는 cluster topology에 민감하다. 수천에서 수만 accelerator가 하나의 job에 묶이면 interconnect, checkpoint, failure recovery, parallelism strategy가 중요해진다. 이런 job은 inference처럼 작은 regional fleet으로 쉽게 나누기 어렵다. 그래서 training capacity는 물리적으로도 운영적으로도 별도 planning이 필요하다.

# 현실적 숫자 범위 잡기

초기 연구 중심 기업은 training share가 높다. 상용화가 진행된 기업은 inference share가 올라가지만 frontier model 경쟁을 한다면 training share를 낮게만 둘 수 없다. 2026년에는 많은 기업이 training과 inference를 모두 크게 늘리는 단계로 보는 것이 합리적이다.

2030년에는 inference share 상승이 base scenario지만, training share가 사라지는 것은 아니다. 특히 reasoning model, multimodal model, agent model, long-context model은 계속 post-training과 eval compute를 요구한다. 따라서 training_power_share는 단순 잔여값이더라도 해석상 '미래 역량 투자 capacity'로 설명해야 한다.

# 모델링 영향

training_power_share가 높아지면 단기 token generation capacity는 낮아진다. 그러나 장기적으로 더 효율적인 모델, 더 작은 active parameter, better routing, distillation을 가능하게 해 future tokens/sec/MW를 올릴 수 있다. 따라서 training share를 단순 비용으로만 보면 안 된다.

메모리 관점에서는 training share가 높을수록 HBM bandwidth/capacity, high-end GPU allocation, scale-up/scale-out network, checkpoint storage 수요가 커진다. inference share가 높을수록 latency, KV cache, SSD retrieval, regional serving fleet 수요가 더 중요해진다.

# Hallucination 위험

training_power_share를 inference의 단순 잔여값으로 두고 설명을 생략하면 안 된다. 또 frontier training run의 peak power 전망을 연중 평균 share로 쓰면 안 된다. training에는 pretraining뿐 아니라 post-training, eval, synthetic data generation이 포함될 수 있음을 명시해야 한다.

# 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?

- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?

- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?

- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?

- low/base/high band와 confidence가 같이 기록되어 있는가?

- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

# 권장 모델 필드

- assumption_id: A06_TRAINING_POWER_SHARE

- field_name: training_power_share

- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나

- confidence: High / Medium / Low

- replacement_path: 공식 source가 나오면 교체할 경로

# 참고자료

- KAPLAN: Scaling Laws for Neural Language Models, Kaplan et al., arXiv, 2020. https://arxiv.org/abs/2001.08361

- CHINCHILLA: Training Compute-Optimal Large Language Models, Hoffmann et al., arXiv, 2022. https://arxiv.org/abs/2203.15556

- EPOCH_TRAIN: Training compute of frontier AI models grows by 4-5x per year, Epoch AI, 2024. https://epoch.ai/blog/training-compute-of-frontier-ai-models-grows-by-4-5x-per-year

- EPOCH_POWER: How much power will frontier AI training demand in 2030?, Epoch AI, 2025. https://epoch.ai/blog/power-demands-of-frontier-ai-training/

- AWS_RAINIER: AWS activates Project Rainier, Amazon, 2025. https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster

- GOOGLE_TPU_V5E: Cloud TPU v5e documentation, Google Cloud, accessed 2026-05-15. https://docs.cloud.google.com/tpu/docs/v5e

# 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
