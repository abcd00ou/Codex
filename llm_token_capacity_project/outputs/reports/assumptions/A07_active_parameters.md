<!-- Converted from A07_active_parameters.docx -->

A07 active_parameters

Dense와 MoE에서 token당 실제 계산량을 결정하는 핵심 변수

# Executive Summary

학습용 starting band: Dense: active ~= total. MoE: official active parameter 사용. Closed model: precise number 금지, band/proxy만 사용.

이 리포트의 숫자 범위는 학습용 starting band입니다. 회사별 공식 telemetry가 공개되면 반드시 교체해야 하며, 공식 source가 없는 값은 fact가 아니라 estimate/proxy/scenario로 표시해야 합니다.

`active_parameters`는 LLM token capacity simulation에서 숫자 정합성을 좌우하는 핵심 가정입니다. 이 문서는 해당 가정이 무엇을 의미하는지, 어떤 물리·운영·경제 원리에 의해 결정되는지, 공개자료를 어떻게 읽어야 하는지, 그리고 모델에 넣을 때 어떤 hallucination 위험을 피해야 하는지를 전문가 관점에서 정리합니다.

# 정의

active_parameters는 token 하나를 생성할 때 실제로 활성화되어 계산에 참여하는 parameter 규모다. Dense Transformer에서는 대부분의 parameter가 매 token 계산에 관여하므로 active parameter가 total parameter와 거의 같다. 반면 MoE는 전체 expert parameter 중 일부만 token마다 activate되므로 total parameter와 active parameter가 크게 다르다.

LLM inference cost를 계산할 때 active_parameters는 total_parameters보다 더 직접적이다. token당 대략적인 forward FLOPs는 2 * active_parameters라는 sanity check로 볼 수 있다. 이 식은 매우 단순하지만, closed model 숫자나 tokens/sec/MW가 물리적으로 말이 되는지 점검하는 데 유용하다.

# 전문가 관점의 운영 원리

MoE는 거대한 지식 capacity와 낮은 per-token compute cost를 동시에 노리는 구조다. DeepSeek-V3는 공식 repo에서 671B total parameters와 37B activated parameters per token을 제시한다. Qwen3 계열도 235B total / 22B active 같은 MoE 구조를 공개한다. 이 숫자들은 total parameter만 보고 inference 비용을 과대평가하면 안 된다는 강한 anchor다.

Closed model은 다르다. OpenAI GPT-4.1 문서는 context window, output token limit, pricing, endpoint 등 product 정보를 제공하지만 parameter count는 공개하지 않는다. 이런 모델에 대해 인터넷 추정치를 precise fact로 쓰면 보고서 신뢰도가 무너진다. closed model은 architecture band, performance class, pricing, latency, context, benchmark proxy로 다뤄야 한다.

active parameter는 KV cache와도 연결된다. token당 compute는 active parameter가 크게 좌우하지만, long context serving에서는 KV cache memory와 attention cost도 중요하다. 따라서 active parameter만으로 tokens/sec/MW를 완전히 설명할 수 없다. 모델 architecture, context length, batch shape, prefill/decode ratio를 함께 봐야 한다.

# 현실적 숫자 범위 잡기

공개 MoE 모델은 official repo 또는 model card의 active parameter를 사용한다. DeepSeek, Qwen처럼 공식 자료가 있으면 confidence를 높일 수 있다. 공개 dense 모델은 total parameter를 active parameter proxy로 둔다. closed model은 단일 숫자 대신 low/base/high band를 두고, benchmark sanity layer에서만 proxy로 사용한다.

active parameter band는 model family별로 잡아야 한다. 같은 회사라도 flagship reasoning model, mini model, coding model, embedding model, multimodal model이 다르다. 상용 token 대부분이 항상 가장 큰 모델에서 나온다고 가정하면 비용을 과대평가할 수 있다. 실제 서비스는 routing과 model cascade를 사용해 작은 모델이 많은 traffic을 처리할 수 있다.

# 모델링 영향

active_parameters가 커지면 token당 FLOPs와 energy cost가 증가하고 tokens/sec/MW는 낮아지는 방향이다. MoE optimization이 좋아지거나 smaller model routing이 커지면 effective active parameter가 낮아져 token capacity가 증가할 수 있다.

이 변수는 tokens/sec/MW를 직접 산정하지 않더라도 sanity check에 필수다. forecast가 어떤 회사의 closed flagship model에 대해 지나치게 높은 tokens/sec/MW를 가정한다면, active parameter band와 accelerator FLOPs로 역산해 모순을 찾아야 한다.

# Hallucination 위험

가장 큰 위험은 closed model parameter rumor를 fact로 쓰는 것이다. 두 번째 위험은 MoE total parameter를 active parameter처럼 사용하거나, 반대로 active parameter만 보고 memory footprint를 과소평가하는 것이다. MoE는 per-token compute와 total weight storage를 분리해야 한다.

# 실무 체크리스트

- 이 값은 fact, estimate, proxy, scenario 중 무엇인가?

- 단위가 GW, MW, TWh/year, tokens/sec, tokens/day 중 무엇인지 명확한가?

- 회사 공식자료가 직접 말한 숫자인가, 우리가 계산한 숫자인가?

- 값이 10% 변하면 2030 Base forecast가 얼마나 움직이는가?

- low/base/high band와 confidence가 같이 기록되어 있는가?

- 새로운 공식 source가 나오면 어떤 replacement path로 교체할 것인가?

# 권장 모델 필드

- assumption_id: A07_ACTIVE_PARAMETERS

- field_name: active_parameters

- derivation_type: Fact / Estimate / Proxy / Scenario 중 하나

- confidence: High / Medium / Low

- replacement_path: 공식 source가 나오면 교체할 경로

# 참고자료

- DEEPSEEK_V3: DeepSeek-V3 GitHub / Technical Report, DeepSeek, 2024. https://github.com/deepseek-ai/DeepSeek-V3

- DEEPSEEK_R1: DeepSeek-R1: Incentivizing Reasoning Capability, DeepSeek, arXiv, 2025. https://arxiv.org/abs/2501.12948

- QWEN3: Qwen3 GitHub, Alibaba Qwen, 2025. https://github.com/QwenLM/Qwen3

- OPENAI_GPT41: GPT-4.1 model documentation, OpenAI, accessed 2026-05-15. https://platform.openai.com/docs/models/gpt-4.1

- KAPLAN: Scaling Laws for Neural Language Models, Kaplan et al., arXiv, 2020. https://arxiv.org/abs/2001.08361

- CHINCHILLA: Training Compute-Optimal Large Language Models, Hoffmann et al., arXiv, 2022. https://arxiv.org/abs/2203.15556

# 저작권 및 사용 메모

이 문서는 외부 자료의 전문을 복제하지 않고, 모델링과 학습에 필요한 범위에서 해석과 요약을 제공합니다. 보고서에 수치를 사용할 때는 원문 source를 다시 열어 title, publisher, date, URL, 숫자 정의를 확인해야 합니다.
