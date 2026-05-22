<!-- Converted from A05_inference_power_share.docx -->

A05 inference_power_share

AI IT load 중 상용 토큰 생성에 배정되는 전력 비중

# Executive Summary

학습용 starting band: 2026 Base 50-60%, 2030 Base 65-80%. 2026 60%+는 fact가 아니라 company-specific bull 또는 scenario로 표현.

이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

`inference_power_share`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

# 정의

inference_power_share는 AI IT load 중 inference serving에 배정되는 비중이다. inference는 학습된 모델을 이용해 prompt를 처리하고 output token을 생성하는 서비스 단계다. ChatGPT, Claude, Gemini, Copilot, Meta AI, Qwen API, Hunyuan 서비스의 traffic이 이 share를 만든다.

이 값은 추론 토큰 생성량의 직접 입력이다. 그러나 공개자료에서 기업별 inference_power_share가 직접 공개되는 경우는 매우 드물다. 따라서 이 변수는 대부분 estimate 또는 scenario이며, 공식 fact처럼 표현하면 안 된다.

# 전문가 관점의 운영 원리

상용 LLM 기업이 성숙할수록 inference_power_share는 상승 압력을 받는다. 매일 들어오는 API 요청, consumer chatbot, enterprise assistant, coding agent, search answer, multimodal generation은 연중 반복되는 serving load다. 반면 training은 대규모 실험과 모델 세대 전환에 집중된다. 상용 traffic이 커지면 marginal capacity는 inference 쪽으로 많이 배정될 수 있다.

하지만 inference share가 100%로 가는 것은 아니다. frontier model training, post-training, eval, safety testing, synthetic data generation, distillation, data pipeline이 계속 compute를 요구한다. 특히 frontier 경쟁을 하는 기업은 상용 inference가 커져도 training reserve를 유지한다.

Google Ironwood처럼 inference-oriented accelerator 발표는 inference 수요의 방향성을 보여준다. Google TPU v5e 문서도 training과 serving provisioning 차이를 설명한다. PagedAttention, Splitwise, DistServe는 inference serving이 prefill/decode, KV cache, latency SLO, batching 문제와 연결된다는 것을 보여준다. 이런 문헌은 inference share를 직접 주지는 않지만, inference가 독립된 capacity planning 대상임을 뒷받침한다.

# 현실적 숫자 범위 잡기

2026년 Base에서 50-60%를 학습용 band로 두는 이유는 상용 inference가 이미 중요하지만 frontier training과 post-training도 여전히 크기 때문이다. 2030년 Base에서 65-80%로 올리는 이유는 LLM이 제품과 workflow에 더 깊게 들어가고, inference-oriented hardware와 serving optimization이 확대될 가능성이 높기 때문이다.

기업별로 조정해야 한다. OpenAI, Anthropic, Google처럼 상용 surface가 큰 기업은 inference share가 높을 수 있다. xAI처럼 빠르게 product traffic을 키우는 challenger는 초기 training-heavy에서 빠르게 inference share가 올라갈 수 있다. DeepSeek, Alibaba, Tencent는 public API와 internal app traffic의 투명성이 낮아 confidence를 낮게 두되, 중국 내 대규모 app integration 가능성을 sensitivity로 봐야 한다.

# 모델링 영향

inference_power_share는 token forecast에 선형적으로 작용한다. AI IT load가 1GW이고 inference share가 60%라면 600MW가 token generation에 들어간다. share가 70%로 오르면 token capacity는 같은 조건에서 16.7% 증가한다.

이 값은 memory marketing에서도 중요하다. inference share가 올라가면 HBM만이 아니라 DDR5/MRDIMM, SSD, CXL, network, power delivery 수요도 달라진다. 긴 context와 RAG가 많아질수록 KV cache, SSD retrieval, CPU-side memory attach의 중요성이 커진다.

# Hallucination 위험

2026년에 전체 AI GW의 60% 이상이 inference라고 단정하는 것은 공개자료만으로는 위험하다. inference-oriented chip 발표는 방향성이지 share fact가 아니다. 또한 inference_power_share와 utilization을 혼동하면 안 된다. inference로 배정된 capacity가 항상 100% token generation으로 전환되는 것은 아니다.

# 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?

- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?

- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?

- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?

- low/base/high band와 confidence가 같이 기록되어 있는가?

- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

# 권장 모델 필드

- assumption_id: A05_INFERENCE_POWER_SHARE

- field_name: inference_power_share

- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나

- confidence: High / Medium / Low

- replacement_path: 공식 source가 나오면 교체할 경로

# 참고자료

- GOOGLE_IRONWOOD: Ironwood: the first Google TPU for the age of inference, Google Cloud, 2025. https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/

- GOOGLE_TPU_V5E: Cloud TPU v5e documentation, Google Cloud, accessed 2026-05-15. https://docs.cloud.google.com/tpu/docs/v5e

- PAGED_ATTENTION: Efficient Memory Management for LLM Serving with PagedAttention, Kwon et al., arXiv, 2023. https://arxiv.org/abs/2309.06180

- SPLITWISE: Splitwise: Efficient generative LLM inference using phase splitting, Patel et al., arXiv, 2023. https://arxiv.org/abs/2311.18677

- DISTSERVE: DistServe: Disaggregating Prefill and Decoding, Zhong et al., arXiv, 2024. https://arxiv.org/abs/2401.09670

- AWS_RAINIER: AWS activates Project Rainier, Amazon, 2025. https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster

- OPENAI_GPT41: GPT-4.1 model documentation, OpenAI, accessed 2026-05-15. https://platform.openai.com/docs/models/gpt-4.1

# 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
